# -*- coding: utf-8 -*-
"""랜드마크별 GrabCut 윤곽(베이징 3.5절과 같은 방법 계열).
- 초기화: clip/poly 상자 밖 = 확정 바탕, 상자 안 = 아마 전경, 상자 안의 '땅·물·하늘 클래스이면서 평평한(국소 표준편차 작음)' 화소 = 아마 바탕.
- poly가 있으면 poly 밖은 확정 바탕.
- 격자 구조(fill_clip)는 GrabCut을 쓰지 않고 poly ∩ (땅·물·하늘 아님)으로 둔다.
결과는 <ref>_gc_masks.npz (랜드마크별 bool 마스크)와 요약 출력.
"""
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


def main(ref):
    D = DEFS[ref]
    art = cv2.imread(os.path.join(OUT, f"{ref}_art.png"))
    cls = np.load(os.path.join(OUT, f"{ref}_class.npy"))
    H, W = cls.shape
    g = cv2.cvtColor(art, cv2.COLOR_BGR2GRAY).astype(np.float32)
    mu = cv2.blur(g, (9, 9))
    sd = np.sqrt(np.maximum(cv2.blur(g * g, (9, 9)) - mu * mu, 0))
    flat_bg = np.isin(cls, [GROUND, WATER, SKY, BG, ROAD]) & (sd < 3.0)
    masks = {}
    for name, spec in D["landmarks"].items():
        if "clip" in spec:
            x0, y0, x1, y1 = spec["clip"]
            region = np.zeros((H, W), bool)
            region[y0:y1, x0:x1] = True
        else:
            region = np.zeros((H, W), np.uint8)
            cv2.fillPoly(region, [np.array(spec["poly"], np.int32)], 1)
            region = region.astype(bool)
        if spec.get("fill_clip"):
            m = region & ~np.isin(cls, [GROUND, WATER, SKY, BG])
            masks[name] = m
            continue
        ys, xs = np.nonzero(region)
        pad = 12
        bx0, by0 = max(0, xs.min() - pad), max(0, ys.min() - pad)
        bx1, by1 = min(W, xs.max() + pad + 1), min(H, ys.max() + pad + 1)
        sub = art[by0:by1, bx0:bx1]
        reg = region[by0:by1, bx0:bx1]
        gm = np.full(reg.shape, cv2.GC_BGD, np.uint8)
        gm[reg] = cv2.GC_PR_FGD
        gm[reg & flat_bg[by0:by1, bx0:bx1]] = cv2.GC_PR_BGD
        for (sx, sy) in spec.get("seeds", []):
            cv2.circle(gm, (sx - bx0, sy - by0), 6, cv2.GC_FGD, -1)
        bgd = np.zeros((1, 65), np.float64)
        fgd = np.zeros((1, 65), np.float64)
        try:
            cv2.grabCut(sub, gm, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
        except cv2.error as e:
            print(name, "grabCut 실패", e)
            continue
        fg = (gm == cv2.GC_FGD) | (gm == cv2.GC_PR_FGD)
        fg &= reg
        # 가장 큰 성분 + 씨앗이 닿는 성분만
        n, lab, st, _ = cv2.connectedComponentsWithStats(fg.astype(np.uint8), 8)
        keep = np.zeros(n, bool)
        if n > 1:
            keep[1 + np.argmax(st[1:, cv2.CC_STAT_AREA])] = True
        for (sx, sy) in spec.get("seeds", []):
            i = lab[min(max(sy - by0, 0), lab.shape[0] - 1), min(max(sx - bx0, 0), lab.shape[1] - 1)]
            if i:
                keep[i] = True
        keep[1:] |= st[1:, cv2.CC_STAT_AREA] >= 0.15 * st[1:, cv2.CC_STAT_AREA].max() if n > 1 else False
        fg = keep[lab]
        full = np.zeros((H, W), bool)
        full[by0:by1, bx0:bx1] = fg
        # 가는 첨탑·안테나(GrabCut이 바탕으로 보내는 부분)를 '바탕 클래스가 아닌 화소'로 더한다
        for poly in spec.get("add_polys", []):
            pm = np.zeros((H, W), np.uint8)
            cv2.fillPoly(pm, [np.array(poly, np.int32)], 1)
            full |= pm.astype(bool) & ~np.isin(cls, [GROUND, WATER, SKY, BG])
        masks[name] = full
    np.savez_compressed(os.path.join(OUT, f"{ref}_gc_masks.npz"), **{k: v for k, v in masks.items()})
    vis = art.copy().astype(np.float32)
    rng = np.random.RandomState(5)
    for nm, m in masks.items():
        col = rng.randint(30, 255, 3).astype(np.float32)
        vis[m] = vis[m] * 0.35 + col * 0.65
    vis = vis.astype(np.uint8)
    for nm, m in masks.items():
        cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(vis, cs, -1, (0, 0, 255), 2)
    cv2.imwrite(os.path.join(OUT, "tny_crops", f"{ref}_gc_small.jpg"), cv2.resize(vis, (1000, 1400), interpolation=cv2.INTER_AREA))
    cv2.imwrite(os.path.join(OUT, f"{ref}_gc_vis.png"), vis)
    for nm, m in masks.items():
        ys, xs = np.nonzero(m)
        if len(xs) == 0:
            print(nm, "빈 마스크")
            continue
        print(f"  {nm}: bbox[{xs.min()},{ys.min()},{xs.max()+1},{ys.max()+1}] {((xs.max()-xs.min()+1)*MMX):.1f}x{((ys.max()-ys.min()+1)*MMY):.1f}mm area {m.sum()*MMX*MMY:.0f}mm2")


if __name__ == "__main__":
    main(sys.argv[1])
