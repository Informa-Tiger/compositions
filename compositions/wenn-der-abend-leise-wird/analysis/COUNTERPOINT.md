# Final musical review

I am satisfied with the current version as a tonal, Bach-inspired chorale fantasia. This is an editorial judgment about the specific score, supported by the checks below; it is not a theorem of historical authenticity or aesthetic equivalence to Bach.

## What I revised in the last pass

I simplified ornaments that obscured their own resolutions instead of adding more activity. The accompaniment to the source C in m.18 now supplies a consonant C/E sonority. The m.8 preparation is a clear descending 9–8 figure over the dominant rather than a simultaneous 9/7/4 cluster. The alto descents in mm.39 and 43 now articulate G–F#–E–D; their accented 9–8 figures resolve within half a beat. The tenor return at m.37 enters over a deliberate deceptive D7–E-minor resolution, with the two tendency notes resolving in their original voices. A sustained alto E in m.41 provides contrast with the moving cantus and soprano, without the earlier displaced fifths. The final D7 resolves C–B and F#–G explicitly, then a held tenor G carries the quiet plagal afterthought.

## Nonchord notes and tendency tones

The harmonic plan is explicit in `../tools/harmonic_review.py`, rather than being inferred from whatever notes happen to sound. Every note after the initial monophonic subject is either part of that declared chord or has a listed treatment. There are **53 nonchord-note events**: passing notes, returning neighbours, three upper appoggiaturas, a dominant anticipation, the early C#–D resolution in m.20, and the prepared/cadential suspensions. Each has a bounded consonant destination. See [the complete list](../generated/v003/NONCHORD_TONES.md).

The early m.20 C#–D followed by C–B is retained as a chromatically inflected turn through A7–D7–G: the leading note reaches D before the harmonic change, then C supplies the next chord's seventh. It is an explicitly identified case, not a generic permission for an unresolved leading note.

All 30 harmonic-tritone pair/tick states are accounted for: either a separately checked passing/neighbor figure or dominant tendency notes resolving by step in their original voices within two quarters. The m.36 D7 resolves deceptively to E minor rather than the root-position G demanded by Matt's policy. All four chromatic secondary-leading-note events (C# or D#) rise immediately by semitone. All 30 chordal-seventh voice/tick occurrences descend by step, apart from the one deliberately preserved source-tune C5–F#4–G4 gesture.

These tests check explicit pitches, timing and local note shapes. The chosen harmonic reading and the suitability of an ornament on its beat remain musical judgments, not consequences of the tests.

## Perfect intervals and voice independence

Matt's unmodified auditor reports no instantaneous, quarter-pulse, or staggered parallel fifths/octaves; no crossing or temporal voice overlap; and rhythmic independence in every voice. The original audit additionally finds no actual-event outer direct perfect arrival with a soprano leap. MIDI and MusicXML still reproduce the exact authored events, including the unchanged source tune and tenor quotation.

I retain stepwise outer arrivals, nonparallel inner-pair arrivals, and contrary-motion octaves as part of the declared tonal style. They remain failures under Matt's stronger blanket rules. Every remaining staggered arrival has a specific explanation in the [exception ledger](../generated/v003/FINDINGS.md), such as the cantus arriving on D well before the bass changes harmony beneath it, a checked suspension, or a common tone linking two chords. None is silently waived as a parallel fifth or octave.

Two exposed inward octave arrivals are deliberate: the fixed D–B–D melody over G–B–D bass at m.17, and the fixed phrase-closing A–D over A7–D7 at m.20. Their harmonic/bass shapes and inner-voice resolutions justify retaining them. I do not treat Matt's ban on every contrary-motion octave as a universal tonal rule. The inner alto D–B arrival in m.40 articulates G/B below a sustained soprano. The larger leap implied by its pulse reduction includes an intermediate D in the actual line.

There is just one adjacent-voice unison, lasting an eighth note in m.38: the tenor cantus passes through held alto D4, then the alto opens to F#4. I retain that brief contact; it does not cross or exchange the voices.

## Explicit melodic exceptions

- Source C5–F#4–G4 at m.24: the tune's literal gesture, with the leading note immediately resolving upward.
- G4–E5–D5–C5 into m.33: the sole high E and a major-sixth ascent immediately reversed by step. This gives the episode a shaped high point; it exceeds Matt's fifth-only upper-voice leap bound.

I have no remaining unexplained finding in this review. That does not make the score pass Matt's original predicate: its strict policy still rejects these documented stylistic choices. The regenerated Lean proof confirms that rejection rather than presenting a false acceptance certificate.
