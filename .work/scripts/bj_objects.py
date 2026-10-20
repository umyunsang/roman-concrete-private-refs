# 베이징 지도 오브젝트를 GrabCut으로 분할해 크기를 잰다(아트 2000x2800 기준, 1px=0.21x0.2121mm).
import cv2, numpy as np, json
from PIL import Image, ImageDraw, ImageFont
img = cv2.imread("out/bj_art.png"); H, W = img.shape[:2]
lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
bg = np.array([51 * 2.55, 58 + 128, 42 + 128], np.float32)          # 바탕 빨강 #d94234 (Lab)
dE_bg = np.sqrt(((lab - bg) ** 2).sum(-1))
O = [  # 이름, 거친 사각형(x0,y0,x1,y1), 종류
 ("만리장성(언덕 받침)", (1110, 370, 1520, 670), "랜드마크"),
 ("이화원(연못 받침)", (680, 510, 1160, 910), "랜드마크"),
 ("냐오차오·워터큐브(녹지 받침)", (50, 840, 910, 1320), "랜드마크"),
 ("CCTV 타워", (110, 690, 470, 2020), "랜드마크"),
 ("지하철", (700, 1170, 900, 1330), "탈것"),
 ("국가대극원", (730, 1260, 1170, 1520), "랜드마크"),
 ("왕푸징 패루", (390, 1440, 740, 1920), "랜드마크"),
 ("천단", (700, 1710, 1120, 2120), "랜드마크"),
 ("천안문(녹지 받침)", (1040, 1380, 1490, 1760), "랜드마크"),
 ("자금성 블록", (1030, 860, 2000, 1800), "중심 블록"),
 ("CCTV 본사", (1550, 1590, 1950, 2000), "랜드마크"),
 ("시내버스", (1140, 1810, 1350, 2000), "탈것"),
 ("택시", (1400, 2000, 1580, 2130), "탈것"),
 ("798 예술구", (1100, 2010, 1650, 2380), "랜드마크"),
 ("싼리툰 타이구리", (410, 1930, 760, 2340), "랜드마크"),
 ("고속철", (0, 1980, 420, 2360), "탈것"),
]
res = []; masks = []
for name, (x0, y0, x1, y1), kind in O:
    m = np.zeros((H, W), np.uint8); bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
    rect = (x0, y0, x1 - x0, y1 - y0)
    cv2.grabCut(img, m, rect, bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
    fg = ((m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD)) & (dE_bg > 14)
    fg = cv2.morphologyEx(fg.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lb, st, _ = cv2.connectedComponentsWithStats(fg)
    if n > 1:
        keep = 1 + np.argsort(-st[1:, 4])[:3]; keep = [k for k in keep if st[k, 4] > 0.08 * st[keep[0], 4]]
        fg = np.isin(lb, keep).astype(np.uint8)
    ys, xs = np.where(fg > 0)
    bx0, bx1, by0, by1 = xs.min(), xs.max(), ys.min(), ys.max()
    area_mm2 = fg.sum() * 0.21 * 0.2121
    res.append({"이름": name, "종류": kind, "박스mm": [round(bx0 * .21, 1), round(by0 * .2121, 1), round(bx1 * .21, 1), round(by1 * .2121, 1)],
                "폭mm": round((bx1 - bx0) * .21, 1), "높이mm": round((by1 - by0) * .2121, 1), "면적mm2": round(area_mm2),
                "포스터비%": round(area_mm2 / (420 * 594) * 100, 2), "지도비%": round(area_mm2 / (420 * 413) * 100, 2),
                "중심mm": [round(xs.mean() * .21, 1), round(ys.mean() * .2121, 1)]})
    masks.append(fg)
json.dump(res, open("out/bj_objects.json", "w"), ensure_ascii=False, indent=1)
# 오버레이 그림
pal = [(255, 230, 0), (0, 255, 255), (255, 0, 255), (0, 255, 0), (255, 128, 0), (128, 0, 255), (0, 128, 255), (255, 0, 128)]
vis = img.copy()
for i, fg in enumerate(masks):
    c = np.array(pal[i % len(pal)][::-1]); vis[fg > 0] = (0.45 * vis[fg > 0] + 0.55 * c).astype(np.uint8)
    cnts, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); cv2.drawContours(vis, cnts, -1, (255, 255, 255), 4)
pil = Image.fromarray(cv2.cvtColor(cv2.resize(vis, (1000, 1400)), cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(pil)
fnt = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 20)
for i, r in enumerate(res):
    x, y = r["중심mm"][0] / .21 / 2, r["중심mm"][1] / .2121 / 2
    d.text((x - 30, y - 10), f"{i + 1}", font=ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 30), fill=(255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0))
pil.save("out/bj_objects_overlay.jpg", quality=88)
print("번호 | 이름 | 폭×높이(mm) | 면적(mm²) | 지도 대비 % ")
for i, r in enumerate(res):
    print(f"{i+1:2d} | {r['이름']:16s} | {r['폭mm']:5.1f}×{r['높이mm']:5.1f} | {r['면적mm2']:6d} | {r['지도비%']:5.2f}%")
tot = np.clip(sum(masks), 0, 1).sum() * 0.21 * 0.2121
print(f"오브젝트 합집합 면적 {tot:.0f}mm² = 지도 무대(420×413mm)의 {tot/(420*413)*100:.1f}%, 포스터의 {tot/(420*594)*100:.1f}%")
