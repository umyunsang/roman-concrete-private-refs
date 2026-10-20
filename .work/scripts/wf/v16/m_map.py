# -*- coding: utf-8 -*-
# 로마 콘크리트 A2 와이어프레임 — 지도 바탕(지면·테베레강·바다·길)과 풍경 소품(밭·수레·배·기중기·다리·바지선)
# 담당 패키지: map · 이 파일은 담당 워커만 고친다(공용 도구는 common.py, 조립은 main.py).

from common import *
from common import _a
import common as C
from m_core import NOTCH_X, NOTCH_Y, cell_verts, cell_center, CORE_X0, CORE_Y0, CORE_W, CORE_HW, CORE_HH, NCELL
from m_arena import ARENA_R, ARENA_XL, ARENA_CY, ARENA_CX
import m_support_bottom as SB

RIVER_W = 9.5
HUG = 24.0                          # 강 중심선과 코어 외곽선의 수직 간격
RIVER_A = (NOTCH_X + 2.0 * HUG, NOTCH_Y)     # 직각으로 꺾이는 꼭짓점(강이 코어 톱니에 안긴다)


def river_centerline(L2=96.0, L3=150.0):
    """오른쪽 위 액자 밖 → ↙ → A(직각) → ↘ → 직각 → ↙ → 바다. 모두 지면 축 ±30°."""
    t0 = (448.0 - RIVER_A[0]) / C30
    start = (RIVER_A[0] + C30 * t0, RIVER_A[1] - 0.5 * t0)
    pts = [start, RIVER_A]
    pts += walk(RIVER_A, [("SE", L2), ("SW", L3)])[1:]
    return pts




def draw_vineyard(L, cx, cy):
    """아피아 가도변 포도밭 구획: 포도 줄과 항아리, 작은 헛간"""
    slab(L, cx, cy, 44.0, t=2.6, top=(172, 188, 118), soil=SOIL)
    iso, S = iso_of_slab(L, cx, cy, 44.0)
    for i in range(6):
        y0 = 3.5 + i * 3.4
        iso.line3([(2.5, y0, 0.1), (S - 2.5, y0, 0.1)], (66, 128, 56), 0.5)
        for q in range(7):
            x_ = 3.0 + q * 3.2
            iso.line3([(x_, y0, 0.1), (x_, y0, 1.5)], (66, 128, 56), 0.3)
    iso.box(S - 9, 2.0, 0, S - 2.5, 7.5, 4.2, ((236, 214, 170), (224, 198, 150), (196, 166, 124)), ol=(120, 84, 54), lw=0.14)
    iso.poly3([(S - 9.5, 1.5, 4.2), (S - 2.0, 1.5, 4.2), (S - 2.0, 4.7, 6.2), (S - 9.5, 4.7, 6.2)], fill=shade(ROOF_RED, 1.1), ol=(130, 60, 40), lw=0.12)
    iso.poly3([(S - 9.5, 4.7, 6.2), (S - 2.0, 4.7, 6.2), (S - 2.0, 8.0, 4.2), (S - 9.5, 8.0, 4.2)], fill=ROOF_RED, ol=(130, 60, 40), lw=0.12)
    for (X, Y) in [(S - 4, S - 4), (S - 7, S - 3.5)]:
        x, y = iso.p(X, Y)
        L.ell(x, y - 1.3, 1.0, 1.3, fill=(176, 116, 78), outline=(110, 70, 44), lw=0.12)


