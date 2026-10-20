"""피부색 덩어리(얼굴 후보)를 찾아 인물 수를 근사한다 (2026-10-18). 입력 이미지는 읽기만 한다.

- 만화 선화(검은 외곽선)라 얼굴이 외곽선으로 분리된다는 점을 이용한다.
- 피부색 조건: R>G>B, R>=120, 0.40<=B/R<=0.78, 0.62<=G/R<=0.86 (모래·석재·벽돌·옷 빨강을 거른다).
- 덩어리 크기·모양 조건: 면적 amin~amax px, 가로세로비 0.5~2.0, 채움비 >= 0.45.
- 사용: uv run --no-project --with opencv-python-headless --with numpy --with pillow python -I cpg_faces.py <이미지> <출력접두사> [amin amax]
- 출력: 얼굴 후보 수, 3x2 구역별 수, 후보 높이(px) 분포, 확인용 오버레이
"""
import json
import sys

import cv2
import numpy as np


def main() -> None:
    img = cv2.imread(sys.argv[1])
    pre = sys.argv[2]
    amin = int(sys.argv[3]) if len(sys.argv) > 3 else 250
    amax = int(sys.argv[4]) if len(sys.argv) > 4 else 2600
    H, W = img.shape[:2]
    b, g, r = [img[:, :, i].astype(np.float32) for i in range(3)]
    rr = np.maximum(r, 1)
    m = (r > g) & (g > b) & (r >= 120) & (b / rr >= 0.40) & (b / rr <= 0.78) & (g / rr >= 0.62) & (g / rr <= 0.86)
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lb, st, cen = cv2.connectedComponentsWithStats(m, connectivity=4)
    keep = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a < amin or a > amax:
            continue
        ar = w / max(h, 1)
        fill = a / max(w * h, 1)
        if 0.5 <= ar <= 2.0 and fill >= 0.45:
            keep.append((int(x), int(y), int(w), int(h), int(a), float(cen[i][0]), float(cen[i][1])))
    print("얼굴 후보 수:", len(keep), f"(면적 {amin}~{amax}px)")
    grid = np.zeros((2, 3), int)
    for k in keep:
        gx = min(2, int(k[5] / (W / 3)))
        gy = min(1, int(k[6] / (H / 2)))
        grid[gy, gx] += 1
    print("구역별(위 줄 / 아래 줄, 왼→오):", grid.tolist())
    hs = np.array([k[3] for k in keep]) if keep else np.zeros(1)
    print("후보 높이 px: 중앙값", float(np.median(hs)), "사분위", np.percentile(hs, [25, 75]).tolist())
    vis = img.copy()
    for (x, y, w, h, a, cx, cy) in keep:
        cv2.rectangle(vis, (x - 3, y - 3), (x + w + 3, y + h + 3), (255, 0, 255), 3)
    for i in range(1, 3):
        cv2.line(vis, (int(W * i / 3), 0), (int(W * i / 3), H), (0, 0, 255), 2)
    cv2.line(vis, (0, H // 2), (W, H // 2), (0, 0, 255), 2)
    cv2.imwrite(pre + "_faces.jpg", vis, [cv2.IMWRITE_JPEG_QUALITY, 85])
    json.dump({"count": len(keep), "grid": grid.tolist(), "boxes": [k[:4] for k in keep]}, open(pre + "_faces.json", "w"))
    print("saved", pre + "_faces.jpg")


if __name__ == "__main__":
    main()
