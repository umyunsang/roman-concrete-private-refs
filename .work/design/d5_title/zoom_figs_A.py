# -*- coding: utf-8 -*-
# 확대 창 그림 A: 콜로세움 기초 고리 / 판테온 돔 단면 쐐기 / 트라야누스 시장 대회랑 볼트
# 규약: fig_<키>(sub, vc, vr, rng) — sub=Layer(0,0,62,62), 글자 없음, 면 3단 색, 난수는 rng만 사용
import sys, math
sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/lib")
from common import *

SANDBG = (236, 220, 178)
MORT = (206, 194, 178)
SOILC = (150, 118, 80)
SOILD = (122, 94, 62)
SOILL = (176, 142, 100)
CREAM = (232, 218, 184)
SCORIA = (96, 72, 66)
PUMICE = (244, 240, 228)
YTUFF = (206, 170, 106)
LIME = (252, 251, 246)


def _frag(sub, cx, cy, rx, ry, col, rng, rot=0.0, nv=None, lw=0.25):
    """3단 면 알갱이: 어두운 밑면 + 중간 본체 + 밝은 윗면"""
    nv = nv or rng.choice((6, 7, 8))
    base = []
    for j in range(nv):
        t = 2 * math.pi * j / nv + rng.random() * 0.4
        q = 0.78 + rng.random() * 0.3
        base.append((rx * q * math.cos(t), ry * q * math.sin(t)))
    c, s = math.cos(rot), math.sin(rot)

    def T(p, k=1.0, dx=0.0, dy=0.0):
        x, y = p[0] * k + dx, p[1] * k + dy
        return (cx + x * c - y * s, cy + x * s + y * c)

    sub.poly([T(p, 1.0, 0.0, 0.0) for p in base], fill=shade(col, 0.76))
    sub.poly([T(p, 0.9, -0.05 * rx, -0.1 * ry) for p in base], fill=col)
    sub.poly([T(p, 0.5, -0.22 * rx, -0.32 * ry) for p in base], fill=shade(col, 1.1 if max(col) < 235 else 1.0))


