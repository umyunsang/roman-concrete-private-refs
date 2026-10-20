# 등각 벽면(기준선 ±30°, 세로획 수직)에 붙은 라벨을 세로 전단으로 펴서 읽기·측정
# 사용: python deshear.py x y w h ang scale out.png [rows]
#   ang: 기준선 각도(반시계 +, 예: +30 = 오른쪽으로 올라감, -30 = 오른쪽으로 내려감)
#   세로 전단 y' = y + (x - x0) * tan(ang)  → 기준선 수평화, 세로 길이 보존
import sys
import math
import cv2
import numpy as np

ART = "/Users/um-yunsang/roman-concrete-private-refs/.work/out/bj_art.png"
x, y, w, h = map(int, sys.argv[1:5])
ang = float(sys.argv[5])
s = float(sys.argv[6])
out = sys.argv[7]
do_rows = len(sys.argv) > 8 and sys.argv[8] == "rows"
img = cv2.imread(ART)
t = math.tan(math.radians(ang))
pad = int(abs(t) * w) + 4
# 여유를 두고 잘라서 변환
y0 = max(0, y - pad)
roi = img[y0:y + h + pad, x:x + w]
H = roi.shape[0]
off = abs(t) * w if t < 0 else 0.0
M = np.float32([[1, 0, 0], [t, 1, off]])  # y' = y + t*x + off
dst = cv2.warpAffine(roi, M, (w, H + int(abs(t) * w) + 2), flags=cv2.INTER_LINEAR, borderValue=(52, 66, 223))
if do_rows:
    b, g, r = [dst[:, :, i].astype(int) for i in range(3)]
    m = ((r > 200) & (g > 165) & (b < 110) & (g - b > 100)).astype(np.uint8)
    prof = m.sum(axis=1)
    on = prof >= 2
    i = 0
    while i < len(on):
        if on[i]:
            j = i
            while j < len(on) and on[j]:
                j += 1
            print(f"줄 {i}-{j-1} 높이 {j-i}px = {(j-i)*0.2121:.2f}mm  최대밀도 {prof[i:j].max()}")
            i = j
        else:
            i += 1
dst = cv2.resize(dst, None, fx=s, fy=s, interpolation=cv2.INTER_LANCZOS4)
cv2.imwrite(out, dst)
