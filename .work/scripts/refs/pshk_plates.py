"""녹지 판(받침)·지면 판을 색으로 분할하고, 연결 성분별 다각형 꼭짓점을 근사해 출력한다 (2026-10-18).

- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- 사용: uv run --no-project --with opencv-python-headless --with numpy python -I pshk_plates.py <ref_id>
"""
import json
import sys

import cv2
import numpy as np

from pshk_common import WORK, lab, poster

# Lab(OpenCV 8비트) 범위: L, a, b
RULES = {
    "203x-paris": {"green": ((120, 255), (90, 122), (138, 175))},
    "203x-shanghai": {"green": ((120, 255), (80, 115), (140, 190)), "water": ((170, 225), (105, 125), (100, 122))},
    "203x-hongkong": {"green": ((120, 210), (90, 118), (140, 180)), "ground": ((85, 150), (122, 134), (130, 145))},
}


def main():
    rid = sys.argv[1]
    img = poster(rid)
    L = lab(img)
    out = {}
    vis = img.copy()
    pal = [(0, 255, 255), (255, 0, 255), (0, 128, 255), (255, 255, 0), (0, 255, 0), (255, 128, 0)]
    for ci, (cls, ((l0, l1), (a0, a1), (b0, b1))) in enumerate(RULES[rid].items()):
        m = ((L[..., 0] >= l0) & (L[..., 0] <= l1) & (L[..., 1] >= a0) & (L[..., 1] <= a1) & (L[..., 2] >= b0) & (L[..., 2] <= b1)).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        cv2.imwrite(f"{WORK}/{rid}_{cls}_mask.png", m * 255)
        n, lb, st, cen = cv2.connectedComponentsWithStats(m)
        comps = []
        for i in np.argsort(-st[1:, 4])[:14] + 1:
            if st[i, 4] < 600:
                continue
            cm = (lb == i).astype(np.uint8)
            cnts, _ = cv2.findContours(cm, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            c = max(cnts, key=cv2.contourArea)
            ap = cv2.approxPolyDP(c, 4.0, True).reshape(-1, 2)
            hull = cv2.convexHull(c)
            x, y, w, h = cv2.boundingRect(c)
            comps.append({"area_px": int(st[i, 4]), "bbox": [int(x), int(y), int(x + w), int(y + h)],
                          "centroid": [round(float(cen[i][0]), 1), round(float(cen[i][1]), 1)],
                          "hull_area_px": int(cv2.contourArea(hull)), "poly": ap.tolist()})
            cv2.drawContours(vis, [c], -1, pal[ci % len(pal)], 2)
        out[cls] = {"total_px": int(m.sum()), "pct_poster": round(float(m.mean() * 100), 2), "components": comps}
    cv2.imwrite(f"{WORK}/{rid}_plates_check.png", vis)
    json.dump(out, open(f"{WORK}/{rid}_plates.json", "w"), ensure_ascii=False, indent=1)
    for cls, v in out.items():
        print(f"== {rid} {cls}: {v['pct_poster']}% of poster")
        for c in v["components"]:
            poly = " ".join(f"({p[0]},{p[1]})" for p in c["poly"][:14])
            print(f"   area {c['area_px']:6d} bbox {c['bbox']} cen {c['centroid']} poly[{len(c['poly'])}] {poly}")


if __name__ == "__main__":
    main()
