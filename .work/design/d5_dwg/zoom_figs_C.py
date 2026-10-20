# -*- coding: utf-8 -*-
"""확대 창 그림 C: 하드리아누스 영묘 드럼 단면 · 카이킬리아 메텔라 드럼 재결속 · 포르투스 방파제 단면
시그니처 fig_<키>(sub, vc, vr, rng). sub = Layer(0,0,62,62) 가상 판(mm), 중심 (vc,vc) 반지름 vr 원 안에 그린다.
근거: docs/research/Basic-대체-정보-추가-건축물-조사-2026-10-19.md A2(영묘),
      docs/research/화산-Support-사례-조사-2026-10-18.md B16(메텔라, Seymour 2021)·B20(코사, Jackson 2017)·B-3 포르투스 표.
"""
import math
import sys
sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/lib")
from common import shade, mix  # noqa: E402

SKY = (238, 228, 202)
MORT = (204, 192, 174)
MORT_D = (178, 166, 148)
MARB = (246, 244, 236)
MARB_D = (222, 218, 206)
TRAVC = (232, 220, 196)
TRAVC_D = (206, 192, 160)
BRK = (184, 111, 76)
TUF = (168, 149, 122)
SOILC = [(150, 118, 80), (128, 98, 62), (112, 86, 56)]
TURF = (118, 144, 78)
SEAC = (146, 182, 208)
SEAC_D = (104, 142, 172)
SEAC_L = (236, 246, 252)
CONC = (166, 160, 148)
INKC = (58, 42, 28)
AGG = [(168, 149, 122), (184, 111, 76), (150, 146, 138), (112, 94, 84), (196, 160, 118), (232, 220, 196)]


def _blob(rng, cx, cy, r, n=None, sq=0.85):
    n = n or (5 + int(rng.random() * 3))
    ph = rng.random() * 6.28
    pts = []
    for j in range(n):
        t = ph + 2 * math.pi * j / n + (rng.random() - 0.5) * 0.5
        q = r * (0.75 + rng.random() * 0.4)
        pts.append((cx + q * math.cos(t), cy + q * sq * math.sin(t)))
    return pts


def clast(sub, rng, cx, cy, r, col, sq=0.85):
    """골재 알갱이: 중간 면 + 어두운 아랫면 + 밝은 윗면(3단)"""
    p = _blob(rng, cx, cy, r, sq=sq)
    sub.poly(p, fill=col)
    n = len(p)
    low = [(x + 0.0, y) for x, y in p if y >= cy - r * 0.05]
    if len(low) >= 3:
        sub.poly(low, fill=shade(col, 0.82))
    hi = [(x, y) for x, y in p if y < cy - r * 0.2]
    if len(hi) >= 3:
        sub.poly(hi + [(cx, cy - r * 0.1)], fill=shade(col, 1.12))
    if r > 1.0:
        sub.line([p[0], p[1], p[2]] if n > 2 else p, shade(col, 0.7), 0.25, joint=False)


def half_ell(cx, cy, rx, ry, n=40, down=False):
    sg = 1 if down else -1
    return [(cx - rx * math.cos(math.pi * i / n), cy + sg * ry * math.sin(math.pi * i / n)) for i in range(n + 1)]


def hexa(sub, x, y, r, col, dark=None):
    pts = [(x + r * math.cos(math.radians(60 * k + 30)), y + r * 0.9 * math.sin(math.radians(60 * k + 30))) for k in range(6)]
    sub.poly(pts, fill=col)
    if dark:
        sub.poly([pts[0], pts[1], pts[2], (x, y)], fill=dark)


