# -*- coding: utf-8 -*-
"""최종 배치 사양 검사: 코어 군 상자·볼록 껍질·실루엣, 위계, 겹침, 고리 거리, 밀도(근사). 결과를 JSON으로 출력한다."""
import json
import math
import sys

import cv2
import numpy as np

sys.path.insert(0, sys.argv[1])
import final_spec_data as D  # noqa: E402

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


def band(pts, w):
    """±30° 중심선 → 수직 폭 w 띠(마이터)"""
    out = []
    left, right = [], []
    n = len(pts)
    dirs = []
    for i in range(n - 1):
        dx, dy = pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]
        L = math.hypot(dx, dy)
        dirs.append((dx / L, dy / L))
    for i in range(n):
        if i == 0 or i == n - 1:
            d = dirs[0] if i == 0 else dirs[-1]
            nn = (-d[1], d[0])
            left.append((pts[i][0] + nn[0] * w / 2, pts[i][1] + nn[1] * w / 2))
            right.append((pts[i][0] - nn[0] * w / 2, pts[i][1] - nn[1] * w / 2))
        else:
            a, b = dirs[i - 1], dirs[i]
            na, nb = (-a[1], a[0]), (-b[1], b[0])
            mx, my = na[0] + nb[0], na[1] + nb[1]
            ml = math.hypot(mx, my)
            mx, my = mx / ml, my / ml
            k = (w / 2) / (mx * na[0] + my * na[1])
            left.append((pts[i][0] + mx * k, pts[i][1] + my * k))
            right.append((pts[i][0] - mx * k, pts[i][1] - my * k))
    out = left + right[::-1]
    return out


def area_mm2(m):
    return float((m > 0).sum()) / (PX * PX)


def bbox(m):
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return None
    return [round(xs.min() / PX, 1), round(ys.min() / PX, 1), round((xs.max() + 1) / PX, 1), round((ys.max() + 1) / PX, 1)]


def clip_frame(m):
    return m  # 캔버스가 곧 액자


# ── 코어 군 구성 마스크
cells = []
for k in range(1, 8):
    v = D.cell_verts(k)
    cells.append(fill(blank(), [v["T"], v["R"], v["B"], v["L"]]))
boards = [fill(blank(), D.board_poly(b["cell"], b["edge"], b["h"], b.get("frac", (0.0, 1.0)))) for b in D.BOARDS]
oct_ = D.arena_oct()
arena = fill(blank(), oct_)
# 옆면(앞쪽 세 변 아래 T)
o = oct_
for k in (7, 0, 1):
    a, b = o[k], o[(k + 1) % 8]
    fill(arena, [a, b, (b[0], b[1] + D.ARENA_T), (a[0], a[1] + D.ARENA_T)])
# 벽: 오른쪽 1/4 조각(높이 FRAG_H), 뒤-오른쪽(BACK_H), 왼쪽 위(BACKLEFT_H), 앞(8)
for t0, t1, h in [(270, 360, D.ARENA_FRAG_H), (225, 270, D.ARENA_BACK_H), (135, 225, D.ARENA_BACKLEFT_H), (0, 135, 8.0)]:
    for t in range(t0, t1, 3):
        p0 = D.arena_ring_pt(t, 0)
        p1 = D.arena_ring_pt(t + 3, 0)
        q0 = D.arena_ring_pt(t, h)
        q1 = D.arena_ring_pt(t + 3, h)
        fill(arena, [p0, p1, q1, q0])
river = blank()
for s in D.RIVER:
    fill(river, band(s["pts"], s["w"]))
river_in = river.copy()
details = blank()
for d in D.CORE_DETAILS:
    fill(details, rect_pts(d["box"]))
road_mat = fill(blank(), band(D.ROADS[1]["pts"], D.ROADS[1]["w"]))

chain = blank()
for m in cells + boards:
    chain |= m
core_parts = {"공정 셀 체인(셀 7 + 간판)": chain, "아레나": arena, "테베레강 구간": river_in, "강변 디테일": details, "재료 운반 길": road_mat}
core = blank()
for m in core_parts.values():
    core |= m
stage = fill(blank(), rect_pts(D.STAGE))
core &= stage

# 실루엣: 13mm 닫힘 + 구멍 메움(레퍼런스 측정과 같은 방법)
ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(13 * PX) | 1, int(13 * PX) | 1))
closed = cv2.morphologyEx(core, cv2.MORPH_CLOSE, ker)
cnts, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
sil = blank()
cv2.drawContours(sil, cnts, -1, 255, -1)
sil &= stage
hull_pts = cv2.convexHull(np.vstack([c for c in cnts]))
hull = blank()
cv2.fillPoly(hull, [hull_pts], 255)
hull &= stage
cb = bbox(core)
box_area = (cb[2] - cb[0]) * (cb[3] - cb[1])
M = cv2.moments(sil)
cx, cy = M["m10"] / M["m00"] / PX, M["m01"] / M["m00"] / PX

