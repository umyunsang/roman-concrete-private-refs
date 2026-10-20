# -*- coding: utf-8 -*-
"""설계안 — Core 지도(히어로·랜드마크·강·바다·길·수도교·소품·지형·심은 지면·포르투스·지리). 담당: map

d4 변경(사용자 검토 2026-10-19 02:24 + 사용자 선택 03:10, 기준선 7절)
- 무대 확장(R·T 자리) 해제: 'R 자리 먼 캄파냐 밭'·'R 자리 먼 밭'·'T 자리 남동 포도밭'과 남동 교외 밭의 T 확장·띠 밑 바다 귀퉁이를 지웠다.
  지도 무대는 기본 STAGE (0,92)~(420,505)뿐이다. 두 옛 자리는 panels의 P2·P5 Basic 패널이 쓴다.
- 베수비오 군을 지도 무대 오른쪽 위(가장 먼 곳)로 내렸다: 산 (360,98)~(418,138) · 포도밭 농장 (366,122)~(408,144) · 알바노 구릉 띠 (318,122)~(420,162).
  앞 능선이 밑동 앞쪽 x 360~418 전체를 3~5mm 연속으로 가리고, 농장 지면과 앞 구릉은 한 지형 실루엣이다(가운데 일괄 하향 삭제).
- 랜드마크 3개 추가(L7 막센티우스 바실리카·L8 하드리아누스 영묘와 폰스 아일리우스·L9 마르켈루스 극장), 새 길 R7, 소품 '네로 청동 거상과 콘크리트(벽돌 마감) 받침'.
  새 건물은 평면 원본(plan)에서 화면 외곽(poly_screen·ground_screen·parts_screen)과 투영 상자를 계산한다.
- 소품 재배치(석회 가마·바지선 2·오스티아), 포르투스 등대섬 78°·반지름 22, 운하 plan_y = 그린 끝점, 하이포게움 통과 개구부·외곽 회랑·옆방, 수도교 관통 아치."""
from v2_base import *  # noqa: F401,F403

# ═════════════ Core 히어로: 콜로세움 ═════════════
HERO_C = (250.0, 318.0)          # 화면 중심
HERO_R = 90.0                    # 팔각 받침 외접 반지름(평면)
HERO_SIDE = 7.0                  # 받침 앞쪽 세 변 옆면(지층 3겹) 높이
HERO_RING = 0.74                 # 외벽 고리 평면 반지름 비
# 벽 높이(평면 방위각 범위, 높이 mm). LocalBanana 원래 방향: 4층 외벽 조각이 뒤-왼쪽(화면 왼쪽 위)
HERO_WALLS = [
    {"part": "4층 외벽 조각(뒤-왼쪽)", "t0": 150, "t1": 235, "h": 60.0},
    {"part": "2층 고리(뒤-오른쪽)", "t0": 235, "t1": 330, "h": 28.0},
    {"part": "무너진 앞쪽 고리(관람석 층·하이포게움이 보임)", "t0": 330, "t1": 510, "h": 12.0},
]
HERO_C_PLAN = to_plan(*HERO_C)

# 히어로 내부 형태(결정 17, LocalBanana 참조의 하이포게움 미로·관람석 통로·안쪽 아케이드). map이 적고 render가 그린다
HERO_INTERIOR = {
    "hypogeum": {"exposed": "앞쪽 반쪽", "floor_drop_mm": 5.0, "wall_t_mm": 1.5,
                 "corridors": "장축 중심 1 + 평행 2(간격 6mm)", "cross_walls": 7, "cross_gap_mm": 5.0,
                 "note": "노출 반쪽의 바닥을 나무 바닥보다 화면 수직 5mm 아래로 낮춘다. 통로 벽 두께 1.5mm, 장축 중심 통로 1 + 평행 통로 2(간격 6mm) + 가로벽 7(간격 5mm)"},
    "seating": {"tiers": 4, "radial_stairs": 12, "stair_every_deg": 30, "stair_w_mm": 2.5, "vomitoria": "계단 자리마다",
                "note": "관람석 4층 구분, 방사 계단 12개(30°마다, 폭 2.5mm), 계단 자리마다 출입구"},
    "arcade": {"inner_face_mm": 1.5, "depth_layers": 2, "layer_gap_mm": 3.0,
               "note": "4층 외벽 조각: 아치 안쪽 면 1.5mm가 보이고, 바깥 아케이드 + 안쪽 회랑의 2 깊이 층(간격 3mm)"},
    "keep": "히어로 상자 203.8×173.0mm, 4층 조각 뒤-왼쪽",
}


def _hypogeum_openings(rf=34.0, wall_t=1.5, gap_c=6.0, n_cross=7, cross_gap=5.0, w_open=3.0, corridor_w=3.5, clear=0.5):
    """하이포게움 가로벽 7개의 통과 개구부 자리(화면 mm, 아레나 중심 기준).
    가로벽 k는 화면 dx = −k·cross_gap(노출 반쪽 = 화면 왼쪽)에 있고, 장축 중심 통로(dy 0)에서 구덩이 가장자리까지의 반길이 L(화면 세로 mm)을 가진다.
    개구부 중심 = 홀수 번째 L/3, 짝수 번째 2L/3(양쪽 ±dy). 장축 방향 벽(dy ±3·±9, 두께 1.5)이나 외곽 회랑(가장자리 안쪽 3.5mm)과
    0.5mm 안으로 겹치면 가장 가까운 허용 구간(평행 통로 안 또는 바깥 옆방 칸)으로 옮긴다. rf = render의 아레나 바닥 반지름(평면, 현재 34)."""
    ks, kt = 1.2247, 0.7071
    walls = [abs(f * gap_c) for f in (0.5, 1.5)]                       # 장축 방향 벽 중심 |dy| 3, 9
    out = []
    for k in range(1, n_cross + 1):
        s = k * cross_gap / ks + wall_t / ks / 2.0
        if s >= rf:
            continue
        L = kt * math.sqrt(rf * rf - s * s)
        f = 1.0 / 3.0 if k % 2 else 2.0 / 3.0
        c0 = f * L
        hi = L - corridor_w - clear - w_open / 2.0                       # 외곽 회랑 안쪽 끝까지
        ivs = []
        lo = 0.0
        for wc in walls:
            a, b = wc - wall_t / 2.0 - clear - w_open / 2.0, wc + wall_t / 2.0 + clear + w_open / 2.0
            ivs.append([lo, a])
            lo = b
        ivs.append([lo, hi])
        ivs = [[round(a, 2), round(b, 2)] for a, b in ivs if b >= a]
        best = None
        for a, b in ivs:
            c = min(max(c0, a), b)
            if best is None or abs(c - c0) < abs(best - c0):
                best = c
        zone = "평행 통로" if best is not None and best < walls[1] else "바깥 옆방 칸"
        out.append({"k": k, "screen_dx_mm": -k * cross_gap, "half_len_mm": round(L, 2), "rule_frac": "1/3" if k % 2 else "2/3",
                    "rule_center_mm": round(c0, 2), "opening_center_dy_mm": [round(-best, 2), round(best, 2)] if best is not None else None,
                    "opening_w_mm": w_open, "zone": zone, "moved": bool(best is not None and abs(best - c0) > 0.01)})
    return out


HERO_INTERIOR["hypogeum"].update({
    "cross_wall_openings": {"w_mm": 3.0, "count": 7, "stagger": "홀수 번째 = 장축 중심 통로에서 바깥쪽 1/3, 짝수 번째 = 2/3(양쪽 ±dy 대칭)",
                            "walls": _hypogeum_openings(),
                            "note": "가로벽마다 폭 3.0mm 통과 개구부. 장축 방향 벽(두께 1.5mm)이나 외곽 회랑과 0.5mm 안으로 겹치는 자리는 가장 가까운 허용 구간으로 옮겼다(moved). "
                                    "그 결과 홀수 벽은 평행 통로를, 짝수 벽은 바깥 옆방 칸을 터서 길이 엇갈리는 미로가 된다. 가로벽 윗면 띠는 개구부 자리에서 끊는다"},
    "outer_corridor": {"w_screen_mm": 3.5, "along": "노출 반쪽 둘레(구덩이 곡선 가장자리 안쪽)",
                       "note": "참조(LocalBanana)의 곡선 외곽 회랑. 가로벽은 이 회랑 안쪽 변에서 멈춰 회랑이 끊기지 않는다. 회랑 바닥은 구덩이 바닥과 같은 높이"},
    "side_rooms": {"where": "가로벽 사이의 바깥 칸(바깥쪽 장축 방향 벽 |dy| 9.75mm 바깥 ~ 외곽 회랑 안쪽 변)",
                   "note": "옆방은 짝수 벽 개구부와 외곽 회랑 쪽 문으로 이어진다. 바닥은 구덩이 바닥과 같고, 방마다 윗면 띠 1.5mm로 칸을 구분한다"},
})


