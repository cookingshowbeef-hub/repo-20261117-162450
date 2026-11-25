"""Music and sound from the project's audio_spec.py, mixed under the narration.

audio_spec.py (in 04_Scripts_Code) defines, with times from docpipe.cues (S_, E_, word, END):
  MUSIC = [(cue, file in the library's BGM folders, film in, film out, offset into track or None = end on the track's end, fade in, fade out, gain dB)]
  SFX   = [(file in SFX_Vault or "fs:<name>" from 07_Audio/freesound, film in, film out or None, offset, fade in, fade out, level dBFS RMS, note)]
  GFX_SFX (optional) = {graphic kind: style} with style one of STYLES below; COUNTER_SFX (optional) = {counter mode: (file, dt, level, note)}
  doc.py <prj> audio            copy the picks into 07_Audio, write 07_Audio/audio_plan.json
  doc.py <prj> audio preview    + voice/music/SFX mix -> 07_Audio/preview_mix.m4a
  doc.py <prj> audio final      -> 07_Audio/final_mix.wav at audio.lufs (two-pass loudnorm, linear)
Music ducks audio.duck_db under the voice (smoothed), so a cue at -9..-13 dB gain sits about 15 dB under the narration.
"""
import json, os, re, shutil, subprocess, sys
import numpy as np
from . import cues

WHOOSH = ["11_Whoosh_Whip_06.mp3", "10_Whoosh_Whip_05.mp3"]
CLICK = ["15_CameraFilm_Switch_02.mp3", "17_CameraFilm_Switch_05.mp3", "21_CameraFilm_Switch_09.mp3"]
RUMBLE, PAGE, TICK = "01_Impact_Low_End_Rumble_Loop_01.mp3", "20_OfficePaper_Book_Page_Turn_06.mp3", "17_ClockHeartbeat_Ticking_clock.mp3"
STYLES = ("card", "map", "whoosh", "whoosh_hit", "page", "tick", "clicks", "stamp", "none")


def gfx_sfx(P, kinds, counter_sfx):
    """accent sounds on the graphics' beats (from overlays.json) and on counter events (counter.json)."""
    out, n = [], 0

    def add(f, t, g, note, t_out=None, fi=0.0, fo=0.05, off=0):
        out.append((f, t, t_out, off, fi, fo, g, "graphic: " + note))
    for o in P.load_out("overlays.json"):
        k, at = o["kind"], [o["start"] + x for x in o["p"]["at"]]
        st = kinds.get(k, "none")
        if st == "card":
            add(WHOOSH[0], at[0] - 0.3, -33, k + " whoosh"); add(RUMBLE, at[0] + 0.15, -27, k + " low hit", fo=0.6)
        elif st == "map":
            n += 1; add(WHOOSH[n % 2], at[0] - 0.1, -35, "map whoosh")
            for t in at[1:]:
                n += 1; add(CLICK[n % 3], t, -37, "map beat click")
        elif st in ("whoosh", "whoosh_hit"):
            for t in at[:3]:
                n += 1; add(WHOOSH[n % 2], t - 0.12, -35, k + " whoosh")
            if st == "whoosh_hit":
                add(RUMBLE, at[0] + 0.05, -31, k + " low hit", fo=0.5)
        elif st == "page":
            add(PAGE, at[0] - 0.05, -32, k + " page")
        elif st == "tick":
            add(TICK, at[0], -36, k + " tick", t_out=at[0] + 1.6, fo=0.4)
        elif st == "clicks":
            last = -9
            for t in at:
                if t - last >= 0.15:
                    n += 1; add(CLICK[n % 3], t, -37, k + " click"); last = t
        elif st == "stamp":
            add(CLICK[0], at[0], -36, k + " stamp")
    if os.path.exists(P.out("counter.json")):
        for c in P.load_out("counter.json"):
            if c["mode"] in counter_sfx:
                f, dt, lvl, note = counter_sfx[c["mode"]]
                add(f, c["t"] + dt, lvl, note, fo=0.8 if f == RUMBLE else 0.05)
    return out


