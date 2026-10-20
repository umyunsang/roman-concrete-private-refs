# -*- coding: utf-8 -*-
"""로마 편 최종 배치 다이어그램 — final_layout_spec.json을 읽어 A2 배치 다이어그램 PNG(1mm = 3px, 1260×1782)를 그린다.

실행: uv run --no-project --with pillow python -I /Users/um-yunsang/roman-concrete-private-refs/.work/scripts/diagrams/final_layout.py [출력 PNG]
- 그리기 도구: v16 common.py(레이어·글꼴·등각 글자·라벨 규격) + prim.py(로우폴리 메시). core_group_v3.py와 같은 바탕이다.
- 입력: 최종 배치 사양 JSON, 코어 군 실루엣 마스크(final_spec_core_sil.npy = 사양 검사 final_spec_check.py와 같은 마스크)
- 좌표: A2 mm(x 오른쪽, y 아래). 등각: 평면 +X → 화면 ↘, +Y → 화면 ↙, +Z → 위(v16 common.Iso와 같다)
- 그리는 순서: 지면 → 밭 → 코어 군 영역 → 바다 → 강 → 길·바닥 글 → 랜드마크(뒤→앞) → 공정 셀 → 아레나 → 흐름 → 확대 창 → 라벨 → 틀 → 주석
"""
import json
import math
import os
import re
import sys
import time

ROOT = "/Users/um-yunsang/roman-concrete-private-refs"
sys.dont_write_bytecode = True
sys.path.insert(0, ROOT + "/.work/scripts/wf/v16")
from prim import *  # noqa: F401,F403  (common.* 포함)
from prim import _hull  # noqa: F401
from PIL import Image, ImageDraw, ImageFilter, ImageChops

T_START = time.time()
SPEC_PATH = ROOT + "/.work/out/refs-analysis/final_layout_spec.json"
SIL_PATH = ROOT + "/.work/out/refs-analysis/_work/final_spec_core_sil.npy"
OUT = sys.argv[1] if len(sys.argv) > 1 else ROOT + "/docs/design/최종-배치-다이어그램.png"
OUT_PX_PER_MM = 3

with open(SPEC_PATH, encoding="utf-8") as fh:
    S = json.load(fh)
FR, CG = S["frame"], S["core_group"]
CH, AR, RV = CG["chain"], CG["arena"], CG["river"]
SC, HC, MM = S["sea_coast"], S["hierarchy_check"], CG["measured_model"]
LBS = S["labels"]
REPORT = {"objects": {}, "labels": {}, "notes": []}
GEO = {}
LABEL_POLYS = []     # (이름, 화면 다각형) — 겹침 검사용

# ───────────────────────── 팔레트 ─────────────────────────
GROUND = (236, 216, 172)
GRID_OP = (228, 206, 162)
CORE_TINT = (247, 205, 196)
SEA_C = (146, 182, 208)
SEA_EDGE = (88, 128, 164)
HARBOR_C = (158, 194, 216)
RIV_C = (116, 172, 212)
RIV_EDGE = (68, 118, 164)
ROAD_C = (208, 190, 152)
ROAD_EDGE = (150, 128, 94)
APPIA_C = (192, 170, 130)
INK_L = (58, 42, 28)
FIELD_G = (176, 186, 118)
VINE_C = (120, 146, 80)
WHEAT_C = (226, 200, 122)
PASTURE_C = (196, 202, 140)
OLIVE_C = (118, 146, 92)
WOOD = (150, 108, 68)
WOOD_L = (184, 142, 96)
LIME_W = (246, 244, 236)
ASH_R = (150, 82, 60)
AGG_G = (156, 150, 140)
CLOTHS = [(150, 70, 52), (96, 110, 140), (172, 140, 82), (118, 92, 128), (92, 122, 90)]
STRATA7 = [(1.2, (94, 126, 66)), (1.8, (128, 98, 62)), (2.0, (150, 118, 80)), (2.0, (112, 86, 56))]
STEP_NOTE = {1: "생석회·화산재·골재 반입", 2: "생석회 + 화산재, 물 없이 섞기", 3: "민물(육상 건물) 붓기",
             4: "발열 반응 → 석회 알갱이", 5: "기초·볼트 거푸집에 다진다", 6: "굳으며 석회 알갱이가 남는다"}


