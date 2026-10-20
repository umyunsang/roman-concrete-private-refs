# -*- coding: utf-8 -*-
"""바탕 모델과 '잉크(바탕이 아닌 것)' 마스크.
- 도쿄: 세이가이하 무늬 + 세로 그라데이션 바탕. 행마다 좌우 가장자리 띠에서 바탕의 a·b 중앙값과 L 범위를 얻는다.
- 뉴욕2·뉴욕1: 바탕 클래스(하늘·땅·물)를 표본색으로 두고 최근접 분류한다.
마스크는 refs-analysis/<ref>_ink.png(255=잉크)로 저장한다.
"""
import json
import os
import sys

import cv2
import numpy as np

ROOT = "/Users/um-yunsang/roman-concrete-private-refs"
OUT = os.path.join(ROOT, ".work/out/refs-analysis")


def to_lab(bgr):
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    lab[..., 0] *= 100 / 255.0
    lab[..., 1] -= 128
    lab[..., 2] -= 128
    return lab


def run_median(v, k):
    pad = k // 2
    vp = np.pad(v, (pad, pad), mode="edge")
    return np.array([np.median(vp[i:i + k]) for i in range(len(v))])


def tokyo_bg(lab):
    H, W = lab.shape[:2]
    strips = np.concatenate([lab[:, 0:60], lab[:, W - 60:W]], axis=1)
    a_med = np.median(strips[..., 1], axis=1)
    b_med = np.median(strips[..., 2], axis=1)
    lo = np.percentile(strips[..., 0], 8, axis=1)
    hi = np.percentile(strips[..., 0], 92, axis=1)
    # 길이 가장자리를 지나가는 행을 걸러 내기 위해 3차 다항식 강건 적합(잔차 큰 행을 빼며 반복)
    y = np.arange(H, dtype=np.float64)
    keep = np.ones(H, bool)
    fits = {}
    for it in range(6):
        for name, v, tol in (("a", a_med, 1.2), ("b", b_med, 1.2), ("lo", lo, 1.5), ("hi", hi, 1.5)):
            c = np.polyfit(y[keep], v[keep], 3)
            fits[name] = np.polyval(c, y)
        res = (np.abs(a_med - fits["a"]) > 1.2) | (np.abs(b_med - fits["b"]) > 1.2) | \
              (np.abs(lo - fits["lo"]) > 1.5) | (np.abs(hi - fits["hi"]) > 1.5)
        keep = ~res
    # a·b 적합에 맞는 화소만으로 L 범위를 다시 잰다(길·판 화소 제외)
    da = strips[..., 1] - fits["a"][:, None]
    db = strips[..., 2] - fits["b"][:, None]
    okc = (da ** 2 + db ** 2) <= 3.0 ** 2
    Ls = np.where(okc, strips[..., 0], np.nan)
    lo2 = np.nanpercentile(Ls, 5, axis=1)
    hi2 = np.nanpercentile(Ls, 95, axis=1)
    good = np.isfinite(lo2) & np.isfinite(hi2) & (okc.mean(1) > 0.5) & ((hi2 - lo2) < 9)
    for name, v in (("lo", lo2), ("hi", hi2)):
        kk = good.copy()
        for it in range(5):
            c = np.polyfit(y[kk], v[kk], 4)
            f = np.polyval(c, y)
            kk = good & (np.abs(v - f) < 1.2)
        fits[name] = f
    return fits["a"], fits["b"], fits["lo"], fits["hi"]


def tokyo_ink(lab, tol_ab=4.0, tol_L=3.0):
    a_s, b_s, lo_s, hi_s = tokyo_bg(lab)
    da = lab[..., 1] - a_s[:, None]
    db = lab[..., 2] - b_s[:, None]
    L = lab[..., 0]
    chroma_ok = (da ** 2 + db ** 2) <= tol_ab ** 2
    L_ok = (L >= (lo_s[:, None] - tol_L)) & (L <= (hi_s[:, None] + tol_L))
    bg = chroma_ok & L_ok
    return (~bg).astype(np.uint8) * 255, {"a": a_s.tolist()[::100], "b": b_s.tolist()[::100],
                                          "Llo": lo_s.tolist()[::100], "Lhi": hi_s.tolist()[::100]}


def class_ink(lab, bg_colors, tol):
    """bg_colors: [(L,a,b), ...] 중 어느 하나와 ΔE<tol이면 바탕."""
    d = np.full(lab.shape[:2], 1e9, np.float32)
    for c in bg_colors:
        c = np.array(c, np.float32)
        d = np.minimum(d, np.sqrt(((lab - c) ** 2).sum(-1)))
    return (d >= tol).astype(np.uint8) * 255


def main(ref):
    art = cv2.imread(os.path.join(OUT, f"{ref}_art.png"))
    lab = to_lab(art)
    info = {}
    if ref == "203x-tokyo":
        ink, info = tokyo_ink(lab)
    elif ref == "203x-newyork2-centralpark":
        ink = class_ink(lab, [(22.7, 6.0, -18.0)], 8.0)  # 남색 하늘만 바탕(땅·물은 지도)
    else:
        ink = class_ink(lab, [(23.1, 6.0, -19.0), (25.6, 7.0, -20.5)], 6.0)  # 남색 바탕(밤·물)
    # 작은 잡티 제거
    k = np.ones((3, 3), np.uint8)
    ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, k)
    cv2.imwrite(os.path.join(OUT, f"{ref}_ink.png"), ink)
    sm = cv2.resize(ink, (500, 700), interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(OUT, "tny_crops", f"{ref}_ink_small.png"), sm)
    print(ref, "ink %", round(100 * (ink > 0).mean(), 1))
    if info:
        print(json.dumps({k: [round(x, 1) for x in v] for k, v in info.items()}))


if __name__ == "__main__":
    main(sys.argv[1])
