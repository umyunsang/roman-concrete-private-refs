"""포스터 팔레트를 Lab k-평균으로 나누고, 군집 지도를 그려 화소 분류의 출발점으로 쓴다 (2026-10-18).

- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- 사용: uv run --no-project --with opencv-python-headless --with numpy --with pillow python -I palette_ref.py <out_dir>
"""
import json
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE = "/Users/um-yunsang/roman-concrete-private-refs/.work/dl/refs-cities"
POSTERS = {
    "203x-paris": "203x-paris/StH_2021_04_Poster_Paris2.jpg",
    "203x-shanghai": "203x-shanghai/shanghai_poster.jpg",
    "203x-hongkong": "203x-hongkong/StH_2022_04_Tokyo.jpg",
}
K = 14
FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"


def main():
    out_dir = sys.argv[1]
    res = {}
    for rid, rel in POSTERS.items():
        img = cv2.imread(f"{BASE}/{rel}")
        H, W = img.shape[:2]
        blur = cv2.GaussianBlur(img, (3, 3), 0)
        lab = cv2.cvtColor(blur, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
        crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.5)
        cv2.setRNGSeed(7)
        _, lbl, cen = cv2.kmeans(lab, K, None, crit, 3, cv2.KMEANS_PP_CENTERS)
        lbl = lbl.reshape(H, W)
        cen_bgr = cv2.cvtColor(cen.reshape(1, -1, 3).astype(np.uint8), cv2.COLOR_LAB2BGR).reshape(-1, 3)
        order = np.argsort(-np.bincount(lbl.ravel(), minlength=K))
        rows = []
        for k in order:
            m = lbl == k
            ys, xs = np.where(m)
            b, g, r = [int(v) for v in cen_bgr[k]]
            rows.append({"k": int(k), "hex": f"#{r:02x}{g:02x}{b:02x}", "pct": round(float(m.mean() * 100), 2),
                         "lab": [round(float(v), 1) for v in cen[k]],
                         "y_p10_p90": [int(np.percentile(ys, 10)), int(np.percentile(ys, 90))],
                         "x_p10_p90": [int(np.percentile(xs, 10)), int(np.percentile(xs, 90))]})
        res[rid] = rows
        np.save(f"{out_dir}/{rid}_kmeans_lbl.npy", lbl.astype(np.uint8))
        # 군집 지도: 군집마다 대표색으로 칠하고 번호 범례를 붙인다
        vis = cen_bgr[lbl]
        pil = Image.fromarray(cv2.cvtColor(vis, cv2.COLOR_BGR2RGB))
        canvas = Image.new("RGB", (W + 260, H), (255, 255, 255))
        canvas.paste(pil, (0, 0))
        d = ImageDraw.Draw(canvas)
        f = ImageFont.truetype(FONT, 18)
        for i, r in enumerate(rows):
            y = 20 + i * 40
            c = tuple(int(r["hex"][j:j + 2], 16) for j in (1, 3, 5))
            d.rectangle([W + 10, y, W + 50, y + 30], fill=c, outline=(0, 0, 0))
            d.text((W + 58, y + 4), f"k{r['k']} {r['hex']} {r['pct']}%", font=f, fill=(0, 0, 0))
        canvas.save(f"{out_dir}/{rid}_kmeans.png")
    json.dump(res, open(f"{out_dir}/palette.json", "w"), ensure_ascii=False, indent=1)
    for rid, rows in res.items():
        print("==", rid)
        for r in rows:
            print(f"  k{r['k']:2d} {r['hex']} {r['pct']:6.2f}%  Lab{r['lab']}  y10-90 {r['y_p10_p90']}  x10-90 {r['x_p10_p90']}")


if __name__ == "__main__":
    main()
