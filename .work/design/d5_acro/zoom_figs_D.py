"""확대 창 그림 D: 수도교 수로 단면 / 네로 거상 받침 단면 / 로마 콘크리트 마스터 단면 (가상 판 62 mm, 중심 31, 반지름 30)"""
import sys, math
sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/lib")
from common import *

# 팔레트(포스터 공통색과 같은 재료는 같은 색)
MORT = (200, 190, 172)      # 모르타르 바탕
MORT_L = (222, 212, 194)
MORT_D = (176, 164, 146)
LIME = (252, 251, 246)      # 석회 알갱이
TUFF_C = (166, 136, 102)    # 응회암
SCORIA = (150, 90, 74)      # 스코리아(붉은 화산 골재)
PUMICE = (214, 204, 178)    # 부석
BRICK_C = (192, 108, 80)
BRICK_CL = (210, 128, 96)
BRICK_CD = (156, 84, 62)
TRAV_C = (208, 186, 144)
SKY = (238, 226, 194)
SOIL_C = (126, 98, 62)
WATER = (104, 150, 196)
WATER_L = (150, 194, 226)
WATER_D = (70, 112, 160)
SIGNINO = (206, 140, 112)   # 기와 가루 방수 모르타르
BRONZE = (150, 112, 62)


def _blob(sub, rng, cx, cy, r, col, nv=None, sq=0.86, lime=False):
    nv = nv or (6 + int(rng.random() * 3))
    ph = rng.random() * 6.28
    pts = []
    for j in range(nv):
        t = ph + 2 * math.pi * j / nv + (rng.random() - 0.5) * 0.4
        q = r * (0.78 + rng.random() * 0.34)
        pts.append((cx + q * math.cos(t), cy + q * sq * math.sin(t)))
    off = max(0.35, r * 0.11)
    sub.poly([(x + off, y + off) for x, y in pts], fill=shade(col, 0.74))
    sub.poly(pts, fill=col)
    sub.ell(cx - r * 0.28, cy - r * 0.3, r * 0.34, r * 0.24, fill=(255, 255, 255) if lime else shade(col, 1.14))
    return pts


def _scatter(sub, rng, inside, n, rmin, rmax, cols, placed, gap=0.5, lime_every=0, tries=60):
    """inside(x, y, r) -> bool 안에 완전히 들어오는 자리에만 알갱이를 놓는다(겹침 방지)"""
    cnt = 0
    for i in range(n):
        for _ in range(tries):
            r = rmin + (rmax - rmin) * rng.random() ** 1.6
            x, y = rng.uniform(0, 62), rng.uniform(0, 62)
            if not inside(x, y, r):
                continue
            if any(math.hypot(x - a, y - b) < r + s + gap for a, b, s in placed):
                continue
            placed.append((x, y, r))
            lime = lime_every and (cnt % lime_every == 0)
            c = LIME if lime else cols[cnt % len(cols)]
            _blob(sub, rng, x, y, r, c, lime=bool(lime))
            if not lime and r > 2.0 and cnt % 3 == 0:                     # 골재 속 작은 알갱이(결)
                for k in range(3):
                    sub.ell(x + (rng.random() - 0.5) * r, y + (rng.random() - 0.5) * r * 0.8, 0.3, 0.26, fill=shade(c, 0.82))
            cnt += 1
            break
    return cnt


def _speckle(sub, rng, inside, n, base=MORT):
    for i in range(n):
        x, y = rng.uniform(0, 62), rng.uniform(0, 62)
        if inside(x, y, 0.5):
            sub.ell(x, y, 0.3 + rng.random() * 0.3, 0.25 + rng.random() * 0.2, fill=(shade(base, 0.86), shade(base, 1.1), MORT_D)[i % 3])


def _crack(sub, rng, x, y, ang, n, step, col=(130, 118, 102), lw=0.3):
    pts = [(x, y)]
    for _ in range(n):
        ang += (rng.random() - 0.5) * 0.9
        x += step * math.cos(ang)
        y += step * math.sin(ang)
        pts.append((x, y))
    sub.line(pts, col, lw, joint=False)


def _hex(sub, x, y, r, col=LIME):
    sub.poly([(x + r * math.cos(k * math.pi / 3), y + 0.86 * r * math.sin(k * math.pi / 3)) for k in range(6)], fill=col)