# ───────────────────────── 1. 하드리아누스 영묘 드럼 단면 ─────────────────────────
def fig_mausoleum(sub, vc, vr, rng):
    sub.rect(-2, -2, 64, 64, fill=SKY)
    # 땅 지층(아래)
    y = 53.0
    for h, c in [(2.6, SOILC[0]), (2.6, SOILC[1]), (8.0, SOILC[2])]:
        sub.rect(-2, y, 64, y + h, fill=c)
        y += h
    for i in range(22):
        sub.ell(rng.random() * 62, 54 + rng.random() * 8, 0.45, 0.35, fill=shade(SOILC[1], 0.8 + 0.3 * rng.random()))
    # 기단: 겉 트래버틴, 속 벽돌(사각 기단 단면)
    sub.rect(1, 46, 61, 53, fill=BRK)
    for k in range(4):
        yy = 46 + k * 1.75
        sub.line([(1, yy), (61, yy)], shade(BRK, 0.78), 0.25, joint=False)
    for k in range(4):
        for xx in range(int(4 + (k % 2) * 3), 58, 6):
            sub.line([(xx, 46 + k * 1.75), (xx, 47.75 + k * 1.75)], shade(BRK, 0.78), 0.25, joint=False)
    for (xa, xb) in [(1, 4.8), (57.2, 61)]:
        sub.rect(xa, 46, xb, 53, fill=TRAVC)
        for k in range(3):
            sub.line([(xa, 48.3 + k * 2.3), (xb, 48.3 + k * 2.3)], TRAVC_D, 0.3, joint=False)
    sub.rect(1, 52.2, 61, 53, fill=shade(BRK, 0.82))
    # 드럼: 속 콘크리트
    X0, X1, Y0, Y1 = 7.0, 55.0, 21.0, 46.0
    sub.rect(X0, Y0, X1, Y1, fill=MORT)
    lifts = [Y0, 27.0, 33.2, 39.4, Y1]
    for i in range(4):
        ya, yb = lifts[i], lifts[i + 1]
        sub.rect(X0 + 4.6, ya, X1 - 4.6, yb, fill=shade(MORT, 1.04 if i % 2 else 0.97))
    for i in range(1, 4):
        sub.line([(X0 + 4.6, lifts[i]), (X1 - 4.6, lifts[i])], MORT_D, 0.3, joint=False)
    for i in range(4):
        ya, yb = lifts[i], lifts[i + 1]
        for _ in range(17):
            x = X0 + 6.4 + rng.random() * (X1 - X0 - 12.8)
            yy = ya + 1.3 + rng.random() * (yb - ya - 2.6)
            if 28.4 < x < 34 and yy > 37:
                continue
            clast(sub, rng, x, yy, 1.3 + rng.random() * 1.5, AGG[int(rng.random() * 6)])
    for _ in range(60):
        x = X0 + 5 + rng.random() * (X1 - X0 - 10)
        yy = Y0 + 0.7 + rng.random() * (Y1 - Y0 - 1.4)
        sub.ell(x, yy, 0.28, 0.22, fill=MORT_D)
    # 통로 하나(거의 속이 찬 콘크리트에 뚫린 통로)
    sub.poly([(29.0, 46), (29.0, 40.4), (29.9, 38.9), (33.1, 38.9), (34.0, 40.4), (34.0, 46)], fill=(74, 60, 50))
    sub.poly([(29.0, 46), (29.0, 40.4), (29.9, 38.9), (30.8, 38.9), (30.8, 46)], fill=(52, 42, 34))
    # 겉 대리석 판
    for (xa, xb, d) in [(X0, X0 + 4.6, 1), (X1 - 4.6, X1, -1)]:
        sub.rect(xa, Y0, xb, Y1, fill=MARB)
        yy = Y0
        k = 0
        while yy < Y1 - 0.1:
            hh = min(3.1, Y1 - yy)
            sub.rect(xa, yy, xb, yy + hh, fill=MARB if k % 2 else shade(MARB, 0.97))
            sub.rect(xa + (0 if d > 0 else 2.6), yy + 0.0, xa + (1.9 if d > 0 else 4.6), yy + hh, fill=MARB_D)
            sub.line([(xa, yy), (xb, yy)], (186, 180, 164), 0.3, joint=False)
            yy += 3.1
            k += 1
        # 대리석과 속 사이 맞닿은 선
        xe = xb if d > 0 else xa
        sub.line([(xe, Y0), (xe, Y1)], (170, 164, 150), 0.35, joint=False)
    # 꼭대기 돌림띠
    sub.rect(5.4, 18.8, 56.6, 21.0, fill=MARB)
    sub.rect(5.4, 20.1, 56.6, 21.0, fill=MARB_D)
    # 위쪽 둔덕(흙)
    cx = 31.0
    sub.poly(half_ell(cx, 18.8, 23.0, 9.2), fill=TURF)
    sub.poly(half_ell(cx, 18.8, 22.2, 8.0), fill=SOILC[0])
    sub.poly(half_ell(cx, 18.8, 21.2, 5.2), fill=SOILC[1])
    sub.poly(half_ell(cx, 18.8, 20.4, 2.6), fill=SOILC[2])
    for _ in range(26):
        t = rng.random() * math.pi
        rr = rng.random() ** 0.5
        x = cx - 20 * rr * math.cos(t)
        yy = 18.5 - 7.0 * rr * math.sin(t)
        sub.ell(x, yy, 0.4, 0.3, fill=shade(SOILC[1], 0.78 + 0.5 * rng.random()))
    # 둔덕 위 풀 점
    for i in range(14):
        t = math.pi * (i + 0.5) / 14
        sub.ell(cx - 22.6 * math.cos(t) * 0.97, 18.8 - 9.0 * math.sin(t), 0.55, 0.4, fill=shade(TURF, 1.18))


