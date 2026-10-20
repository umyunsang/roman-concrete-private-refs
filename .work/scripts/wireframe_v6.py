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

# 바다(왼쪽 아래, 화면 밖으로) · 테베레강(위→왼쪽 아래 바다) · 아피아 가도(콜로세움→베수비오)
d.polygon([(0, mm(372)), (mm(40), mm(392)), (mm(92), mm(430)), (mm(130), mm(498)), (0, mm(498))], fill=(86, 148, 200, 225))
lab(4, 482, "티레니아해(화면 밖으로)", 20, (255, 255, 255))
d.line([(mm(160), mm(100)), (mm(140), mm(160)), (mm(100), mm(205)), (mm(70), mm(255)), (mm(40), mm(300)), (mm(30), mm(380))], fill=(104, 168, 214, 235), width=mm(11), joint="curve")
lab(150, 150, "테베레강", 20, (20, 60, 110))
d.line([(mm(276), mm(262)), (mm(300), mm(250))], fill=(150, 150, 150, 235), width=mm(7))
lab(262, 240, "아피아 가도", 20, (70, 70, 70))
# ---- 타이틀 띠(신문식 전폭 3분할) ----
d.rectangle([mm(10), mm(12), mm(410), mm(96)], fill=(250, 244, 230, 245), outline=(60, 60, 60, 255), width=4)
d.line([mm(10), mm(16), mm(410), mm(16)], fill=(60, 60, 60), width=3); d.line([mm(10), mm(92), mm(410), mm(92)], fill=(60, 60, 60), width=3)
d.line([mm(118), mm(22), mm(118), mm(86)], fill=(80, 80, 80), width=3); d.line([mm(302), mm(22), mm(302), mm(86)], fill=(80, 80, 80), width=3)
lab(16, 20, "Basic  로마 콘크리트란?", 26, C["Basic"]); lab(16, 34, "정의 2줄 + 속성 칩(원형) 5~7개", 20, (70, 70, 70))
lab(126, 24, "ROMAN CONCRETE", 58, C["Core"]); lab(126, 48, "부서질 때마다 스스로 고치는 2000년의 콘크리트", 30, (40, 40, 40))
lab(126, 64, "Core: 왜 2000년을 버텼나 → 스스로 고친다", 24, C["Core"])
lab(308, 20, "Basic  THE RECIPE · ORDER", 26, C["Basic"]); lab(308, 34, "재료 아이콘 4개 + 섞는 순서", 20, (70, 70, 70))
lab(308, 46, "(신문 ADVANTAGES 아이콘 열 문법)", 20, (70, 70, 70))
# ---- 지도 오브젝트(개별 배치, 베이징 크기 등급) ----
# 1 콜로세움 히어로 205×185 (중앙)
cx, cy = 186, 285
base_rhombus(cx, cy + 25, 196, t=7)
for k, (rw, rh, z) in enumerate([(150, 72, 0), (150, 72, 34)]):
    pass
d.ellipse([mm(cx - 78), mm(cy - 28), mm(cx + 78), mm(cy + 48)], fill=(214, 186, 140), outline=(120, 90, 60), width=5)
d.ellipse([mm(cx - 78), mm(cy - 62), mm(cx + 78), mm(cy + 14)], fill=(226, 200, 156), outline=(120, 90, 60), width=5)
d.ellipse([mm(cx - 46), mm(cy - 46), mm(cx + 46), mm(cy - 2)], fill=(190, 160, 115), outline=(120, 90, 60), width=4)
lab(18, 212, "A 콜로세움 — Core 앵커(히어로)", 30, C["Core"]); size_note(18, 228, "약 196×180mm (베이징 자금성급 204×199)")
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
# 3 (삭제) 헤르쿨라네움 — 욕장은 하나만. 화산 밑동은 낮은 포도밭 구릉으로 가림(겹침 원근 유지)
d.polygon([(mm(330), mm(150)), (mm(352), mm(138)), (mm(378), mm(141)), (mm(404), mm(134)), (mm(420), mm(140)), (mm(420), mm(152)), (mm(330), mm(152))], fill=(150, 160, 104), outline=(110, 120, 70))
for i in range(9): d.line([mm(336 + i * 9), mm(146), mm(340 + i * 9), mm(141)], fill=(110, 125, 70), width=3)
lab(332, 154, "포도밭 구릉(화산 밑동을 가림)", 18, (90, 100, 50))
# 4 판테온 — 왼쪽 위
base_rhombus(66, 150, 92); d.ellipse([mm(42), mm(112), mm(90), mm(150)], fill=(212, 190, 150), outline=(110, 85, 55), width=4); d.pieslice([mm(42), mm(100), mm(90), mm(140)], 180, 360, fill=(196, 172, 130), outline=(110, 85, 55))
lab(20, 104, "D 판테온", 24, C["Support"]); size_note(20, 117, "약 92×85mm")
# 5 수도교 — 왼쪽 가장자리에서 들어옴
for i in range(7):
    x0 = 0 + i * 16; y0 = 330 - i * 16 * T30
    d.rectangle([mm(x0), mm(y0 - 34), mm(x0 + 14), mm(y0)], fill=(206, 178, 134), outline=(110, 85, 55), width=3)
    d.pieslice([mm(x0 + 3), mm(y0 - 20), mm(x0 + 11), mm(y0 - 8)], 180, 360, fill=(120, 96, 64))
