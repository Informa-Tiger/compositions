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
