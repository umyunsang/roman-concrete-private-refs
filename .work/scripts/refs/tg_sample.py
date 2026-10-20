"""지정한 정규 좌표 상자 안 화소의 HSV 분포를 출력한다 (2026-10-18). 입력 이미지는 읽기만 한다.
사용: python -I tg_sample.py <이미지> <x0> <y0> <x1> <y1>
"""
import sys
import cv2
import numpy as np
img = cv2.imread(sys.argv[1]); H, W = img.shape[:2]
x0, y0, x1, y1 = (float(v) for v in sys.argv[2:6])
c = img[int(y0*H):int(y1*H), int(x0*W):int(x1*W)]
hsv = cv2.cvtColor(c, cv2.COLOR_BGR2HSV).reshape(-1, 3).astype(int)
bgr = c.reshape(-1, 3).astype(int)
# 채도 높은 화소 중 붉은 계열 후보 상위
for lo, hi, nm in [(0, 7, 'H0-7'), (7, 12, 'H7-12'), (12, 22, 'H12-22'), (170, 180, 'H170-180')]:
    m = (hsv[:, 0] >= lo) & (hsv[:, 0] < hi) & (hsv[:, 1] > 60)
    if m.sum():
        print(nm, int(m.sum()), 'S med', int(np.median(hsv[m, 1])), 'V med', int(np.median(hsv[m, 2])), 'BGR med', np.median(bgr[m], 0).astype(int).tolist())
