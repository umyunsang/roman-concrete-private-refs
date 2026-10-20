"""창 안 비배경 화소를 k-평균(k)으로 묶어 군집 색과 비율을 출력. 사용: r3_winclusters.py <ref> x0,y0,x1,y1 k"""
import os, sys
import cv2
import numpy as np
sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/refs")
from r3_common import OUT, lab, load_norm
ref = sys.argv[1]; x0, y0, x1, y1 = [int(v) for v in sys.argv[2].split(",")]; k = int(sys.argv[3])
im, _ = load_norm(ref); L = lab(im)
m = cv2.imread(os.path.join(OUT, f"{ref}_nonbg.png"), 0) > 0
P = L[y0:y1, x0:x1][m[y0:y1, x0:x1]].astype(np.float32)
crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.2)
_, lb, c = cv2.kmeans(P, k, None, crit, 5, cv2.KMEANS_PP_CENTERS)
cnt = np.bincount(lb.ravel(), minlength=k)
for i in np.argsort(-cnt):
    print("Lab %s  %.1f%%" % (np.round(c[i], 1), 100 * cnt[i] / len(P)))
