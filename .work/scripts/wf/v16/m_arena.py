# -*- coding: utf-8 -*-
# 로마 콘크리트 A2 와이어프레임 — 아레나(콜로세움) — LocalBanana 참조 디오라마 형태
# 담당 패키지: arena · 이 파일은 담당 워커만 고친다(공용 도구는 common.py, 조립은 main.py).

from common import *
from common import _a
import common as C

ARENA_R = 100.0                     # 팔각 외접 반지름
ARENA_XL = 236.0                    # 받침 왼쪽 수직 변 x
ARENA_CY = 305.0
ARENA_CX = ARENA_XL + 1.1316 * ARENA_R

# ───────────────────────── 1 아레나(콜로세움) — LocalBanana 참조 디오라마 형태 ─────────────────────────


def draw_arena(L):
    CX, CY = ARENA_CX, ARENA_CY
    iso = Iso(L, CX, CY)
    R = ARENA_R
    oct_pl = [(R * math.cos(math.radians(22.5 + 45 * k)), R * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
    RS = R / 89.3
    oct_sc = [iso.p(X, Y) for X, Y in oct_pl]
    T = 7.0
    # ── 받침(흙 단면): 앞쪽 세 변(SE·정면·SW)만 측면이 보인다
    side_cols = {7: (92, 68, 44), 0: (114, 88, 56), 1: (132, 102, 66)}
    for k in (7, 0, 1):
        a, b = oct_sc[k], oct_sc[(k + 1) % 8]
        L.poly([a, b, (b[0], b[1] + T), (a[0], a[1] + T)], fill=side_cols[k], outline=(70, 50, 32), lw=0.25)
        L.poly([a, b, (b[0], b[1] + 1.8), (a[0], a[1] + 1.8)], fill=GRASS)
        for j in (0.38, 0.62):
            L.line([(a[0], a[1] + T * j + 1.0), (b[0], b[1] + T * j + 1.0)], shade(side_cols[k], 0.8), 0.18, joint=False)
    # 콘크리트 기초 고리 절개(받침 정면 변 왼쪽 부분): 흙 속에 회색 콘크리트 띠가 드러난다
    a, b = oct_sc[0], oct_sc[1]
    # 정면 변은 a(오른쪽)→b(왼쪽): 왼쪽 36~66% 구간에 절개 창
    def lerp(p, q, t):
        return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
    w0, w1 = lerp(a, b, 0.40), lerp(a, b, 0.66)
    L.poly([w0, w1, (w1[0], w1[1] + T), (w0[0], w0[1] + T)], fill=(150, 124, 92), outline=(70, 50, 32), lw=0.25)
    L.poly([(w0[0], w0[1] + 2.6), (w1[0], w1[1] + 2.6), (w1[0], w1[1] + 6.4), (w0[0], w0[1] + 6.4)], fill=CONC, outline=(104, 98, 88), lw=0.2)
    for i in range(14):
        tt = rnd()
        pp = lerp(w0, w1, tt)
        L.ell(pp[0], pp[1] + 3.2 + rnd() * 2.6, 0.45, 0.4, fill=(214, 206, 188))
    # 윗면(광장)
    L.poly(oct_sc, fill=(186, 168, 138), outline=(70, 50, 30), lw=0.5)
    # 돌 포장 결: ±30° 짧은 선
    for i in range(170):
        X = (rnd() * 2 - 1) * 80
        Y = (rnd() * 2 - 1) * 80
        if abs(X) + abs(Y) > 112 or X * X + Y * Y < 64 * 64:
            continue
        d = 1 if rnd() < 0.5 else 0
        x0, y0 = iso.p(X, Y)
        dx, dy = (C30, 0.5) if d else (-C30, 0.5)
        ln = 1.6 + rnd() * 2.6
        L.line([(x0, y0), (x0 + dx * ln, y0 + dy * ln)], (166, 150, 120), 0.2, joint=False)
    # 포장 앞마당(고리 둘레의 밝은 띠)
    iso.ell(0, 0, 0, 68.5, fill=(210, 197, 170), ol=(160, 144, 114), lw=0.25)

    # ── 광장 뒤쪽(북서·북동) 소품: 사이프러스·올리브·작은 신전 폐허
    for (X, Y, h) in [(-64, -44, 17), (-56, -56, 14), (-74, -34, 15), (18, -76, 15), (46, -62, 13)]:
        x, y = iso.p(X, Y)
        cypress(L, x, y, h)
    olx, oly = iso.p(-70, 20)
    olive(L, olx, oly, 4.6)
    # 뒤 오른쪽 작은 신전 폐허(4기둥 + 박공 조각)
    tx, ty = iso.p(4, -58)
    iso2 = Iso(L, tx, ty)
    iso2.box(0, 0, 0, 20, 14, 2.4, (TRAV_L, TRAV, TRAV_D), ol=(130, 108, 78), lw=0.15)
    for i in range(4):
        px, py = iso2.p(2.5 + i * 5.2, 13.0, 2.4)
        L.rect(px - 0.9, py - 11.5, px + 0.9, py, fill=(240, 228, 202), outline=(150, 128, 94), lw=0.16)
        L.rect(px - 1.4, py - 12.6, px + 1.4, py - 11.5, fill=(230, 216, 188), outline=(150, 128, 94), lw=0.14)
    px0, py0 = iso2.p(1.0, 13.0, 2.4)
    px1, py1 = iso2.p(18.0, 13.0, 2.4)
    L.poly([(px0, py0 - 13.0), (px1, py1 - 13.0), (px1, py1 - 12.0), (px0, py0 - 12.0)], fill=(226, 210, 178), outline=(150, 128, 94), lw=0.16)
    L.poly([(px0, py0 - 13.0), ((px0 + px1) / 2.0, (py0 + py1) / 2.0 - 17.0), (px1, py1 - 13.0)], fill=(232, 218, 188), outline=(150, 128, 94), lw=0.16)

    # ── 링: 화면 타원 중심 = 받침 중심. 평면 원(화면 비 0.577).
    RCx, RCy = CX, CY

    def ep(a, t, z=0.0):
        r = math.radians(t)
        return (RCx + a * math.cos(r), RCy + KE * a * math.sin(r) - z)

    A_OUT, A_IN2, A_RIM, A_FLOOR = 74.0, 64.2, 53.9, 31.1
    H_RIM, H_FLOOR = 24.0, 2.0
    # 관람석(카베아): 바깥 테두리에서 아레나 바닥까지 계단형 동심 타원(안으로 갈수록 낮다)
    nt = 6
    for i in range(nt + 1):
        f = i / nt
        a = A_RIM - (A_RIM - A_FLOOR) * f
        z = H_RIM - (H_RIM - H_FLOOR) * f
        col = (226, 208, 170) if i % 2 == 0 else (206, 186, 148)
        cxz, cyz = ep(0, 0, z)
        L.ell(cxz, cyz, a, KE * a, fill=col, outline=(150, 126, 92), lw=0.2)
    # 방사 통로(보미토리아)
    for t in range(0, 360, 15):
        p0 = ep(A_RIM - 1.0, t, H_RIM)
        p1 = ep(A_FLOOR + 1.0, t, H_FLOOR)
        L.line([p0, p1], (150, 126, 92), 0.16, joint=False)
    # 아레나 바닥: 오른쪽 반 나무 바닥 + 왼쪽 반 하이포게움 노출
    fx, fy = ep(0, 0, H_FLOOR)
    L.ell(fx, fy, A_FLOOR, KE * A_FLOOR, fill=(120, 94, 64), outline=(78, 58, 38), lw=0.35)
    L.pie(fx, fy, A_FLOOR - 0.4, KE * (A_FLOOR - 0.4), 270, 90, fill=(180, 142, 96))
    # 나무 바닥 판자(오른쪽 반): 지면 +X축(화면 ↘ 30°) 방향 줄을 아레나 타원 안으로 자른다
    iso_p = Iso(L, fx, fy)
    Rf = (A_FLOOR - 0.8) / 1.2247
    for j in range(-9, 10):
        y0 = j * 2.6
        if abs(y0) >= Rf - 0.5:
            continue
        xe = math.sqrt(Rf * Rf - y0 * y0)
        xs = max(y0 + 0.5, -xe)
        if xs < xe - 0.8:
            iso_p.line3([(xs, y0, 0.0), (xe, y0, 0.0)], (150, 112, 74), 0.14)
    # 하이포게움 미로(왼쪽 반): 낮은 벽 상자들
    iso_f = Iso(L, fx, fy)
    walls = [(-17, -12, 8, -9.4), (-17, -4, 8, -1.4), (-17, 4, 8, 6.6), (-17, 12, 8, 14.6),
             (-14, -12, -11.4, 14), (-6, -12, -3.4, 14), (2, -12, 4.6, 14)]
    for (X0, Y0, X1, Y1) in walls:
        # 왼쪽 반원 안에 드는 것만 (평면 반지름 24.5 안)
        cx_, cy_ = (X0 + X1) / 2.0, (Y0 + Y1) / 2.0
        if cx_ * cx_ + cy_ * cy_ > 21.5 ** 2:
            continue
        iso_f.box(X0, Y0, 0, X1, Y1, 2.4, ((206, 184, 148), (176, 152, 118), (140, 116, 86)), ol=(90, 70, 46), lw=0.14)
    # 하이포게움/나무 바닥 경계: 중앙 세로선(평면 Y축 방향 아님 — 화면 수직)
    L.line([(fx, fy - KE * (A_FLOOR - 0.4)), (fx, fy + KE * (A_FLOOR - 0.4))], (78, 58, 38), 0.3, joint=False)

    # 안쪽 아케이드 고리(앞쪽 반): 외벽이 낮아진 틈으로 드러나는 두 번째 고리
    def ring_poly(a_list_bottom, a_list_top):
        return a_list_bottom + a_list_top[::-1]

    def band(a, t0, t1, ztop, zb=0.0, step=3.0, fill=TRAV, ol=None, lw=0.2, shadef=True):
        """링 외면/내면 띠: t0→t1, 아래 높이 zb, 위 높이 ztop(t)"""
        n = max(2, int(abs(t1 - t0) / step))
        ts = [t0 + (t1 - t0) * i / n for i in range(n + 1)]
        for i in range(n):
            ta, tb = ts[i], ts[i + 1]
            tm = (ta + tb) / 2.0
            f = (0.93 + 0.14 * math.cos(math.radians(tm - 150.0))) if shadef else 1.0
            c = shade(fill, f)
            pts = [ep(a, ta, zb), ep(a, tb, zb), ep(a, tb, ztop(tb)), ep(a, ta, ztop(ta))]
            L.poly(pts, fill=c)
        top = [ep(a, t, ztop(t)) for t in ts]
        bot = [ep(a, t, zb) for t in ts]
        if ol:
            L.line(top, ol, lw)
            L.line(bot, ol, lw)
        return ts

    def arches(a, t0, t1, rows, ztop, hw=2.3, pitch=7.5, col=ARCH_IN, a_scale=1.0):
        """rows = [(z0, z1)] 각 층의 아치 개구부. ztop 아래에서만."""
        plan_r = a / 1.2247
        ha = plan_r * math.radians(hw)
        t = t0 + pitch / 2.0 if t1 > t0 else t0 - pitch / 2.0
        step = pitch if t1 > t0 else -pitch
        while (t < t1 - 1e-6) if t1 > t0 else (t > t1 + 1e-6):
            for (z0, z1) in rows:
                if z1 + ha + 1.5 > ztop(t):
                    continue
                pts = [ep(a, t - hw, z0), ep(a, t + hw, z0), ep(a, t + hw, z1)]
                for i in range(1, 9):
                    sx = 1 - 2 * i / 9.0
                    pts.append(ep(a, t + hw * sx, z1 + ha * math.sqrt(1 - sx * sx)))
                pts.append(ep(a, t - hw, z1))
                L.poly(pts, fill=col)
            t += step

    # (a) 안쪽 아케이드 고리: 앞쪽 t=15..165, 높이 22 안팎으로 들쭉날쭉
    def h_in(t):
        prof = [(15, 14), (30, 22), (48, 18), (62, 22), (78, 12), (92, 22), (110, 20), (128, 24), (145, 22), (165, 24)]
        for i in range(len(prof) - 1):
            if prof[i][0] <= t <= prof[i + 1][0]:
                return prof[i][1] if (t - prof[i][0]) < (prof[i + 1][0] - prof[i][0]) * 0.6 else prof[i + 1][1]
        return 20

    band(A_IN2, 15, 165, h_in, fill=(206, 184, 146), ol=(130, 106, 76), lw=0.25)
    arches(A_IN2, 15, 165, [(1.5, 8.5), (12.5, 18.0)], h_in, hw=2.2, pitch=8.0)
    # 윗면 얇은 띠
    ts = [15 + 3 * i for i in range(51)]
    L.poly([ep(A_IN2, t, h_in(t)) for t in ts] + [ep(A_IN2 - 4, t, h_in(t)) for t in ts[::-1]], fill=TRAV_L, outline=(130, 106, 76), lw=0.2)

    # (b) 뒤 왼쪽만 남은 4층 외벽 조각: 안쪽면(t 180→262), 윗면, 바깥면(t 120→180)
    def h_tall(t):
        prof = [(120, 26), (128, 26), (128.1, 38), (140, 38), (140.1, 49), (152, 49), (152.1, 62), (205, 62), (232, 60), (262, 34)]
        for i in range(len(prof) - 1):
            if prof[i][0] <= t <= prof[i + 1][0]:
                f = (t - prof[i][0]) / max(1e-6, (prof[i + 1][0] - prof[i][0]))
                return prof[i][1] + (prof[i + 1][1] - prof[i][1]) * f
        return 30

    band(A_OUT - 8, 180, 262, h_tall, zb=H_RIM, fill=(196, 174, 136), ol=(120, 98, 70), lw=0.25)
    arches(A_OUT - 8, 180, 262, [(H_RIM + 3, H_RIM + 10), (H_RIM + 15, H_RIM + 22), (H_RIM + 27, H_RIM + 34)], h_tall, hw=2.1, pitch=7.5, col=(92, 68, 44))
    tsb = [180 + 2 * i for i in range(42)]
    L.poly([ep(A_OUT, t, h_tall(t)) for t in tsb] + [ep(A_OUT - 8, t, h_tall(t)) for t in tsb[::-1]], fill=TRAV_L, outline=(120, 98, 70), lw=0.22)
    band(A_OUT, 120, 180, h_tall, fill=TRAV, ol=(120, 98, 70), lw=0.28)
    arches(A_OUT, 120, 180, [(2, 10), (15.5, 23.5), (29, 37), (42, 50)], h_tall, hw=2.4, pitch=7.5)
    tsc = [120 + 2 * i for i in range(31)]
    L.poly([ep(A_OUT, t, h_tall(t)) for t in tsc] + [ep(A_OUT - 8, t, h_tall(t)) for t in tsc[::-1]], fill=TRAV_L, outline=(120, 98, 70), lw=0.22)
    # 조각의 앞쪽 끝 단면(절단면): 콘크리트 심이 드러나는 면
    pa, pb = ep(A_OUT, 120, 0), ep(A_OUT - 8, 120, 0)
    L.poly([pa, pb, ep(A_OUT - 8, 120, 26), ep(A_OUT, 120, 26)], fill=CONC, outline=(104, 98, 88), lw=0.2)

    # (c) 무너진 앞쪽 고리: t=-8..120, 지그재그 파손 윤곽, 틈으로 안쪽 아케이드가 보인다
    def h_front(t):
        prof = [(-8, 6), (4, 6), (4.1, 14), (14, 14), (14.1, 22), (26, 22), (26.1, 10), (40, 10), (40.1, 0), (56, 0), (56.1, 18), (66, 18),
                (66.1, 26), (76, 26), (76.1, 12), (84, 12), (84.1, 0), (96, 0), (96.1, 20), (108, 20), (108.1, 30), (120, 26)]
        for i in range(len(prof) - 1):
            if prof[i][0] <= t <= prof[i + 1][0]:
                return prof[i][1] + (prof[i + 1][1] - prof[i][1]) * (t - prof[i][0]) / max(1e-6, prof[i + 1][0] - prof[i][0])
        return 6

    # 높이 0 구간은 그리지 않기 위해 조각별로 처리
    segs = [(-8, 40), (56, 84), (96, 120)]
    for (t0, t1) in segs:
        hh = lambda t: max(0.5, h_front(t))
        band(A_OUT, t0, t1, hh, fill=TRAV, ol=(120, 98, 70), lw=0.28)
        arches(A_OUT, t0, t1, [(1.5, 6.5), (13.0, 18.5), (24.0, 29.0)], hh, hw=2.4, pitch=7.5)
        tsd = [t0 + (t1 - t0) * i / max(2, int((t1 - t0) / 2.5)) for i in range(max(2, int((t1 - t0) / 2.5)) + 1)]
        L.poly([ep(A_OUT, t, hh(t)) for t in tsd] + [ep(A_OUT - 8, t, hh(t)) for t in tsd[::-1]], fill=TRAV_L, outline=(120, 98, 70), lw=0.22)
    # 콘크리트 절개 창(앞 고리 한 곳): 방사 볼트(콘크리트)·응회암 벽·석회화 겉면 세 겹
    tc0, tc1 = 58.0, 82.0
    top_z = 18.0
    pts_o = [ep(A_OUT, t, 0) for t in (tc0, tc1)] + [ep(A_OUT, t, top_z) for t in (tc1, tc0)]
    L.poly(pts_o, fill=CONC, outline=(100, 94, 84), lw=0.3)
    pts_t = [ep(A_OUT - 8, t, 0) for t in (tc0, tc1)] + [ep(A_OUT - 8, t, top_z) for t in (tc1, tc0)]
    L.poly([ep(A_OUT, tc0, 0), ep(A_OUT, tc0 + 7, 0), ep(A_OUT, tc0 + 7, top_z), ep(A_OUT, tc0, top_z)], fill=TRAV, outline=(120, 98, 70), lw=0.2)
    L.poly([ep(A_OUT, tc0 + 7, 0), ep(A_OUT, tc0 + 14, 0), ep(A_OUT, tc0 + 14, top_z), ep(A_OUT, tc0 + 7, top_z)], fill=TUFF, outline=(100, 80, 56), lw=0.2)
    for i in range(26):
        tt = tc0 + 14 + rnd() * (tc1 - tc0 - 14)
        zz = 1.5 + rnd() * (top_z - 3)
        px, py = ep(A_OUT, tt, zz)
        L.ell(px, py, 0.5, 0.42, fill=(226, 218, 200))

    # ── 앞 광장 소품: 노점·기둥 폐허·작은 개선문 조각·올리브·사이프러스·사람
    for (X, Y, h) in [(-74, 34, 16), (-70, 40, 13), (50, 56, 15)]:
        x, y = iso.p(X, Y)
        cypress(L, x, y, h)
    for (X, Y) in [(-46, 60), (74, 28), (14, 76)]:
        x, y = iso.p(X, Y)
        olive(L, x, y, 4.2)
    for i, (X, Y) in enumerate([(-66, 12), (-70, 8), (-62, 16), (46, 66), (40, 70), (30, 74)]):
        x, y = iso.p(X, Y)
        column_ruin(L, x, y, 6.5 - (i % 3) * 1.5, 1.5, broken=(i % 3 == 2))
    # 작은 개선문 조각(앞 왼쪽)
    ax_, ay_ = iso.p(-50, 52)
    iso3 = Iso(L, ax_, ay_)
    iso3.box(0, 0, 0, 3, 8, 9, (TRAV_L, TRAV, TRAV_D), ol=(130, 108, 78), lw=0.15)
    iso3.box(10, 0, 0, 13, 8, 9, (TRAV_L, TRAV, TRAV_D), ol=(130, 108, 78), lw=0.15)
    iso3.box(0, 0, 9, 13, 8, 11.5, (TRAV_L, TRAV, TRAV_D), ol=(130, 108, 78), lw=0.15)
    # 노점(차양): 앞 오른쪽
    for (X, Y, c) in [(30, 66, (214, 86, 66)), (-24, 72, (240, 236, 224))]:
        sx, sy = iso.p(X, Y)
        L.poly([(sx - 3.6, sy - 3.2), (sx + 3.6, sy - 3.2), (sx + 4.4, sy - 5.4), (sx - 2.8, sy - 5.4)], fill=c, outline=(120, 90, 60), lw=0.15)
        L.rect(sx - 3.2, sy - 3.2, sx - 2.8, sy, fill=(120, 90, 60))
        L.rect(sx + 3.0, sy - 3.2, sx + 3.4, sy, fill=(120, 90, 60))
    # 사람들: 광장 앞·노점 옆·폐허 옆 세 무리, 키 약 5.6mm
    cols = [(150, 70, 52), (214, 196, 170), (92, 120, 150), (190, 150, 70), (236, 232, 222)]
    groups = [(8, 74, 5), (-40, 66, 4), (46, 58, 3), (-64, 22, 2)]
    for gx, gy, n in groups:
        for i in range(n):
            x, y = iso.p(gx + (rnd() - 0.5) * 16, gy + (rnd() - 0.5) * 8)
            person(L, x, y, 5.6, cols[(i + int(gx)) % 5])
    return {"좌측변중점": (CX - 1.1316 * R, CY), "링왼": ep(A_OUT, 150, 40), "앞변": (CX, CY + 0.6533 * R)}



# ───────────────────────── 배치 명세 ─────────────────────────
def objects():
    return [dict(z=50, name="아레나", tier="아레나", region=(ARENA_XL - 8, 170, 448, 392), fn=draw_arena, args=(), bleed=True)]


def labels():
    return [dict(order=10, kind="label", name="아레나", T=(236.0, 306.0), M=M_WALL_DN, mode="above", side="R", col=C_ARENA_T,
                 en=["COLOSSEUM"], ko="콜로세움 아레나", sup=None,
                 body=["겉은 석회화, 속과 기초는", "콘크리트로 채움", "무너짐의 주원인:", "지반·석재 반출·관리 부재"], gap=2.4)]


def extra_labels(LB):
    pass
