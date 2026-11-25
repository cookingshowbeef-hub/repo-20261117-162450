"""The edit: the asset codes of each VISUAL note, laid on the narration clock -> 05_Renders/edit.json

Asset codes in script_template.md VISUAL lines, in narration order:
  photo:<topic>#<n>[, #<n>...]   Wikimedia Commons photo (03_Images/commons, numbered as on its contact sheet)
  px:<id> / pb:<id>               Pexels / Pixabay clip (02_B-Roll/pexels|pixabay)
  nasa:<topic>                    NASA image (03_Images/nasa); topics in edit.nasa_sequences play every file in order
  file:<path>                     any image or clip, path relative to the project
  lk:<id>                         local footage: id -> absolute path in 02_B-Roll/local/index.json (paths with spaces/Vietnamese)
  <code>@"phrase"                 word anchor: the picture comes in 0.15 s before that phrase is spoken in the block's lines
  <code>@+2.4                      time mark: the picture comes in 2.4 s after the block's first line starts
edit.mode "timed" (recommended): every picture starts at its mark and lasts until the next one; the first picture of a block
opens it, unmarked pictures share the stretch between marks evenly. Nothing is moved, dropped or filled from a pool: a shot under
edit.timed_min s, marks out of order or a phrase missing from the transcript stop the build with the line named; shots longer than
edit.max_own and clip reuse are reported as warnings. Both modes write 05_Renders/shots.csv (time, picture, mark, line).
For each V.O. block the pictures named above it fill the picture from the end of the previous block to the end of this one
(the next act's picture sits under its act card). Shot length comes from time (edit.target / max / min), cuts snap to narration
pauses only when every shot stays inside the limits. Each picture once per block; clips at most edit.clip_cap times in the film and
never twice within edit.clip_gap s; photos at most edit.photo_cap times. Short blocks borrow from the section's spare pool
(pools.py: POOLS + section(block)); no pools.py = the act's own clips.
Full-screen graphics (edit.full_kinds) get a plain plate under them so no footage flashes between them; title -> first chapter
sits on black and the next shot fades up.
"""
import unicodedata
import json, math, os, re, sys
import numpy as np, cv2
from .ctx import VO

ASSET = re.compile(r"photo:(\w+)((?:#\d+(?:, )?)+)|(px|pb):(\d+)|nasa:(\w+)|file:([^\s;,)@]+)|lk:([\w-]+)")
# word anchor: px:123@"double rainbow" = this picture comes in when that phrase is spoken (in this block's lines)
ANCHOR = re.compile(r'((?:px|pb):\d+|photo:\w+#\d+|nasa:\w+|file:[^\s;,)@]+|lk:[\w-]+)@(?:"([^"]+)"|\+(\d+(?:\.\d+)?))')
anchor_val = lambda m: m.group(2) if m.group(2) is not None else float(m.group(3))
norm = lambda w: re.sub(r"[^\w']", "", unicodedata.normalize("NFC", w).lower().replace("’", "'"))   # Unicode-aware (Vietnamese diacritics)
is_clip = lambda a: a.split(":")[0] in ("px", "pb", "lk") or (a.startswith("file:") and a.lower().endswith((".mp4", ".mov", ".webm", ".mkv")))


