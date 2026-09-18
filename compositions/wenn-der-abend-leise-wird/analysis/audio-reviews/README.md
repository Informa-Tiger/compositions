# Blind audio API review

Submitted the rendered audio to Google Vertex AI Gemini 2.5 Pro and Flash with identical neutral prompts. Neither received the title, score, intended style, composer attribution, or prior analysis. MP3 metadata was removed. Credentials were read directly from the user-authorized local service-account file, never copied into this project or printed. JSON records preserve the prompt, audio hashes, model version, usage, and response.

## Outcome and reliability

- Flash identified Baroque/Neo-Baroque organ music with a sacred/chorale character.
- Pro identified organ music but leaned toward late-Romantic or 20th-century neo-Baroque/neo-Romantic style.
- Both gave generally positive assessments. Those assessments are unreliable as detailed musical evidence: Pro invents a timeline ending at 3:16, Flash at 2:20, while ffprobe measures the actual MP3 as 104.304 seconds.
- Both describe registration changes. The performance MIDI contains only four program-change messages, all at time zero, selecting the same organ preset. No later registration switches occur.
- A separate Flash request received the first 20 seconds as a mono 24 kHz WAV, explicitly stating its length and asking only about audible instrumentation, style and texture. It identified organ and sacred/classical music, but incorrectly described a full multi-part opening with little change in density. The actual MIDI starts with tenor alone; alto enters at 4.091 seconds, with further voices later.

These results weakly corroborate broad organ/church-music classification, but do not establish stylistic authenticity, compositional quality, or correctness of counterpoint. In particular, the complimentary prose should not be treated as validation.

No Cyanite credentials were found in the inspected local credential sources, so no authenticated Cyanite request was made. Essentia was not run; it is a separate local-model alternative, not a second hosted API tested here.

## Files

- gemini-2.5-pro.md / .json: full recording, blind review
- gemini-2.5-flash.md / .json: full recording, blind review
- gemini-2.5-flash-opening.md / .json: narrow 20-second WAV check
- ../../tools/blind_audio_review.py: reproducible caller (requires google-auth, requests, ffmpeg; pass credentials via --credentials)

The composition and rendered deliverables were not changed.
