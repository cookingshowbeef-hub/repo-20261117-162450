"""Resolve the project's overlay_spec.OV (and optional COUNTER) against the narration -> 05_Renders/overlays.json + counter.json.

Beat syntax:  "a1_07:picks"  onset of that phrase in line a1_07 (or the next two lines)   "@a1_07+0.4" / "^a1_07-1"  start / end of a line
End: a beat (the graphic ends just before it) or "+5" (seconds after the start).
OV rows: (gfx number, kind, [beats], end, props). Map cameras may name places from public/geo/<map>.json ("pts").
Checks: every beat found, no two graphics overlapping (counter excepted), beats inside each graphic's life, full-screen kinds held
at most overlay.full_hold s past their last beat.
"""
import json, os, re, sys
from .ctx import tc

norm = lambda w: re.sub(r"[^\w']", "", w.lower().replace("’", "'"))
ALIAS = {"kilometres": "kilometers", "metres": "meters", "neighbours": "neighbors", "neighbourhood": "neighborhood", "colour": "color",
         "travelled": "traveled", "honour": "honor", "labourers": "laborers", "programmes": "programs", "diarrhoea": "diarrhea"}


class Beats:
    def __init__(self, P):
        self.P, TL = P, P.timeline()
        self.line = {l["id"]: l for l in TL["lines"]}
        self.alias = dict(ALIAS, **P.cfg["overlay"]["aliases"])
        self.words = {}
        for i, l in self.line.items():
            ws = []
            for w, a, b in P.words(i):
                for part in re.split(r"[-\s]+", w):
                    if norm(part):
                        ws.append((self.alias.get(norm(part), norm(part)), l["start"] + a))
            self.words[i] = ws

    def __call__(self, spec):
        m = re.fullmatch(r"([@^])([a-z]\d+_\d\d)([+-][\d.]+)?", spec)
        if m:
            return self.line[m.group(2)]["start" if m.group(1) == "@" else "end"] + float(m.group(3) or 0)
        lid, phrase = spec.split(":", 1)
        toks = [self.alias.get(norm(x), norm(x)) for x in re.split(r"[-\s]+", phrase) if norm(x)]
        for lj in [lid] + [l for l in self.line if l > lid][:2]:
            ws = self.words[lj]
            for s in range(len(ws)):
                if [w for w, _ in ws[s:s + len(toks)]] == toks:
                    return ws[s][1]
        raise KeyError(f"phrase not found: {spec!r}")


def unkw(x):
    """dict(from_=...) -> {"from": ...}: Python keywords spelled with a trailing underscore in the spec."""
    import keyword
    if isinstance(x, dict):
        return {(k[:-1] if k.endswith("_") and keyword.iskeyword(k[:-1]) else k): unkw(v) for k, v in x.items()}
    if isinstance(x, list):
        return [unkw(v) for v in x]
    return x


def run(P, args):
    sys.stdout.reconfigure(encoding="utf-8")
    spec = P.spec("overlay_spec")
    beat = Beats(P)
    full, hold = P.cfg["edit"]["full_kinds"], P.cfg["overlay"]["full_hold"]
    geo = P.p("06_Graphics", "remotion", "public", "geo")
    out, bad = [], []
    for gfx, kind, beats, end, p in spec.OV:
        try:
            ts = [beat(b) for b in beats]
            t0 = ts[0] - (0.25 if ":" in beats[0] else 0)
            t1 = t0 + float(end[1:]) if end.startswith("+") else beat(end) - (0.1 if ":" in end else 0)
        except KeyError as e:
            bad.append(f"GFX{gfx} {kind}: {e}"); continue
        if kind in full and kind != "end_text":     # end_text keeps its own length (capping it hid the closing lines)
            t1 = min(t1, ts[-1] + hold)
        p = dict(p)
        if kind == "map" and "cam" in p:
            g = json.load(open(os.path.join(geo, p["map"] + ".json")))
            p["cam"] = [[c[0], *(g["pts"][c[1]] if isinstance(c[1], str) else c[1:3]), *c[3:]] for c in p["cam"]]
        p = unkw(p)
        if hasattr(spec, "fix_props"):
            p = spec.fix_props(kind, p)
        out.append(dict(id=f"G{gfx:02d}", gfx=gfx, kind=kind, start=round(t0, 3), end=round(t1, 3),
                        p=dict(p, kind=kind, dur=round(t1 - t0, 3), at=[round(t - t0, 3) for t in ts])))
    out.sort(key=lambda o: o["start"])
    for a, b in zip(out, out[1:]):
        if 0 < a["end"] - b["start"] <= 0.3:
            a["end"] = round(b["start"] - 0.02, 3); a["p"]["dur"] = round(a["end"] - a["start"], 3)
        elif b["start"] < a["end"]:
            bad.append(f"{a['id']} {a['kind']} overlaps {b['id']} {b['kind']} by {a['end'] - b['start']:.2f}s")
    for o in out:
        if o["p"]["dur"] < 1.5 or any(x > o["p"]["dur"] - 0.5 or x < -0.01 for x in o["p"]["at"]):
            bad.append(f"{o['id']} {o['kind']} dur {o['p']['dur']} beats {o['p']['at']}")
    cnt = []
    for gfx, b, v, mode in getattr(spec, "COUNTER", []):
        try:
            cnt.append(dict(gfx=gfx, t=round(beat(b), 3), value=v, mode=mode))
        except KeyError as e:
            bad.append(f"counter GFX{gfx}: {e}")
    P.save_out("overlays.json", out)
    P.save_out("counter.json", sorted(cnt, key=lambda c: c["t"]))
    if "-v" in args:                                              # the full table only on request: it is ~50 lines per run
        for o in out:
            print(f"{o['id']} {tc(o['start']):>7}-{tc(o['end']):>7} {o['kind']:12s} beats {o['p']['at']}")
    end = P.timeline()["end"]
    print(f"{len(out)} graphics ({len(out) / (end / 60):.1f}/min, {sum(o['p']['dur'] for o in out) / 60:.1f} min on screen) + {len(cnt)} counter events")
    for b in bad:
        print("  !", b)
    if bad:
        sys.exit(1)
