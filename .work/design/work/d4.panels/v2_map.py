# -*- coding: utf-8 -*-
"""설계안 — Core 지도(히어로·랜드마크·강·바다·길·수도교·소품·지형·심은 지면·포르투스·지리). 담당: map

d3 변경(사용자 검토 2026-10-19 02:24 반영)
- R 자리 (298,20)~(420,92)를 '가장 먼 곳' 지면으로 돌려준다: 베수비오·포도밭 농장·알바노 구릉 띠를 올리고 먼 밭만 둔다(건물·글·틀 0개).
- T 자리 (312,505)~(420,568)를 남동 교외 밭·포도밭으로 돌려준다(고요한 영역, 글·틀 0개).
- 길은 그림 좌표 그대로 적는다(렌더러의 연장 하드코딩을 사양으로 옮김). 욕장 진입로 R5, 메텔라 진입로 R6a·R6b를 더한다.
- 수도교는 아쿠아 마르키아에서 갈라진 아쿠아 안토니니아나(욕장 급수 관계 모식)로 바로잡는다[S47][S49].
- 포르투스 운하·방파제 두 팔·등대섬, 히어로 내부 형태를 사양으로 적는다(원본은 이 파일, 그림은 render)."""
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
]

# 수도교 지면선 = 화면 ↘ 직선(평면 Y 상수): 카라칼라 욕장 오른쪽 변 (334, 160) → 오른쪽 변 밖(블리드)
AQUEDUCT_PLAN = [to_plan(336.0, 160.0), to_plan(424.0, 160.0 + T30 * 88.0)]
AQUEDUCT_H = 26.0

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
     "form": "실제 경로가 아니라 욕장 급수 관계 모식(아쿠아 마르키아 → 아쿠아 안토니니아나 → 욕장 저수조 64개). 오른쪽 변 밖(남동 시골)에서 ↖로 들어와 카라칼라 욕장 오른쪽 변 (336, 160)에 닿는 아치 열, 높이 26mm(2단 아치), 교각 약 8mm 간격. 맨 위 수로에 물빛 선. 벽돌면 보수 구간 덧댐은 그리지 않는다(이 수도의 근거가 없다)",
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
]
BACKGROUND = [
    {"id": "V", "name": "베수비오(지도 배경, 가장 먼 곳)", "latin": "Vesuvius", "box": [330.0, 30.0, 388.0, 70.0], "zone": "가장 먼 곳(R 자리까지 넓힌 오른쪽 위 지면)",
     "geo": (40.8213, 14.4261), "real": "콜로세움에서 200 km 남동(126°)",
     "form": "79년 이전 모습: 넓고 완만한 봉우리 하나, 잿빛 평평한 정상, 포도밭 비탈. 축척 약 0.6, 대기 원근(바탕색 50% 혼합·흐림), 밑동은 알바노 구릉 띠와 포도밭 농장이 가린다(그리는 순서 산 → 농장 → 구릉, 구릉 능선이 밑동 3~5mm를 가린다). 연기 없음",
     "story": "79년 분화", "number": "로마에서 남동쪽 약 200 km",
     "links": "알바노 구릉 띠(지면), 포도밭 농장"},
]

