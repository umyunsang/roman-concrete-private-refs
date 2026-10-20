# -*- coding: utf-8 -*-
"""레퍼런스 3점(도쿄·뉴욕2·뉴욕1)의 고해상 타일(1000x933, 원본 2000x2800의 2x3 분할 중 3장)을
전체 이미지에 다중 배율 템플릿 매칭으로 정합하고, 2000x2800 합성 아트 좌표계를 만든다.

실행: uv run --no-project --with pillow --with opencv-python-headless --with numpy python -I tny_reg.py
입력 이미지는 읽기만 한다. 출력은 .work/out/refs-analysis/ 에만 쓴다.
"""
import json
import os
import sys

import cv2
import numpy as np

ROOT = "/Users/um-yunsang/roman-concrete-private-refs"
DL = os.path.join(ROOT, ".work/dl/refs-cities")
OUT = os.path.join(ROOT, ".work/out/refs-analysis")
os.makedirs(OUT, exist_ok=True)

REFS = {
    "203x-tokyo": {
        "full": "203x-tokyo/StH_2021_05_Poster_Tokyo-1.jpg",
        "tiles": {"01": "203x-tokyo/StH_2021_Poster_Tokyo_01.jpg",
                  "04": "203x-tokyo/StH_2021_Poster_Tokyo_04.jpg",
                  "05": "203x-tokyo/StH_2021_Poster_Tokyo_05.jpg"},
    },
    "203x-newyork2-centralpark": {
        "full": "203x-newyork2-centralpark/StH_202209_158_new-york2.jpg",
        "tiles": {"01": "203x-newyork2-centralpark/1000_StH_202209_158_poster_01.jpg",
                  "04": "203x-newyork2-centralpark/1000_StH_202209_158_poster_04.jpg",
                  "05": "203x-newyork2-centralpark/1000_StH_202209_158_poster_05.jpg"},
    },
    "203x-newyork": {
        "full": "203x-newyork/New-York1.jpg",
        "tiles": {"1": "203x-newyork/1000_35_newyork_1.jpg",
                  "4": "203x-newyork/1000_35_newyork_4.jpg",
                  "5": "203x-newyork/1000_35_newyork_5.jpg"},
    },
}

ART_W, ART_H = 2000, 2800


def imread(rel):
    p = os.path.join(DL, rel)
    im = cv2.imread(p, cv2.IMREAD_COLOR)
    if im is None:
        sys.exit("읽기 실패: " + p)
    return im


def match_tile(full, tile, s_guess):
    """tile을 배율 s로 줄여 full에서 찾는다. (best score, s, x, y) 반환. 좌표는 full 픽셀."""
    fg = cv2.cvtColor(full, cv2.COLOR_BGR2GRAY).astype(np.float32)
    tg = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY).astype(np.float32)
    best = None
    for s in np.linspace(s_guess * 0.96, s_guess * 1.04, 41):
        tw, th = int(round(tg.shape[1] * s)), int(round(tg.shape[0] * s))
        if tw >= fg.shape[1] or th >= fg.shape[0]:
            continue
        t = cv2.resize(tg, (tw, th), interpolation=cv2.INTER_AREA)
        r = cv2.matchTemplate(fg, t, cv2.TM_CCOEFF_NORMED)
        _, mx, _, loc = cv2.minMaxLoc(r)
        if best is None or mx > best[0]:
            best = (float(mx), float(s), int(loc[0]), int(loc[1]))
    # 부화소 정밀화: 최적 배율 근방에서 다시
    return best


def main():
    report = {}
    for ref, cfg in REFS.items():
        full = imread(cfg["full"])
        H, W = full.shape[:2]
        s_full = W / ART_W  # 아트 1px당 full 픽셀
        art = cv2.resize(full, (ART_W, ART_H), interpolation=cv2.INTER_CUBIC)
        cover = np.zeros((ART_H, ART_W), np.uint8)
        tiles = {}
        for key, rel in cfg["tiles"].items():
            tile = imread(rel)
            sc, s, x, y = match_tile(full, tile, s_full)
            # full 좌표 → 아트 좌표
            ax, ay = x / s_full, y / s_full
            scale_art = s / s_full  # 타일 1px당 아트 px
            tw = int(round(tile.shape[1] * scale_art))
            th = int(round(tile.shape[0] * scale_art))
            t2 = cv2.resize(tile, (tw, th), interpolation=cv2.INTER_AREA if scale_art < 1 else cv2.INTER_CUBIC)
            x0, y0 = int(round(ax)), int(round(ay))
            x1, y1 = min(ART_W, x0 + tw), min(ART_H, y0 + th)
            art[y0:y1, x0:x1] = t2[: y1 - y0, : x1 - x0]
            cover[y0:y1, x0:x1] = 255
            tiles[key] = {"file": rel, "score": round(sc, 4), "scale_tile_to_full": round(s, 5),
                          "scale_tile_to_art": round(scale_art, 5),
                          "art_xy": [round(ax, 1), round(ay, 1)], "art_wh": [tw, th]}
            print(ref, key, tiles[key])
        cv2.imwrite(os.path.join(OUT, f"{ref}_art.png"), art)
        cv2.imwrite(os.path.join(OUT, f"{ref}_cover.png"), cover)
        report[ref] = {"full": cfg["full"], "full_wh": [W, H], "art_wh": [ART_W, ART_H],
                       "hi_res_cover_pct": round(100.0 * (cover > 0).mean(), 1), "tiles": tiles}
    with open(os.path.join(OUT, "tny_reg.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v["hi_res_cover_pct"] for k, v in report.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
