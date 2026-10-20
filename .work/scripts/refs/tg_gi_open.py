"""Gismondi 모형 사진의 열린 면(강·경기장 바닥·넓은 광장) 비율을 에지 밀도로 추정한다 (2026-10-18). 입력 이미지는 읽기만 한다.
- 기준: 테베레·대전차경기장 다각형 안(열린 면 표본)과 도시 조직 표본 상자 안의 에지 밀도 중앙값의 기하평균을 임계로 쓴다.
- 나무: 색상 H 60~125, 채도 12~95, 명도 55~175(D·E 표본 기준). R 사진은 푸른 색조라 나무 색 분리를 하지 않는다.
사용: python -I tg_gi_open.py <사진 폴더>
"""
import sys
import cv2
import numpy as np
sys.path.insert(0, '')
SRC = sys.argv[1]
CFG = {
    "D": ("Vue_maquette_de_Gismondi_JP_Dalbera.jpg",
          [(0, 0.10), (0.19, 0.10), (0.20, 0.06), (0.30, 0.04), (0.35, 0.02), (0.42, 0.015), (0.55, 0.02), (0.70, 0.03), (0.78, 0.04), (0.80, 0.07), (0.85, 0.10), (0.90, 0.13), (0.95, 0.17), (1.0, 0.21), (1, 1), (0, 1)],
          [[(0, 0.56), (0.09, 0.56), (0.07, 0.65), (0, 0.70)], [(0.25, 0.70), (0.30, 0.70), (0.38, 0.79), (0.33, 0.80)]],
          [(0.30, 0.20, 0.40, 0.30), (0.75, 0.40, 0.85, 0.50)], True),
    "R": ("Model_of_imperial_Rome_Velian_Colosseum_Raddato.jpg", [(0, 0), (1, 0), (1, 1), (0, 1)],
          [[(0.45, 0.02), (0.60, 0.02), (0.60, 0.08), (0.45, 0.09)], [(0.15, 0.30), (0.40, 0.21), (0.41, 0.23), (0.16, 0.33)]],
          [(0.80, 0.70, 0.95, 0.85), (0.05, 0.10, 0.20, 0.20)], False),
    "E": ("RomemodelEUR3.jpg", [(0, 0), (1, 0), (1, 1), (0, 1)],
          [[(0.22, 0.27), (0.26, 0.29), (0.20, 0.40), (0.15, 0.38)], [(0.37, 0.37), (0.50, 0.44), (0.49, 0.46), (0.36, 0.39)]],
          [(0.30, 0.65, 0.40, 0.75), (0.50, 0.10, 0.60, 0.15)], True),
}
for key, (fn, model, opens, builts, tree_ok) in CFG.items():
    img = cv2.imread(f"{SRC}/{fn}"); H, W = img.shape[:2]
    s = 1600 / W; img = cv2.resize(img, (1600, int(H * s)), interpolation=cv2.INTER_AREA); h, w = img.shape[:2]
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    e = (cv2.Canny(g, 50, 120) > 0).astype(np.float32)
    d = cv2.boxFilter(e, -1, (25, 25))
    def pmask(poly):
        m = np.zeros((h, w), np.uint8); cv2.fillPoly(m, [np.array([[int(x*w), int(y*h)] for x, y in poly], np.int32)], 1); return m.astype(bool)
    mm = pmask(model)
    o = np.median(np.concatenate([d[pmask(p)] for p in opens]))
    b = np.median(np.concatenate([d[int(y0*h):int(y1*h), int(x0*w):int(x1*w)].ravel() for x0, y0, x1, y1 in builts]))
    thr = np.sqrt(max(o, 1e-3) * b)
    open_frac = float(((d < thr) & mm).sum() / mm.sum() * 100)
    line = f"{key}: 열린 면 표본 에지 밀도 {o:.3f}, 도시 조직 표본 {b:.3f}, 임계 {thr:.3f} → 열린 면 {open_frac:.1f}% / 건물·조직 {100-open_frac:.1f}% (모형 면 대비)"
    if tree_ok:
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV); hh, ss, vv = [hsv[..., i].astype(int) for i in range(3)]
        tree = (hh >= 60) & (hh <= 125) & (ss >= 12) & (ss <= 95) & (vv >= 55) & (vv <= 175)
        tree = cv2.morphologyEx(tree.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)).astype(bool)
        line += f", 나무 색 {float((tree & mm).sum() / mm.sum() * 100):.1f}%"
        vis = img.copy(); vis[tree & mm] = (0, 200, 0); vis[(d < thr) & mm & ~tree] = (255, 120, 0)
        cv2.imwrite(f"/Users/um-yunsang/roman-concrete-private-refs/.work/out/refs-analysis/work_tg/gi_{key}_open.png", vis)
    print(line)
