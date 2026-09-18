# Reusable polyphony and counterpoint toolkit

This package separates a configurable four-voice composition experiment into three jobs: choose musical material, search for compatible voices, and certify explicit properties of the resulting notes. It contains no built-in chorale melody. Use it with your own tune, subject entries, rests, key, registers, and timing.

The policy is deliberately strict, following Matt's requested rules. It is not a complete formalization of Bach's practice, Fux's species counterpoint, or Fenaroli's partimento rules. A successful certificate establishes the listed finite predicates, not stylistic quality.

## A general composition procedure

1. **Choose a time grid.** Represent all onsets and durations as nonnegative integer ticks. Set `ticks_per_quarter` to 2 for an eighth-note grid, 4 for sixteenths, or another exact resolution. Preserve the melody's original rhythmic proportions; multiply its durations if you want an augmented cantus. The model does not infer meter or phrasing from a tune.
2. **Declare your tonal vocabulary.** Choose a tonic pitch class, a major or minor tonic third, allowed pitch classes, and SATB registers. These are input data. The built-in tritone exception resolves to that one tonic; modulation requires an extension with explicit, locally scoped tonal regions.
3. **Design independence before harmonizing.** Put the main tune in a voice, identify a short subject, and specify any exact imitative entries. Offset entrances, leave rests for later reentry, and plan which voice should be active during each phrase. Alternate long notes with shorter counterpoint; merely rearticulating every voice together does not create independence.
4. **Fix what must remain recognizable.** Supply immutable note events for the tune and literal subject entries. Subject transposition and entry time are musical choices. The engine must fail if these collide with a rest or another incompatible fixed note; it must never quietly alter the theme to satisfy a rule.
5. **Search among legal continuations.** At each tick, enumerate sonorities within the declared registers and chord vocabulary. Reject forbidden voice leading against the previous sounding state, the selected slower pulse, and pairwise staggered motion. Keep several candidate histories so an attractive local choice does not unnecessarily block a later cadence. A finite beam is a heuristic: exhausting it does not prove no composition exists.
6. **Use preferences to shape music.** Prefer short melodic motion, comfortable spacing, held countervoices against a moving part, and a bass with a coherent line. Costs and activity schedules influence the result; they are not laws of counterpoint. Listen, revise the musical plan, and rerun the search when the result is monotonous or incoherent.
7. **Audit the exact events independently.** Reconstruct held notes and rests from the event lists. Inspect each failed predicate and its location. Resolve a failure musically or explicitly change the documented policy. Do not suppress the failing test or change its definition merely to claim success.
8. **Generate and compile a certificate.** Embed the configuration and exact note events beside the general Lean definitions. Only a successful Lean run establishes the theorem. Keep the certified JSON and certificate together; any changed pitch, duration, rest, or rule requires a new audit and certificate.
9. **Export and listen.** Export the accepted event data to MIDI, import it into a notation program or DAW, and inspect the individual parts. Check rendered notation and any subsequent edits against the certified events. The theorem does not cover a notation application or audio renderer.

## The musical data model

There are four ordered voices, `s`, `a`, `t`, and `b`. Each contains events of the form:

```json
{"start": 4, "dur": 3, "pitch": 67}
```

That note sounds from tick 4 up to, but excluding, tick 7. A rest is a gap between events, not a special pitch. Pitches in this model are MIDI integers 1–127. Events must be ordered, have positive durations, be nonoverlapping within a voice, and end no later than `total_ticks`. Every voice must contain at least one note. Unisons between different voices are permitted.

Enharmonic spelling is not represented. A tritone means six semitones modulo twelve; a fifth means seven, including compound fifths. This abstraction cannot distinguish an augmented fourth from a diminished fifth by notation.

## Exact counterpoint policy

For a sounding upper/lower pair, let the earlier pitches be `u, l` and the later pitches be `u', l'`. Similar motion means that both pitches move strictly upward or both strictly downward. Held notes have zero motion and do not count as similar motion.

| Rule | Implemented meaning |
|---|---|
| No parallel fifths/octaves | Similar motion from interval class 7 to 7, or 0 to 0. Class 0 includes unisons and compound octaves. |
| No direct fifths/octaves | Any similar-motion arrival at class 7 or 0, whether the approach is by step or leap. Applies to all six voice pairs. |
| No battuta | The upper voice descends and the lower ascends into class 0. This conservative project definition is stricter than some historical usages. |
| No crossing | Every sounding upper part is at least as high as every sounding lower part in SATB order. |
| Registers and scale | Each sounding pitch lies within that voice's configured inclusive range and the configured pitch-class collection. |
| No melodic tritone | Two consecutive notes without an intervening rest may not differ by class 6. A genuine gap breaks that continuity check; repeated articulation does not. |
| Harmonic tritones restricted | Every sounding tritone must belong to the complete, tonic-relative V6/5 sonority and resolve as specified below. |
| Measurable rhythmic independence | When enabled, every voice must make at least the configured number of pitch-changing attacks inside held notes of at least one other voice. A new entry from silence or a repeated pitch does not count. |

