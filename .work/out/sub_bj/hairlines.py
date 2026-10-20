# 가는 지시선(노랑 헤어라인이 배경 빨강과 섞여 주황으로 보이는 선) 검출
# 사용: python hairlines.py x y w h [minlen] [out.png]
# 수평·수직 선은 형태학 열림으로, 사선은 허프 변환으로 검출
import sys
import math
import cv2
import numpy as np

ART = "/Users/um-yunsang/roman-concrete-private-refs/.work/out/bj_art.png"


def main():
    x, y, w, h = map(int, sys.argv[1:5])
    minlen = int(sys.argv[5]) if len(sys.argv) > 5 else 40
    outp = sys.argv[6] if len(sys.argv) > 6 else None
    img = cv2.imread(ART)
    roi = img[y:y + h, x:x + w]
    b, g, r = [roi[:, :, i].astype(int) for i in range(3)]
    # 배경 빨강(G≈60)보다 G가 확실히 높고 B는 낮은 픽셀 = 노랑 잉크 성분
    ink = ((r > 200) & (g > 85) & (b < 110) & (g - b > 30)).astype(np.uint8) * 255
    hk = cv2.getStructuringElement(cv2.MORPH_RECT, (minlen, 1))
    vk = cv2.getStructuringElement(cv2.MORPH_RECT, (1, minlen))
    hl = cv2.morphologyEx(ink, cv2.MORPH_OPEN, hk)
    vl = cv2.morphologyEx(ink, cv2.MORPH_OPEN, vk)
    for name, m, axis in (("수평", hl, 0), ("수직", vl, 1)):
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
        for i in range(1, n):
            sx, sy, sw, sh, area = st[i]
            if max(sw, sh) < minlen:
                continue
            print(f"{name} x{sx+x}-{sx+x+sw-1} y{sy+y}-{sy+y+sh-1} 길이{max(sw,sh)}px 두께{min(sw,sh)}px")
    # 사선: 수평/수직 제거 후 허프
    rest = cv2.subtract(ink, cv2.bitwise_or(hl, vl))
    ls = cv2.HoughLinesP(rest, 1, np.pi / 360, threshold=int(minlen * 0.6), minLineLength=minlen, maxLineGap=2)
    if ls is not None:
        seen = []
        for l in ls.reshape(-1, 4):
            x1, y1, x2, y2 = map(int, l)
            ang = math.degrees(math.atan2(-(y2 - y1), x2 - x1))
            if ang <= -90:
                ang += 180
            if ang > 90:
                ang -= 180
            if abs(ang) < 3 or abs(abs(ang) - 90) < 3:
                continue
            ln = math.hypot(x2 - x1, y2 - y1)
            seen.append((ln, ang, x1 + x, y1 + y, x2 + x, y2 + y))
        seen.sort(reverse=True)
        for ln, ang, a, bb, c, d in seen[:30]:
            print(f"사선 len{ln:6.1f}px ang{ang:7.2f}deg ({a},{bb})-({c},{d})")
    if outp:
        vis = roi.copy()
        vis[hl > 0] = (255, 255, 0)
        vis[vl > 0] = (0, 255, 0)
        cv2.imwrite(outp, vis)


if __name__ == "__main__":
    main()
