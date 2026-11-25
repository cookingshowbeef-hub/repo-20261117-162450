"""Render the film from 05_Renders/edit.json in one pass (1080p30 by default; film.json render.*).

Picture: each shot built frame by frame (photos: slow camera moves and detail moves; clips: fitted, slowed if short), lightly graded.
On the same frame: the Remotion graphics active at that moment (06_Graphics/render/ov/<id>_<kind>.mov, ProRes 4444 with alpha), then
the project's HUD on top (film.json "hud": "module:Class" in 04_Scripts_Code with .draw(frame_bgr, t), e.g. a running counter).
Audio: 07_Audio/final_mix.wav if it exists, else voice_only.wav (rough cut).
  doc.py <prj> render              full film -> 05_Renders/<output>
  doc.py <prj> render 60 120       a section (film seconds) -> 05_Renders/tests/section_60_120.mp4
  doc.py <prj> patch 60 120 [a b]  re-render those sections and lay them into the existing full film (about 10 min, not 30)
"""
import glob, importlib, json, os, shutil, subprocess, sys
import cv2, numpy as np


class Renderer:
    def __init__(self, P):
        self.P = P
        R = P.cfg["render"]
        self.W, self.H, self.FPS, self.FADE = R["width"], R["height"], R["fps"], R["fade_frames"]
        self.SHOTS = P.load_out("edit.json")
        self.TL = P.timeline()
        self.OVS = P.load_out("overlays.json")
        self.IDX = P.load("03_Images", "commons", "sheets", "index.json", default={})
        self.MAN = P.load("03_Images", "commons", "manifest.json", default={})
        self.OVD = P.p("06_Graphics", "render", "ov")
        g = R["grade"]
        from .style import curve, vignette                                            # the style's grade (S-curve, lift, tint) and vignette/letterbox
        self.LUT3 = np.dstack(curve(g)).astype(np.uint8)
        self.VIG3 = np.repeat(vignette(g, self.W, self.H)[..., None], 3, axis=2)
        self.sat = g["saturation"]
        self.USES = {}

    def grade(self, f):
        f = cv2.LUT(f, self.LUT3)
        g = cv2.cvtColor(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
        f = cv2.addWeighted(f, self.sat, g, 1 - self.sat, 0)
        return cv2.multiply(f, self.VIG3, dtype=cv2.CV_8U)

    def cover(self, img, extra=1.0):
        W, H = self.W, self.H
        s = max(W / img.shape[1], H / img.shape[0]) * extra
        return cv2.resize(img, (max(W, round(img.shape[1] * s)), max(H, round(img.shape[0] * s))), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)

    def center_crop(self, img):
        y, x = (img.shape[0] - self.H) // 2, (img.shape[1] - self.W) // 2
        return img[y:y + self.H, x:x + self.W]

    # ------------------------------------------------------------ shot builders: each yields n BGR frames
    def photo(self, img, n, k, move="", focus=None):
        W, H = self.W, self.H
        ease = lambda u: u * u * (3 - 2 * u)
        E = 1.75 if move == "detail" else 1.14
        big = self.cover(img, extra=E)
        bh, bw = big.shape[:2]
        cw0, ch0 = bw / E, bh / E
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
        for i in range(n):
            u = ease(i / max(1, n - 1))
            cx, cy, z = (a[j] + (b[j] - a[j]) * u for j in range(3))
            ww, wh = W / z * E, H / z * E
            px, py = np.clip(cx * bw, ww / 2, bw - ww / 2), np.clip(cy * bh, wh / 2, bh - wh / 2)
            M = np.float32([[W / ww, 0, W / 2 - px * W / ww], [0, H / wh, H / 2 - py * H / wh]])
            yield cv2.warpAffine(big, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

    def video(self, path, n):
        cap = cv2.VideoCapture(path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        nf = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cdur, dur = nf / fps, n / self.FPS
        k = self.USES.get(path, 0); self.USES[path] = k + 1          # a re-used clip starts further in
        room = max(0.0, cdur - 0.3 - dur)
        a = min(0.4, room) + room * [0.0, 0.5, 0.85][k % 3] * (0.9 if room > 0.4 else 0)
        span = min(dur, cdur - a - 0.05)
        speed = max(min(1.0, span / dur) if dur > 0 else 1.0, 0.5)   # short clip: slow it down to fit
        idx, frame = -1, None
        for i in range(n):
            want = min(int(min(a + i / self.FPS * speed, cdur - 0.05) * fps), nf - 1)
            if frame is None or want - idx > 90:
                cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, want)); idx = want - 1
            while idx < want:
                ok, f = cap.read()
                if not ok:
                    break
                frame, idx = f, idx + 1
            f = frame
            if f.shape[1] != self.W or f.shape[0] != self.H:
                f = self.center_crop(self.cover(f))
            yield f

    def source(self, s, n, k):
        kind, ref = s["src"].split(":", 1)
        imread = lambda p: cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
        if kind == "plate":
            f = np.empty((self.H, self.W, 3), np.uint8); f[:] = [int(ref[4:6], 16), int(ref[2:4], 16), int(ref[0:2], 16)]
            return (f for _ in range(n))
        if kind == "photo":
            return self.photo(imread(self.P.p("03_Images", "commons", self.MAN[self.IDX[ref]]["file"])), n, k, s["treatment"], s.get("focus"))
        if kind == "nasa":
            return self.photo(imread(self.P.p("03_Images", "nasa", ref)), n, k, "in")
        if kind in ("file", "lk"):
            path = self.P.p(ref) if kind == "file" else self.P.local(ref)
            if path.lower().endswith((".mp4", ".mov", ".webm", ".mkv")):
                return self.video(path, n)
            return self.photo(imread(path), n, k, s["treatment"] or "in")
        folder = {"px": "pexels", "pb": "pixabay"}[kind]
        return self.video(glob.glob(self.P.p("02_B-Roll", folder, f"{ref}_*.mp4"))[0], n)

    def hud(self):
        spec = self.P.cfg.get("hud")
        if not spec:
            return None
        mod, cls = spec.split(":")
        return getattr(importlib.import_module(mod), cls)()

    # ------------------------------------------------------------ one pass
    def render(self, a, b, out, picture_only=False):
        """picture_only: the graded shots alone (no graphics, no HUD, no sound), for the Resolve review timeline."""
        W, H, FPS = self.W, self.H, self.FPS
        os.makedirs(os.path.dirname(out), exist_ok=True)
        F0, F1 = round(a * FPS), round(b * FPS)
        mix = self.P.p("07_Audio", "final_mix.wav")
        mix = mix if os.path.exists(mix) else self.P.p("07_Audio", "voice_only.wav")
        vin = ["-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
        venc = ["-c:v", "libx264", "-preset", "medium", "-crf", str(self.P.cfg["render"]["crf"]), "-pix_fmt", "yuv420p", "-profile:v", "high"]
        if picture_only:
            cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y", *vin, *venc, "-g", "15", "-movflags", "+faststart", out]   # short GOP: scrubs well in Resolve
        else:
            cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y", *vin, "-ss", f"{F0 / FPS:.3f}", "-t", f"{(F1 - F0) / FPS:.3f}", "-i", mix,
                   "-map", "0:v", "-map", "1:a", *venc, "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", "-shortest", out]
        enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        hud = None if picture_only else self.hud()
        pending = [] if picture_only else sorted((o for o in self.OVS if round(o["end"] * FPS) > F0 and round(o["start"] * FPS) < F1), key=lambda o: o["start"])
        live, written = [], F0

        def overlays(g, fi):
            while pending and round(pending[0]["start"] * FPS) <= fi:
                live.append(Overlay(self, pending.pop(0), fi))
            for ov in live:
                g = ov.blend(g)
            for ov in [x for x in live if x.a + x.n <= fi + 1]:
                ov.close(); live.remove(ov)
            return g
        for s in [s for s in self.SHOTS if round(s["end"] * FPS) > F0 and round(s["start"] * FPS) < F1]:
            s0, s1 = round(s["start"] * FPS), round(s["end"] * FPS)
            f0, f1 = max(s0, F0), min(s1, F1)
            for i, fr in enumerate(self.source(s, s1 - s0, self.SHOTS.index(s))):
                fi = s0 + i
                if fi < f0:
                    continue
                if fi >= f1:
                    break
                g = np.ascontiguousarray(self.grade(fr))
                if fi - s0 < self.FADE and s.get("fade_in"):
                    g = (g * ((fi - s0 + 1) / (self.FADE + 1))).astype(np.uint8)
                g = overlays(g, fi)
                if hud:
                    g = hud.draw(g, fi / FPS)
                enc.stdin.write(g.tobytes()); written += 1
            print(f"{s['id']} {s['src'][:40]:40s} {f1 - f0:4d}f  ({written - F0}/{F1 - F0})", flush=True)
        while written < F1:                                          # end-text tail on black
            enc.stdin.write(overlays(np.zeros((H, W, 3), np.uint8), written).tobytes()); written += 1
        for ov in live:
            ov.close()
        enc.stdin.close(); enc.wait()
        print("->", out)


class Overlay:
    """one graphic, decoded frame by frame (BGRA) while it is on screen."""
    def __init__(self, R, o, f0):
        self.W, self.H = R.W, R.H
        self.a, self.n = round(o["start"] * R.FPS), round(o["p"]["dur"] * R.FPS)
        skip = max(0, f0 - self.a)
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{skip / R.FPS:.4f}", "-i", os.path.join(R.OVD, f"{o['id']}_{o['kind']}.mov"),
                                   "-f", "rawvideo", "-pix_fmt", "bgra", "-"], stdout=subprocess.PIPE)

    def blend(self, frame):
        W, H = self.W, self.H
        buf = self.p.stdout.read(W * H * 4)
        if len(buf) < W * H * 4:
            return frame
        o = np.frombuffer(buf, np.uint8).reshape(H, W, 4)
        a = o[:, :, 3]
        ys = np.flatnonzero(a.max(1))
        if not len(ys):
            return frame
        y0, y1 = ys[0], ys[-1] + 1
        a3 = cv2.cvtColor(a[y0:y1], cv2.COLOR_GRAY2BGR)
        frame[y0:y1] = cv2.add(cv2.multiply(o[y0:y1, :, :3], a3, scale=1 / 255), cv2.multiply(frame[y0:y1], 255 - a3, scale=1 / 255))
        return frame

    def close(self):
        self.p.stdout.close(); self.p.kill()