DEFAULT_GFX = {"chapter": "card", "title": "card", "map": "map", "stat": "whoosh_hit", "define": "page", "list": "clicks", "stamp": "stamp",
               "words": "whoosh", "timeline": "whoosh", "quote": "whoosh", "bars": "whoosh"}


def catalog(lib):
    paths = {}
    for root in ("BGM_NoCopyright", "SFX_Vault"):
        for d, _, fs in os.walk(os.path.join(lib, root)):
            for f in fs:
                paths.setdefault(f, os.path.join(d, f))
    return paths


def load(path, sr=48000):
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def place(bus, x, t_in, t_out, off, fi, fo, gain, sr=48000):
    a = int(off * sr)
    n = len(x) - a if t_out is None else int((t_out - t_in) * sr)
    seg = x[a:a + n].copy()
    n = len(seg)
    env = np.ones(n, np.float32)
    if fi > 0:
        k = min(n, int(fi * sr)); env[:k] = np.linspace(0, 1, k)
    if fo > 0:
        k = min(n, int(fo * sr)); env[n - k:] *= np.linspace(1, 0, k)
    s = int(t_in * sr)
    e = min(len(bus), s + n)
    if e > s:
        bus[s:e] += seg[:e - s] * env[:e - s, None] * 10 ** (gain / 20)


