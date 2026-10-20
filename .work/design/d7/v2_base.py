# -*- coding: utf-8 -*-
"""설계안 공용 기초(상수·좌표 변환·인쇄 규칙). 담당: global
하위 호환: 기존 이름(C30·T30·SQ3·POSTER·STAGE·STAGE_AREA·POSTER_AREA·to_screen·to_plan·plan_rect_screen_box)은 이름과 값을 바꾸지 않는다.
d4: 무대 확장(STAGE_EXT)을 해제하고(R·T 확장 0), 인쇄 패널을 L·P2·B·D·S·P5 6개로 한다(기준선 7절, 사용자 선택 2026-10-19 03:10).
d5: 기준선 8절(05:27~12:49)과 와이어프레임 통합 루프(0-1절, 12:18)의 공용 상수를 더했다(이름 더하기만).
    콜로세움 본체(8.1)·받침 없음(8.2)·히어로 군(12:49 철회 뒤 승인 설계 구성)·위계(투영 상자끼리/그린 외곽끼리)·Z1 새 출발점·
    사람 키 축척·벡터 그림체(AO·조명·그림자 0)·인쇄 선 굵기·Blender 인계(앵커 25개·sil.json·무대·높이)."""
import math

C30 = math.cos(math.radians(30))
T30 = math.tan(math.radians(30))
SQ3 = math.sqrt(3)

POSTER = (420.0, 594.0)
STAGE = (0.0, 92.0, 420.0, 478.0)          # 지도 무대 x0, y0, x1, y1. 사용자 15:41 결정: 아랫선 505 → 478(하단 띠 확대)
STAGE_AREA = (STAGE[2] - STAGE[0]) * (STAGE[3] - STAGE[1])
POSTER_AREA = POSTER[0] * POSTER[1]

# ── d4(기준선 7절): 옛 R 자리(298~420×20~92)와 옛 T 자리(312~420×505~568)는 지도 무대 확장에서 뺀다 ──
# 위 띠 오른쪽에는 Basic P2, 하단 띠 오른쪽에는 Basic P5가 들어가고, 두 자리 바탕은 L·B와 같은 종이/띠 바탕이다(지형·밭·포도밭 0).
# 무대 = STAGE 하나(173,460mm²). 이름은 하위 호환으로 남긴다(검사·조립·render가 읽는다).
STAGE_EXT = []
STAGE_AREA_EXT = STAGE_AREA + sum((r[2] - r[0]) * (r[3] - r[1]) for r in STAGE_EXT)   # = 173,460 (mm²)
STAGE_RECTS = [list(STAGE)] + [list(r) for r in STAGE_EXT]
# 옛 확장 두 자리(사양·보고서 기록용, 무대가 아니다)
FORMER_STAGE_EXT = {"R 자리(위 띠 오른쪽)": [298.0, 20.0, 420.0, 92.0], "T 자리(하단 띠 오른쪽)": [312.0, 505.0, 420.0, 568.0]}

# 사용자 검토(2026-10-19 02:24)로 인쇄 지면에서 뺀 패널 id(사양 조립·검사·미리보기가 걸러 낸다)
REMOVED_PANEL_IDS = ("R", "T")
# 인쇄 패널 6개와 그 순서(사양 frame.panels 순서). 기준선 7절: P2 = ARCH · VAULT · DOME, P5 = LEARNING FROM ROME
PRINT_PANEL_IDS = ("L", "P2", "B", "D", "S", "P5")   # 사용자 15:41·15:32: 장 6개 = ❶ L · ❷ P2 · ❸ 지도 · ❹ B · ❺ D · ❻ P5. S(100 VS 2,000)는 ❻ P5 안(embedded_in)
PANEL_COUNT_RANGE = (5, 7)                 # 도시편 근거(사용자 결정 2절)

