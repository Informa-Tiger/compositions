# Polyphony and counterpoint: reusable rules, generator, and Lean certificates

A tune-independent extraction of the four-voice chorale experiment. Supply musical material and policy parameters in JSON; compose with Python, audit independently, and certify the exact result in Lean. No chorale theme or G-major key is hard-coded into the core.

Read **[PROCEDURE_AND_RULES.md](PROCEDURE_AND_RULES.md)** for the general musical procedure and exact scope. **[JOB_FORMAT.md](JOB_FORMAT.md)** describes composition inputs; **[SCORE_FORMAT.md](SCORE_FORMAT.md)** describes arbitrary scores accepted by the checker.

## Quick start

Requirements: Python 3.10 or newer, NumPy as pinned in `requirements.txt`, and Lean 4.34.0. The Python auditor, certificate writer, and MIDI exporter use only the standard library. Run commands from this folder. If you use elan, `lean-toolchain` selects the tested Lean release; otherwise use your Lean executable explicitly.

```sh
python3 -m pip install -r requirements.txt
python3 compose.py examples/study_c_major_job.json --out build/study.json --beam 300
python3 audit.py build/study.json --out build/audit.json
python3 certify.py build/study.json --out build/Certificate.lean --check
python3 midi.py build/study.json --out build/study.mid --tempo 84
```

`--check` runs `lean` and fails if Lean rejects the generated certificate. To choose a particular compiler, add `--lean /path/to/lean`. Without `--check`, `certify.py` only emits the source and explicitly reports that compilation remains necessary:

```sh
python3 certify.py build/study.json --out build/Certificate.lean
lean build/Certificate.lean
```

The certificate embeds both the general definitions and the actual notes. Successful compilation reports that its two named theorems depend on no axioms. It does not prove that the Python search, MIDI writer, or input transcription is correct; it directly checks the embedded music under the embedded policy.

## Bring your own material

Copy one of the example job files. Set the key, allowed pitch classes, voice ranges, timing, fixed melody, and desired rests/entries. Adjust the activity schedule and chord plan. Then run the same commands on that job. The synthetic C-major and D-major studies are small demonstrations, not templates requiring those keys or those tunes.

For already composed music, bypass the generator: create a score JSON with four event streams, then run `audit.py`, `certify.py`, and `midi.py`. This lets the same counterpoint rules check music written by hand or by another program.

The MIDI contains a conductor track and four separate voice tracks, preserving rests, durations, and repeated articulations. `--program 19` is the default church-organ sound using zero-based General MIDI numbering. Import it into a DAW or notation program for listening, engraving, or MP3 export. This reusable package does not include a general PDF engraver or audio synthesizer.

## Files and responsibilities

| File | Role |
|---|---|
| `Counterpoint.lean` | General rule definitions and the `certified` acceptance predicate |
| `compose.py` | Configurable bounded beam search; no silent rule relaxation |
| `audit.py` | Independent reconstruction and detailed Python checks |
| `certify.py` | Embed the accepted configuration/notes into a standalone Lean source |
| `midi.py` | Export the audited score as a Type-1 MIDI file |
| `examples/` | Input jobs, accepted note data, MIDI studies, and compiled proof sources |
| `tests/` | Positive examples and deliberately invalid counterexamples |
| `evidence/` | Test/compiler logs and validation report from this release |
| `SHA256SUMS.json` | Hashes of the other delivered files |

## Run the checks

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
lean -o Counterpoint.olean Counterpoint.lean
LEAN_PATH=. lean tests/Rules.lean
lean examples/StudyCMajor.lean
lean examples/StudyDMajor.lean
lean examples/StudyAMinor.lean
lean examples/CadenceCMajor.lean
```

The third command uses POSIX shell syntax. On other shells, set the environment variable `LEAN_PATH` to the package directory before invoking Lean on `tests/Rules.lean`. The standalone example certificates require no local module build or custom Lean path.

The A-minor study also requires rhythmic independence. The four-tick C-major cadence example explicitly disables that requirement to isolate the permitted tritone resolution.

## Boundaries of this version

The formal rules cover all six voice pairs at actual ticks, a declared pulse, and alternating staggered attacks. They include a narrow, tonic-relative V6/5-to-I tritone exception and an optional measurable independence requirement. Direct perfect intervals are prohibited even on stepwise approaches and in inner voices.

The generator uses a small consonant-triad vocabulary plus planned V6/5 cadences. It has no general suspension/passing-note grammar and no automatic modulation. Python maximum-leap and voice-overlap checks are additional audits, not Lean theorems. Costs, activity schedules, theme choices, and cadence plans shape the generated music but do not constitute a proof of Bach's style.

Search failure means this bounded search did not find an accepted result. It is not a proof that the musical request is impossible. The included final note data are the stable examples; numerical-library or platform differences can affect which equal-cost history a new search selects.
