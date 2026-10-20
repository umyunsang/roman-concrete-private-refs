# 포스터 전역에서 노란 텍스트 덩어리를 찾아 bbox와 기울기(기준선 각도)를 추정
# 사용: python text_clusters.py [dilate] [minarea] [out.png]
import sys
import math
import cv2
import numpy as np

ART = "/Users/um-yunsang/roman-concrete-private-refs/.work/out/bj_art.png"


def text_mask(img):
    b, g, r = [img[:, :, i].astype(int) for i in range(3)]
    return ((r > 200) & (g > 165) & (b < 90) & (g - b > 110)).astype(np.uint8)


def skew_angle(m):
    """기준선 각도: 회전 후 행 투영 분산이 최대인 각도(도, 반시계 +)."""
    ys, xs = np.nonzero(m)
    if len(xs) < 50:
        return None, 0
    pts = np.stack([xs, ys], 1).astype(np.float32)
    best = (None, -1)
    for a10 in range(-450, 451, 5):
        a = math.radians(a10 / 10.0)
        # 기준선이 각도 a(반시계)인 경우, 그 법선 방향 좌표 = -x*sin(a) - y*cos(a)
        proj = -pts[:, 0] * math.sin(a) - pts[:, 1] * math.cos(a)
        hist, _ = np.histogram(proj, bins=int(proj.max() - proj.min()) + 1)
        v = float((hist.astype(np.float64) ** 2).sum())
        if v > best[1]:
            best = (a10 / 10.0, v)
    return best


def main():
    dil = int(sys.argv[1]) if len(sys.argv) > 1 else 13
    amin = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    out = sys.argv[3] if len(sys.argv) > 3 else None
    img = cv2.imread(ART)
    m = text_mask(img)
    md = cv2.dilate(m, np.ones((dil, dil), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(md, 8)
    rows = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        sub = m[y:y + h, x:x + w] * (lab[y:y + h, x:x + w] == i)
        ink = int(sub.sum())
        if ink < amin:
            continue
        ang, _ = skew_angle(sub)
        rows.append((y, x, w, h, ink, ang))
    rows.sort()
    for y, x, w, h, ink, ang in rows:
        print(f"x{x}-{x+w-1} y{y}-{y+h-1} (w{w} h{h}) mm x{x*0.21:.0f}-{(x+w)*0.21:.0f} y{y*0.2121:.0f}-{(y+h)*0.2121:.0f} 잉크{ink} 기울기{ang}")
    if out:
        vis = cv2.resize(img, (1000, 1400))
        for y, x, w, h, ink, ang in rows:
            cv2.rectangle(vis, (x // 2, y // 2), ((x + w) // 2, (y + h) // 2), (255, 255, 0), 1)
            cv2.putText(vis, f"{ang}", (x // 2, y // 2 - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
        cv2.imwrite(out, vis)


if __name__ == "__main__":
    main()
