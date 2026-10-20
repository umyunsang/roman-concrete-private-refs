"""Trabacchi 상단 띠(y<0.056)의 빨간 제목·검은 글자 상자를 잰다 (2026-10-18). 입력 이미지는 읽기만 한다.
사용: python -I tg_tr_title.py <trabacchi_2.jpg>
"""
import sys
import cv2
import numpy as np
img = cv2.imread(sys.argv[1]); H, W = img.shape[:2]
band = img[:int(0.056*H)]
hsv = cv2.cvtColor(band, cv2.COLOR_BGR2HSV); h, s, v = [hsv[..., i].astype(int) for i in range(3)]
red = ((h <= 8) | (h >= 172)) & (s >= 100) & (v >= 120)
dark = (v < 110) & (s < 90)
for nm, m in [("빨간 제목", red), ("검은 글자", dark)]:
    ys, xs = np.nonzero(m)
    if not len(xs):
        print(nm, "없음"); continue
    cols = np.nonzero(m.sum(0) > 0)[0]
    # 열 묶음(간격 25px 이상이면 분리)
    groups, st = [], cols[0]
    for a, b in zip(cols, cols[1:]):
        if b - a > 25:
            groups.append((st, a)); st = b
    groups.append((st, cols[-1]))
    for g0, g1 in groups:
        sub = m[:, g0:g1+1]; yy = np.nonzero(sub.sum(1) > 0)[0]
        if (g1 - g0) < 15: continue
        print(f"{nm}: x {g0/W:.3f}~{g1/W:.3f}, y {yy.min()/H:.3f}~{yy.max()/H:.3f}, 글자 높이 {yy.max()-yy.min()+1}px")
