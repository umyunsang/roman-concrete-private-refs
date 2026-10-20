# 배경 빨강(웨이브 무늬 포함)이 아닌 픽셀의 바운딩 박스와 행/열 투영
import sys, cv2, numpy as np
ART = "/Users/um-yunsang/roman-concrete-private-refs/.work/out/bj_art.png"
mode = sys.argv[1]; x, y, w, h = map(int, sys.argv[2:6]); thr = int(sys.argv[6]) if len(sys.argv) > 6 else 5
img = cv2.imread(ART).astype(int); roi = img[y:y+h, x:x+w]
b, g, r = roi[:, :, 0], roi[:, :, 1], roi[:, :, 2]
bg = (r > 195) & (r < 240) & (g > 45) & (g < 80) & (b > 30) & (b < 70)
m = (~bg).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
if mode == "bbox":
    ys, xs = np.nonzero(m)
    print(f"비배경 bbox x{xs.min()+x}-{xs.max()+x} y{ys.min()+y}-{ys.max()+y} | mm x{(xs.min()+x)*0.21:.1f}-{(xs.max()+x)*0.21:.1f} y{(ys.min()+y)*0.2121:.1f}-{(ys.max()+y)*0.2121:.1f}")
else:
    prof = m.sum(axis=1 if mode == "rows" else 0); off = y if mode == "rows" else x
    on = prof >= thr; i = 0
    while i < len(on):
        if on[i]:
            j = i
            while j < len(on) and on[j]: j += 1
            print(f"{mode} {i+off}-{j-1+off} ({j-i}px) max{prof[i:j].max()}"); i = j
        else: i += 1
