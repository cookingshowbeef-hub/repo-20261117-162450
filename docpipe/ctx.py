"""Project context shared by every step: paths, film.json, the project's own spec modules, API keys.

A project is a folder with 01_Voice .. 07_Audio and 04_Scripts_Code/film.json. Steps read and write only inside it.
DOC_OUT (env) redirects the 05_Renders outputs (timeline, overlays, edit, renders) to another folder, for dry runs.
"""
import importlib.util, json, os, re, sys

ENGINE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(os.path.dirname(ENGINE_ROOT), "02. Công cụ Авто & Engine - Python Tools")
DOC_ROOT = os.path.dirname(os.path.dirname(ENGINE_ROOT))            # ...\documentary when the engine sits in its usual tree
SETTINGS_FILE = os.environ.get("DOCPIPE_SETTINGS") or os.path.join(os.path.expanduser("~"), ".docpipe", "settings.env")


def setting(name, default=None):
    """Machine paths (projects folder, music library, ...): the environment first, then SETTINGS_FILE (NAME=value lines)."""
    if os.environ.get(name):
        return os.environ[name]
    if os.path.exists(SETTINGS_FILE):
        for line in open(SETTINGS_FILE, encoding="utf-8"):
            k, sep, v = line.strip().partition("=")
            if sep and k.strip() == name and not k.lstrip().startswith("#") and v.strip():
                return v.strip().strip('"')
    return default


def _first_dir(*paths):
    return next((p for p in paths if p and os.path.isdir(p)), paths[-1])


PROJECTS = setting("DOCPIPE_PROJECTS") or _first_dir(os.path.join(DOC_ROOT, "04. Dự án đang Edit - Active Projects"),
                                                     os.path.join(ENGINE_ROOT, "projects"))
BGM_VAULT = setting("DOCPIPE_BGM") or os.path.join(DOC_ROOT, "02. Giọng đọc & Âm thanh - Voice & Audio", "03. Nhạc nền Phim tài liệu - BGM Tracks")
AUDIO_LIBRARY = setting("DOCPIPE_LIBRARY", r"Y:\Data Footage\Discovery\Kien")      # holds BGM_NoCopyright and SFX_Vault

DEFAULTS = {
    "title": "UNTITLED",
    "output": "film_1080p.mp4",
    "narration_md": "Narration.md",
    "template": "script_template.md",
    "sections": [],                       # tags of the narration's "## " sections, in order (c0, a1, ...)
    "acts_regex": r"COLD OPEN|ACT \w+|CLOSING",
    "no_card_acts": ["COLD OPEN"],
    "voice": {"id": "elevenlabs_lnieQLGTodpbhjpZtg1k", "speed": 0.95, "language": "en", "whisper": "medium", "threads": 3},
    "timing": {"gap_line": 0.75, "gap_block": 1.8, "act_card": 5.5, "end_text": 20.0, "hold_before": {}, "hold_after": {},
               "next_act_lead": 5.0},
    "edit": {"target": 3.6, "max": 5.0, "min": 2.5, "clip_cap": 2, "photo_cap": 3, "clip_gap": 60.0,
             "full_kinds": ["map"], "plate": "111418", "title_black": True, "merge_gap": 2.5, "fade": 0.45,
             "nasa_sequences": []},
    "overlay": {"full_hold": 6.0, "aliases": {}},
    "render": {"width": 1920, "height": 1080, "fps": 30, "crf": 17, "fade_frames": 15,
               "grade": {"cool": 0.03, "saturation": 0.9, "vignette": 0.22}},
    "audio": {"library": AUDIO_LIBRARY, "lufs": -14, "duck_db": 6, "sfx_duck_db": 4, "voice_rms": -20},
    "credits": {"intro": "Narration: AI voice. Footage and photographs are licensed stock, archival or public-domain material; no interviews were filmed.",
                "music": "Kevin MacLeod (incompetech.com)", "music_licence": "Creative Commons: By Attribution 4.0 License. http://creativecommons.org/licenses/by/4.0/",
                "extra": []},
    "style": None,                        # styles/<name>.json layered between these defaults and film.json (docpipe/style.py)
    "gfx": {},                            # Remotion palette/fonts/motion (from the style; film.json may override)
    "rules": {"gfx_per_min": [2.5, 3.0], "music_coverage": 0.85, "music_under_voice_db": 15, "suno_cues": [4, 6]},
    "notes": {},
    "commons_user_agent": "DocResearch/1.0 (documentary research script) python-requests",
}


