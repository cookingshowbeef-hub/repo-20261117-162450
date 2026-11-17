---
name: doc-pipeline-engine
description: Shared documentary engine (doc.py) built 2026-11-14 from Aral V2/Pagpag/Oymyakon; use it for new films instead of copying per-project scripts
metadata:
  node_type: memory
  type: project
  originSessionId: 7ee983ce-4097-40bb-ad30-b972c7a4ab37
  modified: 2026-11-14T03:56:02.064Z
---

A shared engine lives in `D:\4. bot\documentary\06. Kịch bản & Công cụ Code - Scripts & Engine\03. Doc Pipeline - Quy trình Phim tài liệu\`.
- Run steps with `python doc.py <project> <step>`.
- Start a project with `python doc.py new "<folder>" "<TITLE>"`.
- The guide is docs/QUY_TRINH.md (Vietnamese); the review checklist is docs/QC_CHECKLIST.md.
- Each project's per-film inputs live in 04_Scripts_Code: film.json, Narration.md, script_template.md, overlay_spec.py, audio_spec.py, media_spec.py, and optionally pools.py.
- It was built from the Oymyakon scripts and reproduces Oymyakon's timeline, overlays, edit and audio plan exactly.

Roles (user, 2026-11-16): the user writes and edits the script (Narration.md); Claude plans voice, visuals, b-roll, graphics, audio and renders. Before the final render, Claude exports a DaVinci Resolve review timeline (`doc.py <prj> review`); the user leaves marker notes and Claude maps them back with `doc.py <prj> notes <edl>`.

**Why:** the user asked (2026-11-14) to turn the three films into a reusable workflow.

**How to apply:**
- New films go through doc.py.
- Fixes to shared behaviour go into docpipe/, not into per-project copies.
- `DOC_OUT=<dir>` makes dry runs that leave the project's 05_Renders alone.
- API keys live only in `~/.docpipe/keys.env` (NAME=value lines; env vars win), set up 2026-11-17. No key is kept in code or in the project folders; ask the user before adding a missing one, and never print a key.

Related: [[graphics-density]], [[music-coverage]], [[render-1080-default]].
