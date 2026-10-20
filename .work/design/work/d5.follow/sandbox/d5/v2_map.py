# -*- coding: utf-8 -*-
"""설계안 — Core 지도(히어로·랜드마크·강·바다·길·수도교·소품·지형·심은 지면·포르투스·지리). 담당: map

d5 변경(기준선 8.1·8.2 + 사용자 12:49 철회, 통합 루프 0-1절, 공통 결정 D2~D7·D12·D13)
- 팔각 받침을 지웠다(HERO_R·HERO_SIDE·HERO_RING·HERO_WALLS·hero_oct·hero_ring_pt·HERO_CUTAWAY 삭제). 콜로세움과 조경은 땅(Z 0) 위에 바로 놓이고 옆면은 0mm다.
- 콜로세움 본체를 LocalBanana 구성으로 다시 적었다(HERO_COLOSSEUM, D2): 외곽 타원 평면 반축 44.0×36.6·장축 방위 315°(화면 가로)·중심 평면 (446.54, 161.86),
  아치 40칸, θ별 외벽 높이 표, 둘째 고리 37(정면 10~80°만 9~12), 관람석·계단석 구역, 경기장 반축 20.1×12.7, 나무 바닥(u ≥ −2.0)·하이포게움(u < −2.0).
  내부 표는 HERO_INTERIOR 하나다(render·hero가 이 표만 읽는다). d4의 ring_ratio 0.74·벽 60/28/12·원형 고리·가로벽 격자 하이포게움 표는 폐기했다.
- 조경(HERO_LANDSCAPE): 사용자 12:49 철회에 따라 LocalBanana 조경 배치(기둥 폐허·쓰러진 토막·단칸 아치·벽돌 담·작은 신전·열주·6주 신전 앞면·포장 고리·판석 갈래길·노점 배치)는 옮기지 않는다.
  둘레는 승인 설계 히어로 군: 광장 포장(판석) + 문 3(R1 아피아 가도·R4 하역장 길·R7 다리 길) + 인물 무리 4 + 둘레 나무 + 기초 공사장 + 네로 거상 마당 + 둘레 시내 지붕.
  예약 반지름은 평면 90(옛 히어로 자리), 비례는 건물 폭 / 조경 대표 폭 = 0.53.
- 투영 상자를 셋으로 나눴다: 건물·조경·히어로 군(HERO_BOXES). R7 북쪽 끝을 광장 판석까지 늘이고(평면 Y 250.4), R1·R4도 판석과 겹치게 이었다(문 자리는 그대로).
- 영묘–다리–R7 높이 접속(R7 끝 진입 경사·기단 북쪽 디딤 2단), L5 그림 1.04배, L6·L9 상자 실측 정정, L5 겉면 문구, 네로 마당, 콜로세움 뒤 시내 지붕 블록, Blender 무대·높이 기준(BLENDER_GEO).

d4 변경(사용자 검토 2026-10-19 02:24 + 사용자 선택 03:10, 기준선 7절)
- 무대 확장(R·T 자리) 해제, 베수비오 군을 지도 무대 오른쪽 위로, 랜드마크 3개 추가(L7·L8·L9), 새 길 R7, 소품 '네로 청동 거상과 콘크리트(벽돌 마감) 받침'.
- 소품 재배치(석회 가마·바지선 2·오스티아), 포르투스 등대섬 78°·반지름 22, 운하 plan_y = 그린 끝점, 수도교 관통 아치."""
from v2_base import *  # noqa: F401,F403

# ═════════════ Core 히어로: 콜로세움(기준선 8.1·8.2, 공통 결정 D2·D3) ═════════════
# 조경(광장) 중심 = 옛 히어로 중심. 받침은 없다: 콜로세움과 조경은 땅 윗면(Z 0)에 바로 놓이고 도시 조직과 이어진다(옆면 0mm)
HERO_C = (250.0, 318.0)          # 조경 중심(화면)
HERO_C_PLAN = to_plan(*HERO_C)   # 조경 중심(평면) = (462.34, 173.66)

# ── 콜로세움 본체(D2). 방위 θ = atan2(평면 dY, 평면 dX)(Blender roma_kit.plan_az와 같다):
#    0° 화면 오른쪽 아래, 45° 정면 아래, 135° 왼쪽, 225° 위, 315° 오른쪽
COLO_C_PLAN = (446.54, 161.86)   # 외곽 타원 중심(평면) = 조경 중심 + (−15.8, −11.8): LocalBanana처럼 뒤-왼쪽으로 물림
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


COLO_SIL = colo_silhouette()
COLO_BASE_SCREEN = [to_screen(*colo_plan_pt(t)) for t in range(0, 360, 3)]

# ── 조경(D3 중 12:49 철회 뒤 남는 것). 받침 0: 옆면 0mm, 외곽 테두리·지층·앞 변 단면 없음
LAND_RESERVE_R = 90.0            # 예약 반지름(평면). 다른 패키지는 이 안에 아무것도 두지 않는다(길 R1·R4·R7의 문 접속만 예외)
LAND_PLAZA_R_REP = 83.1          # 광장 판석 대표 원(평면): 화면 폭 203.5 → 콜로세움 폭 비 0.53


def plaza_rb(theta_rad):
    """광장 판석 경계 반지름(평면): rb(θ) = 84.5 + 3·sin(3θ+0.7) + 1.5·sin(7θ+0.2), θ는 조경 중심에서 잰 평면 방위(라디안). 범위 79.5~89.5"""
    return 84.5 + 3.0 * math.sin(3.0 * theta_rad + 0.7) + 1.5 * math.sin(7.0 * theta_rad + 0.2)


def plaza_plan_poly(n=120):
    X0, Y0 = HERO_C_PLAN
    out = []
    for k in range(n):
        t = 2.0 * math.pi * k / n
        r = plaza_rb(t)
        out.append((X0 + r * math.cos(t), Y0 + r * math.sin(t)))
    return out


def plaza_boundary_y(X, side=-1):
    """평면 X에서 광장 판석 경계의 평면 Y(side −1 = 뒤쪽(작은 Y), +1 = 앞쪽(큰 Y)). 이분법"""
    X0, Y0 = HERO_C_PLAN
    lo, hi = 0.0, 95.0
    for _ in range(60):
        mid = (lo + hi) / 2.0
        Y = Y0 + side * mid
        t = math.atan2(Y - Y0, X - X0)
        if math.hypot(X - X0, Y - Y0) <= plaza_rb(t):
            lo = mid
        else:
            hi = mid
    return Y0 + side * lo


