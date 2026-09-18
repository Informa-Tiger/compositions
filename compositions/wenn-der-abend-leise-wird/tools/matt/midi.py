"""Export an audited SATB JSON score to a Type-1 Standard MIDI File."""
from __future__ import annotations

import argparse
import json
from math import lcm
from pathlib import Path
import struct
import sys

from audit import audit_score


def vlq(value: int) -> bytes:
    if not 0 <= value <= 0x0FFFFFFF:
        raise ValueError("MIDI delta time is outside the four-byte VLQ range")
    encoded = [value & 127]
    while value >> 7:
        value >>= 7
        encoded.insert(0, (value & 127) | 128)
    return bytes(encoded)


def track(events, total: int) -> bytes:
    payload = bytearray()
    previous = 0
    for tick, priority, message in sorted(events, key=lambda e: (e[0], e[1])):
        payload.extend(vlq(tick - previous))
        payload.extend(message)
        previous = tick
    payload.extend(vlq(total - previous) + b"\xff\x2f\x00")
    return b"MTrk" + struct.pack(">I", len(payload)) + payload


def midi_bytes(score: dict, tempo: float = 84, program: int = 19) -> bytes:
    report = audit_score(score)
    if not report["passed"]:
        raise ValueError("Score failed audit; MIDI export refused")
    if not 4 <= tempo <= 300 or not isinstance(program, int) or not 0 <= program <= 127:
        raise ValueError("Tempo must be 4..300 quarter notes/minute; program must be 0..127")
    quarter_ticks = score["config"]["ticks_per_quarter"]
    ppq = lcm(480, quarter_ticks)
    if ppq > 32767:
        raise ValueError("Tick resolution exceeds Standard MIDI File PPQ capacity")
    factor = ppq // quarter_ticks
    total = score["config"]["total_ticks"] * factor
    micros = round(60_000_000 / tempo)
    conductor = track([(0, 0, b"\xff\x51\x03" + micros.to_bytes(3, "big"))], total)
    tracks = [conductor]
    for channel, (name, label) in enumerate(zip("satb", ("Soprano", "Alto", "Tenor", "Bass"))):
        name_bytes = label.encode("ascii")
        events = [(0, -2, b"\xff\x03" + vlq(len(name_bytes)) + name_bytes),
                  (0, -1, bytes([0xC0 + channel, program]))]
        for n in score["voices"][name]:
            start, end = n["start"] * factor, (n["start"] + n["dur"]) * factor
            # Note-off precedes a repeated pitch's new onset at the same tick.
            events.append((start, 1, bytes([0x90 + channel, n["pitch"], 76])))
            events.append((end, 0, bytes([0x80 + channel, n["pitch"], 0])))
        tracks.append(track(events, total))
    return b"MThd" + struct.pack(">IHHH", 6, 1, 5, ppq) + b"".join(tracks)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("score", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--tempo", type=float, default=84)
    parser.add_argument("--program", type=int, default=19, help="Zero-based GM program (19 = church organ)")
    args = parser.parse_args()
    try:
        data = midi_bytes(json.loads(args.score.read_text()), args.tempo, args.program)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(data)
        print(f"Wrote {args.out}")
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
