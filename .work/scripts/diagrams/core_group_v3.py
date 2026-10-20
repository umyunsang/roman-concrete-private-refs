# -*- coding: utf-8 -*-
# 코어 군 구상도 v3 — 사용자·지도교수 스케치(코어가 콤마 모양으로 콜로세움을 감싸며 바로 흘러듦) 반영
# 실행: uv run --no-project --with pillow python -I .work/scripts/diagrams/core_group_v3.py <출력 PNG>
import os, sys, math
sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/wf/v16")
sys.dont_write_bytecode = True
from common import *

OUT = sys.argv[1]
P = Layer(0, 0, PW, PH, "구상도v3", bg=BG + (255,))
SEA_C, SEA_E, RIV_C = (150, 186, 212), (96, 140, 176), (112, 170, 210)
CORE_F = (246, 214, 204)


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
    P.poly([p1, (p1[0] - head * math.cos(a - 0.45), p1[1] - head * math.sin(a - 0.45)),
            (p1[0] - head * math.cos(a + 0.45), p1[1] - head * math.sin(a + 0.45))], fill=col)


def smooth(pts, n=12):
    """닫힌 캣멀롬 곡선"""
    out = []
    m = len(pts)
    for i in range(m):
        p0, p1, p2, p3 = pts[(i - 1) % m], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        for k in range(n):
            t = k / float(n)
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    return out


def flag(x, y, name, sub, col=C_SUP_T):
    P.line([(x, y), (x, y - 9)], col, 0.4, joint=False)
    P.dot(x, y, 0.7, col)
    w = max(tw(name, fnt("b", 2.9)), tw(sub, fnt("m", 2.3))) + 3
    P.rect(x - 0.5, y - 17.5, x + w, y - 9, fill=(255, 251, 240, 235), outline=col, lw=0.3)
    P.text(x + 1, y - 13.6, name, fnt("b", 2.9), col)
    P.text(x + 1, y - 10.2, sub, fnt("m", 2.3), C_INK)


# ── 지도 무대(한 장의 로마 지도) ──
P.rect(0, MAP_Y0, PW, MAP_Y1, fill=(236, 216, 172))
for t in range(-700, 900, 14):
    for sgn in (1, -1):
        P.line([(0, 100 + t), (PW, 100 + t - sgn * PW * T30)], (222, 200, 152, 90), 0.2, joint=False)

# 바다: 왼쪽 아래 모서리(해안선 ±30°, 왼쪽·아래 블리드)
cy0 = 404.0
xe = (MAP_Y1 - cy0) / T30
P.poly([(0, cy0), (xe, MAP_Y1), (0, MAP_Y1)], fill=SEA_C)
for k in range(8):
    y = cy0 + 14 + k * 11
    x1 = (y - cy0) / T30 - 6
    if x1 > 10:
        P.line([(4, y), (x1, y)], (190, 214, 232), 0.35, joint=False)
P.line([(0, cy0), (xe, MAP_Y1)], SEA_E, 0.9, joint=False)
P.text(8, 499, "바다 — 왼쪽 아래 모서리(블리드)", fnt("b", 3.0), (40, 80, 120))

# 포르투스: 해안선에 걸침(육각 내항 = 육지, 외항·등대 = 바다)
hx, hy = 150, 474
hexa = [iso_pt(hx, hy, 10 * math.cos(a), 10 * math.sin(a)) for a in [i * math.pi / 3 for i in range(6)]]
P.poly(hexa, fill=(250, 236, 214), outline=(176, 82, 58), lw=0.8)
P.poly([iso_pt(hx, hy, 6.5 * math.cos(a), 6.5 * math.sin(a)) for a in [i * math.pi / 3 for i in range(6)]], fill=SEA_C)
P.arc(hx - 26, hy + 20, 14, 8, 150, 330, (120, 110, 96), 1.2)
P.poly([(hx - 38, hy + 25), (hx - 36.5, hy + 13), (hx - 35, hy + 25)], fill=(236, 226, 206), outline=(120, 110, 96), lw=0.4)
P.ell(hx - 36.5, hy + 12.5, 1.2, 1.2, fill=(250, 200, 80))
flag(hx + 8, hy - 4, "포르투스", "육각 내항(육지)·외항·등대(바다)")

