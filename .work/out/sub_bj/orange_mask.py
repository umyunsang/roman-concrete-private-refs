# 점 지도 위 지시선 추적용: 주황(노랑 헤어라인+빨강 혼색) 픽셀만 흰색으로 표시
# 사용: python orange_mask.py x y w h scale out.png
import sys
import cv2
import numpy as np

ART = "/Users/um-yunsang/roman-concrete-private-refs/.work/out/bj_art.png"
x, y, w, h, s = map(int, sys.argv[1:6])
out = sys.argv[6]
img = cv2.imread(ART)
roi = img[y:y + h, x:x + w]
b, g, r = [roi[:, :, i].astype(int) for i in range(3)]
orange = (r > 200) & (g > 85) & (g < 185) & (b < 90)
yellow = (r > 200) & (g >= 185) & (b < 120)
vis = np.zeros_like(roi)
vis[yellow] = (0, 90, 120)       # 점(노랑)은 어둡게
vis[orange] = (255, 255, 255)    # 주황(선 후보)은 흰색
vis = cv2.resize(vis, (w * s, h * s), interpolation=cv2.INTER_NEAREST)
# 10px 간격 눈금(원본 좌표)
for gx in range(0, w, 10):
    cv2.line(vis, (gx * s, 0), (gx * s, 6), (0, 0, 255), 1)
    if (x + gx) % 50 == 0:
        cv2.putText(vis, str(x + gx), (gx * s + 2, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
for gy in range(0, h, 10):
    cv2.line(vis, (0, gy * s), (6, gy * s), (0, 0, 255), 1)
    if (y + gy) % 50 == 0:
        cv2.putText(vis, str(y + gy), (8, gy * s + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
cv2.imwrite(out, vis)
