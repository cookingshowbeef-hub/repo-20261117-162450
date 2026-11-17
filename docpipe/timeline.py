"""Lay the voice lines on the film clock -> 05_Renders/timeline.json {"lines", "blocks", "acts", "end"}, and build the readable script.

Blocks are the V.O. groups of script_template.md ({{c0_01 c0_02}} = one block under one VISUAL note); acts are its "## " headings
matching film.json acts_regex. Pauses: timing.gap_line between lines of a block, timing.gap_block between blocks, timing.act_card
before every act's first word (except no_card_acts), plus timing.hold_before / hold_after per line, and timing.end_text at the end.
"""
import json, os, re, sys
from .ctx import VO, tc


def groups(P):
    out, act = [], None
    for line in P.template().split("\n"):
        m = re.match(r"## (%s)" % P.cfg["acts_regex"], line)
        if m:
            act = m.group(1)
        for g in VO.findall(line):
            out.append((act, g.split()))
    return out


def run(P, args):
    T = P.cfg["timing"]
    NARR = {p["id"]: p for p in P.load("01_Voice", "narration.json")}
    gl, gb = T["gap_line"], T["gap_block"]
    t, lines, blocks, acts, prev = 0.0, [], [], [], None
    G = groups(P)
    for k, (act, ids) in enumerate(G):
        if act != prev:
            if prev is not None:
                acts[-1]["end"] = round(t, 3)
            acts.append(dict(name=act, start=round(t, 3)))
            if act not in P.cfg["no_card_acts"]:
                t += T["act_card"] - (gb if k else 0)
            prev = act
        elif k:
            t += gb - gl
        b0 = t
        for i in ids:
            t += T["hold_before"].get(i, 0)
            d = NARR[i]["duration"]
            lines.append(dict(id=i, section=NARR[i]["section"], block=f"K{k:02d}", start=round(t, 3), end=round(t + d, 3), text=NARR[i]["text"]))
            t += d + T["hold_after"].get(i, 0) + gl
        blocks.append(dict(id=f"K{k:02d}", act=act, start=round(b0, 3), end=round(t - gl, 3), lines=ids))
    t += T["end_text"]
    acts[-1]["end"] = round(t, 3)
    used = [i for _, ids in G for i in ids]
    missing, dup = [i for i in NARR if i not in used], sorted({i for i in used if used.count(i) > 1})
    if missing or dup:
        sys.exit(f"voice lines missing from the template {missing} / used twice {dup}")
    P.save_out("timeline.json", dict(lines=lines, blocks=blocks, acts=acts, end=round(t, 3)))
    for a in acts:
        print(f"{a['name']:14s} {tc(a['start'])}")
    print(f"{len(lines)} lines in {len(blocks)} blocks, film {tc(t)}")


def script(P, args):
    """script_template.md + the recorded lines -> <script_out>: V.O. text in place of {{ids}}, GFX numbered, stats filled in."""
    sys.stdout.reconfigure(encoding="utf-8")
    NARR = P.load("01_Voice", "narration.json")
    L = {p["id"]: p for p in NARR}
    TL = P.timeline()
    s = open(os.path.join(P.code, P.cfg["template"]), encoding="utf-8").read()
    s = VO.sub(lambda m: "**V.O.:**\n" + "\n>\n".join(f"> {L[i]['text']}  `[{i}]`" for i in m.group(1).split()), s)
    span = {}
    for l in TL["lines"]:
        a, b = span.get(l["section"], (l["start"], l["end"]))
        span[l["section"]] = (min(a, l["start"]), max(b, l["end"]))
    for sec, (a, b) in span.items():
        s = s.replace("{{T:%s}}" % sec, f"{tc(a)} – {tc(b)}")
    n = [0]

    def num(m):
        n[0] += 1
        return f"**GFX {n[0]}{m.group(1) or ''}:**"
    s = re.sub(r"\*\*GFX( \(NEW\))?:\*\*", num, s)
    speech = sum(p["duration"] for p in NARR)
    s = (s.replace("{{GFXCOUNT}}", str(n[0])).replace("{{GFXRATE}}", f"{n[0] / (TL['end'] / 60):.1f}")
          .replace("{{SPEECH}}", f"{speech / 60:.1f} min").replace("{{WORDS}}", f"{sum(len(p['text'].split()) for p in NARR):,}")
          .replace("{{LINES}}", str(len(NARR))).replace("{{RUNTIME}}", tc(TL["end"])))
    left = re.findall(r"\{\{[^}]+\}\}", s)
    if left:
        print("  ! unfilled:", left[:5])
    name = P.cfg.get("script_out") or re.sub(r"\W+", "_", P.cfg["title"].title()) + "_Script.md"
    open(os.path.join(P.code, name), "w", encoding="utf-8").write(s)
    print(f"{name}: {len(NARR)} voice lines, {n[0]} graphics ({n[0] / (TL['end'] / 60):.1f}/min), runtime {tc(TL['end'])}")
