# -*- coding: utf-8 -*-
"""새 위계 배치 사양 v2 검사: 투영 크기 위계, 겹침, 땅·바다·강, 길 접촉, 고리 거리, 히어로 군(실루엣·껍질·상자),
밀도 근사, 압축 지리(방위 오차·거리 지수). 사용: python -I v2_check.py <data_dir> <out_dir>"""
import json
import math
import sys

import cv2
import numpy as np

sys.path.insert(0, sys.argv[1])
import v2_data as D  # noqa: E402

OUT = sys.argv[2]
PX = 4.0
W, H = int(420 * PX), int(594 * PX)


def blank():
    return np.zeros((H, W), np.uint8)


def fill(m, pts):
    a = np.array([[int(round(x * PX)), int(round(y * PX))] for x, y in pts], np.int32)
    cv2.fillPoly(m, [a], 255)
    return m


def rect_pts(b):
    x0, y0, x1, y1 = b
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def rect_mask(b):
    return fill(blank(), rect_pts(b))


def circ_mask(c, d):
    m = blank()
    cv2.circle(m, (int(round(c[0] * PX)), int(round(c[1] * PX))), int(round(d / 2 * PX)), 255, -1)
    return m


def area_mm2(m):
    return float((m > 0).sum()) / (PX * PX)


def bbox(m):
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return None
    return [round(xs.min() / PX, 1), round(ys.min() / PX, 1), round((xs.max() + 1) / PX, 1), round((ys.max() + 1) / PX, 1)]


def ba(b):
    return round((b[2] - b[0]) * (b[3] - b[1]))


def plan_band(p0, p1, w):
    """평면 선분 p0→p1을 화면 수직 폭 w의 띠로(평면 반폭 = w / (2·cos30))."""
    hw = w / (2 * D.C30)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    nx, ny = -dy / L * hw, dx / L * hw
    return [D.to_screen(p0[0] + nx, p0[1] + ny), D.to_screen(p1[0] + nx, p1[1] + ny), D.to_screen(p1[0] - nx, p1[1] - ny), D.to_screen(p0[0] - nx, p0[1] - ny)]


stage = rect_mask(D.STAGE)

# ── 히어로(콜로세움): 팔각 받침 + 앞 세 변 옆면 + 벽
oct_ = D.hero_oct()
hero = fill(blank(), oct_)
for k in (7, 0, 1):
    a, b = oct_[k], oct_[(k + 1) % 8]
    fill(hero, [a, b, (b[0], b[1] + D.HERO_SIDE), (a[0], a[1] + D.HERO_SIDE)])
for wseg in D.HERO_WALLS:
    t = wseg["t0"]
    while t < wseg["t1"]:
        t2 = min(t + 3, wseg["t1"])
        p0, p1 = D.hero_ring_pt(t), D.hero_ring_pt(t2)
        q0, q1 = D.hero_ring_pt(t, wseg["h"]), D.hero_ring_pt(t2, wseg["h"])
        fill(hero, [p0, p1, q1, q0])
        t = t2
hero &= stage
hero_box = bbox(hero)
worksite = rect_mask(D.WORKSITE["box"])

# ── 강·바다
river = fill(blank(), D.river_polygon()) & stage
sea = fill(blank(), D.SEA) & stage
coast_line = blank()
cv2.line(coast_line, (0, int(D.COAST[0][1] * PX)), (int(D.COAST[1][0] * PX), int(D.COAST[1][1] * PX)), 255, 3)

# ── 길·수도교
roads = {}
for r in D.ROADS:
    roads[r["id"]] = fill(blank(), plan_band(r["plan"][0], r["plan"][1], r["w"])) & stage
a0 = D.to_screen(*D.AQUEDUCT_PLAN[0])
a1 = D.to_screen(*D.AQUEDUCT_PLAN[1])
aqueduct = fill(blank(), [a0, a1, (a1[0], a1[1] - D.AQUEDUCT_H), (a0[0], a0[1] - D.AQUEDUCT_H)]) & stage

