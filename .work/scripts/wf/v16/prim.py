# -*- coding: utf-8 -*-
# 로마 콘크리트 A2 와이어프레임 — 로우폴리 원시 도형 라이브러리(삼각 면·다각 면 메시, 면별 음영, 지층 받침, 레이어 효과)
# 담당 패키지: global · 모든 담당 모듈이 읽기 전용으로 쓴다:  from prim import *
# - 좌표: Iso 평면 좌표(X → 화면 ↘, Y → 화면 ↙, Z → 위, 단위 = 화면 변 길이 mm). 보는 방향은 +X+Y+Z 쪽에서 원점.
# - 음영: 램버트. 빛은 왼쪽 위(평면 −X·+Y·+Z 쪽)에서 온다. 윗면 = 기본색 1.0, 왼면(+Y향) ≈ 0.83, 오른면(+X향) ≈ 0.63.
#   면마다 위치 해시로 정한 작은 밝기 흔들림을 준다(공유 난수 rnd()를 쓰지 않아 다른 모듈의 난수 순서를 바꾸지 않는다).
# - 깊이: 면 중심의 X+Y+Z가 작은(먼) 것부터 그린다(화가 알고리즘). 한 Mesh 안에서만 정렬되므로, 서로 가리는 부품은 한 Mesh에 모아 그린다.
# - 그림자: 그림자는 objects() 명세의 "shadow" 함수로 따로 그리면 크기 자동 실측에서 빠진다(main.py 참고).
from common import *
import common as C
import zlib, random


# ───────────────────────── 벡터 ─────────────────────────
def _n3(v):
    l = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / l, v[1] / l, v[2] / l)


