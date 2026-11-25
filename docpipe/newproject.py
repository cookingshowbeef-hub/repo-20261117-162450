"""New project folder from templates/: python doc.py new "<NN. Tên phim (xx Phút) - slug>" "FILM TITLE" [style] """
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


def create(active, name=None, title=None, style_name="netflix-cold"):
    if not name or not title:
        sys.exit('usage: python doc.py new "<NN. Tên phim (xx Phút) - slug>" "FILM TITLE"')
    from .style import load as load_style
    load_style(style_name)                     # unknown style: stop before making any folder
    root = os.path.join(active, name)
    if os.path.exists(root):
        sys.exit(f"already exists: {root}")
    for d in DIRS:
        os.makedirs(os.path.join(root, d))
    code = os.path.join(root, "04_Scripts_Code")
    for f in os.listdir(os.path.join(TPL, "code")):
        dst = "pools_example.py" if f == "pools.py" else f
        shutil.copy2(os.path.join(TPL, "code", f), os.path.join(code, dst))
    slug = name.rsplit(" - ", 1)[-1] if " - " in name else re.sub(r"\W+", "_", title.lower())
    cfg_p = os.path.join(code, "film.json")
    s = (open(cfg_p, encoding="utf-8").read().replace('"FILM TITLE"', json.dumps(title)).replace('"film_1080p.mp4"', json.dumps(f"{slug}_1080p.mp4"))
         .replace('"style": "netflix-cold"', json.dumps({"style": style_name})[1:-1]))
    open(cfg_p, "w", encoding="utf-8").write(s)
    for f in ("script_template.md", "Narration.md", "overlay_spec.py"):
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
    print(f"new project: {root}  (style {style_name}; change: doc.py <prj> style set <name>)\n  next: write 04_Scripts_Code/Narration.md, then  python doc.py \"{name.split('.')[0]}\" voice")
