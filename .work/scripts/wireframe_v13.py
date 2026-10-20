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
lab(126, 64, "Core: 로마 콘크리트 제작 과정(뜨거운 혼합) → 지도 오른쪽 6단계", 24, C["Core"])
lab(308, 20, "Basic  THE RECIPE · ORDER", 26, C["Basic"]); lab(308, 34, "재료 아이콘 4개 + 섞는 순서", 20, (70, 70, 70))
lab(308, 46, "(신문 ADVANTAGES 아이콘 열 문법)", 20, (70, 70, 70))

# ===== v12: 정보 위계 배치. 아레나 최대 > Core 제작 과정(크게) > Basic·Detail > Support(작게) > Support-2 =====
# 바다(왼쪽 아래) · 테베레강(위 가운데 → 아레나와 공정 사이 → 아래 → 바다)
d.polygon([(0, mm(400)), (mm(40), mm(412)), (mm(92), mm(452)), (mm(120), mm(498)), (0, mm(498))], fill=(86, 148, 200, 225))
lab(4, 482, "티레니아해", 18, (255, 255, 255))
d.line([(mm(244), mm(100)), (mm(232), mm(160)), (mm(228), mm(260)), (mm(228), mm(360)), (mm(200), mm(430)), (mm(140), mm(470)), (mm(104), mm(498))], fill=(104, 168, 214, 235), width=mm(9), joint="curve")
lab(250, 104, "테베레강", 18, (20, 60, 110))
# 2 베수비오 — Support-2(사례의 사례): 뷰 윈도우 뒤끝 지평선 띠, 원근 배율 0.6, 대기 원근(바탕색 50% 혼합), 앞 오브젝트에 밑동이 가려짐
BG = (231, 208, 160)
mix = lambda c, a=0.5: tuple(int(c[i] * (1 - a) + BG[i] * a) for i in range(3))
for xx in range(0, 420, 6):
    d.line([mm(xx), mm(146), mm(xx + 3), mm(146)], fill=(150, 130, 100), width=2)
lab(150, 135, "배경층(지평선 띠): 원근 배율 0.6 · 대기 원근 · 겹침 단서", 18, (120, 100, 70))
d.polygon([(mm(362), mm(146)), (mm(378), mm(126)), (mm(383), mm(127)), (mm(388), mm(124)), (mm(404), mm(146))], fill=mix((140, 100, 66)), outline=mix((80, 52, 30)))
for i in range(3): d.ellipse([mm(381 + i * 3), mm(104 - i * 6), mm(391 + i * 3), mm(112 - i * 6)], fill=mix((205, 205, 205), 0.35) + (150,))
d.line([mm(398), mm(110), mm(398), mm(124)], fill=(90, 70, 50), width=3); d.ellipse([mm(397), mm(123), mm(399.5), mm(125.5)], fill=(90, 70, 50))
lab(400, 104, "베수비오", 18, (90, 60, 30))
size_note(300, 104, "Support-2 · 약 42×22mm")
# 3 (삭제) 헤르쿨라네움 — 욕장은 하나만. 화산 밑동은 낮은 포도밭 구릉으로 가림(겹침 원근 유지)
d.polygon([(mm(330), mm(150)), (mm(352), mm(138)), (mm(378), mm(141)), (mm(404), mm(134)), (mm(420), mm(140)), (mm(420), mm(152)), (mm(330), mm(152))], fill=(150, 160, 104), outline=(110, 120, 70))
for i in range(9): d.line([mm(336 + i * 9), mm(146), mm(340 + i * 9), mm(141)], fill=(110, 125, 70), width=3)
lab(332, 154, "포도밭 구릉(화산 밑동을 가림)", 18, (90, 100, 50))
# 1 콜로세움 — 참조 디오라마 형태: 팔각 흙 받침 · 뒤 왼쪽만 남은 4층 외벽 · 무너진 앞쪽 고리 · 아레나 반쪽 나무 바닥 + 하이포게움 노출 · 광장·나무·폐허
cx, cy = 118, 296
S3 = math.sqrt(3)
def isoP(X, Y): return (cx + 0.866 * (X - Y), cy + 0.5 * (X + Y))
r = 210 / 2.264   # 화면 폭 196mm가 되는 팔각 외접 반지름
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
lab(18, 200, "A 아레나(콜로세움) — 가장 큰 오브젝트", 28, C["Core"])
size_note(18, 214, "투영 약 210×160mm(최대) · 참조 디오라마 형태")

