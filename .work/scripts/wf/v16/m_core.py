# -*- coding: utf-8 -*-
# 로마 콘크리트 A2 와이어프레임 — Core: 로마 콘크리트 제작 과정(신문식 셀 체인)
# 담당 패키지: core · 이 파일은 담당 워커만 고친다(공용 도구는 common.py, 조립은 main.py).

from common import *
from common import _a
import common as C

# ───────────────────────── 배치 설정(mm) ─────────────────────────
CORE_W = 80.0                       # 셀 마름모 화면 폭
CORE_HW = CORE_W / 2.0
CORE_S = CORE_W / SQ3               # 셀 변 길이(화면)
CORE_HH = CORE_S / 2.0              # 반 셀 높이
CORE_X0 = 18.0                      # 체인 왼끝
CORE_Y0 = 190.0                     # 첫 셀 중심 y
NCELL = 7                           # 셀 7개: 1·1·1·2·1·1(뜨거운 혼합 2셀), 마지막 행은 1셀


def cell_center(k):
    return (CORE_X0 + CORE_HW + (CORE_HW if k % 2 else 0.0), CORE_Y0 + k * CORE_HH)


def cell_verts(k):
    cx, cy = cell_center(k)
    return {"T": (cx, cy - CORE_HH), "R": (cx + CORE_HW, cy), "B": (cx, cy + CORE_HH), "L": (cx - CORE_HW, cy)}


NOTCH_X = CORE_X0 + CORE_W          # 오른쪽 열 셀의 위·아래 꼭짓점 x(톱니 안쪽 오목점)
NOTCH_Y = CORE_Y0 + 4 * CORE_HH     # 강이 꺾이는 톱니 행(k=3 아래·k=5 위 꼭짓점)

# ───────────────────────── Core: 로마 콘크리트 제작 과정(신문식 셀 체인) ─────────────────────────
STEP_NAMES = ["재료 준비", "마른 혼합", "물 붓기", "뜨거운 혼합", "타설·다짐", "굳기·석회 알갱이 형성"]
STEP_BODY = [["생석회·화산재·굵은 화산암", "골재를 모아 둔다"],
             ["생석회와 화산재를", "물 없이 먼저 섞는다"],
             ["마른 가루에 물을 붓는다", "육상은 민물, 항구만 바닷물"],
             ["물과 만난 생석회가 끓으며", "열을 낸다 → 알갱이가 남음"],
             ["거푸집에 되직한 반죽을", "다져 넣는다(붓지 않음)"],
             ["굳은 속에 흰 알갱이가 박힌다", "↓ 아래 확대 창으로"]]
CELL_STEP = [0, 1, 2, 3, 3, 4, 5]                 # 셀 → 단계 인덱스(뜨거운 혼합 2셀)
STEP_CELL = [0, 1, 2, 3, 5, 6]                    # 단계가 시작되는 셀
FLOOR_TXT = [("① 재료 모으기", "생석회·화산재·골재"), ("② 마른 채 섞기", "물 없이 먼저"), ("③ 물 붓기", "육상 민물·항구 바닷물"),
             ("④ 뜨거운 혼합", "물과 만난 생석회가 끓음"), ("⑤ 열이 알갱이를 남김", "흰 석회 알갱이"),
             ("⑥ 거푸집에 다져 넣기", "붓지 않는다"), ("⑦ 굳은 단면", "알갱이는 확대 창으로")]
BOARD_H = 15.0                                    # 단계 간판 높이(mm)
CELL_CREAM = (250, 238, 210)
CELL_SEAM = (218, 198, 164)
BOARD_FACE = (240, 220, 178)
BOARD_TOP = (200, 60, 70)


