# -*- coding: utf-8 -*-
# 로마 콘크리트 A2 와이어프레임 — Support(아래 줄): 수도교·포르투스 항·카이킬리아 메텔라 무덤
# 담당 패키지: support_bottom · 이 파일은 담당 워커만 고친다(공용 도구는 common.py, 조립은 main.py).

from common import *
from common import _a
import common as C

# ───────────────────────── 수도교(연속 아케이드 + 상층 수로 + 보수 구간) ─────────────────────────
def draw_aqueduct(L, cx, cy, w=68.0):
    slab(L, cx, cy, w, t=5.0, top=(214, 206, 170))
    iso, S = iso_of_slab(L, cx, cy, w)
    # 풀밭 결
    iso.rect3(1.5, 1.5, S - 1.5, S - 1.5, 0.0, (176, 188, 126), ol=None)
    Yw0, Yw1 = 17.0, 20.5
    X0, X1 = 2.5, S - 2.5
    nb = 7
    pitch = (X1 - X0) / nb
    pier = 1.7
    H1, H2 = 9.5, 18.0
    STONE_C = ((226, 210, 172), (208, 188, 148), (178, 156, 118))
    BRICK_C = ((214, 132, 98), (196, 108, 78), (160, 84, 60))
    # 아치 열 지면 그림자
    # 벽 본체(+Y향 면이 보인다): 하층 + 상층 연속 벽
    iso.box(X0, Yw0, 0, X1, Yw1, H1, STONE_C, ol=(120, 98, 70), lw=0.2)
    iso.box(X0, Yw0, H1, X1, Yw1, H2, STONE_C, ol=(120, 98, 70), lw=0.2)
    # 보수 구간(하드리아누스기 벽돌면 콘크리트): 가운데 두 칸을 벽돌색으로 덧댐
    for i in (3, 4):
        xa = X0 + i * pitch
        iso.fpoly("L", 0, Yw1, 0, [(xa, 0), (xa + pitch, 0), (xa + pitch, H2), (xa, H2)], BRICK_C[1], (120, 70, 50), 0.15)
    # 하층 아치 개구(밑까지 열림) + 상층 작은 아치
    for i in range(nb):
        xa = X0 + i * pitch + pier / 2.0
        xb = X0 + (i + 1) * pitch - pier / 2.0
        iso.arch("L", 0, Yw1, 0, xa, xb, 0, 5.6, (112, 100, 70), (96, 76, 50))
        iso.arch("L", 0, Yw1, 0, xa + 0.4, xb - 0.4, H1 + 1.0, H1 + 3.6, (112, 100, 70), (96, 76, 50))
    # 벽돌 줄눈(보수 구간)
    for i in (3, 4):
        xa = X0 + i * pitch
        for j in range(1, 6):
            iso.fpoly("L", 0, Yw1, 0, [(xa, j * 3.0), (xa + pitch, j * 3.0)], None, (150, 78, 58), 0.1)
    # 상부 수로(스페쿠스): 윗면에 파란 물길
    iso.poly3([(X0 - 0.3, Yw0 + 0.7, H2), (X1 + 0.3, Yw0 + 0.7, H2), (X1 + 0.3, Yw1 - 0.7, H2), (X0 - 0.3, Yw1 - 0.7, H2)], fill=(120, 176, 208), ol=(70, 110, 140), lw=0.15)
    iso.box(X0 - 0.3, Yw0, H2, X1 + 0.3, Yw0 + 0.7, H2 + 1.4, STONE_C, ol=(120, 98, 70), lw=0.15)
    iso.box(X0 - 0.3, Yw1 - 0.7, H2, X1 + 0.3, Yw1, H2 + 1.4, STONE_C, ol=(120, 98, 70), lw=0.15)
    # 들판 소품: 올리브 두 그루와 농부
    for (X, Y) in [(S - 6, 8), (6, 30)]:
        x, y = iso.p(X, Y)
        olive(L, x, y, 3.8)
    x, y = iso.p(22, 31)
    person(L, x, y, 4.8, (176, 112, 72))


# ───────────────────────── 포르투스(트라야누스 육각 내항 + 붉은 기와 창고 열 + 방파제 + 등대) ─────────────────────────

