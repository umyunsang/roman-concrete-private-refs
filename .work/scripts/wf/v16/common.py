# -*- coding: utf-8 -*-
# 로마 콘크리트 A2 와이어프레임 — 공용 도구(글꼴·팔레트·레이어·등각 글자·라벨 규격·소품·받침)
# 담당 패키지: global · 이 파일은 담당 워커만 고친다(공용 도구는 common.py, 조립은 main.py).
# - 원본: wireframe_v16.py(v15 → v16 비평 반영본)를 모듈로 나눈 것. 최종 모델 수준은 LocalBanana 디오라마, 이 도면은 배치 도식이다.
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
import math, os, sys

OUT_DIR = "out"
K = 4                      # 최종 해상도 1mm = 4px
SS = 2                     # 내부 슈퍼샘플 배수
KD = K * SS                # 그리기 해상도(px/mm)
PW, PH = 420, 594          # A2(mm)
SQ3 = math.sqrt(3)
C30 = math.cos(math.radians(30))     # 0.866
T30 = math.tan(math.radians(30))     # 0.577
MAP_Y0, MAP_Y1 = 92, 505             # 베이징 M 구획

KO_PATH = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
EN_PATH = "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf"
_KO_IDX = {"r": 0, "m": 2, "s": 4, "b": 6}
_FC = {}


def fnt(kind, em):
    """kind: r/m/s/b(국문 굵기), en(영문 압축 볼드). em은 mm."""
    px = max(6, int(round(em * KD)))
    key = (kind, px)
    if key not in _FC:
        if kind == "en":
            _FC[key] = ImageFont.truetype(EN_PATH, px)
        else:
            _FC[key] = ImageFont.truetype(KO_PATH, px, index=_KO_IDX[kind])
    return _FC[key]


def tw(s, font):
    """글줄 폭(mm)"""
    return font.getlength(s) / KD


# ───────────────────────── 팔레트 ─────────────────────────
BG = (231, 208, 160)
SAND2 = (222, 198, 150)
C_CORE = (200, 34, 54)
C_CORE_T = (170, 24, 44)
C_BASIC = (70, 60, 150)
C_DETAIL = (222, 112, 16)
C_DETAIL_T = (150, 70, 0)
C_SUP = (46, 147, 60)
C_SUP_T = (22, 100, 44)
C_SUP2 = (96, 126, 118)
C_ARENA_T = (92, 54, 28)
C_INK = (40, 30, 22)
C_GREY = (120, 112, 100)
SOIL = (126, 98, 62)
SOIL_D = (100, 76, 48)
GRASS = (94, 126, 66)
SEA = (140, 174, 200)
SEA_D = (104, 142, 172)
RIVER = (112, 170, 210)
RIVER_T = (66, 112, 156)
ROAD = (184, 164, 132)
ROAD_E = (146, 126, 96)
STONE = (232, 220, 196)
STONE_D = (206, 188, 156)
STONE_DD = (178, 158, 126)
EDGE = (110, 86, 56)
TIER_COL = {"Core": C_CORE, "Basic": C_BASIC, "Detail": C_DETAIL, "Support": C_SUP, "Support-2": C_SUP2}
TIER_TXT = {"Core": C_CORE_T, "Basic": C_BASIC, "Detail": C_DETAIL_T, "Support": C_SUP_T, "Support-2": (70, 92, 86)}


def mix(c, bgc=BG, a=0.5):
    return tuple(int(round(c[i] * (1 - a) + bgc[i] * a)) for i in range(3))


def shade(c, f):
    return tuple(max(0, min(255, int(round(v * f)))) for v in c[:3])


# ───────────────────────── 로그(각도 검사·충돌 검사용) ─────────────────────────
SEG_LOG = []        # (분류, p0, p1) — 분류: 지면/지시선/글줄
LABELS = []         # 라벨 기록
OBJECTS = []        # 오브젝트 기록(이름, 티어, 레이어, 측정값)


def log_seg(kind, p0, p1):
    SEG_LOG.append((kind, tuple(p0), tuple(p1)))


