# 신문 무대 바닥(판 윗면 합집합)의 실제 외곽선(지그재그)을 구해 등각 역투영(Z 동일)으로 평면 다각형을 만든다.
import cv2, numpy as np, json
img = cv2.imread("out/np_art.png"); lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(int)
L, A, B = lab[..., 0] * 100 / 255, lab[..., 1] - 128, lab[..., 2] - 128
top = ((L > 72) & (B > 6) & (B < 30) & (A > -6) & (A < 10)).astype(np.uint8)
top[:480] = 0; top[:, :330] = 0; top[:, 1460:] = 0; top[2700:] = 0
top = cv2.morphologyEx(top, cv2.MORPH_CLOSE, np.ones((41, 41), np.uint8))   # 기계·글자 구멍 메우기
n, lbl, st, _ = cv2.connectedComponentsWithStats(top)
i = 1 + int(np.argmax(st[1:, 4])); m = (lbl == i).astype(np.uint8)
c = max(cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
poly = cv2.approxPolyDP(c, 12, True).reshape(-1, 2).astype(float)
S3 = np.sqrt(3)
XY = np.stack([poly[:, 0] / S3 + poly[:, 1], -poly[:, 0] / S3 + poly[:, 1]], 1) * 0.21
print(f"바닥 외곽 꼭짓점 {len(poly)}개 (화면 mm → 평면 mm):")
for (x, y), (X, Y) in zip(poly, XY):
    print(f"  화면({x*0.21:5.0f},{y*0.2121:5.0f})mm → 평면 X {X:6.0f}, Y {Y:6.0f}")
edges = []
for j in range(len(poly)):
    p, q = poly[j], poly[(j + 1) % len(poly)]; d = q - p
    a = (np.degrees(np.arctan2(-d[1], d[0])) + 90) % 180 - 90
    edges.append(round(float(a)))
print("화면 변 각도:", edges)
vis = img.copy(); cv2.polylines(vis, [poly.astype(np.int32).reshape(-1, 1, 2)], True, (0, 0, 255), 6)
cv2.imwrite("out/np_floor_outline.jpg", cv2.resize(vis[400:2800, 250:1650], (700, 1200)), [cv2.IMWRITE_JPEG_QUALITY, 85])
# 평면 다각형 그림
pts = XY - XY.min(0) + 20; sc = 3.0
canvas = np.full((int(pts[:, 1].max() * sc + 60), int(pts[:, 0].max() * sc + 60), 3), 245, np.uint8)
cv2.fillPoly(canvas, [(pts * sc).astype(np.int32).reshape(-1, 1, 2)], (178, 212, 228))
cv2.polylines(canvas, [(pts * sc).astype(np.int32).reshape(-1, 1, 2)], True, (40, 60, 90), 3)
cv2.imwrite("out/np_floor_plan.png", canvas)
json.dump({"screen_mm": (poly * [0.21, 0.2121]).tolist(), "plan_mm": XY.tolist()}, open("out/np_floor.json", "w"), indent=1)
