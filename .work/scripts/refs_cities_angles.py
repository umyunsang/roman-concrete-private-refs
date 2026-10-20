"""후보 이미지의 선분 방향을 재서 투영(등각 30° / 2:1 26.57° / 기타)을 판정한다 (2026-10-18).

- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- OpenCV LSD로 선분을 찾고, 길이 가중 방향 히스토그램에서 수평·수직을 뺀 지배 각을 구한다.
- 사용: uv run --no-project --with opencv-python-headless --with numpy python -I refs_cities_angles.py <slug>=<경로> ...
"""
import sys

import cv2
import numpy as np


def measure(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    h, w = img.shape
    scale = 1400 / max(h, w)
    if scale < 1:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    lsd = cv2.createLineSegmentDetector()
    lines = lsd.detect(img)[0]
    if lines is None:
        return None
    seg = lines.reshape(-1, 4)
    dx, dy = seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1]
    length = np.hypot(dx, dy)
    keep = length >= 25
    ang = (np.degrees(np.arctan2(-dy[keep], dx[keep])) + 180) % 180  # 화면 위쪽이 +
    L = length[keep]
    out = {}
    for name, lo, hi in [("수평", 0, 3), ("수평2", 177, 180), ("수직", 87, 93)]:
        out[name] = float(L[(ang >= lo) & (ang <= hi)].sum())
    tot = float(L.sum())
    # 지면 축 후보: 15~45°, 135~165°
    res = {}
    for side, lo, hi in [("우상향", 15, 45), ("좌상향", 135, 165)]:
        m = (ang >= lo) & (ang <= hi)
        a = ang[m] if side == "우상향" else 180 - ang[m]
        wts = L[m]
        if wts.sum() == 0:
            res[side] = None
            continue
        hist, edges = np.histogram(a, bins=np.arange(15, 45.25, 0.5), weights=wts)
        k = int(np.argmax(hist))
        peak = (edges[k] + edges[k + 1]) / 2
        near = (a >= peak - 1.5) & (a <= peak + 1.5)
        res[side] = (round(float(np.average(a[near], weights=wts[near])), 2), round(float(wts[near].sum() / tot * 100), 1))
    return res, round((out["수평"] + out["수평2"]) / tot * 100, 1), round(out["수직"] / tot * 100, 1)


def main():
    print("| ref | 우상향 축(°, 길이비%) | 좌상향 축(°, 길이비%) | 수평% | 수직% | 판정 |")
    for arg in sys.argv[1:]:
        slug, path = arg.split("=", 1)
        r = measure(path)
        if r is None:
            print(f"| {slug} | - | - | - | - | 선분 없음 |")
            continue
        res, hz, vt = r
        a1 = res.get("우상향")
        a2 = res.get("좌상향")
        vals = [v[0] for v in (a1, a2) if v]
        verdict = "기타"
        if vals and all(abs(v - 30) <= 1.2 for v in vals):
            verdict = "진짜 등각(30°)"
        elif vals and all(abs(v - 26.57) <= 1.2 for v in vals):
            verdict = "2:1 등각 계열(26.6°)"
        print(f"| {slug} | {a1} | {a2} | {hz} | {vt} | {verdict} |")


if __name__ == "__main__":
    main()
