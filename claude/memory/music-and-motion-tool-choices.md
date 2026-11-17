---
name: music-and-motion-tool-choices
description: Music source and motion-graphics tools the user picked for the documentaries (Suno via AI33 + BGM library since 17 Nov 2026)
metadata:
  node_type: memory
  type: feedback
  originSessionId: e4b95b47-46ab-4b3e-a120-066e572cfda3
  modified: 2026-11-17T02:06:34.655Z
---

Music: since 2026-11-17 the user wants score cues made with **Suno through the AI33 API** (`doc.py <prj> music make <cue> "<prompt>"`, ~3,600 AI33 credits for 2 instrumental takes), combined with the house BGM library (244 Kevin MacLeod tracks in 8 mood folders, `music lib`). **Do not use vidIQ for music any more**: its credits were running out. The workflow is written in QUY_TRINH.md section 7 and the doc-pipeline SKILL.md.

History: on 2026-11-10 the user picked vidIQ orchestral cues over local ACE-Step 1.5 (`D:\4. bot\tools\ACE-Step-1.5`) and rejected code-synthesised score. On 2026-11-17 an A/B of film 12's famine cue (vidIQ vs two Suno takes) led to the switch.

Open question: AI33 has not confirmed in writing the commercial rights for Suno output bought through it.

Motion graphics: Remotion and HyperFrames are both acceptable styles; the plain JavaScript canvas version was judged the worst. Python/OpenCV-drawn graphics read as home-made next to the new music.

B-roll must be specific to each line and must not repeat (the user flagged that the footage was "not up to par" with the new music).

**Why:** the user is pushing the films toward Netflix-level polish (see [[documentary-style-direction]]), and vidIQ credits were nearly gone.

**How to apply:** use Suno for the turning-point cues (cold open, each act, climax, close) and the library for bridges. Use the library as the fallback when Suno's content filter blocks a prompt. Keep [[music-coverage]] targets. See [[doc-pipeline-engine]].
