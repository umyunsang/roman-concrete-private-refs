# -*- coding: utf-8 -*-
# 확대 창 그림 B조: 카라칼라 욕장(벽 단면) · 막센티우스 바실리카(볼트와 코퍼) · 마르켈루스 극장(잠긴 기초)
# 규약: fig_<키>(sub, vc, vr, rng) — sub=Layer(0,0,62,62), 원 중심 (vc,vc) 반지름 vr. 글자 없음. 난수는 rng만.
import math
import sys
sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/lib")
from common import *

LIME_W = (246, 244, 236)
AIR = (240, 228, 200)
ROOM = (226, 208, 172)
INK = (70, 52, 38)


def _lerp(c0, c1, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(c0[i] * (1 - t) + c1[i] * t)) for i in range(3))


def _chunk(L, x, y, r, base, rng, nv=None, lit=1.13, dark=0.82):
    """굵은 알갱이 한 개: 불규칙 다각형 + 밝은 면 + 어두운 면(3단)"""
    nv = nv or rng.choice((5, 6, 7))
    rot = rng.random() * math.tau
    pts = []
    for k in range(nv):
        a = rot + k * math.tau / nv
        rr = r * (0.78 + 0.32 * rng.random())
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a) * 0.86))
    L.poly(pts, fill=base)
    # 위쪽(밝은) 면 / 아래쪽(어두운) 면
    top = [p for p in pts if p[1] <= y + 0.1] + [(x, y)]
    bot = [p for p in pts if p[1] > y + 0.1] + [(x, y)]
    if len(top) >= 3:
        L.poly(top, fill=shade(base, lit))
    if len(bot) >= 3:
        L.poly(bot, fill=shade(base, dark))
    L.poly(pts[:1] + pts[1:], fill=None)
    return pts


def _pumice(L, x, y, r, rng):
    base = (236, 220, 192)
    _chunk(L, x, y, r, base, rng, lit=1.04, dark=0.90)
    for _ in range(max(2, int(r * 2.2))):
        a = rng.random() * math.tau
        d = rng.random() * r * 0.55
        L.dot(x + d * math.cos(a), y + d * math.sin(a) * 0.8, 0.17, (150, 124, 98))


def _in_poly(px, py, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi + 1e-12) + xi:
            inside = not inside
        j = i
    return inside


