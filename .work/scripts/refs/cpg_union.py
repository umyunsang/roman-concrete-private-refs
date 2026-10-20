"""다각형·상자 합집합 면적을 무대 대비 %로 낸다 (2026-10-18). 이미지는 쓰지 않는다.
사용: uv run --no-project --with opencv-python-headless --with numpy python -I cpg_union.py W H x0,y0,x1,y1(무대) <도형.json>
도형.json: [{"poly":[[x,y],..]} | {"box":[x0,y0,x1,y1]}, ...]
"""
import json
import sys
import cv2
import numpy as np
W, H = int(sys.argv[1]), int(sys.argv[2])
sx0, sy0, sx1, sy1 = map(int, sys.argv[3].split(","))
shapes = json.load(open(sys.argv[4]))
m = np.zeros((H, W), np.uint8)
for s in shapes:
    if "poly" in s:
        cv2.fillPoly(m, [np.array(s["poly"], np.int32)], 1)
    else:
        x0, y0, x1, y1 = s["box"]
        m[y0:y1, x0:x1] = 1
st = m[sy0:sy1, sx0:sx1].sum()
print(f"합집합/무대 {st / ((sx1 - sx0) * (sy1 - sy0)) * 100:.2f}%  합집합/전체 {m.sum() / (W * H) * 100:.2f}%")
