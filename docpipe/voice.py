"""Narration: one AI33 voice clip per paragraph of the narration markdown, then word timings with faster-whisper.

Each "## " heading starts a section (tags from film.json "sections"); every non-empty, non-# line is one voice line <tag>_<nn>.
Writes 01_Voice/lines/<id>.mp3 / .wav (48 kHz stereo, trimmed) / .words.json and 01_Voice/narration.json.
  doc.py <prj> voice              all missing lines, then timings
  doc.py <prj> voice c0_02 a3_05  redo those lines (old files kept as .old)
"""
import json, os, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
import requests
from .ctx import key, TOOLS


def paragraphs(P):
    body = open(os.path.join(P.code, P.cfg["narration_md"]), encoding="utf-8").read()
    tags, out, sec, n = P.cfg["sections"], [], -1, 0
    for line in body.splitlines():
        if line.startswith("## "):
            sec, n = sec + 1, 0
        elif line.strip() and not line.startswith(("#", "<!--")) and sec >= 0:
            n += 1
            out.append(dict(id=f"{tags[sec]}_{n:02d}", section=tags[sec], text=re.sub(r"\*([^*]+)\*", r"\1", line.strip())))
    if sec + 1 != len(tags):
        sys.exit(f"narration has {sec + 1} sections, film.json lists {len(tags)}")
    return out


def tts(text, mp3, vcfg):
    s = requests.Session()
    k = key("AI33_API_KEY")
    s.headers.update({"xi-api-key": k, "Authorization": k, "User-Agent": "AI33-Documentary/1.0"})
    for attempt in range(3):
        r = s.post("https://api.ai33.pro/v3/text-to-speech",
                   files={"voice_id": (None, vcfg["id"]), "text": (None, text), "speed": (None, str(vcfg["speed"]))}, timeout=60)
        if r.status_code == 200:
            break
        time.sleep(10 * (attempt + 1))
    else:
        raise RuntimeError(f"submit failed with status {r.status_code}")
    tid, t0 = r.json()["task_id"], time.time()
    while time.time() - t0 < 600:
        time.sleep(4)
        for base in ("https://api.ai33.pro/v1/task", "https://api.ai33.pro/v3/task"):
            try:
                p = s.get(f"{base}/{tid}", timeout=20)
                if p.status_code != 200:
                    continue
                j = p.json(); d = j.get("data") or {}
                st = j.get("status") or d.get("status")
                if st == "done":
                    meta = j.get("metadata") or d.get("metadata") or {}
                    dl = s.get(meta.get("audio_url") or j.get("audio_url") or d.get("audio_url"), timeout=120)
                    dl.raise_for_status()
                    open(mp3, "wb").write(dl.content)
                    return
                if st in ("failed", "error", "cancelled", "canceled"):
                    raise RuntimeError("voice task failed")
                break
            except requests.RequestException:
                pass
    raise RuntimeError("voice task timed out")


def run(P, args):
    out = P.p("01_Voice", "lines")
    os.makedirs(out, exist_ok=True)
    vcfg = P.cfg["voice"]
    paras = paragraphs(P)
    for p in paras:
        if p["id"] in args:
            for ext in (".mp3", ".wav", ".words.json"):
                f = os.path.join(out, p["id"] + ext)
                if os.path.exists(f):
                    os.replace(f, f + ".old")

    def voice(p):
        mp3, wav = os.path.join(out, p["id"] + ".mp3"), os.path.join(out, p["id"] + ".wav")
        if not os.path.exists(mp3):
            tts(p["text"], mp3, vcfg)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-ac", "2", "-ar", "48000", "-af",
                        "silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse",
                        wav], check=True)
        print("voiced", p["id"], flush=True)
    todo = [p for p in paras if not os.path.exists(os.path.join(out, p["id"] + ".wav"))]
    with ThreadPoolExecutor(vcfg["threads"]) as ex:
        list(ex.map(voice, todo))

    model = None
    for p in paras:
        wj = os.path.join(out, p["id"] + ".words.json")
        if not os.path.exists(wj):
            if model is None:
                from . import cuda_dlls  # noqa: F401  (pip-installed NVIDIA DLLs on PATH)
                from faster_whisper import WhisperModel
                model = WhisperModel(vcfg["whisper"], device="cuda", compute_type="float16")
            segs, _ = model.transcribe(os.path.join(out, p["id"] + ".wav"), language=vcfg["language"], word_timestamps=True)
            json.dump([[w.word.strip(), round(w.start, 3), round(w.end, 3)] for sg in segs for w in sg.words],
                      open(wj, "w", encoding="utf-8"), ensure_ascii=False)
        p["duration"] = round(float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                                    os.path.join(out, p["id"] + ".wav")], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout), 2)
    json.dump(paras, open(P.p("01_Voice", "narration.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(paras)} lines, {sum(p['duration'] for p in paras) / 60:.1f} min of voice")


def track(P, args):
    """narration alone on the film clock -> 07_Audio/voice_only.wav (voice RMS at audio.voice_rms), for the rough cut."""
    import numpy as np
    TL, SR = P.timeline(), 48000
    bus = np.zeros((int((TL["end"] + 1) * SR), 2), np.float32)
    for l in TL["lines"]:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", P.p("01_Voice", "lines", f"{l['id']}.wav"), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
        x = np.frombuffer(raw, np.float32).reshape(-1, 2)
        s = int(l["start"] * SR); bus[s:s + len(x)] += x[:len(bus) - s]
    v = bus[np.abs(bus[:, 0]) > 0.01]
    bus *= 10 ** (P.cfg["audio"]["voice_rms"] / 20) / np.sqrt(np.mean(v ** 2))
    os.makedirs(P.p("07_Audio"), exist_ok=True)
    tmp = P.p("07_Audio", "_v.f32"); bus.astype(np.float32).tofile(tmp)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", tmp, "-af", "alimiter=limit=0.89:level=false",
                    "-c:a", "pcm_s16le", P.p("07_Audio", "voice_only.wav")], check=True)
    os.remove(tmp)
    print(f"voice_only.wav {len(bus) / SR:.1f}s")
