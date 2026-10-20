"""자금성 지도 라벨(세로 깃발판) 검출: 짙은 갈색(L<45, 22<a<42, 25<b<46; 원 해상도 타일 군집 31~38,31~35,35~38) 세로 직사각형 성분.

출력: fc_flags.json, fc_flags_dbg.png
"""
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/refs")
from r3_common import OUT, lab, load_norm  # noqa: E402

ref = "203x-forbiddencity"
im, _ = load_norm(ref, scale=2)  # 2000×2800 확대(타일 영역은 원 해상도 아님 → 합성본 사용)
comp = cv2.imread(os.path.join(OUT, f"{ref}_comp2x.png"))
L = lab(comp)
m = (L[..., 0] < 45) & (L[..., 1] > 22) & (L[..., 1] < 42) & (L[..., 2] > 25) & (L[..., 2] < 46)
m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 3), np.uint8))
n, lb, st, cen = cv2.connectedComponentsWithStats(m, connectivity=8)
flags = []
for i in range(1, n):
    x, y, w, h, a = st[i]
    # N 좌표(÷2)
    wN, hN = w / 2, h / 2
    if 6 <= wN <= 22 and 16 <= hN <= 70 and hN >= 1.6 * wN and a / (w * h) > 0.45:
        cx, cy = (x + w / 2) / 2, (y + h / 2) / 2
        flags.append({"box_N": [round(x / 2), round(y / 2), round((x + w) / 2), round((y + h) / 2)], "wh_N": [round(wN, 1), round(hN, 1)]})
# 패널(연표·평면도·요약) 안의 갈색 머리띠 제외: 지도·모형 영역만
EXCL = [[35, 230, 500, 405], [35, 405, 180, 990], [38, 1008, 193, 1307], [39, 112, 268, 217], [728, 139, 970, 217], [478, 235, 978, 300]]
keep = []
for f in flags:
    x0, y0, x1, y1 = f["box_N"]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if any(a <= cx <= c and b <= cy <= d for a, b, c, d in EXCL):
        continue
    keep.append(f)
vis = comp.copy()
for f in keep:
    x0, y0, x1, y1 = [v * 2 for v in f["box_N"]]
    cv2.rectangle(vis, (x0 - 3, y0 - 3), (x1 + 3, y1 + 3), (255, 0, 255), 3)
cv2.imwrite(os.path.join(OUT, "fc_flags_dbg.png"), cv2.resize(vis, (1000, 1400), interpolation=cv2.INTER_AREA))
with open(os.path.join(OUT, "fc_flags.json"), "w", encoding="utf-8") as fh:
    json.dump({"n": len(keep), "flags": keep}, fh, ensure_ascii=False, indent=1)
hs = [f["wh_N"][1] for f in keep]
ws = [f["wh_N"][0] for f in keep]
print("갈색 세로 깃발 후보", len(keep), "높이 중앙값 N", np.median(hs) if hs else None, "폭 중앙값 N", np.median(ws) if ws else None)
