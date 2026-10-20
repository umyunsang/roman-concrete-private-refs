# -*- coding: utf-8 -*-
"""설계안 — Core 지도(히어로·랜드마크·강·바다·길·수도교·소품·지형·심은 지면·포르투스·지리). 담당: map

d5 변경(기준선 8.1·8.2 + 사용자 12:49 철회, 통합 루프 0-1절, 공통 결정 D2~D7·D12·D13)
- 팔각 받침을 지웠다(HERO_R·HERO_SIDE·HERO_RING·HERO_WALLS·hero_oct·hero_ring_pt·HERO_CUTAWAY 삭제). 콜로세움과 조경은 땅(Z 0) 위에 바로 놓이고 옆면은 0mm다.
- 콜로세움 본체를 LocalBanana 구성으로 다시 적었다(HERO_COLOSSEUM, D2): 외곽 타원 평면 반축 44.0×36.6·장축 방위 315°(화면 가로)·중심 평면 (446.54, 161.86),
  아치 40칸, θ별 외벽 높이 표, 둘째 고리 37(정면 10~80°만 9~12), 관람석·계단석 구역, 경기장 반축 20.1×12.7, 나무 바닥(u ≥ −2.0)·하이포게움(u < −2.0).
  내부 표는 HERO_INTERIOR 하나다(render·hero가 이 표만 읽는다). d4의 ring_ratio 0.74·벽 60/28/12·원형 고리·가로벽 격자 하이포게움 표는 폐기했다.
- 조경(HERO_LANDSCAPE): 사용자 12:49 철회에 따라 LocalBanana 조경 배치(기둥 폐허·쓰러진 토막·단칸 아치·벽돌 담·작은 신전·열주·6주 신전 앞면·포장 고리·판석 갈래길·노점 배치)는 옮기지 않는다.
  둘레는 땅 바탕뿐이다(사용자 16:13·16:14): 광장·판석·둘레 나무·인물 무리·노점·기초 공사장·시내 지붕·길은 지도에서 지웠고, Core 건축물과 네로 거상 받침(작은 마당 포함)만 남는다.
  예약 반지름은 평면 90(옛 히어로 자리), 비례는 건물 폭 / 조경 대표 폭 = 0.53.
- 투영 상자를 셋으로 나눴다: 건물·조경 예약 원(비워 두는 땅)·히어로(HERO_BOXES). 길 R1~R7은 사용자 16:14로 없어졌다(다리 북쪽 끝은 진입 경사로 땅에 잇는다).
- 영묘–다리 높이 접속(다리 북쪽 진입 경사·기단 북쪽 디딤 2단), L5 그림 1.04배, L6·L9 상자 실측 정정, L5 겉면 문구, 네로 마당, Blender 무대·높이 기준(BLENDER_GEO).

d4 변경(사용자 검토 2026-10-19 02:24 + 사용자 선택 03:10, 기준선 7절)
- 무대 확장(R·T 자리) 해제, 베수비오 군을 지도 무대 오른쪽 위로, 랜드마크 3개 추가(L7·L8·L9), 새 길 R7, 소품 '네로 청동 거상과 콘크리트(벽돌 마감) 받침'.
- 소품 재배치(석회 가마·바지선 2·오스티아), 포르투스 등대섬 78°·반지름 22, 운하 plan_y = 그린 끝점, 수도교 관통 아치."""
from v2_base import *  # noqa: F401,F403

# ═════════════ Core 히어로: 콜로세움(기준선 8.1·8.2, 공통 결정 D2·D3) ═════════════
# 비워 두는 땅 중심 = 옛 히어로 중심. 받침은 없다: 콜로세움은 땅 윗면(Z 0)에 바로 놓인다(옆면 0mm)
HERO_C = (233.5, 296.0)          # 조경 중심(화면)
HERO_C_PLAN = to_plan(*HERO_C)   # 조경 중심(평면) = (462.34, 173.66)

# ── 콜로세움 본체(D2). 방위 θ = atan2(평면 dY, 평면 dX)(Blender roma_kit.plan_az와 같다):
#    0° 화면 오른쪽 아래, 45° 정면 아래, 135° 왼쪽, 225° 위, 315° 오른쪽
COLO_C_PLAN = (HERO_C_PLAN[0] - 15.8, HERO_C_PLAN[1] - 11.8)   # 외곽 타원 중심(평면) = 조경 중심 + (−15.8, −11.8): LocalBanana처럼 뒤-왼쪽으로 물림
COLO_AXES = (44.0, 36.6)         # 외곽 타원 반축(평면): 장축 · 단축
COLO_MAJOR_AZ = 315.0            # 장축 평면 방위(화면 가로)
COLO_STOREY_Z = [11.5, 24.5, 37.0, 53.0]
# θ별 외벽 높이(평면 방위 범위, 높이 mm). 0°를 지나는 구간은 t1 < t0로 적는다(338 → 18 = 338~360° + 0~18°)
COLO_WALLS = [
    {"t0": 80, "t1": 100, "h": 37.0, "part": "앞-왼쪽 3층"},
    {"t0": 100, "t1": 104, "h": 41.0, "part": "경사 부벽 1단(4층 조각 앞쪽 끝)"},
    {"t0": 104, "t1": 108, "h": 46.0, "part": "경사 부벽 2단"},
    {"t0": 108, "t1": 112, "h": 50.0, "part": "경사 부벽 3단"},
    {"t0": 112, "t1": 205, "h": 53.0, "part": "4층 외벽 조각(왼쪽~뒤-왼쪽)"},
    {"t0": 205, "t1": 209, "h": 44.0, "part": "뒤쪽 끝 수직 끊김"},
    {"t0": 209, "t1": 322, "h": 37.0, "h_range": [33.5, 37.0], "part": "뒤~오른쪽 3층(일부 33.5)"},
    {"t0": 322, "t1": 330, "h": 31.0, "part": "3층 → 2층 계단 1"},
    {"t0": 330, "t1": 338, "h": 27.0, "part": "3층 → 2층 계단 2"},
    {"t0": 338, "t1": 18, "h": 24.5, "h_range": [18.0, 24.5], "part": "앞-오른쪽 2층(윗선 들쭉날쭉 18.0~24.5)"},
    {"t0": 18, "t1": 72, "h": 17.0, "h_range": [14.0, 17.0], "part": "경기장 앞 정면: 1층 + 부서진 2층 토막(상한 17.0)"},
    {"t0": 72, "t1": 80, "h": 30.0, "part": "앞-왼쪽 3층 → 정면 낮춤"},
]
COLO_SECOND_RING = {"h": 37.0, "front_az": [10, 80], "front_h": [9.0, 12.0], "front_h_max": 12.0,
                    "front_low": {"t0": 10, "t1": 80, "h_range": [9.0, 12.0]}, "t": 1.6, "depth_from_outer": [5.2, 6.8],
                    "note": "둘째 고리(안쪽 아케이드) 3층 37. 정면 10~80°만 9~12로 무너졌다"}
COLO_SHELL = {"outer_wall_t": 2.4, "outer_corridor_w": 2.8, "second_ring_t": 1.6,
              "note": "외곽에서 깊이 0~2.4 외벽, 2.4~5.2 바깥 회랑, 5.2~6.8 둘째 고리, 6.8~10.4 안쪽 회랑"}
COLO_ARENA_AXES = (20.1, 12.7)   # 경기장 반축(평면) = 외곽 반축 − 23.9
COLO_U_SPLIT = -2.0              # 장축 좌표 u(평면 방위 315° 쪽이 +) ≥ −2.0 나무 바닥, < −2.0 하이포게움

# 내부 표(HERO_INTERIOR) — render와 hero(Blender roma_colo_in)가 이 표 하나만 읽는다(D2)
HERO_INTERIOR = {
    "source": "기준선 8.1 + 공통 결정 D2(LocalBanana 첨부 이미지 실측). d4 표(바닥 −5 화면 낮춤·장축 통로 1 + 평행 2·가로벽 7·통과 개구부·관람석 4층·방사 계단 12·4층 조각 2 깊이 층)는 폐기",
    "axes": {"center_plan": list(COLO_C_PLAN), "major_az_deg": COLO_MAJOR_AZ, "u": "장축 좌표(평면 방위 315° = 화면 오른쪽이 +)", "v": "단축 좌표(평면 방위 45° = 화면 정면 아래가 +)"},
    "cavea": {"depth_from_outer": [10.4, 22.7], "h_outer_to_inner": [24.0, 4.4],
              "stepped_zones_deg": [[238.0, 360.0], [0.0, 48.0]], "stepped": "계단석(줄눈 있는 단, 단 높이 약 1.0)",
              "other_zones": "방사벽 + 짙은 빈칸(무너진 볼트, L1 깊이색)", "radial_wall_every_deg": 9.0,
              "note": "관람석은 외곽에서 깊이 10.4(높이 24.0)부터 22.7(높이 4.4)까지 내려간다. 계단석은 θ 238~360°·0~48°(오른쪽 구역), 나머지는 방사벽·빈칸"},
    "podium_wall": {"depth_from_outer": [22.7, 23.9], "h": 4.4, "note": "경기장을 두른 포디움 벽(윗면 4.4)"},
    "arena": {"semi_axes_plan": list(COLO_ARENA_AXES), "center_plan": list(COLO_C_PLAN), "major_az_deg": COLO_MAJOR_AZ},
    "wood_floor": {"u_range": [COLO_U_SPLIT, COLO_ARENA_AXES[0]], "share": 0.55, "wood_frac": 0.55, "u_split": COLO_U_SPLIT, "z": 0.6, "railing": True,
                   "note": "복원 나무 바닥(오른쪽 약 55%, 윗면 Z 0.6) + 하이포게움 쪽 끝 난간. 판자 결은 장축(u) 방향"},
    "hypogeum": {"u_range": [-COLO_ARENA_AXES[0], COLO_U_SPLIT], "floor_z": -4.0,
                 "rings_frac": [0.86, 0.72, 0.58, 0.44, 0.30], "central_corridor_half_w": 0.9,
                 "partitions": {"every_deg": 12.0, "r_frac": [0.33, 0.97]}, "wall_t": [0.45, 0.55],
                 "cut": "X_CUT_HeroPit: 경기장 u < −2.0을 Z −4.0까지 파낸다(ground가 맨 끝에 적용)",
                 "note": "동심 벽(경기장 반축의 0.86·0.72·0.58·0.44·0.30배) + 장축 중앙 통로(±0.9) + 12°마다 칸막이(반지름 비 0.33~0.97), 벽 두께 0.45~0.55, 바닥 Z −4.0"},
    "second_ring": COLO_SECOND_RING,
    "shell": COLO_SHELL,
}


def colo_r(theta_deg, depth=0.0):
    """외곽 타원(깊이 depth만큼 안쪽으로 줄인 타원) 위 평면 방위 θ의 평면 반지름"""
    a, b = COLO_AXES[0] - depth, COLO_AXES[1] - depth
    t = math.radians(theta_deg - COLO_MAJOR_AZ)
    return 1.0 / math.sqrt((math.cos(t) / a) ** 2 + (math.sin(t) / b) ** 2)


