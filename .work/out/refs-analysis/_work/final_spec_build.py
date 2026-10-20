# -*- coding: utf-8 -*-
"""final_layout_spec.json 조립: 기하(final_spec_data) + 검사 결과(final_spec_check.json) + 원칙·충돌·워커 지시."""
import json
import sys

sys.path.insert(0, sys.argv[1])
import final_spec_data as D  # noqa: E402
import final_spec_text as TX  # noqa: E402

chk = json.load(open(sys.argv[1] + "/final_spec_check.json"))
G = chk["geometry"]
R2 = lambda v: [round(float(a), 2) for a in v]  # noqa: E731

cells = []
contents = {
    1: "생석회(흰 더미)·화산재(붉은 갈색 더미)·골재(응회암·벽돌 조각) m_mound 3개, 재료 운반 길에서 들어오는 수레 1, 일꾼 2(가리키기·바구니 나르기)",
    2: "물 없는 혼합 판(나무 틀), 괭이로 생석회+화산재를 섞는 일꾼 2, 체 1",
    3: "수도교 분배 탱크에서 오는 물길(왼쪽 꼭짓점) → 물통, 물을 붓는 일꾼 1·통 나르는 일꾼 1. 바닥 글: 육상 건물(콜로세움)은 민물, 바닷물은 항구 구조물에만",
    4: "생석회와 물이 만나 끓는 혼합 구덩이, 김(glow 레이어, 알파 40 이하), 괭이 일꾼 2",
    5: "뜨거운 혼합이 남긴 흰 석회 알갱이가 섞인 반죽 더미(알갱이 다각 면), 반죽을 옮기는 일꾼 1·통 1",
    6: "콜로세움 기초·볼트용 나무 거푸집(아레나 받침 왼쪽 위 모서리에 붙음), 다짐 막대로 다져 넣는 일꾼 2(붓지 않는다)",
    7: "굳은 콘크리트 단면 블록(흰 석회 알갱이, 지시선 시작점 'A' 표지), 단면을 가리키는 일꾼 1. 아레나 받침 왼쪽 위 변과 같은 높이로 이어짐",
}
arrows = {1: "+X ↘", 2: "+Y ↙", 3: "+X ↘", 4: "+Y ↙", 5: "+X ↘", 6: "+Y ↙", 7: "+X ↘(아레나로)"}
for k in range(1, 8):
    g = G["cells"][f"c{k}"]
    v = g["verts"]
    st = D.CELL_STEP[k - 1]
    nxt = D.cell_verts(k + 1) if k < 7 else None
    # 다음 셀(또는 아레나)과 맞닿는 변의 가운데 = 바닥 화살표 자리
    if k < 7:
        if k % 2 == 1:   # +X: 아래-오른쪽 변
            a, b = v["R"], v["B"]
        else:            # +Y: 아래-왼쪽 변
            a, b = v["B"], v["L"]
    else:
        a, b = v["R"], v["B"]
    mid = [round((a[0] + b[0]) / 2, 2), round((a[1] + b[1]) / 2, 2)]
    bx = chk["object_boxes"][f"셀 c{k}(단계 {st})"]
    cells.append({
        "id": f"c{k}", "step": st, "step_name": D.STEP_NAME[st], "step_en": D.STEP_EN[st],
        "column": "왼쪽 열" if k % 2 == 1 else "오른쪽 열",
        "center": g["center"], "verts_TRBL": [v["T"], v["R"], v["B"], v["L"]],
        "screen_w_h": [D.CELL_W, round(2 * D.CELL_HH, 2)], "plan_side": round(D.CELL_S, 2),
        "projected_box_with_board": bx["box"], "projected_box_area": bx["area"],
        "floor_arrow_to_next": {"at": mid, "dir": arrows[k]},
        "contents": contents[k],
    })

boards = []
for b in D.BOARDS:
    p = D.board_poly(b["cell"], b["edge"], b["h"], b.get("frac", (0.0, 1.0)))
    boards.append({"cell": f"c{b['cell']}", "kind": b["kind"], "edge": "뒤-왼쪽 변(−X면, 글줄 ↗)" if b["edge"] == "UL" else "뒤-오른쪽 변(−Y면, 글줄 ↘)",
                   "height": b["h"], "poly": [R2(q) for q in p]})

