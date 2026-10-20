# -*- coding: utf-8 -*-
"""배치 사양 JSON 조립: 기하(v2_data) + 검사(v2_check.json) + 원칙·충돌(v2_text). 담당: global
새 필드(map·panels가 더한 열쇠)는 그대로 spec.json에 넘긴다.
d4: 사용자 검토(2026-10-19 02:24, 옛 R·T 패널 삭제·내부 표기 0) + 사용자 선택(2026-10-19 03:10, 기준선 7절: P2·P5, 랜드마크 3개, 네로 거상 받침).
    무대 확장 해제(STAGE 173,460mm²), 인쇄 패널 6개(L·P2·B·D·S·P5), 짝 표지(PAIR_MARKS·mark_pt), R7·L7~L9 다각형·지면을 사양에 싣는다.
d5: 기준선 8절(05:27~12:49)·통합 루프 0-1(12:18)을 우선순위 맨 위에 둔다. 그림체 = 벡터 일러스트(AO·조명·그림자 0, ISO_TONE 1.0/0.86/0.68, 그림자 확장 0mm).
    core_map.hero.colosseum(8.1 본체 정규형)·core_map.hero.landscape(8.2 받침 없음 + 12:49 히어로 군)·meta.blender_handoff(D8~D13 인계)를 조립하고,
    drawn_contract를 실제 drawn.json 형식(목록형 + schema)으로 맞춘다. 옛 열쇠(center_screen·oct_R_plan·base_side_T·ring_ratio·walls…)는 render 하위 호환으로 남긴다.
사용: python -I v2_build.py <data_dir> <out.json>"""
import json
import os
import sys

sys.path.insert(0, sys.argv[1])
import v2_data as D  # noqa: E402
import v2_text as TX  # noqa: E402

DATA_DIR = os.path.abspath(sys.argv[1])
OUT_JSON = os.path.abspath(sys.argv[2])
OUT_DIR = os.path.dirname(OUT_JSON)
chk = json.load(open(sys.argv[1] + "/v2_check.json"))
R1 = lambda v: [round(float(a), 1) for a in v]  # noqa: E731
R2 = lambda v: [round(float(a), 2) for a in v]  # noqa: E731
H = chk["hierarchy"]
T = TX.build(chk)
PANELS = D.PANELS_PRINT
USER_REVIEW_WORDS = "basic 정보에서 위치도는 빼. 또한 배치다이어그램 새위계도 빼. 이 내용은 작업할때 지시한 내부지시사항인데 표현하면 어쩌라는거니? 연대기도 빼."
# 사용자 선택(2026-10-19 03:10) = 기준선 7절 요지(설계-결정-기준.md 85~130행)
USER_SELECTION_WORDS = ("빈자리 채우기와 추가 랜드마크(1안 '형태 → 배움'): 오른쪽 위(옛 위치도 자리, 약 100×72mm) = P2 '아치·볼트·돔 아치·볼트·돔', "
                        "하단 띠 오른쪽(옛 연대기 자리) = P5 '지금 배우는 것 지금 배우는 중'. Core에 랜드마크 3개 추가(막센티우스 바실리카, 하드리아누스 영묘 + 테베레 다리(폰스 아일리우스), 마르켈루스 극장). "
                        "네로 청동 거상의 콘크리트 받침(콜로세움 곁 작은 소품)")
REQ = chk.get("required_elements", {})



def _river_width_plan():
    """강 중심선 꼭짓점별 화면 수직 폭(mm): 입구 W1 → 어귀 W2(호 길이 비례)"""
    import math as _m
    P_ = D.RIVER_PLAN
    seg = [_m.hypot(P_[k + 1][0] - P_[k][0], P_[k + 1][1] - P_[k][1]) for k in range(len(P_) - 1)]
    tot = sum(seg)
    acc = 0.0
    out = []
    for k in range(len(P_)):
        out.append(round(D.RIVER_W1 + (D.RIVER_W2 - D.RIVER_W1) * acc / tot, 2))
        if k < len(seg):
            acc += seg[k]
    return out

def road_id(rid):
    return next((r for r in D.ROADS if r.get("id") == rid), None)


Z1 = next((d for d in D.DETAILS if d.get("id") == "Z1"), None)
Z1_D = Z1["circle"]["d"] if Z1 and "circle" in Z1 else None
Z1_COMP = D.detail_box(Z1) if Z1 else None
NERO = D.find_nero() if hasattr(D, "find_nero") else None
BRIDGE = D.find_bridge() if hasattr(D, "find_bridge") else None
FARM = D.find_prop("포도밭 농장") if hasattr(D, "find_prop") else None
ALBANO = next((t for t in D.TERRAIN if str(t.get("name", "")).startswith("알바노")), None)
VES_BOX = D.BACKGROUND[0]["box"] if D.BACKGROUND else None
try:
    PAIR_POINTS = D.pair_marks() if hasattr(D, "pair_marks") else []
except Exception as _e:  # panels가 형식을 바꿔도 조립은 계속한다
    PAIR_POINTS = [{"error": str(_e)}]


def _bridge_spec():
    """L8의 다리 사양(dict)을 그대로 싣는다(평면 상판 범위·높이·아치 수). 없으면 None"""
    l8 = next((x for x in D.LANDMARKS if x.get("id") == "L8"), None)
    v = l8.get("bridge") if l8 else None
    if isinstance(v, dict):
        return v
    pl = l8.get("plan") if l8 else None                 # map이 평면 원본(plan) 안에 다리 사양을 두는 경우
    if isinstance(pl, dict) and isinstance(pl.get("bridge"), dict):
        return pl["bridge"]
    it = BRIDGE.get("item") if BRIDGE else None
    return it if isinstance(it, dict) else None


def fbox(b):
    return "(%s,%s)~(%s,%s)" % tuple(("%g" % round(float(v), 2)) for v in b) if b else "없음"


def plan_pts_screen(plan):
    return [R2(D.to_screen(*p)) for p in plan]


def area(b):
    return round((b[2] - b[0]) * (b[3] - b[1]))


def extra(x, known):
    """사양 원본(map·panels)이 더한 새 열쇠를 그대로 넘긴다"""
    return {k: v for k, v in x.items() if k not in known}


oct_ = D.hero_oct() if hasattr(D, "hero_oct") else []
hb = H["hero_box"]
HD5 = chk.get("hierarchy_rule_d5") or {}
B8 = chk.get("baseline_8") or {}
HM = D.hero_model() if hasattr(D, "hero_model") else {}
HLS = D.hero_landscape() if hasattr(D, "hero_landscape") else {}


def _jsonable(v):
    """튜플·numpy 수를 JSON 값으로"""
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    if hasattr(v, "item") and not isinstance(v, (str, bytes)):
        try:
            return v.item()
        except Exception:
            return str(v)
    return v


def colosseum_spec():
    """core_map.hero.colosseum: 8.1 본체 정규형(Blender roma_colo·roma_colo_in과 같은 값). map 새 dict가 있으면 그 값, 없으면 결정 D2 값(출처를 적는다)"""
    dec = dict(D.HERO_COLO_D5)
    if HM and not HM.get("legacy"):
        out = dict(dec)
        for k_out, k_in in (("center_plan", "center_plan"), ("semi_axes_plan", "semi_axes"), ("major_az_deg", "major_az"), ("arena_semi_axes_plan", "arena_semi_axes"),
                            ("arches", "arches"), ("tier_lines_z", "tier_lines_z"), ("base_side_mm", "base_side")):
            if HM.get(k_in) is not None:
                out[k_out] = _jsonable(HM[k_in])
        if HM.get("profile"):
            out["wall_profile"] = [[a, b, lo, hi, n] for a, b, lo, hi, n in HM["profile"]]
        if isinstance(HM.get("second_ring"), dict):
            out["second_ring"] = dict(dec["second_ring"], **{k: v for k, v in HM["second_ring"].items() if v not in (None, [])})
        if HM.get("wood_frac") is not None:
            out["floor"] = dict(dec["floor"], wood_frac=round(float(HM["wood_frac"]), 4))
        out["map_raw"] = _jsonable(HM.get("raw"))
        out["source"] = HM.get("source")
    else:
        out = dec
        out["source"] = "결정 D2(map 새 본체 dict 미등록 — 설계 그림은 아직 d4 옛 형식일 수 있다. 사전·사후 8.1 검사 참조)"
    out["draw_scale"] = getattr(D, "HERO_SCALE", 1.0)
    out["building_box_measured_pre"] = HD5.get("hero_building_box")
    out["building_sil_mm2_pre"] = HD5.get("hero_building_sil_mm2")
    out["theta_rule"] = "θ = atan2(평면 dY, 평면 dX)(roma_kit.plan_az): 0° 화면 오른쪽 아래, 45° 정면 아래, 135° 왼쪽, 225° 위, 315° 오른쪽"
    out["check"] = "사전 v2_check.json baseline_8 · 사후 post_check ⑱(render는 drawn.forms.hero에 그린 값을 적는다)"
    return out


def landscape_spec():
    """core_map.hero.landscape: 8.2 받침 없음 + 사용자 16:13·16:14 둘레(땅 바탕뿐: 광장·공사장·인물 무리·노점·둘레 나무·길 없음, 네로 거상 받침만 곁에)"""
    dec = dict(D.HERO_LANDSCAPE_D5)
    out = dict(dec)
    if HLS and not HLS.get("legacy"):
        if HLS.get("center_plan"):
            out["center_plan"] = _jsonable(HLS["center_plan"])
        for k in ("reserve_R", "rep_R"):
            if HLS.get(k) is not None:
                out[k + "_plan"] = HLS[k]
        if HLS.get("boundary_screen"):
            out["boundary_screen"] = [[[round(p[0], 2), round(p[1], 2)] for p in pg] for pg in HLS["boundary_screen"]]
        out["parts"] = HLS.get("parts") or []
        out["map_raw"] = _jsonable(HLS.get("raw"))
        out["source"] = HLS.get("source")
    else:
        out["parts"] = []
        out["source"] = "결정 D3·8.2(map 새 둘레 dict 미등록 — 설계 그림은 아직 d4 옛 형식일 수 있다. 사전·사후 8.2 검사 참조)"
    if HLS.get("crowds"):
        out["crowds"] = _jsonable(HLS["crowds"])
    out["withdrawn_1249"] = ("12:49 사용자 철회: LocalBanana 조경 배치(기둥 폐허·쓰러진 토막·단칸 아치·벽돌 담·작은 신전·열주·6주 신전 앞면·포장 고리·판석 갈래길·노점 배치)를 "
                             "옮겨 오지 않는다. 금지 부품 이름: " + "·".join(D.LB_REPLICA_KEYS))
    out["people_h_mm"] = None          # 사용자 16:35: 지도에 사람 없음(조각상·네로 청동 거상은 조형물이라 둔다)
    out["exclusion"] = "사용자 16:14: 조경 예약 반지름(평면 %g)은 비워 두는 땅의 기준일 뿐이다. 네로 마당 %s만 히어로 곁에 둔다" % (dec["reserve_R_plan"], dec["nero_yard_screen"])
    return out


