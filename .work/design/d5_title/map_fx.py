# -*- coding: utf-8 -*-
# 로마 콘크리트 A2 — 중앙 지도 '그림 함수 모듈'(땅 무늬·대지 판석·강 디테일·계단 나루·부두·구릉/화산)
# 기존 파일은 건드리지 않는 새 모듈. 사용: import map_fx ; 좌표는 모두 화면 mm(Layer 좌표).
# 금지 준수: 집·나무·밭·일반 길·사람은 그리지 않는다.
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_LIB = os.path.normpath(os.path.join(_HERE, "..", "..", "lib"))
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)
from prim import *  # noqa: F401,F403  (Layer, Iso, in_poly, lit, tint, newell, h01 ...)
import prim as _prim

GROUND_C = (240, 218, 170)


# ───────────────────────── 공용 보조 ─────────────────────────
def _k(c, f):
    return tuple(max(0, min(255, int(round(v * f)))) for v in c[:3])


def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _unit(v):
    l = math.hypot(v[0], v[1]) or 1.0
    return (v[0] / l, v[1] / l)


def _resample(pts, step):
    """화면 점 목록을 호 길이 step 간격으로 다시 찍는다."""
    out = [tuple(pts[0])]
    carry = 0.0
    for i in range(len(pts) - 1):
        p, q = pts[i], pts[i + 1]
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        if L < 1e-9:
            continue
        t = step - carry
        while t <= L:
            out.append(_lerp(p, q, t / L))
            t += step
        carry = L - (t - step)
    if math.hypot(out[-1][0] - pts[-1][0], out[-1][1] - pts[-1][1]) > step * 0.4:
        out.append(tuple(pts[-1]))
    return out


def _vnormals(pts):
    """꼭짓점별 평균 법선(왼쪽 = 진행방향 기준 화면 y-아래 좌표계의 (dy, -dx))"""
    n = len(pts)
    out = []
    for i in range(n):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        t = _unit((b[0] - a[0], b[1] - a[1]))
        out.append((t[1], -t[0]))
    return out


