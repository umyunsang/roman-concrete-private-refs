"""지정한 점들의 RGB(3x3 평균)를 출력한다 (2026-10-18). 입력 이미지는 읽기만 한다.
사용: uv run --no-project --with pillow --with numpy python -I cpg_px.py <이미지> x,y x,y ...
"""
import sys
import numpy as np
from PIL import Image
im = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(int)
for a in sys.argv[2:]:
    x, y = map(int, a.split(","))
    p = im[max(0, y - 1):y + 2, max(0, x - 1):x + 2].reshape(-1, 3).mean(0)
    print(f"({x},{y}) #{int(p[0]):02x}{int(p[1]):02x}{int(p[2]):02x} {tuple(int(v) for v in p)}")
