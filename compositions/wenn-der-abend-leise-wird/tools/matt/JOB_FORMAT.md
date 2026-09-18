# Job format and generator behavior

`compose.py` is tune-independent. It imports NumPy and the local `audit.py`; no source melody, filesystem-specific path, G-major constants or Dumpa phrase positions remain in its core. Its CLI is:

```sh
python compose.py examples/study_c_major_job.json --out build/study.json --beam 300
```

The beam width is a search-resource bound. Failure means this run found no acceptable result, not that no solution exists. It never weakens rules to get a result. Every saved result has passed the separately implemented `audit_score`. An audit pass is not a Lean certificate: use `certify.py` and compile its output independently.

## Required job fields

- `config`: the score configuration shown below. It contains `total_ticks`, `ticks_per_quarter`, `tonic_pc`, `tonic_third` (3 or 4), `allowed_pcs`, four inclusive SATB `ranges`, four `max_leaps`, `pulse_stride`, `pulse_offset`, `tritone_max_wait`, `require_independence`, `min_independent_changes`.
- `title` is optional descriptive text.

All pitch values are MIDI numbers; pitch classes are modulo 12; all times/durations are integer ticks. Choose `ticks_per_quarter` according to the desired finest rhythmic grid. An arbitrary melody becomes `fixed_notes.s`, but any of the four voices may contain arbitrary fixed fragments. A fully unspecified voice is also supported.

A minimal configuration block is:

```json
{
  "total_ticks": 24,
  "ticks_per_quarter": 2,
  "tonic_pc": 0,
  "tonic_third": 4,
  "allowed_pcs": [0, 2, 4, 5, 7, 9, 11],
  "ranges": [[67, 79], [60, 72], [52, 67], [40, 55]],
  "max_leaps": [7, 7, 7, 12],
  "pulse_stride": 2,
  "pulse_offset": 0,
  "tritone_max_wait": 2,
  "require_independence": true,
  "min_independent_changes": 2
}
```

Total ticks, ticks per quarter, pulse stride, tritone maximum wait and minimum independence count must be positive integers. Pulse offset is an integer from zero through stride minus one. Tonic pitch class is 0–11; allowed pitch classes are a nonempty list drawn from 0–11. Ranges are exactly four `[low, high]` pairs satisfying `1 <= low <= high <= 127`, in SATB order. Max leaps contains four positive semitone limits in the same order. Pitch 0 is not a note: silence is an absence of events. `require_independence` is a Boolean, not a string. Every emitted voice must contain at least one note; a job that requests an entirely silent voice cannot pass the score audit.

The generator output is a score JSON with `title`, `config`, and a `voices` object containing all four keys `s`, `a`, `t`, `b`. Each voice holds time-ordered, nonoverlapping `{start,dur,pitch}` events within total duration. Durations are positive. The auditor/certifier may accept a score written by any other composition method; the search-specific job fields below are not part of the score format.

## Optional job fields

`fixed_notes`: map voice names `s`, `a`, `t`, `b` to note lists, each note exactly `{ "start": 0, "dur": 4, "pitch": 72 }`. The generator preserves exact pitch, onset and duration, including repeated-pitch attacks. Fixed notes cannot overlap another fixed note, motif event, or requested rest. Notes need not cover the whole score.

`rests`: map voice names to half-open `[start, end]` tick intervals. These are hard silence constraints. Reentry then follows whatever note or motif constraint occupies the next tick. The generator does not invent rests outside these spans.

`motifs`: map arbitrary names to ordered lists of `{ "pitch": 60, "dur": 2 }`. `entries`: list of `{ "motif": "subject", "voice": "t", "start": 4, "transpose": -12, "duration_scale": 2 }`. Entries expand into ordinary fixed notes. `transpose` defaults to zero semitones; `duration_scale` defaults to one and must be a positive integer. This is exact chromatic transposition and integer augmentation, not a tonal-answer algorithm. A transposed note outside `allowed_pcs` or its register is an explicit input error. Motif entry duration follows from its notes; no fixed tune length is assumed.

`chords`: optional list of custom consonant triads, e.g. `{ "name": "I", "pcs": [0,4,7], "bass_pcs": [0,4], "complete": false }`. A custom vocabulary replaces the derived normal vocabulary; the configured tonic triad is added if no chord named `I` is supplied. `I` is reserved for that exact configured tonic triad and `V65` is reserved for the licensed cadence sonority. Triads must contain three distinct pitch classes forming a major or minor triad, with the root listed first (root-relative intervals `{0,4,7}` or `{0,3,7}`). `bass_pcs` restricts inversion and defaults to the first two listed pitch classes; `complete` requires all three classes to sound and defaults to false. To include a second inversion intentionally, include its fifth in `bass_pcs`; the generator does not prove a full six-four-chord grammar.

Without `chords`, it builds diatonic triads from the major scale when `tonic_third=4`, or the harmonic-minor scale when `tonic_third=3`, keeping only major/minor triads wholly included in `allowed_pcs`. Defaults permit root position and first inversion. Diminished/augmented triads are deliberately omitted. Allowed pitch classes are always caller-specified, so harmonic-minor leading notes must be included explicitly.

