# -*- coding: utf-8 -*-
"""라벨 블록 글줄 기울기 실측.
- 텍스트 마스크: 상자 안 최빈 바탕색(테두리 k-평균 1군)과 ΔE >= tol, 연결 성분 면적 <= max_cc (획만)
- 각도: -40~40° 0.5° 간격으로 마스크를 회전, 행 투영 분산이 최대인 각 = 글줄 기울기(오른쪽 위로 오르면 +)
- 세로획 높이: 열 방향 연속 구간 길이 분포의 90 백분위(대문자·어센더 세로획 근사), mm 환산 0.21
사용: python -I tny_label_angles.py <ref>
"""
import json
import os
import sys

import cv2
import numpy as np

ROOT = "/Users/um-yunsang/roman-concrete-private-refs"
OUT = os.path.join(ROOT, ".work/out/refs-analysis")

LABELS = {
    "203x-tokyo": {
        "Shinkansen(이름+본문)": [1440, 1245, 1560, 1395],
        "Tokyo Station": [1565, 1305, 1720, 1460],
        "Meiji Jingu Shrine": [1140, 1450, 1290, 1605],
        "Rainbow Bridge": [700, 2240, 860, 2395],
        "Tokyo Metropolitan Gov.": [1040, 615, 1260, 835],
        "Tokyo Skytree": [1580, 720, 1760, 895],
        "Imperial Palace": [1205, 860, 1350, 1060],
        "Sensoji Kaminarimon": [1430, 690, 1590, 940],
        "Roppongi Hills Mori Tower": [100, 1415, 345, 1565],
        "Statue of Hachiko": [150, 1650, 345, 1810],
        "Gotokuji Temple": [150, 2200, 300, 2350],
        "Tokyo Tower": [585, 1480, 690, 1645],
        "Sumida River(바닥 글)": [1335, 1885, 1480, 1965],
    },
    "203x-newyork2-centralpark": {
        "The Metropolitan Museum of Art": [495, 670, 700, 880],
        "American Museum of Natural History": [430, 410, 640, 560],
        "Soldiers' and Sailors' Monument": [740, 500, 990, 720],
        "Cathedral of St. John the Divine": [1170, 380, 1460, 600],
        "Solomon R. Guggenheim Museum": [1000, 1080, 1230, 1270],
        "Queensboro Bridge": [600, 1880, 780, 2040],
        "Roosevelt Island Tramway": [950, 1280, 1120, 1450],
        "Opera Gallery New York": [480, 1220, 640, 1360],
        "CENTRAL PARK(바닥 글)": [1140, 548, 1312, 672],
    },
    "203x-newyork": {
        "Christmas Tree": [1640, 1380, 1890, 1550],
        "GE Building": [1600, 980, 1720, 1090],
        "Street Sign": [1500, 1570, 1640, 1690],
        "Statue of Liberty": [440, 2190, 580, 2410],
        "Brooklyn Bridge": [745, 2140, 885, 2360],
        "Manhattan Bridge": [1270, 1650, 1375, 1840],
        "King Kong": [850, 820, 1010, 950],
        "EAST RIVER(바닥 글)": [1650, 1690, 1900, 1810],
    },
}


def lab_img(bgr):
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    lab[..., 0] *= 100 / 255.0
    lab[..., 1] -= 128
    lab[..., 2] -= 128
    return lab


def text_mask(sub_lab, tol=22.0, max_cc=1500):
    h, w = sub_lab.shape[:2]
    px = sub_lab.reshape(-1, 3)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    _, lbl, cen = cv2.kmeans(px.astype(np.float32), 3, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    cnt = np.bincount(lbl.ravel(), minlength=3)
    bg = cen[np.argmax(cnt)]
    d = np.sqrt(((sub_lab - bg) ** 2).sum(-1))
    m = (d >= tol).astype(np.uint8)
    n, l, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros(n, bool)
    keep[1:] = (st[1:, cv2.CC_STAT_AREA] >= 6) & (st[1:, cv2.CC_STAT_AREA] <= max_cc) & \
               (st[1:, cv2.CC_STAT_HEIGHT] <= 80) & (st[1:, cv2.CC_STAT_WIDTH] <= 120)
    return keep[l].astype(np.uint8)


def best_angle(m):
    h, w = m.shape
    best = (-1, 0)
    c = (w / 2, h / 2)
    for a in np.arange(-40, 40.01, 0.5):
        R = cv2.getRotationMatrix2D(c, -a, 1.0)  # 화면에서 +a(오른쪽 위로 오름) 글줄을 수평으로
        r = cv2.warpAffine(m.astype(np.float32), R, (w, h), flags=cv2.INTER_LINEAR)
        prof = r.sum(1)
        v = float(prof.var())
        if v > best[0]:
            best = (v, a)
    return best[1]


def stem_height(m):
    runs = []
    for x in range(m.shape[1]):
        col = m[:, x].astype(np.int8)
        d = np.diff(np.concatenate([[0], col, [0]]))
        st, en = np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]
        runs += [int(b - a) for a, b in zip(st, en) if b - a >= 4]
    if not runs:
        return None
    r = np.array(runs)
    return float(np.percentile(r, 90))


def main(ref):
    art = cv2.imread(os.path.join(OUT, f"{ref}_art.png"))
    lab = lab_img(art)
    out = {}
    for nm, (x0, y0, x1, y1) in LABELS[ref].items():
        sub = lab[y0:y1, x0:x1]
        m = text_mask(sub)
        a = best_angle(m)
        sh = stem_height(m)
        out[nm] = {"box": [x0, y0, x1, y1], "baseline_deg": a, "stem_p90_px": sh, "stem_p90_mm": round(sh * 0.21, 1) if sh else None,
                   "text_px": int(m.sum())}
        print(f"{ref} | {nm}: 글줄 {a:+.1f}°, 세로획 p90 {sh}px({round(sh*0.21,1) if sh else '-'}mm), 글자 화소 {int(m.sum())}")
    with open(os.path.join(OUT, f"{ref}_label_angles.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
