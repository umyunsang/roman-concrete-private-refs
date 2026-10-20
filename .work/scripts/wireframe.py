# 로마 콘크리트 A2 와이어프레임 초안 v0 (분석 규칙 적용). 1mm = 4px.
from PIL import Image, ImageDraw, ImageFont
import math
FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
f = lambda s: ImageFont.truetype(FONT, s)
K = 4; W, H = 420 * K, 594 * K
C = {"Core": (215, 38, 61), "Basic": (27, 152, 224), "Detail": (244, 157, 55), "Support": (46, 147, 60), "구조": (90, 90, 90)}
im = Image.new("RGB", (W, H), (233, 211, 166)); d = ImageDraw.Draw(im, "RGBA")
mm = lambda v: v * K
def iso(X, Y, ox, oy): return (mm(ox + 0.866 * (X - Y)), mm(oy + 0.5 * (X + Y)))
# 등각 격자(지도 영역)
for t in range(-700, 900, 20):
    for sgn in (1, -1):
        x0, y0 = 0, 92 + t; x1 = 420; y1 = y0 - sgn * 420 * math.tan(math.radians(30))
        d.line([mm(x0), mm(y0), mm(x1), mm(y1)], fill=(205, 182, 140, 120), width=1)
def panel(x0, y0, x1, y1, tag, title, lines):
    col = C[tag]
    d.rectangle([mm(x0), mm(y0), mm(x1), mm(y1)], fill=(255, 255, 255, 150), outline=col + (255,), width=6)
    d.rectangle([mm(x0), mm(y0), mm(x0) + 150, mm(y0) + 34], fill=col + (255,))
    d.text((mm(x0) + 8, mm(y0) + 3), tag, font=f(26), fill=(255, 255, 255))
    d.text((mm(x0) + 8, mm(y0) + 42), title, font=f(30), fill=(30, 30, 30))
    for i, l in enumerate(lines): d.text((mm(x0) + 10, mm(y0) + 84 + i * 30), l, font=f(22), fill=(60, 60, 60))
def site(cx, cy, w, h, tag, title, lines, shape="diamond"):
    col = C[tag]
    pts = [(mm(cx), mm(cy - h / 2)), (mm(cx + w / 2), mm(cy)), (mm(cx), mm(cy + h / 2)), (mm(cx - w / 2), mm(cy))]
    d.polygon(pts, fill=col + (70,), outline=col + (255,))
    d.line(pts + [pts[0]], fill=col + (255,), width=6)
    d.text((mm(cx - w / 2) + 10, mm(cy - h / 2) - 4), title, font=f(30), fill=(20, 20, 20), stroke_width=4, stroke_fill=(255, 255, 255))
    for i, l in enumerate(lines): d.text((mm(cx - w / 2) + 10, mm(cy - h / 2) + 34 + i * 28), l, font=f(22), fill=(40, 40, 40), stroke_width=3, stroke_fill=(255, 255, 255))
# 테베레강 · 바다 · 길
d.line([mm(420), mm(108), mm(160), mm(258), mm(60), mm(300), mm(0), mm(338)], fill=(105, 169, 214, 230), width=mm(16), joint="curve")
d.text((mm(335), mm(140)), "테베레강(화면 밖에서 흘러듦)", font=f(22), fill=(20, 60, 110))
d.polygon([(0, mm(330)), (mm(70), mm(370)), (mm(120), mm(440)), (mm(150), mm(505)), (0, mm(505))], fill=(90, 150, 200, 200))
d.text((mm(8), mm(470)), "지중해(화면 밖으로 이어짐)", font=f(22), fill=(255, 255, 255))
for path in ([(285, 330), (285, 360), (240, 386)], [(200, 290), (120, 336), (95, 380)]):
    d.line([(mm(x), mm(y)) for x, y in path], fill=(150, 150, 150, 230), width=mm(7))
