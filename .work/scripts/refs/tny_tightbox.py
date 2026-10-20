# -*- coding: utf-8 -*-
"""검색 창 안의 '잉크' 외곽 상자를 잰다.
바탕 톤 = 창 테두리 화소의 k-평균 군집(테두리가 바탕 위에 있도록 창을 고른다).
잉크 = 모든 바탕 톤과 ΔE(Lab) >= tol 인 화소. 작은 잡티(min_px 미만 연결 성분)는 버린다.
함수 tight_box(ref, (x0,y0,x1,y1), tol=10, k=3, min_px=6) -> (x0,y0,x1,y1, ink_px)
명령행: python -I tny_tightbox.py <ref> '{"name":[x0,y0,x1,y1], ...}' [tol]
"""
import json
import os
import sys

import cv2
import numpy as np

ROOT = "/Users/um-yunsang/roman-concrete-private-refs"
OUT = os.path.join(ROOT, ".work/out/refs-analysis")
_cache = {}


def lab_of(ref):
    if ref not in _cache:
        art = cv2.imread(os.path.join(OUT, f"{ref}_art.png"))
        lab = cv2.cvtColor(art, cv2.COLOR_BGR2LAB).astype(np.float32)
        lab[..., 0] *= 100 / 255.0
        lab[..., 1] -= 128
        lab[..., 2] -= 128
        _cache[ref] = lab
    return _cache[ref]


def ink_in(ref, win, tol=10.0, k=3, min_px=6, border=6):
    lab = lab_of(ref)
    x0, y0, x1, y1 = win
    sub = lab[y0:y1, x0:x1]
    h, w = sub.shape[:2]
    bmask = np.zeros((h, w), bool)
    bmask[:border, :] = True
    bmask[-border:, :] = True
    bmask[:, :border] = True
    bmask[:, -border:] = True
    B = sub[bmask].reshape(-1, 3).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.2)
    _, lbl, cen = cv2.kmeans(B, k, None, crit, 4, cv2.KMEANS_PP_CENTERS)
    cnt = np.bincount(lbl.ravel(), minlength=k)
    cen = cen[cnt >= 0.05 * len(B)]  # 테두리의 5% 이상인 톤만 바탕으로
    d = np.full((h, w), 1e9, np.float32)
    for c in cen:
        d = np.minimum(d, np.sqrt(((sub - c) ** 2).sum(-1)))
    ink = (d >= tol).astype(np.uint8)
    n, lab_cc, stats, _ = cv2.connectedComponentsWithStats(ink, 8)
    keep = np.zeros(n, bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= min_px
    ink = keep[lab_cc]
    return ink, cen


_gink = {}


def global_ink(ref, win, min_px=6):
    """inkmask.py가 만든 전역 잉크 마스크(도쿄: 행별 세이가이하 바탕 모델) 사용."""
    if ref not in _gink:
        _gink[ref] = cv2.imread(os.path.join(OUT, f"{ref}_ink.png"), 0) > 0
    x0, y0, x1, y1 = win
    ink = _gink[ref][y0:y1, x0:x1].astype(np.uint8)
    n, lab_cc, stats, _ = cv2.connectedComponentsWithStats(ink, 8)
    keep = np.zeros(n, bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= min_px
    return keep[lab_cc], None


def tight_box(ref, win, tol=10.0, k=3, min_px=6, mode="border"):
    if mode == "global":
        ink, cen = global_ink(ref, win, min_px)
    else:
        ink, cen = ink_in(ref, win, tol, k, min_px)
    # 창 테두리에 닿는 연결 성분(창 밖에서 들어온 이웃)은 버리고, 창 안에 온전히 든 성분만 합친다
    n, lab_cc, st, _ = cv2.connectedComponentsWithStats(ink.astype(np.uint8), 8)
    h, w = ink.shape
    inside = np.zeros(n, bool)
    for i in range(1, n):
        x, y, ww, hh, a = st[i]
        if a < min_px:
            continue
        if x <= 0 or y <= 0 or x + ww >= w or y + hh >= h:
            continue
        inside[i] = True
    ink = inside[lab_cc]
    ys, xs = np.nonzero(ink)
    if len(xs) == 0:
        return None
    x0, y0 = win[0], win[1]
    return (int(x0 + xs.min()), int(y0 + ys.min()), int(x0 + xs.max() + 1), int(y0 + ys.max() + 1), int(ink.sum()))


if __name__ == "__main__":
    ref = sys.argv[1]
    wins = json.loads(sys.argv[2])
    tol = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
    mode = sys.argv[4] if len(sys.argv) > 4 else "border"
    for name, w in wins.items():
        b = tight_box(ref, w, tol, mode=mode, min_px=12)
        if b is None:
            print(name, "없음")
            continue
        x0, y0, x1, y1, n = b
        print(f"{name}: art({x0},{y0},{x1},{y1}) w{x1-x0} h{y1-y0} | norm({x0/2000:.4f},{y0/2800:.4f},{x1/2000:.4f},{y1/2800:.4f}) | mm({x0*0.21:.1f},{y0*0.21214:.1f},{x1*0.21:.1f},{y1*0.21214:.1f}) ink{n}"
              + ("  [창 경계에 닿음]" if (x0 <= w[0] + 7 or y0 <= w[1] + 7 or x1 >= w[2] - 7 or y1 >= w[3] - 7) else ""))
