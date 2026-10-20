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
  둘레는 승인 설계 히어로 군(광장 판석·문 길·인물 무리 4·흩어진 사람·둘레 나무·공사장·네로 거상 마당)이다. 기준선 8.1의 12:49 사용자 철회에 따라
  LocalBanana 조경 부품(폐허·신전·노점 배치)은 옮겨 오지 않는다. P5 계단은 채움판 없는 꺾은선, P2 ④ 돔은 반구 절개(결정 D15·D16).
  INFO_ONLY=1이면 정보 층만 <d>/out/info/info_layer.png·drawn_info.json·info_check.json으로 쓰고, sil.json이 있으면 앵커에 맞춘다(결정 D11·D12).
- 그리는 순서: 바탕 지면(지면·강·바다·해안·길·바닥 글) → 랜드마크·소품 층 → 라벨 자리 잡기 →
  지형 층(먼 밭·밭·베수비오·농장·구릉·지붕·나무, 랜드마크 층 아래로 합성) → Detail(확대 창·콜아웃·지시선) → 지도 라벨 → 타이틀·패널
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


D4_P2 = {"id": "P2", "tier": "Basic", "name": "아치·볼트·돔(콘크리트가 가능하게 한 모양)", "rect": [302.0, 20.0, 402.0, 92.0], "size": [100.0, 72.0], "box_area": 7200}
D4_P5 = {"id": "P5", "tier": "Basic", "name": "지금 배우는 중(연구 → 현장 → 적용)", "rect": [312.0, 505.0, 402.0, 568.0], "size": [90.0, 63.0], "box_area": 5670}
D4_PAIR_MARKS = [  # 숫자 짝 표지 1~4: 지도 쪽 + P2 칸 쪽(결정 5·6)
    {"mark": "1", "map_pt": [372.0, 163.0], "panel_pt": [304.5, 33.5], "target": "수도교 아치 면"},
    {"mark": "2", "map_pt": [225.0, 177.0], "panel_pt": [330.17, 33.5], "target": "바실리카 측랑 가운데 칸 열린 면"},
    {"mark": "3", "map_pt": [100.0, 112.0], "panel_pt": [355.83, 33.5], "target": "트라야누스 시장 대회랑 걷은 지붕 칸(교차 볼트) 윗면", "tol": 5.0, "snap": "market_vault"},
    {"mark": "4", "map_pt": [78.0, 203.0], "panel_pt": [381.5, 33.5], "target": "판테온 돔 윗면", "tol": 4.0, "snap": "pantheon_dome"},
]
D4_LEADER_MARK_PT = {"A": [271.77, 382.46], "B": [90.77, 217.34], "C": [52.77, 421.46], "D": [367.27, 314.66]}   # 지도 쪽 짝 표지(d3 자리 유지)
D4_LANDMARKS = [
    {"id": "L7", "name": "막센티우스 바실리카", "latin": "Basilica of Maxentius(Basilica Nova)", "tier": "Core(표준 랜드마크)",
     "projected_box": [178.0, 152.0, 255.0, 212.5], "projected_area_mm2": 4663, "geo_approx": [41.8917, 12.4886],
     "plan": {"base_rects": [[276.0, 43.5, 338.0, 62.0], [292.5, 43.5, 338.0, 87.0]], "base_h": 1.5, "aisle": [292.5, 43.5, 338.0, 55.5],
              "aisle_h": 16.0, "bays": 3, "nave": [292.5, 55.5, 338.0, 87.0], "ruin_h": 4.0, "vault_h": 10.0}},
    {"id": "L8", "name": "하드리아누스 영묘 + 폰스 아일리우스", "latin": "Mausoleum Hadriani · Pons Aelius", "tier": "Core(표준 랜드마크)",
     "projected_box": [83.6, 378.5, 162.6, 439.8], "projected_area_mm2": 4843, "geo_approx": [41.9031, 12.4663],
     "plan": {"base": [466.0, 325.5, 510.0, 369.5], "base_h": 5.0, "drum_c": [488.0, 347.5], "drum_r": 16.0, "drum_z": [5.0, 23.0],
              "top_z": [23.0, 28.0], "bridge": [484.5, 304.76, 491.5, 325.5], "bridge_h": 3.0, "bridge_arches": 3}},
    {"id": "L9", "name": "마르켈루스 극장", "latin": "Theatrum Marcelli", "tier": "Core(표준 랜드마크)",
     "projected_box": [32.3, 271.4, 111.7, 329.3], "projected_area_mm2": 4598, "geo_approx": [41.8919, 12.4797],
     "plan": {"center": [340.0, 264.76], "r": 38.0, "h": 12.0, "tier_h": 6.0, "stage_wall_h": 4.0}},
]
D4_COLOSSUS = {"name": "네로 거상 받침(벽돌 마감 콘크리트 받침 + 청동 거상, 거상은 복원 추정)", "box": [178.1, 200.8, 191.9, 226.0],
               "zone": "콜로세움 뒤-왼쪽과 바실리카 사이(베누스·로마 신전 쪽)", "on": "땅", "plan": [328.8, 115.2],
               "base_mm": 8.0, "base_h": 5.0, "statue_mm": 2.4, "statue_h": 15.0}
D4_R7 = {"id": "R7", "name": "영묘 길(콜로세움 받침 앞-왼쪽 변 ↙ 폰스 아일리우스)", "w_screen_perp_mm": 8.0, "center_line": False,
         "plan_pts": [[488.0, 263.81], [488.0, 304.76]], "screen_pts": [[194.15, 375.9], [158.7, 396.4]]}
D4_SLOTS = {
    "막센티우스 바실리카": {"name": "막센티우스 바실리카(Basilica of Maxentius)", "kind": "브래킷", "wall": "↗(+30°)", "box": [121.5, 175.5, 175.5, 218.5],
                    "en": ["BASILICA OF MAXENTIUS"], "ko": "막센티우스 바실리카", "sup": "Basilica Nova", "body": [],
                    "target": "측랑 왼쪽 칸 열린 면", "target_pt": [212.0, 170.0], "top_line": [276.85, -0.57735], "x_range": [121.5, 175.5],
                    "lead": "규선 연장 + ↘30°(꺾임 ≤ 1)"},
    "네로 거상": {"name": "네로 거상(소품 주석)", "kind": "소품 주석", "wall": "↗(+30°)", "box": [138.0, 190.5, 172.0, 218.0],
              "lines": ["콘크리트(벽돌 마감) 받침 위의", "네로의 청동 거상(추정)"], "target": "거상 머리", "target_pt": [185.0, 201.0],
              "top_line": [289.85, -0.57735], "x_range": [138.0, 172.0], "lead": "블록 오른쪽 끝 ↘30°"},
    "마르켈루스 극장": {"name": "마르켈루스 극장(Theatrum Marcelli)", "kind": "브래킷", "wall": "↘(−30°)", "box": [3.0, 259.9, 30.0, 311.5],
                  "en": ["THEATRE OF", "MARCELLUS"], "ko": "마르켈루스 극장", "sup": None, "body": ["테베레 홍수에 잠긴", "기초에서 결정이 자라", "보강(2011년 연구)"],
                  "target": "관람석·아케이드 윗면", "target_pt": [52.0, 315.0], "top_line": [258.2, 0.57735], "x_range": [3.0, 30.0],
                  "lead": "규선 오른쪽 끝 ↘ 연장 + 수직"},
    "하드리아누스 영묘": {"name": "하드리아누스 영묘(Mausoleum Hadriani)", "kind": "브래킷", "wall": "↗(+30°)", "box": [176.0, 427.3, 208.0, 478.7],
                   "en": ["MAUSOLEUM OF", "HADRIAN"], "ko": "하드리아누스 영묘", "sup": None, "body": ["겉은 대리석,", "속은 콘크리트 원통", "폰스 아일리우스 다리"],
                   "body_alt_sup": "Pons Aelius", "target": "기단 윗면", "target_pt": [140.5, 421.0], "top_line": [547.35, -0.57735], "x_range": [176.0, 208.0],
                   "lead": "블록 왼쪽 끝 ↖30° → 기단 윗면"},
}
D4_SLOT_CHANGES = {   # 이름: (d3 값, d4 값)
    "베수비오": ({"box": [390.0, 22.0, 418.0, 66.0]}, {"kind": "브래킷", "wall": "↗(+30°)", "box": [338.0, 95.0, 358.0, 128.0], "body": ["79년 분화", "약 200 km 남동"],
                                                   "target": "산 왼쪽 비탈", "target_pt": [368.0, 124.0], "lead": "규선 오른쪽 끝 ↗ 연장 + 수직"}),
    "바지선": ({"box": [72.0, 322.0, 88.0, 346.0]}, {"box": [84.0, 330.0, 104.0, 346.0]}),
    "화산재 운반선": ({"box": [154.0, 480.0, 176.0, 503.0]}, {"kind": "깃대형", "box": [146.5, 476.0, 174.0, 503.0], "pole_x": 144.25, "target": "선체",
                                                      "lead": "깃대 x 144.25 수직 ↓ → 선체(끝점 Ø0.9)"}),
}
D4_PROP_CHANGES = {"석회 가마": ([90.1, 303.0, 114.3, 335.0], [118.0, 296.0, 146.0, 328.0]), "바지선 2": ([150.0, 428.0, 184.0, 446.0], [128.0, 440.0, 158.0, 462.0]),
                   "오스티아": ([176.0, 448.0, 206.0, 470.0], [214.0, 466.0, 238.0, 482.0]), "포도밭 농장": ([336.0, 54.0, 378.0, 76.0], [366.0, 122.0, 408.0, 144.0])}
D4_TOPLINE = {k: (v["top_line"], v["x_range"], v["box"]) for k, v in D4_SLOTS.items()}


def _d4_overlay(S_):
    """d4 결정값 채우기. 돌려줌: 바꾼 칸 기록(list)"""
    FR_, CM_, DET_ = S_["frame"], S_["core_map"], S_["detail"]
    d3 = not any(p.get("id") in ("P2", "P5") for p in FR_["panels"])
    out = []
    pids = {p.get("id"): p for p in FR_["panels"]}
    for pd in (D4_P2, D4_P5):
        if pd["id"] not in pids:
            FR_["panels"].append(json.loads(json.dumps(pd)))
            out.append("패널 %s 결정값 rect %s" % (pd["id"], pd["rect"]))
    dp = pids.get("D")
    if dp is not None:
        if d3 and _same(dp.get("rect"), [222.0, 505.0, 308.0, 561.0]):
            dp["rect"] = [220.0, 505.0, 306.0, 561.0]
            out.append("D rect → [220,505,306,561]")
        if not dp.get("mark"):
            dp["mark"] = "A"
        if not dp.get("mark_pt"):
            dp["mark_pt"] = [224.0, 509.8]
            out.append("D mark_pt → (224.0, 509.8)")
    for d in DET_["map_elements"]:
        if d.get("id") == "Z1":
            c = d.get("circle") or {}
            if d3 and _same(c.get("d"), 64.0):
                c["d"] = 60.0
                out.append("Z1 원 Ø64 → Ø60")
            if d3 and _same(d.get("text_box"), [212.0, 426.0, 240.0, 462.0]):
                d["text_box"] = [214.0, 426.0, 242.0, 462.0]
            if d3 and _same(d.get("composite_box"), [212.0, 418.0, 307.0, 482.0]):
                d["composite_box"] = [214.0, 420.0, 305.0, 480.0]
                d["projected_box"] = [214.0, 420.0, 305.0, 480.0]
                out.append("Z1 글 칸·합성 상자 결정값")
            if not d.get("mark_pt"):
                d["mark_pt"] = [299.5, 425.5]
    for ld in DET_["leaders"]:
        nm = ld.get("name", "")
        if d3 and nm.startswith("콜로세움 기초 절개") and _same(ld.get("pts"), [[275.0, 383.8], [275.0, 418.0]]):
            ld["pts"] = [[275.0, 383.8], [275.0, 420.0]]
        if d3 and nm.startswith("확대 창 Z1") and _same(ld.get("pts"), [[275.0, 482.0], [275.0, 505.0]]):
            ld["pts"] = [[275.0, 480.0], [275.0, 505.0]]
        m_ = ld.get("mark")
        if nm.startswith("확대 창 Z1"):
            ld["mark_pt_none"] = True            # Z1 → D 선의 A는 Z1·D 쪽 표지가 맡는다(선 시작점에는 찍지 않음)
        elif m_ in D4_LEADER_MARK_PT and not ld.get("mark_pt"):
            ld["mark_pt"] = list(D4_LEADER_MARK_PT[m_])
    if not _find_pair_marks(S_):
        S_.setdefault("detail", {})["pair_marks"] = json.loads(json.dumps(D4_PAIR_MARKS))
        out.append("숫자 짝 표지 1~4 결정값")
    lids = {l.get("id") for l in CM_["landmarks"]}
    for l in D4_LANDMARKS:
        if l["id"] not in lids:
            CM_["landmarks"].append(json.loads(json.dumps(l)))
            out.append("랜드마크 %s 결정값" % l["id"])
    pnames = [p["name"] for p in CM_["props"]]
    if not any(n.startswith("네로") for n in pnames):
        CM_["props"].append(json.loads(json.dumps(D4_COLOSSUS)))
        out.append("네로 거상 받침 결정값")
    for p in CM_["props"]:
        k = p["name"].split("(")[0].strip()
        if d3 and k in D4_PROP_CHANGES and _same(p.get("box"), D4_PROP_CHANGES[k][0]):
            p["box"] = list(D4_PROP_CHANGES[k][1])
            out.append("소품 %s 상자 → %s" % (k, p["box"]))
    v = CM_["background"][0]
    if d3 and _same(v.get("projected_box"), [330.0, 30.0, 388.0, 70.0]):
        v["projected_box"] = [360.0, 98.0, 418.0, 138.0]
        out.append("베수비오 상자 → [360,98,418,138]")
    for t in CM_.get("terrain", []):
        if d3 and t.get("name", "").startswith("알바노") and _same(t.get("box"), [300.0, 64.0, 420.0, 160.0]):
            t["box"] = [318.0, 122.0, 420.0, 162.0]
            t["ridge"] = {"cover_vesuvius_base_mm": [3.0, 5.0], "order": ["베수비오", "포도밭 농장", "알바노 구릉 능선"]}
            out.append("알바노 구릉 띠 → [318,122,420,162]")
    lh = (CM_.get("portus_geometry") or {}).get("lighthouse") or {}
    if d3 and _same(lh.get("plan_angle_deg"), 90.0) and _same(lh.get("plan_r"), 24.0):
        lh["plan_angle_deg"], lh["plan_r"] = 78.0, 22.0
        out.append("등대섬 평면 90°·24 → 78°·22.0")
    for c in (CM_.get("portus_geometry") or {}).get("canals") or []:
        if d3 and _same(c.get("plan_y"), [322.84, 338.6]):
            c["plan_y"] = [322.24, 340.10]
        if d3 and _same(c.get("plan_y"), [368.6, 384.0]):
            c["plan_y"] = [367.10, 384.60]
    if not any(r.get("id") == "R7" for r in CM_["roads"]):
        CM_["roads"].append(json.loads(json.dumps(D4_R7)))
        out.append("길 R7 결정값")
    sl = CM_["labels"]["slots"]
    skeys = {s["name"].split("(")[0].strip(): s for s in sl}
    for k, (old, new) in D4_SLOT_CHANGES.items():
        s = skeys.get(k)
        if s is not None and d3 and all(_same(s.get(kk), vv) for kk, vv in old.items()):
            s.update(json.loads(json.dumps(new)))
            out.append("라벨 %s 결정값" % k)
    for k, s in D4_SLOTS.items():
        kw = {"막센티우스 바실리카": "바실리카", "네로 거상": "거상", "마르켈루스 극장": "극장", "하드리아누스 영묘": "영묘"}[k]
        if not any(kw in kk for kk in skeys):
            sl.append(json.loads(json.dumps(s)))
            out.append("라벨 %s 결정값" % k)
    for f in CM_["labels"]["floor_text"]:
        nm = f.get("name", "")
        if d3 and nm.startswith("COLLI") and _same(f.get("anchor"), [344.0, 112.0]):
            f["anchor"], f["len"] = [380.0, 150.0], 28.0
            out.append("COLLI ALBANI anchor → (380,150)")
        if d3 and nm.startswith("OSTIA") and _same(f.get("anchor"), [176.0, 476.0]):
            f["anchor"], f["len"] = [214.0, 489.0], 22.0
            out.append("OSTIA anchor → (214,489)")
    return out


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
D5_Z1_LEAD = {"pts": [[232.0, 396.8], [272.38, 420.11]], "mark_pt": [233.75, 393.77]}           # D5: 공사장 거푸집 오른쪽 면(다져 넣은 층) ↘30° → Z1 원
D5_P5_STAIRS = [
    {"box": [312.0, 520.0, 340.7, 542.0], "body": ["2014 시장 모르타르:", "판 모양 결정→균열 억제", "2017 항구: 바닷물이", "새 광물을 키움"]},
    {"box": [342.65, 520.0, 371.35, 542.0], "body": ["2023 MIT: 실마리", "2025 폼페이 공사", "현장에서 확인:", "뜨거운 혼합·석회 알갱이"]},
    {"box": [373.3, 520.0, 402.0, 542.0], "body": ["제안·연구 단계:", "해안·항만 보호 구조물", "(큰 골재, 철근 없음)", "3D 프린팅 내구성"]}]
D5_P5_FIG = {"line": [[312.0, 545.0], [341.67, 545.0], [341.67, 543.5], [372.33, 543.5], [372.33, 542.0], [400.0, 542.0]],
             "arrow_tip": [402.0, 542.0], "lw": 0.35, "step_arrows": [[341.67, 522.6], [372.33, 522.6]], "step_arrow_w": 1.6}
D5_P5_CELLS = {"boxes": [[312.0, 547.0, 356.0, 562.5], [358.0, 547.0, 402.0, 562.5]], "title_baseline_y": 549.6,
               "body_baselines_y": [553.5, 557.4, 561.3], "divider": {"x": 357.0, "y": [548.0, 561.8]}}
D5_P2_CAP2 = ["반원 단면 터널 지붕", "(바실리카 측랑, 실선)"]
D5_P2_CAP3_1 = "두 터널이 직각 교차"
D5_P2_CAP3_2 = ["점선 복원: 바실리카 신랑", "(②의 신랑: 점선 복원)", "점선: 바실리카 신랑"]


def _d5_overlay(S_):
    """d5 결정값 채우기(값이 d4 그대로일 때만). 돌려줌: 바꾼 칸 기록(list)"""
    FR_, CM_, DET_ = S_["frame"], S_["core_map"], S_["detail"]
    out = []
    for ld in DET_.get("leaders", []):
        if _same(ld.get("pts"), [[275.0, 383.8], [275.0, 420.0]]):              # Z1 출발점: 받침 앞 변 기초 절개 → 공사장 거푸집 오른쪽 면
            ld["pts"] = json.loads(json.dumps(D5_Z1_LEAD["pts"]))
            ld["mark_pt"] = list(D5_Z1_LEAD["mark_pt"])
            ld["target"] = "공사장 거푸집 오른쪽 면(다져 넣은 층)"
            out.append("Z1 지시선 (232.0,396.8)→(272.38,420.11) ↘30°, A (233.75,393.77)")
    for d in DET_.get("map_elements", []):
        if d.get("id") == "Z1" and "기초 절개" in str(d.get("target", "")):
            d["target"] = "공사장 거푸집 오른쪽 면(다져 넣은 층)"
    pids = {p.get("id"): p for p in FR_["panels"]}
    p5 = pids.get("P5")
    if p5 and isinstance(p5.get("stairs"), list) and p5["stairs"] and _same(p5["stairs"][0].get("title_baseline_y"), 525.0) \
            and _same(p5["stairs"][0].get("body_baselines_y"), [528.9, 532.8, 536.7]):
        for st, nw in zip(p5["stairs"], D5_P5_STAIRS):
            st["box"] = list(nw["box"])
            st["title_baseline_y"] = 524.0
            st["body"] = list(nw["body"])
            st["body_baselines_y"] = [528.0, 531.9, 535.8, 539.7]
        p5["stair_figure"] = dict(p5.get("stair_figure") or {}, **json.loads(json.dumps(D5_P5_FIG)))
        for c, bx in zip(p5.get("cells") or [], D5_P5_CELLS["boxes"]):
            c["box"] = list(bx)
            c["title_baseline_y"] = D5_P5_CELLS["title_baseline_y"]
            c["body_baselines_y"] = list(D5_P5_CELLS["body_baselines_y"])
        ct = p5.get("cell_text") if isinstance(p5.get("cell_text"), dict) else {}
        ct["divider"] = dict(D5_P5_CELLS["divider"])
        p5["cell_text"] = ct
        out.append("P5 계단 꺾은선·칸 이름 524.0·본문 528.0~539.7·두 칸 549.6/553.5~561.3·가름선 x 357(결정 D15)")
    p2 = pids.get("P2")
    if p2:
        hd = p2.get("head") or {}
        if _same(hd.get("en_baseline_y"), 29.0):
            hd["en_baseline_y"] = 29.8
            out.append("P2 머리글 영문 기준선 29.0 → 29.8(결정 D16)")
        cells = p2.get("cells") or []
        if len(cells) >= 3 and _same(cells[1].get("caption"), ["터널 지붕(점선 =", "무너진 신랑 볼트 복원)"]):
            cells[1]["caption"] = list(D5_P2_CAP2)
            out.append("P2 ② 캡션 → 현존 배럴 볼트만(결정 D16)")
        if len(cells) >= 3 and _same(cells[2].get("caption"), ["두 터널 지붕이", "직각으로 만난다"]):
            c2 = next((c for c in D5_P2_CAP3_2 if twf(c, "m", 2.1) <= 23.0 + 1e-6), D5_P2_CAP3_2[-1])
            cells[2]["caption"] = [D5_P2_CAP3_1, c2]
            out.append("P2 ③ 캡션 → '%s / %s'(23.0mm 안 첫 후보)" % (D5_P2_CAP3_1, c2))
    for r in CM_.get("roads", []):
        if r.get("id") == "R7":
            pts = r.get("plan_pts") or []
            if pts and len(pts) >= 2:
                k = 0 if pts[0][1] < pts[-1][1] else len(pts) - 1
                if abs(pts[k][0] - 489.6) < 0.6 and pts[k][1] > 250.9:
                    pts[k] = [489.6, 250.4]
                    out.append("R7 북쪽 끝 → (489.6, 250.4)(광장 판석까지, 결정 D3·D7)")
    return out


D4_NOTES = _d4_overlay(S)
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
VES = CM["background"][0]
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
REPORT = {"objects": {}, "labels": {}, "notes": (["d3 사양 → d4 결정값 보정(워커 단독 확인용): " + " · ".join(D4_NOTES)] if D4_NOTES else [])}
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
H_PERSON = 5.0
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


def road_bands(r):
    """사양 길(plan_pts 꺾은선) → 화면 띠 다각형 목록. 다른 길과 끝점을 공유하는 끝만 반폭만큼 이어 모서리를 메운다."""
    pts = [tuple(p) for p in r["plan_pts"]]
    w = r["w_screen_perp_mm"]
    hw = w / (2.0 * C30)
    ends = []
    for q in CM["roads"]:
        if q is r:
            continue
        ends += [tuple(q["plan_pts"][0]), tuple(q["plan_pts"][-1])]

    def joint(p):
        return hw if any(math.hypot(p[0] - e[0], p[1] - e[1]) < 0.6 for e in ends) else 0.0
    out = []
    n = len(pts)
    for i in range(n - 1):
        e0 = joint(pts[0]) if i == 0 else hw
        e1 = joint(pts[-1]) if i == n - 2 else hw
        out.append(plan_band(pts[i], pts[i + 1], w, e0, e1))
    return out


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


D5_NOTES = _d5_overlay(S)                                            # d5 결정값(사양이 d4 값 그대로일 때만, twf 정의 뒤)
if D5_NOTES:
    REPORT["notes"].append("d4 사양 → d5 결정값 보정(워커 단독 확인용): " + " · ".join(D5_NOTES))


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
CO_BOX = tuple(_hv(HCOL, ("screen_box", "building_box", "projected_box"), [192.6, 226.4, 300.4, 330.1]))
CO_SEAT = ((238.0, 360.0), (0.0, 48.0))                                                        # 계단석 구역(나머지는 방사벽 + 짙은 빈칸)
CO_ST = [dict(z0=0.0, z1=11.5, ob=0.0, sp=5.5, ent=1.45, order="T"), dict(z0=11.5, z1=24.5, ob=12.7, sp=18.2, ent=1.45, order="I"),
         dict(z0=24.5, z1=37.0, ob=25.7, sp=30.9, ent=1.45, order="C"), dict(z0=37.0, z1=53.0, ob=None, sp=None, ent=1.3, order="A")]