res = {"stage_area_mm2": D.STAGE_AREA}
res["core_group"] = {
    "bbox": cb, "bbox_wh": [round(cb[2] - cb[0], 1), round(cb[3] - cb[1], 1)],
    "bbox_area_mm2": round(box_area), "bbox_pct_stage": round(100 * box_area / D.STAGE_AREA, 1),
    "hull_area_mm2": round(area_mm2(hull)), "hull_pct_stage": round(100 * area_mm2(hull) / D.STAGE_AREA, 1),
    "silhouette_area_mm2": round(area_mm2(sil)), "silhouette_pct_stage": round(100 * area_mm2(sil) / D.STAGE_AREA, 1),
    "raw_union_mm2": round(area_mm2(core)), "raw_union_pct_stage": round(100 * area_mm2(core) / D.STAGE_AREA, 1),
    "aspect_h_over_w": round((cb[3] - cb[1]) / (cb[2] - cb[0]), 2),
    "centroid_mm": [round(cx, 1), round(cy, 1)], "centroid_norm": [round(cx / 420, 3), round(cy / 594, 3)],
    "components_after_close": len(cnts),
    "parts_area_mm2": {k: round(area_mm2(v & stage)) for k, v in core_parts.items()},
}

# ── 단일 오브젝트 상자
objs = {}
for k in range(1, 8):
    m = cells[k - 1].copy()
    for b, bm in zip(D.BOARDS, boards):
        if b["cell"] == k:
            m |= bm
    objs[f"셀 c{k}(단계 {D.CELL_STEP[k - 1]})"] = bbox(m)
objs["아레나"] = bbox(arena & stage)
for s in D.SUPPORTS + D.SUPPORT2:
    objs[s["name"]] = s["box"]
mag = D.MAGNIFIER
r = mag["d"] / 2
objs["확대 창"] = [mag["c"][0] - r, mag["c"][1] - r, mag["c"][0] + r, mag["c"][1] + r]


def ba(b):
    return round((b[2] - b[0]) * (b[3] - b[1]))


res["object_boxes"] = {k: {"box": v, "wh": [round(v[2] - v[0], 1), round(v[3] - v[1], 1)], "area": ba(v)} for k, v in objs.items()}
panel_boxes = {p["name"]: ba(p["rect"]) for p in D.PANELS}
bd = {k: v for k, v in panel_boxes.items()}
bd["확대 창"] = ba(objs["확대 창"])
bd_min_name = min(bd, key=bd.get)
sup_max_name = max((s["name"] for s in D.SUPPORTS), key=lambda n: ba(objs[n]))
sup_min_name = min((s["name"] for s in D.SUPPORTS), key=lambda n: ba(objs[n]))
step_boxes = {}
for st in range(1, 7):
    ks = [i + 1 for i, s in enumerate(D.CELL_STEP) if s == st]
    bs = [objs[f"셀 c{k}(단계 {st})"] for k in ks]
    u = [min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs)]
    step_boxes[f"{st}단계 {D.STEP_NAME[st]}"] = {"box": u, "area": ba(u)}
res["hierarchy"] = {
    "core_group_bbox": round(box_area), "arena": ba(objs["아레나"]),
    "max_single_cell": max(ba(objs[f"셀 c{k}(단계 {D.CELL_STEP[k - 1]})"]) for k in range(1, 8)),
    "step_boxes": step_boxes,
    "basic_detail_boxes": bd, "basic_detail_min": [bd_min_name, bd[bd_min_name]], "basic_detail_max": max(bd.values()),
    "support_cap(=BD_min/1.1)": round(bd[bd_min_name] / 1.1),
    "support_max": [sup_max_name, ba(objs[sup_max_name])], "support_min": [sup_min_name, ba(objs[sup_min_name])],
    "support2": ba(D.SUPPORT2[0]["box"]),
}
h = res["hierarchy"]
h["checks"] = {k: bool(v) for k, v in {
    "코어 군 > 아레나": box_area > h["arena"],
    "아레나 ≥ 최대 셀 × 1.1": h["arena"] >= 1.1 * h["max_single_cell"],
    "아레나 > Basic·Detail 최대": h["arena"] > h["basic_detail_max"],
    "모든 단계 상자 ≥ Basic·Detail 최대 × 1.05": all(v["area"] >= 1.05 * h["basic_detail_max"] for v in step_boxes.values()),
    "Support 최대 ≤ Basic·Detail 최소 ÷ 1.1": h["support_max"][1] <= bd[bd_min_name] / 1.1,
    "Support 최소 ≥ Support-2 × 1.1": h["support_min"][1] >= 1.1 * h["support2"],
}.items()}

# ── 겹침 검사(상자·다각형 근사)
shapes = {}
shapes["타이틀"] = fill(blank(), rect_pts(D.TITLE["rect"]))
for p in D.PANELS:
    shapes["패널 " + p["id"]] = fill(blank(), rect_pts(p["rect"]))
