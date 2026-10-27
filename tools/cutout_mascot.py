"""Cut the clinic's fly mascot (illustration on a black background) into puppet layers.

    python3 tools/cutout_mascot.py <mascot.webp|png>

Writes, on one shared 1024 x 1024 canvas so the layers line up:
  fly-to-clinic/assets/mascot-body.png   body, head, arms, legs, antennae (no wings)
  fly-to-clinic/assets/mascot-wings.png  both wings, so they can flap around the shoulder

The background is removed by flood-filling the near-black pixels connected to the image border, so
dark navy shading inside the character is never touched. The anti-aliased edge is un-premultiplied
against black, which removes the dark fringe.
"""
import pathlib
import sys
from collections import deque

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "fly-to-clinic" / "assets"
SIZE = 1024

src = Image.open(sys.argv[1]).convert("RGB")
rgb = np.asarray(src).astype(np.float32)
h, w, _ = rgb.shape
mx = rgb.max(axis=2)

# 1. background = near-black pixels 4-connected to the border
bg = np.zeros((h, w), bool)
dark = mx < 26
q = deque()
for x in range(w):
    for y in (0, h - 1):
        if dark[y, x] and not bg[y, x]:
            bg[y, x] = True
            q.append((y, x))
for y in range(h):
    for x in (0, w - 1):
        if dark[y, x] and not bg[y, x]:
            bg[y, x] = True
            q.append((y, x))
while q:
    y, x = q.popleft()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ny, nx = y + dy, x + dx
        if 0 <= ny < h and 0 <= nx < w and dark[ny, nx] and not bg[ny, nx]:
            bg[ny, nx] = True
            q.append((ny, nx))

# 2. soft alpha in a thin band around the background, from brightness against the local maximum
fg = ~bg
band = np.asarray(Image.fromarray((bg * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
local_max = np.asarray(Image.fromarray(mx.astype(np.uint8)).filter(ImageFilter.MaxFilter(7))).astype(np.float32)
alpha = fg.astype(np.float32)
edge = band & fg
alpha[edge] = np.clip(mx[edge] / np.maximum(local_max[edge], 1), 0, 1)
alpha[bg] = 0
# un-premultiply against black to kill the dark fringe
safe = np.maximum(alpha, 1e-3)[..., None]
col = np.where(alpha[..., None] > 0, np.clip(rgb / safe, 0, 255), 0)

# 3. wings = bright / gold (not navy) pixels inside the wing area (left of the shoulder, above the hands)
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
navy = (b > r + 12) & (mx < 150)
# wing area traced on the 1254 px source: right edge runs along the upper wing up to the root (≈650, 625),
# bottom edge runs above the arm and the left hand
WING_POLY = [(0, 60), (380, 60), (380, 120), (650, 625), (380, 762), (300, 782), (0, 782)]
zone_img = Image.new("L", (w, h), 0)
ImageDraw.Draw(zone_img).polygon([(x * w / 1254, y * h / 1254) for x, y in WING_POLY], fill=255)
wing = (np.asarray(zone_img) > 0) & fg & ~navy
# fill pin-holes and drop specks so the wing layer is a clean shape
wimg = Image.fromarray((wing * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
wing = (np.asarray(wimg) > 127) & fg & ~navy

def save(mask, name):
    a = (alpha * mask).clip(0, 1)
    out = np.dstack([col, a * 255]).astype(np.uint8)
    Image.fromarray(out, "RGBA").resize((SIZE, SIZE), Image.LANCZOS).save(OUT / name, optimize=True)
    print(name, "pixels", int(mask.sum()))

save(wing, "mascot-wings.png")
save(~wing, "mascot-body.png")
ys, xs = np.nonzero(wing)
print("wing bbox", xs.min(), ys.min(), xs.max(), ys.max(), "of", w, h, "| wing root (canvas px):", round(640 * SIZE / 1254), round(610 * SIZE / 1254))
