# -*- coding: utf-8 -*-
# 로마 콘크리트 A2 와이어프레임 — 화면 평행 정보 패널(타이틀·Basic L1/L2/R1·하단 B1/B2/B3·푸터)과 Detail 확대 창
# 담당 패키지: panels · 이 파일은 담당 워커만 고친다(공용 도구는 common.py, 조립은 main.py).

from common import *
from common import _a
import common as C
from m_core import cell_verts, NCELL

PANEL_RECT = {"정의": (18, 20, 118, 68), "레시피": (18, 76, 118, 132), "위치도": (302, 20, 402, 92),
              "석회": (18, 505, 170, 565), "연대기": (178, 505, 294, 565), "수명비교": (302, 505, 402, 565)}
# ───────────────────────── 패널(화면 평행 정보 구획) ─────────────────────────
def pin(P, x, y, col):
    """물방울 핀(2.5×3.6mm) — 끝점이 (x,y)"""
    P.poly([(x, y), (x - 1.2, y - 2.0), (x + 1.2, y - 2.0)], fill=col)
    P.ell(x, y - 2.5, 1.25, 1.25, fill=col)
    P.ell(x, y - 2.5, 0.45, 0.45, fill=(255, 255, 255))


def zone(P, x0, y0, x1, y1, tier, en, ko):
    """패널 구획: 0.3mm 점선 영역선(최종 인쇄에는 상자 없음), 영문 초압축 대문자 제목 + 국문 부제(윗선 정렬), 티어 칩"""
    col = TIER_COL[tier]
    tcol = TIER_TXT[tier]
    P.dashed_rect(x0, y0, x1, y1, col, lw=0.3, dash=2.6, gap=1.5)
    fe = fnt("en", 7.5 / 0.71)
    P.text(x0 + 2.5, y0 + 2.0 + 7.5, en, fe, tcol)
    wk = tw(en, fe)
    P.text(x0 + 2.5 + wk + 2.0, y0 + 2.0 + 3.2, ko, fnt("b", 3.6), tcol)
    f = fnt("s", 2.2)
    wc = tw(tier, f) + 3.0
    P.rect(x1 - wc - 1.6, y0 + 1.6, x1 - 1.6, y0 + 5.4, fill=col)
    P.text_c(x1 - 1.6 - wc / 2.0, y0 + 4.3, tier, f, (255, 255, 255))


def tline(P, x, y, s, em=2.5, col=INK, kind="m"):
    P.text(x, y, s, fnt(kind, em), col)