shapes["코어 체인"] = chain
shapes["아레나"] = arena
shapes["강"] = river
for s in D.SUPPORTS + D.SUPPORT2:
    shapes[s["id"] + " " + s["name"]] = fill(blank(), rect_pts(s["box"]))
mg = blank()
cv2.circle(mg, (int(mag["c"][0] * PX), int(mag["c"][1] * PX)), int(r * PX), 255, -1)
shapes["확대 창"] = mg
for d in D.CORE_DETAILS:
    shapes["디테일 " + d["name"]] = fill(blank(), rect_pts(d["box"]))
for d in D.MAP_PROPS:
    if d["zone"] == "아레나 받침 안":
        continue
    shapes["소품 " + d["name"]] = fill(blank(), rect_pts(d["box"]))
for rd in D.ROADS:
    shapes["길 " + rd["name"]] = fill(blank(), band(rd["pts"], rd["w"]))
for lb in D.LABELS:
    shapes["라벨 " + lb["name"]] = fill(blank(), rect_pts(lb["box"]))
allowed = {
    frozenset(["코어 체인", "아레나"]), frozenset(["디테일 하역장(강 굽이 바깥 둑)", "강"]),
    frozenset(["디테일 바지선 1(윗팔)", "강"]), frozenset(["디테일 바지선 2(앞팔)", "강"]),
    frozenset(["소품 포도밭 농장(베수비오 밑동)", "S6 베수비오(Support-2, 가장 먼 곳)"]),
    frozenset(["길 재료 운반 길(하역장 → 1단계)", "디테일 하역장(강 굽이 바깥 둑)"]),
    frozenset(["길 재료 운반 길(하역장 → 1단계)", "디테일 재료 수레"]),
    frozenset(["길 재료 운반 길(하역장 → 1단계)", "코어 체인"]),
    frozenset(["길 아피아 가도(Via Appia, 주축 길)", "아레나"]),
    frozenset(["길 포르투스 길(Via Portuensis, 보조)", "아레나"]),
    frozenset(["길 포르투스 길(Via Portuensis, 보조)", "S5 포르투스 항(트라야누스 육각 내항 + 클라우디우스 외항 + 등대)"]),
    frozenset(["라벨 베수비오", "S6 베수비오(Support-2, 가장 먼 곳)"]),
    frozenset(["라벨 하역장", "디테일 하역장(강 굽이 바깥 둑)"]),
    frozenset(["S3 수도교(아쿠아 클라우디아 아치 열)", "코어 체인"]),
    frozenset(["라벨 확대 창", "확대 창"]),
    frozenset(["소품 올리브·곡식밭·포도밭(왼쪽 들)", "라벨 수도교"]),
    frozenset(["소품 포도밭 구획(오른쪽 아래)", "라벨 카이킬리아 메텔라 무덤"]),
}
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

# ── 아레나 바닥점 기준 Support 거리(파리 127~263mm, 베이징 140~340mm)
ax, ay = D.ARENA_C
dist = {}
for s in D.SUPPORTS + D.SUPPORT2:
    b = s["box"]
    px, py = (b[0] + b[2]) / 2, b[3] - 0.15 * (b[3] - b[1])
    dist[s["name"]] = round(math.hypot(px - ax, py - ay))
res["support_ring_distance_mm"] = dist

# ── 밀도 근사: 오브젝트(코어 군 실면적 + Support 상자 × 0.7 + 소품 상자 × 0.6) / 지도 무대
obj = core.copy()
sup_area = sum(0.7 * ba(s["box"]) for s in D.SUPPORTS + D.SUPPORT2)
prop_area = sum(0.6 * ba(p["box"]) for p in D.MAP_PROPS if p["zone"] not in ("아레나 받침 안",))
sea = fill(blank(), D.SEA) & stage
res["density_estimate"] = {
    "core_union_mm2": round(area_mm2(core)), "supports_alpha_est_mm2": round(sup_area), "props_alpha_est_mm2": round(prop_area),
    "objects_pct_stage_est": round(100 * (area_mm2(core) + sup_area + prop_area) / D.STAGE_AREA, 1),
    "sea_pct_stage": round(100 * area_mm2(sea) / D.STAGE_AREA, 1),
    "river_pct_stage": round(100 * area_mm2(river & stage) / D.STAGE_AREA, 1),
}
res["geometry"] = {
    "cells": {f"c{k}": {"center": [round(c, 2) for c in D.cell_center(k)], "verts": {n: [round(p[0], 2), round(p[1], 2)] for n, p in D.cell_verts(k).items()}} for k in range(1, 8)},
    "arena_center": [round(ax, 2), round(ay, 2)], "arena_oct": [[round(p[0], 2), round(p[1], 2)] for p in oct_],
    "arena_box_model": [round(v, 1) for v in D.arena_box()],
}
np.save(sys.argv[2] + "/final_spec_core_sil.npy", sil)
json.dump(res, open(sys.argv[2] + "/final_spec_check.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ("core_group", "hierarchy", "overlaps_not_allowed", "support_ring_distance_mm", "density_estimate")}, ensure_ascii=False, indent=1))
