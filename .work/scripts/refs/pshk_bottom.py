"""지도 맨 아래 내용 행 찾기(판 앞 모서리·블리드 확인용). 입력 이미지는 읽기만 한다. (2026-10-18)"""
import numpy as np
from pshk_common import poster, lab
for rid, xs, y0 in [("203x-paris", (470, 520), 1250), ("203x-shanghai", (40, 420), 1150), ("203x-hongkong", (0, 60), 1150), ("203x-hongkong", (880, 1000), 1100)]:
    img = poster(rid); L = lab(img)
    ref = np.median(L[1380:1395, 400:600].reshape(-1, 3), axis=0)
    sub = L[y0:1342, xs[0]:xs[1]]
    d = np.sqrt(((sub - ref) ** 2).sum(-1))
    rows = np.where((d > 12).mean(1) > 0.05)[0]
    print(rid, xs, "바닥 기준색 Lab", ref.round(1), "마지막 내용 행", y0 + rows.max() if len(rows) else None)
