"""Compact contact sheets: first N candidates per query (Pexels first, then Pixabay) -> candidates/<set>/mini_N.jpg, 8 cols x 6 rows of 240x135.

  python tools/mini_sheets.py "<project>" intro,school 4
"""
import json, os, sys
import numpy as np, cv2

root, sets, N = sys.argv[1], sys.argv[2].split(","), int(sys.argv[3]) if len(sys.argv) > 3 else 8
for s in sets:
    d = os.path.join(root, "02_B-Roll", "candidates", s)
    C = json.load(open(os.path.join(d, "candidates.json"), encoding="utf-8"))
    byq = {}
    for cid, c in C.items():
        byq.setdefault(c["q"], []).append(cid)
    order = []
    for q, ids in byq.items():
        px = [i for i in ids if i.startswith("px")]; pb = [i for i in ids if i.startswith("pb")]
        mix = [x for pair in zip(px, pb) for x in pair] + px[len(pb):] + pb[len(px):]
        order += mix[:N]
    tiles = []
    for cid in order:
        p = os.path.join(d, cid.replace(":", "_") + ".jpg")
        im = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR) if os.path.exists(p) else None
        if im is None:
            continue
        im = np.pad(cv2.resize(im, (240, 135)), ((0, 18), (0, 0), (0, 0)))
        cv2.putText(im, f"{cid} {C[cid]['q'][:16]}", (2, 148), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (0, 255, 255), 1, cv2.LINE_AA)
        tiles.append(im)
    per = 48
    for k in range(0, len(tiles), per):
        part = tiles[k:k + per]; part += [np.zeros_like(tiles[0])] * (-len(part) % 8)
        cv2.imencode(".jpg", np.vstack([np.hstack(part[i:i + 8]) for i in range(0, len(part), 8)]), [cv2.IMWRITE_JPEG_QUALITY, 80])[1].tofile(
            os.path.join(d, f"mini_{k // per + 1}.jpg"))
    print(s, len(tiles), "tiles,", -(-len(tiles) // per), "sheets")