# ───────────────────────── 그리기 레이어 ─────────────────────────
def safe_composite(dst, src, x, y):
    x = int(round(x)); y = int(round(y))
    sx0 = max(0, -x); sy0 = max(0, -y)
    dx0 = max(0, x); dy0 = max(0, y)
    sx1 = min(src.width, dst.width - x); sy1 = min(src.height, dst.height - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    dst.alpha_composite(src.crop((sx0, sy0, sx1, sy1)), (dx0, dy0))


def _a(c):
    return c[3] if len(c) == 4 else 255


class Layer:
    """페이지 mm 좌표 영역 (x0,y0)-(x1,y1)에 대응하는 투명 RGBA 레이어(KD px/mm)"""

    def __init__(self, x0, y0, x1, y1, name="", bg=None):
        self.name = name
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        self.w = int(math.ceil((x1 - x0) * KD))
        self.h = int(math.ceil((y1 - y0) * KD))
        self.img = Image.new("RGBA", (self.w, self.h), bg if bg is not None else (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    # 좌표 변환
    def X(self, x):
        return (x - self.x0) * KD

    def Y(self, y):
        return (y - self.y0) * KD

    def P(self, p):
        return ((p[0] - self.x0) * KD, (p[1] - self.y0) * KD)

    def _tmp(self, pts_px, fn, pad=2):
        xs = [p[0] for p in pts_px]; ys = [p[1] for p in pts_px]
        mnx = int(math.floor(min(xs))) - pad; mny = int(math.floor(min(ys))) - pad
        mxx = int(math.ceil(max(xs))) + pad; mxy = int(math.ceil(max(ys))) + pad
        w = mxx - mnx; h = mxy - mny
        if w <= 0 or h <= 0 or w > 12000 or h > 12000:
            return
        tmp = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        fn(ImageDraw.Draw(tmp), [(p[0] - mnx, p[1] - mny) for p in pts_px])
        safe_composite(self.img, tmp, mnx, mny)

    # 도형
    def poly(self, pts, fill=None, outline=None, lw=0.25):
        pp = [self.P(p) for p in pts]
        if fill is not None:
            if _a(fill) == 255:
                self.d.polygon(pp, fill=fill)
            else:
                self._tmp(pp, lambda d, q: d.polygon(q, fill=fill))
        if outline is not None:
            self.line(list(pts) + [pts[0]], outline, lw)

    def line(self, pts, fill, lw=0.25, joint=True, kind=None):
        pp = [self.P(p) for p in pts]
        wpx = max(1, int(round(lw * KD)))
        if kind:
            for i in range(len(pts) - 1):
                log_seg(kind, pts[i], pts[i + 1])
        if _a(fill) == 255:
            self.d.line(pp, fill=fill, width=wpx, joint="curve" if joint else None)
        else:
            self._tmp(pp, lambda d, q: d.line(q, fill=fill, width=wpx, joint="curve" if joint else None), pad=wpx + 2)

    def ell(self, cx, cy, a, b, fill=None, outline=None, lw=0.25):
        box = [self.X(cx - a), self.Y(cy - b), self.X(cx + a), self.Y(cy + b)]
        corners = [(box[0], box[1]), (box[2], box[3])]
        if fill is not None:
            if _a(fill) == 255:
                self.d.ellipse(box, fill=fill)
            else:
                self._tmp(corners, lambda d, q: d.ellipse([q[0][0], q[0][1], q[1][0], q[1][1]], fill=fill))
        if outline is not None:
            wpx = max(1, int(round(lw * KD)))
            if _a(outline) == 255:
                self.d.ellipse(box, outline=outline, width=wpx)
            else:
                self._tmp(corners, lambda d, q: d.ellipse([q[0][0], q[0][1], q[1][0], q[1][1]], outline=outline, width=wpx), pad=wpx + 2)

    def arc(self, cx, cy, a, b, a0, a1, fill, lw=0.25):
        box = [self.X(cx - a), self.Y(cy - b), self.X(cx + a), self.Y(cy + b)]
        wpx = max(1, int(round(lw * KD)))
        self.d.arc(box, a0, a1, fill=fill, width=wpx)

    def pie(self, cx, cy, a, b, a0, a1, fill=None, outline=None, lw=0.25):
        box = [self.X(cx - a), self.Y(cy - b), self.X(cx + a), self.Y(cy + b)]
        wpx = max(1, int(round(lw * KD)))
        if fill is not None:
            self.d.pieslice(box, a0, a1, fill=fill)
        if outline is not None:
            self.d.pieslice(box, a0, a1, outline=outline, width=wpx)

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, lw=0.25):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill, outline, lw)

    def dot(self, x, y, r, fill):
        self.ell(x, y, r, r, fill=fill)

    def dashed(self, p0, p1, fill, lw=0.25, dash=1.6, gap=1.2):
        L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        if L < 1e-6:
            return
        ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
        t = 0.0
        while t < L:
            t2 = min(L, t + dash)
            self.line([(p0[0] + ux * t, p0[1] + uy * t), (p0[0] + ux * t2, p0[1] + uy * t2)], fill, lw, joint=False)
            t += dash + gap

    def dashed_rect(self, x0, y0, x1, y1, fill, lw=0.25, dash=1.6, gap=1.2):
        for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
            self.dashed(a, b, fill, lw, dash, gap)

    # 평면(정면) 글자: 기준선 왼쪽 시작점 (x, y)
    def text(self, x, y, s, font, fill, anchor="ls"):
        self.d.text(self.P((x, y)), s, font=font, fill=fill, anchor=anchor)

    def text_c(self, x, y, s, font, fill):
        self.d.text(self.P((x, y)), s, font=font, fill=fill, anchor="ms")

    def text_r(self, x, y, s, font, fill):
        self.d.text(self.P((x, y)), s, font=font, fill=fill, anchor="rs")

    def paste(self, other):
        """다른 레이어를 이 레이어에 합성"""
        safe_composite(self.img, other.img, (other.x0 - self.x0) * KD, (other.y0 - self.y0) * KD)

    # 측정
    def alpha_mask(self, thr=40):
        return self.img.getchannel("A").point(lambda v: 255 if v > thr else 0)

    def measure(self, clip=(0, 0, PW, PH)):
        """클립 안의 불투명 화소 외곽 상자(mm)와 면적(mm²)"""
        m = self.alpha_mask()
        cx0 = max(0, int(round((clip[0] - self.x0) * KD))); cy0 = max(0, int(round((clip[1] - self.y0) * KD)))
        cx1 = min(self.w, int(round((clip[2] - self.x0) * KD))); cy1 = min(self.h, int(round((clip[3] - self.y0) * KD)))
        if cx1 <= cx0 or cy1 <= cy0:
            return None
        m = m.crop((cx0, cy0, cx1, cy1))
        bb = m.getbbox()
        if bb is None:
            return None
        cnt = m.histogram()[255]
        return {"box": (self.x0 + (cx0 + bb[0]) / KD, self.y0 + (cy0 + bb[1]) / KD,
                        self.x0 + (cx0 + bb[2]) / KD, self.y0 + (cy0 + bb[3]) / KD),
                "area": cnt / (KD * KD)}


def clip_edge_touch(layer):
    """레이어 경계에 불투명 화소가 닿으면 True(그림이 잘렸다는 경고용)"""
    a = layer.img.getchannel("A")
    w, h = a.size
    for box in ((0, 0, w, 2), (0, h - 2, w, h), (0, 0, 2, h), (w - 2, 0, w, h)):
        if a.crop(box).getbbox():
            return True
    return False


# ───────────────────────── 평면 변환 글자(등각 벽면·바닥) ─────────────────────────
class Flat:
    """정면 글자 판(u→오른쪽, v→아래, mm). 변환 전 원본."""

    def __init__(self, w_mm, h_mm, color):
        self.w = int(math.ceil(w_mm * KD)) + 4
        self.h = int(math.ceil(h_mm * KD)) + 4
        self.img = Image.new("RGBA", (self.w, self.h), tuple(color[:3]) + (0,))
        self.d = ImageDraw.Draw(self.img)

    def text(self, u, vb, s, font, fill):
        self.d.text((u * KD + 2, vb * KD + 2), s, font=font, fill=fill, anchor="ls")

    def line(self, u0, v0, u1, v1, fill, lw):
        self.d.line([(u0 * KD + 2, v0 * KD + 2), (u1 * KD + 2, v1 * KD + 2)], fill=fill, width=max(1, int(round(lw * KD))))

    def rect(self, u0, v0, u1, v1, fill):
        self.d.rectangle([u0 * KD + 2, v0 * KD + 2, u1 * KD + 2, v1 * KD + 2], fill=fill)


# 평면별 순방향 행렬 M: 평면 글자 (u,v) → 화면 (x,y). 단위 mm.
M_WALL_UP = ((C30, 0.0), (-0.5, 1.0))        # 벽면, 기준선 ↗(−30°): 북서 구역
M_WALL_DN = ((C30, 0.0), (0.5, 1.0))         # 벽면, 기준선 ↘(+30°)
M_FLOOR_SE = ((C30, -C30), (0.5, 0.5))       # 바닥, 기준선 ↘(+X), 글자 위쪽 = −Y(↗)
M_FLOOR_NE = ((C30, C30), (-0.5, 0.5))       # 바닥, 기준선 ↗(−Y), 글자 위쪽 = −X(↖)


def map_pt(M, ax, ay, u, v):
    (a, b), (c, d) = M
    return (ax + a * u + b * v, ay + c * u + d * v)


def affine_paste(layer, flat, M, ax, ay):
    """flat(원본 판)의 (0,0)이 화면 (ax, ay)mm에 놓이도록 M으로 변환해 layer에 합성"""
    (a, b), (c, d) = M
    log_seg("글줄", (ax, ay), (ax + a * 10.0, ay + c * 10.0))
    w, h = flat.img.size
    # 판 내부 여백 2px 보정: 원본 (0,0)은 판 화소 (2,2)
    corners = [(0, 0), (w, 0), (0, h), (w, h)]
    xs = [a * x + b * y for x, y in corners]
    ys = [c * x + d * y for x, y in corners]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    ow = int(math.ceil(maxx - minx)) + 2
    oh = int(math.ceil(maxy - miny)) + 2
    det = a * d - b * c
    ia, ib, ic, idd = d / det, -b / det, -c / det, a / det
    data = (ia, ib, ia * minx + ib * miny, ic, idd, ic * minx + idd * miny)
    out = flat.img.transform((ow, oh), Image.AFFINE, data, resample=Image.BICUBIC)
    px = layer.X(ax) + minx - (a * 2 + b * 2)
    py = layer.Y(ay) + miny - (c * 2 + d * 2)
    safe_composite(layer.img, out, px, py)


def iso_text(layer, s, font, fill, M, ax, ay, v_base=6.0):
    """한 줄 등각 글자. 기준선 왼쪽 시작점이 화면 (ax, ay)mm에 놓인다. 글줄 폭(mm, 변환 전)을 돌려준다."""
    wmm = tw(s, font) + 1.0
    f = Flat(wmm, v_base + 3.0, fill)
    f.text(0, v_base, s, font, fill)
    (a, b), (c, d) = M
    affine_paste(layer, f, M, ax - b * v_base, ay - d * v_base)
    return wmm


# ───────────────────────── 라벨 규격(베이징 R09~R15) ─────────────────────────
EN_CAP = 3.8          # 영문 대문자 높이(mm)
KO_EM = 3.8           # 국문 이름
SUP_EM = 2.1          # 원어 위첨자
BODY_EM = 3.0         # 본문
BODY_PITCH = 4.15     # 본문 줄 피치
DOT_R = 0.45          # 지시선 끝점 반지름(지름 0.9mm)
LEAD_LW = 0.3         # 지시선 굵기
EN_EM = EN_CAP / 0.71


def build_label_flat(en_lines, ko, sup, body, col):
    """영문 → 국문(+원어 위첨자) → 규선 → 본문 스택을 정면 판으로 만든다. (판, 폭, 높이, 규선 v)를 돌려준다."""
    f_en, f_ko, f_sup, f_bd = fnt("en", EN_EM), fnt("b", KO_EM), fnt("m", SUP_EM), fnt("m", BODY_EM)
    widths = [tw(s, f_en) for s in en_lines]
    ko_w = tw(ko, f_ko) + ((tw(sup, f_sup) + 1.2) if sup else 0.0)
    widths.append(ko_w)
    widths += [tw(s, f_bd) for s in body]
    W = max(widths + [18.0])
    v = 0.3
    base_en = []
    for i, s in enumerate(en_lines):
        v += EN_CAP
        base_en.append(v)
        v += 0.8
    v += 0.5
    base_ko = v + 3.3
    v_rule = base_ko + 1.5
    base_body = [v_rule + 1.6 + 2.7 + BODY_PITCH * i for i in range(len(body))]
    H = (base_body[-1] + 1.3) if body else (v_rule + 0.5)
    f = Flat(W + 2.0, H + 1.0, col)
    for s, vb in zip(en_lines, base_en):
        f.text(0, vb, s, f_en, col)
    f.text(0, base_ko, ko, f_ko, col)
    if sup:
        f.text(tw(ko, f_ko) + 1.2, base_ko - 1.55, sup, f_sup, col)
    if body:
        f.line(0, v_rule, W, v_rule, col, 0.25)
    for s, vb in zip(body, base_body):
        f.text(0, vb, s, f_bd, col)
    return f, W, H, v_rule


def wall_slope_of(M):
    return M[1][0] / M[0][0]


def draw_label(L, T, en_lines, ko, body, col, M, mode="above", side="L", gap=2.4, sup=None, extra_gap=0.0, name="", plate=False):
    """브래킷형 라벨. T = 대상 위 끝점(page mm). 수직 지시선이 규선 끝에서 T까지 가고 끝에 점을 찍는다.
    mode: above(라벨이 대상 위, 지시선 ↓) / below(라벨이 대상 아래, 지시선 ↑)"""
    f, W, H, v_rule = build_label_flat(en_lines, ko, sup, body, col)
    c = M[1][0]
    a = M[0][0]
    ub = -2.2 if side == "L" else W + 2.2
    ax = T[0] - a * ub
    if mode == "above":
        ay = T[1] - gap - extra_gap - H - max(0.0, c * W)
    else:
        ay = T[1] + gap + extra_gap - min(0.0, c * W)
    if plate:        # 바다 위처럼 바탕이 진한 곳: 반투명 크림 판(R16 말풍선의 약식)
        pc = [map_pt(M, ax, ay, u, v) for u, v in ((-1.2, -0.8), (W + 1.2, -0.8), (W + 1.2, H + 0.8), (-1.2, H + 0.8))]
        L.poly(pc, fill=(248, 240, 214, 190))
    affine_paste(L, f, M, ax, ay)
    y_rule_b = ay + c * ub + v_rule
    L.line([(T[0], y_rule_b), (T[0], T[1])], col, LEAD_LW, joint=False, kind="지시선")
    L.dot(T[0], T[1], DOT_R, col)
    corners = [map_pt(M, ax, ay, u, v) for u, v in ((0, 0), (W, 0), (W, H), (0, H))]
    rec = {"이름": name or ko, "종류": "브래킷", "다각형": corners, "대상": T, "열": en_lines[0]}
    LABELS.append(rec)
    return rec


def draw_flag(L, T, en, ko, col, M, side="L", gap=0.0, name="", mode="above", pole=8.0):
    """깃대형 이름표(R15): 영문+국문 두 줄만, 세로 깃대 한 줄이 대상까지 가서 점으로 끝난다.
    mode above: 글이 대상 위(깃대 ↓), below: 글이 대상 아래(깃대 ↑)"""
    f, W, H, v_rule = build_label_flat([en], ko, None, [], col)
    H = v_rule - 0.2
    c = M[1][0]
    a = M[0][0]
    ub = -1.8 if side == "L" else W + 1.8
    ax = T[0] - a * ub
    if mode == "above":
        ay = T[1] - gap - pole - max(0.0, c * W)
        affine_paste(L, f, M, ax, ay)
        y_top_b = ay + c * ub - 0.3
        L.line([(T[0], y_top_b), (T[0], T[1])], col, LEAD_LW, joint=False, kind="지시선")
    else:
        ay = T[1] + gap + pole - min(0.0, c * W)
        affine_paste(L, f, M, ax, ay)
        y_bot_b = ay + c * ub + H + 0.6
        L.line([(T[0], y_bot_b), (T[0], T[1])], col, LEAD_LW, joint=False, kind="지시선")
    L.dot(T[0], T[1], DOT_R, col)
    corners = [map_pt(M, ax, ay, u, v) for u, v in ((0, 0), (W, 0), (W, H), (0, H))]
    rec = {"이름": name or ko, "종류": "깃대형", "다각형": corners, "대상": T, "열": en}
    LABELS.append(rec)
    return rec


def draw_floor_name(L, ax, ay, ko, en, col, kind="SE", em=3.8):
    """지형명: 바닥에 눕혀 지형색 톤온톤으로 쓴다(영문 1줄 + 국문 1줄)"""
    M = M_FLOOR_SE if kind == "SE" else M_FLOOR_NE
    w1 = iso_text(L, en, fnt("en", em * 1.25), col, M, ax, ay)
    # 두 번째 줄: 바닥에서 글자 '아래'는 +Y 방향(↙) 또는 +X 방향(↘)으로 4.6mm
    (a, b), (c, d) = M
    ax2, ay2 = ax + b * 5.4, ay + d * 5.4
    w2 = iso_text(L, ko, fnt("b", em), col, M, ax2, ay2)
    return max(w1, w2)


# ───────────────────────── 등각 입체 도구 ─────────────────────────
class Iso:
    """원점 (ox,oy) = 평면 (0,0,0)의 화면 위치(mm). 평면 길이 단위 = 화면 변 길이(mm).
    +X → 화면 ↘, +Y → 화면 ↙, +Z → 화면 위. 보이는 수직면: +Y향(왼면)·+X향(오른면)."""

    def __init__(self, L, ox, oy):
        self.L, self.ox, self.oy = L, ox, oy

    def p(self, X, Y, Z=0.0):
        return (self.ox + C30 * (X - Y), self.oy + 0.5 * (X + Y) - Z)

    def pl(self, pts3):
        return [self.p(*q) for q in pts3]

    def poly3(self, pts3, fill=None, ol=None, lw=0.2):
        self.L.poly(self.pl(pts3), fill, ol, lw)

    def line3(self, pts3, col, lw=0.2):
        self.L.line(self.pl(pts3), col, lw)

    def rect3(self, X0, Y0, X1, Y1, Z, fill, ol=None, lw=0.2):
        self.poly3([(X0, Y0, Z), (X1, Y0, Z), (X1, Y1, Z), (X0, Y1, Z)], fill, ol, lw)

    def box(self, X0, Y0, Z0, X1, Y1, Z1, cols, ol=EDGE, lw=0.2):
        """cols = (상면, 왼면(+Y향), 오른면(+X향))"""
        top, left, right = cols
        self.poly3([(X0, Y1, Z0), (X1, Y1, Z0), (X1, Y1, Z1), (X0, Y1, Z1)], left, ol, lw)
        self.poly3([(X1, Y0, Z0), (X1, Y1, Z0), (X1, Y1, Z1), (X1, Y0, Z1)], right, ol, lw)
        self.poly3([(X0, Y0, Z1), (X1, Y0, Z1), (X1, Y1, Z1), (X0, Y1, Z1)], top, ol, lw)

    def face(self, kind, X, Y, Z, uv):
        """평면 위 면 좌표 (u,v)를 화면 점으로. kind L: Y=상수 면(+Y향, u↔+X), R: X=상수 면(+X향, u↔+Y)"""
        if kind == "L":
            return [self.p(X + u, Y, Z + v) for u, v in uv]
        return [self.p(X, Y + u, Z + v) for u, v in uv]

    def fpoly(self, kind, X, Y, Z, uv, fill=None, ol=None, lw=0.15):
        self.L.poly(self.face(kind, X, Y, Z, uv), fill, ol, lw)

    def arch(self, kind, X, Y, Z, u0, u1, v0, v1, fill, ol=None, lw=0.12, n=9):
        """사각 개구부 + 반원 상단. 폭 u1-u0, 반원은 v1에서 시작."""
        r = (u1 - u0) / 2.0
        cu = (u0 + u1) / 2.0
        pts = [(u0, v0), (u1, v0), (u1, v1)]
        for i in range(1, n):
            ang = math.pi * i / n
            pts.append((cu + r * math.cos(ang), v1 + r * math.sin(ang)))
        pts.append((u0, v1))
        self.fpoly(kind, X, Y, Z, pts, fill, ol, lw)

    def ell(self, X, Y, Z, R, fill=None, ol=None, lw=0.2):
        a = 1.2247 * R
        b = 0.7071 * R
        cx, cy = self.p(X, Y, Z)
        self.L.ell(cx, cy, a, b, fill, ol, lw)

    def cyl(self, X, Y, Z0, Z1, R, top, side, ol=EDGE, lw=0.2):
        a = 1.2247 * R
        b = 0.7071 * R
        cx0, cy0 = self.p(X, Y, Z0)
        cx1, cy1 = self.p(X, Y, Z1)
        self.L.rect(cx0 - a, cy1, cx0 + a, cy0, fill=side)
        self.L.pie(cx0, cy0, a, b, 0, 180, fill=side)
        self.L.line([(cx0 - a, cy1), (cx0 - a, cy0)], ol, lw, joint=False)
        self.L.line([(cx0 + a, cy1), (cx0 + a, cy0)], ol, lw, joint=False)
        self.L.pie(cx0, cy0, a, b, 0, 180, outline=ol, lw=lw)
        self.L.ell(cx1, cy1, a, b, fill=top, outline=ol, lw=lw)

    def dome(self, X, Y, Z, R, fill, ol=EDGE, lw=0.2):
        """반구 돔: 평면 반지름 R의 반구. 화면에서는 반지름 1.2247R 반원."""
        a = 1.2247 * R
        cx, cy = self.p(X, Y, Z)
        self.L.pie(cx, cy, a, a, 180, 360, fill=fill, outline=ol, lw=lw)
        self.L.line([(cx - a, cy), (cx + a, cy)], ol, lw, joint=False)


def band_poly(pts, w, bevel=False):
    """중심선 꺾은선 → 폭 w(수직 방향 mm)의 띠. 안쪽은 마이터 이음, bevel=True면 바깥쪽 꼭짓점을 깎는다.
    (다각형, 왼쪽 가장자리, 오른쪽 가장자리)"""
    n = len(pts)
    dirs = []
    for i in range(n - 1):
        dx, dy = pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]
        l = math.hypot(dx, dy)
        dirs.append((dx / l, dy / l))
    left, right = [], []
    for i in range(n):
        if i == 0 or i == n - 1:
            d = dirs[0] if i == 0 else dirs[-1]
            nn = (-d[1], d[0])
            left.append((pts[i][0] + nn[0] * w / 2.0, pts[i][1] + nn[1] * w / 2.0))
            right.append((pts[i][0] - nn[0] * w / 2.0, pts[i][1] - nn[1] * w / 2.0))
            continue
        d_in, d_out = dirs[i - 1], dirs[i]
        n_in = (-d_in[1], d_in[0])
        n_out = (-d_out[1], d_out[0])
        mx, my = n_in[0] + n_out[0], n_in[1] + n_out[1]
        ml = math.hypot(mx, my)
        mx, my = mx / ml, my / ml
        k = (w / 2.0) / (mx * n_in[0] + my * n_in[1])
        lm = (pts[i][0] + mx * k, pts[i][1] + my * k)
        rm = (pts[i][0] - mx * k, pts[i][1] - my * k)
        cross = d_in[0] * d_out[1] - d_in[1] * d_out[0]
        if bevel and abs(cross) > 1e-6:
            la = (pts[i][0] + n_in[0] * w / 2.0, pts[i][1] + n_in[1] * w / 2.0)
            lb = (pts[i][0] + n_out[0] * w / 2.0, pts[i][1] + n_out[1] * w / 2.0)
            ra = (pts[i][0] - n_in[0] * w / 2.0, pts[i][1] - n_in[1] * w / 2.0)
            rb = (pts[i][0] - n_out[0] * w / 2.0, pts[i][1] - n_out[1] * w / 2.0)
            if cross > 0:      # +n 쪽이 안쪽 → 오른쪽(−n)이 바깥
                left.append(lm)
                right.extend([ra, rb])
            else:
                left.extend([la, lb])
                right.append(rm)
        else:
            left.append(lm)
            right.append(rm)
    return left + right[::-1], left, right