# ── 오브젝트·정보 요소 상자
lm = {x["id"]: rect_mask(x["box"]) for x in D.LANDMARKS}
lm["L4"] = aqueduct.copy()        # 수도교는 상자 대신 아치 열 평행사변형
portus_shape = blank()
for _part, polys in D.portus_polys().items():
    for pg in polys:
        fill(portus_shape, pg)
portus_box_mask = lm["L6"].copy()
lm["L6"] = portus_shape            # 겹침·땅/바다 검사는 실제 외형으로, 위계는 상자로
bg = {x["id"]: rect_mask(x["box"]) for x in D.BACKGROUND}
props = {p["name"]: rect_mask(p["box"]) for p in D.PROPS}
details = {}
for d in D.DETAILS:
    details[d["id"]] = circ_mask(d["circle"]["c"], d["circle"]["d"]) if "circle" in d else rect_mask(d["box"])
panels = {p["id"]: rect_mask(p["rect"]) for p in D.PANELS}
title = rect_mask(D.TITLE["rect"])
labels = {lb["name"]: rect_mask(lb["box"]) for lb in D.LABELS}


def floor_poly(ft):
    ax, ay = ft["anchor"]
    L = ft["len"]
    if ft["baseline"].startswith("↘"):
        dx, dy = D.C30 * L, 0.5 * L
    else:
        dx, dy = D.C30 * L, -0.5 * L
    return [(ax, ay), (ax + dx, ay + dy), (ax + dx, ay + dy - 4.0), (ax, ay - 4.0)]


floors = {ft["name"]: fill(blank(), floor_poly(ft)) for ft in D.FLOOR_TEXT}

res = {"stage_area_mm2": D.STAGE_AREA, "poster_area_mm2": D.POSTER_AREA}

# ═════ 1. 투영 크기 위계(상자 면적) ═════
z1 = [d for d in D.DETAILS if d["id"] == "Z1"][0]
zr = z1["circle"]["d"] / 2
z1_box = [z1["circle"]["c"][0] - zr, z1["circle"]["c"][1] - zr, z1["circle"]["c"][0] + zr, z1["circle"]["c"][1] + zr]
objects = {"콜로세움(히어로)": hero_box}
for x in D.LANDMARKS:
    objects[x["name"]] = bbox(lm[x["id"]]) if x["id"] == "L4" else x["box"]
for x in D.BACKGROUND:
    objects[x["name"]] = x["box"]
tiers = {"Basic": {}, "Detail": {}, "Support": {}}
for p in D.PANELS:
    tiers[p["tier"]][f'{p["id"]} {p["name"]}'] = p["rect"]
for d in D.DETAILS:
    tiers["Detail"][f'{d["id"]} {d["name"]}'] = z1_box if d["id"] == "Z1" else d["box"]
