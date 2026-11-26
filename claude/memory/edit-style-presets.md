---
name: edit-style-presets
description: "Films pick an edit style preset (styles/<name>.json, film.json \"style\"); Netflix numbers are only the netflix-cold default"
metadata:
  node_type: memory
  type: project
  originSessionId: 82d92324-9150-4643-b482-19c666e2ed37
  modified: 2026-11-26T07:25:00.298Z
---

On 2026-11-25 the user asked for the whole pipeline to accept many edit styles instead of one fixed Netflix look. The engine now has `styles/<name>.json` presets (netflix-cold default, warm-vintage, clean-explainer, noir-crime), layered engine DEFAULTS <- style <- film.json. A style sets grade/letterbox, cut length, pauses, Remotion palette/fonts/motion, `rules` (graphics per minute, music coverage, dB under voice, Suno cue count) and per-stage `notes`. Commands: `doc.py styles`, `doc.py new ... <style>`, `doc.py <prj> style [set <name>]`. Guide: `docs/STYLES.md`.

Same day the user set the intake rule: they give the script plus, optionally, a style file; with no style file the film uses the default template (netflix-cold). `doc.py new ... --script <file> --style <preset | file.json | brief>`: a .json is checked and copied to `04_Scripts_Code/style.json`; a brief (.md/.txt/.docx/.pdf/image) becomes `STYLE_BRIEF.<ext>` for Claude to turn into style.json. Fill-in example: `styles/_template.json`.

Fonts (fixed 2026-11-26 after the user reported "không copy được font"): `gfx`/`new` copy every font file the style names into the film's `06_Graphics/remotion/public/` (from templates, next to the user's style file, or a full path); a user style's fonts are kept in `04_Scripts_Code/fonts/`. `fonts_vi` only replaces the slot it was made for. Premiere text uses `gfx.premiere_font` or the style's serif family, falling back to Georgia when not installed in Windows. `qc` reads the style's `rules`.

**Why:** the user wants to choose and change the editing style per film, and to add new looks without code changes.

**How to apply:** at stage 1 take the script and style file the user gives; no style file means netflix-cold, with no extra question beyond a one-line mention. At each stage follow that style's `rules` and `notes` (`doc.py <prj> style`). For a new look, write a preset that `extends` the nearest one and show test stills before using it. Films without "style" (up to film 17) stay unchanged. The density and music rules in [[graphics-density]] and [[music-coverage]] are the netflix-cold defaults. See [[documentary-style-direction]] and [[doc-pipeline-engine]].
