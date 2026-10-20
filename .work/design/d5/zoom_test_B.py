# -*- coding: utf-8 -*-
import sys, os, random
sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/lib")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from PIL import Image, ImageDraw
import zoom_figs_B as Z

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "zoom_test")
os.makedirs(OUT, exist_ok=True)
KEYS = [("baths", Z.fig_baths), ("basilica", Z.fig_basilica), ("theatre", Z.fig_theatre)]

cells = []
for name, fn in KEYS:
    sub = Layer(0, 0, 62, 62)
    fn(sub, 31.0, 30.0, random.Random(name))
    big = sub.img.convert("RGB")
    full = big.copy()
    # 원 마스크 후 0.5배(= 62 mm → 31 mm 판, 원 지름 30 mm)
    mask = Image.new("L", big.size, 0)
    ImageDraw.Draw(mask).ellipse([(31 - 30) * KD, (31 - 30) * KD, (31 + 30) * KD, (31 + 30) * KD], fill=255)
    bg = Image.new("RGB", big.size, (231, 208, 160))
    bg.paste(big, (0, 0), mask)
    small = bg.resize((big.size[0] // 2, big.size[1] // 2), Image.LANCZOS)
    cells.append((name, full, small))

W = cells[0][1].size[0]
sheet = Image.new("RGB", (W * 3 + 40, W + W // 2 + 30), (255, 255, 255))
for i, (name, full, small) in enumerate(cells):
    sheet.paste(full, (10 + i * (W + 10), 10))
    sheet.paste(small, (10 + i * (W + 10), W + 20))
    big2 = small.resize((small.size[0], small.size[1]))
    sheet.paste(small.resize((small.size[0] // 2, small.size[1] // 2), Image.LANCZOS), (10 + i * (W + 10) + small.size[0] + 10, W + 20))
sheet.save(os.path.join(OUT, "B_시트.png"))
print("saved", sheet.size)
