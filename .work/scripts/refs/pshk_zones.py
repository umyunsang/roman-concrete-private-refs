"""파리·상하이·홍콩 구획·코어 군·밀도·간격을 계산하고 확인용 구획 그림을 그린다 (2026-10-18).

입력
- frame.json(타이틀·패널·푸터, pshk_frame.py), <ref>_objects.json·_objmasks.npy(GrabCut, pshk_objects.py),
  <ref>_kmeans_lbl.npy(팔레트 군집, pshk_palette.py)
- 손으로 잰 값(확대 판독): 히어로 상자(안테나 끝~받침), 지도 무대 세로 범위, 강 통로 다각형, 코어 라벨 상자
출력
- <ref>_zones.json(정규 좌표 구획, 코어 군·밀도 지표), refs-analysis/<ref>_zones.png(확인용 구획 그림)
입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
사용: uv run --no-project --with opencv-python-headless --with numpy --with pillow python pshk_zones.py <ref_id>
"""
import json
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from pshk_common import FONT, MMX, MMY, OUT, WORK, H, W, poster

SQ3 = np.sqrt(3.0)

CFG = {
    "203x-paris": {
        "title_ko": "파리",
        "stage_y": (279, 1326),
        "hero": ("에펠탑(히어로)", (316, 236, 751, 1206)),
        "core_objs": ["에펠탑(탑)", "샹드마르스 받침 판", "메트로 입구"],
        "core_labels": [("Tour Eiffel 라벨", (613, 1088, 707, 1207)), ("Métro entrée 라벨", (273, 893, 332, 947))],
        # 강: 팔레트 군집 + 통로 다각형. 코어에 넣는 강 구간은 core_river_clip 다각형과 겹치는 부분.
        "river": {"name": "센강", "clusters": [9], "corridor": [[(1000, 445), (1000, 557), (300, 961), (300, 1215), (236, 1215), (236, 935),
                                                                    (300, 909), (850, 592)]],
                  "note": "+30° 대각 띠(세로 두께 43~51px = 18~22mm, x 720~760에서 실측), 오른쪽 변에서 시테섬 판을 감싸며 들어와(y 445~557) 루브르–오르세, 콩코르드–샹드마르스 사이를 지나 무대 앞 왼쪽 모서리에서 세로 폭포(x 236~300, y 935~1215)로 허공에 떨어진다"},
        "roads": [],
        "core_river_clip": [(236, 840), (480, 840), (480, 1215), (236, 1215)],
        "sea": None,
        "landmarks_merge": {"콩코르드·튈르리(관람차 포함)": ["콩코르드(오벨리스크·관람차)", "튈르리 정원 판"]},
        "geo": {  # 근사 위경도(일반 지도 지식, ±0.1km)
            "에펠탑(탑)": (48.85826, 2.29450), "개선문+에투알 판": (48.87378, 2.29504), "사크레쾨르+판": (48.88671, 2.34310),
            "가르니에 오페라": (48.87197, 2.33160), "콩코르드(오벨리스크·관람차)": (48.86560, 2.32122), "튈르리 정원 판": (48.86349, 2.32748),
            "루브르 박물관": (48.86106, 2.33584), "퐁피두 센터+판": (48.86064, 2.35222), "노트르담+시테섬 판": (48.85297, 2.34995),
            "오르세 미술관": (48.85998, 2.32656), "로댕 미술관+정원 판": (48.85530, 2.31583),
        },
        "hero_obj": "에펠탑(탑)",
        "geo_origin": "에펠탑(탑)",
        "hero_extra": [(534, 236, 547, 335)],
        # 확대 판독으로 그린 에펠탑 외곽(다리 사이 아치 열림은 받침 판이라 덩어리에 포함)
        "hero_poly": [(535, 236), (546, 236), (546, 330), (557, 345), (563, 380), (575, 500), (590, 600), (598, 700), (605, 780), (622, 800),
                      (622, 840), (633, 880), (667, 905), (668, 1000), (760, 1085), (712, 1118), (613, 1172), (548, 1208), (490, 1175),
                      (370, 1118), (316, 1083), (419, 990), (417, 905), (450, 880), (461, 840), (463, 800), (480, 780), (482, 700),
                      (490, 600), (507, 500), (517, 380), (522, 345), (535, 330)],
    },
    "203x-shanghai": {
        "title_ko": "상하이",
        "stage_y": (249, 1211),
        "hero": ("동방명주(히어로)", (505, 103, 616, 748)),
        "core_objs": ["동방명주(탑)", "동방명주 받침 판", "진마오 타워", "상하이 타워", "상하이 세계금융센터", "중국미술관", "오로라 미술관",
                      "녹지 공원 판(라벨 없음)", "지하철", "크루즈"],
        "core_labels": [("동방명주 라벨", (453, 263, 537, 377)), ("진마오 라벨", (596, 260, 657, 347)), ("SWFC 라벨", (791, 283, 867, 387)),
                        ("상하이 타워 라벨", (623, 733, 697, 862)), ("오로라 라벨", (698, 808, 777, 907)), ("중국미술관 라벨", (908, 748, 982, 852)),
                        ("크루즈 라벨", (458, 828, 547, 902)), ("지하철 라벨", (528, 868, 592, 947)), ("황푸강 라벨", (408, 628, 482, 672))],
        "river": {"name": "황푸강", "clusters": [1], "note": "'<' 띠: 윗팔 30°(세로 두께 46~47px = 19.5mm), 둥근 굽이(x 328~480), 앞팔 30°(72~73px = 30.8mm). 두 끝 모두 오른쪽 변 블리드(윗팔 y 314~361, 앞팔 y 1138~1211)", "corridor": [[(1000, 314), (480, 611), (420, 640), (360, 680), (330, 730), (328, 790),
                                                                   (350, 835), (400, 866), (1000, 1211), (1000, 1138), (450, 820), (430, 790),
                                                                   (428, 740), (440, 700), (470, 664), (1000, 361)]]},
        "core_river_clip": [(320, 270), (1000, 270), (1000, 700), (770, 700), (770, 1215), (320, 1215)],
        "core_river_mode": "visible",
        "roads": [("시내 도로(V자, 시내버스)", (0, 800, 280, 960), "±30° 두 갈래가 버스 자리에서 꺾인다. 세로 두께 약 35px(눈 판독)")],
        "extra_zones": [("와이탄 강변 띠(4채)", "other", (269, 802, 696, 1145), "상하이 총회·강해관·HSBC·아시아 빌딩이 앞팔 강둑을 따라 한 줄. 라벨 4개 모두 −30°(강과 평행)")],
        "sea": None,
        "landmarks_merge": {},
        "geo": {
            "동방명주(탑)": (31.23970, 121.49977), "진마오 타워": (31.23680, 121.50150), "상하이 타워": (31.23350, 121.50550),
            "상하이 세계금융센터": (31.23470, 121.50780), "중국미술관": (31.18630, 121.49300), "록번드 미술관": (31.24260, 121.48640),
            "사순 빌딩·중국은행": (31.23990, 121.48580), "상하이 총회": (31.23340, 121.48880), "강해관(세관)": (31.23700, 121.48740),
            "HSBC 빌딩": (31.23640, 121.48760), "아시아 빌딩": (31.23290, 121.48900), "예원+연못 판": (31.22720, 121.49210),
            "난푸대교": (31.21080, 121.49780),
        },
        "hero_obj": "동방명주(탑)",
        "geo_origin": "동방명주(탑)",
        "hero_extra": [(555, 103, 567, 250)],
    },
    "203x-hongkong": {
        "title_ko": "홍콩",
        "stage_y": (225, 1225),
        "hero": ("ICC(최고 높이, 왼쪽 기둥)", (47, 497, 200, 1200)),
        "core_objs": ["센트럴 플라자", "리포 센터", "중국은행 타워", "의학박물관", "더 센터", "컨벤션 센터", "관람차+판", "해사박물관(센트럴 부두)"],
        "core_labels": [("센트럴 플라자 라벨", (168, 348, 237, 432)), ("리포 라벨", (373, 228, 457, 322)), ("중국은행 라벨", (553, 293, 617, 362)),
                        ("의학박물관 라벨", (603, 348, 692, 412)), ("더 센터 라벨", (826, 278, 882, 347)),
                        ("컨벤션 센터 라벨", (458, 543, 542, 612)), ("관람차 라벨", (620, 573, 702, 652)), ("해사박물관 라벨", (763, 723, 842, 792))],
        "pillars": ["ICC(왼쪽 기둥)", "2IFC(오른쪽 기둥)"],
        "river": {"name": "빅토리아 항(수로)", "clusters": [8, 1, 3], "note": "두 땅판 사이 −30°(오른쪽 아래로) 수로, 세로 두께 약 68px = 28.9mm(x 230 실측), 물결무늬. 어귀(x 493~565, y 1022~1098)에서 앞바다로 열린다", "corridor": [[(190, 700), (200, 712), (480, 870), (565, 1022), (493, 1098),
                                                                             (430, 1065), (300, 905), (190, 805)]]},
        "core_river_clip": [(185, 690), (570, 690), (570, 1100), (185, 1100)],
        "core_river_mode": "visible",
        "sea": {"name": "앞바다(두 땅판 앞, 하단 패널 받침)", "poly": [(0, 1338), (493, 1095), (560, 1025), (915, 1225), (1000, 1160), (1000, 1338)]},
        "roads": [("섬 도로 고리(택시)", (650, 905, 1000, 1135), "회색 도로 고리, ±30° 직선과 둥근 모서리. 땅 마스크 성분·택시 상자로 잰 범위")],
        "extra_zones": [("구룡 땅판(앞 왼쪽)", "other", (0, 671, 493, 1338), "갈회색 땅 #7e796a. 앞 모서리 (0,1338)→(493,1095)px 30°, 옆면 약 49px(20.8mm). 왼쪽·아래 블리드"),
                        ("홍콩섬 땅판(뒤 오른쪽)", "other", (189, 323, 1000, 1225), "윗면 앞 모서리 (620,1016)→(850,1148)px 29.9°, 옆면 43px(18.2mm). 뒤 오른쪽 녹색 언덕(피크)")],
        "geo_origin": "관람차+판",
        "landmarks_merge": {},
        "geo": {
            "ICC(왼쪽 기둥)": (22.30330, 114.16010), "센트럴 플라자": (22.28010, 114.17360), "리포 센터": (22.27940, 114.16490),
            "중국은행 타워": (22.27940, 114.16170), "피크 타워": (22.27110, 114.14980), "의학박물관": (22.28280, 114.15010),
            "더 센터": (22.28390, 114.15460), "2IFC(오른쪽 기둥)": (22.28510, 114.15890), "컨벤션 센터": (22.28290, 114.17330),
            "관람차+판": (22.28530, 114.16130), "해사박물관(센트럴 부두)": (22.28660, 114.16250), "우주박물관": (22.29420, 114.17190),
            "문화센터": (22.29370, 114.17000), "시계탑(침사추이)": (22.29360, 114.16930),
        },
        "hero_obj": "ICC(왼쪽 기둥)",
    },
}


