# 바닥(크림색 윗면)·초록 측면 마스크를 만들어 플랫폼 윤곽을 본다.
import sys
import cv2
import numpy as np

src = sys.argv[1]
out = sys.argv[2]
img = cv2.imread(src)  # BGR
lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)

def mask_near(hexcol, tol):
    r, g, b = int(hexcol[0:2], 16), int(hexcol[2:4], 16), int(hexcol[4:6], 16)
    ref = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2LAB).astype(np.float32)[0, 0]
    d = np.sqrt(((lab - ref) ** 2).sum(axis=2))
    return (d < tol).astype(np.uint8) * 255

floor = mask_near("E6D4B6", 14)
green = mask_near("516D3D", 18)
bg = mask_near("9C8152", 10)

vis = np.zeros_like(img)
vis[bg > 0] = (60, 60, 60)
vis[floor > 0] = (200, 230, 245)
vis[green > 0] = (40, 160, 40)
small = cv2.resize(vis, (vis.shape[1] // 2, vis.shape[0] // 2), interpolation=cv2.INTER_AREA)
cv2.imwrite(out, small)
print("floor px", int((floor > 0).sum()), "green px", int((green > 0).sum()))