def draw_field(L, cx, cy, kind="olive", w=44.0):
    """들판 구획(받침 위): olive 올리브 과수원+착유장, grain 곡식밭+볏단"""
    top = {"olive": (190, 192, 128), "grain": (226, 206, 130)}[kind]
    slab(L, cx, cy, w, t=2.6, top=top, soil=SOIL)
    iso, S = iso_of_slab(L, cx, cy, w)
    if kind == "olive":
        for i in range(3):
            for j in range(3):
                x, y = iso.p(5 + i * 8.5, 5 + j * 8.5)
                olive(L, x, y, 2.9)
        iso.box(S - 9, S - 9, 0, S - 2.5, S - 3.0, 4.0, ((236, 214, 170), (224, 198, 150), (196, 166, 124)), ol=(120, 84, 54), lw=0.14)
    else:
        for i in range(7):
            y0 = 2.5 + i * 2.6
            iso.line3([(2.5, y0, 0.1), (S - 2.5, y0, 0.1)], (200, 168, 82), 0.55)
        for (X, Y) in [(S - 8, 5), (S - 5, 9), (S - 10, 12)]:
            x, y = iso.p(X, Y)
            L.poly([(x - 1.2, y), (x + 1.2, y), (x + 0.6, y - 3.0), (x - 0.6, y - 3.0)], fill=(214, 176, 80), outline=(150, 112, 50), lw=0.1)


# ───────────────────────── 소품: 수레 · 화산재 운반선 · 답차 기중기 (탈것 등급 33~41mm) ─────────────────────────
def draw_cart(L, cx, cy):
    """로마 수레(plaustrum): 짐칸, 바퀴 2개, 끌채. 화산재 포대를 싣는다."""
    iso = Iso(L, cx - 10.0, cy - 8.0)
    L.ell(cx + 1, cy + 6.5, 19.0, 5.2, fill=(120, 98, 64, 90))
    iso.box(0, 1.0, 4.2, 20, 11, 5.6, ((196, 150, 100), (176, 130, 84), (146, 106, 66)), ol=(96, 66, 40), lw=0.15)
    for (X, Y) in [(3.0, 3.0), (7.4, 3.2), (11.8, 3.0), (5.2, 7.2), (9.8, 7.0)]:      # 화산재 포대
        iso.box(X, Y, 5.6, X + 3.6, Y + 3.4, 8.6, ((226, 218, 196), (206, 196, 170), (176, 166, 140)), ol=(110, 100, 80), lw=0.12)
    for u0 in (4.0, 14.5):
        pts = [(u0 + 3.6 * math.cos(math.radians(a)), 3.6 + 3.6 * math.sin(math.radians(a))) for a in range(0, 360, 15)]
        iso.fpoly("L", 0, 11.0, 0.0, pts, (150, 108, 68), (80, 56, 34), 0.25)
        px, py = iso.face("L", 0, 11.0, 0.0, [(u0, 3.6)])[0]
        L.ell(px, py, 0.8, 0.7, fill=(90, 66, 40))
    iso.line3([(20, 6.0, 4.6), (31, 6.0, 4.0)], (110, 80, 50), 0.6)
    iso.line3([(30, 3.4, 4.0), (30, 8.6, 4.0)], (110, 80, 50), 0.5)


def draw_ship(L, cx, cy):
    """화산재 운반선(포추올리 → 포르투스): 선체, 돛대, 돛, 포대."""
    iso = Iso(L, cx - 12.0, cy - 9.0)
    L.ell(cx + 1, cy + 7.5, 21.0, 4.0, fill=(70, 110, 150, 100))
    hull = [(0, 2.0, 0), (22, 1.0, 0), (30, 5.5, 0), (22, 10.0, 0), (0, 9.0, 0)]
    iso.poly3([(a, b, 0.0) for a, b, _ in hull], fill=(150, 108, 70), ol=(90, 62, 38), lw=0.2)
    # 선체 측면(+Y쪽 면)
    iso.poly3([(0, 9.0, 0), (22, 10.0, 0), (22, 10.0, 3.6), (0, 9.0, 3.6)], fill=(176, 128, 84), ol=(90, 62, 38), lw=0.2)
    iso.poly3([(22, 10.0, 0), (30, 5.5, 0), (30, 5.5, 3.6), (22, 10.0, 3.6)], fill=(160, 114, 74), ol=(90, 62, 38), lw=0.2)
    iso.poly3([(0, 2.0, 3.6), (22, 1.0, 3.6), (30, 5.5, 3.6), (22, 10.0, 3.6), (0, 9.0, 3.6)], fill=(196, 150, 100), ol=(90, 62, 38), lw=0.2)
    for (X, Y) in [(3, 4), (7.5, 5.0), (12, 4.0), (5, 7.0)]:
        iso.box(X, Y, 3.6, X + 3.4, Y + 2.6, 6.0, ((226, 218, 196), (206, 196, 170), (176, 166, 140)), ol=(110, 100, 80), lw=0.12)
    iso.line3([(15, 5.5, 3.6), (15, 5.5, 20.0)], (110, 80, 50), 0.5)
    iso.fpoly("L", 0, 5.5, 3.6, [(15.4, 3.0), (24.0, 3.0), (24.0, 16.0), (15.4, 16.0)], (248, 244, 230), (150, 130, 98), 0.2)
    iso.fpoly("L", 0, 5.5, 3.6, [(15.4, 9.0), (24.0, 9.0)], None, (200, 180, 150), 0.15)


