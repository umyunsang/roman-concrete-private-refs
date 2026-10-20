# 중앙 배치 대안 3종(A 남행 두 극 / B 디오라마 섬 지그재그 / C 단면 세계) 썸네일 + 비교 시트. 1mm = 2px.
from PIL import Image, ImageDraw, ImageFont
import math
FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
f = lambda s: ImageFont.truetype(FONT, s)
K = 2; W, H = 420 * K, 594 * K
C = {"Core": (215, 38, 61), "Basic": (27, 152, 224), "Detail": (232, 128, 20), "Support": (46, 147, 60), "화산": (120, 60, 40), "바다": (84, 146, 198)}
SOIL, GRASS, TOP = (122, 96, 62), (96, 128, 70), (238, 222, 186)
mm = lambda v: v * K
def base(bg=(233, 211, 166)):
    im = Image.new("RGB", (W, H), bg); d = ImageDraw.Draw(im, "RGBA"); return im, d
def txt(d, x, y, s, size=16, col=(25, 25, 25)):
    d.text((mm(x), mm(y)), s, font=f(size), fill=col, stroke_width=3, stroke_fill=(255, 255, 255))
def panel(d, x0, y0, x1, y1, tag, title, sub=""):
    col = C[tag]
    d.rectangle([mm(x0), mm(y0), mm(x1), mm(y1)], fill=(255, 255, 255, 150), outline=col + (255,), width=3)
    d.rectangle([mm(x0), mm(y0), mm(x0) + 64, mm(y0) + 18], fill=col + (255,))
    d.text((mm(x0) + 4, mm(y0) + 1), tag, font=f(13), fill=(255, 255, 255))
    d.text((mm(x0) + 4, mm(y0) + 22), title, font=f(15), fill=(30, 30, 30))
    if sub: d.text((mm(x0) + 4, mm(y0) + 42), sub, font=f(12), fill=(70, 70, 70))
def slab(d, ox, oy, X0, Y0, LX, LY, t=8, top=TOP, outline=(90, 70, 40)):
    P = lambda X, Y, Z=0: (mm(ox + 0.866 * (X - Y)), mm(oy + 0.5 * (X + Y) - Z))
    a, b, c, e = P(X0, Y0), P(X0 + LX, Y0), P(X0 + LX, Y0 + LY), P(X0, Y0 + LY)
    d.polygon([b, c, (c[0], c[1] + mm(t)), (b[0], b[1] + mm(t))], fill=SOIL)        # +X 면
    d.polygon([e, c, (c[0], c[1] + mm(t)), (e[0], e[1] + mm(t))], fill=(104, 82, 52))  # +Y 면
    d.line([(e[0], e[1] + 2), (c[0], c[1] + 2), (b[0], b[1] + 2)], fill=GRASS, width=int(mm(1.6)))
    d.polygon([a, b, c, e], fill=top, outline=outline)
    return P
def mark(d, P, X, Y, w, tag, name, z=0, h=16):
    col = C[tag]; cx, cy = P(X, Y)
    d.ellipse([cx - mm(w / 2), cy - mm(w / 4), cx + mm(w / 2), cy + mm(w / 4)], fill=col + (150,), outline=col + (255,), width=3)
    d.text((cx - mm(w / 2), cy - mm(w / 4) - 22), name, font=f(h), fill=(20, 20, 20), stroke_width=3, stroke_fill=(255, 255, 255))
def volcano(d, cx, cy, w, h, name):
    d.polygon([(mm(cx - w / 2), mm(cy)), (mm(cx - w * 0.12), mm(cy - h)), (mm(cx + w * 0.12), mm(cy - h)), (mm(cx + w / 2), mm(cy))], fill=(132, 92, 62), outline=(80, 50, 30))
    d.ellipse([mm(cx - w * 0.12), mm(cy - h - 3), mm(cx + w * 0.12), mm(cy - h + 3)], fill=(70, 40, 25))
    for i in range(3): d.ellipse([mm(cx - 6 + i * 4), mm(cy - h - 14 - i * 6), mm(cx + 6 + i * 4), mm(cy - h - 4 - i * 6)], fill=(200, 200, 200, 160))
    d.text((mm(cx - w / 2), mm(cy) + 4), name, font=f(15), fill=(255, 255, 255), stroke_width=3, stroke_fill=(80, 40, 20))
def title(d):
    d.polygon([(mm(128), mm(34)), (mm(210), mm(12)), (mm(292), mm(34))], fill=C["Core"] + (210,))
    d.rectangle([mm(136), mm(34), mm(284), mm(90)], fill=(255, 245, 230, 240), outline=C["Core"] + (255,), width=4)
    d.text((mm(146), mm(42)), "ROMAN CONCRETE", font=f(30), fill=C["Core"])
    d.text((mm(146), mm(64)), "Core: 왜 2000년을 버텼나", font=f(15), fill=(40, 40, 40))
