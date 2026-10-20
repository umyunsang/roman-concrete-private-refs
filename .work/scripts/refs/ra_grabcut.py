"""랜드마크별 GrabCut 윤곽 분할(1000x1400 해상도). 결과: work/objs_<ref>.npz, work/objs_<ref>.json, work/objs_<ref>.png"""
import sys, json
import cv2, numpy as np
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from ra_common import *
from ra_objects_def import OBJS

refs = sys.argv[1:] or list(OBJS)
for ref in refs:
    art = cv2.imread(str(composite_path(ref)))
    img = cv2.resize(art, (1000, 1400), interpolation=cv2.INTER_AREA)
    H, W = img.shape[:2]
    masks, rows = [], []
    for name, kind, (x0, y0, x1, y1), core in OBJS[ref]:
        x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(W - 1, x1), min(H - 1, y1)
        m = np.zeros((H, W), np.uint8)
        bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
        # 액자 가장자리에 닿는 상자는 사각형을 1px 안쪽으로(GrabCut 사각형 규칙)
        rx0, ry0 = max(1, x0), max(1, y0)
        rx1, ry1 = min(W - 2, x1), min(H - 2, y1)
        cv2.grabCut(img, m, (rx0, ry0, rx1 - rx0, ry1 - ry0), bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)
        fg = ((m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD)).astype(np.uint8)
        fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        n, lb, st, _ = cv2.connectedComponentsWithStats(fg)
        keep = np.zeros_like(fg)
        if n > 1:
            big = np.argmax(st[1:, cv2.CC_STAT_AREA]) + 1
            amax = st[big, cv2.CC_STAT_AREA]
            for i in range(1, n):
                if st[i, cv2.CC_STAT_AREA] >= max(40, 0.04 * amax):
                    keep[lb == i] = 1
        ys, xs = np.nonzero(keep)
        bb = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1] if len(xs) else [x0, y0, x1, y1]
        masks.append(keep)
        rows.append({"name": name, "kind": kind, "core": core, "rect": [x0, y0, x1, y1], "bbox": bb,
                     "mask_area_u2": int(keep.sum()), "rect_fill_pct": round(keep.sum() / ((x1 - x0) * (y1 - y0)) * 100, 1)})
    np.savez_compressed(WORK / f"objs_{ref}.npz", masks=np.array(masks, np.uint8))
    json.dump(rows, open(WORK / f"objs_{ref}.json", "w"), ensure_ascii=False, indent=1)
    ov = img.copy()
    rng = np.random.default_rng(3)
    for k, (mm, r) in enumerate(zip(masks, rows)):
        col = rng.integers(40, 255, 3).tolist()
        ov[mm > 0] = (0.45 * ov[mm > 0] + 0.55 * np.array(col)).astype(np.uint8)
        x0, y0, x1, y1 = r["bbox"]
        cv2.rectangle(ov, (x0, y0), (x1, y1), col, 2)
        cv2.putText(ov, str(k + 1), (x0 + 3, y0 + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 3)
        cv2.putText(ov, str(k + 1), (x0 + 3, y0 + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    cv2.imwrite(str(WORK / f"objs_{ref}.png"), ov)
    for k, r in enumerate(rows):
        print(ref, k + 1, r["name"], r["bbox"], r["mask_area_u2"], r["rect_fill_pct"])
