"""정규 좌표 작은 상자의 중앙값 RGB·HSV를 출력한다 (2026-10-18). 입력 이미지는 읽기만 한다.
사용: python -I tg_px.py <이미지> <이름:x0,y0,x1,y1> ...
"""
import sys
import cv2
import numpy as np
img = cv2.imread(sys.argv[1]); H, W = img.shape[:2]
hsv_all = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
for arg in sys.argv[2:]:
    nm, b = arg.split(':')
    x0, y0, x1, y1 = (float(v) for v in b.split(','))
    c = img[int(y0*H):int(y1*H), int(x0*W):int(x1*W)].reshape(-1, 3)
    h = hsv_all[int(y0*H):int(y1*H), int(x0*W):int(x1*W)].reshape(-1, 3)
    m = np.median(c, 0).astype(int); mh = np.median(h, 0).astype(int)
    p10 = np.percentile(h, 10, 0).astype(int); p90 = np.percentile(h, 90, 0).astype(int)
    print(f"{nm:10s} RGB({m[2]},{m[1]},{m[0]}) HSV med({mh[0]},{mh[1]},{mh[2]}) p10({p10[0]},{p10[1]},{p10[2]}) p90({p90[0]},{p90[1]},{p90[2]})")
