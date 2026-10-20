"""타이베이 지면 분할(정규 1000×1400).

층
- 바탕: 세로 그라데이션(r3_bgmask), ΔE>10 이 비배경.
- 길(도로): 크림색 계열(ΔE<9) 중 폭 48 미만의 띠. 원판 열림(지름 49)으로 판(받침)과 가른다.
- 강: 단수이강 청록(ΔE<7), 강 구역 x≥620·y770~1175 안에서만.
- 글자·지시선: 비배경 중 5×5 열림으로 사라지는 가는 획.
- 오브젝트(받침 포함) = 비배경 − 길 − 강 − 가는 획.
출력: taipei_layers.png(색 분류 시각화), taipei_layers.npz
"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/refs")
from r3_common import OUT, lab, load_norm  # noqa: E402

ref = "203x-taipei"
im, _ = load_norm(ref)
L = lab(cv2.GaussianBlur(im, (3, 3), 0))
nonbg = cv2.imread(os.path.join(OUT, f"{ref}_nonbg.png"), 0) > 0


def near(c, t):
    return np.linalg.norm(L - np.array(c, np.float32), axis=2) < t


cream = (near((82.7, -5, 24), 9) | near((79.2, -3, 14), 9) | near((86.9, -4, 19.5), 9)
         | near((99.2, -3, 10), 7) | near((55.7, -1, 22), 8)) & nonbg
k49 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (49, 49))
cream_u8 = cream.astype(np.uint8)
plates = cv2.morphologyEx(cream_u8, cv2.MORPH_OPEN, k49) > 0
road = cream & ~plates
# 강
riverzone = np.zeros_like(nonbg)
riverzone[770:1175, 620:1000] = True
river = near((72.9, -18, -11.5), 7) & riverzone & nonbg
river = cv2.morphologyEx(river.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0
# 가는 획(글자·지시선)
rest = nonbg & ~road & ~river
k5 = np.ones((5, 5), np.uint8)
rest_open = cv2.morphologyEx(rest.astype(np.uint8), cv2.MORPH_OPEN, k5) > 0
thin = rest & ~rest_open
obj = rest_open
np.savez_compressed(os.path.join(OUT, "taipei_layers.npz"), road=road, river=river, obj=obj, thin=thin, nonbg=nonbg)
vis = (im * 0.35 + 165).astype(np.uint8)
vis[road] = (90, 190, 235)      # 길: 주황빛 노랑(BGR)
vis[river] = (220, 170, 40)     # 강: 파랑
vis[obj] = (im[obj] * 0.9).astype(np.uint8)
vis[thin] = (0, 0, 200)         # 가는 획: 빨강
cv2.imwrite(os.path.join(OUT, "taipei_layers.png"), vis)
print("road %.1f%% river %.1f%% obj %.1f%% thin %.1f%%" % tuple(100 * m.mean() for m in (road, river, obj, thin)))
