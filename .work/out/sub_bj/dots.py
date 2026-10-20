# 지시선 끝점 원형 점 크기 측정 (노랑 덩어리, 선 제거 위해 열림 연산)
import sys, cv2, numpy as np
ART = "/Users/um-yunsang/roman-concrete-private-refs/.work/out/bj_art.png"
img = cv2.imread(ART).astype(int)
for spec in " ".join(sys.argv[1:]).split(";"):
    p = spec.split()
    if not p: continue
    name = p[0]; cx, cy = int(p[1]), int(p[2]); r = 14
    roi = img[cy-r:cy+r, cx-r:cx+r]; b, g, rr = roi[:, :, 0], roi[:, :, 1], roi[:, :, 2]
    m = ((rr > 200) & (g > 150) & (b < 120)).astype(np.uint8)
    m2 = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(m2, 8)
    best = max(range(1, n), key=lambda i: st[i][4]) if n > 1 else None
    if best is None: print(name, "점 없음"); continue
    sx, sy, sw, sh, a = st[best]
    print(f"{name}: 점 bbox x{sx+cx-r}-{sx+cx-r+sw-1} y{sy+cy-r}-{sy+cy-r+sh-1} 지름≈{(sw+sh)/2:.0f}px = {(sw+sh)/2*0.21:.2f}mm 면적{a}")