# Core 제작 과정 — 신문식 셀 체인 6개(셀 화면 폭 110mm, 두 열 반 셀씩 번갈아 내려감), 인물 약 22mm
def cell(cx, cy, w):
    h = w / math.sqrt(3); pts = [(cx - w / 2, cy), (cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2)]
    d.polygon([(mm(x), mm(y)) for x, y in pts], fill=(250, 238, 210, 255)); d.line([(mm(x), mm(y)) for x, y in pts + [pts[0]]], fill=C["Core"] + (255,), width=7)
    # 흙·잔디 측면(바깥 앞쪽 변)
    d.polygon([(mm(pts[0][0]), mm(pts[0][1])), (mm(pts[3][0]), mm(pts[3][1])), (mm(pts[3][0]), mm(pts[3][1] + 5)), (mm(pts[0][0]), mm(pts[0][1] + 5))], fill=SOIL)
    d.polygon([(mm(pts[3][0]), mm(pts[3][1])), (mm(pts[2][0]), mm(pts[2][1])), (mm(pts[2][0]), mm(pts[2][1] + 5)), (mm(pts[3][0]), mm(pts[3][1] + 5))], fill=(104, 80, 50))
    d.polygon([(mm(x), mm(y)) for x, y in pts], fill=(250, 238, 210, 255), outline=C["Core"] + (255,))
w = 96; hh = w / math.sqrt(3) / 2
centers = [(290, 200), (338, 200 + hh), (290, 200 + 2 * hh), (338, 200 + 3 * hh), (290, 200 + 4 * hh), (338, 200 + 5 * hh)]
steps = ["재료 준비(화산재·생석회·골재)", "마른 혼합(생석회+화산재)", "물 붓기", "뜨거운 혼합(발열·증기)", "타설·다짐(거푸집)", "굳기 · 석회 알갱이 형성"]
for k in range(5, -1, -1):
    cell(*centers[k], w)
for k, (x, y) in enumerate(centers):
    d.ellipse([mm(x) - 30, mm(y) - 30, mm(x) + 30, mm(y) + 30], fill=C["Core"] + (255,)); d.text((mm(x) - 12, mm(y) - 24), str(k + 1), font=f(38), fill=(255, 255, 255))
    lab(x - 40, y + 9, steps[k], 18, (120, 20, 30))
for k in range(5):
    (x1, y1), (x2, y2) = centers[k], centers[k + 1]; mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    d.line([mm(mx - 5), mm(my - 3), mm(mx + 5), mm(my + 3)], fill=(90, 105, 64), width=7)
lab(238, 150, "CORE  로마 콘크리트 제작 과정(뜨거운 혼합) — 셀 6개", 28, C["Core"])
size_note(238, 166, "투영: 셀 96×55mm · 공정 전체 약 144×199mm · 작업자 약 19mm")
# Detail: ⑥에서 석회 알갱이 원형 확대 창으로
d.ellipse([mm(322), mm(384), mm(402), mm(464)], outline=C["Detail"] + (255,), width=8); d.line([mm(338), mm(368), mm(350), mm(388)], fill=C["Detail"] + (255,), width=5)
lab(306, 466, "Detail 석회 알갱이 확대 창(투영 80×80mm)", 20, C["Detail"])
# Support(작게) — 판테온·욕장·수도교·추가 후보
base_rhombus(50, 142, 62); d.ellipse([mm(34), mm(114), mm(66), mm(142)], fill=(212, 190, 150), outline=(110, 85, 55), width=4); d.pieslice([mm(34), mm(105), mm(66), mm(134)], 180, 360, fill=(196, 172, 130), outline=(110, 85, 55))
lab(18, 104, "D 판테온", 20, C["Support"]); size_note(18, 116, "Support · 투영 62×55mm")
grand_bath(156, 150, 76, 26)
lab(118, 104, "G 욕장(절개)", 20, C["Support"]); size_note(118, 116, "Support · 투영 76×70mm, 뒤쪽")
for i in range(5):
    x0 = 0 + i * 12; y0 = 404 - i * 12 * T30
    d.rectangle([mm(x0), mm(y0 - 26), mm(x0 + 11), mm(y0)], fill=(206, 178, 134), outline=(110, 85, 55), width=3)
    d.pieslice([mm(x0 + 2.5), mm(y0 - 16), mm(x0 + 8.5), mm(y0 - 7)], 180, 360, fill=(120, 96, 64))
lab(4, 346, "E 수도교(화면 밖에서)", 20, C["Support"]); size_note(4, 358, "Support · 투영 60×50mm")
d.rectangle([mm(130), mm(380), mm(190), mm(422)], outline=(120, 120, 120, 255), width=4); lab(133, 384, "추가 Support 자리", 16, (90, 90, 90)); lab(133, 396, "(투영 60×42 이하)", 14, (110, 110, 110))
# 6 포르투스 항 — 재현도 형태(육각 내항 + 붉은 기와 창고 열 + 짧은 곡선 방파제 + 등대), 크기 축소 약 100×55mm, 왼쪽 아래 바다
ROOF = (196, 112, 72)
def roof_box(x, y, w, h):
    hh = w / math.sqrt(3)
    d.polygon([(mm(x - w / 2), mm(y - h)), (mm(x), mm(y - h + hh / 2)), (mm(x), mm(y + hh / 2)), (mm(x - w / 2), mm(y))], fill=(214, 186, 144))
    d.polygon([(mm(x), mm(y - h + hh / 2)), (mm(x + w / 2), mm(y - h)), (mm(x + w / 2), mm(y)), (mm(x), mm(y + hh / 2))], fill=(190, 160, 118))
    d.polygon([(mm(x - w / 2), mm(y - h)), (mm(x), mm(y - h - hh / 2)), (mm(x + w / 2), mm(y - h)), (mm(x), mm(y - h + hh / 2))], fill=ROOF, outline=(130, 70, 40))
