"""포스터 좌표(1000x1400) 구역을 잘라 확대하고 10 단위 보조 격자·50 단위 눈금을 덧그린다 (2026-10-18).

- 고해상도 타일이 덮는 구역은 타일(2배)에서 잘라 선명하게 보여 준다. 나머지는 전체 포스터를 확대한다.
- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- 사용: python -I pshk_crop.py <ref_id> <out_dir> <scale> <x0,y0,x1,y1> [<x0,y0,x1,y1> ...]
"""
import sys

import cv2
import numpy as np

BASE = "/Users/um-yunsang/roman-concrete-private-refs/.work/dl/refs-cities"
POSTER = {
    "203x-paris": "203x-paris/StH_2021_04_Poster_Paris2.jpg",
    "203x-shanghai": "203x-shanghai/shanghai_poster.jpg",
    "203x-hongkong": "203x-hongkong/StH_2022_04_Tokyo.jpg",
}
TILES = {  # 타일 파일, 포스터 좌표 원점(x, y). 타일은 포스터의 2배 해상도.
    "203x-paris": [("203x-paris/StH_2021_04_Paris_01.jpg", 0, 0), ("203x-paris/StH_2021_04_Paris_04.jpg", 500, 466.5),
                   ("203x-paris/StH_2021_04_Paris_05.jpg", 0, 933)],
    "203x-shanghai": [("203x-shanghai/shanghai_1000_01.jpg", 0, 0), ("203x-shanghai/shanghai_1000_04.jpg", 500, 466.5),
                      ("203x-shanghai/shanghai_1000_05.jpg", 0, 933)],
    "203x-hongkong": [("203x-hongkong/1000_StH_202204_153_Poster_01.jpg", 0, 0),
                      ("203x-hongkong/1000_StH_202204_153_Poster_04.jpg", 500, 466.5),
                      ("203x-hongkong/1000_StH_202204_153_Poster_05.jpg", 0, 933)],
}


def main():
    rid, out_dir, scale = sys.argv[1], sys.argv[2], float(sys.argv[3])
    big = build(rid)
    for spec in sys.argv[4:]:
        x0, y0, x1, y1 = [float(v) for v in spec.split(",")]
        out = f"{out_dir}/{rid}_{int(x0)}_{int(y0)}_{int(x1)}_{int(y1)}.png"
        crop(big, x0, y0, x1, y1, scale, out)


def build(rid):
    P = cv2.imread(f"{BASE}/{POSTER[rid]}")
    big = cv2.resize(P, (2000, 2800), interpolation=cv2.INTER_CUBIC)
    for tp, ox, oy in TILES[rid]:
        T = cv2.imread(f"{BASE}/{tp}")
        X, Y = int(round(ox * 2)), int(round(oy * 2))
        hh, ww = min(T.shape[0], 2800 - Y), min(T.shape[1], 2000 - X)
        big[Y:Y + hh, X:X + ww] = T[:hh, :ww]
    return big


def crop(big, x0, y0, x1, y1, scale, out):
    c = big[int(y0 * 2):int(y1 * 2), int(x0 * 2):int(x1 * 2)].copy()
    f = scale / 2.0
    c = cv2.resize(c, None, fx=f, fy=f, interpolation=cv2.INTER_AREA if f < 1 else cv2.INTER_CUBIC)
    h, w = c.shape[:2]
    ov = c.copy()
    for gx in np.arange(np.ceil(x0 / 10) * 10, x1 + 0.1, 10):
        px = int(round((gx - x0) * scale))
        major = int(gx) % 50 == 0
        cv2.line(ov, (px, 0), (px, h), (0, 255, 255) if major else (200, 200, 200), 1)
        if major:
            cv2.putText(c, str(int(gx)), (px + 2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)
    for gy in np.arange(np.ceil(y0 / 10) * 10, y1 + 0.1, 10):
        py = int(round((gy - y0) * scale))
        major = int(gy) % 50 == 0
        cv2.line(ov, (0, py), (w, py), (0, 255, 255) if major else (200, 200, 200), 1)
        if major:
            cv2.putText(c, str(int(gy)), (2, py - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)
    c = cv2.addWeighted(ov, 0.35, c, 0.65, 0)
    cv2.imwrite(out, c)
    print(out, c.shape[1], "x", c.shape[0])


if __name__ == "__main__":
    main()
