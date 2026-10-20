# 글자 획 방향 분석: 잉크 마스크의 그래디언트 방향 히스토그램에서 두 획 방향(가로획·세로획)을 찾는다.
# 사용: m08_stroke.py img x y w h ink(hex) tol
# 출력 각도: 화면 기준, 0=수평 오른쪽, +는 시계방향(오른쪽 아래), 범위 -90~90
import sys
import cv2
import numpy as np

img = cv2.imread(sys.argv[1])
x, y, w, h = map(int, sys.argv[2:6])
ink = sys.argv[6]
tol = float(sys.argv[7])
crop = img[y:y + h, x:x + w]
lab = cv2.cvtColor(crop, cv2.COLOR_BGR2LAB).astype(np.float32)
r, g, b = int(ink[0:2], 16), int(ink[2:4], 16), int(ink[4:6], 16)
ref = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2LAB).astype(np.float32)[0, 0]
m = (np.sqrt(((lab - ref) ** 2).sum(axis=2)) < tol).astype(np.float32)
m = cv2.GaussianBlur(m, (3, 3), 0.8)
gx = cv2.Sobel(m, cv2.CV_32F, 1, 0, ksize=3)
gy = cv2.Sobel(m, cv2.CV_32F, 0, 1, ksize=3)
mag = np.sqrt(gx ** 2 + gy ** 2)
ang = np.degrees(np.arctan2(gy, gx))  # 그래디언트 방향
stroke = (ang + 90.0) % 180.0  # 획(가장자리) 방향 0~180
stroke[stroke > 90] -= 180  # -90~90
sel = mag > 0.2
hist, edges = np.histogram(stroke[sel], bins=72, range=(-90, 90), weights=mag[sel])
# 원형 평활
hs = np.convolve(np.concatenate([hist[-2:], hist, hist[:2]]), np.ones(5) / 5, mode="valid")
order = np.argsort(hs)[::-1]
peaks = []
for i in order:
    c = (edges[i] + edges[i + 1]) / 2
    if all(min(abs(c - p), 180 - abs(c - p)) > 15 for p, _ in peaks):
        peaks.append((c, hs[i]))
    if len(peaks) == 3:
        break
tot = hs.sum()
for c, v in peaks:
    print("stroke dir %.1f deg  weight %.3f" % (c, v / tot))
