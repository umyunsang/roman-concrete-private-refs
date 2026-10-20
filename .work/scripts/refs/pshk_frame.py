"""타이틀·정보 패널·푸터 상자를 내용 화소로 맞춰 잰다 (2026-10-18).

- 씨앗 상자(눈으로 짚은 값)를 pad만큼 넓힌 뒤, 국지 바탕과 색차 18 넘는 화소의 꼭 맞는 상자를 구한다.
- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- 사용: uv run --no-project --with opencv-python-headless --with numpy --with pillow python -I pshk_frame.py
"""
import json

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from pshk_common import FONT, WORK, area_pct, content_mask, mm, norm, poster, snap_bbox

SEEDS = {
    "203x-paris": [
        ("타이틀 록업(아르누보 메트로 아치)", "title", (262, 30, 740, 275), 4),
        ("CITY INFORMATION 도시 정보", "panel", (45, 45, 250, 168), 6),
        ("CITY SYMBOL 도시 상징", "panel", (45, 180, 250, 312), 6),
        ("ARTIST IN PARIS 파리의 예술가", "panel", (45, 325, 250, 450), 6),
        ("HISTORY 역사", "panel", (750, 45, 965, 172), 6),
        ("FAMOUS BREAD 유명한 빵", "panel", (750, 180, 965, 362), 6),
        ("BRIDGES OF SEINE RIVER 센강 다리", "panel", (45, 1160, 360, 1336), 4),
        ("푸터", "footer", (40, 1342, 960, 1372), 4),
    ],
    "203x-shanghai": [
        ("타이틀 록업(네온 간판)", "title", (262, 15, 750, 245), 4),
        ("CITY INFORMATION 도시 정보", "panel", (45, 65, 250, 195), 6),
        ("FAMOUS CULTURE AREA 문화지역", "panel", (45, 205, 250, 385), 2),
        ("CITY SYMBOLS 도시 상징물", "panel", (45, 398, 250, 475), 2),
        ("HISTORY 역사", "panel", (760, 70, 960, 262), 2),
        ("TOP 4 SKYSCRAPERS 상하이 마천루 TOP 4", "panel", (45, 1205, 300, 1335), 2),
        ("FAMOUS FOOD 유명한 음식", "panel", (310, 1205, 525, 1338), 4),
        ("BRIDGES OF HUANGPU RIVER 황푸강 교량들", "panel", (540, 1208, 968, 1346), 0),
        ("푸터", "footer", (30, 1340, 965, 1375), 3),
    ],
    "203x-hongkong": [
        ("타이틀 록업(네온 간판·등롱)", "title", (270, 0, 735, 222), 3),
        ("CITY INFORMATION 도시 정보", "panel", (45, 48, 248, 165), 2),
        ("FAMOUS CULTURE AREA 문화지역", "panel", (48, 185, 245, 325), 2),
        ("HISTORY 역사", "panel", (750, 45, 950, 252), 3),
        ("TOP 5 SKYSCRAPERS 홍콩 마천루 TOP 5", "panel", (60, 1203, 305, 1332), 2),
        ("FAMOUS FOOD 유명한 음식", "panel", (385, 1200, 625, 1340), 4),
        ("HONG KONG TAXI 홍콩 택시", "panel", (650, 1200, 962, 1326), 4),
        ("푸터", "footer", (25, 1342, 975, 1372), 3),
    ],
}


def main():
    res = {}
    for rid, seeds in SEEDS.items():
        img = poster(rid)
        m, _ = content_mask(img, 41, 18.0)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        rows = []
        for name, kind, seed, pad in seeds:
            b = snap_bbox(m, seed, pad=pad, min_px=4)
            rows.append({"name": name, "kind": kind, "seed": list(seed), "px": b, "norm": norm(b), "mm": mm(b),
                         "w_mm": round((b[2] - b[0]) * 0.42, 1), "h_mm": round((b[3] - b[1]) * 0.424286, 1),
                         "area_pct": area_pct(b)})
        res[rid] = rows
        # 확인 그림
        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(pil)
        f = ImageFont.truetype(FONT, 14)
        for r in rows:
            c = {"title": (255, 210, 0), "panel": (0, 230, 255), "footer": (255, 120, 0)}[r["kind"]]
            d.rectangle(r["px"], outline=c, width=2)
            d.rectangle(r["seed"], outline=(255, 0, 255), width=1)
            d.text((r["px"][0] + 2, r["px"][3] + 1), r["name"][:18], font=f, fill=c)
        pil.save(f"{WORK}/{rid}_frame_check.png")
    json.dump(res, open(f"{WORK}/frame.json", "w"), ensure_ascii=False, indent=1)
    for rid, rows in res.items():
        print("==", rid)
        for r in rows:
            print(f"  {r['kind']:6s} {r['name'][:34]:34s} px{r['px']} mm{r['mm']} {r['w_mm']}x{r['h_mm']}mm {r['area_pct']}%")
        pan = [r for r in rows if r["kind"] == "panel"]
        print(f"  패널 {len(pan)}개, 패널 상자 면적 합 {sum(r['area_pct'] for r in pan):.1f}%")


if __name__ == "__main__":
    main()