# 필수 요소(사전 검사 (a)·사후 검사 ⑬). 하나라도 없으면 실패다
REQUIRED_LANDMARK_IDS = tuple("L%d" % k for k in range(1, 10))
REQUIRED_ROAD_IDS = ("R7",)
# 짝 표지 개수(사후 검사 ⑬): 글자 A~D와 숫자 1~4(P2 칸 ↔ 지도)
# 사용자 15:32·15:41: 글자 표지 A~D 삭제. 1~4는 4mm 형태 아이콘(아치·배럴 볼트·교차 볼트·돔)으로 P2 칸 + 지도 각 1곳, 5 = 지도 위 ❺ 근거 표지 3곳(포르투스·메텔라·공사장)
REQUIRED_MARKS = {"1": 2, "2": 2, "3": 2, "4": 2, "5": 0}
# 표준 랜드마크 하한(신규 L7~L9 포함, 기존 최소 메텔라 4,620과 같은 등급)
LANDMARK_MIN_AREA = 4500.0
# 히어로 ÷ 표준 랜드마크 중앙값 레퍼런스 범위(청와대 4.5 ~ 파리 7.9)
HERO_OVER_MEDIAN_RANGE = (3.2, 7.9)        # (사용자 16:14로 폐기: 히어로가 건물 하나라 판정에 쓰지 않는다)

# 인쇄 글 금지 패턴(작업 이름·티어 이름·치수·검사·설계 주석·사용자 검토로 뺀 패널 이름·보류 문구). m·km 단위와 '모식'은 허용한다.
PRINT_FORBIDDEN = r"Core|Basic|Detail|Support|위계|최종 배치|다이어그램|무대|꼬리표|자리|사양|검사|mm|위치도|연대기|자리 예약|선택 대기|저탄소|41%|29%"
# 영문 티어 이름은 대소문자를 가리지 않고 영문자 경계로도 잡는다(예: 'CORE · …' 꼬리표)
PRINT_FORBIDDEN_CI = r"(?<![A-Za-z])(core|basic|detail|support)(?![A-Za-z])"
# 인쇄 문장 금지(기준선 4·7절): 조각상 문장·반죽 붓기·퐁 뒤 가르·콜로세움 이름 유래(이번 회차 인쇄 0)
PRINT_FORBIDDEN_SENTENCES = r"콘크리트로 만든 조각|콘크리트로 빚은 거상|로마 콘크리트는 저탄소|(반죽|콘크리트|모르타르)\S{0,2}\s?(부었|부어|붓는|붓다)|붓다|퐁 뒤 가르|Pont du Gard|유래"
# 치수 인쇄 금지 대상(바실리카 높이·영묘 치수·극장 지름·거상 치수): 이 라벨·주석에는 '숫자 + m'를 쓰지 않는다
PRINT_NO_DIMENSION_KEYS = ("바실리카", "basilica", "maxentius", "영묘", "mausoleum", "hadrian", "극장", "theatre", "marcellus")   # 사용자 17:28·17:29 결정: 네로 거상은 근거 있는 높이(약 30 m) 허용
PRINT_DIMENSION = r"\d[\d,.]*\s?(m|미터|km)(?![A-Za-z])"

# 인쇄 색: 정보 잉크 한 색과 강조색(폼페이 레드). 티어 색은 인쇄 지면에서 0회.
INK_L = (58, 42, 28)
ACCENT = (200, 34, 54)
TIER_COLORS = {"Core": (47, 107, 58), "Basic": (63, 58, 160), "Detail": (208, 101, 14), "Support": (47, 127, 134)}
# 물 이름 잉크(TIBERIS·MARE TYRRHENUM): 물색보다 짙은 파랑(d3의 (236,246,252)에서 바꿈)
WATER_NAME_INK = (52, 92, 124)