# ═════════════ Core 지도 소품(탈것·시설·지형) ═════════════
PROPS = [
    {"name": "테베레 하역장(엠포리움: 돌 부두·기중기·창고)", "box": [107.4, 348.0, 154.2, 389.0], "zone": "강 왼쪽(북동) 둑", "on": "땅+물(부두)", "note": "하역장 길의 끝. 바지선이 생석회·골재를 내린다"},
    {"name": "석회 가마", "box": [90.1, 303.0, 114.3, 335.0], "zone": "강 왼쪽 둑", "on": "땅", "note": "김·연기는 알파 40 이하 레이어"},
    {"name": "재료 수레", "box": [156.0, 366.0, 176.0, 378.0], "zone": "하역장 길 위", "on": "길", "plan": [462.3, 278.0], "note": "콜로세움 공사장 쪽으로 가는 수레(그리기 기준점 평면 (462.3, 278.0) = d2 그림 자리)"},
    {"name": "바지선 1(올라가는 배)", "box": [64.0, 348.0, 100.0, 368.0], "zone": "테베레 ↘ 팔", "on": "물", "note": "포르투스에서 환적한 짐을 싣고 상류로"},
    {"name": "바지선 2(내려가는 배)", "box": [150.0, 428.0, 184.0, 446.0], "zone": "테베레 ↙ 팔", "on": "물", "note": "하구 쪽으로"},
    {"name": "화산재 운반선", "box": [112.0, 476.0, 152.0, 500.0], "zone": "바다", "on": "물", "note": "나폴리만 화산재(바다 공사용)를 싣고 포르투스 외항으로"},
    {"name": "오스티아(창고 몇 채)", "box": [176.0, 448.0, 206.0, 470.0], "zone": "하구 왼쪽 둑", "on": "땅", "note": "작은 소품. 바닥 글 OSTIA"},
    {"name": "포도밭 농장(베수비오 밑동)", "box": [336.0, 54.0, 378.0, 76.0], "zone": "가장 먼 곳(R 자리)", "on": "땅", "note": "베수비오 밑동을 가린다(1.6절 포도밭 근거). 산 다음, 알바노 구릉 능선 전에 그린다"},
    {"name": "아피아 가도 수레", "box": [350.0, 266.0, 370.0, 282.0], "zone": "아피아 가도 위", "on": "길", "plan": [485.6, 72.0],
     "note": "남동 교외로 가는 짐수레. d2 그림 자리 그대로 둔다(기준점 평면 (485.6, 72.0) = 화면 (358.2, 278.8), 그린 외곽 352.6~368.8×268.8~280.4). 상자만 메텔라 진입로 R6a 띠 밖으로 줄였다(R6a와 1.2mm, VIA APPIA 바닥 글과 2.3mm). 결정 상자 (364,256)~(388,272)는 VIA APPIA 바닥 글(화면 371.3~413.8×241.6~266.1)과 겹쳐 쓰지 않는다"},
    {"name": "교외 빌라(포도밭 농가)", "box": [306.0, 464.0, 328.0, 484.0], "zone": "남동 교외 밭", "on": "땅", "note": "작은 농가, 라벨 없음. 콜아웃 C4(아래 변 456)와 S 패널(왼쪽 변 332) 사이로 옮겼다"},
]
TERRAIN = [
    {"name": "알바노 구릉 띠(화산 지대, 낮은 구릉)", "box": [300.0, 64.0, 420.0, 160.0],
     "note": "지면 결. 화산 그림이 아니다. 능선이 베수비오 밑동 3~5mm를 가린다: 산 → 농장 → 구릉 순. 바닥 글 'COLLI ALBANI 알바노 구릉 — 로마 건물의 화산재'",
     "ridge": {"cover_vesuvius_base_mm": [3.0, 5.0], "order": ["베수비오", "포도밭 농장", "알바노 구릉 능선"],
               "x_ranges": [[330.0, 336.0], [378.0, 388.0]], "farm_front_top_y_min": 76.0,
               "note": "맨 뒤 능선의 윗선을 베수비오 밑동 윤곽(앞쪽 반 타원)보다 3~5mm 위에 둔다. 농장이 이미 밑동을 가리는 x 336~378 구간은 능선 꼭대기를 농장 아래 변 y 76 아래로 낮춰 농장을 가리지 않는다"}},
    {"name": "R 자리 먼 캄파냐 밭", "box": [298.0, 20.0, 420.0, 92.0],
     "note": "가장 먼 곳 구역. 베수비오·포도밭 농장·알바노 구릉 띠(위 끝)·베수비오 깃대 라벨 말고는 건물·글·틀 0개, 먼 밭·구릉 결만 둔다(대기 원근으로 흐리게). 위 변 y 20은 L 패널 윗선과 같고 닫는다. 왼쪽 변 x 298은 타이틀 오른쪽 변 293.5와 4.5mm. 오른쪽은 블리드"},
    {"name": "남동 교외 밭·포도밭(캄파냐)", "box": [296.0, 396.0, 420.0, 568.0],
     "note": "S 패널·콜아웃 C4가 앉는 고요한 영역. T 자리 (312,505)~(420,568)까지 넓혀 하단 띠 오른쪽을 지도로 돌려준다(글·틀 0개). 오른쪽은 블리드, T 자리 아래 변은 푸터 윗선 y 568에서 닫는다. 해안선(y = tan30·x + 380) 아래인 T 자리 왼쪽 아래 귀퉁이는 띠 밑 바다로 둔다(sea_corner, 밭 0)",
     "sea_corner": [[312.0, round(T30 * 312.0 + COAST_Y, 2)], [round((568.0 - COAST_Y) / T30, 2), 568.0], [312.0, 568.0]]},
    {"name": "시내 지붕 블록·나무(콜로세움 둘레)", "box": [112.0, 186.0, 300.0, 300.0], "note": "지스몬디 '지붕의 바다' 밀도, 언덕에 나무 덩어리"},
    {"name": "오른쪽 둑 들판(포르투스 띠)", "box": [0.0, 316.0, 200.0, 440.0], "note": "강과 해안 사이 육지 띠, 곡식밭"},
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
    {"name": "강 쪽 운하", "plan_x": [435.5, 438.5], "plan_y": [322.84, 338.6],
     "note": "테베레 오른쪽 둑(강 수면 0.4 안) → 육각 내항 수면(270° 꼭짓점 안쪽). 육각 포장·성벽·창고 고리에 폭 3mm 개구부"},
    {"name": "외항 쪽 운하", "plan_x": [435.5, 438.5], "plan_y": [368.6, 384.0],
     "note": "육각 내항 수면(90° 꼭짓점 안쪽) → 해안선(Y 380)을 지나 외항 수면 안쪽(방파제 두 팔 사이 263°~277° 빈 곳을 지난다)"},
]
# 외항 방파제 두 팔(평면 각도는 외항 중심 기준, 0° = +X). 마지막 조각은 끝각에서 정확히 자른다
PORTUS_MOLES = {"r_out": 21.0, "r_in": 18.4, "arm_a_deg": [263.0, 123.0], "arm_b_deg": [277.0, 417.0], "cut_exact": True, "colonnade_deg": [12.0, 54.0],
                "note": "팔 A는 263°에서 123°까지(바다 쪽, 창고는 150~210°), 팔 B는 277°에서 417°(=57°)까지. 열주는 팔 B의 12~54°에만. 263°~277° 빈 곳은 외항 쪽 운하, 57°~123° 입구는 등대섬"}
