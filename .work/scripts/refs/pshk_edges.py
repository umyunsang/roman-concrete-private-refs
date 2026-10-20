"""땅 마스크의 열별 최하단 행(판 앞 모서리) 찾기. 입력은 분석 산출물만 읽는다. (2026-10-18)"""
import sys
import cv2
import numpy as np
from pshk_common import WORK
rid, name = sys.argv[1], sys.argv[2]
m = cv2.imread(f"{WORK}/{rid}_{name}_mask.png", 0) > 0
n, lb, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8))
order = 1 + np.argsort(-st[1:, 4])
for k in order[:3]:
    comp = lb == k
    xs = [int(v) for v in sys.argv[3].split(",")]
    out = []
    for x in xs:
        ys = np.where(comp[:, x])[0]
        out.append((x, int(ys.min()) if len(ys) else None, int(ys.max()) if len(ys) else None))
    print(f"성분 {k} 면적 {st[k,4]} bbox x{st[k,0]}~{st[k,0]+st[k,2]} y{st[k,1]}~{st[k,1]+st[k,3]}: (x, 위, 아래) {out}")
