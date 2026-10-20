# 측정한 영역(A2 mm)을 포스터 위에 그려 영역 지도를 만들고, 영역별 면적 비율을 계산한다.
import cv2, numpy as np, json
from PIL import Image, ImageDraw, ImageFont
FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
Z = {
 "bj": [("T", "타이틀 록업", 128, 10, 295, 92, (255, 230, 0)),
        ("L1", "도시 정보(표)", 18, 20, 125, 65, (0, 255, 255)),
        ("L2", "문화지역(점 지도)", 18, 75, 135, 150, (0, 255, 255)),
        ("R1", "역사(타임라인)", 318, 20, 412, 102, (0, 255, 255)),
        ("M", "중앙 지도 무대(풀 블리드)", 0, 92, 420, 505, (255, 255, 255)),
        ("B1", "대표 건축(사진+글)", 18, 505, 180, 565, (0, 255, 120)),
        ("B2", "유명 음식(아이콘+글)", 182, 505, 305, 565, (0, 255, 120)),
        ("B3", "올림픽(엠블럼+글)", 318, 505, 412, 565, (0, 255, 120)),
        ("F", "푸터", 18, 568, 412, 586, (200, 200, 200))],
 "np": [("T", "타이틀 띠(정의·제목·장점)", 10, 22, 410, 100, (255, 230, 0)),
        ("L", "좌측 타임라인(한국 신문 역사)", 18, 105, 125, 575, (0, 255, 255)),
        ("M", "중앙 공정 무대(계단형 바닥)", 78, 100, 305, 562, (255, 255, 255)),
        ("R1", "퓰리처", 305, 105, 412, 155, (0, 255, 120)),
        ("R2", "인쇄 기술 변화", 305, 158, 412, 252, (0, 255, 120)),
        ("R3", "신문 지면 구성", 305, 262, 412, 385, (0, 255, 120)),
        ("R4", "신문 용지", 305, 388, 412, 482, (0, 255, 120)),
        ("R5", "TOP 6 막대그래프", 305, 485, 412, 565, (0, 255, 120)),
        ("F", "푸터", 18, 565, 412, 579, (200, 200, 200))]}
A2 = 420 * 594
res = {}
for key, zs in Z.items():
    img = Image.open(f"out/{key}_art.png").convert("RGB").resize((1000, 1400))
    d = ImageDraw.Draw(img, "RGBA"); f = ImageFont.truetype(FONT, 22)
    for code, name, x0, y0, x1, y1, col in zs:
        X0, Y0, X1, Y1 = x0 / 420 * 1000, y0 / 594 * 1400, x1 / 420 * 1000, y1 / 594 * 1400
        d.rectangle([X0, Y0, X1, Y1], outline=col + (255,), width=5, fill=col + (40,))
        d.text((X0 + 8, Y0 + 6), f"{code} {name}", font=f, fill=(0, 0, 0), stroke_width=4, stroke_fill=col)
    img.save(f"out/{key}_zones.jpg", quality=88)
    res[key] = [(c, n, round((x1 - x0) * (y1 - y0) / A2 * 100, 1), x0, y0, x1, y1) for c, n, x0, y0, x1, y1, _ in zs]
json.dump(res, open("out/zones.json", "w"), ensure_ascii=False, indent=1)
for key, rows in res.items():
    print("[베이징]" if key == "bj" else "[신문 제작 과정]")
    for c, n, pct, x0, y0, x1, y1 in rows:
        print(f"  {c:3s} {n:22s} x {x0:3d}~{x1:3d}  y {y0:3d}~{y1:3d} mm  ({x1-x0}×{y1-y0}mm, 지면의 {pct:4.1f}%)")
