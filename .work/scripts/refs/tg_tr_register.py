"""Trabacchi 상세 사진(trabacchi_4·5)을 전체 지도(trabacchi_2)에 다중 배율 템플릿 정합한다 (2026-10-18).

- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- 상세 사진을 배율 s로 줄여 전체 지도에서 정규화 상관(TM_CCOEFF_NORMED) 최대 위치를 찾는다.
- 출력: 상세 사진이 덮는 전체 지도 정규 좌표 상자, 배율(상세 px / 전체 px), 일치도.
- 사용: python -I tg_tr_register.py <trabacchi_2.jpg> <detail.jpg> [...]
"""
import sys

import cv2
import numpy as np


def main():
    full = cv2.imread(sys.argv[1], cv2.IMREAD_GRAYSCALE)
    H, W = full.shape
    fullf = cv2.GaussianBlur(full, (3, 3), 0)
    for path in sys.argv[2:]:
        det = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        dh, dw = det.shape
        best = None
        for s in np.arange(0.05, 0.40, 0.005):
            tw, th = int(dw * s), int(dh * s)
            if tw < 30 or th < 30 or tw >= W or th >= H:
                continue
            t = cv2.resize(det, (tw, th), interpolation=cv2.INTER_AREA)
            r = cv2.matchTemplate(fullf, t, cv2.TM_CCOEFF_NORMED)
            _, mx, _, loc = cv2.minMaxLoc(r)
            if best is None or mx > best[0]:
                best = (mx, s, loc, tw, th)
        # 주변 배율 정밀화
        mx0, s0, _, _, _ = best
        for s in np.arange(s0 - 0.006, s0 + 0.006, 0.0005):
            tw, th = int(dw * s), int(dh * s)
            t = cv2.resize(det, (tw, th), interpolation=cv2.INTER_AREA)
            r = cv2.matchTemplate(fullf, t, cv2.TM_CCOEFF_NORMED)
            _, mx, _, loc = cv2.minMaxLoc(r)
            if mx > best[0]:
                best = (mx, s, loc, tw, th)
        mx, s, (x, y), tw, th = best
        print(f"{path.split('/')[-1]}: 일치도 {mx:.3f}, 배율 {s:.4f} (상세 1px = 전체 {s:.4f}px, 상세가 {1 / s:.2f}배 고해상)")
        print(f"   전체 지도 px 상자 ({x}, {y}, {x + tw}, {y + th}) → 정규 ({x / W:.4f}, {y / H:.4f}, {(x + tw) / W:.4f}, {(y + th) / H:.4f})")


if __name__ == "__main__":
    main()
