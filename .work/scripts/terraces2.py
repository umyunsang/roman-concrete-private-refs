# 판 윗면 분할 2차: 흙 측면(어두운 녹갈색 띠)을 경계로 삼아 판을 분리한다.
import sys, json, cv2, numpy as np
out = sys.argv[1]
img = cv2.imread(f"{out}/np_art.png"); lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(int)
L, A, B = lab[..., 0] * 100 / 255, lab[..., 1] - 128, lab[..., 2] - 128
top = ((L > 77) & (B > 8) & (B < 26) & (A > -5) & (A < 8))
soil = ((L < 50) & (A < 2) & (B > 12))                               # 녹갈색 흙·잔디 측면
roi = np.zeros(L.shape, bool); roi[480:2760, 300:1560] = True
top &= roi; soil &= roi
soil_d = cv2.dilate(soil.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
t = (top & ~soil_d).astype(np.uint8) * 255
t = cv2.morphologyEx(t, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
n, lbl, st, cen = cv2.connectedComponentsWithStats(t)
idx = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > 25000]
idx.sort(key=lambda i: cen[i][1])
vis = img.copy()
vis[soil] = (0.4 * vis[soil] + 0.6 * np.array([255, 0, 255])).astype(np.uint8)
res = []
for k, i in enumerate(idx):
    comp = (lbl == i).astype(np.uint8) * 255
    c = max(cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
    hull = cv2.convexHull(c); poly = cv2.approxPolyDP(hull, 15, True).reshape(-1, 2)
    x, y, w, h = cv2.boundingRect(c)
    edges = []
    for j in range(len(poly)):
        p, q = poly[j], poly[(j + 1) % len(poly)]; d = q - p
        a = np.degrees(np.arctan2(-d[1], d[0])); a = (a + 90) % 180 - 90
        edges.append([round(float(a), 1), int(np.hypot(*d))])
    res.append({"id": k, "area": int(st[i, 4]), "box": [int(x), int(y), int(x + w), int(y + h)], "poly": poly.tolist(), "edges": edges})
    cv2.polylines(vis, [poly.reshape(-1, 1, 2)], True, (0, 0, 255), 6)
    cv2.putText(vis, str(k), (int(cen[i][0]) - 20, int(cen[i][1]) + 20), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 8)
cv2.imwrite(f"{out}/np_terraces2.jpg", cv2.resize(vis[400:2800, 250:1650], (700, 1200)), [cv2.IMWRITE_JPEG_QUALITY, 85])
json.dump(res, open(f"{out}/np_terraces2.json", "w"), ensure_ascii=False, indent=1)
for r in res:
    b = r["box"]
    print(f"영역 {r['id']}: 면적 {r['area']}px, 화면 x {b[0]*0.21:.0f}~{b[2]*0.21:.0f}mm, y {b[1]*0.2121:.0f}~{b[3]*0.2121:.0f}mm | 변: " + ", ".join(f"{a:+.0f}°/{l*0.21:.0f}mm" for a, l in r["edges"]))