lab(4, 266, "E 수도교(화면 밖에서)", 24, C["Support"]); size_note(4, 279, "약 115×45mm 선형")
# 6 포르투스 항 — 왼쪽 아래 바다
d.polygon([(mm(46), mm(410)), (mm(86), mm(398)), (mm(118), mm(414)), (mm(118), mm(444)), (mm(80), mm(458)), (mm(46), mm(442))], fill=(84, 146, 198), outline=(210, 196, 160), width=mm(3))
lab(30, 382, "F 포르투스 항", 24, C["Support"]); size_note(30, 395, "약 105×85mm")
# 7 카라칼라 욕장 — 뒤쪽(위 가운데, 타이틀 띠 바로 아래)으로 이동. Support라 배경층 축소 없음, 약 132×110mm
grand_bath(238, 178, 132, 46)
lab(306, 166, "G 카라칼라 욕장(절개)", 24, C["Support"])
size_note(306, 179, "약 132×110mm · 뒤쪽 배치")
ref = Image.open("dl/bath-ref/bath_ref.jpg").convert("RGB").resize((mm(24), mm(30)))
im.paste(ref, (mm(388), mm(186))); d.rectangle([mm(388), mm(186), mm(412), mm(216)], outline=C["Support"] + (255,), width=4)
lab(384, 217, "참조 욕장", 16, C["Support"])
# 비워진 앞쪽(아래 가운데): 추가 Support 후보 자리
d.rectangle([mm(130), mm(392), mm(290), mm(480)], outline=(120, 120, 120, 255), width=4)
lab(136, 398, "추가 Support 후보 자리", 24, (90, 90, 90)); lab(136, 412, "(조사 결과 반영 예정)", 20, (110, 110, 110))
# 8 공정 셀 4개(Detail): 정사각 셀 화면 111×64mm, 두 열 번갈아 32mm씩 내려감(신문 P2)
def cell(cx, cy, w):
    h = w / math.sqrt(3); pts = [(cx - w / 2, cy), (cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2)]
    d.polygon([(mm(x), mm(y)) for x, y in pts], fill=(250, 238, 210, 255)); d.line([(mm(x), mm(y)) for x, y in pts + [pts[0]]], fill=C["Detail"] + (255,), width=6)
    return pts
centers = [(318, 262), (368, 291), (318, 320), (368, 349)]
for k, (x, y) in enumerate(centers):
    cell(x, y, 100)
    d.ellipse([mm(x) - 26, mm(y) - 26, mm(x) + 26, mm(y) + 26], fill=C["Detail"] + (255,)); d.text((mm(x) - 10, mm(y) - 20), str(k + 1), font=f(32), fill=(255, 255, 255))
for (a, b) in [((335, 272), (351, 281)), ((351, 301), (335, 310)), ((335, 330), (351, 339))]:
    d.line([mm(a[0]), mm(a[1]), mm(b[0]), mm(b[1])], fill=(90, 105, 64), width=6)
lab(262, 222, "H 폼페이 공사 현장 — Detail 공정", 24, C["Detail"])
for i, s in enumerate(["① 재료 준비", "② 마른 혼합", "③ 물·뜨거운 혼합", "④ 타설·다짐"]):
    x, y = centers[i]; lab(x - 30, y + 8, s[2:], 20, (120, 60, 0))
size_note(262, 382, "셀 100×58mm(신문 148×87의 0.68배), 인물 약 18mm")
d.ellipse([mm(352), mm(392), mm(398), mm(438)], outline=C["Detail"] + (255,), width=6); lab(300, 440, "④ 석회 알갱이 원형 확대 창(신문 P12)", 20, (120, 60, 0))
# 9~11 작은 오브젝트(탈것 33~41mm 등급)
d.polygon([(mm(64), mm(474)), (mm(104), mm(474)), (mm(96), mm(486)), (mm(70), mm(486))], fill=(120, 84, 50)); d.line([mm(84), mm(452), mm(84), mm(474)], fill=(90, 70, 40), width=4)
lab(58, 488, "I 화산재 화물선 45mm", 18, (40, 40, 40))
d.rectangle([mm(282), mm(250), mm(300), mm(260)], fill=(150, 110, 70)); lab(240, 262, "J 수레 35mm", 18, (40, 40, 40))
d.rectangle([mm(108), mm(330), mm(118), mm(356)], fill=(120, 90, 60)); d.ellipse([mm(100), mm(326), mm(126), mm(344)], outline=(120, 90, 60), width=4)
lab(84, 358, "K 답차 기중기 40mm", 18, (40, 40, 40))
# 위치도(Basic) — 지도 왼쪽 위 고요한 영역에 작은 점 지도
tagbox(330, 452, 412, 498, "Basic", "WHERE 위치도", ["점 실루엣 + 핀 4"])
# 하단 띠(신문 이중 괘선 없이 3분할)
tagbox(18, 504, 150, 566, "Core", "100년 vs 2000년", ["수명 비교 막대(사물 모양 막대)"])
tagbox(152, 504, 300, 566, "Detail", "LIME CLASTS", ["석회 알갱이 3단계 확대 단면"])
tagbox(302, 504, 412, 566, "Basic", "HISTORY · 근거", ["연대기 + MIT 2023·폼페이 2025"])
d.rectangle([mm(18), mm(570), mm(412), mm(586)], outline=C["구조"] + (255,), width=4); d.text((mm(24), mm(572)), "푸터", font=f(26), fill=(60, 60, 60))
# 범례
lx, ly = mm(232), mm(470)
lab(18, 494, "크기 위계: Core ≈200 > Detail 셀 ≈100 > Support ≈86~132 > Support-2 ≈50~65(뒤끝·원근) > 소품 35~45mm", 18, (60, 40, 20))
im.save("out/wireframe_v6.png"); im.resize((840, 1188)).save("out/wireframe_v6_small.png")
print("와이어프레임 v6 생성: out/wireframe_v6.png")
