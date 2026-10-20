# -*- coding: utf-8 -*-
# 코어 군 L자 배치 구상도(지도교수 비평 2건 반영안) — A2 420×594mm, 1mm = 3px로 저장
# 실행: uv run --no-project --with pillow python -I .work/scripts/diagrams/core_group_L.py <출력 PNG>
import os, sys, math
sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/wf/v16")
sys.dont_write_bytecode = True
from common import *

OUT = sys.argv[1]
P = Layer(0, 0, PW, PH, "구상도", bg=BG + (255,))
SEA_C, SEA_E = (150, 186, 212), (96, 140, 176)
RIV_C = (112, 170, 210)
CORE_F, CORE_E = (246, 214, 204), C_CORE
SUP_F = (214, 232, 208)
GREY_F = (238, 228, 204)


def tbox(x0, y0, x1, y1, title, sub, col, fill=(250, 244, 230), em=4.0):
    P.rect(x0, y0, x1, y1, fill=fill, outline=col, lw=0.6)
    P.text(x0 + 3, y0 + 7.5, title, fnt("b", em), col)
    if sub:
        P.text(x0 + 3, y0 + 13.5, sub, fnt("m", 2.8), C_INK)


def iso_pt(cx, cy, X, Y):
    return (cx + C30 * (X - Y), cy + 0.5 * (X + Y))


def diamond(cx, cy, w):
    h = w / SQ3
    return [(cx - w / 2, cy), (cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2)]


def arrow(p0, p1, col, lw=1.2, head=3.2):
    P.line([p0, p1], col, lw, joint=False)
    a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    q1 = (p1[0] - head * math.cos(a - 0.45), p1[1] - head * math.sin(a - 0.45))
    q2 = (p1[0] - head * math.cos(a + 0.45), p1[1] - head * math.sin(a + 0.45))
    P.poly([p1, q1, q2], fill=col)


# ── 지도 무대 바탕 ──
P.rect(0, MAP_Y0, PW, MAP_Y1, fill=(236, 216, 172))
for t in range(-700, 900, 14):
    for sgn in (1, -1):
        P.line([(0, 100 + t), (PW, 100 + t - sgn * PW * T30)], (222, 200, 152, 90), 0.2, joint=False)

# ── 바다: 왼쪽 아래 모서리 전부(해안선 ±30°, 왼쪽·아래 블리드) ──
coast = [(0, 372), (230, 372 + 230 * T30)]
sea = [(0, 372), coast[1], (230, MAP_Y1), (0, MAP_Y1)]
sea = [(0, 372), (230, 372 + 230 * T30), (230, MAP_Y1), (0, MAP_Y1)]
P.poly([(0, 372), (233, 372 + 233 * T30), (0, 372 + 233 * T30)], fill=SEA_C)
P.rect(0, 372 + 233 * T30 - 0.2, 233, MAP_Y1, fill=SEA_C)
for k in range(10):
    y = 392 + k * 11
    x0 = max(2, (y - 372) / T30 * 0 + 4)
    xe = (y - 372) / T30 - 6
    if xe > 10:
        P.line([(4, y), (xe, y)], (190, 214, 232), 0.35, joint=False)
P.line([(0, 372), (233, 372 + 233 * T30)], SEA_E, 0.9, joint=False)
P.text(14, 470, "바다(티레니아해) — 왼쪽 아래 모서리 전부", fnt("b", 3.6), (40, 80, 120))
P.text(14, 476.5, "해안선 ±30° 대각 · 왼쪽 변·지도 아래 변 밖으로 이어짐", fnt("m", 2.7), (40, 80, 120))

# ── 포르투스: 육각 내항(육지) + 클라우디우스 외항(바다) + 등대 ──
hx, hy = 132, 426
hexa = [iso_pt(hx, hy, 12 * math.cos(a), 12 * math.sin(a)) for a in [i * math.pi / 3 for i in range(6)]]
P.poly(hexa, fill=(250, 236, 214), outline=(176, 82, 58), lw=0.9)
inner = [iso_pt(hx, hy, 8 * math.cos(a), 8 * math.sin(a)) for a in [i * math.pi / 3 for i in range(6)]]
P.poly(inner, fill=SEA_C)
P.line([(hx - 9, hy + 9), (hx - 22, hy + 22)], SEA_C, 2.2, joint=False)
P.arc(hx - 34, hy + 34, 18, 11, 120, 300, (120, 110, 96), 1.4)
P.poly([(hx - 50, hy + 40), (hx - 48, hy + 26), (hx - 46, hy + 40)], fill=(236, 226, 206), outline=(120, 110, 96), lw=0.4)
P.ell(hx - 48, hy + 25.5, 1.3, 1.3, fill=(250, 200, 80))
P.text(hx + 14, hy - 4, "포르투스(Support·작게)", fnt("b", 3.2), C_SUP_T)
P.text(hx + 14, hy + 1.5, "육각 내항 = 육지 · 클라우디우스 외항 = 바다", fnt("m", 2.5), C_INK)
P.text(hx + 14, hy + 6.5, "외항 입구 섬에 층 쌓은 등대", fnt("m", 2.5), C_INK)