def colo_plan_pt(theta_deg, depth=0.0):
    r = colo_r(theta_deg, depth)
    return (COLO_C_PLAN[0] + r * math.cos(math.radians(theta_deg)), COLO_C_PLAN[1] + r * math.sin(math.radians(theta_deg)))


def _az_in(t, t0, t1):
    """방위 t가 [t0, t1) 안인가(t1 < t0이면 0°를 지나는 구간)"""
    t, t0, t1 = t % 360.0, t0 % 360.0, t1 % 360.0
    return (t0 <= t < t1) if t0 < t1 else (t >= t0 or t < t1)


def colo_wall_h(theta_deg):
    """외벽 높이(표의 상한값). 들쭉날쭉한 구간도 상한으로 잰다(투영 상자·실루엣용)"""
    for w in COLO_WALLS:
        if _az_in(theta_deg, w["t0"], w["t1"]):
            return w["h"]
    return COLO_WALLS[0]["h"]


def _second_ring_h(theta_deg):
    fz = COLO_SECOND_RING["front_az"]
    return COLO_SECOND_RING["front_h_max"] if _az_in(theta_deg, fz[0], fz[1]) else COLO_SECOND_RING["h"]


def colo_silhouette(step_deg=0.5, dx=0.5):
    """콜로세움 건물의 화면 실루엣(열 단위: 위 = 외벽·둘째 고리·관람석 윗선의 최소 y, 아래 = 외곽 타원 앞 가장자리).
    벽은 화면에서 수직이라 열마다 [위, 아래] 한 구간이다. 결과는 위 윤곽(왼→오) + 아래 윤곽(오→왼)"""
    tops, bases = [], []
    n = int(round(360.0 / step_deg))
    for i in range(n):
        th = i * step_deg
        X, Y = colo_plan_pt(th)
        tops.append(to_screen(X, Y, colo_wall_h(th)))
        bases.append(to_screen(X, Y, 0.0))
        X2, Y2 = colo_plan_pt(th, COLO_SECOND_RING["depth_from_outer"][0])
        tops.append(to_screen(X2, Y2, _second_ring_h(th)))
        X3, Y3 = colo_plan_pt(th, HERO_INTERIOR["cavea"]["depth_from_outer"][0])
        tops.append(to_screen(X3, Y3, HERO_INTERIOR["cavea"]["h_outer_to_inner"][0]))
    x0 = min(p[0] for p in bases)
    x1 = max(p[0] for p in bases)
    m = int((x1 - x0) / dx)
    xs = [x0 + (x1 - x0) * k / m for k in range(m + 1)]

    def col(pts, x, fn):
        best = None
        for i in range(len(pts)):
            (ax, ay), (bx, by) = pts[i], pts[(i + 1) % len(pts)]
            if (ax - x) * (bx - x) <= 0 and ax != bx:
                y = ay + (by - ay) * (x - ax) / (bx - ax)
                best = y if best is None else fn(best, y)
        return best
    ring_tops = [tops[k] for k in range(0, len(tops), 3)]
    ring2 = [tops[k] for k in range(1, len(tops), 3)]
    cav = [tops[k] for k in range(2, len(tops), 3)]
    up, lo = [], []
    for x in xs:
        cands = [v for v in (col(ring_tops, x, min), col(ring2, x, min), col(cav, x, min)) if v is not None]
        ylo = col(bases, x, max)
        if not cands or ylo is None:
            continue
        up.append((x, min(cands)))
        lo.append((x, ylo))
    # 양 끝 열: 외곽 타원 좌우 끝점의 벽 높이
    return up + lo[::-1]


def _poly_area(poly):
    s = 0.0
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


HERO_SCALE = 1.188                # 위계 1번 콜로세움: 그림 전체를 1.25배(실루엣 면적 약 1.56배)
_cs = to_screen(*COLO_C_PLAN)
COLO_SIL = [(_cs[0] + HERO_SCALE * (x - _cs[0]), _cs[1] + HERO_SCALE * (y - _cs[1])) for x, y in colo_silhouette()]
COLO_BASE_SCREEN = [to_screen(*colo_plan_pt(t)) for t in range(0, 360, 3)]

# ── 조경(D3 중 12:49 철회 뒤 남는 것). 받침 0: 옆면 0mm, 외곽 테두리·지층·앞 변 단면 없음
LAND_RESERVE_R = 90.0            # 예약 반지름(평면). 다른 패키지는 이 안에 아무것도 두지 않는다(길 R1·R4·R7의 문 접속만 예외)
LAND_REP_R = 83.1             # 비례 기준 반지름(평면): 화면 폭 203.5 → 콜로세움 폭 비 0.53(기준 폭일 뿐, 땅에 그리는 것은 없다)


def _reserve_screen_poly(R, n=96):
    X0, Y0 = HERO_C_PLAN
    return [to_screen(X0 + R * math.cos(2 * math.pi * k / n), Y0 + R * math.sin(2 * math.pi * k / n)) for k in range(n)]


RESERVE_SCREEN = _reserve_screen_poly(LAND_RESERVE_R)


def _box2(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return [round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2)]


HERO_BOXES = {
    "building": _box2(COLO_SIL),
    "landscape": _box2(RESERVE_SCREEN),
    "note": "건물 = 콜로세움 실루엣 외곽 상자, landscape = 비워 두는 땅(평면 R 90.5) 화면 상자(사용자 16:13·16:14: 땅 바탕뿐), cluster = d4 기록(위계에 쓰지 않음). 위계의 히어로 = 콜로세움 건물",
}
HERO_BOXES["cluster"] = [min(HERO_BOXES["building"][0], HERO_BOXES["landscape"][0]), min(HERO_BOXES["building"][1], HERO_BOXES["landscape"][1]),
                         max(HERO_BOXES["building"][2], HERO_BOXES["landscape"][2]), max(HERO_BOXES["building"][3], HERO_BOXES["landscape"][3])]
for _k in ("building", "landscape", "cluster"):
    _b = HERO_BOXES[_k]
    HERO_BOXES[_k + "_wh"] = [round(_b[2] - _b[0], 2), round(_b[3] - _b[1], 2)]
    HERO_BOXES[_k + "_area_mm2"] = round((_b[2] - _b[0]) * (_b[3] - _b[1]), 1)
HERO_BOXES["building_silhouette_area_mm2"] = round(_poly_area(COLO_SIL), 1)
HERO_BOXES["width_ratio_building_over_rep"] = round(HERO_BOXES["building_wh"][0] / (2.0 * LAND_REP_R * 1.2247449), 3)

# ═════════════ 테베레강(평면 직교 꺾임 1회, 둥근 굽이) ═════════════
# 19:25 사용자가 시안 위에 그린 경로: 오른쪽 가장자리(❸ 아래)에서 들어와 ↙ 대각선으로 지도 가운데를 지나, ↘로 꺾였다가 다시 ↙로 왼쪽 아래 바다(출구 ❹ 쪽)로 나간다.
# 20:40 사용자: 강·길은 평면 X·Y 축(화면 ±30°)으로만, 꺾임은 직각.
# 20:53 사용자: 강 = 디오라마 블록 사이 큰 구분선(중앙 군집을 가르지 않는다). 20:55: 블록 4개에 Core를 위계 균형으로 나눈다.
#   테베레 = 지도 오른쪽 아래를 지나는 Y축 직선 하나(입구 오른쪽 가장자리 → 왼쪽 아래 바다 어귀), 블록 사이 운하 4줄(X·Y축).
#   블록: A 콜로세움(중앙) · B 남쪽(포르투스·영묘·바실리카) · C 북동(시장·수도교·메텔라) · D 서쪽(판테온·극장·욕장).
TIBER_X, TIBER_HW = 582.5, 13.0                                    # 테베레: X = 582.5 (↙ 직선), 반폭 13(화면 수직 폭 26)
CANAL_HW = 6.0                                                     # 블록 사이 운하 반폭(평면) = 화면 수직 폭 12
KV_X, KH1_Y, KH2_Y, KV2_X = 350.0, 185.0, 85.0, 478.0               # 운하 선: A 서쪽 · 남서쪽 경계 · A 북쪽 · A 동쪽
KH3_Y = 214.0                                                       # A·C 아래(B와의 경계)
_COAST_PLAN_Y = 380.0
WATER_RECTS = [
    {"id": "tiber", "name": "테베레강", "X": [TIBER_X - TIBER_HW, TIBER_X + TIBER_HW], "Y": [-300.0, _COAST_PLAN_Y + 40.0]},
    {"id": "canal_v1", "name": "A 서쪽 운하(C | A)", "X": [KV_X - CANAL_HW, KV_X + CANAL_HW], "Y": [KH2_Y - CANAL_HW, KH3_Y + CANAL_HW]},
    {"id": "canal_h1", "name": "남서 경계 운하(C | B)", "X": [60.0, KV_X + CANAL_HW], "Y": [KH1_Y - CANAL_HW, KH1_Y + CANAL_HW]},
    {"id": "canal_h3", "name": "A·C 아래 운하(A·C | B)", "X": [KV_X, TIBER_X - TIBER_HW], "Y": [KH3_Y - CANAL_HW, KH3_Y + CANAL_HW]},
    {"id": "canal_h2", "name": "A 북쪽 운하(A | C)", "X": [KV_X - CANAL_HW, KV2_X + CANAL_HW], "Y": [KH2_Y - CANAL_HW, KH2_Y + CANAL_HW]},
    {"id": "aniene", "name": "아니에네강(수도교 아래 → A 북쪽 운하로)", "X": [387.0, 403.0], "Y": [-170.0, KH2_Y + 2.0]},
    {"id": "canal_v2", "name": "A 동쪽 운하(A | C)", "X": [KV2_X - CANAL_HW, KV2_X + CANAL_HW], "Y": [KH2_Y, KH3_Y]},
]
RIVER_PLAN = [(TIBER_X, -300.0), (TIBER_X, _COAST_PLAN_Y + 40.0)]
RIVER_SCREEN_PTS = [to_screen(x, y) for x, y in RIVER_PLAN]                           # 테베레 중심선(화면 mm)
RIVER_XA, RIVER_YA, RIVER_XB_ = TIBER_X, KH1_Y, TIBER_X
RIVER_HW = (TIBER_HW, TIBER_HW, TIBER_HW)
RIVER_FILLET = 14.0              # 굽이 중심선 반지름(평면)
RIVER_W1 = 22.0                  # 입구 쪽 화면 수직 폭(mm)
RIVER_W2 = 28.0                  # 어귀 쪽 화면 수직 폭
COAST_Y = 380.0                  # 해안선 = 평면 Y 380 (화면 y = tan30·x + 380)
RIVER_ENTRY_X = 420.0
RIVER_A = RIVER_PLAN[1][1]
RIVER_Y = RIVER_PLAN[1][1]       # (옛 이름 호환)
RIVER_XB = RIVER_PLAN[-1][0]     # (옛 이름 호환: 어귀 쪽 마지막 꼭짓점 평면 X)


