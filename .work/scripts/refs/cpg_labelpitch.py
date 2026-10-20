"""기울어진(±30°) 라벨 글줄의 줄 피치와 글자 높이를 잰다 (2026-10-18). 입력 이미지는 읽기만 한다.
사용: uv run --no-project --with opencv-python-headless --with numpy python -I cpg_labelpitch.py <이미지> <mm_per_px> <x0,y0,x1,y1> <기울기deg> <출력png>
- 영역을 잘라 글줄이 수평이 되도록 회전한 뒤, 어두운 잉크(밝기 < 기준) 행 투영으로 글줄 띠를 찾는다.
- 기울기: 글줄이 오른쪽으로 올라가면 +30, 내려가면 -30.
"""
import sys
import cv2
import numpy as np
img = cv2.imread(sys.argv[1])
mmpp = float(sys.argv[2])
x0, y0, x1, y1 = map(int, sys.argv[3].split(","))
ang = float(sys.argv[4])
roi = img[y0:y1, x0:x1]
h, w = roi.shape[:2]
M = cv2.getRotationMatrix2D((w / 2, h / 2), -ang, 1.0)  # 글줄을 수평으로
cos, sin = abs(M[0, 0]), abs(M[0, 1])
nw, nh = int(h * sin + w * cos), int(h * cos + w * sin)
M[0, 2] += nw / 2 - w / 2
M[1, 2] += nh / 2 - h / 2
rot = cv2.warpAffine(roi, M, (nw, nh), borderValue=(255, 255, 255))
g = cv2.cvtColor(rot, cv2.COLOR_BGR2GRAY).astype(int)
valid = ~(rot > 250).all(-1)
thr = float(sys.argv[6]) if len(sys.argv) > 6 else 30.0
bgv = np.median(g[valid])
ink = (g < bgv - thr) & valid
prof = ink.sum(1) / np.maximum(valid.sum(1), 1)
rows = prof > (float(sys.argv[7]) if len(sys.argv) > 7 else 0.04)
bands = []
i = 0
while i < len(rows):
    if rows[i]:
        j = i
        while j < len(rows) and rows[j]:
            j += 1
        if j - i >= 3:
            bands.append((i, j))
        i = j
    else:
        i += 1
print("글줄 띠(행 시작~끝, 높이 px→mm):")
for a, b in bands:
    print(f"  {a}~{b}  {b - a}px = {(b - a) * mmpp:.2f}mm")
if len(bands) > 2:
    cs = [ (a + b) / 2 for a, b in bands ]
    d = np.diff(cs)
    print("줄 중심 간격(px):", [round(v, 1) for v in d], "→ 중앙값", round(float(np.median(d)), 1), "px =", round(float(np.median(d)) * mmpp, 2), "mm")
cv2.imwrite(sys.argv[5], rot)
