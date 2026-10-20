"""Trabacchi 지도의 빨간·갈색 좌표 격자선(색인용)을 긴 직선 형태로 찾는다 (2026-10-18). 입력 이미지는 읽기만 한다.
사용: python -I tg_tr_grid.py <trabacchi_2.jpg>
"""
import sys
import cv2
import numpy as np
img = cv2.imread(sys.argv[1]); H, W = img.shape[:2]
b, g, r = [img[..., i].astype(int) for i in range(3)]
# 격자선: 주변보다 붉고 어두운 가는 선. 빨강 우세(r-g>40) & 녹색 낮음
red = ((r - g) > 45) & ((r - b) > 45) & (g < 150)
red = red.astype(np.uint8)
x0, y0, x1, y1 = int(0.036*W), int(0.062*H), int(0.964*W), int(0.945*H)
m = np.zeros_like(red); m[y0:y1, x0:x1] = red[y0:y1, x0:x1]
vl = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 60)))
hl = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (60, 1)))
cs = vl.sum(0); rs = hl.sum(1)
def peaks(arr, thr, scale):
    idx = np.nonzero(arr >= thr)[0]
    out = []
    for i in idx:
        if out and i - out[-1][-1] <= 3: out[-1].append(i)
        else: out.append([i])
    return [(round(np.mean(o) / scale, 4), int(arr[o].max())) for o in out]
print("수직 격자선 x(정규, 최대 길이 px):", peaks(cs, 120, W))
print("수평 격자선 y(정규, 최대 길이 px):", peaks(rs, 120, H))
