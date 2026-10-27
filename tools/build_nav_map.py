"""Build the 3D map data for the "Fly to Klinik Nissa" navigation video.

Every road, building footprint, park, traffic light and landmark in the video comes
from OpenStreetMap (© OpenStreetMap contributors, ODbL). The driving route comes from
the OSRM demo router, which itself runs on OpenStreetMap. Nothing on the map is drawn by hand.

    python3 tools/build_nav_map.py            # downloads into tools/.osm-cache/ (git-ignored)

Output: fly-to-clinic/assets/map-data.js  (window.MAP = {...}, metres, x = east, z = south)
"""
import json
import math
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "tools" / ".osm-cache"
OUT = ROOT / "fly-to-clinic" / "assets" / "map-data.js"
UA = {"User-Agent": "klinik-nissa-nav-video/1.0 (map build script)"}

# OSM tiles (main API, bbox = lon_min,lat_min,lon_max,lat_max) and the route endpoints.
TILES = ["101.778,2.805,101.805,2.840", "101.805,2.805,101.815,2.840"]
START = (2.83305, 101.79775)  # Plaza Tol Nilai exit lanes (OSM node 36365909)
END = (2.81785, 101.79341)  # midpoint of Jalan BBN 1/3C (OSM way, Pusat Bandar Putra Point)

# Origin of the local metric frame (roughly the centre of the route).
LAT0, LON0 = 2.8252, 101.7967
KX = 111320 * math.cos(math.radians(LAT0))
KY = 110574


def fetch(name, url):
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / name
    if not f.exists():
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
            f.write_bytes(r.read())
    return json.loads(f.read_text())


def xz(lat, lon):
    return ((lon - LON0) * KX, -(lat - LAT0) * KY)


def r1(v):
    return round(v, 1)


def flat(pts):
    return [r1(c) for p in pts for c in p]


