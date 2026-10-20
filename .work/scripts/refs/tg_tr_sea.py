"""Trabacchi 지평선 띠(y 0.062~0.12)의 물(바다·호수) 화소를 열별로 세어 바다 띠의 x 범위와 두께를 잰다 (2026-10-18).
입력 이미지는 읽기만 한다. 사용: python -I tg_tr_sea.py <trabacchi_2.jpg>
"""
import sys
import cv2
import numpy as np
img = cv2.imread(sys.argv[1]); H, W = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV); h, s, v = [hsv[..., i].astype(int) for i in range(3)]
blue = (h >= 85) & (h <= 112) & (s >= 60) & (v >= 120)
y0, y1 = int(0.062*H), int(0.13*H)
inset = (int(0.4247*W), int(0.5703*W))
print("x 구간 | 물 화소 세로 두께 중앙값(px) | 물이 있는 행 범위(정규 y)")
for xa in np.arange(0.04, 0.97, 0.04):
    a, b = int(xa*W), int(min(0.964, xa+0.04)*W)
    if a >= inset[0] and b <= inset[1]:
        print(f"{xa:.2f}~{xa+0.04:.2f} | 인셋 | -"); continue
    col = blue[y0:y1, a:b]
    th = np.median(col.sum(0))
    rows = np.nonzero(col.mean(1) > 0.5)[0]
    rng = f"{(rows.min()+y0)/H:.3f}~{(rows.max()+y0)/H:.3f}" if len(rows) else "-"
    print(f"{xa:.2f}~{xa+0.04:.2f} | {th:.0f} | {rng}")