def _merge(a, b):
    out = dict(a)
    for k, v in b.items():
        out[k] = _merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


class Project:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.code = os.path.join(self.root, "04_Scripts_Code")
        cfg = os.path.join(self.code, "film.json")
        if not os.path.exists(cfg):
            sys.exit(f"no film.json in {self.code}")
        raw = json.load(open(cfg, encoding="utf-8"))
        from . import style                        # DEFAULTS <- styles/<film.json "style">.json <- film.json
        self.cfg = _merge(_merge(DEFAULTS, style.layer(raw.get("style"), self.code)), raw)
        self.renders = os.environ.get("DOC_OUT") or os.path.join(self.root, "05_Renders")
        os.makedirs(self.renders, exist_ok=True)
        if self.code not in sys.path:
            sys.path.insert(0, self.code)

    # ------------------------------------------------------------ paths and json
    def p(self, *parts):
        return os.path.join(self.root, *parts)

    def out(self, name):
        return os.path.join(self.renders, name)

    def load(self, *parts, default=None):
        path = self.p(*parts)
        if default is not None and not os.path.exists(path):
            return default
        return json.load(open(path, encoding="utf-8"))

    def load_out(self, name):
        return json.load(open(self.out(name), encoding="utf-8"))

    def save_out(self, name, obj):
        json.dump(obj, open(self.out(name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    def spec(self, name, required=True):
        """the project's own module in 04_Scripts_Code (overlay_spec, audio_spec, pools, hud), or None."""
        path = os.path.join(self.code, name + ".py")
        if not os.path.exists(path):
            if required:
                sys.exit(f"missing {name}.py in {self.code}")
            return None
        s = importlib.util.spec_from_file_location(name, path)
        m = importlib.util.module_from_spec(s)
        sys.modules[name] = m
        s.loader.exec_module(m)
        return m

    def template(self):
        """script_template.md up to the production notes, without <!-- comments -->."""
        s = open(os.path.join(self.code, self.cfg["template"]), encoding="utf-8").read().split("## PRODUCTION NOTES")[0]
        return re.sub(r"<!--.*?-->", "", s, flags=re.S)

    # ------------------------------------------------------------ narration
    def timeline(self):
        return self.load_out("timeline.json")

    def local(self, ref):
        """lk:<id> -> absolute path of a clip/image on this machine (02_B-Roll/local/index.json: {id: {"path": ...}} or {id: path}).
        For footage libraries whose paths hold spaces or Vietnamese, which a file: code cannot carry."""
        if not hasattr(self, "_local"):
            self._local = self.load("02_B-Roll", "local", "index.json", default={})
        v = self._local.get(ref)
        if v is None:
            sys.exit(f"lk:{ref} is not in 02_B-Roll/local/index.json")
        return v["path"] if isinstance(v, dict) else v

    def words(self, line_id):
        return json.load(open(self.p("01_Voice", "lines", f"{line_id}.words.json"), encoding="utf-8"))


VO = re.compile(r"\{\{((?:[a-z]\d+_\d\d ?)+)\}\}")         # {{c0_01 c0_02}} = one V.O. block


KEYS_FILE = os.environ.get("DOCPIPE_KEYS") or os.path.join(os.path.expanduser("~"), ".docpipe", "keys.env")


def key(name):
    """API keys: the environment first, then KEYS_FILE (NAME=value lines, by default ~/.docpipe/keys.env); never printed."""
    if os.environ.get(name):
        return os.environ[name]
    if os.path.exists(KEYS_FILE):
        for line in open(KEYS_FILE, encoding="utf-8"):
            k, sep, v = line.strip().partition("=")
            if sep and k.strip() == name and not k.lstrip().startswith("#") and v.strip():
                return v.strip().strip('"').strip("'")
    sys.exit(f"no key for {name}: add {name}=... to {KEYS_FILE} (or set it as an environment variable)")


tc = lambda t: "%d:%04.1f" % (t // 60, t % 60)
