"""Gismondi 모형 사진 3장 정량 실측 (2026-10-18).

- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- 측정
  1) 벽돌색 수도교(유일한 유채색 선 요소) 색 마스크: 상자, 중심선 길이(사진 폭 대비), 콜로세움과의 최소 거리
  2) 확대 판독 다각형(모형 면, 테베레, 콜로세움, 코어 군 등)의 면적 비율
  3) 콜로세움 위 테두리 타원 비 → 시선 고도(외벽 높이로 교차 검증)
  4) LSD 선분 방향 히스토그램(일관된 지면 축 유무)
- 사용: python -I tg_gi_measure.py <사진 폴더> <출력 폴더>
"""
import json
import math
import sys

import cv2
import numpy as np

PHOTOS = {
    "D": "Vue_maquette_de_Gismondi_JP_Dalbera.jpg",
    "R": "Model_of_imperial_Rome_Velian_Colosseum_Raddato.jpg",
    "E": "RomemodelEUR3.jpg",
}
# 콜로세움 위 테두리 타원(좌·우 끝 x, 맨 위 y, 앞쪽 테두리 y)과 외벽 바닥 y: 확대 판독 정규 좌표(±0.003)
COLO = {
    "D": {"x0": 0.534, "x1": 0.611, "top": 0.4005, "rim_front": 0.4667, "base": 0.500, "장축 화면 방향": "가로(남쪽 시점)"},
    "R": {"x0": 0.4574, "x1": 0.6374, "top": 0.6011, "rim_front": 0.7442, "base": 0.8186, "장축 화면 방향": "깊이(동쪽 시점)"},
    "E": {"x0": 0.6506, "x1": 0.7297, "top": 0.2094, "rim_front": 0.2575, "base": 0.2804, "장축 화면 방향": "가로(남쪽 시점)"},
}
# 수도교 색 임계(H 최소, H 최대, S 최소, V 최소): 사진별 표본(tg_px.py) 기준. D 수도교 HSV(8,117,177) vs 지붕 S p90 89.
AQ_TH = {"D": (6, 11, 112, 130), "R": (9, 18, 100, 120), "E": (10, 16, 92, 115)}
# 확대 판독 다각형(정규 좌표). 경계 판독 오차 ±0.01 안팎.
POLY = {
    "D": {
        "모형 면": [(0, 0.10), (0.19, 0.10), (0.20, 0.06), (0.30, 0.04), (0.35, 0.02), (0.42, 0.015), (0.55, 0.02),
                 (0.70, 0.03), (0.78, 0.04), (0.80, 0.07), (0.85, 0.10), (0.90, 0.13), (0.95, 0.17), (1.0, 0.21), (1, 1), (0, 1)],
        "테베레(앞쪽 굽이)": [(0, 0.405), (0.06, 0.415), (0.10, 0.43), (0.125, 0.46), (0.135, 0.50), (0.12, 0.535), (0.10, 0.56),
                       (0.09, 0.60), (0.07, 0.65), (0.03, 0.70), (0, 0.72)],
        "콜로세움": [(0.534, 0.4005), (0.611, 0.4005), (0.611, 0.500), (0.534, 0.500)],
        "대전차경기장": [(0.17, 0.60), (0.20, 0.595), (0.425, 0.80), (0.42, 0.865), (0.39, 0.87), (0.165, 0.64)],
        "클라우디우스 신전 경내": [(0.555, 0.51), (0.64, 0.505), (0.673, 0.60), (0.66, 0.631), (0.575, 0.631), (0.555, 0.56)],
        "팔라티노 궁전군": [(0.28, 0.50), (0.40, 0.47), (0.47, 0.55), (0.47, 0.70), (0.40, 0.73), (0.33, 0.68), (0.28, 0.58)],
        "코어 군(콜로세움 골짜기)": [(0.45, 0.39), (0.673, 0.39), (0.673, 0.66), (0.45, 0.66)],
    },
    "R": {
        "모형 면": [(0, 0), (1, 0), (1, 1), (0, 1)],
        "테베레": [(0.40, 0.02), (0.52, 0.0), (0.66, 0.0), (0.78, 0.0), (0.98, 0.0), (0.98, 0.04), (0.88, 0.07), (0.80, 0.10),
                (0.72, 0.13), (0.66, 0.12), (0.62, 0.10), (0.55, 0.12), (0.45, 0.13), (0.40, 0.10)],
        "콜로세움": [(0.4574, 0.6011), (0.6374, 0.6011), (0.6374, 0.8186), (0.4574, 0.8186)],
        "클라우디우스 신전 경내": [(0.125, 0.60), (0.355, 0.60), (0.36, 0.80), (0.13, 0.80)],
        "대전차경기장": [(0.05, 0.33), (0.43, 0.19), (0.47, 0.21), (0.10, 0.40), (0.05, 0.39)],
        "코어 군(콜로세움 골짜기)": [(0.0, 0.40), (0.74, 0.40), (0.74, 0.93), (0.0, 0.93)],
    },
    "E": {
        "모형 면": [(0, 0), (1, 0), (1, 1), (0, 1)],
        "테베레": [(0, 0.17), (0.08, 0.18), (0.18, 0.20), (0.24, 0.24), (0.27, 0.29), (0.24, 0.36), (0.17, 0.42), (0.10, 0.47),
                (0.04, 0.53), (0, 0.55)],
        "콜로세움": [(0.6506, 0.2094), (0.7297, 0.2094), (0.7297, 0.2804), (0.6506, 0.2804)],
        "대전차경기장": [(0.33, 0.36), (0.36, 0.34), (0.58, 0.47), (0.57, 0.51), (0.53, 0.52), (0.32, 0.39)],
        "카라칼라 욕장": [(0.73, 0.63), (1.0, 0.60), (1.0, 1.0), (0.80, 1.0), (0.73, 0.80)],
        "코어 군(콜로세움 골짜기)": [(0.60, 0.17), (0.82, 0.17), (0.82, 0.40), (0.60, 0.40)],
    },
}