def draw_portus(L, cx, cy, w=64.0):
    slab(L, cx, cy, w, t=5.0, top=(216, 204, 176))
    iso, S = iso_of_slab(L, cx, cy, w)
    # 육각 내항(물)
    Rh = 12.5
    hc = (S / 2.0, S / 2.0)
    hexp = [(hc[0] + Rh * math.cos(math.radians(60 * k)), hc[1] + Rh * 0.9 * math.sin(math.radians(60 * k))) for k in range(6)]
    iso.poly3([(a, b, 0.0) for a, b in hexp], fill=(214, 200, 170), ol=(150, 130, 98), lw=0.2)
    hexw = [(hc[0] + (Rh - 1.6) * math.cos(math.radians(60 * k)), hc[1] + (Rh - 1.6) * 0.9 * math.sin(math.radians(60 * k))) for k in range(6)]
    iso.poly3([(a, b, -0.6) for a, b in hexw], fill=(112, 172, 214), ol=(70, 120, 160), lw=0.2)
    # 창고 열: 위·아래 변(X축 평행)에 길쭉한 붉은 기와 창고 4연
    def warehouse(X0, Y0, X1, Y1):
        iso.box(X0, Y0, 0, X1, Y1, 3.4, ((226, 190, 150), (214, 176, 134), (186, 148, 108)), ol=(120, 84, 54), lw=0.15)
        iso.poly3([(X0 - 0.3, Y0 - 0.2, 3.4), (X1 + 0.3, Y0 - 0.2, 3.4), (X1 + 0.3, (Y0 + Y1) / 2.0, 5.0), (X0 - 0.3, (Y0 + Y1) / 2.0, 5.0)], fill=shade(ROOF_RED, 1.1), ol=(130, 60, 40), lw=0.15)
        iso.poly3([(X0 - 0.3, (Y0 + Y1) / 2.0, 5.0), (X1 + 0.3, (Y0 + Y1) / 2.0, 5.0), (X1 + 0.3, Y1 + 0.2, 3.4), (X0 - 0.3, Y1 + 0.2, 3.4)], fill=ROOF_RED, ol=(130, 60, 40), lw=0.15)
    ytop = hc[1] - Rh * 0.9 * 0.866 - 5.2
    ybot = hc[1] + Rh * 0.9 * 0.866 + 1.4
    for i in range(4):
        warehouse(hc[0] - 12.5 + i * 6.4, ytop, hc[0] - 12.5 + i * 6.4 + 5.8, ytop + 3.8)
    for i in range(3):
        warehouse(hc[0] - 9.8 + i * 6.4, ybot, hc[0] - 9.8 + i * 6.4 + 5.8, ybot + 3.8)
    # 방파제: 받침 정면에서 바다로 나가는 두 팔(±30° 직선) + 등대
    bw = (232, 222, 196)
    a1 = iso.p(S + 0.0, S * 0.5)
    L.poly([iso.p(S - 2, S * 0.62, 0), iso.p(S + 14, S * 0.62, 0), iso.p(S + 14, S * 0.62 + 2.4, 0), iso.p(S - 2, S * 0.62 + 2.4, 0)], fill=bw, outline=(150, 130, 98), lw=0.2)
    lh = iso.p(S + 14.5, S * 0.62 + 1.2, 0)
    L.poly([(lh[0] - 1.6, lh[1]), (lh[0] + 1.6, lh[1]), (lh[0] + 1.1, lh[1] - 8.0), (lh[0] - 1.1, lh[1] - 8.0)], fill=(244, 238, 222), outline=(130, 108, 78), lw=0.15)
    L.poly([(lh[0] - 1.4, lh[1] - 8.0), (lh[0], lh[1] - 10.4), (lh[0] + 1.4, lh[1] - 8.0)], fill=(240, 196, 90), outline=(130, 108, 78), lw=0.12)
    L.poly([iso.p(S * 0.62, S - 2, 0), iso.p(S * 0.62, S + 11, 0), iso.p(S * 0.62 + 2.4, S + 11, 0), iso.p(S * 0.62 + 2.4, S - 2, 0)], fill=bw, outline=(150, 130, 98), lw=0.2)
    # 배 한 척(내항 안)
    sx, sy = iso.p(hc[0] + 1.0, hc[1] + 0.5, -0.2)
    L.poly([(sx - 3.0, sy), (sx + 3.0, sy - 1.0), (sx + 4.0, sy), (sx - 4.0, sy + 1.0)], fill=(150, 108, 70), outline=(90, 64, 40), lw=0.15)
    L.line([(sx, sy - 0.6), (sx, sy - 5.6)], (110, 80, 50), 0.25, joint=False)
    L.poly([(sx, sy - 5.4), (sx + 2.4, sy - 3.0), (sx, sy - 1.4)], fill=(248, 244, 232), outline=(150, 130, 98), lw=0.1)
    # 부두 인물·나무
    for (X, Y) in [(4, 4), (S - 4, 6)]:
        x, y = iso.p(X, Y)
        cypress(L, x, y, 8.0, 2.2)
    for (X, Y) in [(S - 5, S - 9), (6, S - 8)]:
        x, y = iso.p(X, Y)
        person(L, x, y, 3.8, (176, 100, 60))


