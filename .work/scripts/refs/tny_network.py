# -*- coding: utf-8 -*-
"""길·강 연결망 실측.
- 폭: 마스크의 거리 변환 x2 를 뼈대(중심선) 위에서 읽은 분포(중앙값·사분위). 화면 폭(수직 방향 아님) 기준이다.
  등각에서 ±30° 띠의 '화면 수직 폭' = 실폭. (가로 폭으로 재면 1/sin60 배 커진다.)
- 블리드: 마스크가 액자 네 변에 닿는 구간.
- 접속: 랜드마크 마스크를 r px 부풀렸을 때 길·강과 겹치는지.
입력: <ref>_class.npy, <ref>_objects.json(랜드마크 상자), objects.py가 만든 마스크를 다시 만들지 않고 상자 기반 근사로 접속을 본다.
"""
import json
import os
import sys

import cv2
import numpy as np

ROOT = "/Users/um-yunsang/roman-concrete-private-refs"
OUT = os.path.join(ROOT, ".work/out/refs-analysis")
BG, ROAD, WATER, TEXT, OBJ, GROUND, SKY = 0, 1, 2, 3, 4, 5, 6
MM = 0.21


def skeleton(m):
    m = m.astype(np.uint8)
    try:
        return cv2.ximgproc.thinning(m * 255) > 0
    except Exception:
        # 형태학적 뼈대(간이)
        sk = np.zeros_like(m)
        el = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        img = m.copy()
        while True:
            er = cv2.erode(img, el)
            op = cv2.dilate(er, el)
            sk |= (img - op)
            img = er
            if img.sum() == 0:
                break
        return sk > 0


def widths(mask, min_comp=3000, close_k=7):
    m = mask.astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((close_k, close_k), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros(n, bool)
    keep[1:] = st[1:, cv2.CC_STAT_AREA] >= min_comp
    m = keep[lab].astype(np.uint8)
    if m.sum() == 0:
        return None
    dt = cv2.distanceTransform(m, cv2.DIST_L2, 5)
    sk = skeleton(m)
    v = 2 * dt[sk]
    v = v[v >= 6]
    if len(v) == 0:
        return None
    q = np.percentile(v, [25, 50, 75, 90])
    L = float(sk.sum())
    mean_w = float(m.sum()) / max(L, 1)
    return {"px_q25_med_q75_q90": [round(float(x), 1) for x in q],
            "mm_med": round(float(q[1]) * MM, 1), "pct_poster_w_med": round(100 * float(q[1]) / 2000, 1),
            "mean_w_px(area/centerline)": round(mean_w, 1), "mean_w_mm": round(mean_w * MM, 1),
            "centerline_len_px": int(L), "area_px": int(m.sum())}


def bleeds(mask, H, W, min_len=20):
    out = {}
    edges = {"left": mask[:, 0:4].any(1), "right": mask[:, W - 4:W].any(1), "top": mask[0:4, :].any(0),
             "bottom": mask[H - 4:H, :].any(0)}
    for k, v in edges.items():
        segs = []
        v = v.astype(np.int8)
        d = np.diff(np.concatenate([[0], v, [0]]))
        st, en = np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]
        for a, b in zip(st, en):
            if b - a >= min_len:
                segs.append([int(a), int(b)])
        out[k] = segs
    return out


def main(ref):
    cls = np.load(os.path.join(OUT, f"{ref}_class.npy"))
    H, W = cls.shape
    obj = json.load(open(os.path.join(OUT, f"{ref}_objects.json"), encoding="utf-8"))
    res = {}
    road = cls == ROAD
    water = cls == WATER
    ground = cls == GROUND
    res["road_width"] = widths(road, close_k=15)  # 가운데 흰 줄(바탕색에 가까움)을 메워 한 띠로
    res["water_width"] = widths(water, 8000)
    res["road_bleed"] = bleeds(cv2.morphologyEx(road.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)) > 0, H, W)
    res["water_bleed"] = bleeds(cv2.morphologyEx(water.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)) > 0, H, W)
    if ground.any():
        res["ground_bleed"] = bleeds(ground, H, W, 40)
    # 접속(상자 근사가 아니라 objects.py 마스크가 필요 → 오브젝트 마스크 다시 계산 대신 상자 안 OBJ 화소로 근사)
    objm = np.load(os.path.join(OUT, f"{ref}_objmask.npy"))
    rd = cv2.dilate(road.astype(np.uint8), np.ones((25, 25), np.uint8)) > 0
    wd = cv2.dilate(water.astype(np.uint8), np.ones((25, 25), np.uint8)) > 0
    con = {}
    for nm, info in obj["landmarks"].items():
        bb = info["bbox_art"]
        if not bb:
            continue
        x0, y0, x1, y1 = bb
        sub = objm[y0:y1, x0:x1]
        con[nm] = {"road": bool((sub & rd[y0:y1, x0:x1]).any()), "water": bool((sub & wd[y0:y1, x0:x1]).any())}
    res["landmark_touch_12px"] = con
    res["n_touch_road"] = sum(1 for v in con.values() if v["road"])
    res["n_touch_water"] = sum(1 for v in con.values() if v["water"])
    res["n_landmarks"] = len(con)
    with open(os.path.join(OUT, f"{ref}_network.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "landmark_touch_12px"}, ensure_ascii=False))
    print("길에 안 닿는 것:", [k for k, v in con.items() if not v["road"]])
    print("물에 닿는 것:", [k for k, v in con.items() if v["water"]])


if __name__ == "__main__":
    main(sys.argv[1])
