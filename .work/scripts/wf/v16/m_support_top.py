# -*- coding: utf-8 -*-
# 로마 콘크리트 A2 와이어프레임 — Support(위 줄·뒤쪽): 카라칼라 욕장(절개)·판테온, Support-2 베수비오와 밑동을 가리는 포도밭 농장
# 담당 패키지: support_top · 이 파일은 담당 워커만 고친다(공용 도구는 common.py, 조립은 main.py).

from common import *
from common import _a
import common as C

# ───────────────────────── 욕장(카라칼라 대응, 열탕실 복원 상상도) ─────────────────────────
def draw_bath(L, cx, cy, w=64.0):
    """절개 욕장: 뒤 벽 두 면 전체 높이 + 앞 벽 낮게, 지붕 제거, 열주·벽감 조각상, 코퍼 반쪽 돔(콘크리트 두께, 오큘러스는 점선=복원 추정),
    큰 아치창 빛, 청록 욕조(열탕 구역에만 증기)와 목욕객, 하이포코스트 절개."""
    sl = slab(L, cx, cy, w, t=6.5, top=(222, 212, 186))
    # 하이포코스트(바닥 밑 난방) 절개: 받침 정면 왼쪽 측면에 벽돌 기둥(pilae)과 아궁이가 드러난다
    pa, pb = sl["L"], sl["B"]
    def lp(t):
        return (pa[0] + (pb[0] - pa[0]) * t, pa[1] + (pb[1] - pa[1]) * t)
    n0, n1 = lp(0.18), lp(0.74)
    L.poly([(n0[0], n0[1] + 1.2), (n1[0], n1[1] + 1.2), (n1[0], n1[1] + 5.6), (n0[0], n0[1] + 5.6)], fill=(70, 46, 32), outline=(40, 28, 20), lw=0.15)
    for i in range(7):
        q = lp(0.22 + i * 0.07)
        L.rect(q[0] - 0.6, q[1] + 1.4, q[0] + 0.6, q[1] + 5.4, fill=(196, 116, 80))
    q = lp(0.76)
    L.ell(q[0], q[1] + 3.6, 1.5, 1.2, fill=(244, 156, 60))
    iso, S = iso_of_slab(L, cx, cy, w)
    m = 3.0
    X0, Y0, X1, Y1 = m, m, S - m, S - m
    HZ = 21.0
    HF = 5.5
    WALL = ((226, 204, 164), (214, 190, 148), (192, 166, 126))
    # 바닥
    iso.rect3(X0, Y0, X1, Y1, 0.0, (238, 230, 208), ol=(120, 96, 66), lw=0.2)
    # 뒤 벽 두 면(두께 1.4): NW 벽(X=X0, +X향 면), NE 벽(Y=Y0, +Y향 면)
    iso.box(X0, Y0, 0, X0 + 1.4, Y1, HZ, WALL, ol=(120, 96, 66), lw=0.2)
    iso.box(X0, Y0, 0, X1, Y0 + 1.4, HZ, WALL, ol=(120, 96, 66), lw=0.2)
    # NE 벽 가운데: 코퍼 반쪽 돔이 있는 아프시스 개구(큰 아치) — 콘크리트 두께 링 + 안쪽 코퍼
    cu = (X0 + X1) / 2.0 + 4.0
    r_o, r_i = 9.0, 6.6
    z_spr = 7.0
    ring = []
    for i in range(0, 25):
        a = math.pi * i / 24.0
        ring.append((cu + r_o * math.cos(a), z_spr + r_o * math.sin(a)))
    ring_in = [(cu + r_i * math.cos(math.pi * i / 24.0), z_spr + r_i * math.sin(math.pi * i / 24.0)) for i in range(25)]
    iso.fpoly("L", 0, Y0 + 1.4, 0, [(cu - r_o, 0)] + ring + [(cu + r_o, 0)], fill=CONC, ol=(100, 94, 84), lw=0.2)
    iso.fpoly("L", 0, Y0 + 1.4, 0, [(cu - r_i, 0)] + ring_in + [(cu + r_i, 0)], fill=(246, 238, 214), ol=(150, 130, 98), lw=0.15)
    for k in range(1, 4):                 # 코퍼: 동심 반원(얕은 격자)
        rr = r_i * k / 4.0
        iso.fpoly("L", 0, Y0 + 1.4, 0, [(cu + rr * math.cos(math.pi * i / 16.0), z_spr + rr * math.sin(math.pi * i / 16.0)) for i in range(17)], fill=None, ol=(170, 146, 108), lw=0.12)
    for a in range(20, 180, 22):          # 코퍼: 방사선
        r = math.radians(a)
        iso.fpoly("L", 0, Y0 + 1.4, 0, [(cu, z_spr), (cu + r_i * math.cos(r), z_spr + r_i * math.sin(r))], fill=None, ol=(170, 146, 108), lw=0.1)
    # 오큘러스(복원 추정): 점선 타원 + 점선 빛줄기
    ox, oy = iso.p(cu, Y0 + 1.4, z_spr + r_i * 0.9)
    L.ell(ox, oy, 1.4, 0.8, outline=(150, 120, 60), lw=0.2)
    # 돌 두께 단면의 골재 점
    for i in range(10):
        a = math.pi * (0.1 + 0.8 * rnd())
        rr = r_i + 0.4 + rnd() * (r_o - r_i - 0.8)
        px, py = iso.face("L", 0, Y0 + 1.4, 0, [(cu + rr * math.cos(a), z_spr + rr * math.sin(a))])[0]
        L.ell(px, py, 0.32, 0.28, fill=(228, 222, 206))
    # NW 벽: 큰 아치창 3개(빛이 들어오는 창) + 벽감 조각상 2개
    for j, vy in enumerate((6.5, 14.5, 22.5)):
        iso.arch("R", X0 + 1.4, 0, 9.5, vy - 2.2, vy + 2.2, 0, 5.0, (252, 248, 226), (140, 112, 76))
    for vy in (10.5, 18.5):
        iso.arch("R", X0 + 1.4, 0, 0, vy - 1.6, vy + 1.6, 1.0, 4.4, (214, 190, 150), (140, 112, 76))
        px, py = iso.face("R", X0 + 1.4, 0, 0, [(vy, 2.0)])[0]
        L.ell(px, py - 2.0, 0.8, 0.8, fill=(248, 244, 236))
        L.rect(px - 0.7, py - 1.3, px + 0.7, py + 0.9, fill=(248, 244, 236))
    # 열주(NE 벽 앞, 냉탕 쪽 장축): 기둥 5개
    for i in range(5):
        X = X0 + 2.0 + i * 3.4
        Y = Y0 + 4.0
        bx, by = iso.p(X, Y, 0.0)
        L.rect(bx - 0.9, by - 14.0, bx + 0.9, by, fill=(244, 236, 214), outline=(150, 126, 92), lw=0.14)
        L.rect(bx - 1.5, by - 15.2, bx + 1.5, by - 14.0, fill=(236, 224, 196), outline=(150, 126, 92), lw=0.14)
    # 욕조(청록): 열탕 구역 + 냉탕 구역 구분
    pool = [(X0 + 3, Y0 + 9), (X1 - 4, Y0 + 9), (X1 - 4, Y1 - 4), (X0 + 3, Y1 - 4)]
    iso.poly3([(a, b, 0.2) for a, b in pool], fill=(70, 178, 196), ol=(36, 120, 140), lw=0.25)
    iso.poly3([(X1 - 12, Y0 + 9, 0.3), (X1 - 4, Y0 + 9, 0.3), (X1 - 4, Y1 - 4, 0.3), (X1 - 12, Y1 - 4, 0.3)], fill=(54, 164, 186), ol=None)
    # 증기: 열탕(오른쪽) 한 구역에만
    sx, sy = iso.p(X1 - 8, (Y0 + Y1) / 2.0 + 2, 0.3)
    steam(L, sx, sy - 1.0, 4, 2.2)
    # 빛줄기(큰 창에서) — 반투명
    with_a = (255, 244, 190, 90)
    bx0, by0 = iso.face("R", X0 + 1.4, 0, 9.5, [(14.5, 0)])[0]
    L.poly([(bx0 - 2.0, by0 - 3.0), (bx0 + 2.0, by0 - 3.0), (bx0 + 12.0, by0 + 12.0), (bx0 + 4.0, by0 + 12.0)], fill=with_a)
    # 목욕객 6명(머리+어깨)
    for (X, Y) in [(X0 + 8, Y0 + 14), (X0 + 11, Y0 + 18), (X0 + 14, Y0 + 12), (X1 - 9, Y0 + 14), (X1 - 7, Y0 + 18), (X1 - 11, Y0 + 21)]:
        px, py = iso.p(X, Y, 0.5)
        L.ell(px, py - 1.0, 0.95, 0.95, fill=(214, 156, 120))
        L.ell(px, py + 0.3, 1.5, 0.7, fill=(236, 196, 160))
    # 앞 벽 두 면(낮게 절개)
    iso.box(X0, Y1 - 1.4, 0, X1, Y1, HF, WALL, ol=(120, 96, 66), lw=0.2)
    iso.box(X1 - 1.4, Y0, 0, X1, Y1, HF, WALL, ol=(120, 96, 66), lw=0.2)


