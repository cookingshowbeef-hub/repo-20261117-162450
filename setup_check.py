"""Check that this machine can run the documentary pipeline. Prints OK / MISSING per item; never prints key values.

  python setup_check.py
"""
import importlib, os, shutil, subprocess, sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from docpipe import ctx  # noqa: E402  (paths come from ~/.docpipe/settings.env, see SETUP_CLAUDE.md)
bad = []


def row(ok, what, fix=""):
    print(("  OK       " if ok else "  MISSING  ") + what + ("" if ok or not fix else f"\n             -> {fix}"))
    if not ok:
        bad.append(what)


print("Folders (settings: " + ctx.SETTINGS_FILE + ")")
row(os.path.isdir(ctx.PROJECTS), f"projects folder {ctx.PROJECTS}", "create it, or set DOCPIPE_PROJECTS=<folder> in settings.env")
row(os.path.isfile(os.path.join(ctx.BGM_VAULT, "bgm_vault_catalog.json")), f"BGM library {ctx.BGM_VAULT} (music lib)",
    "optional: set DOCPIPE_BGM=<folder with bgm_vault_catalog.json> in settings.env; Suno cues work without it")

print("Python packages")
for mod, pip in [("numpy", "numpy"), ("cv2", "opencv-python"), ("requests", "requests"), ("PIL", "pillow"), ("scipy", "scipy"),
                 ("soundfile", "soundfile"), ("faster_whisper", "faster-whisper")]:
    try:
        importlib.import_module(mod)
        row(True, pip)
    except Exception:
        row(False, pip, "pip install -r requirements.txt")
row(sys.version_info >= (3, 10), f"Python {sys.version.split()[0]} (3.10+)", "install Python 3.11")

print("Programs")
for exe in ("ffmpeg", "ffprobe"):
    row(bool(shutil.which(exe)), exe, "install ffmpeg (gyan.dev full build) and put its bin on PATH")
pw = os.path.join(os.path.expanduser("~"), "AppData", "Local", "ms-playwright-go", "1.57.0", "node.exe")
node = ctx.setting("REMOTION_NODE") or (pw if os.path.exists(pw) else None) or shutil.which("node")
row(bool(node), "node (Remotion graphics)", "install Node.js 20+ LTS, or set REMOTION_NODE to a node.exe")
sys.path.insert(0, HERE)
from docpipe.newproject import NODE_MODULES as nm  # noqa: E402  (same lookup the engine uses)
row(bool(nm) and os.path.isdir(os.path.join(nm, "remotion")), "Remotion node_modules", f'cd "{os.path.join(HERE, "templates", "remotion")}" && npm install')

print("API keys (environment, else ~/.docpipe/keys.env; values never shown)")
for k, use in [("AI33_API_KEY", "voice"), ("PEXELS_API_KEY", "b-roll"), ("PIXABAY_API_KEY", "b-roll"), ("FREESOUND_API_KEY", "sound effects")]:
    try:
        v = None
        try:
            v = ctx.key(k)
        except SystemExit:
            pass
        row(bool(v), f"{k} ({use})", f"ask the user for it; add {k}=... to {ctx.KEYS_FILE}")
    except Exception:
        row(False, f"{k} ({use})", f"ask the user for it; add {k}=... to {ctx.KEYS_FILE}")

print("Libraries and Resolve")
row(os.path.isdir(os.path.join(ctx.AUDIO_LIBRARY, "SFX_Vault")), f"audio library {ctx.AUDIO_LIBRARY} (BGM_NoCopyright + SFX_Vault)",
    "optional: set DOCPIPE_LIBRARY=<folder> in settings.env; without it use Suno music + Freesound")
lut = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\LUT"
row(os.path.isdir(lut), "DaVinci Resolve installed (LUT folder)", "install DaVinci Resolve 21.0.x (free is fine); do not update to 21.1+")
mcp = ctx.setting("RESOLVE_MCP_DIR", os.path.join(os.path.expanduser("~"), "davinci-resolve-mcp"))
row(os.path.isdir(mcp), "davinci-resolve-mcp (optional: push/pull)", "optional; see SETUP_CLAUDE.md step 6")
try:
    gpu = subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True, timeout=10).stdout.strip()
except Exception:
    gpu = ""
row(bool(gpu), "NVIDIA GPU (" + (gpu.splitlines()[0][:50] if gpu else "none") + ")", "optional: word timings run on CPU, slower")

print("\n" + ("All set." if not bad else f"{len(bad)} item(s) missing (optional ones can stay missing)."))
