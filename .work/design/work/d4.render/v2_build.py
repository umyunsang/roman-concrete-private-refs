# -*- coding: utf-8 -*-
"""배치 사양 JSON 조립: 기하(v2_data) + 검사(v2_check.json) + 원칙·충돌(v2_text). 담당: global
새 필드(map·panels가 더한 열쇠)는 그대로 spec.json에 넘긴다. 사용자 검토(2026-10-19 02:24): R·T 패널은 지면에서 뺀다.
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


def plan_pts_screen(plan):
    return [R2(D.to_screen(*p)) for p in plan]


def area(b):
    return round((b[2] - b[0]) * (b[3] - b[1]))


def extra(x, known):
    """사양 원본(map·panels)이 더한 새 열쇠를 그대로 넘긴다"""
    return {k: v for k, v in x.items() if k not in known}


oct_ = D.hero_oct()
hb = H["hero_box"]
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

size_table = [{"tier": "Core", "name": "지도 무대 전체(로마 건축물 지도, STAGE ∪ STAGE_EXT)", "box": list(D.STAGE), "ext_rects": D.STAGE_EXT, "area_mm2": D.STAGE_AREA_EXT}]
size_table.append({"tier": "Core(히어로)", "name": "콜로세움", "box": hb, "area_mm2": H["hero_area"]})
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


size_order = ("Core(무대 %smm² = STAGE ∪ STAGE_EXT, 콜로세움 %smm² = 최대 단일 오브젝트) > Basic 각 요소(%s, 최소 %s) ≥ Detail 각 요소(%s, 최대 %s, 최소 %s) > Support(%s). "
              "비: Basic 최소 ÷ Detail 최대 = %.2f, Detail 최소 ÷ Support = %.2f. 베수비오(%smm²)는 랜드마크급 지도 요소 가운데 최소" %
              (format(int(D.STAGE_AREA_EXT), ","), format(H["hero_area"], ","), tier_line("Basic"), H["basic_min"][0].split(" ")[0], tier_line("Detail"),
               H["detail_max"][0].split(" ")[0], H["detail_min"][0].split(" ")[0], tier_line("Support"),
               H["ratio_basicmin_over_detailmax"], H["ratio_detailmin_over_support"], format(H["vesuvius_area"], ",")))

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
spec = {
    "meta": {
        "title": "로마 콘크리트 A2 세로 포스터 — 203X 도시 인포그래픽 '로마 편' 배치 사양(새 정보 위계 + 사용자 검토 2026-10-19 02:24)",
        "version": "d3 (2026-10-19, 사용자 검토 02:24 반영)",
        "user_review": {
            "date": "2026-10-19 02:24",
            "words": USER_REVIEW_WORDS,
            "precedence": "기준선 1~5절보다 우선(설계-결정-기준.md 6절). 판정 순서: 사용자 검토 > 기준선 1~5절 > 레퍼런스 실측 > Codex 비평",
            "applied": [
                "상단 오른쪽 R 패널(302~402×20~92, 연한 판 포함)을 지면에서 뺐다. 자리는 지도 무대로 돌려줬다: (298,20)~(420,92) = '가장 먼 곳'",
                "하단 띠 오른쪽 T 패널(316~402×505~565)을 지면에서 뺐다. 자리는 지도 무대로 돌려줬다: (312,505)~(420,568) = 남동 교외 포도밭(고요한 영역)",
                "인쇄 지면의 내부 표기를 모두 뺐다(작업 이름·티어 이름·티어 색 범례·티어 색 모서리·크기 꼬리표·면적·검사 수치·히어로 군 점선 윤곽·투영 상자 모서리·가장자리 눈금·설계 주석·레퍼런스 근거 메모). 이 정보는 spec.json과 보고서에만 둔다",
                "지면에 '자리 예약' 같은 글을 쓰지 않는다. 대체 Basic 정보와 추가 로마 건축물은 다음 회차에 반영한다",
            ],
        },
        "hierarchy_change": {
            "date": "2026-10-18 23:43",
            "user_words": "정보 위계를 변경하자. 도시 인포그래픽처럼 로마 건축물들이 core 정보이고, 로마콘크리트 제작과정은 basic 정보와 detail 정보로 서사하고 support로 현대 콘크리트의 유통기한은 100년, 로마콘크리트는 2000년 으로 서사하는 방향으로 정보위계를 변경하고 변경한 위계에 맞춰서 다시 설계작업 진행해",
            "precedence": "이 위계 변경이 공통 자료·지시 A~J·가중치 순서·이전 종합의 위계 서술보다 우선한다(단, 사용자 검토 2026-10-19 02:24가 그보다 우선)",
        },
        "units": "A2 mm, 포스터 0~420 × 0~594, 화면 좌표(x 오른쪽, y 아래)",
        "projection": "진짜 등각(지면 축 ±30°, 수직 90°, 카메라 고도 35.264°). 평면 +X → 화면 ↘(cos30, 0.5), +Y → 화면 ↙(−cos30, 0.5), 평면 원점 = 화면 (0,0). 화면 ↘ 직선 y = tan30·x + c 는 평면 Y = c, ↗ 직선 y = −tan30·x + d 는 평면 X = d (v16 common.Iso와 같은 규약)",
        "light": "왼쪽 위 하나(윗면 > 왼면 > 오른면)",
        "weight_order": ["0 사용자 검토(2026-10-19 02:24, 기준선 1~5절보다 우선)", "1 정보 위계 변경(2026-10-18 23:43)", "2 도시 인포그래픽 레퍼런스 정밀분석", "3 203X 베이징·신문 정밀분석", "4 사용자 확정 결정(바꿀 수 없음)", "5 지도교수 비평의 원칙(새 위계로 읽음)", "6 손 스케치·구상도 v3(참고만)", "7 Codex 비평"],
        "output": {
            "final": "420×594mm · 300ppi = 4961×7016px(반올림)",
            "final_px": D.OUTPUT["final"]["px"], "final_ppi": D.OUTPUT["final"]["ppi"],
            "review": "검토용 3px/mm = 1260×1782px(지금 diagram.png, 실물 크기에서 76.2ppi)",
            "review_px": D.OUTPUT["review"]["px"],
            "asset_native_width_rule": "자산 고유 폭 = 배치 폭 ÷ 25.4 × 300",
            "asset_native_width_px": {k: {"배치 폭 mm": v[0], "고유 폭 px": v[1]} for k, v in asset_widths.items()},
            "line_weights_mm": D.OUTPUT["line_mm"],
            "final_check": "최종 출력 확인 = render 출력 + global 사후 검사(v2_check.py --post out/drawn.json out/post_check.json). 실패 1건이라도 있으면 make.py 종료 코드 1",
        },
        "sources": {
            "baseline": "/Users/um-yunsang/roman-concrete-private-refs/.work/design/설계-결정-기준.md",
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
        "rule_of_thumb": "좌표는 배치 골격이다. 워커는 상자 안에서 형태를 다듬되, 투영 상자 크기·티어 순서·맞닿음·±30° 규칙은 바꾸지 않는다. 투영 크기는 레이어 알파 외곽 상자로 잰다(그림자·빛 번짐은 shadow 레이어 또는 알파 40 이하). render는 사양 값을 덮어쓰지 않는다",
    },
    "hierarchy": {
        "definition": {
            "Core": "로마 건축물 지도(도시 인포그래픽의 랜드마크 지도): 콜로세움(히어로·최대 단일 오브젝트) + 판테온·트라야누스 시장·카라칼라 욕장(절개)·수도교·카이킬리아 메텔라 무덤·포르투스 + 지도 배경 베수비오 + 테베레강·바다·길·지형·소품. 무대 = STAGE ∪ STAGE_EXT",
            "Basic": "L 로마 콘크리트란?(정의 + 재료), B 제작 과정 6단계(재료 준비 → 마른 혼합 → 물 붓기 → 뜨거운 혼합 → 다져 넣기 → 굳기·석회 알갱이). 화면 평행 패널(도시편 문법), B는 지도 공사장과 지시선 1개로 잇는다. 옛 R·T 자리는 사용자 검토(2026-10-19 02:24)로 지도 무대에 돌려줬다(대체 Basic은 다음 회차)",
            "Detail": "D 석회 알갱이·자가치유·뜨거운 혼합 패널 + 지도 위 확대 창 Z1(원 Ø64 + 글 칸, 위계는 합성 상자로 잰다) + 콜아웃 C1(판테온 돔의 가벼운 골재)·C2(포르투스 방파제와 바닷물)·C4(메텔라 드럼 재결속)",
            "Support": "S 현대 콘크리트 약 100년 vs 로마 콘크리트 2,000년 비교(가장 작은 위계)",
        },
        "projected_size_order": size_order,
        "size_table": size_table,
        "checks": H["checks"],
        "ratios": {"basic_min_over_detail_max": H["ratio_basicmin_over_detailmax"], "detail_min_over_support": H["ratio_detailmin_over_support"],
                   "hero_over_landmark_median": H["hero_over_landmark_median"], "hero_pct_stage": round(100 * H["hero_area"] / D.STAGE_AREA_EXT, 1)},
        "basic_min": H["basic_min"], "detail_max": H["detail_max"], "detail_min": H["detail_min"], "support": H["support"],
        "z1_box_source": H.get("z1_box_source"),
        "panel_count_rule": H.get("panel_count_rule"),
    },
    "frame": {
        "stage": {"rect": list(D.STAGE), "area_mm2": D.STAGE_AREA, "ext_rects": D.STAGE_EXT, "area_mm2_ext": D.STAGE_AREA_EXT, "rects": D.STAGE_RECTS,
                  "note": "지도 무대 = 기본 (0,92)~(420,505) 173,460mm² ∪ 위 확장 (298,20)~(420,92) 8,784mm²(위 변 y 20 = L 윗선, 타이틀 오른쪽 변 293.5와 4.5mm, 오른쪽 블리드, 위는 닫음) ∪ 아래 확장 (312,505)~(420,568) 6,804mm²(D 오른쪽 변 308과 4mm, 아래 변 = 푸터 윗선 568, 오른쪽 블리드) = 189,048mm². render는 ext_rects가 없으면 v2_base.STAGE_EXT 값을 쓴다"},
        "title": {"rect": D.TITLE["rect"], "name": D.TITLE["name"], "width_pct": 39.8,
                  "note": "주제 건축 정면 입면 액자(베이징 궁궐 문·도쿄 도리이·베를린 브란덴부르크 문·자금성 지붕 계열). 인쇄 글은 영문 시리즈 띠 'CITY LANDMARK INFOGRAPHICS · ROMA', 'ROMAN CONCRETE', 국문 부제 '로마 콘크리트', '로마 건축물로 읽는 로마 콘크리트'뿐이다(타이틀 안 치수 메모·부제의 시리즈 설명 0). 카라칼라 욕장 위 끝(y 94)이 아래 변에 2mm로 다가간다(도쿄 0.8mm 접촉 선례)",
                  "print_texts": ["CITY LANDMARK INFOGRAPHICS · ROMA", "ROMAN CONCRETE", "로마 콘크리트", "로마 건축물로 읽는 로마 콘크리트"]},
        "panels": panels,
        "panel_rules": [
            "상자·배경판 없이 바탕 위에 조판한다(베이징·도쿄·홍콩). 연한 판 예외는 없다",
            "머리글: 영문 초압축 대문자 7.4mm + 국문 3.6~3.8mm 윗선 정렬(S는 5.0·2.8), 강조색 폼페이 레드 한 색",
            "L 윗선 y 20, 좌측 정렬선 x 18, 하단 띠 윗선 y 505(B·D 같은 줄), S는 지도 모서리 패널(윗선 y 466, 오른쪽 정렬선 x 402)",
            "인쇄 지면에 티어 이름·티어 색·치수·면적·검사·설계 주석 0(사양·보고서에만). 티어 배지·범례·모서리 표시도 두지 않는다(203X 문법). 티어는 크기·자리로만 읽힌다",
            "패널 수 5~7개 규칙은 이번 회차 보류(사용자 검토로 L·B·D·S 4개). 대체 Basic을 고를 때 되살린다",
        ],
        "print_rules": {
            "forbidden_pattern": D.PRINT_FORBIDDEN,
            "forbidden_pattern_ci": D.PRINT_FORBIDDEN_CI,
            "allowed": "m·km 단위와 '모식'(과학 표기), '※ … 미확인', 연구 연도",
            "reader_elements_kept": ["영문 시리즈 띠 'CITY LANDMARK INFOGRAPHICS · ROMA'", "'ROMAN CONCRETE'", "'로마 건축물로 읽는 로마 콘크리트'", "과학 표기('모식', '※ … 미확인', 연구 연도)"],
            "removed_from_print": ["R 패널 302~402×20~92 전부(연한 판 포함)", "T 패널 316~402×505~565 전부", "타이틀 안 치수 메모", "국문 부제의 시리즈 설명", "패널 점선 틀·티어 꼬리표 6개·지도 무대 꼬리표",
                                   "랜드마크 6·베수비오·히어로의 초록 모서리와 크기 꼬리표, 히어로 꼬리표·투영 상자 꼬리표", "Z1·C1·C2·C4 크기 꼬리표", "Basic 지시선 꼬리표", "히어로 군 점선 윤곽과 꼬리표", "타이틀–욕장 2mm 선",
                                   "가장자리 눈금과 y 92·y 505 표시", "푸터의 점선 틀·작업 이름·작업 정보 줄·티어 색 범례·위계/밀도 수치 2줄·푸터 안내 글", "B 패널의 ⑥ → 지도 공사장 지시선 설명 글"],
            "colors": "지시선·끝점·짝 표지 A~D·Z1 테두리(0.6mm)·콜아웃 테두리(0.25mm)·콜아웃 제목 = 정보 잉크 (58,42,28) 한 색. 폼페이 레드는 타이틀·패널 머리글·단계 번호에만. 티어 색 인쇄 사용 0, 라벨 크림 바탕판 0(말풍선 태그 2개만 예외)",
        },
        "footer": D.FOOTER,
        "footer_rule": "푸터에는 독자용 요소(로고·크레딧·QR)만 둔다. 작업 정보·범례·검사 수치·안내 글 0",
        "panel_area_pct_poster": chk["density_estimate"]["panel_area_pct_poster"],
        "panel_area_mm2": chk["density_estimate"].get("panel_area_mm2"),
    },
    "core_map": {
        "hero": {
            "name": "콜로세움(Amphitheatrum Flavium) — 히어로·최대 단일 오브젝트",
            "center_screen": list(D.HERO_C), "center_plan": R1(D.HERO_C_PLAN), "oct_R_plan": D.HERO_R, "base_side_T": D.HERO_SIDE, "ring_ratio": D.HERO_RING,
            "base_oct_screen": [R1(p) for p in oct_], "walls": D.HERO_WALLS,
            "projected_box": hb, "projected_wh": H["hero_wh"], "projected_area_mm2": H["hero_area"],
            "cutaway": D.HERO_CUTAWAY, "worksite": D.WORKSITE,
            "interior": getattr(D, "HERO_INTERIOR", None),
            "form": [
                "LocalBanana 참조 디오라마 원래 방향: 4층 외벽 조각(높이 60mm)은 뒤-왼쪽(평면 방위 150°~235°), 뒤-오른쪽 고리 2층(28mm), 앞쪽은 무너져(12mm) 관람석 층·하이포게움(왼쪽 반)·복원 나무 바닥(오른쪽 반)이 보인다",
                "받침: strata_slab 지층 3겹 이상(D), 앞 세 변에만 옆면 7mm, 지면 높이에 묻는다(떠 있는 섬처럼 보이지 않게, G)",
                "받침 앞 변(화면 아래 평평한 변) x 208~292를 절개해 콘크리트 기초 고리 단면을 보인다. 왼쪽 발치에 공사장(나무 거푸집·다짐 막대 일꾼 2·반죽 통·재료 더미), 오른쪽 x 275에서 확대 창 Z1 지시선이 나간다",
                "받침 광장 소품: 사이프러스·올리브·기둥 폐허·노점·암포라·인물. 받침 앞 광장 인물 군 3곳(중심 ≈ (190,357)·(236,371)·(306,360), 각 약 20×10mm, 5~7명, 키 5mm, 이웃 발점 간격 3.5~5mm, 노점·암포라·폐허 둘레)",
                "내부 형태(interior, 원본 map HERO_INTERIOR): 하이포게움 노출 반쪽 바닥은 나무 바닥보다 화면 수직 5mm 아래, 통로 벽 1.5mm, 장축 중심 통로 1 + 평행 통로 2(간격 6mm) + 가로벽 7(간격 5mm); 관람석 4층 구분·방사 계단 12개(30°마다, 폭 2.5mm)·계단 자리 출입구; 4층 외벽 조각은 아치 안쪽 면 1.5mm + 바깥 아케이드·안쪽 회랑 2 깊이 층(간격 3mm)",
                "높이 과장은 1.1~1.2배까지(피라미드 1.22배 선례), 라벨 수치는 실제값(약 188×156 m, 높이 약 48 m)",
            ],
            "gates": {"아피아 가도 문(뒤-오른쪽 변)": R1(D.to_screen(*D.road_plan(D.ROADS[0])[0])), "하역장 길 문(앞-왼쪽 변)": R1(D.to_screen(*D.road_plan(D.ROADS[3])[0]))},
        },
        "landmarks": landmarks,
        "background": background,
        "zones": {
            "도심": "콜로세움 + 테베레 ↘ 팔 + 하역장·석회 가마·수레·공사장(지도 가운데)",
            "시내": "트라야누스 시장(왼쪽 위) · 판테온(왼쪽 가운데) · 카라칼라 욕장(뒤쪽 가운데-오른쪽)",
            "남동 교외": "수도교 아치 열(오른쪽 위) · 아피아 가도 · 카이킬리아 메텔라 무덤(오른쪽 가운데) · 포도밭·교외 빌라(오른쪽 아래, 옛 T 자리 (312,505)~(420,568)까지 이어지는 고요한 영역, 글·틀 0)",
            "서남서 해안": "테베레 하구 · 포르투스(육각 내항 육지 + 외항·등대 바다) · 오스티아 · 바다(왼쪽 아래 모서리)",
            "가장 먼 곳": "알바노 구릉 띠(로마 건물의 화산재, 지형 결·라벨만) + 베수비오(오른쪽 위 모서리에서 옛 R 자리 (298,20)~(420,92)까지: 베수비오 (330,30)~(388,70)·포도밭 농장 (336,54)~(378,76)·알바노 구릉 띠 (300,64)~(420,160), 나머지는 먼 밭·구릉 결만, 건물·글·틀 0)",
        },
        "river": {
            "name": "테베레강(Tiberis)",
            "entry_screen": list(D.RIVER_ENTRY_SCREEN), "bend_screen": R1(D.RIVER_BEND_SCREEN), "mouth_screen": R1(D.RIVER_MOUTH_SCREEN),
            "plan": {"arm1": f"평면 Y = {D.RIVER_Y} (↘, 왼쪽 변 → 굽이)", "arm2": f"평면 X = {D.RIVER_XB} (↙, 굽이 → 해안 Y {D.COAST_Y})", "fillet_R": D.RIVER_FILLET},
            "width_screen_perp_mm": {"↘ 팔": D.RIVER_W1, "↙ 팔(하구 쪽)": D.RIVER_W2},
            "polygon_screen": river_poly,
            "rules": ["±30°만(수직 구간 0), 꺾임은 평면 직각 1회(둥근 굽이)", "콜로세움 받침 앞-왼쪽 변과 평행하게 41mm(평면 ΔY) 떨어져 흐른다: 그 사이 띠가 하역장·석회 가마·수레 자리", "강은 콜로세움 군의 가장자리만 지나고 가르지 않는다", "물 면 facet_fill + 둑 contact_ao(D)", "하구는 바다로 흘러들고(사용자 B 원래 결정·트라바키), 하구 오른쪽 둑에 포르투스, 왼쪽 둑에 오스티아"],
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
            "canal_polys_screen": ({k: [R2(p) for p in v] for k, v in D.portus_canal_polys().items()} if hasattr(D, "portus_canal_polys") else None),
            "rules": ["원본은 map 사양, 그림은 render", "외항 방파제 평면 반지름 18.4~21.0, 팔 A 263°→123°·팔 B 277°→417°(=57°), 마지막 조각을 끝각에서 정확히 자른다 → 투영 입구 폭 ≈ 19.8mm(허용 18~22)",
                      "등대섬 평면 각 90°·반지름 24, 화면 기저 ≈ (9.9,431.3). 섬과 두 팔 끝 사이에 보이는 물 ≥ 4mm",
                      "운하 2개 평면 X 435.5~438.5(화면 폭 2.6mm): 강 쪽 Y 322.84 → 338.6, 외항 쪽 Y 368.6 → 384.0. 육각 내항 수면(반지름 15.2) 안쪽과 외항 수면 안쪽까지 잇고 포장·안벽에 폭 3mm 개구부", "외항 열주는 팔 B의 12~54°에만"],
            "land_sea_split_mm2": chk["portus_land_sea_split_mm2"],
            "polygons_screen": portus_polys,
        },
        "roads": roads,
        "aqueduct": {"ground_line_screen": [R1(D.to_screen(*D.AQUEDUCT_PLAN[0])), R1(D.to_screen(*D.AQUEDUCT_PLAN[1]))], "arch_height_mm": D.AQUEDUCT_H,
                     "source": "map v2_map.AQUEDUCT_PLAN(원본). 읽는 쪽: global(검사·조립), render(아치 열 그리기), panels(수도교 라벨 슬롯·지시선 ↑)",
                     "note": "오른쪽 변 밖(남동 시골)에서 ↖로 들어와 카라칼라 욕장 오른쪽 변 (336,160)에 닿는다(아쿠아 마르키아의 지선 아쿠아 안토니니아나 → 욕장 저수조 64개[S47][S49]). 2단 아치, 교각 약 8mm 간격, 지면보다 채도를 2배 이상 높인 벽돌·석재 색(지스몬디 2.1~4.6배)"},
        "road_rules": ["±30° 띠만, 꺾임은 평면 직각", "폭은 화면 수직 폭. 주축 16mm + 흰 중앙선 1.6mm(도쿄·베를린), 보조 8~10mm", "길과 실제 지면 다각형의 간격 ≤ 1.6mm(판테온·욕장·메텔라·시장·콜로세움, 사후 검사 ⑤)",
                       "길 연장(R1 끝 +14, R2·R3 시작 +30, R3 끝 +4.6mm)은 map이 사양 좌표(plan_pts)에 넣는다. render는 길 좌표를 하드코딩하지 않는다", "모든 랜드마크가 길·강·해안·수도교 중 하나에 2.5mm 안으로 닿는다(도쿄 19/23)"],
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
                "슬롯은 화면 상자(허용 영역)이고, 실제 글 블록 평행사변형은 길·건물·다른 라벨·지시선과 2mm 이상 띄운다. 브래킷 수직선은 글 블록 밖 1.5~4mm",
                "방향: 콜로세움 ↘·판테온 ↗·트라야누스 시장 ↗·카라칼라 욕장 ↗·수도교 ↗·메텔라 ↘·포르투스 ↘·베수비오 ↗(깃대형)·화산재 운반선 ↘(규선 연장형). 바닥 글은 그 선형 요소와 평행",
                "형식: 랜드마크 = 브래킷형, 탈것·먼 소품 = 깃대형, 본문 없는 작은 시설 = 말풍선 태그(재료 시설 색), 히어로 받침 안 소품 = 지시선 없이 인접(상하이)",
                "잉크: 지도 라벨은 중립 잉크 한 색(땅 위 짙은 갈색, 물 위 밝은 크림 또는 톤온톤). 강조색은 쓰지 않는다",
                "방위표·축척·범례는 지도에 두지 않는다(베이징·청와대). 실제 방위·거리는 베수비오 라벨의 짧은 거리 표기(로마에서 남동쪽 약 200 km)만 둔다",
            ],
        },
    },
    "basic": {
        "panels": [p for p in panels if p["tier"] == "Basic"],
        "process_representation": {
            "decision": "패널 안 단계 도식(B) + 지도 위 공사장 장면(Core 소품) + 지시선 1개",
            "panel": "B 196×60mm: 6칸 등각 소형 장면, 칸 사이 바닥 화살표(신문), 아래 시간 화살표(피라미드), 단계 번호 원(폼페이 레드). 단계명 3.0mm, 설명 2.6mm(피치 3.9), 시간 화살표 글 2.1mm",
            "map_scene": "콜로세움 받침 앞 변 왼쪽 발치의 공사장(기초 절개 + 거푸집 + 다짐) + 테베레 하역장·석회 가마·수레·바지선(① 재료 준비와 같은 그림)",
            "link": D.LEADERS[0],
            "evidence": "피라미드 CHANGE OF THE FORM 196×50mm(끝 아이콘이 히어로 꼭짓점 15mm 옆), 런던 BUS LINE 9(지도 위 버스 → 패널 제목 지시선), 신문 바닥 화살표, 자금성 ROOF BUILDING(패널 안 등각 아이콘)",
        },
    },
    "detail": {
        "panel": [p for p in panels if p["tier"] == "Detail"][0],
        "map_elements": details,
        "leaders": D.LEADERS[1:],
        "rules": [
            "지시선은 수직·±30°, 꺾임 ≤ 1, 끝점 지름 0.9mm, 굵기 0.30mm, 정보 잉크 한 색, 첫 점 = 지도 쪽. 화살촉은 ⑥ 공사장 지시선의 패널 쪽 끝에만 작게",
            "짝 표지: 콜로세움 절개·Z1·D = 'A', 판테온·C1 = 'B', 포르투스·C2 = 'C', 메텔라·C4 = 'D'(자금성 A·B·C 깃발 짝 문법). 시작점 옆 3~4mm",
            "지시선끼리, 지시선과 라벨의 교차는 0이다(길 위 통과는 허용)",
            "Z1 위계는 원(Ø64)과 글 칸을 합친 합성 상자로 잰다. Basic 최소(L)보다 작게 유지한다",
            "Detail 최소(콜아웃)는 Support(2,100mm²)의 1.1배 이상을 유지한다. 콜아웃을 줄이면 S도 같이 줄인다",
            "글과 상자 테두리는 3mm 이상 띄운다. Z1 테두리 0.6mm, 콜아웃 테두리 0.25mm(정보 잉크)",
        ],
    },
    "support": {
        "panel": [p for p in panels if p["tier"] == "Support"][0],
        "rules": ["포스터에서 가장 작은 정보 요소(2,100mm²)", "막대 2개는 콘크리트 시험체 모양: 높이 4.0mm, 끝 타원 반폭 0.6mm, 같은 왼끝 x 334.4, 바깥 끝 x 337.4(현대)·x 394.4(로마) → 바깥 길이 3.0 : 60.0 = 1:20, 격자선 없음(신문 TOP 6)",
                  "'로마 콘크리트 2,000년+'는 막대 안에 쓴다. 각주는 2.1mm 두 줄: 강도가 아니라 수명(압축 강도는 현대 콘크리트가 높다[S4])", "지도 모서리 패널: 오른쪽 아래 포도밭 위 고요한 영역"],
    },
    "measurements": {
        "hero_cluster": chk["hero_cluster"], "core_group_city": chk["core_group_city"],
        "density_estimate": chk["density_estimate"], "ring_distance_mm": chk["ring_distance_mm"], "ring_distance_background_mm": chk.get("ring_distance_background_mm"),
        "ring_range_median": chk["ring_range_median"], "left_right": chk["left_right"],
        "contact_distance_mm": chk["contact_distance_mm"], "geo": chk["geo"], "overlaps_not_allowed": chk["overlaps_not_allowed"],
        "slot_overlaps_allowed": chk.get("slot_overlaps_allowed"),
        "land_in_sea": chk["land_in_sea"], "land_in_river": chk["land_in_river"],
        "check_warnings": chk.get("warnings", []),
    },
    "accuracy_rules": [
        "육상 건물(콜로세움 등)은 민물, 바닷물은 항구 구조물에만[S1][S4][S12]",
        "콘크리트는 거푸집에 '다져 넣는다'. '타설'·'붓기'를 쓰지 않는다[S4]",
        "화산재 산지: 바다 공사 = 나폴리만 포추올리 일대(캄피 플레그레이), 로마 시내 건물 = 알바노 구릉 붉은 화산재. 둘 다 핀·라벨로만. '포졸라나 = 베수비오 화산재'는 쓰지 않는다[S4][S6][S7]",
        "베수비오 79년 이전 모습: 넓은 봉우리 하나·잿빛 평평한 정상·포도밭 비탈, 연기 없음, 분화는 '79년'만[S3][S24][S30]. 라벨 본문은 '79년 분화' · '로마에서 남동쪽' · '약 200 km'(짧은 거리 표기)",
        "카라칼라 욕장: 본문 4줄 '겉은 벽돌, 속은 콘크리트' · '돔 위쪽엔 가벼운 경석' · '열탕실 돔 경간 약 36 m' · '(오큘러스·코퍼는 복원 추정)'. 오큘러스·코퍼는 반드시 '복원 추정'으로 쓰고(미확인 목록 5.2), 빛은 큰 창 중심, 코퍼는 얕은 격자로 판테온과 구분[S47][S48][S49]",
        "수도교: 영문 'AQUEDUCT', 국문 '수도교', 위첨자 'Aqua Antoniniana'. 본문 '수로 안은 방수 모르타르' · '아쿠아 마르키아의 지선이' · '욕장 저수조 64개에 물을 댐'(조사 보고서 192행 [S47][S49]). 아쿠아 마르키아 → 안토니니아나 지선 관계로만 쓰고, 클라우디아 이름·보수 구간 문장·실측 좌표는 지면과 사양에 쓰지 않는다. 퐁 뒤 가르는 쓰지 않는다",
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
        "path": "out/drawn.json(render가 쓴다) → global 사후 검사 v2_check.py --post out/drawn.json out/post_check.json",
        "fields": {
            "texts": "[{text, layer(층), role(label_en·label_ko·label_sup·label_body·tag·head_en·head_ko·step·subtitle·body·note 등), font, em, face(글자면 mm), bbox 또는 poly, pitch(여러 줄일 때), panel(속한 상자 id)}]",
            "labels": "[{name(슬롯 이름), kind(브래킷·깃대형·태그), poly(실제 글 블록 평행사변형), dir(↗·↘), scale, slot([x0,y0,x1,y1]), faces{en,ko,sup,body}, pitch, leader{pts, dot_d, target, gap}, clearance{building(알파 ≥128 건물과의 최소 간격 mm)}}]",
            "leaders": "[{name(사양 지시선 이름), pts, dot_d, target, gap(대상 면과의 간격 mm)}]",
            "footprints": "{이름: 다각형 또는 다각형 목록} — 판테온 광장·돔·드럼, 욕장 지면, 시장 지면, 메텔라 대지·드럼, 공사장 받침·거푸집 앞면, 콜로세움 받침, 포르투스, 선체",
            "roads": "{id: 다각형}(실제로 그린 길 띠)",
            "boxes": "[{id(L·B·D·S·Z1·Z1 글 칸·Z1 합성·C1·C2·C4), tier, box 또는 circle{c,d}, border(테두리를 그렸는가), kind}]",
            "s_bars": "[{name(현대·로마), x0, x1(끝 타원 포함 바깥 끝), h}]",
            "density": "{pct, num_mm2, den_mm2} — 알파 ≥128 합집합 ÷ (무대 189,048 − 패널·Detail 덮는 면적)",
            "crowds": "[{name, center, feet[[x,y]...]}]",
            "portus": "{entrance_w, island_water[왼, 오른], canals[{name, continuous, opening_w}]}",
            "tier_color_uses": "정수(티어 색으로 칠한 인쇄 요소 수, 0이어야 한다)",
            "objects": "(선택) {id: 그린 외곽 상자} — hero·L1~L6·V",
        },
        "rules": ["① 인쇄 글 금지 패턴 0회", "② 라벨 배율 1.00·글자면 결정 7 ±0.1·피치 4.15±0.05·슬롯 넘침 ≤ 0.5mm·라벨/길/건물/지시선 2mm 이상", "③ 패널 본문 ≥ 2.55mm·주석 ≥ 2.05mm",
                  "④ 지시선 수직·±30°(±0.5°)·꺾임 ≤ 1·끝점 Ø0.9±0.05·대상 간격 ≤ 0.5mm·교차 0", "⑤ 길-지면 간격 ≤ 1.6mm", "⑥ S 바깥 길이 비 20.0±0.2", "⑦ 밀도 ≥ 39.3%", "⑧ 인물 군 3곳·간격 3.5~5mm",
                  "⑨ 포르투스 입구 18~22mm·섬 양옆 ≥ 4mm·운하 2곳 연속", "⑩ 티어 색 사용 0", "⑪ 위계(그린 상자)", "⑫ 글 블록-상자 테두리 ≥ 3mm"],
    },
    "worker_handoff": {
        "map": "v2_map.py 단일 원본: 지형·테베레강·바다·해안·길(R1~R6b, 연장 포함 plan 좌표)·포르투스 기하(PORTUS_CANALS·PORTUS_MOLES·PORTUS_LIGHTHOUSE → core_map.portus_geometry.canals·moles·lighthouse)·히어로 형태(HERO_INTERIOR → core_map.hero.interior)·소품·심은 지면·지형·지리 좌표(geo None = 지리 표 '없음'). 수도교 접점 AQUEDUCT_PLAN(욕장 오른쪽 변 (336,160))의 원본이다 → 읽는 쪽: global(검사·조립), render(아치 열), panels(수도교 라벨 슬롯)",
        "panels": "v2_panels.py 단일 원본: 틀(타이틀 126.5~293.5×10~92·푸터 18~402×568~581과 두 노트), 패널 rect(L·B·D·S), Detail 상자·글(Z1 circle·text_box·composite_box, C1·C2·C4 box), 지시선 꼭짓점(LEADERS), 라벨 슬롯·방향·본문(LABELS), 바닥 글(FLOOR_TEXT) → 읽는 쪽: global(검사·조립), render(그리기)",
        "render": "render.py: 사양을 읽어 그리기만 한다(서체 글자면 → em 환산, 형태·그림·조판, drawn.json 기록). 사양 값을 덮어쓰지 않는다(라벨 배율·자리·지시선 끝점·길 연장 하드코딩 금지). 인쇄 지면만 그린다(내부 표기 0). drawn.json 계약은 drawn_contract",
        "global": "v2_base.py 공용 상수(STAGE·STAGE_EXT·STAGE_AREA_EXT·인쇄 금지 패턴·서체 결정·출력 규격)·v2_data.py 모음(PANELS_PRINT·detail_box)·v2_check.py 사전 검사(사양 기하)와 사후 검사(drawn.json 12규칙)·v2_build.py 조립·v2_text.py 원칙·충돌 글·v2_svg.py 내부 골격 미리보기·make.py 실행기(사후 검사 실패 시 종료 코드 1)",
    },
}


def _hygiene(o, path=()):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _hygiene(v, path + (str(k),))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _hygiene(v, path + (str(i),))
    elif isinstance(o, str):
        if ("위치도" in o or "연대기" in o) and not (path[:2] == ("meta", "user_review") or "보류" in o):
            yield "/".join(path)


bad = list(_hygiene(spec))
json.dump(spec, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if bad:
    print("경고: 사양에 '위치도'·'연대기'가 남음(사용자 검토 인용·보류 기록 제외):", bad[:10])
print("사양 JSON 저장:", sys.argv[2], "· 패널", [p["id"] for p in panels], "· 무대", D.STAGE_AREA_EXT, "· Basic 최소", H["basic_min"], "· Detail 최대", H["detail_max"])
