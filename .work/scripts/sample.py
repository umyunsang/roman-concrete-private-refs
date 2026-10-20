# 지정한 아트 좌표의 색(BGR→hex, Lab)을 찍어 본다.
import sys, cv2, numpy as np
img = cv2.imread(sys.argv[1]); lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
for tok in sys.argv[2:]:
    name, xy = tok.split("=")
    x, y = map(int, xy.split(","))
    b, g, r = [int(v) for v in np.median(img[y-3:y+4, x-3:x+4].reshape(-1, 3), axis=0)]
    L, A, B = [int(v) for v in np.median(lab[y-3:y+4, x-3:x+4].reshape(-1, 3), axis=0)]
    print(f"  {name:10s} ({x},{y}) #{r:02x}{g:02x}{b:02x}  Lab({L*100//255},{A-128},{B-128})")
