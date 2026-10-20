"""패널 상자 대비 랜드마크 상자 비, 히어로 실루엣 면적 등 요약 수치. 분석 산출물만 읽는다. (2026-10-18)"""
import json
import statistics as st
import cv2
import numpy as np
from pshk_common import WORK, MMX, MMY
from pshk_zones import CFG, poly_mask
frame = json.load(open(f"{WORK}/frame.json"))
out = {}
for rid in ["203x-paris", "203x-shanghai", "203x-hongkong"]:
    z = json.load(open(f"{WORK}/{rid}_zones.json"))
    pan = [r for r in frame[rid] if r["kind"] == "panel"]
    pa = [r["w_mm"] * r["h_mm"] for r in pan]
    lm = [x for x in z["landmarks"] if x["kind"] == "랜드마크"]
    la = [x["w_mm"] * x["h_mm"] for x in lm]
    hb = CFG[rid]["hero"][1]
    o = {"panel_box_mm2_median": round(st.median(pa)), "panel_box_mm2_min": round(min(pa)), "panel_box_mm2_max": round(max(pa)),
         "landmark_box_mm2_median": round(st.median(la)), "landmark_box_mm2_min": round(min(la)), "landmark_box_mm2_max": round(max(la)),
         "ratio_landmark_to_panel_median": round(st.median(la) / st.median(pa), 2),
         "share_landmarks_smaller_than_min_panel": f"{sum(1 for a in la if a < min(pa))}/{len(la)}",
         "hero_box_mm": [round((hb[2] - hb[0]) * MMX, 1), round((hb[3] - hb[1]) * MMY, 1)],
         "hero_h_pct_poster": round((hb[3] - hb[1]) / 14, 1), "hero_cx_pct": round((hb[0] + hb[2]) / 20, 1)}
    if CFG[rid].get("hero_poly"):
        m = poly_mask([CFG[rid]["hero_poly"]])
        o["hero_silhouette_mm2"] = round(float(m.sum()) * MMX * MMY)
    out[rid] = o
    print(rid, json.dumps(o, ensure_ascii=False))
json.dump(out, open(f"{WORK}/ratios.json", "w"), ensure_ascii=False, indent=1)