def _reserve_screen_poly(R, n=96):
    X0, Y0 = HERO_C_PLAN
    return [to_screen(X0 + R * math.cos(2 * math.pi * k / n), Y0 + R * math.sin(2 * math.pi * k / n)) for k in range(n)]


PLAZA_PLAN = plaza_plan_poly()
PLAZA_SCREEN = [to_screen(X, Y) for X, Y in PLAZA_PLAN]
RESERVE_SCREEN = _reserve_screen_poly(LAND_RESERVE_R)


def _box2(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return [round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2)]


HERO_BOXES = {
    "building": _box2(COLO_SIL),
    "landscape": _box2(RESERVE_SCREEN),
    "note": "건물 = 콜로세움 실루엣 외곽 상자, landscape = 옛 광장 자리(평면 R 90.5) 화면 상자(13:33 광장 0, 채움 금지 구역), cluster = d4 기록(위계에 쓰지 않음). 위계의 히어로 군은 건물 ∪ 공사장 ∪ 인물 무리 ∪ 노점 ∪ 네로 받침",
}
HERO_BOXES["cluster"] = [min(HERO_BOXES["building"][0], HERO_BOXES["landscape"][0]), min(HERO_BOXES["building"][1], HERO_BOXES["landscape"][1]),
                         max(HERO_BOXES["building"][2], HERO_BOXES["landscape"][2]), max(HERO_BOXES["building"][3], HERO_BOXES["landscape"][3])]
for _k in ("building", "landscape", "cluster"):
    _b = HERO_BOXES[_k]
    HERO_BOXES[_k + "_wh"] = [round(_b[2] - _b[0], 2), round(_b[3] - _b[1], 2)]
    HERO_BOXES[_k + "_area_mm2"] = round((_b[2] - _b[0]) * (_b[3] - _b[1]), 1)
HERO_BOXES["building_silhouette_area_mm2"] = round(_poly_area(COLO_SIL), 1)
HERO_BOXES["width_ratio_building_over_plaza_rep"] = round(HERO_BOXES["building_wh"][0] / (2.0 * LAND_PLAZA_R_REP * 1.2247449), 3)

# 공사장(Core 소품, 히어로 군의 일부). 상자·원점·⑥ 도착점은 d4 그대로다(D5)
WORKSITE = {"name": "콜로세움 기초 공사장(복원 장면)", "box": [208.0, 386.0, 250.0, 410.0], "plan_origin": [519.71, 260.29],
            "z1_origin_screen": [232.0, 396.8],
            "note": "나무 거푸집, 다짐 막대 일꾼 2, 반죽 통, 재료 더미(생석회 흰색·화산재 붉은 갈색·골재 회색). 콜로세움 앞-왼쪽 땅 위(옛 광장 경계 R 90.5 밖)에 놓인다. "
                    "제작 과정 패널 ⑥의 지시선 도착점(거푸집 앞-왼쪽 면 중심, 공사장 지역 좌표 (6.5, 9.0, 2.0)). "
                    "확대 창 Z1의 출발점은 거푸집 오른쪽 면(다져 넣은 층) 화면 (232.0, 396.8)"}

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
_ap0 = to_plan(340.0, 286.8)              # 아피아 가도 문(평면 483.10, 90.50): 조경 예약 원 안 뒤-오른쪽 문 자리(d4 그대로)


def _road_into_plaza(xc, w_screen, side, overlap=0.5, n=40):
    """평면 X 상수 길(화면 수직 폭 w_screen)이 광장 판석과 띠 전체 폭에서 overlap 이상 겹치는 끝 Y.
    side −1: 판석 뒤쪽 경계(작은 Y)에서 들어오는 길(시작 Y ≥ 경계 최대 + overlap), +1: 앞쪽 경계(큰 Y)에서 들어오는 길(시작 Y ≤ 경계 최소 − overlap)"""
    hw = w_screen / (2 * C30)
    ys = [plaza_boundary_y(xc - hw + 2 * hw * k / n, side) for k in range(n + 1)]
    if side < 0:
        return math.ceil((max(ys) + overlap) * 10.0) / 10.0
    return math.floor((min(ys) - overlap) * 10.0) / 10.0


# 문 3곳(D3)의 길 끝을 광장 판석 안까지 잇는다(판석 갈래길은 12:49 철회로 없다 → 길 띠 자체가 판석과 0.5 이상 겹친다)
_NOFILL_R = 90.5                                        # 13:35 옛 광장 자리(조경 중심 평면 반지름): 길·집·나무·밭 0
_R1_Y0 = round(HERO_C_PLAN[1] - math.sqrt(_NOFILL_R ** 2 - (_ap0[0] - HERO_C_PLAN[0]) ** 2), 2)   # 85.57: R 90.5 경계에서 시작
_R4_X = HERO_C_PLAN[0]                                  # 462.34
_R4_GATE_Y = 263.81                                     # 하역장 길 문(조경 예약 원 R 90 앞-왼쪽, d4 그대로)
_R4_Y0 = round(HERO_C_PLAN[1] + _NOFILL_R, 2)                  # 264.16: R 90.5 경계에서 시작
_R7_X = 489.6
_R7_Y0 = round(HERO_C_PLAN[1] + math.sqrt(_NOFILL_R ** 2 - (_R7_X - HERO_C_PLAN[0]) ** 2), 2)   # 259.96: R 90.5 경계에서 시작
_BANK_N = RIVER_Y - RIVER_W1 / (2 * C30)                # 테베레 북쪽 둑 Y 304.76
# R7 끝 진입 경사(D7): 다리 상판 Z 3.0과 길(Z 0)의 높이 차를 R7 남쪽 끝 10mm 안에서 잇는다
R7_RAMP = {"name": "폰스 아일리우스 진입 경사(R7 남쪽 끝)", "X": [round(_R7_X - 8.0 / (2 * C30), 2), round(_R7_X + 8.0 / (2 * C30), 2)],
           "Y": [round(_BANK_N - 10.0, 2), round(_BANK_N, 2)], "z": [0.0, 3.0], "owner": "ground",
           "note": "R7 띠 X 484.98~494.22 안, 평면 Y 294.76 → 304.76에서 윗면 Z 0 → 3.0(다리 상판 높이). 화면 축 (168.74, 392.18) → (160.08, 397.18). 길 윗면(ROAD_Z 0.3)에서 시작해 상판 북쪽 끝과 높이 차 0"}
