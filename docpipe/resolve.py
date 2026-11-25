"""Review cut for DaVinci Resolve (Free or Studio): the film as an editable timeline, so the script's owner can watch and comment
before the final render, then the comments come back here as a list of fixes.

  doc.py <prj> review [--force]   -> 05_Renders/review/: timeline.fcpxml + its media, then File > Import > Timeline in Resolve
  doc.py <prj> notes <file.edl>   Resolve's "File > Export > Timeline Markers to EDL" -> 05_Renders/review/REVIEW_NOTES.md

Timeline (all on the film clock, 30 fps), built from the source files: nothing is rendered but the HUD.
  V1  every shot from its source, named "S131 px:6831205": stock clips at the renderer's in-point and speed, photos with the
      renderer's camera move as scale/position keyframes, plates as solid frames
  V2  the Remotion graphics (their ProRes 4444 files, with alpha)
  V3  the HUD (film.json "hud"), as one alpha clip, when the film has one
  A1  each voice line; then the music cues, then the sound effects, each at the mix's level (music held duck_db lower)
  --rendered: V1 = one rendered picture track and A1-A3 = mixed stems instead (exactly the final look; takes a render)
  markers  one per V.O. block (blue) with its narration; subtitles: narration.srt (File > Import > Subtitle)
Comments: add a marker (M) where something is wrong and type the note in it; any colour. Export the markers to EDL and run `notes`.
"""
import glob, json, os, re, subprocess, sys
from urllib.parse import quote
from xml.sax.saxutils import escape as _esc


def escape(x):
    """XML-escape for attribute values too: a narration line with "quotes" broke Resolve's parser (DOM parser error)."""
    return _esc(x, {'"': "&quot;"})
import numpy as np, cv2


def fr(t, fps):
    return round(t * fps)


def rt(n, fps):
    """frames -> FCPXML rational time."""
    return f"{n * 100}/{fps * 100}s" if n else "0s"


def url(path):
    return "file:///" + quote(os.path.abspath(path).replace("\\", "/"), safe="/:")


def probe_frames(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries", "stream=nb_read_packets",
                          "-of", "csv=p=0", path], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()
    return int(out)


