"""고해상 타일 01·04·05를 전체 포스터(정규 1000×1400)에 다중 배율 템플릿 매칭으로 정합한다.

출력: refs-analysis/r3_register.json
"""
import sys

import cv2
import numpy as np

sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/refs")
from r3_common import NH, NW, REFS, imread, load_norm, save_json  # noqa: E402

res = {}
for ref_id, spec in REFS.items():
    full, (fw, fh) = load_norm(ref_id)
    g = cv2.cvtColor(full, cv2.COLOR_BGR2GRAY).astype(np.float32)
    res[ref_id] = {"full_px": [fw, fh], "tiles": {}}
    for tid, rel in spec["tiles"].items():
        t = imread(rel)
        th, tw = t.shape[:2]
        tg = cv2.cvtColor(t, cv2.COLOR_BGR2GRAY).astype(np.float32)
        best = None
        for s in np.arange(0.44, 0.565, 0.0025):
            w, h = int(round(tw * s)), int(round(th * s))
            if w >= NW or h >= NH:
                continue
            ts = cv2.resize(tg, (w, h), interpolation=cv2.INTER_AREA)
            r = cv2.matchTemplate(g, ts, cv2.TM_CCOEFF_NORMED)
            _, mx, _, loc = cv2.minMaxLoc(r)
            if best is None or mx > best[0]:
                best = (float(mx), float(s), loc, (w, h))
        sc, s, (x, y), (w, h) = best
        res[ref_id]["tiles"][tid] = {
            "file": rel,
            "tile_px": [tw, th],
            "score": round(sc, 4),
            "scale_to_norm": round(s, 4),
            "box_norm1000": [x, y, x + w, y + h],
            "native_px_per_norm": round(1 / s, 3),
        }
        print(ref_id, tid, "score %.3f scale %.4f box" % (sc, s), [x, y, x + w, y + h])
p = save_json("r3_register.json", res)
print("saved", p)
