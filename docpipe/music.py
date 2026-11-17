"""Music for the score: original cues from Suno (through the AI33 API) plus the house BGM library (244 tracks, 8 moods).

  doc.py <prj> music lib <words> [--cat N] [--max S]   search the BGM library by feel / instruments / description (cat 1-8, max seconds)
  doc.py <prj> music make <cue> "<prompt>"              one instrumental Suno cue -> 07_Audio/music/suno_<cue>_1.mp3, _2.mp3 (~3,600 AI33 credits)
  doc.py <prj> music get <cue> <task_id>                fetch a task that was still running when `make` gave up waiting
  doc.py <prj> music credits                            AI33 credit balance (shared with the narration voice)

Suno cues land straight in 07_Audio/music, so audio_spec.MUSIC names them like any library track ("suno_a5_famine_1.mp3").
Library tracks are named by their file name and copied in by `audio` from audio.library (DOCPIPE_LIBRARY) as before.
Each `make` returns two takes; listen to both, use one, and note the pick in HANDOVER.md.
"""
import json, os, re, subprocess, sys, time
import requests
from .ctx import key, BGM_VAULT

API = "https://api.ai33.pro"
VAULT = BGM_VAULT                                     # DOCPIPE_BGM in ~/.docpipe/settings.env
SUFFIX = " Instrumental documentary underscore that sits under narration: no vocals, no humming, no choir words, no drop."
BROWSER = {"User-Agent": "Mozilla/5.0"}          # Suno's CDN answers 403 to python's default agent


def _ai33(method, path, body=None):
    r = requests.request(method, API + path, headers={"xi-api-key": key("AI33_API_KEY")}, json=body, timeout=60)
    r.raise_for_status()
    return r.json()


def lufs(path):
    out = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    m = re.findall(r"^\s+I:\s+(-?[\d.]+) LUFS", out, re.M)
    return float(m[-1]) if m else None


def lib(P, args):
    cat = int(args[args.index("--cat") + 1]) if "--cat" in args else None
    mx = float(args[args.index("--max") + 1]) if "--max" in args else None
    skip = {i for i, a in enumerate(args) if a in ("--cat", "--max")} | {i + 1 for i, a in enumerate(args) if a in ("--cat", "--max")}
    words = [a.lower() for i, a in enumerate(args) if i not in skip]
    C = json.load(open(os.path.join(VAULT, "bgm_vault_catalog.json"), encoding="utf-8"))
    hits = []
    for n, c in enumerate(C["categories"], 1):
        if cat and n != cat:
            continue
        for t in c["tracks"]:
            if mx and t["duration_sec"] > mx:
                continue
            feel, rest = t["feel"].lower(), " ".join((t["title"], t["instruments"], t["description"], c["folder_name"])).lower()
            sc = sum(3 * (w in feel) + (w in rest) for w in words) if words else 1
            if sc:
                hits.append((sc, n, t))
    for sc, n, t in sorted(hits, key=lambda h: (-h[0], h[1], h[2]["index"]))[:20]:
        print(f'{n} {t["filename"]:<58} {t["duration"][3:]} {t["bpm"]:>3}bpm  {t["feel"][:60]}')
    print(f"{len(hits)} matches; use the file name in audio_spec.MUSIC (Kevin MacLeod, CC BY 4.0, credited automatically)")


def _save(P, cue, t, prompt=None):
    out = P.p("07_Audio", "music"); os.makedirs(out, exist_ok=True)
    urls = t["metadata"].get("all_audio_urls") or [t["metadata"]["audio_url"]]
    mp = os.path.join(out, "suno_manifest.json")
    man = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
    for i, u in enumerate(urls, 1):
        name = f"suno_{cue}_{i}.mp3"
        a = requests.get(u, headers=BROWSER, timeout=180); a.raise_for_status()
        open(os.path.join(out, name), "wb").write(a.content)
        clips = (t["metadata"].get("suno_result") or {}).get("clips") or []
        clip = clips[i - 1] if i <= len(clips) else {}
        man[name] = dict(cue=cue, task_id=t["id"], prompt=prompt or man.get(name, {}).get("prompt"), model=t["metadata"].get("major_model_version"),
                         duration=clip.get("duration"), credit_cost=t.get("credit_cost"), made=time.strftime("%Y-%m-%d"), source="Suno via AI33")
        print(f"  {name}  {clip.get('duration') or 0:.0f}s  {lufs(os.path.join(out, name)) or 0:.1f} LUFS")
    json.dump(man, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def _wait(tid, tries=60):
    for _ in range(tries):
        try:
            t = _ai33("GET", f"/v1/task/{tid}")
        except Exception as e:                   # AI33 answers 503 now and then while a task runs (film 14): keep polling
            print(f"  poll {tid[:8]}: {type(e).__name__}, retrying")
            time.sleep(10); continue
        if t["status"] in ("done", "error"):
            return t
        time.sleep(10)
    return None


def make(P, cue, prompt):
    if not re.fullmatch(r"[a-z0-9_]+", cue):
        sys.exit("cue name: lowercase letters, digits and _ only (e.g. a5_famine)")
    full = prompt.strip().rstrip(".") + "." + SUFFIX
    if len(full) > 500:
        sys.exit(f"prompt is {len(full)} chars with the house suffix; Suno takes 500")
    r = _ai33("POST", "/v1s/task/music-generation", {"create_mode": "simple", "make_instrumental": True, "gpt_description_prompt": full})
    print(f"task {r['task_id']} for {cue} (AI33 credits left before charge: {r.get('ec_remain_credits')})")
    t = _wait(r["task_id"])
    if t is None:
        sys.exit(f"still running after 10 min; later: doc.py <prj> music get {cue} {r['task_id']}")
    if t["status"] == "error":
        sys.exit(f"Suno error: {t.get('error_message')} (no retry with the same prompt if it is a content filter; reword or use the library)")
    print(f"done, {t.get('credit_cost')} credits")
    _save(P, cue, t, full)


def run(P, args):
    sys.stdout.reconfigure(encoding="utf-8")
    if not args:
        sys.exit(__doc__)
    if args[0] == "lib":
        return lib(P, args[1:])
    if args[0] == "credits":
        return print("AI33 credits:", _ai33("GET", "/v1/credits")["credits"])
    if args[0] == "make" and len(args) == 3:
        return make(P, args[1], args[2])
    if args[0] == "get" and len(args) == 3:
        t = _wait(args[2], 1) or sys.exit("still running")
        if t["status"] != "done":
            sys.exit(f"task {t['status']}: {t.get('error_message')}")
        return _save(P, args[1], t)
    sys.exit(__doc__)
