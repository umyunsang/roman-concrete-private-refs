"""파리·상하이·홍콩 정밀 분석 공용 도구 (2026-10-18).

- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- 좌표계: 전체 포스터 1000x1400 화소. A2 환산은 x 1px = 0.42mm, y 1px = 0.424286mm.
"""
import cv2
import numpy as np

BASE = "/Users/um-yunsang/roman-concrete-private-refs/.work/dl/refs-cities"
OUT = "/Users/um-yunsang/roman-concrete-private-refs/.work/out/refs-analysis"
WORK = OUT + "/pshk"
POSTER = {
    "203x-paris": "203x-paris/StH_2021_04_Poster_Paris2.jpg",
    "203x-shanghai": "203x-shanghai/shanghai_poster.jpg",
    "203x-hongkong": "203x-hongkong/StH_2022_04_Tokyo.jpg",
}
TILES = {
    "203x-paris": [("203x-paris/StH_2021_04_Paris_01.jpg", 0, 0), ("203x-paris/StH_2021_04_Paris_04.jpg", 500, 466.5),
                   ("203x-paris/StH_2021_04_Paris_05.jpg", 0, 933)],
    "203x-shanghai": [("203x-shanghai/shanghai_1000_01.jpg", 0, 0), ("203x-shanghai/shanghai_1000_04.jpg", 500, 466.5),
                      ("203x-shanghai/shanghai_1000_05.jpg", 0, 933)],
    "203x-hongkong": [("203x-hongkong/1000_StH_202204_153_Poster_01.jpg", 0, 0),
                      ("203x-hongkong/1000_StH_202204_153_Poster_04.jpg", 500, 466.5),
                      ("203x-hongkong/1000_StH_202204_153_Poster_05.jpg", 0, 933)],
}
W, H = 1000, 1400
MMX, MMY = 420 / W, 594 / H
FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"


def poster(rid):
    return cv2.imread(f"{BASE}/{POSTER[rid]}")


def composite2x(rid):
    """전체 포스터를 2배로 키우고 고해상도 타일 3장을 제자리에 붙인다(2000x2800)."""
    P = poster(rid)
    big = cv2.resize(P, (2 * W, 2 * H), interpolation=cv2.INTER_CUBIC)
    cov = np.zeros((2 * H, 2 * W), np.uint8)
    for tp, ox, oy in TILES[rid]:
        T = cv2.imread(f"{BASE}/{tp}")
        X, Y = int(round(ox * 2)), int(round(oy * 2))
        hh, ww = min(T.shape[0], 2 * H - Y), min(T.shape[1], 2 * W - X)
        big[Y:Y + hh, X:X + ww] = T[:hh, :ww]
        cov[Y:Y + hh, X:X + ww] = 1
    return big, cov


def lab(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)


def content_mask(img, k=41, thr=18.0):
    """큰 창 중앙값을 국지 바탕으로 보고, 바탕과 색차가 큰 화소(글자·가는 선)를 고른다."""
    bg = cv2.medianBlur(img, k)
    d = np.sqrt(((lab(img) - lab(bg)) ** 2).sum(-1))
    return (d > thr).astype(np.uint8), d


def snap_bbox(mask, seed, pad=12, min_px=3):
    """씨앗 상자(pad만큼 넓힘) 안 내용 화소의 꼭 맞는 상자를 구한다."""
    x0, y0, x1, y1 = seed
    X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)
    sub = mask[Y0:Y1, X0:X1]
    n, lb, st, _ = cv2.connectedComponentsWithStats(sub)
    keep = np.zeros_like(sub)
    for i in range(1, n):
        if st[i, 4] >= min_px:
            keep[lb == i] = 1
    ys, xs = np.where(keep > 0)
    if len(xs) == 0:
        return None
    return [int(X0 + xs.min()), int(Y0 + ys.min()), int(X0 + xs.max() + 1), int(Y0 + ys.max() + 1)]


def norm(b):
    return [round(b[0] / W, 4), round(b[1] / H, 4), round(b[2] / W, 4), round(b[3] / H, 4)]


def mm(b):
    return [round(b[0] * MMX, 1), round(b[1] * MMY, 1), round(b[2] * MMX, 1), round(b[3] * MMY, 1)]


def area_pct(b, ref=W * H):
    return round((b[2] - b[0]) * (b[3] - b[1]) / ref * 100, 2)