tier_area = {t: {k: ba(v) for k, v in dct.items()} for t, dct in tiers.items()}
obj_area = {k: ba(v) for k, v in objects.items()}
hero_a = obj_area["콜로세움(히어로)"]
lm_areas = {x["name"]: obj_area[x["name"]] for x in D.LANDMARKS}
basic_min = min(tier_area["Basic"].items(), key=lambda kv: kv[1])
detail_max = max(tier_area["Detail"].items(), key=lambda kv: kv[1])
detail_min = min(tier_area["Detail"].items(), key=lambda kv: kv[1])
support = max(tier_area["Support"].items(), key=lambda kv: kv[1])
panel_max = max([v for t in ("Basic", "Detail", "Support") for v in tier_area[t].values()])
ves = obj_area[D.BACKGROUND[0]["name"]]
med_lm = float(np.median(list(lm_areas.values())))
checks = {
    "Core 지도 무대 > 모든 Basic·Detail·Support 요소": D.STAGE_AREA > panel_max,
    "콜로세움 = 최대 단일 오브젝트(≥ 표준 랜드마크 최대 × 1.1)": hero_a >= 1.1 * max(lm_areas.values()),
    "콜로세움 > 가장 큰 패널(제작 과정)": hero_a > panel_max,
    "Basic 각 요소 ≥ Detail 각 요소(최소 Basic ≥ 최대 Detail)": basic_min[1] >= detail_max[1],
    "Detail 각 요소 > Support(최소 Detail ≥ Support × 1.1)": detail_min[1] >= 1.1 * support[1],
    "베수비오 = 가장 작은 랜드마크급 지도 요소(≤ 랜드마크 최소 ÷ 1.1)": ves <= min(lm_areas.values()) / 1.1,
}
res["hierarchy"] = {
    "core_stage_mm2": D.STAGE_AREA, "hero_box": hero_box, "hero_wh": [round(hero_box[2] - hero_box[0], 1), round(hero_box[3] - hero_box[1], 1)], "hero_area": hero_a,
    "landmark_areas": lm_areas, "landmark_median": round(med_lm), "hero_over_landmark_median": round(hero_a / med_lm, 2),
    "vesuvius_area": ves,
    "tier_areas": tier_area,
    "basic_min": list(basic_min), "detail_max": list(detail_max), "detail_min": list(detail_min), "support": list(support),
    "ratio_basicmin_over_detailmax": round(basic_min[1] / detail_max[1], 3),
    "ratio_detailmin_over_support": round(detail_min[1] / support[1], 3),
    "checks": {k: bool(v) for k, v in checks.items()},
}
res["objects_boxes"] = {k: {"box": v, "wh": [round(v[2] - v[0], 1), round(v[3] - v[1], 1)], "area": ba(v)} for k, v in objects.items()}

# ═════ 2. 겹침 검사 ═════
shapes = {"타이틀": title}
for k, m in panels.items():
    shapes["패널 " + k] = m
shapes["콜로세움"] = hero
shapes["공사장"] = worksite
for x in D.LANDMARKS:
    shapes[x["id"] + " " + x["name"]] = lm[x["id"]]
for x in D.BACKGROUND:
    shapes[x["id"] + " " + x["name"]] = bg[x["id"]]
for k, m in props.items():
    shapes["소품 " + k] = m
for k, m in details.items():
    shapes["Detail " + k] = m
for k, m in labels.items():
    shapes["라벨 " + k] = m
for k, m in floors.items():
    shapes["바닥 글 " + k] = m
for r in D.ROADS:
    shapes["길 " + r["id"]] = roads[r["id"]]
shapes["강"] = river
for ld in D.LEADERS:
    m = blank()
    pts = ld["pts"]
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        cv2.line(m, (int(round(x0 * PX)), int(round(y0 * PX))), (int(round(x1 * PX)), int(round(y1 * PX))), 255, 2)
    shapes["지시선 " + ld["name"]] = m