def hero_oct():
    X0, Y0 = HERO_C_PLAN
    return [to_screen(X0 + HERO_R * math.cos(math.radians(22.5 + 45 * k)), Y0 + HERO_R * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]


def hero_ring_pt(theta_deg, z=0.0):
    X0, Y0 = HERO_C_PLAN
    r = HERO_RING * HERO_R
    return to_screen(X0 + r * math.cos(math.radians(theta_deg)), Y0 + r * math.sin(math.radians(theta_deg)), z)


# 앞 변 절개(기초 콘크리트 고리 단면)와 공사장(Core 소품, 히어로의 일부)
HERO_CUTAWAY = {"name": "앞 변 기초 절개(콘크리트 기초 고리 단면, 지층 받침 속)", "x": [208.0, 292.0],
                "note": "받침 앞 변(화면 아래 평평한 변) 옆면 x 208~292를 절개해 기초 고리 단면을 보인다. 왼쪽 부분은 공사장(거푸집·다짐), 오른쪽 부분(x 275 부근)은 확대 창 Z1의 출발점"}
WORKSITE = {"name": "콜로세움 기초 공사장(복원 장면)", "box": [208.0, 386.0, 250.0, 410.0],
            "note": "나무 거푸집, 다짐 막대 일꾼 2, 반죽 통, 재료 더미(생석회 흰색·화산재 붉은 갈색·골재 회색). 받침 앞 변 왼쪽 발치에 붙는다. 제작 과정 패널 ⑥의 지시선 도착점(거푸집 앞-왼쪽 면 중심, 공사장 지역 좌표 (6.5, 9.0, 2.0))"}

# ═════════════ 테베레강(평면 직교 꺾임 1회, 둥근 굽이) ═════════════
RIVER_Y = 314.0                  # ↘ 팔 중심선 = 평면 Y 314 (왼쪽 변 (0,314)에서 들어옴, 블리드)
RIVER_XB = 533.4                 # ↙ 팔 중심선 = 평면 X 533.4 (굽이 화면 (190, 423.7))
RIVER_FILLET = 12.0              # 굽이 중심선 반지름(평면)
RIVER_W1 = 16.0                  # ↘ 팔 화면 수직 폭(mm) — 도쿄 14.2~17.5, 타이베이 14~17
RIVER_W2 = 20.0                  # ↙ 팔(하구 쪽) 화면 수직 폭 — 상하이 앞팔 1.56배처럼 앞쪽을 넓게
COAST_Y = 380.0                  # 해안선 = 평면 Y 380 (화면 y = tan30·x + 380)


def river_centerline(step=4.0):
    pts = []
    x_start = 300.0
    x_end = RIVER_XB - RIVER_FILLET
    n = int((x_end - x_start) / step)
    for i in range(n + 1):
        pts.append((x_start + (x_end - x_start) * i / n, RIVER_Y, 0.0))      # (X, Y, 진행률 0=↘팔)
    cx, cy = RIVER_XB - RIVER_FILLET, RIVER_Y + RIVER_FILLET
    for i in range(1, 12):
        a = math.radians(-90 + 90 * i / 12)
        pts.append((cx + RIVER_FILLET * math.cos(a), cy + RIVER_FILLET * math.sin(a), i / 12))
    y0, y1 = RIVER_Y + RIVER_FILLET, COAST_Y + 14.0
    n = int((y1 - y0) / step)
    for i in range(n + 1):
        pts.append((RIVER_XB, y0 + (y1 - y0) * i / n, 1.0))
    return pts


def river_polygon():
    """평면에서 법선 방향으로 띄운 띠를 화면으로 투영한다. 반폭(평면) = 화면 수직 폭 / (2·cos30)."""
    cl = river_centerline()
    left, right = [], []
    for i, (X, Y, f) in enumerate(cl):
        a = cl[max(i - 1, 0)]
        b = cl[min(i + 1, len(cl) - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty)
        tx, ty = tx / L, ty / L
        nx, ny = -ty, tx
        hw = ((1 - f) * RIVER_W1 + f * RIVER_W2) / (2 * C30)
        left.append(to_screen(X + nx * hw, Y + ny * hw))
        right.append(to_screen(X - nx * hw, Y - ny * hw))
    return left + right[::-1]


RIVER_BEND_SCREEN = to_screen(RIVER_XB, RIVER_Y)
RIVER_MOUTH_SCREEN = to_screen(RIVER_XB, COAST_Y)
RIVER_ENTRY_SCREEN = (0.0, RIVER_Y)


def coast_y(x):
    return T30 * x + COAST_Y


COAST = [(0.0, COAST_Y), (round((505.0 - COAST_Y) / T30, 2), 505.0)]
SEA = [(0.0, COAST_Y), COAST[1], (0.0, 505.0)]
SEA_UNDER_BAND = [COAST[1], (round((568.0 - COAST_Y) / T30, 2), 568.0), (0.0, 568.0), (0.0, 505.0)]

# ═════════════ 길(±30°만, 평면 직선) ═════════════
# 화면 ↘ 직선 = 평면 Y 상수, 화면 ↗ 직선 = 평면 X 상수. 좌표는 그림 그대로다(렌더러는 늘이거나 줄이지 않는다).
# 길이 꺾이는 L자 모서리는 뒤에 오는 길의 시작을 앞 길의 바깥 변까지 반폭만큼 당겨 메운다(모서리 빈틈 0).
_HW8 = 8.0 / (2 * C30)                    # 폭 8mm 길의 평면 반폭 4.62
_ap0 = to_plan(340.0, 286.8)              # 콜로세움 받침 뒤-오른쪽 변 위의 문(평면 483.10, 90.50)
_R2_END = to_plan(224.0, 140.5)           # 시내 길 1의 욕장 쪽 끝(d2와 같음)
_R2_X = _R2_END[0]                        # 시내 길 1 = 평면 X 상수
_R2_Y0 = to_plan(71.56, 228.50)[1]        # 판테온 쪽 끝: 축 ↙ 49mm(렌더러 +30mm 연장 + 19mm)
_R3_P0 = to_plan(88.02, 169.0)            # 시내 길 2 시작(렌더러 +30mm 연장을 넣은 값) = 평면 Y 상수
_R5_X1 = 234.5 / C30 + _R2_END[1]         # 욕장 진입로 끝: 화면 x 234.5(욕장 지면 뒤-왼쪽 변)
_MET_X = 546.7                            # 메텔라 진입로 꺾임(평면 X)
_MET_Y = 85.9                             # 메텔라 진입로 1(평면 Y 상수)
_MET_Y1 = 95.2                            # 메텔라 진입로 2 끝(평면 Y) = 무덤 대지 뒤-오른쪽 변
ROADS = [
    {"id": "R1", "name": "아피아 가도(Via Appia, 주축 길)", "w": 16.0, "center_line": True,
     "plan": [(_ap0[0], _ap0[1]), (_ap0[0], _ap0[1] - 92.4 - 14.0)],
     "note": "콜로세움 받침 뒤-오른쪽 변(평면 법선 방향)의 문 (340.0, 286.8)에서 ↗로 나가 오른쪽 변 (420, 240.6) 밖 (432.1, 233.6)까지 블리드(렌더러에만 있던 끝 +14mm 연장을 사양 좌표에 넣었다). 흰 중앙선 1.6mm는 길 끝까지. 메텔라 무덤은 진입로 R6a·R6b로 잇는다. 바닥 글 'VIA APPIA 아피아 가도 → 캄파니아'"},
    {"id": "R2", "name": "시내 길 1(판테온 ↗ 카라칼라 욕장)", "w": 8.0, "center_line": False,
     "plan": [(_R2_X, _R2_Y0), (_R2_X, _R2_END[1])],
     "note": "판테온 광장 뒤 꼭짓점 ≈(76.7, 231.9)과 약 1.5mm 떨어진 (71.56, 228.50)에서 ↗로 카라칼라 욕장 왼쪽까지 (224.0, 140.5). 판테온 쪽 끝은 돔 뒤로 숨는다(렌더러의 시작 +30mm 연장 + 19mm를 사양 좌표에 넣었다). 콜로세움 뒤-왼쪽 4층 조각 위 약 60mm를 지난다"},
    {"id": "R3", "name": "시내 길 2(트라야누스 시장 ↘ 시내 길 1)", "w": 8.0, "center_line": False,
     "plan": [(_R3_P0[0], _R3_P0[1]), (_R2_X + _HW8, _R3_P0[1])],
     "note": "트라야누스 시장 지면 (88.02, 169.0)에서 ↘로 시내 길 1과 T자로 만난다. 끝은 시내 길 1의 먼 변까지(교점 +X 4.6mm)라 T자 빈틈이 없다(렌더러의 시작 +30mm·끝 +4.6mm 연장을 사양 좌표에 넣었다)"},
    {"id": "R4", "name": "하역장 길(콜로세움 앞-왼쪽 문 ↙ 테베레 하역장)", "w": 10.0, "center_line": False,
     "plan": [(HERO_C_PLAN[0], HERO_C_PLAN[1] + HERO_R * math.sin(math.radians(67.5)) + HERO_SIDE), (HERO_C_PLAN[0], RIVER_Y - RIVER_W1 / (2 * C30))],
     "note": "받침 앞-왼쪽 변 가운데 문에서 평면 법선 방향(↙)으로 강 오른쪽 둑의 하역장까지. 수레 1대"},
    {"id": "R5", "name": "욕장 진입로(시내 길 1 ↘ 카라칼라 욕장)", "w": 8.0, "center_line": False,
     "plan": [(_R2_X - _HW8, _R2_END[1]), (_R5_X1, _R2_END[1])],
     "note": "시내 길 1의 욕장 쪽 끝 (224.0, 140.5)에서 ↘로 꺾어 욕장 지면 뒤-왼쪽 변 (234.5, 146.6)에 닿는다(간격 0, Codex 지적: 욕장–R2 실제 지면 6.5mm 떨어짐). 축은 (224.0, 140.5) → (234.5, 146.6)이고, 띠 시작만 시내 길 1의 바깥 변까지 반폭 4.62mm 당겨 L자 모서리를 메운다(화면 (220.0, 138.2))"},
    {"id": "R6a", "name": "메텔라 진입로 1(아피아 가도 ↘)", "w": 8.0, "center_line": False,
     "plan": [(_ap0[0], _MET_Y), (_MET_X, _MET_Y)],
     "note": "아피아 가도 시작부(평면 483.1, 85.9 = 화면 344.0, 284.5)에서 ↘로 갈라져 콜로세움 받침 뒤-오른쪽 변을 따라 (399.1, 316.3)까지. Codex 지적: 메텔라 기단–아피아 가도 44.7mm 떨어짐"},
    {"id": "R6b", "name": "메텔라 진입로 2(↙ 무덤 대지)", "w": 8.0, "center_line": False,
     "plan": [(_MET_X, _MET_Y - _HW8), (_MET_X, _MET_Y1)],
     "note": "진입로 1의 끝에서 ↙로 꺾어 무덤 대지 뒤-오른쪽 변 (391.0, 321.0)에 닿는다. 축은 평면 (546.7, 85.9) → (546.7, 95.2)이고, 띠 시작만 진입로 1의 바깥 변까지 반폭 4.62mm 당겨 L자 모서리를 메운다(화면 (403.1, 314.0))"},
    {"id": "R7", "name": "다리 길(콜로세움 앞-왼쪽 변 ↙ 폰스 아일리우스)", "w": 8.0, "center_line": False,
     "plan": [(489.0, HERO_C_PLAN[1] + HERO_R * math.sin(math.radians(67.5)) + HERO_SIDE), (489.0, RIVER_Y - RIVER_W1 / (2 * C30))],
     "note": "콜로세움 받침 앞-왼쪽 변(평면 Y 263.81, 받침 옆면 아래 끝) → 폰스 아일리우스 북쪽 끝(테베레 북쪽 둑 Y 304.76). 평면 X 489 상수(하역장 길 R4와 평행, 평면 26.7 떨어짐). "
             "다리 상판(X 485.5~492.5)이 이 띠 안에서 시작한다. 기획 X 488에서 영묘와 함께 +1.0 옮겼다"},
]

# 수도교 지면선 = 화면 ↘ 직선(평면 Y 상수): 카라칼라 욕장 오른쪽 변 (334, 160) → 오른쪽 변 밖(블리드)
AQUEDUCT_PLAN = [to_plan(336.0, 160.0), to_plan(424.0, 160.0 + T30 * 88.0)]
AQUEDUCT_H = 26.0

# ═════════════ d4 추가 랜드마크 3개(기준선 7.2절) — 평면 원본과 화면 외곽 ═════════════
# 평면 좌표(mm, 사양 규약 to_screen)와 높이(화면 수직 mm)가 원본이다. render는 이 평면 좌표를 전역 등각 그대로 그린다
# (fit_frame 배율·높이 과장 없음 → 접촉·간격 실측이 아래 계산과 같다). 화면 외곽은 import 때 계산해 사양에 함께 적는다.
def _cvx_hull(pts):
    """화면 점들의 볼록 껍질(단조 사슬, 반시계)"""
    p = sorted(set((round(x, 4), round(y, 4)) for x, y in pts))
    if len(p) < 3:
        return p

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for q in p:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in reversed(p):
        while len(up) >= 2 and cross(up[-2], up[-1], q) <= 0:
            up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]


def _prism_pts(X0, X1, Y0, Y1, z0, z1):
    return [to_screen(X, Y, z) for X in (X0, X1) for Y in (Y0, Y1) for z in (z0, z1)]


def _ring_pts(c, r, z, n=96, a0=0.0, a1=360.0):
    return [to_screen(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)), z) for i in range(n + 1)]


