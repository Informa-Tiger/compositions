# Composition JSON, version 1

This format separates musical decisions from exporters. The editable source is in `versions/`; the generated snapshot contains those same fields plus optional `playback`, a cache that the browser independently regenerates and the Python verifier checks.

Version 1 covers this project's four-voice, G-major, 3/4 works. It is deliberately scoped: other keys/meters, changing meters and more voices require extending the schema, renderer and checks together. It is not a replacement for MusicXML as a general notation interchange format.

- `format: "composition"`, `schemaVersion: 1`, `id`, `version`: stable identity and format version.
- `title`, `subtitle`, `composer`, `tuneCredit`, `revision`: presentation and provenance.
- `voices`: ordered high to low; name, short name, clef, color, zero-based General MIDI program, pan, volume and base velocity.
- `measures`: ordered measures, each containing four voice arrays. Each note has `pitch` (e.g. `F#4`, `B-3`, or `R` for rest) and `duration` in quarter-note units, stored as an exact decimal string. No floating-point seconds are authored. Supported values are sixteenth through dotted-half durations. Each voice must fill the measure exactly.
- `ties`: `{ "voice": 1, "beat": "36" }` joins the note beginning at absolute quarter-beat 36 to its immediately preceding identical pitch. Beats are zero-based from the start; voice indexes are zero-based. Ties are checked for contiguity and pitch equality.
- `tempos`: `{ "bar": 1, "bpm": 88 }`; one-based bars, quarter-note BPM, applies until the next change. Cadential slowing is represented explicitly. A final fermata is visual; its intended duration is encoded in tempo and note duration rather than an undocumented renderer delay.
- `sections`: one-based bar and display name.
- `cantus`: voice index, start/end quarter-beats (end exclusive), label. These spans set the white outlines and a specified velocity boost.
- `engraving`: staff size, explicit page breaks, system cadence, final fermata, tempo text and footer. Version 1 uses A4 with fixed page margins.
- `render`: relative SoundFont path and content hash, gain, sample rate, reverb/chorus, articulation, loudness normalization, fade and encoding settings; video dimensions, frame rate and view window.
- `playback` (generated only): sounding events after ties are merged, beat/second maps, section times and voice colors. Rests remain in the source but produce no sounding event.

`composition.json`, `composition.mp3`, `composition.pdf`, etc. share one basename. A generated folder is a self-contained set of music and media; its `index.html` opens the repository's shared player. Serve the repository root or the staged site over HTTP. To share a version outside this repository, send its JSON and MP3 and open them in the shared player.

Python validates the JSON Schema and additional musical invariants. The browser validates the subset needed for playback and computes notes/timing itself. `node tools/check-player.mjs` compares the browser derivation with the Python derivation for every version and exercises invalid-duration rejection.
