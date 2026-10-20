"""가로쓰기 글자 영역의 잉크 행 범위(대문자 높이 근사)를 잰다 (2026-10-18). 입력 이미지는 읽기만 한다.
사용: uv run --no-project --with opencv-python-headless --with numpy python -I cpg_textheight.py <이미지> <mm_per_px> x0,y0,x1,y1 [...]
- 영역 안에서 배경(영역 테두리 중앙값 색)과 색차 > 60 인 화소를 잉크로 보고, 잉크가 있는 행의 첫·끝을 출력한다.
"""
import sys
import cv2
import numpy as np
img = cv2.imread(sys.argv[1])[:, :, ::-1].astype(int)
mmpp = float(sys.argv[2])
for a in sys.argv[3:]:
    x0, y0, x1, y1 = map(int, a.split(","))
    roi = img[y0:y1, x0:x1]
    border = np.concatenate([roi[0], roi[-1], roi[:, 0], roi[:, -1]])
    bg = np.median(border, axis=0)
    ink = np.sqrt(((roi - bg) ** 2).sum(-1)) > 60
    rows = np.where(ink.mean(1) > 0.02)[0]
    cols = np.where(ink.mean(0) > 0.02)[0]
    if rows.size == 0:
        print(a, "잉크 없음"); continue
    h = rows[-1] - rows[0] + 1
    w = cols[-1] - cols[0] + 1
    print(f"{a}: 잉크 행 {rows[0]+y0}~{rows[-1]+y0} (높이 {h}px = {h*mmpp:.2f}mm), 열 {cols[0]+x0}~{cols[-1]+x0} (폭 {w}px = {w*mmpp:.1f}mm)")
