---
name: music-coverage
description: "User wants near-continuous music about 15 dB under narration, not sparse cues"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 7ee983ce-4097-40bb-ad30-b972c7a4ab37
  modified: 2026-11-13T01:19:53.808Z
---

The user said "lacking music" about a Pagpag cut where music played 65% of the time and sat about 21 dB under the voice. The script's "sparse cue map" with silent act openings was too restrained for them. The fix was music under about 96% of the film, every cue about 14–19 dB under the voice, ducking at −6 dB (not −9), and the cold open scored from the first picture.

**Why:** the channel's films are narrated with no interviews, so long stretches without score feel empty.

**How to apply:** score every section, including act openings and cold opens. Measure each cue against the voice on the stems (`05_Renders/tests/music_level.py` in Pagpag) and aim for about 15 dB under the narration. Short deliberate cut-outs are fine. See [[music-and-motion-tool-choices]] and [[graphics-density]].

Since 2026-11-25 these numbers are the `netflix-cold` default. Other styles set their own `rules.music_coverage` and `music_under_voice_db`, for example noir-crime at 70% and 17 dB. See [[edit-style-presets]].
