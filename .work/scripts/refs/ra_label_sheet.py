"""라벨 crop 모음(번호 붙임). 사용: ra_label_sheet.py <ref>"""
import sys
import cv2, numpy as np
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from ra_common import *
from ra_labels_def import LABELS
ref = sys.argv[1]
art = cv2.imread(str(composite_path(ref)))
hm = cv2.imread(str(mask_path(ref)), 0)
tiles = []
for k, (name, (x0, y0, x1, y1)) in enumerate(LABELS[ref]):
    pad = 18
    X0, Y0, X1, Y1 = max(0, (x0 - pad) * 2), max(0, (y0 - pad) * 2), min(2000, (x1 + pad) * 2), min(2800, (y1 + pad) * 2)
    c = art[Y0:Y1, X0:X1].copy()
    hi = hm[Y0:Y1, X0:X1].mean() > 127
    s = 300 / c.shape[0]
    c = cv2.resize(c, (int(c.shape[1] * s), 300), interpolation=cv2.INTER_CUBIC)
    cv2.rectangle(c, (0, 0), (c.shape[1] - 1, c.shape[0] - 1), (0, 160, 0) if hi else (0, 0, 220), 3)
    cv2.putText(c, f"{k+1}", (6, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 4)
    cv2.putText(c, f"{k+1}", (6, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    tiles.append(c)
rows, row, wsum = [], [], 0
for t in tiles:
    if wsum + t.shape[1] > 1900 and row:
        rows.append(row); row, wsum = [], 0
    row.append(t); wsum += t.shape[1] + 6
if row: rows.append(row)
W = max(sum(t.shape[1] + 6 for t in r) for r in rows)
sheet = np.full((len(rows) * 306, W, 3), 255, np.uint8)
for i, r in enumerate(rows):
    x = 0
    for t in r:
        sheet[i * 306:i * 306 + 300, x:x + t.shape[1]] = t; x += t.shape[1] + 6
cv2.imwrite(str(WORK / f"labels_{ref}.png"), sheet)
print(WORK / f"labels_{ref}.png", sheet.shape)