_HYS = sget(HCOL, "hypogeum", default=None) or {}
HY = {"rings": _hv(_HYS, ("concentric", "rings", "concentric_fr"), [0.86, 0.72, 0.58, 0.44, 0.30]),
      "corr": float(_hv(_HYS, ("corridor_half_w", "corridor_half", "corridor"), 0.9)),
      "every": float(_hv(_HYS, ("partition_every_deg", "every_deg", "partition_deg"), 12.0)),
      "r_frac": _hv(_HYS, ("partition_r_frac", "r_frac", "partition_r"), [0.33, 0.97]),
      "t_ring": 0.55, "t_corr": 0.5, "t_part": 0.45, "z_top": CO_ZF - 0.15}
CX_S, CY_S = sp(*CO_C)                                                                         # 화면 (246.54, 304.2)
WS_SPEC = sget(HERO, "worksite", default=None) or sget(HLS, "worksite", default=None) or \
    {"name": "콜로세움 기초 공사장(복원 장면)", "box": [208.0, 386.0, 250.0, 410.0]}                 # 결정 D5: 공사장 상자 [208, 386, 250, 410] 유지
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
    return (CX_S + KU * u, CY_S + KV * v - z)


def uvz(u, v, z=0.0):
    return (CX_S + KU * u, CY_S + KV * v - z)


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


def rb(th):
    """조경(광장 판석) 경계 반지름(평면 방위 th°): roma_pkg_hero.rb와 같다(79.5~89.5)"""
    t = math.radians(th)
    return 84.5 + 3.0 * math.sin(3 * t + 0.7) + 1.5 * math.sin(7 * t + 0.2) + 1.0 * (_hash01(int(th * 10), 7) - 0.5)


def ls_pt(r, th):
    """조경 중심 기준 평면 반지름 r, 방위 th → 화면 점"""
    t = math.radians(th)
    return sp(LS_C[0] + r * math.cos(t), LS_C[1] + r * math.sin(t))


def _plaza_obstacles():
    """광장 경계를 줄일 장애물(화면 다각형): 다른 랜드마크 상자(L5는 1.04배), 수도교 띠, 소품 상자, Detail·패널. 길은 접속이라 뺀다"""
    obs = []
    for l in CM["landmarks"]:
        if l["id"] == "L4":
            continue
        b = list(l["projected_box"])
        if l["id"] == "L5":
            b = list(metella_box())
        obs.append(("랜드마크 " + l["id"], box_poly(b)))
    (x0s, y0s), (x1s, y1s) = CM["aqueduct"]["ground_line_screen"]
    Hq = CM["aqueduct"]["arch_height_mm"]
    obs.append(("수도교 띠", [(x0s, y0s - Hq - 1), (x1s, y1s - Hq - 1), (x1s, y1s + 2), (x0s, y0s + 2)]))
    for p in CM["props"]:
        nm = p["name"]
        if nm.startswith("재료 수레") or nm.startswith("아피아 가도 수레") or nm.startswith("네로"):
            continue
        obs.append(("소품 " + nm.split("(")[0], box_poly(p["box"])))
    for d in DET["map_elements"]:
        if d.get("box"):
            obs.append(("Detail " + d["id"], box_poly(d["box"])))
    obs.append(("Z1 글 칸", box_poly(z1_text_box())))
    obs.append(("Z1 원", [(DMAP["Z1"]["circle"]["c"][0] + DMAP["Z1"]["circle"]["d"] / 2.0 * math.cos(math.radians(t)),
                         DMAP["Z1"]["circle"]["c"][1] + DMAP["Z1"]["circle"]["d"] / 2.0 * math.sin(math.radians(t))) for t in range(0, 360, 10)]))
    return obs


def plaza_poly(step=1.0, clear=2.2):
    """광장 판석 외곽(화면 다각형, 받침·옆면 0): rb(θ)에서 시작해 장애물과 clear mm 이상 떨어지게 줄인다. 돌려줌: (다각형, 줄인 기록)"""
    obs = _plaza_obstacles()
    pts, trims, rs = [], [], []
    n = int(round(360.0 / step))
    for k in range(n):
        th = k * step
        r0 = rb(th)
        r = r0
        while r > 60.0:
            q = ls_pt(r, th)
            if all(not in_poly(q, pg) and _pt_poly_gap(q, pg) >= clear for _nm, pg in obs):
                break
            r -= 0.25
        if r < r0 - 0.01:
            trims.append((th, round(r0, 2), round(r, 2)))
        pts.append(ls_pt(r, th))
        rs.append(r)
    GEO["plaza_r"] = rs
    GEO["plaza_step"] = step
    return pts, trims


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
    a = FLOOR["TIBERIS"]["anchor"]
    Yb = RIV_Y + 1.6
    Xs = a[0] / C30 + Yb
    ax, ay = sp(Xs, Yb)
    out.append(dict(name="TIBERIS 테베레강", M=M_FLOOR_SE, ax=ax, ay=ay, parts=[("TIBERIS", "en", 3.3, INK_WATER), ("테베레강", "b", 3.1, INK_WATER)]))
    # MARE TYRRHENUM 티레니아해: 두 줄 — 왼쪽 아래 열린 바다
    a = FLOOR["MARE"]["anchor"]
    ax, ay = a[0], a[1]
    out.append(dict(name="MARE TYRRHENUM", M=M_FLOOR_SE, ax=ax, ay=ay, parts=[("MARE TYRRHENUM", "en", 3.3, INK_WATER)]))
    q = map_pt(M_FLOOR_SE, ax, ay, 0.0, 5.2)
    out.append(dict(name="티레니아해", M=M_FLOOR_SE, ax=q[0], ay=q[1], parts=[("티레니아해", "b", 3.1, INK_WATER)]))
    # VIA APPIA: 위 차선 안, ↗ 바닥 글
    ap = [r for r in CM["roads"] if r["id"] == "R1"][0]
    Xc = ap["plan_pts"][0][0]
    Xb = Xc - 1.5
    a = FLOOR["VIA"]["anchor"]
    Ys = Xb - a[0] / C30
    ax, ay = sp(Xb, Ys)
    out.append(dict(name="VIA APPIA 아피아 가도 → 캄파니아", M=M_FLOOR_NE, ax=ax, ay=ay,
                    parts=[("VIA APPIA", "en", 3.1, (98, 78, 50)), ("아피아 가도 → 캄파니아", "b", 2.8, (98, 78, 50))]))
    # COLLI ALBANI 알바노 구릉: 두 줄
    a = FLOOR["COLLI"]["anchor"]
    out.append(dict(name="COLLI ALBANI", M=M_FLOOR_SE, ax=a[0], ay=a[1], parts=[("COLLI ALBANI", "en", 2.9, (96, 92, 58))]))
    q = map_pt(M_FLOOR_SE, a[0], a[1], 0.0, 4.4)
    out.append(dict(name="알바노 구릉", M=M_FLOOR_SE, ax=q[0], ay=q[1], parts=[("알바노 구릉 — 로마 건물의 화산재", "b", 2.45, (96, 92, 58))]))
    # OSTIA 오스티아
    a = FLOOR["OSTIA"]["anchor"]
    out.append(dict(name="OSTIA 오스티아", M=M_FLOOR_SE, ax=a[0], ay=a[1], parts=[("OSTIA", "en", 3.0, (104, 84, 56)), ("오스티아", "b", 2.8, (104, 84, 56))]))
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
    lk = BAS["process_representation"]["link"]
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
    ex_poly(col_sil_approx(), 1.5)                                   # d5: 받침 0 — 콜로세움 실루엣만 먼저 막는다(광장은 그린 뒤 등록, 둘레 집이 바로 맞닿게)
    ex_rect(WS_SPEC["box"], 1.5)
    for p in CM["props"]:
        if p["name"].startswith("포도밭 농장") or p["name"].startswith("네로"):
            continue                                    # 농장은 지형 층에서 직접 그린다(밭 배치가 피한다). 거상은 실루엣 + 2mm로 막는다
        ex_rect(p["box"], 1.0)
    for f in FLOORS:
        ex_poly(f["poly"], 1.0)
    for d in DET["map_elements"]:
        if d["kind"] == "확대 창":
            ex_circle(d["circle"]["c"], d["circle"]["d"] / 2.0, 2.0)
        else:
            ex_rect(d["box"], 1.6)
    ex_rect(z1_text_box(), 0.8)                          # 확대 창 Z1 글 칸(사양 text_box)
    for pid, pn in PANEL.items():
        ex_rect(pn["rect"], 2.0)
    for _nm, pts, _l, _k in detail_leaders():
        ex_line(pts, 2.6)
    for r in CM["roads"]:
        for b in road_bands(r):
            ex_poly(b, 0.9)
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
    m = stage_mask(k)
    sc_ = sea_corner()
    if sc_:
        ImageDraw.Draw(m).polygon([(x * k, y * k) for x, y in sc_], fill=0)
    return m


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


def texture(L, kind, X0, Y0, X1, Y1, key, far=False):
    """밭 한 구획. far = 대기 원근(바탕색 50% 혼합)"""
    rng = local_rng(key)

    def c(v):
        return mix(v, BG, 0.5) if far else v
    base = c(FIELD_BASE[kind])
    poly = [sp(X0, Y0), sp(X1, Y0), sp(X1, Y1), sp(X0, Y1)]
    L.poly(poly, fill=base, outline=shade(base, 0.86 if far else 0.82), lw=0.16 if far else 0.2)
    if kind == "wheat":
        Y = Y0 + 1.5
        while Y < Y1 - 0.7:
            L.line([sp(X0 + 0.7, Y), sp(X1 - 0.7, Y)], shade(base, 0.88 if far else 0.86), 0.16, joint=False)
            Y += 1.8
    elif kind == "vine":
        X = X0 + 1.3
        while X < X1 - 0.7:
            L.line([sp(X, Y0 + 0.8), sp(X, Y1 - 0.8)], c(VINE_C), 0.34 if far else 0.42, joint=False)
            if not far:
                L.line([sp(X + 0.5, Y0 + 0.8), sp(X + 0.5, Y1 - 0.8)], (162, 174, 106), 0.14, joint=False)
            X += 2.2
    elif kind == "pasture":
        for _ in range(int((X1 - X0) * (Y1 - Y0) / 26.0) + 1):
            x, y = sp(X0 + 1 + rng.random() * (X1 - X0 - 2), Y0 + 1 + rng.random() * (Y1 - Y0 - 2))
            L.ell(x, y, 0.5, 0.3, fill=c((170, 180, 112)))
    elif kind == "fallow":
        Y = Y0 + 2.2
        while Y < Y1 - 1:
            L.line([sp(X0 + 1, Y), sp(X1 - 1, Y)], c((200, 180, 136)), 0.16, joint=False)
            Y += 2.8
    return poly


def place_fields(L, region, Xr, Yr, size, kinds, key, gap=1.1, far=False):
    rx0, ry0, rx1, ry1 = region
    sx, sy = size
    n = 0
    i = 0
    X = Xr[0]
    while X < Xr[1]:
        Y = Yr[0]
        j = 0
        while Y < Yr[1]:
            X0, Y0, X1, Y1 = X + gap / 2, Y + gap / 2, X + sx - gap / 2, Y + sy - gap / 2
            poly = [sp(X0, Y0), sp(X1, Y0), sp(X1, Y1), sp(X0, Y1)]
            cx = sum(p[0] for p in poly) / 4.0
            cy = sum(p[1] for p in poly) / 4.0
            if rx0 <= cx <= rx1 and ry0 <= cy <= ry1:
                if poly_in_stage(poly, 0.3) and poly_free(poly, 0.2, stage=False):
                    kind = kinds[int(h01(key, i, j) * len(kinds)) % len(kinds)]
                    texture(L, kind, X0, Y0, X1, Y1, "%s%d_%d" % (key, i, j), far=far)
                    ex_poly(poly, 0.2)
                    n += 1
            Y += sy
            j += 1
        X += sx
        i += 1
    return n


def draw_fields():
    """밭·포도밭(지형 층). d4: 무대 확장 해제 — 오른쪽 위·하단 오른쪽(옛 R·T 자리)에는 밭을 두지 않는다(종이/띠 바탕)."""
    G = Layer(0, 0, PW, PH)
    n0 = 0
    n1 = place_fields(G, (290, 392, 430, 505), (540, 835), (130, 405), (15.0, 11.0),
                      ["vine", "vine", "vine", "wheat", "pasture", "vine", "fallow"], "남동밭")
    n2 = place_fields(G, (372, 206, 430, 252), (428, 466), (-31, 34), (13.0, 10.0), ["pasture", "wheat", "fallow", "vine"], "가도밭")
    n3 = place_fields(G, (-20, 322, 66, 372), (300, 430), (324.5, 352), (17.0, 11.0), ["wheat", "wheat", "pasture", "fallow"], "곡식밭")
    n4 = place_fields(G, (150, 425, 252, 505), (548, 660), (300, 380), (13.0, 10.0), ["pasture", "wheat", "fallow", "vine"], "하구밭")
    n5 = place_fields(G, (88, 362, 206, 470), (452, 524), (324.5, 380), (13.0, 10.0), ["wheat", "pasture", "wheat", "fallow"], "포르투스띠")
    G.img.putalpha(ImageChops.multiply(G.img.getchannel("A"), land_mask(KD)))
    P.paste(G)
    REPORT["notes"].append("밭 구획: 먼 밭(옛 R 자리) %d · 남동 교외 %d · 가도 옆 %d · 강 오른쪽 둑 곡식밭 %d · 하구 동쪽 %d · 포르투스 띠 %d"
                           % (n0, n1, n2, n3, n4, n5))


def albano_box():
    for t in CM.get("terrain", []):
        if t["name"].startswith("알바노"):
            return tuple(t["box"])
    return (318.0, 122.0, 420.0, 162.0)


def aq_top_y(x):
    """수도교 윗선(화면 y): 기초선 − 높이 − 위 단 돌출(1.0). 수도교 왼쪽 끝보다 왼쪽이면 None"""
    (x0s, y0s), (x1s, y1s) = CM["aqueduct"]["ground_line_screen"]
    if x < x0s - 0.5:
        return None
    return y0s + (x - x0s) * (y1s - y0s) / (x1s - x0s) - CM["aqueduct"]["arch_height_mm"] - 1.0


def albano_ridge_cfg():
    for t in CM.get("terrain", []):
        if t["name"].startswith("알바노"):
            return t.get("ridge") or {}
    return {}


def ves_front_contour():
    """베수비오 밑동 윤곽(바닥 고리 앞쪽 반): x → 가장 아래 y"""
    v = GEO.get("ves")
    if not v:
        return None
    m, allp, ox, oy, sc, zs, bb, hull = v
    fr = ZIso(P, ox, oy, sc, zs)
    ring0 = [fr.p(*q) for q in allp[:24]]
    pts = sorted(ring0)

    def yb(x):
        best = None
        n = len(ring0)
        for i in range(n):
            (x1, y1), (x2, y2) = ring0[i], ring0[(i + 1) % n]
            if (x1 - x) * (x2 - x) <= 0 and x1 != x2:
                y = y1 + (y2 - y1) * (x - x1) / (x2 - x1)
                best = y if best is None else max(best, y)
        return best
    return yb


def draw_albano():
    """알바노 구릉 띠(화산 그림이 아니라 낮은 구릉 지면 결). d4: 산 → 농장 → 구릉 순으로 그린다.
    - 앞 능선 하나가 베수비오 밑동 앞쪽 윤곽(사양 상자 x 전체)을 3~5mm 연속으로 가린다(가운데만 고정값으로 내리던 처리 없음).
    - 농장 밭 아래쪽은 같은 능선 실루엣이 포도밭 결로 이어 받아, 산기슭의 닫힌 윤곽을 끊는다(농장 지면 + 앞 구릉 = 한 지형).
    - 아래 변은 수도교 윗선과 2.2mm, 라벨 블록과는 2.4mm(세로) 띄운다."""
    bx0, by0, bx1, by1 = albano_box()
    rc = albano_ridge_cfg()
    cov = rc.get("cover_vesuvius_base_mm") or [3.0, 5.0]
    c_lo, c_hi = float(cov[0]), float(cov[1])
    c_mid, c_amp = (c_lo + c_hi) / 2.0, (c_hi - c_lo) * 0.28
    yb = ves_front_contour()
    vx0, vy0, vx1, vy1 = VES["projected_box"]
    bath = LM["L3"]["projected_box"]
    xa = max(bx0, bath[2] + 1.5)
    xb = min(PW + 2.0, bx1 + 2.0)
    xs = [xa + 0.5 * i for i in range(int((xb - xa) / 0.5) + 1)]

    def ridge_raw(x):
        if yb is not None and vx0 + 0.4 <= x <= vx1 - 0.4:
            v = yb(x)
            if v is not None:
                return v - (c_mid + c_amp * math.sin(x * 0.31))
        return None
    raw = {x: ridge_raw(x) for x in xs}
    inside = [x for x in xs if raw[x] is not None]
    xl, xr = (min(inside), max(inside)) if inside else (vx0, vx1)
    tl, tr = raw.get(xl), raw.get(xr)
    top = {}
    for x in xs:
        if raw[x] is not None:
            top[x] = raw[x]
        elif x < xl:
            top[x] = (tl if tl is not None else by0) + (xl - x) * 0.30 + 0.5 * math.sin(x * 0.45)
        else:
            top[x] = (tr if tr is not None else by0) + (x - xr) * 0.30
    pushed = []
    for _n, pg in LABEL_POLYS:                                       # 라벨 블록 아래로 세로 2.4mm(수직 거리 2mm)
        if _n.startswith("바닥 글"):
            continue
        e = bbox_of(pg)
        for x in xs:
            if e[0] - 2.4 <= x <= e[2] + 2.4:
                ys_ = [poly_y_at(pg, xx, "bottom") for xx in (max(e[0], x - 2.4), min(e[2], x + 2.4), min(max(x, e[0]), e[2]))]
                ys_ = [v for v in ys_ if v is not None]
                if ys_ and max(ys_) + 2.4 > top[x] and e[1] < by1:
                    top[x] = max(ys_) + 2.4
                    pushed.append(x)

    def bot(x):
        b_ = by1
        at = aq_top_y(x)
        if at is not None:
            b_ = min(b_, at - 2.2)
        return b_
    for x in xs:                                                     # 왼쪽 끝은 능선이 아래 변으로 내려와 뾰족하게 닫힌다(수직 잘림 없음)
        f_ = max(0.0, 1.0 - (x - xa) / 12.0)
        if f_ > 0:
            top[x] = top[x] + (bot(x) - 0.4 - top[x]) * f_ * f_
    pts_top = [(x, top[x]) for x in xs if bot(x) > top[x] + 0.3]
    if len(pts_top) < 3:
        return
    xs_ok = [p_[0] for p_ in pts_top]
    poly = pts_top + [(x, bot(x)) for x in reversed(xs_ok)]
    sub = Layer(xa - 2, min(top.values()) - 2, min(PW, xb) + 2, by1 + 2)
    col = mix((150, 160, 104), GROUND, 0.46)
    sub.poly(poly, fill=col)
    facet_fill(sub, poly, col, cell=6.5, amp=0.035, key="알바노면", jit=0.14)
    for off, a_ in ((6.0, 92), (13.5, 80), (21.0, 66)):              # 안쪽 능선(그늘 + 빛 한 쌍): 낮은 구릉이 겹쳐 이어진다
        ln = [(x, top[x] + off + 1.4 * math.sin(x * 0.13 + off)) for x in xs_ok if top[x] + off + 1.6 < bot(x)]
        if len(ln) > 3:
            soft_line(sub, ln, shade(col, 0.70), alpha=a_, w=0.7, blur=0.45)
            soft_line(sub, [(x, y - 0.8) for x, y in ln], (250, 246, 222), alpha=70, w=0.45, blur=0.3)
    soft_line(sub, pts_top, (250, 246, 220), alpha=95, w=0.5, blur=0.25)   # 능선 윗선 빛
    fp = GEO.get("farm_xr")
    n_v = 0
    if fp:                                                           # 농장 밭이 능선으로 이어지는 포도밭 결
        for k_ in range(1, 4):
            ln = [(x, top[x] + 1.25 * k_) for x in xs_ok if fp[0] + 1.0 <= x <= fp[1] - 1.0 and top[x] + 1.25 * k_ < bot(x) - 0.8]
            if len(ln) > 3:
                sub.line(ln, mix(VINE_C, BG, 0.25), 0.36)
                n_v += 1
    olives = 0
    for i in range(30):
        x = xa + 4 + h01("알바노올리브", i) * (min(PW, xb) - xa - 8)
        if x not in top and xs_ok:
            xx = min(xs_ok, key=lambda q: abs(q - x))
        else:
            xx = x
        if xx not in top:
            continue
        y = top[xx] + 6.0 + h01("알바노올리브y", i) * max(0.0, bot(xx) - top[xx] - 9.0)
        q = [(x - 1, y - 0.7), (x + 1, y - 0.7), (x + 1, y + 0.7), (x - 1, y + 0.7)]
        if y < bot(xx) - 1.5 and poly_free(q, 0.3, stage=True) and in_poly((x, y), poly):
            sub.ell(x, y, 0.9, 0.6, fill=(112, 136, 84))
            olives += 1
    m = Image.new("L", (sub.w, sub.h), 0)                             # 무대 밖(위 띠)으로 넘치지 않게
    ImageDraw.Draw(m).rectangle([sub.X(STAGE[0]), sub.Y(STAGE[1]), sub.X(STAGE[2]), sub.Y(STAGE[3])], fill=255)
    sub.img.putalpha(ImageChops.multiply(sub.img.getchannel("A"), m))
    merge(P, sub, opacity=1.0, blur=0.0)
    ex_poly(poly, 0.2)
    covers = [round(yb(x) - top[x], 2) for x in inside if yb(x) is not None and x not in pushed]
    if covers:
        GEO["ves_cover_mm"] = [min(covers), max(covers)]
    GEO["albano_poly"] = poly
    REPORT["notes"].append("알바노 구릉(d4): 앞 능선 1개가 베수비오 밑동 x %.1f~%.1f를 %s mm 가림(라벨 밑으로 내린 칸 %d), 포도밭 결 %d줄, 올리브 %d, 아래 변 = min(띠 아래 변, 수도교 윗선 − 2.2)"
                           % (xl, xr, GEO.get("ves_cover_mm"), len(set(pushed)), n_v, olives))