# ── 강: 오른쪽 위 액자 밖 → 오른쪽을 따라 내려옴 → ①아래에서 왼쪽 바다 / ②오른쪽 아래 밖 ──
riv = [(440, 104), (372, 143), (412, 166), (352, 201), (398, 228), (356, 252), (408, 282), (364, 307), (406, 331), (366, 354), (410, 380)]
P.line(riv, RIV_C, 9.0, joint=True)
P.line(riv, (80, 140, 190), 0.5, joint=True)
opt1 = [(410, 380), (292, 448), (248, 473)]
P.line(opt1, RIV_C, 9.0, joint=True)
P.line(opt1, (80, 140, 190), 0.5, joint=True)
for t in range(0, 60, 5):
    a = (410 + t * C30 * 0.6, 380 + t * 0.5 * 0.6)
    b = (410 + (t + 3) * C30 * 0.6, 380 + (t + 3) * 0.5 * 0.6)
    P.line([a, b], RIV_C, 6.0, joint=False)
P.text(372, 118, "테베레강", fnt("b", 3.6), (40, 90, 140))
P.text(372, 124, "오른쪽으로 이동", fnt("m", 2.8), (40, 90, 140))
P.text(250, 492, "① 아래로 꺾여 바다·포르투스로", fnt("b", 2.9), (40, 90, 140))
P.text(372, 412, "② 또는 오른쪽 아래 밖으로", fnt("b", 2.9), (40, 90, 140))

# 강변 디테일(강과 함께 오른쪽)
for (x, y, s) in [(380, 182, "바지선·하역장"), (384, 241, "석회 가마"), (378, 296, "석재·화산재 운반"), (382, 345, "수레·길")]:
    P.rect(x - 1, y - 4.2, x + tw(s, fnt("m", 2.7)) + 3, y + 1.4, fill=(255, 250, 238, 230), outline=(110, 150, 190), lw=0.3)
    P.text(x + 1, y, s, fnt("m", 2.7), (40, 70, 110))

# ── 위쪽 줄 Support와 가장 먼 베수비오 ──
for (x0, y0, x1, y1, t, s) in [(150, 102, 212, 140, "욕장(Support)", "카라칼라·절개·뒤쪽"), (222, 102, 284, 140, "판테온(Support)", "돔·오큘러스")]:
    tbox(x0, y0, x1, y1, t, s, C_SUP_T, fill=SUP_F, em=3.2)
P.poly([(300, 136), (318, 104), (336, 136)], fill=(196, 206, 196), outline=(120, 140, 130), lw=0.5)
P.text(296, 143, "베수비오(Support-2, 가장 먼 곳)", fnt("m", 2.6), (70, 92, 86))

# ── 코어 군: L자 공정 셀 체인 → 콜로세움(완공) ──
W_ = 100.0
H_ = W_ / SQ3
cells = [(70, 178), (120, 207), (70, 236), (120, 265), (170, 294), (220, 323)]
names = ["재료 준비", "마른 혼합", "물 붓기", "뜨거운 혼합", "다져 넣기", "굳기·석회 알갱이"]
subs = ["생석회·화산재·골재", "생석회 + 화산재", "민물(육상 건물)", "발열 반응", "거푸집에 다짐", "콜로세움 콘크리트"]
for k, (cx, cy) in enumerate(cells):
    d = diamond(cx, cy, W_)
    P.poly([(x, y + 4) for x, y in d], fill=shade(CORE_F, 0.86))
    P.poly(d, fill=CORE_F, outline=CORE_E, lw=0.7)
    P.ell(cx - 30, cy - 1.5, 4.2, 4.2, fill=C_CORE)
    P.text_c(cx - 30, cy + 0.2, str(k + 1), fnt("b", 4.2), (255, 255, 255))
    P.text(cx - 23, cy - 1, names[k], fnt("b", 3.6), C_CORE_T)
    P.text(cx - 23, cy + 4.5, subs[k], fnt("m", 2.6), C_INK)
# 셀 바깥 큰 L자 흐름 화살표(세로 획 → 꺾임 → 가로 획 → 콜로세움)
# 세로 획(x=11, 1~3단계 왼쪽) → 꺾임 → 셀 4~6 아래를 따라 지면 ↘ 방향 → 콜로세움 왼쪽 아래 면으로
corner = (11, 250)
mid = (corner[0] + C30 * 210, corner[1] + 0.5 * 210)
end = (mid[0] + 40, mid[1])
P.line([(11, 172), corner], C_CORE, 2.4, joint=False)
P.line([corner, mid, end], C_CORE, 2.4, joint=True)
arrow((end[0] - 8, end[1]), (end[0] + 4, end[1]), C_CORE, 2.4, 6.0)
P.text(16, 168, "세로 획: 1~4단계", fnt("b", 3.0), C_CORE_T)
P.text(16, 288, "공정 흐름 →", fnt("b", 3.2), C_CORE_T)
P.text(16, 294.5, "콜로세움 완공", fnt("b", 3.2), C_CORE_T)
P.text(96, 344, "가로 획: 5~6단계(지면 ↘ 방향)", fnt("b", 3.0), C_CORE_T)