def _concrete_in(sub, rng, inside, area_scale=1.0, mort_fill=True):
    """직사각·원 등 임의 영역(inside)에 콘크리트 단면(모르타르+골재+석회 알갱이)을 채운다"""
    _speckle(sub, rng, inside, int(260 * area_scale))
    placed = []
    _scatter(sub, rng, inside, int(34 * area_scale), 1.6, 4.2, [TUFF_C, SCORIA, TRAV_C, (150, 146, 138), BRICK_C, PUMICE], placed, lime_every=5)
    return placed


# ───────────────────────── 3. 로마 콘크리트 마스터 단면 ─────────────────────────
def fig_concrete_master(sub, vc, vr, rng):
    """큰 원 전체: 모르타르 바탕 + 화산 골재(응회암·스코리아·부석·벽돌 조각·트래버틴) + 흰 석회 알갱이(균열·결정) + 기공"""
    R = vr
    inside = lambda x, y, r: math.hypot(x - vc, y - vc) + r < R * 0.985
    sub.ell(vc, vc, R + 1, R + 1, fill=MORT)
    # 모르타르 질감: 3단 반점 + 미세 모래
    for i in range(900):
        a = rng.random() * 6.283
        d = R * math.sqrt(rng.random()) * 1.02
        x, y = vc + d * math.cos(a), vc + d * math.sin(a)
        c = (MORT_D, MORT_L, shade(MORT, 0.93), (214, 196, 170))[i % 4]
        sub.ell(x, y, 0.22 + rng.random() * 0.3, 0.2 + rng.random() * 0.2, fill=c)
    placed = []
    # 큰 골재 먼저, 그 틈에 중간·작은 골재
    big = [TUFF_C, SCORIA, (150, 146, 138), BRICK_C, TRAV_C, (112, 94, 84)]
    _scatter(sub, rng, inside, 15, 4.2, 6.2, big, placed, gap=1.2)
    _scatter(sub, rng, inside, 44, 2.3, 3.8, big + [PUMICE, PUMICE], placed, gap=0.8)
    _scatter(sub, rng, inside, 60, 1.1, 2.0, big + [PUMICE], placed, gap=0.5)
    # 큰 골재 속 기공(부석) 표현
    for (x, y, r) in placed:
        if r > 3.6 and rng.random() < 0.6:
            for k in range(4):
                sub.ell(x + (rng.random() - 0.5) * r * 1.0, y + (rng.random() - 0.5) * r * 0.8, 0.38, 0.32, fill=(236, 226, 204))
    # 흰 석회 알갱이(핵심): 큰 것 + 중간, 일부는 금이 가고 금을 따라 결정이 자람
    limes = []
    lime_in = lambda x, y, r: inside(x, y, r)
    cl = []
    for i in range(14):
        for _ in range(80):
            r = 2.0 + rng.random() * 3.0
            a = rng.random() * 6.283
            d = R * 0.86 * math.sqrt(rng.random())
            x, y = vc + d * math.cos(a), vc + d * math.sin(a)
            if not lime_in(x, y, r + 0.6):
                continue
            if any(math.hypot(x - p, y - q) < r + s + 0.3 for p, q, s in limes):
                continue
            limes.append((x, y, r))
            break
    for i, (x, y, r) in enumerate(limes):
        _blob(sub, rng, x, y, r, LIME, nv=9, sq=0.88, lime=True)
        if i % 3 == 0:                                      # 금이 간 알갱이
            _crack(sub, rng, x - r * 0.6, y - r * 0.3, 0.3, 4, r * 0.35, (150, 140, 126), 0.28)
            _crack(sub, rng, x + r * 0.1, y - r * 0.7, 1.6, 3, r * 0.3, (150, 140, 126), 0.28)
        if i % 3 == 1:                                      # 금을 메운 새 결정(자가치유)
            _hex(sub, x + r * 0.45, y + r * 0.1, 0.62, (255, 255, 252))
            _hex(sub, x + r * 0.05, y + r * 0.45, 0.5, (236, 234, 224))
            _hex(sub, x - r * 0.4, y + r * 0.15, 0.45, (244, 242, 234))
        if i % 3 == 2:                                      # 알갱이 가장자리 반응띠
            sub.ell(x, y, r * 1.18, r * 1.06, outline=(226, 214, 190), lw=0.3)
    # 모르타르 속 가는 균열 + 기공
    for i in range(7):
        a = rng.random() * 6.283
        d = R * 0.8 * math.sqrt(rng.random())
        _crack(sub, rng, vc + d * math.cos(a), vc + d * math.sin(a), rng.random() * 6.283, 4, 1.2, (150, 138, 120), 0.25)
    for i in range(30):
        a = rng.random() * 6.283
        d = R * 0.92 * math.sqrt(rng.random())
        x, y = vc + d * math.cos(a), vc + d * math.sin(a)
        if all(math.hypot(x - p, y - q) > r + 0.5 for p, q, r in placed + limes):
            sub.ell(x, y, 0.38, 0.32, fill=(120, 106, 92))
            sub.ell(x - 0.08, y - 0.08, 0.16, 0.13, fill=MORT_L)


