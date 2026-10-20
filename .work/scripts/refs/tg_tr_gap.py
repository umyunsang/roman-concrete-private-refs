"""Trabacchi: 코어 상자 오른쪽 끝·콜로세움 중심에서 테베레 물 화소까지 최소 거리 (2026-10-18). 입력 이미지는 읽기만 한다.
사용: python -I tg_tr_gap.py <trabacchi_2.jpg>
"""
import sys
import cv2
import numpy as np
img = cv2.imread(sys.argv[1]); H, W = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV); h, s, v = [hsv[..., i].astype(int) for i in range(3)]
blue = (h >= 85) & (h <= 112) & (s >= 60) & (v >= 120)
blue[:int(0.085 * H)] = False
blue = cv2.morphologyEx(blue.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
# 기념물 파란 해칭을 빼려고 다리 끊김을 메운 뒤 가장 큰 연결 성분(테베레 주성분)의 실제 물 화소만 쓴다
cl = cv2.morphologyEx(blue * 255, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
n, L, st, _ = cv2.connectedComponentsWithStats(cl, 8)
main = 1 + int(np.argmax(st[1:, 4]))
blue = (L == main) & (blue > 0)
ys, xs = np.nonzero(blue)
stage_w = (0.964 - 0.036) * W
# 코어 상자 (0.355, 0.245, 0.565, 0.400)
x1, y0, y1 = 0.565 * W, 0.245 * H, 0.400 * H
sel = (ys >= y0) & (ys <= y1) & (xs >= x1)
print("코어 상자 오른쪽 끝 → 같은 높이 띠의 강 물 화소 최소 가로 거리:", round(float((xs[sel] - x1).min()), 1), "px =",
      round(float((xs[sel] - x1).min()) / stage_w * 100, 2), "% 무대 폭")
cx, cy = 0.385 * W, 0.330 * H
d = np.hypot(xs - cx, ys - cy)
i = int(np.argmin(d))
print("콜로세움 중심 → 최근접 강 물 화소:", round(float(d[i]), 1), "px, 위치 정규", (round(xs[i] / W, 3), round(ys[i] / H, 3)),
      ", 콜로세움 그림 폭(55.7px)의", round(float(d[i]) / 55.7, 2), "배, 무대 폭의", round(float(d[i]) / stage_w * 100, 1), "%")
