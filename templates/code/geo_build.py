"""Map geometry for the film's map graphics -> ../06_Graphics/remotion/public/geo/<map>.json  (EXAMPLE from POLE OF COLD: edit P, the routes and MAPS for your film)

Natural Earth (public domain) countries, admin-1 regions and rivers, projected with Lambert azimuthal equal-area
(so "Sakha laid over Western Europe" compares true areas), simplified, and scaled into a 1920x1080 frame.
Each map: {"kmpp", "land": [svg d], "region": d, "rivers": [d], "pts": {name: [x, y]}, "lines": {name: [[x, y], ...]}}.
Coordinates outside the frame are kept (the camera in the graphic can pan); the land is clipped to a generous box.
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
GEO = os.path.normpath(os.path.join(HERE, "..", "..", "..", "06. Kịch bản & Công cụ Code - Scripts & Engine", "03. Doc Pipeline - Quy trình Phim tài liệu", "data", "naturalearth"))   # shared (normpath: the raw ..\ path passes MAX_PATH) Natural Earth data
OUT = os.path.normpath(os.path.join(HERE, "..", "06_Graphics", "remotion", "public", "geo"))
R = 6371.0
L = lambda f: json.load(open(os.path.join(GEO, f), encoding="utf-8"))
COUNTRIES = L("ne_50m_admin_0_countries.geojson")["features"]
ADMIN1 = L("ne_50m_admin_1_states_provinces_lakes.geojson")["features"]
RIVERS = L("ne_10m_rivers_lake_centerlines.geojson")["features"]
SAKHA = next(f for f in ADMIN1 if f["properties"].get("name") == "Sakha (Yakutia)")

P = {   # places (lon, lat)
    "Oymyakon": (142.79, 63.46), "Tomtor": (143.24, 63.25), "Yakutsk": (129.73, 62.03), "Magadan": (150.80, 59.56),
    "Verkhoyansk": (133.39, 67.55), "Batagaika": (134.77, 67.58), "Lake Baikal": (108.0, 53.5), "Ust-Nera": (143.24, 64.57),
    "Nakhodka": (132.87, 42.82), "Vanino": (140.25, 49.08), "Susuman": (148.15, 62.78), "Moscow": (37.62, 55.75),
    "Klinck": (-40.47, 72.30), "Khandyga": (135.58, 62.66),
}
KOLYMA_ROUTE = [(129.73, 62.03), (129.95, 61.95), (131.5, 62.3), (135.58, 62.66), (138.0, 63.0), (140.5, 63.2), (142.2, 63.35),
                (143.24, 63.25), (143.6, 63.9), (143.24, 64.57), (145.5, 64.1), (148.15, 62.78), (149.6, 62.52), (150.7, 62.33),
                (151.6, 61.3), (151.8, 60.85), (150.9, 60.1), (150.80, 59.56)]          # Yakutsk -> Khandyga -> Tomtor/Oymyakon -> Ust-Nera -> Susuman -> Magadan
SEA_ROUTE = [(132.87, 42.82), (134.5, 44.5), (138.2, 47.0), (140.25, 49.08), (141.2, 52.5), (143.5, 55.0), (148.0, 57.5), (150.80, 59.56)]
INLAND = [(150.80, 59.56), (150.9, 60.1), (151.8, 60.85), (150.7, 62.33), (148.15, 62.78)]
MIGRATION = [(108.0, 53.5), (106.5, 55.5), (106.1, 56.8), (108.1, 57.8), (112.0, 59.3), (116.0, 60.0), (120.4, 60.37), (125.5, 61.2), (129.73, 62.03)]


def laea(lon0, lat0):
    l0, p0 = math.radians(lon0), math.radians(lat0)

    def f(lon, lat):
        l, p = math.radians(lon), math.radians(lat)
        c = 1 + math.sin(p0) * math.sin(p) + math.cos(p0) * math.cos(p) * math.cos(l - l0)
        k = math.sqrt(2 / max(c, 1e-9))
        return R * k * math.cos(p) * math.sin(l - l0), R * k * (math.cos(p0) * math.sin(p) - math.sin(p0) * math.cos(p) * math.cos(l - l0))
    return f


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy)
    if n < 1e-9:                                   # closed ring: start == end, use distance to that point
        d = [math.hypot(x - x0, y - y0) for x, y in pts[1:-1]]
    else:
        d = [abs(dy * x - dx * y + x1 * y0 - y1 * x0) / n for x, y in pts[1:-1]]
    i = max(range(len(d)), key=d.__getitem__)
    if d[i] > eps:
        return rdp(pts[:i + 2], eps)[:-1] + rdp(pts[i + 1:], eps)
    return [pts[0], pts[-1]]


def rings(geom):
    t, c = geom["type"], geom["coordinates"]
    if t == "Polygon":
        return c
    if t == "MultiPolygon":
        return [r for poly in c for r in poly]
    if t == "LineString":
        return [c]
    if t == "MultiLineString":
        return c
    return []


class Map:
    def __init__(self, lon0, lat0, kmpp, box):
        self.f, self.kmpp, self.box = laea(lon0, lat0), kmpp, box      # box: lon/lat window to keep land from

    def xy(self, lon, lat):
        X, Y = self.f(lon, lat)
        return round(960 + X / self.kmpp, 1), round(540 - Y / self.kmpp, 1)

    def inbox(self, lon, lat):
        a, b, c, d = self.box
        return a <= lon <= c and b <= lat <= d

    def path(self, geom, closed=True, eps=1.2, keep_all=False):
        out = []
        for r in rings(geom):
            if not keep_all and not any(self.inbox(lo, la) for lo, la in r):
                continue
            pts = rdp([self.xy(lo, la) for lo, la in r], eps)
            if len(pts) < 2:
                continue
            out.append("M" + "L".join(f"{x},{y}" for x, y in pts) + ("Z" if closed else ""))
        return " ".join(out)

    def line(self, pts):
        return [list(self.xy(*p)) for p in pts]


def build(name, lon0, lat0, kmpp, box, region=True, rivers=(), pts=(), lines=None, extra=None):
    m = Map(lon0, lat0, kmpp, box)
    land = [m.path(c["geometry"]) for c in COUNTRIES]
    out = dict(kmpp=kmpp, land=[d for d in land if d], pts={p: m.xy(*P[p]) for p in pts},
               lines={k: m.line(v) for k, v in (lines or {}).items()})
    if region:
        out["region"] = m.path(SAKHA["geometry"], keep_all=True)
    out["rivers"] = [m.path(f["geometry"], closed=False, eps=0.8) for f in RIVERS if (f["properties"].get("name") or "") in rivers]
    out["rivers"] = [d for d in out["rivers"] if d]
    if extra:
        out.update(extra(m))
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, name + ".json"), "w"), separators=(",", ":"))
    print(f"{name:14s} {os.path.getsize(os.path.join(OUT, name + '.json')) // 1024:4d} KB  pts {list(out['pts'])}")


def europe_compare(m):
    """Sakha, projected on its own centre, laid over Western Europe at the same scale (equal-area both ways)."""
    fs = laea(128, 66)
    cx, cy = m.xy(9, 50)
    d = []
    for r in rings(SAKHA["geometry"]):
        pts = rdp([(round(cx + fs(lo, la)[0] / m.kmpp, 1), round(cy - fs(lo, la)[1] / m.kmpp, 1)) for lo, la in r], 1.2)
        if len(pts) > 2:
            d.append("M" + "L".join(f"{x},{y}" for x, y in pts) + "Z")
    return {"overlay": " ".join(d)}


def main():
    import sys; sys.setrecursionlimit(20000)
    RIV = ("Lena", "Aldan", "Vilyuy", "Yana", "Indigirka", "Kolyma")
    build("zoom", 128, 62, 2.2, (60, 35, 200, 82), rivers=RIV, pts=("Oymyakon", "Yakutsk", "Magadan", "Moscow"), lines={"road": KOLYMA_ROUTE})
    build("europe", 9, 50, 2.6, (-25, 30, 45, 72), region=False, pts=(), extra=europe_compare)
    build("kolyma", 140, 62, 1.15, (110, 50, 175, 75), rivers=RIV, pts=("Yakutsk", "Oymyakon", "Tomtor", "Magadan", "Ust-Nera", "Susuman", "Khandyga"),
          lines={"road": KOLYMA_ROUTE, "to_oymyakon": KOLYMA_ROUTE[:8]})
    build("sea", 142, 53, 1.45, (115, 35, 175, 70), region=False, pts=("Nakhodka", "Vanino", "Magadan", "Susuman"), lines={"sea": SEA_ROUTE, "inland": INLAND})
    build("migration", 120, 59, 1.6, (90, 45, 160, 75), rivers=RIV, pts=("Lake Baikal", "Yakutsk"), lines={"path": MIGRATION})
    build("rivals", 138, 65.5, 0.75, (115, 55, 160, 75), rivers=RIV, pts=("Oymyakon", "Verkhoyansk", "Yakutsk", "Batagaika"),
          lines={"span": [P["Oymyakon"], P["Verkhoyansk"]]})
    build("siberian_high", 105, 55, 4.2, (40, 10, 180, 85), region=False, pts=("Lake Baikal", "Oymyakon"))
    build("greenland", -42, 72, 1.6, (-75, 55, -10, 85), region=False, pts=("Klinck",))
    build("batagaika", 138, 65.5, 0.95, (115, 55, 160, 75), rivers=RIV, pts=("Batagaika", "Oymyakon", "Verkhoyansk", "Yakutsk"))


if __name__ == "__main__":
    main()
