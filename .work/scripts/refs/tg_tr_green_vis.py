"""Trabacchi 녹지 성분 상위 4개를 색으로 칠해 확인 이미지를 만든다 (2026-10-18). 입력 이미지는 읽기만 한다.
사용: python -I tg_tr_green_vis.py <trabacchi_2.jpg> <출력.png>
"""
import sys
import cv2
import numpy as np
img = cv2.imread(sys.argv[1]); H, W = img.shape[:2]
lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
C = [((241,237,218),0),((218,206,181),0),((244,166,105),1),((220,176,137),1),((201,143,101),1),((239,231,168),2),
     ((174,215,169),3),((169,188,154),3),((155,165,139),3),((105,192,207),4),((131,136,114),6),((103,102,83),6)]
cen = np.array([cv2.cvtColor(np.uint8([[c[::-1]]]), cv2.COLOR_BGR2LAB)[0,0] for c,_ in C], np.float32)
k = np.argmin(((lab[:,None,:]-cen[None])**2).sum(-1), 1)
cls = np.array([c for _,c in C], np.uint8)[k].reshape(H, W)
x0, y0, x1, y1 = int(0.036*W), int(0.062*H), int(0.964*W), int(0.945*H)
g = np.zeros((H, W), np.uint8)
g[y0:y1, x0:x1] = (np.isin(cls[y0:y1, x0:x1], [3, 6])).astype(np.uint8) * 255
for a, b, c, d in [(0.4247,0.0655,0.5703,0.159),(0.036,0.829,0.1685,0.945)]:
    g[int(b*H):int(d*H), int(a*W):int(c*W)] = 0
g = cv2.morphologyEx(g, cv2.MORPH_OPEN, np.ones((5,5), np.uint8))
g = cv2.morphologyEx(g, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15,15)))
n, L, st, cc = cv2.connectedComponentsWithStats(g, 8)
order = np.argsort(st[1:, 4])[::-1] + 1
vis = (img * 0.45).astype(np.uint8)
cols = [(0, 0, 255), (255, 0, 255), (0, 200, 255), (255, 255, 0)]
for i, c in zip(order[:4], cols):
    vis[L == i] = c
cv2.imwrite(sys.argv[2], vis)
print("ok")
