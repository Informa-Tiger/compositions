#!/usr/bin/env python3
"""Bounded, configurable SATB beam search; independent audit is mandatory.

All tune, key, register, entry, rest and activity choices come from the job.
The consonant vocabulary is intentionally small; this is a reusable experiment,
not a complete grammar of eighteenth-century counterpoint.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np

VOICES = "satb"
PAIRS = list(itertools.combinations(range(4), 2))


class SearchFailure(RuntimeError):
    """This bounded search did not find an audited result (not infeasibility)."""


def integer(value, label, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    return value


def boolean(value, label):
    if type(value) is not bool:
        raise ValueError(f"{label} must be Boolean")
    return value


def prepare_job(job):
    c = job["config"]
    n = integer(c["total_ticks"], "total_ticks", 1)
    integer(c["ticks_per_quarter"], "ticks_per_quarter", 1)
    tonic = integer(c["tonic_pc"], "tonic_pc")
    if tonic > 11 or c["tonic_third"] not in (3, 4):
        raise ValueError("tonic_pc must be 0..11; tonic_third must be 3 or 4")
    if len(c["ranges"]) != 4 or len(c["max_leaps"]) != 4:
        raise ValueError("ranges and max_leaps must have four entries")
    for lo, hi in c["ranges"]:
        if not (type(lo) is int and type(hi) is int and 1 <= lo <= hi <= 127):
            raise ValueError("Each register must satisfy 1 <= lo <= hi <= 127")
    for x in c["max_leaps"]:
        integer(x, "max_leaps entry", 1)
    pcs = c["allowed_pcs"]
    if not pcs or any(type(p) is not int or not 0 <= p < 12 for p in pcs):
        raise ValueError("allowed_pcs must be a nonempty list of pitch classes")
    stride = integer(c["pulse_stride"], "pulse_stride", 1)
    if not 0 <= integer(c["pulse_offset"], "pulse_offset") < stride:
        raise ValueError("pulse_offset must be smaller than pulse_stride")
    integer(c["tritone_max_wait"], "tritone_max_wait", 1)
    integer(c["min_independent_changes"], "min_independent_changes", 1)
    if type(c["require_independence"]) is not bool:
        raise ValueError("require_independence must be Boolean")

    fixed = np.full((n, 4), -1, dtype=np.int16)
    boundaries = [set() for _ in VOICES]
    explicit = {v: [] for v in VOICES}

    def add_note(v, note):
        if v not in VOICES:
            raise ValueError(f"Unknown voice {v}")
        start = integer(note["start"], "note start")
        dur = integer(note["dur"], "note duration", 1)
        pitch = integer(note["pitch"], "note pitch", 1)
        vi = VOICES.index(v)
        if start + dur > n or pitch > 127:
            raise ValueError("Fixed note outside score/MIDI bounds")
        if pitch % 12 not in pcs or not c["ranges"][vi][0] <= pitch <= c["ranges"][vi][1]:
            raise ValueError(f"Fixed note outside key/register: {v} {note}")
        if np.any(fixed[start:start + dur, vi] != -1):
            raise ValueError(f"Overlapping fixed notes/rests: {v} at {start}")
        fixed[start:start + dur, vi] = pitch
        boundaries[vi].update((start, start + dur))
        explicit[v].append(dict(start=start, dur=dur, pitch=pitch))

    for v, notes in job.get("fixed_notes", {}).items():
        for note in notes:
            add_note(v, note)
    for entry in job.get("entries", []):
        motif = job.get("motifs", {})[entry["motif"]]
        if not isinstance(motif, list) or not motif:
            raise ValueError("A motif must be a nonempty note list")
        start = integer(entry["start"], "entry start")
        transpose = entry.get("transpose", 0)
        if type(transpose) is not int:
            raise ValueError("entry transpose must be an integer")
        scale = integer(entry.get("duration_scale", 1), "duration_scale", 1)
        for note in motif:
            dur = integer(note["dur"], "motif duration", 1) * scale
            add_note(entry["voice"], dict(start=start, dur=dur, pitch=integer(note["pitch"], "motif pitch", 1) + transpose))
            start += dur
    for v, spans in job.get("rests", {}).items():
        if v not in VOICES:
            raise ValueError(f"Unknown voice {v}")
        vi = VOICES.index(v)
        for a, b in spans:
            integer(a, "rest start")
            integer(b, "rest end", 1)
            if not a < b <= n or np.any(fixed[a:b, vi] != -1):
                raise ValueError(f"Invalid/overlapping rest: {v} [{a}, {b})")
            fixed[a:b, vi] = 0
            boundaries[vi].update((a, b))

    # Only major/minor consonant triads are derived. Diminished and augmented
    # triads are omitted; the one licensed tritone has a separate cadence path.
    scale = [0, 2, 4, 5, 7, 9, 11] if c["tonic_third"] == 4 else [0, 2, 3, 5, 7, 8, 11]
    derived = []
    for degree, name in enumerate(["I", "ii", "iii", "IV", "V", "vi", "vii"]):
        intervals = [scale[(degree + d) % 7] for d in (0, 2, 4)]
        root = scale[degree]
        quality = {(x - root) % 12 for x in intervals}
        if quality not in ({0, 3, 7}, {0, 4, 7}):
            continue
        chord_pcs = [(tonic + x) % 12 for x in intervals]
        if not set(chord_pcs) <= set(pcs):
            continue
        derived.append(dict(name=name, pcs=chord_pcs, bass_pcs=chord_pcs[:2]))
    chords = {}
    for chord in job.get("chords", derived):
        name = chord["name"]
        chord_pcs = chord["pcs"]
        if not isinstance(name, str) or name in chords or name == "V65":
            raise ValueError("Chord names must be unique strings; V65 is reserved")
        if len(set(chord_pcs)) != 3 or any(type(p) is not int or not 0 <= p < 12 for p in chord_pcs):
            raise ValueError("Vocabulary chords must contain three pitch classes")
        quality = {(pc - chord_pcs[0]) % 12 for pc in chord_pcs}
        if quality not in ({0, 3, 7}, {0, 4, 7}):
            raise ValueError("Vocabulary chords must be major/minor triads with the root listed first")
        bass_pcs = chord.get("bass_pcs", chord_pcs[:2])
        if not bass_pcs or any(type(p) is not int or not 0 <= p < 12 for p in bass_pcs) or not set(bass_pcs) <= set(chord_pcs):
            raise ValueError("bass_pcs must be a nonempty subset of chord pcs")
        chords[name] = dict(pcs=set(chord_pcs), bass_pcs=set(bass_pcs), complete=boolean(chord.get("complete", False), "chord complete"))
    tonic_set = {(tonic + x) % 12 for x in (0, c["tonic_third"], 7)}
    if "I" in chords and chords["I"]["pcs"] != tonic_set:
        raise ValueError("I is reserved for the configured tonic triad")
    if "I" not in chords:
        chords["I"] = dict(pcs=tonic_set, bass_pcs={tonic, (tonic + c["tonic_third"]) % 12}, complete=False)
    normal_names = list(chords)
    chords["V65"] = dict(pcs={(tonic + x) % 12 for x in (11, 2, 5, 7)}, bass_pcs={(tonic + 11) % 12}, complete=True)
    plan = [set(normal_names) for _ in range(n)]
    complete = [False] * n
    planned = [False] * n
    root_bass = [False] * n
    for item in job.get("chord_plan", []):
        a, b = integer(item["start"], "plan start"), integer(item["end"], "plan end", 1)
        names = set(item["chords"])
        if not a < b <= n or not names or not names <= chords.keys():
            raise ValueError("Invalid chord plan span or chord name")
        for t in range(a, b):
            # Plan rows intersect. They never silently override contradictions.
            plan[t] = plan[t] & names if planned[t] else names.copy()
            planned[t] = True
            complete[t] |= boolean(item.get("complete", False), "plan complete")
            root_bass[t] |= boolean(item.get("tonic_root_bass", False), "tonic_root_bass")
    for item in job.get("cadences", []):
        a = integer(item["start"], "cadence start")
        r = integer(item["resolve"], "cadence resolve", 1)
        b = integer(item["end"], "cadence end", 1)
        if not a < r < b <= n or r - a > c["tritone_max_wait"]:
            raise ValueError("Cadence must be start < resolve < end and resolve promptly")
        for t in range(a, r):
            if planned[t] and "V65" not in plan[t]:
                raise ValueError("Cadence contradicts chord_plan")
            plan[t] = {"V65"}
            planned[t] = True
        for t in range(r, b):
            plan[t] &= {"I"}
            planned[t] = True
            complete[t] = root_bass[t] = True
    for t in range(n):
        if not plan[t]:
            raise ValueError(f"Contradictory chord plan at tick {t}")
    activity = []
    for item in job.get("activity", []):
        a, b = item.get("start", 0), item.get("end", n)
        integer(a, "activity start")
        integer(b, "activity end", 1)
        period = integer(item["period"], "activity period", 1)
        offset = integer(item.get("offset", 0), "activity offset")
        if not a < b <= n or offset >= period or item["voice"] not in VOICES:
            raise ValueError("Invalid activity span/voice/offset")
        weight = float(item.get("weight", 1.7))
        if not np.isfinite(weight) or weight < 0:
            raise ValueError("Activity weight must be finite and nonnegative")
        activity.append((a, b, VOICES.index(item["voice"]), period, offset, weight))
    spacing = job.get("max_spacing", [12, 12, 19])
    if len(spacing) != 3 or any(type(x) is not int or x < 1 for x in spacing):
        raise ValueError("max_spacing must contain three positive integers")
    return c, fixed, boundaries, explicit, chords, plan, complete, root_bass, activity, spacing


def make_candidates(t, prepared):
    c, fixed, _, _, chords, plan, complete, root_bass, _, spacing = prepared
    ranges = c["ranges"]
    allowed = set(c["allowed_pcs"])
    frames, names, costs = [], [], []
    for name in sorted(plan[t]):
        chord = chords[name]
        opts = []
        for v in range(4):
            if fixed[t, v] >= 0:
                value = int(fixed[t, v])
                opts.append([value] if value == 0 or value % 12 in chord["pcs"] else [])
            else:
                opts.append([p for p in range(ranges[v][0], ranges[v][1] + 1)
                             if p % 12 in allowed & chord["pcs"]])
        for p in itertools.product(*opts):
            if not any(p):
                continue
            pcs = {x % 12 for x in p if x}
            if p[3] and p[3] % 12 not in chord["bass_pcs"]:
                continue
            if (complete[t] or chord["complete"]) and pcs != chord["pcs"]:
                continue
            if root_bass[t] and (not p[3] or p[3] % 12 != c["tonic_pc"]):
                continue
            if any(p[u] and p[l] and p[u] < p[l] for u, l in PAIRS):
                continue
            if any(p[v] and p[v + 1] and p[v] - p[v + 1] > spacing[v] for v in range(3)):
                continue
            if name == "V65" and (t == c["total_ticks"] - 1 or not p[3]):
                continue
            cost = sum(.008 * (value - sum(ranges[v]) / 2) ** 2 for v, value in enumerate(p) if value)
            cost += .7 * len(chord["pcs"] - pcs)
            cost += sum(.5 for u, l in PAIRS if p[u] and p[u] == p[l])
            frames.append(p)
            names.append(name)
            costs.append(cost)
    if not frames:
        raise SearchFailure(f"No admissible vertical candidate at tick {t}; inspect job constraints")
    return np.array(frames, dtype=np.int16), np.array(names), np.array(costs)


def events_from_frames(frames, boundaries):
    voices = {}
    for v, name in enumerate(VOICES):
        notes = []
        for t, frame in enumerate(frames):
            p = int(frame[v])
            if not p:
                continue
            if notes and notes[-1]["pitch"] == p and notes[-1]["start"] + notes[-1]["dur"] == t and t not in boundaries[v]:
                notes[-1]["dur"] += 1
            else:
                notes.append(dict(start=t, dur=1, pitch=p))
        voices[name] = notes
    return voices


def compose(job, beam=300, progress=None):
    from audit import audit_score

    integer(beam, "beam width", 1)
    prepared = prepare_job(job)
    c, _, boundaries, explicit, _, _, _, _, activity, _ = prepared
    n = c["total_ticks"]
    stride, offset = c["pulse_stride"], c["pulse_offset"]
    candidates = [make_candidates(t, prepared) for t in range(n)]
    if progress:
        progress(f"Candidates per tick: {min(len(q[0]) for q in candidates)}..{max(len(q[0]) for q in candidates)}; beam {beam}")
    p, labels, costs = candidates[0]
    keep = np.argsort(costs, kind="stable")[:beam]
    p, labels, costs = p[keep], labels[keep], costs[keep]
    anchor = p.copy()
    hist = np.array([p[:, [u, l]] for u, l in PAIRS]).transpose(1, 0, 2).copy()
    paths = [[frame.tolist()] for frame in p]
    label_paths = [[str(label)] for label in labels]
    ages = np.ones((len(p), 4), dtype=np.int16)
    tritone_age = np.where(labels == "V65", 1, 0)
    independence = np.zeros((len(p), 4, 4), dtype=np.int16)
    threshold = c["min_independent_changes"]

    for t in range(1, n):
        q, qlabels, qcost = candidates[t]
        d = q[None, :, :] - p[:, None, :]
        active = (p[:, None, :] > 0) & (q[None, :, :] > 0)
        ad = np.abs(d)
        change = (d != 0) & active
        ok = np.all(~active | (ad <= np.array(c["max_leaps"])), axis=2)
        ok &= np.all(~active | (ad % 12 != 6), axis=2)
        for k, (u, l) in enumerate(PAIRS):
            interval = (q[:, u] - q[:, l]) % 12
            perfect = np.isin(interval, [0, 7])[None, :]
            bad = ((d[:, :, u] * d[:, :, l] > 0) & perfect) | ((d[:, :, u] < 0) & (d[:, :, l] > 0) & (interval[None, :] == 0))
            ok &= ~(active[:, :, u] & active[:, :, l] & bad)
            if t > offset and (t - offset) % stride == 0:
                du = q[None, :, u] - anchor[:, None, u]
                dl = q[None, :, l] - anchor[:, None, l]
                sounding = (anchor[:, None, u] > 0) & (anchor[:, None, l] > 0) & (q[None, :, u] > 0) & (q[None, :, l] > 0)
                bad = ((du * dl > 0) & perfect) | ((du < 0) & (dl > 0) & (interval[None, :] == 0))
                ok &= ~(sounding & bad)
            hu, hl = hist[:, k, 0, None], hist[:, k, 1, None]
            pu, pl = p[:, u, None], p[:, l, None]
            qu, ql = q[None, :, u], q[None, :, l]
            alt = ((hu != pu) & (hl == pl) & (pu == qu) & (pl != ql)) | ((hu == pu) & (hl != pl) & (pu != qu) & (pl == ql))
            du, dl = qu - hu, ql - hl
            bad = ((du * dl > 0) & perfect) | ((du < 0) & (dl > 0) & (interval[None, :] == 0))
            ok &= ~(alt & bad & (hu > 0) & (hl > 0) & (qu > 0) & (ql > 0))
        for u in range(3):
            sounding = active[:, :, u] & active[:, :, u + 1]
            ok &= ~sounding | ((q[None, :, u] >= p[:, None, u + 1]) & (q[None, :, u + 1] <= p[:, None, u]))

        # Every sounding V65 incurs the same critical-pitch hold/resolution
        # obligation as the auditor. Any delay is bounded from its first tick.
        for i in np.flatnonzero(labels == "V65"):
            fourth, leading = (c["tonic_pc"] + 5) % 12, (c["tonic_pc"] + 11) % 12
            critical = (p[i] % 12 == fourth) | (p[i] % 12 == leading)
            held = np.all(q[:, critical] == p[i, critical], axis=1) & (qlabels == "V65") & (tritone_age[i] < c["tritone_max_wait"])
            resolved = (qlabels == "I") & (q[:, 3] % 12 == c["tonic_pc"])
            wanted_pcs = {(c["tonic_pc"] + x) % 12 for x in (0, c["tonic_third"], 7)}
            resolved &= np.array([{int(x) % 12 for x in fr if x} == wanted_pcs for fr in q])
            for v in np.flatnonzero(critical):
                step = 1 if p[i, v] % 12 == leading else c["tonic_third"] - 5
                resolved &= q[:, v] == p[i, v] + step
            ok[i] &= held | resolved

        motion = np.sum(ad * np.array([.32, .32, .32, .25]) * active, axis=2)
        motion += np.sum(np.maximum(ad - 2, 0) ** 2 * np.array([.23, .23, .23, .075]) * active, axis=2)
        motion += np.maximum(np.sum(change, axis=2) - 2, 0) * 1.5
        for a, b, v, period, phase, weight in activity:
            if a <= t < b:
                if t % period == phase:
                    motion += np.where(change[:, :, v], -weight, weight * .25)
                    motion += np.where(change[:, :, v] & (ad[:, :, v] > 2), .5, 0)
                else:
                    motion += change[:, :, v] * weight * .2
        motion -= np.sum(change * np.minimum(ages[:, None, :], 8) * .07, axis=2)
        motion += np.sum(change & (ages[:, None, :] < 2), axis=2) * .3
        # Actual pitch-changing onsets must fall strictly inside another event.
        # Boundaries include fixed repeated notes, so a rearticulated pitch is
        # never mistaken for a sustained note by the independence preference.
        gain = np.zeros((len(p), len(q), 4), dtype=np.int8)
        for v in range(4):
            for w in range(4):
                if v == w or t in boundaries[w]:
                    continue
                held = active[:, :, w] & (d[:, :, w] == 0)
                missing = independence[:, None, v, w] < threshold
                gain[:, :, v] |= (change[:, :, v] & held & missing).astype(np.int8)
        if c["require_independence"]:
            motion -= np.sum(gain, axis=2) * 1.6
        total = costs[:, None] + motion + qcost[None, :]
        total[~ok] = np.inf
        per_candidate = min(4, len(p))
        indices = np.argpartition(total, per_candidate - 1, axis=0)[:per_candidate]
        values = np.take_along_axis(total, indices, axis=0)
        chosen = np.argsort(values, axis=None, kind="stable")[:beam]
        ri, ci = np.unravel_index(chosen, values.shape)
        pi = indices[ri, ci]
        selected = values[ri, ci]
        good = np.isfinite(selected)
        pi, ci, selected = pi[good], ci[good], selected[good]
        if not len(pi):
            raise SearchFailure(f"Beam exhausted at tick {t}; increase --beam or revise the job. Constraints were not relaxed.")
        newp = q[ci]
        newhist = hist[pi].copy()
        for k, (u, l) in enumerate(PAIRS):
            moved = np.any(newp[:, [u, l]] != p[pi][:, [u, l]], axis=1)
            newhist[moved, k, :] = p[pi[moved]][:, [u, l]]
        new_independence = independence[pi].copy()
        for v in range(4):
            changing = (newp[:, v] != p[pi, v]) & (newp[:, v] > 0) & (p[pi, v] > 0)
            for w in range(4):
                if v != w and t not in boundaries[w]:
                    held = (newp[:, w] == p[pi, w]) & (newp[:, w] > 0)
                    new_independence[:, v, w] += changing & held
        newages = np.where(newp != p[pi], 1, ages[pi] + 1)
        tritone_age = np.where(qlabels[ci] == "V65", tritone_age[pi] + 1, 0)
        paths = [paths[i] + [newp[k].tolist()] for k, i in enumerate(pi)]
        label_paths = [label_paths[i] + [str(qlabels[j])] for i, j in zip(pi, ci)]
        anchor = newp.copy() if t >= offset and (t - offset) % stride == 0 else anchor[pi].copy()
        p, labels, costs = newp, qlabels[ci], selected
        hist, ages, independence = newhist, newages, new_independence
        if progress and (t % 8 == 0 or t == n - 1):
            progress(f"tick {t}: {len(p)} histories")

    attempted = 0
    for ix in np.argsort(costs, kind="stable"):
        if c["require_independence"] and not np.all(np.max(independence[ix], axis=1) >= threshold):
            continue
        result = dict(title=job.get("title", "Counterpoint study"), config=c,
                      voices=events_from_frames(paths[ix], boundaries),
                      generation=dict(algorithm="bounded SATB beam search", beam=beam,
                                      cost=round(float(costs[ix]), 6), harmonies=label_paths[ix]))
        # The fixed-note contract includes exact note boundaries, not just pitches.
        if any(note not in result["voices"][v] for v in VOICES for note in explicit[v]):
            raise AssertionError("Fixed-note preservation error")
        report = audit_score(result)
        attempted += 1
        if report["passed"]:
            return result
    raise SearchFailure(f"No final history passed the independent audit (audited {attempted} histories; others failed independence). Increase --beam or revise the job. This does not prove infeasibility.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--beam", type=int, default=300)
    args = parser.parse_args()
    try:
        result = compose(json.loads(args.job.read_text()), args.beam, lambda s: print(s, file=sys.stderr))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n")
    except (ValueError, KeyError, TypeError, OSError, SearchFailure) as error:
        print(f"Composition failed: {error}", file=sys.stderr)
        return 1
    print(f"Wrote audited score: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