# ── 코어 군: 콤마 모양 코어가 콜로세움을 왼쪽에서 감싸며 바로 흘러듦(스케치) ──
comma = [(176, 150), (128, 156), (66, 178), (26, 220), (14, 270), (24, 322), (56, 360), (108, 386), (168, 398), (224, 396), (262, 384),
         (240, 352), (204, 330), (170, 306), (150, 272), (146, 232), (154, 196), (178, 172)]
P.poly(smooth(comma, 10), fill=(250, 226, 218), outline=None)
pts = smooth(comma, 10)
for i in range(0, len(pts), 2):
    a, b = pts[i], pts[(i + 1) % len(pts)]
    P.line([a, b], C_CORE, 0.7, joint=False)
P.text(122, 146, "CORE", fnt("en", 8.0), C_CORE_T)
P.text(150, 146, "로마 콘크리트 제작 과정 — 콜로세움으로 바로 흘러듦", fnt("b", 3.0), C_CORE_T)

# 콜로세움(완공) — 코어의 완성품, 가장 큰 단일 오브젝트(지도 중앙)
ax, ay = 292, 314
octa = [iso_pt(ax, ay, 78 * math.cos(a + math.pi / 8), 78 * math.sin(a + math.pi / 8)) for a in [i * math.pi / 4 for i in range(8)]]
P.poly([(x, y + 7) for x, y in octa], fill=(150, 116, 78))
P.poly(octa, fill=(214, 196, 160), outline=(110, 86, 56), lw=0.8)
P.ell(ax, ay - 2, 52, 31, fill=(232, 220, 196), outline=(140, 116, 84), lw=0.6)
P.ell(ax, ay - 2, 31, 18, fill=(196, 160, 112), outline=(140, 116, 84), lw=0.5)
P.rect(ax - 60, ay - 58, ax - 40, ay - 10, fill=(226, 210, 176), outline=(110, 86, 56), lw=0.5)
P.text_c(ax + 10, ay + 46, "콜로세움(완공)", fnt("b", 5.0), C_ARENA_T)
P.text_c(ax + 10, ay + 52.5, "코어 공정의 완성품 · 가장 큰 단일 오브젝트", fnt("m", 2.8), C_INK)

# 공정 셀: 등각 계단으로 콤마를 따라 1(위 가운데) → 3(왼쪽 끝) → 6(콜로세움 왼쪽 아래 받침에 맞닿음)
W_ = 96.0
cells = [(176, 184), (128, 212), (80, 240), (128, 268), (176, 296), (224, 324)]
names = ["재료 준비", "마른 혼합", "물 붓기", "뜨거운 혼합", "다져 넣기", "굳기·석회 알갱이"]
subs = ["강·길로 들어온 재료", "생석회 + 화산재", "민물(육상 건물)", "발열 → 석회 알갱이", "기초·볼트 거푸집", "콜로세움 콘크리트"]
for k, (cx, cy) in enumerate(cells):
    d = diamond(cx, cy, W_)
    P.poly([(x, y + 4) for x, y in d], fill=shade(CORE_F, 0.86))
    P.poly(d, fill=CORE_F, outline=C_CORE, lw=0.7)
    P.ell(cx - 29, cy - 1.5, 4.0, 4.0, fill=C_CORE)
    P.text_c(cx - 29, cy + 0.2, str(k + 1), fnt("b", 4.0), (255, 255, 255))
    P.text(cx - 22, cy - 1, names[k], fnt("b", 3.5), C_CORE_T)
    P.text(cx - 22, cy + 4.5, subs[k], fnt("m", 2.5), C_INK)
