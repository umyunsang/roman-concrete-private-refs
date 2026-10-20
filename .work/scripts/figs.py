# 분석 그림 2종: (1) 베이징 지면 평면도 주석본 (2) 신문 무대 계단형 바닥 구조도(평면·단면·화면)
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
f = lambda s: ImageFont.truetype(FONT, s)
S3 = np.sqrt(3)
# ---------- (1) 베이징 평면도 주석 ----------
W, H = 2000, 2800
h2 = int(round(H * S3)); c = (W / 2, h2 / 2)
R = cv2.getRotationMatrix2D(c, -45, 1.0)
cs, sn = abs(R[0, 0]), abs(R[0, 1]); nw, nh = int(h2 * sn + W * cs), int(h2 * cs + W * sn)
R[0, 2] += nw / 2 - c[0]; R[1, 2] += nh / 2 - c[1]
def to_plan(x, y, disp=1100):
    p = R @ np.array([x, y * S3, 1.0]); return p[0] * disp / nw, p[1] * disp / nh
img = Image.open("out/bj_planXY.jpg").convert("RGB"); d = ImageDraw.Draw(img, "RGBA")
corners = [to_plan(0, 0), to_plan(2000, 0), to_plan(2000, 2800), to_plan(0, 2800)]
d.polygon(corners, outline=(255, 255, 0, 255), width=4)
notes = [((1790, 1293), "자금성 블록: 액자 오른쪽 밖으로 계속 이어짐", (40, 0)),
         ((1950, 560), "강: 액자 밖으로 계속 흐름", (-260, -60)),
         ((1950, 2250), "창안대로: 액자 아래로 빠져나감", (-330, 30)),
         ((40, 2120), "고속철: 액자 왼쪽 밖으로", (20, 40)),
         ((40, 1700), "도로망: 액자 왼쪽 밖으로", (20, -40)),
         ((1335, 1693), "천안문(남쪽 문)", (-200, 40))]
for (x, y), t, (dx, dy) in notes:
    px, py = to_plan(x, y)
    d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=(255, 255, 0, 255))
    d.line([px, py, px + dx * 0.6, py + dy * 0.6], fill=(255, 255, 0, 255), width=3)
    d.text((px + dx * 0.6 + 4, py + dy * 0.6 - 12), t, font=f(20), fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
d.text((30, 30), "베이징 지면 평면도(등각 역투영, 월드 X·Y축 정렬)", font=f(30), fill=(255, 255, 255))
d.text((30, 72), "노란 테두리 = 포스터 액자(화면 창)가 지면을 잘라 보여 주는 범위", font=f(22), fill=(255, 255, 0))
d.text((30, 102), "회색 바깥 = 화면 밖 자유공간(추정: 도로·강·자금성이 계속 이어짐)", font=f(22), fill=(220, 220, 220))
img.save("out/fig_bj_plan.jpg", quality=90)
# ---------- (2) 신문 무대 계단형 바닥 ----------
CW, CH = 1800, 1150
im = Image.new("RGB", (CW, CH), (250, 247, 240)); d = ImageDraw.Draw(im)
d.text((30, 20), "신문 제작 과정 — 중앙 무대 바닥 구조(실측 기반 복원)", font=f(34), fill=(30, 30, 30))
# 평면도(왼쪽): 판 A~D는 X 173 × Y 86 mm, E는 86 × 86 mm. 판마다 (+87, +87) mm 이동
ox, oy, s = 60, 140, 1.25
slabs = [(203 + 87 * k, 27 + 87 * k, 173 if k < 4 else 86, 86) for k in range(5)]
cols = [(228, 212, 178), (234, 219, 190), (231, 212, 180), (229, 212, 182), (226, 210, 176)]
d.text((ox, oy - 50), "① 평면도(위에서 본 모습, 월드 X·Y축)", font=f(24), fill=(30, 30, 30))
for k, (X0, Y0, LX, LY) in enumerate(slabs):
    x0, y0 = ox + (X0 - 180) * s, oy + (Y0 - 10) * s
    d.rectangle([x0, y0, x0 + LX * s, y0 + LY * s], fill=cols[k], outline=(90, 110, 60), width=4)
    d.text((x0 + 10, y0 + 8), f"판 {'ABCDE'[k]}", font=f(22), fill=(60, 50, 30))
    d.text((x0 + 10, y0 + 36), f"{LX}×{LY}mm", font=f(18), fill=(90, 80, 60))
d.text((ox, oy + 560), "판마다 X·Y로 87mm씩 이동(반 칸 비킴) → 화면에선 87mm씩 똑바로 아래로", font=f(20), fill=(120, 60, 30))
d.text((ox, oy + 590), "판 사이 접촉 변 87mm = 다음 판으로 넘어가는 통로", font=f(20), fill=(120, 60, 30))
# 단면도(가운데): 모든 판 같은 높이, 두께 6.6mm(화면)
sx0, sy0 = 760, 200
d.text((sx0, sy0 - 60), "② 단면도(옆에서 본 모습)", font=f(24), fill=(30, 30, 30))
for k in range(5):
    x = sx0 + k * 70
    d.rectangle([x, sy0 + 40, x + 140, sy0 + 40 + 6.6 * 4], fill=(222, 206, 172), outline=(90, 110, 60), width=3)
    d.rectangle([x, sy0 + 40 + 6.6 * 4, x + 140, sy0 + 40 + 6.6 * 4 + 6], fill=(90, 110, 60))
d.text((sx0, sy0 + 100), "모든 판이 같은 높이(단차 없음)", font=f(20), fill=(120, 60, 30))
d.text((sx0, sy0 + 128), "흙·잔디 측면 두께: 화면 6.6~6.8mm(실측)", font=f(20), fill=(120, 60, 30))
d.text((sx0, sy0 + 156), "측면은 판의 바깥 끝(좌·우 교대)에서만 드러남", font=f(20), fill=(120, 60, 30))
# 화면 투영(오른쪽): 같은 판을 등각으로 그려 지그재그 확인
px0, py0, ps = 1330, 120, 0.95
def iso(X, Y): return px0 + 0.866 * (X - Y) * ps - 120, py0 + 0.5 * (X + Y) * ps
d.text((1230, 60), "③ 화면 투영(등각 30°)", font=f(24), fill=(30, 30, 30))
for k, (X0, Y0, LX, LY) in enumerate(slabs):
    pts = [iso(X0, Y0), iso(X0 + LX, Y0), iso(X0 + LX, Y0 + LY), iso(X0, Y0 + LY)]
    d.polygon(pts, fill=cols[k], outline=(90, 110, 60))
    cx = sum(p[0] for p in pts) / 4; cy = sum(p[1] for p in pts) / 4
    d.text((cx - 12, cy - 12), "ABCDE"[k], font=f(22), fill=(60, 50, 30))
d.text((1230, 1060), "좌·우 접힘점이 세로 두 직선(x 78mm·302mm)에 정렬", font=f(20), fill=(120, 60, 30))
im.save("out/fig_np_floor.png")
print("그림 생성: out/fig_bj_plan.jpg, out/fig_np_floor.png")
