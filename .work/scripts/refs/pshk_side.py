"""세로 줄 Lab L 단면을 촘촘히 출력(판 윗면→옆면→물·허공 경계 판독). 입력은 읽기만 한다. (2026-10-18)"""
import sys
import numpy as np
from pshk_common import composite2x, lab
rid, x, y0, y1, step = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
big, cov = composite2x(rid)
L = lab(big)
col = L[2 * y0:2 * y1, 2 * x - 2:2 * x + 3].mean(1)
print(rid, "x", x, "hires" if cov[2 * y0:2 * y1, 2 * x].mean() > 0.9 else "upscaled")
print(" ".join(f"{y0 + i / 2:.0f}:{v[0]:.0f}/{v[2]:.0f}" for i, v in enumerate(col) if i % (2 * step) == 0))
