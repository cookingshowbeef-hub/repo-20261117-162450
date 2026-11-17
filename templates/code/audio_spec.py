"""Music and sound for the film (mixed by `doc.py <prj> audio final`).

Library: Y:\\Data Footage\\Discovery\\Kien  (BGM_NoCopyright = Kevin MacLeod / Incompetech, CC BY 4.0, credited automatically;
SFX_Vault = 1001 Sound Effects) plus CC0 Freesound sounds fetched with `doc.py <prj> freesound get <name> <id>` (use as "fs:<name>").
House style: score under nearly all of the narration (the qc step wants ≥ 85%), about 15 dB under the voice after ducking;
silence only as a deliberate beat. A cue changes with the story's turn, not at random.
"""
from docpipe.cues import S_, E_, word, END

# (cue, file, film in, film out, offset into the track (None = end on the track's end), fade in, fade out, gain dB)
MUSIC = [
    ("c0_drone", "03_Mystery_free_02m32s_Deep_Noise.mp3", 0.5, E_("c0_02", 0.05), 0, 8.0, 0.12, -13),
    ("a1_main",  "20_AncientHistory_74bpm_02m26s_Long_Road_Ahead.mp3", S_("a1_01", -4.0), E_("a1_01", 2.5), 0, 2.0, 3.0, -9),
    ("c9_end",   "18_EmotionalPiano_free_05m04s_Promises_to_Keep.mp3", S_("c9_01", -1.0), END, 0, 2.0, 4.0, -9),
]

# (file in SFX_Vault or "fs:<name>", film in, film out (None = file length; longer than the file = loop), offset, fade in, fade out, level dBFS RMS, note)
SFX = [
    ("21_Suspense_Wind_Howl_01.mp3", 0.0, E_("c0_02"), 0, 3.0, 0.15, -39, "wind under the cold open"),
]

# accent sounds per graphic kind: card | map | whoosh | whoosh_hit | page | tick | clicks | stamp | none
GFX_SFX = {"chapter": "card", "title": "card", "map": "map", "stat": "whoosh_hit", "list": "clicks", "stamp": "stamp", "define": "page"}

# sounds on counter events, by mode: (file, seconds after the event, level dBFS, note)
COUNTER_SFX = {}
