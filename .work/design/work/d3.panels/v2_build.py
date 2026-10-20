# -*- coding: utf-8 -*-
"""final_layout_spec-v2-새위계.json 조립: 기하(v2_data) + 검사(v2_check.json) + 원칙·충돌(v2_text).
사용: python -I v2_build.py <data_dir> <out.json>"""
import json
import math
import sys

sys.path.insert(0, sys.argv[1])
import v2_data as D  # noqa: E402
import v2_text as TX  # noqa: E402

chk = json.load(open(sys.argv[1] + "/v2_check.json"))
R1 = lambda v: [round(float(a), 1) for a in v]  # noqa: E731
H = chk["hierarchy"]


def plan_pts_screen(plan):
    return [R1(D.to_screen(*p)) for p in plan]


def area(b):
    return round((b[2] - b[0]) * (b[3] - b[1]))


oct_ = D.hero_oct()
hb = H["hero_box"]
landmarks = []
for x in D.LANDMARKS:
    b = chk["objects_boxes"][x["name"]]["box"]
    landmarks.append({
        "id": x["id"], "name": x["name"], "latin": x["latin"], "tier": "Core(표준 랜드마크)", "zone": x["zone"],
        "projected_box": b, "projected_wh": chk["objects_boxes"][x["name"]]["wh"], "projected_area_mm2": chk["objects_boxes"][x["name"]]["area"],
        "center": [round((b[0] + b[2]) / 2, 1), round((b[1] + b[3]) / 2, 1)],
        "form": x["form"], "label_story": x["story"], "label_number": x["number"], "links": x["links"],
        "real_position": x["real"], "geo_approx": list(x["geo"]),
        "ring_distance_mm": chk["ring_distance_mm"][x["name"]], "contact_distance_mm": chk["contact_distance_mm"][x["name"]],
    })
background = []
for x in D.BACKGROUND:
    b = x["box"]
    background.append({"id": x["id"], "name": x["name"], "latin": x["latin"], "tier": "Core(지도 배경, 가장 작은 랜드마크급 지도 요소)", "zone": x["zone"],
                       "projected_box": b, "projected_wh": [b[2] - b[0], b[3] - b[1]], "projected_area_mm2": area(b),
                       "form": x["form"], "label_story": x["story"], "label_number": x["number"], "links": x["links"], "real_position": x["real"],
                       "ring_distance_mm": chk["ring_distance_mm"][x["name"]]})

panels = []
for p in D.PANELS:
    b = p["rect"]
    panels.append(dict(p, size=[b[2] - b[0], b[3] - b[1]], box_area=area(b)))

roads = []
for r in D.ROADS:
    roads.append({"id": r["id"], "name": r["name"], "w_screen_perp_mm": r["w"], "center_line": r.get("center_line", False),
                  "screen_pts": plan_pts_screen(r["plan"]), "plan_pts": [R1(p) for p in r["plan"]], "note": r["note"]})

details = []
for d in D.DETAILS:
    e = dict(d)
    if "circle" in d:
        c, dd = d["circle"]["c"], d["circle"]["d"]
        e["projected_box"] = [c[0] - dd / 2, c[1] - dd / 2, c[0] + dd / 2, c[1] + dd / 2]
    else:
        e["projected_box"] = d["box"]
    e["projected_area_mm2"] = area(e["projected_box"])
    e["tier"] = "Detail"
    details.append(e)

size_table = [{"tier": "Core", "name": "지도 무대 전체(로마 건축물 지도)", "box": list(D.STAGE), "area_mm2": D.STAGE_AREA}]
size_table.append({"tier": "Core(히어로)", "name": "콜로세움", "box": hb, "area_mm2": H["hero_area"]})
for x in landmarks:
    size_table.append({"tier": "Core(표준 랜드마크)", "name": x["name"], "box": x["projected_box"], "area_mm2": x["projected_area_mm2"]})
for p in panels:
    size_table.append({"tier": p["tier"], "name": f'{p["id"]} {p["name"]}', "box": p["rect"], "area_mm2": p["box_area"]})
for d in details:
    size_table.append({"tier": "Detail", "name": d["name"], "box": d["projected_box"], "area_mm2": d["projected_area_mm2"]})
for x in background:
    size_table.append({"tier": "Core(지도 배경)", "name": x["name"], "box": x["projected_box"], "area_mm2": x["projected_area_mm2"]})