allowed = set(map(frozenset, [
    ["콜로세움", "공사장"],
    ["길 R1", "콜로세움"], ["길 R4", "콜로세움"], ["길 R4", "소품 테베레 하역장(엠포리움: 돌 부두·기중기·창고)"],
    ["길 R4", "소품 재료 수레"], ["길 R4", "강"],
    ["길 R2", "길 R3"], ["길 R2", "L2 트라야누스 시장"], ["길 R2", "L3 카라칼라 욕장(절개)"], ["길 R3", "L1 판테온"],
    ["길 R1", "L5 카이킬리아 메텔라 무덤"], ["길 R2", "L1 판테온"], ["길 R1", "소품 아피아 가도 수레"],
    ["강", "소품 테베레 하역장(엠포리움: 돌 부두·기중기·창고)"], ["강", "소품 바지선 1(올라가는 배)"], ["강", "소품 바지선 2(내려가는 배)"],
    ["강", "바닥 글 TIBERIS 테베레강"], ["강", "라벨 바지선"],
    ["L3 카라칼라 욕장(절개)", "L4 수도교 아치 열"],
    ["V 베수비오(지도 배경, 가장 먼 곳)", "소품 포도밭 농장(베수비오 밑동)"], ["V 베수비오(지도 배경, 가장 먼 곳)", "라벨 베수비오(Vesuvius)"],
    ["소품 테베레 하역장(엠포리움: 돌 부두·기중기·창고)", "콜로세움"],
    ["라벨 테베레 하역장·석회 가마", "소품 테베레 하역장(엠포리움: 돌 부두·기중기·창고)"],
    ["라벨 콜로세움 공사장(⑤ 다져 넣기)", "공사장"],
    ["바닥 글 VIA APPIA 아피아 가도 → 캄파니아", "길 R1"],
    ["바닥 글 OSTIA 오스티아", "소품 오스티아(창고 몇 채)"],
    ["바닥 글 COLLI ALBANI 알바노 구릉 — 로마 건물의 화산재", "L4 수도교 아치 열"],
    ["지시선 제작 과정 ⑥ → 콜로세움 공사장(지도→패널, 런던 BUS LINE 9 문법)", "공사장"],
    ["지시선 제작 과정 ⑥ → 콜로세움 공사장(지도→패널, 런던 BUS LINE 9 문법)", "패널 B"],
    ["지시선 콜로세움 기초 절개 → 확대 창 Z1", "콜로세움"], ["지시선 콜로세움 기초 절개 → 확대 창 Z1", "Detail Z1"],
    ["지시선 확대 창 Z1 → Detail 패널 D", "Detail Z1"], ["지시선 확대 창 Z1 → Detail 패널 D", "패널 D"],
    ["지시선 판테온 돔 → 콜아웃 C1", "L1 판테온"], ["지시선 판테온 돔 → 콜아웃 C1", "Detail C1"],
    ["지시선 클라우디우스 외항 방파제 → 콜아웃 C2", "L6 포르투스 항"], ["지시선 클라우디우스 외항 방파제 → 콜아웃 C2", "Detail C2"],
    ["지시선 메텔라 무덤 → 콜아웃 C4", "L5 카이킬리아 메텔라 무덤"], ["지시선 메텔라 무덤 → 콜아웃 C4", "Detail C4"],
    ["지시선 메텔라 무덤 → 콜아웃 C4", "소품 교외 빌라(포도밭 농가)"],
]))
keys = list(shapes)
over = []
for i in range(len(keys)):
    for j in range(i + 1, len(keys)):
        a, b = keys[i], keys[j]
        if frozenset([a, b]) in allowed:
            continue
        inter = area_mm2(shapes[a] & shapes[b])
        if inter > 0.5:
            over.append([a, b, round(inter, 1)])
res["overlaps_not_allowed"] = over

# ═════ 3. 땅 요소가 바다·강에 들어갔는지 ═════
land_items = {"콜로세움": hero, "공사장": worksite}
for x in D.LANDMARKS:
    if x["id"] != "L6":
        land_items[x["name"]] = lm[x["id"]]
for p in D.PROPS:
    if p["on"] == "땅":
        land_items[p["name"]] = props[p["name"]]
res["land_in_sea"] = {k: round(area_mm2(m & sea), 1) for k, m in land_items.items() if area_mm2(m & sea) > 0.5}
res["land_in_river"] = {k: round(area_mm2(m & river), 1) for k, m in land_items.items() if area_mm2(m & river) > 0.5}
water_items = {p["name"]: props[p["name"]] for p in D.PROPS if p["on"] == "물"}
res["water_items_on_land_pct"] = {k: round(100 * (1 - area_mm2(m & (sea | river)) / max(area_mm2(m), 1)), 1) for k, m in water_items.items()}
port = portus_shape
res["portus_land_sea_split_mm2"] = {"육지": round(area_mm2(port & ~sea & stage)), "바다": round(area_mm2(port & sea))}

# ═════ 4. 길·강·해안·수도교·히어로 접촉(도쿄: 오브젝트 19/23이 길 2.5mm 안) ═════
net = blank()
for m in roads.values():
    net |= m
