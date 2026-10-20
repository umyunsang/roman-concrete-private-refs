"""정규 좌표 상자 안 화소를 k-평균으로 묶어 군집 중심색(RGB·HSV)과 비율을 출력한다 (2026-10-18). 입력 이미지는 읽기만 한다.
사용: python -I tg_kmeans.py <이미지> <k> <x0> <y0> <x1> <y1> [표본 수=200000]
"""
import sys
import cv2
import numpy as np
img = cv2.imread(sys.argv[1]); H, W = img.shape[:2]
k = int(sys.argv[2]); x0, y0, x1, y1 = (float(v) for v in sys.argv[3:7])
ns = int(sys.argv[7]) if len(sys.argv) > 7 else 200000
c = img[int(y0*H):int(y1*H), int(x0*W):int(x1*W)]
lab = cv2.cvtColor(c, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
rng = np.random.default_rng(0)
idx = rng.choice(len(lab), min(ns, len(lab)), replace=False)
crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.5)
_, lbl, cen = cv2.kmeans(lab[idx], k, None, crit, 4, cv2.KMEANS_PP_CENTERS)
cnt = np.bincount(lbl.ravel(), minlength=k) / len(idx)
for i in np.argsort(-cnt):
    L = cen[i].reshape(1, 1, 3).astype(np.uint8)
    bgr = cv2.cvtColor(L, cv2.COLOR_LAB2BGR)[0, 0]
    hsv = cv2.cvtColor(bgr.reshape(1, 1, 3), cv2.COLOR_BGR2HSV)[0, 0]
    print(f"{cnt[i]*100:5.1f}%  RGB({bgr[2]:3d},{bgr[1]:3d},{bgr[0]:3d})  HSV({hsv[0]:3d},{hsv[1]:3d},{hsv[2]:3d})")
