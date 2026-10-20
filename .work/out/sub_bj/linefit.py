# 대략의 두 끝점 주변(±band px) 노랑 잉크 픽셀로 직선 최소제곱 적합 → 정밀 각도
import sys, math, cv2, numpy as np
ART = "/Users/um-yunsang/roman-concrete-private-refs/.work/out/bj_art.png"
x1, y1, x2, y2 = map(float, sys.argv[1:5]); band = float(sys.argv[5]) if len(sys.argv) > 5 else 2.5
img = cv2.imread(ART).astype(int)
xa, xb = int(min(x1, x2)) - 3, int(max(x1, x2)) + 3; ya, yb = int(min(y1, y2)) - 6, int(max(y1, y2)) + 6
roi = img[ya:yb, xa:xb]; b, g, r = roi[:, :, 0], roi[:, :, 1], roi[:, :, 2]
w = np.clip((g - 60) / 180.0, 0, 1) * ((r > 190) & (b < 120))  # 노랑 성분 가중치
ys, xs = np.nonzero(w > 0.15); ws = w[ys, xs]; xs = xs + xa; ys = ys + ya
dx, dy = x2 - x1, y2 - y1; L = math.hypot(dx, dy); nx, ny = -dy / L, dx / L
d = (xs - x1) * nx + (ys - y1) * ny; t = ((xs - x1) * dx + (ys - y1) * dy) / L
sel = (np.abs(d) <= band) & (t >= 0) & (t <= L)
X, Y, W = xs[sel], ys[sel], ws[sel]
A = np.vstack([X, np.ones_like(X)]).T * np.sqrt(W)[:, None]; B = Y * np.sqrt(W)
k, c = np.linalg.lstsq(A, B, rcond=None)[0]
print(f"표본 {sel.sum()}px  기울기각 {math.degrees(math.atan(-k)):.2f}° (반시계+)  y = {k:.4f}x + {c:.1f}")
