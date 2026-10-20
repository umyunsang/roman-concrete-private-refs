"""지도 무대·밀도·코어 군·히어로·강 통계(정규 1000x1400 단위, A2 mm 환산 포함).
코어 군 덩어리 = 닫힘(코어 오브젝트 전경 ∪ 코어 구간 물 면, 21단위) + 구멍 메움.
"""
import json, sys
import cv2, numpy as np
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from ra_common import *
from ra_objects_def import OBJS

MMX, MMY = 420 / 1000, 594 / 1400
INK = json.load(open(WORK / "ink.json"))
# 지도 무대 M: 전폭 x 0~1000, y = 타이틀 잉크 아래 변 ~ 하단 패널 띠 위 변(하단 띠가 없으면 푸터 위 변)
MSTAGE = {"203x-seoul": (0, 251, 1000, 1177), "203x-london": (0, 198, 1000, 1208), "203x-berlin": (0, 217, 1000, 1342)}
# 물 마스크와 코어 구간 물 성분 id
WATER = {
 "203x-seoul": {"river": ("creek", None), "sea": ("hangang", [50])},
 "203x-london": {"river": ("thames", [28, 37, 18, 14, 24, 25])},
 "203x-berlin": {"river": ("spree", [24, 20, 22, 13, 11, 3, 8, 17])},
}
SKY_IDS = {"203x-seoul": [15, 18, 19, 20, 84, 62, 92]}   # 청계천 색과 같은 하늘 조각(판 바깥)·P6 패널 지도 조각

def mm_box(b):
    x0, y0, x1, y1 = b
    return [round(x0 * MMX, 1), round(y0 * MMY, 1), round(x1 * MMX, 1), round(y1 * MMY, 1)]