# 서체 결정 7(글자면 = 잉크 높이: 국문 '한', 영문 'H' 대문자 높이, mm). 사후 검사 허용 오차 ±0.1, 피치 ±0.05.
TYPE_FACES = {
    "label_en": 3.8, "label_ko": 3.8, "label_sup": 2.1, "label_body": 3.0, "label_pitch": 4.15, "label_scale": 1.00,
    "tag": 2.6,
    "panel_head_en": 7.4, "panel_head_ko": (3.6, 3.8), "s_head_en": 5.0, "s_head_ko": 2.8,
    "step": 3.0, "subtitle": 2.8,
    "body": 2.6, "body_pitch": 3.9,
    "note": 2.1, "note_pitch": 3.0,
    "box_text_clear": 3.0,
    # d4 추가(하위 호환): 소품 주석(네로 거상, 말풍선 없음), 짝 표지 원 반지름(Ø4)과 표지 글자면
    "prop_annot": 2.6,
    "mark_r": 2.0,
    "mark_glyph": 2.2,
}

# 출력 규격(사양에만 적는다)
OUTPUT = {
    "final": {"size_mm": [420, 594], "ppi": 300, "px": [4961, 7016]},
    "review": {"px_per_mm": 3, "px": [1260, 1782]},
    "asset_native_px": "배치 폭 mm ÷ 25.4 × 300",
    "line_mm": {"지시선": 0.30, "콜아웃 테두리": 0.25, "Z1 테두리": 0.6, "내부선": [0.10, 0.20], "복원 점선": 0.25},
}


# ═════════════ d5: 기준선 8절(05:27~12:49) + 통합 루프(0-1절, 12:18) 공용 상수(이름 더하기만) ═════════════
# 판정·인계 우선순위의 맨 위(사양 meta.weight_order·principles·worker_handoff 첫 항목)
BASELINE_TOP = [
    "0 기준선 8절(사용자 2026-10-19 05:27~12:49, 1~7절보다 우선): 콜로세움 본체는 LocalBanana와 같은 방향·부서진 정도·보이는 면·비례(8.1), "
    "팔각형 받침대 없음(8.2), 벡터 일러스트(AO·조명·그림자 0, 8.3), Comfy 재구성 0(8.4). 12:49 철회: 콜로세움 둘레에 LocalBanana 조경 배치를 옮겨 오지 않고 승인 설계의 히어로 군 구성을 따른다",
    "0 통합 루프(기준선-최종본 0-1절, 12:18): 배치 설계안 d{N}과 와이어프레임 b{N}을 한 AAA 루프에서 함께 만든다. 단일 원천 = .work/design/d{N}/out/spec.json(current 링크). 제작 단계 면제 표시는 쓰지 않는다(면제 없음)",
]
# 그림체(기준선 8.3·0-1): 벡터 일러스트, 면 톤은 방향별 고정 평면색만
ISO_TONE = {"top": 1.0, "left": 0.86, "right": 0.68}
SHADOW_EXPAND_MM = 0.0
STYLE_RULE = "AO·조명·그림자 0, ISO_TONE 1.0/0.86/0.68(윗면·왼면·오른면 고정 평면색), 그림자 확장 0mm. 실사 재질·텍스처·블룸·안개·피사계 심도 0, Comfy 재구성 0"
# 렌더 결과 기준 RGB(±3): 종이 = 설계 BG, 땅 윗면 = 설계 GROUND. 판석·물은 Blender PAL 한 값씩(hero·ground·coast 공용)
REF_RGB = {"paper": (231, 208, 160), "ground_top": (236, 216, 172), "ground_hex": "#ECD8AC", "tol": 3,
           "slab": "PAL 'slab' 한 값(판석 길·네로 마당 판석)", "water": "PAL 'water' 한 값",
           "far_mix_with_ground": {"베수비오": 0.50, "포도밭 농장": 0.25, "알바노 구릉": [0.26, 0.46]}}