def _sector(cx, cy, r0, r1, a0, a1, n=24):
    out = [(cx + r1 * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r1 * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    inn = [(cx + r0 * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r0 * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n, -1, -1)]
    return out + inn


# ─────────────────────────── 1. 콜로세움 기초 고리 ───────────────────────────
def fig_colosseum(sub, vc, vr, rng):
    """기초 트렌치 단면: 다짐 층 줄 + 트래버틴·응회암 큰 조각 + 위쪽 외벽 아래부 (화산-Support 사례 조사 602·707행, Basic 대체 조사 206·220행)"""
    sub.rect(-2, -2, 64, 64, fill=SANDBG)
    gy = 17.0                                    # 지표선
    x0, x1 = 12.0, 50.0                          # 트렌치 폭
    # 주변 흙(지표 아래, 3단 줄무늬)
    sub.rect(-2, gy, 64, 64, fill=SOILC)
    for k in range(7):
        yy = gy + 2 + k * 7.5
        sub.rect(-2, yy, x0 + 1, yy + 1.2, fill=SOILD)
        sub.rect(x1 - 1, yy + 3, 64, yy + 4.2, fill=SOILD)
    for i in range(36):
        x = rng.choice((rng.random() * (x0 - 1), x1 + 1 + rng.random() * (63 - x1)))
        sub.ell(x, gy + 1.5 + rng.random() * 44, 0.45, 0.3, fill=SOILL)
    sub.rect(-2, gy, 64, gy + 1.1, fill=SOILL)
    # 트렌치 속 콘크리트: 다짐 층(각 층 ≈4.3 mm), 층마다 평평하게 누운 큰 조각 한 줄
    top, bot, step = gy + 1.1, 63.0, 4.5
    nL = int((bot - top) / step) + 1
    cols = [TRAV, TUFF, (186, 112, 84), TRAV_D, TUFF]
    for L in range(nL):
        y0 = top + L * step
        y1 = min(bot + 1, y0 + step)
        tone = MORT if L % 2 == 0 else shade(MORT, 0.94)
        sub.rect(x0, y0, x1, y1, fill=tone)
        sub.rect(x0, y1 - 0.45, x1, y1, fill=shade(MORT, 0.78))       # 다진 층 사이 어두운 줄
        sub.rect(x0, y0, x1, y0 + 0.3, fill=shade(MORT, 1.06))
        cx_ = x0 + 2.2 + rng.random() * 2
        while cx_ < x1 - 2.5:
            rx = 1.9 + rng.random() * 2.2
            ry = 0.95 + rng.random() * 0.55
            if cx_ + rx > x1 - 0.6:
                break
            col = TRAV_L if rng.random() < 0.42 else (TUFF if rng.random() < 0.7 else (188, 116, 88))
            _frag(sub, cx_ + rx, y0 + step * 0.5 + (rng.random() - 0.5) * 0.7, rx, ry, col, rng, rot=(rng.random() - 0.5) * 0.25)
            cx_ += 2 * rx + 0.5 + rng.random() * 1.2
        for q in range(5):
            sub.ell(x0 + 1 + rng.random() * (x1 - x0 - 2), y0 + 0.9 + rng.random() * 2.4, 0.28, 0.2, fill=shade(MORT, 0.7))
    # 트렌치 벽(흙과 콘크리트 사이 어두운 면)
    sub.rect(x0 - 0.7, gy, x0, 64, fill=SOILD)
    sub.rect(x1, gy, x1 + 0.7, 64, fill=SOILD)
    # 위쪽 외벽 아래부: 트래버틴 블록 단(모르타르 없이 쌓음)
    wx0, wx1 = x0 + 5.5, x1 - 5.5
    rows = 4
    rh = (gy - 1.5) / rows
    for r in range(rows):
        yb = gy - (r + 1) * rh
        sub.rect(wx0, yb, wx1, yb + rh, fill=TRAV_D)
        off = 0.0 if r % 2 == 0 else 5.0
        xs = wx0 - off
        while xs < wx1:
            xa, xb = max(wx0, xs), min(wx1, xs + 10.0)
            if xb - xa > 0.8:
                sub.rect(xa + 0.15, yb + 0.15, xb - 0.15, yb + rh - 0.15, fill=TRAV)
                sub.rect(xa + 0.15, yb + 0.15, xb - 0.15, yb + 0.9, fill=TRAV_L)
                sub.rect(xa + 0.15, yb + rh - 0.7, xb - 0.15, yb + rh - 0.15, fill=shade(TRAV, 0.88))
            xs += 10.0
    # 벽 아래 넓힌 밑단(기초 위 첫 단)
    sub.rect(wx0 - 1.6, gy - 1.0, wx1 + 1.6, gy + 1.1, fill=TRAV_D)
    sub.rect(wx0 - 1.6, gy - 1.0, wx1 + 1.6, gy - 0.2, fill=TRAV)


# ─────────────────────────── 2. 판테온 돔 단면 쐐기 ───────────────────────────
def fig_pantheon(sub, vc, vr, rng):
    """돔 단면 쐐기(v2 'Ⓑ 판테온 돔의 가벼운 골재'): 양쪽 아래=무거운 트래버틴·응회암 조각, 꼭대기=스코리아·부석 (화산-Support 603행 S77, 판테온 SOURCES)"""
    sub.rect(-2, -2, 64, 64, fill=SANDBG)
    cx, cy = 31.0, 62.0
    r0, r1 = 17.0, 46.0
    A0, A1 = 212.0, 328.0
    # 돔 안쪽 빈 공간
    sub.ell(cx, cy, r0, r0, fill=shade(SANDBG, 0.93))
    sub.rect(-2, cy, 64, 64, fill=shade(SANDBG, 0.93))
    # 구역(아래→위) : 각도 경계
    zones = [
        # (a0, a1, 모르타르색, 조각색 목록, 크기, 밀도)
        (205, 228, shade(MORT, 0.92), [TRAV_L, TRAV, TUFF], 3.3, 9),
        (228, 252, MORT, [TUFF, YTUFF, TRAV], 2.5, 15),
        (252, 288, shade(MORT, 1.04), [YTUFF, SCORIA, TUFF], 1.8, 22),
    ]
    zones.append((288, 312, shade(MORT, 1.04), [YTUFF, SCORIA, PUMICE], 1.8, 22))
    zones.append((312, 335, shade(MORT, 0.92), [TRAV_L, TRAV, TUFF], 3.3, 9))
    zones = [(205, 228, shade(MORT, 0.9), [TRAV_L, TRAV, TUFF], 3.4, 7),
             (228, 252, shade(MORT, 0.96), [TUFF, YTUFF, TRAV], 2.5, 13),
             (252, 270, shade(MORT, 1.04), [YTUFF, SCORIA, PUMICE], 1.8, 17),
             (270, 288, shade(MORT, 1.08), [SCORIA, PUMICE, PUMICE], 1.4, 20),
             (288, 308, shade(MORT, 1.04), [YTUFF, SCORIA, PUMICE], 1.8, 17),
             (308, 335, shade(MORT, 0.9), [TUFF, YTUFF, TRAV], 2.5, 13)]
    # 대칭 쐐기: 한쪽(205~270)을 위로 갈수록 가볍게, 반대쪽은 거울
    bands = [(0, 20, 0), (20, 40, 1), (40, 65, 2)]
    zs = [(0, 22, shade(MORT, 0.88), [TRAV_L, TRAV, TUFF], 3.5, 6),
          (22, 46, shade(MORT, 0.95), [TUFF, YTUFF, TRAV], 2.6, 11),
          (46, 65, shade(MORT, 1.04), [YTUFF, SCORIA, PUMICE], 1.8, 16)]
    zs_top = [(65, 90, shade(MORT, 1.08), [SCORIA, PUMICE, PUMICE, SCORIA], 1.35, 20)]
    span = A1 - A0                  # 130도, 한쪽 65도
    allz = []
    for (a, b, mc, cl, sz, nn) in zs:
        allz.append((A0 + a, A0 + b, mc, cl, sz, nn))
    for (a, b, mc, cl, sz, nn) in zs_top:
        allz.append((A0 + a, A0 + b, mc, cl, sz, nn))
    for (a, b, mc, cl, sz, nn) in zs[::-1]:
        allz.append((A1 - b, A1 - a, mc, cl, sz, nn))
    for (a0, a1, mc, cl, sz, nn) in allz:
        sub.poly(_sector(cx, cy, r0, r1, a0, a1, 16), fill=mc)
        light = sz < 2.0
        tot = nn * (24 if light else 22) // 22 * 2
        # 방사 줄 수 대신 층(고리) 방향으로 3줄: 조각 배치
        rings = [r0 + 3.5, r0 + (r1 - r0) * 0.37, r0 + (r1 - r0) * 0.63, r1 - 3.5] if light else [r0 + 4.0, (r0 + r1) / 2.0, r1 - 4.0]
        cnt = 0
        for rr in rings:
            arcl = math.radians(a1 - a0) * rr
            n = max(2, int(arcl / (sz * (1.5 if light else 1.9))))
            for i in range(n):
                th = a0 + (a1 - a0) * (i + 0.5 + (rng.random() - 0.5) * 0.5) / n
                r_ = rr + (rng.random() - 0.5) * 3.4
                x = cx + r_ * math.cos(math.radians(th))
                y = cy + r_ * math.sin(math.radians(th))
                col = rng.choice(cl)
                k = sz * (0.7 + rng.random() * 0.5)
                if col in (SCORIA, PUMICE):
                    k *= 0.85
                _frag(sub, x, y, k, k * 0.72, col, rng, rot=math.radians(th + 90), nv=7)
                if col in (SCORIA, PUMICE):           # 기공(작은 구멍)
                    for q in range(2):
                        sub.ell(x + (rng.random() - 0.5) * k, y + (rng.random() - 0.5) * k * 0.7, 0.2, 0.17,
                                fill=(236, 224, 210) if col == SCORIA else (190, 182, 168))
                cnt += 1
        for q in range(14):
            th = math.radians(a0 + rng.random() * (a1 - a0))
            r_ = r0 + 1 + rng.random() * (r1 - r0 - 2)
            sub.ell(cx + r_ * math.cos(th), cy + r_ * math.sin(th), 0.28, 0.2, fill=shade(mc, 0.74))
    # 구역 경계 줄(얇게)
    for (a0, a1, *_r) in allz:
        for a in (a0, a1):
            sub.line([(cx + r0 * math.cos(math.radians(a)), cy + r0 * math.sin(math.radians(a))),
                      (cx + r1 * math.cos(math.radians(a)), cy + r1 * math.sin(math.radians(a)))], shade(MORT, 0.7), 0.25, joint=False)
    # 안쪽·바깥 가장자리 띠(3단 색으로 두께 표현)
    sub.pie(cx, cy, r1, r1, A0, A1, outline=shade(MORT, 0.6), lw=0.3) if False else None
    sub.poly(_sector(cx, cy, r1 - 0.7, r1, A0, A1, 40), fill=shade(MORT, 0.72))
    sub.poly(_sector(cx, cy, r0, r0 + 0.7, A0, A1, 40), fill=shade(MORT, 0.72))
    # 쐐기 양쪽 절단면 음영(안쪽 어두운 줄)
    for a in (A0, A1):
        sub.line([(cx + r0 * math.cos(math.radians(a)), cy + r0 * math.sin(math.radians(a))),
                  (cx + r1 * math.cos(math.radians(a)), cy + r1 * math.sin(math.radians(a)))], shade(MORT, 0.55), 0.45, joint=False)


# ─────────────────────────── 3. 트라야누스 시장 대회랑 볼트 ───────────────────────────
def fig_markets(sub, vc, vr, rng):
    """벽돌 외피 + 콘크리트 볼트 단면, 오른쪽 아래 확대 렌즈에 석회 알갱이와 판상 결정(스트래틀링가이트)이 균열을 막는 모습 (화산-Support 114·541·542행, Jackson 2014)"""
    sub.rect(-2, -2, 64, 64, fill=SANDBG)
    cx, cy = 27.0, 38.0
    ri, ro = 10.0, 25.0
    bt = 2.8                                   # 벽돌 외피 두께
    # 기둥(양쪽 벽) 먼저
    wl0, wl1 = cx - ro, cx - ri
    wr0, wr1 = cx + ri, cx + ro
    for (a, b) in ((wl0 - 4, wl1), (wr0, wr1 + 4)):
        sub.rect(a, cy, b, 64, fill=MORT)
    # 속 빈 공간
    sub.rect(wl1, cy, wr0, 64, fill=shade(SANDBG, 0.9))
    sub.ell(cx, cy, ri, ri, fill=shade(SANDBG, 0.9))
    # 볼트 콘크리트 고리
    sub.poly(_sector(cx, cy, ri, ro, 180, 360, 40), fill=MORT)
    # 콘크리트 속 알갱이(벽돌 조각·응회암)
    for i in range(34):
        th = math.radians(180 + rng.random() * 180)
        r_ = ri + bt + 1.2 + rng.random() * (ro - ri - 2 * bt - 2.4)
        col = rng.choice((TUFF, BRICK_D, TRAV, TUFF))
        _frag(sub, cx + r_ * math.cos(th), cy + r_ * math.sin(th), 1.4 + rng.random() * 0.9, 1.0 + rng.random() * 0.5, col, rng, rot=th + 1.57, nv=6)
    for (x0_, x1_) in ((wl0 - 4 + bt, wl1 - bt), (wr0 + bt, wr1 + 4 - bt)):
        y = cy + 2.0
        while y < 62:
            x = x0_ + 1.2 + rng.random() * 2
            while x < x1_ - 1.2:
                w = 1.3 + rng.random() * 0.9
                col = rng.choice((TUFF, BRICK_D, TRAV))
                _frag(sub, x + w, y, w, 0.9, col, rng, nv=6)
                x += 2 * w + 0.8 + rng.random()
            y += 3.6
    # 벽돌 외피: 볼트 위·아래 + 벽 바깥면(방사 방향 벽돌 줄)
    def brick_arc(rr0, rr1, a0, a1, n):
        for i in range(n):
            u0 = a0 + (a1 - a0) * i / n
            u1 = a0 + (a1 - a0) * (i + 1) / n
            col = (BRICK, BRICK_L, BRICK_D)[i % 3] if i % 3 else BRICK
            sub.poly(_sector(cx, cy, rr0, rr1, u0 + 0.35, u1 - 0.35, 3), fill=BRICK)
            sub.poly(_sector(cx, cy, rr1 - 0.8, rr1, u0 + 0.35, u1 - 0.35, 3), fill=BRICK_L)
            sub.poly(_sector(cx, cy, rr0, rr0 + 0.7, u0 + 0.35, u1 - 0.35, 3), fill=BRICK_D)
    sub.poly(_sector(cx, cy, ro - bt, ro, 180, 360, 40), fill=BRICK_D)
    sub.poly(_sector(cx, cy, ri, ri + bt, 180, 360, 40), fill=BRICK_D)
    brick_arc(ro - bt, ro, 180, 360, 34)
    brick_arc(ri, ri + bt, 180, 360, 20)
    def brick_col(xa, xb, y0_, y1_):
        sub.rect(xa, y0_, xb, y1_, fill=BRICK_D)
        y = y0_
        k = 0
        while y < y1_:
            h = min(1.4, y1_ - y)
            sub.rect(xa + 0.1, y + 0.15, xb - 0.1, y + h - 0.1, fill=BRICK)
            sub.rect(xa + 0.1, y + 0.15, xb - 0.1, y + 0.55, fill=BRICK_L)
            sub.line([(xa + (1.4 if k % 2 else 0.6) + 0.0, y + 0.15), (xa + (1.4 if k % 2 else 0.6), y + h)], BRICK_D, 0.2, joint=False)
            y += 1.4
            k += 1
    brick_col(wl0 - 4, wl0 - 4 + bt, cy, 64)
    brick_col(wl1 - bt, wl1, cy, 64)
    brick_col(wr0, wr0 + bt, cy, 64)
    brick_col(wr1 + 4 - bt, wr1 + 4, cy, 64)
    # 확대 렌즈
    lx, ly, lr = 38.0, 45.0, 13.4
    ax, ay = cx + 17.0 * math.cos(math.radians(335)), cy + 17.0 * math.sin(math.radians(335))
    sub.line([(ax, ay), (lx - 6, ly - 10.5)], shade(BRICK_D, 0.8), 0.3, joint=False)
    sub.ell(ax, ay, 0.8, 0.8, fill=shade(BRICK_D, 0.8))
    sub.ell(lx, ly, lr + 0.7, lr + 0.7, fill=shade(BRICK_D, 0.8))
    sub.ell(lx, ly, lr, lr, fill=(196, 182, 160))
    # 렌즈 안쪽: 모래알 점 + 석회 알갱이 + 균열 + 판상 결정
    for i in range(46):
        a = rng.random() * 6.283
        d = lr * 0.92 * math.sqrt(rng.random())
        sub.ell(lx + d * math.cos(a), ly + d * math.sin(a), 0.3, 0.22, fill=shade(MORT, 0.76 if i % 2 else 1.1))
    # 석회 알갱이(흰, 오른쪽 아래)
    gx, gy2, gr = lx + 3.6, ly + 3.6, 4.0
    pts = [(gx + gr * (0.88 + 0.12 * math.sin(j * 2.3)) * math.cos(j * math.pi / 7), gy2 + gr * 0.82 * (0.9 + 0.1 * math.cos(j * 1.7)) * math.sin(j * math.pi / 7)) for j in range(14)]
    sub.poly([(x + 0.5, y + 0.6) for x, y in pts], fill=(186, 178, 164))
    sub.poly(pts, fill=LIME)
    sub.poly([(gx + (x - gx) * 0.5 - 1.0, gy2 + (y - gy2) * 0.5 - 1.2) for x, y in pts[:9]], fill=(255, 255, 255))
    # 균열: 위 왼쪽에서 들어와 석회 알갱이 쪽으로, 판상 결정 띠에서 멈춤
    crack = [(lx - 12.0, ly - 6.5), (lx - 9.8, ly - 5.4), (lx - 8.0, ly - 5.0), (lx - 6.2, ly - 3.6), (lx - 4.6, ly - 3.0)]
    sub.line(crack, (92, 68, 50), 0.6)
    sub.line([(crack[3][0], crack[3][1]), (crack[3][0] - 1.4, crack[3][1] + 1.8)], SOILD, 0.3)
    # 판상 결정: 균열 주변 + 알갱이 둘레에 가는 판(길쭉한 육각판) 여러 개, 균열을 가로질러 박힘
    tipx, tipy = crack[-1]
    plates = []
    for i in range(8):
        a = rng.random() * 6.283
        d = 0.8 + rng.random() * 2.8
        plates.append((tipx + d * math.cos(a) * 1.05, tipy + d * math.sin(a) * 0.8, rng.random() * math.pi))
    for i in range(7):
        a = math.radians(170 + 24 * i + rng.random() * 8)
        plates.append((gx + (gr + 0.7) * math.cos(a), gy2 + (gr * 0.85 + 0.7) * math.sin(a), a + 1.57 + (rng.random() - 0.5) * 0.7))
    for (px, py, ang) in plates:
        if (px - lx) ** 2 + (py - ly) ** 2 > (lr - 1.0) ** 2:
            continue
        L, W = 1.3 + rng.random() * 0.5, 0.2
        c, s = math.cos(ang), math.sin(ang)
        quad = [(px + c * L - s * W, py + s * L + c * W), (px + c * L + s * W, py + s * L - c * W),
                (px - c * L + s * W, py - s * L - c * W), (px - c * L - s * W, py - s * L + c * W)]
        sub.poly([(x + 0.15, y + 0.18) for x, y in quad], fill=(120, 104, 86))
        sub.poly(quad, fill=(255, 254, 250))