# ───────────────────────── 공통 도우미 ─────────────────────────
def lerp(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def isoxy(ox, oy, X, Y, Z=0.0):
    return (ox + C30 * (X - Y), oy + 0.5 * (X + Y) - Z)


def proj(p):
    X, Y = p[0], p[1]
    Z = p[2] if len(p) > 2 else 0.0
    return (C30 * (X - Y), 0.5 * (X + Y) - Z)


def mesh_pts(*meshes):
    out = []
    for m in meshes:
        for f in m.faces:
            out.extend(f[0])
    return out


def fit(pts3, box, ax="c", ay="c", pad=0.0):
    """평면 점들의 화면 외곽 상자를 box 안에 맞추는 원점 (ox, oy)와 외곽 상자(화면)"""
    pp = [proj(p) for p in pts3]
    xs = [p[0] for p in pp]
    ys = [p[1] for p in pp]
    bx0, by0, bx1, by1 = box
    if ax == "c":
        ox = (bx0 + bx1) / 2.0 - (min(xs) + max(xs)) / 2.0
    elif ax == "l":
        ox = bx0 + pad - min(xs)
    else:
        ox = bx1 - pad - max(xs)
    if ay == "c":
        oy = (by0 + by1) / 2.0 - (min(ys) + max(ys)) / 2.0
    elif ay == "t":
        oy = by0 + pad - min(ys)
    else:
        oy = by1 - pad - max(ys)
    return ox, oy, (ox + min(xs), oy + min(ys), ox + max(xs), oy + max(ys))


class SIso(Iso):
    """평면 좌표를 sc배 해서 투영하는 등각 틀(아이콘을 사양 투영 상자 크기에 맞출 때)"""

    def __init__(self, L, ox, oy, sc=1.0):
        Iso.__init__(self, L, ox, oy)
        self.sc = sc

    def p(self, X, Y, Z=0.0):
        s = self.sc
        return (self.ox + C30 * (X - Y) * s, self.oy + 0.5 * (X + Y) * s - Z * s)


def icon_frame(key, box, max_sc=1.6):
    _, _, bb = fit(key, box)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    sc = min((box[2] - box[0]) / w, (box[3] - box[1]) / h, max_sc)
    ks = [(p[0] * sc, p[1] * sc, (p[2] if len(p) > 2 else 0.0) * sc) for p in key]
    ox, oy, bb2 = fit(ks, box)
    return ox, oy, sc, bb2


BATH_KEY = [(0, 0, 0), (40, 0, -1.2), (40, 40, -1.2), (0, 40, -1.2), (3, 3, 20), (37, 3, 20), (3, 37, 20), (16, 16, 23.2)]
PANTHEON_KEY = [(-19, -19, 0), (19, -19, 0), (19, 19, -1.0), (-19, 19, -1.0), (0, 0, 32.4), (0, 27.6, 19.0)]


def record(key, name, tier, spec_box, drawn_box):
    sb = [round(v, 1) for v in spec_box]
    db = [round(v, 1) for v in drawn_box]
    dev = max(abs(a - b) for a, b in zip(sb, db))
    REPORT["objects"][key] = {"이름": name, "티어": tier, "사양 상자": sb, "그린 외곽": db, "최대 편차mm": round(dev, 1)}


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


def pill(L, x, y, text, col, em=2.4, anchor="l", fill=(255, 251, 242, 236), bold=True):
    """다이어그램 주석 꼬리표(정면 글자). (x, y) = 꼬리표 왼쪽 위(anchor l) 또는 가운데 위(c)."""
    f = fnt("b" if bold else "m", em)
    w = tw(text, f) + 2.0
    h = em * 1.38
    if anchor == "c":
        x -= w / 2.0
    elif anchor == "r":
        x -= w
    rrect(L, x, y, x + w, y + h, h * 0.32, fill=fill, outline=tuple(col[:3]) + (230,), lw=0.28)
    L.text(x + 1.0, y + h * 0.76, text, f, col)
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


def band_mw(pts, ws):
    """중심선 꺾은선 → 띠 다각형. ws = 구간별 '수직 폭'(±30° 구간에서는 평면 폭과 같다). 마이터 이음."""
    segs = []
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        Ls = math.hypot(x1 - x0, y1 - y0)
        d = ((x1 - x0) / Ls, (y1 - y0) / Ls)
        n = (-d[1], d[0])
        segs.append((pts[i], pts[i + 1], d, n, ws[i] / 2.0 * abs(d[0])))

    def side(sg):
        out = []
        for i, (p0, p1, d, n, h) in enumerate(segs):
            a = (p0[0] + sg * n[0] * h, p0[1] + sg * n[1] * h)
            if i == 0:
                out.append(a)
            if i < len(segs) - 1:
                q0, _q1, d2, n2, h2 = segs[i + 1]
                a2 = (q0[0] + sg * n2[0] * h2, q0[1] + sg * n2[1] * h2)
                det = d[0] * (-d2[1]) - d[1] * (-d2[0])
                t = ((a2[0] - a[0]) * (-d2[1]) - (a2[1] - a[1]) * (-d2[0])) / det
                out.append((a[0] + t * d[0], a[1] + t * d[1]))
            else:
                out.append((p1[0] + sg * n[0] * h, p1[1] + sg * n[1] * h))
        return out

    A_, B_ = side(+1), side(-1)
    return A_ + B_[::-1], A_, B_


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


def find(lst, key, prefix):
    for it in lst:
        if it[key].startswith(prefix):
            return it
    raise KeyError(prefix)


def iso_arrow(L, p, direction, col, s=1.0):
    """바닥에 눕힌 화살표(평면 +X ↘ 또는 +Y ↙)"""
    base = [(-4.2, -1.15), (0.9, -1.15), (0.9, -2.9), (4.4, 0.0), (0.9, 2.9), (0.9, 1.15), (-4.2, 1.15)]
    pts = []
    for X, Y in base:
        X, Y = X * s, Y * s
        if direction == "Y":
            X, Y = Y, X
        pts.append(isoxy(p[0], p[1], X, Y))
    L.poly(pts, fill=col, outline=shade(col, 0.7), lw=0.15)


P = Layer(0, 0, PW, PH, "최종배치", bg=BG + (255,))


# ───────────────────────── 1 지면·밭 ─────────────────────────
def draw_ground():
    sx0, sy0, sx1, sy1 = FR["stage"]["rect"]
    P.rect(sx0, sy0, sx1, sy1, fill=GROUND)
    G = Layer(sx0, sy0, sx1, sy1)
    span = (sx1 - sx0) * T30
    for k in range(-40, 60):
        y0 = sy0 + k * 14.0
        G.line([(sx0, y0), (sx1, y0 + span)], GRID_OP, 0.16, joint=False)
        G.line([(sx0, y0 + span), (sx1, y0)], GRID_OP, 0.16, joint=False)
    P.paste(G)


def parcel(ox, oy, X0, Y0, X1, Y1):
    return [isoxy(ox, oy, X0, Y0), isoxy(ox, oy, X1, Y0), isoxy(ox, oy, X1, Y1), isoxy(ox, oy, X0, Y1)]


def texture(kind, ox, oy, X0, Y0, X1, Y1, key):
    rng = local_rng(key)
    poly = parcel(ox, oy, X0, Y0, X1, Y1)
    base = {"olive": (186, 192, 128), "wheat": WHEAT_C, "vine": (184, 190, 122), "pasture": PASTURE_C}[kind]
    P.poly(poly, fill=base, outline=shade(base, 0.82), lw=0.2)
    if kind == "wheat":
        Y = Y0 + 1.6
        while Y < Y1 - 0.8:
            P.line([isoxy(ox, oy, X0 + 0.8, Y), isoxy(ox, oy, X1 - 0.8, Y)], shade(base, 0.86), 0.18, joint=False)
            Y += 1.9
    elif kind == "vine":
        X = X0 + 1.4
        while X < X1 - 0.8:
            P.line([isoxy(ox, oy, X, Y0 + 0.9), isoxy(ox, oy, X, Y1 - 0.9)], VINE_C, 0.42, joint=False)
            X += 2.3
    elif kind == "olive":
        iso = Iso(P, ox, oy)
        X = X0 + 2.6
        while X < X1 - 1.6:
            Y = Y0 + 2.6 + (1.2 if int(X) % 2 else 0.0)
            while Y < Y1 - 1.6:
                cx, cy = iso.p(X, Y, 0)
                P.ell(cx + 0.4, cy + 0.2, 1.6, 0.6, fill=(140, 140, 96))
                P.ell(cx, cy - 1.3, 1.5, 1.2, fill=OLIVE_C, outline=(86, 110, 66), lw=0.12)
                Y += 4.4 + rng.random() * 0.6
            X += 4.6
    return poly


def draw_fields():
    lf = find(S["props"], "name", "올리브")
    bx0, by0, bx1, by1 = lf["box"]
    A_, B_ = 62.0, 48.0                      # 평면 구획(↘ 62, ↙ 48) → 화면 95×55
    cx, cy = (bx0 + bx1) / 2.0, (by0 + by1) / 2.0 + 2.0
    ox = cx - C30 * (A_ - B_) / 2.0
    oy = cy - 0.5 * (A_ + B_) / 2.0
    kinds = [["pasture", "pasture", "vine"], ["vine", "wheat", "olive"], ["wheat", "olive", "vine"]]
    xs = [(0, 20), (21, 41), (42, 62)]
    ys = [(0, 15), (16, 31), (32, 48)]
    for j, (Y0, Y1) in enumerate(ys):
        for i, (X0, X1) in enumerate(xs):
            texture(kinds[j][i], ox, oy, X0, Y0, X1, Y1, "들%d%d" % (i, j))
    GEO["fields_box"] = (ox - C30 * B_, oy, ox + C30 * A_, oy + 0.5 * (A_ + B_))
    # 오른쪽 아래 포도밭(아피아 가도 남쪽, 오른쪽 블리드)
    texture("vine", 398.0, 418.0, 0, 0, 50, 26, "포도밭1")
    texture("vine", 404.0, 452.0, 0, 0, 34, 34, "포도밭2")


# ───────────────────────── 2 코어 군 영역(사양 검사 실루엣) ─────────────────────────
def load_sil():
    try:
        with open(SIL_PATH, "rb") as fh:
            d = fh.read()
        hl = int.from_bytes(d[8:10], "little")
        hdr = d[10:10 + hl].decode("latin1")
        m = re.search(r"\((\d+),\s*(\d+)\)", hdr)
        h, w = int(m.group(1)), int(m.group(2))
        return Image.frombytes("L", (w, h), d[10 + hl:10 + hl + w * h])
    except Exception as e:  # 실루엣이 없으면 볼록 껍질로 대신한다
        REPORT["notes"].append("실루엣 마스크를 읽지 못해 볼록 껍질로 대신함: %s" % e)
        return None


def draw_core_tint():
    m = load_sil()
    if m is None:
        pts = []
        for c in CH["cells"]:
            pts += [tuple(v) for v in c["verts_TRBL"]]
        pts += [tuple(p) for p in AR["base_oct_screen"]]
        for seg in RV["segments"]:
            pts += [tuple(p) for p in seg["pts"]]
        hull = _hull(pts)
        P.poly(hull, fill=CORE_TINT)
        return
    m = m.filter(ImageFilter.GaussianBlur(4)).point(lambda v: 255 if v >= 128 else 0)
    m = m.resize((P.w, P.h), Image.BILINEAR).point(lambda v: 255 if v >= 128 else 0)
    tint_img = Image.new("RGBA", m.size, CORE_TINT + (0,))
    tint_img.putalpha(m.point(lambda v: 228 if v else 0))
    P.img.alpha_composite(tint_img)
    outer = m.filter(ImageFilter.GaussianBlur(3)).point(lambda v: 255 if v > 24 else 0)
    edge = ImageChops.subtract(outer, m)
    line_img = Image.new("RGBA", m.size, C_CORE + (0,))
    line_img.putalpha(edge.point(lambda v: 200 if v else 0))
    P.img.alpha_composite(line_img)
    bb = m.getbbox()
    GEO["sil_bbox"] = (bb[0] / KD, bb[1] / KD, bb[2] / KD, bb[3] / KD)


# ───────────────────────── 3 바다·해안 ─────────────────────────
def coast_b():
    (x0, y0), _ = SC["coastline"]["pts"]
    return y0 - T30 * x0


def draw_sea():
    b = coast_b()
    sea = [tuple(p) for p in SC["sea_polygon"]]
    under = [tuple(p) for p in SC["sea_under_bottom_band"]["poly"]]
    # 하단 띠 밑 연장(아래로 갈수록 바탕색으로 흐림)
    ys = [p[1] for p in under]
    xs = [p[0] for p in under]
    U = Layer(0, min(ys), max(xs), max(ys))
    U.poly(under, fill=SEA_C)
    g = Image.linear_gradient("L").resize((U.w, U.h)).point(lambda v: int((255 - v) * 0.62))
    U.img.putalpha(ImageChops.multiply(U.img.getchannel("A"), g))
    P.paste(U)
    P.poly(sea, fill=SEA_C)
    facet_fill(P, sea, SEA_C, cell=7.0, amp=0.045, key="바다", jit=0.12)
    for k in range(9):                                  # 잔물결(해안선과 평행)
        off = 16.0 + k * 13.0
        xa = 2.0 + (k % 3) * 9.0
        xb = min((505.0 - b - off) / T30, xa + 70.0)
        if xb > xa + 8:
            P.line([(xa, b + off + T30 * xa), (xb, b + off + T30 * xb)], (176, 204, 224), 0.3, joint=False)
    # 해안 단면(육지 판 앞 변): 10mm 3겹, 포르투스 부두 구간(x 4~76)은 3mm
    Lc = Layer(0, FR["stage"]["rect"][1], PW, FR["stage"]["rect"][3])
    (cx0, cy0), (cx1, cy1) = [tuple(p) for p in SC["coastline"]["pts"]]
    m_ = re.search(r"\(x\s*([\d.]+)~([\d.]+)\)은\s*([\d.]+)mm", SC["coast_section"])
    qx0, qx1, qd = (float(m_.group(1)), float(m_.group(2)), float(m_.group(3))) if m_ else (4.0, 76.0, 3.0)
    m2 = re.search(r"지층 단면\s*([\d.]+)mm", SC["coast_section"])
    deep = float(m2.group(1)) if m2 else 10.0

    def cp(x):
        return (x, b + T30 * x)
    for (xa, xb, dd, layers) in ((cx0, qx0, deep, None), (qx0, qx1, qd, "quay"), (qx1, cx1, deep, None)):
        a, c = cp(xa), cp(xb)
        if layers == "quay":
            Lc.poly([a, c, (c[0], c[1] + dd), (a[0], a[1] + dd)], fill=(198, 186, 160), outline=(120, 104, 80), lw=0.2)
            for t in range(1, 12):
                pt = lerp(a, c, t / 12.0)
                Lc.line([pt, (pt[0], pt[1] + dd)], (150, 136, 110), 0.12, joint=False)
        else:
            lay = [(1.4, (94, 126, 66)), (dd * 0.42, (130, 100, 64)), (dd - 1.4 - dd * 0.42, (156, 124, 86))]
            strata_side(Lc, a, c, lay, f=0.86)
    P.paste(Lc)
    soft_line(P, [(0, b + 0.2), (cx1, b + T30 * cx1 + 0.2)], (40, 60, 80), alpha=60, w=0.8, blur=0.4)
    GEO["coast_b"] = b
    GEO["coast_deep"] = deep
    GEO["quay_deep"] = qd


# ───────────────────────── 4 강 ─────────────────────────
def river_geom():
    segs = RV["segments"]
    pts = [tuple(segs[0]["pts"][0]), tuple(segs[0]["pts"][1]), tuple(segs[1]["pts"][1])]
    ws = [segs[0]["w"], segs[1]["w"]]
    return pts, ws


def draw_river():
    pts, ws = river_geom()
    poly, outer, inner = band_mw(pts, ws)
    P.poly(poly, fill=RIV_C)
    facet_fill(P, poly, RIV_C, cell=6.0, amp=0.05, key="강", jit=0.12)
    # 먼 둑 옆면(물이 지면보다 낮다): 윗팔은 바깥 변, 앞팔은 안쪽 변
    for (p0, p1) in ((outer[0], outer[1]), (inner[1], inner[2])):
        P.poly([p0, p1, (p1[0], p1[1] + 2.2), (p0[0], p0[1] + 2.2)], fill=(150, 124, 88))
        P.line([(p0[0], p0[1] + 2.2), (p1[0], p1[1] + 2.2)], (96, 140, 180), 0.25, joint=False)
    for edge in (outer, inner):
        soft_line(P, edge, (40, 30, 20), alpha=55, w=0.8, blur=0.4)
        P.line(edge, (214, 200, 170), 0.45)
    GEO["river_poly"] = poly
    GEO["river_outer"] = outer
    GEO["river_inner"] = inner


# ───────────────────────── 5 길·바닥 글 ─────────────────────────
def draw_road(pts, w, col=ROAD_C, edge=ROAD_EDGE, center=False):
    poly, A_, B_ = band_mw(pts, [w] * (len(pts) - 1))
    P.poly(poly, fill=col)
    P.line(A_, edge, 0.3)
    P.line(B_, edge, 0.3)
    if center:
        for i in range(len(pts) - 1):
            P.dashed(pts[i], pts[i + 1], (250, 246, 236), 0.9, 4.0, 2.6)
    return poly, A_, B_


def draw_roads():
    ap = find(S["roads"], "name", "아피아")
    pr = find(S["roads"], "name", "포르투스")
    ba = find(S["roads"], "name", "욕장")
    mr = CG["material_road"]
    GEO["appia"] = draw_road([tuple(p) for p in ap["pts"]], ap["w"], APPIA_C, (130, 108, 76), center=True)
    GEO["portus_road"] = draw_road([tuple(p) for p in pr["pts"]], pr["w"])
    GEO["material_road"] = draw_road([tuple(p) for p in mr["pts"]], mr["w"])
    # 욕장 앞길: 사양 시작점에서 같은 방향으로 거슬러 욕장 광장 앞 변까지 잇는다
    (x0, y0), (x1, y1) = [tuple(p) for p in ba["pts"]]
    k = (y1 - y0) / (x1 - x0)
    pl = GEO.get("bath_plaza")
    xs = x0
    if pl:
        L_, B_ = pl[3], pl[2]          # 앞-오른쪽 변: 오른쪽 꼭짓점 → 아래 꼭짓점
        R_ = pl[1]
        k2 = (B_[1] - R_[1]) / (B_[0] - R_[0])
        xs = (R_[1] - k2 * R_[0] - (y0 - k * x0)) / (k - k2)
    GEO["bath_road"] = draw_road([(xs, y0 + k * (xs - x0)), (x1, y1)], ba["w"])
    # 판테온 앞 골목: 광장 왼쪽 앞에서 ↙로 1단계 입구 쪽(2단계 간판 뒤에서 재료 운반 길과 만난다)
    if "pantheon_plaza" in GEO:
        Lv = GEO["pantheon_plaza"][3]
        st = (Lv[0] + 6.0, Lv[1] + 3.5)
        en = (st[0] - C30 * 52.0, st[1] + 0.5 * 52.0)
        GEO["pantheon_st"] = draw_road([st, en], 6.0, (214, 198, 160), ROAD_EDGE)


def draw_floor_texts():
    ft = {f["name"]: f for f in LBS["floor_text"]}
    # TIBERIS: 윗팔 물 위, ↗ 바닥 글(톤온톤 밝은 물색). 글 높이 가운데가 중심선에 오게 반 칸 내린다
    a = ft["TIBERIS 테베레강"]["anchor"]
    floor_line(P, a[0] + C30 * 1.6, a[1] + 0.5 * 1.6, [("TIBERIS", fnt("en", 4.6), (222, 240, 250)), ("테베레강", fnt("b", 3.6), (222, 240, 250))], M_FLOOR_NE)
    # VIA APPIA: 위 차선(사양 앵커 그대로)
    a = ft["VIA APPIA 아피아 가도"]["anchor"]
    a = (a[0] + 6.0, a[1] - 6.0 * T30)              # 메텔라 라벨 지시선(x≈381)을 피해 길을 따라 6mm 민다
    REPORT["notes"].append("VIA APPIA 바닥 글: 사양 앵커를 길 방향으로 6mm 옮김(메텔라 지시선과 겹침 방지)")
    floor_line(P, a[0], a[1], [("VIA APPIA", fnt("en", 4.4), (112, 90, 60)), ("아피아 가도", fnt("b", 3.3), (112, 90, 60))], M_FLOOR_NE)
    # VIA PORTUENSIS
    a = ft["VIA PORTUENSIS 포르투스 길"]["anchor"]
    w = floor_line(P, a[0], a[1], [("VIA PORTUENSIS", fnt("en", 4.0), (124, 102, 72)), ("포르투스 길", fnt("b", 3.1), (124, 102, 72))], M_FLOOR_SE)
    REPORT["notes"].append("VIA PORTUENSIS 바닥 글 끝 x=%.1f (확대 창 지시선 x 123 왼쪽)" % (a[0] + C30 * w))
    # MARE TYRRHENUM: 사양 앵커 (4,494)는 ↘ 22mm 만에 지도 아래 변(y 505)·B1 패널에 닿는다 → 포르투스와 운반선 사이 열린 바다로 옮긴다
    a0 = ft["MARE TYRRHENUM 티레니아해"]["anchor"]
    ax, ay = 6.0, 433.0
    col = (242, 249, 253)
    iso_text(P, "MARE TYRRHENUM", fnt("en", 4.6), col, M_FLOOR_SE, ax, ay)
    iso_text(P, "티레니아해", fnt("b", 3.6), col, M_FLOOR_SE, ax - C30 * 5.0, ay + 0.5 * 5.0)
    REPORT["notes"].append("MARE TYRRHENUM 바닥 글: 사양 앵커 (%g,%g) → (6,433)으로 옮김(하단 띠·B1 겹침 방지)" % (a0[0], a0[1]))


# ───────────────────────── 6 Support 랜드마크(받침 없이 지면에 묻는다) ─────────────────────────
def draw_bath():
    s1 = find(S["supports"], "id", "S1")
    box = s1["box"]
    ox, oy, sc, bb = icon_frame(BATH_KEY, box)
    iso = SIso(P, ox, oy, sc)
    base = m_box(0, 0, -1.2, 40, 40, 0, (196, 180, 150), top=(226, 214, 188))
    base.draw(iso, lw=0.12)
    GEO["bath_plaza"] = [iso.p(0, 0), iso.p(40, 0), iso.p(40, 40, -1.2), iso.p(0, 40, -1.2)]
    GEO["bath_plaza_screen"] = [iso.p(0, 0), iso.p(40, 0), iso.p(40, 40), iso.p(0, 40)]
    iso.poly3([(3, 3, 0.05), (37, 3, 0.05), (37, 37, 0.05), (3, 37, 0.05)], fill=(238, 228, 206), ol=(196, 180, 150), lw=0.15)
    walls = Mesh(None)
    walls.extend(m_box(3, 3, 0, 37, 5.6, 20, BRICK, top=BRICK_L))
    walls.extend(m_box(3, 5.6, 0, 5.6, 37, 20, BRICK, top=BRICK_L))
    walls.draw(iso, lw=0.12)
    for u0 in (27.0, 31.8):
        for (v0, v1) in ((2.0, 9.5), (12.0, 16.0)):
            iso.arch("L", 0, 5.6, 0, u0, u0 + 3.2, v0, v1, (140, 78, 56))
            iso.arch("R", 5.6, 0, 0, u0, u0 + 3.2, v0, v1, (118, 66, 46))
    rot = Mesh((16, 16, 6.5))
    for i in range(12):
        t0, t1 = math.radians(135 + 15 * i), math.radians(150 + 15 * i)
        a0 = (16 + 9.2 * math.cos(t0), 16 + 9.2 * math.sin(t0))
        a1 = (16 + 9.2 * math.cos(t1), 16 + 9.2 * math.sin(t1))
        rot.add([(a0[0], a0[1], 0.3), (a1[0], a1[1], 0.3), (a1[0], a1[1], 13), (a0[0], a0[1], 13)], (214, 190, 160), "in")
    rot.draw(iso, lw=0.08)
    dome = m_dome(16, 16, 13, 10, (206, 190, 166), n=24, rings=6, oculus=0.16, arc=(math.radians(135), math.radians(315)),
                  inner=(238, 226, 202), thick=1.0, section=(190, 112, 86))
    dome.draw(iso, lw=0.08)
    for ph in (0.20, 0.42, 0.64):                      # 코퍼(안쪽 면 네모 홈)
        for i in range(7):
            th = 150 + i * 22.0
            q = []
            for (dt, dp) in ((-6, -0.07), (6, -0.07), (6, 0.07), (-6, 0.07)):
                t = math.radians(th + dt)
                p = (ph + dp) * math.pi / 2.0
                r = 8.85
                q.append((16 + r * math.cos(p) * math.cos(t), 16 + r * math.cos(p) * math.sin(t), 13 + r * math.sin(p)))
            iso.poly3(q, fill=(212, 196, 168))
    soft(P, [iso.p(14.6, 14.6, 22.4), iso.p(17.4, 17.4, 22.4), iso.p(22, 23, 0.3), iso.p(17, 20, 0.3)], (255, 246, 210), alpha=95, blur=0.5)
    m_box(20, 21, 0.0, 34, 34, 1.0, (210, 198, 176), top=(226, 216, 196)).draw(iso, lw=0.1)
    iso.poly3([(21, 22, 1.0), (33, 22, 1.0), (33, 33, 1.0), (21, 33, 1.0)], fill=(112, 182, 216), ol=(80, 140, 180), lw=0.15)
    for (X, Y) in ((24, 26), (29, 29)):
        cx, cy = iso.p(X, Y, 4.0)
        soft_ell(P, cx, cy, 3.4, 2.2, (255, 255, 255), alpha=40, blur=0.7)
    people = Mesh(None)
    people.extend(m_person(25, 18.5, 0.3, 5.5, CLOTHS[0], key="욕장1"))
    people.extend(m_person(33.5, 19.0, 0.3, 5.5, CLOTHS[1], key="욕장2"))
    people.draw(iso, lw=0.06)
    fr = Mesh(None)
    fr.extend(m_box(5.6, 34.4, 0, 37, 37, 5.2, BRICK, top=(176, 98, 72)))
    fr.extend(m_box(34.4, 5.6, 0, 37, 34.4, 5.2, BRICK, top=(176, 98, 72)))
    fr.draw(iso, lw=0.12)
    for k in range(8):
        u = 7.5 + k * 3.6
        iso.fpoly("L", 0, 37, 0, [(u, 0.6), (u + 1.6, 0.6), (u + 1.6, 2.2), (u, 2.2)], fill=(96, 56, 40))
        iso.fpoly("R", 37, 0, 0, [(u, 0.6), (u + 1.6, 0.6), (u + 1.6, 2.2), (u, 2.2)], fill=(84, 48, 34))
    record("S1", s1["name"], "Support", box, bb)


def draw_pantheon():
    s2 = find(S["supports"], "id", "S2")
    box = s2["box"]
    ox, oy, sc, bb = icon_frame(PANTHEON_KEY, box)
    iso = SIso(P, ox, oy, sc)
    m_box(-19, -19, -1.0, 19, 19, 0, (196, 182, 152), top=(228, 216, 190)).draw(iso, lw=0.12)
    GEO["pantheon_plaza"] = [iso.p(-19, -19), iso.p(19, -19), iso.p(19, 19), iso.p(-19, 19)]
    for X in range(-17, 18, 6):
        iso.line3([(X, -18.5, 0.02), (X, 18.5, 0.02)], (214, 200, 172), 0.12)
    bld = Mesh(None)
    bld.extend(m_cyl(0, 0, 14, 0, 17, (216, 202, 176), n=24))
    bld.extend(m_cyl(0, 0, 13.6, 17, 19.6, (206, 192, 166), n=24, k=0.93))
    bld.extend(m_dome(0, 0, 19.6, 12.6, (198, 190, 174), n=24, rings=6, oculus=0.12))
    bld.extend(m_box(-7.5, 9.0, 0, 7.5, 16.5, 15.0, (214, 200, 174)))
    bld.extend(m_box(-9.6, 16.5, 0, 9.6, 27.6, 1.2, (222, 210, 184)))
    for x in (-8.3, -5.95, -3.6, -1.2, 1.2, 3.6, 5.95, 8.3):
        bld.extend(m_cyl(x, 26.6, 0.8, 1.2, 12.0, (242, 234, 216), n=8))
    for y in (19.2, 22.9):
        for x in (-8.3, 8.3):
            bld.extend(m_cyl(x, y, 0.8, 1.2, 12.0, (242, 234, 216), n=8))
    bld.extend(m_box(-9.6, 16.5, 12.0, 9.6, 27.6, 13.6, (232, 222, 200)))
    bld.extend(m_gable(-9.6, 16.5, 9.6, 27.6, 13.6, 19.0, (202, 188, 162), wall=(228, 216, 192), axis="Y"))
    bld.draw(iso, lw=0.08)
    people = Mesh(None)
    people.extend(m_person(-12, 23, 0, 5.0, CLOTHS[2], key="판테온1"))
    people.extend(m_person(13, 15, 0, 5.0, CLOTHS[3], key="판테온2"))
    people.draw(iso, lw=0.06)
    record("S2", s2["name"], "Support", box, bb)


def draw_vesuvius():
    s6 = S["support2"][0]
    box = s6["box"]
    rings = [(23.0, 0.0), (18.8, 8.0), (12.8, 18.0), (7.6, 25.2), (5.3, 27.6)]
    cols = [(132, 152, 94), (150, 146, 104), (148, 124, 96), (136, 118, 102)]
    n = 18
    pts_r = []
    for j, (r, z) in enumerate(rings):
        ring_ = []
        for i in range(n):
            t = 2 * math.pi * i / n + 0.17 * j
            rr = r * (1.0 + (0.07 * (2 * h01("베수비오", j, i) - 1) if j else 0.0))
            ring_.append((rr * math.cos(t), rr * math.sin(t), z + (0.6 * (2 * h01("베수비오z", j, i) - 1) if 0 < j < 4 else 0.0)))
        pts_r.append(ring_)
    m = Mesh((0, 0, 8))
    for j in range(len(rings) - 1):
        A_, B_ = pts_r[j], pts_r[j + 1]
        c = mix(cols[min(j, 3)], GROUND, 0.45)
        for i in range(n):
            m.add([A_[i], A_[(i + 1) % n], B_[(i + 1) % n]], c)
            m.add([A_[i], B_[(i + 1) % n], B_[i]], c)
    crater = [(2.6 * math.cos(2 * math.pi * i / n), 2.6 * math.sin(2 * math.pi * i / n), 25.8) for i in range(n)]
    T_ = pts_r[-1]
    cm = Mesh((0, 0, 30))
    for i in range(n):
        cm.add([T_[i], T_[(i + 1) % n], crater[(i + 1) % n], crater[i]], mix((118, 102, 90), GROUND, 0.45), "two")
    allp = [p for r_ in pts_r for p in r_]
    ox, oy, bb = fit(allp, box)
    iso = Iso(P, ox, oy)
    sub = Layer(box[0] - 4, box[1] - 4, box[2] + 4, box[3] + 4)
    isub = Iso(sub, ox, oy)
    m.draw(isub, lw=0.08)
    cm.draw(isub, lw=0.08, cull=False)
    merge(P, sub, opacity=0.92, blur=0.18)
    GEO["vesuvius"] = (ox, oy)
    record("S6", s6["name"], "Support-2", box, bb)
    # 밑동 포도밭 농장(대기 원근 없이 앞에)
    farm = find(S["props"], "name", "포도밭 농장")
    fb = farm["box"]
    fk = [(0, 0, 0), (24, 0, 0), (24, 14, 0), (0, 14, 0), (3, 2, 7.2)]
    fx, fy, fbb = fit(fk, fb, ay="b", pad=0.5)
    texture("vine", fx, fy, 0, 0, 24, 14, "농장포도")
    fiso = Iso(P, fx, fy)
    house = m_house(2, 1, 9, 6, 0, 3.6, 2.6, (232, 220, 196), (190, 92, 64))
    house.draw(fiso, lw=0.1)
    cyp = m_cypress(11, 2.5, 0, 9.0, 1.3, key="농장사이프러스")
    cyp.draw(fiso, lw=0.06)


def draw_aqueduct():
    s3 = find(S["supports"], "id", "S3")
    box = s3["box"]
    mm = re.findall(r"\(([\d.]+),\s*([\d.]+)\)", s3["link"])
    (x0s, y0s), (x1s, y1s) = [(float(a), float(b)) for a, b in mm[:2]]
    Lp = (x1s - x0s) / C30                      # 평면 길이(88)
    iso = Iso(P, x0s, y0s)
    H_, T_ = 14.6, 1.6
    stone = (212, 186, 150)
    m_box(0, -T_, 0, Lp - 4.5, T_, H_, stone, top=(226, 206, 172)).draw(iso, lw=0.12)
    pitch = 7.0
    nA = int((Lp - 6.0) // pitch)
    for i in range(nA):
        u0 = 1.6 + i * pitch
        iso.arch("L", 0, T_, 0, u0, u0 + 4.6, 0.0, 8.6, (198, 176, 134), (150, 124, 92), 0.12)
    m_box(-0.3, -T_ - 0.4, H_, Lp - 4.5, T_ + 0.4, H_ + 1.4, (196, 168, 132), top=(214, 192, 160)).draw(iso, lw=0.12)
    iso.line3([(0, 0, H_ + 1.45), (Lp - 4.5, 0, H_ + 1.45)], (96, 160, 206), 0.55)
    tank = m_box(Lp - 4.5, -2.0, 0, Lp + 0.5, 2.0, H_ + 1.4, (196, 120, 90), top=(214, 140, 104))
    tank.draw(iso, lw=0.12)
    GEO["aq_front"] = [iso.p(0, T_, 0), iso.p(Lp - 4.5, T_, 0)]
    GEO["aq_tank_face"] = iso.p(Lp + 0.5, 0, 3.0)
    pts = [(0, -T_ - 0.4, H_ + 1.4), (0, T_, 0), (Lp + 0.5, 2.0, 0), (Lp + 0.5, -2.0, 0), (Lp - 4.5, -2.0, H_ + 1.4)]
    pp = [iso.p(*p) for p in pts]
    bb = (min(p[0] for p in pp), min(p[1] for p in pp), max(p[0] for p in pp), max(p[1] for p in pp))
    # 탱크 +X 면과 c3 왼쪽 꼭짓점 거리(평면)
    c3 = find(CH["cells"], "id", "c3")
    Lv = c3["verts_TRBL"][3]
    gap = (Lv[0] - x0s) / C30 / 2.0 + (Lv[1] - y0s)          # 평면 X
    gapY = (2 * (Lv[1] - y0s) - (Lv[0] - x0s) / C30) / 2.0
    REPORT["notes"].append("수도교 분배 탱크 +X 면 ↔ c3 왼쪽 꼭짓점: 평면 %.1fmm(사양 3mm 안)" % (gap - (Lp + 0.5)))
    _ = gapY
    record("S3", s3["name"], "Support", box, bb)


def draw_metella():
    s4 = find(S["supports"], "id", "S4")
    box = s4["box"]
    m = Mesh(None)
    m.extend(m_box(-12, -12, 0, 12, 12, 6, TRAV, top=TRAV_L))
    m.extend(m_cyl(0, 0, 10.5, 6, 22, (228, 216, 192), n=24))
    m.extend(m_cyl(0, 0, 10.65, 18.4, 20.6, (244, 238, 222), n=24))
    for i in range(14):
        a = 2 * math.pi * i / 14
        X, Y = 9.7 * math.cos(a), 9.7 * math.sin(a)
        m.extend(m_box(X - 0.8, Y - 0.8, 22, X + 0.8, Y + 0.8, 24.6, (220, 206, 178)))
    ox, oy, sc, bb = icon_frame(mesh_pts(m), (box[0], box[1], box[2] - 0.6, box[3] - 0.6))
    iso = SIso(P, ox, oy, sc)
    # 진입로: 앞-왼쪽 면에서 ↙ 12mm, 직각으로 꺾어 ↘ 아피아 가도 북서 가장자리까지
    ap_poly, ap_A, ap_B = GEO["appia"]
    nw = ap_A if ap_A[0][1] < ap_B[0][1] else ap_B         # 북서(위) 가장자리
    st = iso.p(0, 12, 0)
    p1 = (st[0] - C30 * 12.0, st[1] + 0.5 * 12.0)
    (ex0, ey0), (ex1, ey1) = nw[0], nw[-1]
    kk = (ey1 - ey0) / (ex1 - ex0)
    t = ((ey0 + kk * (p1[0] - ex0)) - p1[1]) / (0.5 - kk * C30)
    p2 = (p1[0] + C30 * t, p1[1] + 0.5 * t)
    draw_road([st, p1, p2], 4.0, (214, 198, 160), ROAD_EDGE)
    m.draw(iso, lw=0.08)
    for i in range(10):                                 # 프리즈 장식(소머리·꽃줄 점)
        a = math.radians(20 + i * 12)
        cx, cy = iso.p(10.7 * math.cos(a), 10.7 * math.sin(a), 19.5)
        P.dot(cx, cy, 0.45, (176, 160, 130))
    GEO["metella_foot"] = [iso.p(-12, -12), iso.p(12, -12), iso.p(12, 12), iso.p(-12, 12)]
    record("S4", s4["name"], "Support", box, bb)


def hexpts(r, a0=0.0):
    return [(r * math.cos(math.radians(a0 + 60 * k)), r * math.sin(math.radians(a0 + 60 * k))) for k in range(6)]


def draw_portus():
    s5 = find(S["supports"], "id", "S5")
    box = s5["box"]
    nums = [float(v) for v in re.findall(r"\d+(?:\.\d+)?", s5["link"])]
    # link: "육각 내항(육지, 중심 54,380, 반지름 14)·수로·외항(바다, 중심 28,410)·등대(인공섬, 14,424)"
    hx, hy = (nums[0], nums[1]) if len(nums) >= 2 else (54.0, 380.0)
    iso = Iso(P, hx, hy)
    b = GEO["coast_b"]
    Yc = T30 * hx + b - hy                            # 해안선의 평면 Y(육각 중심 기준)
    zs = -GEO["quay_deep"]                            # 바다 면 높이(부두 단면 3mm 아래)
    # 1) 육지: 포장된 둘레와 창고 열(붉은 기와), 부두 테, 내항 물
    pave = hexpts(18.0)
    iso.poly3([(x, y, 0) for x, y in pave], fill=(216, 202, 170), ol=(160, 140, 108), lw=0.2)
    GEO["portus_pave"] = [iso.p(x, y, 0) for x, y in pave]
    iso.poly3([(x, y, 0.3) for x, y in hexpts(14.0)], fill=(206, 194, 168), ol=(150, 132, 104), lw=0.18)
    water = hexpts(12.5)
    iso.poly3([(x, y, 0.3) for x, y in water], fill=HARBOR_C, ol=(96, 136, 166), lw=0.2)
    wh = Mesh(None)
    for k in range(6):
        a0, a1 = math.radians(60 * k), math.radians(60 * (k + 1))
        pieces = [(0.08, 0.92)]
        if k == 1:                                     # +Y 변(해안 쪽): 수로 자리를 비운다
            pieces = [(0.08, 0.44), (0.62, 0.92)]
        for (f0, f1) in pieces:
            q = []
            for (r, f) in ((14.4, f0), (14.4, f1), (17.4, f1), (17.4, f0)):
                pa = (r * math.cos(a0), r * math.sin(a0))
                pb = (r * math.cos(a1), r * math.sin(a1))
                q.append((pa[0] + (pb[0] - pa[0]) * f, pa[1] + (pb[1] - pa[1]) * f))
            wh.extend(m_prism(q, 0.3, 2.4, (226, 204, 172)))
            wh.extend(m_frustum(q, 2.4, 3.7, 0.55, (196, 92, 64)))
    # 2) 수로(육각 내항 +Y 변 → 해안 → 외항)
    C_ = (12.0, 42.0)
    rm = 17.0

    def rimY(X):
        return C_[1] - math.sqrt(max(0.0, rm * rm - (X - C_[0]) ** 2))
    iso.poly3([(0.2, 10.6, 0.3), (2.9, 10.6, 0.3), (2.9, Yc, 0.3), (0.2, Yc, 0.3)], fill=HARBOR_C, ol=(96, 136, 166), lw=0.15)
    iso.poly3([(0.2, Yc, zs), (2.9, Yc, zs), (2.9, rimY(2.9), zs), (0.2, rimY(0.2), zs)], fill=HARBOR_C)
    # 3) 바다: 외항 수면(잔잔) + 방파제 두 팔 + 뿌리
    cx_, cy_ = iso.p(C_[0], C_[1], zs)
    P.ell(cx_, cy_, 1.2247 * 15.6, 0.7071 * 15.6, fill=HARBOR_C)
    moles = Mesh(None)

    def mole_arc(t0, t1, step):
        t = t0
        while (t < t1) if step > 0 else (t > t1):
            ta, tb = math.radians(t), math.radians(t + step)
            q = [(C_[0] + 15.7 * math.cos(ta), C_[1] + 15.7 * math.sin(ta)), (C_[0] + 18.3 * math.cos(ta), C_[1] + 18.3 * math.sin(ta)),
                 (C_[0] + 18.3 * math.cos(tb), C_[1] + 18.3 * math.sin(tb)), (C_[0] + 15.7 * math.cos(tb), C_[1] + 15.7 * math.sin(tb))]
            moles.extend(m_prism(q, zs, zs + 1.3, (206, 196, 174)))
            t += step
    mole_arc(223.0, 100.0, -6.15)
    mole_arc(240.0, 410.0, 6.07)
    tA = math.radians(223.0)
    yA = C_[1] + 17.0 * math.sin(tA)
    moles.extend(m_box(-2.7, Yc - 0.3, zs, 0.0, yA, zs + 1.3, (206, 196, 174)))
    tB = math.radians(240.0)
    yB = C_[1] + 17.0 * math.sin(tB)
    moles.extend(m_box(3.1, Yc - 0.3, zs, 5.7, yB, zs + 1.3, (206, 196, 174)))
    for th in (150.0, 166.0, 182.0, 198.0):            # 위쪽·바다 쪽 방파제 위 창고(붉은 지붕)
        t = math.radians(th)
        Xc, Yc2 = C_[0] + 17.0 * math.cos(t), C_[1] + 17.0 * math.sin(t)
        moles.extend(m_box(Xc - 1.4, Yc2 - 1.4, zs + 1.3, Xc + 1.4, Yc2 + 1.4, zs + 3.2, (230, 210, 180)))
        moles.extend(m_frustum([(Xc - 1.5, Yc2 - 1.5), (Xc + 1.5, Yc2 - 1.5), (Xc + 1.5, Yc2 + 1.5), (Xc - 1.5, Yc2 + 1.5)], zs + 3.2, zs + 4.4, 0.4, (196, 92, 64)))
    for th in range(108, 142, 6):                       # 열주
        t = math.radians(th)
        moles.extend(m_cyl(C_[0] + 17.0 * math.cos(t), C_[1] + 17.0 * math.sin(t), 0.35, zs + 1.3, zs + 4.0, (240, 232, 214), n=6))
    # 등대(외항 입구 인공섬, 4층 + 등롱)
    tL = math.radians(75.0)
    LX, LY = C_[0] + 22.4 * math.cos(tL), C_[1] + 22.4 * math.sin(tL)
    tower = Mesh(None)
    tower.extend(m_mound(LX, LY, zs, 3.6, 1.6, (150, 140, 124), key="등대섬"))
    for (r, z0, z1) in ((2.5, zs + 1.4, zs + 6.6), (1.95, zs + 6.6, zs + 10.6), (1.45, zs + 10.6, zs + 13.8)):
        tower.extend(m_box(LX - r, LY - r, z0, LX + r, LY + r, z1, (236, 226, 204), top=(246, 238, 220)))
    tower.extend(m_cyl(LX, LY, 1.0, zs + 13.8, zs + 16.2, (236, 226, 204), n=8))
    iso_w = Iso(P, hx, hy)
    wh.draw(iso_w, lw=0.08)
    moles.draw(iso_w, lw=0.08)
    tower.draw(iso_w, lw=0.08)
    lx, ly = iso.p(LX, LY, zs + 17.0)
    soft_ell(P, lx, ly, 2.4, 2.0, (255, 214, 110), alpha=150, blur=0.5)
    P.dot(lx, ly, 0.7, (250, 196, 70))
    for (X, Y, Z, sc) in ((-2.0, -3.0, 0.3, 0.8), (6.0, 38.0, zs, 1.0), (20.0, 48.0, zs, 1.0)):    # 작은 범선
        bx_, by_ = iso.p(X, Y, Z)
        P.poly([(bx_ - 3.2 * sc, by_ - 0.6 * sc), (bx_ + 3.2 * sc, by_ + 1.2 * sc), (bx_ + 2.2 * sc, by_ + 2.2 * sc), (bx_ - 2.6 * sc, by_ + 0.9 * sc)], fill=(150, 104, 66))
        P.poly([(bx_ + 0.2 * sc, by_ - 0.2 * sc), (bx_ + 0.2 * sc, by_ - 5.4 * sc), (bx_ + 2.8 * sc, by_ - 1.0 * sc)], fill=(244, 236, 216), outline=(150, 130, 100), lw=0.1)
    pts = [iso.p(x, y, 3.7) for x, y in pave] + [iso.p(x, y, 0) for x, y in pave] + [iso.p(LX, LY, zs + 17.0), iso.p(LX, LY + 3.6, zs)]
    for t in range(0, 360, 15):
        pts.append(iso.p(C_[0] + 18.3 * math.cos(math.radians(t)), C_[1] + 18.3 * math.sin(math.radians(t)), zs))
    bb = (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
    GEO["portus_iso"] = (hx, hy)
    record("S5", s5["name"], "Support", box, bb)


# ───────────────────────── 7 강변 디테일·소품 ─────────────────────────
def draw_dock(d):
    vx, vy = GEO["river_outer"][1]                    # 강 굽이 바깥 꼭짓점
    ox, oy = vx - 1.0 - C30 * 16.0, vy - 8.0
    iso = Iso(P, ox, oy)
    m_box(0, 0, -1.5, 16, 14, 0.8, (186, 176, 156), top=(214, 206, 188)).draw(iso, lw=0.12)
    for X in range(2, 16, 3):
        iso.line3([(X, 0.3, 0.82), (X, 13.7, 0.82)], (196, 186, 166), 0.1)
    stuff = Mesh(None)
    stuff.extend(m_mound(4.0, 10.0, 0.8, 3.0, 2.6, LIME_W, key="부두석회"))
    stuff.extend(m_mound(8.5, 11.0, 0.8, 2.8, 2.4, ASH_R, key="부두화산재"))
    stuff.extend(m_cyl(12.0, 4.0, 0.45, 0.8, 11.5, WOOD, n=6))
    stuff.extend(m_person(7.0, 5.5, 0.8, 6.0, CLOTHS[0], key="부두1"))
    stuff.extend(m_person(10.5, 8.0, 0.8, 6.0, CLOTHS[4], key="부두2"))
    stuff.draw(iso, lw=0.06)
    top = iso.p(12.0, 4.0, 11.5)
    tip = iso.p(20.0, 4.0, 10.5)
    P.line([top, tip], WOOD, 0.45, joint=False)
    P.line([tip, (tip[0], tip[1] + 5.5)], (90, 70, 50), 0.15, joint=False)
    P.rect(tip[0] - 1.2, tip[1] + 5.5, tip[0] + 1.2, tip[1] + 7.3, fill=LIME_W, outline=(150, 140, 120), lw=0.1)
    pts = [iso.p(0, 0, 0.8), iso.p(16, 0, 0.8), iso.p(16, 14, -1.5), iso.p(0, 14, -1.5), top, tip]
    return (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))


def draw_kiln(d):
    m = Mesh(None)
    m.extend(m_cyl(0, 0, 7.4, 0, 10.4, (198, 172, 138), n=14, k=0.8))
    m.extend(m_cyl(0, 0, 6.0, 10.4, 11.4, (176, 150, 118), n=14, top=(70, 52, 40)))
    m.extend(m_box(8.0, -7.0, 0, 12.5, -2.5, 3.0, (232, 228, 214), top=(244, 242, 232)))
    m.extend(m_box(8.5, -2.0, 0, 11.5, 1.0, 2.0, (232, 228, 214), top=(244, 242, 232)))
    m.extend(m_person(-6.0, 9.0, 0, 6.0, CLOTHS[2], key="가마"))
    ox, oy, bb = fit(mesh_pts(m) + [(0, 0, 20)], d["box"])
    iso = Iso(P, ox, oy)
    m.draw(iso, lw=0.08)
    fx, fy = iso.p(5.6, 5.6, 0)
    P.pie(fx, fy - 2.2, 1.9, 2.4, 180, 360, fill=(70, 40, 26))
    P.rect(fx - 1.9, fy - 2.2, fx + 1.9, fy - 0.2, fill=(70, 40, 26))
    P.ell(fx, fy - 1.0, 1.0, 0.8, fill=(236, 120, 50))
    sx, sy = iso.p(0, 0, 12.0)
    for i in range(4):
        soft_ell(P, sx + i * 1.4, sy - i * 2.6, 2.6 - 0.2 * i, 1.8, (236, 232, 226), alpha=40, blur=0.8)
    return bb


def draw_barge(d, axis):
    if axis == "Y":
        hull = m_box(-3.4, -12.0, 0, 3.4, 12.0, 2.2, WOOD, top=WOOD_L)
        cargo = [(-1.5, -6.0), (1.5, -1.0), (-1.2, 4.0), (1.4, 8.0)]
    else:
        hull = m_box(-12.0, -3.4, 0, 12.0, 3.4, 2.2, WOOD, top=WOOD_L)
        cargo = [(-6.0, -1.5), (-1.0, 1.5), (4.0, -1.2), (8.0, 1.4)]
    m = Mesh(None)
    m.extend(hull)
    for i, (X, Y) in enumerate(cargo):
        col = LIME_W if i % 2 == 0 else ASH_R
        m.extend(m_box(X - 1.5, Y - 1.5, 2.2, X + 1.5, Y + 1.5, 4.0, col))
    m.extend(m_person(cargo[-1][0] * 1.2, cargo[-1][1] * 1.2 + (0 if axis == "Y" else 0), 2.2, 5.0, CLOTHS[1], key="바지선" + axis))
    bx0, by0, bx1, by1 = d["box"]
    ox, oy, bb = fit(mesh_pts(m), d["box"])
    if axis == "Y":                                    # 강 중심선에 맞춘다
        segp = RV["segments"][0]["pts"]
    else:
        segp = RV["segments"][1]["pts"]
    (sx0, sy0), (sx1, sy1) = segp
    yc = sy0 + (sy1 - sy0) * (ox - sx0) / (sx1 - sx0)
    oy = yc
    iso = Iso(P, ox, oy)
    w0, w1 = (iso.p(0, -13.5), iso.p(0, 13.5)) if axis == "Y" else (iso.p(-13.5, 0), iso.p(13.5, 0))
    soft_line(P, [w0, w1], (255, 255, 255), alpha=70, w=6.0, blur=1.0)
    m.draw(iso, lw=0.08)
    pts = [iso.p(*p) for p in mesh_pts(m)]
    return (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)), iso


def draw_yard(d):
    m = Mesh(None)
    m.extend(m_mound(4.0, 6.0, 0.05, 7.0, 7.0, LIME_W, n=9, key="마당석회"))
    m.extend(m_mound(17.0, 4.0, 0.05, 7.5, 7.5, ASH_R, n=9, key="마당화산재"))
    m.extend(m_mound(10.0, 18.0, 0.05, 6.5, 5.5, AGG_G, n=9, key="마당골재"))
    m.extend(m_box(21, 14, 1.4, 28, 18.5, 3.6, WOOD, top=WOOD_L))
    m.extend(m_mound(24.5, 16.2, 3.6, 2.6, 1.8, ASH_R, key="마당수레짐"))
    m.extend(m_person(26.0, 22.0, 0, 6.0, CLOTHS[3], key="마당1"))
    pad_ = [(-1, -1, 0), (29, -1, 0), (29, 23, 0), (-1, 23, 0)]
    ox, oy, bb = fit(mesh_pts(m) + pad_, d["box"])
    iso = Iso(P, ox, oy)
    iso.poly3(pad_, fill=(222, 202, 164), ol=(190, 168, 128), lw=0.2)
    for (X, Y) in ((22.5, 18.8), (27.0, 18.8)):
        cx, cy = iso.p(X, Y, 1.4)
        P.ell(cx, cy, 1.3, 1.3, fill=(90, 66, 44))
    m.draw(iso, lw=0.08)
    return bb


def draw_cart(d):
    m = Mesh(None)
    m.extend(m_box(-5.0, -2.6, 1.8, 5.0, 2.6, 4.2, WOOD, top=WOOD_L))
    m.extend(m_mound(0.0, 0.0, 4.2, 3.4, 2.4, LIME_W, key="수레짐"))
    m.extend(m_person(8.0, 0.5, 0, 6.0, CLOTHS[0], key="수레꾼"))
    cxp, cyp, _bb = fit(mesh_pts(m), d["box"], ay="b", pad=0.3)
    iso = Iso(P, cxp, cyp)
    cx, cy = iso.p(0, 2.8, 1.8)
    P.ell(cx, cy, 1.6, 1.6, fill=(90, 66, 44), outline=(60, 44, 30), lw=0.15)
    m.draw(iso, lw=0.08)
    pts = [iso.p(*p) for p in mesh_pts(m)]
    return (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))


