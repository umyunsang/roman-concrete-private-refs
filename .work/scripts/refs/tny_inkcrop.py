# -*- coding: utf-8 -*-
"""전역 잉크 마스크를 원본 위에 반투명 빨강으로 겹친 crop(검증용)."""
import os, sys
import cv2, numpy as np
ROOT = "/Users/um-yunsang/roman-concrete-private-refs"
OUT = os.path.join(ROOT, ".work/out/refs-analysis")
ref = sys.argv[1]; x0, y0, x1, y1 = [int(v) for v in sys.argv[2:6]]; name = sys.argv[6]
art = cv2.imread(os.path.join(OUT, f"{ref}_art.png"))[y0:y1, x0:x1].astype(np.float32)
ink = cv2.imread(os.path.join(OUT, f"{ref}_ink.png"), 0)[y0:y1, x0:x1] > 0
ov = art.copy(); ov[ink] = ov[ink] * 0.4 + np.array([0, 0, 255.0]) * 0.6
s = min(1400 / ov.shape[1], 1500 / ov.shape[0], 3.0)
ov = cv2.resize(ov.astype(np.uint8), None, fx=s, fy=s, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_NEAREST)
for g in range((x0 // 100 + 1) * 100, x1, 100):
    X = int((g - x0) * s); cv2.line(ov, (X, 0), (X, ov.shape[0]), (255, 0, 255), 1); cv2.putText(ov, str(g), (X + 2, 14), 0, 0.45, (255, 0, 255), 1)
for g in range((y0 // 100 + 1) * 100, y1, 100):
    Y = int((g - y0) * s); cv2.line(ov, (0, Y), (ov.shape[1], Y), (255, 160, 0), 1); cv2.putText(ov, str(g), (2, Y - 3), 0, 0.45, (255, 120, 0), 1)
p = os.path.join(OUT, "tny_crops", name + ".jpg"); cv2.imwrite(p, ov); print(p, ov.shape[1], ov.shape[0])