# 8.1 콜로세움 본체(D2). 방위 θ = atan2(평면 dY, 평면 dX): 0° 화면 오른쪽 아래, 45° 정면 아래, 135° 왼쪽, 225° 위, 315° 오른쪽
HERO_COLO_D5 = {
    "center_plan": [495.76, 124.72], "center_screen": [205.34, 272.24], "offset_from_landscape_plan": [-15.8, -11.8],
    "semi_axes_plan": [44.0, 36.6], "major_az_deg": 315.0, "arches": 40, "tier_lines_z": [11.5, 24.5, 37.0, 53.0],
    # 외벽 높이(θ 구간, 화면 수직 mm). [t0, t1, h_lo, h_hi, 메모]. 338~18°처럼 0°를 지나는 구간은 t1 < t0로 적는다
    "wall_profile": [
        [100, 104, 41.0, 41.0, "앞쪽 끝 경사 부벽"], [104, 108, 46.0, 46.0, "경사 부벽"], [108, 112, 50.0, 50.0, "경사 부벽"],
        [112, 205, 53.0, 53.0, "왼쪽~뒤-왼쪽 4층"], [205, 209, 44.0, 44.0, "뒤쪽 끝 수직 절단"],
        [209, 322, 33.5, 37.0, "뒤~오른쪽 3층(일부 33.5)"], [322, 330, 31.0, 31.0, "3층 → 2층 계단"], [330, 338, 27.0, 27.0, "3층 → 2층 계단"],
        [338, 18, 18.0, 24.5, "앞-오른쪽 2층(윗선 들쭉날쭉)"], [18, 72, 14.0, 17.0, "경기장 앞 정면 1층 + 부서진 2층 토막(상한 17.0)"],
        [72, 80, 30.0, 30.0, "앞-왼쪽 3층"], [80, 100, 37.0, 37.0, "앞-왼쪽 3층"],
    ],
    "front_az": [18, 72], "front_h_max": 17.0,
    "second_ring": {"h": 37.0, "front_az": [10, 80], "front_h": [9.0, 12.0], "front_h_max": 12.0},
    "thickness_plan": {"outer_wall": 2.4, "outer_gallery": 2.8, "second_ring": 1.6},
    "cavea": {"depth_from_outer": [10.4, 22.7], "h": [24.0, 4.4], "podium_wall": [22.7, 23.9],
              "stepped_seat_az": [[238, 360], [0, 48]], "elsewhere": "방사벽 + 짙은 빈칸(무너진 볼트)"},
    "arena_semi_axes_plan": [20.1, 12.7],
    "floor": {"u_split": -2.0, "wood": "u ≥ −2.0 복원 나무 바닥(Z 0.6, 난간)", "wood_frac": 0.55, "wood_z": 0.6},
    "hypogeum": {"u_lt": -2.0, "floor_z": -4.0, "rings_k": [0.86, 0.72, 0.58, 0.44, 0.30], "central_passage_half": 0.9,
                 "partition_every_deg": 12, "partition_k": [0.33, 0.97], "wall_t": [0.45, 0.55]},
    "building_screen_box": [157.29, 177.35, 302.79, 317.14], "building_wh": [145.5, 139.79],
    "base_side_mm": 0.0,
    "discarded_d4": "ring_ratio 0.74, 벽 60/28/12, 원형 고리, 가로벽 격자 하이포게움 표(폐기)",
}
# 허용 오차(8.1 검사)
HERO_COLO_TOL = {"semi_axes": 0.05, "width_ratio": [0.53, 0.02], "wall_h": 0.5, "wood_frac": [0.55, 0.03], "box_mm": 1.5}

