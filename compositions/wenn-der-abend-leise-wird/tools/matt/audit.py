#!/usr/bin/env python3
"""Independent, tune-independent SATB counterpoint audit (Python stdlib only).

The auditor reconstructs sounding frames from notes; composer labels and cached
frames are never trusted. See PROCEDURE_AND_RULES.md for the deliberately strict musical policy.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path
from typing import Any

VOICES = "satb"
PAIRS = tuple(itertools.combinations(range(4), 2))
FORMAL_CHECKS = (
    "events_well_formed", "instantaneous_direct", "instantaneous_parallel",
    "instantaneous_battuta", "pulse_direct", "pulse_parallel", "pulse_battuta",
    "stagger_direct", "stagger_parallel", "stagger_battuta", "no_crossing",
    "ranges", "allowed_pitch_classes", "no_melodic_tritone",
    "licensed_harmonic_tritones", "rhythmic_independence",
)
PYTHON_ONLY_CHECKS = ("max_leaps", "adjacent_voice_overlap")


def _integer(value: Any) -> bool:
    return type(value) is int  # JSON true is not the integer one.


def validate_score(score: Any) -> list[dict[str, Any]]:
    """Return all discoverable schema errors without coercing input values.

    Additional metadata keys are allowed and ignored, not interpreted as rules.
    All fields documented in config are mandatory. The title is descriptive.
    """
    errors: list[dict[str, Any]] = []

    def bad(path: str, message: str) -> None:
        errors.append({"check": "schema_valid", "path": path, "message": message})

    if not isinstance(score, dict):
        bad("$", "score must be an object")
        return errors
    if not isinstance(score.get("title"), str) or not score["title"].strip():
        bad("title", "must be a nonempty string")
    config = score.get("config")
    if not isinstance(config, dict):
        bad("config", "must be an object")
        config = {}
    positive = ("total_ticks", "ticks_per_quarter", "pulse_stride",
                "tritone_max_wait", "min_independent_changes")
    for name in positive:
        if not _integer(config.get(name)) or config[name] <= 0:
            bad("config." + name, "must be a positive integer")
    tonic = config.get("tonic_pc")
    if not _integer(tonic) or not 0 <= tonic <= 11:
        bad("config.tonic_pc", "must be an integer in 0..11")
    third = config.get("tonic_third")
    if not _integer(third) or third not in (3, 4):
        bad("config.tonic_third", "must be 3 (minor) or 4 (major)")
    pcs = config.get("allowed_pcs")
    if (not isinstance(pcs, list) or not pcs or
            any(not _integer(p) or not 0 <= p <= 11 for p in pcs)):
        bad("config.allowed_pcs", "must be a nonempty array of integers in 0..11")
    ranges = config.get("ranges")
    if not isinstance(ranges, list) or len(ranges) != 4:
        bad("config.ranges", "must contain four [low, high] MIDI ranges in SATB order")
    else:
        for i, r in enumerate(ranges):
            if (not isinstance(r, list) or len(r) != 2 or
                    any(not _integer(p) for p in r) or not 1 <= r[0] <= r[1] <= 127):
                bad(f"config.ranges[{i}]", "must be [low, high], with 1 <= low <= high <= 127")
    leaps = config.get("max_leaps")
    if (not isinstance(leaps, list) or len(leaps) != 4 or
            any(not _integer(n) or n <= 0 for n in leaps)):
        bad("config.max_leaps", "must contain four positive integers in SATB order")
    offset = config.get("pulse_offset")
    stride = config.get("pulse_stride")
    if not _integer(offset) or offset < 0:
        bad("config.pulse_offset", "must be a nonnegative integer less than pulse_stride")
    elif _integer(stride) and stride > 0 and offset >= stride:
        bad("config.pulse_offset", "must be less than pulse_stride")
    if type(config.get("require_independence")) is not bool:
        bad("config.require_independence", "must be a boolean")
    voices = score.get("voices")
    if not isinstance(voices, dict):
        bad("voices", "must be an object containing s, a, t, b arrays")
        return errors
    if set(voices) != set(VOICES):
        bad("voices", "must have exactly the voice keys s, a, t, b")
    total = config.get("total_ticks")
    for voice in VOICES:
        notes = voices.get(voice)
        if not isinstance(notes, list) or not notes:
            bad("voices." + voice, "must be a nonempty array of note events")
            continue
        last_end = None
        for j, note in enumerate(notes):
            path = f"voices.{voice}[{j}]"
            if not isinstance(note, dict):
                bad(path, "must be an object with start, dur, pitch")
                continue
            valid = True
            for name in ("start", "dur", "pitch"):
                if not _integer(note.get(name)):
                    bad(path + "." + name, "must be an integer")
                    valid = False
            if not valid:
                continue
            start, duration, pitch = note["start"], note["dur"], note["pitch"]
            if start < 0:
                bad(path + ".start", "must be nonnegative")
            if duration <= 0:
                bad(path + ".dur", "must be positive")
            if not 1 <= pitch <= 127:
                bad(path + ".pitch", "must be a sounding MIDI pitch in 1..127; rests are gaps")
            if _integer(total) and start + duration > total:
                bad(path, "event extends beyond total_ticks")
            if last_end is not None and start < last_end:
                bad(path, "events must be sorted and nonoverlapping")
            last_end = start + duration
    return errors


def reconstruct_frames(score: dict[str, Any]) -> list[list[int]]:
    """Build SATB sounding pitches per tick; call validate_score first.

    Zero denotes an absent/resting voice only in this derived representation.
    """
    frames = [[0, 0, 0, 0] for _ in range(score["config"]["total_ticks"])]
    for i, voice in enumerate(VOICES):
        for note in score["voices"][voice]:
            for tick in range(note["start"], note["start"] + note["dur"]):
                frames[tick][i] = note["pitch"]
    return frames


def audit_score(score: Any) -> dict[str, Any]:
    """Audit data and explicit counterpoint policy; return JSON-serializable report.

    A successful report is not a proof of historical style or aesthetic quality.
    The portable Lean certificate independently checks the formal rule subset.
    """
    schema_errors = validate_score(score)
    scope = {
        "formal_rule_subset": list(FORMAL_CHECKS),
        "python_only": list(PYTHON_ONLY_CHECKS),
        "limitations": [
            "This is an explicit strict policy, not universal Bach/Fux correctness.",
            "Pitch classes have no diatonic spelling; not all dissonances or nonchord tones are classified.",
            "Independence counts changed-note onsets inside another voice's held notes; it does not establish thematic or aesthetic independence.",
            "Passing this Python audit is not itself a Lean proof; compile the generated certificate separately.",
        ],
    }
    if schema_errors:
        return {"passed": False, "checks": {"schema_valid": False},
                "errors": schema_errors, "scope": scope}
    config = score["config"]
    notes_by_voice = [score["voices"][v] for v in VOICES]
    total = config["total_ticks"]
    frames = reconstruct_frames(score)
    checks = {name: True for name in ("schema_valid",) + FORMAL_CHECKS + PYTHON_ONLY_CHECKS}
    errors: list[dict[str, Any]] = []

    def fail(check: str, **details: Any) -> None:
        checks[check] = False
        errors.append({"check": check, **details})

    def pair_transition(a: list[int] | tuple[int, int], b: list[int] | tuple[int, int],
                        indices: tuple[int, int], prefix: str, ticks: list[int],
                        local: bool = False) -> None:
        upper, lower = indices
        ua, la = (a[0], a[1]) if local else (a[upper], a[lower])
        ub, lb = (b[0], b[1]) if local else (b[upper], b[lower])
        if not all((ua, la, ub, lb)):
            return
        du, dl = ub - ua, lb - la
        before, after = abs(ua - la) % 12, abs(ub - lb) % 12
        detail = {"voices": VOICES[upper] + VOICES[lower], "ticks": ticks,
                  "from_pitches": [ua, la], "to_pitches": [ub, lb]}
        if du * dl > 0 and after in (0, 7):
            fail(prefix + "_direct", interval_class=after, **detail)
            if before == after:
                fail(prefix + "_parallel", interval_class=after, **detail)
        if du < 0 < dl and after == 0:
            fail(prefix + "_battuta", **detail)

    for tick in range(1, total):
        for pair in PAIRS:
            pair_transition(frames[tick - 1], frames[tick], pair, "instantaneous", [tick - 1, tick])
    pulses = list(range(config["pulse_offset"], total, config["pulse_stride"]))
    for before, after in zip(pulses, pulses[1:]):
        for pair in PAIRS:
            pair_transition(frames[before], frames[after], pair, "pulse", [before, after])
    stagger_windows = 0
    for upper, lower in PAIRS:
        trace: list[tuple[int, tuple[int, int]]] = []
        for tick, frame in enumerate(frames):
            pair_pitches = (frame[upper], frame[lower])
            if not trace or pair_pitches != trace[-1][1]:
                trace.append((tick, pair_pitches))
        for (ta, a), (tb, b), (tc, c) in zip(trace, trace[1:], trace[2:]):
            alternating = ((a[0] != b[0] and a[1] == b[1] and b[0] == c[0] and b[1] != c[1]) or
                           (a[0] == b[0] and a[1] != b[1] and b[0] != c[0] and b[1] == c[1]))
            if alternating and all(a + c):
                stagger_windows += 1
                pair_transition(a, c, (upper, lower), "stagger", [ta, tb, tc], local=True)
    tritone_ticks = []
    tritone_witnesses = []
    tonic = config["tonic_pc"]
    fourth, leading = (tonic + 5) % 12, (tonic + 11) % 12
    dominant_pcs = {(tonic + degree) % 12 for degree in (11, 2, 5, 7)}
    tonic_pcs = {(tonic + degree) % 12 for degree in (0, config["tonic_third"], 7)}
    for tick, frame in enumerate(frames):
        for upper, lower in PAIRS:
            if frame[upper] and frame[lower] and frame[upper] < frame[lower]:
                fail("no_crossing", tick=tick, voices=VOICES[upper] + VOICES[lower], pitches=frame)
        for i, pitch in enumerate(frame):
            if not pitch:
                continue
            if not config["ranges"][i][0] <= pitch <= config["ranges"][i][1]:
                fail("ranges", tick=tick, voice=VOICES[i], pitch=pitch)
            if pitch % 12 not in config["allowed_pcs"]:
                fail("allowed_pitch_classes", tick=tick, voice=VOICES[i], pitch=pitch)
        has_tritone = any(frame[u] and frame[l] and abs(frame[u] - frame[l]) % 12 == 6 for u, l in PAIRS)
        if not has_tritone:
            continue
        tritone_ticks.append(tick)
        pcs = {p % 12 for p in frame if p}
        if not frame[3] or frame[3] % 12 != leading or pcs != dominant_pcs:
            fail("licensed_harmonic_tritones", tick=tick, reason="tritone is not the configured complete V65", pitches=frame)
            continue
        critical = [(i, p, p + (config["tonic_third"] - 5 if p % 12 == fourth else 1))
                    for i, p in enumerate(frame) if p and p % 12 in (fourth, leading)]
        witness = None
        for resolution in range(tick + 1, min(total, tick + config["tritone_max_wait"] + 1)):
            target = frames[resolution]
            if not target[3] or target[3] % 12 != tonic or {p % 12 for p in target if p} != tonic_pcs:
                continue
            if all(all(frames[held][i] == p for held in range(tick, resolution)) and
                   target[i] == expected for i, p, expected in critical):
                witness = resolution
                break
        if witness is None:
            fail("licensed_harmonic_tritones", tick=tick, reason="no timely root-position tonic with critical pitches held and resolved in their own voices", pitches=frame)
        else:
            tritone_witnesses.append({"tick": tick, "resolution_tick": witness})
    for tick in range(1, total):
        before, after = frames[tick - 1], frames[tick]
        for upper, lower in ((0, 1), (1, 2), (2, 3)):
            if all((before[upper], before[lower], after[upper], after[lower])) and (
                    after[upper] < before[lower] or after[lower] > before[upper]):
                fail("adjacent_voice_overlap", tick=tick, voices=VOICES[upper] + VOICES[lower],
                     before=before, after=after)
    independence = [[0] * 4 for _ in range(4)]
    rhythm = {}
    for i, notes in enumerate(notes_by_voice):
        changes = []
        leaps = []
        for before, after in zip(notes, notes[1:]):
            if before["start"] + before["dur"] != after["start"]:
                continue  # rests break melodic continuity
            leap = after["pitch"] - before["pitch"]
            leaps.append(leap)
            if abs(leap) % 12 == 6:
                fail("no_melodic_tritone", voice=VOICES[i], tick=after["start"], semitones=leap)
            if abs(leap) > config["max_leaps"][i]:
                fail("max_leaps", voice=VOICES[i], tick=after["start"], semitones=leap)
            if leap:
                changes.append(after["start"])
        for j, held_notes in enumerate(notes_by_voice):
            if i != j:
                independence[i][j] = sum(any(n["start"] < tick < n["start"] + n["dur"] for n in held_notes) for tick in changes)
        if config["require_independence"] and max(independence[i]) < config["min_independent_changes"]:
            fail("rhythmic_independence", voice=VOICES[i], counts_against_held_voices=independence[i],
                 required=config["min_independent_changes"])
        rhythm[VOICES[i]] = {
            "notes": len(notes), "rest_ticks": total - sum(n["dur"] for n in notes),
            "pitch_changes": len(changes), "largest_contiguous_leap": max(map(abs, leaps), default=0),
            "durations": sorted({n["dur"] for n in notes}),
        }
    return {"passed": all(checks.values()), "checks": checks, "errors": errors,
            "scope": scope, "total_ticks": total, "pulse_ticks": pulses,
            "stagger_windows_checked": stagger_windows, "harmonic_tritone_ticks": tritone_ticks,
            "tritone_resolution_witnesses": tritone_witnesses,
            "independence_matrix": independence, "rhythm": rhythm}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("score", type=Path)
    parser.add_argument("--out", type=Path, help="write the complete JSON audit report")
    args = parser.parse_args(argv)
    try:
        score = json.loads(args.score.read_text(encoding="utf-8"))
        report = audit_score(score)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        report = {"passed": False, "checks": {"input_readable": False}, "errors": [{"check": "input_readable", "message": str(exc)}]}
    output = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
        print(json.dumps({"passed": report["passed"], "error_count": len(report["errors"]), "report": str(args.out)}))
    else:
        sys.stdout.write(output)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
