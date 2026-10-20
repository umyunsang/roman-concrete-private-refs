"""지정 점들의 색(RGB/Lab)을 찍어 본다. 사용: ra_probe.py <ref> x,y x,y ... (정규 1000x1400 단위)"""
import sys
import cv2, numpy as np
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from ra_common import *
ref = sys.argv[1]
art = cv2.imread(str(composite_path(ref)))
lab = cv2.cvtColor(art, cv2.COLOR_BGR2LAB)
for p in sys.argv[2:]:
    x, y = [float(v) for v in p.split(',')]
    X, Y = int(x * 2), int(y * 2)
    patch = art[Y - 2:Y + 3, X - 2:X + 3].reshape(-1, 3).mean(0)
    pl = lab[Y - 2:Y + 3, X - 2:X + 3].reshape(-1, 3).mean(0)
    print(f"{p:>12}  #%02x%02x%02x  Lab({pl[0]:.0f},{pl[1]:.0f},{pl[2]:.0f})" % (int(patch[2]), int(patch[1]), int(patch[0])))