# 8.2 받침 없음 + 히어로 둘레(사용자 16:13·16:14: 땅 바탕뿐. 광장·판석·길·인물·노점·공사장·둘레 나무 없음, 네로 거상 받침과 작은 마당만 곁에)
HERO_LANDSCAPE_D5 = {
    "center_plan": [462.34, 173.66], "center_screen": [134.0, 280.0], "reserve_R_plan": 90.0,
    "reserve_screen_box": [23.71, 216.4, 244.21, 343.6], "rep_R_plan": 83.1, "rep_screen_w": 203.5,
    "base_side_mm": 0.0, "octagon": False, "front_cut": False,
    "top_z": {"네로 마당 판석": 0.12},
    "nero_yard_screen": [82.3, 437.0, 108.3, 469.0],
    "composition_1614": ["콜로세움 건물(기단 계단 2단 포함)", "네로 거상 받침(작은 마당 포함)"],
}
# 12:49 사용자 철회: LocalBanana 조경 배치를 복제한 부품(승인 설계에 없던 것)은 히어로 둘레에 두지 않는다
LB_REPLICA_KEYS = ("단칸 아치", "벽돌 담", "작은 신전", "열주 폐허", "6주 신전", "육주 신전", "문 폐허", "트래버틴 고리", "트래버틴 포장 고리", "포장 고리", "갈래길")
# 위계(D4): 히어로 = 콜로세움 건물(단일 오브젝트, 사용자 16:14). 사전 = 투영 상자끼리, 사후 = 그린 외곽 상자끼리
HERO_GROUP_BOX = [98.5, 194.44, 319.0, 349.64]
HERO_SIL_OVER_OTHER = 1.2                     # 콜로세움 건물 실루엣 ≥ 다른 건물 실루엣 각각 × 1.2
L5_DRAW_SCALE = 1.04                          # 메텔라 설계 그림: 사양 상자 중심 기준 1.04배(x 420에서 잘림) → 그린 상자 ≥ 4,530
# 인물 군(⑧): 12:49 철회로 LocalBanana 4곳(G1~G4) 배치는 필수가 아니다. 승인 설계 3곳 이상, 키는 D8 히어로 축척
CROWD_MIN = 4
CROWD_N = (5, 7)
CROWD_GAP = (3.5, 5.0)
# D8 사람 키(화면 mm, 발~머리, 폭 = 키 × 0.32)와 소품 비례(사람 키 대비)
PERSON_H = {"hero": [4.9, 4.6, 5.2], "hero_edge_road_15mm": [3.4, 3.2, 3.6], "map": [2.4, 2.2, 2.6], "far": [1.8, 1.6, 2.0]}
PERSON_W_RATIO = 0.32
PROP_RATIO = {"노점 높이": 1.4, "노점 폭": 1.8, "암포라": 0.45, "수레 길이": 2.2, "사이프러스(히어로)": [3.3, 4.3], "사이프러스(그 밖)": [2.5, 3.0],
              "올리브(히어로)": 2.9, "올리브(그 밖)": 2.2, "우산소나무": 3.0}
# D5 확대 창 Z1 새 출발점(공사장 거푸집 오른쪽 면 = 다져 넣은 층)
Z1_START = (232.0, 396.8)
Z1_LEADER_END = (272.38, 420.11)
Z1_LEADER = {"dir_deg": 30.0, "bends": 0, "len": 46.6, "lw": 0.30, "dot_d": 0.9}
Z1_A_MARK = (233.75, 393.77)
WORKSITE_BOX_D5 = [208.0, 386.0, 250.0, 410.0]
PRINT_FORBIDDEN_BASE = r"기초 절개|받침 앞 변|받침"           # 인쇄 글: 콜로세움 받침 서술 0
PRINT_BASE_ALLOWED = r"네로|거상|\(벽돌 마감\)\s?받침"          # 네로 거상 받침 문장만 허용
# D7 R7·폰스 아일리우스 높이 접속(평면 mm, Z mm)
R7_LINK_D5 = {"r7_x": [484.98, 494.22], "ramp_y": [294.76, 304.76], "ramp_z": [0.0, 3.0], "north_end": [489.6, 250.4],
              "deck_z": 3.0, "deck_x": [486.1, 493.1], "plinth_z": 5.0,
              "steps": {"y": [325.9, 329.9], "tread_mm": 2.0, "n": 2, "tread_z": [3.67, 4.33], "risers": [0.67, 0.67, 0.67]}}