def draw_riverside_back():
    det = {d["name"]: d for d in CG["riverside_details"]}
    b1 = find(CG["riverside_details"], "name", "바지선 1")
    bb, _ = draw_barge(b1, "Y")
    REPORT["objects"]["바지선 1"] = {"사양 상자": b1["box"], "그린 외곽": [round(v, 1) for v in bb]}
    k = find(CG["riverside_details"], "name", "석회 가마")
    REPORT["objects"]["석회 가마"] = {"사양 상자": k["box"], "그린 외곽": [round(v, 1) for v in draw_kiln(k)]}
    _ = det


def draw_riverside_front():
    dk = find(CG["riverside_details"], "name", "하역장")
    REPORT["objects"]["하역장"] = {"사양 상자": dk["box"], "그린 외곽": [round(v, 1) for v in draw_dock(dk)]}
    b2 = find(CG["riverside_details"], "name", "바지선 2")
    bb, iso2 = draw_barge(b2, "X")
    GEO["barge2_tip"] = iso2.p(12.0, 0, 2.2)
    REPORT["objects"]["바지선 2"] = {"사양 상자": b2["box"], "그린 외곽": [round(v, 1) for v in bb]}
    yd = find(CG["riverside_details"], "name", "골재")
    REPORT["objects"]["하역 마당"] = {"사양 상자": yd["box"], "그린 외곽": [round(v, 1) for v in draw_yard(yd)]}
    ct = find(CG["riverside_details"], "name", "재료 수레")
    REPORT["objects"]["재료 수레"] = {"사양 상자": ct["box"], "그린 외곽": [round(v, 1) for v in draw_cart(ct)]}


