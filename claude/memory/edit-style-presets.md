---
name: edit-style-presets
description: Films pick an edit style preset (styles/<name>.json, film.json "style"); Netflix numbers are only the netflix-cold default
metadata:
  type: project
---

On 2026-11-25 the user asked for the whole pipeline to accept many edit styles instead of one fixed Netflix look. The engine now has `styles/<name>.json` presets (netflix-cold default, warm-vintage, clean-explainer, noir-crime), layered engine DEFAULTS <- style <- film.json. A style sets grade/letterbox, cut length, pauses, Remotion palette/fonts/motion, `rules` (graphics per minute, music coverage, dB under voice, Suno cue count) and per-stage `notes`. Commands: `doc.py styles`, `doc.py new ... <style>`, `doc.py <prj> style [set <name>]`. Guide: `docs/STYLES.md`.

**Why:** the user wants to choose and change the editing style per film, and to add new looks without code changes.

**How to apply:** ask which style at the first question of stage 1, together with the film language. At each stage follow that style's `rules` and `notes` (`doc.py <prj> style`). For a new look, write a preset that `extends` the nearest one and show test stills before using it. Films without "style" (up to film 17) stay unchanged. The density and music rules in [[graphics-density]] and [[music-coverage]] are the netflix-cold defaults. See [[documentary-style-direction]] and [[doc-pipeline-engine]].
