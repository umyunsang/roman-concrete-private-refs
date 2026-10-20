"""지도 영역의 주요 색 군집(k-평균, Lab) -> 바탕·지면·물 색 정의용."""
import sys, json
import cv2, numpy as np
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from ra_common import *

REG = {"203x-seoul": (0, 250, 1000, 1170), "203x-london": (0, 180, 1000, 1200), "203x-berlin": (0, 220, 1000, 1350)}
out = {}
for ref, (x0, y0, x1, y1) in REG.items():
    art = cv2.imread(str(composite_path(ref)))
    sub = art[y0 * 2:y1 * 2:4, x0 * 2:x1 * 2:4]
    lab = cv2.cvtColor(sub, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
    K = 14
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.5)
    _, lbl, cen = cv2.kmeans(lab, K, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    cnt = np.bincount(lbl.ravel(), minlength=K)
    order = np.argsort(-cnt)
    rows = []
    for i in order:
        c = cen[i].astype(np.uint8).reshape(1, 1, 3)
        bgr = cv2.cvtColor(c, cv2.COLOR_LAB2BGR)[0, 0]
        hexc = "#%02x%02x%02x" % (bgr[2], bgr[1], bgr[0])
        rows.append({"hex": hexc, "lab": [round(float(v), 1) for v in cen[i]], "share": round(float(cnt[i] / cnt.sum() * 100), 1)})
    out[ref] = rows
    print(ref)
    for r in rows:
        print("  ", r)
json.dump(out, open(WORK / "palette.json", "w"), ensure_ascii=False, indent=1)