# ───────────────────────── 2. 카이킬리아 메텔라 드럼 재결속 ─────────────────────────
def _drop(sub, x, y, s=1.0):
    sub.poly([(x, y - 1.5 * s), (x + 0.85 * s, y + 0.1 * s), (x, y + 1.0 * s), (x - 0.85 * s, y + 0.1 * s)], fill=(70, 140, 200))
    sub.ell(x - 0.2 * s, y + 0.2 * s, 0.22 * s, 0.3 * s, fill=(190, 224, 246))


def _micro(sub, rng, x, y, s, stage):
    """미시 도해 한 칸: 알갱이 사이 접합부. 1 = 젖어서 류사이트 결정이 녹고 틈이 열림, 2 = 틈에 새 결정이 다시 짜임"""
    sub.rect(x - 0.3, y - 0.3, x + s + 0.3, y + s + 0.3, fill=INKC)
    sub.rect(x, y, x + s, y + s, fill=MORT)
    # 접합부(가운데 세로 띠)
    gx0, gx1 = x + 0.42 * s, x + 0.58 * s
    # 알갱이 A(왼쪽)·B(오른쪽): 응회암 회갈색
    def grain(x0, x1, left):
        pts = [(x0, y + 0.05 * s), (x1, y + 0.05 * s), (x1 + (0.015 if left else -0.015) * s, y + 0.3 * s), (x1, y + 0.55 * s),
               (x1 + (-0.01 if left else 0.012) * s, y + 0.8 * s), (x1, y + 0.95 * s), (x0, y + 0.95 * s)]
        sub.poly(pts, fill=TUF)
        sub.poly([(x0, y + 0.62 * s), (x1, y + 0.62 * s), (x1, y + 0.95 * s), (x0, y + 0.95 * s)], fill=shade(TUF, 0.84))
        sub.poly([(x0, y + 0.05 * s), (x1, y + 0.05 * s), (x1, y + 0.2 * s), (x0, y + 0.2 * s)], fill=shade(TUF, 1.1))
    grain(x + 0.04 * s, gx0, True)
    grain(gx1, x + 0.96 * s, False)
    # 류사이트 결정(육각 다면체 모식)
    sites = [(0.17, 0.3), (0.3, 0.7), (0.72, 0.35), (0.84, 0.76)]
    for k, (fx, fy) in enumerate(sites):
        px, py = x + fx * s, y + fy * s
        if stage == 1:
            hexa(sub, px, py, 0.125 * s, MARB, MARB_D)
            # 녹아 나간 흔적
        else:
            hexa(sub, px, py, 0.07 * s, shade(TUF, 1.22), shade(TUF, 0.95))
    if stage == 1:
        # 열린 틈(어두움) + 물방울 + 녹아 나온 알갱이
        gp = [(gx0, y), (gx1, y), (gx1 - 0.02 * s, y + 0.35 * s), (gx1 + 0.015 * s, y + 0.7 * s), (gx1, y + s), (gx0, y + s),
              (gx0 + 0.02 * s, y + 0.65 * s), (gx0 - 0.015 * s, y + 0.3 * s)]
        sub.poly(gp, fill=(84, 70, 60))
        for k, fy in enumerate([0.12, 0.3, 0.52, 0.76]):
            _drop(sub, x + 0.5 * s + (0.03 if k % 2 else -0.03) * s, y + fy * s, 0.9)
        for k in range(7):
            a = k * 0.93
            sub.ell(x + 0.5 * s + 0.1 * s * math.cos(a), y + (0.2 + 0.1 * k) * s, 0.22, 0.22, fill=MARB)
        # 결정에서 틈으로 나오는 이온 점선
        for (fx, fy) in sites[:2]:
            px, py = x + fx * s, y + fy * s
            for u in range(1, 4):
                sub.ell(px + (gx0 - px) * u / 4.0, py + (0.5 * s + y - py) * 0 + (0.3 * s * (u / 4.0) * (1 if fy < 0.5 else -1)) * 0.2, 0.2, 0.2, fill=(190, 224, 246))
    else:
        # 새 결정이 틈을 가로질러 짜임: 바늘/판
        sub.rect(gx0, y, gx1, y + s, fill=shade(MORT, 1.06))
        for k in range(15):
            fy = 0.04 + 0.92 * k / 14.0
            a = (0.28 if k % 2 else -0.28) + (rng.random() - 0.5) * 0.3
            x0_, y0_ = gx0 - 0.04 * s, y + fy * s
            x1_, y1_ = gx1 + 0.04 * s, y0_ + (gx1 - gx0 + 0.08 * s) * math.tan(a)
            sub.line([(x0_, y0_), (x1_, y1_)], MARB, 0.45, joint=False)
            sub.line([(x0_ + 0.3, y0_ + 0.3), (x1_ + 0.3, y1_ + 0.3)], MARB_D, 0.2, joint=False)
        for k in range(5):
            hexa(sub, x + 0.5 * s + (rng.random() - 0.5) * 0.08 * s, y + (0.1 + 0.19 * k) * s, 0.04 * s, MARB, MARB_D)


