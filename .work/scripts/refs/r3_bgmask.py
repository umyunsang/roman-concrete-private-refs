"""바탕(배경) 모델과 비배경 마스크(정규 1000×1400).

바탕 모델(탐침 r3_bgprobe.py 결과에 근거)
- 타이베이: 세로 그라데이션. 행마다 왼쪽 띠 x0~20의 Lab 중앙값(모든 행에서 산포 ≤5, 물체 없음)을 9행 중앙값으로 평활.
- 제주: 바다 단색 Lab(88.4, -11, -10), 산포 ≤2.3.
- 자금성: 크림 단색 Lab(94.9, 0, 7), 산포 0.
비배경 = 바탕과 ΔE > T.
출력: <ref>_nonbg.png, <ref>_nonbg_vis.jpg, <ref>_dE.npy(float16)
"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/refs")
from r3_common import OUT, lab, load_norm  # noqa: E402

CFG = {
    "203x-taipei": {"mode": "leftstrip", "T": 10.0},
    "203x-jeju": {"mode": "const", "c": (88.4, -11.0, -10.0), "T": 6.0},
    "203x-forbiddencity": {"mode": "const", "c": (94.9, 0.0, 7.0), "T": 8.0},
}

for ref_id, cfg in CFG.items():
    im, _ = load_norm(ref_id)
    L = lab(cv2.GaussianBlur(im, (3, 3), 0))
    H, W = L.shape[:2]
    if cfg["mode"] == "leftstrip":
        strip = np.median(L[:, 0:20], axis=1)
        bg = np.array([np.median(strip[max(0, y - 4):y + 5], axis=0) for y in range(H)], np.float32)
    else:
        bg = np.tile(np.array(cfg["c"], np.float32), (H, 1))
    d = np.linalg.norm(L - bg[:, None, :], axis=2)
    m = (d > cfg["T"]).astype(np.uint8) * 255
    np.save(os.path.join(OUT, f"{ref_id}_bg.npy"), bg)
    np.save(os.path.join(OUT, f"{ref_id}_dE.npy"), d.astype(np.float16))
    cv2.imwrite(os.path.join(OUT, f"{ref_id}_nonbg.png"), m)
    vis = im.copy()
    vis[m == 0] = (vis[m == 0] * 0.2 + 200).astype(np.uint8)
    cv2.imwrite(os.path.join(OUT, f"{ref_id}_nonbg_vis.jpg"), vis, [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(ref_id, "T=%.0f nonbg %.1f%%" % (cfg["T"], 100 * (m > 0).mean()))