def _bbox(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return (min(xs), min(ys), max(xs), max(ys))


# ───────────────────────── 1. 땅 무늬 ─────────────────────────
def draw_ground_texture(P, stage_rect, rng, mask_polys=None, ground=GROUND_C, density=1.0):
    """모래색 바닥 위 흙 결·밝은 결·풀 포기 점(땅 무늬). 오브젝트로 읽히지 않게 성기게.
    stage_rect=(x0,y0,x1,y1) mm. rng=random.Random. mask_polys=피할 화면 다각형 목록(건물·강·글 자리).
    10x10mm 칸마다 0~3개(평균 약 1) 뿌린다. 반환: 찍은 개수."""
    x0, y0, x1, y1 = stage_rect
    masks = [(_bbox(m), m) for m in (mask_polys or [])]

    def blocked(pt):
        for bb, m in masks:
            if bb[0] <= pt[0] <= bb[2] and bb[1] <= pt[1] <= bb[3] and in_poly(pt, m):
                return True
        return False

    dirt = _k(ground, 0.935)
    dirt2 = _k(ground, 0.965)
    light = tuple(min(255, int(v * 1.045 + 1)) for v in ground)
    tuft_c = (_k(ground, 0.92)[0] - 14, _k(ground, 0.92)[1] - 2, _k(ground, 0.92)[2] - 24)
    cnt = 0
    cell = 10.0
    gy = y0
    while gy < y1:
        gx = x0
        while gx < x1:
            r = rng.random()
            n = 0 if r < 0.30 else 1 if r < 0.66 else 2 if r < 0.90 else 3
            if density != 1.0 and rng.random() > density:
                n = max(0, n - 1)
            for _ in range(n):
                x = gx + rng.random() * cell
                y = gy + rng.random() * cell
                if x < x0 or x > x1 or y < y0 or y > y1:
                    continue
                kind = rng.random()
                if kind < 0.45:        # 흙 결: 옅은 가로 획
                    ln = 2.4 + rng.random() * 4.2
                    sl = (rng.random() - 0.5) * 0.35
                    a, b = (x - ln / 2, y), (x + ln / 2, y + sl * ln * 0.2)
                    if blocked(a) or blocked(b) or blocked(_lerp(a, b, 0.5)):
                        continue
                    P.line([a, b], dirt if rng.random() < 0.6 else dirt2, 0.22, joint=False)
                    if rng.random() < 0.5:     # 짧은 보조 획(결이 이어지는 느낌)
                        P.line([(b[0] + 1.2, b[1] + 0.35), (b[0] + 1.2 + ln * 0.35, b[1] + 0.35)], dirt2, 0.18, joint=False)
                elif kind < 0.72:      # 밝은 결
                    ln = 2.0 + rng.random() * 3.4
                    a, b = (x - ln / 2, y), (x + ln / 2, y)
                    if blocked(a) or blocked(b):
                        continue
                    P.line([a, b], light, 0.2, joint=False)
                else:                  # 풀 포기 점: 아주 작은 짧은 선 2~3개 묶음
                    if blocked((x, y)):
                        continue
                    m = 2 + (rng.random() < 0.45)
                    for j in range(m):
                        ang = math.radians(-90 + (j - (m - 1) / 2.0) * 38 + (rng.random() - 0.5) * 14)
                        ln = 0.8 + rng.random() * 0.5
                        P.line([(x + (j - 1) * 0.25, y), (x + (j - 1) * 0.25 + math.cos(ang) * ln, y + math.sin(ang) * ln)],
                               tuft_c, 0.14, joint=False)
                cnt += 1
            gx += cell
        gy += cell
    return cnt


# ───────────────────────── 2. 건물 대지 판석 테두리 ─────────────────────────
def _signed_area(poly):
    s = 0.0
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        s += a[0] * b[1] - b[0] * a[1]
    return s / 2.0


def draw_site_plate(P, poly_screen, thickness=1.2, band=1.5, stone=(232, 220, 196), edge=(150, 126, 92)):
    """대지 판석 테두리. poly_screen = 대지 바닥 외곽 화면 다각형(볼록 권장, mm).
    등각 옆면(두께 thickness)을 아래로 달고, 윗면 가장자리에 폭 band 의 판석 띠(줄눈 포함)를 얹는다.
    건물 안쪽은 칠하지 않는다. 반환: 띠 안쪽 다각형(건물 쪽 경계)."""
    poly = [tuple(p) for p in poly_screen]
    if _signed_area(poly) < 0:       # 화면 y-아래 기준 시계 방향으로 통일
        poly = poly[::-1]
    n = len(poly)
    cx = sum(p[0] for p in poly) / n
    cy = sum(p[1] for p in poly) / n
    # 옆면: 바깥 법선이 화면 아래쪽을 향하는 변만 보인다
    for i in range(n):
        p0, p1 = poly[i], poly[(i + 1) % n]
        ex, ey = p1[0] - p0[0], p1[1] - p0[1]
        nx, ny = ey, -ex           # 시계 방향 다각형의 바깥 법선(화면 y-아래)
        l = math.hypot(nx, ny) or 1
        nx, ny = nx / l, ny / l
        mx, my = (p0[0] + p1[0]) / 2 - cx, (p0[1] + p1[1]) / 2 - cy
        if nx * mx + ny * my < 0:
            nx, ny = -nx, -ny
        if ny < 0.12:
            continue
        f = 0.80 if nx < 0 else 0.62
        col = _k(stone, f)
        P.poly([p0, p1, (p1[0], p1[1] + thickness), (p0[0], p0[1] + thickness)], fill=col)
        L = math.hypot(ex, ey)
        nb = max(1, int(round(L / 3.4)))
        for j in range(1, nb):     # 옆면 세로 줄눈
            q = _lerp(p0, p1, j / nb)
            P.line([q, (q[0], q[1] + thickness)], _k(col, 0.82), 0.1, joint=False)
        P.line([(p0[0], p0[1] + thickness), (p1[0], p1[1] + thickness)], _k(stone, 0.46), 0.18, joint=False)
        P.line([p0, (p0[0], p0[1] + thickness)], _k(col, 0.7), 0.12, joint=False)
    # 안쪽 다각형(중심 방향으로 band 만큼 축소: 마이터 오프셋)
    inner = []
    for i in range(n):
        a, b, c = poly[i - 1], poly[i], poly[(i + 1) % n]
        t1 = _unit((b[0] - a[0], b[1] - a[1]))
        t2 = _unit((c[0] - b[0], c[1] - b[1]))
        n1 = (-t1[1], t1[0])
        n2 = (-t2[1], t2[0])
        mx = n1[0] + n2[0]
        my = n1[1] + n2[1]
        dd = (mx * n1[0] + my * n1[1]) or 1.0
        s = band * 2.0 / dd
        q = (b[0] + mx * s / 2.0 * 1.0, b[1] + my * s / 2.0 * 1.0)
        # 안쪽 판정: 중심에 더 가까운 쪽
        q2 = (b[0] - mx * s / 2.0, b[1] - my * s / 2.0)
        inner.append(q if math.hypot(q[0] - cx, q[1] - cy) < math.hypot(q2[0] - cx, q2[1] - cy) else q2)
    for i in range(n):
        j = (i + 1) % n
        quad = [poly[i], poly[j], inner[j], inner[i]]
        ex, ey = poly[j][0] - poly[i][0], poly[j][1] - poly[i][1]
        shade = 1.0 if ey * 0 + abs(ex) >= 0 else 1.0
        P.poly(quad, fill=_k(stone, 1.02 if (i % 2 == 0) else 0.98))
        L = math.hypot(ex, ey)
        nb = max(1, int(round(L / 2.6)))
        for k2 in range(1, nb):    # 판석 줄눈(띠를 가로지르는 짧은 선)
            t = k2 / nb
            a = _lerp(poly[i], poly[j], t)
            b = _lerp(inner[i], inner[j], t)
            P.line([a, b], _k(stone, 0.80), 0.1, joint=False)
    P.line(poly + [poly[0]], edge, 0.2)
    P.line(inner + [inner[0]], _k(stone, 0.78), 0.14)
    return inner


# ───────────────────────── 3. 강 디테일 ─────────────────────────
def _nearest(pt, pts):
    best, bd = pts[0], 1e18
    for q in pts:
        d = (q[0] - pt[0]) ** 2 + (q[1] - pt[1]) ** 2
        if d < bd:
            best, bd = q, d
    return best


def _offset_out(edge, center, d):
    """edge 를 강 밖(중심선 반대)으로 d mm 평행이동한 점 목록(마이터 정규화)"""
    nr = _vnormals(edge)
    out = []
    for p, nv in zip(edge, nr):
        c = _nearest(p, center)
        if (p[0] - c[0]) * nv[0] + (p[1] - c[1]) * nv[1] < 0:
            nv = (-nv[0], -nv[1])
        out.append((p[0] + nv[0] * d, p[1] + nv[1] * d))
    return out


def draw_river_detail(P, left_edge, right_edge, centerline, width_mm, rng, bank_walk=True,
                      wall_h=2.2, walk_w=1.6):
    """이미 그려진 강 면(+옆면 2.2mm) 위에 얹는 디테일.
    · 둑 석축: 보이는 옆면에 돌 블록 2단(줄눈·엇갈림·명암)
    · 둑길: 강 바깥쪽 walk_w mm 폭의 좁은 포장 띠(줄눈 포함, 강의 일부)
    · 물결 무늬: 강 진행 방향 가는 호선(밝은 청색 + 짧은 짙은 청색)
    left_edge/right_edge/centerline = 화면 점 목록(mm), width_mm = 강 폭(14~24). 반환: 물결 선 개수."""
    left = [tuple(p) for p in left_edge]
    right = [tuple(p) for p in right_edge]
    center = _resample([tuple(p) for p in centerline], 1.0)
    poly = left + right[::-1]

    # (a) 둑길: 강 밖 평행 띠 — 석축보다 먼저(물과 겹치지 않음)
    if bank_walk:
        for edge in (left, right):
            e = _resample(edge, 1.3)
            out = _offset_out(e, center, walk_w)
            for i in range(len(e) - 1):
                quad = [e[i], e[i + 1], out[i + 1], out[i]]
                P.poly(quad, fill=(224, 210, 180) if i % 2 == 0 else (218, 203, 172))
                P.line([e[i], out[i]], (186, 166, 132), 0.1, joint=False)      # 판석 줄눈
            P.line(out, (160, 138, 104), 0.16)                                  # 바깥 가장자리
            P.line([(p[0], p[1]) for p in e], (236, 226, 200), 0.12)            # 안쪽 하이라이트

    # (b) 둑 석축 옆면
    for side in (left, right):
        for i in range(len(side) - 1):
            p0, p1 = side[i], side[i + 1]
            if abs(p1[0] - p0[0]) < 0.05:
                continue
            mx, my = (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0
            if not in_poly((mx, my + 0.8), poly):
                continue
            L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            nb = max(1, int(round(L / 2.4)))
            for course in range(2):
                za, zb = wall_h * course / 2.0, wall_h * (course + 1) / 2.0
                shift = 0.5 if course else 0.0
                for j in range(-1 if course else 0, nb + (1 if course else 0)):
                    ta, tb = (j + shift) / nb, (j + 1 + shift) / nb
                    ta, tb = max(0.0, ta), min(1.0, tb)
                    if tb - ta < 1e-3:
                        continue
                    a = _lerp(p0, p1, ta)
                    b = _lerp(p0, p1, tb)
                    base = (150, 124, 88)
                    f = 0.92 + 0.14 * h01("석축", round(a[0], 1), round(a[1], 1), course)
                    f *= 1.0 - 0.07 * course
                    P.poly([(a[0], a[1] + za), (b[0], b[1] + za), (b[0], b[1] + zb), (a[0], a[1] + zb)],
                           fill=_k(base, f), outline=_k(base, 0.72), lw=0.09)
            P.line([(p0[0], p0[1] + wall_h), (p1[0], p1[1] + wall_h)], (96, 140, 180), 0.25, joint=False)
            P.line([p0, p1], (232, 222, 196), 0.18, joint=False)               # 석축 윗모서리 하이라이트

    # (c) 물결 무늬
    L = 0.0
    for i in range(len(center) - 1):
        L += math.hypot(center[i + 1][0] - center[i][0], center[i + 1][1] - center[i][1])
    nrm = _vnormals(center)
    n_lines = 0
    n_try = int(L / 9.0 * 3.2)
    for _ in range(n_try):
        s0 = rng.randint(0, max(1, len(center) - 14))
        ln = rng.randint(5, 11)
        d = (rng.random() * 2 - 1) * width_mm * 0.34
        ph = rng.random() * 6.28
        amp = 0.16 + 0.12 * rng.random()
        pts = []
        ok = True
        for k in range(ln):
            idx = min(len(center) - 1, s0 + k)
            c, nv = center[idx], nrm[idx]
            dd = d + amp * math.sin(ph + k * 0.9)
            q = (c[0] + nv[0] * dd, c[1] + nv[1] * dd)
            if not in_poly((q[0], q[1] + wall_h * 0.5), poly) or not in_poly(q, poly):
                ok = False
                break
            pts.append(q)
        if not ok or len(pts) < 3:
            continue
        if rng.random() < 0.75:
            P.line(pts, (176, 214, 238), 0.2, joint=True)
        else:
            P.line(pts, (92, 146, 192), 0.16, joint=True)
        n_lines += 1
    return n_lines


def draw_steps(P, pt, direction, width=5.0, n=4, tread=0.95):
    """계단 나루. pt = 둑 가장자리의 계단 시작점(화면 mm), direction = 땅에서 물로 내려가는 화면 방향 벡터.
    폭 width mm, n단, 단 깊이 tread mm. 양쪽에 낮은 석축 뺨벽."""
    d = _unit(direction)
    pv = (-d[1], d[0])
    hw = width / 2.0
    # 뺨벽(양옆)
    for sgn in (-1, 1):
        a = (pt[0] + pv[0] * hw * sgn, pt[1] + pv[1] * hw * sgn)
        b = (a[0] + d[0] * tread * n, a[1] + d[1] * tread * n)
        out = (0.7 * sgn * pv[0], 0.7 * sgn * pv[1])
        P.poly([a, b, (b[0] + out[0], b[1] + out[1] + 0.8), (a[0] + out[0], a[1] + out[1] + 0.8)], fill=(146, 120, 86))
        P.line([a, b], (232, 222, 196), 0.16, joint=False)
    for k in range(n):
        a0 = (pt[0] + d[0] * tread * k, pt[1] + d[1] * tread * k)
        a1 = (pt[0] + d[0] * tread * (k + 1), pt[1] + d[1] * tread * (k + 1))
        quad = [(a0[0] - pv[0] * hw, a0[1] - pv[1] * hw), (a0[0] + pv[0] * hw, a0[1] + pv[1] * hw),
                (a1[0] + pv[0] * hw, a1[1] + pv[1] * hw), (a1[0] - pv[0] * hw, a1[1] - pv[1] * hw)]
        wet = k / float(max(1, n - 1))            # 아래 단일수록 물빛이 섞인다
        base = (232, 220, 196)
        col = tuple(int(base[i] * (1 - 0.28 * wet) + (112, 170, 210)[i] * 0.28 * wet) for i in range(3))
        P.poly(quad, fill=_k(col, 1.0 if k % 2 == 0 else 0.93))
        P.line([quad[0], quad[1]], (176, 154, 118), 0.14, joint=False)        # 단 모서리(챌판 그림자)
        P.line([quad[0], quad[1]], (246, 238, 218), 0.07, joint=False)


def draw_quay(P, p0, p1, depth, toward=None, face_h=1.6, piles=True):
    """부두. p0→p1 = 둑에 붙는 변(화면 mm), depth = 물 쪽으로 내민 길이(화면 mm).
    toward = 물 쪽 단위벡터(생략하면 변에 수직이면서 화면 아래를 향하는 쪽). 윗면 판석 + 앞 단면 석재 + 말뚝 줄."""
    ex, ey = p1[0] - p0[0], p1[1] - p0[1]
    if toward is None:
        nv = _unit((ey, -ex))
        if nv[1] < 0:
            nv = (-nv[0], -nv[1])
    else:
        nv = _unit(toward)
    q0 = (p0[0] + nv[0] * depth, p0[1] + nv[1] * depth)
    q1 = (p1[0] + nv[0] * depth, p1[1] + nv[1] * depth)
    L = math.hypot(ex, ey)
    # 말뚝(앞단 바깥, 물속에서 솟은 줄)
    if piles:
        npile = max(2, int(L / 1.8))
        for i in range(npile + 1):
            q = _lerp(q0, q1, i / npile)
            y0 = q[1] + face_h
            P.rect(q[0] - 0.22, y0, q[0] + 0.22, y0 + 1.3, fill=(98, 74, 48))
            P.rect(q[0] - 0.22, y0 + 1.3, q[0] + 0.22, y0 + 1.5, fill=(96, 140, 180))
            P.ell(q[0], y0, 0.3, 0.16, fill=(132, 104, 72))
    # 앞 단면(+y 방향 두께)
    P.poly([q0, q1, (q1[0], q1[1] + face_h), (q0[0], q0[1] + face_h)], fill=(166, 146, 112))
    nb = max(1, int(L / 2.5))
    for j in range(nb):
        a = _lerp(q0, q1, j / nb)
        b = _lerp(q0, q1, (j + 1) / nb)
        f = 0.94 + 0.12 * h01("부두", round(a[0], 1), round(a[1], 1))
        P.poly([(a[0], a[1] + face_h * 0.5), (b[0], b[1] + face_h * 0.5), (b[0], b[1] + face_h), (a[0], a[1] + face_h)],
               fill=_k((166, 146, 112), f), outline=(116, 96, 68), lw=0.08)
        P.poly([a, b, (b[0], b[1] + face_h * 0.5), (a[0], a[1] + face_h * 0.5)],
               fill=_k((176, 156, 122), 2 - f if f > 1 else 1.0), outline=(116, 96, 68), lw=0.08)
    # 윗면 판석
    P.poly([p0, p1, q1, q0], fill=(228, 216, 190))
    nrow = max(2, int(depth / 1.8))
    for r in range(1, nrow):
        a = _lerp(p0, q0, r / nrow)
        b = _lerp(p1, q1, r / nrow)
        P.line([a, b], (194, 176, 142), 0.09, joint=False)
    nc = max(1, int(L / 2.4))
    for c in range(1, nc):
        a = _lerp(p0, p1, c / nc)
        b = _lerp(q0, q1, c / nc)
        P.line([a, b], (200, 182, 148), 0.07, joint=False)
    P.line([q0, q1], (244, 236, 214), 0.18, joint=False)
    P.line([p0, q0, q1, p1], (140, 116, 82), 0.14)
    return [p0, p1, q1, q0]


# ───────────────────────── 4. 구릉·화산(진짜 등각 지형) ─────────────────────────
def _hill_height(kind, u, v, a, b, H, rng_seed):
    """로컬 (u,v) 지형 높이(평면 mm). u 긴 축."""
    eu, ev = u / a, v / b                           # -1..1
    edge = max(0.0, 1.0 - (max(abs(eu), abs(ev)) ** 6))   # 가장자리에서 0으로 내려가는 포락선
    if kind == "albano":
        centers = [(-0.70, 0.78), (-0.25, 1.0), (0.22, 0.88), (0.68, 0.72)]      # 능선 4개(위치, 상대 높이)
        pk = 0.0
        for k, (cu, ch) in enumerate(centers):
            pk += ch * math.exp(-((eu - cu) / 0.21) ** 2)
        prof = 0.22 + 0.78 * min(1.0, pk)                      # 능선이 이어지는 산마루(안장은 40%까지만 내려감)
        sv = 0.44
        vc = 0.10 * math.sin(eu * 3.1 + 0.4)
        z = prof * math.exp(-((ev - vc) / sv) ** 2)
        z *= 1.0 + 0.08 * math.sin(eu * 11.0 + 1.0) * math.cos(ev * 5.0)
        return H * min(1.0, z) * edge ** 0.5
    # 베수비오: 원뿔 + 분화구(잘린 원뿔 꼭대기에 움푹한 구덩이)
    r = math.hypot(eu, ev)
    rim = 0.30

    def cone(rr):
        return max(0.0, 1.0 - rr / 0.95) ** 0.85
    if r >= rim:
        z = H * cone(r) / cone(rim)
    else:
        z = H * (1.0 - 0.24 * (1.0 - (r / rim) ** 2))
    z *= 1.0 + 0.04 * math.sin(math.atan2(ev, eu) * 7.0 + 0.6) * min(1.0, r * 2)       # 골짜기 결
    return z * edge ** 0.4


def draw_hills(P, name, anchor, rng, axis_deg=0.0, scale=1.0, size=None):
    """구릉/화산을 진짜 등각(±30°)으로 그린다. name = 'albano'(능선 4개 산맥) | 'vesuvio'(원뿔+분화구).
    anchor = 받침 윗면 중심의 화면 점(mm), axis_deg = 긴 축 회전(0이면 긴 축이 화면 가로,
    +면 평면에서 반시계로 돌려 ↘ 방향 쪽), scale = 전체 배율, size=(화면폭, 높이) 직접 지정.
    기본 크기: albano 화면폭 34 × 총높이 26, vesuvio 화면폭 30 × 총높이 24 (mm, scale 곱).
    색: 윗면(밝음)·왼면(+Y)·오른면(+X) 3단(램버트), 먼 지형이라 연한 색.
    반환: 투영 상자 dict(Blender 맞춤용: 'screen_box', 'base_screen', 'plan': center/size/yaw/height_mm)."""
    kind = "albano" if name.lower().startswith("alb") else "vesuvio"
    W, TOT = size if size else ((34.0, 26.0) if kind == "albano" else (30.0, 24.0))
    W *= scale
    TOT *= scale
    skirt = 1.7 * scale
    # 평면 회전: 기본 yaw -22°(albano) → 긴 축이 화면에서 약 14° 기울어 거의 가로, 왼면·오른면 둘 다 보인다
    yaw = math.radians((-22.0 if kind == "albano" else -30.0) + axis_deg)
    cu, su = math.cos(yaw), math.sin(yaw)
    ratio = 0.50 if kind == "albano" else 1.0

    def _proj(u, v):
        X, Y = u * cu - v * su, u * su + v * cu
        return (C30 * (X - Y), 0.5 * (X + Y))

    cs = [_proj(-1, -ratio), _proj(1, -ratio), _proj(1, ratio), _proj(-1, ratio)]
    wx = max(c[0] for c in cs) - min(c[0] for c in cs)
    hy = max(c[1] for c in cs) - min(c[1] for c in cs)
    a = W / wx
    b = a * ratio
    base_h = hy * a
    H = max(4.0, TOT - skirt - base_h / 2.0)
    iso = Iso(P, anchor[0], anchor[1])
    # 지형 격자
    cell = 1.15 * scale
    nu = max(8, int(round(2 * a / cell)))
    nv = max(6, int(round(2 * b / cell)))

    def to_plan(u, v):
        return (u * cu - v * su, u * su + v * cu)

    grid = []
    for i in range(nu + 1):
        row = []
        for j in range(nv + 1):
            u = -a + 2 * a * i / nu
            v = -b + 2 * b * j / nv
            z = _hill_height(kind, u, v, a, b, H, 0)
            row.append((u, v, z))
        grid.append(row)
    if kind == "albano":
        soil_top, grass_lo, grass_hi, rock = (170, 182, 128), (150, 172, 112), (190, 190, 134), (176, 168, 146)
    else:
        soil_top, grass_lo, grass_hi, rock = (172, 160, 128), (148, 160, 108), (186, 166, 130), (150, 138, 120)
    soil_side = (176, 150, 112)

    def colfun(z, zr):
        t = max(0.0, min(1.0, z / H))
        if kind == "vesuvio":
            if t > 0.78:
                c = (160, 140, 120)
            elif t > 0.5:
                tt = (t - 0.5) / 0.28
                c = tuple(grass_hi[i] * (1 - tt) + (160, 140, 120)[i] * tt for i in range(3))
            else:
                c = tuple(grass_lo[i] * (1 - t * 2) + grass_hi[i] * t * 2 for i in range(3))
        else:
            c = tuple(grass_lo[i] * (1 - t) + grass_hi[i] * t for i in range(3))
        return tuple(int(v) for v in c)

    faces = []      # (depth, pts3, fill, tri_id)
    nlev = 4 if kind == "albano" else 5
    levels = [H * (k + 1) / (nlev + 1) for k in range(nlev)]

    def tri(p, q, r, key):
        pts = [to_plan(*p[:2]) + (p[2] + skirt,), to_plan(*q[:2]) + (q[2] + skirt,), to_plan(*r[:2]) + (r[2] + skirt,)]
        n = newell(pts)
        if n[2] < 0:
            pts = pts[::-1]
            n = (-n[0], -n[1], -n[2])
        zc = (p[2] + q[2] + r[2]) / 3.0
        # 등고 띠: 높이 구간마다 색 명도를 살짝 단계 변화
        band = sum(1 for lv in levels if zc > lv)
        base = colfun(zc, H)
        base = _k(base, 1.0 + 0.035 * (band % 2) - 0.02)
        fill = lit(base, n, 0.03, key)
        c = (sum(x[0] for x in pts) / 3, sum(x[1] for x in pts) / 3, sum(x[2] for x in pts) / 3)
        faces.append([c[0] + c[1] + c[2], pts, fill, (p[2], q[2], r[2]), band])

    for i in range(nu):
        for j in range(nv):
            A, B_, C_, D = grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]
            if (i + j) % 2 == 0:
                tri(A, B_, C_, (i, j, 0, kind))
                tri(A, C_, D, (i, j, 1, kind))
            else:
                tri(A, B_, D, (i, j, 2, kind))
                tri(B_, C_, D, (i, j, 3, kind))
    # 받침 옆면(보이는 것만): 경계를 따라 사각 띠
    def edge_pts(side):
        if side == 0:
            return [grid[i][0] for i in range(nu + 1)], (0, -1)
        if side == 1:
            return [grid[nu][j] for j in range(nv + 1)], (1, 0)
        if side == 2:
            return [grid[i][nv] for i in range(nu + 1)][::-1], (0, 1)
        return [grid[0][j] for j in range(nv + 1)][::-1], (-1, 0)

    for side in range(4):
        ep, nl = edge_pts(side)
        npl = (nl[0] * cu - nl[1] * su, nl[0] * su + nl[1] * cu)           # 바깥 법선(평면)
        if npl[0] + npl[1] <= 1e-6:
            continue
        fnorm = (npl[0], npl[1], 0.0)
        for k in range(len(ep) - 1):
            p, q = ep[k], ep[k + 1]
            pp, qq = to_plan(p[0], p[1]), to_plan(q[0], q[1])
            pts = [(pp[0], pp[1], 0.0), (qq[0], qq[1], 0.0), (qq[0], qq[1], q[2] + skirt), (pp[0], pp[1], p[2] + skirt)]
            fill = lit(soil_side, fnorm, 0.02, (side, k, kind))
            c = (sum(x[0] for x in pts) / 4, sum(x[1] for x in pts) / 4, sum(x[2] for x in pts) / 4)
            faces.append([c[0] + c[1] + c[2] - 0.5, pts, fill, None, -1])
    faces.sort(key=lambda f: f[0])
    # 그리기(+ 등고선·암석 점을 면 바로 뒤에 그려 가려짐을 자연스럽게)
    for dep, pts, fill, zs, band in faces:
        iso.poly3(pts, fill=fill, ol=fill, lw=0.12)
        if zs is None:
            continue
        # 등고선: 면과 높이 level 이 만나는 선분
        for lv in levels:
            Z = [p[2] - skirt for p in pts]
            cr = []
            for k in range(3):
                z0_, z1_ = Z[k], Z[(k + 1) % 3]
                if (z0_ - lv) * (z1_ - lv) < 0:
                    t = (lv - z0_) / (z1_ - z0_)
                    pa, pb = pts[k], pts[(k + 1) % 3]
                    cr.append(tuple(pa[m] + (pb[m] - pa[m]) * t for m in range(3)))
            if len(cr) == 2:
                iso.line3(cr, _k(fill, 0.80), 0.14)
    # 암석 점(작은 바위): 면 중심 근처
    rr = _prim.local_rng("rock-" + name)
    cand = [f for f in faces if f[3] is not None and f[4] >= 1]
    for f in cand:
        if rr.random() > 0.045:
            continue
        pts = f[1]
        c = (sum(x[0] for x in pts) / 3, sum(x[1] for x in pts) / 3, sum(x[2] for x in pts) / 3)
        sx, sy = iso.p(*c)
        s = 0.35 + 0.3 * rr.random()
        P.poly([(sx - s, sy + s * 0.5), (sx - s * 0.3, sy - s * 0.6), (sx + s, sy - s * 0.1), (sx + s * 0.5, sy + s * 0.6)],
               fill=_k(rock, 0.95))
        P.poly([(sx - s * 0.3, sy - s * 0.6), (sx + s, sy - s * 0.1), (sx + s * 0.2, sy + s * 0.1)], fill=_k(rock, 1.12))
    # 분화구 안 어두운 면은 이미 낮은 높이 음영으로 표현됨
    # 투영 상자
    allp = []
    corner_plan = [to_plan(-a, -b), to_plan(a, -b), to_plan(a, b), to_plan(-a, b)]
    base_scr = [iso.p(x, y, 0.0) for x, y in corner_plan]
    for f in faces:
        for q in f[1]:
            allp.append(iso.p(*q))
    bx0, by0, bx1, by1 = _bbox(allp + base_scr)
    return {
        "name": kind, "screen_box": (bx0, by0, bx1, by1), "base_screen": base_scr,
        "plan": {"center_screen_anchor": anchor, "half_u": a, "half_v": b, "yaw_deg": math.degrees(yaw),
                 "height_mm": H + skirt, "skirt_mm": skirt, "size_plan_mm": (2 * a, 2 * b, H + skirt)},
    }