def fig_metella(sub, vc, vr, rng):
    sub.rect(-2, -2, 64, 64, fill=SKY)
    # 배경 아래쪽(미시 도해 면)을 약간 어둡게 구분
    sub.poly(half_ell(31, 33.5, 40, 12, down=True) + [(-9, 33.5)], fill=shade(SKY, 0.96))
    sub.rect(-2, 33.5, 64, 64, fill=shade(SKY, 0.95))
    # 드럼 평면 단면(위): 벽돌 겉 · 콘크리트 · 응회암 보강
    dx, dy, R = 31.0, 15.5, 12.4
    sub.ell(dx, dy, R, R, fill=shade(BRK, 0.8))
    sub.ell(dx, dy, R - 0.25, R - 0.25, fill=BRK)
    for k in range(48):
        a = math.radians(k * 7.5)
        sub.line([(dx + (R - 1.35) * math.cos(a), dy + (R - 1.35) * math.sin(a)), (dx + (R - 0.2) * math.cos(a), dy + (R - 0.2) * math.sin(a))], shade(BRK, 0.74), 0.22, joint=False)
    sub.ell(dx, dy, R - 1.4, R - 1.4, fill=shade(BRK, 0.86))
    sub.ell(dx, dy, R - 1.6, R - 1.6, fill=CONC)
    for k in range(14):
        a = math.radians(k * 360 / 14 + 6)
        px, py = dx + (R - 3.4) * math.cos(a), dy + (R - 3.4) * math.sin(a)
        sub.rect(px - 0.9, py - 0.7, px + 0.9, py + 0.7, fill=TUF)
        sub.rect(px - 0.9, py + 0.1, px + 0.9, py + 0.7, fill=shade(TUF, 0.84))
    sub.ell(dx, dy, R - 5.0, R - 5.0, fill=MORT)
    for k in range(26):
        a = rng.random() * 6.28
        q = (R - 5.4) * rng.random() ** 0.6
        clast(sub, rng, dx + q * math.cos(a), dy + q * math.sin(a), 0.6 + rng.random() * 0.9, AGG[int(rng.random() * 6)])
    # 물방울: 위에서 드럼 벽으로
    for (x, y, s_) in [(14.5, 6.5, 1.0), (21.0, 3.8, 1.1), (41.0, 3.8, 1.1), (47.5, 6.5, 1.0), (9.0, 14.0, 0.9), (53.0, 14.0, 0.9), (12.0, 22.5, 0.8), (50.0, 22.5, 0.8)]:
        _drop(sub, x, y, s_)
    # 확대 표시와 지시선
    mx, my = 31.0, dy + R - 0.7
    sub.ell(mx, my, 1.2, 1.2, outline=INKC, lw=0.3)
    cs = 17.5
    x1, x2, cy0 = 9.5, 35.0, 34.0
    sub.line([(mx - 0.8, my + 1.0), (x1 + cs, cy0 - 0.6)], INKC, 0.25, joint=False)
    sub.line([(mx + 0.8, my + 1.0), (x2, cy0 - 0.6)], INKC, 0.25, joint=False)
    _micro(sub, rng, x1, cy0, cs, 1)
    _micro(sub, rng, x2, cy0, cs, 2)
    # 화살표(1 → 2)
    ay = cy0 + cs / 2
    sub.line([(x1 + cs + 1.2, ay), (x2 - 1.5, ay)], INKC, 0.4, joint=False)
    sub.poly([(x2 - 2.4, ay - 1.0), (x2 - 0.7, ay), (x2 - 2.4, ay + 1.0)], fill=INKC)