# ──────────────────────────────────────────────────────────────
# 1) 카라칼라 욕장 — 벽·돔 하부 단면
#    근거: docs/research/화산-Support-사례-조사-2026-10-18.md 1.5절 (벽 전체=겉 벽돌 콘크리트 L180,
#          돔 홀 볼트 골재: 아래 노란 응회암 → 위로 갈수록 짙은 붉은 경석 L183). 두께 수치는 미확인이라 모식.
# ──────────────────────────────────────────────────────────────
def fig_baths(sub, vc, vr, rng):
    L = sub
    L.rect(0, 0, 62, 62, fill=AIR)
    CX, CY = 45.0, 36.0           # 돔 곡률 중심
    XO, XI = 7.0, 21.0            # 벽 바깥면·안쪽면 x
    RO, RI = CX - XO, CX - XI     # 바깥·안쪽 반지름 40, 26
    RM = (RO + RI) / 2
    WALL_Y0 = 72.0
    LW = WALL_Y0 - CY             # 직선 구간 길이
    ARC = math.radians(150) * RM  # 호 구간(180° → 30°)
    TOT = LW + ARC

    def edge(t, off):
        """중심선 위 매개 t에서 off(0=바깥, 1=안쪽)의 점"""
        if t <= LW:
            return (XO + (XI - XO) * off, WALL_Y0 - t)
        ph = math.pi - (t - LW) / RM
        r = RO - (RO - RI) * off
        return (CX + r * math.cos(ph), CY - r * math.sin(ph))

    # 방(안쪽 공간)
    inner = [edge(t, 1.0) for t in [i * TOT / 80 for i in range(81)]]
    L.poly(inner + [(80, 0), (80, 80)], fill=ROOM)
    # 방 바닥의 안쪽 벽 면 힌트: 뒤벽 어두운 면 한 장

    # 몸체: 단면 슬라이스(모르타르 색이 위로 갈수록 밝아짐)
    FB = 0.17                      # 벽돌 외피 두께 비율
    n = 150
    zone_at = lambda t: 0.0 if t < LW else min(1.0, (t - LW) / (ARC * 0.42))
    for i in range(n):
        t0, t1 = TOT * i / n, TOT * (i + 1) / n + 0.25
        z = zone_at((t0 + t1) / 2)
        mort = _lerp((168, 150, 120), (214, 200, 176), z)
        a0, a1 = edge(t0, 0.0), edge(t1, 0.0)
        b1, b0 = edge(t1, 1.0), edge(t0, 1.0)
        L.poly([a0, a1, b1, b0], fill=mort)

    # 골재(굵은 알갱이)
    def band_pt():
        for _ in range(40):
            t = rng.random() * TOT
            off = FB + 0.06 + rng.random() * (1 - 2 * FB - 0.12)
            return t, off, edge(t, off)
    count = 0
    tries = 0
    while count < 150 and tries < 3000:
        tries += 1
        t, off, (x, y) = band_pt()
        z = zone_at(t)
        # 크기: 아래 크고 위로 갈수록 작아짐
        r = (1.7 - 0.7 * z) * (0.7 + 0.5 * rng.random())
        pz = z + (rng.random() - 0.5) * 0.28          # 경석 확률 경계를 거칠게
        if pz < 0.30:
            col = rng.choice(((190, 150, 96), (178, 140, 92), (198, 160, 106)))     # 노란 응회암
            if rng.random() < 0.18:
                col = BRICK_D                                                      # 벽돌 조각
            _chunk(L, x, y, r, col, rng)
        elif pz < 0.62:
            if rng.random() < 0.5:
                _chunk(L, x, y, r, (186, 146, 96), rng)
            else:
                _pumice(L, x, y, r * 0.95, rng)
        else:
            if rng.random() < 0.22:
                _chunk(L, x, y, r * 0.9, (150, 70, 52), rng, lit=1.1, dark=0.85)    # 짙은 붉은 경석
            else:
                _pumice(L, x, y, r, rng)
        count += 1

    # 벽돌 외피(바깥·안쪽) — 벽돌 단(코스) 줄 + 줄눈
    cour = 1.15
    for side_off in (0.0, 1.0 - FB):
        k = 0
        t = 0.0
        while t < TOT:
            t1 = min(TOT, t + cour)
            col = (BRICK, BRICK_L, BRICK_D)[(k * 7 + (3 if side_off else 0)) % 3]
            q0, q1 = edge(t, side_off), edge(t1, side_off)
            q2, q3 = edge(t1, side_off + FB), edge(t, side_off + FB)
            L.poly([q0, q1, q2, q3], fill=col)
            L.line([q0, q3], shade(BRICK_D, 0.72), 0.16, joint=False)
            # 벽돌 세로 줄눈(엇갈림)
            if k % 2 == 0:
                m = ((q0[0] + q1[0] + q2[0] + q3[0]) / 4, (q0[1] + q1[1] + q2[1] + q3[1]) / 4)
                L.dot(m[0], m[1], 0.12, shade(BRICK_D, 0.7))
            t = t1
            k += 1
    # 외피와 콘크리트 경계선, 단면 윤곽
    for off in (0.0, FB, 1.0 - FB, 1.0):
        L.line([edge(TOT * i / 60, off) for i in range(61)], shade(BRICK_D, 0.7) if off in (FB, 1 - FB) else INK, 0.2 if off in (FB, 1 - FB) else 0.4)



