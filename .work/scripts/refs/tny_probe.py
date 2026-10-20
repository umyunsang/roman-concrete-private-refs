# -*- coding: utf-8 -*-
"""색 표본 탐색: 지정한 아트 좌표 상자들의 Lab 통계와 대표 RGB를 출력한다."""
import os, sys, json
import cv2, numpy as np
ROOT = "/Users/um-yunsang/roman-concrete-private-refs"
OUT = os.path.join(ROOT, ".work/out/refs-analysis")
ref = sys.argv[1]
boxes = json.loads(sys.argv[2])
art = cv2.imread(os.path.join(OUT, f"{ref}_art.png"))
lab = cv2.cvtColor(art, cv2.COLOR_BGR2LAB).astype(np.float32)
lab[..., 0] *= 100 / 255.0; lab[..., 1] -= 128; lab[..., 2] -= 128
for name, (x0, y0, x1, y1) in boxes.items():
    px = lab[y0:y1, x0:x1].reshape(-1, 3)
    rgb = art[y0:y1, x0:x1].reshape(-1, 3)[:, ::-1]
    Z = px.copy()
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    k = 3 if len(Z) > 50 else 1
    _, lab_k, cen = cv2.kmeans(Z, k, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    cnt = np.bincount(lab_k.ravel(), minlength=k)
    order = np.argsort(cnt)[::-1]
    s = []
    for i in order:
        m = lab_k.ravel() == i
        c = rgb[m].mean(0).astype(int)
        s.append(f"{100*cnt[i]/len(Z):.0f}% L{cen[i][0]:.1f} a{cen[i][1]:.1f} b{cen[i][2]:.1f} #{c[0]:02x}{c[1]:02x}{c[2]:02x}")
    print(name, "| ".join(s))
