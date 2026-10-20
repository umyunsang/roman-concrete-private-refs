# 박스 안의 글자(잉크) 픽셀로 줄 기울기(자동)와 줄별 높이·폭을 잰다.
# 사용: m06_textlines.py img x y w h ink(hex) tol [angle|auto] [minrow]
import sys
import cv2
import numpy as np

img = cv2.imread(sys.argv[1])
x, y, w, h = map(int, sys.argv[2:6])
ink = sys.argv[6]
tol = float(sys.argv[7])
ang_arg = sys.argv[8] if len(sys.argv) > 8 else "auto"
minrow = int(sys.argv[9]) if len(sys.argv) > 9 else 1
crop = img[y:y + h, x:x + w]
lab = cv2.cvtColor(crop, cv2.COLOR_BGR2LAB).astype(np.float32)
r, g, b = int(ink[0:2], 16), int(ink[2:4], 16), int(ink[4:6], 16)
ref = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2LAB).astype(np.float32)[0, 0]
m = (np.sqrt(((lab - ref) ** 2).sum(axis=2)) < tol).astype(np.uint8)
ys, xs = np.where(m > 0)
print("ink px", len(xs))
if len(xs) == 0:
    sys.exit()

def profile_score(theta):
    # theta: 줄 방향 각도(도, 화면 기준 시계방향 +). 줄에 수직인 축으로 투영
    t = np.radians(theta)
    d = -xs * np.sin(t) + ys * np.cos(t)
    hist, _ = np.histogram(d, bins=np.arange(d.min() - 1, d.max() + 2, 1.0))
    return (hist.astype(np.float64) ** 2).sum(), hist, d.min() - 1

if ang_arg == "auto":
    best = None
    for th in np.arange(-45, 45.01, 0.25):
        s, _, _ = profile_score(th)
        if best is None or s > best[0]:
            best = (s, th)
    theta = best[1]
    # 미세 조정
    for th in np.arange(theta - 0.5, theta + 0.51, 0.05):
        s, _, _ = profile_score(th)
        if s > best[0]:
            best = (s, th)
    theta = best[1]
else:
    theta = float(ang_arg)
print("line angle deg (screen, +=clockwise/down-right):", round(theta, 2))
s, hist, d0 = profile_score(theta)
t = np.radians(theta)
along = xs * np.cos(t) + ys * np.sin(t)
d = -xs * np.sin(t) + ys * np.cos(t)
on = hist >= minrow
lines = []
i = 0
while i < len(on):
    if on[i]:
        j = i
        while j < len(on) and on[j]:
            j += 1
        lines.append((i, j - 1))
        i = j
    else:
        i += 1
# 너무 가까운 줄(1px 틈) 병합
merged = []
for a_, b_ in lines:
    if merged and a_ - merged[-1][1] <= 1:
        merged[-1] = (merged[-1][0], b_)
    else:
        merged.append((a_, b_))
for a_, b_ in merged:
    sel = (d >= d0 + a_) & (d <= d0 + b_ + 1)
    if sel.sum() < 5:
        continue
    al = along[sel]
    # 줄 시작점(화면 좌표)
    k = np.argmin(al)
    print("line: perp %.0f-%.0f  height %d px  len %.0f px  start(x,y)=(%d,%d) ink=%d" % (
        d0 + a_, d0 + b_, b_ - a_ + 1, al.max() - al.min(), x + xs[sel][k], y + ys[sel][k], sel.sum()))
