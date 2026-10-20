"""색 위계: 바탕 비율(비배경 마스크 기준)과 비배경 화소의 k-평균(8) 팔레트 비율.
출력: r3_palette.json
"""
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/refs")
from r3_common import OUT, REFS, load_norm  # noqa: E402

res = {}
for ref in REFS:
    im, _ = load_norm(ref)
    nb = cv2.imread(os.path.join(OUT, f"{ref}_nonbg.png"), 0) > 0
    P = im[nb].reshape(-1, 3).astype(np.float32)
    rng = np.random.default_rng(0)
    if len(P) > 300000:
        P = P[rng.choice(len(P), 300000, replace=False)]
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 60, 0.5)
    _, lb, c = cv2.kmeans(P, 8, None, crit, 4, cv2.KMEANS_PP_CENTERS)
    cnt = np.bincount(lb.ravel(), minlength=8)
    order = np.argsort(-cnt)
    tot_nb = nb.mean()
    pal = []
    for i in order:
        b, g, r = [int(v) for v in c[i]]
        pal.append({"hex": "#%02x%02x%02x" % (r, g, b), "pct_of_poster": round(100 * tot_nb * cnt[i] / cnt.sum(), 1)})
    # 바탕 대표색(가장자리 띠 중앙값)
    edge = np.concatenate([im[:, :15].reshape(-1, 3), im[:, -15:].reshape(-1, 3)])
    bgc = np.median(edge, 0).astype(int)
    res[ref] = {"background_pct": round(100 * (1 - tot_nb), 1), "background_hex(가장자리 중앙값)": "#%02x%02x%02x" % (bgc[2], bgc[1], bgc[0]),
                "palette_nonbg": pal}
    print(ref, res[ref]["background_pct"], res[ref]["background_hex(가장자리 중앙값)"], [(p["hex"], p["pct_of_poster"]) for p in pal])
with open(os.path.join(OUT, "r3_palette.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
