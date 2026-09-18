"""Regression and mutation tests for the independent counterpoint audit.

Run from the toolkit directory: python -m unittest discover -s tests -v
The musical cases deliberately isolate behavior; a negative fixture can violate
more than one policy, so tests assert the relevant named check.
"""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from audit import audit_score, validate_score


def score_from_frames(frames, **config_overrides):
    config = {
        "total_ticks": len(frames), "ticks_per_quarter": 2,
        "tonic_pc": 0, "tonic_third": 4, "allowed_pcs": [0, 2, 4, 5, 7, 9, 11],
        "ranges": [[1, 127] for _ in range(4)], "max_leaps": [7, 7, 7, 12],
        "pulse_stride": 2, "pulse_offset": 0, "tritone_max_wait": 2,
        "require_independence": False, "min_independent_changes": 2,
    }
    config.update(config_overrides)
    voices = {v: [] for v in "satb"}
    for i, voice in enumerate("satb"):
        tick = 0
        while tick < len(frames):
            pitch = frames[tick][i]
            end = tick + 1
            while end < len(frames) and frames[end][i] == pitch:
                end += 1
            if pitch:
                voices[voice].append({"start": tick, "dur": end - tick, "pitch": pitch})
            tick = end
    return {"title": "Synthetic audit fixture", "config": config, "voices": voices}


def transpose(score, semitones):
    result = copy.deepcopy(score)
    cfg = result["config"]
    cfg["tonic_pc"] = (cfg["tonic_pc"] + semitones) % 12
    cfg["allowed_pcs"] = [(p + semitones) % 12 for p in cfg["allowed_pcs"]]
    for notes in result["voices"].values():
        for note in notes:
            note["pitch"] += semitones
    return result


