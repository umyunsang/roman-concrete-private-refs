"""상자 안 '글자 잉크' 색: 국지 바탕과 색차 24 넘는 화소 중, 바탕과 가장 먼 상위 30%의 중앙값. 입력 이미지는 읽기만 한다. (2026-10-18)
사용: python -I pshk_ink.py <ref_id> name:x0,y0,x1,y1 ...
"""
import sys
import cv2
import numpy as np
from pshk_common import composite2x
rid = sys.argv[1]
big, cov = composite2x(rid)
for a in sys.argv[2:]:
    name, bb = a.split(":")
    x0, y0, x1, y1 = [int(float(v) * 2) for v in bb.split(",")]
    c = big[y0:y1, x0:x1]
    bg = cv2.medianBlur(c, 31)
    L1 = cv2.cvtColor(c, cv2.COLOR_BGR2LAB).astype(np.float32); L0 = cv2.cvtColor(bg, cv2.COLOR_BGR2LAB).astype(np.float32)
    d = np.sqrt(((L1 - L0) ** 2).sum(-1))
    m = d > 24
    if m.sum() < 10:
        print(name, "잉크 없음"); continue
    thr = np.percentile(d[m], 70)
    sel = c[(d >= thr) & m]
    b, g, r = [int(v) for v in np.median(sel, axis=0)]
    bb_ = np.median(bg.reshape(-1, 3), axis=0).astype(int)
    print(f"{name:16s} 잉크 #{r:02x}{g:02x}{b:02x}  바탕 #{bb_[2]:02x}{bb_[1]:02x}{bb_[0]:02x}  ({m.mean()*100:.0f}%)")