def _sub3(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot3(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def newell(pts):
    """다각형 법선(뉴웰 방식, 꼭짓점 4개 이상에도 안정)"""
    nx = ny = nz = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0, z0 = pts[i]
        x1, y1, z1 = pts[(i + 1) % n]
        nx += (y0 - y1) * (z0 + z1)
        ny += (z0 - z1) * (x0 + x1)
        nz += (x0 - x1) * (y0 + y1)
    return _n3((nx, ny, nz))


LIGHT = _n3((-0.35, 0.55, 1.0))      # 빛이 오는 방향(평면 좌표)
VIEW = _n3((1.0, 1.0, 1.0))          # 화면 앞(보는 사람) 방향
AMB, DIF = 0.62, 0.44
_TOPF = AMB + DIF * LIGHT[2]
# 그림자가 바닥에 떨어지는 방향(높이 1당 평면 이동량)
SHADOW_DIR = (-LIGHT[0] / LIGHT[2], -LIGHT[1] / LIGHT[2])


def local_rng(name):
    """모듈 전용 결정적 난수(이름이 씨앗). 새 디테일에는 공유 rnd() 대신 이것을 쓴다."""
    return random.Random(zlib.crc32(name.encode("utf-8")))


def h01(*vals):
    """값들로 정하는 0~1 결정적 해시(위치 기반 흔들림용)"""
    s = ",".join(("%.2f" % v) if isinstance(v, float) else str(v) for v in vals)
    return (zlib.crc32(s.encode("utf-8")) & 0xFFFF) / 65535.0


def lit(col, n, jitter=0.0, key=None):
    """법선 n(평면 좌표)에 대한 램버트 음영 색. 윗면(+Z)이 col 그대로(1.0)."""
    f = (AMB + DIF * max(0.0, _dot3(n, LIGHT))) / _TOPF
    if jitter and key is not None:
        f *= 1.0 + jitter * (2.0 * h01(*key) - 1.0)
    out = tuple(max(0, min(255, int(round(c * f)))) for c in col[:3])
    return out + ((col[3],) if len(col) == 4 else ())


def tint(col, f):
    """밝기 배율(알파 유지)"""
    out = tuple(max(0, min(255, int(round(c * f)))) for c in col[:3])
    return out + ((col[3],) if len(col) == 4 else ())


# ───────────────────────── 메시 ─────────────────────────
class Mesh:
    """다각 면(삼각형·사각형 등) 모음.
    - center를 주면 각 면 법선을 center 바깥쪽(orient='out') 또는 안쪽(orient='in')으로 맞춘 뒤, 보는 방향을 등진 면은 버린다.
    - orient='two'면 양면(항상 그림, 보이는 쪽 법선으로 음영).
    - flat 색을 주면 음영 없이 그 색으로 칠한다(단면·절개면 등)."""

    def __init__(self, center=None):
        self.center = center
        self.faces = []

    def add(self, pts3, col, orient="out", flat=None, edge="auto", jitter=0.035):
        if len(pts3) >= 3:
            self.faces.append((list(pts3), col, orient, flat, edge, jitter))
        return self

    def extend(self, other):
        """다른 메시의 면을 합친다(각 면의 바깥 기준은 원래 메시의 center로 미리 고정)"""
        for pts, col, orient, flat, edge, jit in other.faces:
            if orient in ("out", "in") and other.center is not None:
                n = newell(pts)
                c = _centroid(pts)
                out = _sub3(c, other.center)
                want = 1.0 if orient == "out" else -1.0
                if _dot3(n, out) * want < 0:
                    pts = pts[::-1]
                orient = "fixed"
            self.faces.append((pts, col, orient, flat, edge, jit))
        return self

    def draw(self, iso, lw=0.1, edge_f=0.84, cull=True):
        items = []
        for pts, col, orient, flat, edge, jit in self.faces:
            n = newell(pts)
            c = _centroid(pts)
            if orient in ("out", "in") and self.center is not None:
                out = _sub3(c, self.center)
                want = 1.0 if orient == "out" else -1.0
                if _dot3(n, out) * want < 0:
                    n = (-n[0], -n[1], -n[2])
            vis = _dot3(n, VIEW)
            if orient == "two":
                if vis < 0:
                    n = (-n[0], -n[1], -n[2])
            elif cull and vis <= 1e-6:
                continue
            fill = flat if flat is not None else lit(col, n, jit, (round(c[0], 2), round(c[1], 2), round(c[2], 2)))
            items.append((c[0] + c[1] + c[2], pts, fill, edge))
        items.sort(key=lambda t: t[0])
        for _, pts, fill, edge in items:
            ol = None
            if edge == "auto":
                ol = tint(fill, edge_f)[:3]
            elif edge:
                ol = edge
            iso.poly3(pts, fill=fill, ol=ol, lw=lw)
        return len(items)


def _centroid(pts):
    n = float(len(pts))
    return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n, sum(p[2] for p in pts) / n)


# ───────────────────────── 기본 입체 ─────────────────────────
def ring(X, Y, R, n, phase=0.0, ry=None, jit=0.0, key="고리"):
    """평면 원 위 n각 꼭짓점. jit = 반지름 흔들림 비율(위치 해시)."""
    out = []
    for i in range(n):
        a = phase + 2.0 * math.pi * i / n
        k = 1.0 + (jit * (2.0 * h01(key, i) - 1.0) if jit else 0.0)
        out.append((X + R * k * math.cos(a), Y + (ry if ry is not None else R) * k * math.sin(a)))
    return out


def m_prism(base, z0, z1, col, top=None, bottom=False):
    """다각 기둥(볼록 다각형 권장): base = 평면 (X,Y) 꼭짓점 목록"""
    cx = sum(p[0] for p in base) / len(base)
    cy = sum(p[1] for p in base) / len(base)
    m = Mesh((cx, cy, (z0 + z1) / 2.0))
    m.add([(x, y, z1) for x, y in base], top or col)
    if bottom:
        m.add([(x, y, z0) for x, y in base], col)
    nb = len(base)
    for i in range(nb):
        a, b = base[i], base[(i + 1) % nb]
        m.add([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], col)
    return m


def m_box(X0, Y0, Z0, X1, Y1, Z1, col, top=None):
    return m_prism([(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)], Z0, Z1, col, top)


def m_frustum(base, z0, z1, k, col, top=None, apex=None):
    """뿔대: 윗면이 중심 기준 k배(k=0이면 뿔). apex=(X,Y)면 윗면 중심을 그 자리로 옮긴다(기운 봉우리 등)."""
    cx = sum(p[0] for p in base) / len(base)
    cy = sum(p[1] for p in base) / len(base)
    ax, ay = apex if apex else (cx, cy)
    up = [(ax + (x - cx) * k, ay + (y - cy) * k) for x, y in base]
    m = Mesh((cx, cy, z0 + (z1 - z0) * 0.35))
    nb = len(base)
    for i in range(nb):
        a, b = base[i], base[(i + 1) % nb]
        if k <= 1e-6:
            m.add([(a[0], a[1], z0), (b[0], b[1], z0), (ax, ay, z1)], col)
        else:
            ua, ub = up[i], up[(i + 1) % nb]
            m.add([(a[0], a[1], z0), (b[0], b[1], z0), (ub[0], ub[1], z1), (ua[0], ua[1], z1)], col)
    if k > 1e-6:
        m.add([(x, y, z1) for x, y in up], top or col)
    return m


def m_cyl(X, Y, R, z0, z1, col, n=12, top=None, k=1.0, phase=0.0):
    """다면 원기둥(k≠1이면 원뿔대). 기둥·드럼·등대 층·탑에 쓴다."""
    base = ring(X, Y, R, n, phase)
    return m_prism(base, z0, z1, col, top) if abs(k - 1.0) < 1e-9 else m_frustum(base, z0, z1, k, col, top)


def m_cone(X, Y, R, z0, h, col, n=10, apex=None, jit=0.0, key="뿔"):
    return m_frustum(ring(X, Y, R, n, jit=jit, key=key), z0, z0 + h, 0.0, col, apex=apex)


def m_gable(X0, Y0, X1, Y1, z0, zr, roof, wall=None, axis="X", over=0.4):
    """박공지붕: 경사면 2 + 삼각 박공 2. axis = 용마루 방향(X/Y), zr = 용마루 높이, over = 처마 돌출."""
    m = Mesh(((X0 + X1) / 2.0, (Y0 + Y1) / 2.0, (z0 + zr) / 2.0))
    o = over
    w = wall or roof
    if axis == "X":
        ym = (Y0 + Y1) / 2.0
        m.add([(X0 - o, Y0 - o, z0), (X1 + o, Y0 - o, z0), (X1 + o, ym, zr), (X0 - o, ym, zr)], roof)
        m.add([(X0 - o, Y1 + o, z0), (X1 + o, Y1 + o, z0), (X1 + o, ym, zr), (X0 - o, ym, zr)], roof)
        m.add([(X0, Y0, z0), (X0, Y1, z0), (X0, ym, zr)], w)
        m.add([(X1, Y0, z0), (X1, Y1, z0), (X1, ym, zr)], w)
    else:
        xm = (X0 + X1) / 2.0
        m.add([(X0 - o, Y0 - o, z0), (X0 - o, Y1 + o, z0), (xm, Y1 + o, zr), (xm, Y0 - o, zr)], roof)
        m.add([(X1 + o, Y0 - o, z0), (X1 + o, Y1 + o, z0), (xm, Y1 + o, zr), (xm, Y0 - o, zr)], roof)
        m.add([(X0, Y0, z0), (X1, Y0, z0), (xm, Y0, zr)], w)
        m.add([(X0, Y1, z0), (X1, Y1, z0), (xm, Y1, zr)], w)
    return m


def m_house(X0, Y0, X1, Y1, z0, hw, hr, wall, roof, axis="X"):
    """벽 상자 + 박공지붕(창고·농가·항구 창고 열의 한 칸)"""
    m = m_box(X0, Y0, z0, X1, Y1, z0 + hw, wall)
    g = m_gable(X0, Y0, X1, Y1, z0 + hw, z0 + hw + hr, roof, wall, axis)
    out = Mesh(None)
    out.extend(m)
    out.extend(g)
    return out


def m_dome(X, Y, Z, R, col, n=16, rings=5, oculus=0.0, arc=None, inner=None, thick=0.0, section=None):
    """다면 반구 돔(삼각 면).
    - oculus: 꼭대기 구멍 반지름 비율(0이면 막힘).
    - arc=(a0, a1): 그 방위(라디안, 평면 X축 기준 반시계) 범위만 바깥 껍데기를 남긴다(절개 돔).
    - inner: 안쪽 면 색(절개로 안이 보일 때). thick: 껍데기 두께(평면 길이), section: 절개 단면 띠 색."""
    phi_top = math.acos(min(0.999, oculus)) if oculus > 0 else math.pi / 2.0
    a0, a1 = arc if arc else (0.0, 2.0 * math.pi)
    nseg = max(3, int(round(n * (a1 - a0) / (2.0 * math.pi))))

    def sph(r, th, ph):
        return (X + r * math.cos(ph) * math.cos(th), Y + r * math.cos(ph) * math.sin(th), Z + r * math.sin(ph))

    out = Mesh(None)
    shells = [(R, "out", col)]
    if inner is not None:
        shells.append((R - thick if thick > 0 else R * 0.985, "in", inner))
    for (r, orient, cc) in shells:
        m = Mesh((X, Y, Z))
        for j in range(rings):
            p0 = phi_top * j / rings
            p1 = phi_top * (j + 1) / rings
            for i in range(nseg):
                t0 = a0 + (a1 - a0) * i / nseg
                t1 = a0 + (a1 - a0) * (i + 1) / nseg
                q00, q01, q10, q11 = sph(r, t0, p0), sph(r, t1, p0), sph(r, t0, p1), sph(r, t1, p1)
                if j == rings - 1 and oculus <= 0:
                    m.add([q00, q01, (X, Y, Z + r)], cc, orient)
                else:
                    m.add([q00, q01, q11], cc, orient)
                    m.add([q00, q11, q10], cc, orient)
        out.extend(m)
    if arc and section is not None and thick > 0:
        # 절개 단면(껍데기 두께 띠): 양쪽 끝 방위에서 반원 띠
        for th in (a0, a1):
            for j in range(rings):
                p0 = phi_top * j / rings
                p1 = phi_top * (j + 1) / rings
                out.add([sph(R, th, p0), sph(R, th, p1), sph(R - thick, th, p1), sph(R - thick, th, p0)], section, "two", flat=section)
    return out


def m_mound(X, Y, z0, R, h, col, n=8, rings=2, key="무더기", jit=0.18, apex_jit=0.25):
    """로우폴리 무더기(재료 더미·바위·언덕): 흔들린 고리 rings개 + 꼭대기. 삼각 면으로 나눈다."""
    rr = []
    for j in range(rings):
        t = j / float(rings)
        rj = R * (1.0 - t * 0.85)
        zj = z0 + h * (t ** 0.8) * 0.9
        rr.append([(x, y, zj + (h * 0.06 * (2 * h01(key, j, i) - 1) if j else 0.0))
                   for i, (x, y) in enumerate(ring(X, Y, rj, n, phase=0.3 * j, jit=jit, key="%s%d" % (key, j)))])
    ax = X + R * apex_jit * (2 * h01(key, "ax") - 1)
    ay = Y + R * apex_jit * (2 * h01(key, "ay") - 1)
    apex = (ax, ay, z0 + h)
    m = Mesh((X, Y, z0 + h * 0.3))
    for j in range(rings - 1):
        A, B = rr[j], rr[j + 1]
        for i in range(n):
            m.add([A[i], A[(i + 1) % n], B[(i + 1) % n]], col)
            m.add([A[i], B[(i + 1) % n], B[i]], col)
    T = rr[-1]
    for i in range(n):
        m.add([T[i], T[(i + 1) % n], apex], col)
    return m


def m_blob(X, Y, Z, R, col, n=7, key="덩이", jit=0.16, squash=0.85):
    """로우폴리 구(나무 수관·돌덩이): 위·아래 꼭짓점 + 흔들린 고리 2개"""
    up = (X, Y, Z + R * squash)
    dn = (X, Y, Z - R * squash * 0.8)
    r1 = [(x, y, Z + R * 0.35 * squash) for x, y in ring(X, Y, R * 0.92, n, 0.0, jit=jit, key=key + "a")]
    r2 = [(x, y, Z - R * 0.30 * squash) for x, y in ring(X, Y, R, n, math.pi / n, jit=jit, key=key + "b")]
    m = Mesh((X, Y, Z))
    for i in range(n):
        j = (i + 1) % n
        m.add([r1[i], r1[j], up], col)
        m.add([r1[i], r2[i], r1[j]], col)
        m.add([r1[j], r2[i], r2[j]], col)
        m.add([r2[i], dn, r2[j]], col)
    return m


def m_terrain(X0, Y0, X1, Y1, nx, ny, hfun, colfun, skirt=None):
    """높이장 지형: 격자 셀마다 삼각형 2개(대각 방향 교대).
    hfun(X,Y)→Z, colfun(X,Y,Z)→색. skirt=(z바닥, 색)이면 보이는 두 변(+X·+Y)에 흙 옆면을 단다."""
    P = [[(X0 + (X1 - X0) * i / nx, Y0 + (Y1 - Y0) * j / ny) for j in range(ny + 1)] for i in range(nx + 1)]
    Z = [[hfun(*P[i][j]) for j in range(ny + 1)] for i in range(nx + 1)]
    m = Mesh(None)
    for i in range(nx):
        for j in range(ny):
            a = (P[i][j][0], P[i][j][1], Z[i][j])
            b = (P[i + 1][j][0], P[i + 1][j][1], Z[i + 1][j])
            c = (P[i + 1][j + 1][0], P[i + 1][j + 1][1], Z[i + 1][j + 1])
            d = (P[i][j + 1][0], P[i][j + 1][1], Z[i][j + 1])
            tris = ((a, b, c), (a, c, d)) if (i + j) % 2 == 0 else ((a, b, d), (b, c, d))
            for t in tris:
                cc = _centroid(t)
                col = colfun(*cc)
                n = newell(list(t))
                if n[2] < 0:
                    t = t[::-1]
                m.add(list(t), col, "two")
    if skirt is not None:
        zb, sc = skirt
        for i in range(nx):       # +Y 변(왼면)
            p, q = (P[i][ny], Z[i][ny]), (P[i + 1][ny], Z[i + 1][ny])
            m.add([(p[0][0], p[0][1], zb), (q[0][0], q[0][1], zb), (q[0][0], q[0][1], q[1]), (p[0][0], p[0][1], p[1])], sc, "two")
        for j in range(ny):       # +X 변(오른면)
            p, q = (P[nx][j], Z[nx][j]), (P[nx][j + 1], Z[nx][j + 1])
            m.add([(p[0][0], p[0][1], zb), (q[0][0], q[0][1], zb), (q[0][0], q[0][1], q[1]), (p[0][0], p[0][1], p[1])], sc, "two")
    return m


# ───────────────────────── 나무·사람(로우폴리) ─────────────────────────
def m_cypress(X, Y, z0, h, r, col=(66, 100, 58), trunk=(96, 70, 44), n=7, key="사이프러스"):
    m = Mesh(None)
    m.extend(m_cyl(X, Y, r * 0.16, z0, z0 + h * 0.16, trunk, n=5))
    m.extend(m_frustum(ring(X, Y, r, n, jit=0.08, key=key), z0 + h * 0.12, z0 + h * 0.5, 0.82, col))
    m.extend(m_frustum(ring(X, Y, r * 0.82, n, 0.4, jit=0.08, key=key + "2"), z0 + h * 0.5, z0 + h, 0.0, col))
    return m


def m_olive(X, Y, z0, h, r, col=(112, 134, 78), trunk=(110, 86, 60), key="올리브"):
    m = Mesh(None)
    m.extend(m_cyl(X, Y, r * 0.14, z0, z0 + h * 0.45, trunk, n=5, k=0.8))
    m.extend(m_blob(X, Y, z0 + h * 0.66, r, col, n=7, key=key))
    m.extend(m_blob(X + r * 0.45, Y - r * 0.2, z0 + h * 0.58, r * 0.6, tint(col, 0.94), n=6, key=key + "b"))
    return m


def m_person(X, Y, z0, h, cloth=(150, 70, 52), skin=(226, 184, 150), key="사람"):
    """로우폴리 사람(키 h): 다리 상자 2 + 몸통 뿔대 + 머리 다면체. 키 4~6mm에서 읽힌다."""
    w = h * 0.13
    m = Mesh(None)
    m.extend(m_box(X - w, Y - w * 0.6, z0, X - w * 0.15, Y + w * 0.6, z0 + h * 0.42, tint(cloth, 0.7)))
    m.extend(m_box(X + w * 0.15, Y - w * 0.6, z0, X + w, Y + w * 0.6, z0 + h * 0.42, tint(cloth, 0.7)))
    m.extend(m_frustum(ring(X, Y, w * 1.35, 6, 0.3), z0 + h * 0.40, z0 + h * 0.80, 0.72, cloth))
    m.extend(m_blob(X, Y, z0 + h * 0.89, h * 0.11, skin, n=6, key=key, jit=0.05))
    return m


# ───────────────────────── 지층 받침(레이어를 쌓은 흙 단면) ─────────────────────────
STRATA = [(1.2, (94, 126, 66)), (1.6, (128, 98, 62)), (1.4, (150, 118, 80)), (1.8, (112, 86, 56))]


def strata_slab(L, cx, cy, w, layers=None, top=(210, 196, 166), edge=EDGE, wave=0.35, pebbles=True, key="받침"):
    """등각 마름모 받침의 두 옆면에 지층 여러 겹을 쌓는다(경계선은 위치 해시로 살짝 물결).
    layers = [(두께mm, 색), ...] 위에서 아래로. 반환: 마름모 꼭짓점(L,T,R,B)과 총 두께."""
    layers = layers or STRATA
    h = w / SQ3
    Lv, Tv, Rv, Bv = (cx - w / 2, cy), (cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2)
    tot = sum(t for t, _ in layers)
    nseg = 10

    def edge_pts(p, q, d, k):
        pts = []
        for i in range(nseg + 1):
            t = i / float(nseg)
            off = 0.0 if i in (0, nseg) or k == 0 else wave * (2 * h01(key, k, i, p[0]) - 1)
            pts.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t + d + off))
        return pts

    for face, (p, q), f in (("L", (Lv, Bv), 0.83), ("R", (Bv, Rv), 0.63)):
        d0 = 0.0
        for k, (t, col) in enumerate(layers):
            upper = edge_pts(p, q, d0, k)
            lower = edge_pts(p, q, d0 + t, k + 1 if k + 1 < len(layers) else 0)
            L.poly(upper + lower[::-1], fill=tint(col, f / 0.83 if face == "L" else f / 0.83))
            d0 += t
        L.line([p, (p[0], p[1] + tot)], tint(layers[-1][1], 0.6), 0.2, joint=False)
        if pebbles:
            for i in range(9):
                u = 0.08 + 0.84 * h01(key, face, "u", i)
                v = 0.25 + 0.7 * h01(key, face, "v", i)
                x = p[0] + (q[0] - p[0]) * u
                y = p[1] + (q[1] - p[1]) * u + tot * v
                r = 0.25 + 0.35 * h01(key, face, "r", i)
                L.poly([(x - r, y), (x - r * 0.3, y - r * 0.8), (x + r, y - r * 0.2), (x + r * 0.4, y + r * 0.7)],
                       fill=tint((176, 164, 140), 0.95 if face == "L" else 0.78))
    L.line([Lv, (Lv[0], Lv[1] + tot), (Bv[0], Bv[1] + tot), (Rv[0], Rv[1] + tot), Rv], (70, 50, 32), 0.2)
    L.line([Bv, (Bv[0], Bv[1] + tot)], (70, 50, 32), 0.18, joint=False)
    L.poly([Lv, Tv, Rv, Bv], fill=top, outline=edge, lw=0.35)
    return {"L": Lv, "T": Tv, "R": Rv, "B": Bv, "depth": tot}


