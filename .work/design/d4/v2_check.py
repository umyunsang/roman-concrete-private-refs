# -*- coding: utf-8 -*-
"""새 위계 배치 사양 검사. 담당: global
사전 검사(사양 기하): 필수 요소 존재(패널 6·랜드마크 L1~L9·네로 거상·R7·폰스 아일리우스 다리) → 투영 크기 위계(L·P2·B·D·S·P5 + Z1 합성),
  패널 수 5~7, 겹침(L7~L9는 poly_screen), 땅·바다·강(L7~L9는 ground_screen), 길 접촉, 고리 거리, 히어로 군(실루엣·껍질·상자),
  밀도 근사(무대 173,460mm²), 압축 지리(방위 오차·거리 지수, L7~L9 포함).
  사용: python -I v2_check.py <data_dir> <out_dir>   (필수 요소가 하나라도 없으면 v2_check.json을 쓴 뒤 종료 코드 1)
사후 검사(렌더가 실제로 그린 것): out/drawn.json을 15개 규칙(①~⑮)과 보조 확인으로 판정해 out/post_check.json에 쓴다. 실패가 1건이라도 있으면 종료 코드 1.
  사용: python -I v2_check.py --post <drawn.json> <post_check.json> [spec.json]"""
import json
import math
import os
import re
import sys

PX = 4.0
W, H = int(420 * PX), int(594 * PX)
D = None  # 사전 검사에서 v2_data 모듈


# ═══════════════════════════════════════════ 사전 검사 ═══════════════════════════════════════════
def _np():
    import numpy as np
    return np


def _cv():
    import cv2
    return cv2


def blank():
    return _np().zeros((H, W), _np().uint8)


def fill(m, pts):
    a = _np().array([[int(round(x * PX)), int(round(y * PX))] for x, y in pts], _np().int32)
    _cv().fillPoly(m, [a], 255)
    return m


def rect_pts(b):
    x0, y0, x1, y1 = b
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def rect_mask(b):
    return fill(blank(), rect_pts(b))


def circ_mask(c, d):
    m = blank()
    _cv().circle(m, (int(round(c[0] * PX)), int(round(c[1] * PX))), int(round(d / 2 * PX)), 255, -1)
    return m


def area_mm2(m):
    return float((m > 0).sum()) / (PX * PX)


def bbox(m):
    ys, xs = _np().nonzero(m)
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


def road_mask(r, stage):
    m = blank()
    pl = D.road_plan(r)
    w = D.road_w(r)
    for p0, p1 in zip(pl[:-1], pl[1:]):
        if math.hypot(p1[0] - p0[0], p1[1] - p0[1]) > 1e-6:
            fill(m, plan_band(p0, p1, w))
    return m & stage


def floor_poly(ft):
    ax, ay = ft["anchor"]
    L = ft["len"]
    if ft["baseline"].startswith("↘"):
        dx, dy = D.C30 * L, 0.5 * L
    else:
        dx, dy = D.C30 * L, -0.5 * L
    return [(ax, ay), (ax + dx, ay + dy), (ax + dx, ay + dy - 4.0), (ax, ay - 4.0)]


def lb_box(lb):
    return lb.get("box") or lb.get("slot")


def required_elements():
    """(a) 위계 비교 전에 필수 요소가 있는지 본다: 패널 6(L·P2·B·D·S·P5), 랜드마크 L1~L9, '네로 거상' 소품, 길 R7, 폰스 아일리우스 다리.
    하나라도 없으면 실패다(사전 검사 종료 코드 1, 사후 검사 ⑬도 같은 목록을 drawn.json으로 다시 본다)"""
    ids = [p["id"] for p in D.PANELS_PRINT]
    want_p = list(getattr(D, "PRINT_PANEL_IDS", ("L", "P2", "B", "D", "S", "P5")))
    lm_ids = [x["id"] for x in D.LANDMARKS]
    want_l = list(getattr(D, "REQUIRED_LANDMARK_IDS", tuple("L%d" % k for k in range(1, 10))))
    nero = D.find_nero() if hasattr(D, "find_nero") else None
    r7 = D.road_by_id("R7") if hasattr(D, "road_by_id") else next((r for r in D.ROADS if r.get("id") == "R7"), None)
    bridge = D.find_bridge() if hasattr(D, "find_bridge") else None
    missing = []
    missing += ["패널 %s" % k for k in want_p if k not in ids]
    missing += ["랜드마크 %s" % k for k in want_l if k not in lm_ids]
    if nero is None:
        missing.append("소품 '네로 거상'(받침 + 청동 거상)")
    if r7 is None:
        missing.append("길 R7(콜로세움 받침 앞-왼쪽 변 → 다리 북쪽 끝)")
    if bridge is None:
        missing.append("폰스 아일리우스 다리(L8과 함께)")
    extra_p = [k for k in ids if k not in want_p]
    return {
        "ok": not missing and not extra_p, "missing": missing, "unexpected_panels": extra_p,
        "panels": ids, "panels_expected": want_p, "landmarks": lm_ids, "landmarks_expected": want_l,
        "nero": ({"source": nero["source"], "name": nero["name"], "box": nero.get("box")} if nero else None),
        "road_R7": ({"name": r7.get("name"), "plan": D.road_plan(r7), "w": D.road_w(r7)} if r7 else None),
        "bridge": ({"source": bridge["source"], "name": bridge["name"], "has_polys": bool(bridge.get("polys"))} if bridge else None),
        "rule": "하나라도 없으면 실패(위계 비교 전에 판정). 사후 검사 ⑬이 그린 결과(drawn.json)로 다시 본다",
    }