def run(P, args):
    sys.stdout.reconfigure(encoding="utf-8")
    cues.bind(P)
    spec = P.spec("audio_spec")
    A = P.cfg["audio"]
    OUT = P.p("07_Audio")
    sfx = list(spec.SFX) + gfx_sfx(P, getattr(spec, "GFX_SFX", DEFAULT_GFX), getattr(spec, "COUNTER_SFX", {}))
    lib = catalog(A["library"])
    os.makedirs(os.path.join(OUT, "music"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "sfx"), exist_ok=True)
    plan = {"music": [], "sfx": []}
    for cue, f, a, b, off, fi, fo, g in spec.MUSIC:
        dst = os.path.join(OUT, "music", f)
        if not os.path.exists(dst):
            shutil.copy2(lib[f], dst)
        plan["music"].append(dict(cue=cue, file=f"music/{f}", t_in=round(a, 2), t_out=round(b, 2), offset=off, fade_in=fi, fade_out=fo, gain_db=g))
    for f, a, b, off, fi, fo, g, note in sfx:
        if f.startswith("fs:"):
            rel = f"freesound/{f[3:]}.mp3"
        else:
            rel = f"sfx/{f}"
            if not os.path.exists(os.path.join(OUT, rel)):
                shutil.copy2(lib[f], os.path.join(OUT, rel))
        plan["sfx"].append(dict(file=rel, t_in=round(a, 2), t_out=None if b is None else round(b, 2), offset=off, fade_in=fi, fade_out=fo, level_db=g, note=note))
    json.dump(plan, open(os.path.join(OUT, "audio_plan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    cover = coverage(P, plan)
    want = P.cfg.get("rules", {}).get("music_coverage")
    print(f"{len(spec.MUSIC)} music cues, {len(sfx)} sound effects -> 07_Audio | music under {cover * 100:.0f}% of the narration"
          + (f" (style {P.cfg.get('style') or 'default'} wants >= {want * 100:.0f}%)" if want is not None else ""))
    if "preview" in args or "final" in args:
        mix(P, plan, final="final" in args)


def coverage(P, plan):
    """share of narration time with a music cue playing (the house style wants near-continuous score)."""
    TL, on = P.timeline(), 0.0
    for l in TL["lines"]:
        segs = sorted((max(l["start"], m["t_in"]), min(l["end"], m["t_out"])) for m in plan["music"])
        t = l["start"]
        for a, b in segs:
            if b > max(a, t):
                on += b - max(a, t); t = b
    return on / sum(l["end"] - l["start"] for l in TL["lines"])


def mix(P, plan, sr=48000, final=False, stems=None):
    """final: 07_Audio/final_mix.wav; stems=<folder>: voice / music / sfx as separate wavs (ducked as in the mix, at the
    gain that brings their sum to audio.lufs), for the Resolve review timeline."""
    A, OUT, TL = P.cfg["audio"], P.p("07_Audio"), P.timeline()
    n = int((TL["end"] + 2) * sr)
    voice, music, sfx = (np.zeros((n, 2), np.float32) for _ in range(3))
    for l in TL["lines"]:
        place(voice, load(P.p("01_Voice", "lines", f"{l['id']}.wav")), l["start"], None, 0, 0, 0.02, 0)
    for m in plan["music"]:
        x = load(os.path.join(OUT, m["file"]))
        off = m["offset"] if m["offset"] is not None else max(0, len(x) / sr - (m["t_out"] - m["t_in"]))
        place(music, x, m["t_in"], min(m["t_out"], m["t_in"] + len(x) / sr - off), off, m["fade_in"], m["fade_out"], m["gain_db"])
    for s in plan["sfx"]:
        x = load(os.path.join(OUT, s["file"]))
        loud = x[np.abs(x).max(1) > 10 ** (-50 / 20)]
        rms = 20 * np.log10(np.sqrt(np.mean(loud ** 2)) + 1e-9)
        if s["t_out"] is not None:
            need = int((s["t_out"] - s["t_in"] + s["offset"]) * sr) + 1
            if need > len(x):
                x = np.tile(x, (need // len(x) + 1, 1))
        place(sfx, x, s["t_in"], s["t_out"], s["offset"], s["fade_in"], s["fade_out"], s["level_db"] - rms)
    w = int(0.4 * sr)
    c = np.concatenate([[0], np.cumsum((np.abs(voice[:, 0]) > 0.01).astype(np.float64))])
    i = np.arange(len(voice))
    act = np.clip(((c[np.minimum(i + w // 2, len(voice))] - c[np.maximum(i - w // 2, 0)]) / w).astype(np.float32) * 3, 0, 1)
    music = music * (10 ** (-A["duck_db"] * act / 20))[:, None]
    sfx = sfx * (10 ** (-A["sfx_duck_db"] * act / 20))[:, None]
    k = 1 / (np.sqrt(np.mean(voice[np.abs(voice[:, 0]) > 0.01] ** 2)) / 10 ** (A["voice_rms"] / 20))
    out = (voice + music + sfx) * k
    tmp = os.path.join(OUT, "_preview.f32")
    out.astype(np.float32).tofile(tmp)
    src = ["ffmpeg", "-nostdin", "-hide_banner", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "2", "-i", tmp]
    I = A["lufs"]
    if stems:
        log = subprocess.run(src + ["-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
        g = 10 ** ((I - float(re.findall(r"I:\s+(-?[\d.]+) LUFS", log)[-1])) / 20)
        os.makedirs(stems, exist_ok=True)
        for name, bus in (("voice", voice), ("music", music), ("sfx", sfx)):
            bus = np.clip(bus * k * g, -0.98, 0.98).astype(np.float32)
            bus.tofile(tmp)
            subprocess.run(src + ["-c:a", "pcm_s24le", os.path.join(stems, f"{name}.wav")], check=True, capture_output=True)
        os.remove(tmp)
        print("-> stems", ", ".join(f"{n}.wav" for n in ("voice", "music", "sfx")), "in", stems)
        return
    log = subprocess.run(src + ["-af", f"alimiter=limit=0.7:attack=2:release=60:level=false,loudnorm=I={I}:TP=-1.5:LRA=20:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    m = json.loads(log[log.rindex("{"):log.rindex("}") + 1])
    ln = (f"loudnorm=I={I}:TP=-1.5:LRA=20:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}")
    dst = ["-c:a", "pcm_s24le", os.path.join(OUT, "final_mix.wav")] if final else ["-c:a", "aac", "-b:a", "192k", os.path.join(OUT, "preview_mix.m4a")]
    subprocess.run(src + ["-af", "alimiter=limit=0.7:attack=2:release=60:level=false," + ln + ",alimiter=limit=0.76:attack=1:release=50:level=false", "-ar", "48000"] + dst,
                   check=True, capture_output=True)
    os.remove(tmp)
    print("->", "07_Audio/final_mix.wav" if final else "07_Audio/preview_mix.m4a")
