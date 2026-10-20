"""타이베이 실측: 랜드마크 마스크(자르기 다각형 ∩ 오브젝트 층), 코어 군, 지도 무대, 밀도, 강·길 폭, 블리드.

- 좌표: 정규 1000×1400(N). A2 환산 x 0.42mm/N, y 0.4243mm/N.
- 오브젝트 층: r3_taipei_seg.py(비배경 − 길 − 강 − 가는 획) + 크림 받침 보정(용산사·LOVE).
- 화면에서 높은 101 탑이 고궁박물원·스린 판 앞을 가리므로 연결 성분 대신 자르기 다각형과 '먼저 잡은 것 빼기' 순서로 가른다.
출력: taipei_measure.json, taipei_objects.png
"""
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/refs")
from r3_common import OUT, lab, load_norm, norm01, to_mm  # noqa: E402

ref = "203x-taipei"
im, _ = load_norm(ref)
Lb = lab(cv2.GaussianBlur(im, (3, 3), 0))
Z = np.load(os.path.join(OUT, "taipei_layers.npz"))
road, river, obj, thin, nonbg = Z["road"], Z["river"], Z["obj"].copy(), Z["thin"], Z["nonbg"]
H, W = obj.shape


def poly(pts):
    c = np.zeros((H, W), np.uint8)
    cv2.fillPoly(c, [np.array(pts, np.int32)], 1)
    return c > 0


# 크림 받침 보정
ovr = np.zeros((H, W), np.uint8)
cv2.ellipse(ovr, (110, 1017), (90, 68), 0, 0, 360, 1, -1)
ovr = (ovr > 0) | poly([(182, 1078), (263, 1141), (352, 1093), (335, 1072), (290, 1048), (230, 1040)])
ovr &= nonbg & ~river
obj |= ovr
road &= ~ovr

# 타이틀·패널(지도 바깥 층)
TITLE = [293, 60, 710, 217]
PANELS = {  # r3_tightbox.py 실측
    "CITY INFORMATION": [55, 58, 245, 168], "FAMOUS CULTURE AREA": [55, 191, 244, 359],
    "CITY SYMBOL": [55, 387, 240, 485], "NEARBY ATTRACTIONS": [55, 508, 228, 618],
    "HISTORY": [755, 58, 933, 192], "FAMOUS FOOD": [55, 1203, 278, 1323], "TRAFFIC LIGHT": [315, 1203, 431, 1325],
}
FOOTER = [55, 1338, 945, 1362]
offmap = np.zeros((H, W), bool)
for b in list(PANELS.values()) + [TITLE, FOOTER]:
    offmap[b[1]:b[3], b[0]:b[2]] = True
road &= ~offmap
river &= ~offmap
objm = obj & ~offmap
green = np.linalg.norm(Lb - np.array([83, -22, 37], np.float32), axis=2) < 12
# 지도 라벨 글자(청록·남색): b*<-20, a*<3, 40<L<72 (r3_winclusters.py 군집 결과)
Lraw = lab(im)
label = nonbg & (Lraw[..., 2] < -20) & (Lraw[..., 1] < 3) & (Lraw[..., 0] > 40) & (Lraw[..., 0] < 72) & ~offmap
label_d = cv2.dilate(label.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
objm = objm & ~label_d
objm = cv2.morphologyEx(objm.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)) > 0
np.save(os.path.join(OUT, "taipei_label.npy"), label)