def bottom(d):
    panel(d, 18, 512, 180, 566, "Support", "100년 vs 2000년")
    panel(d, 182, 512, 305, 566, "Support", "근거 연구")
    panel(d, 318, 512, 412, 566, "Support", "TODAY")
def header(d, s):
    d.rectangle([0, 0, W, mm(9)], fill=(40, 40, 40)); d.text((mm(3), 1), s, font=f(15), fill=(255, 255, 255))
# ---------------- A: 남행 두 극 ----------------
im, d = base(); header(d, "A안  남행(南行) 두 극 구도 — 연속 지도")
d.polygon([(0, mm(95)), (mm(70), mm(140)), (mm(60), mm(260)), (mm(110), mm(360)), (mm(160), mm(505)), (0, mm(505))], fill=C["바다"] + (220,))
txt(d, 6, 300, "티레니아해", 15, (255, 255, 255))
title(d)
panel(d, 18, 18, 125, 88, "Basic", "로마 콘크리트란?", "정의·사실 표")
panel(d, 318, 18, 412, 102, "Basic", "THE RECIPE·ORDER", "재료 산지 → 화산")
# 로마 군집(위)
d.ellipse([mm(120), mm(110), mm(330), mm(225)], fill=(250, 238, 210, 220), outline=C["Core"] + (255,), width=3)
txt(d, 128, 104, "로마 군집", 16, C["Core"])
for (x, y, w, tag, n) in [(225, 168, 70, "Core", "콜로세움"), (160, 145, 34, "Support", "판테온"), (205, 205, 36, "Support", "카라칼라 욕장"), (290, 150, 30, "Support", "트라야누스 시장")]:
    d.ellipse([mm(x - w / 2), mm(y - w / 4), mm(x + w / 2), mm(y + w / 4)], fill=C[tag] + (150,), outline=C[tag] + (255,), width=3); txt(d, x - w / 2, y - w / 4 - 12, n, 14)
d.line([mm(420), mm(150), mm(320), mm(175)], fill=C["Support"] + (255,), width=int(mm(4))); txt(d, 335, 160, "수도교 →", 14)
txt(d, 80, 232, "포르투스 항", 15); d.ellipse([mm(80), mm(240), mm(130), mm(262)], fill=C["Support"] + (150,), outline=C["Support"] + (255,), width=3)

# 아피아 가도 S자 동선 + 번호
pts = [(230, 225), (270, 270), (230, 315), (190, 360), (230, 400), (285, 430)]
d.line([(mm(x), mm(y)) for x, y in pts], fill=(140, 140, 140), width=mm(5), joint="curve")
for i, (x, y) in enumerate(pts[1:5]):
    d.ellipse([mm(x) - 14, mm(y) - 14, mm(x) + 14, mm(y) + 14], fill=C["Detail"]); d.text((mm(x) - 5, mm(y) - 11), str(i + 1), font=f(16), fill=(255, 255, 255))
txt(d, 276, 300, "아피아 가도: 번호 정거장", 14)
# 나폴리만(아래)
txt(d, 30, 430, "바이아 욕장 돔·포추올리·미세눔(해안 건축)", 14)
volcano(d, 330, 478, 110, 66, "베수비오(유일한 화산)")
d.rectangle([mm(250), mm(400), mm(310), mm(440)], outline=C["Detail"] + (255,), width=3); txt(d, 238, 386, "폼페이 공정 판", 14)
panel(d, 18, 330, 110, 400, "Detail", "LIME CLASTS", "확대 단면")
bottom(d); A = im
# ---------------- B: 디오라마 섬 3개 지그재그 ----------------
im, d = base(); header(d, "B안  디오라마 섬 3개 지그재그 — 신문식 떠 있는 판 + 베이징식 랜드마크")
title(d)
P1 = slab(d, 90, 105, 40, 0, 160, 95, t=10)     # 로마 섬
mark(d, P1, 115, 45, 70, "Core", "콜로세움(히어로)", h=17)
mark(d, P1, 70, 25, 32, "Support", "판테온")
mark(d, P1, 175, 22, 28, "Support", "트라야누스 시장")
mark(d, P1, 150, 80, 32, "Support", "카라칼라 욕장")
txt(d, 100, 112, "섬 1 · ROME", 17, C["Core"])
P2 = slab(d, 250, 245, 20, 0, 130, 80, t=9)       # 해안·항구 섬
d.polygon([P2(60, 45), P2(150, 45), P2(150, 80), P2(60, 80)], fill=C["바다"] + (220,))
mark(d, P2, 105, 58, 38, "Support", "포르투스 항")
mark(d, P2, 50, 25, 26, "Support", "오스티아")
txt(d, 318, 250, "섬 2 · COAST", 17, C["Support"])
P3 = slab(d, 100, 370, 30, 0, 150, 80, t=10)     # 화산만 섬
volcano(d, 160, 458, 84, 52, "베수비오(유일한 화산)")
mark(d, P3, 70, 30, 26, "Support", "바이아 욕장 돔")
mark(d, P3, 45, 62, 22, "Support", "피시나 미라빌리스")
d.rectangle([mm(178), mm(468), mm(238), mm(496)], outline=C["Detail"] + (255,), width=3); txt(d, 238, 476, "폼페이 공정 판 ①~④", 13)
txt(d, 60, 372, "섬 3 · VOLCANIC BAY", 17, C["화산"])
for a, b in [((215, 238), (262, 262)), ((262, 352), (230, 388))]:
    d.line([mm(a[0]), mm(a[1]), mm(b[0]), mm(b[1])], fill=(110, 110, 110), width=4)