# ───────────────────────── 2 강·바다·해안 ─────────────────────────
def draw_river():
    poly = [tuple(p) for p in RV["polygon_screen"]]
    n = len(poly) // 2
    left, right = poly[:n], poly[n:][::-1]
    P.poly(poly, fill=RIV_C)
    facet_fill(P, poly, RIV_C, cell=6.0, amp=0.05, key="강", jit=0.12)
    walls = []
    for side in (left, right):
        for i in range(len(side) - 1):
            p0, p1 = side[i], side[i + 1]
            if abs(p1[0] - p0[0]) < 0.05:
                continue
            mx, my = (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0
            if in_poly((mx, my + 0.8), poly):
                P.poly([p0, p1, (p1[0], p1[1] + 2.2), (p0[0], p0[1] + 2.2)], fill=(150, 124, 88))
                walls.append((p0, p1))
    for (p0, p1) in walls:
        P.line([(p0[0], p0[1] + 2.2), (p1[0], p1[1] + 2.2)], (96, 140, 180), 0.25, joint=False)
    for edge in (left, right):
        soft_line(P, edge, (40, 30, 20), alpha=55, w=0.8, blur=0.4)
        P.line(edge, (214, 200, 170), 0.45)
    GEO["river_poly"] = poly
    GEO["river_left"], GEO["river_right"] = left, right


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
        xb = min((505.0 - COAST_B - off) / T30, xa + 62.0)
        if xb > xa + 8:
            P.line([(xa, COAST_B + off + T30 * xa), (xb, COAST_B + off + T30 * xb)], (176, 204, 224), 0.3, joint=False)


MOUTH_X = (C30 * (RIV_XB - RIV_HW2 - COAST_B), C30 * (RIV_XB + RIV_HW2 - COAST_B))     # 하구가 해안선을 지나는 x 범위
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
def road_edges(bands, rid):
    """길 rid의 가장자리선(띠의 긴 변 2줄). 다른 길 띠의 안쪽(0.25mm 안으로 줄인 영역)에 든 부분은 지운다.
    T자(R2–R3)·L자(R2–R5, R6a–R6b)·갈림목(R1–R6a)에서 포장 위를 가로지르는 선을 없앤다(통합 d3, map 요청)."""
    polys = bands[rid]
    xs = [p[0] for pg in polys for p in pg]
    ys = [p[1] for pg in polys for p in pg]
    L = Layer(math.floor(min(xs)) - 1, math.floor(min(ys)) - 1, math.ceil(max(xs)) + 1, math.ceil(max(ys)) + 1)
    for poly in polys:
        L.line([poly[0], poly[1]], ROAD_EDGE, 0.3, joint=False)
        L.line([poly[3], poly[2]], ROAD_EDGE, 0.3, joint=False)
    m = Image.new("L", L.img.size, 0)
    md = ImageDraw.Draw(m)
    for oid, ops in bands.items():
        if oid == rid:
            continue
        for pg in ops:
            md.polygon([L.P(p) for p in pg], fill=255)
    m = m.filter(ImageFilter.MinFilter(2 * int(round(0.25 * KD)) + 1))
    L.img.putalpha(ImageChops.subtract(L.img.getchannel("A"), m))
    P.paste(L)


def draw_roads():
    """사양 길(plan_pts)만 그린다. 연장은 사양 좌표에 들어 있다(렌더 하드코딩 없음). 가장자리선 2줄."""
    bands = {}
    for r in CM["roads"]:
        bands[r["id"]] = road_bands(r)
        col = APPIA_C if r.get("center_line") else ROAD_C
        for poly in bands[r["id"]]:
            P.poly(poly, fill=col)
    for r in CM["roads"]:                                # 가장자리선은 모든 길을 칠한 다음(이음 모서리가 덮이지 않게)
        road_edges(bands, r["id"])
        if r.get("center_line"):
            pts = [tuple(p) for p in r["plan_pts"]]
            for p0, p1 in zip(pts[:-1], pts[1:]):
                P.dashed(sp(*p0), sp(*p1), (250, 246, 236), 1.0, 4.0, 2.6)
                rng = local_rng("포석")
                hw = r["w_screen_perp_mm"] / (2.0 * C30) - 1.6
                dx, dy = p1[0] - p0[0], p1[1] - p0[1]
                Ls = math.hypot(dx, dy)
                nx, ny = -dy / Ls, dx / Ls
                for i in range(int(Ls)):                 # 현무암 포석 결
                    t = rng.random()
                    off = (rng.random() * 2 - 1) * hw
                    x, y = sp(p0[0] + dx * t + nx * off, p0[1] + dy * t + ny * off)
                    P.ell(x, y, 0.35, 0.22, fill=(170, 150, 112))
        GEO["road_" + r["id"]] = bands[r["id"]][0]
        DRAWN["roads"].append({"id": r["id"], "name": r.get("name", r["id"]), "polys": [[[round(x, 2), round(y, 2)] for x, y in pg] for pg in bands[r["id"]]]})


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
def try_mesh(m, pad=0.5, draw=True):
    pts = [ISO.p(*p) for p in mesh_pts(m)]
    bb = bbox_of(pts)
    poly = box_poly(bb)
    if not poly_free(poly, pad):
        return False
    if draw:
        m.draw(ISO, lw=0.10)
    ex_poly(poly, 0.3)
    return True


def try_mesh_hull(m, pad=0.3, draw=True):
    """try_mesh와 같되 사각 외곽 대신 투영 볼록 껍질로 빈 자리를 본다(광장 경계에 집을 바짝 붙인다)"""
    pts = [ISO.p(*p) for p in mesh_pts(m)]
    hull = _hull(pts)
    if len(hull) < 3 or not poly_free(hull, pad):
        return False
    if draw:
        m.draw(ISO, lw=0.10)
    ex_poly(hull, 0.3)
    return True


def draw_scatter():
    rng = local_rng("지붕")
    placed = {"집": 0, "올리브": 0, "사이프러스": 0, "소나무": 0}
    cands = []
    # (영역 화면 상자, 간격, 종류 비율)
    regions = [((116, 138, 178, 196), 9.0, "house"), ((158, 156, 236, 218), 8.6, "house"), ((224, 190, 272, 214), 8.4, "house"),
               ((314, 224, 354, 274), 8.6, "house"), ((112, 278, 150, 302), 8.0, "mix"), ((114, 294, 150, 334), 8.0, "mix"),
               ((112, 190, 228, 238), 6.4, "olive"), ((0, 96, 18, 300), 7.0, "tree"), ((18, 182, 116, 198), 6.0, "cyp"),
               ((40, 290, 92, 336), 7.0, "tree"), ((146, 452, 236, 503), 7.0, "pine"), ((150, 226, 236, 262), 6.5, "olive"),
               ((296, 300, 356, 340), 7.5, "tree"), ((330, 386, 420, 505), 9.5, "cyp"), ((0, 290, 40, 326), 7.5, "tree"),
               ((178, 136, 224, 150), 8.0, "house")]
    for (box, step, kind) in regions:
        x0, y0, x1, y1 = box
        y = y0 + 3.0
        row = 0
        while y < y1:
            x = x0 + (step / 2.0 if row % 2 else 0.0) + 2.0
            while x < x1:
                cands.append((y + rng.random() * 0.8, x + (rng.random() - 0.5) * 1.6, kind))
                x += step
            y += step * 0.72
            row += 1
    cands.sort()
    for (y, x, kind) in cands:
        X, Y = to_plan(x, y)
        r = rng.random()
        if kind == "house" or (kind == "mix" and r < 0.45):
            w = 5.2 + rng.random() * 2.4
            d = 4.2 + rng.random() * 2.0
            hw = 3.4 + rng.random() * 2.4
            wall = (232 - int(rng.random() * 18), 212 - int(rng.random() * 18), 180 - int(rng.random() * 16))
            m = m_house(X - w / 2, Y - d / 2, X + w / 2, Y + d / 2, 0, hw, 1.9, wall, ROOF if rng.random() < 0.8 else (176, 84, 58),
                        axis="X" if rng.random() < 0.5 else "Y")
            if try_mesh(m, 0.35):
                placed["집"] += 1
                continue
            kind = "olive"
        if kind in ("olive", "mix", "tree") and (kind != "tree" or r < 0.6):
            m = m_olive(X, Y, 0, 6.0 + rng.random() * 1.6, 2.2 + rng.random() * 0.6, key="올리브%.1f%.1f" % (x, y))
            if try_mesh(m, 0.3):
                placed["올리브"] += 1
            continue
        if kind in ("cyp", "tree"):
            m = m_cypress(X, Y, 0, 9.0 + rng.random() * 3.0, 1.5, key="사이프러스%.1f%.1f" % (x, y))
            if try_mesh(m, 0.3):
                placed["사이프러스"] += 1
            continue
        if kind == "pine":
            m = m_pine(X, Y, 0, 9.0 + rng.random() * 2.0, 3.6 + rng.random() * 0.8, key="소나무%.1f%.1f" % (x, y))
            if try_mesh(m, 0.3):
                placed["소나무"] += 1
    # d5: 조경 경계 바로 밖 첫 집 줄(승인 설계 '둘레 시내 지붕과 나무', 결정 D14: 경계 ↔ 첫 집 줄 빈 띠 ≤ 3mm 평면)
    rr_ = GEO.get("plaza_r")
    ring = {"집": 0, "나무": 0, "빈 띠(평면 mm)": []}
    if rr_:
        stp = GEO.get("plaza_step", 1.0)
        th = 0.0
        while th < 360.0:
            k = int(round(th / stp)) % len(rr_)
            r_e = rr_[k]
            w = 5.2 + rng.random() * 2.4
            d = 4.2 + rng.random() * 2.0
            hw = 3.4 + rng.random() * 2.4
            placed_ = False
            for extra in (0.0, 1.0, 2.0, 3.2, 8.0, 9.4):
                rc = r_e + 0.8 + extra + max(w, d) / 2.0
                t_ = math.radians(th)
                X, Y = LS_C[0] + rc * math.cos(t_), LS_C[1] + rc * math.sin(t_)
                if rng.random() < 0.82:
                    wall = (232 - int(rng.random() * 18), 212 - int(rng.random() * 18), 180 - int(rng.random() * 16))
                    m = m_house(X - w / 2, Y - d / 2, X + w / 2, Y + d / 2, 0, hw, 1.9, wall, ROOF if rng.random() < 0.8 else (176, 84, 58),
                                axis="X" if rng.random() < 0.5 else "Y")
                    kind_ = "집"
                else:
                    m = m_olive(X, Y, 0, 6.0 + rng.random() * 1.6, 2.4, key="광장둘레올리브%.0f" % th) if rng.random() < 0.6 else \
                        m_cypress(X, Y, 0, 9.5 + rng.random() * 2.5, 1.5, key="광장둘레사이프러스%.0f" % th)
                    kind_ = "나무"
                if try_mesh_hull(m, 0.25):
                    ring[kind_] += 1
                    ring["빈 띠(평면 mm)"].append(round(0.8 + extra + max(w, d) / 2.0 - min(w, d) / 2.0, 2))
                    placed_ = True
                    break
            th += (6.4 if placed_ else 2.4) / max(60.0, r_e) * 180.0 / math.pi
        gaps = ring.pop("빈 띠(평면 mm)")
        ring["빈 띠 중앙값(평면 mm)"] = round(sorted(gaps)[len(gaps) // 2], 2) if gaps else None
        DRAWN.setdefault("hero", {})["ring_houses"] = ring
        REPORT["notes"].append("광장 둘레 첫 집 줄: 집 %d · 나무 %d" % (ring["집"], ring["나무"]))
    # 아피아 가도 길가 사이프러스·소나무 열(사양 planted: 아피아 가도 둘레)
    ap = [r for r in CM["roads"] if r["id"] == "R1"][0]
    Xc = ap["plan_pts"][0][0]
    hw = ap["w_screen_perp_mm"] / (2.0 * C30)
    k = 0
    for side, Xs in ((0, Xc - hw - 2.4), (1, Xc + hw + 2.4)):
        Y = 84.0
        while Y > -14.0:
            if side == 1 and k % 3 == 2:
                m = m_pine(Xs + 1.0, Y, 0, 9.5, 3.4, key="가도소나무%d" % k)
            else:
                m = m_cypress(Xs, Y, 0, 10.5, 1.5, key="가도사이프러스%d" % k)
            if try_mesh(m, 0.2):
                placed["사이프러스"] += 1
            Y -= 7.5
            k += 1
    REPORT["notes"].append("지붕·나무 배치: " + ", ".join("%s %d" % (a, b) for a, b in placed.items()))


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


def ves_geom():
    """베수비오(사양 projected_box, 79년 이전 넓은 봉우리 하나·잿빛 평평한 정상)의 메시와 투영 틀"""
    if "ves" in GEO:
        return GEO["ves"]
    box = VES["projected_box"]
    n = 24
    rings = [(23.0, 0.0), (19.6, 4.6), (14.8, 10.2), (10.0, 15.4), (7.2, 18.8)]
    cols = [(128, 150, 92), (142, 146, 102), (146, 132, 106), (138, 126, 112)]
    pts_r = []
    for j, (r, z) in enumerate(rings):
        ring_ = []
        for i in range(n):
            t = 2 * math.pi * i / n + 0.13 * j
            rr = r * (1.0 + (0.06 * (2 * h01("베수비오", j, i) - 1) if j else 0.0))
            zz = z + (0.5 * (2 * h01("베수비오z", j, i) - 1) if 0 < j < 4 else 0.0)
            ring_.append((rr * math.cos(t), rr * math.sin(t), zz))
        pts_r.append(ring_)
    m = Mesh((0, 0, 6))
    for j in range(len(rings) - 1):
        A_, B_ = pts_r[j], pts_r[j + 1]
        c = mix(cols[min(j, 3)], GROUND, 0.42)
        for i in range(n):
            m.add([A_[i], A_[(i + 1) % n], B_[(i + 1) % n]], c)
            m.add([A_[i], B_[(i + 1) % n], B_[i]], c)
    m.add(list(pts_r[-1]), mix((150, 142, 132), GROUND, 0.4))       # 잿빛 평평한 정상(79년 이전, 연기 없음)
    allp = [p for r_ in pts_r for p in r_]
    ox, oy, sc, zs, bb = fit_frame(allp, box)
    fr = ZIso(P, ox, oy, sc, zs)
    hull = _hull([fr.p(*q) for q in allp])
    GEO["ves"] = (m, allp, ox, oy, sc, zs, bb, hull)
    return GEO["ves"]


def draw_vesuvius():
    box = VES["projected_box"]
    m, allp, ox, oy, sc, zs, bb, hull = ves_geom()
    sub = Layer(box[0] - 4, box[1] - 4, box[2] + 4, box[3] + 4)
    isub = ZIso(sub, ox, oy, sc, zs)
    m.draw(isub, lw=0.10)
    for f in (0.28, 0.55, 0.8):                                      # 포도밭 비탈(앞 반쪽 등고 줄)
        r_ = 23.0 + (19.6 - 23.0) * f
        z_ = 4.6 * f
        pts = [isub.p(r_ * math.cos(math.radians(t)), r_ * math.sin(math.radians(t)), z_) for t in range(-40, 136, 6)]
        sub.line(pts, mix((96, 126, 70), GROUND, 0.35), 0.22)
    merge(P, sub, opacity=1.0, blur=0.14)
    GEO["ves_iso"] = (ox, oy, sc, zs)
    GEO["ves_bb"] = bb
    GEO["ves_pts"] = [isub.p(*q) for q in allp]
    record("V", VES["name"], VES.get("tier", ""), box, bb)


def draw_farm():
    """밑동 포도밭 농장(사양 props 상자): 베수비오 밑동 앞, 구릉 능선 뒤"""
    fb = PROPS["포도밭 농장"]["box"]
    fk = [(0, 0, 0), (27, 0, 0), (27, 15, 0), (0, 15, 0), (3, 2, 7.0)]
    fx, fy, fsc, fzs, fbb = fit_frame(fk, fb, ay="b")
    fiso = ZIso(P, fx, fy, fsc, 1.0)
    poly = [fiso.p(0, 0), fiso.p(27, 0), fiso.p(27, 15), fiso.p(0, 15)]
    base = mix(FIELD_BASE["vine"], BG, 0.25)
    P.poly(poly, fill=base, outline=shade(base, 0.82), lw=0.2)
    X = 1.3
    while X < 26.3:
        P.line([fiso.p(X, 0.8), fiso.p(X, 14.2)], mix(VINE_C, BG, 0.25), 0.42, joint=False)
        X += 2.2
    farm = Mesh(None)
    farm.extend(m_house(2, 1, 9, 6, 0, 3.6, 2.6, (232, 220, 196), (190, 92, 64)))
    farm.extend(m_cypress(11, 2.5, 0, 9.0, 1.3, key="농장사이프러스"))
    farm.draw(fiso, lw=0.10)
    GEO["farm_xr"] = (min(p_[0] for p_ in poly), max(p_[0] for p_ in poly))
    REPORT["objects"]["포도밭 농장"] = {"사양 상자": fb, "그린 외곽": [round(v, 1) for v in fbb]}


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
    tiers = ((0.0, w_lo, 9.0, True), (0.7, w_hi, 4.2, True))         # (기둥 안 시작, 폭, 기점 높이(개구 바닥에서), 바닥·문턱 띠)
    u0 = X0 + 1.4
    while u0 + 5.2 < Xe:
        for ti, (du, w, zs, has_floor) in enumerate(tiers):
            ua, ub = u0 + du, u0 + du + w
            z_base = 0.0 if ti == 0 else 13.0
            ol = [(u, z + z_base) for (u, z) in arch_outline(ua, ub, zs)]
            F = [isub.p(u, yf + 0.01, z) for (u, z) in ol]
            B = [isub.p(u, yk - 0.01, z) for (u, z) in ol]
            sub.poly(F, fill=soffit)
            if has_floor:                                              # 개구 바닥(지면 높이)
                fl = clip_convex([isub.p(ua, yf, z_base), isub.p(ub, yf, z_base), isub.p(ub, yk, z_base), isub.p(ua, yk, z_base)], F)
                if len(fl) >= 3:
                    sub.poly(fl, fill=floor_c)
            zj = ol[2][1]
            jb = clip_convex([isub.p(ua, yf, z_base), isub.p(ua, yk, z_base), isub.p(ua, yk, zj), isub.p(ua, yf, zj)], F)
            if len(jb) >= 3:
                sub.poly(jb, fill=in_col)
            see = clip_convex(B, F)                                      # 앞·뒤 개구가 겹치는 곳 = 뒤 지면이 보인다(뚫음)
            if len(see) >= 3:
                cd.polygon([sub.P(q) for q in see], fill=255)
                n_open[ti] += 1
            sub.line(F + [F[0]], shade(face_n, 0.62), 0.12)
        u0 += pitch
    sub.img.putalpha(ImageChops.subtract(sub.img.getchannel("A"), cut))
    isub.line3([(X0, yf + 0.03, 12.3), (Xe, yf + 0.03, 12.3)], (226, 192, 146), 0.35)   # 두 층 사이 띠돌
    isub.line3([(X0, Y0 - 0.25, H + 0.05), (Xe, Y0 - 0.25, H + 0.05)], (214, 150, 128), 0.3)    # 수로 안 방수 모르타르(분홍 회반죽)
    isub.line3([(X0, Y0 + 0.2, H + 0.05), (Xe, Y0 + 0.2, H + 0.05)], (96, 160, 206), 0.5)      # 수로 물
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


def draw_pantheon():
    L1 = LM["L1"]
    box = L1["projected_box"]
    base = m_box(-22, -22, -1.2, 22, 44.85, 0, (196, 182, 152), top=(228, 216, 190))
    rot = Mesh(None)
    rot.extend(m_cyl(0, 0, 18.0, 0, 24.0, (216, 202, 176), n=36))
    rot.extend(m_cyl(0, 0, 17.4, 24.0, 26.4, (206, 192, 166), n=36, k=0.975))
    rot.extend(m_cyl(0, 0, 16.7, 26.4, 28.0, (212, 198, 172), n=36, k=0.97))
    dome = m_dome(0, 0, 26.0, 16.2, (198, 190, 174), n=36, rings=7, oculus=0.13)
    front = Mesh(None)
    front.extend(m_box(-9.5, 14.5, 0, 9.5, 21.0, 27.0, (214, 200, 174)))
    front.extend(m_gable(-9.5, 14.5, 9.5, 21.0, 27.0, 31.0, (202, 188, 162), wall=(222, 210, 186), axis="Y", over=0.3))
    front.extend(m_box(-11.0, 21.0, 0, 11.0, 33.6, 1.4, (222, 210, 184)))
    for x in (-9.75, -6.96, -4.18, -1.39, 1.39, 4.18, 6.96, 9.75):
        front.extend(m_cyl(x, 32.6, 0.95, 1.4, 16.0, (232, 222, 208), n=8))
    for y in (24.6, 28.6):
        for x in (-9.75, -4.18, 4.18, 9.75):
            front.extend(m_cyl(x, y, 0.95, 1.4, 16.0, (226, 214, 200), n=8))
    front.extend(m_box(-11.0, 21.0, 16.0, 11.0, 33.6, 18.2, (232, 222, 200)))
    front.extend(m_gable(-11.0, 21.0, 11.0, 33.6, 18.2, 24.0, (202, 188, 162), wall=(228, 216, 192), axis="Y"))
    court = Mesh(None)
    for xs_ in (-19.5, 19.5):                                        # 앞마당 열주(포르티쿠스)
        for y in (35.0, 37.4, 39.8, 42.2):
            court.extend(m_cyl(xs_ - 1.0 * (1 if xs_ > 0 else -1), y, 0.7, 0, 8.0, (234, 224, 206), n=7))
        court.extend(m_box(xs_ - 2.2, 34.0, 8.0, xs_ + 2.2, 43.6, 9.4, (214, 196, 166), top=(196, 102, 72)))
    trees = Mesh(None)
    trees.extend(m_cypress(-18.5, -18.5, 0, 27.0, 2.3, key="판테온사이프러스1"))
    trees.extend(m_cypress(-10.5, -20.0, 0, 21.0, 2.0, key="판테온사이프러스2"))
    trees.extend(m_pine(18.5, -16.5, 0, 16.0, 6.0, key="판테온소나무"))
    trees.extend(m_olive(-18.0, 22.0, 0, 7.0, 2.6, key="판테온올리브"))
    pts = mesh_pts(base, rot, dome, front, court, trees)
    ox, oy, sc, zs, bb = fit_frame(pts, box, zs_max=1.22)
    iso = ZIso(P, ox, oy, sc, zs)
    base.draw(iso, lw=0.12)
    for X in range(-19, 21, 6):
        iso.line3([(X, -21.5, 0.02), (X, 44.3, 0.02)], (214, 200, 172), 0.12)
    back_trees = Mesh(None)
    back_trees.faces = [f for f in trees.faces if (sum(p[0] + p[1] for p in f[0]) / len(f[0])) < 5]
    front_trees = Mesh(None)
    front_trees.faces = [f for f in trees.faces if (sum(p[0] + p[1] for p in f[0]) / len(f[0])) >= 5]
    back_trees.draw(iso, lw=0.10)
    rot.draw(iso, lw=0.10)
    for zc in (8.0, 16.0):
        iso.line3([(18.05 * math.cos(math.radians(t)), 18.05 * math.sin(math.radians(t)), zc) for t in range(-45, 136, 6)], (196, 182, 156), 0.22)
    dome.draw(iso, lw=0.10)
    oc = [iso.p(2.1 * math.cos(math.radians(t)), 2.1 * math.sin(math.radians(t)), 26.0 + 16.06) for t in range(0, 360, 30)]
    P.poly(oc, fill=(92, 80, 66))
    front.draw(iso, lw=0.10)
    iso.line3([(-9.0, 33.62, 17.2), (9.0, 33.62, 17.2)], (150, 132, 108), 0.3)    # 박공 아래 명문 띠
    court.draw(iso, lw=0.10)
    ppl = Mesh(None)
    for (X, Y, c) in ((-6.0, 38.5, 0), (5.0, 40.0, 2), (9.5, 36.0, 4), (-13.0, 30.0, 1)):
        ppl.extend(m_person(X, Y, 0.02, H_PERSON / max(sc * zs, 0.6), CLOTHS[c], key="판테온사람%d" % c))
    ppl.extend(front_trees)
    ppl.draw(iso, lw=0.10)
    GEO["pantheon_shoulder"] = iso.p(16.2 * math.cos(math.radians(36)) * math.cos(math.radians(315)),
                                     16.2 * math.cos(math.radians(36)) * math.sin(math.radians(315)), 26.0 + 16.2 * math.sin(math.radians(36)))
    GEO["pantheon_top_r"] = iso.p(16.2 * math.cos(math.radians(62)) * math.cos(math.radians(315)),
                                  16.2 * math.cos(math.radians(62)) * math.sin(math.radians(315)), 26.0 + 16.2 * math.sin(math.radians(62)))
    GEO["pantheon_iso"] = iso
    add_fp("판테온 광장", _hull([iso.p(X, Y, Z) for X in (-22, 22) for Y in (-22, 44.85) for Z in (-1.2, 0)]), "지면")
    add_fp("판테온 드럼", _hull([iso.p(*q) for q in mesh_pts(rot)]), "대상 면")
    dome_pts = [iso.p(*q) for q in mesh_pts(dome)]
    add_fp("판테온 돔", _hull(dome_pts), "대상 면")
    # 돔 왼쪽 위 면(라벨 지시선 대상): 보이는 면(법선·시선 > 0) 가운데 화면 왼쪽 위 점들
    face_ul = []
    for th in range(110, 200, 6):
        for ph in range(20, 70, 6):
            t, f = math.radians(th), math.radians(ph)
            n_ = (math.cos(f) * math.cos(t), math.cos(f) * math.sin(t), math.sin(f))
            if n_[0] + n_[1] + n_[2] > 0.15:
                face_ul.append(iso.p(16.2 * n_[0], 16.2 * n_[1], 26.0 + 16.2 * n_[2]))
    GEO["pantheon_dome_ul"] = face_ul
    ocx, ocy = iso.p(0.0, 0.0, 26.0 + 16.06)
    snap = []
    for th in range(0, 360, 8):                                       # 숫자 짝 4: 돔 윗면(보이는 면, 오큘러스와 3.5mm 이상)
        for ph in range(35, 80, 5):
            t, f = math.radians(th), math.radians(ph)
            n_ = (math.cos(f) * math.cos(t), math.cos(f) * math.sin(t), math.sin(f))
            if n_[0] + n_[1] + n_[2] > 0.25:
                q = iso.p(16.2 * n_[0], 16.2 * n_[1], 26.0 + 16.2 * n_[2])
                if math.hypot(q[0] - ocx, q[1] - ocy) >= 3.5:
                    snap.append(q)
    GEO["snap_pantheon_dome"] = snap
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
    r6 = [b for r in CM["roads"] if r["id"].startswith("R6") for b in road_bands(r)]

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


def draw_basilica():
    """L7 막센티우스 바실리카(결정 7 후보 (가)): L자 기단 포장 1.5 + 북쪽 측랑(현존) 팔각 코퍼 배럴 볼트 3칸(열린 면 +Y) + 신랑 유적(기둥·낮은 벽 ≤ 4)
    + 무너진 신랑 교차 볼트 3칸 점선 복원(0.25mm, 높이 ≤ 10, 측랑 열린 면과 화면에서 겹치지 않게). 높이 수치는 인쇄하지 않는다."""
    lm = LM.get("L7")
    if not lm:
        return
    g = {k: _lm_plan(lm, k, v) for k, v in D4_LANDMARKS[0]["plan"].items()}
    iso = ISO
    rects = [[float(v) for v in r] for r in g["base_rects"]]
    bh = float(g["base_h"])
    ax0, ay0, ax1, ay1 = [float(v) for v in g["aisle"]]
    H = float(g["aisle_h"])
    nb = int(g["bays"])
    nx0, ny0, nx1, ny1 = [float(v) for v in g["nave"]]
    rh, vh = float(g["ruin_h"]), float(g["vault_h"])
    # 1 기단 포장(두 직사각형 합집합 = L자)
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
    # 2 신랑 유적: 남쪽 기둥 그루터기 + 무너진 낮은 벽(높이 ≤ ruin_h)
    bw = (nx1 - nx0) / nb
    ruin = Mesh(None)
    for k in range(nb + 1):
        Xk = min(max(nx0 + bw * k, nx0 + 1.2), nx1 - 1.2)
        hh = rh * (0.55 + 0.45 * h01("바실리카기둥", k))
        ruin.extend(m_cyl(Xk, ny1 - 1.7, 0.95, bh, bh + hh, (236, 228, 212), n=8))
    for k in range(nb):
        Xa, Xb = nx0 + bw * k + 2.2, nx0 + bw * (k + 1) - 2.2
        for j in range(3):
            xa_, xb_ = Xa + (Xb - Xa) * j / 3.0, Xa + (Xb - Xa) * (j + 1) / 3.0 - 0.3
            hh = 0.8 + (rh - 1.6) * h01("바실리카벽", k, j)
            ruin.extend(m_box(xa_, ny1 - 1.1, bh, xb_, ny1 - 0.1, bh + hh, (198, 132, 100), top=(214, 176, 146)))
    ruin.extend(m_box(nx0 + 0.2, ny0 + 4.0, bh, nx0 + 1.2, ny1 - 4.0, bh + rh * 0.6, (198, 132, 100), top=(214, 176, 146)))
    ppl = Mesh(None)
    for (Xp, Yp, c) in ((nx0 + bw * 0.55, ny0 + 13.0, 2), (nx0 + bw * 1.6, ny0 + 18.0, 4), (nx0 + bw * 2.4, ny0 + 9.0, 0)):
        ppl.extend(m_person(Xp, Yp, bh, H_PERSON, CLOTHS[c], key="바실리카사람%d" % c))
    ruin.extend(ppl)
    ruin.draw(iso, lw=0.10)
    # 3 무너진 신랑 교차 볼트 점선 복원(0.25mm, 높이 ≤ vault_h): 화면에서 측랑 열린 면 아래로만 지난다(Z < Y − 측랑 앞면 Y)
    ghost = (100, 88, 74)
    yA, yB = ny0 + 2.5, ny1

    def par(t):
        return vh * 4.0 * t * (1.0 - t)
    for k in range(nb + 1):
        Xk = nx0 + bw * k
        dotted(P, [iso.p(Xk, yA + (yB - yA) * i / 24.0, bh + par(i / 24.0)) for i in range(25)], ghost, 0.25)
    for k in range(nb):
        Xa, Xb = nx0 + bw * k, nx0 + bw * (k + 1)
        for (pa, pb) in (((Xa, yA), (Xb, yB)), ((Xb, yA), (Xa, yB))):
            dotted(P, [iso.p(pa[0] + (pb[0] - pa[0]) * i / 24.0, pa[1] + (pb[1] - pa[1]) * i / 24.0, bh + par(i / 24.0)) for i in range(25)], ghost, 0.25)
        dotted(P, [iso.p(Xa + (Xb - Xa) * i / 20.0, yB, bh + par(i / 20.0)) for i in range(21)], ghost, 0.25)
    # 4 북쪽 측랑: 팔각 코퍼 배럴 볼트 3칸, 열린 면 +Y(화면 왼쪽 아래)
    tp, tbk = 2.2, 2.0
    divs = [ax0 + (ax1 - ax0) * k / nb for k in range(nb + 1)]
    r_a = (divs[1] - divs[0] - tp) / 2.0
    z_s = H - 1.8 - r_a
    yb_ = ay0 + tbk
    pts_bb = [iso.p(x_, y_, z_) for x_ in (ax0, ax1) for y_ in (ay0, ay1) for z_ in (bh, H)]
    e0 = bbox_of(pts_bb)
    sub = Layer(e0[0] - 2, e0[1] - 2, e0[2] + 2, e0[3] + 2)
    isub = Iso(sub, 0.0, 0.0)
    brick = (186, 118, 88)
    fcol, ecol, tcol = lit(brick, (0.0, 1.0, 0.0)), lit(brick, (1.0, 0.0, 0.0)), lit((178, 164, 140), (0.0, 0.0, 1.0))
    front = [isub.p(ax0, ay1, bh), isub.p(ax1, ay1, bh), isub.p(ax1, ay1, H), isub.p(ax0, ay1, H)]
    sub.poly([isub.p(ax1, ay1, bh), isub.p(ax1, ay0, bh), isub.p(ax1, ay0, H), isub.p(ax1, ay1, H)], fill=ecol, outline=shade(ecol, 0.7), lw=0.12)
    sub.poly([isub.p(ax0, ay0, H), isub.p(ax1, ay0, H), isub.p(ax1, ay1, H), isub.p(ax0, ay1, H)], fill=tcol, outline=shade(tcol, 0.75), lw=0.12)
    for k_ in range(1, 6):                                            # 지붕 윗면 거친 콘크리트 결
        Xq = ax0 + (ax1 - ax0) * k_ / 6.0
        isub.line3([(Xq, ay0 + 0.6, H + 0.02), (Xq, ay1 - 0.6, H + 0.02)], shade(tcol, 0.9), 0.1)
    sub.poly(front, fill=fcol, outline=shade(fcol, 0.7), lw=0.12)
    soffit, jamb_c = (112, 104, 94), lit((150, 142, 130), (1.0, 0.0, 0.0))
    back_c, floor_c = shade(lit(brick, (0.0, 1.0, 0.0)), 0.74), (206, 194, 170)
    bay_info = []
    for k in range(nb):
        ua, ub = divs[k] + tp / 2.0, divs[k + 1] - tp / 2.0
        uc = (ua + ub) / 2.0
        ol = [(ua, bh), (ub, bh), (ub, z_s)] + [(uc + r_a * math.cos(math.pi * i / 14.0), z_s + r_a * math.sin(math.pi * i / 14.0)) for i in range(1, 14)] + [(ua, z_s)]
        F = [isub.p(u, ay1 + 0.01, z) for u, z in ol]
        B = [isub.p(u, yb_, z) for u, z in ol]
        sub.poly(F, fill=soffit)
        BF = clip_convex(B, F)
        if len(BF) >= 3:
            sub.poly(BF, fill=back_c)
            win = [(uc - 2.2, z_s + 0.6), (uc + 2.2, z_s + 0.6), (uc + 2.2, z_s + 2.6)] + \
                  [(uc + 2.2 * math.cos(math.pi * i / 8.0), z_s + 2.6 + 2.2 * math.sin(math.pi * i / 8.0)) for i in range(1, 8)] + [(uc - 2.2, z_s + 2.6)]
            wq = clip_convex([isub.p(u, yb_ - 0.01, z) for u, z in win], BF)
            if len(wq) >= 3:
                sub.poly(wq, fill=(250, 236, 196))                   # 뒤 벽 큰 창(빛)
        fl = clip_convex([isub.p(ua, ay1, bh), isub.p(ub, ay1, bh), isub.p(ub, yb_, bh), isub.p(ua, yb_, bh)], F)
        if len(fl) >= 3:
            sub.poly(fl, fill=floor_c)
        jb = clip_convex([isub.p(ua, ay1, bh), isub.p(ua, yb_, bh), isub.p(ua, yb_, z_s), isub.p(ua, ay1, z_s)], F)
        if len(jb) >= 3:
            sub.poly(jb, fill=jamb_c)
        cf = Layer(sub.x0, sub.y0, sub.x1, sub.y1)                    # 팔각 코퍼 결(보이는 아치 안쪽 윗면에만)
        icf = Iso(cf, 0.0, 0.0)
        for d_ in (2.4, 4.8, 7.2, 9.6):
            if ay1 - d_ <= yb_:
                continue
            icf.line3([(uc + r_a * math.cos(math.radians(a)), ay1 - d_, z_s + r_a * math.sin(math.radians(a))) for a in range(80, 181, 6)], (86, 80, 72), 0.14)
        for a in (100, 122, 144, 166):
            icf.line3([(uc + r_a * math.cos(math.radians(a)), ay1, z_s + r_a * math.sin(math.radians(a))),
                       (uc + r_a * math.cos(math.radians(a)), yb_, z_s + r_a * math.sin(math.radians(a)))], (86, 80, 72), 0.14)
            for d_ in (1.2, 3.6, 6.0, 8.4):
                q = icf.p(uc + (r_a - 0.2) * math.cos(math.radians(a + 11)), ay1 - d_, z_s + (r_a - 0.2) * math.sin(math.radians(a + 11)))
                cf.poly([(q[0] + 0.5 * math.cos(math.radians(22.5 + 45 * j)), q[1] + 0.42 * math.sin(math.radians(22.5 + 45 * j))) for j in range(8)],
                        fill=(136, 128, 116))
        _clip_layer(cf, [F], [BF] + ([jb] if len(jb) >= 3 else []) + ([fl] if len(fl) >= 3 else []))
        sub.paste(cf)
        sub.line(F + [F[0]], shade(fcol, 0.55), 0.14)
        bay_info.append({"bay": k + 1, "u": [round(ua, 2), round(ub, 2)], "open_face_center": [round(v, 2) for v in iso.p(uc, ay1, bh + (z_s - bh) * 0.55)]})
    isub.line3([(ax0, ay1 + 0.02, H - 1.8), (ax1, ay1 + 0.02, H - 1.8)], shade(fcol, 1.12), 0.25)   # 볼트 머리 띠
    merge(P, sub)
    # 5 기록
    base_pts = [iso.p(r[i], r[j], z) for r in rects for i in (0, 2) for j in (1, 3) for z in (0.0, bh)]
    aisle_pts = [iso.p(x_, y_, z_) for x_ in (ax0, ax1) for y_ in (ay0, ay1) for z_ in (bh, H)]
    nave_pts = [iso.p(x_, y_, z_) for x_ in (nx0, nx1) for y_ in (ny0, ny1) for z_ in (bh, bh + rh)]
    add_fp("바실리카 지면", _hull(base_pts), "지면")
    add_fp("바실리카 측랑 볼트", _hull(aisle_pts), "대상 면")
    add_fp("바실리카 신랑 유적", _hull(nave_pts), "대상 면")
    uc0 = (divs[0] + divs[1]) / 2.0
    GEO["lead_tgt_막센티우스 바실리카"] = iso.p(uc0, ay1, bh + (z_s - bh) * 0.62)
    GEO["basilica_mid_bay"] = iso.p((divs[1] + divs[2]) / 2.0 if nb >= 3 else uc0, ay1, bh + (z_s - bh) * 0.62)
    hull = _hull(base_pts + aisle_pts)
    GEO["parts_L7"] = [_hull([iso.p(r[i], r[j], z) for i in (0, 2) for j in (1, 3) for z in (0.0, bh)]) for r in rects] + [_hull(aisle_pts), _hull(nave_pts)]
    for pg in GEO["parts_L7"]:
        ex_poly(pg, 2.0)
    GEO["sil_L7"] = hull
    bb = bbox_of(base_pts + aisle_pts)
    GEO["basilica_form"] = {"bays": bay_info, "arch_r_plan": round(r_a, 2), "spring_z": round(z_s, 2), "aisle_h": H, "vault_ghost_h_max": vh,
                            "ghost_rule": "점선 점 Z < Y − 측랑 앞면 Y(화면에서 열린 면 아래 변보다 아래)"}
    record("L7", lm["name"], "Core(표준 랜드마크)", lm["projected_box"], bb, "북쪽 측랑 배럴 볼트 3칸 + 신랑 교차 볼트 점선 복원")


def draw_mausoleum():
    """L8 하드리아누스 영묘 + 폰스 아일리우스(결정 8 후보 (나)): 사각 기단 h5 + 원통(겉 대리석·속 콘크리트, 앞 오른쪽에 겉을 벗긴 창)
    + 정상 낮은 둔덕·난간(조각·교황 증축 형태 없음) + ↘ 팔을 건너는 다리(상판 3, 아치 3). 치수는 인쇄하지 않는다."""
    lm = LM.get("L8")
    if not lm:
        return
    g = {k: _lm_plan(lm, k, v) for k, v in D4_LANDMARKS[1]["plan"].items()}
    iso = ISO
    X0, Y0, X1, Y1 = [float(v) for v in g["base"]]
    bh = float(g["base_h"])
    dcx, dcy = [float(v) for v in g["drum_c"]]
    R = float(g["drum_r"])
    z0d, z1d = [float(v) for v in g["drum_z"]]
    zt0, zt1 = [float(v) for v in g["top_z"]]
    bX0, bY0, bX1, bY1 = [float(v) for v in g["bridge"]]
    brh = float(g["bridge_h"])
    nar = int(g["bridge_arches"])
    marble, trav = (246, 238, 220), (226, 212, 182)
    # 0 R7 남쪽 끝 진입 경사(다리보다 뒤)(평면 Y 294.76~304.76, Z 0 → 다리 상판 3.0) — 결정 D7
    r7 = next((r for r in CM["roads"] if r["id"] == "R7"), None)
    ramp = None
    if r7:
        hw7 = float(r7.get("w_screen_perp_mm", 8.0)) / (2.0 * C30)
        xr7 = float(r7["plan_pts"][0][0])
        ya_, yb7 = bY0 - 10.0, bY0
        rx0, rx1 = xr7 - hw7, xr7 + hw7
        P.poly([iso.p(rx0, ya_, 0.0), iso.p(rx1, ya_, 0.0), iso.p(rx1, yb7, brh), iso.p(rx0, yb7, brh)], fill=ROAD_C)
        P.poly([iso.p(rx1, ya_, 0.0), iso.p(rx1, yb7, 0.0), iso.p(rx1, yb7, brh)], fill=ftone(ROAD_C, 0.7071, 0.7071))
        for k in range(1, 5):
            f_ = k / 5.0
            P.line([iso.p(rx0, ya_ + 10.0 * f_, brh * f_), iso.p(rx1, ya_ + 10.0 * f_, brh * f_)], ROAD_EDGE, 0.12, joint=False)
        P.line([iso.p(rx1, ya_, 0.0), iso.p(rx1, yb7, brh)], ROAD_EDGE, 0.3, joint=False)
        ramp = {"plan_X": [round(rx0, 2), round(rx1, 2)], "plan_Y": [round(ya_, 2), round(yb7, 2)], "z": [0.0, brh]}
    # 1 다리(가장 뒤): 상판·난간 + +X면 아치 nar개(아치 아래는 그늘진 물)
    br = Mesh(None)
    br.extend(m_box(bX0, bY0, -0.4, bX1, bY1, brh, trav, top=(232, 222, 198)))
    br.extend(m_box(bX0, bY0, brh, bX0 + 0.5, bY1, brh + 0.8, (228, 216, 190)))
    br.extend(m_box(bX1 - 0.5, bY0, brh, bX1, bY1, brh + 0.8, (228, 216, 190)))
    br.draw(iso, lw=0.1)
    ab_, pier = 1.4, 1.6
    aw = (bY1 - bY0 - 2 * ab_ - (nar - 1) * pier) / nar
    for k in range(nar):
        ya = bY0 + ab_ + k * (aw + pier)
        yc = ya + aw / 2.0
        q = [(ya, -0.4), (ya + aw, -0.4)] + [(yc + aw / 2.0 * math.cos(math.pi * i / 10.0), 0.4 + (brh - 1.0) * math.sin(math.pi * i / 10.0)) for i in range(0, 11)]
        P.poly([iso.p(bX1 + 0.02, u, z) for u, z in q], fill=(70, 108, 140), outline=(120, 104, 80), lw=0.1)
    # 2 사각 기단(대리석 마감) + 윗단 띠 + 북쪽 변 디딤 2단(다리 상판 3.0 → 3.67 → 4.33 → 기단 5.0, 챌면 0.67 × 3)
    base = Mesh(None)
    base.extend(m_box(X0, Y0, 0, X1, Y1, bh, marble, top=(230, 222, 204)))
    base.draw(iso, lw=0.12)
    st_x0, st_x1 = bX0, bX1
    rise = (bh - brh) / 3.0
    steps_ = []
    for k in range(2):
        ys0_, ys1_ = Y0 + 2.0 * k, Y0 + 2.0 * (k + 1)
        zt_ = brh + rise * (k + 1)
        P.poly([iso.p(st_x0, ys0_, zt_), iso.p(st_x1, ys0_, zt_), iso.p(st_x1, ys1_, zt_), iso.p(st_x0, ys1_, zt_)], fill=(236, 228, 212))
        P.poly([iso.p(st_x0, ys1_, zt_), iso.p(st_x0, ys1_, bh), iso.p(st_x0, ys0_, bh), iso.p(st_x0, ys0_, zt_)], fill=ftone(marble, 0.7071, 0.7071))
        P.line([iso.p(st_x0, ys0_, zt_), iso.p(st_x1, ys0_, zt_)], (200, 190, 170), 0.15, joint=False)
        steps_.append({"Y": [round(ys0_, 2), round(ys1_, 2)], "z_top": round(zt_, 2)})
    P.line([iso.p(st_x0, Y0 + 4.0, bh), iso.p(st_x1, Y0 + 4.0, bh)], (200, 190, 170), 0.15, joint=False)
    GEO["mausoleum_steps"] = {"X": [st_x0, st_x1], "steps": steps_, "riser": round(rise, 3), "ramp": ramp,
                              "rule": "결정 D7: R7 남쪽 끝 Z 0→3.0 경사 + 기단 북쪽 변 디딤 2단(3.67·4.33) → 기단 5.0. 양 끝 보행면 높이 차 0"}
    for zc in (1.6, 3.2):
        iso.line3([(X0, Y1 + 0.01, zc), (X1, Y1 + 0.01, zc)], (206, 198, 180), 0.1)
        iso.line3([(X1 + 0.01, Y0, zc), (X1 + 0.01, Y1, zc)], (200, 192, 172), 0.1)
    iso.line3([(X0, Y1 + 0.01, bh - 0.6), (X1, Y1 + 0.01, bh - 0.6), ], (190, 180, 160), 0.22)
    iso.line3([(X1 + 0.01, Y0, bh - 0.6), (X1 + 0.01, Y1, bh - 0.6)], (184, 174, 154), 0.22)
    # 3 원통(겉 대리석) + 정상 난간·둔덕
    drum = Mesh(None)
    zp = z1d                                                         # 원통 윗변 z 23(결정). 높은 아티카는 두지 않는다: 원통 뒤-오른쪽 테가 강 건너 하역장 부두 아래 변과 맞닿기 때문
    drum.extend(m_cyl(dcx, dcy, R, z0d, z1d, marble, n=44, top=(150, 160, 106)))
    drum.draw(iso, lw=0.10)
    for zc in (8.5, 12.0, 15.5, 19.0):                               # 대리석 줄눈
        iso.line3([(dcx + R * 1.002 * math.cos(math.radians(t)), dcy + R * 1.002 * math.sin(math.radians(t)), zc) for t in range(-44, 135, 6)], (214, 206, 188), 0.12)
    iso.line3([(dcx + R * 1.003 * math.cos(math.radians(t)), dcy + R * 1.003 * math.sin(math.radians(t)), z1d - 1.2) for t in range(-44, 135, 6)], (196, 186, 166), 0.26)
    iso.line3([(dcx + (R - 0.6) * math.cos(math.radians(t)), dcy + (R - 0.6) * math.sin(math.radians(t)), z1d + 0.02) for t in range(0, 361, 6)], (232, 224, 204), 0.45)   # 낮은 난간 테
    mr_ = min(R - 1.4, float(_lm_plan(lm, "mound_r", R - 1.4)))            # 사양 mound.r_max(통합 d4)
    m_mound(dcx, dcy, z1d, mr_, zt1 - z1d, (128, 146, 92), n=16, rings=3, key="영묘둔덕", jit=0.05, apex_jit=0.08).draw(iso, lw=0.10)
    # 4 겉을 벗긴 창(앞 오른쪽): 속 콘크리트 + 대리석 겉켜 두께 띠
    ta, tb_, zc0, zc1 = -6.0, 26.0, 9.0, 20.0
    conc = (168, 162, 150)
    t = ta
    while t < tb_ - 1e-6:
        t1 = min(tb_, t + 4.0)
        tm = math.radians((t + t1) / 2.0)
        P.poly(cyl_quad(iso, dcx, dcy, R + 0.03, t, t1, zc0, zc1), fill=lit(conc, (math.cos(tm), math.sin(tm), 0.0)))
        t = t1
    rngm = local_rng("영묘콘크리트")
    for i in range(26):
        tt = math.radians(ta + 2 + rngm.random() * (tb_ - ta - 4))
        zz = zc0 + 0.8 + rngm.random() * (zc1 - zc0 - 1.6)
        q = iso.p(dcx + (R + 0.05) * math.cos(tt), dcy + (R + 0.05) * math.sin(tt), zz)
        P.ell(q[0], q[1], 0.36, 0.28, fill=(120, 110, 98) if i % 3 else (238, 234, 222))
    left_edge = [iso.p(dcx + R * math.cos(math.radians(ta)), dcy + R * math.sin(math.radians(ta)), z) for z in (zc0, zc1)]
    bot_edge = [iso.p(dcx + R * math.cos(math.radians(tt)), dcy + R * math.sin(math.radians(tt)), zc0) for tt in range(int(ta), int(tb_) + 1, 4)]
    P.line(left_edge, (250, 248, 240), 0.9, joint=False)
    P.line(bot_edge, (250, 248, 240), 0.7)
    P.line(left_edge, (150, 140, 124), 0.12, joint=False)
    P.line([(q[0], q[1] + 0.36) for q in bot_edge], (150, 140, 124), 0.12)
    # 5 기록
    base_pts = [iso.p(x_, y_, z_) for x_ in (X0, X1) for y_ in (Y0, Y1) for z_ in (0.0, bh)]
    drum_pts = [iso.p(dcx + R * math.cos(math.radians(t)), dcy + R * math.sin(math.radians(t)), z) for t in range(0, 360, 10) for z in (z0d, z1d)]
    drum_pts.append(iso.p(dcx, dcy, zt1))
    br_pts = [iso.p(x_, y_, z_) for x_ in (bX0, bX1) for y_ in (bY0, bY1) for z_ in (-0.4, brh + 0.8)]
    add_fp("영묘 기단", _hull(base_pts), "대상 면")
    add_fp("영묘 원통", _hull(drum_pts), "대상 면")
    add_fp("폰스 아일리우스 다리", _hull(br_pts), "대상 면")
    strip_r = [iso.p(X1 - 4.6, Y0 + 0.6, bh), iso.p(X1 - 0.3, Y0 + 0.6, bh), iso.p(X1 - 0.3, Y1 - 0.3, bh), iso.p(X1 - 4.6, Y1 - 0.3, bh)]
    strip_f = [iso.p(X0 + 0.6, Y1 - 4.6, bh), iso.p(X1 - 0.3, Y1 - 4.6, bh), iso.p(X1 - 0.3, Y1 - 0.3, bh), iso.p(X0 + 0.6, Y1 - 0.3, bh)]
    GEO["fpset_영묘 기단 윗면"] = [strip_r, strip_f]
    add_fp("영묘 기단 윗면", strip_r, "대상 면")
    hull = _hull(base_pts + drum_pts)
    GEO["parts_L8"] = [_hull(base_pts), _hull(drum_pts), _hull(br_pts)]
    for pg in GEO["parts_L8"]:
        ex_poly(pg, 2.0)
    GEO["sil_L8"] = hull
    GEO["sil_L8_bridge"] = _hull(br_pts)
    bb = bbox_of(base_pts + drum_pts + br_pts)
    record("L8", lm["name"], "Core(표준 랜드마크)", lm["projected_box"], bb, "다리 포함 외곽")
    DRAWN["mausoleum_access"] = GEO.get("mausoleum_steps")


def draw_theatre():
    """L9 마르켈루스 극장(결정 9 후보 (라)): 반원 평면(지름 = 무대 쪽, 곡면 = +X), 바깥 아케이드 2단(6+6), 관람석 단, 무대 쪽 벽 ≤ 4.
    3단은 그리지 않는다. 지름은 인쇄하지 않는다."""
    lm = LM.get("L9")
    if not lm:
        return
    g = {k: _lm_plan(lm, k, v) for k, v in D4_LANDMARKS[2]["plan"].items()}
    iso = ISO
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
    yard = sget(d, "yard_box", "yard_screen", default=None) or [172.0, 196.0, 198.0, 228.0]
    cxs, cys = sp(X, Y)
    hs = min((yard[2] - yard[0]) / (4.0 * C30), (yard[3] - cys) / 1.0, 7.5)          # 평면 정사각 마당(화면 마름모가 마당 상자 안)
    yq = [sp(X - hs, Y - hs), sp(X + hs, Y - hs), sp(X + hs, Y + hs), sp(X - hs, Y + hs)]
    P.poly(yq, fill=H_PLAZA)
    for k in range(1, 6):                                            # 마당 판석 줄눈(L3)
        f_ = k / 6.0
        P.line([lerp(yq[0], yq[1], f_), lerp(yq[3], yq[2], f_)], H_PLAZA_J, 0.12, joint=False)
        P.line([lerp(yq[0], yq[3], f_), lerp(yq[1], yq[2], f_)], H_PLAZA_J, 0.12, joint=False)
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
    arm_a = [float(v) for v in sget(mol, "arm_a_deg", "arm_a", default=[263.0, 123.0])]
    arm_b = [float(v) for v in sget(mol, "arm_b_deg", "arm_b", default=[277.0, 417.0])]
    col = [float(v) for v in sget(mol, "colonnade_deg", "colonnade", default=[12.0, 54.0])]
    canals = []
    for c in (can or [{"name": "강 쪽 운하", "plan_x": [435.5, 438.5], "plan_y": [322.84, 338.6]},
                      {"name": "외항 쪽 운하", "plan_x": [435.5, 438.5], "plan_y": [368.6, 384.0]}]):
        canals.append({"name": c.get("name", "운하"), "x": [float(v) for v in c.get("plan_x", [435.5, 438.5])], "y": [float(v) for v in c.get("plan_y")]})
    ang = float(sget(lh, "plan_angle_deg", "angle_deg", "angle", default=90.0))
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
    iso = ISO
    # 1 육각 내항(육지): 포장 둘레·성벽·창고 고리(붉은 기와)·부두·물
    pave = hexring(hx, hy, HR)
    iso.poly3([(x, y, 0) for x, y in pave], fill=(216, 202, 170), ol=(150, 130, 98), lw=0.25)
    wall = Mesh(None)
    trims = {0: (0.0, 0.88), 1: (0.12, 1.0), 3: (0.0, 0.88), 4: (0.12, 1.0)}
    for k in range(6):
        a0p, b0p = pave[k], pave[(k + 1) % 6]
        f0, f1 = trims.get(k, (0.0, 1.0))
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
        if k in (0, 3):
            pieces = [(0.06, 0.46), (0.54, 0.80)]
        elif k in (1, 4):
            pieces = [(0.20, 0.46), (0.54, 0.94)]
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
        ya, yb_ = min(y0, y1), max(y0, y1)
        # d4 결정 13: 사양 plan_y 그대로 그린다(렌더의 끝점 추가 연장 0). 그린 끝점 = 사양 ±0.3mm
        ya_d, yb_d = ya, yb_
        q = [iso.p(x0, ya_d, 0.33), iso.p(x1, ya_d, 0.33), iso.p(x1, yb_d, 0.33), iso.p(x0, yb_d, 0.33)]
        P.poly(q, fill=HARBOR_C)
        P.line([iso.p(x0, ya_d, 0.33), iso.p(x0, yb_d, 0.33)], (96, 136, 166), 0.15, joint=False)
        P.line([iso.p(x1, ya_d, 0.33), iso.p(x1, yb_d, 0.33)], (96, 136, 166), 0.15, joint=False)
        hexw = hexring(hx, hy, HWR)
        if ya > hy:          # 외항 쪽: 육각 수면(위 끝) ↔ 외항 수면(아래 끝)
            e_hex, e_out = ya_d, yb_d
            ok_hex = all(in_poly((x, e_hex), hexw) for x in (x0, x1))
            ok_out = all(math.hypot(x - bx, e_out - by) < r_in for x in (x0, x1))
        else:                # 강 쪽: 강 수면(위 끝) ↔ 육각 수면(아래 끝)
            e_hex, e_out = yb_d, ya_d
            ok_hex = all(in_poly((x, e_hex), hexw) for x in (x0, x1))
            ok_out = e_out < RIV_Y + RIV_HW1
        canal_info.append({"name": c["name"], "continuous": bool(ok_hex and ok_out), "opening_w": round(x1 - x0, 2),
                           "screen_w": round((x1 - x0) * C30, 2), "plan_y": [round(ya_d, 2), round(yb_d, 2)],
                           "plan_y_drawn": [round(ya_d, 2), round(yb_d, 2)], "plan_y_spec": [round(ya, 2), round(yb_, 2)],
                           "end_dev_mm": round(max(abs(ya_d - ya), abs(yb_d - yb_)), 3), "render_extension_mm": 0.0})
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
            moles.extend(m_prism(q, -0.4, 1.0, (206, 196, 174)))
            if i == n - 1:
                tip_polys[key] = _hull([iso.p(x, y, z) for x, y in q for z in (-0.4, 1.0)])
    mole_arc(pp["arm_a"][0], pp["arm_a"][1], "arm_a")
    mole_arc(pp["arm_b"][0], pp["arm_b"][1], "arm_b")
    rm = (r_in + r_out) / 2.0
    for th in (150.0, 165.0, 180.0, 195.0, 210.0):                  # 바다 쪽 방파제(팔 A) 위 창고
        t = math.radians(th)
        Xc, Yc = bx + rm * math.cos(t), by + rm * math.sin(t)
        moles.extend(m_box(Xc - 1.2, Yc - 1.2, 1.0, Xc + 1.2, Yc + 1.2, 2.9, (230, 210, 180)))
        moles.extend(m_frustum([(Xc - 1.3, Yc - 1.3), (Xc + 1.3, Yc - 1.3), (Xc + 1.3, Yc + 1.3), (Xc - 1.3, Yc + 1.3)], 2.9, 4.1, 0.4, ROOF))
    c0, c1 = pp["col"]
    th = c0
    while th <= c1 + 1e-6:                                          # 열주: 팔 B의 12~54°에만
        t = math.radians(th)
        moles.extend(m_cyl(bx + rm * math.cos(t), by + rm * math.sin(t), 0.35, 1.0, 3.6, (240, 232, 214), n=6))
        th += 7.0
    # 5 등대섬(사양 평면 각·반지름): 섬 + 층을 쌓은 탑 + 등롱
    LX, LY = bx + pp["lr"] * math.cos(math.radians(pp["ang"])), by + pp["lr"] * math.sin(math.radians(pp["ang"]))
    tower = Mesh(None)
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
    for (X, Y, sc_) in ((hx - 5.0, hy + 3.0, 0.8), (hx + 4.0, hy - 4.0, 0.8), (bx - 6.0, by + 4.0, 1.0), (bx + 7.0, by - 2.0, 1.0)):
        bx_, by_ = iso.p(X, Y, 0.3)
        P.poly([(bx_ - 3.2 * sc_, by_ - 0.6 * sc_), (bx_ + 3.2 * sc_, by_ + 1.2 * sc_), (bx_ + 2.2 * sc_, by_ + 2.2 * sc_), (bx_ - 2.6 * sc_, by_ + 0.9 * sc_)], fill=(150, 104, 66))
        P.poly([(bx_ + 0.2 * sc_, by_ - 0.2 * sc_), (bx_ + 0.2 * sc_, by_ - 5.0 * sc_), (bx_ + 2.6 * sc_, by_ - 1.0 * sc_)], fill=(244, 236, 216), outline=(150, 130, 100), lw=0.1)
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
    isl_fp = [iso.p(LX + pp["isl"] * math.cos(math.radians(t)), LY + pp["isl"] * math.sin(math.radians(t)), 0.0) for t in range(0, 360, 10)]
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
                       "island_water_rule": "수면 높이(z 0)에서 등대섬 외곽 ↔ 두 팔 끝 조각 외곽의 화면 거리(팔 A, 팔 B)",
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
    sub = Layer(CX_S - KU * a - 3, CY_S - KV * b - 8, CX_S + 3, CY_S + KV * b + 6)
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
H_PLAZA, H_PLAZA_J, H_PATH = (221, 209, 184), (207, 194, 168), (230, 218, 192)     # 광장 판석·줄눈·문 길


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


D5_CROWDS = [("G1 앞 광장", (245.0, 351.0)), ("G2 앞-오른쪽 광장", (277.0, 339.0)), ("G3 왼쪽 광장", (186.0, 322.0)), ("G4 하역장 길 문", (197.5, 349.5))]
D5_SCATTER = [(-10.2, 59.2), (-20.6, 58.4), (-58.2, 30.6), (-61.0, 32.8), (51.6, -37.6), (20.6, -62.0), (22.8, -70.2)]   # 흩어진 사람(조경 중심 기준 평면)
H_PERSON_HERO = 4.9                                                     # 결정 D8: 히어로 조경·공사장·네로 마당 사람 키(화면 mm)


def col_sil_approx():
    """그리기 전 빈 자리 마스크용 콜로세움 실루엣(외곽 타원 + 칸별 윗선의 볼록 껍질)"""
    pts = []
    for b in BAYS:
        for s in (b["s0"], b["sc"], b["s1"]):
            pts.append(M(s, -2.6, 0.0))
            pts.append(M(s, 0.0, z_wall(b, s, 1)))
            pts.append(M(s, CO_D2, z_wall(b, s, 2)))
    return _hull(pts)


def _gate_paths():
    """문 길(조경 중심 기준 평면 직사각형): 콜로세움 쪽 → 사양 길 끝(아피아 가도 R1 · 하역장 길 R4). 길 폭 = 사양 w_screen_perp_mm"""
    out = []
    for rid in ("R1", "R4"):
        r = next((q for q in CM["roads"] if q["id"] == rid), None)
        if not r:
            continue
        hw = float(r.get("w_screen_perp_mm", 8.0)) / (2.0 * C30)
        ends_ = [tuple(r["plan_pts"][0]), tuple(r["plan_pts"][-1])]
        e = min(ends_, key=lambda q: math.hypot(q[0] - LS_C[0], q[1] - LS_C[1]))
        ex_, ey_ = e[0] - LS_C[0], e[1] - LS_C[1]
        if rid == "R4":                                                    # 앞-왼쪽: 콜로세움 앞 → 남쪽(+Y) 문
            q = [(ex_ - hw, 30.0), (ex_ + hw, 30.0), (ex_ + hw, ey_), (ex_ - hw, ey_)]
        else:                                                              # 뒤-오른쪽: 북쪽(−Y) 문 → 콜로세움 오른쪽
            q = [(ex_ - hw, ey_), (ex_ + hw, ey_), (ex_ + hw, -52.0), (ex_ - hw, -52.0)]
        out.append((rid, [sp(LS_C[0] + a, LS_C[1] + b) for a, b in q], hw, (ex_, ey_)))
    return out


def _plaza_joints(L, poly, key="광장"):
    """광장 판석 줄눈(평면 X·Y 축 4.6 격자) + 판석 톤 몇 장(L3). poly 안만"""
    x0, y0, x1, y1 = bbox_of(poly)
    sub = Layer(x0 - 1, y0 - 1, x1 + 1, y1 + 1)
    rng = local_rng(key)
    g = 4.6
    Xs = [LS_C[0] + k * g for k in range(-22, 23)]
    Ys = [LS_C[1] + k * g for k in range(-22, 23)]
    for X in Xs:
        for Y in Ys:
            if rng.random() < 0.10:
                c = (214, 202, 177) if rng.random() < 0.6 else (226, 215, 192)
                sub.poly([sp(X, Y), sp(X + g, Y), sp(X + g, Y + g), sp(X, Y + g)], fill=c)
    for X in Xs:
        sub.line([sp(X, Ys[0]), sp(X, Ys[-1])], H_PLAZA_J, 0.12, joint=False)
    for Y in Ys:
        sub.line([sp(Xs[0], Y), sp(Xs[-1], Y)], H_PLAZA_J, 0.12, joint=False)
    m = Image.new("L", (sub.w, sub.h), 0)
    ImageDraw.Draw(m).polygon([sub.P(p) for p in poly], fill=255)
    sub.img.putalpha(ImageChops.multiply(sub.img.getchannel("A"), m))
    L.paste(sub)


def _free_box(bb, pad=0.4):
    """사각 외곽이 빈 자리(EXCL)와 라벨 슬롯·Detail 상자와 겹치지 않는가"""
    if not poly_free(box_poly(bb), pad):
        return False
    for s in LBS["slots"]:
        b = s.get("box")
        if b and not (bb[2] < b[0] - 1.0 or bb[0] > b[2] + 1.0 or bb[3] < b[1] - 1.0 or bb[1] > b[3] + 1.0):
            return False
    return True


def _hero_trees(sil):
    """둘레 나무(승인 설계 히어로 군: 광장 가장자리 사이프러스·올리브). 키는 결정 D8(사람 4.9 기준 사이프러스 3.3~4.3배 · 올리브 2.9배)"""
    specs = [("c", 192.0, 17.5), ("c", 200.0, 19.0), ("o", 212.0, 14.2), ("c", 298.0, 18.0), ("c", 306.0, 16.5), ("o", 318.0, 14.2),
             ("o", 104.0, 14.2), ("o", 116.0, 14.2), ("c", 66.0, 18.5), ("c", 72.0, 16.5), ("o", 20.0, 14.2), ("c", 338.0, 17.0)]
    back, front, placed = Mesh(None), Mesh(None), []
    for kd, th, h in specs:
        r = rb(th) - 4.5
        t = math.radians(th)
        X, Y = LS_C[0] + r * math.cos(t), LS_C[1] + r * math.sin(t)
        m = m_cypress(X, Y, 0, h, 1.8, key="히어로사이프러스%d" % th) if kd == "c" else m_olive(X, Y, 0, h, 3.6, key="히어로올리브%d" % th)
        pts = [ISO.p(*q) for q in mesh_pts(m)]
        bb = bbox_of(pts)
        if not _free_box(bb, 0.3) or any(in_poly(q, sil) for q in pts) or not in_poly(ISO.p(X, Y), GEO["plaza_poly"]):
            continue
        du, dv = (X - CO_C[0] - (Y - CO_C[1])) * KV, (X - CO_C[0] + Y - CO_C[1]) * KV
        (back if dv < 0 else front).extend(m)
        placed.append({"kind": "사이프러스" if kd == "c" else "올리브", "th": th, "plan": [round(X, 2), round(Y, 2)], "h": h, "box": [round(v, 2) for v in bb]})
    return back, front, placed


def _hero_crowds(sil, avoid):
    """인물 군 4곳(결정 D3 자리, 군마다 5~7명·이웃 발점 3.5~5mm, 키 4.9) + 흩어진 사람 7명"""
    offs = [(-8.0, -1.5), (-4.0, -2.6), (0.2, -1.2), (4.3, -2.4), (-2.2, 2.4), (2.9, 2.7)]
    plaza = GEO["plaza_poly"]

    def ok_pt(x, y):
        if not in_poly((x, y), plaza) or in_poly((x, y), sil) or _pt_poly_gap((x, y), sil) < 1.2:
            return False
        return all(not (b[0] - 0.8 <= x <= b[2] + 0.8 and b[1] - 0.8 <= y + 0.5 and y - 5.0 <= b[3] + 0.8) for b in avoid)

    def nn_ok(feet):
        for i, p in enumerate(feet):
            d = min(math.hypot(p[0] - q[0], p[1] - q[1]) for j, q in enumerate(feet) if j != i)
            if d < 3.5 or d > 5.0:
                return False
        return True
    out = []
    for k, (nm, c0) in enumerate(D5_CROWDS):
        best = None
        for dx in (0.0, 1.5, -1.5, 3.0, -3.0, 4.5, -4.5, 6.0, -6.0):
            for dy in (0.0, 1.0, -1.0, 2.0, -2.0, 3.0, -3.0):
                feet = [(c0[0] + dx + ox, c0[1] + dy + oy) for ox, oy in offs]
                feet = [p for p in feet if ok_pt(*p)]
                if 5 <= len(feet) <= 7 and nn_ok(feet):
                    score = len(feet) - 0.04 * (abs(dx) + abs(dy))
                    if best is None or score > best[0]:
                        best = (score, feet, (c0[0] + dx, c0[1] + dy))
        if best:
            out.append({"name": nm, "k": k, "feet": best[1], "center": best[2]})
        else:
            REPORT["notes"].append("인물 군 자리 없음: %s" % nm)
    scat = []
    for (pX, pY) in D5_SCATTER:
        x, y = sp(LS_C[0] + pX, LS_C[1] + pY)
        if ok_pt(x, y):
            scat.append((x, y))
    return out, scat


def draw_arena():
    """히어로(결정 D2·D3 · 기준선 8.1 12:49 철회 · 8.2): 받침 0(옆면·팔각 외곽·지층·앞 변 절개 없음). 지도 땅 높이의 광장 판석(테두리선 0) 위에
    콜로세움 건물 + 승인 설계 히어로 군(광장 포장·문 길·인물 무리 4·흩어진 사람·둘레 나무). LocalBanana 조경 부품(폐허·신전·노점 배치)은 옮겨 오지 않는다.
    공사장은 draw_worksite, 네로 거상 받침·마당은 draw_colossus가 그린다."""
    sil0 = col_sil_approx()
    # 1 광장 판석(땅 높이, 옆면 0) + 문 길
    poly, trims = plaza_poly()
    GEO["plaza_poly"] = poly
    P.poly(poly, fill=H_PLAZA)
    _plaza_joints(P, poly)
    paths = _gate_paths()
    for rid, q, hw, end in paths:
        P.poly(q, fill=H_PATH)
        for k in range(1, 40):                                            # 문 길 판석 가로 줄눈(L3)
            f = k / 40.0
            a_, b_ = lerp(q[0], q[3], f), lerp(q[1], q[2], f)
            P.line([a_, b_], H_PLAZA_J, 0.12, joint=False)
    # 2 둘레 나무(뒤) → 콜로세움 건물 → 앞 나무·인물
    tb, tf, trees = _hero_trees(sil0)
    tb.draw(ISO, lw=0.1)
    BL, crec = draw_colosseum_d5()
    P.paste(BL)
    sil = _layer_sil(BL)
    bbox_b, area_b, poly_b, top_y = sil if sil else (CO_BOX, 0.0, sil0, lambda x: None)
    ws_box = WS_SPEC["box"]
    groups, scat = _hero_crowds(poly_b, [ws_box] + [t_["box"] for t_ in trees])
    tf.draw(ISO, lw=0.1)
    ppl = Mesh(None)
    for g in groups:
        for i, (x, y) in enumerate(g["feet"]):
            X, Y = to_plan(x, y)
            ppl.extend(m_person(X, Y, 0, H_PERSON_HERO, CLOTHS[(i + g["k"]) % 6], key="군%d사람%d" % (g["k"], i)))
    for i, (x, y) in enumerate(scat):
        X, Y = to_plan(x, y)
        ppl.extend(m_person(X, Y, 0, H_PERSON_HERO, CLOTHS[(i + 3) % 6], key="흩어진사람%d" % i))
    ppl.draw(ISO, lw=0.1)
    for g in groups:
        DRAWN["crowds"].append({"name": g["name"], "center": [round(v, 2) for v in g["center"]], "feet": [[round(x, 2), round(y, 2)] for x, y in g["feet"]],
                                "n": len(g["feet"]), "height_mm": H_PERSON_HERO})
    # 3 기록: 히어로 = 콜로세움 건물 ∪ 조경 광장(결정 D4). 건물 상자는 외벽 실루엣(기단 계단 0.62 높이 띠는 따로 적는다)
    bx_p = bbox_of(poly + [p for _r, q, _h, _e in paths for p in q])
    union = (min(bbox_b[0], bx_p[0]), min(bbox_b[1], bx_p[1]), max(bbox_b[2], bx_p[2]), max(bbox_b[3], bx_p[3]))
    record("hero", HERO_NAME, "Core(히어로)", sget(HLS, "screen_box", "reserve_box", default=[139.7, 226.4, 360.2, 381.6]), union,
           "콜로세움 건물 ∪ 조경 광장(받침 0)")
    wall_box = bbox_of([M(b["sc"] + x, 0.0, 0.0) for b in BAYS for x in (-CO_W / 2, 0.0, CO_W / 2)] +
                       [M(s, 0.0, z_wall(b, s, 1)) for b in BAYS for s in (b["s0"], b["sc"], b["s1"])])
    add_fp("콜로세움 건물", poly_b, "건물")
    add_fp("콜로세움 외벽", poly_b, "대상 면")
    add_fp("콜로세움 조경 광장", poly, "지면")
    for rid, q, hw, end in paths:
        add_fp("콜로세움 광장 문 길 " + rid, q, "지면")
    GEO["arena_top_y"] = lambda x: (None if top_y(x) is None else top_y(x))
    GEO["col_sil"] = poly_b
    ex_poly(poly, 0.3)
    ex_poly(poly_b, 1.5)
    for rid, q, hw, end in paths:
        ex_poly(q, 0.3)
    hc = _d5_height_check(crec["bays"])
    DRAWN["hypogeum"] = crec["hypogeum"]
    DRAWN["hero"] = {
        "rule": "결정 D2·D3·D4(기준선 8.1·8.2, 12:49 철회 반영): 받침 0, 콜로세움 건물 + 조경 광장. LocalBanana 조경 부품 배치 0",
        "building": {"box": [round(v, 2) for v in bbox_b], "wall_box": [round(v, 2) for v in wall_box], "w": round(wall_box[2] - wall_box[0], 2),
                     "h": round(wall_box[3] - wall_box[1], 2), "sil_area_mm2": round(area_b, 1), "decision_box": list(CO_BOX),
                     "plinth": "기단 계단 2단(d −2.6~0.2, z 0~0.62)은 건물 상자 밖 띠로 그렸다"},
        "ellipse": {"center_plan": list(CO_C), "center_screen": [round(CX_S, 2), round(CY_S, 2)], "semi_axes": [CO_A, CO_B], "major_az_deg": 315,
                    "bays": CO_NB, "bay_w": round(CO_W, 3), "wall_t": CO_T1, "corridor_w": CO_G1, "ring2_t": CO_T2, "story_z": [s_["z1"] for s_ in CO_ST]},
        "heights_check": hc, "heights_ok": all(v.get("ok", True) for v in hc.values()),
        "bays": crec["bays"], "cavea": crec["cavea"],
        "arena": {"semi_axes": list(CO_ARS), "wood_u_min": CO_US, "wood_z": CO_ZF, "wood_share": round((CO_ARS[0] - CO_US) / (2 * CO_ARS[0]), 3), "rail": True},
        "plaza": {"center_plan": list(LS_C), "reserve_r": LS_R, "box": [round(v, 2) for v in bbox_of(poly)], "trimmed": trims[:60], "trimmed_n": len(trims),
                  "rule": "rb(θ) = 84.5 + 3·sin(3θ+0.7) + 1.5·sin(7θ+0.2) ± 0.5(roma_pkg_hero.rb), 장애물과 2.2mm 이상이 되게 줄인 곳만 trimmed"},
        "gate_paths": [{"road": rid, "poly": [[round(x, 2), round(y, 2)] for x, y in q], "end_local": [round(v, 2) for v in end]} for rid, q, hw, end in paths],
        "trees": trees, "scatter_people": [[round(x, 2), round(y, 2)] for x, y in scat], "people_h_mm": H_PERSON_HERO,
        "union_box": [round(v, 2) for v in union], "union_area_mm2": round((union[2] - union[0]) * (union[3] - union[1]), 1),
        "removed": ["콜로세움 받침(팔각 판·지층 옆면)", "앞 변 기초 절개", "원형 고리·동심 관람석 그릇", "가로벽 격자 하이포게움"],
    }
    REPORT["objects"]["hero_building"] = {"이름": "콜로세움 건물(외벽 실루엣, 기단 계단 띠 제외)", "그린 외곽": [round(v, 1) for v in wall_box],
                                          "기단 계단 포함 외곽": [round(v, 1) for v in bbox_b], "실루엣 면적mm²": round(area_b, 1)}


# ───────────────────────── 6 지도 소품(사양 props 10 + 공사장) ─────────────────────────
def draw_kiln():
    d = PROPS["석회 가마"]
    m = Mesh(None)
    m.extend(m_cyl(0, 0, 7.4, 0, 10.4, (198, 172, 138), n=14, k=0.8))
    m.extend(m_cyl(0, 0, 6.0, 10.4, 11.4, (176, 150, 118), n=14, top=(70, 52, 40)))
    m.extend(m_box(8.0, -7.0, 0, 12.5, -2.5, 3.0, (232, 228, 214), top=(244, 242, 232)))
    m.extend(m_box(8.5, -2.0, 0, 11.5, 1.0, 2.0, (232, 228, 214), top=(244, 242, 232)))
    m.extend(m_mound(-8.0, -5.0, 0, 3.0, 2.4, (172, 166, 152), key="가마석회암"))
    m.extend(m_person(-6.0, 9.0, 0, H_PERSON / 0.8, CLOTHS[2], key="가마"))
    ox, oy, sc, zs, bb = fit_frame(mesh_pts(m) + [(0, 0, 19)], d["box"])
    iso = ZIso(P, ox, oy, sc, zs)
    m.draw(iso, lw=0.10)
    fx, fy = iso.p(5.6, 5.6, 0)
    P.pie(fx, fy - 2.0, 1.7, 2.2, 180, 360, fill=(70, 40, 26))
    P.rect(fx - 1.7, fy - 2.0, fx + 1.7, fy - 0.2, fill=(70, 40, 26))
    P.ell(fx, fy - 0.9, 0.9, 0.7, fill=(236, 120, 50))
    sx, sy = iso.p(0, 0, 12.0)
    for i in range(4):
        soft_ell(P, sx + i * 1.3, sy - i * 2.4, 2.4 - 0.2 * i, 1.7, (236, 232, 226), alpha=38, blur=0.8)
    REPORT["objects"]["석회 가마"] = {"사양 상자": d["box"], "그린 외곽": [round(v, 1) for v in bb]}


def draw_dock():
    d = PROPS["테베레 하역장"]
    yb = RIV_Y - RIV_HW1
    m = Mesh(None)
    m.extend(m_box(426.0, 296.0, -2.2, 474.5, yb - 0.1, 0.9, (186, 176, 156), top=(214, 206, 188)))
    m.extend(m_house(430.0, 283.0, 452.0, 294.0, 0, 6.0, 3.0, WALL_W, ROOF, axis="X"))
    m.extend(m_house(417.0, 287.0, 427.0, 295.0, 0, 4.4, 2.4, (226, 208, 176), ROOF, axis="Y"))
    m.extend(m_mound(435.0, 300.2, 0.9, 2.6, 2.4, LIME_W, key="부두석회"))
    m.extend(m_mound(440.5, 301.0, 0.9, 2.5, 2.2, ASH_R, key="부두화산재"))
    m.extend(m_mound(446.0, 300.4, 0.9, 2.3, 2.0, AGG_G, key="부두골재"))
    m.extend(m_amphorae(451.0, 299.2, n=5, key="부두암포라"))
    m.extend(m_cyl(472.0, 300.6, 0.45, 0.9, 13.0, WOOD, n=6))
    for (X, Y, c) in ((453.5, 302.0, 0), (438.0, 297.4, 4), (444.0, 303.2, 1)):
        m.extend(m_person(X, Y, 0.9, H_PERSON, CLOTHS[c], key="부두%d" % c))
    m.draw(ISO, lw=0.10)
    for X in range(429, 474, 3):
        ISO.line3([(X, 296.3, 0.92), (X, yb - 0.4, 0.92)], (198, 188, 168), 0.1)
    top = ISO.p(472.0, 300.6, 13.0)
    tip = ISO.p(472.0, 310.5, 11.6)
    P.line([top, tip], WOOD, 0.5, joint=False)
    P.line([tip, (tip[0], tip[1] + 6.4)], (90, 70, 50), 0.15, joint=False)
    P.rect(tip[0] - 1.2, tip[1] + 6.4, tip[0] + 1.2, tip[1] + 8.0, fill=LIME_W, outline=(150, 140, 120), lw=0.1)
    wheel = [ISO.p(468.2 + 3.0 * math.cos(math.radians(t)), 300.6, 4.2 + 3.0 * math.sin(math.radians(t))) for t in range(0, 361, 15)]
    P.line(wheel, (128, 92, 58), 0.4)
    c0 = ISO.p(468.2, 300.6, 4.2)
    for t in range(0, 180, 45):
        P.line([ISO.p(468.2 + 3.0 * math.cos(math.radians(t)), 300.6, 4.2 + 3.0 * math.sin(math.radians(t))),
                ISO.p(468.2 - 3.0 * math.cos(math.radians(t)), 300.6, 4.2 - 3.0 * math.sin(math.radians(t)))], (128, 92, 58), 0.15, joint=False)
    _ = c0
    pts = [ISO.p(*p) for p in mesh_pts(m)] + [top, tip, (tip[0], tip[1] + 8.0)]
    bb = bbox_of(pts)
    GEO["dock_bb"] = bb
    add_fp("하역장", [ISO.p(426.0, 296.0, 0.9), ISO.p(474.5, 296.0, 0.9), ISO.p(474.5, yb - 0.1, 0.9), ISO.p(426.0, yb - 0.1, 0.9)], "지면")
    add_fp("하역장 부두 면", [ISO.p(426.0, yb - 0.1, 0.9), ISO.p(474.5, yb - 0.1, 0.9), ISO.p(474.5, yb - 0.1, -2.2), ISO.p(426.0, yb - 0.1, -2.2)], "대상 면")
    REPORT["objects"]["테베레 하역장"] = {"사양 상자": d["box"], "그린 외곽": [round(v, 1) for v in bb]}


def draw_barge(d, axis, key):
    if axis == "X":
        hull = m_box(-12.0, -3.4, 0, 12.0, 3.4, 2.2, WOOD, top=WOOD_L)
        cargo = [(-6.0, -1.5), (-1.0, 1.5), (4.0, -1.2), (8.0, 1.4)]
    else:
        hull = m_box(-3.4, -12.0, 0, 3.4, 12.0, 2.2, WOOD, top=WOOD_L)
        cargo = [(-1.5, -6.0), (1.5, -1.0), (-1.2, 4.0), (1.4, 8.0)]
    m = Mesh(None)
    m.extend(hull)
    for i, (X, Y) in enumerate(cargo):
        col = LIME_W if i % 2 == 0 else ASH_R
        m.extend(m_box(X - 1.5, Y - 1.5, 2.2, X + 1.5, Y + 1.5, 4.0, col))
    if axis == "X":
        m.extend(m_person(-9.5, 0.5, 2.2, H_PERSON, CLOTHS[1], key=key))
    else:
        m.extend(m_person(0.5, -9.5, 2.2, H_PERSON, CLOTHS[1], key=key))
    bx0, by0, bx1, by1 = d["box"]
    cxs = (bx0 + bx1) / 2.0
    if axis == "X":
        Xp = cxs / C30 + RIV_Y
        Yp = RIV_Y
    else:
        Yp = RIV_XB - cxs / C30
        Xp = RIV_XB
    ox, oy = sp(Xp, Yp)
    iso = Iso(P, ox, oy)
    w0, w1 = (iso.p(13.5, 0), iso.p(26.0, 0)) if axis == "X" else (iso.p(0, -13.5), iso.p(0, -26.0))
    soft_line(P, [w0, w1], (255, 255, 255), alpha=70, w=4.0, blur=1.0)
    m.draw(iso, lw=0.10)
    pts = [iso.p(*p) for p in mesh_pts(m)]
    bb = bbox_of(pts)
    REPORT["objects"][key] = {"사양 상자": d["box"], "그린 외곽": [round(v, 1) for v in bb]}
    add_fp(key, _hull([iso.p(*p) for p in mesh_pts(hull)]), "대상 면")
    return bb


def draw_road_cart(d, key, Xr, Yr, axis="Y", load=LIME_W):
    m = m_cart(0, 0, axis, load, key=key)
    ox, oy = sp(Xr, Yr)
    iso = Iso(P, ox, oy)
    m.draw(iso, lw=0.10)
    wheels(iso, 0, 0, axis)
    pts = [iso.p(*p) for p in mesh_pts(m)]
    bb = bbox_of(pts)
    REPORT["objects"][key] = {"사양 상자": d["box"], "그린 외곽": [round(v, 1) for v in bb]}


WORKSITE_PLAN = (519.71, 260.29)    # 결정 D5: 공사장 지역 원점(Blender roma_pkg_hero.WORKSITE_PLAN, 축척 1.0) → ⑥ 도착점 (6.5, 9.0, 2.0) · Z1 출발점 (13, 4.5, 2.0)


def draw_worksite():
    """콜로세움 기초 공사장(나무 거푸집·다짐 일꾼·반죽 통·재료 더미). d5: 원점 고정(평면 (519.71, 260.29), 축척 1.0), 사람 키 4.9(결정 D8),
    '공사장 거푸집 오른쪽 면'(다져 넣은 층, 지역 X = 13) = 확대 창 Z1 지시선 출발점(결정 D5, 간격 0)"""
    ws = WS_SPEC
    box = ws["box"]
    m = Mesh(None)
    for (a, b, c, d_, e, f) in ((0, 0, 0, 13, 0.6, 4.0), (0, 8.4, 0, 13, 9.0, 4.0), (0, 0.6, 0, 0.6, 8.4, 4.0), (12.4, 0.6, 0, 13, 8.4, 4.0)):
        m.extend(m_box(a, b, c, d_, e, f, WOOD, top=WOOD_L))
    m.extend(m_box(0.6, 0.6, 0, 12.4, 8.4, 2.9, (176, 168, 154), top=(190, 182, 168)))
    m.extend(m_person(4.5, 3.6, 2.9, H_PERSON_HERO, CLOTHS[0], key="공사1"))
    m.extend(m_person(9.2, 5.8, 2.9, H_PERSON_HERO, CLOTHS[3], key="공사2"))
    m.extend(m_cyl(17.5, 2.6, 1.9, 0, 2.1, WOOD, n=10, top=(170, 164, 152)))
    m.extend(m_mound(16.0, 8.4, 0, 2.8, 2.5, LIME_W, key="공사석회"))
    m.extend(m_mound(20.6, 6.4, 0, 2.6, 2.3, ASH_R, key="공사화산재"))
    m.extend(m_mound(21.6, 1.6, 0, 2.2, 1.9, AGG_G, key="공사골재"))
    m.extend(m_person(15.0, 12.0, 0, H_PERSON_HERO, CLOTHS[2], key="공사3"))
    pad_ = [(-1, -1, 0), (24, -1, 0), (24, 14, 0), (-1, 14, 0)]
    pts = mesh_pts(m) + pad_
    org = tuple(sget(ws, "origin_plan", "local_origin_plan", default=None) or WORKSITE_PLAN)
    ox, oy = sp(float(org[0]), float(org[1]))
    sc, zs = 1.0, 1.0
    q_ = [(ox + C30 * (p_[0] - p_[1]), oy + 0.5 * (p_[0] + p_[1]) - (p_[2] if len(p_) > 2 else 0.0)) for p_ in pts]
    bb = bbox_of(q_)
    iso = ZIso(P, ox, oy, sc, zs)
    iso.poly3(pad_, fill=(214, 190, 150), ol=(184, 160, 120), lw=0.2)
    m.draw(iso, lw=0.10)
    for (X, Y) in ((4.5, 3.6), (9.2, 5.8)):                          # 다짐 막대
        a = iso.p(X + 0.8, Y + 0.8, 2.9 + 4.6)
        b = iso.p(X + 2.4, Y + 2.8, 2.95)
        P.line([a, b], (110, 80, 50), 0.4, joint=False)
    for zc in (0.9, 1.8, 2.7):                                       # 다져 넣은 층(바깥 널에 비치는 층 표시)
        P.line([iso.p(0.0, 9.02, zc), iso.p(13.0, 9.02, zc)], (130, 92, 58), 0.12, joint=False)
        P.line([iso.p(13.02, 0.0, zc), iso.p(13.02, 9.0, zc)], (120, 84, 52), 0.12, joint=False)
    GEO["worksite_bb"] = bb
    add_fp("공사장 받침", [iso.p(-1, -1, 0), iso.p(24, -1, 0), iso.p(24, 14, 0), iso.p(-1, 14, 0)], "지면")
    add_fp("공사장 거푸집 앞면", [iso.p(0, 9.0, 0), iso.p(13, 9.0, 0), iso.p(13, 9.0, 4.0), iso.p(0, 9.0, 4.0)], "대상 면")
    add_fp("공사장 거푸집 오른쪽 면", [iso.p(13.0, 0.0, 0), iso.p(13.0, 9.0, 0), iso.p(13.0, 9.0, 4.0), iso.p(13.0, 0.0, 4.0)], "대상 면")
    GEO["worksite_origin"] = (ox, oy)
    record("worksite", ws.get("name", "콜로세움 기초 공사장(복원 장면)"), "Core(히어로 소품)", box, bb)


def draw_ostia():
    d = PROPS["오스티아"]
    m = Mesh(None)
    m.extend(m_house(0, 0, 9, 5, 0, 3.6, 2.0, WALL_W, ROOF, axis="X"))
    m.extend(m_house(10.5, 1.0, 17, 6, 0, 3.0, 1.8, (226, 208, 176), ROOF, axis="Y"))
    m.extend(m_house(1.0, 7.0, 8.0, 12.0, 0, 3.2, 1.8, (230, 212, 182), (180, 86, 60), axis="X"))
    m.extend(m_box(9.5, 8.0, 0, 17.5, 8.8, 1.6, (200, 182, 148)))
    m.extend(m_pine(15.5, 12.5, 0, 9.0, 3.4, key="오스티아소나무"))
    m.extend(m_person(11.0, 11.0, 0, H_PERSON, CLOTHS[4], key="오스티아사람"))
    ox, oy, sc, zs, bb = fit_frame(mesh_pts(m), d["box"], sc_max=1.0)
    iso = ZIso(P, ox, oy, sc, zs)
    iso.poly3([(-1, -1, 0.02), (18.5, -1, 0.02), (18.5, 14, 0.02), (-1, 14, 0.02)], fill=(222, 204, 168), ol=(190, 170, 134), lw=0.15)
    m.draw(iso, lw=0.10)
    add_fp("오스티아", _hull([iso.p(*q) for q in mesh_pts(m)] + [iso.p(x_, y_, 0.0) for x_ in (-1, 18.5) for y_ in (-1, 14)]), "지면")
    REPORT["objects"]["오스티아"] = {"사양 상자": d["box"], "그린 외곽": [round(v, 1) for v in bb]}


def draw_villa():
    d = PROPS["교외 빌라"]
    m = Mesh(None)
    m.extend(m_house(0, 0, 10, 7, 0, 4.4, 2.4, (234, 220, 190), ROOF, axis="X"))
    m.extend(m_house(11, 1.5, 15.5, 5.5, 0, 2.8, 1.6, (226, 210, 178), (180, 86, 60), axis="Y"))
    m.extend(m_cypress(-2.5, 8.0, 0, 11.0, 1.4, key="빌라사이프러스"))
    m.extend(m_olive(13.0, 9.0, 0, 6.0, 2.2, key="빌라올리브"))
    ox, oy, sc, zs, bb = fit_frame(mesh_pts(m), d["box"], sc_max=1.0)
    iso = ZIso(P, ox, oy, sc, zs)
    m.draw(iso, lw=0.10)
    REPORT["objects"]["교외 빌라"] = {"사양 상자": d["box"], "그린 외곽": [round(v, 1) for v in bb]}


def draw_ash_ship():
    d = PROPS["화산재 운반선"]
    base = [(17, -3.6), (-13, -3.6), (-18, 0), (-13, 3.6), (17, 3.6), (18.5, 0)]
    m = Mesh(None)
    m.extend(m_prism(base, -0.6, 2.8, WOOD, top=WOOD_L))
    for i, X in enumerate((12, 7, 2, -4, -9)):
        m.extend(m_box(X - 1.8, -2.2, 2.8, X + 1.8, 2.2, 4.6, (150, 126, 104) if i % 2 else (168, 142, 116)))
    m.extend(m_cyl(-0.8, 0, 0.45, 2.8, 17.5, (120, 84, 50), n=6))
    sail = [(-1.2, -6.2, 7.0), (-1.2, 6.2, 7.0), (-1.2, 6.6, 16.6), (-1.2, -6.6, 16.6)]
    ox, oy, sc, zs, bb = fit_frame(mesh_pts(m) + sail, d["box"])
    iso = ZIso(P, ox, oy, sc, zs)
    soft_line(P, [iso.p(30, -2), iso.p(19, 0)], (255, 255, 255), alpha=90, w=2.6, blur=0.8)
    soft_line(P, [iso.p(30, 2.5), iso.p(19, 0)], (255, 255, 255), alpha=90, w=2.0, blur=0.8)
    m.draw(iso, lw=0.10)
    iso.poly3(sail, fill=(242, 232, 206), ol=(150, 130, 100), lw=0.15)
    iso.poly3([(-1.25, -6.3, 10.8), (-1.25, 6.3, 10.8), (-1.25, 6.4, 12.6), (-1.25, -6.4, 12.6)], fill=(196, 72, 60))
    iso.line3([(-1.3, -7.2, 16.8), (-1.3, 7.2, 16.8)], (110, 80, 50), 0.35)
    GEO["ship_top"] = iso.p(-0.8, 0, 17.5)
    GEO["ship_deck"] = iso.p(4.0, 0, 4.6)
    add_fp("선체", _hull([iso.p(x, y, z) for x, y in base for z in (-0.6, 2.8)]), "대상 면")
    REPORT["objects"]["화산재 운반선"] = {"사양 상자": d["box"], "그린 외곽": [round(v, 1) for v in bb]}


# ───────────────────────── 7 Detail: 확대 창 Z1 · 콜아웃 C1·C2·C4 · 지시선 ─────────────────────────
MARK_R = 2.0           # 짝 표지 원 반지름
MARK_FACE = 2.2        # 짝 표지 글자면(주석 최소 2.05 이상)
DETAIL_FILL = (253, 248, 236, 238)


def mark(x, y, letter, r=MARK_R, layer="짝 표지", source="map", origin=""):
    """짝 표지(A~D·1~4): 정보 잉크 원 Ø4 + 흰 글자 2.2. texts에 role 'mark'로 글자·중심·출처(map/detail/panel)를 남긴다"""
    P.ell(x, y, r, r, fill=INK_L, outline=(255, 255, 255), lw=0.25)
    f, em, fa = fface("b", MARK_FACE, letter)
    yb = y + fa / 2.0
    P.text(x, yb, letter, f, (255, 255, 255), anchor="ms")
    bb = f.getbbox(letter, anchor="ms")
    rec_text(letter, "mark", "b", em, fa, box_poly((x + bb[0] / KD, yb + bb[1] / KD, x + bb[2] / KD, yb + bb[3] / KD)), layer)
    DRAWN["texts"][-1].update({"mark": str(letter), "c": [round(x, 2), round(y, 2)], "source": source, "origin": origin, "d": 2.0 * r})
    return (x - r, y - r, x + r, y + r)


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
        ex = {"tol": tol_, "snap": snap_, "target": pm.get("target") or pm.get("map_target")}
        for kk, src in (("map_pt", "map"), ("map", "map"), ("map_c", "map"), ("panel_pt", "panel"), ("panel", "panel"), ("panel_c", "panel")):
            v = pm.get(kk)
            if isinstance(v, (list, tuple)) and len(v) == 2 and all(isinstance(t, (int, float)) for t in v):
                add(lt, v, "숫자 짝 %s(%s)" % (lt, src), src, ex if src == "map" else None)
        if isinstance(pm.get("pt"), (list, tuple)):
            add(lt, pm["pt"], "숫자 짝 %s" % lt, None, ex)


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
        mark(mk["c"][0], mk["c"][1], mk["letter"], layer="짝 표지 " + mk["source"], source=mk["source"], origin=mk["origin"])
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


def draw_z1():
    z = DMAP["Z1"]
    (cx, cy), d = z["circle"]["c"], z["circle"]["d"]
    r = d / 2.0
    sub = Layer(cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1)
    sub.ell(cx, cy, r, r, fill=MORTAR)
    rng = local_rng("확대창")
    for i in range(220):
        x = cx + (rng.random() * 2 - 1) * r
        y = cy + (rng.random() * 2 - 1) * r
        sub.ell(x, y, 0.3, 0.25, fill=(188, 176, 160) if i % 2 else (220, 210, 196))
    agg_cols = [(168, 136, 104), (186, 104, 78), (150, 146, 138), (112, 94, 84), (196, 160, 118), (204, 196, 170)]
    for i in range(26):
        ax_ = cx + (rng.random() * 2 - 1) * r * 0.95
        ay_ = cy + (rng.random() * 2 - 1) * r * 0.95
        rr = 2.4 + rng.random() * 4.4
        nv = 5 + int(rng.random() * 3)
        pts = []
        for j in range(nv):
            t = 2 * math.pi * j / nv + rng.random() * 0.5
            q = rr * (0.7 + rng.random() * 0.45)
            pts.append((ax_ + q * math.cos(t), ay_ + q * 0.85 * math.sin(t)))
        c = agg_cols[i % 6]
        sub.poly(pts, fill=c, outline=shade(c, 0.75), lw=0.15)
        if i % 6 == 5:                                                 # 경석(기공)
            for k in range(4):
                sub.ell(ax_ + (rng.random() - 0.5) * rr, ay_ + (rng.random() - 0.5) * rr * 0.8, 0.35, 0.3, fill=(170, 160, 136))
    clasts = [(-12, -10, 4.0), (9, -15, 3.0), (-4, 11, 4.6), (15, 7, 2.8), (-19, 12, 2.4), (2, -2, 2.2), (20, -6, 2.0), (6, 19, 2.6)]
    for (dx, dy, rr) in clasts:
        pts = [(cx + dx + rr * (0.86 + 0.14 * h01("알갱이", dx, j)) * math.cos(j * math.pi / 6), cy + dy + rr * 0.9 * math.sin(j * math.pi / 6)) for j in range(12)]
        sub.poly([(x + 0.5, y + 0.5) for x, y in pts], fill=(150, 140, 126))
        sub.poly(pts, fill=(253, 253, 248), outline=(198, 192, 180), lw=0.2)
        sub.ell(cx + dx - rr * 0.3, cy + dy - rr * 0.3, rr * 0.25, rr * 0.18, fill=(255, 255, 255))
    for i in range(14):
        sub.ell(cx + (rng.random() * 2 - 1) * r * 0.85, cy + (rng.random() * 2 - 1) * r * 0.85, 0.5, 0.4, fill=(120, 108, 96))
    mask = Image.new("L", (sub.w, sub.h), 0)
    ImageDraw.Draw(mask).ellipse([sub.X(cx - r), sub.Y(cy - r), sub.X(cx + r), sub.Y(cy + r)], fill=255)
    sub.img.putalpha(ImageChops.multiply(sub.img.getchannel("A"), mask))
    P.paste(sub)
    cap = "로마 콘크리트 단면 모식"
    cw = twf(cap, "m", 2.1)
    rrect(P, cx - cw / 2 - 1.6, cy + r - 9.7, cx + cw / 2 + 1.6, cy + r - 5.3, 1.2, fill=(252, 247, 236, 225))
    ptext(cx, cy + r - 6.3, cap, "m", 2.1, INK_L, "caption", anchor="c", layer="확대 창 Z1")
    P.ell(cx, cy, r, r, outline=INK_L, lw=0.6)                       # Z1 테두리 0.6mm(정보 잉크)
    P.ell(cx, cy, r - 0.8, r - 0.8, outline=(255, 248, 236), lw=0.3)
    INFO_POLYS.append(("Z1 확대 창", [(cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy + r)]))
    # 글 칸(사양 text_box): 제목 2.8 · 본문 2.6/3.9 · 주의 2.1/3.0. 바탕판·테두리 없이 지면 위에 조판
    x0, y0, x1, y1 = z1_text_box()
    W = x1 - x0
    title = z.get("title") or "콜로세움 기초 단면"
    yb = y0 + 3.0
    ptext(x0, yb, title, "b", 2.8, INK_L, "z1title", layer="확대 창 Z1 글 칸")
    body = []
    for s in print_texts(z):
        s = re.sub(r"^콜로세움:\s*", "", s)
        body += chunk_wrap(s, "m", 2.6, W)
    yb += 4.6
    yl = draw_lines(x0, yb, body, "m", 2.6, INK_L, "body", 3.9, "확대 창 Z1 글 칸")
    nt = print_note(z)
    if nt:
        draw_lines(x0, yl + 4.0, wrap(nt, "m", 2.1, W), "m", 2.1, NOTE_C, "note", 3.0, "확대 창 Z1 글 칸")
    INFO_POLYS.append(("Z1 글 칸", box_poly((x0, y0, x1, y1))))
    record("Z1", z["name"], "Detail", z["projected_box"], (cx - r, cy - r, cx + r, cy + r))
    DRAWN["boxes"].append({"id": "Z1 원", "kind": "확대 창", "tier": "Detail", "circle": {"c": [cx, cy], "d": d}, "border": True,
                           "box": [cx - r, cy - r, cx + r, cy + r]})
    DRAWN["boxes"].append({"id": "Z1 글 칸", "kind": "글 칸", "tier": "Detail", "box": [x0, y0, x1, y1], "border": False})
    DRAWN["boxes"].append({"id": "Z1 합성", "kind": "composite(원 + 글 칸)", "tier": "Detail", "box": list(z1_composite_box()), "border": False})


def callout_plate(d):
    box = d["box"]
    x0, y0, x1, y1 = box
    rrect(P, x0, y0, x1, y1, 1.6, fill=DETAIL_FILL, outline=INK_L + (255,), lw=0.25)   # 콜아웃 테두리 0.25mm(정보 잉크)
    mx, my = x0 + 3.0 + 1.2, y0 + 3.0 + 1.5
    if d.get("mark") and not d.get("mark_pt"):                       # 사양 mark_pt가 없으면 판 왼쪽 위(d3 자리), 있으면 MARKS가 그 자리에 그린다
        mark(mx, my, d["mark"], layer="콜아웃 " + d["id"], source="detail", origin=d["id"])
        MARKS.append({"letter": str(d["mark"]), "c": [mx, my], "source": "detail", "origin": d["id"], "drawn": True})
    title = d.get("title") or d["name"].split(":")[-1].strip()
    ptext(mx + MARK_R + 1.4, y0 + 6.1, title, "b", 2.8, INK_L, "callouttitle", layer="콜아웃 " + d["id"])
    INFO_POLYS.append(("콜아웃 " + d["id"], box_poly(box)))
    DRAWN["boxes"].append({"id": d["id"], "kind": "콜아웃", "tier": "Detail", "box": list(box), "border": True})
    return x0 + BOX_CLEAR, y0 + 6.1, x1 - BOX_CLEAR, y1 - BOX_CLEAR


def draw_c1():
    c = DMAP["C1"]
    lay = "콜아웃 C1"
    cx0, ty, cx1, cy1 = callout_plate(c)
    # 돔 단면 쐐기: 아래 무거운 돌 → 위 가벼운 돌(그림 왼쪽)
    R1, R2 = 15.5, 11.0
    ox, oy = cx0 + 0.5, ty + 5.0 + R1
    bands = [(0, 30, (226, 222, 210)), (30, 55, (176, 128, 96)), (55, 90, (214, 196, 128))]
    for (a0, a1, col) in bands:
        q = [(ox + R1 * math.cos(math.radians(a)), oy - R1 * math.sin(math.radians(a))) for a in range(a0, a1 + 1, 5)]
        q += [(ox + R2 * math.cos(math.radians(a)), oy - R2 * math.sin(math.radians(a))) for a in range(a1, a0 - 1, -5)]
        P.poly(q, fill=col, outline=(120, 100, 80), lw=0.15)
    rng = local_rng("C1골재")
    for i in range(24):
        a = rng.random() * 90
        rr = R2 + 0.6 + rng.random() * (R1 - R2 - 1.2)
        x, y = ox + rr * math.cos(math.radians(a)), oy - rr * math.sin(math.radians(a))
        P.ell(x, y, 0.4, 0.34, fill=(150, 146, 140) if a < 30 else ((150, 90, 66) if a < 55 else (186, 176, 150)))
    ax_ = ox + R1 + 1.6
    P.line([(ax_, oy - 1.0), (ax_, oy - R1 + 2.0)], INK_L, 0.3, joint=False)
    P.poly([(ax_ - 0.9, oy - R1 + 3.4), (ax_, oy - R1 + 1.4), (ax_ + 0.9, oy - R1 + 3.4)], fill=INK_L)
    ptext(ox, oy - R1 - 1.0, "가벼운 돌", "b", 2.1, INK_L, "caption", layer=lay)
    ptext(ox - 0.3, oy + 3.3, "무거운 돌(석회화)", "m", 2.1, INK_L, "caption", layer=lay)
    # 본문(사양 text, 2.6/3.9) — 그림 오른쪽 칸
    tx = ax_ + 2.6
    body = []
    for s in print_texts(c):
        body += chunk_wrap(s, "m", 2.6, cx1 - tx)
    yl = draw_lines(tx, ty + 5.4, body, "m", 2.6, INK_L, "body", 3.9, lay)
    nt = print_note(c)
    if nt:
        yn = max(yl, oy + 3.3) + 3.9
        draw_lines(cx0, yn, wrap(nt, "m", 2.1, cx1 - cx0), "m", 2.1, NOTE_C, "note", 3.0, lay)
    GEO["C1_bottom"] = max(yl, oy + 3.3) + (3.9 if nt else 0.0)


def draw_c2():
    c = DMAP["C2"]
    lay = "콜아웃 C2"
    cx0, ty, cx1, cy1 = callout_plate(c)
    body = []
    for s in print_texts(c):
        body += chunk_wrap(s, "m", 2.6, cx1 - cx0)
    nt = print_note(c)
    n_note = len(wrap(nt, "m", 2.1, cx1 - cx0)) if nt else 0
    text_h = 2.8 + (len(body) - 1) * 3.9 + (n_note * 3.0 + 1.0 if n_note else 0.0) + 0.7
    fig_h = max(2.4, min(9.0, cy1 - ty - 1.8 - text_h - 1.8))
    # 방파제 단면 + 바닷물 + 새로 자란 광물 결정(그림)
    fy0 = ty + 1.8
    P.rect(cx0, fy0 + fig_h * 0.3, cx1, fy0 + fig_h, fill=(150, 186, 210))
    for k in range(5):
        xx = cx0 + 2 + k * 9.6
        if xx + 2.4 < cx1:
            P.arc(xx, fy0 + fig_h * 0.32, 2.4, 0.8, 180, 360, (236, 246, 252), 0.3)
    P.poly([(cx0 + 7, fy0 + fig_h), (cx0 + 10, fy0 + 0.6), (cx1 - 15, fy0 + 0.6), (cx1 - 12, fy0 + fig_h)], fill=CONC2, outline=(96, 90, 80), lw=0.2)
    rng = local_rng("C2결정")
    for i in range(16):
        x = cx0 + 11 + rng.random() * (cx1 - cx0 - 27)
        y = fy0 + 1.6 + rng.random() * (fig_h - 2.6)
        if i % 2:
            P.poly([(x - 0.9, y), (x - 0.45, y - 0.7), (x + 0.45, y - 0.7), (x + 0.9, y), (x + 0.45, y + 0.7), (x - 0.45, y + 0.7)], fill=(250, 250, 246), outline=(170, 166, 156), lw=0.10)
        else:
            P.ell(x, y, 0.5, 0.5, fill=(236, 228, 210), outline=(170, 160, 140), lw=0.10)
    ptext(cx1, fy0 + fig_h - 1.0, "바닷물", "b", 2.1, (40, 80, 110), "caption", anchor="r", layer=lay)
    yb = fy0 + fig_h + 1.8 + 2.8
    yl = draw_lines(cx0, yb, body, "m", 2.6, INK_L, "body", 3.9, lay)
    if nt:
        draw_lines(cx0, yl + 4.0, wrap(nt, "m", 2.1, cx1 - cx0), "m", 2.1, NOTE_C, "note", 3.0, lay)


def micro_cell(x, y, s, stage):
    """C4 미시 도해 한 칸(정면). stage 1 = 젖은 벽에서 류사이트 결정이 녹아 나옴, 2 = 접합부 결정이 다시 짜임"""
    P.rect(x, y, x + s, y + s, fill=(214, 204, 188), outline=(120, 104, 84), lw=0.2)
    grains = [(0.26, 0.34, 0.2), (0.72, 0.30, 0.17), (0.30, 0.76, 0.18), (0.74, 0.74, 0.19)]
    for (gx, gy, gr) in grains:                                     # 화산재·골재 알갱이
        cxg, cyg = x + gx * s, y + gy * s
        P.poly([(cxg + gr * s * math.cos(t * 1.05), cyg + gr * s * 0.86 * math.sin(t * 1.05)) for t in range(6)], fill=(150, 132, 112), outline=(110, 94, 78), lw=0.1)
    jx, jy = x + 0.5 * s, y + 0.52 * s                              # 접합부(가운데)
    if stage == 1:
        for k in range(4):                                           # 젖은 벽: 물방울
            P.ell(x + s * (0.2 + 0.2 * k), y + 1.2, 0.36, 0.48, fill=(80, 150, 206))
        P.poly([(jx - 1.4, jy), (jx - 0.7, jy - 1.2), (jx + 0.7, jy - 1.2), (jx + 1.4, jy), (jx + 0.7, jy + 1.2), (jx - 0.7, jy + 1.2)],
               fill=(246, 244, 236), outline=(160, 156, 146), lw=0.1)  # 류사이트 결정
        for k in range(7):                                           # 녹아 나오는 성분(점)
            a = k * 0.9
            P.ell(jx + 2.4 * math.cos(a), jy + 2.0 * math.sin(a), 0.22, 0.22, fill=(236, 234, 226))
    else:
        for k in range(9):                                           # 접합부를 다시 짠 결정 섬유
            a = k * math.pi / 9
            P.line([(jx - 2.6 * math.cos(a), jy - 2.2 * math.sin(a)), (jx + 2.6 * math.cos(a), jy + 2.2 * math.sin(a))], (250, 250, 246), 0.22, joint=False)
        P.poly([(jx - 0.8, jy + 2.9), (jx + 0.8, jy + 2.9), (jx, jy + 1.9)], fill=INK_L)   # 접합부 표지(작은 삼각)


def draw_c4():
    c = DMAP["C4"]
    lay = "콜아웃 C4"
    cx0, ty, cx1, cy1 = callout_plate(c)
    fig = c.get("figure") or {}
    dd = float(fig.get("drum_d", 12.0))
    cs = (fig.get("micro_cell_mm") or [14.0, 14.0])[0]
    arw = float(fig.get("arrow_mm", 2.0))
    fy0 = ty + 2.2
    # 드럼 단면 모식 Ø12: 벽돌 겉면 · 콘크리트 속 · 응회암 보강
    R = dd / 2.0
    dcx, dcy = cx0 + R, fy0 + cs / 2.0
    P.ell(dcx, dcy, R, R, fill=BRICK, outline=(110, 60, 44), lw=0.2)
    P.ell(dcx, dcy, R - 0.9, R - 0.9, fill=CONC2)
    for k in range(10):
        a = math.radians(k * 36 + 8)
        x, y = dcx + (R - 2.0) * math.cos(a), dcy + (R - 2.0) * math.sin(a)
        P.rect(x - 0.7, y - 0.5, x + 0.7, y + 0.5, fill=TUFF, outline=(120, 96, 70), lw=0.10)
    P.ell(dcx, dcy, R - 3.4, R - 3.4, fill=(196, 186, 168))
    # 미시 도해 2칸 + 사이 화살표 2mm
    x1c = dcx + R + 2.0
    micro_cell(x1c, fy0, cs, 1)
    ax0 = x1c + cs + 1.0
    P.line([(ax0, fy0 + cs / 2), (ax0 + arw - 0.6, fy0 + cs / 2)], INK_L, 0.3, joint=False)
    P.poly([(ax0 + arw - 0.9, fy0 + cs / 2 - 0.7), (ax0 + arw, fy0 + cs / 2), (ax0 + arw - 0.9, fy0 + cs / 2 + 0.7)], fill=INK_L)
    x2c = ax0 + arw + 1.0
    micro_cell(x2c, fy0, cs, 2)
    caps = fig.get("captions") or ["류사이트 용출", "접합부 재편"]
    ptext(x1c + cs / 2, fy0 + cs + 3.0, caps[0], "m", 2.1, INK_L, "caption", anchor="c", layer=lay)
    ptext(x2c + cs / 2, fy0 + cs + 3.0, caps[1], "m", 2.1, INK_L, "caption", anchor="c", layer=lay)
    body = []
    for s in print_texts(c):
        body += chunk_wrap(s, "m", 2.6, cx1 - cx0)
    yl = draw_lines(cx0, fy0 + cs + 3.0 + 4.6, body, "m", 2.6, INK_L, "body", 3.9, lay)
    nt = print_note(c)
    if nt:
        draw_lines(cx0, yl + 4.0, wrap(nt, "m", 2.1, cx1 - cx0), "m", 2.1, NOTE_C, "note", 3.0, lay)


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
LABEL_ORDER = ["콜로세움", "카라칼라 욕장", "트라야누스 시장", "판테온", "수도교", "카이킬리아 메텔라 무덤", "포르투스 항",
               "막센티우스 바실리카", "네로 거상", "마르켈루스 극장", "하드리아누스 영묘",
               "베수비오", "바지선", "화산재 운반선", "테베레 하역장·석회 가마", "콜로세움 공사장"]
LF_PROP, LF_PROP_PITCH = 2.6, 3.9     # 소품 주석(새 종류, d4): 글자면 2.6 고정, 정보 잉크, 말풍선 없음
# 지시선 문법(사양 lead 문장을 렌더 동작으로 옮긴 것): (방식, 쪽, 대상 지면 다각형 이름)
LEAD_RULE = {
    "콜로세움": ("vertical", "R", "콜로세움 외벽"),
    "카라칼라 욕장": ("extend", "R", "욕장 왼쪽 벽 윗면"),
    "트라야누스 시장": ("extend", "L", "시장 오른쪽 동 끝면"),
    "판테온": ("extend", "R", "판테온 돔"),
    "수도교": ("vertical", "R", "수도교 아치 면"),
    "카이킬리아 메텔라 무덤": ("vertical", "L", "메텔라 기단"),
    "포르투스 항": ("vertical2", "R", "포르투스 외항 방파제"),
    "베수비오": ("extend", "R", "베수비오"),                    # d4: 깃대형 → 브래킷(산 왼쪽 비탈)
    "바지선": ("flag", "L", "바지선 1"),
    "화산재 운반선": ("flag", "L", "선체"),                      # d4: 규선 연장형 → 깃대형(x 144.25 수직)
    "막센티우스 바실리카": ("extend_v30", "R", "바실리카 측랑 볼트"),
    "네로 거상": ("ray_dr", "R", "네로 거상"),
    "마르켈루스 극장": ("extend", "R", "극장 반원 아케이드"),
    "하드리아누스 영묘": ("ray_ul", "L", "영묘 기단 윗면"),
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
    "콜로세움": (["COLOSSEUM"], "콜로세움", "Amphitheatrum Flavium"), "판테온": (["PANTHEON"], "판테온", None),
    "카라칼라 욕장": (["BATHS OF CARACALLA"], "카라칼라 욕장", "Thermae Antoninianae"),
    "트라야누스 시장": (["TRAJAN'S MARKETS"], "트라야누스 시장", "Mercati di Traiano"), "수도교": (["AQUEDUCT"], "수도교", "Aqua Antoniniana"),
    "카이킬리아 메텔라 무덤": (["CAECILIA METELLA"], "카이킬리아 메텔라 무덤", None), "포르투스 항": (["PORTUS"], "포르투스 항", "Portus"),
    "베수비오": (["VESUVIUS"], "베수비오", None), "바지선": (["BARGE"], "바지선", None), "화산재 운반선": (["ASH SHIP"], "화산재 운반선", None),
    "막센티우스 바실리카": (["BASILICA OF MAXENTIUS"], "막센티우스 바실리카", "Basilica Nova"),
    "마르켈루스 극장": (["THEATRE OF", "MARCELLUS"], "마르켈루스 극장", None),
    "하드리아누스 영묘": (["MAUSOLEUM OF", "HADRIAN"], "하드리아누스 영묘", None),
}
TAG_TEXT_FALLBACK = {"테베레 하역장·석회 가마": "하역장·석회 가마", "콜로세움 공사장": "공사장 · ⑤ 다져 넣기"}


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
    for i, t_ in enumerate(lines_):
        lines.append((t_, fk_, LF_PROP, 0.0, v + i * LF_PROP_PITCH, "prop_label"))
    W = max(twf(t_, fk_, LF_PROP) for t_ in lines_) if lines_ else 1.0
    H = v + LF_PROP_PITCH * (len(lines_) - 1) + 0.7
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
        for r in CM["roads"]:
            for b in road_bands(r):
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
            return False
    for l_ in PLACED_LEADS:
        if _poly_dist(l_, pts, False, False) < 0.6:
            return False
    for _n, pg in INFO_BOXES:
        if _poly_dist(pg, pts, True, False) < 0.3:
            return False
    return True


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
                if LEAD_RULE.get(key) and ld is None:
                    continue
                if ld and not _lead_ok(ld[0], poly):
                    continue
                if ld and ld[2] > 0.5:
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
        REPORT["notes"].append("라벨 자리 없음: %s" % key)
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
    x0, y0, x1, y1 = FR["title"]["rect"]
    pr = FR["title"].get("print") or ["CITY LANDMARK INFOGRAPHICS · ROMA", "ROMAN CONCRETE", "로마 콘크리트", "로마 건축물로 읽는 로마 콘크리트"]
    band, main_t, sub_t, line_t = (pr + [""] * 4)[:4]
    cx = (x0 + x1) / 2.0
    red = ACCENT
    P.rect(x0 + 2, y1 - 7.6, x1 - 2, y1 - 3.8, fill=(246, 228, 216), outline=red, lw=0.4)
    P.rect(x0, y1 - 3.8, x1, y1, fill=(240, 218, 204), outline=red, lw=0.4)
    cy0, cy1 = y0 + 40.0, y1 - 7.6
    for i in range(8):
        x = x0 + 13.0 + i * (x1 - x0 - 26.0) / 7.0
        P.rect(x - 2.9, cy0 + 2.4, x + 2.9, cy1 - 1.4, fill=(252, 238, 230), outline=red, lw=0.35)
        for dx in (-1.3, 0.0, 1.3):
            P.line([(x + dx, cy0 + 3.4), (x + dx, cy1 - 2.4)], (236, 196, 196), 0.18, joint=False)
        P.rect(x - 3.9, cy0, x + 3.9, cy0 + 2.4, fill=(246, 226, 218), outline=red, lw=0.3)
        P.rect(x - 3.9, cy1 - 1.4, x + 3.9, cy1, fill=(246, 226, 218), outline=red, lw=0.3)
    P.rect(x0 + 4, y0 + 30.5, x1 - 4, y0 + 40.0, fill=(250, 236, 228), outline=red, lw=0.5)
    if band:
        ptext(cx, y0 + 37.4, band, "en", 3.56, red, "title_band", anchor="c", layer="타이틀")
    P.poly([(x0 + 2, y0 + 30.5), (cx, y0 + 1.0), (x1 - 2, y0 + 30.5)], fill=(252, 242, 234), outline=red, lw=0.6)
    P.poly([(x0 + 16, y0 + 28.0), (cx, y0 + 6.2), (x1 - 16, y0 + 28.0)], outline=(226, 150, 150), lw=0.3)
    P.ell(cx, y0 + 17.0, 3.0, 3.0, outline=red, lw=0.45)
    P.rect(cx - 52, y0 + 44.0, cx + 52, y0 + 66.0, fill=(253, 247, 240), outline=red, lw=0.6)
    if main_t:
        ptext(cx, y0 + 57.0, main_t, "en", 9.26, red, "title_main", anchor="c", layer="타이틀")
    if sub_t:
        ptext(cx, y0 + 63.4, sub_t, "b", 3.05, red, "title_sub", anchor="c", layer="타이틀")
    P.rect(cx - 60, y0 + 67.6, cx + 60, y0 + 73.4, fill=(250, 230, 228), outline=red, lw=0.4)
    if line_t:
        ptext(cx, y0 + 71.9, line_t, "b", 2.61, red, "title_line", anchor="c", layer="타이틀")


def panel_header(x0, y0, en, ko, en_face=7.4, ko_face=3.7, panel="", col=ACCENT):
    """패널 머리글: 영문 초압축 대문자 + 국문, 윗선 정렬(강조색 한 색)"""
    yb = y0 + 2.4 + en_face
    box, fa = ptext(x0 + 2.0, yb, en, "en", en_face, col, "head_en", layer="패널 " + panel, panel=panel)
    fk = fface("b", ko_face, ko)[2]
    kb = (yb - fa) + fk * (0.812 / 0.870)
    ptext(box[2] + 2.0, kb, ko, "b", ko_face, col, "head_ko", layer="패널 " + panel, panel=panel)
    return yb


def draw_panel_L():
    x0, y0, x1, y1 = PANEL["L"]["rect"]
    lay = "패널 L"
    yb = panel_header(x0, y0, "ROMAN CONCRETE?", "로마 콘크리트란?", panel="L")
    defs = ["생석회와 화산재가 물과 반응해 굳는 반죽에", "돌·벽돌 조각(골재)을 다져 넣은 로마 건축 재료.", "철근 없이 돔·볼트·방파제를 지었다."]
    draw_lines(x0 + 2.2, yb + 5.4, wrap_all(defs, "m", 2.6, x1 - x0 - 4.4), "m", 2.6, INK_L, "body", 3.9, lay)
    items = [("생석회", ["석회암을 구운 것"]), ("화산재", ["시내 = 알바노 구릉", "바다 = 포추올리"]),
             ("골재", ["응회암·벽돌·", "경석 조각"]), ("물", ["육상 = 민물", "바다 공사 = 바닷물"])]
    for i, (name, sub) in enumerate(items):
        cx = x0 + 13.0 + i * 24.6
        iso = Iso(P, cx, y0 + 38.5)
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
        ptext(cx, y0 + 47.2, name, "b", 2.8, INK_L, "subtitle", anchor="c", layer=lay)
        draw_lines(cx, y0 + 50.8, sub, "m", 2.1, INK_L, "iconcaption", 3.0, lay, anchor="c")
    P.line([(x0 + 2.2, y0 + 57.8), (x1 - 2.2, y0 + 57.8)], (176, 156, 120), 0.25, joint=False)
    ptext(x0 + 2.2, y0 + 63.4, "섞는 순서가 열쇠 → 아래 '제작 과정'", "b", 2.6, INK_L, "body", layer=lay)


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
    x0, y0, x1, y1 = PANEL["B"]["rect"]
    lay = "패널 B"
    panel_header(x0, y0, "HOW IT WAS MADE", "로마 콘크리트 제작 과정", panel="B")
    names = ["재료 준비", "마른 혼합", "물 붓기", "뜨거운 혼합", "다져 넣기", "굳기·석회 알갱이"]
    notes = [["생석회·화산재·골재", "강·길로 들어온 재료"], ["물 없이 먼저 섞기", "(2025 폼페이: 미리 섞은 더미)"],
             ["육상 건물은 민물", "(바닷물은 항구 구조물만)"], ["끓어오르며 열·김", "흰 석회 알갱이가 남는다"],
             ["거푸집에 층층이", "다져 넣는다(붓지 않음)"], ["굳은 단면 속 흰 알갱이", "→ 콜로세움 기초·볼트"]]
    cw, gap = 30.6, 1.6
    tile_sc = 13.0 / 15.0                                           # 장면 타일 15 → 13mm(설명 3줄 자리)
    for i in range(6):
        cl = x0 + 2.0 + i * (cw + gap)
        cxm = cl + cw / 2.0
        iso = ZIso(P, cxm, y0 + 17.4, sc=tile_sc)
        scene_tile(iso)
        draw_scene(i + 1, iso)
        P.ell(cl + 2.9, y0 + 15.0, 2.6, 2.6, fill=ACCENT, outline=(255, 255, 255), lw=0.3)
        ptext(cl + 2.9, y0 + 15.0 + 1.2, str(i + 1), "b", 2.4, (255, 255, 255), "number", anchor="c", layer=lay)
        ptext(cxm, y0 + 36.4, names[i], "b", 3.0, INK_L, "step", anchor="c", layer=lay)
        lines = wrap_all(notes[i], "m", 2.6, cw - 1.0)[:3]
        draw_lines(cxm, y0 + 40.6, lines, "m", 2.6, INK_L, "body", 3.9, lay, anchor="c")
        if i < 5:
            ax_ = cl + cw + gap / 2.0
            ay_ = y0 + 25.4
            P.poly([(ax_ - 1.6, ay_ - 0.8), (ax_ + 0.2, ay_ - 0.8), (ax_ + 0.2, ay_ - 1.7), (ax_ + 1.9, ay_), (ax_ + 0.2, ay_ + 1.7), (ax_ + 0.2, ay_ + 0.8), (ax_ - 1.6, ay_ + 0.8)],
                   fill=BROWN_A)
    ty_ = y0 + 53.6
    P.line([(x0 + 3.0, ty_), (x0 + 150.0, ty_)], BROWN_A, 0.35, joint=False)
    P.poly([(x0 + 150.0, ty_ - 1.2), (x0 + 153.4, ty_), (x0 + 150.0, ty_ + 1.2)], fill=BROWN_A)
    ptext(x0 + 155.0, ty_ + 0.8, "시간 → 콜로세움 완공", "b", 2.1, BROWN_A, "timearrow", layer=lay)


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


def draw_panel_D():
    x0, y0, x1, y1 = PANEL["D"]["rect"]
    lay = "패널 D"
    mp = PANEL["D"].get("mark_pt")
    xh = (mp[0] + MARK_R + 2.5) if mp else x0 + 2.0                  # 'Ⓐ LIME CLASTS': 짝 표지 A(MARKS) 다음 x 228.5부터
    panel_header_at(xh, y0, "LIME CLASTS", "석회 알갱이·자가치유", 7.4, 3.6, panel="D", x_max=x1)
    caps = [("(가) 뜨거운 혼합", ["생석회 + 물 → 열,", "흰 알갱이가 남는다"]), ("(나) 균열", ["금이 가며", "알갱이를 지난다"]),
            ("(다) 빗물", ["빗물이 스며 알갱이의", "칼슘이 녹아 나온다"]), ("(라) 결정 봉합", ["탄산칼슘 결정이", "틈을 메운다"])]
    s = 13.4
    for i, (t, ls) in enumerate(caps):
        gx, gy = i % 2, i // 2
        bx = x0 + 2.4 + gx * 42.0
        by = y0 + 12.6 + gy * 15.4
        lime_sq(bx, by, s, i + 1)
        ptext(bx + s + 1.6, by + 3.0, t, "b", 2.8, INK_L, "subtitle", layer=lay)
        lines = wrap_all(ls, "m", 2.6, 42.0 - s - 1.6 - 0.2)
        draw_lines(bx + s + 1.6, by + 6.9, lines, "m", 2.6, INK_L, "body", 3.9, lay)
        if gx == 0:
            P.poly([(bx + 39.6, by + s / 2 - 1.0), (bx + 41.4, by + s / 2), (bx + 39.6, by + s / 2 + 1.0)], fill=BROWN_A)
    src = wrap("2023 MIT 연구(프리베르눔 시료)가 실마리를 찾고, 2025 폼페이 공사 현장 연구가 확인했다", "m", 2.6, x1 - x0 - 4.8)
    draw_lines(x0 + 2.4, y1 - 4.6 - 3.9 * (len(src) - 1), src, "m", 2.6, INK_L, "body", 3.9, lay)


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
                        "figure_box": c.get("figure_box")} for c in pn["cells"]]
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
    """P2 'ARCH · VAULT · DOME 아치·볼트·돔'(옛 위치도 자리, 상자·배경판 없음): 머리글 y 21~29, 등각 단면 4칸(23×30, y 32~62),
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
    panel_header_at(x0, y0, pr.get("head_en") or "ARCH · VAULT · DOME", pr.get("head_ko") or "아치·볼트·돔", 7.4, 3.8, panel="P2", x_max=x1,
                    baseline=float(hb_) if hb_ is not None else y0 + 9.0)
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
        fb = c.get("figure_box")
        caps = wrap_all(c.get("caption") or [], "m", 2.1, cw)[:2]
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
    bars = pr.get("span_bars") or [{"text": "트라야누스 시장 대회랑 8.6 m", "m": 8.6}, {"text": "카라칼라 열탕실 약 36 m", "m": 36.0}, {"text": "판테온 43.3 m", "m": 43.3}]
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
    """P5 'LEARNING FROM ROME 지금 배우는 중'(결정 D15, 상자·배경판·채움판 0, 사투영 0): 머리글 → 세 칸(연구 → 현장 → 적용, 사양 상자·기준선)
    → 칸 아래 계단 꺾은선(사양 stair_figure.line, 0.35mm, BROWN_A) + 끝 화살촉 + 칸 사이 화살촉(폭 1.6) → 두 칸(가져올 것 / 못 가져올 것) → 탄소 한 줄.
    글 뒤는 띠 바탕이다. 본문 줄이 사양 폭을 넘으면 낱말 경계에서만 다시 끊는다(줄 수 유지)."""
    pn = PANEL.get("P5")
    if not pn:
        return
    x0, y0, x1, y1 = pn["rect"]
    lay = "패널 P5"
    pr = _p5_print(pn)
    stx = pn.get("stair_text") or {}
    tf_ = float(stx.get("title_face", 2.8))
    bf_ = float(stx.get("body_face", 2.6))
    pitch = float(stx.get("pitch", 3.9))
    maxw = float(stx.get("max_w", 28.2))
    panel_header_at(x0, y0, pr.get("head_en") or "LEARNING FROM ROME", pr.get("head_ko") or "지금 배우는 중", 7.4, 3.6, panel="P5", x_max=x1)
    p5txt = []
    st_rec = []
    for i, st in enumerate((pn.get("stairs") or [])[:3]):
        bx = st.get("box") or [x0 + i * 30.65, 520.0, x0 + i * 30.65 + 28.7, 542.0]
        tby = float(st.get("title_baseline_y", 524.0))
        bys = [float(v) for v in (st.get("body_baselines_y") or [])]
        body = list(st.get("body") or [])
        lines, rebroke = _fit_lines(body, maxw, "m", bf_)
        if bys and len(lines) > len(bys):
            lines = lines[:len(bys)]
        b_, _fa = ptext(bx[0], tby, st.get("title") or st.get("key", ""), "b", tf_, INK_L, "subtitle" if tf_ < 2.9 else "step", layer=lay)
        p5txt.append(b_)
        for k, ln in enumerate(lines):
            yb_ = bys[k] if k < len(bys) else (bys[-1] if bys else tby + 4.0) + pitch * (k - len(bys) + 1)
            b_, _fa = ptext(bx[0], yb_, ln, "m", bf_, INK_L, "body", layer=lay, pitch=pitch if len(lines) > 1 else None)
            p5txt.append(b_)
        st_rec.append({"step": st.get("title"), "box": list(bx), "lines": lines, "rebroken": rebroke,
                       "max_line_w": round(max(twf(s, "m", bf_) for s in lines), 2) if lines else 0.0})
    sf = pn.get("stair_figure") or {}
    line = [tuple(p) for p in (sf.get("line") or [])]
    lw = max(0.35, float(sf.get("lw", 0.35)))
    figs = []
    if len(line) >= 2:
        P.line(line, BROWN_A, lw, joint=False)                                  # 계단 꺾은선(채움판 0)
        figs.append(("계단선", line))
        tip = tuple(sf.get("arrow_tip") or (line[-1][0] + 2.0, line[-1][1]))
        bx_, by_ = line[-1]
        ux, uy = tip[0] - bx_, tip[1] - by_
        ln_ = math.hypot(ux, uy) or 1.0
        ux, uy = ux / ln_, uy / ln_
        tri = [(bx_ - uy * 0.85, by_ + ux * 0.85), tip, (bx_ + uy * 0.85, by_ - ux * 0.85)]
        P.poly(tri, fill=BROWN_A)
        figs.append(("끝 화살촉", tri))
    aw = float(sf.get("step_arrow_w", 1.6))
    for (ax_, ay_) in (sf.get("step_arrows") or []):                          # 칸 사이 화살촉(→, 폭 1.6)
        tri = [(ax_ - aw / 2.0, ay_ - 0.7), (ax_ + aw / 2.0, ay_), (ax_ - aw / 2.0, ay_ + 0.7)]
        P.poly(tri, fill=BROWN_A)
        figs.append(("칸 사이 화살촉", tri))
    cols = pr.get("cells") or []
    cells_sp = pn.get("cells") or []
    ct = pn.get("cell_text") or {}
    cbf = float(ct.get("body_face", 2.6))
    cpitch = float(ct.get("pitch", 3.9))
    for j, cc in enumerate(cols[:2]):
        csp = cells_sp[j] if j < len(cells_sp) else {}
        cb = csp.get("box") or [x0 + j * 46.0, 547.0, x0 + j * 46.0 + 44.0, 562.5]
        tbx = float(csp.get("title_x", cb[0] + 3.4))
        tby = float(csp.get("title_baseline_y", cb[1] + 2.6))
        bys = [float(v) for v in (csp.get("body_baselines_y") or [tby + 3.9, tby + 7.8, tby + 11.7])]
        if cc.get("icon"):                                                      # ○ 가져올 것 · × 못 가져올 것(정보 잉크 2.4mm, 선 0.3)
            ic_x, ic_y = cb[0] + 1.2, tby - 1.3
            if "×" in str(cc["icon"]):
                P.line([(ic_x - 1.0, ic_y - 1.0), (ic_x + 1.0, ic_y + 1.0)], INK_L, 0.3, joint=False)
                P.line([(ic_x - 1.0, ic_y + 1.0), (ic_x + 1.0, ic_y - 1.0)], INK_L, 0.3, joint=False)
            else:
                P.ell(ic_x, ic_y, 1.05, 1.05, outline=INK_L, lw=0.3)
            figs.append(("아이콘 %d" % j, [(ic_x - 1.2, ic_y - 1.2), (ic_x + 1.2, ic_y - 1.2), (ic_x + 1.2, ic_y + 1.2), (ic_x - 1.2, ic_y + 1.2)]))
        b_, _fa = ptext(tbx, tby, cc["title"], "b", 2.8, INK_L, "subtitle", layer=lay)
        p5txt.append(b_)
        items = cc["items"]
        for k, it in enumerate(items[:len(bys)]):
            yy = bys[k]
            if j == 0:
                P.ell(cb[0] + 0.8, yy - 1.0, 0.55, 0.55, fill=INK_L)
            else:
                P.ell(cb[0] + 0.8, yy - 1.0, 0.55, 0.55, outline=INK_L, lw=0.2)
            b_, _fa = ptext(cb[0] + 2.2, yy, it, "m", cbf, INK_L, "body", layer=lay, pitch=cpitch if len(items) > 1 else None)
            p5txt.append(b_)
    dv = _parse_divider(ct.get("divider"))
    if dv:                                                                      # 두 칸 사이 가름선(0.25)
        P.line([(dv[0], dv[1]), (dv[0], dv[2])], (176, 156, 120), 0.25, joint=False)
        figs.append(("가름선", [(dv[0], dv[1]), (dv[0], dv[2])]))
    cbn = pn.get("carbon") if isinstance(pn.get("carbon"), dict) else {}
    b_, _fa = ptext(float(cbn.get("x", x0)), float(cbn.get("baseline_y", y1 - 1.4)), pr.get("carbon") or "탄소: 만들 때 배출은 비슷하거나 더 크고, 오래 쓸수록 이득이다",
                    "m", float(cbn.get("face", 2.1)), INK_L, "footnote", layer=lay)
    p5txt.append(b_)
    clear, clear_a = None, None
    for tb_ in p5txt:                                                           # 글자 상자 ↔ 도식 선 최소 간격(결정: ≥ 1.5mm)
        tp = box_poly(tb_)
        for nm, pg in figs:
            d_ = _poly_dist(tp, pg, True, nm not in ("계단선", "가름선"))
            if nm.startswith("칸 사이") or nm.startswith("아이콘"):
                if clear_a is None or d_ < clear_a[0]:
                    clear_a = (d_, nm, [round(v, 2) for v in tb_])
                continue
            if clear is None or d_ < clear[0]:
                clear = (d_, nm, [round(v, 2) for v in tb_])
    DRAWN["p5"] = {"steps": st_rec, "cells": [c_["title"] for c_ in cols[:2]], "stair_line": [[round(x, 2), round(y, 2)] for x, y in line],
                   "stair_lw": lw, "fill_plates": 0, "oblique": 0,
                   "text_line_clear_mm": round(clear[0], 2) if clear else None, "text_line_clear_at": clear[1:] if clear else None,
                   "text_marker_clear_mm": round(clear_a[0], 2) if clear_a else None, "text_marker_clear_at": clear_a[1:] if clear_a else None,
                   "marker_note": "칸 사이 화살촉(사양 자리, 폭 1.6)은 칸 사이 1.95mm에 들어 칸 이름과 약 0.2mm다(결정 D15 자리 그대로)"}


def draw_panel_S():
    pn = PANEL["S"]
    x0, y0, x1, y1 = pn["rect"]
    lay = "패널 S"
    panel_header(x0, y0, "100 VS 2,000", "콘크리트 수명", en_face=5.0, ko_face=2.8, panel="S")
    bars = pn.get("bars") or {}
    h = float(bars.get("height", 4.0))
    rx = float(bars.get("cap_rx", 0.6))
    lx = float(bars.get("left_x", 334.4))
    items = bars.get("items") or [{"print": "현대 콘크리트 약 100년", "outer_x": 337.4, "text": "막대 오른쪽"},
                                  {"print": "로마 콘크리트 2,000년+", "outer_x": 394.4, "text": "막대 안"}]
    ycs = [y0 + 12.0, y0 + 18.4]
    fills = [((178, 180, 182), (204, 206, 208), (130, 132, 134)), ((190, 178, 158), (214, 204, 186), (136, 124, 104))]
    for k, it in enumerate(items[:2]):
        yc = ycs[k]
        ox_ = float(it["outer_x"])
        fb, fc, oc = fills[k]
        P.rect(lx, yc - h / 2.0, ox_ - rx, yc + h / 2.0, fill=fb)
        P.ell(ox_ - rx, yc, rx, h / 2.0, fill=fc, outline=oc, lw=0.12)
        inside = "안" in str(it.get("text", ""))
        if inside:
            box, _fa = ptext(lx + 2.0, yc + 1.3, it["print"], "b", 2.6, INK_L, "body", layer=lay)
            rng = local_rng("S막대")
            for i in range(10):
                xx = box[2] + 1.5 + rng.random() * max(0.5, ox_ - rx - box[2] - 3.0)
                P.ell(xx, yc - h / 2 + 0.7 + rng.random() * (h - 1.4), 0.3, 0.26, fill=(246, 244, 236))
        else:
            ptext(ox_ + 2.0, yc + 1.3, it["print"], "b", 2.6, INK_L, "body", layer=lay)
        DRAWN["s_bars"].append({"name": it["print"], "x0": round(lx, 3), "x1": round(ox_, 3), "h": h, "cap_rx": rx,
                                "box": [round(lx, 3), round(yc - h / 2.0, 3), round(ox_, 3), round(yc + h / 2.0, 3)]})
    fn = pn.get("footnote") or ["강도가 아니라 수명이다", "(압축 강도는 현대 콘크리트가 높다)"]
    draw_lines(x0 + 2.4, y0 + 25.0, fn, "m", 2.1, INK_L, "footnote", 3.0, lay)


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
    ves = area("V")
    basic = {p: PANEL[p]["box_area"] for p in PANEL if PANEL[p]["tier"] == "Basic"}
    zc = z1_composite_box()
    detail = {"D": PANEL["D"]["box_area"], "Z1(합성)": (zc[2] - zc[0]) * (zc[3] - zc[1])}
    for d in DET["map_elements"]:
        if d["kind"] == "콜아웃":
            b = d["box"]
            detail[d["id"]] = (b[2] - b[0]) * (b[3] - b[1])
    sup = PANEL["S"]["box_area"]
    REPORT["hierarchy_drawn"] = {
        "콜로세움 mm²": int(round(hero)), "랜드마크 mm²": {k: int(round(v)) for k, v in lms.items()}, "베수비오 mm²": int(round(ves)),
        "Basic mm²": basic, "Detail mm²": {k: int(round(v)) for k, v in detail.items()}, "Support mm²": sup,
        "콜로세움 ≥ 랜드마크 최대 × 1.1": hero >= max(lms.values()) * 1.1,
        "Basic 최소 ≥ Detail 최대": min(basic.values()) >= max(detail.values()),
        "Detail 최소 ≥ Support × 1.1": min(detail.values()) >= sup * 1.1,
        "베수비오 ≤ 랜드마크 최소 ÷ 1.1": ves <= min(lms.values()) / 1.1,
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
    z = DMAP["Z1"]
    (cx, cy), dd = z["circle"]["c"], z["circle"]["d"]
    d.ellipse([(cx - dd / 2) * OK4, (cy - dd / 2) * OK4, (cx + dd / 2) * OK4, (cy + dd / 2) * OK4], fill=255)
    tb = z1_text_box()
    d.rectangle([tb[0] * OK4, tb[1] * OK4, tb[2] * OK4 - 1, tb[3] * OK4 - 1], fill=255)
    for dm in DET["map_elements"]:
        if dm.get("box"):
            b = dm["box"]
            d.rectangle([b[0] * OK4, b[1] * OK4, b[2] * OK4 - 1, b[3] * OK4 - 1], fill=255)
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
        rd = min(_poly_dist(poly, b) for r in CM["roads"] for b in road_bands(r))
        rec["clearance"]["road"] = round(rd, 2)


def measure_road_gaps():
    groups = {"판테온": ["판테온 광장"], "욕장": ["욕장 지면"], "메텔라": ["메텔라 대지"], "시장": ["시장 지면"], "콜로세움": ["콜로세움 조경 광장"]}
    for g, names in groups.items():
        best = None
        for nm in names:
            fp = GEO.get("fp_" + nm)
            if not fp:
                continue
            for r in CM["roads"]:
                for b in road_bands(r):
                    dd = _poly_dist(fp, b)
                    if best is None or dd < best[0]:
                        best = (dd, r["id"])
        if best:
            DRAWN["road_gaps"][g] = round(best[0], 2)
            DRAWN["road_gaps"][g + " 길"] = best[1]


def write_drawn():
    for pid, pn in PANEL.items():
        DRAWN["boxes"].append({"id": pid, "kind": "패널", "tier": pn["tier"], "box": list(pn["rect"]), "border": False})
    for k, v in REPORT["objects"].items():
        b = v.get("그린 외곽")
        if b:
            DRAWN["objects"].append({"id": k, "name": v.get("이름", k), "box": b})
    DRAWN["tier_color_uses"] = TIER_USES[0]
    DRAWN["stage"] = {"rects": [list(r) for r in STAGE_RECTS], "area_mm2": STAGE_AREA, "ext_rects": [],
                      "rule": "d4: 무대 확장 해제(R·T 자리 = 종이/띠 바탕, 지형·밭·포도밭 0)"}
    DRAWN["forms"] = {k: GEO[k] for k in ("aqueduct_form", "basilica_form", "hypogeum") if k in GEO}
    DRAWN["vesuvius_cover_mm"] = GEO.get("ves_cover_mm")
    DRAWN["silhouette_gaps"] = SIL_GAPS
    DRAWN["print_rule"] = "인쇄 지면에 보이는 것만 그렸다(위치도·연대기·티어 표기·크기 꼬리표·검사 수치·설계 주석 0). 이 기록은 사후 검사용이다"
    DRAWN["notes"] = REPORT["notes"]
    with open(DRAWN_PATH, "w", encoding="utf-8") as fh:
        json.dump(DRAWN, fh, ensure_ascii=False, indent=1)


def build_info_boxes():
    """라벨 자리 잡기 장애물: Detail 원·글 칸·콜아웃, 지도 안 패널(사양 좌표)"""
    z = DMAP["Z1"]
    INFO_BOXES.append(("Z1 원", z1_circle_poly()))
    INFO_BOXES.append(("Z1 글 칸", box_poly(z1_text_box())))
    for d in DET["map_elements"]:
        if d.get("box"):
            INFO_BOXES.append((d["id"], box_poly(d["box"])))
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
    hero = [pg for pg in (GEO.get("col_sil"), GEO.get("plaza_poly")) if pg]    # d5: 콜로세움 건물 실루엣 + 조경 광장(받침 0)

    def fp(*names):
        return [GEO["fp_" + n] for n in names if GEO.get("fp_" + n)]
    groups = {"콜로세움": hero, "바실리카": GEO.get("parts_L7") or [], "네로 거상": GEO.get("parts_colossus") or [],
              "극장": GEO.get("parts_L9") or [], "영묘": (GEO.get("parts_L8") or [])[:2], "영묘 다리": (GEO.get("parts_L8") or [])[2:],
              "판테온": fp("판테온 광장", "판테온 드럼", "판테온 돔"), "욕장": fp("욕장 지면"), "시장": fp("시장 지면"),
              "포르투스 육각 내항": fp("포르투스 육각 내항"), "하역장": fp("하역장", "하역장 부두 면"), "바지선 2": fp("바지선 2"), "공사장": fp("공사장 받침"),
              "오스티아": fp("오스티아"), "Z1 글 칸": [box_poly(z1_text_box())]}
    pairs = [("바실리카", "콜로세움"), ("바실리카", "네로 거상"), ("바실리카", "욕장"), ("바실리카", "시장"), ("네로 거상", "콜로세움"),
             ("극장", "판테온"), ("영묘", "포르투스 육각 내항"), ("영묘", "하역장"), ("영묘 다리", "하역장"), ("영묘", "바지선 2"), ("영묘", "공사장"),
             ("오스티아", "Z1 글 칸")]
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
ANCHOR_MAP = {   # 앵커 이름(ANCHOR_ 뒤) → (종류, 정보 층 요소)
    "HERO_label": ("label", "콜로세움"), "NERO_label": ("label", "네로 거상"), "WS_label": ("tag", "콜로세움 공사장"),
    "L1_label": ("label", "판테온"), "L2_label": ("label", "트라야누스 시장"), "L3_label": ("label", "카라칼라 욕장"), "L4_label": ("label", "수도교"),
    "L5_label": ("label", "카이킬리아 메텔라 무덤"), "L6_label": ("label", "포르투스 항"), "L7_label": ("label", "막센티우스 바실리카"),
    "L8_label": ("label", "하드리아누스 영묘"), "L9_label": ("label", "마르켈루스 극장"), "V_label": ("label", "베수비오"),
    "BARGE1_label": ("label", "바지선"), "ASH_label": ("label", "화산재 운반선"), "EMP_label": ("tag", "테베레 하역장·석회 가마"),
    "WS_z1": ("leader", "→ 확대 창 Z1"), "WS_s6": ("link", "⑥"), "L1_c1": ("leader", "콜아웃 C1"), "L6_c2": ("leader", "콜아웃 C2"),
    "L5_c4": ("leader", "콜아웃 C4"), "L4_m1": ("mark", "1"), "L7_m2": ("mark", "2"), "L2_m3": ("mark", "3"), "L1_m4": ("mark", "4"),
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
    path = os.environ.get("INFO_SIL") or (ROOT + "/.work/blender/rounds/b%d/sil.json" % n if n is not None else None)
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
    pts_all = [p for _n, pg in raw for p in pg] + [tuple(v) if not isinstance(v, dict) else (v.get("x"), v.get("y")) for v in anc.values() if v]
    k_ = 3.0 if pts_all and max(max(abs(float(p[0] or 0)) for p in pts_all), max(abs(float(p[1] or 0)) for p in pts_all) / 1.414) > 600 else 1.0   # 화소(3 px/mm)면 mm로
    polys = [(nm, [(x / k_, y / k_) for x, y in pg]) for nm, pg in raw]
    anchors = {}
    for nm, v in anc.items():
        if isinstance(v, dict):
            v = v.get("screen") or [v.get("x"), v.get("y")]
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


def main():
    _t("시작")
    if INFO_ONLY:
        load_sil()
    build_info_boxes()
    build_marks()
    build_exclusions()
    # 1 바탕 지면(무대 = 지도 무대 하나. 위 띠 오른쪽·하단 띠 오른쪽은 종이/띠 바탕)
    use_layer(BASE)
    draw_ground()
    draw_river()
    draw_sea()
    draw_coast_section()
    draw_roads()
    register_floor_polys()
    _t("지면")
    # 2 랜드마크·소품 층(뒤 → 앞): 바실리카는 카라칼라 다음·시장 전, 극장은 판테온 다음, 영묘는 포르투스 다음, 거상은 아레나 전
    use_layer(OBJ)
    draw_caracalla()
    draw_aqueduct()
    draw_basilica()
    draw_market()
    draw_pantheon()
    draw_theatre()
    draw_kiln()
    draw_barge(PROPS["바지선 1"], "X", "바지선 1")
    ac = PROPS["아피아 가도 수레"]
    apl = ac.get("plan") or [485.6, 72.0]
    draw_road_cart(ac, "아피아 가도 수레", apl[0], apl[1], "Y", ASH_G)
    draw_colossus()
    draw_arena()
    draw_dock()
    mc = PROPS["재료 수레"]
    mpl = mc.get("plan") or [462.3, 278.0]
    draw_road_cart(mc, "재료 수레", mpl[0], mpl[1], "Y", LIME_W)
    draw_metella()
    draw_portus()
    draw_mausoleum()
    draw_barge(PROPS["바지선 2"], "Y", "바지선 2")
    draw_worksite()
    draw_ostia()
    draw_villa()
    draw_ash_ship()
    snap_marks()
    exclude_marks()
    _t("랜드마크")
    # 3 라벨 자리 잡기(랜드마크 실측 외곽 기준). 지형 층의 베수비오는 외곽만 먼저 등록한다(브래킷 대상)
    use_layer(BASE)
    _v = ves_geom()
    add_fp("베수비오", _v[7], "배경 산")
    if INFO_ONLY:
        apply_anchor_targets()
    plan_labels()
    if INFO_ONLY:
        snap_info_to_anchors()
    _t("라벨 자리")
    # 4 지형 층(밭·베수비오·농장·구릉·지붕·나무) — 랜드마크 층 아래로 합성. 그리는 순서: 산 → 농장 → 구릉
    use_layer(TER)
    m, allp, ox, oy, sc, zs, bb, hull = ves_geom()
    ex_poly(hull, 0.6)
    ex_rect(PROPS["포도밭 농장"]["box"], 0.6)
    draw_fields()
    draw_vesuvius()
    draw_farm()
    draw_albano()
    draw_scatter()
    BASE.img.alpha_composite(TER.img)
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
    draw_z1()
    draw_c1()
    draw_c2()
    draw_c4()
    draw_leaders()
    draw_labels()
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
