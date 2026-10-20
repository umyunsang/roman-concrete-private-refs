"""바탕색 탐침: 좌·우 가장자리 띠의 행별 Lab 중앙값과 산포(무늬 대비)를 출력한다."""
import sys

import cv2
import numpy as np

sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/refs")
from r3_common import lab, load_norm  # noqa: E402

ref_id = sys.argv[1]
xs = [int(v) for v in sys.argv[2].split(",")] if len(sys.argv) > 2 else [0, 20, 980, 1000]
im, _ = load_norm(ref_id)
L = lab(im)
for y in range(0, 1400, 25):
    out = []
    for i in range(0, len(xs), 2):
        a, b = xs[i], xs[i + 1]
        p = L[max(0, y - 2):y + 3, a:b].reshape(-1, 3)
        med = np.median(p, 0)
        spread = np.percentile(np.linalg.norm(p - med, axis=1), 90)
        out.append("x%d-%d L%5.1f a%5.1f b%5.1f s%4.1f" % (a, b, med[0], med[1], med[2], spread))
    print("y%4d | " % y + " | ".join(out))
