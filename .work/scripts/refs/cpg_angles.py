"""선분 각도 히스토그램으로 투영(진짜 등각 30° / 2:1 26.57° / 기타)을 판정한다. 영역별로 잴 수 있다 (2026-10-18).

- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- OpenCV LSD 선분 → 길이 가중 방향 히스토그램(0.25° 간격). 각도는 화면 위쪽이 +, 0~180°.
- 사용: uv run --no-project --with opencv-python-headless --with numpy --with pillow python -I cpg_angles.py \
        <이미지> <이름> [x0,y0,x1,y1 ...]   (영역을 주지 않으면 전체. 좌표는 그 이미지 픽셀)
  환경변수 대신 인자 끝에 out=<png> 를 주면 히스토그램 그림을 저장한다.
- 출력: 영역마다 선분 수, 수평·수직·우상향·좌상향 길이 비율, 지배 사선 각(가중 평균 ± 표준편차), 판정
"""
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"


def seg_angles(gray):
    lsd = cv2.createLineSegmentDetector()
    lines = lsd.detect(gray)[0]
    if lines is None:
        return np.zeros(0), np.zeros(0)
    s = lines.reshape(-1, 4)
    dx, dy = s[:, 2] - s[:, 0], s[:, 3] - s[:, 1]
    L = np.hypot(dx, dy)
    ang = (np.degrees(np.arctan2(-dy, dx)) + 180) % 180
    return ang, L


def peak(a, w, lo, hi):
    m = (a >= lo) & (a <= hi)
    if w[m].sum() == 0:
        return None
    hist, edges = np.histogram(a[m], bins=np.arange(lo, hi + 0.25, 0.25), weights=w[m])
    k = int(np.argmax(hist))
    pk = (edges[k] + edges[k + 1]) / 2
    near = m & (np.abs(a - pk) <= 1.5)
    mu = float(np.average(a[near], weights=w[near]))
    sd = float(np.sqrt(np.average((a[near] - mu) ** 2, weights=w[near])))
    return mu, sd, float(w[near].sum())


def analyse(gray, minlen):
    a, L = seg_angles(gray)
    keep = L >= minlen
    a, L = a[keep], L[keep]
    tot = float(L.sum()) if L.size else 1.0
    hz = float(L[(a <= 2) | (a >= 178)].sum()) / tot * 100
    vt = float(L[np.abs(a - 90) <= 2].sum()) / tot * 100
    up = peak(a, L, 15, 45)          # 우상향(/)
    dn = peak(180 - a, L, 15, 45)    # 좌상향(\) 을 0~90 으로 접어서
    upf = float(L[(a >= 15) & (a <= 45)].sum()) / tot * 100
    dnf = float(L[(a >= 135) & (a <= 165)].sum()) / tot * 100
    return dict(n=int(keep.sum()), hz=hz, vt=vt, up=up, dn=dn, upf=upf, dnf=dnf, a=a, L=L)


def verdict(r):
    vals = [v[0] for v in (r["up"], r["dn"]) if v]
    if not vals:
        return "사선 없음"
    if all(abs(v - 30) <= 1.0 for v in vals):
        return "진짜 등각(30°)"
    if all(abs(v - 26.57) <= 1.0 for v in vals):
        return "2:1 등각(26.57°)"
    return "기타/혼합"


def main() -> None:
    path, name = sys.argv[1], sys.argv[2]
    rest = sys.argv[3:]
    out = None
    minlen = 20
    rects = []
    for t in rest:
        if t.startswith("out="):
            out = t[4:]
        elif t.startswith("minlen="):
            minlen = float(t[7:])
        else:
            rects.append(tuple(map(int, t.split(","))))
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    H, W = img.shape
    if not rects:
        rects = [(0, 0, W, H)]
    results = []
    for (x0, y0, x1, y1) in rects:
        r = analyse(img[y0:y1, x0:x1], minlen)
        results.append(((x0, y0, x1, y1), r))
        fu = f"{r['up'][0]:.2f}±{r['up'][1]:.2f}" if r["up"] else "-"
        fd = f"{r['dn'][0]:.2f}±{r['dn'][1]:.2f}" if r["dn"] else "-"
        print(f"{name} {x0},{y0},{x1},{y1}: 선분 {r['n']} | 수평 {r['hz']:.1f}% 수직 {r['vt']:.1f}% | "
              f"우상향 {fu}° ({r['upf']:.1f}%) | 좌상향 {fd}° ({r['dnf']:.1f}%) | {verdict(r)}")
    if out:
        Wd, Hd = 900, 260 * len(results)
        im = Image.new("RGB", (Wd, Hd), (255, 255, 255))
        d = ImageDraw.Draw(im)
        f = ImageFont.truetype(FONT, 15)
        for i, (rc, r) in enumerate(results):
            oy = i * 260
            hist, edges = np.histogram(r["a"], bins=np.arange(0, 180.5, 0.5), weights=r["L"])
            mx = hist.max() if hist.max() > 0 else 1
            for j, h in enumerate(hist):
                x = 40 + j * 2.3
                hh = min(1.0, h / mx) * 190
                col = (220, 60, 60) if (abs(edges[j] - 30) < 1 or abs(edges[j] - 150) < 1) else \
                      (60, 120, 220) if (abs(edges[j] - 26.5) < 0.6 or abs(edges[j] - 153.5) < 0.6) else (120, 120, 120)
                d.rectangle([x, oy + 220 - hh, x + 1.8, oy + 220], fill=col)
            for t in (0, 26.57, 30, 45, 90, 135, 150, 153.43, 180):
                x = 40 + t / 0.5 * 2.3
                d.line([(x, oy + 222), (x, oy + 230)], fill=(0, 0, 0))
                d.text((x - 12, oy + 232), f"{t:g}", fill=(0, 0, 0), font=f)
            d.text((44, oy + 6), f"{name} 영역 {rc} · 선분 {r['n']} · {verdict(r)} (빨강=30°/150°, 파랑=26.57°/153.43°)",
                   fill=(0, 0, 0), font=f)
        im.save(out)
        print("saved", out)


if __name__ == "__main__":
    main()