txt(d, 233, 342, "화산재 해상 운송로", 13, (80, 80, 80))
panel(d, 300, 112, 412, 210, "Basic", "로마 콘크리트란?", "섬이 빈 자리에 맞물림")
panel(d, 18, 270, 150, 352, "Basic", "THE RECIPE·ORDER", "+ 위치도(점 지도)")
panel(d, 318, 380, 412, 500, "Detail", "LIME CLASTS", "확대 단면 3단계")
panel(d, 18, 18, 125, 88, "Basic", "HISTORY", "연대기")
bottom(d); B = im
# ---------------- C: 단면 세계 ----------------
im, d = base(); header(d, "C안  단면 세계 — 하나의 거대한 디오라마 블록, 앞 절단면에 지하를 드러냄")
title(d)
ox, oy = 210, 120
P = lambda X, Y, Z=0: (mm(ox + 0.866 * (X - Y)), mm(oy + 0.5 * (X + Y) - Z))
LX, LY, T = 260, 170, 120
a, b, c, e = P(0, 0), P(LX, 0), P(LX, LY), P(0, LY)
d.polygon([b, c, (c[0], c[1] + mm(T)), (b[0], b[1] + mm(T))], fill=(150, 120, 85))
d.polygon([e, c, (c[0], c[1] + mm(T)), (e[0], e[1] + mm(T))], fill=(128, 100, 70))
for i, (frac, col) in enumerate([(0.25, (170, 140, 100)), (0.5, (110, 100, 95)), (0.75, (160, 110, 80))]):
    y0 = mm(T * frac)
    d.line([(e[0], e[1] + y0), (c[0], c[1] + y0), (b[0], b[1] + y0)], fill=col, width=int(mm(3)))
d.polygon([a, b, c, e], fill=TOP, outline=(90, 70, 40))
txt(d, 40, 330, "앞 절단면(지하)", 16, (60, 30, 10))
txt(d, 40, 344, "콜로세움 기초 링 · 수중 교각 · 화산재 지층", 13, (60, 30, 10))
for (X, Y, w, tag, n) in [(130, 70, 70, "Core", "콜로세움"), (60, 40, 30, "Support", "판테온"), (200, 40, 30, "Support", "카라칼라 욕장"), (60, 140, 36, "Support", "포르투스 항"), (230, 140, 30, "Support", "폼페이")]:
    cx, cy = P(X, Y); d.ellipse([cx - mm(w / 2), cy - mm(w / 4), cx + mm(w / 2), cy + mm(w / 4)], fill=C[tag] + (150,), outline=C[tag] + (255,), width=3)
    d.text((cx - mm(w / 2), cy - mm(w / 4) - 20), n, font=f(15), fill=(20, 20, 20), stroke_width=3, stroke_fill=(255, 255, 255))
volcano(d, 330, 205, 70, 46, "베수비오(유일한 화산)")
for k in range(4):
    x0 = 150 + k * 24; y0 = 400 + k * 18
    d.rectangle([mm(x0), mm(y0), mm(x0 + 40), mm(y0 + 10)], fill=(250, 236, 205), outline=C["Detail"] + (255,), width=3)
txt(d, 140, 388, "채석장 계단 공정 ①~④(절단면에 파 넣음)", 13, (110, 55, 0))
panel(d, 18, 18, 125, 88, "Basic", "로마 콘크리트란?")
panel(d, 318, 18, 412, 102, "Basic", "THE RECIPE·ORDER")
panel(d, 318, 380, 412, 500, "Detail", "LIME CLASTS")
bottom(d); Cc = im
# ---------------- 비교 시트 ----------------
sheet = Image.new("RGB", (W * 3 + 80, H + 140), (250, 248, 243)); sd = ImageDraw.Draw(sheet)
sd.text((20, 14), "중앙 배치 대안 3종 v2 — 화산은 베수비오 하나만(모두 등각·참조 디오라마 수준 모델 전제)", font=f(34), fill=(30, 30, 30))
sd.text((20, 60), "색: 빨강 Core · 파랑 Basic · 주황 Detail · 초록 Support · 갈색 화산", font=f(24), fill=(80, 80, 80))
for i, im_ in enumerate([A, B, Cc]):
    sheet.paste(im_, (20 + i * (W + 20), 110))
sheet.save("out/alt_layouts.png")
for n, im_ in zip("ABC", [A, B, Cc]): im_.save(f"out/alt_{n}.png")
print("대안 3종 생성: out/alt_layouts.png (비교 시트), out/alt_A.png·alt_B.png·alt_C.png")
