# -*- coding: utf-8 -*-
"""±30° 띠(길·강)의 세로 두께(열마다 연속 구간 길이) 분포. 세로 두께 t_y = 다른 지면 축 방향 화면 길이,
화면 수직 폭 d = t_y * cos30 = 0.866 t_y. 사용: python -I tny_bandrun.py <ref> <class:1|2> [close_k]"""
import os, sys, json
import cv2, numpy as np
OUT = "/Users/um-yunsang/roman-concrete-private-refs/.work/out/refs-analysis"
ref = sys.argv[1]; c = int(sys.argv[2]); k = int(sys.argv[3]) if len(sys.argv) > 3 else 15
cls = np.load(os.path.join(OUT, f"{ref}_class.npy"))
m = (cls == c).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((k, k), np.uint8))
runs = []
for x in range(0, m.shape[1], 10):
    col = m[:, x].astype(np.int8)
    d = np.diff(np.concatenate([[0], col, [0]]))
    st, en = np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]
    for a, b in zip(st, en):
        if b - a >= 12:
            runs.append(int(b - a))
runs = np.array(runs)
h, e = np.histogram(runs, bins=np.arange(10, 400, 5))
top = np.argsort(h)[::-1][:6]
print(ref, "class", c, "n", len(runs), "q25/50/75", np.percentile(runs, [25, 50, 75]).round(1).tolist(),
      "최빈 구간(px,빈도)", [(int(e[i]), int(h[i])) for i in top])