def blender_handoff():
    """meta.blender_handoff: 와이어프레임(Blender) 워커 공용 인계(D8~D13, 사양이 단일 원천)"""
    anchors = []
    for pkg, nm, pt in D.BLENDER_ANCHORS:
        anchors.append({"pkg": pkg, "name": "ANCHOR_" + nm, "target_role": nm, "screen_mm": list(pt) if pt else None,
                        "provisional": "고정 점" if pt else "d4 spec labels[].target_pt · leaders 끝 · pair_marks map_pt"})
    return {
        "priority": "기준선-최종본 0-1(12:18) → 설계 기준선 8절(05:27~12:49) → 7·6·1~5절. 위치·크기의 원천 = 이 spec(current). 같은 회차에 decisions 수치가 있으면 그것을 따른다",
        "style": D.STYLE_RULE, "iso_tone": D.ISO_TONE, "shadow_expand_mm": D.SHADOW_EXPAND_MM, "outline_L7": "쓰지 않는다(b1 결정 OUTLINE=False)",
        "edge_highlight_L5": "화면 0.25~0.4mm 띠, 면색 명도 +10~15%",
        "ref_rgb": {k: (list(v) if isinstance(v, tuple) else v) for k, v in D.REF_RGB.items()},
        "palette_fix": "Blender PAL 'ground' #E3CFA8 → #ECD8AC(땅 윗면 = 설계 GROUND (236,216,172)), 종이 (231,208,160) = compose PAPER = 설계 BG",
        "person_scale": {"h_mm": D.PERSON_H, "w_ratio": D.PERSON_W_RATIO, "props_ratio": D.PROP_RATIO,
                         "rule": "원형은 키 1.0으로 정규화(bglobal), 패키지는 배율만 곱한다(city H_PERSON 1.7 → 2.4). 히어로 둘레(예약 반지름 안)·공사장·네로 마당 4.9, 경계 밖 15mm 길 3.4, 표준 지도 2.4, 가장 먼 곳 1.8"},
        "layers": {"name": "{PKG}_{Obj}_L{n}_{part}", "root": "{PKG}_{Obj}_root", "required": "모든 2.5D·3D 오브젝트에 L0~L6 메시가 층마다 1개 이상(빈 메시 금지)",
                   "audit": "bglobal roma_kit.layer_audit(coll) 결과를 보고에 붙인다", "passes": ["1회 L0~L2", "2회 L3~L4", "3회 L5~L6"],
                   "compare": "매회 자기 crop 8 px/mm 렌더 + LocalBanana(lb_*.png)·203X 같은 축척 비교 rounds/work/{pkg}_cmp.png",
                   "density": "8 px/mm에서 깊이색·무늬·디테일 없는 6×6mm 초과 빈 단색 면 0(라벨 비움 구역 평지 제외)"},
        "anchors": {"items": anchors, "count": len(anchors), "rule": "숨긴 Empty ANCHOR_{대상}_{역할}을 자기 컬렉션에 둔다. 점은 보이는 면 위 3D 점",
                    "from_spec": _jsonable(D.blender_anchor_items()) if hasattr(D, "blender_anchor_items") else []},
        "sil_json": ".work/blender/rounds/b{N}/sil.json(roma_render.export_sil: 루트별 {id, box, poly ≤ 96점(3 px/mm 알파 윤곽), area} + 앵커별 화면 좌표)",
        "snap": {"snap_within_mm": D.ANCHOR_SNAP_MM, "post_tol_mm": D.ANCHOR_TOL_MM, "result": "out/info/info_check.json(render INFO_ONLY)",
                 "rule": "정보 층은 sil.json으로 지시선 끝·짝 표지를 앵커에 맞춘다(6mm 안이면 맞추고, 밖이면 맞추지 않고 기록 → 사후 ⑰ 실패)"},
        "stage": D.BLENDER_STAGE, "heights": D.HEIGHTS_Z, "rebuild_order": D.REBUILD_ORDER,
        "r7_link": D.R7_LINK_D5,
        "zones": {"hero": "조경 예약 반지름 90 안 + 네로 마당 [172,196,198,228] + 공사장 [206,384,252,412]",
                  "ground": "그 밖의 땅·물·길(R7 진입 경사 포함)·집·나무·밭. 랜드마크 투영 상자 +2mm·라벨 글 블록(block_poly)·바닥 글 +1.5mm·조경 R 90.5·네로 마당·공사장에는 집·나무·소품 0",
                  "coast": "항구·영묘·다리 상판·디딤·하역장·석회 가마·오스티아·배", "suburb": "메텔라·아피아 소품·빌라·농장·베수비오·알바노 띠(COLLI ALBANI 바닥 글 블록 +1.5mm에 1mm 넘는 오브젝트 0)"},
        "wire_density": D.WIRE_DENSITY,
        "l5_draw_scale": D.L5_DRAW_SCALE,
        "forbidden": "헤드리스 Blender·Comfy 재구성 0, 장면 설정(카메라·엔진·색 관리·월드) 변경 0, 저장은 통합 담당만",
    }
LM_KNOWN = {"id", "name", "latin", "box", "zone", "geo", "real", "form", "story", "number", "links"}
landmarks = []
for x in D.LANDMARKS:
    ob = chk["objects_boxes"][x["name"]]
    b = ob["box"]
    e = {"id": x["id"], "name": x["name"], "latin": x.get("latin"), "tier": "Core(표준 랜드마크)", "zone": x.get("zone"),
         "projected_box": b, "projected_wh": ob["wh"], "projected_area_mm2": ob["area"],
         "center": [round((b[0] + b[2]) / 2, 1), round((b[1] + b[3]) / 2, 1)],
         "form": x.get("form"), "label_story": x.get("story"), "label_number": x.get("number"), "links": x.get("links"),
         "real_position": x.get("real"), "geo_approx": list(x["geo"]) if x.get("geo") else None,
         "ring_distance_mm": chk["ring_distance_mm"].get(x["name"]), "contact_distance_mm": chk["contact_distance_mm"].get(x["name"])}
    e.update(extra(x, LM_KNOWN))
    landmarks.append(e)
background = []
for x in D.BACKGROUND:
    b = x["box"]
    e = {"id": x["id"], "name": x["name"], "latin": x.get("latin"), "tier": "Core(지도 배경, 가장 작은 랜드마크급 지도 요소)", "zone": x.get("zone"),
         "projected_box": b, "projected_wh": [b[2] - b[0], b[3] - b[1]], "projected_area_mm2": area(b),
         "form": x.get("form"), "label_story": x.get("story"), "label_number": x.get("number"), "links": x.get("links"), "real_position": x.get("real"),
         "geo_approx": list(x["geo"]) if x.get("geo") else None,
         "ring_distance_mm": chk.get("ring_distance_background_mm", {}).get(x["name"], chk["ring_distance_mm"].get(x["name"])),
         "ring_rule": "베수비오·배경은 고리 거리와 좌우 개수에서 뺀다"}
    e.update(extra(x, LM_KNOWN))
    background.append(e)

panels = []
for p in PANELS:
    b = p["rect"]
    panels.append(dict(p, size=[b[2] - b[0], b[3] - b[1]], box_area=area(b)))

roads = []
RD_KNOWN = {"id", "name", "w", "w_screen_perp_mm", "center_line", "plan", "plan_pts", "note"}
for r in D.ROADS:
    pl = D.road_plan(r)
    e = {"id": r["id"], "name": r.get("name", ""), "w_screen_perp_mm": D.road_w(r), "center_line": r.get("center_line", False),
         "screen_pts": plan_pts_screen(pl), "plan_pts": [R2(p) for p in pl], "note": r.get("note", "")}
    e.update(extra(r, RD_KNOWN))
    roads.append(e)

details = []
for d in D.DETAILS:
    e = dict(d)
    if "circle" in d:
        e["circle_box"] = R2(D.detail_circle_box(d))
    e["projected_box"] = R2(D.detail_box(d))
    e["projected_box_source"] = D.detail_box_source(d)
    e["projected_area_mm2"] = area(e["projected_box"])
    e["tier"] = "Detail"
    details.append(e)

size_table = [{"tier": "Core", "name": "지도 무대 전체(로마 건축물 지도, STAGE 하나·확장 0)", "box": list(D.STAGE), "ext_rects": D.STAGE_EXT, "area_mm2": D.STAGE_AREA_EXT}]
size_table.append({"tier": "Core(히어로)", "name": "콜로세움 히어로 군(건물 ∪ 공사장 ∪ 인물 무리 ∪ 노점 ∪ 네로 받침, 13:33)", "box": hb, "area_mm2": H["hero_area"],
                   "building_box": HD5.get("hero_building_box"), "building_sil_mm2": HD5.get("hero_building_sil_mm2"), "basis": "사전 투영(예정) 상자 — 최종은 사후 ⑪"})
for x in landmarks:
    size_table.append({"tier": "Core(표준 랜드마크)", "name": x["name"], "box": x["projected_box"], "area_mm2": x["projected_area_mm2"]})
for p in panels:
    size_table.append({"tier": p["tier"], "name": f'{p["id"]} {p["name"]}', "box": p["rect"], "area_mm2": p["box_area"]})
for d in details:
    size_table.append({"tier": "Detail", "name": d["name"], "box": d["projected_box"], "area_mm2": d["projected_area_mm2"], "box_source": d["projected_box_source"]})
for x in background:
    size_table.append({"tier": "Core(지도 배경)", "name": x["name"], "box": x["projected_box"], "area_mm2": x["projected_area_mm2"]})

ta = H["tier_areas"]


def tier_line(t):
    return " · ".join("%s %s" % (k.split(" ")[0], format(v, ",")) for k, v in sorted(ta.get(t, {}).items(), key=lambda kv: -kv[1]))


size_order = ("Core(무대 %smm² = STAGE 하나(확장 0), 콜로세움 %smm² = 최대 단일 오브젝트, 표준 랜드마크 %d개 중앙값 %smm²의 %.2f배). 사용자 15:41·16:14: 장 6개가 같은 위계(Basic)이고, "
              "확대 원(Detail)과 100 VS 2,000(Support)은 ❺·❻ 패널 안 요소다. 베수비오·배경은 지도에서 지웠다." %
              (format(int(D.STAGE_AREA_EXT), ","), format(H["hero_area"], ","), len(H["landmark_areas"]), format(H["landmark_median"], ","), H["hero_over_landmark_median"]))

# 자산 고유 폭(300ppi): 배치 폭 ÷ 25.4 × 300
asset_widths = {"콜로세움(히어로)": [H["hero_wh"][0], D.asset_px(H["hero_wh"][0])]}
for x in landmarks:
    w = x["projected_wh"][0]
    asset_widths[x["name"]] = [w, D.asset_px(w)]
for x in background:
    w = x["projected_wh"][0]
    asset_widths[x["name"]] = [w, D.asset_px(w)]

try:
    portus_polys = {k: [[R1(p) for p in pg] for pg in v] for k, v in D.portus_polys().items()}
except Exception as e_:  # map이 형태 함수를 바꾸면 다각형 없이 넘긴다
    portus_polys = {"오류": str(e_)}

river_poly = [R1(p) for p in D.river_polygon()]
_pcr = H.get("panel_count_rule") or {}
_pc_txt = ("인쇄 패널 %d개(%s) — 패널 수 %s 규칙 판정 %s" % (_pcr.get("count", len(panels)), "·".join(_pcr.get("ids", [p["id"] for p in panels])), "5~7개",
                                                     "통과" if _pcr.get("pass") else "실패")) if isinstance(_pcr, dict) else str(_pcr)
