# 신문 포스터 중앙 무대: 판 윗면(밝은 베이지)을 색으로 분할해 판별 다각형·꼭짓점을 구하고,
# 등각 역투영(Z=0 가정)으로 평면 치수를 계산한다. 결과 이미지는 out/np_terraces.jpg.
import sys, json, cv2, numpy as np
out = sys.argv[1]
img = cv2.imread(f"{out}/np_art.png"); lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(int)
L, A, B = lab[..., 0] * 100 / 255, lab[..., 1] - 128, lab[..., 2] - 128
m = ((L > 77) & (B > 8) & (B < 26) & (A > -5) & (A < 8)).astype(np.uint8) * 255
m[:480] = 0; m[:, :300] = 0; m[:, 1560:] = 0                      # 타이틀 띠·좌우 칼럼 제외
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
n, lbl, st, cen = cv2.connectedComponentsWithStats(m)
idx = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > 40000]
idx.sort(key=lambda i: cen[i][1])
vis = img.copy(); res = []
for k, i in enumerate(idx):
    comp = (lbl == i).astype(np.uint8) * 255
    cnts, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cnts, key=cv2.contourArea)
    hull = cv2.convexHull(c)
    poly = cv2.approxPolyDP(hull, 18, True).reshape(-1, 2)
    edges = []
    for j in range(len(poly)):
        p, q = poly[j], poly[(j + 1) % len(poly)]
        d = q - p; ang = np.degrees(np.arctan2(-d[1], d[0])); ang = (ang + 90) % 180 - 90
        edges.append((round(float(ang), 1), round(float(np.hypot(*d)), 0)))
    # 등각 역투영(Z=0): X = x/√3 + y, Y = -x/√3 + y  (단위: 화면 px와 같은 등각 길이)
    XY = np.stack([poly[:, 0] / np.sqrt(3) + poly[:, 1], -poly[:, 0] / np.sqrt(3) + poly[:, 1]], 1)
    span = XY.max(0) - XY.min(0)
    x, y, w, h = cv2.boundingRect(c)
    res.append({"판": chr(65 + k), "면적px": int(st[i, cv2.CC_STAT_AREA]), "화면박스": [int(x), int(y), int(x + w), int(y + h)],
                "꼭짓점수": len(poly), "변(각도,길이)": edges, "평면X폭": round(float(span[0]), 0), "평면Y폭": round(float(span[1]), 0)})
    cv2.polylines(vis, [poly.reshape(-1, 1, 2)], True, (0, 0, 255), 6)
    cv2.putText(vis, chr(65 + k), (int(cen[i][0]), int(cen[i][1])), cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 0, 255), 10)
cv2.imwrite(f"{out}/np_terraces.jpg", cv2.resize(vis, (800, 1120)), [cv2.IMWRITE_JPEG_QUALITY, 85])
json.dump(res, open(f"{out}/np_terraces.json", "w"), ensure_ascii=False, indent=1)
for r in res:
    bx = r["화면박스"]
    print(f"판 {r['판']}: 화면 x {bx[0]*0.21:.0f}~{bx[2]*0.21:.0f}mm, y {bx[1]*0.2121:.0f}~{bx[3]*0.2121:.0f}mm, 꼭짓점 {r['꼭짓점수']}개, 평면(Z=0) {r['평면X폭']*0.21:.0f}×{r['평면Y폭']*0.21:.0f}mm 상당")
    print("    변:", ", ".join(f"{a:+.1f}°/{l*0.21:.0f}mm" for a, l in r["변(각도,길이)"]))
