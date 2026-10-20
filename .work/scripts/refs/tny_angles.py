# -*- coding: utf-8 -*-
"""선분 방향 히스토그램(OpenCV LSD, 길이 가중)으로 지면 축 각도를 잰다.
- 각도: 화면 기준, 오른쪽 위로 오르면 +, 오른쪽 아래로 내리면 - (0~180 접기 후 -90~90)
- 고해상 타일 3장과 1000x1400(또는 450x630) 전체 이미지를 따로 잰다.
- 패널 영역(화면 평행 글자)이 섞이지 않도록 '지도 전용 창'에서도 따로 잰다.
"""
import json
import os

import cv2
import numpy as np

ROOT = "/Users/um-yunsang/roman-concrete-private-refs"
OUT = os.path.join(ROOT, ".work/out/refs-analysis")
REG = json.load(open(os.path.join(OUT, "tny_reg.json"), encoding="utf-8"))

# 지도 전용 창(아트 2000x2800 좌표, 눈으로 고른 '패널·타이틀 없는' 영역)
MAP_WINDOWS = {
    "203x-tokyo": [(520, 470, 1990, 2050), (520, 2050, 1990, 2680)],
    "203x-newyork2-centralpark": [(0, 420, 1990, 1500), (0, 1500, 1420, 2200)],
    "203x-newyork": [(560, 420, 1480, 2380), (0, 1180, 560, 2600)],
}


def lsd_segments(gray, min_len):
    lsd = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)
    lines = lsd.detect(gray)[0]
    if lines is None:
        return np.zeros((0, 4), np.float32)
    L = lines.reshape(-1, 4)
    ln = np.hypot(L[:, 2] - L[:, 0], L[:, 3] - L[:, 1])
    return L[ln >= min_len]


def angles_of(L):
    dx = L[:, 2] - L[:, 0]
    dy = L[:, 3] - L[:, 1]
    a = np.degrees(np.arctan2(-dy, dx))  # 화면 위쪽이 +
    a = (a + 90.0) % 180.0 - 90.0  # -90~90
    ln = np.hypot(dx, dy)
    return a, ln


def peak(a, w, lo, hi):
    m = (a >= lo) & (a < hi)
    if m.sum() == 0:
        return None
    aa, ww = a[m], w[m]
    # 0.1° 히스토그램 최빈값 → 그 주변 ±1.0° 가중 평균
    h, e = np.histogram(aa, bins=np.arange(lo, hi + 0.1, 0.1), weights=ww)
    c = e[np.argmax(h)] + 0.05
    m2 = np.abs(aa - c) <= 1.0
    mu = float(np.average(aa[m2], weights=ww[m2]))
    sd = float(np.sqrt(np.average((aa[m2] - mu) ** 2, weights=ww[m2])))
    return {"deg": round(mu, 2), "sd": round(sd, 2), "len_px": int(ww[m2].sum()), "n": int(m2.sum())}


def analyse(gray, min_len):
    L = lsd_segments(gray, min_len)
    a, ln = angles_of(L)
    tot = ln.sum()
    res = {"n_seg": int(len(L)), "total_len": int(float(tot))}
    res["pos"] = peak(a, ln, 15, 40)    # 오른쪽 위로 오르는 지면 축
    res["neg"] = peak(a, ln, -40, -15)  # 오른쪽 아래로 내리는 지면 축
    res["vert"] = peak(np.abs(a), ln, 80, 90.01)
    res["horiz"] = peak(a, ln, -5, 5)
    # 길이 비율
    def share(lo, hi, absval=False):
        x = np.abs(a) if absval else a
        return round(float(100.0 * ln[(x >= lo) & (x < hi)].sum() / max(tot, 1)), 1)
    res["share_pct"] = {
        "+25..+32": share(25, 32), "-32..-25": share(-32, -25),
        "|80..90|": share(80, 90.01, True), "-3..+3": share(-3, 3),
        "+26.0..+27.2": share(26.0, 27.2), "+29.4..+30.6": share(29.4, 30.6),
        "-27.2..-26.0": share(-27.2, -26.0), "-30.6..-29.4": share(-30.6, -29.4),
    }
    # 1° 히스토그램(길이 비율 %) 상위
    h, e = np.histogram(a, bins=np.arange(-90, 91, 1.0), weights=ln)
    top = np.argsort(h)[::-1][:8]
    res["top_bins"] = [[int(e[i]), round(float(100 * h[i] / max(tot, 1)), 1)] for i in top]
    return res


def main():
    out = {}
    for ref, info in REG.items():
        art = cv2.imread(os.path.join(OUT, f"{ref}_art.png"))
        g = cv2.cvtColor(art, cv2.COLOR_BGR2GRAY)
        r = {"tiles": {}, "map_windows_hi": None}
        for key, t in info["tiles"].items():
            x, y = [int(round(v)) for v in t["art_xy"]]
            w, h = t["art_wh"]
            r["tiles"][key] = analyse(g[y:y + h, x:x + w], 25)
        # 지도 전용 창 중 고해상 덮인 부분만
        cover = cv2.imread(os.path.join(OUT, f"{ref}_cover.png"), 0)
        acc = []
        for (x0, y0, x1, y1) in MAP_WINDOWS[ref]:
            sub = g[y0:y1, x0:x1].copy()
            cov = cover[y0:y1, x0:x1] > 0
            if cov.mean() < 0.05:
                continue
            L = lsd_segments(sub, 25)
            if len(L) == 0:
                continue
            mx = ((L[:, 0] + L[:, 2]) / 2).astype(int).clip(0, sub.shape[1] - 1)
            my = ((L[:, 1] + L[:, 3]) / 2).astype(int).clip(0, sub.shape[0] - 1)
            acc.append(L[cov[my, mx]])
        if acc:
            L = np.concatenate(acc)
            a, ln = angles_of(L)
            r["map_windows_hi"] = {"n_seg": int(len(L)), "pos": peak(a, ln, 15, 40), "neg": peak(a, ln, -40, -15),
                                   "vert": peak(np.abs(a), ln, 80, 90.01)}
        # 원본 전체 이미지(저해상)
        full = cv2.imread(os.path.join(ROOT, ".work/dl/refs-cities", info["full"]), 0)
        r["full_image"] = analyse(full, 12)
        out[ref] = r
        print(ref)
        for k, v in r["tiles"].items():
            print("  tile", k, "pos", v["pos"], "neg", v["neg"], "vert", v["vert"])
            print("        share", v["share_pct"])
        print("  mapwin", r["map_windows_hi"])
        print("  full  pos", r["full_image"]["pos"], "neg", r["full_image"]["neg"])
    with open(os.path.join(OUT, "tny_angles.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