# ───────────────────────── 로우폴리 면 채우기(물·밭·광장) ─────────────────────────
def facet_fill(L, poly, col, cell=5.0, amp=0.06, key="면", jit=0.16, edge_f=None, lw=0.06):
    """화면 다각형 poly(mm) 안을 ±30° 삼각 격자(로우폴리 면)로 채운다. 면마다 밝기 흔들림 amp, 꼭짓점 흔들림 jit(셀 비율)."""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    W = int(math.ceil((x1 - x0) * KD)) + 2
    H = int(math.ceil((y1 - y0) * KD)) + 2
    if W <= 2 or H <= 2:
        return
    tile = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    c = float(cell)
    # 화면 (x,y) = (C30*(u−v)c, 0.5*(u+v)c) 격자
    corners = [(0, 0), (x1 - x0, 0), (0, y1 - y0), (x1 - x0, y1 - y0)]
    us = [(x / (C30 * c) + 2 * y / c) / 2 for x, y in corners]
    vs = [(2 * y / c - x / (C30 * c)) / 2 for x, y in corners]
    u0, u1 = int(math.floor(min(us))) - 1, int(math.ceil(max(us))) + 1
    v0, v1 = int(math.floor(min(vs))) - 1, int(math.ceil(max(vs))) + 1

    def P(i, j):
        jx = jit * c * (2 * h01(key, "x", i, j) - 1)
        jy = jit * c * 0.6 * (2 * h01(key, "y", i, j) - 1)
        return ((C30 * (i - j) * c + jx) * KD, (0.5 * (i + j) * c + jy) * KD)

    for i in range(u0, u1):
        for j in range(v0, v1):
            a, b, cc, e = P(i, j), P(i + 1, j), P(i + 1, j + 1), P(i, j + 1)
            for k, tri in enumerate(((a, b, cc), (a, cc, e))):
                f = 1.0 + amp * (2 * h01(key, i, j, k) - 1)
                fill = tint(col, f)
                if len(fill) == 3:
                    fill = fill + (255,)
                if edge_f:
                    d.polygon(tri, fill=fill, outline=tint(fill, edge_f)[:3] + (fill[3],))
                else:
                    d.polygon(tri, fill=fill)
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon([((x - x0) * KD, (y - y0) * KD) for x, y in poly], fill=255)
    tile.putalpha(ImageChops.multiply(tile.getchannel("A"), mask))
    safe_composite(L.img, tile, L.X(x0), L.Y(y0))