class Edit:
    def __init__(self, P):
        self.P, self.E = P, P.cfg["edit"]
        self.TL = P.timeline()
        self.IDX = P.load("03_Images", "commons", "sheets", "index.json", default={})
        self.MAN = P.load("03_Images", "commons", "manifest.json", default={})
        self.NASA = P.load("03_Images", "nasa", "manifest.json", default={})
        W = []
        for l in self.TL["lines"]:
            W += [(l["start"] + a, l["start"] + b) for _, a, b in P.words(l["id"])]
        self.PAUSES = [round((W[i - 1][1] + W[i][0]) / 2, 3) for i in range(1, len(W)) if W[i][0] - W[i - 1][1] >= 0.18]
        self.PAUSES += [l["end"] + 0.25 for l in self.TL["lines"]]
        self.pools = P.spec("pools", required=False)
        self.USES, self.LAST = {}, {}
        self.LN = {l["id"]: l for l in self.TL["lines"]}

    # ------------------------------------------------------------ word anchors
    def word_time(self, b, phrase, strict=True):
        if not isinstance(phrase, str):                              # @+sec: seconds after the block's first line starts
            return self.LN[b["lines"][0]]["start"] + phrase + 0.15
        t = [x for x in map(norm, phrase.split()) if x]
        for lid in b["lines"]:
            ws = [(norm(w), a) for w, a, _ in self.P.words(lid)]
            ws = [x for x in ws if x[0]]
            for i in range(len(ws)):
                if [w for w, _ in ws[i:i + len(t)]] == t:
                    return self.LN[lid]["start"] + ws[i][1]
        if not strict:
            return None
        sys.exit(f"{' '.join(b['lines'])}: anchor phrase {phrase!r} is not in the transcript (doc.py script shows the words)")

    def build_timed(self, blocks, groups, anchors):
        """edit.mode "timed": pictures start exactly at their marks; problems are reported, never patched over."""
        E, MIN, MAXO = self.E, self.E.get("timed_min", 2.0), self.E.get("max_own", 7.0)
        errs, warns, shots, moves, used = [], [], [], ["in", "right", "out", "left"], {}
        for k, (b, assets) in enumerate(zip(blocks, groups)):
            ids = " ".join(b["lines"])
            lo = 0.0 if k == 0 else shots[-1]["end"]
            hi = blocks[k + 1]["start"] - 0.05 if k + 1 < len(blocks) else self.TL["end"]
            if k + 1 < len(blocks) and blocks[k + 1]["act"] != b["act"]:
                hi = blocks[k + 1]["start"] - self.P.cfg["timing"]["next_act_lead"]
            if k and assets is groups[k - 1]:                        # no VISUAL line of its own: the last picture holds on
                shots[-1]["end"] = round(hi, 3)
                continue
            if not assets:
                errs.append(f"{ids}: no pictures"); continue
            anc = anchors[k]
            T, marks = [None] * len(assets), ["line start"] + ["even"] * (len(assets) - 1)
            T[0] = lo
            for i, a in enumerate(assets):
                if a not in anc:
                    continue
                v = anc[a]
                t = self.word_time(b, v, strict=False)
                if t is None:
                    errs.append(f"{ids}: {a} phrase {v!r} is not in the transcript"); continue
                t, marks[i] = round(t - 0.15, 3), (f'"{v}"' if isinstance(v, str) else f"+{v}")
                if i == 0:
                    if shots and t > lo:                             # first picture marked later: the previous picture holds until it
                        shots[-1]["end"] = T[0] = t
                    continue
                T[i] = t
            known = [i for i, t in enumerate(T) if t is not None]
            for j, i in enumerate(known):                            # unmarked pictures share the stretch between marks evenly
                i2 = known[j + 1] if j + 1 < len(known) else len(assets)
                t2 = T[i2] if i2 < len(assets) else hi
                for q in range(i + 1, i2):
                    T[q] = round(T[i] + (t2 - T[i]) * (q - i) / (i2 - i), 3)
            ends = T[1:] + [round(hi, 3)]
            for i, a in enumerate(assets):
                s, e = T[i], ends[i]
                under = self.hidden(s, e) and self.covered(s, e) > 0     # mostly behind a full-screen graphic: becomes the plate
                if e - s < MIN and not under:
                    errs.append(f"{ids}: {a} ({marks[i]}) would be on screen {e - s:.2f}s at {s:.2f}s (min {MIN}s)"
                                + (" - marks out of order" if e < s else ""))
                    continue
                if under:
                    a = f"plate:{E['plate']}"
                elif e - s > MAXO:
                    warns.append(f"{ids}: {a} holds {e - s:.1f}s at {s:.1f}s - add a picture or a mark")
                if is_clip(a):
                    if self.USES.get(a, 0) >= self.cap(a):
                        warns.append(f"{ids}: {a} used {self.USES[a] + 1}x (clip_cap {self.cap(a)})")
                    elif self.recent(a, s):
                        warns.append(f"{ids}: {a} again {s - self.LAST[a]:.0f}s after its last use (clip_gap {E['clip_gap']})")
                    self.LAST[a] = s
                self.USES[a] = self.USES.get(a, 0) + 1
                mv = ""
                if a.startswith("photo:"):
                    u = used.get(a, 0); used[a] = u + 1
                    mv = "detail" if u % 3 == 2 else moves[(k + i) % 4]
                shots.append(dict(block=b["id"], act=b["act"], start=s, end=e, src=a, treatment=mv, mark=marks[i],
                                  focus=self.focus(a.split(":", 1)[1]) if mv == "detail" else None))
        for w in warns:
            print("warning:", w)
        if errs:
            print("\n".join(f"ERROR: {x}" for x in errs))
            sys.exit(f"{len(errs)} timing problem(s) in script_template.md - fix the marks above, nothing was written")
        shots = self.under_graphics(shots)
        for i, s in enumerate(shots):
            s["id"] = f"S{i:03d}"
        shots[0]["fade_in"] = True
        return shots, groups

    def anchor_cuts(self, b, assets, anc, lo, hi):
        """cuts for a block with anchored pictures: each anchored picture starts 0.15 s before its phrase; the pictures between
        two anchors share that stretch evenly. An anchored first picture simply opens the block."""
        gap = 2.1                                                    # shots under 2 s count as hidden and become plates
        pts = [(0, lo)]
        for i, a in enumerate(assets):
            if a in anc and i > 0:
                t = max(pts[-1][1] + gap, self.word_time(b, anc[a]) - 0.15)
                if t > hi - gap:
                    break                                            # no room left: later anchored pictures are dropped
                pts.append((i, t))
        cuts, order = [], []
        for j, (i, t) in enumerate(pts):
            i2, t2 = pts[j + 1] if j + 1 < len(pts) else (len(assets), hi)
            m = max(1, min(i2 - i, int((t2 - t) // gap)))
            cuts += [round(t + (t2 - t) * q / m, 3) for q in range(m)]
            order += assets[i:i + m]
        return cuts + [round(hi, 3)], order

    # ------------------------------------------------------------ assets
    def expand(self, line):
        out = []
        for m in ASSET.finditer(line):
            if m.group(1):
                out += [f"photo:{m.group(1)}#{n}" for n in re.findall(r"#(\d+)", m.group(2))]
            elif m.group(3):
                out.append(f"{m.group(3)}:{m.group(4)}")
            elif m.group(5):
                t = m.group(5)
                files = sorted(v["file"] for v in self.NASA.values() if v["topic"] == t)
                big = [f for f in files if "_lrg" in f]
                files = big or files
                if not files:
                    sys.exit(f"no NASA images for topic {t}")
                out += [f"nasa:{f}" for f in files] if t in self.E["nasa_sequences"] else [f"nasa:{files[0]}"]
            elif m.group(7):
                out.append(f"lk:{m.group(7)}")
            else:
                out.append(f"file:{m.group(6)}")
        return out

    def photo_path(self, ref):
        return self.P.p("03_Images", "commons", self.MAN[self.IDX[ref]]["file"])

    def cap(self, a):
        return self.E["clip_cap"] if is_clip(a) else (self.E["photo_cap"] if a.startswith(("photo:", "file:")) else 99)

    def recent(self, a, t):
        return a in self.LAST and t - self.LAST[a] < self.E["clip_gap"]

    def focus(self, ref, z=1.65):
        """busiest window of the photo for a detail move (fine-detail energy), as (cx, cy) in 0..1 of the cover-fitted frame."""
        img = cv2.imdecode(np.fromfile(self.photo_path(ref), np.uint8), cv2.IMREAD_COLOR)
        s = max(1920 / img.shape[1], 1080 / img.shape[0])
        img = cv2.resize(img, (round(img.shape[1] * s), round(img.shape[0] * s)), interpolation=cv2.INTER_AREA)
        oy, ox = (img.shape[0] - 1080) // 2, (img.shape[1] - 1920) // 2
        g = cv2.cvtColor(img[oy:oy + 1080, ox:ox + 1920], cv2.COLOR_BGR2GRAY)
        e = cv2.GaussianBlur(np.abs(cv2.Laplacian(cv2.GaussianBlur(g, (0, 0), 1.5), cv2.CV_32F)), (0, 0), 25)
        ww, wh = int(1920 / z), int(1080 / z)
        best, bc = -1, (0.5, 0.5)
        for cy in range(wh // 2, 1080 - wh // 2 + 1, 30):
            for cx in range(ww // 2, 1920 - ww // 2 + 1, 30):
                v = e[cy - wh // 2:cy + wh // 2, cx - ww // 2:cx + ww // 2].mean()
                if v > best:
                    best, bc = v, (cx / 1920, cy / 1080)
        return [round(bc[0], 3), round(bc[1], 3)]

    # ------------------------------------------------------------ cuts
    def cut_near(self, prev, left, hi):
        """next cut after prev with `left` shots still to place before hi: an even share, moved onto a narration pause only when
        that keeps this shot and every later one between min and max."""
        mn, mx = self.E["min"], self.E["max"]
        want = prev + (hi - prev) / left
        ok = lambda p: mn <= p - prev <= mx and (left - 1) * mn <= hi - p <= (left - 1) * mx
        c = [p for p in self.PAUSES if abs(p - want) <= 0.9 and ok(p)]
        return min(c, key=lambda p: abs(p - want)) if c else want

    def full_windows(self):
        O = self.P.load_out("overlays.json")
        win = []
        for o in sorted((o for o in O if o["kind"] in self.E["full_kinds"]), key=lambda o: o["start"]):
            if win and o["start"] - win[-1][1] < self.E["merge_gap"]:
                win[-1][1] = o["end"]
            else:
                win.append([o["start"], o["end"], self.E["plate"]])
        t = next((o for o in O if o["kind"] == "title"), None)
        if self.E["title_black"] and t:
            chs = [o for o in O if o["kind"] == "chapter" and o["start"] > t["start"]]
            if chs:
                win.append([t["start"], min(chs, key=lambda o: o["start"])["start"] + self.E["fade"], "000000"])
        return sorted(win)

    def covered(self, a, b):
        F = self.E["fade"]
        return sum(max(0.0, min(b, we - F) - max(a, ws + F)) for ws, we, _ in self.WIN)

    def hidden(self, a, b):
        return (b - a) - self.covered(a, b) < 2.0

    def under_graphics(self, shots):
        F, MIN = self.E["fade"], self.E["min"]
        for ws, we, col in self.WIN:
            a, b = ws + F, we - F
            before = [dict(x) for x in shots if x["start"] < a]
            after = [dict(x) for x in shots if x["end"] > b]
            if not before or not after:
                continue
            if len(before) > 1 and a - before[-1]["start"] < 3.2:
                c = round(a - MIN, 3)
                if a - before[-2]["start"] > 5.5 and c - before[-2]["start"] >= MIN:
                    before[-2]["end"] = before[-1]["start"] = c
                else:
                    before.pop()
            if len(after) > 1 and after[0]["end"] - we < 3.2:
                c = round(we + MIN, 3)
                if after[1]["end"] - we > 5.5 and after[1]["end"] - c >= MIN:
                    after[0]["end"] = after[1]["start"] = c
                else:
                    after.pop(0)
            before[-1]["end"], after[0]["start"] = round(a, 3), round(b, 3)
            plate = dict(block=before[-1]["block"], act=before[-1]["act"], start=round(a, 3), end=round(b, 3), src=f"plate:{col}", treatment="", focus=None)
            if col == "000000":
                after[0]["fade_in"] = True
            shots = before + [plate] + after
        return shots

    # ------------------------------------------------------------ main
    def section(self, b):
        return self.pools.section(b) if self.pools else b["act"]

    def pool(self, sec):
        if self.pools:
            return self.pools.POOLS[sec]
        return sorted(self.ACT_POOL.get(sec, []))

    def build(self):
        E = self.E
        self.WIN = self.full_windows()
        groups, pending, last, anchors, pend_anc = [], [], [], [], {}
        for line in self.P.template().split("\n"):
            if line.startswith("**VISUAL"):
                pending += self.expand(line)
                pend_anc.update({m.group(1): anchor_val(m) for m in ANCHOR.finditer(line)})
            for _ in VO.findall(line):
                assets = pending or last
                groups.append(assets); anchors.append(pend_anc if pending else {}); last = assets; pending = []; pend_anc = {}
        blocks = self.TL["blocks"]
        assert len(groups) == len(blocks), (len(groups), len(blocks))
        missing = sorted({a for g in groups for a in g if a.startswith("photo:") and a[6:] not in self.IDX})
        if missing:
            sys.exit(f"photo codes not on the contact sheets: {missing[:10]}")
        self.ACT_POOL = {}
        for blk, assets in zip(blocks, groups):
            self.ACT_POOL.setdefault(blk["act"], set()).update(a for a in assets if is_clip(a))
        if E.get("mode") == "timed":
            return self.build_timed(blocks, groups, anchors)
        seqs = tuple(f"nasa:{t}/" for t in E["nasa_sequences"])
        shots, moves, used = [], ["in", "right", "out", "left"], {}
        for k, (b, assets) in enumerate(zip(blocks, groups)):
            lo = 0.0 if k == 0 else shots[-1]["end"]
            hi = blocks[k + 1]["start"] - 0.05 if k + 1 < len(blocks) else self.TL["end"]
            if k + 1 < len(blocks) and blocks[k + 1]["act"] != b["act"]:
                hi = blocks[k + 1]["start"] - self.P.cfg["timing"]["next_act_lead"]
            span = hi - lo
            nasa_seq = bool(seqs) and all(a.startswith(seqs) for a in assets)
            n = max(1, min(max(round(span / E["target"]), math.ceil(span / E["max"])), int(span // E["min"])))
            if (k == 0 or assets is not groups[k - 1]) and 0 < len(assets) < n:
                # too few pictures named for this line: hold each of its own pictures longer (up to edit.max_own s) rather than
                # filling with unrelated pool clips, so the picture stays on what the narration is saying
                n = max(len(assets), math.ceil(span / E.get("max_own", 7.0)))
            if nasa_seq:
                n = max(1, min(len(assets), int(span // E["min"])))
            cuts = [lo]
            for i in range(1, n):
                cuts.append(round(self.cut_near(cuts[-1], n - i + 1, hi), 3))
            cuts.append(round(hi, 3))
            order = None
            if anchors[k] and not nasa_seq:
                cuts, order = self.anchor_cuts(b, assets, anchors[k], lo, hi)
                n = len(cuts) - 1
            seq, sec, vis = [], self.section(b), 0
            POOL = self.pool(sec)
            for i in range(n):
                if self.hidden(cuts[i], cuts[i + 1]):
                    seq.append((f"plate:{E['plate']}", 0)); continue
                own = 0 if (k and assets is groups[k - 1] and vis) else len(assets)
                i, vis = vis, vis + 1
                pick = None
                if nasa_seq:
                    pick = (assets[i % len(assets)], 0)
                elif i < own:
                    a = order[i] if order and i < len(order) else assets[i % len(assets)]
                    if self.USES.get(a, 0) < self.cap(a) and not (seq and seq[-1][0] == a) and not (is_clip(a) and (i >= len(assets) or self.recent(a, lo))):
                        pick = (a, i // len(assets))
                if pick is None:
                    spare = [x for x in POOL + [y for y in assets if not y.startswith("nasa")]
                             if self.USES.get(x, 0) < self.cap(x) and x not in [s_[0] for s_ in seq] and not (is_clip(x) and self.recent(x, lo))]
                    if not spare:
                        spare = sorted(POOL + assets, key=lambda x: self.USES.get(x, 0))
                    pick = (min(spare, key=lambda x: (self.USES.get(x, 0), POOL.index(x) if x in POOL else 99)), 0)
                self.USES[pick[0]] = self.USES.get(pick[0], 0) + 1
                self.LAST[pick[0]] = lo
                seq.append(pick)
            for i, (a, rep) in enumerate(seq):
                mv = ""
                if a.startswith("photo:"):
                    u = used.get(a, 0); used[a] = u + 1
                    mv = "detail" if rep or u % 3 == 2 else moves[(k + i) % 4]
                shots.append(dict(block=b["id"], act=b["act"], start=cuts[i], end=cuts[i + 1], src=a, treatment=mv,
                                  focus=self.focus(a.split(":", 1)[1]) if mv == "detail" else None))
        shots = self.under_graphics(shots)
        for i, s in enumerate(shots):
            s["id"] = f"S{i:03d}"
        shots[0]["fade_in"] = True
        return shots, groups


def write_shot_list(P, ed, shots):
    """05_Renders/shots.csv: one row per shot - when it comes in, how long, the picture, its mark and the line being spoken."""
    import csv
    tc = lambda t: f"{int(t // 60)}:{t % 60:05.2f}"
    lines = ed.TL["lines"]
    with open(P.out("shots.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["shot", "start", "end", "dur", "block", "picture", "mark", "line", "words from the cut"])
        for s in shots:
            ln = next((l for l in lines if l["start"] <= s["start"] + 0.2 <= l["end"] + 0.8), None)
            said = ""
            if ln:
                ws = [x for x in P.words(ln["id"]) if ln["start"] + x[2] > s["start"] + 0.1]
                said = " ".join(x[0] for x in ws[:6])
            w.writerow([s["id"], tc(s["start"]), tc(s["end"]), f"{s['end'] - s['start']:.2f}", s["block"], s["src"],
                        s.get("mark", ""), ln["id"] if ln else "", said])


def run(P, args):
    sys.stdout.reconfigure(encoding="utf-8")
    ed = Edit(P)
    shots, groups = ed.build()
    P.save_out("edit.json", shots)
    write_shot_list(P, ed, shots)
    d = np.array([s["end"] - s["start"] for s in shots])
    kinds = {}
    for s in shots:
        kinds[s["src"].split(":")[0]] = kinds.get(s["src"].split(":")[0], 0) + 1
    print(f"{len(shots)} shots, film {ed.TL['end']:.1f}s | median {np.median(d):.1f}s, max {d.max():.1f}s, <1.8s {np.sum(d < 1.8)} | {kinds}")
    print("distinct pictures:", len({s['src'] for s in shots if not s['src'].startswith('plate')}))
