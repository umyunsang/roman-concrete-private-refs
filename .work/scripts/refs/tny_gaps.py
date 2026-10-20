# -*- coding: utf-8 -*-
"""랜드마크 최근접 이웃 간격(화소 기준·상자 기준, mm). 라벨 없는 풍경 판은 제외."""
import json, os, sys
import cv2, numpy as np
OUT = "/Users/um-yunsang/roman-concrete-private-refs/.work/out/refs-analysis"
ref = sys.argv[1]
obj = json.load(open(os.path.join(OUT, f"{ref}_objects.json"), encoding="utf-8"))
M = np.load(os.path.join(OUT, f"{ref}_lm_masks.npz"))
names = [n for n, v in obj["landmarks"].items() if v["bbox_art"] and v.get("label", True) is not False and v["area_mm2"] > 50]
dts = {}
for n in names:
    m = M[n.replace("/", "_")].astype(np.uint8)
    dts[n] = cv2.distanceTransform(1 - m, cv2.DIST_L2, 5)
px_gap, box_gap = {}, {}
for a in names:
    ma = M[a.replace("/", "_")]
    best, bestn = 1e9, None
    for b in names:
        if a == b: continue
        d = float(dts[b][ma].min()) if ma.any() else 1e9
        if d < best: best, bestn = d, b
    px_gap[a] = (round(best * 0.21, 1), bestn)
    A = obj["landmarks"][a]["bbox_art"]; bb = 1e9
    for b in names:
        if a == b: continue
        B = obj["landmarks"][b]["bbox_art"]
        dx = max(0, max(A[0], B[0]) - min(A[2], B[2])); dy = max(0, max(A[1], B[1]) - min(A[3], B[3]))
        bb = min(bb, (dx * dx + dy * dy) ** 0.5)
    box_gap[a] = round(bb * 0.21, 1)
pg = np.array([v[0] for v in px_gap.values()]); bg = np.array(list(box_gap.values()))
print(ref, "n", len(names), "화소 간격 mm 중앙값", float(np.median(pg)), "사분위", np.percentile(pg, [25, 75]).round(1).tolist(),
      "| 상자 간격 중앙값", float(np.median(bg)), "상자 겹침(0) 비율", round(float((bg == 0).mean()), 2))
for k, v in sorted(px_gap.items(), key=lambda t: -t[1][0])[:6]:
    print("   먼 쪽:", k, v)
json.dump({"pixel_gap_mm": px_gap, "box_gap_mm": box_gap, "median_pixel_gap_mm": float(np.median(pg)), "median_box_gap_mm": float(np.median(bg))},
          open(os.path.join(OUT, f"{ref}_gaps.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
