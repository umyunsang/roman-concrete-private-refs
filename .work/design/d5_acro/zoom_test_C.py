# -*- coding: utf-8 -*-
import sys, random
sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/lib")
sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/design/d5")
from common import *
from PIL import Image, ImageDraw
import zoom_figs_C as Z

FIGS = [("mausoleum", Z.fig_mausoleum), ("metella", Z.fig_metella), ("portus", Z.fig_portus)]
vc, vr = 31.0, 30.0
tiles = []
for name, fn in FIGS:
    sub = Layer(0, 0, 62, 62)
    fn(sub, vc, vr, random.Random(7))
    full = sub.img.convert("RGBA")
    mask = Image.new("L", full.size, 0)
    ImageDraw.Draw(mask).ellipse([sub.X(vc - vr), sub.Y(vc - vr), sub.X(vc + vr), sub.Y(vc + vr)], fill=255)
    circ = Image.new("RGBA", full.size, (255, 255, 255, 0)); circ.paste(full, (0, 0), mask)
    small = circ.resize((full.width // 2, full.height // 2), Image.LANCZOS)
    tiles.append((full, small))
W = tiles[0][0].width; H = tiles[0][0].height
sheet = Image.new("RGB", (W * 2 + 50 + W // 2, (H + 20) * 3), (255, 255, 255))
for i, (full, small) in enumerate(tiles):
    y = i * (H + 20) + 10
    sheet.paste(full, (10, y), full)
    c = Image.new("RGBA", small.size, (255, 255, 255, 255)); c.alpha_composite(small)
    sheet.paste(c.convert("RGB"), (W + 30, y))
    big = small.resize((W, H), Image.LANCZOS)  # 0.5배 결과를 확대해 보기
    c2 = Image.new("RGBA", big.size, (255, 255, 255, 255)); c2.alpha_composite(big)
    sheet.paste(c2.convert("RGB"), (W + 30 + small.width + 10, y))
sheet.save("out/zoom_test/C_시트.png")
print(sheet.size)
