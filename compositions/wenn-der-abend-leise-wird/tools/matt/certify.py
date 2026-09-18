"""Emit a self-contained Lean certificate for arbitrary validated SATB data.

Emission is not proof checking. Run Lean on the output, or pass --check.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from audit import audit_score


def lean_list(values):
    return "[" + ", ".join(map(str, values)) + "]"


def certificate_text(score: dict) -> str:
    report = audit_score(score)
    if not report["passed"]:
        failed = [name for name, passed in report["checks"].items() if not passed]
        raise ValueError("Refusing to certify a failed audit: " + ", ".join(failed))
    c = score["config"]
    names = {
        "totalTicks": "total_ticks", "ticksPerQuarter": "ticks_per_quarter",
        "tonicPc": "tonic_pc", "tonicThird": "tonic_third",
        "pulseStride": "pulse_stride", "pulseOffset": "pulse_offset",
        "tritoneMaxWait": "tritone_max_wait",
        "minIndependentChanges": "min_independent_changes",
    }
    fields = [f"  {lean_name} := {c[json_name]}" for lean_name, json_name in names.items()]
    fields += [
        f"  allowedPcs := {lean_list(c['allowed_pcs'])}",
        "  ranges := [" + ", ".join(f"({lo}, {hi})" for lo, hi in c["ranges"]) + "]",
        f"  maxLeaps := {lean_list(c['max_leaps'])}",
        "  requireIndependence := " + str(c["require_independence"]).lower(),
    ]
    parts = []
    for name in "satb":
        notes = ",\n    ".join(
            f"⟨{n['start']}, {n['dur']}, {n['pitch']}⟩" for n in score["voices"][name]
        )
        parts.append(f"  {name} := [{notes}]")
    core = Path(__file__).with_name("Counterpoint.lean").read_text(encoding="utf-8")
    return (core + "\n\n-- Generated from audited input; run Lean to verify.\n"
            "set_option maxRecDepth 100000\n"
            "set_option maxHeartbeats 0\n"
            "namespace Certificate\nopen Counterpoint\n\n"
            "def config : Config := {\n" + "\n".join(fields) + "\n}\n\n"
            "def voices : Voices := {\n" + "\n".join(parts) + "\n}\n\n"
            "theorem config_valid : validConfig config = true := by decide\n"
            "theorem accepted : certified config voices = true := by decide\n\n"
            "#print axioms config_valid\n#print axioms accepted\n"
            "end Certificate\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("score", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--check", action="store_true", help="Also run the Lean compiler")
    parser.add_argument("--lean", default="lean", help="Lean executable for --check")
    args = parser.parse_args()
    try:
        score = json.loads(args.score.read_text(encoding="utf-8"))
        text = certificate_text(score)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        if args.check:
            result = subprocess.run([args.lean, str(args.out.resolve())], check=False)
            if result.returncode:
                print("Lean rejected the certificate; it is not verified.", file=sys.stderr)
                return result.returncode
            print(f"Lean verified {args.out}")
        else:
            print(f"Wrote {args.out}; proof verification requires running Lean.")
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
