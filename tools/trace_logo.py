"""Rebuild the original Klinik Nissa logo as a clean vector from a reference frame.

Usage: python3 tools/trace_logo.py <frame.png> <x> <y> <w> <h> [<hires.png>]

<hires.png> is an optional AI-upscaled copy of exactly that crop; when given, shapes are
traced from it (much cleaner edges) while coordinates stay in frame-crop pixels.

The logo crop (x, y, w, h) comes from the clinic's own poster video. Because that
source is small and compressed, the logo is rebuilt in three parts:
  * the outer ring  -> a least-squares fitted circle, drawn only over the arcs
                       where the original ring is visible;
  * leaves, figure and brain -> colour-separated, smoothed and traced with potrace;
  * the wordmark    -> typeset in Poppins Bold (matching the original lettering).

Writes tools/klinik-nissa-logo.svg (1024 x 1024, transparent). Rasterise it to
assets/klinik-nissa-logo.png with headless Chromium (see README).
"""
import math
import pathlib
import sys

import numpy as np
import potrace
from PIL import Image, ImageFilter

SCALE = 8
YELLOW, TURQ = "#F7D748", "#4FD8D6"
OUT = 1024
RING_R_OUT = 205  # ring radius in the 1024 layout
RING_C = (512, 430)

src, x, y, w, h = sys.argv[1], *map(int, sys.argv[2:6])
img = Image.open(src).convert("RGB").crop((x, y, x + w, y + h))
HIRES = len(sys.argv) > 6
if HIRES:  # clean AI upscale of the same crop
    hi = Image.open(sys.argv[6]).convert("RGB")
    img = hi.resize((w, h), Image.LANCZOS)
    big = np.asarray(hi.resize((w * SCALE, h * SCALE), Image.LANCZOS)).astype(float) / 255
else:
    big = np.asarray(img.resize((w * SCALE, h * SCALE), Image.BICUBIC)).astype(float) / 255
small = np.asarray(img).astype(float) / 255
BLUR = 0.45 if HIRES else 1.0  # edge smoothing (source px); a clean source needs little


