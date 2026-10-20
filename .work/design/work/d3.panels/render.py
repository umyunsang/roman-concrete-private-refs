# -*- coding: utf-8 -*-
"""로마 편 최종 배치 다이어그램 v2(새 정보 위계) — final_layout_spec-v2-새위계.json을 읽어
A2 배치 다이어그램 PNG(1mm = 3px, 1260×1782)를 그린다.

실행: uv run --no-project --with pillow python -I /Users/um-yunsang/roman-concrete-private-refs/.work/scripts/diagrams/final_layout-v2-새위계.py [출력 PNG]
- 바탕: 이전 최종 다이어그램 스크립트(final_layout.py)의 그리기 도구 + v16 common.py·prim.py(레이어·글꼴·등각 글자·로우폴리 메시).
  이전 스크립트·이전 PNG는 건드리지 않는다.
- 새 위계(사용자 결정 2026-10-18 23:43)
  Core    = 로마 건축물 지도(콜로세움 히어로 + 판테온·트라야누스 시장·카라칼라 욕장(절개)·수도교·메텔라 무덤·포르투스, 배경 베수비오)
  Basic   = L 로마 콘크리트란? · R 위치도 · B 제작 과정 6단계 · T 연대기
  Detail  = 확대 창 Z1 · 콜아웃 C1·C2·C4 · D 석회 알갱이·자가치유 패널
  Support = S 현대 콘크리트 약 100년 vs 로마 콘크리트 2,000년(가장 작은 위계)
- 좌표: A2 mm(x 오른쪽, y 아래). 등각: 평면 +X → 화면 ↘, +Y → 화면 ↙, +Z → 위. 평면 원점 = 화면 (0, 0)(사양 규약 = v16 common.Iso)
- 그리는 순서: 지면 → 밭·구릉 → 강 → 바다·해안 → 길 → 바닥 글 → 지붕·나무 → 랜드마크·소품(뒤→앞)
  → Detail(확대 창·콜아웃·지시선) → 지도 라벨 → 틀(타이틀·패널·푸터·눈금) → 주석(티어 색 모서리·꼬리표·히어로 군 윤곽)
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
from PIL import Image, ImageDraw, ImageFilter, ImageChops

T_START = time.time()
SPEC_PATH = sys.argv[2] if len(sys.argv) > 2 else ROOT + "/.work/out/refs-analysis/final_layout_spec-v2-새위계.json"
SIL_PATH = sys.argv[3] if len(sys.argv) > 3 else ROOT + "/.work/out/refs-analysis/_work_v2/v2_hero_cluster_sil.npy"
OUT = sys.argv[1] if len(sys.argv) > 1 else ROOT + "/docs/design/최종-배치-다이어그램-v2-새위계.png"
OUT_PX_PER_MM = 3

with open(SPEC_PATH, encoding="utf-8") as fh:
    S = json.load(fh)
META, HI, FR, CM = S["meta"], S["hierarchy"], S["frame"], S["core_map"]
HERO, RV, SC, PG = CM["hero"], CM["river"], CM["sea_coast"], CM["portus_geometry"]
LBS = CM["labels"]
BAS, DET, SUP, MEAS = S["basic"], S["detail"], S["support"], S["measurements"]
STAGE = tuple(FR["stage"]["rect"])
PANEL = {p["id"]: p for p in FR["panels"]}
LM = {l["id"]: l for l in CM["landmarks"]}
VES = CM["background"][0]
PROPS = {p["name"].split("(")[0].strip(): p for p in CM["props"]}
DMAP = {d["id"]: d for d in DET["map_elements"]}
SLOT = {s["name"].split("(")[0].strip(): s for s in LBS["slots"]}
FLOOR = {f["name"].split(" ")[0]: f for f in LBS["floor_text"]}
SIZE = {r["name"]: r for r in HI["size_table"]}
REPORT = {"objects": {}, "labels": {}, "notes": []}
GEO = {}
LABEL_POLYS = []     # (이름, 화면 다각형) — 겹침 검사용
INFO_POLYS = []      # (이름, 화면 다각형) — 콜아웃·패널·확대 창(라벨과 겹치면 안 됨)

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
INK_L = (58, 42, 28)            # 지도 라벨 잉크(땅 위 짙은 갈색)
INK_WATER = (236, 246, 252)     # 물 위 바닥 글(밝은 크림)
PLATE = (250, 244, 228, 168)
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
# 새 티어 색(다이어그램 주석 전용 — 사양 미리보기 COL과 같은 값). 포스터에는 티어 배지·범례를 두지 않는다.
T_COL = {"Core": (47, 107, 58), "Basic": (63, 58, 160), "Detail": (208, 101, 14), "Support": (47, 127, 134)}
T_TXT = {"Core": (29, 80, 40), "Basic": (52, 46, 138), "Detail": (150, 66, 0), "Support": (24, 92, 98)}
ACCENT = (200, 34, 54)          # 폼페이 레드(#c82236): 타이틀·패널 머리글·제작 과정 단계 번호에만
H_PERSON = 5.0


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


def pill(L, x, y, text, col, em=2.2, anchor="l", fill=(255, 251, 242, 236), bold=True):
    """다이어그램 주석 꼬리표(정면 글자). (x, y) = 꼬리표 왼쪽 위(l) · 가운데 위(c) · 오른쪽 위(r)"""
    f = fnt("b" if bold else "m", em)
    w = tw(text, f) + 2.0
    h = em * 1.38
    if anchor == "c":
        x -= w / 2.0
    elif anchor == "r":
        x -= w
    rrect(L, x, y, x + w, y + h, h * 0.32, fill=fill, outline=tuple(col[:3]) + (230,), lw=0.28)
    L.text(x + 1.0, y + h * 0.76, text, f, col)
    INFO_POLYS.append(("꼬리표:" + text[:14], [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]))
    return (x, y, x + w, y + h)


def corner_marks(L, box, col, arm=3.2, lw=0.32):
    x0, y0, x1, y1 = box
    for (x, y, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        L.line([(x + dx * arm, y), (x, y), (x, y + dy * arm)], col, lw, joint=False)


def strata_side(L, a, b, layers, f=0.83):
    """화면 변 a→b 아래로 지층 옆면(층마다 수직 두께)"""
    d0 = 0.0
    for t, col in layers:
        L.poly([(a[0], a[1] + d0), (b[0], b[1] + d0), (b[0], b[1] + d0 + t), (a[0], a[1] + d0 + t)], fill=tint(col, f))
        d0 += t
    L.line([a, b, (b[0], b[1] + d0), (a[0], a[1] + d0), a], (70, 50, 32), 0.2)


def plan_band(p0, p1, w, ext0=0.0, ext1=0.0):
    """평면 선분 p0→p1을 화면 수직 폭 w의 띠로(사양 v2_check와 같다: 평면 반폭 = w / (2·cos30))"""
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


def wheels(iso, X, Y, axis="Y"):
    pos = [(X + 2.6, Y), (X - 2.6, Y)] if axis == "Y" else [(X, Y + 2.6), (X, Y - 2.6)]
    for (a, b) in pos:
        cx, cy = iso.p(a, b, 1.5)
        P.ell(cx, cy, 1.5, 1.5, fill=(90, 66, 44), outline=(60, 44, 30), lw=0.15)


P = Layer(0, 0, PW, PH, "최종배치v2", bg=BG + (255,))
ISO = Iso(P, 0.0, 0.0)


# ───────────────────────── 빈 자리 마스크(지붕·나무·밭이 라벨·패널·길을 덮지 않게) ─────────────────────────
EXK = 2      # 마스크 해상도 px/mm
EXCL = Image.new("L", (PW * EXK, PH * EXK), 0)
EXD = ImageDraw.Draw(EXCL)


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


def poly_free(poly, pad=0.0, stage=True):
    x0, y0, x1, y1 = bbox_of(poly)
    if stage and (y0 < STAGE[1] + 0.5 or y1 > STAGE[3] - 0.5 or x1 < 0 or x0 > PW):
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
    out = []
    # TIBERIS 테베레강: ↘ 팔 물 위, 글 높이 가운데가 중심선(평면 Y 314)에 오게
    a = FLOOR["TIBERIS"]["anchor"]
    Yb = RIV_Y + 1.6
    Xs = a[0] / C30 + Yb
    ax, ay = sp(Xs, Yb)
    out.append(dict(name="TIBERIS 테베레강", M=M_FLOOR_SE, ax=ax, ay=ay, cap=3.3,
                    parts=[("TIBERIS", fnt("en", 4.6), INK_WATER), ("테베레강", fnt("b", 3.6), INK_WATER)]))
    # MARE TYRRHENUM: 두 줄(한 줄이면 36mm 안에 들지 않아 하단 띠를 침범) — 왼쪽 아래 열린 바다
    a = FLOOR["MARE"]["anchor"]
    ax, ay = a[0] + 6.5, a[1] - 4.0
    out.append(dict(name="MARE TYRRHENUM", M=M_FLOOR_SE, ax=ax, ay=ay, cap=3.3, parts=[("MARE TYRRHENUM", fnt("en", 4.6), INK_WATER)]))
    q = map_pt(M_FLOOR_SE, ax, ay, 0.0, 5.2)
    out.append(dict(name="티레니아해", M=M_FLOOR_SE, ax=q[0], ay=q[1], cap=2.8, parts=[("티레니아해", fnt("b", 3.6), INK_WATER)]))
    # VIA APPIA: 위 차선(평면 X 473.9~483.1) 안, ↗ 바닥 글
    ap = [r for r in CM["roads"] if r["id"] == "R1"][0]
    Xc = ap["plan_pts"][0][0]
    Xb = Xc - 1.5
    a = FLOOR["VIA"]["anchor"]
    Ys = Xb - (a[0] + 2.0) / C30
    ax, ay = sp(Xb, Ys)
    out.append(dict(name="VIA APPIA 아피아 가도 → 캄파니아", M=M_FLOOR_NE, ax=ax, ay=ay, cap=3.1,
                    parts=[("VIA APPIA", fnt("en", 4.4), (98, 78, 50)), ("아피아 가도 → 캄파니아", fnt("b", 3.2), (98, 78, 50))]))
    # COLLI ALBANI: 두 줄
    a = FLOOR["COLLI"]["anchor"]
    out.append(dict(name="COLLI ALBANI", M=M_FLOOR_SE, ax=a[0], ay=a[1], cap=2.9, parts=[("COLLI ALBANI", fnt("en", 4.0), (96, 92, 58))]))
    q = map_pt(M_FLOOR_SE, a[0], a[1], 0.0, 4.4)
    out.append(dict(name="알바노 구릉", M=M_FLOOR_SE, ax=q[0], ay=q[1], cap=2.2, parts=[("알바노 구릉 — 로마 건물의 화산재", fnt("b", 2.8), (96, 92, 58))]))
    # OSTIA
    a = FLOOR["OSTIA"]["anchor"]
    out.append(dict(name="OSTIA 오스티아", M=M_FLOOR_SE, ax=a[0], ay=a[1], cap=3.0, parts=[("OSTIA", fnt("en", 4.2), (104, 84, 56)), ("오스티아", fnt("b", 3.2), (104, 84, 56))]))
    for f in out:
        W = sum(tw(t, ft) + 1.6 for t, ft, _c in f["parts"]) - 1.6
        f["W"] = W
        f["poly"] = [map_pt(f["M"], f["ax"], f["ay"], u, v) for u, v in ((0, -f["cap"]), (W, -f["cap"]), (W, 0.9), (0, 0.9))]
    return out


FLOORS = floor_specs()


def build_exclusions():
    for l in CM["landmarks"]:
        ex_rect(l["projected_box"], 1.4)
    ex_rect(VES["projected_box"], 1.0)
    octs = [tuple(p) for p in HERO["base_oct_screen"]]
    ex_poly(octs, 1.6)
    ex_poly([octs[7], octs[0], octs[1], octs[2], (octs[2][0], octs[2][1] + AR_T), (octs[1][0], octs[1][1] + AR_T),
             (octs[0][0], octs[0][1] + AR_T), (octs[7][0], octs[7][1] + AR_T)], 1.6)
    ex_poly(arena_wall_sil(), 1.5)
    ex_rect(HERO["worksite"]["box"], 1.5)
    for p in CM["props"]:
        ex_rect(p["box"], 1.0)
    for s_ in LBS["slots"]:
        key = s_["name"].split("(")[0].strip()
        if "anchor" in LABEL_CFGS.get(key, {}):
            continue
        ex_rect(s_["box"], 1.6)
    for f in FLOORS:
        ex_poly(f["poly"], 1.0)
    for d in DET["map_elements"]:
        if d["kind"] == "확대 창":
            ex_circle(d["circle"]["c"], d["circle"]["d"] / 2.0, 2.0)
        else:
            ex_rect(d["box"], 1.6)
    ex_rect((211.0, 425.0, 244.0, 482.0), 0.8)           # 확대 창 Z1 글 칸
    ex_rect(PANEL["S"]["rect"], 2.0)
    ex_rect((350.0, 461.5, 402.5, 466.0), 0.5)           # S 꼬리표 자리
    for ld in DET["leaders"]:
        ex_line([tuple(p) for p in ld["pts"]], 2.6)
    ex_line([tuple(p) for p in BAS["process_representation"]["link"]["pts"]], 2.6)
    for r in CM["roads"]:
        p0, p1 = [tuple(p) for p in r["plan_pts"]]
        ex_poly(plan_band(p0, p1, r["w_screen_perp_mm"], 0.0, 14.0 if r["id"] == "R1" else 0.0), 0.9)
    ex_poly([tuple(p) for p in RV["polygon_screen"]], 1.2)
    ex_poly([tuple(p) for p in SC["sea_polygon"]], 1.5)
    (x0s, y0s), (x1s, y1s) = CM["aqueduct"]["ground_line_screen"]
    H = CM["aqueduct"]["arch_height_mm"]
    ex_poly([(x0s, y0s - H - 1), (x1s, y1s - H - 1), (x1s, y1s + 2), (x0s, y0s + 2)], 1.0)
    # 다이어그램 꼬리표 자리(지붕·나무·밭이 덮지 않게)
    for b in ((290.0, 384.5, 352.5, 397.0), (1.5, 301.0, 82.0, 305.2), (370.0, 208.8, 420.0, 213.0), (366.0, 283.8, 420.0, 288.0),
              (326.0, 461.4, 402.5, 466.0), (148.0, 488.2, 208.6, 491.4), (278.0, 482.4, 332.0, 485.6), (1.5, 92.4, 118.0, 95.6)):
        ex_rect(b, 0.3)


# ───────────────────────── 1 지면·밭·구릉 ─────────────────────────
def draw_ground():
    sx0, sy0, sx1, sy1 = STAGE
    P.rect(sx0, sy0, sx1, sy1, fill=GROUND)
    G = Layer(sx0, sy0, sx1, sy1)
    span = (sx1 - sx0) * T30
    for k in range(-40, 60):
        y0 = sy0 + k * 14.0
        G.line([(sx0, y0), (sx1, y0 + span)], GRID_OP, 0.16, joint=False)
        G.line([(sx0, y0 + span), (sx1, y0)], GRID_OP, 0.16, joint=False)
    P.paste(G)


FIELD_BASE = {"vine": (186, 190, 122), "wheat": WHEAT_C, "pasture": PASTURE_C, "fallow": (216, 198, 152), "olive": (186, 192, 128)}


def texture(L, kind, X0, Y0, X1, Y1, key):
    rng = local_rng(key)
    base = FIELD_BASE[kind]
    poly = [sp(X0, Y0), sp(X1, Y0), sp(X1, Y1), sp(X0, Y1)]
    L.poly(poly, fill=base, outline=shade(base, 0.82), lw=0.2)
    if kind == "wheat":
        Y = Y0 + 1.5
        while Y < Y1 - 0.7:
            L.line([sp(X0 + 0.7, Y), sp(X1 - 0.7, Y)], shade(base, 0.86), 0.18, joint=False)
            Y += 1.8
    elif kind == "vine":
        X = X0 + 1.3
        while X < X1 - 0.7:
            L.line([sp(X, Y0 + 0.8), sp(X, Y1 - 0.8)], VINE_C, 0.42, joint=False)
            L.line([sp(X + 0.5, Y0 + 0.8), sp(X + 0.5, Y1 - 0.8)], (162, 174, 106), 0.14, joint=False)
            X += 2.2
    elif kind == "pasture":
        for _ in range(int((X1 - X0) * (Y1 - Y0) / 26.0) + 1):
            x, y = sp(X0 + 1 + rng.random() * (X1 - X0 - 2), Y0 + 1 + rng.random() * (Y1 - Y0 - 2))
            L.ell(x, y, 0.5, 0.3, fill=(170, 180, 112))
    elif kind == "fallow":
        Y = Y0 + 2.2
        while Y < Y1 - 1:
            L.line([sp(X0 + 1, Y), sp(X1 - 1, Y)], (200, 180, 136), 0.16, joint=False)
            Y += 2.8
    return poly


def place_fields(L, region, Xr, Yr, size, kinds, key, gap=1.1):
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
                bb = bbox_of(poly)
                inside = bb[1] >= STAGE[1] + 0.5 and bb[3] <= STAGE[3] + 6.0
                if inside and poly_free(poly, 0.2, stage=False):
                    kind = kinds[int(h01(key, i, j) * len(kinds)) % len(kinds)]
                    texture(L, kind, X0, Y0, X1, Y1, "%s%d_%d" % (key, i, j))
                    ex_poly(poly, 0.2)
                    n += 1
            Y += sy
            j += 1
        X += sx
        i += 1
    return n


def draw_fields():
    G = Layer(*STAGE)
    n1 = place_fields(G, (290, 392, 430, 512), (540, 780), (130, 360), (15.0, 11.0),
                      ["vine", "vine", "vine", "wheat", "pasture", "vine", "fallow"], "남동밭")
    n2 = place_fields(G, (372, 206, 430, 252), (428, 466), (-31, 34), (13.0, 10.0), ["pasture", "wheat", "fallow", "vine"], "가도밭")
    n3 = place_fields(G, (-20, 322, 66, 372), (300, 430), (324.5, 352), (17.0, 11.0), ["wheat", "wheat", "pasture", "fallow"], "곡식밭")
    n4 = place_fields(G, (150, 425, 252, 505), (548, 660), (300, 380), (13.0, 10.0), ["pasture", "wheat", "fallow", "vine"], "하구밭")
    n5 = place_fields(G, (88, 362, 206, 470), (452, 524), (324.5, 380), (13.0, 10.0), ["wheat", "pasture", "wheat", "fallow"], "포르투스띠")
    P.paste(G)
    REPORT["notes"].append("밭 구획: 남동 교외 %d · 가도 옆 %d · 강 오른쪽 둑 곡식밭 %d · 하구 동쪽 %d · 포르투스 띠 %d" % (n1, n2, n3, n4, n5))


def draw_albano():
    """알바노 구릉 띠: 화산 그림이 아니라 낮은 구릉 지면 결(사양 terrain)"""
    sub = Layer(306, 110, 420, 172)
    isub = Iso(sub, 0, 0)
    m = Mesh(None)
    spots = [(322, 158, 10, 3.4), (342, 153, 14, 5.0), (366, 157, 15, 4.8), (392, 151, 14, 5.6), (414, 159, 11, 4.0),
             (352, 164, 9, 2.6), (404, 165, 8, 2.4), (378, 146, 9, 3.0)]
    for i, (x, y, R, h) in enumerate(spots):
        X, Y = to_plan(x, y)
        m.extend(m_mound(X, Y, 0, R, h, mix((150, 160, 104), GROUND, 0.3), n=11, rings=3, key="알바노%d" % i, jit=0.1, apex_jit=0.15))
    m.draw(isub, lw=0.05)
    for i in range(16):
        x = 318 + h01("알바노올리브", i) * 100
        y = 150 + h01("알바노올리브y", i) * 14
        sub.ell(x, y, 0.9, 0.6, fill=(112, 136, 84))
    merge(P, sub, opacity=0.92, blur=0.08)


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
    for r in CM["roads"]:
        p0, p1 = [tuple(p) for p in r["plan_pts"]]
        ext1 = 14.0 if r["id"] == "R1" else (4.6 if r["id"] == "R3" else 0.0)
        ext0 = {"R2": 30.0, "R3": 30.0}.get(r["id"], 0.0)
        poly = plan_band(p0, p1, r["w_screen_perp_mm"], ext0, ext1)
        col = APPIA_C if r["center_line"] else ROAD_C
        P.poly(poly, fill=col)
        P.line([poly[0], poly[1]], ROAD_EDGE, 0.3, joint=False)
        P.line([poly[3], poly[2]], ROAD_EDGE, 0.3, joint=False)
        if r["center_line"]:
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            Ls = math.hypot(dx, dy)
            e = (p1[0] + dx / Ls * ext1, p1[1] + dy / Ls * ext1)
            P.dashed(sp(*p0), sp(*e), (250, 246, 236), 1.0, 4.0, 2.6)
            rng = local_rng("포석")
            for i in range(90):                         # 현무암 포석 결
                t = rng.random()
                off = (rng.random() * 2 - 1) * 7.6
                X = p0[0] + off
                Y = p0[1] + (e[1] - p0[1]) * t
                x, y = sp(X, Y)
                P.ell(x, y, 0.35, 0.22, fill=(170, 150, 112))
        GEO["road_" + r["id"]] = poly


def draw_floor_texts():
    for f in FLOORS:
        floor_line(P, f["ax"], f["ay"], f["parts"], f["M"])
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
def draw_vesuvius():
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
    sub = Layer(box[0] - 4, box[1] - 4, box[2] + 4, box[3] + 4)
    isub = ZIso(sub, ox, oy, sc, zs)
    m.draw(isub, lw=0.08)
    for f in (0.28, 0.55, 0.8):                                      # 포도밭 비탈(앞 반쪽 등고 줄)
        r_ = 23.0 + (19.6 - 23.0) * f
        z_ = 4.6 * f
        pts = [isub.p(r_ * math.cos(math.radians(t)), r_ * math.sin(math.radians(t)), z_) for t in range(-40, 136, 6)]
        sub.line(pts, mix((96, 126, 70), GROUND, 0.35), 0.22)
    merge(P, sub, opacity=0.9, blur=0.14)
    GEO["ves_iso"] = (ox, oy, sc, zs)
    GEO["ves_bb"] = bb
    GEO["ves_pts"] = [isub.p(*q) for q in allp]
    record("V", VES["name"], VES["tier"], box, bb)
    # 밑동 포도밭 농장(사양 props: 베수비오 밑동을 가린다)
    fb = PROPS["포도밭 농장"]["box"]
    fk = [(0, 0, 0), (27, 0, 0), (27, 15, 0), (0, 15, 0), (3, 2, 7.0)]
    fx, fy, fsc, fzs, fbb = fit_frame(fk, fb, ay="b")
    fiso = ZIso(P, fx, fy, fsc, 1.0)
    poly = [fiso.p(0, 0), fiso.p(27, 0), fiso.p(27, 15), fiso.p(0, 15)]
    P.poly(poly, fill=FIELD_BASE["vine"], outline=shade(FIELD_BASE["vine"], 0.82), lw=0.2)
    X = 1.3
    while X < 26.3:
        P.line([fiso.p(X, 0.8), fiso.p(X, 14.2)], VINE_C, 0.42, joint=False)
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
    record("L3", L3["name"], "Core(표준 랜드마크)", box, bb)


def draw_aqueduct():
    L4 = LM["L4"]
    (x0s, y0s), (x1s, y1s) = CM["aqueduct"]["ground_line_screen"]
    X0, Y0 = to_plan(x0s, y0s)
    X1, _Y1 = to_plan(x1s, y1s)
    H = CM["aqueduct"]["arch_height_mm"]
    T = 1.6
    stone = (206, 158, 106)          # 지면보다 채도를 높인 석재(아쿠아 클라우디아 아치는 석재)
    brick = (190, 104, 72)           # 위 단·보수 구간은 벽돌면
    Xe = X1 + 10.0
    m = Mesh(None)
    m.extend(m_box(X0, Y0 - T, 0, Xe, Y0 + T, H - 3.2, stone, top=(222, 182, 132)))
    m.extend(m_box(X0 - 0.3, Y0 - T - 0.4, H - 3.2, Xe, Y0 + T + 0.4, H, brick, top=(206, 126, 92)))
    m.draw(ISO, lw=0.12)
    pitch = 8.0
    i = 0
    u0 = X0 + 1.4
    while u0 + 5.2 < Xe:
        ISO.arch("L", 0, Y0 + T + 0.02, 0, u0, u0 + 5.3, 0.0, 9.0, (164, 120, 84), (128, 90, 60), 0.12)
        ISO.arch("L", 0, Y0 + T + 0.02, 0, u0 + 0.7, u0 + 4.6, 13.0, 17.2, (164, 120, 84), (128, 90, 60), 0.1)
        if i % 3 == 1:                                              # 보수 구간(벽돌면 콘크리트)
            ISO.fpoly("L", 0, Y0 + T + 0.03, 0, [(u0 + 5.3, 0.4), (u0 + 8.0, 0.4), (u0 + 8.0, H - 3.4), (u0 + 5.3, H - 3.4)], fill=(196, 114, 80))
        u0 += pitch
        i += 1
    ISO.line3([(X0, Y0 - T - 0.2, 12.3), (Xe, Y0 - T - 0.2, 12.3)], (226, 192, 146), 0.35)
    ISO.line3([(X0, Y0, H + 0.05), (Xe, Y0, H + 0.05)], (96, 160, 206), 0.6)
    pts = [ISO.p(X0, Y0 - T - 0.4, H), ISO.p(X0, Y0 + T, 0), ISO.p(Xe, Y0 + T, 0), ISO.p(Xe, Y0 - T, H)]
    bb = bbox_of(pts)
    bb = (bb[0], bb[1], min(bb[2], PW), bb[3] if bb[2] <= PW else (pts[1][1] + (PW - pts[1][0]) * T30))
    GEO["aq_ground"] = lambda x: (pts[1][1] + (x - pts[1][0]) * T30)
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
    q0, q1 = iso.p(12.73, -12.73, 0.0), iso.p(12.73, -12.73, 24.0)
    GEO["pantheon_drum_r"] = (q0[0], q1[1], q0[1])
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
    trees = Mesh(None)
    trees.extend(m_cypress(-19.5, -7.0, 0, 26.0, 2.1, key="메텔라사이프러스1"))
    trees.extend(m_cypress(-8.0, -20.5, 0, 22.0, 2.0, key="메텔라사이프러스2"))
    trees.extend(m_pine(19.0, -14.0, 0, 17.0, 6.2, key="메텔라소나무"))
    trees.extend(m_cypress(19.5, 13.0, 0, 16.0, 1.7, key="메텔라사이프러스3"))
    ppl = Mesh(None)
    ppl.extend(m_person(-12.0, 19.0, 0, H_PERSON, CLOTHS[3], key="메텔라1"))
    ppl.extend(m_person(6.0, 19.5, 0, H_PERSON, CLOTHS[1], key="메텔라2"))
    pts = mesh_pts(m, trees, ppl) + [(-19, -19, 0), (21, -19, 0), (21, 21, 0), (-19, 21, 0)]
    ox, oy, sc, zs, bb = fit_frame(pts, box, zs_max=1.25)
    iso = ZIso(P, ox, oy, sc, zs)
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
    record("L5", L5["name"], "Core(표준 랜드마크)", box, bb, "높이 과장 %.2f배" % zs)


def hexring(cx, cy, r, a0=30.0):
    return [(cx + r * math.cos(math.radians(a0 + 60 * k)), cy + r * math.sin(math.radians(a0 + 60 * k))) for k in range(6)]


def draw_portus():
    L6 = LM["L6"]
    hx, hy = PG["hexagon_plan_center"]
    HR = PG["hexagon_plan_R"]
    bx, by = PG["claudian_basin_plan_center"]
    BR = PG["claudian_basin_plan_R"]
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
    iso.poly3([(x, y, 0.3) for x, y in hexring(hx, hy, 16.6)], fill=(206, 194, 168), ol=(150, 132, 104), lw=0.18)
    water = [(x, y, 0.32) for x, y in hexring(hx, hy, 15.2)]
    wp = [iso.p(*p) for p in water]
    P.poly(wp, fill=HARBOR_C, outline=(96, 136, 166), lw=0.2)
    facet_fill(P, wp, HARBOR_C, cell=3.2, amp=0.05, key="육각물", jit=0.12)
    wh = Mesh(None)
    for k in range(6):
        a0_, a1_ = math.radians(30 + 60 * k), math.radians(30 + 60 * (k + 1))
        pieces = [(0.06, 0.46), (0.54, 0.94)]
        if k == 0:
            pieces = [(0.06, 0.46), (0.54, 0.80)]
        elif k == 1:
            pieces = [(0.20, 0.46), (0.54, 0.94)]
        elif k == 3:
            pieces = [(0.06, 0.46), (0.54, 0.80)]
        elif k == 4:
            pieces = [(0.20, 0.46), (0.54, 0.94)]
        for (f0, f1) in pieces:
            q = []
            for (r, f) in ((17.2, f0), (17.2, f1), (22.0, f1), (22.0, f0)):
                pa = (hx + r * math.cos(a0_), hy + r * math.sin(a0_))
                pb = (hx + r * math.cos(a1_), hy + r * math.sin(a1_))
                q.append((pa[0] + (pb[0] - pa[0]) * f, pa[1] + (pb[1] - pa[1]) * f))
            wh.extend(m_prism(q, 0.3, 4.2, WALL_W))
            wh.extend(m_frustum(q, 4.2, 6.0, 0.5, ROOF))
    # 2 수로: 테베레 오른쪽 둑 ↔ 육각 내항 ↔ 해안 ↔ 외항(짧은 운하)
    yb_r = RIV_Y + RIV_HW1
    for (ya, yb_) in ((yb_r - 0.4, hy - 16.6), (hy + 16.6, COAST_B + 2.6)):
        q = [iso.p(hx - 1.5, ya, 0.3), iso.p(hx + 1.5, ya, 0.3), iso.p(hx + 1.5, yb_, 0.3), iso.p(hx - 1.5, yb_, 0.3)]
        P.poly(q, fill=HARBOR_C, outline=(96, 136, 166), lw=0.15)
    wall.draw(iso, lw=0.08)
    wh.draw(iso, lw=0.08)
    # 3 클라우디우스 외항(바다): 잔잔한 수면 + 휘어 감싼 방파제 두 팔 + 방파제 위 창고·열주 + 등대
    cx_, cy_ = iso.p(bx, by, 0)
    P.ell(cx_, cy_, 1.2247 * (BR - 2.4), 0.7071 * (BR - 2.4), fill=HARBOR_C)
    moles = Mesh(None)

    def mole_arc(t0, t1, step):
        t = t0
        while (t < t1) if step > 0 else (t > t1):
            ta, tb = math.radians(t), math.radians(t + step)
            q = [(bx + (BR - 2.6) * math.cos(ta), by + (BR - 2.6) * math.sin(ta)), (bx + BR * math.cos(ta), by + BR * math.sin(ta)),
                 (bx + BR * math.cos(tb), by + BR * math.sin(tb)), (bx + (BR - 2.6) * math.cos(tb), by + (BR - 2.6) * math.sin(tb))]
            moles.extend(m_prism(q, -0.4, 1.0, (206, 196, 174)))
            t += step
    mole_arc(263.0, 103.0, -6.15)
    mole_arc(277.0, 437.0, 6.15)
    for th in (150.0, 165.0, 180.0, 195.0, 210.0):                  # 바다 쪽 방파제 위 창고
        t = math.radians(th)
        Xc, Yc = bx + (BR - 1.3) * math.cos(t), by + (BR - 1.3) * math.sin(t)
        moles.extend(m_box(Xc - 1.4, Yc - 1.4, 1.0, Xc + 1.4, Yc + 1.4, 2.9, (230, 210, 180)))
        moles.extend(m_frustum([(Xc - 1.5, Yc - 1.5), (Xc + 1.5, Yc - 1.5), (Xc + 1.5, Yc + 1.5), (Xc - 1.5, Yc + 1.5)], 2.9, 4.1, 0.4, ROOF))
    for th in range(12, 62, 7):                                      # 열주
        t = math.radians(th)
        moles.extend(m_cyl(bx + (BR - 1.3) * math.cos(t), by + (BR - 1.3) * math.sin(t), 0.35, 1.0, 3.6, (240, 232, 214), n=6))
    tL = math.radians(86.8)
    LX, LY = bx + (BR + 2.5) * math.cos(tL), by + (BR + 2.5) * math.sin(tL)
    tower = Mesh(None)
    tower.extend(m_mound(LX, LY, -0.4, 3.4, 1.4, (150, 140, 124), key="등대섬"))
    for (r, z0, z1) in ((2.8, 1.0, 9.0), (2.25, 9.0, 15.4), (1.75, 15.4, 20.6)):
        tower.extend(m_box(LX - r, LY - r, z0, LX + r, LY + r, z1, (236, 226, 204), top=(246, 238, 220)))
    tower.extend(m_cyl(LX, LY, 1.1, 20.6, 24.0, (236, 226, 204), n=8))
    tower.extend(m_cone(LX, LY, 1.25, 24.0, 1.4, (196, 92, 64), n=8))
    moles.draw(iso, lw=0.08)
    tower.draw(iso, lw=0.08)
    for k_, zc in enumerate((5.0, 12.0, 18.0)):
        cx2, cy2 = iso.p(LX + 2.85 - 0.55 * k_, LY + 0.0, zc)
        P.rect(cx2 - 0.45, cy2 - 0.9, cx2 + 0.45, cy2 + 0.9, fill=(110, 90, 70))
    lx, ly = iso.p(LX, LY, 22.4)
    soft_ell(P, lx, ly, 2.2, 1.8, (255, 214, 110), alpha=120, blur=0.5)
    P.dot(lx, ly, 0.6, (250, 196, 70))
    for (X, Y, sc_) in ((hx - 5.0, hy + 3.0, 0.8), (hx + 4.0, hy - 4.0, 0.8), (bx - 6.0, by + 4.0, 1.0), (bx + 7.0, by - 2.0, 1.0)):
        bx_, by_ = iso.p(X, Y, 0.3)
        P.poly([(bx_ - 3.2 * sc_, by_ - 0.6 * sc_), (bx_ + 3.2 * sc_, by_ + 1.2 * sc_), (bx_ + 2.2 * sc_, by_ + 2.2 * sc_), (bx_ - 2.6 * sc_, by_ + 0.9 * sc_)], fill=(150, 104, 66))
        P.poly([(bx_ + 0.2 * sc_, by_ - 0.2 * sc_), (bx_ + 0.2 * sc_, by_ - 5.0 * sc_), (bx_ + 2.6 * sc_, by_ - 1.0 * sc_)], fill=(244, 236, 216), outline=(150, 130, 100), lw=0.1)
    pts = [iso.p(x, y, 6.0) for x, y in pave] + [iso.p(x, y, 0) for x, y in pave] + [iso.p(LX, LY, 25.4), iso.p(LX, LY + 3.4, 0)]
    for t in range(0, 360, 10):
        pts.append(iso.p(bx + BR * math.cos(math.radians(t)), by + BR * math.sin(math.radians(t)), 0))
    bb = bbox_of(pts)
    GEO["portus_basin_c"] = (cx_, cy_)
    GEO["portus_light"] = iso.p(LX, LY, 0)
    record("L6", L6["name"], "Core(표준 랜드마크)", L6["projected_box"], bb)


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
    th = 139.5
    while th < 314.0:
        h = min(hwall(th - 2.3), hwall(th + 2.3))
        for (z0, z1) in rows_for(h):
            if z1 + 3.0 < h:
                arch_on(RING_I - 0.02, th, 2.0, z0, z1, ARCH_D)
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
    for i in range(8):                                               # 관람석(카베아) 동심 단
        r = RING_I - 0.5 - i * 2.9
        z = 11.0 - i * 1.25
        ex, ey = iso.p(0, 0, z)
        col = (228, 210, 172) if i % 2 == 0 else (206, 186, 148)
        P.ell(ex, ey, 1.2247 * r, 0.7071 * r, fill=col, outline=(160, 136, 100), lw=0.15)
    for t in range(0, 360, 20):
        P.line([rp(RING_I - 1.0, t, 10.6), rp(RING_I - 21.0, t, 2.4)], (166, 142, 106), 0.14, joint=False)
    rf = 34.0                                                        # 아레나 바닥: 왼쪽 반 하이포게움, 오른쪽 반 복원 나무 바닥
    fx, fy = iso.p(0, 0, 1.2)
    P.ell(fx, fy, 1.2247 * rf, 0.7071 * rf, fill=(116, 90, 62), outline=(78, 58, 38), lw=0.35)
    P.pie(fx, fy, 1.2247 * rf - 0.4, 0.7071 * rf - 0.4, 270, 90, fill=(186, 146, 98))
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
    hy_ = [(-24, -12, 4, -9.8), (-24, -4, 4, -1.8), (-24, 4, 4, 6.2), (-24, 12, 4, 14.2),
           (-20, -12, -17.8, 15), (-12, -12, -9.8, 15), (-4, -12, -1.8, 15)]
    for (X0, Y0, X1, Y1) in hy_:
        ccx, ccy = (X0 + X1) / 2.0, (Y0 + Y1) / 2.0
        if ccx * ccx + ccy * ccy > 27.0 ** 2 or (ccx - ccy) > 0:
            continue
        isf.box(X0, Y0, 0, X1, Y1, 2.3, ((206, 184, 148), (176, 152, 118), (140, 116, 86)), ol=(90, 70, 46), lw=0.12)
    P.line([(fx, fy - 0.7071 * rf + 0.4), (fx, fy + 0.7071 * rf - 0.4)], (78, 58, 38), 0.3, joint=False)
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
    for i, th in enumerate((4, 27, 46, 64, 80, 100, 112, 342, 352)):
        t = math.radians(th)
        r_ = 73 + (i % 3) * 2.5
        front.extend(m_person(r_ * math.cos(t), r_ * math.sin(t), 0, H_PERSON, CLOTHS[i % 6], key="아레나사람%d" % i))
    front.draw(iso, lw=0.06)
    pts = list(octs) + [(o[0], o[1] + Tz) for o in (octs[7], octs[0], octs[1], octs[2])] + [rp(RING_O, t, hwall(t)) for t in range(0, 360, 2)]
    bb = bbox_of(pts)
    record("hero", HERO["name"], "Core(히어로)", HERO["projected_box"], bb)

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
    REPORT["objects"]["화산재 운반선"] = {"사양 상자": d["box"], "그린 외곽": [round(v, 1) for v in bb]}


# ───────────────────────── 7 Detail: 확대 창 Z1 · 콜아웃 C1·C2·C4 · 지시선 ─────────────────────────
def mark(x, y, letter, col=None, r=2.4):
    col = col or T_COL["Detail"]
    P.ell(x, y, r, r, fill=col, outline=(255, 255, 255), lw=0.3)
    P.text_c(x, y + r * 0.45, letter, fnt("b", r * 1.35), (255, 255, 255))


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
    rrect(P, cx - 15.5, cy + r - 9.2, cx + 15.5, cy + r - 4.8, 1.2, fill=(252, 247, 236, 225))
    P.text_c(cx, cy + r - 6.0, "로마 콘크리트 단면 모식", fnt("b", 2.2), T_TXT["Detail"])
    P.ell(cx, cy, r, r, outline=T_COL["Detail"], lw=1.5)
    P.ell(cx, cy, r - 1.0, r - 1.0, outline=(255, 248, 236), lw=0.35)
    mark(cx + r * 0.72, cy - r * 0.69, z["mark"], r=3.0)
    INFO_POLYS.append(("Z1 확대 창", [(cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy + r)]))
    # 글 칸(창 왼쪽): 콜로세움 기초 이야기 + 주의
    tx, ty = 213.0, 430.5
    rrect(P, tx - 1.2, ty - 4.2, tx + 30.5, ty + 21.6, 1.2, fill=(252, 247, 236, 200))
    P.text(tx, ty, "콜로세움 기초 단면", fnt("b", 2.35), T_TXT["Detail"])
    lines = ["겉은 석회화 돌,", "속과 기초 고리는 콘크리트", "확대(모식): 골재 +", "석회·화산재 반죽 +", "흰 석회 알갱이"]
    for i, t in enumerate(lines):
        P.text(tx, ty + 3.6 + i * 3.1, t, fnt("m", 2.15), INK_L)
    P.text(tx, ty + 3.6 + 5 * 3.1 + 0.2, "※ 콜로세움 시료 분석은 미확인", fnt("m", 1.75), (130, 90, 60))
    INFO_POLYS.append(("Z1 글 칸", [(tx - 1.2, ty - 4.2), (tx + 30.5, ty - 4.2), (tx + 30.5, ty + 21.6), (tx - 1.2, ty + 21.6)]))
    record("Z1", z["name"], "Detail", z["projected_box"], (cx - r, cy - r, cx + r, cy + r))


def callout_plate(box, letter, title):
    x0, y0, x1, y1 = box
    rrect(P, x0, y0, x1, y1, 1.6, fill=(253, 248, 236, 238), outline=T_COL["Detail"] + (255,), lw=0.5)
    mark(x0 + 3.4, y0 + 3.6, letter, r=2.3)
    P.text(x0 + 6.8, y0 + 4.6, title, fnt("b", 2.45), T_TXT["Detail"])
    INFO_POLYS.append(("콜아웃 " + letter, box_poly(box)))


def callout_size(box, cid):
    x0, y0, x1, y1 = box
    P.text_r(x1 - 1.2, y1 - 1.1, "%s · Detail · %.0f×%.0f · %smm²" % (cid, x1 - x0, y1 - y0, format(int(round((x1 - x0) * (y1 - y0))), ",")),
             fnt("b", 1.65), T_COL["Detail"])


def draw_c1():
    c = DMAP["C1"]
    box = c["box"]
    x0, y0, x1, y1 = box
    callout_plate(box, c["mark"], "판테온 돔의 가벼운 골재")
    # 돔 단면 쐐기: 아래 무거운 돌 → 위 가벼운 돌
    ox, oy, R1, R2 = x0 + 3.0, y0 + 32.0, 20.0, 15.0
    bands = [(0, 30, (226, 222, 210), "석회화"), (30, 55, (176, 128, 96), ""), (55, 90, (214, 196, 128), "")]
    for (a0, a1, col, _n) in bands:
        q = [(ox + R1 * math.cos(math.radians(a)), oy - R1 * math.sin(math.radians(a))) for a in range(a0, a1 + 1, 5)]
        q += [(ox + R2 * math.cos(math.radians(a)), oy - R2 * math.sin(math.radians(a))) for a in range(a1, a0 - 1, -5)]
        P.poly(q, fill=col, outline=(120, 100, 80), lw=0.15)
    rng = local_rng("C1골재")
    for i in range(26):
        a = rng.random() * 90
        rr = R2 + 0.6 + rng.random() * (R1 - R2 - 1.2)
        x, y = ox + rr * math.cos(math.radians(a)), oy - rr * math.sin(math.radians(a))
        P.ell(x, y, 0.42, 0.36, fill=(150, 146, 140) if a < 30 else ((150, 90, 66) if a < 55 else (186, 176, 150)))
    P.line([(ox + R1 + 1.5, oy - 1.0), (ox + R1 + 1.5, oy - R1 + 2.0)], INK_L, 0.3, joint=False)
    P.poly([(ox + R1 + 0.6, oy - R1 + 3.4), (ox + R1 + 1.5, oy - R1 + 1.4), (ox + R1 + 2.4, oy - R1 + 3.4)], fill=INK_L)
    P.text(ox + 0.5, oy + 3.2, "무거운 돌(석회화)", fnt("m", 1.85), INK_L)
    P.text(ox + 1.0, oy - R1 - 0.8, "가벼운 돌", fnt("b", 1.85), INK_L)
    lines = ["돔 단면 쐐기:", "아래 무거운 돌(석회화)", "→ 위 가벼운 돌", "(스코리아·노란 응회암)", "위로 갈수록 가벼운", "골재로 무게를 줄였다"]
    for i, t in enumerate(lines):
        P.text(x0 + 27.0, y0 + 10.2 + i * 3.6, t, fnt("b" if i in (0, 4, 5) else "m", 2.05), INK_L)
    P.text(x0 + 27.0, y0 + 10.2 + 6 * 3.6 + 0.4, "※ 골재 산지는 미확인", fnt("m", 1.65), (130, 90, 60))
    callout_size(box, "C1")


def draw_c2():
    c = DMAP["C2"]
    box = c["box"]
    x0, y0, x1, y1 = box
    callout_plate(box, c["mark"], "포르투스 방파제와 바닷물")
    # 방파제 단면 + 바닷물 + 새로 자란 광물 결정
    bx0, by0 = x0 + 3.0, y0 + 7.5
    P.rect(bx0, by0 + 3.0, x1 - 3.0, by0 + 11.0, fill=(150, 186, 210))
    for k in range(5):
        xx = bx0 + 2 + k * 9.6
        P.arc(xx, by0 + 3.2, 2.4, 1.0, 180, 360, (236, 246, 252), 0.3)
    P.poly([(bx0 + 10, by0 + 11.0), (bx0 + 13, by0 + 1.0), (x1 - 16, by0 + 1.0), (x1 - 13, by0 + 11.0)], fill=CONC2, outline=(96, 90, 80), lw=0.2)
    rng = local_rng("C2결정")
    for i in range(16):
        x = bx0 + 14 + rng.random() * (x1 - bx0 - 31)
        y = by0 + 2.4 + rng.random() * 7.4
        if i % 2:
            P.poly([(x - 0.9, y), (x - 0.45, y - 0.7), (x + 0.45, y - 0.7), (x + 0.9, y), (x + 0.45, y + 0.7), (x - 0.45, y + 0.7)], fill=(250, 250, 246), outline=(170, 166, 156), lw=0.08)
        else:
            P.ell(x, y, 0.5, 0.5, fill=(236, 228, 210), outline=(170, 160, 140), lw=0.08)
    P.text(x1 - 12.4, by0 + 6.4, "바닷물", fnt("b", 1.8), (40, 80, 110))
    lines = ["바다 콘크리트는 바닷물과 반응해 새 광물", "(알루미늄 토버모라이트·필립사이트)이",
             "자라 결속이 강해졌다", "(2017년 연구, 코사 항 시료)", "포르투스 방파제(약 115년) 반죽은", "로마 근교 화산재 + 나폴리만 화산재"]
    for i, t in enumerate(lines):
        P.text(x0 + 2.6, y0 + 22.6 + i * 3.25, t, fnt("b" if i == 2 else "m", 1.95), INK_L)
    callout_size(box, "C2")


def draw_c4():
    c = DMAP["C4"]
    box = c["box"]
    x0, y0, x1, y1 = box
    callout_plate(box, c["mark"], "메텔라 무덤 드럼의 재결속")
    cx, cy, R = x0 + 12.0, y0 + 20.5, 9.0
    P.ell(cx, cy, R, R, fill=BRICK, outline=(110, 60, 44), lw=0.2)
    P.ell(cx, cy, R - 1.1, R - 1.1, fill=CONC2)
    for k in range(10):
        a = math.radians(k * 36 + 8)
        x, y = cx + (R - 2.6) * math.cos(a), cy + (R - 2.6) * math.sin(a)
        P.rect(x - 1.0, y - 0.7, x + 1.0, y + 0.7, fill=TUFF, outline=(120, 96, 70), lw=0.08)
    P.ell(cx, cy, R - 4.4, R - 4.4, fill=(196, 186, 168))
    for k in range(5):
        x = cx - 3.0 + k * 1.5
        P.poly([(x, cy - R - 3.4), (x - 0.5, cy - R - 2.4), (x + 0.5, cy - R - 2.4)], fill=(80, 150, 206))
        P.ell(x, cy - R - 2.2, 0.5, 0.5, fill=(80, 150, 206))
    P.text_c(cx, cy + R + 3.2, "벽돌 겉면 · 콘크리트 속 · 응회암 보강", fnt("m", 1.6), INK_L)
    lines = ["젖을 때마다", "화산재 속 류사이트가", "녹아 접합부를", "다시 짰다", "(2021년 연구)"]
    for i, t in enumerate(lines):
        P.text(x0 + 24.0, y0 + 10.8 + i * 3.5, t, fnt("b" if i in (1, 3) else "m", 2.05), INK_L)
    P.text(x0 + 24.0, y0 + 10.8 + 5 * 3.5 + 0.4, "※ 석회 알갱이와 다른 원리", fnt("m", 1.6), (130, 90, 60))
    callout_size(box, "C4")


def draw_leaders():
    col = T_COL["Detail"]
    # 콜로세움 기초 절개 → Z1 → D (같은 'A' 표지)
    for ld in DET["leaders"]:
        nm = ld["name"]
        pts = [tuple(p) for p in ld["pts"]]
        if nm.startswith("판테온"):
            # 판테온 이름 라벨 지시선(규선 연장 ↙, 원통 벽 위쪽)과 엇갈리지 않게 원통 벽 오른쪽(사양 시작점 (102, 233) 부근)에서 ↘
            dr = GEO.get("pantheon_drum_r")
            s0 = (dr[0] - 0.3, min(dr[2] - 4.0, dr[1] + 11.6)) if dr else pts[0]
            ex = pts[-1][0]
            t = (ex - s0[0]) / C30
            pts = [s0, (ex, s0[1] + 0.5 * t)] if t > 0 else pts
            mark(s0[0] - 3.4, s0[1] + 1.2, "B", r=1.9)
        elif nm.startswith("클라우디우스"):
            bcx, bcy = GEO.get("portus_basin_c", (30.66, 419.3))
            a_, b_ = 1.2247 * PG["claudian_basin_plan_R"], 0.7071 * PG["claudian_basin_plan_R"]
            x = pts[0][0]
            dxr = (x - bcx) / a_
            y_m = bcy + b_ * math.sqrt(max(0.0, 1 - dxr * dxr)) + 1.0 if abs(dxr) < 1 else pts[0][1]
            pts = [(x, y_m), pts[-1]]
            mark(x + 2.8, y_m + 2.4, "C", r=1.9)
        elif nm.startswith("메텔라"):
            foot = GEO.get("metella_foot")
            if foot:
                y_m = poly_y_at(foot, pts[0][0], "bottom")
                if y_m is not None:
                    pts[0] = (pts[0][0], y_m + 0.4)
            mark(pts[0][0] - 2.9, pts[0][1] + 3.6, "D", r=1.9)
        elif nm.startswith("콜로세움"):
            mark(pts[0][0] - 3.4, pts[0][1] - 2.6, "A", r=1.9)
        P.line(pts, col, 0.42, joint=False)
        P.dot(pts[0][0], pts[0][1], 0.55, col)
        P.dot(pts[-1][0], pts[-1][1], 0.55, col)
    # Basic: 제작 과정 ⑥ → 콜로세움 공사장(지도→패널, 패널 쪽 끝만 작은 화살촉)
    lk = BAS["process_representation"]["link"]
    (x0, y0), (x1, y1) = [tuple(p) for p in lk["pts"]]
    wb = GEO.get("worksite_bb")
    if wb:
        y0 = min(y0, wb[3] + 0.4)
    cb = T_COL["Basic"]
    P.line([(x0, y0), (x1, y1 - 1.6)], cb, 0.42, joint=False)
    P.dot(x0, y0, 0.55, cb)
    P.poly([(x1 - 1.2, y1 - 2.2), (x1 + 1.2, y1 - 2.2), (x1, y1 + 0.1)], fill=cb)


# ───────────────────────── 8 지도 라벨(등각 벽면·깃대·말풍선) ─────────────────────────
def stack_flat(en_lines, ko, sup, body, col, s=1.0):
    f_en, f_ko, f_sup, f_bd = fnt("en", EN_EM * s), fnt("b", KO_EM * s), fnt("m", SUP_EM * s), fnt("m", BODY_EM * s)
    widths = [tw(t, f_en) for t in en_lines]
    widths.append(tw(ko, f_ko) + ((tw(sup, f_sup) + 1.2 * s) if sup else 0.0))
    widths += [tw(t, f_bd) for t in body]
    W = max(widths)
    v = 0.3 * s
    base_en = []
    for _ in en_lines:
        v += EN_CAP * s
        base_en.append(v)
        v += 0.8 * s
    v += 0.5 * s
    base_ko = v + 3.3 * s
    v_rule = base_ko + 1.5 * s
    base_body = [v_rule + 4.3 * s + BODY_PITCH * s * i for i in range(len(body))]
    H = (base_body[-1] + 1.3 * s) if body else (v_rule - 0.2 * s)
    f = Flat(W + 2.0, H + 1.5, col)
    for t, vb in zip(en_lines, base_en):
        f.text(0, vb, t, f_en, col)
    f.text(0, base_ko, ko, f_ko, col)
    if sup:
        f.text(tw(ko, f_ko) + 1.2 * s, base_ko - 1.55 * s, sup, f_sup, col)
    if body:
        f.line(0, v_rule, W, v_rule, col, 0.25)
        for t, vb in zip(body, base_body):
            f.text(0, vb, t, f_bd, col)
    return f, W, H, v_rule


def label_extent(M, W, H):
    return bbox_of([map_pt(M, 0, 0, u, v) for u, v in ((0, 0), (W, 0), (W, H), (0, H))])


def road_edge_y(rid, x, side=+1):
    """↗ 길(평면 X 상수)의 화면 가장자리 y: side +1 = 아래(앞) 가장자리, −1 = 위(뒤) 가장자리"""
    r = [q for q in CM["roads"] if q["id"] == rid][0]
    Xc = r["plan_pts"][0][0]
    hw = r["w_screen_perp_mm"] / (2.0 * C30)
    return -T30 * x + Xc + side * hw


# 지도 라벨 설정(슬롯 = 사양 labels.slots). anchor가 있는 라벨은 읽기 쉬운 배율을 위해 슬롯 옆 빈 자리까지 쓴다(보고서에 넘침 기록).
LABEL_CFGS = {
    "콜로세움": dict(en=["COLOSSEUM"], ko="콜로세움", sup="Amphitheatrum Flavium", ha="l", va="b", smin=0.8),
    # 판테온: 시내 구역 한 방향(↗, 트라야누스 시장·카라칼라와 같음)과 사양 지시선 '규선 연장 ↙'에 맞춰 ↗ 벽면. 시내 길 1 아래 변과 나란히 둔다.
    "판테온": dict(en=["PANTHEON"], ko="판테온", wall="↗", s=1.0, anchor=("road", "R2", 118.4, 1.5)),
    "카라칼라 욕장": dict(en=["BATHS OF CARACALLA"], ko="카라칼라 욕장", sup="Thermae Antoninianae", s=0.86, anchor=("r", 222.0, 98.0)),
    "트라야누스 시장": dict(en=["TRAJAN'S MARKETS"], ko="트라야누스 시장", sup="Mercati di Traiano", s=0.85, anchor=("l", 118.4, 95.0)),
    "수도교": dict(en=["AQUA CLAUDIA"], ko="수도교", sup="Aqua Claudia · Antoniniana", s=0.85, anchor=("r", 376.5, 189.6)),
    "카이킬리아 메텔라 무덤": dict(en=["CAECILIA METELLA"], ko="카이킬리아 메텔라 무덤", ha="r", va="t", smin=0.6),
    "포르투스 항": dict(en=["PORTUS"], ko="포르투스 항", sup="Portus", ha="l", va="t", smin=0.6, plate=(250, 244, 228, 215)),
    "베수비오": dict(en=["VESUVIUS"], ko="베수비오", body=["79년 분화"], ha="r", va="t", smin=0.5, slack_h=3.0),
    "바지선": dict(en=["BARGE"], ko="바지선", body=[], ha="c", va="t", smin=0.55, slack_h=2.0),
    "화산재 운반선": dict(en=["ASH SHIP"], ko="화산재 운반선", body=[], ha="l", va="t", smin=0.5, slack_h=2.0, plate=(250, 244, 228, 215)),
}


def place_label(key, cfg, draw=True):
    slot = SLOT[key]
    box = slot["box"]
    wall = cfg.get("wall", slot["wall"])
    M = M_WALL_UP if wall.startswith("↗") else M_WALL_DN
    body = cfg.get("body", slot["body"])
    en = cfg["en"] if isinstance(cfg["en"], list) else [cfg["en"]]
    sup = cfg.get("sup")
    f, W, H, vr = stack_flat(en, cfg["ko"], sup, body, INK_L, 1.0)
    ex = label_extent(M, W, H)
    if "s" in cfg:
        s = cfg["s"]
    else:
        bw = box[2] - box[0] - 0.8 + cfg.get("slack_w", 0.0)
        bh = box[3] - box[1] - 0.8 + cfg.get("slack_h", 0.0)
        s = min(1.0, bw / (ex[2] - ex[0]), bh / (ex[3] - ex[1])) * 0.99
        s = max(cfg.get("smin", 0.55), min(cfg.get("smax", 1.0), s))
    if s < 0.999:
        f, W, H, vr = stack_flat(en, cfg["ko"], sup, body, INK_L, s)
        ex = label_extent(M, W, H)
    an = cfg.get("anchor")
    if an and an[0] == "road":
        ax = an[2] - ex[0]
        ay = road_edge_y(an[1], an[2], +1) + an[3]
    elif an:
        ax = (an[1] - ex[0]) if an[0] == "l" else (an[1] - ex[2])
        ay = an[2] - ex[1]
    else:
        ha, va = cfg.get("ha", "c"), cfg.get("va", "c")
        ax = {"l": box[0] + 0.4 - ex[0], "r": box[2] - 0.4 - ex[2], "c": (box[0] + box[2]) / 2.0 - (ex[0] + ex[2]) / 2.0}[ha]
        ay = {"t": box[1] + 0.4 - ex[1], "b": box[3] - 0.4 - ex[3], "c": (box[1] + box[3]) / 2.0 - (ex[1] + ex[3]) / 2.0}[va]
    ax += cfg.get("dx", 0.0)
    ay += cfg.get("dy", 0.0)
    poly = [map_pt(M, ax, ay, u, v) for u, v in ((0, 0), (W, 0), (W, H), (0, H))]
    info = dict(M=M, ax=ax, ay=ay, W=W, H=H, vr=vr, s=s, poly=poly)
    if not draw:
        return info
    pc = [map_pt(M, ax, ay, u, v) for u, v in ((-0.9, -0.6), (W + 0.9, -0.6), (W + 0.9, H + 0.6), (-0.9, H + 0.6))]
    P.poly(pc, fill=cfg.get("plate", PLATE))
    affine_paste(P, f, M, ax, ay)
    LABEL_POLYS.append((key, poly))
    e = bbox_of(poly)
    over = max(0.0, box[0] - e[0], e[2] - box[2], box[1] - e[1], e[3] - box[3])
    REPORT["labels"][key] = {"방향": "↗" if M is M_WALL_UP else "↘", "슬롯": box, "그린 외곽": [round(v, 1) for v in e], "배율": round(s, 2),
                             "슬롯 넘침mm": round(over, 1)}
    if an:
        REPORT["labels"][key]["배치"] = "슬롯 옆 빈 자리까지 사용(읽기 배율 확보)"
    if wall != slot["wall"]:
        REPORT["labels"][key]["방향 메모"] = "사양 %s → %s(시내 구역 한 방향·규선 연장 ↙)" % (slot["wall"], wall)
    return info


def plan_labels():
    """라벨 자리를 먼저 잡아 빈 자리 마스크에 넣는다(지붕·나무·밭이 라벨을 덮지 않게)"""
    for key, cfg in LABEL_CFGS.items():
        info = place_label(key, cfg, draw=False)
        ex_poly(info["poly"], 1.4)
        if key == "판테온":
            pe = map_pt(info["M"], info["ax"], info["ay"], 0.0, info["vr"])
            ex_line([pe, (pe[0] - 24.0, pe[1] + 24.0 * T30)], 2.4)
        if key == "수도교":
            pe = map_pt(info["M"], info["ax"], info["ay"], info["W"] + 1.6, info["vr"])
            ex_line([pe, (pe[0], pe[1] - 18.0)], 2.4)
        if key == "콜로세움":
            pe = map_pt(info["M"], info["ax"], info["ay"], info["W"] + 1.6, info["vr"])
            ex_line([pe, (pe[0], pe[1] + 32.0)], 2.4)


def lead_rule(info, side, target, ink=INK_L, ext_min=1.4):
    """규선을 side 쪽으로 늘여 대상 x에 닿고, 모자라면 수직으로 대상 y까지(꺾임 ≤ 1)"""
    M, ax, ay, W, vr = info["M"], info["ax"], info["ay"], info["W"], info["vr"]
    a = M[0][0]
    u_end = W if side == "R" else 0.0
    pe = map_pt(M, ax, ay, u_end, vr)
    tx, ty = target
    du = (tx - pe[0]) / a
    du = max(du, ext_min) if side == "R" else min(du, -ext_min)
    q = map_pt(M, ax, ay, u_end + du, vr)
    pts = [pe, q]
    if ty is not None and abs(q[1] - ty) > 0.4:
        pts.append((q[0], ty))
    P.line(pts, ink, LEAD_LW, joint=False)
    P.dot(pts[-1][0], pts[-1][1], DOT_R, ink)
    return pts


def lead_pole(info, ty, u=-1.4, ink=INK_L):
    M, ax, ay, H = info["M"], info["ax"], info["ay"], info["H"]
    top = map_pt(M, ax, ay, u, 0.0)
    bot = map_pt(M, ax, ay, u, H)
    if ty >= bot[1]:
        P.line([top, (top[0], ty)], ink, LEAD_LW, joint=False)
    else:
        P.line([bot, (bot[0], ty)], ink, LEAD_LW, joint=False)
    P.dot(top[0], ty, DOT_R, ink)
    return (top[0], ty)


def place_tag(key, text, fill=(198, 112, 58)):
    slot = SLOT[key]
    box = slot["box"]
    M = M_WALL_UP if slot["wall"].startswith("↗") else M_WALL_DN
    em = 2.6
    for _ in range(4):
        f_ = fnt("b", em)
        W = tw(text, f_) + 2.4
        H = em * 1.5
        ex = label_extent(M, W, H)
        if ex[2] - ex[0] <= box[2] - box[0] + 2.0 and ex[3] - ex[1] <= box[3] - box[1] + 5.0:
            break
        em *= 0.9
    ax = (box[0] + box[2]) / 2.0 - (ex[0] + ex[2]) / 2.0
    ay = (box[1] + box[3]) / 2.0 - (ex[1] + ex[3]) / 2.0
    pc = [map_pt(M, ax, ay, u, v) for u, v in ((0, 0), (W, 0), (W, H), (0, H))]
    tail = [map_pt(M, ax, ay, 2.2, H), map_pt(M, ax, ay, 4.6, H), map_pt(M, ax, ay, 2.6, H + 2.2)]
    P.poly(tail, fill=fill)
    P.poly(pc, fill=fill, outline=shade(fill, 0.7), lw=0.25)
    bl = map_pt(M, ax, ay, 1.2, H * 0.74)
    iso_text(P, text, f_, (255, 250, 240), M, bl[0], bl[1])
    LABEL_POLYS.append((key, pc))
    e = bbox_of(pc)
    over = max(0.0, box[0] - e[0], e[2] - box[2], box[1] - e[1], e[3] - box[3])
    REPORT["labels"][key] = {"종류": "말풍선 태그", "슬롯": box, "그린 외곽": [round(v, 1) for v in e], "글자mm": round(em, 2), "슬롯 넘침mm": round(over, 1)}


def draw_labels():
    C = LABEL_CFGS
    # 1 콜로세움(브래킷, ↘, 수직 ↓ 지시선 → 뒤-오른쪽 2층 고리 윗면)
    info = place_label("콜로세움", C["콜로세움"])
    pe = map_pt(info["M"], info["ax"], info["ay"], info["W"] + 1.6, info["vr"])
    ty = GEO["arena_top_y"](pe[0]) or (pe[1] + 17)
    P.line([map_pt(info["M"], info["ax"], info["ay"], info["W"], info["vr"]), pe, (pe[0], ty)], INK_L, LEAD_LW, joint=False)
    P.dot(pe[0], ty, DOT_R, INK_L)
    REPORT["labels"]["콜로세움"]["지시선"] = "수직 %.1fmm" % (ty - pe[1])
    # 2 판테온(↗, 규선 연장 ↙ → 원통 벽 오른쪽)
    info = place_label("판테온", C["판테온"])
    dr = GEO.get("pantheon_drum_r")
    pe = map_pt(info["M"], info["ax"], info["ay"], 0.0, info["vr"])
    if dr:
        xt = dr[0] - 0.7
        yq = pe[1] + T30 * (pe[0] - xt)
        ty = None if dr[1] + 0.8 <= yq <= dr[2] - 0.8 else min(max(yq, dr[1] + 0.8), dr[2] - 0.8)
        pts = lead_rule(info, "L", (xt, ty))
    else:
        pts = lead_rule(info, "L", (98.0, None))
    REPORT["labels"]["판테온"]["지시선"] = "규선 연장 ↙ %.1fmm" % math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1])
    # 3 카라칼라 욕장(↗, 규선 연장 ↗ + 수직 → 왼쪽 벽 윗면)
    info = place_label("카라칼라 욕장", C["카라칼라 욕장"])
    tgt = GEO.get("bath_label_tgt", (232, 120))
    pts = lead_rule(info, "R", (tgt[0], tgt[1]))
    REPORT["labels"]["카라칼라 욕장"]["지시선"] = "규선 연장 %.1fmm + 수직 %.1fmm" % (math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]),
                                                                       abs(pts[-1][1] - pts[1][1]) if len(pts) > 2 else 0.0)
    # 4 트라야누스 시장(↗, 규선 연장 ↙ → 시장 오른쪽 상점 동 끝면)
    info = place_label("트라야누스 시장", C["트라야누스 시장"])
    tgt = GEO.get("market_tgt", (105, 140))
    pts = lead_rule(info, "L", tgt)
    REPORT["labels"]["트라야누스 시장"]["지시선"] = "규선 연장 ↙ %.1fmm%s" % (math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]),
                                                                     (" + 수직 %.1fmm" % abs(pts[-1][1] - pts[1][1])) if len(pts) > 2 else "")
    # 5 수도교(↗, 수직 ↑ → 아치 열 지면선)
    info = place_label("수도교", C["수도교"])
    pe = map_pt(info["M"], info["ax"], info["ay"], info["W"] + 1.6, info["vr"])
    ty = GEO["aq_ground"](pe[0]) - 1.2
    P.line([map_pt(info["M"], info["ax"], info["ay"], info["W"], info["vr"]), pe, (pe[0], ty)], INK_L, LEAD_LW, joint=False)
    P.dot(pe[0], ty, DOT_R, INK_L)
    REPORT["labels"]["수도교"]["지시선"] = "수직 %.1fmm" % (pe[1] - ty)
    # 6 카이킬리아 메텔라 무덤(↘, 수직 ↑ → 드럼 기단)
    info = place_label("카이킬리아 메텔라 무덤", C["카이킬리아 메텔라 무덤"])
    pe = map_pt(info["M"], info["ax"], info["ay"], -1.6, info["vr"])
    ty = poly_y_at(GEO["metella_foot"], pe[0], "bottom") if GEO.get("metella_foot") else None
    ty = (ty + 0.3) if ty is not None else pe[1] - 4.0
    P.line([map_pt(info["M"], info["ax"], info["ay"], 0.0, info["vr"]), pe, (pe[0], ty)], INK_L, LEAD_LW, joint=False)
    P.dot(pe[0], ty, DOT_R, INK_L)
    REPORT["labels"]["카이킬리아 메텔라 무덤"]["지시선"] = "수직 %.1fmm" % (pe[1] - ty)
    # 7 포르투스 항(↘, 바다 위: 크림 판, 윗변에서 수직 ↑ → 등대 섬)
    info = place_label("포르투스 항", C["포르투스 항"])
    lx_, ly_ = GEO.get("portus_light", (11.5, 431.7))
    u_l = max(0.6, min(info["W"] - 0.6, (lx_ - info["ax"]) / C30))
    q0 = map_pt(info["M"], info["ax"], info["ay"], u_l, -0.7)
    ty = ly_ + 2.6
    P.line([q0, (q0[0], ty)], INK_L, LEAD_LW, joint=False)
    P.dot(q0[0], ty, DOT_R, INK_L)
    REPORT["labels"]["포르투스 항"]["지시선"] = "윗변에서 수직 %.1fmm(등대 섬)" % (q0[1] - ty)
    # 8 베수비오(깃대형, ↗, 깃대 ↓ → 봉우리 어깨)
    info = place_label("베수비오", C["베수비오"])
    pole_x = map_pt(info["M"], info["ax"], info["ay"], -1.2, 0.0)[0]
    vp = [q for q in GEO.get("ves_pts", []) if abs(q[0] - pole_x) < 1.6]
    ty = (min(q[1] for q in vp) + 1.2) if vp else map_pt(info["M"], info["ax"], info["ay"], -1.2, info["H"])[1] + 6.0
    lead_pole(info, ty, u=-1.2)
    # 9 바지선 · 10 화산재 운반선(깃대형, ↘)
    info = place_label("바지선", C["바지선"])
    pole_x = map_pt(info["M"], info["ax"], info["ay"], -1.4, 0.0)[0]
    b1 = REPORT["objects"].get("바지선 1", {}).get("그린 외곽")
    if b1 and b1[0] <= pole_x <= b1[2]:
        ty = T30 * pole_x + RIV_Y - 3.6
    else:
        ty = map_pt(info["M"], info["ax"], info["ay"], -1.4, info["H"])[1] + 6.0
    lead_pole(info, ty)
    info = place_label("화산재 운반선", C["화산재 운반선"])
    st = GEO.get("ship_deck")
    if st:
        lead_rule(info, "L", (st[0], st[1]))
    # 11 · 12 말풍선 태그(재료 시설 색)
    place_tag("테베레 하역장·석회 가마", "하역장·석회 가마")
    place_tag("콜로세움 공사장", "공사장 · ⑤ 다져 넣기")


# ───────────────────────── 9 틀: 타이틀·패널·푸터·눈금 ─────────────────────────
def draw_title():
    x0, y0, x1, y1 = FR["title"]["rect"]
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
    P.text_c(cx, y0 + 37.4, "CITY LANDMARK INFOGRAPHICS · ROMA", fnt("en", 5.0), red)
    P.poly([(x0 + 2, y0 + 30.5), (cx, y0 + 1.0), (x1 - 2, y0 + 30.5)], fill=(252, 242, 234), outline=red, lw=0.6)
    P.poly([(x0 + 16, y0 + 28.0), (cx, y0 + 6.2), (x1 - 16, y0 + 28.0)], outline=(226, 150, 150), lw=0.3)
    P.ell(cx, y0 + 17.0, 3.0, 3.0, outline=red, lw=0.45)
    P.text_c(cx, y0 + 25.2, "타이틀 록업 · 신전 페디먼트 정면 입면 · %.0f×%.0fmm(폭 %.1f%%)" % (x1 - x0, y1 - y0, FR["title"]["width_pct"]), fnt("m", 2.1), (150, 60, 60))
    P.rect(cx - 52, y0 + 44.0, cx + 52, y0 + 66.0, fill=(253, 247, 240), outline=red, lw=0.6)
    P.text_c(cx, y0 + 57.0, "ROMAN CONCRETE", fnt("en", 13.0), red)
    P.text_c(cx, y0 + 63.4, "로마 콘크리트 — 도시 인포그래픽 '로마 편'", fnt("b", 3.5), red)
    P.rect(cx - 60, y0 + 67.6, cx + 60, y0 + 73.4, fill=(250, 230, 228), outline=red, lw=0.4)
    P.text_c(cx, y0 + 71.9, "로마 건축물로 읽는 로마 콘크리트", fnt("b", 3.0), red)


def panel_header(x0, y0, en, ko, en_cap=7.4, ko_em=3.8, col=ACCENT):
    f_en = fnt("en", en_cap / 0.71)
    yb = y0 + 2.4 + en_cap
    P.text(x0 + 2.0, yb, en, f_en, col)
    w = tw(en, f_en)
    P.text(x0 + 2.0 + w + 2.0, y0 + 2.4 + ko_em * 0.78, ko, fnt("b", ko_em), col)
    return yb


def panel_frame(pid, tag_pos):
    pn = PANEL[pid]
    x0, y0, x1, y1 = pn["rect"]
    tier = pn["tier"]
    P.dashed_rect(x0, y0, x1, y1, T_COL[tier], 0.4, 2.4, 1.3)
    t = "%s · %s · %.0f×%.0f · %smm²" % (pid, tier, x1 - x0, y1 - y0, format(int(pn["box_area"]), ","))
    if pid == "R":
        t += " · 연한 판(포스터에서 R만)"
    if pid == "S":
        t += " · 가장 작은 위계"
    if tag_pos == "above_r":
        pill(P, x1, y0 - 3.6, t, T_TXT[tier], em=2.0, anchor="r")
    elif tag_pos == "above_l":
        pill(P, x0, y0 - 3.6, t, T_TXT[tier], em=2.0)
    INFO_POLYS.append(("패널 " + pid, box_poly(pn["rect"])))


def draw_panel_L():
    x0, y0, x1, y1 = PANEL["L"]["rect"]
    yb = panel_header(x0, y0, "ROMAN CONCRETE?", "로마 콘크리트란?")
    defs = ["생석회와 화산재가 물과 반응해 굳는 반죽에", "돌·벽돌 조각(골재)을 다져 넣은 로마 건축 재료.", "철근 없이 돔·볼트·방파제를 지었다."]
    for i, t in enumerate(defs):
        P.text(x0 + 2.2, yb + 5.8 + i * 4.1, t, fnt("m", 2.85), INK_L)
    items = [("생석회", ["석회암을 구운 것"]), ("화산재", ["시내 = 알바노 구릉", "바다 = 포추올리"]),
             ("골재", ["응회암·벽돌·", "경석 조각"]), ("물", ["육상 = 민물", "바다 공사 = 바닷물"])]
    for i, (name, sub) in enumerate(items):
        cx = x0 + 13.0 + i * 24.6
        iso = Iso(P, cx, y0 + 39.0)
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
        P.text_c(cx, y0 + 49.6, name, fnt("b", 2.8), INK_L)
        for k, t in enumerate(sub):
            P.text_c(cx, y0 + 53.4 + k * 3.0, t, fnt("m", 2.05), INK_L)
    P.line([(x0 + 2.2, y0 + 61.4), (x1 - 2.2, y0 + 61.4)], (176, 156, 120), 0.25, joint=False)
    P.text(x0 + 2.2, y0 + 66.6, "섞는 순서가 열쇠 → 아래 '제작 과정'", fnt("b", 2.7), INK_L)


def draw_location_map(x0, y0, x1, y1):
    col = T_TXT["Basic"]
    mx0, my0, k = x0 + 9.0, y0 + 13.5, 25.0
    kx = k * 0.755
    sub = Layer(x0 + 1.0, y0 + 12.0, x0 + 57.5, y0 + 59.0)

    def g(lon, lat):
        return (mx0 + (lon - 12.1) * kx, my0 + (42.15 - lat) * k)
    coast = [(11.9, 42.35), (12.26, 41.78), (12.45, 41.62), (12.63, 41.45), (13.03, 41.33), (13.25, 41.28), (13.57, 41.21),
             (13.89, 41.12), (14.03, 40.92), (14.05, 40.85), (14.12, 40.82), (14.25, 40.84), (14.45, 40.75), (14.37, 40.63), (14.33, 40.4)]
    cp = [g(*p) for p in coast]
    sea = cp + [(cp[-1][0], y0 + 70), (x0 - 5, y0 + 70), (x0 - 5, cp[0][1])]
    sub.poly(sea, fill=(196, 220, 234))
    sub.line(cp, (110, 150, 180), 0.35)
    tib = [g(12.53, 42.14), g(12.49, 42.0), g(12.47, 41.93), g(12.48, 41.88), g(12.42, 41.83), g(12.33, 41.79), g(12.26, 41.75)]
    sub.line(tib, (96, 150, 200), 0.5)
    appia = [g(12.50, 41.88), g(12.64, 41.74), g(13.25, 41.29), g(14.25, 41.08)]
    for i in range(len(appia) - 1):
        sub.dashed(appia[i], appia[i + 1], (150, 120, 84), 0.32, 1.3, 0.9)
    P.paste(sub)
    zones = [("①②", 12.492, 41.890, 1.8, (-5.0, -2.2)), ("③", 12.62, 41.80, 3.2, (0.4, 6.4)), ("④", 12.27, 41.77, 2.2, (-2.0, 7.4)), ("⑤", 14.43, 40.82, 2.8, (2.4, -3.6))]
    for (z, lon, lat, rr, off) in zones:
        x, y = g(lon, lat)
        n = 28
        for i in range(0, n, 2):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            P.line([(x + rr * math.cos(a0), y + rr * 0.8 * math.sin(a0)), (x + rr * math.cos(a1), y + rr * 0.8 * math.sin(a1))], col, 0.22, joint=False)
        P.text_c(x + off[0], y + off[1], z, fnt("b", 2.0), col)
    pins = [("로마", 12.492, 41.890, (2.2, -0.6), "l", True), ("오스티아·", 12.26, 41.77, (-1.6, 1.4), "r", False),
            ("알바노 구릉", 12.70, 41.75, (2.0, 1.2), "l", False), ("포추올리", 14.12, 40.82, (-1.8, -1.2), "r", False),
            ("베수비오·폼페이", 14.45, 40.80, (0.4, 5.0), "r", False)]
    for (name, lon, lat, off, al, big) in pins:
        x, y = g(lon, lat)
        P.ell(x, y, 1.15 if big else 0.85, 1.15 if big else 0.85, fill=INK_L if big else col, outline=(255, 255, 255), lw=0.2)
        f = fnt("b", 2.15 if big else 1.9)
        if al == "l":
            P.text(x + off[0], y + off[1], name, f, INK_L)
        else:
            P.text_r(x + off[0], y + off[1], name, f, INK_L)
    ox_, oy_ = g(12.26, 41.77)
    P.text_r(ox_ - 1.6, oy_ + 4.2, "포르투스", fnt("b", 1.9), INK_L)
    sx0 = x0 + 36.0
    P.line([(sx0, y0 + 16.0), (sx0 + 0.45 * k, y0 + 16.0)], INK_L, 0.4, joint=False)
    P.text(sx0, y0 + 19.0, "50 km", fnt("m", 1.8), INK_L)
    nx, ny = x1 - 5.0, y0 + 6.4
    P.poly([(nx, ny - 3.2), (nx + 1.6, ny + 1.6), (nx, ny + 0.6), (nx - 1.6, ny + 1.6)], fill=INK_L)
    P.text_c(nx, ny + 4.6, "N", fnt("b", 2.4), INK_L)
    lx = x0 + 59.0
    rows = [("지도에 담은 구역", True), ("①② 도심·시내 — 로마", False), ("③ 남동 교외 — 아피아 가도", False), ("④ 서남서 해안 — 하구", False),
            ("⑤ 가장 먼 곳 — 베수비오", False), ("핀", True), ("알바노 구릉 = 로마 건물 화산재", False), ("포추올리 = 바다 공사 화산재", False),
            ("  ('포졸라나'라는 말의 고향)", False), ("베수비오·폼페이 = 79년 분화,", False), ("  2025 공사 현장 연구", False)]
    for i, (t, b) in enumerate(rows):
        P.text(lx, y0 + 18.0 + i * 3.25, t, fnt("b" if b else "m", 1.85 if not b else 1.95), col if b else INK_L)
    P.text(x0 + 2.2, y1 - 5.0, "큰 지도는 구도를 위해 돌리고 줄였다. 실제 방위·거리는 이 지도:", fnt("m", 1.85), INK_L)
    P.text(x0 + 2.2, y1 - 1.9, "로마 → 포르투스 약 23 km 서남서 · 로마 → 베수비오 약 200 km 남동", fnt("b", 1.85), INK_L)


def draw_panel_R():
    x0, y0, x1, y1 = PANEL["R"]["rect"]
    rrect(P, x0, y0, x1, y1, 1.2, fill=(252, 248, 238, 232))
    panel_header(x0, y0, "WHERE", "위치도")
    draw_location_map(x0, y0, x1, y1)


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


def draw_panel_B():
    x0, y0, x1, y1 = PANEL["B"]["rect"]
    panel_header(x0, y0, "HOW IT WAS MADE", "로마 콘크리트 제작 과정")
    names = ["재료 준비", "마른 혼합", "물 붓기", "뜨거운 혼합", "다져 넣기", "굳기·석회 알갱이"]
    notes = [["생석회·화산재·골재", "강·길로 들어온 재료"], ["물 없이 먼저 섞기", "(2025 폼페이: 미리 섞은 더미)"],
             ["육상 건물은 민물", "(바닷물은 항구 구조물만)"], ["끓어오르며 열·김", "흰 석회 알갱이가 남는다"],
             ["거푸집에 층층이", "다져 넣는다(붓지 않음)"], ["굳은 단면 속 흰 알갱이", "→ 콜로세움 기초·볼트"]]
    cw, gap = 30.6, 1.6
    for i in range(6):
        cl = x0 + 2.0 + i * (cw + gap)
        cxm = cl + cw / 2.0
        iso = Iso(P, cxm, y0 + 20.0)
        scene_tile(iso)
        draw_scene(i + 1, iso)
        P.ell(cl + 2.9, y0 + 16.6, 2.6, 2.6, fill=ACCENT, outline=(255, 255, 255), lw=0.3)
        P.text_c(cl + 2.9, y0 + 17.8, str(i + 1), fnt("b", 3.4), (255, 255, 255))
        P.text_c(cxm, y0 + 41.4, names[i], fnt("b", 2.55), INK_L)
        for k_, t in enumerate(notes[i]):
            P.text_c(cxm, y0 + 44.8 + k_ * 2.9, t, fnt("m", 1.85), INK_L)
        if i < 5:
            ax_ = cl + cw + gap / 2.0
            ay_ = y0 + 28.2
            P.poly([(ax_ - 1.6, ay_ - 0.8), (ax_ + 0.2, ay_ - 0.8), (ax_ + 0.2, ay_ - 1.7), (ax_ + 1.9, ay_), (ax_ + 0.2, ay_ + 1.7), (ax_ + 0.2, ay_ + 0.8), (ax_ - 1.6, ay_ + 0.8)],
                   fill=(110, 86, 60))
    ty_ = y1 - 4.4
    P.line([(x0 + 3.0, ty_), (x0 + 150.0, ty_)], (110, 86, 60), 0.35, joint=False)
    P.poly([(x0 + 150.0, ty_ - 1.2), (x0 + 153.4, ty_), (x0 + 150.0, ty_ + 1.2)], fill=(110, 86, 60))
    P.text(x0 + 155.0, ty_ + 0.8, "시간 → 콜로세움 완공", fnt("b", 2.1), (110, 86, 60))
    P.text_r(x1 - 1.4, y1 - 0.9, "⑥ → 지도의 공사장 지시선", fnt("m", 1.75), T_TXT["Basic"])


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


def draw_panel_D():
    x0, y0, x1, y1 = PANEL["D"]["rect"]
    panel_header(x0, y0, "LIME CLASTS", "석회 알갱이·자가치유")
    mark(x1 - 3.6, y0 + 4.2, DMAP["Z1"]["mark"], r=2.4)
    caps = [("(가) 뜨거운 혼합", ["생석회 + 물 → 열,", "흰 알갱이가 남는다"]), ("(나) 균열", ["금이 가며", "알갱이를 지난다"]),
            ("(다) 빗물", ["빗물이 스며 알갱이의", "칼슘이 녹아 나온다"]), ("(라) 결정 봉합", ["탄산칼슘 결정이", "틈을 메운다"])]
    s = 13.4
    for i, (t, ls) in enumerate(caps):
        gx, gy = i % 2, i // 2
        bx = x0 + 2.4 + gx * 42.0
        by = y0 + 13.6 + gy * 16.2
        lime_sq(bx, by, s, i + 1)
        P.text(bx + s + 1.6, by + 3.6, t, fnt("b", 2.15), INK_L)
        for k_, l_ in enumerate(ls):
            P.text(bx + s + 1.6, by + 6.9 + k_ * 2.9, l_, fnt("m", 1.85), INK_L)
        if gx == 0:
            P.poly([(bx + 39.4, by + s / 2 - 1.0), (bx + 41.2, by + s / 2), (bx + 39.4, by + s / 2 + 1.0)], fill=T_COL["Detail"])
    P.text(x0 + 2.4, y1 - 4.1, "2023 MIT 연구(프리베르눔 시료)가 실마리를 찾고,", fnt("m", 1.8), INK_L)
    P.text(x0 + 2.4, y1 - 1.3, "2025 폼페이 공사 현장 연구가 확인했다", fnt("m", 1.8), INK_L)


def draw_panel_T():
    x0, y0, x1, y1 = PANEL["T"]["rect"]
    panel_header(x0, y0, "HISTORY", "연대기")
    rows = [("BCE 2세기 말 이전", "바다 콘크리트, 나폴리만에서 태어남(추정)"), ("BCE 30–10", "카이킬리아 메텔라 무덤"), ("42", "클라우디우스 외항 착공"),
            ("79", "베수비오 분화"), ("80*", "콜로세움 개장"), ("96–115", "트라야누스 시장"), ("약 100–112", "트라야누스 육각 내항"),
            ("약 125*", "판테온 재건"), ("216", "카라칼라 욕장 봉헌"), ("2023", "MIT '뜨거운 혼합' 연구"), ("2025", "폼페이 공사 현장 연구")]
    lx = x0 + 22.4
    yy0 = y0 + 14.6
    P.line([(lx, yy0 - 1.6), (lx, yy0 + 10 * 3.72 + 0.4)], (150, 128, 96), 0.3, joint=False)
    for i, (yr, t) in enumerate(rows):
        yy = yy0 + i * 3.72
        P.text_r(lx - 1.6, yy + 0.7, yr, fnt("b", 1.62 if i == 0 else 1.95), INK_L)
        P.ell(lx, yy, 0.6, 0.6, fill=INK_L if i not in (0, 9, 10) else (150, 128, 96))
        P.text(lx + 1.8, yy + 0.7, t, fnt("m", 1.95), INK_L)
    P.text(x0 + 2.0, y1 - 1.3, "* 조사 보고서 밖 일반 연표 — 인쇄 전 출처 확인", fnt("m", 1.75), (130, 90, 60))


def draw_panel_S():
    x0, y0, x1, y1 = PANEL["S"]["rect"]
    panel_header(x0, y0, "100 VS 2,000", "콘크리트 수명", en_cap=5.0, ko_em=2.8)
    ya = y0 + 12.4
    P.rect(x0 + 2.4, ya - 2.0, x0 + 5.4, ya + 2.0, fill=(178, 180, 182))
    P.ell(x0 + 5.4, ya, 0.8, 2.0, fill=(204, 206, 208), outline=(130, 132, 134), lw=0.12)
    P.text(x0 + 7.4, ya + 0.9, "현대 콘크리트 약 100년", fnt("b", 2.15), INK_L)
    yb = y0 + 19.6
    P.rect(x0 + 2.4, yb - 2.9, x0 + 62.4, yb + 2.9, fill=(190, 178, 158))
    P.ell(x0 + 62.4, yb, 1.1, 2.9, fill=(214, 204, 186), outline=(136, 124, 104), lw=0.12)
    rng = local_rng("S막대")
    for i in range(16):
        P.ell(x0 + 4 + rng.random() * 56, yb - 2.2 + rng.random() * 4.4, 0.3, 0.26, fill=(246, 244, 236))
    P.text(x0 + 4.0, yb + 0.9, "로마 콘크리트 2,000년+", fnt("b", 2.35), INK_L)
    P.text(x0 + 2.4, y1 - 0.9, "강도가 아니라 수명이다(압축 강도는 현대 콘크리트가 높다)", fnt("m", 1.72), INK_L)


def draw_footer():
    x0, y0, x1, y1 = FR["footer"]["rect"]
    P.dashed_rect(x0, y0, x1, y1, (150, 136, 112), 0.3, 2.0, 1.2)
    P.text_r(x1 - 1.6, y0 + 4.0, "푸터 자리: Street H 로고 · 크레딧 · 203X 로고 · QR", fnt("m", 2.0), (140, 126, 104))
    P.text(x0 + 2.0, y0 + 4.6, "최종 배치 다이어그램(새 위계)", fnt("b", 3.4), T_TXT["Core"])
    w = tw("최종 배치 다이어그램(새 위계)", fnt("b", 3.4))
    P.text(x0 + 4.0 + w, y0 + 4.6, "로마 콘크리트 A2 세로(420×594mm) · 도시 인포그래픽 '로마 편' · 사양 %s · 위계 변경 %s · 1mm = 3px" %
           (META["version"], META["hierarchy_change"]["date"]), fnt("m", 2.15), INK_L)
    items = [("Core 로마 건축물 지도(히어로 콜로세움 + 랜드마크·길·강·바다)", T_COL["Core"]), ("Basic 정의·제작 과정·위치도·연대기", T_COL["Basic"]),
             ("Detail 확대 창·콜아웃·석회 알갱이", T_COL["Detail"]), ("Support 100년 vs 2,000년", T_COL["Support"]),
             ("강조색 폼페이 레드(타이틀·머리글·단계 번호)", ACCENT), ("강·바다", RIV_C), ("길", ROAD_C), ("밭·포도밭", FIELD_BASE["vine"])]
    xx = x0 + 2.0
    yy = y0 + 10.4
    for name, cc in items:
        P.rect(xx, yy - 2.4, xx + 2.8, yy + 0.3, fill=cc, outline=(90, 80, 64), lw=0.15)
        P.text(xx + 3.6, yy, name, fnt("b", 2.15), INK_L)
        xx += 3.6 + tw(name, fnt("b", 2.15)) + 3.0
    st = {r["name"]: r["area_mm2"] for r in HI["size_table"]}
    lm_areas = [l["projected_area_mm2"] for l in CM["landmarks"]]
    basic = [p["box_area"] for p in FR["panels"] if p["tier"] == "Basic"]
    det = [d["projected_area_mm2"] for d in DET["map_elements"]] + [PANEL["D"]["box_area"]]
    line3 = ("위계(투영 상자 mm²): Core 지도 무대 %s > 콜로세움 %s(최대 단일 오브젝트, 표준 랜드마크 중앙값의 %.1f배) · 표준 랜드마크 %s~%s > "
             "Basic %s~%s ≥ Detail %s~%s(비 %.2f) > Support %s(비 %.2f) · 베수비오(지도 배경) %s" %
             (format(int(FR["stage"]["area_mm2"]), ","), format(HERO["projected_area_mm2"], ","), HI["ratios"]["hero_over_landmark_median"],
              format(min(lm_areas), ","), format(max(lm_areas), ","), format(min(basic), ","), format(max(basic), ","),
              format(min(det), ","), format(max(det), ","), HI["ratios"]["basic_min_over_detail_max"], format(PANEL["S"]["box_area"], ","),
              HI["ratios"]["detail_min_over_support"], format(VES["projected_area_mm2"], ",")))
    P.text(x0 + 2.0, y1 + 4.9, line3, fnt("m", 2.15), INK_L)
    hc, cg, de = MEAS["hero_cluster"], MEAS["core_group_city"], MEAS["density_estimate"]
    line4 = ("히어로 군 상자 %.1f%%·껍질 %.1f%%·실루엣 %.1f%% · 도심·시내 코어 군 %.1f%%·%.1f%%·%.1f%% · 밀도 %.1f%%(심은 지면 포함 %.1f%%) · 라벨 %d(벽면·깃대·태그 %d + 바닥 %d) · "
             "패널 %d(포스터의 %.1f%%) · 모서리 표시 = 투영 상자 · 등각 글자 = 지도 라벨 · 정면 글자 = 다이어그램 주석" %
             (hc["bbox_pct_stage"], hc["hull_pct_stage"], hc["silhouette_pct_stage"], cg["bbox_pct_stage"], cg["hull_pct_stage"], cg["silhouette_pct_stage"],
              de["objects_pct_stage_est"], de["objects_plus_planted_pct_stage_est"], LBS["count"]["total"], LBS["count"]["wall_flag_tag"],
              LBS["count"]["floor_text"], len(FR["panels"]), FR["panel_area_pct_poster"]))
    P.text(x0 + 2.0, y1 + 9.4, line4, fnt("m", 2.15), INK_L)


def draw_ticks():
    c = (150, 134, 108)
    for x in range(0, 421, 10):
        Lt = 3.0 if x % 50 == 0 else 1.5
        P.line([(x, 0), (x, Lt)], c, 0.2, joint=False)
        if x % 50 == 0 and 0 < x < 420:
            P.text_c(x, 6.2, str(x), fnt("m", 2.1), c)
    for y in range(0, 595, 10):
        Lt = 3.0 if y % 50 == 0 else 1.5
        P.line([(0, y), (Lt, y)], c, 0.2, joint=False)
        P.line([(PW - Lt, y), (PW, y)], c, 0.2, joint=False)
    sx0, sy0, sx1, sy1 = STAGE
    for y, lab, dy in ((sy0, "y %g" % sy0, -1.4), (sy1, "y %g" % sy1, 3.4)):
        P.line([(0, y), (6.0, y)], T_COL["Core"], 0.45, joint=False)
        P.line([(PW - 6.0, y), (PW, y)], T_COL["Core"], 0.45, joint=False)
        P.text(1.0, y + dy, lab, fnt("b", 2.1), T_TXT["Core"])


# ───────────────────────── 10 다이어그램 주석(티어 색 모서리·꼬리표·히어로 군 윤곽) ─────────────────────────
def load_sil():
    try:
        with open(SIL_PATH, "rb") as fh:
            d = fh.read()
        hl = int.from_bytes(d[8:10], "little")
        hdr = d[10:10 + hl].decode("latin1")
        m = re.search(r"\((\d+),\s*(\d+)\)", hdr)
        h, w = int(m.group(1)), int(m.group(2))
        img = Image.frombytes("L", (w, h), d[10 + hl:10 + hl + w * h])
        return img.point(lambda v: 255 if v else 0)
    except Exception as e:
        REPORT["notes"].append("히어로 군 실루엣을 읽지 못함: %s" % e)
        return None


def draw_hero_contour():
    m = load_sil()
    if m is None:
        return
    m = m.resize((P.w, P.h), Image.NEAREST)
    inner = m.filter(ImageFilter.MinFilter(5))
    edge = ImageChops.subtract(m, inner)
    dots = Image.new("L", m.size, 0)
    dd = ImageDraw.Draw(dots)
    step = int(2.2 * KD)
    for yy in range(0, m.size[1], step):
        dd.rectangle([0, yy, m.size[0], yy + int(1.3 * KD)], fill=255)
    edge = ImageChops.multiply(edge, dots)
    line_img = Image.new("RGBA", m.size, T_COL["Core"] + (0,))
    line_img.putalpha(edge.point(lambda v: 190 if v else 0))
    P.img.alpha_composite(line_img)


def draw_annotations():
    core_t = T_TXT["Core"]
    # 지도 무대 = Core
    pill(P, 2.0, STAGE[1] + 0.6, "CORE · 로마 건축물 지도 · 무대 420×413mm = %smm²(포스터 높이 69.5%%)" % format(int(FR["stage"]["area_mm2"]), ","), core_t, em=2.0)
    # 표준 랜드마크·배경: 초록 모서리 + 꼬리표
    pos = {"L1": ("bl", "판테온"), "L2": ("tl", "트라야누스 시장"), "L3": ("bl", "카라칼라 욕장(절개)"), "L4": ("br", "수도교 아치 열"),
           "L5": ("tr", "메텔라 무덤"), "L6": ("tl", "포르투스 항")}
    for lid, (p, nm) in pos.items():
        l = LM[lid]
        b = l["projected_box"]
        corner_marks(P, b, T_COL["Core"], arm=3.2, lw=0.36)
        w_, h_ = b[2] - b[0], b[3] - b[1]
        t = "%s %s · %.0f×%.0f · %smm²" % (lid, nm, w_, h_, format(int(l["projected_area_mm2"]), ","))
        if p == "bl":
            pill(P, b[0] + 0.8, b[3] - 3.8, t, core_t, em=1.95)
        elif p == "tl":
            pill(P, b[0] + 0.8, b[1] + 0.6, t, core_t, em=1.95)
        elif p == "tr":
            pill(P, b[2] - 0.4, b[1] - 3.4, t, core_t, em=1.95, anchor="r")
        else:
            pill(P, b[2] - 0.4, b[3] + 0.6, t, core_t, em=1.95, anchor="r")
    b = VES["projected_box"]
    corner_marks(P, b, T_COL["Core"], arm=2.6, lw=0.3)
    pill(P, 338.5, STAGE[1] + 1.0, "V 베수비오(지도 배경) · %.0f×%.0f · %smm²" % (b[2] - b[0], b[3] - b[1], format(VES["projected_area_mm2"], ",")), core_t, em=1.75)
    # 히어로
    hb = HERO["projected_box"]
    corner_marks(P, hb, T_COL["Core"], arm=5.0, lw=0.55)
    pill(P, hb[2] + 0.2, hb[3] + 1.0, "콜로세움 = Core 히어로 · 최대 단일 오브젝트", core_t, em=2.2, anchor="r")
    pill(P, hb[2] + 0.2, hb[3] + 4.6, "투영 상자 %.1f×%.1fmm = %smm²(랜드마크 중앙값의 %.1f배)" % (HERO["projected_wh"][0], HERO["projected_wh"][1],
         format(HERO["projected_area_mm2"], ","), HI["ratios"]["hero_over_landmark_median"]), core_t, em=1.85, anchor="r", bold=False)
    # Detail 꼬리표(확대 창)
    z = DMAP["Z1"]
    zc, zd = z["circle"]["c"], z["circle"]["d"]
    pill(P, zc[0] + 4.0, zc[1] + zd / 2.0 + 0.8, "Z1 · Detail · Ø%.0f · %smm²" % (zd, format(z["projected_area_mm2"], ",")), T_TXT["Detail"], em=1.8)
    # Basic 지시선 꼬리표
    lk = BAS["process_representation"]["link"]
    (lx0, ly0), (lx1, ly1) = lk["pts"]
    pill(P, lx0 - 1.6, 488.6, "Basic 지시선 · 제작 과정 ⑥ → 공사장 %.0fmm" % (ly1 - ly0), T_TXT["Basic"], em=1.75, anchor="r")
    # 히어로 군(실루엣 윤곽) 꼬리표
    hc = MEAS["hero_cluster"]
    pill(P, 2.0, 302.0, "히어로 군(점선 윤곽) 상자 %.1f%% · 껍질 %.1f%% · 실루엣 %.1f%%" % (hc["bbox_pct_stage"], hc["hull_pct_stage"], hc["silhouette_pct_stage"]),
         core_t, em=1.75, bold=False)
    # 타이틀 ↔ 욕장 위 끝(2mm)
    bbx = GEO.get("bath_box")
    if bbx:
        P.line([(bbx[0] + 56, FR["title"]["rect"][3]), (bbx[0] + 56, bbx[1])], core_t, 0.3, joint=False)


# ───────────────────────── 11 겹침 검사(래스터) ─────────────────────────
def overlap_check():
    K = 2
    masks = []
    for name, poly in LABEL_POLYS:
        bb = bbox_of(poly)
        m = Image.new("L", (PW * K, PH * K), 0)
        ImageDraw.Draw(m).polygon([(x * K, y * K) for x, y in poly], fill=255)
        masks.append((name, m, bb))
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
    """그린 외곽(투영 상자)으로 새 위계를 다시 판정한다"""
    o = REPORT["objects"]

    def area(k):
        b = o[k]["그린 외곽"]
        return (b[2] - b[0]) * (b[3] - b[1])
    hero = area("hero")
    lms = {k: area(k) for k in ("L1", "L2", "L3", "L4", "L5", "L6")}
    ves = area("V")
    basic = {p: PANEL[p]["box_area"] for p in ("L", "R", "B", "T")}
    detail = {"D": PANEL["D"]["box_area"], "Z1": area("Z1")}
    for d in DET["map_elements"]:
        if d["kind"] == "콜아웃":
            b = d["box"]
            detail[d["id"]] = (b[2] - b[0]) * (b[3] - b[1])
    sup = PANEL["S"]["box_area"]
    REPORT["hierarchy_drawn"] = {
        "콜로세움 mm²": int(round(hero)), "랜드마크 mm²": {k: int(round(v)) for k, v in lms.items()}, "베수비오 mm²": int(round(ves)),
        "Basic mm²": basic, "Detail mm²": {k: int(round(v)) for k, v in detail.items()}, "Support mm²": sup,
        "콜로세움 ≥ 랜드마크 최대 × 1.1": hero >= max(lms.values()) * 1.1,
        "콜로세움 > 가장 큰 패널(B)": hero > PANEL["B"]["box_area"],
        "Basic 최소 ≥ Detail 최대": min(basic.values()) >= max(detail.values()),
        "Detail 최소 ≥ Support × 1.1": min(detail.values()) >= sup * 1.1,
        "베수비오 ≤ 랜드마크 최소 ÷ 1.1": ves <= min(lms.values()) / 1.1,
    }
    REPORT["notes"].append("겹침 검사 범위: 지도 라벨·바닥 글·말풍선 태그 ↔ 서로, 그리고 콜아웃·패널·확대 창·다이어그램 꼬리표(래스터 0.5mm 격자, 0.3mm² 넘으면 기록)")


# ───────────────────────── 12 실행 ─────────────────────────
def main():
    build_exclusions()
    plan_labels()
    draw_ground()
    draw_fields()
    draw_river()
    draw_sea()
    draw_coast_section()
    draw_roads()
    draw_vesuvius()
    draw_albano()
    draw_floor_texts()
    draw_scatter()
    draw_caracalla()
    draw_aqueduct()
    draw_market()
    draw_pantheon()
    draw_kiln()
    draw_barge(PROPS["바지선 1"], "X", "바지선 1")
    ac = PROPS["아피아 가도 수레"]
    draw_road_cart(ac, "아피아 가도 수레", 485.6, 72.0, "Y", ASH_G)
    draw_arena()
    draw_dock()
    draw_road_cart(PROPS["재료 수레"], "재료 수레", 462.3, 278.0, "Y", LIME_W)
    draw_metella()
    draw_portus()
    draw_barge(PROPS["바지선 2"], "Y", "바지선 2")
    draw_worksite()
    draw_ostia()
    draw_villa()
    draw_ash_ship()
    draw_z1()
    draw_c1()
    draw_c2()
    draw_c4()
    draw_leaders()
    draw_labels()
    draw_title()
    draw_panel_L()
    draw_panel_R()
    draw_panel_B()
    draw_panel_D()
    draw_panel_T()
    draw_panel_S()
    panel_frame("L", "above_l")
    panel_frame("R", "above_r")
    panel_frame("B", "above_l")
    panel_frame("D", "above_l")
    panel_frame("T", "above_r")
    panel_frame("S", "above_r")
    draw_footer()
    draw_ticks()
    draw_hero_contour()
    draw_annotations()
    overlap_check()
    hierarchy_check()
    out = P.img.resize((PW * OUT_PX_PER_MM, PH * OUT_PX_PER_MM), Image.LANCZOS).convert("RGB")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out.save(OUT, optimize=True)
    REPORT["output"] = OUT
    REPORT["size_px"] = out.size
    REPORT["seconds"] = round(time.time() - T_START, 1)
    print(json.dumps(REPORT, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