def draw_crane(L, cx, cy):
    """답차 기중기(treadwheel crane): 나무 틀, 큰 답차 바퀴, 지브와 줄."""
    iso = Iso(L, cx - 10.0, cy - 9.0)
    L.ell(cx + 2, cy + 8.0, 19.0, 4.6, fill=(120, 98, 64, 90))
    iso.box(0, 0, 0, 22, 14, 2.0, ((206, 190, 150), (190, 170, 128), (160, 140, 100)), ol=(110, 90, 60), lw=0.15)
    for (X, Y) in [(3, 11), (19, 11)]:
        iso.line3([(X, Y, 2.0), (X, Y, 22.0)], (126, 92, 56), 1.0)
    iso.line3([(3, 11, 22.0), (19, 11, 22.0)], (126, 92, 56), 0.9)
    pts = [(11 + 7.0 * math.cos(math.radians(a)), 12.2 + 7.0 * math.sin(math.radians(a))) for a in range(0, 360, 12)]
    iso.fpoly("L", 0, 11.0, 0.0, [(11 + 7.2 * math.cos(math.radians(a)), 9.4 + 7.2 * math.sin(math.radians(a))) for a in range(0, 360, 12)], (180, 140, 94), (96, 66, 40), 0.3)
    for a in range(0, 180, 30):
        r = math.radians(a)
        iso.fpoly("L", 0, 11.0, 0.0, [(11 + 7.0 * math.cos(r), 9.4 + 7.0 * math.sin(r)), (11 - 7.0 * math.cos(r), 9.4 - 7.0 * math.sin(r))], None, (96, 66, 40), 0.2)
    iso.line3([(11, 11, 22.0), (27, 11, 26.0)], (126, 92, 56), 0.8)
    iso.line3([(27, 11, 26.0), (27, 11, 12.0)], (110, 98, 84), 0.3)
    iso.box(26, 10, 9.0, 29, 12.5, 12.0, ((226, 218, 196), (206, 196, 170), (176, 166, 140)), ol=(110, 100, 80), lw=0.12)


def draw_bridge(L, cx, cy):
    """돌 아치 다리: 길(↘)이 강(↙)을 건넌다. (cx,cy)는 다리 중심(상판 중앙)의 화면 위치."""
    iso = Iso(L, cx - C30 * (13 - 3.2), cy - 0.5 * (13 + 3.2) + 1.8)
    STONE_B = ((226, 214, 186), (206, 192, 160), (176, 160, 128))
    # 상판(길 색) + 난간
    iso.box(0, 0, 0, 26, 6.4, 1.8, STONE_B, ol=(110, 90, 62), lw=0.18)
    iso.rect3(0, 0.9, 26, 5.5, 1.8, ROAD, ol=ROAD_E, lw=0.12)
    iso.box(0, 0, 1.8, 26, 0.9, 3.0, STONE_B, ol=(110, 90, 62), lw=0.12)
    iso.box(0, 5.5, 1.8, 26, 6.4, 3.0, STONE_B, ol=(110, 90, 62), lw=0.12)
    iso.arch("L", 0, 6.4, 0.0, 7.5, 18.5, 0.0, 0.2, (96, 128, 160), (70, 56, 40), lw=0.1)


