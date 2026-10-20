"""물 면 색 분할: 기준색(Lab)과의 거리로 마스크 -> 성분 분석 -> 시각화.
사용: ra_water.py <ref> <name> <thr> L,a,b [L,a,b ...]
출력: work/water_<ref>_<name>.png(덧그림), work/water_<ref>_<name>_mask.png, 성분 bbox(정규 단위)
"""
import sys, json
import cv2, numpy as np
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from ra_common import *
ref, name, thr = sys.argv[1], sys.argv[2], float(sys.argv[3])
refs = [np.array([float(v) for v in s.split(',')], np.float32) for s in sys.argv[4:]]
art = cv2.imread(str(composite_path(ref)))
small = cv2.resize(art, (1000, 1400), interpolation=cv2.INTER_AREA)
lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB).astype(np.float32)
d = np.min(np.stack([np.linalg.norm(lab - r, axis=2) for r in refs]), axis=0)
m = (d < thr).astype(np.uint8) * 255
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
n, lb, st, ce = cv2.connectedComponentsWithStats(m)
comps = []
for i in range(1, n):
    x, y, w, h, a = st[i]
    if a < 300:
        continue
    comps.append({"id": i, "bbox": [int(x), int(y), int(x + w), int(y + h)], "area": int(a)})
comps.sort(key=lambda c: -c["area"])
for c in comps[:25]:
    print(c)
ov = small.copy()
ov[m > 0] = (0.35 * ov[m > 0] + 0.65 * np.array([0, 0, 255])).astype(np.uint8)
for c in comps[:25]:
    x0, y0, x1, y1 = c["bbox"]
    cv2.rectangle(ov, (x0, y0), (x1, y1), (0, 255, 255), 1)
    cv2.putText(ov, str(c["id"]), (x0 + 2, y0 + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 2)
    cv2.putText(ov, str(c["id"]), (x0 + 2, y0 + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
cv2.imwrite(str(WORK / f"water_{ref}_{name}.png"), ov)
cv2.imwrite(str(WORK / f"water_{ref}_{name}_mask.png"), m)
np.save(str(WORK / f"water_{ref}_{name}_labels.npy"), lb)
json.dump(comps, open(WORK / f"water_{ref}_{name}.json", "w"))