class RuleTests(unittest.TestCase):
    def test_static_consonance_passes_and_audit_does_not_mutate_input(self):
        score = score_from_frames([[72, 67, 64, 48]] * 4)
        before = copy.deepcopy(score)
        report = audit_score(score)
        self.assertTrue(report["passed"], report["errors"])
        self.assertEqual(score, before)
        self.assertEqual(report["harmonic_tritone_ticks"], [])

    def test_direct_fifth_is_rejected_even_with_upper_voice_step(self):
        report = audit_score(score_from_frames([[72, 66, 60, 48], [74, 67, 60, 48]], allowed_pcs=list(range(12))))
        self.assertFalse(report["checks"]["instantaneous_direct"])
        hits = [e for e in report["errors"] if e["check"] == "instantaneous_direct"]
        self.assertTrue(any(e["voices"] == "sa" and e["interval_class"] == 7 for e in hits))

    def test_parallel_octaves_and_fifths_are_distinct_diagnostics(self):
        report = audit_score(score_from_frames([[72, 65, 60, 48], [74, 67, 62, 50]]))
        self.assertFalse(report["checks"]["instantaneous_parallel"])
        self.assertEqual({e["interval_class"] for e in report["errors"] if e["check"] == "instantaneous_parallel"}, {0, 7})

    def test_inward_octave_battuta(self):
        report = audit_score(score_from_frames([[74, 67, 65, 59], [72, 67, 64, 60]]))
        self.assertFalse(report["checks"]["instantaneous_battuta"])

    def test_compressed_pair_trace_catches_delayed_stagger(self):
        frames = [[72, 66, 60, 48], [74, 66, 60, 48], [74, 66, 60, 48], [74, 67, 60, 48]]
        report = audit_score(score_from_frames(frames, allowed_pcs=list(range(12)), pulse_stride=4))
        self.assertTrue(report["checks"]["instantaneous_direct"])
        self.assertFalse(report["checks"]["stagger_direct"])
        self.assertTrue(any(e["ticks"] == [0, 1, 3] and e["voices"] == "sa"
                            for e in report["errors"] if e["check"] == "stagger_direct"))

    def test_pulse_reduction_has_configurable_phase_and_stride(self):
        frames = [[72, 66, 60, 48], [71, 68, 60, 48], [74, 67, 60, 48]]
        report = audit_score(score_from_frames(frames, allowed_pcs=list(range(12))))
        self.assertTrue(report["checks"]["instantaneous_direct"])
        self.assertFalse(report["checks"]["pulse_direct"])
        other_phase = audit_score(score_from_frames(frames, allowed_pcs=list(range(12)), pulse_offset=1))
        self.assertTrue(other_phase["checks"]["pulse_direct"])
        self.assertEqual(other_phase["pulse_ticks"], [1])

    def test_rests_break_melodic_continuity(self):
        score = score_from_frames([[72, 67, 64, 48], [0, 67, 64, 48], [78, 67, 64, 48]], allowed_pcs=list(range(12)))
        report = audit_score(score)
        self.assertTrue(report["checks"]["no_melodic_tritone"])
        score["voices"]["s"][0]["dur"] = 2
        self.assertFalse(audit_score(score)["checks"]["no_melodic_tritone"])

    def test_compound_melodic_tritone_and_max_leap(self):
        score = score_from_frames([[72, 67, 64, 48], [90, 67, 64, 48]], allowed_pcs=list(range(12)))
        report = audit_score(score)
        self.assertFalse(report["checks"]["no_melodic_tritone"])
        self.assertFalse(report["checks"]["max_leaps"])
        self.assertIn("max_leaps", report["scope"]["python_only"])
        self.assertNotIn("max_leaps", report["scope"]["formal_rule_subset"])

    def test_major_v65_resolution_with_held_critical_pitches(self):
        report = audit_score(score_from_frames([[74, 67, 65, 59]] * 2 + [[76, 67, 64, 60]] * 2))
        self.assertTrue(report["passed"], report["errors"])
        self.assertEqual(report["tritone_resolution_witnesses"], [{"tick": 0, "resolution_tick": 2}, {"tick": 1, "resolution_tick": 2}])

    def test_minor_resolution_and_transposition(self):
        score = score_from_frames([[74, 67, 65, 59]] * 2 + [[75, 67, 63, 60]] * 2,
                                  tonic_third=3, allowed_pcs=[0, 2, 3, 5, 7, 8, 11])
        for displacement in (0, 2, -3, 7):
            report = audit_score(transpose(score, displacement))
            self.assertTrue(report["passed"], (displacement, report["errors"]))

    def test_major_resolution_does_not_silently_license_minor_third(self):
        score = score_from_frames([[74, 67, 65, 59], [75, 67, 63, 60]], allowed_pcs=list(range(12)))
        self.assertFalse(audit_score(score)["checks"]["licensed_harmonic_tritones"])

    def test_premature_critical_movement_and_rest_are_rejected(self):
        for premature in (64, 0):
            frames = [[74, 67, 65, 59], [74, 67, premature, 59], [76, 67, 64, 60]]
            report = audit_score(score_from_frames(frames))
            self.assertFalse(report["checks"]["licensed_harmonic_tritones"])
            self.assertTrue(any(e.get("tick") == 0 for e in report["errors"] if e["check"] == "licensed_harmonic_tritones"))

    def test_resolution_exactly_at_wait_limit_is_allowed(self):
        score = score_from_frames([[74, 67, 65, 59]] * 2 + [[76, 67, 64, 60]])
        self.assertTrue(audit_score(score)["checks"]["licensed_harmonic_tritones"])
        score["config"]["tritone_max_wait"] = 1
        self.assertFalse(audit_score(score)["checks"]["licensed_harmonic_tritones"])

    def test_terminal_tritone_is_unresolved(self):
        report = audit_score(score_from_frames([[74, 67, 65, 59]]))
        self.assertFalse(report["checks"]["licensed_harmonic_tritones"])

    def test_v65_exact_chord_and_root_position_tonic_are_required(self):
        for frames in (
            [[74, 65, 59, 55], [76, 64, 60, 48]],  # root-position V7
            [[74, 67, 65, 59], [76, 67, 64, 64]],  # tonic first inversion
            [[74, 71, 65, 59], [76, 72, 64, 60]],  # incomplete V65
        ):
            report = audit_score(score_from_frames(frames))
            self.assertFalse(report["checks"]["licensed_harmonic_tritones"])

    def test_crossing_and_temporal_overlap_are_distinct(self):
        crossing = audit_score(score_from_frames([[60, 67, 64, 48]]))
        self.assertFalse(crossing["checks"]["no_crossing"])
        overlap = audit_score(score_from_frames([[72, 67, 64, 48], [79, 74, 64, 48]]))
        self.assertTrue(overlap["checks"]["no_crossing"])
        self.assertFalse(overlap["checks"]["adjacent_voice_overlap"])

    def test_pitch_mutations_violate_range_scale_and_tritone_rules(self):
        score = score_from_frames([[72, 67, 64, 48]] * 3, ranges=[[60, 76], [55, 77], [48, 69], [36, 64]])
        baseline = audit_score(score)
        self.assertTrue(baseline["passed"])
        range_mutation = copy.deepcopy(score)
        range_mutation["voices"]["s"][0]["pitch"] = 84
        self.assertFalse(audit_score(range_mutation)["checks"]["ranges"])
        scale_mutation = copy.deepcopy(score)
        scale_mutation["voices"]["s"][0]["pitch"] = 73
        self.assertFalse(audit_score(scale_mutation)["checks"]["allowed_pitch_classes"])
        tritone_mutation = copy.deepcopy(score)
        tritone_mutation["voices"]["s"][0]["pitch"] = 70  # B-flat against tenor E
        self.assertFalse(audit_score(tritone_mutation)["checks"]["licensed_harmonic_tritones"])

    def test_independence_requires_changed_pitch_not_reattack_or_entry(self):
        score = score_from_frames([[72, 67, 64, 48]] * 4, require_independence=True, min_independent_changes=1)
        score["voices"]["s"] = [{"start": 0, "dur": 2, "pitch": 72}, {"start": 2, "dur": 2, "pitch": 72}]
        report = audit_score(score)
        self.assertFalse(report["checks"]["rhythmic_independence"])
        self.assertEqual(report["independence_matrix"][0], [0, 0, 0, 0])
        score["voices"]["s"][1]["pitch"] = 74
        report = audit_score(score)
        self.assertEqual(report["independence_matrix"][0], [0, 1, 1, 1])
        score["voices"]["s"][0]["dur"] = 1  # a rest before the second note
        self.assertEqual(audit_score(score)["independence_matrix"][0], [0, 0, 0, 0])

    def test_hold_end_boundary_is_not_independent(self):
        score = score_from_frames([[72, 67, 64, 48], [74, 69, 65, 50]], require_independence=True, min_independent_changes=1)
        report = audit_score(score)
        self.assertEqual(report["independence_matrix"], [[0] * 4 for _ in range(4)])
        self.assertFalse(report["checks"]["rhythmic_independence"])

    def test_independence_needs_one_witness_voice_not_union_of_different_holds(self):
        score = score_from_frames([[72, 67, 64, 48]] * 4, require_independence=True)
        score["voices"]["s"] = [{"start": 0, "dur": 1, "pitch": 72}, {"start": 1, "dur": 1, "pitch": 74}, {"start": 2, "dur": 2, "pitch": 72}]
        score["voices"]["a"] = [{"start": 0, "dur": 2, "pitch": 67}, {"start": 2, "dur": 2, "pitch": 67}]
        score["voices"]["t"] = [{"start": 0, "dur": 1, "pitch": 64}, {"start": 1, "dur": 3, "pitch": 64}]
        score["voices"]["b"] = [{"start": i, "dur": 1, "pitch": 48} for i in range(4)]
        report = audit_score(score)
        self.assertEqual(report["independence_matrix"][0], [0, 1, 1, 0])
        self.assertTrue(any(e["voice"] == "s" for e in report["errors"] if e["check"] == "rhythmic_independence"))


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.score = score_from_frames([[72, 67, 64, 48]] * 4)

    def test_every_required_config_field_is_required(self):
        for key in self.score["config"]:
            score = copy.deepcopy(self.score)
            del score["config"][key]
            with self.subTest(key=key):
                self.assertFalse(audit_score(score)["passed"])
                self.assertFalse(audit_score(score)["checks"]["schema_valid"])

    def test_bad_parameters_are_errors_not_coercions(self):
        for key, value in (
            ("total_ticks", True), ("total_ticks", 0), ("ticks_per_quarter", 1.0),
            ("pulse_stride", 0), ("pulse_offset", 2), ("pulse_offset", -1),
            ("tonic_pc", 12), ("tonic_third", 5), ("tritone_max_wait", 0),
            ("require_independence", 1), ("min_independent_changes", 0),
            ("allowed_pcs", []), ("allowed_pcs", [0, True]), ("allowed_pcs", [12]),
            ("ranges", [[60, 59]] * 4), ("ranges", [[1, 128]] * 4), ("ranges", [[1, 127]] * 3),
            ("max_leaps", [7, 7, 7, False]), ("max_leaps", [7, 7, 7, 0]),
        ):
            score = copy.deepcopy(self.score)
            score["config"][key] = value
            with self.subTest(key=key, value=value):
                self.assertFalse(audit_score(score)["checks"]["schema_valid"])

    def test_malformed_notes_and_voice_keys_are_rejected(self):
        for note in (
            None, {}, {"start": "0", "dur": 2, "pitch": 72},
            {"start": True, "dur": 2, "pitch": 72}, {"start": 0, "dur": 0, "pitch": 72},
            {"start": -1, "dur": 2, "pitch": 72}, {"start": 3, "dur": 2, "pitch": 72},
            {"start": 0, "dur": 2, "pitch": 0}, {"start": 0, "dur": 2, "pitch": 128},
        ):
            score = copy.deepcopy(self.score)
            score["voices"]["s"] = [note]
            with self.subTest(note=note):
                self.assertFalse(audit_score(score)["checks"]["schema_valid"])
        for voice_mutation in (None, {"s": []}, {**self.score["voices"], "extra": []}):
            score = copy.deepcopy(self.score)
            score["voices"] = voice_mutation
            self.assertFalse(audit_score(score)["passed"])

    def test_overlapping_and_unsorted_events_are_rejected(self):
        for notes in (
            [{"start": 0, "dur": 3, "pitch": 72}, {"start": 2, "dur": 2, "pitch": 74}],
            [{"start": 2, "dur": 2, "pitch": 74}, {"start": 0, "dur": 2, "pitch": 72}],
        ):
            score = copy.deepcopy(self.score)
            score["voices"]["s"] = notes
            self.assertTrue(any("nonoverlapping" in e["message"] for e in validate_score(score)))

    def test_exact_end_boundary_and_midi_extremes_are_valid(self):
        score = score_from_frames([[127, 100, 50, 1]], allowed_pcs=list(range(12)))
        self.assertEqual(validate_score(score), [])

    def test_cli_writes_report_and_failure_exit_status(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "score.json"
            output = Path(directory) / "report.json"
            path.write_text(json.dumps(self.score))
            result = subprocess.run([sys.executable, str(ROOT / "audit.py"), str(path), "--out", str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(output.read_text())["passed"])
            self.score["voices"]["s"][0]["pitch"] = 0
            path.write_text(json.dumps(self.score))
            result = subprocess.run([sys.executable, str(ROOT / "audit.py"), str(path), "--out", str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(json.loads(output.read_text())["passed"])
            path.write_text("not json")
            result = subprocess.run([sys.executable, str(ROOT / "audit.py"), str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(json.loads(result.stdout)["passed"])


if __name__ == "__main__":
    unittest.main()
