# 신문 무대의 흙 측면(계단 챌판) 띠를 찾아 위치·방향·두께를 잰다.
import sys, cv2, numpy as np
out = sys.argv[1]
img = cv2.imread(f"{out}/np_art.png"); lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(int)
L, A, B = lab[..., 0] * 100 / 255, lab[..., 1] - 128, lab[..., 2] - 128
soil = ((L < 50) & (A < 2) & (B > 12)).astype(np.uint8)
soil[:480] = 0; soil[:, :300] = 0; soil[:, 1560:] = 0; soil[2760:] = 0
soil = cv2.morphologyEx(soil, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
n, lbl, st, cen = cv2.connectedComponentsWithStats(soil)
rows = []
for i in range(1, n):
    if st[i, 4] < 6000: continue
    ys, xs = np.where(lbl == i)
    pts = np.stack([xs, ys], 1).astype(np.float32)
    (cx, cy), (w, h), ang = cv2.minAreaRect(pts)
    # 띠의 긴 방향 각도(화면 위쪽 +)
    vx, vy, _, _ = cv2.fitLine(pts, cv2.DIST_L2, 0, 0.01, 0.01).ravel()
    a = np.degrees(np.arctan2(-vy, vx)); a = (a + 90) % 180 - 90
    # 두께: 띠 중심선에 수직인 방향의 퍼짐 대신, 각 x열의 세로 두께 중앙값
    cols = {}
    for x, y in zip(xs, ys): cols.setdefault(x, []).append(y)
    th = np.median([max(v) - min(v) + 1 for v in cols.values() if len(v) > 3]) if cols else 0
    rows.append((cy, cx, xs.min(), xs.max(), ys.min(), ys.max(), a, th, st[i, 4]))
rows.sort()
print("흙 측면 띠(위→아래): 중심(mm), x범위(mm), 방향, 세로 두께(mm), 면적")
for cy, cx, x0, x1, y0, y1, a, th, ar in rows:
    print(f"  중심({cx*0.21:5.0f},{cy*0.2121:5.0f})  x {x0*0.21:4.0f}~{x1*0.21:4.0f}  y {y0*0.2121:4.0f}~{y1*0.2121:4.0f}  {a:+6.1f}°  두께 {th*0.2121:4.1f}mm  {ar}px")
