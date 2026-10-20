"""패널 제목·메인 타이틀 글자 띠 높이(수평 글줄). 행 투영으로 가장 큰 띠. 단위 mm."""
import json, sys
import cv2, numpy as np
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from ra_common import *
T = {
 "203x-seoul": [("SUMMARY(패널 제목, 고해상)", (48, 70, 125, 94)), ("Symbol(패널 소제목, 고해상)", (48, 196, 100, 214)),
                ("SEOUL(메인 타이틀)", (345, 92, 655, 220)), ("CITY WHERE PAST AND PRESENT COEXIST(부제)", (342, 224, 662, 252)),
                ("PERSON IN SEOUL(하단 패널 제목, 고해상)", (48, 1176, 165, 1198))],
 "203x-london": [("HISTORY(패널 제목, 고해상)", (48, 52, 98, 72)), ("WILLIAM MORRIS(패널 제목, 고해상)", (48, 246, 115, 263)),
                 ("LONDON(메인 타이틀)", (440, 105, 830, 172)), ("HARRY BECK(하단 패널 제목, 고해상)", (48, 1280, 128, 1298))],
 "203x-berlin": [("CITY INFORMATION(패널 제목, 고해상)", (38, 40, 155, 64)), ("FAMOUS CULTURE AREA(패널 제목, 고해상)", (38, 178, 180, 202)),
                 ("Berlin(메인 타이틀)", (405, 118, 600, 190)), ("FAMOUS FOOD(하단 패널 제목, 고해상)", (38, 1214, 125, 1240))],
}
MMV = 0.2121
out = {}
for ref, items in T.items():
    art = cv2.imread(str(composite_path(ref)))
    L = cv2.cvtColor(art, cv2.COLOR_BGR2LAB)
    res = []
    for name, (x0, y0, x1, y1) in items:
        sub = L[y0 * 2:y1 * 2, x0 * 2:x1 * 2].astype(np.float32)
        border = np.concatenate([sub[:2].reshape(-1, 3), sub[-2:].reshape(-1, 3), sub[:, :2].reshape(-1, 3), sub[:, -2:].reshape(-1, 3)])
        bg = np.median(border, 0)
        ink = np.linalg.norm(sub - bg, axis=2) > 28
        prof = ink.sum(1)
        on = prof > max(3, 0.12 * prof.max())
        ys = np.nonzero(on)[0]
        # 가장 긴 연속 띠
        best, cur, start = (0, 0, 0), 0, None
        for i, v in enumerate(on):
            if v and start is None: start = i
            if (not v or i == len(on) - 1) and start is not None:
                end = i if not v else i + 1
                if end - start > best[0]: best = (end - start, start, end)
                start = None
        res.append({"name": name, "band_mm": round(best[0] * MMV, 1)})
        print(ref, name, round(best[0] * MMV, 1), "mm")
    out[ref] = res
json.dump(out, open(WORK / "titlesize.json", "w"), ensure_ascii=False, indent=1)
