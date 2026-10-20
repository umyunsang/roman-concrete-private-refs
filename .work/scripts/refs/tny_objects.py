# -*- coding: utf-8 -*-
"""오브젝트 분할과 코어 군·밀도 실측.

방법(도쿄):
  1) classmap.py 라벨에서 오브젝트 후보 = OBJ ∪ (크기가 큰 TEXT 색 성분: 붉은 오브젝트) ∪ (지정한 물 판: 해자 등)
     - 지도 위 라벨 글자(붉은 갈색 가는 획)는 '작은 TEXT 성분'으로 보고 뺀다(면적 < TEXT_MIN).
     - 길(ROAD)·강(WATER)은 오브젝트가 아니다(베이징 3.5절과 같은 기준: 받침은 포함, 길·강·라벨은 제외).
  2) 랜드마크 = 씨앗 점이 닿는 연결 성분의 합(필요하면 자르기 상자 clip 안으로 한정).
  3) 코어 군 = 지정한 랜드마크들의 합집합 + (선택) 강 구간, 덩어리 외곽 = 닫힘 연산(반지름 R) 후 구멍 메움.
결과: <ref>_objects.json, <ref>_objects_vis.png
명령: python -I tny_objects.py <ref>
"""
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/refs")
from tny_refdefs import DEFS  # noqa: E402

ROOT = "/Users/um-yunsang/roman-concrete-private-refs"
OUT = os.path.join(ROOT, ".work/out/refs-analysis")
BG, ROAD, WATER, TEXT, OBJ, GROUND, SKY = 0, 1, 2, 3, 4, 5, 6
MMX, MMY = 420 / 2000, 594 / 2800


def poly_mask(shape, pts):
    m = np.zeros(shape, np.uint8)
    cv2.fillPoly(m, [np.array(pts, np.int32)], 1)
    return m.astype(bool)


def rect_mask(shape, r):
    m = np.zeros(shape, bool)
    x0, y0, x1, y1 = r
    m[max(0, y0):y1, max(0, x0):x1] = True
    return m


def bbox_of(m):
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def object_candidates(ref, cls, D):
    H, W = cls.shape
    text = (cls == TEXT).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(text, 8)
    big = np.zeros(n, bool)
    big[1:] = st[1:, cv2.CC_STAT_AREA] >= D.get("text_min", 900)
    obj = (cls == OBJ) | big[lab]
    for r in D.get("water_as_object", []):  # 해자·연못 등 물 받침
        obj |= rect_mask((H, W), r) & (cls == WATER)
    for r in D.get("ground_as_object", []):
        obj |= rect_mask((H, W), r) & (cls == GROUND)
    for r in D.get("exclude_rects", []):  # 패널·타이틀·푸터 등 지도 밖 요소
        obj &= ~rect_mask((H, W), r)
    for p in D.get("exclude_polys", []):
        obj &= ~poly_mask((H, W), p)
    # 얇은 연결(길 가장자리 선·지시선)을 끊는다
    k = D.get("open_k", 3)
    if k > 1:
        obj = cv2.morphologyEx(obj.astype(np.uint8), cv2.MORPH_OPEN, np.ones((k, k), np.uint8)).astype(bool)
    smax = D.get("small_obj_max", 0)
    if smax:
        n2, lab2, st2, _ = cv2.connectedComponentsWithStats(obj.astype(np.uint8), 8)
        keep2 = np.zeros(n2, bool)
        keep2[1:] = st2[1:, cv2.CC_STAT_AREA] > smax
        obj = keep2[lab2]
    return obj