def draw_ash_ship():
    pr = find(S["props"], "name", "화산재 운반선")
    base = [(-17, -3.6), (13, -3.6), (18, 0), (13, 3.6), (-17, 3.6), (-18.5, 0)]
    m = Mesh(None)
    m.extend(m_prism(base, -0.6, 2.8, WOOD, top=WOOD_L))
    for i, X in enumerate((-12, -7, -2, 4, 9)):
        m.extend(m_box(X - 1.8, -2.2, 2.8, X + 1.8, 2.2, 4.6, (150, 126, 104) if i % 2 else (168, 142, 116)))
    m.extend(m_cyl(0.8, 0, 0.45, 2.8, 17.5, (120, 84, 50), n=6))
    sail = [(1.2, -6.2, 7.0), (1.2, 6.2, 7.0), (1.2, 6.6, 16.6), (1.2, -6.6, 16.6)]
    ox, oy, bb = fit(mesh_pts(m) + sail, pr["box"])
    iso = Iso(P, ox, oy)
    soft_line(P, [iso.p(-30, -2), iso.p(-19, 0)], (255, 255, 255), alpha=90, w=2.6, blur=0.8)
    soft_line(P, [iso.p(-30, 2.5), iso.p(-19, 0)], (255, 255, 255), alpha=90, w=2.0, blur=0.8)
    m.draw(iso, lw=0.08)
    iso.poly3(sail, fill=(242, 232, 206), ol=(150, 130, 100), lw=0.15)
    iso.poly3([(1.25, -6.3, 10.8), (1.25, 6.3, 10.8), (1.25, 6.4, 12.6), (1.25, -6.4, 12.6)], fill=(196, 72, 60))
    iso.line3([(1.3, -7.2, 16.8), (1.3, 7.2, 16.8)], (110, 80, 50), 0.35)
    GEO["ship_top"] = iso.p(0.8, 0, 17.5)
    REPORT["objects"]["화산재 운반선"] = {"사양 상자": pr["box"], "그린 외곽": [round(v, 1) for v in bb]}


def draw_trees():
    """빈 땅 소품(밭 가장자리·길가 나무). 라벨 자리와 길을 피한다."""
    spots = [(8, 214, "c"), (16, 222, "o"), (28, 216, "c"), (58, 322, "o"), (70, 330, "c"), (84, 318, "o"), (96, 340, "o"),
             (60, 348, "c"), (92, 398, "o"), (104, 404, "c"), (82, 404, "o"), (250, 501, "o"), (356, 500, "c"), (368, 497, "o"),
             (360, 160, "c")]
    for (x, y, k) in spots:
        if k == "c":
            cypress(P, x, y, 9.0, 2.0)
        else:
            olive(P, x, y, 2.8)


