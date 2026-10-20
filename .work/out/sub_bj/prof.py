# 임의 이미지 파일의 노란 잉크 행/열 투영 (x0 x1 y0 y1 범위 제한)
import sys, cv2, numpy as np
p = sys.argv[1]; mode = sys.argv[2]; x0, x1, y0, y1 = map(int, sys.argv[3:7]); thr = int(sys.argv[7]) if len(sys.argv) > 7 else 2
img = cv2.imread(p)[y0:y1, x0:x1].astype(int)
b, g, r = img[:, :, 0], img[:, :, 1], img[:, :, 2]
m = ((r > 200) & (g > 165) & (b < 110) & (g - b > 100)).astype(np.uint8)
prof = m.sum(axis=1 if mode == "rows" else 0); off = y0 if mode == "rows" else x0
on = prof >= thr; i = 0
while i < len(on):
    if on[i]:
        j = i
        while j < len(on) and on[j]: j += 1
        print(f"{mode} {i+off}-{j-1+off} ({j-i}px) max{prof[i:j].max()}"); i = j
    else: i += 1