# ───────────────────────── 레이어 효과 ─────────────────────────
def sublayer(L, name="부분"):
    """같은 영역의 투명 하위 레이어(그린 뒤 merge로 합친다)"""
    return Layer(L.x0, L.y0, L.x1, L.y1, (L.name or "") + "/" + name)


def merge(L, S, opacity=1.0, blur=0.0):
    """하위 레이어 S를 L에 합성. blur = 가우스 흐림 반지름(mm), opacity = 0~1"""
    img = S.img
    if blur > 0:
        img = img.filter(ImageFilter.GaussianBlur(blur * KD))
    if opacity < 1.0:
        img = img.copy()
        img.putalpha(img.getchannel("A").point(lambda v: int(v * opacity)))
    safe_composite(L.img, img, (S.x0 - L.x0) * KD, (S.y0 - L.y0) * KD)


def cast_shadow(L, iso, footprint, h, col=(70, 52, 32), alpha=95, blur=0.9):
    """바닥 그림자: 평면 발자국(볼록 다각형 권장) footprint와 높이 h로 빛 반대쪽에 떨어지는 그림자를 흐리게 깐다.
    objects()의 "shadow" 함수 안에서 쓰면 크기 자동 실측에 들어가지 않는다."""
    dx, dy = SHADOW_DIR
    pts = [iso.p(x, y, 0.0) for x, y in footprint] + [iso.p(x + dx * h, y + dy * h, 0.0) for x, y in footprint]
    hull = _hull(pts)
    S = sublayer(L, "그림자")
    S.poly(hull, fill=col + (alpha,))
    merge(L, S, blur=blur)


def contact_ao(L, pts, w=0.9, col=(40, 28, 16), alpha=70, blur=0.45):
    """접지선 어둠(앰비언트 오클루전): 화면 점 목록을 따라 흐린 어둠 띠"""
    S = sublayer(L, "접지")
    S.line(pts, col + (alpha,), w, joint=True)
    merge(L, S, blur=blur)


def glow(L, poly, col, alpha=90, blur=1.2):
    """빛줄기·증기·물빛: 화면 다각형을 흐리게 밝힌다"""
    S = sublayer(L, "빛")
    S.poly(poly, fill=col + (alpha,))
    merge(L, S, blur=blur)


def rim(L, pts, col=(255, 248, 230), alpha=150, w=0.25):
    """윤곽 하이라이트(빛을 받는 모서리)"""
    L.line(pts, col + (alpha,), w, joint=True)


def _hull(pts):
    pts = sorted(set((round(x, 4), round(y, 4)) for x, y in pts))
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
