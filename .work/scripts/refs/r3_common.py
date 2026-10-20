"""공용 도구: 레퍼런스 3점(타이베이·제주·자금성) 정밀 분석.

- 모든 좌표의 기준은 '정규 좌표 1000×1400'(N 좌표)이다. 0~1 정규화는 N/1000, N/1400.
- 원본 이미지는 읽기만 한다(내려받은 폴더 안에서 아무것도 실행하지 않는다).
"""
import json
import os

import cv2
import numpy as np

ROOT = "/Users/um-yunsang/roman-concrete-private-refs"
DL = os.path.join(ROOT, ".work/dl/refs-cities")
OUT = os.path.join(ROOT, ".work/out/refs-analysis")
os.makedirs(OUT, exist_ok=True)

NW, NH = 1000, 1400  # 정규 좌표 크기

REFS = {
    "203x-taipei": {
        "full": "203x-taipei/StH_2023_12_Poster_re.jpg",
        "tiles": {
            "01": "203x-taipei/1000_StH_2023_12_Poster_re_01.jpg",
            "04": "203x-taipei/1000_StH_2023_12_Poster_re_04.jpg",
            "05": "203x-taipei/1000_StH_2023_12_Poster_re_05.jpg",
        },
    },
    "203x-jeju": {
        "full": "203x-jeju/jejudo-4.jpg",
        "tiles": {
            "01": "203x-jeju/1000_40_jejudo_1.jpg",
            "04": "203x-jeju/1000_40_jejudo_4.jpg",
            "05": "203x-jeju/1000_40_jejudo_5.jpg",
        },
    },
    "203x-forbiddencity": {
        "full": "203x-forbiddencity/forbidden_city_poster.jpg",
        "tiles": {
            "01": "203x-forbiddencity/StH_202010_137_Poster_01.jpg",
            "04": "203x-forbiddencity/StH_202010_137_Poster_04.jpg",
            "05": "203x-forbiddencity/StH_202010_137_Poster_05.jpg",
        },
    },
}


def imread(rel):
    p = os.path.join(DL, rel)
    im = cv2.imread(p, cv2.IMREAD_COLOR)
    if im is None:
        raise FileNotFoundError(p)
    return im


def load_norm(ref_id, scale=1):
    """전체 포스터를 정규 좌표(1000×1400)×scale 로 맞춘다."""
    im = imread(REFS[ref_id]["full"])
    h, w = im.shape[:2]
    interp = cv2.INTER_CUBIC if w < NW * scale else cv2.INTER_AREA
    return cv2.resize(im, (NW * scale, NH * scale), interpolation=interp), (w, h)


def save_json(name, obj):
    p = os.path.join(OUT, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    return p


def load_json(name):
    with open(os.path.join(OUT, name), encoding="utf-8") as f:
        return json.load(f)


def to_mm(box):
    """N 좌표 상자를 A2(420×594mm) mm로."""
    x0, y0, x1, y1 = box
    return [round(x0 * 0.42, 1), round(y0 * 594 / 1400, 1), round(x1 * 0.42, 1), round(y1 * 594 / 1400, 1)]


def norm01(box):
    x0, y0, x1, y1 = box
    return [round(x0 / NW, 4), round(y0 / NH, 4), round(x1 / NW, 4), round(y1 / NH, 4)]


def lab(im_bgr):
    return cv2.cvtColor(im_bgr, cv2.COLOR_BGR2LAB).astype(np.float32) * np.array([100 / 255, 1, 1], np.float32) - np.array([0, 128, 128], np.float32)
