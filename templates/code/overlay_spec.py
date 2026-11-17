"""On-screen graphics, pinned to the narration (resolved by `doc.py <prj> overlays` -> 05_Renders/overlays.json).

Row: (GFX number, kind, [beats], end, props)
Beats:  "a1_07:picks"        onset of that phrase in line a1_07 (plain words; numbers as the transcript writes them, often digits)
        "@a1_07" / "^a1_07"  start / end of the line, with an offset: "@a1_07-3.8", "^c0_12+0.4"
End:    a beat (the graphic ends just before it) or "+5" (seconds after the start)
Kinds come from 06_Graphics/remotion/src (Film.jsx + Overlays.jsx): title, chapter, lower, stamp, stat, list, words, quote, define,
timeline, map, bars, split_labels, end_text, ... Each component gets the props plus dur (s) and at (beat times, s from its start).
Full-screen kinds (film.json edit.full_kinds, e.g. map) get a plain plate under them in the edit.
House style: about 45 graphics in a 20-minute film (≥ 2 per minute), full-screen graphics move the whole time they are up.
"""

OV = [
    (1, "title", ["^c0_02+0.5"], "+5.5", dict(title="FILM TITLE", subtitle="One line that says what the film is")),
    (2, "chapter", ["@a1_01-3.8"], "@a1_01-0.1", dict(part="PART ONE", title="Part title")),
    (3, "lower", ["@a1_01+0.2"], "+5.2", dict(text="Place name", sub="Region, Country")),
    # (4, "stat", ["a1_02:some phrase"], "^a1_02", dict(big="1937", sub="what the number means")),
    # (5, "map", ["@a1_03", "a1_03:phrase"], "^a1_03", dict(map="zoom", cam=[["@0", 960, 540, 0.9], ["@1", "Place", None, 1.2]],
    #                                                     pts=[dict(name="Place", at=1, big=True)], caption=dict(kicker="REGION", title="Place", at=1))),
    (90, "end_text", ["^c9_01+0.5"], "+19", dict(lines=["First end line.", "Second.", "Third."], title="FILM TITLE", subtitle="One line that says what the film is")),
]

# optional running counter drawn by the render engine (film.json "hud"): (GFX number, beat, value, mode)
COUNTER = []


def fix_props(kind, p):
    """optional: adjust props after the beats are resolved."""
    return p
