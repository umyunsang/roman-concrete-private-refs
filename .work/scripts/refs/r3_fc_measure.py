"""자금성 실측(정규 1000×1400): 궁역 평행사변형(해자 포함) 마스크, 꼭짓점, 블리드, 재질 구성, 해자 폭, 끌어낸 모형.

- 궁역 바닥(분홍 크림 89.8,4,11)이 바탕 크림(94.9,0,7)과 ΔE 7.6이라 궁역 전용 문턱 ΔE>4를 쓴다(바탕 산포 0).
- 궁역 = (ΔE>4) 중 가장 큰 연결 성분(연표 왼쪽 열·평면도 상자 제외) → 닫힘 → 구멍 메우기.
출력: fc_measure.json, fc_palace_dbg.png
"""
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/refs")
from r3_common import OUT, lab, load_norm, norm01, to_mm  # noqa: E402

ref = "203x-forbiddencity"
im, _ = load_norm(ref)
L = lab(cv2.GaussianBlur(im, (3, 3), 0))
H, W = L.shape[:2]
d = np.linalg.norm(L - np.array([94.9, 0, 7], np.float32), axis=2)
nb4 = d > 4
EXCL = {"HISTORY 왼쪽 열(위)": [35, 405, 180, 862], "HISTORY 왼쪽 열(아래 글자)": [35, 862, 136, 990], "PLANE DRAWING": [38, 1008, 193, 1307], "FOOTER": [50, 1341, 951, 1369]}
reg = nb4.copy()
reg[:405, :] = False  # 궁역은 y≥405
for b in EXCL.values():
    reg[b[1]:b[3], b[0]:b[2]] = False