# D17 인쇄 선 굵기(mm). 더 가는 보조선은 print:false로 표시하고 인쇄에서 뺀다
PRINT_LINE_MM = {"내부선": [0.10, 0.20], "지시선": 0.30, "콜아웃 테두리": 0.25, "Z1 테두리": 0.60, "P5 계단선": 0.35}
PRINT_LINE_MIN = 0.10
PRINT_LINE_TOL = 0.01
P5_STAIR = {"pts": [[312.0, 545.0], [341.67, 545.0], [341.67, 543.5], [372.33, 543.5], [372.33, 542.0], [400.0, 542.0]], "tip": [402.0, 542.0],
            "lw": 0.35, "fill": False, "text_clear_mm": 1.5, "tol_mm": 0.3}
# 와이어프레임 밀도(b{N} map.png, 무대 [0,92,420,505]에서 땅색 ±6·물색이 아닌 화소 비율)
WIRE_DENSITY = {"target_pct": 36.0, "min_pct": 34.0, "ground_tol": 6, "stage": [0, 92, 420, 478]}
# D11 앵커(숨긴 Empty ANCHOR_{대상}_{역할}). 점이 None이면 d4 spec labels[].target_pt·leaders 끝·pair_marks map_pt가 잠정 점이다
BLENDER_ANCHORS = [
    ("hero", "HERO_label", (269.97, 244.0)), ("hero", "NERO_label", None), ("hero", "HERO_c5", (246.5, 323.0)),
    ("city", "L1_label", None), ("city", "L1_m4", (168.0, 160.0)), ("city", "L2_label", None), ("city", "L2_m3", (141.5, 306.6)),
    ("city", "L7_label", (212.0, 170.0)), ("city", "L7_m2", (75.6, 254.0)), ("city", "L9_label", None),
    ("baths", "L3_label", None), ("baths", "L4_label", None), ("baths", "L4_m1", (372.0, 163.0)),
    ("suburb", "L5_label", None), ("suburb", "L5_c4", None),
    ("coast", "L6_label", None), ("coast", "L6_c2", None), ("coast", "L8_label", None),
]
ANCHOR_SNAP_MM = 6.0                           # 정보 층: 6mm 안이면 앵커에 맞추고, 밖이면 맞추지 않고 기록
ANCHOR_TOL_MM = 0.5                            # 사후 ⑰: 맞춘 지시선 끝–앵커 ≤ 0.5mm
# D12 무대·합성, D13 높이
BLENDER_STAGE = {"ground_top_screen": [0.0, 92.0, 420.0, 478.0], "ground_z": 0.0, "sea_z": -9.7, "sea_bleed_screen_y": 594.0,
                 "coast_section_mm": 10.0, "coast_section_layers": 3, "top_edge_min_y": 93.0, "no_object_zone": [302.0, 20.0, 402.0, 92.0],
                 "compose": "종이 → Blender map.png(투명 바탕) → 정보 층(.work/design/d{N}/out/info/info_layer.png)", "poster_px_per_mm": 3, "crop_px_per_mm": 8}
HEIGHTS_Z = {"땅 윗면": 0.0, "강 수면": -2.0, "바다": -9.7, "내항·운하": -2.0, "길 윗면": [0.285, 0.31], "네로 마당": [0.12, 0.24], "건물 포장 턱 최대": 0.3,
             "겹치는 면 Z 차 최소": 0.05, "하이포게움 바닥": -4.0, "나무 바닥": 0.6}
REBUILD_ORDER = ["설계 d{N} 병합", "current → d{N}", "hero", "city", "baths", "suburb", "coast", "ground(X_CUT_* 적용, 맨 끝)",
                 "b{N} 렌더(전체 3 px/mm, crops 8 px/mm)", "export_sil → rounds/b{N}/sil.json", "d{N} render.py INFO_ONLY=1 → out/info/", "합성 rounds/b{N}/poster.png"]
# 사양 정리(d5): 조명 방향 지정·그림자 허용·제작 단계 면제 문구 0(사용자 원문 인용 제외)
SPEC_FORBIDDEN_D5 = r"왼쪽 위 하나|\[제작 단계 과제\]|빛 번짐|shadow 레이어|그림자[^0]{0,8}허용"


