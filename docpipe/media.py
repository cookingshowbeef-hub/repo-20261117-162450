"""Finding and fetching pictures and sounds. Queries and Commons topics live in the project's media_spec.py:
  BROLL  = {set name: [search queries]}                       stock video searches (Pexels + Pixabay)
  TOPICS = {topic: ([queries], how many to keep, must-mention regex, min width)}   Wikimedia Commons photos

  doc.py <prj> search <set>                     thumbnails + contact sheets -> 02_B-Roll/candidates/<set>/sheet_N.jpg (vet them by eye)
  doc.py <prj> pick px:123=what it shows [pb:45=...] [--where "Siberia (not Yakutia)"]   add vetted clips to picks.json (default where: generic)
  doc.py <prj> fetch                            download every pick -> 02_B-Roll/pexels|pixabay/<id>_<slug>.mp4 + manifest.json
  doc.py <prj> commons [topic ...]              free-licence Commons photos -> 03_Images/commons/<topic>/ + manifest.json, then contact sheets
  doc.py <prj> sheets                           rebuild the photo contact sheets (topic#n codes) -> 03_Images/commons/sheets/
  doc.py <prj> freesound list "query" [min_s max_s] | get <name> <id>    CC0 sounds -> 07_Audio/freesound/
Keys come from the environment or the engine tools and are never printed. Location rule: a clip's "where" is what it may honestly
stand for; "generic" clips are never captioned as a named place.
"""
import json, os, re, sys, time
import numpy as np, cv2, requests
from .ctx import key


def _sheet(tiles, out, per=48, cols=6):
    blank = np.zeros_like(tiles[0])
    for s in range(0, len(tiles), per):
        part = tiles[s:s + per]; part += [blank] * (-len(part) % cols)
        cv2.imencode(".jpg", np.vstack([np.hstack(part[i:i + cols]) for i in range(0, len(part), cols)]), [cv2.IMWRITE_JPEG_QUALITY, 82])[1].tofile(
            os.path.join(out, f"sheet_{s // per + 1}.jpg"))