# ───────────────────────── 8 공정 셀 체인 ─────────────────────────
def cell_iso(c):
    T_ = c["verts_TRBL"][0]
    return Iso(P, T_[0], T_[1])


def draw_board(b, step, name, en):
    poly = [tuple(p) for p in b["poly"]]
    h = b["height"]
    is_ul = b["edge"].startswith("뒤-왼쪽")
    core = b["kind"].startswith("CORE")
    fill = (238, 206, 186) if core else ((240, 222, 198) if is_ul else (248, 236, 214))
    P.poly(poly, fill=fill, outline=C_CORE, lw=0.42)
    P.line([poly[3], poly[2]], shade(fill, 0.8), 0.6, joint=False)
    length = abs(poly[1][0] - poly[0][0]) / C30
    M = M_WALL_UP if is_ul else M_WALL_DN
    f = Flat(length, h, C_CORE_T)
    if core:
        f.text(3.0, 15.0, "CORE", fnt("en", 15.0), C_CORE_T)
        f.text(3.0, 22.6, "로마 콘크리트 제작 과정", fnt("b", 4.3), C_CORE_T)
        f.text(3.0, 28.4, "6단계 · 셀 7개(1·1·1·2·1·1)", fnt("m", 2.8), INK_L)
        f.text(3.0, 32.6, "공정 끝에서 콜로세움이 완공된다", fnt("m", 2.8), INK_L)
        need = max(tw("로마 콘크리트 제작 과정", fnt("b", 4.3)), tw("공정 끝에서 콜로세움이 완공된다", fnt("m", 2.8))) + 3.0
    else:
        u0 = 10.2 if is_ul else 2.6
        ub = 4.6 if is_ul else length - 4.6          # 단계 번호 배지: 간판의 바깥 끝(신문 문법)
        f.d.ellipse([(ub - 3.5) * KD + 2, (6.9 - 3.5) * KD + 2, (ub + 3.5) * KD + 2, (6.9 + 3.5) * KD + 2], fill=C_CORE, outline=(255, 255, 255), width=max(1, int(0.3 * KD)))
        f.d.text((ub * KD + 2, (6.9 + 1.75) * KD + 2), str(step), font=fnt("b", 5.0), fill=(255, 255, 255), anchor="ms")
        f.text(u0, 5.9, name, fnt("b", 4.2), C_CORE_T)
        f.text(u0, 10.1, en, fnt("en", 3.5), C_CORE_T)
        f.text(u0, 14.2, STEP_NOTE[step], fnt("m", 2.6), INK_L)
        need = u0 + max(tw(name, fnt("b", 4.2)), tw(STEP_NOTE[step], fnt("m", 2.6)), tw(en, fnt("en", 3.5))) + (0.0 if is_ul else 9.0)
    if need > length:
        REPORT["notes"].append("간판 글 넘침: %s %.1f > %.1f" % (b["kind"], need, length))
    affine_paste(P, f, M, poly[3][0], poly[3][1])


def draw_cell_contents(c, k):
    iso = cell_iso(c)
    s = CH["cell_plan_side"]
    m = Mesh(None)
    hp = 12.0
    if k == 1:
        m.extend(m_mound(13, 28, 0, 6.0, 6.5, LIME_W, key="c1석회"))
        m.extend(m_mound(25, 40, 0, 6.5, 7.0, ASH_R, key="c1화산재"))
        m.extend(m_mound(13, 46, 0, 5.0, 4.6, AGG_G, key="c1골재"))
        m.extend(m_box(49, 2.6, 1.6, 58, 7.6, 4.2, WOOD, top=WOOD_L))
        m.extend(m_mound(53.5, 5.1, 4.2, 2.8, 2.0, LIME_W, key="c1수레짐"))
        m.extend(m_person(36, 54, 0, hp, CLOTHS[0], key="c1a"))
        m.extend(m_person(46, 46, 0, hp, CLOTHS[1], key="c1b"))
    elif k == 2:
        m.extend(m_box(34, 8, 0, 50, 22, 1.6, WOOD, top=WOOD_L))
        m.extend(m_mound(42, 15, 1.6, 5.2, 3.0, (220, 202, 186), key="c2혼합"))
        m.extend(m_person(24, 14, 0, hp, CLOTHS[0], key="c2a"))
        m.extend(m_person(57, 27, 0, hp, CLOTHS[4], key="c2b"))
    elif k == 3:
        m.extend(m_cyl(14, 48, 3.0, 0, 5.5, (150, 108, 70), n=10, top=(96, 150, 196)))
        m.extend(m_cyl(20, 55, 1.6, 0, 3.0, (150, 108, 70), n=8, top=(96, 150, 196)))
        m.extend(m_person(24, 44, 0, hp, CLOTHS[1], key="c3a"))
        m.extend(m_person(44, 54, 0, hp, CLOTHS[2], key="c3b"))
    elif k == 4:
        m.extend(m_person(20, 27, 0, hp, CLOTHS[0], key="c4a"))
        m.extend(m_person(56, 30, 0, hp, CLOTHS[3], key="c4b"))
    elif k == 5:
        m.extend(m_mound(22, 48, 0, 7.5, 6.5, (206, 190, 178), n=9, key="c5반죽"))
        m.extend(m_cyl(42, 57, 1.8, 0, 2.6, WOOD, n=8, top=(206, 190, 178)))
        m.extend(m_person(34, 54, 0, hp, CLOTHS[4], key="c5a"))
    elif k == 6:
        m.extend(m_box(42, 42, 0, 60, 60, 4.6, (170, 124, 80), top=(184, 178, 166)))
        m.extend(m_person(36, 17, 0, hp, CLOTHS[0], key="c6a"))
        m.extend(m_person(52, 30, 0, hp, CLOTHS[2], key="c6b"))
    elif k == 7:
        m.extend(m_box(8, 57, 0, 15, 63.0, 6.0, (176, 170, 156), top=(196, 190, 176)))
        m.extend(m_person(26, 46, 0, hp, CLOTHS[3], key="c7a"))
        m.extend(m_person(44, 56, 0, hp, CLOTHS[1], key="c7b"))
    if k == 4:                                      # 뜨거운 혼합 구덩이(가라앉은 면) + 김(알파 40 이하)
        pit = [(22, 5, 0.04), (44, 5, 0.04), (44, 21, 0.04), (22, 21, 0.04)]
        iso.poly3(pit, fill=(176, 92, 54), ol=(120, 70, 40), lw=0.2)
        iso.poly3([(24, 7, 0.06), (42, 7, 0.06), (42, 19, 0.06), (24, 19, 0.06)], fill=(226, 128, 70))
        for (X, Y) in ((28, 10), (36, 12), (32, 17)):
            cx, cy = iso.p(X, Y, 0)
            P.ell(cx, cy, 1.0, 0.6, fill=(246, 236, 220))
        for i, (X, Y) in enumerate(((30, 12), (36, 15), (26, 17))):
            cx, cy = iso.p(X, Y, 5.0 + 2.0 * i)
            soft_ell(P, cx, cy, 3.6, 2.4, (255, 255, 255), alpha=40, blur=0.9)
    m.draw(iso, lw=0.06)
    if k == 5:                                      # 반죽 속 흰 석회 알갱이
        rng = local_rng("c5알갱이")
        for i in range(10):
            X = 22 + (rng.random() * 2 - 1) * 5.0
            Y = 48 + (rng.random() * 2 - 1) * 5.0
            cx, cy = iso.p(X, Y, 1.0 + rng.random() * 3.6)
            P.ell(cx, cy, 0.5, 0.4, fill=(255, 255, 252))
    if k == 6:                                      # 거푸집 널 줄 + 다짐 막대
        for Z in (1.2, 2.4, 3.6):
            iso.line3([(42, 60, Z), (60, 60, Z)], (130, 92, 58), 0.12)
            iso.line3([(60, 42, Z), (60, 60, Z)], (120, 84, 52), 0.12)
        for (X, Y) in ((36, 17), (52, 30)):
            a = iso.p(X + 1.0, Y + 1.0, 8.0)
            b = iso.p(X + 4.5, Y + 6.5, 0.5)
            P.line([a, b], (110, 80, 50), 0.4, joint=False)
    if k == 7:                                      # 굳은 단면 블록 앞면: 골재·흰 석회 알갱이
        rng = local_rng("c7단면")
        for i in range(8):
            u = 0.7 + rng.random() * 5.6
            v = 0.7 + rng.random() * 4.6
            cx, cy = iso.p(8 + u, 63.0, v)
            P.ell(cx, cy, 0.65, 0.5, fill=(150, 120, 92) if i % 3 else (255, 255, 250))
        GEO["c7_block"] = iso.p(8, 63.0, 6.0)
    if k == 3:
        tf = GEO.get("aq_tank_face")
        if tf:
            bar = iso.p(14, 48, 4.0)
            P.line([tf, (bar[0] - 2.4, bar[1] + 1.0), bar], (90, 152, 204), 0.6, joint=True)
    if k == 1:
        GEO["c1_cart"] = iso.p(53.5, 5.1, 6.0)


def draw_chain():
    cells = CH["cells"]
    bmap = {}
    for b in CH["boards"]:
        bmap.setdefault(b["cell"], []).append(b)
    badges = []
    for k, c in enumerate(cells, start=1):
        T_, R_, B_, L_ = [tuple(v) for v in c["verts_TRBL"]]
        left = c["column"].startswith("왼쪽")
        if left:
            strata_side(P, L_, B_, STRATA7, f=0.86)
        else:
            strata_side(P, B_, R_, STRATA7, f=0.68)
        P.poly([T_, R_, B_, L_], fill=(250, 241, 224))
        for i in (1, 2, 3):
            P.line([lerp(T_, R_, i / 4.0), lerp(L_, B_, i / 4.0)], (238, 224, 200), 0.16, joint=False)
            P.line([lerp(T_, L_, i / 4.0), lerp(R_, B_, i / 4.0)], (238, 224, 200), 0.16, joint=False)
        P.poly([T_, R_, B_, L_], outline=C_CORE, lw=0.55)
        for b in bmap.get(c["id"], []):
            st = c["step"]
            draw_board(b, st, c["step_name"], c["step_en"])
        draw_cell_contents(c, k)
        iso = cell_iso(c)
        s = CH["cell_plan_side"]
        bp = iso.p(4.0, s - 18.0) if left else iso.p(s - 18.0, 4.0)
        badges.append((bp, c))
        if c["id"] == "c2":
            draw_hidden_material_road()
    GEO["badges"] = badges


def draw_hidden_material_road():
    """재료 운반 길이 2단계 간판 뒤로 지나는 구간을 숨은선(점선)으로 보인다"""
    poly, A_, B_ = GEO["material_road"]
    c2 = find(CH["cells"], "id", "c2")
    xT, xR = c2["verts_TRBL"][0][0], c2["verts_TRBL"][1][0]
    for edge in (A_, B_):
        (x0, y0), (x1, y1) = edge
        k = (y1 - y0) / (x1 - x0)
        xa, xb = max(min(x0, x1), xT), min(max(x0, x1), xR)
        if xb > xa:
            P.dashed((xa, y0 + k * (xa - x0)), (xb, y0 + k * (xb - x0)), (120, 96, 66), 0.3, 1.6, 1.2)
    ft = find(LBS["floor_text"], "name", "재료 운반 길")
    a = ft["anchor"]
    iso_text(P, "재료 운반 길", fnt("b", 2.6), (120, 96, 66, 170), M_FLOOR_SE, a[0] - 4.0, a[1] - 1.5)
    REPORT["notes"].append("재료 운반 길 바닥 글 앵커 (%g,%g)와 길 x 223~278 구간이 2단계 간판 뒤에 가림 → 숨은선으로 표시" % (a[0], a[1]))


def draw_badges():
    has_board = {b["cell"] for b in CH["boards"] if not b["kind"].startswith("CORE")}
    for (bp, c) in GEO["badges"]:
        T_, R_, B_, L_ = [tuple(v) for v in c["verts_TRBL"]]
        left = c["column"].startswith("왼쪽")
        area = format(c["projected_box_area"], ",")
        if c["id"] not in has_board:              # 간판 없는 셀(4단계 2셀째): 바닥 배지
            P.ell(bp[0], bp[1], 4.0, 4.0, fill=C_CORE, outline=(255, 255, 255), lw=0.35)
            P.text_c(bp[0], bp[1] + 1.75, str(c["step"]), fnt("b", 5.0), (255, 255, 255))
            P.text(bp[0] + 5.0, bp[1] + 1.0, "4단계 ②(간판 없음)", fnt("b", 2.3), C_CORE_T)
        tag = "%s · %smm²" % (c["id"], area)
        f = fnt("m", 2.3)
        if c["id"] == "c7":                       # 앞-왼쪽 단면 블록을 피해 셀 밖 왼쪽 땅에
            P.text_r(L_[0] - 2.0, L_[1] + 1.0, tag, f, (120, 70, 60))
        elif left:
            P.text(L_[0] + 6.0, L_[1] + 1.0, tag, f, (120, 70, 60))
        else:
            P.text_r(R_[0] - 6.0, R_[1] + 1.0, tag, f, (120, 70, 60))


# ───────────────────────── 9 아레나(콜로세움) ─────────────────────────
RING_O = 0.74 * AR["oct_R_plan"]
RING_I = RING_O - 6.0
H_FRAG, H_BACK, H_UL, H_FRONT = 62.0, 26.0, 10.0, 8.0     # 사양 form: 4층 조각 62 · 뒤-오른쪽 2층 26 · 왼쪽 위 ≤12 · 앞 무너짐


def hwall(th):
    th %= 360.0
    if 270.0 <= th < 360.0:
        if th < 273.0:
            return H_BACK
        if th <= 338.0:
            return H_FRAG
        prof = [(338, 62), (343, 49), (348, 36), (353, 22), (357, 12), (360, 9)]
        for i in range(len(prof) - 1):
            if prof[i][0] <= th < prof[i + 1][0]:
                return prof[i][1]
        return 9.0
    if 225.0 <= th < 270.0:
        return H_BACK
    if 135.0 <= th < 225.0:
        return H_UL - 1.5 * (0.5 + 0.5 * math.sin(math.radians(th * 3.0)))
    return H_FRONT - 1.5 * (0.5 + 0.5 * math.cos(math.radians(th * 4.0)))