def draw_barge(L, cx, cy):
    """테베레 바지선(↙ 방향): 화산재 포대를 실은 긴 배"""
    iso = Iso(L, cx - C30 * (3 - 14), cy - 0.5 * (3 + 14))
    L.ell(cx + 1, cy + 2.5, 15.0, 3.6, fill=(70, 110, 150, 90))
    hull = [(0.4, 0, 0.0), (5.6, 0, 0.0), (6.0, 22, 0.0), (3.0, 29, 0.0), (0.0, 22, 0.0)]
    iso.poly3(hull, fill=(150, 108, 70), ol=(90, 62, 38), lw=0.2)
    iso.poly3([(6.0, 22, 0), (6.0, 22, 3.2), (3.0, 29, 3.2), (3.0, 29, 0)], fill=(160, 114, 74), ol=(90, 62, 38), lw=0.2)
    iso.poly3([(5.6, 0, 0), (6.0, 22, 0), (6.0, 22, 3.2), (5.6, 0, 3.2)], fill=(176, 128, 84), ol=(90, 62, 38), lw=0.2)
    iso.poly3([(0.4, 0, 3.2), (5.6, 0, 3.2), (6.0, 22, 3.2), (3.0, 29, 3.2), (0.0, 22, 3.2)], fill=(196, 150, 100), ol=(90, 62, 38), lw=0.2)
    for (X, Y) in [(0.8, 2.0), (3.0, 5.4), (0.8, 8.8), (3.0, 12.2), (0.8, 15.6)]:
        iso.box(X, Y, 3.2, X + 2.4, Y + 3.0, 5.6, ((226, 218, 196), (206, 196, 170), (176, 166, 140)), ol=(110, 100, 80), lw=0.12)
    iso.line3([(3.0, 22, 3.2), (3.0, 22, 12.0)], (110, 80, 50), 0.4)


# ───────────────────────── 지면: 바다·강·길 ─────────────────────────
RIVER_L2 = None      # 두 번째 구간 길이(계산)
RIVER_L3 = None
SEA_X_LEFT = 108.0
SEA_X_RIGHT = 225.0


def river_params():
    """강 중심선(±30°): 오른쪽 위 → A(직각) → ↘ → B(직각) → ↙ 하구."""
    xb = 215.0
    L2 = (xb - RIVER_A[0]) / C30
    xm = 112.0
    L3 = (xb - xm) / C30
    return L2, L3


def sea_polygon(cl):
    """바다: 강 북쪽 둑선에서 시작해 ↘로 꺾이는 해안선, 좌우는 부두 수직 변"""
    off = (RIVER_W / 2.0) / C30

    def yn(x):
        return cl[-1][1] - off + T30 * (cl[-1][0] - x)

    xl = SEA_X_LEFT
    nb = (xl, yn(xl))
    t = (SEA_X_RIGHT - xl) / C30
    rp = (SEA_X_RIGHT, nb[1] + 0.5 * t)
    return [nb, rp, (SEA_X_RIGHT, MAP_Y1 - 7.0), (xl, MAP_Y1 - 7.0)]


ROADS = []     # 각 길: 중심선 점 목록


