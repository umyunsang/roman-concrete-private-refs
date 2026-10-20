"""고해상도 타일 01·04·05를 전체 포스터(1000x1400)에 다중 배율 템플릿 매칭으로 정합한다 (2026-10-18).

- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- 사용: uv run --no-project --with opencv-python-headless --with numpy python -I reg_tiles.py <out_json>
"""
import json
import sys

import cv2
import numpy as np

BASE = "/Users/um-yunsang/roman-concrete-private-refs/.work/dl/refs-cities"
REFS = {
    "203x-paris": ("203x-paris/StH_2021_04_Poster_Paris2.jpg",
                   ["203x-paris/StH_2021_04_Paris_01.jpg", "203x-paris/StH_2021_04_Paris_04.jpg", "203x-paris/StH_2021_04_Paris_05.jpg"]),
    "203x-shanghai": ("203x-shanghai/shanghai_poster.jpg",
                      ["203x-shanghai/shanghai_1000_01.jpg", "203x-shanghai/shanghai_1000_04.jpg", "203x-shanghai/shanghai_1000_05.jpg"]),
    "203x-hongkong": ("203x-hongkong/StH_2022_04_Tokyo.jpg",
                      ["203x-hongkong/1000_StH_202204_153_Poster_01.jpg", "203x-hongkong/1000_StH_202204_153_Poster_04.jpg",
                       "203x-hongkong/1000_StH_202204_153_Poster_05.jpg"]),
}


def main():
    out = {}
    for rid, (pp, tiles) in REFS.items():
        P = cv2.imread(f"{BASE}/{pp}", cv2.IMREAD_GRAYSCALE)
        H, W = P.shape
        info = {"poster_wh": [W, H], "tiles": {}}
        for tp in tiles:
            T = cv2.imread(f"{BASE}/{tp}", cv2.IMREAD_GRAYSCALE)
            best = (-1.0, 0.0, (0, 0), (0, 0))
            for s in np.linspace(0.44, 0.56, 61):
                t = cv2.resize(T, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
                if t.shape[0] > H or t.shape[1] > W:
                    continue
                r = cv2.matchTemplate(P, t, cv2.TM_CCOEFF_NORMED)
                _, mv, _, ml = cv2.minMaxLoc(r)
                if mv > best[0]:
                    best = (float(mv), float(s), ml, t.shape)
            mv, s, (mx, my), (th, tw) = best
            info["tiles"][tp.split("/")[-1]] = {
                "score": round(mv, 3), "scale": round(s, 4), "xy": [int(mx), int(my)],
                "bbox_poster_px": [int(mx), int(my), int(mx + tw), int(my + th)],
                "bbox_norm": [round(mx / W, 4), round(my / H, 4), round((mx + tw) / W, 4), round((my + th) / H, 4)],
            }
        out[rid] = info
    json.dump(out, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
    for rid, v in out.items():
        print(rid, v["poster_wh"])
        for k, d in v["tiles"].items():
            print(f"   {k}: score {d['score']} scale {d['scale']} bbox {d['bbox_poster_px']}")


if __name__ == "__main__":
    main()