def centroid(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def inside(p, poly):
    x, y = p
    c = False
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


# ------------------------------------------------------------------ load OSM
nodes, ways = {}, {}
for i, bbox in enumerate(TILES):
    d = fetch(f"tile{i}.json", f"https://api.openstreetmap.org/api/0.6/map.json?bbox={bbox}")
    for e in d["elements"]:
        if e["type"] == "node":
            nodes[e["id"]] = e
        elif e["type"] == "way":
            ways[e["id"]] = e


def way_pts(w):
    return [xz(nodes[n]["lat"], nodes[n]["lon"]) for n in w["nodes"] if n in nodes]


# ------------------------------------------------------------------ route
osrm = fetch(
    "route.json",
    "https://router.project-osrm.org/route/v1/driving/"
    f"{START[1]},{START[0]};{END[1]},{END[0]}?steps=true&geometries=geojson&overview=full",
)
route_ll = osrm["routes"][0]["geometry"]["coordinates"]
raw = [xz(lat, lon) for lon, lat in route_ll]
cum = [0.0]
for a, b in zip(raw, raw[1:]):
    cum.append(cum[-1] + math.dist(a, b))
LENGTH = cum[-1]


def at(s):
    s = max(0.0, min(LENGTH, s))
    for i in range(1, len(cum)):
        if cum[i] >= s:
            t = (s - cum[i - 1]) / max(1e-9, cum[i] - cum[i - 1])
            a, b = raw[i - 1], raw[i]
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    return raw[-1]


def along(p):
    """Distance along the route of the closest point, distance off it, and side (L/R)."""
    best = None
    for i in range(len(raw) - 1):
        a, b = raw[i], raw[i + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy or 1e-9
        t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
        q = (a[0] + t * dx, a[1] + t * dy)
        d = math.dist(p, q)
        if best is None or d < best[1]:
            side = "R" if dx * (p[1] - a[1]) - dy * (p[0] - a[0]) > 0 else "L"  # z points south
            best = (cum[i] + t * math.sqrt(L2), d, side)
    return best


STEP = 2.0
samples = [at(i * STEP) for i in range(int(LENGTH / STEP) + 1)] + [raw[-1]]

steps = []
for st in osrm["routes"][0]["legs"][0]["steps"]:
    m = st["maneuver"]
    lon, lat = m["location"]
    s, _, _ = along(xz(lat, lon))
    steps.append({"s": r1(s), "type": m["type"], "mod": m.get("modifier", ""), "name": st.get("name", "")})

# ------------------------------------------------------------------ crop window
xs = [p[0] for p in raw]
zs = [p[1] for p in raw]
MARGIN = 900
X0, X1 = min(xs) - MARGIN, max(xs) + MARGIN
Z0, Z1 = min(zs) - MARGIN, max(zs) + MARGIN


def in_window(p):
    return X0 <= p[0] <= X1 and Z0 <= p[1] <= Z1


# ------------------------------------------------------------------ roads
WIDTH = {
    "motorway": 24, "trunk": 18, "primary": 16, "secondary": 13, "tertiary": 10,
    "motorway_link": 8, "trunk_link": 8, "primary_link": 8, "secondary_link": 7, "tertiary_link": 7,
    "unclassified": 7, "residential": 6, "living_street": 5, "service": 4,
}
MAJOR = {"motorway", "trunk", "primary", "secondary", "tertiary"}
roads = []
for w in ways.values():
    t = w.get("tags", {})
    hw = t.get("highway")
    if hw not in WIDTH:
        continue
    if hw == "service" and t.get("service") in ("parking_aisle", "driveway", "drive-through"):
        continue
    pts = way_pts(w)
    if len(pts) < 2 or not any(in_window(p) for p in pts):
        continue
    lanes = t.get("lanes")
    width = WIDTH[hw]
    if lanes and lanes.isdigit() and hw not in ("motorway",):
        width = max(width, int(lanes) * 3.4)
    roads.append({"c": "major" if hw in MAJOR else ("link" if hw.endswith("_link") else "minor"),
                  "w": r1(width), "o": t.get("oneway") == "yes", "p": flat(pts)})

# ------------------------------------------------------------------ landmarks (OSM ids)
LM_AEON = 568194917  # landuse=commercial "AEON Mall Nilai"
LM_DATARAN = 1276331117  # leisure=park "Dataran Nilai"
LM_MCD = 857063682  # building "McDonald's" (Gerbang Alaf), Persiaran Pusat Bandar
LM_KFC_NODE = 3731357256  # amenity=fast_food "KFC", Jalan Nilai Square
LM_TOLL = 36365909  # barrier=toll_booth "Plaza Tol Nilai"
aeon_poly = way_pts(ways[LM_AEON])
kfc_p = xz(nodes[LM_KFC_NODE]["lat"], nodes[LM_KFC_NODE]["lon"])

# ------------------------------------------------------------------ buildings
DEFAULT_H = {"apartments": 34, "commercial": 13, "retail": 12, "office": 18, "hotel": 22, "mosque": 14,
             "school": 10, "university": 14, "house": 6, "terrace": 7, "residential": 8, "roof": 7,
             "industrial": 10, "warehouse": 10, "yes": 9}
buildings = []
kfc_bldg = None
for w in ways.values():
    t = w.get("tags", {})
    b = t.get("building")
    if not b or b in ("no",):
        continue
    pts = way_pts(w)
    if len(pts) < 4:
        continue
    if pts[0] == pts[-1]:
        pts = pts[:-1]
    c = centroid(pts)
    if not in_window(c):
        continue
    if "height" in t:
        try:
            h = float(t["height"].split()[0])
        except ValueError:
            h = DEFAULT_H.get(b, 9)
    elif t.get("building:levels", "").replace(".", "").isdigit():
        h = float(t["building:levels"]) * 3.4
    else:
        h = DEFAULT_H.get(b, 9)
    tag = ""
    if w["id"] == LM_MCD:
        tag, h = "mcd", 8
    elif inside(c, aeon_poly):
        tag, h = "aeon", max(h, 20)
    elif inside(kfc_p, pts):
        tag, h = "kfc", 8
    if t.get("barrier") == "toll_booth":
        continue  # the toll plaza canopy is modelled separately
    buildings.append({"h": r1(h), "t": tag, "p": flat(pts)})
    if tag == "kfc":
        kfc_bldg = c

# ------------------------------------------------------------------ green areas & water
GREEN = {("leisure", "park"), ("leisure", "pitch"), ("leisure", "golf_course"), ("leisure", "garden"),
         ("landuse", "grass"), ("landuse", "recreation_ground"), ("landuse", "forest"), ("landuse", "meadow"),
         ("natural", "wood"), ("natural", "scrub"), ("natural", "grassland")}
URBAN = {"residential", "commercial", "retail", "industrial", "education", "institutional", "religious"}
areas = []
for w in ways.values():
    t = w.get("tags", {})
    kind = None
    if any((k, t.get(k)) in GREEN for k in ("leisure", "landuse", "natural")):
        kind = "green"
    elif t.get("natural") == "water" or t.get("landuse") in ("reservoir", "basin"):
        kind = "water"
    elif t.get("landuse") in URBAN or t.get("amenity") in ("university", "college", "school"):
        kind = "urban"
    elif t.get("amenity") == "parking":
        kind = "parking"
    if not kind:
        continue
    pts = way_pts(w)
    if len(pts) < 4 or not any(in_window(p) for p in pts):
        continue
    areas.append({"k": "plaza" if w["id"] == LM_DATARAN else kind, "p": flat(pts[:-1] if pts[0] == pts[-1] else pts)})

# ------------------------------------------------------------------ traffic lights on the route
signals = []
for n in nodes.values():
    if n.get("tags", {}).get("highway") == "traffic_signals":
        s, d, _ = along(xz(n["lat"], n["lon"]))
        if d < 20:
            signals.append(s)
signals.sort()
lights = []  # one model per junction cluster
for s in signals:
    if not lights or s - lights[-1] > 60:
        lights.append(s)

# ------------------------------------------------------------------ landmark summary
def lm(name, p):
    s, d, side = along(p)
    return {"name": name, "x": r1(p[0]), "z": r1(p[1]), "s": r1(s), "off": r1(d), "side": side}


toll_p = xz(nodes[LM_TOLL]["lat"], nodes[LM_TOLL]["lon"])
landmarks = {
    "toll": lm("Plaza Tol Nilai", toll_p),
    "mcd": lm("McDonald's", centroid(way_pts(ways[LM_MCD]))),
    "kfc": lm("KFC (Jalan Nilai Square)", kfc_bldg or kfc_p),
    "dataran": lm("Dataran Nilai", centroid(way_pts(ways[LM_DATARAN]))),
    "aeon": lm("AEON Mall Nilai", centroid(aeon_poly)),
    "clinic": lm("Jalan BBN 1/3C", raw[-1]),
}

data = {
    "source": "© OpenStreetMap contributors (ODbL); route: OSRM",
    "origin": [LAT0, LON0],
    "window": [r1(X0), r1(Z0), r1(X1), r1(Z1)],
    "length": r1(LENGTH),
    "step": STEP,
    "route": flat(samples),
    "steps": steps,
    "lights": [r1(s) for s in lights],
    "landmarks": landmarks,
    "roads": roads,
    "buildings": buildings,
    "areas": areas,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("// Generated by tools/build_nav_map.py from OpenStreetMap data (© OpenStreetMap contributors, ODbL).\n"
               "window.MAP = " + json.dumps(data, separators=(",", ":")) + ";\n")

print(f"route {LENGTH:.0f} m, {len(roads)} roads, {len(buildings)} buildings, {len(areas)} areas, "
      f"lights at {[round(s) for s in lights]}")
for st in steps:
    print(f"  step {st['s']:7.0f} m  {st['type']:11} {st['mod']:12} {st['name']}")
for k, v in landmarks.items():
    print(f"  {k:8} {v['name']:26} along {v['s']:6.0f} m  off {v['off']:5.0f} m  side {v['side']}")
print(OUT, OUT.stat().st_size, "bytes")
