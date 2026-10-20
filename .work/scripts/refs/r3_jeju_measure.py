"""제주 실측(정규 1000×1400, 원본 450×630 확대본 + 고해상 타일 50%).

- 바다 = 바탕(ΔE≤6). 섬 바닥색 두 가지: PLACES TO GO 연두(81,-19,12), BUS ROUTE 청록(84,-15.6,-2).
- 섬 실루엣 = 바닥색 마스크를 닫힘(15) 후 구멍 메우기. 위 오브젝트까지 포함.
- 섬 위 오브젝트 = 비배경 ∩ 섬 − 바닥색 − 가는 획(글자).
출력: jeju_measure.json, jeju_zones_dbg.png
"""
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/refs")
from r3_common import OUT, lab, load_norm, norm01, to_mm  # noqa: E402

ref = "203x-jeju"
im, _ = load_norm(ref)
L = lab(cv2.GaussianBlur(im, (3, 3), 0))
nonbg = cv2.imread(os.path.join(OUT, f"{ref}_nonbg.png"), 0) > 0
H, W = nonbg.shape


def near(c, t):
    return np.linalg.norm(L - np.array(c, np.float32), axis=2) < t


def fill_holes(m):
    m8 = m.astype(np.uint8)
    ff = m8.copy()
    mask = np.zeros((H + 2, W + 2), np.uint8)
    cv2.floodFill(ff, mask, (0, 0), 1)
    return (m8 | (1 - ff)) > 0


def box_of(m):
    ys, xs = np.nonzero(m)
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


band_places = np.zeros((H, W), bool)
band_places[898:1338, :] = True
band_bus = np.zeros((H, W), bool)
band_bus[505:898, :] = True
TEXTBOX = {"ANNEXED ISLANDS": [725, 1218, 954, 1330], "PLACES TO GO 제목": [98, 975, 475, 1003], "BUS ROUTE 제목": [48, 595, 222, 618]}
txt = np.zeros((H, W), bool)
for b in TEXTBOX.values():
    txt[b[1]:b[3], b[0]:b[2]] = True

green = near((81, -19, 12), 8) & band_places
teal = near((84.1, -15.6, -2.2), 6) & band_bus
k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))


def silhouette(ground, band, min_area):
    s = cv2.morphologyEx(ground.astype(np.uint8), cv2.MORPH_CLOSE, k) > 0
    s = fill_holes(s) & band
    n, lb, st, _ = cv2.connectedComponentsWithStats(s.astype(np.uint8), connectivity=8)
    comps = sorted([(st[i, cv2.CC_STAT_AREA], i) for i in range(1, n)], reverse=True)
    main = lb == comps[0][1]
    small = [(a, i) for a, i in comps[1:] if a >= min_area]
    return main, [(int(a), box_of(lb == i)) for a, i in small]


isl_p, small_p = silhouette(green | (nonbg & band_places & ~txt & near((81, -19, 12), 20)), band_places, 300)
isl_b, small_b = silhouette(teal, band_bus, 300)
np.save(os.path.join(OUT, "jeju_island_places.npy"), isl_p)
np.save(os.path.join(OUT, "jeju_island_bus.npy"), isl_b)
k5 = np.ones((5, 5), np.uint8)
objp = nonbg & isl_p & ~green & ~txt
objp_o = cv2.morphologyEx(objp.astype(np.uint8), cv2.MORPH_OPEN, k5) > 0
# 버스 노선도: 섬 위 선·정류장·요금 깃발(정보 도식) 비율
info_b = nonbg & isl_b & ~teal
res = {}
A_band_p = band_places.sum()
res["places_to_go"] = {
    "island_box_N": box_of(isl_p), "island_box01": norm01(box_of(isl_p)), "island_wh_mm": None,
    "island_area_pct_poster": round(100 * isl_p.sum() / (H * W), 1),
    "island_area_pct_band(y898~1338 전폭)": round(100 * isl_p.sum() / A_band_p, 1),
    "objects_pct_island(글자 제외)": round(100 * objp_o.sum() / isl_p.sum(), 1),
    "small_islands": small_p,
}
b = box_of(isl_p)
res["places_to_go"]["island_wh_mm"] = [round((b[2] - b[0]) * 0.42, 1), round((b[3] - b[1]) * 594 / 1400, 1)]
bb = box_of(isl_b)
res["bus_route"] = {"island_box_N": bb, "island_box01": norm01(bb),
                    "island_wh_mm": [round((bb[2] - bb[0]) * 0.42, 1), round((bb[3] - bb[1]) * 594 / 1400, 1)],
                    "island_area_pct_poster": round(100 * isl_b.sum() / (H * W), 1),
                    "info_ink_pct_island(노선·정류장·깃발·한라산)": round(100 * info_b.sum() / isl_b.sum(), 1),
                    "small_islands": small_b}
