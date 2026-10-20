# -*- coding: utf-8 -*-
"""로마 편 배치 다이어그램(인쇄 지면) — 사양 spec.json을 읽어 A2 다이어그램 PNG(1mm = 3px, 1260×1782)와
그린 기록 drawn.json(사후 검사용)을 만든다. 담당: render

실행: python -I render.py <출력 PNG> <spec.json> [히어로 군 실루엣 npy]   (make.py가 부른다)
- 사용자 검토(2026-10-19 02:24): 다이어그램은 실제로 인쇄될 포스터 지면만 보인다.
  위치도(R)·연대기(T) 패널, 작업 이름, 티어 이름·티어 색·범례, 크기 꼬리표, 면적·검사 수치, 투영 상자 모서리,
  히어로 군 점선 윤곽, 가장자리 눈금, 설계 주석은 그리지 않는다. 그 정보는 spec.json과 보고서(drawn.json)에만 둔다.
- 비어 있던 오른쪽 위 자리와 하단 띠 오른쪽 자리는 지도 무대로 돌려준다(사양 frame.stage.ext_rects).
- 사양이 단일 원본이다: 라벨 슬롯·방향·본문, 지시선 꼭짓점, Detail 상자·글, 길 좌표, 포르투스·히어로 내부 형태는 사양 값을 그대로 쓴다.
  렌더는 그 값을 덮어쓰지 않고, 슬롯 안 줄바꿈·자리 조정과 모델의 실제 표면 접점 계산만 한다.
- 서체는 글자면(잉크 높이) 기준이다: 국문은 '한', 영문·라틴 문자열은 'H' 대문자 높이. em = 글자면 ÷ 글꼴 실측 비.
- 좌표: A2 mm(x 오른쪽, y 아래). 등각: 평면 +X → 화면 ↘, +Y → 화면 ↙, +Z → 위. 평면 원점 = 화면 (0, 0)(사양 규약 = v16 common.Iso)
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
META, HI, FR, CM = S["meta"], S["hierarchy"], S["frame"], S["core_map"]
HERO, RV, SC, PG = CM["hero"], CM["river"], CM["sea_coast"], CM["portus_geometry"]
LBS = CM["labels"]
BAS, DET, SUP, MEAS = S["basic"], S["detail"], S["support"], S["measurements"]
STAGE = tuple(FR["stage"]["rect"])
STAGE_EXT = [tuple(float(v) for v in r) for r in (FR["stage"].get("ext_rects") or [[298.0, 20.0, 420.0, 92.0], [312.0, 505.0, 420.0, 568.0]])]
STAGE_RECTS = [STAGE] + STAGE_EXT
REMOVED_PANELS = ("R", "T")                          # 사용자 검토: 위치도·연대기는 인쇄 지면에서 0개
PANEL = {p["id"]: p for p in FR["panels"] if p["id"] not in REMOVED_PANELS}
LM = {l["id"]: l for l in CM["landmarks"]}
VES = CM["background"][0]
PROPS = {p["name"].split("(")[0].strip(): p for p in CM["props"]}
DMAP = {d["id"]: d for d in DET["map_elements"]}
SLOT = {s["name"].split("(")[0].strip(): s for s in LBS["slots"]}
FLOOR = {f["name"].split(" ")[0]: f for f in LBS["floor_text"]}
TERR = {t["name"].split("(")[0].split(" ")[0]: t for t in CM.get("terrain", [])}
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
INK_WATER = (236, 246, 252)     # 물 위 바닥 글(밝은 크림)
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
    db = [round(v, 1) for v in drawn_box]
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


# ───────────────────────── 콜로세움 기하(사양 core_map.hero) ─────────────────────────
AR_C = tuple(HERO["center_screen"])
AR_R = HERO["oct_R_plan"]
AR_T = HERO["base_side_T"]
RING_O = HERO["ring_ratio"] * AR_R
RING_I = RING_O - 6.0
_W = HERO["walls"]
F0, F1 = float(_W[0]["t0"]), float(_W[0]["t1"])     # 4층 조각 150~235(뒤-왼쪽, LocalBanana 원래 방향)
B1 = float(_W[1]["t1"])                             # 2층 고리 ~330
HF, HB, HL = _W[0]["h"], _W[1]["h"], _W[2]["h"]     # 60 · 28 · 12


def hwall(th):
    """외벽 고리 높이(평면 방위각 θ, X→Y 반시계). 끝은 계단처럼 들쭉날쭉 무너진다."""
    th %= 360.0
    if F0 <= th < F1:
        for lim, h in ((F0 + 3, HL + 12), (F0 + 6, HL + 24), (F0 + 9, HL + 35), (F0 + 12, HF - 5)):
            if th < lim:
                return h
        if th < F1 - 6:
            return HF
        if th < F1 - 3:
            return HF - 9
        return HF - 19
    if F1 <= th < B1:
        if th < B1 - 9:
            return HB
        if th < B1 - 6:
            return HB - 5
        if th < B1 - 3:
            return HB - 10
        return HL + 2
    return HL - 1.6 * (0.5 + 0.5 * math.cos(math.radians(th * 5.0)))


def arena_rp(r, th, z=0.0):
    t = math.radians(th)
    X, Y = r * math.cos(t), r * math.sin(t)
    return (AR_C[0] + C30 * (X - Y), AR_C[1] + 0.5 * (X + Y) - z)


def arena_wall_sil():
    top = [arena_rp(RING_O + 1.0, t, hwall(t) + 1.0) for t in range(132, 346, 3)]
    bot = [arena_rp(RING_O, t, 0.0) for t in range(345, 131, -3)]
    return top + bot


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
    return tuple(sget(DMAP["Z1"], "text_box", "textbox", default=[212.0, 426.0, 240.0, 462.0]))


def z1_composite_box():
    return tuple(sget(DMAP["Z1"], "composite_box", "composite", default=[212.0, 418.0, 307.0, 482.0]))


def detail_leaders():
    """Detail·Basic 지시선(사양 꼭짓점 그대로): [(이름, 점들, 짝 표지 글자, 종류)]"""
    out = []
    lk = BAS["process_representation"]["link"]
    out.append((lk["name"], [tuple(p) for p in lk["pts"]], None, "basic"))
    for ld in DET["leaders"]:
        nm = ld["name"]
        letter = None
        tgt = nm.split("→")[1] if "→" in nm else ""
        for d in DET["map_elements"]:
            if re.search(r"(?<![A-Za-z0-9])%s(?![A-Za-z0-9])" % d["id"], tgt):
                letter = d.get("mark")
        out.append((nm, [tuple(p) for p in ld["pts"]], letter, "detail"))
    return out


def build_exclusions():
    for l in CM["landmarks"]:
        ex_rect(l["projected_box"], 1.4)
    octs = [tuple(p) for p in HERO["base_oct_screen"]]
    ex_poly(octs, 1.6)
    ex_poly([octs[7], octs[0], octs[1], octs[2], (octs[2][0], octs[2][1] + AR_T), (octs[1][0], octs[1][1] + AR_T),
             (octs[0][0], octs[0][1] + AR_T), (octs[7][0], octs[7][1] + AR_T)], 1.6)
    ex_poly(arena_wall_sil(), 1.5)
    ex_rect(HERO["worksite"]["box"], 1.5)
    for p in CM["props"]:
        if p["name"].startswith("포도밭 농장"):
            continue                                    # 농장은 지형 층에서 직접 그린다(밭 배치가 피한다)
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
    """밭·포도밭(지형 층). 오른쪽 위 확장 자리는 대기 원근의 먼 밭, 하단 오른쪽 확장 자리는 남동 교외 밭을 그대로 잇는다."""
    G = Layer(0, 0, PW, PH)
    n0 = place_fields(G, (298, 20, 420, 95), (180, 350), (-236, -66), (10.0, 7.5),
                      ["vine", "wheat", "pasture", "vine", "fallow", "wheat"], "먼밭", gap=0.9, far=True)
    n1 = place_fields(G, (290, 392, 430, 575), (540, 835), (130, 405), (15.0, 11.0),
                      ["vine", "vine", "vine", "wheat", "pasture", "vine", "fallow"], "남동밭")
    n2 = place_fields(G, (372, 206, 430, 252), (428, 466), (-31, 34), (13.0, 10.0), ["pasture", "wheat", "fallow", "vine"], "가도밭")
    n3 = place_fields(G, (-20, 322, 66, 372), (300, 430), (324.5, 352), (17.0, 11.0), ["wheat", "wheat", "pasture", "fallow"], "곡식밭")
    n4 = place_fields(G, (150, 425, 252, 505), (548, 660), (300, 380), (13.0, 10.0), ["pasture", "wheat", "fallow", "vine"], "하구밭")
    n5 = place_fields(G, (88, 362, 206, 470), (452, 524), (324.5, 380), (13.0, 10.0), ["wheat", "pasture", "wheat", "fallow"], "포르투스띠")
    G.img.putalpha(ImageChops.multiply(G.img.getchannel("A"), land_mask(KD)))
    P.paste(G)
    REPORT["notes"].append("밭 구획: 먼 밭(오른쪽 위) %d · 남동 교외(하단 오른쪽까지) %d · 가도 옆 %d · 강 오른쪽 둑 곡식밭 %d · 하구 동쪽 %d · 포르투스 띠 %d"
                           % (n0, n1, n2, n3, n4, n5))


def albano_box():
    for t in CM.get("terrain", []):
        if t["name"].startswith("알바노"):
            return tuple(t["box"])
    return (300.0, 64.0, 420.0, 160.0)


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
    """알바노 구릉 띠(사양 terrain 상자): 화산 그림이 아니라 낮은 구릉 지면 결.
    맨 뒤 능선의 윗선을 베수비오 밑동 윤곽보다 3~5mm 위에 둔다(사양 ridge.x_ranges). 농장이 밑동을 가리는 구간은
    능선 꼭대기를 농장 아래 변(ridge.farm_front_top_y_min) 아래로 낮춘다. 그리는 순서: 산 → 농장 → 구릉."""
    bx0, by0, bx1, by1 = albano_box()
    rc = albano_ridge_cfg()
    cov = rc.get("cover_vesuvius_base_mm") or [3.0, 5.0]
    cover = (float(cov[0]) + float(cov[1])) / 2.0
    xr = rc.get("x_ranges") or [[VES["projected_box"][0], PROPS["포도밭 농장"]["box"][0]], [PROPS["포도밭 농장"]["box"][2], VES["projected_box"][2]]]
    farm_y = float(rc.get("farm_front_top_y_min", PROPS["포도밭 농장"]["box"][3]))
    sub = Layer(bx0 - 12, by0 - 30, min(PW, bx1 + 12), by1 + 8)
    isub = Iso(sub, 0, 0)
    col = mix((150, 160, 104), GROUND, 0.42)
    col_far = mix((150, 160, 104), BG, 0.45)
    m = Mesh(None)
    yb = ves_front_contour()
    covers = []
    n_r = n_b = 0
    if yb:
        x = xr[0][0] + 0.5
        k = 0
        while x <= xr[-1][1] + 0.01:
            in_side = any(r[0] - 0.01 <= x <= r[1] + 0.01 for r in xr)
            yv = yb(x)
            if in_side and yv is not None:
                apex = yv - cover
                h, R = 2.6, 3.6
            else:
                apex = farm_y + 0.6
                h, R = 1.5, 6.2
            yc = apex + h
            fp = [(x - 1.2247 * R, apex - 0.3), (x + 1.2247 * R, apex - 0.3), (x + 1.2247 * R, yc + 0.7071 * R), (x - 1.2247 * R, yc + 0.7071 * R)]
            if any(_poly_dist(fp, pg) < LABEL_CLEAR + 0.3 for _n, pg in LABEL_POLYS if not _n.startswith("바닥 글")):
                x += 2.6 if in_side else 5.0
                k += 1
                continue
            X, Y = to_plan(x, yc)
            m.extend(m_mound(X, Y, 0, R, h, col_far, n=10, rings=3, key="능선%d" % k, jit=0.05, apex_jit=0.06))
            if in_side and yv is not None:
                covers.append(round(yv - apex, 2))
            x += 2.6 if in_side else 7.0
            k += 1
            n_r += 1
    rng = local_rng("알바노결")
    cands = []
    y = max(by0 + 8.0, farm_y + 4.0)
    row = 0
    while y < by1 - 1.0:
        x = bx0 + (6.0 if row % 2 else 0.0) + 2.0
        while x < bx1 + 4.0:
            R = 7.0 + rng.random() * 4.0
            h = 1.3 + rng.random() * 1.2
            xx, yy = x + (rng.random() - 0.5) * 3.0, y + (rng.random() - 0.5) * 1.6
            hx, hy = 1.2247 * R, 0.7071 * R
            fp = [(xx - hx, yy - h - 0.4), (xx + hx, yy - h - 0.4), (xx + hx, yy + hy), (xx - hx, yy + hy)]
            if poly_free(fp, 0.3, stage=False) and poly_in_stage(fp, 1.0):
                cands.append((yy, xx, R, h, fp, row))
            x += 12.0
        y += 6.5
        row += 1
    for (yy, xx, R, h, fp, row) in sorted(cands):                   # 뒤 → 앞(서로 겹쳐 이어지는 구릉 결)
        X, Y = to_plan(xx, yy)
        m.extend(m_mound(X, Y, 0, R, h, col, n=10, rings=3, key="알바노%d_%d" % (row, int(xx)), jit=0.1, apex_jit=0.15))
        n_b += 1
    for (yy, xx, R, h, fp, row) in cands:
        ex_poly(fp, 0.2)
    m.draw(isub, lw=0.05)
    for i in range(26):
        x = bx0 + 6 + h01("알바노올리브", i) * (bx1 - bx0 - 10)
        y = max(by0, farm_y) + 6 + h01("알바노올리브y", i) * (by1 - max(by0, farm_y) - 10)
        if poly_free([(x - 1, y - 0.7), (x + 1, y - 0.7), (x + 1, y + 0.7), (x - 1, y + 0.7)], 0.2, stage=False):
            sub.ell(x, y, 0.9, 0.6, fill=(112, 136, 84))
    merge(P, sub, opacity=1.0, blur=0.0)
    if covers:
        GEO["ves_cover_mm"] = [min(covers), max(covers)]
    REPORT["notes"].append("알바노 구릉: 능선 %d · 구릉 결 %d · 베수비오 밑동 가림 %s mm(옆 구간), 농장 구간은 농장 아래 변 y %.1f 아래" % (n_r, n_b, GEO.get("ves_cover_mm"), farm_y))


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
def draw_roads():
    """사양 길(plan_pts)만 그린다. 연장은 사양 좌표에 들어 있다(렌더 하드코딩 없음). 가장자리선 2줄."""
    bands = {}
    for r in CM["roads"]:
        bands[r["id"]] = road_bands(r)
        col = APPIA_C if r.get("center_line") else ROAD_C
        for poly in bands[r["id"]]:
            P.poly(poly, fill=col)
    for r in CM["roads"]:                                # 가장자리선은 모든 길을 칠한 다음(이음 모서리가 덮이지 않게)
        for poly in bands[r["id"]]:
            P.line([poly[0], poly[1]], ROAD_EDGE, 0.3, joint=False)
            P.line([poly[3], poly[2]], ROAD_EDGE, 0.3, joint=False)
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


def draw_floor_texts():
    for f in FLOORS:
        u = 0.0
        (a, b), (c, d) = f["M"]
        for (t, ft, col, kind, em, fa) in f["fparts"]:
            iso_text(P, t, ft, col, f["M"], f["ax"] + a * u, f["ay"] + c * u)
            w = tw(t, ft)
            poly = [map_pt(f["M"], f["ax"], f["ay"], u + uu, vv) for uu, vv in ((0, -fa), (w, -fa), (w, 0.3), (0, 0.3))]
            rec_text(t, "floor_" + ("en" if kind == "en" else "ko"), kind, em, fa, poly, layer="바닥 글")
            u += w + 1.6
        LABEL_POLYS.append(("바닥 글:" + f["name"], f["poly"]))


# ───────────────────────── 4 지붕의 바다·나무(빈 자리만) ─────────────────────────
def try_mesh(m, pad=0.5, draw=True):
    pts = [ISO.p(*p) for p in mesh_pts(m)]
    bb = bbox_of(pts)
    poly = box_poly(bb)
    if not poly_free(poly, pad):
        return False
    if draw:
        m.draw(ISO, lw=0.07)
    ex_poly(poly, 0.3)
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
    m.draw(isub, lw=0.08)
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
    farm.draw(fiso, lw=0.08)
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
    stat.draw(iso, lw=0.05)
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
    dome.draw(iso, lw=0.07)
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
    bath.draw(iso, lw=0.05)

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
            P.poly(q, fill=col, outline=shade(col, 0.8), lw=0.08)
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
    m_box(55.5, 13.0, 0, 60.0, 16.5, 4.6, BRICK, top=BRICK_L).draw(iso, lw=0.08)
    iso.arch("L", 0, 16.52, 0, 56.6, 58.9, 0.2, 2.4, (70, 40, 26))
    fcx, fcy = iso.p(57.75, 16.6, 1.4)
    P.ell(fcx, fcy, 0.9, 0.7, fill=(240, 140, 50))
    work = Mesh(None)
    work.extend(m_person(61.6, 18.6, 0, H_PERSON, CLOTHS[0], key="화로꾼"))
    for i in range(4):
        work.extend(m_box(63.4 + i * 0.2, 16.0 + i * 0.9, 0, 66.0, 16.7 + i * 0.9, 0.7 + 0.1 * i, WOOD, top=WOOD_L))
    work.draw(iso, lw=0.06)
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
    cols.draw(iso, lw=0.06)
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


def draw_aqueduct():
    L4 = LM["L4"]
    (x0s, y0s), (x1s, y1s) = CM["aqueduct"]["ground_line_screen"]
    X0, Y0 = to_plan(x0s, y0s)
    X1, _Y1 = to_plan(x1s, y1s)
    H = CM["aqueduct"]["arch_height_mm"]
    T = 1.6
    stone = (206, 158, 106)          # 지면보다 채도를 높인 석재 아치
    brick = (190, 104, 72)           # 위 단(수로를 받치는 단)은 벽돌면
    Xe = X1 + 10.0
    m = Mesh(None)
    m.extend(m_box(X0, Y0 - T, 0, Xe, Y0 + T, H - 3.2, stone, top=(222, 182, 132)))
    m.extend(m_box(X0 - 0.3, Y0 - T - 0.4, H - 3.2, Xe, Y0 + T + 0.4, H, brick, top=(206, 126, 92)))
    m.draw(ISO, lw=0.12)
    pitch = 8.0
    u0 = X0 + 1.4
    while u0 + 5.2 < Xe:
        ISO.arch("L", 0, Y0 + T + 0.02, 0, u0, u0 + 5.3, 0.0, 9.0, (164, 120, 84), (128, 90, 60), 0.12)
        ISO.arch("L", 0, Y0 + T + 0.02, 0, u0 + 0.7, u0 + 4.6, 13.0, 17.2, (164, 120, 84), (128, 90, 60), 0.1)
        u0 += pitch
    ISO.line3([(X0, Y0 - T - 0.2, 12.3), (Xe, Y0 - T - 0.2, 12.3)], (226, 192, 146), 0.35)
    ISO.line3([(X0, Y0 - 0.55, H + 0.05), (Xe, Y0 - 0.55, H + 0.05)], (214, 150, 128), 0.3)    # 수로 안 방수 모르타르(분홍 회반죽)
    ISO.line3([(X0, Y0, H + 0.05), (Xe, Y0, H + 0.05)], (96, 160, 206), 0.6)                    # 수로 물
    pts = [ISO.p(X0, Y0 - T - 0.4, H), ISO.p(X0, Y0 + T, 0), ISO.p(Xe, Y0 + T, 0), ISO.p(Xe, Y0 - T, H)]
    bb = bbox_of(pts)
    bb = (bb[0], bb[1], min(bb[2], PW), bb[3] if bb[2] <= PW else (pts[1][1] + (PW - pts[1][0]) * T30))
    GEO["aq_ground"] = lambda x: (pts[1][1] + (x - pts[1][0]) * T30)
    face = [ISO.p(X0, Y0 + T, 0), ISO.p(Xe, Y0 + T, 0), ISO.p(Xe, Y0 + T, H), ISO.p(X0, Y0 + T, H)]
    add_fp("수도교 아치 면", face, "대상 면")
    record("L4", L4["name"], "Core(표준 랜드마크)", L4["projected_box"], bb, "오른쪽 변 블리드(상자는 x 420에서 자름)")


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
    s1.draw(iso, lw=0.07)
    s2.draw(iso, lw=0.07)
    s3.draw(iso, lw=0.07)
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
    ppl.draw(iso, lw=0.06)
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
    back_trees.draw(iso, lw=0.06)
    rot.draw(iso, lw=0.08)
    for zc in (8.0, 16.0):
        iso.line3([(18.05 * math.cos(math.radians(t)), 18.05 * math.sin(math.radians(t)), zc) for t in range(-45, 136, 6)], (196, 182, 156), 0.22)
    dome.draw(iso, lw=0.07)
    oc = [iso.p(2.1 * math.cos(math.radians(t)), 2.1 * math.sin(math.radians(t)), 26.0 + 16.06) for t in range(0, 360, 30)]
    P.poly(oc, fill=(92, 80, 66))
    front.draw(iso, lw=0.07)
    iso.line3([(-9.0, 33.62, 17.2), (9.0, 33.62, 17.2)], (150, 132, 108), 0.3)    # 박공 아래 명문 띠
    court.draw(iso, lw=0.06)
    ppl = Mesh(None)
    for (X, Y, c) in ((-6.0, 38.5, 0), (5.0, 40.0, 2), (9.5, 36.0, 4), (-13.0, 30.0, 1)):
        ppl.extend(m_person(X, Y, 0.02, H_PERSON / max(sc * zs, 0.6), CLOTHS[c], key="판테온사람%d" % c))
    ppl.extend(front_trees)
    ppl.draw(iso, lw=0.06)
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
    record("L1", L1["name"], "Core(표준 랜드마크)", box, bb, "높이 과장 %.2f배" % zs)


def draw_metella():
    L5 = LM["L5"]
    box = L5["projected_box"]
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
    back.draw(iso, lw=0.06)
    m.draw(iso, lw=0.08)
    for zc in (13.0, 15.6, 18.2, 20.8, 23.4):                       # 벽돌 줄눈
        iso.line3([(14.55 * math.cos(math.radians(t)), 14.55 * math.sin(math.radians(t)), zc) for t in range(-44, 135, 6)], (188, 136, 104), 0.14)
    for i in range(12):
        a = math.radians(-36 + i * 14.5)
        cx_, cy_ = iso.p(14.8 * math.cos(a), 14.8 * math.sin(a), 27.7)
        P.ell(cx_, cy_, 0.5, 0.42, fill=(172, 156, 126))
    frontt.draw(iso, lw=0.06)
    ppl.draw(iso, lw=0.06)
    foot = [iso.p(-16, -16), iso.p(16, -16), iso.p(16, 16), iso.p(-16, 16)]
    GEO["metella_foot"] = foot
    GEO["metella_drum_l"] = iso.p(-14.5 * 0.7071, 14.5 * 0.7071, 9.0)
    add_fp("메텔라 대지", [iso.p(-19, -19, 0), iso.p(21, -19, 0), iso.p(21, 21, 0), iso.p(-19, 21, 0)], "지면")
    add_fp("메텔라 기단", _hull([iso.p(X, Y, Z) for X in (-16, 16) for Y in (-16, 16) for Z in (0, 8.0)]), "대상 면")
    add_fp("메텔라 드럼", _hull([iso.p(14.5 * math.cos(math.radians(t)), 14.5 * math.sin(math.radians(t)), z)
                              for t in range(0, 360, 10) for z in (10.6, 26.2)]), "대상 면")
    record("L5", L5["name"], "Core(표준 랜드마크)", box, bb, "높이 과장 %.2f배" % zs)


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
        # 육각 내항 쪽 끝을 수면 안으로 1.5mm 더 넣어 수면이 이어지게(같은 물빛). 다른 끝은 강·외항 수면 안 0.6mm
        if ya > hy:
            ya_d, yb_d = ya - 1.5, yb_ + 0.6
        else:
            ya_d, yb_d = ya - 0.6, yb_ + 1.5
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
                           "screen_w": round((x1 - x0) * C30, 2), "plan_y": [round(ya_d, 2), round(yb_d, 2)]})
    wall.draw(iso, lw=0.08)
    wh.draw(iso, lw=0.08)
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
    moles.draw(iso, lw=0.08)
    tower.draw(iso, lw=0.08)
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


def draw_cutaway(a, b, Tz):
    """콜로세움 받침 앞 변 기초 절개: 왼쪽 = 공사 중(거푸집 널), 오른쪽 = 굳은 기초 콘크리트 고리 단면(골재·흰 석회 알갱이)"""
    x0, x1 = min(a[0], b[0]), max(a[0], b[0])
    y0 = a[1]
    P.rect(x0, y0, x1, y0 + Tz, fill=(140, 110, 76))
    P.rect(x0, y0, x1, y0 + 0.9, fill=(94, 126, 66))
    cx0, cx1 = x0 + 3.5, x1 - 3.5
    P.rect(cx0, y0 + 1.3, cx1, y0 + Tz, fill=CONC2)
    rng = local_rng("기초단면")
    for i in range(70):
        x = cx0 + 0.5 + rng.random() * (cx1 - cx0 - 1.0)
        y = y0 + 1.8 + rng.random() * (Tz - 2.3)
        if x < cx0 + 40:
            continue
        r_ = 0.3 + rng.random() * 0.45
        col = (250, 250, 244) if i % 4 == 0 else ((168, 136, 104) if i % 4 == 1 else ((186, 104, 78) if i % 4 == 2 else (120, 112, 104)))
        P.ell(x, y, r_, r_ * 0.8, fill=col)
    for k in range(9):                                               # 공사 중 부분: 나무 거푸집 널
        xx = cx0 + 1.0 + k * 4.4
        P.rect(xx, y0 + 1.3, xx + 3.8, y0 + Tz, fill=WOOD if k % 2 else WOOD_L, outline=(110, 80, 50), lw=0.1)
    for k in range(4):
        yy = y0 + 2.2 + k * 1.2
        P.line([(cx0 + 0.5, yy), (cx0 + 39.8, yy)], (176, 168, 154), 0.18, joint=False)
    for xx in (x0, x1):
        for k in range(4):
            P.line([(xx + (1.2 if xx == x0 else -1.2) * 0.0, y0 + 1.6 + k * 1.4), (xx + (1.6 if xx == x0 else -1.6), y0 + 0.9 + k * 1.4)], (70, 50, 32), 0.14, joint=False)
    P.rect(x0, y0, x1, y0 + Tz, outline=(60, 44, 30), lw=0.25)
    GEO["cut_A"] = (min(x1 - 4.0, AR_C[0] + 25.0), y0 + Tz)
    add_fp("콜로세움 기초 절개", [(x0, y0), (x1, y0), (x1, y0 + Tz), (x0, y0 + Tz)], "대상 면")


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


def draw_hypogeum(iso, rf):
    """하이포게움 노출 반쪽(화면 왼쪽): 바닥을 나무 바닥보다 화면 수직 drop mm 낮추고, 장축 중심 통로 1 + 평행 통로 2 + 가로벽을 그린다(사양 hero.interior)."""
    hp = HERO_IN.get("hypogeum", {})
    drop = float(hp.get("floor_drop_mm", 5.0))
    wt = float(hp.get("wall_t_mm", 1.5))
    gap_c = _num_in(hp.get("corridors"), 6.0)
    n_cross = int(hp.get("cross_walls", 7))
    cross_gap = float(hp.get("cross_gap_mm", 5.0))
    z_top, z_pit = 1.2, 1.2 - drop
    cx, cy = iso.ox, iso.oy
    sub = Layer(cx - 1.2247 * rf - 2, cy - 0.7071 * rf - 8, cx + 2, cy + 0.7071 * rf + 8)
    isub = Iso(sub, cx, cy)

    def P3(s_, t_, z):
        return isub.p((s_ + t_) / SQ2, (t_ - s_) / SQ2, z)

    def half(z, n=36):
        return [isub.p(rf * math.cos(math.radians(a)), rf * math.sin(math.radians(a)), z) for a in [45 + 180.0 * i / n for i in range(n + 1)]]
    sub.poly(half(z_pit), fill=(86, 62, 40))                         # 구덩이 바닥
    for a0 in range(135, 225, 5):                                    # 먼 쪽 둥근 벽 안쪽 면(보이는 쪽)
        a1 = a0 + 5
        q = [isub.p(rf * math.cos(math.radians(a)), rf * math.sin(math.radians(a)), z) for a, z in ((a0, z_pit), (a1, z_pit), (a1, z_top), (a0, z_top))]
        sub.poly(q, fill=lit((150, 118, 82), (-math.cos(math.radians(a0 + 2.5)), -math.sin(math.radians(a0 + 2.5)), 0.0)))
    kt = 0.7071                                                      # 화면 세로 mm → 평면 t
    ks = 1.2247                                                      # 화면 가로 mm → 평면 s
    walls_dy = [-1.5 * gap_c, -0.5 * gap_c, 0.5 * gap_c, 1.5 * gap_c]   # 통로 3개(중심 0, ±gap_c)의 벽
    for c_dy in (-gap_c, 0.0, gap_c):                                # 통로 바닥(조금 밝게)
        t0, t1 = (c_dy - gap_c / 2.0 + wt / 2.0) / kt, (c_dy + gap_c / 2.0 - wt / 2.0) / kt
        tm = max(abs(t0), abs(t1))
        if tm >= rf:
            continue
        sa, sb = -math.sqrt(rf * rf - t0 * t0), -math.sqrt(rf * rf - t1 * t1)
        sub.poly([P3(sa, t0, z_pit), P3(0, t0, z_pit), P3(0, t1, z_pit), P3(sb, t1, z_pit)], fill=(128, 100, 68))
    for w_dy in walls_dy:                                            # 장축 방향 벽(뒤 → 앞): 앞면 + 윗면
        tw0, tw1 = (w_dy - wt / 2.0) / kt, (w_dy + wt / 2.0) / kt
        if max(abs(tw0), abs(tw1)) >= rf:
            continue
        s0, s1 = -math.sqrt(rf * rf - tw1 * tw1), -math.sqrt(rf * rf - tw0 * tw0)
        sub.poly([P3(s0, tw1, z_pit), P3(0, tw1, z_pit), P3(0, tw1, z_top), P3(s0, tw1, z_top)], fill=(176, 150, 112), outline=(120, 96, 66), lw=0.08)
        sub.poly([P3(s1, tw0, z_top), P3(0, tw0, z_top), P3(0, tw1, z_top), P3(s0, tw1, z_top)], fill=(214, 192, 154), outline=(150, 126, 92), lw=0.08)
    for k in range(1, n_cross + 1):                                  # 가로벽(간격 cross_gap mm): 윗면 띠
        sc = -k * cross_gap / ks
        sw = wt / ks
        if abs(sc) + sw >= rf:
            continue
        tl = math.sqrt(rf * rf - (abs(sc) + sw / 2.0) ** 2)
        sub.poly([P3(sc - sw / 2, -tl, z_top), P3(sc + sw / 2, -tl, z_top), P3(sc + sw / 2, tl, z_top), P3(sc - sw / 2, tl, z_top)], fill=(214, 192, 154))
        sub.line([P3(sc + sw / 2, -tl, z_top), P3(sc + sw / 2, tl, z_top)], (140, 114, 82), 0.12, joint=False)
    m = Image.new("L", (sub.w, sub.h), 0)                            # 구덩이 입구(나무 바닥 높이의 왼쪽 반)로만 보인다
    ImageDraw.Draw(m).polygon([sub.P(p) for p in half(z_top, 48)], fill=255)
    sub.img.putalpha(ImageChops.multiply(sub.img.getchannel("A"), m))
    P.paste(sub)
    hx = [p for p in half(z_top, 48)]
    P.line(hx, (78, 58, 38), 0.35)
    GEO["hypogeum"] = {"drop_mm": drop, "wall_t_mm": wt, "corridor_gap_mm": gap_c, "cross_walls": n_cross, "cross_gap_mm": cross_gap}


def crowd_groups(iso, props_fp):
    """히어로 받침 앞 광장의 인물 군 3곳(각 약 20×10mm, 5~7명, 키 5mm, 이웃 발점 간격 3.5~5mm). 노점·암포라·폐허 둘레, 소품과 겹치지 않게 자리를 조금 옮긴다."""
    cfg = sget(HERO, "crowds", default=None) or [{"name": "군 1(노점·암포라 둘레)", "c": [306.0, 360.0]}, {"name": "군 2(기둥 폐허 둘레)", "c": [236.0, 371.0]},
                                                  {"name": "군 3(노점 앞)", "c": [190.0, 357.0]}]
    offs = [(-8.0, -1.5), (-4.0, -2.6), (0.2, -1.2), (4.3, -2.4), (8.2, -0.9), (-2.2, 2.4), (2.9, 2.7)]
    r_min, r_max = RING_O + 2.4, AR_R * math.cos(math.radians(22.5)) - 3.0

    def nn_ok(feet):
        for i, p in enumerate(feet):
            d = min(math.hypot(p[0] - q[0], p[1] - q[1]) for j, q in enumerate(feet) if j != i)
            if d < 3.5 or d > 5.0:
                return False
        return True
    out = []
    for k, g in enumerate(cfg):
        c0 = g.get("c") or g.get("center")
        best = None
        for dx in (0.0, 1.5, -1.5, 3.0, -3.0, 4.5, -4.5, 6.0, -6.0):
            for dy in (0.0, 1.0, -1.0, 2.0, -2.0, 3.0, -3.0):
                feet, plan = [], []
                for (ox, oy) in offs:
                    x, y = c0[0] + dx + ox, c0[1] + dy + oy
                    a = (x - iso.ox) / C30
                    X, Y = (a + 2.0 * (y - iso.oy)) / 2.0, (2.0 * (y - iso.oy) - a) / 2.0
                    r = math.hypot(X, Y)
                    if r < r_min or r > r_max:
                        continue
                    if any(abs(X - px) < hx + 0.5 and abs(Y - py) < hy + 0.5 for px, py, hx, hy in props_fp):
                        continue
                    feet.append((x, y))
                    plan.append((X, Y))
                if 5 <= len(feet) <= 7 and nn_ok(feet):
                    score = len(feet) - 0.04 * (abs(dx) + abs(dy))
                    if best is None or score > best[0]:
                        best = (score, feet, plan, (c0[0] + dx, c0[1] + dy))
        if best:
            out.append({"name": g.get("name", "군 %d" % (k + 1)), "k": k, "feet": best[1], "plan": best[2], "center": best[3]})
        else:
            REPORT["notes"].append("인물 군 자리 없음: %s" % g.get("name", k))
    return out


def draw_arena():
    cx, cy = AR_C
    Tz = AR_T
    octs = [tuple(p) for p in HERO["base_oct_screen"]]
    iso = Iso(P, cx, cy)
    tot = sum(t for t, _ in STRATA7)
    lay = [(t * Tz / tot, c) for t, c in STRATA7]
    strata_side(P, octs[7], octs[0], lay, f=0.66)
    strata_side(P, octs[1], octs[2], lay, f=0.88)
    draw_cutaway(octs[0], octs[1], Tz)
    P.poly(octs, fill=(212, 196, 164), outline=(92, 70, 44), lw=0.5)
    rng = local_rng("광장결")
    for i in range(170):
        X, Y = (rng.random() * 2 - 1) * 84, (rng.random() * 2 - 1) * 84
        if abs(X) + abs(Y) > 112 or X * X + Y * Y < 72 * 72:
            continue
        x0, y0 = iso.p(X, Y)
        dx, dy = (C30, 0.5) if rng.random() < 0.5 else (-C30, 0.5)
        ln = 1.4 + rng.random() * 2.4
        P.line([(x0, y0), (x0 + dx * ln, y0 + dy * ln)], (192, 176, 144), 0.18, joint=False)
    gx = (483.1 - HERO["center_plan"][0])                            # 문 길(아피아 가도 문 · 하역장 길 문)
    for (Xa, Xb, Ya, Yb) in ((gx - 4.6, gx + 4.6, -83.2, -66.0), (-4.6, 4.6, 66.0, 83.2)):
        iso.poly3([(Xa, Ya, 0.02), (Xb, Ya, 0.02), (Xb, Yb, 0.02), (Xa, Yb, 0.02)], fill=(226, 212, 182), ol=(190, 172, 136), lw=0.15)
    iso.ell(0, 0, 0, RING_O + 3.0, fill=(222, 208, 178), ol=(176, 158, 124), lw=0.2)
    back = Mesh(None)
    for i, th in enumerate((198, 212, 246, 262, 296, 306)):
        t = math.radians(th)
        back.extend(m_cypress(80 * math.cos(t), 80 * math.sin(t), 0, 12.0, 1.7, key="아레나뒤%d" % i))
    back.extend(m_olive(82 * math.cos(math.radians(230)), 82 * math.sin(math.radians(230)), 0, 7.0, 2.8, key="아레나뒤올리브"))
    back.draw(iso, lw=0.06)

    def rp(r, th, z):
        return arena_rp(r, th, z)
    TRV = (210, 188, 146)
    ARCH_D = (104, 80, 52)
    faces = []
    th = 135.0
    while th < 315.0 - 1e-6:
        t1 = min(315.0, th + 3.0)
        tm = (th + t1) / 2.0
        n = (-math.cos(math.radians(tm)), -math.sin(math.radians(tm)), 0.0)
        faces.append((math.cos(math.radians(tm)) + math.sin(math.radians(tm)), th, t1, hwall(tm), lit(TRV, n)))
        th = t1
    for _, t0, t1, h, col in sorted(faces):
        P.poly([rp(RING_I, t0, 0), rp(RING_I, t1, 0), rp(RING_I, t1, h), rp(RING_I, t0, h)], fill=col)

    def arch_on(r, thc, hw_deg, z0, z1, col):
        ha = r * math.radians(hw_deg)
        pts = [rp(r, thc - hw_deg, z0), rp(r, thc + hw_deg, z0), rp(r, thc + hw_deg, z1)]
        for i in range(1, 9):
            sx = 1 - 2 * i / 9.0
            pts.append(rp(r, thc + hw_deg * sx, z1 + ha * math.sqrt(max(0.0, 1 - sx * sx))))
        pts.append(rp(r, thc - hw_deg, z1))
        P.poly(pts, fill=col)

    def rows_for(h):
        if h >= 55:
            return [(2, 10), (15.5, 23.5), (29, 37)]
        if h >= 24:
            return [(2, 10), (14, 21)]
        return [(1.6, 7.0)]
    ai = HERO_IN.get("arcade", {})
    j_mm = float(ai.get("inner_face_mm", 1.5))
    gap_mm = float(ai.get("layer_gap_mm", 3.0))

    def arch_pts(r, thc, hw_deg, z0, z1):
        ha = r * math.radians(hw_deg)
        pts = [rp(r, thc - hw_deg, z0), rp(r, thc + hw_deg, z0), rp(r, thc + hw_deg, z1)]
        for i in range(1, 9):
            sx = 1 - 2 * i / 9.0
            pts.append(rp(r, thc + hw_deg * sx, z1 + ha * math.sqrt(max(0.0, 1 - sx * sx))))
        pts.append(rp(r, thc - hw_deg, z1))
        return pts

    def arch_deep(thc, hw_deg, z0, z1):
        """안쪽 면 아치: 안쪽 회랑(어두움) → 3mm 뒤 바깥 아케이드의 아치(밝음) → 보이는 쪽 아치 안쪽 면 1.5mm"""
        op = arch_pts(RING_I - 0.02, thc, hw_deg, z0, z1)
        P.poly(op, fill=ARCH_D)
        far = clip_convex(arch_pts(RING_I + gap_mm, thc, hw_deg * 0.82, z0 + 0.4, z1 - 0.2), op)
        if len(far) >= 3:
            P.poly(far, fill=(206, 182, 140))
        t = math.radians(thc)
        tan_vis = (-math.sin(t) + math.cos(t))
        tj = thc - hw_deg if tan_vis > 0 else thc + hw_deg
        rx = abs(C30 * (math.cos(t) - math.sin(t))) or 0.5
        dep = max(1.2, min(4.0, j_mm / rx))
        jamb = clip_convex([rp(RING_I, tj, z0), rp(RING_I + dep, tj, z0), rp(RING_I + dep, tj, z1 + 1.0), rp(RING_I, tj, z1 + 1.0)], op)
        if len(jamb) >= 3:
            P.poly(jamb, fill=(168, 136, 96))
    th = 139.5
    while th < 314.0:
        h = min(hwall(th - 2.3), hwall(th + 2.3))
        for (z0, z1) in rows_for(h):
            if z1 + 3.0 < h:
                arch_deep(th, 2.0, z0, z1)
        if h >= 55:
            p0, p1 = rp(RING_I - 0.02, th - 1.0, 44.5), rp(RING_I - 0.02, th + 1.0, 48.5)
            P.rect(min(p0[0], p1[0]), min(p0[1], p1[1]), max(p0[0], p1[0]), max(p0[1], p1[1]), fill=(110, 84, 54))
        th += 7.0
    for zc in (13.0, 26.5, 40.0, 52.5):
        seg = [t for t in range(150, 236) if hwall(t + 0.5) > zc + 1.0]
        if len(seg) > 2:
            P.line([rp(RING_I - 0.03, t, zc) for t in seg], (232, 216, 182), 0.32)
    for t in range(138, 316, 3):                                     # 들쭉날쭉 끝의 단면(보이는 쪽만)
        ha, hb = hwall(t - 1.5), hwall(t + 1.5)
        if abs(ha - hb) < 0.5:
            continue
        tr = math.radians(t)
        n = (math.sin(tr), -math.cos(tr)) if hb > ha else (-math.sin(tr), math.cos(tr))
        if n[0] + n[1] <= 0:
            continue
        lo, hi = min(ha, hb), max(ha, hb)
        P.poly([rp(RING_I, t, lo), rp(RING_O, t, lo), rp(RING_O, t, hi), rp(RING_I, t, hi)], fill=lit(TRV, (n[0], n[1], 0.0)))
    for t0 in range(135, 315, 3):
        t1 = t0 + 3
        h0, h1 = hwall(t0 + 0.01), hwall(t1 - 0.01)
        P.poly([rp(RING_I, t0, h0), rp(RING_O, t0, h0), rp(RING_O, t1, h1), rp(RING_I, t1, h1)], fill=(226, 208, 170), outline=(176, 154, 116), lw=0.1)
    si = HERO_IN.get("seating", {})
    n_tier = int(si.get("tiers", 4))
    n_st = int(si.get("radial_stairs", 12))
    st_every = float(si.get("stair_every_deg", 360.0 / max(1, n_st)))
    st_w = float(si.get("stair_w_mm", 2.5))
    steps = 8
    tier_cols = [(232, 214, 176), (216, 196, 158), (226, 206, 168), (204, 184, 146)]
    rr_ = [RING_I - 0.5 - i * 2.9 for i in range(steps)]
    zz_ = [11.0 - i * 1.25 for i in range(steps)]
    per = max(1, steps // n_tier)
    for i in range(steps):                                           # 관람석(카베아) 동심 단: 4층(마이아니아나) 구분
        ex, ey = iso.p(0, 0, zz_[i])
        tier = min(n_tier - 1, i // per)
        col = tier_cols[tier % 4] if i % per == 0 else shade(tier_cols[tier % 4], 0.94)
        P.ell(ex, ey, 1.2247 * rr_[i], 0.7071 * rr_[i], fill=col, outline=(160, 136, 100), lw=0.15)
    for k in range(1, n_tier):                                       # 층 사이 통로(프라이킨크티오)
        i = k * per
        ex, ey = iso.p(0, 0, zz_[i] + 0.05)
        P.ell(ex, ey, 1.2247 * (rr_[i] + 0.5), 0.7071 * (rr_[i] + 0.5), outline=(246, 236, 210), lw=0.45)
    r_hi, r_lo = RING_I - 0.6, rr_[-1] - 1.6
    for k in range(n_st):                                            # 방사 계단 12개 + 계단 자리 출입구(보미토리움)
        t = k * st_every + 15.0
        dl = math.degrees((st_w / 1.15) / 2.0 / ((r_hi + r_lo) / 2.0))
        P.poly([rp(r_hi, t - dl, 10.6), rp(r_hi, t + dl, 10.6), rp(r_lo, t + dl * 1.25, 2.0), rp(r_lo, t - dl * 1.25, 2.0)], fill=(240, 230, 204))
        for q in range(1, 8):
            f = q / 8.0
            r_ = r_hi + (r_lo - r_hi) * f
            z_ = 10.6 + (2.0 - 10.6) * f
            P.line([rp(r_, t - dl, z_), rp(r_, t + dl, z_)], (196, 176, 140), 0.1, joint=False)
        for kk in range(1, n_tier):
            i = kk * per
            a0_, a1_ = t + dl + 0.6, t + dl + 2.6
            r0_, z0_ = rr_[i] + 0.3, zz_[i]
            P.poly([rp(r0_, a0_, z0_), rp(r0_, a1_, z0_), rp(r0_, a1_, z0_ + 1.6), rp(r0_, a0_, z0_ + 1.6)], fill=(96, 72, 48))
    rf = 34.0                                                        # 아레나 바닥: 오른쪽 반 복원 나무 바닥, 왼쪽 반 하이포게움(노출)
    draw_hypogeum(iso, rf)
    fx, fy = iso.p(0, 0, 1.2)
    P.pie(fx, fy, 1.2247 * rf - 0.2, 0.7071 * rf - 0.2, 270, 90, fill=(186, 146, 98))
    isf = Iso(P, fx, fy)
    for j in range(-12, 13):
        Y0 = j * 2.6
        lim = rf - 0.8
        if abs(Y0) >= lim:
            continue
        xe = math.sqrt(lim * lim - Y0 * Y0)
        xs = max(Y0 + 0.5, -xe)
        if xs < xe - 0.8:
            isf.line3([(xs, Y0, 0.0), (xe, Y0, 0.0)], (152, 114, 74), 0.13)
    P.arc(fx, fy, 1.2247 * rf, 0.7071 * rf, 270, 90, (78, 58, 38), 0.35)
    P.line([(fx, fy - 0.7071 * rf + 0.2), (fx, fy + 0.7071 * rf - 0.2)], (78, 58, 38), 0.3, joint=False)
    faces = []                                                       # 앞쪽 벽 바깥 면(θ 315→495)
    th = 315.0
    while th < 495.0 - 1e-6:
        t1 = min(495.0, th + 3.0)
        tm = (th + t1) / 2.0
        n = (math.cos(math.radians(tm)), math.sin(math.radians(tm)), 0.0)
        faces.append((math.cos(math.radians(tm)) + math.sin(math.radians(tm)), th, t1, hwall(tm), lit(TRV, n)))
        th = t1
    for _, t0, t1, h, col in sorted(faces):
        P.poly([rp(RING_O, t0, 0), rp(RING_O, t1, 0), rp(RING_O, t1, h), rp(RING_O, t0, h)], fill=col)
    th = 318.5
    while th < 494.0:
        h = min(hwall(th - 2.3), hwall(th + 2.3))
        for (z0, z1) in rows_for(h):
            if z1 + 2.6 < h:
                arch_on(RING_O + 0.02, th, 2.2, z0, z1, (100, 74, 46))
        th += 7.5
    P.line([rp(RING_O + 0.03, t, 13.0) for t in range(316, 330)], (236, 222, 190), 0.35)
    for t in range(316, 496, 3):
        ha, hb = hwall(t - 1.5), hwall(t + 1.5)
        if abs(ha - hb) < 0.5:
            continue
        tr = math.radians(t)
        n = (math.sin(tr), -math.cos(tr)) if hb > ha else (-math.sin(tr), math.cos(tr))
        if n[0] + n[1] <= 0:
            continue
        lo, hi = min(ha, hb), max(ha, hb)
        P.poly([rp(RING_I, t, lo), rp(RING_O, t, lo), rp(RING_O, t, hi), rp(RING_I, t, hi)], fill=lit(TRV, (n[0], n[1], 0.0)))
    for t0 in range(315, 495, 3):
        t1 = t0 + 3
        h0, h1 = hwall(t0 + 0.01), hwall(t1 - 0.01)
        P.poly([rp(RING_I, t0, h0), rp(RING_O, t0, h0), rp(RING_O, t1, h1), rp(RING_I, t1, h1)], fill=(226, 208, 170), outline=(176, 154, 116), lw=0.1)
    front = Mesh(None)                                               # 앞 광장 소품(LocalBanana): 올리브·기둥 폐허·노점·암포라·사람
    for i, th in enumerate((104, 118, 130, 140)):
        t = math.radians(th)
        front.extend(m_olive(80 * math.cos(t), 80 * math.sin(t), 0, 8.0, 2.8, key="아레나앞%d" % i))
    for i, th in enumerate((30, 40, 50, 60)):
        t = math.radians(th)
        front.extend(m_cyl(79 * math.cos(t), 79 * math.sin(t), 1.0, 0, 6.0 if i % 2 else 9.0, (238, 228, 204), n=8))
    for i, (th, c) in enumerate(((12, (196, 72, 60)), (70, (70, 110, 150)))):
        t = math.radians(th)
        front.extend(m_stall(76 * math.cos(t), 76 * math.sin(t), c, key="노점%d" % i))
    front.extend(m_amphorae(76 * math.cos(math.radians(22)), 76 * math.sin(math.radians(22)), key="아레나암포라"))
    props_fp = [(76 * math.cos(math.radians(th)), 76 * math.sin(math.radians(th)), 3.3, 2.5) for th in (12, 70)]
    props_fp += [(76 * math.cos(math.radians(22)), 76 * math.sin(math.radians(22)), 2.4, 2.4)]
    props_fp += [(79 * math.cos(math.radians(th)), 79 * math.sin(math.radians(th)), 1.6, 1.6) for th in (30, 40, 50, 60)]
    props_fp += [(80 * math.cos(math.radians(th)), 80 * math.sin(math.radians(th)), 3.2, 3.2) for th in (104, 118, 130, 140)]
    groups = crowd_groups(iso, props_fp)
    for g in groups:
        for i, (X, Y) in enumerate(g["plan"]):
            front.extend(m_person(X, Y, 0, H_PERSON, CLOTHS[(i + g["k"]) % 6], key="군%d사람%d" % (g["k"], i)))
    front.draw(iso, lw=0.06)
    for g in groups:
        DRAWN["crowds"].append({"name": g["name"], "center": [round(v, 2) for v in g["center"]], "feet": [[round(x, 2), round(y, 2)] for x, y in g["feet"]],
                                "n": len(g["feet"]), "height_mm": H_PERSON})
    pts = list(octs) + [(o[0], o[1] + Tz) for o in (octs[7], octs[0], octs[1], octs[2])] + [rp(RING_O, t, hwall(t)) for t in range(0, 360, 2)]
    bb = bbox_of(pts)
    record("hero", HERO["name"], "Core(히어로)", HERO["projected_box"], bb)
    add_fp("콜로세움 받침", _hull(list(octs) + [(o[0], o[1] + Tz) for o in (octs[7], octs[0], octs[1], octs[2])]), "지면")
    add_fp("콜로세움 외벽", arena_wall_sil(), "대상 면")

    def top_y(x):
        best = None
        for tt in range(180, 330):
            q = rp(RING_O, tt + 0.5, hwall(tt + 0.5))
            if abs(q[0] - x) < 1.2:
                best = q[1] if best is None else min(best, q[1])
        return best
    GEO["arena_top_y"] = top_y


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
    m.draw(iso, lw=0.08)
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
    m.draw(ISO, lw=0.08)
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
    m.draw(iso, lw=0.08)
    pts = [iso.p(*p) for p in mesh_pts(m)]
    bb = bbox_of(pts)
    REPORT["objects"][key] = {"사양 상자": d["box"], "그린 외곽": [round(v, 1) for v in bb]}
    add_fp(key, _hull([iso.p(*p) for p in mesh_pts(hull)]), "대상 면")
    return bb


def draw_road_cart(d, key, Xr, Yr, axis="Y", load=LIME_W):
    m = m_cart(0, 0, axis, load, key=key)
    ox, oy = sp(Xr, Yr)
    iso = Iso(P, ox, oy)
    m.draw(iso, lw=0.08)
    wheels(iso, 0, 0, axis)
    pts = [iso.p(*p) for p in mesh_pts(m)]
    bb = bbox_of(pts)
    REPORT["objects"][key] = {"사양 상자": d["box"], "그린 외곽": [round(v, 1) for v in bb]}


def draw_worksite():
    ws = HERO["worksite"]
    box = ws["box"]
    m = Mesh(None)
    for (a, b, c, d_, e, f) in ((0, 0, 0, 13, 0.6, 4.0), (0, 8.4, 0, 13, 9.0, 4.0), (0, 0.6, 0, 0.6, 8.4, 4.0), (12.4, 0.6, 0, 13, 8.4, 4.0)):
        m.extend(m_box(a, b, c, d_, e, f, WOOD, top=WOOD_L))
    m.extend(m_box(0.6, 0.6, 0, 12.4, 8.4, 2.9, (176, 168, 154), top=(190, 182, 168)))
    m.extend(m_person(4.5, 3.6, 2.9, H_PERSON, CLOTHS[0], key="공사1"))
    m.extend(m_person(9.2, 5.8, 2.9, H_PERSON, CLOTHS[3], key="공사2"))
    m.extend(m_cyl(17.5, 2.6, 1.9, 0, 2.1, WOOD, n=10, top=(170, 164, 152)))
    m.extend(m_mound(16.0, 8.4, 0, 2.8, 2.5, LIME_W, key="공사석회"))
    m.extend(m_mound(20.6, 6.4, 0, 2.6, 2.3, ASH_R, key="공사화산재"))
    m.extend(m_mound(21.6, 1.6, 0, 2.2, 1.9, AGG_G, key="공사골재"))
    m.extend(m_person(15.0, 12.0, 0, H_PERSON, CLOTHS[2], key="공사3"))
    pad_ = [(-1, -1, 0), (24, -1, 0), (24, 14, 0), (-1, 14, 0)]
    pts = mesh_pts(m) + pad_
    ox, oy, sc, zs, bb = fit_frame(pts, box, ay="t", sc_max=1.0)
    iso = ZIso(P, ox, oy, sc, zs)
    iso.poly3(pad_, fill=(214, 190, 150), ol=(184, 160, 120), lw=0.2)
    m.draw(iso, lw=0.07)
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
    record("worksite", ws["name"], "Core(히어로 소품)", box, bb)


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
    m.draw(iso, lw=0.07)
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
    m.draw(iso, lw=0.07)
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
    m.draw(iso, lw=0.08)
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


def mark(x, y, letter, r=MARK_R, layer="짝 표지"):
    """짝 표지 A~D: 정보 잉크 원 + 흰 글자"""
    P.ell(x, y, r, r, fill=INK_L, outline=(255, 255, 255), lw=0.25)
    f, em, fa = fface("b", MARK_FACE, letter)
    yb = y + fa / 2.0
    P.text(x, yb, letter, f, (255, 255, 255), anchor="ms")
    bb = f.getbbox(letter, anchor="ms")
    rec_text(letter, "mark", "b", em, fa, box_poly((x + bb[0] / KD, yb + bb[1] / KD, x + bb[2] / KD, yb + bb[3] / KD)), layer)
    return (x - r, y - r, x + r, y + r)


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
    mark(mx, my, d.get("mark", "?"), layer="콜아웃 " + d["id"])
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
            P.poly([(x - 0.9, y), (x - 0.45, y - 0.7), (x + 0.45, y - 0.7), (x + 0.9, y), (x + 0.45, y + 0.7), (x - 0.45, y + 0.7)], fill=(250, 250, 246), outline=(170, 166, 156), lw=0.08)
        else:
            P.ell(x, y, 0.5, 0.5, fill=(236, 228, 210), outline=(170, 160, 140), lw=0.08)
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
        P.rect(x - 0.7, y - 0.5, x + 0.7, y + 0.5, fill=TUFF, outline=(120, 96, 70), lw=0.08)
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


def _leader_target(name):
    """Detail 지시선 이름 → 지도 쪽 대상 지면 다각형 이름"""
    for kw, fp in (("공사장", "공사장 거푸집 앞면"), ("기초 절개", "콜로세움 기초 절개"), ("확대 창 Z1 →", "확대 창 Z1"),
                   ("판테온", "판테온 돔"), ("방파제", "포르투스 외항 방파제"), ("메텔라", "메텔라 드럼")):
        if kw in name:
            return fp
    return None


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
        tname = _leader_target(nm)
        tps = target_polys(tname) if tname else []
        gap = round(min(_pt_poly_gap(pts[0], q_) for q_ in tps), 2) if tps else None
        rec = {"name": nm, "pts": [[round(x, 2), round(y, 2)] for x, y in pts], "dot_d": 2 * DOT_RR, "lw": LEAD_W, "ink": list(INK_L),
               "target": tname, "gap": gap, "first_point": "지도 쪽", "arrow": "패널 쪽 끝" if kind == "basic" else None}
        if letter:
            mp = place_mark(pts)
            mark(mp[0], mp[1], letter, layer="지시선 짝 표지")
            rec["mark"] = {"letter": letter, "c": [round(mp[0], 2), round(mp[1], 2)], "dist": round(math.hypot(mp[0] - pts[0][0], mp[1] - pts[0][1]), 2)}
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
               "베수비오", "바지선", "화산재 운반선", "테베레 하역장·석회 가마", "콜로세움 공사장"]
# 지시선 문법(사양 lead 문장을 렌더 동작으로 옮긴 것): (방식, 쪽, 대상 지면 다각형 이름)
LEAD_RULE = {
    "콜로세움": ("vertical", "R", "콜로세움 외벽"),
    "카라칼라 욕장": ("extend", "R", "욕장 왼쪽 벽 윗면"),
    "트라야누스 시장": ("extend", "L", "시장 오른쪽 동 끝면"),
    "판테온": ("extend", "R", "판테온 돔"),
    "수도교": ("vertical", "R", "수도교 아치 면"),
    "카이킬리아 메텔라 무덤": ("vertical", "L", "메텔라 기단"),
    "포르투스 항": ("vertical2", "R", "포르투스 외항 방파제"),
    "베수비오": ("flag", "L", "베수비오"),
    "바지선": ("flag", "L", "바지선 1"),
    "화산재 운반선": ("ko_ray", "L", "선체"),
}
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
}
TAG_TEXT_FALLBACK = {"테베레 하역장·석회 가마": "하역장·석회 가마", "콜로세움 공사장": "공사장 · ⑤ 다져 넣기"}


def label_strings(slot, key):
    fb = LABEL_TEXT_FALLBACK.get(key, ([], key, None))
    en = slot.get("en") if slot.get("en") is not None else fb[0]
    ko = slot.get("ko") or fb[1]
    sup = slot.get("sup") if "sup" in slot else fb[2]
    return list(en or []), ko, sup


def label_stack(slot, key, maxw=None, sup_own=False, en_split=False):
    """라벨 글 블록 조판(글자면 기준). 돌려줌: lines[(글, 종류, 글자면, u, 기준선 v, 역할)], W, H, v_rule, base_ko"""
    en, ko, sup = label_strings(slot, key)
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
    body = list(slot.get("body") or [])
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
    v_rule = v_after + 1.5
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
        else:
            T = GEO.get("market_tgt")
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
    elif mode in ("vertical", "vertical2"):
        d = 2.0 if mode == "vertical2" else BRACKET_D
        du = d if side == "R" else -d
        u_end = W if side == "R" else 0.0
        pe = map_pt(M, ax, ay, u_end, vr)
        q = map_pt(M, ax, ay, u_end + du, vr)
        if tname == "콜로세움 외벽":
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
        for k in range(0, 11):                                       # 깃대 = 글 블록 밖 1.5~4.0mm(화면 가로)
            dh = 1.5 + 0.25 * k
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


def _obstacles_for(kind_tag):
    m = _mask_new()
    if not kind_tag:
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
    """슬롯 안에서 글 블록 자리를 고른다(배율 1.00, 줄바꿈·자리 조정만). 간격이 큰 자리 → 짧은 지시선 순"""
    slot = SLOT[key]
    is_tag = "태그" in slot.get("kind", "")
    M = lab_M(slot)
    box = slot["box"]
    dt = _dt(_obstacles_for(is_tag))
    variants = []
    if is_tag:
        variants.append(("tag", None))
    else:
        base = label_stack(slot, key)
        variants.append(("기본", label_stack(slot, key)))
        variants.append(("위첨자 줄", label_stack(slot, key, sup_own=True)))
        variants.append(("영문 2줄", label_stack(slot, key, en_split=True)))
        variants.append(("영문 2줄·위첨자 줄", label_stack(slot, key, sup_own=True, en_split=True)))
        for f in (0.8, 0.65):
            variants.append(("본문 줄바꿈 %.2f" % f, label_stack(slot, key, maxw=base["W"] * f, sup_own=True)))
    best = None
    for vname, st in variants:
        if vname == "tag":
            st = tag_stack(slot)
        W, H = st["W"], st["H"]
        ext = bbox_of(lab_poly(M, 0, 0, W, H))
        axs = (box[0] + 0.3 - ext[0], box[2] - 0.3 - ext[2])
        ays = (box[1] + 0.3 - ext[1], box[3] - 0.3 - ext[3])
        over = max(0.0, axs[0] - axs[1], ays[0] - ays[1])
        nx = max(1, int((axs[1] - axs[0]) / 0.5) + 1) if axs[1] >= axs[0] else 1
        ny = max(1, int((ays[1] - ays[0]) / 0.5) + 1) if ays[1] >= ays[0] else 1
        for i in range(nx):
            ax = axs[0] + (axs[1] - axs[0]) * (i / (nx - 1) if nx > 1 else 0.5)
            for j in range(ny):
                ay = ays[0] + (ays[1] - ays[0]) * (j / (ny - 1) if ny > 1 else 0.5)
                poly = lab_poly(M, ax, ay, W, H)
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
                e_ = bbox_of(poly)
                off_c = math.hypot((e_[0] + e_[2]) / 2.0 - cxs, (e_[1] + e_[3]) / 2.0 - cys)
                score = (0.0 if over <= 0.45 else -over, min(cl, LABEL_CLEAR), -L_len * 0.02 - (0.3 if vname not in ("기본", "tag") else 0.0) - off_c * 0.01)
                if best is None or score > best[0]:
                    best = (score, vname, st, ax, ay, poly, ld, cl, over)
    if best is None:
        REPORT["notes"].append("라벨 자리 없음: %s" % key)
        return None
    score, vname, st, ax, ay, poly, ld, cl, over = best
    LABEL_PLAN[key] = dict(M=M, ax=ax, ay=ay, st=st, poly=poly, lead=ld, clear=cl, variant=vname, over=over, tag=is_tag)
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
            ex_line(info["lead"][0], 2.4)


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
    for (s, kind, face, u, vb, role) in st["lines"]:
        ft, em, fa = fface(kind, face, s)
        f.text(u, vb, s, ft, INK_L)
        w = tw(s, ft)
        poly = [map_pt(M, ax, ay, uu, vv) for uu, vv in ((u, vb - fa), (u + w, vb - fa), (u + w, vb + 0.25), (u, vb + 0.25))]
        rec_text(s, role, kind, em, fa, poly, layer="지도 라벨 " + key, pitch=LF_PITCH if role == "label_body" and len(st["body"]) > 1 else None)
        faces.setdefault(role.replace("label_", ""), round(fa, 3))
    if st["has_rule"]:
        f.line(0, st["v_rule"], W, st["v_rule"], INK_L, 0.25)
    affine_paste(P, f, M, ax, ay)
    rec = {"name": key, "kind": slot.get("kind", ""), "poly": [[round(x, 2), round(y, 2)] for x, y in info["poly"]],
           "dir": "↗" if M is M_WALL_UP else "↘", "scale": 1.0, "slot": list(slot["box"]), "faces": faces, "pitch": LF_PITCH,
           "en": st["en"], "ko": label_strings(slot, key)[1], "sup": label_strings(slot, key)[2], "body": st["body"], "variant": info["variant"],
           "slot_over_mm": round(info["over"], 2)}
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
        m.draw(iso, lw=0.07)
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
    m.draw(iso, lw=0.06)
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
            P.poly([(px - 0.5, py), (px, py - 0.6), (px + 0.5, py), (px, py + 0.6)], fill=(255, 255, 255), outline=(190, 190, 180), lw=0.06)


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


def draw_panel_D():
    x0, y0, x1, y1 = PANEL["D"]["rect"]
    lay = "패널 D"
    panel_header(x0, y0, "LIME CLASTS", "석회 알갱이·자가치유", panel="D")
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
    lms = {k: area(k) for k in ("L1", "L2", "L3", "L4", "L5", "L6") if k in o}
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
    DRAWN["density"] = {"pct": round(100.0 * num / den, 2), "num_mm2": round(num, 1), "den_mm2": round(den, 1), "stage_mm2": round(stage_mm2, 1),
                        "covered_mm2": round(cov_mm2, 1), "landmark_layer_mm2": round(obj_only, 1), "terrain_layer_mm2": round(num - obj_only, 1),
                        "rule": "알파 ≥ 128(랜드마크·소품·사람 층 ∪ 밭·포도밭·구릉·지붕·나무 층) ÷ (무대 − 패널·Detail 덮는 면적). 바탕 지면·강·바다·길·라벨·바닥 글 제외",
                        "target_pct": 39.3}


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
    groups = {"판테온": ["판테온 광장"], "욕장": ["욕장 지면"], "메텔라": ["메텔라 대지"], "시장": ["시장 지면"], "콜로세움": ["콜로세움 받침"]}
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
    DRAWN["stage"] = {"rects": [list(r) for r in STAGE_RECTS]}
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


# ───────────────────────── 11 실행 ─────────────────────────
def main():
    build_info_boxes()
    build_exclusions()
    # 1 바탕 지면
    use_layer(BASE)
    draw_ground()
    draw_river()
    draw_sea()
    draw_coast_section()
    draw_roads()
    draw_floor_texts()
    # 2 랜드마크·소품 층(뒤 → 앞)
    use_layer(OBJ)
    draw_caracalla()
    draw_aqueduct()
    draw_market()
    draw_pantheon()
    draw_kiln()
    draw_barge(PROPS["바지선 1"], "X", "바지선 1")
    ac = PROPS["아피아 가도 수레"]
    apl = ac.get("plan") or [485.6, 72.0]
    draw_road_cart(ac, "아피아 가도 수레", apl[0], apl[1], "Y", ASH_G)
    draw_arena()
    draw_dock()
    mc = PROPS["재료 수레"]
    mpl = mc.get("plan") or [462.3, 278.0]
    draw_road_cart(mc, "재료 수레", mpl[0], mpl[1], "Y", LIME_W)
    draw_metella()
    draw_portus()
    draw_barge(PROPS["바지선 2"], "Y", "바지선 2")
    draw_worksite()
    draw_ostia()
    draw_villa()
    draw_ash_ship()
    # 3 라벨 자리 잡기(랜드마크 실측 외곽 기준). 지형 층의 베수비오는 외곽만 먼저 등록한다(깃대 대상)
    use_layer(BASE)
    _v = ves_geom()
    add_fp("베수비오", _v[7], "배경 산")
    plan_labels()
    # 4 지형 층(밭·먼 밭·베수비오·농장·구릉·지붕·나무) — 랜드마크 층 아래로 합성
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
    # 5 Detail·라벨·틀
    draw_z1()
    draw_c1()
    draw_c2()
    draw_c4()
    draw_leaders()
    draw_labels()
    draw_title()
    draw_panel_L()
    draw_panel_B()
    draw_panel_D()
    draw_panel_S()
    # 6 기록·검사(그리지 않는다)
    overlap_check()
    hierarchy_check()
    measure_density()
    measure_label_clearance()
    measure_road_gaps()
    out = BASE.img.resize((PW * OUT_PX_PER_MM, PH * OUT_PX_PER_MM), Image.LANCZOS).convert("RGB")
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    out.save(OUT, optimize=True)
    write_drawn()
    REPORT["output"] = OUT
    REPORT["drawn"] = DRAWN_PATH
    REPORT["size_px"] = out.size
    REPORT["density"] = DRAWN["density"].get("pct")
    REPORT["tier_color_uses"] = TIER_USES[0]
    REPORT["seconds"] = round(time.time() - T_START, 1)
    print(json.dumps(REPORT, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
