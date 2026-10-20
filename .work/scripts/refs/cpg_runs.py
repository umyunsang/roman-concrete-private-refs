"""한 열(또는 행)을 따라 지정 색(허용 오차 안)이 이어지는 구간을 찾는다 (2026-10-18). 입력 이미지는 읽기만 한다.
사용: uv run --no-project --with pillow --with numpy python -I cpg_runs.py <이미지> col|row <좌표> <시작> <끝> <R,G,B> <tol>
"""
import sys
import numpy as np
from PIL import Image
im = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(int)
mode, c, a, b = sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
ref = np.array(list(map(int, sys.argv[6].split(","))))
tol = float(sys.argv[7])
line = im[a:b, c] if mode == "col" else im[c, a:b]
ok = np.sqrt(((line - ref) ** 2).sum(-1)) < tol
runs = []
i = 0
while i < len(ok):
    if ok[i]:
        j = i
        while j < len(ok) and ok[j]:
            j += 1
        runs.append((a + i, a + j, j - i))
        i = j
    else:
        i += 1
print([r for r in runs if r[2] >= 4])