def poly_mask(polys):
    m = np.zeros((H, W), np.uint8)
    for p in polys:
        cv2.fillPoly(m, [np.array(p, np.int32)], 1)
    return m


def bbox_of(m):
    ys, xs = np.where(m > 0)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def fill_silhouette(m, k=9):
    c = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((k, k), np.uint8))
    ff = c.copy()
    h, w = c.shape
    mm = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(ff, mm, (0, 0), 1)
    holes = (ff == 0).astype(np.uint8)
    return np.clip(c + holes, 0, 1)


def nb(b):
    return [round(b[0] / W, 4), round(b[1] / H, 4), round(b[2] / W, 4), round(b[3] / H, 4)]


def mmb(b):
    return [round(b[0] * MMX, 1), round(b[1] * MMY, 1), round(b[2] * MMX, 1), round(b[3] * MMY, 1)]


def gap_mm(a, b):
    dx = max(0, max(a[0], b[0]) - min(a[2], b[2])) * MMX
    dy = max(0, max(a[1], b[1]) - min(a[3], b[3])) * MMY
    return float(np.hypot(dx, dy))


def foot(b):
    """등각 상자 바닥 중심 근사: 바닥 모서리에서 화면 폭의 0.289배 위."""
    return ((b[0] + b[2]) / 2, b[3] - 0.289 * (b[2] - b[0]))


