"""투영 측정: 고해상 타일(아트 px)에서 OpenCV LSD 선분 -> 길이 가중 각도 히스토그램.
지도 영역(타이틀·패널·푸터 상자 밖)만 쓴다. 화면 각도: 수평 0, 반시계 +(y 위로).
출력: work/angles.json, work/angles_hist.png
"""
import json, sys
import cv2, numpy as np
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from ra_common import *

INK = json.load(open(WORK / "ink.json"))
res = {}
hist_rows = []
for ref, cfg in REFS.items():
    art = cv2.imread(str(composite_path(ref)))
    gray = cv2.cvtColor(art, cv2.COLOR_BGR2GRAY)
    excl = np.zeros(gray.shape, np.uint8)
    z = INK[ref]
    for b in [z["title"]["bbox"], z["footer"]["bbox"]] + [p["bbox"] for p in z["panels"]]:
        x0, y0, x1, y1 = [v * 2 for v in b]
        excl[max(0, y0 - 10):y1 + 10, max(0, x0 - 10):x1 + 10] = 1
    lsd = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)
    allang, alllen, panel_ang, panel_len = [], [], [], []
    per_tile = {}
    for tid in cfg["tiles"]:
        X, Y = TILE_EXPECT[tid]
        th = 934 if tid in (3, 4) else 933
        sub = gray[Y:Y + th, X:X + 1000]
        lines = lsd.detect(sub)[0]
        if lines is None:
            continue
        L = lines.reshape(-1, 4)
        x1, y1, x2, y2 = L.T
        ln = np.hypot(x2 - x1, y2 - y1)
        ang = np.degrees(np.arctan2(-(y2 - y1), x2 - x1))   # y 위로 +
        ang = (ang + 90) % 180 - 90                          # (-90, 90]
        mx, my = ((x1 + x2) / 2 + X).astype(int), ((y1 + y2) / 2 + Y).astype(int)
        inmap = excl[np.clip(my, 0, ART_H - 1), np.clip(mx, 0, ART_W - 1)] == 0
        keep = ln >= 25
        a_m, l_m = ang[keep & inmap], ln[keep & inmap]
        a_p, l_p = ang[keep & ~inmap], ln[keep & ~inmap]
        allang.append(a_m); alllen.append(l_m); panel_ang.append(a_p); panel_len.append(l_p)
        def peak(a, l, lo, hi):
            s = (a > lo) & (a < hi)
            if s.sum() < 5:
                return None
            # 길이 가중 중앙값 대신 가중 평균(±3° 창에서 반복)
            c = np.average(a[s], weights=l[s])
            for _ in range(3):
                s2 = (np.abs(a - c) < 2.0)
                c = np.average(a[s2], weights=l[s2])
            s2 = (np.abs(a - c) < 2.0)
            sd = float(np.sqrt(np.average((a[s2] - c) ** 2, weights=l[s2])))
            return {"deg": round(float(c), 2), "sd": round(sd, 2), "n": int(s2.sum()), "len_px": int(l[s2].sum())}
        per_tile[tid] = {"pos": peak(a_m, l_m, 20, 36), "neg": peak(a_m, l_m, -36, -20),
                         "vert": peak(np.where(a_m < 0, a_m + 180, a_m), l_m, 84, 96),
                         "horiz": peak(a_m, l_m, -4, 4)}
    a = np.concatenate(allang); l = np.concatenate(alllen)
    ap = np.concatenate(panel_ang); lp = np.concatenate(panel_len)
    bins = np.arange(-90, 90.5, 0.5)
    h, _ = np.histogram(a, bins=bins, weights=l)
    hp, _ = np.histogram(ap, bins=bins, weights=lp)
    tot = l.sum()
    def share(lo, hi):
        s = (np.abs(a) >= lo) & (np.abs(a) < hi)
        return round(float(l[s].sum() / tot * 100), 1)
    # 26.57(2:1)과 30(등각) 창 비교
    def win(c, w=1.5):
        s = np.abs(np.abs(a) - c) < w
        return round(float(l[s].sum() / tot * 100), 1)
    res[ref] = {"per_tile": per_tile,
                "share_pct": {"horiz(|a|<4)": share(0, 4), "ground_axes(20-36)": share(20, 36), "vertical(84-90)": share(84, 90.01)},
                "window_pct": {"26.57±1.5": win(26.565), "30.0±1.5": win(30.0)},
                "n_segments_map": int(len(a))}
    hist_rows.append((ref, h, hp))
    print(ref, json.dumps(res[ref], ensure_ascii=False))
json.dump(res, open(WORK / "angles.json", "w"), ensure_ascii=False, indent=1)
# 히스토그램 그림
Wd, Hd = 1500, 260
canvas = np.full((Hd * 3 + 40, Wd, 3), 255, np.uint8)
for k, (ref, h, hp) in enumerate(hist_rows):
    y0 = k * Hd + 20
    hh = h / h.max()
    for i, v in enumerate(hh):
        x = int(i / len(hh) * (Wd - 60)) + 40
        cv2.line(canvas, (x, y0 + Hd - 40), (x, y0 + Hd - 40 - int(v * (Hd - 70))), (60, 60, 200), 2)
    for deg, col in [(-30, (0, 160, 0)), (30, (0, 160, 0)), (-26.565, (200, 120, 0)), (26.565, (200, 120, 0)), (0, (120, 120, 120)), (90, (120, 120, 120)), (-90, (120, 120, 120))]:
        x = int((deg + 90) / 180 * (Wd - 60)) + 40
        cv2.line(canvas, (x, y0 + 10), (x, y0 + Hd - 40), col, 1)
    for deg in range(-90, 91, 15):
        x = int((deg + 90) / 180 * (Wd - 60)) + 40
        cv2.putText(canvas, str(deg), (x - 12, y0 + Hd - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
    cv2.putText(canvas, f"{ref}  map-area LSD (length-weighted, 0.5deg bins)  green=+-30  blue=+-26.57(2:1)", (50, y0 + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
cv2.imwrite(str(WORK / "angles_hist.png"), canvas)
