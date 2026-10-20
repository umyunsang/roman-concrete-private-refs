# 공정도 영역에서 행(y)마다 바닥/측면(배경이 아닌 것)의 좌우 끝 x를 구해 플랫폼 꼭짓점을 찾는다.
import sys
import cv2
import numpy as np

img = cv2.imread(sys.argv[1])
lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)

def near(hexcol, tol):
    r, g, b = int(hexcol[0:2], 16), int(hexcol[2:4], 16), int(hexcol[4:6], 16)
    ref = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2LAB).astype(np.float32)[0, 0]
    return np.sqrt(((lab - ref) ** 2).sum(axis=2)) < tol

floor = near("E6D4B6", 14)
X0, X1 = 340, 1470
step = 10
rows = []
for y in range(400, 2700, step):
    xs = np.where(floor[y, X0:X1])[0]
    if len(xs) < 5:
        rows.append((y, None, None))
        continue
    rows.append((y, X0 + int(xs.min()), X0 + int(xs.max())))
for y, a, b in rows:
    print(y, a, b)