# 흐름 화살표(콤마 바깥 둘레, 셀 글자 가리지 않게)
flow = [(150, 158), (100, 166), (46, 194), (20, 238)]
P.line(flow, C_CORE, 2.2, joint=True)
flow2 = [(20, 238), (20, 272), (48, 338), (110, 384), (196, 400), (248, 386)]
P.line(flow2, C_CORE, 2.2, joint=True)
arrow((238, 390), (252, 383), C_CORE, 2.2, 6.0)
P.text(64, 350, "공정 흐름 1 → 6", fnt("b", 3.2), C_CORE_T)
P.text(64, 356.5, "→ 콜로세움 완공", fnt("b", 3.2), C_CORE_T)

# 확대 창(Detail): 왼쪽 아래 — 코어 아래쪽(4단계 뜨거운 혼합: 석회 알갱이가 생기는 원리)에서 수직 지시선 → 하단 B1 패널
zx, zy, zr = 70, 440, 30
P.line([(zx, 286), (zx, zy - zr)], C_DETAIL, 0.6, joint=False)
P.dot(zx, 286, 0.9, C_DETAIL)
P.ell(zx, zy, zr, zr, fill=(250, 236, 214), outline=C_DETAIL, lw=1.0)
for (dx, dy, r) in [(-9, -8, 3.2), (8, -10, 2.4), (-4, 9, 2.8), (11, 6, 2.0), (2, -1, 1.6)]:
    P.ell(zx + dx, zy + dy, r, r, fill=(255, 255, 255), outline=(180, 170, 150), lw=0.2)
P.line([(zx - 14, zy - 20), (zx - 2, zy + 4), (zx + 12, zy + 22)], (120, 100, 80), 0.4)
P.line([(zx, zy + zr), (zx, 505)], C_DETAIL, 0.6, joint=False)
P.text(zx + zr + 3, zy - 6, "확대 창(Detail)", fnt("b", 3.0), C_DETAIL_T)
P.text(zx + zr + 3, zy - 0.5, "석회 알갱이·자가치유", fnt("m", 2.6), C_INK)

# ── 테베레강: 오른쪽 대각(스케치의 사선) + 강변 디테일 ──
riv = [(262, 148), (262 + C30 * 128, 148 + 0.5 * 128), (440, 212 + 0.5 * 0)]
riv = [(258, 140), (258 + C30 * 140, 140 + 0.5 * 140), (258 + C30 * 140 - C30 * 30, 210 + 15), (440, 225 + 0.5 * (440 - (258 + C30 * 140 - C30 * 30)) / C30)]
P.line(riv, RIV_C, 9.0, joint=True)
P.line(riv, (80, 140, 190), 0.5, joint=True)
P.text(268, 136, "테베레강(오른쪽 대각)", fnt("b", 3.2), (40, 90, 140))
for (x, y, s) in [(330, 176, "바지선·하역장"), (372, 200, "석회 가마"), (336, 244, "재료 운반 길")]:
    P.rect(x - 1, y - 4.2, x + tw(s, fnt("m", 2.6)) + 3, y + 1.4, fill=(255, 250, 238, 230), outline=(110, 150, 190), lw=0.3)
    P.text(x + 1, y, s, fnt("m", 2.6), (40, 70, 110))