n, lb, st, _ = cv2.connectedComponentsWithStats(reg.astype(np.uint8), connectivity=8)
i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
pal = lb == i
pal = cv2.morphologyEx(pal.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
ff = pal.copy()
msk = np.zeros((H + 2, W + 2), np.uint8)
cv2.floodFill(ff, msk, (0, 0), 1)
pal = (pal | (1 - ff)) > 0
np.save(os.path.join(OUT, "fc_palace_mask.npy"), pal)
ys, xs = np.nonzero(pal)
box = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
# 꼭짓점: 왼쪽 꼭짓점(x 최소), 아래 꼭짓점(y 최대), 오른쪽 변 블리드 구간
left_v = [int(xs.min()), int(np.median(ys[xs == xs.min()]))]
bot_v = [int(np.median(xs[ys == ys.max()])), int(ys.max())]
redge = np.nonzero(pal[:, W - 1])[0]
top_exit = int(redge.min()) if len(redge) else None
bot_exit = int(redge.max()) if len(redge) else None
# 무대: 궁역 세로 범위 전폭 띠 − 겹친 패널
st_ = np.zeros((H, W), bool)
st_[box[1]:box[3], :] = True
PAN = {"HISTORY 왼쪽 열": [35, 405, 180, 986], "PLANE DRAWING": [38, 1008, 193, 1307], "ROOF BUILDING(아래 일부)": [478, 240, 978, 492]}
pm = np.zeros((H, W), bool)
for b in PAN.values():
    pm[b[1]:b[3], b[0]:b[2]] = True
net = st_ & ~pm
# 끌어낸 모형(코어 군 구성) — 건물+기단+깃발+면적 치수선 포함 상자(크롭 판독)
MODELS = {"A 태화전 모형": [192, 590, 392, 778], "B 중화전 모형": [340, 500, 488, 672], "C 보화전 모형": [458, 428, 640, 618],
          "천안문 모형": [238, 1078, 432, 1262]}
mod_mask = np.zeros((H, W), bool)
for b in MODELS.values():
    sub = nb4[b[1]:b[3], b[0]:b[2]]
    mod_mask[b[1]:b[3], b[0]:b[2]] |= sub
core = pal | mod_mask
cys, cxs = np.nonzero(core)
core_box = [int(cxs.min()), int(cys.min()), int(cxs.max()) + 1, int(cys.max()) + 1]


def near(c, t):
    return np.linalg.norm(L - np.array(c, np.float32), axis=2) < t


cls = {
    "지붕(노랑)": near((81, 11, 55), 14),
    "담장·벽(빨강)": near((50, 51, 30), 12) | near((62, 44, 28), 10) | near((72.9, 30, 24), 9),
    "마당·바닥(분홍 크림)": near((89.8, 4, 11), 4.5),
    "나무(초록)": near((55.7, -28, 17), 16),
    "해자·물(청록)": near((82, -13, -2), 8) | near((76.5, -11, 14), 7),
}
comp_ = {k: round(100 * float((v & pal).sum()) / float(pal.sum()), 1) for k, v in cls.items()}
comp_["기타(난간·계단·그림자·글자 등)"] = round(100 - sum(comp_.values()), 1)
# 해자 폭: 왼쪽 위 변(+30° 띠)에서 x마다 청록 세로 연속 길이
moat = (near((82, -13, -2), 8)) & pal
mw = []
for x in range(200, 900, 50):
    col = np.nonzero(moat[:, x])[0]
    if len(col) == 0:
        continue
    runs, s0 = [], col[0]
    for a, b in zip(col[:-1], col[1:]):
        if b - a > 2:
            runs.append((s0, a))
            s0 = b
    runs.append((s0, col[-1]))
    top = [r for r in runs if r[1] - r[0] >= 6]
    if top:
        r = top[0]
        mw.append((x, int(r[0]), int(r[1]), round((r[1] - r[0] + 1) * np.cos(np.radians(30)), 1)))
res = {
    "palace": {"box_N": box, "box01": norm01(box), "box_mm": to_mm(box),
               "area_pct_poster": round(100 * pal.sum() / (H * W), 1),
               "bbox_pct_poster": round(100 * (box[2] - box[0]) * (box[3] - box[1]) / (H * W), 1),
               "fill_ratio": round(float(pal.sum()) / ((box[2] - box[0]) * (box[3] - box[1])), 2),
               "left_vertex_N": left_v, "bottom_vertex_N": bot_v,
               "right_edge_bleed_y_N": [top_exit, bot_exit],
               "right_edge_bleed_len_pct_H": round(100 * (bot_exit - top_exit) / H, 1) if top_exit is not None else None,
               "composition_pct": comp_},
    "map_stage": {"band_y_N": [box[1], box[3]], "h_pct_poster": round(100 * (box[3] - box[1]) / H, 1),
                  "net_area_pct_poster": round(100 * net.sum() / (H * W), 1)},
    "core_group": {"members": ["궁역(해자·담장·전각 전부)", "끌어낸 모형 A·B·C", "천안문 모형"],
                   "box_N": core_box, "box01": norm01(core_box),
                   "area_pct_poster": round(100 * core.sum() / (H * W), 1),
                   "palace_pct_net_stage": round(100 * (pal & net).sum() / net.sum(), 1),
                   "core_pct_net_stage": round(100 * (core & net).sum() / net.sum(), 1),
                   "models_area_pct_poster": round(100 * mod_mask.sum() / (H * W), 2)},
    "models_box_N": MODELS,
    "models_wh_mm": {k: [round((b[2] - b[0]) * 0.42, 1), round((b[3] - b[1]) * 594 / 1400, 1)] for k, b in MODELS.items()},
    "moat_runs(x,y0,y1,수직단면폭N)": mw,
}
with open(os.path.join(OUT, "fc_measure.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
vis = (im * 0.4 + 150).astype(np.uint8)
cnts, _ = cv2.findContours(pal.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cv2.drawContours(vis, cnts, -1, (0, 0, 255), 2)
for b in MODELS.values():
    cv2.rectangle(vis, (b[0], b[1]), (b[2], b[3]), (255, 0, 0), 2)
cv2.imwrite(os.path.join(OUT, "fc_palace_dbg.png"), vis)
# 윤곽 근사 다각형(꼭짓점)
c = max(cnts, key=cv2.contourArea)
ap = cv2.approxPolyDP(c, 6, True).reshape(-1, 2).tolist()
res["palace"]["outline_approx_N"] = ap
with open(os.path.join(OUT, "fc_measure.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False))