The direct-perfect ban already implies the parallel-perfect ban in this model; both predicates are kept so their meanings and failures can be inspected separately.

### Timing levels

The perfect-interval and battuta checks operate at three levels:

- **Actual sounding states:** every adjacent tick, including sustained pitches.
- **Declared pulse:** ticks satisfying `tick % pulse_stride == pulse_offset`. For eighth-note ticks, stride 2 and offset 0 give quarter-note snapshots. This is a specified reduction, not a claim about every possible harmonic reduction.
- **Staggered motion:** project the timeline onto each voice pair, remove unchanged pair states, and inspect alternating single-voice movements. If one voice moves and then the other, their combined endpoints may not conceal a direct perfect arrival or battuta.

A pair rule needs both voices sounding at both endpoints. Rests therefore break the relevant obligation. This is an explicit modeling choice; it does not prove that any rest makes every larger-scale contrapuntal relationship acceptable. Very sparse pulse settings can omit much of the music: choose and inspect them deliberately.

### The permitted 6/dim5/3 → 5/3 tritone resolution

Let the tonic pitch class be `T`, and the tonic third be 4 semitones for major or 3 for minor. A licensed dominant seventh in first inversion has:

- Bass pitch class `T + 11`.
- Exactly the pitch classes `T + {11, 2, 5, 7}` modulo 12.
- A complete tonic triad, `T + {0, tonic_third, 7}`, with tonic in the bass, reached within `tritone_max_wait` ticks.
- Every occurrence of the leading tone (`T + 11`) held in its original voice and at its exact original pitch until it rises one semitone to the tonic.
- Every occurrence of the chordal seventh (`T + 5`) similarly held until it descends to the tonic third: one semitone in major, two in minor.
- The two critical resolutions occur together. Premature resolution, intervening rests, swapping the critical notes between voices, or leaving and returning to a critical pitch do not satisfy this exception.

All other harmonic tritones are rejected. Thus, for example, the model does not automatically license every dominant-seventh inversion, diminished chord, modulation, or chromatic sequence. Extend the named exception and its tests if you intentionally want more vocabulary.

## What is proved, audited, or merely preferred

**Lean's `certified` predicate** checks valid configuration, valid note streams, the three levels of perfect-interval/battuta restrictions, no crossing, ranges, allowed pitch classes, melodic tritones, the harmonic-tritone exception, and the optional independence requirement. The formal timeline is reconstructed directly from the supplied notes.

**Python additionally checks** configured melodic leap limits and adjacent-voice overlap. These two properties are not conjuncts of the Lean certificate in this version. A passing Python audit is required before the certificate writer or MIDI exporter proceeds.

**The composition search additionally restricts** its chord vocabulary, fixed material, spacing, rests, and planned activity. Those generator choices are not automatically properties of every arbitrary score accepted by the checker. In particular, this core does not give a complete classification or treatment of nonchord tones. The reusable generator uses consonant triads and the explicitly licensed V6/5 option. The earlier chorale experiment's broader ornamental-note heuristics have not been promoted into a claimed general dissonance grammar.

**Neither system establishes** harmonic function by listening, phrase quality, good text setting, stylistic authenticity, every structural reduction, or aesthetic success. A chord progression can satisfy these predicates and still need substantial musical revision.

The general Lean helpers `subjectAt` and `hasReentry` are available for additional, piece-specific theorems. Their presence does not mean every generated certificate asserts a subject recurrence or a reentry; the default certificate proves the core policy only.

## Reusing and extending the code

Start with an example job and replace its fixed notes, not with an edit to the engine's source. All durations and entry times use the same tick unit. If you transpose a study, transpose its actual pitches, allowed pitch classes, tonic, and register limits consistently. Do not copy a completed certificate onto a different score.

To add a new exception, define precisely its triggering sonority, permitted voices, preparation if needed, resolution interval and direction, maximum delay, and behavior across rests. Add a positive example and negative controls that differ in only the relevant detail. Implement the same specification independently in Python and Lean, then recompile the certificate. Keep stricter or more permissive policies named and documented instead of silently weakening an existing rule.

For longer or more chromatic work, useful future extensions include local tonal regions, spelled pitches, explicit suspension/passing/neighbor-note categories, text accents, and phrase-level cadence requirements. Those are extension points, not existing capabilities.

See `README.md` for commands, `JOB_FORMAT.md` for the generator's inputs, and `SCORE_FORMAT.md` for the checker's inputs.
