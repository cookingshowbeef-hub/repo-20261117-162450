"""Edit styles: one JSON preset per look in ENGINE/styles/<name>.json, chosen per film with film.json "style": "<name>".

Settings are layered:  ctx.DEFAULTS  <-  styles/<name>.json (after its "extends" chain)  <-  film.json.
So a style sets the film-wide look (grade, letterbox, cut length, card timing, ducking, graphics palette/fonts/motion,
house rules such as graphics per minute and music coverage), and film.json can still override any single key.
A film.json without "style" gets ctx.DEFAULTS alone (films made before styles existed are unchanged).

"style" is either a preset name in styles/ ("warm-vintage") or the film's own style file: a path ending in .json, relative
to 04_Scripts_Code ("style.json", what `doc.py new ... --style <file>` and `style set <file>` write) or absolute. A file's
"extends" may name a preset or another .json next to it. styles/_template.json is the fill-in example for users.

Preset keys (all optional; see docs/STYLES.md):
  name, label, description, extends   meta ("extends": another preset to start from)
  timing / edit / overlay / render / audio   same keys as film.json (merged into the film's settings)
  gfx     palette, fonts, fonts_vi, motion, text_shadow, grain -> 06_Graphics/remotion/src/style.json for the Remotion graphics
  rules   gfx_per_min [lo, hi], music_coverage (0-1), music_under_voice_db, suno_cues [lo, hi]  (lint/audio report against these)
  notes   free text for Claude per stage: narration, broll, graphics, music (Suno prompt character), sound
"""
import json, os, sys

import numpy as np

STYLES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "styles")
META = ("name", "label", "description", "extends")
BASE = "netflix-cold"          # the gfx block a style-less film falls back to


def _merge(a, b):
    out = dict(a)
    for k, v in b.items():
        out[k] = _merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


is_file = lambda name: str(name).lower().endswith(".json") or os.sep in str(name) or "/" in str(name)
KNOWN = set(META) | {"timing", "edit", "overlay", "render", "audio", "gfx", "rules", "notes", "voice"}
GRADE = {"contrast", "lift", "cool", "warm", "saturation", "vignette", "letterbox"}


def path(name, base=None):
    """preset name -> styles/<name>.json; a .json path -> itself (relative to base, the film's 04_Scripts_Code)."""
    if is_file(name):
        return os.path.normpath(name if os.path.isabs(name) else os.path.join(base or os.getcwd(), name))
    return os.path.join(STYLES_DIR, f"{name}.json")