DIRS = {"SE": (C30, 0.5), "SW": (-C30, 0.5), "NE": (C30, -0.5), "NW": (-C30, -0.5)}


def walk(start, steps):
    """등각 지면 선분 사슬: steps = [(방향, 길이mm), ...] 방향은 SE/SW/NE/NW(±30°)"""
    pts = [tuple(start)]
    for d, l in steps:
        dx, dy = DIRS[d]
        x, y = pts[-1]
        pts.append((x + dx * l, y + dy * l))
    return pts

INK = (52, 44, 36)
GREYBAR = (178, 162, 132)
GREYBAR_D = (150, 134, 108)


def in_poly(pt, poly):
    x, y = pt
    ins = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            if x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                ins = not ins
    return ins


# ───────────────────────── 소품 공용 ─────────────────────────
_seed = [12345]


def rnd():
    _seed[0] = (_seed[0] * 1103515245 + 12345) & 0x7FFFFFFF
    return _seed[0] / 0x7FFFFFFF


def person(L, x, y, h=5.6, col=(150, 70, 52), skin=(226, 184, 150)):
    """작은 인물 실루엣: (x,y)는 발 밑. 머리+몸통+그림자"""
    L.ell(x + 0.2, y + 0.1, h * 0.28, h * 0.1, fill=(110, 90, 62, 150))
    L.poly([(x - h * 0.2, y), (x + h * 0.2, y), (x + h * 0.15, y - h * 0.62), (x - h * 0.15, y - h * 0.62)], fill=col)
    L.ell(x, y - h * 0.80, h * 0.15, h * 0.15, fill=skin)