def worker(L, x, y, h=14.5, tunic=(176, 96, 60), tool=None, facing=1):
    """작업자 실루엣(키 h). tool: hoe/rammer/bucket/point/None"""
    L.ell(x + 0.4, y + 0.2, h * 0.24, h * 0.08, fill=(110, 90, 62, 150))
    L.poly([(x - h * 0.13, y), (x - h * 0.02, y), (x - h * 0.02, y - h * 0.42), (x - h * 0.14, y - h * 0.42)], fill=(98, 76, 52))
    L.poly([(x + h * 0.02, y), (x + h * 0.13, y), (x + h * 0.14, y - h * 0.42), (x + h * 0.02, y - h * 0.42)], fill=(98, 76, 52))
    L.poly([(x - h * 0.19, y - h * 0.40), (x + h * 0.19, y - h * 0.40), (x + h * 0.15, y - h * 0.76), (x - h * 0.15, y - h * 0.76)], fill=tunic, outline=shade(tunic, 0.7), lw=0.15)
    L.ell(x, y - h * 0.88, h * 0.12, h * 0.12, fill=(228, 188, 152), outline=(150, 112, 84), lw=0.12)
    if tool == "hoe":
        L.line([(x + h * 0.15, y - h * 0.62), (x + h * 0.55 * facing, y - h * 0.12)], (110, 80, 50), 0.4, joint=False)
        L.line([(x + h * 0.55 * facing, y - h * 0.12), (x + h * 0.7 * facing, y - h * 0.16)], (90, 90, 96), 0.7, joint=False)
    elif tool == "rammer":
        L.line([(x + h * 0.16, y - h * 0.9), (x + h * 0.3 * facing, y - h * 0.05)], (110, 80, 50), 0.45, joint=False)
        L.rect(x + h * 0.3 * facing - 1.2, y - 1.2, x + h * 0.3 * facing + 1.2, y, fill=(96, 96, 100))
    elif tool == "bucket":
        L.poly([(x + h * 0.2, y - h * 0.55), (x + h * 0.42, y - h * 0.55), (x + h * 0.38, y - h * 0.3), (x + h * 0.24, y - h * 0.3)], fill=(150, 112, 74), outline=(96, 70, 44), lw=0.14)
    elif tool == "point":
        L.line([(x + h * 0.17, y - h * 0.66), (x + h * 0.5 * facing, y - h * 0.86)], tunic, 0.8, joint=False)


def pile(L, x, y, r, h, col, dots=None):
    """더미: (x,y) 바닥 중심, 반지름 r, 높이 h"""
    L.ell(x + 0.6, y + 0.2, r * 1.02, r * 0.34, fill=(120, 98, 64, 120))
    L.poly([(x - r, y), (x - r * 0.45, y - h * 0.7), (x, y - h), (x + r * 0.5, y - h * 0.65), (x + r, y)], fill=col, outline=shade(col, 0.68), lw=0.2)
    L.pie(x, y, r, r * 0.34, 0, 180, fill=shade(col, 0.9))
    if dots:
        for i in range(8):
            L.ell(x - r * 0.6 + rnd() * r * 1.2, y - h * 0.15 - rnd() * h * 0.55, 0.5, 0.42, fill=dots)


def pill(L, x, y, text, M, ax_u=0.0):
    """기계 알약(갈색, 밝은 황토 글자): 벽면 평면 위. (x,y)는 알약 왼쪽 아래 모서리의 화면 위치"""
    f = fnt("s", 2.5)
    w = tw(text, f) + 2.4
    h = 4.6
    pf = Flat(w + 1, h + 1, (210, 175, 138))
    pf.d.rounded_rectangle([2, 2, 2 + w * KD, 2 + h * KD], radius=int(h * KD / 2), fill=(127, 91, 77, 255))
    pf.text(1.2, 3.3, text, f, (214, 180, 142))
    (a, b), (c, d) = M
    affine_paste(L, pf, M, x - b * h, y - d * h)
    return w


