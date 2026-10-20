# 바닥의 옅은 이음선(가는 어두운 선) 지도: 바닥색 영역에서 블랙햇(닫힘-원본)으로 가는 어두운 선을 강조.
import sys
import cv2
import numpy as np

img = cv2.imread(sys.argv[1])
out = sys.argv[2]
x0, y0, x1, y1 = 330, 380, 1490, 2660
sub = img[y0:y1, x0:x1]
lab = cv2.cvtColor(sub, cv2.COLOR_BGR2LAB).astype(np.float32)
L = lab[:, :, 0]
ref = cv2.cvtColor(np.uint8([[[0xB6, 0xD4, 0xE6]]]), cv2.COLOR_BGR2LAB).astype(np.float32)[0, 0]
d = np.sqrt(((lab - ref) ** 2).sum(axis=2))
floorish = (d < 22).astype(np.uint8)
floor_big = cv2.morphologyEx(floorish, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
bh = cv2.morphologyEx(L.astype(np.uint8), cv2.MORPH_BLACKHAT, k).astype(np.float32)
line = ((bh > 4) & (bh < 40) & (floor_big > 0) & (d < 30)).astype(np.uint8) * 255
vis = cv2.cvtColor((floor_big * 60).astype(np.uint8), cv2.COLOR_GRAY2BGR)
vis[line > 0] = (0, 0, 255)
# 꼭짓점 표시
for (px, py) in [(378, 755), (378, 1170), (373, 1580), (372, 1990), (375, 2400), (737, 962), (737, 1372), (737, 1782), (727, 2195),
                 (1437, 960), (1434, 1370), (1431, 1780), (1435, 2190), (1082, 1165), (1082, 1575), (1082, 1985), (713, 2600), (715, 560)]:
    cv2.circle(vis, (px - x0, py - y0), 6, (0, 255, 0), 2)
small = cv2.resize(vis, (int(vis.shape[1] * 0.45), int(vis.shape[0] * 0.45)), interpolation=cv2.INTER_AREA)
cv2.imwrite(out, small)
print(small.shape)