def _in_cvx(p, poly, eps=1e-9):
    """점이 볼록 다각형(반시계) 안 또는 변 위에 있는가"""
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) < -eps:
            return False
    return True


def _seg_x(p1, p2, p3, p4):
    d = (p2[0] - p1[0]) * (p4[1] - p3[1]) - (p2[1] - p1[1]) * (p4[0] - p3[0])
    if abs(d) < 1e-12:
        return None
    t = ((p3[0] - p1[0]) * (p4[1] - p3[1]) - (p3[1] - p1[1]) * (p4[0] - p3[0])) / d
    u = ((p3[0] - p1[0]) * (p2[1] - p1[1]) - (p3[1] - p1[1]) * (p2[0] - p1[0])) / d
    if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
        return (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]))
    return None


def _union_star(A, B, c):
    """겹치는 두 볼록 다각형의 합집합 외곽(점 c는 두 다각형 공통 안쪽 → 합집합은 c에 대해 별 모양이라 각도 순으로 잇는다)"""
    pts = [p for p in A if not _in_cvx(p, B, 1e-7)] + [p for p in B if not _in_cvx(p, A, 1e-7)]
    for i in range(len(A)):
        for j in range(len(B)):
            q = _seg_x(A[i], A[(i + 1) % len(A)], B[j], B[(j + 1) % len(B)])
            if q:
                pts.append(q)
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts), key=lambda q: math.atan2(q[1] - c[1], q[0] - c[0]))
    return pts


def _bbox(pts, nd=1):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    f = 10 ** nd
    return [math.floor(min(xs) * f + 0.5) / f, math.floor(min(ys) * f + 0.5) / f, math.floor(max(xs) * f + 0.5) / f, math.floor(max(ys) * f + 0.5) / f]


def _r2(poly):
    return [[round(x, 2), round(y, 2)] for x, y in poly]


# ── L7 막센티우스 바실리카(후보 자리 (가): 히어로 4층 조각 뒤, 시내 길 1과 카라칼라 욕장 사이)
BASILICA = {
    "paving": {"rects_plan": [[276.0, 338.0, 43.5, 62.0], [292.5, 335.5, 43.5, 87.0]], "h": 1.5,
               "note": "기단 포장 = 두 직사각형의 합(L자). 뒤-왼쪽 변(평면 X 276)이 시내 길 1 바깥 변(X 274.45)과 평면 1.55 = 화면 1.35mm(접속 ≤ 1.6). "
                       "신랑 쪽 앞 끝은 X 335.5까지(측랑 X 338보다 2.5 안쪽): 그림의 콜로세움 외벽 윗단 밝은 띠(사전 검사 모형보다 약 1.7mm 높다)와 2mm 이상 띄우려고 줄였다(338이면 0.56mm)"},
    "aisle": {"name": "북쪽 측랑", "X": [292.5, 338.0], "Y": [43.5, 55.5], "h": 16.0, "bays": 3, "bay_plan": round((338.0 - 292.5) / 3.0, 2),
              "vault": "팔각 코퍼를 새긴 콘크리트 배럴 볼트(볼트 축 = 평면 Y 방향, 칸마다 하나)", "open_face": "+Y(신랑 쪽, 화면 왼쪽 아래)",
              "note": "현존하는 북쪽 측랑 3칸. 칸 경계 평면 X 292.5·307.67·322.83·338.0, 두꺼운 칸막이 벽 위에 볼트가 얹힌다. 열린 면(평면 Y 55.5, z 0~16)에서 코퍼 반원통 안쪽이 보인다"},
    "nave_ruins": {"name": "신랑·남쪽 측랑 유적", "X": [292.5, 335.5], "Y": [55.5, 87.0], "h_max": 4.0,
                   "place_rule": "기둥 밑동·낮은 벽은 평면 Y ≥ 60.0에만 둔다(높이 4 이하라 측랑 열린 면 아래 끝을 가리지 않는다)",
                   "note": "낮은 기둥 밑동·벽 자국·포장 결. 남쪽 측랑 칸 벽 자국 3칸"},
    "nave_vault_dashed": {"name": "무너진 신랑 교차 볼트(점선 복원)", "bays": 3, "line_mm": 0.25, "h_max": 10.0, "dash_mm": [1.2, 0.8],
                          "profile": "칸 경계 평면 X 292.5·306.83·321.17·335.5의 가로 아치 z(Y) = 9.0·sin(π·(Y − 56.5)/30.5)(Y 56.5~87.0) + 꼭대기 마루선(Y 71.75, z 9.0) + 칸마다 대각 리브",
                          "rule": "윤곽의 모든 점 (X, Y, z)가 (Y − 55.5) ≥ z를 지킨다 → 화면에서 측랑 열린 면(Y 55.5, z 0~16) 아래 끝보다 아래라 열린 면과 겹치지 않는다(가로 아치–열린 면 최소 0.87mm)",
                          "label": "점선 = 무너진 신랑 볼트 복원(P2 ② 캡션과 같은 말)"},
}
_B = BASILICA
_pav = [(276.0, 43.5), (338.0, 43.5), (338.0, 62.0), (335.5, 62.0), (335.5, 87.0), (292.5, 87.0), (292.5, 62.0), (276.0, 62.0)]
_L7_ground = [to_screen(X, Y) for X, Y in _pav]
_L7_aisle = _cvx_hull(_prism_pts(292.5, 338.0, 43.5, 55.5, 0.0, 16.0))
_L7_nave = _cvx_hull(_prism_pts(292.5, 335.5, 55.5, 87.0, 0.0, 4.0))
_L7_all = [to_screen(X, Y, z) for X, Y in _pav for z in (0.0, 1.5)] + _L7_aisle + _L7_nave
L7_POLY = _cvx_hull(_L7_all)
L7_BOX = _bbox(L7_POLY)