def draw_ground(G, cl):
    """바다 → 강 → 길 순으로 지면 레이어에 그린다. 지면 선분은 모두 ±30°."""
    # 지형 결(등각 격자)
    for t in range(-700, 900, 20):
        for sgn in (1, -1):
            G.line([(0, 100 + t), (PW, 100 + t - sgn * PW * T30)], (206, 182, 136, 70), 0.2, joint=False)
    # 강
    poly, lft, rgt = band_poly(cl, RIVER_W, bevel=True)
    G.poly(poly, fill=RIVER, outline=RIVER_T, lw=0.4)
    for a, b in zip(cl[:-1], cl[1:]):
        log_seg("지면", a, b)
        G.dashed(a, b, (232, 244, 252), 0.25, 4.0, 5.0)
    # 바다(강 하구를 덮는다) + 해변 띠
    sea = sea_polygon(cl)
    beach = (244, 232, 200)
    nb_, rp_ = sea[0], sea[1]
    nx, ny = 0.5 * 3.2, -C30 * 3.2
    G.poly([nb_, rp_, (rp_[0] + nx, rp_[1] + ny), (nb_[0] + nx, nb_[1] + ny)], fill=beach)
    G.poly([(sea[0][0] - 3.0, sea[0][1] + 0.5), sea[0], sea[3], (sea[3][0] - 3.0, sea[3][1])], fill=beach)
    G.poly([sea[1], (sea[1][0] + 3.0, sea[1][1] - 0.5), (sea[2][0] + 3.0, sea[2][1]), sea[2]], fill=beach)
    G.poly(sea, fill=SEA, outline=SEA_D, lw=0.6)
    for (xq, sgn) in ((sea[0][0], -1), (sea[1][0], 1)):
        y_a = sea[0][1] if sgn < 0 else sea[1][1]
        G.line([(xq + sgn * 1.4, y_a + 1.0), (xq + sgn * 1.4, sea[3][1])], (150, 130, 98), 0.5, joint=False)
        yq = y_a + 6.0
        while yq < sea[3][1] - 3:
            G.ell(xq + sgn * 1.4, yq, 0.55, 0.45, fill=(120, 100, 72))
            yq += 9.0
    for a, b in zip(sea[:-1], sea[1:]):
        if abs(a[0] - b[0]) > 1e-6 and abs(a[1] - b[1]) > 1e-6:
            log_seg("지면", a, b)
    for i in range(70):
        x = 112 + (i * 29) % 108
        y = 388 + (i * 37) % 104
        if in_poly((x, y), sea):
            G.line([(x, y), (x + 4.0, y + 2.3)], (176, 206, 226), 0.3, joint=False)
            G.line([(x + 4.0, y + 2.3), (x + 6.0, y + 1.1)], (176, 206, 226), 0.3, joint=False)
    # 길: 가장자리색 굵은 띠를 먼저 모두 깔고, 그 위에 길 색 띠를 모두 덮어 교차로의 안쪽 경계선을 없앤다
    for road in ROADS:
        G.poly(band_poly(road, 5.4 + 0.8)[0], fill=ROAD_E)
    for road in ROADS:
        G.poly(band_poly(road, 5.4)[0], fill=ROAD)
    for road in ROADS:
        for a, b in zip(road[:-1], road[1:]):
            log_seg("지면", a, b)
            G.dashed(a, b, (218, 204, 176), 0.22, 2.4, 2.0)


def setup_roads():
    global ROADS
    ROADS = []
    R_ = ARENA_R
    cy_, xl_ = ARENA_CY, ARENA_XL
    cx_ = ARENA_CX
    yb = cy_ + 0.654 * R_                       # 광장 정면 변 y
    F = (cx_ - 12.0, yb)
    ROADS.append(walk(F, [("SE", 170.0)]))                                  # 아피아 가도(오른쪽 액자 밖으로)
    # 공정(6단계) → 다리 → 아레나 광장 남서 변
    q = (78.0 + C30 * 100.0, 340.1 + 0.5 * 100.0)
    yl = cy_ + 0.271 * R_
    ex = (q[1] + T30 * q[0] - yl + T30 * xl_) / (2 * T30)
    ne = (ex - q[0]) / C30
    ROADS.append(walk((78.0, 340.1), [("SE", 100.0), ("NE", ne)]))
    # T자 교차: 위 길의 북동 구간에서 갈라져 수도교 윗 꼭짓점으로
    ax_, ay_, aw_ = SB.POS["aqueduct"]
    top = (ax_, ay_ - aw_ / SQ3 / 2.0)
    # 북동 구간 위의 점 P(t) = q + t·NE 에서 SE로 s만큼 가면 top에 닿는다
    dx, dy = top[0] - q[0], top[1] - q[1]
    t = (dx / C30 - 2.0 * dy) / 2.0
    sl_ = (dx / C30 + 2.0 * dy) / 2.0
    P = (q[0] + C30 * t, q[1] - 0.5 * t)
    ROADS.append(walk(P, [("SE", sl_)]))



# ───────────────────────── 배치 명세 ─────────────────────────
POS = {"vineyard": (398, 486), "field1": (188, 228), "field2": (212, 407), "cart": (107, 355), "ship": (200, 478),
       "crane": (84, 479), "bridge": (133.5, 372.1), "barge": (342.0, 167.0)}


