"""합성본에서 N 좌표 상자를 잘라 격자(25 단위)와 함께 저장한다.

사용: r3_crop.py <ref_id> <x0> <y0> <x1> <y1> <name> [격자간격=25]
"""
import os
import sys

import cv2

sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/refs")
from r3_common import OUT  # noqa: E402

ref_id = sys.argv[1]
x0, y0, x1, y1 = [int(v) for v in sys.argv[2:6]]
name = sys.argv[6]
step = int(sys.argv[7]) if len(sys.argv) > 7 else 25
im = cv2.imread(os.path.join(OUT, f"{ref_id}_comp2x.png"))
c = im[y0 * 2:y1 * 2, x0 * 2:x1 * 2].copy()
# 격자: N 좌표 step 단위
for gx in range((x0 // step + 1) * step, x1, step):
    X = (gx - x0) * 2
    col = (255, 0, 255) if gx % 100 == 0 else (200, 120, 255)
    cv2.line(c, (X, 0), (X, c.shape[0]), col, 1)
    if gx % 50 == 0:
        cv2.putText(c, str(gx), (X + 2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 255), 1, cv2.LINE_AA)
for gy in range((y0 // step + 1) * step, y1, step):
    Y = (gy - y0) * 2
    col = (255, 160, 0) if gy % 100 == 0 else (255, 210, 120)
    cv2.line(c, (0, Y), (c.shape[1], Y), col, 1)
    if gy % 50 == 0:
        cv2.putText(c, str(gy), (2, Y - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 120, 0), 1, cv2.LINE_AA)
os.makedirs(os.path.join(OUT, "crops"), exist_ok=True)
p = os.path.join(OUT, "crops", f"{ref_id}_{name}.png")
cv2.imwrite(p, c)
print(p, c.shape)