`chord_plan`: list of `{ "start": 0, "end": 4, "chords": ["I","vi"], "complete": false, "tonic_root_bass": false }`. Spans are half-open. Multiple rows covering a tick intersect their permitted chord names; contradictory plans fail. `complete` additionally requires the full selected chord's pitch-class set; `tonic_root_bass` requires the configured tonic in the actual bass. Those Boolean flags combine by OR. Unplanned ticks allow the normal consonant vocabulary. `V65` is selectable only by an explicit plan or cadence.

`cadences`: list of `{ "start": 18, "resolve": 20, "end": 24 }`. This forces V6/5 during `[start, resolve)` and a complete root-position tonic chord during `[resolve, end)`. V6/5 uses tonic-relative pitch classes `{11,2,5,7}` with degree 7 in the bass. The two critical notes must hold until degree 7 rises one semitone and degree 4 falls to degree 3 simultaneously. The delay cannot exceed `tritone_max_wait`. A cadence conflicts rather than overrides an incompatible chord plan. All direct-perfect/battuta/leap constraints still apply, so a requested cadence may be unachievable for a particular cantus or beam.

`activity`: list of `{ "voice": "a", "start": 0, "end": 24, "period": 2, "offset": 1, "weight": 2.4 }`. Within the half-open span it rewards a pitch change on ticks satisfying `tick % period == offset` and mildly discourages movement on other ticks. Defaults: start zero, end total_ticks, offset zero, weight 1.7. These are soft preferences, not hard rhythm promises; actual independent attacks are required by the separate audit if `require_independence=true`. Use fixed notes when a rhythm must be literal.

`max_spacing`: three positive maximum semitone distances between adjacent sounding voices, default `[12,12,19]`. This is a generation filter, not currently a named Lean theorem.

## Search and exported score

Each tick gets candidate SATB sonorities consistent with fixed notes, rests, registers, allowed pitch classes, chord vocabulary/plan, spacing and no crossing. The vectorized search propagates a limited set of histories, checking instantaneous, pulse-sampled, and staggered-pair direct/parallel-perfect and inward-battuta rules plus melodic-tritone, max-leap, overlap and exact planned tritone-resolution rules. Cost favors compact registers, smaller leaps, configurable rhythmic activity, and missing independent-change counts. It retains up to four histories per current candidate before global beam pruning. This is a heuristic, not an exhaustive solver.

The output contains the ordinary `title`, `config` and `voices` score fields plus a `generation` provenance field with algorithm name, beam width, cost, and harmonic label at each tick. Repeated pitches merge into held notes unless a fixed-note or motif boundary requires a reattack. The independent auditor reconstructs the music from event lists; it does not trust the harmonic labels.

The generator currently uses consonant triadic sonorities, with the one explicitly planned V6/5 exception. It does not generate a general vocabulary of suspensions/passing tones/neighbor tones, automatically choose motives, transform tonal answers, or guarantee Bach style. This is deliberately narrower than the earlier tune-specific experiment's ornamentation code; the general rule checker accepts arbitrary external scores subject to its declared rules and likewise does not certify all historical dissonance grammar. The strong all-pair direct-perfect policy is the user's experiment policy, not a universal historical rule.

## Verified small studies

`examples/study_c_major_job.json` and `study_d_major_job.json` run with `--beam 300` in under a second each on the development machine. Their generated `_score.json` files both pass the independent audit. D major is a complete two-semitone transposition, verifying tonic/register/pitch-class parameters are operational. There are 24 ticks at two ticks per quarter; the fixed soprano is C5–D5–E5–D5–C5–C5 in six two-quarter events for the first study.

The C-major result has note durations S `[4]`, A `[1,2,5,6]`, T `[1,2,3,4,10]`, B `[1,2,4]` ticks. Independence counts against each voice's best held partner are respectively `[4,7,5,6]`, exceeding the configured threshold of two. The samples are short mechanical demonstrations, not a new finished chorale commission.


## Small motif and cadence inputs

Add these fields to a job with suitable nonoverlapping fixed notes and registers:

```json
{
  "motifs": {
    "cell": [{"pitch": 72, "dur": 1}, {"pitch": 76, "dur": 1}]
  },
  "entries": [
    {"motif": "cell", "voice": "t", "start": 0, "transpose": -12, "duration_scale": 2}
  ],
  "rests": {"a": [[0, 2]]}
}
```

This fixes tenor C4 for two ticks followed by E4 for two ticks, and an alto rest for the first two ticks. Each requested entry is a constraint; the search may reject incompatible placements instead of changing the motif.

`examples/cadence_c_major_job.json` provides a four-tick V6/5-to-I demonstration, with soprano D5 for two ticks followed by E5 for two ticks. Its cadence field is `[{"start":0,"resolve":2,"end":4}]`. The generator finds F4–E4 in alto, held G3 in tenor, B2–C3 in bass. Its `require_independence` flag is explicitly false because this two-chord micro-example is for the cadence exception alone; the full C/D studies require independence.


`examples/study_a_minor_job.json` supplies a separate 24-tick harmonic-minor study with fixed A4–B4–C5–B4–A4–A4 soprano and `tonic_third=3`. Its generated score also passes the independent audit with independence required. This tests the minor-mode vocabulary rather than merely transposing the major study.