net |= river | coast_line | aqueduct
dist_t = cv2.distanceTransform(255 - net, cv2.DIST_L2, 5) / PX
contact = {}
for x in D.LANDMARKS:
    m = lm[x["id"]]
    others = net.copy()
    if x["id"] == "L4":
        others = (net & ~aqueduct) | lm["L3"]
    d_t = cv2.distanceTransform(255 - others, cv2.DIST_L2, 5) / PX
    contact[x["name"]] = round(float(d_t[m > 0].min()), 1)
contact["콜로세움"] = round(float(dist_t[hero > 0].min()), 1)
res["contact_distance_mm"] = contact
res["contact_ok_le_2.5mm"] = {k: v <= 2.5 for k, v in contact.items()}

# ═════ 5. 히어로 중심에서 랜드마크 바닥점까지(파리 127~263mm, 베이징 140~340mm) ═════
hx, hy = D.HERO_C


def base_pt(b):
    return ((b[0] + b[2]) / 2, b[3] - 0.15 * (b[3] - b[1]))


ring = {}
side = {"왼쪽": [], "오른쪽": []}
for x in D.LANDMARKS + D.BACKGROUND:
    b = objects[x["name"]]
    px, py = base_pt(b)
    ring[x["name"]] = round(math.hypot(px - hx, py - hy))
    side["왼쪽" if px < hx else "오른쪽"].append(x["name"])
res["ring_distance_mm"] = ring
res["ring_range_median"] = [min(ring.values()), max(ring.values()), round(float(np.median(list(ring.values()))))]
res["left_right"] = {k: len(v) for k, v in side.items()}

# ═════ 6. 히어로 군(콜로세움 + 공사장 + 하역장 띠 소품 + 하역장 길 + 인접 테베레 구간) — 레퍼런스 코어 군과 같은 측정법 ═════
hz = hero | worksite | roads["R4"]
for nm in ["테베레 하역장(엠포리움: 돌 부두·기중기·창고)", "석회 가마", "재료 수레", "바지선 2(내려가는 배)"]:
    hz |= props[nm]
riv_part = river.copy()
riv_part[:, : int(100 * PX)] = 0
riv_part[:, int(232 * PX):] = 0
hz |= riv_part
hz &= stage
ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(13 * PX) | 1, int(13 * PX) | 1))
closed = cv2.morphologyEx(hz, cv2.MORPH_CLOSE, ker)
cnts, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
sil = blank()
cv2.drawContours(sil, cnts, -1, 255, -1)
sil &= stage
hull = blank()
cv2.fillPoly(hull, [cv2.convexHull(np.vstack(cnts))], 255)
hull &= stage
cb = bbox(hz)
M = cv2.moments(sil)
cx, cy = M["m10"] / M["m00"] / PX, M["m01"] / M["m00"] / PX
res["hero_cluster"] = {
    "definition": "콜로세움(받침·벽) + 공사장 + 하역장·석회 가마·수레·바지선 2 + 하역장 길 + 테베레 구간(x 100~232)",
    "bbox": cb, "bbox_wh": [round(cb[2] - cb[0], 1), round(cb[3] - cb[1], 1)],
    "bbox_pct_stage": round(100 * ba(cb) / D.STAGE_AREA, 1),
    "hull_pct_stage": round(100 * area_mm2(hull) / D.STAGE_AREA, 1), "hull_mm2": round(area_mm2(hull)),
    "silhouette_pct_stage": round(100 * area_mm2(sil) / D.STAGE_AREA, 1), "silhouette_mm2": round(area_mm2(sil)),
    "centroid_mm": [round(cx, 1), round(cy, 1)], "centroid_norm_poster": [round(cx / 420, 3), round(cy / 594, 3)],
    "aspect_h_over_w": round((cb[3] - cb[1]) / (cb[2] - cb[0]), 2),
}