def _river_samples(step=3.0):
    """꺾은선을 둥근 모서리(평면 반지름 RIVER_FILLET)로 표본화한다. (X, Y, 진행률 0~1)"""
    P = RIVER_PLAN
    out = [P[0]]
    for i in range(1, len(P) - 1):
        a, b, c = P[i - 1], P[i], P[i + 1]
        v1 = (b[0] - a[0], b[1] - a[1]); v2 = (c[0] - b[0], c[1] - b[1])
        l1 = math.hypot(*v1); l2 = math.hypot(*v2)
        f = min(RIVER_FILLET, l1 / 2.0, l2 / 2.0)
        p1 = (b[0] - v1[0] / l1 * f, b[1] - v1[1] / l1 * f)
        p2 = (b[0] + v2[0] / l2 * f, b[1] + v2[1] / l2 * f)
        out.append(p1)
        for k in range(1, 12):
            t = k / 12.0
            out.append(((1 - t) ** 2 * p1[0] + 2 * t * (1 - t) * b[0] + t ** 2 * p2[0], (1 - t) ** 2 * p1[1] + 2 * t * (1 - t) * b[1] + t ** 2 * p2[1]))
        out.append(p2)
    out.append(P[-1])
    dense = [out[0]]
    for p in out[1:]:
        q = dense[-1]; L = math.hypot(p[0] - q[0], p[1] - q[1]); n = max(1, int(L / step))
        for k in range(1, n + 1):
            dense.append((q[0] + (p[0] - q[0]) * k / n, q[1] + (p[1] - q[1]) * k / n))
    cum = [0.0]
    for a_, b_ in zip(dense[:-1], dense[1:]):
        cum.append(cum[-1] + math.hypot(b_[0] - a_[0], b_[1] - a_[1]))
    return [(x, y, c / cum[-1]) for (x, y), c in zip(dense, cum)]


def river_centerline(step=3.0):
    return _river_samples(step)


def _grid_cells(rects, extra=None):
    xs = sorted({v for r in rects for v in r["X"]} | set(extra[0] if extra else []))
    ys = sorted({v for r in rects for v in r["Y"]} | set(extra[1] if extra else []))
    return xs, ys


def _trace_loops(filled, xs, ys):
    """칸(i,j) 점유 판정 함수 filled → X·Y축 변만의 닫힌 경로(점 목록) 모음. 점유 칸이 왼쪽에 오는 방향."""
    edges = {}
    nx, ny = len(xs) - 1, len(ys) - 1

    def f(i, j):
        return 0 <= i < nx and 0 <= j < ny and filled(i, j)
    for i in range(nx):
        for j in range(ny):
            if not f(i, j):
                continue
            x0, x1, y0, y1 = xs[i], xs[i + 1], ys[j], ys[j + 1]
            if not f(i, j - 1):
                edges.setdefault((x0, y0), []).append((x1, y0))
            if not f(i + 1, j):
                edges.setdefault((x1, y0), []).append((x1, y1))
            if not f(i, j + 1):
                edges.setdefault((x1, y1), []).append((x0, y1))
            if not f(i - 1, j):
                edges.setdefault((x0, y1), []).append((x0, y0))
    loops = []
    while edges:
        start = next(iter(edges))
        loop = [start]
        cur = start
        while True:
            nxt = edges[cur].pop()
            if not edges[cur]:
                del edges[cur]
            if nxt == start:
                break
            loop.append(nxt)
            cur = nxt
        simp = []
        n = len(loop)
        for k in range(n):
            a_, b_, c_ = loop[k - 1], loop[k], loop[(k + 1) % n]
            if (b_[0] - a_[0]) * (c_[1] - b_[1]) - (b_[1] - a_[1]) * (c_[0] - b_[0]) != 0:
                simp.append(b_)
        loops.append(simp)
    return loops


def water_union_plan(rects=None):
    """물 직사각형 합의 바깥 경계(평면 점 목록) 모음"""
    rects = rects or WATER_RECTS
    xs, ys = _grid_cells(rects)

    def filled(i, j):
        cx, cy = (xs[i] + xs[i + 1]) / 2.0, (ys[j] + ys[j + 1]) / 2.0
        return any(r["X"][0] <= cx <= r["X"][1] and r["Y"][0] <= cy <= r["Y"][1] for r in rects)
    return _trace_loops(filled, xs, ys)


def river_polygon():
    """물 합집합의 큰 경계를 화면으로 투영한 다각형(X·Y축 변만 → 화면 ±30° 변)"""
    loops = water_union_plan()
    big = max(loops, key=lambda lp: abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(lp, lp[1:] + lp[:1]))))
    return [to_screen(X, Y) for X, Y in big]