hx, hy, hr = 66, 440, 14
hexp = [(hx + hr * math.cos(math.radians(60 * k)), hy + hr * .577 * math.sin(math.radians(60 * k))) for k in range(6)]
d.polygon([(mm(x), mm(y)) for x, y in hexp], fill=(126, 98, 62))
d.polygon([(mm(x), mm(y + 2)) for x, y in hexp], fill=(112, 172, 214))
for k in range(6):
    a, b = hexp[k], hexp[(k + 1) % 6]
    for t in (.3, .7):
        x = a[0] + (b[0] - a[0]) * t; y = a[1] + (b[1] - a[1]) * t
        roof_box(x + (x - hx) * .28, y + (y - hy) * .38, 5.5, 2.5)
d.line([(mm(24), mm(430)), (mm(36), mm(422)), (mm(50), mm(422))], fill=(222, 210, 182), width=mm(2.6), joint="curve")
d.line([(mm(26), mm(458)), (mm(40), mm(463)), (mm(54), mm(457))], fill=(222, 210, 182), width=mm(2.6), joint="curve")
d.rectangle([mm(20), mm(438), mm(24), mm(448)], fill=(238, 226, 200), outline=(110, 85, 55), width=3)
d.polygon([(mm(20.5), mm(438)), (mm(22), mm(434)), (mm(23.5), mm(438))], fill=(240, 196, 90))
lab(18, 404, "F 포르투스 항", 20, C["Support"]); size_note(18, 416, "Support · 투영 64×40mm")

tagbox(124, 436, 224, 496, "Basic", "WHERE 위치도", ["투영 100×60mm"])
# 하단 띠(신문 이중 괘선 없이 3분할)
tagbox(18, 504, 150, 566, "Basic", "100년 vs 2000년", ["수명 비교 막대(사물 모양 막대)"])
tagbox(152, 504, 300, 566, "Detail", "LIME CLASTS", ["석회 알갱이 3단계 확대 단면"])
tagbox(302, 504, 412, 566, "Basic", "HISTORY · 근거", ["연대기 + MIT 2023·폼페이 2025"])
d.rectangle([mm(18), mm(570), mm(412), mm(586)], outline=C["구조"] + (255,), width=4); d.text((mm(24), mm(572)), "푸터", font=f(26), fill=(60, 60, 60))
# 범례
lx, ly = mm(232), mm(470)
lab(232, 486, "크기는 모두 화면 투영 기준(폭×높이 mm)", 18, (60, 40, 20))

# ---- 투영 크기 위계 검사(화면 투영 박스, mm) ----
REG = [("아레나(콜로세움)", "아레나", 13, 207, 223, 367), ("Core 제작 과정(셀 6)", "Core", 242, 172, 386, 371),
       ("Basic 로마 콘크리트란?(타이틀 띠 왼쪽)", "Basic", 10, 16, 118, 92), ("Basic THE RECIPE·ORDER(띠 오른쪽)", "Basic", 302, 16, 410, 92),
       ("Basic WHERE 위치도", "Basic", 124, 436, 224, 496), ("Basic 100년 vs 2000년", "Basic", 18, 504, 150, 566), ("Basic HISTORY·근거", "Basic", 302, 504, 412, 566),
       ("Detail LIME CLASTS 패널", "Detail", 152, 504, 300, 566), ("Detail 확대 창", "Detail", 322, 384, 402, 464),
       ("Support 욕장(절개)", "Support", 118, 96, 194, 166), ("Support 판테온", "Support", 19, 105, 81, 160), ("Support 수도교", "Support", 0, 352, 60, 404),
       ("Support 포르투스", "Support", 20, 422, 84, 463), ("Support 추가 후보 자리", "Support", 130, 380, 190, 422), ("Support-2 베수비오", "Support-2", 362, 120, 404, 146)]
area = {n: (x1 - x0) * (y1 - y0) for n, t, x0, y0, x1, y1 in REG}
print("투영 크기 표(화면 폭×높이 mm, 면적 mm²):")
for n, t, x0, y0, x1, y1 in REG: print(f"  [{t:9s}] {n:30s} {x1-x0:4d}×{y1-y0:<4d} = {area[n]:6d}")
A = [area[n] for n, t, *_ in REG if t == "아레나"][0]; Cc = max(area[n] for n, t, *_ in REG if t == "Core")
BD = min(area[n] for n, t, *_ in REG if t in ("Basic", "Detail")); Sp = max(area[n] for n, t, *_ in REG if t == "Support"); S2 = max(area[n] for n, t, *_ in REG if t == "Support-2")
ok = A > Cc > BD > Sp > S2
print(f"위계 검사: 아레나 {A} > Core {Cc} > Basic·Detail 최소 {BD} > Support 최대 {Sp} > Support-2 {S2} → {'통과' if ok else '실패'}")

im.save("out/wireframe_v13.png"); im.resize((840, 1188)).save("out/wireframe_v13_small.png")
print("와이어프레임 v13 생성: out/wireframe_v13.png")
