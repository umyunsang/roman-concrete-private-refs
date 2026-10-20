# -*- coding: utf-8 -*-
"""설계안 공용 기초(상수·좌표 변환·인쇄 규칙). 담당: global
하위 호환: 기존 이름(C30·T30·SQ3·POSTER·STAGE·STAGE_AREA·POSTER_AREA·to_screen·to_plan·plan_rect_screen_box)은 이름과 값을 바꾸지 않는다.
d4: 무대 확장(STAGE_EXT)을 해제하고(R·T 확장 0), 인쇄 패널을 L·P2·B·D·S·P5 6개로 한다(기준선 7절, 사용자 선택 2026-10-19 03:10)."""
import math

C30 = math.cos(math.radians(30))
T30 = math.tan(math.radians(30))
SQ3 = math.sqrt(3)

POSTER = (420.0, 594.0)
STAGE = (0.0, 92.0, 420.0, 505.0)          # 지도 무대 x0, y0, x1, y1 (베이징 실측 틀)
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
PRINT_PANEL_IDS = ("L", "P2", "B", "D", "S", "P5")
PANEL_COUNT_RANGE = (5, 7)                 # 도시편 근거(사용자 결정 2절)

# 필수 요소(사전 검사 (a)·사후 검사 ⑬). 하나라도 없으면 실패다
REQUIRED_LANDMARK_IDS = tuple("L%d" % k for k in range(1, 10))
REQUIRED_ROAD_IDS = ("R7",)
# 짝 표지 개수(사후 검사 ⑬): 글자 A~D와 숫자 1~4(P2 칸 ↔ 지도)
REQUIRED_MARKS = {"A": 3, "B": 2, "C": 2, "D": 2, "1": 2, "2": 2, "3": 2, "4": 2}
# 표준 랜드마크 하한(신규 L7~L9 포함, 기존 최소 메텔라 4,620과 같은 등급)
LANDMARK_MIN_AREA = 4500.0
# 히어로 ÷ 표준 랜드마크 중앙값 레퍼런스 범위(청와대 4.5 ~ 파리 7.9)
HERO_OVER_MEDIAN_RANGE = (4.5, 7.9)

# 인쇄 글 금지 패턴(작업 이름·티어 이름·치수·검사·설계 주석·사용자 검토로 뺀 패널 이름·보류 문구). m·km 단위와 '모식'은 허용한다.
PRINT_FORBIDDEN = r"Core|Basic|Detail|Support|위계|최종 배치|다이어그램|무대|꼬리표|자리|사양|검사|mm|위치도|연대기|자리 예약|선택 대기|저탄소|41%|29%"
# 영문 티어 이름은 대소문자를 가리지 않고 영문자 경계로도 잡는다(예: 'CORE · …' 꼬리표)
PRINT_FORBIDDEN_CI = r"(?<![A-Za-z])(core|basic|detail|support)(?![A-Za-z])"
# 인쇄 문장 금지(기준선 4·7절): 조각상 문장·반죽 붓기·퐁 뒤 가르·콜로세움 이름 유래(이번 회차 인쇄 0)
PRINT_FORBIDDEN_SENTENCES = r"콘크리트로 만든 조각|콘크리트로 빚은 거상|로마 콘크리트는 저탄소|(반죽|콘크리트|모르타르)\S{0,2}\s?(부었|부어|붓는|붓다)|붓다|퐁 뒤 가르|Pont du Gard|유래"
# 치수 인쇄 금지 대상(바실리카 높이·영묘 치수·극장 지름·거상 치수): 이 라벨·주석에는 '숫자 + m'를 쓰지 않는다
PRINT_NO_DIMENSION_KEYS = ("바실리카", "basilica", "maxentius", "영묘", "mausoleum", "hadrian", "극장", "theatre", "marcellus", "네로", "거상", "colossus")
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