# ── L8 하드리아누스 영묘 + 폰스 아일리우스(후보 자리 (나): 테베레 굽이 안쪽 오른쪽 둑)
MAUSOLEUM = {
    "base": {"name": "사각 기단", "X": [466.5, 511.5], "Y": [325.3, 370.3], "h": 5.0,
             "note": "45×45 정사각 기단(평면). 뒤-오른쪽 변(평면 Y 325.3)이 테베레 남쪽 둑(Y 323.24)과 평면 2.06 = 화면 1.78mm(접속 ≤ 2.5)"},
    "drum": {"name": "원통", "c": [489.0, 347.8], "r": 16.0, "z": [5.0, 23.0], "skin": "겉 = 대리석", "core": "속 = 콘크리트 원통",
             "note": "기단 가운데의 큰 원통. 절개하지 않는다(겉 대리석 면 + 위쪽 테두리 띠에 콘크리트 속을 보이는 작은 이음 자국)"},
    "top": {"name": "정상(낮은 둔덕·난간)", "parapet": {"r": 16.0, "z": [23.0, 25.5]}, "mound": {"r_max": 10.0, "z_top": 28.0},
            "omit": "정상 조각(황제상·사두마차)과 교황 증축(산탄젤로성) 형태는 그리지 않는다",
            "note": "테두리 난간은 낮게(z 25.5까지) 둔다: 원통 꼭대기 테두리가 강 건너 하역장 부두 앞 변(d3 그림)과 화면 2.2mm 떨어진다(기획대로 테두리를 z 28까지 올리면 부두 앞 변과 0.23mm 겹친다). 안쪽 흙 둔덕은 꼭대기 z 28(테두리 안쪽이라 실루엣 밖으로 나가지 않는다), 나무 없음"},
    "bridge": {"name": "폰스 아일리우스", "deck_X": [485.5, 492.5], "deck_Y": [304.76, 325.3], "h": 3.0, "arches": 3,
               "piers_Y": [[309.9, 311.9], [316.1, 318.1]], "cutwater_X": [484.5, 493.5], "bridge": True,
               "note": "상판이 ↘ 팔(평면 Y 304.76~323.24)을 건너 북쪽 둑 끝에서 새 길 R7과 만난다(R7 띠 X 484.38~493.62 안). 아치 3개·교각 2개(물가름 앞뒤 1mm). 강 위 예외(bridge: 땅·강 검사에서 뺀다)"},
    "shift_from_plan": "기획 좌표(기단 X 466~510 × Y 325.5~369.5, 원통 (488,347.5), 테두리 z 28, 다리·R7 X 488)에서 바꾼 것: 원통·기단 중심 평면 +X 1.0·+Y 0.3, 기단 44 → 45, 테두리 z 28 → 25.5. "
                       "이유: 기획값 그대로면 원통 왼쪽 실루엣–포르투스 육각 내항 창고 지붕 1.46mm, 원통 꼭대기–하역장 부두 앞 변 −0.23mm(겹침). 바꾼 뒤 2.07·2.2mm이고 투영 면적은 ±3% 안",
}
_M = MAUSOLEUM
_mb, _md = _M["base"], _M["drum"]
_L8_ground = [to_screen(_mb["X"][0], _mb["Y"][0]), to_screen(_mb["X"][1], _mb["Y"][0]), to_screen(_mb["X"][1], _mb["Y"][1]), to_screen(_mb["X"][0], _mb["Y"][1])]
_L8_base = _cvx_hull(_prism_pts(_mb["X"][0], _mb["X"][1], _mb["Y"][0], _mb["Y"][1], 0.0, _mb["h"]))
_L8_drum = _cvx_hull(_ring_pts(_md["c"], _md["r"], _md["z"][0]) + _ring_pts(_md["c"], _md["r"], _M["top"]["parapet"]["z"][1])
                     + [to_screen(_md["c"][0], _md["c"][1], _M["top"]["mound"]["z_top"])])
_mbr = _M["bridge"]
_L8_bridge = _cvx_hull(_prism_pts(_mbr["deck_X"][0], _mbr["deck_X"][1], _mbr["deck_Y"][0], _mbr["deck_Y"][1], 0.0, _mbr["h"])
                       + sum([_prism_pts(_mbr["cutwater_X"][0], _mbr["cutwater_X"][1], py[0], py[1], 0.0, _mbr["h"]) for py in _mbr["piers_Y"]], []))
L8_POLY = _union_star(_L8_base, _L8_drum, to_screen(_md["c"][0], _md["c"][1], _mb["h"]))      # 건물 실루엣(기단 ∪ 원통, 볼록 아님)
L8_BOX = _bbox(L8_POLY + _L8_bridge)                                                            # 투영 상자 = 건물 + 다리

# ── L9 마르켈루스 극장(후보 자리 (라): 판테온과 강 사이 테베레 둑)
THEATRE = {
    "plan": {"diameter_X": 340.0, "diameter_Y": [226.76, 302.76], "c": [340.0, 264.76], "r": 38.0, "curve": "+X(화면 오른쪽 아래)",
             "note": "반원 평면. 지름(무대 쪽)은 평면 X 340, 곡면(바깥 아케이드)은 +X 쪽 X 378까지"},
    "arcade": {"tiers": 2, "h": 12.0, "tier_h": [6.0, 6.0], "third_tier": "그리지 않는다(그린다면 점선 + '추정')",
               "note": "바깥 곡면 아케이드 2단(아래 도리스·위 이오니아 기둥 붙임). 관람석은 곡면에서 지름 쪽으로 내려간다"},
    "stage_wall": {"h_max": 4.0, "note": "무대 쪽(지름 쪽) 벽은 낮은 유적으로 두어 관람석 층이 보이게 한다"},
}
_T = THEATRE["plan"]
_arc = [(_T["c"][0] + _T["r"] * math.cos(math.radians(a)), _T["c"][1] + _T["r"] * math.sin(math.radians(a))) for a in [-90.0 + 180.0 * i / 60 for i in range(61)]]
_L9_ground = [to_screen(X, Y) for X, Y in _arc]
L9_POLY = _cvx_hull([to_screen(X, Y, z) for X, Y in _arc for z in (0.0, THEATRE["arcade"]["h"])]
                    + [to_screen(_T["diameter_X"], Y, THEATRE["stage_wall"]["h_max"]) for Y in _T["diameter_Y"]])
L9_BOX = _bbox(L9_POLY)


