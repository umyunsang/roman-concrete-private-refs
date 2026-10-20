"""Trabacchi 1960 지도(trabacchi_2.jpg, 1500×1000)의 테두리·인셋 상자를 어두운 직선 투영으로 찾는다 (2026-10-18).

- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- 어두운 화소(회색 < 90)의 행·열 누적 비율에서 긴 수평·수직선을 찾는다.
- 사용: python -I tr_frame.py <trabacchi_2.jpg>
"""
import sys

import cv2
import numpy as np


def runs(mask_1d, min_len):
    """1차원 불리언 배열에서 길이 min_len 이상인 연속 구간 목록."""
    out, start = [], None
    for i, v in enumerate(list(mask_1d) + [False]):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start >= min_len:
                out.append((start, i - 1))
            start = None
    return out


def main():
    img = cv2.imread(sys.argv[1])
    H, W = img.shape[:2]
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    dark = (g < 90).astype(np.uint8)
    # 긴 수평선: 수평 열림(길이 120px)
    hk = cv2.getStructuringElement(cv2.MORPH_RECT, (120, 1))
    vk = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 80))
    hl = cv2.morphologyEx(dark, cv2.MORPH_OPEN, hk)
    vl = cv2.morphologyEx(dark, cv2.MORPH_OPEN, vk)
    print(f"이미지 {W}×{H}")
    print("[긴 수평선] y: (x 시작~끝, 길이)")
    for y in range(H):
        for a, b in runs(hl[y] > 0, 120):
            print(f"  y={y:4d} ({y / H:.4f})  x {a}~{b} ({a / W:.4f}~{b / W:.4f})  길이 {b - a + 1}")
    print("[긴 수직선] x: (y 시작~끝, 길이)")
    for x in range(W):
        for a, b in runs(vl[:, x] > 0, 80):
            print(f"  x={x:4d} ({x / W:.4f})  y {a}~{b} ({a / H:.4f}~{b / H:.4f})  길이 {b - a + 1}")


if __name__ == "__main__":
    main()
