# -*- coding: utf-8 -*-
"""클래스 지도 crop + 격자(아트 좌표)."""
import os, sys
import cv2, numpy as np
ROOT = "/Users/um-yunsang/roman-concrete-private-refs"
OUT = os.path.join(ROOT, ".work/out/refs-analysis")
ref = sys.argv[1]; x0, y0, x1, y1 = [int(v) for v in sys.argv[2:6]]; name = sys.argv[6]
step = int(sys.argv[7]) if len(sys.argv) > 7 else 100
blend = float(sys.argv[8]) if len(sys.argv) > 8 else 0.55
vis = cv2.imread(os.path.join(OUT, f"{ref}_class.png"))[y0:y1, x0:x1].astype(np.float32)
art = cv2.imread(os.path.join(OUT, f"{ref}_art.png"))[y0:y1, x0:x1].astype(np.float32)
c = (vis * blend + art * (1 - blend)).astype(np.uint8)
s = min(1300 / c.shape[1], 1500 / c.shape[0], 3.0)
c = cv2.resize(c, None, fx=s, fy=s, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_NEAREST)
for g in range((x0 // step + 1) * step, x1, step):
    X = int((g - x0) * s); cv2.line(c, (X, 0), (X, c.shape[0]), (255, 0, 255), 1); cv2.putText(c, str(g), (X + 2, 14), 0, 0.45, (255, 0, 255), 1)
for g in range((y0 // step + 1) * step, y1, step):
    Y = int((g - y0) * s); cv2.line(c, (0, Y), (c.shape[1], Y), (0, 200, 255), 1); cv2.putText(c, str(g), (2, Y - 3), 0, 0.45, (0, 200, 255), 1)
p = os.path.join(OUT, "tny_crops", name + ".jpg"); cv2.imwrite(p, c); print(p, c.shape[1], c.shape[0], round(s, 3))