# ───────────────────────── 카이킬리아 메텔라 무덤(아피아 가도변, 원통 드럼 사분 절개) ─────────────────────────
def draw_metella(L, cx, cy, w=64.0):
    slab(L, cx, cy, w, t=5.0, top=(196, 196, 150))
    iso, S = iso_of_slab(L, cx, cy, w)
    iso.rect3(1.5, 1.5, S - 1.5, S - 1.5, 0.0, (184, 192, 134), ol=None)
    Xc, Yc = 19.0, 19.0
    R = 10.5
    Zp, Zd = 6.0, 19.0
    for (X, Y, h) in [(4, 5, 10), (S - 4, 6, 9)]:
        x, y = iso.p(X, Y)
        cypress(L, x, y, h, 2.4)
    # 사각 기단
    iso.box(Xc - 14, Yc - 14, 0, Xc + 14, Yc + 14, Zp, ((228, 216, 186), (212, 198, 164), (186, 170, 136)), ol=(120, 98, 70), lw=0.2)
    # 드럼: 앞쪽(관찰자 쪽) 1/4를 걷어 내 두 절단면을 드러낸다
    def arc_pts(t0, t1, z, n=10):
        return [(Xc + R * math.cos(math.radians(t0 + (t1 - t0) * i / n)), Yc + R * math.sin(math.radians(t0 + (t1 - t0) * i / n)), z) for i in range(n + 1)]
    # 바깥 측면 두 조각(θ −45~0°, 90~135°)
    for (t0, t1) in ((-45, 0), (90, 135)):
        lo = arc_pts(t0, t1, Zp)
        hi = arc_pts(t0, t1, Zd)
        iso.poly3(lo + hi[::-1], fill=(206, 188, 150) if t0 < 0 else (222, 204, 166), ol=(120, 98, 70), lw=0.25)
        # 프리즈 띠
        lo2 = arc_pts(t0, t1, Zd - 2.2)
        iso.poly3(lo2 + hi[::-1], fill=(236, 226, 198), ol=(130, 108, 78), lw=0.15)
    # 윗면(3/4 원판)
    top = [(Xc, Yc, Zd)] + [(Xc + R * math.cos(math.radians(t)), Yc + R * math.sin(math.radians(t)), Zd) for t in range(90, 361, 8)]
    iso.poly3(top, fill=(238, 228, 200), ol=(120, 98, 70), lw=0.3)
    # 절단면 ① Y=Yc 평면(+Y향, X Xc→Xc+R) ② X=Xc 평면(+X향, Y Yc→Yc+R)
    H = Zd - Zp
    for kind in ("L", "R"):
        X, Y = (Xc, Yc)
        iso.fpoly(kind, X, Y, Zp, [(0, 0), (R, 0), (R, H), (0, H)], CONC, (100, 94, 84), 0.25)
        iso.fpoly(kind, X, Y, Zp, [(R - 2.4, 0), (R, 0), (R, H), (R - 2.4, H)], BRICK, (130, 70, 50), 0.2)      # 벽돌 겉면
        iso.fpoly(kind, X, Y, Zp, [(0, 0), (R - 2.4, 0), (R - 2.4, 3.0), (0, 3.0)], TUFF, (100, 80, 56), 0.15)    # 응회암 보강
        for i in range(26):
            u = rnd() * (R - 3.0)
            v = 3.4 + rnd() * (H - 3.8)
            px, py = iso.face(kind, X, Y, Zp, [(u, v)])[0]
            L.ell(px, py, 0.5, 0.42, fill=(226, 220, 204) if rnd() > 0.4 else (122, 116, 104))
        iso.arch(kind, X, Y, Zp, 0.0, 4.4, 3.0, 6.2, (92, 70, 48), (60, 44, 30))          # 무덤방(작은 아치 공동)
        iso.fpoly(kind, X, Y, Zp, [(0, H - 2.2), (R, H - 2.2), (R, H), (0, H)], (236, 226, 198), (130, 108, 78), 0.15)
    # 물방울(비가 스며 류사이트가 녹음) — 자기 치유와는 다른 메커니즘
    for (u, v) in [(4.0, 10.5), (7.0, 9.0), (9.0, 11.0)]:
        px, py = iso.face("L", Xc, Yc, Zp, [(u, v)])[0]
        L.poly([(px, py - 1.4), (px - 0.8, py), (px + 0.8, py)], fill=(80, 140, 206))
    x, y = iso.p(S - 5, S - 5)
    cypress(L, x, y, 10, 2.4)
    x, y = iso.p(5, S - 6)
    olive(L, x, y, 3.4)
    for (X, Y) in [(S - 9, S - 3), (S - 12, S - 4)]:
        x, y = iso.p(X, Y)
        person(L, x, y, 4.4, (150, 70, 52) if X > S - 10 else (92, 120, 150))



