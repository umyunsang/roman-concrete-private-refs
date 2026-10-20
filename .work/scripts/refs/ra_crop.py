"""합성 아트(2000x2800)에서 영역을 잘라 1000x1400 정규 단위 격자를 덧그린다.
사용: ra_crop.py <ref> x0 y0 x1 y1 [step=25] [maxside=1400] [outname]
좌표 단위: 1000x1400 정규 격자(아트 px의 1/2).
"""
import sys
import cv2, numpy as np
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from ra_common import *

ref = sys.argv[1]
x0, y0, x1, y1 = [float(v) for v in sys.argv[2:6]]
step = float(sys.argv[6]) if len(sys.argv) > 6 else 25
maxside = int(sys.argv[7]) if len(sys.argv) > 7 else 1400
name = sys.argv[8] if len(sys.argv) > 8 else f"crop_{ref}_{int(x0)}_{int(y0)}_{int(x1)}_{int(y1)}.png"
art = cv2.imread(str(composite_path(ref)))
X0, Y0, X1, Y1 = int(x0 * 2), int(y0 * 2), int(x1 * 2), int(y1 * 2)
c = art[Y0:Y1, X0:X1].copy()
k = min(maxside / c.shape[1], maxside / c.shape[0], 3.0)
c = cv2.resize(c, (int(c.shape[1] * k), int(c.shape[0] * k)), interpolation=cv2.INTER_CUBIC if k > 1 else cv2.INTER_AREA)
ppu = 2 * k  # 화면 px per 정규 단위
def gx(u): return int(round((u - x0) * ppu))
def gy(u): return int(round((u - y0) * ppu))
ov = c.copy()
u = np.ceil(x0 / step) * step
while u <= x1:
    major = abs(u / (step * 4) - round(u / (step * 4))) < 1e-6
    col = (255, 0, 255) if major else (255, 120, 255)
    cv2.line(ov, (gx(u), 0), (gx(u), c.shape[0]), col, 2 if major else 1)
    u += step
u = np.ceil(y0 / step) * step
while u <= y1:
    major = abs(u / (step * 4) - round(u / (step * 4))) < 1e-6
    col = (255, 200, 0) if major else (255, 230, 120)
    cv2.line(ov, (0, gy(u)), (c.shape[1], gy(u)), col, 2 if major else 1)
    u += step
c = cv2.addWeighted(ov, 0.55, c, 0.45, 0)
# 라벨
u = np.ceil(x0 / step) * step
while u <= x1:
    if abs(u / (step * 2) - round(u / (step * 2))) < 1e-6:
        cv2.putText(c, f"{int(u)}", (gx(u) + 2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 3)
        cv2.putText(c, f"{int(u)}", (gx(u) + 2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    u += step
u = np.ceil(y0 / step) * step
while u <= y1:
    if abs(u / (step * 2) - round(u / (step * 2))) < 1e-6:
        cv2.putText(c, f"{int(u)}", (2, gy(u) - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 3)
        cv2.putText(c, f"{int(u)}", (2, gy(u) - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    u += step
out = WORK / name
cv2.imwrite(str(out), c)
print(out, c.shape)
