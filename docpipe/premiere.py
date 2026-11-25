"""The film as a ready-built Adobe Premiere Pro timeline (FCP7 XML / xmeml, which Premiere imports natively), the same cut
as the Resolve review timeline: every element in place from its source file, nothing rendered but the HUD.

  doc.py <prj> premiere [--force] [--no-hud]   -> 05_Renders/premiere/timeline.xml + its media
  (film.json "editor": "premiere" also makes `review` do this)

In Premiere: File > Import... > timeline.xml (it comes in as a bin with the sequence). Then the grade, once:
File > New > Adjustment Layer, drop it on V2 over the whole film, Lumetri Color > Creative > Look: docpipe_<TITLE>_grade.

Tracks (film clock, 30 fps)
  V1  every shot from its source, named "S131 px:6831205": stock clips at the renderer's in-point and speed (Time Remap),
      scaled to cover the frame; photos with the renderer's camera move as Scale/Center keyframes; plates as solid frames
  V2  empty: for the adjustment layer with the grade LUT (it grades the shots below, not the graphics above)
  V3  the vignette, V4 the Remotion graphics (ProRes 4444 with alpha), V5 the HUD (film.json "hud")
  A1  the voice lines; A2+ the music cues, then the sound effects, each baked with the mix's level, fades and ducking
  markers  one per V.O. block with its narration; subtitles: narration.srt (File > Import)
"""
import glob, json, os, re, shutil, sys
from urllib.parse import quote

import numpy as np, cv2

from .resolve import (escape as _escape, fr, safe_name, src_info, clip_timing, photo_views, hud_clip, srt, grade_lut,
                      vignette_png, bake_audio, duration_s)

LUT_DIR = os.path.join(os.environ.get("APPDATA", ""), "Adobe", "Common", "LUTs", "Creative")