_lm_names = "·".join(x["name"].split("(")[0].strip() for x in D.LANDMARKS)
_basic_ids = [p["id"] for p in panels if p.get("tier") == "Basic"]
R1_ROAD, R4_ROAD, R7_ROAD = road_id("R1"), road_id("R4"), road_id("R7")
_nero_box = NERO.get("box") if NERO else None
spec = {
    "meta": {
        "title": "로마 콘크리트 A2 세로 포스터 — 203X 도시 인포그래픽 '로마 편' 배치 사양(기준선 8절 + 통합 루프 0-1 + 사용자 선택 03:10 + 사용자 검토 02:24)",
        "version": "d5 (2026-10-19, 기준선 8절(05:27~12:49)·와이어프레임 통합 루프(12:18) 반영, 설계 d5 = 와이어프레임 b5의 원천)",
        "baseline_8": {
            "source": "설계-결정-기준.md 8절(1~7절보다 우선) + 기준선-최종본.md 0-1절(12:18, 이 사양의 다른 절보다 우선)",
            "applied": [
                "8.1 콜로세움 본체: 외곽 타원 반축 44×36.6(평면, 장축 315° = 화면 가로), 중심 (446.54,161.86)(조경 중심에서 뒤-왼쪽으로 물림), 아치 40칸, θ 구간 외벽 높이(4층 53·3층 37·2층 24.5, 경사 부벽·수직 절단), 정면 18~72° ≤ 17, 둘째 고리 37(정면 10~80° ≤ 12), 나무 바닥 55%·하이포게움. core_map.hero.colosseum",
                "8.1 비례: 콜로세움 폭 ≈ 기준 폭 203.5의 0.53(기준 폭일 뿐, 땅에 그리는 것은 없다). 이 비례가 d4의 ring_ratio 0.74·벽 60/28/12보다 우선한다(폐기)",
                "12:49 사용자 철회: 콜로세움 둘레에 LocalBanana 조경 배치를 옮겨 오지 않는다. 사용자 16:13·16:14: 광장·판석·경계석·문 앞 포장·둘레 나무·인물 무리·노점·공사장·길은 없고 둘레는 땅 바탕뿐이다. 히어로 = 콜로세움 건물(기단 계단 2단 포함) 하나. core_map.hero.landscape",
                "8.2 팔각형 받침대 없음: 받침 옆면 0mm, 팔각 외곽·지층·앞 변 기초 절개 0. 확대 창 Z1 출발점은 공사장 거푸집 오른쪽 면(다져 넣은 층) (232.0, 396.8)",
                "8.3·0-1 그림체: 벡터 일러스트(203X). " + D.STYLE_RULE + ". 제작 단계 면제 표시는 쓰지 않는다(와이어프레임이 루프 안에 있다)",
                "8.4: Comfy 재구성 모델 0. 7절(P2·P5·L7~L9·네로 받침)은 d4 이행을 유지한다",
            ],
            "checks": "사전 v2_check.json baseline_8(기록) · 사후 post_check ⑱(8.1)·⑲(8.2·12:49)·⑳(D5·D7) — 사후 실패 시 make.py 종료 코드 1",
            "pre_result": {"pass": B8.get("pass"), "failed": B8.get("failed"), "hero_model_source": B8.get("hero_model_source"), "landscape_source": B8.get("landscape_source")},
        },
        "blender_handoff": blender_handoff(),
        "user_review": {
            "date": "2026-10-19 02:24",
            "words": USER_REVIEW_WORDS,
            "precedence": "기준선 1~5절보다 우선(설계-결정-기준.md 6절). 판정 순서: 사용자 선택(7절) > 사용자 검토(6절) > 기준선 1~5절 > 레퍼런스 실측 > Codex 비평",
            "applied": [
                "옛 R 패널(302~402×20~92, 연한 판 포함)을 지면에서 뺐다. 그 자리는 지도 무대 확장에서도 빼고, 사용자 선택(03:10)대로 Basic P2 '아치·볼트·돔'을 L과 같은 종이 바탕 위에 조판한다(지형·밭·포도밭 0)",
                "옛 T 패널(316~402×505~565)을 지면에서 뺐다. 그 자리는 지도 무대 확장에서도 빼고, 사용자 선택(03:10)대로 Basic P5 '지금 배우는 것'(312~402×505~568)을 하단 띠 바탕 위에 조판한다",
                "인쇄 지면의 내부 표기를 모두 뺀다(작업 이름·티어 이름·티어 색 범례·티어 색 모서리·크기 꼬리표·면적·검사 수치·히어로 군 점선 윤곽·투영 상자 모서리·가장자리 눈금·설계 주석·레퍼런스 근거 메모). 이 정보는 spec.json과 보고서에만 둔다. 사후 검사 ①(금지 표기 0)·⑩(티어 색 0)이 지킨다",
                "지면에는 자리를 예약하거나 선택을 기다린다는 글을 쓰지 않는다. 다이어그램은 실제로 인쇄될 포스터 지면만 보인다",
            ],
        },
        "user_selection": {
            "date": "2026-10-19 03:10",
            "source": "설계-결정-기준.md 7절(기준선 1~6절보다 우선, 설계 2회차 기획부터 적용: d3 판정 → d4 제작). 근거 보고서 docs/research/Basic-대체-정보-추가-건축물-조사-2026-10-19.md",
            "words": USER_SELECTION_WORDS,
            "applied": [
                "P2 아치·볼트·돔 아치·볼트·돔(302~402×20~92 = 7,200mm²): 등각 소형 단면 4칸(아치 = 비교 기준·배럴 볼트·교차 볼트·돔) + 스팬 막대 3줄(트라야누스 시장 대회랑 8.6 m → 카라칼라 열탕실 약 36 m → 판테온 43.3 m, 43.3 m = 60.0mm 비례) + 각주(거푸집에 '다져 넣어'). 지도와는 숫자 짝 표지 1~4로 잇는다",
                "P5 지금 배우는 것 지금 배우는 중(312~402×505~568 = 5,670mm²): 3단 계단(연구 → 현장 → 적용) + '가져올 것 / 못 가져올 것' 두 칸 + 탄소 정성 한 줄. S(100 vs 2000) 바로 아래 같은 오른쪽 정렬선 x 402",
                "Core 표준 랜드마크 3개 추가(각 ≥ 4,500mm², 콜로세움보다 작게): L7 막센티우스 바실리카(히어로 4층 조각 뒤, R2와 카라칼라 사이), L8 하드리아누스 영묘 + 폰스 아일리우스(테베레 굽이 안쪽 오른쪽 둑, 새 길 R7로 콜로세움과 이음), L9 마르켈루스 극장(판테온과 강 사이 테베레 둑)",
                "네로 청동 거상의 콘크리트 받침(콜로세움 뒤-왼쪽과 바실리카 사이, 벽돌 마감 콘크리트 받침 + 청동 거상 '추정'). 치수·'콜로세움' 이름 유래는 인쇄하지 않는다",
                "Z1 원 Ø64 → Ø60(중심 (275,450) 유지), 글 칸 [214,426,242,462], 합성 상자 [214,420,305,480] = 5,460mm² → Basic 최소 P5 5,670 ≥ Detail 최대 5,460",
                "무대 확장 해제: 무대 = STAGE (0,92)~(420,505) 173,460mm². 베수비오 군은 무대 안 오른쪽 위로 내린다",
            ],
        },
        "hierarchy_change": {
            "date": "2026-10-18 23:43",
            "user_words": "정보 위계를 변경하자. 도시 인포그래픽처럼 로마 건축물들이 core 정보이고, 로마콘크리트 제작과정은 basic 정보와 detail 정보로 서사하고 support로 현대 콘크리트의 유통기한은 100년, 로마콘크리트는 2000년 으로 서사하는 방향으로 정보위계를 변경하고 변경한 위계에 맞춰서 다시 설계작업 진행해",
            "precedence": "이 위계 변경이 공통 자료·지시 A~J·가중치 순서·이전 종합의 위계 서술보다 우선한다(단, 사용자 검토 2026-10-19 02:24와 사용자 선택 2026-10-19 03:10이 그보다 우선)",
        },
        "units": "A2 mm, 포스터 0~420 × 0~594, 화면 좌표(x 오른쪽, y 아래)",
        "projection": "진짜 등각(지면 축 ±30°, 수직 90°, 카메라 고도 35.264°). 평면 +X → 화면 ↘(cos30, 0.5), +Y → 화면 ↙(−cos30, 0.5), 평면 원점 = 화면 (0,0). 화면 ↘ 직선 y = tan30·x + c 는 평면 Y = c, ↗ 직선 y = −tan30·x + d 는 평면 X = d (v16 common.Iso와 같은 규약)",
        "light": "조명 없음 — " + D.STYLE_RULE,
        "style": {"rule": D.STYLE_RULE, "iso_tone": D.ISO_TONE, "shadow_expand_mm": D.SHADOW_EXPAND_MM, "outline_L7": "쓰지 않는다", "ref_rgb": {k: (list(v) if isinstance(v, tuple) else v) for k, v in D.REF_RGB.items()}},
        "weight_order": list(D.BASELINE_TOP) + ["1 사용자 선택(2026-10-19 03:10, 기준선 7절, 1~6절보다 우선)", "2 사용자 검토(2026-10-19 02:24, 기준선 6절, 1~5절보다 우선)", "3 정보 위계 변경(2026-10-18 23:43)",
                         "4 도시 인포그래픽 레퍼런스 정밀분석", "5 203X 베이징·신문 정밀분석", "6 사용자 확정 결정(바꿀 수 없음)", "7 지도교수 비평의 원칙(새 위계로 읽음)", "8 손 스케치·구상도 v3(참고만)", "9 Codex 비평"],
        "output": {
            "final": "420×594mm · 300ppi = 4961×7016px(반올림)",
            "final_px": D.OUTPUT["final"]["px"], "final_ppi": D.OUTPUT["final"]["ppi"],
            "review": "검토용 3px/mm = 1260×1782px(지금 diagram.png, 실물 크기에서 76.2ppi)",
            "review_px": D.OUTPUT["review"]["px"],
            "asset_native_width_rule": "자산 고유 폭 = 배치 폭 ÷ 25.4 × 300",
            "asset_native_width_px": {k: {"배치 폭 mm": v[0], "고유 폭 px": v[1]} for k, v in asset_widths.items()},
            "line_weights_mm": D.OUTPUT["line_mm"],
            "final_check": "최종 출력 확인 = render 출력 + global 사후 검사(v2_check.py --post out/drawn.json out/post_check.json, 규칙 ①~㉑ + 보조). 사전 검사 필수 요소 누락이나 사후 검사 실패가 1건이라도 있으면 make.py 종료 코드 1. "
                           "정보 층(make.py --info: render INFO_ONLY=1 → out/info/info_layer.png·info_check.json)은 b{N} sil.json이 생긴 뒤 선택 실행하고 사후 ⑰이 판정한다",
        },
        "sources": {
            "baseline": "/Users/um-yunsang/roman-concrete-private-refs/.work/design/설계-결정-기준.md",
            "selection_research": "/Users/um-yunsang/roman-concrete-private-refs/docs/research/Basic-대체-정보-추가-건축물-조사-2026-10-19.md",
            "reference_analysis": "/Users/um-yunsang/roman-concrete-private-refs/.work/out/refs-analysis/*_zones.png 와 관련 JSON",
            "benchmark": "/Users/um-yunsang/roman-concrete-private-refs/docs/references/benchmark-analysis/203X-벤치마크-정밀분석.md",
            "accuracy": "/Users/um-yunsang/roman-concrete-private-refs/docs/research/화산-Support-사례-조사-2026-10-18.md ([S#] 번호)",
            "report_md": "/Users/um-yunsang/roman-concrete-private-refs/docs/references/benchmark-analysis/도시-인포그래픽-종합분석-v2-새위계.md",
            "geometry_source": DATA_DIR + "/v2_map.py · v2_panels.py (v2_base.py 공용 상수)",
            "check_source": DATA_DIR + "/v2_check.py",
            "check_result": DATA_DIR + "/v2_check.json",
            "drawn": OUT_DIR + "/drawn.json",
            "post_check_result": OUT_DIR + "/post_check.json",
        },
        "rule_of_thumb": "좌표는 배치 골격이다. 워커는 상자 안에서 형태를 다듬되, 투영 상자 크기·티어 순서·맞닿음·±30° 규칙은 바꾸지 않는다. 투영 크기는 레이어 알파 외곽 상자로 잰다. "
                         "AO·조명·그림자 0, ISO_TONE 1.0/0.86/0.68, 그림자 확장 0mm(외곽 상자 = 실제 그린 면). render는 사양 값을 덮어쓰지 않는다(짝 표지는 사양 mark·mark_pt 값으로만 그린다)",
    },
    "hierarchy": {
        "definition": {
            "Core": "로마 건축물 지도(도시 인포그래픽의 랜드마크 지도): 콜로세움(히어로·최대 단일 오브젝트) + 표준 랜드마크 %d개(%s) + 지도 배경 베수비오 + 테베레강·바다·길(R1~R7)·지형·소품(네로 거상 받침 포함). 무대 = STAGE (0,92)~(420,505) %smm²(확장 0)" % (len(D.LANDMARKS), _lm_names, format(int(D.STAGE_AREA_EXT), ",")),
            "Basic": "L 로마 콘크리트란?(정의 + 재료) · P2 아치·볼트·돔(형태: 아치·배럴 볼트·교차 볼트·돔 + 스팬 비교) · B 제작 과정 6단계(재료 준비 → 마른 혼합 → 물 붓기 → 뜨거운 혼합 → 다져 넣기 → 굳기·석회 알갱이) · P5 지금 배우는 것(배움: 연구 → 현장 → 적용). 화면 평행 패널(도시편 문법). B는 지도 공사장과 지시선 1개, P2는 지도와 숫자 짝 표지 1~4로 잇는다",
            "Detail": "D 석회 알갱이·자가치유·뜨거운 혼합 패널 + 지도 위 확대 창 Z1(원 Ø%s + 글 칸, 위계는 합성 상자 %s로 잰다) + 콜아웃 C1(판테온 돔의 가벼운 골재)·C2(포르투스 방파제와 바닷물)·C4(메텔라 드럼 재결속)" % (("%g" % Z1_D) if Z1_D else "?", fbox(Z1_COMP)),
            "Support": "S 현대 콘크리트 약 100년 vs 로마 콘크리트 2,000년 비교(가장 작은 위계). 바로 아래 P5가 '그래서 지금 배우는 중'으로 잇는다",
        },
        "projected_size_order": size_order,
        "size_table": size_table,
        "checks": H["checks"],
        "ratios": {"basic_min_over_detail_max": H["ratio_basicmin_over_detailmax"], "detail_min_over_support": H["ratio_detailmin_over_support"],
                   "hero_over_landmark_median": H["hero_over_landmark_median"], "hero_over_landmark_max": H.get("hero_over_landmark_max"),
                   "hero_pct_stage": round(100 * H["hero_area"] / D.STAGE_AREA_EXT, 1)},
        "basic_min": H["basic_min"], "detail_max": H["detail_max"], "detail_min": H["detail_min"], "support": H["support"],
        "z1_box_source": H.get("z1_box_source"),
        "panel_count_rule": H.get("panel_count_rule"),
        "landmark_count": H.get("landmark_count", len(H["landmark_areas"])),
        "landmark_min_rule_mm2": H.get("landmark_min_rule_mm2"),
        "required_elements": REQ,
        "basis_d5": "사전 checks는 투영(예정) 상자끼리의 판정이다(통과 보고 아님). 최종 판정은 사후 ⑪(drawn.objects 그린 외곽 상자끼리·sil_mm2 실루엣끼리)이고 make.py가 post_summary에 적는다",
        "rule_d5": HD5,
        "hero_definition": "최대 단일 오브젝트 = 콜로세움 건물(실루엣 ≥ 다른 건물 × 1.2). 히어로 군 = 콜로세움 건물 ∪ 기초 공사장 ∪ 인물 무리 ∪ 노점 2 ∪ 네로 거상 받침(사용자 13:33 히어로 군). 사전 히어로 군 상자 = 부품 예정 상자의 합, 사후 = 그린 외곽 상자(drawn.objects hero_group)",
        "l5_rule": "메텔라는 그린 상자가 66×64.8 = 4,276.8mm²로 하한 미달이었다(d4). 설계 2D 그림은 사양 상자 [354,288,420,358] 중심 기준 %.2f배(x 420에서 잘림) → 4,530 이상(render), Blender suburb는 fit_to_box" % D.L5_DRAW_SCALE,
        "post_summary": None,
    },
    "frame": {
        "stage": {"rect": list(D.STAGE), "area_mm2": D.STAGE_AREA, "ext_rects": D.STAGE_EXT, "area_mm2_ext": D.STAGE_AREA_EXT, "rects": D.STAGE_RECTS,
                  "former_ext_not_stage": getattr(D, "FORMER_STAGE_EXT", {}),
                  "note": "지도 무대 = STAGE (0,92)~(420,505) %smm² 하나(STAGE_EXT = [], R·T 확장 0). 위 띠 오른쪽 (298~420)×(20~92)와 하단 띠 오른쪽 (312~420)×(505~568)는 L·B와 같은 종이/띠 바탕이고(지형·밭·포도밭 0) 그 위에 P2·P5를 조판한다. ext_rects는 빈 목록이다(render는 빈 목록을 '확장 없음'으로 읽는다)" % format(int(D.STAGE_AREA_EXT), ",")},
        "title": {"rect": D.TITLE["rect"], "name": D.TITLE["name"], "width_pct": 39.8,
                  "note": "주제 건축 정면 입면 액자(베이징 궁궐 문·도쿄 도리이·베를린 브란덴부르크 문·자금성 지붕 계열). 인쇄 글은 국문 제목 '로마 콘크리트'와 '로마 건축물로 읽는 로마 콘크리트'뿐이다(타이틀 안 치수 메모·부제의 시리즈 설명 0). 카라칼라 욕장 위 끝(y 94)이 아래 변에 2mm로 다가간다(도쿄 0.8mm 접촉 선례)",
                  "print_texts": D.TITLE.get("print", ["CITY LANDMARK INFOGRAPHICS · ROMA", "ROMAN CONCRETE", "로마 콘크리트", "로마 건축물로 읽는 로마 콘크리트"])},
        "panels": panels,
        "panel_rules": [
            "상자·배경판 없이 바탕 위에 조판한다(베이징·도쿄·홍콩). 연한 판 예외는 없다(P2·P5 포함)",
            "머리글: 영문 초압축 대문자 7.4mm + 국문 3.6~3.8mm 윗선 정렬(S는 5.0·2.8), 강조색 폼페이 레드 한 색. P2 '아치·볼트·돔' + '아치·볼트·돔'(3.8), P5 '지금 배우는 것' + '지금 배우는 중'(3.6, 넘치면 바로 아랫줄 왼쪽 맞춤)",
            "정렬선: L·P2 윗선 y 20, 왼쪽 정렬선 x 18, 오른쪽 정렬선 x 402(P2·S·P5, 오른쪽 여백 18mm). 하단 띠 윗선 y 505(B 18~214·D 220~306·P5 312~402, 간격 B–D 6mm·D–P5 6mm). S는 지도 모서리 패널(332~402×466~496)이고 P5가 바로 아래에 와서 한 열로 읽힌다",
            _pc_txt + "(도시편 중앙값 6, 사용자 결정 2절). 패널 면적 합 %smm² = 포스터의 %s%%" % (format(int(chk["density_estimate"].get("panel_area_mm2", 0)), ","), chk["density_estimate"]["panel_area_pct_poster"]),
            "인쇄 지면에 티어 이름·티어 색·치수·면적·검사·설계 주석 0(사양·보고서에만). 티어 배지·범례·모서리 표시도 두지 않는다(203X 문법). 티어는 크기·자리로만 읽힌다",
            "짝 표지: A~D(지도 ↔ Detail, 정보 잉크 Ø4 원 + 흰 글자 2.2)와 숫자 1~4(P2 칸 ↔ 지도, 같은 모양). B 패널의 빨간 원숫자 ①~⑥와 구분하고, P5는 원숫자를 쓰지 않는다",
        ],
        "print_rules": {
            "forbidden_pattern": D.PRINT_FORBIDDEN,
            "forbidden_pattern_ci": D.PRINT_FORBIDDEN_CI,
            "forbidden_sentences": getattr(D, "PRINT_FORBIDDEN_SENTENCES", None),
            "no_dimension_labels": {"keys": list(getattr(D, "PRINT_NO_DIMENSION_KEYS", ())), "pattern": getattr(D, "PRINT_DIMENSION", None),
                                    "rule": "바실리카 높이·영묘 치수·극장 지름·거상 치수는 인쇄하지 않는다(그 라벨·주석에 '숫자 + m' 0)"},
            "allowed": "m·km 단위와 '모식'(과학 표기), '※ … 미확인', 연구 연도, P2 스팬 막대의 경간 수치(8.6 m·약 36 m·43.3 m, '스팬 비교'로만)",
            "reader_elements_kept": ["영문 시리즈 띠 'CITY LANDMARK INFOGRAPHICS · ROMA'", "'ROMAN CONCRETE'", "'로마 건축물로 읽는 로마 콘크리트'", "과학 표기('모식', '※ … 미확인', 연구 연도)"],
            "removed_from_print": ["옛 R 패널 302~402×20~92 전부(연한 판 포함, 그 자리는 P2)", "옛 T 패널 316~402×505~565 전부(그 자리는 P5)", "타이틀 안 치수 메모", "국문 부제의 시리즈 설명", "패널 점선 틀·티어 꼬리표·지도 무대 꼬리표",
                                   "랜드마크·베수비오·히어로의 초록 모서리와 크기 꼬리표, 히어로 꼬리표·투영 상자 꼬리표", "Z1·C1·C2·C4 크기 꼬리표", "Basic 지시선 꼬리표", "히어로 군 점선 윤곽과 꼬리표", "타이틀–욕장 2mm 선",
                                   "가장자리 눈금과 y 92·y 505 표시", "푸터의 점선 틀·작업 이름·작업 정보 줄·티어 색 범례·위계/밀도 수치 2줄·푸터 안내 글", "B 패널의 ⑥ → 지도 공사장 지시선 설명 글",
                                   "자리를 예약하거나 선택을 기다린다는 글", "레퍼런스 근거 메모·설계 주석"],
            "sentence_rules": ["'콘크리트로 만든 조각'·'콘크리트로 빚은 거상' 금지(거상은 '콘크리트(벽돌 마감) 받침 위의 청동 거상' 꼴만, '추정' 표기)", "'로마 콘크리트는 저탄소'·41%·29% 금지(탄소는 정성 문장만)",
                               "반죽을 '부었다'·'붓다' 금지(다져 넣는다)", "퐁 뒤 가르 0, 미확인 주장(조사 보고서 5.2절) 0", "'콜로세움' 이름 유래는 이번 회차 인쇄 0", "'[일반 연표]' 표시 규칙 유지"],
            "colors": "지시선·끝점·짝 표지 A~D와 1~4·Z1 테두리(0.6mm)·콜아웃 테두리(0.25mm)·콜아웃 제목·소품 주석 = 정보 잉크 (58,42,28) 한 색. 폼페이 레드는 타이틀·패널 머리글·단계 번호에만. 물 이름(TIBERIS·MARE TYRRHENUM) 잉크 = %s(물색보다 짙은 파랑). 티어 색 인쇄 사용 0, 라벨 크림 바탕판 0(말풍선 태그 2개만 예외)" % (list(getattr(D, "WATER_NAME_INK", (52, 92, 124))),),
        },
        "footer": D.FOOTER,
        "footer_rule": "푸터에는 독자용 요소(로고·크레딧·QR)만 둔다. 작업 정보·범례·검사 수치·안내 글 0",
        "panel_area_pct_poster": chk["density_estimate"]["panel_area_pct_poster"],
        "panel_area_mm2": chk["density_estimate"].get("panel_area_mm2"),
    },
    "core_map": {
        "hero": {
            "name": "콜로세움(Amphitheatrum Flavium) — 히어로·최대 단일 오브젝트(건물). 히어로 군 = 건물 ∪ 공사장 ∪ 인물 무리 ∪ 노점 ∪ 네로 받침",
            # render 하위 호환 열쇠(map 옛 상수가 남아 있으면 그 값, 없으면 받침 0의 기본값). d5 원천은 아래 colosseum·landscape다
            "center_screen": list(getattr(D, "HERO_C", D.HERO_LANDSCAPE_D5["center_screen"])), "center_plan": R1(getattr(D, "HERO_C_PLAN", D.HERO_LANDSCAPE_D5["center_plan"])),
            "nofill_R_plan": 90.5, "nofill_rule": "사용자 16:13·16:14: 조경 중심 평면 R 90.5는 비워 두는 땅의 기준일 뿐이다(건물을 콜로세움 쪽으로 모으므로 검사에 쓰지 않는다)",
            "removed_keys_d5": "d4 받침 열쇠(oct_R_plan·base_side_T·ring_ratio·base_oct_screen·walls·cutaway)는 d5에서 뺐다(8.2·13:33). 원천은 colosseum·landscape",
            "projected_box": hb, "projected_wh": H["hero_wh"], "projected_area_mm2": H["hero_area"],
            "hero_group_box": hb, "building_box": HD5.get("hero_building_box"), "building_sil_mm2": HD5.get("hero_building_sil_mm2"),
            "colosseum": colosseum_spec(), "landscape": landscape_spec(),
            "interior": getattr(D, "HERO_INTERIOR", None),
            "form": [
                "기준선 8.1(LocalBanana와 같은 본체): 외곽 타원 반축 44×36.6(평면, 장축 315° = 화면 가로), 중심 (446.54,161.86) = 조경 중심 (462.34,173.66)에서 뒤-왼쪽 (−15.8,−11.8), 아치 40칸, 층 윗선 z 11.5·24.5·37·53",
                "부서진 정도(θ = atan2(dY,dX)): 100~205° 왼쪽~뒤-왼쪽 4층 53(앞쪽 끝 100~112° 경사 부벽 41·46·50, 뒤쪽 끝 205~209° 수직 절단 44), 209~322° 뒤~오른쪽 3층 37(일부 33.5), 322~338° 3층 → 2층 계단 31·27, 338~18° 앞-오른쪽 2층 24.5(들쭉날쭉 18~24.5), 18~72° 경기장 앞 정면 1층 + 토막 ≤ 17, 72~100° 앞-왼쪽 3층 30·37",
                "보이는 면: 둘째 고리 37(정면 10~80°만 9~12), 관람석(깊이 10.4~22.7, 높이 24.0→4.4, 계단석 θ 238~360°·0~48°, 나머지 방사벽·짙은 빈칸), 경기장 반축 20.1×12.7 — u ≥ −2.0 복원 나무 바닥(55%, Z 0.6, 난간), u < −2.0 하이포게움(바닥 Z −4.0, 동심 벽·중앙 통로·칸막이)",
                "기준선 8.2: 팔각형 받침대 없음 — 콜로세움과 둘레는 지도 땅(Z 0) 위에 바로 놓이고 도시 조직과 이어진다. 받침 옆면·지층·앞 변 기초 절개 0",
                "둘레(사용자 16:13·16:14): 광장·판석·경계석·문 앞 포장·둘레 나무·인물 무리·노점·공사장·길은 없다. 네로 거상 받침과 작은 포장 마당만 곁에 둔다. LocalBanana 조경 배치는 옮겨 오지 않는다(12:49)",
                "확대 원 Z1은 ❺ 패널 안 Ø30(중심 (240,536))이고 지도 쪽 지시선은 없다(사용자 15:41). 지도에는 ❺ 근거 표지(Ø3.2 + 흰 '5')만 남는다",
                "높이 과장 없음(8.1 수치 그대로), 라벨 수치는 실제값(약 188×156 m, 높이 약 48 m)",
            ],
            "gates": {},
        },
        "landmarks": landmarks,
        "background": background,
        "nero_colossus": {
            "found": NERO is not None, "source": NERO.get("source") if NERO else None, "name": NERO.get("name") if NERO else None, "box": _nero_box,
            "plan_center": (NERO.get("item") or {}).get("plan") if NERO else None, "base": "8×8, 높이 5, 벽돌 마감 콘크리트, 윗단에 가는 대리석 띠", "statue": "청동 2.4×2.4, 높이 15, 복원 추정",
            "rules": ["콜로세움 뒤-왼쪽과 바실리카 사이(베누스·로마 신전 쪽) 지면(d4 자리 유지: 평면 중심 (327.0, 113.4), 화면 받침 [177.8,211.1,192.2,224.3], 거상 [183.1,200.2,186.9,216.3])", "그린 실루엣이 콜로세움·바실리카와 2mm 이상(사후 ⑭)", "받침 둘레 화면 [172,196,198,228]은 집·나무 0인 작은 포장 마당(hero가 짓고 ground가 비운다), 사람 키 4.9",
                      "소품 주석(2.6, 정보 잉크, 말풍선 없음) 2줄 '콘크리트(벽돌 마감) 받침 위의' / '네로의 청동 거상(추정)'. 치수·'콜로세움' 이름 유래 인쇄 0"],
        },
        "bridge": {"found": BRIDGE is not None, "source": BRIDGE.get("source") if BRIDGE else None, "name": BRIDGE.get("name") if BRIDGE else None,
                   "spec": _bridge_spec(), "polys_screen": [[R2(p) for p in pg] for pg in (BRIDGE.get("polys") or [])] if BRIDGE else None,
                   "rule": "상판이 ↘ 팔을 건너 R7과 만난다(상판 높이 3, 아치 3개). 다리–강·다리–R7 접촉은 정상(사전 허용쌍·사후 ⑭ 제외). 다리는 L8 영묘 묶음"},
        "zones": {
            "도심": "콜로세움(건물, 받침 0, 둘레는 땅 바탕뿐) + 테베레 ↘ 팔 + 네로 거상 받침과 작은 포장 마당 [172,196,198,228](뒤-왼쪽)",
            "시내": "트라야누스 시장(왼쪽 위) · 판테온(왼쪽 가운데) · 마르켈루스 극장(판테온과 강 사이 둑) · 막센티우스 바실리카(히어로 4층 조각 뒤) · 카라칼라 욕장(뒤쪽 가운데-오른쪽)",
            "테베레 오른쪽 둑": "하드리아누스 영묘 + 폰스 아일리우스(굽이 안쪽, 다리 북쪽 끝은 진입 경사로 땅에 잇는다)",
            "남동 교외": "수도교 아치 열(오른쪽 위) · 아피아 가도 · 카이킬리아 메텔라 무덤(오른쪽 가운데) · 포도밭·교외 빌라(오른쪽 아래, 무대 아래 변 y 505까지). 하단 띠 오른쪽은 P5(띠 바탕)",
            "서남서 해안": "테베레 하구 · 포르투스(육각 내항 육지 + 외항·등대 바다) · 오스티아(하구 왼쪽 둑, Z1 글 칸 아래) · 바다(왼쪽 아래 모서리)",
            "가장 먼 곳": "무대 안 오른쪽 위: 베수비오 %s · 포도밭 농장 %s · 알바노 구릉 띠 %s(그리는 순서 산 → 농장 → 구릉, 앞 능선이 산 밑동 x 360~418 전체를 3~5mm 연속으로 가림). 위 띠 오른쪽은 P2(종이 바탕)" % (fbox(VES_BOX), fbox(FARM.get("box") if FARM else None), fbox(ALBANO.get("box") if ALBANO else None)),
        },
        "river": {
            "name": "테베레강(Tiberis)",
            "entry_screen": list(D.RIVER_ENTRY_SCREEN), "bend_screen": R1(D.RIVER_BEND_SCREEN), "mouth_screen": R1(D.RIVER_MOUTH_SCREEN),
            "plan": {"arm1": f"평면 Y = {D.RIVER_Y} (↘, 왼쪽 변 → 굽이)", "arm2": f"평면 X = {D.RIVER_XB} (↙, 굽이 → 해안 Y {D.COAST_Y})", "fillet_R": D.RIVER_FILLET},
            "width_screen_perp_mm": {"↘ 팔": D.RIVER_W1, "↙ 팔(하구 쪽)": D.RIVER_W2},
            "polygon_screen": river_poly,
            "centerline_screen": [[round(x, 2), round(y, 2)] for x, y in D.RIVER_SCREEN_PTS],
            "centerline_plan": [[round(X, 2), round(Y, 2)] for X, Y in D.RIVER_PLAN],
            "width_plan": _river_width_plan(),
            "fillet_R_plan": D.RIVER_FILLET,
            "tributaries": [{"name": t_["name"], "centerline_screen": [list(q) for q in t_["screen_pts"]],
                             "centerline_plan": [[round(v, 2) for v in D.to_plan(*q)] for q in t_["screen_pts"]],
                             "width_plan": [t_["width"]] * len(t_["screen_pts"]),
                             "join_plan": [round(v, 2) for v in D.to_plan(*t_["screen_pts"][0])],
                             "end_plan": [round(v, 2) for v in D.to_plan(*t_["screen_pts"][-1])]} for t_ in D.RIVER_TRIBS],
            "rules": ["±30°만(수직 구간 0), 꺾임은 평면 직각 1회(둥근 굽이)", "강은 콜로세움 군의 가장자리만 지나고 가르지 않는다", "물 면 = 평면색 한 값(PAL water), 둑 = 평면 면 톤(AO 0)", "하구는 바다로 흘러들고(사용자 B 원래 결정·트라바키), 하구 오른쪽 둑에 포르투스", "폰스 아일리우스가 ↘ 팔을 건너 영묘(오른쪽 둑)와 땅(왼쪽 둑 진입 경사)을 잇는다"],
            "river_pct_stage": chk["density_estimate"]["river_pct_stage"],
        },
        "sea_coast": {
            "coastline": {"pts": D.COAST, "equation": f"y = tan30·x + {D.COAST_Y} (평면 Y = {D.COAST_Y})", "note": "하나의 ↘(+X) 직선. 좌우 부두 수직 변 없음(B). 강 ↘ 팔과 평행하게 66mm(평면) 아래"},
            "sea_polygon": D.SEA,
            "sea_under_bottom_band": {"poly": D.SEA_UNDER_BAND, "note": "하단 띠 밑으로 이어지며 아래로 갈수록 바탕색으로 흐린다(홍콩 앞바다 선례). B·D 패널은 그 위에 얹는다"},
            "coast_section": "육지 앞 변(해안선)에 지층 단면 10mm(3겹)를 한 번만 보인다(서울 17~19mm·홍콩 18~21mm의 축소). 포르투스 부두 구간은 3mm",
            "on_sea_only": ["클라우디우스 외항·방파제·등대(포르투스 외형)", "화산재 운반선", "콜아웃 C2·포르투스 라벨·바닥 글 MARE TYRRHENUM(정보 오버레이)"],
            "sea_pct_stage": chk["density_estimate"]["sea_pct_stage"],
        },
        "portus_geometry": {
            "hexagon_plan_center": list(D.PORTUS_HEX_C), "hexagon_plan_R": D.PORTUS_HEX_R,
            "claudian_basin_plan_center": list(D.PORTUS_BASIN_C), "claudian_basin_plan_R": D.PORTUS_BASIN_R, "lighthouse_box": D.PORTUS_LIGHT,
            "canals": getattr(D, "PORTUS_CANALS", None), "moles": getattr(D, "PORTUS_MOLES", None), "lighthouse": getattr(D, "PORTUS_LIGHTHOUSE", None),
            "hexagon_water_R": getattr(D, "PORTUS_HEX_WATER_R", None),
            "east_canal": getattr(D, "PORTUS_EAST_CANAL", None),
            "canal_polys_screen": ({k: [R2(p) for p in v] for k, v in D.portus_canal_polys().items()} if hasattr(D, "portus_canal_polys") else None),
            "rules": ["원본은 map 사양, 그림은 render", "외항 방파제 평면 반지름 18.4~21.0, 팔 A 263°→123°·팔 B 277°→417°(=57°), 마지막 조각을 끝각에서 정확히 자른다 → 투영 입구 폭 ≈ 20mm(허용 18~22)",
                      "등대섬 평면 각·반지름·화면 기저는 lighthouse 값(d4 결정 78°·22.0, 기저 ≈ (15.98,432.35)). 섬과 두 팔 끝 사이(수면)와 탑과 두 팔 끝 사이(보이는 물) 모두 ≥ 4mm(사후 ⑨)",
                      "운하 2개(화면 폭 2.6mm)의 평면 Y 끝점은 canals 값 그대로 그린다(render 추가 연장 0, 사후 ⑮ ±0.3mm). 육각 내항 수면과 외항 수면 안쪽까지 잇고 포장·안벽에 폭 3mm 개구부", "외항 열주는 팔 B의 12~54°에만",
                      "포르투스 라벨 글 블록은 등대섬·탑과 2mm 이상(필요하면 슬롯 안에서 아래로 최대 3mm)"],
            "land_sea_split_mm2": chk["portus_land_sea_split_mm2"],
            "polygons_screen": portus_polys,
        },
        "roads": roads,
        "aqueduct": {"ground_line_screen": [R1(D.to_screen(*D.AQUEDUCT_PLAN[0])), R1(D.to_screen(*D.AQUEDUCT_PLAN[1]))], "arch_height_mm": D.AQUEDUCT_H,
                     "source": "map v2_map.AQUEDUCT_PLAN(원본). 읽는 쪽: global(검사·조립), render(아치 열 그리기), panels(수도교 라벨 슬롯·지시선 ↑)",
                     "note": "오른쪽 변 밖(남동 시골)에서 ↖로 들어와 카라칼라 욕장 오른쪽 변 (336,160)에 닿는다(아쿠아 마르키아의 지선 아쿠아 안토니니아나 → 욕장 저수조 64개[S47][S49]). 2단 관통 아치(높이 26·교각 간격 8 유지, 아래층 개구 폭 5.3·위층 3.9, 아치 안쪽 면 1.5mm, 개구부 뒤로 지면이 보인다), 지면보다 채도를 2배 이상 높인 벽돌·석재 색(지스몬디 2.1~4.6배). 숫자 짝 표지 1 = 아치 면"},
        "road_rules": ["±30° 띠만, 꺾임은 평면 직각", "폭은 화면 수직 폭. 주축 16mm + 흰 중앙선 1.6mm(도쿄·베를린), 보조 8~10mm", "길과 실제 지면 다각형의 간격 ≤ 1.6mm(판테온·욕장·메텔라·시장·콜로세움·바실리카–R2, 사후 검사 ⑤)",
                       "길 연장은 map이 사양 좌표(plan_pts)에 넣는다. render는 길 좌표를 하드코딩하지 않는다", "모든 랜드마크가 길·강·해안·수도교 중 하나에 2.5mm 안으로 닿는다(도쿄 19/23)",
                       "길은 없다(사용자 16:14). 폰스 아일리우스 북쪽 끝(Y 304.76)에서 남쪽 끝 Y 294.76~304.76에 Z 0→3.0 진입 경사를 둔다(다리 상판 3.0과 높이 차 0)"],
        "props": D.PROPS,
        "terrain": D.TERRAIN,
        "planted": D.PLANTED,
        "labels": {
            "count": chk["labels"], "reference": "도시편 11~21개(중앙값 17), 파리 15·상하이 21·홍콩 16·도쿄 21·베를린 15",
            "slots": D.LABELS, "floor_text": D.FLOOR_TEXT,
            "type_faces_mm": D.TYPE_FACES,
            "grammar": [
                "지도 위 글자는 전부 등각 평면: 이름·설명은 벽면(세로획 수직), 지형명은 바닥에 눕힌다. 화면 평행 0° 글자 0개",
                "서체 크기는 글자면(잉크 높이: 국문 '한', 영문 'H' 대문자 높이)으로 잰다. em은 글꼴 실측 비로 환산. 스택: 영문 압축 볼드 대문자 3.8mm → 국문 볼드 3.8mm + 원어 위첨자 2.1mm → 헤어라인 규선 → 본문 3.0mm(줄 피치 4.15mm). 본문 첫 줄은 그 건물의 '콘크리트 이야기'(H)",
                "배율 1.00 고정(자동 축소·개별 배율 금지), 모든 랜드마크가 같은 크기, 라벨 바탕판 없음(말풍선 태그 2개만 예외, 2.6mm 고정). 넘치면 줄바꿈과 슬롯 안 자리 조정만 한다",
                "슬롯은 화면 상자(허용 영역)이고, 실제 글 블록 평행사변형은 길·건물·다른 라벨·지시선과 2mm 이상 띄운다. 비스듬한 블록과 길·건물·둑 사이는 세로 2.4mm(수직 거리 2.0)를 띄운다. 브래킷 수직선은 글 블록 밖 1.5~4mm",
                "방향: 콜로세움 ↘·판테온 ↗·트라야누스 시장 ↗·카라칼라 욕장 ↗·수도교 ↗·메텔라 ↘·포르투스 ↘·베수비오 ↗(브래킷)·막센티우스 바실리카 ↗·하드리아누스 영묘 ↗·마르켈루스 극장 ↘·네로 거상 주석 ↗·화산재 운반선 ↘(깃대형)·바지선 ↘(깃대형). 바닥 글은 그 선형 요소와 평행",
                "형식: 랜드마크 = 브래킷형, 작은 소품 설명 = 소품 주석(2.6, 정보 잉크, 말풍선 없음, ↘30° ≤ 12mm 지시선). 사용자 16:14: 탈것·말풍선 태그·깃대형 라벨은 없다",
                "잉크: 지도 라벨은 중립 잉크 한 색(땅 위 짙은 갈색, 물 위 밝은 크림 또는 톤온톤). 물 이름 바닥 글은 물색보다 짙은 파랑. 강조색은 쓰지 않는다",
                "방위표·축척·범례는 지도에 두지 않는다(베이징·청와대). 실제 방위·거리는 베수비오 라벨의 짧은 거리 표기만 둔다",
            ],
        },
    },
    "chapter_marks": {"raw": D.CHAPTER_MARKS, "map_head": D.MAP_HEAD, "badge": D.CHAPTER_BADGE},
    "route_marks": D.ROUTE_MARKS,
    "pair_marks": {
        "raw": getattr(D, "PAIR_MARKS", None),
        "points": PAIR_POINTS,
        "counts_spec": chk.get("pair_marks_spec", {}).get("counts"),
        "expected_drawn": getattr(D, "REQUIRED_MARKS", None),
        "shape": {"r_mm": D.TYPE_FACES.get("mark_r", 2.0), "glyph_mm": D.TYPE_FACES.get("mark_glyph", 2.2), "ink": "정보 잉크 (58,42,28) 원 + 흰 글자"},
        "rules": [
            "A~D: 지도 ↔ Detail(A = 공사장 거푸집 오른쪽 면 쪽 (%g, %g)(D5, 시작점의 수직 방향 3.5mm) · Z1 원 오른쪽 위 바깥 (299.5,425.5) · D 머리글 시작 (224.0,509.8) 3곳, B·C·D는 지금 자리 2곳씩)" % tuple(D.Z1_A_MARK),
            "1~4: P2 칸 ↔ 지도(1 = 수도교 아치 면 (372,163), 2 = 바실리카 측랑 가운데 칸 열린 면 (225,177), 3 = 트라야누스 시장 대회랑 걷은 지붕 칸 윗면 (76.2,111.6)±5(기획 (100,112)은 빈 지면이라 통합 d4에서 render 실측 자리로 고침) — render가 실제 볼트 칸 위로 맞춰 기록, 4 = 판테온 돔 윗면 (78,203)±4). P2 칸 중심 (304.5,33.5)·(330.17,33.5)·(355.83,33.5)·(381.5,33.5)",
            "표지는 사양의 mark·mark_pt 값으로만 그린다(이름 추론 금지). 지도 표지는 다른 글·지시선·표지와 2mm 이상(사후 ⑬)",
            "drawn.json texts role 'mark'에 글자·중심·출처(map/detail/panel)를 기록한다(총 17개: A 3·B 2·C 2·D 2·숫자 8)",
        ],
    },
    "basic": {
        "panels": [p for p in panels if p["tier"] == "Basic"],
        "panel_ids": _basic_ids,
        "process_representation": {
            "decision": "패널 안 단계 도식(B) + 지도 위 공사장 장면(Core 소품) + 지시선 1개",
            "panel": "B 196×60mm: 6칸 등각 소형 장면, 칸 사이 바닥 화살표(신문), 아래 시간 화살표(피라미드), 단계 번호 원(폼페이 레드). 단계명 3.0mm, 설명 2.6mm(피치 3.9), 시간 화살표 글 2.1mm",
            "map_scene": "콜로세움 앞-왼쪽 땅 위의 기초 공사장(거푸집·다짐 막대 일꾼·반죽 통·재료 더미, 상자 [208,386,250,410]) + 테베레 하역장·석회 가마·수레·바지선(① 재료 준비와 같은 그림). 거푸집 오른쪽 면(다져 넣은 층)이 확대 창 Z1의 출발점",
            "link": None,
            "evidence": "피라미드 CHANGE OF THE FORM 196×50mm(끝 아이콘이 히어로 꼭짓점 15mm 옆), 런던 BUS LINE 9(지도 위 버스 → 패널 제목 지시선), 신문 바닥 화살표, 자금성 ROOF BUILDING(패널 안 등각 아이콘)",
        },
        "form_and_learning": {
            "P2": "아치·볼트·돔: 머리글 y 21~29, 등각 소형 단면 4칸(각 23×30mm, y 32~62, x 302~325 / 327.67~350.67 / 353.33~376.33 / 379~402: 아치·배럴 볼트·교차 볼트·돔), 칸 글 이름 2.6 + 캡션 2.1 최대 2줄(② 캡션 '점선 = 무너진 신랑 볼트 복원'), 스팬 막대 3줄(y 66~86, 피치 6.5, 높이 2.5, 왼끝 x 302, 43.3 m = 60.0mm: 8.6 m = 11.9mm·약 36 m = 49.9mm·43.3 m = 60.0mm, 막대 오른쪽 2mm에 2.6 글), 각주 2.1 한 줄(y 88~91, 거푸집에 '다져 넣어' 곡면 지붕)",
            "P5": "지금 배우는 것: 머리글 영문 7.4(x 312부터) + 국문 3.6 '지금 배우는 중', 3단 계단(연구 → 현장 → 적용, 각 28.7mm 폭, y 520~541, 원숫자 없음), 아래 두 칸(각 44mm, y 543~562) '가져올 것'·'못 가져올 것', 탄소 2.1 한 줄(y 563~567). 본문 ≥ 2.55mm, 주석 ≥ 2.05mm",
            "evidence": "도시편 하단 띠·모서리 패널 문법(베이징·홍콩·상하이·서울, 파리·도쿄 BRIDGES), 사용자 선택 1안 '형태 → 배움'",
        },
    },
    "detail": {
        "panel": next(p for p in panels if p["id"] == "D"),
        "map_elements": details,
        "leaders": list(D.LEADERS),
        "rules": [
            "지시선은 수직·±30°, 꺾임 ≤ 1, 끝점 지름 0.9mm, 굵기 0.30mm, 정보 잉크 한 색, 첫 점 = 지도 쪽. 화살촉은 ⑥ 공사장 지시선의 패널 쪽 끝에만 작게",
            "짝 표지: 콜로세움 절개·Z1·D = 'A'(3곳), 판테온·C1 = 'B', 포르투스·C2 = 'C', 메텔라·C4 = 'D'(자금성 A·B·C 깃발 짝 문법). Ø4 정보 잉크 원 + 흰 글자 2.2. 사양 mark·mark_pt 값으로만 그린다",
            "지시선끼리, 지시선과 라벨의 교차는 0이다(길 위 통과는 허용)",
            "Z1 위계는 원(Ø%s)과 글 칸을 합친 합성 상자 %s로 잰다. Basic 최소(P5)보다 작게 유지한다" % (("%g" % Z1_D) if Z1_D else "?", fbox(Z1_COMP)),
            "Detail 최소(콜아웃)는 Support(2,100mm²)의 1.1배 이상을 유지한다. 콜아웃을 줄이면 S도 같이 줄인다",
            "글과 상자 테두리는 3mm 이상 띄운다. Z1 테두리 0.6mm, 콜아웃 테두리 0.25mm(정보 잉크)",
        ],
    },
    "support": {
        "panel": [p for p in panels if p["tier"] == "Support"][0],
        "rules": ["포스터에서 가장 작은 정보 요소(2,100mm²)", "막대 2개는 콘크리트 시험체 모양: 높이 4.0mm, 끝 타원 반폭 0.6mm, 같은 왼끝 x 334.4, 바깥 끝 x 337.4(현대)·x 394.4(로마) → 바깥 길이 3.0 : 60.0 = 1:20, 격자선 없음(신문 TOP 6)",
                  "'로마 콘크리트 2,000년+'는 막대 안에 쓴다. 각주는 2.1mm 두 줄: 강도가 아니라 수명(압축 강도는 현대 콘크리트가 높다[S4])", "지도 모서리 패널: 오른쪽 아래 포도밭 위 고요한 영역. 바로 아래 하단 띠의 P5와 오른쪽 정렬선 x 402를 공유한다"],
    },
    "measurements": {
        "hero_cluster": chk["hero_cluster"], "core_group_city": chk["core_group_city"],
        "density_estimate": chk["density_estimate"], "ring_distance_mm": chk["ring_distance_mm"], "ring_distance_background_mm": chk.get("ring_distance_background_mm"),
        "ring_range_median": chk["ring_range_median"], "left_right": chk["left_right"],
        "contact_distance_mm": chk["contact_distance_mm"], "geo": chk["geo"], "overlaps_not_allowed": chk["overlaps_not_allowed"],
        "slot_overlaps_allowed": chk.get("slot_overlaps_allowed"),
        "land_in_sea": chk["land_in_sea"], "land_in_river": chk["land_in_river"],
        "required_elements": REQ, "landmark_shape_source": chk.get("landmark_shape_source"), "bridge": chk.get("bridge"),
        "pair_marks_spec": chk.get("pair_marks_spec"),
        "check_warnings": chk.get("warnings", []),
    },
    "accuracy_rules": [
        "육상 건물(콜로세움 등)은 민물, 바닷물은 항구 구조물에만[S1][S4][S12]",
        "콘크리트는 거푸집에 '다져 넣는다'. '타설'·'붓기'를 쓰지 않는다[S4]",
        "화산재 산지: 바다 공사 = 나폴리만 포추올리 일대(캄피 플레그레이), 로마 시내 건물 = 알바노 구릉 붉은 화산재. 둘 다 핀·라벨로만. '포졸라나 = 베수비오 화산재'는 쓰지 않는다[S4][S6][S7]",
        "베수비오 79년 이전 모습: 넓은 봉우리 하나·잿빛 평평한 정상·포도밭 비탈, 연기 없음, 분화는 '79년'만[S3][S24][S30]. 라벨은 브래킷(VESUVIUS / 베수비오 / '79년 분화', 들어가면 '약 200 km 남동')",
        "카라칼라 욕장: 본문 4줄 '겉은 벽돌, 속은 콘크리트' · '돔 위쪽엔 가벼운 경석' · '열탕실 돔 경간 약 36 m' · '(오큘러스·코퍼는 복원 추정)'. 오큘러스·코퍼는 반드시 '복원 추정'으로 쓰고(미확인 목록 5.2), 빛은 큰 창 중심, 코퍼는 얕은 격자로 판테온과 구분[S47][S48][S49]",
        "수도교: 영문 'AQUEDUCT', 국문 '수도교', 위첨자 'Aqua Antoniniana'. 본문 '수로 안은 방수 모르타르' · '아쿠아 마르키아의 지선이' · '욕장 저수조 64개에 물을 댐'(조사 보고서 192행 [S47][S49]). 클라우디아 이름·보수 구간 문장·실측 좌표는 쓰지 않는다. 퐁 뒤 가르는 쓰지 않는다",
        "막센티우스 바실리카: 현존하는 북쪽 측랑 3칸의 팔각 코퍼 배럴 볼트, 무너진 신랑 교차 볼트는 점선 복원(0.25mm). 높이 수치 인쇄 금지. 판테온 코퍼와는 '배럴 볼트'로 구분(기준선 7.2)",
        "하드리아누스 영묘 + 폰스 아일리우스: 사각 기단 + 큰 원통(겉은 대리석, 속은 콘크리트) + 다리. 정상 조각과 교황 증축(산탄젤로성) 형태는 그리지 않는다. 치수 인쇄 금지. 메텔라와는 사각 기단과 다리로 구분(기준선 7.2)",
        "마르켈루스 극장: 반원 평면·아케이드 2단(3단은 그리지 않고, 그린다면 점선 + '추정'). 테베레 홍수에 거듭 잠긴 콘크리트 기초에서 결정이 자라 보강(Jackson 2011·2026). 지름 인쇄 금지(기준선 7.2)",
        "네로 거상: 받침은 벽돌 마감 콘크리트(원래 대리석으로 덮임), 청동 거상은 복원 상상이라 '추정'. 라벨은 '콘크리트(벽돌 마감) 받침 위의 청동 거상' 꼴만. '콘크리트로 만든 조각'·'콘크리트로 빚은 거상' 금지, 치수 인쇄 금지, '콜로세움' 이름 유래는 이번 회차 인쇄 0(기준선 7.3)",
        "P2: 아치 칸은 '비교 기준'(아치는 콘크리트 없이도 가능), 콘크리트가 가능하게 한 모양은 볼트·돔. 판테온 수치는 지도 라벨과 다르게 '스팬 비교'로만. 퐁 뒤 가르 0. 각주는 거푸집에 '다져 넣어'(붓다 금지)(기준선 7.1)",
        "P5: 연구는 2014 시장 모르타르 판 모양 결정·2017 바닷물이 키운 광물·2023 MIT 실마리 → 2025 폼페이 확인을 한 덩어리로(D와 중복을 줄인다). 못 가져올 것: 강도가 느리게 붙음·철근을 못 지킴(알칼리성 낮음)·부재가 커짐. 탄소는 정성 문장만(만들 때 배출은 비슷하거나 더 크고, 오래 쓸수록 이득). 41%·29%·'로마 콘크리트는 저탄소' 금지(기준선 7.1)",
        "판화 속 황제 거상은 판화가의 상상도. 넣더라도 라벨에서 사실로 쓰지 않는다(불변 조건 13)",
        "콜로세움 시료 직접 분석은 미확인: 기초 깊이·화산재 산지를 단정하지 않는다. '겉은 석회화 돌, 속과 기초는 콘크리트'로 쓴다[S61][S4]. Z1 창 안 그림은 '로마 콘크리트 단면 모식'",
        "판테온 골재 산지는 미확인: '위로 갈수록 가벼운 골재'까지만 쓴다[S13][S77]",
        "로마 콘크리트가 현대보다 강하다고 쓰지 않는다. 강점은 오랜 결속과 회복력이다[S4]",
        "'2,000년 동안 더 단단해졌다' 대신 '바닷물과 반응해 새 광물이 자라 결속이 강해졌다'[S4][S12]",
        "C2 첫 문장 '2017년 연구, 코사 항 시료'는 유지하고, 둘째 문장은 '별도 시료: 포르투스의 트라야누스 방파제(약 115년)' · '로마 근교 화산재 + 나폴리만 화산재를 섞었다'로 쓴다(조사 보고서 604행 [S4])",
        "'2023년 MIT가 정확히 밝혀냈다' 대신 '2023 MIT 연구가 실마리를 찾고 2025 폼페이 공사 현장 연구가 확인했다'[S10][S11]",
        "메텔라 무덤의 류사이트 재결속은 석회 알갱이 자가치유와 다른 메커니즘이라 문장을 구분한다[S9][S4]",
        "일반 연표 항목(80 콜로세움 개장·약 125 판테온 재건)은 이번 판 지면에 없음. 다시 넣을 때 '[일반 연표]' 표시를 달고 인쇄 전 출처를 확인한다",
    ],
    "principles": T["PRINCIPLES"],
    "conflicts": T["CONFLICTS"],
    "holds": T["HOLDS"],
    "invalidated_from_previous": T["INVALIDATED"],
    "reused_from_previous": T["REUSED"],
    "drawn_contract": {
        "path": "out/drawn.json(render가 쓴다) → global 사후 검사 v2_check.py --post out/drawn.json out/post_check.json [spec.json] [--info out/info/info_check.json]",
        "units": "화면 mm(포스터 0~420 × 0~594, x 오른쪽·y 아래)",
        "schema": {
            "footprints": {"required": ["name", "kind", "poly"], "unique": None, "geom": "poly"},
            "roads": {"required": ["id", "name", "polys"], "unique": "id", "geom": "polys"},
            "objects": {"required": ["id", "name", "box"], "unique": "id", "geom": "box"},
        },
        "schema_rule": "세 목록은 위 형식(목록형)만 받는다. 목록이 아니거나 필수 필드가 빠지거나 id가 겹치면 사후 보조 '계약 형식'이 실패한다(make.py 종료 코드 1)",
        "fields": {
            "texts": "[{text, layer(층), role(label_en·label_ko·label_sup·label_body·prop_annot·tag·head_en·head_ko·step·subtitle·body·note·mark 등), font, em, face(글자면 mm), bbox 또는 poly, pitch(여러 줄일 때), panel(속한 상자 id)}]. role 'mark'(짝 표지)는 text = 글자(A~D·1~4), c = 중심 [x,y], source = map·detail·panel, r = 원 반지름(2.0)을 함께 쓴다(총 17개: A 3·B 2·C 2·D 2·숫자 8)",
            "labels": "[{name(슬롯 이름), kind(브래킷·깃대형·태그·소품 주석), poly(실제 글 블록 평행사변형), dir(↗·↘), scale, slot([x0,y0,x1,y1]), faces{en,ko,sup,body | 소품 주석은 모든 줄 2.6}, pitch, leader{pts, dot_d, target, gap, lw}, clearance{building(알파 ≥128 건물과의 최소 간격 mm)}}]. 깃대형은 leader.pts가 한 수직선(x 편차 ≤ 0.1)",
            "leaders": "[{name(사양 지시선 이름), pts, dot_d, lw(0.30), target, gap(대상 면과의 간격 mm), mark{letter, c}}]. '→ 확대 창 Z1' 지시선은 공사장 거푸집 오른쪽 면 (232.0, 396.8)에서 ↘30° 한 직선",
            "footprints": "[{name, kind, poly}] — 판테온 앞마당·돔·드럼, 욕장 지면, 시장 지면, 메텔라 대지·드럼, 공사장 받침·거푸집 앞면·거푸집 오른쪽 면, 콜로세움 건물·외벽, 노점 1·2, 포르투스, 선체, 바실리카 지면·측랑 볼트·신랑 유적, 영묘 기단·원통, 폰스 아일리우스 다리, 극장 반원 아케이드, 네로 거상 받침·네로 거상, 오스티아. 콜로세움 받침·기초 절개 footprint는 0(8.2)",
            "roads": "[{id, name, polys}](실제로 그린 길 띠, R7 포함, polys = 다각형 목록)",
            "objects": "[{id, name, box, sil_mm2}] — id 'hero'(콜로세움 건물 외곽 상자 + 알파 ≥128 실루엣 면적 sil_mm2), 'hero_group'(히어로 군 외곽 상자 = 건물 ∪ 공사장 ∪ 인물 무리 ∪ 노점 ∪ 네로 받침), L1~L9(각 sil_mm2), V, worksite, 소품(네로 거상 포함). 사후 ⑪은 hero_group으로 잰다",
            "boxes": "[{id(L·P2·B·D·S·P5·Z1 원·Z1 글 칸·Z1 합성·C1·C2·C4), tier, box 또는 circle{c,d}, border(테두리를 그렸는가), lw(테두리 굵기: 콜아웃 0.25·Z1 0.60), kind}]",
            "strokes": "[{role(내부선·지시선·콜아웃 테두리·Z1 테두리·P5 계단선·복원 점선·보조선 …), lw, print(인쇄 여부), count}] — 인쇄 선 굵기 요약(사후 ⑯). 0.10mm보다 가는 보조선은 print:false",
            "forms": "{hero: {semi_axes_plan, major_az_deg, center_plan, wall_profile[[t0,t1,lo,hi,메모]], second_ring{h, front_az, front_h_max}, wood_frac, base_side_mm}(실제로 그린 본체 값, 사후 ⑱), aqueduct_form, basilica_form, hypogeum}",
            "p5": "{stair: {pts(꺾은선 꼭짓점, D15), lw 0.35, fill false}, fill_boxes(배경판 수 = 0), steps, cells}",
            "s_bars": "[{name(현대·로마), x0, x1(끝 타원 포함 바깥 끝), h}]",
            "density": "{num_mm2(알파 ≥128 합집합), stage_mm2(= 173,460), pct_full_stage(= num ÷ 173,460), covered_mm2, den_mm2(= 무대 − 패널·Detail 덮는 면적), pct_open_stage(= num ÷ den)} — 판정은 전체 무대",
            "crowds": "[{name, center, feet[[x,y]...], n, height_mm(또는 heights[])}] — 키 4.6~5.2(D8 히어로 축척)",
            "portus": "{entrance_w, island_water[팔 A, 팔 B](수면), tower_to_arm_tips[팔 A, 팔 B](탑까지 포함한 보이는 물), canals[{name, continuous, opening_w, plan_y(실제 그린 평면 Y 범위)}]}",
            "tier_color_uses": "정수(티어 색으로 칠한 인쇄 요소 수, 0이어야 한다)",
            "stage": "{rects: 실제로 그린 무대 사각형 목록} — STAGE 하나",
        },
        "info_check": "out/info/info_check.json(render INFO_ONLY=1, b{N} sil.json 기준): {sil: 경로, leaders: [{name, anchor, d_mm(맞춘 뒤 끝–앵커), snapped(6mm 안이면 true)}], label_sil_overlaps: [{label, root, area_mm2, allowed}]} — 사후 ⑰",
        "rules": ["① 인쇄 글 금지 패턴 0회(새 금지어·문장·치수 + 콜로세움 받침 서술 '받침'·'기초 절개'·'받침 앞 변' 0, 네로 거상 받침 문장만 허용)",
                  "② 라벨 배율 1.00·글자면 결정 7 ±0.1(소품 주석 2.6·짝 표지 2.2)·피치 4.15±0.05·슬롯 넘침 ≤ 0.5mm·라벨/길/건물/지시선 2mm 이상·깃대형 수직(x 편차 ≤ 0.1)·끝점 Ø0.9·대상 간격 ≤ 0.5",
                  "③ 패널 본문 ≥ 2.55mm·주석 ≥ 2.05mm", "④ 지시선 수직·±30°(±0.5°)·꺾임 ≤ 1·끝점 Ø0.9±0.05·대상 간격 ≤ 0.5mm·교차 0", "⑤ 길-지면 간격 ≤ 1.6mm(바실리카–R2 포함)", "⑥ S 바깥 길이 비 20.0±0.2",
                  "⑦ 밀도 ≥ 39.3%(전체 무대 173,460mm² 기준, 열린 무대 값 기록)", "⑧ 인물 군 ≥ %d곳·군마다 5~7명·간격 3.5~5mm·키 4.6~5.2" % D.CROWD_MIN,
                  "⑨ 포르투스 입구 18~22mm·섬 양옆 ≥ 4mm·탑–두 팔 끝 ≥ 4mm·운하 2곳 연속", "⑩ 티어 색 사용 0",
                  "⑪ 위계(그린 상자): 6패널 Basic 최소 ≥ Detail 최대·Detail 최소 ≥ Support × 1.1·R·T 0 + 지도(그린 외곽 상자끼리): 히어로 군(hero_group = 건물 ∪ 공사장 ∪ 인물 무리 ∪ 노점 ∪ 네로 받침) ÷ 중앙값 3.2~7.9·≥ 최대 × 1.1·표준 랜드마크 각각 ≥ 4,500·베수비오 최소·콜로세움 건물 실루엣 ≥ 다른 건물 × 1.2",
                  "⑫ 글 블록-상자 테두리 ≥ 3mm",
                  "⑬ 필수 요소 존재(패널 6·L1~L9·네로 거상·R7·다리·표지 A 3·B~D 각 2·숫자 1~4 각 2, 지도 표지 간격 ≥ 2mm)", "⑭ 건물 실루엣 간격 ≥ 2mm(길–지면 접속·다리–강·다리–R7 제외)", "⑮ 운하 사양 끝점 = 그린 끝점 ±0.3mm",
                  "⑯ 인쇄 선 굵기(내부선 0.10~0.20·지시선 0.30·콜아웃 테두리 0.25·Z1 테두리 0.60·P5 계단선 0.35, 가는 보조선 print:false)",
                  "⑰ 정보 층 정합(INFO_ONLY 실행 시: 지시선 끝–앵커 ≤ 0.5mm, 허용쌍 밖 라벨 블록–실루엣 겹침 0. 미실행이면 건너뜀으로 기록)",
                  "⑱ 기준선 8.1 콜로세움 본체(그린 값: 반축·방위·중심·폭 비 0.53·θ 구간 높이·정면 ≤ 17·둘째 고리·나무 바닥·건물 상자)",
                  "⑲ 기준선 8.2 받침 없음 + 사용자 16:13·16:14 둘레(받침 옆면 0·받침/절개 footprint 0·광장·공사장·인물 무리·노점·길 0·네로 받침 있음·LocalBanana 조경 복제 0)",
                  "⑳ D7 연결(영묘 양 끝 보행면 높이 차 0: 다리 북쪽 진입 경사·디딤 2단)",
                  "㉑ P5 계단(채움 0 꺾은선·D15 좌표 ±0.3·굵기 0.35·글과 ≥ 1.5mm)",
                  "보조: 사양 정리(뺀 패널 이름·대기 문구 0, 조명 방향 지정·그림자 예외·제작 단계 면제 문구 0, 콜로세움 받침 서술 0) · frame.panels = L·P2·B·D·S·P5 · weight_order 맨 위 = 8절·0-1 · worker_handoff 4열쇠 + 8절·완료 조건 · Blender 인계 · drawn 계약 형식 · 그린 무대 = STAGE 하나"],
    },
    "verification": {
        "scope": [
            "사전 검사(v2_check.json, 사양 기하): 필수 요소 존재 → 위계(투영 상자끼리: 히어로 군 = 건물 ∪ 공사장 ∪ 인물 무리 ∪ 노점 ∪ 네로 받침·Basic ≥ Detail ≥ Support×1.1·베수비오·랜드마크 하한 4,500·히어로 ÷ 중앙값 3.2~7.9·건물 실루엣 × 1.2) · 패널 수 5~7 · 겹침 · 땅/강/바다 · 길 접촉 ≤ 2.5 · 고리 거리 · 히어로 군 · 밀도 근사 · 압축 지리 · 짝 표지 기록 · 기준선 8.1·8.2·D5·D7(baseline_8, 기록)",
            "사후 검사(post_check.json, 그린 결과): ①~㉑ + 보조. 실패 1건이라도 있으면 make.py 종료 코드 1",
            "자체 시험(v2_check.py --selftest = make.py --selftest): d4 사양(받침·고리 0.74)이면 8.1·8.2 새 검사가 실패, d5 사양이면 통과, LocalBanana 복제 부품 감지, drawn 계약 형식 판정",
        ],
        "not_checked": [
            "라벨 글 블록–강 둑 2mm: drawn.json에 강·바다 다각형이 없어 사후 검사가 보지 못한다(render가 water 다각형을 기록하면 더할 수 있다)",
            "짝 표지 위치 = 사양 mark_pt: 숫자 3·4는 render가 실제 면 위로 ±5·±4mm 맞추므로 위치 일치는 기록만 하고 판정하지 않는다(A는 사후 ⑳이 판정)",
            "형태 사양(하이포게움 동심 벽·칸막이 세부, 수도교 관통 아치, 베수비오 앞 능선 연속 가림·농장–구릉 한 실루엣, P2 스팬 막대 비례)은 그림으로 확인한다(검사 항목 없음)",
            "와이어프레임 밀도: b{N} map.png 무대 [0, 92, 420, 478]에서 땅색 ±6·물색이 아닌 화소(사용자 16:14: Core 건물만)를 통합 담당이 잰다. 203X 건물 실루엣 비율 26~40%",
            "와이어프레임 표현 레이어 L0~L6·디테일 밀도(6×6mm 빈 단색 면 0)는 Blender 패키지 보고(roma_kit.layer_audit)로 본다",
        ],
    },
    "worker_handoff": {
        "map": "우선순위: 기준선 8절(05:27~12:49, 12:49 철회 포함) > 0-1 통합 루프 > 7절. v2_map.py 단일 원본: 지형·테베레강·바다·해안·다리 진입 경사·포르투스 기하·랜드마크 L1~L9(L9 상자 [64.5,291.0,145.7,348.9]·L6 [5.0,372.0,102.0,434.8] 정정)·네로 거상 받침·소품. "
               "콜로세움 본체는 HERO_COLOSSEUM(dict, v2_base.HERO_COLO_D5 형식: center_plan·semi_axes_plan·major_az_deg·wall_profile[[t0,t1,lo,hi,메모]]·second_ring·floor.wood_frac·arena_semi_axes_plan·base_side_mm 0)로, 둘레는 HERO_LANDSCAPE(dict: center_plan·reserve_R_plan·rep_R_plan·boundary_plan 또는 boundary_screen·parts·crowds·base_side_mm 0)로 등록한다. "
               "완료 조건: 사전 baseline_8 실패 0(받침 옆면 0·절개 0·반축·폭 비 0.53·θ 구간 높이·둘째 고리·나무 바닥·둘레 땅 바탕뿐)·LocalBanana 조경 복제 부품 0·사양에 콜로세움 받침 서술 0(네로 받침 제외)",
        "panels": "우선순위: 기준선 8절 > 0-1 > 7절. v2_panels.py 단일 원본: 틀(타이틀·푸터), 패널 rect 6개(L·P2·B·D·S·P5, D15 P5 조판·D16 P2 수치), Detail 상자·글(Z1 Ø60 중심 (275,450)·글 칸·합성 상자 유지, C1·C2·C4), 지시선 꼭짓점(LEADERS: '→ 확대 창 Z1'은 (232.0,396.8) → ↘30° → (272.38,420.11), 굵기 0.30·끝점 Ø0.9), 짝 표지(A 지도 쪽 (233.75,393.77)·숫자 1~4), 라벨 슬롯·본문(LABELS, blender_anchor 열쇠), 바닥 글. "
                  "완료 조건: 사전 baseline_8 D5-1·D5-2 통과·사후 ①(인쇄 글 '기초 절개'·'받침 앞 변' 0)·②③⑪⑫⑬⑳ 통과",
        "render": "우선순위: 기준선 8절 > 0-1 > 7절. render.py: 사양을 읽어 그리기만 한다(사양 값을 덮어쓰지 않는다). 콜로세움은 core_map.hero.colosseum·landscape로 그리고(받침 0), 메텔라 설계 그림은 사양 상자 중심 기준 1.04배(x 420에서 잘림). 벡터 일러스트(AO·조명·그림자 0, ISO_TONE). "
                  "drawn.json은 drawn_contract.schema(목록형)와 새 기록(objects hero·hero_group·sil_mm2, hero.stalls, forms.hero, strokes, p5.stair, crowds height_mm)을 쓴다. INFO_ONLY=1이면 out/info/info_layer.png와 info_check.json(앵커 맞춤 기록)을 쓴다. "
                  "완료 조건: 사후 ①~㉑ + 보조 실패 0(make.py 종료 코드 0)",
        "global": "우선순위: 기준선 8절 > 0-1 > 7절. v2_base.py 공용 상수(d5: HERO_COLO_D5·HERO_LANDSCAPE_D5·LB_REPLICA_KEYS·PERSON_H·Z1_START·R7_LINK_D5·PRINT_LINE_MM·P5_STAIR·BLENDER_ANCHORS·BLENDER_STAGE·HEIGHTS_Z, 순수 기하 도우미)·v2_data.py 모음(hero_model·hero_landscape·hero_building_polys·landscape_width·hero_part_names·blender_anchor_items)·"
                  "v2_check.py 사전 검사(+ baseline_8)와 사후 검사(①~㉑ + 보조)·자체 시험(--selftest)·v2_build.py 조립(colosseum·landscape·blender_handoff·drawn_contract schema)·v2_text.py 원칙·충돌 글·v2_svg.py 내부 골격 미리보기·make.py 실행기(--info 정보 층 선택 실행, --selftest). "
                  "완료 조건: 자체 시험 통과(d4 → 8.1·8.2 실패, d5 → 통과)·사양 정리 보조 통과·make.py 종료 코드는 다른 패키지 결과를 그대로 보고한다",
    },
}


