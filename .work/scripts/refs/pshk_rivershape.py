"""강 군집 마스크를 지도 영역에서 보여 주는 확인 그림. 입력 이미지는 읽기만 한다. (2026-10-18)
사용: python pshk_rivershape.py <ref_id> <k> [<k2> ...]
"""
import sys
import cv2
import numpy as np
from pshk_common import WORK, poster
rid = sys.argv[1]
ks = [int(k) for k in sys.argv[2:]]
lbl = np.load(f"{WORK}/{rid}_kmeans_lbl.npy")
img = poster(rid)
m = np.isin(lbl, ks).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
vis = (img * 0.35).astype(np.uint8)
vis[m > 0] = (0, 255, 255)
for y in range(0, 1400, 50):
    cv2.line(vis, (0, y), (1000, y), (90, 90, 90) if y % 100 else (160, 160, 160), 1)
    cv2.putText(vis, str(y), (2, y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (200, 200, 200), 1)
for x in range(0, 1000, 50):
    cv2.line(vis, (x, 0), (x, 1400), (90, 90, 90) if x % 100 else (160, 160, 160), 1)
    cv2.putText(vis, str(x), (x + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (200, 200, 200), 1)
cv2.imwrite(f"{WORK}/{rid}_rivershape.png", vis)
np.save(f"{WORK}/{rid}_rivercluster.npy", m)
print("saved", m.mean())