_R2_END = to_plan(224.0, 140.5)           # 시내 길 1의 욕장 쪽 끝(d2와 같음)
_R2_X = _R2_END[0]                        # 시내 길 1 = 평면 X 상수
_R2_Y0 = to_plan(71.56, 228.50)[1]        # 판테온 쪽 끝: 축 ↙ 49mm(렌더러 +30mm 연장 + 19mm)
_R3_P0 = to_plan(88.02, 169.0)            # 시내 길 2 시작(렌더러 +30mm 연장을 넣은 값) = 평면 Y 상수
_R5_X1 = 234.5 / C30 + _R2_END[1]         # 욕장 진입로 끝: 화면 x 234.5(욕장 지면 뒤-왼쪽 변)
_MET_X = 529.6                            # 메텔라 진입로 꺾임(평면 X)
_MET_Y = 85.9                             # 메텔라 진입로 1(평면 Y 상수)
_MET_Y1 = 111.66                            # 메텔라 진입로 2 끝(평면 Y) = 무덤 대지 뒤-오른쪽 변
ROADS = [
    {"id": "R1", "name": "아피아 가도(Via Appia, 주축 길)", "w": 16.0, "center_line": True,
     "plan": [(_ap0[0], _R1_Y0), (_ap0[0], _ap0[1] - 92.4 - 14.0)], "gate_plan": [round(_ap0[0], 2), round(_ap0[1], 2)],
     "note": "d5(13:35): 띠는 옛 광장 경계(조경 중심 평면 R 90.5, Y 85.57)에서 시작해 ↗로 나가 오른쪽 변 (420, 240.6) 밖 (432.1, 233.6)까지 블리드한다(옛 광장 자리 안에 길 0). 흰 중앙선 1.6mm는 길 끝까지. 메텔라 무덤은 진입로 R6a·R6b로 잇는다. 바닥 글 'VIA APPIA 아피아 가도 → 캄파니아'"},
    {"id": "R2", "name": "시내 길 1(판테온 ↗ 카라칼라 욕장)", "w": 8.0, "center_line": False,
     "plan": [(_R2_X, _R2_Y0), (_R2_X, _R2_END[1])],
     "note": "판테온 광장 뒤 꼭짓점 ≈(76.7, 231.9)과 약 1.5mm 떨어진 (71.56, 228.50)에서 ↗로 카라칼라 욕장 왼쪽까지 (224.0, 140.5). 판테온 쪽 끝은 돔 뒤로 숨는다(렌더러의 시작 +30mm 연장 + 19mm를 사양 좌표에 넣었다). 콜로세움 뒤-왼쪽 4층 조각 위 약 60mm를 지난다"},
    {"id": "R3", "name": "시내 길 2(트라야누스 시장 ↘ 시내 길 1)", "w": 8.0, "center_line": False,
     "plan": [(_R3_P0[0], _R3_P0[1]), (_R2_X + _HW8, _R3_P0[1])],
     "note": "트라야누스 시장 지면 (88.02, 169.0)에서 ↘로 시내 길 1과 T자로 만난다. 끝은 시내 길 1의 먼 변까지(교점 +X 4.6mm)라 T자 빈틈이 없다(렌더러의 시작 +30mm·끝 +4.6mm 연장을 사양 좌표에 넣었다)"},
    {"id": "R4", "name": "하역장 길(콜로세움 앞-왼쪽 문 ↙ 테베레 하역장)", "w": 10.0, "center_line": False,
     "plan": [(_R4_X, _R4_Y0), (_R4_X, _BANK_N)], "gate_plan": [round(_R4_X, 2), _R4_GATE_Y],
     "note": "d5(13:35): 띠는 옛 광장 경계(평면 (462.34, 264.16), R 90.5)에서 시작해 평면 법선 방향(↙)으로 강 오른쪽 둑의 하역장까지 간다(옛 광장 자리 안에 길 0). 수레 1대"},
    {"id": "R5", "name": "욕장 진입로(시내 길 1 ↘ 카라칼라 욕장)", "w": 8.0, "center_line": False,
     "plan": [(_R2_X - _HW8, _R2_END[1]), (_R5_X1, _R2_END[1])],
     "note": "시내 길 1의 욕장 쪽 끝 (224.0, 140.5)에서 ↘로 꺾어 욕장 지면 뒤-왼쪽 변 (234.5, 146.6)에 닿는다(간격 0, Codex 지적: 욕장–R2 실제 지면 6.5mm 떨어짐). 축은 (224.0, 140.5) → (234.5, 146.6)이고, 띠 시작만 시내 길 1의 바깥 변까지 반폭 4.62mm 당겨 L자 모서리를 메운다(화면 (220.0, 138.2))"},
    {"id": "R6a", "name": "메텔라 진입로 1(아피아 가도 ↘)", "w": 8.0, "center_line": False,
     "plan": [(_ap0[0], _MET_Y), (_MET_X, _MET_Y)],
     "note": "아피아 가도 시작부(평면 483.1, 85.9 = 화면 344.0, 284.5)에서 ↘로 갈라져 콜로세움 조경 뒤-오른쪽 가장자리를 따라 (399.1, 316.3)까지. Codex 지적: 메텔라 기단–아피아 가도 44.7mm 떨어짐"},
    {"id": "R6b", "name": "메텔라 진입로 2(↙ 무덤 대지)", "w": 8.0, "center_line": False,
     "plan": [(_MET_X, _MET_Y - _HW8), (_MET_X, _MET_Y1)],
     "note": "진입로 1의 끝에서 ↙로 꺾어 무덤 대지 뒤-오른쪽 변 (391.0, 321.0)에 닿는다. 축은 평면 (546.7, 85.9) → (546.7, 95.2)이고, 띠 시작만 진입로 1의 바깥 변까지 반폭 4.62mm 당겨 L자 모서리를 메운다(화면 (403.1, 314.0))"},
    {"id": "R7", "name": "다리 길(콜로세움 앞-왼쪽 변 ↙ 폰스 아일리우스)", "w": 8.0, "center_line": False,
     "plan": [(_R7_X, _R7_Y0), (_R7_X, _BANK_N)], "gate_plan": [_R7_X, _R7_Y0], "ramp": R7_RAMP,
     "note": "d5(13:35): 북쪽 끝 = 옛 광장 경계(평면 (489.6, 259.96), R 90.5). → 폰스 아일리우스 북쪽 끝(테베레 북쪽 둑 Y 304.76). 평면 X 489.6 상수, 띠 폭 평면 9.24 = 화면 8.0. 남쪽 끝 10mm(Y 294.76~304.76)는 진입 경사(Z 0 → 3.0, ramp)라 다리 상판과 높이 차 0. 다리 상판(X 486.1~493.1)이 이 띠 안에서 시작한다"},
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
    "base": {"name": "사각 기단", "X": [467.1, 512.1], "Y": [325.9, 370.9], "h": 5.0,
             "note": "45×45 정사각 기단(평면). 뒤-오른쪽 변(평면 Y 325.9)이 테베레 남쪽 둑(Y 323.24)과 평면 2.66 = 화면 2.30mm(접속 ≤ 2.5)"},
    "drum": {"name": "원통", "c": [489.6, 348.4], "r": 16.0, "z": [5.0, 23.0], "skin": "겉 = 대리석", "core": "속 = 콘크리트 원통",
             "note": "기단 가운데의 큰 원통. 절개하지 않는다(겉 대리석 면 + 위쪽 테두리 띠에 콘크리트 속을 보이는 작은 이음 자국)"},
    "top": {"name": "정상(낮은 둔덕·난간)", "parapet": {"r": 16.0, "z": [23.0, 25.5]}, "mound": {"r_max": 10.0, "z_top": 28.0},
            "omit": "정상 조각(황제상·사두마차)과 교황 증축(산탄젤로성) 형태는 그리지 않는다",
            "note": "테두리 난간은 낮게(z 25.5까지) 둔다: 원통 꼭대기 테두리가 강 건너 하역장 부두 앞 변(d3 그림)과 화면 2.2mm 떨어진다(기획대로 테두리를 z 28까지 올리면 부두 앞 변과 0.23mm 겹친다). 안쪽 흙 둔덕은 꼭대기 z 28(테두리 안쪽이라 실루엣 밖으로 나가지 않는다), 나무 없음"},
    "bridge": {"name": "폰스 아일리우스", "deck_X": [486.1, 493.1], "deck_Y": [304.76, 325.9], "h": 3.0, "arches": 3,
               "piers_Y": [[309.9, 311.9], [316.1, 318.1]], "cutwater_X": [485.1, 494.1], "bridge": True,
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
_rp = R7_RAMP
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
L9_BOX_POLY = _bbox(L9_POLY)                     # 평면 원본 외곽 상자 [32.3, 271.4, 111.7, 329.3]
L9_BOX = [30.5, 271.4, 111.7, 329.3]              # d5(D4): 렌더 실측 상자(무대 쪽 낮은 유적이 왼쪽으로 1.8mm 더 나온다)로 정정


# ═════════════ Core 랜드마크(투영 상자 = 레이어 알파 외곽 상자 목표) ═════════════
LANDMARKS = [
    {"id": "L1", "name": "판테온", "latin": "Pantheon", "box": [18.0, 198.0, 128.0, 288.0], "zone": "시내(왼쪽 가운데, 강 위쪽 — 실제로 테베레 굽이 안쪽 캄푸스 마르티우스)",
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
     "form": "욕장 참조 이미지(열주·벽감 조각상·돔 열탕실·증기 욕조·목욕객)를 절개 단면으로: 칼다리움 드럼 벽(겉 벽돌·속 콘크리트·돔 위쪽 경석 층), 하이포코스트·화로 일꾼, 냉탕실 열주와 교차 볼트 한 칸(화면과 나란한 면으로 절개). 빛은 큰 창 중심, 오큘러스·코퍼는 복원 추정",
     "story": "겉은 벽돌, 속은 콘크리트. 돔 위쪽엔 가벼운 경석", "number": "열탕실 돔 경간 약 36 m",
     "links": "시내 길 1·욕장 진입로 R5(지면 뒤-왼쪽 변), 수도교 아치 열(오른쪽 변: 아쿠아 마르키아에서 갈라진 아쿠아 안토니니아나가 저수조 64개에 물을 댐[S47][S49])"},
    {"id": "L4", "name": "수도교 아치 열(아쿠아 안토니니아나)", "latin": "Aqua Antoniniana(아쿠아 마르키아 지선)", "box": [336.0, 134.0, 420.0, 208.5], "zone": "남동 교외(오른쪽 위, 오른쪽 변 블리드)",
     "geo": None, "real": "아쿠아 마르키아에서 갈라진 지선, 212–213년 비문[S47][S49]. 경로 좌표는 조사 보고서에 없어 지리 검사에서 뺀다",
     "form": "실제 경로가 아니라 욕장 급수 관계 모식(아쿠아 마르키아 → 아쿠아 안토니니아나 → 욕장 저수조 64개). 오른쪽 변 밖(남동 시골)에서 ↖로 들어와 카라칼라 욕장 오른쪽 변 (336, 160)에 닿는 아치 열, 높이 26mm(2단 아치), 교각 약 8mm 간격. 아치는 관통 아치로 그린다: 아래층 개구 폭 5.3mm·위층 3.9mm, 아치 안쪽 면 1.5mm가 보이고 개구부 뒤로 지면(밭·구릉)이 보인다(막힌 벽면에 아치 무늬만 그리지 않는다). 맨 위 수로에 물빛 선. 벽돌면 보수 구간 덧댐은 그리지 않는다(이 수도의 근거가 없다)",
     "story": "수로 안은 방수 모르타르", "number": "욕장 저수조 64개에 물을 댐",
     "links": "카라칼라 욕장(왼쪽 끝, 욕장 오른쪽 변 (336, 160))"},
    {"id": "L5", "name": "카이킬리아 메텔라 무덤", "latin": "Mausoleo di Cecilia Metella", "box": [319.36, 282.75, 395.26, 363.25], "zone": "남동 교외(오른쪽 가운데), 아피아 가도 남쪽 길가",
     "geo": (41.8518, 12.5205), "real": "콜로세움에서 4.9 km 남남동(151°), 아피아 가도",
     "form": "네모 기단 위 원통 드럼(16면 이상), 트래버틴 마름돌 겉면(일부 뜯겨 콘크리트 속이 보임), 꼭대기 아래 소머리·꽃줄 부조 띠, 중세 흉벽 증축은 그리지 않음. 둘레 사이프러스·소나무(진입로 R6a·R6b 띠 밖 2mm 이상)",
     "draw_scale": 1.0, "draw_scale_center": [357.31, 323.0], "draw_clip_x": None,
     "draw_box_d4": [354.0, 290.6, 420.0, 355.4], "draw_box_expected": [352.68, 289.3, 420.0, 356.7],
     "draw_rule": "d5(D4): 설계 2D 그림을 spec 상자 중심 (387.0, 323.0) 기준 1.04배로 키우고 x 420에서 자른다. d4 실측 [354.0, 290.6, 420.0, 355.4] = 66×64.8 = 4,276.8mm² → [352.68, 289.3, 420.0, 356.7] = 67.32×67.4 = 4,537mm²(≥ 4,530). Blender suburb는 fit_to_box로 spec 상자 [354, 288, 420, 358]을 채운다",
     "draw_gaps_expected_mm": {"대지–라벨 글 블록": 4.61, "대지–C4 상자": 46.0, "드럼 왼쪽 실루엣–지도 D 표지(d4 자리 (367.27, 314.66))": 0.68,
                               "rule": "D 표지는 2mm 이상 떨어져야 한다 → panels가 map_pt를 x 365.9 이하로 옮긴다(C4 지시선 시작 (370.5, 316.0)은 키운 드럼 면 안 1.4mm 그대로)"},
     "story": "BCE 30–10년의 원통 무덤", "number": "드럼 지름 29 m",
     "links": "아피아 가도 → 메텔라 진입로 R6a·R6b(무덤 대지 뒤-오른쪽 변)"},
    {"id": "L6", "name": "포르투스 항", "latin": "Portus Traiani · Portus Claudii", "box": [5.0, 372.0, 102.0, 434.8], "box_source": "d5: 렌더 실측 아래 변 434.8로 정정(d4 434.0)", "zone": "서남서 해안(왼쪽 아래), 강 오른쪽 둑과 해안 사이",
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
     "plan": BASILICA, "poly_screen": _r2(L7_POLY), "ground_screen": _r2(_L7_ground),
     "parts_screen": {"바실리카 지면": _r2(_L7_ground), "바실리카 측랑 볼트": _r2(_L7_aisle), "바실리카 신랑 유적": _r2(_L7_nave)},
     "gaps_expected_mm": {"기단 포장–시내 길 1(R2) 지면": 1.35, "실루엣–콜로세움 사전 검사 모형": 2.28, "실루엣–콜로세움 외벽(d3 그림 윗단 띠)": 2.3,
                          "실루엣–카라칼라 욕장 지면(d3 그림)": 2.45, "실루엣–네로 거상": 4.76},
     "draw": "평면 원본(plan)을 전역 등각 그대로 그린다(fit_frame 배율·높이 과장 없음). 투영 상자는 poly_screen의 외곽 상자"},
    {"id": "L8", "name": "하드리아누스 영묘·폰스 아일리우스", "latin": "Mausoleum Hadriani · Pons Aelius", "box": L8_BOX,
     "zone": "테베레 굽이 안쪽 오른쪽 둑(↘ 팔 남쪽, 포르투스 육각 내항과 강 사이) — 후보 자리 (나)",
     "geo": (41.9031, 12.4663), "real": "콜로세움에서 2.6 km 북서(304°), 테베레 서안",
     "form": "사각 기단 + 큰 원통(겉은 대리석, 속은 콘크리트 원통) + 정상의 낮은 흙 둔덕과 테두리 난간 + 테베레를 건너는 다리(아치 3개). "
             "정상 조각(복원 추정)과 교황 증축(지금의 산탄젤로성) 형태는 그리지 않는다. 카이킬리아 메텔라 무덤과는 사각 기단과 다리로 구분한다. 다리 북쪽 끝은 새 길 R7(남쪽 끝 진입 경사)로 콜로세움 앞-왼쪽 옛 광장 경계(R 90.5)까지 잇고, 기단 쪽은 북쪽 디딤 2단으로 기단 윗면에 오른다",
     "story": "겉은 대리석, 속은 콘크리트 원통", "number": None,
     "links": "테베레 남쪽 둑(기단 뒤-오른쪽 변, 실제 지면 간격 ≤ 2.5mm) + 폰스 아일리우스(강 위) + R7(다리 북쪽 끝)",
     "plan": MAUSOLEUM, "poly_screen": _r2(L8_POLY), "ground_screen": _r2(_L8_ground),
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
     "plan": THEATRE, "poly_screen": _r2(L9_POLY), "ground_screen": _r2(_L9_ground),
     "parts_screen": {"극장 반원 아케이드": _r2(L9_POLY)}, "box_poly": L9_BOX_POLY,
     "box_source": "d5: 렌더 실측(81.2×57.9 = 4,701.5mm²)으로 정정. poly_screen(겹침용)은 평면 원본 그대로",
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
    {"name": "석회 가마", "box": [118.0, 296.0, 146.0, 328.0], "zone": "강 왼쪽 둑(콜로세움 조경 왼쪽 바깥)", "on": "땅",
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
     "plan": [327.0, 113.4],
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
NERO_YARD = {"name": "네로 거상 마당(작은 포장 마당)", "screen_box": [172.0, 196.0, 198.0, 228.0],
             "plan_poly": [[round(v, 2) for v in to_plan(x, y)] for x, y in ((172.0, 196.0), (198.0, 196.0), (198.0, 228.0), (172.0, 228.0))],
             "z_top": 0.12, "owner": "hero(짓는다) · ground(집·나무를 비운다)",
             "rule": "상자 안에 집·나무 0. 포장 판석(판석 길과 같은 PAL 'slab'), 받침 둘레 사람 2~3(키 4.9)",
             "discarded": "hero LAYOUT 'nero' (−40.7, 44.7) = 화면 (176, 320)"}
_nero["yard"] = NERO_YARD
TERRAIN = [
    {"name": "알바노 구릉 띠(화산 지대, 낮은 구릉)", "box": [318.0, 122.0, 420.0, 162.0],
     "note": "지면 결. 화산 그림이 아니다. 지도 무대 오른쪽 위 '가장 먼 곳'(대기 원근). 그리는 순서 산 → 포도밭 농장 → 구릉. 바닥 글 'COLLI ALBANI 알바노 구릉 — 로마 건물의 화산재'. 수도교 윗선과 겹치는 앞쪽은 수도교 뒤(먼 지면)로 그린다",
     "ridge": {"cover_vesuvius_base_mm": [3.0, 5.0], "order": ["베수비오", "포도밭 농장", "알바노 구릉 능선"],
               "cover_x_range": [360.0, 418.0], "continuous": True, "farm_merge": True,
               "note": "앞 능선이 베수비오 밑동 앞쪽 윤곽(바닥 고리 앞쪽 반)의 x 360~418 전체를 3~5mm 연속으로 가린다. 가운데(농장 구간)만 고정값으로 내리던 처리는 없다. "
                       "농장 지면(포도밭 농장 상자)과 앞 구릉은 한 지형 실루엣으로 이어(농장이 능선 위 비탈에 얹힌 모양) 산기슭의 닫힌 윤곽을 끊는다. 옛 열쇠 x_ranges·farm_front_top_y_min은 지웠다"}},
    {"name": "남동 교외 밭·포도밭(캄파냐)", "box": [296.0, 396.0, 420.0, 505.0],
     "note": "S 패널·콜아웃 C4가 앉는 고요한 영역. 오른쪽은 블리드, 아래 변은 지도 무대 아래 변 y 505에서 닫는다(하단 띠 오른쪽은 P5 패널의 띠 바탕)"},
    {"name": "시내 지붕 블록·나무(콜로세움 둘레)", "box": [112.0, L7_BOX[3], 330.0, 300.0], "exclude_boxes": [PROPS[-1]["box"], NERO_YARD["screen_box"]],
     "exclude_reserve": {"center_plan": [round(HERO_C_PLAN[0], 2), round(HERO_C_PLAN[1], 2)], "R_plan": 90.5},
     "exclude_screen": [_r2(_reserve_screen_poly(90.5, 72))],
     "edge_gap_plan_max": 3.0,
     "note": "지스몬디 '지붕의 바다' 밀도, 언덕에 나무 덩어리. d4: 위 변을 막센티우스 바실리카 투영 상자 아래 변까지 내리고 네로 거상 소품 상자를 뺀다. "
             "d5: 오른쪽 변을 330까지(옛 고리가 비운 콜로세움 뒤 띠 포함), 옛 광장 자리(평면 R 90.5)와 네로 마당을 뺀다(13:35: 그 경계에 붙이는 집 줄 없음)"},
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
    # d5: 옛 고리(60mm 외벽)가 덮던 콜로세움 뒤 띠를 시내 지붕 블록으로 채운다(밀도 ⑦ 유지)
    {"name": "콜로세움 뒤 시내 지붕 블록(옛 외벽 고리 자리)", "box": [196.0, 212.0, 330.0, 258.0], "cover": 0.25, "kind": "roofs",
     "exclude": ["콜로세움 실루엣 +2mm(HERO_SPEC colosseum.silhouette_screen)", "콜로세움 라벨 글 블록 +1.5mm(d4 슬롯 [270, 194, 318, 244])", "네로 마당 [172, 196, 198, 228]",
                 "옛 광장 자리(평면 R 90.5, 13:35)"],
     "free_mm2": 2366, "free_frac": 0.384, "roof_cover_of_free": 0.65,
     "note": "상자 6,164mm² 중 빈 면 2,366mm²(38%)에 지붕 블록·안뜰·작은 나무(지붕 덮음 0.65) → 상자 기준 덮음 0.25. ground(Blender)·render가 집을 놓고, 랜드마크 상자 +2mm·라벨 블록 +1.5mm에는 0"},
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


# ═════════════ d5 히어로 사양(core_map.hero 원본). global이 이 사전을 그대로 core_map.hero로 쓴다 ═════════════
def _sil_coarse(dx=1.0):
    pts = colo_silhouette(dx=dx)
    return [[round(x, 2), round(y, 2)] for x, y in pts]


HERO_COLOSSEUM = {
    "source": "기준선 8.1(LocalBanana 첨부 이미지와 같은 본체: 방향·부서진 정도·보이는 면·비례) + 공통 결정 D2. Blender roma_colo·roma_colo_in과 같은 값",
    "center_plan": list(COLO_C_PLAN), "center_screen": [round(v, 2) for v in to_screen(*COLO_C_PLAN)],
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
    "width_ratio_to_plaza_rep": HERO_BOXES["width_ratio_building_over_plaza_rep"],
    "discarded": "d4 ring_ratio 0.74, 벽 60/28/12, 원형 고리, 가로벽 격자 하이포게움 표(폐기)",
}

# 문 3곳(D3): 문 자리는 그대로, 길 띠는 광장 판석과 겹치게 늘였다
_RD = {r["id"]: r for r in ROADS}


def _gate(rid, name, gate_plan):
    r = _RD[rid]
    p0 = r["plan"][0]
    return {"id": rid, "name": name, "gate_plan": [round(gate_plan[0], 2), round(gate_plan[1], 2)],
            "gate_screen": [round(v, 2) for v in to_screen(*gate_plan)],
            "road_end_plan": [round(p0[0], 2), round(p0[1], 2)], "road_end_screen": [round(v, 2) for v in to_screen(*p0)],
            "road_w_screen": r["w"], "road_w_plan": round(r["w"] / C30, 2)}


_TREES = [
    # 둘레 나무(광장 가장자리 풀밭과 시내 조직을 잇는 자리). 땅 기준점은 화면 mm, 높이는 화면 mm(사람 키 4.9 기준 D8)
    ("사이프러스", (166.0, 288.0), 21.0), ("사이프러스", (165.3, 292.3), 17.0),
    ("사이프러스", (202.0, 356.3), 20.0), ("사이프러스", (198.8, 360.4), 16.5),
    ("사이프러스", (296.8, 269.0), 21.0), ("사이프러스", (303.7, 269.8), 17.5),
    ("사이프러스", (353.9, 312.0), 20.0), ("사이프러스", (355.0, 316.0), 16.5),
    ("사이프러스", (334.0, 334.0), 19.0),
    ("올리브", (184.0, 282.0), 15.0), ("올리브", (150.1, 326.0), 14.5), ("올리브", (315.8, 286.0), 15.5), ("올리브", (327.9, 343.0), 14.5),
]
_GROUPS = [
    ("G1", "앞(정면, 공사장 위쪽)", (245.0, 351.0), 6, None),
    ("G2", "앞-오른쪽(아피아 가도 끝 쪽)", (277.0, 339.0), 6, None),
    ("G3", "왼쪽(시내·네로 마당 쪽)", (186.0, 322.0), 6, None),
    ("G4", "앞-왼쪽(하역장 길 R4 끝 쪽)", (197.5, 349.5), 6, [186.0, 342.0, 209.0, 357.0]),
]


def _plan_of(pt):
    return [round(v, 2) for v in to_plan(*pt)]


def _r_in_reserve(pt):
    X, Y = to_plan(*pt)
    return round(math.hypot(X - HERO_C_PLAN[0], Y - HERO_C_PLAN[1]), 2)


HERO_LANDSCAPE = {
    "source": "기준선 8.1(12:49 사용자 철회 반영)·8.2 + 공통 결정 D3 중 철회 뒤 남는 항목. 13:33·13:35 반영: 히어로 군 = 기초 공사장·인물 무리·노점 2·네로 거상 받침과 마당. 광장 포장·둘레 나무·첫 집 줄은 짓지 않는다",
    "withdrawn_1249": {"rule": "콜로세움 둘레에 LocalBanana의 조경 배치를 옮겨 오지 않는다(사용자 12:49 철회, 루프 프롬프트의 '주변 조경' 문구는 무효)",
                       "not_built": ["기둥 폐허·쓰러진 토막", "단칸 아치", "낮은 벽돌 담", "작은 신전", "열주 폐허", "6주 신전 앞면", "뒤-오른쪽 문 폐허",
                                     "외벽을 두른 트래버틴 포장 고리", "회색 판석 띠와 갈래길", "노점(흰·빨간 차양) 배치", "암포라 무리"]},
    "center_plan": [round(HERO_C_PLAN[0], 2), round(HERO_C_PLAN[1], 2)], "center_screen": list(HERO_C),
    "reserve_R_plan": LAND_RESERVE_R, "reserve_screen_box": HERO_BOXES["landscape"], "rep_R_plan": LAND_PLAZA_R_REP, "rep_screen_w": round(2 * LAND_PLAZA_R_REP * 1.2247449, 1),
    "boundary_screen": None, "base_side_mm": 0.0, "octagon": False, "front_cut": False,
    "withdrawn_1333": {"rule": "사용자 13:33: 콜로세움 둘레의 넓은 판석 광장(판석 원판·경계석·문 앞 포장)을 없앤다. 13:35: 그 자리(조경 중심 평면 R 90.5)를 땅·길·시내 집·나무로 메우지 않고 Core 건축물이 더 잘 보이는 배치에 쓴다",
                       "not_built": ["광장 포장(판석)", "광장 가장자리 풀밭", "경계석", "문 앞 포장", "둘레 나무 13", "둘레 첫 집 줄"],
                       "kept": ["콜로세움 기단 계단 2단(건물의 일부)", "인물 무리 G1~G4·흩어진 사람(땅 Z 0)", "노점 2(땅 Z 0)", "네로 거상 받침·마당", "기초 공사장"]},
    "parts": ["기초 공사장(거푸집·일꾼·재료 더미)", "인물 무리 G1~G4 + 흩어진 사람(땅 Z 0)", "노점 2(흰·빨간 차양, 땅 기준점 (210, 364)·(300, 359))", "네로 거상 받침·마당"],
    "stalls_screen": [[210.0, 364.0], [300.0, 359.0]],
    "pedestal": None, "side_mm": 0.0, "on_ground": "땅 윗면 Z 0에 바로 놓인다(외곽 테두리·지층·앞 변 단면 0). 둘레 시내 지붕 블록과 바로 잇는다(빈 띠 ≤ 3mm 평면)",
    "reserve": {"R_plan": LAND_RESERVE_R, "screen_box": HERO_BOXES["landscape"], "screen_semi_axes": [round(LAND_RESERVE_R * 1.2247449, 2), round(LAND_RESERVE_R * 0.7071068, 2)],
                "rule": "13:35: 옛 광장 자리(평면 R 90.5) 안에는 Core 랜드마크와 히어로 군(건물·공사장·인물 무리·노점·네로 받침)만 둔다. 집·나무·밭·길·소품 0. 길 R1·R4·R7은 이 경계에서 끝난다"},
    "plaza_d5_withdrawn": {"name": "광장 포장(판석, PAL 'slab') — 13:33 철회(짓지 않음)", "rb": "84.5 + 3·sin(3θ+0.7) + 1.5·sin(7θ+0.2)(θ = 조경 중심에서 잰 평면 방위, 라디안), 허용 ±0.5",
              "rb_range_plan": [round(min(plaza_rb(2 * math.pi * k / 720) for k in range(720)), 2), round(max(plaza_rb(2 * math.pi * k / 720) for k in range(720)), 2)],
              "R_rep_plan": LAND_PLAZA_R_REP, "rep_screen_w": round(2 * LAND_PLAZA_R_REP * 1.2247449, 1),
              "boundary_plan": _r2(PLAZA_PLAN[::2]), "boundary_screen": _r2(PLAZA_SCREEN[::2]), "z_top": 0.12,
              "pattern": "판석 줄눈(L3)·마모 얼룩(L6). 6×6mm보다 큰 빈 단색 면 0(D10)"},
    "plaza": None, "fringe": None,
    "z_tops": {"땅": 0.0, "네로 마당 판석": 0.12, "길(ground ROAD_Z)": [0.285, 0.31]},
    "gates": [_gate("R1", "아피아 가도 끝(옛 광장 경계 R 90.5)", (_ap0[0], _R1_Y0)), _gate("R4", "하역장 길 끝(옛 광장 경계 R 90.5)", (_R4_X, _R4_Y0)),
              _gate("R7", "다리 길 끝(옛 광장 경계 R 90.5)", (_R7_X, _R7_Y0))],
    "people": {"h_screen": 4.9, "h_range": [4.6, 5.2], "w_over_h": 0.32, "neighbor_feet_mm": [3.5, 5.0],
               "groups": [{"id": gid, "name": nm, "center_screen": list(c), "center_plan": _plan_of(c), "r_plan": _r_in_reserve(c), "count": n,
                           **({"area_screen": a} if a else {})} for gid, nm, c, n, a in _GROUPS],
               "scattered": {"count": 7, "where": "땅(Z 0) 위, 콜로세움 실루엣·공사장·라벨 블록 밖(13:33 광장 0)"},
               "note": "옛 인물 군 3곳 (190,357)·(236,371)·(306,360)은 지운다(D3). 노점·폐허 둘레가 아니라 광장·문 길목에 선다(12:49 철회). "
                       "인원은 군마다 5~7명(G1 6·G2~G4 5): 승인 설계의 군 크기와 사후 검사 ⑧(군마다 5~7명)에 맞췄다(D3의 3명에서 늘림)"},
    "trees": [], "trees_rule": "13:35: 옛 광장 자리(R 90.5) 안 나무 0",
    "worksite": "hero.worksite(공사장, 옛 광장 경계 R 90.5 밖 앞-왼쪽, hero 영역 [206, 384, 252, 412])",
    "nero_yard": "hero.nero_yard(네로 거상 마당 [172, 196, 198, 228], hero 영역)",
    "city_edge": "둘레 시내 지붕은 옛 광장 자리(R 90.5) 밖에만 둔다. 경계에 붙이는 집 줄은 없다(13:35)",
}

HERO_LANDSCAPE["crowds"] = HERO_LANDSCAPE["people"]["groups"]       # global hero_landscape가 읽는 상위 열쇠(같은 목록)

HERO_SPEC = {
    "name": "콜로세움(Amphitheatrum Flavium) — 히어로·최대 단일 오브젝트",
    "center_screen": list(HERO_C), "center_plan": [round(HERO_C_PLAN[0], 2), round(HERO_C_PLAN[1], 2)],
    "center_note": "조경(광장) 중심. 콜로세움 외곽 타원 중심은 colosseum.center_plan (446.54, 161.86)",
    "pedestal": None, "side_mm": 0.0,
    "colosseum": HERO_COLOSSEUM,
    "landscape": HERO_LANDSCAPE,
    "interior": HERO_INTERIOR,
    "projected_box": HERO_BOXES["cluster"], "projected_box_rule": "위계 사전 검사는 히어로 군(건물 ∪ 조경) 투영 상자, 사후 검사는 실제 그린 외곽 상자(drawn.json·sil.json)끼리(D4)",
    "projected_box_building": HERO_BOXES["building"], "projected_box_landscape": HERO_BOXES["landscape"], "projected_box_cluster": HERO_BOXES["cluster"],
    "projected_boxes": HERO_BOXES,
    "worksite": WORKSITE,
    "nero_yard": NERO_YARD,
    "gates_screen": {g["name"]: g["gate_screen"] for g in HERO_LANDSCAPE["gates"]},
    "form": [
        "LocalBanana 첨부 이미지와 같은 본체(기준선 8.1): 외곽 타원 평면 반축 44.0×36.6, 장축은 평면 방위 315°(화면 가로), 중심 평면 (446.54, 161.86)은 조경 중심에서 (−15.8, −11.8) 뒤-왼쪽으로 물렸다. 아치 40칸, 층 윗선 z 11.5·24.5·37.0·53.0",
        "부서진 정도(평면 방위 θ): 100~112° 경사 부벽(41·46·50) → 112~205° 4층 53 → 205~209° 수직 끊김 44 → 209~322° 3층 37(일부 33.5) → 322~338° 계단(31·27) → 338~18° 2층 24.5(윗선 18.0~24.5 들쭉날쭉) → 18~72° 경기장 앞 정면 1층 + 부서진 2층 토막(상한 17.0) → 72~80° 30 → 80~100° 3층 37",
        "둘째 고리(안쪽 아케이드) 37, 정면 10~80°만 9~12로 무너짐. 외벽 두께 2.4, 바깥 회랑 2.8, 둘째 고리 1.6",
        "관람석: 외곽에서 깊이 10.4~22.7, 높이 24.0 → 4.4. 계단석은 θ 238~360°·0~48°, 나머지는 방사벽과 짙은 빈칸(무너진 볼트). 포디움 벽 깊이 22.7~23.9",
        "경기장 반축 20.1×12.7: 장축 좌표 u ≥ −2.0은 복원 나무 바닥(약 55%, Z 0.6, 난간), u < −2.0은 하이포게움(바닥 Z −4.0, 동심 벽 0.86·0.72·0.58·0.44·0.30배, 중앙 통로 ±0.9, 12°마다 칸막이 0.33~0.97, 벽 두께 0.45~0.55)",
        "땅 위에 바로 선다(옆면 0, 단 없음). 13:33 히어로 군: 기초 공사장(앞-왼쪽 바깥), 인물 무리 4 + 흩어진 사람(키 4.9, 땅 Z 0), 노점 2, 네로 거상 받침과 마당. 넓은 판석 광장·경계석·문 앞 포장·둘레 나무 0. 길 R1·R4·R7은 옛 광장 경계(R 90.5)에서 끝난다",
        "LocalBanana 둘레 조경 배치는 옮기지 않는다(사용자 12:49 철회): 둘레는 승인 설계 히어로 군 구성만 쓴다",
        "비례: 건물 화면 폭 107.8 = 광장 대표 폭 203.5의 0.53. 위계는 히어로 군(건물 ∪ 조경) 단일 오브젝트로 잰다. 라벨 수치는 실제값(약 188×156 m, 높이 약 48 m)",
    ],
}

# ═════════════ Blender 무대·높이 기준(D12·D13). global이 core_map.blender_geo로 쓴다 ═════════════
_STAGE_PLAN = [[round(v, 2) for v in to_plan(x, y)] for x, y in ((STAGE[0], STAGE[1]), (STAGE[2], STAGE[1]), (STAGE[2], STAGE[3]), (STAGE[0], STAGE[3]))]
BLENDER_GEO = {
    "source": "공통 결정 D12·D13(통합 루프 0-1절). Blender 패키지(hero·city·baths·suburb·coast·ground)가 읽는 기계용 열쇠",
    "stage_screen": list(STAGE),
    "ground_plate": {"plan_corners": _STAGE_PLAN, "z_top": 0.0, "z_bottom": -10.0,
                     "rule": "땅 판 윗면(Z 0) 외곽 = 화면 무대 [0, 92]~[420, 505]를 평면으로 되돌린 평행사변형(꼭짓점 순서: 화면 왼쪽 위 → 오른쪽 위 → 오른쪽 아래 → 왼쪽 아래). 위 변 = 화면 y 92 수평선, 왼쪽 x 0·오른쪽 x 420은 블리드"},
    "sea": {"z": -9.7, "bleed_screen_y": 594.0, "bleed_edges": ["왼쪽 변", "아래 변"], "coastline": "평면 Y %.1f(화면 y = tan30·x + %.1f)" % (COAST_Y, COAST_Y)},
    "coast_strata": {"thickness_mm": 10.0, "layers": 3, "where": "해안선(±30°) 앞면에만"},
    "top_edge": {"min_object_top_screen_y": 93.0},
    "no_object_zones_screen": {"P2 자리": [302.0, 20.0, 402.0, 92.0], "위 띠": [0.0, 0.0, 420.0, 92.0]},
    "z": {"ground_top": 0.0, "river_water": -2.0, "sea_water": -9.7, "harbor_canal_water": -2.0, "road_top": [0.285, 0.31], "plaza": [0.12, 0.24],
          "building_paving_step_max": 0.3, "min_overlap_face_dz": 0.05, "hero_pit_floor": -4.0, "mausoleum_base_top": 5.0, "bridge_deck": 3.0},
    "z_rules": ["떠 있음·관통·z-파이팅 0(겹치는 면의 Z 차 ≥ 0.05)",
                "땅 파기는 X_CUT_*로만: hero X_CUT_HeroPit(경기장 u < −2.0을 Z −4.0까지), coast X_CUT_Coast*(내항·운하). ground가 맨 마지막에 모두 적용",
                "R7 진입 경사(Y 294.76~304.76, Z 0 → 3.0)와 영묘 북쪽 디딤 2단(Y 325.9~329.9, Z 3.67·4.33)으로 길–다리–기단 보행면 높이 차 0(D7)"],
    "compose": {"order": ["종이 (231, 208, 160)", "Blender map.png(투명 바탕)", "정보 층 .work/design/d5/out/info/info_layer.png(d5 render.py INFO_ONLY=1)"],
                "px_per_mm": {"poster": 3, "crops": 8}, "poster_px": [1260, 1782]},
}
