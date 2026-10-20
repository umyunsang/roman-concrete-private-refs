# 바닥 화살표 형상 분석: 마스크 윤곽을 다각형 근사하고, 꼭짓점 각도로 촉(가장 뾰족한 볼록 꼭짓점)과 꼬리 노치(오목 꼭짓점)를 찾는다.
import sys
import cv2
import numpy as np

img = cv2.imread(sys.argv[1])
lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
ref = cv2.cvtColor(np.uint8([[[0x40, 0x69, 0x5A]]]), cv2.COLOR_BGR2LAB).astype(np.float32)[0, 0]
pts_in = [tuple(map(int, p.split(","))) for p in sys.argv[2:]]
for (cx, cy) in pts_in:
    x0, y0 = cx - 30, cy - 20
    sub = lab[y0:y0 + 40, x0:x0 + 60]
    m = (np.sqrt(((sub - ref) ** 2).sum(axis=2)) < 22).astype(np.uint8)
    n, l, s, c = cv2.connectedComponentsWithStats(m, 8)
    if n < 2:
        print(cx, cy, "none")
        continue
    k = 1 + int(np.argmax(s[1:, 4]))
    mm = (l == k).astype(np.uint8) * 255
    big = cv2.resize(mm, (mm.shape[1] * 8, mm.shape[0] * 8), interpolation=cv2.INTER_LINEAR)
    _, big = cv2.threshold(big, 127, 255, cv2.THRESH_BINARY)
    cnts, _ = cv2.findContours(big, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cnt = max(cnts, key=cv2.contourArea)
    approx = cv2.approxPolyDP(cnt, 0.035 * cv2.arcLength(cnt, True), True).reshape(-1, 2).astype(np.float64)
    # 원래 좌표로
    P = approx / 8.0 + np.array([x0, y0])
    cen = P.mean(axis=0)
    out = []
    N = len(P)
    area_sign = np.sign(cv2.contourArea(approx.astype(np.float32), oriented=True))
    for i in range(N):
        a, b, cpt = P[i - 1], P[i], P[(i + 1) % N]
        v1, v2 = a - b, cpt - b
        ang = np.degrees(np.arccos(np.clip(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9), -1, 1)))
        cross = (b - a)[0] * (cpt - b)[1] - (b - a)[1] * (cpt - b)[0]
        convex = np.sign(cross) == -area_sign or True
        out.append((i, b, ang, cross))
    # 촉 = 중심에서 가장 먼 꼭짓점 중 각도가 가장 작은 것
    dists = [np.linalg.norm(b - cen) for (_, b, _, _) in out]
    tip_i = min(range(N), key=lambda i: out[i][2] - 0.5 * dists[i])
    tip = out[tip_i][1]
    d = tip - cen
    heading = np.degrees(np.arctan2(d[1], d[0]))
    print("arrow at (%d,%d): verts=%d tip=(%.1f,%.1f) centroid=(%.1f,%.1f) heading=%.1f deg (화면, 0=오른쪽, +=아래쪽)" % (
        cx, cy, N, tip[0], tip[1], cen[0], cen[1], heading))
    print("   verts:", "; ".join("(%.1f,%.1f) %.0f°" % (b[0], b[1], ang) for (_, b, ang, _) in out))
