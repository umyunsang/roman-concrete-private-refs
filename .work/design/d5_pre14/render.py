# -*- coding: utf-8 -*-
"""로마 편 배치 다이어그램(인쇄 지면) — 사양 spec.json을 읽어 A2 다이어그램 PNG(1mm = 3px, 1260×1782)와
그린 기록 drawn.json(사후 검사용)을 만든다. 담당: render

실행: python -I render.py <출력 PNG> <spec.json> [히어로 군 실루엣 npy]   (make.py가 부른다)
- 사용자 검토(2026-10-19 02:24): 다이어그램은 실제로 인쇄될 포스터 지면만 보인다.
  위치도(R)·연대기(T) 패널, 작업 이름, 티어 이름·티어 색·범례, 크기 꼬리표, 면적·검사 수치, 투영 상자 모서리,
  히어로 군 점선 윤곽, 가장자리 눈금, 설계 주석은 그리지 않는다. 그 정보는 spec.json과 보고서(drawn.json)에만 둔다.
- d4(기준선 7절, 사용자 선택 03:10): 무대 확장(STAGE_EXT)을 해제한다. 지도 무대는 (0,92)~(420,505) 하나이고,
  위 띠 오른쪽·하단 띠 오른쪽은 L·B와 같은 종이/띠 바탕이다(지형·밭 0). 그 자리에 Basic P2(아치·볼트·돔)·P5(지금 배우는 중)를 조판한다.
  랜드마크 L7 막센티우스 바실리카·L8 하드리아누스 영묘 + 폰스 아일리우스·L9 마르켈루스 극장과 네로 거상 받침을 그린다.
- 사양이 단일 원본이다: 라벨 슬롯·방향·본문, 지시선 꼭짓점, Detail 상자·글, 길 좌표, 포르투스·히어로 내부 형태는 사양 값을 그대로 쓴다.
  렌더는 그 값을 덮어쓰지 않고, 슬롯 안 줄바꿈·자리 조정과 모델의 실제 표면 접점 계산만 한다.
- 서체는 글자면(잉크 높이) 기준이다: 국문은 '한', 영문·라틴 문자열은 'H' 대문자 높이. em = 글자면 ÷ 글꼴 실측 비.
- 좌표: A2 mm(x 오른쪽, y 아래). 등각: 평면 +X → 화면 ↘, +Y → 화면 ↙, +Z → 위. 평면 원점 = 화면 (0, 0)(사양 규약 = v16 common.Iso)
- d5(기준선 8절 · 통합 루프 0-1절, 공통 결정 D1~D17): 히어로를 받침 없이 지도 땅 위에 다시 그린다(팔각 판·지층 옆면·앞 변 기초 절개 0).
  콜로세움 건물은 Blender roma_colo·roma_colo_in과 같은 칸 40·θ별 높이·둘째 고리·관람석·포디움·나무 바닥·하이포게움(결정 D2),
  둘레는 땅 바탕뿐이다(사용자 16:13·16:14: 광장·판석·인물·노점·공사장·길·둘레 나무 없음). 네로 거상 받침과 작은 마당만 곁에 둔다.
  장 6개(사용자 15:32·15:41): 장 배지 Ø10 + 영문 제목 7.0 + 국문 부제 2.8, 하단 장 3개(❹ B · ❺ D · ❻ P5)와 지도 안 ❸ 머리·❺ 근거 표지.
  INFO_ONLY=1이면 정보 층만 <d>/out/info/info_layer.png·drawn_info.json·info_check.json으로 쓰고, sil.json이 있으면 앵커에 맞춘다(결정 D11·D12).
- 그리는 순서: 바탕 지면(지면·강·바다·해안·바닥 글) → Core 건물 층 → 라벨 자리 잡기 → 지도 라벨·❸ 머리 → 타이틀·패널(❺ 안 확대 원 포함)
"""
import json
import math
import os
import re
import sys
import time

ROOT = "/Users/um-yunsang/roman-concrete-private-refs"
sys.dont_write_bytecode = True
sys.path.insert(0, ROOT + "/.work/lib")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prim import *  # noqa: F401,F403  (common.* 포함)
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont

# d5(결정 D17·작업 지시 5): 인쇄 내부선 하한 0.10mm. 지시선 0.30 · 콜아웃 테두리 0.25 · Z1 테두리 0.60은 그대로.
# 이 렌더러 안에서만 Layer 선 굵기를 0.10mm 이상으로 맞춘다(그보다 가는 보조선은 그리지 않는다 → drawn print_lines에 0건으로 적는다).
LW_MIN = 0.10
LW_LOG = {"n": 0}
_L_line, _L_poly, _L_ell, _L_arc, _L_pie = Layer.line, Layer.poly, Layer.ell, Layer.arc, Layer.pie


def _lwc(lw):
    if lw is not None and lw < LW_MIN - 1e-9:
        LW_LOG["n"] += 1
        return LW_MIN
    return lw


def _ln_(self, pts, fill, lw=0.25, joint=True, kind=None):
    return _L_line(self, pts, fill, _lwc(lw), joint, kind)


def _pl_(self, pts, fill=None, outline=None, lw=0.25):
    return _L_poly(self, pts, fill, outline, _lwc(lw) if outline is not None else lw)


def _el_(self, cx, cy, a, b, fill=None, outline=None, lw=0.25):
    return _L_ell(self, cx, cy, a, b, fill, outline, _lwc(lw) if outline is not None else lw)


def _ar_(self, cx, cy, a, b, a0, a1, fill, lw=0.25):
    return _L_arc(self, cx, cy, a, b, a0, a1, fill, _lwc(lw))


def _pi_(self, cx, cy, a, b, a0, a1, fill=None, outline=None, lw=0.25):
    return _L_pie(self, cx, cy, a, b, a0, a1, fill, outline, _lwc(lw) if outline is not None else lw)


Layer.line, Layer.poly, Layer.ell, Layer.arc, Layer.pie = _ln_, _pl_, _el_, _ar_, _pi_
try:
    import numpy as np
    import cv2
except Exception:          # 측정 도구가 없으면 drawn.json의 실측 칸은 None으로 남긴다
    np = None
    cv2 = None

T_START = time.time()
SPEC_PATH = sys.argv[2] if len(sys.argv) > 2 else ROOT + "/.work/design/d2/out/spec.json"
SIL_PATH = sys.argv[3] if len(sys.argv) > 3 else ROOT + "/.work/design/d2/v2_hero_cluster_sil.npy"
OUT = sys.argv[1] if len(sys.argv) > 1 else ROOT + "/.work/design/d2/out/diagram.png"
DRAWN_PATH = os.path.join(os.path.dirname(os.path.abspath(OUT)), "drawn.json")
OUT_PX_PER_MM = 3

with open(SPEC_PATH, encoding="utf-8") as fh:
    S = json.load(fh)


# ───────────────────────── d4 결정값(공통 결정 2026-10-19) ─────────────────────────
# 원칙: 통합 사양(d4)에 열쇠가 있으면 사양 값을 그대로 쓴다. 아래 결정값은
#   (1) 사양에 그 열쇠가 없을 때(새 키), (2) 워커 단독 확인용 d3 사양(frame.panels에 P2·P5 없음)을 받았을 때
#       값이 d3 그대로인 칸만 d4 결정값으로 바꿔 d4 사양을 흉내 낼 때만 쓴다. 바꾼 칸은 drawn.json notes에 남긴다.
def _same(a, b, tol=0.06):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) <= tol
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and len(a) == len(b):
        return all(_same(x, y, tol) for x, y in zip(a, b))
    return a == b






# 랜드마크 평면·슬롯 윗선의 기본값(사양에 열쇠가 없을 때만 쓴다)
D4_LANDMARKS = [
    {"id": "L7", "name": "막센티우스 바실리카", "latin": "Basilica of Maxentius(Basilica Nova)", "tier": "Core(표준 랜드마크)",
     "projected_box": [178.0, 152.0, 255.0, 212.5], "projected_area_mm2": 4663, "geo_approx": [41.8917, 12.4886],
     "plan": {"base_rects": [[276.0, 43.5, 338.0, 62.0], [292.5, 43.5, 338.0, 87.0]], "base_h": 1.5, "aisle": [292.5, 43.5, 338.0, 55.5],
              "aisle_h": 16.0, "bays": 3, "nave": [292.5, 55.5, 338.0, 87.0], "ruin_h": 4.0, "vault_h": 10.0}},
    {"id": "L8", "name": "하드리아누스 영묘 + 폰스 아일리우스", "latin": "Mausoleum Hadriani · Pons Aelius", "tier": "Core(표준 랜드마크)",
     "projected_box": [83.6, 378.5, 162.6, 439.8], "projected_area_mm2": 4843, "geo_approx": [41.9031, 12.4663],
     "plan": {"base": [465.6, 326.9, 513.6, 374.9], "base_h": 5.0, "drum_c": [489.6, 350.9], "drum_r": 11.5, "drum_z": [5.0, 18.0],
              "top_z": [18.0, 23.8], "bridge": [484.6, 367.9, 494.6, 396.9], "bridge_h": 3.0, "bridge_arches": 3}},
    {"id": "L9", "name": "마르켈루스 극장", "latin": "Theatrum Marcelli", "tier": "Core(표준 랜드마크)",
     "projected_box": [32.3, 271.4, 111.7, 329.3], "projected_area_mm2": 4598, "geo_approx": [41.8919, 12.4797],
     "plan": {"center": [340.0, 264.76], "r": 38.0, "h": 12.0, "tier_h": 6.0, "stage_wall_h": 4.0}},
]
D4_COLOSSUS = {"name": "네로 거상 받침(벽돌 마감 콘크리트 받침 + 청동 거상, 거상은 복원 추정)", "box": [178.1, 200.8, 191.9, 226.0],
               "zone": "콜로세움 뒤-왼쪽과 바실리카 사이(베누스·로마 신전 쪽)", "on": "땅", "plan": [328.8, 115.2],
               "base_mm": 8.0, "base_h": 5.0, "statue_mm": 2.4, "statue_h": 15.0}
D4_SLOTS = {
    "막센티우스 바실리카": {"name": "막센티우스 바실리카(Basilica of Maxentius)", "kind": "브래킷", "wall": "↗(+30°)", "box": [121.5, 175.5, 175.5, 218.5],
                    "en": ["BASILICA OF MAXENTIUS"], "ko": "막센티우스 바실리카", "sup": "Basilica Nova", "body": ["측랑은 코퍼 배럴 볼트, 신랑은 교차 볼트", "북쪽 측랑 3칸이 지금도 서 있다"],
                    "target": "측랑 왼쪽 칸 열린 면", "target_pt": [212.0, 170.0], "top_line": [276.85, -0.57735], "x_range": [121.5, 175.5],
                    "lead": "규선 연장 + ↘30°(꺾임 ≤ 1)"},
    "네로 거상": {"name": "네로 거상(소품 주석)", "kind": "소품 주석", "wall": "↗(+30°)", "box": [138.0, 190.5, 172.0, 218.0],
              "lines": ["네로 거상", "높이 약 30 m 청동상,", "콘크리트 받침"], "target": "거상 머리", "target_pt": [185.0, 201.0],
              "top_line": [289.85, -0.57735], "x_range": [138.0, 172.0], "lead": "블록 오른쪽 끝 ↘30°"},
    "마르켈루스 극장": {"name": "마르켈루스 극장(Theatrum Marcelli)", "kind": "브래킷", "wall": "↘(−30°)", "box": [3.0, 259.9, 30.0, 311.5],
                  "en": ["THEATRE OF", "MARCELLUS"], "ko": "마르켈루스 극장", "sup": None, "body": ["테베레 홍수에 잠긴", "기초에서 결정이 자라", "보강(2011년 연구)"],
                  "target": "관람석·아케이드 윗면", "target_pt": [52.0, 315.0], "top_line": [258.2, 0.57735], "x_range": [3.0, 30.0],
                  "lead": "규선 오른쪽 끝 ↘ 연장 + 수직"},
    "하드리아누스 영묘": {"name": "하드리아누스 영묘(Mausoleum Hadriani)", "kind": "브래킷", "wall": "↗(+30°)", "box": [176.0, 427.3, 208.0, 478.7],
                   "en": ["MAUSOLEUM OF", "HADRIAN"], "ko": "하드리아누스 영묘", "sup": None, "body": ["겉은 대리석,", "속은 콘크리트 원통", "폰스 아일리우스 다리"],
                   "target": "기단 윗면", "target_pt": [140.5, 421.0], "top_line": [547.35, -0.57735], "x_range": [176.0, 208.0],
                   "lead": "블록 왼쪽 끝 ↖30° → 기단 윗면"},
}
D4_TOPLINE = {k: (v["top_line"], v["x_range"], v["box"]) for k, v in D4_SLOTS.items()}


def _find_pair_marks(o, depth=0):
    """사양 어디에 있든 숫자 짝 표지 목록(pair_marks·PAIR_MARKS 등)을 찾는다"""
    if depth > 6:
        return None
    if isinstance(o, dict):
        for k, v in o.items():
            if re.search(r"pair_?marks?", str(k), re.I) and isinstance(v, list) and v:
                return v
        for v in o.values():
            r = _find_pair_marks(v, depth + 1)
            if r:
                return r
    elif isinstance(o, list):
        for v in o:
            r = _find_pair_marks(v, depth + 1)
            if r:
                return r
    return None


# ───────────────────────── d5 결정값(공통 결정 D3·D5·D7·D15·D16, 2026-10-19 통합 루프) ─────────────────────────
# 원칙(d4와 같다): 통합 사양(d5)에 새 값이 있으면 사양 값을 그대로 쓴다. 아래 결정값은 워커 단독 확인용으로 d4 사양을 받았을 때
# 값이 d4 그대로인 칸만 d5 결정값으로 바꿔 d5 사양을 흉내 낼 때만 쓴다. 바꾼 칸은 drawn.json notes에 남긴다.




META, HI, FR, CM = S["meta"], S["hierarchy"], S["frame"], S["core_map"]
HERO, RV, SC, PG = CM["hero"], CM["river"], CM["sea_coast"], CM["portus_geometry"]
LBS = CM["labels"]
BAS, DET, SUP, MEAS = S["basic"], S["detail"], S["support"], S["measurements"]
STAGE = tuple(FR["stage"]["rect"])
STAGE_EXT = []                                       # d4: 무대 확장 해제(R·T 자리 = 종이/띠 바탕, 지형 0). 사양 ext_rects는 읽지 않는다
STAGE_RECTS = [STAGE]
STAGE_AREA = (STAGE[2] - STAGE[0]) * (STAGE[3] - STAGE[1])      # 173,460mm²
REMOVED_PANELS = ("R", "T")                          # 사용자 검토: 위치도·연대기는 인쇄 지면에서 0개
PANEL = {p["id"]: p for p in FR["panels"] if p["id"] not in REMOVED_PANELS}
LM = {l["id"]: l for l in CM["landmarks"]}
PROPS = {p["name"].split("(")[0].strip(): p for p in CM["props"]}
DMAP = {d["id"]: d for d in DET["map_elements"]}
SLOT = {s["name"].split("(")[0].strip(): s for s in LBS["slots"]}
for _ck, _kw in (("막센티우스 바실리카", "바실리카"), ("하드리아누스 영묘", "영묘"), ("마르켈루스 극장", "극장"), ("네로 거상", "거상")):
    if _ck not in SLOT:                              # 사양 슬롯 이름이 조금 달라도 같은 라벨로 받는다
        for _k in list(SLOT):
            if _kw in _k:
                SLOT[_ck] = SLOT[_k]
                break
for _s in LBS["slots"]:                              # 통합 d4: panels 슬롯 열쇠(top_edge·flag·tag_text) → 렌더 열쇠(top_line·x_range·pole_x·lines)
    _te = _s.get("top_edge")
    if isinstance(_te, dict) and _s.get("top_line") is None and _te.get("x"):
        _a = _te.get("d", _te.get("c"))
        if _a is not None:
            _s["top_line"] = [float(_a), (-0.57735 if str(_s.get("wall", "↘")).startswith("↗") else 0.57735)]
            _s["x_range"] = [float(_te["x"][0]), float(_te["x"][1])]
    _fl = _s.get("flag")
    if isinstance(_fl, dict) and _s.get("pole_x") is None and _fl.get("x") is not None:
        _s["pole_x"] = float(_fl["x"])
    if "주석" in str(_s.get("kind", "")) and not _s.get("lines") and _s.get("tag_text"):
        _tt = _s["tag_text"]
        _s["lines"] = list(_tt) if isinstance(_tt, (list, tuple)) else [str(_tt)]
FLOOR = {f["name"].split(" ")[0]: f for f in LBS["floor_text"]}
TERR = {t["name"].split("(")[0].split(" ")[0]: t for t in CM.get("terrain", [])}
COLOSSUS = next((p for p in CM["props"] if p["name"].startswith("네로")), None)
REPORT = {"objects": {}, "labels": {}, "notes": []}
GEO = {}
LABEL_POLYS = []     # (이름, 화면 다각형) — 겹침 검사용
INFO_POLYS = []      # (이름, 화면 다각형) — 콜아웃·패널·확대 창(라벨과 겹치면 안 됨)
DRAWN = {"texts": [], "labels": [], "leaders": [], "footprints": [], "roads": [], "boxes": [], "s_bars": [], "crowds": [],
         "portus": {}, "density": {}, "objects": [], "road_gaps": {}, "notes": []}


def sget(d, *keys, default=None):
    """사양 새 필드 읽기: 여러 열쇠 이름 중 처음 있는 값(map·panels가 정한 이름을 모두 받는다)"""
    if not isinstance(d, dict):
        return default
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default

RIV_Y = float(re.search(r"Y\s*=\s*([\d.]+)", RV["plan"]["arm1"]).group(1))          # 314
RIV_XB = float(re.search(r"X\s*=\s*([\d.]+)", RV["plan"]["arm2"]).group(1))         # 533.4
RIV_HW1 = RV["width_screen_perp_mm"]["↘ 팔"] / (2.0 * C30)                          # 평면 반폭 9.24
RIV_HW2 = RV["width_screen_perp_mm"]["↙ 팔(하구 쪽)"] / (2.0 * C30)                   # 11.55
COAST_B = float(re.search(r"\+\s*([\d.]+)", SC["coastline"]["equation"]).group(1))   # 380
COAST_DEEP = float(re.search(r"지층 단면\s*([\d.]+)mm", SC["coast_section"]).group(1))  # 10
QUAY_DEEP = float(re.search(r"부두 구간은\s*([\d.]+)mm", SC["coast_section"]).group(1))  # 3

# ───────────────────────── 팔레트 ─────────────────────────
GROUND = (236, 216, 172)
GRID_OP = (228, 206, 162)
SEA_C = (146, 182, 208)
HARBOR_C = (162, 198, 220)
RIV_C = (116, 172, 212)
ROAD_C = (212, 194, 156)
ROAD_EDGE = (150, 128, 94)
APPIA_C = (190, 168, 128)
INK_L = (58, 42, 28)            # 정보 잉크 한 색: 지도 라벨·지시선·끝점·짝 표지·콜아웃 테두리·제목
INK_WATER = (52, 92, 124)       # 물 이름 바닥 글(TIBERIS·MARE TYRRHENUM): 물보다 짙은 파랑(d4, 물 위 명도 대비는 drawn.json floor_contrast)
VINE_C = (118, 144, 78)
WHEAT_C = (226, 200, 122)
PASTURE_C = (198, 202, 142)
OLIVE_C = (118, 146, 92)
WOOD = (150, 108, 68)
WOOD_L = (184, 142, 96)
LIME_W = (246, 244, 236)
ASH_R = (150, 82, 60)
ASH_G = (172, 162, 134)
AGG_G = (156, 150, 140)
MORTAR = (206, 194, 178)
CONC2 = (166, 160, 148)
PUMICE = (216, 208, 186)
ROOF = (196, 92, 64)
WALL_W = (232, 214, 184)
CLOTHS = [(150, 70, 52), (96, 110, 140), (172, 140, 82), (118, 92, 128), (92, 122, 90), (184, 156, 112)]
STRATA7 = [(1.2, (94, 126, 66)), (1.8, (128, 98, 62)), (2.0, (150, 118, 80)), (2.0, (112, 86, 56))]
ACCENT = (200, 34, 54)          # 폼페이 레드(#c82236): 타이틀·패널 머리글·제작 과정 단계 번호에만
BROWN_A = (110, 86, 60)         # 패널 안 화살표·시간 화살표
NOTE_C = (110, 80, 54)          # 주의(※) 글
H_PERSON = 2.4                     # 결정 D8: 표준 랜드마크·길·하역장·항구 사람 키(화면 mm). 히어로 군은 H_PERSON_HERO 4.9
LEAD_W = 0.30                   # 지시선 굵기(mm)
DOT_RR = 0.45                   # 지시선 끝점 반지름(지름 0.9mm)
BOX_CLEAR = 3.0                 # 테두리 상자 안 글 ↔ 테두리 최소 간격(mm)

# 티어 색은 인쇄 지면에서 0회다. 아래 값이 그리기 호출에 들어오면 센다(drawn.json tier_color_uses).
_TIER_RGB = {(47, 107, 58), (63, 58, 160), (208, 101, 14), (47, 127, 134), (29, 80, 40), (52, 46, 138), (150, 66, 0), (24, 92, 98)}
TIER_USES = [0]


def _tier_hit(*cols):
    for c in cols:
        if isinstance(c, tuple) and len(c) >= 3 and tuple(int(v) for v in c[:3]) in _TIER_RGB:
            TIER_USES[0] += 1


def _guard(name):
    orig = getattr(Layer, name)

    def f(self, *a, **k):
        _tier_hit(*[v for v in list(a) + list(k.values()) if isinstance(v, tuple)])
        return orig(self, *a, **k)
    setattr(Layer, name, f)


for _n in ("poly", "line", "ell", "rect", "dot", "text", "text_c", "text_r", "pie", "arc", "dashed"):
    _guard(_n)

# ───────────────────────── 글자면(잉크 높이) 기준 글꼴 ─────────────────────────
_KO_I = {"r": 0, "m": 2, "s": 4, "b": 6}
_HANGUL = re.compile(r"[가-힣]")
_RATIO = {}


def face_ratio(kind, s):
    """글꼴 실측 비 = 잉크 높이 ÷ em. 국문이 든 문자열은 '한', 그 밖(영문·라틴·숫자)은 'H'로 잰다(1000px, 알파 ≥ 128)."""
    sample = "한" if (kind != "en" and _HANGUL.search(s or "")) else "H"
    key = (kind, sample)
    if key not in _RATIO:
        f = ImageFont.truetype(EN_PATH, 1000) if kind == "en" else ImageFont.truetype(KO_PATH, 1000, index=_KO_I[kind])
        im = Image.new("L", (3000, 2200), 0)
        ImageDraw.Draw(im).text((500, 1600), sample, font=f, fill=255, anchor="ls")
        b = im.point(lambda v: 255 if v >= 128 else 0).getbbox()
        _RATIO[key] = (b[3] - b[1]) / 1000.0
    return _RATIO[key]


def fface(kind, face, s="한"):
    """글자면(mm) → (글꼴, em mm, 실제 글자면 mm). 그리기 해상도(KD px/mm)에서 가장 가까운 px를 고른다."""
    r = face_ratio(kind, s)
    px0 = face / r * KD
    cands = sorted({max(6, int(math.floor(px0))), max(6, int(math.ceil(px0)))})
    px = min(cands, key=lambda p: abs(p / KD * r - face))
    em = px / KD
    return fnt(kind, em), em, em * r


def rec_text(s, role, kind, em, face, poly, layer="", pitch=None, panel=None):
    """인쇄 글줄 기록(사후 검사: 금지 패턴·글자면·피치·테두리 간격)"""
    t = {"text": s, "role": role, "layer": layer, "font": kind, "em": round(em, 3), "face": round(face, 3),
         "poly": [[round(x, 2), round(y, 2)] for x, y in poly]}
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    t["bbox"] = [round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2)]
    if pitch:
        t["pitch"] = pitch
    if panel:
        t["panel"] = panel
    DRAWN["texts"].append(t)


def ptext(x, y, s, kind, face, col, role, anchor="l", layer="", pitch=None, panel=None, L=None):
    """정면(화면 평행) 글줄: 기준선 (x, y). anchor l/c/r. (외곽 상자, 실제 글자면)을 돌려준다."""
    L = L or P
    f, em, fa = fface(kind, face, s)
    a = {"l": "ls", "c": "ms", "r": "rs"}[anchor]
    L.text(x, y, s, f, col, anchor=a)
    bb = f.getbbox(s, anchor=a)
    box = (x + bb[0] / KD, y + bb[1] / KD, x + bb[2] / KD, y + bb[3] / KD)
    rec_text(s, role, kind, em, fa, box_poly(box), layer, pitch, panel)
    return box, fa


def twf(s, kind, face):
    return tw(s, fface(kind, face, s)[0])


def wrap(s, kind, face, maxw):
    """공백 기준 줄바꿈. 한 낱말이 한 줄보다 길면 가운뎃점(·) 뒤에서도 끊는다(국문 조판 관례)"""
    toks = []
    for i, w in enumerate(s.split(" ")):
        parts = re.split(r"(?<=·)", w)
        for j, p_ in enumerate(parts):
            if p_:
                toks.append((p_, j == 0))
    lines, cur = [], ""
    for p_, sp_before in toks:
        t = p_ if not cur else cur + (" " if sp_before else "") + p_
        if not cur or twf(t, kind, face) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = p_
    if cur:
        lines.append(cur)
    return lines


def wrap_all(texts, kind, face, maxw):
    out = []
    for s in texts:
        out += wrap(s, kind, face, maxw)
    return out


# ───────────────────────── 공통 도우미 ─────────────────────────
def lerp(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def sp(X, Y, Z=0.0):
    """사양 평면 좌표 → 화면 mm(평면 원점 = 화면 원점)"""
    return (C30 * (X - Y), 0.5 * (X + Y) - Z)


def to_plan(x, y):
    a = x / C30
    return ((a + 2.0 * y) / 2.0, (2.0 * y - a) / 2.0)


def bbox_of(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def mesh_pts(*meshes):
    out = []
    for m in meshes:
        for f in m.faces:
            out.extend(f[0])
    return out


def _seg_x(p1, p2, q1, q2):
    def o(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    d1, d2, d3, d4 = o(q1, q2, p1), o(q1, q2, p2), o(p1, p2, q1), o(p1, p2, q2)
    return ((d1 > 1e-9 and d2 < -1e-9) or (d1 < -1e-9 and d2 > 1e-9)) and ((d3 > 1e-9 and d4 < -1e-9) or (d3 < -1e-9 and d4 > 1e-9))


def _pt_seg(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


def _edges(pg, closed=True):
    n = len(pg)
    return [(pg[i], pg[(i + 1) % n]) for i in range(n if closed else n - 1)]


def _poly_dist(A, B, a_closed=True, b_closed=True):
    """두 다각형(또는 꺾은선) 최소 거리. 겹치거나 교차하면 0"""
    ea, eb = _edges(A, a_closed), _edges(B, b_closed)
    for p1, p2 in ea:
        for q1, q2 in eb:
            if _seg_x(p1, p2, q1, q2):
                return 0.0
    if b_closed and len(B) >= 3 and any(in_poly(p, B) for p in A):
        return 0.0
    if a_closed and len(A) >= 3 and any(in_poly(p, A) for p in B):
        return 0.0
    d = min(_pt_seg(p, q1, q2) for p in A for q1, q2 in eb) if eb else 1e9
    d2 = min(_pt_seg(q, p1, p2) for q in B for p1, p2 in ea) if ea else 1e9
    return min(d, d2)


def _pt_poly_gap(p, poly):
    """점 → 다각형 간격(안이면 0)"""
    if len(poly) >= 3 and in_poly(p, poly):
        return 0.0
    return min(_pt_seg(p, a, b) for a, b in _edges(poly))


class SIso(Iso):
    """랜드마크 하나를 위계 크기에 맞춰 중심 piv 기준 s배로 그리는 등각 틀(높이 포함)."""

    def __init__(self, base, piv, s):
        Iso.__init__(self, base.L, base.ox, base.oy)
        self.piv, self.s = piv, s

    def p(self, X, Y, Z=0.0):
        x, y = Iso.p(self, X, Y, Z)
        return (self.piv[0] + self.s * (x - self.piv[0]), self.piv[1] + self.s * (y - self.piv[1]))


def _siso(lid):
    lm = LM.get(lid) or {}
    s_ = float(lm.get("draw_scale", 1.0) or 1.0)
    piv = lm.get("draw_pivot")
    if abs(s_ - 1.0) < 1e-6 or not piv:
        return ISO
    return SIso(ISO, tuple(piv), s_)


class ZIso(Iso):
    """평면 sc배 + 높이 zs배(높이 과장) 등각 틀. 아이콘을 사양 투영 상자에 맞출 때 쓴다."""

    def __init__(self, L, ox, oy, sc=1.0, zs=1.0):
        Iso.__init__(self, L, ox, oy)
        self.sc, self.zs = sc, zs

    def p(self, X, Y, Z=0.0):
        s = self.sc
        return (self.ox + C30 * (X - Y) * s, self.oy + 0.5 * (X + Y) * s - Z * s * self.zs)


def fit_frame(pts3, box, ax="c", ay="c", zs_max=1.0, sc_max=1.3, sc_min=0.5):
    """국소 평면 점들의 투영 외곽을 box에 맞춘다: 폭·높이로 sc를 정하고, 높이가 모자라면 zs(≤ zs_max)로 채운다."""
    def ext(sc, zs):
        xs, ys = [], []
        for p in pts3:
            Z = p[2] if len(p) > 2 else 0.0
            xs.append(C30 * (p[0] - p[1]) * sc)
            ys.append(0.5 * (p[0] + p[1]) * sc - Z * sc * zs)
        return min(xs), min(ys), max(xs), max(ys)
    bw, bh = box[2] - box[0], box[3] - box[1]
    x0, y0, x1, y1 = ext(1.0, 1.0)
    sc = max(sc_min, min(bw / (x1 - x0), bh / (y1 - y0), sc_max))
    zs = 1.0
    if zs_max > 1.0:
        x0, y0, x1, y1 = ext(sc, zs_max)
        if (y1 - y0) <= bh:
            zs = zs_max
        else:
            lo, hi = 1.0, zs_max
            for _ in range(32):
                mid = (lo + hi) / 2.0
                x0, y0, x1, y1 = ext(sc, mid)
                if (y1 - y0) > bh:
                    hi = mid
                else:
                    lo = mid
            zs = lo
    x0, y0, x1, y1 = ext(sc, zs)
    ox = {"c": (box[0] + box[2]) / 2.0 - (x0 + x1) / 2.0, "l": box[0] - x0, "r": box[2] - x1}[ax]
    oy = {"c": (box[1] + box[3]) / 2.0 - (y0 + y1) / 2.0, "t": box[1] - y0, "b": box[3] - y1}[ay]
    return ox, oy, sc, zs, (ox + x0, oy + y0, ox + x1, oy + y1)


def record(key, name, tier, spec_box, drawn_box, note=None):
    sb = [round(v, 1) for v in spec_box]
    db = [round(v, 2) for v in drawn_box]
    dev = max(abs(a - b) for a, b in zip(sb, db))
    rec = {"이름": name, "티어": tier, "사양 상자": sb, "그린 외곽": db, "최대 편차mm": round(dev, 1),
           "그린 면적mm²": int(round((db[2] - db[0]) * (db[3] - db[1])))}
    if note:
        rec["메모"] = note
    REPORT["objects"][key] = rec


def soft(L, pts, col, alpha=60, blur=1.0):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    pad = blur * 3.0 + 1.0
    Sb = Layer(min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
    Sb.poly(pts, fill=tuple(col[:3]) + (alpha,))
    img = Sb.img.filter(ImageFilter.GaussianBlur(blur * KD)) if blur > 0 else Sb.img
    safe_composite(L.img, img, (Sb.x0 - L.x0) * KD, (Sb.y0 - L.y0) * KD)


def soft_line(L, pts, col, alpha=70, w=0.9, blur=0.45):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    pad = blur * 3.0 + w + 1.0
    Sb = Layer(min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
    Sb.line(pts, tuple(col[:3]) + (alpha,), w, joint=True)
    img = Sb.img.filter(ImageFilter.GaussianBlur(blur * KD)) if blur > 0 else Sb.img
    safe_composite(L.img, img, (Sb.x0 - L.x0) * KD, (Sb.y0 - L.y0) * KD)


def soft_ell(L, cx, cy, a, b, col, alpha=40, blur=0.8):
    pts = [(cx + a * math.cos(t * math.pi / 12), cy + b * math.sin(t * math.pi / 12)) for t in range(24)]
    soft(L, pts, col, alpha, blur)


def rrect(L, x0, y0, x1, y1, r, fill=None, outline=None, lw=0.25):
    pad = 3
    W = int(math.ceil((x1 - x0) * KD)) + 2 * pad
    H = int(math.ceil((y1 - y0) * KD)) + 2 * pad
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    d.rounded_rectangle([pad, pad, pad + (x1 - x0) * KD, pad + (y1 - y0) * KD], radius=r * KD, fill=fill,
                        outline=outline, width=max(1, int(round(lw * KD))) if outline else 0)
    safe_composite(L.img, tmp, L.X(x0) - pad, L.Y(y0) - pad)


def strata_side(L, a, b, layers, f=0.83):
    """화면 변 a→b 아래로 지층 옆면(층마다 수직 두께)"""
    d0 = 0.0
    for t, col in layers:
        L.poly([(a[0], a[1] + d0), (b[0], b[1] + d0), (b[0], b[1] + d0 + t), (a[0], a[1] + d0 + t)], fill=tint(col, f))
        d0 += t
    L.line([a, b, (b[0], b[1] + d0), (a[0], a[1] + d0), a], (70, 50, 32), 0.2)


def plan_band(p0, p1, w, ext0=0.0, ext1=0.0):
    """평면 선분 p0→p1을 화면 수직 폭 w의 띠로(사양 v2_check와 같다: 평면 반폭 = w / (2·cos30)).
    ext0·ext1은 다른 길과 끝점을 공유하는 모서리 이음(반폭만큼)에만 쓴다."""
    hw = w / (2.0 * C30)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    Ls = math.hypot(dx, dy)
    ux, uy = dx / Ls, dy / Ls
    a = (p0[0] - ux * ext0, p0[1] - uy * ext0)
    b = (p1[0] + ux * ext1, p1[1] + uy * ext1)
    nx, ny = -uy * hw, ux * hw
    return [sp(a[0] + nx, a[1] + ny), sp(b[0] + nx, b[1] + ny), sp(b[0] - nx, b[1] - ny), sp(a[0] - nx, a[1] - ny)]




def poly_y_at(poly, x, which="top"):
    ys = []
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if x1 == x2:
            continue
        if (x1 - x) * (x2 - x) <= 0:
            t = (x - x1) / (x2 - x1)
            ys.append(y1 + (y2 - y1) * t)
    if not ys:
        return None
    return min(ys) if which == "top" else max(ys)


def coast_y(x):
    return T30 * x + COAST_B


def m_pine(X, Y, z0, h, r, key="소나무"):
    """우산소나무(오스티아·아피아 가도의 지중해 소나무): 곧은 줄기 + 납작한 수관"""
    m = Mesh(None)
    m.extend(m_cyl(X, Y, r * 0.09, z0, z0 + h * 0.8, (112, 84, 58), n=5, k=0.85))
    m.extend(m_blob(X, Y, z0 + h * 0.86, r, (86, 116, 70), n=8, key=key, jit=0.14, squash=0.36))
    m.extend(m_blob(X + r * 0.3, Y - r * 0.25, z0 + h * 0.95, r * 0.55, (104, 134, 82), n=6, key=key + "b", jit=0.1, squash=0.4))
    return m


def m_bather(X, Y, z0, h, cloth, key="목욕"):
    """물에 잠긴 목욕객(몸통 위쪽 + 머리)"""
    w = h * 0.13
    m = Mesh(None)
    m.extend(m_frustum(ring(X, Y, w * 1.35, 6, 0.3), z0, z0 + h * 0.36, 0.72, cloth))
    m.extend(m_blob(X, Y, z0 + h * 0.46, h * 0.11, (226, 184, 150), n=6, key=key, jit=0.05))
    return m


def m_stall(X, Y, awn, key="노점"):
    m = Mesh(None)
    m.extend(m_box(X - 2.2, Y - 1.4, 0, X + 2.2, Y + 1.4, 2.0, WOOD, top=WOOD_L))
    for (dx, dy) in ((-2.0, -1.2), (2.0, -1.2), (-2.0, 1.2), (2.0, 1.2)):
        m.extend(m_box(X + dx - 0.15, Y + dy - 0.15, 2.0, X + dx + 0.15, Y + dy + 0.15, 4.4, WOOD))
    m.extend(m_frustum([(X - 2.7, Y - 1.9), (X + 2.7, Y - 1.9), (X + 2.7, Y + 1.9), (X - 2.7, Y + 1.9)], 4.4, 5.5, 0.22, awn))
    m.extend(m_cyl(X - 1.0, Y + 0.2, 0.45, 2.0, 2.9, (182, 104, 70), n=6, k=0.6))
    m.extend(m_cyl(X + 0.8, Y - 0.3, 0.45, 2.0, 2.9, (196, 120, 80), n=6, k=0.6))
    return m


def m_amphorae(X, Y, n=4, key="암포라"):
    m = Mesh(None)
    for i in range(n):
        dx = (h01(key, i, "x") - 0.5) * 3.2
        dy = (h01(key, i, "y") - 0.5) * 3.2
        m.extend(m_cyl(X + dx, Y + dy, 0.55, 0, 2.0, (182, 104, 70), n=7, k=0.55))
    return m


def m_cart(X, Y, axis="Y", load=LIME_W, key="수레", ox_=True):
    """짐수레(+소, 몰이꾼). axis = 진행 축(Y: 화면 ↙↗ 방향, X: ↘↖ 방향), 앞쪽 = 음(−) 방향"""
    m = Mesh(None)
    if axis == "Y":
        m.extend(m_box(X - 2.4, Y - 4.0, 1.6, X + 2.4, Y + 4.0, 3.6, WOOD, top=WOOD_L))
        m.extend(m_mound(X, Y + 0.5, 3.6, 2.6, 2.0, load, key=key + "짐"))
        if ox_:
            m.extend(m_box(X - 1.1, Y - 10.2, 1.5, X + 1.1, Y - 5.0, 3.6, (146, 112, 82)))
            m.extend(m_box(X - 0.7, Y - 11.6, 2.4, X + 0.7, Y - 10.2, 3.9, (128, 98, 72)))
            for (dx, dy) in ((-0.8, -9.6), (0.8, -9.6), (-0.8, -5.6), (0.8, -5.6)):
                m.extend(m_box(X + dx - 0.25, Y + dy - 0.25, 0, X + dx + 0.25, Y + dy + 0.25, 1.6, (110, 84, 60)))
        m.extend(m_person(X + 3.4, Y - 6.0, 0, H_PERSON, CLOTHS[0], key=key + "꾼"))
    else:
        m.extend(m_box(X - 4.0, Y - 2.4, 1.6, X + 4.0, Y + 2.4, 3.6, WOOD, top=WOOD_L))
        m.extend(m_mound(X + 0.5, Y, 3.6, 2.6, 2.0, load, key=key + "짐"))
        if ox_:
            m.extend(m_box(X - 10.2, Y - 1.1, 1.5, X - 5.0, Y + 1.1, 3.6, (146, 112, 82)))
            m.extend(m_box(X - 11.6, Y - 0.7, 2.4, X - 10.2, Y + 0.7, 3.9, (128, 98, 72)))
            for (dx, dy) in ((-9.6, -0.8), (-9.6, 0.8), (-5.6, -0.8), (-5.6, 0.8)):
                m.extend(m_box(X + dx - 0.25, Y + dy - 0.25, 0, X + dx + 0.25, Y + dy + 0.25, 1.6, (110, 84, 60)))
        m.extend(m_person(X - 6.0, Y + 3.4, 0, H_PERSON, CLOTHS[0], key=key + "꾼"))
    return m


MAP_MODE = [False]          # True인 동안(지도 그리기) 사람·나무·노점·수레·암포라·덤불은 만들지 않는다(사용자 16:14). 패널 장면(❹)은 False


def _map_gate(fn):
    def w(*a, **k):
        return Mesh(None) if MAP_MODE[0] else fn(*a, **k)
    w.__name__ = getattr(fn, "__name__", "gated")
    return w


m_pine, m_bather, m_stall, m_amphorae, m_cart = (_map_gate(f_) for f_ in (m_pine, m_bather, m_stall, m_amphorae, m_cart))
m_cypress, m_olive = (_map_gate(f_) for f_ in (m_cypress, m_olive))
_m_person_orig = m_person


def m_person(*a, **k):
    """사용자 16:14·16:35: 지도에는 사람이 없다(인물 무리·일꾼·목욕객). 조각상(키 '조각상…')과 패널 장면의 사람은 둔다"""
    if MAP_MODE[0] and not str(k.get("key", "")).startswith("조각상"):
        return Mesh(None)
    return _m_person_orig(*a, **k)


def wheels(iso, X, Y, axis="Y"):
    pos = [(X + 2.6, Y), (X - 2.6, Y)] if axis == "Y" else [(X, Y + 2.6), (X, Y - 2.6)]
    for (a, b) in pos:
        cx, cy = iso.p(a, b, 1.5)
        P.ell(cx, cy, 1.5, 1.5, fill=(90, 66, 44), outline=(60, 44, 30), lw=0.15)


# 그리기 층: BASE(인쇄 지면 바탕: 지면·강·바다·길·바닥 글 + 마지막 Detail·라벨·타이틀·패널),
# OBJ(랜드마크·소품), TER(밭·먼 밭·베수비오·농장·구릉·지붕·나무). 합성 순서 BASE ← TER ← OBJ.
# 밀도(결정 14)는 TER ∪ OBJ 알파 ≥ 128로 잰다.
BASE = Layer(0, 0, PW, PH, "인쇄지면", bg=BG + (255,))
OBJ = Layer(0, 0, PW, PH, "랜드마크층")
TER = Layer(0, 0, PW, PH, "지형층")
P = BASE
ISO = Iso(P, 0.0, 0.0)


def use_layer(L):
    global P
    P = L
    ISO.L = L


def in_stage(x, y, tol=0.0):
    return any(r[0] - tol <= x <= r[2] + tol and r[1] - tol <= y <= r[3] + tol for r in STAGE_RECTS)


def stage_mask(k):
    """무대(STAGE ∪ STAGE_EXT) 마스크, k px/mm"""
    m = Image.new("L", (PW * k, PH * k), 0)
    d = ImageDraw.Draw(m)
    for r in STAGE_RECTS:
        d.rectangle([r[0] * k, r[1] * k, r[2] * k - 1, r[3] * k - 1], fill=255)
    return m


# ───────────────────────── 빈 자리 마스크(지붕·나무·밭이 라벨·패널·길을 덮지 않게) ─────────────────────────
EXK = 2      # 마스크 해상도 px/mm
EXCL = Image.new("L", (PW * EXK, PH * EXK), 0)
EXD = ImageDraw.Draw(EXCL)
STAGE_M2 = stage_mask(EXK)


def ex_poly(pts, pad=0.0):
    q = [(x * EXK, y * EXK) for x, y in pts]
    EXD.polygon(q, fill=255)
    if pad > 0:
        EXD.line(q + [q[0]], fill=255, width=max(1, int(round(2 * pad * EXK))), joint="curve")


def ex_rect(b, pad=0.0):
    EXD.rectangle([(b[0] - pad) * EXK, (b[1] - pad) * EXK, (b[2] + pad) * EXK, (b[3] + pad) * EXK], fill=255)


def ex_circle(c, r, pad=0.0):
    rr = r + pad
    EXD.ellipse([(c[0] - rr) * EXK, (c[1] - rr) * EXK, (c[0] + rr) * EXK, (c[1] + rr) * EXK], fill=255)


def ex_line(pts, w):
    EXD.line([(x * EXK, y * EXK) for x, y in pts], fill=255, width=max(1, int(round(w * EXK))))


def poly_in_stage(poly, tol=0.3):
    """다각형이 무대 합집합 안에 드는가(오른쪽 블리드 x > 420은 허용)"""
    q = [(min(x, PW - 0.01), y) for x, y in poly]
    if not all(in_stage(x, y, tol) for x, y in q):
        return False
    x0, y0, x1, y1 = bbox_of(q)
    X0, Y0 = int(math.floor(x0 * EXK)) - 1, int(math.floor(y0 * EXK)) - 1
    X1, Y1 = int(math.ceil(x1 * EXK)) + 2, int(math.ceil(y1 * EXK)) + 2
    m = Image.new("L", (X1 - X0, Y1 - Y0), 0)
    ImageDraw.Draw(m).polygon([(x * EXK - X0, y * EXK - Y0) for x, y in q], fill=255)
    out = ImageChops.subtract(m, STAGE_M2.crop((X0, Y0, X1, Y1)))
    return out.histogram()[255] <= 2 * EXK * EXK


def poly_free(poly, pad=0.0, stage=True):
    x0, y0, x1, y1 = bbox_of(poly)
    if x1 < 0 or x0 > PW:
        return False
    if stage and not poly_in_stage(poly, 0.0):
        return False
    X0 = int(math.floor((x0 - pad) * EXK))
    Y0 = int(math.floor((y0 - pad) * EXK))
    X1 = int(math.ceil((x1 + pad) * EXK)) + 1
    Y1 = int(math.ceil((y1 + pad) * EXK)) + 1
    m = Image.new("L", (X1 - X0, Y1 - Y0), 0)
    d = ImageDraw.Draw(m)
    q = [((x * EXK) - X0, (y * EXK) - Y0) for x, y in poly]
    d.polygon(q, fill=255)
    if pad > 0:
        d.line(q + [q[0]], fill=255, width=max(1, int(round(2 * pad * EXK))))
    crop = EXCL.crop((X0, Y0, X1, Y1))
    return ImageChops.multiply(m, crop).getbbox() is None


def box_poly(b):
    return [(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])]




# ───────────────────────── 콜로세움 기하(d5: 기준선 8.1·8.2 · 결정 D2·D3, Blender roma_colo·roma_colo_in과 같은 값) ─────────────────────────
# 사양 core_map.hero.colosseum·landscape 열쇠가 있으면 그 값을, 없으면 결정 상수를 쓴다.
# d4의 팔각 받침·지층 옆면·앞 변 기초 절개·원형 고리(ring_ratio 0.74)·벽 60/28/12·동심 관람석 그릇·가로벽 격자 하이포게움은 쓰지 않는다.
# 국소 좌표 (u, v): u = 장축(평면 방위 315°, 화면 가로), v = 단축(평면 방위 45°, 화면 아래). 화면 = (cx + 1.2247u, cy + 0.7071v − z).
# 외곽 타원 매개변수 t: (u, v) = (a·cos t, −b·sin t) — Blender Ell(a, b, 45°)의 t와 같다(칸 번호·들쭉날쭉 높이가 와이어프레임과 같게).
import bisect

KU, KV = 1.22474487, 0.70710678


def _hash01(*k):
    """Blender roma_kit.hash01과 같은 결정적 해시"""
    h = 2166136261
    for v in k:
        h = ((h ^ (int(v * 1000003) & 0xffffffff)) * 16777619) & 0xffffffff
    return (h % 100000) / 100000.0


def _rnd(i, k=0):
    return _hash01(i * 7.13 + k * 1.91, k + 3.3)


def _hv(d, keys, default):
    """사양 새 열쇠 읽기(숫자·숫자 목록). 없거나 형식이 다르면 결정 상수"""
    v = sget(d, *keys, default=None) if isinstance(d, dict) else None
    if v is None:
        return default
    try:
        if isinstance(v, (list, tuple)):
            out = [float(x) for x in v]
            return out if (not isinstance(default, list) or len(out) == len(default)) else default
        return float(v)
    except (TypeError, ValueError):
        return default


HCOL = sget(HERO, "colosseum", default=None) or {}
HLS = sget(HERO, "landscape", default=None) or {}
LS_C = tuple(_hv(HLS, ("center_plan", "plan_center", "c_plan"), [462.34, 173.66]))          # 조경 중심(옛 히어로 자리, 화면 (250, 318))
LS_R = float(_hv(HLS, ("reserve_r_plan", "reserve_r", "r_plan"), 90.0))                       # 예약 반지름(평면)
CO_C = tuple(_hv(HCOL, ("center_plan", "ellipse_center_plan", "plan_center", "c_plan"), [446.54, 161.86]))
CO_A, CO_B = _hv(HCOL, ("semi_axes", "semi_axes_plan", "axes"), [44.0, 36.6])
CO_NB = int(_hv(HCOL, ("arches", "n_bays", "bays"), 40))
CO_T1 = float(_hv(HCOL, ("wall_t", "outer_wall_t"), 2.4))
CO_G1 = float(_hv(HCOL, ("corridor_w", "outer_corridor_w"), 2.8))
CO_T2 = float(_hv(HCOL, ("ring2_t", "second_ring_t"), 1.6))
CO_D2 = CO_T1 + CO_G1                                                                          # 둘째 고리 바깥면 깊이 5.2
CO_D3 = (9.2, 10.4)                                                                            # 셋째 고리벽(출입구 아치)
CO_DC = tuple(_hv(HCOL, ("seating_depth", "cavea_depth"), [10.4, 22.7]))
CO_ZC = tuple(_hv(HCOL, ("seating_z", "cavea_z"), [24.0, 4.4]))                              # 관람석 윗선 → 아랫선
CO_DP = tuple(_hv(HCOL, ("podium_depth",), [22.7, 23.9]))
CO_ARS = tuple(_hv(HCOL, ("arena_semi_axes", "arena_axes"), [round(CO_A - CO_DP[1], 2), round(CO_B - CO_DP[1], 2)]))   # 20.1 × 12.7
CO_AR = (CO_ARS[0] + 0.05, CO_ARS[1] + 0.05)                                                   # Blender build_arena와 같은 바닥 타원
CO_US = float(_hv(HCOL, ("u_split", "floor_u_split", "wood_u_min"), -2.0))                    # u ≥ −2.0 나무 바닥(55%), u < −2.0 하이포게움
CO_ZF, CO_ZP = 0.6, float(_hv(HCOL, ("pit_z", "hypogeum_floor_z"), -4.0))
CO_BOX = tuple(_hv(HCOL, ("building_screen_box", "screen_box", "building_box", "projected_box"), [267.44, 232.57, 375.21, 336.12]))
CO_SEAT = ((238.0, 360.0), (0.0, 48.0))                                                        # 계단석 구역(나머지는 방사벽 + 짙은 빈칸)
CO_ST = [dict(z0=0.0, z1=11.5, ob=0.0, sp=5.5, ent=1.45, order="T"), dict(z0=11.5, z1=24.5, ob=12.7, sp=18.2, ent=1.45, order="I"),
         dict(z0=24.5, z1=37.0, ob=25.7, sp=30.9, ent=1.45, order="C"), dict(z0=37.0, z1=53.0, ob=None, sp=None, ent=1.3, order="A")]
_HYS = sget(HCOL, "hypogeum", default=None) or {}
HY = {"rings": _hv(_HYS, ("concentric", "rings", "concentric_fr"), [0.86, 0.72, 0.58, 0.44, 0.30]),
      "corr": float(_hv(_HYS, ("corridor_half_w", "corridor_half", "corridor"), 0.9)),
      "every": float(_hv(_HYS, ("partition_every_deg", "every_deg", "partition_deg"), 12.0)),
      "r_frac": _hv(_HYS, ("partition_r_frac", "r_frac", "partition_r"), [0.33, 0.97]),
      "t_ring": 0.55, "t_corr": 0.5, "t_part": 0.45, "z_top": CO_ZF - 0.15}
HS = float(_hv(HCOL, ("draw_scale",), 1.0))                                                       # 17:3x 위계 1번: 콜로세움 그림 배율
CX_S, CY_S = sp(*CO_C)                                                                         # 화면 (246.54, 304.2)
HERO_NAME = HERO.get("name") or "콜로세움(Amphitheatrum Flavium) — 히어로·최대 단일 오브젝트"
D5_HERO_TABLE = [(100, 104, 41.0), (104, 108, 46.0), (108, 112, 50.0), (112, 205, 53.0), (205, 209, 44.0), (209, 322, 37.0),
                 (322, 330, 31.0), (330, 338, 27.0), (338, 378, 24.5), (378, 432, 17.0), (432, 440, 30.0), (440, 460, 37.0)]   # 기준선 8.1 표(상한)


def _ell_table(a, b, n=6000):
    ts = [2.0 * math.pi * i / n for i in range(n + 1)]
    pts = [(a * math.cos(t), -b * math.sin(t)) for t in ts]
    cum = [0.0]
    for i in range(n):
        cum.append(cum[-1] + math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]))
    return ts, cum


_ETS, _ECUM = _ell_table(CO_A, CO_B)
CO_L = _ECUM[-1]
CO_W = CO_L / CO_NB                                                                            # 칸 폭(호 길이) ≈ 6.37
CO_OW = 0.64 * CO_W
CO_RA = CO_OW / 2.0


def e_t(s):
    s %= CO_L
    i = bisect.bisect_right(_ECUM, s) - 1
    i = min(max(i, 0), len(_ECUM) - 2)
    f = (s - _ECUM[i]) / max(1e-12, _ECUM[i + 1] - _ECUM[i])
    return _ETS[i] + f * (_ETS[i + 1] - _ETS[i])


def e_frame(s):
    """호 길이 s → 외곽 점 (u, v), 바깥 법선 (nu, nv), 접선 (tu, tv)(s 증가 방향)"""
    t = e_t(s)
    u, v = CO_A * math.cos(t), -CO_B * math.sin(t)
    nu, nv = math.cos(t) / CO_A, -math.sin(t) / CO_B
    ln = math.hypot(nu, nv)
    du, dv = -CO_A * math.sin(t), -CO_B * math.cos(t)
    lt = math.hypot(du, dv)
    return u, v, nu / ln, nv / ln, du / lt, dv / lt


def e_uv(s, d):
    u, v, nu, nv, _tu, _tv = e_frame(s)
    return u - nu * d, v - nv * d


def M(s, d, z=0.0):
    """호 길이 s, 안쪽 깊이 d(평행 곡선, Blender E.M과 같다), 높이 z → 화면 점"""
    u, v = e_uv(s, d)
    return (CX_S + HS * KU * u, CY_S + HS * (KV * v - z))


def uvz(u, v, z=0.0):
    return (CX_S + HS * KU * u, CY_S + HS * (KV * v - z))


def az_uv(u, v):
    """국소 (u, v) → 평면 방위(X→Y 반시계, 도)"""
    return math.degrees(math.atan2(v - u, u + v)) % 360.0


def h1(th, i):
    """외벽 높이(roma_colo.h1과 같다): 100~205° 4층(앞 끝 경사 부벽 41·46·50, 뒤 끝 205~209° 수직 절단 44), 209~322° 3층(일부 33.5),
    322~338° 31·27, 338~18° 2층 24.5(들쭉날쭉 18.0~24.5), 18~72° 1층 + 토막(14.0~17.0), 72~100° 30·37.
    결정 D2 표를 따른다(roma_colo.h1의 72~100° −2.5 변형은 표에 없어 쓰지 않는다)"""
    th %= 360.0
    r = _rnd(i, 4)
    if 100.0 <= th < 205.0:
        if th < 104.0:
            return 41.0
        if th < 108.0:
            return 46.0
        if th < 112.0:
            return 50.0
        return 53.0
    if 205.0 <= th < 322.0:
        if th < 209.0:
            return 44.0
        return 37.0 if r > 0.25 else 33.5
    if 322.0 <= th < 338.0:
        return 31.0 if th < 330.0 else 27.0
    if 18.0 <= th < 72.0:
        return 14.0 + 3.2 * _rnd(i, 8)
    if th >= 338.0 or th < 18.0:
        return 24.5 - (0.0 if r > 0.55 else (2.0 + 4.5 * _rnd(i, 7)))
    return 30.0 if th < 80.0 else 37.0                                   # 72~80° 30 · 80~100° 37(결정 D2 표 그대로, 변형 없음)


def h2(th, i):
    """둘째 고리(안쪽 아케이드) 높이(roma_colo.h2와 같다): 37, 정면 10~80°만 9~12"""
    th %= 360.0
    if 100.0 <= th < 209.0:
        return 37.0
    if 10.0 <= th < 80.0:
        return 9.0 + 3.0 * _rnd(i, 6)
    return 37.0 - (0.0 if _rnd(i, 5) > 0.35 else 2.0 + 3.0 * _rnd(i, 6))


def seat_sector(th):
    th %= 360.0
    return any(a <= th < b for a, b in CO_SEAT)


def _top_tilt(H, i, stories, tilt, add=0):
    """무너진 윗선 기울기(roma_colo.cut_top): 맨 위 층이 잘렸으면 tan(a), 아니면 0"""
    k_top = None
    for k, s_ in enumerate(stories):
        if s_["z0"] >= H - 0.2:
            break
        k_top = k
    if k_top is None:
        return 0.0, None
    if H < stories[k_top]["z1"] - 0.05:
        a = math.radians((_rnd(i * 4 + k_top + add, 9) * 2 - 1) * tilt)
        return math.tan(a), k_top
    return 0.0, k_top


def _bays():
    out = []
    for i in range(CO_NB):
        sc = (i + 0.5) * CO_W
        u, v, nu, nv, tu, tv = e_frame(sc)
        th = az_uv(u, v)
        H1, H2 = h1(th, i), h2(th, i)
        tg1, k1 = _top_tilt(H1, i, CO_ST, 14.0)
        tg2, k2 = _top_tilt(H2, i, CO_ST[:3], 20.0, 101)
        ztop = min(CO_ZC[0], H2 - 9.0) if not (100.0 <= th < 209.0) else CO_ZC[0]
        ztop = max(ztop, 12.0)
        if 8.0 <= th < 82.0:
            ztop = 6.0                                                   # 정면: 관람석이 무너져 경기장이 보인다
        out.append(dict(i=i, s0=i * CO_W, s1=(i + 1) * CO_W, sc=sc, th=th, v=v, nv=nv, tu=tu, tv=tv, H1=H1, H2=H2, tg1=tg1, tg2=tg2,
                        k1=k1, k2=k2, ztop=ztop, back=(nv < 0.0)))
    return out


BAYS = _bays()


def z_wall(b, s, which=1):
    """칸 b의 호 길이 s 자리 윗선 높이(기운 윗선)"""
    x = s - b["sc"]
    return (b["H1"] - b["tg1"] * x) if which == 1 else (b["H2"] - b["tg2"] * x)




def ls_pt(r, th):
    """조경 중심 기준 평면 반지름 r, 방위 th → 화면 점"""
    t = math.radians(th)
    return sp(LS_C[0] + r * math.cos(t), LS_C[1] + r * math.sin(t))






METELLA_F = [1.04]


def metella_box(f=None):
    """L5 메텔라: 사양 상자 [354, 288, 420, 358](d4)면 중심 기준 1.04배(결정 D4, x 420에서 잘림). 다른 값이면 사양 그대로"""
    b = list(LM["L5"]["projected_box"])
    f = METELLA_F[0] if f is None else f
    if _same(b, [354.0, 288.0, 420.0, 358.0], 0.3):
        cx, cy = (b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0
        hw, hh = (b[2] - b[0]) / 2.0 * f, (b[3] - b[1]) / 2.0 * f
        return (cx - hw, cy - hh, cx + hw, cy + hh)
    return tuple(b)


# ───────────────────────── 바닥 글(사양 floor_text 5) ─────────────────────────
def floor_specs():
    """바닥 글(사양 floor_text anchor). parts = (글, 글꼴 종류, 글자면 mm, 색). 강·길 위 글은 사양 anchor의 x를 쓰고 기준선을 그 띠 안에 둔다."""
    out = []
    # TIBERIS 테베레강: ↘ 팔 물 위, 글 높이 가운데가 중심선(평면 Y 314)에 오게
    # 22:33 오른쪽 아래 바다: 테베레 어귀부터 바다 글(티레니아해)
    ax, ay = 300.0, 452.0
    out.append(dict(name="MARE TYRRHENUM 티레니아해", M=M_WALL_UP, ax=ax, ay=ay, parts=[("MARE TYRRHENUM", "en", 3.3, INK_WATER), ("티레니아해", "b", 3.1, INK_WATER)]))
    # MARE TYRRHENUM 티레니아해: 두 줄 — 왼쪽 아래 열린 바다
    a = FLOOR["MARE"]["anchor"]
    ax, ay = a[0], a[1]
    out.append(dict(name="MARE TYRRHENUM", M=M_FLOOR_SE, ax=ax, ay=ay, parts=[("MARE TYRRHENUM", "en", 3.3, INK_WATER)]))
    q = map_pt(M_FLOOR_SE, ax, ay, 0.0, 5.2)
    out.append(dict(name="티레니아해", M=M_FLOOR_SE, ax=q[0], ay=q[1], parts=[("티레니아해", "b", 3.1, INK_WATER)]))
    # 사용자 16:14: VIA APPIA·COLLI ALBANI·OSTIA 바닥 글은 지도에서 지웠다(길·구릉·오스티아가 없다). TIBERIS·MARE TYRRHENUM만 남는다
    for f in out:
        fp = []
        for t, kind, face, c in f["parts"]:
            ft, em, fa = fface(kind, face, t)
            fp.append((t, ft, c, kind, em, fa))
        f["fparts"] = fp
        W = sum(tw(t, ft) + 1.6 for t, ft, *_r in fp) - 1.6
        cap = max(fa for *_r, fa in fp)
        f["W"], f["cap"] = W, cap
        f["poly"] = [map_pt(f["M"], f["ax"], f["ay"], u, v) for u, v in ((0, -cap - 0.2), (W, -cap - 0.2), (W, 0.9), (0, 0.9))]
    return out


FLOORS = floor_specs()


def z1_text_box():
    return tuple(sget(DMAP["Z1"], "text_box", "textbox", default=[214.0, 426.0, 242.0, 462.0]))


def z1_composite_box():
    return tuple(sget(DMAP["Z1"], "composite_box", "composite", default=[214.0, 420.0, 305.0, 480.0]))


def detail_leaders():
    """Detail·Basic 지시선(사양 꼭짓점 그대로): [(이름, 점들, 짝 표지 글자, 종류)].
    짝 표지 글자는 사양 mark 값만 쓴다(지시선 이름에서 추론하지 않는다). 표지 자리는 MARKS(사양 mark_pt)가 맡는다."""
    out = []
    lk = BAS["process_representation"].get("link")
    if lk:
        out.append((lk["name"], [tuple(p) for p in lk["pts"]], None, "basic"))
    for ld in DET["leaders"]:
        out.append((ld["name"], [tuple(p) for p in ld["pts"]], ld.get("mark"), "detail"))
    return out


NEW_LM = ("L7", "L8", "L9")      # 새 랜드마크: 사각 상자 대신 실제 실루엣 + 2mm로 빈 자리를 막는다(그린 뒤 등록)


def build_exclusions():
    for l in CM["landmarks"]:
        if l["id"] in NEW_LM:
            continue
        ex_rect(metella_box() if l["id"] == "L5" else l["projected_box"], 1.4)
    ex_poly(col_sil_approx(), 1.5)                                   # d5: 받침 0 — 콜로세움 실루엣만 먼저 막는다
    for p in CM["props"]:
        if p["name"].startswith("포도밭 농장") or p["name"].startswith("네로"):
            continue                                    # 농장은 지형 층에서 직접 그린다(밭 배치가 피한다). 거상은 실루엣 + 2mm로 막는다
        ex_rect(p["box"], 1.0)
    for f in FLOORS:
        ex_poly(f["poly"], 1.0)
    mh_ = {}                                             # 20:53 번호·입구 표지 제거: 지도 장 머리 없음
    if mh_:                                              # ❸ 지도 장 머리(배지 + 제목)
        bc_ = mh_["badge_c"]
        ex_rect([bc_[0] - 6.5, bc_[1] - 6.5, mh_["title_x"] + 26.0, bc_[1] + 6.5], 1.5)
    for pid, pn in PANEL.items():
        ex_rect(pn["rect"], 2.0)
    for _nm, pts, _l, _k in detail_leaders():
        ex_line(pts, 2.6)
    ex_poly([tuple(p) for p in RV["polygon_screen"]], 1.2)
    ex_poly([tuple(p) for p in SC["sea_polygon"]], 1.5)
    (x0s, y0s), (x1s, y1s) = CM["aqueduct"]["ground_line_screen"]
    H = CM["aqueduct"]["arch_height_mm"]
    ex_poly([(x0s, y0s - H - 1), (x1s, y1s - H - 1), (x1s, y1s + 2), (x0s, y0s + 2)], 1.0)


# ───────────────────────── 1 지면·밭·구릉 ─────────────────────────
def sea_corner():
    """하단 오른쪽 확장 자리 중 해안선(y = tan30·x + 380) 아래 귀퉁이 = 띠 밑 바다(사양 terrain sea_corner)"""
    for t in CM.get("terrain", []):
        if t.get("sea_corner"):
            return [tuple(p) for p in t["sea_corner"]]
    for r in STAGE_EXT:
        if r[1] >= STAGE[3] - 0.5:
            x0, y0, x1, y1 = r
            yc = T30 * x0 + COAST_B
            if yc < y1:
                return [(x0, yc), ((y1 - COAST_B) / T30, y1), (x0, y1)]
    return None


def land_mask(k):
    """지면 마스크 = 무대 − 띠 밑 바다 귀퉁이"""
    return stage_mask(k)                                              # 22:33 왼쪽 아래 바다 없음(바다는 오른쪽 아래 모서리)


def draw_ground():
    """지면 + 격자(무대 STAGE ∪ STAGE_EXT, 오른쪽 위 '가장 먼 곳'과 하단 오른쪽 교외 밭까지)"""
    G0 = Layer(0, 0, PW, PH)
    for r in STAGE_RECTS:
        G0.rect(r[0], r[1], r[2], r[3], fill=GROUND)
    span = PW * T30
    for k in range(-60, 90):
        y0 = STAGE[1] + k * 14.0
        G0.line([(0, y0), (PW, y0 + span)], GRID_OP, 0.16, joint=False)
        G0.line([(0, y0 + span), (PW, y0)], GRID_OP, 0.16, joint=False)
    G0.img.putalpha(ImageChops.multiply(G0.img.getchannel("A"), land_mask(KD)))
    P.paste(G0)
    sc_ = sea_corner()
    if sc_:
        ex_poly(sc_, 0.6)


FIELD_BASE = {"vine": (186, 190, 122), "wheat": WHEAT_C, "pasture": PASTURE_C, "fallow": (216, 198, 152), "olive": (186, 192, 128)}


















# ───────────────────────── 2 강·바다·해안 ─────────────────────────
DIO_T = 7.0                       # 20:40 디오라마: 블록 옆면 높이(화면 mm) = 수면이 땅보다 낮은 깊이(Blender water_z −7과 같다)
DIO_STRATA = [(1.2, (222, 200, 150)), (2.2, (186, 146, 100)), (2.0, (150, 112, 78)), (1.6, (126, 98, 72))]   # 표토 → 황토 → 응회암 → 콘크리트(합 7.0)


def draw_river():
    """물(테베레 + 블록 사이 운하): 직사각형(평면 X·Y축) 여러 개를 같은 물색으로. 옆면·낮춘 수면은 draw_diorama_water가 맡는다."""
    rects = [[tuple(q) for q in r["polygon_screen"]] for r in (RV.get("water_rects") or [])]
    for r_, pg in zip((RV.get("water_rects") or []), rects):
        col_ = SEA_C if r_.get("tone") == "sea" else RIV_C
        P.poly(pg, fill=col_)
        facet_fill(P, pg, col_, cell=7.0 if col_ == SEA_C else 6.0, amp=0.045 if col_ == SEA_C else 0.05, key="바다" if col_ == SEA_C else "강", jit=0.12)
    loops = [[tuple(q) for q in lp] for lp in (RV.get("water_loops_screen") or [])]
    GEO["water_rects"] = rects
    GEO["water_loops"] = loops
    poly = [tuple(p) for p in RV["polygon_screen"]]
    GEO["river_poly"] = poly
    n = len(poly) // 2
    GEO["river_left"], GEO["river_right"] = poly[:n], poly[n:][::-1]


def _loop_dir(lp):
    a = sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(lp, lp[1:] + lp[:1]))
    return 1.0 if a > 0 else -1.0


def draw_diorama_water(G, W):
    """수면을 DIO_T 아래로 내리고(W 층을 아래로 민다), 땅 가장자리 옆면(지층 줄무늬)을 그린 뒤, 땅 윗면을 G(바탕 복사본)로 되돌린다."""
    off = int(round(DIO_T * KD))
    sh = Image.new("RGBA", W.img.size, (0, 0, 0, 0))
    sh.paste(W.img, (0, off))
    BASE.img.alpha_composite(sh)
    loops = GEO.get("water_loops") or []
    faces = []
    for lp in loops:
        sgn = _loop_dir(lp)
        n = len(lp)
        for i in range(n):
            a, b = lp[i], lp[(i + 1) % n]
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy)
            if L < 0.5:
                continue
            nx, ny = dy / L * sgn, -dx / L * sgn                    # 물 바깥(땅 쪽) 법선: 수식 부호는 아래서 시험으로 바로잡는다
            mid = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
            probe = (mid[0] + nx * 0.8, mid[1] + ny * 0.8)
            if any(in_poly(probe, pg) for pg in GEO["water_rects"]):
                nx, ny = -nx, -ny
            if ny < -0.3:                                            # 땅이 화면 위쪽에 있다 = 옆면이 보인다
                faces.append((a, b, 0.80 if dx * dy < 0 else 0.92))
    use_layer(BASE)
    for a, b, f in faces:
        mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
        Xp, Yp = ((mx / C30 + 2.0 * my) / 2.0, (2.0 * my - mx / C30) / 2.0)
        lot = lot_of_probe(Xp, Yp - 6.0)
        style_face(BASE, a, b, (lot or {}).get("style", "earth"), f, T=DIO_T)
    # 땅 윗면 복원: 물 직사각형 밖 = 땅
    m = Image.new("L", BASE.img.size, 0)
    md = ImageDraw.Draw(m)
    for pg in GEO["water_rects"]:
        md.polygon([((x) * KD, (y) * KD) for x, y in pg], fill=255)
    BASE.img.paste(G, (0, 0), ImageChops.invert(m))
    for a, b, f in faces:                                            # 윗면 가장자리 띠(밝은 모래 선)
        BASE.line([a, b], (240, 226, 190), 0.5)
    DRAWN["diorama"] = {"water_depth_mm": DIO_T, "strata_mm": [t for t, _ in DIO_STRATA], "face_edges": len(faces)}


ROAD_FILL, ROAD_EDGE_C, ROAD_JOINT_C = (222, 214, 196), (176, 164, 138), (204, 194, 172)


def _plan_rect_screen(X0, X1, Y0, Y1):
    return [ISO.p(X0, Y0), ISO.p(X1, Y0), ISO.p(X1, Y1), ISO.p(X0, Y1)]


FACE_STYLES = {
    "earth": dict(layers=DIO_STRATA, joints=None),
    "travertine": dict(layers=[(1.0, (238, 228, 200)), (3.0, (226, 212, 176)), (3.0, (218, 202, 164))], joints=("stone", 6.0, (176, 158, 120))),
    "ashlar": dict(layers=[(1.0, (214, 190, 146)), (6.0, (198, 172, 130))], joints=("stone", 8.0, (146, 118, 84))),
    "brick": dict(layers=[(1.0, (214, 196, 150)), (6.0, (184, 98, 72))], joints=("brick", 3.2, (130, 64, 46))),
    "quay": dict(layers=[(1.0, (224, 208, 170)), (6.0, (176, 166, 148))], joints=("stone", 5.0, (122, 112, 96))),
    "riverbank": dict(layers=[(1.0, (216, 198, 152)), (3.0, (182, 166, 134)), (3.0, (164, 150, 120))], joints=("stone", 6.0, (116, 104, 84))),
    "slab": dict(layers=[(1.0, (230, 220, 190)), (1.0, (214, 200, 164))], joints=("stone", 6.0, (160, 146, 114))),
}


def style_face(L, a, b, key, f, T=None):
    """화면 변 a→b 아래로 옆면: 층 색 + 줄눈(마름돌·벽돌·석축). 층 합 = T(없으면 스타일 층 합)"""
    st = FACE_STYLES.get(key) or FACE_STYLES["earth"]
    lay = st["layers"]
    tot = sum(t for t, _ in lay)
    if T is not None and abs(T - tot) > 1e-6:
        k = T / tot
        lay = [(t * k, c) for t, c in lay]
        tot = T
    strata_side(L, a, b, lay, f=f)
    jt = st.get("joints")
    if jt and tot > 2.0:
        kind, sp, col = jt
        col = tint(col, f)
        d0 = 0.0
        Lseg = math.hypot(b[0] - a[0], b[1] - a[1])
        if Lseg < 0.5:
            return
        for ci, (t, _c) in enumerate(lay[1:], 1):                     # 층 경계선(켜)
            d0 += lay[ci - 1][0]
            L.line([(a[0], a[1] + d0), (b[0], b[1] + d0)], col, 0.15, joint=False)
        d0 = lay[0][0]
        row = 0
        yy = d0
        for ci, (t, _c) in enumerate(lay[1:], 1):
            n = max(1, int(Lseg / sp))
            off = (0.5 if row % 2 else 0.0) * sp / Lseg
            for q in range(n + 1):
                u = (q / n + off) % 1.0 if n else 0.0
                x = a[0] + (b[0] - a[0]) * u
                y = a[1] + (b[1] - a[1]) * u + yy
                L.line([(x, y), (x, y + t)], col, 0.12, joint=False)
            yy += t
            row += 1


LOT_ID_OF_KEY = {"콜로세움": "colosseum", "판테온": "acropolis", "트라야누스 시장": "market", "수도교": "aqueduct", "마르켈루스 극장": "theatre", "막센티우스 바실리카": "basilica",
                 "하드리아누스 영묘": "mausoleum", "포르투스 항": "portus", "카이킬리아 메텔라 무덤": "metella"}


def lot_of_probe(Xp, Yp):
    """평면 점이 속한(가장 가까운) 구획"""
    best = None
    for lt in (CM.get("lots") or []):
        x0, x1, y0, y1 = lt["rect"]
        dx = max(x0 - Xp, 0.0, Xp - x1)
        dy = max(y0 - Yp, 0.0, Yp - y1)
        d = math.hypot(dx, dy)
        if best is None or d < best[0]:
            best = (d, lt)
    return best[1] if best and best[0] < 40.0 else None


def draw_plinths():
    """z > 0 구획(시장 벽돌 옹벽 비탈·메텔라 둔덕·바실리카 판석 단): 평면 직사각형 기단(윗면 + 보이는 두 옆면). 그 위 건물은 z만큼 올려 그린다."""
    for lt in (CM.get("lots") or []):
        z = float(lt.get("z", 0.0))
        if z <= 0.0 or lt.get("drawn_in"):
            continue
        x0, x1, y0, y1 = lt["rect"]
        top = [ISO.p(x0, y0, z), ISO.p(x1, y0, z), ISO.p(x1, y1, z), ISO.p(x0, y1, z)]
        P.poly(top, fill=GROUND if lt["style"] != "earth" else (206, 192, 136))
        P.poly(top, outline=(222, 206, 168), lw=0.3)
        st_key = lt["style"]
        # +X 면(오른쪽 아래): 변 (x1,y0)→(x1,y1), +Y 면(왼쪽 아래): 변 (x1,y1)→(x0,y1)
        a, b = ISO.p(x1, y0, z), ISO.p(x1, y1, z)
        style_face(P, a, b, st_key, 0.86, T=z)
        a, b = ISO.p(x1, y1, z), ISO.p(x0, y1, z)
        style_face(P, a, b, st_key, 0.98, T=z)


def draw_roads():
    """20:53 Core를 잇는 도로 = 구획 경계선. 판석 길(X·Y축 직선), 물 위는 다리(상판 + 아래 그늘). 폭 7 = 강(26)·운하(12)보다 가늘다."""
    nets = CM.get("road_net") or []
    water = [(r["plan_X"], r["plan_Y"]) for r in (RV.get("water_rects") or [])]
    DRAWN["road_net"] = []
    for rd in nets:
        pts = [tuple(p) for p in rd["pts"]]
        hw = float(rd["w"]) / 2.0
        bridges = []
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            along_x = abs(y1 - y0) < 1e-6
            a0, a1 = (min(x0, x1), max(x0, x1)) if along_x else (min(y0, y1), max(y0, y1))
            fx = y0 if along_x else x0                                   # 고정 좌표
            ext = hw
            A0, A1 = a0 - ext, a1 + ext
            if along_x:
                rect = (A0, A1, fx - hw, fx + hw)
            else:
                rect = (fx - hw, fx + hw, A0, A1)
            P.poly(_plan_rect_screen(*rect), fill=ROAD_FILL)
            GEO.setdefault("road_polys", []).append(_plan_rect_screen(*rect))
            # 판석 이음(가로선): 5 간격
            k = A0 + 2.5
            while k < A1:
                if along_x:
                    P.line([ISO.p(k, fx - hw), ISO.p(k, fx + hw)], ROAD_JOINT_C, 0.12, joint=False)
                else:
                    P.line([ISO.p(fx - hw, k), ISO.p(fx + hw, k)], ROAD_JOINT_C, 0.12, joint=False)
                k += 5.0
            if along_x:
                P.line([ISO.p(A0, fx - hw), ISO.p(A1, fx - hw)], ROAD_EDGE_C, 0.3, joint=False)
                P.line([ISO.p(A0, fx + hw), ISO.p(A1, fx + hw)], ROAD_EDGE_C, 0.3, joint=False)
            else:
                P.line([ISO.p(fx - hw, A0), ISO.p(fx - hw, A1)], ROAD_EDGE_C, 0.3, joint=False)
                P.line([ISO.p(fx + hw, A0), ISO.p(fx + hw, A1)], ROAD_EDGE_C, 0.3, joint=False)
            # 다리: 중심선이 물 직사각형 안인 구간
            for (wX, wY) in water:
                if along_x:
                    if wY[0] <= fx <= wY[1]:
                        lo, hi = max(A0, wX[0]), min(A1, wX[1])
                        if hi - lo > 1.0:
                            bridges.append((True, fx, lo, hi))
                else:
                    if wX[0] <= fx <= wX[1]:
                        lo, hi = max(A0, wY[0]), min(A1, wY[1])
                        if hi - lo > 1.0:
                            bridges.append((False, fx, lo, hi))
        for ax_, fx, lo, hi in bridges:                                 # 다리 그늘(상판 아래 면) + 난간
            if ax_:
                q = [ISO.p(lo, fx + hw), ISO.p(hi, fx + hw)]
                P.poly([q[0], q[1], (q[1][0], q[1][1] + 2.2), (q[0][0], q[0][1] + 2.2)], fill=(150, 132, 104))
                for sd in (-hw, hw):
                    P.line([ISO.p(lo, fx + sd), ISO.p(hi, fx + sd)], (120, 104, 80), 0.5, joint=False)
            else:
                q = [ISO.p(fx + hw, lo), ISO.p(fx + hw, hi)]
                P.poly([q[0], q[1], (q[1][0], q[1][1] + 2.2), (q[0][0], q[0][1] + 2.2)], fill=(136, 118, 92))
                for sd in (-hw, hw):
                    P.line([ISO.p(fx + sd, lo), ISO.p(fx + sd, hi)], (120, 104, 80), 0.5, joint=False)
        DRAWN["road_net"].append({"id": rd["id"], "pts": rd["pts"], "w": rd["w"], "bridges": [{"axis": "X" if b[0] else "Y", "fixed": b[1], "span": [round(b[2], 1), round(b[3], 1)]} for b in bridges]})


def draw_sea():
    sea = [tuple(p) for p in SC["sea_polygon"]]
    under = [tuple(p) for p in SC["sea_under_bottom_band"]["poly"]]
    ys = [p[1] for p in under]
    xs = [p[0] for p in under]
    U = Layer(0, min(ys), max(xs), max(ys))
    U.poly(under, fill=SEA_C)
    g = Image.linear_gradient("L").resize((U.w, U.h)).point(lambda v: int((255 - v) * 0.62))
    U.img.putalpha(ImageChops.multiply(U.img.getchannel("A"), g))
    P.paste(U)
    P.poly(sea, fill=SEA_C)
    facet_fill(P, sea, SEA_C, cell=7.0, amp=0.045, key="바다", jit=0.12)
    for k in range(10):
        off = 15.0 + k * 11.0
        xa = 2.0 + (k % 3) * 8.0
        xb = min((STAGE[3] - COAST_B - off) / T30, xa + 62.0)
        if xb > xa + 8:
            P.line([(xa, COAST_B + off + T30 * xa), (xb, COAST_B + off + T30 * xb)], (176, 204, 224), 0.3, joint=False)


def _mouth_x():
    """하구가 해안선을 지나는 x 범위(강 다각형과 해안선의 교차)"""
    poly_ = [tuple(p) for p in RV["polygon_screen"]]
    xs_ = [k * 0.2 for k in range(0, 900) if in_poly((k * 0.2, coast_y(k * 0.2)), poly_)]
    return (min(xs_), max(xs_)) if xs_ else (C30 * (RIV_XB - RIV_HW2 - COAST_B), C30 * (RIV_XB + RIV_HW2 - COAST_B))


MOUTH_X = _mouth_x()                                                                   # 하구가 해안선을 지나는 x 범위
QUAY_X = (0.0, 62.0)                                                                  # 포르투스 부두 구간(3mm 단면)


def draw_coast_section():
    Lc = Layer(0, STAGE[1], PW, STAGE[3])
    x_end = (STAGE[3] - COAST_B) / T30

    def cp(x):
        return (x, coast_y(x))
    segs = [(QUAY_X[0], QUAY_X[1], "quay"), (QUAY_X[1], MOUTH_X[0], "strata"), (MOUTH_X[0], MOUTH_X[1], "mouth"), (MOUTH_X[1], x_end, "strata")]
    for xa, xb, kind in segs:
        a, c = cp(xa), cp(xb)
        if kind == "quay":
            dd = QUAY_DEEP
            Lc.poly([a, c, (c[0], c[1] + dd), (a[0], a[1] + dd)], fill=(198, 186, 160), outline=(120, 104, 80), lw=0.2)
            for t in range(1, 16):
                pt = lerp(a, c, t / 16.0)
                Lc.line([pt, (pt[0], pt[1] + dd)], (150, 136, 110), 0.12, joint=False)
        elif kind == "strata":
            dd = COAST_DEEP
            lay = [(1.4, (94, 126, 66)), (dd * 0.42, (130, 100, 64)), (dd - 1.4 - dd * 0.42, (156, 124, 86))]
            strata_side(Lc, a, c, lay, f=0.86)
        else:
            dd = COAST_DEEP
            Lc.poly([a, c, (c[0], c[1] + dd), (a[0], a[1] + dd)], fill=(124, 180, 216))
            for t in range(1, 9):
                pt = lerp(a, c, t / 9.0)
                Lc.line([(pt[0], pt[1] + 0.6), (pt[0], pt[1] + dd - 0.4)], (196, 226, 242), 0.22, joint=False)
    P.paste(Lc)
    a, c = cp(MOUTH_X[0]), cp(MOUTH_X[1])
    soft_ell(P, (a[0] + c[0]) / 2.0, (a[1] + c[1]) / 2.0 + COAST_DEEP + 0.6, 11.0, 2.4, (255, 255, 255), alpha=110, blur=0.7)
    soft_line(P, [(0, COAST_B + 0.2), (MOUTH_X[0], coast_y(MOUTH_X[0]) + 0.2)], (40, 60, 80), alpha=60, w=0.8, blur=0.4)
    soft_line(P, [(MOUTH_X[1], coast_y(MOUTH_X[1]) + 0.2), (x_end, STAGE[3] + 0.2)], (40, 60, 80), alpha=60, w=0.8, blur=0.4)


# ───────────────────────── 3 길·바닥 글 ─────────────────────────




# ───────────────────────── 읽기 길 R_route(사용자 16:41): 입구 → 정거장 11 → 테베레강 → 출구 ─────────────────────────
ROUTE = next((r for r in CM["roads"] if r.get("id") == "R_route"), None)
ROUTE_FILL, ROUTE_EDGE, ROUTE_JOINT = (214, 206, 189), (185, 174, 152), (200, 191, 171)
ROUTE_W_MM = float((ROUTE or {}).get("w_screen_perp_mm", 5.0))
ROUTE_HW = ROUTE_W_MM / (2.0 * C30)


def _route_pts(key):
    if not ROUTE:
        return []
    v = ROUTE.get(key)
    return [tuple(p) for p in (v or [])]


def _band(p0, p1, ext0=True, ext1=True):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy * ROUTE_HW, ux * ROUTE_HW
    a = (p0[0] - ux * ROUTE_HW * ext0, p0[1] - uy * ROUTE_HW * ext0)
    b = (p1[0] + ux * ROUTE_HW * ext1, p1[1] + uy * ROUTE_HW * ext1)
    return [sp(a[0] + nx, a[1] + ny), sp(b[0] + nx, b[1] + ny), sp(b[0] - nx, b[1] - ny), sp(a[0] - nx, a[1] - ny)]


def route_polys():
    pl = _route_pts("plan_pts")
    return [_band(p0, p1) for p0, p1 in zip(pl[:-1], pl[1:]) if math.hypot(p1[0] - p0[0], p1[1] - p0[1]) > 1e-6]


def draw_route():
    """폭 5mm 판석 길(#D6CEBD, 가장자리 #B9AE98 0.3mm)과 강 구간 짙은 잉크 점선(0.5mm, 간격 2mm). 입구·출구 화살표는 draw_route_marks가 그린다"""
    if not ROUTE:
        return
    pl = _route_pts("plan_pts")
    spts = [sp(*p) for p in pl]
    P.line(spts, ROUTE_EDGE, ROUTE_W_MM + 0.6, joint=True)                       # 가장자리 선 0.3mm(양쪽)
    P.line(spts, ROUTE_FILL, ROUTE_W_MM, joint=True)
    for p0, p1 in zip(pl[:-1], pl[1:]):                                          # 판석 줄눈(길 가로, 0.12mm)
        L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        if L < 1e-6:
            continue
        ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
        nx, ny = -uy * ROUTE_HW * 0.9, ux * ROUTE_HW * 0.9
        t = 3.0
        while t < L - 1.0:
            cx, cy = p0[0] + ux * t, p0[1] + uy * t
            P.line([sp(cx + nx, cy + ny), sp(cx - nx, cy - ny)], ROUTE_JOINT, 0.12, joint=False)
            t += 6.0
    rv = _route_pts("river_plan")
    for p0, p1 in zip(rv[:-1], rv[1:]):
        P.dashed(sp(*p0), sp(*p1), INK_L, 0.5, 0.5, 2.0)
    DRAWN["roads"].append({"id": "R_route", "name": ROUTE.get("name", "R_route"), "polys": [[[round(x, 2), round(y, 2)] for x, y in pg] for pg in route_polys()]})
    GEO["route_polys"] = route_polys()


def _arrow(p_tip, u, size=5.0, half=2.2):
    """평면 점 p_tip(끝)에서 방향 u(평면 단위 벡터)로 가리키는 삼각 화살표(화면 mm 크기)"""
    tip = sp(*p_tip)
    b = sp(p_tip[0] - u[0] * size, p_tip[1] - u[1] * size)
    nx, ny = -u[1], u[0]
    w = half / C30 * 0.55
    return [tip, sp(p_tip[0] - u[0] * size + nx * w, p_tip[1] - u[1] * size + ny * w), sp(p_tip[0] - u[0] * size - nx * w, p_tip[1] - u[1] * size - ny * w)]


def draw_route_marks():
    """입구·출구 화살표와 글(정보 잉크). 입구 = 오른쪽 가장자리 메텔라 곁, 출구 = 포르투스 곁 해안 → ❹ 패널 쪽"""
    if not ROUTE:
        return
    pl = _route_pts("plan_pts")
    rv = _route_pts("river_plan")
    e0, e1 = pl[0], pl[1]
    L = math.hypot(e1[0] - e0[0], e1[1] - e0[1])
    u = ((e1[0] - e0[0]) / L, (e1[1] - e0[1]) / L)
    tip_e = (e0[0] + u[0] * 11.0, e0[1] + u[1] * 11.0)
    P.poly(_arrow(tip_e, u), fill=INK_L)
    x0, x1 = rv[-2], rv[-1]
    L2 = math.hypot(x1[0] - x0[0], x1[1] - x0[1])
    u2 = ((x1[0] - x0[0]) / L2, (x1[1] - x0[1]) / L2)
    P.poly(_arrow(x1, u2, size=6.0), fill=INK_L)
    ex = sp(*e0)
    mk = (S.get("route_marks") or {})
    ent = mk.get("entrance") or {}
    ex_ = mk.get("exit") or {}
    lines = ent.get("lines") or ["입구", "VIA APPIA", "아피아 가도"]
    base = ent.get("baselines_y") or [340.0, 345.5, 350.5]
    xr = float(ent.get("right_x", 419.0))
    kinds = [("b", 2.8, "subtitle"), ("en", 2.8, "head_en"), ("b", 2.6, "body")]
    for t, y, (kd, fc, role) in zip(lines, base, kinds):
        ptext(xr, float(y), t, kd, fc, INK_L, "route_mark" if role != "subtitle" else "subtitle", anchor="r", layer="입구 표지", panel="MAP")
    ptext(float(ex_.get("x", 126.0)), float(ex_.get("baseline_y", 470.0)), ex_.get("text", "출구 · 바다로 → 아래 만드는 과정"), "b", 2.8, INK_L, "subtitle", layer="출구 표지", panel="MAP")
    DRAWN["route_marks"] = {"entrance_screen": [round(ex[0], 2), round(ex[1], 2)], "exit_screen": [round(v, 2) for v in sp(*rv[-1])]}


def measure_route():
    """읽기 길 개선 수치(사후 ⑤): 길가 건물 수·건물–길 간격·라벨–길 교차·꺾임·길이·입구–❷·출구–❹ 거리"""
    if not ROUTE:
        return
    pl = _route_pts("plan_pts")
    rv = _route_pts("river_plan")
    polys = GEO.get("route_polys") or []
    riv = [tuple(p) for p in RV["polygon_screen"]]
    names = {"카이킬리아 메텔라 무덤": ["fp_메텔라 대지"], "수도교": ["fp_수도교 아치 면"], "카라칼라 욕장": ["fp_욕장 지면"], "콜로세움": ["fp_콜로세움 건물"],
             "막센티우스 바실리카": ["fp_바실리카 지면"], "트라야누스 시장": ["fp_시장 지면"], "판테온": ["fp_아크로폴리스 지면"],
             "마르켈루스 극장": ["fp_극장 반원 아케이드"], "하드리아누스 영묘·폰스 아일리우스(강)": ["fp_영묘 기단"], "포르투스(출구)": ["fp_포르투스 육각 내항"]}
    stops = {}
    for nm, keys in names.items():
        fps_ = [GEO[k] for k in keys if GEO.get(k)]
        if not fps_:
            stops[nm] = None
            continue
        d_land = min(_poly_dist(pg, fp) for pg in polys for fp in fps_) if polys else 99.0
        d_riv = _poly_dist(riv, fps_[0]) if nm.startswith(("하드리아누스", "포르투스")) else 99.0
        stops[nm] = {"gap_mm": round(min(d_land, d_riv), 2), "via": "강" if d_riv < d_land else "땅 길"}
    land_len = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pl[:-1], pl[1:]))
    riv_len = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(rv[:-1], rv[1:]))

    def turns(pts):
        n = 0
        for a, b, c in zip(pts[:-2], pts[1:-1], pts[2:]):
            if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) > 1e-6:
                n += 1
        return n
    cross = []
    for lb in DRAWN["labels"]:
        lp = [tuple(p) for p in lb.get("poly", [])]
        if lp and any(_poly_dist(lp, pg) < 0.05 or _pt_in_any(lp, pg) for pg in polys):
            cross.append(lb["name"])
    ent = sp(*pl[0])
    ext = sp(*rv[-1])
    p2 = PANEL["P2"]["rect"]
    pb = PANEL["B"]["rect"]
    DRAWN["route"] = {"id": "R_route", "width_mm": ROUTE_W_MM, "land_length_mm": round(land_len, 1), "river_length_mm": round(riv_len, 1),
                      "turns": turns(pl) + turns(rv), "stops": stops,
                      "stops_total": len(names), "stops_within_3mm": sum(1 for v in stops.values() if v and v["gap_mm"] <= 3.0),
                      "stops_within_8mm": sum(1 for v in stops.values() if v and v["gap_mm"] <= 8.0),
                      "max_gap_mm": max([v["gap_mm"] for v in stops.values() if v] or [0.0]),
                      "label_cross": cross, "label_cross_count": len(cross),
                      "entrance_screen": [round(ent[0], 2), round(ent[1], 2)], "exit_screen": [round(ext[0], 2), round(ext[1], 2)],
                      "entrance_to_P2_mm": round(math.hypot(ent[0] - min(max(ent[0], p2[0]), p2[2]), ent[1] - p2[3]), 1),
                      "exit_to_B_mm": round(math.hypot(ext[0] - min(max(ext[0], pb[0]), pb[2]), ext[1] - pb[1]), 1)}


def _pt_in_any(pts, pg):
    return any(in_poly(p, pg) for p in pts)


FLOOR_DRAWS = [0]


def draw_floor_texts():
    FLOOR_DRAWS[0] += 1
    for f in FLOORS:
        u = 0.0
        (a, b), (c, d) = f["M"]
        for (t, ft, col, kind, em, fa) in f["fparts"]:
            iso_text(P, t, ft, col, f["M"], f["ax"] + a * u, f["ay"] + c * u)
            w = tw(t, ft)
            poly = [map_pt(f["M"], f["ax"], f["ay"], u + uu, vv) for uu, vv in ((0, -fa), (w, -fa), (w, 0.3), (0, 0.3))]
            rec_text(t, "floor_" + ("en" if kind == "en" else "ko"), kind, em, fa, poly, layer="바닥 글")
            u += w + 1.6


def register_floor_polys():
    """바닥 글 외곽을 라벨 자리 잡기 장애물로 먼저 등록한다(바닥 글은 지형·건물 합성 뒤에 그린다)"""
    for f in FLOORS:
        LABEL_POLYS.append(("바닥 글:" + f["name"], f["poly"]))


# ───────────────────────── 4 지붕의 바다·나무(빈 자리만) ─────────────────────────






# ───────────────────────── 5 Core 랜드마크 ─────────────────────────
def _hull(pts):
    pts = sorted(set((round(p[0], 3), round(p[1], 3)) for p in pts))
    if len(pts) < 3:
        return pts

    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def add_fp(name, poly, kind=""):
    """지면 다각형(사후 검사: 지시선 대상·길 접촉)"""
    if poly:
        DRAWN["footprints"].append({"name": name, "kind": kind, "poly": [[round(x, 2), round(y, 2)] for x, y in poly]})
        GEO["fp_" + name] = [tuple(p) for p in poly]








def cyl_quad(iso, cx, cy, r, t0, t1, z0, z1):
    a, b = math.radians(t0), math.radians(t1)
    return [iso.p(cx + r * math.cos(a), cy + r * math.sin(a), z0), iso.p(cx + r * math.cos(b), cy + r * math.sin(b), z0),
            iso.p(cx + r * math.cos(b), cy + r * math.sin(b), z1), iso.p(cx + r * math.cos(a), cy + r * math.sin(a), z1)]


def cyl_arch(iso, cx, cy, r, tc, half_deg, z0, z1, fill):
    hz = r * math.radians(half_deg)
    tz = [(tc - half_deg, z0), (tc + half_deg, z0), (tc + half_deg, z1)]
    for i in range(1, 8):
        s = 1 - 2 * i / 8.0
        tz.append((tc + half_deg * s, z1 + hz * math.sqrt(max(0.0, 1 - s * s))))
    tz.append((tc - half_deg, z1))
    P.poly([iso.p(cx + r * math.cos(math.radians(t)), cy + r * math.sin(math.radians(t)), z) for t, z in tz], fill=fill)


def draw_caracalla():
    L3 = LM["L3"]
    box = L3["projected_box"]
    WX, WY, WH = 72.0, 57.3, 32.0
    key = [(0, 0, -1.4), (WX, 0, -1.4), (WX, WY, -1.4), (0, WY, -1.4), (2, 2, WH), (WX - 2, 2, WH), (2, WY - 2, WH), (0, 0, 0)]
    ox, oy, sc, zs, bb = fit_frame(key, box)
    iso = ZIso(P, ox, oy, sc, zs)
    # 1 받침·바닥
    m_box(0, 0, -1.4, WX, WY, 0, (196, 180, 150), top=(226, 214, 188)).draw(iso, lw=0.12)
    iso.poly3([(3, 3, 0.04), (WX - 3, 3, 0.04), (WX - 3, WY - 3, 0.04), (3, WY - 3, 0.04)], fill=(238, 228, 206), ol=(206, 192, 166), lw=0.12)
    for X in range(8, int(WX) - 3, 6):
        iso.line3([(X, 3.2, 0.06), (X, WY - 3.2, 0.06)], (226, 214, 190), 0.1)
    for Y in range(8, int(WY) - 3, 6):
        iso.line3([(3.2, Y, 0.06), (WX - 3.2, Y, 0.06)], (226, 214, 190), 0.1)
    # 2 뒤 벽(안쪽 면이 보임: 겉 벽돌) + 저수조(수도교 지선이 닿는 자리)
    back = Mesh(None)
    back.extend(m_box(2, 2, 0, WX - 2, 5, WH, BRICK, top=BRICK_L))
    back.extend(m_box(2, 5, 0, 5, WY - 2, WH, BRICK, top=BRICK_L))
    back.draw(iso, lw=0.1)
    win = (252, 238, 198)
    for u0 in (8.0, 16.5, 25.0):                                   # 큰 창(빛은 큰 창 중심)
        iso.arch("L", 0, 5.02, 0, u0, u0 + 4.6, 12.5, 21.0, win)
        iso.arch("L", 0, 5.02, 0, u0 + 0.8, u0 + 3.8, 24.0, 27.6, win)
    for u0 in (9.5, 19.5, 29.5, 39.5):
        iso.arch("R", 5.02, 0, 0, u0, u0 + 4.6, 12.5, 21.0, win)
        iso.arch("R", 5.02, 0, 0, u0 + 0.8, u0 + 3.8, 24.0, 27.6, win)
    for u0 in (12.5, 22.5, 32.5, 42.5):                            # 벽감 + 조각상
        iso.arch("R", 5.02, 0, 0, u0, u0 + 3.4, 1.2, 6.8, (150, 96, 72))
    stat = Mesh(None)
    for u0 in (12.5, 22.5, 32.5, 42.5):
        stat.extend(m_person(6.0, u0 + 1.7, 1.0, 4.4, (238, 234, 224), skin=(238, 234, 224), key="조각상%d" % u0))
    stat.draw(iso, lw=0.10)
    iso.line3([(5.05, 4.0, 11.0), (5.05, WY - 2.5, 11.0)], (226, 160, 128), 0.35)
    iso.line3([(4.0, 5.05, 11.0), (WX - 2.5, 5.05, 11.0)], (226, 160, 128), 0.35)
    for (wx0, wy0, wx1, wy1) in ((10.0, 5.2, 13.6, 30.0), (19.0, 5.2, 22.6, 30.0), (5.2, 12.0, 30.0, 15.6), (5.2, 22.0, 30.0, 25.6)):
        soft(P, [iso.p(wx0, wy0, 20.0), iso.p(wx1, wy0, 20.0), iso.p(wx1, wy1, 0.1), iso.p(wx0, wy1, 0.1)], (255, 246, 214), alpha=46, blur=0.8)
    m_box(WX - 10.0, 5.2, 0, WX - 3.0, 12.0, 26.5, (182, 112, 84), top=(118, 172, 210)).draw(iso, lw=0.1)
    # 3 칼다리움(열탕실): 앞 반쪽을 절개, 드럼 벽(겉 벽돌·속 콘크리트) + 돔(아래 콘크리트·위 경석) 단면
    Xc, Yc = 46.0, 26.0
    Ro, Ri, Hd = 15.5, 12.8, 19.0
    Rdo, Rdi = 15.5, 13.4
    a0, a1 = 135.0, 315.0
    faces = []
    t = a0
    while t < a1 - 1e-6:
        t1 = min(a1, t + 6.0)
        tm = math.radians((t + t1) / 2.0)
        n = (-math.cos(tm), -math.sin(tm), 0.0)
        faces.append((math.cos(tm) + math.sin(tm), t, t1, lit((232, 220, 198), n)))
        t = t1
    for _, ta, tb, col in sorted(faces):
        P.poly(cyl_quad(iso, Xc, Yc, Ri, ta, tb, 3.0, Hd), fill=col)
    for tc in (190.0, 225.0, 260.0):
        cyl_arch(iso, Xc, Yc, Ri - 0.05, tc, 5.0, 8.5, 14.0, win)
    dome = m_dome(Xc, Yc, Hd, Rdo, (198, 184, 160), n=30, rings=7, oculus=0.12, arc=(math.radians(a0), math.radians(a1)),
                  inner=(230, 218, 196), thick=Rdo - Rdi)
    dome.draw(iso, lw=0.10)
    for ph in (0.18, 0.36, 0.54):                                    # 얕은 코퍼(판테온보다 얕게 — 복원 추정)
        for i in range(8):
            th = 150 + i * 21.0
            q = []
            for (dt, dp) in ((-5.5, -0.06), (5.5, -0.06), (5.5, 0.06), (-5.5, 0.06)):
                tt = math.radians(th + dt)
                pp = (ph + dp) * math.pi / 2.0
                q.append((Xc + (Rdi - 0.1) * math.cos(pp) * math.cos(tt), Yc + (Rdi - 0.1) * math.cos(pp) * math.sin(tt), Hd + (Rdi - 0.1) * math.sin(pp)))
            iso.poly3(q, fill=(216, 202, 178))
    half = [(Xc + Ri * math.cos(math.radians(tt)), Yc + Ri * math.sin(math.radians(tt)), 3.0) for tt in range(135, 316, 9)]
    iso.poly3(half, fill=(236, 226, 206), ol=(206, 190, 164), lw=0.1)
    iso.poly3([(Xc - 6.5, Yc - 2.0, 3.05), (Xc + 1.0, Yc - 9.5, 3.05), (Xc + 4.0, Yc - 6.5, 3.05), (Xc - 3.5, Yc + 1.0, 3.05)], fill=(112, 182, 216), ol=(80, 140, 180), lw=0.15)
    for (dx, dy, zz) in ((-2.0, -4.0, 6.0), (1.0, -6.5, 8.0), (-3.5, -1.5, 9.5)):
        cx_, cy_ = iso.p(Xc + dx, Yc + dy, zz)
        soft_ell(P, cx_, cy_, 3.4, 2.0, (255, 255, 255), alpha=38, blur=0.8)
    bath = Mesh(None)
    bath.extend(m_bather(Xc - 2.5, Yc - 4.5, 3.0, H_PERSON, CLOTHS[1], key="열탕1"))
    bath.extend(m_person(Xc - 7.5, Yc - 7.0, 3.0, H_PERSON, CLOTHS[5], key="열탕2"))
    bath.draw(iso, lw=0.10)

    def sec(r, th, z):
        tt = math.radians(th)
        return iso.p(Xc + r * math.cos(tt), Yc + r * math.sin(tt), z)
    for th in (a0, a1):                                               # 단면(절개면은 보는 사람을 향한다)
        P.poly([sec(Ri, th, 0), sec(Ro - 0.9, th, 0), sec(Ro - 0.9, th, Hd), sec(Ri, th, Hd)], fill=CONC2, outline=(96, 90, 80), lw=0.12)
        P.poly([sec(Ro - 0.9, th, 0), sec(Ro, th, 0), sec(Ro, th, Hd), sec(Ro - 0.9, th, Hd)], fill=BRICK)
        rngs = local_rng("드럼단면%d" % th)
        for i in range(7):
            rr = Ri + 0.4 + rngs.random() * (Ro - Ri - 1.6)
            zz = 1.0 + rngs.random() * (Hd - 2.0)
            q = sec(rr, th, zz)
            P.ell(q[0], q[1], 0.42, 0.3, fill=(120, 106, 90) if i % 3 else (250, 248, 240))
        steps = 8
        for j in range(steps):
            p0_ = (math.pi / 2.0) * 0.98 * j / steps
            p1_ = (math.pi / 2.0) * 0.98 * (j + 1) / steps
            col = CONC2 if (p0_ + p1_) / 2.0 < math.radians(46) else PUMICE
            tt = math.radians(th)
            q = [iso.p(Xc + Rdo * math.cos(pp) * math.cos(tt), Yc + Rdo * math.cos(pp) * math.sin(tt), Hd + Rdo * math.sin(pp)) for pp in (p0_, p1_)]
            q += [iso.p(Xc + Rdi * math.cos(pp) * math.cos(tt), Yc + Rdi * math.cos(pp) * math.sin(tt), Hd + Rdi * math.sin(pp)) for pp in (p1_, p0_)]
            P.poly(q, fill=col, outline=shade(col, 0.8), lw=0.10)
            if col == PUMICE:
                for k_ in range(3):
                    f_ = (k_ + 0.5) / 3.0
                    pp = p0_ + (p1_ - p0_) * f_
                    rr = (Rdo + Rdi) / 2.0
                    qq = iso.p(Xc + rr * math.cos(pp) * math.cos(tt), Yc + rr * math.cos(pp) * math.sin(tt), Hd + rr * math.sin(pp))
                    P.ell(qq[0], qq[1], 0.28, 0.22, fill=(176, 166, 140))
    # 하이포코스트: 절개면 아래 바닥 띠(받침 기둥 사이로 뜨거운 공기)
    for k_ in range(-8, 9):
        s0, s1 = k_ * 1.5 - 0.35, k_ * 1.5 + 0.35
        if abs(s0) > Ri - 0.6:
            continue
        pa = (Xc + s0 / math.sqrt(2), Yc - s0 / math.sqrt(2))
        pb = (Xc + s1 / math.sqrt(2), Yc - s1 / math.sqrt(2))
        P.poly([iso.p(pa[0], pa[1], 0), iso.p(pb[0], pb[1], 0), iso.p(pb[0], pb[1], 2.2), iso.p(pa[0], pa[1], 2.2)], fill=(80, 46, 34))
    sL = (Xc - (Ri - 0.3) / math.sqrt(2), Yc + (Ri - 0.3) / math.sqrt(2))
    sR = (Xc + (Ri - 0.3) / math.sqrt(2), Yc - (Ri - 0.3) / math.sqrt(2))
    P.poly([iso.p(sL[0], sL[1], 2.2), iso.p(sR[0], sR[1], 2.2), iso.p(sR[0], sR[1], 3.0), iso.p(sL[0], sL[1], 3.0)], fill=(198, 170, 140), outline=(120, 96, 72), lw=0.1)
    fx_, fy_ = iso.p(Xc + 7.0, Yc - 7.0, 1.0)
    soft_ell(P, fx_, fy_, 6.0, 1.6, (255, 150, 70), alpha=70, blur=0.6)
    # 화로(프라이푸르니움) + 불 때는 일꾼
    m_box(55.5, 13.0, 0, 60.0, 16.5, 4.6, BRICK, top=BRICK_L).draw(iso, lw=0.10)
    iso.arch("L", 0, 16.52, 0, 56.6, 58.9, 0.2, 2.4, (70, 40, 26))
    fcx, fcy = iso.p(57.75, 16.6, 1.4)
    P.ell(fcx, fcy, 0.9, 0.7, fill=(240, 140, 50))
    work = Mesh(None)
    work.extend(m_person(61.6, 18.6, 0, H_PERSON, CLOTHS[0], key="화로꾼"))
    for i in range(4):
        work.extend(m_box(63.4 + i * 0.2, 16.0 + i * 0.9, 0, 66.0, 16.7 + i * 0.9, 0.7 + 0.1 * i, WOOD, top=WOOD_L))
    work.draw(iso, lw=0.10)
    # 4 냉탕실 열주 + 수영장(나타티오) + 목욕객
    iso.poly3([(7.0, 41.0, 0.06), (31.0, 41.0, 0.06), (31.0, 53.0, 0.06), (7.0, 53.0, 0.06)], fill=(214, 204, 184), ol=(176, 160, 132), lw=0.15)
    pool = [iso.p(8.0, 42.0, 0.1), iso.p(30.0, 42.0, 0.1), iso.p(30.0, 52.0, 0.1), iso.p(8.0, 52.0, 0.1)]
    P.poly(pool, fill=(124, 186, 214))
    facet_fill(P, pool, (124, 186, 214), cell=3.0, amp=0.06, key="냉탕", jit=0.12)
    cols = Mesh(None)
    for X in (8.5, 13.4, 18.3, 23.2, 28.1):
        cols.extend(m_cyl(X, 38.5, 1.0, 0, 15.0, (240, 232, 214), n=10))
        cols.extend(m_box(X - 1.3, 37.2, 15.0, X + 1.3, 39.8, 15.8, (232, 222, 200)))
    cols.extend(m_box(6.5, 37.4, 15.8, 30.0, 39.6, 17.6, (230, 220, 198)))
    for (X, Y, c) in ((13.5, 46.5, 2), (19.5, 48.5, 3), (25.0, 45.5, 4)):
        cols.extend(m_bather(X, Y, 0.1, H_PERSON, CLOTHS[c], key="냉탕%d" % c))
    for (X, Y, c) in ((35.5, 44.0, 1), (40.0, 49.5, 5), (14.0, 33.0, 3), (34.0, 31.0, 0)):
        cols.extend(m_person(X, Y, 0.04, H_PERSON, CLOTHS[c], key="욕장사람%d" % c))
    cols.extend(m_box(33.0, 50.0, 0, 35.0, 52.0, 2.2, (226, 216, 196)))
    cols.extend(m_person(34.0, 51.0, 2.2, 4.6, (238, 234, 224), skin=(238, 234, 224), key="조각상앞"))
    cols.draw(iso, lw=0.10)
    # 5 앞쪽 낮은 절개 벽(단면이 보이게)
    fr = Mesh(None)
    fr.extend(m_box(5.0, WY - 3.0, 0, WX - 3.0, WY - 1.0, 5.4, BRICK, top=(176, 122, 96)))
    fr.extend(m_box(WX - 3.0, 14.0, 0, WX - 1.0, WY - 3.0, 5.4, BRICK, top=(176, 122, 96)))
    fr.draw(iso, lw=0.1)
    for k_ in range(10):
        u = 7.0 + k_ * 6.0
        iso.line3([(u, WY - 3.0, 5.42), (u + 1.6, WY - 1.0, 5.42)], (140, 92, 70), 0.14)
    for k_ in range(7):
        v = 16.0 + k_ * 5.8
        iso.line3([(WX - 3.0, v, 5.42), (WX - 1.0, v + 1.6, 5.42)], (140, 92, 70), 0.14)
    GEO["bath_iso"] = iso
    GEO["bath_label_tgt"] = iso.p(3.5, WY - 9.0, WH)
    GEO["bath_box"] = bb
    add_fp("욕장 지면", _hull([iso.p(X, Y, Z) for X in (0, WX) for Y in (0, WY) for Z in (-1.4, 0)]), "지면")
    add_fp("욕장 왼쪽 벽 윗면", [iso.p(2, 5, WH), iso.p(5, 5, WH), iso.p(5, WY - 2, WH), iso.p(2, WY - 2, WH)], "대상 면")
    record("L3", L3["name"], "Core(표준 랜드마크)", box, bb)


def arch_outline(u0, u1, zs, n=10):
    """정면 아치 개구부 윤곽(면 좌표 u·z): 아래 변 z 0 → 기둥 → 반원(반지름 (u1−u0)/2, 기점 zs)"""
    r = (u1 - u0) / 2.0
    cu = (u0 + u1) / 2.0
    pts = [(u0, 0.0), (u1, 0.0), (u1, zs)]
    for i in range(1, n):
        a = math.pi * i / n
        pts.append((cu + r * math.cos(a), zs + r * math.sin(a)))
    pts.append((u0, zs))
    return pts


def draw_aqueduct():
    """수도교 아치 열(관통 아치, d4 결정 9): 높이 26·교각 간격 8 유지. 아래층 개구 폭 5.3, 위층 3.9.
    벽 두께를 화면에서 아치 안쪽 면(왼쪽 교각 옆면)이 1.5mm 보이게 정하고, 앞·뒤 개구가 겹치는 곳은 뚫어 뒤 지면이 보이게 한다."""
    L4 = LM["L4"]
    aq = CM["aqueduct"]
    (x0s, y0s), (x1s, y1s) = aq["ground_line_screen"]
    X0, Y0 = to_plan(x0s, y0s)
    X1, _Y1 = to_plan(x1s, y1s)
    H = aq["arch_height_mm"]
    pitch = float(sget(aq, "pier_pitch_mm", "pitch_mm", default=8.0))
    w_lo = float(sget(aq, "opening_lower_mm", "lower_opening_mm", default=5.3))
    w_hi = float(sget(aq, "opening_upper_mm", "upper_opening_mm", default=3.9))
    jamb = float(sget(aq, "inner_face_mm", "jamb_mm", default=1.5))
    T2 = jamb / C30                  # 벽 두께(평면): 화면 안쪽 면 폭 = C30 × T2 = 1.5mm
    T = T2 / 2.0
    stone = (206, 158, 106)          # 지면보다 채도를 높인 석재 아치
    brick = (190, 104, 72)           # 위 단(수로를 받치는 단)은 벽돌면
    Xe = X1 + 10.0
    yf, yk = Y0 + T, Y0 - T          # 앞면(+Y, 보이는 면)·뒷면
    pts_bb = [sp(X0, yk - 0.4, H), sp(X0, yf + 0.4, 0), sp(Xe, yf + 0.4, 0), sp(Xe, yk - 0.4, H)]
    bb0 = bbox_of(pts_bb)
    sub = Layer(bb0[0] - 2, bb0[1] - 2, bb0[2] + 2, bb0[3] + 2)
    isub = Iso(sub, 0.0, 0.0)
    m = Mesh(None)
    m.extend(m_box(X0, yk, 0, Xe, yf, H - 3.2, stone, top=(222, 182, 132)))
    m.extend(m_box(X0 - 0.3, yk - 0.4, H - 3.2, Xe, yf + 0.4, H, brick, top=(206, 126, 92)))
    m.draw(isub, lw=0.12)
    face_n = lit(stone, (0.0, 1.0, 0.0))
    in_col = lit(shade(stone, 0.78), (1.0, 0.0, 0.0))                 # 왼쪽 교각 옆면(+X향, 그늘)
    soffit = shade(stone, 0.62)                                        # 아치 안쪽 윗면(그늘)
    floor_c = lit((196, 178, 140), (0.0, 0.0, 1.0))
    cut = Image.new("L", (sub.w, sub.h), 0)
    cd = ImageDraw.Draw(cut)
    n_open = [0, 0]
    # 21:55 사용자: 퐁 뒤 가르처럼 3단 아치 — 아래 두 단은 큰 아치(강 위), 맨 위 단은 작은 아치 열. 가운데 큰 아치는 아니에네강 물 위
    an = next((r for r in (RV.get("water_rects") or []) if r["id"] == "aniene"), None)
    wx0, wx1 = (an["plan_X"] if an else (-1.0, -1.0))
    Xc = 0.5 * (wx0 + wx1) if an else 0.5 * (X0 + Xe)
    top_h = 3.0
    TIERS = [(0.0, H * 0.38, 10.5, 14.5), (H * 0.38, H * 0.70, 10.5, 14.5), (H * 0.70, H - top_h, 3.6, 4.84)]
    for ti, (z_b, z_t, w, pitch_t) in enumerate(TIERS):
        kmax = int((Xe - X0) / pitch_t) + 2
        for k in range(-kmax, kmax + 1):
            cx_ = Xc + k * pitch_t
            ua, ub = cx_ - w / 2.0, cx_ + w / 2.0
            if ua < X0 + 0.8 or ub > Xe - 0.8:
                continue
            zs = (z_t - z_b) - w / 2.0 - 0.9
            ol = [(u, z + z_b) for (u, z) in arch_outline(ua, ub, zs)]
            F = [isub.p(u, yf + 0.01, z) for (u, z) in ol]
            B = [isub.p(u, yk - 0.01, z) for (u, z) in ol]
            sub.poly(F, fill=soffit)
            over_water = (ua < wx1 and ub > wx0) and ti == 0
            if not over_water:
                fl = clip_convex([isub.p(ua, yf, z_b), isub.p(ub, yf, z_b), isub.p(ub, yk, z_b), isub.p(ua, yk, z_b)], F)
                if len(fl) >= 3:
                    sub.poly(fl, fill=floor_c)
            zj = ol[2][1]
            jb = clip_convex([isub.p(ua, yf, z_b), isub.p(ua, yk, z_b), isub.p(ua, yk, zj), isub.p(ua, yf, zj)], F)
            if len(jb) >= 3:
                sub.poly(jb, fill=in_col)
            see = clip_convex(B, F)
            if len(see) >= 3:
                cd.polygon([sub.P(q) for q in see], fill=255)
                n_open[min(ti, 1)] += 1
            sub.line(F + [F[0]], shade(face_n, 0.62), 0.12)
    sub.img.putalpha(ImageChops.subtract(sub.img.getchannel("A"), cut))
    for zb_ in (H * 0.38, H * 0.70):
        isub.line3([(X0, yf + 0.03, zb_), (Xe, yf + 0.03, zb_)], (226, 192, 146), 0.35)   # 층 사이 띠돌
    isub.line3([(X0, Y0 - 0.25, H + 0.05), (Xe, Y0 - 0.25, H + 0.05)], (214, 150, 128), 0.3)    # 수로 안 방수 모르타르(분홍 회반죽)
    isub.line3([(X0, Y0 + 0.2, H + 0.05), (Xe, Y0 + 0.2, H + 0.05)], (96, 160, 206), 0.5)      # 수로 물
    # 물에 비친 아치(반영): 앞 밑선(z 0)을 수면(z −DIO_T)에서 거울로 뒤집어 물 위에만, 연하게
    try:
        import numpy as _np
        arr = _np.array(sub.img)
        h_, w_ = arr.shape[0], arr.shape[1]
        base_y = lambda xm: ISO.p(X0, yf, 0)[1] + (xm - ISO.p(X0, yf, 0)[0]) * T30
        cols = _np.arange(w_)
        xm_ = sub.x0 + cols / KD
        ym_px = (base_y(xm_) + DIO_T - sub.y0) * KD
        rows = _np.arange(h_)[:, None]
        src = (2 * ym_px[None, :] - rows).astype(int)
        valid = (src >= 0) & (src < h_) & (rows > ym_px[None, :])
        srcc = _np.clip(src, 0, h_ - 1)
        refl = arr[srcc, cols[None, :]]
        refl = _np.where(valid[:, :, None], refl, 0)
        al = (refl[:, :, 3].astype(float) * 0.42).astype(_np.uint8)
        tint = _np.array(RIV_C, float)
        rgb = (refl[:, :, :3].astype(float) * 0.55 + tint * 0.45).astype(_np.uint8)
        rl = Image.fromarray(_np.dstack([rgb, al]), "RGBA")
        wm = Image.new("L", (sub.w, sub.h), 0)
        wmd = ImageDraw.Draw(wm)
        for pg in (GEO.get("water_rects") or []):
            wmd.polygon([sub.P((x, y + DIO_T)) for x, y in pg], fill=255)           # 낮춘 수면 위치
        rl.putalpha(ImageChops.multiply(rl.getchannel("A"), wm))
        P.img.alpha_composite(rl, (int(round((sub.x0 - P.x0) * KD)), int(round((sub.y0 - P.y0) * KD))))
    except Exception as e_:                                                # noqa: BLE001
        REPORT["notes"].append("수도교 반영 실패: %s" % e_)
    merge(P, sub)
    pts = [ISO.p(X0, yk - 0.4, H), ISO.p(X0, yf, 0), ISO.p(Xe, yf, 0), ISO.p(Xe, yk, H)]
    bb = bbox_of(pts)
    bb = (bb[0], bb[1], min(bb[2], PW), bb[3] if bb[2] <= PW else (pts[1][1] + (PW - pts[1][0]) * T30))
    GEO["aq_ground"] = lambda x: (pts[1][1] + (x - pts[1][0]) * T30)
    face = [ISO.p(X0, yf, 0), ISO.p(Xe, yf, 0), ISO.p(Xe, yf, H), ISO.p(X0, yf, H)]
    add_fp("수도교 아치 면", face, "대상 면")
    GEO["aqueduct_form"] = {"through_arches": True, "pier_pitch_mm": pitch, "opening_lower_mm": w_lo, "opening_upper_mm": w_hi,
                            "inner_face_screen_mm": round(C30 * T2, 2), "wall_plan_thickness": round(T2, 3), "height_mm": H,
                            "see_through_openings": {"lower": n_open[0], "upper": n_open[1]}}
    record("L4", L4["name"], "Core(표준 랜드마크)", L4["projected_box"], bb, "오른쪽 변 블리드(상자는 x 420에서 자름) · 관통 아치")


def hemi_faces(cx, cy, r_in, r_out, z0, z1, t0, t1, nseg, col_face, col_top):
    m = Mesh(None)
    for i in range(nseg):
        a = math.radians(t0 + (t1 - t0) * i / nseg)
        b = math.radians(t0 + (t1 - t0) * (i + 1) / nseg)
        pai = (cx + r_in * math.cos(a), cy + r_in * math.sin(a))
        pbi = (cx + r_in * math.cos(b), cy + r_in * math.sin(b))
        pao = (cx + r_out * math.cos(a), cy + r_out * math.sin(a))
        pbo = (cx + r_out * math.cos(b), cy + r_out * math.sin(b))
        m.add([(pai[0], pai[1], z0), (pbi[0], pbi[1], z0), (pbi[0], pbi[1], z1), (pai[0], pai[1], z1)], col_face, "two")
        m.add([(pai[0], pai[1], z1), (pao[0], pao[1], z1), (pbo[0], pbo[1], z1), (pbi[0], pbi[1], z1)], col_top, "two")
    for t in (t0, t1):
        a = math.radians(t)
        pi_ = (cx + r_in * math.cos(a), cy + r_in * math.sin(a))
        po_ = (cx + r_out * math.cos(a), cy + r_out * math.sin(a))
        m.add([(pi_[0], pi_[1], z0), (po_[0], po_[1], z0), (po_[0], po_[1], z1), (pi_[0], pi_[1], z1)], col_face, "two")
    return m


def draw_market():
    L2 = LM["L2"]
    box = L2["projected_box"]
    WX, WY = 60.0, 50.85
    hc = (31.0, 34.0)
    base = m_box(0, 0, -1.4, WX, WY, 0, (196, 182, 152), top=(224, 210, 182))
    terr = m_box(0, 0, 0, WX, 19.0, 9.0, (178, 136, 102), top=(214, 194, 160))
    hall = m_box(3.0, 2.0, 9.0, 31.0, 14.0, 27.0, BRICK, top=(214, 192, 164))
    rblk = m_box(36.0, 2.0, 9.0, 57.0, 12.5, 20.0, (186, 112, 84), top=(208, 180, 150))
    s1 = hemi_faces(hc[0], hc[1], 14.0, 21.0, 0.0, 7.0, 135, 315, 11, BRICK, (214, 190, 160))
    s2 = hemi_faces(hc[0], hc[1], 15.6, 21.0, 7.0, 12.4, 135, 315, 11, (186, 104, 76), (212, 188, 158))
    s3 = hemi_faces(hc[0], hc[1], 17.2, 21.0, 12.4, 16.8, 135, 315, 11, (180, 100, 74), (210, 186, 156))
    trees = Mesh(None)
    trees.extend(m_pine(53.5, 44.0, 0, 15.0, 5.4, key="시장소나무"))
    trees.extend(m_cypress(5.5, 46.5, 0, 14.0, 1.8, key="시장사이프러스"))
    trees.extend(m_olive(57.0, 27.0, 0, 7.0, 2.6, key="시장올리브"))
    pts = mesh_pts(base, terr, hall, rblk, s1, s2, s3, trees)
    ox, oy, sc, zs, bb = fit_frame(pts, box, zs_max=1.15)
    iso = ZIso(P, ox, oy, sc, zs)
    base.draw(iso, lw=0.12)
    iso.poly3([(hc[0] + 13.6 * math.cos(math.radians(t)), hc[1] + 13.6 * math.sin(math.radians(t)), 0.03) for t in range(135, 316, 9)],
              fill=(232, 220, 196), ol=(200, 184, 156), lw=0.12)
    m_ter = Mesh(None)
    m_ter.extend(terr)
    m_ter.extend(hall)
    m_ter.extend(rblk)
    m_ter.draw(iso, lw=0.1)
    dark = (98, 62, 46)
    for u0 in [x for x in range(2, 58, 5) if not (13 <= x <= 47)]:
        iso.arch("L", 0, 19.02, 0, u0, u0 + 2.8, 0.4, 5.0, dark)
    for k_ in range(6):                                             # 대회랑 창 2줄
        u0 = 4.4 + k_ * 4.5
        iso.arch("L", 0, 14.02, 9.0, u0, u0 + 2.2, 3.0, 7.0, dark)
        iso.fpoly("L", 0, 14.02, 9.0, [(u0 + 0.3, 10.6), (u0 + 1.9, 10.6), (u0 + 1.9, 13.6), (u0 + 0.3, 13.6)], fill=dark)
    iso.arch("R", 31.02, 0, 9.0, 4.5, 9.5, 0.2, 8.0, dark)
    for k_ in range(4):
        u0 = 37.5 + k_ * 4.8
        iso.arch("L", 0, 12.52, 9.0, u0, u0 + 2.2, 0.3, 4.4, dark)
    for k_ in range(1, 6):                                          # 지붕 칸 줄
        X = 3.0 + k_ * 4.67
        iso.line3([(X, 2.0, 27.02), (X, 14.0, 27.02)], (186, 160, 130), 0.14)
    bx0, bx1 = 3.0 + 3 * 4.67, 3.0 + 4 * 4.67                       # 지붕 한 칸을 걷어 교차 볼트를 보인다
    iso.poly3([(bx0 + 0.3, 2.4, 27.04), (bx1 - 0.3, 2.4, 27.04), (bx1 - 0.3, 13.6, 27.04), (bx0 + 0.3, 13.6, 27.04)], fill=(110, 76, 56))
    for (pa, pb) in (((bx0 + 0.3, 2.4), (bx1 - 0.3, 13.6)), ((bx1 - 0.3, 2.4), (bx0 + 0.3, 13.6))):
        q = []
        for i in range(9):
            f = i / 8.0
            X = pa[0] + (pb[0] - pa[0]) * f
            Y = pa[1] + (pb[1] - pa[1]) * f
            q.append((X, Y, 24.5 + 2.4 * math.sin(math.pi * f)))
        iso.line3(q, (236, 214, 180), 0.32)
    for Yb in (2.4, 13.6):
        q = [(bx0 + 0.3 + (bx1 - bx0 - 0.6) * i / 8.0, Yb, 24.5 + 2.4 * math.sin(math.pi * i / 8.0)) for i in range(9)]
        iso.line3(q, (226, 200, 168), 0.22)
    # 숫자 짝 3: 걷은 지붕 칸(교차 볼트) 바로 옆 지붕 윗면(표지가 볼트 갈빗대를 가리지 않게 칸 가장자리에 붙인다)
    GEO["snap_market_vault"] = [iso.p(bx1 + 2.7, 8.0, 27.04), iso.p(bx0 - 2.7, 8.0, 27.04)]
    GEO["snap_market_vault_any"] = True
    s1.draw(iso, lw=0.10)
    s2.draw(iso, lw=0.10)
    s3.draw(iso, lw=0.10)
    for i in range(11):                                              # 1층 상점 문(아치), 2층 창, 3층 네모 창
        tc = 135 + (i + 0.5) * 180.0 / 11
        cyl_arch(iso, hc[0], hc[1], 13.95, tc, 4.2, 0.4, 3.8, dark)
        cyl_arch(iso, hc[0], hc[1], 15.55, tc, 3.0, 8.2, 10.4, dark)
        a_ = math.radians(tc - 2.4)
        b_ = math.radians(tc + 2.4)
        r_ = 17.15
        P.poly([iso.p(hc[0] + r_ * math.cos(a_), hc[1] + r_ * math.sin(a_), 13.6), iso.p(hc[0] + r_ * math.cos(b_), hc[1] + r_ * math.sin(b_), 13.6),
                iso.p(hc[0] + r_ * math.cos(b_), hc[1] + r_ * math.sin(b_), 15.6), iso.p(hc[0] + r_ * math.cos(a_), hc[1] + r_ * math.sin(a_), 15.6)], fill=dark)
    ppl = Mesh(None)
    for (X, Y, c) in ((26.0, 38.0, 0), (33.0, 42.0, 2), (38.0, 33.0, 4), (22.0, 30.0, 1), (44.0, 44.0, 3)):
        ppl.extend(m_person(X, Y, 0.03, H_PERSON / max(sc * zs, 0.6), CLOTHS[c], key="시장사람%d" % c))
    ppl.extend(trees)
    ppl.draw(iso, lw=0.10)
    GEO["market_tgt"] = iso.p(57.0, 7.0, 14.5)
    add_fp("시장 지면", _hull([iso.p(X, Y, Z) for X in (0, WX) for Y in (0, WY) for Z in (-1.4, 0)]), "지면")
    add_fp("시장 오른쪽 동 끝면", [iso.p(57.0, 2.0, 9.0), iso.p(57.0, 12.5, 9.0), iso.p(57.0, 12.5, 20.0), iso.p(57.0, 2.0, 20.0)], "대상 면")
    record("L2", L2["name"], "Core(표준 랜드마크)", box, bb, "높이 과장 %.2f배" % zs)


def _rot90_mesh(m):
    """메시를 국소 (x, y, z) → (y, −x, z)로 90° 돌린다(방향 보존). 면 법선·보이는 면 판정을 다시 하므로 점을 직접 옮긴다."""
    c = m.center
    n = Mesh(None if c is None else (c[1], -c[0], c[2]))
    for pts, col, orient, flat, edge, jit in m.faces:
        n.faces.append(([(q[1], -q[0], q[2]) for q in pts], col, orient, flat, edge, jit))
    return n


# 아크로폴리스 파르테논 폐허 (draw_pantheon 대체). render.py 의 'def draw_pantheon():' ~ 'def draw_metella():' 직전까지를 이 파일 내용으로 교체.
# 모든 좌표는 평면(plan) X·Y: 정면(기둥 8개 짧은 변)은 +X, 긴 변(17개)은 ±Y. 회전 없음.
def _acr_rnd(i, j=0):
    v = math.sin(i * 127.1 + j * 311.7 + 17.3) * 43758.5453
    return v - math.floor(v)


def draw_pantheon():
    L1 = LM["L1"]
    box = L1["projected_box"]
    X0, Y0 = 34.75, 15.45                 # 열주 중심 사각 (기둥 중심선: 가로 69.5 m × 세로 30.9 m)
    NX, NY = 17, 8                        # 긴 변 17, 짧은 변 8 (모서리 공유)
    ZB = 1.7                              # 스타일로베이트 윗면
    CH, EH = 10.4, 3.3                    # 기둥 높이, 엔타블러처 높이
    MAR = (226, 212, 182)                 # 대리석 베이지
    MAR_L = (240, 230, 206)
    ARCH = (214, 198, 166)
    FRIEZE = (234, 222, 194)
    ROCK = [(196, 164, 112), (214, 184, 132), (186, 154, 104), (206, 174, 122), (192, 160, 108), (220, 190, 140), (200, 168, 116)]
    # ── 바위 언덕: 위로 갈수록 조금씩 안쪽으로 들어간 직사각 슬랩을 쌓는다(층 줄무늬 + 들쭉날쭉한 절벽). 윗면은 평평한 대지.
    rock = Mesh(None)
    PX0, PX1, PY0, PY1 = -46.0, 40.0, -25.0, 19.8
    WALL_H = 36.0                         # 22:22 사용자: 아크로폴리스 = 마름돌 성벽이 수직 절벽처럼 솟은 높은 블록(레퍼런스 user_acropolis_hill.jpg)
    rock.extend(m_box(PX0, PY0, -WALL_H, PX1, PY1, -0.9, (200, 176, 134), top=(206, 178, 128)))
    rock.extend(m_box(PX0, PY0, -0.9, PX1, PY1, 0.0, (214, 196, 152), top=(222, 208, 172)))
    # 앞 가장자리 바위 덩이(축 정렬 작은 직사각 기둥)
    for i, (bx, by, w, d, h) in enumerate(((38.0, 17.0, 6.0, 5.0, 2.0), (28.0, 20.5, 7.0, 3.5, 1.4), (-30.0, 20.0, 8.0, 3.5, 1.6), (40.5, -6.0, 3.5, 7.0, 1.6), (-40.0, 8.0, 3.5, 7.0, 1.3))):
        rock.extend(m_box(bx - w / 2, by - d / 2, 0, bx + w / 2, by + d / 2, h, (190, 158, 110), top=(210, 186, 140)))
    # ── 스타일로베이트 3단
    st = Mesh(None)
    for k, (m_, z0_, z1_) in enumerate(((2.8, 0.0, 0.6), (1.9, 0.6, 1.15), (1.0, 1.15, ZB))):
        st.extend(m_box(-X0 - m_, -Y0 - m_, z0_, X0 + m_, Y0 + m_, z1_, (228, 216, 188) if k != 1 else (222, 208, 178), top=(236, 226, 200)))
    # ── 기둥·엔타블러처·셀라 벽
    rn = Mesh(None)
    cols = []
    for i in range(NX):
        for (y, side) in ((-Y0, "S"), (Y0, "N")):
            cols.append((-X0 + i * 2 * X0 / (NX - 1), y, ("L", i)))
    for j in range(1, NY - 1):
        for (x, side) in ((-X0, "W"), (X0, "E")):
            cols.append((x, -Y0 + j * 2 * Y0 / (NY - 1), ("E" if x > 0 else "W", j)))
    broken = {("L", 7, +1): 5.2, ("L", 8, +1): 3.4, ("L", 9, +1): 6.5, ("L", 6, +1): 8.0, ("L", 10, +1): 4.4,
              ("L", 3, -1): 7.2, ("L", 12, -1): 6.0, ("L", 13, -1): 8.4, ("L", 1, +1): 9.0, ("L", 0, -1): 9.6,
              ("W", 2, 0): 6.4, ("W", 4, 0): 4.6, ("W", 5, 0): 8.2, ("E", 3, 0): 9.4}
    for (x, y, kk) in cols:
        sgn = 0 if kk[0] in ("E", "W") else (1 if y > 0 else -1)
        h = broken.get((kk[0], kk[1], sgn), CH)
        if kk[0] == "L" and kk[1] in (6, 7, 8, 9, 10) and y > 0 and h == CH:
            h = 6.0
        r = 0.95
        rn.extend(m_cyl(x, y, r, ZB, ZB + h, MAR, n=8, top=(214, 200, 170) if h < CH else MAR_L))
        if h >= CH:
            rn.extend(m_cyl(x, y, r, ZB + h, ZB + h + 0.55, MAR_L, n=8, k=1.22))
            rn.extend(m_box(x - 1.3, y - 1.3, ZB + h + 0.55, x + 1.3, y + 1.3, ZB + h + 1.0, MAR_L))
    zt = ZB + CH + 1.0
    # 엔타블러처: 기둥 사이 칸마다 한 덩이. 윗변이 들쭉날쭉(높이 다름), 일부 칸은 없다.
    def bay(xa, ya, xb, yb, key, along):
        r_ = _acr_rnd(*key)
        if along == "N" and 6 <= key[0] <= 9:
            return                                                   # 폭발로 날아간 가운데 칸(앞 긴 변)
        if along == "S" and 5 <= key[0] <= 11:
            return
        if along == "W" and key[0] in (2, 3, 4, 5):
            return
        eh = EH * (0.55 + 0.45 * r_) if r_ < 0.55 else EH
        w = 1.15
        if along in ("N", "S"):
            b1 = m_box(xa, ya - w, zt, xb, ya + w, zt + 1.5, ARCH)
            rn.extend(b1)
            if eh > 1.7:
                rn.extend(m_box(xa, ya - w + 0.1, zt + 1.5, xb, ya + w - 0.1, zt + eh, FRIEZE, top=MAR_L))
        else:
            b1 = m_box(xa - w, ya, zt, xa + w, yb, zt + 1.5, ARCH)
            rn.extend(b1)
            if eh > 1.7:
                rn.extend(m_box(xa - w + 0.1, ya, zt + 1.5, xa + w - 0.1, yb, zt + eh, FRIEZE, top=MAR_L))
    xs = [-X0 + i * 2 * X0 / (NX - 1) for i in range(NX)]
    ys = [-Y0 + j * 2 * Y0 / (NY - 1) for j in range(NY)]
    for i in range(NX - 1):
        bay(xs[i], Y0, xs[i + 1], Y0, (i, 1), "N")
        bay(xs[i], -Y0, xs[i + 1], -Y0, (i, 2), "S")
    for j in range(NY - 1):
        bay(X0, ys[j], X0, ys[j + 1], (j, 3), "E") if j != 99 else None
        bay(-X0, ys[j], -X0, ys[j + 1], (j, 4), "W")
    # 셀라(안쪽 신전 벽): 구간마다 높이가 다른 낮은 벽 토막
    cx0, cx1, cy0, cy1, th = -22.0, 22.0, -9.4, 9.4, 1.25
    seg = 6
    for s in range(seg):
        xa = cx0 + (cx1 - cx0) * s / seg
        xb = cx0 + (cx1 - cx0) * (s + 1) / seg
        hN = 3.0 + 7.0 * _acr_rnd(s, 9)
        hS = 4.0 + 6.0 * _acr_rnd(s, 5)
        if 2 <= s <= 3:
            hN = 1.4 + _acr_rnd(s, 2) * 1.4
        rn.extend(m_box(xa, cy1 - th, ZB, xb, cy1, ZB + hN, MAR, top=MAR_L))
        rn.extend(m_box(xa, cy0, ZB, xb, cy0 + th, ZB + hS, MAR, top=MAR_L))
    for t_ in range(4):
        ya = cy0 + (cy1 - cy0) * t_ / 4
        yb = cy0 + (cy1 - cy0) * (t_ + 1) / 4
        rn.extend(m_box(cx1 - th, ya, ZB, cx1, yb, ZB + 2.0 + 6.5 * _acr_rnd(t_, 3), MAR, top=MAR_L))
        rn.extend(m_box(cx0, ya, ZB, cx0 + th, yb, ZB + 3.0 + 7.0 * _acr_rnd(t_, 8), MAR, top=MAR_L))
    rn.extend(m_box(cx0 + 12, cy0 + 1.25, ZB, cx0 + 14, cy0 + 3.0, ZB + 2.2, MAR_L))
    # 정면 앞 흩어진 돌 조각
    rub = Mesh(None)
    for i, (bx, by, w, d, h) in enumerate(((40.0, -9.0, 2.6, 1.8, 1.0), (41.5, 4.0, 2.2, 2.6, 0.9), (38.8, 11.0, 2.8, 1.6, 0.7), (36.0, -13.5, 1.8, 1.8, 0.8), (-39.5, -3.0, 2.4, 2.0, 0.8), (-37.0, 12.0, 2.0, 2.6, 0.7))):
        rub.extend(m_box(bx - w / 2, by - d / 2, 0, bx + w / 2, by + d / 2, h, (226, 212, 184), top=(240, 230, 206)))
    for (x, y) in ((24.0, 19.5), (2.0, 19.8)):
        rub.extend(m_cyl(x, y, 1.0, 0, 2.0, MAR, n=8, top=MAR_L))
    pts = mesh_pts(rock, st, rn, rub)
    ox, oy, sc, zs, bb = fit_frame(pts, box, zs_max=1.22)
    iso = ZIso(P, ox, oy, sc, zs)
    ip = iso.p
    rock.draw(iso, lw=0.12)
    # 마름돌 줄눈: 켜 높이 3.0, 돌 폭 8, 켜마다 반 칸 어긋남(+Y 앞면·+X 오른쪽 면)
    JC = (150, 120, 84)
    ncourse = int(WALL_H / 3.0)
    for kc in range(ncourse + 1):
        zc = -WALL_H + kc * (WALL_H - 0.9) / ncourse
        iso.line3([(PX0, PY1 + 0.02, zc), (PX1, PY1 + 0.02, zc)], JC, 0.2)
        iso.line3([(PX1 + 0.02, PY0, zc), (PX1 + 0.02, PY1, zc)], JC, 0.2)
    for kc in range(ncourse):
        z0c = -WALL_H + kc * (WALL_H - 0.9) / ncourse
        z1c = -WALL_H + (kc + 1) * (WALL_H - 0.9) / ncourse
        off = 0.0 if kc % 2 == 0 else 4.0
        xj = PX0 + off
        while xj < PX1:
            if xj > PX0 + 0.5:
                iso.line3([(xj, PY1 + 0.02, z0c), (xj, PY1 + 0.02, z1c)], JC, 0.18)
            xj += 8.0 + 1.5 * (_acr_rnd(kc, int(xj)) - 0.5)
        yj = PY0 + off
        while yj < PY1:
            if yj > PY0 + 0.5:
                iso.line3([(PX1 + 0.02, yj, z0c), (PX1 + 0.02, yj, z1c)], JC, 0.18)
            yj += 8.0 + 1.5 * (_acr_rnd(kc, int(yj) + 99) - 0.5)
    st.draw(iso, lw=0.10)
    rn.draw(iso, lw=0.10)
    rub.draw(iso, lw=0.10)
    # 엔타블러처 정면(+X) 면: 지시선 대상
    ent = [ip(X0, -Y0, zt), ip(X0, Y0, zt), ip(X0, Y0, zt + EH), ip(X0, -Y0, zt + EH)]
    ent_pts = [ip(X0 + 0.0, y_, z_) for y_ in (-Y0 * 0.9, Y0 * 0.9) for z_ in (zt + 0.3, zt + EH * 0.6)]
    GEO["pantheon_iso"] = iso
    GEO["lead_tgt_파르테논 엔타블러처"] = ip(X0, 0.0, zt + 1.7)
    GEO["pantheon_dome_ul"] = [ip(X0, y_, zt + z_) for y_ in (-10.0, -5.0, 0.0, 5.0, 10.0) for z_ in (0.6, 1.2, 1.8)]
    GEO["snap_pantheon_dome"] = list(GEO["pantheon_dome_ul"])
    add_fp("아크로폴리스 지면", _hull([ip(X, Y, Z) for X in (PX0, PX1) for Y in (PY0, PY1) for Z in (-0.9, 0)]), "지면")
    add_fp("파르테논 엔타블러처", _hull(ent_pts + ent), "대상 면")
    add_fp("아크로폴리스 암반", _hull([ip(X, Y, Z) for X in (PX0, PX1) for Y in (PY0, PY1) for Z in (-19.0, -0.9)]), "대상 면")
    hullp = _hull([ip(*q) for q in pts])
    GEO["sil_L1"] = hullp
    GEO["parts_L1"] = [hullp]
    record("L1", L1["name"], "Core(표준 랜드마크)", box, bb, "높이 과장 %.2f배" % zs)


def draw_metella():
    L5 = LM["L5"]
    box = metella_box()                                              # d5: 사양 상자 중심 기준 1.04배(결정 D4) — 실제 외곽 4,530mm² 이상
    m = Mesh(None)
    m.extend(m_box(-16, -16, 0, 16, 16, 8.0, TRAV, top=TRAV_L))                        # 네모 기단
    m.extend(m_box(-16.6, -16.6, 7.2, 16.6, 16.6, 8.0, (226, 208, 172)))
    m.extend(m_cyl(0, 0, 14.5, 8.0, 10.6, TUFF, n=32))                                 # 응회암 보강 띠
    m.extend(m_cyl(0, 0, 14.5, 10.6, 26.2, (212, 160, 126), n=32))                    # 원통 드럼(벽돌 겉면, 지름 29 m)
    m.extend(m_cyl(0, 0, 14.75, 26.2, 29.2, (236, 226, 204), n=32))                   # 프리즈(소머리·꽃줄)
    m.extend(m_cyl(0, 0, 14.6, 29.2, 30.6, (220, 200, 168), n=32, top=(150, 162, 104)))
    ppl = Mesh(None)
    ppl.extend(m_person(-12.0, 19.0, 0, H_PERSON, CLOTHS[3], key="메텔라1"))
    ppl.extend(m_person(6.0, 19.5, 0, H_PERSON, CLOTHS[1], key="메텔라2"))
    pts = mesh_pts(m, ppl) + [(-19, -19, 0), (21, -19, 0), (21, 21, 0), (-19, 21, 0)]
    # 나무 4그루. 사이프러스 2는 진입로 R6a·R6b 띠 밖 2mm 이상인 자리로 옮긴다(후보 중 첫 빈 자리).
    tree_specs = [("c", -19.5, -7.0, 26.0, 2.1, "메텔라사이프러스1"), ("c2", -8.0, -20.5, 22.0, 2.0, "메텔라사이프러스2"),
                  ("p", 19.0, -14.0, 17.0, 6.2, "메텔라소나무"), ("c", 19.5, 13.0, 16.0, 1.7, "메텔라사이프러스3")]
    trial = Mesh(None)
    for kd, X, Y, h, r, k in tree_specs:
        trial.extend(m_pine(X, Y, 0, h, r, key=k) if kd == "p" else m_cypress(X, Y, 0, h, r, key=k))
    ox, oy, sc, zs, bb = fit_frame(pts + mesh_pts(trial), box, zs_max=1.25)
    for _k in range(10):                                             # 실제 외곽(x 420 잘림) ≥ 4,530mm²(결정 D4)가 되게 1.04배에서 0.002씩
        a_ = (min(float(PW), bb[2]) - max(0.0, bb[0])) * (bb[3] - bb[1])
        if a_ >= 4535.0 or not _same(list(L5["projected_box"]), [354.0, 288.0, 420.0, 358.0], 0.3):
            break
        METELLA_F[0] += 0.002
        box = metella_box()
        ox, oy, sc, zs, bb = fit_frame(pts + mesh_pts(trial), box, zs_max=1.25)
    iso = ZIso(P, ox, oy, sc, zs)
    r6 = []                                                          # 사용자 16:14: 진입로 길은 없다

    def clear_of_roads(X, Y, r_, h_):
        foot = [iso.p(X + dx, Y + dy, 0) for dx, dy in ((-r_, -r_), (r_, -r_), (r_, r_), (-r_, r_))]
        crown = [iso.p(X, Y, h_)]
        q = _hull(foot + crown + [iso.p(X - r_, Y + r_, h_ * 0.6), iso.p(X + r_, Y - r_, h_ * 0.6)])
        return all(_poly_dist(q, b) >= 2.0 for b in r6)
    trees = Mesh(None)
    moved = None
    for kd, X, Y, h, r, k in tree_specs:
        if kd == "c2" and r6 and not clear_of_roads(X, Y, r, h):
            for (cx_, cy_) in ((-20.0, 9.0), (-19.0, 16.5), (-13.5, -19.0), (-19.5, -15.0), (10.0, 19.5), (19.5, 4.0)):
                if clear_of_roads(cx_, cy_, r, h):
                    moved = (X, Y, cx_, cy_)
                    X, Y = cx_, cy_
                    break
        trees.extend(m_pine(X, Y, 0, h, r, key=k) if kd == "p" else m_cypress(X, Y, 0, h, r, key=k))
    if moved:
        REPORT["notes"].append("메텔라 사이프러스 2: 국소 (%.1f, %.1f) → (%.1f, %.1f)(R6a·R6b 띠 밖 2mm 이상)" % moved)
    iso.poly3([(-19, -19, 0.02), (21, -19, 0.02), (21, 21, 0.02), (-19, 21, 0.02)], fill=(214, 202, 168), ol=(186, 170, 134), lw=0.15)
    back = Mesh(None)
    back.faces = [f for f in trees.faces if (sum(p[0] + p[1] for p in f[0]) / len(f[0])) < -2]
    frontt = Mesh(None)
    frontt.faces = [f for f in trees.faces if (sum(p[0] + p[1] for p in f[0]) / len(f[0])) >= -2]
    back.draw(iso, lw=0.10)
    m.draw(iso, lw=0.10)
    for zc in (13.0, 15.6, 18.2, 20.8, 23.4):                       # 벽돌 줄눈
        iso.line3([(14.55 * math.cos(math.radians(t)), 14.55 * math.sin(math.radians(t)), zc) for t in range(-44, 135, 6)], (188, 136, 104), 0.14)
    for i in range(12):
        a = math.radians(-36 + i * 14.5)
        cx_, cy_ = iso.p(14.8 * math.cos(a), 14.8 * math.sin(a), 27.7)
        P.ell(cx_, cy_, 0.5, 0.42, fill=(172, 156, 126))
    frontt.draw(iso, lw=0.10)
    ppl.draw(iso, lw=0.10)
    foot = [iso.p(-16, -16), iso.p(16, -16), iso.p(16, 16), iso.p(-16, 16)]
    GEO["metella_foot"] = foot
    GEO["metella_drum_l"] = iso.p(-14.5 * 0.7071, 14.5 * 0.7071, 9.0)
    add_fp("메텔라 대지", [iso.p(-19, -19, 0), iso.p(21, -19, 0), iso.p(21, 21, 0), iso.p(-19, 21, 0)], "지면")
    add_fp("메텔라 기단", _hull([iso.p(X, Y, Z) for X in (-16, 16) for Y in (-16, 16) for Z in (0, 8.0)]), "대상 면")
    add_fp("메텔라 드럼", _hull([iso.p(14.5 * math.cos(math.radians(t)), 14.5 * math.sin(math.radians(t)), z)
                              for t in range(0, 360, 10) for z in (10.6, 26.2)]), "대상 면")
    bbc = (max(0.0, bb[0]), bb[1], min(float(PW), bb[2]), bb[3])                  # 지면 오른쪽 변(x 420)에서 잘린 실제 외곽
    record("L5", L5["name"], "Core(표준 랜드마크)", L5["projected_box"], bbc, "높이 과장 %.2f배 · 그림 상자 %.3f배 %s" % (zs, METELLA_F[0], [round(v, 2) for v in box]))


# ───────────────────────── 5b 새 랜드마크(d4 결정 7~10): 바실리카·영묘 + 다리·극장·네로 거상 받침 ─────────────────────────
def _flat_plan(lm):
    """통합 d4: map 사양의 평면 원본(중첩 열쇠)을 렌더 평면 열쇠로 옮긴다.
    L7 paving{rects_plan [X0,X1,Y0,Y1], h}·aisle{X,Y,h,bays}·nave_ruins{X,Y,h_max}·nave_vault_dashed{h_max}
    L8 base{X,Y,h}·drum{c,r,z}·top{parapet,mound}·bridge{deck_X,deck_Y,h,arches} / L9 plan{c,r}·arcade{h,tier_h}·stage_wall{h_max}.
    렌더 열쇠(base_rects…)가 이미 평면 값이면 그대로 둔다."""
    pl = sget(lm, "plan", "plan_geom", "geometry", default=None)
    if not isinstance(pl, dict):
        return {}
    out = {}

    def rect_xy(d):
        return [float(d["X"][0]), float(d["Y"][0]), float(d["X"][1]), float(d["Y"][1])]
    try:
        if isinstance(pl.get("paving"), dict):                                   # L7 막센티우스 바실리카
            pv = pl["paving"]
            out["base_rects"] = [[float(r[0]), float(r[2]), float(r[1]), float(r[3])] for r in pv["rects_plan"]]
            out["base_h"] = float(pv.get("h", 1.5))
            if isinstance(pl.get("aisle"), dict):
                a = pl["aisle"]
                out["aisle"], out["aisle_h"], out["bays"] = rect_xy(a), float(a["h"]), int(a.get("bays", 3))
            if isinstance(pl.get("nave_ruins"), dict):
                n_ = pl["nave_ruins"]
                out["nave"], out["ruin_h"] = rect_xy(n_), float(n_.get("h_max", 4.0))
            if isinstance(pl.get("nave_vault_dashed"), dict):                    # 점선 복원 높이 ≤ h_max(지면 기준) → 포장 위 높이
                out["vault_h"] = max(1.0, float(pl["nave_vault_dashed"].get("h_max", 10.0)) - out["base_h"])
        if isinstance(pl.get("drum"), dict) and isinstance(pl.get("base"), dict):  # L8 하드리아누스 영묘 + 폰스 아일리우스
            b_, d_ = pl["base"], pl["drum"]
            out["base"], out["base_h"] = rect_xy(b_), float(b_.get("h", 5.0))
            out["drum_c"], out["drum_r"] = [float(v) for v in d_["c"]], float(d_["r"])
            out["drum_z"] = [float(v) for v in d_["z"]]
            tp_ = pl.get("top") or {}
            mz = (tp_.get("mound") or {}).get("z_top")
            out["top_z"] = [out["drum_z"][1], float(mz if mz is not None else out["drum_z"][1] + 5.0)]
            mr = (tp_.get("mound") or {}).get("r_max")
            if mr is not None:
                out["mound_r"] = float(mr)
            br_ = pl.get("bridge") or {}
            if br_.get("deck_X") and br_.get("deck_Y"):
                out["bridge"] = [float(br_["deck_X"][0]), float(br_["deck_Y"][0]), float(br_["deck_X"][1]), float(br_["deck_Y"][1])]
                out["bridge_h"] = float(br_.get("h", 3.0))
                out["bridge_arches"] = int(br_.get("arches", 3))
                if br_.get("canal_Y"):
                    out["canal_Y"] = [float(v) for v in br_["canal_Y"]]
        if isinstance(pl.get("plan"), dict) and isinstance(pl.get("arcade"), dict):  # L9 마르켈루스 극장
            p_, ar_ = pl["plan"], pl["arcade"]
            out["center"], out["r"] = [float(v) for v in (p_.get("c") or p_.get("center"))], float(p_["r"])
            out["h"] = float(ar_.get("h", 12.0))
            th_ = ar_.get("tier_h", 6.0)
            out["tier_h"] = float(th_[0] if isinstance(th_, (list, tuple)) else th_)
            out["stage_wall_h"] = float((pl.get("stage_wall") or {}).get("h_max", 4.0))
    except (KeyError, TypeError, ValueError, IndexError) as e_:
        REPORT["notes"].append("평면 원본 변환 실패 %s: %s(결정값 사용)" % (lm.get("id"), e_))
        return {}
    return out


def _lm_plan(lm, key, default):
    """랜드마크 평면 기하: 사양 plan(map 중첩 열쇠는 _flat_plan으로 옮김)에 열쇠가 있으면 사양 값, 없으면 결정값"""
    fl = _flat_plan(lm)
    if fl.get(key) is not None:
        return fl[key]
    pl = sget(lm, "plan", "plan_geom", "geometry", default=None)
    if isinstance(pl, dict) and pl.get(key) is not None and not isinstance(pl[key], dict):
        return pl[key]
    return default


def dotted(L, pts, col, lw=0.25, dash=0.8, gap=0.7):
    """점선 꺾은선(곡선은 표본점 목록으로)"""
    period = dash + gap
    ph = 0.0
    for p0, p1 in zip(pts[:-1], pts[1:]):
        Ls = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        if Ls < 1e-9:
            continue
        u = 0.0
        while u < Ls - 1e-9:
            if ph < dash:
                st_ = max(1e-4, min(dash - ph, Ls - u))
                L.line([lerp(p0, p1, u / Ls), lerp(p0, p1, min(1.0, (u + st_) / Ls))], col, lw, joint=False)
            else:
                st_ = max(1e-4, min(period - ph, Ls - u))
            u += st_
            ph += st_
            if ph >= period - 1e-9:
                ph = 0.0


def _mask_of(L, polys):
    m = Image.new("L", (L.w, L.h), 0)
    d = ImageDraw.Draw(m)
    for pg in polys:
        if pg and len(pg) >= 3:
            d.polygon([L.P(q) for q in pg], fill=255)
    return m


def _clip_layer(L, keep, cut=()):
    """하위 레이어 알파를 keep 다각형 안으로 자르고 cut 다각형은 지운다"""
    a = L.img.getchannel("A")
    a = ImageChops.multiply(a, _mask_of(L, keep))
    if cut:
        a = ImageChops.subtract(a, _mask_of(L, cut))
    L.img.putalpha(a)


def _bas_arch(uc, zs, r, a0=0.0, a1=180.0, n=14):
    """반원 호 점(u, z) 목록: 각 a0 → a1"""
    return [(uc + r * math.cos(math.radians(a0 + (a1 - a0) * i / float(n))), zs + r * math.sin(math.radians(a0 + (a1 - a0) * i / float(n)))) for i in range(n + 1)]


def _bas_runs(u0, u1, step, ok):
    """u0~u1을 step 간격으로 훑어 ok(u)가 참인 연속 구간 목록"""
    out, cur, u = [], None, u0
    while u <= u1 + 1e-9:
        if ok(u):
            cur = [u, u] if cur is None else [cur[0], u]
        elif cur is not None:
            out.append(tuple(cur))
            cur = None
        u += step
    if cur is not None:
        out.append(tuple(cur))
    return out


def draw_basilica():
    """L7 막센티우스 바실리카(d5_bas 새 그림, 사용자 21:57): 레퍼런스(키 큰 붉은 벽돌 교각 + 거대한 반원 아치 열 + 너머 2~3단 아케이드 벽이 둘러싼 안뜰).
    모든 모양은 평면 X·Y축에 맞춘다. 큰 아치 열 = 화면에 보이는 +Y 면(앞), 뒤 -Y·-X 벽 안쪽 면 2~3단 아케이드, +X 바깥 면 낮은 2단 아케이드,
    윗변은 폐허처럼 들쭉날쭉. 지면 포장은 기존 L자 기단. 높이 수치는 인쇄하지 않는다."""
    lm = LM.get("L7")
    if not lm:
        return
    g = {k: _lm_plan(lm, k, v) for k, v in D4_LANDMARKS[0]["plan"].items()}
    iso = _siso("L7")
    rects = [[float(v) for v in r] for r in g["base_rects"]]
    bh = float(g["base_h"])
    mx0, my0, mx1, my1 = rects[1]                      # 본체 직사각형(안뜰 + 큰 아치 열)
    brick, cream = (186, 118, 88), (232, 222, 196)
    cream_top, wall_top = (222, 208, 180), (206, 190, 160)
    dark, glow = (96, 70, 58), (236, 190, 138)
    fcol = lit(brick, (0.0, 1.0, 0.0))                 # +Y 면 벽돌색
    xcol = lit(brick, (1.0, 0.0, 0.0))                 # +X 면 벽돌색
    ccolY, ccolX = lit(cream, (0.0, 1.0, 0.0)), lit(cream, (1.0, 0.0, 0.0))
    lineY, lineX = shade(fcol, 0.84), shade(xcol, 0.84)

    def Q(face, f, u, z):
        return (u, f, bh + z) if face == "Y" else (f, u, bh + z)

    def face_poly(face, f, pts_uz, fill, ol=None, lw=0.1):
        iso.poly3([Q(face, f, u, z) for u, z in pts_uz], fill=fill, ol=ol, lw=lw)

    def face_line(face, f, pts_uz, col, lw=0.1):
        iso.line3([Q(face, f, u, z) for u, z in pts_uz], col, lw)

    # 1 기단 포장(L자) + 줄눈
    pave = Mesh(None)
    for r in rects:
        pave.extend(m_box(r[0], r[1], 0, r[2], r[3], bh, (202, 188, 158), top=(226, 214, 190)))
    pave.draw(iso, lw=0.12)

    def y_range(X):
        ys_ = [(r[1], r[3]) for r in rects if r[0] <= X <= r[2]]
        return (min(a for a, b in ys_), max(b for a, b in ys_)) if ys_ else None

    def x_range(Y):
        xs_ = [(r[0], r[2]) for r in rects if r[1] <= Y <= r[3]]
        return (min(a for a, b in xs_), max(b for a, b in xs_)) if xs_ else None
    jc = (212, 198, 170)
    X = min(r[0] for r in rects) + 4.0
    while X < max(r[2] for r in rects) - 1.0:
        yr = y_range(X)
        if yr:
            iso.line3([(X, yr[0] + 0.4, bh + 0.02), (X, yr[1] - 0.4, bh + 0.02)], jc, 0.1)
        X += 4.0
    Y = min(r[1] for r in rects) + 4.0
    while Y < max(r[3] for r in rects) - 1.0:
        xr_ = x_range(Y)
        if xr_:
            iso.line3([(xr_[0] + 0.4, Y, bh + 0.02), (xr_[1] - 0.4, Y, bh + 0.02)], jc, 0.1)
        Y += 4.0

    # 2 아케이드 벽(뒤 -Y 벽·-X 벽 안쪽 면, +X 바깥 면): 칸마다 벽돌 상자(윗변 들쭉날쭉) + 단마다 반원 개구부 + 크림 띠
    def arcade(face, f, u0, u1, depth, heights, tiers, ow, ring=0.6):
        """face 'Y': 벽 +Y 면이 Y=f에 있고 두께가 -Y로 depth. face 'X': +X 면이 X=f, 두께 -X로 depth. u = 면을 따라 가는 좌표.
        tiers = [(바닥 z, 스프링 z, 반지름, 빛(참이면 밝은 개구부))...]"""
        n = len(heights)
        pitch = (u1 - u0) / float(n)
        wall = Mesh(None)
        for k in range(n):
            ua, ub = u0 + pitch * k, u0 + pitch * (k + 1)
            if face == "Y":
                wall.extend(m_box(ua, f - depth, bh, ub, f, bh + heights[k], brick, top=wall_top))
            else:
                wall.extend(m_box(f - depth, ua, bh, f, ub, bh + heights[k], brick, top=wall_top))
        wall.draw(iso, lw=0.1)
        base_f = fcol if face == "Y" else xcol
        cr = ccolY if face == "Y" else ccolX
        ln_c = lineY if face == "Y" else lineX
        # 벽돌 줄눈
        zt_max = max(heights)
        z_ = 1.6
        while z_ < zt_max:
            def ok(u, z_=z_):
                k = min(n - 1, int((u - u0) / pitch))
                if z_ > heights[k] - 0.3:
                    return False
                uc = u0 + pitch * (k + 0.5)
                for (zb, zs_, rr, lt) in tiers:
                    if zs_ + rr + 0.4 < heights[k] + 0.5 and abs(u - uc) < rr + ring + 0.2 and zb - 0.1 <= z_ <= zs_ + rr + ring + 0.1:
                        return False
                return True
            for (a, b) in _bas_runs(u0 + 0.2, u1 - 0.2, 0.4, ok):
                if b - a > 0.5:
                    face_line(face, f + 0.01, [(a, z_), (b, z_)], ln_c, 0.1)
            z_ += 1.8
        # 단 사이 크림 띠(벽 높이를 넘지 않는 만큼)
        for t in range(len(tiers) - 1):
            zb = tiers[t][1] + tiers[t][2] + ring + 0.15
            zc = zb + 0.6
            for (a, b) in _bas_runs(u0, u1, 0.5, lambda u, zc=zc: heights[min(n - 1, int((u - u0) / pitch))] > zc + 0.3):
                face_poly(face, f + 0.01, [(a, zb), (b + 0.5 * 0, zb), (b, zc), (a, zc)], cr, ol=None)
        # 개구부(반원 아치) + 크림 아치 띠
        for k in range(n):
            uc = u0 + pitch * (k + 0.5)
            for (zb, zs_, rr, lt) in tiers:
                if heights[k] < zs_ + rr + ring + 1.0:
                    continue
                arc_in = _bas_arch(uc, zs_, rr)
                op = [(uc - rr, zb), (uc + rr, zb)] + arc_in[:]
                face_poly(face, f + 0.012, op, glow if lt else dark, ol=None)
                outer = _bas_arch(uc, zs_, rr + ring)
                rg = outer + arc_in[::-1]
                face_poly(face, f + 0.02, rg, cr, ol=None)
                for a_ in range(15, 180, 30):
                    ca, sa = math.cos(math.radians(a_)), math.sin(math.radians(a_))
                    face_line(face, f + 0.03, [(uc + rr * ca, zs_ + rr * sa), (uc + (rr + ring) * ca, zs_ + (rr + ring) * sa)], shade(cr, 0.8), 0.1)
                # 아래 벽돌 지지 교각 기둥머리 자리: 뒤 단 개구부 아래 크림 문턱
                face_poly(face, f + 0.02, [(uc - rr - 0.3, zb), (uc + rr + 0.3, zb), (uc + rr + 0.3, zb + 0.35), (uc - rr - 0.3, zb + 0.35)], cr, ol=None)

    # 뒤쪽 낮은 유적 연장(왼쪽 로브 쪽 -Y 벽 토막, 안쪽 면 없음)
    ruin = Mesh(None)
    lx0 = rects[0][0]
    for k_, (a_, b_, h_) in enumerate(((lx0 + 0.4, lx0 + 5.6, 6.0), (lx0 + 5.6, lx0 + 10.4, 10.2), (lx0 + 10.4, lx0 + 13.8, 4.8), (lx0 + 13.8, mx0, 8.6))):
        ruin.extend(m_box(a_, my0, bh, b_, my0 + 3.4, bh + h_, brick, top=wall_top))
    for (cx_, cy_, hh_) in ((lx0 + 6.0, my0 + 9.0, 2.6), (lx0 + 12.0, my0 + 14.0, 1.8), (lx0 + 4.0, my0 + 15.0, 1.2)):
        ruin.extend(m_cyl(cx_, cy_, 1.3, bh, bh + hh_, cream, n=8))
    ruin.draw(iso, lw=0.1)

    # 2a 뒤 -Y 벽(안쪽 +Y 면): 6칸, 3단(맨 위는 일부만)
    t_back = [(0.0, 6.2, 2.2, False), (10.0, 13.6, 2.0, True), (17.4, 20.2, 1.8, True)]
    h_back = [24.6, 21.0, 18.8, 23.8, 16.8, 22.4]
    arcade("Y", my0 + 4.6, mx0, mx1, 4.6, h_back, t_back, 2.2)
    # 2b -X 벽(안쪽 +X 면): 뒤 벽 안쪽 모서리부터 앞 아치 열 뒤까지 5칸
    t_side = [(0.0, 6.2, 2.1, False), (10.0, 13.6, 1.9, True)]
    h_wx = [20.0, 23.6, 15.6, 21.6, 14.4]
    arcade("X", mx0 + 3.2, my0 + 4.6, my1 - 6.0, 3.2, h_wx, t_side, 2.1)
    # 2c +X 바깥 면 낮은 2단 아케이드(여러 칸이 무너져 낮다)
    t_east = [(0.0, 4.6, 1.7, False), (8.0, 9.8, 1.7, True)]
    h_east = [12.8, 9.0, 6.8, 13.0, 7.4, 11.2]
    arcade("X", mx1, my0 + 4.6, my1 - 6.0, 3.0, h_east, t_east, 1.7)

    # 안뜰 바닥 잔해(무너져 내린 크림 돌덩이와 기둥 도막)
    deb = Mesh(None)
    for (px_, py_, sx_, sy_, hz_) in ((mx0 + 14.0, my0 + 14.0, 3.0, 2.2, 1.4), (mx0 + 20.0, my0 + 22.0, 2.2, 3.0, 0.9), (mx0 + 28.0, my0 + 12.0, 2.6, 2.0, 1.1), (mx0 + 12.0, my0 + 26.0, 2.0, 2.4, 0.8)):
        deb.extend(m_box(px_, py_, bh, px_ + sx_, py_ + sy_, bh + hz_, cream, top=cream_top))
    for (px_, py_, hz_) in ((mx0 + 22.0, my0 + 10.0, 2.2), (mx0 + 31.0, my0 + 20.0, 1.4)):
        deb.extend(m_cyl(px_, py_, 1.3, bh, bh + hz_, cream, n=8))
    deb.draw(iso, lw=0.1)

    # 3 큰 아치 열(앞 +Y 면): 키 큰 붉은 벽돌 교각 4개 + 크림 돌 기둥머리·받침·아치 띠 + 3칸 반원 아치, 윗변 폐허
    yF, dp = my1, 6.0
    npier, pw = 3, 5.2
    nb_ = npier - 1
    ow = (mx1 - mx0 - npier * pw) / float(nb_)                 # 아치 열린 폭
    r_a = ow / 2.0
    z_s = 14.6
    pier_h = [27.4, 29.0, 25.8]
    px0 = [mx0 + k * (pw + ow) for k in range(npier)]
    row = Mesh(None)
    for k in range(npier):
        a, b = px0[k], px0[k] + pw
        row.extend(m_box(a, yF - dp, bh, b, yF, bh + pier_h[k], brick, top=wall_top))
        row.extend(m_box(a - 0.45, yF - dp - 0.45, bh, b + 0.45, yF + 0.45, bh + 1.6, cream, top=cream_top))              # 받침
        row.extend(m_box(a - 0.55, yF - dp - 0.55, bh + z_s - 1.7, b + 0.55, yF + 0.55, bh + z_s, cream, top=cream_top))   # 기둥머리
        row.extend(m_box(a - 0.8, yF - dp - 0.8, bh + z_s - 0.45, b + 0.8, yF + 0.8, bh + z_s + 0.2, cream, top=cream_top))  # 주판
    row.draw(iso, lw=0.1)
    # 벽돌 줄눈(교각 앞면)
    z_ = 3.0
    while z_ < max(pier_h) - 0.5:
        for k in range(npier):
            if z_ < pier_h[k] - 0.4 and not (z_s - 1.9 < z_ < z_s + 0.5):
                face_line("Y", yF + 0.01, [(px0[k] + 0.2, z_), (px0[k] + pw - 0.2, z_)], lineY, 0.1)
        z_ += 1.8
    tops = [[(0.0, 26.4), (0.55, 26.4), (0.55, 25.6), (1.0, 25.6)],
            [(0.0, 26.0), (0.22, 26.0), (0.22, 24.9), (0.62, 24.9), (0.62, 24.0), (0.8, 24.0), (0.8, 25.2), (1.0, 25.2)]]

    def top_at(k, ua, ub, u):
        t = (u - ua) / (ub - ua)
        zz = tops[k][0][1]
        for (tt, zv) in tops[k]:
            if t >= tt - 1e-9:
                zz = zv
        return zz
    for k in range(nb_):
        ua, ub = px0[k] + pw, px0[k + 1]
        uc = (ua + ub) / 2.0
        # 아치 안쪽 면(왼쪽 반 = +X를 향해 보임)
        Fo, Bo = [], []
        for (u, z) in _bas_arch(uc, z_s, r_a, 90.0, 180.0, 10):
            Fo.append((u, yF, bh + z))
            Bo.append((u, yF - dp, bh + z))
        for i in range(len(Fo) - 1):
            iso.poly3([Fo[i], Fo[i + 1], Bo[i + 1], Bo[i]], fill=shade(xcol, 0.78), ol=None, lw=0.1)
        # 앞면 스팬드럴(아치 위 벽돌 면)
        topline = []
        nt = len(tops[k])
        for i, (tt, zv) in enumerate(tops[k]):
            topline.append((ua + (ub - ua) * tt, zv))
            nxt = tops[k][i + 1][0] if i + 1 < nt else 1.0
            topline.append((ua + (ub - ua) * nxt, zv))
        arc = _bas_arch(uc, z_s, r_a, 0.0, 180.0, 24)
        # 반시계: (ua,z_s) → 아치 호(왼쪽 → 위 → 오른쪽) → (ub,z_s) → 윗변 오른쪽에서 왼쪽
        sp = [(ua, z_s)] + [(u, z) for (u, z) in arc[::-1]] + [(ub, z_s)] + topline[::-1]
        face_poly("Y", yF + 0.005, sp, fcol, ol=None)
        # 벽돌 줄눈(스팬드럴)
        z_ = z_s + 0.9
        while z_ < 26.0:
            def okk(u, z_=z_, k=k, ua=ua, ub=ub, uc=uc):
                if z_ > top_at(k, ua, ub, u) - 1.4:
                    return False
                d = z_ - z_s
                return abs(u - uc) > math.sqrt(max(0.0, (r_a + 1.4) ** 2 - d * d)) if abs(d) < r_a + 1.4 else True
            for (a, b) in _bas_runs(ua + 0.1, ub - 0.1, 0.3, okk):
                if b - a > 0.4:
                    face_line("Y", yF + 0.01, [(a, z_), (b, z_)], lineY, 0.1)
            z_ += 1.8
        # 크림 돌 아치 띠 + 쐐기돌 줄
        outer = _bas_arch(uc, z_s, r_a + 1.4, 0.0, 180.0, 24)
        face_poly("Y", yF + 0.02, outer + arc[::-1], ccolY, ol=None)
        for a_ in range(8, 180, 10):
            ca, sa = math.cos(math.radians(a_)), math.sin(math.radians(a_))
            face_line("Y", yF + 0.03, [(uc + r_a * ca, z_s + r_a * sa), (uc + (r_a + 1.4) * ca, z_s + (r_a + 1.4) * sa)], shade(ccolY, 0.78), 0.1)
        # 윗변 크림 코니스 띠 + 마른 윗면
        for i, (tt, zv) in enumerate(tops[k]):
            nxt = tops[k][i + 1][0] if i + 1 < nt else 1.0
            a, b = ua + (ub - ua) * tt, ua + (ub - ua) * nxt
            face_poly("Y", yF + 0.02, [(a, zv - 1.0), (b, zv - 1.0), (b, zv), (a, zv)], ccolY, ol=None)
            iso.poly3([(a, yF - dp, bh + zv), (b, yF - dp, bh + zv), (b, yF, bh + zv), (a, yF, bh + zv)], fill=wall_top, ol=shade(wall_top, 0.8), lw=0.1)
    # 앞 가장자리 교각 윗면 균열 표시(폐허 느낌): 가장 낮은 교각 위 돌 두 덩이
    brk = Mesh(None)
    k_lo = pier_h.index(min(pier_h))
    brk.extend(m_box(px0[k_lo] + 0.5, yF - dp + 0.5, bh + pier_h[k_lo], px0[k_lo] + 2.4, yF - 1.4, bh + pier_h[k_lo] + 1.5, brick, top=wall_top))
    brk.draw(iso, lw=0.1)

    # 기록
    base_pts = [iso.p(r[i], r[j], z) for r in rects for i in (0, 2) for j in (1, 3) for z in (0.0, bh)]
    row_pts = [iso.p(x_, y_, bh + z_) for x_ in (mx0, mx1) for y_ in (yF - dp, yF) for z_ in (0.0, max(pier_h))]
    back_pts = [iso.p(x_, y_, bh + z_) for x_, y_, z_ in ((mx0, my0, 0.0), (mx1, my0, 0.0), (mx1, my0 + 4.6, 0.0), (mx0, my0, max(h_back)), (mx1, my0, max(h_back)),
                                                      (mx0, my1 - 6.0, 0.0), (mx0 + 3.2, my1 - 6.0, max(h_wx)))]
    add_fp("바실리카 지면", _hull(base_pts), "지면")
    add_fp("바실리카 측랑 볼트", _hull(row_pts), "대상 면")
    add_fp("바실리카 신랑 유적", _hull(back_pts), "대상 면")
    uc0 = (px0[0] + pw + px0[1]) / 2.0
    uc1 = (px0[1] + pw + px0[2]) / 2.0
    tgt = iso.p(mx1, yF - dp * 0.5, bh + pier_h[-1] - 3.6)         # 큰 아치 열 오른쪽 끝 교각 윗부분(+X 면)
    GEO["lead_tgt_막센티우스 바실리카"] = tgt
    if "막센티우스 바실리카" in SLOT:
        SLOT["막센티우스 바실리카"]["target_pt"] = [round(tgt[0], 2), round(tgt[1], 2)]
    GEO["basilica_mid_bay"] = iso.p(uc1, yF, bh + z_s + r_a + 2.2)
    all_pts = base_pts + row_pts + back_pts
    GEO["parts_L7"] = [_hull([iso.p(r[i], r[j], z) for i in (0, 2) for j in (1, 3) for z in (0.0, bh)]) for r in rects] + [_hull(row_pts), _hull(back_pts)]
    for pg in GEO["parts_L7"]:
        ex_poly(pg, 2.0)
    GEO["sil_L7"] = _hull(all_pts)
    bb = bbox_of(all_pts)
    GEO["basilica_form"] = {"bays": [{"bay": k + 1, "u": [round(px0[k] + pw, 2), round(px0[k + 1], 2)],
                                      "open_face_center": [round(v, 2) for v in iso.p((px0[k] + pw + px0[k + 1]) / 2.0, yF, bh + z_s * 0.55)]} for k in range(nb_)],
                            "arch_r_plan": round(r_a, 2), "spring_z": round(z_s, 2), "aisle_h": max(pier_h), "vault_ghost_h_max": 0.0,
                            "ghost_rule": "점선 복원 없음(d5_bas: 큰 아치 열 + 안뜰 아케이드 벽)"}
    record("L7", lm["name"], "Core(표준 랜드마크)", lm["projected_box"], bb, "큰 반원 아치 열(벽돌 교각 4·아치 3) + 안뜰을 두른 2~3단 아케이드 벽(폐허 윗변)")


def draw_mausoleum():
    """L8 하드리아누스 영묘 + 폰스 아일리우스(22:10 재구성, 레퍼런스 user_hadrian_bridge.jpg):
    앞(+Y, 카메라 쪽)에서 영묘 앞 운하(canal_h6)를 건너는 아치 3개 다리(가운데 아치가 가장 큼) → 풀 덮인 둔덕(잔디 비탈) 위 축대 기단
    → 원형 기둥 회랑(작은 열주) + 얕은 돔. 모든 모양은 평면 X·Y축 정렬. 치수는 인쇄하지 않는다."""
    lm = LM.get("L8")
    if not lm:
        return
    g = {k: _lm_plan(lm, k, v) for k, v in D4_LANDMARKS[1]["plan"].items()}
    iso = _siso("L8")
    X0, Y0, X1, Y1 = [float(v) for v in g["base"]]                  # 둔덕 지면(풀 비탈 밑변)
    bh = float(g["base_h"])                                         # 축대 기단 윗면 z(5.0)
    dcx, dcy = [float(v) for v in g["drum_c"]]
    R = float(g["drum_r"])                                          # 회랑 바닥(스타일로베이트) 반지름
    z0d, z1d = [float(v) for v in g["drum_z"]]                      # 회랑 z: 기단 윗면 ~ 엔타블러처 윗면
    zt1 = float(g["top_z"][1])                                      # 돔 꼭대기 z
    bX0, bY0, bX1, bY1 = [float(v) for v in g["bridge"]]
    brh = float(g["bridge_h"])                                      # 다리 상판 z(3.0) = 둔덕 윗면 z
    nar = int(g["bridge_arches"])
    marble, trav = (246, 238, 220), (226, 212, 182)
    grass, grass_top = (122, 150, 84), (146, 172, 100)
    cxm, cym = (X0 + X1) / 2.0, (Y0 + Y1) / 2.0
    # 0 풀 둔덕: 사각 뿔대(비탈 잔디색), 밑변 = 기단 지면, 윗면(z = 상판 높이)은 안쪽으로 6 들어간다
    inset = 8.0
    hill_base = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]
    k_ = ((X1 - X0) - 2 * inset) / float(X1 - X0)
    hill = m_frustum(hill_base, 0.0, brh, k_, grass, top=grass_top)
    hill.draw(iso, lw=0.10)
    PX0, PY0, PX1, PY1 = X0 + inset, Y0 + inset, X1 - inset, Y1 - inset   # 둔덕 윗면(평평한 풀밭)
    for u in (0.3, 0.62):                                           # 비탈 풀결(수평 띠)
        zc = brh * u
        ii = inset * (1.0 - u)
        iso.line3([(X0 + ii, Y1 - ii + 0.01, zc), (X1 - ii, Y1 - ii + 0.01, zc)], (112, 138, 76), 0.1)
        iso.line3([(X1 - ii + 0.01, Y0 + ii, zc), (X1 - ii + 0.01, Y1 - ii, zc)], (108, 134, 72), 0.1)
    # 1 축대 기단(대리석 마감): 둔덕 윗면 위 사각 축대 z brh → bh
    WX0, WX1 = dcx - 15.5, dcx + 15.5
    WY0, WY1 = dcy - 14.0, dcy + 12.5
    wall = Mesh(None)
    wall.extend(m_box(WX0, WY0, brh, WX1, WY1, bh, marble, top=(232, 224, 206)))
    wall.draw(iso, lw=0.12)
    iso.line3([(WX0, WY1 + 0.01, brh + 1.0), (WX1, WY1 + 0.01, brh + 1.0)], (200, 190, 170), 0.15)
    iso.line3([(WX1 + 0.01, WY0, brh + 1.0), (WX1 + 0.01, WY1, brh + 1.0)], (194, 184, 164), 0.15)
    for xj in range(int(WX0) + 3, int(WX1), 4):                     # 축대 줄눈(앞면)
        iso.line3([(xj, WY1 + 0.01, brh), (xj, WY1 + 0.01, bh)], (214, 206, 188), 0.1)
    for yj in range(int(WY0) + 3, int(WY1), 4):
        iso.line3([(WX1 + 0.01, yj, brh), (WX1 + 0.01, yj, bh)], (208, 200, 182), 0.1)
    # 2 원형 기둥 회랑 + 얕은 돔(한 메시로 깊이순 정렬)
    col_r = R - 1.3                                                 # 기둥 고리 반지름
    ncol = 18
    zc0, zc1 = z0d + 0.7, z1d - 1.6                                 # 기둥 아래·위
    col = Mesh(None)
    col.extend(m_cyl(dcx, dcy, R, z0d, z0d + 0.7, marble, n=32, top=(236, 228, 210)))          # 스타일로베이트
    col.extend(m_cyl(dcx, dcy, col_r - 1.5, z0d + 0.7, zc1, (196, 184, 162), n=28, top=(214, 204, 184)))   # 안쪽 벽(그늘)
    for i in range(ncol):
        a = 2.0 * math.pi * i / ncol
        col.extend(m_cyl(dcx + col_r * math.cos(a), dcy + col_r * math.sin(a), 0.72, zc0, zc1, (250, 244, 228), n=8, top=(240, 232, 214)))
    col.extend(m_cyl(dcx, dcy, R - 0.2, zc1, z1d, marble, n=32, top=(238, 230, 212)))            # 엔타블러처
    ra, za = col_r - 2.4, z1d + 2.2
    col.extend(m_cyl(dcx, dcy, ra, z1d, za, (238, 230, 212), n=28, top=(226, 218, 200)))         # 낮은 아티카 원통
    dome_c = (150, 158, 160)
    prof = [(ra, za), (ra * 0.97, za + 0.6), (ra * 0.82, za + 1.5), (ra * 0.55, za + 2.2), (ra * 0.22, za + 2.6)]
    for (r_a, z_a), (r_b, z_b) in zip(prof[:-1], prof[1:]):
        col.extend(m_cyl(dcx, dcy, r_a, z_a, z_b, dome_c, n=28, k=r_b / r_a))
    col.extend(m_cyl(dcx, dcy, ra * 0.12, zt1 - 0.5, zt1, (214, 206, 188), n=8))
    col.draw(iso, lw=0.08)
    # 3 다리 앞 디딤 2단(둔덕 윗면 3.0 → 3.67 → 4.33 → 축대 윗면 5.0): 축대 앞(+Y) 변에서 앞쪽으로. 폭 = 둑 길 폭 7
    rx0, rx1 = (bX0 + bX1) / 2.0 - 3.5, (bX0 + bX1) / 2.0 + 3.5     # 둑 길 X(폭 7)
    st_x0, st_x1 = rx0, rx1
    rise = (bh - brh) / 3.0
    ys_n = WY1                                                      # 축대 앞 변 평면 Y
    stp = Mesh(None)
    steps_ = []
    for k in range(2):
        ya_, yb_ = ys_n + 2.0 * k, ys_n + 2.0 * (k + 1)             # k=0: 축대 쪽 높은 단(4.33), k=1: 바깥 단(3.67)
        zt_ = brh + rise * (2 - k)
        stp.extend(m_box(st_x0, ya_, brh - 0.01, st_x1, yb_, zt_, (232, 224, 206), top=(238, 230, 214)))
        steps_.append({"Y": [round(ya_, 2), round(yb_, 2)], "z_top": round(zt_, 2)})
    stp.draw(iso, lw=0.1)
    # 4 둑 길 북쪽(언덕 앞 비탈 오름길): 언덕 밑변(Y1, z 0) → 둔덕 윗면 앞 변(PY1, z 3.0), 폭 7. 다리 북쪽 끝(Y1)에서 바로 이어진다
    road_c, road_s = (226, 212, 182), (214, 200, 170)
    P.poly([iso.p(rx0, Y1, 0.0), iso.p(rx1, Y1, 0.0), iso.p(rx1, PY1, brh), iso.p(rx0, PY1, brh)], fill=road_c)
    P.line([iso.p(rx1, Y1, 0.0), iso.p(rx1, PY1, brh)], road_s, 0.18, joint=False)
    P.line([iso.p(rx0, Y1, 0.0), iso.p(rx0, PY1, brh)], road_s, 0.14, joint=False)
    # 5 다리: 물길(canal_Y)을 +Y축으로 직각으로 건넌다. 상판은 가운데가 솟은 활 모양(z = brh·(1 − ((Y − 중심)/반길이)^2)), 양 끝은 둑(z 0)과 만난다
    w_y0, w_y1 = [float(v) for v in _lm_plan(lm, "canal_Y", [bY0 + 4.0, bY1 - 4.0])]   # 물 구간 Y 폭
    wz = -DIO_T                                                     # 수면 z
    ym, hl = (bY0 + bY1) / 2.0, (bY1 - bY0) / 2.0

    def deck_z(y_):
        return brh * (1.0 - ((y_ - ym) / hl) ** 2)
    ys = [bY0 + (bY1 - bY0) * i / 40.0 for i in range(41)]
    trav_s = ftone(trav, 0.7071, 0.7071)
    # 5a +X 옆면(몸통): 밑 = 둑 구간 -0.4, 물 구간 수면(교각이 물속에 선다)
    bot = [(bY0, -0.4), (w_y0, -0.4), (w_y0, wz), (w_y1, wz), (w_y1, -0.4), (bY1, -0.4)]
    side = [iso.p(bX1, u, z) for u, z in bot] + [iso.p(bX1, y_, deck_z(y_)) for y_ in reversed(ys)]
    P.poly(side, fill=trav, outline=(150, 134, 108), lw=0.12)
    # 5b 상판 윗면(가운데가 솟은 활) + 난간(양쪽 가장자리 낮은 벽)
    for y0_, y1_ in zip(ys[:-1], ys[1:]):
        P.poly([iso.p(bX0, y0_, deck_z(y0_)), iso.p(bX1, y0_, deck_z(y0_)), iso.p(bX1, y1_, deck_z(y1_)), iso.p(bX0, y1_, deck_z(y1_))], fill=(238, 228, 204))
    pw = 0.55
    for xa_, xb_, col_ in ((bX0, bX0 + pw, (222, 210, 184)), (bX1 - pw, bX1, (230, 218, 192))):
        for y0_, y1_ in zip(ys[:-1], ys[1:]):
            za_, zb_ = deck_z(y0_), deck_z(y1_)
            P.poly([iso.p(xb_, y0_, za_), iso.p(xb_, y0_, za_ + 0.8), iso.p(xb_, y1_, zb_ + 0.8), iso.p(xb_, y1_, zb_)], fill=ftone(col_, 0.7071, 0.7071))      # +X 향한 면
            P.poly([iso.p(xa_, y0_, za_ + 0.8), iso.p(xb_, y0_, za_ + 0.8), iso.p(xb_, y1_, zb_ + 0.8), iso.p(xa_, y1_, zb_ + 0.8)], fill=col_)               # 윗면
    # 5c 아치 3개(물 구간 안): 가운데 = 큰 아치(너비 2배), 좌우 = 작은 아치, 교각 1.2. 꼭대기 = 상판 아래 0.9
    pier = 1.2
    wsm = (w_y1 - w_y0 - (nar - 1) * pier) / (nar - 1 + 2.0)        # 작은 아치 폭(가운데 = 2배)
    widths = [wsm if k != nar // 2 else wsm * 2.0 for k in range(nar)]
    ya = w_y0
    arches_ = []
    for k in range(nar):
        aw = widths[k]
        yc = ya + aw / 2.0
        rr_ = aw / 2.0
        crown = deck_z(yc) - 0.9
        zsp = crown - rr_
        q = [(ya, wz), (ya + aw, wz), (ya + aw, zsp)] + [(yc + rr_ * math.cos(math.pi * i / 14.0), zsp + rr_ * math.sin(math.pi * i / 14.0)) for i in range(0, 15)] + [(ya, zsp)]
        P.poly([iso.p(bX1 + 0.02, u, z) for u, z in q], fill=(70, 116, 152), outline=(124, 108, 84), lw=0.14)
        P.poly([iso.p(bX1 + 0.025, u, z) for u, z in [(ya + 0.15, wz), (ya + aw - 0.15, wz), (ya + aw - 0.15, wz + 1.6), (ya + 0.15, wz + 1.6)]], fill=(120, 172, 208))   # 수면 가까이 밝은 물빛
        qi = [(yc + rr_ * 1.12 * math.cos(math.pi * i / 14.0), zsp + rr_ * 1.12 * math.sin(math.pi * i / 14.0)) for i in range(0, 15)]
        P.line([iso.p(bX1 + 0.03, u, z) for u, z in qi], (176, 160, 130), 0.14)          # 아치 테(쐐기돌 띠)
        arches_.append([round(ya, 2), round(ya + aw, 2), round(crown, 2)])
        ya += aw + pier
    P.line([iso.p(bX1 + 0.03, y_, deck_z(y_) - 0.2) for y_ in ys], (170, 154, 126), 0.16)      # 상판 아랫 띠
    # 5d 둑 길 남쪽(다리 남쪽 끝 → 평면 Y +5, 폭 7, 높이 0)
    ra0, ra1 = bY1, bY1 + 5.0
    P.poly([iso.p(rx0, ra0, 0.0), iso.p(rx1, ra0, 0.0), iso.p(rx1, ra1, 0.0), iso.p(rx0, ra1, 0.0)], fill=road_c)
    P.line([iso.p(rx1, ra0, 0.0), iso.p(rx1, ra1, 0.0)], road_s, 0.14, joint=False)
    GEO["mausoleum_steps"] = {"X": [st_x0, st_x1], "steps": steps_, "riser": round(rise, 3), "ramp": {"X": [rx0, rx1], "Y": [Y1, PY1], "z": [0.0, brh]},
                              "bridge": {"axis": "Y", "span_Y": [bY0, bY1], "water_Y": [w_y0, w_y1], "center_X": (bX0 + bX1) / 2.0, "arches": arches_},
                              "rule": "22:40 재설계: 다리(+Y축, 물길 직각) 양 끝 높이 0 = 둑 길. 북쪽 길이 언덕 앞 비탈(폭 7)로 3.0까지 오르고 → 축대 앞 디딤 2단(3.67·4.33) → 축대 윗면 5.0. 양 끝 보행면 높이 차 0"}
    # 6 기록
    hill_pts = [iso.p(x_, y_, z_) for x_ in (X0, X1) for y_ in (Y0, Y1) for z_ in (0.0,)] + [iso.p(x_, y_, brh) for x_ in (PX0, PX1) for y_ in (PY0, PY1)]
    wall_pts = [iso.p(x_, y_, z_) for x_ in (WX0, WX1) for y_ in (WY0, WY1) for z_ in (brh, bh)]
    col_pts = [iso.p(dcx + R * math.cos(math.radians(t)), dcy + R * math.sin(math.radians(t)), z) for t in range(0, 360, 10) for z in (z0d, z1d)]
    col_pts.append(iso.p(dcx, dcy, zt1))
    br_pts = ([iso.p(x_, y_, z_) for x_ in (bX0, bX1) for y_ in (bY0, bY1) for z_ in (-0.4, 0.8)]
              + [iso.p(x_, ym, brh + 0.8) for x_ in (bX0, bX1)]
              + [iso.p(x_, y_, wz) for x_ in (bX0, bX1) for y_ in (w_y0, w_y1)])
    ramp_pts = [iso.p(x_, y_, 0.0) for x_ in (rx0, rx1) for y_ in (ra1,)]
    base_pts = hill_pts + wall_pts
    add_fp("영묘 기단", _hull(base_pts), "대상 면")
    add_fp("영묘 원통", _hull(col_pts), "대상 면")
    add_fp("폰스 아일리우스 다리", _hull(br_pts), "대상 면")
    strip_r = [iso.p(WX1 - 1.9, WY0 + 0.6, bh), iso.p(WX1 - 0.3, WY0 + 0.6, bh), iso.p(WX1 - 0.3, WY1 - 0.3, bh), iso.p(WX1 - 1.9, WY1 - 0.3, bh)]
    strip_f = [iso.p(WX0 + 0.6, WY1 - 1.5, bh), iso.p(WX1 - 0.3, WY1 - 1.5, bh), iso.p(WX1 - 0.3, WY1 - 0.3, bh), iso.p(WX0 + 0.6, WY1 - 0.3, bh)]
    GEO["fpset_영묘 기단 윗면"] = [strip_r, strip_f]
    add_fp("영묘 기단 윗면", strip_r, "대상 면")
    hull = _hull(base_pts + col_pts)
    GEO["parts_L8"] = [_hull(base_pts), _hull(col_pts), _hull(br_pts + ramp_pts)]
    for pg in GEO["parts_L8"]:
        ex_poly(pg, 2.0)
    GEO["sil_L8"] = hull
    GEO["sil_L8_bridge"] = _hull(br_pts + ramp_pts)
    bb = bbox_of(base_pts + col_pts + br_pts + ramp_pts)
    record("L8", lm["name"], "Core(표준 랜드마크)", lm["projected_box"], bb, "다리 포함 외곽")
    DRAWN["mausoleum_access"] = GEO.get("mausoleum_steps")


def draw_theatre():
    """L9 마르켈루스 극장(결정 9 후보 (라)): 반원 평면(지름 = 무대 쪽, 곡면 = +X), 바깥 아케이드 2단(6+6), 관람석 단, 무대 쪽 벽 ≤ 4.
    3단은 그리지 않는다. 지름은 인쇄하지 않는다."""
    lm = LM.get("L9")
    if not lm:
        return
    g = {k: _lm_plan(lm, k, v) for k, v in D4_LANDMARKS[2]["plan"].items()}
    iso = _siso("L9")
    cx, cy = [float(v) for v in g["center"]]
    R = float(g["r"])
    Hh = float(g["h"])
    tier = float(g["tier_h"])
    swh = min(4.0, float(g["stage_wall_h"]))
    trav = (214, 194, 150)
    # 1 무대 쪽 벽(지름 뒤, 낮은 유적) + 무대 단 + 오케스트라
    m0 = Mesh(None)
    m0.extend(m_box(cx - 2.0, cy - R, 0, cx - 0.5, cy + R, swh, (204, 186, 150), top=(222, 206, 174)))
    m0.extend(m_box(cx - 0.5, cy - R * 0.66, 0, cx + 2.6, cy + R * 0.66, 1.1, (196, 172, 130), top=(214, 194, 154)))
    m0.draw(iso, lw=0.1)
    r_in, r_out = 11.0, R - 1.4
    iso.poly3([(cx + (r_in - 0.3) * math.cos(math.radians(t)), cy + (r_in - 0.3) * math.sin(math.radians(t)), 0.5) for t in range(-90, 91, 6)],
              fill=(226, 214, 188), ol=(190, 172, 140), lw=0.12)
    # 2 관람석 단(카베아) + 보이는 계단 앞면 + 바깥 아케이드 벽
    n = 7
    rows = [r_in + (r_out - r_in) * k / n for k in range(n + 1)]
    zr = [1.0 + (Hh - 1.0) * (k + 1) / n for k in range(n)]
    seat_c, riser_c = (230, 216, 186), (196, 180, 148)
    m = Mesh(None)
    for k in range(n):
        ra, rb, z = rows[k], rows[k + 1], zr[k]
        zlow = zr[k - 1] if k > 0 else 0.5
        t = -90.0
        while t < 90.0 - 1e-6:
            t1 = min(90.0, t + 6.0)
            a, b = math.radians(t), math.radians(t1)
            q = [(cx + ra * math.cos(a), cy + ra * math.sin(a), z), (cx + ra * math.cos(b), cy + ra * math.sin(b), z),
                 (cx + rb * math.cos(b), cy + rb * math.sin(b), z), (cx + rb * math.cos(a), cy + rb * math.sin(a), z)]
            m.add(q, seat_c if k % 2 else shade(seat_c, 0.95), "two")
            tm = math.radians((t + t1) / 2.0)
            if -math.cos(tm) - math.sin(tm) > 0.02:
                m.add([(cx + ra * math.cos(a), cy + ra * math.sin(a), zlow), (cx + ra * math.cos(b), cy + ra * math.sin(b), zlow),
                       (cx + ra * math.cos(b), cy + ra * math.sin(b), z), (cx + ra * math.cos(a), cy + ra * math.sin(a), z)], riser_c, "two")
            t = t1
    t = -90.0
    while t < 90.0 - 1e-6:
        t1 = min(90.0, t + 3.0)
        a, b = math.radians(t), math.radians(t1)
        m.add([(cx + r_out * math.cos(a), cy + r_out * math.sin(a), Hh), (cx + r_out * math.cos(b), cy + r_out * math.sin(b), Hh),
               (cx + R * math.cos(b), cy + R * math.sin(b), Hh), (cx + R * math.cos(a), cy + R * math.sin(a), Hh)], (226, 210, 174), "two")
        tm = math.radians((t + t1) / 2.0)
        if math.cos(tm) + math.sin(tm) > 0.02:
            m.add([(cx + R * math.cos(a), cy + R * math.sin(a), 0.0), (cx + R * math.cos(b), cy + R * math.sin(b), 0.0),
                   (cx + R * math.cos(b), cy + R * math.sin(b), Hh), (cx + R * math.cos(a), cy + R * math.sin(a), Hh)], trav, "two")
        t = t1
    m.draw(iso, lw=0.10)
    for a_ in (-50.0, 0.0, 50.0):                                    # 방사 계단 3
        iso.line3([(cx + r_in * math.cos(math.radians(a_)), cy + r_in * math.sin(math.radians(a_)), 1.0),
                   (cx + r_out * math.cos(math.radians(a_)), cy + r_out * math.sin(math.radians(a_)), Hh)], (246, 238, 214), 0.35)
    # 3 아케이드 2단(아래 도리아·위 이오니아), 보이는 쪽만
    dark = (96, 72, 50)
    tc = -84.0
    while tc <= 84.0 + 1e-6:
        if math.cos(math.radians(tc)) + math.sin(math.radians(tc)) > 0.12:
            cyl_arch(iso, cx, cy, R + 0.02, tc, 2.4, 0.4, 3.1, dark)
            cyl_arch(iso, cx, cy, R + 0.02, tc, 2.2, tier + 0.5, tier + 2.9, dark)
        tc += 8.0
    vis = [t_ for t_ in range(-44, 91, 3)]
    iso.line3([(cx + (R + 0.03) * math.cos(math.radians(t_)), cy + (R + 0.03) * math.sin(math.radians(t_)), tier) for t_ in vis], (238, 222, 188), 0.32)
    iso.line3([(cx + (R + 0.03) * math.cos(math.radians(t_)), cy + (R + 0.03) * math.sin(math.radians(t_)), Hh - 0.1) for t_ in vis], (240, 226, 194), 0.3)
    # 4 기록·지시선 대상(관람석 윗면 가운데 가까운 점)
    pts = [iso.p(cx + R * math.cos(math.radians(t_)), cy + R * math.sin(math.radians(t_)), z) for t_ in range(-90, 91, 5) for z in (0.0, Hh)]
    pts += [iso.p(cx - 2.0, cy + s_ * R, z) for s_ in (-1, 1) for z in (0.0, swh)]
    hull = _hull(pts)
    add_fp("극장 반원 아케이드", hull, "대상 면")
    tpt = (SLOT.get("마르켈루스 극장") or {}).get("target_pt") or [52.0, 315.0]
    best = None
    for k in range(1, n - 1):
        for t_ in range(-30, 88, 2):
            rr = (rows[k] + rows[k + 1]) / 2.0
            q = iso.p(cx + rr * math.cos(math.radians(t_)), cy + rr * math.sin(math.radians(t_)), zr[k])
            d_ = math.hypot(q[0] - tpt[0], q[1] - tpt[1])
            if best is None or d_ < best[0]:
                best = (d_, q)
    GEO["lead_tgt_마르켈루스 극장"] = best[1]
    ex_poly(hull, 2.0)
    GEO["sil_L9"] = hull
    GEO["parts_L9"] = [hull]
    record("L9", lm["name"], "Core(표준 랜드마크)", lm["projected_box"], bbox_of(pts), "반원 아케이드 2단, 관람석 %d단" % n)


def m_statue(X, Y, z0, h, col, col_l, key="거상"):
    """가는 서 있는 청동상(평면 폭 ≤ 2.4): 다리 2 + 몸통 + 머리 + 지팡이"""
    m = Mesh(None)
    m.extend(m_box(X - 0.62, Y - 0.32, z0, X - 0.1, Y + 0.32, z0 + h * 0.44, tint(col, 0.86)))
    m.extend(m_box(X + 0.1, Y - 0.32, z0, X + 0.62, Y + 0.32, z0 + h * 0.44, tint(col, 0.86)))
    m.extend(m_frustum(ring(X, Y, 0.95, 6, 0.3), z0 + h * 0.42, z0 + h * 0.82, 0.78, col))
    m.extend(m_box(X + 0.75, Y - 0.2, z0 + h * 0.55, X + 1.15, Y + 0.2, z0 + h * 0.80, col_l))
    m.extend(m_blob(X, Y, z0 + h * 0.895, 0.62, col_l, n=6, key=key, jit=0.04))
    m.extend(m_cyl(X - 1.05, Y, 0.12, z0, z0 + h * 0.96, tint(col, 0.8), n=5))
    return m


H_YARD, H_YARD_J = (221, 209, 184), (207, 194, 168)     # 네로 거상 마당 판석·줄눈


def draw_colossus():
    """네로 거상 받침(결정 10): 벽돌 마감 콘크리트 받침 8×8·높이 5 + 윗단 가는 대리석 띠 + 청동 거상(복원 추정) 2.4×2.4·높이 15.
    치수·'콜로세움' 이름 유래는 인쇄하지 않는다."""
    d = COLOSSUS
    if not d:
        return
    X, Y = [float(v) for v in (d.get("plan") or D4_COLOSSUS["plan"])]
    ped, sta = d.get("pedestal") or {}, d.get("statue") or {}             # 통합 d4: map 사양 pedestal{plan_size,h}·statue{plan_size,z}
    b = float(d.get("base_mm") or (ped.get("plan_size") or [8.0])[0]) / 2.0
    bh = float(d.get("base_h") or ped.get("h") or 5.0)
    sz_ = sta.get("z")
    sh = float(d.get("statue_h") or ((float(sz_[1]) - float(sz_[0])) if sz_ else 15.0))
    iso = ISO
    yard = sget(d, "yard_box", "yard_screen", default=None) or [82.3, 437.0, 108.3, 469.0]
    cxs, cys = sp(X, Y)
    hs = min((yard[2] - yard[0]) / (4.0 * C30), (yard[3] - cys) / 1.0, 7.5)          # 평면 정사각 마당(화면 마름모가 마당 상자 안)
    yq = [sp(X - hs, Y - hs), sp(X + hs, Y - hs), sp(X + hs, Y + hs), sp(X - hs, Y + hs)]
    P.poly(yq, fill=H_YARD)
    for k in range(1, 6):                                            # 마당 판석 줄눈(L3)
        f_ = k / 6.0
        P.line([lerp(yq[0], yq[1], f_), lerp(yq[3], yq[2], f_)], H_YARD_J, 0.12, joint=False)
        P.line([lerp(yq[0], yq[3], f_), lerp(yq[1], yq[2], f_)], H_YARD_J, 0.12, joint=False)
    ex_rect(yard, 0.0)
    add_fp("네로 거상 마당", yq, "지면")
    m = Mesh(None)
    m.extend(m_box(X - b, Y - b, 0, X + b, Y + b, bh - 0.6, BRICK, top=BRICK_L))
    m.extend(m_box(X - b - 0.15, Y - b - 0.15, bh - 0.6, X + b + 0.15, Y + b + 0.15, bh, (240, 234, 220), top=(246, 242, 230)))
    m.draw(iso, lw=0.1)
    for zc in (1.1, 2.2, 3.3):                                       # 벽돌 줄눈(보이는 두 면)
        iso.line3([(X - b, Y + b + 0.01, zc), (X + b, Y + b + 0.01, zc)], shade(BRICK, 0.8), 0.1)
        iso.line3([(X + b + 0.01, Y - b, zc), (X + b + 0.01, Y + b, zc)], shade(BRICK, 0.8), 0.1)
    bronze, bronze_l = (146, 106, 60), (186, 144, 84)
    st = Mesh(None)
    st.extend(m_box(X - 1.1, Y - 1.1, bh, X + 1.1, Y + 1.1, bh + 0.5, bronze_l))
    st.extend(m_statue(X, Y, bh + 0.5, sh - 0.5, bronze, bronze_l, key="네로거상"))
    st.draw(iso, lw=0.10)
    hx, hy = iso.p(X, Y, bh + 0.5 + (sh - 0.5) * 0.895)
    for k in range(7):                                              # 빛살 관(태양신 모습, 복원 추정)
        a = math.radians(-165 + k * 25.0)
        P.line([(hx + 0.72 * math.cos(a), hy + 0.72 * math.sin(a)), (hx + 1.35 * math.cos(a), hy + 1.35 * math.sin(a))], (200, 160, 84), 0.16, joint=False)
    base_pts = [iso.p(x_, y_, z_) for x_ in (X - b - 0.15, X + b + 0.15) for y_ in (Y - b - 0.15, Y + b + 0.15) for z_ in (0.0, bh)]
    st_pts = [iso.p(*q) for q in mesh_pts(st)] + [(hx, hy - 1.35)]
    add_fp("네로 거상 받침", _hull(base_pts), "대상 면")
    add_fp("네로 거상", _hull(st_pts), "대상 면")
    GEO["colossus_head"] = (hx, hy)
    hull = _hull(base_pts + st_pts)
    GEO["parts_colossus"] = [_hull(base_pts), _hull(st_pts)]
    for pg in GEO["parts_colossus"]:
        ex_poly(pg, 2.0)
    GEO["sil_colossus"] = hull
    bb = bbox_of(base_pts + st_pts)
    REPORT["objects"]["네로 거상 받침"] = {"이름": d["name"], "사양 상자": d.get("box"), "그린 외곽": [round(v, 1) for v in bb]}


def hexring(cx, cy, r, a0=30.0):
    return [(cx + r * math.cos(math.radians(a0 + 60 * k)), cy + r * math.sin(math.radians(a0 + 60 * k))) for k in range(6)]


def portus_params():
    """사양 core_map.portus_geometry의 방파제·운하·등대섬(없으면 결정 값)"""
    mol = sget(PG, "moles", "PORTUS_MOLES", default=None) or sget(CM, "portus_moles", default=None) or {}
    can = sget(PG, "canals", "PORTUS_CANALS", default=None) or sget(CM, "portus_canals", default=None) or []
    lh = sget(PG, "lighthouse", "PORTUS_LIGHTHOUSE", default=None) or sget(CM, "portus_lighthouse", default=None) or {}
    r_out = float(sget(mol, "r_out", "r_outer", default=21.0))
    r_in = float(sget(mol, "r_in", "r_inner", default=18.4))
    arm_a = [float(v) for v in sget(mol, "arm_a_deg", "arm_a", default=[173.0, 33.0])]
    arm_b = [float(v) for v in sget(mol, "arm_b_deg", "arm_b", default=[187.0, 327.0])]
    col = [float(v) for v in sget(mol, "colonnade_deg", "colonnade", default=[282.0, 324.0])]
    canals = []
    for c in (can or [{"name": "강 쪽 운하", "plan_x": [511.7, 531.4], "plan_y": [310.5, 313.5]},
                      {"name": "외항 쪽 운하", "plan_x": [554.8, 574.06], "plan_y": [310.5, 313.5]}]):
        canals.append({"name": c.get("name", "운하"), "x": [float(v) for v in c.get("plan_x")], "y": [float(v) for v in c.get("plan_y")]})
    ang = float(sget(lh, "plan_angle_deg", "angle_deg", "angle", default=348.0))
    lr = float(sget(lh, "plan_r", "r", default=24.0))
    isl = float(sget(lh, "island_r", default=3.4))
    tiers = sget(lh, "tiers", default=[[2.8, 1.0, 9.0], [2.25, 9.0, 15.4], [1.75, 15.4, 20.6]])
    lant = sget(lh, "lantern", default=[1.1, 20.6, 24.0])
    hwr = float(sget(PG, "hexagon_water_R", default=15.2) or 15.2)
    return dict(r_out=r_out, r_in=r_in, arm_a=arm_a, arm_b=arm_b, col=col, canals=canals, ang=ang, lr=lr, isl=isl, tiers=tiers, lant=lant, hwr=hwr)


def draw_portus():
    L6 = LM["L6"]
    hx, hy = PG["hexagon_plan_center"]
    HR = PG["hexagon_plan_R"]
    bx, by = PG["claudian_basin_plan_center"]
    pp = portus_params()
    r_in, r_out, HWR = pp["r_in"], pp["r_out"], pp["hwr"]
    iso = _siso("L6")
    # 1 육각 내항(육지): 포장 둘레·성벽·창고 고리(붉은 기와)·부두·물
    pave = hexring(hx, hy, HR)
    iso.poly3([(x, y, 0) for x, y in pave], fill=(216, 202, 170), ol=(150, 130, 98), lw=0.25)
    wall = Mesh(None)
    # 22:33: 운하는 +X(변 5)·−X(변 2) 쪽 변 가운데로 지난다 → 그 두 변은 가운데(0.44~0.56, 변 24mm 중 약 2.9mm 위로 개구 3mm 이상)를 비운다
    trims = {2: [(0.0, 0.42), (0.58, 1.0)], 5: [(0.0, 0.42), (0.58, 1.0)]}
    for k in range(6):
        a0p, b0p = pave[k], pave[(k + 1) % 6]
        for (f0, f1) in trims.get(k, [(0.0, 1.0)]):
            a, b = lerp(a0p, b0p, f0), lerp(a0p, b0p, f1)
            wall.extend(m_prism([a, b, lerp(b, (hx, hy), 0.04), lerp(a, (hx, hy), 0.04)], 0, 1.4, (198, 176, 140), top=(214, 196, 162)))
    iso.poly3([(x, y, 0.3) for x, y in hexring(hx, hy, HWR + 1.4)], fill=(206, 194, 168), ol=(150, 132, 104), lw=0.18)
    water = [(x, y, 0.32) for x, y in hexring(hx, hy, HWR)]
    wp = [iso.p(*p) for p in water]
    P.poly(wp, fill=HARBOR_C, outline=(96, 136, 166), lw=0.2)
    facet_fill(P, wp, HARBOR_C, cell=3.2, amp=0.05, key="육각물", jit=0.12)
    wh = Mesh(None)
    for k in range(6):
        a0_, a1_ = math.radians(30 + 60 * k), math.radians(30 + 60 * (k + 1))
        pieces = [(0.06, 0.46), (0.54, 0.94)]
        if k in (2, 5):          # 운하가 지나는 변: 가운데 폭 약 3.5mm 이상 비운다
            pieces = [(0.06, 0.40), (0.60, 0.94)]
        for (f0, f1) in pieces:
            q = []
            for (r, f) in ((17.2, f0), (17.2, f1), (22.0, f1), (22.0, f0)):
                pa = (hx + r * math.cos(a0_), hy + r * math.sin(a0_))
                pb = (hx + r * math.cos(a1_), hy + r * math.sin(a1_))
                q.append((pa[0] + (pb[0] - pa[0]) * f, pa[1] + (pb[1] - pa[1]) * f))
            wh.extend(m_prism(q, 0.3, 4.2, WALL_W))
            wh.extend(m_frustum(q, 4.2, 6.0, 0.5, ROOF))
    # 2 클라우디우스 외항 수면(바다 위): 방파제 안쪽
    cx_, cy_ = iso.p(bx, by, 0)
    P.ell(cx_, cy_, 1.2247 * (r_in + 0.6), 0.7071 * (r_in + 0.6), fill=HARBOR_C)
    # 3 운하 2개(사양 plan_x·plan_y): 강·외항 수면에서 육각 내항 수면 안쪽까지, 포장·안벽 위에 그려 폭 3mm 개구부를 낸다
    canal_info = []
    for c in pp["canals"]:
        (x0, x1), (y0, y1) = c["x"], c["y"]
        xa, xb = min(x0, x1), max(x0, x1)
        ya, yb_ = min(y0, y1), max(y0, y1)
        # 22:33 회전: 운하는 X축 방향(긴 쪽 x, 폭 y). 사양 plan_x 그대로 그린다(추가 연장 0)
        q = [iso.p(xa, ya, 0.33), iso.p(xb, ya, 0.33), iso.p(xb, yb_, 0.33), iso.p(xa, yb_, 0.33)]
        P.poly(q, fill=HARBOR_C)
        P.line([iso.p(xa, ya, 0.33), iso.p(xb, ya, 0.33)], (96, 136, 166), 0.15, joint=False)
        P.line([iso.p(xa, yb_, 0.33), iso.p(xb, yb_, 0.33)], (96, 136, 166), 0.15, joint=False)
        hexw = hexring(hx, hy, HWR)
        if xa > hx:          # 외항 쪽(+X): 육각 수면(안쪽 끝 xa) ↔ 외항 수면(바깥 끝 xb)
            e_hex, e_out = xa, xb
            ok_hex = all(in_poly((e_hex, y), hexw) for y in (y0, y1))
            ok_out = all(math.hypot(e_out - bx, y - by) < r_in for y in (y0, y1))
        else:                # 강 쪽(−X): 강(바깥 끝 xa) ↔ 육각 수면(안쪽 끝 xb)
            e_hex, e_out = xb, xa
            ok_hex = all(in_poly((e_hex, y), hexw) for y in (y0, y1))
            ok_out = e_out <= hx - 31.0          # 지도의 강은 원본 d5에서 −X 쪽으로 옮긴다(복사본 지도에는 아직 없음)
        canal_info.append({"name": c["name"], "continuous": bool(ok_hex and ok_out), "opening_w": round(y1 - y0, 2),
                           "screen_w": round((y1 - y0) * C30, 2), "plan_y": [round(ya, 2), round(yb_, 2)], "plan_x": [round(xa, 2), round(xb, 2)],
                           "plan_y_drawn": [round(ya, 2), round(yb_, 2)], "plan_y_spec": [round(ya, 2), round(yb_, 2)],
                           "end_dev_mm": 0.0, "render_extension_mm": 0.0})
    wall.draw(iso, lw=0.10)
    wh.draw(iso, lw=0.10)
    # 4 방파제 두 팔(마지막 조각을 끝각에서 정확히 자른다) + 창고·열주
    moles = Mesh(None)
    tip_polys = {}

    def mole_arc(t0, t1, key):
        n = max(1, int(math.ceil(abs(t1 - t0) / 6.15)))
        for i in range(n):
            ta = math.radians(t0 + (t1 - t0) * i / n)
            tb = math.radians(t0 + (t1 - t0) * (i + 1) / n)
            q = [(bx + r_in * math.cos(ta), by + r_in * math.sin(ta)), (bx + r_out * math.cos(ta), by + r_out * math.sin(ta)),
                 (bx + r_out * math.cos(tb), by + r_out * math.sin(tb)), (bx + r_in * math.cos(tb), by + r_in * math.sin(tb))]
            moles.extend(m_prism(q, -9.7, 0.0, (206, 196, 174)))          # d5: 바다 수면 −9.7부터(Blender coast·D12와 같은 바깥 면 9.7mm)
            if i == n - 1:
                tip_polys[key] = _hull([iso.p(x, y, -9.7) for x, y in q])          # 수면(−9.7) 높이 팔 끝 외곽
    mole_arc(pp["arm_a"][0], pp["arm_a"][1], "arm_a")
    mole_arc(pp["arm_b"][0], pp["arm_b"][1], "arm_b")
    rm = (r_in + r_out) / 2.0
    for th in (60.0, 75.0, 90.0, 105.0, 120.0):                     # 바다 쪽 방파제(팔 A) 위 창고(옛 150~210°에서 −90°)
        t = math.radians(th)
        Xc, Yc = bx + rm * math.cos(t), by + rm * math.sin(t)
        moles.extend(m_box(Xc - 1.2, Yc - 1.2, 0.0, Xc + 1.2, Yc + 1.2, 1.9, (230, 210, 180)))
        moles.extend(m_frustum([(Xc - 1.3, Yc - 1.3), (Xc + 1.3, Yc - 1.3), (Xc + 1.3, Yc + 1.3), (Xc - 1.3, Yc + 1.3)], 1.9, 3.1, 0.4, ROOF))
    c0, c1 = pp["col"]
    th = c0
    while th <= c1 + 1e-6:                                          # 열주: 팔 B의 12~54°에만
        t = math.radians(th)
        moles.extend(m_cyl(bx + rm * math.cos(t), by + rm * math.sin(t), 0.35, 0.0, 2.6, (240, 232, 214), n=6))
        th += 7.0
    # 5 등대섬(사양 평면 각·반지름): 섬 + 층을 쌓은 탑 + 등롱
    LX, LY = bx + pp["lr"] * math.cos(math.radians(pp["ang"])), by + pp["lr"] * math.sin(math.radians(pp["ang"]))
    tower = Mesh(None)
    tower.extend(m_cyl(LX, LY, pp["isl"], -9.7, -0.4, (150, 140, 124), n=16))                # d5: 섬 옆면을 바다 수면 −9.7까지(Blender coast와 같은 깊이)
    tower.extend(m_mound(LX, LY, -0.4, pp["isl"], 1.4, (150, 140, 124), key="등대섬"))
    for (r, z0, z1) in pp["tiers"]:
        tower.extend(m_cyl(LX, LY, r * 0.82, z0, z1, (236, 226, 204), n=8, top=(246, 238, 220)))
    r_l, z0_l, z1_l = pp["lant"]
    tower.extend(m_cyl(LX, LY, r_l * 0.9, z0_l, z1_l, (236, 226, 204), n=8))
    tower.extend(m_cone(LX, LY, r_l * 1.05, z1_l, 1.4, (196, 92, 64), n=8))
    moles.draw(iso, lw=0.10)
    tower.draw(iso, lw=0.10)
    for k_, (r, z0, z1) in enumerate(pp["tiers"]):
        zc = (z0 + z1) / 2.0
        cx2, cy2 = iso.p(LX + r * 0.82 * 0.7071, LY + r * 0.82 * 0.7071, zc)
        P.rect(cx2 - 0.4, cy2 - 0.8, cx2 + 0.4, cy2 + 0.8, fill=(110, 90, 70))
    lx, ly = iso.p(LX, LY, (z0_l + z1_l) / 2.0)
    soft_ell(P, lx, ly, 2.0, 1.6, (255, 214, 110), alpha=120, blur=0.5)
    P.dot(lx, ly, 0.55, (250, 196, 70))
    # 사용자 16:14: 포르투스 안의 배(돛배 4)는 지도에서 지웠다
    # 6 기록: 외곽·입구 폭·섬 양옆 물길·운하
    fps = []
    for key, (t0, t1) in (("팔 A", pp["arm_a"]), ("팔 B", pp["arm_b"])):
        n = max(8, int(abs(t1 - t0) / 3))
        ts = [t0 + (t1 - t0) * i / n for i in range(n + 1)]
        top = [iso.p(*_polar2(bx, by, r_out, t), 1.0) for t in ts] + [iso.p(*_polar2(bx, by, r_in, t), 1.0) for t in reversed(ts)]
        face = [iso.p(*_polar2(bx, by, r_out, t), 1.0) for t in ts] + [iso.p(*_polar2(bx, by, r_out, t), -0.4) for t in reversed(ts)]
        fps += [top, face]
        add_fp("포르투스 외항 방파제 %s 윗면" % key, top, "대상 면")
        add_fp("포르투스 외항 방파제 %s 바깥 면" % key, face, "대상 면")
    GEO["fpset_포르투스 외항 방파제"] = fps
    isl_fp = [iso.p(LX + pp["isl"] * math.cos(math.radians(t)), LY + pp["isl"] * math.sin(math.radians(t)), -9.7) for t in range(0, 360, 10)]
    add_fp("포르투스 등대섬", isl_fp, "섬")
    add_fp("포르투스 육각 내항", [iso.p(x, y, 0) for x, y in pave], "지면")
    ea, eb = tip_polys.get("arm_a"), tip_polys.get("arm_b")

    def face_seg(e_deg):
        return (iso.p(*_polar2(bx, by, r_in, e_deg), 0.0), iso.p(*_polar2(bx, by, r_out, e_deg), 0.0))
    sa, sb = face_seg(pp["arm_a"][1]), face_seg(pp["arm_b"][1])
    ent = min(math.hypot(p[0] - q[0], p[1] - q[1]) for p in sa for q in sb)
    ent_x = abs(sb[1][0] - sa[1][0])
    gw = [round(_poly_dist(isl_fp, ea), 2) if ea else None, round(_poly_dist(isl_fp, eb), 2) if eb else None]
    tower_fp = _hull([iso.p(LX + r * 0.82 * math.cos(math.radians(t)), LY + r * 0.82 * math.sin(math.radians(t)), z)
                      for (r, z0, z1) in pp["tiers"] for z in (z0, z1) for t in range(0, 360, 45)])
    gw_tower = [round(_poly_dist(tower_fp, ea), 2) if ea else None, round(_poly_dist(tower_fp, eb), 2) if eb else None]
    DRAWN["portus"] = {"entrance_w": round(ent, 2), "entrance_screen_x_w": round(ent_x, 2), "island_water": gw,
                       "island_water_rule": "바다 수면 높이(z −9.7, D12)에서 등대섬 외곽 ↔ 두 팔 끝 조각 외곽의 화면 거리(팔 A, 팔 B)",
                       "tower_to_arm_tips": gw_tower, "canals": canal_info,
                       "arm_end_deg": [pp["arm_a"][1] % 360, pp["arm_b"][1] % 360], "colonnade_deg": [c0, c1],
                       "lighthouse_plan": [round(LX, 2), round(LY, 2)], "lighthouse_screen_base": [round(v, 2) for v in iso.p(LX, LY, 0)]}
    pts = [iso.p(x, y, 6.0) for x, y in pave] + [iso.p(x, y, 0) for x, y in pave] + [iso.p(LX, LY, z1_l + 1.4)]
    for t in range(0, 360, 10):
        pts.append(iso.p(bx + r_out * math.cos(math.radians(t)), by + r_out * math.sin(math.radians(t)), 0))
    pts += isl_fp
    bb = bbox_of(pts)
    GEO["portus_basin_c"] = (cx_, cy_)
    GEO["portus_light"] = iso.p(LX, LY, 0)
    record("L6", L6["name"], "Core(표준 랜드마크)", L6["projected_box"], bb)


def _polar2(cx, cy, r, deg):
    return (cx + r * math.cos(math.radians(deg)), cy + r * math.sin(math.radians(deg)))


HERO_IN = sget(HERO, "interior", default=None) or sget(CM, "hero_interior", default=None) or {}
SQ2 = math.sqrt(2.0)


def clip_convex(subject, clip):
    """Sutherland–Hodgman: subject 다각형을 볼록 다각형 clip 안으로 자른다"""
    if len(clip) < 3 or len(subject) < 3:
        return []
    area = sum(clip[i][0] * clip[(i + 1) % len(clip)][1] - clip[(i + 1) % len(clip)][0] * clip[i][1] for i in range(len(clip)))
    cl = clip if area > 0 else clip[::-1]

    def inside(p, a, b):
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= 0

    def inter(p, q, a, b):
        x1, y1, x2, y2 = p[0], p[1], q[0], q[1]
        x3, y3, x4, y4 = a[0], a[1], b[0], b[1]
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(den) < 1e-12:
            return q
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
    out = list(subject)
    for i in range(len(cl)):
        a, b = cl[i], cl[(i + 1) % len(cl)]
        inp, out = out, []
        if not inp:
            break
        s_ = inp[-1]
        for e in inp:
            if inside(e, a, b):
                if not inside(s_, a, b):
                    out.append(inter(s_, e, a, b))
                out.append(e)
            elif inside(s_, a, b):
                out.append(inter(s_, e, a, b))
            s_ = e
    return out


def _num_in(text, default):
    m = re.search(r"간격\s*([\d.]+)", str(text or ""))
    return float(m.group(1)) if m else default


def draw_hypogeum_d5(L):
    """하이포게움(경기장 u < −2.0, 바닥 Z −4.0): 동심 타원 벽(경기장 반축의 0.86·0.72·0.58·0.44·0.30배), 중앙 통로(장축 ±0.9),
    방사 칸막이(12°마다, 0.33~0.97), 벽 두께 0.45~0.55(roma_colo_in.build_arena와 같은 자리). 구덩이 입구(파라펫 윗선)로만 보인다.
    돌려줌: 기록(drawn.json hypogeum)"""
    a, b = CO_AR
    t0 = math.acos(max(-1.0, min(1.0, CO_US / a)))
    zt_ = HY["z_top"]
    sub = Layer(CX_S - HS * KU * a - 3, CY_S - HS * KV * b - 8 * HS, CX_S + 3, CY_S + HS * KV * b + 6 * HS)
    pit = [uvz(a * math.cos(t), b * math.sin(t), CO_ZP) for t in [t0 + (2 * math.pi - 2 * t0) * k / 64 for k in range(65)]]
    sub.poly(pit, fill=H_DEEPER)
    walls = []

    def wall(u0, v0, u1, v1, t, kind):
        du, dv = u1 - u0, v1 - v0
        ln = math.hypot(du, dv)
        if ln < 0.2:
            return
        nu, nv = -dv / ln * t / 2.0, du / ln * t / 2.0                  # 두께 방향(국소)
        if nv < 0:
            nu, nv = -nu, -nv                                            # 보이는 옆면 = +v 쪽
        face = [uvz(u0 + nu, v0 + nv, CO_ZP), uvz(u1 + nu, v1 + nv, CO_ZP), uvz(u1 + nu, v1 + nv, zt_), uvz(u0 + nu, v0 + nv, zt_)]
        top = [uvz(u0 - nu, v0 - nv, zt_), uvz(u1 - nu, v1 - nv, zt_), uvz(u1 + nu, v1 + nv, zt_), uvz(u0 + nu, v0 + nv, zt_)]
        walls.append(((v0 + v1) / 2.0, face, top, ftone(H_TUFF, nu / (t / 2.0), nv / (t / 2.0)), kind))
    rings = []
    for fr in HY["rings"]:
        q = [(a * fr * math.cos(t), b * fr * math.sin(t)) for t in [t0 + (2 * math.pi - 2 * t0) * k / 32 for k in range(33)]]
        for k in range(32):
            wall(q[k][0], q[k][1], q[k + 1][0], q[k + 1][1], HY["t_ring"], "동심")
        rings.append({"fr": fr, "semi_axes": [round(a * fr, 3), round(b * fr, 3)], "u_max": round(a * fr * math.cos(t0), 3)})
    corr = []
    for sgn in (-1, 1):
        wall(CO_US - 0.2, sgn * HY["corr"], -a * 0.97, sgn * HY["corr"], HY["t_corr"], "통로")
        corr.append({"v": sgn * HY["corr"], "u": [round(CO_US - 0.2, 3), round(-a * 0.97, 3)]})
    parts = []
    ang = math.degrees(t0) + 10.0
    r0f, r1f = HY["r_frac"]
    while ang < 360.0 - math.degrees(t0) - 6.0:
        t = math.radians(ang)
        ub, vb = math.cos(t), -math.sin(t)                               # Blender (u, v) → 국소 (u, −v)
        p0 = (a * r0f * ub, b * r0f * vb)
        p1 = (a * r1f * ub, b * r1f * vb)
        wall(p0[0], p0[1], p1[0], p1[1], HY["t_part"], "칸막이")
        parts.append({"blender_deg": round(ang, 2), "p0_uv": [round(p0[0], 3), round(p0[1], 3)], "p1_uv": [round(p1[0], 3), round(p1[1], 3)],
                      "p0": [round(v_, 2) for v_ in uvz(p0[0], p0[1], zt_)], "p1": [round(v_, 2) for v_ in uvz(p1[0], p1[1], zt_)]})
        ang += HY["every"]
    walls.sort(key=lambda w: w[0])
    for _v, face, top, col, kind in walls:
        sub.poly(face, fill=col)
        sub.poly(top, fill=(196, 178, 148))
    # 구덩이 입구(파라펫 윗선 z 5.1, u < −2.0)로만 보인다
    m = Image.new("L", (sub.w, sub.h), 0)
    hole = [uvz(a * math.cos(t), b * math.sin(t), 5.1) for t in [t0 + (2 * math.pi - 2 * t0) * k / 64 for k in range(65)]]
    ImageDraw.Draw(m).polygon([sub.P(p) for p in hole], fill=255)
    sub.img.putalpha(ImageChops.multiply(sub.img.getchannel("A"), m))
    L.paste(sub)
    return {"floor_z": CO_ZP, "u_split": CO_US, "arena_semi_axes": [round(a, 3), round(b, 3)], "wall_top_z": round(zt_, 3),
            "wall_t": {"concentric": HY["t_ring"], "corridor": HY["t_corr"], "partition": HY["t_part"]},
            "concentric": rings, "concentric_count": len(rings), "corridor": corr, "corridor_half_w": HY["corr"],
            "partitions": parts, "partition_count": len(parts), "partition_every_deg": HY["every"], "partition_r_frac": [r0f, r1f],
            "rule": "roma_colo_in.build_arena와 같은 자리(국소 u = 장축, v = −Blender v). 동심 벽은 t0~2π−t0 호, 칸막이는 t0+10°부터 12°마다"}


def ftone(col, nu, nv):
    """수직 면 평면색(빛 계산 없음): 바깥 법선 (nu, nv)의 평면 방위로 오른면 0.68(+X) ~ 왼면 0.86(+Y) 사이 고정 톤(기준선 1.1 ISO_TONE)"""
    nX, nY = (nu + nv) * KV, (nv - nu) * KV
    a = math.degrees(math.atan2(nY, nX))
    f = 0.68 + 0.18 * max(0.0, min(1.0, a / 90.0))
    return tuple(max(0, min(255, int(round(c * f)))) for c in col[:3])


def _hi(col, f=1.12):
    return tuple(max(0, min(255, int(round(c * f)))) for c in col[:3])


H_TRV, H_TRV_HI, H_TRV_LO = (216, 185, 142), (232, 208, 168), (201, 165, 122)      # PAL trav·trav_hi·trav_lo
H_DEEP, H_DEEPER, H_VOID = (140, 107, 75), (110, 80, 56), (78, 58, 43)             # L1 깊이색(아치 속·구덩이·무너진 볼트 빈칸)
H_TUFF, H_BRICK = (168, 149, 122), (184, 111, 76)
H_FIN = (176, 132, 100)                                                            # 방사벽(벽돌 + 응회암, 차분한 톤)
H_SEAT, H_RISER = (228, 208, 170), (196, 168, 128)
H_WOOD, H_WOOD_DK = (169, 123, 79), (126, 90, 57)


def _strip(L, s0, s1, d, z_fn, z0, col_fn, n=3):
    """호 s0~s1, 깊이 d의 수직 면(아래 z0, 위 z_fn(s)). col_fn(nu, nv) → 색"""
    for k in range(n):
        sa, sb = s0 + (s1 - s0) * k / n, s0 + (s1 - s0) * (k + 1) / n
        sm = (sa + sb) / 2.0
        _u, _v, nu, nv, _tu, _tv = e_frame(sm)
        za, zb = (z0(sa), z0(sb)) if callable(z0) else (z0, z0)
        L.poly([M(sa, d, za), M(sb, d, zb), M(sb, d, z_fn(sb)), M(sa, d, z_fn(sa))], fill=col_fn(nu, nv))


def _cap(L, s0, s1, d0, d1, z_fn, col, n=3):
    """윗면 띠(호 s0~s1, 깊이 d0~d1, 높이 z_fn(s))"""
    ss = [s0 + (s1 - s0) * k / n for k in range(n + 1)]
    L.poly([M(s, d0, z_fn(s)) for s in ss] + [M(s, d1, z_fn(s)) for s in ss[::-1]], fill=col)


def _arch_poly(sc, d, x0, x1, ob, sp_, ra, ztop_fn, n=10):
    """칸 안 아치 개구부(호 sc+x, 깊이 d). 윗선 아래 0.35mm까지만(무너진 칸은 잘린 아치)"""
    cx = (x0 + x1) / 2.0
    pts = [(x0, ob), (x0, sp_)] + [(cx + ra * math.cos(math.pi - math.pi * k / n), sp_ + ra * math.sin(math.pi - math.pi * k / n)) for k in range(1, n)] + [(x1, sp_), (x1, ob)]
    out = []
    for x, z in pts:
        zc = ztop_fn(sc + x) - 0.35
        out.append(M(sc + x, d, min(z, zc)))
    return out


def draw_colosseum_d5():
    """콜로세움 건물(결정 D2): 칸 40, θ별 외벽 높이, 둘째 고리, 셋째 고리, 관람석(계단석 / 방사벽 + 짙은 빈칸), 포디움,
    나무 바닥 55% + 난간, 하이포게움. 뒤 반쪽은 바깥 → 안쪽, 앞 반쪽은 안쪽 → 바깥 순으로 그린다(등각 화가 순서).
    돌려줌: (건물 층, 기록)"""
    BL = Layer(CO_BOX[0] - 8, CO_BOX[1] - 6, CO_BOX[2] + 8, CO_BOX[3] + 8, "콜로세움 건물")
    T1, D2_, T2 = CO_T1, CO_D2, CO_T2
    DC0, DC1 = CO_DC
    ZT, ZB = CO_ZC
    DP0, DP1 = CO_DP
    back = sorted([b for b in BAYS if b["back"]], key=lambda b: b["v"])
    front = sorted([b for b in BAYS if not b["back"]], key=lambda b: -b["v"])        # 앞 반쪽: 안쪽(먼 쪽) 칸부터
    nb = len(BAYS)

    def zt(b, d):
        return ZB + (DC1 - d) / (DC1 - DC0) * (b["ztop"] - ZB)

    def zw1(b):
        return lambda s: z_wall(b, s, 1)

    def zw2(b):
        return lambda s: z_wall(b, s, 2)

    def ends(b, which, d0, d1):
        """칸 경계 단면(이웃과 높이가 다른 곳, 보이는 쪽만)"""
        for side in (0, 1):
            nbb = BAYS[(b["i"] + (1 if side else -1)) % nb]
            s_ = b["s1"] if side else b["s0"]
            za = z_wall(b, s_, which)
            zb_ = z_wall(nbb, s_ if side else nbb["s1"], which)
            if za <= zb_ + 0.3:
                continue
            _u, _v, _nu, _nv, tu, tv = e_frame(s_)
            nu_, nv_ = (tu, tv) if side else (-tu, -tv)
            if nv_ <= 0.02:
                continue
            BL.poly([M(s_, d0, zb_), M(s_, d1, zb_), M(s_, d1, za), M(s_, d0, za)], fill=ftone(H_TUFF, nu_, nv_))

    def outer_wall(b, face_d, front_face):
        s0, s1, sc = b["s0"], b["s1"], b["sc"]
        f = zw1(b)
        _strip(BL, s0, s1, face_d, f, 0.0, lambda nu, nv: ftone(H_TRV, nu, nv) if front_face else ftone(H_TRV_LO, -nu, -nv))
        _u, _v, nu, nv, tu, tv = e_frame(sc)
        for k, s_ in enumerate(CO_ST):
            if s_["z0"] >= b["H1"] - 0.2:
                break
            if s_["ob"] is not None:
                if b["H1"] > s_["ob"] + 0.8:
                    BL.poly(_arch_poly(sc, face_d, -CO_RA, CO_RA, s_["ob"], s_["sp"], CO_RA, f), fill=H_DEEP)
                    if front_face:                                       # 보이는 쪽 문설주(벽 두께, L2)
                        for sx, (ju, jv) in ((1, (-tu, -tv)), (-1, (tu, tv))):
                            if jv > 0.02:
                                xj = sx * CO_RA
                                ztp = min(s_["sp"], z_wall(b, sc + xj, 1) - 0.35)
                                if ztp > s_["ob"] + 0.3:
                                    BL.poly([M(sc + xj, 0.0, s_["ob"]), M(sc + xj, min(T1, 1.6), s_["ob"]), M(sc + xj, min(T1, 1.6), ztp), M(sc + xj, 0.0, ztp)],
                                            fill=ftone(H_TRV_LO, ju, jv))
                    if front_face and b["H1"] > s_["sp"] + CO_RA + 0.5:     # 쐐기돌(L2)
                        BL.poly([M(sc - 0.28, -0.05, s_["sp"] + CO_RA - 0.15), M(sc + 0.28, -0.05, s_["sp"] + CO_RA - 0.15),
                                 M(sc + 0.28, -0.05, s_["sp"] + CO_RA + 0.55), M(sc - 0.28, -0.05, s_["sp"] + CO_RA + 0.55)], fill=_hi(ftone(H_TRV, nu, nv), 1.08))
            elif b["i"] % 2 == 0 and b["H1"] > s_["z0"] + 9.8:               # 아티카 창(짝수 칸)
                w2 = 0.17 * CO_W
                BL.poly([M(sc - w2, face_d, s_["z0"] + 6.4), M(sc + w2, face_d, s_["z0"] + 6.4), M(sc + w2, face_d, s_["z0"] + 9.6), M(sc - w2, face_d, s_["z0"] + 9.6)],
                        fill=H_DEEP)
            if not front_face:
                continue
            trunc = b["H1"] < s_["z1"] - 0.05
            ztop_ = min(s_["z1"] - s_["ent"], b["H1"])
            cz0 = s_["z0"] + (0.0 if s_["order"] == "T" else 1.25)
            if s_["order"] in "TIC" and ztop_ - cz0 > 0.6:                   # 반원기둥(칸 왼쪽 끝, L2) + 밝은 띠(L5)
                s_c = s0
                zc_ = min(ztop_, z_wall(b, s_c + 0.5, 1) - 0.2)
                BL.poly([M(s_c - 0.5, -0.45, cz0), M(s_c + 0.5, -0.45, cz0), M(s_c + 0.5, -0.45, zc_), M(s_c - 0.5, -0.45, zc_)], fill=_hi(ftone(H_TRV, nu, nv), 1.04))
                BL.line([M(s_c + 0.12, -0.5, cz0 + 0.2), M(s_c + 0.12, -0.5, zc_ - 0.1)], _hi(ftone(H_TRV, nu, nv), 1.16), 0.25, joint=False)
            elif s_["order"] == "A" and ztop_ - s_["z0"] > 0.6:              # 아티카 벽기둥
                zc_ = min(ztop_, z_wall(b, s0 + 0.45, 1) - 0.2)
                BL.poly([M(s0 - 0.45, -0.3, s_["z0"]), M(s0 + 0.45, -0.3, s_["z0"]), M(s0 + 0.45, -0.3, zc_), M(s0 - 0.45, -0.3, zc_)], fill=_hi(ftone(H_TRV, nu, nv), 1.03))
            if not trunc:                                                    # 엔타블러처 + 코니스(L2) + 코니스 윗선(L5)
                ss = [s0 + (s1 - s0) * j / 3.0 for j in range(4)]
                BL.poly([M(s, -0.6, s_["z1"] - s_["ent"]) for s in ss] + [M(s, -0.6, s_["z1"] - 0.42) for s in ss[::-1]], fill=_hi(ftone(H_TRV, nu, nv), 0.97))
                BL.poly([M(s, -0.9, s_["z1"] - 0.42) for s in ss] + [M(s, -0.9, s_["z1"]) for s in ss[::-1]], fill=_hi(ftone(H_TRV, nu, nv), 1.06))
                BL.line([M(s, -0.95, s_["z1"] - 0.05) for s in ss], _hi(ftone(H_TRV, nu, nv), 1.18), 0.3)
            if b["H1"] >= s_["z1"] - 0.05 and _rnd(b["i"], 200 + k) > 0.45:   # 빗물 자국(L6)
                Ls_ = 1.4 + 3.4 * _rnd(b["i"], 210 + k)
                xs_ = CO_RA + 0.1
                zt0 = s_["z1"] - s_["ent"]
                BL.poly([M(sc + xs_, -0.02, zt0 - Ls_), M(sc + xs_ + 0.32, -0.02, zt0 - Ls_), M(sc + xs_ + 0.32, -0.02, zt0), M(sc + xs_, -0.02, zt0)],
                        fill=tint(ftone(H_TRV, nu, nv), 0.9))
        _cap(BL, s0, s1, 0.0, T1, f, H_TRV_HI)                              # 윗면(L5 밝은 갓돌)
        BL.line([M(s, 0.0 if front_face else T1, f(s) + 0.02) for s in (s0, (s0 + s1) / 2.0, s1)], _hi(H_TRV_HI, 1.06), 0.3)
        ends(b, 1, 0.0, T1)

    def ring2(b, face_d, front_face):
        s0, s1, sc = b["s0"], b["s1"], b["sc"]
        f = zw2(b)
        _strip(BL, s0, s1, face_d, f, 0.0, lambda nu, nv: ftone(H_TRV_LO, nu, nv) if front_face else ftone(H_TRV_LO, -nu, -nv))
        for k, s_ in enumerate(CO_ST[:3]):
            if s_["z0"] >= b["H2"] - 0.2:
                break
            ob = s_["z0"] if k == 0 else s_["z0"] + 0.9
            if b["H2"] > ob + 0.8:
                BL.poly(_arch_poly(sc, face_d, -CO_RA * 0.92, CO_RA * 0.92, ob, s_["sp"] - 0.6, CO_RA * 0.92, f), fill=H_DEEP)
        _cap(BL, s0, s1, D2_, D2_ + T2, f, H_TRV_HI)
        ends(b, 2, D2_, D2_ + T2)

    def corridor(b):
        s0, s1 = b["s0"], b["s1"]
        _cap(BL, s0 + 0.05, s1 - 0.05, T1, D2_, lambda s: 0.02, H_DEEPER)
        zv = None
        mn = min(b["H1"], b["H2"])
        for s_ in CO_ST[:3]:
            if s_["z1"] <= mn + 0.05:
                zv = s_["z1"]
        if zv is not None:                                                 # 회랑 천장 볼트(두 고리가 모두 남은 층)
            _cap(BL, s0, s1, T1 - 0.05, D2_ + 0.05, lambda s: zv, H_TUFF)
        return zv

    def ring3(b, face_d, front_face):
        s0, s1 = b["s0"], b["s1"]
        zr = b["ztop"] + 1.5
        _strip(BL, s0, s1, face_d, lambda s: zr, (b["ztop"] - 0.6) if not front_face else 0.0,
               lambda nu, nv: ftone(H_TUFF, nu, nv) if front_face else ftone(H_TUFF, -nu, -nv), n=2)
        _cap(BL, s0, s1, CO_D3[0], CO_D3[1], lambda s: zr, _hi(H_TUFF, 1.12), n=2)

    def cavea(b, front_face):
        """관람석 세 띠(roma_colo_in.build): 위 10.4~15.5 무너진 볼트 빈칸(일부 볼트), 가운데 15.5~19.5 볼트(60%) 또는 빈칸, 아래 계단석.
        계단석 구역(238~360°·0~48°)은 11.4부터 계단석. 돌려줌: 이 칸의 띠 기록"""
        s0, s1, i = b["s0"] + 0.5, b["s1"] - 0.5, b["i"]
        DU, DM = 15.5, 19.5
        ss = seat_sector(b["th"])
        rec = {"i": i, "th": round(b["th"], 2), "ztop": round(b["ztop"], 2), "seat": ss}
        bands = []
        bands.append((DC0, DU, "볼트" if _rnd(i, 21) > 0.72 else "빈칸"))
        bands.append((DU, DM, "볼트" if (_rnd(i, 22) > 0.4 or ss) else "빈칸"))
        d_from = DC0 + 1.0 if ss else DM
        order = bands if not front_face else bands[::-1]
        for (da, db_, kind) in order:
            if ss and da >= d_from - 0.01:
                continue
            ss_ = [s0 + (s1 - s0) * k / 2.0 for k in range(3)]
            if kind == "볼트":
                BL.poly([M(s, da, zt(b, da)) for s in ss_] + [M(s, db_, zt(b, db_)) for s in ss_[::-1]], fill=(186, 166, 134))
            else:
                BL.poly([M(s, da, zt(b, da)) for s in ss_] + [M(s, db_, zt(b, db_)) for s in ss_[::-1]], fill=H_VOID)
                BL.poly([M(s, da + 0.3, zt(b, da) - 1.6) for s in ss_] + [M(s, db_ - 0.3, zt(b, db_) - 1.6) for s in ss_[::-1]], fill=(64, 48, 36))
        nst = max(2, int(round((DC1 - d_from) / 0.56)))
        steps = [(d_from + j * (DC1 - d_from) / nst, d_from + (j + 1) * (DC1 - d_from) / nst) for j in range(nst)]
        if front_face:
            steps = steps[::-1]
        ss_ = [s0 + (s1 - s0) * k / 2.0 for k in range(3)]
        _u, _v, nu, nv, _tu, _tv = e_frame(b["sc"])
        for (d0, d1) in steps:
            z = zt(b, d0)
            BL.poly([M(s, d0, z) for s in ss_] + [M(s, d1, z) for s in ss_[::-1]], fill=H_SEAT)
            if not front_face:                                               # 챌면(안쪽을 본다 = 보는 사람 쪽)
                z1_ = zt(b, d1)
                BL.poly([M(s, d1, z1_) for s in ss_] + [M(s, d1, z) for s in ss_[::-1]], fill=ftone(H_RISER, -nu, -nv))
        for dd in ((3.0, 6.2, 9.4) if ss else (DM - DC0 + 1.4,)):          # 발테우스(낮은 벽, L2) + 윗선(L5)
            d_ = DC0 + dd
            if d_ < d_from:
                continue
            z = zt(b, d_)
            BL.poly([M(s, d_ - 0.35, z + 1.1) for s in ss_] + [M(s, d_ + 0.15, z + 1.1) for s in ss_[::-1]], fill=H_TRV_HI)
            if not front_face:
                BL.poly([M(s, d_ + 0.15, z - 0.3) for s in ss_] + [M(s, d_ + 0.15, z + 1.1) for s in ss_[::-1]], fill=ftone(H_TRV, -nu, -nv))
        rec["bands"] = [k for _a, _b, k in bands]
        rec["seat_from_d"] = round(d_from, 2)
        return rec

    def fin(b, front_face):
        """방사벽(칸 경계, 벽돌): 윗선 2단 + 밝은 갓돌(L5). 보이는 옆면만"""
        s_ = b["s0"]
        Lf = DC1 - DC0 - 1.2
        hi = 1.6 if seat_sector(b["th"]) else 2.6
        zA, zB = zt(b, DC0) + hi, zt(b, DC1 - 1.2) + hi * 0.6
        dm = DC0 + Lf * 0.55
        zm = zB + (zA - zB) * 0.45
        prof = [(DC0, zA), (dm, zm + 0.9), (dm, zm), (DC1 - 1.2, zB)]
        _u, _v, _nu, _nv, tu, tv = e_frame(s_)
        sgn = 1.0 if tv > 0 else -1.0
        sx = s_ + 0.5 * sgn
        nu_, nv_ = tu * sgn, tv * sgn
        lo = [(d, zt(b, d) - (2.4 if d < 19.5 else 0.0)) for d, _z in prof]
        BL.poly([M(sx, d, z) for d, z in prof] + [M(sx, d, z) for d, z in lo[::-1]], fill=ftone(H_FIN, nu_, nv_))
        for (da, za), (db_, zb_) in ((prof[0], prof[1]), (prof[2], prof[3])):
            BL.poly([M(s_ - 0.55, da, za + 0.2), M(s_ + 0.55, da, za + 0.2), M(s_ + 0.55, db_, zb_ + 0.2), M(s_ - 0.55, db_, zb_ + 0.2)], fill=H_TRV_HI)

    def podium(b, front_face):
        s0, s1 = b["s0"], b["s1"]
        _u, _v, nu, nv, _tu, _tv = e_frame(b["sc"])
        if not front_face:                                                 # 안쪽 면(구덩이 쪽은 Z −4.0부터, 나무 바닥 쪽은 0.6부터)
            def zbase(s):
                u_, _v_ = e_uv(s, DP1)
                return CO_ZP if u_ < CO_US else CO_ZF
            _strip(BL, s0, s1, DP1, lambda s: 5.1, zbase, lambda nu_, nv_: ftone(H_TUFF, -nu_, -nv_), n=2)
            BL.line([M(s, DP1, 1.2) for s in (s0, s1)], tint(ftone(H_TUFF, -nu, -nv), 0.92), 0.12, joint=False)
        _cap(BL, s0, s1, DP0, DP1 - 0.45, lambda s: ZB, H_TRV, n=2)
        if front_face:
            _strip(BL, s0, s1, DP1 - 0.45, lambda s: 5.1, ZB, lambda nu_, nv_: ftone(H_TRV, nu_, nv_), n=2)
        _cap(BL, s0, s1, DP1 - 0.52, DP1 + 0.05, lambda s: 5.26, H_TRV_HI, n=2)

    def plinth(b):
        s0, s1 = b["s0"], b["s1"]
        for (da, db_, z0_, z1_) in ((-2.6, 0.2, 0.0, 0.32), (-1.4, 0.2, 0.32, 0.62)):
            _strip(BL, s0, s1, da, lambda s: z1_, z0_, lambda nu, nv: ftone(H_TRV, nu, nv), n=2)
            _cap(BL, s0, s1, da, db_, lambda s: z1_, H_TRV_HI, n=2)

    rec_bays, rec_cav = [], []
    # 1 뒤 반쪽(바깥 → 안쪽): 외벽 안쪽 면 → 회랑 → 둘째 고리 안쪽 면 → 셋째 고리 → 관람석 → 방사벽 → 포디움 안쪽 면
    for b in back:
        outer_wall(b, T1, False)
    for b in back:
        corridor(b)
    for b in back:
        ring2(b, D2_ + T2, False)
    for b in back:
        ring3(b, CO_D3[1], False)
    for b in back:
        rec_cav.append(cavea(b, False))
    for b in back:
        fin(b, False)
    for b in back:
        podium(b, False)
    # 2 경기장: 하이포게움(구덩이) → 나무 바닥 55%(Z 0.6) + 경계 난간
    hyrec = draw_hypogeum_d5(BL)
    a, bb_ = CO_AR
    t0 = math.acos(max(-1.0, min(1.0, CO_US / a)))
    floor = [uvz(a * math.cos(t), bb_ * math.sin(t), CO_ZF) for t in [-t0 + 2 * t0 * k / 64 for k in range(65)]]
    BL.poly(floor, fill=H_WOOD)
    for j in range(-12, 13):                                                # 널 줄눈(장축 방향, L3)
        v_ = j * 1.05
        if abs(v_) >= bb_ - 0.3:
            continue
        ue = a * math.sqrt(max(0.0, 1 - (v_ / bb_) ** 2)) - 0.25
        if ue > CO_US + 0.6:
            BL.line([uvz(CO_US + 0.3, v_, CO_ZF), uvz(ue, v_, CO_ZF)], (146, 104, 66), 0.12, joint=False)
    for k in range(9):                                                      # 널 이음(가로, 엇갈림)
        u_ = CO_US + 2.4 + k * 2.4
        for j in range(-11, 12, 2):
            v_ = (j + (0.5 if k % 2 else 0.0)) * 1.05
            if abs(v_) + 0.6 < bb_ * math.sqrt(max(0.0, 1 - (u_ / a) ** 2)):
                BL.line([uvz(u_, v_ - 0.5, CO_ZF), uvz(u_, v_ + 0.5, CO_ZF)], (150, 108, 70), 0.12, joint=False)
    vh = bb_ * math.sqrt(max(0.0, 1 - (CO_US / a) ** 2))
    for zz in (CO_ZF + 0.5, CO_ZF + 0.95):                                 # 난간 두 줄 + 기둥(L2)
        BL.line([uvz(CO_US + 0.1, -vh, zz), uvz(CO_US + 0.1, vh, zz)], H_WOOD_DK, 0.2, joint=False)
    for k in range(27):
        v_ = -vh + 2 * vh * k / 26
        BL.line([uvz(CO_US + 0.1, v_, CO_ZF), uvz(CO_US + 0.1, v_, CO_ZF + 1.05)], H_WOOD_DK, 0.15, joint=False)
    BL.line([uvz(CO_US + 0.1, -vh, CO_ZF + 1.0), uvz(CO_US + 0.1, vh, CO_ZF + 1.0)], (206, 168, 120), 0.12, joint=False)
    # 3 앞 반쪽(안쪽 → 바깥): 포디움 → 관람석 → 방사벽 → 셋째 고리 → 둘째 고리 바깥 면 → 회랑 → 외벽 바깥 면 → 기단 계단
    for b in front:
        podium(b, True)
    for b in front:
        rec_cav.append(cavea(b, True))
    for b in front:
        fin(b, True)
    for b in front:
        ring3(b, CO_D3[0], True)
    for b in front:
        ring2(b, D2_, True)
    for b in front:
        corridor(b)
    for b in front:
        outer_wall(b, 0.0, True)
    for b in front:
        plinth(b)
    for b in BAYS:
        rec_bays.append({"i": b["i"], "th": round(b["th"], 2), "h1": round(b["H1"], 2), "h2": round(b["H2"], 2), "ztop": round(b["ztop"], 2),
                         "tilt1": round(b["tg1"], 3), "tilt2": round(b["tg2"], 3), "half": "뒤" if b["back"] else "앞"})
    return BL, {"bays": rec_bays, "cavea": sorted(rec_cav, key=lambda r: r["i"]), "hypogeum": hyrec}


def _layer_sil(L, thr=128):
    """층 알파 → (외곽 상자, 면적 mm², 윤곽 다각형(≤ 96점), 열별 윗선 함수)"""
    a = np.array(L.img.getchannel("A")) >= thr
    ys, xs = np.nonzero(a)
    if len(xs) == 0:
        return None
    k = float(KD)
    box = (float(L.x0 + xs.min() / k), float(L.y0 + ys.min() / k), float(L.x0 + (xs.max() + 1) / k), float(L.y0 + (ys.max() + 1) / k))
    area = float(a.sum()) / (k * k)
    cnts, _h = cv2.findContours(a.astype(np.uint8) * 255, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    c = max(cnts, key=cv2.contourArea)
    eps = 0.3
    ap = cv2.approxPolyDP(c, eps * k, True)
    while len(ap) > 96:
        eps *= 1.3
        ap = cv2.approxPolyDP(c, eps * k, True)
    poly = [(L.x0 + float(p[0][0]) / k, L.y0 + float(p[0][1]) / k) for p in ap]
    tops = np.full(a.shape[1], -1, dtype=np.int64)
    has = a.any(axis=0)
    tops[has] = a[:, has].argmax(axis=0)

    def top_y(x):
        j = int(round((x - L.x0) * k))
        if j < 0 or j >= a.shape[1] or tops[j] < 0:
            return None
        return float(L.y0 + tops[j] / k)
    return box, area, poly, top_y


def _d5_height_check(rec_bays):
    """θ 구간별 그린 외벽 높이 ↔ 결정 D2 표(±0.5, 표에 적힌 변형 33.5·18.0~24.5·14.0~17.0 포함)"""
    segs = [("100~104°", 100, 104, [41.0]), ("104~108°", 104, 108, [46.0]), ("108~112°", 108, 112, [50.0]), ("112~205°", 112, 205, [53.0]),
            ("205~209°", 205, 209, [44.0]), ("209~322°", 209, 322, [37.0, 33.5]), ("322~330°", 322, 330, [31.0]), ("330~338°", 330, 338, [27.0]),
            ("338~18°", 338, 378, None), ("18~72°", 18, 72, None), ("72~80°", 72, 80, [30.0]), ("80~100°", 80, 100, [37.0])]
    out = {}
    for nm, a0, a1, allowed in segs:
        hs = []
        for r in rec_bays:
            th = r["th"] + 360.0 if (a1 > 360 and r["th"] < a1 - 360) else r["th"]
            if a0 <= th < a1:
                hs.append(r["h1"])
        if not hs:
            out[nm] = {"bays": 0}
            continue
        if allowed:
            ok = all(any(abs(h - v) <= 0.5 for v in allowed) for h in hs)
        elif nm.startswith("338"):
            ok = all(18.0 - 0.5 <= h <= 24.5 + 0.5 for h in hs)
        else:
            ok = all(14.0 - 0.5 <= h <= 17.0 + 0.5 for h in hs)
        out[nm] = {"bays": len(hs), "h": sorted(set(round(h, 2) for h in hs)), "ok": ok}
    return out




def col_sil_approx():
    """그리기 전 빈 자리 마스크용 콜로세움 실루엣(외곽 타원 + 칸별 윗선의 볼록 껍질)"""
    pts = []
    for b in BAYS:
        for s in (b["s0"], b["sc"], b["s1"]):
            pts.append(M(s, -2.6, 0.0))
            pts.append(M(s, 0.0, z_wall(b, s, 1)))
            pts.append(M(s, CO_D2, z_wall(b, s, 2)))
    return _hull(pts)






def _free_box(bb, pad=0.4):
    """사각 외곽이 빈 자리(EXCL)와 라벨 슬롯·Detail 상자와 겹치지 않는가"""
    if not poly_free(box_poly(bb), pad):
        return False
    for s in LBS["slots"]:
        b = s.get("box")
        if b and not (bb[2] < b[0] - 1.0 or bb[0] > b[2] + 1.0 or bb[3] < b[1] - 1.0 or bb[1] > b[3] + 1.0):
            return False
    return True











def _record_hero_group():
    """사용자 16:14: 히어로 = 콜로세움 건물(기단 계단 포함) 하나. 인물 무리·노점·공사장은 지도에서 지웠다 → objects 'hero_group'"""
    parts_ = list(GEO.get("hero_group_parts") or [])
    if not parts_:
        return
    u_ = (min(b_[0] for b_ in parts_), min(b_[1] for b_ in parts_), max(b_[2] for b_ in parts_), max(b_[3] for b_ in parts_))
    record("hero_group", "콜로세움 히어로(건물 + 기단 계단)", "Core(히어로 군)", u_, u_, "16:14 정의: 건물만")
    DRAWN.setdefault("hero", {})["group_box"] = [round(v, 2) for v in u_]


def draw_arena():
    """히어로(결정 D2 · 기준선 8.1 · 8.2): 받침 0(옆면·팔각 외곽·지층·앞 변 절개 없음). 지도 땅 위에 콜로세움 건물(기단 계단 2단 포함)만 둔다.
    사용자 16:13·16:14: 광장·둘레 나무·인물 무리·노점·공사장·길은 없다(Core 건축물만). 네로 거상 받침은 draw_colossus가 그린다."""
    sil0 = col_sil_approx()
    BL, crec = draw_colosseum_d5()
    P.paste(BL)
    sil = _layer_sil(BL)
    bbox_b, area_b, poly_b, top_y = sil if sil else (CO_BOX, 0.0, sil0, lambda x: None)
    wall_box0 = bbox_of([M(b["sc"] + x, 0.0, 0.0) for b in BAYS for x in (-CO_W / 2, 0.0, CO_W / 2)] +
                        [M(s, 0.0, z_wall(b, s, 1)) for b in BAYS for s in (b["s0"], b["sc"], b["s1"])])
    record("hero", HERO_NAME, "Core(히어로)", CO_BOX, wall_box0, "콜로세움 건물")
    SIL_MM2["hero"] = round(area_b, 1)
    SIL_MM2["hero_building"] = round(area_b, 1)
    GEO["hero_group_parts"] = [tuple(wall_box0)]
    wall_box = wall_box0
    add_fp("콜로세움 건물", poly_b, "건물")
    add_fp("콜로세움 외벽", poly_b, "대상 면")
    GEO["arena_top_y"] = lambda x: (None if top_y(x) is None else top_y(x))
    GEO["col_sil"] = poly_b
    ex_poly(poly_b, 1.5)
    hc = _d5_height_check(crec["bays"])
    DRAWN["hypogeum"] = crec["hypogeum"]
    DRAWN["hero"] = {
        "rule": "결정 D2(기준선 8.1·8.2, 사용자 16:13·16:14): 받침 0, 콜로세움 건물(기단 계단 2단 포함)만. 광장·둘레 나무·인물·노점·공사장·길 없음",
        "building": {"box": [round(v, 2) for v in bbox_b], "wall_box": [round(v, 2) for v in wall_box], "w": round(wall_box[2] - wall_box[0], 2),
                     "h": round(wall_box[3] - wall_box[1], 2), "sil_area_mm2": round(area_b, 1), "decision_box": list(CO_BOX),
                     "plinth": "기단 계단 2단(d −2.6~0.2, z 0~0.62)은 건물 상자 밖 띠로 그렸다"},
        "ellipse": {"center_plan": list(CO_C), "center_screen": [round(CX_S, 2), round(CY_S, 2)], "semi_axes": [CO_A, CO_B], "major_az_deg": 315,
                    "bays": CO_NB, "bay_w": round(CO_W, 3), "wall_t": CO_T1, "corridor_w": CO_G1, "ring2_t": CO_T2, "story_z": [s_["z1"] for s_ in CO_ST]},
        "heights_check": hc, "heights_ok": all(v.get("ok", True) for v in hc.values()),
        "bays": crec["bays"], "cavea": crec["cavea"],
        "arena": {"semi_axes": list(CO_ARS), "wood_u_min": CO_US, "wood_z": CO_ZF, "wood_share": round((CO_ARS[0] - CO_US) / (2 * CO_ARS[0]), 3), "rail": True},
        "gate_paths": [], "trees": [], "stalls": [], "scatter_people": [],
        "union_box": [round(v, 2) for v in wall_box], "union_area_mm2": round((wall_box[2] - wall_box[0]) * (wall_box[3] - wall_box[1]), 1),
        "union_parts": "콜로세움 건물(외벽 실루엣). 사용자 16:14: 인물 무리·노점·공사장은 지도에서 지웠다",
        "removed": ["콜로세움 받침(팔각 판·지층 옆면)", "앞 변 기초 절개", "원형 고리·동심 관람석 그릇", "가로벽 격자 하이포게움"],
    }
    REPORT["objects"]["hero_building"] = {"이름": "콜로세움 건물(외벽 실루엣, 기단 계단 띠 제외)", "그린 외곽": [round(v, 1) for v in wall_box],
                                          "기단 계단 포함 외곽": [round(v, 1) for v in bbox_b], "실루엣 면적mm²": round(area_b, 1)}


# ───────────────────────── 6 지도 소품(사양 props 10 + 공사장) ─────────────────────────


















# ───────────────────────── 7 Detail: 확대 창 Z1 · 콜아웃 C1·C2·C4 · 지시선 ─────────────────────────
MARK_R = 2.0           # 짝 표지 원 반지름
MARK_FACE = 2.2        # 짝 표지 글자면(주석 최소 2.05 이상)
DETAIL_FILL = (253, 248, 236, 238)


def mark(x, y, letter, r=MARK_R, layer="짝 표지", source="map", origin="", shape=None, chapter=False):
    """표지. 사용자 15:32·15:41: 형태 표지(1~4)는 숫자 없이 Ø4 형태 아이콘(아치·배럴 볼트·교차 볼트·돔), ❺ 근거 표지(5)는 Ø3.2 장 잉크 원 + 흰 '5'.
    texts에 role 'mark'로 글자(아이콘은 빈 글)·중심·출처(map/detail/panel)를 남긴다"""
    if chapter:
        r = 1.6
        P.ell(x, y, r, r, fill=ACCENT, outline=(255, 255, 255), lw=0.25)
        f, em, fa = fface("b", MARK_FACE, letter)
        yb = y + fa / 2.0
        P.text(x, yb, letter, f, (255, 255, 255), anchor="ms")
        bb = f.getbbox(letter, anchor="ms")
        rec_text(letter, "mark", "b", em, fa, box_poly((x + bb[0] / KD, yb + bb[1] / KD, x + bb[2] / KD, yb + bb[3] / KD)), layer)
    else:
        P.ell(x, y, r, r, fill=INK_L, outline=(255, 255, 255), lw=0.25)
        mark_icon(x, y, shape or {"1": "arch", "2": "barrel", "3": "cross", "4": "dome"}.get(str(letter), "arch"))
        f, em, fa = fface("b", MARK_FACE, "한")
        rec_text("", "mark", "b", em, fa, box_poly((x - 1.2, y - 1.2, x + 1.2, y + 1.2)), layer)
    DRAWN["texts"][-1].update({"mark": str(letter), "c": [round(x, 2), round(y, 2)], "source": source, "origin": origin, "d": 2.0 * r,
                               "shape": None if chapter else (shape or "arch"), "chapter": bool(chapter)})
    return (x - r, y - r, x + r, y + r)


def mark_icon(x, y, shape):
    """Ø4 원 안 흰 형태 아이콘(2.4mm 안). arch = 아치(∩ + 두 다리), barrel = 터널(겹 아치), cross = 두 터널 교차(X + 네 다리), dome = 반구 + 오큘러스 점"""
    W_ = (255, 255, 255)
    LW_ = 0.3
    if shape in ("arch", "barrel"):
        rr = 0.95
        arc = [(x + rr * math.cos(math.radians(a)), y - 0.15 - rr * math.sin(math.radians(a))) for a in range(180, -1, -20)]
        P.line([(x - rr, y + 1.0)] + arc + [(x + rr, y + 1.0)], W_, LW_, joint=True)
        if shape == "barrel":
            r2 = 0.45
            arc2 = [(x + r2 * math.cos(math.radians(a)), y - 0.15 - r2 * math.sin(math.radians(a))) for a in range(180, -1, -30)]
            P.line([(x - r2, y + 1.0)] + arc2 + [(x + r2, y + 1.0)], W_, 0.2, joint=True)
    elif shape == "cross":
        P.line([(x - 1.0, y - 1.0), (x + 1.0, y + 1.0)], W_, LW_, joint=False)
        P.line([(x - 1.0, y + 1.0), (x + 1.0, y - 1.0)], W_, LW_, joint=False)
        P.line([(x - 1.15, y - 1.15), (x + 1.15, y - 1.15), (x + 1.15, y + 1.15), (x - 1.15, y + 1.15), (x - 1.15, y - 1.15)], W_, 0.18, joint=True)
    else:   # dome
        rr = 1.25
        pts = [(x + rr * math.cos(math.radians(a)), y + 0.7 - rr * math.sin(math.radians(a))) for a in range(180, -1, -15)]
        P.poly(pts, fill=W_)
        P.line([(x - 1.35, y + 0.75), (x + 1.35, y + 0.75)], W_, 0.25, joint=False)
        P.ell(x, y - 0.1, 0.22, 0.22, fill=INK_L)


MARKS = []      # 짝 표지 목록: {letter, c, source(map·detail·panel), origin}


def mark_source(c):
    x, y = c
    for pid, pn in PANEL.items():
        r = pn["rect"]
        if r[0] - 3 <= x <= r[2] + 3 and r[1] - 3 <= y <= r[3] + 3:
            return "panel"
    cb = z1_composite_box()
    if cb[0] - 3 <= x <= cb[2] + 3 and cb[1] - 3 <= y <= cb[3] + 3:
        return "detail"
    for d in DET["map_elements"]:
        b = d.get("box")
        if b and b[0] <= x <= b[2] and b[1] <= y <= b[3]:
            return "detail"
    return "map"


def build_marks():
    """사양의 mark·mark_pt·숫자 짝 표지(pair_marks)만으로 표지 목록을 만든다(이름 추론 없음)"""
    seen = set()

    def add(letter, c, origin, source=None, extra=None):
        if letter is None or not c:
            return
        key = (str(letter), round(float(c[0]) * 2) / 2, round(float(c[1]) * 2) / 2)
        if key in seen:
            return
        seen.add(key)
        e = {"letter": str(letter), "c": [float(c[0]), float(c[1])], "source": source or mark_source(c), "origin": origin}
        if extra:
            e.update(extra)
        MARKS.append(e)
    for ld in DET["leaders"]:
        if ld.get("mark") and ld.get("mark_pt") and not ld.get("mark_pt_none"):
            add(ld["mark"], ld["mark_pt"], "지시선 " + ld["name"])
    for d in DET["map_elements"]:
        if d.get("mark") and d.get("mark_pt"):
            add(d["mark"], d["mark_pt"], d["id"])
    for pid, pn in PANEL.items():
        if pn.get("mark") and pn.get("mark_pt"):
            add(pn["mark"], pn["mark_pt"], "패널 " + pid)
    for pm in (_find_pair_marks(S) or []):
        if not isinstance(pm, dict):
            continue
        lt = sget(pm, "mark", "label", "num", "n", "text", "id")
        snap_ = pm.get("snap") or {"L2": "market_vault", "L1": "pantheon_dome"}.get(str(pm.get("map_landmark") or ""))   # 통합 d4: panels PAIR_MARKS(map_landmark·tol_mm)
        tol_ = pm.get("tol") if pm.get("tol") is not None else pm.get("tol_mm")
        ex = {"tol": tol_, "snap": snap_, "target": pm.get("target") or pm.get("map_target"), "shape": pm.get("shape")}
        for kk, src in (("map_pt", "map"), ("map", "map"), ("map_c", "map"), ("panel_pt", "panel"), ("panel", "panel"), ("panel_c", "panel")):
            v = pm.get(kk)
            if isinstance(v, (list, tuple)) and len(v) == 2 and all(isinstance(t, (int, float)) for t in v):
                add(lt, v, "숫자 짝 %s(%s)" % (lt, src), src, ex if src == "map" else None)
        if isinstance(pm.get("pt"), (list, tuple)):
            add(lt, pm["pt"], "숫자 짝 %s" % lt, None, ex)
    for cm in ((S.get("chapter_marks") or {}).get("raw") or []):          # 사용자 15:41: ❺ 근거 표지(지도, Ø3.2 + 흰 '5')
        if cm.get("map_pt"):
            add(str(cm.get("mark", "5")), cm["map_pt"], "❺ 근거 표지 %s" % cm.get("map_target", ""), "map", {"chapter": True, "target": cm.get("map_target")})


def snap_marks():
    """숫자 짝 3·4: 실제로 그린 대상 면 위로 맞춘다(허용 ±tol). 맞춘 자리를 기록한다"""
    for mk in MARKS:
        if mk["source"] != "map" or not mk.get("snap"):
            continue
        tol = float(mk.get("tol") or 4.0)
        c0 = mk["c"]
        cands = GEO.get("snap_" + mk["snap"]) or []
        best = None
        for q in cands:
            d_ = math.hypot(q[0] - c0[0], q[1] - c0[1])
            if d_ <= tol + 1e-6 and (best is None or d_ < best[0]):
                best = (d_, q)
        if best is None and cands and GEO.get("snap_" + mk["snap"] + "_any"):   # 결정: 실제 볼트 칸 위로 맞춘다(사양 좌표가 칸에서 벗어남)
            q = min(cands, key=lambda q_: math.hypot(q_[0] - c0[0], q_[1] - c0[1]))
            best = (math.hypot(q[0] - c0[0], q[1] - c0[1]), q)
            mk["spec_tol_exceeded"] = True
            REPORT["notes"].append("짝 표지 %s: 사양 자리 (%.1f, %.1f)는 대상 면 밖(빈 지면). 실제로 그린 걷은 지붕 칸 옆 지붕 (%.1f, %.1f)으로 맞춤(%.1fmm, 허용 ±%.1f 초과)"
                                   % (mk["letter"], c0[0], c0[1], q[0], q[1], best[0], tol))
        if best:
            mk["spec_c"] = list(c0)
            mk["c"] = [round(best[1][0], 2), round(best[1][1], 2)]
            mk["snap_dev_mm"] = round(best[0], 2)
        elif cands:
            q = min(cands, key=lambda q_: math.hypot(q_[0] - c0[0], q_[1] - c0[1]))
            REPORT["notes"].append("짝 표지 %s: 대상 면 가장 가까운 점 (%.1f, %.1f)이 허용 ±%.1f 밖(%.1fmm) → 사양 자리 유지"
                                   % (mk["letter"], q[0], q[1], tol, math.hypot(q[0] - c0[0], q[1] - c0[1])))


def draw_marks():
    for mk in MARKS:
        if mk.get("drawn"):
            continue
        mark(mk["c"][0], mk["c"][1], mk["letter"], layer="짝 표지 " + mk["source"], source=mk["source"], origin=mk["origin"], shape=mk.get("shape"), chapter=bool(mk.get("chapter")))
        mk["drawn"] = True


def measure_marks():
    """짝 표지 ↔ 다른 글·지시선·표지 간격(2mm 이상 규칙 확인용)"""
    texts = [t for t in DRAWN["texts"] if t.get("role") != "mark"]
    leads = [ld["pts"] for ld in DRAWN["leaders"]] + [lb["leader"]["pts"] for lb in DRAWN["labels"] if lb.get("leader")]
    out = []
    for i, mk in enumerate(MARKS):
        c = mk["c"]
        circ = [(c[0] + MARK_R * math.cos(math.radians(t)), c[1] + MARK_R * math.sin(math.radians(t))) for t in range(0, 360, 20)]
        dt_ = min([_poly_dist(circ, [tuple(p) for p in t["poly"]]) for t in texts] or [99.0])
        dl_ = min([_poly_dist(circ, [tuple(p) for p in l_], True, False) for l_ in leads] or [99.0])
        dm_ = min([math.hypot(c[0] - o["c"][0], c[1] - o["c"][1]) - 2 * MARK_R for j, o in enumerate(MARKS) if j != i] or [99.0])
        e = {"letter": mk["letter"], "c": [round(c[0], 2), round(c[1], 2)], "source": mk["source"], "origin": mk["origin"],
             "clear_text_mm": round(dt_, 2), "clear_leader_mm": round(dl_, 2), "clear_mark_mm": round(dm_, 2)}
        for k in ("spec_c", "snap_dev_mm", "target", "spec_tol_exceeded"):
            if mk.get(k) is not None:
                e[k] = mk[k]
        out.append(e)
    cnt = {}
    for mk in MARKS:
        cnt[mk["letter"]] = cnt.get(mk["letter"], 0) + 1
    DRAWN["marks"] = out
    DRAWN["mark_counts"] = cnt


def print_note(d):
    """Detail 주의 글: figure.footnote가 있으면 그것, 없으면 caution 첫 문장이 '미확인'일 때만(내부 지시 문장은 인쇄하지 않는다)"""
    if d.get("print_note"):
        return d["print_note"]
    fig = d.get("figure") or {}
    if fig.get("footnote"):
        return fig["footnote"]
    c = (d.get("caution") or "").split(". ")[0].strip().rstrip(".")
    if c.endswith("미확인"):
        return "※ " + c
    return None


def print_texts(d):
    """Detail 본문(사양 text). 그림 사양 문장(치수·Ø·'미시 도해')은 인쇄하지 않는다"""
    out = []
    for s in d.get("text", []):
        if re.search(r"mm|Ø|미시 도해|단면 모식 Ø", s):
            continue
        out.append(s)
    return out


def chunk_wrap(s, kind, face, maxw):
    """' + '·' → ' 앞뒤를 먼저 끊을 자리로 쓰는 줄바꿈"""
    parts = re.split(r"(?<=\+) |(?<=→) ", s)
    if len(parts) == 1:
        return wrap(s, kind, face, maxw)
    lines = []
    cur = ""
    for p in parts:
        t = p if not cur else cur + " " + p
        if not cur or twf(t, kind, face) <= maxw:
            cur = t
        else:
            lines += wrap(cur, kind, face, maxw)
            cur = p
    if cur:
        lines += wrap(cur, kind, face, maxw)
    return lines


def draw_lines(x, y, lines, kind, face, col, role, pitch, layer, anchor="l"):
    """여러 줄 글(기준선 y부터 pitch 간격). 마지막 기준선 y를 돌려준다"""
    yy = y
    for i, t in enumerate(lines):
        yy = y + i * pitch
        ptext(x, yy, t, kind, face, col, role, anchor=anchor, layer=layer, pitch=pitch if len(lines) > 1 else None)
    return yy


def _leader_target(name, p0=None):
    """Detail 지시선 이름 → 지도 쪽 대상 지면 다각형 이름. 후보가 여럿이면 시작점에 가장 가까운 면(d5: Z1 출발점 = 공사장 거푸집 오른쪽 면)"""
    cands = None
    for kw, fp in (("확대 창 Z1 →", ["확대 창 Z1"]), ("→ 확대 창 Z1", ["공사장 거푸집 오른쪽 면", "공사장 거푸집 앞면"]), ("⑥", ["공사장 거푸집 앞면"]),
                   ("공사장", ["공사장 거푸집 앞면", "공사장 거푸집 오른쪽 면"]), ("기초 절개", ["공사장 거푸집 오른쪽 면"]),
                   ("판테온", ["판테온 돔"]), ("방파제", ["포르투스 외항 방파제"]), ("메텔라", ["메텔라 드럼"])):
        if kw in name:
            cands = fp
            break
    if not cands:
        return None
    if p0 is None or len(cands) == 1:
        return cands[0]
    return min(cands, key=lambda n_: min([_pt_poly_gap(p0, q_) for q_ in target_polys(n_)] or [99.0]))


def z1_circle_poly():
    z = DMAP["Z1"]
    (cx, cy), d = z["circle"]["c"], z["circle"]["d"]
    return [(cx + d / 2.0 * math.cos(math.radians(t)), cy + d / 2.0 * math.sin(math.radians(t))) for t in range(0, 360, 5)]


def draw_leaders():
    """Detail·Basic 지시선: 사양 꼭짓점 그대로, 정보 잉크 0.30mm, 끝점 Ø0.9, ⑥만 패널 쪽 작은 화살촉. 짝 표지는 시작점 옆 3~4mm"""
    add_fp("확대 창 Z1", z1_circle_poly(), "Detail")
    for nm, pts, letter, kind in detail_leaders():
        if kind == "basic":
            (xa, ya), (xb, yb) = pts[-2], pts[-1]
            L_ = math.hypot(xb - xa, yb - ya)
            ux, uy = (xb - xa) / L_, (yb - ya) / L_
            base = (xb - ux * 1.9, yb - uy * 1.9)
            P.line(pts[:-1] + [base], INK_L, LEAD_W, joint=False)
            P.poly([(base[0] - uy * 0.8, base[1] + ux * 0.8), (xb, yb), (base[0] + uy * 0.8, base[1] - ux * 0.8)], fill=INK_L)
            P.dot(pts[0][0], pts[0][1], DOT_RR, INK_L)
        else:
            P.line(pts, INK_L, LEAD_W, joint=False)
            P.dot(pts[0][0], pts[0][1], DOT_RR, INK_L)
            P.dot(pts[-1][0], pts[-1][1], DOT_RR, INK_L)
        tname = _leader_target(nm, pts[0])
        tps = target_polys(tname) if tname else []
        gap = round(min(_pt_poly_gap(pts[0], q_) for q_ in tps), 2) if tps else None
        rec = {"name": nm, "pts": [[round(x, 2), round(y, 2)] for x, y in pts], "dot_d": 2 * DOT_RR, "lw": LEAD_W, "ink": list(INK_L),
               "target": tname, "gap": gap, "first_point": "지도 쪽", "arrow": "패널 쪽 끝" if kind == "basic" else None}
        if letter:                                                   # 표지는 사양 mark_pt 자리(MARKS)에 그린다. 지시선 시작점에 가장 가까운 같은 글자 표지를 기록
            near = [mk for mk in MARKS if mk["letter"] == str(letter)]
            if near:
                mk = min(near, key=lambda q: math.hypot(q["c"][0] - pts[0][0], q["c"][1] - pts[0][1]))
                rec["mark"] = {"letter": letter, "c": [round(mk["c"][0], 2), round(mk["c"][1], 2)],
                               "dist": round(math.hypot(mk["c"][0] - pts[0][0], mk["c"][1] - pts[0][1]), 2)}
        DRAWN["leaders"].append(rec)


def place_mark(pts):
    """짝 표지 자리: 시작점에서 3.5mm 떨어진 8방향 후보 가운데 지시선·라벨·글과 가장 먼 곳"""
    sx, sy = pts[0]
    best = None
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        c = (sx + 3.5 * math.cos(a), sy + 3.5 * math.sin(a))
        circ = [(c[0] + MARK_R * math.cos(math.radians(t)), c[1] + MARK_R * math.sin(math.radians(t))) for t in range(0, 360, 30)]
        d = min([_poly_dist(circ, pts, True, False)] + [_poly_dist(circ, pg) for _n, pg in LABEL_POLYS] +
                [_poly_dist(circ, l_, True, False) for l_ in PLACED_LEADS])
        if best is None or d > best[0] + 1e-6:
            best = (d, c)
    return best[1]


# ───────────────────────── 8 지도 라벨(등각 벽면·깃대·말풍선) ─────────────────────────
# 서체 결정 7(글자면 mm): 영문 3.8 · 국문 이름 3.8 · 원어 위첨자 2.1 · 본문 3.0(피치 4.15) · 태그 2.6. 배율 1.00 고정, 바탕판 없음.
LF_EN, LF_KO, LF_SUP, LF_BODY, LF_PITCH, LF_TAG = 3.8, 3.8, 2.1, 3.0, 4.15, 2.6
LABEL_CLEAR = 2.3          # 글 블록 ↔ 길·건물·다른 라벨·지시선 목표 간격(규칙 2mm + 여유)
BRACKET_D = 2.3            # 브래킷 수직선 = 글 블록 밖 C30 × 2.3 ≈ 2.0mm(허용 1.5~4)
FLAG_D = 1.9               # 깃대 = 글 블록 밖 C30 × 1.9 ≈ 1.65mm
LABEL_ORDER = ["콜로세움", "트라야누스 시장", "판테온", "수도교", "카이킬리아 메텔라 무덤", "포르투스 항",
               "막센티우스 바실리카", "네로 거상", "마르켈루스 극장", "하드리아누스 영묘"]      # 사용자 16:14: Core 건축물 라벨 11개만
LF_PROP, LF_PROP_PITCH = 2.6, 3.9     # 소품 주석(새 종류, d4): 글자면 2.6 고정, 정보 잉크, 말풍선 없음
# 지시선 문법(사양 lead 문장을 렌더 동작으로 옮긴 것): (방식, 쪽, 대상 지면 다각형 이름)
LEAD_RULE = {
    "콜로세움": ("free", "R", "콜로세움 외벽"),
    "카라칼라 욕장": ("free", "R", "욕장 왼쪽 벽 윗면"),
    "트라야누스 시장": ("free", "L", "시장 지면"),
    "판테온": ("free", "R", "파르테논 엔타블러처"),
    "수도교": ("free", "R", "수도교 아치 면"),
    "카이킬리아 메텔라 무덤": ("free", "R", "메텔라 기단"),
    "포르투스 항": ("free", "R", "포르투스 외항 방파제"),
    "막센티우스 바실리카": ("free", "R", "바실리카 측랑 볼트"),
    "네로 거상": ("free", "R", "네로 거상"),
    "마르켈루스 극장": ("free", "R", "극장 반원 아케이드"),
    "하드리아누스 영묘": ("free", "L", "영묘 기단 윗면"),
}
LEAD_PREF = {"콜로세움": tuple(sget(SLOT.get("콜로세움", {}), "blender_anchor_pt", "anchor_pt", default=None) or (269.97, 244.0))}   # 결정 D11 앵커(잠정): 지시선 끝 선호점
PLACED_LEADS = []          # 놓인 지시선(라벨·Detail) 꺾은선
LABEL_PLAN = {}            # 라벨 자리 잡기 결과

# 자리 잡기용 장애물 격자(4px/mm)
OK4 = 4


def _mask_new():
    return Image.new("L", (PW * OK4, PH * OK4), 0)


def _mask_poly(m, poly, pad=0.0):
    d = ImageDraw.Draw(m)
    q = [(x * OK4, y * OK4) for x, y in poly]
    d.polygon(q, fill=255)
    if pad > 0:
        d.line(q + [q[0]], fill=255, width=max(1, int(round(2 * pad * OK4))), joint="curve")


def _mask_line(m, pts, w=0.5):
    ImageDraw.Draw(m).line([(x * OK4, y * OK4) for x, y in pts], fill=255, width=max(1, int(round(w * OK4))))


# 사양 슬롯에 en·ko·sup·tag_text가 없을 때만 쓰는 인쇄 문자열(결정 문안과 같다). 사양 값이 있으면 사양이 우선이다.
LABEL_TEXT_FALLBACK = {
    "콜로세움": (["COLOSSEUM"], "콜로세움", "Amphitheatrum Flavium"), "판테온": (["ACROPOLIS"], "아크로폴리스", None),
    "카라칼라 욕장": (["BATHS OF CARACALLA"], "카라칼라 욕장", "Thermae Antoninianae"),
    "트라야누스 시장": (["TRAJAN'S MARKETS"], "트라야누스 시장", "Mercati di Traiano"), "수도교": (["AQUEDUCT"], "수도교", "Aqua Antoniniana"),
    "카이킬리아 메텔라 무덤": (["CAECILIA METELLA"], "카이킬리아 메텔라 무덤", None), "포르투스 항": (["PORTUS"], "포르투스 항", "Portus"),
    "막센티우스 바실리카": (["BASILICA OF MAXENTIUS"], "막센티우스 바실리카", "Basilica Nova"),
    "마르켈루스 극장": (["THEATRE OF MARCELLUS"], "마르켈루스 극장", None),
    "하드리아누스 영묘": (["MAUSOLEUM OF HADRIAN"], "하드리아누스 영묘", None),
}
TAG_TEXT_FALLBACK = {}


def label_strings(slot, key):
    fb = LABEL_TEXT_FALLBACK.get(key, ([], key, None))
    en = slot.get("en") if slot.get("en") is not None else fb[0]
    ko = slot.get("ko") or fb[1]
    sup = slot.get("sup") if "sup" in slot else fb[2]
    return list(en or []), ko, sup


def note_stack(slot):
    """소품 주석(2.6 고정, 정보 잉크, 말풍선·규선 없음) 글 블록"""
    lines_ = list(slot.get("lines") or slot.get("body") or [])
    fk_ = slot.get("font") if slot.get("font") in ("b", "m") else "b"      # 사양 글꼴(panels 실측 기준, 통합 d4)
    lines, v = [], 0.3 + LF_PROP
    # 사용자 17:28·17:29 결정: 이름(굵게) + 사실 줄(본문 크기)
    v = 0.3 + 3.0
    for i, t_ in enumerate(lines_):
        if i == 0:
            lines.append((t_, "b", 3.0, 0.0, v, "prop_label"))
        else:
            lines.append((t_, "m", LF_PROP, 0.0, v + 0.6 + LF_PROP_PITCH * i, "prop_label"))
    W = max(twf(l_[0], l_[1], l_[2]) for l_ in lines) if lines else 1.0
    H = v + 0.6 + LF_PROP_PITCH * (len(lines_) - 1) + 0.7
    return {"lines": lines, "W": W, "H": H, "v_rule": None, "base_ko": None, "has_rule": False, "body": [], "en": [], "note": True, "text": lines_}


def label_stack(slot, key, maxw=None, sup_own=False, en_split=False, body_override=None, sup_override=None):
    """라벨 글 블록 조판(글자면 기준). 돌려줌: lines[(글, 종류, 글자면, u, 기준선 v, 역할)], W, H, v_rule, base_ko"""
    en, ko, sup = label_strings(slot, key)
    if sup_override is not None:
        sup = sup_override
    if en_split:
        en2 = []
        for s in en:
            ws = s.split(" ")
            if len(ws) >= 3:
                h = len(ws) // 2 + (1 if len(ws) % 2 else 0) - (1 if len(ws) == 3 else 0)
                h = max(1, min(len(ws) - 1, h if len(ws) != 3 else 2))
                en2 += [" ".join(ws[:h]), " ".join(ws[h:])]
            else:
                en2.append(s)
        en = en2
    body = list(slot.get("body") or []) if body_override is None else list(body_override)
    if maxw:
        body = wrap_all(body, "m", LF_BODY, maxw)
    lines = []
    v = 0.3
    if slot.get("name_inline") and len(en) == 1:               # 사용자 16:14: 영문·국문 이름을 한 줄에 둔다(좁은 바다 자리에 사실 1줄이 들어가게)
        v = 0.3 + LF_EN
        lines.append((en[0], "en", LF_EN, 0.0, v, "label_en"))
        u_ko = twf(en[0], "en", LF_EN) + 2.0
        lines.append((ko, "b", LF_KO, u_ko, v, "label_ko"))
        if sup:
            lines.append((sup, "m", LF_SUP, u_ko + twf(ko, "b", LF_KO) + 1.2, v, "label_sup"))
        base_ko = v
        v_after = v
    else:
        for s in en:
            v += LF_EN
            lines.append((s, "en", LF_EN, 0.0, v, "label_en"))
            v += 0.8
        v += 0.5
        base_ko = v + 3.6
        lines.append((ko, "b", LF_KO, 0.0, base_ko, "label_ko"))
        v_after = base_ko
        if sup:
            if sup_own:
                v_after = base_ko + 0.9 + LF_SUP
                lines.append((sup, "m", LF_SUP, 0.0, v_after, "label_sup"))
            else:
                lines.append((sup, "m", LF_SUP, twf(ko, "b", LF_KO) + 1.2, base_ko - 1.45, "label_sup"))
    v_rule = v_after + (1.5 if body else 1.2)          # 본문 없는 브래킷(L7): 블록 두께 10.6(결정 14 (1))
    if body:
        for i, s in enumerate(body):
            lines.append((s, "m", LF_BODY, 0.0, v_rule + 4.15 + LF_PITCH * i, "label_body"))
        H = v_rule + 4.15 + LF_PITCH * (len(body) - 1) + 0.6
    else:
        H = v_after + 0.7 if "깃대" in slot.get("kind", "") or "규선" in slot.get("kind", "") else v_rule + 0.4
    W = max(u + twf(s, k, f) for s, k, f, u, vb, r in lines)
    return {"lines": lines, "W": W, "H": H, "v_rule": v_rule, "base_ko": base_ko, "has_rule": bool(body) or not ("깃대" in slot.get("kind", "") or "규선" in slot.get("kind", "")),
            "body": body, "en": en}


def lab_M(slot):
    return M_WALL_UP if str(slot.get("wall", "↘")).startswith("↗") else M_WALL_DN


def lab_poly(M, ax, ay, W, H):
    return [map_pt(M, ax, ay, u, v) for u, v in ((0, 0), (W, 0), (W, H), (0, H))]


def _vert_hit(poly, x, y_from, direction):
    """수직선 x가 다각형 경계와 만나는 y 가운데 y_from에서 direction(+1 아래, −1 위)으로 처음 만나는 값"""
    ys = []
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (x1 - x) * (x2 - x) <= 0 and x1 != x2:
            ys.append(y1 + (y2 - y1) * (x - x1) / (x2 - x1))
    ys = [y for y in ys if (y - y_from) * direction > 0.05]
    if not ys:
        return None
    return min(ys, key=lambda y: abs(y - y_from))


def target_polys(name):
    """대상 이름 → 지면 다각형 목록(여러 조각이면 fpset_)"""
    return GEO.get("fpset_" + name) or ([GEO["fp_" + name]] if GEO.get("fp_" + name) else [])


def _vert_hit_any(polys, x, y_from, direction):
    hits = [h for h in (_vert_hit(pg, x, y_from, direction) for pg in polys) if h is not None]
    return min(hits, key=lambda y: abs(y - y_from)) if hits else None


AXDIR = {"X": (C30, 0.5), "Y": (-C30, 0.5), "Z": (0.0, -1.0)}     # 등각 축 방향(화면): X ↘ · Y ↙ · Z 위


def axis_paths(p, t):
    """p → t 를 등각 축 방향 선분만으로 잇는 꺾은선 후보(꺾임 ≤ 1). 축 쌍 3가지 × 순서 2가지 가운데 길이 짧은 순 [(길이, [점...])]"""
    vx, vy = t[0] - p[0], t[1] - p[1]
    out = []
    for n1, n2 in (("X", "Y"), ("X", "Z"), ("Y", "Z")):
        d1, d2 = AXDIR[n1], AXDIR[n2]
        det = d1[0] * d2[1] - d1[1] * d2[0]
        a = (vx * d2[1] - vy * d2[0]) / det
        b = (d1[0] * vy - d1[1] * vx) / det
        L = abs(a) + abs(b)
        for first, (da, sa), (db, sb) in (("1", (d1, a), (d2, b)), ("2", (d2, b), (d1, a))):
            mid = (p[0] + da[0] * sa, p[1] + da[1] * sa)
            pts = [p]
            tiny = (0.01 < abs(sa) < 0.8) or (0.01 < abs(sb) < 0.8)      # 아주 짧은 꺾음 조각은 반올림하면 각도가 틀어진다 → 뒤로 미룬다
            if abs(sa) > 0.01 and abs(sb) > 0.01:
                pts.append(mid)
            pts.append(t)
            out.append((L + (1000.0 if tiny else 0.0), pts))
    out.sort(key=lambda e: e[0])
    return out


def axis_path(p, t):
    return axis_paths(p, t)[0][1]


def lead_for(key, slot, st, M, ax, ay):
    """라벨 지시선(꺾임 ≤ 1, 수직·±30°). 돌려줌: (점들, 대상 이름, 간격) 또는 None"""
    rule = LEAD_RULE.get(key)
    if not rule:
        return None
    mode, side, tname = rule
    tps = target_polys(tname)
    if not tps:
        return None
    tp = tps[0]
    W, H, vr = st["W"], st["H"], st["v_rule"]
    a = M[0][0]
    tpt = slot.get("target_pt")
    if mode == "extend":
        u_end = W if side == "R" else 0.0
        pe = map_pt(M, ax, ay, u_end, vr)
        if tname == "판테온 돔":
            cand = [q for q in GEO.get("pantheon_dome_ul", []) if in_poly(q, tp)]
            T = tuple(tpt) if (tpt and in_poly(tuple(tpt), tp)) else (min(cand, key=lambda q: math.hypot(q[0] - tpt[0], q[1] - tpt[1])) if (cand and tpt) else (cand[0] if cand else None))
        elif tname == "욕장 왼쪽 벽 윗면":
            T = GEO.get("bath_label_tgt")
        elif tname == "시장 오른쪽 동 끝면":
            T = GEO.get("market_tgt")
        else:
            T = GEO.get("lead_tgt_" + key) or (tuple(tpt) if tpt else None)
            if T is not None and not any(in_poly(tuple(T), q_) for q_ in tps):
                pool = [q for pg in tps for q in pg]
                T = min(pool, key=lambda q: math.hypot(q[0] - T[0], q[1] - T[1])) if pool else T
        if T is None:
            return None
        dx = T[0] - pe[0]
        if (side == "R" and dx < 1.5) or (side == "L" and dx > -1.5):
            return None
        du = dx / a
        q = map_pt(M, ax, ay, u_end + du, vr)
        pts = [pe, q]
        if abs(q[1] - T[1]) > 0.4:
            pts.append((q[0], T[1]))
        end = pts[-1]
    elif mode == "extend_v30":                                       # 규선 오른쪽 끝 ↗ 연장 → ↘30° 한 번 꺾어 대상(L7)
        T = GEO.get("lead_tgt_" + key) or (tuple(tpt) if tpt else None)
        if T is None:
            return None
        pe = map_pt(M, ax, ay, W, vr)
        d1 = (M[0][0], M[1][0])
        d2 = (C30, 0.5)
        det = d1[0] * d2[1] - d2[0] * d1[1]
        if abs(det) < 1e-6:
            return None
        rx, ry = T[0] - pe[0], T[1] - pe[1]
        s1 = (rx * d2[1] - d2[0] * ry) / det
        s2 = (d1[0] * ry - rx * d1[1]) / det
        if s1 < 1.0 or s2 < 1.0:
            return None
        bend = (pe[0] + d1[0] * s1, pe[1] + d1[1] * s1)
        pts = [pe, bend, (T[0], T[1])]
        end = pts[-1]
    elif mode in ("ray_ul", "ray_dr"):                               # 블록 왼쪽 끝 ↖30°(영묘) / 오른쪽 끝 ↘30°(거상 주석) 한 직선
        dirv = (-C30, -0.5) if mode == "ray_ul" else (C30, 0.5)
        u_edge = -0.35 if mode == "ray_ul" else W + 0.35
        head = GEO.get("colossus_head") if mode == "ray_dr" else None
        best = None
        nv = max(1, int((H - 0.6) / 0.4))
        for iv in range(nv + 1):
            v_s = 0.3 + (H - 0.6) * iv / nv
            s0 = map_pt(M, ax, ay, u_edge, v_s)
            th = _ray_hit(s0, dirv, tps, 60.0)
            if th is None or th <= 0.0:
                continue
            t2 = th + 0.4
            e_ = (s0[0] + dirv[0] * t2, s0[1] + dirv[1] * t2)
            if not any(in_poly(e_, q_) for q_ in tps):
                t2 = th + 0.1
                e_ = (s0[0] + dirv[0] * t2, s0[1] + dirv[1] * t2)
            score = t2 + (0.6 * abs(e_[1] - head[1]) if head else 0.0)
            if best is None or score < best[0]:
                best = (score, s0, e_)
        if best is None:
            return None
        pts = [best[1], best[2]]
        end = pts[-1]
    elif mode in ("vertical", "vertical2"):
        d = 2.0 if mode == "vertical2" else BRACKET_D
        du = d if side == "R" else -d
        u_end = W if side == "R" else 0.0
        pe = map_pt(M, ax, ay, u_end, vr)
        q = map_pt(M, ax, ay, u_end + du, vr)
        if tname == "콜로세움 외벽":
            ty = GEO["arena_top_y"](q[0])
            if ty is None:                                               # d5: 건물이 좁아져 오른쪽 끝 아래에 벽이 없으면 규선 왼쪽 끝에서 수직
                pe = map_pt(M, ax, ay, 0.0, vr)
                q = map_pt(M, ax, ay, -d, vr)
                ty = GEO["arena_top_y"](q[0])
            if ty is None:
                return None
            end = (q[0], ty + 0.8)
        else:
            cy_ = sum(p[1] for p in tp) / len(tp)
            direction = 1 if cy_ > q[1] else -1
            yh = _vert_hit_any(tps, q[0], q[1], direction)
            if yh is None:
                return None
            end = (q[0], yh + 0.7 * direction)
        pts = [pe, q, end]
    elif mode == "free":                                             # 17:24 제약 완화: 글 블록 가장자리에서 대상까지 곧은 선(각도 제한 없음)
        T = tuple(tpt) if tpt else None
        if T is not None and INFO_ONLY:
            pass                                                         # 정보 층: Blender 앵커 점 그대로 지시선 끝
        elif T is None or not any(in_poly(T, q_) for q_ in tps):
            pool = [q for pg in tps for q in pg]
            ctr_ = map_pt(M, ax, ay, W / 2.0, H / 2.0)                  # 글 블록 가운데에서 가장 가까운 대상 꼭짓점
            T = min(pool, key=lambda q: math.hypot(q[0] - ctr_[0], q[1] - ctr_[1]))
        cands = [map_pt(M, ax, ay, u_, v_) for u_ in (0.0, W / 2.0, W) for v_ in (0.0, H / 2.0, H)]
        best_p = None
        for pe_ in cands:                                              # 21:59 지시선 = 등각 축(X ↘ · Y ↙ · Z 수직) 선분만, 꺾임 ≤ 1
            L_, pp_ = axis_paths(pe_, T)[0]
            if best_p is None or L_ < best_p[0]:
                best_p = (L_, pp_)
        pts = best_p[1]
        end = T
    elif mode == "flag":
        cy_ = sum(p[1] for p in tp) / len(tp)
        hit = None
        px_ = slot.get("pole_x")
        dhs = [ax - float(px_)] if px_ is not None else [1.5 + 0.25 * k for k in range(0, 11)]
        for dh in dhs:                                               # 깃대 = 글 블록 밖 1.5~4.0mm(화면 가로)
            if not (1.45 <= dh <= 4.05):
                continue
            du = dh / a
            top = map_pt(M, ax, ay, -du, 0.0)
            if cy_ < top[1]:
                return None
            yh = _vert_hit_any(tps, top[0], top[1], 1)
            if yh is not None:
                hit = (top, (top[0], yh + 0.7))
                break
        if hit is None:
            return None
        pts = [hit[0], hit[1]]
        end = pts[-1]
    else:   # ko_ray: 국문 기준선 왼쪽 끝에서 30° 한 직선(사양 ↖, 선체가 기준선보다 아래면 ↙)
        s0 = map_pt(M, ax, ay, -0.4, st["base_ko"] + 0.4)
        end = None
        for sy in (-0.5, 0.5):
            for i in range(1, 121):
                t = i * 0.1
                p = (s0[0] - C30 * t, s0[1] + sy * t)
                if any(in_poly(p, q_) for q_ in tps):
                    t2 = t + 0.6
                    end = (s0[0] - C30 * t2, s0[1] + sy * t2)
                    break
            if end:
                break
        if end is None:
            return None
        pts = [s0, end]
    gap = min(_pt_poly_gap(end, q_) for q_ in tps)
    if INFO_ONLY and SIL and mode == "free" and tpt:
        gap = 0.0                                                    # 정보 층: 끝점 = Blender 앵커 점(대상 면은 실루엣)
    return pts, tname, gap


def _ray_hit(p0, d, polys, tmax=80.0):
    """반직선 p0 + t·d(t > 0)가 다각형 경계와 처음 만나는 t. 시작점이 안이면 0, 없으면 None"""
    best = None
    for pg in polys:
        if len(pg) >= 3 and in_poly(p0, pg):
            return 0.0
        n = len(pg)
        for i in range(n):
            a, b = pg[i], pg[(i + 1) % n]
            ex, ey = b[0] - a[0], b[1] - a[1]
            den = d[0] * ey - d[1] * ex
            if abs(den) < 1e-12:
                continue
            wx, wy = a[0] - p0[0], a[1] - p0[1]
            t = (wx * ey - wy * ex) / den
            u = (d[1] * wx - d[0] * wy) / den
            if 1e-6 < t <= tmax and -1e-9 <= u <= 1.0 + 1e-9 and (best is None or t < best):
                best = t
    return best


def _obstacles_for(kind_tag):
    m = _mask_new()
    if not kind_tag:
        if INFO_ONLY and SIL:                                        # 정보 층: 와이어프레임 실루엣(sil.json)으로 라벨 자리를 잡는다
            m = sil_obstacle_mask(m)
        else:
            a = OBJ.img.getchannel("A").resize((PW * OK4, PH * OK4), Image.BOX).point(lambda v: 255 if v >= 128 else 0)
            m = ImageChops.lighter(m, a)
        for b in (GEO.get("route_polys") or []):                       # 읽기 길(사용자 16:41)
            _mask_poly(m, b)
    for f in FLOORS:
        _mask_poly(m, f["poly"])
    for _n, pg in INFO_BOXES:
        _mask_poly(m, pg)
    for _n, pg in LABEL_POLYS:
        _mask_poly(m, pg)
    for l_ in PLACED_LEADS:
        _mask_line(m, l_, 0.4)
    for mk in MARKS:                                                 # 지도 쪽 짝 표지(Ø4)도 라벨 장애물
        if mk["source"] == "map":
            c = mk["c"]
            _mask_poly(m, [(c[0] + MARK_R * math.cos(math.radians(t)), c[1] + MARK_R * math.sin(math.radians(t))) for t in range(0, 360, 20)])
    return m


def _dt(m):
    free = np.array(m, dtype=np.uint8)
    free = np.where(free > 0, 0, 255).astype(np.uint8)
    return cv2.distanceTransform(free, cv2.DIST_L2, 5) / float(OK4)


def _clear_of(dt, poly):
    """다각형 안 화소 가운데 장애물까지 가장 가까운 거리(mm)"""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    X0, Y0 = max(0, int(min(xs) * OK4) - 1), max(0, int(min(ys) * OK4) - 1)
    X1, Y1 = min(PW * OK4, int(max(xs) * OK4) + 2), min(PH * OK4, int(max(ys) * OK4) + 2)
    if X1 <= X0 or Y1 <= Y0:
        return 0.0
    mm = Image.new("L", (X1 - X0, Y1 - Y0), 0)
    ImageDraw.Draw(mm).polygon([(x * OK4 - X0, y * OK4 - Y0) for x, y in poly], fill=255)
    a = np.array(mm) > 0
    sub = dt[Y0:Y1, X0:X1]
    if not a.any():
        return 0.0
    return float(sub[a].min())


def _lead_ok(pts, own_poly):
    """지시선이 다른 라벨·지시선을 지나지 않고, 다른 라벨과 2mm 이상인가"""
    for _n, pg in LABEL_POLYS:
        if _poly_dist(pg, pts, True, False) < 2.05:
            LEAD_WHY[_n] = LEAD_WHY.get(_n, 0) + 1
            return False
    for l_ in PLACED_LEADS:
        if _poly_dist(l_, pts, False, False) < 0.6:
            LEAD_WHY["지시선"] = LEAD_WHY.get("지시선", 0) + 1
            return False
    for _n, pg in INFO_BOXES:
        if _n == "읽기 길":                                            # 지시선은 길을 가로질러도 된다(글 블록만 길 밖)
            continue
        if _poly_dist(pg, pts, True, False) < 0.3:
            LEAD_WHY[_n] = LEAD_WHY.get(_n, 0) + 1
            return False
    return True


LEAD_WHY = {}


DBG_LABEL = {}


def plan_label(key):
    """슬롯 안에서 글 블록 자리를 고른다(배율 1.00, 줄바꿈·자리 조정만). 간격이 큰 자리 → 짧은 지시선 순.
    슬롯에 top_line(윗변 y = a + b·x)·x_range가 있으면(또는 결정값 슬롯이면) 블록 윗변을 그 선 위에 둔다(비스듬한 블록 세로 2.4mm 규칙)."""
    slot = SLOT[key]
    kind = slot.get("kind", "")
    is_tag = "태그" in kind
    is_note = "주석" in kind
    M = lab_M(slot)
    box = slot["box"]
    dt = _dt(_obstacles_for(is_tag))
    tl, xr = slot.get("top_line"), slot.get("x_range")
    if tl is None and key in D4_TOPLINE and _same(list(box), D4_TOPLINE[key][2], 0.6):
        tl, xr = D4_TOPLINE[key][0], D4_TOPLINE[key][1]
    variants = []
    if is_tag:
        variants.append(("tag", None))
    elif is_note:
        variants.append(("주석", note_stack(slot)))
    elif tl and xr:                                                   # 윗변 선 고정 라벨: 결정 조판 + (넘칠 때) 본문 3줄째 → 위첨자
        variants.append(("기본", label_stack(slot, key)))
        if slot.get("body_alt_sup") and slot.get("body"):
            variants.append(("본문 3줄째 → 위첨자", label_stack(slot, key, body_override=list(slot["body"])[:-1], sup_override=slot["body_alt_sup"], sup_own=True)))
    else:
        base = label_stack(slot, key)
        variants.append(("기본", label_stack(slot, key)))
        variants.append(("위첨자 줄", label_stack(slot, key, sup_own=True)))
        variants.append(("영문 2줄", label_stack(slot, key, en_split=True)))
        variants.append(("영문 2줄·위첨자 줄", label_stack(slot, key, sup_own=True, en_split=True)))
        for f in (0.8, 0.65):
            variants.append(("본문 줄바꿈 %.2f" % f, label_stack(slot, key, maxw=base["W"] * f, sup_own=True)))
        if slot.get("body_alt_sup") and slot.get("body"):
            variants.append(("본문 3줄째 → 위첨자", label_stack(slot, key, body_override=list(slot["body"])[:-1], sup_override=slot["body_alt_sup"], sup_own=True)))
    best = None
    for vname, st in variants:
        if vname == "tag":
            st = tag_stack(slot)
        W, H = st["W"], st["H"]
        ext = bbox_of(lab_poly(M, 0, 0, W, H))
        cands = []
        if tl and xr and not is_tag:
            x_lo, x_hi = xr[0] - ext[0], xr[1] - ext[2]
            if x_hi < x_lo:
                x_hi = x_lo
            nx = max(1, int((x_hi - x_lo) / 0.25) + 1)
            for i in range(nx):
                ax = x_lo + (x_hi - x_lo) * (i / (nx - 1) if nx > 1 else 0.0)
                cands.append((ax, float(tl[0]) + float(tl[1]) * ax))
        else:
            axs = (box[0] + 0.3 - ext[0], box[2] - 0.3 - ext[2])
            ays = (box[1] + 0.3 - ext[1], box[3] - 0.3 - ext[3])
            nx = max(1, int((axs[1] - axs[0]) / 0.5) + 1) if axs[1] >= axs[0] else 1
            ny = max(1, int((ays[1] - ays[0]) / 0.5) + 1) if ays[1] >= ays[0] else 1
            for i in range(nx):
                ax = axs[0] + (axs[1] - axs[0]) * (i / (nx - 1) if nx > 1 else 0.5)
                for j in range(ny):
                    cands.append((ax, ays[0] + (ays[1] - ays[0]) * (j / (ny - 1) if ny > 1 else 0.5)))
        for ax, ay in cands:
            poly = lab_poly(M, ax, ay, W, H)
            e_ = bbox_of(poly)
            over = max(0.0, box[0] - e_[0], e_[2] - box[2], box[1] - e_[1], e_[3] - box[3])
            cl = _clear_of(dt, poly)
            ld = None
            if not is_tag:
                ld = lead_for(key, slot, st, M, ax, ay)
                _dbg = DBG_LABEL.setdefault(key, [0, 0, 0, 0])
                _dbg[0] += 1
                if LEAD_RULE.get(key) and ld is None:
                    _dbg[1] += 1
                    continue
                if ld and not _lead_ok(ld[0], poly):
                    _dbg[2] += 1
                    continue
                if ld and ld[2] > 0.5:
                    _dbg[3] += 1
                    continue
            L_len = sum(math.hypot(q2[0] - q1[0], q2[1] - q1[1]) for q1, q2 in zip(ld[0][:-1], ld[0][1:])) if ld else 0.0
            cxs, cys = (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0
            off_c = math.hypot((e_[0] + e_[2]) / 2.0 - cxs, (e_[1] + e_[3]) / 2.0 - cys)
            pref = LEAD_PREF.get(key) if not (INFO_ONLY and SIL) else (slot.get("target_pt") if slot.get("target_pt_spec") else LEAD_PREF.get(key))
            d_pref = math.hypot(ld[0][-1][0] - pref[0], ld[0][-1][1] - pref[1]) if (ld and pref) else 0.0
            score = (0.0 if over <= 0.45 else -over, min(cl, LABEL_CLEAR),
                     -L_len * 0.02 - (0.3 if vname not in ("기본", "tag", "주석") else 0.0) - off_c * 0.01 - d_pref * 0.3)
            if best is None or score > best[0]:
                best = (score, vname, st, ax, ay, poly, ld, cl, over)
    if best is None:
        REPORT["notes"].append("라벨 자리 없음: %s (후보·리드없음·리드불가·리드교차 %s) 막은 것 %s" % (key, DBG_LABEL.get(key), dict(LEAD_WHY)))
        return None
    score, vname, st, ax, ay, poly, ld, cl, over = best
    LABEL_PLAN[key] = dict(M=M, ax=ax, ay=ay, st=st, poly=poly, lead=ld, clear=cl, variant=vname, over=over, tag=is_tag, note=is_note,
                           top_line=list(tl) if tl else None)
    LABEL_POLYS.append((key, poly))
    if ld:
        PLACED_LEADS.append(ld[0])
    return LABEL_PLAN[key]


def tag_stack(slot):
    """말풍선 태그(2.6 고정, 자동 축소 없음). 넘치면 두 줄로 나눈다"""
    key_ = slot["name"].split("(")[0].strip()
    text = slot.get("tag_text") or TAG_TEXT_FALLBACK.get(key_) or key_
    M = lab_M(slot)
    box = slot["box"]
    lines = [text]
    W = twf(text, "b", LF_TAG) + 2.4
    H = LF_TAG + 1.8
    ext = bbox_of(lab_poly(M, 0, 0, W, H))
    if ext[2] - ext[0] > box[2] - box[0] - 0.6 or ext[3] - ext[1] > box[3] - box[1] - 0.6:
        ws = re.split(r"(?<=·) | (?=·)", text) if "·" in text else text.split(" ")
        if len(ws) >= 2:
            h = len(ws) // 2
            lines = [" ".join(ws[:h]).strip(), " ".join(ws[h:]).strip()]
            lines = [re.sub(r"^[\s·]+|[\s·]+$", "", s) for s in lines]   # 줄 끝·줄 머리의 구분점 '·'은 뺀다(통합 d3)
            W = max(twf(s, "b", LF_TAG) for s in lines) + 2.4
            H = LF_TAG * 2 + 1.3 + 1.8
    return {"lines": lines, "W": W, "H": H, "v_rule": None, "base_ko": None, "tag": True}


def plan_labels():
    """라벨 자리를 먼저 잡아 빈 자리 마스크에 넣는다(지붕·나무·밭이 라벨을 덮지 않게). 랜드마크 층을 그린 다음 부른다."""
    for key in LABEL_ORDER:
        if key not in SLOT:
            continue
        info = plan_label(key)
        if not info:
            continue
        ex_poly(info["poly"], LABEL_CLEAR + 0.7)
        if info["lead"]:
            ex_line(info["lead"][0], 4.0)          # 지시선 양옆 2mm는 나무·지붕·밭을 두지 않는다(통합 d3, panels 요청: 판테온 지시선 꺾임점 옆 사이프러스)


def draw_label(key):
    info = LABEL_PLAN.get(key)
    if not info:
        return
    slot = SLOT[key]
    M, ax, ay, st = info["M"], info["ax"], info["ay"], info["st"]
    if info["tag"]:
        draw_tag(key, slot, info)
        return
    W, H = st["W"], st["H"]
    f = Flat(W + 2.0, H + 1.5, INK_L)
    faces = {}
    is_note = bool(st.get("note"))
    for (s, kind, face, u, vb, role) in st["lines"]:
        ft, em, fa = fface(kind, face, s)
        f.text(u, vb, s, ft, INK_L)
        w = tw(s, ft)
        poly = [map_pt(M, ax, ay, uu, vv) for uu, vv in ((u, vb - fa), (u + w, vb - fa), (u + w, vb + 0.25), (u, vb + 0.25))]
        if is_note:
            rec_text(s, role, kind, em, fa, poly, layer="지도 소품 글 " + key, pitch=LF_PROP_PITCH if len(st["lines"]) > 1 else None)
        else:
            rec_text(s, role, kind, em, fa, poly, layer="지도 라벨 " + key, pitch=LF_PITCH if role == "label_body" and len(st["body"]) > 1 else None)
        faces.setdefault(role.replace("label_", ""), round(fa, 3))
    if st["has_rule"]:
        f.line(0, st["v_rule"], W, st["v_rule"], INK_L, 0.25)
    affine_paste(P, f, M, ax, ay)
    if is_note:
        rec = {"name": key, "kind": slot.get("kind", "소품 주석"), "poly": [[round(x, 2), round(y, 2)] for x, y in info["poly"]],
               "dir": "↗" if M is M_WALL_UP else "↘", "scale": 1.0, "slot": list(slot["box"]), "faces": {"prop_note": round(LF_PROP, 2)},
               "line_pitch_prop": LF_PROP_PITCH, "text": " / ".join(st["text"]), "en": [], "body": [], "variant": info["variant"],
               "slot_over_mm": round(info["over"], 2), "ink": list(INK_L), "bubble": False}
    else:
        rec = {"name": key, "kind": slot.get("kind", ""), "poly": [[round(x, 2), round(y, 2)] for x, y in info["poly"]],
               "dir": "↗" if M is M_WALL_UP else "↘", "scale": 1.0, "slot": list(slot["box"]), "faces": faces, "pitch": LF_PITCH,
               "en": st["en"], "ko": label_strings(slot, key)[1], "sup": [t_[0] for t_ in st["lines"] if t_[5] == "label_sup"][:1] or None,
               "body": st["body"], "variant": info["variant"], "slot_over_mm": round(info["over"], 2)}
        if isinstance(rec["sup"], list):
            rec["sup"] = rec["sup"][0]
    if info.get("top_line"):
        rec["top_line"] = info["top_line"]
    ld = info["lead"]
    if ld:
        pts, tname, gap = ld
        P.line(pts, INK_L, LEAD_W, joint=False)
        P.dot(pts[-1][0], pts[-1][1], DOT_RR, INK_L)
        rec["leader"] = {"pts": [[round(x, 2), round(y, 2)] for x, y in pts], "dot_d": 2 * DOT_RR, "target": tname, "gap": round(gap, 2), "lw": LEAD_W}
    DRAWN["labels"].append(rec)
    e = bbox_of(info["poly"])
    REPORT["labels"][key] = {"방향": rec["dir"], "슬롯": slot["box"], "그린 외곽": [round(v, 1) for v in e], "배율": 1.0, "조판": info["variant"],
                             "자리 잡을 때 간격mm": round(info["clear"], 2)}


def draw_tag(key, slot, info):
    """말풍선 태그(재료 시설 색, 흰 글자 2.6). 꼬리는 대상 시설 쪽"""
    M, ax, ay, st = info["M"], info["ax"], info["ay"], info["st"]
    W, H = st["W"], st["H"]
    fill = (198, 112, 58)
    pc = lab_poly(M, ax, ay, W, H)
    tgt = GEO.get("worksite_bb") if "공사장" in key else GEO.get("dock_bb")
    up = bool(tgt) and ((tgt[1] + tgt[3]) / 2.0 < (pc[0][1] + pc[3][1]) / 2.0)
    if up:
        tail = [map_pt(M, ax, ay, 2.2, 0.0), map_pt(M, ax, ay, 4.6, 0.0), map_pt(M, ax, ay, 2.6, -2.2)]
    else:
        tail = [map_pt(M, ax, ay, 2.2, H), map_pt(M, ax, ay, 4.6, H), map_pt(M, ax, ay, 2.6, H + 2.2)]
    P.poly(tail, fill=fill)
    P.poly(pc, fill=fill, outline=shade(fill, 0.7), lw=0.25)
    ft, em, fa = fface("b", LF_TAG, st["lines"][0])
    for i, s in enumerate(st["lines"]):
        vb = 0.9 + fa + i * (LF_TAG + 1.3)
        bl = map_pt(M, ax, ay, 1.2, vb)
        iso_text(P, s, ft, (255, 250, 240), M, bl[0], bl[1])
        w = tw(s, ft)
        poly = [map_pt(M, ax, ay, uu, vv) for uu, vv in ((1.2, vb - fa), (1.2 + w, vb - fa), (1.2 + w, vb + 0.25), (1.2, vb + 0.25))]
        rec_text(s, "tag", "b", em, fa, poly, layer="말풍선 태그 " + key)
    DRAWN["labels"].append({"name": key, "kind": "말풍선 태그", "poly": [[round(x, 2), round(y, 2)] for x, y in pc], "tail": [[round(x, 2), round(y, 2)] for x, y in tail],
                            "dir": "↗" if M is M_WALL_UP else "↘", "scale": 1.0, "slot": list(slot["box"]), "faces": {"tag": round(fa, 3)},
                            "text": " ".join(st["lines"]), "slot_over_mm": round(info["over"], 2)})
    e = bbox_of(pc)
    REPORT["labels"][key] = {"종류": "말풍선 태그", "슬롯": slot["box"], "그린 외곽": [round(v, 1) for v in e], "글자면mm": round(fa, 2), "줄": len(st["lines"])}


def draw_labels():
    for key in LABEL_ORDER:
        if key in SLOT:
            draw_label(key)


# ───────────────────────── 9 틀: 타이틀·패널(인쇄 지면에 보이는 것만) ─────────────────────────
def draw_title():
    # 20:40 사용자: 타이틀부 재디자인 → title_v3.py (베를린식 신전 정면 + ROMA 대형 세리프 + 파리식 부제 + 박공 안 시리즈 줄 + SPQR 명판)
    import title_v3
    DRAWN["title_v3"] = title_v3.draw(globals())


CH_EN, CH_KO = 7.0, 2.8          # 사용자 15:32·15:41: 장 영문 제목 글자면 7.0, 국문 장 질문 작은 부제 2.8


def chapter_badge(n, cx, cy, d=10.0, layer="장 배지"):
    # panels-v2: 숫자 글자면을 배지 지름에 비례(Ø10 → 5.6)
    """장 배지: 원을 로마 콘크리트란? 제목색(ACCENT)으로 채우고 흰 숫자. 모든 장이 같은 모양"""
    return                                              # 20:35 사용자: 1~6 번호 표시 전부 제거(장 배지 없음)
    r = d / 2.0
    P.ell(cx, cy, r, r, fill=ACCENT)
    f, em, fa = fface("b", 5.6 * d / 10.0, str(n))
    yb = cy + fa / 2.0
    P.text(cx, yb, str(n), f, (255, 255, 255), anchor="ms")
    bb = f.getbbox(str(n), anchor="ms")
    rec_text(str(n), "badge", "b", em, fa, box_poly((cx + bb[0] / KD, yb + bb[1] / KD, cx + bb[2] / KD, yb + bb[3] / KD)), layer)
    DRAWN["texts"][-1].update({"chapter_badge": int(n), "c": [round(cx, 2), round(cy, 2)], "d": d})
    DRAWN.setdefault("badges", []).append({"n": int(n), "c": [round(cx, 2), round(cy, 2)], "d": d, "ink": list(ACCENT), "layer": layer})


def chapter_header(pid, n, en, ko, x0, x1, yb, en_x=None, ko_baseline=None, en_face=None, badge_d=None):
    # panels-v2: 장 머리글 + 제목 글자면(en_face)·배지 지름(badge_d)을 패널마다 다르게 줄 수 있다(Basic 위계: ❶ 8.4 > ❹ 7.6 > ❷ 7.0 > ❺ 6.6 > ❻ 6.2)
    """장 머리글: 배지(영문 제목 왼쪽, 제목 대문자 높이 가운데) + 영문 제목(기본 7.0) + 국문 장 질문 부제 2.8(영문 옆, 넘치면 아랫줄 왼쪽 맞춤)"""
    lay = "패널 " + pid
    ef = float(en_face) if en_face else CH_EN
    bd = float(badge_d) if badge_d else 10.0
    fe = fface("en", ef, en)[2]
    chapter_badge(n, x0 + bd / 2.0, yb - fe / 2.0, d=bd, layer=lay)
    ex = x0                                             # 20:35 번호 배지 없음 → 제목을 패널 왼쪽 변에 맞춘다
    box, fa = ptext(ex, yb, en, "en", ef, ACCENT, "head_en", layer=lay, panel=pid)
    if not ko or ko == en:   # 사용자 17:28·17:29: 부제가 제목과 뜻이 겹치면 둘 중 하나만
        return yb, None
    kw = twf(ko, "b", CH_KO)
    if box[2] + 2.0 + kw <= x1 + 0.01 and ko_baseline is None:
        ptext(box[2] + 2.0, yb, ko, "b", CH_KO, ACCENT, "subtitle", layer=lay, panel=pid)
        return yb, None
    kb = ko_baseline if ko_baseline is not None else yb + 1.8 + fface("b", CH_KO, ko)[2]
    ptext(ex, kb, ko, "b", CH_KO, ACCENT, "subtitle", layer=lay, panel=pid)
    return yb, kb


# ───────────────────────── 땅 무늬·강 디테일·지형(map_fx.py, 19:2x 사용자 지시: Core만 + 땅 무늬·둑·지형) ─────────────────────────
HILLS = [("albano", (388.0, 466.0), -23.0, 1.0, (64.0, 22.0)), ("vesuvio", (398.0, 436.0), 0.0, 1.0, None)]


def draw_fx_ground():
    try:
        import map_fx as FX
        import random as _r
    except Exception as e_:                                          # noqa: BLE001
        REPORT["notes"].append("map_fx 못 읽음: %s" % e_)
        return
    rng = _r.Random("땅 무늬")
    poly = [tuple(p) for p in RV["polygon_screen"]]
    sea = [tuple(p) for p in SC["sea_polygon"]]
    n = FX.draw_ground_texture(P, (0.0, STAGE[1], 420.0, STAGE[3]), rng, mask_polys=[poly, sea], density=1.8)
    DRAWN["fx_ground_marks"] = n


def draw_fx_river():
    try:
        import map_fx as FX
        import random as _r
    except Exception as e_:                                          # noqa: BLE001
        return
    rng = _r.Random("강 디테일")
    left, right = GEO.get("river_left"), GEO.get("river_right")
    return                                                           # 20:53 새 물(직사각형 합)에서는 사인 물결 대신 면 무늬만 쓴다
    if not left or not right:
        return
    cl = [((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0) for a, b in zip(left, right)]
    DRAWN["fx_river_waves"] = FX.draw_river_detail(P, left, right, cl, 25.0, rng)


def draw_mountain_band(P_, rng):
    """22:35 타이틀 아래 산맥 띠: 화면 가로 능선(X·Y축 제약 없음). 뒤·가운데·앞 3겹, 멀수록 연하고 푸르게, 아래 자락은 땅에 스며든다. 꼭대기는 y 96 이하."""
    MB = (CM.get("mountain_band") or {})
    if not MB:
        return
    ybase = MB["ridge_base_y"]
    hz = MB["haze"]
    ground = (240, 218, 170)
    haze_c = (200, 206, 206)
    cols = [(172, 186, 176), (156, 176, 150), (140, 162, 126)]
    peak_sets = [
        [(18, 14, 38), (70, 18, 46), (132, 13, 40), (196, 17, 52), (262, 12, 44), (322, 16, 48), (388, 13, 40)],
        [(40, 12, 34), (104, 15, 40), (166, 11, 36), (232, 15, 44), (296, 11, 38), (352, 14, 42), (412, 11, 32)],
        [(0, 9, 30), (62, 11, 34), (126, 8, 32), (214, 10, 38), (280, 8, 30), (338, 10, 36), (400, 8, 30)],
    ]
    Lm = Layer(0, 90, PW, 134)
    for li in range(3):
        yb = ybase[li]
        pts = []
        xs = [i * 1.5 for i in range(-4, int(PW / 1.5) + 6)]
        for x in xs:
            h = 0.0
            for (xc, hh, ww) in peak_sets[li]:
                u = abs(x - xc) / ww
                if u < 1.0:
                    h = max(h, 0.82 * hh * (1.0 - u) ** 1.25 * (1.0 + 0.06 * math.sin(x * 0.9 + li)))
            h += 1.6 + 0.9 * math.sin(x * 0.11 + li * 1.7)
            pts.append((x, yb - h))
        c0 = tuple(int(cols[li][k] * (1 - hz[li]) + haze_c[k] * hz[li]) for k in range(3))
        poly = pts + [(xs[-1], yb + 14), (xs[0], yb + 14)]
        Ll = Layer(0, 90, PW, 134)
        Ll.poly(poly, fill=c0)
        # 오른쪽 사면 그늘(꼭대기 오른쪽 아래로 짙은 면)
        for (xc, hh, ww) in peak_sets[li]:
            yk = yb - hh
            sh_ = [(xc, yk + 0.2), (xc + ww * 0.85, yb + 2), (xc + 2.0, yb + 2)]
            Ll.poly(sh_, fill=tuple(int(v * 0.90) for v in c0))
            Ll.line([(xc, yk), (xc + ww * 0.5, yk + hh * 0.55)], tuple(int(v * 0.84) for v in c0), 0.18, joint=False)
        g = Image.linear_gradient("L").resize((Ll.w, Ll.h)).point(lambda v: 255 - v)             # 아래로 갈수록 투명
        gy0 = int((yb - 8 - 90) * KD)
        gm = Image.new("L", (Ll.w, Ll.h), 255)
        for yy in range(max(0, gy0), Ll.h):
            a_ = max(0.0, 1.0 - (yy - gy0) / (22.0 * KD))
            ImageDraw.Draw(gm).line([(0, yy), (Ll.w, yy)], fill=int(255 * a_))
        Ll.img.putalpha(ImageChops.multiply(Ll.img.getchannel("A"), gm))
        Lm.img.alpha_composite(Ll.img)
    # 베수비오(오른쪽 끝 가장 작은 봉우리, 분화구)
    ve = MB.get("vesuvio") or {}
    if ve:
        vx, vh = ve["x"], ve["h"]
        yb = ybase[2] + 2.0
        hz_ = 0.34                                           # 연한 대기 원근
        def hzc(c):
            return tuple(int(c[k] * (1 - hz_) + haze_c[k] * hz_) for k in range(3))
        n_ = 14
        lw_, tw_ = 21.0, 5.6                                 # 밑 반폭 / 분화구 윗면 반폭: 넓고 완만한 원뿔
        def side(sg):                                        # 오목하게 올라가는 사면
            return [(vx + sg * (tw_ + (lw_ - tw_) * (t_ / n_) ** 1.7), yb - vh * (1 - t_ / n_) ** 1.0 * 1.0) for t_ in range(n_ + 1)]
        L_, R_ = side(-1), side(1)
        body = [L_[0]] + [p for p in L_[1:]] + [p for p in reversed(R_)]
        Lm.poly(body, fill=hzc((158, 140, 118)))
        Lm.poly([(vx + 0.5, yb - vh)] + R_[0:0] + list(reversed(R_)) + [(vx + 2.0, yb)], fill=hzc((128, 110, 94)))   # 오른쪽 그늘면
        rim_c = hzc((104, 90, 78))
        Lm.poly([(vx - tw_, yb - vh), (vx + tw_, yb - vh), (vx + tw_ - 1.2, yb - vh + 1.6), (vx - tw_ + 1.2, yb - vh + 1.6)], fill=rim_c)   # 평평한 분화구 정상
        Lm.poly([(vx - tw_ + 1.4, yb - vh + 0.35), (vx + tw_ - 1.4, yb - vh + 0.35), (vx + tw_ - 2.6, yb - vh + 1.2), (vx - tw_ + 2.6, yb - vh + 1.2)], fill=hzc((84, 72, 64)))
        for gx_, gk_ in ((-0.66, 0.9), (-0.30, 1.0), (0.05, 0.85), (0.38, 1.0), (0.70, 0.88)):   # 사면 골
            x0_ = vx + gx_ * tw_ * 1.15
            x1_ = vx + gx_ * lw_ * 0.92
            Lm.line([(x0_, yb - vh + 1.8), (x0_ * 0.45 + x1_ * 0.55 + (0.8 if gx_ > 0 else -0.8), yb - vh * 0.5), (x1_, yb - 0.4)], hzc((112, 96, 82)), 0.22, joint=False)
    P_.paste(Lm)
    DRAWN["mountain_band"] = {"y_range": [96.0, 134.0], "layers": 3, "peaks": [len(x) for x in peak_sets], "vesuvio": ve}


def draw_fx_hills():
    """20:53 지형: 실제 크기·방향 평면 발자국(창 밖까지), 가장자리 원근 축소 s(d) + 대기 원근(안개색 섞기). 별도 판(옆면)이 아니라 땅에서 솟는다(flat_base)."""
    try:
        import map_fx as FX
        import random as _r
    except Exception as e_:                                          # noqa: BLE001
        return
    rng = _r.Random("구릉")
    DRAWN["terrain"] = []
    hz_c = tuple((CM.get("perspective") or {}).get("haze_color", [178, 196, 208]))
    for t_ in sorted(CM.get("terrain") or [], key=lambda t: -t["plan_center"][0] - t["plan_center"][1] if t["id"] != "vesuvio" else -1e9):
        s_, h_ = float(t_["persp_scale"]), float(t_["haze"])
        ph = (t_["plan_half"][0] * s_, t_["plan_half"][1] * s_)
        box = FX.draw_hills(P, "albano" if t_["kind"] == "albano" else "vesuvio", t_["screen_center"], rng, axis_deg=0.0, scale=1.0,
                            size=(60.0, float(t_["height_mm"]) * s_ + 1.0), plan_half=ph, yaw_deg=t_["yaw_deg"], haze=(hz_c, h_), flat_base=True)
        DRAWN["terrain"].append({"name": t_["name"], "anchor": t_["screen_center"], "dist_mm": t_["dist_mm"], "persp_scale": t_["persp_scale"], "haze": t_["haze"], "box": box})
    draw_mountain_band(P, rng)


# ───────────────────────── 건물별 Detail 확대 창(19:35) ─────────────────────────
def _win_tf(w):
    return 1.0 + (float(w["d"]) - 30.0) / 30.0 * 0.5


def _win_half(w):
    """창 반폭·반높이(mm): 원 = d/2 두 개, 판(plate) = plate_wh/2"""
    if w.get("shape") == "plate":
        return w["plate_wh"][0] / 2.0, w["plate_wh"][1] / 2.0
    return w["d"] / 2.0, w["d"] / 2.0

def _window_box(w):
    cx, cy = w["c"]
    hw, hh = _win_half(w)
    tf = _win_tf(w)
    tw, th = 38.0 * tf, 18.5 * tf
    side = w.get("side", "below")
    if side == "right":
        return [cx - hw - 1.0, cy - hh - 1.0, cx + hw + 3.0 + tw, cy + hh + 1.0]
    if side == "left":
        return [cx - hw - 3.0 - tw, cy - hh - 1.0, cx + hw + 1.0, cy + hh + 1.0]
    if side == "above":
        return [cx - max(hw + 1.0, tw / 2.0), cy - hh - th, cx + max(hw + 1.0, tw / 2.0), cy + hh + 1.0]
    return [cx - max(hw + 1.0, tw / 2.0), cy - hh - 1.0, cx + max(hw + 1.0, tw / 2.0), cy + hh + th]


WIN_OBJ = {"네로 거상": "네로 거상 받침", "콜로세움": "hero", "판테온": "L1", "카라칼라 욕장": "L3", "트라야누스 시장": "L2", "카이킬리아 메텔라 무덤": "L5", "포르투스 항": "L6",
           "막센티우스 바실리카": "L7", "하드리아누스 영묘": "L8", "마르켈루스 극장": "L9", "수도교": "L4"}
WIN_AVOID_BOXES = [[356.0, 440.0, 420.0, 478.0]]
PINS = {("win", "포르투스 항"): (292.0, 418.0, "right"), ("lab", "포르투스 항"): (207.0, 400.0), ("win", "마르켈루스 극장"): (34.0, 198.0, "above"), ("lab", "마르켈루스 극장"): (88.0, 228.0), ("win", "하드리아누스 영묘"): (188.0, 388.0, "right"), ("lab", "콜로세움"): (240.0, 317.0), ("win", "수도교"): (283.0, 112.0, "left")}   # 손으로 고정한 자리: 창 = (x, y, 글 쪽), 라벨 = (x, y)



def auto_place_all():
    """20:53 확대 창 10개 + 라벨 11개를 한꺼번에 자동 배치. 후보 자리가 가장 적은 것부터 놓아 자리 다툼을 줄인다.
    창: 원(건물·물·도로 피함) + 글 칸(건물만 피함), 라벨: 글 블록 상자(건물·물·창 피함, 도로 위는 허용). 거리 = 건물 실루엣까지(짧을수록 좋음)."""
    import numpy as np
    import cv2
    import v2_windows as _W
    S2 = 2
    Hh, Ww = PH * S2, PW * S2
    mask = np.array(OBJ.img.getchannel("A").resize((Ww, Hh), Image.BOX)) > 20
    mk = Image.new("L", (Ww, Hh), 0)
    ImageDraw.Draw(mk).rectangle([0, 0, Ww, 92 * S2], fill=255)
    ImageDraw.Draw(mk).rectangle([0, 478 * S2, Ww, Hh], fill=255)
    ImageDraw.Draw(mk).rectangle([420 * S2, 0, Ww, Hh], fill=255)
    for b_ in WIN_AVOID_BOXES:
        ImageDraw.Draw(mk).rectangle([b_[0] * S2, b_[1] * S2, b_[2] * S2, b_[3] * S2], fill=255)
    for r_ in (RV.get("water_rects") or []):                                      # 테베레는 구획을 가르는 큰 경계: 창·라벨이 건너지 않는다
        if r_["id"] == "tiber":
            ImageDraw.Draw(mk).polygon([(x * S2, y * S2) for x, y in r_["polygon_screen"]], fill=255)
    mks = Image.new("L", (Ww, Hh), 0)                                           # 물·도로: 겹치면 감점(금지 아님)
    for pg in (GEO.get("water_rects") or []) + (GEO.get("road_polys") or []):
        ImageDraw.Draw(mks).polygon([(x * S2, y * S2) for x, y in pg], fill=255)
    ker = np.ones((int(1.6 * S2) * 2 + 1,) * 2, np.uint8)
    base_t = cv2.dilate((mask | (np.array(mk) > 0)).astype(np.uint8), ker) > 0
    base_r = base_t.copy()
    soft_np = np.array(mks) > 0
    mkw = Image.new("L", (Ww, Hh), 0)
    for pg in (GEO.get("water_rects") or []):
        ImageDraw.Draw(mkw).polygon([(x * S2, y * S2) for x, y in pg], fill=255)
    water_np = np.array(mkw) > 0
    road_np = soft_np & ~water_np
    comp_map = cv2.connectedComponents((~water_np).astype(np.uint8), connectivity=4)[1]
    FPN = {"콜로세움": "콜로세움 건물", "판테온": "아크로폴리스 지면", "트라야누스 시장": "시장 지면", "카이킬리아 메텔라 무덤": "메텔라 대지", "포르투스 항": "포르투스 육각 내항",
           "막센티우스 바실리카": "바실리카 지면", "하드리아누스 영묘": "영묘 기단", "마르켈루스 극장": "극장 반원 아케이드", "수도교": "시장 지면", "네로 거상": "메텔라 대지"}

    def block_of(key):
        fp = next((f for f in DRAWN["footprints"] if f["name"] == FPN.get(key)), None)
        if not fp:
            return None
        pg = fp["poly"]
        cx_ = sum(p[0] for p in pg) / len(pg)
        cy_ = sum(p[1] for p in pg) / len(pg)
        ix, iy = int(cx_ * S2), int(cy_ * S2)
        if 0 <= iy < Hh and 0 <= ix < Ww:
            return int(comp_map[iy, ix])
        return None
    blk_of = {k: block_of(k) for k in FPN}
    objbox = {k: v["그린 외곽"] for k, v in REPORT["objects"].items()}
    if "hero" not in objbox:
        objbox["hero"] = list(CO_BOX)

    def sat(m):
        z = np.zeros((m.shape[0] + 1, m.shape[1] + 1), np.int32)
        z[1:, 1:] = np.cumsum(np.cumsum(m.astype(np.int32), 0), 1)
        return z

    def free_map(satm, bx_w, bx_h, ox, oy):
        """상자(폭 bx_w, 높이 bx_h mm)의 왼쪽 위가 (x, y)일 때 비어 있나. 반환 배열 [y, x] (S2 격자), 상자 왼쪽 위 = (x, y)/S2 + 오프셋 (ox, oy) 없음"""
        wp, hp = int(math.ceil(bx_w * S2)), int(math.ceil(bx_h * S2))
        H_, W_ = satm.shape[0] - 1, satm.shape[1] - 1
        out = np.zeros((H_, W_), bool)
        ys, xs = H_ - hp + 1, W_ - wp + 1
        if ys <= 0 or xs <= 0:
            return out, wp, hp
        v = satm[hp:hp + ys, wp:wp + xs] - satm[0:ys, wp:wp + xs] - satm[hp:hp + ys, 0:xs] + satm[0:ys, 0:xs]
        out[:ys, :xs] = v == 0
        return out, wp, hp

    def free_map_cnt(satm, bx_w, bx_h):
        """상자 안 칸 수(물·도로 겹침 감점용)"""
        wp, hp = int(math.ceil(bx_w * S2)), int(math.ceil(bx_h * S2))
        H_, W_ = satm.shape[0] - 1, satm.shape[1] - 1
        out = np.zeros((H_, W_), np.float32)
        ys, xs = H_ - hp + 1, W_ - wp + 1
        if ys > 0 and xs > 0:
            out[:ys, :xs] = satm[hp:hp + ys, wp:wp + xs] - satm[0:ys, wp:wp + xs] - satm[hp:hp + ys, 0:xs] + satm[0:ys, 0:xs]
        return out, wp, hp

    items = []
    for w in _W.DETAIL_WINDOWS:
        oid = WIN_OBJ.get(w["key"])
        if oid in objbox:
            items.append({"kind": "win", "key": w["key"], "w": w, "oid": oid})
    for key in LABEL_ORDER:
        slot = SLOT.get(key)
        oid = WIN_OBJ.get(key)
        if slot and oid in objbox:
            items.append({"kind": "lab", "key": key, "slot": slot, "oid": oid})
    # 건물별 실루엣 거리 지도
    dmaps = {}
    for it in items:
        oid = it["oid"]
        if oid in dmaps:
            continue
        ob = objbox[oid]
        m = np.zeros_like(mask)
        x0, y0, x1, y1 = [int(v * S2) for v in (max(0, ob[0] - 3), max(0, ob[1] - 3), ob[2] + 3, ob[3] + 3)]
        m[y0:y1, x0:x1] = mask[y0:y1, x0:x1]
        dmaps[oid] = cv2.distanceTransform((~m).astype(np.uint8), cv2.DIST_L2, 5) / S2
    st_t, st_r = sat(base_t), sat(base_r)
    st_soft = sat(soft_np)
    # 각 항목의 후보 만들기
    for it in items:
        cands = []
        if it["kind"] == "win":
            w = it["w"]
            r = w["d"] / 2.0
            for side in ("below", "right", "left", "above"):
                bx = _window_box({"c": (0.0, 0.0), "d": w["d"], "side": side, "shape": w.get("shape"), "plate_wh": w.get("plate_wh")})   # 중심 (0,0) 기준 상자
                bw, bh = bx[2] - bx[0], bx[3] - bx[1]
                f_all, wp, hp = free_map(st_t, bw, bh, 0, 0)
                # 원은 따로 더 엄격하게: 원 상자 (2r × 2r) 도로 포함
                f_ring, rwp, rhp = free_map(st_r, 2 * r, 2 * r, 0, 0)
                cands.append((side, bx, f_all, wp, hp, f_ring, rwp, rhp))
            it["cands"] = cands
        else:
            slot = it["slot"]
            M = lab_M(slot)
            stk0 = label_stack(slot, it["key"])
            stk = label_stack(slot, it["key"], maxw=stk0["W"] * 0.66, sup_own=True)          # 좁은 변형(본문 줄바꿈)으로 자리를 잡는다
            ext = bbox_of(lab_poly(M, 0, 0, stk["W"], stk["H"]))
            bw, bh = ext[2] - ext[0], ext[3] - ext[1]
            f_all, wp, hp = free_map(st_t, bw, bh, 0, 0)
            it["lab_dims"] = (bw, bh, f_all, wp, hp)
    sil_cache = {}

    def sil_pts(oid):
        if oid not in sil_cache:
            ob = objbox[oid]
            x0, y0 = int(max(0, ob[0] - 3) * S2), int(max(0, ob[1] - 3) * S2)
            sub = mask[y0:int((ob[3] + 3) * S2), x0:int((ob[2] + 3) * S2)]
            ys2, xs2 = np.nonzero(sub)
            if len(xs2) > 6000:
                sel = np.arange(0, len(xs2), max(1, len(xs2) // 6000))
                ys2, xs2 = ys2[sel], xs2[sel]
            sil_cache[oid] = (xs2 / S2 + x0 / S2, ys2 / S2 + y0 / S2)
        return sil_cache[oid]

    def path_pen(oid, ref, r0):
        """ref에서 건물 실루엣 가장 가까운 점까지 등각 축 꺾은선 지시선: 길이 증가분 + 물·도로 통과 감점. 반환 (추가 비용, 경로)"""
        sx, sy = sil_pts(oid)
        k = int(np.argmin((sx - ref[0]) ** 2 + (sy - ref[1]) ** 2))
        t = (float(sx[k]), float(sy[k]))
        dist = math.hypot(t[0] - ref[0], t[1] - ref[1])
        best = None
        for L_, pts_ in axis_paths(ref, t)[:4]:
            wh = rh = n_ = 0
            for q1, q2 in zip(pts_[:-1], pts_[1:]):
                m_ = max(2, int(math.hypot(q2[0] - q1[0], q2[1] - q1[1]) / 2.0))
                for q in range(1, m_):
                    xx = q1[0] + (q2[0] - q1[0]) * q / m_
                    yy = q1[1] + (q2[1] - q1[1]) * q / m_
                    ix, iy = int(xx * S2), int(yy * S2)
                    n_ += 1
                    if 0 <= iy < Hh and 0 <= ix < Ww:
                        wh += 1 if water_np[iy, ix] else 0
                        rh += 1 if road_np[iy, ix] else 0
            pen = max(0.0, L_ - r0 - (dist - r0)) + 12.0 * wh / max(1, n_) + 4.0 * rh / max(1, n_)
            if best is None or pen < best[0]:
                best = (pen, pts_)
        return best

    def cand_item(it, st_t_now, topn=400, use_blk=True):
        """정적 장애물(건물·경계)만 피하는 후보 [(거리비용, side, x, y, rect)] — 거리 짧은 순, 자리 다양화"""
        D = dmaps[it["oid"]]
        out = []
        ob_ = objbox[it["oid"]]
        if it["kind"] == "win":
            w = it["w"]
            r = w["d"] / 2.0
            for side in ("below", "right", "left", "above"):
                bx = _window_box({"c": (0.0, 0.0), "d": w["d"], "side": side, "shape": w.get("shape"), "plate_wh": w.get("plate_wh")})
                bw, bh = bx[2] - bx[0], bx[3] - bx[1]
                f_all, wp, hp = free_map(st_t_now, bw, bh, 0, 0)
                H_, W_ = f_all.shape
                ys, xs = np.mgrid[0:H_, 0:W_]
                cxm = xs / S2 - bx[0]
                cym = ys / S2 - bx[1]
                ok = f_all & (cxm - r > 0.5) & (cxm + r < 419.5) & (cym - r > 92.5) & (cym + r < 477.5)
                bx0_, by0_, bx1_, by1_ = cxm + bx[0], cym + bx[1], cxm + bx[2], cym + bx[3]
                pen_blk = 0.0
                blk_ = blk_of.get(it["key"]) if use_blk else None
                if blk_:
                    ci0 = np.clip((cxm * S2).astype(int), 0, Ww - 1)
                    cj0 = np.clip((cym * S2).astype(int), 0, Hh - 1)
                    bcx = np.clip(((bx0_ + bx1_) * 0.5 * S2).astype(int), 0, Ww - 1)
                    bcy = np.clip(((by0_ + by1_) * 0.5 * S2).astype(int), 0, Hh - 1)
                    pen_blk = 30.0 * (comp_map[cj0, ci0] != blk_) + 10.0 * (comp_map[bcy, bcx] != blk_)
                ok &= ~((bx0_ < ob_[2] - 3.0) & (bx1_ > ob_[0] + 3.0) & (by0_ < ob_[3] - 3.0) & (by1_ > ob_[1] + 3.0))
                ci = np.clip((cxm * S2).astype(int), 0, W_ - 1)
                cj = np.clip((cym * S2).astype(int), 0, H_ - 1)
                wsoft, _a, _b = free_map_cnt(st_soft, bw, bh)
                L = D[cj, ci] - r + 20.0 * wsoft / max(1.0, bw * bh * S2 * S2) + pen_blk
                Lm = np.where(ok, L, 1e9)
                idx = np.argsort(Lm.ravel())[:12000]
                for k in idx:
                    if Lm.flat[k] >= 1e8:
                        break
                    j, i = divmod(int(k), W_)
                    cx_, cy_ = float(cxm[j, i]), float(cym[j, i])
                    if any(abs(cx_ - o[2]) < 6.0 and abs(cy_ - o[3]) < 6.0 and side == o[1] for o in out):
                        continue
                    out.append((float(Lm.flat[k]), side, cx_, cy_, [cx_ + bx[0], cy_ + bx[1], cx_ + bx[2], cy_ + bx[3]]))
        else:
            bw, bh = it["lab_dims"][0], it["lab_dims"][1]
            f_all, wp, hp = free_map(st_t_now, bw, bh, 0, 0)
            H_, W_ = f_all.shape
            Dm = cv2.erode(D.astype(np.float32), np.ones((hp, wp), np.uint8))
            ys_, xs_ = np.mgrid[0:H_, 0:W_]
            ok = f_all & (xs_ / S2 > 0.5) & (xs_ / S2 + bw < 419.5) & (ys_ / S2 > 92.5) & (ys_ / S2 + bh < 477.5)
            ok &= ~((xs_ / S2 < ob_[2] - 3.0) & (xs_ / S2 + bw > ob_[0] + 3.0) & (ys_ / S2 < ob_[3] - 3.0) & (ys_ / S2 + bh > ob_[1] + 3.0))
            blk_ = blk_of.get(it["key"]) if use_blk else None
            if blk_:
                lcx = np.clip(((xs_ / S2 + bw / 2.0) * S2).astype(int), 0, Ww - 1)
                lcy = np.clip(((ys_ / S2 + bh / 2.0) * S2).astype(int), 0, Hh - 1)
                pen_lab = 30.0 * (comp_map[lcy, lcx] != blk_)
            else:
                pen_lab = 0.0
            sh = np.full_like(Dm, 1e9)
            sh[:H_ - hp // 2, :W_ - wp // 2] = Dm[hp // 2:, wp // 2:]
            wsoft, _a, _b = free_map_cnt(st_soft, bw, bh)
            L = sh + 20.0 * wsoft / max(1.0, bw * bh * S2 * S2) + pen_lab
            Lm = np.where(ok, L, 1e9)
            idx = np.argsort(Lm.ravel())[:12000]
            for k in idx:
                if Lm.flat[k] >= 1e8:
                    break
                j, i = divmod(int(k), W_)
                x_, y_ = i / S2, j / S2
                if any(abs(x_ - o[2]) < 5.0 and abs(y_ - o[3]) < 5.0 for o in out):
                    continue
                out.append((float(Lm.flat[k]), "lab", x_, y_, [x_, y_, x_ + bw, y_ + bh]))
        out = out[:topn]
        res = []
        for (Lc, sd, xc, yc, rc) in out:
            if sd == "lab":
                ref = (rc[0] + (rc[2] - rc[0]) / 2.0, rc[1] + (rc[3] - rc[1]) / 2.0)
                r0 = 0.5 * min(rc[2] - rc[0], rc[3] - rc[1])
            else:
                ref = (xc, yc)
                r0 = it["w"]["d"] / 2.0
            pen, pth = path_pen(it["oid"], ref, r0)
            if sd != "lab" and len(pth) >= 2:
                vx_, vy_ = pth[-1][0] - ref[0], pth[-1][1] - ref[1]
                dd_ = math.hypot(vx_, vy_) or 1.0
                # 글 칸이 원과 건물 사이에 끼면(지시선이 글을 가로지름) 제외
                if (sd == "below" and vy_ > 0.4 * dd_) or (sd == "above" and vy_ < -0.4 * dd_) or (sd == "right" and vx_ > 0.4 * dd_) or (sd == "left" and vx_ < -0.4 * dd_):
                    continue
            res.append((Lc + pen, sd, xc, yc, rc, pth))
        return res

    import random as _rr
    cands_all = []
    for it in items:
        pin = PINS.get((it["kind"], it["key"]))
        if pin:
            if it["kind"] == "win":
                cx_, cy_, sd_ = pin
                bx_ = _window_box({"c": (cx_, cy_), "d": it["w"]["d"], "side": sd_})
                pn_, pth_ = path_pen(it["oid"], (cx_, cy_), it["w"]["d"] / 2.0)
                cs = [(0.0, sd_, float(cx_), float(cy_), bx_, pth_)]
            else:
                x0_, y0_ = pin
                bw_, bh_ = it["lab_dims"][0], it["lab_dims"][1]
                rc_ = [float(x0_), float(y0_), float(x0_) + bw_, float(y0_) + bh_]
                pn_, pth_ = path_pen(it["oid"], ((rc_[0] + rc_[2]) / 2.0, (rc_[1] + rc_[3]) / 2.0), 0.5 * min(bw_, bh_))
                cs = [(0.0, "lab", float(x0_), float(y0_), rc_, pth_)]
        else:
            cs = cand_item(it, st_t)
        if not cs:
            REPORT["notes"].append("구획 안 자리 없음(구획 제한 해제): %s %s" % (it["kind"], it["key"]))
            cs = cand_item(it, st_t, use_blk=False)
        if not cs:
            cs = [(900.0, "none", 0.0, 0.0, [-999.0, -999.0, -998.0, -998.0], None)]
        cands_all.append(cs)
    n = len(items)
    # 후보 쌍 겹침(여유 1.5mm) 행렬
    rects = [np.array([c[4] for c in cs]) for cs in cands_all]

    def overlap(ra, rb, m=3.0):
        return (ra[:, None, 0] < rb[None, :, 2] + m) & (ra[:, None, 2] > rb[None, :, 0] - m) & (ra[:, None, 1] < rb[None, :, 3] + m) & (ra[:, None, 3] > rb[None, :, 1] - m)
    OV = {}
    for i in range(n):
        for j in range(i + 1, n):
            OV[(i, j)] = overlap(rects[i], rects[j])

    def ov(i, ci, j, cj):
        return OV[(i, j)][ci, cj] if i < j else OV[(j, i)][cj, ci]
    costs = [np.array([(c[0] if c[0] < 15.0 else 15.0 + (c[0] - 15.0) * 4.0) for c in cs]).clip(max=900.0) for cs in cands_all]
    def total(st):
        t = sum(costs[i][st[i]] for i in range(n))
        for i in range(n):
            for j in range(i + 1, n):
                if ov(i, st[i], j, st[j]):
                    t += 3000.0
        return t
    best_state, best_cost = None, 1e18
    iters = int(os.environ.get("AUTO_ITERS", "60000"))
    for seed_ in range(int(os.environ.get("AUTO_SEEDS", "6"))):
        rng_ = _rr.Random(7 + seed_ * 101)
        state = [int(np.argmin(c)) if seed_ == 0 else rng_.randrange(len(c)) for c in costs]
        cur = total(state)
        T0 = 80.0
        for it_no in range(iters):
            T = T0 * (1.0 - it_no / iters) + 0.5
            i = rng_.randrange(n)
            ci_new = rng_.randrange(len(cands_all[i]))
            ci_old = state[i]
            if ci_new == ci_old:
                continue
            d_ = costs[i][ci_new] - costs[i][ci_old]
            for j in range(n):
                if j == i:
                    continue
                if ov(i, ci_new, j, state[j]):
                    d_ += 3000.0
                if ov(i, ci_old, j, state[j]):
                    d_ -= 3000.0
            if d_ < 0 or rng_.random() < math.exp(-d_ / T):
                state[i] = ci_new
                cur += d_
                if cur < best_cost - 1e-9:
                    best_cost, best_state = cur, list(state)
    placed = []
    for i, it in enumerate(items):
        L, side, x_, y_, rect, pth_ = cands_all[i][best_state[i]]
        if side == "none":
            REPORT["notes"].append("자리 없음: %s %s" % (it["kind"], it["key"]))
            continue
        if it["kind"] == "win":
            w = it["w"]
            w["c"] = (round(x_, 1), round(y_, 1))
            w["side"] = side
            ob = objbox[it["oid"]]
            ys2, xs2 = np.nonzero(mask[int(max(0, ob[1] - 3) * S2):int((ob[3] + 3) * S2), int(max(0, ob[0] - 3) * S2):int((ob[2] + 3) * S2)])
            px = xs2 / S2 + max(0, ob[0] - 3)
            py = ys2 / S2 + max(0, ob[1] - 3)
            k = int(np.argmin((px - x_) ** 2 + (py - y_) ** 2))
            w["t"] = (round(float(px[k]), 1), round(float(py[k]), 1))
            w["path"] = pth_
            INFO_BOXES.append(("확대 창 " + w["key"], box_poly(_window_box(w))))
            placed.append(("win", w["key"], w["c"], side, round(L, 1), 0))
        else:
            slot = it["slot"]
            slot["box"] = [round(rect[0] - 1.5, 1), round(rect[1] - 1.5, 1), round(rect[2] + 1.5, 1), round(rect[3] + 1.5, 1)]
            for k_ in ("top_edge", "block_poly"):
                slot.pop(k_, None)
            placed.append(("lab", it["key"], slot["box"], round(L, 1), 0))
    DRAWN["auto_place_cost"] = round(best_cost, 1)
    DRAWN["auto_place_overlaps"] = [[items[i]["kind"] + ":" + items[i]["key"], items[j]["kind"] + ":" + items[j]["key"]] for i in range(n) for j in range(i + 1, n) if ov(i, best_state[i], j, best_state[j])]
    DRAWN["auto_place"] = placed


def draw_detail_windows():
    """Core 건물 곁 Detail: 원 안 확대 단면(zoom_figs_*.py) + 주황 테 + 지시선 + 제목 1줄·본문 2줄 + 수치 칩(Support)."""
    import importlib
    import random as _rnd
    try:
        import v2_windows as _W
    except Exception as e_:                                          # noqa: BLE001
        REPORT["notes"].append("확대 창 자료 없음: %s" % e_)
        return
    mods = []
    for t_ in "ABCD":
        try:
            mods.append(importlib.import_module("zoom_figs_" + t_))
        except Exception as e_:                                      # noqa: BLE001
            REPORT["notes"].append("확대 창 그림 모듈 %s 못 읽음: %s" % (t_, e_))
    DRAWN["detail_windows"] = []
    for w in _W.DETAIL_WINDOWS:
        if w.get("reserved"):
            DRAWN["detail_windows"].append({"key": w["key"], "rank": w["rank"], "c": list(w["c"]), "d": w["d"], "reserved": True})
            continue
        fn = next((getattr(m, "fig_" + w["fig"]) for m in mods if hasattr(m, "fig_" + w["fig"])), None)
        (cx, cy), d = w["c"], w["d"]
        r = d / 2.0
        if fn is None:
            REPORT["notes"].append("확대 창 그림 함수 없음: fig_%s" % w["fig"])
            continue
        vc, vr = 31.0, 30.0
        sub = Layer(0, 0, 62, 62)
        fn(sub, vc, vr, _rnd.Random(w["key"]))
        plate = w.get("shape") == "plate"
        hw, hh = _win_half(w)
        if not plate:
            mask = Image.new("L", (sub.w, sub.h), 0)
            ImageDraw.Draw(mask).ellipse([sub.X(vc - vr), sub.Y(vc - vr), sub.X(vc + vr), sub.Y(vc + vr)], fill=255)
            sub.img.putalpha(ImageChops.multiply(sub.img.getchannel("A"), mask))
        k = d / 60.0
        tgt = Layer(cx - r - k, cy - r - k, cx + r + k, cy + r + k)
        tgt.img = sub.img.resize((tgt.w, tgt.h), Image.LANCZOS)
        tgt.d = ImageDraw.Draw(tgt.img)
        P.paste(tgt)
        if plate:                                                    # 도면 판: 직사각형 주황 테(다른 확대 창과 같은 색·두께)
            P.rect(cx - hw, cy - hh, cx + hw, cy + hh, outline=_W.ORANGE, lw=0.9)
        else:
            P.ell(cx, cy, r, r, outline=_W.ORANGE, lw=0.9)
        tx, ty = w["t"]
        dist = math.hypot(tx - cx, ty - cy)
        pth = w.get("path")
        if pth and len(pth) >= 2 and dist > r + 1.5:
            # 꺾은선이 원(판이면 직사각형) 가장자리를 벗어나는 첫 점에서 시작한다(안쪽은 자른다)
            def _ins(p_):
                return (abs(p_[0] - cx) <= hw and abs(p_[1] - cy) <= hh) if plate else math.hypot(p_[0] - cx, p_[1] - cy) <= r
            pl = None
            for q0, q1 in zip(pth[:-1], pth[1:]):
                if _ins(q1):
                    continue
                if not _ins(q0):
                    ex = tuple(q0)
                else:
                    lo, hi = 0.0, 1.0
                    for _ in range(30):
                        mm = (lo + hi) / 2.0
                        pm = (q0[0] + (q1[0] - q0[0]) * mm, q0[1] + (q1[1] - q0[1]) * mm)
                        if _ins(pm):
                            lo = mm
                        else:
                            hi = mm
                    ex = (q0[0] + (q1[0] - q0[0]) * hi, q0[1] + (q1[1] - q0[1]) * hi)
                rest = [tuple(q) for q in pth[pth.index(q1):]] if q1 in pth else [tuple(q1)]
                pl = [ex] + rest
                break
            if pl is None:
                pl = [(cx, cy), (tx, ty)]
            P.line(pl, _W.ORANGE, 0.35, joint=False)
            P.dot(tx, ty, 0.5, _W.ORANGE)
            w["leader_pts"] = [[round(q[0], 2), round(q[1], 2)] for q in pl]
        side = w.get("side", "below")
        chip = w.get("chip")
        tf = _win_tf(w)
        st_ = 3.9 * tf
        if side == "below":
            tx0, anc, y0 = cx, "c", cy + hh + 4.2 * tf
        elif side == "right":
            tx0, anc, y0 = cx + hw + 3.0, "l", cy - 5.5 * tf
        elif side == "above":
            tx0, anc, y0 = cx, "c", cy - hh - 14.8 * tf
        else:
            tx0, anc, y0 = cx - hw - 3.0, "r", cy - 5.5 * tf
        ptext(tx0, y0, w["title"], "b", 3.0 * tf, INK_L, "caption", anchor=anc, layer="확대 창 " + w["key"], panel="MAP")
        for i_, ln in enumerate(w["lines"][:2]):
            ptext(tx0, y0 + st_ * (i_ + 1), ln, "m", 2.5 * tf, INK_L, "caption", anchor=anc, layer="확대 창 " + w["key"], panel="MAP")
        if chip:
            yc = y0 + st_ * 3 + 1.0
            wch = max(14.0, 2.35 * tf * len(chip) * 0.62 + 4.0)
            xa = tx0 - wch / 2.0 if anc == "c" else (tx0 if anc == "l" else tx0 - wch)
            P.rect(xa, yc - 3.2 * tf, xa + wch, yc + 1.0, fill=(250, 238, 214), outline=_W.ORANGE, lw=0.25)
            ptext(xa + wch / 2.0, yc, chip, "m", 2.3 * tf, INK_L, "caption", anchor="c", layer="확대 창 " + w["key"], panel="MAP")
        DRAWN["detail_windows"].append({"key": w["key"], "rank": w["rank"], "c": [cx, cy], "d": d, "target": [tx, ty],
                                        "leader_mm": round(max(0.0, dist - r), 1), "leader_pts": w.get("leader_pts"), "title": w["title"], "lines": w["lines"][:2], "chip": chip})


def draw_map_head():
    """❸ 지도 장 머리(20:53 삭제)"""
    mh = {}
    if not mh:
        return
    c = mh["badge_c"]
    chapter_badge(mh["n"], c[0], c[1], mh.get("badge_d", 10.0), layer="지도 ❸")
    w = twf(mh["title"], "b", mh.get("title_face", 3.8))
    anc = mh.get("title_anchor", "l")
    ptext(mh["title_x"], mh["title_baseline_y"], mh["title"], "b", mh.get("title_face", 3.8), ACCENT, "head_ko", anchor=anc, layer="지도 ❸", panel="MAP")
    x0t = mh["title_x"] - (w if anc == "r" else 0.0)
    DRAWN["map_head"] = {"badge_c": list(c), "title": mh["title"], "box": [round(min(c[0] - 5, x0t), 2), round(c[1] - 5, 2), round(max(c[0] + 5, x0t + w), 2), round(mh["title_baseline_y"] + 1.0, 2)]}


def draw_panel_L():
    # panels-v2: ❶ 로마 콘크리트란? = Basic 1순위(제목 8.4 · 정의 3.0 · 재료 그림 ×1.7 · 이름 3.2 · 설명 2.4). 칸·글 자리는 사양 rect·head에서 읽는다
    pn = PANEL["L"]
    x0, y0, x1, y1 = pn["rect"]
    lay = "패널 L"
    hd = pn.get("head") or {}
    bd = (hd.get("badge") or {}).get("d")
    yb, kb = chapter_header("L", 1, "ROMAN CONCRETE?", hd.get("ko", "무엇으로 만들었나"), x0, x1, float(hd.get("en_baseline_y", y0 + 12.5)), en_x=hd.get("en_x"),
                            en_face=hd.get("en_face"), badge_d=bd)
    ydef = (kb + 6.2) if kb else (yb + 9.0)
    defs = ["생석회와 화산재가 물과 반응해 굳는 반죽에", "돌·벽돌 조각(골재)을 다져 넣은 로마 건축 재료.", "돔·볼트·방파제에 쓰였고 철근은 쓰지 않았다."]
    draw_lines(x0 + 0.6, ydef, wrap_all(defs, "m", 3.0, x1 - x0 - 1.2), "m", 3.0, INK_L, "body", 3.9, lay)
    items = [("생석회", ["석회암을 구운 것"]), ("화산재", ["시내 = 알바노 구릉", "바다 = 포추올리"]),
             ("골재", ["응회암·벽돌·", "경석 조각"]), ("물", ["육상 = 민물", "바다 공사 = 바닷물"])]
    isc = float(hd.get("icon_scale", 1.5))
    for i, (name, sub) in enumerate(items):
        cx = x0 + 14.0 + i * float(hd.get("icon_pitch", 27.0))
        iso = ZIso(P, cx, y0 + float(hd.get("icon_oy", 54.5)), sc=isc)
        m = Mesh(None)
        if i == 0:
            m.extend(m_mound(0, 0, 0, 4.6, 4.2, LIME_W, key="L석회"))
            m.extend(m_box(3.2, 2.0, 0, 5.2, 4.0, 1.6, (240, 238, 228), top=(250, 250, 244)))
            m.extend(m_box(-4.6, 1.0, 0, -2.8, 2.8, 1.4, (240, 238, 228), top=(250, 250, 244)))
        elif i == 1:
            m.extend(m_mound(-2.4, 0.5, 0, 3.6, 3.4, ASH_R, key="L화산재1"))
            m.extend(m_mound(3.2, -0.5, 0, 3.4, 3.0, ASH_G, key="L화산재2"))
        elif i == 2:
            for k, (X, Y, c) in enumerate(((-3, 0, (168, 136, 104)), (0, 2.5, (186, 104, 78)), (2.6, -1.6, (150, 146, 138)), (-0.5, -3, (204, 196, 170)), (3.6, 2.4, (176, 140, 108)))):
                m.extend(m_blob(X, Y, 1.0, 1.7, c, n=6, key="L골재%d" % k, jit=0.25, squash=0.7))
        else:
            m.extend(m_cyl(0, 0, 3.0, 0, 4.6, (150, 108, 70), n=12, top=(110, 172, 214)))
        m.draw(iso, lw=0.10)
        ptext(cx, y0 + 69.5, name, "b", 3.2, INK_L, "subtitle", anchor="c", layer=lay)
        draw_lines(cx, y0 + 73.1, sub, "m", 2.4, INK_L, "iconcaption", 3.0, lay, anchor="c")
    P.line([(x0 + 0.6, y0 + 79.4), (x1 - 2.2, y0 + 79.4)], (176, 156, 120), 0.25, joint=False)
    ptext(x0 + 0.6, y0 + 83.6, "섞는 순서가 열쇠 → 아래 만드는 과정", "b", 2.8, INK_L, "body", layer=lay)


def scene_tile(iso, s=15.0, top=(240, 230, 210)):
    T_, R_, B_, L_ = iso.p(0, 0), iso.p(s, 0), iso.p(s, s), iso.p(0, s)
    lay = [(0.5, (94, 126, 66)), (1.1, (140, 108, 72))]
    strata_side(P, L_, B_, lay, f=0.9)
    strata_side(P, B_, R_, lay, f=0.7)
    P.poly([T_, R_, B_, L_], fill=top, outline=(150, 128, 96), lw=0.2)


def draw_scene(k, iso):
    m = Mesh(None)
    hp = 5.2
    if k == 1:
        m.extend(m_mound(4.0, 5.0, 0, 3.0, 3.2, LIME_W, key="B1석회"))
        m.extend(m_mound(9.5, 3.8, 0, 3.0, 2.8, ASH_R, key="B1화산재"))
        m.extend(m_mound(4.4, 11.0, 0, 2.6, 2.4, AGG_G, key="B1골재"))
        m.extend(m_box(9.0, 9.5, 0.9, 13.6, 12.6, 2.4, WOOD, top=WOOD_L))
        m.extend(m_mound(11.3, 11.0, 2.4, 1.5, 1.1, LIME_W, key="B1짐"))
        m.extend(m_person(12.8, 6.8, 0, hp, CLOTHS[0], key="B1사람"))
    elif k == 2:
        m.extend(m_box(2.0, 3.5, 0, 12.5, 11.0, 0.6, WOOD, top=WOOD_L))
        m.extend(m_mound(7.0, 7.2, 0.6, 3.6, 2.6, (214, 190, 176), key="B2혼합"))
        m.extend(m_person(12.4, 12.6, 0, hp, CLOTHS[4], key="B2사람"))
    elif k == 3:
        m.extend(m_box(2.0, 3.5, 0, 12.5, 11.0, 0.6, WOOD, top=WOOD_L))
        m.extend(m_mound(7.0, 7.2, 0.6, 3.6, 2.4, (190, 172, 162), key="B3반죽"))
        m.extend(m_box(0.4, 12.4, 3.0, 8.0, 14.0, 3.8, WOOD, top=(110, 172, 212)))
        m.extend(m_box(0.6, 12.8, 0, 1.4, 13.6, 3.0, WOOD))
        m.extend(m_person(12.0, 11.5, 0, hp, CLOTHS[1], key="B3사람"))
    elif k == 4:
        m.extend(m_person(12.6, 12.4, 0, hp, CLOTHS[0], key="B4사람"))
    elif k == 5:
        for (a, b, c, d_, e, f) in ((3, 3, 0, 11.5, 3.5, 4.0), (3, 9.5, 0, 11.5, 10.0, 4.0), (3, 3.5, 0, 3.5, 9.5, 4.0), (11.0, 3.5, 0, 11.5, 9.5, 4.0)):
            m.extend(m_box(a, b, c, d_, e, f, WOOD, top=WOOD_L))
        m.extend(m_box(3.5, 3.5, 0, 11.0, 9.5, 3.0, (176, 168, 154), top=(190, 182, 168)))
        m.extend(m_person(7.0, 6.5, 3.0, hp, CLOTHS[4], key="B5사람"))
        m.extend(m_person(13.2, 12.5, 0, hp, CLOTHS[2], key="B5사람2"))
    elif k == 6:
        m.extend(m_box(2.5, 4.0, 0, 10.5, 11.5, 5.0, (176, 170, 158), top=(196, 190, 178)))
        m.extend(m_box(3.2, 5.0, 5.0, 4.7, 10.5, 9.2, TRAV, top=TRAV_L))
        m.extend(m_box(8.3, 5.0, 5.0, 9.8, 10.5, 9.2, TRAV, top=TRAV_L))
        m.extend(m_box(3.2, 5.0, 9.2, 9.8, 10.5, 11.4, TRAV, top=TRAV_L))
        m.extend(m_person(13.0, 12.0, 0, hp, CLOTHS[3], key="B6사람"))
    if k == 4:
        pit = [(2.5, 3.0, 0.03), (12.0, 3.0, 0.03), (12.0, 10.5, 0.03), (2.5, 10.5, 0.03)]
        iso.poly3(pit, fill=(176, 92, 54), ol=(120, 70, 40), lw=0.2)
        iso.poly3([(3.4, 3.8, 0.05), (11.1, 3.8, 0.05), (11.1, 9.7, 0.05), (3.4, 9.7, 0.05)], fill=(232, 136, 72))
        for (X, Y) in ((5.0, 5.5), (8.0, 6.5), (6.5, 8.5), (9.8, 8.6), (4.5, 8.0)):
            cx, cy = iso.p(X, Y, 0)
            P.ell(cx, cy, 0.6, 0.38, fill=(250, 246, 236))
    m.draw(iso, lw=0.10)
    if k == 1:
        for (a, b) in ((10.0, 12.6), (12.6, 9.5)):
            cx, cy = iso.p(a if a < 11 else 13.6, b, 1.0)
            P.ell(cx, cy, 0.9, 0.9, fill=(90, 66, 44))
    if k == 2:
        a = iso.p(11.8, 12.0, 4.0)
        b = iso.p(8.6, 8.8, 1.2)
        P.line([a, b], (110, 80, 50), 0.35, joint=False)
    if k == 3:
        bk = iso.p(10.0, 9.4, 4.6)
        P.poly([(bk[0] - 1.1, bk[1] - 0.6), (bk[0] + 1.1, bk[1] - 0.6), (bk[0] + 0.8, bk[1] + 1.4), (bk[0] - 0.8, bk[1] + 1.4)], fill=(150, 108, 70))
        tgt = iso.p(7.6, 7.6, 3.0)
        P.line([(bk[0] - 1.0, bk[1] + 0.2), (tgt[0] + 0.6, tgt[1] - 0.6)], (90, 152, 206), 0.45, joint=False)
        for i in range(3):
            P.ell(tgt[0] + 1.0 - i * 0.9, tgt[1] - 1.6 - i * 0.6, 0.35, 0.45, fill=(90, 152, 206))
        sp_ = iso.p(8.0, 13.2, 3.8)
        P.line([sp_, (sp_[0] + 0.4, sp_[1] + 3.0)], (90, 152, 206), 0.45, joint=False)
    if k == 4:
        for i, (X, Y) in enumerate(((6.0, 6.0), (9.0, 7.0), (5.0, 8.4))):
            cx, cy = iso.p(X, Y, 3.5 + 1.6 * i)
            soft_ell(P, cx, cy, 2.6, 1.6, (255, 255, 255), alpha=40, blur=0.6)
        a = iso.p(12.0, 12.0, 4.0)
        b = iso.p(8.0, 7.6, 0.4)
        P.line([a, b], (110, 80, 50), 0.35, joint=False)
    if k == 5:
        a = iso.p(7.6, 7.2, 3.0 + 4.6)
        b = iso.p(8.8, 8.6, 3.05)
        P.line([a, b], (110, 80, 50), 0.4, joint=False)
        for zc in (1.0, 2.0):
            P.line([iso.p(3.0, 10.02, zc), iso.p(11.5, 10.02, zc)], (130, 92, 58), 0.12, joint=False)
    if k == 6:
        rng = local_rng("B6단면")
        for i in range(14):
            u = 0.5 + rng.random() * 7.0
            v = 0.5 + rng.random() * 4.0
            cx, cy = iso.p(2.5 + u, 11.52, v)
            P.ell(cx, cy, 0.42, 0.34, fill=(150, 120, 92) if i % 3 else (255, 255, 250))
        for i in range(8):
            u = 0.5 + rng.random() * 6.6
            v = 0.5 + rng.random() * 4.0
            cx, cy = iso.p(10.52, 4.0 + u, v)
            P.ell(cx, cy, 0.38, 0.3, fill=(140, 112, 86) if i % 3 else (250, 250, 244))
        iso.arch("L", 0, 10.52, 5.0, 4.7, 8.3, 0.0, 2.6, (110, 84, 60))


def lime_sq(x, y, s, stage):
    """D 패널 작은 단면 그림(정면): stage 1 뜨거운 혼합, 2 균열, 3 빗물·칼슘, 4 결정 봉합"""
    P.rect(x, y, x + s, y + s, fill=MORTAR, outline=(130, 112, 92), lw=0.25)
    rng = local_rng("D단면%d" % stage)
    for i in range(10):
        ax_ = x + 1.2 + rng.random() * (s - 2.4)
        ay_ = y + 1.2 + rng.random() * (s - 2.4)
        rr = 0.8 + rng.random() * 1.1
        c = [(168, 136, 104), (186, 104, 78), (150, 146, 138)][i % 3]
        P.poly([(ax_ + rr * math.cos(t * 1.26), ay_ + rr * 0.85 * math.sin(t * 1.26)) for t in range(5)], fill=c)
    cx, cy = x + s * 0.5, y + s * 0.55
    clr = 2.6 if stage < 4 else 2.0
    P.ell(cx, cy, clr, clr * 0.85, fill=(253, 253, 248), outline=(196, 190, 178), lw=0.2)
    crack = [(x + s * 0.25, y + 0.3), (x + s * 0.4, y + s * 0.35), (cx - 0.3, cy), (x + s * 0.62, y + s * 0.7), (x + s * 0.72, y + s - 0.3)]
    if stage == 1:
        for k in range(3):
            xx = x + s * (0.3 + 0.2 * k)
            P.line([(xx, y + 2.6), (xx + 0.6, y + 1.6), (xx, y + 0.8)], (226, 110, 40), 0.3)
        P.ell(x + 2.0, y + 2.0, 0.7, 0.9, fill=(90, 150, 206))
    if stage >= 2:
        P.line(crack, (70, 56, 46), 0.5)
    if stage == 3:
        for (fx, fy) in ((0.3, 0.12), (0.45, 0.42), (0.58, 0.6)):
            P.ell(x + s * fx + 0.8, y + s * fy, 0.45, 0.6, fill=(80, 150, 206))
        soft_ell(P, cx, cy, clr + 0.8, clr * 0.85 + 0.8, (170, 220, 236), alpha=120, blur=0.3)
    if stage == 4:
        P.line(crack, (250, 250, 250), 0.9)
        for (px, py) in crack[1:4]:
            P.poly([(px - 0.5, py), (px, py - 0.6), (px + 0.5, py), (px, py + 0.6)], fill=(255, 255, 255), outline=(190, 190, 180), lw=0.10)


def draw_panel_B():
    # panels-v2: ❹ 만드는 과정 = Basic 2순위. 칸 폭 60·그림 ×1.0(❺·❻보다 한 단계 큼), 단계명 3.4·설명 2.8, 4단계 '뜨거운 혼합' 강조(그림 ×1.08 + 장 색 테 + 장 색 단계명)
    """❹ 만드는 과정: 6단계 등각 장면(3열 2행), 단계마다 이름 + 1줄(근거 수준 표기 1곳만 2줄), Ø4 테두리 단계 번호"""
    pn = PANEL["B"]
    x0, y0, x1, y1 = pn["rect"]
    lay = "패널 B"
    hd = pn["head"]
    chapter_header("B", 4, hd["en"], hd["ko"], x0, x1, float(hd["en_baseline_y"]), en_x=hd.get("en_x"), en_face=hd.get("en_face"), badge_d=(hd.get("badge") or {}).get("d"))
    g = pn["grid"]
    tile_sc = float(g.get("tile_scale", 1.0))
    emph_sc = float(g.get("emph_scale", 1.08))
    emph_n = int(g.get("emph_step", 4))
    nface, dface = float(g.get("name_face", 3.4)), float(g.get("desc_face", 2.8))
    cwid = float(g["cell_w"])
    for i, st in enumerate(pn["steps"][:6]):
        col, row = i % int(g["cols"]), i // int(g["cols"])
        cl = float(g["col_x0"]) + col * cwid
        cxm = cl + cwid / 2.0
        ry = float(g["row_y0"][row])
        emph = int(st["n"]) == emph_n
        if emph:                                                   # 4단계 강조: 장 색 테(0.5mm) + 옅은 바탕
            rrect(P, cl + 1.5, ry + 1.0, cl + cwid - 3.0, ry + 47.6, 1.8, fill=(252, 236, 228, 120), outline=ACCENT, lw=0.5)
        iso = ZIso(P, cxm, ry + 18.6, sc=emph_sc if emph else tile_sc)
        scene_tile(iso)
        draw_scene(i + 1, iso)
        # 20:35 사용자: 단계 번호 ①~⑥ 제거(순서는 화살표로 읽힌다)
        ptext(cxm, ry + 41.0, st["name"], "b", nface, ACCENT if emph else INK_L, "step", anchor="c", layer=lay)
        lines = wrap_all(st["lines"], "m", dface, cwid - 4.0)
        draw_lines(cxm, ry + 45.2, lines, "m", dface, INK_L, "body", 3.9, lay, anchor="c")
        if col < int(g["cols"]) - 1:
            ax_ = cl + cwid + 0.6
            ay_ = ry + 25.4
            P.poly([(ax_ - 1.6, ay_ - 0.8), (ax_ + 0.2, ay_ - 0.8), (ax_ + 0.2, ay_ - 1.7), (ax_ + 1.9, ay_), (ax_ + 0.2, ay_ + 1.7), (ax_ + 0.2, ay_ + 0.8), (ax_ - 1.6, ay_ + 0.8)],
                   fill=BROWN_A)
    DRAWN["panel_B"] = {"cols": int(g["cols"]), "rows": int(g["rows"]), "steps": len(pn["steps"]), "number_circle_d": 4.0}


def panel_header_at(x, y0, en, ko, en_face=7.4, ko_face=3.7, panel="", col=ACCENT, x_max=None, gap=2.0, baseline=None):
    """패널 머리글(영문 초압축 대문자 + 국문 윗선 정렬, 강조색 한 색). 국문이 x_max를 넘으면 바로 아랫줄 왼쪽 맞춤으로 내린다.
    돌려줌: (영문 기준선, 아랫줄로 내린 국문 기준선 또는 None)"""
    yb = baseline if baseline is not None else y0 + 2.4 + en_face
    box, fa = ptext(x, yb, en, "en", en_face, col, "head_en", layer="패널 " + panel, panel=panel)
    fk = fface("b", ko_face, ko)[2]
    kw = twf(ko, "b", ko_face)
    g_ = gap
    if x_max is not None and box[2] + g_ + kw > x_max:
        g_ = max(1.2, x_max - box[2] - kw)
    if x_max is not None and box[2] + g_ + kw > x_max + 0.01:
        kb = yb + 1.5 + fk * (0.812 / 0.870)
        ptext(x, kb, ko, "b", ko_face, col, "head_ko", layer="패널 " + panel, panel=panel)
        return yb, kb
    kb = (yb - fa) + fk * (0.812 / 0.870)
    ptext(box[2] + g_, kb, ko, "b", ko_face, col, "head_ko", layer="패널 " + panel, panel=panel)
    return yb, None


def draw_zoom():
    """❺ 확대 원 Ø30 '로마 콘크리트 단면': Ø60 원본 그림을 가상 판에 그린 뒤 0.5배로 줄여 붙인다(콜로세움 시료 직접 분석은 미확인이라 모식으로 밝힌다)"""
    z = DMAP["Z1"]
    (cx, cy), d = z["circle"]["c"], z["circle"]["d"]
    r = d / 2.0
    k = d / 60.0
    vc, vr = 31.0, 30.0
    sub = Layer(0, 0, 62, 62)
    sub.ell(vc, vc, vr, vr, fill=MORTAR)
    rng = local_rng("확대창")
    for i in range(220):
        x = vc + (rng.random() * 2 - 1) * vr
        y = vc + (rng.random() * 2 - 1) * vr
        sub.ell(x, y, 0.5, 0.4, fill=(188, 176, 160) if i % 2 else (220, 210, 196))
    agg_cols = [(168, 136, 104), (186, 104, 78), (150, 146, 138), (112, 94, 84), (196, 160, 118), (204, 196, 170)]
    for i in range(26):
        ax_ = vc + (rng.random() * 2 - 1) * vr * 0.95
        ay_ = vc + (rng.random() * 2 - 1) * vr * 0.95
        rr = 2.4 + rng.random() * 4.4
        nv = 5 + int(rng.random() * 3)
        pts = []
        for j in range(nv):
            t = 2 * math.pi * j / nv + rng.random() * 0.5
            q = rr * (0.7 + rng.random() * 0.45)
            pts.append((ax_ + q * math.cos(t), ay_ + q * 0.85 * math.sin(t)))
        c = agg_cols[i % 6]
        sub.poly(pts, fill=c, outline=shade(c, 0.75), lw=0.3)
        if i % 6 == 5:
            for kk in range(4):
                sub.ell(ax_ + (rng.random() - 0.5) * rr, ay_ + (rng.random() - 0.5) * rr * 0.8, 0.5, 0.45, fill=(170, 160, 136))
    clasts = [(-12, -10, 4.0), (9, -15, 3.0), (-4, 11, 4.6), (15, 7, 2.8), (-19, 12, 2.4), (2, -2, 2.2), (20, -6, 2.0), (6, 19, 2.6)]
    for (dx, dy, rr) in clasts:
        pts = [(vc + dx + rr * (0.86 + 0.14 * h01("알갱이", dx, j)) * math.cos(j * math.pi / 6), vc + dy + rr * 0.9 * math.sin(j * math.pi / 6)) for j in range(12)]
        sub.poly([(x + 0.7, y + 0.7) for x, y in pts], fill=(150, 140, 126))
        sub.poly(pts, fill=(253, 253, 248), outline=(198, 192, 180), lw=0.4)
        sub.ell(vc + dx - rr * 0.3, vc + dy - rr * 0.3, rr * 0.25, rr * 0.18, fill=(255, 255, 255))
    for i in range(14):
        sub.ell(vc + (rng.random() * 2 - 1) * vr * 0.85, vc + (rng.random() * 2 - 1) * vr * 0.85, 0.7, 0.6, fill=(120, 108, 96))
    mask = Image.new("L", (sub.w, sub.h), 0)
    ImageDraw.Draw(mask).ellipse([sub.X(vc - vr), sub.Y(vc - vr), sub.X(vc + vr), sub.Y(vc + vr)], fill=255)
    sub.img.putalpha(ImageChops.multiply(sub.img.getchannel("A"), mask))
    tgt = Layer(cx - r - k, cy - r - k, cx + r + k, cy + r + k)
    tgt.img = sub.img.resize((tgt.w, tgt.h), Image.LANCZOS)
    tgt.d = ImageDraw.Draw(tgt.img)
    P.paste(tgt)
    P.ell(cx, cy, r, r, outline=INK_L, lw=0.6)                       # Z1 테두리 0.6mm(정보 잉크)
    zz = PANEL["D"].get("zoom") or {}
    ptext(cx, float(zz.get("caption_baseline_y", cy + r + 5.6)), z.get("inner_caption") or "로마 콘크리트 단면", "m", 2.1, INK_L, "caption", anchor="c", layer="확대 원")
    INFO_POLYS.append(("확대 원", [(cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy + r)]))
    record("Z1", z["name"], "Detail", z["projected_box"], (cx - r, cy - r, cx + r, cy + r))
    DRAWN["boxes"].append({"id": "Z1 원", "kind": "확대 원", "tier": "Detail", "circle": {"c": [cx, cy], "d": d}, "border": True, "lw": 0.60,
                           "box": [cx - r, cy - r, cx + r, cy + r]})
    DRAWN["boxes"].append({"id": "Z1 합성", "kind": "composite(원 = 합성)", "tier": "Detail", "box": [cx - r, cy - r, cx + r, cy + r], "border": False})


def micro_cell(x, y, s, stage):
    """미시 도해 한 칸(정면). stage 1 = 젖은 벽에서 류사이트 결정이 녹아 나옴, 2 = 접합부 결정이 다시 짜임"""
    P.rect(x, y, x + s, y + s, fill=(214, 204, 188), outline=(120, 104, 84), lw=0.2)
    grains = [(0.26, 0.34, 0.2), (0.72, 0.30, 0.17), (0.30, 0.76, 0.18), (0.74, 0.74, 0.19)]
    for (gx, gy, gr) in grains:
        cxg, cyg = x + gx * s, y + gy * s
        P.poly([(cxg + gr * s * math.cos(t * 1.05), cyg + gr * s * 0.86 * math.sin(t * 1.05)) for t in range(6)], fill=(150, 132, 112), outline=(110, 94, 78), lw=0.1)
    jx, jy = x + 0.5 * s, y + 0.52 * s
    if stage == 1:
        for k in range(4):
            P.ell(x + s * (0.2 + 0.2 * k), y + 1.2, 0.36, 0.48, fill=(80, 150, 206))
        P.poly([(jx - 1.4, jy), (jx - 0.7, jy - 1.2), (jx + 0.7, jy - 1.2), (jx + 1.4, jy), (jx + 0.7, jy + 1.2), (jx - 0.7, jy + 1.2)],
               fill=(246, 244, 236), outline=(160, 156, 146), lw=0.1)
        for k in range(7):
            a = k * 0.9
            P.ell(jx + 2.4 * math.cos(a), jy + 2.0 * math.sin(a), 0.22, 0.22, fill=(236, 234, 226))
    else:
        for k in range(9):
            a = k * math.pi / 9
            P.line([(jx - 2.6 * math.cos(a), jy - 2.2 * math.sin(a)), (jx + 2.6 * math.cos(a), jy + 2.2 * math.sin(a))], (250, 250, 246), 0.22, joint=False)
        P.poly([(jx - 0.8, jy + 2.9), (jx + 0.8, jy + 2.9), (jx, jy + 1.9)], fill=INK_L)


def fig_seawater(x0, y0, x1, h, lay):
    """근거 카드 '바닷물 · 포르투스' 그림: 방파제 단면 + 바닷물 + 새로 자란 광물 결정"""
    P.rect(x0, y0 + h * 0.3, x1, y0 + h, fill=(150, 186, 210))
    for k in range(5):
        xx = x0 + 3 + k * 10.6
        if xx + 2.4 < x1:
            P.arc(xx, y0 + h * 0.32, 2.4, 0.8, 180, 360, (236, 246, 252), 0.3)
    P.poly([(x0 + 10, y0 + h), (x0 + 13.5, y0 + 0.6), (x1 - 17, y0 + 0.6), (x1 - 13.5, y0 + h)], fill=CONC2, outline=(96, 90, 80), lw=0.2)
    rng = local_rng("카드결정")
    for i in range(16):
        x = x0 + 14 + rng.random() * (x1 - x0 - 33)
        y = y0 + 1.8 + rng.random() * (h - 3.0)
        if i % 2:
            P.poly([(x - 0.9, y), (x - 0.45, y - 0.7), (x + 0.45, y - 0.7), (x + 0.9, y), (x + 0.45, y + 0.7), (x - 0.45, y + 0.7)], fill=(250, 250, 246), outline=(170, 166, 156), lw=0.10)
        else:
            P.ell(x, y, 0.5, 0.5, fill=(236, 228, 210), outline=(170, 160, 140), lw=0.10)
    ptext(x1 - 0.8, y0 + h - 1.0, "바닷물", "b", 2.1, (40, 80, 110), "caption", anchor="r", layer=lay)


def fig_leucite(x0, y0, h, lay):
    """근거 카드 '빗물 · 메텔라 무덤' 그림: 드럼 단면 모식 + 미시 도해 2칸(류사이트 용출 → 접합부 재편)"""
    cs = 12.0
    R = 6.0
    dcx, dcy = x0 + R, y0 + cs / 2.0
    P.ell(dcx, dcy, R, R, fill=BRICK, outline=(110, 60, 44), lw=0.2)
    P.ell(dcx, dcy, R - 0.8, R - 0.8, fill=CONC2)
    for k in range(10):
        a = math.radians(k * 36 + 8)
        x, y = dcx + (R - 1.8) * math.cos(a), dcy + (R - 1.8) * math.sin(a)
        P.rect(x - 0.6, y - 0.45, x + 0.6, y + 0.45, fill=TUFF, outline=(120, 96, 70), lw=0.10)
    P.ell(dcx, dcy, R - 3.0, R - 3.0, fill=(196, 186, 168))
    x1c = dcx + R + 3.0
    micro_cell(x1c, y0, cs, 1)
    ax0 = x1c + cs + 1.0
    P.line([(ax0, y0 + cs / 2), (ax0 + 1.4, y0 + cs / 2)], INK_L, 0.3, joint=False)
    P.poly([(ax0 + 1.1, y0 + cs / 2 - 0.7), (ax0 + 2.0, y0 + cs / 2), (ax0 + 1.1, y0 + cs / 2 + 0.7)], fill=INK_L)
    x2c = ax0 + 3.0
    micro_cell(x2c, y0, cs, 2)
    ptext(x1c + cs / 2, y0 + cs + 3.0, "류사이트 용출", "m", 2.1, INK_L, "caption", anchor="c", layer=lay)
    ptext(x2c + cs / 2, y0 + cs + 3.0, "접합부 재편", "m", 2.1, INK_L, "caption", anchor="c", layer=lay)


def draw_panel_D():
    # panels-v2: ❺ 석회 알갱이 = 건물을 넘는 공통 원리만(자가치유 4단계 + 단면 원). 건물별 근거 카드(포르투스·메텔라)는 지도 Detail 창이 맡는다
    """❺ 석회 알갱이 왜 오래가나: [석회 알갱이 자가치유 4단계 + 화살표] [확대 원(단면)] + 출처 1줄"""
    pn = PANEL["D"]
    x0, y0, x1, y1 = pn["rect"]
    lay = "패널 D"
    hd = pn["head"]
    chapter_header("D", 5, hd["en"], hd["ko"], x0, x1, float(hd["en_baseline_y"]), en_x=hd.get("en_x"), en_face=hd.get("en_face"), badge_d=(hd.get("badge") or {}).get("d"))
    sl = pn["stage_layout"]
    s_ = float(sl["tile_s"])
    for i, st in enumerate(pn["stages"][:4]):
        ty = float(sl["y0"]) + i * float(sl["pitch"])
        lime_sq(float(sl["x"]), ty, s_, i + 1)
        ptext(float(sl["text_x"]), ty + float(sl["name_dy"]), st["name"], "b", 3.0, INK_L, "subtitle", layer=lay)
        ptext(float(sl["text_x"]), ty + float(sl["line_dy"]), st["line"], "m", 2.6, INK_L, "body", layer=lay)
        if i < 3:                                                    # 단계 사이 아래 화살표
            ax_ = float(sl["arrow_x"])
            P.line([(ax_, ty + s_ + 0.6), (ax_, ty + s_ + 3.4)], BROWN_A, 0.35, joint=False)
            P.poly([(ax_ - 0.9, ty + s_ + 2.8), (ax_ + 0.9, ty + s_ + 2.8), (ax_, ty + s_ + 4.4)], fill=BROWN_A)
    draw_zoom()
    src = pn["source"]
    ptext(float(src["x"]), float(src["baseline_y"]), src["print"], "m", 2.6, INK_L, "body", layer=lay)
    DRAWN["panel_D"] = {"stages": len(pn["stages"]), "cards": [], "zoom_d": float(DMAP["Z1"]["circle"]["d"])}


# ───────────────────────── P2 아치·볼트·돔 / P5 지금 배우는 중(d4, 상자·배경판 없음) ─────────────────────────
def m_prism_y(xz, y0, y1, col, front=None, edge="auto"):
    """X·Z 단면 다각형을 Y 방향으로 민 기둥(볼록 권장). front = +Y 끝면 색"""
    cx = sum(p_[0] for p_ in xz) / len(xz)
    cz = sum(p_[1] for p_ in xz) / len(xz)
    m = Mesh((cx, (y0 + y1) / 2.0, cz))
    m.add([(x, y1, z) for x, z in xz], front or col, edge=edge)
    m.add([(x, y0, z) for x, z in xz], col, edge=edge)
    n = len(xz)
    for i in range(n):
        a, b = xz[i], xz[(i + 1) % n]
        m.add([(a[0], y0, a[1]), (b[0], y0, b[1]), (b[0], y1, b[1]), (a[0], y1, a[1])], col, edge=edge)
    return m


def _ring_wedges(cx, cz, ri, ro, n, y0, y1, cols, front=None, edge="auto", a0=0.0, a1=180.0):
    m = Mesh(None)
    for i in range(n):
        t0 = math.radians(a0 + (a1 - a0) * i / n)
        t1 = math.radians(a0 + (a1 - a0) * (i + 1) / n)
        q = [(cx + ri * math.cos(t0), cz + ri * math.sin(t0)), (cx + ro * math.cos(t0), cz + ro * math.sin(t0)),
             (cx + ro * math.cos(t1), cz + ro * math.sin(t1)), (cx + ri * math.cos(t1), cz + ri * math.sin(t1))]
        c = cols[i % len(cols)]
        m.extend(m_prism_y(q, y0, y1, c, front=(front[i % len(front)] if front else None), edge=edge))
    return m


def p2_icon(kind, box, cell_x1=None):
    """P2 칸 등각 소형 단면(정보 잉크 선 0.2): 아치 = 돌·벽돌색, 볼트·돔 = 콘크리트 회색.
    d5(결정 D16): ② 점선 교차 볼트 0, ③ 오른쪽 뒤 0.25mm 점선 교차 볼트 한 칸, ④ 반구 절개 돔(p2_dome_icon)"""
    extra_bb = None
    stone, brick_ = (214, 190, 146), (192, 112, 82)
    conc, conc_s = (172, 166, 154), (150, 144, 132)
    m = Mesh(None)
    extra = []
    if kind == "arch":                                              # 비교 기준: 돌·벽돌 쐐기 아치(콘크리트 없이도 선다)
        m.extend(m_prism_y([(0.0, 0.0), (2.6, 0.0), (2.6, 6.0), (0.0, 6.0)], -4.0, 0.0, stone, edge=INK_L))
        m.extend(m_prism_y([(11.4, 0.0), (14.0, 0.0), (14.0, 6.0), (11.4, 6.0)], -4.0, 0.0, stone, edge=INK_L))
        m.extend(_ring_wedges(7.0, 6.0, 4.4, 7.0, 9, -4.0, 0.0, [stone, brick_], edge=INK_L))
        pts = mesh_pts(m)
    elif kind == "barrel":                                          # 배럴 볼트: 터널 모양 콘크리트 껍질(앞 끝 단면)
        m.extend(m_prism_y([(0.6, 0.0), (2.2, 0.0), (2.2, 4.2), (0.6, 4.2)], -12.0, 0.0, conc, edge=INK_L))
        m.extend(m_prism_y([(11.8, 0.0), (13.4, 0.0), (13.4, 4.2), (11.8, 4.2)], -12.0, 0.0, conc, edge=INK_L))
        m.extend(_ring_wedges(7.0, 4.2, 4.8, 6.4, 8, -12.0, 0.0, [conc], front=[conc_s], edge=INK_L))
        pts = mesh_pts(m)
    elif kind == "cross":                                           # 교차 볼트: 두 배럴 볼트가 직각으로 만난다(그로인 = 대각선)
        c, ro, ri, zs = 7.0, 6.0, 4.6, 4.0

        def hf(X, Y):
            return zs + max(math.sqrt(max(0.0, ro * ro - (X - c) ** 2)), math.sqrt(max(0.0, ro * ro - (Y - c) ** 2)))
        m.extend(m_terrain(1.0, 1.0, 13.0, 13.0, 14, 14, hf, lambda X, Y, Z: conc))
        for (X0_, Y0_) in ((11.4, 11.4), (11.4, 1.0), (1.0, 11.4)):
            m.extend(m_box(X0_, Y0_, 0.0, X0_ + 1.6, Y0_ + 1.6, zs, conc_s))
        pts = mesh_pts(m)
        extra.append(("cross", c, ro, ri, zs))
    else:                                                           # 돔(결정 D16): 반구 절개 2D 등각 도식(메시 아님)
        return p2_dome_icon(box)
    ox, oy, sc, zs_, bb = fit_frame(pts, box, ax="c", ay="b", sc_max=1.35)
    if kind == "cross" and cell_x1 is not None:                     # ③: 오른쪽 뒤 점선 칸이 칸 안에 들게 그림 전체를 왼쪽으로(실선 칸은 그림 자리 안)
        dbb0 = p2_cross_dashed(ZIso(P, ox, oy, sc, 1.0), draw=False)
        shift = max(box[0] - bb[0], min(0.0, cell_x1 - 0.4 - dbb0[2]))
        ox += shift
        bb = (bb[0] + shift, bb[1], bb[2] + shift, bb[3])
    fr = ZIso(P, ox, oy, sc, 1.0)
    if kind == "cross" and cell_x1 is not None:                     # 점선 칸(뒤)을 먼저, 실선 칸을 그 위에
        extra_bb = p2_cross_dashed(fr, draw=True)
    m.draw(fr, lw=0.2 if kind in ("arch", "barrel") else 0.10)
    for e in extra:
        _k, c, ro, ri, zs = e
        n_ = 24
        for (pa, pb) in (((1.0, 1.0), (13.0, 13.0)), ((13.0, 1.0), (1.0, 13.0))):   # 그로인 선
            q = []
            for i in range(n_ + 1):
                X = pa[0] + (pb[0] - pa[0]) * i / n_
                Y = pa[1] + (pb[1] - pa[1]) * i / n_
                q.append(fr.p(X, Y, zs + math.sqrt(max(0.0, ro * ro - (X - c) ** 2)) + 0.05))
            P.line(q, INK_L, 0.2)
        for side in ("Y", "X"):                                       # 보이는 두 끝 단면(반 고리)
            ring_o = [(c + ro * math.cos(math.radians(t)), zs + ro * math.sin(math.radians(t))) for t in range(0, 181, 10)]
            ring_i = [(c + ri * math.cos(math.radians(t)), zs + ri * math.sin(math.radians(t))) for t in range(180, -1, -10)]
            if side == "Y":
                poly = [fr.p(u, 13.0, z) for u, z in ring_o + ring_i]
                hole = [fr.p(u, 13.0, z) for u, z in [(c - ri, 0.0), (c + ri, 0.0)] + [(c + ri * math.cos(math.radians(t)), zs + ri * math.sin(math.radians(t))) for t in range(0, 181, 10)]]
            else:
                poly = [fr.p(13.0, u, z) for u, z in ring_o + ring_i]
                hole = [fr.p(13.0, u, z) for u, z in [(c - ri, 0.0), (c + ri, 0.0)] + [(c + ri * math.cos(math.radians(t)), zs + ri * math.sin(math.radians(t))) for t in range(0, 181, 10)]]
            P.poly(hole, fill=(96, 90, 82))
            P.poly(poly, fill=conc_s, outline=INK_L, lw=0.2)
    if extra_bb:
        DRAWN.setdefault("p2", {})["cross_dashed_box"] = [round(v, 2) for v in extra_bb]
    return bb


def _p2_print(pn):
    """통합 d4: panels 사양 P2(head·cells·span_bars.rows·footnote)를 렌더 인쇄 열쇠로 옮긴다. 사양 'print'가 있으면 그것이 우선"""
    pr = dict(pn.get("print") or {})
    hd = pn.get("head") or {}
    if hd.get("en") and not pr.get("head_en"):
        pr["head_en"] = hd["en"]
    if hd.get("ko") and not pr.get("head_ko"):
        pr["head_ko"] = hd["ko"]
    kmap = {"arch": "arch", "barrel_vault": "barrel", "barrel": "barrel", "groin_vault": "cross", "cross_vault": "cross", "cross": "cross", "dome": "dome"}
    if not pr.get("cells") and isinstance(pn.get("cells"), list) and pn["cells"]:
        pr["cells"] = [{"kind": kmap.get(str(c.get("key")), "arch"), "name": c.get("name", ""), "caption": list(c.get("caption") or []),
                        "figure_box": c.get("figure_box"), "box": c.get("box")} for c in pn["cells"]]
    sb = pn.get("span_bars")
    if not pr.get("span_bars") and isinstance(sb, dict) and sb.get("rows"):
        pr["span_bars"] = [{"text": r_["print"], "m": float(r_["span_m"]), "bar": r_.get("bar")} for r_ in sb["rows"]]
    fn = pn.get("footnote")
    if not pr.get("footnote") and isinstance(fn, dict) and fn.get("print"):
        pr["footnote"] = fn["print"]
    return pr


def _p5_print(pn):
    """통합 d4: panels 사양 P5(head·stairs·cells·carbon)를 렌더 인쇄 열쇠로 옮긴다. 사양 'print'가 있으면 그것이 우선"""
    pr = dict(pn.get("print") or {})
    hd = pn.get("head") or {}
    if hd.get("en") and not pr.get("head_en"):
        pr["head_en"] = hd["en"]
    if hd.get("ko") and not pr.get("head_ko"):
        pr["head_ko"] = hd["ko"]
    if not pr.get("steps") and isinstance(pn.get("stairs"), list) and pn["stairs"]:
        pr["steps"] = [{"name": s_.get("title") or s_.get("key"), "text": list(s_.get("body") or [])} for s_ in pn["stairs"]]
    if not pr.get("cells") and isinstance(pn.get("cells"), list) and pn["cells"]:
        pr["cells"] = [{"title": c_.get("title") or c_.get("key"), "items": list(c_.get("body") or []), "icon": c_.get("icon")} for c_ in pn["cells"]]
    cb = pn.get("carbon")
    if not pr.get("carbon") and isinstance(cb, dict) and cb.get("print"):
        pr["carbon"] = cb["print"]
    return pr


def draw_panel_P2():
    """P2 '아치·볼트·돔 아치·볼트·돔'(옛 위치도 자리, 상자·배경판 없음): 머리글 y 21~29, 등각 단면 4칸(23×30, y 32~62),
    스팬 막대 3줄(y 66~86, 43.3 m = 60.0mm 비례), 각주 2.1 한 줄(y 88~91). 짝 표지 1~4는 MARKS가 그린다."""
    pn = PANEL.get("P2")
    if not pn:
        return
    x0, y0, x1, y1 = pn["rect"]
    lay = "패널 P2"
    pr = _p2_print(pn)
    ct = pn.get("cell_text") or {}
    nb_y, cb_y = ct.get("name_baseline_y"), ct.get("caption_baselines_y")
    hb_ = (pn.get("head") or {}).get("en_baseline_y")
    hd_ = pn.get("head") or {}
    chapter_header("P2", 2, pr.get("head_en") or "ARCH · VAULT · DOME", pr.get("head_ko") or "어떤 모양을 지었나", x0, x1,
                   float(hb_) if hb_ is not None else y0 + 8.0, en_x=hd_.get("en_x"))
    cells = pr.get("cells") or [
        {"kind": "arch", "name": "아치", "caption": ["비교 기준: 돌·벽돌", "쐐기가 서로 밀어 받침"]},
        {"kind": "barrel", "name": "배럴 볼트", "caption": ["점선 = 무너진", "신랑 볼트 복원"]},
        {"kind": "cross", "name": "교차 볼트", "caption": ["두 터널 지붕이", "직각으로 만난다"]},
        {"kind": "dome", "name": "돔", "caption": ["아치를 한 바퀴", "돌린 둥근 지붕"]}]
    cw = 23.0
    gapw = ((x1 - x0) - 4 * cw) / 3.0
    cy0 = y0 + 12.0
    rec = []
    for i, c in enumerate(cells[:4]):
        cx0 = x0 + i * (cw + gapw)
        cx1 = cx0 + cw
        if c.get("box"):                                              # 사용자 15:41: 칸 폭 21.5·21.5·21.5·31.7(돔 칸 설명 2줄이 들어가게)
            cx0, cx1 = float(c["box"][0]), float(c["box"][2])
        fb = c.get("figure_box")
        caps = wrap_all(c.get("caption") or [], "m", 2.1, cx1 - cx0 + 0.01)[:2]
        if nb_y is not None and cb_y and fb:                          # 통합 d4: panels 칸 배치(그림 figure_box → 이름 기준선 → 캡션 2줄, 칸 왼쪽 맞춤)
            ptext(cx0, float(nb_y), c["name"], "b", 2.6, INK_L, "body", layer=lay)
            bb = p2_icon(c.get("kind", ["arch", "barrel", "cross", "dome"][i]),
                         (float(fb[0]) + 0.6, max(float(fb[1]), y0 + 13.5 + MARK_R + 1.0), float(fb[2]) - 0.6, float(fb[3])), cell_x1=cx1)
            draw_lines(cx0, float(cb_y[0]), caps, "m", 2.1, INK_L, "caption", float(ct.get("caption_pitch", 3.0)), lay)
        else:
            ptext(cx0 + 6.6, cy0 + 2.9, c["name"], "b", 2.6, INK_L, "body", layer=lay)
            bb = p2_icon(c.get("kind", ["arch", "barrel", "cross", "dome"][i]), (cx0 + 0.6, cy0 + 5.2, cx1 - 0.6, cy0 + 21.6))
            draw_lines(cx0, cy0 + 24.6, caps, "m", 2.1, INK_L, "caption", 3.0, lay)
        rec.append({"cell": i + 1, "x": [round(cx0, 2), round(cx1, 2)], "y": [cy0, cy0 + 30.0], "kind": c.get("kind"), "icon_box": [round(v, 2) for v in bb]})
    bars = pr.get("span_bars") or [{"text": "메텔라 무덤 드럼 지름 29 m", "m": 29.0}, {"text": "하드리아누스 영묘 원통 지름 64 m", "m": 64.0}]
    ref_m = max(float(b_["m"]) for b_ in bars)
    ref_len = float(pr.get("span_ref_mm", 60.0))
    p2b = []
    for i, b_ in enumerate(bars):
        yc = ((float(b_["bar"][1]) + float(b_["bar"][3])) / 2.0) if b_.get("bar") else (y0 + 49.25 + 6.5 * i)   # 사양 막대 자리(통합 d4)
        Lb = ref_len * float(b_["m"]) / ref_m
        P.rect(x0, yc - 1.25, x0 + Lb, yc + 1.25, fill=(170, 164, 152), outline=(120, 114, 104), lw=0.15)
        for xt in (x0, x0 + Lb):                                      # 경간 끝 눈
            P.line([(xt, yc - 1.9), (xt, yc + 1.9)], INK_L, 0.2, joint=False)
        ptext(x0 + Lb + 2.0, yc + 1.3, b_["text"], "m", 2.6, INK_L, "body", layer=lay)
        p2b.append({"text": b_["text"], "m": b_["m"], "x0": x0, "x1": round(x0 + Lb, 2), "len_mm": round(Lb, 2), "y": [round(yc - 1.25, 2), round(yc + 1.25, 2)]})
    fn_y = (pn.get("footnote") or {}).get("baseline_y") if isinstance(pn.get("footnote"), dict) else None
    ptext(x0, float(fn_y) if fn_y else y0 + 70.5, pr.get("footnote") or "나무 틀(거푸집)에 반죽과 골재를 다져 넣어 곡면 지붕을 만들었다", "m", 2.1, INK_L, "footnote", layer=lay)
    DRAWN.setdefault("p2", {}).update({"cells": rec, "span_bars": p2b, "scale": "%.1f m = %.1fmm" % (ref_m, ref_len),
                                       "head_en_baseline_y": float(hb_) if hb_ is not None else y0 + 9.0})


def p2_dome_icon(box):
    """④ 돔(결정 D16): 반구 절개 실루엣 폭 12.5 · 원통 1.5 + 반구 솟음 6.25 · 껍질 단면 띠 0.8 → 꼭대기 0.5 · 오큘러스 틈 Ø1.4 · 절개 윤곽 0.2.
    등각 정사영(1.2247배)에서 앞 반쪽을 수직면으로 걷어 낸 뒤 반쪽: 바깥 등(뒤 반쪽 위) → 안쪽 면·바닥 → 절개 단면 띠 → 오큘러스 → 윤곽.
    원통 윗면은 그리지 않아 반구 안을 가리지 않는다. 돌려줌: 그린 외곽"""
    W2, hd, tb, tt, oc = 6.25, 1.5, 0.8, 0.5, 0.7
    R = W2 / KU                                                       # 평면 반지름 5.10 → 절개면 반원은 화면 6.25 × 5.10
    cx = (box[0] + box[2]) / 2.0
    cy = box[3] - hd                                                  # 스프링 라인(반구 기단) 중심
    conc, conc_s, inner, floor_c, deep = (176, 170, 158), (150, 144, 132), (208, 202, 190), (186, 180, 168), (92, 84, 74)

    def arc(a, b, a0, a1, n=36, oy=0.0):
        return [(cx + a * math.cos(math.radians(t)), cy + oy - b * math.sin(math.radians(t))) for t in [a0 + (a1 - a0) * k / n for k in range(n + 1)]]
    ai, bi = W2 - tb, R - tt
    outer_c = arc(W2, W2, 180, 0)                                      # 구 실루엣(뒤 반쪽 바깥 등의 윗선)
    outer_s = arc(W2, R, 0, 180)                                       # 절개면 바깥 반원(오른쪽 → 왼쪽)
    P.poly(outer_c + outer_s[1:-1], fill=conc)                         # 1 바깥 등(초승달)
    P.line(arc(W2 - 0.18, W2 - 0.18, 160, 20, 24), _hi(conc, 1.12), 0.25)            # L5 윗선 밝은 띠
    P.poly(arc(W2, R, 180, 0) + [(cx + W2 - tb, cy + hd), (cx - W2 + tb, cy + hd)], fill=inner)   # 2 안쪽 면(절개 반원 안 + 원통 안)
    P.poly(arc(ai, ai * KV / KU, 180, 0, 36, hd), fill=floor_c)        # 바닥(뒤 반쪽)
    for f_ in (0.84, 0.66, 0.48):                                      # 코퍼 격자(L3): 위도 줄 3 + 경도 눈 7
        P.line(arc(ai * f_ + 0.2, bi * f_ + 0.2, 168, 12, 20), (170, 162, 148), 0.12)
    for t_ in (30, 52, 74, 90, 106, 128, 150):
        a_ = math.radians(t_)
        P.line([(cx + (ai * 0.84 + 0.2) * math.cos(a_), cy - (bi * 0.84 + 0.2) * math.sin(a_)), (cx + (ai * 0.48 + 0.2) * math.cos(a_), cy - (bi * 0.48 + 0.2) * math.sin(a_))],
               (170, 162, 148), 0.12, joint=False)
    P.line(arc(ai, ai * KV / KU, 180, 0, 36), (172, 164, 150), 0.12)  # 스프링 라인(안쪽 원통 윗선)
    yo = cy - R * math.sqrt(max(0.0, 1 - (oc / W2) ** 2))
    yi = cy - bi * math.sqrt(max(0.0, 1 - (oc / ai) ** 2))
    for sgn in (-1, 1):                                                # 3 절개 단면 띠(옆 0.8 → 꼭대기 0.5) + 원통 단면, 오큘러스 틈 |x| < 0.7
        ta = math.degrees(math.acos(oc / W2))
        tia = math.degrees(math.acos(oc / ai))
        if sgn < 0:
            o_ = arc(W2, R, 180, 180 - ta, 24)
            i_ = arc(ai, bi, 180 - tia, 180, 24)
            band = o_ + i_ + [(cx - ai, cy + hd), (cx - W2, cy + hd)]
        else:
            o_ = arc(W2, R, ta, 0, 24)
            i_ = arc(ai, bi, 0, tia, 24)
            band = o_ + [(cx + W2, cy + hd), (cx + ai, cy + hd)] + i_
        P.poly(band, fill=conc_s, outline=INK_L, lw=0.2)
        rng = local_rng("P2돔단면%d" % sgn)
        for k in range(10):                                            # 골재 결(단면 띠 가운데 줄)
            t_ = math.radians(8 + 72 * rng.random())
            t_ = math.pi - t_ if sgn < 0 else t_
            f_ = 0.5
            x_ = cx + (W2 - tb * f_) * math.cos(t_)
            y_ = cy - (R - tt * f_) * math.sin(t_)
            P.ell(x_, y_, 0.16, 0.13, fill=(120, 114, 104) if k % 3 else (214, 208, 196))
    P.poly([(cx - oc, yi), (cx + oc, yi)] + [(cx + oc * math.cos(math.radians(t)), cy - R - (oc * KV / KU) * math.sin(math.radians(t))) for t in range(0, 181, 15)],
           fill=deep)                                                  # 4 오큘러스: 단면 띠 틈(폭 1.4) + 꼭대기 테의 뒤 반쪽(짙은 틈)
    P.line(outer_c, INK_L, 0.2)                                        # 5 윤곽 0.2(실루엣 + 바닥 절개선)
    P.line([(cx - W2, cy), (cx - W2, cy + hd), (cx + W2, cy + hd), (cx + W2, cy)], INK_L, 0.2, joint=False)
    DRAWN.setdefault("p2", {})["dome"] = {"silhouette_w": round(2 * W2, 2), "rise": W2, "drum_h": hd, "band_side": tb, "band_top": tt,
                                         "oculus_w": 2 * oc, "outline_lw": 0.2, "springing_y": round(cy, 2), "top_y": round(cy - W2, 2),
                                         "base_y": round(cy + hd, 2), "oculus_band_gap_y": [round(yi, 2), round(yo, 2)]}
    return (cx - W2, cy - W2, cx + W2, cy + hd)


def p2_cross_dashed(fr, draw=True):
    """③ 오른쪽 뒤(−Y)에 0.25mm 점선 교차 볼트 한 칸(무너진 신랑 교차 볼트 복원 문법, 결정 D16). 돌려줌: 점선 외곽"""
    c, ro, zs = 7.0, 6.0, 4.0
    ys0, ys1 = -11.0, 1.0
    yc = (ys0 + ys1) / 2.0
    lines = []
    lines.append([fr.p(c + ro * math.cos(math.radians(t)), ys0, zs + ro * math.sin(math.radians(t))) for t in range(0, 181, 10)])    # 먼 끝 아치
    lines.append([fr.p(13.0, yc + ro * math.cos(math.radians(t)), zs + ro * math.sin(math.radians(t))) for t in range(0, 181, 10)])  # 오른쪽 옆 아치
    for (pa, pb) in (((1.0, ys0), (13.0, ys1)), ((13.0, ys0), (1.0, ys1))):                                                          # 그로인
        q = []
        for i in range(25):
            X = pa[0] + (pb[0] - pa[0]) * i / 24.0
            Y = pa[1] + (pb[1] - pa[1]) * i / 24.0
            q.append(fr.p(X, Y, zs + max(math.sqrt(max(0.0, ro * ro - (X - c) ** 2)), math.sqrt(max(0.0, ro * ro - (Y - yc) ** 2)))))
        lines.append(q)
    for (X, Y) in ((13.0, ys0), (1.0, ys0)):
        lines.append([fr.p(X, Y, 0.0), fr.p(X, Y, zs)])
    lines.append([fr.p(1.0, ys0, zs), fr.p(13.0, ys0, zs), fr.p(13.0, ys1, zs)])                   # 스프링 선(먼 변·오른쪽 변)
    pts = [p for l_ in lines for p in l_]
    bb = bbox_of(pts)
    if draw:
        for l_ in lines:
            dotted(P, l_, INK_L, lw=0.25, dash=0.7, gap=0.55)
    return bb


def _fit_lines(lines, maxw, kind="m", face=2.6):
    """줄 폭이 maxw를 넘으면 낱말 경계에서만 다시 끊는다(줄 수·내용 유지). 돌려줌: (줄 목록, 다시 끊었는가)"""
    if all(twf(s, kind, face) <= maxw + 1e-6 for s in lines):
        return list(lines), False
    words = " ".join(lines).split(" ")
    n = len(lines)
    best = None

    def rec(i, k, acc):
        nonlocal best
        if k == n - 1:
            ln = " ".join(words[i:])
            if words[i:] and twf(ln, kind, face) <= maxw + 1e-6:
                cand = acc + [ln]
                w = max(twf(s, kind, face) for s in cand)
                if best is None or w < best[0]:
                    best = (w, cand)
            return
        for j in range(i + 1, len(words) - (n - 2 - k)):
            ln = " ".join(words[i:j])
            if twf(ln, kind, face) > maxw + 1e-6:
                break
            rec(j, k + 1, acc + [ln])
    if len(words) >= n:
        rec(0, 0, [])
    return (best[1], True) if best else (list(lines), False)


def _parse_divider(dv):
    if isinstance(dv, dict) and dv.get("x") is not None:
        y_ = dv.get("y") or [543.6, 558.4]
        return float(dv["x"]), float(y_[0]), float(y_[1])
    if isinstance(dv, str):
        m1 = re.search(r"x\s*([\d.]+)", dv)
        m2 = re.search(r"y\s*([\d.]+)\s*~\s*([\d.]+)", dv)
        if m1 and m2:
            return float(m1.group(1)), float(m2.group(1)), float(m2.group(2))
    return None


def draw_panel_P5():
    """❻ 지금 배우는 것 지금 배우는 것: 머리글 → 세로 타임라인(연구 → 현장 → 적용, 각 2줄) → ○ 가져올 것 · × 못 가져올 것(각 2개) → 100 VS 2,000(S) → 탄소 한 줄"""
    pn = PANEL["P5"]
    x0, y0, x1, y1 = pn["rect"]
    lay = "패널 P5"
    hd = pn["head"]
    chapter_header("P5", 6, hd["en"], hd["ko"], x0, x1, float(hd["en_baseline_y"]), en_x=hd.get("en_x"), ko_baseline=hd.get("ko_baseline_y"),
                   en_face=hd.get("en_face"), badge_d=(hd.get("badge") or {}).get("d"))
    stx = pn["stair_text"]
    tx = float(stx["text_x"])
    pitch = float(stx.get("pitch", 3.9))
    p5txt = []
    figs = []
    st_rec = []
    ys = [float(s_["title_baseline_y"]) for s_ in pn["stairs"][:3]]
    lx = float(stx["line_x"])
    dr = float(stx.get("dot_r", 0.8))
    P.line([(lx, ys[0] - 1.0), (lx, ys[-1] - 2.4)], BROWN_A, 0.35, joint=False)                  # 타임라인: 연구 → 현장 → 적용
    P.poly([(lx - 0.9, ys[-1] - 3.6), (lx + 0.9, ys[-1] - 3.6), (lx, ys[-1] - 1.9)], fill=BROWN_A)
    figs.append(("타임라인", [(lx, ys[0] - 1.0), (lx, ys[-1] - 1.9)]))
    for st, ty in zip(pn["stairs"][:3], ys):
        P.ell(lx, ty - 1.0, dr, dr, fill=BROWN_A)
        b_, _fa = ptext(tx, ty, st["title"], "b", 2.8, INK_L, "subtitle", layer=lay)
        p5txt.append(b_)
        lines, rebroke = _fit_lines(list(st["body"]), float(stx["max_w"]), "m", 2.6)
        for k, ln in enumerate(lines):
            b_, _fa = ptext(tx, ty + pitch * (k + 1), ln, "m", 2.6, INK_L, "body", layer=lay, pitch=pitch if len(lines) > 1 else None)
            p5txt.append(b_)
        st_rec.append({"step": st["title"], "lines": lines, "rebroken": rebroke, "max_line_w": round(max(twf(s, "m", 2.6) for s in lines), 2) if lines else 0.0})
    cells_sp = pn.get("cells") or []
    ct = pn.get("cell_text") or {}
    cpitch = float(ct.get("pitch", 3.9))
    for j, csp in enumerate(cells_sp[:2]):
        cb = csp["box"]
        tby = float(csp["title_baseline_y"])
        ic_x, ic_y = cb[0] + 1.2, tby - 1.3
        if j == 1:                                                              # × 못 가져올 것 · ○ 가져올 것(정보 잉크 2.4mm, 선 0.3)
            P.line([(ic_x - 1.0, ic_y - 1.0), (ic_x + 1.0, ic_y + 1.0)], INK_L, 0.3, joint=False)
            P.line([(ic_x - 1.0, ic_y + 1.0), (ic_x + 1.0, ic_y - 1.0)], INK_L, 0.3, joint=False)
        else:
            P.ell(ic_x, ic_y, 1.05, 1.05, outline=INK_L, lw=0.3)
        figs.append(("아이콘 %d" % j, [(ic_x - 1.2, ic_y - 1.2), (ic_x + 1.2, ic_y - 1.2), (ic_x + 1.2, ic_y + 1.2), (ic_x - 1.2, ic_y + 1.2)]))
        b_, _fa = ptext(cb[0] + 3.4, tby, csp["title"], "b", 2.8, INK_L, "subtitle", layer=lay)
        p5txt.append(b_)
        for k, it in enumerate(csp["body"][:2]):
            yy = float(csp["body_baselines_y"][k])
            if j == 0:
                P.ell(cb[0] + 0.6, yy - 1.0, 0.5, 0.5, fill=INK_L)
            else:
                P.ell(cb[0] + 0.6, yy - 1.0, 0.5, 0.5, outline=INK_L, lw=0.2)
            b_, _fa = ptext(cb[0] + 1.7, yy, it, "m", 2.6, INK_L, "body", layer=lay, pitch=cpitch)
            p5txt.append(b_)
    cbn = pn.get("carbon") if isinstance(pn.get("carbon"), dict) else {}
    b_, _fa = ptext(float(cbn.get("x", x0)), float(cbn.get("baseline_y", y1 - 3.0)), cbn.get("print") or "탄소: 만들 때 배출은 비슷하거나 더 크고, 오래 쓸수록 이득이다",
                    "m", float(cbn.get("face", 2.1)), INK_L, "footnote", layer=lay)
    p5txt.append(b_)
    clear, clear_a = None, None
    for tb_ in p5txt:                                                           # 글자 상자 ↔ 도식 선 최소 간격
        tp = box_poly(tb_)
        for nm, pg in figs:
            d_ = _poly_dist(tp, pg, True, nm != "타임라인")
            if nm.startswith("아이콘"):
                if clear_a is None or d_ < clear_a[0]:
                    clear_a = (d_, nm, [round(v, 2) for v in tb_])
                continue
            if clear is None or d_ < clear[0]:
                clear = (d_, nm, [round(v, 2) for v in tb_])
    DRAWN["p5"] = {"steps": st_rec, "cells": [c_["title"] for c_ in cells_sp[:2]], "stair_line": [], "stair_lw": 0.35, "fill_plates": 0, "oblique": 0, "timeline": True,
                   "text_line_clear_mm": round(clear[0], 2) if clear else None, "text_line_clear_at": clear[1:] if clear else None,
                   "text_marker_clear_mm": round(clear_a[0], 2) if clear_a else None, "text_marker_clear_at": clear_a[1:] if clear_a else None}


def draw_panel_S():
    """100 VS 2,000(❻ 안): 막대 2개 + 각주 2줄"""
    pn = PANEL["S"]
    x0, y0, x1, y1 = pn["rect"]
    lay = "패널 S"
    bars = pn.get("bars") or {}
    h = float(bars.get("height", 4.0))
    rx = float(bars.get("cap_rx", 0.6))
    lx = float(bars.get("left_x", x0 + 2.0))
    yb = float(bars.get("head_baseline_y", y0 + 7.4))
    box, fa = ptext(lx, yb, "100 VS 2,000", "en", 5.0, ACCENT, "head_en", layer=lay, panel="S")
    fk = fface("b", 2.8, "콘크리트 수명")[2]
    ptext(box[2] + 2.0, (yb - fa) + fk * (0.812 / 0.870), "콘크리트 수명", "b", 2.8, ACCENT, "head_ko", layer=lay, panel="S")
    items = bars.get("items") or []
    ycs = bars.get("yc") or [yb + 4.6, yb + 11.0]
    fills = [((178, 180, 182), (204, 206, 208), (130, 132, 134)), ((190, 178, 158), (214, 204, 186), (136, 124, 104))]
    for k, it in enumerate(items[:2]):
        yc = float(ycs[k])
        ox_ = float(it["outer_x"])
        fb, fc, oc = fills[k]
        P.rect(lx, yc - h / 2.0, ox_ - rx, yc + h / 2.0, fill=fb)
        P.ell(ox_ - rx, yc, rx, h / 2.0, fill=fc, outline=oc, lw=0.12)
        inside = "안" in str(it.get("text", ""))
        if inside:
            bx_, _fa = ptext(lx + 2.0, yc + 1.3, it["print"], "b", 2.6, INK_L, "body", layer=lay)
            rng = local_rng("S막대")
            for i in range(10):
                xx = bx_[2] + 1.5 + rng.random() * max(0.5, ox_ - rx - bx_[2] - 3.0)
                P.ell(xx, yc - h / 2 + 0.7 + rng.random() * (h - 1.4), 0.3, 0.26, fill=(246, 244, 236))
        else:
            ptext(ox_ + 2.0, yc + 1.3, it["print"], "b", 2.6, INK_L, "body", layer=lay)
        DRAWN["s_bars"].append({"name": it["print"], "x0": round(lx, 3), "x1": round(ox_, 3), "h": h, "cap_rx": rx,
                                "box": [round(lx, 3), round(yc - h / 2.0, 3), round(ox_, 3), round(yc + h / 2.0, 3)]})
    fn = pn.get("footnote") or ["강도가 아니라 수명이다", "압축 강도는 현대 콘크리트가 높다"]
    for t_, yy in zip(fn, pn.get("footnote_baselines_y") or [y0 + 22.0, y0 + 25.0]):
        ptext(lx, float(yy), t_, "m", 2.1, INK_L, "footnote", layer=lay, pitch=3.0)


# ───────────────────────── 10 기록·검사(drawn.json: 사후 검사용, 인쇄 지면에는 그리지 않는다) ─────────────────────────
def overlap_check():
    K = 2
    masks = []
    for name, poly in LABEL_POLYS:
        m = Image.new("L", (PW * K, PH * K), 0)
        ImageDraw.Draw(m).polygon([(x * K, y * K) for x, y in poly], fill=255)
        masks.append((name, m, bbox_of(poly)))
    info = []
    for name, poly in INFO_POLYS:
        m = Image.new("L", (PW * K, PH * K), 0)
        ImageDraw.Draw(m).polygon([(x * K, y * K) for x, y in poly], fill=255)
        info.append((name, m, bbox_of(poly)))

    def hit(a, b):
        (na, ma, ba), (nb, mb, bbb) = a, b
        if min(ba[2], bbb[2]) - max(ba[0], bbb[0]) <= 0 or min(ba[3], bbb[3]) - max(ba[1], bbb[1]) <= 0:
            return 0.0
        cr = (int(max(ba[0], bbb[0]) * K) - 1, int(max(ba[1], bbb[1]) * K) - 1, int(min(ba[2], bbb[2]) * K) + 2, int(min(ba[3], bbb[3]) * K) + 2)
        ov = ImageChops.multiply(ma.crop(cr), mb.crop(cr))
        return ov.histogram()[255] / float(K * K)
    out = []
    for i in range(len(masks)):
        for j in range(i + 1, len(masks)):
            a = hit(masks[i], masks[j])
            if a > 0.3:
                out.append((masks[i][0], masks[j][0], round(a, 1)))
        for k in range(len(info)):
            a = hit(masks[i], info[k])
            if a > 0.3:
                out.append((masks[i][0], info[k][0], round(a, 1)))
    REPORT["label_overlaps"] = out


def hierarchy_check():
    """그린 외곽(투영 상자)으로 위계를 다시 판정한다(보고서용)"""
    o = REPORT["objects"]

    def area(k):
        b = o[k]["그린 외곽"]
        return (b[2] - b[0]) * (b[3] - b[1])
    hero = area("hero")
    lms = {k: area(k) for k in sorted(o) if re.match(r"^L\d+$", k)}
    basic = {p: PANEL[p]["box_area"] for p in PANEL if PANEL[p]["tier"] == "Basic"}
    zc = z1_composite_box()
    detail = {"Z1(합성)": (zc[2] - zc[0]) * (zc[3] - zc[1])}
    sup = PANEL["S"]["box_area"]
    REPORT["hierarchy_drawn"] = {
        "콜로세움 mm²": int(round(hero)), "랜드마크 mm²": {k: int(round(v)) for k, v in lms.items()},
        "Basic mm²": basic, "Detail mm²": {k: int(round(v)) for k, v in detail.items()}, "Support mm²": sup,
        "콜로세움 ≥ 랜드마크 최대 × 1.1": hero >= max(lms.values()) * 1.1,
        "Basic 최소 ≥ Detail 최대": min(basic.values()) >= max(detail.values()),
        "Detail 최소 ≥ Support × 1.1": min(detail.values()) >= sup * 1.1,
    }


def _alpha4(L):
    return np.array(L.img.getchannel("A").resize((PW * OK4, PH * OK4), Image.BOX)) >= 128


def measure_density():
    """결정 14: (건물·소품·사람·나무·밭·포도밭·구릉 층의 알파 ≥ 128 합집합) ÷ (무대 189,048mm² − 패널·Detail이 덮는 면적)"""
    if np is None:
        DRAWN["density"] = {"pct": None, "note": "numpy 없음"}
        return
    obj = _alpha4(OBJ) | _alpha4(TER)
    stg = np.array(stage_mask(OK4)) > 0
    cov = Image.new("L", (PW * OK4, PH * OK4), 0)
    d = ImageDraw.Draw(cov)
    for pid, pn in PANEL.items():
        r = pn["rect"]
        d.rectangle([r[0] * OK4, r[1] * OK4, r[2] * OK4 - 1, r[3] * OK4 - 1], fill=255)
    cov = np.array(cov) > 0
    a_px = 1.0 / (OK4 * OK4)
    stage_mm2 = float(stg.sum()) * a_px
    cov_mm2 = float((stg & cov).sum()) * a_px
    num = float((obj & stg & ~cov).sum()) * a_px
    den = stage_mm2 - cov_mm2
    obj_only = float((_alpha4(OBJ) & stg & ~cov).sum()) * a_px
    num_full = float((obj & stg).sum()) * a_px
    DRAWN["density"] = {"pct": round(100.0 * num / den, 2), "pct_open_stage": round(100.0 * num / den, 2),
                        "pct_full_stage": round(100.0 * num_full / STAGE_AREA, 2), "num_full_mm2": round(num_full, 1), "full_stage_mm2": round(STAGE_AREA, 1),
                        "num_mm2": round(num, 1), "den_mm2": round(den, 1), "stage_mm2": round(stage_mm2, 1),
                        "covered_mm2": round(cov_mm2, 1), "landmark_layer_mm2": round(obj_only, 1), "terrain_layer_mm2": round(num - obj_only, 1),
                        "rule": "pct = pct_open_stage = 알파 ≥ 128(랜드마크·소품·사람 층 ∪ 밭·포도밭·구릉·지붕·나무 층) ÷ (무대 173,460 − 패널·Detail 덮는 면적). "
                                "pct_full_stage = 같은 분자(덮인 곳 포함) ÷ 전체 무대 173,460. 바탕 지면·강·바다·길·라벨·바닥 글 제외",
                        "target_pct": 39.3}


def _lum(c):
    def ch(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def measure_floor_contrast(img):
    """물 이름 바닥 글(TIBERIS·MARE TYRRHENUM) 잉크 ↔ 글 둘레 물빛(렌더 실측 중앙값)의 명도 대비(WCAG 식)"""
    out = {}
    if np is None:
        return
    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    k = img.size[0] / float(PW)
    for f in FLOORS:
        if not (f["name"].startswith("TIBERIS") or f["name"].startswith("MARE") or f["name"].startswith("티레니아")):
            continue
        e = bbox_of(f["poly"])
        X0, Y0, X1, Y1 = [int(round(v * k)) for v in (e[0] - 1.5, e[1] - 1.5, e[2] + 1.5, e[3] + 1.5)]
        X0, Y0 = max(0, X0), max(0, Y0)
        sub = arr[Y0:Y1, X0:X1].reshape(-1, 3)
        ink = np.array(INK_WATER, dtype=np.float32)
        dist = np.abs(sub - ink).sum(axis=1)
        bgp = sub[dist > 90]
        if len(bgp) == 0:
            continue
        bg = tuple(int(v) for v in np.median(bgp, axis=0))
        la, lb = _lum(INK_WATER), _lum(bg)
        cr = (max(la, lb) + 0.05) / (min(la, lb) + 0.05)
        out[f["name"]] = {"ink": list(INK_WATER), "water_median": list(bg), "contrast": round(cr, 2)}
    for nm, col in (("강(기준색)", RIV_C), ("바다(기준색)", SEA_C)):
        la, lb = _lum(INK_WATER), _lum(col)
        out[nm] = {"ink": list(INK_WATER), "water": list(col), "contrast": round((max(la, lb) + 0.05) / (min(la, lb) + 0.05), 2)}
    DRAWN["floor_contrast"] = out


def measure_label_clearance():
    """라벨 글 블록 ↔ 건물(알파 ≥ 128) 최소 간격(렌더 실측)"""
    if np is None:
        return
    obj = (_alpha4(OBJ) | _alpha4(TER)).astype(np.uint8) * 255
    dt = cv2.distanceTransform(np.where(obj > 0, 0, 255).astype(np.uint8), cv2.DIST_L2, 5) / float(OK4)
    for rec in DRAWN["labels"]:
        if "태그" in rec.get("kind", ""):
            continue
        poly = [tuple(p) for p in rec["poly"]]
        rec["clearance"] = {"building": round(_clear_of(dt, poly), 2)}
        if rec["clearance"]["building"] < 2.05:
            e = bbox_of(poly)
            X0, Y0, X1, Y1 = [int(v * OK4) for v in (e[0] - 3, e[1] - 3, e[2] + 3, e[3] + 3)]
            ys, xs = np.nonzero(obj[max(0, Y0):Y1, max(0, X0):X1])
            near = None
            for yy, xx in zip(ys[::7], xs[::7]):
                pt = ((xx + max(0, X0)) / OK4, (yy + max(0, Y0)) / OK4)
                dd = _pt_poly_gap(pt, poly)
                if near is None or dd < near[0]:
                    near = (dd, pt)
            if near:
                rec["clearance"]["nearest_building_pt"] = [round(near[1][0], 1), round(near[1][1], 1)]
        rec["clearance"]["road"] = None                              # 사용자 16:14: 길이 없다


def measure_road_gaps():
    """사용자 16:14: 길 전부를 지웠으므로 길–지면 간격 측정은 없다(기록만 비운다)"""
    DRAWN["road_gaps"] = {}


def write_drawn():
    for pid, pn in PANEL.items():
        DRAWN["boxes"].append({"id": pid, "kind": "패널", "tier": pn["tier"], "box": list(pn["rect"]), "border": False})
    for k, v in REPORT["objects"].items():
        b = v.get("그린 외곽")
        if b:
            o_ = {"id": k, "name": v.get("이름", k), "box": b}
            if k in SIL_MM2:
                o_["sil_mm2"] = SIL_MM2[k]
            DRAWN["objects"].append(o_)
    n_ld = len(DRAWN.get("leaders", []))
    DRAWN["strokes"] = [{"role": "지시선", "lw": LEAD_W, "print": True, "count": n_ld},
                        {"role": "콜아웃 테두리", "lw": 0.25, "print": True, "count": len([b for b in DRAWN["boxes"] if b.get("kind") == "콜아웃"])},
                        {"role": "Z1 테두리", "lw": 0.60, "print": True, "count": 1},
                        {"role": "P5 타임라인", "lw": float((DRAWN.get("p5") or {}).get("stair_lw") or 0.35), "print": True, "count": 1},
                        {"role": "내부선", "lw": float((DRAWN.get("print_lines") or {}).get("min_lw_mm") or 0.10), "print": True, "count": 1}]
    if DRAWN.get("p5") and DRAWN["p5"].get("stair_line"):
        DRAWN["p5"]["stair"] = {"pts": DRAWN["p5"]["stair_line"], "lw": DRAWN["p5"].get("stair_lw", 0.35), "fill": False}
        DRAWN["p5"]["fill_boxes"] = 0
    DRAWN["tier_color_uses"] = TIER_USES[0]
    DRAWN["stage"] = {"rects": [list(r) for r in STAGE_RECTS], "area_mm2": STAGE_AREA, "ext_rects": [],
                      "rule": "d4: 무대 확장 해제(R·T 자리 = 종이/띠 바탕, 지형·밭·포도밭 0)"}
    DRAWN["forms"] = {k: GEO[k] for k in ("aqueduct_form", "basilica_form", "hypogeum") if k in GEO}
    hh_ = DRAWN.get("hero") or {}
    DRAWN["forms"]["hero"] = {"semi_axes_plan": [CO_A, CO_B], "major_az_deg": 315.0, "center_plan": list(CO_C),
                              "wall_profile": HCOL.get("wall_profile"), "second_ring": HCOL.get("second_ring"),
                              "wood_frac": (hh_.get("arena") or {}).get("wood_share"), "base_side_mm": 0.0, "front_cut": False,
                              "heights_measured": hh_.get("heights_check"), "heights_ok": hh_.get("heights_ok"),
                              "rule": "그린 본체 값(render가 쓴 CO_* 상수와 사양 wall_profile). θ 구간 실측은 heights_measured"}
    DRAWN["vesuvius_cover_mm"] = GEO.get("ves_cover_mm")
    DRAWN["silhouette_gaps"] = SIL_GAPS
    DRAWN["print_rule"] = "인쇄 지면에 보이는 것만 그렸다(위치도·연대기·티어 표기·크기 꼬리표·검사 수치·설계 주석 0). 이 기록은 사후 검사용이다"
    DRAWN["notes"] = REPORT["notes"]
    DRAWN["sil_mm2"] = SIL_MM2
    DRAWN["scatter"] = {"items": SCATTER_OUT, "count": len(SCATTER_OUT), "rule": "13:40 청사진: 화면 mm·평면 mm. 집 w·d·h(평면 mm, h = 벽 높이), 나무 h·r. ground는 이 자리·크기에 짓는다"}
    DRAWN["fields"] = {"items": FIELDS_OUT, "count": len(FIELDS_OUT), "rule": "13:40 청사진: 밭 구획 평면 [X0, Y0, X1, Y1]과 화면 다각형, kind = vine·wheat·pasture·fallow"}
    with open(DRAWN_PATH, "w", encoding="utf-8") as fh:
        json.dump(DRAWN, fh, ensure_ascii=False, indent=1)


def build_info_boxes():
    """라벨 자리 잡기 장애물: Detail 원·글 칸·콜아웃, 지도 안 패널(사양 좌표)"""
    mh_ = (S.get("chapter_marks") or {}).get("map_head") or {}
    if mh_:
        bc_ = mh_["badge_c"]
        INFO_BOXES.append(("지도 ❸ 장 머리", box_poly([min(bc_[0] - 5.0, mh_["title_x"] - 25.0), bc_[1] - 5.0, max(bc_[0] + 5.0, mh_["title_x"]), mh_["title_baseline_y"] + 1.0])))
    for pg_ in route_polys():                                                  # 라벨이 읽기 길을 가로지르지 않게 한다(사용자 16:41)
        INFO_BOXES.append(("읽기 길", pg_))
    ent_ = (S.get("route_marks") or {}).get("entrance") or {}
    if ent_:
        INFO_BOXES.append(("입구 표지", box_poly([ent_.get("right_x", 419.0) - 24.0, ent_["baselines_y"][0] - 4.0, ent_.get("right_x", 419.0) + 0.5, ent_["baselines_y"][-1] + 1.5])))
    ex_ = (S.get("route_marks") or {}).get("exit") or {}
    if ex_:
        INFO_BOXES.append(("출구 표지", box_poly([ex_.get("x", 126.0) - 8.0, ex_.get("baseline_y", 470.5) - 4.0, ex_.get("x", 126.0) + 38.0, ex_.get("baseline_y", 470.5) + 1.5])))
    # 확대 창 상자는 랜드마크를 그린 뒤 auto_place_windows()가 자리를 잡으며 등록한다(20:53)
    for pid, pn in PANEL.items():
        r = pn["rect"]
        if in_stage((r[0] + r[2]) / 2.0, (r[1] + r[3]) / 2.0):
            INFO_BOXES.append(("패널 " + pid, box_poly(r)))
    for _nm, pts, _l, _k in detail_leaders():
        PLACED_LEADS.append(pts)


INFO_BOXES = []
SIL_GAPS = {}


def measure_sil_gaps():
    """새 실루엣(볼록 부품 합집합) ↔ 이웃 건물 간격(mm). 콜로세움은 외벽 실루엣(여유 없음) + 받침. 길–지면 접속·다리–강·다리–R7은 접속이라 뺀다"""
    hero = [pg for pg in (GEO.get("col_sil"),) if pg]                          # 사용자 16:14: 콜로세움 건물 실루엣(받침 0)

    def fp(*names):
        return [GEO["fp_" + n] for n in names if GEO.get("fp_" + n)]
    groups = {"콜로세움": hero, "바실리카": GEO.get("parts_L7") or [], "네로 거상": GEO.get("parts_colossus") or [],
              "극장": GEO.get("parts_L9") or [], "영묘": (GEO.get("parts_L8") or [])[:2], "영묘 다리": (GEO.get("parts_L8") or [])[2:],
              "판테온": fp("아크로폴리스 지면", "아크로폴리스 암반", "파르테논 엔타블러처"), "욕장": fp("욕장 지면"), "시장": fp("시장 지면"),
              "포르투스 육각 내항": fp("포르투스 육각 내항"),               "오스티아": fp("오스티아")}
    pairs = [("바실리카", "콜로세움"), ("바실리카", "네로 거상"), ("바실리카", "욕장"), ("바실리카", "시장"), ("네로 거상", "콜로세움"),
             ("극장", "판테온"), ("영묘", "포르투스 육각 내항"), 
             ]
    for a_, b_ in pairs:
        A_, B_ = groups.get(a_) or [], groups.get(b_) or []
        if A_ and B_:
            SIL_GAPS["%s ↔ %s" % (a_, b_)] = round(min(_poly_dist(pa, pb) for pa in A_ for pb in B_), 2)
    rv = GEO.get("river_poly")
    for nm, key in (("극장 ↔ 강(접속 허용)", "극장"), ("영묘 ↔ 강(접속 허용)", "영묘")):
        if rv and groups.get(key):
            SIL_GAPS[nm] = round(min(_poly_dist(pg, rv) for pg in groups[key]), 2)


def exclude_marks():
    for mk in MARKS:                                                 # 짝 표지(지도 쪽) 둘레 2mm에는 지붕·나무·밭을 두지 않는다
        if mk["source"] == "map":
            ex_circle(mk["c"], MARK_R, 2.0)


# ───────────────────────── 정보 층(INFO_ONLY=1, 결정 D11·D12): Blender 실루엣·앵커에 지시선 끝·짝 표지를 맞춘다 ─────────────────────────
INFO_ONLY = os.environ.get("INFO_ONLY") == "1"
INFO_DIR = None
if INFO_ONLY:                                                       # 출력은 <d>/out/info/에만(설계 diagram.png·drawn.json을 덮어쓰지 않는다)
    _od = os.path.dirname(os.path.abspath(OUT))
    INFO_DIR = _od if os.path.basename(_od) == "info" else os.path.join(_od, "info")
    os.makedirs(INFO_DIR, exist_ok=True)
    OUT = os.path.join(INFO_DIR, "info_layer.png")
    DRAWN_PATH = os.path.join(INFO_DIR, "drawn_info.json")
ANCHOR_MAP = {   # 앵커 이름(ANCHOR_ 뒤) → (종류, 정보 층 요소). 사용자 16:14: 지워진 대상(공사장·베수비오·배·하역장)의 앵커는 없다
    "HERO_label": ("label", "콜로세움"), "NERO_label": ("label", "네로 거상"),
    "L1_label": ("label", "판테온"), "L2_label": ("label", "트라야누스 시장"), "L3_label": ("label", "카라칼라 욕장"), "L4_label": ("label", "수도교"),
    "L5_label": ("label", "카이킬리아 메텔라 무덤"), "L6_label": ("label", "포르투스 항"), "L7_label": ("label", "막센티우스 바실리카"),
    "L8_label": ("label", "하드리아누스 영묘"), "L9_label": ("label", "마르켈루스 극장"),
    "L4_m1": ("mark", "1"), "L7_m2": ("mark", "2"), "L2_m3": ("mark", "3"), "L1_m4": ("mark", "4"),
}
SNAP_MM = 6.0
SIL = None                                                          # {"path", "polys": [(id, poly)], "anchors": {이름: (x, y)}}
INFO_CHECK = {"anchors": [], "unmatched": [], "label_sil": [], "notes": []}


def _round_no():
    v = os.environ.get("INFO_ROUND")
    if v and v.isdigit():
        return int(v)
    for p_ in (os.path.dirname(os.path.abspath(__file__)), SPEC_PATH, OUT):
        m = re.search(r"/d(\d+)(?:\.[a-z]+)?(?:/|$)", p_)
        if m:
            return int(m.group(1))
    return None


def load_sil():
    """.work/blender/rounds/b{N}/sil.json(bglobal roma_render.export_sil): 루트별 {id, box, poly, area}와 앵커 화면 좌표"""
    global SIL
    n = _round_no()
    path = os.environ.get("SIL_JSON") or os.environ.get("INFO_SIL") or (ROOT + "/.work/blender/rounds/b%d/sil.json" % n if n is not None else None)
    INFO_CHECK["round"] = n
    INFO_CHECK["sil_path"] = path
    if not path or not os.path.exists(path):
        INFO_CHECK["notes"].append("sil.json 없음 → 지시선 끝·짝 표지·라벨 장애물은 사양 점과 설계 그림을 쓴다")
        return None
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception as e_:
        INFO_CHECK["notes"].append("sil.json 읽기 실패: %s" % e_)
        return None
    roots = d.get("roots") or d.get("objects") or d.get("silhouettes") or []
    if isinstance(roots, dict):
        roots = [dict(v, id=k) if isinstance(v, dict) else {"id": k, "poly": v} for k, v in roots.items()]
    anc = d.get("anchors") or {}
    if isinstance(anc, list):
        anc = {str(a.get("name") or a.get("id")): (a.get("screen") or a.get("pt") or a.get("xy") or [a.get("x"), a.get("y")]) for a in anc if isinstance(a, dict)}
    raw = []
    for r_ in roots:
        pg = r_.get("poly") or r_.get("contour") or []
        if isinstance(pg, list) and len(pg) >= 3:
            raw.append((str(r_.get("id") or r_.get("name")), [tuple(map(float, p[:2])) for p in pg]))
    pts_all = [p for _n, pg in raw for p in pg] + [tuple(v[:2]) if not isinstance(v, dict) else tuple((v.get("pt") or v.get("screen") or [v.get("x"), v.get("y")])[:2]) for v in anc.values() if v]
    k_ = 3.0 if pts_all and max(max(abs(float(p[0] or 0)) for p in pts_all), max(abs(float(p[1] or 0)) for p in pts_all) / 1.414) > 600 else 1.0   # 화소(3 px/mm)면 mm로
    polys = [(nm, [(x / k_, y / k_) for x, y in pg]) for nm, pg in raw]
    anchors = {}
    for nm, v in anc.items():
        if isinstance(v, dict):
            v = v.get("pt") or v.get("screen") or [v.get("x"), v.get("y")]      # bglobal export_sil: {"pt": [x, y], "world", "root", "on_sil"}
        if isinstance(v, (list, tuple)) and len(v) >= 2 and v[0] is not None:
            anchors[re.sub(r"^ANCHOR_", "", str(nm))] = (float(v[0]) / k_, float(v[1]) / k_)
    SIL = {"path": path, "polys": polys, "anchors": anchors, "scale": k_}
    INFO_CHECK["sil_roots"] = len(polys)
    INFO_CHECK["sil_anchors"] = sorted(anchors)
    return SIL


def _anchor(name):
    return (SIL or {}).get("anchors", {}).get(name) if SIL else None


def apply_anchor_targets():
    """라벨 대상점(target_pt)을 앵커 쪽으로(6mm 안이면). 라벨 자리 잡기 전에 부른다"""
    if not SIL:
        return
    for an, (kind, key) in ANCHOR_MAP.items():
        if kind != "label" or key not in SLOT:
            continue
        a = _anchor(an)
        if a is None:
            INFO_CHECK["unmatched"].append({"anchor": an, "target": key, "reason": "sil.json에 앵커 없음"})
            continue
        tp = SLOT[key].get("target_pt")
        if tp and math.hypot(a[0] - tp[0], a[1] - tp[1]) <= SNAP_MM:
            SLOT[key]["target_pt_spec"] = list(tp)
            SLOT[key]["target_pt"] = [a[0], a[1]]
            GEO["lead_tgt_" + key] = (a[0], a[1])


def _slide_end(pts, a):
    """지시선 마지막 선분 위에서 앵커에 가장 가까운 점으로 끝을 옮긴다(방향 유지, 수직 거리 ≤ 0.6mm일 때만)"""
    (x0, y0), (x1, y1) = pts[-2], pts[-1]
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy
    if L2 < 1e-9:
        return None
    t = ((a[0] - x0) * dx + (a[1] - y0) * dy) / L2
    q = (x0 + dx * t, y0 + dy * t)
    if t <= 0.05 or math.hypot(q[0] - a[0], q[1] - a[1]) > 0.6:
        return None
    return pts[:-1] + [q]


def snap_info_to_anchors():
    """라벨 지시선 끝·Detail 지시선 시작점·지도 쪽 짝 표지를 앵커에 맞춘다(6mm 안). 결과는 INFO_CHECK에"""
    if not SIL:
        for an, (kind, key) in ANCHOR_MAP.items():
            INFO_CHECK["anchors"].append({"anchor": an, "kind": kind, "target": key, "snapped": False, "reason": "sil.json 없음(사양 점 사용)"})
        return
    for an, (kind, key) in ANCHOR_MAP.items():
        a = _anchor(an)
        rec = {"anchor": an, "kind": kind, "target": key, "anchor_pt": [round(a[0], 2), round(a[1], 2)] if a else None}
        if a is None:
            rec.update(snapped=False, reason="앵커 없음")
            INFO_CHECK["anchors"].append(rec)
            continue
        if kind == "label":
            info = LABEL_PLAN.get(key)
            if not info or not info.get("lead"):
                rec.update(snapped=False, reason="라벨 지시선 없음")
            else:
                pts, tname, gap = info["lead"]
                e = pts[-1]
                d_ = math.hypot(e[0] - a[0], e[1] - a[1])
                rec.update(spec_pt=[round(e[0], 2), round(e[1], 2)], dev_mm=round(d_, 2))
                if d_ <= 0.05:
                    rec.update(snapped=True, reason="이미 일치")
                elif d_ <= SNAP_MM:
                    np_ = _slide_end(list(pts), a)
                    if np_:
                        info["lead"] = (np_, tname, gap)
                        rec.update(snapped=True, new_pt=[round(np_[-1][0], 2), round(np_[-1][1], 2)], residual_mm=round(math.hypot(np_[-1][0] - a[0], np_[-1][1] - a[1]), 2))
                    else:
                        rec.update(snapped=False, reason="지시선 방향 밖(꺾임·각도 규칙 유지)")
                else:
                    rec.update(snapped=False, reason="6mm 밖")
        elif kind in ("leader", "link"):
            hit = None
            for ld in (DET["leaders"] if kind == "leader" else [BAS["process_representation"]["link"]]):
                nm = ld.get("name", "")
                if (kind == "link") or (key in nm) or (key.startswith("콜아웃") and nm.endswith(key)):
                    hit = ld
                    break
            if not hit:
                rec.update(snapped=False, reason="지시선 없음")
            else:
                p0 = tuple(hit["pts"][0])
                d_ = math.hypot(p0[0] - a[0], p0[1] - a[1])
                rec.update(spec_pt=[round(p0[0], 2), round(p0[1], 2)], dev_mm=round(d_, 2))
                if d_ <= 0.05:
                    rec.update(snapped=True, reason="이미 일치")
                elif d_ <= SNAP_MM:
                    dx, dy = a[0] - p0[0], a[1] - p0[1]
                    pts = [tuple(p) for p in hit["pts"]]
                    if len(pts) >= 3:                                   # 첫 선분을 평행 이동, 꺾임점 = 두 선의 교점
                        (bx, by), (cx_, cy_) = pts[1], pts[2]
                        d1 = (pts[1][0] - pts[0][0], pts[1][1] - pts[0][1])
                        d2 = (cx_ - bx, cy_ - by)
                        det = d1[0] * d2[1] - d1[1] * d2[0]
                        if abs(det) > 1e-9:
                            t = ((bx - a[0]) * d2[1] - (by - a[1]) * d2[0]) / det
                            bend = (a[0] + d1[0] * t, a[1] + d1[1] * t)
                            hit["pts"] = [[a[0], a[1]], [bend[0], bend[1]]] + [list(p) for p in pts[2:]]
                            rec.update(snapped=True, new_pt=[round(a[0], 2), round(a[1], 2)])
                        else:
                            rec.update(snapped=False, reason="꺾임점 계산 불가")
                    else:                                               # 한 선분: 방향 유지, 끝은 같은 대상 경계(Z1 원·콜아웃 상자)까지 다시 잰다
                        nm_ = hit.get("name", "")
                        tgt_pg = z1_circle_poly() if nm_.endswith("확대 창 Z1") else None
                        for cid in ("C1", "C2", "C4"):
                            if nm_.endswith(cid) and DMAP.get(cid, {}).get("box"):
                                tgt_pg = box_poly(DMAP[cid]["box"])
                        ux_, uy_ = pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1]
                        ln_ = math.hypot(ux_, uy_) or 1.0
                        ux_, uy_ = ux_ / ln_, uy_ / ln_
                        th_ = _ray_hit((a[0], a[1]), (ux_, uy_), [tgt_pg], ln_ + 10.0) if tgt_pg else None
                        if th_:
                            end_ = (a[0] + ux_ * th_, a[1] + uy_ * th_)
                            hit["pts"] = [[a[0], a[1]], [end_[0], end_[1]]]
                            rec.update(snapped=True, new_pt=[round(a[0], 2), round(a[1], 2)], new_end=[round(end_[0], 2), round(end_[1], 2)],
                                       note="방향 유지, 끝은 대상 경계와 다시 만난 점")
                        else:
                            hit["pts"] = [[a[0], a[1]], [pts[-1][0] + dx, pts[-1][1] + dy]]
                            rec.update(snapped=True, new_pt=[round(a[0], 2), round(a[1], 2)], note="끝점도 같은 만큼 옮김(대상 경계와 %.2fmm)" % math.hypot(dx, dy))
                    if kind == "leader" and hit.get("mark_pt"):
                        mp = hit["mark_pt"]
                        hit["mark_pt"] = [mp[0] + dx, mp[1] + dy]
                        for mk in MARKS:
                            if mk["source"] == "map" and math.hypot(mk["c"][0] - mp[0], mk["c"][1] - mp[1]) < 0.05:
                                mk["c"] = [mk["c"][0] + dx, mk["c"][1] + dy]
                else:
                    rec.update(snapped=False, reason="6mm 밖")
        elif kind == "mark":
            cand = [mk for mk in MARKS if mk["source"] == "map" and mk["letter"] == key]
            if not cand:
                rec.update(snapped=False, reason="지도 쪽 표지 없음")
            else:
                mk = min(cand, key=lambda q: math.hypot(q["c"][0] - a[0], q["c"][1] - a[1]))
                d_ = math.hypot(mk["c"][0] - a[0], mk["c"][1] - a[1])
                rec.update(spec_pt=[round(mk["c"][0], 2), round(mk["c"][1], 2)], dev_mm=round(d_, 2))
                if d_ <= SNAP_MM:
                    mk["c"] = [a[0], a[1]]
                    rec.update(snapped=True)
                else:
                    rec.update(snapped=False, reason="6mm 밖")
        else:
            rec.update(snapped=False, reason="말풍선 태그(지시선 없음): 자리만 기록")
        INFO_CHECK["anchors"].append(rec)


def sil_obstacle_mask(m):
    """라벨 장애물: 설계 랜드마크 층 대신 Blender 실루엣 다각형(sil.json)"""
    for _nm, pg in SIL["polys"]:
        _mask_poly(m, pg)
    return m


def measure_label_sil():
    """라벨 글 블록 ↔ Blender 실루엣 겹침·간격(정보 층 검사)"""
    if not SIL:
        return
    for rec in DRAWN["labels"]:
        lp = [tuple(p) for p in rec["poly"]]
        best = None
        for nm, pg in SIL["polys"]:
            d_ = _poly_dist(lp, pg)
            ov = any(in_poly(p, pg) for p in lp) or any(in_poly(p, lp) for p in pg)
            if best is None or d_ < best[0] or ov:
                best = (0.0 if ov else d_, nm, ov)
        if best:
            INFO_CHECK["label_sil"].append({"label": rec["name"], "nearest_root": best[1], "gap_mm": round(best[0], 2), "overlap": best[2]})


def draw_info_bands():
    """정보 층 위 띠(y < 92, 종이 바탕 불투명)와 하단 띠 베일(y ≥ 505): d4 설계 그림과 같은 색·알파.
    하단 띠: d4는 바다를 띠 밑으로 알파 0.62 → 0(아래로)로 흐렸다. Blender 바다가 y 594까지 불투명하므로 종이 베일 알파 = 1 − 0.62·(1 − t)."""
    top = STAGE[1]
    P.rect(0, 0, PW, top, fill=BG + (255,))
    und = SC.get("sea_under_bottom_band") or {}
    ys = [p[1] for p in und.get("poly", [])] or [STAGE[3], 568.0]
    y0_, y1_ = STAGE[3], max(ys)
    V = Layer(0, y0_, PW, PH)
    V.rect(0, y0_, PW, PH, fill=BG + (255,))
    g = Image.linear_gradient("L").resize((V.w, int(round((y1_ - y0_) * KD))))
    g = g.point(lambda v: int(round(255 * (1.0 - 0.62 * (1.0 - v / 255.0)))))
    a = Image.new("L", (V.w, V.h), 255)
    a.paste(g, (0, 0))
    V.img.putalpha(a)
    P.paste(V)
    INFO_CHECK["bands"] = {"top": [0, 0, PW, top], "top_alpha": 1.0, "bottom": [0, y0_, PW, PH], "bottom_alpha": [0.38, 1.0], "bottom_ramp_to_y": y1_,
                           "color": list(BG), "rule": "d4: 하단 띠 밑 바다 알파 0.62→0 ↔ 정보 층 베일 알파 0.38→1.0(y 505→568), 568 아래 1.0"}


def write_info_check():
    if not INFO_ONLY:
        return
    INFO_CHECK["output"] = OUT
    INFO_CHECK["drawn_info"] = DRAWN_PATH
    INFO_CHECK["floor_text_draws"] = FLOOR_DRAWS[0]
    snapped = sum(1 for r in INFO_CHECK["anchors"] if r.get("snapped"))
    INFO_CHECK["summary"] = {"anchors": len(ANCHOR_MAP), "snapped": snapped, "unmatched": len([r for r in INFO_CHECK["anchors"] if not r.get("snapped")]),
                             "label_sil_overlaps": sum(1 for r in INFO_CHECK["label_sil"] if r.get("overlap"))}
    with open(os.path.join(INFO_DIR, "info_check.json"), "w", encoding="utf-8") as fh:
        json.dump(INFO_CHECK, fh, ensure_ascii=False, indent=1)


# ───────────────────────── 11 실행 ─────────────────────────
def _t(tag):
    REPORT.setdefault("timing", []).append([tag, round(time.time() - T_START, 1)])
    sys.stderr.write("[render %5.1fs] %s\n" % (time.time() - T_START, tag))
    sys.stderr.flush()



SIL_MM2 = {}
LANDMARK_CLEAR_MM = 3.0   # 13:35: 시내 집·나무를 랜드마크 그린 외곽 상자에서 3.0mm 밖에만 둔다(ground도 같은 값)
SCATTER_OUT = []    # d5(13:40): draw_scatter가 실제로 놓은 시내 집·나무(와이어프레임 ground가 같은 자리에 짓는다)
FIELDS_OUT = []     # d5(13:40): place_fields가 실제로 놓은 밭 구획


def _sil_call(lid, fn):
    """d5: 랜드마크 한 개를 그린 전후 랜드마크층 알파 ≥ 128 면적 차이 = 그 랜드마크 실루엣 면적(mm²)"""
    a0 = np.array(OBJ.img.getchannel("A")) >= 128
    fn()
    a1 = np.array(OBJ.img.getchannel("A")) >= 128
    SIL_MM2[lid] = round(float((a1 & ~a0).sum()) / (KD * KD), 1)


def _lot_z(lot_id):
    return float(next((lt.get("z", 0.0) for lt in (CM.get("lots") or []) if lt["id"] == lot_id and not lt.get("drawn_in")), 0.0))


def _lot_call(lot_id, lid, fn):
    """구획 높이 z만큼 건물을 위로 올려 그린다(ISO 세로 기준을 −z)"""
    z = _lot_z(lot_id)
    ISO.oy -= z
    try:
        _sil_call(lid, fn)
    finally:
        ISO.oy += z


def main():
    MAP_MODE[0] = True
    _t("시작")
    if INFO_ONLY:
        load_sil()
    build_info_boxes()
    build_marks()
    build_exclusions()
    # 1 바탕 지면(무대 = 지도 무대 하나. 위 띠 오른쪽·하단 띠 오른쪽은 종이/띠 바탕)
    use_layer(BASE)
    draw_ground()
    draw_fx_ground()
    G_land = BASE.img.copy()
    W_layer = Layer(0, 0, PW, PH)
    use_layer(W_layer)
    draw_river()
    draw_fx_river()
    use_layer(BASE)
    open("/Users/um-yunsang/.claude/jobs/f96d1a72/tmp/dbg.txt", "w").write(repr((W_layer.img.getchannel("A").getbbox(), len(GEO.get("water_rects", [])), W_layer.img.size)))
    draw_diorama_water(G_land, W_layer)
    draw_roads()
    draw_plinths()
    # 22:33 옛 왼쪽 아래 바다·해안 단면 없음(바다 = 물 직사각형 sea·tiber)
    draw_route()                                                     # 사용자 16:41: 읽기 길 한 줄(입구 → 정거장 → 강 → 출구)
    register_floor_polys()
    _t("지면")
    # 2 랜드마크·소품 층(뒤 → 앞): 바실리카는 카라칼라 다음·시장 전, 극장은 판테온 다음, 영묘는 포르투스 다음, 거상은 아레나 전
    use_layer(OBJ)
    # 21:38 카라칼라 욕장 지도에서 제거(draw_caracalla 안 부름)
    _sil_call("L4", draw_aqueduct)
    _lot_call("basilica", "L7", draw_basilica)
    _lot_call("market", "L2", draw_market)
    _sil_call("L1", draw_pantheon)
    _sil_call("L9", draw_theatre)
    draw_colossus()
    _sil_call("HERO_ALL", draw_arena)
    _lot_call("metella", "L5", draw_metella)
    _sil_call("L6", draw_portus)
    _sil_call("L8", draw_mausoleum)
    _record_hero_group()
    auto_place_all()
    if os.environ.get("DUMP_OBJ_MASK"):
        OBJ.img.getchannel("A").resize((PW * 2, PH * 2), Image.BOX).save(os.environ["DUMP_OBJ_MASK"])
    snap_marks()
    exclude_marks()
    _t("랜드마크")
    # 3 라벨 자리 잡기(랜드마크 실측 외곽 기준). 지형 층의 베수비오는 외곽만 먼저 등록한다(브래킷 대상)
    use_layer(BASE)
    if INFO_ONLY:
        apply_anchor_targets()
    plan_labels()
    if INFO_ONLY:
        snap_info_to_anchors()
    _t("라벨 자리")
    # 4 지형 층(밭·베수비오·농장·구릉·지붕·나무) — 랜드마크 층 아래로 합성. 그리는 순서: 산 → 농장 → 구릉
    use_layer(TER)
    draw_fx_hills()
    _tm = Image.new("L", TER.img.size, 0)                                  # 지형은 지도 창(y 92~478) 밖으로 새지 않는다
    ImageDraw.Draw(_tm).rectangle([0, int(92 * KD), TER.img.size[0], int(478 * KD)], fill=255)
    TER.img.putalpha(ImageChops.multiply(TER.img.getchannel("A"), _tm))
    use_layer(TER)                                                   # 사용자 16:14: 밭·베수비오·농장·구릉·집·나무·인물·소품은 지도에서 지웠다(Core 건축물만)
    BASE.img.alpha_composite(TER.img)
    _om = Image.new("L", OBJ.img.size, 0)                                  # 건물은 지도 창(y 478) 아래 띠로 넘치지 않는다
    ImageDraw.Draw(_om).rectangle([0, 0, OBJ.img.size[0], int(478 * KD)], fill=255)
    OBJ.img.putalpha(ImageChops.multiply(OBJ.img.getchannel("A"), _om))
    BASE.img.alpha_composite(OBJ.img)
    use_layer(BASE)
    # 와이어프레임 합성용 정보 층만(INFO_ONLY=1, 결정 D12): 지도 그림은 Blender가 맡는다. 투명 바탕에 위 띠(종이)·하단 띠 베일 → 바닥 글(한 번) → Detail·라벨·패널
    if INFO_ONLY:
        BASE.img = Image.new("RGBA", BASE.img.size, (0, 0, 0, 0))
        BASE.d = ImageDraw.Draw(BASE.img)
        draw_info_bands()
    _t("지형")
    draw_floor_texts()                                               # 바닥 글은 지형·건물 위(구릉 위 COLLI ALBANI가 보이게). 한 번만 그린다
    # 5 Detail·라벨·틀
    MAP_MODE[0] = False
    draw_leaders()
    draw_labels()
    draw_detail_windows()
    draw_map_head()
    draw_route_marks()
    draw_title()
    draw_panel_L()
    draw_panel_P2()
    draw_panel_B()
    draw_panel_D()
    draw_panel_P5()
    draw_panel_S()
    draw_marks()
    _t("패널")
    # 6 기록·검사(그리지 않는다)
    overlap_check()
    hierarchy_check()
    measure_density()
    measure_label_clearance()
    measure_road_gaps()
    measure_route()
    measure_marks()
    measure_sil_gaps()
    if INFO_ONLY:
        measure_label_sil()
    DRAWN["print_lines"] = {"min_lw_mm": LW_MIN, "leader": LEAD_W, "callout_border": 0.25, "z1_border": 0.6,
                            "rule": "인쇄 내부선 0.10~0.20mm(이보다 가는 보조선 0 — Layer 선 굵기 하한 %.2f), 지시선 0.30 · 콜아웃 테두리 0.25 · Z1 테두리 0.60" % LW_MIN,
                            "thinner_requested": LW_LOG["n"], "print_false": []}
    out = BASE.img.resize((PW * OUT_PX_PER_MM, PH * OUT_PX_PER_MM), Image.LANCZOS)
    out = out if INFO_ONLY else out.convert("RGB")
    measure_floor_contrast(out)
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    out.save(OUT, optimize=True)
    write_drawn()
    write_info_check()
    REPORT["output"] = OUT
    REPORT["drawn"] = DRAWN_PATH
    REPORT["size_px"] = out.size
    REPORT["density"] = DRAWN["density"].get("pct")
    REPORT["tier_color_uses"] = TIER_USES[0]
    REPORT["seconds"] = round(time.time() - T_START, 1)
    print(json.dumps(REPORT, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
