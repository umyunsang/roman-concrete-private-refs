"""창(N 좌표) 안 비배경 화소의 꽉 찬 상자. 사용: r3_tightbox.py <ref> name:x0,y0,x1,y1 ...  (선택: --min 픽셀 수 행·열 문턱)"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/refs")
from r3_common import OUT, norm01, to_mm  # noqa: E402

ref = sys.argv[1]
m = cv2.imread(os.path.join(OUT, f"{ref}_nonbg.png"), 0) > 0
mn = 2
args = []
for a in sys.argv[2:]:
    if a.startswith("--min="):
        mn = int(a[6:])
    else:
        args.append(a)
for a in args:
    name, b = a.split(":")
    x0, y0, x1, y1 = [int(v) for v in b.split(",")]
    sub = m[y0:y1, x0:x1]
    rows = np.nonzero(sub.sum(1) >= mn)[0]
    cols = np.nonzero(sub.sum(0) >= mn)[0]
    if len(rows) == 0:
        print(name, "없음")
        continue
    box = [x0 + int(cols.min()), y0 + int(rows.min()), x0 + int(cols.max()) + 1, y0 + int(rows.max()) + 1]
    fill = sub.mean()
    print("%-28s N %s  01 %s  mm %s  wh_mm %.1f×%.1f  fill %.2f" % (name, box, norm01(box), to_mm(box), (box[2] - box[0]) * 0.42, (box[3] - box[1]) * 594 / 1400, fill))
