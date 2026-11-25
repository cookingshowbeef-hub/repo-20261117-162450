"""Credits and the automatic quality report.

  doc.py <prj> credits   -> 05_Renders/CREDITS.md from what the film actually uses (photos, clips, music, Freesound)
  doc.py <prj> qc        -> 05_Renders/QC_REPORT.md: the house rules checked on edit.json / overlays.json / audio_plan.json / final mix
The report never replaces watching the film: it catches the mechanical faults, the eye catches wrong pictures.
"""
import json, os, re, subprocess, sys
import numpy as np
from .ctx import tc

ws = lambda x: re.sub(r"\s+", " ", re.sub(r"(Unknown author)+", "Unknown author", x or "")).strip()


def credits(P, args):
    sys.stdout.reconfigure(encoding="utf-8")
    C = P.cfg["credits"]
    S = P.load_out("edit.json")
    IDX, MAN = P.load("03_Images", "commons", "sheets", "index.json", default={}), P.load("03_Images", "commons", "manifest.json", default={})
    PX, PB = P.load("02_B-Roll", "pexels", "manifest.json", default={}), P.load("02_B-Roll", "pixabay", "manifest.json", default={})
    FS = P.load("07_Audio", "freesound", "manifest.json", default={})
    NASA = P.load("03_Images", "nasa", "manifest.json", default={})
    plan = P.load("07_Audio", "audio_plan.json", default={"music": [], "sfx": []})
    used = {s["src"] for s in S}
    photos = sorted({IDX[s[6:]] for s in used if s.startswith("photo:")}, key=lambda t: (MAN[t]["topic"], t))
    px = sorted({PX[s[3:]]["user"] for s in used if s.startswith("px:")})
    pb = sorted({str(PB[s[3:]]["user"]) for s in used if s.startswith("pb:")})
    nasa = sorted({NASA.get(os.path.basename(s[5:]), {}).get("source", "") for s in used if s.startswith("nasa:")} - {""})
    ai = re.compile(r"^(suno|vidiq)_")
    gen = sorted({os.path.basename(m["file"]).split("_")[0] for m in plan["music"] if ai.match(os.path.basename(m["file"]))})
    tracks = sorted({re.sub(r"^\d+_[A-Za-z]+_(\d+bpm|free)_\d+m\d+s_", "", os.path.basename(m["file"]))[:-4].replace("_", " ") for m in plan["music"]
                     if not ai.match(os.path.basename(m["file"]))})
    fs = sorted({FS[os.path.basename(x["file"])[:-4]]["author"] for x in plan["sfx"] if x["file"].startswith("freesound/") and os.path.basename(x["file"])[:-4] in FS})
    L = [f"# {P.cfg['title']} — credits for the video description", "", C["intro"], ""]
    if tracks or gen:
        L.append("## Music")
        if gen:
            L.append(C.get("ai_music") or "Original score: AI-generated cues (%s)." % ", ".join({"suno": "Suno", "vidiq": "vidIQ"}[g] for g in gen))
        if tracks:
            L += [f"Music by {C['music']}: " + ", ".join(f'"{t}"' for t in tracks) + ".", f"Licensed under {C['music_licence']}"]
        L.append("")
    if photos:
        L.append("## Photographs (Wikimedia Commons)")
        for t in photos:
            m = MAN[t]
            L.append('- "%s" by %s, %s, %s' % (t.rsplit(".", 1)[0], ws(m["author"]) or "unknown", m["licence"], m["page"]))
        L.append("")
    if nasa:
        L += ["## Satellite imagery", "- NASA Earth Observatory (public domain): " + (C.get("nasa") or ", ".join(nasa)), ""]
    L += ["## Video"] + (["- Pexels (Pexels License): " + ", ".join(px)] if px else []) + (["- Pixabay (Pixabay Content License): " + ", ".join(pb)] if pb else []) + [""]
    L += ["## Sound", "- Sound effects: 1001 Sound Effects" + ("; Freesound (CC0): " + ", ".join(fs) if fs else ""), ""]
    L += C["extra"]
    open(P.out("CREDITS.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"{len(photos)} photos, {len(px)} Pexels and {len(pb)} Pixabay creators, {len(tracks)} music tracks, {len(fs)} Freesound authors")


def loudness(path):
    log = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", log)
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", log)
    return (float(i[-1]) if i else None), (float(tp[-1]) if tp else None)


def qc(P, args):
    sys.stdout.reconfigure(encoding="utf-8")
    E, TL = P.cfg["edit"], P.timeline()
    S, O = P.load_out("edit.json"), P.load_out("overlays.json")
    PX, PB = P.load("02_B-Roll", "pexels", "manifest.json", default={}), P.load("02_B-Roll", "pixabay", "manifest.json", default={})
    mins = TL["end"] / 60
    R, fails = [], 0

    def row(ok, name, value, rule):
        nonlocal fails
        fails += 0 if ok else 1
        R.append(f"| {'OK' if ok else '**FIX**'} | {name} | {value} | {rule} |")
    vis = [s for s in S if not s["src"].startswith("plate:")]
    d = np.array([s["end"] - s["start"] for s in vis])
    short = [s for s in vis if s["end"] - s["start"] < E["min"] - 0.3]
    long_ = [s for s in vis if s["end"] - s["start"] > E["max"] + 1.0]
    row(not short, "Short shots", f"{len(short)}" + (" (" + ", ".join(f"{s['id']} {tc(s['start'])}" for s in short[:6]) + ")" if short else ""), f"none under {E['min'] - 0.3:.1f} s")
    row(len(long_) <= 3, "Long shots", f"{len(long_)}" + (" (" + ", ".join(f"{s['id']} {tc(s['start'])} {s['end'] - s['start']:.1f}s" for s in long_[:6]) + ")" if long_ else ""),
        f"at most 3 over {E['max'] + 1:.1f} s")
    row(True, "Shot length", f"median {np.median(d):.1f} s, {len(vis)} shots", f"target {E['target']} s")
    uses, blk, rep_blk, gap = {}, {}, [], []
    last = {}
    for s in vis:
        a = s["src"]
        uses[a] = uses.get(a, 0) + 1
        if (s["block"], a) in blk:
            rep_blk.append(f"{s['id']} {a}")
        blk[(s["block"], a)] = 1
        if a.split(":")[0] in ("px", "pb", "lk") and a in last and s["start"] - last[a] < E["clip_gap"]:
            gap.append(f"{s['id']} {a}")
        last[a] = s["start"]
    row(not rep_blk, "Same picture twice in a block", f"{len(rep_blk)} " + ", ".join(rep_blk[:5]), "none")
    from .edit import is_clip
    over = [f"{a} ×{n}" for a, n in uses.items() if n > (E["clip_cap"] if is_clip(a) else E["photo_cap"])]
    row(not over, "Film-wide reuse", f"{len(over)} over cap " + ", ".join(over[:5]), f"clips ≤{E['clip_cap']}, photos ≤{E['photo_cap']}")
    row(not gap, "Clip back within the gap", f"{len(gap)} " + ", ".join(gap[:5]), f"none within {E['clip_gap']:.0f} s")
    row(len(uses) >= len(vis) * 0.75, "Distinct pictures", f"{len(uses)} for {len(vis)} shots", "at least 75% of shots")
    static = [f"{s['id']} {tc(s['start'])}" for s in vis if s["src"].startswith("photo:") and not s["treatment"]]
    row(not static, "Photos without a move", f"{len(static)}", "every still moves")
    # pictures under a place caption must be from that place: a generic clip under a lower third is suspicious
    lows = [o for o in O if o["kind"] in ("lower",)]
    sus = []
    LK = P.load("02_B-Roll", "local", "index.json", default={})
    for o in lows:
        for s in vis:
            k, ref = s["src"].split(":", 1)
            man = PX if k == "px" else PB if k == "pb" else LK if k == "lk" else None
            if man and s["start"] < o["end"] and s["end"] > o["start"] and man.get(ref, {}).get("where") == "generic":
                sus.append(f"{s['id']} {s['src']} under “{o['p'].get('text', '')}”")
    row(not sus, "Generic clip under a caption", f"{len(sus)} " + "; ".join(sus), "the picture under a lower third must show what it names; never caption stock as a named place")
    # graphics
    gpm = len(O) / mins
    row(gpm >= 2.5, "Graphics density", f"{len(O)} graphics, {gpm:.1f}/min", "2.5-3/min (50-60 in a 20-min film)")
    full = [o for o in O if o["kind"] in E["full_kinds"]]
    stat = [f"{o['id']} {o['p']['dur'] - max(o['p']['at']):.1f}s" for o in full if o["p"]["dur"] - max(o["p"]["at"]) > P.cfg["overlay"]["full_hold"] + 0.1]
    row(not stat, "Full-screen graphics holding still", f"{len(stat)} " + ", ".join(stat[:5]), f"≤ {P.cfg['overlay']['full_hold']} s after the last beat")
    t = next((o for o in O if o["kind"] == "title"), None)
    ch = min((o for o in O if o["kind"] == "chapter" and t and o["start"] > t["start"]), key=lambda o: o["start"], default=None)
    if t and ch:
        g = ch["start"] - t["end"]
        row(g >= 1.5, "Title → first chapter gap", f"{g:.1f} s", "≥ 1.5 s of black between them")
    # audio
    plan = P.load("07_Audio", "audio_plan.json", default=None)
    if plan:
        from .audio import coverage
        cv = coverage(P, plan)
        row(cv >= 0.85, "Music under the narration", f"{cv * 100:.0f}%", "≥ 85% (near-continuous score)")
        gains = [m["gain_db"] for m in plan["music"]]
        row(True, "Music cue gains", f"{min(gains):.0f} … {max(gains):.0f} dB", "aim for the bed about 15 dB under the voice after ducking")
    film = args[0] if args else P.out(P.cfg["output"])              # qc <file>: the film Resolve rendered
    mix = film if args else P.p("07_Audio", "final_mix.wav")
    if os.path.exists(mix):
        i, tp = loudness(mix)
        row(i is not None and abs(i - P.cfg["audio"]["lufs"]) <= 1.0 and (tp is None or tp <= -1.0), "Loudness" + (" (rendered film)" if args else " (final mix)"),
            f"{i} LUFS, true peak {tp} dBFS", f"{P.cfg['audio']['lufs']} ±1 LUFS, true peak ≤ −1 dBFS")
    if os.path.exists(film):
        n = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=nb_frames,width,height", "-of", "csv=p=0", film],
                           capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip().split(",")
        want = round(TL["end"] * P.cfg["render"]["fps"])
        row(n[0] in (str(P.cfg["render"]["width"]),) and abs(int(n[2]) - want) <= 2 if len(n) == 3 else False,
            "Render", f"{n[0]}x{n[1]}, {n[2] if len(n) == 3 else '?'} frames", f"{P.cfg['render']['width']}x{P.cfg['render']['height']}, {want} frames")
    head = [f"# QC — {P.cfg['title']}", "", f"Film {tc(TL['end'])} · {len(TL['lines'])} voice lines · {len(TL['blocks'])} blocks · "
            f"{'all checks pass' if not fails else f'{fails} to fix'}", "", "| | Check | Value | Rule |", "|---|---|---|---|"]
    tail = ["", "Not checked by machine — watch for these: wrong place or country in a shot (flags, signs, writing in another language), "
            "children's faces, watermarks or logos, a picture that contradicts the line, blurry or broken clips, captions that claim a place the "
            "picture is not."]
    open(P.out("QC_REPORT.md"), "w", encoding="utf-8").write("\n".join(head + R + tail) + "\n")
    print("\n".join(head[2:3] + R))
    print("->", P.out("QC_REPORT.md"))