spec = {
    "meta": {
        "title": "로마 콘크리트 A2 세로 포스터 — 203X 도시 인포그래픽 '로마 편' 최종 배치 사양",
        "version": "final-1 (2026-10-18)",
        "units": "A2 mm, 포스터 0~420 × 0~594, 화면 좌표(x 오른쪽, y 아래)",
        "projection": "진짜 등각(지면 축 ±30°, 수직 90°, 카메라 고도 35.264°). 평면 +X → 화면 ↘(cos30, 0.5), +Y → 화면 ↙(−cos30, 0.5). 평면 길이 1 = 화면 변 길이 1mm(v16 common.Iso와 같음)",
        "light": "왼쪽 위 하나(윗면 > 왼면 > 오른면)",
        "weight_order": ["1 도시 인포그래픽 레퍼런스 정밀분석(최우선)", "2 203X 베이징·신문 정밀분석", "3 사용자 확정 결정(바꿀 수 없음)", "4 지도교수 비평의 원칙", "5 손 스케치·구상도 v3(참고만)"],
        "sources": {
            "reference_analysis": "/Users/um-yunsang/roman-concrete-private-refs/.work/out/refs-analysis/*_zones.png 와 관련 JSON",
            "benchmark": "/Users/um-yunsang/roman-concrete-private-refs/docs/references/benchmark-analysis/203X-벤치마크-정밀분석.md",
            "user_directives": "/Users/um-yunsang/roman-concrete-private-refs/.work/out/review/v16_user_updates.txt (A~J)",
            "v16_measure": "/Users/um-yunsang/roman-concrete-private-refs/.work/out/wireframe_v16_measure.json",
            "geometry_source": "/Users/um-yunsang/roman-concrete-private-refs/.work/out/refs-analysis/_work/final_spec_data.py",
            "check_source": "/Users/um-yunsang/roman-concrete-private-refs/.work/out/refs-analysis/_work/final_spec_check.py",
            "preview_png": "/Users/um-yunsang/roman-concrete-private-refs/.work/out/refs-analysis/final_layout_spec_preview.png",
        },
        "rule_of_thumb": "좌표는 배치 골격이다. 워커는 상자 안에서 형태를 다듬되, 상자 크기 상한·맞닿음 조건·±30° 규칙은 바꾸지 않는다.",
    },
    "frame": {
        "stage": {"rect": list(D.STAGE), "note": "지도 무대 420×413mm(포스터 높이 69.5%), 좌우 전폭 블리드. 표준 틀(상하 패널 띠) 레퍼런스 68.7~71.4%"},
        "title": {"rect": D.TITLE["rect"], "name": D.TITLE["name"], "width_pct": 39.8,
                  "note": "주제 건축 정면 입면 액자(베이징 궁궐 문·도쿄 도리이·베를린 브란덴부르크 문·자금성 지붕 계열). 글자를 가리지 않도록 CORE 입구 간판은 아래 변에 0~2mm로만 닿는다"},
        "panels": [dict(p, size=[p["rect"][2] - p["rect"][0], p["rect"][3] - p["rect"][1]], box_area=(p["rect"][2] - p["rect"][0]) * (p["rect"][3] - p["rect"][1])) for p in D.PANELS],
        "panel_rules": [
            "상자·배경판 없이 바탕 위에 조판한다(베이징·도쿄·홍콩). 예외: R 위치도만 연한 판(청와대 SPACE LAYOUT 선례)",
            "머리글: 영문 초압축 대문자 7.4~7.8mm + 국문 3.6~4.0mm 윗선 정렬, 강조색 한 색",
            "L·R 윗선 y 20, 좌측 정렬선 x 18(=v16), 하단 띠 윗선 y 505",
            "L 통합: 정의 + 재료 비율·순서 1~2줄 요약(순서는 CORE가 자세히 맡는다). R 위치도: 북쪽 위 실제 지리, 로마·오스티아/포르투스(테베레 하구)·알바노 구릉·포추올리·베수비오/폼페이 핀, 지도에 담은 구역 5곳(도심 코어·시내·남동 교외·서남서 해안·베수비오) 표시, 방위표는 여기에만",
            "B1 석회 알갱이(4장면: 알갱이 → 균열 → 물·칼슘 → 방해석 봉합)는 바다 위 고요한 영역에 얹는다. B2 연대기·근거, B3 100년 vs 2000년",
        ],
        "footer": D.FOOTER,
        "panel_area_pct_poster": round(100 * sum((p["rect"][2] - p["rect"][0]) * (p["rect"][3] - p["rect"][1]) for p in D.PANELS) / (420 * 594), 1),
    },
    "core_group": {
        "definition": "공정 셀 체인(셀 7 + 간판 + 셀 소품) + 아레나 + 테베레강 굽이 + 강변 디테일(하역장·석회 가마·하역 마당·바지선·수레) + 재료 운반 길",
        "shape": "세로 'ㅗ' + L 발: 타이틀 아래에서 곧게 내려오는 신문식 지그재그 셀 기둥(세로 획) → 마지막 ↘ 한 걸음으로 아레나(밑)로 흘러든다. 강 '<' 굽이가 오른쪽 위를 두른다",
        "measure_method": "구성 레이어 알파 합집합 → 13mm 닫힘 → 구멍 메움 = 실루엣. 볼록 껍질, 지도 무대로 자른 바깥 상자. 세 값을 모두 검사표 맨 위에 출력한다(파리·도쿄 교훈)",
        "targets": {
            "silhouette_pct": [30, 40], "hull_pct": [45, 60], "bbox_pct": [55, 70],
            "aspect_h_over_w_min": 1.2, "centroid_norm_x": [0.52, 0.70], "centroid_norm_y": [0.42, 0.71],
            "reference_ranges": {
                "silhouette": "파리 25.6 · 상하이 32.5 · 홍콩 37.5 · 도쿄 27.6(확장 36.8) % / 절대 47,860~73,742mm²",
                "hull": "파리 38.5 · 상하이 45.3 · 홍콩 48.7 · 도쿄 35.3(확장 49.6) % / 절대 70,700~99,400mm²",
                "bbox": "파리 60.1 · 상하이 57.3 · 홍콩 62.3 · 도쿄 47.2(확장 60.5) · 베를린 60.9 % / 절대 98,200~122,000mm²",
            },
        },
        "measured_model": chk["core_group"],
        "chain": {
            "grammar": "신문 「The Journey of Newspaper」 등각 셀 체인: 같은 높이의 정사각 셀, 반 셀(55mm) 엇갈림, 단계 번호 배지(바깥쪽 끝), 바닥 화살표(+X·+Y), 단계 간판(뒤 가장자리 수직 보드, 좌우 교대), 바닥 글 2층(간판=대분류, 바닥 ①~⑭=소분류)",
            "cell_w": D.CELL_W, "cell_plan_side": round(D.CELL_S, 2), "half_step": [55.0, round(D.CELL_HH, 2)],
            "allocation": "셀 7개 = 1·1·1·2·1·1(4단계 뜨거운 혼합 2셀, 신문 P6 복잡도 배분)",
            "cells": cells, "boards": boards,
            "people": "셀당 2~3명, 키 약 19mm(셀 변 63.5mm의 0.3배, 신문 0.3배), 동작은 가리키기·들어 보이기·도구 들기",
            "step_box_rule": "단계 상자(셀+간판) ≥ Basic·Detail 최대 상자 × 1.05 (검사 결과 표 참조)",
        },
        "arena": {
            "center": G["arena_center"], "oct_R_plan": D.ARENA_R, "base_oct_screen": G["arena_oct"],
            "base_side_T": D.ARENA_T, "box_target": chk["object_boxes"]["아레나"]["box"], "box_wh": chk["object_boxes"]["아레나"]["wh"], "box_area": chk["object_boxes"]["아레나"]["area"],
            "contacts": [
                "c7의 +X 변(화면 아래-오른쪽 변 (223.0,352.53)→(168.0,384.28))이 팔각 받침 −X 변((226.0,350.8)→(165.0,386.0))과 한 직선에서 0mm로 맞닿는다(같은 높이의 단, 빈 띠 없음)",
                "c6의 아래 꼭짓점(223.0,352.53)이 받침 윗변 왼쪽 끝(226.0,350.8)에 3mm 안으로 닿는다(5단계 거푸집이 기초·볼트 모서리에 붙는다)",
            ],
            "form": [
                "LocalBanana 참조 디오라마를 좌우 반전: 4층 외벽 조각(높이 약 62mm)은 오른쪽 위 1/4(평면 방위 270°~360°), 뒤-오른쪽 고리는 2층(약 26mm)",
                "셀 6·7이 닿는 왼쪽 위 1/4(평면 135°~225°)은 높이 12mm 이하로 무너뜨려 셀을 가리지 않는다",
                "앞쪽은 무너져 관람석 층·하이포게움(왼쪽 반)·복원 나무 바닥(오른쪽 반)이 보인다",
                "받침: strata_slab 지층 3겹 이상(D), 앞쪽 세 변에만 옆면 7mm. 받침 앞-왼쪽 변에 콘크리트 기초 고리 절개",
                "광장 소품: 사이프러스·올리브·기둥 폐허·노점·인물(구스 모라이스 폐허 어휘). 이웃 근거(지스몬디): 앞-왼쪽 나무 열 정원(클라우디우스 신전 경내), 오른쪽 앞 작은 타원(루두스 마그누스)을 넣으면 라벨에 '콘스탄티누스 시대 복원 모형 기준'을 밝힌다",
                "높이 과장은 1.1~1.2배까지(피라미드 1.22배 선례), 라벨에는 실제 치수(188×156m, 높이 약 48m)",
            ],
        },
        "river": {
            "name": "테베레강(Tiberis)",
            "segments": D.RIVER,
            "bend": "평면 직각(화면 60°) 꺾임 1회, 굽이 꼭짓점 (318.0,208.89). 둥근 굽이(상하이 바깥 반지름 약 54mm)로 다듬어도 된다",
            "bleed": "두 끝 모두 오른쪽 변 밖(윗팔 y 150 부근에서 들어오고, 앞팔 y 268 부근에서 나간다). 하구는 지도에 그리지 않고 R 위치도가 맡는다",
            "rules": ["±30°만(수직 구간 0)", "띠 수직 폭 윗팔 16·앞팔 20mm(도쿄 14.2~17.5, 타이베이 14~17, 상하이 앞팔 1.56배)", "코어 체인–아레나 연결부와 떨어진 오른쪽 위에만 둔다(강이 코어와 콜로세움 사이를 가르지 않는다)", "물 면 facet_fill + 둑 contact_ao(D)"],
        },
        "riverside_details": D.CORE_DETAILS,
        "material_road": D.ROADS[1],
    },
    "sea_coast": {
        "coastline": {"pts": D.COAST, "equation": f"y = tan30·x + {D.COAST_B}", "note": "하나의 ↘(+X) 직선. 아레나 받침 앞-왼쪽 변과 평행하게 18mm 아래. 좌우 부두 수직 변 없음(B)"},
        "sea_polygon": D.SEA,
        "sea_under_bottom_band": {"poly": D.SEA_UNDER_BAND, "note": "하단 띠 밑으로 이어지며 아래로 갈수록 바탕색으로 흐린다(홍콩 앞바다 선례). 패널은 그 위에 얹는다"},
        "coast_section": "육지 판 앞 변(해안선)에 지층 단면 10mm(3겹)를 한 번만 보인다(서울 17~19mm·홍콩 18~21mm의 축소). 포르투스 부두 구간(x 4~76)은 3mm",
        "on_sea_only": ["클라우디우스 외항·방파제·등대(포르투스 상자 안)", "화산재 운반선", "확대 창(걸침 허용)", "바닥 글 MARE TYRRHENUM 티레니아해"],
        "sea_pct_stage": chk["density_estimate"]["sea_pct_stage"],
    },
    "roads": D.ROADS + [{"name": "욕장 앞길(보조)", "w": 8.0, "pts": [[92.0, 150.0], [113.0, 162.0]], "note": "욕장 앞 광장에서 ↘로 c1 왼쪽 꼭짓점까지"}],
    "road_rules": ["±30° 띠만, 꺾임은 평면 직각", "주축 16mm + 흰 중앙선 1.6mm(도쿄·베를린), 보조 8~10mm", "모든 Support가 길·강·해안·코어 중 하나에 2.5mm 안으로 닿는다(도쿄 19/23)"],
    "supports": D.SUPPORTS,
    "support2": D.SUPPORT2,
    "support_rules": [
        "받침 판 없이 지면 높이에 묻는다(옆면 0~2mm). 떠 있는 섬처럼 보이면 안 된다(G)",
        "투영 상자(레이어 알파 외곽 상자) ≤ Basic·Detail 최소 ÷ 1.1 = 5,251mm². 그림자·빛 번짐은 shadow 레이어나 알파 40 이하",
        "라벨 본문 2줄 + 수치 1줄(상하이·도쿄 수치 줄), 콘크리트 이야기 한 줄을 반드시 넣는다(H)",
        "포르투스: 바다 면은 지면(map) 소관이라 상자에 넣지 않는다. 판화를 좌우 반전해 육각 내항은 오른쪽 위 육지, 외항·등대는 왼쪽 아래 바다. 판화의 황제 거상은 넣더라도 라벨에서 사실로 설명하지 않는다(A·C)",
        "베수비오: Support-2, 대기 원근(바탕색 50% 혼합·흐림), 깃대형 이름표, 지도 속에서 키우지 않는다(제주 한라산 선례). 화산은 이것 하나",
        "욕장: 절개(앞 벽 30% 높이, 반쪽 코퍼 돔 단면, 오큘러스 빛줄기, 증기 욕조, 하이포코스트). 욕장은 이것 하나",
    ],
    "detail": {"magnifier": D.MAGNIFIER, "leaders": D.LEADERS,
               "rules": ["지시선은 수직·±30°, 꺾임 ≤ 1, 화살표 없이 끝점 지름 0.9mm", "c7 단면 블록과 확대 창 테두리에 같은 'A' 표지(자금성 끌어낸 모형 A·B·C 짝 문법)", "확대 창 Ø76 = Basic·Detail 최소(5,776mm²) → Support 상한을 정한다. 지름을 줄이면 Support 상한도 함께 줄어든다"]},
    "props": D.MAP_PROPS,
    "labels": {
        "count": {"wall_or_flag": len(D.LABELS), "floor_text": len(D.FLOOR_TEXT), "total": len(D.LABELS) + len(D.FLOOR_TEXT), "reference": "도시편 11~21개(중앙값 17), 파리 15·상하이 21·홍콩 16·도쿄 21"},
        "slots": D.LABELS, "floor_text": D.FLOOR_TEXT,
        "grammar": [
            "지도 위 글자는 전부 등각 평면: 이름·설명은 벽면(세로획 수직), 지형명은 바닥에 눕힌다. 화면 평행 0° 글자 0개",
            "스택(v16 common 표준 = 베이징): 영문 압축 볼드 대문자 3.8mm → 국문 볼드 3.8mm + 라틴어 원명 위첨자 2.1mm → 헤어라인 규선 → 본문 3.0mm(줄 피치 4.15mm)",
            "방향: 구역마다 한 방향. 뒤쪽 줄(욕장·판테온·베수비오)·강 윗팔 구역 = ↗(+30°), 그 밖 = ↘(−30°) 기본. 바닥 글은 그 선형 요소와 평행",
            "형식: Support = 브래킷형, 탈것·먼 소품 = 깃대형, 본문 없는 작은 시설 = 2색 말풍선 태그(재료 시설/교통 시설), 셀 안 소품 = 지시선 없이 인접(상하이)",
            "잉크: 지도 라벨은 중립 잉크 한 색(땅 위 짙은 갈색, 물 위 밝은 크림 또는 톤온톤). 강조색(폼페이 레드 #c82236)은 타이틀·패널 제목·Core 단계 번호·CORE 간판에만(베를린·피라미드)",
            "방위표·축척·범례는 지도에 두지 않는다(베이징·청와대). 실제 방위는 R 위치도",
        ],
    },
    "hierarchy_check": chk["hierarchy"],
    "overlaps_not_allowed": chk["overlaps_not_allowed"],
    "support_ring_distance_mm": chk["support_ring_distance_mm"],
    "density_estimate": chk["density_estimate"],
    "principles": TX.PRINCIPLES,
    "conflicts": TX.CONFLICTS,
    "worker_handoff": {
        "core": "cells·boards·floor_arrow 좌표 그대로. CELL_W 110, 7셀. 셀 소품·인물·바닥 글은 각 셀 contents. c1 오른쪽 25%는 재료 운반 길 입구",
        "arena": "center·R·contacts·form. 상자 208.5×163.4mm 안팎(±5%)",
        "map": "강 segments·해안선·바다(띠 밑 연장 포함)·길 4개·강변 디테일·밭/포도밭·바닥 글 5개",
        "support_top": "욕장 S1·판테온 S2·베수비오 S6 + 포도밭 농장",
        "support_bottom": "수도교 S3(c3로 물을 대는 끝 분배 탱크)·메텔라 S4(아피아 가도 길가)·포르투스 S5(앵커 3개)",
        "panels": "frame.panels 좌표, 확대 창·지시선 detail, R 위치도에 하구–포르투스·오스티아 관계 필수",
        "global": "검사표 맨 위에 코어 군 세 값(실루엣·껍질·상자)과 targets 판정, 단일 오브젝트 위계는 셀 단위(체인 전체는 하위 군)",
    },
}
json.dump(spec, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
print("written", sys.argv[2])
