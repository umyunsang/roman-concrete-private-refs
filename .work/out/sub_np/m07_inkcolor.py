# 박스별 배경색(최빈 근사)과 잉크색(가장 어두운/밝은 픽셀 군의 중앙값)을 hex로 출력한다.
# 사용: m07_inkcolor.py img "이름:x,y,w,h[:dark|light]" ...
import sys
import cv2
import numpy as np

img = cv2.imread(sys.argv[1])
for spec in sys.argv[2:]:
    parts = spec.split(":")
    name = parts[0]
    x, y, w, h = map(int, parts[1].split(","))
    mode = parts[2] if len(parts) > 2 else "dark"
    c = img[y:y + h, x:x + w].reshape(-1, 3).astype(np.float32)
    lum = 0.114 * c[:, 0] + 0.587 * c[:, 1] + 0.299 * c[:, 2]
    # 배경: 휘도 중앙값 부근 픽셀의 중앙값
    q = np.argsort(lum)
    n = len(q)
    if mode == "dark":
        bgsel = q[int(n * 0.6):int(n * 0.9)]
        inksel = q[:max(3, int(n * 0.06))]
    else:
        bgsel = q[int(n * 0.1):int(n * 0.4)]
        inksel = q[-max(3, int(n * 0.06)):]
    bg = np.median(c[bgsel], axis=0).astype(int)
    ink = np.median(c[inksel], axis=0).astype(int)
    print("%-16s bg #%02X%02X%02X  ink #%02X%02X%02X" % (name, bg[2], bg[1], bg[0], ink[2], ink[1], ink[0]))
