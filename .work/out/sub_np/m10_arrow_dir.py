# 등각 바닥 화살표의 진행 방향 판정.
# 바닥에 누운 화살표는 화면에서 '세로로 곧은 변'(미늘~촉)과 '수평으로 긴 변'(촉~반대 미늘)을 가진다.
#  아래 변이 길고 오른쪽 변이 곧음 → +X(오른쪽 아래), 아래 길고 왼쪽 곧음 → +Y(왼쪽 아래)
#  위 변이 길고 오른쪽 곧음 → -Y(오른쪽 위), 위 길고 왼쪽 곧음 → -X(왼쪽 위)
import sys
import cv2
import numpy as np

img = cv2.imread(sys.argv[1])
out = sys.argv[2]
pts = [tuple(map(int, p.split(","))) for p in sys.argv[3:]]
lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
L = lab[:, :, 0] * 100 / 255
A = lab[:, :, 1] - 128
B = lab[:, :, 2] - 128
green = ((A < -6) & (B > 8) & (L > 25) & (L < 62)).astype(np.uint8)
tiles = []
for (cx, cy) in pts:
    x0, y0 = cx - 25, cy - 16
    sub = green[y0:y0 + 32, x0:x0 + 50]
    n, l, s, c = cv2.connectedComponentsWithStats(sub, 8)
    k = 1 + int(np.argmax(s[1:, 4]))
    m = (l == k)
    ys, xs = np.where(m)
    bx0, bx1, by0, by1 = xs.min(), xs.max(), ys.min(), ys.max()
    w, h = bx1 - bx0 + 1, by1 - by0 + 1
    # 가장자리 띠(2px)에서의 점유 길이
    top = m[by0:by0 + 2, :].any(axis=0).sum()
    bot = m[by1 - 1:by1 + 1, :].any(axis=0).sum()
    left = m[:, bx0:bx0 + 2].any(axis=1).sum()
    right = m[:, bx1 - 1:bx1 + 1].any(axis=1).sum()
    vert = "R" if right > left else "L"
    horiz = "B" if bot > top else "T"
    lut = {("B", "R"): "+X 오른쪽아래", ("B", "L"): "+Y 왼쪽아래", ("T", "R"): "-Y 오른쪽위", ("T", "L"): "-X 왼쪽위"}
    d = lut[(horiz, vert)]
    print("(%d,%d) bbox %dx%d top=%d bot=%d left=%d right=%d -> %s" % (cx, cy, w, h, top, bot, left, right, d))
    crop = img[cy - 16:cy + 16, cx - 25:cx + 25].copy()
    crop = cv2.resize(crop, (200, 128), interpolation=cv2.INTER_CUBIC)
    tag = d.split()[0]
    cv2.putText(crop, "%d,%d %s" % (cx, cy, tag), (3, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
    tiles.append(crop)
cols = 5
rows = (len(tiles) + cols - 1) // cols
sheet = np.full((rows * 128, cols * 200, 3), 255, np.uint8)
for i, t in enumerate(tiles):
    r, cc = divmod(i, cols)
    sheet[r * 128:(r + 1) * 128, cc * 200:(cc + 1) * 200] = t
cv2.imwrite(out, sheet)
