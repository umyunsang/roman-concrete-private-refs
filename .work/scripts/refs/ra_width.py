"""강·길 폭: 지정 열(x)에서 세로 단면을 따라 기준색과 가까운 연속 구간 길이 -> 수직 두께 -> 축 직각 폭.
사용: ra_width.py <ref> <theta> <x> <y0> <y1> <thr> L,a,b [L,a,b..]  (정규 단위, 아트 px로 측정)"""
import sys, math
import cv2, numpy as np
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from ra_common import *
ref, th = sys.argv[1], float(sys.argv[2]); x, y0, y1, thr = float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
refs = [np.array([float(v) for v in s.split(',')], np.float32) for s in sys.argv[7:]]
art = cv2.imread(str(composite_path(ref)))
lab = cv2.cvtColor(art, cv2.COLOR_BGR2LAB).astype(np.float32)
X = int(x * 2)
col = lab[int(y0 * 2):int(y1 * 2), X - 2:X + 3].mean(1)
d = np.min(np.stack([np.linalg.norm(col - r, axis=1) for r in refs]), 0)
on = d < thr
runs, i = [], 0
while i < len(on):
    if on[i]:
        j = i
        while j < len(on) and on[j]: j += 1
        if j - i >= 4: runs.append((i, j))
        i = j
    else: i += 1
for a, b in runs:
    tv = (b - a) / 2   # 정규 단위
    print(f"{ref} x={x}: y {y0 + a/2:.0f}~{y0 + b/2:.0f}  수직 두께 {tv:.1f}u ({tv*0.4243:.1f}mm)  축 직각 폭 {tv*math.cos(math.radians(th)):.1f}u ({tv*math.cos(math.radians(th))*0.42:.1f}mm)")
