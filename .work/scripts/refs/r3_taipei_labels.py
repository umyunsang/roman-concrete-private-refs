"""타이베이 지도 라벨 블록: 라벨 글자 마스크(taipei_label.npy)를 9×9 팽창으로 블록화하고 PCA로 기울기를 잰다.

- 지도 무대 안(패널·타이틀 제외)만. 면적 ≥ 150 N² 블록.
- 기울기: 화면 기준(오른쪽 0°, 위 +). 블록 장축 방향.
출력: taipei_labels.json, taipei_labels_dbg.png
"""
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/refs")
from r3_common import OUT, load_norm  # noqa: E402

im, _ = load_norm("203x-taipei")
lab_ = np.load(os.path.join(OUT, "taipei_label.npy"))
H, W = lab_.shape
lab_[:294, :] = False
blk = cv2.dilate(lab_.astype(np.uint8), np.ones((9, 9), np.uint8))
n, lb, st, cen = cv2.connectedComponentsWithStats(blk, connectivity=8)
out = []
vis = (im * 0.5 + 120).astype(np.uint8)
for i in range(1, n):
    if st[i, cv2.CC_STAT_AREA] < 150:
        continue
    ys, xs = np.nonzero((lb == i) & lab_)
    if len(xs) < 40:
        continue
    pts = np.stack([xs, -ys], 1).astype(np.float32)
    pts -= pts.mean(0)
    cov = np.cov(pts.T)
    w, v = np.linalg.eigh(cov)
    elong = float(np.sqrt(w[1] / max(w[0], 1e-6)))
    # 글줄 방향: 투영 단면(글줄 법선 방향 히스토그램)의 분산이 최대인 각
    best, ang = -1, 0.0
    for th in np.arange(-60, 60.5, 1.0):
        t = np.radians(th)
        nrm = np.array([-np.sin(t), np.cos(t)], np.float32)
        proj = pts @ nrm
        h, _ = np.histogram(proj, bins=np.arange(proj.min() - 1, proj.max() + 2, 1.0))
        sc = float(np.var(h))
        if sc > best:
            best, ang = sc, float(th)
    x0, y0, bw, bh = st[i, :4]
    out.append({"box_N": [int(x0), int(y0), int(x0 + bw), int(y0 + bh)], "angle_deg": round(ang, 1), "elong": round(elong, 2),
                "ink_px": int(len(xs))})
    col = (0, 0, 255) if abs(abs(ang) - 30) < 8 else (255, 0, 0)
    cv2.rectangle(vis, (int(x0), int(y0)), (int(x0 + bw), int(y0 + bh)), col, 1)
    cv2.putText(vis, "%.0f" % ang, (int(x0), int(y0) - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.35, col, 1)
cv2.imwrite(os.path.join(OUT, "taipei_labels_dbg.png"), vis)
angs = np.array([o["angle_deg"] for o in out if o["ink_px"] >= 200])
summary = {"n_blocks": len(out), "n_blocks_ink200": int(len(angs)),
           "near_-30": int(np.sum(np.abs(angs + 30) < 8)), "near_+30": int(np.sum(np.abs(angs - 30) < 8)),
           "near_0": int(np.sum(np.abs(angs) < 8)), "near_90": int(np.sum(np.abs(np.abs(angs) - 90) < 8))}
with open(os.path.join(OUT, "taipei_labels.json"), "w", encoding="utf-8") as f:
    json.dump({"summary": summary, "blocks": out}, f, ensure_ascii=False, indent=1)
print(summary)
for o in sorted(out, key=lambda o: o["box_N"][1]):
    print(o)