def draw_board(L, edge_a, edge_b, wall, height, name, body, num, badge_end, title_style=False, en=None):
    """등각 수직 보드. edge_a→edge_b: 셀 뒤 가장자리(화면 mm). wall: 'NW'(YZ벽, 글줄 ↗) 또는 'NE'(XZ벽, 글줄 ↘).
    badge_end: 번호 배지를 달 쪽('a' 또는 'b')."""
    ax_, ay_ = edge_a
    bx_, by_ = edge_b
    # 보드 면(평행사변형): 아래 변은 셀 가장자리, 위 변은 height만큼 위
    face = [(ax_, ay_), (bx_, by_), (bx_, by_ - height), (ax_, ay_ - height)]
    L.poly(face, fill=BOARD_FACE, outline=(120, 70, 50), lw=0.3)
    # 윗면(얇은 두께)과 끝 단면
    th = 1.6
    L.poly([(ax_, ay_ - height), (bx_, by_ - height), (bx_ + 0.0, by_ - height - th), (ax_, ay_ - height - th)], fill=BOARD_TOP)
    M = M_WALL_UP if wall == "NW" else M_WALL_DN
    # 글자: 보드 왼쪽(화면 x가 작은 쪽)에서 시작. 판 위 여백 1.6mm
    if wall == "NW":
        # 기준선 ↗: 왼쪽 끝이 아래쪽 점. 시작점 = 보드 왼쪽 아래 모서리 위
        sx, sy = ax_ if ax_ < bx_ else bx_, (ay_ if ax_ < bx_ else by_)
    else:
        sx, sy = ax_ if ax_ < bx_ else bx_, (ay_ if ax_ < bx_ else by_)
    inset = 2.0
    # 평면 좌표에서 u=inset, v=(height - 위 여백)부터
    usable = CORE_S - 2 * inset - (11.0 if not title_style else 0.0)
    lines = []
    base_v = 4.6
    if title_style:
        f = Flat(CORE_S * 2, height + 2, C_CORE_T)
        f.text(inset + 1.0, 10.6, en or "CORE", fnt("en", 8.2 / 0.71), C_CORE_T)
        f.text(inset + 1.0 + tw(en or "CORE", fnt("en", 8.2 / 0.71)) + 2.4, 10.6, name, fnt("b", 4.4), C_INK)
        # 평면 판의 (0,0) = 보드 왼쪽 위 → 화면: 왼쪽 아래 점에서 height 만큼 위
        (a, b), (c, d) = M
        affine_paste(L, f, M, sx, sy - height)
    else:
        f = Flat(CORE_S, height + 2, C_CORE_T)
        x_start = inset + (11.0 if badge_end == "a" else 0.0)

        def fit(txt, kind, em):
            w0 = tw(txt, fnt(kind, em))
            return em if w0 <= usable else em * usable / w0

        em_n = fit(name, "b", 3.5)
        f.text(x_start, 4.2, name, fnt("b", em_n), C_CORE_T)
        for i, ln in enumerate(body):
            em_b = fit(ln, "m", 2.7)
            f.text(x_start, 4.2 + 1.0 + 3.1 * (i + 1), ln, fnt("m", em_b), (64, 46, 36))
        affine_paste(L, f, M, sx, sy - height)
    # 번호 배지(타원 10.5×13): 바깥쪽 끝(배지는 보드 끝에 걸쳐서)
    if num is not None:
        if badge_end == "a":
            bxm, bym = ax_, ay_ - height * 0.5
        else:
            bxm, bym = bx_, by_ - height * 0.5
        inward = 5.25 if (bxm - 20 < 0 or True) else 0
        # 왼쪽 끝은 안쪽으로 당겨 x≥18을 지킨다
        if badge_end == "a":
            bxm += 5.25
        else:
            bxm -= 5.25
        L.ell(bxm, bym, 5.25, 6.5, fill=C_CORE, outline=(255, 255, 255), lw=0.5)
        L.text_c(bxm, bym + 2.9, str(num), fnt("b", 7.6), (255, 255, 255))


def floor_text(L, X, Y, lines, iso, em=2.2):
    """바닥에 눕힌 설명 글(기준선 +X ↘, 글자 위 = −Y ↗). (X,Y)는 첫 줄 기준선 왼쪽."""
    x0, y0 = iso.p(X, Y)
    for i, (txt, kind, col) in enumerate(lines):
        # 줄이 바뀌면 평면 +Y 방향(화면 ↙)으로 내려간다(글자 '아래')
        xx, yy = iso.p(X, Y + 3.4 * i)
        iso_text(L, txt, fnt(kind, em), col, M_FLOOR_SE, xx, yy)


