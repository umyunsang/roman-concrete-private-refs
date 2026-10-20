"""203X 상세 타일(1000x93x)을 전체 이미지(1000x14xx)에 정합한다 (2026-10-18, refs-analysis 3묶음).

- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- 타일은 원본(2000x28xx)을 2x3으로 쪼갠 조각이라고 보고, 0.5배로 줄여 전체 이미지에서 템플릿 매칭으로 자리를 찾는다.
- 사용: uv run --no-project --with opencv-python-headless --with numpy python -I cpg_register_tiles.py <전체> <타일1> [<타일2> ...]
- 출력: 타일마다 (x0, y0) 전체 이미지 좌표, 배율, 일치도
"""
import sys

import cv2
import numpy as np


def main() -> None:
    full = cv2.imread(sys.argv[1], cv2.IMREAD_GRAYSCALE)
    H, W = full.shape
    print(f"full {W}x{H}")
    for p in sys.argv[2:]:
        t = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
        best = None
        for s in np.arange(0.48, 0.521, 0.002):
            ts = cv2.resize(t, (int(round(t.shape[1] * s)), int(round(t.shape[0] * s))), interpolation=cv2.INTER_AREA)
            if ts.shape[0] > H or ts.shape[1] > W:
                continue
            r = cv2.matchTemplate(full, ts, cv2.TM_CCOEFF_NORMED)
            _, mx, _, loc = cv2.minMaxLoc(r)
            if best is None or mx > best[0]:
                best = (mx, s, loc, ts.shape[1], ts.shape[0])
        mx, s, loc, tw, th = best
        print(f"{p.split('/')[-1]}: tile {t.shape[1]}x{t.shape[0]} scale {s:.3f} at ({loc[0]},{loc[1]}) size {tw}x{th} score {mx:.4f}")


if __name__ == "__main__":
    main()