# 콜로세움(완공) — 공정의 완성품, 가장 큰 단일 오브젝트
ax, ay = 300, 318
octa = [iso_pt(ax, ay, 62 * math.cos(a + math.pi / 8), 62 * math.sin(a + math.pi / 8)) for a in [i * math.pi / 4 for i in range(8)]]
P.poly([(x, y + 6) for x, y in octa], fill=(150, 116, 78))
P.poly(octa, fill=(214, 196, 160), outline=(110, 86, 56), lw=0.8)
P.ell(ax, ay - 2, 40, 24, fill=(232, 220, 196), outline=(140, 116, 84), lw=0.6)
P.ell(ax, ay - 2, 24, 14, fill=(196, 160, 112), outline=(140, 116, 84), lw=0.5)
P.rect(ax - 46, ay - 44, ax - 30, ay - 8, fill=(226, 210, 176), outline=(110, 86, 56), lw=0.5)
P.text_c(ax, ay + 34, "콜로세움(완공)", fnt("b", 4.6), C_ARENA_T)
P.text_c(ax, ay + 40, "공정의 완성품 · 가장 큰 단일 오브젝트", fnt("m", 2.8), C_INK)

# 확대 창(Detail) ← 6단계, → 하단 석회 알갱이 패널
P.ell(196, 392, 15, 15, fill=(250, 236, 214), outline=C_DETAIL, lw=0.9)
for (dx, dy) in [(-5, -4), (4, -6), (-2, 5), (6, 3)]:
    P.ell(196 + dx, 392 + dy, 1.6, 1.6, fill=(255, 255, 255), outline=(180, 170, 150), lw=0.2)
P.line([(220, 338), (204, 379)], C_DETAIL, 0.5, joint=False)
P.line([(196, 407), (96, 505)], C_DETAIL, 0.5, joint=False)
P.text(213, 392, "확대 창(Detail)", fnt("b", 3.0), C_DETAIL_T)
P.text(213, 397.5, "6단계 → 석회 알갱이", fnt("m", 2.6), C_INK)

# 코어 군 경계(점선)와 면적 목표
grp = [(6, 150), (292, 150), (292, 100), (419, 100), (419, 420), (232, 420), (6, 418)]
for i in range(len(grp)):
    P.dashed(grp[i], grp[(i + 1) % len(grp)], C_CORE, 0.7, 3.4, 2.2)
P.rect(196, 176, 336, 206, fill=(255, 246, 240, 240), outline=C_CORE, lw=0.5)
P.text(200, 184, "코어 군(Core group)", fnt("b", 3.8), C_CORE_T)
P.text(200, 191, "L자 공정 6단계 + 콜로세움(완공)", fnt("m", 2.8), C_INK)
P.text(200, 196.5, "+ 오른쪽 테베레강 + 강변 디테일", fnt("m", 2.8), C_INK)
P.text(200, 202, "지도 무대의 45~60% · 볼거리·정보 최다", fnt("m", 2.8), C_INK)

# 아래 둘레 Support
tbox(334, 452, 410, 478, "수도교·메텔라(Support)", "아래 둘레·작게", C_SUP_T, fill=SUP_F, em=3.0)

# ── 화면 평행 패널(그대로) ──
P.poly([(140, 92), (140, 40), (211, 12), (282, 40), (282, 92)], fill=(250, 240, 222), outline=C_CORE, lw=0.6)
P.text_c(211, 60, "ROMAN CONCRETE", fnt("en", 7.0), C_CORE_T)
P.text_c(211, 70, "타이틀(페디먼트)", fnt("b", 3.6), C_INK)
tbox(18, 20, 118, 68, "L1 로마 콘크리트란?", "Basic", C_BASIC)
tbox(18, 76, 118, 132, "L2 레시피·순서", "Basic", C_BASIC)
tbox(302, 20, 402, 92, "R1 위치도", "Basic", C_BASIC)
tbox(18, 505, 170, 565, "B1 석회 알갱이·자가치유", "Detail", C_DETAIL_T)
tbox(178, 505, 294, 565, "B2 연대기·근거", "Basic", C_BASIC)
tbox(302, 505, 402, 565, "B3 100년 vs 2000년", "Basic", C_BASIC)
P.dashed_rect(18, 568, 402, 581, C_GREY, 0.3, 2.6, 1.5)
P.text(22, 576.5, "구상도: 지도교수 비평(코어 군·L자) 반영안 — 실제 도면은 배치 골격 담당이 지면 축 ±30°·실측 위계로 다시 잡는다", fnt("m", 2.4), C_GREY)

out = P.img.resize((PW * 3, PH * 3), Image.LANCZOS).convert("RGB")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
out.save(OUT)
print("저장:", OUT)
