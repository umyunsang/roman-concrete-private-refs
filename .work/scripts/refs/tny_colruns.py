# -*- coding: utf-8 -*-
"""지정 열(x)에서 클래스 띠의 세로 구간(시작·끝·두께)을 출력한다. 띠가 ±θ 축이면 화면 수직 폭 = 두께 × cos θ.
사용: python -I tny_colruns.py <ref> <class> <x1,x2,...> [y0] [y1] [close_k] [theta_deg]"""
import os, sys
import cv2, numpy as np
OUT = "/Users/um-yunsang/roman-concrete-private-refs/.work/out/refs-analysis"
ref = sys.argv[1]; c = int(sys.argv[2]); xs = [int(v) for v in sys.argv[3].split(",")]
y0 = int(sys.argv[4]) if len(sys.argv) > 4 else 0; y1 = int(sys.argv[5]) if len(sys.argv) > 5 else 2800
k = int(sys.argv[6]) if len(sys.argv) > 6 else 15; th = float(sys.argv[7]) if len(sys.argv) > 7 else 30.0
cls = np.load(os.path.join(OUT, f"{ref}_class.npy"))
m = cv2.morphologyEx((cls == c).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((k, k), np.uint8))
for x in xs:
    col = m[y0:y1, x].astype(np.int8); d = np.diff(np.concatenate([[0], col, [0]]))
    st, en = np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]
    runs = [(int(a + y0), int(b + y0), int(b - a), round((b - a) * np.cos(np.radians(th)) * 0.21, 1)) for a, b in zip(st, en) if b - a >= 15]
    print(f"{ref} cls{c} x{x}: (y시작, y끝, 세로두께px, 수직폭mm) {runs}")