def draw_arena():
    cx, cy = AR["center"]
    Tz = AR["base_side_T"]
    octs = [tuple(p) for p in AR["base_oct_screen"]]
    iso = Iso(P, cx, cy)
    tot = sum(t for t, _ in STRATA7)
    lay = [(t * Tz / tot, c) for t, c in STRATA7]
    for k, f in ((7, 0.66), (0, 0.76), (1, 0.88)):
        strata_side(P, octs[k], octs[(k + 1) % 8], lay, f=f)
    a, b = octs[1], octs[2]                          # 앞-왼쪽 변: 콘크리트 기초 고리 절개
    w0, w1 = lerp(a, b, 0.30), lerp(a, b, 0.62)
    P.poly([w0, w1, (w1[0], w1[1] + Tz), (w0[0], w0[1] + Tz)], fill=(132, 108, 80), outline=(70, 50, 32), lw=0.2)
    P.poly([(w0[0], w0[1] + 1.4), (w1[0], w1[1] + 1.4), (w1[0], w1[1] + 6.0), (w0[0], w0[1] + 6.0)], fill=CONC, outline=(104, 98, 88), lw=0.15)
    rng = local_rng("기초단면")
    for i in range(16):
        pp = lerp(w0, w1, rng.random())
        P.ell(pp[0], pp[1] + 2.2 + rng.random() * 3.0, 0.45, 0.38, fill=(246, 244, 236) if i % 2 else (150, 122, 92))
    P.poly(octs, fill=(212, 196, 164), outline=(92, 70, 44), lw=0.5)
    rng = local_rng("광장결")
    for i in range(150):
        X, Y = (rng.random() * 2 - 1) * 84, (rng.random() * 2 - 1) * 84
        if abs(X) + abs(Y) > 112 or X * X + Y * Y < 72 * 72:
            continue
        x0, y0 = iso.p(X, Y)
        dx, dy = (C30, 0.5) if rng.random() < 0.5 else (-C30, 0.5)
        ln = 1.4 + rng.random() * 2.4
        P.line([(x0, y0), (x0 + dx * ln, y0 + dy * ln)], (192, 176, 144), 0.18, joint=False)
    iso.ell(0, 0, 0, RING_O + 3.0, fill=(222, 208, 178), ol=(176, 158, 124), lw=0.2)
    back = Mesh(None)                                 # 광장 뒤쪽 나무
    for i, th in enumerate((198, 214, 236, 256, 290)):
        t = math.radians(th)
        back.extend(m_cypress(80 * math.cos(t), 80 * math.sin(t), 0, 12.0, 1.7, key="아레나뒤%d" % i))
    back.draw(iso, lw=0.06)

    def rp(r, th, z):
        t = math.radians(th)
        return iso.p(r * math.cos(t), r * math.sin(t), z)

    TRV = (210, 188, 146)
    # 뒤쪽 벽 안쪽 면(θ 135→315), 먼 것부터
    faces = []
    th = 135.0
    while th < 315.0 - 1e-6:
        t1 = min(315.0, th + 3.0)
        tm = (th + t1) / 2.0
        h = hwall(tm)
        n = (-math.cos(math.radians(tm)), -math.sin(math.radians(tm)), 0.0)
        faces.append((RING_I * (math.cos(math.radians(tm)) + math.sin(math.radians(tm))), th, t1, h, lit(TRV, n)))
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
    th = 229.0
    while th < 314.0:
        h = hwall(th)
        rows = [(2, 10), (14, 21)] if h < 40 else [(2, 10), (15.5, 23.5), (29, 37), (42.5, 50.5)]
        for (z0, z1) in rows:
            if z1 + 3.0 < h:
                arch_on(RING_I, th, 2.0, z0, z1, (104, 80, 52))
        th += 7.0
    for t0 in range(135, 315, 3):                     # 뒤쪽 벽 윗면
        t1 = t0 + 3
        h0, h1 = hwall(t0 + 0.01), hwall(t1 - 0.01)
        P.poly([rp(RING_I, t0, h0), rp(RING_O, t0, h0), rp(RING_O, t1, h1), rp(RING_I, t1, h1)], fill=(226, 208, 170), outline=(176, 154, 116), lw=0.1)
    # 관람석(카베아): 동심 단
    for i in range(8):
        r = RING_I - 0.5 - i * 2.9
        z = 13.0 - i * 1.5
        ex, ey = iso.p(0, 0, z)
        col = (228, 210, 172) if i % 2 == 0 else (206, 186, 148)
        P.ell(ex, ey, 1.2247 * r, 0.7071 * r, fill=col, outline=(160, 136, 100), lw=0.15)
    for t in range(0, 360, 20):                       # 통로(방사선)
        P.line([rp(RING_I - 1.0, t, 12.6), rp(RING_I - 21.0, t, 2.6)], (166, 142, 106), 0.14, joint=False)
    # 아레나 바닥: 왼쪽 반 하이포게움, 오른쪽 반 복원 나무 바닥
    rf = 38.0
    fx, fy = iso.p(0, 0, 1.5)
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
    hy = [(-26, -14, 6, -11.6), (-26, -5, 6, -2.6), (-26, 4, 6, 6.4), (-26, 13, 6, 15.4),
          (-22, -14, -19.6, 16), (-13, -14, -10.6, 16), (-4, -14, -1.6, 16)]
    for (X0, Y0, X1, Y1) in hy:
        ccx, ccy = (X0 + X1) / 2.0, (Y0 + Y1) / 2.0
        if ccx * ccx + ccy * ccy > 30.0 ** 2 or (ccx - ccy) > 0:
            continue
        isf.box(X0, Y0, 0, X1, Y1, 2.4, ((206, 184, 148), (176, 152, 118), (140, 116, 86)), ol=(90, 70, 46), lw=0.12)
    P.line([(fx, fy - 0.7071 * rf + 0.4), (fx, fy + 0.7071 * rf - 0.4)], (78, 58, 38), 0.3, joint=False)
    # 앞쪽 벽 바깥 면(θ 315→495), 옆에서 앞으로
    faces = []
    th = 315.0
    while th < 495.0 - 1e-6:
        t1 = min(495.0, th + 3.0)
        tm = (th + t1) / 2.0
        h = hwall(tm)
        n = (math.cos(math.radians(tm)), math.sin(math.radians(tm)), 0.0)
        faces.append((RING_O * (math.cos(math.radians(tm)) + math.sin(math.radians(tm))), th, t1, h, lit(TRV, n)))
        th = t1
    for _, t0, t1, h, col in sorted(faces):
        P.poly([rp(RING_O, t0, 0), rp(RING_O, t1, 0), rp(RING_O, t1, h), rp(RING_O, t0, h)], fill=col)
    th = 318.5                                        # 4층 조각 바깥 면 아치(1~3층) + 4층 창
    while th < 357.0:
        h = hwall(th)
        for (z0, z1) in ((2, 10), (15.5, 23.5), (29, 37)):
            if z1 + 3.0 < h:
                arch_on(RING_O, th, 2.2, z0, z1, (100, 74, 46))
        if h > 54:
            p0, p1 = rp(RING_O, th - 1.0, 46.0), rp(RING_O, th + 1.0, 49.0)
            P.rect(min(p0[0], p1[0]), min(p0[1], p1[1]), max(p0[0], p1[0]), max(p0[1], p1[1]), fill=(110, 84, 54))
        th += 7.5
    for zc in (13.0, 26.5, 40.0, 52.5):               # 층 띠(코니스)
        pts = [rp(RING_O, t, zc) for t in range(316, 339)]
        P.line(pts, (236, 222, 190), 0.35)
    for t0 in range(315, 495, 3):                     # 앞쪽 벽 윗면
        t1 = t0 + 3
        h0, h1 = hwall(t0 + 0.01), hwall(t1 - 0.01)
        P.poly([rp(RING_I, t0, h0), rp(RING_O, t0, h0), rp(RING_O, t1, h1), rp(RING_I, t1, h1)], fill=(226, 208, 170), outline=(176, 154, 116), lw=0.1)
    front = Mesh(None)                                # 앞쪽 소품: 올리브·기둥 폐허·사람
    for i, th in enumerate((104, 118)):
        t = math.radians(th)
        front.extend(m_olive(80 * math.cos(t), 80 * math.sin(t), 0, 9.0, 3.0, key="아레나앞%d" % i))
    for i, th in enumerate((38, 50, 62, 74)):
        t = math.radians(th)
        front.extend(m_cyl(78 * math.cos(t), 78 * math.sin(t), 1.0, 0, 6.0 if i % 2 else 9.0, (238, 228, 204), n=8))
    for i, th in enumerate((18, 86, 96)):
        t = math.radians(th)
        front.extend(m_person(76 * math.cos(t), 76 * math.sin(t), 0, 5.0, CLOTHS[i % 5], key="아레나사람%d" % i))
    front.draw(iso, lw=0.06)
    pts = list(octs) + [(o[0], o[1] + Tz) for o in octs[:3]] + [rp(RING_O, t, hwall(t)) for t in range(0, 360, 2)]
    bb = (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
    record("arena", "아레나(콜로세움)", "아레나", AR["box_target"], bb)
    GEO["arena_top"] = lambda x: min((rp(RING_O, t, hwall(t))[1] for t in range(180, 300) if abs(rp(RING_O, t, 0)[0] - x) < 1.6), default=None)


# ───────────────────────── 10 공정 흐름(셀 중심 → 바닥 화살표 → 아레나) ─────────────────────────
def draw_flow():
    cells = CH["cells"]
    pts = []
    for c in cells:
        pts.append(tuple(c["center"]))
        pts.append(tuple(c["floor_arrow_to_next"]["at"]))
    last = pts[-1]
    end = (last[0] + C30 * 40.0, last[1] + 0.5 * 40.0)
    pts.append(end)
    soft_line(P, pts, C_CORE, alpha=150, w=3.4, blur=0.35)
    for c in cells:
        fa = c["floor_arrow_to_next"]
        iso_arrow(P, tuple(fa["at"]), "X" if fa["dir"].startswith("+X") else "Y", C_CORE, s=1.15)
    iso_arrow(P, end, "X", C_CORE, s=1.9)
    tip = isoxy(end[0], end[1], 8.4, 0)
    GEO["flow_end"] = tip
    return pts


# ───────────────────────── 11 확대 창(Detail)·지시선 ─────────────────────────
def draw_magnifier():
    mg = S["detail"]["magnifier"]
    (cx, cy), d = mg["c"], mg["d"]
    r = d / 2.0
    sub = Layer(cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1)
    sub.ell(cx, cy, r, r, fill=(220, 210, 190))
    rng = local_rng("확대창")
    agg_cols = [(168, 136, 104), (186, 104, 78), (150, 146, 138), (112, 94, 84), (196, 160, 118)]
    for i in range(22):
        ax = cx + (rng.random() * 2 - 1) * r * 0.95
        ay = cy + (rng.random() * 2 - 1) * r * 0.95
        rr = 2.6 + rng.random() * 4.6
        nv = 5 + int(rng.random() * 3)
        pts = []
        for j in range(nv):
            t = 2 * math.pi * j / nv + rng.random() * 0.5
            q = rr * (0.7 + rng.random() * 0.45)
            pts.append((ax + q * math.cos(t), ay + q * 0.85 * math.sin(t)))
        sub.poly(pts, fill=agg_cols[i % 5], outline=shade(agg_cols[i % 5], 0.75), lw=0.15)
    clasts = [(-13, -10, 4.4), (9, -15, 3.2), (-4, 11, 5.0), (15, 7, 3.0), (-19, 13, 2.6), (2, -2, 2.4), (20, -6, 2.2)]
    for (dx, dy, rr) in clasts:
        pts = [(cx + dx + rr * (0.86 + 0.14 * h01("알갱이", dx, j)) * math.cos(j * math.pi / 5), cy + dy + rr * 0.9 * math.sin(j * math.pi / 5)) for j in range(10)]
        sub.poly(pts, fill=(252, 252, 246), outline=(196, 190, 178), lw=0.2)
    crack = [(cx - 24, cy - 28), (cx - 15, cy - 13), (cx - 9, cy - 4), (cx - 4, cy + 9), (cx + 3, cy + 18), (cx + 12, cy + 31)]
    sub.line(crack, (66, 54, 46), 0.7)
    sub.line(crack[2:5], (236, 244, 250), 0.45)
    mask = Image.new("L", (sub.w, sub.h), 0)
    ImageDraw.Draw(mask).ellipse([sub.X(cx - r), sub.Y(cy - r), sub.X(cx + r), sub.Y(cy + r)], fill=255)
    sub.img.putalpha(ImageChops.multiply(sub.img.getchannel("A"), mask))
    P.paste(sub)
    P.ell(cx, cy, r, r, outline=C_DETAIL, lw=1.5)
    P.ell(cx, cy, r - 1.0, r - 1.0, outline=(255, 248, 236), lw=0.35)
    for ld in S["detail"]["leaders"]:
        (x0, y0), (x1, y1) = ld["pts"]
        P.line([(x0, y0), (x1, y1)], C_DETAIL, 0.42, joint=False)
        P.dot(x0, y0, 0.55, C_DETAIL)
        P.dot(x1, y1, 0.55, C_DETAIL)
    ax_, ay_ = cx + r * 0.72, cy - r * 0.69
    P.ell(ax_, ay_, 3.0, 3.0, fill=C_DETAIL, outline=(255, 255, 255), lw=0.3)
    P.text_c(ax_, ay_ + 1.3, "A", fnt("b", 3.6), (255, 255, 255))
    bp = GEO.get("c7_block")
    if bp:
        P.ell(bp[0] - 6.0, bp[1] - 2.0, 2.6, 2.6, fill=C_DETAIL, outline=(255, 255, 255), lw=0.3)
        P.text_c(bp[0] - 6.0, bp[1] - 0.9, "A", fnt("b", 3.2), (255, 255, 255))


# ───────────────────────── 12 지도 라벨(등각 벽면·깃대·말풍선) ─────────────────────────
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


def place(box, W, H, M, ul, mode, side, pad=0.6):
    (a, _b), (c, _d) = M
    u0, u1 = min(0.0, ul), max(W, ul)
    xs = [a * u0, a * u1]
    ys = [c * u + v for u in (u0, u1) for v in (0.0, H)]
    ex0, ex1, ey0, ey1 = min(xs), max(xs), min(ys), max(ys)
    bx0, by0, bx1, by1 = box
    ax = (bx1 - pad - ex1) if side == "R" else (bx0 + pad - ex0)
    if mode == "above":
        ay = by1 - pad - ey1
    elif mode == "below":
        ay = by0 + pad - ey0
    else:
        ay = (by0 + by1) / 2.0 - (ey0 + ey1) / 2.0
    over = max(0.0, (ex1 - ex0) - (bx1 - bx0 - 2 * pad), (ey1 - ey0) - (by1 - by0 - 2 * pad))
    return ax, ay, (ax + ex0, ay + ey0, ax + ex1, ay + ey1), over


def lead_mm(slot):
    m = re.search(r"([\d.]+)\s*mm", slot.get("lead", ""))
    return float(m.group(1)) if m else 0.0


LABEL_CONTENT = {
    "콜로세움": dict(t="bracket", en=["COLOSSEUM"], ko="콜로세움", sup="Amphitheatrum Flavium",
                  body=["기초·볼트 = 공정의 완성품", "188×156m · 높이 약 48m"], side="R", mode="above", end="arena"),
    "카라칼라 욕장": dict(t="bracket", en=["CARACALLA"], ko="카라칼라 욕장", sup=None, body=["절개 · 코퍼 돔 단면"], side="R", mode="below", end="bath"),
    "수도교": dict(t="bracket", en=["AQUA CLAUDIA"], ko="수도교", sup="아쿠아 클라우디아", body=["3단계 물 붓기에 민물"], side="R", mode="below", end="aqueduct"),
    "판테온": dict(t="bracket", en=["PANTHEON"], ko="판테온", sup=None, body=["콘크리트 돔 지름 약 43m"], side="R", mode="none", end="rule"),
    "카이킬리아 메텔라 무덤": dict(t="bracket", en=["CAECILIA METELLA"], ko="카이킬리아 메텔라 무덤", sup=None, body=["아피아 가도 길가"], side="L", mode="below", end="metella"),
    "포르투스 항": dict(t="bracket", en=["PORTUS"], ko="포르투스 항", sup=None, body=["육각 내항은 육지", "외항·등대는 바다", "바닷물은 항구 구조물에만"], side="R", mode="above", end="portus"),
    "베수비오": dict(t="flag", en="VESUVIUS", ko="베수비오", side="L", mode="above"),
    "하역장": dict(t="tag", ko="하역장"),
    "석회 가마": dict(t="flag", en="LIME KILN", ko="석회 가마", side="L", mode="above"),
    "테베레 바지선": dict(t="flag", en="BARGE", ko="바지선", side="L", mode="below"),
    "재료 수레": dict(t="flag", en="CART", ko="재료 수레", side="L", mode="above"),
    "화산재 운반선": dict(t="flag", en="ASH SHIP", ko="화산재 운반선", side="L", mode="above"),
    "확대 창": dict(t="flag", en="DETAIL", ko="확대 창", side="L", mode="none"),
}


def end_y(kind, x, fallback):
    try:
        if kind == "arena":
            y = GEO["arena_top"](x)
        elif kind == "bath":
            y = poly_y_at(GEO["bath_plaza"], x, "bottom")
        elif kind == "aqueduct":
            (x0, y0), (x1, y1) = GEO["aq_front"]
            y = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
        elif kind == "metella":
            y = poly_y_at(GEO["metella_foot"], x, "bottom")
        elif kind == "portus":
            y0 = poly_y_at(GEO["portus_pave"], x, "top")
            y = None if y0 is None else y0 - 3.6
        else:
            y = None
    except Exception:
        y = None
    return fallback if y is None else y


def draw_labels():
    plate = (250, 244, 228, 150)
    for slot in LBS["slots"]:
        key = slot["name"].split("(")[0]
        cfg = LABEL_CONTENT.get(key)
        if cfg is None:
            REPORT["notes"].append("라벨 내용 없음: " + slot["name"])
            continue
        box = slot["box"]
        M = M_WALL_UP if slot["wall"].startswith("↗") else M_WALL_DN
        (a, _b), (c, _d) = M
        ink = INK_L
        if cfg["t"] == "tag":
            f_ = fnt("b", 3.0)
            W = tw(cfg["ko"], f_) + 2.4
            H = 4.6
            ax, ay, ext, over = place(box, W, H, M, 0.0, "none", "L", pad=0.2)
            pc = [map_pt(M, ax, ay, u, v) for u, v in ((0, 0), (W, 0), (W, H), (0, H))]
            P.poly(pc, fill=(206, 112, 54), outline=(150, 74, 30), lw=0.25)
            tip0 = map_pt(M, ax, ay, 2.6, 0)
            P.poly([tip0, map_pt(M, ax, ay, 5.4, 0), (tip0[0] + 0.8, tip0[1] - 3.2)], fill=(206, 112, 54))
            iso_text(P, cfg["ko"], f_, (255, 250, 240), M, ax + a * 1.2, ay + c * 1.2 + 3.6)
            LABEL_POLYS.append((key, pc))
            REPORT["labels"][key] = {"종류": "말풍선", "상자": box, "넘침mm": round(over, 1)}
            continue
        scale = 1.0
        for _ in range(3):
            if cfg["t"] == "bracket":
                f, W, H, v_rule = stack_flat(cfg["en"], cfg["ko"], cfg["sup"], cfg["body"], ink, scale)
                ul = -1.8 if cfg["side"] == "L" else W + 1.8
            else:
                f, W, H, v_rule = stack_flat([cfg["en"]], cfg["ko"], None, [], ink, scale)
                ul = -1.4 if cfg["side"] == "L" else W + 1.4
            ax, ay, ext, over = place(box, W, H, M, ul, cfg["mode"], cfg["side"])
            if over <= 0.3 or scale <= 0.72:
                break
            bw, bh = box[2] - box[0] - 1.2, box[3] - box[1] - 1.2
            need_w, need_h = ext[2] - ext[0], ext[3] - ext[1]
            scale = max(0.72, scale * min(bw / need_w, bh / need_h) * 0.995)
        pc = [map_pt(M, ax, ay, u, v) for u, v in ((-1.0, -0.6), (W + 1.0, -0.6), (W + 1.0, H + 0.6), (-1.0, H + 0.6))]
        P.poly(pc, fill=plate)
        affine_paste(P, f, M, ax, ay)
        LABEL_POLYS.append((key, [map_pt(M, ax, ay, u, v) for u, v in ((0, 0), (W, 0), (W, H), (0, H))]))
        info = {"종류": cfg["t"], "방향": "↗" if M is M_WALL_UP else "↘", "상자": box, "배율": round(scale, 2), "넘침mm": round(over, 1)}
        if cfg["t"] == "bracket":
            lx, ly = map_pt(M, ax, ay, ul, v_rule)
            re_ = map_pt(M, ax, ay, W if cfg["side"] == "R" else 0.0, v_rule)
            if cfg["end"] == "rule":
                tgt = GEO["pantheon_plaza"][3][0] + 3.0
                ext_u = max(6.0, min(18.0, (tgt - re_[0]) / a))
                e = map_pt(M, ax, ay, W + ext_u, v_rule)
                P.line([re_, e], ink, LEAD_LW, joint=False)
                P.dot(e[0], e[1], DOT_R, ink)
                info["지시선"] = "규선 연장 %.1fmm" % ext_u
            else:
                P.line([re_, (lx, ly)], ink, 0.25, joint=False)
                fb = ly + 12.0 if cfg["mode"] == "above" else ly - 12.0
                yt = end_y(cfg["end"], lx, fb)
                P.line([(lx, ly), (lx, yt)], ink, LEAD_LW, joint=False)
                P.dot(lx, yt, DOT_R, ink)
                info["지시선"] = "수직 %.1fmm" % abs(yt - ly)
        else:
            pole = lead_mm(slot)
            if pole > 0:
                top = map_pt(M, ax, ay, ul, 0.0)
                bot = map_pt(M, ax, ay, ul, H)
                if cfg["mode"] == "below":
                    yt = top[1] - pole
                    P.line([bot, (top[0], yt)], ink, LEAD_LW, joint=False)
                else:
                    yt = bot[1] + pole
                    P.line([top, (bot[0], yt)], ink, LEAD_LW, joint=False)
                P.dot(top[0], yt, DOT_R, ink)
                info["깃대"] = "%.0fmm" % pole
        REPORT["labels"][key] = info


# ───────────────────────── 13 틀: 타이틀·패널·푸터·눈금 ─────────────────────────
def draw_title():
    x0, y0, x1, y1 = FR["title"]["rect"]
    cx = (x0 + x1) / 2.0
    red = (200, 34, 54)
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
    P.text_c(cx, y0 + 37.4, "CITY INFOGRAPHIC · ROMA", fnt("en", 5.0), red)
    P.poly([(x0 + 2, y0 + 30.5), (cx, y0 + 1.0), (x1 - 2, y0 + 30.5)], fill=(252, 242, 234), outline=red, lw=0.6)
    P.poly([(x0 + 16, y0 + 28.0), (cx, y0 + 6.2), (x1 - 16, y0 + 28.0)], outline=(226, 150, 150), lw=0.3)
    P.ell(cx, y0 + 18.0, 3.2, 3.2, outline=red, lw=0.45)
    P.text_c(cx, y0 + 25.2, "타이틀 록업 · 신전 페디먼트 정면 입면 · %.0f×%.0fmm(폭 %.1f%%)" % (x1 - x0, y1 - y0, FR["title"]["width_pct"]), fnt("m", 2.2), (150, 60, 60))
    P.rect(cx - 52, y0 + 44.0, cx + 52, y0 + 66.0, fill=(253, 247, 240), outline=red, lw=0.6)
    P.text_c(cx, y0 + 57.0, "ROMAN CONCRETE", fnt("en", 13.0), red)
    P.text_c(cx, y0 + 63.4, "로마 콘크리트 — 도시 인포그래픽 '로마 편'", fnt("b", 3.5), red)
    P.rect(cx - 60, y0 + 67.6, cx + 60, y0 + 73.4, fill=(250, 230, 228), outline=red, lw=0.4)
    P.text_c(cx, y0 + 71.9, "갈라져도 물을 만나 스스로 메우는 콘크리트", fnt("b", 3.0), red)


def panel_header(x0, y0, en, ko, col):
    f_en = fnt("en", 7.4 / 0.71)
    P.text(x0 + 2.0, y0 + 2.6 + 7.4, en, f_en, col)
    w = tw(en, f_en)
    P.text(x0 + 2.0 + w + 2.0, y0 + 2.6 + 3.2, ko, fnt("b", 3.8), col)
    return y0 + 2.6 + 7.4


def panel_tag(x1, y1, text, col):
    P.text_r(x1 - 1.6, y1 - 1.6, text, fnt("b", 2.2), col)


def draw_panels():
    for pn in FR["panels"]:
        x0, y0, x1, y1 = pn["rect"]
        col = TIER_TXT[pn["tier"]]
        plate = (252, 248, 238, 215) if pn["id"] == "R" else (252, 247, 236, 120)
        rrect(P, x0, y0, x1, y1, 1.0, fill=plate)
        P.dashed_rect(x0, y0, x1, y1, TIER_COL[pn["tier"]], 0.35, 2.2, 1.3)
        tag = "%s · %s · %.0f×%.0f · %smm²" % (pn["id"], pn["tier"], x1 - x0, y1 - y0, format(int(pn["box_area"]), ","))
        if pn["id"] == "L":
            yb = panel_header(x0, y0, "DEFINITION", "로마 콘크리트란?", col)
            lines = ["정의 1~2줄 + 재료 비율·순서 1~2줄 요약", "(자세한 순서는 CORE 공정이 맡는다)", "상자·배경판 없이 바탕 위에 조판"]
            for i, t in enumerate(lines):
                P.text(x0 + 2.4, yb + 7.0 + i * 4.6, t, fnt("m", 2.8), INK_L)
            chips = [("생석회", LIME_W), ("화산재", ASH_R), ("골재", AGG_G), ("물", (120, 178, 214))]
            xx = x0 + 2.4
            for name, cc in chips:
                w = tw(name, fnt("b", 2.6)) + 6.4
                rrect(P, xx, y1 - 13.4, xx + w, y1 - 8.2, 2.4, fill=(255, 252, 244, 255), outline=(150, 136, 112), lw=0.25)
                P.ell(xx + 2.6, y1 - 10.8, 1.5, 1.5, fill=cc, outline=(120, 104, 84), lw=0.15)
                P.text(xx + 4.8, y1 - 9.7, name, fnt("b", 2.6), INK_L)
                xx += w + 1.6
            panel_tag(x1, y1, tag, col)
        elif pn["id"] == "R":
            panel_header(x0, y0, "WHERE", "위치도", col)
            draw_location_map(x0, y0, x1, y1, col)
            panel_tag(x1, y1, tag, col)
        elif pn["id"] == "B1":
            yb = panel_header(x0, y0, "LIME CLASTS", "석회 알갱이·자가 치유", col)
            caps = ["석회 알갱이", "균열 + 빗물", "칼슘이 녹아 나옴", "방해석 봉합"]
            for i, cap in enumerate(caps):
                bx = x0 + 4.0 + i * 31.5
                by = yb + 3.0
                P.rect(bx, by, bx + 23, by + 23, fill=(244, 234, 214), outline=(196, 120, 50), lw=0.35)
                for j in range(9):
                    P.dot(bx + 3 + (j * 7.3) % 18, by + 4 + (j * 5.1) % 16, 0.6, (150, 130, 106))
                if i == 0:
                    P.ell(bx + 11.5, by + 11.5, 4.2, 3.4, fill=(255, 255, 250), outline=(196, 186, 170), lw=0.2)
                if i >= 1:
                    P.line([(bx + 6, by + 1), (bx + 10, by + 8), (bx + 9, by + 14), (bx + 13, by + 22)], (80, 64, 50), 0.45)
                if i == 2:
                    for (dx, dy) in ((14, 5), (16, 10), (6, 16)):
                        P.ell(bx + dx, by + dy, 0.9, 1.2, fill=(90, 150, 206))
                if i == 3:
                    P.line([(bx + 10, by + 8), (bx + 9, by + 14)], (250, 250, 250), 0.9, joint=False)
                P.text_c(bx + 11.5, by + 27.6, cap, fnt("b", 2.5), INK_L)
                if i < 3:
                    P.poly([(bx + 24.6, by + 10.5), (bx + 28.6, by + 11.5), (bx + 24.6, by + 12.5)], fill=C_DETAIL)
            panel_tag(x1, y1, tag + " · 바다 위 고요한 영역", col)
        elif pn["id"] == "B2":
            yb = panel_header(x0, y0, "HISTORY", "연대기·근거", col)
            ly = yb + 14.0
            P.line([(x0 + 6, ly), (x1 - 8, ly)], col, 0.5, joint=False)
            P.poly([(x1 - 8, ly - 1.4), (x1 - 4.6, ly), (x1 - 8, ly + 1.4)], fill=col)
            for i, f_ in enumerate((0.06, 0.30, 0.66, 0.90)):
                xx = x0 + 6 + (x1 - x0 - 14) * f_
                P.ell(xx, ly, 1.4, 1.4, fill=col)
                P.text_c(xx, ly - 3.0 if i % 2 == 0 else ly + 5.2, "사건 %d" % (i + 1), fnt("b", 2.4), INK_L)
            P.text(x0 + 2.4, ly + 13.0, "연표: 내용 비례 간격 · 주요 사건만 배지", fnt("m", 2.6), INK_L)
            P.text(x0 + 2.4, ly + 17.4, "각 사건에 근거(출처) 한 줄", fnt("m", 2.6), INK_L)
            panel_tag(x1, y1, tag, col)
        elif pn["id"] == "B3":
            yb = panel_header(x0, y0, "100 VS 2000", "100년 vs 2000년", col)
            base = y1 - 9.0
            P.line([(x0 + 4, base), (x1 - 4, base)], INK_L, 0.3, joint=False)
            P.rect(x0 + 12, base - 4.0, x0 + 24, base, fill=(150, 146, 140))
            P.rect(x0 + 44, base - 30.0, x0 + 56, base, fill=col)
            P.text_c(x0 + 18, base - 5.2, "100년", fnt("b", 2.6), INK_L)
            P.text_c(x0 + 50, base - 31.2, "2000년", fnt("b", 2.6), INK_L)
            P.text_c(x0 + 18, base + 3.4, "현대 콘크리트", fnt("m", 2.3), INK_L)
            P.text_c(x0 + 50, base + 3.4, "로마 콘크리트", fnt("m", 2.3), INK_L)
            P.text(x0 + 62, yb + 6.0, "수명(사용 기록)", fnt("m", 2.4), INK_L)
            P.text(x0 + 62, yb + 9.6, "비교 — 강도", fnt("m", 2.4), INK_L)
            P.text(x0 + 62, yb + 13.2, "비교가 아님", fnt("m", 2.4), INK_L)
            panel_tag(x1, y1, tag, col)


def draw_location_map(x0, y0, x1, y1, col):
    mx0, my0, k = x0 + 4.0, y0 + 15.0, 34.0
    kx = k * 0.755

    def g(lon, lat):
        return (mx0 + (lon - 12.1) * kx, my0 + (42.1 - lat) * k)
    coast = [(11.95, 42.3), (12.26, 41.78), (12.45, 41.62), (12.63, 41.45), (13.03, 41.33), (13.25, 41.28), (13.57, 41.21),
             (13.89, 41.12), (14.03, 40.92), (14.05, 40.85), (14.12, 40.82), (14.25, 40.84), (14.45, 40.75), (14.37, 40.63), (14.33, 40.55)]
    cp = [g(*p) for p in coast]
    cp = [(max(x0 + 0.8, x), min(y1 - 0.8, max(y0 + 14.0, y))) for x, y in cp]
    sea = cp + [(cp[-1][0], y1 - 0.8), (x0 + 0.8, y1 - 0.8), (x0 + 0.8, cp[0][1])]
    P.poly(sea, fill=(196, 220, 234))
    P.line(cp, (110, 150, 180), 0.35)
    tib = [g(12.53, 42.12), g(12.49, 42.0), g(12.47, 41.93), g(12.48, 41.88), g(12.42, 41.83), g(12.33, 41.79), g(12.27, 41.76)]
    P.line(tib, (96, 150, 200), 0.5)
    appia = [g(12.50, 41.88), g(12.64, 41.74), g(13.25, 41.29), g(14.25, 41.08)]
    for i in range(len(appia) - 1):
        P.dashed(appia[i], appia[i + 1], (150, 120, 84), 0.35, 1.4, 1.0)
    pins = [("로마", 12.50, 41.90, (2.4, 0.9), "l"), ("알바노 구릉", 12.70, 41.75, (2.2, 2.4), "l"),
            ("포추올리", 14.12, 40.82, (-2.0, -1.2), "r"), ("베수비오·폼페이", 14.43, 40.82, (2.2, -1.4), "l")]
    for (name, lon, lat, off, al) in pins:
        x, y = g(lon, lat)
        P.ell(x, y, 1.0, 1.0, fill=C_CORE if name == "로마" else col, outline=(255, 255, 255), lw=0.2)
        if al == "l":
            P.text(x + off[0], y + off[1], name, fnt("b", 2.4), INK_L)
        else:
            P.text_r(x + off[0], y + off[1], name, fnt("b", 2.4), INK_L)
    px, py = g(12.27, 41.77)
    P.ell(px, py, 1.0, 1.0, fill=col, outline=(255, 255, 255), lw=0.2)
    P.text(x0 + 1.6, py + 6.0, "포르투스·오스티아", fnt("b", 2.4), INK_L)
    P.text(x0 + 1.6, py + 9.2, "(테베레 하구)", fnt("m", 2.3), INK_L)
    P.line([(px, py + 0.9), (px - 1.0, py + 3.6)], INK_L, 0.18, joint=False)
    zones = [("①", 12.50, 41.90, (-1.0, -3.0)), ("②", 12.50, 41.90, (2.6, -3.0)), ("③", 12.64, 41.74, (-4.0, 1.6)),
             ("④", 12.27, 41.77, (-3.6, -1.6)), ("⑤", 14.43, 40.82, (-0.8, 3.6))]
    for (z, lon, lat, off) in zones:
        x, y = g(lon, lat)
        P.text_c(x + off[0], y + off[1], z, fnt("b", 2.6), C_CORE_T)
    lx = x1 - 22.0
    for i, t in enumerate(["지도에 담은 구역", "① 도심 코어", "② 시내", "③ 남동 교외", "④ 서남서 해안", "⑤ 베수비오"]):
        P.text(lx, y0 + 21.0 + i * 3.6, t, fnt("b" if i == 0 else "m", 2.2), INK_L if i else col)
    nx, ny = x1 - 5.0, y0 + 6.0
    P.poly([(nx, ny - 3.2), (nx + 1.6, ny + 1.6), (nx, ny + 0.6), (nx - 1.6, ny + 1.6)], fill=col)
    P.text_c(nx, ny + 5.0, "N", fnt("b", 2.6), col)
    P.text(x0 + 30.0, y1 - 5.6, "북쪽 위 · 방위표는 여기만 · 하구–포르투스 관계", fnt("m", 2.1), col)


def draw_footer():
    x0, y0, x1, y1 = FR["footer"]["rect"]
    P.dashed_rect(x0, y0, x1, y1, (150, 136, 112), 0.3, 2.0, 1.2)
    P.text(x0 + 2.0, y0 + 5.0, "최종 배치 다이어그램", fnt("b", 3.4), C_CORE_T)
    w = tw("최종 배치 다이어그램", fnt("b", 3.4))
    P.text(x0 + 4.0 + w, y0 + 5.0, "로마 콘크리트 A2 세로 포스터(420×594mm) · 도시 인포그래픽 '로마 편' · 사양 %s · 지도 무대 y %g~%g(높이 %.1f%%) · 패널 %d개(포스터의 %.1f%%) · 1mm = 3px · 좌표 A2 mm" %
           (S["meta"]["version"], FR["stage"]["rect"][1], FR["stage"]["rect"][3], 100.0 * (FR["stage"]["rect"][3] - FR["stage"]["rect"][1]) / PH, len(FR["panels"]), FR["panel_area_pct_poster"]),
           fnt("m", 2.6), INK_L)
    items = [("Core 제작 과정", C_CORE), ("아레나 = 공정의 완성품", (150, 112, 70)), ("Basic", C_BASIC), ("Detail", C_DETAIL),
             ("Support", C_SUP), ("Support-2", C_SUP2), ("코어 군 영역", CORE_TINT), ("강·바다", RIV_C), ("길", ROAD_C), ("밭·포도밭", FIELD_G)]
    xx = x0 + 2.0
    yy = y0 + 10.6
    for name, cc in items:
        P.rect(xx, yy - 2.5, xx + 2.8, yy + 0.3, fill=cc, outline=(90, 80, 64), lw=0.15)
        P.text(xx + 3.6, yy, name, fnt("b", 2.4), INK_L)
        xx += 3.6 + tw(name, fnt("b", 2.4)) + 3.4
    P.text(xx + 1.0, yy, "모서리 표시 = 투영 상자 · 등각 글자 = 지도 라벨 자리 · 정면 글자 = 다이어그램 주석 · 점선 길 = 가린 구간", fnt("m", 2.3), (110, 100, 86))
    st = HC["step_boxes"]
    st_areas = [v["area"] for k_, v in st.items() if not k_.startswith("4단계")]
    bdv = HC["basic_detail_boxes"].values()
    sm = HC["support_max"][1]
    smin = HC["support_min"][1]
    line3 = ("위계(투영 상자 mm²): 아레나 %s > 단계 상자 %s~%s(4단계 2셀 %s) > Basic·Detail %s~%s > Support %s~%s(상한 %s) > Support-2 %s" %
             (format(HC["arena"], ","), format(min(st_areas), ","), format(max(st_areas), ","), format(st["4단계 뜨거운 혼합"]["area"], ","),
              format(min(bdv), ","), format(max(bdv), ","), format(smin, ","), format(sm, ","), format(HC["support_cap(=BD_min/1.1)"], ","), format(HC["support2"], ",")))
    P.text(x0 + 2.0, y1 + 5.2, line3, fnt("m", 2.4), INK_L)
    line4 = ("코어 군(지도 무대 대비) 실루엣 %.1f%% · 껍질 %.1f%% · 상자 %.1f%%(%.0f×%.0fmm) · 세로/가로 %.2f · 무게중심 (%.3f, %.3f) · 라벨 %d(벽면·깃대 %d + 바닥 %d) · 허용하지 않은 겹침 %d건" %
             (MM["silhouette_pct_stage"], MM["hull_pct_stage"], MM["bbox_pct_stage"], MM["bbox_wh"][0], MM["bbox_wh"][1], MM["aspect_h_over_w"],
              MM["centroid_norm"][0], MM["centroid_norm"][1], LBS["count"]["total"], LBS["count"]["wall_or_flag"], LBS["count"]["floor_text"], len(S["overlaps_not_allowed"])))
    P.text(x0 + 2.0, y1 + 9.9, line4, fnt("m", 2.4), INK_L)


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
    sx0, sy0, sx1, sy1 = FR["stage"]["rect"]
    for y, lab, dy in ((sy0, "y %g" % sy0, -1.4), (sy1, "y %g" % sy1, 3.4)):
        P.line([(0, y), (5.0, y)], C_CORE_T, 0.35, joint=False)
        P.text(1.0, y + dy, lab, fnt("b", 2.1), C_CORE_T)


# ───────────────────────── 14 다이어그램 주석(정면 글자) ─────────────────────────
def draw_annotations():
    sup_txt = TIER_TXT["Support"]
    tags = {"S1": "l_top_right", "S2": "top_right", "S3": "top_right", "S4": "top_left", "S5": "bottom_right"}
    for s in S["supports"]:
        b = s["box"]
        corner_marks(P, b, C_SUP)
        area = (b[2] - b[0]) * (b[3] - b[1])
        t = "%s · %.0f×%.0f · %s" % (s["id"], b[2] - b[0], b[3] - b[1], format(int(round(area)), ","))
        if s["id"] == HC["support_max"][0][:0] or s["name"] == HC["support_max"][0]:
            t += "(최대)"
        pos = tags.get(s["id"], "top_right")
        if pos in ("top_right", "l_top_right"):
            pill(P, b[2] - 0.8, b[1] + 0.6, t, sup_txt, anchor="r")
        elif pos == "top_left":
            pill(P, b[0] + 0.8, b[1] + 0.6, t, sup_txt)
        else:
            pill(P, b[2] - 0.8, b[3] - 4.2, t, sup_txt, anchor="r")
    s6 = S["support2"][0]
    b = s6["box"]
    corner_marks(P, b, C_SUP2)
    pill(P, b[0] + 0.6, b[1] + 0.6, "S6 · %.0f×%.0f" % (b[2] - b[0], b[3] - b[1]), TIER_TXT["Support-2"], em=2.2)
    # 확대 창(Detail)
    mg = S["detail"]["magnifier"]
    pill(P, mg["c"][0] - 2.0, mg["c"][1] + mg["d"] / 2.0 + 1.4, "Detail · Ø%.0f · %smm²(Basic·Detail 최소)" % (mg["d"], format(HC["basic_detail_boxes"]["확대 창"], ",")), TIER_TXT["Detail"], em=2.2, anchor="r")
    # 아레나
    corner_marks(P, AR["box_target"], (150, 112, 70), arm=4.0, lw=0.4)
    bx = AR["box_target"]
    ax_ = (bx[0] + bx[2]) / 2.0 + 30.0
    P.text_c(ax_, bx[3] + 7.4, "콜로세움(아레나) = 공정의 완성품 · 가장 큰 단일 오브젝트", fnt("b", 2.9), (110, 70, 34))
    P.text_c(ax_, bx[3] + 11.6, "투영 상자 %.1f×%.1fmm · %smm²(최대 셀의 %.1f배)" % (AR["box_wh"][0], AR["box_wh"][1], format(AR["box_area"], ","), AR["box_area"] / HC["max_single_cell"]),
             fnt("m", 2.5), (110, 70, 34))
    # 코어 군
    cx0, cy0 = 280.5, 243.0
    P.text(cx0, cy0, "CORE GROUP", fnt("en", 4.2), C_CORE_T)
    P.text(cx0, cy0 + 4.3, "코어 군(연한 영역)", fnt("b", 2.6), C_CORE_T)
    P.text(cx0, cy0 + 8.0, "실루엣 %.1f%%" % MM["silhouette_pct_stage"], fnt("m", 2.3), C_CORE_T)
    P.text(cx0, cy0 + 11.2, "껍질 %.1f%% · 상자 %.1f%%" % (MM["hull_pct_stage"], MM["bbox_pct_stage"]), fnt("m", 2.3), C_CORE_T)
    # P5 접촉: CORE 간판 위 끝 = 타이틀 아래 변
    cb = find(CH["boards"], "kind", "CORE")
    tpt = min(cb["poly"], key=lambda p: p[1])
    P.ell(tpt[0], tpt[1], 1.4, 1.4, outline=C_CORE, lw=0.35)
    pill(P, tpt[0] + 3.0, tpt[1] + 2.6, "CORE 간판 위 끝 y %.2f = 타이틀 아래 변(접촉)" % tpt[1], C_CORE_T, em=2.2)
    # P6 맞닿음
    pill(P, 168.4, 384.8, "0mm 맞닿음", C_CORE_T, em=2.2)
    c6 = find(CH["cells"], "id", "c6")
    bv = c6["verts_TRBL"][2]
    ov = AR["base_oct_screen"][4]
    P.ell((bv[0] + ov[0]) / 2.0, (bv[1] + ov[1]) / 2.0, 2.4, 2.4, outline=C_CORE, lw=0.3)
    pill(P, 229.0, 351.7, "%.1fmm 닿음" % math.hypot(bv[0] - ov[0], bv[1] - ov[1]), C_CORE_T, em=2.0)
    fe = GEO.get("flow_end")
    if fe:
        pill(P, fe[0] + 1.6, fe[1] - 2.4, "공정 흐름 → 콜로세움 완공", C_CORE_T, em=2.4)
    # 이름 라벨이 없는 요소(다이어그램 주석)
    pill(P, 324.0, 293.2, "골재·화산재 하역 마당", (110, 90, 70), em=2.0, bold=False)
    b1 = find(CG["riverside_details"], "name", "바지선 1")["box"]
    pill(P, b1[0] - 1.0, b1[3] + 1.4, "바지선 1", (60, 100, 140), em=2.0, bold=False)
    fb = GEO.get("fields_box")
    if fb:
        pill(P, fb[0] + 4.0, fb[3] - 3.0, "들(올리브·밀·포도밭)", (90, 110, 60), em=2.0, bold=False)


# ───────────────────────── 15 실행 ─────────────────────────
def main():
    draw_ground()
    draw_fields()
    draw_core_tint()
    draw_sea()
    draw_river()
    # 판테온 광장·욕장 광장 좌표를 길보다 먼저 알아야 하므로 기하만 미리 잡는다
    s1 = find(S["supports"], "id", "S1")
    ox, oy, sc, _ = icon_frame(BATH_KEY, s1["box"])
    si = SIso(P, ox, oy, sc)
    GEO["bath_plaza"] = [si.p(0, 0), si.p(40, 0), si.p(40, 40, -1.2), si.p(0, 40, -1.2)]
    s2 = find(S["supports"], "id", "S2")
    ox2, oy2, sc2, _ = icon_frame(PANTHEON_KEY, s2["box"])
    si2 = SIso(P, ox2, oy2, sc2)
    GEO["pantheon_plaza"] = [si2.p(-19, -19), si2.p(19, -19), si2.p(19, 19), si2.p(-19, 19)]
    draw_roads()
    draw_floor_texts()
    draw_trees()
    draw_vesuvius()
    draw_pantheon()
    draw_bath()
    draw_riverside_back()
    draw_aqueduct()
    draw_chain()
    draw_riverside_front()
    draw_metella()
    draw_portus()
    draw_ash_ship()
    draw_arena()
    draw_flow()
    draw_badges()
    draw_magnifier()
    draw_labels()
    draw_title()
    draw_panels()
    draw_footer()
    draw_ticks()
    draw_annotations()
    # 라벨끼리 겹침(화면 다각형 외곽 상자 근사)
    over = []
    for i in range(len(LABEL_POLYS)):
        for j in range(i + 1, len(LABEL_POLYS)):
            a, pa = LABEL_POLYS[i]
            b, pb = LABEL_POLYS[j]
            ax0, ax1 = min(p[0] for p in pa), max(p[0] for p in pa)
            ay0, ay1 = min(p[1] for p in pa), max(p[1] for p in pa)
            bx0, bx1 = min(p[0] for p in pb), max(p[0] for p in pb)
            by0, by1 = min(p[1] for p in pb), max(p[1] for p in pb)
            if min(ax1, bx1) - max(ax0, bx0) > 0.5 and min(ay1, by1) - max(ay0, by0) > 0.5:
                over.append((a, b))
    REPORT["label_overlaps"] = over
    out = P.img.resize((PW * OUT_PX_PER_MM, PH * OUT_PX_PER_MM), Image.LANCZOS).convert("RGB")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out.save(OUT, optimize=True)
    REPORT["output"] = OUT
    REPORT["size_px"] = out.size
    REPORT["seconds"] = round(time.time() - T_START, 1)
    print(json.dumps(REPORT, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