# 6-2. 도심·시내 코어 군(히어로 군 + 판테온 + 트라야누스 시장 + 카라칼라 욕장 + 시내 길 2): 상하이·홍콩·도쿄처럼 건물 여러 채를 담는 코어 군과 비교
hz2 = hz | rect_mask(D.LANDMARKS[0]["box"]) | rect_mask(D.LANDMARKS[1]["box"]) | rect_mask(D.LANDMARKS[2]["box"]) | roads["R2"] | roads["R3"]
hz2 &= stage
closed2 = cv2.morphologyEx(hz2, cv2.MORPH_CLOSE, ker)
cnts2, _ = cv2.findContours(closed2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
sil2 = blank()
cv2.drawContours(sil2, cnts2, -1, 255, -1)
sil2 &= stage
hull2 = blank()
cv2.fillPoly(hull2, [cv2.convexHull(np.vstack(cnts2))], 255)
hull2 &= stage
cb2 = bbox(hz2)
M2 = cv2.moments(sil2)
res["core_group_city"] = {
    "definition": "히어로 군 + 판테온 + 트라야누스 시장 + 카라칼라 욕장 + 시내 길 2개(도심·시내 구역)",
    "bbox": cb2, "bbox_wh": [round(cb2[2] - cb2[0], 1), round(cb2[3] - cb2[1], 1)], "bbox_pct_stage": round(100 * ba(cb2) / D.STAGE_AREA, 1),
    "hull_pct_stage": round(100 * area_mm2(hull2) / D.STAGE_AREA, 1), "silhouette_pct_stage": round(100 * area_mm2(sil2) / D.STAGE_AREA, 1),
    "silhouette_mm2": round(area_mm2(sil2)), "hull_mm2": round(area_mm2(hull2)),
    "centroid_norm_poster": [round(M2["m10"] / M2["m00"] / PX / 420, 3), round(M2["m01"] / M2["m00"] / PX / 594, 3)],
    "components_after_close": len(cnts2),
}

# ═════ 7. 밀도 근사(Core 오브젝트 / 지도 무대) ═════
core_union = (hero | worksite) & stage
alpha = {"L1": 0.7, "L2": 0.7, "L3": 0.7, "L5": 0.7, "L6": 0.6}
lm_est = sum(alpha[x["id"]] * ba(x["box"]) for x in D.LANDMARKS if x["id"] in alpha) + 0.45 * area_mm2(aqueduct)
bg_est = 0.6 * ba(D.BACKGROUND[0]["box"])
prop_est = 0.6 * sum(ba(p["box"]) for p in D.PROPS)
obj_est = area_mm2(core_union) + lm_est + bg_est + prop_est
planted_est = sum(pl["cover"] * ba(pl["box"]) for pl in D.PLANTED)
res["density_estimate"] = {
    "hero_union_mm2": round(area_mm2(core_union)), "landmarks_alpha_est_mm2": round(lm_est), "background_alpha_est_mm2": round(bg_est), "props_alpha_est_mm2": round(prop_est),
    "objects_pct_stage_est": round(100 * obj_est / D.STAGE_AREA, 1),
    "objects_pct_poster_est": round(100 * obj_est / D.POSTER_AREA, 1),
    "planted_cover_est_mm2": round(planted_est),
    "objects_plus_planted_pct_stage_est": round(100 * (obj_est + planted_est) / D.STAGE_AREA, 1),
    "objects_plus_planted_pct_poster_est": round(100 * (obj_est + planted_est) / D.POSTER_AREA, 1),
    "river_pct_stage": round(100 * area_mm2(river) / D.STAGE_AREA, 1),
    "sea_pct_stage": round(100 * area_mm2(sea) / D.STAGE_AREA, 1),
    "roads_pct_stage": round(100 * area_mm2(sum_r := (roads["R1"] | roads["R2"] | roads["R3"] | roads["R4"])) / D.STAGE_AREA, 1),
    "panel_area_pct_poster": round(100 * sum(ba(p["rect"]) for p in D.PANELS) / D.POSTER_AREA, 1),
    "map_panels_cover_stage_pct": round(100 * area_mm2(panels["S"] & stage) / D.STAGE_AREA, 1),
}

# ═════ 8. 압축 지리(방위·거리) ═════
lat0, lon0 = D.GEO_COLOSSEUM


def real_vec(geo):
    lat, lon = geo
    dE = (lon - lon0) * 111.32 * math.cos(math.radians(lat0))
    dN = (lat - lat0) * 110.57
    return dE, dN


def plan_vec(screen_pt):
    X0, Y0 = D.HERO_C_PLAN
    X, Y = D.to_plan(*screen_pt)
    dX, dY = X - X0, Y - Y0
    right = (dX - dY) / math.sqrt(2)
    up = -(dX + dY) / math.sqrt(2)
    return right, up


items = []
for x in D.LANDMARKS + D.BACKGROUND:
    items.append({"name": x["name"], "geo": x["geo"], "screen": base_pt(objects[x["name"]])})
for e in D.GEO_EXTRA:
    items.append({"name": e["name"], "geo": e["geo"], "screen": e["screen"]})
for it in items:
    dE, dN = real_vec(it["geo"])
    it["real_km"] = math.hypot(dE, dN)
    it["real_bearing"] = math.degrees(math.atan2(dE, dN)) % 360
    r, u = plan_vec(it["screen"])
    it["plan_mm"] = math.hypot(r, u)
    it["plan_bearing"] = math.degrees(math.atan2(r, u)) % 360


def wrap(a):
    return (a + 180) % 360 - 180


diffs = [math.radians(wrap(it["plan_bearing"] - it["real_bearing"])) for it in items]
delta = math.degrees(math.atan2(sum(math.sin(d) for d in diffs), sum(math.cos(d) for d in diffs)))
for it in items:
    it["err"] = wrap(it["plan_bearing"] - it["real_bearing"] - delta)
errs = [abs(it["err"]) for it in items]
lx = np.log([it["real_km"] for it in items])
ly = np.log([it["plan_mm"] for it in items])
b_, a_ = np.polyfit(lx, ly, 1)
# 실제 북쪽의 화면 방향
dl = math.radians(delta)
X = math.sqrt(2) * (math.sin(dl) - math.cos(dl)) / 2
Y = -math.sqrt(2) * (math.sin(dl) + math.cos(dl)) / 2
sx, sy = D.C30 * (X - Y), 0.5 * (X + Y)
north_screen = math.degrees(math.atan2(sx, -sy)) % 360
res["geo"] = {
    "rotation_plan_minus_real_deg": round(delta, 1),
    "real_north_screen_bearing_deg(시계 방향, 화면 위=0)": round(north_screen, 1),
    "bearing_error_abs_mean_deg": round(float(np.mean(errs)), 1), "bearing_error_abs_median_deg": round(float(np.median(errs)), 1),
    "bearing_error_max": [max(items, key=lambda it: abs(it["err"]))["name"], round(max(errs), 1)],
    "distance_law": f"평면 mm ≈ {math.exp(a_):.0f} × km^{b_:.2f}",
    "distance_exponent": round(float(b_), 2),
    "items": [{"name": it["name"], "real_km": round(it["real_km"], 1), "real_bearing": round(it["real_bearing"]), "plan_mm": round(it["plan_mm"]), "plan_bearing": round(it["plan_bearing"]), "err_deg": round(it["err"])} for it in items],
}

# ═════ 9. 라벨 수 ═════
res["labels"] = {"wall_flag_tag": len(D.LABELS), "floor_text": len(D.FLOOR_TEXT), "total": len(D.LABELS) + len(D.FLOOR_TEXT)}

np.save(OUT + "/v2_hero_cluster_sil.npy", sil)
json.dump(res, open(OUT + "/v2_check.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ("hierarchy", "overlaps_not_allowed", "land_in_sea", "land_in_river", "portus_land_sea_split_mm2", "water_items_on_land_pct", "contact_distance_mm", "ring_range_median", "left_right", "hero_cluster", "core_group_city", "density_estimate", "labels")}, ensure_ascii=False, indent=1))
print("방위:", res["geo"]["rotation_plan_minus_real_deg"], "평균 오차", res["geo"]["bearing_error_abs_mean_deg"], "중앙값", res["geo"]["bearing_error_abs_median_deg"], "최대", res["geo"]["bearing_error_max"], res["geo"]["distance_law"])
