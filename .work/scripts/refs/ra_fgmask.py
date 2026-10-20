"""전역 GrabCut(개정): 타이틀·패널·푸터는 테두리 중앙값 색으로 칠해 확실 배경,
히어로의 타이틀 침범부(keep 다각형)는 원본 화소를 살려 확실 전경, 유리 탑 등은 sure_fg 다각형.
오브젝트 상자 안 = 아마 전경, 밖 = 확실 배경. 출력: work/fg_<ref>.png, work/fgov_<ref>.png
"""
import sys, json
import cv2, numpy as np
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from ra_common import *
from ra_objects_def import OBJS

INK = json.load(open(WORK / "ink.json"))
KEEP = {  # 타이틀 침범부(원본 유지 + 확실 전경)
 "203x-london": [[(375, 40), (388, 40), (390, 86), (428, 200), (333, 200), (374, 86)]],
 "203x-berlin": [[(626, 110), (640, 110), (645, 218), (621, 218)]],
 "203x-seoul": [],
}
SURE_FG = {
 "203x-seoul": [
  [(740, 525), (758, 525), (798, 700), (822, 925), (720, 925), (706, 700), (720, 600)],   # 롯데월드타워 몸체
  [(525, 700), (595, 700), (598, 920), (505, 920), (505, 725)],                          # 무역센터 몸체
  [(632, 420), (658, 420), (658, 690), (632, 690)],                                      # N서울타워 기둥
 ],
 "203x-london": [
  [(555, 318), (588, 352), (603, 450), (594, 556), (566, 596), (522, 588), (510, 450), (522, 352)],  # 거킨
 ],
 "203x-berlin": [
  [(396, 380), (414, 380), (444, 452), (444, 568), (366, 568), (356, 452)],  # 카이저 빌헬름 교회
 ],
}

def fill_rect_bg(img, rect):
    x0, y0, x1, y1 = rect
    sub = img[y0:y1, x0:x1]
    border = np.concatenate([sub[:2].reshape(-1, 3), sub[-2:].reshape(-1, 3), sub[:, :2].reshape(-1, 3), sub[:, -2:].reshape(-1, 3)])
    img[y0:y1, x0:x1] = np.median(border, axis=0).astype(np.uint8)

for ref in (sys.argv[1:] or list(OBJS)):
    art = cv2.imread(str(composite_path(ref)))
    orig = cv2.resize(art, (1000, 1400), interpolation=cv2.INTER_AREA)
    img = orig.copy()
    H, W = img.shape[:2]
    z = INK[ref]
    paint = [z["title"]["bbox"], z["footer"]["bbox"]] + [p["bbox"] for p in z["panels"]]
    for r in paint:
        fill_rect_bg(img, r)
    keepm = np.zeros((H, W), np.uint8)
    for poly in KEEP[ref]:
        cv2.fillPoly(keepm, [np.array(poly, np.int32)], 1)
    img[keepm > 0] = orig[keepm > 0]
    m = np.full((H, W), cv2.GC_BGD, np.uint8)
    for name, kind, (x0, y0, x1, y1), core in OBJS[ref]:
        m[max(0, y0):min(H, y1), max(0, x0):min(W, x1)] = cv2.GC_PR_FGD
    for r in paint:
        x0, y0, x1, y1 = r
        m[y0:y1, x0:x1] = cv2.GC_BGD
    sfg = np.zeros((H, W), np.uint8)
    for poly in SURE_FG[ref]:
        cv2.fillPoly(sfg, [np.array(poly, np.int32)], 1)
    m[(sfg > 0) | (keepm > 0)] = cv2.GC_FGD
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(img, m, None, bgd, fgd, 10, cv2.GC_INIT_WITH_MASK)
    fg = ((m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD)).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lb, st, _ = cv2.connectedComponentsWithStats(fg)
    keep = np.zeros_like(fg)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] >= 60:
            keep[lb == i] = 1
    cv2.imwrite(str(WORK / f"fg_{ref}.png"), keep * 255)
    ov = orig.copy()
    ov[keep > 0] = (0.4 * ov[keep > 0] + 0.6 * np.array([40, 40, 230])).astype(np.uint8)
    for name, kind, (x0, y0, x1, y1), core in OBJS[ref]:
        cv2.rectangle(ov, (x0, y0), (x1, y1), (0, 220, 255) if core else (255, 255, 0), 1)
    cv2.imwrite(str(WORK / f"fgov_{ref}.png"), ov)
    print(ref, "FG px", int(keep.sum()))