# 등대섬(입구 인공섬). 탑 치수는 d2 그림 그대로(평면 반폭·높이 mm)
PORTUS_LIGHTHOUSE = {"plan_angle_deg": 90.0, "plan_r": 24.0, "screen_base": [9.87, 431.3],
                     "island_r": 3.4, "tiers": [[2.8, 1.0, 9.0], [2.25, 9.0, 15.4], [1.75, 15.4, 20.6]], "lantern": [1.1, 20.6, 24.0], "apex_z": 25.4,
                     "note": "평면 (437.0, 425.6). 섬과 두 팔 끝 사이 물은 수면 높이에서 4mm 이상(ground_water_gap_mm: 팔 A 6.9 · 팔 B 11.5). 다만 탑(높이 25.4)이 화면에서 섬보다 뒤에 있는 팔 A 끝(화면 5.5~8.6 × 421~422)과 겹쳐, 탑 몸통과 팔 A 끝 사이에 보이는 물은 거의 없다(앞에 선 탑이 뒤 방파제 끝을 가린다)"}
PORTUS_LIGHT = [4.9, 404.0, 14.9, 435.0]     # 등대섬 + 탑 투영 외곽(목표)


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
    {"name": "시내 언덕 올리브 숲(판테온·트라야누스 시장·콜로세움 사이)", "box": [112.0, 190.0, 226.0, 236.0], "cover": 0.4},
    {"name": "강 오른쪽 둑 곡식밭(포르투스 띠 위쪽)", "box": [0.0, 326.0, 60.0, 372.0], "cover": 0.35},
    {"name": "남동 교외 밭(수도교와 아피아 가도 사이)", "box": [376.0, 214.0, 420.0, 240.0], "cover": 0.3},
    {"name": "하구 왼쪽 둑 소나무(오스티아 둘레)", "box": [150.0, 456.0, 230.0, 500.0], "cover": 0.25},
    {"name": "T 자리 남동 포도밭", "box": [312.0, 505.0, 420.0, 568.0], "cover": 0.35},
    {"name": "R 자리 먼 밭", "box": [298.0, 24.0, 420.0, 92.0], "cover": 0.35},
]


# ═════════════ 실제 좌표(조사 보고서 4.2절, 근사) ═════════════
GEO_COLOSSEUM = (41.8902, 12.4922)
GEO_EXTRA = [
    {"name": "테베레 하구(오스티아 쪽, 근사)", "geo": (41.7400, 12.2390), "screen": RIVER_MOUTH_SCREEN, "note": "[근사] 고대 하구 위치는 지금과 다르다"},
    {"name": "알바노 구릉(몬테 카보)", "geo": (41.7510, 12.7090), "screen": (360.0, 112.0)},
    {"name": "오스티아 안티카(근사)", "geo": (41.7556, 12.2917), "screen": (191.0, 466.0), "note": "[근사]"},
]
