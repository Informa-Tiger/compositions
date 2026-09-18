# Validation of this toolkit release

- Python 3.12.9, NumPy 2.2.3, Lean 4.34.0 on macOS arm64.
- 43 Python regression/integration tests passed, including contradictory input plans, fixed-note preservation, direct and staggered perfect intervals, cadence hold/resolution mutations, rhythmic independence, invalid configurations, certificate refusal, and MIDI event ordering.
- 66 Lean rule fixtures compiled successfully using ordinary `by decide`.
- Four standalone certificates compiled: C-major and D-major independent-voice studies, an A-minor independent-voice study, and a four-tick C-major V6/5-to-I example. Both named theorems in every certificate report no axiom dependencies.
- The cadence micro-example deliberately sets `require_independence=false`; all three longer studies set it true.
- All four score JSONs pass the independent audit. Each embedded certificate was compared with its exact score/configuration and the current core definitions.
- All four MIDI files were independently parsed with music21 and matched every pitch, onset, and duration in the score data. The runtime toolkit does not require music21; it was used only for this release check.

The logs and JSON reports in this folder retain the evidence. Compiler paths in logs are normalized to `lean` for portability. These checks support the documented finite policy and export fidelity; they do not establish a complete historical counterpoint grammar or musical quality.
