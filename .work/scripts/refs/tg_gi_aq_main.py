"""Gismondi 사진별 수도교 주성분(가장 큰 벽돌색 선 성분)만의 중심선 길이와 콜로세움 최소 거리 (2026-10-18). 입력 이미지는 읽기만 한다.
사용: python -I tg_gi_aq_main.py <사진 폴더>
"""
import sys
import cv2
import numpy as np
SRC = sys.argv[1]
CFG = {"D": ("Vue_maquette_de_Gismondi_JP_Dalbera.jpg", (6, 11, 112, 130), (0.534, 0.4005, 0.611, 0.500)),
       "R": ("Model_of_imperial_Rome_Velian_Colosseum_Raddato.jpg", (9, 18, 100, 120), (0.4574, 0.6011, 0.6374, 0.8186)),
       "E": ("RomemodelEUR3.jpg", (10, 16, 92, 115), (0.6506, 0.2094, 0.7297, 0.2804))}
def skeleton(mask):
    sk = np.zeros_like(mask); el = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3)); m = mask.copy()
    while True:
        er = cv2.erode(m, el); op = cv2.dilate(er, el); sk |= (m & ~op); m = er
        if not m.any(): break
    return sk
for k, (fn, th, cb) in CFG.items():
    img = cv2.imread(f"{SRC}/{fn}"); H, W = img.shape[:2]; s = 1600 / W
    img = cv2.resize(img, (1600, int(H * s)), interpolation=cv2.INTER_AREA); h, w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV); hh, ss, vv = [hsv[..., i].astype(int) for i in range(3)]
    aq = ((hh >= th[0]) & (hh <= th[1]) & (ss >= th[2]) & (vv >= th[3])).astype(np.uint8) * 255
    aq = cv2.morphologyEx(aq, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    aq = cv2.morphologyEx(aq, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    n, L, st, _ = cv2.connectedComponentsWithStats(aq, 8)
    i = 1 + int(np.argmax(st[1:, 4]))
    m = (L == i).astype(np.uint8)
    sk = skeleton(m)
    ys, xs = np.nonzero(m)
    cx, cy = (cb[0] + cb[2]) / 2 * w, (cb[1] + cb[3]) / 2 * h
    cw = (cb[2] - cb[0]) * w
    x0, y0, bw, bh, a = st[i]
    print(f"{k}: 주성분 상자 ({x0/w:.3f}, {y0/h:.3f}, {(x0+bw)/w:.3f}, {(y0+bh)/h:.3f}), 중심선 길이/사진 폭 {sk.sum()/w:.2f}, "
          f"콜로세움 중심까지 최소 거리 {np.min(np.hypot(xs-cx, ys-cy))/cw:.2f} 콜로세움 폭, 화소 비율 {m.mean()*100:.2f}%")