def scores(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    yel = np.clip((np.minimum(r, g) - b - 0.18) / 0.25, 0, 1)
    tur = np.clip((np.minimum(g, b) - r - 0.12) / 0.25, 0, 1)
    return yel, tur


yel_s, _ = scores(small)
yel, tur = scores(big)

# ---- fit the ring (source pixel space) --------------------------------------
ys, xs = np.nonzero(yel_s > 0.5)
cx, cy, R = w / 2, h * 0.42, min(w, h) * 0.35
for _ in range(6):
    d = np.hypot(xs - cx, ys - cy)
    sel = (d > R * 0.85) & (d < R * 1.15)
    X, Y = xs[sel].astype(float), ys[sel].astype(float)
    A = np.c_[2 * X, 2 * Y, np.ones_like(X)]
    sol, *_ = np.linalg.lstsq(A, X**2 + Y**2, rcond=None)
    cx, cy = sol[0], sol[1]
    R = math.sqrt(sol[2] + cx**2 + cy**2)
# ring thickness from the radial profile
d = np.hypot(xs - cx, ys - cy)
band = d[(d > R * 0.8) & (d < R * 1.2)]
hist, edges = np.histogram(band, bins=np.arange(R * 0.8, R * 1.2, 0.25))
on = edges[:-1][hist > hist.max() * 0.35]
r_in, r_out = on.min(), on.max() + 0.25
R, T = (r_in + r_out) / 2, r_out - r_in
print(f"ring centre=({cx:.2f},{cy:.2f}) R={R:.2f} T={T:.2f}")

# angular coverage of the ring
present = []
for i in range(720):
    a = math.radians(i / 2)
    px, py = (cx + R * math.cos(a)) * SCALE, (cy + R * math.sin(a)) * SCALE
    present.append(yel[int(py), int(px)] > 0.5 if 0 <= py < h * SCALE and 0 <= px < w * SCALE else False)
present = np.array(present)
for _ in range(2):  # close tiny gaps (compression noise)
    present = present | (np.roll(present, 4) & np.roll(present, -4))
start = int(np.argmin(present))  # begin scanning inside a gap
arcs, cur = [], None
for k in range(720):
    i = (start + k) % 720
    if present[i] and cur is None:
        cur = i
    if not present[i] and cur is not None:
        arcs.append((cur / 2, ((i - 1) % 720) / 2))
        cur = None
if cur is not None:
    arcs.append((cur / 2, ((start - 1) % 720) / 2))
arcs = [(a0, a1) for a0, a1 in arcs if ((a1 - a0) % 360) > 6]
print("ring arcs (deg):", arcs)

# ---- trace leaves / figure / brain -------------------------------------------
yy, xx = np.mgrid[0 : h * SCALE, 0 : w * SCALE] / SCALE
dist = np.hypot(xx - cx, yy - cy)
ring_band = np.abs(dist - R) < T / 2 + (0.6 if HIRES else -0.5)  # the stroked ring is drawn on top
text_cut = yy > cy + R + 4  # wordmark is typeset, not traced
brain_zone = (yy < cy + 0.05 * R) & (dist < R - T)
brain_zone &= ~((xx > cx + 0.55 * R) & (yy > cy - 0.15 * R))  # yellow leaf tip is not brain


def trace(score, sigma, thresh):
    m = Image.fromarray((score * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(sigma * SCALE))
    bm = potrace.Bitmap(np.asarray(m) <= thresh * 255)  # potracer treats "dark" (False) as ink
    plist = bm.trace(turdsize=SCALE * SCALE * 3, alphamax=1.25, opticurve=True, opttolerance=0.6)
    return plist


def to_path(plist, f):
    out = []
    for curve in plist:
        p = curve.start_point
        out.append("M%.2f,%.2f" % f(p.x / SCALE, p.y / SCALE))
        for s in curve.segments:
            if s.is_corner:
                out.append("L%.2f,%.2f" % f(s.c.x / SCALE, s.c.y / SCALE))
                out.append("L%.2f,%.2f" % f(s.end_point.x / SCALE, s.end_point.y / SCALE))
            else:
                out.append(
                    "C%.2f,%.2f %.2f,%.2f %.2f,%.2f"
                    % (*f(s.c1.x / SCALE, s.c1.y / SCALE), *f(s.c2.x / SCALE, s.c2.y / SCALE), *f(s.end_point.x / SCALE, s.end_point.y / SCALE))
                )
        out.append("Z")
    return "".join(out)


def thin(mask):
    """Zhang-Suen thinning -> 1px skeleton (bool array)."""
    im = np.pad(mask.astype(np.uint8), 1)
    while True:
        changed = False
        for step in (0, 1):
            P = [im[:-2, 1:-1], im[:-2, 2:], im[1:-1, 2:], im[2:, 2:], im[2:, 1:-1], im[2:, :-2], im[1:-1, :-2], im[:-2, :-2]]
            B = sum(P.copy())
            A = sum(((P[i] == 0) & (P[(i + 1) % 8] == 1)).astype(np.uint8) for i in range(8))
            if step == 0:
                c = (P[0] * P[2] * P[4] == 0) & (P[2] * P[4] * P[6] == 0)
            else:
                c = (P[0] * P[2] * P[6] == 0) & (P[0] * P[4] * P[6] == 0)
            rm = (im[1:-1, 1:-1] == 1) & (B >= 2) & (B <= 6) & (A == 1) & c
            if rm.any():
                im[1:-1, 1:-1][rm] = 0
                changed = True
        if not changed:
            return im[1:-1, 1:-1].astype(bool)


def skeleton_paths(skel, min_len):
    """Walk the skeleton graph into polylines (list of (x, y) arrays, upscaled px)."""
    pts = set(zip(*np.nonzero(skel)))
    nb = lambda p: [(p[0] + dy, p[1] + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy or dx) and (p[0] + dy, p[1] + dx) in pts]
    deg = {p: len(nb(p)) for p in pts}
    nodes = {p for p in pts if deg[p] != 2}
    used = set()
    lines = []

    def walk(a, b):
        line = [a, b]
        used.add((a, b)); used.add((b, a))
        prev, cur = a, b
        while cur not in nodes:
            nxt = [q for q in nb(cur) if q != prev and (cur, q) not in used]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            used.add((prev, cur)); used.add((cur, prev))
            line.append(cur)
            if cur == line[0]:
                break
        return line

    for n in nodes:
        for q in nb(n):
            if (n, q) not in used:
                lines.append(walk(n, q))
    for p in pts:  # closed loops without nodes
        if deg[p] == 2 and all((p, q) not in used for q in nb(p)):
            nodes.add(p)
            lines.append(walk(p, nb(p)[0]))
            nodes.discard(p)
    # drop short spurs (thinning artefacts) that dangle from an end point
    out = []
    for l in lines:
        n_end = sum(deg[e] == 1 for e in (l[0], l[-1]))
        if len(l) < min_len and n_end >= 1:
            continue
        out.append(np.array([(x, y) for y, x in l], float))
    return out


def smooth_path(line, f, win=int(2.5 * SCALE) | 1, step=SCALE):
    if len(line) >= win:
        k_ = np.ones(win) / win
        sm = np.c_[np.convolve(np.pad(line[:, 0], win // 2, mode="edge"), k_, "valid"), np.convolve(np.pad(line[:, 1], win // 2, mode="edge"), k_, "valid")]
        sm[0], sm[-1] = line[0], line[-1]
    else:
        sm = line
    idx = sorted(set(list(range(0, len(sm), step)) + [len(sm) - 1]))
    q = [f(x / SCALE, y / SCALE) for x, y in sm[idx]]
    if len(q) < 2:
        return ""
    d = ["M%.2f,%.2f" % q[0]]
    for i in range(len(q) - 1):  # Catmull-Rom -> cubic Bezier
        p0, p1, p2, p3 = q[max(i - 1, 0)], q[i], q[i + 1], q[min(i + 2, len(q) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append("C%.2f,%.2f %.2f,%.2f %.2f,%.2f" % (*c1, *c2, *p2))
    return "".join(d)


# map source pixel space -> 1024 layout (ring outer edge at RING_R_OUT)
k = RING_R_OUT / (R + T / 2)


def f(px, py):
    return (RING_C[0] + (px - cx) * k, RING_C[1] + (py - cy) * k)


outside_ring = dist > R - T / 2 + 0.3  # the stroked ring covers everything from here out
yel_body = np.where(ring_band | outside_ring | text_cut | brain_zone, 0, yel)
yel_brain = np.where(brain_zone & ~ring_band, yel, 0)
tur_body = np.where(text_cut, 0, tur)

d_tur = to_path(trace(tur_body, BLUR * 1.1, 0.5), f)
d_yel = to_path(trace(yel_body, BLUR * 0.8, 0.5), f)
# Brain: a single-weight scribble in the original, so rebuild it from its centre line.
bm_soft = np.asarray(Image.fromarray((yel_brain * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur((0.3 if HIRES else 0.5) * SCALE))) / 255
brain_mask = bm_soft > (0.4 if HIRES else 0.3)
skel = thin(brain_mask)
brain_w = (bm_soft > 0.5).sum() / max(skel.sum(), 1) / SCALE  # mean line width, source px
print(f"brain stroke ~{brain_w:.2f}px, skeleton {skel.sum()} px")
d_brain = " ".join(smooth_path(l, f) for l in skeleton_paths(skel, min_len=int(2.5 * SCALE)))

# ring arcs as stroked paths
ring_paths = []
Rk, Tk = R * k, T * k
for a0, a1 in arcs:
    span = (a1 - a0) % 360
    p0 = (RING_C[0] + Rk * math.cos(math.radians(a0)), RING_C[1] + Rk * math.sin(math.radians(a0)))
    p1 = (RING_C[0] + Rk * math.cos(math.radians(a1)), RING_C[1] + Rk * math.sin(math.radians(a1)))
    large = 1 if span > 180 else 0
    ring_paths.append(f"M{p0[0]:.2f},{p0[1]:.2f} A{Rk:.2f},{Rk:.2f} 0 {large} 1 {p1[0]:.2f},{p1[1]:.2f}")

text_y = RING_C[1] + (209 - cy) * k  # original baseline sits ~209px down the crop
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {OUT} {OUT}" width="{OUT}" height="{OUT}">
<defs><style>@font-face{{font-family:P;font-weight:700;src:url(../assets/fonts/poppins-latin-700-normal.woff2)}}</style></defs>
<circle cx="{RING_C[0]}" cy="{RING_C[1]}" r="{Rk:.2f}" fill="#0B2850"/>
<path fill="{TURQ}" fill-rule="evenodd" d="{d_tur}"/>
<path fill="{YELLOW}" fill-rule="evenodd" d="{d_yel}"/>
<path fill="none" stroke="{YELLOW}" stroke-width="{brain_w * 1.15 * k:.2f}" stroke-linecap="round" stroke-linejoin="round" d="{d_brain}"/>
<path fill="none" stroke="{YELLOW}" stroke-width="{Tk:.2f}" d="{' '.join(ring_paths)}"/>
<text x="{RING_C[0]}" y="{text_y:.0f}" text-anchor="middle" font-family="P" font-weight="700" font-size="70" letter-spacing="1"><tspan fill="{YELLOW}">KLINIK </tspan><tspan fill="{TURQ}">NISSA</tspan></text>
</svg>
'''
out = pathlib.Path(__file__).resolve().parent / "klinik-nissa-logo.svg"
out.write_text(svg)
print(out, len(svg))

# Emblem-only vector (no wordmark) for crisp display at any resolution.
body = svg.split("</defs>\n", 1)[1].rsplit("<text", 1)[0]
emblem = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="280 220 470 420" width="940" height="840">\n{body}</svg>\n'
out = pathlib.Path(__file__).resolve().parent.parent / "assets" / "klinik-nissa-emblem.svg"
out.write_text(emblem)
print(out, len(emblem))
