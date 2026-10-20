# -*- coding: utf-8 -*-
"""창 안 전역 잉크의 열·행 누적 프로파일(경계 판독용). 연결 성분 목록도 출력."""
import os, sys, json
import cv2, numpy as np
ROOT = "/Users/um-yunsang/roman-concrete-private-refs"
OUT = os.path.join(ROOT, ".work/out/refs-analysis")
ref = sys.argv[1]; x0, y0, x1, y1 = [int(v) for v in sys.argv[2:6]]
minpx = int(sys.argv[6]) if len(sys.argv) > 6 else 12
ink = (cv2.imread(os.path.join(OUT, f"{ref}_ink.png"), 0)[y0:y1, x0:x1] > 0).astype(np.uint8)
n, lab, st, cen = cv2.connectedComponentsWithStats(ink, 8)
order = np.argsort(st[1:, cv2.CC_STAT_AREA])[::-1] + 1
print("성분(면적 큰 순) x0,y0,x1,y1,area:")
for i in order[:25]:
    x, y, w, h, a = st[i]
    if a < minpx: continue
    print(f"  ({x0+x},{y0+y},{x0+x+w},{y0+y+h}) a{a}")