# ───────────────────────── 배치 명세 ─────────────────────────
POS = {"aqueduct": (270, 425, 68), "metella": (388, 440, 64), "portus": (150, 455, 64)}


def objects():
    ax, ay, aw = POS["aqueduct"]
    mx, my, mw = POS["metella"]
    qx, qy, qw = POS["portus"]
    return [
        dict(z=80, name="수도교", tier="Support", region=(ax - 46, ay - 46, ax + 46, ay + 36), fn=draw_aqueduct, args=(ax, ay, aw)),
        dict(z=90, name="카이킬리아 메텔라 무덤", tier="Support", region=(mx - 46, my - 46, mx + 46, my + 36), fn=draw_metella, args=(mx, my, mw)),
        dict(z=100, name="포르투스 항", tier="Support", region=(qx - 42, qy - 40, qx + 62, qy + 36), fn=draw_portus, args=(qx, qy, qw)),
    ]


def labels():
    return [
        dict(order=40, kind="label", name="수도교", T=(270.0, 443.5), M=M_WALL_DN, mode="below", side="L", col=C_SUP_T,
             en=["AQUA CLAUDIA"], ko="아쿠아 클라우디아", sup=None, body=["석재 아치에 하드리아누스기", "벽돌면 콘크리트로 보수한", "구간(붉은 두 칸)"], gap=9.5),
        dict(order=50, kind="label", name="메텔라 무덤", T=(356.0, 440.0), M=M_WALL_DN, mode="above", side="R", col=C_SUP_T,
             en=["CAECILIA METELLA"], ko="카이킬리아 메텔라 무덤", sup=None,
             body=["지름 29m 콘크리트 드럼", "젖을 때마다 류사이트가", "녹아 접합부를 다시 짬", "※ 알갱이 치유와는 다름"], gap=2.4),
        dict(order=60, kind="label", name="포르투스 항", T=(150.0, 436.0), M=M_WALL_DN, mode="above", side="R", col=C_SUP_T,
             en=["PORTUS"], ko="포르투스 항", sup=None,
             body=["트라야누스 육각 내항", "(약 100~112년)", "방파제 모르타르: 로마", "근교+포추올리 화산재", "바닷물은 항구 구조물만"], gap=2.4, plate=True),
    ]


def extra_labels(LB):
    pass
