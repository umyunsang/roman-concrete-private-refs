# 로마 콘크리트 A2 와이어프레임 v1 (1mm = 4px)
# 규칙: 베이징 공간 배치(풀 블리드 지도·중심 랜드마크·모서리 패널·하단 3분할) + 신문 동선(2:1 반 칸 비킴 판 지그재그·번호 간판)
from PIL import Image, ImageDraw, ImageFont
import math
FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
f = lambda s: ImageFont.truetype(FONT, s)
K = 4; W, H = 420 * K, 594 * K
C = {"Core": (215, 38, 61), "Basic": (27, 152, 224), "Detail": (232, 128, 20), "Support": (46, 147, 60), "구조": (90, 90, 90)}
im = Image.new("RGB", (W, H), (233, 211, 166)); d = ImageDraw.Draw(im, "RGBA")
mm = lambda v: v * K
T30 = math.tan(math.radians(30))
for t in range(-700, 900, 20):
    for sgn in (1, -1):
        d.line([0, mm(92 + t), mm(420), mm(92 + t - sgn * 420 * T30)], fill=(205, 182, 140, 110), width=1)
def label(x, y, s, size=24, col=(30, 30, 30)):
    d.text((mm(x), mm(y)), s, font=f(size), fill=col, stroke_width=3, stroke_fill=(255, 255, 255))
def panel(x0, y0, x1, y1, tag, title, lines):
    col = C[tag]
    d.rectangle([mm(x0), mm(y0), mm(x1), mm(y1)], fill=(255, 255, 255, 160), outline=col + (255,), width=6)
    d.rectangle([mm(x0), mm(y0), mm(x0) + 150, mm(y0) + 34], fill=col + (255,))
    d.text((mm(x0) + 8, mm(y0) + 3), tag, font=f(26), fill=(255, 255, 255))
    d.text((mm(x0) + 8, mm(y0) + 42), title, font=f(30), fill=(30, 30, 30))
    for i, l in enumerate(lines): d.text((mm(x0) + 10, mm(y0) + 84 + i * 30), l, font=f(22), fill=(60, 60, 60))
def diamond(cx, cy, w, h, tag, alpha=70):
    col = C[tag]; pts = [(mm(cx), mm(cy - h / 2)), (mm(cx + w / 2), mm(cy)), (mm(cx), mm(cy + h / 2)), (mm(cx - w / 2), mm(cy))]
    d.polygon(pts, fill=col + (alpha,)); d.line(pts + [pts[0]], fill=col + (255,), width=6)
# 강(오른쪽 위 가장자리 → 콜로세움 위를 지나 → 왼쪽 가장자리의 바다)
d.line([mm(420), mm(92), mm(0), mm(92 + 420 * T30)], fill=(105, 169, 214, 235), width=mm(15))
label(318, 118, "테베레강 ← 화면 밖에서", 22, (20, 60, 110))
d.polygon([(0, mm(335)), (mm(55), mm(368)), (mm(95), mm(430)), (mm(120), mm(505)), (0, mm(505))], fill=(84, 146, 198, 215))
label(4, 488, "지중해(화면 밖으로)", 22, (255, 255, 255))
# 길
for path in ([(300, 326), (262, 348)], [(205, 252), (130, 296), (110, 340)], [(398, 252), (420, 264)]):
    d.line([(mm(x), mm(y)) for x, y in path], fill=(150, 150, 150, 230), width=mm(6))
# 타이틀(Core)
d.polygon([(mm(128), mm(34)), (mm(210), mm(10)), (mm(292), mm(34))], fill=C["Core"] + (210,))
d.rectangle([mm(136), mm(34), mm(284), mm(92)], fill=(255, 245, 230, 240), outline=C["Core"] + (255,), width=8)
d.text((mm(146), mm(39)), "ROMAN CONCRETE", font=f(64), fill=C["Core"])
d.text((mm(146), mm(61)), "부서질 때마다 스스로 고치는 2000년의 콘크리트", font=f(30), fill=(40, 40, 40))
d.text((mm(146), mm(77)), "Core: 왜 2000년을 버텼나 → 스스로 고친다", font=f(24), fill=C["Core"])
# 모서리 패널(Basic)
panel(18, 20, 125, 65, "Basic", "로마 콘크리트란?", ["정의 2~3줄 + 사실 표 6칸"])
panel(18, 75, 135, 150, "Basic", "THE RECIPE · ORDER", ["재료 4종을 같은 받침대에", "섞는 순서: 마른 혼합 → 물"])
panel(318, 20, 412, 102, "Basic", "HISTORY 연대기", ["기원전 3세기 ~ 2025", "(베이징 HISTORY 목록형)"])
# 지도 위 랜드마크
diamond(305, 250, 190, 150, "Core")
label(214, 236, "콜로세움 (Core 앵커, 히어로)", 28)
label(232, 262, "참조 디오라마 수준 · 팔각 흙 받침", 22, (60, 60, 60))
label(232, 280, "아레나·하이포게움 노출 · 기초 링 절개", 22, (60, 60, 60))
diamond(192, 140, 86, 62, "Support"); label(158, 128, "판테온", 26); label(152, 150, "돔 절개·경량 골재", 20, (60, 60, 60))
d.line([mm(420), mm(372), mm(356), mm(335)], fill=C["Support"] + (255,), width=mm(9))
for i in range(6):
    x = 420 - i * 11; y = 372 - i * 11 * T30
    d.arc([mm(x - 6), mm(y - 8), mm(x + 4), mm(y + 2)], 180, 360, fill=(255, 255, 255, 255), width=4)