# ──────────────────────────────────────────────────────────────
# 2) 막센티우스 바실리카 — 배럴 볼트 단면 + 8각 코퍼 + 점선 복원
#    근거: Basic-대체-정보-추가-건축물-조사-2026-10-19.md L439 (아치 3칸, 배럴 볼트의 팔각 코퍼,
#          사라진 신랑 교차 볼트는 점선 복원), 화산-Support 사례 L546–552 (측랑 코퍼 배럴 볼트, 신랑 교차 볼트 3개)
# ──────────────────────────────────────────────────────────────
def _octagon(cx, cy, r):
    return [(cx + r * math.cos(math.radians(22.5 + 45 * k)), cy + r * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]


def fig_basilica(sub, vc, vr, rng):
    L = sub
    L.rect(0, 0, 62, 62, fill=AIR)
    # 점선 복원: 사라진 신랑 교차 볼트 3칸(윗줄, 낮은 대비)
    DASH = (150, 122, 90)
    span = 20.0
    for b in range(3):
        x0 = 1.0 + b * span
        cxm = x0 + span / 2
        cyb = 19.0
        pts = [(cxm + (span / 2) * math.cos(math.radians(a)), cyb - 13.0 * math.sin(math.radians(a))) for a in range(180, 361 - 180, -6)]
        pts = [(cxm - (span / 2) * math.cos(math.radians(a)), cyb - 13.0 * math.sin(math.radians(a))) for a in range(0, 181, 6)]
        for i in range(len(pts) - 1):
            L.dashed(pts[i], pts[i + 1], DASH, 0.38, dash=1.3, gap=0.9)
        # 교차선(그로인) 점선
        L.dashed((x0, cyb), (cxm, cyb - 13.0), DASH, 0.32, dash=1.1, gap=1.0)
        L.dashed((x0 + span, cyb), (cxm, cyb - 13.0), DASH, 0.32, dash=1.1, gap=1.0)
    L.dashed((0.5, 19.0), (61.5, 19.0), DASH, 0.32, dash=1.4, gap=1.1)

    # 남은 측랑 배럴 볼트 단면 (아치 반지름)
    CX, CY = 31.0, 49.0
    RI, RO = 14.0, 23.0
    # 몸체: 벽(좌우) + 아치 링
    # 좌우 벽체(콘크리트 단면)
    L.rect(1, CY, 61, 63, fill=CONC)
    # 링
    n = 72
    def ring(a_deg, r):
        return (CX + r * math.cos(math.radians(a_deg)), CY - r * math.sin(math.radians(a_deg)))
    for i in range(n):
        a0 = 180 - 180.0 * i / n
        a1 = 180 - 180.0 * (i + 1) / n - 0.2
        z = i / n
        mort = _lerp((164, 156, 140), (192, 184, 166), 1 - abs(z - 0.5) * 2)
        L.poly([ring(a0, RO), ring(a1, RO), ring(a1, RI), ring(a0, RI)], fill=mort)
    # 팔각 코퍼 파임: 내면 곡선에 단계 홈(단면에서 코퍼는 깊이 변화로 보임)
    for i in range(6):
        a0 = 168 - i * 27.0
        a1 = a0 - 15.0
        L.poly([ring(a0, RI), ring(a1, RI), ring(a1, RI + 2.5), ring(a0, RI + 2.5)], fill=shade(CONC, 0.74))
        L.poly([ring(a0, RI), ring(a1, RI), ring(a1, RI + 0.8), ring(a0, RI + 0.8)], fill=shade(CONC, 0.62))
    # 벽 위 어깨 부분 채움 : 링 바깥~사각 모서리
    for side in (-1, 1):
        pts = [(CX + side * RO, CY), (CX + side * 30, CY), (CX + side * 30, CY - 14), (CX + side * 22, CY - 16)]
        for a in range(0, 46, 9):
            pts.append(ring(90 + side * (90 - a) if side > 0 else 90 + (90 - a), RO))
    # 골재(링 + 벽)
    cnt = 0
    tries = 0
    while cnt < 70 and tries < 2000:
        tries += 1
        a = rng.random() * 180
        r = RI + 1.8 + rng.random() * (RO - RI - 3.6)
        x, y = ring(a, r)
        _chunk(L, x, y, 0.9 + rng.random() * 0.9, rng.choice(((178, 144, 100), (170, 134, 100), BRICK_D, (190, 160, 118))), rng)
        cnt += 1
    for _ in range(26):
        x = rng.choice((rng.uniform(2.5, CX - RO - 1.0), rng.uniform(CX + RO + 1.0, 59.5)))
        y = rng.uniform(CY + 2, 61)
        _chunk(L, x, y, 0.9 + rng.random() * 0.9, rng.choice(((178, 144, 100), BRICK_D, (190, 160, 118))), rng)
    # 벽돌 외피 : 아치 바깥 둘레(링 바깥 1.3 mm), 바깥 단 줄눈
    k = 0
    for i in range(0, 45):
        a0 = 180 - 4.0 * i
        a1 = a0 - 4.0
        col = (BRICK, BRICK_L, BRICK_D)[k % 3]
        L.poly([ring(a0, RO), ring(a1, RO), ring(a1, RO + 2.2), ring(a0, RO + 2.2)], fill=col)
        L.line([ring(a0, RO), ring(a0, RO + 2.2)], shade(BRICK_D, 0.7), 0.16, joint=False)
        k += 1
    # 아치 바깥 둘레 위 벽돌 외피 : 바깥 쪽 위 벽(링 바깥~) 벽돌 단
    for side in (-1, 1):
        for j in range(8):
            y0 = CY - 0.0 + j * 2.2
            if y0 > 61:
                break
            xo = CX + side * (RO + 0.0)
            L.rect(min(xo, xo + side * 2.2), y0, max(xo, xo + side * 2.2), y0 + 2.2, fill=(BRICK, BRICK_L, BRICK_D)[j % 3])
            L.line([(xo, y0), (xo + side * 2.2, y0)], shade(BRICK_D, 0.7), 0.15, joint=False)
    # 기둥(피어): 좌우 벽 안쪽 면에 벽돌 외피
    for side in (-1, 1):
        xi = CX + side * RI
        for j in range(8):
            y0 = CY + j * 2.2
            if y0 > 61:
                break
            L.rect(min(xi, xi - side * 2.2), y0, max(xi, xi - side * 2.2), y0 + 2.2, fill=(BRICK, BRICK_L, BRICK_D)[(j + 1) % 3])
        pass
    # 개구(아치 안쪽 열린 부분): 8각 코퍼 격자
    op = []
    for a in range(0, 181, 5):
        op.append(ring(a, RI - 0.2))
    op += [(CX - RI + 0.2, 62), (CX + RI - 0.2, 62)]
    L.poly(op, fill=shade(CONC, 0.92))
    pitch = 6.4
    R8 = 2.75
    # 8각 코퍼 + 사이 작은 사각 코퍼 (줄 엇갈림 없이 격자)
    for row in range(-1, 6):
        for col in range(-3, 4):
            ox = CX + col * pitch
            oy = CY - RI + 3.4 + row * pitch
            pts = _octagon(ox, oy, R8 + 0.35)
            if all(math.hypot(px - CX, py - CY) < RI - 0.5 for (px, py) in pts) and oy < 63:
                L.poly(pts, fill=shade(CONC, 1.12))
                inn = _octagon(ox, oy, R8 - 0.55)
                L.poly(inn, fill=shade(CONC, 0.62))
                L.poly([inn[5], inn[4], inn[3], inn[2], (ox + 0.2, oy + 0.4)], fill=shade(CONC, 0.74)) if False else None
                half = [p for p in inn if p[1] <= oy + 0.1]
                L.poly(half + [(ox, oy)], fill=shade(CONC, 0.54))
            sx, sy = ox + pitch / 2, oy + pitch / 2
            sq = [(sx - 0.8, sy), (sx, sy - 0.8), (sx + 0.8, sy), (sx, sy + 0.8)]
            if all(math.hypot(px - CX, py - CY) < RI - 0.5 for (px, py) in sq) and sy < 63:
                L.poly(sq, fill=shade(CONC, 0.66))
    # 단면 윤곽
    L.line([ring(a, RO) for a in range(0, 181, 6)], INK, 0.35)
    L.line([ring(a, RO + 2.2) for a in range(0, 181, 6)], shade(BRICK_D, 0.7), 0.25)
    L.line([ring(a, RI) for a in range(0, 181, 6)], INK, 0.35)


# ──────────────────────────────────────────────────────────────
# 3) 마르켈루스 극장 — 테베레에 잠긴 기초와 결정
#    근거: Basic-대체-정보-추가-건축물-조사-2026-10-19.md L469 ('기원전 44~11년 … 콘크리트 하부 구조는 테베레 홍수에
#          거듭 잠겼고, 포촐라네 로세 스코리아의 계면에 바늘·판 모양 스트래틀링가이트 결정이 보강한다'
#          [Jackson 외 2026, S4 pp.278–279]; 원 연구 Jackson 외 2011, Archaeometry 53(4), 초록 요약만 확인·본문 미열람).
#          위키백과: 응회암·콘크리트에 레티쿨라툼 마감(L471). 균열을 결정이 메우는 모습은 모식.
# ──────────────────────────────────────────────────────────────
def fig_theatre(sub, vc, vr, rng):
    L = sub
    L.rect(0, 0, 62, 62, fill=AIR)
    WL = 30.0                       # 평상시 수위
    X0, X1 = 7.0, 45.0              # 기초 좌우
    YT, YB = 12.0, 54.0             # 기초 위·아래

    # 오른쪽: 강 둑 바깥(강물) / 아래: 땅
    L.rect(X1, WL, 62, 62, fill=RIVER)
    for i in range(7):
        L.arc(50 + (i % 2) * 5, WL + 3.5 + i * 4.2, 3.2, 1.0, 190, 350, (206, 232, 246), 0.3)
    L.rect(0, 53.5, 62, 62, fill=SOIL)
    L.rect(0, 53.5, 62, 55.0, fill=SOIL_D)
    for _ in range(18):
        _chunk(L, rng.uniform(1, 61), rng.uniform(56.5, 61.5), 0.7 + rng.random() * 0.6, rng.choice((SOIL_D, (146, 118, 80))), rng)
    # 왼쪽 둑 흙
    L.rect(0, WL - 2, X0, 54, fill=SOIL)
    L.rect(0, WL - 2, X0, WL, fill=(94, 126, 66))

    # 기초 콘크리트 몸체
    MORT = (150, 138, 120)
    L.rect(X0, YT, X1, YB, fill=MORT)
    # 위쪽 마감 줄: 레티쿨라툼(마름모 응회암 쐐기) 얇은 띠 + 오른쪽 트래버틴 널
    for ix in range(0, int((X1 - X0) / 2.6)):
        for iy in range(0, 3):
            cxx = X0 + 2.2 + ix * 2.6 + (1.3 if iy % 2 else 0)
            cyy = 2.6 + iy * 2.6
            if cxx < X1 - 2:
                L.poly([(cxx, cyy - 1.3), (cxx + 1.3, cyy), (cxx, cyy + 1.3), (cxx - 1.3, cyy)], fill=(TUFF, shade(TUFF, 1.12), shade(TUFF, 0.88))[(ix + iy) % 3])
    L.rect(X0, 0, X0 + 2.2, YT, fill=TRAV_L)
    L.rect(X0, 0, X0 + 0.8, YT, fill=LIME_W)
    L.rect(X0 + 2.2, YT - 0.8, X1, YT, fill=shade(MORT, 0.8))

    # 골재: 어두운 붉은 갈색 스코리아(포촐라네 로세) + 노란 응회암 조각
    scor = []
    tries = 0
    while len(scor) < 40 and tries < 1500:
        tries += 1
        x, y = rng.uniform(X0 + 1.5, X1 - 1.5), rng.uniform(YT + 1.5, YB - 1.5)
        r = 1.1 + rng.random() * 1.7
        if any(math.hypot(x - a, y - b) < r + rr + 0.3 for a, b, rr in scor):
            continue
        scor.append((x, y, r))
    # 균열 중심선 (위→아래 갈지자)
    cr = [(21.0, YT), (25.0, 19.0), (20.5, 26.0), (26.0, 34.0), (22.0, 42.0), (27.0, 48.0), (25.0, YB)]
    cw = [1.3, 1.7, 2.1, 2.4, 2.1, 1.8, 1.3]          # 반폭
    cl, cr_ = [], []
    for i, (px, py) in enumerate(cr):
        cl.append((px - cw[i], py))
        cr_.append((px + cw[i], py))
    crack_poly = cl + cr_[::-1]
    for (x, y, r) in scor:
        # 균열 안에 중심이 드는 알갱이는 건너뜀
        if _in_poly(x, y, crack_poly):
            continue
        base = rng.choice(((112, 58, 46), (126, 66, 50), (100, 54, 44), (136, 76, 56)))
        if rng.random() < 0.22:
            base = (190, 150, 100)
        _chunk(L, x, y, r, base, rng)
        if base[0] < 150:
            for _ in range(int(r * 1.5)):
                a = rng.random() * math.tau
                d = rng.random() * r * 0.5
                L.dot(x + d * math.cos(a), y + d * math.sin(a) * 0.8, 0.14, (56, 30, 26))
    # 평상시 수위 아래 물에 잠긴 부분 : 청색 기운
    L.rect(0, WL, X1, 54, fill=(110, 170, 210, 62))
    L.rect(0, WL, X0, 54, fill=(110, 170, 210, 40))
    # 균열 : 어두운 틈 → 결정으로 메움
    L.poly(crack_poly, fill=(58, 40, 34))
    # 틈 위쪽 입구 : 물이 스며드는 푸른색
    # 결정 : 양쪽 벽에서 자라 가운데로 모임(판 + 바늘). 아래쪽 끝은 아직 비어 있음
    def hexplate(x, y, w, h, ang, col):
        pts = []
        for k in range(6):
            a = math.radians(60 * k)
            px, py = w * math.cos(a), h * math.sin(a)
            pts.append((x + px * math.cos(ang) - py * math.sin(ang), y + px * math.sin(ang) + py * math.cos(ang)))
        L.poly(pts, fill=col)
        L.poly([pts[3], pts[4], pts[5], pts[0], (x, y)], fill=shade(col, 0.88))
    for i in range(len(cr) - 1):
        (xa, ya), (xb, yb) = cr[i], cr[i + 1]
        steps = 7
        for s in range(steps):
            f = s / steps
            xm, ym = xa + (xb - xa) * f, ya + (yb - ya) * f
            wm = cw[i] + (cw[i + 1] - cw[i]) * f
            fill_level = 0.0 if ym < WL else (1.0 if ym < 44 else max(0.0, 1.0 - (ym - 44) / 9.0))
            for sd in (-1, 1):
                if fill_level > 0 and rng.random() < 0.95 * fill_level + 0.1:
                    ang = math.radians(rng.uniform(-40, 40) + (0 if sd < 0 else 180) + 90 * 0)
                    hexplate(xm + sd * (wm - 1.0 + rng.random() * 0.4), ym + rng.uniform(-0.5, 0.5), 1.7 + rng.random() * 0.6, 0.85 + rng.random() * 0.3, ang, LIME_W)
                for _ in range(2):
                    if rng.random() < fill_level:
                        a = math.radians(rng.uniform(-30, 30)) + (0 if sd < 0 else math.pi)
                        ln = wm * (0.55 + 0.5 * rng.random())
                        x0 = xm + sd * (wm - 0.2)
                        y0 = ym + rng.uniform(-0.8, 0.8)
                        L.line([(x0, y0), (x0 + ln * math.cos(a), y0 + ln * math.sin(a))], (252, 250, 240), 0.28, joint=False)
            # 가운데 쪽 결정
            if rng.random() < fill_level:
                hexplate(xm + rng.uniform(-0.8, 0.8), ym + rng.uniform(-0.6, 0.6), 1.2 + rng.random() * 0.6, 0.7, math.radians(rng.uniform(-30, 30)), (250, 248, 238))
    # 스코리아 계면 결정 : 잠긴 구간 스코리아 테두리에 작은 흰 바늘·판
    for (x, y, r) in scor:
        if y < WL or _in_poly(x, y, crack_poly):
            continue
        for _ in range(3 + int(r * 1.5)):
            a = rng.random() * math.tau
            px, py = x + (r + 0.15) * math.cos(a), y + (r + 0.15) * 0.86 * math.sin(a)
            if rng.random() < 0.5:
                L.line([(px, py), (px + 0.9 * math.cos(a), py + 0.9 * math.sin(a))], (252, 250, 240), 0.22, joint=False)
            else:
                L.dot(px, py, 0.26, (250, 248, 238))
    # 수위 선(들): 홍수 흔적 점선 2줄 + 평상시 수위 실선
    for yy in (WL - 12.0, WL - 6.5):
        L.dashed((X0 - 0.3, yy), (X1 + 0.3, yy), (96, 150, 188), 0.3, dash=1.6, gap=1.2)
    L.line([(0, WL), (62, WL)], (60, 112, 156), 0.45, joint=False)
    for i in range(6):
        L.arc(X1 + 3 + i * 2.8, WL, 1.3, 0.5, 180, 360, (210, 236, 248), 0.25)
    # 기초 윤곽
    L.line([(X0, 0), (X0, YB), (X1, YB), (X1, YT)], INK, 0.35)