def cypress(L, x, y, h=16.0, w=3.2):
    """사이프러스: 좁고 높은 상록수"""
    L.ell(x + 0.6, y + 0.2, w * 0.7, w * 0.25, fill=(90, 100, 70, 150))
    L.rect(x - 0.35, y - 1.5, x + 0.35, y, fill=(96, 70, 44))
    L.poly([(x - w / 2, y - 1.5), (x - w * 0.42, y - h * 0.55), (x, y - h), (x + w * 0.42, y - h * 0.55), (x + w / 2, y - 1.5)], fill=(52, 96, 58), outline=(36, 70, 40), lw=0.2)
    L.line([(x - w * 0.12, y - h * 0.8), (x - w * 0.18, y - h * 0.2)], (92, 138, 84), 0.35, joint=False)


def olive(L, x, y, r=4.4):
    """올리브: 둥근 수관과 굽은 줄기"""
    L.ell(x + 0.8, y + 0.2, r * 0.9, r * 0.28, fill=(90, 100, 70, 150))
    L.poly([(x - 0.5, y), (x + 0.5, y), (x + 0.3, y - r * 0.9), (x - 0.3, y - r * 0.9)], fill=(106, 80, 52))
    L.ell(x, y - r * 1.4, r, r * 0.82, fill=(122, 150, 96), outline=(86, 112, 66), lw=0.2)
    L.ell(x - r * 0.3, y - r * 1.55, r * 0.45, r * 0.3, fill=(160, 184, 126))