# ───────────────────────── 판테온(돔 절개: 코퍼·오큘러스·위로 갈수록 가벼운 골재 3띠) ─────────────────────────

def draw_pantheon(L, cx, cy, w=66.0):
    slab(L, cx, cy, w, t=5.0, top=(222, 212, 186))
    iso, S = iso_of_slab(L, cx, cy, w)
    R = 11.0
    Xc, Yc = 14.5, 17.0
    Hd = 10.0
    Rt = 3.0
    # 계단형 광장 포장
    iso.rect3(2, 3, S - 2, S - 3, 0.0, (232, 222, 198), ol=(170, 154, 124), lw=0.2)
    x, y = iso.p(S - 6, 5)
    cypress(L, x, y, 11.0, 2.6)
    # 드럼 바닥(실내 바닥) 타원
    iso.ell(Xc, Yc, 0.2, R - Rt, fill=(236, 226, 204), ol=(150, 130, 98), lw=0.2)
    # 드럼 뒤쪽 반(안쪽면) — 화면 위쪽 반 타원 사이를 채운다
    cxs, cys = iso.p(Xc, Yc, 0.0)
    a_i = 1.2247 * (R - Rt)
    a_o = 1.2247 * R
    top_in = iso.p(Xc, Yc, Hd)
    # 안쪽 벽 면(오목면): 바닥 뒤 반원호 ~ 림 뒤 반원호
    pts = [(cxs + a_i * math.cos(math.radians(t)), cys + KE * a_i * math.sin(math.radians(t))) for t in range(180, 361, 6)]
    pts_top = [(cxs + a_i * math.cos(math.radians(t)), cys - Hd + KE * a_i * math.sin(math.radians(t))) for t in range(360, 179, -6)]
    L.poly(pts + pts_top, fill=(224, 204, 164), outline=(120, 98, 70), lw=0.2)
    for t in range(190, 360, 16):            # 벽감(안쪽 아치)
        c = math.cos(math.radians(t))
        sn = math.sin(math.radians(t))
        bx, by = cxs + a_i * c, cys + KE * a_i * sn
        L.rect(bx - 0.9, by - 6.5, bx + 0.9, by - 1.2, fill=(176, 148, 108))
    # 돔 바깥 반구(뒤쪽 볼록면)
    L.pie(top_in[0], top_in[1], a_o, a_o, 180, 360, fill=(206, 188, 150), outline=(120, 98, 70), lw=0.25)
    # 절개면(Y=Yc 평면, +Y향): 드럼 벽 단면 + 돔 단면(콘크리트 두께, 골재 3띠) + 안쪽 코퍼
    def sec(uv, fill, ol=None, lw=0.15):
        iso.fpoly("L", Xc, Yc, 0.0, uv, fill, ol, lw)
    Ro, Ri = R, R - 3.4
    # 드럼 벽 단면 두 줄
    sec([(-R, 0), (-R + Rt, 0), (-R + Rt, Hd), (-R, Hd)], CONC, (100, 94, 84))
    sec([(R - Rt, 0), (R, 0), (R, Hd), (R - Rt, Hd)], CONC, (100, 94, 84))
    # 돔 단면: 3개 골재 띠(아래 무거운 짙은 색 → 위 가벼운 옅은 색)
    def arc(r, a0, a1, n=28):
        return [(r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), Hd + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    bands = [(Ro, Ro - 1.15, (150, 142, 130)), (Ro - 1.15, Ro - 2.3, (186, 180, 168)), (Ro - 2.3, Ri, (224, 220, 210))]
    # 띠를 각도로 나누어 아래(0~40°) 무거움, 위로 갈수록 가벼움
    segs = [(0, 38, (146, 138, 126)), (38, 72, (178, 172, 160)), (72, 108, (206, 202, 192)), (108, 142, (178, 172, 160)), (142, 180, (146, 138, 126))]
    for (a0, a1, col) in segs:
        sec(arc(Ro, a0, a1, 10) + arc(Ri, a1, a0, 10), col, None)
    sec(arc(Ro, 0, 180) , None, (100, 94, 84), 0.22)
    sec(arc(Ri, 0, 180), None, (100, 94, 84), 0.22)
    # 안쪽 오목면(코퍼) — 안쪽 반원 영역
    inner = arc(Ri, 0, 180)
    sec(inner, (238, 230, 210), None)
    for k in range(1, 6):                    # 코퍼 5단
        sec(arc(Ri * k / 5.3, 0, 180, 18), None, (178, 156, 118), 0.12)
    for a in range(16, 180, 20):
        r = math.radians(a)
        sec([(0, Hd), (Ri * math.cos(r), Hd + Ri * math.sin(r))], None, (178, 156, 118), 0.1)
    # 오큘러스: 꼭대기 개구(복원이 아니라 실제 — 판테온은 현존)
    ox, oy = iso.face("L", Xc, Yc, 0.0, [(0, Hd + Ro)])[0]
    L.ell(ox, oy + 0.6, 1.9, 0.9, fill=(255, 252, 232), outline=(120, 98, 70), lw=0.2)
    # 포르티코(오른쪽 +X): 박스 + 8기둥 + 삼각 박공
    px0 = Xc + R - 1.0
    px1 = px0 + 9.5
    py0, py1 = Yc - 8.0, Yc + 8.0
    iso.box(px0, py0, 0, px1, py1, 2.0, ((238, 228, 204), (224, 210, 180), (200, 184, 150)), ol=(130, 108, 78), lw=0.2)
    for i in range(8):
        Y = py0 + 1.0 + i * (py1 - py0 - 2.0) / 7.0
        bx, by = iso.p(px1 - 1.0, Y, 2.0)
        L.rect(bx - 0.55, by - 11.0, bx + 0.55, by, fill=(246, 238, 216), outline=(150, 126, 92), lw=0.12)
    # 엔타블러처 + 박공(+X면, 'R'면)
    iso.poly3([(px0, py0, 13.0), (px1, py0, 13.0), (px1, py1, 13.0), (px0, py1, 13.0)], fill=(230, 214, 184), ol=(130, 108, 78), lw=0.15)
    iso.fpoly("R", px1, py0 - 0.0, 13.0, [(0, 0), (py1 - py0, 0), ((py1 - py0) / 2.0, 4.6)], (236, 222, 192), (130, 108, 78), 0.18)
    iso.fpoly("R", px1, py0, 11.0, [(0, 0), (py1 - py0, 0), (py1 - py0, 2.0), (0, 2.0)], (226, 210, 178), (130, 108, 78), 0.14)
    # 광장 인물과 나무(앞쪽)
    for (X, Y) in [(S - 5, 29), (6, 31)]:
        x, y = iso.p(X, Y)
        cypress(L, x, y, 11.0, 2.6)
    for (X, Y) in [(24, 30), (27, 31), (10, 33)]:
        x, y = iso.p(X, Y)
        person(L, x, y, 4.6, (150, 70, 52) if X > 20 else (92, 120, 150))


# ───────────────────────── 베수비오(Support-2): 79년 이전, 봉우리 하나·포도밭 비탈, 대기 원근 ─────────────────────────
def draw_vesuvius(L, cx, cy, w=52.0):
    """원근 배율 약 0.6(표준 86×80 → 52×48), 모든 색을 바탕과 50% 섞는다. 정상은 평평한 잿빛, 비탈은 포도밭 줄무늬. 연기는 그리지 않는다."""
    A = 0.5
    slab(L, cx, cy, w, t=4.0, top=mix((176, 190, 124), BG, A), soil=mix(SOIL, BG, A))
    prof = [(-26, 0), (-23, 2.6), (-19.5, 5.8), (-15.5, 9.6), (-11.5, 14.2), (-8, 19), (-5.4, 23.6), (-3.8, 26.2), (4.2, 26.2),
            (5.8, 24.4), (8.6, 20.4), (12.4, 15.6), (16.8, 10.8), (21, 6.2), (24, 3.0), (26, 0)]
    pts = [(cx + u, cy - h) for u, h in prof]
    L.poly(pts, fill=mix((146, 124, 88), BG, A), outline=mix((92, 70, 48), BG, A), lw=0.3)
    # 입체감: 오른쪽 비탈을 어둡게
    L.poly([(cx + 0.5, cy - 26.2)] + [(cx + u, cy - h) for u, h in prof[8:]] + [(cx + 5, cy)], fill=mix((122, 100, 68), BG, A))
    # 능선·골(물 흐른 자국)
    for (u0, u1, hh0) in [(-3.0, -9.0, 24.0), (0.5, -1.0, 25.5), (2.5, 7.5, 24.0), (-1.0, -15.0, 20.0)]:
        L.line([(cx + u0, cy - hh0), (cx + (u0 + u1) / 2.0, cy - hh0 * 0.55), (cx + u1, cy - 2.0)], mix((110, 88, 60), BG, A), 0.3)
    # 잿빛 평평한 정상
    L.poly([(cx - 3.8, cy - 26.2), (cx + 4.2, cy - 26.2), (cx + 5.8, cy - 24.4), (cx - 5.4, cy - 23.6)], fill=mix((178, 174, 166), BG, A), outline=mix((100, 94, 86), BG, A), lw=0.2)

    def xlim(h):
        for i in range(len(prof) - 1):
            if prof[i][1] <= h <= prof[i + 1][1] and prof[i + 1][1] > prof[i][1]:
                f = (h - prof[i][1]) / (prof[i + 1][1] - prof[i][1])
                return prof[i][0] + (prof[i + 1][0] - prof[i][0]) * f
        return -26.0

    # 비탈 중하단 포도밭: 등고선을 따라 놓인 줄(짧은 지면축 선분)
    for j in range(6):
        hh = 1.8 + j * 2.5
        xl = xlim(hh)
        x = xl + 1.6
        while x < -xl - 2.4:
            L.line([(cx + x, cy - hh), (cx + x + 1.6, cy - hh + 0.92)], mix((70, 132, 58), BG, A), 0.45, joint=False)
            x += 2.4
    # 앞 비탈(받침 앞 반) 포도밭: 지면축 ±30° 줄
    side = w / SQ3
    for j in range(5):
        x0 = cx - 20 + j * 3.2
        y0 = cy + 1.4 + j * 1.9
        for q in range(8):
            xa, ya = x0 + q * 3.6, y0 + q * 2.08
            if in_poly((xa + 1.5, ya + 0.9), [(cx - w / 2, cy), (cx, cy - side / 2), (cx + w / 2, cy), (cx, cy + side / 2)]):
                L.line([(xa, ya), (xa + 2.6, ya + 1.5)], mix((86, 144, 70), BG, A), 0.4, joint=False)


def draw_farm(L, cx, cy):
    """베수비오 밑동 앞의 포도밭 농장(빌라 레지나형): 작은 받침, 줄지은 포도, 지붕 얹은 집, 항아리. 밑동 5~6mm를 가린다."""
    slab(L, cx, cy, 30.0, t=1.8, top=(176, 190, 124), soil=SOIL)
    iso, S = iso_of_slab(L, cx, cy, 30.0)
    for i in range(4):
        y0 = 3.0 + i * 3.4
        iso.line3([(3, y0, 0.1), (S - 3, y0, 0.1)], (70, 130, 58), 0.45)
    iso.box(2.5, 2.5, 0, 10.5, 8.5, 4.4, ((236, 214, 170), (224, 198, 150), (196, 166, 124)), ol=(120, 84, 54), lw=0.15)
    iso.poly3([(2.0, 2.0, 4.4), (11.0, 2.0, 4.4), (11.0, 5.5, 6.4), (2.0, 5.5, 6.4)], fill=shade(ROOF_RED, 1.1), ol=(130, 60, 40), lw=0.12)
    iso.poly3([(2.0, 5.5, 6.4), (11.0, 5.5, 6.4), (11.0, 9.0, 4.4), (2.0, 9.0, 4.4)], fill=ROOF_RED, ol=(130, 60, 40), lw=0.12)
    for (X, Y) in [(14, 4), (16, 7)]:
        x, y = iso.p(X, Y)
        L.ell(x, y - 1.4, 1.1, 1.4, fill=(176, 116, 78), outline=(110, 70, 44), lw=0.12)

# ───────────────────────── 배치 명세 ─────────────────────────
POS = {"bath": (176, 138, 64), "pantheon": (245, 138, 66), "vesuvius": (326, 126, 52), "farm": (332, 127)}


def objects():
    bx, by, bw = POS["bath"]
    vx, vy, vw = POS["vesuvius"]
    fx, fy = POS["farm"]
    px, py, pw = POS["pantheon"]
    return [
        dict(z=10, name="베수비오", tier="Support-2", region=(vx - 40, vy - 40, vx + 40, vy + 28), fn=draw_vesuvius, args=(vx, vy, vw)),
        dict(z=20, name="포도밭 농장", tier="소품", region=(fx - 24, fy - 20, fx + 24, fy + 18), fn=draw_farm, args=(fx, fy)),
        dict(z=30, name="욕장", tier="Support", region=(bx - 46, by - 46, bx + 46, by + 36), fn=draw_bath, args=(bx, by, bw)),
        dict(z=40, name="판테온", tier="Support", region=(px - 46, py - 46, px + 46, py + 36), fn=draw_pantheon, args=(px, py, pw)),
    ]


def labels():
    return [
        dict(order=20, kind="label", name="욕장", T=(176.0, 156.5), M=M_WALL_UP, mode="below", side="L", col=C_SUP_T,
             en=["CARACALLA BATHS"], ko="카라칼라 욕장", sup=None,
             body=["열탕실 복원 상상도", "오큘러스·코퍼는 복원 추정", "냉탕실 열주를 합친 복합도", "겉은 벽돌, 속은 콘크리트"], gap=9.5),
        dict(order=30, kind="label", name="판테온", T=(245.0, 156.5), M=M_WALL_UP, mode="below", side="L", col=C_SUP_T,
             en=["PANTHEON"], ko="판테온", sup=None, body=["철근 없는 콘크리트 돔", "지름 43.3m", "위로 갈수록 가벼운 골재"], gap=9.5),
        dict(order=110, kind="flag", name="베수비오", T=(341.3, 114.0), M=M_WALL_UP, col=C_SUP_T, en="VESUVIUS", ko="베수비오", side="L", mode="above", pole=9.0),
    ]


def extra_labels(LB):
    pass
