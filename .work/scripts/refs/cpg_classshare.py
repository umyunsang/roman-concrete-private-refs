"""k-평균 군집 번호(npy)를 의미 부류로 묶어 영역별 비율을 낸다 (2026-10-18).
사용: uv run --no-project --with numpy python -I cpg_classshare.py <labels.npy> <부류정의.json> x0,y0,x1,y1 [...]
부류정의: {"부류명": [군집번호, ...], ...}
"""
import json
import sys
import numpy as np
lab = np.load(sys.argv[1])
cls = json.load(open(sys.argv[2]))
for a in sys.argv[3:]:
    x0, y0, x1, y1 = map(int, a.split(","))
    roi = lab[y0:y1, x0:x1]
    n = roi.size
    out = []
    for k, ids in cls.items():
        out.append((k, np.isin(roi, ids).sum() / n * 100))
    print(a, " | ".join(f"{k} {v:.1f}%" for k, v in out))