def run(P, args):
    sys.stdout.reconfigure(encoding="utf-8")
    R = Renderer(P)
    if len(args) >= 2:
        a, b = float(args[0]), float(args[1])
        R.render(a, b, P.out(os.path.join("tests", f"section_{int(a)}_{int(b)}.mp4")))
    else:
        R.render(0.0, R.TL["end"], P.out(P.cfg["output"]))


def patch(P, args):
    """re-render the sections a b [a b ...] and lay them over the existing full film (video re-encoded once, audio copied).
    The old film is kept as <output>_prepatch.mp4 until you delete it."""
    sys.stdout.reconfigure(encoding="utf-8")
    if len(args) < 2 or len(args) % 2:
        sys.exit("patch needs pairs of film seconds: a b [a b ...]")
    R = Renderer(P)
    film = P.out(P.cfg["output"])
    if not os.path.exists(film):
        sys.exit(f"no full render to patch: {film}")
    secs = [(float(args[i]), float(args[i + 1])) for i in range(0, len(args), 2)]
    parts = []
    for a, b in secs:
        p = P.out(os.path.join("tests", f"section_{int(a)}_{int(b)}.mp4"))
        R.render(a, b, p)
        parts.append((p, round(a * R.FPS) / R.FPS, round(b * R.FPS) / R.FPS))
    old = film[:-4] + "_prepatch.mp4"
    shutil.move(film, old)
    inputs, chain, last = ["-i", old], [], "[0:v]"
    for k, (p, t0, t1) in enumerate(parts, 1):
        inputs += ["-i", p]
        chain.append(f"[{k}:v]setpts=PTS-STARTPTS+{t0:.4f}/TB[s{k}]")
        chain.append(f"{last}[s{k}]overlay=enable='between(t,{t0:.4f},{t1 - 0.0001:.4f})':eof_action=pass[v{k}]")
        last = f"[v{k}]"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(chain), "-map", last, "-map", "0:a",
                    "-c:v", "libx264", "-preset", "medium", "-crf", str(P.cfg["render"]["crf"]), "-pix_fmt", "yuv420p", "-profile:v", "high",
                    "-c:a", "copy", "-movflags", "+faststart", film], check=True)
    n = lambda f: subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries", "stream=nb_read_packets",
                                  "-of", "csv=p=0", f], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()
    print(f"patched {len(parts)} sections -> {film} ({n(film)} frames; before: {n(old)}). Old film kept at {old}")
