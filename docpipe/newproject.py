"""New project folder from templates/:

  python doc.py new "<NN. Tên phim (xx Phút) - slug>" "FILM TITLE" [--script <file>] [--style <preset | style.json | brief>]

--script: the user's narration. A .md/.txt goes in as 04_Scripts_Code/Narration.md (Claude still checks the engine format);
          any other file (.docx, .pdf ...) is kept as SCRIPT_SOURCE.<ext> for Claude to turn into Narration.md.
--style:  a preset name (styles/), the user's own .json style file (-> 04_Scripts_Code/style.json), or a brief
          (.md/.txt/.docx/.pdf/image -> STYLE_BRIEF.<ext>, turned into style.json by Claude). Without it: netflix-cold.
A bare third argument is taken as --style (older usage).
"""
import json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(HERE, "templates")
# shared Remotion node_modules: $DOC_NODE_MODULES, else templates/remotion/node_modules (npm install there once), else the Amazon project's
NODE_MODULES = next((p for p in (os.environ.get("DOC_NODE_MODULES"), os.path.join(TPL, "remotion", "node_modules"),
                                 os.path.join(os.path.dirname(os.path.dirname(HERE)), "04. Dự án đang Edit - Active Projects",
                                              "01. Bí mật Rừng Amazon (25 Phút 4K) - amazon_secrets_4k", "motion_v", "remotion", "node_modules"))
                     if p and os.path.isdir(p)), "")
DIRS = ["01_Voice/lines", "02_B-Roll/candidates", "03_Images/commons", "04_Scripts_Code", "05_Renders/tests", "06_Graphics/render/ov",
        "06_Graphics/remotion/public/geo", "07_Audio/freesound"]


USAGE = 'usage: python doc.py new "<NN. Tên phim (xx Phút) - slug>" "FILM TITLE" [--script <file>] [--style <preset | file>]'


def parse(args):
    pos, opt, it = [], {}, iter(args)
    for a in it:
        if a in ("--style", "--script"):
            opt[a[2:]] = next(it, None) or sys.exit(USAGE)
        else:
            pos.append(a)
    if len(pos) > 2:
        opt.setdefault("style", pos[2])
    if len(pos) < 2:
        sys.exit(USAGE)
    return pos[0], pos[1], opt.get("style") or "netflix-cold", opt.get("script")


def create(active, *args):
    name, title, style_src, script = parse(args)
    from .style import load as load_style, adopt, BRIEF_EXT, _read
    if os.path.isfile(style_src):              # a file: check it can be used before making any folder
        if not style_src.lower().endswith((".json",) + BRIEF_EXT):
            sys.exit(f"--style {style_src}: give a preset name, a .json style file, or a brief ({', '.join(BRIEF_EXT)})")
        if style_src.lower().endswith(".json"):
            s = _read(style_src, style_src)        # broken JSON or a missing "extends" preset: stop now
            if s.get("extends"):
                load_style(s["extends"], os.path.dirname(os.path.abspath(style_src)))
    else:
        load_style(style_src)                  # unknown preset: stop now
    if script and not os.path.isfile(script):
        sys.exit(f"--script {script}: file not found")
    root = os.path.join(active, name)
    if os.path.exists(root):
        sys.exit(f"already exists: {root}")
    for d in DIRS:
        os.makedirs(os.path.join(root, d))
    code = os.path.join(root, "04_Scripts_Code")
    for f in os.listdir(os.path.join(TPL, "code")):
        dst = "pools_example.py" if f == "pools.py" else f
        shutil.copy2(os.path.join(TPL, "code", f), os.path.join(code, dst))
    style_val, style_note = adopt(style_src, code)
    style_val = style_val or "netflix-cold"        # a brief: default until Claude writes style.json
    script_note = "no script yet: write 04_Scripts_Code/Narration.md"
    if script:
        ext = os.path.splitext(script)[1].lower()
        if ext in (".md", ".txt"):
            shutil.copy2(script, os.path.join(code, "Narration.md"))
            script_note = f"script {os.path.basename(script)} -> 04_Scripts_Code/Narration.md (check the engine format: one line per sentence, '## ' per section)"
        else:
            shutil.copy2(script, os.path.join(code, "SCRIPT_SOURCE" + ext))
            script_note = f"script {os.path.basename(script)} -> 04_Scripts_Code/SCRIPT_SOURCE{ext}: Claude turns it into Narration.md"
    slug = name.rsplit(" - ", 1)[-1] if " - " in name else re.sub(r"\W+", "_", title.lower())
    cfg_p = os.path.join(code, "film.json")
    s = (open(cfg_p, encoding="utf-8").read().replace('"FILM TITLE"', json.dumps(title)).replace('"film_1080p.mp4"', json.dumps(f"{slug}_1080p.mp4"))
         .replace('"style": "netflix-cold"', json.dumps({"style": style_val})[1:-1]))
    open(cfg_p, "w", encoding="utf-8").write(s)
    for f in ("script_template.md", "overlay_spec.py") + (() if script else ("Narration.md",)):
        p = os.path.join(code, f)
        s = open(p, encoding="utf-8").read()
        open(p, "w", encoding="utf-8").write(s.replace("FILM TITLE", title))
    open(os.path.join(code, "FACT_CHECK.md"), "w", encoding="utf-8").write(
        f"# {title} — fact check\n\n| Claim (line) | Source | Status |\n|---|---|---|\n")
    rem = os.path.join(root, "06_Graphics", "remotion")
    shutil.copytree(os.path.join(TPL, "remotion"), rem, dirs_exist_ok=True)
    if not NODE_MODULES:
        print("  ! no Remotion node_modules: run  npm install  in templates/remotion  (or set DOC_NODE_MODULES), then make this project again")
    else:
        subprocess.run(["cmd", "/c", "mklink", "/J", os.path.join(rem, "node_modules"), NODE_MODULES], check=True, capture_output=True)
    from .ctx import Project
    from .style import write_gfx
    write_gfx(Project(root))                   # src/style.json for the Remotion graphics
    print(f"new project: {root}\n  style: {style_note}  (film.json style = {style_val}; change: doc.py <prj> style set <preset | file>)"
          f"\n  {script_note}\n  next: python doc.py \"{name.split('.')[0]}\" voice")
