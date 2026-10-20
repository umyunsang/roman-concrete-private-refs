"""연속 지면 판 범위: 판 윗면·옆면 색 마스크의 최대 성분(오브젝트 전경과 합쳐 닫힘) 외곽."""
import sys, json
import cv2, numpy as np
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from ra_common import *
C = {"203x-seoul": [(212.5, 107.9, 134.5), (181.1, 106.9, 134.1), (187, 108, 134), (226, 121, 130)],
     "203x-london": [(167.0, 121.1, 127.4), (146.5, 121.4, 125.6), (159, 120, 124), (148, 121, 129)]}
out = {}
for ref, cols in C.items():
    art = cv2.imread(str(composite_path(ref)))
    img = cv2.resize(art, (1000, 1400), interpolation=cv2.INTER_AREA)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
    d = np.min(np.stack([np.linalg.norm(lab - np.array(c, np.float32), axis=2) for c in cols]), 0)
    m = (d < 7).astype(np.uint8)
    fg = (cv2.imread(str(WORK / f"fg_{ref}.png"), 0) > 0).astype(np.uint8)
    # 패널·타이틀 영역 제외
    ink = json.load(open(WORK / "ink.json"))[ref]
    for b in [ink["title"]["bbox"], ink["footer"]["bbox"]] + [p["bbox"] for p in ink["panels"]]:
        m[b[1]:b[3], b[0]:b[2]] = 0
    u = cv2.morphologyEx(m | fg, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lb, st, _ = cv2.connectedComponentsWithStats(u)
    big = np.argmax(st[1:, cv2.CC_STAT_AREA]) + 1
    x, y, w, h, a = st[big]
    pm = (lb == big) & (m > 0)
    ys, xs = np.nonzero(pm)
    # 왼쪽·오른쪽 변 블리드 여부: x=0, x=999 열의 판 화소 세로 범위
    def edge(col):
        yy = np.nonzero(pm[:, col])[0]
        return [int(yy.min()), int(yy.max())] if len(yy) else None
    out[ref] = {"plate_bbox_u": [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1],
                "left_edge_y": edge(0), "right_edge_y": edge(999), "plate_px_pct_of_poster": round(float(pm.mean() * 100), 1)}
    print(ref, out[ref])
json.dump(out, open(WORK / "plate.json", "w"), ensure_ascii=False, indent=1)
