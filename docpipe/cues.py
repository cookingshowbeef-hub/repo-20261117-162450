"""Time helpers for a project's audio_spec.py, bound to the project before the spec is imported:
    from docpipe.cues import S_, E_, word, END
S_("a1_04", -1.0) = 1 s before line a1_04 starts; E_("a1_12", 2.0) = 2 s after it ends; word("a3_13", "a faint crackle") = onset of the phrase.
"""
import re
import unicodedata

P = LN = None
END = 0.0


def bind(project):
    global P, LN, END
    P = project
    TL = P.timeline()
    LN = {l["id"]: l for l in TL["lines"]}
    END = TL["end"]


def S_(i, d=0.0):
    return LN[i]["start"] + d


def E_(i, d=0.0):
    return LN[i]["end"] + d


def word(line, phrase):
    norm = lambda w: re.sub(r"[^\w']", "", unicodedata.normalize("NFC", w).lower().replace("’", "'"))   # Unicode-aware (Vietnamese)
    ws = [(norm(w), a) for w, a, b in P.words(line)]
    ws = [x for x in ws if x[0]]
    t = [x for x in map(norm, phrase.split()) if x]
    for i in range(len(ws)):
        if [w for w, _ in ws[i:i + len(t)]] == t:
            return LN[line]["start"] + ws[i][1]
    raise KeyError(f"{line}: {phrase!r}")
