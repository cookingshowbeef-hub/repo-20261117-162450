"""Edit styles: one JSON preset per look in ENGINE/styles/<name>.json, chosen per film with film.json "style": "<name>".

Settings are layered:  ctx.DEFAULTS  <-  styles/<name>.json (after its "extends" chain)  <-  film.json.
So a style sets the film-wide look (grade, letterbox, cut length, card timing, ducking, graphics palette/fonts/motion,
house rules such as graphics per minute and music coverage), and film.json can still override any single key.
A film.json without "style" gets ctx.DEFAULTS alone (films made before styles existed are unchanged).

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


def path(name):
    return os.path.join(STYLES_DIR, f"{name}.json")


def load(name, _seen=()):
    """the preset with its "extends" chain resolved (meta keys kept from the preset itself)."""
    p = path(name)
    if not os.path.exists(p):
        sys.exit(f"style {name!r} not found in {STYLES_DIR} (have: {', '.join(n for n, *_ in available()) or 'none'})")
    if name in _seen:
        sys.exit(f"style {name!r}: extends loop ({' -> '.join(_seen + (name,))})")
    s = json.load(open(p, encoding="utf-8"))
    if s.get("extends"):
        base = {k: v for k, v in load(s["extends"], _seen + (name,)).items() if k not in META}
        s = _merge(base, s)
    s["name"] = name
    return s


def layer(name):
    """the part of a preset that merges into the film's settings."""
    return {k: v for k, v in load(name).items() if k not in META} if name else {}


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
    base = load(BASE).get("gfx", {}) if os.path.exists(path(BASE)) else {}
    g = _merge(base, P.cfg.get("gfx", {}))
    if str(P.cfg.get("voice", {}).get("language", "")).lower().startswith("vi") and g.get("fonts_vi"):
        g["fonts"] = _merge(g.get("fonts", {}), g["fonts_vi"])
    g.pop("fonts_vi", None)
    g["style"] = P.cfg.get("style") or "(none)"
    return g


def write_gfx(P):
    """06_Graphics/remotion/src/style.json from the film's style; only for Remotion copies that read it (src/style.js).
    Rewritten only when it changed, so the stills hash does not move for nothing. Returns True when written."""
    src = P.p("06_Graphics", "remotion", "src")
    if not os.path.exists(os.path.join(src, "style.js")):
        return False                          # films made before styles: their JSX keeps its own constants
    dst = os.path.join(src, "style.json")
    new = json.dumps(gfx(P), ensure_ascii=False, indent=1)
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
        s = load(name)
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
    if args[:1] == ["set"] and len(args) > 1:            # doc.py <prj> style set <name>: write it into film.json
        load(args[1])
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
