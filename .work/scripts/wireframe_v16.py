# -*- coding: utf-8 -*-
# 로마 콘크리트 A2 와이어프레임 v16 (최종 1mm = 4px, 내부 2배 슈퍼샘플로 그린 뒤 축소)
# - v15 → v16: 비평가 4명의 지적 반영(지도 위 글자 등각 평면화, 규격 지시선, 강 ±30° 재작도,
#   오브젝트별 레이어 자동 실측 검사표, 베수비오 밑동 가림, 욕장 축소, 추가 Support 후보, 밀도 보강,
#   Core 셀 체인 신문 문법, 패널 문법 정리, 범례·푸터).
# - 모든 모델의 최종 수준은 LocalBanana 미니어처 콜로세움 디오라마이며, 이 도면은 형태·크기·배치·절개 여부만 판정하는 배치 도식이다.
# - 실행: cd .work && uv run --no-project --with pillow python -I scripts/wireframe_v16.py
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


PANEL_RECT = {"정의": (18, 20, 118, 68), "레시피": (18, 76, 118, 132), "위치도": (302, 20, 402, 92),
              "석회": (18, 505, 170, 565), "연대기": (178, 505, 294, 565), "수명비교": (302, 505, 402, 565)}
INK = (52, 44, 36)
GREYBAR = (178, 162, 132)
GREYBAR_D = (150, 134, 108)


# ───────────────────────── 패널(화면 평행 정보 구획) ─────────────────────────
def pin(P, x, y, col):
    """물방울 핀(2.5×3.6mm) — 끝점이 (x,y)"""
    P.poly([(x, y), (x - 1.2, y - 2.0), (x + 1.2, y - 2.0)], fill=col)
    P.ell(x, y - 2.5, 1.25, 1.25, fill=col)
    P.ell(x, y - 2.5, 0.45, 0.45, fill=(255, 255, 255))


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


def zone(P, x0, y0, x1, y1, tier, en, ko):
    """패널 구획: 0.3mm 점선 영역선(최종 인쇄에는 상자 없음), 영문 초압축 대문자 제목 + 국문 부제(윗선 정렬), 티어 칩"""
    col = TIER_COL[tier]
    tcol = TIER_TXT[tier]
    P.dashed_rect(x0, y0, x1, y1, col, lw=0.3, dash=2.6, gap=1.5)
    fe = fnt("en", 7.5 / 0.71)
    P.text(x0 + 2.5, y0 + 2.0 + 7.5, en, fe, tcol)
    wk = tw(en, fe)
    P.text(x0 + 2.5 + wk + 2.0, y0 + 2.0 + 3.2, ko, fnt("b", 3.6), tcol)
    f = fnt("s", 2.2)
    wc = tw(tier, f) + 3.0
    P.rect(x1 - wc - 1.6, y0 + 1.6, x1 - 1.6, y0 + 5.4, fill=col)
    P.text_c(x1 - 1.6 - wc / 2.0, y0 + 4.3, tier, f, (255, 255, 255))


def tline(P, x, y, s, em=2.5, col=INK, kind="m"):
    P.text(x, y, s, fnt(kind, em), col)


