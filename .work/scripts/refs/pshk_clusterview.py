"""군집 몇 개를 색으로 보여 주는 확인 그림(축소). 입력은 읽기만 한다. (2026-10-18)
사용: python pshk_clusterview.py <ref_id> <out_suffix> k:BBGGRR ...
"""
import sys
import cv2
import numpy as np
from pshk_common import WORK, poster
rid, suf = sys.argv[1], sys.argv[2]
lbl = np.load(f"{WORK}/{rid}_kmeans_lbl.npy")
img = poster(rid)
vis = (img * 0.3).astype(np.uint8)
for a in sys.argv[3:]:
    k, c = a.split(":")
    vis[lbl == int(k)] = (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
cv2.imwrite(f"{WORK}/{rid}_cv_{suf}.png", cv2.resize(vis, (600, 840), interpolation=cv2.INTER_AREA))
