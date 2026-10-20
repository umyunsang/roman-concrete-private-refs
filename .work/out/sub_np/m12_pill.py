# 알약형 라벨 분석: 갈색(또는 지정색) 알약 영역을 찾고, 그 안의 밝은 글자만으로 획 방향·줄 기울기·크기를 잰다.
# 사용: m12_pill.py img x y w h [pill_hex] [pill_tol]
import sys
import cv2
import numpy as np

img = cv2.imread(sys.argv[1])
x, y, w, h = map(int, sys.argv[2:6])
pill_hex = sys.argv[6] if len(sys.argv) > 6 else "7A5446"
pill_tol = float(sys.argv[7]) if len(sys.argv) > 7 else 22
sub = img[y:y + h, x:x + w]
lab = cv2.cvtColor(sub, cv2.COLOR_BGR2LAB).astype(np.float32)
r, g, b = int(pill_hex[0:2], 16), int(pill_hex[2:4], 16), int(pill_hex[4:6], 16)
ref = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2LAB).astype(np.float32)[0, 0]
pill = (np.sqrt(((lab - ref) ** 2).sum(axis=2)) < pill_tol).astype(np.uint8)
n, l, s, c = cv2.connectedComponentsWithStats(pill, 8)
k = 1 + int(np.argmax(s[1:, 4]))
pm = (l == k).astype(np.uint8)
filled = cv2.morphologyEx(pm, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
cnts, _ = cv2.findContours(filled, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
cnt = max(cnts, key=cv2.contourArea)
hull_mask = np.zeros_like(filled)
cv2.drawContours(hull_mask, [cnt], -1, 1, -1)
inner = cv2.erode(hull_mask, np.ones((3, 3), np.uint8))
Lc = lab[:, :, 0]
txt = ((inner > 0) & (pm == 0) & (Lc > 150)).astype(np.uint8)
rect = cv2.minAreaRect(cnt)
(cx, cy), (rw, rh), ang = rect
print("pill bbox x %d-%d y %d-%d, minAreaRect center (%.0f,%.0f) size %.0fx%.0f angle %.1f" % (
    x + s[k, 0], x + s[k, 0] + s[k, 2] - 1, y + s[k, 1], y + s[k, 1] + s[k, 3] - 1, x + cx, y + cy, rw, rh, ang))
# 획 방향
m = cv2.GaussianBlur(txt.astype(np.float32), (3, 3), 0.8)
gx = cv2.Sobel(m, cv2.CV_32F, 1, 0, ksize=3)
gy = cv2.Sobel(m, cv2.CV_32F, 0, 1, ksize=3)
mag = np.sqrt(gx ** 2 + gy ** 2)
st = (np.degrees(np.arctan2(gy, gx)) + 90.0) % 180.0
st[st > 90] -= 180
sel = mag > 0.2
hist, edges = np.histogram(st[sel], bins=72, range=(-90, 90), weights=mag[sel])
hs = np.convolve(np.concatenate([hist[-2:], hist, hist[:2]]), np.ones(5) / 5, mode="valid")
order = np.argsort(hs)[::-1]
peaks = []
for i in order:
    cc = (edges[i] + edges[i + 1]) / 2
    if all(min(abs(cc - p), 180 - abs(cc - p)) > 15 for p, _ in peaks):
        peaks.append((cc, hs[i]))
    if len(peaks) == 3:
        break
print("text px", int(txt.sum()), "stroke dirs:", ", ".join("%.1f(%.3f)" % (p, v / hs.sum()) for p, v in peaks))
ys, xs = np.where(txt > 0)
best = None
for th in np.arange(-45, 45.01, 0.25):
    t = np.radians(th)
    d = -xs * np.sin(t) + ys * np.cos(t)
    hh, _ = np.histogram(d, bins=np.arange(d.min() - 1, d.max() + 2, 1.0))
    sc = (hh.astype(np.float64) ** 2).sum()
    if best is None or sc > best[0]:
        best = (sc, th)
t = np.radians(best[1])
d = -xs * np.sin(t) + ys * np.cos(t)
al = xs * np.cos(t) + ys * np.sin(t)
print("text line angle %.2f, perp height %.0f px, length %.0f px" % (best[1], d.max() - d.min() + 1, al.max() - al.min() + 1))
pc = np.median(sub[pm > 0].reshape(-1, 3), axis=0).astype(int)
tc = np.median(sub[txt > 0].reshape(-1, 3), axis=0).astype(int) if txt.sum() > 0 else pc
print("pill color #%02X%02X%02X  text color #%02X%02X%02X" % (pc[2], pc[1], pc[0], tc[2], tc[1], tc[0]))