river_poly = [R1(p) for p in D.river_polygon()]
spec = {
    "meta": {
        "title": "로마 콘크리트 A2 세로 포스터 — 203X 도시 인포그래픽 '로마 편' 최종 배치 사양 v2(새 정보 위계)",
        "version": "final-2 새위계 (2026-10-19)",
        "hierarchy_change": {
            "date": "2026-10-18 23:43",
            "user_words": "정보 위계를 변경하자. 도시 인포그래픽처럼 로마 건축물들이 core 정보이고, 로마콘크리트 제작과정은 basic 정보와 detail 정보로 서사하고 support로 현대 콘크리트의 유통기한은 100년, 로마콘크리트는 2000년 으로 서사하는 방향으로 정보위계를 변경하고 변경한 위계에 맞춰서 다시 설계작업 진행해",
            "precedence": "이 위계 변경이 공통 자료·지시 A~J·가중치 순서·이전 종합의 위계 서술보다 우선한다",
        },
        "units": "A2 mm, 포스터 0~420 × 0~594, 화면 좌표(x 오른쪽, y 아래)",
        "projection": "진짜 등각(지면 축 ±30°, 수직 90°, 카메라 고도 35.264°). 평면 +X → 화면 ↘(cos30, 0.5), +Y → 화면 ↙(−cos30, 0.5), 평면 원점 = 화면 (0,0). 화면 ↘ 직선 y = tan30·x + c 는 평면 Y = c, ↗ 직선 y = −tan30·x + d 는 평면 X = d (v16 common.Iso와 같은 규약)",
        "light": "왼쪽 위 하나(윗면 > 왼면 > 오른면)",
        "weight_order": ["0 정보 위계 변경(2026-10-18 23:43, 최우선)", "1 도시 인포그래픽 레퍼런스 정밀분석", "2 203X 베이징·신문 정밀분석", "3 사용자 확정 결정(바꿀 수 없음)", "4 지도교수 비평의 원칙(새 위계로 읽음)", "5 손 스케치·구상도 v3(참고만)"],
        "sources": {
            "reference_analysis": "/Users/um-yunsang/roman-concrete-private-refs/.work/out/refs-analysis/*_zones.png 와 관련 JSON",
            "benchmark": "/Users/um-yunsang/roman-concrete-private-refs/docs/references/benchmark-analysis/203X-벤치마크-정밀분석.md",
            "user_directives": "/Users/um-yunsang/roman-concrete-private-refs/.work/out/review/v16_user_updates.txt (A~J)",
            "accuracy": "/Users/um-yunsang/roman-concrete-private-refs/docs/research/화산-Support-사례-조사-2026-10-18.md ([S#] 번호)",
            "previous_spec": "/Users/um-yunsang/roman-concrete-private-refs/.work/out/refs-analysis/final_layout_spec.json",
            "geometry_source": "/Users/um-yunsang/roman-concrete-private-refs/.work/out/refs-analysis/_work_v2/v2_data.py",
            "check_source": "/Users/um-yunsang/roman-concrete-private-refs/.work/out/refs-analysis/_work_v2/v2_check.py",
            "check_result": "/Users/um-yunsang/roman-concrete-private-refs/.work/out/refs-analysis/_work_v2/v2_check.json",
            "preview_png": "/Users/um-yunsang/roman-concrete-private-refs/.work/out/refs-analysis/final_layout_spec-v2-새위계_preview.png",
            "report_md": "/Users/um-yunsang/roman-concrete-private-refs/docs/references/benchmark-analysis/도시-인포그래픽-종합분석-v2-새위계.md",
        },
        "rule_of_thumb": "좌표는 배치 골격이다. 워커는 상자 안에서 형태를 다듬되, 투영 상자 크기·티어 순서·맞닿음·±30° 규칙은 바꾸지 않는다. 투영 크기는 레이어 알파 외곽 상자로 잰다(그림자·빛 번짐은 shadow 레이어 또는 알파 40 이하).",
    },
    "hierarchy": {
        "definition": {
            "Core": "로마 건축물 지도(도시 인포그래픽의 랜드마크 지도): 콜로세움(히어로·최대 단일 오브젝트) + 판테온·트라야누스 시장·카라칼라 욕장(절개)·수도교·카이킬리아 메텔라 무덤·포르투스 + 지도 배경 베수비오 + 테베레강·바다·길·지형·소품",
            "Basic": "L 로마 콘크리트란?(정의 + 재료), R 위치도, B 제작 과정 6단계(재료 준비 → 마른 혼합 → 물 붓기 → 뜨거운 혼합 → 다져 넣기 → 굳기·석회 알갱이), T 연대기. 화면 평행 패널(도시편 문법), B는 지도 공사장과 지시선 1개로 잇는다",
            "Detail": "D 석회 알갱이·자가치유·뜨거운 혼합 패널 + 지도 위 확대 창 Z1(콜로세움 기초 콘크리트 → 석회 알갱이) + 콜아웃 C1(판테온 돔의 가벼운 골재)·C2(포르투스 방파제와 바닷물)·C4(메텔라 드럼 재결속)",
            "Support": "S 현대 콘크리트 약 100년 vs 로마 콘크리트 2,000년 비교(가장 작은 위계)",
        },
        "projected_size_order": "Core(지도 무대 173,460mm², 콜로세움 35,257mm² = 최대 단일 오브젝트) > Basic 각 요소(최소 T 5,160) ≥ Detail 각 요소(최대 D 4,816, 최소 콜아웃 2,376) > Support(S 2,100). 베수비오(2,320)는 랜드마크급 지도 요소 가운데 최소",
        "size_table": size_table,
        "checks": H["checks"],
        "ratios": {"basic_min_over_detail_max": H["ratio_basicmin_over_detailmax"], "detail_min_over_support": H["ratio_detailmin_over_support"],
                   "hero_over_landmark_median": H["hero_over_landmark_median"], "hero_pct_stage": round(100 * H["hero_area"] / D.STAGE_AREA, 1)},
    },
    "frame": {
        "stage": {"rect": list(D.STAGE), "area_mm2": D.STAGE_AREA, "note": "지도 무대 420×413mm(포스터 높이 69.5%), 좌우 전폭. 상하 패널 띠를 모두 두는 표준 틀 레퍼런스 68.7~71.4%(상하이·베이징·청와대·홍콩)"},
        "title": {"rect": D.TITLE["rect"], "name": D.TITLE["name"], "width_pct": 39.8,
                  "note": "주제 건축 정면 입면 액자(베이징 궁궐 문·도쿄 도리이·베를린 브란덴부르크 문·자금성 지붕 계열). 시리즈 표기 'CITY LANDMARK INFOGRAPHICS · ROMA' 띠를 둔다. 카라칼라 욕장 위 끝(y 94)이 아래 변에 2mm로 다가간다(도쿄 0.8mm 접촉 선례)"},
        "panels": panels,
        "panel_rules": [
            "상자·배경판 없이 바탕 위에 조판한다(베이징·도쿄·홍콩). 예외: R 위치도만 연한 판(청와대 SPACE LAYOUT 선례)",
            "머리글: 영문 초압축 대문자 7.4~7.8mm + 국문 3.6~4.0mm 윗선 정렬, 강조색 폼페이 레드 한 색",
            "L·R 윗선 y 20, 좌측 정렬선 x 18, 하단 띠 윗선 y 505(같은 줄), S는 지도 모서리 패널(윗선 y 466, 오른쪽 정렬선 x 402 = R·T와 같음)",
            "티어 배지·범례는 포스터에 두지 않는다(203X 문법). 티어는 크기·자리로만 읽힌다",
        ],
        "footer": D.FOOTER,
        "panel_area_pct_poster": chk["density_estimate"]["panel_area_pct_poster"],
    },
    "core_map": {
        "hero": {
            "name": "콜로세움(Amphitheatrum Flavium) — 히어로·최대 단일 오브젝트",
            "center_screen": list(D.HERO_C), "center_plan": R1(D.HERO_C_PLAN), "oct_R_plan": D.HERO_R, "base_side_T": D.HERO_SIDE, "ring_ratio": D.HERO_RING,
            "base_oct_screen": [R1(p) for p in oct_], "walls": D.HERO_WALLS,
            "projected_box": hb, "projected_wh": H["hero_wh"], "projected_area_mm2": H["hero_area"],
            "cutaway": D.HERO_CUTAWAY, "worksite": D.WORKSITE,
            "form": [
                "LocalBanana 참조 디오라마 원래 방향: 4층 외벽 조각(높이 60mm)은 뒤-왼쪽(평면 방위 150°~235°), 뒤-오른쪽 고리 2층(28mm), 앞쪽은 무너져(12mm) 관람석 층·하이포게움(왼쪽 반)·복원 나무 바닥(오른쪽 반)이 보인다",
                "받침: strata_slab 지층 3겹 이상(D), 앞 세 변에만 옆면 7mm, 지면 높이에 묻는다(떠 있는 섬처럼 보이지 않게, G)",
                "받침 앞 변(화면 아래 평평한 변) x 208~292를 절개해 콘크리트 기초 고리 단면을 보인다. 왼쪽 발치에 공사장(나무 거푸집·다짐 막대 일꾼 2·반죽 통·재료 더미), 오른쪽 x 275에서 확대 창 Z1 지시선이 나간다",
                "받침 광장 소품: 사이프러스·올리브·기둥 폐허·노점·암포라·인물(구스 모라이스 폐허 어휘, LocalBanana). 이웃(지스몬디): 앞-왼쪽 나무 열 정원, 오른쪽 앞 작은 타원(루두스 마그누스)을 넣으면 라벨에 '콘스탄티누스 시대 복원 모형 기준'을 밝힌다",
                "높이 과장은 1.1~1.2배까지(피라미드 1.22배 선례), 라벨 수치는 실제값(약 188×156 m, 높이 약 48 m)",
            ],
            "gates": {"아피아 가도 문(뒤-오른쪽 변)": R1(D.to_screen(*D.ROADS[0]["plan"][0])), "하역장 길 문(앞-왼쪽 변)": R1(D.to_screen(*D.ROADS[3]["plan"][0]))},
        },
        "landmarks": landmarks,
        "background": background,
        "zones": {
            "도심": "콜로세움 + 테베레 ↘ 팔 + 하역장·석회 가마·수레·공사장(지도 가운데)",
            "시내": "트라야누스 시장(왼쪽 위) · 판테온(왼쪽 가운데) · 카라칼라 욕장(뒤쪽 가운데-오른쪽)",
            "남동 교외": "수도교 아치 열(오른쪽 위) · 아피아 가도 · 카이킬리아 메텔라 무덤(오른쪽 가운데) · 포도밭·교외 빌라(오른쪽 아래)",
            "서남서 해안": "테베레 하구 · 포르투스(육각 내항 육지 + 외항·등대 바다) · 오스티아 · 바다(왼쪽 아래 모서리)",
            "가장 먼 곳": "알바노 구릉 띠(로마 건물의 화산재, 지형 결·라벨만) + 베수비오(오른쪽 위 모서리)",
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
            "land_sea_split_mm2": chk["portus_land_sea_split_mm2"],
            "polygons_screen": {k: [[R1(p) for p in pg] for pg in v] for k, v in D.portus_polys().items()},
        },
        "roads": roads,
        "aqueduct": {"ground_line_screen": [R1(D.to_screen(*D.AQUEDUCT_PLAN[0])), R1(D.to_screen(*D.AQUEDUCT_PLAN[1]))], "arch_height_mm": D.AQUEDUCT_H,
                     "note": "오른쪽 변 밖(남동 시골)에서 ↖로 들어와 카라칼라 욕장 오른쪽 변에 닿는다(아쿠아 안토니니아나 지선 → 저수조 64개[S47][S49]). 2단 아치, 교각 약 8mm 간격, 지면보다 채도를 2배 이상 높인 벽돌·석재 색(지스몬디 2.1~4.6배)"},
        "road_rules": ["±30° 띠만, 꺾임은 평면 직각", "주축 16mm + 흰 중앙선 1.6mm(도쿄·베를린), 보조 8~10mm", "모든 랜드마크가 길·강·해안·수도교 중 하나에 2.5mm 안으로 닿는다(도쿄 19/23)"],
        "props": D.PROPS,
        "terrain": D.TERRAIN,
        "planted": D.PLANTED,
        "labels": {
            "count": chk["labels"], "reference": "도시편 11~21개(중앙값 17), 파리 15·상하이 21·홍콩 16·도쿄 21·베를린 15",
            "slots": D.LABELS, "floor_text": D.FLOOR_TEXT,
            "grammar": [
                "지도 위 글자는 전부 등각 평면: 이름·설명은 벽면(세로획 수직), 지형명은 바닥에 눕힌다. 화면 평행 0° 글자 0개",
                "스택(v16 common 표준 = 베이징): 영문 압축 볼드 대문자 3.8mm → 국문 볼드 3.8mm + 라틴어 원명 위첨자 2.1mm → 헤어라인 규선 → 본문 3.0mm(줄 피치 4.15mm) 2줄 + 수치 1줄. 본문 첫 줄은 그 건물의 '콘크리트 이야기'(H)",
                "방향: 구역마다 한 방향. 뒤쪽 줄(트라야누스 시장·카라칼라·수도교·베수비오) = ↗(+30°), 그 밖 = ↘(−30°). 바닥 글은 그 선형 요소와 평행",
                "형식: 랜드마크 = 브래킷형, 탈것·먼 소품 = 깃대형, 본문 없는 작은 시설 = 말풍선 태그(재료 시설 색), 히어로 받침 안 소품 = 지시선 없이 인접(상하이)",
                "잉크: 지도 라벨은 중립 잉크 한 색(땅 위 짙은 갈색, 물 위 밝은 크림 또는 톤온톤). 강조색은 쓰지 않는다",
                "방위표·축척·범례는 지도에 두지 않는다(베이징·청와대). 실제 방위는 R 위치도",
            ],
        },
    },
    "basic": {
        "panels": [p for p in panels if p["tier"] == "Basic"],
        "process_representation": {
            "decision": "패널 안 단계 도식(B) + 지도 위 공사장 장면(Core 소품) + 지시선 1개",
            "panel": "B 196×60mm: 6칸 등각 소형 장면(칸당 약 31×30mm), 칸 사이 바닥 화살표(신문), 아래 시간 화살표(피라미드), 단계 번호 원(폼페이 레드)",
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
            "지시선은 수직·±30°, 꺾임 ≤ 1, 화살표 없이 끝점 지름 0.9mm",
            "짝 표지: 콜로세움 절개·Z1·D = 'A', 판테온·C1 = 'B', 포르투스·C2 = 'C', 메텔라·C4 = 'D'(자금성 A·B·C 깃발 짝 문법)",
            "콜아웃 크기 54×44mm = Detail 최소 2,376mm². Support(2,100mm²)보다 1.13배 크게 유지한다. 콜아웃을 줄이면 S도 같이 줄인다",
            "Detail 패널 D(4,816mm²)는 Basic 최소(T 5,160mm²)보다 작게 유지한다",
        ],
    },
    "support": {
        "panel": [p for p in panels if p["tier"] == "Support"][0],
        "rules": ["포스터에서 가장 작은 정보 요소(2,100mm²)", "막대 2개는 콘크리트 시험체 모양, 길이 비 1:20(현대 약 3mm : 로마 약 60mm), 격자선 없음(신문 TOP 6)", "각주: 강도가 아니라 수명(압축 강도는 현대 콘크리트가 높다[S4])", "지도 모서리 패널: 포도밭 위 고요한 영역, 연대기 T 바로 위"],
    },
    "measurements": {
        "hero_cluster": chk["hero_cluster"], "core_group_city": chk["core_group_city"],
        "density_estimate": chk["density_estimate"], "ring_distance_mm": chk["ring_distance_mm"], "ring_range_median": chk["ring_range_median"], "left_right": chk["left_right"],
        "contact_distance_mm": chk["contact_distance_mm"], "geo": chk["geo"], "overlaps_not_allowed": chk["overlaps_not_allowed"],
        "land_in_sea": chk["land_in_sea"], "land_in_river": chk["land_in_river"],
    },
    "accuracy_rules": [
        "육상 건물(콜로세움 등)은 민물, 바닷물은 항구 구조물에만[S1][S4][S12]",
        "콘크리트는 거푸집에 '다져 넣는다'. '타설'·'붓기'를 쓰지 않는다[S4]",
        "화산재 산지: 바다 공사 = 나폴리만 포추올리 일대(캄피 플레그레이), 로마 시내 건물 = 알바노 구릉 붉은 화산재. 둘 다 핀·라벨로만. '포졸라나 = 베수비오 화산재'는 쓰지 않는다[S4][S6][S7]",
        "베수비오 79년 이전 모습: 넓은 봉우리 하나·잿빛 평평한 정상·포도밭 비탈, 연기 없음, 분화는 '79년'만[S3][S24][S30]",
        "카라칼라 욕장 오큘러스·코퍼는 '복원 추정', 빛은 큰 창 중심, 코퍼는 얕은 격자로 판테온과 구분[S47][S48][S49]",
        "판화 속 황제 거상은 판화가의 상상도. 넣더라도 라벨에서 사실로 쓰지 않는다(불변 조건 13)",
        "콜로세움 시료 직접 분석은 미확인: 기초 깊이·화산재 산지를 단정하지 않는다. '겉은 석회화 돌, 속과 기초는 콘크리트'로 쓴다[S61][S4]. Z1 창 안 그림은 '로마 콘크리트 단면 모식'",
        "판테온 골재 산지는 미확인: '위로 갈수록 가벼운 골재'까지만 쓴다[S13][S77]",
        "로마 콘크리트가 현대보다 강하다고 쓰지 않는다. 강점은 오랜 결속과 회복력이다[S4]",
        "'2,000년 동안 더 단단해졌다' 대신 '바닷물과 반응해 새 광물이 자라 결속이 강해졌다'[S4][S12]",
        "'2023년 MIT가 정확히 밝혀냈다' 대신 '2023 MIT 연구가 실마리를 찾고 2025 폼페이 공사 현장 연구가 확인했다'[S10][S11]",
        "수도교: 퐁 뒤 가르는 콘크리트 구조가 아니다. 아쿠아 클라우디아 아치는 석재, 네로 아치는 벽돌, 하드리아누스기 보수 구간은 벽돌면 콘크리트[S59][S60]",
        "메텔라 무덤의 류사이트 재결속은 석회 알갱이 자가치유와 다른 메커니즘이라 문장을 구분한다[S9][S4]",
        "연대기의 '80 콜로세움 개장'·'약 125 판테온 재건'은 조사 보고서 밖 일반 연표다. 인쇄 전 출처를 확인한다",
    ],
    "principles": TX.PRINCIPLES,
    "conflicts": TX.CONFLICTS,
    "invalidated_from_previous": TX.INVALIDATED,
    "reused_from_previous": TX.REUSED,
    "worker_handoff": {
        "arena": "core_map.hero 전부(중심·R·벽 높이·LocalBanana 원래 방향·앞 변 절개·공사장). 상자 203.8×173.0mm ±5%, 최대 단일 오브젝트 유지",
        "support_top(이름 유지, 역할 = Core 랜드마크 뒤쪽 줄)": "트라야누스 시장 L2(새로 맡음)·판테온 L1·카라칼라 욕장 L3(절개)·베수비오 V + 알바노 구릉 띠·포도밭 농장",
        "support_bottom(이름 유지, 역할 = Core 랜드마크 가장자리)": "수도교 L4(카라칼라로 물을 대는 아치 열)·메텔라 L5(아피아 가도 남쪽 길가)·포르투스 L6(육각 내항·외항·등대 외형)",
        "map": "지면·테베레강 polygon_screen·해안선·바다(띠 밑 연장)·길 4개·수도교 지면선은 support_bottom과 공유·소품 10개·심은 지면 6곳·바닥 글 5",
        "panels": "frame.panels 좌표(L·R·B·D·T·S), B 6칸 소형 장면, Detail Z1·C1·C2·C4, 지시선 6개, 위치도(R)의 하구–포르투스·알바노 구릉·포추올리·베수비오 핀",
        "core(옛 셀 체인 담당)": "지도 위 셀 체인은 없앤다. B 패널 6칸 소형 장면(화면 평행 패널 안 등각 아이콘)을 맡거나 panels에 합친다",
        "global": "검사표를 새 위계로 바꾼다: Core 지도 > Basic 최소 ≥ Detail 최대, Detail 최소 ≥ Support × 1.1, 콜로세움 ≥ 랜드마크 최대 × 1.1, 베수비오 ≤ 랜드마크 최소 ÷ 1.1. 히어로 군·도심·시내 코어 군의 실루엣·껍질·상자와 밀도(심은 지면 포함)를 맨 위에 출력",
    },
}
json.dump(spec, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("사양 JSON 저장:", sys.argv[2])
