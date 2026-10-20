"""Cut the panel logos out of the clinic's poster frame and key out its turquoise card.

Usage:
  python3 tools/extract_panels.py <clean_frame.png>
  python3 tools/extract_panels.py <upscaled_region.png> <origin_x> <origin_y> <region_w>
The second form takes an AI-upscaled crop of the poster's panel card whose top-left
corner was (origin_x, origin_y) in the frame and whose original width was region_w.
Writes assets/panels/<name>.png (transparent, trimmed, at most MAX_W px wide).
"""
import pathlib
import sys

import numpy as np
from PIL import Image, ImageFilter

UP = 3
MAX_W = 640
# name: (x0, y0, x1, y1) in the 1080x1350 poster frame (generous boxes, trimmed later)
BOXES = {
    "pmcare": (586, 756, 689, 857),
    "aia": (702, 764, 786, 852),
    "etiqa": (804, 794, 898, 832),
    "asp": (584, 867, 690, 924),
    "emas": (690, 874, 795, 921),
    "perodua": (792, 858, 908, 940),
    "fomema": (594, 953, 686, 985),
    "mains": (700, 926, 786, 1031),
    "great-eastern": (795, 952, 908, 997),
    "redalert": (574, 1037, 694, 1076),
    "healthmetrics": (697, 1036, 800, 1075),
    "medkad": (803, 1023, 912, 1092),
}

frame = Image.open(sys.argv[1]).convert("RGB")
if len(sys.argv) == 5:  # upscaled region: map frame boxes into its pixel space
    ox, oy, rw = map(int, sys.argv[2:5])
    k = frame.width / rw
    BOXES = {n: tuple(round(v) for v in ((x0 - ox) * k, (y0 - oy) * k, (x1 - ox) * k, (y1 - oy) * k)) for n, (x0, y0, x1, y1) in BOXES.items()}
    UP = 1
out_dir = pathlib.Path(__file__).resolve().parent.parent / "assets" / "panels"
out_dir.mkdir(parents=True, exist_ok=True)

for name, (x0, y0, x1, y1) in BOXES.items():
    crop = frame.crop((x0, y0, x1, y1))
    big = crop.resize(((x1 - x0) * UP, (y1 - y0) * UP), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2)) if UP > 1 else crop
    a = np.asarray(big).astype(float)
    # background = median of the crop border (the poster's turquoise card)
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    bg = np.median(border, axis=0)
    dist = np.linalg.norm(a - bg, axis=2)
    alpha = np.clip((dist - 28) / 50, 0, 1)
    al = alpha[..., None]
    rgb = np.where(al > 0.02, (a - (1 - al) * bg) / np.maximum(al, 0.02), 0)
    rgba = np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8)
    img = Image.fromarray(rgba, "RGBA")
    ys, xs = np.nonzero(alpha > 0.15)
    img = img.crop((max(xs.min() - 4, 0), max(ys.min() - 4, 0), xs.max() + 5, ys.max() + 5))
    if img.width > MAX_W:
        img = img.resize((MAX_W, round(img.height * MAX_W / img.width)), Image.LANCZOS)
    img.save(out_dir / f"{name}.png", optimize=True)
    print(name, img.size, "bg", bg.round())
