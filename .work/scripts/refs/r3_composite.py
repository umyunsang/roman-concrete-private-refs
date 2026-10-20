"""정규 좌표 ×2(2000×2800) 합성본을 만든다. 바탕은 전체 포스터 확대본, 그 위에 고해상 타일 3장을 원 해상도로 붙인다.

출력: refs-analysis/<ref>_comp2x.png, <ref>_hires_mask.png(고해상 커버리지)
"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/refs")
from r3_common import OUT, REFS, imread, load_json, load_norm  # noqa: E402

reg = load_json("r3_register.json")
for ref_id, spec in REFS.items():
    base, _ = load_norm(ref_id, scale=2)  # 2000×2800
    cov = np.zeros(base.shape[:2], np.uint8)
    for tid, t in reg[ref_id]["tiles"].items():
        im = imread(t["file"])
        x0, y0, x1, y1 = [v * 2 for v in t["box_norm1000"]]
        w, h = x1 - x0, y1 - y0
        im = cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA if im.shape[1] > w else cv2.INTER_CUBIC)
        base[y0:y1, x0:x1] = im
        cov[y0:y1, x0:x1] = 255
    cv2.imwrite(os.path.join(OUT, f"{ref_id}_comp2x.png"), base)
    cv2.imwrite(os.path.join(OUT, f"{ref_id}_hires_mask.png"), cov)
    print(ref_id, base.shape, "hires %.1f%%" % (100 * (cov > 0).mean()))
