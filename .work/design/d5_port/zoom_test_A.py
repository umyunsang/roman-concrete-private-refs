# -*- coding: utf-8 -*-
import sys, random
sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/lib")
sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/design/d5")
from common import *
from PIL import Image, ImageDraw, ImageChops
import zoom_figs_A as Z

FIGS = [("colosseum", Z.fig_colosseum), ("pantheon", Z.fig_pantheon), ("markets", Z.fig_markets)]
vc, vr = 31.0, 30.0
BGC = (231, 208, 160, 255)
cells = []
for name, fn in FIGS:
    sub = Layer(0, 0, 62, 62)
    fn(sub, vc, vr, random.Random(7))
    mask = Image.new("L", (sub.w, sub.h), 0)
    ImageDraw.Draw(mask).ellipse([sub.X(vc - vr), sub.Y(vc - vr), sub.X(vc + vr), sub.Y(vc + vr)], fill=255)
    im = sub.img.copy()
    im.putalpha(ImageChops.multiply(im.getchannel("A"), mask))
    small = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
    cells.append((name, sub.img, small))
W = sum(c[1].width for c in cells) + 40
H = cells[0][1].height + cells[0][2].height + 40
sheet = Image.new("RGBA", (W, H), BGC)
x = 10
for name, full, small in cells:
    sheet.alpha_composite(full, (x, 10))
    sheet.alpha_composite(small, (x + (full.width - small.width) // 2, 20 + full.height))
    x += full.width + 10
sheet.convert("RGB").save("out/zoom_test/A_시트.png")
print(sheet.size)