def column_ruin(L, x, y, h=7.0, w=1.5, broken=False):
    """기둥 폐허"""
    L.ell(x + 0.5, y + 0.2, w * 1.2, w * 0.4, fill=(120, 100, 70, 120))
    L.rect(x - w / 2, y - h, x + w / 2, y, fill=(236, 224, 198), outline=(150, 128, 94), lw=0.18)
    if not broken:
        L.rect(x - w * 0.85, y - h - 0.9, x + w * 0.85, y - h, fill=(228, 214, 186), outline=(150, 128, 94), lw=0.18)
    L.line([(x - w * 0.15, y - h + 0.6), (x - w * 0.15, y - 0.4)], (206, 190, 160), 0.22, joint=False)


KE = 0.57735
TRAV = (208, 186, 144)
TRAV_L = (224, 204, 164)
TRAV_D = (176, 152, 114)
ARCH_IN = (104, 78, 50)
TUFF = (166, 136, 102)
CONC = (170, 164, 150)
def steam(L, x, y, n=4, r=2.6):
    with_alpha = (255, 255, 255, 170)
    for i in range(n):
        L.ell(x + (i % 2) * 2.2 - 1.0, y - i * 2.8, r * (1.0 - 0.1 * i), r * 0.8 * (1.0 - 0.1 * i), fill=with_alpha, outline=(220, 214, 204, 200), lw=0.15)


