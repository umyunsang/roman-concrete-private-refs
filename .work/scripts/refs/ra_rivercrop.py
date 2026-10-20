"""강 마스크를 원본 위에 덧칠한 확대 crop. 사용: ra_rivercrop.py <ref> x0 y0 x1 y1 out"""
import sys
import cv2, numpy as np
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from ra_common import *
ref = sys.argv[1]; x0, y0, x1, y1 = [int(v) for v in sys.argv[2:6]]; outn = sys.argv[6]
art = cv2.imread(str(composite_path(ref)))
img = cv2.resize(art, (1000, 1400), interpolation=cv2.INTER_AREA)
river = np.load(WORK / f"river_{ref}.npy")
ov = img.copy()
ov[river] = (0.3 * ov[river] + 0.7 * np.array([0, 0, 255])).astype(np.uint8)
c = ov[y0:y1, x0:x1]
k = 1100 / max(c.shape[:2])
c = cv2.resize(c, (int(c.shape[1] * k), int(c.shape[0] * k)), interpolation=cv2.INTER_CUBIC)
for u in range((x0 // 50 + 1) * 50, x1, 50):
    X = int((u - x0) * k); cv2.line(c, (X, 0), (X, c.shape[0]), (255, 0, 255), 1)
    cv2.putText(c, str(u), (X + 2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 2)
for u in range((y0 // 50 + 1) * 50, y1, 50):
    Y = int((u - y0) * k); cv2.line(c, (0, Y), (c.shape[1], Y), (255, 200, 0), 1)
    cv2.putText(c, str(u), (2, Y - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 2)
cv2.imwrite(str(WORK / outn), c)
print(WORK / outn)
