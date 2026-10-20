"""바탕색(하늘 등)과의 색차로 '세계(지도) 시작선'을 열마다 찾는다 (2026-10-18). 입력 이미지는 읽기만 한다.
사용: uv run --no-project --with opencv-python-headless --with numpy python -I cpg_skyline.py <이미지> <R,G,B> <tol> <ystart> <run>
- 열마다 ystart 아래에서 바탕색과 ΔRGB>tol 인 화소가 run 개 이상 연속되는 첫 행을 찾는다.
"""
import sys
import cv2
import numpy as np
img = cv2.imread(sys.argv[1])[:, :, ::-1].astype(int)
ref = np.array(list(map(int, sys.argv[2].split(","))))
tol = float(sys.argv[3]); ys = int(sys.argv[4]); run = int(sys.argv[5])
H, W = img.shape[:2]
d = np.sqrt(((img - ref) ** 2).sum(-1))
non = d > tol
out = []
for x in range(0, W, 10):
    col = non[ys:, x]
    first = None
    c = 0
    for i, v in enumerate(col):
        c = c + 1 if v else 0
        if c >= run:
            first = ys + i - run + 1
            break
    out.append((x, first))
print(" ".join(f"{x}:{f}" for x, f in out))
vals = [f for _, f in out if f is not None]
print("min", min(vals), "median", int(np.median(vals)), "max", max(vals))
