---
name: sonnet-picks-broll
description: "B-roll and Commons photo vetting goes to a Sonnet subagent, not the main session; CLIP was tried and removed (17 Nov 2026)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: e4b95b47-46ab-4b3e-a120-066e572cfda3
  modified: 2026-11-17T03:07:41.752Z
---

From 2026-11-17, contact sheets (b-roll `mini_N.jpg` and Commons topic sheets) are vetted by a subagent run with `model: "sonnet"`. The prompt templates are in the engine's `docs/PICKER_SONNET.md`. The agent runs `doc.py pick` itself, writes `picker_notes.md` / `usable.md`, and replies in 10 lines or fewer. The main session never opens the sheets.

The user also had a local CLIP pre-filter installed, tested and then removed on the same day (venv, model cache, `clip_rank.py`, `doc.py clip`). The test showed only about 25% fewer tiles and about 1% saving for the whole film. Do not re-propose CLIP.

**Why:** image viewing was the largest Claude-usage cost of stage 2, and the user wants it moved to the cheaper model.

**How to apply:** in stage 2, make the mini sheets, then give one Sonnet agent per set or Commons topic group. Ask it follow-up questions with SendMessage rather than viewing images in the main session. See [[stage-per-session]] and [[doc-pipeline-engine]].