# ───────────────────────── 3. 포르투스 방파제 단면(바닷물 + 새 광물) ─────────────────────────
def _plate(sub, x, y, L, w, ang, col, dk):
    ca, sa = math.cos(ang), math.sin(ang)
    nx, ny = -sa * w, ca * w
    p = [(x - ca * L / 2 - nx, y - sa * L / 2 - ny), (x + ca * L / 2 - nx, y + sa * L / 2 - ny),
         (x + ca * L / 2 + nx, y + sa * L / 2 + ny), (x - ca * L / 2 + nx, y - sa * L / 2 + ny)]
    sub.poly(p, fill=col)
    sub.poly([p[3], p[2], ((p[2][0] + p[1][0]) / 2, (p[2][1] + p[1][1]) / 2), ((p[3][0] + p[0][0]) / 2, (p[3][1] + p[0][1]) / 2)], fill=dk)


def fig_portus(sub, vc, vr, rng):
    WL = 21.0
    sub.rect(-2, -2, 64, WL, fill=SKY)
    sub.rect(-2, WL, 64, 64, fill=SEAC)
    sub.rect(-2, 41, 64, 64, fill=SEAC_D)
    sub.rect(-2, 54.5, 64, 64, fill=SOILC[0])
    sub.rect(-2, 58.5, 64, 64, fill=SOILC[1])
    for i in range(18):
        sub.ell(rng.random() * 62, 55 + rng.random() * 8, 0.45, 0.32, fill=shade(SOILC[1], 0.75 + 0.35 * rng.random()))
    # 방파제 단면
    xt0, xt1, yt = 22.5, 39.5, 12.0
    xb0, xb1, yb = 12.5, 49.5, 54.5
    body = [(xb0, yb), (xt0, yt), (xt1, yt), (xb1, yb)]
    sub.poly(body, fill=CONC)

    def xl(y):
        return xt0 + (xb0 - xt0) * (y - yt) / (yb - yt)

    def xr(y):
        return xt1 + (xb1 - xt1) * (y - yt) / (yb - yt)
    # 물에 잠긴 부분 어두운 3단째(잠긴 면은 바다색이 스며 어둡다)
    sub.poly([(xl(WL), WL), (xr(WL), WL), (xb1, yb), (xb0, yb)], fill=shade(CONC, 0.9))
    sub.poly([(xl(WL), WL), (xr(WL), WL), (xr(WL) - 0.0, WL + 0.1), (xl(WL), WL + 0.1)], fill=CONC)
    # 위쪽(공기 중) 밝은 면
    sub.poly([(xt0, yt), (xt1, yt), (xr(WL), WL), (xl(WL), WL)], fill=shade(CONC, 1.1))
    # 콘크리트: 층(투입 구획)과 골재
    for yy in (27.5, 34.0, 41.0, 48.0):
        sub.line([(xl(yy), yy), (xr(yy), yy)], shade(CONC, 0.72), 0.28, joint=False)
    for _ in range(70):
        y = yt + 1.2 + rng.random() * (yb - yt - 2.4)
        x = xl(y) + 1.6 + rng.random() * (xr(y) - xl(y) - 3.2)
        clast(sub, rng, x, y, 0.8 + rng.random() * 1.2, AGG[int(rng.random() * 6)])
    for _ in range(40):
        y = yt + 1.0 + rng.random() * (yb - yt - 2.0)
        x = xl(y) + 1.0 + rng.random() * (xr(y) - xl(y) - 2.0)
        sub.ell(x, y, 0.28, 0.2, fill=shade(CONC, 0.7))
    # 바닷물이 스며드는 길(양쪽 면에서 안쪽으로 파란 점선)
    for (yy, d) in [(26.5, 1), (31.5, 1), (37, 1), (30, -1), (35.5, -1), (45, -1)]:
        x0 = xl(yy) if d > 0 else xr(yy)
        for u in range(5):
            sub.ell(x0 + d * (0.7 + 1.5 * u), yy + 0.25 * u * (-1 if u % 2 else 1), 0.55 - 0.05 * u, 0.4, fill=(74, 140, 200))
    # 방파제 안 작은 공극의 새 광물(판 + 구)
    for (fx, fy) in [(20.5, 40), (25, 46.5), (30.5, 50.2), (21, 31)]:
        for k in range(3):
            sub.line([(fx + (k - 1) * 0.7 - 0.8, fy + 0.6), (fx + (k - 1) * 0.7 + 0.8, fy - 0.6)], MARB, 0.35, joint=False)
        sub.ell(fx + 1.3, fy + 0.9, 0.5, 0.5, fill=(236, 228, 210))
    # 수면선: 흰 물결
    for x in (3, 9.0, 52.5, 58):
        sub.arc(x, WL + 0.6, 2.0, 0.8, 180, 360, SEAC_L, 0.3)
    sub.line([(-2, WL), (xl(WL), WL)], SEAC_L, 0.3, joint=False)
    sub.line([(xr(WL), WL), (64, WL)], SEAC_L, 0.3, joint=False)
    # 파도 화살표(왼쪽 바다 → 방파제)
    sub.line([(3.5, 29.0), (9.2, 29.0)], (60, 112, 156), 0.4, joint=False)
    sub.poly([(8.4, 28.0), (10.6, 29.0), (8.4, 30.0)], fill=(60, 112, 156))
    sub.line([(3.5, 36.5), (8.0, 36.5)], (60, 112, 156), 0.4, joint=False)
    sub.poly([(7.2, 35.5), (9.4, 36.5), (7.2, 37.5)], fill=(60, 112, 156))
    # 확대 원(안쪽 공극): 바닷물과 반응해 자라는 알루미늄 토버모라이트 판 · 필립사이트 구
    ix, iy, ir = 42.0, 41.5, 11.0
    mx, my = 30.5, 41.5
    sub.line([(mx + 0.7, my - 0.8), (ix - 5.0, iy - ir * 0.9)], INKC, 0.25, joint=False)
    sub.line([(mx + 0.7, my + 0.8), (ix - 5.0, iy + ir * 0.9)], INKC, 0.25, joint=False)
    sub.ell(mx, my, 1.1, 1.1, outline=INKC, lw=0.3)
    sub.ell(ix, iy, ir + 0.6, ir + 0.6, fill=INKC)
    sub.ell(ix, iy, ir, ir, fill=MORT)
    for _ in range(14):
        a = rng.random() * 6.28
        q = ir * 0.95 * rng.random() ** 0.5
        sub.ell(ix + q * math.cos(a), iy + q * math.sin(a), 0.3, 0.24, fill=MORT_D)
    # 공극(바닷물이 찬 빈 곳)
    pore = []
    for k in range(10):
        t = 2 * math.pi * k / 10
        q = 6.2 * (0.8 + 0.28 * math.sin(3 * t + 1.0))
        pore.append((ix + q * math.cos(t), iy + q * 0.86 * math.sin(t)))
    sub.poly(pore, fill=SEAC)
    sub.poly([p for p in pore if p[1] > iy] + [(ix + 5.0, iy + 0.1), (ix - 5.0, iy + 0.1)], fill=SEAC_D)
    # 공극 가장자리에서 안쪽으로 자라는 판(토버모라이트)
    for k in range(10):
        t = 2 * math.pi * k / 10 + 0.15
        q = 5.75 * (0.8 + 0.28 * math.sin(3 * (t - 0.15) + 1.0))
        px, py = ix + q * math.cos(t), iy + q * 0.86 * math.sin(t)
        _plate(sub, px - 1.0 * math.cos(t), py - 1.0 * math.sin(t), 3.6, 0.38, t + (0.35 if k % 2 else -0.35), MARB, MARB_D)
    # 구형 필립사이트 알갱이 무리
    for (a, q) in [(0.5, 3.0), (2.6, 2.8), (4.1, 3.3)]:
        for j in range(3):
            px = ix + q * math.cos(a) + (j - 1) * 0.8
            py = iy + q * 0.86 * math.sin(a) + (j % 2) * 0.5
            sub.ell(px, py, 0.8, 0.8, fill=shade((236, 228, 210), 0.88))
            sub.ell(px - 0.18, py - 0.2, 0.4, 0.34, fill=(252, 250, 240))
    # 공극 물방울 점
    for _ in range(5):
        sub.ell(ix + (rng.random() - 0.5) * 3.0, iy + (rng.random() - 0.5) * 2.4, 0.2, 0.2, fill=SEAC_L)