def escape(x):
    """XML-escape, and drop control characters (they make Premiere's XML reader fail)."""
    return _escape(re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", str(x)))


def pathurl(path):
    return "file://localhost/" + quote(os.path.abspath(path).replace("\\", "/"), safe="/")


def rate(num, den=1):
    """xmeml <rate>: 29.97 is timebase 30 + ntsc TRUE."""
    ntsc = den == 1001
    tb = round(num / den)
    return f"<rate><timebase>{tb}</timebase><ntsc>{'TRUE' if ntsc else 'FALSE'}</ntsc></rate>"


def premiere(P, args):
    sys.stdout.reconfigure(encoding="utf-8")
    from .render import Renderer
    R = Renderer(P)
    FPS, W, H = R.FPS, R.W, R.H
    D = P.out("premiere")
    os.makedirs(D, exist_ok=True)
    force, no_hud = "--force" in args, "--no-hud" in args
    end = fr(R.TL["end"], FPS)
    A = P.cfg["audio"]
    SEQ = rate(FPS)

    hudp = os.path.join(D, "hud.mov")
    if P.cfg.get("hud") and not no_hud and (force or not os.path.exists(hudp) or not os.path.exists(hudp + ".json")
                                             or os.path.getmtime(hudp) < os.path.getmtime(P.out("counter.json"))):
        print("rendering the HUD track…", flush=True)
        hud_clip(P, R, hudp)
    srt(R.TL, os.path.join(D, "narration.srt"))
    lut = os.path.join(D, "grade.cube")
    grade_lut(P, lut)
    vig = os.path.join(D, "vignette.png")
    vignette_png(P, vig, W, H)

    files, ids = {}, [0]

    def nid():
        ids[0] += 1
        return ids[0]

    def file_el(path, kind, w=None, h=None, num=FPS, den=1, frames=None):
        """the <file> of a clipitem: full the first time a file is used, a reference after that."""
        if path in files:
            return f'<file id="{files[path]}"/>'
        fid = files[path] = f"file-{len(files) + 1}"
        real = safe_name(path, D)
        media = ""
        if kind in ("video", "still"):
            media += (f"<video><samplecharacteristics>{rate(num, den)}<width>{w}</width><height>{h}</height>"
                      f"<pixelaspectratio>square</pixelaspectratio><fielddominance>none</fielddominance></samplecharacteristics></video>")
        if kind == "audio":
            media += "<audio><samplecharacteristics><depth>24</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio>"
        return (f'<file id="{fid}"><name>{escape(os.path.basename(real))}</name><pathurl>{pathurl(real)}</pathurl>{rate(num, den)}'
                f"<duration>{frames}</duration><timecode>{rate(num, den)}<string>00:00:00:00</string><frame>0</frame><displayformat>NDF</displayformat></timecode>"
                f"<media>{media}</media></file>")

    def motion(scale, cx=0.0, cy=0.0, keys=None):
        """Basic Motion: Scale in % of the source's own size (Premiere does not fit on import), Center as a fraction of the
        frame from its middle (x right, y down). keys: [(frame in clip, scale, cx, cy)]."""
        if keys:
            sk = "".join(f"<keyframe><when>{t}</when><value>{s:.3f}</value></keyframe>" for t, s, _, _ in keys)
            ck = "".join(f"<keyframe><when>{t}</when><value><horiz>{x:.5f}</horiz><vert>{y:.5f}</vert></value></keyframe>" for t, _, x, y in keys)
            sv = f"<value>{keys[0][1]:.3f}</value>{sk}"
            cv = f"<value><horiz>{keys[0][2]:.5f}</horiz><vert>{keys[0][3]:.5f}</vert></value>{ck}"
        else:
            sv, cv = f"<value>{scale:.3f}</value>", f"<value><horiz>{cx:.5f}</horiz><vert>{cy:.5f}</vert></value>"
        return ("<filter><effect><name>Basic Motion</name><effectid>basic</effectid><effectcategory>motion</effectcategory>"
                "<effecttype>motion</effecttype><mediatype>video</mediatype>"
                f"<parameter authoringApp=\"PremierePro\"><parameterid>scale</parameterid><name>Scale</name><valuemin>0</valuemin><valuemax>1000</valuemax>{sv}</parameter>"
                f"<parameter authoringApp=\"PremierePro\"><parameterid>center</parameterid><name>Center</name>{cv}</parameter>"
                "</effect></filter>")

    def speed_filter(pct):
        return ("<filter><effect><name>Time Remap</name><effectid>timeremap</effectid><effectcategory>motion</effectcategory>"
                "<effecttype>motion</effecttype><mediatype>video</mediatype>"
                f"<parameter><parameterid>variablespeed</parameterid><name>variablespeed</name><valuemin>0</valuemin><valuemax>1</valuemax><value>0</value></parameter>"
                f"<parameter><parameterid>speed</parameterid><name>speed</name><valuemin>-100000</valuemin><valuemax>100000</valuemax><value>{pct:.4f}</value></parameter>"
                "<parameter><parameterid>reverse</parameterid><name>reverse</name><value>FALSE</value></parameter>"
                "<parameter><parameterid>frameblending</parameterid><name>frameblending</name><value>FALSE</value></parameter>"
                "</effect></filter>")

    def vclip(name, start, n, file_xml, cin, length, filters=""):
        return (f'<clipitem id="clipitem-{nid()}"><name>{escape(name)}</name><enabled>TRUE</enabled><duration>{length}</duration>{SEQ}'
                f"<start>{start}</start><end>{start + n}</end><in>{cin}</in><out>{cin + n}</out>"
                f"<alphatype>straight</alphatype>{file_xml}{filters}</clipitem>")

    tracks = {k: [] for k in ("V1", "V3", "V4", "V5")}
    # ---------------------------------------------------------------- V1 shots
    uses, slowed = {}, 0
    os.makedirs(os.path.join(D, "plates"), exist_ok=True)
    for s in R.SHOTS:
        a, b = fr(s["start"], FPS), fr(s["end"], FPS)
        n = b - a
        if n <= 0:
            continue
        kind, ref = s["src"].split(":", 1)
        name = f"{s['id']} {s['src']}"
        if kind == "plate":
            pp = os.path.join(D, "plates", f"plate_{ref}_solid.png")
            if not os.path.exists(pp):
                im = np.empty((H, W, 3), np.uint8); im[:] = [int(ref[4:6], 16), int(ref[2:4], 16), int(ref[0:2], 16)]
                cv2.imencode(".png", im)[1].tofile(pp)
            tracks["V1"].append(vclip(f"{s['id']} plate", a, n, file_el(pp, "still", W, H, frames=end), 0, end, motion(100)))
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
            sc = max(W / si["w"], H / si["h"]) * 100
            fx = file_el(path, "video", si["w"], si["h"], si["num"], si["den"], si["frames"])
            # in/out on the sequence clock; with Time Remap they count the remapped (slowed) media
            cin = round(t0 * FPS / speed)
            length = round(si["frames"] * si["den"] / si["num"] * FPS / speed)
            cin = min(cin, max(0, length - n))
            filt = motion(sc)
            if speed < 0.999:
                slowed += 1
                filt = speed_filter(speed * 100) + filt
            tracks["V1"].append(vclip(name, a, n, fx, cin, length, filt))
            continue
        im = cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_REDUCED_GRAYSCALE_2)
        ih, iw = im.shape[0] * 2, im.shape[1] * 2
        move = s["treatment"] if kind == "photo" else (s["treatment"] or "in")
        va, vb, cw0, ch0 = photo_views(iw, ih, W, H, move, s.get("focus"), R.SHOTS.index(s))
        cover = max(W / iw, H / ih)
        keys = []
        for j in range(5):                                          # the renderer's smoothstep ease, sampled
            u = j / 4; e = u * u * (3 - 2 * u)
            cx, cy, z = (va[q] + (vb[q] - va[q]) * e for q in range(3))
            keys.append((min(round(n * u), n - 1), cover * z * 100, (0.5 - cx) * cw0 * z / W, (0.5 - cy) * ch0 * z / H))
        tracks["V1"].append(vclip(name, a, n, file_el(path, "still", iw, ih, frames=end), 0, end, motion(0, keys=keys)))
    # ---------------------------------------------------------------- V3 vignette, V4 graphics, V5 HUD
    tracks["V3"].append(vclip("vignette", 0, end, file_el(vig, "still", W, H, frames=end), 0, end, motion(100)))
    for o in R.OVS:
        f = os.path.join(R.OVD, f"{o['id']}_{o['kind']}.mov")
        if not os.path.exists(f):
            print("  ! missing graphic", f); continue
        a, n = fr(o["start"], FPS), fr(o["p"]["dur"], FPS)
        si = src_info(f)
        length = max(n, round(si["frames"] * si["den"] / si["num"] * FPS))
        label = o["p"].get("text") or o["p"].get("title") or o["p"].get("big") or o["p"].get("head") or ""
        tracks["V4"].append(vclip(f"{o['id']} {o['kind']}" + (f" · {label}" if label else ""), a, n,
                                  file_el(f, "video", si["w"], si["h"], si["num"], si["den"], si["frames"]), 0, length,
                                  motion(min(W / si["w"], H / si["h"]) * 100)))
    if os.path.exists(hudp) and P.cfg.get("hud") and not no_hud:
        hp = json.load(open(hudp + ".json")) if os.path.exists(hudp + ".json") else dict(k=1, cx=W / 2, cy=H / 2)
        si = src_info(hudp)
        tracks["V5"].append(vclip("HUD", 0, end, file_el(hudp, "video", si["w"], si["h"], si["num"], si["den"], si["frames"]), 0,
                                  max(end, si["frames"]), motion(100, (hp["cx"] - W / 2) / W, (hp["cy"] - H / 2) / H)))
    # ---------------------------------------------------------------- V6+ editable text (04_Scripts_Code/text_spec.py, optional)
    ntext = 0
    for tr, items in text_tracks(P, FPS, end, nid).items():
        tracks[tr] = items
        ntext += sum(x.startswith("<generatoritem") for x in items)
    # ---------------------------------------------------------------- audio
    aud = bake_audio(P, R, D, A)

    def audio_tracks(mono):
        """stereo (used): one stereo clip per file on a Premiere stereo track, as Premiere itself exports. The track needs
        currentExplodedTrackIndex/totalExplodedTrackCount, or Premiere drops every audio track on import (film 12).
        mono: the classic FCP7 form, each file as a left and a right clip on a pair of tracks (kept as a fallback)."""
        atr = {}
        for x in aud:
            n = x["frames"]
            for ch in ((1, 2) if mono else (1,)):
                tr = (x["track"] - 1) * 2 + ch if mono else x["track"]
                atr.setdefault(tr, []).append(
                    f'<clipitem id="clipitem-{nid()}"{"" if mono else " premiereChannelType=" + chr(34) + "stereo" + chr(34)}>'
                    f"<name>{escape(x['name'])}</name><enabled>TRUE</enabled><duration>{n}</duration>{SEQ}"
                    f"<start>{x['frame']}</start><end>{x['frame'] + n}</end><in>0</in><out>{n}</out>"
                    f"{file_el(x['path'], 'audio', frames=n)}<sourcetrack><mediatype>audio</mediatype><trackindex>{ch}</trackindex></sourcetrack></clipitem>")
        attrs = ' currentExplodedTrackIndex="0" totalExplodedTrackCount="1" premiereTrackType="Stereo"' if not mono else ""
        return "".join(f'<track{attrs}>{"".join(atr.get(t, []))}<enabled>TRUE</enabled><locked>FALSE</locked>'
                       f"<outputchannelindex>{(t - 1) % 2 + 1 if mono else 1}</outputchannelindex></track>" for t in range(1, max(atr, default=1) + 1))
    json.dump(aud, open(os.path.join(D, "audio.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # ---------------------------------------------------------------- markers, LUT, the XML
    markers = []
    for bl in R.TL["blocks"]:
        text = " ".join(f"[{l['id']}] {l['text']}" for l in R.TL["lines"] if l["block"] == bl["id"])
        markers.append(f"<marker><name>{escape(bl['id'] + ' · ' + ', '.join(bl['lines']))}</name><comment>{escape(text[:900])}</comment>"
                       f"<in>{fr(bl['start'], FPS)}</in><out>-1</out></marker>")
    lname = "docpipe_" + re.sub(r"[^A-Za-z0-9_]+", "_", P.cfg["title"]).strip("_") + "_grade.cube"
    try:
        os.makedirs(LUT_DIR, exist_ok=True)
        shutil.copy2(lut, os.path.join(LUT_DIR, lname))
    except OSError as e:
        print(f"   ! could not copy the LUT into Premiere's LUT folder ({e}); browse to 05_Renders/premiere/grade.cube in Lumetri")

    vtrack = lambda items: f"<track>{''.join(items)}<enabled>TRUE</enabled><locked>FALSE</locked></track>"
    vnames = ["V1", "V2", "V3", "V4", "V5"] + sorted((k for k in tracks if k[1:].isdigit() and int(k[1:]) > 5), key=lambda k: int(k[1:]))
    video = "".join(vtrack(tracks[k]) if k in tracks else vtrack([]) for k in vnames)
    title = escape(P.cfg["title"])
    out = os.path.join(D, "timeline.xml")
    write_xml(out, title, end, SEQ, W, H, video, audio_tracks(False), markers)
    missing = [f for f in files if not os.path.exists(safe_name(f, D))]
    nl = sum(x["role"] == "dialogue" for x in aud); nm = sum(x["role"] == "music" for x in aud); ns = sum(x["role"] == "effects" for x in aud)
    print(f"-> {out}: {len(tracks['V1'])} shots ({slowed} slowed), {len(tracks['V4'])} graphics, {ntext} text, {nl} voice lines, {nm} music cues, "
          f"{ns} sound effects, {len(markers)} block markers" + (f", {len(missing)} MISSING" if missing else ""))
    print(f"   Premiere: File > Import > timeline.xml. Grade: Adjustment Layer on V2 over the film, Lumetri > Creative > Look: {lname}")


TEXT_STYLES = {   # Premiere "Text" generator: size in px, origin (x, y) as a share of the frame from the centre, y down
    "title":    dict(size=110, origin=(0, -0.04), font="Georgia"),
    "subtitle": dict(size=44, origin=(0, 0.08), font="Georgia"),
    "chapter":  dict(size=84, origin=(0, -0.03), font="Georgia"),
    "chapter_sub": dict(size=38, origin=(0, 0.07), font="Georgia"),
    "fact":     dict(size=46, origin=(0, 0.36), font="Georgia"),
}


def text_tracks(P, FPS, end, nid):
    """04_Scripts_Code/text_spec.py TEXT = [(t_in, t_out, text, style)] with times from docpipe.cues (S_, E_, word, END)
    -> {"V6": [...], "V7": [...]}: editable Premiere Text generators with a cross dissolve in and out (Premiere ignores
    keyframes on generators, so no motion). Overlapping items go to the next track up; style = a TEXT_STYLES key or a dict."""
    from . import cues
    if not os.path.exists(os.path.join(P.code, "text_spec.py")):
        return {}
    cues.bind(P)
    spec = P.spec("text_spec")
    SEQ, D = rate(FPS), round(0.5 * FPS)
    lanes, out = [], {}
    for t_in, t_out, text, style in sorted(spec.TEXT, key=lambda x: x[0]):
        st = dict(TEXT_STYLES["fact"], **(TEXT_STYLES[style] if isinstance(style, str) else style))
        a, b = max(0, fr(t_in, FPS)), min(end, fr(t_out, FPS))
        if b - a < 2 * D:
            print(f"  ! text too short, skipped: {text!r}"); continue
        lane = next((i for i, e in enumerate(lanes) if e <= a), None)
        if lane is None:
            lanes.append(0); lane = len(lanes) - 1
        lanes[lane] = b
        n, (ox, oy) = b - a, st["origin"]
        dis = lambda s0, s1, al: (f"<transitionitem>{SEQ}<start>{s0}</start><end>{s1}</end><alignment>{al}</alignment><effect><name>Cross Dissolve</name>"
                                  "<effectid>Cross Dissolve</effectid><effectcategory>Dissolve</effectcategory><effecttype>transition</effecttype>"
                                  "<mediatype>video</mediatype><wipecode>0</wipecode><wipeaccuracy>100</wipeaccuracy><startratio>0</startratio>"
                                  "<endratio>1</endratio><reverse>FALSE</reverse></effect></transitionitem>")
        par = lambda pid, name, val: f"<parameter><parameterid>{pid}</parameterid><name>{name}</name><value>{val}</value></parameter>"
        g = (f'<generatoritem id="generator-{nid()}"><name>{escape(text[:60])}</name><duration>{n}</duration>{SEQ}<start>{a}</start><end>{b}</end>'
             f"<in>0</in><out>{n}</out><enabled>TRUE</enabled><anamorphic>FALSE</anamorphic><alphatype>black</alphatype>"
             "<effect><name>Text</name><effectid>Text</effectid><effectcategory>Text</effectcategory><effecttype>generator</effecttype><mediatype>video</mediatype>"
             + par("str", "Text", escape(text)) + par("fontname", "Font", st["font"]) + par("fontsize", "Size", st["size"])
             + par("fontstyle", "Style", 1) + par("fontalign", "Alignment", 2)
             + par("fontcolor", "Font Color", "<alpha>255</alpha><red>255</red><green>255</green><blue>255</blue>")
             + par("origin", "Origin", f"<horiz>{ox}</horiz><vert>{oy}</vert>") + "</effect></generatoritem>")
        out.setdefault(f"V{6 + lane}", []).extend([dis(a, a + D, "start"), g, dis(b - D, b, "end")])
    return out


def write_xml(out, title, end, SEQ, W, H, video, audio, markers):
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="4">
<sequence id="sequence-1">
<name>{title}</name>
<duration>{end}</duration>
{SEQ}
<timecode>{SEQ}<string>00:00:00:00</string><frame>0</frame><displayformat>NDF</displayformat></timecode>
<media>
<video>
<format><samplecharacteristics>{SEQ}<width>{W}</width><height>{H}</height><anamorphic>FALSE</anamorphic><pixelaspectratio>square</pixelaspectratio><fielddominance>none</fielddominance><colordepth>24</colordepth></samplecharacteristics></format>
{video.replace("</clipitem>", "</clipitem>" + chr(10))}
</video>
<audio>
<numOutputChannels>2</numOutputChannels>
<format><samplecharacteristics><depth>24</depth><samplerate>48000</samplerate></samplecharacteristics></format>
<outputs><group><index>1</index><numchannels>2</numchannels><downmix>0</downmix><channel><index>1</index></channel><channel><index>2</index></channel></group></outputs>
{audio.replace("</clipitem>", "</clipitem>" + chr(10))}
</audio>
</media>
{chr(10).join(markers)}
</sequence>
</xmeml>
"""
    open(out, "w", encoding="utf-8").write(xml)
    from xml.dom import minidom
    minidom.parse(out)                                               # fail here, not in Premiere
