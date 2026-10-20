"""패널·타이틀·푸터 상자를 잉크 외곽으로 정밀화.
바탕색 = 상자 테두리 띠 화소의 중앙값(Lab). 잉크 = 바탕과 ΔE>thr. 작은 점 제거 후 외곽 상자.
출력: work/ink_<ref>.json, work/ink_<ref>.png
"""
import sys, json
import cv2, numpy as np
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from ra_common import *
from ra_zones_def import ZONES

def ink_box(lab, rect, thr=16, pad=6):
    x0, y0, x1, y1 = rect
    X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(1000, x1 + pad), min(1400, y1 + pad)
    sub = lab[Y0:Y1, X0:X1].astype(np.float32)
    border = np.concatenate([sub[:3].reshape(-1, 3), sub[-3:].reshape(-1, 3), sub[:, :3].reshape(-1, 3), sub[:, -3:].reshape(-1, 3)])
    bg = np.median(border, axis=0)
    d = np.linalg.norm(sub - bg, axis=2)
    ink = (d > thr).astype(np.uint8)
    ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    n, lb, st, _ = cv2.connectedComponentsWithStats(cv2.dilate(ink, np.ones((7, 7), np.uint8)))
    keep = np.zeros_like(ink)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] >= 120:
            keep[(lb == i) & (ink > 0)] = 1
    ys, xs = np.nonzero(keep)
    if len(xs) == 0:
        return list(rect), bg.tolist(), 0.0
    bb = [int(xs.min() + X0), int(ys.min() + Y0), int(xs.max() + X0 + 1), int(ys.max() + Y0 + 1)]
    return bb, bg.tolist(), float(keep.mean() * 100)

out = {}
for ref, z in ZONES.items():
    art = cv2.imread(str(composite_path(ref)))
    img = cv2.resize(art, (1000, 1400), interpolation=cv2.INTER_AREA)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    r = {"title": None, "panels": [], "footer": None}
    name, rect = z["title"]
    bb, bg, ip = ink_box(lab, rect, thr=18, pad=0)
    r["title"] = {"name": name, "rough": rect, "bbox": bb, "ink_pct": round(ip, 1)}
    for name, slot, rect in z["panels"]:
        bb, bg, ip = ink_box(lab, rect, thr=18, pad=0)
        r["panels"].append({"name": name, "slot": slot, "rough": rect, "bbox": bb, "ink_pct": round(ip, 1)})
    name, rect = z["footer"]
    bb, bg, ip = ink_box(lab, rect, thr=18, pad=0)
    r["footer"] = {"name": name, "rough": rect, "bbox": bb, "ink_pct": round(ip, 1)}
    out[ref] = r
    ov = img.copy()
    for it in [r["title"], r["footer"]] + r["panels"]:
        x0, y0, x1, y1 = it["rough"]; cv2.rectangle(ov, (x0, y0), (x1, y1), (180, 180, 180), 1)
        x0, y0, x1, y1 = it["bbox"]; cv2.rectangle(ov, (x0, y0), (x1, y1), (0, 0, 255), 2)
    cv2.imwrite(str(WORK / f"ink_{ref}.png"), ov)
    print(ref)
    for it in [r["title"]] + r["panels"] + [r["footer"]]:
        print("  ", it["name"][:30], it["rough"], "->", it["bbox"], it["ink_pct"])
json.dump(out, open(WORK / "ink.json", "w"), ensure_ascii=False, indent=1)