# ═════════════ Core 랜드마크(투영 상자 = 레이어 알파 외곽 상자 목표) ═════════════
LANDMARKS = [
    {"id": "L1", "name": "판테온", "latin": "Pantheon", "box": [18.0, 198.0, 114.0, 288.0], "zone": "시내(왼쪽 가운데, 강 위쪽 — 실제로 테베레 굽이 안쪽 캄푸스 마르티우스)",
     "geo": (41.8986, 12.4769), "real": "콜로세움에서 1.6 km 북서(306°)",
     "form": "주랑 현관 + 원통 + 돔(오큘러스). 절개하지 않는다(욕장만 절개). 둘레 광장·나무·사람",
     "story": "2,000년째 서 있는 철근 없는 콘크리트 돔", "number": "돔 지름 43.3 m",
     "links": "시내 길 1(광장 뒤 꼭짓점 쪽, 끝은 돔 뒤로 숨는다)"},
    {"id": "L2", "name": "트라야누스 시장", "latin": "Mercati di Traiano", "box": [18.0, 98.0, 114.0, 182.0], "zone": "시내(뒤쪽 왼쪽, L 패널 바로 아래)",
     "geo": (41.8958, 12.4861), "real": "콜로세움에서 0.8 km 북서(321°)",
     "form": "반원형 벽돌 정면(층층 상점) + 대회랑 교차 볼트(지붕 한 칸을 걷어 볼트를 보인다)",
     "story": "판 모양 결정이 갈라짐을 막았다(2014년 연구)", "number": "대회랑 중앙 볼트 경간 8.6 m",
     "links": "시내 길 2(오른쪽 아래 지면에서 시작)"},
    {"id": "L3", "name": "카라칼라 욕장(절개)", "latin": "Thermae Antoninianae", "box": [224.0, 94.0, 336.0, 190.0], "zone": "시내(뒤쪽 가운데-오른쪽) — 사용자 결정 '뒤쪽'",
     "geo": (41.8791, 12.4924), "real": "콜로세움에서 1.2 km 남(179°)",
     "form": "욕장 참조 이미지(열주·벽감 조각상·돔 열탕실·증기 욕조·목욕객)를 절개 단면으로: 칼다리움 드럼 벽(겉 벽돌·속 콘크리트·돔 위쪽 경석 층), 하이포코스트·화로 일꾼, 냉탕실 열주. 빛은 큰 창 중심, 오큘러스·코퍼는 복원 추정",
     "story": "겉은 벽돌, 속은 콘크리트. 돔 위쪽엔 가벼운 경석", "number": "열탕실 돔 경간 약 36 m",
     "links": "시내 길 1·욕장 진입로 R5(지면 뒤-왼쪽 변), 수도교 아치 열(오른쪽 변: 아쿠아 마르키아에서 갈라진 아쿠아 안토니니아나가 저수조 64개에 물을 댐[S47][S49])"},
    {"id": "L4", "name": "수도교 아치 열(아쿠아 안토니니아나)", "latin": "Aqua Antoniniana(아쿠아 마르키아 지선)", "box": [336.0, 134.0, 420.0, 208.5], "zone": "남동 교외(오른쪽 위, 오른쪽 변 블리드)",
     "geo": None, "real": "아쿠아 마르키아에서 갈라진 지선, 212–213년 비문[S47][S49]. 경로 좌표는 조사 보고서에 없어 지리 검사에서 뺀다",
     "form": "실제 경로가 아니라 욕장 급수 관계 모식(아쿠아 마르키아 → 아쿠아 안토니니아나 → 욕장 저수조 64개). 오른쪽 변 밖(남동 시골)에서 ↖로 들어와 카라칼라 욕장 오른쪽 변 (336, 160)에 닿는 아치 열, 높이 26mm(2단 아치), 교각 약 8mm 간격. 아치는 관통 아치로 그린다: 아래층 개구 폭 5.3mm·위층 3.9mm, 아치 안쪽 면 1.5mm가 보이고 개구부 뒤로 지면(밭·구릉)이 보인다(막힌 벽면에 아치 무늬만 그리지 않는다). 맨 위 수로에 물빛 선. 벽돌면 보수 구간 덧댐은 그리지 않는다(이 수도의 근거가 없다)",
     "story": "수로 안은 방수 모르타르", "number": "욕장 저수조 64개에 물을 댐",
     "links": "카라칼라 욕장(왼쪽 끝, 욕장 오른쪽 변 (336, 160))"},
    {"id": "L5", "name": "카이킬리아 메텔라 무덤", "latin": "Mausoleo di Cecilia Metella", "box": [354.0, 288.0, 420.0, 358.0], "zone": "남동 교외(오른쪽 가운데), 아피아 가도 남쪽 길가",
     "geo": (41.8518, 12.5205), "real": "콜로세움에서 4.9 km 남남동(151°), 아피아 가도",
     "form": "네모 기단 위 원통 드럼(16면 이상), 벽돌 겉면·응회암 보강. 둘레 사이프러스·소나무(진입로 R6a·R6b 띠 밖 2mm 이상)",
     "story": "BCE 30–10년의 원통 무덤", "number": "드럼 지름 29 m",
     "links": "아피아 가도 → 메텔라 진입로 R6a·R6b(무덤 대지 뒤-오른쪽 변)"},
    {"id": "L6", "name": "포르투스 항", "latin": "Portus Traiani · Portus Claudii", "box": [5.0, 372.0, 102.0, 434.0], "zone": "서남서 해안(왼쪽 아래), 강 오른쪽 둑과 해안 사이",
     "geo": (41.7781, 12.2593), "real": "콜로세움에서 23.0 km 서남서(237°)",
     "form": "판화를 바다가 왼쪽 아래로 오게 돌림: 트라야누스 육각 내항(육지, 평면 중심 (437.0, 353.6), 반지름 24, 붉은 기와 창고 고리, 수면 반지름 15.2) · 클라우디우스 외항(바다, 평면 중심 (437.0, 401.6), 휘어 감싼 방파제 두 팔: 평면 반지름 18.4~21.0, 팔 A 263°→123°, 팔 B 277°→57°, 끝각에서 정확히 자름 → 입구 화면 폭 약 19.8mm, 창고·열주) · 등대(입구 인공섬: 평면 90°·반지름 24, 4층 탑 + 등롱) · 운하 2개(강 ↔ 육각 내항 ↔ 외항, 화면 폭 2.6mm) · 두 항구 수면의 작은 범선. 판화의 황제 거상은 넣더라도 라벨에서 사실로 쓰지 않는다",
     "story": "트라야누스 육각 내항은 육지, 클라우디우스 외항·등대는 바다. 바닷물은 항구 구조물에만", "number": "육각 내항 약 32 ha(약 100–112년), 외항 42년 착공",
     "links": "테베레 오른쪽 둑(강 쪽 운하로 육각 내항과 이음), 해안선(외항 쪽 운하로 외항과 이음)"},
    # ── d4 추가(기준선 7.2절): 모두 표준 랜드마크 등급(투영 면적 ≥ 4,500mm², 콜로세움보다 작게). 형태·이야기 글에 높이·지름·치수 수치를 쓰지 않는다
    {"id": "L7", "name": "막센티우스 바실리카", "latin": "Basilica Maxentii · Basilica Nova", "box": L7_BOX,
     "zone": "시내(뒤쪽 가운데: 콜로세움 4층 조각 뒤, 시내 길 1과 카라칼라 욕장 사이) — 후보 자리 (가)",
     "geo": (41.8917, 12.4886), "real": "콜로세움에서 0.3 km 서북서(299°), 포룸 로마눔 동쪽 끝",
     "form": "현존하는 북쪽 측랑 3칸의 거대한 콘크리트 배럴 볼트(팔각 코퍼, 열린 면은 신랑 쪽 = 화면 왼쪽 아래)가 주인공. 신랑·남쪽 측랑 자리는 낮은 기둥 밑동·벽 자국 유적, "
             "무너진 신랑 교차 볼트 3칸은 가는 점선 복원 윤곽(측랑보다 낮게, 측랑 열린 면과 화면에서 겹치지 않게). 판테온의 돔 코퍼와는 '배럴 볼트'로 구분한다. 기단 포장이 시내 길 1에 닿는다",
     "story": "북쪽 측랑의 콘크리트 배럴 볼트 3칸이 지금도 서 있다", "number": None,
     "links": "시내 길 1(R2): 기단 포장 뒤-왼쪽 변이 길 바깥 변에 닿는다(실제 지면 간격 ≤ 1.6mm)",
     "plan": BASILICA, "poly_screen": _r2(L7_POLY), "ground_screen": _r2(_L7_ground),
     "parts_screen": {"바실리카 지면": _r2(_L7_ground), "바실리카 측랑 볼트": _r2(_L7_aisle), "바실리카 신랑 유적": _r2(_L7_nave)},
     "gaps_expected_mm": {"기단 포장–시내 길 1(R2) 지면": 1.35, "실루엣–콜로세움 사전 검사 모형": 2.28, "실루엣–콜로세움 외벽(d3 그림 윗단 띠)": 2.3,
                          "실루엣–카라칼라 욕장 지면(d3 그림)": 2.45, "실루엣–네로 거상": 4.76},
     "draw": "평면 원본(plan)을 전역 등각 그대로 그린다(fit_frame 배율·높이 과장 없음). 투영 상자는 poly_screen의 외곽 상자"},
    {"id": "L8", "name": "하드리아누스 영묘·폰스 아일리우스", "latin": "Mausoleum Hadriani · Pons Aelius", "box": L8_BOX,
     "zone": "테베레 굽이 안쪽 오른쪽 둑(↘ 팔 남쪽, 포르투스 육각 내항과 강 사이) — 후보 자리 (나)",
     "geo": (41.9031, 12.4663), "real": "콜로세움에서 2.6 km 북서(304°), 테베레 서안",
     "form": "사각 기단 + 큰 원통(겉은 대리석, 속은 콘크리트 원통) + 정상의 낮은 흙 둔덕과 테두리 난간 + 테베레를 건너는 다리(아치 3개). "
             "정상 조각(복원 추정)과 교황 증축(지금의 산탄젤로성) 형태는 그리지 않는다. 카이킬리아 메텔라 무덤과는 사각 기단과 다리로 구분한다. 다리 북쪽 끝은 새 길 R7로 콜로세움 받침 앞-왼쪽 변에 잇는다",
     "story": "겉은 대리석, 속은 콘크리트 원통", "number": None,
     "links": "테베레 남쪽 둑(기단 뒤-오른쪽 변, 실제 지면 간격 ≤ 2.5mm) + 폰스 아일리우스(강 위) + R7(다리 북쪽 끝)",
     "plan": MAUSOLEUM, "poly_screen": _r2(L8_POLY), "ground_screen": _r2(_L8_ground),
     "bridge_screen": _r2(_L8_bridge), "bridge": True,
     "parts_screen": {"영묘 기단": _r2(_L8_base), "영묘 원통": _r2(_L8_drum), "폰스 아일리우스 다리": _r2(_L8_bridge)},
     "box_building_only": _bbox(L8_POLY),
     "gaps_expected_mm": {"기단 지면–테베레 남쪽 둑": 1.78, "원통 왼쪽 실루엣–포르투스 육각 내항 창고 지붕": 2.07, "기단–육각 내항": 3.4,
                          "원통 꼭대기 테두리–하역장 부두 앞 변(d3 그림)": 2.2, "R7–재료 수레 상자": 4.1, "실루엣–바지선 2 상자": 2.08},
     "draw": "평면 원본(plan)을 전역 등각 그대로 그린다. 다리 상판·교각은 강 위(bridge 예외), 기단 지면(ground_screen)만 땅 검사 대상. poly_screen = 기단 ∪ 원통 실루엣(다리 제외, 볼록 아님)"},
    {"id": "L9", "name": "마르켈루스 극장", "latin": "Theatrum Marcelli", "box": L9_BOX,
     "zone": "시내 서쪽 테베레 둑(판테온과 강 사이, 티베리나 섬 곁) — 후보 자리 (라)",
     "geo": (41.8919, 12.4797), "real": "콜로세움에서 1.1 km 서(280°), 테베레 둑·티베리나 섬 곁",
     "form": "반원 평면의 극장: 바깥 곡면 아케이드 2단(곡면은 화면 오른쪽 아래). 3단은 그리지 않는다(그린다면 점선 + '추정'). 무대 쪽(지름 쪽) 벽은 낮은 유적으로 두어 관람석 층이 보인다. "
             "콜로세움과는 반원 평면·표준 크기로 구분한다. 지름 쪽 앞 끝이 테베레 북쪽 둑에 닿는다",
     "story": "테베레 홍수에 거듭 잠긴 콘크리트 기초에서 결정이 자라 보강했다(2011년 연구)", "number": None,
     "links": "테베레 북쪽 둑(지름 쪽 +Y 끝, 실제 지면 간격 ≤ 2.5mm)",
     "plan": THEATRE, "poly_screen": _r2(L9_POLY), "ground_screen": _r2(_L9_ground),
     "parts_screen": {"극장 반원 아케이드": _r2(L9_POLY)},
     "gaps_expected_mm": {"지름 쪽 +Y 끝–테베레 북쪽 둑": 1.73, "실루엣–판테온 광장(d3 그림)": 6.84, "실루엣–석회 가마 상자": 6.3},
     "draw": "평면 원본(plan)을 전역 등각 그대로 그린다"},
]
BACKGROUND = [
    {"id": "V", "name": "베수비오(지도 배경, 가장 먼 곳)", "latin": "Vesuvius", "box": [360.0, 98.0, 418.0, 138.0], "zone": "가장 먼 곳(지도 무대 오른쪽 위)",
     "geo": (40.8213, 14.4261), "real": "콜로세움에서 200 km 남동(126°)",
     "form": "79년 이전 모습: 넓고 완만한 봉우리 하나, 잿빛 평평한 정상, 포도밭 비탈. 축척 약 0.6, 대기 원근(바탕색 50% 혼합·흐림). 그리는 순서 산 → 포도밭 농장 → 알바노 구릉. 앞 능선이 산 밑동 앞쪽 윤곽 x 360~418 전체를 3~5mm 연속으로 가리고(가운데만 내리는 처리 없음), 농장 지면과 앞 구릉을 한 지형 실루엣으로 이어 산기슭의 닫힌 윤곽을 끊는다. 크기 58×40mm 유지(d2 자리 (356,96)에서 +4,+2). 연기 없음",
     "story": "79년 분화", "number": "로마에서 남동쪽 약 200 km",
     "links": "알바노 구릉 띠(지면), 포도밭 농장"},
]

