"""Generator regressions: real search, constraint preservation and honest failure."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from audit import audit_score
from compose import SearchFailure, compose, prepare_job


def job(name="study_c_major_job.json"):
    return json.loads((ROOT / "examples" / name).read_text())


class ComposerTests(unittest.TestCase):
    def test_independent_c_and_d_studies_and_transposition(self):
        c = compose(job(), beam=300)
        d = compose(job("study_d_major_job.json"), beam=300)
        for score in (c, d):
            report = audit_score(score)
            self.assertTrue(report["passed"], report["errors"])
            self.assertTrue(all(max(row) >= 2 for row in report["independence_matrix"]))
            self.assertGreater(len({n["dur"] for n in score["voices"]["a"]}), 1)
        for v in "satb":
            transposed = [dict(n, pitch=n["pitch"] + 2) for n in c["voices"][v]]
            self.assertEqual(transposed, d["voices"][v])
        self.assertEqual(c["voices"]["s"], job()["fixed_notes"]["s"])

    def test_a_minor_study_uses_minor_third_and_leading_note(self):
        result = compose(job("study_a_minor_job.json"), beam=300)
        self.assertTrue(audit_score(result)["passed"])
        self.assertEqual(result["config"]["tonic_third"], 3)
        self.assertIn(8, result["config"]["allowed_pcs"])
        self.assertEqual(result["voices"]["s"], job("study_a_minor_job.json")["fixed_notes"]["s"])

    def test_overlapping_fixed_notes_fail(self):
        spec = job()
        spec["fixed_notes"]["s"].append(dict(start=1, dur=1, pitch=72))
        with self.assertRaisesRegex(ValueError, "Overlapping"):
            prepare_job(spec)

    def test_fixed_note_rest_conflict_fails(self):
        spec = job()
        spec["rests"] = {"s": [[1, 2]]}
        with self.assertRaisesRegex(ValueError, "overlapping rest"):
            prepare_job(spec)

    def test_contradictory_normal_and_v65_plans_fail(self):
        for order in (("I", "V65"), ("V65", "I")):
            spec = job()
            spec["chord_plan"] = [dict(start=0, end=2, chords=[name]) for name in order]
            with self.assertRaisesRegex(ValueError, "Contradictory chord plan"):
                prepare_job(spec)

    def test_incompatible_cadence_and_plan_fail(self):
        spec = job("cadence_c_major_job.json")
        spec["chord_plan"] = [dict(start=0, end=2, chords=["I"])]
        with self.assertRaisesRegex(ValueError, "contradicts"):
            prepare_job(spec)

    def test_cluster_is_not_accepted_as_triad(self):
        spec = job()
        spec["chords"] = [dict(name="cluster", pcs=[0, 1, 2])]
        with self.assertRaisesRegex(ValueError, "major/minor triads"):
            prepare_job(spec)

    def test_non_boolean_complete_flag_fails(self):
        spec = job()
        spec["chord_plan"][0]["complete"] = "false"
        with self.assertRaisesRegex(ValueError, "Boolean"):
            prepare_job(spec)

    def test_motif_expands_with_transposition_and_augmentation(self):
        spec = job()
        spec["motifs"] = {"cell": [dict(pitch=72, dur=1), dict(pitch=76, dur=1)]}
        spec["entries"] = [dict(motif="cell", voice="t", start=0, transpose=-12, duration_scale=2)]
        result = compose(spec, beam=300)
        self.assertTrue(audit_score(result)["passed"])
        self.assertIn(dict(start=0, dur=2, pitch=60), result["voices"]["t"])
        self.assertIn(dict(start=2, dur=2, pitch=64), result["voices"]["t"])

    def test_requested_rest_is_preserved(self):
        spec = job()
        spec["rests"] = {"a": [[0, 2]]}
        result = compose(spec, beam=300)
        self.assertTrue(audit_score(result)["passed"])
        self.assertEqual(result["voices"]["a"][0]["start"], 2)

    def test_planned_v65_critical_voices_hold_and_resolve(self):
        result = compose(job("cadence_c_major_job.json"), beam=300)
        report = audit_score(result)
        self.assertTrue(report["passed"], report["errors"])
        self.assertEqual(report["harmonic_tritone_ticks"], [0, 1])
        self.assertEqual(result["voices"]["a"], [dict(start=0, dur=2, pitch=65), dict(start=2, dur=2, pitch=64)])
        self.assertEqual(result["voices"]["b"], [dict(start=0, dur=2, pitch=47), dict(start=2, dur=2, pitch=48)])

    def test_forced_parallel_octaves_are_bounded_search_failure(self):
        spec = job()
        spec["config"]["total_ticks"] = 2
        spec["config"]["require_independence"] = False
        spec["fixed_notes"] = {
            "s": [dict(start=0, dur=1, pitch=72), dict(start=1, dur=1, pitch=74)],
            "b": [dict(start=0, dur=1, pitch=48), dict(start=1, dur=1, pitch=50)]}
        spec.pop("chord_plan")
        spec.pop("activity")
        with self.assertRaisesRegex(SearchFailure, "Constraints were not relaxed"):
            compose(spec, beam=300)

    def test_fixed_note_outside_key_fails_without_correction(self):
        spec = job()
        spec["fixed_notes"]["s"][0]["pitch"] = 73
        with self.assertRaisesRegex(ValueError, "outside key/register"):
            prepare_job(spec)


if __name__ == "__main__":
    unittest.main()