def search(P, args):
    sys.stdout.reconfigure(encoding="utf-8")
    spec = P.spec("media_spec")
    name = args[0] if args else sys.exit("search needs a set name from media_spec.BROLL: " + ", ".join(spec.BROLL))
    Q = spec.BROLL[name]
    out = P.p("02_B-Roll", "candidates", name)
    os.makedirs(out, exist_ok=True)
    seen_p = P.p("02_B-Roll", "candidates", "seen.json")
    seen = set(json.load(open(seen_p, encoding="utf-8"))) if os.path.exists(seen_p) else set()
    picks = P.load("02_B-Roll", "candidates", "picks.json", default={"pexels": {}, "pixabay": {}})
    seen |= {f"px:{k}" for k in picks.get("pexels", {})} | {f"pb:{k}" for k in picks.get("pixabay", {})}
    PEX, PIX = key("PEXELS_API_KEY"), key("PIXABAY_API_KEY")
    cands = {}
    for q in Q:
        try:
            for v in requests.get("https://api.pexels.com/videos/search", headers={"Authorization": PEX}, params={"query": q, "per_page": 15}, timeout=30).json().get("videos", []):
                files = sorted((f for f in v["video_files"] if f.get("width")), key=lambda f: f["width"])
                cid = f"px:{v['id']}"
                if cid in seen or not files or files[-1]["width"] < 1920:
                    continue
                pics = v.get("video_pictures") or []
                cands.setdefault(cid, dict(q=q, slug=re.sub(r"https://www.pexels.com/video/|-\d+/?$", "", v["url"]), user=v["user"]["name"],
                                           dur=v["duration"], thumb=pics[len(pics) // 2]["picture"] if pics else None))
            for h in requests.get("https://pixabay.com/api/videos/", params={"key": PIX, "q": q, "per_page": 15, "video_type": "film"}, timeout=30).json().get("hits", []):
                big = h["videos"].get("large") or {}
                cid = f"pb:{h['id']}"
                if cid in seen or (big.get("width") or 0) < 1920:
                    continue
                cands.setdefault(cid, dict(q=q, slug=h["tags"], user=h["user"], dur=h["duration"],
                                           thumb=(h["videos"].get("medium") or {}).get("thumbnail") or big.get("thumbnail")))
        except requests.RequestException:
            pass
        time.sleep(0.8)
    tiles = []
    for cid, c in cands.items():
        p = os.path.join(out, cid.replace(":", "_") + ".jpg")
        if c["thumb"] and not os.path.exists(p):
            try:
                open(p, "wb").write(requests.get(c["thumb"], timeout=30).content)
            except requests.RequestException:
                continue
        im = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR) if os.path.exists(p) else None
        if im is None:
            continue
        im = np.pad(cv2.resize(im, (320, 180)), ((0, 22), (0, 0), (0, 0)))
        cv2.putText(im, f"{cid} {c['slug'][:24]}", (3, 196), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (0, 255, 255), 1, cv2.LINE_AA)
        tiles.append(im)
    json.dump(cands, open(os.path.join(out, "candidates.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(sorted(seen | set(cands)), open(seen_p, "w", encoding="utf-8"))
    if tiles:
        _sheet(tiles, out)
    print(f"{len(cands)} new candidates, {-(-len(tiles) // 48)} sheets in {out}")


def pick(P, args):
    where = "generic"
    if "--where" in args:
        i = args.index("--where"); where = args[i + 1]; args = args[:i] + args[i + 2:]
    path = P.p("02_B-Roll", "candidates", "picks.json")
    d = P.load("02_B-Roll", "candidates", "picks.json", default={"pexels": {}, "pixabay": {}})
    n = 0
    for a in args:
        code, _, use = a.partition("=")
        kind, vid = code.split(":")
        d.setdefault({"px": "pexels", "pb": "pixabay"}[kind], {})[vid] = [use or "?", where]
        n += 1
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{n} picks saved ({where})")


def fetch(P, args):
    sys.stdout.reconfigure(encoding="utf-8")
    picks = P.load("02_B-Roll", "candidates", "picks.json")
    PEX, PIX = key("PEXELS_API_KEY"), key("PIXABAY_API_KEY")

    def api_get(url, **kw):
        # Pexels answers bursts with 429 (no Retry-After) even with hourly quota left: back off and retry
        for wait in (20, 40, 60, 90, 120, 180):
            r = requests.get(url, timeout=30, **kw)
            if r.status_code != 429:
                r.raise_for_status()
                return r.json()
            print(f"   429, waiting {wait}s", flush=True)
            time.sleep(wait)
        r.raise_for_status()

    def stream(url, dst):
        with requests.get(url, stream=True, timeout=180) as r:
            r.raise_for_status()
            with open(dst + ".part", "wb") as fh:
                for chunk in r.iter_content(1 << 20):
                    fh.write(chunk)
        os.replace(dst + ".part", dst)
    for kind in ("pexels", "pixabay"):
        out = P.p("02_B-Roll", kind)
        os.makedirs(out, exist_ok=True)
        mpath = os.path.join(out, "manifest.json")
        man = json.load(open(mpath, encoding="utf-8")) if os.path.exists(mpath) else {}
        for vid, (use, where) in picks.get(kind, {}).items():
            if vid in man and os.path.exists(os.path.join(out, man[vid]["file"])):
                continue
            try:
                if kind == "pexels":
                    v = api_get(f"https://api.pexels.com/videos/videos/{vid}", headers={"Authorization": PEX})
                    files = sorted((f for f in v["video_files"] if (f.get("width") or 0) >= 1920), key=lambda f: f["width"])
                    url, w, user, page = files[0]["link"], files[0]["width"], v["user"]["name"], v["url"]
                    slug = re.sub(r"https://www.pexels.com/video/|-?\d+/?$", "", page).strip("/") or "clip"
                else:
                    h = api_get("https://pixabay.com/api/videos/", params={"key": PIX, "id": vid})["hits"][0]
                    big = h["videos"]["large"]
                    url, w, user, page = big["url"], big["width"], h["user"], h["pageURL"]
                    slug = re.sub(r"[^a-z0-9]+", "-", h["tags"].lower())[:40].strip("-")
                name = f"{vid}_{slug[:50]}.mp4"
                stream(url, os.path.join(out, name))
                man[vid] = dict(file=name, user=user, url=page, width=w, use=use, where=where,
                                licence="Pexels License" if kind == "pexels" else "Pixabay Content License")
                json.dump(man, open(mpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                print(f"{kind} {vid} {w}px {name[:60]}", flush=True)
            except Exception as e:
                print(f"{kind} {vid} FAILED {type(e).__name__}", flush=True)
            time.sleep(1)


FREE = re.compile(r"^(public domain|pd|cc0|cc by(-sa)? \d|cc-by(-sa)?-\d)", re.I)
clean = lambda html: re.sub(r"<[^>]+>", "", html or "").strip()


def commons(P, args):
    sys.stdout.reconfigure(encoding="utf-8")
    spec = P.spec("media_spec")
    root = P.p("03_Images", "commons")
    os.makedirs(root, exist_ok=True)
    S = requests.Session()
    S.headers["User-Agent"] = P.cfg["commons_user_agent"]
    API = "https://commons.wikimedia.org/w/api.php"

    def get(params):
        for attempt in range(6):
            r = S.get(API, params=params, timeout=40)
            if r.status_code == 429:
                time.sleep(20 * (attempt + 1)); continue
            r.raise_for_status(); time.sleep(1.5)
            return r.json()
        raise RuntimeError("Commons kept rate-limiting")
    mpath = os.path.join(root, "manifest.json")
    manifest = json.load(open(mpath, encoding="utf-8")) if os.path.exists(mpath) else {}
    for topic, (queries, keep, must, minw) in spec.TOPICS.items():
        if args and topic not in args:
            continue
        os.makedirs(os.path.join(root, topic), exist_ok=True)
        got = sum(1 for v in manifest.values() if v["topic"] == topic)
        for q in queries:
            if got >= keep:
                break
            j = get({"action": "query", "generator": "search", "gsrsearch": q, "gsrnamespace": 6, "gsrlimit": 40, "prop": "imageinfo",
                     "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1920, "format": "json"})
            for p in sorted(j.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0)):
                if got >= keep:
                    break
                ii = (p.get("imageinfo") or [{}])[0]
                m = ii.get("extmetadata", {})
                lic, name = clean(m.get("LicenseShortName", {}).get("value")), p["title"][5:]
                desc = clean(m.get("ImageDescription", {}).get("value"))
                if not re.search(must, name + " " + desc + " " + clean(m.get("Categories", {}).get("value")), re.I):
                    continue                                                # must name the place / subject
                if name in manifest or ii.get("mime") not in ("image/jpeg", "image/png") or ii.get("width", 0) < minw or not FREE.match(lic):
                    continue
                url = ii["url"] if ii["width"] <= 2600 else (ii.get("thumburl") or ii["url"])
                base, ext = os.path.splitext(name)
                safe = re.sub(r"[^\w-]+", "_", base)[:60] + ext.lower()
                for attempt in range(4):
                    a = S.get(url, timeout=120)
                    if a.status_code != 429:
                        break
                    wait = int(a.headers.get("retry-after") or 120) + 15
                    print(f"   throttled, waiting {wait}s", flush=True); time.sleep(wait)
                if a.status_code != 200:
                    continue
                open(os.path.join(root, topic, safe), "wb").write(a.content)
                time.sleep(6)
                manifest[name] = dict(topic=topic, file=f"{topic}/{safe}", author=clean(m.get("Artist", {}).get("value"))[:120], licence=lic,
                                      page=ii.get("descriptionurl"), width=ii["width"], height=ii["height"],
                                      date=clean(m.get("DateTimeOriginal", {}).get("value"))[:40], description=desc[:300])
                got += 1
                json.dump(manifest, open(mpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"{topic:18s} {got:3d} images", flush=True)
    sheets(P, [])


def sheets(P, args):
    """one contact sheet per topic, numbered in manifest order (old numbers never move: new photos are appended)."""
    R = P.p("03_Images", "commons")
    M = json.load(open(os.path.join(R, "manifest.json"), encoding="utf-8"))
    os.makedirs(os.path.join(R, "sheets"), exist_ok=True)
    idx, by = {}, {}
    for t, m in M.items():
        by.setdefault(m["topic"], []).append(t)
    for topic, titles in by.items():
        tiles = []
        for n, t in enumerate(titles):
            idx[f"{topic}#{n}"] = t
            fp = os.path.join(R, M[t]["file"])
            im = cv2.imdecode(np.fromfile(fp, np.uint8), cv2.IMREAD_COLOR) if os.path.exists(fp) else None
            if im is None:                                           # unreadable download (TIFF/SVG/truncated): keep its number, grey tile
                print(f"  {topic}#{n} unreadable, do not use: {M[t]['file']}")
                im = np.full((300, 400, 3), 60, np.uint8)
            s = min(400 / im.shape[1], 300 / im.shape[0]); im = cv2.resize(im, (int(im.shape[1] * s), int(im.shape[0] * s)), interpolation=cv2.INTER_AREA)
            tile = np.zeros((330, 400, 3), np.uint8); tile[:im.shape[0], :im.shape[1]] = im
            cv2.putText(tile, f"#{n} {t[:44]}", (3, 322), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 255), 1, cv2.LINE_AA)
            tiles.append(tile)
        tiles += [np.zeros_like(tiles[0])] * (-len(tiles) % 5)
        cv2.imencode(".jpg", np.vstack([np.hstack(tiles[i:i + 5]) for i in range(0, len(tiles), 5)]), [cv2.IMWRITE_JPEG_QUALITY, 82])[1].tofile(
            os.path.join(R, "sheets", f"{topic}.jpg"))
    json.dump(idx, open(os.path.join(R, "sheets", "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(idx), "photos on", len(by), "sheets")


def freesound(P, args):
    sys.stdout.reconfigure(encoding="utf-8")
    K = key("FREESOUND_API_KEY")
    lib = P.p("07_Audio", "freesound"); os.makedirs(lib, exist_ok=True)
    S = requests.Session()
    F = "id,name,username,duration,license,url,num_downloads,avg_rating,num_ratings,previews,tags,description"
    if args[0] == "list":
        mind, maxd = (float(args[2]), float(args[3])) if len(args) > 3 else (1, 240)
        r = S.get("https://freesound.org/apiv2/search/text/", params={"query": args[1], "filter": f'license:"Creative Commons 0" duration:[{mind} TO {maxd}]',
                                                                       "fields": F, "page_size": 40, "token": K}, timeout=40)
        r.raise_for_status()
        sc = lambda x: x["num_downloads"] ** 0.5 * (1 + (x["avg_rating"] or 3) / 5) * (1 if x["num_ratings"] >= 2 else 0.6)
        for x in sorted(r.json().get("results", []), key=sc, reverse=True)[:12]:
            print(f'{x["id"]:>8} {x["duration"]:6.1f}s {x["num_downloads"]:6d}dl  {x["name"][:55]}  [{",".join(x["tags"][:7])}]')
        return
    name, sid = args[1], args[2]
    r = S.get(f"https://freesound.org/apiv2/sounds/{sid}/", params={"token": K, "fields": F}, timeout=40); r.raise_for_status(); x = r.json()
    if "Creative Commons 0" not in x["license"] and "publicdomain/zero" not in x["license"]:
        sys.exit(f"{sid} is not CC0: {x['license']}")
    a = S.get(x["previews"]["preview-hq-mp3"], timeout=180); a.raise_for_status()
    open(os.path.join(lib, name + ".mp3"), "wb").write(a.content)
    mp = os.path.join(lib, "manifest.json")
    man = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
    man[name] = dict(id=x["id"], name=x["name"], author=x["username"], license=x["license"], url=x["url"], duration=round(x["duration"], 1))
    json.dump(man, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("got", name, "<-", x["name"], f"({x['duration']:.1f}s)")