# ═════════════ Core 지도 소품(탈것·시설·지형) ═════════════
PROPS = [
    {"name": "테베레 하역장(엠포리움: 돌 부두·기중기·창고)", "box": [107.4, 348.0, 154.2, 389.0], "zone": "강 왼쪽(북동) 둑", "on": "땅+물(부두)", "note": "하역장 길의 끝. 바지선이 생석회·골재를 내린다"},
    {"name": "석회 가마", "box": [118.0, 296.0, 146.0, 328.0], "zone": "강 왼쪽 둑(콜로세움 받침 왼쪽 발치)", "on": "땅",
     "note": "김·연기는 알파 40 이하 레이어. d4: 옛 자리 [90.1,303,114.3,335]는 마르켈루스 극장 앞이라 오른쪽으로 옮겼다(극장 실루엣 6.3·콜로세움 2.2·하역장 태그 3.0mm)"},
    {"name": "재료 수레", "box": [156.0, 366.0, 176.0, 378.0], "zone": "하역장 길 위", "on": "길", "plan": [462.3, 278.0], "note": "콜로세움 공사장 쪽으로 가는 수레(그리기 기준점 평면 (462.3, 278.0) = d2 그림 자리)"},
    {"name": "바지선 1(올라가는 배)", "box": [64.0, 348.0, 100.0, 368.0], "zone": "테베레 ↘ 팔", "on": "물", "note": "포르투스에서 환적한 짐을 싣고 상류로"},
    {"name": "바지선 2(내려가는 배)", "box": [128.0, 440.0, 158.0, 462.0], "zone": "테베레 ↙ 팔(하구 쪽, 강 중심선 위)", "on": "물",
     "note": "하구 쪽으로. d4: 옛 자리 [150,428,184,446]는 L8 라벨·영묘 둘레라 ↙ 팔 중심선(평면 X 533.4) 위 하구 쪽으로 옮겼다(영묘 실루엣 2.08mm, 영묘 지시선보다 아래)"},
    {"name": "화산재 운반선", "box": [112.0, 476.0, 152.0, 500.0], "zone": "바다", "on": "물", "note": "나폴리만 화산재(바다 공사용)를 싣고 포르투스 외항으로"},
    {"name": "오스티아(창고 몇 채)", "box": [214.0, 466.0, 238.0, 482.0], "zone": "하구 왼쪽(동쪽) 둑, 해안선 위", "on": "땅", "plan": [604.5, 343.5],
     "note": "작은 소품. 바닥 글 OSTIA는 그 아래. d4: 동쪽 둑 옛 자리는 영묘 라벨 자리로 비우고 Z1 글 칸 아래·⑥ 수직선(x 210)에서 4mm 오른쪽·해안선 위로 옮겼다"},
    {"name": "포도밭 농장(베수비오 밑동)", "box": [366.0, 122.0, 408.0, 144.0], "zone": "가장 먼 곳(지도 무대 오른쪽 위)", "on": "땅",
     "note": "베수비오 밑동 앞(1.6절 포도밭 근거). 산 다음, 알바노 구릉 앞 능선 전에 그린다. 농장 지면은 앞 구릉과 한 지형 실루엣으로 잇는다(따로 떠 있는 밭판 금지). 아래 변은 수도교 윗선과 2mm 이상"},
    {"name": "아피아 가도 수레", "box": [350.0, 266.0, 370.0, 282.0], "zone": "아피아 가도 위", "on": "길", "plan": [485.6, 72.0],
     "note": "남동 교외로 가는 짐수레. d2 그림 자리 그대로 둔다(기준점 평면 (485.6, 72.0) = 화면 (358.2, 278.8), 그린 외곽 352.6~368.8×268.8~280.4). 상자만 메텔라 진입로 R6a 띠 밖으로 줄였다(R6a와 1.2mm, VIA APPIA 바닥 글과 2.3mm). 결정 상자 (364,256)~(388,272)는 VIA APPIA 바닥 글(화면 371.3~413.8×241.6~266.1)과 겹쳐 쓰지 않는다"},
    {"name": "교외 빌라(포도밭 농가)", "box": [306.0, 464.0, 328.0, 484.0], "zone": "남동 교외 밭", "on": "땅", "note": "작은 농가, 라벨 없음. 콜아웃 C4(아래 변 456)와 S 패널(왼쪽 변 332) 사이로 옮겼다"},
    # d4 추가(기준선 7.3절): 콜로세움 곁 작은 소품. 받침과 거상의 재료를 구분한다
    {"name": "네로 청동 거상과 콘크리트(벽돌 마감) 받침", "box": None, "zone": "콜로세움 뒤-왼쪽과 막센티우스 바실리카 사이(베누스·로마 신전 쪽) 지면", "on": "땅",
     "plan": [327.3, 113.7],
     "pedestal": {"name": "네로 거상 받침", "plan_size": [8.0, 8.0], "h": 5.0, "finish": "벽돌 마감 콘크리트(원래 대리석으로 덮임), 윗단에 가는 대리석 띠"},
     "statue": {"name": "네로 거상", "plan_size": [2.4, 2.4], "z": [5.0, 20.0], "material": "청동(복원 추정)", "head_screen": None},
     "note": "받침 = 벽돌 마감 콘크리트(원래 대리석), 거상 = 청동 복원 추정, 치수 인쇄 금지. 라벨 문장은 '콘크리트(벽돌 마감) 받침 위의 / 네로의 청동 거상(추정)' 꼴만 쓴다"
             "('콘크리트로 만든 조각'·'콘크리트로 빚은 거상' 금지, '콜로세움' 이름 유래는 이번 회차에 인쇄하지 않는다). "
             "기획 중심 (328.8,115.2)에서 평면 (−1.5,−1.5) = 화면 위로 1.5mm 옮겼다: 그림의 콜로세움 외벽 윗단 띠와 0.81 → 2.11mm(사전 검사 모형과는 3.8mm). 머리 (185,201)는 그대로 거상 윗면 안이다"},
]
_nero = PROPS[-1]
_nc = _nero["plan"]
_nps = _nero["pedestal"]["plan_size"]
_nss = _nero["statue"]["plan_size"]
_NERO_PED = _cvx_hull(_prism_pts(_nc[0] - _nps[0] / 2, _nc[0] + _nps[0] / 2, _nc[1] - _nps[1] / 2, _nc[1] + _nps[1] / 2, 0.0, _nero["pedestal"]["h"]))
_NERO_STA = _cvx_hull(_prism_pts(_nc[0] - _nss[0] / 2, _nc[0] + _nss[0] / 2, _nc[1] - _nss[1] / 2, _nc[1] + _nss[1] / 2, _nero["statue"]["z"][0], _nero["statue"]["z"][1]))
_nero["box"] = _bbox(_NERO_PED + _NERO_STA)
_nero["statue"]["head_screen"] = [round(v, 2) for v in to_screen(_nc[0], _nc[1], _nero["statue"]["z"][1] - 1.0)]
_nero["parts_screen"] = {"네로 거상 받침": _r2(_NERO_PED), "네로 거상": _r2(_NERO_STA)}
TERRAIN = [
    {"name": "알바노 구릉 띠(화산 지대, 낮은 구릉)", "box": [318.0, 122.0, 420.0, 162.0],
     "note": "지면 결. 화산 그림이 아니다. 지도 무대 오른쪽 위 '가장 먼 곳'(대기 원근). 그리는 순서 산 → 포도밭 농장 → 구릉. 바닥 글 'COLLI ALBANI 알바노 구릉 — 로마 건물의 화산재'. 수도교 윗선과 겹치는 앞쪽은 수도교 뒤(먼 지면)로 그린다",
     "ridge": {"cover_vesuvius_base_mm": [3.0, 5.0], "order": ["베수비오", "포도밭 농장", "알바노 구릉 능선"],
               "cover_x_range": [360.0, 418.0], "continuous": True, "farm_merge": True,
               "note": "앞 능선이 베수비오 밑동 앞쪽 윤곽(바닥 고리 앞쪽 반)의 x 360~418 전체를 3~5mm 연속으로 가린다. 가운데(농장 구간)만 고정값으로 내리던 처리는 없다. "
                       "농장 지면(포도밭 농장 상자)과 앞 구릉은 한 지형 실루엣으로 이어(농장이 능선 위 비탈에 얹힌 모양) 산기슭의 닫힌 윤곽을 끊는다. 옛 열쇠 x_ranges·farm_front_top_y_min은 지웠다"}},
    {"name": "남동 교외 밭·포도밭(캄파냐)", "box": [296.0, 396.0, 420.0, 505.0],
     "note": "S 패널·콜아웃 C4가 앉는 고요한 영역. 오른쪽은 블리드, 아래 변은 지도 무대 아래 변 y 505에서 닫는다(하단 띠 오른쪽은 P5 패널의 띠 바탕)"},
    {"name": "시내 지붕 블록·나무(콜로세움 둘레)", "box": [112.0, L7_BOX[3], 300.0, 300.0], "exclude_boxes": [PROPS[-1]["box"]],
     "note": "지스몬디 '지붕의 바다' 밀도, 언덕에 나무 덩어리. d4: 위 변을 막센티우스 바실리카 투영 상자 아래 변까지 내리고 네로 거상 소품 상자를 뺀다"},
    {"name": "오른쪽 둑 들판(포르투스 띠)", "box": [0.0, 329.5, 200.0, 440.0], "exclude_screen": [_r2(_L8_ground), _r2(_L8_bridge)],
     "note": "강과 해안 사이 육지 띠, 곡식밭. d4: 위 변 329.5(마르켈루스 극장 상자 아래), 하드리아누스 영묘 기단 지면과 다리를 뺀다"},
]

