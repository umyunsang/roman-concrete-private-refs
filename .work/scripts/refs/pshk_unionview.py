"""오브젝트 합집합·코어 덩어리 확인 그림(축소). 입력 이미지는 읽기만 한다. (2026-10-18)"""
import sys
import cv2
import numpy as np
from pshk_common import WORK, poster
rid = sys.argv[1]
img = poster(rid)
u = cv2.imread(f"{WORK}/{rid}_objunion.png", 0) > 0
vis = img.copy()
vis[u] = (0.45 * vis[u] + 0.55 * np.array([0, 255, 255])).astype(np.uint8)
cv2.imwrite(f"{WORK}/{rid}_union_view.png", cv2.resize(vis, (700, 980), interpolation=cv2.INTER_AREA))
