"""같은 LSD 지표(길이 가중, 선분≥25px, 긴 변 1600px로 축소)로 여러 이미지의 지면 축 집중도를 비교한다 (2026-10-18).
입력 이미지는 읽기만 한다. 사용: python -I tg_lsd_compare.py <이름=경로[@x0,y0,x1,y1]> ...
"""
import sys
import cv2
import numpy as np

def run(path, box):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    H, W = img.shape
    if box:
        x0, y0, x1, y1 = box
        img = img[int(y0*H):int(y1*H), int(x0*W):int(x1*W)]
    h, w = img.shape
    s = 1600 / max(h, w)
    img = cv2.resize(img, (int(w*s), int(h*s)), interpolation=cv2.INTER_AREA)
    segs = cv2.createLineSegmentDetector().detect(img)[0].reshape(-1, 4)
    dx, dy = segs[:, 2]-segs[:, 0], segs[:, 3]-segs[:, 1]
    L = np.hypot(dx, dy); k = L >= 25
    a = (np.degrees(np.arctan2(-dy[k], dx[k])) + 90) % 180 - 90; wt = L[k]; tot = wt.sum()
    hist, e = np.histogram(a, bins=np.arange(-90, 90.5, 1.0), weights=wt)
    pk = []
    for i in np.argsort(hist)[::-1]:
        c = (e[i]+e[i+1])/2
        if all(abs(((c-p[0])+90) % 180-90) > 6 for p in pk):
            win = np.abs(((a-c)+90) % 180-90) <= 1.5
            pk.append((round(float(c), 1), round(float(wt[win].sum()/tot*100), 1)))
        if len(pk) >= 6: break
    obl = [p for p in pk if 8 < abs(p[0]) < 82][:2]
    def band(lo, hi):
        m = (a >= lo) & (a <= hi)
        return round(float(wt[m].sum()/tot*100), 1)
    return pk, round(sum(p[1] for p in obl), 1), band(28.5, 31.5)+band(-31.5, -28.5), band(25.0, 28.0)+band(-28.0, -25.0), int(k.sum())

print("| 이미지 | 봉우리(각°, ±1.5° 길이비%) | 사선 상위 2봉우리 합% | ±30°±1.5° 합% | ±26.6°±1.5° 합% | 선분 수 |")
for arg in sys.argv[1:]:
    nm, rest = arg.split('=', 1)
    box = None
    if '@' in rest:
        rest, b = rest.split('@'); box = [float(v) for v in b.split(',')]
    pk, top2, b30, b26, n = run(rest, box)
    print(f"| {nm} | {pk} | {top2} | {b30} | {b26} | {n} |")
