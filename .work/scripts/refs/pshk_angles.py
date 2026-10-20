"""레퍼런스 3점의 투영을 선분 방향 히스토그램으로 판정한다 (2026-10-18).

- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- OpenCV LSD로 선분을 찾고, 길이 가중 방향 히스토그램(0.25° 칸, 5칸 이동평균)에서 봉우리를 찾는다.
- 각도는 화면 기준이다. 오른쪽 위로 올라가면 +, 오른쪽 아래로 내려가면 -.
- 고해상도 타일(원본 2000x2800의 1/6 조각)과 전체 포스터(1000x1400)를 따로 잰다.
- 전체 포스터는 지도 영역 마스크(패널·타이틀 상자 제외) 안의 선분만 쓴다.
- 사용: uv run --no-project --with opencv-python-headless --with numpy python -I angles_ref.py <out_json>
"""
import json
import sys

import cv2
import numpy as np

BASE = "/Users/um-yunsang/roman-concrete-private-refs/.work/dl/refs-cities"
TILES = {
    "203x-paris": ["203x-paris/StH_2021_04_Paris_01.jpg", "203x-paris/StH_2021_04_Paris_04.jpg", "203x-paris/StH_2021_04_Paris_05.jpg"],
    "203x-shanghai": ["203x-shanghai/shanghai_1000_01.jpg", "203x-shanghai/shanghai_1000_04.jpg", "203x-shanghai/shanghai_1000_05.jpg"],
    "203x-hongkong": ["203x-hongkong/1000_StH_202204_153_Poster_01.jpg", "203x-hongkong/1000_StH_202204_153_Poster_04.jpg",
                      "203x-hongkong/1000_StH_202204_153_Poster_05.jpg"],
}
POSTER = {
    "203x-paris": "203x-paris/StH_2021_04_Poster_Paris2.jpg",
    "203x-shanghai": "203x-shanghai/shanghai_poster.jpg",
    "203x-hongkong": "203x-hongkong/StH_2022_04_Tokyo.jpg",
}
# 지도 밖(타이틀·패널·푸터) 상자, 1000x1400 화소. 지도 선분만 남기려고 가린다.
MASK_OUT = {
    "203x-paris": [(40, 40, 255, 450), (265, 30, 735, 265), (745, 40, 965, 365), (40, 1160, 360, 1340), (0, 1340, 1000, 1400)],
    "203x-shanghai": [(40, 60, 250, 475), (260, 15, 750, 245), (755, 60, 965, 265), (40, 1195, 1000, 1400)],
    "203x-hongkong": [(40, 40, 255, 330), (270, 15, 730, 220), (745, 40, 965, 250), (40, 1195, 1000, 1400)],
}

LSD = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)


def segs_of(gray, minlen):
    s = LSD.detect(gray)[0]
    if s is None:
        return np.zeros((0, 4))
    s = s.reshape(-1, 4)
    L = np.hypot(s[:, 2] - s[:, 0], s[:, 3] - s[:, 1])
    return s[L >= minlen]


def peaks(seg, top=8):
    dx, dy = seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1]
    L = np.hypot(dx, dy)
    a = np.degrees(np.arctan2(-dy, dx))
    a = (a + 90) % 180 - 90  # [-90, 90)
    bins = np.arange(-90, 90.25, 0.25)
    h, _ = np.histogram(a, bins=bins, weights=L)
    hs = np.convolve(np.r_[h[-8:], h, h[:8]], np.ones(5) / 5, mode="same")[8:-8]
    tot = float(L.sum())
    out = []
    for i in np.argsort(hs)[::-1]:
        c = (bins[i] + bins[i + 1]) / 2
        if all(abs(c - o["deg"]) > 4 and abs(abs(c - o["deg"]) - 180) > 4 for o in out):
            win = (a > c - 2) & (a < c + 2)
            if c > 88:
                win = win | (a < -88)
            if c < -88:
                win = win | (a > 88)
            if win.sum() < 5:
                continue
            aw = a[win].copy()
            if abs(c) > 85:
                aw = np.where(aw < 0, aw + 180, aw)  # 수직 근처는 0~180으로 펴서 평균
            m = float(np.average(aw, weights=L[win]))
            sd = float(np.sqrt(np.average((aw - m) ** 2, weights=L[win])))
            out.append({"deg": round(m, 2), "sd": round(sd, 2), "n": int(win.sum()), "len_pct": round(float(L[win].sum()) / tot * 100, 1)})
        if len(out) >= top:
            break
    # 고정 칸 점유율
    def share(lo, hi):
        return round(float(L[(a >= lo) & (a <= hi)].sum()) / tot * 100, 1)
    bands = {
        "+30±1.5": share(28.5, 31.5), "-30±1.5": share(-31.5, -28.5),
        "+26.6±1.5": share(25.1, 28.1), "-26.6±1.5": share(-28.1, -25.1),
        "0±1.5": share(-1.5, 1.5), "90±1.5": round(float(L[np.abs(a) >= 88.5].sum()) / tot * 100, 1),
    }
    return out, bands, int(len(seg)), round(tot)


def main():
    res = {}
    for rid in TILES:
        r = {"tiles": {}, "poster_map": None}
        for tp in TILES[rid]:
            g = cv2.imread(f"{BASE}/{tp}", cv2.IMREAD_GRAYSCALE)
            seg = segs_of(g, 25)
            pk, bands, n, tot = peaks(seg)
            r["tiles"][tp.split("/")[-1]] = {"peaks": pk, "bands": bands, "n_seg": n, "len_total": tot}
        g = cv2.imread(f"{BASE}/{POSTER[rid]}", cv2.IMREAD_GRAYSCALE)
        seg = segs_of(g, 20)
        keep = np.ones(len(seg), bool)
        mx, my = (seg[:, 0] + seg[:, 2]) / 2, (seg[:, 1] + seg[:, 3]) / 2
        for x0, y0, x1, y1 in MASK_OUT[rid]:
            keep &= ~((mx >= x0) & (mx <= x1) & (my >= y0) & (my <= y1))
        pk, bands, n, tot = peaks(seg[keep])
        r["poster_map"] = {"peaks": pk, "bands": bands, "n_seg": n, "len_total": tot}
        # 패널 영역만(화면 평행 검사)
        keep2 = np.zeros(len(seg), bool)
        for x0, y0, x1, y1 in MASK_OUT[rid][:-1]:
            keep2 |= (mx >= x0) & (mx <= x1) & (my >= y0) & (my <= y1)
        pk2, bands2, n2, tot2 = peaks(seg[keep2])
        r["poster_panels"] = {"peaks": pk2, "bands": bands2, "n_seg": n2, "len_total": tot2}
        res[rid] = r
    json.dump(res, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
    for rid, r in res.items():
        print("==", rid)
        for k, v in list(r["tiles"].items()) + [("poster_map", r["poster_map"]), ("poster_panels", r["poster_panels"])]:
            pk = ", ".join(f"{p['deg']:+.2f}°±{p['sd']:.2f}({p['len_pct']}%)" for p in v["peaks"][:6])
            print(f"  [{k}] n={v['n_seg']} bands={v['bands']}")
            print(f"      peaks: {pk}")


if __name__ == "__main__":
    main()
