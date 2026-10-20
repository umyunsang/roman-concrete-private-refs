# -*- coding: utf-8 -*-
"""새 위계 배치 사양 검사. 담당: global
사전 검사(사양 기하): 필수 요소 존재(패널 6·랜드마크 L1~L9·네로 거상·R7·폰스 아일리우스 다리) → 투영 크기 위계(L·P2·B·D·S·P5 + Z1 합성),
  패널 수 5~7, 겹침(L7~L9는 poly_screen), 땅·바다·강(L7~L9는 ground_screen), 길 접촉, 고리 거리, 히어로 군(실루엣·껍질·상자),
  밀도 근사(무대 173,460mm²), 압축 지리(방위 오차·거리 지수, L7~L9 포함).
  사용: python -I v2_check.py <data_dir> <out_dir>   (필수 요소가 하나라도 없으면 v2_check.json을 쓴 뒤 종료 코드 1)
사후 검사(렌더가 실제로 그린 것): out/drawn.json을 21개 규칙(①~㉑)과 보조 확인으로 판정해 out/post_check.json에 쓴다. 실패가 1건이라도 있으면 종료 코드 1.
  사용: python -I v2_check.py --post <drawn.json> <post_check.json> [spec.json] [--info out/info/info_check.json]
d5(기준선 8절·통합 루프 0-1): 사전 baseline_8(8.1 본체·8.2 받침 없음·12:49 히어로 군·D5 Z1 출발점·D7 R7/영묘 높이, 기록)과 위계 D4(투영 상자끼리·건물 실루엣 × 1.2),
  사후 ⑧(인물 군 ≥ 3·키 4.6~5.2)·⑪(그린 외곽 상자끼리: 히어로 = 건물 ∪ 광장, 표준 하한 4,500, 실루엣 × 1.2)·⑯ 인쇄 선 굵기·⑰ 정보 층 정합(INFO_ONLY)·
  ⑱ 8.1·⑲ 8.2·⑳ D5·D7·㉑ P5 계단 + 보조(사양 정리 d5·weight_order·worker_handoff 완료 조건·Blender 인계·drawn 계약 형식).
  자체 시험: python -I v2_check.py --selftest (d4 사양 → 8.1·8.2 실패, d5 사양 → 통과, LocalBanana 복제 감지, 계약 형식)"""
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
    return [round(float(xs.min()) / PX, 1), round(float(ys.min()) / PX, 1), round(float(xs.max() + 1) / PX, 1), round(float(ys.max() + 1) / PX, 1)]


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

    # ── 히어로(콜로세움). d5(기준선 8.1·8.2): 본체 실루엣(타원 + θ 구간 외벽) ∪ 조경 광장(예약 반지름의 화면 타원 + 광장 경계), 받침 0.
    #    d4 옛 형식(map에 새 dict가 없을 때): 팔각 받침 + 앞 세 변 옆면 + 원형 고리 벽(8.2 검사가 실패로 잡는다)
    hm = D.hero_model() if hasattr(D, "hero_model") else {}
    hl = D.hero_landscape() if hasattr(D, "hero_landscape") else {}
    hero_bld = blank()
    for pg in (D.hero_building_polys(hm) if hasattr(D, "hero_building_polys") else []):
        if len(pg) >= 3:
            fill(hero_bld, pg)
    hero_bld &= stage
    plaza = blank()
    if hl.get("legacy") and hl.get("boundary_screen"):                 # 옛 팔각 받침(윗면 + 앞 세 변 옆면)
        oct_ = hl["boundary_screen"][0]
        fill(plaza, oct_)
        side = float(hl.get("base_side") or 0.0)
        if side > 0 and len(oct_) == 8:
            for k in (7, 0, 1):
                a, b = oct_[k], oct_[(k + 1) % 8]
                fill(plaza, [a, b, (b[0], b[1] + side), (a[0], a[1] + side)])
    else:
        c_ = hl.get("center_plan") or getattr(D, "HERO_C_PLAN", None)
        R_ = float(hl["reserve_R"]) if _isnum(hl.get("reserve_R")) else float(getattr(D, "HERO_LANDSCAPE_D5", {}).get("reserve_R_plan", 90.0))
        # 13:33: 광장 0 → 히어로 군 = 건물 ∪ 공사장 ∪ 인물 무리 ∪ 노점 ∪ 네로 거상 받침(예정 상자)
        def _rect(b_):
            fill(plaza, [(b_[0], b_[1]), (b_[2], b_[1]), (b_[2], b_[3]), (b_[0], b_[3])])
        ws0 = (getattr(D, "WORKSITE", None) or {}).get("box")
        if ws0:
            _rect(ws0)
        nr0 = D.find_nero() if hasattr(D, "find_nero") else None
        if isinstance(nr0, dict) and nr0.get("box"):
            _rect(nr0["box"])
        for g_ in (hl.get("crowds") or []):
            cs_ = g_.get("center_screen") if isinstance(g_, dict) else None
            if cs_:
                _rect([cs_[0] - 9.0, cs_[1] - 7.0, cs_[0] + 9.0, cs_[1] + 4.0])
        for sx_, sy_ in getattr(_B, "STALLS_SCREEN", []):
            _rect([sx_ - 4.0, sy_ - 7.0, sx_ + 4.0, sy_ + 1.0])
    plaza &= stage
    hero = hero_bld | plaza
    hero_box = bbox(hero)
    hero_bld_box = bbox(hero_bld)
    hero_bld_sil = area_mm2(hero_bld)
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
    # d5(D4): 콜로세움 건물 실루엣 ≥ 다른 건물 실루엣 각각 × 1.2. 실루엣끼리만 비교한다(상자만 있는 건물은 사후 ⑪이 그린 실루엣으로 판정)
    sil_k = float(getattr(D, "HERO_SIL_OVER_OTHER", 1.2))
    sil_rows, sil_bad, sil_open = [], [], []
    for x in D.LANDMARKS:
        lid = x["id"]
        if lid == "L4":
            a_, src_ = area_mm2(lm["L4"]), "수도교 아치 열 평행사변형"
        elif lid == "L6":
            a_, src_ = area_mm2(lm["L6"]), "포르투스 외형 다각형"
        elif lm_src.get(lid, {}).get("overlap") == "poly_screen":
            a_, src_ = area_mm2(lm[lid]), "poly_screen"
        else:
            a_, src_ = float(ba(x["box"])), "상자(실루엣 자료 없음, 상한)"
        okk = hero_bld_sil >= sil_k * a_
        sil_rows.append({"id": lid, "name": x["name"], "sil_mm2": round(a_), "source": src_, "pass": bool(okk) if src_[:2] != "상자" else (True if okk else None)})
        if not okk:
            (sil_open if src_.startswith("상자") else sil_bad).append(lid)
    checks["콜로세움 건물 실루엣 ≥ 다른 건물 실루엣 × %.1f(사전: 실루엣이 있는 건물만, 상자만 있는 건물은 사후 ⑪)" % sil_k] = (hero_bld_sil > 0) and not sil_bad
    res["hierarchy_rule_d5"] = {
        "basis": "사전 = 투영(예정) 상자끼리·실루엣끼리 비교(통과 보고 아님). 최종 판정은 사후 ⑪(drawn.objects 그린 외곽 상자·sil_mm2)",
        "hero_group": "콜로세움 건물 ∪ 기초 공사장 ∪ 인물 무리 ∪ 노점 ∪ 네로 거상 받침(사용자 13:33, 예정 상자)",
        "hero_group_box": hero_box, "hero_group_area": hero_a, "hero_group_box_d5_decision": getattr(D, "HERO_GROUP_BOX", None),
        "hero_building_box": hero_bld_box, "hero_building_sil_mm2": round(hero_bld_sil),
        "landmark_median": round(med_lm), "hero_over_median": round(hero_a / med_lm, 2),
        "building_sil_rule": "콜로세움 건물 실루엣 ≥ 다른 건물 실루엣 × %.1f" % sil_k, "building_sil_rows": sil_rows,
        "building_sil_fail": sil_bad, "building_sil_undetermined_pre": sil_open,
        "building_sil_over_max_other": round(hero_bld_sil / max([r["sil_mm2"] for r in sil_rows if not r["source"].startswith("상자")] or [1]), 2),
        "model_source": hm.get("source"), "landscape_source": hl.get("source"),
    }
    res["hierarchy"] = {
        "core_stage_mm2": SA, "core_stage_main_mm2": D.STAGE_AREA,
        "hero_box": hero_box, "hero_wh": [round(hero_box[2] - hero_box[0], 1), round(hero_box[3] - hero_box[1], 1)], "hero_area": hero_a,
        "hero_building_box": hero_bld_box, "hero_building_sil_mm2": round(hero_bld_sil),
        "basis": "사전 판정(투영 상자끼리). 예정 상자로 통과를 보고하지 않는다 — 최종은 사후 ⑪",
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
    # d5: 겹침은 본체 실루엣으로 본다(광장은 땅 높이라 앞에 선 소품이 화면에서 덮는 것이 정상. 광장 침범은 평면 예약 반지름 검사 8.2-5가 본다)
    shapes["콜로세움"] = hero if hl.get("legacy") else hero_bld
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
            # d5(D5): '→ 확대 창 Z1' 지시선은 공사장 거푸집 오른쪽 면에서 출발해 Z1 원에 닿는다(지시선 이름이 바뀌어도 허용)
            z1l = [k for k in (a, b) if k.startswith("지시선 ") and re.search(r"→\s*(확대 창\s*)?Z1", k)]
            if z1l and ({a, b} - set(z1l)) & {"공사장", "Detail Z1"}:
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

    # ═════ 11. 기준선 8.1·8.2 + D5·D7 사전 판정(사양 기하로 기록. 사후 ⑱~⑳이 그린 결과로 다시 본다) ═════
    ctx8 = pre_ctx8(D, hm, hl, hero_bld_box, pm)
    items8 = eval_baseline8(hm, hl, ctx8)
    res["baseline_8"] = {"pass": all(i["pass"] for i in items8), "failed": [i["id"] for i in items8 if not i["pass"]], "items": items8,
                         "hero_model_source": hm.get("source"), "landscape_source": hl.get("source"),
                         "rule": "기준선 8.1(본체 비례·방향·부서진 정도·보이는 면)·8.2(받침 없음)·12:49 철회(LocalBanana 조경 복제 0, 승인 설계 히어로 군)·D5(Z1 출발점)·D7(R7·영묘 높이). "
                                 "사전 결과는 기록이고, 사후 ⑱·⑲·⑳이 실패하면 make.py 종료 코드 1",
                         "context": {k: v for k, v in ctx8.items() if k not in ("z1_leader",)}}
    res["warnings"] = warnings

    np.save(out_dir + "/v2_hero_cluster_sil.npy", sil)
    json.dump(res, open(out_dir + "/v2_check.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in ("required_elements", "hierarchy", "overlaps_not_allowed", "land_in_sea", "land_in_river", "portus_land_sea_split_mm2", "water_items_on_land_pct", "contact_distance_mm", "ring_range_median", "left_right", "hero_cluster", "core_group_city", "density_estimate", "labels", "warnings")}, ensure_ascii=False, indent=1))
    print("방위:", res["geo"]["rotation_plan_minus_real_deg"], "평균 오차", res["geo"]["bearing_error_abs_mean_deg"], "중앙값", res["geo"]["bearing_error_abs_median_deg"], "최대", res["geo"]["bearing_error_max"], res["geo"]["distance_law"])
    b8 = res["baseline_8"]
    print("사전 8절 검사 %s: 실패 %d건 %s · 본체 원천 %s" % ("통과" if b8["pass"] else "실패", len(b8["failed"]), "·".join(b8["failed"]), b8["hero_model_source"]))
    for i in items8:
        if not i["pass"]:
            print("    8절 %s %s — 값 %s %s" % (i["id"], i["name"][:60], json.dumps(i["value"], ensure_ascii=False)[:120], i["note"][:80]))
    hd = res["hierarchy_rule_d5"]
    print("사전 위계(예정 상자): 히어로 군 %s = %s mm² · 중앙값 %s · 히어로 비 %s · 건물 실루엣 %s mm²(다른 건물 최대 대비 %s배)" %
          ([round(float(v), 1) for v in hd["hero_group_box"]], format(hd["hero_group_area"], ","), format(hd["landmark_median"], ","), hd["hero_over_median"], format(hd["hero_building_sil_mm2"], ","), hd["building_sil_over_max_other"]))
    if not req["ok"]:
        print("사전 검사 실패: 필수 요소 없음 →", " · ".join(req["missing"] + ["예상 밖 패널 %s" % k for k in req["unexpected_panels"]]))
        return 1
    print("사전 검사 완료: 필수 요소 모두 있음 · 패널", res["panels_print"], "· 랜드마크", len(lm_areas), "· 허용 안 된 겹침", len(over), "· 경고", len(warnings))
    return 0


def pre_ctx8(D, hm, hl, hero_bld_box, pm):
    """사전 검사의 8절 측정값(사양 기하). eval_baseline8의 ctx"""
    c_ = hl.get("center_plan") or getattr(D, "HERO_C_PLAN", None)
    R_ = float(hl["reserve_R"]) if _isnum(hl.get("reserve_R")) else float(getattr(D, "HERO_LANDSCAPE_D5", {}).get("reserve_R_plan", 90.0))
    road = (lambda rid: D.road_by_id(rid)) if hasattr(D, "road_by_id") else (lambda rid: next((r for r in D.ROADS if r.get("id") == rid), None))

    def near(r):
        if not r or not c_:
            return None
        return min(math.hypot(p[0] - c_[0], p[1] - c_[1]) for p in D.road_plan(r))
    # R7 북쪽 끝–광장 틈
    r7, g7 = road("R7"), None
    if r7 and c_:
        end = min(D.road_plan(r7), key=lambda p: math.hypot(p[0] - c_[0], p[1] - c_[1]))
        g7 = abs(math.hypot(end[0] - c_[0], end[1] - c_[1]) - float(getattr(_B, "NOFILL_R_PLAN", 90.5)))   # 13:35: 길 끝 = 옛 광장 경계
    # 히어로 군 구성(12:49)
    names = D.hero_part_names() if hasattr(D, "hero_part_names") else [str(p.get("name", "")) for p in D.PROPS]
    crowds = hl.get("crowds")
    g1, g4 = near(road("R1")), near(road("R4"))
    comp = {"판석 광장·문 앞 포장 0(13:33)": not hl.get("boundary_screen"),
            "기초 공사장": isinstance(getattr(D, "WORKSITE", None), dict),
            "인물 무리": len(crowds) if isinstance(crowds, list) else 0,
            "노점 2": len(getattr(_B, "STALLS_SCREEN", [])) == 2,
            "네로 거상 받침": (D.find_nero() is not None) if hasattr(D, "find_nero") else False}
    lbr = sorted(set(n for n in names + list(hl.get("parts") or []) if any(k in n for k in LB_KEYS)))
    # 조경 예약 반지름 침범(다른 패키지의 랜드마크·배경·소품. 문 길·네로 마당·공사장은 히어로 영역)
    intr = []
    if c_:
        for x in list(D.LANDMARKS) + list(D.BACKGROUND):
            gr = D.landmark_ground(x) if hasattr(D, "landmark_ground") else None
            b = x.get("box")
            pts = [D.to_plan(*p) for pg in (gr or []) for p in pg] or ([D.to_plan((b[0] + b[2]) / 2.0, b[3])] if b else [])
            if pts:
                dmin = min(math.hypot(p[0] - c_[0], p[1] - c_[1]) for p in pts)
                if dmin < R_ - 0.05:
                    intr.append([x["id"], round(dmin, 1)])
        for p in D.PROPS:
            nm = str(p.get("name", ""))
            if "네로" in nm or "공사장" in nm:
                continue
            b = D.prop_box(p) if hasattr(D, "prop_box") else p.get("box")
            if not b:
                continue
            q = D.to_plan((b[0] + b[2]) / 2.0, b[3])
            dq = math.hypot(q[0] - c_[0], q[1] - c_[1])
            if dq < R_ - 0.05:
                intr.append(["소품 " + nm, round(dq, 1)])
    # Z1 지시선(→ 확대 창 Z1)과 지도 쪽 A 표지
    zl = None
    for ld in D.LEADERS:
        if re.search(r"→\s*(확대 창\s*)?Z1", str(ld.get("name", ""))):
            zl = [(float(p[0]), float(p[1])) for p in ld.get("pts", [])]
            break
    ma = next((m_["pt"] for m_ in (pm or []) if m_.get("glyph") == "A" and m_.get("source") == "map"), None)
    # R7·다리·영묘 높이(map 값, 없으면 결정 D7 값으로 채우고 출처를 적는다)
    MZ = getattr(D, "MAUSOLEUM", None) or {}
    br, base = MZ.get("bridge") or {}, MZ.get("base") or {}
    src = []
    st = MZ.get("steps") or MZ.get("stairs") or base.get("steps") or br.get("steps")
    if not isinstance(st, dict):
        st = R7L.get("steps") or {}
        src.append("디딤 = 결정 D7(map 미등록)")
    ramp = (r7 or {}).get("ramp") or (r7 or {}).get("z_profile")
    if isinstance(ramp, dict) and isinstance(ramp.get("z"), (list, tuple)):
        r7_top = max(ramp["z"])
    elif isinstance(ramp, dict) and _isnum(ramp.get("z_top")):
        r7_top = ramp["z_top"]
    else:
        r7_top = (R7L.get("ramp_z") or [0.0, 3.0])[1]
        src.append("R7 진입 경사 = 결정 D7(map 미등록)")
    deck = br.get("deck_z", br.get("h"))
    risers = st.get("risers") or []
    maus = {"r7_top_z": r7_top, "deck_z": deck, "step_bottom_z": st.get("bottom_z", deck), "risers": risers, "plinth_z": base.get("h"),
            "source": " · ".join(src) or "map"}
    return {"building_box": hero_bld_box, "building_w": (hero_bld_box[2] - hero_bld_box[0]) if hero_bld_box else None,
            "plaza_w": D.landscape_width(hl) if hasattr(D, "landscape_width") else None, "cut_footprints": [],
            "composition": comp, "lb_replica": lbr, "reserve_intrusions": intr, "z1_leader": zl, "mark_a": ma, "r7_gap": g7, "mausoleum": maus}


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
# d5 공용 상수(v2_base에 없으면 같은 값의 기본값)
HC8 = getattr(_B, "HERO_COLO_D5", {}) or {}
HL8 = getattr(_B, "HERO_LANDSCAPE_D5", {}) or {}
TOL8 = getattr(_B, "HERO_COLO_TOL", {"semi_axes": 0.05, "width_ratio": [0.53, 0.02], "wall_h": 0.5, "wood_frac": [0.55, 0.03], "box_mm": 1.5})
LB_KEYS = tuple(getattr(_B, "LB_REPLICA_KEYS", ("단칸 아치", "벽돌 담", "작은 신전", "열주 폐허", "6주 신전", "문 폐허", "포장 고리", "갈래길")))
CROWD_MIN_ = int(getattr(_B, "CROWD_MIN", 3))
CROWD_N_ = tuple(getattr(_B, "CROWD_N", (5, 7)))
CROWD_GAP_ = tuple(getattr(_B, "CROWD_GAP", (3.5, 5.0)))
PERSON_HERO = (getattr(_B, "PERSON_H", {}) or {}).get("hero", [4.9, 4.6, 5.2])
Z1_START_ = tuple(getattr(_B, "Z1_START", (232.0, 396.8)))
Z1_END_ = tuple(getattr(_B, "Z1_LEADER_END", (272.38, 420.11)))
Z1_A_ = tuple(getattr(_B, "Z1_A_MARK", (233.75, 393.77)))
R7L = getattr(_B, "R7_LINK_D5", {}) or {}
BASE_FORBID = re.compile(getattr(_B, "PRINT_FORBIDDEN_BASE", r"기초 절개|받침 앞 변|받침"))
BASE_OK = re.compile(getattr(_B, "PRINT_BASE_ALLOWED", r"네로|거상|\(벽돌 마감\)\s?받침"))
LINE_MM = getattr(_B, "PRINT_LINE_MM", {"내부선": [0.10, 0.20], "지시선": 0.30, "콜아웃 테두리": 0.25, "Z1 테두리": 0.60, "P5 계단선": 0.35})
LINE_MIN = float(getattr(_B, "PRINT_LINE_MIN", 0.10))
LINE_TOL = float(getattr(_B, "PRINT_LINE_TOL", 0.01))
P5S = getattr(_B, "P5_STAIR", {}) or {}
SPEC_FORBID_D5 = re.compile(getattr(_B, "SPEC_FORBIDDEN_D5", r"왼쪽 위 하나|\[제작 단계 과제\]|빛 번짐|shadow 레이어|그림자[^0]{0,8}허용"))
ANCHOR_TOL = float(getattr(_B, "ANCHOR_TOL_MM", 0.5))


def _seg_iter(t0, t1, step=1.0):
    """구간 [t0, t1) 안쪽 표본 방위(경계 0.5° 안쪽, 0°를 지나는 구간 포함)"""
    t0, t1 = float(t0), float(t1)
    span = (t1 - t0) % 360.0 if (t1 - t0) % 360.0 else 360.0
    k, out = 0.5, []
    while k < span - 0.49:
        out.append((t0 + k) % 360.0)
        k += step
    return out


def _it(items, iid, name, ok, value=None, expected=None, note=""):
    items.append({"id": iid, "name": name, "pass": bool(ok), "value": value, "expected": expected, "note": note})


def eval_baseline8(hm, hl, ctx):
    """기준선 8.1(콜로세움 본체)·8.2(받침 없음 + 12:49 히어로 군 구성)·D5(Z1 출발점)·D7(R7·영묘 높이) 판정. 사전·사후·자체 시험 공용.
    hm = 본체 정규형(v2_data.hero_model 꼴: semi_axes·major_az·center_plan·profile·second_ring·wood_frac·base_side·front_cut),
    hl = 둘레 정규형(base_side·octagon·front_cut), ctx = 측정값(building_box·building_w·plaza_w·cut_footprints·composition·lb_replica·
    reserve_intrusions·z1_leader·mark_a·r7_gap·mausoleum). 값이 없으면 그 항목은 '자료 없음'으로 실패한다"""
    hm, hl, items = hm or {}, hl or {}, []
    ta = float(TOL8.get("semi_axes", 0.05))
    # 8.1-1 반축
    ax, exp = hm.get("semi_axes"), HC8.get("semi_axes_plan", [44.0, 36.6])
    ok = bool(ax) and abs(ax[0] - exp[0]) <= ta + 1e-9 and abs(ax[1] - exp[1]) <= ta + 1e-9
    _it(items, "8.1-1", "외곽 타원 반축 %g×%g(평면, ±%g)" % (exp[0], exp[1], ta), ok, [round(v, 3) for v in ax] if ax else None, exp, "" if ax else "자료 없음")
    # 8.1-2 장축 방위(화면 가로 = 평면 315°, 직선이라 135°와 같다)
    maz = hm.get("major_az")
    dd = None if maz is None else min(abs((maz - 315.0) % 180.0), 180.0 - abs((maz - 315.0) % 180.0))
    _it(items, "8.1-2", "장축 평면 방위 315°(화면 가로, ±0.5°)", dd is not None and dd <= 0.5, maz, 315.0, "" if maz is not None else "자료 없음")
    # 8.1-3 외곽 중심(조경 중심에서 뒤-왼쪽으로 물림)
    c, ce = hm.get("center_plan"), HC8.get("center_plan", [446.54, 161.86])
    dc = math.hypot(c[0] - ce[0], c[1] - ce[1]) if c else None
    _it(items, "8.1-3", "외곽 타원 중심 평면 (%g, %g)(±0.5)" % tuple(ce), dc is not None and dc <= 0.5, [round(v, 2) for v in c] if c else None, ce,
        "" if c else "자료 없음")
    # 8.1-4 폭 비
    r0, rt = TOL8.get("width_ratio", [0.53, 0.02])
    bw, pw = ctx.get("building_w"), float(getattr(_B, "LANDSCAPE_REP_W", 203.5))      # 13:33 광장 0: 비례 기준 폭(옛 조경 대표 원 R 83.1)
    ratio = (bw / pw) if (_isnum(bw) and _isnum(pw) and pw > 0) else None
    _it(items, "8.1-4", "콜로세움 폭 ÷ 조경 영역 대표 폭 203.5 = %g±%g" % (r0, rt), ratio is not None and abs(ratio - r0) <= rt + 1e-9,
        round(ratio, 3) if ratio else None, r0, "" if ratio else "자료 없음(본체 폭 %s · 광장 폭 %s)" % (bw, pw))
    # 8.1-5 θ 구간 외벽 높이(D2 표 ±0.5)
    prof, th = hm.get("profile") or [], float(TOL8.get("wall_h", 0.5))
    bad, miss = [], []
    for t0, t1, lo, hi, note in (_B.parse_profile(HC8.get("wall_profile")) if _B else []):
        hs = []
        for t in _seg_iter(t0, t1):
            h = _B.wall_h(prof, t) if prof else None
            if h is None:
                miss.append(round(t, 1))
            else:
                hs += [h[0], h[1]]
        if hs and (min(hs) < lo - th - 1e-9 or max(hs) > hi + th + 1e-9):
            bad.append("%g~%g°: 그린 %.1f~%.1f ≠ %g~%g(%s)" % (t0, t1, min(hs), max(hs), lo, hi, note))
    _it(items, "8.1-5", "θ 구간 외벽 높이 = D2 표 ±%g(4층 53·3층 37·2층 24.5, 경사 부벽·수직 절단 포함)" % th, bool(prof) and not bad and not miss,
        bad[:6] or None, "D2 표", ("자료 없음(외벽 표)" if not prof else ("표 빈 방위 %d곳(예 %s)" % (len(miss), miss[:4]) if miss else "")))
    # 8.1-6 정면 18~72° ≤ 17.0
    fa, fmax = HC8.get("front_az", [18, 72]), float(HC8.get("front_h_max", 17.0))
    fh = [(_B.wall_h(prof, t) or (None, None))[1] for t in _seg_iter(fa[0], fa[1])] if prof else []
    fh = [v for v in fh if v is not None]
    _it(items, "8.1-6", "경기장 앞 정면(θ %g~%g°) 높이 ≤ %g(경기장이 보이게)" % (fa[0], fa[1], fmax), bool(fh) and max(fh) <= fmax + 1e-9,
        max(fh) if fh else None, fmax, "" if fh else "자료 없음")
    # 8.1-7 둘째 고리 37, 정면 10~80° ≤ 12
    r2, r2e = hm.get("second_ring"), HC8.get("second_ring", {"h": 37.0, "front_az": [10, 80], "front_h_max": 12.0})
    ok = isinstance(r2, dict) and _isnum(r2.get("h")) and abs(float(r2["h"]) - r2e["h"]) <= th + 1e-9 and _isnum(r2.get("front_h_max")) \
        and float(r2["front_h_max"]) <= r2e["front_h_max"] + 1e-9
    fz = r2.get("front_az") if isinstance(r2, dict) else None
    if ok and isinstance(fz, (list, tuple)) and len(fz) == 2:
        ok = abs(float(fz[0]) - r2e["front_az"][0]) <= 1.0 and abs(float(fz[1]) - r2e["front_az"][1]) <= 1.0
    _it(items, "8.1-7", "둘째 고리 높이 %g(±%g)·정면 %g~%g° ≤ %g" % (r2e["h"], th, r2e["front_az"][0], r2e["front_az"][1], r2e["front_h_max"]), ok,
        {k: r2.get(k) for k in ("h", "front_az", "front_h_max")} if isinstance(r2, dict) else None, r2e, "" if isinstance(r2, dict) else "자료 없음(둘째 고리)")
    # 8.1-8 나무 바닥 55±3%
    w0, wt = TOL8.get("wood_frac", [0.55, 0.03])
    wf = hm.get("wood_frac")
    _it(items, "8.1-8", "경기장 복원 나무 바닥 %d±%d%%(나머지 하이포게움)" % (round(w0 * 100), round(wt * 100)), _isnum(wf) and abs(wf - w0) <= wt + 1e-9,
        round(wf, 3) if _isnum(wf) else None, w0, "" if _isnum(wf) else "자료 없음")
    # 8.1-9 건물 화면 상자
    bb, be, tb = ctx.get("building_box"), HC8.get("building_screen_box", [192.6, 226.4, 300.4, 330.1]), float(TOL8.get("box_mm", 1.5))
    db = max(abs(float(a) - float(b)) for a, b in zip(bb, be)) if _is_box(bb) else None
    _it(items, "8.1-9", "건물 화면 상자 [%s](±%g mm)" % (", ".join("%g" % v for v in be), tb), db is not None and db <= tb + 1e-9,
        [round(float(v), 1) for v in bb] if _is_box(bb) else None, be, "" if db is not None else "자료 없음")
    # 8.2-1 받침 옆면 0
    sides = [v for v in (hm.get("base_side"), hl.get("base_side")) if v is not None]
    _it(items, "8.2-1", "팔각 받침 옆면 0mm(땅 위에 바로 놓임)", bool(sides) and all(abs(float(v)) <= 1e-9 for v in sides), sides or None, 0.0,
        "" if sides else "자료 없음")
    # 8.2-2 받침·앞 변 절개 0
    cuts = list(ctx.get("cut_footprints") or [])
    flags = [k for k, v in (("팔각 받침", hl.get("octagon")), ("앞 변 기초 절개", hl.get("front_cut") or hm.get("front_cut"))) if v]
    _it(items, "8.2-2", "받침·앞 변 기초 절개 0(형태·footprint)", not cuts and not flags, (flags + cuts) or None, [], "")
    # 8.2-3 히어로 군 구성(12:49 철회 뒤 승인 설계)
    comp = ctx.get("composition")
    if isinstance(comp, dict):
        need = []
        for k, v in comp.items():
            if k == "인물 무리":
                if not (_isnum(v) and v >= CROWD_MIN_):
                    need.append("%s %s곳 < %d" % (k, v, CROWD_MIN_))
            elif not v:
                need.append(k)
        _it(items, "8.2-3", "히어로 군 구성(13:33): 판석 광장·문 앞 포장 0·기초 공사장·인물 무리 ≥ %d·노점 2·네로 거상 받침" % CROWD_MIN_,
            not need, comp, "모두", "없음: " + " · ".join(need) if need else "")
    else:
        _it(items, "8.2-3", "히어로 군 구성(12:49)", False, None, "모두", "자료 없음")
    # 8.2-4 LocalBanana 조경 배치 복제 0
    lbr = ctx.get("lb_replica")
    _it(items, "8.2-4", "LocalBanana 조경 배치 복제 부품 0(12:49 철회: 단칸 아치·벽돌 담·작은 신전·열주·6주 신전·문 폐허·포장 고리·갈래길)",
        lbr is not None and not lbr, lbr, [], "" if lbr is not None else "자료 없음")
    # 8.2-5 조경 예약 반지름 침범 0(사전만)
    if ctx.get("reserve_intrusions") is not None:
        ri = ctx["reserve_intrusions"]
        _it(items, "8.2-5", "조경 예약 반지름(평면 %g) 안 다른 오브젝트 0(문 길·히어로 부품 제외)" % float(HL8.get("reserve_R_plan", 90.0)), not ri, ri or None, [], "")
    # D5-1 Z1 지시선: 공사장 거푸집 오른쪽 면에서 ↘30° 한 직선
    zl = ctx.get("z1_leader")
    if zl and len(zl) >= 2:
        d0 = math.hypot(zl[0][0] - Z1_START_[0], zl[0][1] - Z1_START_[1])
        d1 = math.hypot(zl[-1][0] - Z1_END_[0], zl[-1][1] - Z1_END_[1])
        dirs = seg_dirs(zl)
        ang = [round(a, 2) for a, _l in dirs]
        ok = d0 <= 0.5 + 1e-9 and d1 <= 0.5 + 1e-9 and len(dirs) == 1 and min(abs(ang[0] - 30.0), 180 - abs(ang[0] - 30.0)) <= 0.5
        _it(items, "D5-1", "Z1 지시선 = 공사장 거푸집 오른쪽 면 (%g, %g) → ↘30° 한 직선(꺾임 0) → Z1 원 (%g, %g)(각 ±0.5mm)" % (Z1_START_ + Z1_END_), ok,
            {"start": [round(v, 2) for v in zl[0]], "end": [round(v, 2) for v in zl[-1]], "dirs_deg": ang, "start_gap_mm": round(d0, 2)}, [list(Z1_START_), list(Z1_END_)], "")
    else:
        _it(items, "D5-1", "Z1 지시선 출발점 = 공사장 거푸집 오른쪽 면", False, None, [list(Z1_START_), list(Z1_END_)], "자료 없음(→ 확대 창 Z1 지시선)")
    ma = ctx.get("mark_a")
    da = math.hypot(ma[0] - Z1_A_[0], ma[1] - Z1_A_[1]) if ma else None
    _it(items, "D5-2", "지도 쪽 A 표지 중심 (%g, %g)(±0.5)" % Z1_A_, da is not None and da <= 0.5 + 1e-9, [round(v, 2) for v in ma] if ma else None, list(Z1_A_),
        "" if ma else "자료 없음")
    # D7-1 R7–광장 틈 0
    g7 = ctx.get("r7_gap")
    _it(items, "D7-1", "R7 북쪽 끝 = 옛 광장 경계(평면 R 90.5) ±0.5", _isnum(g7) and g7 <= 0.5 + 1e-9, round(g7, 3) if _isnum(g7) else None, 0.0, "" if _isnum(g7) else "자료 없음")
    # D7-2 영묘 양 끝 보행면 높이 차 0
    mz = ctx.get("mausoleum") or {}
    try:
        rs = [float(v) for v in mz.get("risers") or []]
        d_n = abs(float(mz["r7_top_z"]) - float(mz["deck_z"]))
        d_s = abs(float(mz["step_bottom_z"]) - float(mz["deck_z"]))
        d_t = abs(float(mz["deck_z"]) + sum(rs) - float(mz["plinth_z"]))
        ok = d_n <= 0.01 and d_s <= 0.01 and d_t <= 0.02 and rs and max(rs) - min(rs) <= 0.02
        _it(items, "D7-2", "R7 진입 경사 윗끝 = 다리 상판 = 디딤 아래(높이 차 0), 챌면 같게 → 기단 윗면", ok,
            {"북쪽 차": round(d_n, 3), "남쪽 차": round(d_s, 3), "챌면": rs, "챌면 합 차": round(d_t, 3)}, 0.0, str(mz.get("source", "")))
    except (KeyError, TypeError, ValueError):
        _it(items, "D7-2", "R7·폰스 아일리우스·영묘 디딤 높이 접속", False, None, 0.0, "자료 없음")
    return items


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


def _area_box(b):
    return (float(b[2]) - float(b[0])) * (float(b[3]) - float(b[1]))


def drawn_objects(dr):
    """drawn.objects → {id: {box, name, sil(sil_mm2), raw}}. 목록형 [{id, name, box}](계약)과 옛 사전형을 모두 받는다"""
    out = {}
    for o in as_list(G(dr, "objects", "오브젝트", default=[]) or []):
        ob = as_polys(G(o, "box", "bbox", "rect", "poly", default=None)) if isinstance(o, dict) else []
        bb = bbox_pts(ob) if ob else None
        if bb:
            out[str(G(o, "id", "name", default="?"))] = {"box": bb, "name": str(G(o, "name", default="")),
                                                         "sil": G(o, "sil_mm2", "silhouette_mm2", "alpha_mm2"), "raw": o}
    return out


DRAWN_SCHEMA = {
    "footprints": {"required": ["name", "kind", "poly"], "unique": None, "geom": "poly"},
    "roads": {"required": ["id", "name", "polys"], "unique": "id", "geom": "polys"},
    "objects": {"required": ["id", "name", "box"], "unique": "id", "geom": "box"},
}


def check_drawn_contract(dr, schema=None):
    """drawn.json 정식 형식(사양 drawn_contract.schema): footprints [{name, kind, poly}], roads [{id, name, polys}], objects [{id, name, box}](화면 mm).
    목록이 아니거나 필수 필드가 빠지거나 id가 겹치면 실패 목록을 돌려준다"""
    sch = schema or DRAWN_SCHEMA
    fails = []
    for key, rule_ in sch.items():
        v = dr.get(key) if isinstance(dr, dict) else None
        if not isinstance(v, list):
            fails.append("%s: 목록이 아니다(%s)" % (key, type(v).__name__))
            continue
        seen = {}
        for i, e in enumerate(v):
            if not isinstance(e, dict):
                fails.append("%s[%d]: 항목이 dict가 아니다" % (key, i))
                continue
            miss = [f for f in rule_["required"] if e.get(f) in (None, "", [])]
            if miss:
                fails.append("%s[%d] %s: 필수 필드 없음 %s" % (key, i, e.get("id") or e.get("name") or "?", "·".join(miss)))
            g_ = e.get(rule_["geom"])
            if g_ is not None:
                ok_g = (_is_box(g_) if rule_["geom"] == "box" else bool(as_polys(g_)) and (rule_["geom"] != "polys" or (isinstance(g_, list) and all(_is_pts(p) for p in g_))))
                if not ok_g:
                    fails.append("%s[%d] %s: %s 형식이 다르다(화면 mm %s)" % (key, i, e.get("id") or e.get("name") or "?", rule_["geom"],
                                                                         "[x0,y0,x1,y1]" if rule_["geom"] == "box" else ("[[x,y],…]" if rule_["geom"] == "poly" else "[[[x,y],…],…]")))
            u = rule_.get("unique")
            if u and e.get(u) is not None:
                if e[u] in seen:
                    fails.append("%s: id 중복 '%s'(%d·%d번째)" % (key, e[u], seen[e[u]], i))
                seen.setdefault(e[u], i)
    return fails


def walk_strings(o, path=()):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk_strings(v, path + (str(k),))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk_strings(v, path + (str(i),))
    elif isinstance(o, str):
        yield path, o


def main_post(drawn_path, out_path, spec_path=None, info_path=None):
    """사후 검사. info_path = 정보 층 정합 기록(없으면 drawn.json 옆 info/info_check.json, 그것도 없으면 ⑰은 건너뛴다)"""
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
        # d5(기준선 8.2·D5): 콜로세움 받침 서술 0('기초 절개'·'받침 앞 변'·'받침'). 네로 거상 받침 문장만 허용한다
        mb = BASE_FORBID.search(s)
        if mb and not BASE_OK.search(s + " " + lay):
            fails.append("받침 서술 '%s' in [%s] %s(기준선 8.2: 받침 없음 — 네로 거상 받침만 허용)" % (mb.group(0), lay, s[:60]))
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
              "시장": ["시장", "market", "traian"],
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
    rule("⑤", "길-지면 간격 ≤ 1.6mm(판테온·욕장·메텔라·시장·바실리카–R2). 콜로세움 쪽 길 끝은 옛 광장 경계 R 90.5(13:35, ⑳ D7-1·⑲ 문)", fails, info)

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
        dmin_ = float(getattr(_B, "DENSITY_MIN_PCT", 39.3))
        if pct_full < dmin_ - 1e-9:
            fails.append("밀도(전체 무대) %.2f%% < %.1f%%" % (pct_full, dmin_))
    if pct_open is not None:
        info["pct_open_stage"] = round(pct_open, 2)
    rule("⑦", "밀도 ≥ %.1f%%(렌더 실측, 전체 무대 173,460mm² 기준 판정 · 열린 무대 값 기록. 13:33 광장 제거·13:35 채우지 않음 반영)" % float(getattr(_B, "DENSITY_MIN_PCT", 39.3)), fails, info)

    # ⑧ 인물 군 ≥ 3곳(승인 설계, 12:49 철회로 LocalBanana 4곳 배치는 필수 아님), 군마다 5~7명, 이웃 발점 간격 3.5~5mm, 키 4.6~5.2(D8 히어로 축척)
    fails, info = [], {}
    crowds = as_list(G(dr, "crowds", "인물 군", default=[]))
    if len(crowds) < CROWD_MIN_:
        fails.append("인물 군 %d곳 < %d" % (len(crowds), CROWD_MIN_))
    h_lo, h_hi = float(PERSON_HERO[1]), float(PERSON_HERO[2])
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
        if not _isnum(n) or not (CROWD_N_[0] <= n <= CROWD_N_[1]):
            fails.append("군 %s 인원 %s(%d~%d명 아님)" % (nm, n, CROWD_N_[0], CROWD_N_[1]))
        hs = G(g, "heights", "heights_mm", "키")
        hs = [float(v) for v in hs if _isnum(v)] if isinstance(hs, list) else ([float(G(g, "height_mm", "h", "height"))] if _isnum(G(g, "height_mm", "h", "height")) else [])
        if not hs:
            fails.append("군 %s 키 자료 없음(height_mm 또는 heights)" % nm)
        elif min(hs) < h_lo - 1e-9 or max(hs) > h_hi + 1e-9:
            fails.append("군 %s 키 %.2f~%.2fmm(%.1f~%.1f 밖, D8 히어로 축척)" % (nm, min(hs), max(hs), h_lo, h_hi))
        info.setdefault("heights_mm", {})[nm] = [round(min(hs), 2), round(max(hs), 2)] if hs else None
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
            if lo < CROWD_GAP_[0] - 0.05 or hi > CROWD_GAP_[1] + 0.05:
                fails.append("군 %s 이웃 간격 %.2f~%.2fmm(%g~%g 밖)" % (nm, lo, hi, CROWD_GAP_[0], CROWD_GAP_[1]))
    rule("⑧", "인물 군 ≥ %d곳(승인 설계)·군마다 %d~%d명·이웃 발점 간격 %g~%gmm·키 %.1f~%.1fmm(D8)" % (CROWD_MIN_, CROWD_N_[0], CROWD_N_[1], CROWD_GAP_[0], CROWD_GAP_[1], h_lo, h_hi), fails, info)

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
    # d5(D4): 지도 위계는 실제 그린 외곽 상자끼리(drawn.objects). 히어로 = 콜로세움 건물('hero') ∪ 조경 광장('hero_plaza') 단일 오브젝트.
    #          표준 랜드마크 각각 ≥ 4,500mm²(그린 상자), 히어로 ÷ 중앙값 4.5~7.9, 히어로 ≥ 최대 × 1.1, 베수비오 ≤ 최소 ÷ 1.1,
    #          콜로세움 건물 실루엣(sil_mm2) ≥ 다른 건물 실루엣 각각 × 1.2. 예정 상자(사양)로 통과를 보고하지 않는다
    O = drawn_objects(dr)
    lm_floor = float(getattr(_B, "LANDMARK_MIN_AREA", 4500.0))
    hm_lo, hm_hi = getattr(_B, "HERO_OVER_MEDIAN_RANGE", (4.5, 7.9))
    sil_k = float(getattr(_B, "HERO_SIL_OVER_OTHER", 1.2))
    hb = (O.get("hero_building") or O.get("hero") or {}).get("box")
    pb = (O.get("hero_plaza") or O.get("hero_landscape") or O.get("plaza") or {}).get("box")
    gb = (O.get("hero_group") or {}).get("box") or ([min(hb[0], pb[0]), min(hb[1], pb[1]), max(hb[2], pb[2]), max(hb[3], pb[3])] if hb and pb else None)
    if not O:
        fails.append("자료 없음: drawn.objects(그린 외곽 상자)")
    if not hb:
        fails.append("자료 없음: drawn.objects 'hero'(콜로세움 건물 외곽 상자)")
    if not pb and not (O.get("hero_group") or {}).get("box"):
        fails.append("자료 없음: drawn.objects 'hero_plaza'(조경 광장 외곽 상자) — 히어로 군 = 건물 ∪ 광장을 잴 수 없다")
    lms = {k: v for k, v in O.items() if re.match(r"^L\d+$", k)}
    la = {k: _area_box(v["box"]) for k, v in lms.items()}
    if la:
        med = sorted(la.values())[len(la) // 2] if len(la) % 2 else sum(sorted(la.values())[len(la) // 2 - 1: len(la) // 2 + 1]) / 2.0
        info.update({"landmark_areas_drawn": {k: round(v) for k, v in sorted(la.items())}, "landmark_median_drawn": round(med),
                     "L5_drawn_area": round(la["L5"], 1) if "L5" in la else None, "basis": "그린 외곽 상자끼리(drawn.objects). 예정 상자 아님"})
    if (gb or hb) and la:
        ga = _area_box(gb or hb)
        info.update({"hero_group_box": [round(v, 1) for v in (gb or hb)], "hero_group_area": round(ga), "hero_building_box": [round(v, 1) for v in hb] if hb else None,
                     "hero_plaza_box": [round(v, 1) for v in pb] if pb else None, "hero_group_from": "hero ∪ hero_plaza" if gb else "hero만(광장 상자 없음 — 판정 실패)",
                     "hero_over_median": round(ga / med, 2), "hero_over_landmark_max": round(ga / max(la.values()), 2)})
        if not (hm_lo <= ga / med <= hm_hi):
            fails.append("히어로 ÷ 표준 랜드마크 중앙값 %.2f(%.1f~%.1f 밖)" % (ga / med, hm_lo, hm_hi))
        if ga < 1.1 * max(la.values()):
            fails.append("히어로 군 %.0f < 랜드마크 최대 × 1.1" % ga)
    for k in REQUIRED_LM_:
        if k not in la:
            fails.append("그린 상자 없음: %s" % k)
        elif la[k] < lm_floor - 1e-6:
            fails.append("표준 랜드마크 %s 그린 상자 %.1f mm² < %s(%s)" % (k, la[k], format(int(lm_floor), ","), "×".join("%.1f" % (lms[k]["box"][i + 2] - lms[k]["box"][i]) for i in (0, 1))))
    ves = next((_area_box(v["box"]) for k, v in O.items() if k == "V" or "베수비오" in v.get("name", "")), None)
    if ves and la and ves > min(la.values()) / 1.1:
        fails.append("베수비오 %.0f > 랜드마크 최소 ÷ 1.1" % ves)
    hs_ = (O.get("hero_building") or O.get("hero") or {}).get("sil")
    others = {k: v.get("sil") for k, v in lms.items()}
    if not _isnum(hs_):
        fails.append("자료 없음: drawn.objects 'hero' sil_mm2(콜로세움 건물 실루엣 면적, 알파 ≥ 128)")
    miss = sorted(k for k, v in others.items() if not _isnum(v))
    if miss:
        fails.append("자료 없음: drawn.objects sil_mm2 %s" % "·".join(miss))
    if _isnum(hs_) and others and not miss:
        mx = max(others.items(), key=lambda kv: kv[1])
        info["building_sil_mm2"] = round(hs_)
        info["building_sil_over_max_other"] = [mx[0], round(hs_ / mx[1], 2)]
        for k, v in sorted(others.items()):
            if hs_ < sil_k * v - 1e-6:
                fails.append("콜로세움 건물 실루엣 %.0f < %s 실루엣 %.0f × %.1f" % (hs_, k, v, sil_k))
    rule("⑪", "위계(그린 상자): 6패널 Basic 최소 ≥ Detail 최대(Z1 합성)·Detail 최소 ≥ Support × 1.1·R·T 0 + 지도(그린 외곽 상자끼리): 히어로 군(건물 ∪ 공사장 ∪ 인물 무리 ∪ 노점 ∪ 네로 받침) ÷ 중앙값 %.1f~%.1f·"
         "≥ 최대 × 1.1·표준 랜드마크 각각 ≥ %s·베수비오 최소·콜로세움 건물 실루엣 ≥ 다른 건물 × %.1f" % (hm_lo, hm_hi, format(int(lm_floor), ","), sil_k), fails, info)

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

    # ⑯ 인쇄 선 굵기(D17): 내부선 0.10~0.20·지시선 0.30·콜아웃 테두리 0.25·Z1 테두리 0.60·P5 계단선 0.35. 더 가는 보조선은 print:false로 표시하고 인쇄에서 뺀다
    fails, info = [], {"strokes": 0, "print_false": 0}

    def want_lw(role):
        r_ = norm(role)
        for k, v in LINE_MM.items():
            if norm(k) in r_:
                return k, v
        if "leader" in r_ or "지시" in r_:
            return "지시선", LINE_MM.get("지시선", 0.30)
        if "callout" in r_ or "콜아웃" in r_:
            return "콜아웃 테두리", LINE_MM.get("콜아웃 테두리", 0.25)
        if "z1" in r_:
            return "Z1 테두리", LINE_MM.get("Z1 테두리", 0.60)
        if "inner" in r_ or "내부" in r_ or "외곽선" in r_ or "윤곽" in r_ or "outline" in r_:
            return "내부선", LINE_MM.get("내부선", [0.10, 0.20])
        return None, None

    def lw_ok(v, w):
        return (w[0] - LINE_TOL <= v <= w[1] + LINE_TOL) if isinstance(w, (list, tuple)) else abs(v - float(w)) <= LINE_TOL + 1e-9
    for ld in leaders:
        lw = G(ld, "lw", "line_w", "width", "굵기")
        if not _isnum(lw):
            fails.append("지시선 굵기 자료 없음: %s" % str(G(ld, "name", default="?"))[:30])
        elif not lw_ok(lw, LINE_MM.get("지시선", 0.30)):
            fails.append("지시선 굵기 %.2f ≠ %s: %s" % (lw, LINE_MM.get("지시선", 0.30), str(G(ld, "name", default="?"))[:30]))
    for b in boxes:
        if G(b, "border", "테두리") is not True:
            continue
        bid, kind = str(G(b, "id", "name", default="?")), str(G(b, "kind", default=""))
        lw = G(b, "lw", "border_lw", "stroke_w", "border_w")
        exp_k = "Z1 테두리" if bid.startswith("Z1") else "콜아웃 테두리"
        if not _isnum(lw):
            fails.append("테두리 굵기 자료 없음: %s(%s)" % (bid, kind))
        elif not lw_ok(lw, LINE_MM.get(exp_k)):
            fails.append("%s 굵기 %.2f ≠ %s: %s" % (exp_k, lw, LINE_MM.get(exp_k), bid))
    stk = as_list(G(dr, "strokes", "lines", "line_widths", "선 굵기", default=[]) or [])
    if not stk:
        fails.append("자료 없음: drawn.strokes(인쇄 선 굵기 기록 [{role, lw, print, count}])")
    for s_ in stk:
        role, lw, pr = str(G(s_, "role", "kind", "name", "id", default="")), G(s_, "lw", "w", "width"), G(s_, "print", "인쇄", default=True)
        if pr is False:
            info["print_false"] += 1
            continue
        info["strokes"] += 1
        if not _isnum(lw):
            fails.append("선 굵기 자료 없음: %s" % role)
            continue
        k_, w_ = want_lw(role)
        if w_ is not None and not lw_ok(float(lw), w_):
            fails.append("%s 굵기 %.2f ≠ %s(%s)" % (k_, lw, w_, role))
        elif float(lw) < LINE_MIN - 1e-9:
            fails.append("인쇄 선 %.2fmm < %.2f(보조선은 print:false): %s" % (lw, LINE_MIN, role))
    rule("⑯", "인쇄 선 굵기: 내부선 0.10~0.20·지시선 0.30·콜아웃 테두리 0.25·Z1 테두리 0.60·P5 계단선 0.35, 그보다 가는 선은 print:false", fails, info)

    # ⑰ 정보 층 정합(INFO_ONLY 실행 결과 out/info/info_check.json: 지시선 끝–앵커 ≤ 0.5mm, 허용쌍 밖 라벨 블록–실루엣 겹침 0). 실행하지 않았으면 건너뛴다(기록)
    fails, info = [], {}
    ip = info_path or os.path.join(os.path.dirname(os.path.abspath(drawn_path)), "info", "info_check.json")
    if not os.path.exists(ip):
        info = {"skipped": True, "reason": "INFO_ONLY 미실행(%s 없음). b{N} 렌더·export_sil 뒤 make.py --info로 판정한다" % ip}
    else:
        ic = json.load(open(ip, encoding="utf-8"))
        info = {"path": ip}
        snaps = as_list(G(ic, "leaders", "leader_snaps", "snaps", "anchors", default=[]) or [])
        if not snaps:
            fails.append("자료 없음: info_check.leaders(지시선 끝–앵커)")
        far = []
        for e in snaps:
            nm = str(G(e, "name", "id", "anchor", default="?"))
            d_ = G(e, "d_mm", "dist_mm", "after_mm", "gap_mm", "d")
            sn = G(e, "snapped", "matched", "ok", default=None)
            if sn is False:
                far.append(nm)
                fails.append("앵커 6mm 밖이라 맞추지 못함: %s(%s mm)" % (nm, d_))
            elif not _isnum(d_):
                fails.append("앵커 거리 자료 없음: %s" % nm)
            elif d_ > ANCHOR_TOL + 1e-9:
                fails.append("지시선 끝–앵커 %.2fmm > %.1f: %s" % (d_, ANCHOR_TOL, nm))
        info["snapped"] = len(snaps) - len(far)
        info["not_snapped"] = far
        ov = as_list(G(ic, "label_sil_overlaps", "overlaps", "label_overlaps", default=[]) or [])
        bad_ov = [e for e in ov if not G(e, "allowed", "허용", default=False) and _isnum(G(e, "area_mm2", "area", default=0)) and G(e, "area_mm2", "area", default=0) > 0.05]
        for e in bad_ov:
            fails.append("라벨 블록–실루엣 겹침 %.2fmm²: %s ↔ %s" % (G(e, "area_mm2", "area"), G(e, "label", "name", default="?"), G(e, "root", "id", "sil", default="?")))
        info["overlaps_checked"] = len(ov)
        if G(ic, "sil", "sil_json", "sil_path"):
            info["sil"] = G(ic, "sil", "sil_json", "sil_path")
    rule("⑰", "정보 층 정합(INFO_ONLY): 지시선 끝–앵커 ≤ %.1fmm(6mm 밖은 맞추지 못함 = 실패), 허용쌍 밖 라벨 블록–Blender 실루엣 겹침 0" % ANCHOR_TOL, fails, info)

    # ⑱·⑲·⑳ 기준선 8.1·8.2 + D5·D7(그린 결과): 본체 값은 render가 그린 값(drawn.forms.hero), 상자는 drawn.objects, 받침·절개는 footprints
    fh = G(G(dr, "forms", default={}) or {}, "hero", "colosseum", "hero_colosseum", default=None)
    hm_p = {}
    if isinstance(fh, dict):
        r2 = _B.first_of(fh, "second_ring", "ring2", "inner_ring")
        fl = _B.first_of(fh, "floor", "wood_floor") or {}
        hm_p = {"semi_axes": _B.pair_of(_B.first_of(fh, "semi_axes_plan", "semi_axes", "outer_semi_axes")),
                "major_az": _B.first_of(fh, "major_az_deg", "major_az"),
                "center_plan": _B.pair_of(_B.first_of(fh, "center_plan", "outer_center_plan")),
                "profile": _B.parse_profile(_B.first_of(fh, "wall_profile", "outer_walls", "walls", "wall_heights")),
                "second_ring": ({"h": _B.first_of(r2, "h", "height"), "front_az": _B.first_of(r2, "front_az", "front"),
                                 "front_h_max": _B.first_of(r2, "front_h_max", "front_max") if _B.first_of(r2, "front_h_max", "front_max") is not None
                                 else (max(r2["front_h"]) if isinstance(r2.get("front_h"), (list, tuple)) and r2["front_h"] else None)} if isinstance(r2, dict) else None),
                "wood_frac": _B.first_of(fh, "wood_frac") if _B.first_of(fh, "wood_frac") is not None else (_B.first_of(fl, "wood_frac") if isinstance(fl, dict) else None),
                "base_side": _B.first_of(fh, "base_side_mm", "base_side"), "front_cut": bool(fh.get("front_cut", False))}
    fpn = [str(G(f, "name", "id", default="")) for f in footprints]
    on = [v.get("name", "") for v in O.values()] + list(O.keys())
    cut_fp = sorted(set(n for n in fpn if "기초 절개" in n or ("받침" in n and not ("네로" in n or "거상" in n or n.startswith("공사장")))))
    hl_p = {"base_side": hm_p.get("base_side"), "octagon": any(("콜로세움 받침" in n) or ("팔각" in n) for n in fpn), "front_cut": any("기초 절개" in n for n in fpn)}
    plaza_polys = []
    for f in footprints:
        n_ = str(G(f, "name", default=""))
        if ("광장" in n_ and ("콜로세움" in n_ or "히어로" in n_ or "판석" in n_)) or n_ in ("콜로세움 받침",):
            plaza_polys += as_polys(f)
    if not plaza_polys and pb:
        plaza_polys = as_polys(pb)
    r7p = next((as_polys(r) for r in roads if norm(G(r, "id", default="")) == "r7"), [])
    sp_cm = (spec or {}).get("core_map") or {}
    # 문(R1·R4)은 조경 예약 반지름 가장자리에 있다(D3: R1 (483.1,90.5)·R4 (462.34,263.81)) → 예약 타원과 ≤ 0.5mm. R7만 광장 판석까지(D7-1)
    lsp = ((sp_cm.get("hero") or {}).get("landscape") or {})
    lc = lsp.get("center_plan") or HL8.get("center_plan", [462.34, 173.66])
    lR = float(getattr(_B, "NOFILL_R_PLAN", 90.5))                       # 13:35: 길 끝 = 옛 광장 경계(평면 R 90.5)
    C30_ = math.cos(math.radians(30))
    reserve_poly = [(C30_ * ((lc[0] + lR * math.cos(math.radians(t))) - (lc[1] + lR * math.sin(math.radians(t)))),
                     0.5 * ((lc[0] + lR * math.cos(math.radians(t))) + (lc[1] + lR * math.sin(math.radians(t))))) for t in range(0, 360, 2)]
    gate = {}
    for rid in ("R1", "R4", "R7"):
        rp = next((as_polys(r) for r in roads if str(G(r, "id", default="")) == rid), [])
        gate[rid] = round(multi_dist(rp, [reserve_poly]), 2) if rp else False
    terr = [str(t.get("name", "")) for t in (sp_cm.get("terrain") or []) + (sp_cm.get("planted") or [])]
    hero_d = G(dr, "hero", default={}) or {}
    comp = {"판석 광장·문 앞 포장 0(13:33)": (not plaza_polys) and not hero_d.get("plaza") and not hero_d.get("gate_paths"),
            "기초 공사장": ("worksite" in O) or any(n.startswith("공사장") for n in fpn), "인물 무리": len(crowds),
            "노점 2": len([n for n in fpn if n.startswith("노점")]) == 2,
            "네로 거상 받침": any("네로" in n for n in on + fpn),
            "길 끝 R1·R4·R7 = 옛 광장 경계 R 90.5(±0.6mm)": all(v is not False and v <= 0.6 + 1e-9 for v in gate.values())}
    lparts = ((sp_cm.get("hero") or {}).get("landscape") or {}).get("parts") or []
    lbr = sorted(set(n for n in on + fpn + [str(p if not isinstance(p, dict) else p.get("name", "")) for p in lparts] if any(k in n for k in LB_KEYS)))
    zl = None
    for ld in leaders:
        if re.search(r"→\s*(확대 창\s*)?Z1", str(G(ld, "name", default=""))):
            zl = lead_pts(ld)
            break
    ma = None
    for m_ in as_list(G(dr, "marks", default=[]) or []):
        if str(G(m_, "letter", "glyph", "text", default="")).upper() == "A" and nsrc(G(m_, *SRC_K)) == "map":
            ma = G(m_, "c", "center", "pt")
    if ma is None:
        ma = next((m_["c"] for m_ in marks if m_["glyph"] == "A" and m_["source"] == "map"), None)
    g7 = None
    l8 = next((x for x in sp_cm.get("landmarks", []) if x.get("id") == "L8"), {}) or {}
    l8p = l8.get("plan") if isinstance(l8.get("plan"), dict) else {}
    br_, base_ = (l8p.get("bridge") or l8.get("bridge") or {}), (l8p.get("base") or {})
    st_ = l8p.get("steps") or l8p.get("stairs") or base_.get("steps") or br_.get("steps")
    r7s = next((r for r in sp_cm.get("roads", []) if r.get("id") == "R7"), {}) or {}
    r7pp = r7s.get("plan_pts") or r7s.get("plan") or []
    if r7pp:
        e7 = min(r7pp, key=lambda p: math.hypot(p[0] - lc[0], p[1] - lc[1]))
        g7 = abs(math.hypot(e7[0] - lc[0], e7[1] - lc[1]) - float(getattr(_B, "NOFILL_R_PLAN", 90.5)))   # 13:35: R7 끝 = 옛 광장 경계
    bh = ((spec or {}).get("meta") or {}).get("blender_handoff") or {}
    src_ = []
    if not isinstance(st_, dict):
        st_ = ((bh.get("r7_link") or {}).get("steps")) or R7L.get("steps") or {}
        src_.append("디딤 = 결정 D7(map 미등록)")
    ramp_ = r7s.get("ramp") if isinstance(r7s.get("ramp"), dict) else None
    r7_top = (max(ramp_["z"]) if ramp_ and isinstance(ramp_.get("z"), (list, tuple)) else (ramp_ or {}).get("z_top"))
    if r7_top is None:
        r7_top = ((bh.get("r7_link") or {}).get("ramp_z") or R7L.get("ramp_z") or [0.0, 3.0])[1]
        src_.append("R7 진입 경사 = 결정 D7(map 미등록)")
    deck_ = br_.get("deck_z", br_.get("h"))
    maus = {"r7_top_z": r7_top, "deck_z": deck_, "step_bottom_z": st_.get("bottom_z", deck_), "risers": st_.get("risers") or [], "plinth_z": base_.get("h"),
            "source": " · ".join(src_) or "사양 L8·R7"}
    ctx_p = {"building_box": hb, "building_w": (hb[2] - hb[0]) if hb else None,
             "plaza_w": (pb[2] - pb[0]) if pb else ((lambda e: e[2] - e[0])(bbox_pts(plaza_polys)) if plaza_polys else None),
             "cut_footprints": cut_fp, "composition": comp, "lb_replica": lbr, "reserve_intrusions": None, "z1_leader": zl, "mark_a": ma, "r7_gap": g7, "mausoleum": maus}
    items_p = eval_baseline8(hm_p, hl_p, ctx_p)
    if not isinstance(fh, dict):
        for it in items_p:
            if it["id"] in ("8.1-1", "8.1-2", "8.1-3", "8.1-5", "8.1-6", "8.1-7", "8.1-8", "8.2-1"):
                it["note"] = (it["note"] + " · " if it["note"] else "") + "drawn.forms.hero(그린 본체 반축·방위·중심·외벽 표·둘째 고리·나무 바닥 비·받침 옆면) 없음"
    for no, pre_, nm in (("⑱", "8.1", "기준선 8.1 콜로세움 본체(그린 결과): 반축 44×36.6·장축 315°·중심·폭 비 0.53±0.02·θ 구간 외벽 높이 ±0.5·정면 ≤ 17·둘째 고리 37/정면 ≤ 12·나무 바닥 55±3%·건물 상자"),
                         ("⑲", "8.2", "기준선 8.2 받침 없음 + 12:49 히어로 군(그린 결과): 받침 옆면 0·받침·절개 footprint 0·광장·공사장·인물 무리·네로 받침·문·시내 지붕과 나무·LocalBanana 조경 복제 0"),
                         ("⑳", "D", "D5·D7 연결(그린 결과): Z1 지시선 = 공사장 거푸집 오른쪽 면에서 ↘30° 한 직선·A 표지 자리·R7–광장 틈 0·영묘 양 끝 높이 차 0")):
        sel = [i for i in items_p if i["id"].startswith(pre_)]
        rule(no, nm, ["%s %s — 값 %s%s" % (i["id"], i["name"][:48], json.dumps(i["value"], ensure_ascii=False)[:110], (" · " + i["note"]) if i["note"] else "") for i in sel if not i["pass"]],
             {"items": sel})

    # ㉑ P5 계단: 채움판 없는 꺾은선(D15 좌표 ±0.3·굵기 0.35)과 글 블록 ≥ 1.5mm
    fails, info = [], {}
    p5 = G(dr, "p5", default={}) or {}
    st = G(p5, "stair", "stair_line", "steps_line", "계단선", default=None)
    spts = lead_pts(st) if st is not None else None
    if not spts:
        fails.append("자료 없음: drawn.p5.stair.pts(계단 꺾은선)")
    else:
        want = [tuple(p) for p in (P5S.get("pts") or [])]
        if want and len(spts) == len(want):
            dev = max(math.hypot(a[0] - b[0], a[1] - b[1]) for a, b in zip(spts, want))
            info["pts_dev_mm"] = round(dev, 2)
            if dev > float(P5S.get("tol_mm", 0.3)) + 1e-9:
                fails.append("계단 꼭짓점 편차 %.2fmm > %.1f(D15 좌표)" % (dev, float(P5S.get("tol_mm", 0.3))))
        elif want:
            fails.append("계단 꼭짓점 %d개 ≠ %d개(D15)" % (len(spts), len(want)))
        if G(st, "fill", "filled", default=False):
            fails.append("계단에 채움판이 있다(채움 0)")
        if _isnum(G(p5, "fill_boxes", "bg_boxes")) and G(p5, "fill_boxes", "bg_boxes") > 0:
            fails.append("P5 배경판 %d개(상자·배경판 0)" % G(p5, "fill_boxes", "bg_boxes"))
        lw = G(st, "lw", "w")
        if not _isnum(lw):
            fails.append("계단선 굵기 자료 없음")
        elif abs(lw - float(P5S.get("lw", 0.35))) > LINE_TOL + 1e-9:
            fails.append("계단선 굵기 %.2f ≠ %.2f" % (lw, float(P5S.get("lw", 0.35))))
        clr = []
        for t in texts:
            pan = str(G(t, "panel", "box", default="")) + " " + str(G(t, "layer", "층", default=""))
            if "P5" not in pan:
                continue
            tp = as_polys(G(t, "bbox", "box", "poly"))
            if tp:
                clr.append((min(shape_dist(pg, spts, True, False) for pg in tp), text_of(t)[:20]))
        if not clr:
            fails.append("자료 없음: P5 글 외곽(bbox)")
        else:
            mn = min(clr)
            info["min_text_clear_mm"] = [round(mn[0], 2), mn[1]]
            if mn[0] < float(P5S.get("text_clear_mm", 1.5)) - 0.05:
                fails.append("계단선–글 %.2fmm < %.1f: %s" % (mn[0], float(P5S.get("text_clear_mm", 1.5)), mn[1]))
    rule("㉑", "P5 계단: 채움판 없는 꺾은선(D15 좌표 ±0.3mm·굵기 0.35)과 글 블록 간격 ≥ 1.5mm", fails, info)

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
        wh_d = spec.get("worker_handoff", {}) or {}
        wh = list(wh_d.keys())
        okw = sorted(wh) == sorted(["map", "panels", "render", "global"])
        # d5(Codex prod 지적): 열쇠 4개만이 아니라 각 인계에 기준선 8절 우선과 완료 조건이 있어야 한다
        wmiss = [k for k in ("map", "panels", "render", "global") if k in wh_d and not ("완료 조건" in str(wh_d[k]) and "8절" in str(wh_d[k]))]
        supp.append({"name": "worker_handoff 열쇠 = map·panels·render·global + 각 인계에 기준선 8절 우선·완료 조건", "pass": okw and not wmiss,
                     "fails": ([] if okw else ["worker_handoff = %s" % wh]) + ["%s: '8절'·'완료 조건' 없음" % k for k in wmiss]})
        # d5 사양 정리: 조명 방향 지정·그림자/빛 번짐 허용·'[제작 단계 과제]' 면제 0(사용자 원문 인용·금지 패턴 정의 제외)
        bad3, bad4 = [], []
        BASE_SPEC = re.compile(r"(콜로세움|히어로|팔각|지층)\s?받침|받침 (앞|뒤|옆|윗|광장|변|판)|받침대|앞 변 기초 절개|기초 절개")
        BASE_SPEC_OK = re.compile(r"없|0|폐기|철회|금지|지운|지웠|뺀|뺐|아니|대신|옛|d4|네로|거상|LocalBanana 참조|원문")
        for path, s in walk_strings(spec):
            if path[:2] in (("meta", "user_review"), ("meta", "user_selection"), ("meta", "user_decisions_d5")) or path[:1] == ("invalidated_from_previous",):
                continue
            if path[:2] == ("frame", "print_rules") and path[2:3] in (("forbidden_pattern",), ("forbidden_pattern_ci",), ("forbidden_sentences",), ("forbidden_base",)):
                continue
            if path[:2] == ("meta", "spec_forbidden_d5"):
                continue
            m3 = SPEC_FORBID_D5.search(s)
            if m3:
                bad3.append("%s '%s'" % ("/".join(path)[:70], m3.group(0)))
            m4 = BASE_SPEC.search(s)
            if m4 and not BASE_SPEC_OK.search(s):
                bad4.append("%s '%s'" % ("/".join(path)[:70], m4.group(0)))
        supp.append({"name": "사양에 '왼쪽 위 하나'·그림자/빛 번짐 허용·'[제작 단계 과제]' 0(기준선 0-1·8.3, 원문 인용 제외)", "pass": not bad3, "fails": bad3[:20]})
        supp.append({"name": "사양에 콜로세움 받침·앞 변 절개 서술 0(기준선 8.2. 네로 거상 받침·없음/폐기 서술·지난 판 기록 제외)", "pass": not bad4, "fails": bad4[:20]})
        wo = (spec.get("meta", {}) or {}).get("weight_order") or []
        ok_wo = bool(wo) and "8절" in str(wo[0]) and any("0-1" in str(w) for w in wo[:2])
        supp.append({"name": "meta.weight_order 맨 위 = 기준선 8절(05:27~12:49)·통합 루프 0-1(12:18)", "pass": ok_wo, "fails": [] if ok_wo else ["weight_order[0:2] = %s" % [str(w)[:40] for w in wo[:2]]]})
        bh = (spec.get("meta", {}) or {}).get("blender_handoff")
        bh_f = []
        if not isinstance(bh, dict):
            bh_f.append("meta.blender_handoff 없음")
        else:
            na = len(((bh.get("anchors") or {}).get("items")) or [])
            if na != 25:
                bh_f.append("앵커 %d개 ≠ 25" % na)
            for k in ("person_scale", "ref_rgb", "layers", "stage", "heights", "rebuild_order", "sil_json"):
                if not bh.get(k):
                    bh_f.append("blender_handoff.%s 없음" % k)
        cmh = ((spec.get("core_map") or {}).get("hero") or {})
        for k in ("colosseum", "landscape"):
            if not isinstance(cmh.get(k), dict):
                bh_f.append("core_map.hero.%s 없음" % k)
        supp.append({"name": "Blender 인계: meta.blender_handoff(사람 키·기준 RGB·표현 레이어·앵커 25·sil.json·무대·높이·순서) + core_map.hero.colosseum·landscape", "pass": not bh_f, "fails": bh_f})
    else:
        supp.append({"name": "spec.json", "pass": False, "fails": ["spec.json을 찾지 못함(drawn.json 옆 또는 넷째 인자)"]})
    # d5(Codex prod 지적): drawn.json 정식 형식(사양 drawn_contract.schema). 다르면 실패
    sch = (((spec or {}).get("drawn_contract") or {}).get("schema")) if spec else None
    cf = check_drawn_contract(dr, sch if isinstance(sch, dict) and sch else None)
    supp.append({"name": "drawn.json 계약 형식: footprints [{name, kind, poly}]·roads [{id, name, polys}]·objects [{id, name, box}](화면 mm, 필수 필드·id 중복 0)", "pass": not cf, "fails": cf[:20]})
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


def selftest():
    """회귀 시험(기준선 8.1·8.2): d4 사양(팔각 받침·고리 0.74·벽 60/28/12)을 넣으면 새 검사가 실패하고, d5 사양(결정 D2·12:49 히어로 군)을 넣으면 통과해야 한다.
    사전 판정(eval_baseline8, 사양 정규형)과 사후 판정(⑱·⑲·⑳, drawn 기록)을 같은 함수로 본다. 종료 코드 0 = 둘 다 기대대로"""
    H = HC8
    # d4 사양 그대로(map 옛 상수): 반지름 90·고리 0.74 원형, 벽 60/28/12, 받침 옆면 7, 앞 변 절개, Z1 수직 지시선, A 표지 절개 쪽
    d4_hm = {"semi_axes": (66.6, 66.6), "major_az": 315.0, "center_plan": (462.34, 173.66),
             "profile": [(150, 235, 60, 60, "4층"), (235, 330, 28, 28, "2층"), (330, 510, 12, 12, "무너진 앞쪽")], "second_ring": None,
             "wood_frac": 0.5, "base_side": 7.0, "front_cut": True}
    d4_hl = {"base_side": 7.0, "octagon": True, "front_cut": True}
    d4_ctx = {"building_box": [168.5, 211.0, 331.8, 365.2], "building_w": 163.1, "plaza_w": 203.7, "cut_footprints": ["콜로세움 받침", "콜로세움 기초 절개"],
              "composition": {"판석 광장·문 앞 포장 0(13:33)": True, "기초 공사장": True, "인물 무리": 4, "노점 2": True, "네로 거상 받침": True},
              "lb_replica": [], "reserve_intrusions": [], "z1_leader": [(275.0, 383.8), (275.0, 420.0)], "mark_a": (271.77, 382.46), "r7_gap": 6.06,
              "mausoleum": {"r7_top_z": 3.0, "deck_z": 3.0, "step_bottom_z": 3.0, "risers": [0.67, 0.67, 0.67], "plinth_z": 5.0}}
    # d5 사양(결정 D2·D3 수치, 12:49 철회 뒤 구성): 본체 표·둘째 고리·나무 바닥 u ≥ −2.0, 받침 0, Z1 새 출발점
    d5_hm = {"semi_axes": tuple(H["semi_axes_plan"]), "major_az": H["major_az_deg"], "center_plan": tuple(H["center_plan"]),
             "profile": _B.parse_profile(H["wall_profile"]), "second_ring": {"h": 37.0, "front_az": [10, 80], "front_h_max": 12.0},
             "wood_frac": 0.5632, "base_side": 0.0, "front_cut": False}
    d5_hl = {"base_side": 0.0, "octagon": False, "front_cut": False}
    bpolys = _B.colo_building_polys(H["center_plan"], H["semi_axes_plan"], H["major_az_deg"], d5_hm["profile"])
    bb = _B.polys_bbox(bpolys)
    d5_ctx = {"building_box": bb, "building_w": bb[2] - bb[0], "plaza_w": 2 * 83.1 * math.sqrt(1.5), "cut_footprints": [],
              "composition": dict(d4_ctx["composition"]), "lb_replica": [], "reserve_intrusions": [],
              "z1_leader": [Z1_START_, Z1_END_], "mark_a": Z1_A_, "r7_gap": 0.0, "mausoleum": dict(d4_ctx["mausoleum"])}
    must_fail = ["8.1-1", "8.1-4", "8.1-5", "8.1-7", "8.1-8", "8.2-1", "8.2-2", "D5-1", "D5-2", "D7-1"]
    r4 = {i["id"]: i for i in eval_baseline8(d4_hm, d4_hl, d4_ctx)}
    r5 = {i["id"]: i for i in eval_baseline8(d5_hm, d5_hl, d5_ctx)}
    ok4 = all(not r4[k]["pass"] for k in must_fail)
    ok5 = all(i["pass"] for i in r5.values())
    # 12:49 철회: LocalBanana 조경 복제 부품을 넣으면 8.2-4가 실패해야 한다
    c_lb = dict(d5_ctx, lb_replica=["6주 신전 앞면", "단칸 아치"])
    ok_lb = not next(i for i in eval_baseline8(d5_hm, d5_hl, c_lb) if i["id"] == "8.2-4")["pass"]
    # drawn 계약: 목록형·필수 필드·id 중복
    good = {"footprints": [{"name": "a", "kind": "지면", "poly": [[0, 0], [1, 0], [1, 1]]}], "roads": [{"id": "R1", "name": "r", "polys": [[[0, 0], [1, 0], [1, 1]]]}],
            "objects": [{"id": "hero", "name": "콜로세움", "box": [0, 0, 1, 1]}]}
    bad = {"footprints": {"a": [[0, 0], [1, 0], [1, 1]]}, "roads": [{"id": "R1", "polys": [[[0, 0], [1, 0], [1, 1]]]}, {"id": "R1", "name": "x", "polys": []}],
           "objects": [{"id": "hero", "name": "콜로세움", "box": [0, 0, 1, 1]}, {"id": "hero", "name": "중복", "box": [0, 0, 1, 1]}]}
    ok_c = not check_drawn_contract(good) and len(check_drawn_contract(bad)) >= 4
    out = {"d4_must_fail": {k: (not r4[k]["pass"]) for k in must_fail}, "d4_pass": ok4,
           "d5_all_pass": ok5, "d5_failed": [k for k, i in r5.items() if not i["pass"]], "lb_replica_detected": ok_lb, "contract_ok": ok_c,
           "d5_building_box": [round(v, 2) for v in bb], "d5_width_ratio": round((bb[2] - bb[0]) / (2 * 83.1 * math.sqrt(1.5)), 3)}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    good_all = ok4 and ok5 and ok_lb and ok_c
    print("자체 시험 %s: d4 사양 → 8.1·8.2 새 검사 실패 %s · d5 사양 → 모두 통과 %s · LocalBanana 복제 감지 %s · 계약 형식 %s" %
          ("통과" if good_all else "실패", ok4, ok5, ok_lb, ok_c))
    return 0 if good_all else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(selftest())
    if len(sys.argv) > 1 and sys.argv[1] == "--post":
        args = [a for a in sys.argv[2:]]
        info_p = None
        if "--info" in args:
            k = args.index("--info")
            info_p = args[k + 1] if k + 1 < len(args) else None
            args = args[:k] + args[k + 2:]
        if len(args) < 2:
            sys.exit("사용: python -I v2_check.py --post <drawn.json> <post_check.json> [spec.json] [--info info_check.json]")
        sys.exit(main_post(args[0], args[1], args[2] if len(args) > 2 else None, info_p))
    sys.exit(main_pre(sys.argv[1], sys.argv[2]))