def floor_arrow(iso, L, X, Y, direction, col=(86, 104, 58)):
    """바닥에 눕힌 올리브 화살표(길이 6.4, 폭 3.2). direction: 'X'(↘ +X) 또는 'Y'(↙ +Y). (X,Y)는 화살표 중심."""
    if direction == "X":
        pts = [(X - 3.2, Y - 0.55), (X + 0.6, Y - 0.55), (X + 0.6, Y - 1.6), (X + 3.2, Y), (X + 0.6, Y + 1.6), (X + 0.6, Y + 0.55), (X - 3.2, Y + 0.55)]
    else:
        pts = [(X - 0.55, Y - 3.2), (X - 0.55, Y + 0.6), (X - 1.6, Y + 0.6), (X, Y + 3.2), (X + 1.6, Y + 0.6), (X + 0.55, Y + 0.6), (X + 0.55, Y - 3.2)]
    iso.poly3([(a, b, 0.0) for a, b in pts], fill=col, ol=(60, 76, 40), lw=0.15)


def draw_core(L):
    """셀 7개 체인. 슬래브 하나로 합친 윤곽, 앞쪽 바깥 변에만 흙 측면, 내부는 이음선. 간판·번호 배지·기계 알약·작업자·바닥 글·바닥 화살표."""
    S = CORE_S
    T = 5.0
    verts = [cell_verts(k) for k in range(NCELL)]
    # ── 제목 보드(첫 두 셀의 뒤쪽 NE 변 뒤에 더 높게): 평면 −Y로 12 물린 선
    t0 = verts[0]["T"]
    off = (C30 * 12.0, -0.5 * 12.0)
    ta = (t0[0] + off[0], t0[1] + off[1])
    tb = (ta[0] + C30 * 1.7 * S, ta[1] + 0.5 * 1.7 * S)
    draw_board(L, ta, tb, "NE", 16.0, "로마 콘크리트 제작 과정", [], None, "b", title_style=True, en="CORE")
    # ── 슬래브 흙 측면(앞쪽 바깥 변)
    for k in range(NCELL):
        v = verts[k]
        if k % 2 == 0:       # 왼쪽 열: 남서 변
            a, b = v["L"], v["B"]
            L.poly([a, b, (b[0], b[1] + T), (a[0], a[1] + T)], fill=(134, 104, 66), outline=(80, 58, 36), lw=0.2)
            L.poly([a, b, (b[0], b[1] + 1.2), (a[0], a[1] + 1.2)], fill=GRASS)
        if k % 2 == 1 or k == NCELL - 1:       # 오른쪽 열: 남동 변(마지막 셀도 앞 오른쪽 변이 드러남)
            a, b = v["B"], v["R"]
            L.poly([a, b, (b[0], b[1] + T), (a[0], a[1] + T)], fill=(100, 76, 48), outline=(80, 58, 36), lw=0.2)
            L.poly([a, b, (b[0], b[1] + 1.2), (a[0], a[1] + 1.2)], fill=GRASS)
    # ── 슬래브 윗면(셀 합집합 윤곽) + 내부 이음선
    outline = [(60 - 0.0, 0)]  # placeholder
    xs0 = CORE_X0
    TL = verts[0]["T"]
    chain = []
    # 오른쪽 경계(위→아래)
    chain.append(verts[0]["T"])
    for k in range(0, NCELL - 1, 2):
        if k % 2 == 0 and k + 1 < NCELL:
            pass
    right = [verts[0]["T"], verts[0]["R"]]
    for k in range(1, NCELL, 2):
        right += [verts[k]["R"], verts[k]["B"]]
    right = [verts[0]["T"], verts[0]["R"]]
    for k in range(1, NCELL, 2):
        right.append(verts[k]["R"])
        right.append(verts[k]["B"])
    left_up = []
    last = verts[NCELL - 1]
    right.append(last["B"])
    for k in range(NCELL - 1, -1, -2):
        left_up.append(verts[k]["L"])
        left_up.append(verts[k]["T"])
    outline = right + left_up[:-1]
    L.poly(outline, fill=CELL_CREAM)
    for k in range(NCELL - 1):
        a = verts[k]
        b = verts[k + 1]
        if k % 2 == 0:
            L.line([a["R"], a["B"]], CELL_SEAM, 0.25, joint=False)
        else:
            L.line([a["B"], a["L"]], CELL_SEAM, 0.25, joint=False)
    L.line(outline + [outline[0]], C_CORE, 0.55)
    # ── 셀별 내용(뒤에서 앞으로)
    for k in range(NCELL):
        v = verts[k]
        iso = Iso(L, v["T"][0], v["T"][1])
        step = CELL_STEP[k]
        # 간판(단계가 시작되는 셀의 뒤 가장자리)
        if k in STEP_CELL:
            si = STEP_CELL.index(k)
            if k % 2 == 0:        # 왼쪽 열: 북서 변(YZ벽, 글줄 ↗), 번호 배지는 왼쪽(바깥) 끝
                draw_board(L, v["L"], v["T"], "NW", BOARD_H, STEP_NAMES[si], STEP_BODY[si], si + 1, "a")
            else:                 # 오른쪽 열: 북동 변(XZ벽, 글줄 ↘), 번호 배지는 오른쪽(바깥) 끝
                draw_board(L, v["T"], v["R"], "NE", BOARD_H, STEP_NAMES[si], STEP_BODY[si], si + 1, "b")
        draw_cell_content(L, iso, k)
        # 바닥 글
        ft = FLOOR_TXT[k]
        floor_text(L, 4.0, S - 8.2, [(ft[0], "b", (70, 52, 40)), (ft[1], "m", (96, 78, 60))], iso, 2.2)
        # 바닥 화살표(셀 경계마다 하나, 경계와 직교): 짝수→홀수는 +X(↘), 홀수→짝수는 +Y(↙)
        if k < NCELL - 1:
            if k % 2 == 0:
                floor_arrow(iso, L, S - 1.0, S * 0.62, "X")
            else:
                floor_arrow(iso, L, S * 0.62, S - 1.0, "Y")