# 두 섬 실루엣의 중심·폭 비교(같은 축척·같은 자리인지)
for nm, m in (("places", isl_p), ("bus", isl_b)):
    ys, xs = np.nonzero(m)
    res[f"{nm}_centroid_N"] = [round(float(xs.mean()), 1), round(float(ys.mean()), 1)]
# 한라산 세 번: 생태 모형, 노선도 가운데, PLACES 가운데
HALLA = {
    "ECOSYSTEM 모형(산 몸체)": [262, 290, 610, 505],
    "BUS ROUTE 가운데 산": [415, 650, 555, 750],
    "PLACES 한라산 국립공원(산)": [418, 1036, 535, 1124],
}
res["hallasan"] = {}
for nm, (x0, y0, x1, y1) in HALLA.items():
    sub = nonbg[y0:y1, x0:x1] & ~(teal[y0:y1, x0:x1])
    if "PLACES" in nm:
        # 국립공원 산은 섬 바닥보다 짙은 초록·갈색: 바닥 연두 제외
        sub = sub & ~green[y0:y1, x0:x1]
    sub = cv2.morphologyEx(sub.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)) > 0
    ys, xs = np.nonzero(sub)
    bx = [x0 + int(xs.min()), y0 + int(ys.min()), x0 + int(xs.max()) + 1, y0 + int(ys.max()) + 1]
    res["hallasan"][nm] = {"box_N": bx, "box01": norm01(bx),
                           "wh_mm": [round((bx[2] - bx[0]) * 0.42, 1), round((bx[3] - bx[1]) * 594 / 1400, 1)],
                           "center_x_N": round((bx[0] + bx[2]) / 2, 1)}
res["textboxes_N"] = TEXTBOX
with open(os.path.join(OUT, "jeju_measure.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
vis = (im * 0.35 + 160).astype(np.uint8)
vis[isl_p] = (vis[isl_p] * 0.6 + np.array([40, 120, 40]) * 0.4).astype(np.uint8)
vis[isl_b] = (vis[isl_b] * 0.6 + np.array([120, 120, 20]) * 0.4).astype(np.uint8)
vis[objp_o] = im[objp_o]
for nm, d in res["hallasan"].items():
    x0, y0, x1, y1 = d["box_N"]
    cv2.rectangle(vis, (x0, y0), (x1, y1), (0, 0, 255), 2)
cv2.imwrite(os.path.join(OUT, "jeju_zones_dbg.png"), vis)
print(json.dumps(res, ensure_ascii=False, indent=1))

# --- 오브젝트 개수(연결 성분, 면적 ≥ 120 N²) ---
n, lb, st, cen = cv2.connectedComponentsWithStats(objp_o.astype(np.uint8), connectivity=8)
big = [(int(st[i, cv2.CC_STAT_AREA]), [int(st[i, 0]), int(st[i, 1]), int(st[i, 0] + st[i, 2]), int(st[i, 1] + st[i, 3])]) for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= 120]
big.sort(reverse=True)
areas = np.array([a for a, _ in big])
wh = np.array([[(b[2] - b[0]) * 0.42, (b[3] - b[1]) * 594 / 1400] for _, b in big])
print("PLACES 오브젝트 성분(≥120N²):", len(big), "면적 중앙값 mm²", round(float(np.median(areas)) * 0.42 * 0.4243, 0),
      "폭×높이 중앙값 mm", np.round(np.median(wh, 0), 1), "최대 3개", big[:3])
vis2 = (im * 0.4 + 150).astype(np.uint8)
for a, b in big:
    cv2.rectangle(vis2, (b[0], b[1]), (b[2], b[3]), (0, 0, 255), 1)
cv2.imwrite(os.path.join(OUT, "jeju_objects_dbg.png"), vis2)