# ── 주변 정보(Support)를 남은 자리에 한 장의 지도로 정리 ──
# 뒤쪽(위): 카라칼라 욕장·판테온, 가장 먼 베수비오
P.poly([(206, 120), (230, 106), (254, 120), (230, 134)], fill=(214, 168, 132), outline=(140, 96, 70), lw=0.4)
P.poly([(206, 120), (230, 134), (230, 141), (206, 127)], fill=(176, 126, 96))
P.poly([(230, 134), (254, 120), (254, 127), (230, 141)], fill=(150, 104, 78))
P.pie(230, 117, 9, 9, 180, 360, fill=(232, 214, 186), outline=(140, 96, 70), lw=0.4)
flag(208, 124, "카라칼라 욕장", "뒤쪽 · 절개")
P.rect(300, 112, 318, 123, fill=(220, 206, 176), outline=(130, 110, 80), lw=0.4)
P.pie(309, 112, 9, 7, 180, 360, fill=(206, 192, 162), outline=(130, 110, 80), lw=0.4)
flag(318, 125, "판테온", "시내")
P.poly([(352, 128), (370, 100), (388, 128)], fill=(196, 206, 196), outline=(150, 164, 156), lw=0.4)
P.text(352, 135, "베수비오(가장 먼 곳)", fnt("m", 2.4), (90, 110, 104))
# 오른쪽 아래: 아피아 가도·메텔라 무덤·수도교(남동 교외)
via = [(330, 392), (330 + C30 * 104, 392 + 0.5 * 104)]
P.line(via, (176, 152, 116), 4.4, joint=False)
P.dashed(via[0], via[1], (246, 236, 212), 0.5, 2.0, 1.6)
P.text(336, 410, "아피아 가도", fnt("b", 2.7), (126, 106, 76))
P.ell(388, 430, 7.5, 4.2, fill=(222, 210, 186), outline=(130, 110, 80), lw=0.4)
P.rect(380.5, 422, 395.5, 430, fill=(222, 210, 186))
P.ell(388, 422, 7.5, 4.2, fill=(236, 226, 206), outline=(130, 110, 80), lw=0.4)
flag(394, 434, "메텔라 무덤", "아피아 가도")
aq0, aq1 = (238, 428), (238 + C30 * 60, 428 + 0.5 * 60)
for k in range(8):
    t = k / 7.0
    x = aq0[0] + (aq1[0] - aq0[0]) * t
    y = aq0[1] + (aq1[1] - aq0[1]) * t
    P.rect(x - 2.6, y - 9, x + 2.6, y, fill=(214, 186, 150), outline=(140, 110, 80), lw=0.25)
    P.pie(x, y - 1.2, 1.6, 2.4, 180, 360, fill=(236, 216, 172))
P.line([(aq0[0], aq0[1] - 9), (aq1[0], aq1[1] - 9)], (140, 110, 80), 0.8, joint=False)
flag(296, 470, "수도교", "민물 공급")

# ── 화면 평행 패널: 상단 Basic 2개 + 타이틀, 하단 3분할 ──
P.poly([(140, 92), (140, 40), (211, 12), (282, 40), (282, 92)], fill=(250, 240, 222), outline=C_CORE, lw=0.6)
P.text_c(211, 60, "ROMAN CONCRETE", fnt("en", 7.0), C_CORE_T)
P.text_c(211, 70, "타이틀(페디먼트)", fnt("b", 3.6), C_INK)
tbox(18, 20, 118, 92, "L 로마 콘크리트란?", "Basic · 정의 + 재료·순서 요약", C_BASIC)
tbox(302, 20, 402, 92, "R 위치도", "Basic · 실제 지리", C_BASIC)
tbox(18, 505, 170, 565, "B1 석회 알갱이·자가치유", "Detail", C_DETAIL_T)
tbox(178, 505, 294, 565, "B2 연대기·근거", "Basic", C_BASIC)
tbox(302, 505, 402, 565, "B3 100년 vs 2000년", "Basic", C_BASIC)
P.dashed_rect(18, 568, 402, 581, C_GREY, 0.3, 2.6, 1.5)
P.text(22, 576.5, "구상도 v3: 스케치(코어가 콤마 모양으로 콜로세움을 감싸며 바로 흘러듦) 반영 — 실제 셀은 신문식 등각 계단, 좌표·크기는 배치 골격이 실측 위계로 확정", fnt("m", 2.3), C_GREY)

out = P.img.resize((PW * 3, PH * 3), Image.LANCZOS).convert("RGB")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
out.save(OUT)
print("저장:", OUT)
