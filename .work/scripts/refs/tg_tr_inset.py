"""Trabacchi 인셋 상자(리도·E.U.R.)의 테두리선을 짧은 직선 검출로 확인한다 (2026-10-18). 입력 이미지는 읽기만 한다.
사용: python -I tg_tr_inset.py <trabacchi_2.jpg>
"""
import sys
import cv2
import numpy as np
img = cv2.imread(sys.argv[1]); H, W = img.shape[:2]
g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
dark = (g < 110).astype(np.uint8)
for nm, (x0, y0, x1, y1) in {"리도 인셋 부근": (0.40, 0.055, 0.60, 0.18), "E.U.R. 인셋 부근": (0.030, 0.80, 0.20, 0.955)}.items():
    a, b, c, d = int(x0*W), int(y0*H), int(x1*W), int(y1*H)
    sub = dark[b:d, a:c]
    hl = cv2.morphologyEx(sub, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (60, 1)))
    vl = cv2.morphologyEx(sub, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 45)))
    rows = [(i + b) / H for i in np.nonzero(hl.sum(1) >= 60)[0]]
    cols = [(j + a) / W for j in np.nonzero(vl.sum(0) >= 45)[0]]
    def runs(v):
        out = []
        for x in v:
            if out and x - out[-1][1] < 0.004: out[-1][1] = x
            else: out.append([x, x])
        return [f"{p:.4f}~{q:.4f}" for p, q in out]
    print(nm, "수평선 y:", runs(rows), " 수직선 x:", runs(cols))
