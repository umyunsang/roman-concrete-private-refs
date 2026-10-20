# -*- coding: utf-8 -*-
"""설계안 공용 기초(상수·좌표 변환·인쇄 규칙). 담당: global
하위 호환: 기존 이름(C30·T30·SQ3·POSTER·STAGE·STAGE_AREA·POSTER_AREA·to_screen·to_plan·plan_rect_screen_box)은 이름과 값을 바꾸지 않는다."""
import math

C30 = math.cos(math.radians(30))
T30 = math.tan(math.radians(30))
SQ3 = math.sqrt(3)

POSTER = (420.0, 594.0)
STAGE = (0.0, 92.0, 420.0, 505.0)          # 지도 무대 x0, y0, x1, y1 (베이징 실측 틀)
STAGE_AREA = (STAGE[2] - STAGE[0]) * (STAGE[3] - STAGE[1])
POSTER_AREA = POSTER[0] * POSTER[1]

# ── 사용자 검토(2026-10-19 02:24): 상단 오른쪽 R 자리와 하단 띠 오른쪽 T 자리를 지도 무대로 돌려준다 ──
# 무대 = STAGE ∪ STAGE_EXT. 위 확장(298,20)~(420,92) = '가장 먼 곳'(베수비오·알바노 구릉·먼 밭),
# 아래 확장(312,505)~(420,568) = 남동 교외 밭·포도밭의 고요한 영역(글·틀 0개).
STAGE_EXT = [[298.0, 20.0, 420.0, 92.0], [312.0, 505.0, 420.0, 568.0]]
STAGE_AREA_EXT = 189048.0                  # 173,460 + 8,784 + 6,804 (mm²)
STAGE_RECTS = [list(STAGE)] + [list(r) for r in STAGE_EXT]

# 사용자 검토로 인쇄 지면에서 뺀 패널 id(사양 조립·검사·미리보기가 걸러 낸다. panels가 지우면 걸러 낼 것이 없을 뿐이다)
REMOVED_PANEL_IDS = ("R", "T")
PRINT_PANEL_IDS = ("L", "B", "D", "S")

# 인쇄 글 금지 패턴(작업 이름·티어 이름·치수·검사·설계 주석). m·km 단위와 '모식'은 허용한다.
PRINT_FORBIDDEN = r"Core|Basic|Detail|Support|위계|최종 배치|다이어그램|무대|꼬리표|자리|사양|검사|mm"
# 영문 티어 이름은 대소문자를 가리지 않고 영문자 경계로도 잡는다(예: 'CORE · …' 꼬리표)
PRINT_FORBIDDEN_CI = r"(?<![A-Za-z])(core|basic|detail|support)(?![A-Za-z])"

# 인쇄 색: 정보 잉크 한 색과 강조색(폼페이 레드). 티어 색은 인쇄 지면에서 0회.
INK_L = (58, 42, 28)
ACCENT = (200, 34, 54)
TIER_COLORS = {"Core": (47, 107, 58), "Basic": (63, 58, 160), "Detail": (208, 101, 14), "Support": (47, 127, 134)}

# 서체 결정 7(글자면 = 잉크 높이: 국문 '한', 영문 'H' 대문자 높이, mm). 사후 검사 허용 오차 ±0.1, 피치 ±0.05.
TYPE_FACES = {
    "label_en": 3.8, "label_ko": 3.8, "label_sup": 2.1, "label_body": 3.0, "label_pitch": 4.15, "label_scale": 1.00,
    "tag": 2.6,
    "panel_head_en": 7.4, "panel_head_ko": (3.6, 3.8), "s_head_en": 5.0, "s_head_ko": 2.8,
    "step": 3.0, "subtitle": 2.8,
    "body": 2.6, "body_pitch": 3.9,
    "note": 2.1, "note_pitch": 3.0,
    "box_text_clear": 3.0,
}

# 출력 규격(사양에만 적는다)
OUTPUT = {
    "final": {"size_mm": [420, 594], "ppi": 300, "px": [4961, 7016]},
    "review": {"px_per_mm": 3, "px": [1260, 1782]},
    "asset_native_px": "배치 폭 mm ÷ 25.4 × 300",
    "line_mm": {"지시선": 0.30, "콜아웃 테두리": 0.25, "Z1 테두리": 0.6, "내부선": [0.10, 0.20]},
}


def asset_px(width_mm, ppi=300):
    """자산 고유 픽셀 폭 = 배치 폭 ÷ 25.4 × ppi(반올림)"""
    return int(round(width_mm / 25.4 * ppi))


def in_stage(x, y):
    """점이 무대(STAGE ∪ STAGE_EXT) 안에 있는가"""
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