def poly_area(p):
    a = 0.0
    for (x1, y1), (x2, y2) in zip(p, p[1:] + p[:1]):
        a += x1 * y2 - x2 * y1
    return abs(a) / 2


def skeleton(mask):
    sk = np.zeros_like(mask)
    el = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    m = mask.copy()
    while True:
        er = cv2.erode(m, el)
        op = cv2.dilate(er, el)
        sk |= (m & ~op)
        m = er
        if not m.any():
            break
    return sk


def lsd(gray):
    det = cv2.createLineSegmentDetector()
    segs = det.detect(gray)[0].reshape(-1, 4)
    dx, dy = segs[:, 2] - segs[:, 0], segs[:, 3] - segs[:, 1]
    L = np.hypot(dx, dy)
    keep = L >= 25
    a = (np.degrees(np.arctan2(-dy[keep], dx[keep])) + 90) % 180 - 90
    w = L[keep]
    tot = w.sum()
    hist, edges = np.histogram(a, bins=np.arange(-90, 90.5, 1.0), weights=w)
    peaks = []
    for i in np.argsort(hist)[::-1]:
        c = (edges[i] + edges[i + 1]) / 2
        if all(abs(((c - p[0]) + 90) % 180 - 90) > 6 for p in peaks):
            win = np.abs(((a - c) + 90) % 180 - 90) <= 1.5
            peaks.append((round(float(c), 1), round(float(w[win].sum() / tot * 100), 1)))
        if len(peaks) >= 5:
            break
    # 길이 가중 방향 분포의 정점 집중도: 상위 2개 사선 봉우리(±1.5°) 합
    obl = [p for p in peaks if 8 < abs(p[0]) < 82][:2]
    return {"봉우리(각°, ±1.5° 길이비%)": peaks, "사선 상위 2봉우리 합%": round(sum(p[1] for p in obl), 1),
            "수직±2°%": round(float(w[np.abs(np.abs(a) - 90) <= 2].sum() / tot * 100), 1),
            "수평±2°%": round(float(w[np.abs(a) <= 2].sum() / tot * 100), 1), "선분 수": int(keep.sum())}


