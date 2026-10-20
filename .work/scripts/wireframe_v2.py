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
# 바다(왼쪽 아래, 화면 밖으로) · 테베레강(위→왼쪽 아래 바다) · 아피아 가도(콜로세움→베수비오)
d.polygon([(0, mm(372)), (mm(40), mm(392)), (mm(92), mm(430)), (mm(130), mm(498)), (0, mm(498))], fill=(86, 148, 200, 225))
lab(4, 482, "티레니아해(화면 밖으로)", 20, (255, 255, 255))
d.line([(mm(160), mm(100)), (mm(140), mm(160)), (mm(100), mm(205)), (mm(70), mm(255)), (mm(40), mm(300)), (mm(30), mm(380))], fill=(104, 168, 214, 235), width=mm(11), joint="curve")
lab(150, 150, "테베레강", 20, (20, 60, 110))
d.line([(mm(270), mm(255)), (mm(318), mm(228)), (mm(345), mm(212))], fill=(150, 150, 150, 235), width=mm(7))
lab(282, 246, "아피아 가도", 20, (70, 70, 70))
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
lab(cx - 92, cy - 96, "A 콜로세움 — Core 앵커(히어로)", 30, C["Core"]); size_note(cx - 92, cy - 80, "약 196×180mm (베이징 자금성급 204×199)")
# 2 베수비오(유일한 화산) — 오른쪽 위, 액자 밖으로 이어짐
d.polygon([(mm(262), mm(242)), (mm(352), mm(128)), (mm(392), mm(124)), (mm(440), mm(200)), (mm(440), mm(242))], fill=(140, 100, 66), outline=(80, 52, 30))
d.ellipse([mm(350), mm(118), mm(394), mm(132)], fill=(70, 42, 26))
for i in range(4): d.ellipse([mm(358 + i * 6), mm(100 - i * 9), mm(378 + i * 6), mm(116 - i * 9)], fill=(205, 205, 205, 170))
lab(300, 104, "B 베수비오(유일한 화산)", 28, (90, 40, 10)); size_note(300, 118, "약 150×140mm, 액자 밖으로 이어짐")
# 3 헤르쿨라네움(화산 옆 건축·교외 욕장) — 베수비오 왼쪽 발치
base_rhombus(250, 150, 90); d.rectangle([mm(222), mm(122), mm(278), mm(150)], fill=(206, 176, 132), outline=(110, 85, 55), width=4)
lab(204, 104, "C 헤르쿨라네움 교외 욕장", 24, C["Support"]); size_note(204, 117, "약 90×80mm")
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
# 7 카라칼라 욕장 — 아래 가운데
base_rhombus(186, 440, 100); d.rectangle([mm(158), mm(404), mm(214), mm(438)], fill=(204, 172, 128), outline=(110, 85, 55), width=4)
for i in range(3): d.pieslice([mm(160 + i * 18), mm(396), mm(176 + i * 18), mm(412)], 180, 360, fill=(186, 154, 112))
lab(140, 380, "G 카라칼라 욕장", 24, C["Support"]); size_note(140, 393, "약 100×85mm")
# 8 공정 셀 4개(Detail): 정사각 셀 화면 111×64mm, 두 열 번갈아 32mm씩 내려감(신문 P2)
def cell(cx, cy, w):
    h = w / math.sqrt(3); pts = [(cx - w / 2, cy), (cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2)]
    d.polygon([(mm(x), mm(y)) for x, y in pts], fill=(250, 238, 210, 255)); d.line([(mm(x), mm(y)) for x, y in pts + [pts[0]]], fill=C["Detail"] + (255,), width=6)
    return pts
centers = [(318, 320), (368, 349), (318, 378), (368, 407)]
for k, (x, y) in enumerate(centers):
    cell(x, y, 100)
    d.ellipse([mm(x) - 26, mm(y) - 26, mm(x) + 26, mm(y) + 26], fill=C["Detail"] + (255,)); d.text((mm(x) - 10, mm(y) - 20), str(k + 1), font=f(32), fill=(255, 255, 255))
for (a, b) in [((335, 330), (351, 339)), ((351, 359), (335, 368)), ((335, 388), (351, 397))]:
    d.line([mm(a[0]), mm(a[1]), mm(b[0]), mm(b[1])], fill=(90, 105, 64), width=6)
lab(282, 276, "H 폼페이 공사 현장 — Detail 공정", 24, C["Detail"])
for i, s in enumerate(["① 재료 준비", "② 마른 혼합", "③ 물·뜨거운 혼합", "④ 타설·다짐"]):
    x, y = centers[i]; lab(x - 30, y + 8, s[2:], 20, (120, 60, 0))
size_note(262, 440, "셀 100×58mm(신문 148×87의 0.68배), 인물 약 18mm")
# 9~11 작은 오브젝트(탈것 33~41mm 등급)
d.polygon([(mm(64), mm(474)), (mm(104), mm(474)), (mm(96), mm(486)), (mm(70), mm(486))], fill=(120, 84, 50)); d.line([mm(84), mm(452), mm(84), mm(474)], fill=(90, 70, 40), width=4)
lab(58, 488, "I 화산재 화물선 45mm", 18, (40, 40, 40))
d.rectangle([mm(300), mm(228), mm(326), mm(242)], fill=(150, 110, 70)); lab(292, 214, "J 수레 35mm", 18, (40, 40, 40))
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
lab(140, 486, "크기 기준(베이징 실측): 히어로 204×199 · 표준 86×80(중앙값) · 탈것 33~41mm · 오브젝트가 지도의 46%를 덮음", 18, (60, 40, 20))
im.save("out/wireframe_v2.png"); im.resize((840, 1188)).save("out/wireframe_v2_small.png")
print("와이어프레임 v2 생성: out/wireframe_v2.png")