def hud_clip(P, R, path):
    """the HUD alone as a small alpha clip: only the 16:9 window (a 1/k-size of the frame) that holds it, so it renders in minutes.
    Alpha from drawing on black and on white. Writes <path>.json with where the window sits: {k, cx, cy} (frame pixels);
    the timeline scales the clip by 1/k after Resolve's fit-to-frame and moves it there, so it lands pixel for pixel."""
    hud = R.hud()
    W, H, FPS = R.W, R.H, R.FPS
    n = fr(R.TL["end"], FPS)
    black = np.zeros((H, W, 3), np.uint8)
    seen = np.zeros((H, W), bool)
    for t in np.linspace(0, R.TL["end"], 400):                   # the box the HUD ever uses
        seen |= hud.draw(black.copy(), float(t)).any(2)
    ys, xs = np.nonzero(seen)
    if not len(ys):
        ys, xs = np.array([H - 2, H - 1]), np.array([0, 1])
    m = 40
    by0, by1, bx0, bx1 = max(0, ys.min() - m), min(H, ys.max() + m), max(0, xs.min() - m), min(W, xs.max() + m)
    k = 1
    for kk in (4, 3, 2):                                         # the smallest 16:9 window that holds it
        if (bx1 - bx0) <= W // kk and (by1 - by0) <= H // kk:
            k = kk
            break
    ww, wh = W // k, H // k
    x0 = min(max(0, (bx0 + bx1) // 2 - ww // 2), W - ww)
    y0 = min(max(0, (by0 + by1) // 2 - wh // 2), H - wh)
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{ww}x{wh}", "-r", str(FPS), "-i", "-",
                            "-c:v", "png", "-pix_fmt", "rgba", path], stdin=subprocess.PIPE)
    empty = np.zeros((wh, ww, 4), np.uint8).tobytes()
    for i in range(n):
        b = hud.draw(black.copy(), i / FPS)[y0:y0 + wh, x0:x0 + ww]
        if not b.any():
            enc.stdin.write(empty)
            continue
        w = hud.draw(np.full((H, W, 3), 255, np.uint8), i / FPS)[y0:y0 + wh, x0:x0 + ww]
        a = 255 - (w.astype(np.int16) - b.astype(np.int16)).max(2).clip(0, 255).astype(np.uint8)
        col = np.where(a[..., None] > 0, (b.astype(np.uint16) * 255 // np.maximum(a, 1)[..., None]).clip(0, 255), 0).astype(np.uint8)
        enc.stdin.write(np.dstack([col, a]).tobytes())
    enc.stdin.close(); enc.wait()
    json.dump(dict(k=k, cx=x0 + ww / 2, cy=y0 + wh / 2), open(path + ".json", "w"))


def srt(TL, path):
    s = lambda t: "%02d:%02d:%02d,%03d" % (t // 3600, t % 3600 // 60, t % 60, round(t % 1 * 1000) % 1000)
    out = []
    for k, l in enumerate(TL["lines"], 1):
        out.append(f"{k}\n{s(l['start'])} --> {s(l['end'])}\n[{l['id']}] {l['text']}\n")
    open(path, "w", encoding="utf-8").write("\n".join(out))


def photo_views(img_w, img_h, W, H, move, focus, k):
    """the renderer's camera move on a still (render.Renderer.photo) as start/end (cx, cy, zoom) on the cover-fitted picture,
    clamped the same way, plus the cover-fitted size in frame pixels."""
    s = max(W / img_w, H / img_h)
    cw0, ch0 = img_w * s, img_h * s
    move = move or ["in", "out", "right", "left"][k % 4]
    rx = lambda z: max(0.0, 0.5 - W / z / cw0 / 2)
    ry = lambda z: max(0.0, 0.5 - H / z / ch0 / 2)
    if move == "in":
        a, b = (0.5, 0.5, 1.0), (0.5, 0.5, 1.10)
    elif move == "out":
        a, b = (0.5, 0.5, 1.10), (0.5, 0.5, 1.0)
    elif move in ("left", "right"):
        d = min(rx(1.12) * 0.85, 0.06 + rx(1.0) * 0.6)
        a, b = (0.5 + d, 0.5, 1.12), (0.5 - d, 0.5, 1.12)
        if move == "right":
            a, b = b, a
    elif move in ("up", "down"):
        d = min(ry(1.10) * 0.85, 0.05 + ry(1.0) * 0.7)
        a, b = (0.5, 0.5 + d, 1.10), (0.5, 0.5 - d, 1.10)
        if move == "down":
            a, b = b, a
    elif move == "detail" and focus:
        fx, fy = ((cw0 - W) / 2 + focus[0] * W) / cw0, ((ch0 - H) / 2 + focus[1] * H) / ch0
        a, b = (fx, fy, 1.62), (fx, fy, 1.72)
    else:
        a, b = (0.5, 0.5, 1.03), (0.5, 0.5, 1.05)

    def clamp(v):
        cx, cy, z = v
        hx, hy = W / z / cw0 / 2, H / z / ch0 / 2
        return (min(max(cx, hx), 1 - hx), min(max(cy, hy), 1 - hy), z)
    return clamp(a), clamp(b), cw0, ch0


def drop_frame_tc(path):
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream_tags=timecode:format_tags=timecode", "-of", "default=nw=1:nk=1", path],
                       capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    return ";" in o


def safe_name(path, D):
    """Resolve fails to find some media whose file name is not ASCII (Cyrillic, accents) or whose path runs long, and then asks
    "clips were not found" — a dialog a script cannot answer, so the whole import is cancelled. Such a file gets an ASCII-named
    hard link (same disk, no copy; a copy if linking fails) in review/links, and the timeline points there."""
    import hashlib, shutil, unicodedata
    name = os.path.basename(path)
    if path.lower().endswith((".mp4", ".mov", ".m4v")) and drop_frame_tc(path):
        # Resolve and FCPXML disagree on drop-frame timecode, so the clip is "not found" or offline: a lossless remux
        # without the timecode track (starts at 0) sidesteps it
        dst = os.path.join(D, "links", re.sub(r"[^A-Za-z0-9_-]+", "_", os.path.splitext(name)[0])[:40] + "_notc.mp4")
        if not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", path, "-map", "0:v:0", "-map", "0:a?", "-c", "copy",
                            "-map_metadata", "-1", "-write_tmcd", "0", dst], check=True)
        return dst
    if name.isascii() and len(path.encode("utf-8")) < 240:
        return path
    base, ext = os.path.splitext(name)
    ascii_ = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode() or "media"
    ascii_ = re.sub(r"[^A-Za-z0-9_-]+", "_", ascii_)[:40].strip("_") or "media"
    dst = os.path.join(D, "links", f"{ascii_}_{hashlib.md5(path.encode('utf-8')).hexdigest()[:8]}{ext.lower()}")
    if not os.path.exists(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        try:
            os.link(path, dst)
        except OSError:
            shutil.copy2(path, dst)
    return dst


_SRC = {}


def src_info(path):
    """a clip's own frame rate (num/den), size, frame count and start timecode (in its frames), as Resolve reads them."""
    if path in _SRC:
        return _SRC[path]
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=r_frame_rate,width,height,nb_frames,duration:stream_tags=timecode:format=duration:format_tags=timecode",
                                   "-of", "json", path], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout)
    st, fm = j["streams"][0], j.get("format", {})
    num, den = map(int, st["r_frame_rate"].split("/"))
    dur = float(st.get("duration") or fm.get("duration") or 0)
    frames = int(st["nb_frames"]) if str(st.get("nb_frames", "")).isdigit() else int(dur * num / den)
    tc = (st.get("tags") or {}).get("timecode") or (fm.get("tags") or {}).get("timecode")
    tcf = 0
    if tc and ";" in tc:
        tc = None                                                    # drop-frame: the timeline uses a remux without timecode (safe_name)
    if tc:
        h, m, s_, f = map(int, re.split(r"[:;.]", tc))
        nominal = round(num / den)
        tcf = ((h * 60 + m) * 60 + s_) * nominal + f
        if ";" in tc or "," in tc:                                   # drop-frame: 2 (or 4 at 59.94) labels skipped each minute but every 10th
            drop = round(nominal / 15)
            mins = h * 60 + m
            tcf -= drop * (mins - mins // 10)
    _SRC[path] = dict(num=num, den=den, w=int(st["width"]), h=int(st["height"]), frames=frames, tc=tcf)
    return _SRC[path]


def clip_timing(path, n, FPS, uses):
    """the renderer's in-point and speed for a stock clip (render.Renderer.video): (in seconds, speed, clip seconds)."""
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    nf = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    cdur, dur = nf / fps, n / FPS
    k = uses.get(path, 0); uses[path] = k + 1
    room = max(0.0, cdur - 0.3 - dur)
    a = min(0.4, room) + room * [0.0, 0.5, 0.85][k % 3] * (0.9 if room > 0.4 else 0)
    span = min(dur, cdur - a - 0.05)
    speed = max(min(1.0, span / dur) if dur > 0 else 1.0, 0.5)
    return a, speed, cdur


def rms_db(path):
    from .audio import load
    x = load(path)
    loud = x[np.abs(x).max(1) > 10 ** (-50 / 20)]
    return 20 * np.log10(np.sqrt(np.mean(loud ** 2)) + 1e-9), len(x) / 48000


def duration_s(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout)


class Lanes:
    """greedy lanes for clips that may overlap (music cues, sound effects)."""
    def __init__(self, first, step):
        self.ends, self.first, self.step = [], first, step

    def take(self, a, b):
        for i, e in enumerate(self.ends):
            if e <= a:
                self.ends[i] = b
                return self.first + i * self.step
        self.ends.append(b)
        return self.first + (len(self.ends) - 1) * self.step

    def last(self):
        return self.first + max(0, len(self.ends) - 1) * self.step


LUT_DIR = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\LUT\docpipe"


def grade_lut(P, path, n=33):
    """render.Renderer.grade without the vignette (S-curve per channel with the cool tint, then saturation) as a 3D .cube LUT."""
    from .style import curve as style_curve
    g = P.cfg["render"]["grade"]
    curve = dict(zip("bgr", style_curve(g)))
    v = np.linspace(0, 255, n)
    f = lambda c, t: np.interp(t, np.arange(256), curve[c]) / 255.0
    lines = [f'TITLE "{P.cfg["title"]} grade"', f"LUT_3D_SIZE {n}", "DOMAIN_MIN 0 0 0", "DOMAIN_MAX 1 1 1"]
    for bi in v:                               # .cube: red changes fastest
        for gi in v:
            for ri in v:
                r, g_, b_ = f("r", ri), f("g", gi), f("b", bi)
                y = 0.299 * r + 0.587 * g_ + 0.114 * b_
                s_ = g["saturation"]
                lines.append("%.6f %.6f %.6f" % tuple(np.clip(s_ * c + (1 - s_) * y, 0, 1) for c in (r, g_, b_)))
    open(path, "w").write("\n".join(lines) + "\n")


def vignette_png(P, path, W, H):
    """the renderer's vignette (and letterbox) as black with alpha: laid over the shots, it darkens exactly as the render's multiply does."""
    from .style import vignette
    vig = vignette(P.cfg["render"]["grade"], W, H)                  # with the style's letterbox bars (alpha 255)
    a = np.round((1 - vig) * 255).astype(np.uint8)
    cv2.imencode(".png", np.dstack([np.zeros((H, W, 3), np.uint8), a]))[1].tofile(path)   # tofile: cv2.imwrite fails silently on non-ASCII paths


def voice_activity(P, R, rate=1000):
    """the mix's ducking control (audio.mix): voice present (|x| > 0.01), 0.4 s moving average, x3, clipped — at `rate` Hz."""
    from .audio import load
    n = int((R.TL["end"] + 2) * rate)
    act = np.zeros(n, np.float32)
    hop = 48000 // rate
    for l in R.TL["lines"]:
        x = np.abs(load(P.p("01_Voice", "lines", f"{l['id']}.wav"))[:, 0]) > 0.01
        m = len(x) // hop
        b = x[:m * hop].reshape(m, hop).mean(1)
        s0 = int(l["start"] * rate)
        act[s0:s0 + m] += b[:max(0, n - s0)]
    w = int(0.4 * rate)
    c = np.concatenate([[0], np.cumsum(act, dtype=np.float64)])
    i = np.arange(n)
    return np.clip((c[np.minimum(i + w // 2, n)] - c[np.maximum(i - w // 2, 0)]) / w * 3, 0, 1).astype(np.float32)


def bake_audio(P, R, D, A):
    """every audio element on the film clock as its own file, with what the mix does to it baked in: its level, fades, loops, and
    the ducking under the voice (music duck_db, effects sfx_duck_db, following the voice as in the mix), all scaled so the voice
    sits at audio.voice_rms. Voice lines on A1, music cues on A2+, sound effects after. Returns [{path, frame, frames, track, lane, name, role}]."""
    from concurrent.futures import ThreadPoolExecutor
    import hashlib
    from .audio import load
    FPS, SR, RATE = R.FPS, 48000, 1000
    plan = json.load(open(P.p("07_Audio", "audio_plan.json"), encoding="utf-8"))
    out = os.path.join(D, "audio")
    os.makedirs(out, exist_ok=True)
    act = voice_activity(P, R, RATE)
    vs = [load(P.p("01_Voice", "lines", f"{l['id']}.wav")) for l in R.TL["lines"]]
    allv = np.concatenate(vs)
    k = 10 ** (A["voice_rms"] / 20) / np.sqrt(np.mean(allv[np.abs(allv[:, 0]) > 0.01] ** 2))
    items, jobs = [], []

    def job(src, t_in, off, dur, gain_db, fi, fo, duck_db, label):
        key = hashlib.md5(f"v2|{src}|{t_in:.3f}|{off:.3f}|{dur:.3f}|{gain_db:.2f}|{fi}|{fo}|{duck_db}|{k:.6f}".encode()).hexdigest()[:10]
        dst = os.path.join(out, f"{re.sub(r'[^A-Za-z0-9_]+', '_', label)[:40]}_{key}.wav")
        jobs.append((dst, src, t_in, off, dur, gain_db, fi, fo, duck_db))
        return dst

    cache = {}

    def run(j):
        dst, src, t_in, off, dur, gain_db, fi, fo, duck_db = j
        if os.path.exists(dst):
            return
        x = cache[src] if src in cache else load(src)
        seg = x[int(off * SR):int(off * SR) + int(dur * SR)].copy()
        n = len(seg)
        env = np.full(n, 10 ** (gain_db / 20) * k, np.float32)
        if fi > 0:
            m = min(n, int(fi * SR)); env[:m] *= np.linspace(0, 1, m)
        if fo > 0:
            m = min(n, int(fo * SR)); env[n - m:] *= np.linspace(1, 0, m)
        if duck_db:
            t = t_in + np.arange(n) / SR
            env *= 10 ** (-duck_db * np.interp(t * RATE, np.arange(len(act)), act) / 20)
        seg = (seg * env[:, None]).astype(np.float32)
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "pcm_s24le", dst],
                       input=seg.tobytes(), check=True)
    for l, x in zip(R.TL["lines"], vs):
        p = P.p("01_Voice", "lines", f"{l['id']}.wav")
        d = len(x) / SR
        items.append(dict(path=job(p, l["start"], 0, d, 0, 0, 0.02, 0, l["id"]), frame=fr(l["start"], FPS), frames=max(1, int(d * FPS)),
                          track=1, lane=-1, name=l["id"], role="dialogue"))
    ml = Lanes(2, 1)
    for m in plan["music"]:
        p = P.p("07_Audio", m["file"])
        L = duration_s(p)
        off = m["offset"] if m["offset"] is not None else max(0, L - (m["t_out"] - m["t_in"]))
        d = min(m["t_out"] - m["t_in"], L - off)
        a, n = fr(m["t_in"], FPS), fr(d, FPS)
        tr = ml.take(a, a + n)
        items.append(dict(path=job(p, m["t_in"], off, d, m["gain_db"], m["fade_in"], m["fade_out"], A["duck_db"], m["cue"]), frame=a, frames=n,
                          track=tr, lane=-tr, name=m["cue"], role="music"))
    sl = Lanes(ml.first + len(ml.ends), 1)
    rmsc = {}
    for x in plan["sfx"]:
        p = P.p("07_Audio", x["file"])
        if p not in rmsc:
            rmsc[p] = rms_db(p)
        r_db, L = rmsc[p]
        t_out = x["t_out"] if x["t_out"] is not None else x["t_in"] + (L - x["offset"])
        t, off, first = x["t_in"], x["offset"], True
        while t < t_out - 0.05:
            d = min(t_out - t, L - off)
            if d <= 0.05:
                off = 0
                continue
            last = t + d >= t_out - 0.05
            a, n = fr(t, FPS), max(1, fr(d, FPS))
            tr = sl.take(a, a + n)
            items.append(dict(path=job(p, t, off, d, x["level_db"] - r_db, x["fade_in"] if first else 0, x["fade_out"] if last else 0,
                                       A["sfx_duck_db"], os.path.basename(p)[:-4]), frame=a, frames=n, track=tr, lane=-tr, name=x["note"][:60], role="effects"))
            t, off, first = t + d, 0, False
    for j in jobs:
        if not os.path.exists(j[0]) and j[1] not in cache and sum(1 for q in jobs if q[1] == j[1]) > 1:
            cache[j[1]] = load(j[1])
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(run, jobs))
    level_to_target(P, R, items, A["lufs"])
    return items


def level_to_target(P, R, items, lufs):
    """sum the baked files as Resolve will, measure the loudness, and scale every file so the film lands at `lufs`
    (the engine's mix does this with loudnorm; Resolve has no master gain we can set). Idempotent: a second run finds ~0 dB.
    Reports the peak, since Resolve's mix has no limiter unless one is put on its bus."""
    from .audio import load
    SR = 48000
    bus = np.zeros((int((R.TL["end"] + 2) * SR), 2), np.float32)
    for x in items:
        y = load(x["path"])
        s0 = int(x["frame"] / R.FPS * SR)
        e = min(len(bus), s0 + len(y))
        bus[s0:e] += y[:e - s0]
    tmp = os.path.join(os.path.dirname(items[0]["path"]) if items else ".", "_bus.f32")
    bus.tofile(tmp)
    log = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", tmp, "-af", "ebur128=peak=true",
                          "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    os.remove(tmp)
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", log)[-1])
    tp = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", log)[-1])
    g = lufs - I
    if abs(g) > 0.2:
        for path in sorted({x["path"] for x in items}):
            y = (load(path) * 10 ** (g / 20)).astype(np.float32)
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "pcm_s24le", path],
                           input=y.tobytes(), check=True)
        tp += g
    over = tp > -1.0
    print(f"   audio: {I:.1f} LUFS before, scaled {g:+.1f} dB to {lufs} LUFS; true peak {tp:.1f} dBFS"
          + (" — OVER -1 dBTP: Resolve: Deliver > 'Normalize Audio Levels' (true peak -1) or a limiter on the main bus; Premiere: Export > Effects > Loudness Normalization (true peak -1)" if over else ""))


def review(P, args):
    """the review timeline. Default: every element in place from its source file (clips, photos with their camera moves as
    keyframes, graphics, voice lines, music cues, sound effects): no render, ready in a minute. --rendered: one rendered picture
    track + mixed stems instead (looks exactly like the final, takes as long as a render)."""
    sys.stdout.reconfigure(encoding="utf-8")
    from .render import Renderer
    from . import audio, cues
    R = Renderer(P)
    FPS, W, H = R.FPS, R.W, R.H
    D = P.out("review")
    os.makedirs(D, exist_ok=True)
    force = "--force" in args
    rendered = "--rendered" in args
    stale = lambda f, src: force or not os.path.exists(f) or os.path.getmtime(f) < os.path.getmtime(src)
    end = fr(R.TL["end"], FPS)
    A = P.cfg["audio"]
    hudp = os.path.join(D, "hud.mov")
    no_hud = "--no-hud" in args                                      # leave the HUD out (e.g. while it is still rendering)
    if P.cfg.get("hud") and not no_hud and (stale(hudp, P.out("counter.json")) or not os.path.exists(hudp + ".json")):
        print("rendering the HUD track…", flush=True)
        hud_clip(P, R, hudp)
    srt(R.TL, os.path.join(D, "narration.srt"))
    lut = os.path.join(D, "grade.cube")
    grade_lut(P, lut)
    vig = os.path.join(D, "vignette.png")
    vignette_png(P, vig, W, H)
    assets, res = {}, []

    formats = {}

    def asset(path, video=True, audio_=False, seconds=None, still=False, src=None):
        """src (a stock clip's src_info): the asset declares the file's own frame rate, size, start timecode and length, as
        Resolve checks every clip's in-point against them (a 25 fps or timecoded clip declared as 30 fps from 0 is refused)."""
        if path in assets:
            return assets[path]
        aid = f"a{len(assets) + 1}"
        assets[path] = aid
        path = safe_name(path, D)
        fmt = "r1"
        if src:
            key = (src["num"], src["den"], src["w"], src["h"])
            if key not in formats:
                formats[key] = f"f{len(formats) + 1}"
            fmt = formats[key]
            dur, start = f"{src['frames'] * src['den']}/{src['num']}s", f"{src['tc'] * src['den']}/{src['num']}s" if src["tc"] else "0s"
        else:
            dur, start = ("0s" if still else rt(int((seconds if seconds is not None else duration_s(path)) * FPS), FPS)), "0s"
        attrs = f'id="{aid}" name="{escape(os.path.basename(path))}" start="{start}" duration="{dur}"'
        attrs += f' hasVideo="1" format="{fmt}" videoSources="1"' if video else ""
        attrs += ' hasAudio="1" audioSources="1" audioChannels="2" audioRate="48000"' if audio_ else ""
        res.append(f'  <asset {attrs}>\n   <media-rep kind="original-media" src="{url(path)}"/>\n  </asset>')
        return aid
    clips = []
    blocks = {b["id"]: b for b in R.TL["blocks"]}
    first_in_block = {}
    for s in R.SHOTS:
        first_in_block.setdefault(s["block"], s["id"])

    def marker(s, a_local):
        return ""                                                    # block markers go on the timeline (below)
        if first_in_block[s["block"]] != s["id"] or s["block"] not in blocks:
            return ""
        bl = blocks[s["block"]]
        text = " ".join(f"[{l['id']}] {l['text']}" for l in R.TL["lines"] if l["block"] == s["block"])
        return f'\n    <marker start="{a_local}" duration="{rt(1, FPS)}" value="{escape(bl["id"] + " · " + ", ".join(bl["lines"]))}" note="{escape(text[:900])}"/>'

    # ---------------------------------------------------------------- V1 picture
    slowed = 0
    if rendered:
        pic = os.path.join(D, "picture.mp4")
        if stale(pic, P.out("edit.json")):
            print("rendering the picture track (graded shots, no graphics)…", flush=True)
            R.render(0.0, R.TL["end"], pic, picture_only=True)
        pid = asset(pic)
        for s in R.SHOTS:
            a, b = fr(s["start"], FPS), fr(s["end"], FPS)
            if b > a:
                clips.append(f'   <asset-clip ref="{pid}" lane="1" offset="{rt(a, FPS)}" start="{rt(a, FPS)}" duration="{rt(b - a, FPS)}" '
                             f'name="{escape(s["id"] + " " + s["src"])}">{marker(s, rt(a, FPS))}\n   </asset-clip>')
    else:
        uses = {}
        os.makedirs(os.path.join(D, "plates"), exist_ok=True)
        for s in R.SHOTS:
            a, b = fr(s["start"], FPS), fr(s["end"], FPS)
            n = b - a
            if n <= 0:
                continue
            kind, ref = s["src"].split(":", 1)
            name = escape(f"{s['id']} {s['src']}")
            if kind == "plate":
                pp = os.path.join(D, "plates", f"plate_{ref}_solid.png")   # an all-digit name is read by Resolve as an image sequence and goes missing
                if not os.path.exists(pp):
                    im = np.empty((H, W, 3), np.uint8); im[:] = [int(ref[4:6], 16), int(ref[2:4], 16), int(ref[0:2], 16)]
                    cv2.imencode(".png", im)[1].tofile(pp)
                clips.append(f'   <asset-clip ref="{asset(pp, still=True)}" lane="1" offset="{rt(a, FPS)}" start="0s" duration="{rt(n, FPS)}" '
                             f'name="{escape(s["id"])} plate">{marker(s, "0s")}\n   </asset-clip>')
                continue
            if kind == "photo":
                path = P.p("03_Images", "commons", R.MAN[R.IDX[ref]]["file"])
            elif kind == "nasa":
                path = P.p("03_Images", "nasa", ref)
            elif kind == "file":
                path = P.p(ref)
            elif kind == "lk":
                path = P.local(ref)
            else:
                path = glob.glob(P.p("02_B-Roll", {"px": "pexels", "pb": "pixabay"}[kind], f"{ref}_*.mp4"))[0]
            if path.lower().endswith((".mp4", ".mov", ".webm", ".mkv")):
                t0, speed, cdur = clip_timing(path, n, FPS, uses)
                si = src_info(path)
                vw, vh = si["w"], si["h"]
                f_cov = max(W / vw, H / vh) / min(W / vw, H / vh)
                sc = f'\n    <adjust-transform scale="{f_cov:.4f} {f_cov:.4f}"/>' if f_cov > 1.001 else ""
                sf = lambda t: si["tc"] + min(round(t * si["num"] / si["den"]), si["frames"] - 1)   # seconds -> source frame
                st = f"{sf(t0) * si['den']}/{si['num']}s"
                tm = ""
                if speed < 0.999:
                    slowed += 1
                    tm = (f'\n    <timeMap><timept time="0s" value="{st}" interp="linear"/>'
                          f'<timept time="{rt(n, FPS)}" value="{sf(t0 + n / FPS * speed) * si["den"]}/{si["num"]}s" interp="linear"/></timeMap>')
                clips.append(f'   <asset-clip ref="{asset(path, src=si)}" lane="1" offset="{rt(a, FPS)}" start="{st}" duration="{rt(n, FPS)}" name="{name}">'
                             f'{tm}{sc}{marker(s, st)}\n   </asset-clip>')
                continue
            im = cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_REDUCED_GRAYSCALE_2)
            ih, iw = im.shape[0] * 2, im.shape[1] * 2
            move = s["treatment"] if kind == "photo" else (s["treatment"] or "in")
            va, vb, cw0, ch0 = photo_views(iw, ih, W, H, move, s.get("focus"), R.SHOTS.index(s))
            cover = max(W / iw, H / ih) / min(W / iw, H / ih)       # Resolve shows a still fitted inside the frame
            kp, ks = [], []
            for j in range(5):                                      # the renderer's smoothstep ease, sampled
                u = j / 4; e = u * u * (3 - 2 * u)
                cx, cy, z = (va[q] + (vb[q] - va[q]) * e for q in range(3))
                t = rt(min(round(n * u), n - 1), FPS)
                dx, dy = (0.5 - cx) * cw0 * z, (cy - 0.5) * ch0 * z  # frame pixels; FCPXML y points up
                kp.append(f'<keyframe time="{t}" value="{dx / H * 100:.3f} {dy / H * 100:.3f}"/>')
                ks.append(f'<keyframe time="{t}" value="{z * cover:.4f} {z * cover:.4f}"/>')
            clips.append(f'   <asset-clip ref="{asset(path, still=True)}" lane="1" offset="{rt(a, FPS)}" start="0s" duration="{rt(n, FPS)}" name="{name}">'
                         f'\n    <adjust-transform><param name="position"><keyframeAnimation>{"".join(kp)}</keyframeAnimation></param>'
                         f'<param name="scale"><keyframeAnimation>{"".join(ks)}</keyframeAnimation></param></adjust-transform>{marker(s, "0s")}\n   </asset-clip>')
    # ---------------------------------------------------------------- V2 vignette, V3 graphics, V4 HUD
    if not rendered:                                                 # (the rendered picture already carries the grade and vignette)
        clips.append(f'   <asset-clip ref="{asset(vig, still=True)}" lane="2" offset="0s" start="0s" duration="{rt(end, FPS)}" name="vignette"/>')

    for o in R.OVS:
        f = os.path.join(R.OVD, f"{o['id']}_{o['kind']}.mov")
        if not os.path.exists(f):
            print("  ! missing graphic", f); continue
        a, n = fr(o["start"], FPS), fr(o["p"]["dur"], FPS)
        label = o["p"].get("text") or o["p"].get("title") or o["p"].get("big") or o["p"].get("head") or ""
        clips.append(f'   <asset-clip ref="{asset(f, seconds=n / FPS)}" lane="3" offset="{rt(a, FPS)}" start="0s" duration="{rt(n, FPS)}" '
                     f'name="{escape(o["id"] + " " + o["kind"] + (" · " + str(label) if label else ""))}"/>')
    if os.path.exists(hudp) and P.cfg.get("hud") and not no_hud:
        hp = json.load(open(hudp + ".json")) if os.path.exists(hudp + ".json") else dict(k=1, cx=W / 2, cy=H / 2)
        tf = (f'<adjust-transform position="{(hp["cx"] - W / 2) / H * 100:.3f} {(H / 2 - hp["cy"]) / H * 100:.3f}" '
              f'scale="{1 / hp["k"]:.5f} {1 / hp["k"]:.5f}"/>')                # Resolve fits the small clip to the frame: undo, then place
        clips.append(f'   <asset-clip ref="{asset(hudp, seconds=end / FPS)}" lane="4" offset="0s" start="0s" duration="{rt(end, FPS)}" name="HUD">{tf}</asset-clip>')
    # ---------------------------------------------------------------- audio
    nl = nmus = nsfx = 0
    if rendered:
        st_dir = os.path.join(D, "stems")
        if force or not os.path.exists(os.path.join(st_dir, "voice.wav")) or os.path.getmtime(os.path.join(st_dir, "voice.wav")) < os.path.getmtime(P.p("07_Audio", "audio_plan.json")):
            cues.bind(P)
            audio.mix(P, json.load(open(P.p("07_Audio", "audio_plan.json"), encoding="utf-8")), stems=st_dir)
        for lane, nm, role in ((-1, "voice", "dialogue"), (-2, "music", "music"), (-3, "sfx", "effects")):
            p = os.path.join(st_dir, f"{nm}.wav")
            clips.append(f'   <asset-clip ref="{asset(p, video=False, audio_=True)}" lane="{lane}" offset="0s" start="0s" duration="{rt(end, FPS)}" name="{nm}" audioRole="{role}"/>')
    else:
        aud = bake_audio(P, R, D, A)
        for x in aud:
            clips.append(f'   <asset-clip ref="{asset(x["path"], video=False, audio_=True, seconds=x["frames"] / FPS)}" lane="{x["lane"]}" '
                         f'offset="{rt(x["frame"], FPS)}" start="0s" duration="{rt(x["frames"], FPS)}" name="{escape(x["name"])}" audioRole="{x["role"]}"/>')
        nl = sum(x["role"] == "dialogue" for x in aud)
        nmus = sum(x["role"] == "music" for x in aud)
        nsfx = sum(x["role"] == "effects" for x in aud)
        json.dump(aud, open(os.path.join(D, "audio.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    gap_markers = []
    for bl in R.TL["blocks"]:
        text = " ".join(f"[{l['id']}] {l['text']}" for l in R.TL["lines"] if l["block"] == bl["id"])
        gap_markers.append(f'       <marker start="{rt(fr(bl["start"], FPS), FPS)}" duration="{rt(1, FPS)}" '
                           f'value="{escape(bl["id"] + " · " + ", ".join(bl["lines"]))}" note="{escape(text[:900])}"/>')
    # the grade LUT where Resolve looks for LUTs (Color page > right-click a clip > LUTs > docpipe)
    lname = re.sub(r"[^A-Za-z0-9_]+", "_", P.cfg["title"]) + "_grade.cube"
    try:
        os.makedirs(LUT_DIR, exist_ok=True)
        import shutil
        shutil.copy2(lut, os.path.join(LUT_DIR, lname))
    except OSError as e:
        print(f"   ! could not copy the LUT into Resolve's LUT folder ({e}); use 05_Renders/review/grade.cube")
    title = escape(P.cfg["title"])
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.10">
 <resources>
  <format id="r1" name="FFVideoFormat1080p30" frameDuration="{rt(1, FPS)}" width="{W}" height="{H}"/>
{"".join(f'  <format id="{fid}" frameDuration="{d}/{nm}s" width="{w}" height="{h}"/>' + chr(10) for (nm, d, w, h), fid in formats.items())}{chr(10).join(res)}
 </resources>
 <library>
  <event name="{title} review">
   <project name="{title} review">
    <sequence format="r1" duration="{rt(end, FPS)}" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">
     <spine>
      <gap name="film" offset="0s" start="0s" duration="{rt(end, FPS)}">
{chr(10).join(gap_markers)}
{chr(10).join(clips)}
      </gap>
     </spine>
    </sequence>
   </project>
  </event>
 </library>
</fcpxml>
"""
    open(os.path.join(D, "timeline.fcpxml"), "w", encoding="utf-8").write(xml)
    open(os.path.join(D, "timeline_video.fcpxml"), "w", encoding="utf-8").write("\n".join(l for l in xml.split("\n") if 'audioRole="' not in l))
    json.dump([dict(id=x["id"], src=x["src"], frame=fr(x["start"], FPS)) for x in R.SHOTS if fr(x["end"], FPS) > fr(x["start"], FPS)],
              open(os.path.join(D, "shots.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"made": os.path.getmtime(P.out("edit.json")), "frames": end, "mode": "rendered" if rendered else "components"},
              open(os.path.join(D, "review.json"), "w"))
    if rendered:
        print(f"-> {os.path.join(D, 'timeline.fcpxml')}: rendered picture, {len(R.OVS)} graphics, 3 stems, {len(blocks)} block markers")
    else:
        print(f"-> {os.path.join(D, 'timeline.fcpxml')}: {len(R.SHOTS)} shots from their sources ({slowed} slowed clips), {len(R.OVS)} graphics, "
              f"{nl} voice lines, {nmus} music cues, {nsfx} sound effects, {len(blocks)} block markers")
        print("   grade: grade.cube on every shot (push applies it), vignette.png above the shots; audio carries the mix's levels and ducking")
        print("   next: doc.py <prj> push   (or File > Import > Timeline... > timeline.fcpxml by hand)")


TC = re.compile(r"(\d\d):(\d\d):(\d\d)[:;](\d\d)")


def notes(P, args):
    """Resolve marker EDL -> REVIEW_NOTES.md: each note with its time, the shot under it, the graphic on screen and the line being said."""
    sys.stdout.reconfigure(encoding="utf-8")
    if not args:
        sys.exit("notes needs the marker EDL exported from Resolve (File > Export > Timeline Markers to EDL)")
    FPS = P.cfg["render"]["fps"]
    TL, S, O = P.timeline(), P.load_out("edit.json"), P.load_out("overlays.json")
    src = open(args[0], encoding="utf-8-sig", errors="replace").read().splitlines()
    marks, cur = [], None
    for line in src:
        m = re.match(r"\s*\d{3,}\s", line)
        if m:
            tcs = TC.findall(line)
            if tcs:
                h, mi, s_, f = map(int, tcs[2] if len(tcs) > 2 else tcs[0])
                cur = dict(t=h * 3600 + mi * 60 + s_ + f / FPS, note="", color="")
                marks.append(cur)
        elif cur is not None and "|M:" in line:
            cur["note"] = line.split("|M:", 1)[1].split(" |D:")[0].strip()
            c = re.search(r"\|C:(\w+)", line)
            cur["color"] = c.group(1).replace("ResolveColor", "") if c else ""
    if marks and all(m["t"] >= 3600 for m in marks) and TL["end"] < 3600:
        for m in marks:
            m["t"] -= 3600                                 # timeline started at 01:00:00:00
    marks = [m for m in marks if not re.match(r"K\d\d ·", m["note"])]   # our own block markers
    tc = lambda t: "%d:%04.1f" % (t // 60, t % 60)
    L = [f"# Review notes — {P.cfg['title']}", "", f"{len(marks)} notes from {os.path.basename(args[0])}.", "",
         "| # | Time | Note | Shot under it | Graphic on screen | Line being said |", "|---|---|---|---|---|---|"]
    for k, m in enumerate(sorted(marks, key=lambda m: m["t"]), 1):
        t = m["t"]
        shot = next((s for s in S if s["start"] <= t < s["end"]), None)
        gfx = [o for o in O if o["start"] <= t < o["end"]]
        line = min(TL["lines"], key=lambda l: 0 if l["start"] <= t <= l["end"] else min(abs(t - l["start"]), abs(t - l["end"])))
        L.append(f"| {k} | {tc(t)} | {m['note'] or '(no text)'} | {shot['id'] + ' ' + shot['src'] if shot else ''} (block {shot['block'] if shot else ''}) | "
                 f"{', '.join(o['id'] + ' ' + o['kind'] for o in gfx)} | [{line['id']}] {line['text'][:90]} |")
    out = P.out(os.path.join("review", "REVIEW_NOTES.md"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L[4:]))
    print("->", out)


# ---------------------------------------------------------------- live Resolve, through davinci-resolve-mcp's bridge
from .ctx import setting as _setting  # noqa: E402
MCP_DIR = _setting("RESOLVE_MCP_DIR", os.path.join(os.path.expanduser("~"), "davinci-resolve-mcp"))


def resolve_app():
    """the running Resolve, through the in-app bridge (Free: Workspace > Scripts > resolve_bridge must be running)."""
    if MCP_DIR not in sys.path:
        sys.path.insert(0, MCP_DIR)
    os.environ.setdefault("DAVINCI_RESOLVE_BRIDGE", "1")
    try:
        from src.utils.resolve_bridge_client import connect
        return connect()
    except Exception as e:
        sys.exit(f"no connection to Resolve ({type(e).__name__}: {e}).\n"
                 "Open Resolve, open any project, run Workspace > Scripts > resolve_bridge, then try again. "
                 "Without the bridge: File > Import > Timeline… > 05_Renders/review/timeline.fcpxml by hand.")


def push(P, args):
    """put the review timeline into the running Resolve: project "<title> review", a new timeline named with the date and time.
    Picture (shots with their camera moves, graphics, HUD) from timeline_video.fcpxml; then through the API: audio clip by clip
    on named tracks (voice, music, sfx), each shot named by its id, one blue marker per V.O. block with its narration."""
    sys.stdout.reconfigure(encoding="utf-8")
    import time
    D = P.out("review")
    fx = os.path.join(D, "timeline_video.fcpxml")
    if not os.path.exists(fx):
        sys.exit("no review timeline yet: run  doc.py <prj> review  first")
    FPS = P.cfg["render"]["fps"]
    r = resolve_app()
    pm = r.GetProjectManager()
    name = f"{P.cfg['title']} review"
    cur = pm.GetCurrentProject()
    proj = cur if cur and cur.GetName() == name else (pm.LoadProject(name) or pm.CreateProject(name))
    if not proj:
        sys.exit(f"could not open or create the Resolve project {name!r}")
    for k, v in (("timelineFrameRate", str(FPS)), ("timelineResolutionWidth", str(P.cfg["render"]["width"])),
                 ("timelineResolutionHeight", str(P.cfg["render"]["height"]))):
        proj.SetSetting(k, v)
    mp = proj.GetMediaPool()
    tname = f"{P.cfg['title']} {time.strftime('%m-%d %H.%M.%S')}"
    tl = None
    if "--current" in args:                                          # the user imported timeline_video.fcpxml by hand:
        tl = proj.GetCurrentTimeline()                               # finish that one (names, grade, vignette, audio, markers)
        if not tl or any(tl.GetTrackName("audio", t) == "voice" for t in range(1, tl.GetTrackCount("audio") + 1)):
            sys.exit("open the timeline imported from timeline_video.fcpxml (one that has no audio laid yet), then run push --current")
    if not tl:
        # Resolve cancels a scripted FCPXML import that has to bring in a lot of media itself (its import dialog can't be answered
        # from a script), so the media goes into the pool first, in batches, and the timeline then links to it
        from urllib.parse import unquote
        src = open(fx, encoding="utf-8").read()
        media = sorted({unquote(m)[len("file:///"):].replace("/", "\\") for m in re.findall(r'src="(file:///[^"]+)"', src)})
        pre = mp.AddSubFolder(mp.GetRootFolder(), f"media {time.strftime('%m-%d %H.%M.%S')}")
        if pre:
            mp.SetCurrentFolder(pre)
        got = 0
        for k in range(0, len(media), 40):
            got += len(mp.ImportMedia(media[k:k + 40]) or [])
        print(f"   {got}/{len(media)} media files in the pool", flush=True)
    for attempt in range(0 if tl else 4):
        tl = mp.ImportTimelineFromFile(fx, {"timelineName": f"{tname}" + (f" ({attempt + 1})" if attempt else ""),
                                            "importSourceClips": attempt % 2 == 1})
        if tl:
            break
        print(f"   import cancelled by Resolve, retrying ({attempt + 1}/4)…", flush=True)
        time.sleep(5)
    if not tl:
        sys.exit("Resolve cancelled the FCPXML import. In Resolve: File > Import > Timeline... > 05_Renders/review/timeline_video.fcpxml, "
                 "open that timeline, then run  doc.py <prj> push --current")
    proj.SetCurrentTimeline(tl)
    if not (tl.GetItemListInTrack("video", 1) or []) and tl.GetTrackCount("video") > 1:
        tl.DeleteTrack("video", 1)                                   # the import leaves V1 empty (the gap the clips hang on)
    end = int(json.load(open(os.path.join(D, "review.json")))["frames"])
    folder = mp.AddSubFolder(mp.GetRootFolder(), f"push {time.strftime('%m-%d %H.%M.%S')}")   # this push's media (a path already
    if folder:                                                       # in the folder it is imported to comes back empty)
        mp.SetCurrentFolder(folder)
    vig_p = os.path.join(D, "vignette.png")
    vig_ok = False
    if tl.GetItemListInTrack("video", 2) and any("vignette" in (it.GetName() or "") for it in tl.GetItemListInTrack("video", 2)[:1]):
        vig_ok = True                                                # it came with the timeline file
    elif os.path.exists(vig_p) and json.load(open(os.path.join(D, "review.json"))).get("mode") == "components":
        tl.AddTrack("video", {"index": 2})                          # vignette between the shots and the graphics
        v = mp.ImportMedia([vig_p])
        if v:                                                        # a still placed by the API lasts Resolve's still duration
            first = mp.AppendToTimeline([{"mediaPoolItem": v[0], "startFrame": 0, "endFrame": end - 1, "mediaType": 1, "trackIndex": 2,
                                          "recordFrame": tl.GetStartFrame()}]) or []   # (often 150 frames), whatever endFrame says:
            seg = first[0].GetDuration() if first else 0                # measure it, then tile the rest end to end
            if seg:
                infos = [{"mediaPoolItem": v[0], "startFrame": 0, "endFrame": min(seg, end - f0) - 1, "mediaType": 1, "trackIndex": 2,
                          "recordFrame": tl.GetStartFrame() + f0} for f0 in range(seg, end, seg)]
                got = 0
                for k in range(0, len(infos), 60):
                    got += len(mp.AppendToTimeline(infos[k:k + 60]) or [])
                vig_ok = got == len(infos)
    names = ("shots", "vignette", "graphics", "HUD") if vig_ok else ("shots", "graphics", "HUD")
    for i, nm in enumerate(names, 1):
        if i <= tl.GetTrackCount("video"):
            tl.SetTrackName("video", i, nm)
    shots = json.load(open(os.path.join(D, "shots.json"), encoding="utf-8"))
    items = sorted(tl.GetItemListInTrack("video", 1) or [], key=lambda it: it.GetStart())
    named = 0
    if len(items) == len(shots):
        for it, s_ in zip(items, shots):
            named += bool(it.SetName(f"{s_['id']} {s_['src']}"))
    # the film's grade on every shot: the LUT goes into Resolve's LUT folder so Resolve can find it
    lut_src = os.path.join(D, "grade.cube")
    graded = 0
    if os.path.exists(lut_src):
        import shutil
        lname = re.sub(r"[^A-Za-z0-9_]+", "_", P.cfg["title"]) + "_grade.cube"
        try:
            os.makedirs(LUT_DIR, exist_ok=True)
            shutil.copy2(lut_src, os.path.join(LUT_DIR, lname))
            lut_path = os.path.join(LUT_DIR, lname)
        except OSError:
            lut_path = lut_src
        proj.RefreshLUTList()
        for it in items:
            g = it.GetNodeGraph()
            graded += bool(g and g.SetLUT(1, lut_path))
    # audio, clip by clip
    aud = json.load(open(os.path.join(D, "audio.json"), encoding="utf-8"))
    # stock clips that carry their own sound bring it along on the first audio tracks: keep it, muted, under our tracks
    base = 0
    for t in range(1, tl.GetTrackCount("audio") + 1):
        if tl.GetItemListInTrack("audio", t):
            base = t
    for t in range(1, base + 1):
        tl.SetTrackName("audio", t, "clip sound (off)")
        tl.SetTrackEnable("audio", t, False)
    need = base + max(x["track"] for x in aud)
    while tl.GetTrackCount("audio") < need:
        tl.AddTrack("audio", "stereo")
    for x in aud:
        x["track"] += base
        tl.SetTrackName("audio", x["track"], "music" if x["role"] == "music" else ("sfx" if x["role"] == "effects" else "voice"))
    paths = sorted({x["path"] for x in aud})
    pool = {}
    for k in range(0, len(paths), 50):
        for it in mp.ImportMedia(paths[k:k + 50]) or []:
            pool[os.path.normcase(os.path.abspath(it.GetClipProperty("File Path")))] = it
    infos = []
    for x in aud:
        it = pool.get(os.path.normcase(os.path.abspath(x["path"])))
        if it:
            infos.append({"mediaPoolItem": it, "startFrame": 0, "endFrame": x["frames"] - 1, "mediaType": 2, "trackIndex": x["track"],
                          "recordFrame": tl.GetStartFrame() + x["frame"]})
    placed = 0
    for k in range(0, len(infos), 40):
        placed += len(mp.AppendToTimeline(infos[k:k + 40]) or [])
    # one blue marker per V.O. block, with its narration
    TL = P.timeline()
    marks = len(tl.GetMarkers() or {})
    for bl in ([] if marks else TL["blocks"]):
        text = " ".join(f"[{l['id']}] {l['text']}" for l in TL["lines"] if l["block"] == bl["id"])
        marks += bool(tl.AddMarker(fr(bl["start"], FPS), "Blue", f"{bl['id']} · {', '.join(bl['lines'])}", text[:1500], 1))
    srt_p = os.path.join(D, "narration.srt")
    if os.path.exists(srt_p):
        mp.ImportMedia([srt_p])                                      # in the Media Pool: drag it onto the timeline to read the lines
    pm.SaveProject()
    print(f"Resolve: project {name!r}, timeline {tl.GetName()!r}: {len(items)} shots ({named} named, {graded} graded), "
          f"vignette {'on' if vig_ok else 'MISSING'}, {len(tl.GetItemListInTrack('video', 3 if vig_ok else 2) or [])} graphics, {placed}/{len(aud)} audio clips on {tl.GetTrackCount('audio')} tracks, {marks} block markers")


def pull(P, args):
    """the markers on the current Resolve timeline -> REVIEW_NOTES.md (as `notes`, without exporting an EDL)."""
    sys.stdout.reconfigure(encoding="utf-8")
    r = resolve_app()
    proj = r.GetProjectManager().GetCurrentProject()
    tl = proj.GetCurrentTimeline() if proj else None
    if not tl:
        sys.exit("no timeline open in Resolve")
    FPS = P.cfg["render"]["fps"]
    start = tl.GetStartFrame()
    tmp = P.out(os.path.join("review", "_markers.edl"))
    lines = ["TITLE: markers", "FCM: NON-DROP FRAME", ""]
    tcf = lambda f: "%02d:%02d:%02d:%02d" % (f // (3600 * FPS), f // (60 * FPS) % 60, f // FPS % 60, f % FPS)
    k = 0
    for f, m in sorted((tl.GetMarkers() or {}).items()):
        k += 1
        f = int(f)
        if re.match(r"K\d\d ·", m.get("name", "")):
            continue                                                   # our own block markers
        note = " ".join(x for x in (m.get("name", ""), m.get("note", "")) if x).replace("|", "/")
        lines += [f"{k:03d}  001      V     C        {tcf(f)} {tcf(f + 1)} {tcf(f)} {tcf(f + 1)}", f" |C:ResolveColor{m.get('color', '')} |M:{note} |D:1", ""]
    # markers placed on clips (not on the timeline ruler) count too
    for kind in ("video", "audio"):
        for ti in range(1, (tl.GetTrackCount(kind) or 0) + 1):
            for it in tl.GetItemListInTrack(kind, ti) or []:
                for f, m in sorted((it.GetMarkers() or {}).items()):
                    if re.match(r"K\d\d ·", m.get("name", "")):
                        continue
                    k += 1
                    g = int(it.GetStart()) - start + int(f) - int(it.GetLeftOffset() or 0)
                    note = " ".join(x for x in (m.get("name", ""), m.get("note", "")) if x).replace("|", "/")
                    lines += [f"{k:03d}  001      V     C        {tcf(g)} {tcf(g + 1)} {tcf(g)} {tcf(g + 1)}", f" |C:ResolveColor{m.get('color', '')} |M:{note} |D:1", ""]
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    open(tmp, "w", encoding="utf-8").write("\n".join(lines))
    notes(P, [tmp])