if HLS.get("crowds"):
    spec["core_map"]["hero"]["crowds"] = _jsonable(HLS["crowds"])      # render는 sget(HERO, "crowds")로 읽는다
spec["frame"]["print_rules"]["forbidden_base"] = {"pattern": D.PRINT_FORBIDDEN_BASE, "allowed": D.PRINT_BASE_ALLOWED,
                                                  "rule": "인쇄 글에 콜로세움 받침 서술 0('받침'·'기초 절개'·'받침 앞 변'). 네로 거상 받침 문장 '콘크리트(벽돌 마감) 받침 위의 / 네로의 청동 거상(추정)'만 허용(사후 ①)"}
spec["meta"]["spec_hygiene_d5"] = "사양 정리: 조명 방향 지정·그림자 예외·제작 단계 면제 문구 0(패턴은 v2_base.SPEC_FORBIDDEN_D5, 사후 보조가 판정)"


def _hygiene(o, path=()):
    """사양 정리: '위치도'·'연대기'는 사용자 원문 인용 구역(meta.user_review·meta.user_selection)에만, '보류'·'선택 대기'는 원문(words)에만. 인쇄 금지 패턴 정의는 뺀다"""
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _hygiene(v, path + (str(k),))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _hygiene(v, path + (str(i),))
    elif isinstance(o, str):
        quote = path[:2] in (("meta", "user_review"), ("meta", "user_selection"))
        if path[:2] == ("frame", "print_rules") and path[2:3] in (("forbidden_pattern",), ("forbidden_pattern_ci",), ("forbidden_sentences",)):
            return                                        # 인쇄 금지 패턴 정의(낱말 목록 자체)
        if ("위치도" in o or "연대기" in o) and not quote:
            yield "/".join(path) + " (위치도·연대기)"
        if ("보류" in o or "선택 대기" in o) and not (quote and path[2:3] == ("words",)):
            yield "/".join(path) + " (보류·선택 대기)"


