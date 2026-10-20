# -*- coding: utf-8 -*-
"""아트 좌표(2000x2800) 격자를 얹은 확대 crop을 만든다(눈 판독용).
사용: python -I tny_crop.py <ref> <x0> <y0> <x1> <y1> [step=50] [maxw=1400] [name]
"""
import os
import sys

import cv2

ROOT = "/Users/um-yunsang/roman-concrete-private-refs"
OUT = os.path.join(ROOT, ".work/out/refs-analysis")
TMP = os.path.join(OUT, "tny_crops")
os.makedirs(TMP, exist_ok=True)

ref = sys.argv[1]
x0, y0, x1, y1 = [int(v) for v in sys.argv[2:6]]
step = int(sys.argv[6]) if len(sys.argv) > 6 else 50
maxw = int(sys.argv[7]) if len(sys.argv) > 7 else 1400
name = sys.argv[8] if len(sys.argv) > 8 else f"{ref}_{x0}_{y0}_{x1}_{y1}"
art = cv2.imread(os.path.join(OUT, f"{ref}_art.png"))
c = art[y0:y1, x0:x1].copy()
s = min(maxw / c.shape[1], 1600 / c.shape[0], 4.0)
c = cv2.resize(c, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA)
for gx in range((x0 // step + 1) * step, x1, step):
    X = int((gx - x0) * s)
    col = (255, 0, 255) if gx % (step * 2) == 0 else (200, 120, 255)
    cv2.line(c, (X, 0), (X, c.shape[0]), col, 1)
    cv2.putText(c, str(gx), (X + 2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 255), 1, cv2.LINE_AA)
for gy in range((y0 // step + 1) * step, y1, step):
    Y = int((gy - y0) * s)
    col = (255, 160, 0) if gy % (step * 2) == 0 else (255, 210, 120)
    cv2.line(c, (0, Y), (c.shape[1], Y), col, 1)
    cv2.putText(c, str(gy), (2, Y - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 120, 0), 1, cv2.LINE_AA)
p = os.path.join(TMP, name + ".jpg")
cv2.imwrite(p, c, [cv2.IMWRITE_JPEG_QUALITY, 88])
print(p, c.shape[1], c.shape[0], "scale", round(s, 3))
