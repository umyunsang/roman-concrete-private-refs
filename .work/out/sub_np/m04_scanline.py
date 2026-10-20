# 수평/수직 주사선을 따라 색 구간(런)을 출력한다. 사용: m04_scanline.py img h|v 좌표 [시작 끝] [허용차]
import sys
import cv2
import numpy as np

img = cv2.imread(sys.argv[1])
mode = sys.argv[2]
pos = int(sys.argv[3])
H, W = img.shape[:2]
a = int(sys.argv[4]) if len(sys.argv) > 4 else 0
b = int(sys.argv[5]) if len(sys.argv) > 5 else (W if mode == "h" else H)
tol = float(sys.argv[6]) if len(sys.argv) > 6 else 18
if mode == "h":
    line = img[pos, a:b].astype(np.float32)
else:
    line = img[a:b, pos].astype(np.float32)
runs = []
start = 0
ref = line[0]
for i in range(1, len(line)):
    if np.abs(line[i] - ref).max() > tol:
        runs.append((start, i - 1, line[start:i].mean(axis=0)))
        start = i
        ref = line[i]
runs.append((start, len(line) - 1, line[start:].mean(axis=0)))
for s, e, c in runs:
    if e - s + 1 >= int(sys.argv[7]) if len(sys.argv) > 7 else 3:
        bgr = c.astype(int)
        print("%5d-%5d (%4d) #%02X%02X%02X" % (s + a, e + a, e - s + 1, bgr[2], bgr[1], bgr[0]))
