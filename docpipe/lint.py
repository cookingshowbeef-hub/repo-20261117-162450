"""Check the whole plan in one pass before `build`, printing only the problems.

  doc.py <prj> lint

Runs timeline, overlays and edit into a scratch folder (05_Renders is not touched), keeps going after a stage fails
when the next stage still has its input, then checks that every picture and music file the plan names is on disk.
Prints the ERROR / warning lines and one summary line per stage; exits 1 when anything must be fixed.
Use it after each round of edits to the template or the specs, and run `build` once it is clean.
"""
import glob, io, json, os, re, shutil, sys, tempfile
from contextlib import redirect_stdout
from . import timeline, overlays, edit
from .ctx import BGM_VAULT

KEEP = re.compile(r"ERROR|warning|^\s*!|unfilled|not in the transcript|missing|overlaps", re.I)
VAULT = BGM_VAULT                                     # DOCPIPE_BGM in ~/.docpipe/settings.env


class Buf(io.StringIO):
    def reconfigure(self, **kw):                 # the steps call sys.stdout.reconfigure(encoding=...)
        pass


def stage(P, name, fn, tail=1):
    buf = Buf()
    err = None
    try:
        with redirect_stdout(buf):
            fn(P, [])
    except SystemExit as e:
        err = e.code if isinstance(e.code, str) else None
        err = err or "failed"
    except Exception as e:                       # a crash in a spec module is a problem to report, not a traceback to read
        err = f"{type(e).__name__}: {e}"
    out = buf.getvalue().splitlines()
    probs = [l.strip() for l in out if KEEP.search(l)]
    summary = " | ".join([l.strip() for l in out if l.strip() and not KEEP.search(l)][-tail:])
    return err, probs, summary


def media(P):
    errs = []
    codes = {f"{m.group(1)}:{m.group(2)}" if m.group(1) else f"lk:{m.group(3)}"
             for m in re.finditer(r"\b(px|pb):(\d+)|\blk:([\w-]+)", P.template())}     # from the template: works even when edit failed
    try:
        codes |= {x["src"] for x in P.load_out("edit.json") if x["src"].startswith(("file:", "nasa:"))}
    except FileNotFoundError:
        pass
    for s in sorted(codes):
        kind, ref = s.split(":", 1)
        if kind in ("px", "pb"):
            if not glob.glob(P.p("02_B-Roll", {"px": "pexels", "pb": "pixabay"}[kind], f"{ref}_*.mp4")):
                errs.append(f"{s} not downloaded (doc.py <prj> fetch)")
        elif kind == "lk":
            try:
                if not os.path.exists(P.local(ref)):
                    errs.append(f"{s} missing: {P.local(ref)}")
            except SystemExit as e:
                errs.append(str(e.code))
        elif kind == "file" and not os.path.exists(P.p(ref)):
            errs.append(f"{s} missing")
        elif kind == "nasa" and not os.path.exists(P.p("03_Images", "nasa", ref)):
            errs.append(f"{s} missing")
    try:
        from . import cues
        cues.bind(P)                             # audio_spec times are written against the timeline
        spec = P.spec("audio_spec", required=False)
    except Exception as e:
        return errs + [f"audio_spec.py: {type(e).__name__}: {e}"]
    if spec is not None:
        have = {f for _, _, fs in os.walk(VAULT) for f in fs} | set(os.listdir(P.p("07_Audio", "music")) if os.path.isdir(P.p("07_Audio", "music")) else [])
        for m in getattr(spec, "MUSIC", []):
            if m[1] not in have:
                errs.append(f"music {m[0]}: {m[1]} is neither in 07_Audio/music nor in the BGM library")
    return errs


def style_rules(P, tmp):
    """the film against its style's house rules (graphics per minute, music coverage): warnings, never errors."""
    from . import style
    f = os.path.join(tmp, "overlays.json")
    ovs = json.load(open(f, encoding="utf-8")) if os.path.exists(f) else None
    music = None
    try:
        from . import cues
        cues.bind(P)
        spec = P.spec("audio_spec", required=False)
        if spec is not None and getattr(spec, "MUSIC", None):
            music = [(m[2], m[3]) for m in spec.MUSIC]
    except Exception:
        pass
    real, P.renders = P.renders, tmp if os.path.exists(os.path.join(tmp, "timeline.json")) else P.renders
    try:
        summary, warn = style.check(P, ovs, music)
    finally:
        P.renders = real
    for w in warn:
        print(f"  {w}")
    print(f"style     {'ok' if not warn else 'warn'}  {summary}")
    return len(warn)


def run(P, args):
    sys.stdout.reconfigure(encoding="utf-8")
    real, tmp = P.renders, tempfile.mkdtemp(prefix="doclint_")
    P.renders = tmp
    n_err = n_warn = 0
    try:
        for name, fn in (("timeline", timeline.run), ("overlays", overlays.run), ("edit", edit.run)):
            need = {"overlays": "timeline.json", "edit": "overlays.json"}.get(name)
            if need and not os.path.exists(os.path.join(tmp, need)):
                print(f"{name:9} skipped (no {need})"); continue
            err, probs, summary = stage(P, name, fn, 2 if name == "edit" else 1)
            for p in probs:
                print(f"  {p}")
            e = sum(1 for p in probs if not p.lower().startswith("warning")) + (1 if err and not probs else 0)
            w = len(probs) - sum(1 for p in probs if not p.lower().startswith("warning"))
            n_err += e if err else 0; n_warn += w
            print(f"{name:9} {'FAIL: ' + err if err else 'ok'}  {summary[:150]}")
        m = media(P)
        for x in m:
            print(f"  {x}")
        n_err += len(m)
        print(f"media     {'FAIL' if m else 'ok'}  {len(m)} missing file(s)")
        n_warn += style_rules(P, tmp)
    finally:
        P.renders = real
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"lint: {n_err} problem(s) to fix, {n_warn} warning(s)" + ("" if n_err else " - ready for build"))
    if n_err:
        sys.exit(1)
