"""라벨 영역의 글줄 기준선 방향(+30° 우상향 / -30° 우하향 / 0° 수평)을 판정한다 (2026-10-18). 입력 이미지는 읽기만 한다.

- 방법: 영역을 후보 각도마다 회전해 글줄을 수평으로 만든 뒤, 잉크 행 투영의 '띠 선명도'(투영값 분산/평균²)를 비교한다.
  글줄이 실제로 그 각도면 행 투영이 줄 단위로 끊겨 분산이 커진다.
- 각도 규약: 화면 위쪽이 +. +30 = 오른쪽으로 올라가는 글줄, -30 = 오른쪽으로 내려가는 글줄.
- 사용: uv run --no-project --with opencv-python-headless --with numpy python -I cpg_textdir.py <이미지> 이름=x0,y0,x1,y1 [...]
"""
import sys

import cv2
import numpy as np


def score(gray, valid, ang):
    h, w = gray.shape
    # 화면 위쪽 + 규약의 글줄 각 ang 을 수평으로: OpenCV 각도(반시계 +)로 -ang 만큼 돌리면 된다
    M = cv2.getRotationMatrix2D((w / 2, h / 2), -ang, 1.0)
    cos, sin = abs(M[0, 0]), abs(M[0, 1])
    nw, nh = int(h * sin + w * cos) + 2, int(h * cos + w * sin) + 2
    M[0, 2] += nw / 2 - w / 2
    M[1, 2] += nh / 2 - h / 2
    g = cv2.warpAffine(gray, M, (nw, nh), borderValue=255)
    v = cv2.warpAffine(valid.astype(np.uint8), M, (nw, nh), borderValue=0) > 0
    bg = np.median(g[v]) if v.any() else 255
    ink = (g < bg - 40) & v
    prof = ink.sum(1) / np.maximum(v.sum(1), 1)
    rows = v.sum(1) > 5
    p = prof[rows]
    if p.size < 5 or p.mean() == 0:
        return 0.0
    return float(p.var() / (p.mean() ** 2))


def main() -> None:
    img = cv2.imread(sys.argv[1], cv2.IMREAD_GRAYSCALE)
    for a in sys.argv[2:]:
        name, box = a.split("=")
        x0, y0, x1, y1 = map(int, box.split(","))
        roi = img[y0:y1, x0:x1]
        valid = np.ones_like(roi, bool)
        s = {ang: score(roi, valid, ang) for ang in (-30, 0, 30)}
        best = max(s, key=s.get)
        print(f"{name}: " + " ".join(f"{k:+d}°={v:.2f}" for k, v in s.items()) + f" → 기준선 {best:+d}°")


if __name__ == "__main__":
    main()
