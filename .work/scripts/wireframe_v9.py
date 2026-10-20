# 로마 콘크리트 A2 와이어프레임 v2 (1mm = 4px)
# - 군집 없이 중앙 지도를 넓게, 오브젝트 크기는 베이징 실측 등급(히어로 ≈204×199, 표준 ≈86×80, 탈것 33~41mm)
# - 구획: 신문식 전폭 타이틀 띠 + 넓은 지도(오브젝트 개별 배치) + 하단 띠. 화산은 베수비오 하나.
from PIL import Image, ImageDraw, ImageFont
import math
FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
f = lambda s: ImageFont.truetype(FONT, s)
K = 4; W, H = 420 * K, 594 * K
C = {"Core": (215, 38, 61), "Basic": (27, 152, 224), "Detail": (232, 128, 20), "Support": (46, 147, 60), "구조": (90, 90, 90)}
SOIL, GRASS = (126, 98, 62), (94, 126, 66)
im = Image.new("RGB", (W, H), (231, 208, 160)); d = ImageDraw.Draw(im, "RGBA")
mm = lambda v: int(round(v * K))
T30 = math.tan(math.radians(30))
for t in range(-700, 900, 20):
    for sgn in (1, -1):
        d.line([0, mm(100 + t), mm(420), mm(100 + t - sgn * 420 * T30)], fill=(206, 182, 136, 90), width=1)
def lab(x, y, s, size=26, col=(25, 25, 25)):
    d.text((mm(x), mm(y)), s, font=f(size), fill=col, stroke_width=4, stroke_fill=(255, 255, 255))
def tagbox(x0, y0, x1, y1, tag, title, lines=()):
    col = C[tag]
    d.rectangle([mm(x0), mm(y0), mm(x1), mm(y1)], fill=(255, 252, 244, 170), outline=col + (255,), width=6)
    d.rectangle([mm(x0), mm(y0), mm(x0) + 150, mm(y0) + 34], fill=col + (255,)); d.text((mm(x0) + 8, mm(y0) + 3), tag, font=f(26), fill=(255, 255, 255))
    d.text((mm(x0) + 8, mm(y0) + 42), title, font=f(30), fill=(30, 30, 30))
    for i, l in enumerate(lines): d.text((mm(x0) + 10, mm(y0) + 84 + i * 30), l, font=f(22), fill=(60, 60, 60))
def base_rhombus(cx, cy, w, t=5, top=(240, 226, 192)):
    """화면 폭 w인 정사각 받침(등각 마름모) + 흙 측면"""
    h = w / math.sqrt(3)
    L, T, R, B = (cx - w / 2, cy), (cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2)
    d.polygon([(mm(L[0]), mm(L[1])), (mm(B[0]), mm(B[1])), (mm(B[0]), mm(B[1] + t)), (mm(L[0]), mm(L[1] + t))], fill=SOIL)
    d.polygon([(mm(B[0]), mm(B[1])), (mm(R[0]), mm(R[1])), (mm(R[0]), mm(R[1] + t)), (mm(B[0]), mm(B[1] + t))], fill=(104, 80, 50))
    d.line([(mm(L[0]), mm(L[1]) + 2), (mm(B[0]), mm(B[1]) + 2), (mm(R[0]), mm(R[1]) + 2)], fill=GRASS, width=mm(1.4))
    d.polygon([(mm(p[0]), mm(p[1])) for p in (L, T, R, B)], fill=top, outline=(110, 90, 60))
