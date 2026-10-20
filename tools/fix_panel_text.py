"""Repair panel logos after AI upscaling (run after tools/extract_panels.py on the upscale).

The upscaler sharpens the logos but invents letters in their tiny taglines. This script:
  * asp       - repaints the yellow band with the real text "Electronic Health Care Cards";
  * redalert  - repaints the tagline as "Realtime Electronic Data";
  * emas      - removes the (illegible in the source) green tagline;
  * mains     - keeps the sharp upscaled crest (crescent, weapons, MAINS, gear) but takes the
                curved fine print and calligraphy from the original pixels, so no lettering
                is invented.

Usage: python3 tools/fix_panel_text.py <clean_poster_frame.png> <upscaled_region.png> <origin_x> <origin_y> <region_w>
"""
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
PANELS = ROOT / "assets" / "panels"
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"


def load(name):
    return np.asarray(Image.open(PANELS / f"{name}.png").convert("RGBA")).copy()


def save(name, a):
    img = Image.fromarray(a, "RGBA")
    img = img.crop(img.getbbox())
    img.save(PANELS / f"{name}.png", optimize=True)
    print(name, img.size)


def fit_font(text, box_w, box_h):
    size = int(box_h)
    while size > 6:
        f = ImageFont.truetype(BOLD, size)
        l, t, r, b = f.getbbox(text)
        if r - l <= box_w and b - t <= box_h:
            return f
        size -= 1
    return ImageFont.truetype(BOLD, 6)


# ---- ASP: repaint the yellow band ---------------------------------------------
a = load("asp")
r, g, b = (a[..., i].astype(int) for i in range(3))
yellow = (r > 190) & (g > 170) & (b < 140) & (a[..., 3] > 200)
rows = np.nonzero(yellow.sum(1) > a.shape[1] * 0.5)[0]
cols = np.nonzero(yellow[rows].sum(0) > len(rows) * 0.5)[0]
y0, y1, x0, x1 = rows.min(), rows.max(), cols.min(), cols.max()
fill = np.median(a[y0 : y1 + 1, x0 : x1 + 1][yellow[y0 : y1 + 1, x0 : x1 + 1]], axis=0).astype(np.uint8)
a[y0 + 2 : y1 - 1, x0 + 3 : x1 - 2] = fill
img = Image.fromarray(a, "RGBA")
d = ImageDraw.Draw(img)
text = "Electronic Health Care Cards"
bh = y1 - y0
font = fit_font(text, (x1 - x0) * 0.9, bh * 0.62)
l, t, rr, bb = font.getbbox(text)
d.text((x0 + (x1 - x0) * 0.05 - l, y0 + (bh - (bb - t)) / 2 - t), text, font=font, fill=(26, 26, 26, 255))
save("asp", np.asarray(img).copy())

# ---- RedAlert: repaint the tagline ----------------------------------------------
a = load("redalert")
h, w = a.shape[:2]
r, g, b = (a[..., i].astype(int) for i in range(3))
reddish = (r > g + 50) & (r > b + 50)
zone = np.zeros((h, w), bool)
zone[int(h * 0.66) :, : int(w * 0.62)] = True
tag = zone & ~reddish & (a[..., 3] > 60)
ys, xs = np.nonzero(tag)
ty0, ty1, tx0, tx1 = ys.min(), ys.max(), xs.min(), xs.max()
a[..., 3][tag] = 0
img = Image.fromarray(a, "RGBA")
d = ImageDraw.Draw(img)
text = "Realtime Electronic Data"
font = fit_font(text, (tx1 - tx0) * 1.0, (ty1 - ty0) * 1.0)
l, t, rr, bb = font.getbbox(text)
d.text((tx0 - l, ty0 + ((ty1 - ty0) - (bb - t)) / 2 - t), text, font=font, fill=(88, 88, 88, 255))
save("redalert", np.asarray(img).copy())

# ---- eMAS: drop the green tagline ---------------------------------------------
a = load("emas")
h = a.shape[0]
r, g, b = (a[..., i].astype(int) for i in range(3))
green = (g > r + 30) & (g > b + 10)
band = np.zeros_like(green)
band[int(h * 0.62) :] = True
kill = np.asarray(Image.fromarray(((green & band) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))) > 0
a[..., 3][kill & band] = 0
save("emas", a)

# ---- MAINS: sharp crest from the upscale, fine print from the original ------------
frame = Image.open(sys.argv[1]).convert("RGB")
region = Image.open(sys.argv[2]).convert("RGB")
ox, oy, rw = map(int, sys.argv[3:6])
k = region.width / rw
BOX = (700, 926, 786, 1031)
W, H = (BOX[2] - BOX[0]) * 7, (BOX[3] - BOX[1]) * 7
ai = region.crop(tuple(round(v) for v in ((BOX[0] - ox) * k, (BOX[1] - oy) * k, (BOX[2] - ox) * k, (BOX[3] - oy) * k)))
ai = np.asarray(ai.resize((W, H), Image.LANCZOS)).astype(float)
orig = np.asarray(frame.crop(BOX).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(2.2))).astype(float)
r, g, b = ai[..., 0], ai[..., 1], ai[..., 2]
gear = (r > g + 60) & (r > b + 60)
gear = np.asarray(Image.fromarray((gear * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(11))) > 0
lower = np.zeros((H, W), bool)
lower[int(H * 0.5) : int(H * 0.93), int(W * 0.06) : int(W * 0.94)] = True
m = (lower & ~gear).astype(np.uint8) * 255
m = np.asarray(Image.fromarray(m).filter(ImageFilter.GaussianBlur(6))).astype(float)[..., None] / 255
a = ai * (1 - m) + orig * m
bg = np.median(np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]]), axis=0)
alpha = np.clip((np.linalg.norm(a - bg, axis=2) - 28) / 50, 0, 1)
al = alpha[..., None]
rgb = np.where(al > 0.02, (a - (1 - al) * bg) / np.maximum(al, 0.02), 0)
save("mains", np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8))