# ───────────────────────── 받침(흙 단면 디오라마 타일) ─────────────────────────
def slab(L, cx, cy, w, t=5.0, top=(210, 196, 166), grass=True, edge=EDGE, soil=None):
    """등각 마름모 받침: 화면 폭 w, 흙 측면 두께 t. (cx,cy)=마름모 중심. 평면 변 길이 = w/√3."""
    h = w / SQ3
    Lv, Tv, Rv, Bv = (cx - w / 2, cy), (cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2)
    c1, c2 = (soil or SOIL), shade(soil or SOIL, 0.78)
    L.poly([Lv, Bv, (Bv[0], Bv[1] + t), (Lv[0], Lv[1] + t)], fill=c1, outline=(70, 50, 32), lw=0.2)
    L.poly([Bv, Rv, (Rv[0], Rv[1] + t), (Bv[0], Bv[1] + t)], fill=c2, outline=(70, 50, 32), lw=0.2)
    if grass:
        L.poly([Lv, Bv, (Bv[0], Bv[1] + 1.3), (Lv[0], Lv[1] + 1.3)], fill=GRASS)
        L.poly([Bv, Rv, (Rv[0], Rv[1] + 1.3), (Bv[0], Bv[1] + 1.3)], fill=shade(GRASS, 0.82))
    L.poly([Lv, Tv, Rv, Bv], fill=top, outline=edge, lw=0.35)
    return {"L": Lv, "T": Tv, "R": Rv, "B": Bv, "side": h / 2 * 0 + (w / SQ3)}


def iso_of_slab(L, cx, cy, w, inset=3.0):
    """받침 위 건물용 Iso: 마름모의 위쪽 꼭짓점이 평면 (0,0). 평면 변 = w/√3"""
    side = w / SQ3
    return Iso(L, cx, cy - side / 2.0), side


BRICK = (192, 108, 80)
BRICK_L = (210, 128, 96)
BRICK_D = (156, 84, 62)

ROOF_RED = (196, 92, 64)

def floor_line(L, ax, ay, parts, M):
    """바닥에 눕힌 한 줄 글(여러 글꼴 이어 붙임)"""
    u = 0.0
    (a, b), (c, d) = M
    for (txt, font, col) in parts:
        iso_text(L, txt, font, col, M, ax + a * u, ay + c * u)
        u += tw(txt, font) + 1.6
    return u

VERSION = "v16"