label(350, 344, "수도교 ← 화면 밖에서", 24); label(352, 358, "수로 절개·방수 모르타르", 20, (60, 60, 60))
diamond(58, 432, 92, 68, "Support"); label(18, 418, "포르투스 항", 26); label(18, 440, "바닷물 속 방파제", 20, (60, 60, 60))
# 공정 지그재그(Detail): 2:1 판 3장 + 정사각 1장, 반 칸 비킴, 같은 높이, 세로 피치 42mm
ox, oy = 228, 332
def iso(X, Y): return (mm(ox + 0.866 * (X - Y)), mm(oy + 0.5 * (X + Y)))
slabs = [(0, 0, 96, 48), (48, 48, 96, 48), (96, 96, 96, 48), (144, 144, 48, 48)]
steps = ["① 재료 준비", "② 마른 혼합", "③ 물·뜨거운 혼합", "④ 타설·다짐"]
for k, (X0, Y0, LX, LY) in enumerate(slabs):
    X0 -= 48; Y0 += 0
    pts = [iso(X0, Y0), iso(X0 + LX, Y0), iso(X0 + LX, Y0 + LY), iso(X0, Y0 + LY)]
    d.polygon(pts, fill=(250, 236, 205, 255)); d.line(pts + [pts[0]], fill=C["Detail"] + (255,), width=6)
    side = pts[1] if k % 2 == 0 else pts[3]
    sx, sy = side[0] + (20 if k % 2 == 0 else -260), side[1] - 70
    d.rectangle([sx, sy, sx + 240, sy + 56], fill=(255, 244, 220, 255), outline=C["Detail"] + (255,), width=5)
    d.ellipse([sx + 6, sy + 6, sx + 50, sy + 50], fill=C["Detail"] + (255,))
    d.text((sx + 18, sy + 7), str(k + 1), font=f(30), fill=(255, 255, 255))
    d.text((sx + 58, sy + 12), steps[k][2:], font=f(26), fill=(60, 30, 0))
label(150, 488, "Detail: 폼페이 공사 현장 재현 — 판 위 작업자·도구, 바닥 화살표", 22, (110, 55, 0))
# 미시 원리(Detail) 패널 + 확대선
panel(318, 392, 412, 500, "Detail", "LIME CLASTS", ["석회 알갱이 확대 단면", "균열→빗물→칼슘 용출", "→방해석 결정→봉합", "같은 시점 3단계"])
d.line([mm(262), mm(470), mm(318), mm(450)], fill=C["Detail"] + (255,), width=5)
# 하단 띠(Support)
panel(18, 510, 180, 565, "Support", "100년 vs 2000년", ["수명 비교 막대(신문 TOP6 문법)"])
panel(182, 510, 305, 565, "Support", "근거: MIT 2023·폼페이 2025", ["연구 카드 2장 + 출처"])
panel(318, 510, 412, 565, "Support", "TODAY", ["현대 과학이 배우는 레시피"])
d.rectangle([mm(18), mm(568), mm(412), mm(586)], outline=C["구조"] + (255,), width=4)
d.text((mm(24), mm(571)), "푸터(크레딧·출처·라이선스 대장)", font=f(26), fill=(60, 60, 60))
# 범례·방위
lx, ly = mm(18), mm(165)
for i, (k, v) in enumerate([("Core", "핵심"), ("Basic", "기초"), ("Detail", "세부"), ("Support", "사례")]):
    d.rectangle([lx, ly + i * 40, lx + 30, ly + i * 40 + 30], fill=C[k]); d.text((lx + 40, ly + i * 40), f"{k} {v}", font=f(26), fill=(30, 30, 30))
label(18, 236, "북쪽 = 화면 오른쪽 위 30°", 22, (60, 60, 60))
im.save("out/wireframe_v1.png"); im.resize((840, 1188)).save("out/wireframe_v1_small.png")
print("와이어프레임 v1 생성: out/wireframe_v1.png")
