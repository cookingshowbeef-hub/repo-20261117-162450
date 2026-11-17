"""Documentary pipeline: one command per step, run on a project folder.

  python doc.py new "<folder name>" "<FILM TITLE>"     new project in 04. Dự án đang Edit (from templates/)
  python doc.py <project> <step> [args]

Steps, in order (see docs/QUY_TRINH.md):
  voice [ids]        narration markdown -> voice lines + word timings           (01_Voice)
  timeline           lines on the film clock                                     (05_Renders/timeline.json)
  script             readable script with V.O. text and numbered GFX             (04_Scripts_Code/<title>_Script.md)
  overlays           overlay_spec.py -> graphics times                           (05_Renders/overlays.json, counter.json)
  gfx [ids|stills [--all]]  Remotion renders; stills = only new/changed ones + review sheet _review_N.jpg                           (06_Graphics/render/ov/*.mov)
  edit               pictures on the clock                                       (05_Renders/edit.json)
  voicetrack         narration alone, for a rough cut                            (07_Audio/voice_only.wav)
  music lib|make|get|credits  score: Suno cues via AI33 + the BGM library     (07_Audio/music/suno_*.mp3)
  audio [preview|final]  music + SFX mix                                         (07_Audio/final_mix.wav)
  render [a b]       the film, or a section                                      (05_Renders/<output>, tests/section_a_b.mp4)
  patch a b [a b]    re-render sections into the existing film (~10 min, not a full render)
  review [--rendered]  DaVinci Resolve review timeline from the source files, no render (05_Renders/review/timeline.fcpxml)
  notes <file.edl>   Resolve's exported markers -> 05_Renders/review/REVIEW_NOTES.md (each note mapped to shot, graphic, line)
  push               put it into the running Resolve: shots, graphics, audio on named tracks, block markers (needs the bridge)
  pull               read the comment markers straight from Resolve -> REVIEW_NOTES.md
  credits            05_Renders/CREDITS.md
  qc [film]          05_Renders/QC_REPORT.md (film = the file Resolve rendered; default: the engine render)
  lint               check timeline + overlays + edit + media in a scratch folder, print only the problems (before build)
  build              timeline + overlays + edit (after any change to the template or the specs)
Media: search <set> | pick px:1=desc ... [--where X] | fetch | commons [topics] | sheets | freesound list "q" | freesound get name id
<project> may be a full path or the folder name (or its number, e.g. 11) inside the projects folder (DOCPIPE_PROJECTS, default ../../04. Dự án đang Edit - Active Projects).
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from docpipe.ctx import PROJECTS as ACTIVE, setting  # noqa: E402  (DOCPIPE_PROJECTS in ~/.docpipe/settings.env)


def find(name):
    if os.path.isdir(name):
        return name
    hits = [d for d in os.listdir(ACTIVE) if d == name or d.startswith(name + ".") or d.startswith(name + " ") or name.lower() in d.lower()]
    if len(hits) != 1:
        sys.exit(f"project {name!r}: {'not found' if not hits else 'ambiguous: ' + ', '.join(hits)}")
    return os.path.join(ACTIVE, hits[0])


def changed_stills(P, rem, force):
    """ids whose props or the Remotion sources changed since their still was made (stills/_hash.json)."""
    import hashlib, json
    src = hashlib.sha1()
    for d, _, fs in sorted(os.walk(os.path.join(rem, "src"))):
        for f in sorted(fs):
            src.update(f.encode()); src.update(open(os.path.join(d, f), "rb").read())
    ovs = json.load(open(P.out("overlays.json"), encoding="utf-8"))
    hp = P.p("06_Graphics", "render", "ov", "stills", "_hash.json")
    old = json.load(open(hp, encoding="utf-8")) if os.path.exists(hp) and not force else {}
    new = {o["id"]: hashlib.sha1((src.hexdigest() + o["kind"] + json.dumps(o["p"], sort_keys=True)).encode()).hexdigest() for o in ovs}
    ids = [o["id"] for o in ovs if old.get(o["id"]) != new[o["id"]]
           or not os.path.exists(P.p("06_Graphics", "render", "ov", "stills", f"{o['id']}_{o['kind']}.png"))]
    return ids, new, hp, {o["id"]: o["kind"] for o in ovs}


def review_sheet(P, ids, kinds):
    """the stills to look at, 4x4 per image at 480x270 (one 1920x1080 picture = 16 graphics) -> stills/_review_N.jpg"""
    import glob, cv2, numpy as np
    d = P.p("06_Graphics", "render", "ov", "stills")
    for f in glob.glob(os.path.join(d, "_review_*.jpg")):
        os.remove(f)
    tiles = []
    for i in ids:
        im = cv2.imdecode(np.fromfile(os.path.join(d, f"{i}_{kinds[i]}.png"), np.uint8), cv2.IMREAD_UNCHANGED)
        if im is None:
            continue
        if im.shape[2] == 4:                                       # transparent graphic: show it over mid grey
            a = im[..., 3:] / 255.0
            im = (im[..., :3] * a + 96 * (1 - a)).astype(np.uint8)
        im = cv2.resize(im, (480, 270), interpolation=cv2.INTER_AREA)
        cv2.putText(im, f"{i} {kinds[i]}", (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1, cv2.LINE_AA)
        tiles.append(im)
    for k in range(0, len(tiles), 16):
        part = tiles[k:k + 16]
        part += [np.zeros_like(part[0])] * (-len(part) % 4)
        cv2.imencode(".jpg", np.vstack([np.hstack(part[r:r + 4]) for r in range(0, len(part), 4)]), [cv2.IMWRITE_JPEG_QUALITY, 82])[1].tofile(
            os.path.join(d, f"_review_{k // 16 + 1}.jpg"))
    return -(-len(tiles) // 16)


def gfx(P, args):
    import shutil, json
    node = (setting("REMOTION_NODE") or next((n for n in (os.path.join(os.path.expanduser("~"), "AppData", "Local", "ms-playwright-go", "1.57.0", "node.exe"),) if os.path.exists(n)), None)
            or shutil.which("node") or sys.exit("no node.exe: install Node.js 20+ or set REMOTION_NODE"))
    rem = P.p("06_Graphics", "remotion")
    env = dict(os.environ, DOC_OUT=P.renders)
    if args[:1] == ["stills"]:                     # only new or changed graphics, then one review sheet of just those
        force = "--all" in args
        ids, new, hp, kinds = changed_stills(P, rem, force)
        named = [a for a in args[1:] if a != "--all"]
        if named:                                  # stills G07 G15: exactly these
            ids = [i for i in new if i in named]
        if not ids:
            return print("stills: nothing changed since the last stills (--all to redo them)")
        subprocess.run([node, "render_ov.mjs", "stills", *ids], cwd=rem, check=True, env=env, stdout=subprocess.DEVNULL)
        done = {i: new[i] for i in ids}
        old = json.load(open(hp, encoding="utf-8")) if os.path.exists(hp) else {}
        json.dump({**old, **done}, open(hp, "w", encoding="utf-8"), indent=0)
        n = review_sheet(P, ids, kinds)
        return print(f"stills: {len(ids)} new/changed of {len(new)} -> {n} review sheet(s) 06_Graphics/render/ov/stills/_review_N.jpg"
                     f" ({', '.join(ids[:12])}{' ...' if len(ids) > 12 else ''})")
    subprocess.run([node, "render_ov.mjs", *args], cwd=rem, check=True, env=env)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    if sys.argv[1] == "new":
        from docpipe.newproject import create
        return create(ACTIVE, *sys.argv[2:])
    from docpipe.ctx import Project
    from docpipe import voice, timeline, overlays, edit, audio, render, qc, media, resolve, music
    P = Project(find(sys.argv[1]))
    step, args = sys.argv[2], sys.argv[3:]
    steps = {"voice": voice.run, "voicetrack": voice.track, "timeline": timeline.run, "script": timeline.script, "overlays": overlays.run,
             "gfx": gfx, "edit": edit.run, "music": music.run, "audio": audio.run, "render": render.run, "patch": render.patch, "credits": qc.credits, "qc": qc.qc,
             "search": media.search, "pick": media.pick, "fetch": media.fetch, "commons": media.commons, "sheets": media.sheets,
             "freesound": media.freesound, "review": resolve.review, "notes": resolve.notes, "push": resolve.push, "pull": resolve.pull}
    if step == "lint":
        from docpipe import lint
        return lint.run(P, args)
    if step == "build":
        for f in (timeline.run, overlays.run, edit.run):
            f(P, [])
        return
    if step not in steps:
        sys.exit(f"unknown step {step!r}\n" + __doc__)
    steps[step](P, args)


if __name__ == "__main__":
    main()