def panel_definition(P):
    x0, y0, x1, y1 = PANEL_RECT["정의"]
    zone(P, x0, y0, x1, y1, "Basic", "DEFINITION", "로마 콘크리트란?")
    tline(P, x0 + 2.5, y0 + 17.0, "석회와 화산재, 굵은 골재를 물과 섞어 굳힌", 2.7)
    tline(P, x0 + 2.5, y0 + 20.8, "고대 로마의 콘크리트(철근 없음)", 2.7)
    cells = ["결합재", "굵은 골재", "반죽·다짐", "철근", "수명", "대표 건물"]
    cw = (x1 - x0 - 5.0) / 3.0
    for i, nm in enumerate(cells):
        cx = x0 + 2.5 + (i % 3) * cw
        cy = y0 + 25.0 + (i // 3) * 10.6
        P.line([(cx, cy), (cx + cw - 2.0, cy)], C_BASIC, 0.3, joint=False)
        tline(P, cx, cy + 3.4, nm, 2.3, C_BASIC, "s")
        P.rect(cx, cy + 4.6, cx + cw - 2.0 - (i % 2) * 7, cy + 5.8, fill=GREYBAR)


def panel_recipe(P):
    x0, y0, x1, y1 = PANEL_RECT["레시피"]
    zone(P, x0, y0, x1, y1, "Basic", "THE RECIPE", "레시피·순서")
    chips = ["생석회", "화산재", "화산암 골재", "물"]
    cw = (x1 - x0 - 5.0 - 3 * 2.0) / 4.0
    for i, nm in enumerate(chips):
        cx = x0 + 2.5 + i * (cw + 2.0)
        cy = y0 + 14.0
        P.rect(cx, cy, cx + cw, cy + 9.0, outline=C_BASIC, lw=0.3)
        P.rect(cx + 1.2, cy + 1.2, cx + 6.2, cy + 6.2, fill=GREYBAR)
        P.text_c(cx + cw / 2.0, cy + 8.0 - 0.6, nm, fnt("s", 2.2 if len(nm) > 4 else 2.4), INK)
    steps = ["① 마른 채 섞기", "② 물 붓기", "③ 끓어오름"]
    sx = x0 + 2.5
    for i, st in enumerate(steps):
        w = tw(st, fnt("s", 2.5)) + 4.0
        P.rect(sx, y0 + 26.5, sx + w, y0 + 32.5, fill=C_BASIC)
        P.text_c(sx + w / 2.0, y0 + 30.9, st, fnt("s", 2.5), (255, 255, 255))
        if i < 2:
            P.poly([(sx + w + 1.0, y0 + 29.5 - 1.6), (sx + w + 3.6, y0 + 29.5), (sx + w + 1.0, y0 + 29.5 + 1.6)], fill=C_BASIC)
        sx += w + 4.8
    tline(P, x0 + 2.5, y0 + 40.0, "화산재: 바다 공사=포추올리 일대, 로마 건물=알바노 구릉", 2.3)
    tline(P, x0 + 2.5, y0 + 43.8, "물: 육상 건물=민물, 항구 구조물만 바닷물", 2.3)
    tline(P, x0 + 2.5, y0 + 47.6, "반죽은 붓지 않고 거푸집에 다져 넣는다", 2.3)


ITALY = [(0.20, 0.00), (0.16, 0.10), (0.20, 0.20), (0.30, 0.30), (0.38, 0.40), (0.48, 0.47), (0.54, 0.53), (0.62, 0.62),
         (0.70, 0.72), (0.78, 0.84), (0.84, 0.96), (0.92, 1.00), (0.98, 0.88), (0.90, 0.76), (0.98, 0.64), (0.94, 0.52),
         (0.84, 0.46), (0.72, 0.38), (0.62, 0.28), (0.54, 0.18), (0.46, 0.08), (0.40, 0.00)]


def panel_where(P):
    x0, y0, x1, y1 = PANEL_RECT["위치도"]
    zone(P, x0, y0, x1, y1, "Basic", "WHERE", "위치도")
    mx0, my0, mw, mh = x0 + 24.5, y0 + 14.0, 51.0, 53.0
    poly = [(mx0 + a * mw, my0 + b * mh) for a, b in ITALY]
    gy = my0
    while gy < my0 + mh:
        gx = mx0
        while gx < mx0 + mw:
            if in_poly((gx, gy), poly):
                P.ell(gx, gy, 0.36, 0.36, fill=(196, 166, 98))
            gx += 1.3
        gy += 1.3
    # 핀: 로마(콜로세움·포르투스 공유 핀) · 알바노 구릉 · 포추올리 · 베수비오
    pts = {"rome": (mx0 + 0.31 * mw, my0 + 0.32 * mh), "alban": (mx0 + 0.34 * mw, my0 + 0.345 * mh),
           "poz": (mx0 + 0.495 * mw, my0 + 0.465 * mh), "ves": (mx0 + 0.535 * mw, my0 + 0.48 * mh)}
    pin(P, pts["rome"][0] - 0.8, pts["rome"][1], C_BASIC)
    pin(P, pts["alban"][0] + 1.4, pts["alban"][1] + 0.6, C_BASIC)
    pin(P, pts["poz"][0] - 0.6, pts["poz"][1], C_BASIC)
    pin(P, pts["ves"][0] + 1.6, pts["ves"][1] + 0.5, C_BASIC)
    # 좌우 2열 라벨 + 직교 지시선(규선 → 직교로 꺾여 핀까지, 끝 장식 없음)
    f1, f2 = fnt("b", 2.5), fnt("m", 2.2)
    lx = x0 + 2.5
    rx = mx0 + mw + 4.0
    items = [("로마", "콜로세움·포르투스", lx, y0 + 15.0, pts["rome"][0] - 0.8, pts["rome"][1] - 3.0, "L"),
             ("알바노 구릉", "로마 건물의 화산재", lx, y0 + 40.0, pts["alban"][0] + 1.4, pts["alban"][1] + 0.6 - 0.2, "L"),
             ("포추올리", "바다 공사용 화산재", rx, y0 + 28.0, pts["poz"][0] - 0.6, pts["poz"][1] - 3.0, "R"),
             ("베수비오", "79년 분화", rx, y0 + 58.0, pts["ves"][0] + 1.6, pts["ves"][1] + 0.5 - 0.2, "R")]
    for nm, sub, tx, ty, px_, py_, side in items:
        wl = max(tw(nm, f1), tw(sub, f2))
        P.text(tx, ty, nm, f1, C_BASIC)
        P.text(tx, ty + 3.4, sub, f2, INK)
        ry = ty + 4.4
        P.line([(tx, ry), (tx + wl, ry)], C_BASIC, 0.2, joint=False)
        ex = tx + wl if side == "L" else tx
        P.line([(ex, ry), (px_, ry), (px_, py_)], C_BASIC, 0.2, joint=False)


def panel_lime(P):
    x0, y0, x1, y1 = PANEL_RECT["석회"]
    zone(P, x0, y0, x1, y1, "Detail", "LIME CLASTS", "석회 알갱이·자가치유")
    caps = [("석회 알갱이", "뜨거운 혼합에서 남음"), ("균열 + 빗물", "틈으로 스며듦"), ("칼슘 용출", "알갱이가 녹아 나옴"), ("방해석 봉합", "결정이 균열을 메움")]
    cw = 31.0
    for i, (a, b) in enumerate(caps):
        cx = x0 + 3.0 + i * (cw + 4.0)
        cy = y0 + 14.0
        P.rect(cx, cy, cx + cw, cy + 26.0, fill=(236, 222, 188), outline=C_DETAIL, lw=0.3)
        # 콘크리트 단면 자리(점·균열·결정)
        for k in range(9):
            P.ell(cx + 4 + (k * 7) % 24, cy + 5 + (k * 11) % 16, 0.5, 0.5, fill=GREYBAR_D)
        if i == 0:
            P.ell(cx + cw / 2, cy + 13, 3.6, 3.0, fill=(252, 250, 244), outline=C_DETAIL, lw=0.25)
        if i >= 1:
            P.line([(cx + cw / 2 - 1, cy), (cx + cw / 2 + 2, cy + 7), (cx + cw / 2 - 2, cy + 14), (cx + cw / 2 + 1, cy + 22)], C_INK if False else INK, 0.35)
        if i == 1:
            for k in range(3):
                P.line([(cx + 5 + k * 9, cy + 1.5), (cx + 5 + k * 9 - 1, cy + 5)], (70, 120, 190), 0.4, joint=False)
        if i == 2:
            P.ell(cx + cw / 2 + 5, cy + 18, 2.4, 2.0, fill=(252, 250, 244), outline=C_DETAIL, lw=0.2)
            for k in range(4):
                P.ell(cx + cw / 2 + 1 - k * 1.8, cy + 8 + k * 2.4, 0.7, 0.7, fill=(70, 120, 190))
        if i == 3:
            for k in range(5):
                P.poly([(cx + cw / 2 - 2 + k * 0.8, cy + 3 + k * 4.4), (cx + cw / 2 + 0.6 + k * 0.8, cy + 2 + k * 4.4), (cx + cw / 2 + 1.0 + k * 0.8, cy + 5.4 + k * 4.4)], fill=(252, 250, 244), outline=C_DETAIL, lw=0.15)
        P.text_c(cx + cw / 2, cy + 30.6, a, fnt("s", 2.5), C_DETAIL_T)
        P.text_c(cx + cw / 2, cy + 34.4, b, fnt("m", 2.2), INK)
        if i < 3:
            ax = cx + cw + 0.6
            P.poly([(ax, cy + 11), (ax + 2.8, cy + 13), (ax, cy + 15)], fill=C_DETAIL)
    tline(P, x0 + 3.0, y1 - 3.0, "같은 단면, 같은 시점 4칸 — 6단계에서 이어지는 확대 창의 풀이", 2.2, C_DETAIL_T)


def panel_history(P):
    x0, y0, x1, y1 = PANEL_RECT["연대기"]
    zone(P, x0, y0, x1, y1, "Basic", "HISTORY", "연대기·근거")
    ev = [("79년", "폼페이 공사 현장", "화산재에 매몰"), ("2017", "바닷물이 키운", "새 광물 연구"), ("2023", "MIT: 뜨거운 혼합", "가설 제시"), ("2025", "폼페이 현장에서", "가설 확인")]
    ly = y0 + 31.0
    P.line([(x0 + 4, ly), (x1 - 4, ly)], C_BASIC, 0.35, joint=False)
    P.poly([(x1 - 4, ly - 1.4), (x1 - 1.6, ly), (x1 - 4, ly + 1.4)], fill=C_BASIC)
    cwid = (x1 - x0 - 8) / 4.0
    for i, (yr, a, b) in enumerate(ev):
        cx = x0 + 4 + cwid * (i + 0.12)
        P.ell(cx, ly, 1.1, 1.1, fill=C_BASIC)
        up = (i % 2 == 0)
        if up:
            P.line([(cx, ly - 1.2), (cx, ly - 5.0)], C_BASIC, 0.25, joint=False)
            tline(P, cx + 1.6, y0 + 20.4, yr, 3.4, C_BASIC, "b")
            tline(P, cx + 1.6, y0 + 24.2, a, 2.2)
            tline(P, cx + 1.6, y0 + 27.4, b, 2.2)
        else:
            P.line([(cx, ly + 1.2), (cx, ly + 5.0)], C_BASIC, 0.25, joint=False)
            tline(P, cx + 1.6, y0 + 41.4, yr, 3.4, C_BASIC, "b")
            tline(P, cx + 1.6, y0 + 45.2, a, 2.2)
            tline(P, cx + 1.6, y0 + 48.4, b, 2.2)
    tline(P, x0 + 3.0, y1 - 3.0, "2023 → 2025: 실마리 → 현장 확인(과장 금지)", 2.1, C_BASIC)


def panel_100v2000(P):
    x0, y0, x1, y1 = PANEL_RECT["수명비교"]
    zone(P, x0, y0, x1, y1, "Basic", "100 VS 2000", "수명 비교")
    base = y1 - 9.0
    hb = 30.0
    P.rect(x0 + 10, base - hb * 100 / 2000.0, x0 + 24, base, fill=GREYBAR_D)
    P.rect(x0 + 40, base - hb, x0 + 54, base, fill=C_BASIC)
    P.line([(x0 + 4, base), (x1 - 4, base)], INK, 0.3, joint=False)
    tline(P, x0 + 7, base - 3.2, "100년", 3.2, INK, "b")
    tline(P, x0 + 36, base - hb - 1.6, "2000년", 3.2, C_BASIC, "b")
    tline(P, x0 + 7, base + 3.6, "현대 콘크리트", 2.2)
    tline(P, x0 + 36, base + 3.6, "로마 콘크리트", 2.2)
    tline(P, x0 + 60, y0 + 16.0, "수명(사용 기록) 비교", 2.3, C_BASIC, "s")
    tline(P, x0 + 60, y0 + 19.8, "— 강도 비교가 아님", 2.3, INK)
    tline(P, x0 + 60, y0 + 24.2, "현대 약 30MPa", 2.1, GREYBAR_D)
    tline(P, x0 + 60, y0 + 27.4, "로마 약 6MPa", 2.1, GREYBAR_D)


def draw_title(P):
    """타이틀 록업: 로마 신전 정면 입면(월드의 등각과 대비되는 화면 평행). 헥사스타일 6열주 + 엔타블러처 + 계단, 글자는 중심 210에 가운데 정렬."""
    cx = 210.0
    tint = (244, 214, 208)
    # 페디먼트
    P.poly([(126.5, 35.0), (cx, 10.0), (293.5, 35.0)], fill=tint, outline=C_CORE, lw=0.8)
    P.poly([(139.0, 33.0), (cx, 14.5), (281.0, 33.0)], fill=(250, 232, 226), outline=C_CORE, lw=0.35)
    P.ell(cx, 25.0, 3.4, 3.4, fill=(250, 244, 230), outline=C_CORE, lw=0.5)
    # 엔타블러처(프리즈) + 영문 부제
    P.rect(128.5, 35.0, 291.5, 43.5, fill=(252, 240, 226), outline=C_CORE, lw=0.6)
    P.text_c(cx, 41.0, "ANCIENT ROME · SELF-HEALING CONCRETE", fnt("en", 3.4 / 0.71), C_CORE_T)
    # 열주 6개 (왼 3 + 오른 3), 높이 40mm
    for k in range(6):
        x = (141.0 + 12.5 * k) if k < 3 else (254.0 + 12.5 * (k - 3))
        P.rect(x - 4.2, 44.0, x + 4.2, 46.6, fill=(244, 232, 214), outline=C_CORE, lw=0.4)
        P.rect(x - 2.9, 46.6, x + 2.9, 80.0, fill=(250, 242, 228), outline=C_CORE, lw=0.4)
        for fx in (-1.0, 0.0, 1.0):
            P.line([(x + fx, 47.2), (x + fx, 79.4)], (222, 196, 180), 0.18, joint=False)
        P.rect(x - 4.2, 80.0, x + 4.2, 82.6, fill=(244, 232, 214), outline=C_CORE, lw=0.4)
    # 중앙 제목 판
    P.rect(172.0, 46.0, 248.0, 79.5, fill=(255, 250, 238), outline=C_CORE, lw=0.8)
    P.rect(173.8, 47.8, 246.2, 77.7, outline=C_CORE, lw=0.3)
    P.text_c(cx, 60.2, "ROMAN CONCRETE", fnt("en", 8.6 / 0.71), C_CORE_T)
    P.text_c(cx, 67.6, "로마 콘크리트", fnt("b", 4.6), C_INK)
    # 리본(슬로건)
    P.poly([(150.0, 71.0), (270.0, 71.0), (270.0, 78.6), (150.0, 78.6)], fill=(250, 226, 214), outline=C_CORE, lw=0.5)
    P.text_c(cx, 76.4, "갈라져도 물을 만나 스스로 메우는 콘크리트", fnt("b", 3.6), C_CORE_T)
    # 계단
    P.rect(130.0, 82.6, 290.0, 87.4, fill=(246, 234, 218), outline=C_CORE, lw=0.5)
    P.rect(126.5, 87.4, 293.5, 92.0, fill=(240, 224, 208), outline=C_CORE, lw=0.5)


# ───────────────────────── 배치 설정(mm) ─────────────────────────
CORE_W = 80.0                       # 셀 마름모 화면 폭
CORE_HW = CORE_W / 2.0
CORE_S = CORE_W / SQ3               # 셀 변 길이(화면)
CORE_HH = CORE_S / 2.0              # 반 셀 높이
CORE_X0 = 18.0                      # 체인 왼끝
CORE_Y0 = 190.0                     # 첫 셀 중심 y
NCELL = 7                           # 셀 7개: 1·1·1·2·1·1(뜨거운 혼합 2셀), 마지막 행은 1셀


def cell_center(k):
    return (CORE_X0 + CORE_HW + (CORE_HW if k % 2 else 0.0), CORE_Y0 + k * CORE_HH)


def cell_verts(k):
    cx, cy = cell_center(k)
    return {"T": (cx, cy - CORE_HH), "R": (cx + CORE_HW, cy), "B": (cx, cy + CORE_HH), "L": (cx - CORE_HW, cy)}


NOTCH_X = CORE_X0 + CORE_W          # 오른쪽 열 셀의 위·아래 꼭짓점 x(톱니 안쪽 오목점)
NOTCH_Y = CORE_Y0 + 4 * CORE_HH     # 강이 꺾이는 톱니 행(k=3 아래·k=5 위 꼭짓점)

RIVER_W = 9.5
HUG = 24.0                          # 강 중심선과 코어 외곽선의 수직 간격
RIVER_A = (NOTCH_X + 2.0 * HUG, NOTCH_Y)     # 직각으로 꺾이는 꼭짓점(강이 코어 톱니에 안긴다)

ARENA_R = 100.0                     # 팔각 외접 반지름
ARENA_XL = 236.0                    # 받침 왼쪽 수직 변 x
ARENA_CY = 305.0
ARENA_CX = ARENA_XL + 1.1316 * ARENA_R


def river_centerline(L2=96.0, L3=150.0):
    """오른쪽 위 액자 밖 → ↙ → A(직각) → ↘ → 직각 → ↙ → 바다. 모두 지면 축 ±30°."""
    t0 = (448.0 - RIVER_A[0]) / C30
    start = (RIVER_A[0] + C30 * t0, RIVER_A[1] - 0.5 * t0)
    pts = [start, RIVER_A]
    pts += walk(RIVER_A, [("SE", L2), ("SW", L3)])[1:]
    return pts


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


# ───────────────────────── 1 아레나(콜로세움) — LocalBanana 참조 디오라마 형태 ─────────────────────────
KE = 0.57735
TRAV = (208, 186, 144)
TRAV_L = (224, 204, 164)
TRAV_D = (176, 152, 114)
ARCH_IN = (104, 78, 50)
TUFF = (166, 136, 102)
CONC = (170, 164, 150)


def draw_arena(L):
    CX, CY = ARENA_CX, ARENA_CY
    iso = Iso(L, CX, CY)
    R = ARENA_R
    oct_pl = [(R * math.cos(math.radians(22.5 + 45 * k)), R * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
    RS = R / 89.3
    oct_sc = [iso.p(X, Y) for X, Y in oct_pl]
    T = 7.0
    # ── 받침(흙 단면): 앞쪽 세 변(SE·정면·SW)만 측면이 보인다
    side_cols = {7: (92, 68, 44), 0: (114, 88, 56), 1: (132, 102, 66)}
    for k in (7, 0, 1):
        a, b = oct_sc[k], oct_sc[(k + 1) % 8]
        L.poly([a, b, (b[0], b[1] + T), (a[0], a[1] + T)], fill=side_cols[k], outline=(70, 50, 32), lw=0.25)
        L.poly([a, b, (b[0], b[1] + 1.8), (a[0], a[1] + 1.8)], fill=GRASS)
        for j in (0.38, 0.62):
            L.line([(a[0], a[1] + T * j + 1.0), (b[0], b[1] + T * j + 1.0)], shade(side_cols[k], 0.8), 0.18, joint=False)
    # 콘크리트 기초 고리 절개(받침 정면 변 왼쪽 부분): 흙 속에 회색 콘크리트 띠가 드러난다
    a, b = oct_sc[0], oct_sc[1]
    # 정면 변은 a(오른쪽)→b(왼쪽): 왼쪽 36~66% 구간에 절개 창
    def lerp(p, q, t):
        return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
    w0, w1 = lerp(a, b, 0.40), lerp(a, b, 0.66)
    L.poly([w0, w1, (w1[0], w1[1] + T), (w0[0], w0[1] + T)], fill=(150, 124, 92), outline=(70, 50, 32), lw=0.25)
    L.poly([(w0[0], w0[1] + 2.6), (w1[0], w1[1] + 2.6), (w1[0], w1[1] + 6.4), (w0[0], w0[1] + 6.4)], fill=CONC, outline=(104, 98, 88), lw=0.2)
    for i in range(14):
        tt = rnd()
        pp = lerp(w0, w1, tt)
        L.ell(pp[0], pp[1] + 3.2 + rnd() * 2.6, 0.45, 0.4, fill=(214, 206, 188))
    # 윗면(광장)
    L.poly(oct_sc, fill=(186, 168, 138), outline=(70, 50, 30), lw=0.5)
    # 돌 포장 결: ±30° 짧은 선
    for i in range(170):
        X = (rnd() * 2 - 1) * 80
        Y = (rnd() * 2 - 1) * 80
        if abs(X) + abs(Y) > 112 or X * X + Y * Y < 64 * 64:
            continue
        d = 1 if rnd() < 0.5 else 0
        x0, y0 = iso.p(X, Y)
        dx, dy = (C30, 0.5) if d else (-C30, 0.5)
        ln = 1.6 + rnd() * 2.6
        L.line([(x0, y0), (x0 + dx * ln, y0 + dy * ln)], (166, 150, 120), 0.2, joint=False)
    # 포장 앞마당(고리 둘레의 밝은 띠)
    iso.ell(0, 0, 0, 68.5, fill=(210, 197, 170), ol=(160, 144, 114), lw=0.25)

    # ── 광장 뒤쪽(북서·북동) 소품: 사이프러스·올리브·작은 신전 폐허
    for (X, Y, h) in [(-64, -44, 17), (-56, -56, 14), (-74, -34, 15), (18, -76, 15), (46, -62, 13)]:
        x, y = iso.p(X, Y)
        cypress(L, x, y, h)
    olx, oly = iso.p(-70, 20)
    olive(L, olx, oly, 4.6)
    # 뒤 오른쪽 작은 신전 폐허(4기둥 + 박공 조각)
    tx, ty = iso.p(4, -58)
    iso2 = Iso(L, tx, ty)
    iso2.box(0, 0, 0, 20, 14, 2.4, (TRAV_L, TRAV, TRAV_D), ol=(130, 108, 78), lw=0.15)
    for i in range(4):
        px, py = iso2.p(2.5 + i * 5.2, 13.0, 2.4)
        L.rect(px - 0.9, py - 11.5, px + 0.9, py, fill=(240, 228, 202), outline=(150, 128, 94), lw=0.16)
        L.rect(px - 1.4, py - 12.6, px + 1.4, py - 11.5, fill=(230, 216, 188), outline=(150, 128, 94), lw=0.14)
    px0, py0 = iso2.p(1.0, 13.0, 2.4)
    px1, py1 = iso2.p(18.0, 13.0, 2.4)
    L.poly([(px0, py0 - 13.0), (px1, py1 - 13.0), (px1, py1 - 12.0), (px0, py0 - 12.0)], fill=(226, 210, 178), outline=(150, 128, 94), lw=0.16)
    L.poly([(px0, py0 - 13.0), ((px0 + px1) / 2.0, (py0 + py1) / 2.0 - 17.0), (px1, py1 - 13.0)], fill=(232, 218, 188), outline=(150, 128, 94), lw=0.16)

    # ── 링: 화면 타원 중심 = 받침 중심. 평면 원(화면 비 0.577).
    RCx, RCy = CX, CY

    def ep(a, t, z=0.0):
        r = math.radians(t)
        return (RCx + a * math.cos(r), RCy + KE * a * math.sin(r) - z)

    A_OUT, A_IN2, A_RIM, A_FLOOR = 74.0, 64.2, 53.9, 31.1
    H_RIM, H_FLOOR = 24.0, 2.0
    # 관람석(카베아): 바깥 테두리에서 아레나 바닥까지 계단형 동심 타원(안으로 갈수록 낮다)
    nt = 6
    for i in range(nt + 1):
        f = i / nt
        a = A_RIM - (A_RIM - A_FLOOR) * f
        z = H_RIM - (H_RIM - H_FLOOR) * f
        col = (226, 208, 170) if i % 2 == 0 else (206, 186, 148)
        cxz, cyz = ep(0, 0, z)
        L.ell(cxz, cyz, a, KE * a, fill=col, outline=(150, 126, 92), lw=0.2)
    # 방사 통로(보미토리아)
    for t in range(0, 360, 15):
        p0 = ep(A_RIM - 1.0, t, H_RIM)
        p1 = ep(A_FLOOR + 1.0, t, H_FLOOR)
        L.line([p0, p1], (150, 126, 92), 0.16, joint=False)
    # 아레나 바닥: 오른쪽 반 나무 바닥 + 왼쪽 반 하이포게움 노출
    fx, fy = ep(0, 0, H_FLOOR)
    L.ell(fx, fy, A_FLOOR, KE * A_FLOOR, fill=(120, 94, 64), outline=(78, 58, 38), lw=0.35)
    L.pie(fx, fy, A_FLOOR - 0.4, KE * (A_FLOOR - 0.4), 270, 90, fill=(180, 142, 96))
    # 나무 바닥 판자(오른쪽 반): 지면 +X축(화면 ↘ 30°) 방향 줄을 아레나 타원 안으로 자른다
    iso_p = Iso(L, fx, fy)
    Rf = (A_FLOOR - 0.8) / 1.2247
    for j in range(-9, 10):
        y0 = j * 2.6
        if abs(y0) >= Rf - 0.5:
            continue
        xe = math.sqrt(Rf * Rf - y0 * y0)
        xs = max(y0 + 0.5, -xe)
        if xs < xe - 0.8:
            iso_p.line3([(xs, y0, 0.0), (xe, y0, 0.0)], (150, 112, 74), 0.14)
    # 하이포게움 미로(왼쪽 반): 낮은 벽 상자들
    iso_f = Iso(L, fx, fy)
    walls = [(-17, -12, 8, -9.4), (-17, -4, 8, -1.4), (-17, 4, 8, 6.6), (-17, 12, 8, 14.6),
             (-14, -12, -11.4, 14), (-6, -12, -3.4, 14), (2, -12, 4.6, 14)]
    for (X0, Y0, X1, Y1) in walls:
        # 왼쪽 반원 안에 드는 것만 (평면 반지름 24.5 안)
        cx_, cy_ = (X0 + X1) / 2.0, (Y0 + Y1) / 2.0
        if cx_ * cx_ + cy_ * cy_ > 21.5 ** 2:
            continue
        iso_f.box(X0, Y0, 0, X1, Y1, 2.4, ((206, 184, 148), (176, 152, 118), (140, 116, 86)), ol=(90, 70, 46), lw=0.14)
    # 하이포게움/나무 바닥 경계: 중앙 세로선(평면 Y축 방향 아님 — 화면 수직)
    L.line([(fx, fy - KE * (A_FLOOR - 0.4)), (fx, fy + KE * (A_FLOOR - 0.4))], (78, 58, 38), 0.3, joint=False)

    # 안쪽 아케이드 고리(앞쪽 반): 외벽이 낮아진 틈으로 드러나는 두 번째 고리
    def ring_poly(a_list_bottom, a_list_top):
        return a_list_bottom + a_list_top[::-1]

    def band(a, t0, t1, ztop, zb=0.0, step=3.0, fill=TRAV, ol=None, lw=0.2, shadef=True):
        """링 외면/내면 띠: t0→t1, 아래 높이 zb, 위 높이 ztop(t)"""
        n = max(2, int(abs(t1 - t0) / step))
        ts = [t0 + (t1 - t0) * i / n for i in range(n + 1)]
        for i in range(n):
            ta, tb = ts[i], ts[i + 1]
            tm = (ta + tb) / 2.0
            f = (0.93 + 0.14 * math.cos(math.radians(tm - 150.0))) if shadef else 1.0
            c = shade(fill, f)
            pts = [ep(a, ta, zb), ep(a, tb, zb), ep(a, tb, ztop(tb)), ep(a, ta, ztop(ta))]
            L.poly(pts, fill=c)
        top = [ep(a, t, ztop(t)) for t in ts]
        bot = [ep(a, t, zb) for t in ts]
        if ol:
            L.line(top, ol, lw)
            L.line(bot, ol, lw)
        return ts

    def arches(a, t0, t1, rows, ztop, hw=2.3, pitch=7.5, col=ARCH_IN, a_scale=1.0):
        """rows = [(z0, z1)] 각 층의 아치 개구부. ztop 아래에서만."""
        plan_r = a / 1.2247
        ha = plan_r * math.radians(hw)
        t = t0 + pitch / 2.0 if t1 > t0 else t0 - pitch / 2.0
        step = pitch if t1 > t0 else -pitch
        while (t < t1 - 1e-6) if t1 > t0 else (t > t1 + 1e-6):
            for (z0, z1) in rows:
                if z1 + ha + 1.5 > ztop(t):
                    continue
                pts = [ep(a, t - hw, z0), ep(a, t + hw, z0), ep(a, t + hw, z1)]
                for i in range(1, 9):
                    sx = 1 - 2 * i / 9.0
                    pts.append(ep(a, t + hw * sx, z1 + ha * math.sqrt(1 - sx * sx)))
                pts.append(ep(a, t - hw, z1))
                L.poly(pts, fill=col)
            t += step

    # (a) 안쪽 아케이드 고리: 앞쪽 t=15..165, 높이 22 안팎으로 들쭉날쭉
    def h_in(t):
        prof = [(15, 14), (30, 22), (48, 18), (62, 22), (78, 12), (92, 22), (110, 20), (128, 24), (145, 22), (165, 24)]
        for i in range(len(prof) - 1):
            if prof[i][0] <= t <= prof[i + 1][0]:
                return prof[i][1] if (t - prof[i][0]) < (prof[i + 1][0] - prof[i][0]) * 0.6 else prof[i + 1][1]
        return 20

    band(A_IN2, 15, 165, h_in, fill=(206, 184, 146), ol=(130, 106, 76), lw=0.25)
    arches(A_IN2, 15, 165, [(1.5, 8.5), (12.5, 18.0)], h_in, hw=2.2, pitch=8.0)
    # 윗면 얇은 띠
    ts = [15 + 3 * i for i in range(51)]
    L.poly([ep(A_IN2, t, h_in(t)) for t in ts] + [ep(A_IN2 - 4, t, h_in(t)) for t in ts[::-1]], fill=TRAV_L, outline=(130, 106, 76), lw=0.2)

    # (b) 뒤 왼쪽만 남은 4층 외벽 조각: 안쪽면(t 180→262), 윗면, 바깥면(t 120→180)
    def h_tall(t):
        prof = [(120, 26), (128, 26), (128.1, 38), (140, 38), (140.1, 49), (152, 49), (152.1, 62), (205, 62), (232, 60), (262, 34)]
        for i in range(len(prof) - 1):
            if prof[i][0] <= t <= prof[i + 1][0]:
                f = (t - prof[i][0]) / max(1e-6, (prof[i + 1][0] - prof[i][0]))
                return prof[i][1] + (prof[i + 1][1] - prof[i][1]) * f
        return 30

    band(A_OUT - 8, 180, 262, h_tall, zb=H_RIM, fill=(196, 174, 136), ol=(120, 98, 70), lw=0.25)
    arches(A_OUT - 8, 180, 262, [(H_RIM + 3, H_RIM + 10), (H_RIM + 15, H_RIM + 22), (H_RIM + 27, H_RIM + 34)], h_tall, hw=2.1, pitch=7.5, col=(92, 68, 44))
    tsb = [180 + 2 * i for i in range(42)]
    L.poly([ep(A_OUT, t, h_tall(t)) for t in tsb] + [ep(A_OUT - 8, t, h_tall(t)) for t in tsb[::-1]], fill=TRAV_L, outline=(120, 98, 70), lw=0.22)
    band(A_OUT, 120, 180, h_tall, fill=TRAV, ol=(120, 98, 70), lw=0.28)
    arches(A_OUT, 120, 180, [(2, 10), (15.5, 23.5), (29, 37), (42, 50)], h_tall, hw=2.4, pitch=7.5)
    tsc = [120 + 2 * i for i in range(31)]
    L.poly([ep(A_OUT, t, h_tall(t)) for t in tsc] + [ep(A_OUT - 8, t, h_tall(t)) for t in tsc[::-1]], fill=TRAV_L, outline=(120, 98, 70), lw=0.22)
    # 조각의 앞쪽 끝 단면(절단면): 콘크리트 심이 드러나는 면
    pa, pb = ep(A_OUT, 120, 0), ep(A_OUT - 8, 120, 0)
    L.poly([pa, pb, ep(A_OUT - 8, 120, 26), ep(A_OUT, 120, 26)], fill=CONC, outline=(104, 98, 88), lw=0.2)

    # (c) 무너진 앞쪽 고리: t=-8..120, 지그재그 파손 윤곽, 틈으로 안쪽 아케이드가 보인다
    def h_front(t):
        prof = [(-8, 6), (4, 6), (4.1, 14), (14, 14), (14.1, 22), (26, 22), (26.1, 10), (40, 10), (40.1, 0), (56, 0), (56.1, 18), (66, 18),
                (66.1, 26), (76, 26), (76.1, 12), (84, 12), (84.1, 0), (96, 0), (96.1, 20), (108, 20), (108.1, 30), (120, 26)]
        for i in range(len(prof) - 1):
            if prof[i][0] <= t <= prof[i + 1][0]:
                return prof[i][1] + (prof[i + 1][1] - prof[i][1]) * (t - prof[i][0]) / max(1e-6, prof[i + 1][0] - prof[i][0])
        return 6

    # 높이 0 구간은 그리지 않기 위해 조각별로 처리
    segs = [(-8, 40), (56, 84), (96, 120)]
    for (t0, t1) in segs:
        hh = lambda t: max(0.5, h_front(t))
        band(A_OUT, t0, t1, hh, fill=TRAV, ol=(120, 98, 70), lw=0.28)
        arches(A_OUT, t0, t1, [(1.5, 6.5), (13.0, 18.5), (24.0, 29.0)], hh, hw=2.4, pitch=7.5)
        tsd = [t0 + (t1 - t0) * i / max(2, int((t1 - t0) / 2.5)) for i in range(max(2, int((t1 - t0) / 2.5)) + 1)]
        L.poly([ep(A_OUT, t, hh(t)) for t in tsd] + [ep(A_OUT - 8, t, hh(t)) for t in tsd[::-1]], fill=TRAV_L, outline=(120, 98, 70), lw=0.22)
    # 콘크리트 절개 창(앞 고리 한 곳): 방사 볼트(콘크리트)·응회암 벽·석회화 겉면 세 겹
    tc0, tc1 = 58.0, 82.0
    top_z = 18.0
    pts_o = [ep(A_OUT, t, 0) for t in (tc0, tc1)] + [ep(A_OUT, t, top_z) for t in (tc1, tc0)]
    L.poly(pts_o, fill=CONC, outline=(100, 94, 84), lw=0.3)
    pts_t = [ep(A_OUT - 8, t, 0) for t in (tc0, tc1)] + [ep(A_OUT - 8, t, top_z) for t in (tc1, tc0)]
    L.poly([ep(A_OUT, tc0, 0), ep(A_OUT, tc0 + 7, 0), ep(A_OUT, tc0 + 7, top_z), ep(A_OUT, tc0, top_z)], fill=TRAV, outline=(120, 98, 70), lw=0.2)
    L.poly([ep(A_OUT, tc0 + 7, 0), ep(A_OUT, tc0 + 14, 0), ep(A_OUT, tc0 + 14, top_z), ep(A_OUT, tc0 + 7, top_z)], fill=TUFF, outline=(100, 80, 56), lw=0.2)
    for i in range(26):
        tt = tc0 + 14 + rnd() * (tc1 - tc0 - 14)
        zz = 1.5 + rnd() * (top_z - 3)
        px, py = ep(A_OUT, tt, zz)
        L.ell(px, py, 0.5, 0.42, fill=(226, 218, 200))

    # ── 앞 광장 소품: 노점·기둥 폐허·작은 개선문 조각·올리브·사이프러스·사람
    for (X, Y, h) in [(-74, 34, 16), (-70, 40, 13), (50, 56, 15)]:
        x, y = iso.p(X, Y)
        cypress(L, x, y, h)
    for (X, Y) in [(-46, 60), (74, 28), (14, 76)]:
        x, y = iso.p(X, Y)
        olive(L, x, y, 4.2)
    for i, (X, Y) in enumerate([(-66, 12), (-70, 8), (-62, 16), (46, 66), (40, 70), (30, 74)]):
        x, y = iso.p(X, Y)
        column_ruin(L, x, y, 6.5 - (i % 3) * 1.5, 1.5, broken=(i % 3 == 2))
    # 작은 개선문 조각(앞 왼쪽)
    ax_, ay_ = iso.p(-50, 52)
    iso3 = Iso(L, ax_, ay_)
    iso3.box(0, 0, 0, 3, 8, 9, (TRAV_L, TRAV, TRAV_D), ol=(130, 108, 78), lw=0.15)
    iso3.box(10, 0, 0, 13, 8, 9, (TRAV_L, TRAV, TRAV_D), ol=(130, 108, 78), lw=0.15)
    iso3.box(0, 0, 9, 13, 8, 11.5, (TRAV_L, TRAV, TRAV_D), ol=(130, 108, 78), lw=0.15)
    # 노점(차양): 앞 오른쪽
    for (X, Y, c) in [(30, 66, (214, 86, 66)), (-24, 72, (240, 236, 224))]:
        sx, sy = iso.p(X, Y)
        L.poly([(sx - 3.6, sy - 3.2), (sx + 3.6, sy - 3.2), (sx + 4.4, sy - 5.4), (sx - 2.8, sy - 5.4)], fill=c, outline=(120, 90, 60), lw=0.15)
        L.rect(sx - 3.2, sy - 3.2, sx - 2.8, sy, fill=(120, 90, 60))
        L.rect(sx + 3.0, sy - 3.2, sx + 3.4, sy, fill=(120, 90, 60))
    # 사람들: 광장 앞·노점 옆·폐허 옆 세 무리, 키 약 5.6mm
    cols = [(150, 70, 52), (214, 196, 170), (92, 120, 150), (190, 150, 70), (236, 232, 222)]
    groups = [(8, 74, 5), (-40, 66, 4), (46, 58, 3), (-64, 22, 2)]
    for gx, gy, n in groups:
        for i in range(n):
            x, y = iso.p(gx + (rnd() - 0.5) * 16, gy + (rnd() - 0.5) * 8)
            person(L, x, y, 5.6, cols[(i + int(gx)) % 5])
    return {"좌측변중점": (CX - 1.1316 * R, CY), "링왼": ep(A_OUT, 150, 40), "앞변": (CX, CY + 0.6533 * R)}


# ───────────────────────── Core: 로마 콘크리트 제작 과정(신문식 셀 체인) ─────────────────────────
STEP_NAMES = ["재료 준비", "마른 혼합", "물 붓기", "뜨거운 혼합", "타설·다짐", "굳기·석회 알갱이 형성"]
STEP_BODY = [["생석회·화산재·굵은 화산암", "골재를 모아 둔다"],
             ["생석회와 화산재를", "물 없이 먼저 섞는다"],
             ["마른 가루에 물을 붓는다", "육상은 민물, 항구만 바닷물"],
             ["물과 만난 생석회가 끓으며", "열을 낸다 → 알갱이가 남음"],
             ["거푸집에 되직한 반죽을", "다져 넣는다(붓지 않음)"],
             ["굳은 속에 흰 알갱이가 박힌다", "↓ 아래 확대 창으로"]]
CELL_STEP = [0, 1, 2, 3, 3, 4, 5]                 # 셀 → 단계 인덱스(뜨거운 혼합 2셀)
STEP_CELL = [0, 1, 2, 3, 5, 6]                    # 단계가 시작되는 셀
FLOOR_TXT = [("① 재료 모으기", "생석회·화산재·골재"), ("② 마른 채 섞기", "물 없이 먼저"), ("③ 물 붓기", "육상 민물·항구 바닷물"),
             ("④ 뜨거운 혼합", "물과 만난 생석회가 끓음"), ("⑤ 열이 알갱이를 남김", "흰 석회 알갱이"),
             ("⑥ 거푸집에 다져 넣기", "붓지 않는다"), ("⑦ 굳은 단면", "알갱이는 확대 창으로")]
BOARD_H = 15.0                                    # 단계 간판 높이(mm)
CELL_CREAM = (250, 238, 210)
CELL_SEAM = (218, 198, 164)
BOARD_FACE = (240, 220, 178)
BOARD_TOP = (200, 60, 70)


def worker(L, x, y, h=14.5, tunic=(176, 96, 60), tool=None, facing=1):
    """작업자 실루엣(키 h). tool: hoe/rammer/bucket/point/None"""
    L.ell(x + 0.4, y + 0.2, h * 0.24, h * 0.08, fill=(110, 90, 62, 150))
    L.poly([(x - h * 0.13, y), (x - h * 0.02, y), (x - h * 0.02, y - h * 0.42), (x - h * 0.14, y - h * 0.42)], fill=(98, 76, 52))
    L.poly([(x + h * 0.02, y), (x + h * 0.13, y), (x + h * 0.14, y - h * 0.42), (x + h * 0.02, y - h * 0.42)], fill=(98, 76, 52))
    L.poly([(x - h * 0.19, y - h * 0.40), (x + h * 0.19, y - h * 0.40), (x + h * 0.15, y - h * 0.76), (x - h * 0.15, y - h * 0.76)], fill=tunic, outline=shade(tunic, 0.7), lw=0.15)
    L.ell(x, y - h * 0.88, h * 0.12, h * 0.12, fill=(228, 188, 152), outline=(150, 112, 84), lw=0.12)
    if tool == "hoe":
        L.line([(x + h * 0.15, y - h * 0.62), (x + h * 0.55 * facing, y - h * 0.12)], (110, 80, 50), 0.4, joint=False)
        L.line([(x + h * 0.55 * facing, y - h * 0.12), (x + h * 0.7 * facing, y - h * 0.16)], (90, 90, 96), 0.7, joint=False)
    elif tool == "rammer":
        L.line([(x + h * 0.16, y - h * 0.9), (x + h * 0.3 * facing, y - h * 0.05)], (110, 80, 50), 0.45, joint=False)
        L.rect(x + h * 0.3 * facing - 1.2, y - 1.2, x + h * 0.3 * facing + 1.2, y, fill=(96, 96, 100))
    elif tool == "bucket":
        L.poly([(x + h * 0.2, y - h * 0.55), (x + h * 0.42, y - h * 0.55), (x + h * 0.38, y - h * 0.3), (x + h * 0.24, y - h * 0.3)], fill=(150, 112, 74), outline=(96, 70, 44), lw=0.14)
    elif tool == "point":
        L.line([(x + h * 0.17, y - h * 0.66), (x + h * 0.5 * facing, y - h * 0.86)], tunic, 0.8, joint=False)


def steam(L, x, y, n=4, r=2.6):
    with_alpha = (255, 255, 255, 170)
    for i in range(n):
        L.ell(x + (i % 2) * 2.2 - 1.0, y - i * 2.8, r * (1.0 - 0.1 * i), r * 0.8 * (1.0 - 0.1 * i), fill=with_alpha, outline=(220, 214, 204, 200), lw=0.15)


def pile(L, x, y, r, h, col, dots=None):
    """더미: (x,y) 바닥 중심, 반지름 r, 높이 h"""
    L.ell(x + 0.6, y + 0.2, r * 1.02, r * 0.34, fill=(120, 98, 64, 120))
    L.poly([(x - r, y), (x - r * 0.45, y - h * 0.7), (x, y - h), (x + r * 0.5, y - h * 0.65), (x + r, y)], fill=col, outline=shade(col, 0.68), lw=0.2)
    L.pie(x, y, r, r * 0.34, 0, 180, fill=shade(col, 0.9))
    if dots:
        for i in range(8):
            L.ell(x - r * 0.6 + rnd() * r * 1.2, y - h * 0.15 - rnd() * h * 0.55, 0.5, 0.42, fill=dots)


def pill(L, x, y, text, M, ax_u=0.0):
    """기계 알약(갈색, 밝은 황토 글자): 벽면 평면 위. (x,y)는 알약 왼쪽 아래 모서리의 화면 위치"""
    f = fnt("s", 2.5)
    w = tw(text, f) + 2.4
    h = 4.6
    pf = Flat(w + 1, h + 1, (210, 175, 138))
    pf.d.rounded_rectangle([2, 2, 2 + w * KD, 2 + h * KD], radius=int(h * KD / 2), fill=(127, 91, 77, 255))
    pf.text(1.2, 3.3, text, f, (214, 180, 142))
    (a, b), (c, d) = M
    affine_paste(L, pf, M, x - b * h, y - d * h)
    return w


def draw_board(L, edge_a, edge_b, wall, height, name, body, num, badge_end, title_style=False, en=None):
    """등각 수직 보드. edge_a→edge_b: 셀 뒤 가장자리(화면 mm). wall: 'NW'(YZ벽, 글줄 ↗) 또는 'NE'(XZ벽, 글줄 ↘).
    badge_end: 번호 배지를 달 쪽('a' 또는 'b')."""
    ax_, ay_ = edge_a
    bx_, by_ = edge_b
    # 보드 면(평행사변형): 아래 변은 셀 가장자리, 위 변은 height만큼 위
    face = [(ax_, ay_), (bx_, by_), (bx_, by_ - height), (ax_, ay_ - height)]
    L.poly(face, fill=BOARD_FACE, outline=(120, 70, 50), lw=0.3)
    # 윗면(얇은 두께)과 끝 단면
    th = 1.6
    L.poly([(ax_, ay_ - height), (bx_, by_ - height), (bx_ + 0.0, by_ - height - th), (ax_, ay_ - height - th)], fill=BOARD_TOP)
    M = M_WALL_UP if wall == "NW" else M_WALL_DN
    # 글자: 보드 왼쪽(화면 x가 작은 쪽)에서 시작. 판 위 여백 1.6mm
    if wall == "NW":
        # 기준선 ↗: 왼쪽 끝이 아래쪽 점. 시작점 = 보드 왼쪽 아래 모서리 위
        sx, sy = ax_ if ax_ < bx_ else bx_, (ay_ if ax_ < bx_ else by_)
    else:
        sx, sy = ax_ if ax_ < bx_ else bx_, (ay_ if ax_ < bx_ else by_)
    inset = 2.0
    # 평면 좌표에서 u=inset, v=(height - 위 여백)부터
    usable = CORE_S - 2 * inset - (11.0 if not title_style else 0.0)
    lines = []
    base_v = 4.6
    if title_style:
        f = Flat(CORE_S * 2, height + 2, C_CORE_T)
        f.text(inset + 1.0, 10.6, en or "CORE", fnt("en", 8.2 / 0.71), C_CORE_T)
        f.text(inset + 1.0 + tw(en or "CORE", fnt("en", 8.2 / 0.71)) + 2.4, 10.6, name, fnt("b", 4.4), C_INK)
        # 평면 판의 (0,0) = 보드 왼쪽 위 → 화면: 왼쪽 아래 점에서 height 만큼 위
        (a, b), (c, d) = M
        affine_paste(L, f, M, sx, sy - height)
    else:
        f = Flat(CORE_S, height + 2, C_CORE_T)
        x_start = inset + (11.0 if badge_end == "a" else 0.0)

        def fit(txt, kind, em):
            w0 = tw(txt, fnt(kind, em))
            return em if w0 <= usable else em * usable / w0

        em_n = fit(name, "b", 3.5)
        f.text(x_start, 4.2, name, fnt("b", em_n), C_CORE_T)
        for i, ln in enumerate(body):
            em_b = fit(ln, "m", 2.7)
            f.text(x_start, 4.2 + 1.0 + 3.1 * (i + 1), ln, fnt("m", em_b), (64, 46, 36))
        affine_paste(L, f, M, sx, sy - height)
    # 번호 배지(타원 10.5×13): 바깥쪽 끝(배지는 보드 끝에 걸쳐서)
    if num is not None:
        if badge_end == "a":
            bxm, bym = ax_, ay_ - height * 0.5
        else:
            bxm, bym = bx_, by_ - height * 0.5
        inward = 5.25 if (bxm - 20 < 0 or True) else 0
        # 왼쪽 끝은 안쪽으로 당겨 x≥18을 지킨다
        if badge_end == "a":
            bxm += 5.25
        else:
            bxm -= 5.25
        L.ell(bxm, bym, 5.25, 6.5, fill=C_CORE, outline=(255, 255, 255), lw=0.5)
        L.text_c(bxm, bym + 2.9, str(num), fnt("b", 7.6), (255, 255, 255))


def floor_text(L, X, Y, lines, iso, em=2.2):
    """바닥에 눕힌 설명 글(기준선 +X ↘, 글자 위 = −Y ↗). (X,Y)는 첫 줄 기준선 왼쪽."""
    x0, y0 = iso.p(X, Y)
    for i, (txt, kind, col) in enumerate(lines):
        # 줄이 바뀌면 평면 +Y 방향(화면 ↙)으로 내려간다(글자 '아래')
        xx, yy = iso.p(X, Y + 3.4 * i)
        iso_text(L, txt, fnt(kind, em), col, M_FLOOR_SE, xx, yy)


def floor_arrow(iso, L, X, Y, direction, col=(86, 104, 58)):
    """바닥에 눕힌 올리브 화살표(길이 6.4, 폭 3.2). direction: 'X'(↘ +X) 또는 'Y'(↙ +Y). (X,Y)는 화살표 중심."""
    if direction == "X":
        pts = [(X - 3.2, Y - 0.55), (X + 0.6, Y - 0.55), (X + 0.6, Y - 1.6), (X + 3.2, Y), (X + 0.6, Y + 1.6), (X + 0.6, Y + 0.55), (X - 3.2, Y + 0.55)]
    else:
        pts = [(X - 0.55, Y - 3.2), (X - 0.55, Y + 0.6), (X - 1.6, Y + 0.6), (X, Y + 3.2), (X + 1.6, Y + 0.6), (X + 0.55, Y + 0.6), (X + 0.55, Y - 3.2)]
    iso.poly3([(a, b, 0.0) for a, b in pts], fill=col, ol=(60, 76, 40), lw=0.15)


def draw_core(L):
    """셀 7개 체인. 슬래브 하나로 합친 윤곽, 앞쪽 바깥 변에만 흙 측면, 내부는 이음선. 간판·번호 배지·기계 알약·작업자·바닥 글·바닥 화살표."""
    S = CORE_S
    T = 5.0
    verts = [cell_verts(k) for k in range(NCELL)]
    # ── 제목 보드(첫 두 셀의 뒤쪽 NE 변 뒤에 더 높게): 평면 −Y로 12 물린 선
    t0 = verts[0]["T"]
    off = (C30 * 12.0, -0.5 * 12.0)
    ta = (t0[0] + off[0], t0[1] + off[1])
    tb = (ta[0] + C30 * 1.7 * S, ta[1] + 0.5 * 1.7 * S)
    draw_board(L, ta, tb, "NE", 16.0, "로마 콘크리트 제작 과정", [], None, "b", title_style=True, en="CORE")
    # ── 슬래브 흙 측면(앞쪽 바깥 변)
    for k in range(NCELL):
        v = verts[k]
        if k % 2 == 0:       # 왼쪽 열: 남서 변
            a, b = v["L"], v["B"]
            L.poly([a, b, (b[0], b[1] + T), (a[0], a[1] + T)], fill=(134, 104, 66), outline=(80, 58, 36), lw=0.2)
            L.poly([a, b, (b[0], b[1] + 1.2), (a[0], a[1] + 1.2)], fill=GRASS)
        if k % 2 == 1 or k == NCELL - 1:       # 오른쪽 열: 남동 변(마지막 셀도 앞 오른쪽 변이 드러남)
            a, b = v["B"], v["R"]
            L.poly([a, b, (b[0], b[1] + T), (a[0], a[1] + T)], fill=(100, 76, 48), outline=(80, 58, 36), lw=0.2)
            L.poly([a, b, (b[0], b[1] + 1.2), (a[0], a[1] + 1.2)], fill=GRASS)
    # ── 슬래브 윗면(셀 합집합 윤곽) + 내부 이음선
    outline = [(60 - 0.0, 0)]  # placeholder
    xs0 = CORE_X0
    TL = verts[0]["T"]
    chain = []
    # 오른쪽 경계(위→아래)
    chain.append(verts[0]["T"])
    for k in range(0, NCELL - 1, 2):
        if k % 2 == 0 and k + 1 < NCELL:
            pass
    right = [verts[0]["T"], verts[0]["R"]]
    for k in range(1, NCELL, 2):
        right += [verts[k]["R"], verts[k]["B"]]
    right = [verts[0]["T"], verts[0]["R"]]
    for k in range(1, NCELL, 2):
        right.append(verts[k]["R"])
        right.append(verts[k]["B"])
    left_up = []
    last = verts[NCELL - 1]
    right.append(last["B"])
    for k in range(NCELL - 1, -1, -2):
        left_up.append(verts[k]["L"])
        left_up.append(verts[k]["T"])
    outline = right + left_up[:-1]
    L.poly(outline, fill=CELL_CREAM)
    for k in range(NCELL - 1):
        a = verts[k]
        b = verts[k + 1]
        if k % 2 == 0:
            L.line([a["R"], a["B"]], CELL_SEAM, 0.25, joint=False)
        else:
            L.line([a["B"], a["L"]], CELL_SEAM, 0.25, joint=False)
    L.line(outline + [outline[0]], C_CORE, 0.55)
    # ── 셀별 내용(뒤에서 앞으로)
    for k in range(NCELL):
        v = verts[k]
        iso = Iso(L, v["T"][0], v["T"][1])
        step = CELL_STEP[k]
        # 간판(단계가 시작되는 셀의 뒤 가장자리)
        if k in STEP_CELL:
            si = STEP_CELL.index(k)
            if k % 2 == 0:        # 왼쪽 열: 북서 변(YZ벽, 글줄 ↗), 번호 배지는 왼쪽(바깥) 끝
                draw_board(L, v["L"], v["T"], "NW", BOARD_H, STEP_NAMES[si], STEP_BODY[si], si + 1, "a")
            else:                 # 오른쪽 열: 북동 변(XZ벽, 글줄 ↘), 번호 배지는 오른쪽(바깥) 끝
                draw_board(L, v["T"], v["R"], "NE", BOARD_H, STEP_NAMES[si], STEP_BODY[si], si + 1, "b")
        draw_cell_content(L, iso, k)
        # 바닥 글
        ft = FLOOR_TXT[k]
        floor_text(L, 4.0, S - 8.2, [(ft[0], "b", (70, 52, 40)), (ft[1], "m", (96, 78, 60))], iso, 2.2)
        # 바닥 화살표(셀 경계마다 하나, 경계와 직교): 짝수→홀수는 +X(↘), 홀수→짝수는 +Y(↙)
        if k < NCELL - 1:
            if k % 2 == 0:
                floor_arrow(iso, L, S - 1.0, S * 0.62, "X")
            else:
                floor_arrow(iso, L, S * 0.62, S - 1.0, "Y")


def crate(iso, X0, Y0, X1, Y1, Z1, col=(190, 150, 100)):
    iso.box(X0, Y0, 0, X1, Y1, Z1, (shade(col, 1.08), col, shade(col, 0.78)), ol=(100, 72, 44), lw=0.16)


def draw_cell_content(L, iso, k):
    """셀 한 칸의 장면. 바닥 글 띠(Y 37~43)는 비워 두고, 소품은 Y ≤ 33에 둔다."""
    S = CORE_S
    P = iso.p
    if k == 0:       # 재료 준비
        x, y = P(12, 12); pile(L, x, y, 6.4, 8.0, (240, 236, 224), dots=(200, 196, 186))       # 생석회 더미
        x, y = P(28, 9); pile(L, x, y, 6.4, 7.0, (150, 140, 128))                                # 화산재 더미
        x, y = P(10, 26); pile(L, x, y, 6.0, 6.0, (92, 80, 70), dots=(150, 140, 130))            # 굵은 화산암 골재
        crate(iso, 31, 5, 39, 12, 5.0)
        x, y = P(31.6, 12); pill(L, x, y - 0.8, "자재 더미", M_WALL_DN)
        x, y = P(33, 27); worker(L, x, y, 14.0, (176, 96, 60), "point", 1)
    elif k == 1:     # 마른 혼합
        iso.rect3(6, 5, 38, 32, 0.0, (246, 232, 196), ol=(190, 168, 132), lw=0.25)
        x, y = P(21, 17); pile(L, x, y, 8.0, 7.2, (206, 198, 184), dots=(250, 248, 240))
        crate(iso, 31, 5, 38, 11, 4.0)
        x, y = P(31.6, 11); pill(L, x, y - 0.8, "건식 혼합", M_WALL_DN)
        x, y = P(9, 31); worker(L, x, y, 14.0, (150, 112, 74), "hoe", 1)
    elif k == 2:     # 물 붓기
        x, y = P(26, 20); pile(L, x, y, 7.2, 6.2, (206, 198, 184))
        iso.cyl(9, 10, 0, 9.0, 3.4, (170, 130, 84), (190, 150, 100))
        bx, by = P(9, 10); L.ell(bx, by - 9.0, 2.2, 1.3, fill=(112, 170, 210))
        L.line([(bx + 2, by - 8.0), (bx + 7, by - 3.5), (x - 3.5, y - 4.2)], (112, 170, 210), 0.9)
        x, y = P(36, 31); worker(L, x, y, 14.0, (96, 120, 150), "bucket", 1)
        x, y = P(5.5, 15); pill(L, x, y, "물통", M_WALL_DN)
    elif k in (3, 4):  # 뜨거운 혼합(2셀)
        iso.rect3(8, 5, 38, 31, 0.0, (236, 196, 150), ol=(150, 98, 60), lw=0.3)
        iso.rect3(12, 9, 34, 27, 0.0, (226, 120, 60), ol=(150, 70, 30), lw=0.3)
        x, y = P(23, 18)
        L.ell(x, y, 7.6, 4.2, fill=(236, 150, 70, 200))
        steam(L, x - 1.0, y - 3.0, 5 if k == 3 else 4, 2.8)
        if k == 3:
            worker(L, *P(7, 30), 14.0, (170, 80, 60), "hoe", 1)
            x, y = P(3.0, 22); pill(L, x, y, "혼합 구덩이", M_WALL_DN)
        else:
            worker(L, *P(40, 13), 14.0, (170, 80, 60), "hoe", -1)
            worker(L, *P(36, 32), 14.0, (120, 96, 70), None, 1)
            x, y = P(8.5, 5.5); pill(L, x, y - 0.4, "열 · 증기", M_WALL_DN)
    elif k == 5:     # 타설·다짐: 거푸집에 다져 넣기
        iso.box(9, 11, 0, 31, 31, 8.0, ((176, 150, 110), (170, 128, 84), (140, 104, 66)), ol=(96, 70, 44), lw=0.2)
        iso.rect3(11, 13, 29, 29, 8.0, (190, 186, 176), ol=(120, 116, 106), lw=0.2)
        for i in range(10):
            x, y = P(13 + rnd() * 14, 15 + rnd() * 12); L.ell(x, y - 8.0, 0.9, 0.55, fill=(120, 108, 96))
        x, y = P(38, 25); pile(L, x, y, 4.4, 4.2, (110, 98, 88), dots=(160, 150, 140))
        worker(L, *P(5, 22), 14.0, (170, 112, 72), "rammer", 1)
        x, y = P(10, 31); pill(L, x, y - 1.2, "거푸집", M_WALL_DN)
    elif k == 6:     # 굳기: 굳은 단면(앞 꼭짓점 쪽, 확대 창으로 수직 지시선) + 뒤쪽 완성 벽(사용 장면)
        iso.box(14, 4, 0, 38, 7, 14.0, ((226, 222, 212), (196, 190, 176), (156, 150, 138)), ol=(110, 106, 96), lw=0.2)
        iso.arch("L", 0, 7, 0, 20, 31, 0, 7.5, (110, 84, 56), None)
        iso.box(22, 22, 0, 34, 34, 10.0, ((226, 222, 212), (190, 186, 174), (150, 146, 136)), ol=(110, 106, 96), lw=0.2)
        for i in range(16):
            x, y = P(22.5 + rnd() * 11, 34.0); L.ell(x + (rnd() - 0.5) * 1.0, y - 1.2 - rnd() * 7.8, 0.7, 0.6, fill=(255, 255, 252), outline=(150, 146, 136), lw=0.1)
        worker(L, *P(10, 24), 14.0, (176, 96, 60), "point", 1)
        worker(L, *P(14, 30), 14.0, (92, 120, 150), None, 1)
        x, y = P(22.6, 34); pill(L, x, y - 1.2, "굳은 단면", M_WALL_DN)


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


# ───────────────────────── 욕장(카라칼라 대응, 열탕실 복원 상상도) ─────────────────────────
def draw_bath(L, cx, cy, w=64.0):
    """절개 욕장: 뒤 벽 두 면 전체 높이 + 앞 벽 낮게, 지붕 제거, 열주·벽감 조각상, 코퍼 반쪽 돔(콘크리트 두께, 오큘러스는 점선=복원 추정),
    큰 아치창 빛, 청록 욕조(열탕 구역에만 증기)와 목욕객, 하이포코스트 절개."""
    sl = slab(L, cx, cy, w, t=6.5, top=(222, 212, 186))
    # 하이포코스트(바닥 밑 난방) 절개: 받침 정면 왼쪽 측면에 벽돌 기둥(pilae)과 아궁이가 드러난다
    pa, pb = sl["L"], sl["B"]
    def lp(t):
        return (pa[0] + (pb[0] - pa[0]) * t, pa[1] + (pb[1] - pa[1]) * t)
    n0, n1 = lp(0.18), lp(0.74)
    L.poly([(n0[0], n0[1] + 1.2), (n1[0], n1[1] + 1.2), (n1[0], n1[1] + 5.6), (n0[0], n0[1] + 5.6)], fill=(70, 46, 32), outline=(40, 28, 20), lw=0.15)
    for i in range(7):
        q = lp(0.22 + i * 0.07)
        L.rect(q[0] - 0.6, q[1] + 1.4, q[0] + 0.6, q[1] + 5.4, fill=(196, 116, 80))
    q = lp(0.76)
    L.ell(q[0], q[1] + 3.6, 1.5, 1.2, fill=(244, 156, 60))
    iso, S = iso_of_slab(L, cx, cy, w)
    m = 3.0
    X0, Y0, X1, Y1 = m, m, S - m, S - m
    HZ = 21.0
    HF = 5.5
    WALL = ((226, 204, 164), (214, 190, 148), (192, 166, 126))
    # 바닥
    iso.rect3(X0, Y0, X1, Y1, 0.0, (238, 230, 208), ol=(120, 96, 66), lw=0.2)
    # 뒤 벽 두 면(두께 1.4): NW 벽(X=X0, +X향 면), NE 벽(Y=Y0, +Y향 면)
    iso.box(X0, Y0, 0, X0 + 1.4, Y1, HZ, WALL, ol=(120, 96, 66), lw=0.2)
    iso.box(X0, Y0, 0, X1, Y0 + 1.4, HZ, WALL, ol=(120, 96, 66), lw=0.2)
    # NE 벽 가운데: 코퍼 반쪽 돔이 있는 아프시스 개구(큰 아치) — 콘크리트 두께 링 + 안쪽 코퍼
    cu = (X0 + X1) / 2.0 + 4.0
    r_o, r_i = 9.0, 6.6
    z_spr = 7.0
    ring = []
    for i in range(0, 25):
        a = math.pi * i / 24.0
        ring.append((cu + r_o * math.cos(a), z_spr + r_o * math.sin(a)))
    ring_in = [(cu + r_i * math.cos(math.pi * i / 24.0), z_spr + r_i * math.sin(math.pi * i / 24.0)) for i in range(25)]
    iso.fpoly("L", 0, Y0 + 1.4, 0, [(cu - r_o, 0)] + ring + [(cu + r_o, 0)], fill=CONC, ol=(100, 94, 84), lw=0.2)
    iso.fpoly("L", 0, Y0 + 1.4, 0, [(cu - r_i, 0)] + ring_in + [(cu + r_i, 0)], fill=(246, 238, 214), ol=(150, 130, 98), lw=0.15)
    for k in range(1, 4):                 # 코퍼: 동심 반원(얕은 격자)
        rr = r_i * k / 4.0
        iso.fpoly("L", 0, Y0 + 1.4, 0, [(cu + rr * math.cos(math.pi * i / 16.0), z_spr + rr * math.sin(math.pi * i / 16.0)) for i in range(17)], fill=None, ol=(170, 146, 108), lw=0.12)
    for a in range(20, 180, 22):          # 코퍼: 방사선
        r = math.radians(a)
        iso.fpoly("L", 0, Y0 + 1.4, 0, [(cu, z_spr), (cu + r_i * math.cos(r), z_spr + r_i * math.sin(r))], fill=None, ol=(170, 146, 108), lw=0.1)
    # 오큘러스(복원 추정): 점선 타원 + 점선 빛줄기
    ox, oy = iso.p(cu, Y0 + 1.4, z_spr + r_i * 0.9)
    L.ell(ox, oy, 1.4, 0.8, outline=(150, 120, 60), lw=0.2)
    # 돌 두께 단면의 골재 점
    for i in range(10):
        a = math.pi * (0.1 + 0.8 * rnd())
        rr = r_i + 0.4 + rnd() * (r_o - r_i - 0.8)
        px, py = iso.face("L", 0, Y0 + 1.4, 0, [(cu + rr * math.cos(a), z_spr + rr * math.sin(a))])[0]
        L.ell(px, py, 0.32, 0.28, fill=(228, 222, 206))
    # NW 벽: 큰 아치창 3개(빛이 들어오는 창) + 벽감 조각상 2개
    for j, vy in enumerate((6.5, 14.5, 22.5)):
        iso.arch("R", X0 + 1.4, 0, 9.5, vy - 2.2, vy + 2.2, 0, 5.0, (252, 248, 226), (140, 112, 76))
    for vy in (10.5, 18.5):
        iso.arch("R", X0 + 1.4, 0, 0, vy - 1.6, vy + 1.6, 1.0, 4.4, (214, 190, 150), (140, 112, 76))
        px, py = iso.face("R", X0 + 1.4, 0, 0, [(vy, 2.0)])[0]
        L.ell(px, py - 2.0, 0.8, 0.8, fill=(248, 244, 236))
        L.rect(px - 0.7, py - 1.3, px + 0.7, py + 0.9, fill=(248, 244, 236))
    # 열주(NE 벽 앞, 냉탕 쪽 장축): 기둥 5개
    for i in range(5):
        X = X0 + 2.0 + i * 3.4
        Y = Y0 + 4.0
        bx, by = iso.p(X, Y, 0.0)
        L.rect(bx - 0.9, by - 14.0, bx + 0.9, by, fill=(244, 236, 214), outline=(150, 126, 92), lw=0.14)
        L.rect(bx - 1.5, by - 15.2, bx + 1.5, by - 14.0, fill=(236, 224, 196), outline=(150, 126, 92), lw=0.14)
    # 욕조(청록): 열탕 구역 + 냉탕 구역 구분
    pool = [(X0 + 3, Y0 + 9), (X1 - 4, Y0 + 9), (X1 - 4, Y1 - 4), (X0 + 3, Y1 - 4)]
    iso.poly3([(a, b, 0.2) for a, b in pool], fill=(70, 178, 196), ol=(36, 120, 140), lw=0.25)
    iso.poly3([(X1 - 12, Y0 + 9, 0.3), (X1 - 4, Y0 + 9, 0.3), (X1 - 4, Y1 - 4, 0.3), (X1 - 12, Y1 - 4, 0.3)], fill=(54, 164, 186), ol=None)
    # 증기: 열탕(오른쪽) 한 구역에만
    sx, sy = iso.p(X1 - 8, (Y0 + Y1) / 2.0 + 2, 0.3)
    steam(L, sx, sy - 1.0, 4, 2.2)
    # 빛줄기(큰 창에서) — 반투명
    with_a = (255, 244, 190, 90)
    bx0, by0 = iso.face("R", X0 + 1.4, 0, 9.5, [(14.5, 0)])[0]
    L.poly([(bx0 - 2.0, by0 - 3.0), (bx0 + 2.0, by0 - 3.0), (bx0 + 12.0, by0 + 12.0), (bx0 + 4.0, by0 + 12.0)], fill=with_a)
    # 목욕객 6명(머리+어깨)
    for (X, Y) in [(X0 + 8, Y0 + 14), (X0 + 11, Y0 + 18), (X0 + 14, Y0 + 12), (X1 - 9, Y0 + 14), (X1 - 7, Y0 + 18), (X1 - 11, Y0 + 21)]:
        px, py = iso.p(X, Y, 0.5)
        L.ell(px, py - 1.0, 0.95, 0.95, fill=(214, 156, 120))
        L.ell(px, py + 0.3, 1.5, 0.7, fill=(236, 196, 160))
    # 앞 벽 두 면(낮게 절개)
    iso.box(X0, Y1 - 1.4, 0, X1, Y1, HF, WALL, ol=(120, 96, 66), lw=0.2)
    iso.box(X1 - 1.4, Y0, 0, X1, Y1, HF, WALL, ol=(120, 96, 66), lw=0.2)


# ───────────────────────── 판테온(돔 절개: 코퍼·오큘러스·위로 갈수록 가벼운 골재 3띠) ─────────────────────────
BRICK = (192, 108, 80)
BRICK_L = (210, 128, 96)
BRICK_D = (156, 84, 62)


def draw_pantheon(L, cx, cy, w=66.0):
    slab(L, cx, cy, w, t=5.0, top=(222, 212, 186))
    iso, S = iso_of_slab(L, cx, cy, w)
    R = 11.0
    Xc, Yc = 14.5, 17.0
    Hd = 10.0
    Rt = 3.0
    # 계단형 광장 포장
    iso.rect3(2, 3, S - 2, S - 3, 0.0, (232, 222, 198), ol=(170, 154, 124), lw=0.2)
    x, y = iso.p(S - 6, 5)
    cypress(L, x, y, 11.0, 2.6)
    # 드럼 바닥(실내 바닥) 타원
    iso.ell(Xc, Yc, 0.2, R - Rt, fill=(236, 226, 204), ol=(150, 130, 98), lw=0.2)
    # 드럼 뒤쪽 반(안쪽면) — 화면 위쪽 반 타원 사이를 채운다
    cxs, cys = iso.p(Xc, Yc, 0.0)
    a_i = 1.2247 * (R - Rt)
    a_o = 1.2247 * R
    top_in = iso.p(Xc, Yc, Hd)
    # 안쪽 벽 면(오목면): 바닥 뒤 반원호 ~ 림 뒤 반원호
    pts = [(cxs + a_i * math.cos(math.radians(t)), cys + KE * a_i * math.sin(math.radians(t))) for t in range(180, 361, 6)]
    pts_top = [(cxs + a_i * math.cos(math.radians(t)), cys - Hd + KE * a_i * math.sin(math.radians(t))) for t in range(360, 179, -6)]
    L.poly(pts + pts_top, fill=(224, 204, 164), outline=(120, 98, 70), lw=0.2)
    for t in range(190, 360, 16):            # 벽감(안쪽 아치)
        c = math.cos(math.radians(t))
        sn = math.sin(math.radians(t))
        bx, by = cxs + a_i * c, cys + KE * a_i * sn
        L.rect(bx - 0.9, by - 6.5, bx + 0.9, by - 1.2, fill=(176, 148, 108))
    # 돔 바깥 반구(뒤쪽 볼록면)
    L.pie(top_in[0], top_in[1], a_o, a_o, 180, 360, fill=(206, 188, 150), outline=(120, 98, 70), lw=0.25)
    # 절개면(Y=Yc 평면, +Y향): 드럼 벽 단면 + 돔 단면(콘크리트 두께, 골재 3띠) + 안쪽 코퍼
    def sec(uv, fill, ol=None, lw=0.15):
        iso.fpoly("L", Xc, Yc, 0.0, uv, fill, ol, lw)
    Ro, Ri = R, R - 3.4
    # 드럼 벽 단면 두 줄
    sec([(-R, 0), (-R + Rt, 0), (-R + Rt, Hd), (-R, Hd)], CONC, (100, 94, 84))
    sec([(R - Rt, 0), (R, 0), (R, Hd), (R - Rt, Hd)], CONC, (100, 94, 84))
    # 돔 단면: 3개 골재 띠(아래 무거운 짙은 색 → 위 가벼운 옅은 색)
    def arc(r, a0, a1, n=28):
        return [(r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), Hd + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    bands = [(Ro, Ro - 1.15, (150, 142, 130)), (Ro - 1.15, Ro - 2.3, (186, 180, 168)), (Ro - 2.3, Ri, (224, 220, 210))]
    # 띠를 각도로 나누어 아래(0~40°) 무거움, 위로 갈수록 가벼움
    segs = [(0, 38, (146, 138, 126)), (38, 72, (178, 172, 160)), (72, 108, (206, 202, 192)), (108, 142, (178, 172, 160)), (142, 180, (146, 138, 126))]
    for (a0, a1, col) in segs:
        sec(arc(Ro, a0, a1, 10) + arc(Ri, a1, a0, 10), col, None)
    sec(arc(Ro, 0, 180) , None, (100, 94, 84), 0.22)
    sec(arc(Ri, 0, 180), None, (100, 94, 84), 0.22)
    # 안쪽 오목면(코퍼) — 안쪽 반원 영역
    inner = arc(Ri, 0, 180)
    sec(inner, (238, 230, 210), None)
    for k in range(1, 6):                    # 코퍼 5단
        sec(arc(Ri * k / 5.3, 0, 180, 18), None, (178, 156, 118), 0.12)
    for a in range(16, 180, 20):
        r = math.radians(a)
        sec([(0, Hd), (Ri * math.cos(r), Hd + Ri * math.sin(r))], None, (178, 156, 118), 0.1)
    # 오큘러스: 꼭대기 개구(복원이 아니라 실제 — 판테온은 현존)
    ox, oy = iso.face("L", Xc, Yc, 0.0, [(0, Hd + Ro)])[0]
    L.ell(ox, oy + 0.6, 1.9, 0.9, fill=(255, 252, 232), outline=(120, 98, 70), lw=0.2)
    # 포르티코(오른쪽 +X): 박스 + 8기둥 + 삼각 박공
    px0 = Xc + R - 1.0
    px1 = px0 + 9.5
    py0, py1 = Yc - 8.0, Yc + 8.0
    iso.box(px0, py0, 0, px1, py1, 2.0, ((238, 228, 204), (224, 210, 180), (200, 184, 150)), ol=(130, 108, 78), lw=0.2)
    for i in range(8):
        Y = py0 + 1.0 + i * (py1 - py0 - 2.0) / 7.0
        bx, by = iso.p(px1 - 1.0, Y, 2.0)
        L.rect(bx - 0.55, by - 11.0, bx + 0.55, by, fill=(246, 238, 216), outline=(150, 126, 92), lw=0.12)
    # 엔타블러처 + 박공(+X면, 'R'면)
    iso.poly3([(px0, py0, 13.0), (px1, py0, 13.0), (px1, py1, 13.0), (px0, py1, 13.0)], fill=(230, 214, 184), ol=(130, 108, 78), lw=0.15)
    iso.fpoly("R", px1, py0 - 0.0, 13.0, [(0, 0), (py1 - py0, 0), ((py1 - py0) / 2.0, 4.6)], (236, 222, 192), (130, 108, 78), 0.18)
    iso.fpoly("R", px1, py0, 11.0, [(0, 0), (py1 - py0, 0), (py1 - py0, 2.0), (0, 2.0)], (226, 210, 178), (130, 108, 78), 0.14)
    # 광장 인물과 나무(앞쪽)
    for (X, Y) in [(S - 5, 29), (6, 31)]:
        x, y = iso.p(X, Y)
        cypress(L, x, y, 11.0, 2.6)
    for (X, Y) in [(24, 30), (27, 31), (10, 33)]:
        x, y = iso.p(X, Y)
        person(L, x, y, 4.6, (150, 70, 52) if X > 20 else (92, 120, 150))


# ───────────────────────── 수도교(연속 아케이드 + 상층 수로 + 보수 구간) ─────────────────────────
def draw_aqueduct(L, cx, cy, w=68.0):
    slab(L, cx, cy, w, t=5.0, top=(214, 206, 170))
    iso, S = iso_of_slab(L, cx, cy, w)
    # 풀밭 결
    iso.rect3(1.5, 1.5, S - 1.5, S - 1.5, 0.0, (176, 188, 126), ol=None)
    Yw0, Yw1 = 17.0, 20.5
    X0, X1 = 2.5, S - 2.5
    nb = 7
    pitch = (X1 - X0) / nb
    pier = 1.7
    H1, H2 = 9.5, 18.0
    STONE_C = ((226, 210, 172), (208, 188, 148), (178, 156, 118))
    BRICK_C = ((214, 132, 98), (196, 108, 78), (160, 84, 60))
    # 아치 열 지면 그림자
    # 벽 본체(+Y향 면이 보인다): 하층 + 상층 연속 벽
    iso.box(X0, Yw0, 0, X1, Yw1, H1, STONE_C, ol=(120, 98, 70), lw=0.2)
    iso.box(X0, Yw0, H1, X1, Yw1, H2, STONE_C, ol=(120, 98, 70), lw=0.2)
    # 보수 구간(하드리아누스기 벽돌면 콘크리트): 가운데 두 칸을 벽돌색으로 덧댐
    for i in (3, 4):
        xa = X0 + i * pitch
        iso.fpoly("L", 0, Yw1, 0, [(xa, 0), (xa + pitch, 0), (xa + pitch, H2), (xa, H2)], BRICK_C[1], (120, 70, 50), 0.15)
    # 하층 아치 개구(밑까지 열림) + 상층 작은 아치
    for i in range(nb):
        xa = X0 + i * pitch + pier / 2.0
        xb = X0 + (i + 1) * pitch - pier / 2.0
        iso.arch("L", 0, Yw1, 0, xa, xb, 0, 5.6, (112, 100, 70), (96, 76, 50))
        iso.arch("L", 0, Yw1, 0, xa + 0.4, xb - 0.4, H1 + 1.0, H1 + 3.6, (112, 100, 70), (96, 76, 50))
    # 벽돌 줄눈(보수 구간)
    for i in (3, 4):
        xa = X0 + i * pitch
        for j in range(1, 6):
            iso.fpoly("L", 0, Yw1, 0, [(xa, j * 3.0), (xa + pitch, j * 3.0)], None, (150, 78, 58), 0.1)
    # 상부 수로(스페쿠스): 윗면에 파란 물길
    iso.poly3([(X0 - 0.3, Yw0 + 0.7, H2), (X1 + 0.3, Yw0 + 0.7, H2), (X1 + 0.3, Yw1 - 0.7, H2), (X0 - 0.3, Yw1 - 0.7, H2)], fill=(120, 176, 208), ol=(70, 110, 140), lw=0.15)
    iso.box(X0 - 0.3, Yw0, H2, X1 + 0.3, Yw0 + 0.7, H2 + 1.4, STONE_C, ol=(120, 98, 70), lw=0.15)
    iso.box(X0 - 0.3, Yw1 - 0.7, H2, X1 + 0.3, Yw1, H2 + 1.4, STONE_C, ol=(120, 98, 70), lw=0.15)
    # 들판 소품: 올리브 두 그루와 농부
    for (X, Y) in [(S - 6, 8), (6, 30)]:
        x, y = iso.p(X, Y)
        olive(L, x, y, 3.8)
    x, y = iso.p(22, 31)
    person(L, x, y, 4.8, (176, 112, 72))


# ───────────────────────── 포르투스(트라야누스 육각 내항 + 붉은 기와 창고 열 + 방파제 + 등대) ─────────────────────────
ROOF_RED = (196, 92, 64)


def draw_portus(L, cx, cy, w=64.0):
    slab(L, cx, cy, w, t=5.0, top=(216, 204, 176))
    iso, S = iso_of_slab(L, cx, cy, w)
    # 육각 내항(물)
    Rh = 12.5
    hc = (S / 2.0, S / 2.0)
    hexp = [(hc[0] + Rh * math.cos(math.radians(60 * k)), hc[1] + Rh * 0.9 * math.sin(math.radians(60 * k))) for k in range(6)]
    iso.poly3([(a, b, 0.0) for a, b in hexp], fill=(214, 200, 170), ol=(150, 130, 98), lw=0.2)
    hexw = [(hc[0] + (Rh - 1.6) * math.cos(math.radians(60 * k)), hc[1] + (Rh - 1.6) * 0.9 * math.sin(math.radians(60 * k))) for k in range(6)]
    iso.poly3([(a, b, -0.6) for a, b in hexw], fill=(112, 172, 214), ol=(70, 120, 160), lw=0.2)
    # 창고 열: 위·아래 변(X축 평행)에 길쭉한 붉은 기와 창고 4연
    def warehouse(X0, Y0, X1, Y1):
        iso.box(X0, Y0, 0, X1, Y1, 3.4, ((226, 190, 150), (214, 176, 134), (186, 148, 108)), ol=(120, 84, 54), lw=0.15)
        iso.poly3([(X0 - 0.3, Y0 - 0.2, 3.4), (X1 + 0.3, Y0 - 0.2, 3.4), (X1 + 0.3, (Y0 + Y1) / 2.0, 5.0), (X0 - 0.3, (Y0 + Y1) / 2.0, 5.0)], fill=shade(ROOF_RED, 1.1), ol=(130, 60, 40), lw=0.15)
        iso.poly3([(X0 - 0.3, (Y0 + Y1) / 2.0, 5.0), (X1 + 0.3, (Y0 + Y1) / 2.0, 5.0), (X1 + 0.3, Y1 + 0.2, 3.4), (X0 - 0.3, Y1 + 0.2, 3.4)], fill=ROOF_RED, ol=(130, 60, 40), lw=0.15)
    ytop = hc[1] - Rh * 0.9 * 0.866 - 5.2
    ybot = hc[1] + Rh * 0.9 * 0.866 + 1.4
    for i in range(4):
        warehouse(hc[0] - 12.5 + i * 6.4, ytop, hc[0] - 12.5 + i * 6.4 + 5.8, ytop + 3.8)
    for i in range(3):
        warehouse(hc[0] - 9.8 + i * 6.4, ybot, hc[0] - 9.8 + i * 6.4 + 5.8, ybot + 3.8)
    # 방파제: 받침 정면에서 바다로 나가는 두 팔(±30° 직선) + 등대
    bw = (232, 222, 196)
    a1 = iso.p(S + 0.0, S * 0.5)
    L.poly([iso.p(S - 2, S * 0.62, 0), iso.p(S + 14, S * 0.62, 0), iso.p(S + 14, S * 0.62 + 2.4, 0), iso.p(S - 2, S * 0.62 + 2.4, 0)], fill=bw, outline=(150, 130, 98), lw=0.2)
    lh = iso.p(S + 14.5, S * 0.62 + 1.2, 0)
    L.poly([(lh[0] - 1.6, lh[1]), (lh[0] + 1.6, lh[1]), (lh[0] + 1.1, lh[1] - 8.0), (lh[0] - 1.1, lh[1] - 8.0)], fill=(244, 238, 222), outline=(130, 108, 78), lw=0.15)
    L.poly([(lh[0] - 1.4, lh[1] - 8.0), (lh[0], lh[1] - 10.4), (lh[0] + 1.4, lh[1] - 8.0)], fill=(240, 196, 90), outline=(130, 108, 78), lw=0.12)
    L.poly([iso.p(S * 0.62, S - 2, 0), iso.p(S * 0.62, S + 11, 0), iso.p(S * 0.62 + 2.4, S + 11, 0), iso.p(S * 0.62 + 2.4, S - 2, 0)], fill=bw, outline=(150, 130, 98), lw=0.2)
    # 배 한 척(내항 안)
    sx, sy = iso.p(hc[0] + 1.0, hc[1] + 0.5, -0.2)
    L.poly([(sx - 3.0, sy), (sx + 3.0, sy - 1.0), (sx + 4.0, sy), (sx - 4.0, sy + 1.0)], fill=(150, 108, 70), outline=(90, 64, 40), lw=0.15)
    L.line([(sx, sy - 0.6), (sx, sy - 5.6)], (110, 80, 50), 0.25, joint=False)
    L.poly([(sx, sy - 5.4), (sx + 2.4, sy - 3.0), (sx, sy - 1.4)], fill=(248, 244, 232), outline=(150, 130, 98), lw=0.1)
    # 부두 인물·나무
    for (X, Y) in [(4, 4), (S - 4, 6)]:
        x, y = iso.p(X, Y)
        cypress(L, x, y, 8.0, 2.2)
    for (X, Y) in [(S - 5, S - 9), (6, S - 8)]:
        x, y = iso.p(X, Y)
        person(L, x, y, 3.8, (176, 100, 60))


# ───────────────────────── 카이킬리아 메텔라 무덤(아피아 가도변, 원통 드럼 사분 절개) ─────────────────────────
def draw_metella(L, cx, cy, w=64.0):
    slab(L, cx, cy, w, t=5.0, top=(196, 196, 150))
    iso, S = iso_of_slab(L, cx, cy, w)
    iso.rect3(1.5, 1.5, S - 1.5, S - 1.5, 0.0, (184, 192, 134), ol=None)
    Xc, Yc = 19.0, 19.0
    R = 10.5
    Zp, Zd = 6.0, 19.0
    for (X, Y, h) in [(4, 5, 10), (S - 4, 6, 9)]:
        x, y = iso.p(X, Y)
        cypress(L, x, y, h, 2.4)
    # 사각 기단
    iso.box(Xc - 14, Yc - 14, 0, Xc + 14, Yc + 14, Zp, ((228, 216, 186), (212, 198, 164), (186, 170, 136)), ol=(120, 98, 70), lw=0.2)
    # 드럼: 앞쪽(관찰자 쪽) 1/4를 걷어 내 두 절단면을 드러낸다
    def arc_pts(t0, t1, z, n=10):
        return [(Xc + R * math.cos(math.radians(t0 + (t1 - t0) * i / n)), Yc + R * math.sin(math.radians(t0 + (t1 - t0) * i / n)), z) for i in range(n + 1)]
    # 바깥 측면 두 조각(θ −45~0°, 90~135°)
    for (t0, t1) in ((-45, 0), (90, 135)):
        lo = arc_pts(t0, t1, Zp)
        hi = arc_pts(t0, t1, Zd)
        iso.poly3(lo + hi[::-1], fill=(206, 188, 150) if t0 < 0 else (222, 204, 166), ol=(120, 98, 70), lw=0.25)
        # 프리즈 띠
        lo2 = arc_pts(t0, t1, Zd - 2.2)
        iso.poly3(lo2 + hi[::-1], fill=(236, 226, 198), ol=(130, 108, 78), lw=0.15)
    # 윗면(3/4 원판)
    top = [(Xc, Yc, Zd)] + [(Xc + R * math.cos(math.radians(t)), Yc + R * math.sin(math.radians(t)), Zd) for t in range(90, 361, 8)]
    iso.poly3(top, fill=(238, 228, 200), ol=(120, 98, 70), lw=0.3)
    # 절단면 ① Y=Yc 평면(+Y향, X Xc→Xc+R) ② X=Xc 평면(+X향, Y Yc→Yc+R)
    H = Zd - Zp
    for kind in ("L", "R"):
        X, Y = (Xc, Yc)
        iso.fpoly(kind, X, Y, Zp, [(0, 0), (R, 0), (R, H), (0, H)], CONC, (100, 94, 84), 0.25)
        iso.fpoly(kind, X, Y, Zp, [(R - 2.4, 0), (R, 0), (R, H), (R - 2.4, H)], BRICK, (130, 70, 50), 0.2)      # 벽돌 겉면
        iso.fpoly(kind, X, Y, Zp, [(0, 0), (R - 2.4, 0), (R - 2.4, 3.0), (0, 3.0)], TUFF, (100, 80, 56), 0.15)    # 응회암 보강
        for i in range(26):
            u = rnd() * (R - 3.0)
            v = 3.4 + rnd() * (H - 3.8)
            px, py = iso.face(kind, X, Y, Zp, [(u, v)])[0]
            L.ell(px, py, 0.5, 0.42, fill=(226, 220, 204) if rnd() > 0.4 else (122, 116, 104))
        iso.arch(kind, X, Y, Zp, 0.0, 4.4, 3.0, 6.2, (92, 70, 48), (60, 44, 30))          # 무덤방(작은 아치 공동)
        iso.fpoly(kind, X, Y, Zp, [(0, H - 2.2), (R, H - 2.2), (R, H), (0, H)], (236, 226, 198), (130, 108, 78), 0.15)
    # 물방울(비가 스며 류사이트가 녹음) — 자기 치유와는 다른 메커니즘
    for (u, v) in [(4.0, 10.5), (7.0, 9.0), (9.0, 11.0)]:
        px, py = iso.face("L", Xc, Yc, Zp, [(u, v)])[0]
        L.poly([(px, py - 1.4), (px - 0.8, py), (px + 0.8, py)], fill=(80, 140, 206))
    x, y = iso.p(S - 5, S - 5)
    cypress(L, x, y, 10, 2.4)
    x, y = iso.p(5, S - 6)
    olive(L, x, y, 3.4)
    for (X, Y) in [(S - 9, S - 3), (S - 12, S - 4)]:
        x, y = iso.p(X, Y)
        person(L, x, y, 4.4, (150, 70, 52) if X > S - 10 else (92, 120, 150))


# ───────────────────────── 베수비오(Support-2): 79년 이전, 봉우리 하나·포도밭 비탈, 대기 원근 ─────────────────────────
def draw_vesuvius(L, cx, cy, w=52.0):
    """원근 배율 약 0.6(표준 86×80 → 52×48), 모든 색을 바탕과 50% 섞는다. 정상은 평평한 잿빛, 비탈은 포도밭 줄무늬. 연기는 그리지 않는다."""
    A = 0.5
    slab(L, cx, cy, w, t=4.0, top=mix((176, 190, 124), BG, A), soil=mix(SOIL, BG, A))
    prof = [(-26, 0), (-23, 2.6), (-19.5, 5.8), (-15.5, 9.6), (-11.5, 14.2), (-8, 19), (-5.4, 23.6), (-3.8, 26.2), (4.2, 26.2),
            (5.8, 24.4), (8.6, 20.4), (12.4, 15.6), (16.8, 10.8), (21, 6.2), (24, 3.0), (26, 0)]
    pts = [(cx + u, cy - h) for u, h in prof]
    L.poly(pts, fill=mix((146, 124, 88), BG, A), outline=mix((92, 70, 48), BG, A), lw=0.3)
    # 입체감: 오른쪽 비탈을 어둡게
    L.poly([(cx + 0.5, cy - 26.2)] + [(cx + u, cy - h) for u, h in prof[8:]] + [(cx + 5, cy)], fill=mix((122, 100, 68), BG, A))
    # 능선·골(물 흐른 자국)
    for (u0, u1, hh0) in [(-3.0, -9.0, 24.0), (0.5, -1.0, 25.5), (2.5, 7.5, 24.0), (-1.0, -15.0, 20.0)]:
        L.line([(cx + u0, cy - hh0), (cx + (u0 + u1) / 2.0, cy - hh0 * 0.55), (cx + u1, cy - 2.0)], mix((110, 88, 60), BG, A), 0.3)
    # 잿빛 평평한 정상
    L.poly([(cx - 3.8, cy - 26.2), (cx + 4.2, cy - 26.2), (cx + 5.8, cy - 24.4), (cx - 5.4, cy - 23.6)], fill=mix((178, 174, 166), BG, A), outline=mix((100, 94, 86), BG, A), lw=0.2)

    def xlim(h):
        for i in range(len(prof) - 1):
            if prof[i][1] <= h <= prof[i + 1][1] and prof[i + 1][1] > prof[i][1]:
                f = (h - prof[i][1]) / (prof[i + 1][1] - prof[i][1])
                return prof[i][0] + (prof[i + 1][0] - prof[i][0]) * f
        return -26.0

    # 비탈 중하단 포도밭: 등고선을 따라 놓인 줄(짧은 지면축 선분)
    for j in range(6):
        hh = 1.8 + j * 2.5
        xl = xlim(hh)
        x = xl + 1.6
        while x < -xl - 2.4:
            L.line([(cx + x, cy - hh), (cx + x + 1.6, cy - hh + 0.92)], mix((70, 132, 58), BG, A), 0.45, joint=False)
            x += 2.4
    # 앞 비탈(받침 앞 반) 포도밭: 지면축 ±30° 줄
    side = w / SQ3
    for j in range(5):
        x0 = cx - 20 + j * 3.2
        y0 = cy + 1.4 + j * 1.9
        for q in range(8):
            xa, ya = x0 + q * 3.6, y0 + q * 2.08
            if in_poly((xa + 1.5, ya + 0.9), [(cx - w / 2, cy), (cx, cy - side / 2), (cx + w / 2, cy), (cx, cy + side / 2)]):
                L.line([(xa, ya), (xa + 2.6, ya + 1.5)], mix((86, 144, 70), BG, A), 0.4, joint=False)


def draw_farm(L, cx, cy):
    """베수비오 밑동 앞의 포도밭 농장(빌라 레지나형): 작은 받침, 줄지은 포도, 지붕 얹은 집, 항아리. 밑동 5~6mm를 가린다."""
    slab(L, cx, cy, 30.0, t=1.8, top=(176, 190, 124), soil=SOIL)
    iso, S = iso_of_slab(L, cx, cy, 30.0)
    for i in range(4):
        y0 = 3.0 + i * 3.4
        iso.line3([(3, y0, 0.1), (S - 3, y0, 0.1)], (70, 130, 58), 0.45)
    iso.box(2.5, 2.5, 0, 10.5, 8.5, 4.4, ((236, 214, 170), (224, 198, 150), (196, 166, 124)), ol=(120, 84, 54), lw=0.15)
    iso.poly3([(2.0, 2.0, 4.4), (11.0, 2.0, 4.4), (11.0, 5.5, 6.4), (2.0, 5.5, 6.4)], fill=shade(ROOF_RED, 1.1), ol=(130, 60, 40), lw=0.12)
    iso.poly3([(2.0, 5.5, 6.4), (11.0, 5.5, 6.4), (11.0, 9.0, 4.4), (2.0, 9.0, 4.4)], fill=ROOF_RED, ol=(130, 60, 40), lw=0.12)
    for (X, Y) in [(14, 4), (16, 7)]:
        x, y = iso.p(X, Y)
        L.ell(x, y - 1.4, 1.1, 1.4, fill=(176, 116, 78), outline=(110, 70, 44), lw=0.12)


def draw_vineyard(L, cx, cy):
    """아피아 가도변 포도밭 구획: 포도 줄과 항아리, 작은 헛간"""
    slab(L, cx, cy, 44.0, t=2.6, top=(172, 188, 118), soil=SOIL)
    iso, S = iso_of_slab(L, cx, cy, 44.0)
    for i in range(6):
        y0 = 3.5 + i * 3.4
        iso.line3([(2.5, y0, 0.1), (S - 2.5, y0, 0.1)], (66, 128, 56), 0.5)
        for q in range(7):
            x_ = 3.0 + q * 3.2
            iso.line3([(x_, y0, 0.1), (x_, y0, 1.5)], (66, 128, 56), 0.3)
    iso.box(S - 9, 2.0, 0, S - 2.5, 7.5, 4.2, ((236, 214, 170), (224, 198, 150), (196, 166, 124)), ol=(120, 84, 54), lw=0.14)
    iso.poly3([(S - 9.5, 1.5, 4.2), (S - 2.0, 1.5, 4.2), (S - 2.0, 4.7, 6.2), (S - 9.5, 4.7, 6.2)], fill=shade(ROOF_RED, 1.1), ol=(130, 60, 40), lw=0.12)
    iso.poly3([(S - 9.5, 4.7, 6.2), (S - 2.0, 4.7, 6.2), (S - 2.0, 8.0, 4.2), (S - 9.5, 8.0, 4.2)], fill=ROOF_RED, ol=(130, 60, 40), lw=0.12)
    for (X, Y) in [(S - 4, S - 4), (S - 7, S - 3.5)]:
        x, y = iso.p(X, Y)
        L.ell(x, y - 1.3, 1.0, 1.3, fill=(176, 116, 78), outline=(110, 70, 44), lw=0.12)


def draw_field(L, cx, cy, kind="olive", w=44.0):
    """들판 구획(받침 위): olive 올리브 과수원+착유장, grain 곡식밭+볏단"""
    top = {"olive": (190, 192, 128), "grain": (226, 206, 130)}[kind]
    slab(L, cx, cy, w, t=2.6, top=top, soil=SOIL)
    iso, S = iso_of_slab(L, cx, cy, w)
    if kind == "olive":
        for i in range(3):
            for j in range(3):
                x, y = iso.p(5 + i * 8.5, 5 + j * 8.5)
                olive(L, x, y, 2.9)
        iso.box(S - 9, S - 9, 0, S - 2.5, S - 3.0, 4.0, ((236, 214, 170), (224, 198, 150), (196, 166, 124)), ol=(120, 84, 54), lw=0.14)
    else:
        for i in range(7):
            y0 = 2.5 + i * 2.6
            iso.line3([(2.5, y0, 0.1), (S - 2.5, y0, 0.1)], (200, 168, 82), 0.55)
        for (X, Y) in [(S - 8, 5), (S - 5, 9), (S - 10, 12)]:
            x, y = iso.p(X, Y)
            L.poly([(x - 1.2, y), (x + 1.2, y), (x + 0.6, y - 3.0), (x - 0.6, y - 3.0)], fill=(214, 176, 80), outline=(150, 112, 50), lw=0.1)


# ───────────────────────── 소품: 수레 · 화산재 운반선 · 답차 기중기 (탈것 등급 33~41mm) ─────────────────────────
def draw_cart(L, cx, cy):
    """로마 수레(plaustrum): 짐칸, 바퀴 2개, 끌채. 화산재 포대를 싣는다."""
    iso = Iso(L, cx - 10.0, cy - 8.0)
    L.ell(cx + 1, cy + 6.5, 19.0, 5.2, fill=(120, 98, 64, 90))
    iso.box(0, 1.0, 4.2, 20, 11, 5.6, ((196, 150, 100), (176, 130, 84), (146, 106, 66)), ol=(96, 66, 40), lw=0.15)
    for (X, Y) in [(3.0, 3.0), (7.4, 3.2), (11.8, 3.0), (5.2, 7.2), (9.8, 7.0)]:      # 화산재 포대
        iso.box(X, Y, 5.6, X + 3.6, Y + 3.4, 8.6, ((226, 218, 196), (206, 196, 170), (176, 166, 140)), ol=(110, 100, 80), lw=0.12)
    for u0 in (4.0, 14.5):
        pts = [(u0 + 3.6 * math.cos(math.radians(a)), 3.6 + 3.6 * math.sin(math.radians(a))) for a in range(0, 360, 15)]
        iso.fpoly("L", 0, 11.0, 0.0, pts, (150, 108, 68), (80, 56, 34), 0.25)
        px, py = iso.face("L", 0, 11.0, 0.0, [(u0, 3.6)])[0]
        L.ell(px, py, 0.8, 0.7, fill=(90, 66, 40))
    iso.line3([(20, 6.0, 4.6), (31, 6.0, 4.0)], (110, 80, 50), 0.6)
    iso.line3([(30, 3.4, 4.0), (30, 8.6, 4.0)], (110, 80, 50), 0.5)


def draw_ship(L, cx, cy):
    """화산재 운반선(포추올리 → 포르투스): 선체, 돛대, 돛, 포대."""
    iso = Iso(L, cx - 12.0, cy - 9.0)
    L.ell(cx + 1, cy + 7.5, 21.0, 4.0, fill=(70, 110, 150, 100))
    hull = [(0, 2.0, 0), (22, 1.0, 0), (30, 5.5, 0), (22, 10.0, 0), (0, 9.0, 0)]
    iso.poly3([(a, b, 0.0) for a, b, _ in hull], fill=(150, 108, 70), ol=(90, 62, 38), lw=0.2)
    # 선체 측면(+Y쪽 면)
    iso.poly3([(0, 9.0, 0), (22, 10.0, 0), (22, 10.0, 3.6), (0, 9.0, 3.6)], fill=(176, 128, 84), ol=(90, 62, 38), lw=0.2)
    iso.poly3([(22, 10.0, 0), (30, 5.5, 0), (30, 5.5, 3.6), (22, 10.0, 3.6)], fill=(160, 114, 74), ol=(90, 62, 38), lw=0.2)
    iso.poly3([(0, 2.0, 3.6), (22, 1.0, 3.6), (30, 5.5, 3.6), (22, 10.0, 3.6), (0, 9.0, 3.6)], fill=(196, 150, 100), ol=(90, 62, 38), lw=0.2)
    for (X, Y) in [(3, 4), (7.5, 5.0), (12, 4.0), (5, 7.0)]:
        iso.box(X, Y, 3.6, X + 3.4, Y + 2.6, 6.0, ((226, 218, 196), (206, 196, 170), (176, 166, 140)), ol=(110, 100, 80), lw=0.12)
    iso.line3([(15, 5.5, 3.6), (15, 5.5, 20.0)], (110, 80, 50), 0.5)
    iso.fpoly("L", 0, 5.5, 3.6, [(15.4, 3.0), (24.0, 3.0), (24.0, 16.0), (15.4, 16.0)], (248, 244, 230), (150, 130, 98), 0.2)
    iso.fpoly("L", 0, 5.5, 3.6, [(15.4, 9.0), (24.0, 9.0)], None, (200, 180, 150), 0.15)


def draw_crane(L, cx, cy):
    """답차 기중기(treadwheel crane): 나무 틀, 큰 답차 바퀴, 지브와 줄."""
    iso = Iso(L, cx - 10.0, cy - 9.0)
    L.ell(cx + 2, cy + 8.0, 19.0, 4.6, fill=(120, 98, 64, 90))
    iso.box(0, 0, 0, 22, 14, 2.0, ((206, 190, 150), (190, 170, 128), (160, 140, 100)), ol=(110, 90, 60), lw=0.15)
    for (X, Y) in [(3, 11), (19, 11)]:
        iso.line3([(X, Y, 2.0), (X, Y, 22.0)], (126, 92, 56), 1.0)
    iso.line3([(3, 11, 22.0), (19, 11, 22.0)], (126, 92, 56), 0.9)
    pts = [(11 + 7.0 * math.cos(math.radians(a)), 12.2 + 7.0 * math.sin(math.radians(a))) for a in range(0, 360, 12)]
    iso.fpoly("L", 0, 11.0, 0.0, [(11 + 7.2 * math.cos(math.radians(a)), 9.4 + 7.2 * math.sin(math.radians(a))) for a in range(0, 360, 12)], (180, 140, 94), (96, 66, 40), 0.3)
    for a in range(0, 180, 30):
        r = math.radians(a)
        iso.fpoly("L", 0, 11.0, 0.0, [(11 + 7.0 * math.cos(r), 9.4 + 7.0 * math.sin(r)), (11 - 7.0 * math.cos(r), 9.4 - 7.0 * math.sin(r))], None, (96, 66, 40), 0.2)
    iso.line3([(11, 11, 22.0), (27, 11, 26.0)], (126, 92, 56), 0.8)
    iso.line3([(27, 11, 26.0), (27, 11, 12.0)], (110, 98, 84), 0.3)
    iso.box(26, 10, 9.0, 29, 12.5, 12.0, ((226, 218, 196), (206, 196, 170), (176, 166, 140)), ol=(110, 100, 80), lw=0.12)


def draw_bridge(L, cx, cy):
    """돌 아치 다리: 길(↘)이 강(↙)을 건넌다. (cx,cy)는 다리 중심(상판 중앙)의 화면 위치."""
    iso = Iso(L, cx - C30 * (13 - 3.2), cy - 0.5 * (13 + 3.2) + 1.8)
    STONE_B = ((226, 214, 186), (206, 192, 160), (176, 160, 128))
    # 상판(길 색) + 난간
    iso.box(0, 0, 0, 26, 6.4, 1.8, STONE_B, ol=(110, 90, 62), lw=0.18)
    iso.rect3(0, 0.9, 26, 5.5, 1.8, ROAD, ol=ROAD_E, lw=0.12)
    iso.box(0, 0, 1.8, 26, 0.9, 3.0, STONE_B, ol=(110, 90, 62), lw=0.12)
    iso.box(0, 5.5, 1.8, 26, 6.4, 3.0, STONE_B, ol=(110, 90, 62), lw=0.12)
    iso.arch("L", 0, 6.4, 0.0, 7.5, 18.5, 0.0, 0.2, (96, 128, 160), (70, 56, 40), lw=0.1)


def draw_barge(L, cx, cy):
    """테베레 바지선(↙ 방향): 화산재 포대를 실은 긴 배"""
    iso = Iso(L, cx - C30 * (3 - 14), cy - 0.5 * (3 + 14))
    L.ell(cx + 1, cy + 2.5, 15.0, 3.6, fill=(70, 110, 150, 90))
    hull = [(0.4, 0, 0.0), (5.6, 0, 0.0), (6.0, 22, 0.0), (3.0, 29, 0.0), (0.0, 22, 0.0)]
    iso.poly3(hull, fill=(150, 108, 70), ol=(90, 62, 38), lw=0.2)
    iso.poly3([(6.0, 22, 0), (6.0, 22, 3.2), (3.0, 29, 3.2), (3.0, 29, 0)], fill=(160, 114, 74), ol=(90, 62, 38), lw=0.2)
    iso.poly3([(5.6, 0, 0), (6.0, 22, 0), (6.0, 22, 3.2), (5.6, 0, 3.2)], fill=(176, 128, 84), ol=(90, 62, 38), lw=0.2)
    iso.poly3([(0.4, 0, 3.2), (5.6, 0, 3.2), (6.0, 22, 3.2), (3.0, 29, 3.2), (0.0, 22, 3.2)], fill=(196, 150, 100), ol=(90, 62, 38), lw=0.2)
    for (X, Y) in [(0.8, 2.0), (3.0, 5.4), (0.8, 8.8), (3.0, 12.2), (0.8, 15.6)]:
        iso.box(X, Y, 3.2, X + 2.4, Y + 3.0, 5.6, ((226, 218, 196), (206, 196, 170), (176, 166, 140)), ol=(110, 100, 80), lw=0.12)
    iso.line3([(3.0, 22, 3.2), (3.0, 22, 12.0)], (110, 80, 50), 0.4)


# ───────────────────────── Detail 확대 창(6단계 → 석회 알갱이) ─────────────────────────
def draw_zoom(L, cx, cy, D=72.0):
    r = D / 2.0
    L.ell(cx, cy, r, r, fill=(238, 224, 192), outline=C_DETAIL, lw=1.0)
    L.ell(cx, cy, r - 1.4, r - 1.4, outline=(255, 255, 255), lw=0.5)
    # 콘크리트 단면 확대: 모르타르 바탕 + 굵은 골재 + 흰 석회 알갱이 + 균열 + 결정
    L.ell(cx, cy, r - 3.0, r - 3.0, fill=(206, 200, 186))
    # 골재(둥근 돌) — 원 안쪽에 드는 것만
    for i in range(34):
        a = rnd() * 2 * math.pi
        rr = (r - 8) * math.sqrt(rnd())
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        sz = 1.4 + rnd() * 2.6
        L.ell(x, y, sz, sz * 0.8, fill=(142, 130, 116) if rnd() > 0.4 else (176, 164, 148), outline=(110, 100, 90), lw=0.15)
    # 흰 석회 알갱이
    for i in range(14):
        a = rnd() * 2 * math.pi
        rr = (r - 10) * math.sqrt(rnd())
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        sz = 1.2 + rnd() * 2.4
        L.ell(x, y, sz, sz * 0.82, fill=(253, 252, 248), outline=C_DETAIL, lw=0.25)
    # 균열(지그재그)과 방해석 결정
    zz = [(cx - 14, cy - 28), (cx - 8, cy - 18), (cx - 15, cy - 8), (cx - 7, cy + 2), (cx - 13, cy + 12), (cx - 6, cy + 24)]
    L.line(zz, (60, 46, 36), 0.7)
    for k in range(7):
        x, y = zz[1 + (k % 4)]
        L.poly([(x + 1.0 + k * 0.2, y - 2.0), (x + 3.0 + k * 0.2, y - 3.0), (x + 3.4 + k * 0.2, y - 0.4)], fill=(253, 252, 248), outline=C_DETAIL, lw=0.15)
    # 확대 창 안쪽 점선 십자(확대 단면 자리 표시)
    L.dashed((cx - r + 6, cy), (cx + r - 6, cy), (255, 255, 255), 0.3, 2.0, 1.6)
    L.dashed((cx, cy - r + 6), (cx, cy + r - 6), (255, 255, 255), 0.3, 2.0, 1.6)


# ───────────────────────── 지면: 바다·강·길 ─────────────────────────
RIVER_L2 = None      # 두 번째 구간 길이(계산)
RIVER_L3 = None
SEA_X_LEFT = 108.0
SEA_X_RIGHT = 225.0


def river_params():
    """강 중심선(±30°): 오른쪽 위 → A(직각) → ↘ → B(직각) → ↙ 하구."""
    xb = 215.0
    L2 = (xb - RIVER_A[0]) / C30
    xm = 112.0
    L3 = (xb - xm) / C30
    return L2, L3


def sea_polygon(cl):
    """바다: 강 북쪽 둑선에서 시작해 ↘로 꺾이는 해안선, 좌우는 부두 수직 변"""
    off = (RIVER_W / 2.0) / C30

    def yn(x):
        return cl[-1][1] - off + T30 * (cl[-1][0] - x)

    xl = SEA_X_LEFT
    nb = (xl, yn(xl))
    t = (SEA_X_RIGHT - xl) / C30
    rp = (SEA_X_RIGHT, nb[1] + 0.5 * t)
    return [nb, rp, (SEA_X_RIGHT, MAP_Y1 - 7.0), (xl, MAP_Y1 - 7.0)]


ROADS = []     # 각 길: 중심선 점 목록


def draw_ground(G, cl):
    """바다 → 강 → 길 순으로 지면 레이어에 그린다. 지면 선분은 모두 ±30°."""
    # 지형 결(등각 격자)
    for t in range(-700, 900, 20):
        for sgn in (1, -1):
            G.line([(0, 100 + t), (PW, 100 + t - sgn * PW * T30)], (206, 182, 136, 70), 0.2, joint=False)
    # 강
    poly, lft, rgt = band_poly(cl, RIVER_W, bevel=True)
    G.poly(poly, fill=RIVER, outline=RIVER_T, lw=0.4)
    for a, b in zip(cl[:-1], cl[1:]):
        log_seg("지면", a, b)
        G.dashed(a, b, (232, 244, 252), 0.25, 4.0, 5.0)
    # 바다(강 하구를 덮는다) + 해변 띠
    sea = sea_polygon(cl)
    beach = (244, 232, 200)
    nb_, rp_ = sea[0], sea[1]
    nx, ny = 0.5 * 3.2, -C30 * 3.2
    G.poly([nb_, rp_, (rp_[0] + nx, rp_[1] + ny), (nb_[0] + nx, nb_[1] + ny)], fill=beach)
    G.poly([(sea[0][0] - 3.0, sea[0][1] + 0.5), sea[0], sea[3], (sea[3][0] - 3.0, sea[3][1])], fill=beach)
    G.poly([sea[1], (sea[1][0] + 3.0, sea[1][1] - 0.5), (sea[2][0] + 3.0, sea[2][1]), sea[2]], fill=beach)
    G.poly(sea, fill=SEA, outline=SEA_D, lw=0.6)
    for (xq, sgn) in ((sea[0][0], -1), (sea[1][0], 1)):
        y_a = sea[0][1] if sgn < 0 else sea[1][1]
        G.line([(xq + sgn * 1.4, y_a + 1.0), (xq + sgn * 1.4, sea[3][1])], (150, 130, 98), 0.5, joint=False)
        yq = y_a + 6.0
        while yq < sea[3][1] - 3:
            G.ell(xq + sgn * 1.4, yq, 0.55, 0.45, fill=(120, 100, 72))
            yq += 9.0
    for a, b in zip(sea[:-1], sea[1:]):
        if abs(a[0] - b[0]) > 1e-6 and abs(a[1] - b[1]) > 1e-6:
            log_seg("지면", a, b)
    for i in range(70):
        x = 112 + (i * 29) % 108
        y = 388 + (i * 37) % 104
        if in_poly((x, y), sea):
            G.line([(x, y), (x + 4.0, y + 2.3)], (176, 206, 226), 0.3, joint=False)
            G.line([(x + 4.0, y + 2.3), (x + 6.0, y + 1.1)], (176, 206, 226), 0.3, joint=False)
    # 길: 가장자리색 굵은 띠를 먼저 모두 깔고, 그 위에 길 색 띠를 모두 덮어 교차로의 안쪽 경계선을 없앤다
    for road in ROADS:
        G.poly(band_poly(road, 5.4 + 0.8)[0], fill=ROAD_E)
    for road in ROADS:
        G.poly(band_poly(road, 5.4)[0], fill=ROAD)
    for road in ROADS:
        for a, b in zip(road[:-1], road[1:]):
            log_seg("지면", a, b)
            G.dashed(a, b, (218, 204, 176), 0.22, 2.4, 2.0)


# ───────────────────────── 조립 ─────────────────────────
POS = {
    "bath": (176, 138, 64),
    "pantheon": (245, 138, 66),
    "vesuvius": (326, 126, 52),
    "farm": (332, 127),
    "zoom": (58, 415, 66),
    "aqueduct": (270, 425, 68),
    "metella": (388, 440, 64),
    "vineyard": (398, 486),
    "field1": (188, 228),
    "field2": (212, 407),
    "portus": (150, 455, 64),
    "cart": (107, 355),
    "ship": (200, 478),
    "crane": (84, 479),
    "bridge": (133.5, 372.1),
    "barge": (342.0, 167.0),
}


# ───────────────────────── 라벨 명세 ─────────────────────────
def floor_line(L, ax, ay, parts, M):
    """바닥에 눕힌 한 줄 글(여러 글꼴 이어 붙임)"""
    u = 0.0
    (a, b), (c, d) = M
    for (txt, font, col) in parts:
        iso_text(L, txt, font, col, M, ax + a * u, ay + c * u)
        u += tw(txt, font) + 1.6
    return u


LABEL_SPECS = [
    # (이름, 대상 점, 방향 M, 위치 mode, 브래킷 쪽, 색, 영문, 국문, 원어 위첨자, 본문, gap)
    ("아레나", (236.0, 306.0), M_WALL_DN, "above", "R", C_ARENA_T, ["COLOSSEUM"], "콜로세움 아레나", None,
     ["겉은 석회화, 속과 기초는", "콘크리트로 채움", "무너짐의 주원인:", "지반·석재 반출·관리 부재"], 2.4),
    ("욕장", (176.0, 156.5), M_WALL_UP, "below", "L", C_SUP_T, ["CARACALLA BATHS"], "카라칼라 욕장", None,
     ["열탕실 복원 상상도", "오큘러스·코퍼는 복원 추정", "냉탕실 열주를 합친 복합도", "겉은 벽돌, 속은 콘크리트"], 9.5),
    ("판테온", (245.0, 156.5), M_WALL_UP, "below", "L", C_SUP_T, ["PANTHEON"], "판테온", None,
     ["철근 없는 콘크리트 돔", "지름 43.3m", "위로 갈수록 가벼운 골재"], 9.5),
    ("수도교", (270.0, 443.5), M_WALL_DN, "below", "L", C_SUP_T, ["AQUA CLAUDIA"], "아쿠아 클라우디아", None,
     ["석재 아치에 하드리아누스기", "벽돌면 콘크리트로 보수한", "구간(붉은 두 칸)"], 9.5),
    ("메텔라 무덤", (356.0, 440.0), M_WALL_DN, "above", "R", C_SUP_T, ["CAECILIA METELLA"], "카이킬리아 메텔라 무덤", None,
     ["지름 29m 콘크리트 드럼", "젖을 때마다 류사이트가", "녹아 접합부를 다시 짬", "※ 알갱이 치유와는 다름"], 2.4),
    ("포르투스 항", (150.0, 436.0), M_WALL_DN, "above", "R", C_SUP_T, ["PORTUS"], "포르투스 항", None,
     ["트라야누스 육각 내항", "(약 100~112년)", "방파제 모르타르: 로마", "근교+포추올리 화산재", "바닷물은 항구 구조물만"], 2.4),
]
FLAG_SPECS = [
    # (이름, 대상 점, M, 색, 영문, 국문, 깃대 쪽, mode, 깃대 길이)
    ("베수비오", (341.3, 114.0), M_WALL_UP, C_SUP_T, "VESUVIUS", "베수비오", "L", "above", 9.0),
    ("수레", (107.0, 353.0), M_WALL_DN, C_INK, "CART", "수레", "L", "above", 12.0),
    ("화산재 운반선", (200.0, 468.0), M_WALL_DN, C_INK, "ASH SHIP", "화산재 운반선", "L", "above", 8.0),
    ("답차 기중기", (84.0, 463.0), M_WALL_DN, C_INK, "CRANE", "답차 기중기", "L", "above", 6.0),
    ("확대 창", (36.8, 389.7), M_WALL_DN, C_DETAIL_T, "DETAIL", "확대 창", "R", "above", 8.0),
    ("테베레 바지선", (343.0, 163.0), M_WALL_UP, C_INK, "BARGE", "바지선", "L", "below", 10.0),
]


def draw_labels(LB):
    for (nm, T, M, mode, side, col, en, ko, sup, body, gap) in LABEL_SPECS:
        draw_label(LB, T, en, ko, body, col, M, mode=mode, side=side, sup=sup, name=nm, gap=gap, plate=(nm == "포르투스 항"))
    for (nm, T, M, col, en, ko, side, mode, pole) in FLAG_SPECS:
        draw_flag(LB, T, en, ko, col, M, side=side, name=nm, mode=mode, pole=pole)


def setup_roads():
    global ROADS
    ROADS = []
    R_ = ARENA_R
    cy_, xl_ = ARENA_CY, ARENA_XL
    cx_ = ARENA_CX
    yb = cy_ + 0.654 * R_                       # 광장 정면 변 y
    F = (cx_ - 12.0, yb)
    ROADS.append(walk(F, [("SE", 170.0)]))                                  # 아피아 가도(오른쪽 액자 밖으로)
    # 공정(6단계) → 다리 → 아레나 광장 남서 변
    q = (78.0 + C30 * 100.0, 340.1 + 0.5 * 100.0)
    yl = cy_ + 0.271 * R_
    ex = (q[1] + T30 * q[0] - yl + T30 * xl_) / (2 * T30)
    ne = (ex - q[0]) / C30
    ROADS.append(walk((78.0, 340.1), [("SE", 100.0), ("NE", ne)]))
    # T자 교차: 위 길의 북동 구간에서 갈라져 수도교 윗 꼭짓점으로
    ax_, ay_, aw_ = POS["aqueduct"]
    top = (ax_, ay_ - aw_ / SQ3 / 2.0)
    # 북동 구간 위의 점 P(t) = q + t·NE 에서 SE로 s만큼 가면 top에 닿는다
    dx, dy = top[0] - q[0], top[1] - q[1]
    t = (dx / C30 - 2.0 * dy) / 2.0
    sl_ = (dx / C30 + 2.0 * dy) / 2.0
    P = (q[0] + C30 * t, q[1] - 0.5 * t)
    ROADS.append(walk(P, [("SE", sl_)]))


def build_map():
    page = Layer(0, 0, PW, PH, "page", bg=BG + (255,))
    cl_params = river_params()
    cl = river_centerline(*cl_params)
    setup_roads()
    ground = Layer(0, MAP_Y0, PW, MAP_Y1, "지면")
    draw_ground(ground, cl)
    page.paste(ground)
    objs = []

    def add(name, tier, region, fn, *args):
        l = Layer(*region, name)
        fn(l, *args)
        m = l.measure()
        objs.append({"이름": name, "티어": tier, "레이어": l, "측정": m, "경계접촉": clip_edge_touch(l) and not (name == "아레나")})
        page.paste(l)
        return l

    bx, by, bw = POS["bath"]
    vx, vy, vw = POS["vesuvius"]
    add("베수비오", "Support-2", (vx - 40, vy - 40, vx + 40, vy + 28), draw_vesuvius, vx, vy, vw)
    fx, fy = POS["farm"]
    add("포도밭 농장", "소품", (fx - 24, fy - 20, fx + 24, fy + 18), draw_farm, fx, fy)
    add("욕장", "Support", (bx - 46, by - 46, bx + 46, by + 36), draw_bath, bx, by, bw)
    px, py, pw = POS["pantheon"]
    add("판테온", "Support", (px - 46, py - 46, px + 46, py + 36), draw_pantheon, px, py, pw)
    add("아레나", "아레나", (ARENA_XL - 8, 170, 448, 392), draw_arena)
    add("Core 제작 과정", "Core", (8, 125, 170, 380), draw_core)
    zx, zy, zd = POS["zoom"]
    add("확대 창", "Detail", (zx - zd / 2 - 2, zy - zd / 2 - 2, zx + zd / 2 + 2, zy + zd / 2 + 2), draw_zoom, zx, zy, zd)
    ax, ay, aw = POS["aqueduct"]
    add("수도교", "Support", (ax - 46, ay - 46, ax + 46, ay + 36), draw_aqueduct, ax, ay, aw)
    mx, my, mw = POS["metella"]
    add("카이킬리아 메텔라 무덤", "Support", (mx - 46, my - 46, mx + 46, my + 36), draw_metella, mx, my, mw)
    qx, qy, qw = POS["portus"]
    add("포르투스 항", "Support", (qx - 42, qy - 40, qx + 62, qy + 36), draw_portus, qx, qy, qw)
    cx_, cy_ = POS["cart"]
    add("수레", "소품", (cx_ - 26, cy_ - 22, cx_ + 26, cy_ + 20), draw_cart, cx_, cy_)
    sx_, sy_ = POS["ship"]
    add("화산재 운반선", "소품", (sx_ - 28, sy_ - 24, sx_ + 28, sy_ + 20), draw_ship, sx_, sy_)
    rx_, ry_ = POS["crane"]
    add("답차 기중기", "소품", (rx_ - 28, ry_ - 28, rx_ + 28, ry_ + 20), draw_crane, rx_, ry_)
    gx, gy = POS["bridge"]
    add("돌 다리", "소품", (gx - 22, gy - 16, gx + 22, gy + 16), draw_bridge, gx, gy)
    vx2, vy2 = POS["vineyard"]
    add("포도밭 구획", "소품", (vx2 - 26, vy2 - 18, vx2 + 26, vy2 + 14), draw_vineyard, vx2, vy2)
    f1x, f1y = POS["field1"]
    add("올리브 과수원", "소품", (f1x - 26, f1y - 20, f1x + 26, f1y + 18), draw_field, f1x, f1y, "olive")
    f2x, f2y = POS["field2"]
    add("곡식밭", "소품", (f2x - 26, f2y - 18, f2x + 26, f2y + 16), draw_field, f2x, f2y, "grain")
    bgx, bgy = POS["barge"]
    add("테베레 바지선", "소품", (bgx - 22, bgy - 22, bgx + 22, bgy + 20), draw_barge, bgx, bgy)
    return {"page": page, "objs": objs, "river": cl, "ground": ground}


def build_labels(R):
    LABELS.clear()
    LB = Layer(0, MAP_Y0 - 10, PW, MAP_Y1 + 10, "라벨")
    draw_labels(LB)
    # 지형명: 바닥에 눕혀 지형색 톤온톤으로(강은 ↗ 기준선, 길·바다는 ↘ 기준선), 지시선 없음
    fe3, fk3 = fnt("en", 3.4 / 0.71), fnt("b", 3.2)
    cxr = 372.0
    cyr = RIVER_A[1] - T30 * (cxr - RIVER_A[0])
    floor_line(LB, cxr + 0.82, cyr + 1.43, [("TIBER", fe3, RIVER_T), ("테베레강", fk3, RIVER_T)], M_FLOOR_NE)
    F0 = (ARENA_CX - 12.0, ARENA_CY + 0.654 * ARENA_R)
    cxa = F0[0] + 30.0
    cya = F0[1] + T30 * 30.0
    floor_line(LB, cxa - 0.82, cya + 1.43, [("VIA APPIA", fe3, (126, 106, 76)), ("아피아 가도", fk3, (126, 106, 76))], M_FLOOR_SE)
    draw_floor_name(LB, 178.0, 431.0, "티레니아해", "TYRRHENIAN SEA", (60, 96, 132), kind="SE", em=3.4)
    # 6단계 → 확대 창: 셀 앞 꼭짓점의 굳은 단면에서 수직 지시선(끝점은 대상 쪽)
    zx, zy, zd = POS["zoom"]
    bx_, by_ = cell_verts(NCELL - 1)["B"][0], cell_verts(NCELL - 1)["B"][1] - 12.4
    LB.line([(bx_, by_), (bx_, zy - zd / 2.0)], C_DETAIL_T, LEAD_LW, joint=False, kind="지시선")
    LB.dot(bx_, by_, DOT_R, C_DETAIL_T)
    LABELS.append({"이름": "확대 창 지시선", "종류": "지시선", "다각형": [], "대상": (bx_, by_), "열": ""})
    # 확대 창 → 하단 Detail 패널(석회 알갱이·자가치유): 수직 지시선, 끝점은 패널 윗변
    bx2 = bx_
    LB.line([(bx2, zy + zd / 2.0), (bx2, PANEL_RECT["석회"][1])], C_DETAIL_T, LEAD_LW, joint=False, kind="지시선")
    LB.dot(bx2, PANEL_RECT["석회"][1], DOT_R, C_DETAIL_T)
    R["page"].paste(LB)
    R["labels"] = LB


def render_panels(R):
    page = R["page"]
    rows = []
    funcs = [("정의", "Basic", "로마 콘크리트란?", panel_definition), ("레시피", "Basic", "레시피·순서", panel_recipe),
             ("위치도", "Basic", "위치도", panel_where), ("석회", "Detail", "석회 알갱이 패널", panel_lime),
             ("연대기", "Basic", "연대기·근거", panel_history), ("수명비교", "Basic", "100 vs 2000", panel_100v2000)]
    for key, tier, nm, fn in funcs:
        x0, y0, x1, y1 = PANEL_RECT[key]
        l = Layer(x0 - 3, y0 - 3, x1 + 3, y1 + 3, nm)
        fn(l)
        m = l.measure()
        rows.append({"이름": nm, "티어": tier, "측정": m, "레이어": l, "구획": (x0, y0, x1, y1)})
        page.paste(l)
    R["panels"] = rows
    draw_title(page)


def draw_footer(P, R=None):
    x0, y0, x1, y1 = 18, 568, 402, 581
    P.dashed_rect(x0, y0, x1, y1, C_GREY, lw=0.3, dash=2.6, gap=1.5)
    P.rect(x0 + 2, y0 + 2, x0 + 40, y1 - 2, outline=C_GREY, lw=0.25)
    P.text_c(x0 + 21, y0 + 7.8, "로고 자리", fnt("m", 2.3), C_GREY)
    P.rect(x1 - 40, y0 + 2, x1 - 2, y1 - 2, outline=C_GREY, lw=0.25)
    P.text_c(x1 - 21, y0 + 7.8, "QR 자리", fnt("m", 2.3), C_GREY)
    # 1줄: 티어 색 범례
    items = [("Hero", "아레나(티어 없음)"), ("Core", "제작 과정"), ("Basic", "기본 정보"), ("Detail", "확대·세부"), ("Support", "사례"), ("Support-2", "베수비오")]
    cx = x0 + 45
    fch, fb = fnt("s", 2.0), fnt("m", 2.0)
    for tier, desc in items:
        col = C_ARENA_T if tier == "Hero" else TIER_COL[tier]
        w = tw(tier, fch) + 2.4
        P.rect(cx, y0 + 1.6, cx + w, y0 + 4.8, fill=col)
        P.text_c(cx + w / 2, y0 + 4.1, tier, fch, (255, 255, 255))
        P.text(cx + w + 1.0, y0 + 4.1, desc, fb, INK)
        cx += w + tw(desc, fb) + 4.2
    # 2줄: 주석
    P.text(x0 + 45, y0 + 7.8, "※ 와이어프레임 v16: 배치 도식(최종 렌더 아님) · 거리·방위는 구도 우선으로 압축, 실제 위치는 위치도 · 베수비오는 79년 이전 모습(복원 상상도) · 크기는 투영 기준 아레나 > Core > Basic·Detail > Support > Support-2", fnt("m", 1.8), C_GREY)
    # 3줄: 자동 실측 치수(치수는 라벨이 아니라 이 줄로만 표기)
    if R is not None and "areas" in R:
        order = ["아레나", "Core 제작 과정", "확대 창", "욕장", "판테온", "수도교", "카이킬리아 메텔라 무덤", "트라야누스 시장", "포르투스 항", "베수비오"]
        short = {"Core 제작 과정": "Core", "카이킬리아 메텔라 무덤": "메텔라 무덤", "포르투스 항": "포르투스"}
        parts = []
        for nm in order:
            if nm in R["areas"]:
                t, ar, aa, w_, h_ = R["areas"][nm]
                parts.append("%s %.0f×%.0f" % (short.get(nm, nm), w_, h_))
        P.text(x0 + 45, y0 + 11.2, "투영 크기(폭×높이 mm, 레이어 자동 실측): " + " · ".join(parts), fnt("m", 1.8), C_GREY)


# ───────────────────────── 분석(자동 실측·검사) ─────────────────────────
S2 = 2


def _empty_mask():
    return Image.new("L", (PW * S2, PH * S2), 0)


def layer_mask(layer):
    a = layer.alpha_mask()
    f = KD // S2
    small = a.resize((max(1, a.width // f), max(1, a.height // f)), Image.BOX).point(lambda v: 255 if v > 100 else 0)
    full = _empty_mask()
    full.paste(255, (int(round(layer.x0 * S2)), int(round(layer.y0 * S2))), small)
    return full


def poly_mask(poly):
    m = _empty_mask()
    ImageDraw.Draw(m).polygon([(x * S2, y * S2) for x, y in poly], fill=255)
    return m


def area_of(mask):
    return mask.histogram()[255] / float(S2 * S2)


def inter_area(m1, m2):
    return area_of(ImageChops.multiply(m1, m2))


def largest_empty_rect(occ, region):
    one = occ.resize((PW, PH), Image.BOX).point(lambda v: 255 if v > 0 else 0)
    x0, y0, x1, y1 = region
    crop = one.crop((x0, y0, x1, y1))
    w, h = crop.size
    data = crop.tobytes()
    heights = [0] * w
    best_area, best = 0, None
    for r in range(h):
        row = data[r * w:(r + 1) * w]
        for c in range(w):
            heights[c] = 0 if row[c] else heights[c] + 1
        stack = []
        for c in range(w + 1):
            hc = heights[c] if c < w else 0
            start = c
            while stack and stack[-1][1] >= hc:
                st, hh = stack.pop()
                area = (c - st) * hh
                if area > best_area:
                    best_area = area
                    best = (x0 + st, y0 + r - hh + 1, x0 + c, y0 + r + 1)
                start = st
            stack.append((start, hc))
    return best_area, best


def angle_of(p0, p1):
    return math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0])) % 180.0


def near(a, targets, tol=0.6):
    return any(min(abs(a - t), 180 - abs(a - t)) <= tol for t in targets)


BJ_ZONES = {"T(타이틀)": (128, 10, 295, 92), "L1": (18, 20, 125, 65), "L2": (18, 75, 135, 150), "R1": (318, 20, 412, 102),
            "B1": (18, 505, 180, 565), "B2": (182, 505, 305, 565), "B3": (318, 505, 412, 565), "F(푸터)": (18, 568, 412, 586)}
BJ_OBJECTS = {"아레나": ("자금성 블록(중심 블록)", (216.3, 182.4, 419.8, 381.1)),
              "Core 제작 과정": ("CCTV 타워(세로 척추)", (23.1, 185.8, 98.5, 428.2)),
              "욕장": ("이화원(위쪽 줄)", (144.5, 111.8, 242.3, 192.8)),
              "베수비오": ("만리장성(가장 먼 대상)", (233.1, 80.6, 303.0, 141.9)),
              "수도교": ("798 예술구(아래 줄)", (231.0, 428.2, 334.3, 504.4)),
              "포르투스 항": ("고속철(아래 줄 왼쪽)", (0.0, 420.0, 88.0, 495.3))}


def analyze(R):
    out = []
    P = out.append
    objs = {o["이름"]: o for o in R["objs"]}
    # ── 1. 투영 크기 검사표(렌더한 레이어를 알파 외곽 상자로 자동 실측)
    rows = []
    for o in R["objs"]:
        if o["이름"] == "포도밭 농장" or o["티어"] == "소품":
            continue
        rows.append((o["티어"], o["이름"], o["측정"]))
    for pnl in R["panels"]:
        rows.append((pnl["티어"], pnl["이름"], pnl["측정"]))
    order = {"아레나": 0, "Core": 1, "Basic": 2, "Detail": 2, "Support": 3, "Support-2": 4}
    rows.sort(key=lambda r: (order[r[0]], -((r[2]["box"][2] - r[2]["box"][0]) * (r[2]["box"][3] - r[2]["box"][1]))))
    P("투영 크기 검사표(화면 폭×높이 mm, 레이어 알파 외곽 상자 자동 실측 · 면적 mm²):")
    P("  %-10s %-18s %12s %12s %12s" % ("티어", "요소", "폭×높이", "상자 면적", "실점유 면적"))
    areas = {}
    for tier, nm, m in rows:
        b = m["box"]
        w_, h_ = b[2] - b[0], b[3] - b[1]
        ar = w_ * h_
        areas[nm] = (tier, ar, m["area"], w_, h_)
        P("  [%-9s] %-14s %6.1f×%-5.1f %10.0f %12.0f" % (tier, nm, w_, h_, ar, m["area"]))
    # ── 2. 위계 검사(상자 면적 기준 + 실점유 기준, 마진 10%)
    def agg(tiers, idx, fn):
        vals = [(v[idx], n) for n, v in areas.items() if v[0] in tiers]
        return fn(vals)

    A = agg(("아레나",), 1, max)
    C = agg(("Core",), 1, max)
    BDmin = agg(("Basic", "Detail"), 1, min)
    BDmax = agg(("Basic", "Detail"), 1, max)
    Sp = agg(("Support",), 1, max)
    Spmin = agg(("Support",), 1, min)
    S2v = agg(("Support-2",), 1, max)
    ok_box = A[0] > C[0] > BDmin[0] > Sp[0] > S2v[0] and C[0] > BDmax[0]
    margin_ok = (A[0] >= 1.10 * C[0]) and (BDmin[0] >= 1.10 * Sp[0]) and (Spmin[0] >= 1.10 * S2v[0])
    Aa = agg(("아레나",), 2, max)
    Ca = agg(("Core",), 2, max)
    ok_pix = Aa[0] > Ca[0]
    P("위계 검사(상자 면적): 아레나 %.0f > Core %.0f > Basic·Detail 최소 %.0f(%s) > Support 최대 %.0f(%s) > Support-2 %.0f → %s" %
      (A[0], C[0], BDmin[0], BDmin[1], Sp[0], Sp[1], S2v[0], "통과" if ok_box else "실패"))
    P("  마진 10%% 조건(아레나≥Core×1.10, Basic·Detail 최소≥Support 최대×1.10, Support 최소≥Support-2×1.10): %s" % ("통과" if margin_ok else "미달"))
    P("  실점유(알파) 기준: 아레나 %.0f vs Core %.0f → %s · Core 상자 > Basic·Detail 최대 %.0f(%s): %s" % (Aa[0], Ca[0], "통과" if ok_pix else "실패", BDmax[0], BDmax[1], "통과" if C[0] > BDmax[0] else "실패"))
    R["ok_hier"] = ok_box and margin_ok
    R["areas"] = areas
    # ── 3. 베이징 구획·오브젝트 위치 대조(mm 차이)
    P("베이징 구획 대조(3.1절 좌표 대비, 단위 mm; 우측 여백 18mm 통일로 의도한 차이 포함):")
    mine = {"L1": PANEL_RECT["정의"], "L2": PANEL_RECT["레시피"], "R1": PANEL_RECT["위치도"], "B1": PANEL_RECT["석회"], "B2": PANEL_RECT["연대기"], "B3": PANEL_RECT["수명비교"],
            "T(타이틀)": (126.5, 10, 293.5, 92), "F(푸터)": (18, 568, 402, 581)}
    for k, bj in BJ_ZONES.items():
        m_ = mine[k]
        d = tuple(round(m_[i] - bj[i], 1) for i in range(4))
        P("  %-9s 베이징 %s → 도면 %s  차이(좌,상,우,하) %s" % (k, bj, m_, d))
    P("베이징 오브젝트 위치 대조(실측 bj_objects 대비 박스 차이, mm):")
    for nm, (bjn, bb) in BJ_OBJECTS.items():
        m = objs[nm]["측정"]["box"]
        d = tuple(round(m[i] - bb[i], 1) for i in range(4))
        P("  %-12s ↔ %-20s 도면 (%.1f,%.1f,%.1f,%.1f) 차이(좌,상,우,하) %s" % (nm, bjn, m[0], m[1], m[2], m[3], d))
    # ── 4. 밀도·빈자리·최근접 간격
    obj_masks = {}
    union = _empty_mask()
    for o in R["objs"]:
        mk = layer_mask(o["레이어"])
        obj_masks[o["이름"]] = mk
        union = ImageChops.lighter(union, mk)
    map_box = (0, MAP_Y0 * S2, PW * S2, MAP_Y1 * S2)
    map_area = PW * (MAP_Y1 - MAP_Y0)
    cov = area_of(union.crop(map_box)) if False else union.crop(map_box).histogram()[255] / float(S2 * S2)
    P("오브젝트 점유율: 지도 무대(%d×%d=%d mm²) 중 %.1f%% (베이징 46.2%%, 목표 42~48%%) · 오브젝트 수 %d개(소품 포함, 베이징 16개)" % (PW, MAP_Y1 - MAP_Y0, map_area, 100.0 * cov / map_area, len(R["objs"])))
    ea, eb = largest_empty_rect(union, (0, MAP_Y0, PW, MAP_Y1))
    P("최대 빈 직사각형(오브젝트만 기준): %.0f×%.0f mm = %.0f mm² (지도의 %.1f%%) 위치 %s" % (eb[2] - eb[0], eb[3] - eb[1], ea, 100.0 * ea / map_area, eb))
    # 최근접 이웃 간격
    P("최근접 이웃 간격(오브젝트 상자 아닌 실제 화소 기준, mm; ≥24면 '24+'):")
    names = [o["이름"] for o in R["objs"]]
    small = {n: obj_masks[n].resize((PW, PH), Image.BOX).point(lambda v: 255 if v > 0 else 0) for n in names}
    gaps = {}
    for n in names:
        cur = small[n]
        found = {}
        for step in range(1, 13):
            cur = cur.filter(ImageFilter.MaxFilter(5))
            for m_ in names:
                if m_ == n or m_ in found:
                    continue
                if ImageChops.multiply(cur, small[m_]).getbbox():
                    found[m_] = 2 * step
            if len(found) == len(names) - 1:
                break
        if found:
            k = min(found, key=lambda z: found[z])
            gaps[n] = (found[k], k)
        else:
            gaps[n] = (24, "-")
    P("  " + " · ".join("%s→%s %s" % (n, g[1], ("≤%d" % g[0]) if g[0] < 24 else "24+") for n, g in gaps.items()))
    R["masks"] = obj_masks
    R["union"] = union
    # ── 5. 지면 지형 마스크
    cl = R["river"]
    river_poly = band_poly(cl, RIVER_W, bevel=True)[0]
    m_river = poly_mask(river_poly)
    m_roads = _empty_mask()
    for road in ROADS:
        m_roads = ImageChops.lighter(m_roads, poly_mask(band_poly(road, 5.4)[0]))
    m_sea = poly_mask(sea_polygon(cl))
    # ── 6. 지시선·글줄 각도 검사
    tot = {"지면": 0, "지시선": 0, "글줄": 0}
    bad = []
    for kind, p0, p1 in SEG_LOG:
        if math.hypot(p1[0] - p0[0], p1[1] - p0[1]) < 1e-6:
            continue
        ang = angle_of(p0, p1)
        tot[kind] += 1
        if kind == "지면":
            good = near(ang, (30.0, 150.0))
        elif kind == "지시선":
            good = near(ang, (90.0, 30.0, 150.0))
        else:
            good = near(ang, (30.0, 150.0))
        if not good:
            bad.append((kind, round(ang, 1), tuple(round(v, 1) for v in p0)))
    P("각도 검사(허용: 지면 ±30°, 지시선 수직·±30°, 지도 위 글줄 ±30°; 오차 ±0.6°): 지면 선분 %d · 지시선 %d · 글줄 %d → 어긋남 %d개 %s" % (tot["지면"], tot["지시선"], tot["글줄"], len(bad), bad[:4]))
    up_n = sum(1 for k_, a_, b_ in SEG_LOG if k_ == "글줄" and near(angle_of(a_, b_), (150.0,)))
    dn_n = sum(1 for k_, a_, b_ in SEG_LOG if k_ == "글줄" and near(angle_of(a_, b_), (30.0,)))
    P("지도 위 글줄 평면(화면 평행 0°는 0개): 기준선 ↗(북서 구역 벽면·강 바닥) %d · 기준선 ↘(그 밖의 벽면·바닥) %d · 지시선은 전부 수직" % (up_n, dn_n))
    cl_ = R["river"]
    segs_ = [(round(angle_of(cl_[i], cl_[i + 1]), 1), round(math.hypot(cl_[i + 1][0] - cl_[i][0], cl_[i + 1][1] - cl_[i][1]))) for i in range(len(cl_) - 1)]
    ent_y = RIVER_A[1] - T30 * (PW - RIVER_A[0])
    P("강 중심선: 구간 %d개 (화면 각도°, 길이mm) %s · 지면 축 ±30°만 사용(수직 구간 0) · 직각(평면) 꺾임 %d곳 · 액자 오른쪽 변 진입점 y=%.0fmm(오른쪽 위에서 대각 진입)" % (len(segs_), segs_, len(segs_) - 1, ent_y))
    P("아레나 받침: 팔각 외접 반지름 %.1fmm(화면 폭 %.1fmm), 왼쪽 수직 변 x=%.0fmm, 우측 수직 변 x=%.1fmm(액자 오른쪽 변 %dmm 밖 %.1fmm로 블리드 — 광장이 액자 밖으로 이어짐) · 화산 %d개(베수비오) · 욕장 %d개" % (
        ARENA_R, 2.263 * ARENA_R, ARENA_XL, ARENA_CX + 1.1316 * ARENA_R, PW, ARENA_CX + 1.1316 * ARENA_R - PW, sum(1 for o in R["objs"] if o["티어"] == "Support-2"), sum(1 for o in R["objs"] if o["이름"] == "욕장")))
    # ── 7. 라벨 충돌 검사(라벨 글 상자 ↔ 오브젝트·강·길·다른 라벨)
    P("라벨 충돌 검사(글 상자와 겹침 면적 mm², 0이어야 함):")
    lab_masks = []
    nbad = 0
    for rec in LABELS:
        if len(rec["다각형"]) < 3:
            lab_masks.append(None)
            continue
        lm = poly_mask(rec["다각형"])
        lab_masks.append(lm)
        hits = []
        for n, mk in obj_masks.items():
            a_ = inter_area(lm, mk)
            if a_ > 0.5:
                hits.append("%s %.0f" % (n, a_))
        for nm_, mk in (("강", m_river), ("길", m_roads)):
            a_ = inter_area(lm, mk)
            if a_ > 0.5:
                hits.append("%s %.0f" % (nm_, a_))
        # 패널 구획·지도 경계
        bb = [min(p[0] for p in rec["다각형"]), min(p[1] for p in rec["다각형"]), max(p[0] for p in rec["다각형"]), max(p[1] for p in rec["다각형"])]
        if bb[0] < 6 or bb[2] > PW - 4 or bb[1] < MAP_Y0 + 2 or bb[3] > MAP_Y1 - 2:
            hits.append("지도 경계 밖")
        for key, (x0, y0, x1, y1) in PANEL_RECT.items():
            if bb[2] > x0 and bb[0] < x1 and bb[3] > y0 and bb[1] < y1:
                hits.append("패널 " + key)
        if hits:
            nbad += 1
        P("  %-14s 상자 (%.0f,%.0f)-(%.0f,%.0f) %s" % (rec["이름"], bb[0], bb[1], bb[2], bb[3], ("충돌: " + ", ".join(hits)) if hits else "충돌 없음"))
    for i in range(len(LABELS)):
        for j in range(i + 1, len(LABELS)):
            if lab_masks[i] is not None and lab_masks[j] is not None:
                a_ = inter_area(lab_masks[i], lab_masks[j])
                if a_ > 0.5:
                    nbad += 1
                    P("  라벨끼리 겹침: %s ↔ %s %.0f" % (LABELS[i]["이름"], LABELS[j]["이름"], a_))
    R["label_collisions"] = nbad
    # ── 8. 강: 받침·오브젝트와의 간격
    ov = [(n, inter_area(m_river, mk)) for n, mk in obj_masks.items() if inter_area(m_river, mk) > 0.5 and n not in ("돌 다리", "테베레 바지선")]
    P("강 간격 검사: 강 띠와 오브젝트 겹침(mm², 다리·바지선은 강 위에 놓는 것이라 제외): " + (", ".join("%s %.0f" % (n, a_) for n, a_ in ov) if ov else "겹침 없음"))
    R["river_overlap"] = ov
    # 강 중심선과 아레나 받침·베수비오·Core 사이 최소 간격(mm, 0.5mm 단위 근사)
    gaps2 = {}
    for nm_ in ("아레나", "Core 제작 과정", "욕장", "판테온", "베수비오"):
        cur = m_river
        g_ = None
        for step in range(1, 25):
            cur = cur.filter(ImageFilter.MaxFilter(3))
            if ImageChops.multiply(cur, obj_masks[nm_]).getbbox():
                g_ = step * 0.5
                break
        gaps2[nm_] = g_
    P("강 띠 가장자리와의 최소 간격(mm): " + " · ".join("%s %s" % (k_, ("%.1f" % v_) if v_ is not None else "12+") for k_, v_ in gaps2.items()))
    # 베수비오 밑동을 앞 요소(농장)가 가리는 면적
    fv = inter_area(obj_masks["포도밭 농장"], obj_masks["베수비오"])
    P("베수비오 밑동 가림: 앞 요소(포도밭 농장)와 겹친 면적 %.0f mm² (밑동 아래 약 5~6mm 띠)" % fv)
    R["m_river"], R["m_roads"], R["m_sea"] = m_river, m_roads, m_sea
    return out


def main():
    R = build_map()
    build_labels(R)
    render_panels(R)
    lines = analyze(R)
    draw_footer(R["page"], R)
    finish(R["page"], "wireframe_v16.png")
    small = Image.open(os.path.join(OUT_DIR, "wireframe_v16.png")).resize((840, 1188), Image.LANCZOS)
    small.save(os.path.join(OUT_DIR, "wireframe_v16_small.png"))
    for ln in lines:
        print(ln)
    print("와이어프레임 v16 생성: out/wireframe_v16.png")
    return R


def finish(page, name):
    out = page.img.resize((PW * K, PH * K), Image.LANCZOS).convert("RGB")
    os.makedirs(OUT_DIR, exist_ok=True)
    out.save(os.path.join(OUT_DIR, name))
    return out


if __name__ == "__main__":
    main()