def size_note(x, y, s): lab(x, y, s, 20, (120, 70, 20))
def grand_bath(cx, cy, w, hz, cut=0.26):
    """참조 욕장(장대한 황제 욕장 실내)을 절개로: 열주·조각상·코퍼 반쪽 돔·오큘러스 빛줄기·증기 욕조·목욕하는 인물·하이포코스트"""
    h = w / math.sqrt(3)
    Lp, Tp, Rp, Bp = (cx - w / 2, cy), (cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2)
    up = lambda p, z: (p[0], p[1] - z); P = lambda pts: [(mm(x), mm(y)) for x, y in pts]
    q = lambda a, b, t: (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    base_rhombus(cx, cy, w + 8, t=6)
    d.polygon(P([Lp, Tp, up(Tp, hz), up(Lp, hz)]), fill=(222, 198, 156), outline=(110, 85, 55))
    d.polygon(P([Tp, Rp, up(Rp, hz), up(Tp, hz)]), fill=(204, 176, 134), outline=(110, 85, 55))
    for t in [.15, .35, .55, .75, .9]:                       # 뒤 벽 열주(기둥+주두)
        for a, b in [(Lp, Tp), (Tp, Rp)]:
            x, y = q(a, b, t); d.rectangle([mm(x - 1.4), mm(y - hz * .82), mm(x + 1.4), mm(y)], fill=(238, 224, 196), outline=(140, 110, 75))
            d.rectangle([mm(x - 2.6), mm(y - hz * .86), mm(x + 2.6), mm(y - hz * .8)], fill=(238, 224, 196), outline=(140, 110, 75))
    for t in [.25, .65]:                                     # 벽감 조각상
        x, y = q(Lp, Tp, t); d.ellipse([mm(x - 1.8), mm(y - hz * .55), mm(x + 1.8), mm(y - hz * .48)], fill=(245, 240, 230)); d.rectangle([mm(x - 1.4), mm(y - hz * .48), mm(x + 1.4), mm(y - hz * .3)], fill=(245, 240, 230))
    d.polygon(P([Lp, Tp, Rp, Bp]), fill=(236, 226, 204), outline=(110, 85, 55))
    pool = [q(Lp, Tp, .25), q(Tp, Rp, .2), q(Rp, Bp, .35), q(Lp, Bp, .4)]
    d.polygon(P(pool), fill=(70, 178, 196), outline=(40, 120, 140))      # 청록 욕조
    dx, dy = q(Tp, Rp, .45); dy -= hz                                    # 코퍼 반쪽 돔 + 콘크리트 두께
    R1, R2 = w * .26, w * .2
    d.pieslice([mm(dx - R1), mm(dy - R1 * .8), mm(dx + R1), mm(dy + R1 * .8)], 180, 360, fill=(196, 168, 126), outline=(110, 85, 55), width=3)
    d.pieslice([mm(dx - R2), mm(dy - R2 * .8), mm(dx + R2), mm(dy + R2 * .8)], 180, 360, fill=(230, 214, 182))
    for k in range(1, 4): d.arc([mm(dx - R2 * k / 4), mm(dy - R2 * .8 * k / 4), mm(dx + R2 * k / 4), mm(dy + R2 * .8 * k / 4)], 180, 360, fill=(170, 140, 100), width=2)
    for a in range(200, 360, 20):
        d.line([mm(dx), mm(dy), mm(dx + R2 * math.cos(math.radians(a))), mm(dy + R2 * .8 * math.sin(math.radians(a)))], fill=(170, 140, 100), width=2)
    d.ellipse([mm(dx - 3), mm(dy - R2 * .8 - 1.5), mm(dx + 3), mm(dy - R2 * .8 + 1.5)], fill=(255, 250, 220))          # 오큘러스
    cxp = (pool[0][0] + pool[2][0]) / 2; cyp = (pool[0][1] + pool[2][1]) / 2
    d.polygon(P([(dx - 2, dy - R2 * .8), (dx + 2, dy - R2 * .8), (cxp + 12, cyp), (cxp - 6, cyp)]), fill=(255, 245, 200, 110))  # 빛줄기
    for i in range(7):                                       # 증기
        x = cxp - 18 + i * 6; y = cyp - 4 - (i % 3) * 3; d.ellipse([mm(x - 5), mm(y - 3), mm(x + 5), mm(y + 3)], fill=(255, 255, 255, 120))
    for i in range(9):                                       # 목욕하는 인물(작은 점)
        x = cxp - 16 + (i % 5) * 7; y = cyp - 2 + (i // 5) * 6; d.ellipse([mm(x - 1), mm(y - 1), mm(x + 1), mm(y + 1)], fill=(150, 90, 60))
    d.polygon(P([Lp, Bp, up(Bp, hz * cut), up(Lp, hz * cut)]), fill=(212, 182, 138), outline=(110, 85, 55))
    d.polygon(P([Bp, Rp, up(Rp, hz * cut), up(Bp, hz * cut)]), fill=(192, 160, 118), outline=(110, 85, 55))
    hb = q(Bp, Rp, .12)
    d.rectangle([mm(hb[0] - 10), mm(hb[1] + 2), mm(hb[0] + 10), mm(hb[1] + 10)], fill=(90, 62, 40))
    for i in range(5): d.rectangle([mm(hb[0] - 9 + i * 4), mm(hb[1] + 3), mm(hb[0] - 7.6 + i * 4), mm(hb[1] + 9)], fill=(200, 120, 80))

def cutaway_bath(cx, cy, w, hz, cut=0.3, dome=True, label=None, note=None, tagcol=None):
    """절개 욕장: 뒤 벽 전체 높이, 앞 벽은 cut 비율로 낮게, 지붕 제거, 반쪽 돔(콘크리트 두께), 욕조, 하이포코스트 절개"""
    h = w / math.sqrt(3)
    Lp, Tp, Rp, Bp = (cx - w / 2, cy), (cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2)
    up = lambda p, z: (p[0], p[1] - z)
    P = lambda pts: [(mm(x), mm(y)) for x, y in pts]
    base_rhombus(cx, cy, w + 8, t=6)
    d.polygon(P([Lp, Tp, up(Tp, hz), up(Lp, hz)]), fill=(214, 186, 144), outline=(110, 85, 55))      # 뒤 왼쪽 벽
    d.polygon(P([Tp, Rp, up(Rp, hz), up(Tp, hz)]), fill=(196, 166, 124), outline=(110, 85, 55))      # 뒤 오른쪽 벽
    d.polygon(P([Lp, Tp, Rp, Bp]), fill=(232, 220, 196), outline=(110, 85, 55))                         # 바닥
    q = lambda a, b, t: (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    pool = [q(Lp, Tp, .35), q(Tp, Rp, .25), q(q(Rp, Bp, .5), q(Lp, Tp, .35), .35), q(Lp, Bp, .45)]
    d.polygon(P(pool), fill=(98, 160, 210), outline=(60, 110, 160))                                     # 욕조
    d.line(P([q(Tp, Bp, .2), up(q(Tp, Bp, .2), hz * .55)]), fill=(150, 120, 85), width=4)               # 칸막이 벽
    d.polygon(P([Lp, Bp, up(Bp, hz * cut), up(Lp, hz * cut)]), fill=(206, 176, 132), outline=(110, 85, 55))  # 앞 왼쪽 벽(낮게 절개)
    d.polygon(P([Bp, Rp, up(Rp, hz * cut), up(Bp, hz * cut)]), fill=(186, 154, 112), outline=(110, 85, 55))  # 앞 오른쪽 벽(낮게 절개)
    if dome:                                                                                             # 반쪽 돔: 단면에 콘크리트 두께
        dx, dy = q(Tp, Rp, .5); dy -= hz
        d.pieslice([mm(dx - w * .18), mm(dy - w * .16), mm(dx + w * .18), mm(dy + w * .16)], 180, 360, fill=(204, 178, 138), outline=(110, 85, 55), width=3)
        d.pieslice([mm(dx - w * .13), mm(dy - w * .11), mm(dx + w * .13), mm(dy + w * .11)], 180, 360, fill=(150, 125, 90))
    hb = q(Bp, Rp, .15)                                                                                  # 하이포코스트 절개(바닥 아래 기둥)
    d.rectangle([mm(hb[0] - 9), mm(hb[1] + 2), mm(hb[0] + 9), mm(hb[1] + 9)], fill=(90, 62, 40))
    for i in range(4): d.rectangle([mm(hb[0] - 8 + i * 4.5), mm(hb[1] + 3), mm(hb[0] - 6.5 + i * 4.5), mm(hb[1] + 8)], fill=(200, 120, 80))
    if label: lab(cx - w / 2, cy - h / 2 - hz - 16, label, 24, tagcol or C["Support"])
    if note: size_note(cx - w / 2, cy - h / 2 - hz - 3, note)


# ---- 타이틀 띠(신문식 전폭 3분할) ----
d.rectangle([mm(10), mm(12), mm(410), mm(96)], fill=(250, 244, 230, 245), outline=(60, 60, 60, 255), width=4)
d.line([mm(10), mm(16), mm(410), mm(16)], fill=(60, 60, 60), width=3); d.line([mm(10), mm(92), mm(410), mm(92)], fill=(60, 60, 60), width=3)
d.line([mm(118), mm(22), mm(118), mm(86)], fill=(80, 80, 80), width=3); d.line([mm(302), mm(22), mm(302), mm(86)], fill=(80, 80, 80), width=3)
lab(16, 20, "Basic  로마 콘크리트란?", 26, C["Basic"]); lab(16, 34, "정의 2줄 + 속성 칩(원형) 5~7개", 20, (70, 70, 70))
lab(126, 24, "ROMAN CONCRETE", 58, C["Core"]); lab(126, 48, "부서질 때마다 스스로 고치는 2000년의 콘크리트", 30, (40, 40, 40))
lab(126, 64, "Core: 왜 2000년을 버텼나 → 스스로 고친다", 24, C["Core"])
lab(308, 20, "Basic  THE RECIPE · ORDER", 26, C["Basic"]); lab(308, 34, "재료 아이콘 4개 + 섞는 순서", 20, (70, 70, 70))
lab(308, 46, "(신문 ADVANTAGES 아이콘 열 문법)", 20, (70, 70, 70))


# ===== v9: 포르투스 고고학 평면도의 물-땅 뼈대 + 포르투스 재현도 형태. 물은 땅보다 낮게(먼 쪽 둑 흙 측면) =====
WATER, DEEP, BANK, STONE, ROOF = (112, 172, 214), (78, 132, 182), (126, 98, 62), (222, 210, 182), (196, 112, 72)
def water(poly, col=WATER, drop=3):
    d.polygon([(mm(x), mm(y)) for x, y in poly], fill=BANK)                        # 둑(땅 높이)
    d.polygon([(mm(x), mm(y + drop)) for x, y in poly], fill=col)                    # 물면(3mm 낮게)
def river(pts, wdt, drop=2.5):
    d.line([(mm(x), mm(y)) for x, y in pts], fill=BANK, width=mm(wdt), joint="curve")
    d.line([(mm(x), mm(y + drop)) for x, y in pts], fill=WATER, width=mm(wdt - 1), joint="curve")
def roof_box(x, y, w, dpt, h, col=ROOF):
    """작은 등각 창고(기와 지붕): 바닥 중심 (x,y), 화면 폭 w"""
    hh = w / math.sqrt(3) * dpt
    top = [(x - w / 2, y - h), (x, y - h - hh / 2), (x + w / 2, y - h), (x, y - h + hh / 2)]
    d.polygon([(mm(x - w / 2), mm(y - h)), (mm(x), mm(y - h + hh / 2)), (mm(x), mm(y + hh / 2)), (mm(x - w / 2), mm(y))], fill=(214, 186, 144))
    d.polygon([(mm(x), mm(y - h + hh / 2)), (mm(x + w / 2), mm(y - h)), (mm(x + w / 2), mm(y)), (mm(x), mm(y + hh / 2))], fill=(190, 160, 118))
    d.polygon([(mm(px), mm(py)) for px, py in top], fill=col, outline=(130, 70, 40))
# 바다(왼쪽, 액자 밖으로 이어짐)
water([(0, 150), (34, 150), (40, 200), (20, 236), (22, 330), (70, 392), (120, 452), (150, 498), (0, 498)], DEEP)
lab(6, 470, "티레니아해(화면 밖으로)", 20, (255, 255, 255))
# 클라우디우스 내항 + 곡선 방파제 두 팔 + 등대
water([(20, 236), (60, 214), (110, 212), (146, 236), (150, 268), (132, 306), (84, 326), (30, 318), (22, 300)], DEEP)
for arc in [[(20, 236), (60, 212), (110, 210), (146, 234)], [(30, 320), (84, 328), (132, 308), (148, 286)]]:
    d.line([(mm(x), mm(y)) for x, y in arc], fill=STONE, width=mm(4.5), joint="curve")
    d.line([(mm(x), mm(y + 2.4)) for x, y in arc], fill=(160, 140, 110), width=mm(1.2), joint="curve")
d.rectangle([mm(14), mm(250), mm(24), mm(276)], fill=(238, 226, 200), outline=(110, 85, 55), width=3)
d.ellipse([mm(13), mm(246), mm(25), mm(254)], fill=(250, 240, 214), outline=(110, 85, 55)); d.polygon([(mm(15), mm(246)), (mm(19), mm(238)), (mm(23), mm(246))], fill=(240, 196, 90))
lab(4, 226, "파로스 등대", 18, (40, 40, 40))
# 트라야누스 육각 내항 + 창고 열(붉은 기와) — 포르투스 재현도 형태
hx, hy, hr = 192, 262, 40
hexp = [(hx + hr * math.cos(math.radians(60 * k)), hy + hr * .577 * math.sin(math.radians(60 * k))) for k in range(6)]
water(hexp, WATER)
d.line([mm(150), mm(262), mm(146), mm(262)], fill=WATER, width=mm(6))                          # 다르세나 연결 수로
for k in range(6):
    a, b = hexp[k], hexp[(k + 1) % 6]
    for t in (.25, .55, .82):
        x = a[0] + (b[0] - a[0]) * t; y = a[1] + (b[1] - a[1]) * t
        ox, oy = (x - hx) * .22, (y - hy) * .3
        roof_box(x + ox, y + oy, 13, 1.0, 5)
lab(150, 300, "F 포르투스(육각 내항·창고 열·방파제·등대)", 22, C["Support"]); size_note(150, 313, "참조 재현도 형태 · 해양 콘크리트")
pref = Image.open("dl/portus-ref/portus_ref.jpg").convert("RGB").resize((mm(34), mm(24)))
im.paste(pref, (mm(108), mm(336))); d.rectangle([mm(108), mm(336), mm(142), mm(360)], outline=C["Support"] + (255,), width=4); lab(106, 361, "참조 포르투스", 16, C["Support"])
# 트라야누스 운하 → 테베레강 곡류(오른쪽에서 들어와 아래로 굽이쳐 오스티아로)
river([(232, 262), (270, 300)], 7)
river([(420, 286), (360, 292), (300, 296), (268, 304), (252, 350), (266, 398), (302, 430), (344, 450), (352, 474), (326, 498)], 10)
lab(362, 302, "테베레강 ← 로마에서", 20, (20, 60, 110))
# 섬(이솔라 사크라) = Detail 공정 섬
def cell(cx, cy, w):
    h = w / math.sqrt(3); pts = [(cx - w / 2, cy), (cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2)]
    d.polygon([(mm(x), mm(y)) for x, y in pts], fill=(250, 238, 210, 255)); d.line([(mm(x), mm(y)) for x, y in pts + [pts[0]]], fill=C["Detail"] + (255,), width=6)
centers = [(176, 386), (214, 408), (176, 430), (214, 452)]
for k, (x, y) in enumerate(centers):
    cell(x, y, 76)
    d.ellipse([mm(x) - 21, mm(y) - 21, mm(x) + 21, mm(y) + 21], fill=C["Detail"] + (255,)); d.text((mm(x) - 9, mm(y) - 18), str(k + 1), font=f(28), fill=(255, 255, 255))
for i, sname in enumerate(["재료 준비", "마른 혼합", "물·뜨거운 혼합", "타설·다짐"]):
    x, y = centers[i]; lab(x - 24, y + 7, sname, 17, (120, 60, 0))
lab(150, 364, "H 공정 섬 — Detail(뜨거운 혼합, 셀 4개)", 22, C["Detail"])
# 오스티아(맨 아래 강 하구) = 추가 Support 후보 자리
d.rectangle([mm(240), mm(458), mm(318), mm(496)], outline=(120, 120, 120, 255), width=4); lab(244, 462, "오스티아 — 추가 Support 후보", 18, (90, 90, 90))
# 내륙(로마 방향)에서 가도·수도교가 육각 내항으로
d.line([(mm(206), mm(100)), (mm(204), mm(236))], fill=(150, 150, 150, 235), width=mm(5))
for i in range(6):
    x0 = 210; y0 = 104 + i * 21
    d.rectangle([mm(x0), mm(y0), mm(x0 + 8), mm(y0 + 14)], fill=(206, 178, 134), outline=(110, 85, 55), width=3)
    d.pieslice([mm(x0 + 1.5), mm(y0 + 6), mm(x0 + 6.5), mm(y0 + 12)], 180, 360, fill=(120, 96, 64))
lab(220, 100, "E 수도교·가도 ← 내륙", 20, C["Support"])
# 2 베수비오 — Support-2(사례의 사례): 뷰 윈도우 뒤끝 지평선 띠, 원근 배율 0.6, 대기 원근(바탕색 50% 혼합), 앞 오브젝트에 밑동이 가려짐
BG = (231, 208, 160)
mix = lambda c, a=0.5: tuple(int(c[i] * (1 - a) + BG[i] * a) for i in range(3))
for xx in range(0, 420, 6):
    d.line([mm(xx), mm(146), mm(xx + 3), mm(146)], fill=(150, 130, 100), width=2)
lab(150, 135, "배경층(지평선 띠): 원근 배율 0.6 · 대기 원근 · 겹침 단서", 18, (120, 100, 70))
d.polygon([(mm(346), mm(146)), (mm(372), mm(116)), (mm(380), mm(118)), (mm(388), mm(114)), (mm(410), mm(146))], fill=mix((140, 100, 66)), outline=mix((80, 52, 30)))
for i in range(3): d.ellipse([mm(381 + i * 3), mm(104 - i * 6), mm(391 + i * 3), mm(112 - i * 6)], fill=mix((205, 205, 205), 0.35) + (150,))
d.line([mm(398), mm(110), mm(398), mm(124)], fill=(90, 70, 50), width=3); d.ellipse([mm(397), mm(123), mm(399.5), mm(125.5)], fill=(90, 70, 50))
lab(400, 104, "베수비오", 18, (90, 60, 30))
size_note(296, 104, "Support-2 · 약 64×32mm")
# 1 콜로세움 — 참조 디오라마 형태: 팔각 흙 받침 · 뒤 왼쪽만 남은 4층 외벽 · 무너진 앞쪽 고리 · 아레나 반쪽 나무 바닥 + 하이포게움 노출 · 광장·나무·폐허
cx, cy = 318, 206
S3 = math.sqrt(3)
def isoP(X, Y): return (cx + 0.866 * (X - Y), cy + 0.5 * (X + Y))
r = 196 / 2.264   # 화면 폭 196mm가 되는 팔각 외접 반지름
octo = [isoP(r * math.cos(math.radians(22.5 + 45 * k)), r * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
low = sorted(octo, key=lambda p: -p[1])
for i in range(8):                                                    # 팔각 받침 흙 측면(앞쪽 변만)
    a, b = octo[i], octo[(i + 1) % 8]
    if (a[1] + b[1]) / 2 > cy - 2:
        d.polygon([(mm(a[0]), mm(a[1])), (mm(b[0]), mm(b[1])), (mm(b[0]), mm(b[1] + 8)), (mm(a[0]), mm(a[1] + 8))], fill=SOIL)
        d.line([(mm(a[0]), mm(a[1] + 1)), (mm(b[0]), mm(b[1] + 1))], fill=GRASS, width=mm(1.5))
d.polygon([(mm(x), mm(y)) for x, y in octo], fill=(214, 204, 182), outline=(110, 90, 60))   # 돌 포장 광장
for i in range(40):                                                   # 포장석 결
    x = cx - 85 + (i * 37) % 170; y = cy - 30 + (i * 23) % 60; d.line([mm(x), mm(y), mm(x + 4), mm(y + 1)], fill=(180, 170, 150), width=2)
E = lambda ox, oy, a, b: [mm(ox - a), mm(oy - b), mm(ox + a), mm(oy + b)]
a_out, b_out, H1, H2 = 72, 40, 20, 44                                  # 바깥 타원 반축, 낮은 고리 높이, 남은 외벽 높이
d.chord(E(cx, cy, a_out, b_out), 0, 180, fill=(196, 160, 118), outline=(110, 85, 55))      # 앞쪽 외벽 아래 면
d.rectangle([mm(cx - a_out), mm(cy - H1), mm(cx + a_out), mm(cy)], fill=(196, 160, 118))
d.chord(E(cx, cy - H1, a_out, b_out), 0, 180, fill=(196, 160, 118))
for row in range(2):                                                  # 아치 행
    for k in range(-9, 10):
        t = k / 10.0; x = cx + a_out * 0.97 * t; y = cy - 4 - row * 9 + b_out * math.sqrt(max(0, 1 - t * t)) * 0.95
        d.pieslice([mm(x - 2), mm(y - 5), mm(x + 2), mm(y - 1)], 180, 360, fill=(110, 82, 52))
d.ellipse(E(cx, cy - H1, a_out, b_out), fill=(214, 188, 146), outline=(110, 85, 55), width=3)   # 관람석(카베아) 윗면
for k in range(1, 4):
    d.ellipse(E(cx, cy - H1 + k * 2, a_out - k * 9, b_out - k * 5), outline=(170, 140, 100), width=2)
d.ellipse(E(cx, cy - H1 + 9, 34, 17), fill=(120, 96, 66), outline=(90, 70, 45), width=3)       # 아레나
for k in range(-3, 4): d.line([mm(cx - 30 + k * 2), mm(cy - H1 + 9 - 12), mm(cx - 30 + k * 2 + 14), mm(cy - H1 + 9 + 12)], fill=(80, 60, 40), width=2)
d.chord(E(cx, cy - H1 + 9, 34, 17), 270, 90, fill=(176, 138, 92), outline=(90, 70, 45))   # 오른쪽 반쪽 나무 바닥
pts = []                                                               # 뒤 왼쪽만 남은 4층 외벽 조각
for ang in range(160, 262, 4):
    x = cx + a_out * math.cos(math.radians(ang)); y = cy - H1 + b_out * math.sin(math.radians(ang)); pts.append((x, y))
band = [(mm(x), mm(y)) for x, y in pts] + [(mm(x), mm(y - (H2 - H1))) for x, y in reversed(pts)]
d.polygon(band, fill=(204, 168, 124), outline=(110, 85, 55))
for (x, y) in pts[::2]:
    for row in range(3): d.rectangle([mm(x - 1.3), mm(y - 8 - row * 8), mm(x + 1.3), mm(y - 4 - row * 8)], fill=(110, 82, 52))
for (tx, ty) in [(cx - 92, cy - 10), (cx + 88, cy - 6), (cx - 40, cy + 44), (cx + 60, cy + 38), (cx + 20, cy - 52)]:   # 사이프러스·올리브
    d.ellipse([mm(tx - 2.5), mm(ty - 12), mm(tx + 2.5), mm(ty)], fill=(78, 112, 60))
for (px, py) in [(cx - 70, cy + 26), (cx + 74, cy + 20), (cx - 18, cy + 50)]:               # 작은 폐허 기둥
    for j in range(3): d.rectangle([mm(px + j * 3), mm(py - 9), mm(px + j * 3 + 1.4), mm(py)], fill=(226, 214, 190), outline=(140, 120, 90))
for i in range(14):                                                   # 사람들(작은 점)
    x = cx - 60 + (i * 19) % 120; y = cy + 30 + (i * 7) % 18; d.ellipse([mm(x - .9), mm(y - 2.2), mm(x + .9), mm(y)], fill=(140, 60, 40))
lab(330, 262, "A 콜로세움 — Core 히어로", 24, C["Core"])
size_note(330, 275, "참조 디오라마 형태 · 받침 196mm")
aref = Image.open("dl/arena-ref/arena_ref.jpg").convert("RGB").resize((mm(46), mm(26)))



# G 욕장(참조 욕장 실내 절개) — 왼쪽 위 뒤쪽
grand_bath(104, 172, 118, 40)
lab(48, 102, "G 카라칼라 욕장(절개)", 22, C["Support"])
# D 판테온 — 테베레 동쪽
base_rhombus(378, 368, 78); d.ellipse([mm(358), mm(336), mm(398), mm(368)], fill=(212, 190, 150), outline=(110, 85, 55), width=4); d.pieslice([mm(358), mm(324), mm(398), mm(358)], 180, 360, fill=(196, 172, 130), outline=(110, 85, 55))
lab(344, 308, "D 판테온", 22, C["Support"])
# 작은 오브젝트: 화산재 화물선(클라우디우스 내항)
d.polygon([(mm(64), mm(286)), (mm(96), mm(286)), (mm(89), mm(295)), (mm(70), mm(295))], fill=(120, 84, 50)); d.line([mm(80), mm(268), mm(80), mm(286)], fill=(90, 70, 40), width=4)
lab(54, 298, "I 화산재 화물선", 16, (255, 255, 255))
# 위치도(바다 위 고요한 영역)
tagbox(18, 404, 106, 452, "Basic", "WHERE 위치도", ["점 실루엣 + 핀"])
# 하단 띠(신문 이중 괘선 없이 3분할)
tagbox(18, 504, 150, 566, "Core", "100년 vs 2000년", ["수명 비교 막대(사물 모양 막대)"])
tagbox(152, 504, 300, 566, "Detail", "LIME CLASTS", ["석회 알갱이 3단계 확대 단면"])
tagbox(302, 504, 412, 566, "Basic", "HISTORY · 근거", ["연대기 + MIT 2023·폼페이 2025"])
d.rectangle([mm(18), mm(570), mm(412), mm(586)], outline=C["구조"] + (255,), width=4); d.text((mm(24), mm(572)), "푸터", font=f(26), fill=(60, 60, 60))
# 범례
lx, ly = mm(232), mm(470)
lab(150, 486, "구조: 포르투스 고고학 평면도 뼈대 · 물은 땅보다 3mm 낮게(둑 흙 측면) · 포르투스는 재현도 형태", 18, (60, 40, 20))
im.save("out/wireframe_v9.png"); im.resize((840, 1188)).save("out/wireframe_v9_small.png")
print("와이어프레임 v9 생성: out/wireframe_v9.png")