def crate(iso, X0, Y0, X1, Y1, Z1, col=(190, 150, 100)):
    iso.box(X0, Y0, 0, X1, Y1, Z1, (shade(col, 1.08), col, shade(col, 0.78)), ol=(100, 72, 44), lw=0.16)


def draw_cell_content(L, iso, k):
    """셀 한 칸의 장면. 바닥 글 띠(Y 37~43)는 비워 두고, 소품은 Y ≤ 33에 둔다."""
    S = CORE_S
    P = iso.p
    if k == 0:       # 재료 준비
        x, y = P(12, 12); pile(L, x, y, 6.4, 8.0, (240, 236, 224), dots=(200, 196, 186))       # 생석회 더미
        x, y = P(28, 9); pile(L, x, y, 6.4, 7.0, (150, 140, 128))                                # 화산재 더미
        x, y = P(10, 26); pile(L, x, y, 6.0, 6.0, (92, 80, 70), dots=(150, 140, 130))            # 굵은 화산암 골재
        crate(iso, 31, 5, 39, 12, 5.0)
        x, y = P(31.6, 12); pill(L, x, y - 0.8, "자재 더미", M_WALL_DN)
        x, y = P(33, 27); worker(L, x, y, 14.0, (176, 96, 60), "point", 1)
    elif k == 1:     # 마른 혼합
        iso.rect3(6, 5, 38, 32, 0.0, (246, 232, 196), ol=(190, 168, 132), lw=0.25)
        x, y = P(21, 17); pile(L, x, y, 8.0, 7.2, (206, 198, 184), dots=(250, 248, 240))
        crate(iso, 31, 5, 38, 11, 4.0)
        x, y = P(31.6, 11); pill(L, x, y - 0.8, "건식 혼합", M_WALL_DN)
        x, y = P(9, 31); worker(L, x, y, 14.0, (150, 112, 74), "hoe", 1)
    elif k == 2:     # 물 붓기
        x, y = P(26, 20); pile(L, x, y, 7.2, 6.2, (206, 198, 184))
        iso.cyl(9, 10, 0, 9.0, 3.4, (170, 130, 84), (190, 150, 100))
        bx, by = P(9, 10); L.ell(bx, by - 9.0, 2.2, 1.3, fill=(112, 170, 210))
        L.line([(bx + 2, by - 8.0), (bx + 7, by - 3.5), (x - 3.5, y - 4.2)], (112, 170, 210), 0.9)
        x, y = P(36, 31); worker(L, x, y, 14.0, (96, 120, 150), "bucket", 1)
        x, y = P(5.5, 15); pill(L, x, y, "물통", M_WALL_DN)
    elif k in (3, 4):  # 뜨거운 혼합(2셀)
        iso.rect3(8, 5, 38, 31, 0.0, (236, 196, 150), ol=(150, 98, 60), lw=0.3)
        iso.rect3(12, 9, 34, 27, 0.0, (226, 120, 60), ol=(150, 70, 30), lw=0.3)
        x, y = P(23, 18)
        L.ell(x, y, 7.6, 4.2, fill=(236, 150, 70, 200))
        steam(L, x - 1.0, y - 3.0, 5 if k == 3 else 4, 2.8)
        if k == 3:
            worker(L, *P(7, 30), 14.0, (170, 80, 60), "hoe", 1)
            x, y = P(3.0, 22); pill(L, x, y, "혼합 구덩이", M_WALL_DN)
        else:
            worker(L, *P(40, 13), 14.0, (170, 80, 60), "hoe", -1)
            worker(L, *P(36, 32), 14.0, (120, 96, 70), None, 1)
            x, y = P(8.5, 5.5); pill(L, x, y - 0.4, "열 · 증기", M_WALL_DN)
    elif k == 5:     # 타설·다짐: 거푸집에 다져 넣기
        iso.box(9, 11, 0, 31, 31, 8.0, ((176, 150, 110), (170, 128, 84), (140, 104, 66)), ol=(96, 70, 44), lw=0.2)
        iso.rect3(11, 13, 29, 29, 8.0, (190, 186, 176), ol=(120, 116, 106), lw=0.2)
        for i in range(10):
            x, y = P(13 + rnd() * 14, 15 + rnd() * 12); L.ell(x, y - 8.0, 0.9, 0.55, fill=(120, 108, 96))
        x, y = P(38, 25); pile(L, x, y, 4.4, 4.2, (110, 98, 88), dots=(160, 150, 140))
        worker(L, *P(5, 22), 14.0, (170, 112, 72), "rammer", 1)
        x, y = P(10, 31); pill(L, x, y - 1.2, "거푸집", M_WALL_DN)
    elif k == 6:     # 굳기: 굳은 단면(앞 꼭짓점 쪽, 확대 창으로 수직 지시선) + 뒤쪽 완성 벽(사용 장면)
        iso.box(14, 4, 0, 38, 7, 14.0, ((226, 222, 212), (196, 190, 176), (156, 150, 138)), ol=(110, 106, 96), lw=0.2)
        iso.arch("L", 0, 7, 0, 20, 31, 0, 7.5, (110, 84, 56), None)
        iso.box(22, 22, 0, 34, 34, 10.0, ((226, 222, 212), (190, 186, 174), (150, 146, 136)), ol=(110, 106, 96), lw=0.2)
        for i in range(16):
            x, y = P(22.5 + rnd() * 11, 34.0); L.ell(x + (rnd() - 0.5) * 1.0, y - 1.2 - rnd() * 7.8, 0.7, 0.6, fill=(255, 255, 252), outline=(150, 146, 136), lw=0.1)
        worker(L, *P(10, 24), 14.0, (176, 96, 60), "point", 1)
        worker(L, *P(14, 30), 14.0, (92, 120, 150), None, 1)
        x, y = P(22.6, 34); pill(L, x, y - 1.2, "굳은 단면", M_WALL_DN)



# ───────────────────────── 배치 명세(main.py가 모아 z 순서로 그린다) ─────────────────────────
def objects():
    return [dict(z=60, name="Core 제작 과정", tier="Core", region=(8, 125, 170, 380), fn=draw_core, args=())]


def labels():
    return []


def extra_labels(LB):
    pass
