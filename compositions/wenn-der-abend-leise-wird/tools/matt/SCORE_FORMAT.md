# Input format for auditing, certification, and MIDI

The following illustrates the configuration and event syntax; the abbreviated voice lists must be filled with an actual score before it can pass validation.

```json
{
  "title": "My study",
  "config": {
    "total_ticks": 24,
    "ticks_per_quarter": 2,
    "tonic_pc": 0,
    "tonic_third": 4,
    "allowed_pcs": [0, 2, 4, 5, 7, 9, 11],
    "ranges": [[60, 84], [55, 77], [48, 69], [36, 64]],
    "max_leaps": [7, 7, 7, 12],
    "pulse_stride": 2,
    "pulse_offset": 0,
    "tritone_max_wait": 2,
    "require_independence": true,
    "min_independent_changes": 2
  },
  "voices": {
    "s": [{"start": 0, "dur": 2, "pitch": 67}],
    "a": [],
    "t": [],
    "b": []
  }
}
```

- `title` must be a nonempty string. It is descriptive metadata and does not affect the musical rules.
- `total_ticks` and `ticks_per_quarter` must be positive integers.
- `tonic_pc` is 0–11, with C = 0. `tonic_third` is 3 or 4. These determine the licensed tritone resolution, not an inferred key.
- `allowed_pcs` is a nonempty list of pitch classes 0–11. It is independently supplied; a minor key with a raised leading tone must explicitly include that pitch class.
- `ranges` has four inclusive `[minimum, maximum]` pairs in SATB order, within 1–127.
- `max_leaps` has four positive semitone limits in SATB order, checked by Python across contiguous notes. It is not a formal maximum-leap theorem.
- `pulse_stride` is positive; `pulse_offset` lies between 0 and stride minus one. Offsets refer to the tick origin, including any pickup. This setting is explicit rather than inferred from meter.
- `tritone_max_wait` is a positive integer tick count.
- `require_independence` is a JSON boolean; `min_independent_changes` is a positive integer even if the requirement is disabled. Disable it only when you intentionally want to certify a passage without this requirement, such as a two-chord unit test.
- All four voice lists must be nonempty, sorted, monophonic, and within the duration. Rests are gaps. Separate same-pitch events are rearticulations; one longer event represents a held note.

The audit reconstructs its own sounding timeline. It does not trust precomputed `frames`, harmonic labels, or other metadata. Extra descriptive fields do not acquire verification semantics merely by being present.