# ═════════════ d5 순수 기하 도우미(사전·사후 검사·자체 시험 공용, map을 import하지 않는다) ═════════════
def isnum(a):
    return isinstance(a, (int, float)) and not isinstance(a, bool)


def first_of(d, *keys):
    """dict에서 처음으로 값이 있는 열쇠의 값"""
    if not isinstance(d, dict):
        return None
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def pair_of(v):
    """[a, b] · (a, b) · {a, b}/{rx, ry}/{x, y} → (a, b)"""
    if isinstance(v, (list, tuple)) and len(v) >= 2 and isnum(v[0]) and isnum(v[1]):
        return (float(v[0]), float(v[1]))
    if isinstance(v, dict):
        a, b = first_of(v, "a", "rx", "major", "semi_major", "X", "x"), first_of(v, "b", "ry", "minor", "semi_minor", "Y", "y")
        if isnum(a) and isnum(b):
            return (float(a), float(b))
    return None


def plan_az(dX, dY):
    """평면 방위 θ = atan2(dY, dX) (0~360). roma_kit.plan_az와 같은 규약"""
    return math.degrees(math.atan2(dY, dX)) % 360.0


def az_in(theta, t0, t1):
    """θ가 구간 [t0, t1) 안인가(0°를 지나는 t1 < t0, 또는 t1 > 360 모두 받는다)"""
    th, a, b = theta % 360.0, float(t0), float(t1)
    if b - a >= 360.0:
        return True
    a, b = a % 360.0, b % 360.0
    return a <= th < b if a < b else (th >= a or th < b)


def parse_profile(v):
    """외벽 높이 표 → [(t0, t1, lo, hi, 메모)]. [t0,t1,h] · [t0,t1,lo,hi,메모] ·
    {t0/az0/th0 + t1/az1/th1 | range/az/deg [a,b]} + {h | [lo,hi] | h_range | h_lo·h_hi | h_min·h_max | h0·h1} 모두 받는다"""
    out = []
    for e in (v or []):
        t0 = t1 = lo = hi = None
        note = ""
        if isinstance(e, (list, tuple)) and len(e) >= 3 and all(isnum(x) for x in e[:3]):
            t0, t1 = float(e[0]), float(e[1])
            if len(e) >= 4 and isnum(e[3]):
                lo, hi = float(min(e[2], e[3])), float(max(e[2], e[3]))
                note = str(e[4]) if len(e) > 4 else ""
            else:
                lo = hi = float(e[2])
                note = str(e[3]) if len(e) > 3 else ""
        elif isinstance(e, dict):
            rg = first_of(e, "range", "az", "theta", "deg", "az_deg", "theta_deg")
            if isinstance(rg, (list, tuple)) and len(rg) == 2 and all(isnum(x) for x in rg):
                t0, t1 = float(rg[0]), float(rg[1])
            else:
                a_, b_ = first_of(e, "t0", "az0", "th0", "theta0", "from"), first_of(e, "t1", "az1", "th1", "theta1", "to")
                if isnum(a_) and isnum(b_):
                    t0, t1 = float(a_), float(b_)
            h = first_of(e, "h", "height", "h_mm")
            if isinstance(h, (list, tuple)) and len(h) == 2 and all(isnum(x) for x in h):
                lo, hi = float(min(h)), float(max(h))
            elif isnum(h):
                lo = hi = float(h)
            hr = first_of(e, "h_range", "range_h")
            if isinstance(hr, (list, tuple)) and len(hr) == 2:
                lo, hi = float(min(hr)), float(max(hr))
            for ka, kb in (("h_lo", "h_hi"), ("h_min", "h_max"), ("h0", "h1")):
                if isnum(e.get(ka)) and isnum(e.get(kb)):
                    lo, hi = float(min(e[ka], e[kb])), float(max(e[ka], e[kb]))
            if hi is None and isnum(e.get("h_max")):
                hi = float(e["h_max"])
                lo = float(e["h_min"]) if isnum(e.get("h_min")) else hi
            note = str(first_of(e, "part", "note", "name") or "")
        if None not in (t0, t1, lo, hi):
            out.append((t0, t1, lo, hi, note))
    return out