def to_plan(p, o):
    sx, sy = (p[0] - o[0]) * MMX, (p[1] - o[1]) * MMY
    return np.array([sy + sx / SQ3, sy - sx / SQ3])


def main():
    rid = sys.argv[1]
    cfg = CFG[rid]
    img = poster(rid)
    frame = json.load(open(f"{WORK}/frame.json"))[rid]
    objs = json.load(open(f"{WORK}/{rid}_objects.json"))
    masks = np.load(f"{WORK}/{rid}_objmasks.npy")
    lbl = np.load(f"{WORK}/{rid}_kmeans_lbl.npy")
    names = [o["name"] for o in objs]
    y0, y1 = cfg["stage_y"]
    stage = np.zeros((H, W), np.uint8)
    stage[y0:y1, :] = 1
    stage_area = float(stage.sum())

    # 히어로 실루엣: GrabCut 마스크 + 손으로 잰 상자 안 안테나 보강(채움)
    hero_name, hb = cfg["hero"]
    hi = names.index(cfg["hero_obj"])
    hero_m = fill_silhouette(masks[hi].copy(), 9)
    for ex0, ey0, ex1, ey1 in cfg.get("hero_extra", []):  # GrabCut이 놓친 가는 안테나(확대 판독)
        sub = img[ey0:ey1, ex0:ex1]
        bgc = np.median(np.concatenate([img[ey0:ey1, ex0 - 6:ex0 - 2].reshape(-1, 3), img[ey0:ey1, ex1 + 2:ex1 + 6].reshape(-1, 3)]), axis=0)
        dd = np.sqrt(((sub.astype(np.float32) - bgc) ** 2).sum(-1))
        hero_m[ey0:ey1, ex0:ex1] |= (dd > 40).astype(np.uint8)
    if cfg.get("hero_poly"):
        hero_m = poly_mask([cfg["hero_poly"]])
    masks = masks.copy()
    masks[hi] = hero_m

    # 강
    rv = cfg["river"]
    corr = poly_mask(rv["corridor"])
    water = np.isin(lbl, rv["clusters"]).astype(np.uint8)
    river_vis = (corr & water).astype(np.uint8)
    river_vis = cv2.morphologyEx(river_vis, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    river_bb = bbox_of(corr)
    river_vis_bb = bbox_of(river_vis)
    # 강 폭: 통로 다각형의 세로 두께 중앙값 × cos30 (수직 낙차 구간 제외)
    col_th = corr[:, :].sum(0)
    th = [int(v) for v in col_th if v > 0]
    river_vthick_med = float(np.median(th)) if th else 0.0

    # 바다(HK)
    sea_m = None
    if cfg.get("sea"):
        sea_m = poly_mask([cfg["sea"]["poly"]])

    # 코어 군
    core_m = np.zeros((H, W), np.uint8)
    for n in cfg["core_objs"]:
        core_m |= masks[names.index(n)]
    core_m |= hero_m if cfg["hero_obj"] in cfg["core_objs"] else 0
    clip = poly_mask([cfg["core_river_clip"]])
    if cfg.get("core_river_mode", "corridor") == "visible":
        # 보이는 물 화소만(앞에 그려진 건물을 강으로 세지 않도록). 반사광 줄무늬 틈은 9px 닫힘으로 메운다.
        rv_closed = cv2.morphologyEx(river_vis, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        core_river = (rv_closed & corr & clip).astype(np.uint8)
    else:
        core_river = (corr & clip).astype(np.uint8)
    core_m |= core_river
    for _, b in cfg["core_labels"]:
        core_m[b[1]:b[3], b[0]:b[2]] = 1
    core_ink = core_m.copy()
    core_foot = fill_silhouette(cv2.morphologyEx(core_m, cv2.MORPH_CLOSE, np.ones((31, 31), np.uint8)), 3)
    core_bb = bbox_of(core_m)
    cnts, _ = cv2.findContours(core_foot, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    hull = cv2.convexHull(np.vstack(cnts))
    hull_m = np.zeros((H, W), np.uint8)
    cv2.fillPoly(hull_m, [hull], 1)
    core = {
        "bbox_px": core_bb, "bbox_norm": nb(core_bb), "bbox_mm": mmb(core_bb),
        "bbox_area_pct_of_stage": round((core_bb[2] - core_bb[0]) * (min(core_bb[3], y1) - max(core_bb[1], y0)) / stage_area * 100, 1),
        "footprint_pct_of_stage": round(float((core_foot & stage).sum()) / stage_area * 100, 1),
        "ink_pct_of_stage": round(float((core_ink & stage).sum()) / stage_area * 100, 1),
        "hull_pct_of_stage": round(float((hull_m & stage).sum()) / stage_area * 100, 1),
        "centroid_norm": [round(float(np.where(core_foot)[1].mean()) / W, 3), round(float(np.where(core_foot)[0].mean()) / H, 3)],
        "footprint_area_mm2": round(float(core_foot.sum()) * MMX * MMY),
    }
    # 기둥 포함 변형(HK)
    if cfg.get("pillars"):
        cm2 = core_m.copy()
        for n in cfg["pillars"]:
            cm2 |= masks[names.index(n)]
        cm2 |= river_vis
        f2 = fill_silhouette(cv2.morphologyEx(cm2, cv2.MORPH_CLOSE, np.ones((31, 31), np.uint8)), 3)
        b2 = bbox_of(cm2)
        core["with_pillars"] = {"bbox_px": b2, "bbox_norm": nb(b2), "footprint_pct_of_stage": round(float((f2 & stage).sum()) / stage_area * 100, 1)}

    # 밀도: 오브젝트 합집합(받침 포함) / 지도 무대
    union = np.clip(masks.sum(0), 0, 1).astype(np.uint8)
    union[hero_m > 0] = 1
    dens = {
        "objects_union_pct_of_stage": round(float((union & stage).sum()) / stage_area * 100, 1),
        "objects_union_pct_of_poster": round(float(union.mean()) * 100, 1),
        "river_visible_pct_of_stage": round(float((river_vis & stage).sum()) / stage_area * 100, 1),
        "river_corridor_pct_of_stage": round(float((corr & stage).sum()) / stage_area * 100, 1),
    }
    if sea_m is not None:
        dens["sea_pct_of_stage"] = round(float((sea_m & stage).sum()) / stage_area * 100, 1)
        dens["sea_pct_of_poster"] = round(float(sea_m.mean()) * 100, 1)

    # 랜드마크 표(합치기 반영)
    merged = {}
    for k, parts in cfg["landmarks_merge"].items():
        mm_ = np.zeros((H, W), np.uint8)
        for p in parts:
            mm_ |= masks[names.index(p)]
        merged[k] = (bbox_of(mm_), int(mm_.sum()), parts)
    lm = []
    skip = set(p for v in cfg["landmarks_merge"].values() for p in v)
    for o, m in zip(objs, masks):
        if o["name"] in skip:
            continue
        b = o["bbox_px"]
        if o["name"] == cfg["hero_obj"]:
            b = list(cfg["hero"][1])
        lm.append({"name": o["name"], "kind": o["kind"], "bbox_px": b, "area_mm2": o["area_mm2"]})
    for k, (b, a, parts) in merged.items():
        lm.append({"name": k, "kind": "랜드마크", "bbox_px": b, "area_mm2": round(a * MMX * MMY)})
    for r in lm:
        b = r["bbox_px"]
        r["bbox_norm"] = nb(b)
        r["w_mm"], r["h_mm"] = round((b[2] - b[0]) * MMX, 1), round((b[3] - b[1]) * MMY, 1)
        r["pct_of_stage"] = round(r["area_mm2"] / (stage_area * MMX * MMY) * 100, 2)
    # 가장 가까운 이웃 상자 간격(탈것·받침 제외 랜드마크끼리)
    L_ = [r for r in lm if r["kind"] in ("랜드마크", "히어로")]
    for r in L_:
        g = [gap_mm(r["bbox_px"], q["bbox_px"]) for q in L_ if q is not r]
        r["nn_gap_mm"] = round(min(g), 1) if g else None
    gaps = [r["nn_gap_mm"] for r in L_ if r.get("nn_gap_mm") is not None]

    # 히어로 바닥에서 각 랜드마크까지 평면 거리(등각 역투영, mm)와 실제 거리·방위 비교
    hero_b = cfg["hero"][1]
    gname = cfg.get("geo_origin", cfg["hero_obj"])
    gb = hero_b if gname == cfg["hero_obj"] else next(r["bbox_px"] for r in lm if r["name"] == gname)
    o_ = foot(gb)
    geo = cfg.get("geo", {})
    lat0, lon0 = geo.get(gname, (None, None))
    georows = []
    for r in lm:
        if r["kind"] not in ("랜드마크", "히어로") or r["name"] == gname:
            continue
        P = to_plan(foot(r["bbox_px"]), o_)
        row = {"name": r["name"], "plan_mm": [round(float(P[0]), 1), round(float(P[1]), 1)], "plan_dist_mm": round(float(np.hypot(*P)), 1),
               "screen_dist_mm": round(float(np.hypot((foot(r["bbox_px"])[0] - o_[0]) * MMX, (foot(r["bbox_px"])[1] - o_[1]) * MMY)), 1)}
        key = r["name"]
        if key not in geo and key in cfg["landmarks_merge"]:
            key = cfg["landmarks_merge"][key][0]
        if lat0 is not None and key in geo:
            la, lo = geo[key]
            e = (lo - lon0) * 111.320 * np.cos(np.radians(lat0))
            n = (la - lat0) * 110.574
            row["real_km"] = round(float(np.hypot(e, n)), 2)
            row["real_en_km"] = [round(float(e), 2), round(float(n), 2)]
        georows.append(row)
    fit = None
    pts = [g for g in georows if "real_km" in g and g["real_km"] > 0.05]
    if len(pts) >= 4:
        # 회전만 맞춤(방위 충실도): 실제 방위각과 평면 방위각 차이의 원형 평균
        d = []
        for g in pts:
            ar = np.arctan2(g["real_en_km"][1], g["real_en_km"][0])
            ap = np.arctan2(-g["plan_mm"][1], g["plan_mm"][0])  # 평면 X=오른쪽 아래 축, Y=왼쪽 아래 축 → (X, -Y)를 오른손 좌표로
            d.append(ap - ar)
        th = float(np.angle(np.mean(np.exp(1j * np.array(d)))))
        dev = [float(np.degrees(np.angle(np.exp(1j * (x - th))))) for x in d]
        for g, dv in zip(pts, dev):
            g["bearing_dev_deg"] = round(dv, 1)
        # 거리 압축: log(평면) = a + b log(실제)
        xr = np.log([g["real_km"] for g in pts])
        yr = np.log([g["plan_dist_mm"] for g in pts])
        bcoef, acoef = np.polyfit(xr, yr, 1)
        # 화면에서 실제 북쪽이 가리키는 방향(화면 각, 오른쪽 위 +)
        north = np.array([np.cos(th + np.pi / 2), np.sin(th + np.pi / 2)])  # (X, -Y) 좌표의 북쪽 단위벡터
        Xn, Yn = north[0], -north[1]
        sx, sy = (Xn - Yn) * np.cos(np.radians(30)), (Xn + Yn) * 0.5
        north_screen = float(np.degrees(np.arctan2(-sy, sx)))
        fit = {"rotation_deg": round(np.degrees(th), 1), "bearing_abs_dev_median_deg": round(float(np.median(np.abs(dev))), 1),
               "bearing_abs_dev_max_deg": round(float(np.max(np.abs(dev))), 1),
               "dist_exponent": round(float(bcoef), 3), "dist_coef_mm": round(float(np.exp(acoef)), 1),
               "real_km_range": [min(g["real_km"] for g in pts), max(g["real_km"] for g in pts)],
               "plan_mm_range": [min(g["plan_dist_mm"] for g in pts), max(g["plan_dist_mm"] for g in pts)],
               "north_on_screen_deg": round(north_screen, 1), "n": len(pts)}

    # 구획 목록(정규 좌표)
    zones = []
    for r in frame:
        zones.append({"name": r["name"], "kind": r["kind"], "bbox_norm": r["norm"], "px": r["px"],
                      "note": f"{r['w_mm']}×{r['h_mm']}mm, 포스터 면적 {r['area_pct']}%"})
    zones.append({"name": "지도 무대(전폭 띠)", "kind": "map", "bbox_norm": nb([0, y0, W, y1]), "px": [0, y0, W, y1],
                  "note": f"y {y0}~{y1}px = {round(y0 * MMY, 1)}~{round(y1 * MMY, 1)}mm, 세로 {round((y1 - y0) / H * 100, 1)}%"})
    zones.append({"name": "코어 군", "kind": "core_group", "bbox_norm": core["bbox_norm"], "px": core_bb,
                  "note": f"덩어리(닫힘) 면적 = 지도 무대의 {core['footprint_pct_of_stage']}%, 상자 {core['bbox_area_pct_of_stage']}%"})
    zones.append({"name": hero_name, "kind": "hero", "bbox_norm": nb(hero_b), "px": list(hero_b),
                  "note": f"{round((hero_b[2] - hero_b[0]) * MMX, 1)}×{round((hero_b[3] - hero_b[1]) * MMY, 1)}mm, 포스터 높이의 {round((hero_b[3] - hero_b[1]) / H * 100, 1)}%"})
    for r in lm:
        if r["name"] == cfg["hero_obj"]:
            continue
        zones.append({"name": r["name"], "kind": "landmark" if r["kind"] in ("랜드마크", "히어로", "판") else ("other" if r["kind"] != "히어로 받침" else "landmark"),
                      "bbox_norm": r["bbox_norm"], "px": r["bbox_px"], "note": f"{r['w_mm']}×{r['h_mm']}mm, {r['kind']}"})
    zones.append({"name": rv["name"], "kind": "river", "bbox_norm": nb(river_bb), "px": river_bb,
                  "note": rv.get("note", "")})
    for en, ek, eb, enote in cfg.get("extra_zones", []):
        zones.append({"name": en, "kind": ek, "bbox_norm": nb(eb), "px": list(eb), "note": enote})
    for rn, rb, rnote in cfg.get("roads", []):
        zones.append({"name": rn, "kind": "road", "bbox_norm": nb(rb), "px": list(rb), "note": rnote})
    if sea_m is not None:
        sb = bbox_of(sea_m)
        zones.append({"name": cfg["sea"]["name"], "kind": "sea", "bbox_norm": nb(sb), "px": sb, "note": f"지도 무대의 {dens['sea_pct_of_stage']}%"})

    res = {"ref": rid, "stage_px": [0, y0, W, y1], "stage_area_mm2": round(stage_area * MMX * MMY), "core": core, "density": dens,
           "landmarks": lm, "nn_gap_mm": {"median": round(float(np.median(gaps)), 1) if gaps else None, "values": gaps},
           "geo_rows": georows, "geo_fit": fit, "river_vthick_med_px": river_vthick_med, "zones": zones}
    json.dump(res, open(f"{WORK}/{rid}_zones.json", "w"), ensure_ascii=False, indent=1)

    # 확인용 구획 그림
    vis = img.copy()
    ov = vis.copy()
    ov[core_foot > 0] = (0.5 * ov[core_foot > 0] + 0.5 * np.array([0, 0, 255])).astype(np.uint8)
    ov[river_vis > 0] = (0.4 * ov[river_vis > 0] + 0.6 * np.array([255, 200, 0])).astype(np.uint8)
    if sea_m is not None:
        ov[sea_m > 0] = (0.6 * ov[sea_m > 0] + 0.4 * np.array([255, 120, 0])).astype(np.uint8)
    vis = cv2.addWeighted(ov, 0.75, vis, 0.25, 0)
    big = cv2.resize(vis, (2 * W, 2 * H), interpolation=cv2.INTER_CUBIC)
    pil = Image.fromarray(cv2.cvtColor(big, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(pil)
    f = ImageFont.truetype(FONT, 24)
    fs = ImageFont.truetype(FONT, 20)
    col = {"title": (255, 215, 0), "panel": (0, 230, 255), "footer": (255, 140, 0), "map": (0, 255, 120), "core_group": (255, 40, 40),
           "hero": (255, 0, 255), "landmark": (255, 255, 255), "other": (200, 200, 200), "river": (0, 170, 255), "sea": (0, 120, 255),
           "road": (190, 190, 120)}
    for z in zones:
        b = [v * 2 for v in z["px"]]
        c = col[z["kind"]]
        wdt = 6 if z["kind"] in ("core_group", "map") else (4 if z["kind"] in ("title", "panel", "hero", "river", "sea") else 2)
        d.rectangle(b, outline=c, width=wdt)
    for z in zones:
        b = [v * 2 for v in z["px"]]
        c = col[z["kind"]]
        txt = z["name"] if z["kind"] not in ("landmark", "other") else z["name"].split("(")[0]
        ff = f if z["kind"] in ("core_group", "map", "title", "panel", "hero", "river", "sea", "road") else fs
        tx, ty = b[0] + 6, b[1] + 4
        if z["kind"] == "map":
            tx, ty = b[0] + 8, b[1] + 8
        if z["kind"] == "core_group":
            tx, ty = b[0] + 8, b[3] - 34
        d.text((tx, ty), txt, font=ff, fill=c, stroke_width=3, stroke_fill=(0, 0, 0))
    # 범례
    lg = [("타이틀", "title"), ("패널", "panel"), ("푸터", "footer"), ("지도 무대", "map"), ("코어 군(빨강 칠=덩어리)", "core_group"),
          ("히어로", "hero"), ("랜드마크", "landmark"), ("강(하늘색 칠=보이는 물)", "river")] + ([("바다", "sea")] if sea_m is not None else [])
    x, y = 20, 2 * H - 40 - 34 * len(lg)
    d.rectangle([x - 10, y - 10, x + 420, y + 34 * len(lg) + 4], fill=(0, 0, 0))
    for i, (t, k) in enumerate(lg):
        d.rectangle([x, y + i * 34 + 6, x + 40, y + i * 34 + 26], outline=col[k], width=4)
        d.text((x + 52, y + i * 34), t, font=fs, fill=(255, 255, 255))
    pil.save(f"{OUT}/{rid}_zones.png")
    print(json.dumps({"core": core, "density": dens, "nn_gap_median_mm": res["nn_gap_mm"]["median"], "geo_fit": fit,
                      "river_bb": river_bb, "river_vthick_med_px": river_vthick_med}, ensure_ascii=False, indent=1))
    for r in lm:
        print(f"  {r['kind']:6s} {r['name'][:24]:24s} {r['w_mm']:6.1f}x{r['h_mm']:6.1f}mm  {r['area_mm2']:6d}mm2  무대 {r['pct_of_stage']:5.2f}%  gap {r.get('nn_gap_mm')}")
    for g in georows:
        print("  geo", g)


if __name__ == "__main__":
    main()