def _read(p, name):
    try:
        return json.load(open(p, encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"style {name!r}: not valid JSON ({p}: line {e.lineno}, col {e.colno}: {e.msg})")


def problems(s):
    """unknown keys and bad values in a style file: a typo would otherwise be ignored without a word."""
    out = [f"unknown key {k!r}" for k in s if k not in KNOWN and not k.startswith("_")]
    g = s.get("render", {}).get("grade", {})
    out += [f"render.grade: unknown key {k!r} (have {', '.join(sorted(GRADE))})" for k in g if k not in GRADE]
    for k, v in (s.get("gfx", {}).get("palette") or {}).items():
        if not (isinstance(v, str) and v.startswith("#") and len(v) in (4, 7)):
            out.append(f"gfx.palette.{k}: {v!r} is not a #RRGGBB colour")
    return out


_WARNED = set()


def load(name, base=None, _seen=()):
    """the preset or style file with its "extends" chain resolved (meta keys kept from the file itself)."""
    p = path(name, base)
    if not os.path.exists(p):
        where = p if is_file(name) else STYLES_DIR
        sys.exit(f"style {name!r} not found ({where}); presets: {', '.join(n for n, *_ in available()) or 'none'}")
    if p in _seen:
        sys.exit(f"style {name!r}: extends loop")
    s = _read(p, name)
    bad = problems(s)
    if bad and p not in _WARNED:                     # once per file per run
        _WARNED.add(p)
        print(f"  ! style {name}: " + "; ".join(bad))
    for f in font_files(s.get("gfx", {})):           # a font file next to the style file: remember where it is
        if not os.path.isabs(f["file"]) and os.path.isfile(os.path.join(os.path.dirname(p), f["file"])):
            f["src"] = os.path.join(os.path.dirname(p), f["file"])
    if s.get("extends"):
        base_s = {k: v for k, v in load(s["extends"], os.path.dirname(p), _seen + (p,)).items() if k not in META}
        if "gfx" in base_s:
            base_s["gfx"] = drop_vi(base_s["gfx"], s.get("gfx", {}))
        s = _merge(base_s, s)
    s["name"] = name
    return s


def font_files(g):
    """every {"file": ...} entry under gfx.fonts and gfx.fonts_vi (the dicts themselves, so they can be annotated)."""
    return [x for blk in ("fonts", "fonts_vi") for f in (g.get(blk) or {}).values() if isinstance(f, dict)
            for x in (f.get("files") or []) if isinstance(x, dict) and x.get("file")]


def drop_vi(base, top):
    """base gfx without the Vietnamese substitutes of the font slots that `top` replaces with another family and gives
    no Vietnamese version of: a fonts_vi entry belongs to the font it was made for (otherwise every style's own font,
    e.g. noir's Courier New, turned back into Lora/Be Vietnam Pro in a Vietnamese film)."""
    fv = dict(base.get("fonts_vi") or {})
    tv = top.get("fonts_vi") or {}
    for k, f in (top.get("fonts") or {}).items():
        old = (base.get("fonts") or {}).get(k) or {}
        if k in fv and k not in tv and isinstance(f, dict) and f.get("family") != old.get("family"):
            fv.pop(k)
    return dict(base, fonts_vi=fv) if "fonts_vi" in base else base


def layer(name, base=None):
    """the part of a preset or style file that merges into the film's settings."""
    return {k: v for k, v in load(name, base).items() if k not in META} if name else {}


BRIEF_EXT = (".md", ".txt", ".docx", ".pdf", ".png", ".jpg", ".jpeg", ".webp")


def adopt(src, code):
    """a style the user brought for this film -> (value for film.json "style", note).
    .json: checked, copied to 04_Scripts_Code/style.json. A brief (.md/.txt/.docx/.pdf/image): copied as STYLE_BRIEF.<ext>
    for Claude to turn into style.json; the film keeps the default style until then. Anything else: a preset name."""
    if not os.path.isfile(src):
        load(src)                                       # preset name (fails with the list of presets)
        return src, f"preset {src}"
    ext = os.path.splitext(src)[1].lower()
    if ext == ".json":
        import shutil
        s = _read(src, src)
        bad = problems(s)
        here = os.path.dirname(os.path.abspath(src))
        if s.get("extends") and is_file(s["extends"]) and not os.path.isabs(s["extends"]):
            s["extends"] = os.path.normpath(os.path.join(here, s["extends"]))
        copied = []
        for f in font_files(s.get("gfx", {})):          # font files the user put next to the style (or gave by full path)
            p = f["file"] if os.path.isabs(f["file"]) else os.path.join(here, f["file"])
            if os.path.isfile(p):                       # -> 04_Scripts_Code/fonts/, so the film keeps them with its style.json
                os.makedirs(os.path.join(code, "fonts"), exist_ok=True)
                if os.path.normcase(os.path.abspath(p)) != os.path.normcase(os.path.join(code, "fonts", os.path.basename(p))):
                    shutil.copy2(p, os.path.join(code, "fonts", os.path.basename(p)))
                f["file"] = "fonts/" + os.path.basename(p)
                copied.append(os.path.basename(p))
            elif os.path.isabs(f["file"]) or not any(os.path.isfile(os.path.join(d, f["file"])) for d in PUBLIC_DIRS()):
                bad.append(f"font file {f['file']!r} not found (next to the style file or in templates/remotion/public)")
        json.dump(s, open(os.path.join(code, "style.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        load("style.json", code)                        # its extends chain must resolve
        return "style.json", (f"style file {os.path.basename(src)} -> 04_Scripts_Code/style.json"
                              + (f", fonts -> 04_Scripts_Code/fonts: {', '.join(copied)}" if copied else "")
                              + (f" (check: {'; '.join(bad)})" if bad else ""))
    if ext in BRIEF_EXT:
        import shutil
        shutil.copy2(src, os.path.join(code, "STYLE_BRIEF" + ext))
        return None, (f"style brief -> 04_Scripts_Code/STYLE_BRIEF{ext}: Claude turns it into 04_Scripts_Code/style.json"
                      f" (extends the nearest preset), then  doc.py <prj> style set style.json")
    sys.exit(f"style {src!r}: give a preset name, a .json style file, or a brief ({', '.join(BRIEF_EXT)})")


def available():
    out = []
    if os.path.isdir(STYLES_DIR):
        for f in sorted(os.listdir(STYLES_DIR)):
            if f.endswith(".json") and not f.startswith("_"):
                s = json.load(open(os.path.join(STYLES_DIR, f), encoding="utf-8"))
                out.append((f[:-5], s.get("label", ""), s.get("description", ""), s.get("extends")))
    return out


def gfx(P):
    """the graphics block for Remotion: the film's gfx (style + film.json), on top of the base style's; Vietnamese
    narration (voice.language "vi") swaps in gfx.fonts_vi so diacritics render."""
    import copy
    base = load(BASE).get("gfx", {}) if os.path.exists(path(BASE)) else {}
    top = copy.deepcopy(P.cfg.get("gfx", {}))
    g = _merge(drop_vi(base, top), top)
    vi = str(P.cfg.get("voice", {}).get("language", "")).lower().startswith("vi")
    if vi and g.get("fonts_vi"):
        g["fonts"] = _merge(g.get("fonts", {}), g["fonts_vi"])
    g.pop("fonts_vi", None)
    g["style"] = P.cfg.get("style") or "(none)"
    return g


ENGINE_PUBLIC = os.path.join(os.path.dirname(STYLES_DIR), "templates", "remotion", "public")
PUBLIC_DIRS = lambda: [ENGINE_PUBLIC]


def system_fonts():
    """family names of the fonts installed in Windows (machine + this user), lower case; empty off Windows."""
    if not hasattr(system_fonts, "cache"):
        names = set()
        try:
            import winreg
            for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                try:
                    k = winreg.OpenKey(hive, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts")
                except OSError:
                    continue
                for i in range(winreg.QueryInfoKey(k)[1]):
                    n = winreg.EnumValue(k, i)[0].split(" (")[0]            # "Georgia Bold Italic (TrueType)"
                    for part in n.split(" & "):                             # "Cambria & Cambria Math (TrueType)"
                        names.add(part.strip().lower())
        except ImportError:
            pass
        system_fonts.cache = names
    return system_fonts.cache


def installed(family):
    """True if a Windows font of this family is installed (or the machine is not Windows: cannot tell)."""
    names = system_fonts()
    fam = family.lower()
    return not names or any(n == fam or n.startswith(fam + " ") for n in names)


def sync_fonts(P, g):
    """make every font file the graphics name servable by Remotion (staticFile = the project's public/ folder):
    a file missing there is copied from the engine's templates/remotion/public, from next to the style file that named
    it, or from its full path. Returns (g for src/style.json, [warnings]); unfound files are left out (the family then
    falls back to an installed font of that name, else the fallback) and named in the warnings."""
    import copy, shutil
    pub = P.p("06_Graphics", "remotion", "public")
    g, warn = copy.deepcopy(g), []
    for name, f in (g.get("fonts") or {}).items():
        keep = []
        for x in f.get("files") or []:
            rel = x["file"].replace("\\", "/")
            if os.path.isabs(rel):
                rel = "fonts/" + os.path.basename(rel)
            dst = os.path.join(pub, *rel.split("/"))
            if not os.path.isfile(dst):
                cand = [x.get("src"), x["file"] if os.path.isabs(x["file"]) else None]
                cand += [os.path.join(d, *rel.split("/")) for d in PUBLIC_DIRS()] + [os.path.join(P.code, *rel.split("/"))]
                got = next((c for c in cand if c and os.path.isfile(c)), None)
                if got:
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(got, dst)
                    print(f"gfx: font {rel} -> 06_Graphics/remotion/public/{rel}")
            x.pop("src", None)
            if os.path.isfile(dst):
                keep.append(dict(x, file=rel))
            else:
                warn.append(f"font file {x['file']} ({name}: {f.get('family')}) not found: put it in templates/remotion/public/fonts"
                            f" or next to the style file; until then the graphics use "
                            + (f"the installed {f.get('family')}" if installed(f.get("family", "")) else f"the fallback ({f.get('fallback')})"))
        f["files"] = keep
        if not keep and f.get("family") and not installed(f["family"]):
            warn.append(f"font {f['family']} ({name}) has no file and is not installed in Windows: the graphics fall back to {f.get('fallback')}")
    return g, warn


def write_gfx(P):
    """06_Graphics/remotion/src/style.json from the film's style; only for Remotion copies that read it (src/style.js).
    Copies the style's font files into the project's public/ first (sync_fonts). Rewritten only when it changed, so the
    stills hash does not move for nothing. Returns True when written."""
    src = P.p("06_Graphics", "remotion", "src")
    if not os.path.exists(os.path.join(src, "style.js")):
        return False                          # films made before styles: their JSX keeps its own constants
    g, warn = sync_fonts(P, gfx(P))
    for w in dict.fromkeys(warn):
        print(f"  ! gfx: {w}")
    dst = os.path.join(src, "style.json")
    new = json.dumps(g, ensure_ascii=False, indent=1)
    if os.path.exists(dst) and open(dst, encoding="utf-8").read() == new:
        return False
    open(dst, "w", encoding="utf-8").write(new)
    return True


# ---------------------------------------------------------------- picture: grade curve, vignette + letterbox
def curve(g):
    """per-channel 256-entry curves (b, g, r) for render.grade: S-curve of strength `contrast`, blacks lifted by `lift`,
    `cool` tints blue (negative = warm), `warm` is the same tint the other way."""
    x = np.arange(256) / 255.0
    c, lift = g.get("contrast", 0.2), g.get("lift", 3)
    lut = np.clip(((1 - c) * x + c * x * x * (3 - 2 * x)) * 255 + lift, 0, 255)
    t = g.get("cool", 0.0) - g.get("warm", 0.0)
    return np.clip(lut * (1 + t), 0, 255), lut, np.clip(lut * (1 - t * 2 / 3), 0, 255)


def vignette(g, W, H):
    """multiplier (H, W) float32: 1 = untouched; the vignette darkens the corners, a letterbox (e.g. 2.39) blacks the bars."""
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - g.get("vignette", 0.22) * np.clip(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2 - 0.25, 0, 1.5) / 1.5
    lb = g.get("letterbox") or 0
    if lb and W / lb < H:
        bar = int(round((H - W / lb) / 2))
        v[:bar] = 0
        v[H - bar:] = 0
    return v.astype(np.float32)


# ---------------------------------------------------------------- house rules (lint, audio)
def check(P, overlays=None, music=None):
    """(summary, [warnings]) of the film against its style's rules. overlays: the overlays.json list; music: [(t_in, t_out)]."""
    R, warn, bits = P.cfg.get("rules", {}), [], []
    try:
        TL = P.timeline()
    except FileNotFoundError:
        return "no timeline yet", []
    minutes = TL["end"] / 60
    if overlays is not None and R.get("gfx_per_min"):
        lo, hi = R["gfx_per_min"]
        rate = len(overlays) / minutes if minutes else 0
        bits.append(f"{rate:.1f} gfx/min ({lo}-{hi})")
        if rate < lo - 0.05:
            warn.append(f"warning: {len(overlays)} graphics = {rate:.1f}/min, style wants {lo}-{hi} -> about {round(lo * minutes)}-{round(hi * minutes)}")
        elif rate > hi + 0.5:
            warn.append(f"warning: {rate:.1f} graphics/min is well above the style's {lo}-{hi}")
    if music is not None and R.get("music_coverage") is not None:
        speech = sum(l["end"] - l["start"] for l in TL["lines"]) or 1
        on = 0.0
        for l in TL["lines"]:
            t = l["start"]
            for a, b in sorted((max(l["start"], a), min(l["end"], b)) for a, b in music):
                if b > max(a, t):
                    on += b - max(a, t); t = b
        cov, want = on / speech, R["music_coverage"]
        bits.append(f"music {cov * 100:.0f}% (>= {want * 100:.0f}%)")
        if cov < want - 0.02:
            warn.append(f"warning: music under {cov * 100:.0f}% of the narration, style wants >= {want * 100:.0f}%")
    return f"{P.cfg.get('style') or '(no style)'}: " + (", ".join(bits) or "nothing to check yet"), warn


def show(P):
    """doc.py <prj> style: the film's style and the settings it ends up with."""
    name = P.cfg.get("style")
    print(f"style: {name or '(none: engine defaults)'}")
    if name:
        s = load(name, P.code)
        print(f"  {s.get('label', '')} - {s.get('description', '')}")
        if s.get("extends"):
            print(f"  extends {s['extends']}")
    C = P.cfg
    g = C["render"]["grade"]
    print(f"  grade     contrast {g.get('contrast', 0.2)}, lift {g.get('lift', 3)}, cool {g.get('cool', 0)}, warm {g.get('warm', 0)},"
          f" saturation {g.get('saturation')}, vignette {g.get('vignette')}, letterbox {g.get('letterbox') or 'off'}")
    e = C["edit"]
    print(f"  cuts      target {e['target']} s ({e['min']}-{e['max']}), fade {e.get('fade')}")
    t = C["timing"]
    print(f"  timing    gap_line {t['gap_line']}, gap_block {t['gap_block']}, act_card {t['act_card']}, end_text {t['end_text']}")
    print(f"  audio     lufs {C['audio']['lufs']}, duck {C['audio']['duck_db']} dB")
    print(f"  rules     {json.dumps(C.get('rules', {}), ensure_ascii=False)}")
    gf = gfx(P)
    print(f"  palette   {json.dumps(gf.get('palette', {}))}")
    print(f"  fonts     " + ", ".join(f"{k}={v.get('family')}" for k, v in gf.get("fonts", {}).items()))
    for k, v in (C.get("notes") or {}).items():
        print(f"  notes.{k}: {v}")


def run(P, args):
    sys.stdout.reconfigure(encoding="utf-8")
    if args[:1] == ["set"] and len(args) > 1:            # doc.py <prj> style set <preset | file.json | brief>
        src = args[1]
        if not os.path.isfile(src) and is_file(src):    # a file already in 04_Scripts_Code, e.g. style.json
            load(src, P.code)
            value, note = src, f"style file 04_Scripts_Code/{src}"
        else:
            value, note = adopt(src, P.code)
        print(note)
        if value is None:
            return
        args = ["set", value]
        cfg_p = os.path.join(P.code, "film.json")
        raw = json.load(open(cfg_p, encoding="utf-8"))
        raw["style"] = args[1]
        json.dump(raw, open(cfg_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"film.json: style = {args[1]}  (film.json keys still override the style; then: build, gfx stills --all, premiere)")
        return
    show(P)


def list_styles():
    sys.stdout.reconfigure(encoding="utf-8")
    for n, label, desc, ext in available():
        print(f"  {n:18} {label}{'  (extends ' + ext + ')' if ext else ''}\n  {'':18} {desc}")