out = {}
for ref in OBJS:
    fg = cv2.imread(str(WORK / f"fg_{ref}.png"), 0) > 0
    H, W = fg.shape
    mx0, my0, mx1, my1 = MSTAGE[ref]
    Mmask = np.zeros_like(fg); Mmask[my0:my1, mx0:mx1] = True
    Marea = (mx1 - mx0) * (my1 - my0)
    # 강 마스크
    wname, wids = WATER[ref]["river"]
    lb = np.load(WORK / f"water_{ref}_{wname}_labels.npy")
    if wids is None:
        comps = json.load(open(WORK / f"water_{ref}_{wname}.json"))
        wids = [c["id"] for c in comps if c["id"] not in SKY_IDS.get(ref, [])]
    river = np.isin(lb, wids)
    # 코어 군
    core_objs = [o for o in OBJS[ref] if o[3]]
    rect_union = np.zeros_like(fg)
    for name, kind, (x0, y0, x1, y1), core in core_objs:
        rect_union[max(0, y0):y1, max(0, x0):x1] = True
    core_fg = fg & rect_union
    # 코어 구간 물: 코어 상자 합집합의 볼록 껍질 안 물
    ys, xs = np.nonzero(rect_union)
    hull = cv2.convexHull(np.stack([xs, ys], 1).astype(np.int32))
    hullm = np.zeros(fg.shape, np.uint8); cv2.fillPoly(hullm, [hull], 1)
    core_water = river & (hullm > 0)
    mass = (core_fg | core_water).astype(np.uint8)
    k = 21
    mass = cv2.morphologyEx(mass, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    # 구멍 메움
    ff = mass.copy(); h2, w2 = ff.shape
    flood = np.zeros((h2 + 2, w2 + 2), np.uint8)
    inv = (1 - ff).astype(np.uint8)
    cv2.floodFill(inv, flood, (0, 0), 0)
    mass = (mass | inv).astype(np.uint8)
    n, lbm, st, _ = cv2.connectedComponentsWithStats(mass)
    if n > 2:  # 가장 큰 덩어리 + 그와 맞닿는 것만
        big = np.argmax(st[1:, cv2.CC_STAT_AREA]) + 1
        mass = (lbm == big).astype(np.uint8)
    mass_in_M = mass.astype(bool) & Mmask
    ys, xs = np.nonzero(mass)
    mbb = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    cnts, _ = cv2.findContours(mass, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnt = max(cnts, key=cv2.contourArea)
    chull = cv2.convexHull(cnt)
    poly = cv2.approxPolyDP(cnt, 6, True).reshape(-1, 2).tolist()
    m = cv2.moments(mass, True)
    cx, cy = m["m10"] / m["m00"], m["m01"] / m["m00"]
    obb_area = (mbb[2] - mbb[0]) * (mbb[3] - mbb[1])
    # 코어 상자 합집합의 바깥 상자(오브젝트 상자 기준, 와이어프레임 '상자' 정의와 같음)
    cb = [min(o[2][0] for o in core_objs), min(o[2][1] for o in core_objs), max(o[2][2] for o in core_objs), max(o[2][3] for o in core_objs)]
    cb_area = (cb[2] - cb[0]) * (cb[3] - cb[1])
    # 모든 오브젝트 밀도
    dens = (fg & Mmask).sum() / Marea * 100
    res = {
     "map_stage_u": [mx0, my0, mx1, my1], "map_stage_mm": mm_box([mx0, my0, mx1, my1]),
     "map_stage_pct_of_poster_area": round(Marea / (1000 * 1400) * 100, 1),
     "map_stage_height_pct": round((my1 - my0) / 1400 * 100, 1),
     "fg_elements_y_extent_u": [int(np.nonzero(fg.any(1))[0].min()), int(np.nonzero(fg.any(1))[0].max())],
     "object_density_pct_of_M": round(float(dens), 1),
     "object_union_pct_of_poster": round(float(fg.sum() / (1000 * 1400) * 100), 1),
     "core": {
       "members": [o[0] for o in core_objs],
       "obj_box_union_u": cb, "obj_box_union_mm": mm_box(cb),
       "obj_box_pct_of_M": round(cb_area / Marea * 100, 1), "obj_box_pct_of_poster": round(cb_area / 1.4e6 * 100, 1),
       "mass_area_pct_of_M": round(float(mass_in_M.sum() / Marea * 100), 1),
       "mass_area_pct_of_poster": round(float(mass.sum() / 1.4e6 * 100), 1),
       "mass_bbox_u": mbb, "mass_bbox_mm": mm_box(mbb), "mass_bbox_pct_of_M": round(obb_area / Marea * 100, 1),
       "mass_fill_of_bbox_pct": round(float(mass.sum() / obb_area * 100), 1),
       "silhouette_pct_of_M": round(float((core_fg & Mmask).sum() / Marea * 100), 1),
       "core_water_px": int(core_water.sum()), "core_water_pct_of_M": round(float(core_water.sum() / Marea * 100), 2),
       "convex_hull_pct_of_M": round(float(cv2.contourArea(chull) / Marea * 100), 1),
       "centroid_u": [round(cx), round(cy)], "centroid_norm": [round(cx / 1000, 3), round(cy / 1400, 3)],
       "polygon_u": poly,
       "core_share_of_all_objects_pct": round(float(core_fg.sum() / fg.sum() * 100), 1),
     },
     "river_visible_px": int(river.sum()), "river_visible_pct_of_M": round(float((river & Mmask).sum() / Marea * 100), 2),
    }
    if "sea" in WATER[ref]:
        sname, sids = WATER[ref]["sea"]
        lbs = np.load(WORK / f"water_{ref}_{sname}_labels.npy")
        sea = np.isin(lbs, sids)
        ys, xs = np.nonzero(sea)
        res["sea"] = {"bbox_u": [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1],
                      "area_pct_of_poster": round(float(sea.sum() / 1.4e6 * 100), 1),
                      "area_in_M_pct": round(float((sea & Mmask).sum() / Marea * 100), 1)}
    out[ref] = res
    cv2.imwrite(str(WORK / f"coremass_{ref}.png"), mass * 255)
    np.save(WORK / f"river_{ref}.npy", river)
    print(ref, json.dumps({k: v for k, v in res.items() if k != "core"}, ensure_ascii=False))
    print("   core", json.dumps({k: v for k, v in res["core"].items() if k != "polygon_u"}, ensure_ascii=False))
json.dump(out, open(WORK / "stats.json", "w"), ensure_ascii=False, indent=1)