def main(ref):
    D = DEFS[ref]
    cls = np.load(os.path.join(OUT, f"{ref}_class.npy"))
    H, W = cls.shape
    art = cv2.imread(os.path.join(OUT, f"{ref}_art.png"))
    obj = object_candidates(ref, cls, D)
    n, lab, st, _ = cv2.connectedComponentsWithStats(obj.astype(np.uint8), 8)
    stage = D["map_stage"]
    stage_m = rect_mask((H, W), stage)
    stage_area = stage_m.sum()
    res = {"ref": ref, "map_stage_art": stage, "map_stage_area_px": int(stage_area),
           "map_stage_mm": [round(stage[0] * MMX, 1), round(stage[1] * MMY, 1), round(stage[2] * MMX, 1), round(stage[3] * MMY, 1)],
           "landmarks": {}}
    used = np.zeros(n, bool)
    lm_masks = {}
    excl = np.zeros((H, W), bool)
    for r in D.get("exclude_rects", []):
        excl |= rect_mask((H, W), r)
    gc = None
    if D.get("use_grabcut"):
        gc = np.load(os.path.join(OUT, f"{ref}_gc_masks.npz"))
    for name, spec in D["landmarks"].items():
        if gc is not None and name in gc.files:
            m = gc[name] & ~excl
            lm_masks[name] = m
            bb = bbox_of(m)
            area = int(m.sum())
            res["landmarks"][name] = {
                "tier": spec.get("tier", ""), "label": spec.get("label", True), "method": "GrabCut" if not spec.get("fill_clip") else "poly∩비지면",
                "bbox_art": bb,
                "bbox_norm": [round(bb[0] / W, 4), round(bb[1] / H, 4), round(bb[2] / W, 4), round(bb[3] / H, 4)] if bb else None,
                "wh_mm": [round((bb[2] - bb[0]) * MMX, 1), round((bb[3] - bb[1]) * MMY, 1)] if bb else None,
                "area_mm2": round(area * MMX * MMY, 0),
                "pct_of_map_stage": round(100.0 * area / stage_area, 2),
                "n_components": 0,
            }
            continue
        m = np.zeros((H, W), bool)
        clip = rect_mask((H, W), spec["clip"]) if "clip" in spec else None
        if "poly" in spec:
            pm = poly_mask((H, W), spec["poly"])
            clip = pm if clip is None else (clip & pm)
        ids = set()
        for (sx, sy) in spec.get("seeds", []):
            # 씨앗 주변 7px 안에서 가장 가까운 성분
            best = 0
            for r in range(0, 8):
                win = lab[max(0, sy - r):sy + r + 1, max(0, sx - r):sx + r + 1]
                v = win[win > 0]
                if len(v):
                    best = int(np.bincount(v).argmax())
                    break
            if best:
                ids.add(best)
        for i in ids:
            m |= lab == i
            used[i] = True
        if spec.get("fill_clip") and clip is not None:
            # 격자 구조(탑·관람차·다리): 자르기 영역 안의 오브젝트 화소 전부
            m |= obj & clip
        if spec.get("road_as_object") and clip is not None:
            # 다리 상판처럼 길 색인 오브젝트 부분
            m |= (cls == ROAD) & clip
        if clip is not None:
            m &= clip
        lm_masks[name] = m
        bb = bbox_of(m)
        area = int(m.sum())
        res["landmarks"][name] = {
            "tier": spec.get("tier", ""), "label": spec.get("label", True),
            "bbox_art": bb,
            "bbox_norm": [round(bb[0] / W, 4), round(bb[1] / H, 4), round(bb[2] / W, 4), round(bb[3] / H, 4)] if bb else None,
            "wh_mm": [round((bb[2] - bb[0]) * MMX, 1), round((bb[3] - bb[1]) * MMY, 1)] if bb else None,
            "area_mm2": round(area * MMX * MMY, 0),
            "pct_of_map_stage": round(100.0 * area / stage_area, 2),
            "n_components": len(ids),
        }
    lm_any = np.zeros((H, W), bool)
    for m in lm_masks.values():
        lm_any |= m
    allobj = (obj | lm_any) & stage_m
    res["objects_union_pct_of_map_stage"] = round(100.0 * allobj.sum() / stage_area, 1)
    lm_union = np.zeros((H, W), bool)
    for m in lm_masks.values():
        lm_union |= m
    res["landmarks_union_pct_of_map_stage"] = round(100.0 * (lm_union & stage_m).sum() / stage_area, 1)
    res["road_pct_of_map_stage"] = round(100.0 * ((cls == ROAD) & stage_m).sum() / stage_area, 1)
    res["water_pct_of_map_stage"] = round(100.0 * ((cls == WATER) & stage_m & ~lm_union).sum() / stage_area, 1)
    res["ground_pct_of_map_stage"] = round(100.0 * ((cls == GROUND) & stage_m).sum() / stage_area, 1)

    # 코어 군
    cores = {}
    for cname, cspec in D.get("core_groups", {}).items():
        cm = np.zeros((H, W), bool)
        for nm in cspec["members"]:
            cm |= lm_masks[nm]
        for p in cspec.get("extra_polys", []):  # 강 구간·코어 라벨 등
            pm = poly_mask((H, W), p)
            cm |= pm & (cls != BG)
        R = cspec.get("close_r", 40)
        ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * R + 1, 2 * R + 1))
        mass = cv2.morphologyEx(cm.astype(np.uint8), cv2.MORPH_CLOSE, ker)
        # 구멍 메움
        ff = mass.copy() * 255
        h2, w2 = ff.shape
        mk = np.zeros((h2 + 2, w2 + 2), np.uint8)
        ff2 = ff.copy()
        cv2.floodFill(ff2, mk, (0, 0), 255)
        holes = cv2.bitwise_not(ff2)
        mass = ((ff | holes) > 0)
        # 가장 큰 덩어리 외 작은 조각도 남긴다(합)
        hull_pts = cv2.findNonZero(cm.astype(np.uint8))
        hull = cv2.convexHull(hull_pts)
        hull_m = np.zeros((H, W), np.uint8)
        cv2.fillPoly(hull_m, [hull], 1)
        bb = bbox_of(cm)
        bb_area = (bb[2] - bb[0]) * (bb[3] - bb[1])
        # 구성원 상자 합집합
        boxu = np.zeros((H, W), bool)
        for nm in cspec["members"]:
            b2 = bbox_of(lm_masks[nm])
            if b2:
                boxu |= rect_mask((H, W), b2)
        cores[cname] = {
            "members": cspec["members"], "note": cspec.get("note", ""),
            "bbox_art": bb, "bbox_norm": [round(bb[0] / W, 4), round(bb[1] / H, 4), round(bb[2] / W, 4), round(bb[3] / H, 4)],
            "bbox_mm": [round(bb[0] * MMX, 1), round(bb[1] * MMY, 1), round(bb[2] * MMX, 1), round(bb[3] * MMY, 1)],
            "bbox_pct_of_map_stage": round(100.0 * bb_area / stage_area, 1),
            "member_box_union_pct": round(100.0 * (boxu & stage_m).sum() / stage_area, 1),
            "mass_pct_of_map_stage": round(100.0 * (mass & stage_m).sum() / stage_area, 1),
            "hull_pct_of_map_stage": round(100.0 * (hull_m.astype(bool) & stage_m).sum() / stage_area, 1),
            "object_px_pct_of_map_stage": round(100.0 * (cm & stage_m).sum() / stage_area, 1),
            "centroid_norm": [round(float(np.nonzero(mass)[1].mean()) / W, 3), round(float(np.nonzero(mass)[0].mean()) / H, 3)],
            "close_r_px": R,
        }
        lm_masks["__core__" + cname] = mass
        lm_masks["__hull__" + cname] = hull_m.astype(bool)
        # 모양: 주축 각도(화면, 오른쪽 위로 오르면 +)·길쭉함(주축/부축 표준편차 비)·채움(덩어리/볼록 껍질)·상자 종횡비
        yy, xx = np.nonzero(mass)
        cx, cy = xx.mean(), yy.mean()
        C = np.cov(np.vstack([xx - cx, -(yy - cy)]))
        ev, evec = np.linalg.eigh(C)
        major = evec[:, 1]
        ang = float(np.degrees(np.arctan2(major[1], major[0])))
        ang = (ang + 90) % 180 - 90
        elong = float(np.sqrt(ev[1] / max(ev[0], 1e-6)))
        solidity = float(mass.sum() / max(hull_m.sum(), 1))
        mb = bbox_of(mass)
        cores[cname]["shape"] = {"principal_axis_deg": round(ang, 1), "elongation": round(elong, 2),
                                 "solidity_mass_over_hull": round(solidity, 2),
                                 "mass_bbox_art": mb, "mass_bbox_aspect_w_over_h": round((mb[2] - mb[0]) / (mb[3] - mb[1]), 2)}
    res["core_groups"] = cores

    # 시각화
    vis = art.copy().astype(np.float32) * 0.45 + 255 * 0.55 * 0.0
    vis = art.copy().astype(np.float32)
    rng = np.random.RandomState(3)
    over = vis.copy()
    for nm, m in lm_masks.items():
        if nm.startswith("__"):
            continue
        col = rng.randint(40, 255, 3).astype(np.float32)
        over[m] = over[m] * 0.35 + col * 0.65
    other = obj & ~lm_union
    over[other] = over[other] * 0.5 + np.array([128, 128, 128], np.float32) * 0.5
    vis = over.astype(np.uint8)
    core_cols = [(0, 0, 255), (255, 0, 160), (0, 140, 255), (200, 0, 0)]
    for ci, cname in enumerate(cores):
        mass = lm_masks["__core__" + cname].astype(np.uint8)
        cs, _ = cv2.findContours(mass, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(vis, cs, -1, core_cols[ci % 4], 7 - 2 * ci)
    x0, y0, x1, y1 = stage
    cv2.rectangle(vis, (x0 + 3, y0 + 3), (x1 - 4, y1 - 4), (0, 200, 0), 6)
    for nm, info in res["landmarks"].items():
        if info["bbox_art"]:
            bx0, by0, bx1, by1 = info["bbox_art"]
            cv2.rectangle(vis, (bx0, by0), (bx1, by1), (255, 255, 0), 2)
    cv2.imwrite(os.path.join(OUT, f"{ref}_objects_vis.png"), vis)
    cv2.imwrite(os.path.join(OUT, "tny_crops", f"{ref}_objects_small.jpg"), cv2.resize(vis, (800, 1120), interpolation=cv2.INTER_AREA))
    np.save(os.path.join(OUT, f"{ref}_objmask.npy"), obj)
    np.savez_compressed(os.path.join(OUT, f"{ref}_lm_masks.npz"), **{k.replace("/", "_"): v for k, v in lm_masks.items()})
    with open(os.path.join(OUT, f"{ref}_objects.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "landmarks"}, ensure_ascii=False, indent=1))
    for nm, info in res["landmarks"].items():
        print(f"  {nm}: bbox{info['bbox_art']} {info['wh_mm']}mm area{info['area_mm2']}mm2 {info['pct_of_map_stage']}% comps{info['n_components']}")


if __name__ == "__main__":
    main(sys.argv[1])
