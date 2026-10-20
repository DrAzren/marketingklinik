"""Interim vector redraw of the Klinik Nissa logo (1024x1024, transparent).

Replace assets/klinik-nissa-logo.png with the original logo file when available;
the composition crops the emblem from the same 1024-square layout.
"""
import math, pathlib

Y, C = "#F8E04A", "#4ED8DA"
root = pathlib.Path(__file__).resolve().parent.parent

# Brain: a looping scribble that travels around a brain-shaped outline.
pts = []
N = 900
for i in range(N + 1):
    t = i / N
    a = math.pi * (1.05 + 1.9 * t)          # sweep over the top of the brain
    rx, ry = 104 + 8 * math.sin(3 * a), 66 + 6 * math.cos(2 * a)
    ox, oy = 527 + rx * math.cos(a), 352 + ry * math.sin(a) * 0.95
    k = 13 * 2 * math.pi * t                 # 13 loops
    r = 17 + 4 * math.sin(5 * t * math.pi)
    pts.append((ox + r * math.cos(k), oy + r * math.sin(k)))
# inner loops along the middle + the stem down to the head
for i in range(301):
    t = i / 300
    ox, oy = 455 + 150 * t, 365 + 20 * math.sin(t * math.pi)
    k = 4 * 2 * math.pi * t + math.pi
    pts.append((ox + 15 * math.cos(k), oy + 13 * math.sin(k)))
for i in range(121):
    t = i / 120
    ox, oy = 600 - 55 * t, 380 + 62 * t
    k = 1.2 * 2 * math.pi * t
    pts.append((ox + 12 * math.cos(k) * (1 - t), oy + 10 * math.sin(k) * (1 - t)))
brain = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" width="1024" height="1024">
<defs><style>@font-face{{font-family:P;src:url(../assets/fonts/poppins-latin-700-normal.woff2)}}</style></defs>
<circle cx="527" cy="447" r="191" fill="none" stroke="{Y}" stroke-width="15"/>
<path d="{brain}" fill="none" stroke="{Y}" stroke-width="5.5" stroke-linecap="round" stroke-linejoin="round"/>
<!-- yellow right leaf -->
<path d="M655,428 C700,500 660,600 560,640 C540,600 548,520 600,470 C620,452 640,445 655,428 Z" fill="{Y}" stroke="#0B2850" stroke-width="10"/>
<!-- figure: head + swooping body -->
<circle cx="537" cy="470" r="22" fill="{Y}"/>
<path d="M528,500 C548,520 548,560 520,605 C510,620 498,640 480,656 C506,640 540,612 556,570 C566,540 560,512 545,498 Z" fill="{Y}"/>
<!-- turquoise left leaf with navy vein -->
<path d="M298,393 C400,410 495,470 520,560 C528,600 515,640 490,656 C420,640 335,600 305,520 C290,480 290,430 298,393 Z" fill="{C}" stroke="#0B2850" stroke-width="10"/>
<path d="M330,470 C400,455 470,490 500,560 C470,510 410,488 330,470 Z" fill="#0B2850"/>
<path d="M420,612 C460,640 500,648 530,640 C500,660 455,656 420,612 Z" fill="#0B2850"/>
<text x="512" y="738" text-anchor="middle" font-family="P" font-weight="700" font-size="62" letter-spacing="1"><tspan fill="{Y}">KLINIK </tspan><tspan fill="{C}">NISSA</tspan></text>
</svg>'''
out = root / "tools" / "klinik-nissa-logo-redraw.svg"
out.write_text(svg)
print(out)
