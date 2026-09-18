"""Integration checks: exact MIDI events and refusal to export failed scores."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from certify import certificate_text
from midi import midi_bytes


def read_midi_notes(data):
    """Small independent SMF reader for our documented note/meta event subset."""
    if data[:4] != b"MThd":
        raise AssertionError("Missing SMF header")
    length, fmt, count, ppq = struct.unpack(">IHHH", data[4:14])
    if (length, fmt, count) != (6, 1, 5):
        raise AssertionError("Wrong format or voice count")
    pos = 14
    tracks, endings = [], []
    for _ in range(count):
        if data[pos:pos + 4] != b"MTrk":
            raise AssertionError("Missing track")
        size = int.from_bytes(data[pos + 4:pos + 8], "big")
        raw = data[pos + 8:pos + 8 + size]
        pos += 8 + size
        at, tick, active, notes = 0, 0, {}, []

        def read_vlq():
            nonlocal at
            value = 0
            for _ in range(4):
                byte = raw[at]
                at += 1
                value = (value << 7) | (byte & 127)
                if byte < 128:
                    return value
            raise AssertionError("Invalid VLQ")

        ended = False
        while at < len(raw):
            tick += read_vlq()
            status = raw[at]
            at += 1
            if status == 255:
                kind = raw[at]
                at += 1
                size = read_vlq()
                at += size
                if kind == 47:
                    if active or at != len(raw):
                        raise AssertionError("Unclosed note or premature track end")
                    ended = True
            elif status & 240 == 192:
                at += 1
            elif status & 240 in (128, 144):
                pitch, velocity = raw[at:at + 2]
                at += 2
                key = (status & 15, pitch)
                if status & 240 == 144 and velocity:
                    if key in active:
                        raise AssertionError("Repeated pitch was not released first")
                    active[key] = tick
                else:
                    start = active.pop(key)
                    notes.append((start, tick - start, pitch))
            else:
                raise AssertionError(f"Unexpected event {status:x}")
        if not ended:
            raise AssertionError("No track end")
        tracks.append(sorted(notes))
        endings.append(tick)
    if pos != len(data):
        raise AssertionError("Trailing data")
    return ppq, tracks, endings


class PipelineTests(unittest.TestCase):
    def test_generated_studies_round_trip_exactly(self):
        for name in ("study_c_major", "study_d_major", "study_a_minor", "cadence_c_major"):
            score = json.loads((ROOT / f"examples/{name}_score.json").read_text())
            ppq, tracks, endings = read_midi_notes(midi_bytes(score))
            factor = ppq // score["config"]["ticks_per_quarter"]
            self.assertEqual(tracks[0], [])
            for i, voice in enumerate("satb", 1):
                expected = [(n["start"] * factor, n["dur"] * factor, n["pitch"])
                            for n in score["voices"][voice]]
                self.assertEqual(tracks[i], expected)
            self.assertEqual(endings, [score["config"]["total_ticks"] * factor] * 5)

    def test_rearticulation_rest_and_septuplet_grid(self):
        score = json.loads((ROOT / "examples/study_c_major_score.json").read_text())
        score["config"].update(total_ticks=4, ticks_per_quarter=7, require_independence=False)
        score["voices"] = {
            "s": [{"start": 0, "dur": 2, "pitch": 72}, {"start": 2, "dur": 2, "pitch": 72}],
            "a": [{"start": 0, "dur": 4, "pitch": 64}],
            "t": [{"start": 0, "dur": 1, "pitch": 55}, {"start": 2, "dur": 2, "pitch": 55}],
            "b": [{"start": 0, "dur": 4, "pitch": 48}],
        }
        score["config"]["ranges"] = [[1, 127]] * 4
        ppq, tracks, _ = read_midi_notes(midi_bytes(score))
        self.assertEqual(ppq % 7, 0)
        factor = ppq // 7
        self.assertEqual(tracks[1], [(0, 2 * factor, 72), (2 * factor, 2 * factor, 72)])
        self.assertEqual(tracks[3], [(0, factor, 55), (2 * factor, 2 * factor, 55)])

    def test_export_and_certificate_refuse_mutated_pitch(self):
        score = json.loads((ROOT / "examples/study_c_major_score.json").read_text())
        bad = copy.deepcopy(score)
        bad["voices"]["b"][0]["pitch"] = 126
        for exporter in (midi_bytes, certificate_text):
            with self.assertRaises(ValueError):
                exporter(bad)

    def test_certificate_does_not_interpret_title_as_lean(self):
        score = json.loads((ROOT / "examples/study_c_major_score.json").read_text())
        score["title"] = "UNTRUSTED_TITLE := sorry"
        generated = certificate_text(score)
        self.assertNotIn("UNTRUSTED_TITLE", generated)
        self.assertIn("theorem accepted : certified config voices = true := by decide", generated)


if __name__ == "__main__":
    unittest.main()
