"""지정 좌표 주변(5x5) 중앙값 색을 뽑는다. 입력 이미지는 읽기만 한다. (2026-10-18)
사용: python -I pshk_sample.py <ref_id> name:x,y ...
"""
import sys
import cv2
import numpy as np
from pshk_common import composite2x
rid = sys.argv[1]
big, cov = composite2x(rid)
for a in sys.argv[2:]:
    name, xy = a.split(":")
    x, y = [int(float(v) * 2) for v in xy.split(",")]
    p = big[max(0, y - 3):y + 4, max(0, x - 3):x + 4].reshape(-1, 3)
    b, g, r = [int(v) for v in np.median(p, axis=0)]
    print(f"{name:14s} ({xy}) #{r:02x}{g:02x}{b:02x}")
