"""행·열 색 프로파일과 지배 색(k-평균)을 뽑는다 (2026-10-18, refs-analysis 3묶음).

- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- 사용: uv run --no-project --with opencv-python-headless --with numpy python -I cpg_profile.py <이미지> <k> [x0 y0 x1 y1]
- 출력: 지배 색 k개(비율·RGB), 50px 간격 행마다 각 지배 색 비율
"""
import sys

import cv2
import numpy as np


def main() -> None:
    img = cv2.imread(sys.argv[1])
    k = int(sys.argv[2])
    H, W = img.shape[:2]
    if len(sys.argv) > 3:
        x0, y0, x1, y1 = map(int, sys.argv[3:7])
    else:
        x0, y0, x1, y1 = 0, 0, W, H
    roi = img[y0:y1, x0:x1]
    Z = roi.reshape(-1, 3).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    cv2.setRNGSeed(7)
    _, lab, cen = cv2.kmeans(Z, k, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    lab = lab.reshape(roi.shape[:2])
    order = np.argsort(-np.bincount(lab.ravel(), minlength=k))
    print("지배 색(비율%, RGB hex):")
    for i, c in enumerate(order):
        b, g, r = cen[c]
        print(f"  c{i}: {np.mean(lab == c) * 100:5.1f}%  #{int(r):02x}{int(g):02x}{int(b):02x}")
    print("행 프로파일(행 y: 각 색 %):")
    for y in range(0, roi.shape[0], 25):
        row = lab[y]
        s = " ".join(f"{np.mean(row == c) * 100:4.0f}" for c in order)
        print(f"  y={y + y0:5d}: {s}")


if __name__ == "__main__":
    main()
