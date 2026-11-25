---
name: premiere-editable-text
description: "Premiere imports FCP7-XML Text generators as editable text and reads transitionitems, but ignores keyframes on generators"
metadata:
  node_type: memory
  type: project
  originSessionId: ad88e9b0-a3ea-4797-a25d-771d9b115728
  modified: 2026-11-20T09:33:53.378Z
---

Tested 20 Nov 2026 (film 16 demo, `05_Renders/premiere/demo_text_v3.xml`) in the user's Premiere:
- `<generatoritem>` with effect "Text" / "Outline Text" imports; text, font, size are editable in Premiere. A `<clipitem>` without a file (first try) makes the import fail with an empty error.
- `<transitionitem>` Cross Dissolve at the head/tail of a text clip works.
- Basic Motion / Opacity keyframes on a generatoritem are ignored, even with authoringApp="PremierePro" (they do work on file clips).

**Why:** the user wants reviewers to change graphic text/font/size in Premiere without asking Claude (saves credit).
**Decision (20 Nov 2026):** the user dropped the idea: losing Remotion's motion is not worth editable text. Keep every graphic as a Remotion render; don't re-propose editable text cards unless Premiere starts honouring the keyframes. Related: [[premiere-for-new-films]].

**Update 23 Nov 2026 (film 17):** for a film with no Remotion graphics the user chose Premiere Text generators for on-screen facts/chapter cards. The engine now supports it: optional `04_Scripts_Code/text_spec.py` (TEXT = [(t_in, t_out, text, style)] with docpipe.cues times) → `premiere.py text_tracks()` writes generators on V6+ with dissolves. Remotion stays the default when a film has graphics.
