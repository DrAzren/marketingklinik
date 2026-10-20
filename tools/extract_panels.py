"""Cut the panel logos out of the clinic's poster frame and key out its turquoise card.

Usage: python3 tools/extract_panels.py <clean_frame.png>
Writes assets/panels/<name>.png (transparent, trimmed, upscaled 3x).
"""
import pathlib
import sys

import numpy as np
from PIL import Image, ImageFilter

UP = 3
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
out_dir = pathlib.Path(__file__).resolve().parent.parent / "assets" / "panels"
out_dir.mkdir(parents=True, exist_ok=True)

for name, (x0, y0, x1, y1) in BOXES.items():
    crop = frame.crop((x0, y0, x1, y1))
    big = crop.resize(((x1 - x0) * UP, (y1 - y0) * UP), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))
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
    img.save(out_dir / f"{name}.png")
    print(name, img.size, "bg", bg.round())
