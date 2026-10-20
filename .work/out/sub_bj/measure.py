# 노란 잉크(텍스트·선) 마스크 기반 측정 도구
# 사용: python measure.py bbox x y w h            -> 노란 픽셀 바운딩 박스
#       python measure.py rows x y w h [minpx]     -> 행 투영으로 텍스트 줄(시작/끝/높이) 검출
#       python measure.py cols x y w h [minpx]     -> 열 투영으로 열 구간 검출
#       python measure.py lines x y w h            -> 허프 변환 직선 검출(각도 포함)
import sys
import math
import cv2
import numpy as np

ART = "/Users/um-yunsang/roman-concrete-private-refs/.work/out/bj_art.png"
MMX = 0.21
MMY = 0.2121


def yellow_mask(roi, loose=False):
    b, g, r = [roi[:, :, i].astype(int) for i in range(3)]
    if loose:
        return ((r > 200) & (g > 150) & (b < 120) & (g - b > 90)).astype(np.uint8)
    return ((r > 215) & (g > 190) & (b < 110)).astype(np.uint8)


def runs(profile, minpx=1, gap=0):
    on = profile >= minpx
    res = []
    i = 0
    n = len(on)
    while i < n:
        if on[i]:
            j = i
            while j < n and on[j]:
                j += 1
            res.append([i, j - 1])
            i = j
        else:
            i += 1
    # 작은 틈 병합
    if gap > 0 and res:
        merged = [res[0]]
        for s, e in res[1:]:
            if s - merged[-1][1] - 1 <= gap:
                merged[-1][1] = e
            else:
                merged.append([s, e])
        res = merged
    return res


def main():
    mode = sys.argv[1]
    x, y, w, h = map(int, sys.argv[2:6])
    extra = sys.argv[6:]
    img = cv2.imread(ART)
    roi = img[y:y + h, x:x + w]
    loose = "loose" in extra
    m = yellow_mask(roi, loose)
    if mode == "bbox":
        ys, xs = np.nonzero(m)
        if len(xs) == 0:
            print("노란 픽셀 없음")
            return
        x0, x1, y0, y1 = xs.min() + x, xs.max() + x, ys.min() + y, ys.max() + y
        print(f"bbox px x{x0}-{x1} y{y0}-{y1} (w{x1-x0+1} h{y1-y0+1}) | mm x{x0*MMX:.1f}-{x1*MMX:.1f} y{y0*MMY:.1f}-{y1*MMY:.1f} (w{(x1-x0+1)*MMX:.1f} h{(y1-y0+1)*MMY:.1f})")
    elif mode in ("rows", "cols"):
        minpx = int(extra[0]) if extra and extra[0].isdigit() else 1
        gap = int(extra[1]) if len(extra) > 1 and extra[1].isdigit() else 0
        prof = m.sum(axis=1) if mode == "rows" else m.sum(axis=0)
        off = y if mode == "rows" else x
        sc = MMY if mode == "rows" else MMX
        for s, e in runs(prof, minpx, gap):
            print(f"{mode[:-1]} {s+off}-{e+off} 길이{e-s+1}px = {(e-s+1)*sc:.2f}mm  (최대밀도 {prof[s:e+1].max()})")
    elif mode == "lines":
        edges = (m * 255).astype(np.uint8)
        ls = cv2.HoughLinesP(edges, 1, np.pi / 720, threshold=40, minLineLength=int(extra[0]) if extra and extra[0].isdigit() else 40, maxLineGap=3)
        if ls is None:
            print("직선 없음")
            return
        out = []
        for l in ls.reshape(-1, 4):
            x1, y1, x2, y2 = l
            ang = math.degrees(math.atan2(-(y2 - y1), x2 - x1))
            if ang < -90:
                ang += 180
            if ang > 90:
                ang -= 180
            ln = math.hypot(x2 - x1, y2 - y1)
            out.append((ln, ang, x1 + x, y1 + y, x2 + x, y2 + y))
        out.sort(reverse=True)
        for ln, ang, a, b, c, d in out[:40]:
            print(f"len{ln:6.1f}px ang{ang:7.2f}deg ({a},{b})-({c},{d})")


if __name__ == "__main__":
    main()