# (이름, 분류, 자르기 다각형, 뺄 이름들, 추가 조건)
SPEC = [
    ("시내버스", "탈것", [(818, 565), (915, 565), (915, 640), (818, 640)], [], "notgreen"),
    ("택시", "탈것", [(615, 462), (690, 462), (690, 520), (655, 552), (615, 552)], [], None),
    ("고속철 THSR", "탈것", [(495, 818), (560, 800), (585, 800), (612, 812), (612, 862), (560, 885), (495, 885)], [], None),
    ("MRT", "탈것", [(528, 900), (600, 900), (700, 975), (700, 1030), (640, 1030), (528, 965)], [], None),
    ("LOVE 조형물+판", "코어", [(176, 962), (312, 962), (318, 1000), (360, 1085), (352, 1095), (263, 1145), (176, 1082)], [], "notgreen"),
    ("타이베이 101 탑", "히어로", [(312, 300), (352, 300), (356, 470), (398, 470), (398, 950), (362, 950), (362, 1050), (262, 1050), (262, 470), (300, 470), (305, 385)],
     ["LOVE 조형물+판"], "notgreen"),
    ("101 판+몰", "코어", [(282, 880), (530, 880), (530, 1030), (375, 1103), (290, 1062), (282, 1040)], ["타이베이 101 탑", "LOVE 조형물+판", "MRT"], None),
    ("고궁박물원", "랜드마크", [(356, 285), (672, 285), (672, 425), (600, 468), (510, 528), (440, 492), (395, 472), (356, 472)], ["타이베이 101 탑", "택시"], None),
    ("디화제 기둥", "랜드마크", [(690, 315), (735, 315), (735, 445), (690, 445)], [], None),
    ("시립미술관", "랜드마크", [(650, 420), (960, 420), (960, 640), (650, 640)], ["시내버스", "택시"], None),
    ("스린 야시장", "랜드마크", [(386, 545), (668, 545), (668, 690), (455, 825), (386, 792)], ["타이베이 101 탑"], None),
    ("그랜드 호텔", "랜드마크", [(50, 640), (262, 640), (262, 895), (50, 895)], [], None),
    ("타이베이 중앙역", "랜드마크", [(530, 720), (845, 720), (845, 960), (530, 960)], ["고속철 THSR", "MRT"], None),
    ("공원 판(이름 없음)", "받침", [(770, 600), (1000, 600), (1000, 800), (770, 800)], ["시내버스"], None),
    ("용산사", "랜드마크", [(15, 880), (150, 880), (150, 940), (205, 940), (205, 1090), (15, 1090)], [], None),
    ("라오허제 야시장", "랜드마크", [(805, 795), (985, 795), (985, 1032), (805, 1032)], [], None),
    ("시먼 홍러우", "랜드마크", [(715, 1020), (965, 1020), (965, 1235), (715, 1235)], [], None),
    ("닝샤 야시장", "랜드마크", [(470, 1030), (645, 1030), (645, 1255), (470, 1255)], [], None),
    ("무지개 횡단보도", "랜드마크", [(520, 1210), (705, 1210), (705, 1328), (520, 1328)], [], None),
    ("나무(오른쪽 아래)", "소품", [(900, 1225), (960, 1225), (960, 1295), (900, 1295)], [], None),
]
masks = {}
res = {"landmarks": {}}
for name, kind, clip, excl, cond in SPEC:
    m = objm & poly(clip)
    for e in excl:
        m &= ~masks[e]
    if cond == "notgreen":
        m &= ~green
    # 작은 조각 제거
    n, lb, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=8)
    keep = np.zeros(n, bool)
    keep[1:] = st[1:, cv2.CC_STAT_AREA] >= 40
    m = keep[lb]
    # 견고 상자: 면적 큰 성분부터 누적 97%까지만
    n2, lb2, st2, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=8)
    order = np.argsort(-st2[1:, cv2.CC_STAT_AREA]) + 1
    cum, tot, sel = 0, st2[1:, cv2.CC_STAT_AREA].sum(), []
    for i in order:
        sel.append(i)
        cum += st2[i, cv2.CC_STAT_AREA]
        if cum >= 0.97 * tot:
            break
    m = np.isin(lb2, sel)
    masks[name] = m
    ys, xs = np.nonzero(m)
    box = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    res["landmarks"][name] = {"kind": kind, "box_N": box, "box01": norm01(box),
                              "wh_mm": [round((box[2] - box[0]) * 0.42, 1), round((box[3] - box[1]) * 594 / 1400, 1)],
                              "area_N2": int(m.sum()), "area_mm2": round(float(m.sum()) * 0.42 * 594 / 1400, 0)}

