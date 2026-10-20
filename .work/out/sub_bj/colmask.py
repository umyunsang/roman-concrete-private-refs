# 지정 색(허용오차) 마스크의 bbox / 행·열 투영
import sys, cv2, numpy as np
ART = "/Users/um-yunsang/roman-concrete-private-refs/.work/out/bj_art.png"
mode = sys.argv[1]; hexc = sys.argv[2]; tol = int(sys.argv[3]); x, y, w, h = map(int, sys.argv[4:8]); thr = int(sys.argv[8]) if len(sys.argv) > 8 else 1
c = np.array([int(hexc[i:i+2], 16) for i in (4, 2, 0)])  # BGR
img = cv2.imread(ART).astype(int); roi = img[y:y+h, x:x+w]
d = np.abs(roi - c).max(axis=2); m = (d <= tol).astype(np.uint8)
if mode == "bbox":
    ys, xs = np.nonzero(m)
    if len(xs) == 0: print("없음"); sys.exit()
    x0, x1, y0, y1 = xs.min()+x, xs.max()+x, ys.min()+y, ys.max()+y
    print(f"bbox x{x0}-{x1} y{y0}-{y1} (w{x1-x0+1} h{y1-y0+1}) | mm x{x0*0.21:.1f}-{x1*0.21:.1f} y{y0*0.2121:.1f}-{y1*0.2121:.1f} (w{(x1-x0+1)*0.21:.1f} h{(y1-y0+1)*0.2121:.1f})")
else:
    prof = m.sum(axis=1 if mode == "rows" else 0); off = y if mode == "rows" else x; sc = 0.2121 if mode == "rows" else 0.21
    on = prof >= thr; i = 0
    while i < len(on):
        if on[i]:
            j = i
            while j < len(on) and on[j]: j += 1
            print(f"{mode} {i+off}-{j-1+off} ({j-i}px={((j-i)*sc):.2f}mm) max{prof[i:j].max()}"); i = j
        else: i += 1