bad = list(_hygiene(spec))
# 19:3x 사용자 지시(지도 창·투영·Core 위계·Detail·지형): spec에 확정해 적는다
import math as _m
_C30 = _m.sqrt(3) / 2.0
_win = [0.0, 92.0, 420.0, 478.0]
spec["meta"]["projection"] = {
    "window_rect_mm": _win, "bleed": "좌우 블리드(x 0·420에서 그림이 잘림)", "angle_deg": 30.0,
    "to_screen": "x = cos30·(X − Y), y = 0.5·(X + Y) − Z   (cos30 = 0.8660254)",
    "to_plan": "X = x/(2·cos30) + y, Y = y − x/(2·cos30)   (Z = 0)",
    "window_corners_plan_trapezoid": [[round(v, 2) for v in D.to_plan(x, y)] for x, y in ((0, 92), (420, 92), (420, 478), (0, 478))],
    "note": "화면 창의 네 모서리를 바닥(Z 0)으로 되돌린 평면 사변형(회전 사각형). 높이 h인 물체의 윗면은 화면에서 h만큼 위로 올라간다.",
}
spec["frame"].setdefault("stage", {})["window_rect_mm"] = _win
_rank = [("콜로세움", "HERO"), ("판테온", "L1"), ("카라칼라 욕장", "L3"), ("트라야누스 시장", "L2"), ("카이킬리아 메텔라 무덤", "L5"), ("포르투스 항", "L6"),
         ("막센티우스 바실리카", "L7"), ("하드리아누스 영묘·폰스 아일리우스", "L8"), ("마르켈루스 극장", "L9"), ("수도교", "L4")]