d.text((mm(292), mm(342)), "아피아 가도", font=f(22), fill=(70, 70, 70))
# 타이틀(Core)
d.polygon([(mm(128), mm(34)), (mm(210), mm(10)), (mm(292), mm(34))], fill=C["Core"] + (200,))
d.rectangle([mm(136), mm(34), mm(284), mm(92)], fill=(255, 245, 230, 235), outline=C["Core"] + (255,), width=8)
d.text((mm(150), mm(40)), "ROMAN CONCRETE", font=f(64), fill=C["Core"])
d.text((mm(150), mm(62)), "로마 콘크리트 — 부서질 때마다 스스로 고친다", font=f(34), fill=(40, 40, 40))
d.text((mm(150), mm(78)), "Core: 핵심 질문과 답 · 2000년 vs 100년", font=f(24), fill=C["Core"])
# 상단 모서리 패널(Basic)
panel(18, 20, 125, 65, "Basic", "로마 콘크리트란?", ["정의 2~3줄 + 사실 표 6칸", "(베이징 도시정보·신문 정의 박스)"])
panel(18, 75, 135, 150, "Basic", "THE RECIPE · ORDER", ["재료 4종: 화산재·생석회·물·화산암", "같은 형식 받침대 + 분기선", "섞는 순서 3단계(마른 혼합→물)"])
panel(318, 20, 412, 102, "Basic", "HISTORY 연대기", ["기원전 3세기 첫 사용", "126 판테온 … 2023 MIT", "2025 폼페이 연구(목록형)"])
# 지도 위 랜드마크
site(285, 252, 190, 150, "Core", "콜로세움(중심 앵커)", ["참조 디오라마 수준 3D", "내부 아레나·하이포게움 노출", "콘크리트 기초 링 절개"])
site(190, 148, 92, 70, "Support", "판테온", ["돔 절개: 골재 경량화", "철근 없는 최대 돔"])
site(392, 345, 70, 60, "Support", "수도교", ["화면 오른쪽 밖에서 들어옴", "수로 절개: 방수 모르타르"])
site(78, 418, 120, 90, "Support", "포르투스 항", ["바닷물 속 방파제", "더 단단해지는 반응"])
# 공정 계단(Detail): 2:1 판 4장, 반 칸 비킴, 같은 높이
ox, oy = 165, 330
for k in range(4):
    X0, Y0 = 22 * k, 22 * k; LX, LY = 44 if k < 3 else 22, 22
    pts = [iso(X0, Y0, ox, oy), iso(X0 + LX, Y0, ox, oy), iso(X0 + LX, Y0 + LY, ox, oy), iso(X0, Y0 + LY, ox, oy)]
    d.polygon(pts, fill=(250, 236, 205, 255), outline=C["Detail"] + (255,))
    d.line(pts + [pts[0]], fill=C["Detail"] + (255,), width=6)
    cx = sum(p[0] for p in pts) / 4; cy = sum(p[1] for p in pts) / 4
    d.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], fill=C["Detail"] + (255,))
    d.text((cx - 10, cy - 20), str(k + 1), font=f(32), fill=(255, 255, 255))
d.text((mm(150), mm(318)), "Detail 공정(폼페이 공사 현장)", font=f(30), fill=(20, 20, 20), stroke_width=4, stroke_fill=(255, 255, 255))
for i, t in enumerate(["① 재료 준비", "② 마른 혼합", "③ 물·뜨거운 혼합", "④ 타설·다짐"]):
    d.text((mm(262), mm(384 + i * 24)), t, font=f(26), fill=(120, 60, 0), stroke_width=3, stroke_fill=(255, 255, 255))
d.text((mm(150), mm(470)), "판 위 작업자·도구, 바닥 화살표, 번호 간판", font=f(22), fill=(80, 50, 10))
# 미시 원리(Detail) 패널 + 확대선
panel(318, 380, 412, 500, "Detail", "LIME CLASTS", ["석회 알갱이 확대 단면", "균열→빗물→칼슘 용출", "→방해석 결정→봉합", "(같은 시점 3단계)"])
d.line([mm(247), mm(470), mm(318), mm(440)], fill=C["Detail"] + (255,), width=5)
# 하단 띠
panel(18, 510, 180, 565, "Support", "100년 vs 2000년", ["현대·로마 수명 비교 막대", "(신문 TOP6 막대 문법)"])
panel(182, 510, 305, 565, "Support", "근거: MIT 2023·폼페이 2025", ["연구 카드 2장 + 출처"])
panel(318, 510, 412, 565, "Support", "TODAY", ["현대 과학이 배우는 레시피", "자가치유 콘크리트 연구"])
d.rectangle([mm(18), mm(568), mm(412), mm(586)], outline=C["구조"] + (255,), width=4)
d.text((mm(24), mm(571)), "푸터(크레딧·출처·라이선스 대장)", font=f(26), fill=(60, 60, 60))
# 범례
lx, ly = mm(18), mm(158)
for i, (k, v) in enumerate([("Core", "핵심"), ("Basic", "기초"), ("Detail", "세부"), ("Support", "사례")]):
    d.rectangle([lx, ly + i * 40, lx + 30, ly + i * 40 + 30], fill=C[k])
    d.text((lx + 40, ly + i * 40), f"{k} {v}", font=f(26), fill=(30, 30, 30))
d.text((mm(18), mm(326)), "북쪽 = 화면 오른쪽 위 30°", font=f(22), fill=(60, 60, 60))
d.text((mm(18), mm(338)), "(베이징과 같은 방위 규칙)", font=f(22), fill=(60, 60, 60))
im.save("out/wireframe_v0.png")
im.resize((840, 1188)).save("out/wireframe_v0_small.png")
print("와이어프레임 v0 생성: out/wireframe_v0.png (1680x2376, 1mm=4px)")
