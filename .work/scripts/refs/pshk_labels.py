"""지도 위 라벨의 글줄 기울기·크기를 재고, 판독용 모음 그림을 만든다 (2026-10-18).

- 글줄 기울기: 라벨 상자 안 내용 화소(국지 바탕과 색차 22 초과)를 -45~45°로 0.5°씩 돌려 가며
  가로 투영 분산이 가장 큰 각을 찾는다. 화면 기준, 오른쪽 위로 오르면 +.
- 고해상도 타일이 덮는 라벨은 2배 합성본에서 잰다(더 정확).
- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- 사용: uv run --no-project --with opencv-python-headless --with numpy --with pillow python -I pshk_labels.py <ref_id>
"""
import json
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from pshk_common import FONT, MMX, MMY, WORK, composite2x

LABELS = {
    "203x-paris": [
        ("Sacré-Cœur 사크레쾨르 대성당", (160, 495, 266, 576)), ("Palais Garnier 오페라 가르니에", (276, 430, 342, 502)),
        ("Jardin des Tuileries 튈르리 가든", (436, 500, 501, 602)), ("Place de la Concorde 콩코르드 광장", (275, 680, 337, 748)),
        ("Centre Georges-Pompidou 퐁피두 센터", (663, 296, 742, 402)), ("Cathédrale Notre-Dame 노트르담 대성당", (758, 408, 852, 512)),
        ("Musée du Louvre 루브르 박물관", (668, 503, 745, 602)), ("la Seine 센강", (616, 758, 657, 802)),
        ("Musée d'Orsay 오르세 미술관", (608, 778, 692, 872)), ("Musée Rodin 로댕 미술관", (858, 783, 972, 887)),
        ("Arc de Triomphe 에투알 개선문", (163, 1038, 237, 1137)), ("Métro entrée 파리 지하철 입구", (273, 893, 332, 947)),
        ("Tour Eiffel 에펠탑", (613, 1088, 707, 1207)), ("RER 고속 교외 철도", (888, 1088, 952, 1162)),
        ("Métro de Paris 파리 지하철", (888, 1138, 952, 1207)),
    ],
    "203x-shanghai": [
        ("Oriental Pearl 동방명주", (453, 263, 537, 377)), ("Jinmao Tower 진마오 타워", (596, 260, 657, 347)),
        ("SWFC 세계금융센터", (791, 283, 867, 387)), ("Yangshupu Waterworks 양수푸 상수도", (238, 338, 302, 437)),
        ("Rockbund Art Museum 록번드 미술관", (46, 598, 132, 702)), ("Sassoon Building 사순 빌딩", (46, 733, 102, 782)),
        ("Bank Of China 중국은행", (46, 763, 107, 822)), ("Huangpu River 황푸강", (408, 628, 482, 672)),
        ("Shanghai Tower 상하이 타워", (623, 733, 697, 862)), ("Aurora Art Museum 오로라 미술관", (698, 808, 777, 907)),
        ("China Art Palace 중국 미술관", (908, 748, 982, 852)), ("Cruise 크루즈", (458, 828, 547, 902)),
        ("Metro 지하철", (528, 868, 592, 947)), ("City Bus 시내버스", (46, 893, 107, 987)),
        ("Shanghai Club Building 상하이 총회", (308, 988, 377, 1062)), ("Shanghai Custom House 강해관", (403, 1033, 452, 1097)),
        ("HSBC Bank Building HSBC 빌딩", (450, 1073, 522, 1137)), ("Asia Building 아시아 빌딩", (556, 1123, 617, 1187)),
        ("Yu Garden 예원", (48, 1093, 132, 1197)), ("Nanpu Bridge 난푸대교", (713, 1093, 772, 1172)),
        ("Taxi 택시", (806, 1028, 847, 1097)),
    ],
    "203x-hongkong": [
        ("ICC 국제상업센터", (63, 418, 147, 502)), ("Central Plaza 센트럴 프라자", (168, 348, 237, 432)),
        ("Lippo Centre Tower 리포센터", (373, 228, 457, 322)), ("Bank of China Tower 중국은행 타워", (553, 293, 617, 362)),
        ("Peak Tower 피크타워", (596, 233, 657, 282)), ("Museum of Medical Sciences 의학박물관", (603, 348, 692, 412)),
        ("The Center 더센터", (826, 278, 882, 347)), ("Two IFC 국제금융센터", (903, 308, 977, 402)),
        ("Convention Centre 컨벤션 센터", (458, 543, 542, 612)), ("Observation Wheel 대관람차", (620, 573, 702, 652)),
        ("Maritime Museum 해사 박물관", (763, 723, 842, 792)), ("Space Museum 우주박물관", (250, 748, 317, 812)),
        ("Cultural Centre 문화센터", (248, 1008, 317, 1072)), ("Tsim Sha Tsui 침사추이종루", (248, 1058, 332, 1142)),
        ("Ferry 페리", (518, 1108, 567, 1172)), ("MTR 지하철", (583, 1128, 652, 1192)),
    ],
}