core = masks["타이베이 101 탑"] | masks["101 판+몰"] | masks["LOVE 조형물+판"]
np.save(os.path.join(OUT, "taipei_core_mask.npy"), core)
np.save(os.path.join(OUT, "taipei_landmark_union.npy"), np.logical_or.reduce([m for m in masks.values()]))
ys, xs = np.nonzero(core)
core_box = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
union = np.zeros((H, W), bool)
for m in masks.values():
    union |= m

# 지도 무대: 지도 층(오브젝트·길·강)의 세로 범위, 전폭
mapel = (objm | road | river)
rows = np.nonzero(mapel.sum(1) >= 3)[0]
stage = [0, int(rows.min()), W, int(rows.max()) + 1]
st = np.zeros((H, W), bool)
st[stage[1]:stage[3], :] = True
pm = np.zeros((H, W), bool)
for b in list(PANELS.values()) + [TITLE]:
    pm[b[1]:b[3], b[0]:b[2]] = True
net = st & ~pm
A_st, A_net = st.sum(), net.sum()
res["map_stage"] = {"box_N": stage, "box01": norm01(stage), "h_pct_poster": round(100 * (stage[3] - stage[1]) / H, 1),
                    "net_area_pct_poster(지도 띠 − 겹친 패널)": round(100 * A_net / (H * W), 1),
                    "panels_overlapping_stage": [k for k, b in PANELS.items() if b[3] > stage[1] and b[1] < stage[3]]}
res["core_group"] = {"members": ["타이베이 101 탑", "101 판+몰", "LOVE 조형물+판"],
                     "box_N": core_box, "box01": norm01(core_box), "box_mm": to_mm(core_box),
                     "wh_mm": [round((core_box[2] - core_box[0]) * 0.42, 1), round((core_box[3] - core_box[1]) * 594 / 1400, 1)],
                     "area_mm2": round(float(core.sum()) * 0.42 * 594 / 1400, 0),
                     "area_pct_net_stage": round(100 * core.sum() / A_net, 1),
                     "area_pct_poster": round(100 * core.sum() / (H * W), 1),
                     "bbox_pct_poster": round(100 * (core_box[2] - core_box[0]) * (core_box[3] - core_box[1]) / (H * W), 1),
                     "fill_ratio": round(core.sum() / ((core_box[2] - core_box[0]) * (core_box[3] - core_box[1])), 2)}
# 가장 큰 단일 덩어리 비교
areas = sorted(((v["area_N2"], k) for k, v in res["landmarks"].items()), reverse=True)
res["area_rank"] = [(k, round(100 * a / A_net, 2)) for a, k in areas]
res["density"] = {
    "object_union_pct_net_stage(받침 포함, 길·강·글자 제외)": round(100 * (objm & net).sum() / A_net, 1),
    "labeled_object_union_pct_net_stage": round(100 * (union & net).sum() / A_net, 1),
    "road_pct_net_stage": round(100 * (road & net).sum() / A_net, 1),
    "river_pct_net_stage": round(100 * (river & net).sum() / A_net, 1),
    "thin_text_pct_net_stage": round(100 * (thin & net & ~offmap).sum() / A_net, 1),
    "empty_bg_pct_net_stage": round(100 * (net & ~nonbg).sum() / A_net, 1),
}


def runs_of(rr):
    if len(rr) == 0:
        return []
    segs, s0 = [], rr[0]
    for a, b in zip(rr[:-1], rr[1:]):
        if b - a > 3:
            segs.append([int(s0), int(a)])
            s0 = b
    segs.append([int(s0), int(rr[-1])])
    return [s for s in segs if s[1] - s[0] >= 4]


edge = {}
for nm, sl in {"left": (slice(None), slice(0, 3)), "right": (slice(None), slice(997, 1000))}.items():
    for lname, lm in {"road": road, "river": river, "obj": objm}.items():
        edge[f"{nm}:{lname}"] = runs_of(np.nonzero(lm[sl].any(1))[0])
for nm, sl in {"top": (slice(0, 3), slice(None)), "bottom": (slice(1397, 1400), slice(None))}.items():
    for lname, lm in {"road": road, "river": river, "obj": objm}.items():
        edge[f"{nm}:{lname}"] = runs_of(np.nonzero(lm[sl].any(0))[0])
