# 아트 좌표 격자를 덧그린 확대 크롭을 만든다. 사용: m05_gridcrop.py img x y w h scale step out
import sys
import cv2
import numpy as np

img = cv2.imread(sys.argv[1])
x, y, w, h = map(int, sys.argv[2:6])
scale = float(sys.argv[6])
step = int(sys.argv[7])
out = sys.argv[8]
crop = img[y:y + h, x:x + w].copy()
crop = cv2.resize(crop, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
gx0 = (x // step + 1) * step
for gx in range(gx0, x + w, step):
    px = int((gx - x) * scale)
    cv2.line(crop, (px, 0), (px, crop.shape[0] - 1), (255, 0, 255), 1)
    cv2.putText(crop, str(gx), (px + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 255), 1)
gy0 = (y // step + 1) * step
for gy in range(gy0, y + h, step):
    py = int((gy - y) * scale)
    cv2.line(crop, (0, py), (crop.shape[1] - 1, py), (255, 0, 255), 1)
    cv2.putText(crop, str(gy), (2, py - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 255), 1)
cv2.imwrite(out, crop)