def _coast_cross():
    """강 중심선(화면 꺾은선)이 해안선 y = tan30·x + COAST_Y 를 지나는 점"""
    P = RIVER_SCREEN_PTS
    for (x0, y0), (x1, y1) in zip(P[:-1], P[1:]):
        f0 = y0 - (T30 * x0 + COAST_Y)
        f1 = y1 - (T30 * x1 + COAST_Y)
        if f0 * f1 <= 0 and f0 != f1:
            t = f0 / (f0 - f1)
            return (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
    return P[-1]


# 19:40 아니에네강(지류): 테베레 둑에서 갈라져 수도교 상류 끝(수도교가 시작되는 오른쪽 끝)에 닿는다. 폭 8mm.
RIVER_TRIBS = []                  # 20:53: 지류 대신 블록 사이 운하(WATER_RECTS)가 구분선 역할
RIVER_BEND_SCREEN = RIVER_SCREEN_PTS[1]
RIVER_MOUTH_SCREEN = _coast_cross()
RIVER_ENTRY_SCREEN = (420.0, round(RIVER_SCREEN_PTS[0][1] + (RIVER_SCREEN_PTS[1][1] - RIVER_SCREEN_PTS[0][1]) * (RIVER_SCREEN_PTS[0][0] - 420.0) / (RIVER_SCREEN_PTS[0][0] - RIVER_SCREEN_PTS[1][0]), 1))


def coast_y(x):
    return T30 * x + COAST_Y


COAST = [(0.0, COAST_Y), (round((478.0 - COAST_Y) / T30, 2), 478.0)]       # 사용자 15:41: 무대 아랫선 505 → 478
SEA = [(0.0, COAST_Y), COAST[1], (0.0, 478.0)]
SEA_UNDER_BAND = [COAST[1], (round((568.0 - COAST_Y) / T30, 2), 568.0), (0.0, 568.0), (0.0, 478.0)]

# ═════════════ 길 없음 / 다리 진입 경사 ═════════════
# 사용자 16:14: 길 전부(R1~R7·아피아 가도·메텔라 진입로·시내 길)는 지도에서 지웠다. 다리 북쪽 끝은 길 없이 땅에서 바로 오르는 경사로 잇는다.
_NOFILL_R = 90.5                                        # 비워 두는 반지름(조경 중심 평면): 땅 바탕만, 집·나무·밭·길 0
_MAUS_D = (-27.6, -94.9)                                  # 영묘·다리 평면 이동(17:22 재설계)
_BANK_N = 304.76 + _MAUS_D[1]                              # 다리 북쪽 끝(둑) 평면 Y
_BRIDGE_X = 489.6 + _MAUS_D[0]                                       # 폰스 아일리우스 다리 중심선(평면 X 상수)
# 다리 북쪽 진입 경사(D7): 다리 상판 Z 3.0과 땅(Z 0)의 높이 차를 다리 북쪽 끝 10mm 안에서 잇는다
BRIDGE_RAMP = {"name": "폰스 아일리우스 진입 경사(다리 북쪽 끝)", "X": [round(_BRIDGE_X - 8.0 / (2 * C30), 2), round(_BRIDGE_X + 8.0 / (2 * C30), 2)],
               "Y": [round(_BANK_N - 10.0, 2), round(_BANK_N, 2)], "z": [0.0, 3.0], "owner": "ground",
               "note": "다리 상판 X 486.1~493.1을 덮는 폭 안, 평면 Y 294.76 → 304.76에서 윗면 Z 0 → 3.0(다리 상판 높이). 화면 축 (168.74, 392.18) → (160.08, 397.18). 땅에서 시작해 상판 북쪽 끝과 높이 차 0"}
# 사용자 16:14: 길 전부(R1~R7·아피아 가도)는 지도에서 지웠다(Core 건축물만). 16:13의 '길을 기단 발치까지 잇기'는 길이 없어져 취소됐다.
# 사용자 16:41: 길 전부 삭제(16:14)의 예외로, 정보를 이끄는 길 하나(R_route)만 둔다 — 읽기 순서다(꾸미기 아님).
# 아피아 가도로 들어와(오른쪽 가장자리) → 메텔라 → 수도교·욕장 → 콜로세움·네로 거상 → 막센티우스 바실리카 → 트라야누스 시장 → 판테온 → 마르켈루스 극장 → 테베레강을 따라 바다로 → 포르투스 곁 출구.
# ±30° 등각 축(평면 X·Y 축 평행)만 쓴다. 건물 앞면(남·동 쪽 변)을 따라 지나가 건물이 길을 가리지 않는다. 중심선 → 건물 지면 평면 거리 4.4(화면 수직 3.8mm, 길 가장자리 간격 1.3mm).
ROUTE_W = 5.0
ROUTE_LAND = [(618.2, 133.2), (618.2, 184.8), (493.7, 184.8), (493.7, 12.0), (450.0, 12.0), (450.0, -28.7), (359.7, -28.7), (359.7, 29.1), (342.4, 29.1),
              (342.4, 125.3), (236.8, 125.3), (236.8, 156.0), (328.2, 156.0), (328.2, 256.7), (369.4, 256.7), (369.4, 304.8)]
def _route_river():
    f = RIVER_FILLET
    pts = [(369.4, 304.8), (369.4, RIVER_Y), (RIVER_XB - f, RIVER_Y)]
    for k in range(1, 8):                                    # 굽이(둥근 모서리, 평면 반지름 12)
        t = math.radians(90.0 * k / 8.0)
        pts.append((RIVER_XB - f + f * math.sin(t), RIVER_Y + f - f * math.cos(t)))
    pts += [(RIVER_XB, RIVER_Y + f), (RIVER_XB, COAST_Y), (RIVER_XB, COAST_Y + 15.0)]
    return [(round(x, 2), round(y, 2)) for x, y in pts]
ROUTE_RIVER = _route_river()
ROUTE_STOPS = ["카이킬리아 메텔라 무덤", "수도교", "카라칼라 욕장", "콜로세움", "막센티우스 바실리카", "트라야누스 시장", "판테온", "마르켈루스 극장",
               "하드리아누스 영묘·폰스 아일리우스(강)", "포르투스(출구)"]
ROADS = []
# 20:53 사용자: Core를 잇는 도로 = 구획 경계선(강보다 가볍다). X·Y축 직선, 꺾임 직각, 물을 건너는 곳은 다리, 모든 건물 대지 입구에 닿는다.
ROAD_W = 7.0                                                       # 도로 폭(화면 수직 mm = 평면 폭). 강 26·운하 12보다 가늘다
ROAD_NET = [
    {"id": "RA", "name": "북쪽 가로(메텔라 · 판테온 · 시장 사이)", "pts": [(173.0, 68.0), (530.0, 68.0), (530.0, 121.0)], "w": ROAD_W},
    {"id": "RB", "name": "판테온 서쪽 곁", "pts": [(210.0, 68.0), (210.0, 157.0)], "w": ROAD_W},
    {"id": "RM", "name": "메텔라 진입", "pts": [(173.0, 68.0), (173.0, 107.0)], "w": ROAD_W},
    {"id": "T1", "name": "서쪽 줄기(판테온 동쪽 · 극장 동쪽 · 바실리카)", "pts": [(315.0, 68.0), (315.0, 262.0), (380.0, 262.0)], "w": ROAD_W},
    {"id": "RD", "name": "콜로세움 북쪽 진입", "pts": [(415.0, 68.0), (415.0, 95.0)], "w": ROAD_W},
    {"id": "TB", "name": "남쪽 줄기(바실리카 동쪽 → 가로)", "pts": [(380.0, 232.0), (380.0, 290.0)], "w": ROAD_W},
    {"id": "RE", "name": "영묘 서쪽 진입", "pts": [(380.0, 232.0), (432.0, 232.0)], "w": ROAD_W},
    {"id": "RG", "name": "남쪽 가로(영묘 | 포르투스)", "pts": [(380.0, 290.0), (530.0, 290.0), (530.0, 185.0)], "w": ROAD_W},
    {"id": "RP", "name": "포르투스 진입", "pts": [(472.0, 290.0), (472.0, 301.0)], "w": ROAD_W},
]
                       # 17:22 재설계: 땅 위 길(R_route)을 지운다. 읽기 순서는 테베레 본류가 정한다


# 수도교 지면선 = 화면 ↘ 직선(평면 Y 상수): 카라칼라 욕장 오른쪽 변 (334, 160) → 오른쪽 변 밖(블리드)
AQUEDUCT_PLAN = [(335.0, -19.2), (448.4, -19.2)]               # 20:55 위계 5위: 화면 가로 150 · X축 직선, 테베레 대신 서쪽 경계 운하(X 350)를 건넌다
AQUEDUCT_H = 46.0

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



def _shift_plan_dict(d, dX, dY):
    """17:22 재설계: 평면 원본 dict의 좌표(X·Y 열쇠, 중심 c, 교각·계단·날개)를 (dX, dY)만큼 옮긴다(높이 z는 그대로)."""
    for k, v in list(d.items()):
        if isinstance(v, dict):
            _shift_plan_dict(v, dX, dY)
        elif k in ("X", "deck_X", "cutwater_X") and isinstance(v, list) and v and not isinstance(v[0], (list, dict)):
            d[k] = [round(x + dX, 2) for x in v]
        elif k in ("Y", "deck_Y", "diameter_Y", "wing_Y_minus", "wing_Y_plus") and isinstance(v, list) and v and not isinstance(v[0], (list, dict)):
            d[k] = [round(y + dY, 2) for y in v]
        elif k == "piers_Y":
            d[k] = [[round(y + dY, 2) for y in pr] for pr in v]
        elif k == "c" and isinstance(v, list) and len(v) == 2:
            d[k] = [round(v[0] + dX, 2), round(v[1] + dY, 2)]
        elif k == "diameter_X":
            d[k] = round(v + dX, 2)
        elif k == "rects_plan":
            d[k] = [[round(r[0] + dX, 2), round(r[1] + dX, 2), round(r[2] + dY, 2), round(r[3] + dY, 2)] for r in v]
        elif k == "treads":
            for t in v:
                t["Y"] = [round(y + dY, 2) for y in t["Y"]]
        elif k == "riser_faces":
            d[k] = [[round(f[0] + dY, 2), f[1], f[2]] for f in v]


# ── L7 막센티우스 바실리카(후보 자리 (가): 히어로 4층 조각 뒤, 시내 길 1과 카라칼라 욕장 사이)
BASILICA = {
    "paving": {"rects_plan": [[276.0, 338.0, 43.5, 62.0], [292.5, 335.5, 43.5, 87.0]], "h": 1.5,
               "note": "기단 포장 = 두 직사각형의 합(L자). 뒤-왼쪽 변(평면 X 276)이 시내 길 1 바깥 변(X 274.45)과 평면 1.55 = 화면 1.35mm(접속 ≤ 1.6). "
                       "신랑 쪽 앞 끝은 X 335.5까지(측랑 X 338보다 2.5 안쪽): 그림의 콜로세움 외벽 윗단 밝은 띠(사전 검사 모형보다 약 1.7mm 높다)와 2mm 이상 띄우려고 줄였다(338이면 0.56mm)"},
    "aisle": {"name": "북쪽 측랑", "X": [292.5, 338.0], "Y": [43.5, 55.5], "h": 16.0, "bays": 3, "bay_plan": round((338.0 - 292.5) / 3.0, 2),
              "vault": "8각형 코퍼를 새긴 콘크리트 배럴 볼트(볼트 축 = 평면 Y 방향, 칸마다 하나)", "open_face": "+Y(신랑 쪽, 화면 왼쪽 아래)",
              "note": "현존하는 북쪽 측랑 3칸. 칸 경계 평면 X 292.5·307.67·322.83·338.0, 두꺼운 칸막이 벽 위에 볼트가 얹힌다. 열린 면(평면 Y 55.5, z 0~16)에서 코퍼 반원통 안쪽이 보인다"},
    "nave_ruins": {"name": "신랑·남쪽 측랑 유적", "X": [292.5, 335.5], "Y": [55.5, 87.0], "h_max": 4.0,
                   "place_rule": "기둥 밑동·낮은 벽은 평면 Y ≥ 60.0에만 둔다(높이 4 이하라 측랑 열린 면 아래 끝을 가리지 않는다)",
                   "note": "낮은 기둥 밑동·벽 자국·포장 결. 남쪽 측랑 칸 벽 자국 3칸"},
    "nave_vault_dashed": {"name": "무너진 신랑 교차 볼트(점선 복원)", "bays": 3, "line_mm": 0.25, "h_max": 10.0, "dash_mm": [1.2, 0.8],
                          "profile": "칸 경계 평면 X 292.5·306.83·321.17·335.5의 가로 아치 z(Y) = 9.0·sin(π·(Y − 56.5)/30.5)(Y 56.5~87.0) + 꼭대기 마루선(Y 71.75, z 9.0) + 칸마다 대각 리브",
                          "rule": "윤곽의 모든 점 (X, Y, z)가 (Y − 55.5) ≥ z를 지킨다 → 화면에서 측랑 열린 면(Y 55.5, z 0~16) 아래 끝보다 아래라 열린 면과 겹치지 않는다(가로 아치–열린 면 최소 0.87mm)",
                          "label": "점선 = 무너진 신랑 볼트 복원(P2 ② 캡션과 같은 말)"},
}
_shift_plan_dict(BASILICA, 34.2, 226.5)
_B = BASILICA
_pav = [(X + 34.2, Y + 226.5) for X, Y in [(276.0, 43.5), (338.0, 43.5), (338.0, 62.0), (335.5, 62.0), (335.5, 87.0), (292.5, 87.0), (292.5, 62.0), (276.0, 62.0)]]
_L7_ground = [to_screen(X, Y) for X, Y in _pav]
_L7_aisle = _cvx_hull(_prism_pts(292.5 + 34.2, 338.0 + 34.2, 43.5 + 226.5, 55.5 + 226.5, 0.0, 16.0))
_L7_nave = _cvx_hull(_prism_pts(292.5 + 34.2, 335.5 + 34.2, 55.5 + 226.5, 87.0 + 226.5, 0.0, 4.0))
_L7_all = [to_screen(X, Y, z) for X, Y in _pav for z in (0.0, 1.5)] + _L7_aisle + _L7_nave
L7_POLY = _cvx_hull(_L7_all)
L7_BOX = _bbox(L7_POLY)

# ── L8 하드리아누스 영묘 + 폰스 아일리우스(후보 자리 (나): 테베레 굽이 안쪽 오른쪽 둑)
MAUSOLEUM = {
    "base": {"name": "사각 기단", "X": [467.1, 512.1], "Y": [325.9, 370.9], "h": 5.0,
             "note": "45×45 정사각 기단(평면). 뒤-오른쪽 변(평면 Y 325.9)이 테베레 남쪽 둑(Y 323.24)과 평면 2.66 = 화면 2.30mm(접속 ≤ 2.5)"},
    "drum": {"name": "원통", "c": [489.6, 348.4], "r": 16.0, "z": [5.0, 23.0], "skin": "겉 = 대리석", "core": "속 = 콘크리트 원통",
             "note": "기단 가운데의 큰 원통. 절개하지 않는다(겉 대리석 면 + 위쪽 테두리 띠에 콘크리트 속을 보이는 작은 이음 자국)"},
    "top": {"name": "정상(낮은 둔덕·난간)", "parapet": {"r": 16.0, "z": [23.0, 25.5]}, "mound": {"r_max": 10.0, "z_top": 28.0},
            "omit": "정상 조각(황제상·사두마차)과 교황 증축(산탄젤로성) 형태는 그리지 않는다",
            "note": "테두리 난간은 낮게(z 25.5까지) 둔다: 원통 꼭대기 테두리가 강 건너 하역장 부두 앞 변(d3 그림)과 화면 2.2mm 떨어진다(기획대로 테두리를 z 28까지 올리면 부두 앞 변과 0.23mm 겹친다). 안쪽 흙 둔덕은 꼭대기 z 28(테두리 안쪽이라 실루엣 밖으로 나가지 않는다), 나무 없음"},
    "bridge": {"name": "폰스 아일리우스", "deck_X": [486.1, 493.1], "deck_Y": [291.9, 325.9], "h": 3.0, "arches": 3,
               "piers_Y": [[300.18, 302.18], [312.95, 314.95]], "cutwater_X": [485.1, 494.1], "bridge": True,
               "note": "상판이 ↘ 팔(평면 Y 304.76~323.24)을 건너 북쪽 둑 끝에서 새 길 R7과 만난다(R7 띠 X 484.98~494.22 안). 아치 3개·교각 2개(물가름 앞뒤 1mm). 강 위 예외(bridge: 땅·강 검사에서 뺀다)"},
    "steps": {"name": "기단 북쪽 디딤 2단(폰스 아일리우스 → 기단 윗면)", "X": [486.1, 493.1], "Y": [325.9, 329.9], "owner": "coast",
              "treads": [{"Y": [325.9, 327.9], "z": 3.67}, {"Y": [327.9, 329.9], "z": 4.33}],
              "bottom_z": 3.0, "top_z": 5.0, "risers": [0.67, 0.66, 0.67],
              "riser_faces": [[325.9, 3.0, 3.67], [327.9, 3.67, 4.33], [329.9, 4.33, 5.0]],
              "tread_mm": 2.0, "riser_mm": 0.67,
              "note": "기단(높이 5.0) 북쪽 변 안쪽 평면 Y 325.9~329.9, 폭 = 다리 상판 X 486.1~493.1에 판다. 디딤 윗면 Z 3.67·4.33, 챌면 3개 각 0.67(상판 3.0 → 3.67 → 4.33 → 기단 윗면 5.0). "
                      "다리 상판 남쪽 끝(Y 325.9, Z 3.0)과 첫 챌면 아래 끝이 같은 높이라 양 끝 보행면 높이 차 0"},
    "shift_from_plan": "기획 좌표(기단 X 466~510 × Y 325.5~369.5, 원통 (488,347.5), 테두리 z 28, 다리·R7 X 488)에서 바꾼 것: 원통·기단 중심 평면 +X 1.0·+Y 0.3, 기단 44 → 45, 테두리 z 28 → 25.5. 통합 d4: 기단·원통·다리·R7을 평면 (+0.6, +0.6) 더 옮겼다(화면 아래로 0.6mm, 그린 원통 뒤-오른쪽 테–하역장 부두 면 1.68 → 2mm 이상, 육각 내항 간격은 그대로). "
                       "이유: 기획값 그대로면 원통 왼쪽 실루엣–포르투스 육각 내항 창고 지붕 1.46mm, 원통 꼭대기–하역장 부두 앞 변 −0.23mm(겹침). 바꾼 뒤 2.07·2.2mm이고 투영 면적은 ±3% 안",
}
_shift_plan_dict(MAUSOLEUM, -27.6, -94.9)
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
# 높이 접속(D7): R7 진입 경사 윗면(ground)과 기단 북쪽 디딤 2단 윗면·챌면(coast)의 화면 다각형
_rp = BRIDGE_RAMP
_L8_RAMP = [to_screen(_rp["X"][0], _rp["Y"][0], _rp["z"][0]), to_screen(_rp["X"][1], _rp["Y"][0], _rp["z"][0]),
            to_screen(_rp["X"][1], _rp["Y"][1], _rp["z"][1]), to_screen(_rp["X"][0], _rp["Y"][1], _rp["z"][1])]
_ms = _M["steps"]
_L8_TREADS = [[to_screen(_ms["X"][0], t["Y"][0], t["z"]), to_screen(_ms["X"][1], t["Y"][0], t["z"]),
               to_screen(_ms["X"][1], t["Y"][1], t["z"]), to_screen(_ms["X"][0], t["Y"][1], t["z"])] for t in _ms["treads"]]
_L8_RISERS = [[to_screen(_ms["X"][0], Yr, z0), to_screen(_ms["X"][1], Yr, z0), to_screen(_ms["X"][1], Yr, z1), to_screen(_ms["X"][0], Yr, z1)]
              for Yr, z0, z1 in _ms["riser_faces"]]
L8_BOX = _bbox(L8_POLY + _L8_bridge)                                                            # 투영 상자 = 건물 + 다리

# ── L9 마르켈루스 극장(후보 자리 (라): 판테온과 강 사이 테베레 둑)
THEATRE = {
    "plan": {"diameter_X": 379.26, "diameter_Y": [217.76, 293.76], "c": [379.26, 255.76], "r": 38.0, "curve": "+X(화면 오른쪽 아래)",
             "note": "반원 평면. 지름(무대 쪽)은 평면 X 340, 곡면(바깥 아케이드)은 +X 쪽 X 378까지"},
    "arcade": {"tiers": 2, "h": 12.0, "tier_h": [6.0, 6.0], "third_tier": "그리지 않는다(그린다면 점선 + '추정')",
               "note": "바깥 곡면 아케이드 2단(아래 도리스·위 이오니아 기둥 붙임). 관람석은 곡면에서 지름 쪽으로 내려간다"},
    # 16:41 Blender 요청: 반원 지름 양 끝 옆날개(직사각 블록). 날개 자리를 비우려고 극장을 평면 Y −9 옮겼다(+Y 날개 끝이 테베레 북쪽 둑 평면 Y ≈ 304.8에서 3mm 떨어진다)
    "side_wings": {"wing_Y_minus": [209.76, 217.76], "wing_Y_plus": [293.76, 301.76], "X": [375.26, 379.26], "h": 8.0,
                   "note": "지름(평면 X 379.26)에서 −X 쪽으로 4, 지름 끝에서 바깥(±Y)으로 8. 그리지 않고 Blender가 만든다"},
    "stage_wall": {"h_max": 4.0, "note": "무대 쪽(지름 쪽) 벽은 낮은 유적으로 두어 관람석 층이 보이게 한다"},
}
_shift_plan_dict(THEATRE, -102.5, -22.8)
_T = THEATRE["plan"]
_arc = [(_T["c"][0] + _T["r"] * math.cos(math.radians(a)), _T["c"][1] + _T["r"] * math.sin(math.radians(a))) for a in [-90.0 + 180.0 * i / 60 for i in range(61)]]
_L9_ground = [to_screen(X, Y) for X, Y in _arc]
L9_POLY = _cvx_hull([to_screen(X, Y, z) for X, Y in _arc for z in (0.0, THEATRE["arcade"]["h"])]
                    + [to_screen(_T["diameter_X"], Y, THEATRE["stage_wall"]["h_max"]) for Y in _T["diameter_Y"]])
L9_BOX_POLY = _bbox(L9_POLY)                     # 평면 원본 외곽 상자 [32.3, 271.4, 111.7, 329.3]
L9_BOX = [9.47, 120.88, 90.67, 178.78]              # d5(D4): 렌더 실측 상자(무대 쪽 낮은 유적이 왼쪽으로 1.8mm 더 나온다)로 정정


# ═════════════ Core 랜드마크(투영 상자 = 레이어 알파 외곽 상자 목표) ═════════════
LANDMARKS = [
    {"id": "L1", "name": "판테온", "latin": "Pantheon", "box": [67.5, 135.5, 162.5, 224.5], "zone": "시내(왼쪽 가운데, 강 위쪽 — 실제로 테베레 굽이 안쪽 캄푸스 마르티우스)",
     "geo": (41.8986, 12.4769), "real": "콜로세움에서 1.6 km 북서(306°)",
     "form": "주랑 현관 + 원통 + 돔(오큘러스). 절개하지 않는다(욕장만 절개). 앞마당은 건물의 일부",
     "story": "2,000년째 서 있는 철근 없는 콘크리트 돔", "number": "돔 지름 43.3 m",
     "links": "없음(길은 지도에서 지웠다)"},
    {"id": "L2", "name": "트라야누스 시장", "latin": "Mercati di Traiano", "box": [277.5, 282.0, 380.5, 372.0], "zone": "시내(뒤쪽 왼쪽, L 패널 바로 아래)",
     "geo": (41.8958, 12.4861), "real": "콜로세움에서 0.8 km 북서(321°)",
     "form": "반원형 벽돌 정면(층층 상점) + 대회랑 교차 볼트(지붕 한 칸을 걷어 볼트를 보인다)",
     "story": "판 모양 결정이 갈라짐을 막았다(2014년 연구)", "number": "대회랑 중앙 볼트 경간 8.6 m",
     "links": "시내 길 2(오른쪽 아래 지면에서 시작)"},
    {"id": "L3", "name": "카라칼라 욕장(절개)", "latin": "Thermae Antoninianae", "box": [180.0, 96.0, 250.0, 156.0], "zone": "시내(뒤쪽 가운데-오른쪽) — 사용자 결정 '뒤쪽'",
     "geo": (41.8791, 12.4924), "real": "콜로세움에서 1.2 km 남(179°)",
     "form": "욕장 참조 이미지(열주·벽감 조각상·돔 열탕실·증기 욕조·목욕객)를 절개 단면으로: 칼다리움 드럼 벽(겉 벽돌·속 콘크리트·돔 위쪽 경석 층), 하이포코스트·화로 일꾼, 냉탕실 열주와 교차 볼트 한 칸(화면과 나란한 면으로 절개). 빛은 큰 창 중심, 오큘러스·코퍼는 복원 추정",
     "story": "겉은 벽돌, 속은 콘크리트. 돔 위쪽엔 가벼운 경석", "number": "열탕실 돔 경간 약 36 m",
     "links": "시내 길 1·욕장 진입로 R5(지면 뒤-왼쪽 변), 수도교 아치 열(오른쪽 변: 아쿠아 마르키아에서 갈라진 아쿠아 안토니니아나가 저수조 64개에 물을 댐[S47][S49])"},
    {"id": "L4", "name": "수도교 아치 열(아쿠아 안토니니아나)", "latin": "Aqua Antoniniana(아쿠아 마르키아 지선)", "box": [351.52, 142.60, 420.0, 206.14], "zone": "남동 교외(오른쪽 위, 오른쪽 변 블리드)",
     "geo": None, "real": "아쿠아 마르키아에서 갈라진 지선, 212–213년 비문[S47][S49]. 경로 좌표는 조사 보고서에 없어 지리 검사에서 뺀다",
     "form": "실제 경로가 아니라 욕장 급수 관계 모식(아쿠아 마르키아 → 아쿠아 안토니니아나 → 욕장 저수조 64개). 오른쪽 변 밖(남동 시골)에서 ↖로 들어와 카라칼라 욕장 오른쪽 변 (336, 160)에 닿는 아치 열, 높이 26mm(2단 아치), 교각 약 8mm 간격. 아치는 관통 아치로 그린다: 아래층 개구 폭 5.3mm·위층 3.9mm, 아치 안쪽 면 1.5mm가 보이고 개구부 뒤로 지면(밭·구릉)이 보인다(막힌 벽면에 아치 무늬만 그리지 않는다). 맨 위 수로에 물빛 선. 벽돌면 보수 구간 덧댐은 그리지 않는다(이 수도의 근거가 없다)",
     "story": "수로 안은 방수 모르타르", "number": "욕장 저수조 64개에 물을 댐",
     "links": "카라칼라 욕장(왼쪽 끝, 욕장 오른쪽 변 (336, 160))"},
    {"id": "L5", "name": "카이킬리아 메텔라 무덤", "latin": "Mausoleo di Cecilia Metella", "box": [8.0, 100.5, 76.0, 168.5], "zone": "남동 교외(오른쪽 가운데), 아피아 가도 남쪽 길가",
     "geo": (41.8518, 12.5205), "real": "콜로세움에서 4.9 km 남남동(151°), 아피아 가도",
     "form": "네모 기단 위 원통 드럼(16면 이상), 트래버틴 마름돌 겉면(일부 뜯겨 콘크리트 속이 보임), 꼭대기 아래 소머리·꽃줄 부조 띠, 중세 흉벽 증축은 그리지 않음. 둘레 사이프러스·소나무(진입로 R6a·R6b 띠 밖 2mm 이상)",
     "draw_scale": 1.0, "draw_scale_center": [375.31, 359.0], "draw_clip_x": None,
     "draw_box_d4": [354.0, 290.6, 420.0, 355.4], "draw_box_expected": [352.68, 289.3, 420.0, 356.7],
     "draw_rule": "d5(D4): 설계 2D 그림을 spec 상자 중심 (387.0, 323.0) 기준 1.04배로 키우고 x 420에서 자른다. d4 실측 [354.0, 290.6, 420.0, 355.4] = 66×64.8 = 4,276.8mm² → [352.68, 289.3, 420.0, 356.7] = 67.32×67.4 = 4,537mm²(≥ 4,530). Blender suburb는 fit_to_box로 spec 상자 [354, 288, 420, 358]을 채운다",
     "draw_gaps_expected_mm": {"대지–라벨 글 블록": 4.61, "대지–C4 상자": 46.0, "드럼 왼쪽 실루엣–지도 D 표지(d4 자리 (367.27, 314.66))": 0.68,
                               "rule": "D 표지는 2mm 이상 떨어져야 한다 → panels가 map_pt를 x 365.9 이하로 옮긴다(C4 지시선 시작 (370.5, 316.0)은 키운 드럼 면 안 1.4mm 그대로)"},
     "story": "BCE 30–10년의 원통 무덤", "number": "드럼 지름 29 m",
     "links": "아피아 가도 → 메텔라 진입로 R6a·R6b(무덤 대지 뒤-오른쪽 변)"},
    {"id": "L6", "name": "포르투스 항", "latin": "Portus Traiani · Portus Claudii", "box": [5.0, 382.0, 155.0, 474.0], "draw_scale": 1.41, "draw_pivot": [round(v, 2) for v in to_screen(496.16 - 23.76, 380.0)], "box_source": "d5: 렌더 실측 아래 변 434.8로 정정(d4 434.0)", "zone": "서남서 해안(왼쪽 아래), 강 오른쪽 둑과 해안 사이",
     "geo": (41.7781, 12.2593), "real": "콜로세움에서 23.0 km 서남서(237°)",
     "form": "판화를 바다가 왼쪽 아래로 오게 돌림: 트라야누스 육각 내항(육지, 평면 중심 (437.0, 353.6), 반지름 24, 붉은 기와 창고 고리, 수면 반지름 15.2) · 클라우디우스 외항(바다, 평면 중심 (437.0, 401.6), 휘어 감싼 방파제 두 팔: 평면 반지름 18.4~21.0, 팔 A 263°→123°, 팔 B 277°→57°, 끝각에서 정확히 자름 → 입구 화면 폭 약 19.8mm, 창고·열주) · 등대(입구 인공섬: 평면 90°·반지름 24, 4층 탑 + 등롱) · 운하 2개(강 ↔ 육각 내항 ↔ 외항, 화면 폭 2.6mm) · 두 항구 수면의 작은 범선. 판화의 황제 거상은 넣더라도 라벨에서 사실로 쓰지 않는다",
     "story": "트라야누스 육각 내항은 육지, 클라우디우스 외항·등대는 바다. 바닷물은 항구 구조물에만", "number": "육각 내항 약 32 ha(약 100–112년), 외항 42년 착공",
     "links": "테베레 오른쪽 둑(강 쪽 운하로 육각 내항과 이음), 해안선(외항 쪽 운하로 외항과 이음)"},
    # ── d4 추가(기준선 7.2절): 모두 표준 랜드마크 등급(투영 면적 ≥ 4,500mm², 콜로세움보다 작게). 형태·이야기 글에 높이·지름·치수 수치를 쓰지 않는다
    {"id": "L7", "name": "막센티우스 바실리카", "latin": "Basilica Maxentii · Basilica Nova", "box": L7_BOX,
     "zone": "시내(뒤쪽 가운데: 콜로세움 4층 조각 뒤, 시내 길 1과 카라칼라 욕장 사이) — 후보 자리 (가)",
     "geo": (41.8917, 12.4886), "real": "콜로세움에서 0.3 km 서북서(299°), 포룸 로마눔 동쪽 끝",
     "form": "현존하는 북쪽 측랑 3칸의 거대한 콘크리트 배럴 볼트(8각형 코퍼, 열린 면은 신랑 쪽 = 화면 왼쪽 아래)가 주인공. 신랑·남쪽 측랑 자리는 낮은 기둥 밑동·벽 자국 유적, "
             "무너진 신랑 교차 볼트 3칸은 가는 점선 복원 윤곽(측랑보다 낮게, 측랑 열린 면과 화면에서 겹치지 않게). 판테온의 돔 코퍼와는 '배럴 볼트'로 구분한다. 기단 포장이 시내 길 1에 닿는다",
     "story": "북쪽 측랑의 콘크리트 배럴 볼트 3칸이 지금도 서 있다", "number": None,
     "links": "시내 길 1(R2): 기단 포장 뒤-왼쪽 변이 길 바깥 변에 닿는다(실제 지면 간격 ≤ 1.6mm)",
     "plan": BASILICA, "draw_scale": 0.78, "draw_pivot": [round(sum(p[0] for p in _L7_ground) / len(_L7_ground), 2), round(sum(p[1] for p in _L7_ground) / len(_L7_ground), 2)], "poly_screen": _r2(L7_POLY), "ground_screen": _r2(_L7_ground),
     "parts_screen": {"바실리카 지면": _r2(_L7_ground), "바실리카 측랑 볼트": _r2(_L7_aisle), "바실리카 신랑 유적": _r2(_L7_nave)},
     "gaps_expected_mm": {"기단 포장–시내 길 1(R2) 지면": 1.35, "실루엣–콜로세움 사전 검사 모형": 2.28, "실루엣–콜로세움 외벽(d3 그림 윗단 띠)": 2.3,
                          "실루엣–카라칼라 욕장 지면(d3 그림)": 2.45, "실루엣–네로 거상": 4.76},
     "draw": "평면 원본(plan)을 전역 등각 그대로 그린다(fit_frame 배율·높이 과장 없음). 투영 상자는 poly_screen의 외곽 상자"},
    {"id": "L8", "name": "하드리아누스 영묘·폰스 아일리우스", "latin": "Mausoleum Hadriani · Pons Aelius", "box": L8_BOX,
     "zone": "테베레 굽이 안쪽 오른쪽 둑(↘ 팔 남쪽, 포르투스 육각 내항과 강 사이) — 후보 자리 (나)",
     "geo": (41.9031, 12.4663), "real": "콜로세움에서 2.6 km 북서(304°), 테베레 서안",
     "form": "사각 기단 + 큰 원통(겉은 대리석, 속은 콘크리트 원통) + 정상의 낮은 흙 둔덕과 테두리 난간 + 테베레를 건너는 다리(아치 3개). "
             "정상 조각(복원 추정)과 교황 증축(지금의 산탄젤로성) 형태는 그리지 않는다. 카이킬리아 메텔라 무덤과는 사각 기단과 다리로 구분한다. 다리 북쪽 끝은 진입 경사(Z 0 → 3.0)로 땅에 잇고, 기단 쪽은 북쪽 디딤 2단으로 기단 윗면에 오른다",
     "story": "겉은 대리석, 속은 콘크리트 원통", "number": None,
     "links": "테베레 남쪽 둑(기단 뒤-오른쪽 변, 실제 지면 간격 ≤ 2.5mm) + 폰스 아일리우스(강 위) + R7(다리 북쪽 끝)",
     "plan": MAUSOLEUM, "draw_scale": 1.04, "draw_pivot": [round(v, 2) for v in to_screen((MAUSOLEUM["base"]["X"][0] + MAUSOLEUM["base"]["X"][1]) / 2.0, (MAUSOLEUM["base"]["Y"][0] + MAUSOLEUM["base"]["Y"][1]) / 2.0)], "poly_screen": _r2(L8_POLY), "ground_screen": _r2(_L8_ground),
     "bridge_screen": _r2(_L8_bridge), "bridge": True,
     "parts_screen": {"영묘 기단": _r2(_L8_base), "영묘 원통": _r2(_L8_drum), "폰스 아일리우스 다리": _r2(_L8_bridge),
                      "R7 진입 경사 윗면(ground)": _r2(_L8_RAMP), "기단 북쪽 디딤 1단 윗면(coast)": _r2(_L8_TREADS[0]), "기단 북쪽 디딤 2단 윗면(coast)": _r2(_L8_TREADS[1]),
                      "기단 북쪽 챌면 3개(coast)": [_r2(q) for q in _L8_RISERS]},
     "walk_levels": {"R7 길 윗면": 0.3, "R7 진입 경사": [0.0, 3.0], "다리 상판": 3.0, "디딤 1단": 3.67, "디딤 2단": 4.33, "기단 윗면": 5.0,
                     "rule": "길 → 경사 → 상판 → 디딤 → 기단 윗면이 이어져 양 끝 보행면 높이 차 0(D7)"},
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
     "plan": THEATRE, "draw_scale": 0.88, "draw_pivot": [round(v, 2) for v in to_screen(THEATRE["plan"]["c"][0], THEATRE["plan"]["c"][1])], "poly_screen": _r2(L9_POLY), "ground_screen": _r2(_L9_ground),
     "parts_screen": {"극장 반원 아케이드": _r2(L9_POLY)}, "box_poly": L9_BOX_POLY,
     "box_source": "d5: 렌더 실측(81.2×57.9 = 4,701.5mm²)으로 정정. poly_screen(겹침용)은 평면 원본 그대로",
     "gaps_expected_mm": {"지름 쪽 +Y 끝–테베레 북쪽 둑": 1.73, "실루엣–판테온 앞마당(d3 그림)": 6.84},
     "draw": "평면 원본(plan)을 전역 등각 그대로 그린다"},
]
# 사용자 16:14: 베수비오·알바노 구릉·먼 들은 지도에서 지웠다(Core 건축물만)
BACKGROUND = []

# ═════════════ Core 지도 소품(탈것·시설·지형) ═════════════
# 사용자 16:14: 하역장·석회 가마·수레·바지선·화산재 운반선·오스티아·빌라·공사장·농장은 지도에서 지웠다. Core 소품은 네로 거상 받침만 남는다.
PROPS = [
    # d4 추가(기준선 7.3절): 콜로세움 곁 작은 소품. 받침과 거상의 재료를 구분한다
    {"name": "네로 청동 거상과 콘크리트(벽돌 마감) 받침", "box": None, "zone": "콜로세움 뒤-왼쪽과 막센티우스 바실리카 사이(베누스·로마 신전 쪽) 지면", "on": "땅",
     "plan": [500.0, 45.0],   # 16:41 길 남서쪽으로 옮김(길과 라벨이 겹치지 않게)
     "pedestal": {"name": "네로 거상 받침", "plan_size": [8.0, 8.0], "h": 5.0, "finish": "벽돌 마감 콘크리트(원래 대리석으로 덮임), 윗단에 가는 대리석 띠"},
     "statue": {"name": "네로 거상", "plan_size": [2.4, 2.4], "z": [5.0, 20.0], "material": "청동(복원 추정)", "head_screen": None},
     "note": "받침 = 벽돌 마감 콘크리트(원래 대리석), 거상 = 청동 복원 추정, 치수 인쇄 금지. 라벨 문장은 '콘크리트(벽돌 마감) 받침 위의 / 네로의 청동 거상(추정)' 꼴만 쓴다"
             "('콘크리트로 만든 조각'·'콘크리트로 빚은 거상' 금지, '콜로세움' 이름 유래는 이번 회차에 인쇄하지 않는다). "
             "기획 중심 (328.8,115.2)에서 평면 (−1.5,−1.5) = 화면 위로 1.5mm 옮겼다: 그림의 콜로세움 외벽 윗단 띠와 0.81 → 2.11mm(사전 검사 모형과는 3.8mm). 통합 d4: 그린 받침–외벽이 1.98mm라 평면 (−0.3,−0.3) 더 옮겼다(화면 위로 0.3mm). 머리 (185,201)는 그대로 거상 윗면 안이다"},
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
# d5(D6): 자리는 d4 그대로. hero LAYOUT의 'nero' (−40.7, 44.7) = 화면 (176, 320)은 폐기한다(LocalBanana 조경 구성을 바꾸지 않고, 바실리카 쪽 뒤-왼쪽 지리를 지킨다)
NERO_YARD = {"name": "네로 거상 마당(작은 포장 마당)", "screen_box": [381.0, 256.0, 407.0, 288.0],
             "plan_poly": [[round(v, 2) for v in to_plan(x, y)] for x, y in ((143.7, 261.5), (169.7, 261.5), (169.7, 293.5), (143.7, 293.5))],
             "z_top": 0.12, "owner": "hero(짓는다) · ground(집·나무를 비운다)",
             "rule": "상자 안에 집·나무 0. 포장 판석(판석 길과 같은 PAL 'slab'), 받침 둘레 사람 2~3(키 4.9)",
             "discarded": "hero LAYOUT 'nero' (−40.7, 44.7) = 화면 (176, 320)"}
_nero["yard"] = NERO_YARD
# 사용자 16:14: 알바노 구릉 띠·남동 교외 밭·시내 지붕 블록은 지도에서 지웠다(땅 판 바탕만 남는다)
TERRAIN = []

# ═════════════ 포르투스(원본은 이 사양, 그림은 render) ═════════════
# 상자는 위계 실측 목표, 다각형은 형태 골격(겹침·땅/바다 검사용)
PORTUS_DX = -23.76                    # 20:55 위계 2위·중앙 집중: 해안선(Y 380)을 따라 −X로 옮기고 그림 전체를 1.56배(SIso, 중심 = 해안선 위 육각 축)
PORTUS_HEX_C = (496.16 + PORTUS_DX, 353.64)        # 평면: 강 오른쪽 둑(Y 323.24)과 해안(Y 380) 사이 띠 가운데
PORTUS_HEX_R = 24.0                  # 창고 고리 포함 평면 반지름
PORTUS_HEX_WATER_R = 15.2            # 육각 내항 수면 반지름
PORTUS_BASIN_C = (496.16 + PORTUS_DX, 401.64)      # 클라우디우스 외항(바다)
PORTUS_BASIN_R = 21.0                # 방파제 포함

# 운하 2개(평면 X 435.5~438.5 = 화면 수직 폭 2.6mm). 육각 내항 수면 안쪽과 외항 수면 안쪽까지 잇고, 포장·안벽에 폭 3mm 개구부를 낸다
PORTUS_CANALS = [
    {"name": "강 쪽 운하", "plan_x": [494.66 + PORTUS_DX, 497.66 + PORTUS_DX], "plan_y": [322.24, 340.10],
     "note": "테베레 오른쪽 둑(강 수면 1.0 안) → 육각 내항 수면(270° 꼭짓점 안쪽 1.5). 육각 포장·성벽·창고 고리에 폭 3mm 개구부. d4: d3 그림의 끝점을 채택했다(render의 추가 연장 0)"},
    {"name": "외항 쪽 운하", "plan_x": [494.66 + PORTUS_DX, 497.66 + PORTUS_DX], "plan_y": [367.10, 384.60],
     "note": "육각 내항 수면(90° 꼭짓점 안쪽 1.5) → 해안선(Y 380)을 지나 외항 수면 안쪽(방파제 두 팔 사이 263°~277° 빈 곳을 지난다). d4: d3 그림의 끝점을 채택했다(render의 추가 연장 0)"},
]
# 외항 방파제 두 팔(평면 각도는 외항 중심 기준, 0° = +X). 마지막 조각은 끝각에서 정확히 자른다
PORTUS_EAST_CANAL = {"name": "강 쪽 운하(동쪽)", "plan_x": [517.0 + PORTUS_DX, 527.0 + PORTUS_DX], "plan_y": [352.0, 355.0],
                     "note": "19:3x 새 강 기준: 육각 동쪽 변 → 강 서쪽 둑. (옛 북쪽 강 쪽 운하는 새 강에서 떨어져 의미 없음)"}
PORTUS_MOLES = {"r_out": 21.0, "r_in": 18.4, "arm_a_deg": [263.0, 123.0], "arm_b_deg": [277.0, 417.0], "cut_exact": True, "colonnade_deg": [12.0, 54.0],
                "note": "팔 A는 263°에서 123°까지(바다 쪽, 창고는 150~210°), 팔 B는 277°에서 417°(=57°)까지. 열주는 팔 B의 12~54°에만. 263°~277° 빈 곳은 외항 쪽 운하, 57°~123° 입구는 등대섬"}
# 등대섬(입구 인공섬). 탑 치수는 d2 그림 그대로(평면 반폭·높이 mm)
PORTUS_LIGHTHOUSE = {"plan_angle_deg": 78.0, "plan_r": 22.0, "screen_base": [67.18, 461.95],
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
# 사용자 16:14: 심은 지면(밭·포도밭·올리브 숲·사이프러스 열·지붕 블록)은 지도에서 지웠다
PLANTED = []


# ═════════════ 실제 좌표(조사 보고서 4.2절, 근사) ═════════════
GEO_COLOSSEUM = (41.8902, 12.4922)
GEO_EXTRA = [
    {"name": "테베레 하구(오스티아 쪽, 근사)", "geo": (41.7400, 12.2390), "screen": RIVER_MOUTH_SCREEN, "note": "[근사] 고대 하구 위치는 지금과 다르다"},
    {"name": "알바노 구릉(몬테 카보)", "geo": (41.7510, 12.7090), "screen": (338.0, 146.0), "note": "d4: 구릉 띠 [318,122,420,162] 안, 베수비오·농장 왼쪽"},
    {"name": "오스티아 안티카(근사)", "geo": (41.7556, 12.2917), "screen": (226.0, 474.0), "note": "[근사] d4: 오스티아 소품 상자 중심"},
]
# 추가 랜드마크 L7~L9의 geo·real은 LANDMARKS에 있다(지리 검사가 LANDMARKS를 돈다). 배치는 구역 서사 우선이고 방위 오차는 기록만 한다
GEO_NOTE = "L7~L9는 구역 서사(시내 뒤쪽·테베레 굽이·판테온과 강 사이)를 먼저 따르고, 실제 방위·거리 오차는 v2_check geo 표에 기록만 한다"


# ═════════════ d5 히어로 사양(core_map.hero 원본). global이 이 사전을 그대로 core_map.hero로 쓴다 ═════════════
def _sil_coarse(dx=1.0):
    pts = colo_silhouette(dx=dx)
    return [[round(x, 2), round(y, 2)] for x, y in pts]


HERO_COLOSSEUM = {
    "source": "기준선 8.1(LocalBanana 첨부 이미지와 같은 본체: 방향·부서진 정도·보이는 면·비례) + 공통 결정 D2. Blender roma_colo·roma_colo_in과 같은 값",
    "draw_scale": HERO_SCALE, "center_plan": list(COLO_C_PLAN), "center_screen": [round(v, 2) for v in to_screen(*COLO_C_PLAN)],
    "offset_from_landscape_plan": [-15.8, -11.8],
    "semi_axes_plan": list(COLO_AXES), "major_axis_az_deg": COLO_MAJOR_AZ, "major_axis_screen": "가로",
    "az_rule": "θ = atan2(평면 dY, 평면 dX)(roma_kit.plan_az): 0° 화면 오른쪽 아래, 45° 정면 아래, 135° 왼쪽, 225° 위, 315° 오른쪽",
    "arches": 40, "arches_note": "시각 비례(실제 80칸)", "storey_tops_z": COLO_STOREY_Z, "tier_lines_z": COLO_STOREY_Z,
    "side_mm": 0.0, "octagon": False, "front_cut": False,
    "wall_profile": [[w["t0"], w["t1"], (w.get("h_range") or [w["h"], w["h"]])[0], (w.get("h_range") or [w["h"], w["h"]])[1], w["part"]] for w in COLO_WALLS],
    "front_az": [18, 72], "front_h_max": 17.0,
    "outer_wall_h": COLO_WALLS,
    "outer_wall_rule": "wall_profile = [t0, t1, 낮은 높이, 높은 높이, 메모]. 0°를 지나는 구간은 t1 < t0(338 → 18). 4층 외벽 조각은 뒤-왼쪽(100~205°), 앞쪽 끝 100~112°는 경사 부벽(41·46·50), 뒤쪽 끝 205~209°는 수직 끊김(44). "
                       "경기장 앞 정면 18~72°는 1층 + 부서진 2층 토막(14.0~17.0, 상한 17.0): 진짜 등각에서 높이 h 벽 뒤 1.414·h가 가려지므로 이렇게 낮춰야 경기장이 보인다",
    "second_ring": COLO_SECOND_RING,
    "wall_t": COLO_SHELL["outer_wall_t"], "outer_corridor_w": COLO_SHELL["outer_corridor_w"], "second_ring_t": COLO_SHELL["second_ring_t"],
    "cavea": HERO_INTERIOR["cavea"], "podium_wall": HERO_INTERIOR["podium_wall"],
    "arena_semi_axes_plan": list(COLO_ARENA_AXES), "u_split": COLO_U_SPLIT,
    "wood_floor": HERO_INTERIOR["wood_floor"], "hypogeum": HERO_INTERIOR["hypogeum"],
    "wood_floor_z": HERO_INTERIOR["wood_floor"]["z"], "hypogeum_floor_z": HERO_INTERIOR["hypogeum"]["floor_z"],
    "screen_box": HERO_BOXES["building"], "building_screen_box": HERO_BOXES["building"], "screen_wh": HERO_BOXES["building_wh"],
    "silhouette_screen": _sil_coarse(), "silhouette_area_mm2": HERO_BOXES["building_silhouette_area_mm2"],
    "base_ellipse_screen": _r2(COLO_BASE_SCREEN),
    "width_ratio_to_rep": HERO_BOXES["width_ratio_building_over_rep"],
    "discarded": "d4 ring_ratio 0.74, 벽 60/28/12, 원형 고리, 가로벽 격자 하이포게움 표(폐기)",
}

HERO_LANDSCAPE = {
    "source": "기준선 8.1(12:49 사용자 철회 반영)·8.2. 사용자 16:13·16:14: 콜로세움 둘레에는 땅 바탕뿐이다 — 판석·경계석·풀띠·문 앞 포장·둘레 나무·인물 무리·노점·공사장·길은 없다",
    "center_plan": [round(HERO_C_PLAN[0], 2), round(HERO_C_PLAN[1], 2)], "center_screen": list(HERO_C),
    "reserve_R_plan": LAND_RESERVE_R, "reserve_screen_box": HERO_BOXES["landscape"], "rep_R_plan": LAND_REP_R, "rep_screen_w": round(2 * LAND_REP_R * 1.2247449, 1),
    "boundary_screen": None, "base_side_mm": 0.0, "octagon": False, "front_cut": False,
    "kept": ["콜로세움 기단 계단 2단(건물의 일부)", "네로 거상 받침(Core 소품)과 그 작은 마당"],
    "pedestal": None, "side_mm": 0.0, "on_ground": "땅 윗면 Z 0에 바로 놓인다(외곽 테두리·지층·앞 변 단면 0).",
    "z_tops": {"땅": 0.0, "네로 마당 판석": 0.12},
    "gates": [], "crowds": [], "trees": [], "stalls_screen": [],
    "people": {"groups": [], "count": 0},
    "nero_yard": "hero.nero_yard(네로 거상 마당 [172, 196, 198, 228], hero 영역)",
}

HERO_SPEC = {
    "name": "콜로세움(Amphitheatrum Flavium) — 히어로·최대 단일 오브젝트",
    "center_screen": list(HERO_C), "center_plan": [round(HERO_C_PLAN[0], 2), round(HERO_C_PLAN[1], 2)],
    "center_note": "비워 두는 땅 중심. 콜로세움 외곽 타원 중심은 colosseum.center_plan (446.54, 161.86)",
    "pedestal": None, "side_mm": 0.0,
    "colosseum": HERO_COLOSSEUM,
    "landscape": HERO_LANDSCAPE,
    "interior": HERO_INTERIOR,
    "projected_box": HERO_BOXES["cluster"], "projected_box_rule": "위계 사전 검사는 히어로 군(건물 ∪ 조경) 투영 상자, 사후 검사는 실제 그린 외곽 상자(drawn.json·sil.json)끼리(D4)",
    "projected_box_building": HERO_BOXES["building"], "projected_box_landscape": HERO_BOXES["landscape"], "projected_box_cluster": HERO_BOXES["cluster"],
    "projected_boxes": HERO_BOXES,
    "nero_yard": NERO_YARD,
    "gates_screen": {},
    "form": [
        "LocalBanana 첨부 이미지와 같은 본체(기준선 8.1): 외곽 타원 평면 반축 44.0×36.6, 장축은 평면 방위 315°(화면 가로), 중심 평면 (446.54, 161.86)은 조경 중심에서 (−15.8, −11.8) 뒤-왼쪽으로 물렸다. 아치 40칸, 층 윗선 z 11.5·24.5·37.0·53.0",
        "부서진 정도(평면 방위 θ): 100~112° 경사 부벽(41·46·50) → 112~205° 4층 53 → 205~209° 수직 끊김 44 → 209~322° 3층 37(일부 33.5) → 322~338° 계단(31·27) → 338~18° 2층 24.5(윗선 18.0~24.5 들쭉날쭉) → 18~72° 경기장 앞 정면 1층 + 부서진 2층 토막(상한 17.0) → 72~80° 30 → 80~100° 3층 37",
        "둘째 고리(안쪽 아케이드) 37, 정면 10~80°만 9~12로 무너짐. 외벽 두께 2.4, 바깥 회랑 2.8, 둘째 고리 1.6",
        "관람석: 외곽에서 깊이 10.4~22.7, 높이 24.0 → 4.4. 계단석은 θ 238~360°·0~48°, 나머지는 방사벽과 짙은 빈칸(무너진 볼트). 포디움 벽 깊이 22.7~23.9",
        "경기장 반축 20.1×12.7: 장축 좌표 u ≥ −2.0은 복원 나무 바닥(약 55%, Z 0.6, 난간), u < −2.0은 하이포게움(바닥 Z −4.0, 동심 벽 0.86·0.72·0.58·0.44·0.30배, 중앙 통로 ±0.9, 12°마다 칸막이 0.33~0.97, 벽 두께 0.45~0.55)",
        "땅 위에 바로 선다(옆면 0, 단 없음). 사용자 16:13·16:14: 콜로세움 둘레에는 땅 바탕뿐이다(광장·인물·노점·공사장·둘레 나무·길 없음). 네로 거상 받침과 작은 마당만 곁에 둔다",
        "LocalBanana 둘레 조경 배치는 옮기지 않는다(사용자 12:49 철회): 둘레는 승인 설계 히어로 군 구성만 쓴다",
        "비례: 건물 화면 폭 107.8 = 기준 폭 203.5의 0.53. 위계는 히어로(콜로세움 건물) 단일 오브젝트로 잰다. 라벨 수치는 실제값(약 188×156 m, 높이 약 48 m)",
    ],
}

# ═════════════ Blender 무대·높이 기준(D12·D13). global이 core_map.blender_geo로 쓴다 ═════════════
_STAGE_PLAN = [[round(v, 2) for v in to_plan(x, y)] for x, y in ((STAGE[0], STAGE[1]), (STAGE[2], STAGE[1]), (STAGE[2], STAGE[3]), (STAGE[0], STAGE[3]))]
BLENDER_GEO = {
    "source": "공통 결정 D12·D13(통합 루프 0-1절). Blender 패키지(hero·city·baths·suburb·coast·ground)가 읽는 기계용 열쇠",
    "stage_screen": list(STAGE),
    "ground_plate": {"plan_corners": _STAGE_PLAN, "z_top": 0.0, "z_bottom": -10.0,
                     "rule": "땅 판 윗면(Z 0) 외곽 = 화면 무대 [0, 92]~[420, 478]를 평면으로 되돌린 평행사변형(꼭짓점 순서: 화면 왼쪽 위 → 오른쪽 위 → 오른쪽 아래 → 왼쪽 아래). 위 변 = 화면 y 92 수평선, 왼쪽 x 0·오른쪽 x 420은 블리드"},
    "sea": {"z": -9.7, "bleed_screen_y": 594.0, "bleed_edges": ["왼쪽 변", "아래 변"], "coastline": "평면 Y %.1f(화면 y = tan30·x + %.1f)" % (COAST_Y, COAST_Y)},
    "coast_strata": {"thickness_mm": 10.0, "layers": 3, "where": "해안선(±30°) 앞면에만"},
    "top_edge": {"min_object_top_screen_y": 93.0},
    "no_object_zones_screen": {"P2 자리": [302.0, 20.0, 402.0, 92.0], "위 띠": [0.0, 0.0, 420.0, 92.0]},
    "z": {"ground_top": 0.0, "river_water": -2.0, "sea_water": -9.7, "harbor_canal_water": -2.0, "road_top": [0.285, 0.31], "nero_yard": [0.12, 0.24],
          "building_paving_step_max": 0.3, "min_overlap_face_dz": 0.05, "hero_pit_floor": -4.0, "mausoleum_base_top": 5.0, "bridge_deck": 3.0},
    "z_rules": ["떠 있음·관통·z-파이팅 0(겹치는 면의 Z 차 ≥ 0.05)",
                "땅 파기는 X_CUT_*로만: hero X_CUT_HeroPit(경기장 u < −2.0을 Z −4.0까지), coast X_CUT_Coast*(내항·운하). ground가 맨 마지막에 모두 적용",
                "R7 진입 경사(Y 294.76~304.76, Z 0 → 3.0)와 영묘 북쪽 디딤 2단(Y 325.9~329.9, Z 3.67·4.33)으로 길–다리–기단 보행면 높이 차 0(D7)"],
    "compose": {"order": ["종이 (231, 208, 160)", "Blender map.png(투명 바탕)", "정보 층 .work/design/d5/out/info/info_layer.png(d5 render.py INFO_ONLY=1)"],
                "px_per_mm": {"poster": 3, "crops": 8}, "poster_px": [1260, 1782]},
}


# ═════════════ 지형(20:53 사용자 21:45): 실제 크기·방향, 창 밖까지, 가장자리로 갈수록 원근 축소 + 대기 원근 ═════════════
# 등각은 정사영이라 원근이 저절로 생기지 않는다 → 지도 중심(Core 군집)에서 화면 거리 d(mm)에 따른 배율 s(d)와 대기 원근(연하고 푸르게)을 쓴다.
PERSP = {"center_screen": [210.0, 285.0], "d": [150.0, 280.0, 330.0], "scale": [1.0, 0.55, 0.40], "haze": [0.25, 0.60, 0.78],
         "haze_color": [200, 206, 206],
         "note": "d ≤ 150(Core 군집 가장자리) 배율 1.0·안개 0.12 → d 280(창 가장자리) 0.55·0.50 → d ≥ 330(창 밖) 0.40·0.70. 사이는 선형"}


def persp(d):
    xs, ss, hs = PERSP["d"], PERSP["scale"], PERSP["haze"]
    if d <= xs[0]:
        return ss[0], hs[0]
    for i in range(1, len(xs)):
        if d <= xs[i]:
            t = (d - xs[i - 1]) / (xs[i] - xs[i - 1])
            return ss[i - 1] + (ss[i] - ss[i - 1]) * t, hs[i - 1] + (hs[i] - hs[i - 1]) * t
    return ss[-1], hs[-1]


TERRAIN_SET = [
    {"id": "albano", "name": "알바노 구릉(산맥)", "kind": "albano", "dir": "남동", "plan_center": [666.0, 265.0], "plan_half": [64.0, 115.0], "yaw_deg": 0.0, "height_mm": 95.0,
     "note": "로마 남동쪽 큰 화산 구릉. 테베레 동쪽 둑에서 시작해 창 아래·오른쪽 밖까지 이어진다"},
    {"id": "appennino", "name": "아펜니노 산맥(북동 먼 곳)", "kind": "albano", "dir": "북동", "plan_center": [350.0, -106.0], "plan_half": [70.0, 40.0], "yaw_deg": 0.0, "height_mm": 110.0,
     "note": "동·북동 먼 산맥. 창 오른쪽 위 모서리에 일부만 보인다"},
    {"id": "aq_hill_w", "name": "수도교 서쪽 언덕(골짜기 서쪽 비탈)", "kind": "albano", "dir": "북", "plan_center": [300.0, -62.0], "plan_half": [46.0, 30.0], "yaw_deg": 0.0, "height_mm": 62.0,
     "note": "수도교 서쪽 끝이 닿는 언덕 자락"},
    {"id": "aq_hill_e", "name": "수도교 동쪽 언덕(골짜기 동쪽 비탈)", "kind": "albano", "dir": "북동", "plan_center": [462.0, -62.0], "plan_half": [44.0, 30.0], "yaw_deg": 0.0, "height_mm": 62.0,
     "note": "수도교 동쪽 끝이 닿는 언덕 자락"},
    {"id": "vesuvio", "name": "베수비오(남동 아주 먼 곳)", "kind": "vesuvio", "dir": "남동 아주 멀리", "plan_center": [716.0, 232.0], "plan_half": [26.0, 26.0], "yaw_deg": 0.0, "height_mm": 85.0,
     "note": "가장 멀어 가장 작다. 창 오른쪽 아래 모서리에 일부만 보인다"},
]
for _t in TERRAIN_SET:
    _sc = to_screen(*_t["plan_center"])
    _d = math.hypot(_sc[0] - PERSP["center_screen"][0], _sc[1] - PERSP["center_screen"][1])
    _s, _h = persp(_d)
    _t["screen_center"] = [round(_sc[0], 2), round(_sc[1], 2)]
    _t["dist_mm"] = round(_d, 1)
    _t["persp_scale"], _t["haze"] = round(_s, 3), round(_h, 3)