def main():
    src, outdir = sys.argv[1], sys.argv[2]
    out = {}
    for key, fn in PHOTOS.items():
        img = cv2.imread(f"{src}/{fn}")
        H, W = img.shape[:2]
        s = 1600 / W
        small = cv2.resize(img, (1600, int(H * s)), interpolation=cv2.INTER_AREA)
        h, w = small.shape[:2]
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        hh, ss, vv = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
        th = AQ_TH[key]
        aq = ((hh >= th[0]) & (hh <= th[1]) & (ss >= th[2]) & (vv >= th[3])).astype(np.uint8) * 255
        mpoly = np.array([[int(x * w), int(y * h)] for x, y in POLY[key]["모형 면"]], np.int32)
        mmask = np.zeros((h, w), np.uint8)
        cv2.fillPoly(mmask, [mpoly], 255)
        aq = cv2.bitwise_and(aq, mmask)
        aq = cv2.morphologyEx(aq, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        aq = cv2.morphologyEx(aq, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
        n, lab, st, _ = cv2.connectedComponentsWithStats(aq, 8)
        comps = []
        keep = np.zeros_like(aq, bool)
        for i in range(1, n):
            x, y, bw, bh, a = st[i]
            if a < 400:
                continue
            elong = max(bw, bh) / max(1, min(bw, bh))
            fill = a / (bw * bh)
            if elong >= 2.5 or fill < 0.35:  # 가늘고 긴 선 요소만
                keep |= lab == i
                comps.append({"상자 정규": [round(x / w, 3), round(y / h, 3), round((x + bw) / w, 3), round((y + bh) / h, 3)],
                              "면적 px(1600폭)": int(a)})
        sk = skeleton(keep.astype(np.uint8))
        c = COLO[key]
        cx, cy = (c["x0"] + c["x1"]) / 2 * w, (c["top"] + c["base"]) / 2 * h
        ys, xs = np.nonzero(keep)
        dmin = float(np.min(np.hypot(xs - cx, ys - cy))) if len(xs) else None
        colo_w = (c["x1"] - c["x0"]) * w
        # 타원 비와 시선 고도
        rim_w = (c["x1"] - c["x0"]) * W
        rim_h = (c["rim_front"] - c["top"]) * H
        wall = (c["base"] - c["rim_front"]) * H
        ratio = rim_h / rim_w
        if c["장축 화면 방향"].startswith("가로"):
            sin_el = ratio / (156 / 188)
            ppm = rim_w / 188
        else:
            sin_el = ratio / (188 / 156)
            ppm = rim_w / 156
        el = math.degrees(math.asin(min(1.0, sin_el)))
        wall_pred = 48 * math.cos(math.radians(el)) * ppm
        polys = {k: round(poly_area(v) * 100, 2) for k, v in POLY[key].items()}
        model_a = poly_area(POLY[key]["모형 면"])
        rel = {k: round(poly_area(v) / model_a * 100, 2) for k, v in POLY[key].items() if k != "모형 면"}
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        out[key] = {
            "파일": fn, "원본 크기": [W, H],
            "수도교(벽돌색) 성분": comps,
            "수도교 중심선 길이/사진 폭": round(float(sk.sum()) / w, 2),
            "수도교–콜로세움 중심 최소 거리(콜로세움 화면 폭 배수)": round(dmin / colo_w, 2) if dmin is not None else None,
            "수도교 화소 비율%(사진)": round(float(keep.mean() * 100), 2),
            "콜로세움 타원": {"위 테두리 폭 px": round(rim_w), "위 테두리 높이 px": round(rim_h), "높이/폭": round(ratio, 3),
                         "장축 화면 방향 가정": c["장축 화면 방향"], "시선 고도°": round(el, 1),
                         "외벽 높이 실측 px": round(wall), "외벽 높이 예측 px(48m×cos고도)": round(wall_pred),
                         "예측/실측": round(wall_pred / wall, 2),
                         "콜로세움 상자 사진 대비%": round((c["x1"] - c["x0"]) * (c["base"] - c["top"]) * 100, 2)},
            "다각형 면적%(사진 대비)": polys, "다각형 면적%(모형 면 대비)": rel,
            "선분 방향(LSD)": lsd(gray),
        }
        vis = small.copy()
        vis[keep] = (0, 255, 255)
        vis[sk > 0] = (255, 0, 255)
        for k, v in POLY[key].items():
            pts = np.array([[int(x * w), int(y * h)] for x, y in v], np.int32)
            cv2.polylines(vis, [pts], True, (0, 0, 255) if "코어" in k else (255, 255, 0), 2)
        cv2.imwrite(f"{outdir}/gi_{key}_check.png", vis)
    with open(f"{outdir}/gi_measure.json", "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
