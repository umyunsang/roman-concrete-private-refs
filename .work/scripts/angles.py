# 고해상도 타일에서 선분을 검출해 길이 가중 방향 히스토그램을 만들고 주요 각도를 찾는다.
# 각도는 화면 기준, 오른쪽 위로 올라가면 +, 오른쪽 아래로 내려가면 - (도).
import sys, json, cv2, numpy as np
src = sys.argv[1]
lsd = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)
def peaks(angles, lengths, minlen):
    sel = lengths >= minlen
    a, w = angles[sel], lengths[sel]
    bins = np.arange(-90, 90.25, 0.25)
    h, _ = np.histogram(a, bins=bins, weights=w)
    hs = np.convolve(np.r_[h[-8:], h, h[:8]], np.ones(5) / 5, mode="same")[8:-8]
    out = []
    for i in np.argsort(hs)[::-1]:
        c = (bins[i] + bins[i + 1]) / 2
        if all(abs(c - o[0]) > 4 for o in out):
            win = (a > c - 2) & (a < c + 2)
            if win.sum() < 5: continue
            m = float(np.average(a[win], weights=w[win])); sd = float(np.sqrt(np.average((a[win] - m) ** 2, weights=w[win])))
            out.append((round(m, 2), round(sd, 2), int(win.sum()), round(float(w[win].sum()), 0)))
        if len(out) >= 6: break
    return out
rep = {}
for key in ["bj", "np"]:
    for c in ["01", "04", "05"]:
        g = cv2.imread(f"{src}/{key}_{c}.jpg", cv2.IMREAD_GRAYSCALE)
        segs = lsd.detect(g)[0].reshape(-1, 4)
        dx, dy = segs[:, 2] - segs[:, 0], segs[:, 3] - segs[:, 1]
        L = np.hypot(dx, dy)
        ang = np.degrees(np.arctan2(-dy, dx))            # 화면 위쪽을 +로
        ang = (ang + 90) % 180 - 90                        # [-90, 90)
        rep[f"{key}_{c}"] = peaks(ang, L, 25)
for k, v in rep.items():
    name = {"bj": "베이징", "np": "신문"}[k[:2]] + " 타일 " + k[3:]
    print(f"[{name}] 주요 방향(평균각°, 표준편차°, 선분 수, 길이합):")
    for m, sd, n, wsum in v:
        print(f"    {m:+7.2f}°  ±{sd:.2f}  {n:4d}개  {int(wsum)}px")
