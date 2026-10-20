"""세로 줄 색 단면(Lab L)과 강 띠 세로 두께. 입력 이미지는 읽기만 한다. (2026-10-18)"""
import sys
import cv2
import numpy as np
from pshk_common import WORK, poster, lab
mode = sys.argv[1]
if mode == "profile":
    rid, x = sys.argv[2], int(sys.argv[3])
    L = lab(poster(rid))
    col = L[:, x - 2:x + 3].mean(1)
    for y in range(0, 1400, 25):
        print(y, col[y].round(1))
elif mode == "thick":
    rid = sys.argv[2]
    m = np.load(f"{WORK}/{rid}_rivercluster.npy")
    for spec in sys.argv[3:]:
        x, ya, yb = [int(v) for v in spec.split(",")]
        c = m[ya:yb, x]
        runs, s = [], None
        for i, v in enumerate(c):
            if v and s is None:
                s = i
            if not v and s is not None:
                runs.append((ya + s, ya + i)); s = None
        if s is not None:
            runs.append((ya + s, yb))
        runs = [r for r in runs if r[1] - r[0] >= 8]
        print(f"x={x} y{ya}-{yb}: runs {runs} 세로 두께 {[r[1]-r[0] for r in runs]}")
