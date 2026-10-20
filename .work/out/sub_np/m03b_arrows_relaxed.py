# 바닥 위의 작은 초록 화살표를 찾아 위치·크기·방향을 기록하고 접사 시트를 만든다.
import sys
import cv2
import numpy as np

img = cv2.imread(sys.argv[1])
out_sheet = sys.argv[2]
H, W = img.shape[:2]
lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)

def near(hexcol, tol):
    r, g, b = int(hexcol[0:2], 16), int(hexcol[2:4], 16), int(hexcol[4:6], 16)
    ref = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2LAB).astype(np.float32)[0, 0]
    return np.sqrt(((lab - ref) ** 2).sum(axis=2)) < tol

green = near("5A6940", 26).astype(np.uint8)
floor = near("E6D4B6", 16).astype(np.uint8)
# 공정도 영역만
roi = np.zeros_like(green)
roi[380:2650, 340:1480] = 1
green = green * roi
n, lbl, stats, cents = cv2.connectedComponentsWithStats(green, 8)
found = []
for i in range(1, n):
    x, y, w, h, a = stats[i]
    if not (60 <= a <= 900):
        continue
    if w > 60 or h > 45:
        continue
    # 주변 링이 대부분 바닥색이어야 화살표로 간주
    pad = 6
    x0, y0, x1, y1 = max(0, x - pad), max(0, y - pad), min(W, x + w + pad), min(H, y + h + pad)
    ring = floor[y0:y1, x0:x1].astype(bool) & ~(lbl[y0:y1, x0:x1] == i)
    comp = (lbl[y0:y1, x0:x1] == i)
    area_box = (x1 - x0) * (y1 - y0)
    floor_ratio = ring.sum() / max(1, area_box - comp.sum())
    if floor_ratio < 0.5:
        continue
    ys, xs = np.where(lbl == i)
    cx, cy = xs.mean(), ys.mean()
    # 볼록 껍질에서 결손(노치) 방향 = 꼬리, 그 반대 = 머리
    pts = np.stack([xs, ys], 1).astype(np.int32)
    hull = cv2.convexHull(pts)
    hull_mask = np.zeros((H, W), np.uint8)
    cv2.fillPoly(hull_mask, [hull], 1)
    defect = hull_mask.astype(bool) & ~(lbl == i)
    dys, dxs = np.where(defect)
    if len(dxs) > 0:
        tail = (dxs.mean() - cx, dys.mean() - cy)
        head_dir = np.degrees(np.arctan2(-tail[1], -tail[0]))  # 화면 좌표(y 아래) 기준 각도
    else:
        head_dir = float("nan")
    found.append((int(cx), int(cy), int(a), int(w), int(h), round(float(floor_ratio), 2), round(float(head_dir), 1)))

found.sort(key=lambda t: (t[1], t[0]))
for f in found:
    print("cx=%d cy=%d area=%d w=%d h=%d floor=%.2f head_deg=%.1f" % f)

# 접사 시트
tiles = []
for (cx, cy, a, w, h, fr, hd) in found:
    x0, y0 = max(0, cx - 40), max(0, cy - 28)
    crop = img[y0:y0 + 56, x0:x0 + 80].copy()
    crop = cv2.resize(crop, (240, 168), interpolation=cv2.INTER_CUBIC)
    cv2.putText(crop, "%d,%d" % (cx, cy), (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
    tiles.append(crop)
if tiles:
    cols = 6
    rows = (len(tiles) + cols - 1) // cols
    sheet = np.full((rows * 168, cols * 240, 3), 255, np.uint8)
    for k, t in enumerate(tiles):
        r, c = divmod(k, cols)
        sheet[r * 168:(r + 1) * 168, c * 240:(c + 1) * 240] = t
    cv2.imwrite(out_sheet, sheet)
print("count", len(found))
