"""지도 무대 영역을 k-평균으로 색 분할하고, 군집별 거짓 색 이미지와 범례를 만든다 (2026-10-18).

- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- 사용: uv run --no-project --with opencv-python-headless --with numpy --with pillow python -I cpg_kmeans_map.py \
        <이미지> <k> <x0> <y0> <x1> <y1> <출력접두사>
- 출력: <접두사>_labels.npy(군집 번호, 전체 이미지 크기, 영역 밖 -1), <접두사>_false.png, 표준 출력에 군집 표
"""
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
PAL = [(230, 25, 75), (60, 180, 75), (255, 225, 25), (0, 130, 200), (245, 130, 48), (145, 30, 180), (70, 240, 240),
       (240, 50, 230), (210, 245, 60), (250, 190, 212), (0, 128, 128), (220, 190, 255), (170, 110, 40), (255, 250, 200),
       (128, 0, 0), (170, 255, 195), (128, 128, 0), (255, 215, 180), (0, 0, 128), (128, 128, 128)]


def main() -> None:
    path, k = sys.argv[1], int(sys.argv[2])
    x0, y0, x1, y1 = map(int, sys.argv[3:7])
    pre = sys.argv[7]
    img = cv2.imread(path)
    H, W = img.shape[:2]
    roi = img[y0:y1, x0:x1]
    lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.3)
    cv2.setRNGSeed(11)
    _, lb, cen = cv2.kmeans(lab, k, None, crit, 4, cv2.KMEANS_PP_CENTERS)
    lb = lb.reshape(roi.shape[:2])
    full = -np.ones((H, W), np.int16)
    full[y0:y1, x0:x1] = lb
    np.save(pre + "_labels.npy", full)
    cen_bgr = cv2.cvtColor(cen.reshape(1, -1, 3).astype(np.uint8), cv2.COLOR_LAB2BGR).reshape(-1, 3)
    order = np.argsort(-np.bincount(lb.ravel(), minlength=k))
    print("군집 | 비율% | RGB | 무게중심(x,y) | 세로 범위(5~95%)")
    for c in order:
        ys, xs = np.where(lb == c)
        b, g, r = cen_bgr[c]
        print(f"c{c:02d} | {np.mean(lb == c) * 100:5.1f} | #{r:02x}{g:02x}{b:02x} | ({xs.mean() + x0:.0f},{ys.mean() + y0:.0f}) | "
              f"{np.percentile(ys, 5) + y0:.0f}~{np.percentile(ys, 95) + y0:.0f}")
    fc = np.zeros((*lb.shape, 3), np.uint8)
    for c in range(k):
        fc[lb == c] = PAL[c % len(PAL)]
    pil = Image.fromarray(fc)
    leg = Image.new("RGB", (pil.width, 30 * ((k + 3) // 4)), (255, 255, 255))
    d = ImageDraw.Draw(leg)
    f = ImageFont.truetype(FONT, 16)
    for i, c in enumerate(range(k)):
        cx, cy = (i % 4) * (pil.width // 4), (i // 4) * 30
        d.rectangle([cx + 4, cy + 4, cx + 26, cy + 26], fill=PAL[c % len(PAL)])
        b, g, r = cen_bgr[c]
        d.rectangle([cx + 30, cy + 4, cx + 52, cy + 26], fill=(int(r), int(g), int(b)))
        d.text((cx + 58, cy + 6), f"c{c:02d}", fill=(0, 0, 0), font=f)
    out = Image.new("RGB", (pil.width, pil.height + leg.height), (255, 255, 255))
    out.paste(pil, (0, 0))
    out.paste(leg, (0, pil.height))
    out.save(pre + "_false.png")
    print("saved", pre + "_false.png")


if __name__ == "__main__":
    main()
