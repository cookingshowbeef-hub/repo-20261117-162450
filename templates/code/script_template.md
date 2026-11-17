# FILM TITLE
### Subtitle

**Runtime:** {{RUNTIME}} ({{SPEECH}} of narration)
**Format:** Narrated documentary (AI voice-over), no on-camera interviews
**Narration:** {{WORDS}} words in {{LINES}} voice lines, fact-checked (see `FACT_CHECK.md`).
**Graphics:** {{GFXCOUNT}} ({{GFXRATE}} per minute — aim for about 45 in a 20-minute film)
**Score:** Near-continuous, about 15 dB under the narration. Silence only where marked as a deliberate beat.

<!-- HOW THIS FILE DRIVES THE FILM
  {{c0_01 c0_02}}   one V.O. block: these voice lines, in order. Every voice line appears exactly once.
  **VISUAL:** ...   the pictures for the NEXT block, in narration order, as asset codes inside the prose:
                    photo:<topic>#<n>  (Commons contact sheet number)   px:<id> / pb:<id>  (vetted clips)   nasa:<topic>   file:<path>
                    Name about one picture per 3.6 s of the block. A block with no VISUAL line reuses the previous block's pictures.
  **GFX:** / **SFX:** / **MUSIC:**   notes for overlay_spec.py / audio_spec.py (numbered by `doc.py <prj> script`).
  ## COLD OPEN / ## ACT ONE ... / ## CLOSING   acts (film.json acts_regex); every act but the cold open opens on a part card.
  {{T:a1}}  replaced by the section's time range.
  Location rule: a generic stock clip is never described or captioned as a named place.
-->

---

## COLD OPEN — "Title of the open" ({{T:c0}})

**VISUAL:** What we see first (px:000000); then (photo:topic#0).
**MUSIC:** A low drone.

{{c0_01 c0_02}}

**GFX:** TITLE CARD: **FILM TITLE**

---

## ACT ONE — "Part title" ({{T:a1}})

**GFX:** Part card: PART ONE · Part title
**VISUAL:** (photo:topic#1, photo:topic#2); (px:000001).

{{a1_01}}

---

## CLOSING ({{T:c9}})

**VISUAL:** ...

{{c9_01}}

**GFX:** End text, then the title.

## PRODUCTION NOTES

Anything below this heading is ignored by the pipeline.