# ───────────────────────── 1. 수도교 수로 단면 ─────────────────────────
def _courses(sub, x0, y0, x1, y1, rowh, bw, col, rng, joint=None):
    """돌·벽돌 줄쌓기 면: 한 단씩 엇갈려 3단 색(밝음·중간·어두움)으로"""
    joint = joint or shade(col, 0.72)
    r = 0
    y = y0
    while y < y1 - 0.05:
        h = min(rowh, y1 - y)
        x = x0 - (bw * 0.5 if r % 2 else 0.0)
        while x < x1:
            xa, xb = max(x, x0), min(x + bw, x1)
            if xb - xa > 0.15:
                tone = (shade(col, 1.07), col, shade(col, 0.93))[int(rng.random() * 3)]
                sub.rect(xa, y, xb, y + h, fill=joint)
                sub.rect(xa + 0.2, y + 0.2, xb - 0.2, y + h - 0.2, fill=tone)
                sub.rect(xa + 0.2, y + 0.2, xb - 0.2, y + 0.55, fill=shade(tone, 1.1))
            x += bw
        y += rowh
        r += 1


def fig_aqueduct(sub, vc, vr, rng):
    """수도교 절개: 위=수로(물·방수 모르타르 층·콘크리트/잡석 몸체·덮개돌), 아래=아치 위 구조(교각·아치 돌)"""
    sub.rect(-2, -2, 64, 64, fill=SKY)
    # 먼 하늘의 얇은 층
    sub.rect(-2, 6, 64, 8.5, fill=shade(SKY, 0.96))
    # 몸체(수로를 둘러싼 콘크리트·잡석 단면) x 6~56, y 11~36
    bx0, bx1, by0, by1 = 6.0, 56.0, 12.0, 37.0
    sub.rect(bx0, by0, bx1, by1, fill=MORT)
    ins = lambda x, y, r: (bx0 + 5.2 < x - r and x + r < bx1 - 5.2 and by0 + 1.0 < y - r and y + r < by1 - 1.0
                           and not (15.0 < x + r and x - r < 47.0 and y - r < 31.5))
    _speckle(sub, rng, lambda x, y, r: bx0 + 5 < x < bx1 - 5 and by0 + 1 < y < by1 - 1, 220)
    pl = []
    _scatter(sub, rng, ins, 20, 1.5, 3.0, [TUFF_C, TRAV_C, (150, 146, 138), SCORIA], pl, lime_every=6)
    # 양쪽 겉면: 벽돌 마감
    _courses(sub, bx0, by0, bx0 + 5.0, by1, 1.9, 4.0, BRICK_C, rng)
    _courses(sub, bx1 - 5.0, by0, bx1, by1, 1.9, 4.0, BRICK_C, rng)
    # 방수 모르타르 층(수로 안쪽 바닥·양 벽, 기와 가루 섞인 붉은 분홍색)
    cx0, cx1, cy0, cy1 = 15.0, 47.0, 12.0, 31.5          # 수로 바깥 윤곽(라이닝 포함)
    t = 2.6
    sub.rect(cx0, cy0, cx1, cy1, fill=SIGNINO)
    for i in range(160):
        x, y = rng.uniform(cx0, cx1), rng.uniform(cy0, cy1)
        sub.ell(x, y, 0.22 + rng.random() * 0.2, 0.2 + rng.random() * 0.15, fill=(BRICK_C, shade(SIGNINO, 1.12), shade(SIGNINO, 0.85))[i % 3])
    for i in range(18):                                    # 기와 가루 조각
        x, y = rng.uniform(cx0 + 0.5, cx1 - 0.5), rng.uniform(cy0 + 0.5, cy1 - 0.5)
        if cx0 + t < x < cx1 - t and y < cy1 - t:
            continue
        sub.poly([(x, y), (x + 0.9, y - 0.2), (x + 0.7, y + 0.6), (x - 0.2, y + 0.5)], fill=BRICK_CD)
    # 물이 흐르는 수로(사각 단면) 안쪽
    wx0, wx1, wy0, wy1 = cx0 + t, cx1 - t, cy0 - 1, cy1 - t
    sub.rect(wx0, wy0, wx1, wy1, fill=SKY)                 # 물 위 빈 공간(공기)
    sy = 19.0                                              # 수면
    sub.rect(wx0, sy, wx1, wy1, fill=WATER)
    sub.rect(wx0, sy + 4.2, wx1, wy1, fill=WATER_D)
    sub.rect(wx0, sy, wx1, sy + 0.8, fill=WATER_L)
    for k in range(4):                                     # 물결
        x = wx0 + 3.0 + k * 7.4
        sub.arc(x, sy + 1.6, 2.2, 0.9, 180, 360, WATER_L, 0.3)
        sub.arc(x + 3.2, sy + 5.0, 2.0, 0.8, 180, 360, WATER_L, 0.3)
    for k in range(3):                                     # 흐름 방향 점
        sub.ell(wx0 + 5 + k * 9, sy + 8.0, 0.5, 0.35, fill=WATER_L)
    # 덮개 돌(수로 위): 평평한 석판 2장
    sub.rect(cx0 - 1.4, 9.0, cx1 + 1.4, 12.0, fill=shade(TRAV_C, 0.82))
    sub.rect(cx0 - 1.4, 9.0, cx1 + 1.4, 9.7, fill=TRAV_C)
    sub.rect(31 - 0.2, 9.0, 31 + 0.2, 12.0, fill=shade(TRAV_C, 0.62))
    # 아래: 아치 위 구조. 교각 + 반원 아치 + 쐐기돌
    ay0 = by1
    sub.rect(2, ay0, 60, 64, fill=TRAV_C)
    _courses(sub, 2, ay0, 60, 64, 3.2, 6.5, TUFF_C, rng)
    ac, ar_in = 31.0, 11.5
    ayc = 48.0
    # 아치 개구부(하늘색) + 반원 돌 고리
    sub.rect(ac - ar_in, ayc, ac + ar_in, 64, fill=SKY)
    sub.pie(ac, ayc, ar_in, ar_in, 180, 360, fill=SKY)
    ring = 3.4
    n = 11
    for i in range(n):
        a0 = math.pi + i * math.pi / n
        a1 = math.pi + (i + 1) * math.pi / n
        ro, ri = ar_in + ring, ar_in
        pts = [(ac + ri * math.cos(a0), ayc + ri * math.sin(a0)), (ac + ro * math.cos(a0), ayc + ro * math.sin(a0)),
               (ac + ro * math.cos(a1), ayc + ro * math.sin(a1)), (ac + ri * math.cos(a1), ayc + ri * math.sin(a1))]
        col = (TRAV_C, shade(TRAV_C, 1.08), shade(TRAV_C, 0.92))[i % 3] if i != n // 2 else shade(TRAV_C, 1.14)
        sub.poly(pts, fill=shade(TRAV_C, 0.62))
        mid = [((p[0] * 0.8 + ac * 0.2), (p[1] * 0.8 + ayc * 0.2)) for p in pts]
        sub.poly(pts, fill=col)
        sub.line(pts[:2], shade(TRAV_C, 0.62), 0.3, joint=False)
    sub.rect(ac - ar_in - ring - 0.1, ayc, ac - ar_in, 64, fill=shade(TUFF_C, 1.02))
    # 아치 개구부 밑의 어두운 안쪽 그늘 면
    sub.rect(ac - ar_in, ayc, ac - ar_in + 1.2, 64, fill=SKY)
    # 몸체와 아치 사이 이음(돌 가로띠)
    sub.rect(2, ay0, 60, ay0 + 1.3, fill=shade(TRAV_C, 0.8))
    sub.rect(2, ay0, 60, ay0 + 0.5, fill=shade(TRAV_C, 1.08))