def panel_definition(P):
    x0, y0, x1, y1 = PANEL_RECT["정의"]
    zone(P, x0, y0, x1, y1, "Basic", "DEFINITION", "로마 콘크리트란?")
    tline(P, x0 + 2.5, y0 + 17.0, "석회와 화산재, 굵은 골재를 물과 섞어 굳힌", 2.7)
    tline(P, x0 + 2.5, y0 + 20.8, "고대 로마의 콘크리트(철근 없음)", 2.7)
    cells = ["결합재", "굵은 골재", "반죽·다짐", "철근", "수명", "대표 건물"]
    cw = (x1 - x0 - 5.0) / 3.0
    for i, nm in enumerate(cells):
        cx = x0 + 2.5 + (i % 3) * cw
        cy = y0 + 25.0 + (i // 3) * 10.6
        P.line([(cx, cy), (cx + cw - 2.0, cy)], C_BASIC, 0.3, joint=False)
        tline(P, cx, cy + 3.4, nm, 2.3, C_BASIC, "s")
        P.rect(cx, cy + 4.6, cx + cw - 2.0 - (i % 2) * 7, cy + 5.8, fill=GREYBAR)


def panel_recipe(P):
    x0, y0, x1, y1 = PANEL_RECT["레시피"]
    zone(P, x0, y0, x1, y1, "Basic", "THE RECIPE", "레시피·순서")
    chips = ["생석회", "화산재", "화산암 골재", "물"]
    cw = (x1 - x0 - 5.0 - 3 * 2.0) / 4.0
    for i, nm in enumerate(chips):
        cx = x0 + 2.5 + i * (cw + 2.0)
        cy = y0 + 14.0
        P.rect(cx, cy, cx + cw, cy + 9.0, outline=C_BASIC, lw=0.3)
        P.rect(cx + 1.2, cy + 1.2, cx + 6.2, cy + 6.2, fill=GREYBAR)
        P.text_c(cx + cw / 2.0, cy + 8.0 - 0.6, nm, fnt("s", 2.2 if len(nm) > 4 else 2.4), INK)
    steps = ["① 마른 채 섞기", "② 물 붓기", "③ 끓어오름"]
    sx = x0 + 2.5
    for i, st in enumerate(steps):
        w = tw(st, fnt("s", 2.5)) + 4.0
        P.rect(sx, y0 + 26.5, sx + w, y0 + 32.5, fill=C_BASIC)
        P.text_c(sx + w / 2.0, y0 + 30.9, st, fnt("s", 2.5), (255, 255, 255))
        if i < 2:
            P.poly([(sx + w + 1.0, y0 + 29.5 - 1.6), (sx + w + 3.6, y0 + 29.5), (sx + w + 1.0, y0 + 29.5 + 1.6)], fill=C_BASIC)
        sx += w + 4.8
    tline(P, x0 + 2.5, y0 + 40.0, "화산재: 바다 공사=포추올리 일대, 로마 건물=알바노 구릉", 2.3)
    tline(P, x0 + 2.5, y0 + 43.8, "물: 육상 건물=민물, 항구 구조물만 바닷물", 2.3)
    tline(P, x0 + 2.5, y0 + 47.6, "반죽은 붓지 않고 거푸집에 다져 넣는다", 2.3)


ITALY = [(0.20, 0.00), (0.16, 0.10), (0.20, 0.20), (0.30, 0.30), (0.38, 0.40), (0.48, 0.47), (0.54, 0.53), (0.62, 0.62),
         (0.70, 0.72), (0.78, 0.84), (0.84, 0.96), (0.92, 1.00), (0.98, 0.88), (0.90, 0.76), (0.98, 0.64), (0.94, 0.52),
         (0.84, 0.46), (0.72, 0.38), (0.62, 0.28), (0.54, 0.18), (0.46, 0.08), (0.40, 0.00)]


def panel_where(P):
    x0, y0, x1, y1 = PANEL_RECT["위치도"]
    zone(P, x0, y0, x1, y1, "Basic", "WHERE", "위치도")
    mx0, my0, mw, mh = x0 + 24.5, y0 + 14.0, 51.0, 53.0
    poly = [(mx0 + a * mw, my0 + b * mh) for a, b in ITALY]
    gy = my0
    while gy < my0 + mh:
        gx = mx0
        while gx < mx0 + mw:
            if in_poly((gx, gy), poly):
                P.ell(gx, gy, 0.36, 0.36, fill=(196, 166, 98))
            gx += 1.3
        gy += 1.3
    # 핀: 로마(콜로세움·포르투스 공유 핀) · 알바노 구릉 · 포추올리 · 베수비오
    pts = {"rome": (mx0 + 0.31 * mw, my0 + 0.32 * mh), "alban": (mx0 + 0.34 * mw, my0 + 0.345 * mh),
           "poz": (mx0 + 0.495 * mw, my0 + 0.465 * mh), "ves": (mx0 + 0.535 * mw, my0 + 0.48 * mh)}
    pin(P, pts["rome"][0] - 0.8, pts["rome"][1], C_BASIC)
    pin(P, pts["alban"][0] + 1.4, pts["alban"][1] + 0.6, C_BASIC)
    pin(P, pts["poz"][0] - 0.6, pts["poz"][1], C_BASIC)
    pin(P, pts["ves"][0] + 1.6, pts["ves"][1] + 0.5, C_BASIC)
    # 좌우 2열 라벨 + 직교 지시선(규선 → 직교로 꺾여 핀까지, 끝 장식 없음)
    f1, f2 = fnt("b", 2.5), fnt("m", 2.2)
    lx = x0 + 2.5
    rx = mx0 + mw + 4.0
    items = [("로마", "콜로세움·포르투스", lx, y0 + 15.0, pts["rome"][0] - 0.8, pts["rome"][1] - 3.0, "L"),
             ("알바노 구릉", "로마 건물의 화산재", lx, y0 + 40.0, pts["alban"][0] + 1.4, pts["alban"][1] + 0.6 - 0.2, "L"),
             ("포추올리", "바다 공사용 화산재", rx, y0 + 28.0, pts["poz"][0] - 0.6, pts["poz"][1] - 3.0, "R"),
             ("베수비오", "79년 분화", rx, y0 + 58.0, pts["ves"][0] + 1.6, pts["ves"][1] + 0.5 - 0.2, "R")]
    for nm, sub, tx, ty, px_, py_, side in items:
        wl = max(tw(nm, f1), tw(sub, f2))
        P.text(tx, ty, nm, f1, C_BASIC)
        P.text(tx, ty + 3.4, sub, f2, INK)
        ry = ty + 4.4
        P.line([(tx, ry), (tx + wl, ry)], C_BASIC, 0.2, joint=False)
        ex = tx + wl if side == "L" else tx
        P.line([(ex, ry), (px_, ry), (px_, py_)], C_BASIC, 0.2, joint=False)


def panel_lime(P):
    x0, y0, x1, y1 = PANEL_RECT["석회"]
    zone(P, x0, y0, x1, y1, "Detail", "LIME CLASTS", "석회 알갱이·자가치유")
    caps = [("석회 알갱이", "뜨거운 혼합에서 남음"), ("균열 + 빗물", "틈으로 스며듦"), ("칼슘 용출", "알갱이가 녹아 나옴"), ("방해석 봉합", "결정이 균열을 메움")]
    cw = 31.0
    for i, (a, b) in enumerate(caps):
        cx = x0 + 3.0 + i * (cw + 4.0)
        cy = y0 + 14.0
        P.rect(cx, cy, cx + cw, cy + 26.0, fill=(236, 222, 188), outline=C_DETAIL, lw=0.3)
        # 콘크리트 단면 자리(점·균열·결정)
        for k in range(9):
            P.ell(cx + 4 + (k * 7) % 24, cy + 5 + (k * 11) % 16, 0.5, 0.5, fill=GREYBAR_D)
        if i == 0:
            P.ell(cx + cw / 2, cy + 13, 3.6, 3.0, fill=(252, 250, 244), outline=C_DETAIL, lw=0.25)
        if i >= 1:
            P.line([(cx + cw / 2 - 1, cy), (cx + cw / 2 + 2, cy + 7), (cx + cw / 2 - 2, cy + 14), (cx + cw / 2 + 1, cy + 22)], C_INK if False else INK, 0.35)
        if i == 1:
            for k in range(3):
                P.line([(cx + 5 + k * 9, cy + 1.5), (cx + 5 + k * 9 - 1, cy + 5)], (70, 120, 190), 0.4, joint=False)
        if i == 2:
            P.ell(cx + cw / 2 + 5, cy + 18, 2.4, 2.0, fill=(252, 250, 244), outline=C_DETAIL, lw=0.2)
            for k in range(4):
                P.ell(cx + cw / 2 + 1 - k * 1.8, cy + 8 + k * 2.4, 0.7, 0.7, fill=(70, 120, 190))
        if i == 3:
            for k in range(5):
                P.poly([(cx + cw / 2 - 2 + k * 0.8, cy + 3 + k * 4.4), (cx + cw / 2 + 0.6 + k * 0.8, cy + 2 + k * 4.4), (cx + cw / 2 + 1.0 + k * 0.8, cy + 5.4 + k * 4.4)], fill=(252, 250, 244), outline=C_DETAIL, lw=0.15)
        P.text_c(cx + cw / 2, cy + 30.6, a, fnt("s", 2.5), C_DETAIL_T)
        P.text_c(cx + cw / 2, cy + 34.4, b, fnt("m", 2.2), INK)
        if i < 3:
            ax = cx + cw + 0.6
            P.poly([(ax, cy + 11), (ax + 2.8, cy + 13), (ax, cy + 15)], fill=C_DETAIL)
    tline(P, x0 + 3.0, y1 - 3.0, "같은 단면, 같은 시점 4칸 — 6단계에서 이어지는 확대 창의 풀이", 2.2, C_DETAIL_T)


def panel_history(P):
    x0, y0, x1, y1 = PANEL_RECT["연대기"]
    zone(P, x0, y0, x1, y1, "Basic", "HISTORY", "연대기·근거")
    ev = [("79년", "폼페이 공사 현장", "화산재에 매몰"), ("2017", "바닷물이 키운", "새 광물 연구"), ("2023", "MIT: 뜨거운 혼합", "가설 제시"), ("2025", "폼페이 현장에서", "가설 확인")]
    ly = y0 + 31.0
    P.line([(x0 + 4, ly), (x1 - 4, ly)], C_BASIC, 0.35, joint=False)
    P.poly([(x1 - 4, ly - 1.4), (x1 - 1.6, ly), (x1 - 4, ly + 1.4)], fill=C_BASIC)
    cwid = (x1 - x0 - 8) / 4.0
    for i, (yr, a, b) in enumerate(ev):
        cx = x0 + 4 + cwid * (i + 0.12)
        P.ell(cx, ly, 1.1, 1.1, fill=C_BASIC)
        up = (i % 2 == 0)
        if up:
            P.line([(cx, ly - 1.2), (cx, ly - 5.0)], C_BASIC, 0.25, joint=False)
            tline(P, cx + 1.6, y0 + 20.4, yr, 3.4, C_BASIC, "b")
            tline(P, cx + 1.6, y0 + 24.2, a, 2.2)
            tline(P, cx + 1.6, y0 + 27.4, b, 2.2)
        else:
            P.line([(cx, ly + 1.2), (cx, ly + 5.0)], C_BASIC, 0.25, joint=False)
            tline(P, cx + 1.6, y0 + 41.4, yr, 3.4, C_BASIC, "b")
            tline(P, cx + 1.6, y0 + 45.2, a, 2.2)
            tline(P, cx + 1.6, y0 + 48.4, b, 2.2)
    tline(P, x0 + 3.0, y1 - 3.0, "2023 → 2025: 실마리 → 현장 확인(과장 금지)", 2.1, C_BASIC)


def panel_100v2000(P):
    x0, y0, x1, y1 = PANEL_RECT["수명비교"]
    zone(P, x0, y0, x1, y1, "Basic", "100 VS 2000", "수명 비교")
    base = y1 - 9.0
    hb = 30.0
    P.rect(x0 + 10, base - hb * 100 / 2000.0, x0 + 24, base, fill=GREYBAR_D)
    P.rect(x0 + 40, base - hb, x0 + 54, base, fill=C_BASIC)
    P.line([(x0 + 4, base), (x1 - 4, base)], INK, 0.3, joint=False)
    tline(P, x0 + 7, base - 3.2, "100년", 3.2, INK, "b")
    tline(P, x0 + 36, base - hb - 1.6, "2000년", 3.2, C_BASIC, "b")
    tline(P, x0 + 7, base + 3.6, "현대 콘크리트", 2.2)
    tline(P, x0 + 36, base + 3.6, "로마 콘크리트", 2.2)
    tline(P, x0 + 60, y0 + 16.0, "수명(사용 기록) 비교", 2.3, C_BASIC, "s")
    tline(P, x0 + 60, y0 + 19.8, "— 강도 비교가 아님", 2.3, INK)
    tline(P, x0 + 60, y0 + 24.2, "현대 약 30MPa", 2.1, GREYBAR_D)
    tline(P, x0 + 60, y0 + 27.4, "로마 약 6MPa", 2.1, GREYBAR_D)


def draw_title(P):
    """타이틀 록업: 로마 신전 정면 입면(월드의 등각과 대비되는 화면 평행). 헥사스타일 6열주 + 엔타블러처 + 계단, 글자는 중심 210에 가운데 정렬."""
    cx = 210.0
    tint = (244, 214, 208)
    # 페디먼트
    P.poly([(126.5, 35.0), (cx, 10.0), (293.5, 35.0)], fill=tint, outline=C_CORE, lw=0.8)
    P.poly([(139.0, 33.0), (cx, 14.5), (281.0, 33.0)], fill=(250, 232, 226), outline=C_CORE, lw=0.35)
    P.ell(cx, 25.0, 3.4, 3.4, fill=(250, 244, 230), outline=C_CORE, lw=0.5)
    # 엔타블러처(프리즈) + 영문 부제
    P.rect(128.5, 35.0, 291.5, 43.5, fill=(252, 240, 226), outline=C_CORE, lw=0.6)
    P.text_c(cx, 41.0, "ANCIENT ROME · SELF-HEALING CONCRETE", fnt("en", 3.4 / 0.71), C_CORE_T)
    # 열주 6개 (왼 3 + 오른 3), 높이 40mm
    for k in range(6):
        x = (141.0 + 12.5 * k) if k < 3 else (254.0 + 12.5 * (k - 3))
        P.rect(x - 4.2, 44.0, x + 4.2, 46.6, fill=(244, 232, 214), outline=C_CORE, lw=0.4)
        P.rect(x - 2.9, 46.6, x + 2.9, 80.0, fill=(250, 242, 228), outline=C_CORE, lw=0.4)
        for fx in (-1.0, 0.0, 1.0):
            P.line([(x + fx, 47.2), (x + fx, 79.4)], (222, 196, 180), 0.18, joint=False)
        P.rect(x - 4.2, 80.0, x + 4.2, 82.6, fill=(244, 232, 214), outline=C_CORE, lw=0.4)
    # 중앙 제목 판
    P.rect(172.0, 46.0, 248.0, 79.5, fill=(255, 250, 238), outline=C_CORE, lw=0.8)
    P.rect(173.8, 47.8, 246.2, 77.7, outline=C_CORE, lw=0.3)
    P.text_c(cx, 60.2, "ROMAN CONCRETE", fnt("en", 8.6 / 0.71), C_CORE_T)
    P.text_c(cx, 67.6, "로마 콘크리트", fnt("b", 4.6), C_INK)
    # 리본(슬로건)
    P.poly([(150.0, 71.0), (270.0, 71.0), (270.0, 78.6), (150.0, 78.6)], fill=(250, 226, 214), outline=C_CORE, lw=0.5)
    P.text_c(cx, 76.4, "갈라져도 물을 만나 스스로 메우는 콘크리트", fnt("b", 3.6), C_CORE_T)
    # 계단
    P.rect(130.0, 82.6, 290.0, 87.4, fill=(246, 234, 218), outline=C_CORE, lw=0.5)
    P.rect(126.5, 87.4, 293.5, 92.0, fill=(240, 224, 208), outline=C_CORE, lw=0.5)


# ───────────────────────── Detail 확대 창(6단계 → 석회 알갱이) ─────────────────────────
def draw_zoom(L, cx, cy, D=72.0):
    r = D / 2.0
    L.ell(cx, cy, r, r, fill=(238, 224, 192), outline=C_DETAIL, lw=1.0)
    L.ell(cx, cy, r - 1.4, r - 1.4, outline=(255, 255, 255), lw=0.5)
    # 콘크리트 단면 확대: 모르타르 바탕 + 굵은 골재 + 흰 석회 알갱이 + 균열 + 결정
    L.ell(cx, cy, r - 3.0, r - 3.0, fill=(206, 200, 186))
    # 골재(둥근 돌) — 원 안쪽에 드는 것만
    for i in range(34):
        a = rnd() * 2 * math.pi
        rr = (r - 8) * math.sqrt(rnd())
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        sz = 1.4 + rnd() * 2.6
        L.ell(x, y, sz, sz * 0.8, fill=(142, 130, 116) if rnd() > 0.4 else (176, 164, 148), outline=(110, 100, 90), lw=0.15)
    # 흰 석회 알갱이
    for i in range(14):
        a = rnd() * 2 * math.pi
        rr = (r - 10) * math.sqrt(rnd())
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        sz = 1.2 + rnd() * 2.4
        L.ell(x, y, sz, sz * 0.82, fill=(253, 252, 248), outline=C_DETAIL, lw=0.25)
    # 균열(지그재그)과 방해석 결정
    zz = [(cx - 14, cy - 28), (cx - 8, cy - 18), (cx - 15, cy - 8), (cx - 7, cy + 2), (cx - 13, cy + 12), (cx - 6, cy + 24)]
    L.line(zz, (60, 46, 36), 0.7)
    for k in range(7):
        x, y = zz[1 + (k % 4)]
        L.poly([(x + 1.0 + k * 0.2, y - 2.0), (x + 3.0 + k * 0.2, y - 3.0), (x + 3.4 + k * 0.2, y - 0.4)], fill=(253, 252, 248), outline=C_DETAIL, lw=0.15)
    # 확대 창 안쪽 점선 십자(확대 단면 자리 표시)
    L.dashed((cx - r + 6, cy), (cx + r - 6, cy), (255, 255, 255), 0.3, 2.0, 1.6)
    L.dashed((cx, cy - r + 6), (cx, cy + r - 6), (255, 255, 255), 0.3, 2.0, 1.6)


def draw_footer(P, R=None):
    x0, y0, x1, y1 = 18, 568, 402, 581
    P.dashed_rect(x0, y0, x1, y1, C_GREY, lw=0.3, dash=2.6, gap=1.5)
    P.rect(x0 + 2, y0 + 2, x0 + 40, y1 - 2, outline=C_GREY, lw=0.25)
    P.text_c(x0 + 21, y0 + 7.8, "로고 자리", fnt("m", 2.3), C_GREY)
    P.rect(x1 - 40, y0 + 2, x1 - 2, y1 - 2, outline=C_GREY, lw=0.25)
    P.text_c(x1 - 21, y0 + 7.8, "QR 자리", fnt("m", 2.3), C_GREY)
    # 1줄: 티어 색 범례
    items = [("Hero", "아레나(티어 없음)"), ("Core", "제작 과정"), ("Basic", "기본 정보"), ("Detail", "확대·세부"), ("Support", "사례"), ("Support-2", "베수비오")]
    cx = x0 + 45
    fch, fb = fnt("s", 2.0), fnt("m", 2.0)
    for tier, desc in items:
        col = C_ARENA_T if tier == "Hero" else TIER_COL[tier]
        w = tw(tier, fch) + 2.4
        P.rect(cx, y0 + 1.6, cx + w, y0 + 4.8, fill=col)
        P.text_c(cx + w / 2, y0 + 4.1, tier, fch, (255, 255, 255))
        P.text(cx + w + 1.0, y0 + 4.1, desc, fb, INK)
        cx += w + tw(desc, fb) + 4.2
    # 2줄: 주석
    P.text(x0 + 45, y0 + 7.8, "※ 와이어프레임 " + C.VERSION + ": 배치 도식(최종 렌더 아님) · 거리·방위는 구도 우선으로 압축, 실제 위치는 위치도 · 베수비오는 79년 이전 모습(복원 상상도) · 크기는 투영 기준 아레나 > Core > Basic·Detail > Support > Support-2", fnt("m", 1.8), C_GREY)
    # 3줄: 자동 실측 치수(치수는 라벨이 아니라 이 줄로만 표기)
    if R is not None and "areas" in R:
        order = ["아레나", "Core 제작 과정", "확대 창", "욕장", "판테온", "수도교", "카이킬리아 메텔라 무덤", "트라야누스 시장", "포르투스 항", "베수비오"]
        short = {"Core 제작 과정": "Core", "카이킬리아 메텔라 무덤": "메텔라 무덤", "포르투스 항": "포르투스"}
        parts = []
        for nm in order:
            if nm in R["areas"]:
                t, ar, aa, w_, h_ = R["areas"][nm]
                parts.append("%s %.0f×%.0f" % (short.get(nm, nm), w_, h_))
        P.text(x0 + 45, y0 + 11.2, "투영 크기(폭×높이 mm, 레이어 자동 실측): " + " · ".join(parts), fnt("m", 1.8), C_GREY)



# ───────────────────────── 배치 명세 ─────────────────────────
POS = {"zoom": (58, 415, 66)}
PANELS = [("정의", "Basic", "로마 콘크리트란?", panel_definition), ("레시피", "Basic", "레시피·순서", panel_recipe),
          ("위치도", "Basic", "위치도", panel_where), ("석회", "Detail", "석회 알갱이 패널", panel_lime),
          ("연대기", "Basic", "연대기·근거", panel_history), ("수명비교", "Basic", "100 vs 2000", panel_100v2000)]


def objects():
    zx, zy, zd = POS["zoom"]
    return [dict(z=70, name="확대 창", tier="Detail", region=(zx - zd / 2 - 2, zy - zd / 2 - 2, zx + zd / 2 + 2, zy + zd / 2 + 2), fn=draw_zoom, args=(zx, zy, zd))]


def labels():
    return [dict(order=150, kind="flag", name="확대 창", T=(36.8, 389.7), M=M_WALL_DN, col=C_DETAIL_T, en="DETAIL", ko="확대 창", side="R", mode="above", pole=8.0)]


def extra_labels(LB):
    """6단계 → 확대 창: 셀 앞 꼭짓점의 굳은 단면에서 수직 지시선, 확대 창 → 하단 Detail 패널 윗변"""
    zx, zy, zd = POS["zoom"]
    bx_, by_ = cell_verts(NCELL - 1)["B"][0], cell_verts(NCELL - 1)["B"][1] - 12.4
    LB.line([(bx_, by_), (bx_, zy - zd / 2.0)], C_DETAIL_T, LEAD_LW, joint=False, kind="지시선")
    LB.dot(bx_, by_, DOT_R, C_DETAIL_T)
    LABELS.append({"이름": "확대 창 지시선", "종류": "지시선", "다각형": [], "대상": (bx_, by_), "열": ""})
    bx2 = bx_
    LB.line([(bx2, zy + zd / 2.0), (bx2, PANEL_RECT["석회"][1])], C_DETAIL_T, LEAD_LW, joint=False, kind="지시선")
    LB.dot(bx2, PANEL_RECT["석회"][1], DOT_R, C_DETAIL_T)