spec["hierarchy"]["core_rank_order"] = [{"rank": i + 1, "name": n, "id": k} for i, (n, k) in enumerate(_rank)]
spec["core_map"]["terrain"] = [
    {"name": "알바노 구릉(산맥)", "kind": "terrain", "screen_anchor": [396.0, 462.0], "box": None, "note": "긴 축 화면 가로, 받침 34×높이 26 mm급, 렌더가 drawn.terrain에 상자를 적는다"},
    {"name": "베수비오(화산)", "kind": "terrain", "screen_anchor": [398.0, 420.0], "box": None, "note": "가장 작은 지형, 받침 30×높이 24 mm급"},
]
try:
    import v2_windows as _VW
    spec["core_map"]["detail_windows"] = [{"key": w_["key"], "rank": w_["rank"], "center": list(w_["c"]), "diameter": w_["d"], "target": list(w_["t"]),
                                           "title": w_["title"], "lines": w_["lines"], "chip": w_.get("chip"), "fig": w_["fig"]} for w_ in _VW.DETAIL_WINDOWS]
except Exception:
    pass
json.dump(spec, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if bad:
    print("경고: 사양 정리 위반(사용자 원문 인용 제외):", bad[:10])
print("사양 JSON 저장:", sys.argv[2], "· 패널", [p["id"] for p in panels], "· 무대", D.STAGE_AREA_EXT, "· 랜드마크", len(D.LANDMARKS), "· Basic 최소", H["basic_min"], "· Detail 최대", H["detail_max"],
      "· 필수 요소", "모두 있음" if REQ.get("ok") else ("없음 " + " · ".join(REQ.get("missing", []))))
