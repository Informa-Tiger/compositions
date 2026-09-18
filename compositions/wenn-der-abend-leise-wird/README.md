# Wenn der Abend leise wird

A newly composed four-voice chorale fantasia on **Es wird scho glei dumpa**. G major, 3/4, 48 measures, approximately 1:44 with reverberation. New composition by Codex, September 2026, commissioned and reviewed interactively by the repository owner. Source tune credited to Anton Reidinger (1839–1912).

**[Listen and compare versions](https://informa-tiger.github.io/compositions/player/)** · [Current source](versions/v003.json) · [Current exports](generated/v003/)

## Musical method

The pitches and rhythms were explicitly authored, including the accompanying lines. Python was used to represent, transpose for the tenor quotation, export, render and check those decisions. There was no random note generator, constraint-search composition, or generative-audio model. Matt's supplied accompaniment and generator were not used to compose this work.

The complete source melody appears in soprano at its original durations, rather than augmentation. A walking quarter-note tempo around 88 was chosen; it is a compositional performance choice, not an assertion that the reference score prescribes this tempo. The first two source phrases return an octave lower in tenor. The title and new countervoices belong to this new arrangement, not the source edition.

| Measures | Design |
|---|---|
| 1–8 | Imitative introduction: tenor alone, alto answer, soprano, then bass. The G–G–A–B–D outline comes from the tune. This is not claimed to be a strict fugue exposition. |
| 8 beat 3–28 beat 2 | Complete cantus firmus in soprano, unchanged in pitch and duration. Moving inner parts and changing inversions vary the accompaniment. |
| 29–36 | Minor-colored episode through E minor and A minor, with secondary dominants, an upper-register high point and return toward D. |
| 36 beat 3–44 beat 2 | First two source phrases in tenor, one octave lower. Soprano becomes a countervoice. |
| 45–48 | Cadential 6/4–5/3, dominant resolution, and a quiet plagal afterthought. |

The source C5–F#4–G4 gesture is deliberately retained. The source's identity outweighs a blanket ban on melodic tritones. The episode's G4–E5 ascent reverses through D5–C5, giving the line a shaped high point rather than being removed solely to satisfy a maximum-fifth leap rule.

## Revision and verification

The original audit checked note ranges, crossings, selected perfect-interval progressions, exact source melody and export roundtrips. Its scope was insufficient for a claim of complete counterpoint correctness. We subsequently ran Matt's unchanged auditor, generated a Lean rejection proof using his definitions, revised the music, and added an explicitly authored harmonic analysis.

| Version | Sounding notes | Raw strict findings | Main result |
|---|---:|---:|---|
| v001 | 534 | 210 | Original version; staggered parallels and temporal overlap still present. |
| v002 | 537 | 208 | Repaired staggered parallels, overlap and an avoidable bass tritone; strict stylistic disagreements remained. |
| v003 | 523 | 190 | Simplified unclear ornaments, improved dissonance treatment and voice separation, clarified the tenor return and final cadence. |

The raw count includes repeated ticks and overlapping reductions; it is not a count of independent musical mistakes. The version sources were recovered from the original local Git commits recorded in their metadata; those old commit identifiers document provenance but are not commits in this new public repository.

The current version passes Matt's instantaneous, quarter-pulse and staggered parallel-perfect checks, crossing, adjacent-voice overlap, range and rhythmic-independence checks. All versions reproduce the complete cantus exactly and pass exact MIDI and MusicXML note roundtrips. Browser and Python playback derivations agree.

Under the written harmonic plan, the final version additionally checks:

- 53 nonchord-note events with explicit passing, neighbor, appoggiatura, anticipation or suspension treatment and bounded consonant destinations.
- 30 harmonic-tritone pair/tick states, accounted for by checked ornaments or dominant tendency-tone resolutions.
- Four chromatic leading-note events, each resolving upward by semitone in the same voice.
- 30 chordal-seventh voice/tick occurrences, with the source C–F#–G exception explicitly identified.
- One brief adjacent-voice unison in measure 38, with no voice crossing.

Read [the musical assessment](analysis/COUNTERPOINT.md), [the complete exception ledger](generated/v003/FINDINGS.md), [the nonchord-tone analysis](generated/v003/NONCHORD_TONES.md), and [the raw strict audit](generated/v003/matt-audit.json).

### What remains rejected

The final work still fails the strict checker for direct perfect arrivals, selected contrary-motion octave arrivals, staggered arrivals, its narrow harmonic-tritone license, chromatic notes outside G major, the source melodic tritone, and the expressive sixth. Each final finding has an explicit musical assessment. These are accepted exceptions under our tonal reading, not alterations to Matt's predicate.

The Lean statement is **`certified config voices = false`**, proved with `by decide`, without `sorry` or added axioms. It proves rejection by these definitions, not compositional quality. The broader individual-predicate diagnostic file is supplied but has not been compiled for this version. General dissonance grammar, historical style, phrasing and aesthetic quality are not fully formalized.

The authoring agent judged the final written composition musically defensible after score and harmonic review. It could not directly hear the rendered audio in its session. No specific Bach passage has been verified as a historical precedent for the retained exceptions; “Bach-like” describes the intention, not an established attribution or equivalence.

## Sound and visualization

FluidSynth renders the GeneralUser GS 2.0.3 Church Organ preset, with separate voice channels, restrained pan and volume, modest reverberation and short note separation. FFmpeg normalizes and encodes the result. It is sampled synthesis, not a recorded organist. Tempo, articulation and sound settings live in each version's JSON.

The shared browser player and MP4 use the same sounding events and tempo map. Soprano is gold, alto cyan, tenor violet, bass rose; white outlines identify cantus notes. The player supports version selection, local JSON/MP3 files, measure/time jumps, scrubbing, overview seeking, playback speed and viewing-window controls. Visual inspiration came from a scrolling piano-roll presentation; no reference video or audio was copied.

## Blind audio API experiment

Gemini 2.5 Pro and Flash received the audio with identifying metadata removed and the same neutral prompt. They were not told the title, intended Bach style, score or prior findings. Both recognized organ music. Flash favored Baroque/Neo-Baroque; Pro favored late-Romantic or twentieth-century Neo-Baroque/Neo-Romantic organ writing.

Their detailed reports were unreliable: both invented events beyond the 104.304-second recording and registration changes not present in the MIDI. A separate 20-second WAV test also misidentified the solo opening as multiple simultaneous parts. Their favorable prose is therefore not used as validation. [Reports, prompts, hashes and assessment](analysis/audio-reviews/README.md) are preserved. No Cyanite call was made because no suitable credentials were available. These reviews concern the pre-migration render; that file's hashes are preserved in the reports, rather than being claimed to identify a newly rebuilt file.

## Reproduce

From the repository root:

```sh
python tools/build.py compositions/wenn-der-abend-leise-wird/versions/v003.json
python tools/check.py
node tools/check-player.mjs

# Optional formal rejection proof, with Lean 4.34.0 available
lean compositions/wenn-der-abend-leise-wird/generated/v003/Rejected.lean
```

Matt's original toolkit, tests and examples are in [tools/matt](tools/matt/). The final harmonic and exception-review scripts are alongside it. Build verification reports genuine checker failures without pretending they are build failures; malformed sources or inconsistent exports do fail the build.

For a new editorial revision, copy the current source to `versions/v004.json`, change its `version` and revision description, then edit and rebuild. The final-v003 editorial analysis is deliberately version-specific and must be reviewed for new music rather than blindly reused as a certificate.

## References

See [sources/README.md](sources/README.md) and [../../NOTICE.md](../../NOTICE.md) for tune attribution, public references, and third-party notices.
