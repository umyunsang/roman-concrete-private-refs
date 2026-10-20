# 흐린 영역용 느슨한 노랑-주황 잉크 bbox (배경 빨강 제외)
import sys, cv2, numpy as np
ART = "/Users/um-yunsang/roman-concrete-private-refs/.work/out/bj_art.png"
img = cv2.imread(ART).astype(int)
for line in sys.stdin:
    p = line.split()
    if not p: continue
    name = p[0]; x, y, w, h = map(int, p[1:5])
    roi = img[y:y+h, x:x+w]; b, g, r = roi[:, :, 0], roi[:, :, 1], roi[:, :, 2]
    m = ((r > 215) & (g > 110) & (b < 70) & (g - b > 70)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    ys, xs = np.nonzero(m)
    if len(xs) == 0: print(name, "없음"); continue
    x0, x1, y0, y1 = xs.min()+x, xs.max()+x, ys.min()+y, ys.max()+y
    print(f"{name}: px x{x0}-{x1} y{y0}-{y1} (w{x1-x0+1} h{y1-y0+1}) | mm x{x0*0.21:.1f}-{x1*0.21:.1f} y{y0*0.2121:.1f}-{y1*0.2121:.1f} (w{(x1-x0+1)*0.21:.1f} h{(y1-y0+1)*0.2121:.1f})")
