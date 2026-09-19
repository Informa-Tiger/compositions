# Compositions

Versioned compositions with inspectable notes, reproducible exports, and a shared audio-synchronized piano-roll player.

**[Listen on GitHub Pages](https://informa-tiger.github.io/compositions/)** · **[Open the player](https://informa-tiger.github.io/compositions/player/)**

The first work is [Wenn der Abend leise wird](compositions/wenn-der-abend-leise-wird/README.md), a four-voice chorale fantasia on *Es wird scho glei dumpa*. Its composition folder contains the source versions, methods, references, supplied counterpoint toolkit, analyses, and one generated folder per version.

## Source and outputs

`compositions/<piece>/versions/vNNN.json` is the editable source of truth. `generated/vNNN/composition.json` contains an exact source snapshot plus a derived playback cache. Notes, durations, ties, tempos, voice metadata, cantus spans, engraving and rendering settings all live in the source. Exporters make no compositional choices.

Each generated version includes MusicXML, LilyPond, score PDF, exact MIDI, articulated performance MIDI, MP3, piano-roll MP4, preview image, a player entry page, verification results, and an artifact-hash manifest. The shared player derives playback directly from the source fields, so it can also load the smaller editable source JSON.

See [the format specification](schema/README.md) and [the composition's methods and results](compositions/wenn-der-abend-leise-wird/README.md).

## Build

Requires Python 3.13, LilyPond 2.26, FluidSynth 2.6, FFmpeg, and a system Arial/Georgia or DejaVu font installation. The licensed GeneralUser GS SoundFont is included beside the composition. Python dependencies are pinned. The manifest records external renderer versions; audio/engraving can differ slightly between tool versions and fonts.

```sh
# macOS system tools
brew install lilypond fluid-synth ffmpeg
python3 -m venv .venv
. .venv/bin/activate
pip install -r tools/requirements.txt

# Build every historical version, including PDF, MP3 and MP4
python tools/build.py --all

# Or build one version
python tools/build.py compositions/wenn-der-abend-leise-wird/versions/v003.json

# Verify committed artifact hashes, source consistency, note exports and counterpoint
python tools/check.py
node tools/check-player.mjs

# Stage the static site, then preview it
python tools/site.py
python -m http.server 8769 --directory _site
```

`--no-video` skips video rendering; `--no-media` builds symbolic exports and checks only. Partial builds are for development and must not be published as complete releases. `tools/check.py` rejects media not bound to the current source and settings by the manifest.

The Pages workflow verifies the committed exports and publishes the staged site. It does not rerender the videos on each push. Rebuild and commit outputs whenever a source changes.

For local files, open the player through an HTTP server and select a JSON and its matching MP3. Selecting files keeps them in your browser; no upload endpoint or analytics service is involved. Published JSON URLs automatically use the neighboring file with the same basename and `.mp3` extension.

## Evidence and attribution

The checker can reject a piece that has documented stylistic exceptions. The final work remains rejected by the supplied strict predicate; no claim of formally certified Bach style is made. Blind Gemini assessments were also unreliable and are preserved with criticism rather than treated as validation.

Matt's supplied toolkit is included unchanged under the composition's `tools/matt/` folder with the repository owner's explicit authorization. GeneralUser GS carries its own license. See [NOTICE](NOTICE.md). No private Slack messages, account credentials, or credential-bearing repository history are included.

## Shareable player URLs

- Latest version: [`player/?composition=wenn-der-abend-leise-wird`](https://informa-tiger.github.io/compositions/player/?composition=wenn-der-abend-leise-wird)
- Explicit latest: `player/?composition=wenn-der-abend-leise-wird&version=latest`
- Pinned version: [`player/?composition=wenn-der-abend-leise-wird&version=v002`](https://informa-tiger.github.io/compositions/player/?composition=wenn-der-abend-leise-wird&version=v002)
- Direct JSON: `player/?score=compositions/wenn-der-abend-leise-wird/generated/v003/composition.json`

`composition` is the stable folder ID. Omitting `version` means `latest`; latest is the highest published version number. A pinned version stays fixed. Selecting a catalog entry updates the URL. Unknown IDs or versions show an error rather than silently choosing another piece. If both `composition` and `score` are supplied, `composition` takes precedence. Direct JSON URLs must permit browser fetching (CORS for other origins).

## Hear individual voices

Click a voice in the player legend to mute or restore it. Cantus-firmus measure ranges remain visible and muted notes dim. All four voices may be muted.

The browser downloads one `composition.voices.mp4` containing four stereo AAC-LC tracks, encoded at 320 kb/s per voice directly from FluidSynth PCM renders. It isolates each track in memory without changing encoded samples, chunk offsets, or encoder-delay edit lists, then decodes the tracks into Web Audio buffers. All four buffers start at the same AudioContext time and offset. There are no separate running media clocks or periodic corrective seeks. Mute changes use an 8 ms gain transition. Pause, seek and speed apply to all voices together.

This replaces the previous four-HTMLAudioElement implementation, whose repeated drift-correction seeks were a plausible source of audible artifacts. That cause has not been confirmed by direct listening. Automated checks verify track extraction preserves decoded PCM exactly, the transport uses identical start times, and muting never seeks. At 75% and 125%, the summed stereo signal passes through one SoundTouchJS AudioWorklet with pitch fixed at 1 and playback-rate compensation. The four source clocks remain identical. At 100%, the processor is bypassed so normal-speed audio is unchanged. Time stretching can introduce some processing coloration and a short buffering delay; it does not transpose the music. The bundled processor and corresponding sources are under MPL-2.0 in `player/vendor/`.

A common mastering gain preserves authored balance and leaves headroom for every voice subset. The interactive mix can be quieter than the separately loudness-normalized full-mix MP3. The original full-mix MP3, video, individual MP3 downloads, and musical notes remain unchanged. MP3 is fetched as a fallback only if multitrack decoding fails. Loading all decoded tracks uses about 160 MB of PCM memory for this piece.

Build all audio with the normal build, or regenerate voice assets only:

```sh
python tools/stems.py --all
node tools/check-mixer.mjs
node tools/check-pitch.mjs
```

For local playback, select the composition JSON and matching `composition.voices.mp4`. JSON plus the full-mix MP3 still works, with voice controls disabled. Muting does not change the score or counterpoint verification.

For a real-browser DSP check, serve the repository and open `tools/pitch-browser-test.html`. It renders four simultaneous test tones through the same summed-audio worklet architecture offline and measures their output frequencies at 75%, 100%, and 125%. Browser verification measured 220/440/660/880 Hz within 0.25 Hz at all speeds. This validates pitch preservation, not a subjective listening judgment.