# ───────────────────────── 2. 네로 거상 받침 단면 ─────────────────────────
def fig_nero(sub, vc, vr, rng):
    """거상 받침 단면: 겉 벽돌 마감 + 속 콘크리트(골재·모르타르) + 위에 청동 거상 발 일부(복원 모식)"""
    sub.rect(-2, -2, 64, 64, fill=SKY)
    # 땅
    sub.rect(-2, 50.5, 64, 64, fill=SOIL_C)
    sub.rect(-2, 50.5, 64, 52.0, fill=shade(SOIL_C, 1.14))
    for i in range(40):
        sub.ell(rng.uniform(0, 62), rng.uniform(53, 62), 0.5 + rng.random() * 0.6, 0.4, fill=(shade(SOIL_C, 0.82), shade(SOIL_C, 1.2))[i % 2])
    # 받침 몸체
    px0, px1, py0, py1 = 11.0, 51.0, 30.0, 50.5
    bw = 5.4
    sub.rect(px0, py0, px1, py1, fill=MORT)
    ins = lambda x, y, r: px0 + bw + 0.5 < x - r and x + r < px1 - bw - 0.5 and py0 + 1.5 < y - r and y + r < py1 - 0.6
    _speckle(sub, rng, lambda x, y, r: px0 + bw < x < px1 - bw and py0 + 1 < y < py1, 260)
    pl = []
    _scatter(sub, rng, ins, 30, 1.4, 3.0, [TUFF_C, BRICK_C, TRAV_C, (150, 146, 138), SCORIA, PUMICE], pl, lime_every=7)
    _courses(sub, px0, py0, px0 + bw, py1, 1.7, 4.6, BRICK_C, rng, joint=BRICK_CD)
    _courses(sub, px1 - bw, py0, px1, py1, 1.7, 4.6, BRICK_C, rng, joint=BRICK_CD)
    # 윗면 벽돌 한 줄(바닥 덮개), 3단 색 띠
    sub.rect(px0 - 1.0, py0 - 1.9, px1 + 1.0, py0, fill=BRICK_CD)
    sub.rect(px0 - 1.0, py0 - 1.9, px1 + 1.0, py0 - 1.2, fill=BRICK_CL)
    sub.rect(px0 - 1.0, py0 - 1.2, px1 + 1.0, py0 - 0.2, fill=BRICK_C)
    # 청동 거상 발 일부: 발바닥 판 + 두 발목(단면, 속이 빈 청동 벽)
    sy0, sy1 = 27.0, py0 - 1.9
    sub.rect(15.0, sy0, 47.0, sy1, fill=shade(BRONZE, 0.7))
    sub.rect(15.0, sy0, 47.0, sy0 + 1.0, fill=shade(BRONZE, 1.18))
    for (x0, x1) in ((18.0, 28.0), (34.0, 44.0)):
        sub.poly([(x0 - 1.0, sy0), (x1 + 1.0, sy0), (x1 - 0.2, 6.0), (x0 + 0.2, 6.0)], fill=shade(BRONZE, 0.7))
        sub.poly([(x0 + 0.4, sy0), (x1 - 0.4, sy0), (x1 - 1.6, 6.0), (x0 + 1.6, 6.0)], fill=BRONZE)
        sub.poly([(x0 + 1.4, sy0), (x0 + 3.0, sy0), (x0 + 3.4, 6.0), (x0 + 2.2, 6.0)], fill=shade(BRONZE, 1.2))
        # 속 빈 공간(어둡게)
        sub.poly([(x0 + 3.4, sy0), (x1 - 3.0, sy0), (x1 - 3.8, 6.0), (x0 + 4.2, 6.0)], fill=(86, 62, 38))
    for k in range(5):
        sub.ell(rng.uniform(17, 45), sy0 + 1.8 + rng.random() * 1.0, 0.4, 0.25, fill=shade(BRONZE, 1.25))
    # 발바닥 판 아래 틈: 받침 윗면과 발판 사이 모르타르 줄
    sub.rect(15.0, sy1 - 0.4, 47.0, sy1, fill=MORT_D)