def main_pre(data_dir, out_dir):
    global D
    sys.path.insert(0, data_dir)
    import v2_data as D_  # noqa: E402
    D = D_
    np, cv2 = _np(), _cv()
    warnings = []

    stage_main = rect_mask(D.STAGE)
    stage = stage_main.copy()
    for r in D.STAGE_EXT:                 # d4: STAGE_EXT = [](R·T 확장 0) → 무대 = STAGE 173,460mm²
        stage |= rect_mask(r)
    SA = D.STAGE_AREA_EXT
    panels_print = D.PANELS_PRINT
    req = required_elements()
    if not req["ok"]:
        print("사전 검사 실패: 필수 요소 없음 →", " · ".join(req["missing"] + ["예상 밖 패널 %s" % k for k in req["unexpected_panels"]]))

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
    roads = {r["id"]: road_mask(r, stage) for r in D.ROADS}
    a0 = D.to_screen(*D.AQUEDUCT_PLAN[0])
    a1 = D.to_screen(*D.AQUEDUCT_PLAN[1])
    aqueduct = fill(blank(), [a0, a1, (a1[0], a1[1] - D.AQUEDUCT_H), (a0[0], a0[1] - D.AQUEDUCT_H)]) & stage

    # ── 오브젝트·정보 요소 상자
    # (c) 랜드마크 겹침 = poly_screen(있으면), 땅·강·바다·접촉 = ground_screen(있으면). 없으면 상자로 대신하고 L7~L9는 경고한다
    def polys_mask(polys):
        m = blank()
        for pg in polys:
            if pg and len(pg) >= 3:
                fill(m, pg)
        return m

    lm, lm_ground, lm_src = {}, {}, {}
    for x in D.LANDMARKS:
        lid = x["id"]
        pl = D.landmark_polys(x) if hasattr(D, "landmark_polys") else None
        gr = D.landmark_ground(x) if hasattr(D, "landmark_ground") else None
        lm[lid] = polys_mask(pl) if pl else rect_mask(x["box"])
        lm_ground[lid] = polys_mask(gr) if gr else lm[lid].copy()
        lm_src[lid] = {"overlap": "poly_screen" if pl else "box", "ground": "ground_screen" if gr else ("poly_screen" if pl else "box")}
        if lid in ("L7", "L8", "L9"):
            if not pl:
                warnings.append("%s %s: poly_screen이 없어 겹침을 투영 상자로 대신함 → map에 등록 요청" % (lid, x["name"]))
            if not gr:
                warnings.append("%s %s: ground_screen이 없어 땅·강·바다·접촉을 %s로 대신함 → map에 등록 요청" % (lid, x["name"], "poly_screen" if pl else "투영 상자"))
    # 폰스 아일리우스 다리: L8의 강 위 부분(다리 상판)은 강·접촉 검사에서 '다리'로 따로 본다
    bridge = D.find_bridge() if hasattr(D, "find_bridge") else None
    bridge_mask = polys_mask(bridge["polys"]) if bridge and bridge.get("polys") else None
    if "L4" in lm:
        lm["L4"] = aqueduct.copy()        # 수도교는 상자 대신 아치 열 평행사변형
        lm_ground["L4"] = aqueduct.copy()
    portus_shape = blank()
    try:
        for _part, polys in D.portus_polys().items():
            for pg in polys:
                if pg and len(pg) >= 3:
                    fill(portus_shape, pg)
    except Exception as e:  # map이 형태 함수를 바꿔도 검사는 상자로 계속한다
        warnings.append("포르투스 외형을 읽지 못해 상자로 대신함: %s" % e)
        portus_shape = lm.get("L6", blank()).copy()
    if "L6" in lm:
        lm["L6"] = portus_shape            # 겹침·땅/바다 검사는 실제 외형으로, 위계는 상자로
        lm_ground["L6"] = portus_shape.copy()
    bg = {x["id"]: rect_mask(x["box"]) for x in D.BACKGROUND}
    props = {}
    for p in D.PROPS:
        pb = D.prop_box(p) if hasattr(D, "prop_box") else p.get("box")
        if pb is None:
            warnings.append("소품 %s: 상자·다각형이 없어 검사에서 뺌 → map에 box 등록 요청" % p.get("name"))
            continue
        props[p["name"]] = rect_mask(pb)
    details = {}
    for d in D.DETAILS:
        details[d["id"]] = circ_mask(d["circle"]["c"], d["circle"]["d"]) if "circle" in d else rect_mask(d["box"])
        tb = d.get("text_box")
        if isinstance(tb, (list, tuple)) and len(tb) == 4:
            details[d["id"] + " 글 칸"] = rect_mask(tb)
    panels = {p["id"]: rect_mask(p["rect"]) for p in panels_print}
    title = rect_mask(D.TITLE["rect"])
    labels, label_src = {}, {}
    for lb in D.LABELS:                       # 글 블록 다각형(block_poly)이 있으면 그것으로, 없으면 슬롯 상자(허용 영역)로 잰다
        blk = D.label_block(lb) if hasattr(D, "label_block") else None
        if blk:
            m_ = blank()
            for pg in blk:
                if len(pg) >= 3:
                    fill(m_, pg)
            labels[lb["name"]] = m_
            label_src[lb["name"]] = "block_poly"
        elif lb_box(lb):
            labels[lb["name"]] = rect_mask(lb_box(lb))
            label_src[lb["name"]] = "slot"
    floors = {ft["name"]: fill(blank(), floor_poly(ft)) for ft in D.FLOOR_TEXT}

    res = {"stage_area_mm2": D.STAGE_AREA, "stage_area_mm2_ext": SA, "stage_rects": D.STAGE_RECTS,
           "stage_area_raster_mm2": round(area_mm2(stage)), "poster_area_mm2": D.POSTER_AREA,
           "panels_print": [p["id"] for p in panels_print],
           "required_elements": req,
           "landmark_shape_source": lm_src, "label_shape_source": label_src}

    # ═════ 1. 투영 크기 위계(상자 면적): 패널 L·P2·B·D·S·P5 + Detail(Z1 = 원 + 글 칸 합성 상자). 필수 요소 판정(위)이 먼저다 ═════
    objects = {"콜로세움(히어로)": hero_box}
    for x in D.LANDMARKS:
        objects[x["name"]] = bbox(lm[x["id"]]) if x["id"] == "L4" else x["box"]
    for x in D.BACKGROUND:
        objects[x["name"]] = x["box"]
    tiers = {"Basic": {}, "Detail": {}, "Support": {}}
    for p in panels_print:
        tiers.setdefault(p["tier"], {})[f'{p["id"]} {p["name"]}'] = p["rect"]
    z1_src = None
    for d in D.DETAILS:
        tiers["Detail"][f'{d["id"]} {d["name"]}'] = D.detail_box(d)
        if d["id"] == "Z1":
            z1_src = D.detail_box_source(d)
    if z1_src == "circle_only":
        warnings.append("Z1 글 칸(text_box)·합성 상자(composite_box)가 사양에 없어 원 상자만으로 위계를 계산함 → panels에 등록 요청")
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
    n_pan = len(panels_print)
    pc_lo, pc_hi = getattr(D, "PANEL_COUNT_RANGE", (5, 7))
    lm_floor = float(getattr(D, "LANDMARK_MIN_AREA", 4500.0))
    hm_lo, hm_hi = getattr(D, "HERO_OVER_MEDIAN_RANGE", (4.5, 7.9))
    checks = {
        "필수 요소 존재(패널 6·랜드마크 L1~L9·네로 거상·R7·폰스 아일리우스 다리)": req["ok"],
        "패널 수 %d~%d(도시편 근거·사용자 결정 2절)" % (pc_lo, pc_hi): pc_lo <= n_pan <= pc_hi,
        "인쇄 패널 = L·P2·B·D·S·P5": [p["id"] for p in panels_print] == list(getattr(D, "PRINT_PANEL_IDS", ())),
        "Core 지도 무대 > 모든 Basic·Detail·Support 요소": SA > panel_max,
        "콜로세움 = 최대 단일 오브젝트(≥ 표준 랜드마크 최대 × 1.1)": hero_a >= 1.1 * max(lm_areas.values()),
        "콜로세움 > 가장 큰 패널(제작 과정)": hero_a > panel_max,
        "Basic 각 요소 ≥ Detail 각 요소(최소 Basic ≥ 최대 Detail)": basic_min[1] >= detail_max[1],
        "Detail 각 요소 > Support(최소 Detail ≥ Support × 1.1)": detail_min[1] >= 1.1 * support[1],
        "베수비오 = 가장 작은 랜드마크급 지도 요소(≤ 랜드마크 최소 ÷ 1.1)": ves <= min(lm_areas.values()) / 1.1,
        "표준 랜드마크 하한(각 ≥ %s mm², 메텔라 4,620과 같은 등급)" % format(int(lm_floor), ","): min(lm_areas.values()) >= lm_floor,
        "콜로세움 ÷ 표준 랜드마크 중앙값 %.1f~%.1f배(청와대~파리)" % (hm_lo, hm_hi): hm_lo <= hero_a / med_lm <= hm_hi,
    }
    res["hierarchy"] = {
        "core_stage_mm2": SA, "core_stage_main_mm2": D.STAGE_AREA,
        "hero_box": hero_box, "hero_wh": [round(hero_box[2] - hero_box[0], 1), round(hero_box[3] - hero_box[1], 1)], "hero_area": hero_a,
        "landmark_areas": lm_areas, "landmark_count": len(lm_areas), "landmark_median": round(med_lm), "hero_over_landmark_median": round(hero_a / med_lm, 2),
        "hero_over_landmark_max": round(hero_a / max(lm_areas.values()), 2), "landmark_min_rule_mm2": lm_floor,
        "vesuvius_area": ves,
        "tier_areas": tier_area,
        "z1_box_source": z1_src,
        "basic_min": list(basic_min), "detail_max": list(detail_max), "detail_min": list(detail_min), "support": list(support),
        "ratio_basicmin_over_detailmax": round(basic_min[1] / detail_max[1], 3),
        "ratio_detailmin_over_support": round(detail_min[1] / support[1], 3),
        "panel_count_rule": {"rule": "인쇄 패널 %d~%d개(도시편 중앙값 6, 사용자 결정 2절)" % (pc_lo, pc_hi), "count": n_pan,
                             "ids": [p["id"] for p in panels_print], "pass": bool(pc_lo <= n_pan <= pc_hi)},
        "checks": {k: bool(v) for k, v in checks.items()},
    }
    res["objects_boxes"] = {k: {"box": v, "wh": [round(v[2] - v[0], 1), round(v[3] - v[1], 1)], "area": ba(v)} for k, v in objects.items()}
    res["panel_rects"] = {p["id"]: [round(float(v), 2) for v in p["rect"]] for p in panels_print}
    try:
        _lh = getattr(D, "PORTUS_LIGHTHOUSE", {}) or {}
        res["portus_spec"] = {"lighthouse": {k: _lh.get(k) for k in ("plan_angle_deg", "plan_r", "screen_base", "island_r", "apex_z")},
                              "canals": [{"name": c.get("name"), "plan_x": c.get("plan_x"), "plan_y": c.get("plan_y")} for c in (getattr(D, "PORTUS_CANALS", []) or [])]}
    except Exception as e:  # 기록용
        res["portus_spec"] = {"error": str(e)}
    z1d = next((d for d in D.DETAILS if d.get("id") == "Z1"), None)
    if z1d is not None:
        res["z1"] = {"circle": z1d.get("circle"), "text_box": z1d.get("text_box"), "composite_box": D.detail_box(z1d), "area": ba(D.detail_box(z1d))}

    # ═════ 2. 겹침 검사(라벨 슬롯은 '허용 영역': 슬롯-길·슬롯-랜드마크 상자 겹침은 실패로 치지 않는다) ═════
    shapes = {"타이틀": title}
    for k, m in panels.items():
        shapes["패널 " + k] = m
    shapes["콜로세움"] = hero
    shapes["공사장"] = worksite
    lm_keys = {"콜로세움"}
    for x in D.LANDMARKS:
        shapes[x["id"] + " " + x["name"]] = lm[x["id"]]
        lm_keys.add(x["id"] + " " + x["name"])
    for x in D.BACKGROUND:
        shapes[x["id"] + " " + x["name"]] = bg[x["id"]]
        lm_keys.add(x["id"] + " " + x["name"])
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
        ["길 R5", "L3 카라칼라 욕장(절개)"], ["길 R5", "길 R2"], ["길 R6a", "길 R1"], ["길 R6a", "길 R6b"],
        ["길 R6a", "콜로세움"], ["길 R3", "L2 트라야누스 시장"],      # 진입로는 문(받침 변)·지면에서 시작한다
        ["길 R6a", "L5 카이킬리아 메텔라 무덤"], ["길 R6b", "L5 카이킬리아 메텔라 무덤"],
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
        ["지시선 제작 과정 ⑥ → 콜로세움 공사장(지도→패널, 런던 BUS LINE 9 문법)", "콜로세움"],
        ["지시선 콜로세움 기초 절개 → 확대 창 Z1", "콜로세움"], ["지시선 콜로세움 기초 절개 → 확대 창 Z1", "Detail Z1"],
        ["지시선 확대 창 Z1 → Detail 패널 D", "Detail Z1"], ["지시선 확대 창 Z1 → Detail 패널 D", "패널 D"],
        ["지시선 판테온 돔 → 콜아웃 C1", "L1 판테온"], ["지시선 판테온 돔 → 콜아웃 C1", "Detail C1"],
        ["지시선 클라우디우스 외항 방파제 → 콜아웃 C2", "L6 포르투스 항"], ["지시선 클라우디우스 외항 방파제 → 콜아웃 C2", "Detail C2"],
        ["지시선 메텔라 무덤 → 콜아웃 C4", "L5 카이킬리아 메텔라 무덤"], ["지시선 메텔라 무덤 → 콜아웃 C4", "Detail C4"],
        ["지시선 메텔라 무덤 → 콜아웃 C4", "소품 교외 빌라(포도밭 농가)"],
        ["Detail Z1", "Detail Z1 글 칸"],
        # d4(기준선 7절) 새 랜드마크·길·다리
        ["길 R2", "L7"],                                   # 바실리카 기단 포장–시내 길 1 접속(≤ 1.6mm, 사후 ⑤)
        ["L3", "L7"],                                      # 상자 단계만. 사후 ⑭가 실루엣 ≥ 2mm를 본다
        ["L1", "L9"],                                      # 상자 단계만(판테온 광장 아래 극장)
        ["강", "L8"],                                      # 폰스 아일리우스 다리가 ↘ 팔을 건넌다
        ["소품 테베레 하역장", "L8"],                      # 상자 단계만(원통 꼭대기–부두 아래 변 ≥ 4는 사후 ⑭)
        ["길 R7", "L8"], ["길 R7", "콜로세움"], ["길 R7", "강"],
        ["라벨 화산재 운반선", "소품 화산재 운반선"],      # 깃대형: 깃대가 선체 위에서 선다
    ]))
    # 이름이 조금 달라도 맞도록 키워드로 적는 허용쌍(상자·슬롯 단계만. 실제 실루엣·글 블록은 사후 검사 ②·⑭가 본다)
    allowed_kw = [
        (("소품 네로", "소품 네로의"), ("콜로세움",)),                 # 거상 받침 상자 모서리가 4층 조각 상자에 걸친다(실루엣 2.54mm)
        (("소품 네로", "소품 네로의"), ("L7 ",)),                       # 거상 상자–바실리카 상자(실루엣 6.06mm)
        (("라벨 막센티우스", "라벨 바실리카", "라벨 BASILICA", "라벨 Basilica"), ("라벨 네로", "라벨 거상", "라벨 콘크리트(벽돌 마감)")),  # 비스듬한 두 블록이 세로 2.4mm(수직 2.0) 간격으로 겹쳐 앉는다
        (("라벨 하드리아누스", "라벨 영묘", "라벨 MAUSOLEUM", "라벨 Mausoleum"), ("강",)),   # 슬롯 왼쪽 위 모서리가 ↙ 팔 물 위(글 블록은 둑선에서 세로 2.4mm 밖)
        (("라벨 마르켈루스", "라벨 극장", "라벨 THEATRE", "라벨 Theatre"), ("강",)),        # 슬롯 왼쪽 아래 모서리가 ↘ 팔 물 위(글 블록은 둑에서 10mm 위)
    ]

    def kw_allowed(a, b):
        for ka, kb in allowed_kw:
            if (any(a.startswith(k) for k in ka) and any(b.startswith(k) or b == k.strip() for k in kb)) or \
               (any(b.startswith(k) for k in ka) and any(a.startswith(k) or a == k.strip() for k in kb)):
                return True
        return False

    def canon(k):
        """허용 목록 대조용 이름: 괄호 설명을 떼고, 랜드마크는 id만 쓴다(map·panels가 표시 이름을 다듬어도 대조가 깨지지 않게)"""
        k2 = re.sub(r"\(.*$", "", k).strip()
        m_ = re.match(r"^(L\d+|V) ", k2)
        return m_.group(1) if m_ else k2

    allowed = set(frozenset(canon(k) for k in pair) for pair in allowed)
    keys = list(shapes)
    over, slot_ok = [], []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = keys[i], keys[j]
            if frozenset([canon(a), canon(b)]) in allowed or kw_allowed(a, b):
                continue
            inter = area_mm2(shapes[a] & shapes[b])
            if inter <= 0.5:
                continue
            if {a.split(" ")[0], b.split(" ")[0]} == {"지시선", "길"}:
                continue                      # 지시선의 길 위 통과는 허용
            is_slot = a.startswith("라벨 ") or b.startswith("라벨 ")
            other = b if a.startswith("라벨 ") else a
            if is_slot and (other.startswith("길 ") or other in lm_keys):
                slot_ok.append([a, b, round(inter, 1)])
                continue
            over.append([a, b, round(inter, 1)])
    res["overlaps_not_allowed"] = over
    res["slot_overlaps_allowed"] = {"rule": "라벨 슬롯은 허용 영역이다. 슬롯-길·슬롯-랜드마크 상자 겹침은 실패가 아니며, 실제 글 블록 외곽은 사후 검사(drawn.json)가 판정한다", "pairs": slot_ok}
    res["allowed_keyword_pairs"] = [[list(a), list(b)] for a, b in allowed_kw]

    # ═════ 3. 땅 요소가 바다·강에 들어갔는지(랜드마크는 ground_screen, 없으면 겹침 외형). 다리 상판은 강 위가 정상이라 뺀다 ═════
    land_items = {"콜로세움": hero, "공사장": worksite}
    for x in D.LANDMARKS:
        if x["id"] != "L6":
            g = lm_ground[x["id"]].copy()
            if x["id"] == "L8" and bridge_mask is not None:
                g &= ~bridge_mask
            land_items[x["name"]] = g
    for p in D.PROPS:
        if p.get("on") == "땅" and p["name"] in props:
            land_items[p["name"]] = props[p["name"]]
    res["land_in_sea"] = {k: round(area_mm2(m & sea), 1) for k, m in land_items.items() if area_mm2(m & sea) > 0.5}
    res["land_in_river"] = {k: round(area_mm2(m & river), 1) for k, m in land_items.items() if area_mm2(m & river) > 0.5}
    res["bridge"] = {"found": bridge is not None, "source": bridge["source"] if bridge else None, "polys": bool(bridge_mask is not None),
                     "river_overlap_mm2": round(area_mm2(bridge_mask & river), 1) if bridge_mask is not None else None,
                     "rule": "다리 상판(L8)의 강 위 부분은 land_in_river에서 뺀다(다리–강·다리–R7 접촉은 정상)"}
    water_items = {p["name"]: props[p["name"]] for p in D.PROPS if p.get("on") == "물" and p["name"] in props}
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
        m = lm_ground[x["id"]]
        others = net.copy()
        if x["id"] == "L4":
            others = (net & ~aqueduct) | lm.get("L3", blank())
        d_t = cv2.distanceTransform(255 - others, cv2.DIST_L2, 5) / PX
        contact[x["name"]] = round(float(d_t[m > 0].min()), 1) if (m > 0).any() else None
    contact["콜로세움"] = round(float(dist_t[hero > 0].min()), 1)
    res["contact_distance_mm"] = contact
    res["contact_ok_le_2.5mm"] = {k: (v is not None and v <= 2.5) for k, v in contact.items()}

    # ═════ 5. 히어로 중심에서 랜드마크 바닥점까지(파리 127~263mm, 베이징 140~340mm). 베수비오·배경은 고리·좌우에서 뺀다 ═════
    hx, hy = D.HERO_C

    def base_pt(b):
        return ((b[0] + b[2]) / 2, b[3] - 0.15 * (b[3] - b[1]))

    ring, ring_bg = {}, {}
    side = {"왼쪽": [], "오른쪽": []}
    for x in D.LANDMARKS:
        px_, py_ = base_pt(objects[x["name"]])
        ring[x["name"]] = round(math.hypot(px_ - hx, py_ - hy))
        side["왼쪽" if px_ < hx else "오른쪽"].append(x["name"])
    for x in D.BACKGROUND:
        px_, py_ = base_pt(objects[x["name"]])
        ring_bg[x["name"]] = round(math.hypot(px_ - hx, py_ - hy))
    res["ring_distance_mm"] = ring
    res["ring_distance_background_mm"] = ring_bg
    res["ring_range_median"] = [min(ring.values()), max(ring.values()), round(float(np.median(list(ring.values()))))]
    res["left_right"] = {k: len(v) for k, v in side.items()}
    res["left_right_names"] = side

    # ═════ 6. 히어로 군(콜로세움 + 공사장 + 하역장 띠 소품 + 하역장 길 + 인접 테베레 구간) ═════
    def prop_mask(prefix):
        for k, m in props.items():
            if k == prefix or k.split("(")[0].strip() == prefix.split("(")[0].strip():
                return m
        return None

    hz = hero | worksite
    if "R4" in roads:
        hz |= roads["R4"]
    for nm in ["테베레 하역장", "석회 가마", "재료 수레"]:          # 통합 d4: 바지선 2는 ↙ 팔 하구 쪽으로 옮겨 히어로 군에서 뺀다(map 요청)
        m = prop_mask(nm)
        if m is not None:
            hz |= m
    riv_part = river.copy()
    riv_part[:, : int(100 * PX)] = 0
    riv_part[:, int(232 * PX):] = 0
    hz |= riv_part
    hz &= stage
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(13 * PX) | 1, int(13 * PX) | 1))

    def group_stats(mask):
        closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, ker)
        cnts, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        sil = blank()
        cv2.drawContours(sil, cnts, -1, 255, -1)
        sil &= stage
        hull = blank()
        cv2.fillPoly(hull, [cv2.convexHull(np.vstack(cnts))], 255)
        hull &= stage
        return cnts, sil, hull

    cnts, sil, hull = group_stats(hz)
    cb = bbox(hz)
    M = cv2.moments(sil)
    cx, cy = M["m10"] / M["m00"] / PX, M["m01"] / M["m00"] / PX
    res["hero_cluster"] = {
        "definition": "콜로세움(받침·벽) + 공사장 + 하역장·석회 가마·수레 + 하역장 길 + 테베레 구간(x 100~232)(바지선 2는 하구 쪽이라 뺌). 비율의 분모 = 무대 %smm²(STAGE, 확장 0)" % format(int(SA), ","),
        "bbox": cb, "bbox_wh": [round(cb[2] - cb[0], 1), round(cb[3] - cb[1], 1)],
        "bbox_pct_stage": round(100 * ba(cb) / SA, 1),
        "hull_pct_stage": round(100 * area_mm2(hull) / SA, 1), "hull_mm2": round(area_mm2(hull)),
        "silhouette_pct_stage": round(100 * area_mm2(sil) / SA, 1), "silhouette_mm2": round(area_mm2(sil)),
        "centroid_mm": [round(cx, 1), round(cy, 1)], "centroid_norm_poster": [round(cx / 420, 3), round(cy / 594, 3)],
        "aspect_h_over_w": round((cb[3] - cb[1]) / (cb[2] - cb[0]), 2),
    }

    # 6-2. 도심·시내 코어 군(히어로 군 + 판테온 + 트라야누스 시장 + 카라칼라 욕장 + 시내 길 2)
    hz2 = hz.copy()
    for x in D.LANDMARKS:
        if x["id"] in ("L1", "L2", "L3"):
            hz2 |= rect_mask(x["box"])
    for rid in ("R2", "R3"):
        if rid in roads:
            hz2 |= roads[rid]
    hz2 &= stage
    cnts2, sil2, hull2 = group_stats(hz2)
    cb2 = bbox(hz2)
    M2 = cv2.moments(sil2)
    res["core_group_city"] = {
        "definition": "히어로 군 + 판테온 + 트라야누스 시장 + 카라칼라 욕장 + 시내 길 2개(도심·시내 구역). 분모 = 무대 %smm²" % format(int(SA), ","),
        "bbox": cb2, "bbox_wh": [round(cb2[2] - cb2[0], 1), round(cb2[3] - cb2[1], 1)], "bbox_pct_stage": round(100 * ba(cb2) / SA, 1),
        "hull_pct_stage": round(100 * area_mm2(hull2) / SA, 1), "silhouette_pct_stage": round(100 * area_mm2(sil2) / SA, 1),
        "silhouette_mm2": round(area_mm2(sil2)), "hull_mm2": round(area_mm2(hull2)),
        "centroid_norm_poster": [round(M2["m10"] / M2["m00"] / PX / 420, 3), round(M2["m01"] / M2["m00"] / PX / 594, 3)],
        "components_after_close": len(cnts2),
    }

    # ═════ 7. 밀도 근사(Core 오브젝트 / 무대 173,460mm²). 기준은 렌더 실측(drawn.json density, 전체 무대 기준 하한 39.3%, 열린 무대 값은 기록만) ═════
    core_union = (hero | worksite) & stage
    alpha = {"L1": 0.7, "L2": 0.7, "L3": 0.7, "L5": 0.7, "L6": 0.6}
    lm_est = sum(alpha.get(x["id"], 0.7) * ba(x["box"]) for x in D.LANDMARKS if x["id"] != "L4") + 0.45 * area_mm2(aqueduct)
    bg_est = sum(0.6 * ba(x["box"]) for x in D.BACKGROUND)
    prop_est = 0.6 * sum(ba(D.prop_box(p) if hasattr(D, "prop_box") else p["box"]) for p in D.PROPS if (D.prop_box(p) if hasattr(D, "prop_box") else p.get("box")))
    obj_est = area_mm2(core_union) + lm_est + bg_est + prop_est
    planted_est = sum(pl.get("cover", 0.3) * ba(pl["box"]) for pl in D.PLANTED)
    cover_mask = blank()
    for k, m in panels.items():
        cover_mask |= m
    for k, m in details.items():
        cover_mask |= m
    covered = area_mm2(cover_mask & stage)
    roads_all = blank()
    for m in roads.values():
        roads_all |= m
    res["density_estimate"] = {
        "stage_area_mm2": SA,
        "note": "배치 상자 × 덮는 비율 추정(판정에 쓰지 않는다). 판정은 렌더 실측(사후 검사 ⑦): 건물·소품·사람·나무·밭·포도밭·구릉 레이어 알파 ≥ 128 합집합 ÷ 전체 무대 173,460mm² ≥ 39.3%(레퍼런스와 같은 정의). 열린 무대(무대 − 패널·Detail이 덮는 면적) 값은 기록만 한다",
        "hero_union_mm2": round(area_mm2(core_union)), "landmarks_alpha_est_mm2": round(lm_est), "background_alpha_est_mm2": round(bg_est), "props_alpha_est_mm2": round(prop_est),
        "objects_pct_stage_est": round(100 * obj_est / SA, 1),
        "objects_pct_poster_est": round(100 * obj_est / D.POSTER_AREA, 1),
        "planted_cover_est_mm2": round(planted_est), "planted_count": len(D.PLANTED),
        "objects_plus_planted_pct_stage_est": round(100 * (obj_est + planted_est) / SA, 1),
        "objects_plus_planted_pct_poster_est": round(100 * (obj_est + planted_est) / D.POSTER_AREA, 1),
        "panels_details_cover_stage_mm2": round(covered),
        "objects_plus_planted_pct_open_stage_est": round(100 * (obj_est + planted_est) / max(SA - covered, 1.0), 1),
        "river_pct_stage": round(100 * area_mm2(river) / SA, 1),
        "sea_pct_stage": round(100 * area_mm2(sea) / SA, 1),
        "roads_pct_stage": round(100 * area_mm2(roads_all) / SA, 1),
        "panel_area_pct_poster": round(100 * sum(ba(p["rect"]) for p in panels_print) / D.POSTER_AREA, 1),
        "panel_area_mm2": sum(ba(p["rect"]) for p in panels_print),
        "map_panels_cover_stage_pct": round(100 * area_mm2(panels["S"] & stage) / SA, 1) if "S" in panels else 0.0,
    }

    # ═════ 8. 압축 지리(방위·거리). geo가 None인 랜드마크(예: 수도교, 실측 좌표 삭제)는 표에서 건너뛰고 '없음'으로 적는다 ═════
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

    items, no_geo = [], []
    for x in D.LANDMARKS + D.BACKGROUND:
        if x.get("geo") is None:
            no_geo.append(x["name"])
            continue
        items.append({"name": x["name"], "geo": x["geo"], "screen": base_pt(objects[x["name"]])})
    for e in getattr(D, "GEO_EXTRA", []):
        if e.get("geo") is None:
            no_geo.append(e["name"])
            continue
        items.append({"name": e["name"], "geo": e["geo"], "screen": e["screen"]})
    for it in items:
        dE, dN = real_vec(it["geo"])
        it["real_km"] = math.hypot(dE, dN)
        it["real_bearing"] = math.degrees(math.atan2(dE, dN)) % 360
        r_, u_ = plan_vec(it["screen"])
        it["plan_mm"] = math.hypot(r_, u_)
        it["plan_bearing"] = math.degrees(math.atan2(r_, u_)) % 360

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
        "no_geo": {nm: "없음" for nm in no_geo},
    }

    # ═════ 9. 라벨 수 ═════
    res["labels"] = {"wall_flag_tag": len(D.LABELS), "floor_text": len(D.FLOOR_TEXT), "total": len(D.LABELS) + len(D.FLOOR_TEXT)}

    # ═════ 10. 짝 표지(사양 mark·mark_pt·PAIR_MARKS). 판정은 사후 검사 ⑬(drawn.json texts role 'mark')이고 여기서는 기록만 한다 ═════
    try:
        pm = D.pair_marks() if hasattr(D, "pair_marks") else []
    except Exception as e:  # panels가 형식을 바꿔도 검사는 계속한다(기록만)
        pm = []
        res["pair_marks_error"] = str(e)
    cnt = {}
    for m_ in pm:
        cnt[m_["glyph"]] = cnt.get(m_["glyph"], 0) + 1
    res["pair_marks_spec"] = {"counts": cnt, "expected_drawn": getattr(D, "REQUIRED_MARKS", {}), "items": pm,
                              "has_PAIR_MARKS": hasattr(D, "PAIR_MARKS"),
                              "rule": "표지는 사양의 mark·mark_pt 값으로만 그린다(이름 추론 금지). 사후 검사 ⑬이 그린 표지 17개(A 3·B~D 각 2·숫자 1~4 각 2)를 본다"}
    res["warnings"] = warnings

    np.save(out_dir + "/v2_hero_cluster_sil.npy", sil)
    json.dump(res, open(out_dir + "/v2_check.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in ("required_elements", "hierarchy", "overlaps_not_allowed", "land_in_sea", "land_in_river", "portus_land_sea_split_mm2", "water_items_on_land_pct", "contact_distance_mm", "ring_range_median", "left_right", "hero_cluster", "core_group_city", "density_estimate", "labels", "warnings")}, ensure_ascii=False, indent=1))
    print("방위:", res["geo"]["rotation_plan_minus_real_deg"], "평균 오차", res["geo"]["bearing_error_abs_mean_deg"], "중앙값", res["geo"]["bearing_error_abs_median_deg"], "최대", res["geo"]["bearing_error_max"], res["geo"]["distance_law"])
    if not req["ok"]:
        print("사전 검사 실패: 필수 요소 없음 →", " · ".join(req["missing"] + ["예상 밖 패널 %s" % k for k in req["unexpected_panels"]]))
        return 1
    print("사전 검사 완료: 필수 요소 모두 있음 · 패널", res["panels_print"], "· 랜드마크", len(lm_areas), "· 허용 안 된 겹침", len(over), "· 경고", len(warnings))
    return 0


# ═══════════════════════════════════════════ 사후 검사(drawn.json) ═══════════════════════════════════════════
# drawn.json 계약(render가 쓴다). 열쇠 이름은 아래 별칭을 모두 받는다. 값이 없으면 그 규칙은 '자료 없음'으로 실패한다.
def _base():
    """공용 상수(v2_base)를 이 파일 옆에서 읽는다(-I 실행에서도). 못 읽으면 None(아래 기본값을 쓴다)"""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    try:
        import v2_base as B_  # noqa: E402
        return B_
    except Exception:
        return None


_B = _base()
_PF = getattr(_B, "PRINT_FORBIDDEN", r"Core|Basic|Detail|Support|위계|최종 배치|다이어그램|무대|꼬리표|자리|사양|검사|mm|위치도|연대기|자리 예약|선택 대기|저탄소|41%|29%")
_PF_CI = getattr(_B, "PRINT_FORBIDDEN_CI", r"(?<![A-Za-z])(core|basic|detail|support)(?![A-Za-z])")
_PF_S = getattr(_B, "PRINT_FORBIDDEN_SENTENCES", r"콘크리트로 만든 조각|콘크리트로 빚은 거상|로마 콘크리트는 저탄소|붓다|퐁 뒤 가르|Pont du Gard|유래")
FORBIDDEN = re.compile(_PF)
FORBIDDEN_CI = re.compile(_PF_CI, re.I)
FORBIDDEN_S = re.compile(_PF_S)
NO_DIM_KEYS = tuple(k.lower() for k in getattr(_B, "PRINT_NO_DIMENSION_KEYS", ("바실리카", "영묘", "극장", "네로", "거상")))
DIMENSION = re.compile(getattr(_B, "PRINT_DIMENSION", r"\d[\d,.]*\s?(m|미터|km)(?![A-Za-z])"))
STAGE_MAIN = list(getattr(_B, "STAGE", (0.0, 92.0, 420.0, 505.0)))
STAGE_AREA_FULL = float(getattr(_B, "STAGE_AREA_EXT", 173460.0))
PRINT_PANEL_IDS_ = list(getattr(_B, "PRINT_PANEL_IDS", ("L", "P2", "B", "D", "S", "P5")))
REQUIRED_MARKS_ = dict(getattr(_B, "REQUIRED_MARKS", {"A": 3, "B": 2, "C": 2, "D": 2, "1": 2, "2": 2, "3": 2, "4": 2}))
REQUIRED_LM_ = list(getattr(_B, "REQUIRED_LANDMARK_IDS", tuple("L%d" % k for k in range(1, 10))))
TF_ = getattr(_B, "TYPE_FACES", {})
TOL_FACE, TOL_PITCH, TOL_ANG = 0.1, 0.05, 0.5
# 서체 결정 7(글자면 mm). 앞쪽이 더 구체적인 범주다(라벨 본문이 일반 본문보다 먼저).
FACE_CATS = [
    ("label_sup", ["labelsup", "위첨자", "원어", "superscript"], 2.1),
    ("label_en", ["labelen", "라벨영문", "maplabelen"], 3.8),
    ("label_ko", ["labelko", "라벨국문", "labelname"], 3.8),
    ("label_body", ["labelbody", "라벨본문"], 3.0),
    ("prop_annot", ["propannot", "소품주석"], float(TF_.get("prop_annot", 2.6))),
    ("tag", ["tag", "태그", "말풍선"], 2.6),
    ("s_head_en", ["sheaden", "s머리글영문"], 5.0),
    ("s_head_ko", ["sheadko", "s머리글국문"], 2.8),
    ("panel_head_en", ["headen", "머리글영문", "headeren"], 7.4),
    ("panel_head_ko", ["headko", "머리글국문", "headerko"], (3.6, 3.8)),
    ("step", ["step", "단계명"], 3.0),
    ("note", ["note", "주석", "출처", "source", "caption", "캡션", "시간화살표", "timearrow", "각주", "footnote", "아이콘설명", "iconcaption"], 2.1),
    ("subtitle", ["subtitle", "소제목", "콜아웃제목", "callouttitle", "z1title", "z1제목", "title2"], 2.8),
    ("body", ["body", "본문"], 2.6),
    ("mark_glyph", [], float(TF_.get("mark_glyph", 2.2))),       # 짝 표지 글자(role 'mark'만, cat_of가 따로 고른다)
]
PITCH = {"label_body": 4.15, "body": 3.9, "note": 3.0}
MARK_R = float(TF_.get("mark_r", 2.0))


def G(d, *keys, default=None):
    if not isinstance(d, dict):
        return default
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def as_list(v):
    if v is None:
        return []
    if isinstance(v, dict):
        out = []
        for k, x in v.items():
            if isinstance(x, dict):
                y = dict(x)
                y.setdefault("name", k)
                y.setdefault("id", k)
                out.append(y)
            else:
                out.append({"name": k, "id": k, "geom": x})
        return out
    return list(v)


def _isnum(a):
    return isinstance(a, (int, float)) and not isinstance(a, bool)


def _is_box(v):
    return isinstance(v, (list, tuple)) and len(v) == 4 and all(_isnum(a) for a in v)


def _is_pts(v):
    return isinstance(v, (list, tuple)) and len(v) >= 2 and all(isinstance(p, (list, tuple)) and len(p) >= 2 and _isnum(p[0]) and _isnum(p[1]) for p in v)


GEOM_KEYS = ("poly", "polygon", "outline", "외곽", "parallelogram", "pts", "points", "꼭짓점", "bbox", "box", "rect", "geom", "polys")


def as_polys(v):
    """상자 [x0,y0,x1,y1] · 점 목록 · 여러 다각형 · {poly/outline/box…} → [[(x,y),…], …]"""
    if v is None:
        return []
    if isinstance(v, dict):
        for k in GEOM_KEYS:
            if k in v and v[k] is not None:
                return as_polys(v[k])
        return []
    if _is_box(v):
        x0, y0, x1, y1 = [float(a) for a in v]
        return [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]
    if _is_pts(v):
        return [[(float(p[0]), float(p[1])) for p in v]]
    if isinstance(v, (list, tuple)):
        out = []
        for e in v:
            out += as_polys(e)
        return out
    return []


def bbox_pts(polys):
    xs = [p[0] for pg in polys for p in pg]
    ys = [p[1] for pg in polys for p in pg]
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None


def norm(s):
    return re.sub(r"[\s_\-·.()/]", "", str(s)).lower()


def seg_inter(p1, p2, q1, q2, eps=1e-9):
    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    d1, d2, d3, d4 = orient(q1, q2, p1), orient(q1, q2, p2), orient(p1, p2, q1), orient(p1, p2, q2)
    if ((d1 > eps and d2 < -eps) or (d1 < -eps and d2 > eps)) and ((d3 > eps and d4 < -eps) or (d3 < -eps and d4 > eps)):
        return True
    return False


def pt_seg(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def pt_in_poly(p, poly):
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xi:
                inside = not inside
    return inside


def edges(poly, closed=True):
    n = len(poly)
    m = n if closed else n - 1
    return [(poly[i], poly[(i + 1) % n]) for i in range(m)]


def shape_dist(A, B, a_closed=True, b_closed=True):
    """두 다각형(또는 꺾은선) 사이 최소 거리. 겹치거나 교차하면 0"""
    ea, eb = edges(A, a_closed), edges(B, b_closed)
    for p1, p2 in ea:
        for q1, q2 in eb:
            if seg_inter(p1, p2, q1, q2):
                return 0.0
    if b_closed and len(B) >= 3 and any(pt_in_poly(p, B) for p in A):
        return 0.0
    if a_closed and len(A) >= 3 and any(pt_in_poly(p, A) for p in B):
        return 0.0
    d = min(pt_seg(p, q1, q2) for p in A for q1, q2 in eb) if eb else float("inf")
    d2 = min(pt_seg(q, p1, p2) for q in B for p1, p2 in ea) if ea else float("inf")
    return min(d, d2)


def multi_dist(As, Bs, a_closed=True, b_closed=True):
    best = float("inf")
    for A in As:
        for B in Bs:
            best = min(best, shape_dist(A, B, a_closed, b_closed))
    return best


def line_crosses_poly(line, poly):
    for p1, p2 in edges(line, False):
        for q1, q2 in edges(poly, True):
            if seg_inter(p1, p2, q1, q2):
                return True
    return any(pt_in_poly(p, poly) for p in line)


def lines_cross(a, b):
    for p1, p2 in edges(a, False):
        for q1, q2 in edges(b, False):
            if seg_inter(p1, p2, q1, q2):
                return True
    return False


def text_of(t):
    return G(t, "text", "s", "string", "문자열", "str", default="")


def face_of(t):
    v = G(t, "face", "face_mm", "글자면", "ink_h", "ink_mm", "cap_mm", "glyph_mm")
    return float(v) if _isnum(v) else None


def role_of(t):
    return norm(" ".join(str(G(t, k, default="")) for k in ("layer", "층", "role", "역할", "kind", "종류", "cat", "category")))


def cat_of(t):
    r = role_of(t)
    if not r:
        return None
    if norm(G(t, "role", "역할", default="")) == "mark":
        return "mark_glyph"
    for name, aliases, _v in FACE_CATS:
        if not aliases:
            continue
        if any(a in r for a in aliases):
            if name in ("panel_head_en", "panel_head_ko"):
                pid = str(G(t, "panel", "패널", "box", "in", "owner", default=""))
                if pid.strip().upper() == "S" or "panels" in r or "패널s" in r:
                    return "s_head_en" if name == "panel_head_en" else "s_head_ko"
            return name
    return None


def face_ok(cat, f):
    exp = dict((n, v) for n, _a, v in FACE_CATS)[cat]
    if isinstance(exp, tuple):
        return exp[0] - TOL_FACE <= f <= exp[1] + TOL_FACE, exp
    return abs(f - exp) <= TOL_FACE + 1e-9, exp


def lead_pts(ld):
    if isinstance(ld, dict):
        v = G(ld, "pts", "points", "꼭짓점", "vertices", "poly")
        return [(float(p[0]), float(p[1])) for p in v] if _is_pts(v) else None
    if _is_pts(ld):
        return [(float(p[0]), float(p[1])) for p in ld]
    return None


def seg_dirs(pts):
    """선분 방향(도, 0~180)과 길이. 같은 방향으로 이어진 선분은 합친다"""
    out = []
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        if L < 0.05:
            continue
        a = math.degrees(math.atan2(y1 - y0, x1 - x0)) % 180.0
        if out and min(abs(out[-1][0] - a), 180 - abs(out[-1][0] - a)) < TOL_ANG:
            out[-1] = (out[-1][0], out[-1][1] + L)
        else:
            out.append((a, L))
    return out


def ang_ok(a):
    return any(min(abs(a - t), 180 - abs(a - t)) <= TOL_ANG for t in (90.0, 30.0, 150.0))


def spec_slots(spec):
    out = {}
    try:
        for s in spec["core_map"]["labels"]["slots"]:
            out[s["name"].split("(")[0].strip()] = s
    except Exception:
        pass
    return out


def find_slot(slots, name):
    k = str(name).split("(")[0].strip()
    if k in slots:
        return slots[k]
    for kk, s in slots.items():
        if kk.startswith(k) or k.startswith(kk):
            return s
    return None


def walk_strings(o, path=()):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk_strings(v, path + (str(k),))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk_strings(v, path + (str(i),))
    elif isinstance(o, str):
        yield path, o


def main_post(drawn_path, out_path, spec_path=None):
    rules = []

    def rule(no, name, fails, info=None):
        rules.append({"no": no, "name": name, "pass": not fails, "fails": fails, "info": info or {}})

    if not os.path.exists(drawn_path):
        res = {"drawn": drawn_path, "pass": False, "fail_count": 1, "rules": [], "error": "drawn.json이 없다(렌더가 그린 것을 기록하지 않았다)"}
        json.dump(res, open(out_path, "w"), ensure_ascii=False, indent=1)
        print("사후 검사 실패: drawn.json 없음 →", drawn_path)
        return 1
    dr = json.load(open(drawn_path, encoding="utf-8"))
    if spec_path is None:
        cand = os.path.join(os.path.dirname(os.path.abspath(drawn_path)), "spec.json")
        spec_path = cand if os.path.exists(cand) else None
    spec = json.load(open(spec_path, encoding="utf-8")) if spec_path else {}
    slots = spec_slots(spec)

    texts = as_list(G(dr, "texts", "글", default=[]))
    labels = as_list(G(dr, "labels", "라벨", default=[]))
    leaders = as_list(G(dr, "leaders", "지시선", default=[]))
    roads = as_list(G(dr, "roads", "길", default=[]))
    footprints = as_list(G(dr, "footprints", "지면", default=[]))
    boxes = as_list(G(dr, "boxes", "상자", default=[]))
    road_polys = []
    for r in roads:
        road_polys += as_polys(r)

    # 라벨 외곽·지시선 정리
    L = []
    for lb in labels:
        name = G(lb, "name", "key", "id", "이름", default="?")
        polys = as_polys(G(lb, "poly", "outline", "외곽", "parallelogram", "bbox", "box"))
        own = lead_pts(G(lb, "leader", "지시선", "lead", default=None) or {})
        kind = str(G(lb, "kind", "종류", "type", default=""))
        L.append({"name": name, "polys": polys, "lead": own, "kind": kind, "raw": lb})
    LD = []
    for ld in leaders:
        LD.append({"name": G(ld, "name", "id", "이름", default="?"), "pts": lead_pts(ld), "raw": ld})
    for l_ in L:
        if l_["lead"]:
            raw = G(l_["raw"], "leader", "지시선", "lead")
            raw = dict(raw) if isinstance(raw, dict) else {}
            for k_src, k_dst in (("dot_d", "dot_d"), ("end_d", "dot_d"), ("lead_dot_d", "dot_d"), ("gap", "gap"), ("lead_gap", "gap"), ("target_gap", "gap")):
                if k_dst not in raw and _isnum(G(l_["raw"], k_src)):
                    raw[k_dst] = G(l_["raw"], k_src)
            LD.append({"name": "라벨 지시선 " + str(l_["name"]), "pts": l_["lead"], "raw": raw, "label": l_["name"]})

    # ① 인쇄 글 금지 패턴
    fails = []
    strings = [(str(G(t, "layer", "층", default="")), text_of(t)) for t in texts]
    for l_ in L:
        for k in ("en", "ko", "sup", "text", "tag_text", "lines"):
            v = G(l_["raw"], k)
            if isinstance(v, str):
                strings.append(("라벨", v))
            elif isinstance(v, list):
                strings += [("라벨", s) for s in v if isinstance(s, str)]
        b = G(l_["raw"], "body", "본문")
        if isinstance(b, list):
            strings += [("라벨 본문", s) for s in b if isinstance(s, str)]
    for lay, s in strings:
        m = FORBIDDEN.search(s) or FORBIDDEN_CI.search(s) or FORBIDDEN_S.search(s)
        if m:
            fails.append("금지 표기 '%s' in [%s] %s" % (m.group(0), lay, s[:60]))
    # 치수 인쇄 금지(바실리카 높이·영묘 치수·극장 지름·거상 치수): 그 라벨·주석에는 '숫자 + m'가 없어야 한다
    n_dim = 0
    for l_ in L:
        key = (str(l_["name"]) + " " + l_["kind"] + " " + " ".join(str(G(l_["raw"], k, default="")) for k in ("en", "ko", "sup"))).lower()
        if not any(k in key for k in NO_DIM_KEYS):
            continue
        n_dim += 1
        lines = []
        for k in ("en", "ko", "sup", "text", "body", "본문", "lines", "tag_text"):
            v = G(l_["raw"], k)
            if isinstance(v, str):
                lines.append(v)
            elif isinstance(v, list):
                lines += [x for x in v if isinstance(x, str)]
        for s in lines:
            mm_ = DIMENSION.search(s)
            if mm_:
                fails.append("치수 인쇄 금지 '%s': %s — %s" % (mm_.group(0), l_["name"], s[:40]))
    if not texts:
        fails.append("자료 없음: drawn.texts가 비어 있다")
    rule("①", "인쇄 글 금지 패턴 0회(작업 이름·티어 이름·치수 단위 mm·검사·위치도·연대기·자리 예약·선택 대기·저탄소·41%·29%, 조각상 문장·반죽 붓기·퐁 뒤 가르·이름 유래, 새 랜드마크·거상 치수; m·km·'모식' 허용)",
         fails, {"texts_scanned": len(strings), "no_dimension_labels": n_dim})

    # ② 라벨: 배율 1.00, 글자면 결정 7 ±0.1, 피치 4.15±0.05, 슬롯 넘침 ≤ 0.5mm, 라벨·길·건물·지시선과 2mm 이상
    fails, info = [], {"labels": len(L), "classified_texts": 0, "unclassified_texts": 0}
    if not L:
        fails.append("자료 없음: drawn.labels가 비어 있다")
    for t in texts:
        c, f = cat_of(t), face_of(t)
        if c is None:
            info["unclassified_texts"] += 1
            continue
        info["classified_texts"] += 1
        if f is None:
            fails.append("글자면 자료 없음: [%s] %s" % (c, text_of(t)[:30]))
            continue
        ok, exp = face_ok(c, f)
        if not ok:
            fails.append("글자면 %.2f ≠ %s(%s) — %s" % (f, exp, c, text_of(t)[:30]))
        p = G(t, "pitch", "line_pitch", "피치", "줄 피치")
        if _isnum(p) and c in PITCH and abs(p - PITCH[c]) > TOL_PITCH:
            fails.append("줄 피치 %.2f ≠ %.2f(%s) — %s" % (p, PITCH[c], c, text_of(t)[:30]))
    for i, l_ in enumerate(L):
        raw, nm = l_["raw"], l_["name"]
        sc = G(raw, "scale", "배율", "s")
        if not _isnum(sc):
            fails.append("배율 자료 없음: %s" % nm)
        elif abs(sc - 1.0) > 0.005:
            fails.append("배율 %.2f ≠ 1.00: %s" % (sc, nm))
        faces = G(raw, "faces", "글자면", default={}) or {}
        is_annot = ("소품 주석" in l_["kind"]) or ("annot" in l_["kind"].lower())
        if is_annot:
            info["prop_annotations"] = info.get("prop_annotations", 0) + 1
            for k, v in (faces.items() if isinstance(faces, dict) else []):
                if _isnum(v):
                    ok, exp = face_ok("prop_annot", v)
                    if not ok:
                        fails.append("소품 주석 글자면 %s %.2f ≠ %s: %s" % (k, v, exp, nm))
            if not any(_isnum(v) for v in (faces.values() if isinstance(faces, dict) else [])):
                fails.append("소품 주석 글자면 자료 없음: %s" % nm)
        else:
            for k, cat in (("en", "label_en"), ("ko", "label_ko"), ("sup", "label_sup"), ("body", "label_body"), ("tag", "tag")):
                v = G(faces, k)
                if _isnum(v):
                    ok, exp = face_ok(cat, v)
                    if not ok:
                        fails.append("라벨 글자면 %s %.2f ≠ %s: %s" % (k, v, exp, nm))
        sl = find_slot(slots, nm)
        nbody = len(G(raw, "body", "본문", default=None) or (sl or {}).get("body", []) or [])
        p = G(raw, "pitch", "body_pitch", "피치", "줄 피치")
        if _isnum(p):
            okp = [4.15, PITCH["body"]] if is_annot else [4.15]          # 소품 주석(2.6)은 본문 피치 3.9도 받는다
            if min(abs(p - q) for q in okp) > TOL_PITCH:
                fails.append("라벨 줄 피치 %.2f ≠ %s: %s" % (p, "·".join("%.2f" % q for q in okp), nm))
        elif nbody >= 2 and "태그" not in l_["kind"] and "tag" not in l_["kind"].lower() and not is_annot:
            fails.append("라벨 줄 피치 자료 없음(본문 %d줄): %s" % (nbody, nm))
        # 깃대형(바지선·화산재 운반선): 깃대 수직(x 편차 ≤ 0.1)·끝점 Ø0.9·대상 간격 ≤ 0.5
        if "깃대" in l_["kind"] or "flag" in l_["kind"].lower():
            info["flagpoles"] = info.get("flagpoles", 0) + 1
            lp = l_["lead"]
            lraw = G(raw, "leader", "지시선", "lead", default={}) or {}
            lraw = lraw if isinstance(lraw, dict) else {}
            if not lp or len(lp) < 2:
                fails.append("깃대 자료 없음: %s" % nm)
            else:
                dx_ = max(p_[0] for p_ in lp) - min(p_[0] for p_ in lp)
                if dx_ > 0.1 + 1e-9:
                    fails.append("깃대 수직 아님(x 편차 %.2fmm > 0.1): %s" % (dx_, nm))
                dd_ = G(lraw, "dot_d", "end_d", "끝점 지름")
                if not _isnum(dd_) and _isnum(G(raw, "dot_d", "end_d")):
                    dd_ = G(raw, "dot_d", "end_d")
                if not _isnum(dd_) or abs(dd_ - 0.9) > 0.05 + 1e-9:
                    fails.append("깃대 끝점 지름 %s ≠ 0.9: %s" % (dd_, nm))
                gp_ = G(lraw, "gap", "target_gap", "대상 간격")
                if not _isnum(gp_) and _isnum(G(raw, "gap", "lead_gap", "target_gap")):
                    gp_ = G(raw, "gap", "lead_gap", "target_gap")
                if not _isnum(gp_) or gp_ > 0.5 + 1e-9:
                    fails.append("깃대 대상 간격 %s > 0.5(또는 자료 없음): %s" % (gp_, nm))
        slot_box = G(raw, "slot", "슬롯")
        if not _is_box(slot_box) and sl:
            slot_box = sl.get("box") or sl.get("slot")
        e = bbox_pts(l_["polys"]) if l_["polys"] else None
        if e is None:
            fails.append("라벨 외곽 자료 없음: %s" % nm)
            continue
        if _is_box(slot_box):
            over = max(0.0, slot_box[0] - e[0], e[2] - slot_box[2], slot_box[1] - e[1], e[3] - slot_box[3])
            if over > 0.5 + 1e-9:
                fails.append("슬롯 넘침 %.2fmm: %s" % (over, nm))
        else:
            fails.append("슬롯 자료 없음: %s" % nm)
        dr_dir = str(G(raw, "dir", "direction", "방향", "wall", default=""))[:1]
        sp_dir = str((sl or {}).get("dir") or (sl or {}).get("wall") or "")[:1]
        if dr_dir and sp_dir and dr_dir in "↗↘" and sp_dir in "↗↘" and dr_dir != sp_dir:
            fails.append("방향 %s ≠ 사양 %s: %s" % (dr_dir, sp_dir, nm))
        # 다른 라벨과 2mm
        for j in range(i + 1, len(L)):
            if L[j]["polys"]:
                d = multi_dist(l_["polys"], L[j]["polys"])
                if d < 2.0 - 0.05:
                    fails.append("라벨 간격 %.2fmm < 2: %s ↔ %s" % (d, nm, L[j]["name"]))
        is_tag = ("태그" in l_["kind"]) or ("tag" in l_["kind"].lower())
        # 길과 2mm(말풍선 태그는 시설에 붙는 인접형이라 뺀다)
        if not is_tag and road_polys:
            d = multi_dist(l_["polys"], road_polys)
            if d < 2.0 - 0.05:
                fails.append("라벨-길 간격 %.2fmm < 2: %s" % (d, nm))
        # 지시선과 2mm(자기 지시선 제외)
        for ld in LD:
            if ld.get("label") == nm or not ld["pts"]:
                continue
            d = min(shape_dist(pg, ld["pts"], True, False) for pg in l_["polys"])
            if d < 2.0 - 0.05:
                fails.append("라벨-지시선 간격 %.2fmm < 2: %s ↔ %s" % (d, nm, ld["name"]))
        # 건물(알파 ≥ 128)과 2mm: 렌더 실측 값
        clr = G(raw, "clearance", "clear", "간격", default={}) or {}
        bd = G(clr, "building", "buildings", "건물", "bldg")
        if not is_tag:
            if not _isnum(bd):
                fails.append("라벨-건물 간격 자료 없음: %s" % nm)
            elif bd < 2.0 - 0.05:
                fails.append("라벨-건물 간격 %.2fmm < 2: %s" % (bd, nm))
    if info["classified_texts"] == 0 and not any(G(l_["raw"], "faces", "글자면") for l_ in L):
        fails.append("자료 없음: 글자면 범주(role·layer)나 라벨 faces가 하나도 없다")
    rule("②", "라벨 배율 1.00·글자면 결정 7 ±0.1(소품 주석 2.6·짝 표지 2.2)·피치 4.15±0.05·슬롯 넘침 ≤ 0.5mm·라벨/길/건물/지시선과 2mm 이상·깃대형 깃대 수직(x 편차 ≤ 0.1)·끝점 Ø0.9·대상 간격 ≤ 0.5", fails, info)

    # ③ 패널 본문 ≥ 2.55mm, 주석 ≥ 2.05mm(그리고 어떤 글도 2.05mm 미만 금지)
    fails = []
    for t in texts:
        f = face_of(t)
        if f is None:
            continue
        c = cat_of(t)
        if c in ("body", "label_body") and f < 2.55 - 1e-9:
            fails.append("본문 %.2fmm < 2.55: %s" % (f, text_of(t)[:30]))
        elif f < 2.05 - 1e-9:
            fails.append("글자면 %.2fmm < 2.05(%s): %s" % (f, c or "미분류", text_of(t)[:30]))
    if not any(face_of(t) is not None for t in texts):
        fails.append("자료 없음: 글자면 값이 하나도 없다")
    rule("③", "패널 본문 ≥ 2.55mm, 주석 ≥ 2.05mm", fails)

    # ④ 지시선: 수직·±30°(±0.5°), 꺾임 ≤ 1, 끝점 Ø0.9±0.05, 대상 간격 ≤ 0.5mm, 교차 0
    fails, info = [], {"leaders": len(LD)}
    if not leaders:
        fails.append("자료 없음: drawn.leaders가 비어 있다")
    for ld in LD:
        pts, nm, raw = ld["pts"], ld["name"], ld["raw"] or {}
        if not pts or len(pts) < 2:
            fails.append("꼭짓점 자료 없음: %s" % nm)
            continue
        dirs = seg_dirs(pts)
        for a, Ls in dirs:
            if not ang_ok(a):
                fails.append("각도 %.1f°(수직·±30° 아님): %s" % (a if a <= 90 else a - 180, nm))
        if len(dirs) - 1 > 1:
            fails.append("꺾임 %d회 > 1: %s" % (len(dirs) - 1, nm))
        dd = G(raw, "dot_d", "end_d", "끝점 지름", "dot_diameter", "dot")
        if not _isnum(dd) and _isnum(G(raw, "dot_r", "끝점 반지름")):
            dd = 2.0 * G(raw, "dot_r", "끝점 반지름")
        if not _isnum(dd):
            fails.append("끝점 지름 자료 없음: %s" % nm)
        elif abs(dd - 0.9) > 0.05 + 1e-9:
            fails.append("끝점 지름 %.2f ≠ 0.9: %s" % (dd, nm))
        gap = G(raw, "gap", "target_gap", "대상 간격", "gap_mm")
        if not _isnum(gap):
            fails.append("대상 간격 자료 없음: %s" % nm)
        elif gap > 0.5 + 1e-9:
            fails.append("대상 간격 %.2fmm > 0.5: %s" % (gap, nm))
    for i in range(len(LD)):
        for j in range(i + 1, len(LD)):
            if LD[i]["pts"] and LD[j]["pts"] and lines_cross(LD[i]["pts"], LD[j]["pts"]):
                fails.append("지시선 교차: %s ↔ %s" % (LD[i]["name"], LD[j]["name"]))
    for ld in LD:
        if not ld["pts"]:
            continue
        for l_ in L:
            if ld.get("label") == l_["name"]:
                continue
            if any(line_crosses_poly(ld["pts"], pg) for pg in l_["polys"]):
                fails.append("지시선-라벨 교차: %s ↔ %s" % (ld["name"], l_["name"]))
    rule("④", "지시선 수직·±30°(±0.5°)·꺾임 ≤ 1·끝점 Ø0.9±0.05·대상 간격 ≤ 0.5mm·교차 0", fails, info)

    # ⑤ 길-지면 간격 ≤ 1.6mm(판테온·욕장·메텔라·시장·콜로세움·바실리카–R2)
    fails, info = [], {}
    groups = {"판테온": ["판테온", "pantheon"], "욕장": ["욕장", "bath", "caracalla"], "메텔라": ["메텔라", "metella"],
              "시장": ["시장", "market", "traian"], "콜로세움": ["콜로세움", "colosse", "arena", "히어로"],
              "바실리카": ["바실리카", "basilica", "maxentius"]}
    given = G(dr, "road_gaps", "길 간격", default={}) or {}
    for g, keys in groups.items():
        v = None
        for k, x in (given.items() if isinstance(given, dict) else []):
            if any(kk in norm(k) for kk in keys) and _isnum(x):
                v = x if v is None else min(v, x)
        fps = [f for f in footprints if any(kk in norm(G(f, "name", "id", default="")) for kk in keys)]
        if fps and road_polys:
            polys = []
            for f in fps:
                polys += as_polys(f)
            if polys:
                d = multi_dist(polys, road_polys)
                v = d if v is None else min(v, d)
        if v is None:
            fails.append("자료 없음: %s 지면 다각형 또는 길 다각형" % g)
            continue
        info[g] = round(v, 2)
        if v > 1.6 + 1e-9:
            fails.append("%s 길-지면 간격 %.2fmm > 1.6" % (g, v))
    rule("⑤", "길-지면 간격 ≤ 1.6mm(판테온·욕장·메텔라·시장·콜로세움·바실리카–R2)", fails, info)

    # ⑥ S 막대 바깥 길이 비 20.0±0.2(높이 4.0, 같은 왼끝)
    fails, info = [], {}
    bars = as_list(G(dr, "s_bars", "S 막대", default=[]))
    parsed = []
    for b in bars:
        nm = str(G(b, "name", "id", "kind", default=""))
        x0, x1 = G(b, "x0", "left", "x_left"), G(b, "x1", "right", "outer_x", "x_right")
        hh = G(b, "h", "height", "높이")
        bx = G(b, "box", "bbox", "rect", "geom")
        if _is_box(bx):
            x0 = bx[0] if x0 is None else x0
            x1 = bx[2] if x1 is None else x1
            hh = (bx[3] - bx[1]) if hh is None else hh
        if _isnum(x0) and _isnum(x1):
            parsed.append({"name": nm, "x0": float(x0), "x1": float(x1), "len": float(x1) - float(x0), "h": hh})
    if len(parsed) < 2:
        fails.append("자료 없음: S 막대 2개")
    else:
        mod = [p for p in parsed if "현대" in p["name"] or "modern" in p["name"].lower()]
        rom = [p for p in parsed if "로마" in p["name"] or "roman" in p["name"].lower()]
        srt = sorted(parsed, key=lambda p: p["len"])
        m_, r_ = (mod[0] if mod else srt[0]), (rom[0] if rom else srt[-1])
        ratio = r_["len"] / m_["len"] if m_["len"] > 0 else float("inf")
        info = {"modern_len": round(m_["len"], 2), "roman_len": round(r_["len"], 2), "ratio": round(ratio, 2)}
        if abs(ratio - 20.0) > 0.2 + 1e-9:
            fails.append("바깥 길이 비 %.2f ≠ 20.0±0.2" % ratio)
        if abs(m_["x0"] - r_["x0"]) > 0.1:
            fails.append("왼끝이 다르다: %.2f vs %.2f" % (m_["x0"], r_["x0"]))
        for p in (m_, r_):
            if _isnum(p["h"]) and abs(p["h"] - 4.0) > 0.1:
                fails.append("막대 높이 %.2f ≠ 4.0: %s" % (p["h"], p["name"]))
    rule("⑥", "S 막대 바깥 길이 비 20.0±0.2", fails, info)

    # ⑦ 밀도 ≥ 39.3%: 판정은 전체 무대(173,460mm², 레퍼런스와 같은 정의). 열린 무대(무대 − 패널·Detail 덮는 면적) 값도 기록한다
    fails, info = [], {}
    den = G(dr, "density", "밀도")
    pct_full, pct_open = None, None

    def _pct(v):
        return None if not _isnum(v) else (v * 100.0 if v <= 1.0 else float(v))
    if _isnum(den):
        pct_open = _pct(den)
    elif isinstance(den, dict):
        info = {k: v for k, v in den.items() if _isnum(v)}
        num = G(den, "num_mm2", "numerator", "분자")
        if _isnum(num):
            pct_full = 100.0 * num / STAGE_AREA_FULL                       # 분모는 사양 무대(확장 0) 173,460mm²
        if pct_full is None:
            pct_full = _pct(G(den, "pct_full_stage", "pct_full", "full_pct", "pct_stage", "전체 무대"))
        pct_open = _pct(G(den, "pct_open_stage", "pct_open", "open_pct", "열린 무대"))
        if pct_open is None and _isnum(num) and _isnum(G(den, "den_mm2", "denominator")):
            pct_open = 100.0 * num / G(den, "den_mm2", "denominator")
        if pct_open is None:
            pct_open = _pct(G(den, "pct", "percent", "value", "밀도"))
        st = G(den, "stage_mm2", "stage")
        if _isnum(st) and abs(st - STAGE_AREA_FULL) > 1.0:
            fails.append("render 무대 면적 %.0f ≠ 사양 무대 %.0f mm²(STAGE_EXT 해제 미반영)" % (st, STAGE_AREA_FULL))
    if pct_full is None:
        fails.append("자료 없음: drawn.density(전체 무대 기준 num_mm2)")
    else:
        info["pct_full_stage"] = round(pct_full, 2)
        info["full_stage_mm2"] = STAGE_AREA_FULL
        if pct_full < 39.3 - 1e-9:
            fails.append("밀도(전체 무대) %.2f%% < 39.3%%" % pct_full)
    if pct_open is not None:
        info["pct_open_stage"] = round(pct_open, 2)
    rule("⑦", "밀도 ≥ 39.3%(렌더 실측, 전체 무대 173,460mm² 기준 판정 · 열린 무대 값 기록)", fails, info)

    # ⑧ 인물 군 3곳, 이웃 발점 간격 3.5~5mm, 군마다 5~7명
    fails, info = [], {}
    crowds = as_list(G(dr, "crowds", "인물 군", default=[]))
    if len(crowds) < 3:
        fails.append("인물 군 %d곳 < 3" % len(crowds))
    for k, g in enumerate(crowds):
        nm = str(G(g, "name", "id", default=k))
        feet = G(g, "feet", "foot_pts", "발점", "pts", "people", default=None)
        pts = []
        if isinstance(feet, list):
            for f in feet:
                if isinstance(f, dict):
                    f = G(f, "foot", "pt", "xy")
                if isinstance(f, (list, tuple)) and len(f) >= 2 and _isnum(f[0]):
                    pts.append((float(f[0]), float(f[1])))
        n = len(pts) if pts else G(g, "n", "count", "명")
        if not _isnum(n) or not (5 <= n <= 7):
            fails.append("군 %s 인원 %s(5~7명 아님)" % (nm, n))
        if len(pts) >= 2:
            nn = [min(math.hypot(p[0] - q[0], p[1] - q[1]) for q in pts if q is not p) for p in pts]
            lo, hi = min(nn), max(nn)
        else:
            sp_ = G(g, "spacing", "간격", default=None)
            lo, hi = (sp_[0], sp_[1]) if isinstance(sp_, (list, tuple)) and len(sp_) == 2 else (None, None)
        if lo is None:
            fails.append("군 %s 간격 자료 없음" % nm)
        else:
            info[nm] = [round(lo, 2), round(hi, 2)]
            if lo < 3.5 - 0.05 or hi > 5.0 + 0.05:
                fails.append("군 %s 이웃 간격 %.2f~%.2fmm(3.5~5 밖)" % (nm, lo, hi))
    rule("⑧", "인물 군 3곳·이웃 발점 간격 3.5~5mm", fails, info)

    # ⑨ 포르투스: 입구 18~22mm, 섬 양옆 물길 ≥ 4mm, 운하 2곳 연속
    fails, info = [], {}
    po = G(dr, "portus", "포르투스", default={}) or {}
    ent = G(po, "entrance_w", "entrance_mm", "entrance_screen_w_mm", "entrance", "mouth_w", "입구 폭", "입구")
    if not _isnum(ent):
        fails.append("자료 없음: 입구 폭")
    else:
        info["entrance_mm"] = ent
        if not (18.0 - 1e-9 <= ent <= 22.0 + 1e-9):
            fails.append("입구 폭 %.2fmm(18~22 밖)" % ent)
    iw = G(po, "island_water", "island_gaps", "ground_water_gap_mm", "섬 양옆", "island_water_mm")
    if isinstance(iw, dict):
        iw = list(iw.values())
    if not (isinstance(iw, (list, tuple)) and len(iw) >= 2 and all(_isnum(v) for v in iw)):
        fails.append("자료 없음: 섬 양옆 물길")
    else:
        info["island_water_mm"] = iw
        if min(iw) < 4.0 - 1e-9:
            fails.append("섬 옆 물길 %.2fmm < 4" % min(iw))
    # 탑까지 포함한 양쪽 보이는 물(탑–팔 끝) ≥ 4mm
    tw = G(po, "tower_to_arm_tips", "tower_water", "탑–팔 끝", "tower_gaps")
    if isinstance(tw, dict):
        tw = list(tw.values())
    if not (isinstance(tw, (list, tuple)) and len(tw) >= 2 and all(_isnum(v) for v in tw)):
        fails.append("자료 없음: tower_to_arm_tips(탑–두 팔 끝 보이는 물)")
    else:
        info["tower_to_arm_tips_mm"] = tw
        if min(tw) < 4.0 - 1e-9:
            fails.append("탑–팔 끝 보이는 물 %.2fmm < 4" % min(tw))
    cn = as_list(G(po, "canals", "운하", default=[]))
    info["canals"] = len(cn)
    if len(cn) < 2:
        fails.append("운하 %d곳 < 2" % len(cn))
    for k, c in enumerate(cn):
        ok = G(c, "continuous", "연속", "ok", "open")
        if ok is not True:
            fails.append("운하 %s 연속 아님(또는 자료 없음)" % G(c, "name", "id", default=k))
        ow = G(c, "opening_w", "opening", "개구부", "opening_mm")
        if _isnum(ow) and ow < 3.0 - 0.05:
            fails.append("운하 %s 개구부 %.2fmm < 3" % (G(c, "name", "id", default=k), ow))
    rule("⑨", "포르투스 입구 18~22mm·섬 양옆 물길 ≥ 4mm·탑–두 팔 끝 보이는 물 ≥ 4mm·운하 2곳 연속", fails, info)

    # ⑩ 티어 색 사용 0
    fails = []
    tc = G(dr, "tier_color_uses", "티어 색", default=None)
    n_tc = None
    if _isnum(tc):
        n_tc = int(tc)
    elif isinstance(tc, (list, tuple)):
        n_tc = len(tc)
    elif isinstance(tc, dict):
        n_tc = int(G(tc, "count", "n", default=sum(v for v in tc.values() if _isnum(v))))
    if n_tc is None:
        fails.append("자료 없음: tier_color_uses")
    elif n_tc != 0:
        fails.append("티어 색 %d회 사용" % n_tc)
    rule("⑩", "티어 색(Core·Basic·Detail·Support) 인쇄 사용 0", fails, {"uses": n_tc})

    # ⑪ 위계(그린 상자 기준): Basic 최소 ≥ Detail 최대(Z1 합성), Detail 최소 ≥ Support × 1.1, R·T 0
    fails, info = [], {}
    sp_tier = {}
    for p in (spec.get("frame", {}).get("panels", []) if spec else []):
        sp_tier[p["id"]] = p.get("tier")
    B_ = {"Basic": {}, "Detail": {}, "Support": {}}
    z1 = []
    for b in boxes:
        bid = str(G(b, "id", "name", default="?"))
        tier = G(b, "tier", "티어")
        circ = G(b, "circle")
        box = G(b, "box", "rect", "bbox", "geom")
        if not _is_box(box) and isinstance(circ, dict):
            c, dd = circ.get("c"), circ.get("d")
            box = [c[0] - dd / 2, c[1] - dd / 2, c[0] + dd / 2, c[1] + dd / 2]
        if not _is_box(box):
            pl = as_polys(b)
            box = bbox_pts(pl) if pl else None
        if box is None:
            fails.append("상자 자료 없음: %s" % bid)
            continue
        key = bid.split(" ")[0]
        if key in ("R", "T"):
            fails.append("뺀 패널 %s가 그려졌다" % key)
            continue
        if key.startswith("Z1"):
            z1.append((bid, box, G(b, "kind", default="")))
            continue
        if tier is None:
            tier = sp_tier.get(key) or ("Detail" if key[:1] in ("C", "Z") else None)
        if tier not in B_:
            continue
        B_[tier][key] = (box[2] - box[0]) * (box[3] - box[1])
    if z1:
        comp = [b for b in z1 if "composite" in norm(b[0]) + norm(b[2]) or "합성" in b[0] + str(b[2])]
        zb = comp[0][1] if comp else [min(b[1][0] for b in z1), min(b[1][1] for b in z1), max(b[1][2] for b in z1), max(b[1][3] for b in z1)]
        B_["Detail"]["Z1"] = (zb[2] - zb[0]) * (zb[3] - zb[1])
    for t in ("Basic", "Detail", "Support"):
        if not B_[t]:
            fails.append("자료 없음: %s 상자" % t)
    drawn_panels = [k for t in B_ for k in B_[t] if k in PRINT_PANEL_IDS_ or re.match(r"^(L|B|D|S|P\d)$", k)]
    for pid in PRINT_PANEL_IDS_:
        if pid not in drawn_panels:
            fails.append("인쇄 패널 상자 없음: %s(6패널 L·P2·B·D·S·P5 기준)" % pid)
    info["panels_drawn"] = sorted(drawn_panels, key=lambda k: PRINT_PANEL_IDS_.index(k) if k in PRINT_PANEL_IDS_ else 99)
    if all(B_[t] for t in ("Basic", "Detail", "Support")):
        bmin = min(B_["Basic"].items(), key=lambda kv: kv[1])
        dmax = max(B_["Detail"].items(), key=lambda kv: kv[1])
        dmin = min(B_["Detail"].items(), key=lambda kv: kv[1])
        smax = max(B_["Support"].items(), key=lambda kv: kv[1])
        info.update({"basic_min": [bmin[0], round(bmin[1])], "detail_max": [dmax[0], round(dmax[1])], "detail_min": [dmin[0], round(dmin[1])],
                     "support": [smax[0], round(smax[1])], "ratio_basic_detail": round(bmin[1] / dmax[1], 3), "ratio_detail_support": round(dmin[1] / smax[1], 3),
                     "areas": {t: {k: round(v) for k, v in B_[t].items()} for t in B_}})
        if bmin[1] < dmax[1]:
            fails.append("Basic 최소 %s %.0f < Detail 최대 %s %.0f" % (bmin[0], bmin[1], dmax[0], dmax[1]))
        if dmin[1] < 1.1 * smax[1]:
            fails.append("Detail 최소 %s %.0f < Support %.0f × 1.1" % (dmin[0], dmin[1], smax[1]))
        if "Z1" not in B_["Detail"]:
            fails.append("Z1 상자 자료 없음")
    objs = G(dr, "objects", "오브젝트", default=None)
    if objs:
        oa = {}
        for o in as_list(objs):
            ob = as_polys(o)
            if ob:
                bb = bbox_pts(ob)
                oa[str(G(o, "id", "name"))] = (bb[2] - bb[0]) * (bb[3] - bb[1])
        hero = next((v for k, v in oa.items() if k in ("hero", "콜로세움") or "히어로" in k), None)
        lms = {k: v for k, v in oa.items() if re.match(r"^L\d", k)}
        ves = next((v for k, v in oa.items() if k == "V" or "베수비오" in k), None)
        if hero and lms:
            info["hero_over_landmark_max"] = round(hero / max(lms.values()), 2)
            if hero < 1.1 * max(lms.values()):
                fails.append("콜로세움 %.0f < 랜드마크 최대 × 1.1" % hero)
        if ves and lms and ves > min(lms.values()) / 1.1:
            fails.append("베수비오 %.0f > 랜드마크 최소 ÷ 1.1" % ves)
    rule("⑪", "위계(그린 상자, 6패널 L·P2·B·D·S·P5): Basic 최소 ≥ Detail 최대(Z1 합성), Detail 최소 ≥ Support × 1.1, R·T 0", fails, info)

    # ⑫ 글 블록과 상자 테두리 ≥ 3mm(테두리를 그린 상자: 콜아웃·Z1 원·테두리 표시가 있는 상자)
    fails, info = [], {"bordered_boxes": 0, "texts_checked": 0}
    bordered = []
    for b in boxes:
        bid = str(G(b, "id", "name", default="?"))
        flag = G(b, "border", "stroke", "frame", "테두리")
        kind = norm(G(b, "kind", "종류", default=""))
        circ = G(b, "circle")
        if isinstance(circ, dict) and (flag is None or flag):
            bordered.append(("circle", bid, circ))
            continue
        if flag is False:
            continue
        if flag or "callout" in kind or "콜아웃" in kind or re.match(r"^C\d", bid):
            box = G(b, "box", "rect", "bbox")
            if _is_box(box):
                bordered.append(("rect", bid, box))
    info["bordered_boxes"] = len(bordered)
    for t in texts:
        tp = as_polys(G(t, "bbox", "box", "outline", "외곽", "poly"))
        if not tp:
            continue
        e = bbox_pts(tp)
        cx, cy = (e[0] + e[2]) / 2, (e[1] + e[3]) / 2
        for kind, bid, g in bordered:
            if kind == "rect":
                if not (g[0] <= cx <= g[2] and g[1] <= cy <= g[3]):
                    continue
                d = min(e[0] - g[0], e[1] - g[1], g[2] - e[2], g[3] - e[3])
            else:
                c, R = g["c"], g["d"] / 2.0
                if math.hypot(cx - c[0], cy - c[1]) > R:
                    continue
                d = R - max(math.hypot(x - c[0], y - c[1]) for x in (e[0], e[2]) for y in (e[1], e[3]))
            info["texts_checked"] += 1
            if d < 3.0 - 0.05:
                fails.append("글-테두리 %.2fmm < 3: %s ∈ %s" % (d, text_of(t)[:24], bid))
    if not bordered:
        fails.append("자료 없음: 테두리 상자(콜아웃·Z1)")
    elif info["texts_checked"] == 0:
        fails.append("자료 없음: 테두리 상자 안 글의 외곽(bbox)이 하나도 없다")
    rule("⑫", "글 블록과 상자 테두리 ≥ 3mm", fails, info)

    # ⑬ 필수 요소 존재(그린 결과): 패널 6·랜드마크 L1~L9·네로 거상·R7·폰스 아일리우스 다리 + 짝 표지 A 3·B~D 각 2·숫자 1~4 각 2(글자·중심·출처)
    fails, info = [], {}
    box_ids = [str(G(b, "id", "name", default="")).split(" ")[0] for b in boxes]
    for pid in PRINT_PANEL_IDS_:
        if pid not in box_ids:
            fails.append("패널 없음: %s" % pid)
    objs_l = as_list(G(dr, "objects", "오브젝트", default=[]))
    obj_ids = [str(G(o, "id", default="")) for o in objs_l]
    obj_names = [str(G(o, "name", "id", default="")) for o in objs_l]
    fp_names = [str(G(f, "name", "id", default="")) for f in footprints]
    if not objs_l:
        fails.append("자료 없음: drawn.objects(랜드마크 id L1~L9)")
    for lid in REQUIRED_LM_:
        if lid not in obj_ids:
            fails.append("랜드마크 없음: %s" % lid)
    all_names = obj_names + fp_names
    if not any("네로" in n and "거상" in n for n in all_names):
        fails.append("소품 없음: 네로 거상(받침 + 거상)")
    if not any(norm(G(r, "id", default="")) == "r7" for r in roads):
        fails.append("길 없음: R7")
    if not any(("폰스" in n or "pons" in n.lower() or "다리" in n) for n in all_names):
        fails.append("다리 없음: 폰스 아일리우스 다리(footprints '폰스 아일리우스 다리')")
    info["objects"] = len(objs_l)
    # 짝 표지
    SRC_K = ("source", "src", "출처", "where", "from", "side", "origin")

    def nsrc(v):
        v = str(v or "").lower()
        return "map" if ("map" in v or "지도" in v) else "detail" if any(k in v for k in ("detail", "z1", "확대", "콜아웃", "callout")) else \
            "panel" if any(k in v for k in ("panel", "패널", "p2", "칸")) else (v or None)
    marks = []
    for t in texts:
        if norm(G(t, "role", "역할", default="")) != "mark":
            continue
        g = str(text_of(t)).strip().upper()
        c = G(t, "c", "center", "중심", "mark_pt", "pt")
        if not (isinstance(c, (list, tuple)) and len(c) >= 2 and _isnum(c[0])):
            tp = as_polys(G(t, "bbox", "box", "poly", "outline"))
            e = bbox_pts(tp) if tp else None
            c = [(e[0] + e[2]) / 2, (e[1] + e[3]) / 2] if e else None
        r_ = G(t, "r", "radius", "mark_r", "반지름")
        marks.append({"glyph": g, "c": c, "source": nsrc(G(t, *SRC_K)), "r": r_ if _isnum(r_) else None})
    cnt = {}
    for m_ in marks:
        cnt[m_["glyph"]] = cnt.get(m_["glyph"], 0) + 1
    info["marks"] = cnt
    info["marks_total"] = len(marks)
    for g, n in REQUIRED_MARKS_.items():
        if cnt.get(g, 0) != n:
            fails.append("짝 표지 %s %d개 ≠ %d" % (g, cnt.get(g, 0), n))
    extra_g = sorted(g for g in cnt if g not in REQUIRED_MARKS_)
    if extra_g:
        fails.append("예상 밖 짝 표지: %s" % "·".join(extra_g))
    want_src = {"A": ["detail", "map", "panel"], "B": ["detail", "map"], "C": ["detail", "map"], "D": ["detail", "map"],
                "1": ["map", "panel"], "2": ["map", "panel"], "3": ["map", "panel"], "4": ["map", "panel"]}
    no_src = [m_["glyph"] for m_ in marks if not m_["source"]]
    if no_src:
        fails.append("표지 출처(map/detail/panel) 자료 없음: %s" % "·".join(no_src))
    else:
        for g, ws in want_src.items():
            got = sorted(m_["source"] for m_ in marks if m_["glyph"] == g)
            if got and got != ws:
                fails.append("표지 %s 출처 %s ≠ %s" % (g, "·".join(got), "·".join(ws)))
    if any(m_["c"] is None for m_ in marks):
        fails.append("표지 중심 자료 없음: %s" % "·".join(m_["glyph"] for m_ in marks if m_["c"] is None))
    for m_ in marks:
        if m_["r"] is not None and abs(m_["r"] - MARK_R) > 0.1 + 1e-9:
            fails.append("표지 %s 반지름 %.2f ≠ %.1f" % (m_["glyph"], m_["r"], MARK_R))
    # 지도 위 표지는 다른 글(라벨·바닥 글)·남의 지시선·다른 표지와 2mm 이상
    def circ_poly(c, r, n=24):
        return [(c[0] + r * math.cos(2 * math.pi * k / n), c[1] + r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    floor_polys = [as_polys(G(t, "poly", "bbox", "box")) for t in texts if norm(G(t, "role", default="")).startswith("floor")]
    clr = []
    for i, m_ in enumerate(marks):
        if m_["source"] != "map" or m_["c"] is None:
            continue
        R = m_["r"] or MARK_R
        cp = circ_poly(m_["c"], R)
        best = float("inf")
        for l_ in L:
            if l_["polys"]:
                best = min(best, multi_dist([cp], l_["polys"]))
        for fp_ in floor_polys:
            if fp_:
                best = min(best, multi_dist([cp], fp_))
        for ld in LD:
            if not ld["pts"]:
                continue
            own = G(ld["raw"] or {}, "mark")
            own = G(own, "letter", "glyph", "text") if isinstance(own, dict) else own
            if own is not None and str(own).strip().upper() == m_["glyph"]:
                continue
            best = min(best, shape_dist(cp, ld["pts"], True, False))
        for j, o in enumerate(marks):
            if j != i and o["c"] is not None:
                best = min(best, math.hypot(o["c"][0] - m_["c"][0], o["c"][1] - m_["c"][1]) - R - (o["r"] or MARK_R))
        clr.append([m_["glyph"], round(best, 2)])
        if best < 2.0 - 0.05:
            fails.append("지도 표지 %s 간격 %.2fmm < 2(글·지시선·표지)" % (m_["glyph"], best))
    info["map_mark_clearance_mm"] = clr
    rule("⑬", "필수 요소 존재: 패널 6(L·P2·B·D·S·P5)·랜드마크 L1~L9·네로 거상·R7·폰스 아일리우스 다리·짝 표지 A 3·B~D 각 2·숫자 1~4 각 2(글자·중심·출처), 지도 표지 간격 ≥ 2mm", fails, info)

    # ⑭ 건물 실루엣 간격 ≥ 2mm(footprints를 건물별로 묶어 서로 다른 건물 쌍만. 길–지면 접속·다리–강·다리–R7·수도교–욕장 급수 접속은 제외)
    fails, info = [], {}
    MERGE = {"공사장": "콜로세움", "폰스": "영묘", "다리": "영묘", "아일리우스": "영묘"}
    SKIP_KIND = ("detail", "배경", "길", "road", "강", "river", "물", "water", "바다", "sea")
    VESSEL = ("바지선", "선체", "운반선", "배 ", "범선")
    KNOWN = ("콜로세움", "판테온", "욕장", "수도교", "시장", "메텔라", "포르투스", "하역장", "바실리카", "영묘", "극장", "네로", "오스티아", "석회 가마", "빌라", "농장")
    CONTACT_OK = {frozenset(["욕장", "수도교"])}

    def bgroup(f):
        nm = str(G(f, "name", "id", default=""))
        kd = norm(G(f, "kind", "종류", default=""))
        if any(k in kd for k in SKIP_KIND) or any(nm.startswith(v) or v in nm for v in VESSEL) or nm.startswith("확대 창"):
            return None
        for k, v in MERGE.items():
            if nm.startswith(k) or (k in nm and k in ("폰스", "아일리우스")):
                return v
        for k in KNOWN:
            if k in nm:
                return k
        return nm.split(" ")[0] if nm else None
    grp = {}
    for f in footprints:
        g = bgroup(f)
        if g:
            grp.setdefault(g, []).extend(as_polys(f))
    if not grp:
        fails.append("자료 없음: drawn.footprints(건물 지면·면 다각형)")
    gk = sorted(grp)
    pairs = []
    for i in range(len(gk)):
        for j in range(i + 1, len(gk)):
            a, b = gk[i], gk[j]
            if frozenset([a, b]) in CONTACT_OK or not grp[a] or not grp[b]:
                continue
            ea, eb = bbox_pts(grp[a]), bbox_pts(grp[b])
            dx = max(0.0, eb[0] - ea[2], ea[0] - eb[2])
            dy = max(0.0, eb[1] - ea[3], ea[1] - eb[3])
            if math.hypot(dx, dy) > 6.0:
                continue
            d = multi_dist(grp[a], grp[b])
            pairs.append([a, b, round(d, 2)])
            if d < 2.0 - 0.05:
                fails.append("건물 실루엣 간격 %.2fmm < 2: %s ↔ %s" % (d, a, b))
    info["groups"] = gk
    info["near_pairs_mm"] = sorted(pairs, key=lambda p_: p_[2])[:30]
    info["excluded"] = "길–지면 접속(⑤가 ≤ 1.6mm로 본다)·다리–강·다리–R7(다리는 영묘 묶음)·수도교–욕장(급수 접속)·선박·Detail·배경 산"
    rule("⑭", "건물 실루엣 간격 ≥ 2mm(footprints 건물 묶음 쌍, 길–지면 접속·다리–강·다리–R7 제외)", fails, info)

    # ⑮ 운하: 사양 끝점(core_map.portus_geometry.canals plan_y·plan_x) = 그린 끝점 ±0.3mm, render 추가 연장 0
    fails, info = [], {}
    sp_c = (((spec or {}).get("core_map") or {}).get("portus_geometry") or {}).get("canals") or []
    dr_c = as_list(G(po, "canals", "운하", default=[]))
    if not sp_c:
        fails.append("자료 없음: 사양 core_map.portus_geometry.canals")
    if not dr_c:
        fails.append("자료 없음: drawn.portus.canals")
    rows = []
    for k, c in enumerate(sp_c):
        nm = str(c.get("name", k))
        d_ = next((x for x in dr_c if str(G(x, "name", "id", default="")) == nm), dr_c[k] if k < len(dr_c) else None)
        if d_ is None:
            fails.append("그린 운하 없음: %s" % nm)
            continue
        for key in ("plan_y", "plan_x"):
            sv, dv = c.get(key), G(d_, key, "y" if key == "plan_y" else "x")
            if key == "plan_x" and dv is None:
                continue
            if not (isinstance(sv, (list, tuple)) and isinstance(dv, (list, tuple)) and len(sv) == 2 and len(dv) == 2):
                fails.append("운하 %s %s 자료 없음" % (nm, key))
                continue
            dev = max(abs(float(sv[0]) - float(dv[0])), abs(float(sv[1]) - float(dv[1])))
            rows.append([nm, key, list(sv), list(dv), round(dev, 2)])
            if dev > 0.3 + 1e-9:
                fails.append("운하 %s %s 사양 %s ≠ 그림 %s(편차 %.2fmm > 0.3)" % (nm, key, list(sv), list(dv), dev))
    info["canals"] = rows
    rule("⑮", "운하 사양 끝점 = 그린 끝점 ±0.3mm(render 추가 연장 0)", fails, info)

    # 보조 확인(같이 판정한다): 사양 정리 — '위치도'·'연대기'·'보류'·'선택 대기'는 사용자 원문 인용에만, frame.panels = L·P2·B·D·S·P5, 무대 확장 0
    supp = []
    if spec:
        bad, bad2 = [], []
        for path, s in walk_strings(spec):
            quote = path[:2] in (("meta", "user_review"), ("meta", "user_selection"))
            if path[:2] == ("frame", "print_rules") and path[2:3] in (("forbidden_pattern",), ("forbidden_pattern_ci",), ("forbidden_sentences",)):
                continue                                      # 인쇄 금지 패턴 정의(낱말 목록 자체)
            if ("위치도" in s or "연대기" in s) and not quote:
                bad.append("/".join(path)[:80])
            if ("보류" in s or "선택 대기" in s) and not (quote and path[2:3] in (("words",), ("baseline_words",), ("quote",))):
                bad2.append("/".join(path)[:80])
        supp.append({"name": "사양에 '위치도'·'연대기' 0(사용자 검토·선택 원문 인용·인쇄 금지 패턴 정의 제외)", "pass": not bad, "fails": bad[:20]})
        supp.append({"name": "사양에 '보류'·'선택 대기' 0(사용자 원문 인용·인쇄 금지 패턴 정의 제외)", "pass": not bad2, "fails": bad2[:20]})
        ids = [p.get("id") for p in spec.get("frame", {}).get("panels", [])]
        want = PRINT_PANEL_IDS_
        supp.append({"name": "사양 frame.panels = %s" % "·".join(want), "pass": ids == want, "fails": [] if ids == want else ["frame.panels = %s" % ids]})
        wh = list(spec.get("worker_handoff", {}).keys())
        okw = sorted(wh) == sorted(["map", "panels", "render", "global"])
        supp.append({"name": "worker_handoff 열쇠 = map·panels·render·global", "pass": okw, "fails": [] if okw else ["worker_handoff = %s" % wh]})
    else:
        supp.append({"name": "spec.json", "pass": False, "fails": ["spec.json을 찾지 못함(drawn.json 옆 또는 넷째 인자)"]})
    st_r = G(G(dr, "stage", "무대", default={}) or {}, "rects", default=None)
    if isinstance(st_r, list):
        ok_st = len(st_r) == 1 and all(abs(float(a) - float(b)) < 0.01 for a, b in zip(st_r[0], STAGE_MAIN))
        supp.append({"name": "그린 무대 = STAGE 하나(R·T 확장 0)", "pass": ok_st, "fails": [] if ok_st else ["drawn.stage.rects = %s" % st_r]})
    else:
        supp.append({"name": "그린 무대 = STAGE 하나(R·T 확장 0)", "pass": False, "fails": ["자료 없음: drawn.stage.rects"]})

    nfail = sum(1 for r in rules if not r["pass"]) + sum(1 for s in supp if not s["pass"])
    res = {"drawn": os.path.abspath(drawn_path), "spec": spec_path, "pass": nfail == 0, "fail_count": nfail,
           "rules": rules, "supplementary": supp,
           "contract": "render가 out/drawn.json에 texts(짝 표지는 role 'mark' + 글자·중심·출처 map/detail/panel)·labels(소품 주석·깃대형 포함)·leaders·footprints(바실리카 지면·측랑 볼트·신랑 유적, 영묘 기단·원통, 폰스 아일리우스 다리, 극장 반원 아케이드, 네로 거상 받침·네로 거상, 오스티아 포함)·roads(R7 포함)·boxes(L·P2·B·D·S·P5·Z1·C1·C2·C4)·s_bars·density(num_mm2·전체 무대·열린 무대)·crowds·portus(tower_to_arm_tips·island_water·canals plan_y)·tier_color_uses·objects(L1~L9·V·hero·소품)·stage를 쓴다. 열쇠 별칭은 v2_check.py 사후 검사 부분 참조",
           "rules_count": len(rules)}
    json.dump(res, open(out_path, "w"), ensure_ascii=False, indent=1)
    for r in rules:
        print("%s %s %s" % (r["no"], "통과" if r["pass"] else "실패", r["name"]))
        for f in r["fails"][:6]:
            print("    - " + f)
        if len(r["fails"]) > 6:
            print("    … 외 %d건" % (len(r["fails"]) - 6))
    for s in supp:
        print("보조 %s %s" % ("통과" if s["pass"] else "실패", s["name"]))
        for f in s["fails"][:4]:
            print("    - " + f)
    print("사후 검사 %s: 실패 %d건 → %s" % ("통과" if nfail == 0 else "실패", nfail, out_path))
    return 0 if nfail == 0 else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--post":
        if len(sys.argv) < 4:
            sys.exit("사용: python -I v2_check.py --post <drawn.json> <post_check.json> [spec.json]")
        sys.exit(main_post(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None))
    sys.exit(main_pre(sys.argv[1], sys.argv[2]))
