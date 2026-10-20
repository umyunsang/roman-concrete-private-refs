"""고해상 타일을 원 해상도로 잘라 10px 격자와 N 좌표 눈금을 붙인다.
사용: r3_tilecrop.py <ref> <tile 01|04|05> <N x0> <N y0> <N x1> <N y1> <이름> [확대=2]
- 타일 원 해상도에서 1 N = 2 px. 격자는 N 5 단위(원 10px), 25 단위마다 굵게.
"""
import os
import sys

import cv2

sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/refs")
from r3_common import OUT, imread, load_json  # noqa: E402

ref, tid = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = [float(v) for v in sys.argv[3:7]]
name = sys.argv[7]
zoom = int(sys.argv[8]) if len(sys.argv) > 8 else 2
t = load_json("r3_register.json")[ref]["tiles"][tid]
bx0, by0, bx1, by1 = t["box_norm1000"]
im = imread(t["file"])
sx = im.shape[1] / (bx1 - bx0)
sy = im.shape[0] / (by1 - by0)
X0, Y0, X1, Y1 = int((x0 - bx0) * sx), int((y0 - by0) * sy), int((x1 - bx0) * sx), int((y1 - by0) * sy)
c = im[max(0, Y0):Y1, max(0, X0):X1].copy()
c = cv2.resize(c, (c.shape[1] * zoom, c.shape[0] * zoom), interpolation=cv2.INTER_NEAREST)
import numpy as np  # noqa: E402

for gx in np.arange(np.ceil(x0 / 5) * 5, x1, 5):
    X = int((gx - x0) * sx * zoom)
    thick = 25 if gx % 25 == 0 else 0
    cv2.line(c, (X, 0), (X, c.shape[0]), (255, 0, 255) if thick else (230, 180, 255), 1)
    if gx % 25 == 0:
        cv2.putText(c, "%d" % gx, (X + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 0, 200), 1)
for gy in np.arange(np.ceil(y0 / 5) * 5, y1, 5):
    Y = int((gy - y0) * sy * zoom)
    thick = gy % 25 == 0
    cv2.line(c, (0, Y), (c.shape[1], Y), (255, 140, 0) if thick else (255, 220, 160), 1)
    if gy % 25 == 0:
        cv2.putText(c, "%d" % gy, (2, Y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 100, 0), 1)
os.makedirs(os.path.join(OUT, "crops"), exist_ok=True)
p = os.path.join(OUT, "crops", f"{ref}_T{tid}_{name}.png")
cv2.imwrite(p, c)
print(p, c.shape, "px/N", round(sx * zoom, 2))