# ═════════════ 포르투스(원본은 이 사양, 그림은 render) ═════════════
# 상자는 위계 실측 목표, 다각형은 형태 골격(겹침·땅/바다 검사용)
PORTUS_HEX_C = (437.0, 353.6)        # 평면: 강 오른쪽 둑(Y 323.24)과 해안(Y 380) 사이 띠 가운데
PORTUS_HEX_R = 24.0                  # 창고 고리 포함 평면 반지름
PORTUS_HEX_WATER_R = 15.2            # 육각 내항 수면 반지름
PORTUS_BASIN_C = (437.0, 401.6)      # 클라우디우스 외항(바다)
PORTUS_BASIN_R = 21.0                # 방파제 포함

# 운하 2개(평면 X 435.5~438.5 = 화면 수직 폭 2.6mm). 육각 내항 수면 안쪽과 외항 수면 안쪽까지 잇고, 포장·안벽에 폭 3mm 개구부를 낸다
PORTUS_CANALS = [
    {"name": "강 쪽 운하", "plan_x": [435.5, 438.5], "plan_y": [322.24, 340.10],
     "note": "테베레 오른쪽 둑(강 수면 1.0 안) → 육각 내항 수면(270° 꼭짓점 안쪽 1.5). 육각 포장·성벽·창고 고리에 폭 3mm 개구부. d4: d3 그림의 끝점을 채택했다(render의 추가 연장 0)"},
    {"name": "외항 쪽 운하", "plan_x": [435.5, 438.5], "plan_y": [367.10, 384.60],
     "note": "육각 내항 수면(90° 꼭짓점 안쪽 1.5) → 해안선(Y 380)을 지나 외항 수면 안쪽(방파제 두 팔 사이 263°~277° 빈 곳을 지난다). d4: d3 그림의 끝점을 채택했다(render의 추가 연장 0)"},
]
# 외항 방파제 두 팔(평면 각도는 외항 중심 기준, 0° = +X). 마지막 조각은 끝각에서 정확히 자른다
PORTUS_MOLES = {"r_out": 21.0, "r_in": 18.4, "arm_a_deg": [263.0, 123.0], "arm_b_deg": [277.0, 417.0], "cut_exact": True, "colonnade_deg": [12.0, 54.0],
                "note": "팔 A는 263°에서 123°까지(바다 쪽, 창고는 150~210°), 팔 B는 277°에서 417°(=57°)까지. 열주는 팔 B의 12~54°에만. 263°~277° 빈 곳은 외항 쪽 운하, 57°~123° 입구는 등대섬"}
# 등대섬(입구 인공섬). 탑 치수는 d2 그림 그대로(평면 반폭·높이 mm)
PORTUS_LIGHTHOUSE = {"plan_angle_deg": 78.0, "plan_r": 22.0, "screen_base": [15.98, 432.35],
                     "island_r": 3.4, "tiers": [[2.8, 1.0, 9.0], [2.25, 9.0, 15.4], [1.75, 15.4, 20.6]], "lantern": [1.1, 20.6, 24.0], "apex_z": 25.4,
                     "note": "외항 중심 기준 평면 78°·반지름 22(평면 (441.57, 423.12)). 섬 반지름·탑 층·높이는 그대로. 섬과 두 팔 끝 사이 물(수면 높이)과 탑 몸통과 두 팔 끝 사이 보이는 물을 모두 4mm 이상 둔다(아래 ground_water_gap_mm·tower_to_arm_tips_mm)"}
PORTUS_LIGHT = None                          # 등대섬 + 탑 투영 외곽(아래에서 portus_light_poly로 계산)


def _polar(c, r, deg):
    return (c[0] + r * math.cos(math.radians(deg)), c[1] + r * math.sin(math.radians(deg)))


def _hull(pts):
    """화면 점들의 볼록 껍질(단조 사슬)"""
    p = sorted(set((round(x, 4), round(y, 4)) for x, y in pts))
    if len(p) < 3:
        return p

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for q in p:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in reversed(p):
        while len(up) >= 2 and cross(up[-2], up[-1], q) <= 0:
            up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]


def portus_light_plan():
    return _polar(PORTUS_BASIN_C, PORTUS_LIGHTHOUSE["plan_r"], PORTUS_LIGHTHOUSE["plan_angle_deg"])


def portus_light_poly():
    """등대섬(평면 원) + 층 탑 + 등롱의 화면 외곽(볼록 껍질)"""
    LX, LY = portus_light_plan()
    L = PORTUS_LIGHTHOUSE
    pts = [to_screen(LX + L["island_r"] * math.cos(math.radians(t)), LY + L["island_r"] * math.sin(math.radians(t))) for t in range(0, 360, 10)]
    for r, z0, z1 in L["tiers"]:
        for z in (z0, z1):
            pts += [to_screen(LX + sx * r, LY + sy * r, z) for sx in (-1, 1) for sy in (-1, 1)]
    r, z0, z1 = L["lantern"]
    pts += [to_screen(LX + r * math.cos(math.radians(t)), LY + r * math.sin(math.radians(t)), z1) for t in range(0, 360, 45)]
    pts.append(to_screen(LX, LY, L["apex_z"]))
    return _hull(pts)


def portus_mole_ends():
    """방파제 두 팔 끝(바깥·안쪽 모서리, 수면 높이 0)의 화면 좌표와 투영 입구 폭(두 팔 바깥 모서리의 화면 x 차)"""
    M = PORTUS_MOLES
    ends = {}
    for k, e in (("arm_a", M["arm_a_deg"][1]), ("arm_b", M["arm_b_deg"][1])):
        ends[k] = {"end_deg": e % 360.0,
                   "out": [round(v, 2) for v in to_screen(*_polar(PORTUS_BASIN_C, M["r_out"], e))],
                   "in": [round(v, 2) for v in to_screen(*_polar(PORTUS_BASIN_C, M["r_in"], e))]}
    return {"ends_screen": ends, "entrance_screen_w_mm": round(abs(ends["arm_b"]["out"][0] - ends["arm_a"]["out"][0]), 2)}