def wall_h(profile, theta):
    """θ에서의 외벽 높이 (lo, hi). 표에 없으면 None"""
    for t0, t1, lo, hi, _n in profile:
        if az_in(theta, t0, t1):
            return (lo, hi)
    return None


def ellipse_r(theta, a, b, major_az):
    """평면 타원(반축 a·b, 장축 방위 major_az) 중심에서 방위 θ 쪽 둘레점까지의 거리"""
    d = math.radians(theta - major_az)
    return 1.0 / math.sqrt((math.cos(d) / a) ** 2 + (math.sin(d) / b) ** 2)


def colo_building_polys(center_plan, semi_axes, major_az, profile, step=2.0):
    """콜로세움 본체 화면 실루엣 다각형들: 바닥 타원 + θ마다 외벽 사각(바닥 → 윗선 hi)"""
    (X0, Y0), (a, b) = center_plan, semi_axes
    maz = 315.0 if major_az is None else major_az
    n = int(round(360.0 / step))
    pts = []
    for k in range(n + 1):
        th = k * step
        r = ellipse_r(th, a, b, maz)
        pts.append((X0 + r * math.cos(math.radians(th)), Y0 + r * math.sin(math.radians(th))))
    out = [[to_screen(X, Y) for X, Y in pts[:-1]]]
    for k in range(n):
        h = wall_h(profile or [], (k + 0.5) * step)
        if not h or h[1] <= 0:
            continue
        (Xa, Ya), (Xb, Yb) = pts[k], pts[k + 1]
        out.append([to_screen(Xa, Ya), to_screen(Xb, Yb), to_screen(Xb, Yb, h[1]), to_screen(Xa, Ya, h[1])])
    return out


def polys_bbox(polys):
    xs = [p[0] for pg in polys for p in pg]
    ys = [p[1] for pg in polys for p in pg]
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None


def asset_px(width_mm, ppi=300):
    """자산 고유 픽셀 폭 = 배치 폭 ÷ 25.4 × ppi(반올림)"""
    return int(round(width_mm / 25.4 * ppi))


def in_stage(x, y):
    """점이 무대(STAGE ∪ STAGE_EXT) 안에 있는가. d4는 STAGE_EXT가 비어 STAGE만 본다"""
    return any(r[0] <= x <= r[2] and r[1] <= y <= r[3] for r in STAGE_RECTS)


def to_screen(X, Y, Z=0.0):
    return (C30 * (X - Y), 0.5 * (X + Y) - Z)


def to_plan(x, y):
    a = x / C30
    return ((a + 2 * y) / 2.0, (2 * y - a) / 2.0)


def plan_rect_screen_box(X0, X1, Y0, Y1, h=0.0):
    pts = [to_screen(X, Y) for X in (X0, X1) for Y in (Y0, Y1)]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return [round(min(xs), 1), round(min(ys) - h, 1), round(max(xs), 1), round(max(ys), 1)]


# 사용자 16:13·16:14: 콜로세움 둘레에는 땅 바탕뿐이다(광장·길·집·나무·밭·인물·소품 없음). 아래 반지름은 비워 두는 땅의 기준일 뿐 검사에 쓰지 않는다
NOFILL_R_PLAN = 90.5
DENSITY_MIN_PCT = 26.0          # 설계 밀도 하한(전체 무대, Core 건물 실루엣). 사용자 16:14로 Core만 남아 31.5 → 26.0. 203X 실측 권장 26~40%(도쿄 25.3·파리 27.1·타이베이 30.1·상하이 31.5·베이징 37.3, 중앙값 ≈ 31%)
LANDSCAPE_REP_W = 203.5         # 8.1 비례 기준 폭(옛 조경 대표 원 R 83.1의 화면 폭). 땅에 그리는 것은 없고 비례 기준으로만 쓴다
STALLS_SCREEN = []   # 사용자 16:14: 노점은 지도에서 지웠다