res["edge_bleed"] = edge
rv = {}
for x in (760, 800, 850, 900, 950, 990):
    rr = runs_of(np.nonzero(river[:, x])[0])
    rv[str(x)] = [(a, b, round((b - a + 1) * np.cos(np.radians(30)), 1)) for a, b in rr if b - a > 8]
res["river_vertical_runs(x: y0,y1,수직폭×cos30=수직 단면 폭 N)"] = rv
rw = []
for x in range(420, 1000, 20):
    for a, b in runs_of(np.nonzero(road[:, x])[0]):
        if 25 <= b - a + 1 <= 70:
            rw.append(b - a + 1)
res["road_width"] = {"n_runs": len(rw), "vertical_run_median_N": float(np.median(rw)),
                     "perp_width_median_N": round(float(np.median(rw)) * np.cos(np.radians(30)), 1),
                     "perp_width_median_mm": round(float(np.median(rw)) * np.cos(np.radians(30)) * 0.42, 1)}
res["panels_N"] = PANELS
res["title_N"] = TITLE
res["footer_N"] = FOOTER
with open(os.path.join(OUT, "taipei_measure.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
vis = (im * 0.3 + 175).astype(np.uint8)
rng = np.random.default_rng(5)
for name, m in masks.items():
    col = np.array([int(v) for v in rng.integers(30, 230, 3)])
    vis[m] = (col * 0.5 + im[m] * 0.5).astype(np.uint8)
vis[road] = (90, 190, 235)
vis[river] = (220, 170, 40)
# 진단: 랜드마크별 자르기 다각형 + 마스크 + 상자
diag = []
big = cv2.resize(im, (W * 2, H * 2), interpolation=cv2.INTER_CUBIC)
for name, kind, clip, excl, cond in SPEC:
    b = res["landmarks"][name]["box_N"]
    xs_ = [p_[0] for p_ in clip]; ys_ = [p_[1] for p_ in clip]
    X0, Y0, X1, Y1 = max(0, min(xs_) - 15), max(0, min(ys_) - 15), min(W, max(xs_) + 15), min(H, max(ys_) + 15)
    c = (big[Y0 * 2:Y1 * 2, X0 * 2:X1 * 2] * 0.5 + 100).astype(np.uint8)
    mm = cv2.resize(masks[name].astype(np.uint8), (W * 2, H * 2), interpolation=cv2.INTER_NEAREST)[Y0 * 2:Y1 * 2, X0 * 2:X1 * 2] > 0
    c[mm] = (big[Y0 * 2:Y1 * 2, X0 * 2:X1 * 2][mm] * 0.6 + np.array([0, 90, 0])).clip(0, 255).astype(np.uint8)
    cv2.polylines(c, [((np.array(clip) - [X0, Y0]) * 2).astype(np.int32)], True, (0, 0, 255), 1)
    cv2.rectangle(c, ((b[0] - X0) * 2, (b[1] - Y0) * 2), ((b[2] - X0) * 2, (b[3] - Y0) * 2), (255, 0, 0), 1)
    cv2.putText(c, name.encode('ascii', 'ignore').decode() or str(len(diag)), (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    cv2.imwrite(os.path.join(OUT, "crops", "taipei_diag_%02d.png" % len(diag)), c)
    diag.append(name)
print("diag:", list(enumerate(diag)))
cnts, _ = cv2.findContours(core.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cv2.drawContours(vis, cnts, -1, (0, 0, 255), 2)
cv2.imwrite(os.path.join(OUT, "taipei_objects.png"), vis)
print(json.dumps({k: res[k] for k in ("map_stage", "core_group", "density", "edge_bleed", "road_width", "area_rank")}, ensure_ascii=False))
print(json.dumps(res["river_vertical_runs(x: y0,y1,수직폭×cos30=수직 단면 폭 N)"], ensure_ascii=False))
for k, v in res["landmarks"].items():
    print("%-16s %-5s box %s wh_mm %s area_mm2 %s" % (k, v["kind"], v["box_N"], v["wh_mm"], v["area_mm2"]))