def _seg_dist(p, a, b):
    ax, ay = b[0] - a[0], b[1] - a[1]
    L2 = ax * ax + ay * ay
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * ax + (p[1] - a[1]) * ay) / L2))
    return math.hypot(p[0] - a[0] - t * ax, p[1] - a[1] - t * ay)


def portus_island_water_gap():
    """바닥 높이(z 0)에서 등대섬 외곽과 두 팔 끝 면 사이의 화면 거리(mm)"""
    LX, LY = portus_light_plan()
    R = PORTUS_LIGHTHOUSE["island_r"]
    isl = [to_screen(LX + R * math.cos(math.radians(t)), LY + R * math.sin(math.radians(t))) for t in range(0, 360, 3)]
    M = PORTUS_MOLES
    gap = {}
    for k, e in (("arm_a", M["arm_a_deg"][1]), ("arm_b", M["arm_b_deg"][1])):
        a = to_screen(*_polar(PORTUS_BASIN_C, M["r_in"], e))
        b = to_screen(*_polar(PORTUS_BASIN_C, M["r_out"], e))
        gap[k] = round(min(_seg_dist(p, a, b) for p in isl), 2)
    return gap


def _poly_gap(A, B):
    """두 다각형 외곽 사이 최소 화면 거리(겹치면 0)"""
    if any(_in_cvx(p, _cvx_hull(B)) for p in A) or any(_in_cvx(p, _cvx_hull(A)) for p in B):
        return 0.0
    d = min(_seg_dist(p, B[j], B[(j + 1) % len(B)]) for p in A for j in range(len(B)))
    return min(d, min(_seg_dist(p, A[j], A[(j + 1) % len(A)]) for p in B for j in range(len(A))))


def portus_tip_gaps():
    """render 실측과 같은 정의: 팔 끝 마지막 조각(6.15° 이하, z −0.4~1.0) 외곽 ↔ (1) 탑 층 원통(반지름 0.82배, 8각) 외곽, (2) 등대섬(수면 높이) 외곽"""
    M, L = PORTUS_MOLES, PORTUS_LIGHTHOUSE
    LX, LY = portus_light_plan()
    tower = _cvx_hull([to_screen(LX + r * 0.82 * math.cos(math.radians(t)), LY + r * 0.82 * math.sin(math.radians(t)), z)
                       for (r, z0, z1) in L["tiers"] for z in (z0, z1) for t in range(0, 360, 45)])
    isl = [to_screen(LX + L["island_r"] * math.cos(math.radians(t)), LY + L["island_r"] * math.sin(math.radians(t))) for t in range(0, 360, 10)]
    out = {"tower_to_arm_tips_mm": {}, "island_to_arm_tips_mm": {}}
    for key, (t0, t1) in (("arm_a", M["arm_a_deg"]), ("arm_b", M["arm_b_deg"])):
        n = max(1, int(math.ceil(abs(t1 - t0) / 6.15)))
        ta = t0 + (t1 - t0) * (n - 1) / n
        q = [_polar(PORTUS_BASIN_C, M["r_in"], ta), _polar(PORTUS_BASIN_C, M["r_out"], ta), _polar(PORTUS_BASIN_C, M["r_out"], t1), _polar(PORTUS_BASIN_C, M["r_in"], t1)]
        tip = _cvx_hull([to_screen(x, y, z) for x, y in q for z in (-0.4, 1.0)])
        out["tower_to_arm_tips_mm"][key] = round(_poly_gap(tower, tip), 2)
        out["island_to_arm_tips_mm"][key] = round(_poly_gap(isl, tip), 2)
    return out


def portus_canal_polys():
    """운하 2개의 화면 다각형(수면 높이 0.3)"""
    out = {}
    for c in PORTUS_CANALS:
        (x0, x1), (y0, y1) = c["plan_x"], c["plan_y"]
        out[c["name"]] = [to_screen(x0, y0, 0.3), to_screen(x1, y0, 0.3), to_screen(x1, y1, 0.3), to_screen(x0, y1, 0.3)]
    return out


# 계산값을 사양 사전에 함께 적는다(검사·렌더러가 그대로 읽는다)
PORTUS_MOLES.update(portus_mole_ends())
PORTUS_LIGHTHOUSE["plan"] = [round(v, 2) for v in portus_light_plan()]
PORTUS_LIGHTHOUSE["ground_water_gap_mm"] = portus_island_water_gap()
PORTUS_LIGHTHOUSE.update(portus_tip_gaps())
PORTUS_LIGHTHOUSE["screen_base_calc"] = [round(v, 2) for v in to_screen(*portus_light_plan())]
PORTUS_LIGHT = _bbox(portus_light_poly(), 2)
PORTUS_LIGHTHOUSE["entrance_screen_w_mm"] = PORTUS_MOLES["entrance_screen_w_mm"]
for _c in PORTUS_CANALS:
    _c["screen_w_mm"] = round((_c["plan_x"][1] - _c["plan_x"][0]) * C30, 2)
    _xm = (_c["plan_x"][0] + _c["plan_x"][1]) / 2.0
    _c["screen_axis"] = [[round(v, 2) for v in to_screen(_xm, _c["plan_y"][0])], [round(v, 2) for v in to_screen(_xm, _c["plan_y"][1])]]


def portus_polys():
    hexa = [to_screen(PORTUS_HEX_C[0] + PORTUS_HEX_R * math.cos(math.radians(30 + 60 * k)), PORTUS_HEX_C[1] + PORTUS_HEX_R * math.sin(math.radians(30 + 60 * k))) for k in range(6)]
    roof = [(x, y - 6.0) for x, y in hexa]
    basin = [to_screen(PORTUS_BASIN_C[0] + PORTUS_BASIN_R * math.cos(math.radians(15 * k)), PORTUS_BASIN_C[1] + PORTUS_BASIN_R * math.sin(math.radians(15 * k))) for k in range(24)]
    return {"육각 내항(육지)": [hexa, roof], "클라우디우스 외항(바다)": [basin], "등대(인공섬)": [portus_light_poly()]}


# 심은 지면(올리브 숲·포도밭·곡식밭): 베이징 밀도 46.2%가 녹지·연못 받침을 포함한 것처럼, 덮는 비율을 곱해 밀도에 따로 더한다
PLANTED = [
    {"name": "남동 교외 포도밭(오른쪽 아래, 블리드)", "box": [296.0, 444.0, 420.0, 505.0], "cover": 0.35},
    {"name": "아피아 가도 둘레 사이프러스·소나무 열", "box": [352.0, 240.0, 420.0, 290.0], "cover": 0.3},
    {"name": "시내 언덕 올리브 숲(판테온·트라야누스 시장·콜로세움 사이)", "box": [112.0, 190.0, 178.0, 236.0], "cover": 0.4,
     "note": "d4: 오른쪽 변을 막센티우스 바실리카 상자 왼쪽 변(x 178)까지 줄였다(네로 거상 상자도 그 오른쪽)"},
    {"name": "강 오른쪽 둑 곡식밭(포르투스 띠 위쪽)", "box": [0.0, 329.5, 60.0, 372.0], "cover": 0.35,
     "note": "d4: 위 변을 마르켈루스 극장 상자 아래 변(329.3) 밑으로 내렸다"},
    {"name": "남동 교외 밭(수도교와 아피아 가도 사이)", "box": [376.0, 214.0, 420.0, 240.0], "cover": 0.3},
    {"name": "하구 왼쪽 둑 소나무(오스티아 둘레)", "box": [150.0, 456.0, 230.0, 500.0], "cover": 0.25},
]


# ═════════════ 실제 좌표(조사 보고서 4.2절, 근사) ═════════════
GEO_COLOSSEUM = (41.8902, 12.4922)
GEO_EXTRA = [
    {"name": "테베레 하구(오스티아 쪽, 근사)", "geo": (41.7400, 12.2390), "screen": RIVER_MOUTH_SCREEN, "note": "[근사] 고대 하구 위치는 지금과 다르다"},
    {"name": "알바노 구릉(몬테 카보)", "geo": (41.7510, 12.7090), "screen": (338.0, 146.0), "note": "d4: 구릉 띠 [318,122,420,162] 안, 베수비오·농장 왼쪽"},
    {"name": "오스티아 안티카(근사)", "geo": (41.7556, 12.2917), "screen": (226.0, 474.0), "note": "[근사] d4: 오스티아 소품 상자 중심"},
]
# 추가 랜드마크 L7~L9의 geo·real은 LANDMARKS에 있다(지리 검사가 LANDMARKS를 돈다). 배치는 구역 서사 우선이고 방위 오차는 기록만 한다
GEO_NOTE = "L7~L9는 구역 서사(시내 뒤쪽·테베레 굽이·판테온과 강 사이)를 먼저 따르고, 실제 방위·거리 오차는 v2_check geo 표에 기록만 한다"