def objects():
    cx_, cy_ = POS["cart"]
    sx_, sy_ = POS["ship"]
    rx_, ry_ = POS["crane"]
    gx, gy = POS["bridge"]
    vx2, vy2 = POS["vineyard"]
    f1x, f1y = POS["field1"]
    f2x, f2y = POS["field2"]
    bgx, bgy = POS["barge"]
    return [
        dict(z=110, name="수레", tier="소품", region=(cx_ - 26, cy_ - 22, cx_ + 26, cy_ + 20), fn=draw_cart, args=(cx_, cy_)),
        dict(z=120, name="화산재 운반선", tier="소품", region=(sx_ - 28, sy_ - 24, sx_ + 28, sy_ + 20), fn=draw_ship, args=(sx_, sy_)),
        dict(z=130, name="답차 기중기", tier="소품", region=(rx_ - 28, ry_ - 28, rx_ + 28, ry_ + 20), fn=draw_crane, args=(rx_, ry_)),
        dict(z=140, name="돌 다리", tier="소품", region=(gx - 22, gy - 16, gx + 22, gy + 16), fn=draw_bridge, args=(gx, gy)),
        dict(z=150, name="포도밭 구획", tier="소품", region=(vx2 - 26, vy2 - 18, vx2 + 26, vy2 + 14), fn=draw_vineyard, args=(vx2, vy2)),
        dict(z=160, name="올리브 과수원", tier="소품", region=(f1x - 26, f1y - 20, f1x + 26, f1y + 18), fn=draw_field, args=(f1x, f1y, "olive")),
        dict(z=170, name="곡식밭", tier="소품", region=(f2x - 26, f2y - 18, f2x + 26, f2y + 16), fn=draw_field, args=(f2x, f2y, "grain")),
        dict(z=180, name="테베레 바지선", tier="소품", region=(bgx - 22, bgy - 22, bgx + 22, bgy + 20), fn=draw_barge, args=(bgx, bgy)),
    ]


def labels():
    return [
        dict(order=120, kind="flag", name="수레", T=(107.0, 353.0), M=M_WALL_DN, col=C_INK, en="CART", ko="수레", side="L", mode="above", pole=12.0),
        dict(order=130, kind="flag", name="화산재 운반선", T=(200.0, 468.0), M=M_WALL_DN, col=C_INK, en="ASH SHIP", ko="화산재 운반선", side="L", mode="above", pole=8.0),
        dict(order=140, kind="flag", name="답차 기중기", T=(84.0, 463.0), M=M_WALL_DN, col=C_INK, en="CRANE", ko="답차 기중기", side="L", mode="above", pole=6.0),
        dict(order=160, kind="flag", name="테베레 바지선", T=(343.0, 163.0), M=M_WALL_UP, col=C_INK, en="BARGE", ko="바지선", side="L", mode="below", pole=10.0),
    ]


def extra_labels(LB):
    """지형명: 바닥에 눕혀 지형색 톤온톤으로(강은 ↗ 기준선, 길·바다는 ↘ 기준선), 지시선 없음"""
    fe3, fk3 = fnt("en", 3.4 / 0.71), fnt("b", 3.2)
    cxr = 372.0
    cyr = RIVER_A[1] - T30 * (cxr - RIVER_A[0])
    floor_line(LB, cxr + 0.82, cyr + 1.43, [("TIBER", fe3, RIVER_T), ("테베레강", fk3, RIVER_T)], M_FLOOR_NE)
    F0 = (ARENA_CX - 12.0, ARENA_CY + 0.654 * ARENA_R)
    cxa = F0[0] + 30.0
    cya = F0[1] + T30 * 30.0
    floor_line(LB, cxa - 0.82, cya + 1.43, [("VIA APPIA", fe3, (126, 106, 76)), ("아피아 가도", fk3, (126, 106, 76))], M_FLOOR_SE)
    draw_floor_name(LB, 178.0, 431.0, "티레니아해", "TYRRHENIAN SEA", (60, 96, 132), kind="SE", em=3.4)
