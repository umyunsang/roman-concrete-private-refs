"""고해상 타일(1000x933)을 전체 이미지에 정합 -> 2000x2800 합성 아트 생성.
출력: work/<ref>_art2000.png, work/<ref>_hires_mask.png, work/register.json
"""
import json, sys
import cv2, numpy as np
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from ra_common import *

res = {}
for ref, cfg in REFS.items():
    full = cv2.imread(str(cfg["full"]))
    fh, fw = full.shape[:2]
    s0 = fw / ART_W
    gfull = cv2.cvtColor(full, cv2.COLOR_BGR2GRAY).astype(np.float32)
    art = cv2.resize(full, (ART_W, ART_H), interpolation=cv2.INTER_CUBIC)
    hm = np.zeros((ART_H, ART_W), np.uint8)
    r = {"full_size": [fw, fh], "scale_full_per_art": round(s0, 5), "tiles": {}}
    for tid, tp in cfg["tiles"].items():
        tile = cv2.imread(str(tp))
        th, tw = tile.shape[:2]
        best = None
        for s in np.linspace(s0 * 0.97, s0 * 1.03, 25):
            small = cv2.resize(tile, (max(8, int(round(tw * s))), max(8, int(round(th * s)))), interpolation=cv2.INTER_AREA)
            gs = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32)
            if gs.shape[0] >= gfull.shape[0] or gs.shape[1] >= gfull.shape[1]:
                continue
            m = cv2.matchTemplate(gfull, gs, cv2.TM_CCOEFF_NORMED)
            _, mx, _, loc = cv2.minMaxLoc(m)
            if best is None or mx > best[0]:
                best = (mx, s, loc)
        mx, s, loc = best
        ox, oy = loc[0] / s0, loc[1] / s0   # 아트 좌표로 환산(전체 이미지 배율 기준)
        ex = TILE_EXPECT[tid]
        r["tiles"][tid] = {"score": round(float(mx), 4), "best_scale": round(float(s), 5),
                           "scale_ratio_to_full": round(float(s / s0), 4),
                           "offset_art_est": [round(ox, 1), round(oy, 1)], "offset_expected": ex,
                           "tile_size": [tw, th]}
        # 기대 오프셋에 붙임(정합 오차가 작으면)
        X, Y = ex
        art[Y:Y + th, X:X + tw] = tile[:min(th, ART_H - Y), :min(tw, ART_W - X)]
        hm[Y:Y + th, X:X + tw] = 255
    cv2.imwrite(str(composite_path(ref)), art)
    cv2.imwrite(str(mask_path(ref)), hm)
    r["hires_cover_pct"] = round(float((hm > 0).mean() * 100), 1)
    res[ref] = r
    print(ref, json.dumps(r, ensure_ascii=False))
json.dump(res, open(WORK / "register.json", "w"), ensure_ascii=False, indent=1)