def text_mask(crop):
    bg = cv2.medianBlur(crop, 31)
    L1 = cv2.cvtColor(crop, cv2.COLOR_BGR2LAB).astype(np.float32)
    L0 = cv2.cvtColor(bg, cv2.COLOR_BGR2LAB).astype(np.float32)
    d = np.sqrt(((L1 - L0) ** 2).sum(-1))
    return (d > 22).astype(np.uint8)


def baseline_angle(m):
    h, w = m.shape
    best = (-1, 0.0)
    c = (w / 2, h / 2)
    for a in np.arange(-45, 45.01, 0.5):
        R = cv2.getRotationMatrix2D(c, -a, 1.0)  # +a(오른쪽 위로 오르는 글줄)를 수평으로 눕힌다
        r = cv2.warpAffine(m.astype(np.float32), R, (w, h), flags=cv2.INTER_LINEAR)
        prof = r.sum(1)
        v = float(np.var(prof))
        if v > best[0]:
            best = (v, float(a))
    return best[1]


def main():
    rid = sys.argv[1]
    big, cov = composite2x(rid)
    rows = []
    tiles = []
    f = ImageFont.truetype(FONT, 22)
    for i, (name, (x0, y0, x1, y1)) in enumerate(LABELS[rid]):
        X0, Y0, X1, Y1 = 2 * x0, 2 * y0, 2 * x1, 2 * y1
        crop = big[Y0:Y1, X0:X1]
        m = text_mask(crop)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        ang = baseline_angle(m)
        ys, xs = np.where(m > 0)
        tb = [x0 + xs.min() / 2, y0 + ys.min() / 2, x0 + (xs.max() + 1) / 2, y0 + (ys.max() + 1) / 2] if len(xs) else None
        hires = bool(cov[Y0:Y1, X0:X1].mean() > 0.5)
        rows.append({"name": name, "seed": [x0, y0, x1, y1], "text_bbox": [round(v, 1) for v in tb] if tb else None,
                     "w_mm": round((tb[2] - tb[0]) * MMX, 1) if tb else None, "h_mm": round((tb[3] - tb[1]) * MMY, 1) if tb else None,
                     "baseline_deg": ang, "hires_tile": hires})
        # 판독용: 라벨 둘레(아래 60·옆 30)까지 넓혀 지시선이 보이게 한다
        ex = big[max(0, Y0 - 40):min(2800, Y1 + 120), max(0, X0 - 60):min(2000, X1 + 60)].copy()
        pil = Image.fromarray(cv2.cvtColor(ex, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(pil)
        d.text((4, 2), f"{i + 1} {ang:+.1f}°", font=f, fill=(255, 255, 0), stroke_width=3, stroke_fill=(0, 0, 0))
        tiles.append(pil)
    json.dump(rows, open(f"{WORK}/{rid}_labels.json", "w"), ensure_ascii=False, indent=1)
    # 모음 그림(한 줄 4칸)
    cw, ch = 330, 330
    n = len(tiles)
    cols = 4
    sheet = Image.new("RGB", (cols * cw, ((n + cols - 1) // cols) * ch), (40, 40, 40))
    for i, t in enumerate(tiles):
        t.thumbnail((cw - 6, ch - 6))
        sheet.paste(t, ((i % cols) * cw + 3, (i // cols) * ch + 3))
    sheet.save(f"{WORK}/{rid}_labels_sheet.png")
    for i, r in enumerate(rows):
        print(f"{i + 1:2d} {r['name'][:34]:34s} 기울기 {r['baseline_deg']:+5.1f}°  글 상자 {r['text_bbox']}  {r['w_mm']}x{r['h_mm']}mm  {'타일' if r['hires_tile'] else '확대'}")


if __name__ == "__main__":
    main()
