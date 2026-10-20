# -*- coding: utf-8 -*-
# roma_pkg_suburb — 남동 교외·가장 먼 곳. 담당: suburb
#   카이킬리아 메텔라 무덤 · 아피아 가도 소품(수레·우산소나무·사이프러스 열) · 교외 빌라 · 포도밭 농장 · 베수비오(79년 이전) · 알바노 구릉 띠
# b5 회차(설계 current = d4 spec + 공통 결정 D1~D17). 앞선 워커 코드(도구·나무·부조·소)를 이어 쓰고 배치·크기·층 구성을 고쳤다.
#   - 오브젝트마다 표현 레이어 L0~L6을 쌓는다(D10). 이름 SUB_{Obj}_L{n}_{part}, 루트 SUB_{Obj}_root
#     L0 덩어리 · L1 깊이색 · L2 부재 · L3 표면 무늬 · L4 형태 디테일 · L5 하이라이트 · L6 얼룩·식생·생활 (L7 외곽선 없음)
#   - 벡터 일러스트(203X, D9): 조명·AO·그림자 0. 면은 ISO_TONE 평면 톤(roma_flat)만 쓴다.
#     대기 원근은 땅색 FL.PAL['ground']와 섞은 평면색 단계로만 낸다(베수비오 50%, 농장 25%, 알바노 26~46%).
#   - 받침 없음. 모든 것이 땅 Z=0에 선다. 길 위 소품은 길 윗면(ground ROAD_Z, R1 0.30)에 선다(D13).
#   - 자리·크기는 spec(current)과 공통 결정(D1). 상자·좌표 하드코딩 금지: 비움 자리는 spec 라벨 블록·바닥 글·
#     히어로 예약 원·수도교·이웃 랜드마크 상자·drawn.json 지시선에서 읽는다.
#   - 사람 키(D8, 화면 mm 발~머리, 폭 ≈ 키 × 0.32): 메텔라·아피아 2.4, 농장·빌라·베수비오·알바노 1.8.
#     나무는 사람 키 배율(사이프러스 2.5~3.0, 올리브 2.2, 우산소나무 3.0), 암포라 0.45, 수레 길이 2.2.
#   - 앵커(D11): ANCHOR_L5_label · ANCHOR_L5_c4 · ANCHOR_V_label(보이는 면 위 3D 점, 렌더하지 않는 Empty)
import bpy, bmesh, math, json, re, colorsys
from mathutils import Vector, Matrix
import roma_kit as R, roma_flat as FL, roma_geo as G

COLL = 'LM_Suburb'
WORK = '/Users/um-yunsang/roman-concrete-private-refs/.work'
SPEC = WORK + '/design/current/out/spec.json'
DRAWN = WORK + '/design/current/out/drawn.json'        # 설계 2D 실측: 라벨 블록·바닥 글·지시선·짝 표지
PKG = 'SUB'
DECOR = False                                          # 16:14 사용자 결정(core 정보 오브젝트만): 메텔라 무덤과 그 대지만 짓는다.
TERRAIN = False                                        # b7(d7): 산맥 띠·베수비오는 roma_terrain_persp.build_band가 짓는다. 옛: 17:32 사용자: 알바노 구릉(화산 구릉 산맥)·베수비오(화산)만 되살린다. 먼 들·빌라·포도밭·나무·사람 0
#   베수비오·알바노 구릉·먼 들·아피아 가도 소품(수레·가로수)·교외 빌라·포도밭 농장, 무덤 둘레 나무·방문객은 짓지 않는다(코드는 보관)
ROAD_TOP = {'R1': 0.30, 'R6a': 0.29, 'R6b': 0.295}     # ground ROAD_Z(길 윗면, D13)
C30 = math.cos(math.radians(30.0))
REPORT = {}
H_NEAR, H_FAR = 2.4, 1.8                               # D8 사람 키: 표준 랜드마크·길 / 가장 먼 곳·교외 빌라
K_CYP, K_OLIVE, K_PINE = (2.5, 3.0), 2.2, 3.0           # D8 나무 키 ÷ 사람 키(히어로 밖)
HERO_C_DEF, HERO_R_DEF = (462.34, 173.66), 90.0        # D3 상수: spec core_map.hero.landscape 열쇠가 없을 때만 쓴다
D9_GROUND = '#ECD8AC'                                  # D9 땅 윗면 렌더 RGB (236, 216, 172)


# ───────────────────────── 작은 도구 ─────────────────────────
def _h(*k):
    return R.hash01(*k)


def _j(*k):
    return 2.0 * R.hash01(*k) - 1.0


def hexmix(a, b, k):
    a, b = a.lstrip('#'), b.lstrip('#')
    ca = [int(a[i:i + 2], 16) for i in (0, 2, 4)]
    cb = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return '#%02X%02X%02X' % tuple(int(round(x + (y - x) * k)) for x, y in zip(ca, cb))


def hi_of(hexcol, k=1.13, sat=0.9):
    """L5 하이라이트 색: 같은 색상에서 명도 +k(D9 +10~15%), 채도 조금 낮춤"""
    h_ = hexcol.lstrip('#')
    r, g, b = [int(h_[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    hh, s, v = colorsys.rgb_to_hsv(r, g, b)
    r, g, b = colorsys.hsv_to_rgb(hh, s * sat, min(1.0, v * k))
    return '#%02X%02X%02X' % (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def bump(x, c, hw):
    """c에서 1, |x − c| ≥ hw에서 0인 매끈한 혹"""
    u = abs(x - c) / hw
    return 0.0 if u >= 1.0 else math.cos(0.5 * math.pi * u) ** 2


def _sin(node, ident, name):
    for s in node.inputs:
        if s.identifier == ident:
            return s
    return node.inputs[name]


def ground_hex():
    """D9 땅색. FL.PAL['ground']를 읽고, bglobal이 아직 옛 값(#E3CFA8)이면 D9 결정값을 쓴다"""
    g = str(FL.PAL.get('ground', D9_GROUND)).upper()
    return D9_GROUND if g == '#E3CFA8' else g


# ───────────────────────── 재질(평면색 · 대기 원근 단계) ─────────────────────────
_MC = {}


def _atmo(m, k):
    """ISO_TONE 결과를 땅색과 k만큼 섞는다. 색과 면 톤 대비가 함께 줄어드는 평면색 단계(빛 계산 없음)"""
    nt = m.node_tree
    em = next(n for n in nt.nodes if n.type == 'EMISSION')
    src = em.inputs['Color'].links[0].from_socket
    mx = nt.nodes.new('ShaderNodeMix')
    mx.data_type = 'RGBA'
    mx.blend_type = 'MIX'
    _sin(mx, 'Factor_Float', 'Factor').default_value = k
    nt.links.new(src, _sin(mx, 'A_Color', 'A'))
    _sin(mx, 'B_Color', 'B').default_value = (*FL.srgb(ground_hex()), 1.0)
    out = next(s for s in mx.outputs if s.identifier == 'Result_Color')
    nt.links.new(out, em.inputs['Color'])
    return m


def _mname(key, atmo):
    return 'F_sub_' + key + ('' if atmo <= 0 else '_a%02d' % int(round(atmo * 100)))


def mat(key, hexcol, atmo=0.0):
    name = _mname(key, atmo)
    m = _MC.get(name)
    if m is None:
        m = FL.flat(name, hexcol)
        if atmo > 0:
            _atmo(m, atmo)
            m.diffuse_color = (*FL.srgb(hexmix(hexcol, ground_hex(), atmo)), 1.0)
        _MC[name] = m
    return m


def blk(key, c1, c2, c3, joint, bw, rh, jw, atmo=0.0):
    name = _mname(key, atmo)
    m = _MC.get(name)
    if m is None:
        m = FL.blocks(name, c1, c2, c3, joint, bw, rh, jw)
        if atmo > 0:
            _atmo(m, atmo)
        _MC[name] = m
    return m


# ───────────────────────── 표현 레이어 모음 ─────────────────────────
class Lay:
    """한 오브젝트의 레이어 메시들: (층 n, 부분) → bmesh + 재질 목록 → SUB_{Obj}_L{n}_{part}"""
    def __init__(self, obj, root, coll):
        self.obj, self.root, self.coll = obj, root, coll
        self.parts = {}

    def __call__(self, n, part, mats):
        k = (n, part)
        if k not in self.parts:
            self.parts[k] = (bmesh.new(), list(mats))
        return self.parts[k][0]

    def finish(self):
        obs = []
        for k in sorted(self.parts):
            bm, mats = self.parts[k]
            if len(bm.faces) == 0:
                bm.free()
                continue
            ob = R.bm_to_obj(bm, '%s_%s_L%d_%s' % (PKG, self.obj, k[0], k[1]), mats, self.coll, self.root)
            obs.append(ob)
        self.parts = {}
        bpy.context.view_layer.update()
        return obs


class XB:
    """bmesh에 행렬을 씌운다: roma_geo 도형을 돌리고 옮겨 쌓을 때(verts.new만 변환)"""
    def __init__(self, bm, M):
        self._bm, self.M = bm, M
        self.verts = self
        self.faces, self.loops, self.edges = bm.faces, bm.loops, bm.edges

    def new(self, co):
        return self._bm.verts.new(self.M @ Vector(co))


# ───────────────────────── 도형 ─────────────────────────
def lathe(bm, cx, cy, prof, n=12, mi=0, phase=0.0, rj=None, zj=None, sx=1.0, sy=1.0, rot=0.0, mi_fn=None):
    """회전체(옆면 + 위·아래 마개, 닫힌 입체). prof=[(r, z)] 아래→위, r=0이면 꼭짓점.
    rj(k, j): 반지름 배율, zj(k, j): 높이 더하기, mi_fn(k, j): 띠 j의 재질 번호"""
    cr, sr = math.cos(rot), math.sin(rot)
    rows = []
    for j, (r, z) in enumerate(prof):
        if r <= 1e-6:
            rows.append([bm.verts.new((cx, cy, z + (zj(0, j) if zj else 0.0)))])
            continue
        row = []
        for k in range(n):
            a = 2 * math.pi * k / n + phase
            rr = r * (rj(k, j) if rj else 1.0)
            x, y = rr * math.cos(a) * sx, rr * math.sin(a) * sy
            row.append(bm.verts.new((cx + cr * x - sr * y, cy + sr * x + cr * y, z + (zj(k, j) if zj else 0.0))))
        rows.append(row)
    fs = []
    for j in range(len(rows) - 1):
        A, B = rows[j], rows[j + 1]
        if len(A) == 1 and len(B) == 1:
            continue
        for k in range(n):
            k2 = (k + 1) % n
            if len(A) == 1:
                f = bm.faces.new([A[0], B[k2], B[k]])
            elif len(B) == 1:
                f = bm.faces.new([A[k], A[k2], B[0]])
            else:
                f = bm.faces.new([A[k], A[k2], B[k2], B[k]])
            f.material_index = mi_fn(k, j) if mi_fn else mi
            fs.append(f)
    if len(rows[-1]) > 1:
        f = bm.faces.new(rows[-1])
        f.material_index = mi_fn(0, len(rows) - 2) if mi_fn else mi
        fs.append(f)
    if len(rows[0]) > 1:
        f = bm.faces.new(rows[0][::-1])
        f.material_index = mi_fn(0, 0) if mi_fn else mi
        fs.append(f)
    return fs, rows


def blob(bm, c, rx, ry, rz, n=8, m=4, jit=0.12, seed=0.0, mi=0, zmin=None):
    """울퉁불퉁한 잎·흙 덩어리(닫힌 입체). zmin을 주면 밑을 평평하게 자른다(땅에 붙는다)"""
    cx, cy, cz = c

    def zc(z):
        return z if zmin is None else max(z, zmin)
    rows = []
    for j in range(1, m):
        ph = -math.pi / 2 + math.pi * j / m
        row = []
        for k in range(n):
            a = 2 * math.pi * k / n + seed * 0.37
            q = 1.0 + jit * _j(seed, j, k)
            row.append(bm.verts.new((cx + rx * q * math.cos(ph) * math.cos(a), cy + ry * q * math.cos(ph) * math.sin(a),
                                     zc(cz + rz * q * math.sin(ph)))))
        rows.append(row)
    b = bm.verts.new((cx, cy, zc(cz - rz)))
    t = bm.verts.new((cx, cy, cz + rz * (1.0 + 0.5 * jit * _j(seed, 99))))
    fs = []
    for k in range(n):
        k2 = (k + 1) % n
        fs.append(bm.faces.new([b, rows[0][k2], rows[0][k]]))
        fs.append(bm.faces.new([t, rows[-1][k], rows[-1][k2]]))
    for j in range(len(rows) - 1):
        for k in range(n):
            k2 = (k + 1) % n
            fs.append(bm.faces.new([rows[j][k], rows[j][k2], rows[j + 1][k2], rows[j + 1][k]]))
    for f in fs:
        f.material_index = mi
    return fs


def tube(bm, p0, p1, r0, r1, n=6, mi=0):
    """두 점 사이 원뿔대(닫힌 입체, 어떤 방향이든)"""
    p0, p1 = Vector(p0), Vector(p1)
    ax = p1 - p0
    if ax.length < 1e-9:
        return []
    ax.normalize()
    t = Vector((1, 0, 0)) if abs(ax.x) < 0.9 else Vector((0, 1, 0))
    u = ax.cross(t).normalized()
    v = ax.cross(u).normalized()
    cs = [(math.cos(2 * math.pi * k / n), math.sin(2 * math.pi * k / n)) for k in range(n)]
    lo = [bm.verts.new(p0 + (u * c + v * s) * r0) for c, s in cs]
    hi = [bm.verts.new(p1 + (u * c + v * s) * r1) for c, s in cs]
    fs = [bm.faces.new([lo[k], lo[(k + 1) % n], hi[(k + 1) % n], hi[k]]) for k in range(n)]
    fs.append(bm.faces.new(hi))
    fs.append(bm.faces.new(lo[::-1]))
    for f in fs:
        f.material_index = mi
    return fs


def ribbon(bm, pts, w, th=0.15, mi=0, w1=None):
    """3D 꺾은선을 따라 수평 폭 w(끝 w1)·두께 th인 납작한 띠(닫힌 입체). 길·담·포도 줄·물길"""
    n = len(pts)
    if n < 2:
        return []
    P = [Vector(p) for p in pts]
    top, bot = [], []
    for i in range(n):
        a, b = P[max(i - 1, 0)], P[min(i + 1, n - 1)]
        d = Vector((b.x - a.x, b.y - a.y, 0.0))
        if d.length < 1e-9:
            d = Vector((1.0, 0.0, 0.0))
        d.normalize()
        nr = Vector((-d.y, d.x, 0.0))
        ww = (w if w1 is None else w + (w1 - w) * i / (n - 1)) / 2.0
        Lp, Rp = P[i] + nr * ww, P[i] - nr * ww
        top.append((bm.verts.new(Lp), bm.verts.new(Rp)))
        bot.append((bm.verts.new(Lp - Vector((0, 0, th))), bm.verts.new(Rp - Vector((0, 0, th)))))
    fs = []
    for i in range(n - 1):
        (tl0, tr0), (tl1, tr1) = top[i], top[i + 1]
        (bl0, br0), (bl1, br1) = bot[i], bot[i + 1]
        fs.append(bm.faces.new([tl0, tr0, tr1, tl1]))
        fs.append(bm.faces.new([bl1, br1, br0, bl0]))
        fs.append(bm.faces.new([tl0, tl1, bl1, bl0]))
        fs.append(bm.faces.new([tr1, tr0, br0, br1]))
    fs.append(bm.faces.new([top[0][1], top[0][0], bot[0][0], bot[0][1]]))
    fs.append(bm.faces.new([top[-1][0], top[-1][1], bot[-1][1], bot[-1][0]]))
    for f in fs:
        f.material_index = mi
    return fs


def pbox(bm, X0, X1, Y0, Y1, z0, z1, mi=0):
    """설계 평면 지역 좌표(X ↘, Y ↙) 상자 → Blender 지역(x = X, y = −Y)"""
    return G.box(bm, X0, X1, -Y1, -Y0, z0, z1, mi)


def pgable(bm, X0, X1, Y0, Y1, z0, z1, axis='X', mi=0, over=0.0):
    return G.gable(bm, X0, X1, -Y1, -Y0, z0, z1, axis, mi, over)


def fan(bm, pts, mi=0):
    """별 모양 다각형(3D 점 목록)을 가운데 점 부채꼴 삼각형으로(오목해도 깨지지 않게)"""
    n = len(pts)
    c = Vector((sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n, sum(p[2] for p in pts) / n))
    vc = bm.verts.new(c)
    vs = [bm.verts.new(p) for p in pts]
    fs = []
    for i in range(n):
        f = bm.faces.new([vc, vs[i], vs[(i + 1) % n]])
        f.material_index = mi
        fs.append(f)
    return fs


def ray_z(obs, x, y, ztop=300.0):
    """지역 좌표(루트 기준) 수직 광선: 겉면 높이(없으면 None). obs는 같은 루트의 레이어 메시"""
    best = None
    for ob in obs:
        ok, loc, nor, idx = ob.ray_cast(Vector((x, y, ztop)), Vector((0.0, 0.0, -1.0)))
        if ok and (best is None or loc.z > best):
            best = loc.z
    return best


def slab(bm, pts, z0, z1, mi_top, mi_side=None, side_fn=None):
    """평면 다각형(Blender xy)을 z0~z1로 세운 닫힌 입체. side_fn(i) → 옆면 i(점 i→i+1)의 재질"""
    n = len(pts)
    lo = [bm.verts.new((x, y, z0)) for x, y in pts]
    hi = [bm.verts.new((x, y, z1)) for x, y in pts]
    ms = mi_top if mi_side is None else mi_side
    fs = []
    for i in range(n):
        f = bm.faces.new([lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]])
        f.material_index = side_fn(i) if side_fn else ms
        fs.append(f)
    f = bm.faces.new(hi); f.material_index = mi_top; fs.append(f)
    f = bm.faces.new(lo[::-1]); f.material_index = ms; fs.append(f)
    return fs


def arc_slab(bm, inner, outer, z0, z1, mi_top, mi_side, mi_in=None):
    """같은 점 수의 안쪽·바깥 꺾은선(열린 호, Blender xy) 사이 띠 입체(닫힘). z0·z1은 수 하나 또는 점마다 목록"""
    n = len(inner)
    Z0 = z0 if isinstance(z0, (list, tuple)) else [z0] * n
    Z1 = z1 if isinstance(z1, (list, tuple)) else [z1] * n
    il = [bm.verts.new((inner[i][0], inner[i][1], Z0[i])) for i in range(n)]
    ih = [bm.verts.new((inner[i][0], inner[i][1], Z1[i])) for i in range(n)]
    ol = [bm.verts.new((outer[i][0], outer[i][1], Z0[i])) for i in range(n)]
    oh = [bm.verts.new((outer[i][0], outer[i][1], Z1[i])) for i in range(n)]
    mi_in = mi_side if mi_in is None else mi_in
    for i in range(n - 1):
        j = i + 1
        for vs, mi in (([ih[i], oh[i], oh[j], ih[j]], mi_top), ([ol[i], ol[j], oh[j], oh[i]], mi_side),
                       ([il[j], il[i], ih[i], ih[j]], mi_in), ([il[i], il[j], ol[j], ol[i]], mi_side)):
            f = bm.faces.new(vs)
            f.material_index = mi
    for k in (0, n - 1):
        f = bm.faces.new([il[k], ol[k], oh[k], ih[k]])
        f.material_index = mi_side


# ───────────────────────── 화면 다각형 검사 ─────────────────────────
def _seg_d(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _pip(x, y, poly):
    c = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def _sx(a, b, c, d):
    def cr(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    return (cr(a, b, c) > 0) != (cr(a, b, d) > 0) and (cr(c, d, a) > 0) != (cr(c, d, b) > 0)


def poly_dist(A, B):
    """두 화면 다각형 사이 최소 거리(겹치면 0)"""
    if any(_pip(x, y, B) for x, y in A) or any(_pip(x, y, A) for x, y in B):
        return 0.0
    for i in range(len(A)):
        for k in range(len(B)):
            if _sx(A[i], A[(i + 1) % len(A)], B[k], B[(k + 1) % len(B)]):
                return 0.0
    d = 1e9
    for P_, Q_ in ((A, B), (B, A)):
        for i in range(len(P_)):
            a1, a2 = P_[i], P_[(i + 1) % len(P_)]
            for q in Q_:
                d = min(d, _seg_d(q[0], q[1], a1[0], a1[1], a2[0], a2[1]))
    return d


def line_dist(A, L):
    """닫힌 다각형 A와 꺾은선 L(닫지 않음, 지시선) 사이 최소 거리"""
    if any(_pip(x, y, A) for x, y in L):
        return 0.0
    n = len(A)
    for i in range(len(L) - 1):
        for k in range(n):
            if _sx(L[i], L[i + 1], A[k], A[(k + 1) % n]):
                return 0.0
    d = 1e9
    for i in range(len(L) - 1):
        for q in A:
            d = min(d, _seg_d(q[0], q[1], L[i][0], L[i][1], L[i + 1][0], L[i + 1][1]))
    for p in L:
        for k in range(n):
            d = min(d, _seg_d(p[0], p[1], A[k][0], A[k][1], A[(k + 1) % n][0], A[(k + 1) % n][1]))
    return d


def pt_poly_d(p, A):
    if _pip(p[0], p[1], A):
        return 0.0
    n = len(A)
    return min(_seg_d(p[0], p[1], A[k][0], A[k][1], A[(k + 1) % n][0], A[(k + 1) % n][1]) for k in range(n))


def rbox(b):
    return [(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])]


MET_BOX_D4 = (354.0, 288.0, 420.0, 358.0)             # d4 L5 상자(대지 모양 계산용)
R6B_D4 = (542.08, 551.32, 81.28, 95.2)                 # d4 R6b 평면 사각형(X0, X1, Y0, Y1): spec에 없을 때 메텔라 대지 뒤 변 기준


def road_rects(CM):
    """spec 길 → 평면 사각형(ground World.roads와 같은 셈: 반폭 = 화면 수직 폭 / cos30 / 2)"""
    out = {}
    for r in CM['roads']:
        if len(r.get('plan_pts', [])) != 2:                    # d5 R_route(꺾은선) 등은 사각형 길이 아니다
            continue
        (X0, Y0), (X1, Y1) = r['plan_pts']
        hw = r['w_screen_perp_mm'] / C30 / 2.0
        if abs(X0 - X1) < 1e-6:
            out[r['id']] = (X0 - hw, X0 + hw, min(Y0, Y1), max(Y0, Y1))
        else:
            out[r['id']] = (min(X0, X1), max(X0, X1), Y0 - hw, Y0 + hw)
    return out


def rect_scr(rc):
    X0, X1, Y0, Y1 = rc
    return [R.to_screen(X, Y) for X, Y in ((X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1))]


def tree_scr(X, Y, Z, r, h):
    """나무 하나의 화면 외곽(축 정렬 사각형): 밑동 원 + 수관 꼭대기"""
    sx, sy = R.to_screen(X, Y, Z)
    return [(sx - 1.2247 * r, sy - h - 0.7071 * r), (sx + 1.2247 * r, sy - h - 0.7071 * r),
            (sx + 1.2247 * r, sy + 0.7071 * r), (sx - 1.2247 * r, sy + 0.7071 * r)]


def kids_bbox(root):
    bpy.context.view_layer.update()
    return G.screen_bbox([o for o in root.children_recursive if o.type == 'MESH' and not o.hide_render])


def info_leaders(D):
    """drawn.json 지시선(지도→패널 지시선 + 라벨 지시선) 꺾은선 목록"""
    out = []
    for L in D.get('leaders', []):
        if len(L.get('pts', [])) >= 2:
            out.append([tuple(p) for p in L['pts']])
    for lb in D.get('labels', []):
        ld = lb.get('leader') or {}
        if len(ld.get('pts', [])) >= 2:
            out.append([tuple(p) for p in ld['pts']])
    return out


# ───────────────────────── 문맥(spec·drawn에서 읽는 자리·비움 영역) ─────────────────────────
def _terrain_list(CM):
    """d7: core_map.terrain = {features, band} → features 목록(옛 spec은 목록 그대로)"""
    t = CM.get('terrain') or []
    return t.get('features', []) if isinstance(t, dict) else t


class Ctx:
    def __init__(self):
        S = json.load(open(SPEC, encoding='utf-8'))
        self.S, self.CM = S, S['core_map']
        try:
            self.D = json.load(open(DRAWN, encoding='utf-8'))
        except Exception:
            self.D = {}
        H = self.CM.get('hero') or {}
        L = H.get('landscape') if isinstance(H.get('landscape'), dict) else {}
        c = L.get('center_plan') or HERO_C_DEF
        r = L.get('reserve_R_plan') or (L.get('reserve') or {}).get('R_plan') or HERO_R_DEF
        self.hero_c, self.hero_r = (float(c[0]), float(c[1])), float(r)
        self.hero_src = 'spec core_map.hero.landscape' if L else '공통 결정 D3 상수'
        self.roads = road_rects(self.CM)
        self.lm = {l['id']: l for l in self.CM['landmarks']}
        self.V = (self.CM.get('background') or [None])[0]          # d5: 베수비오 삭제 → None(메텔라만 짓는다)
        if self.V is None:                                          # 17:32: 새 d5는 베수비오를 core_map.terrain에 둘 수 있다
            self.V = next((t for t in _terrain_list(self.CM) if str(t.get('name', '')).startswith('베수비오')), None)
        self.leads = info_leaders(self.D)
        self.marks = [tuple(m['c']) for m in self.D.get('marks', []) if m.get('c')]
        aq = self.CM['aqueduct']
        (ax, ay), (bx, by) = aq['ground_line_screen']
        self.aq_Y = R.to_plan(ax, ay)[1]                 # 수도교 지면선의 평면 Y(상수, ↘ 아치 열)
        self.aq_H = float(aq.get('arch_height_mm', 26.0))
        self.aq_x0 = min(ax, bx)

    def prop(self, prefix):
        return next(p for p in self.CM['props'] if p['name'].startswith(prefix))

    def slot(self, kw):
        return next((s for s in self.CM['labels']['slots'] if kw in s['name']), None)

    def label_block(self, kw):
        """라벨 글 블록: spec block_poly → drawn 라벨 외곽 → 슬롯 상자 순"""
        s = self.slot(kw)
        if s is None:
            return None
        if s.get('block_poly'):
            return [tuple(p) for p in s['block_poly']]
        for l in self.D.get('labels', []):
            if kw in l.get('name', '') and l.get('poly'):
                return [tuple(p) for p in l['poly']]
        return rbox(s['box'])

    def floor_blocks(self, kws):
        """바닥 글 블록: spec floor_text block_poly → drawn 바닥 글 외곽"""
        out = []
        for ft in self.CM['labels'].get('floor_text', []):
            if any(k in ft['name'] for k in kws) and ft.get('block_poly'):
                out.append([tuple(p) for p in ft['block_poly']])
        if not out:
            for t in self.D.get('texts', []):
                if str(t.get('role', '')).startswith('floor') and any(k in t.get('text', '') for k in kws):
                    out.append([tuple(p) for p in t['poly']])
        return out

    def aq_top_y(self, x):
        """수도교 뒤 난간 윗선의 화면 y(이보다 아래 화면은 수도교에 가린다)"""
        return 0.57735 * x + self.aq_Y - 1.6 - self.aq_H

    def aq_back_Y(self):
        """이보다 평면 Y가 작아야 수도교 뒤(먼 쪽)다(수도교 두께·띠 1.95 + 여유)"""
        return self.aq_Y - 2.4

    def reserve_d(self, X, Y):
        return math.hypot(X - self.hero_c[0], Y - self.hero_c[1]) - self.hero_r


# ───────────────────────── 나무·사람 원형(레이어별로 쌓는다) ─────────────────────────
def tree_mats(atmo=0.0):
    a = atmo
    return {
        0: [mat('cyp', '#3E5A33', a), mat('pine', '#5B7A3D', a), mat('oli', '#8A936A', a), mat('bush', '#7D8B45', a)],
        1: [mat('cyp_dk', '#2B4126', a), mat('pine_dk', '#3B5230', a), mat('oli_dk', '#616A49', a), mat('bush_dk', '#5E6B35', a)],
        2: [mat('bark', '#6B5240', a), mat('bark_dk', '#4F3C2F', a)],
        3: [mat('cyp2', '#4F6E3D', a), mat('pine2', '#6E8B48', a), mat('oli2', '#A0A67C', a), mat('bush2', '#94A055', a)],
        4: [mat('cyp', '#3E5A33', a), mat('pine', '#5B7A3D', a), mat('oli', '#8A936A', a), mat('bush', '#7D8B45', a)],
        5: [mat('cyp_hi', '#6E8E4E', a), mat('pine_hi', '#93AB61', a), mat('oli_hi', '#C2C498', a), mat('bush_hi', '#B4B96E', a)],
        6: [mat('grass', '#8E9A52', a), mat('grass2', '#A9AE68', a), mat('needles', '#A88A5E', a)],
    }


TREE_PART = {0: 'Crowns', 1: 'CrownShade', 2: 'Trunks', 3: 'Leaves', 4: 'Lobes', 5: 'CrownLight', 6: 'Ground'}


def crown_r(kind, h):
    """D8 나무 수관 반지름(평면): 사이프러스 0.125·h, 우산소나무 0.4·h, 올리브 0.45·h"""
    return {'c': 0.125, 'p': 0.40, 'o': 0.45, 'b': 0.5}[kind] * h


class Trees:
    """사이프러스·우산소나무·올리브·덤불. L0 수관 · L1 수관 속 그늘 · L2 줄기·가지 · L3 잎결 · L4 혹 · L5 위-왼쪽 밝은 결 · L6 밑동 풀"""
    def __init__(self, Ly, atmo=0.0, pre='Tree'):
        self.Ly, self.M, self.pre = Ly, tree_mats(atmo), pre

    def bm(self, n):
        return self.Ly(n, self.pre + TREE_PART[n], self.M[n])

    def put(self, kind, x, y, z, h, seed):
        if kind == 'c':
            self.cypress(x, y, z, h, crown_r('c', h), seed)
        elif kind == 'p':
            self.pine(x, y, z, h, crown_r('p', h), seed)
        else:
            self.olive(x, y, z, h, crown_r('o', h), seed)

    def cypress(self, x, y, z, h, r, seed):
        G.cyl(self.bm(2), x, y, r * 0.17, z, z + h * 0.09, 6, 0, r_top=r * 0.13, bottom=True)
        prof = [(0.55, 0.06), (0.90, 0.15), (1.0, 0.28), (0.97, 0.42), (0.86, 0.57), (0.66, 0.72), (0.42, 0.85), (0.16, 0.95), (0.0, 1.0)]
        lathe(self.bm(0), x, y, [(r * a, z + h * b) for a, b in prof], n=9, mi=0, phase=seed,
              rj=lambda k, j: 1.0 + 0.09 * _j(seed, k, j))

        def rad(t):
            for i in range(len(prof) - 1):
                (a0, b0), (a1, b1) = prof[i], prof[i + 1]
                if b0 <= t <= b1:
                    return r * (a0 + (a1 - a0) * (t - b0) / max(1e-6, b1 - b0))
            return 0.0
        for i in range(4):                                             # L1 잎 덩어리 사이 골(오른쪽·아래)
            t = 0.2 + 0.17 * i + 0.05 * _j(seed, i, 1)
            a = math.radians(-15 + 40 * _j(seed, i, 2))
            rr = rad(t) * 0.86
            blob(self.bm(1), (x + rr * math.cos(a), y + rr * math.sin(a), z + h * t), r * 0.30, r * 0.30, h * 0.07, 6, 3, 0.15, seed + i, 0)
        for i in range(14):                                            # L3 비늘 잎결
            t = 0.12 + 0.78 * _h(seed, i, 3)
            a = math.radians(-140 + 190 * _h(seed, i, 4))
            rr = rad(t) * 0.92
            blob(self.bm(3), (x + rr * math.cos(a), y + rr * math.sin(a), z + h * t), r * 0.26, r * 0.26, h * 0.05, 6, 3, 0.2, seed + 10 + i, 0)
        for i in range(5):                                             # L4 층층 혹(윤곽을 깬다)
            t = 0.22 + 0.14 * i
            a = math.radians(-160 + 70 * i + 20 * _j(seed, i, 5))
            rr = rad(t) * 0.95
            blob(self.bm(4), (x + rr * math.cos(a), y + rr * math.sin(a), z + h * t), r * 0.38, r * 0.38, h * 0.08, 7, 3, 0.15, seed + 20 + i, 0)
        for i in range(3):                                             # L5 위-왼쪽 밝은 결
            t = 0.45 + 0.15 * i
            a = math.radians(-95 + 25 * _j(seed, i, 6))
            rr = rad(t) * 0.93
            blob(self.bm(5), (x + rr * math.cos(a), y + rr * math.sin(a), z + h * t), r * 0.18, r * 0.18, h * 0.06, 5, 3, 0.1, seed + 30 + i, 0)
        for i in range(3):                                             # L6 밑동 풀
            a = 2 * math.pi * i / 3 + seed
            blob(self.bm(6), (x + r * 0.55 * math.cos(a), y + r * 0.55 * math.sin(a), z), r * 0.35, r * 0.35, h * 0.03, 6, 2, 0.2, seed + 40 + i, i % 2, zmin=z)

    def pine(self, x, y, z, h, rc, seed):
        top = Vector((x + 0.07 * h * _j(seed, 1), y + 0.07 * h * _j(seed, 2), z + 0.70 * h))
        tube(self.bm(2), (x, y, z), top, 0.05 * h, 0.032 * h, 6, 0)
        for i in range(3):                                             # L2 가지 갈래
            a = 2 * math.pi * i / 3 + seed
            tube(self.bm(2), top, (top.x + 0.38 * rc * math.cos(a), top.y + 0.38 * rc * math.sin(a), z + 0.80 * h), 0.026 * h, 0.016 * h, 5, 1)
        cx, cy, zc = top.x, top.y, z + 0.84 * h
        blob(self.bm(1), (cx, cy, zc - 0.08 * h), rc * 0.94, rc * 0.94, 0.05 * h, 12, 3, 0.06, seed, 1)      # L1 우산 밑면 그늘
        blob(self.bm(0), (cx, cy, zc), rc * 0.62, rc * 0.62, 0.10 * h, 10, 4, 0.08, seed + 1, 1)             # L0 우산
        for i in range(6):
            a = 2 * math.pi * i / 6 + seed * 1.3
            rr = rc * (0.52 + 0.08 * _j(seed, i, 7))
            blob(self.bm(0), (cx + rr * math.cos(a), cy + rr * math.sin(a), zc - 0.01 * h + 0.03 * h * _j(seed, i, 8)),
                 rc * 0.44, rc * 0.44, 0.085 * h, 9, 4, 0.1, seed + 2 + i, 1)
        for i in range(9):                                             # L4 가장자리 혹
            a = 2 * math.pi * i / 9 + seed * 0.7
            blob(self.bm(4), (cx + rc * 0.9 * math.cos(a), cy + rc * 0.9 * math.sin(a), zc - 0.015 * h), rc * 0.2, rc * 0.2, 0.06 * h, 6, 3, 0.15, seed + 10 + i, 1)
        for i in range(11):                                            # L3 윗면 잎결
            a = 2 * math.pi * _h(seed, i, 9)
            rr = rc * 0.72 * math.sqrt(_h(seed, i, 10))
            blob(self.bm(3), (cx + rr * math.cos(a), cy + rr * math.sin(a), zc + 0.075 * h), rc * 0.17, rc * 0.17, 0.035 * h, 6, 3, 0.2, seed + 20 + i, 1)
        for i in range(3):                                             # L5 위-왼쪽 밝은 반점
            a = math.radians(-100 + 30 * _j(seed, i, 11))
            rr = rc * (0.25 + 0.3 * _h(seed, i, 12))
            blob(self.bm(5), (cx + rr * math.cos(a), cy + rr * math.sin(a), zc + 0.095 * h), rc * 0.15, rc * 0.11, 0.022 * h, 6, 2, 0.1, seed + 30 + i, 1)
        blob(self.bm(6), (x, y, z), rc * 0.55, rc * 0.55, 0.012 * h, 10, 2, 0.15, seed + 40, 2, zmin=z)     # L6 솔잎 깔개
        for i in range(2):
            a = 2 * math.pi * _h(seed, i, 13)
            blob(self.bm(6), (x + rc * 0.35 * math.cos(a), y + rc * 0.35 * math.sin(a), z), rc * 0.16, rc * 0.16, 0.03 * h, 6, 2, 0.2, seed + 41 + i, i % 2, zmin=z)

    def olive(self, x, y, z, h, r, seed):
        b2 = self.bm(2)
        p1 = Vector((x + 0.05 * h * _j(seed, 1), y + 0.05 * h * _j(seed, 2), z + 0.34 * h))
        tube(b2, (x, y, z), p1, 0.09 * h, 0.065 * h, 6, 0)
        for i in range(3):
            a = 2 * math.pi * i / 3 + seed
            tube(b2, p1, (p1.x + 0.42 * r * math.cos(a), p1.y + 0.42 * r * math.sin(a), z + 0.55 * h), 0.045 * h, 0.028 * h, 5, i % 2)
        zc = z + 0.66 * h
        blob(self.bm(1), (p1.x + 0.15 * r, p1.y - 0.05 * r, zc - 0.10 * h), r * 0.7, r * 0.7, 0.16 * h, 8, 3, 0.15, seed, 2)
        for i in range(5):
            a = 2 * math.pi * i / 5 + seed * 0.9
            blob(self.bm(0), (p1.x + r * 0.48 * math.cos(a), p1.y + r * 0.48 * math.sin(a), zc + 0.06 * h * _j(seed, i, 3)),
                 r * 0.52, r * 0.52, 0.22 * h, 8, 4, 0.18, seed + 1 + i, 2)
        blob(self.bm(0), (p1.x, p1.y, zc + 0.12 * h), r * 0.55, r * 0.55, 0.22 * h, 8, 4, 0.15, seed + 9, 2)
        for i in range(7):
            a = 2 * math.pi * i / 7 + 0.4 * seed
            blob(self.bm(4), (p1.x + r * 0.85 * math.cos(a), p1.y + r * 0.85 * math.sin(a), zc + 0.05 * h * _j(seed, i, 4)),
                 r * 0.22, r * 0.22, 0.12 * h, 6, 3, 0.2, seed + 10 + i, 2)
        for i in range(10):
            a = math.radians(-150 + 210 * _h(seed, i, 5))
            rr = r * (0.55 + 0.35 * _h(seed, i, 6))
            blob(self.bm(3), (p1.x + rr * math.cos(a), p1.y + rr * math.sin(a), zc + 0.25 * h * _j(seed, i, 7)),
                 r * 0.17, r * 0.17, 0.07 * h, 6, 3, 0.2, seed + 20 + i, 2)
        for i in range(3):
            a = math.radians(-100 + 30 * _j(seed, i, 8))
            blob(self.bm(5), (p1.x + r * 0.45 * math.cos(a), p1.y + r * 0.45 * math.sin(a), zc + 0.30 * h), r * 0.16, r * 0.13, 0.05 * h, 6, 2, 0.1, seed + 30 + i, 2)
        for i in range(3):
            a = 2 * math.pi * i / 3 + seed
            blob(self.bm(6), (x + r * 0.5 * math.cos(a), y + r * 0.5 * math.sin(a), z), r * 0.25, r * 0.25, 0.05 * h, 6, 2, 0.2, seed + 40 + i, i % 2, zmin=z)

    def bush(self, x, y, z, r, seed, kind=3):
        for i in range(3):
            a = 2 * math.pi * i / 3 + seed
            blob(self.bm(0), (x + 0.45 * r * math.cos(a), y + 0.45 * r * math.sin(a), z + 0.45 * r), 0.6 * r, 0.6 * r, 0.5 * r, 7, 3, 0.2, seed + i, kind, zmin=z)
        blob(self.bm(1), (x + 0.25 * r, y - 0.05 * r, z + 0.2 * r), 0.5 * r, 0.5 * r, 0.3 * r, 6, 3, 0.2, seed + 5, kind, zmin=z)
        blob(self.bm(3), (x - 0.15 * r, y - 0.3 * r, z + 0.8 * r), 0.25 * r, 0.25 * r, 0.15 * r, 5, 2, 0.2, seed + 6, kind)
        blob(self.bm(5), (x - 0.25 * r, y - 0.2 * r, z + 0.92 * r), 0.15 * r, 0.12 * r, 0.06 * r, 5, 2, 0.1, seed + 7, kind)


CLOTH = ['#EFE8DA', '#B13A2C', '#3E5D8C', '#C99B45', '#5F7B4A', '#8C5236', '#D9C8A8']
SKIN, HAIR, BELT = len(CLOTH), len(CLOTH) + 1, len(CLOTH) + 2


def people_mats(atmo=0.0):
    return [mat('cl%d' % i, c, atmo) for i, c in enumerate(CLOTH)] + [mat('skin', '#D8A07C', atmo), mat('hair', '#3B2A20', atmo), mat('belt', '#6E4A30', atmo)]


def person(bm, x, y, z, H, cloth, seed, arm=0.0):
    """사람 하나. H = 키(발~머리 꼭대기, D8), 화면 폭 ≈ 0.31·H: 다리(피부)·튜닉·띠·팔·목·머리·머리카락"""
    w = H
    G.box(bm, x - 0.068 * w, x - 0.014 * w, y - 0.03 * w, y + 0.03 * w, z, z + 0.32 * w, SKIN)
    G.box(bm, x + 0.014 * w, x + 0.068 * w, y - 0.03 * w, y + 0.03 * w, z, z + 0.32 * w, SKIN)
    G.cyl(bm, x, y, 0.125 * w, z + 0.28 * w, z + 0.72 * w, 8, cloth, r_top=0.095 * w, bottom=True)
    G.cyl(bm, x, y, 0.112 * w, z + 0.50 * w, z + 0.54 * w, 8, BELT, bottom=True)
    for sx in (-1, 1):
        lift = arm if sx > 0 else 0.0
        tube(bm, (x + sx * 0.108 * w, y, z + 0.70 * w), (x + sx * 0.132 * w, y - lift * 0.12 * w, z + (0.43 + 0.22 * lift) * w),
             0.03 * w, 0.026 * w, 5, cloth if sx < 0 else SKIN)
    G.cyl(bm, x, y, 0.036 * w, z + 0.70 * w, z + 0.83 * w, 6, SKIN, bottom=True)
    blob(bm, (x, y, z + 0.885 * w), 0.068 * w, 0.068 * w, 0.075 * w, 6, 3, 0.03, seed, SKIN)
    blob(bm, (x + 0.008 * w, y + 0.01 * w, z + 0.948 * w), 0.07 * w, 0.07 * w, 0.05 * w, 6, 2, 0.04, seed + 1, HAIR)


def person_scr(X, Y, Z, H):
    sx, sy = R.to_screen(X, Y, Z)
    return rbox((sx - 0.16 * H, sy - H, sx + 0.16 * H, sy + 0.1 * H))


def amphora(bm, x, y, z, h, mi, mi_dk=None, seed=0.0):
    prof = [(0.0, 0.0), (0.10, 0.06), (0.17, 0.25), (0.16, 0.45), (0.09, 0.62), (0.05, 0.74), (0.075, 0.78), (0.05, 0.80)]
    lathe(bm, x, y, [(r * h, z + q * h) for r, q in prof], n=8, mi=mi, phase=seed)
    if mi_dk is not None:
        G.cyl(bm, x, y, 0.035 * h, z + 0.80 * h, z + 0.815 * h, 6, mi_dk, bottom=True)


# ───────────────────────── 1. 카이킬리아 메텔라 무덤 ─────────────────────────
# 로마 시대 무덤(BCE 30–10)을 오늘의 폐허 상태로 그린다: 네모 기단(무덤 자체의 건축 기단, 전시 받침 아님) + 원통 드럼.
# 겉면은 트래버틴 마름돌(L3 줄눈), 일부 뜯긴 자리에서 콘크리트 속(L4: 석회 반죽 + 응회암·현무암 덩이)이 보인다.
# 꼭대기 아래에 소머리(부크라니움)·꽃줄 부조 띠(L4). 중세 카에타니 성채의 톱니 흉벽은 0. 꼭대기는 흙·풀·나무(폐허 식생, L6).
# 크기는 설계 2D(drawn.json 메텔라 기단 29.8×9.3·드럼 반지름 13.44·높이 29.1)와 같은 비례로 평면 mm에 직접 짓고,
# fit_to_box로 spec 상자 [354, 288, 420, 358]을 채운다(D4).
MET_P, MET_R = 15.0, 13.4                     # 기단 반폭 · 드럼 반지름(평면 mm)
MET_ZLOT = 0.22                               # 대지 포장 윗면(D13 포장 턱 ≤ 0.3)
MZ = dict(plinth=1.0, band=1.3, pod_f=8.2, pod_c=8.8, pod_t=9.1, db1=9.6, db2=10.1, d_f=26.0, frieze=28.4,
          corn1=28.9, corn2=29.3, attic=30.4, cap=31.1)
TH_I = -95.0                                  # 비문판 방위(Blender 지역 각, 보이는 앞-왼쪽 면)
MET_SUMMIT = [('c', -8.4, -8.6, 7.2), ('c', -4.4, -11.0, 6.6), ('c', -10.9, -4.2, 6.2), ('o', -2.0, -5.5, 4.6)]   # 꼭대기 나무(평면 오프셋)


def metella_mats():
    return dict(
        face=blk('MetDrum', '#DCC59D', '#E3CFA9', '#D3BB92', '#BFA27B', 4.4, 1.5, 0.13),      # 16:25 레퍼런스(피라네시): 큰 마름돌 켜(드럼 약 10켜)
        pod=blk('MetPodium', '#D6BE95', '#DDC69F', '#CDB389', '#B99C75', 4.6, 1.6, 0.14),
        attic=blk('MetAttic', '#DDC8A2', '#E7D5B2', '#D2BA92', '#B59873', 1.8, 0.55, 0.11),
        pave=blk('MetPave', '#D9C9A7', '#CBB994', '#E4D7BA', '#B39F7B', 1.8, 1.3, 0.12),
        trav=mat('met_trav', '#DDC7A0'), trav_lo=mat('met_trav_lo', '#C8AF86'), trav_hi=mat('met_trav_hi', hi_of('#DDC7A0')),
        core=mat('met_core', '#A39279'), core_dk=mat('met_core_dk', '#7E6E58'), aggr=mat('met_aggr', '#86806F'), aggr2=mat('met_aggr2', '#BDB29C'),
        lime=mat('met_lime', '#CFC6B0'),
        marble=mat('met_marble', '#F3EDE0'), marble2=mat('met_marble2', '#D8CDB9'), mdeep=mat('met_mdeep', '#A08F75'),
        deep=mat('met_deep', '#7C6047'), deeper=mat('met_deeper', '#5C4431'),
        hi=mat('met_hi', hi_of('#E2CCA4', 1.14)), hi_m=mat('met_hi_m', hi_of('#F3EDE0', 1.04)),
        tuff=mat('met_tuff', '#B8A487'), tuff_top=mat('met_tuff_top', '#D3C3A5'), tuff_hi=mat('met_tuff_hi', hi_of('#D3C3A5', 1.12)),
        grass=mat('met_grass', '#9BA35C'), grass2=mat('met_grass2', '#B4B56E'), moss=mat('met_moss', '#8E9A52'),
        stain=mat('met_stain', '#C2A884'), soil=mat('met_soil', '#B38A63'), earth=mat('met_earth', '#C9B48E'),
    )


def met_layout(ctx):
    """메텔라 대지·기단·드럼 자리(평면 mm, spec·히어로 예약 원에서 계산).
    대지 뒤-오른쪽 변 = R6b 끝(평면 Y), R6b 띠가 변 안에 1mm 여유로 들어온다. 오른쪽 꼭짓점·앞 꼭짓점·왼쪽 앞 모서리가 상자 변을 채우고,
    왼쪽 뒤 모서리는 히어로 예약 원(R 90.5) 밖이 되게 한 칸 들인 계단 모서리로 만든다"""
    box_fit = ctx.lm['L5']['projected_box']
    if 'R6b' in ctx.roads:
        box, r6b = box_fit, ctx.roads['R6b']
    else:                                                  # d5: 길 0 → d4 대지 기하(d4 상자 + d4 R6b)로 모양을 잡고, fit_to_box가 새 상자로 옮긴다
        box, r6b = MET_BOX_D4, R6B_D4
    y_edge = r6b[3]
    X0 = r6b[0] - 1.0
    X1 = (box[2] - 0.2) / C30 + y_edge
    Yf = 2.0 * (box[3] - 0.05) - X1
    Xl = (box[0] + 0.5) / C30 + Yf
    cx, cy = ctx.hero_c
    Rr = ctx.hero_r + 1.4
    d2 = Rr * Rr - (X0 - cx) ** 2
    Yn = min(Yf, cy - math.sqrt(d2)) if d2 > 0 else Yf
    while math.hypot(Xl - cx, Yf - cy) < Rr and Xl < X1 - 10.0:
        Xl += 0.2
    if 'R6b' not in ctx.roads or Yn <= y_edge + 2 * MET_P + 3.0:   # 20:01 d5: 길 0·예약 원 철회 → 계단 모서리 없는 네모 대지
        Yn, Xl = Yf, X0
    if Yn < Yf - 0.05 and Xl > X0 + 0.05:
        poly = [(X0, y_edge), (X1, y_edge), (X1, Yf), (Xl, Yf), (Xl, Yn), (X0, Yn)]
    else:
        poly = [(X0, y_edge), (X1, y_edge), (X1, Yf), (X0, Yf)]
    P = MET_P
    py0 = y_edge + 2.0
    if py0 + 2 * P > Yn - 0.8 and Xl > X0 + 2.0:          # 계단 모서리와 기단이 부딪히면 기단을 줄인다
        P = max(MET_R + 1.2, (Yn - 0.8 - py0) / 2.0)
    Xc, Yc = X0 + 2.0 + P, py0 + P
    return dict(box=box_fit, poly=poly, Xc=Xc, Yc=Yc, P=P, y_edge=y_edge, X0=X0, X1=X1, Yf=Yf, Xl=Xl, Yn=Yn, r6b=r6b)


def face_patch(bm, axis, c, uc, zc, ru, rz, seed, mi_rim, mi_core, out=1.0, nn=14):
    """평평한 벽면 위 '뜯긴 겉면': 들쭉날쭉한 짙은 테(L1 깊이) + 안쪽 콘크리트 속(L4). axis 'y': 면 y=c, 'x': 면 x=c. out: 바깥 방향 부호"""
    pts = []
    for i in range(nn):
        a = 2 * math.pi * i / nn
        q = 1.0 + 0.22 * _j(seed, i) + (0.18 if i % 3 == 0 else 0.0)
        pts.append((uc + ru * q * math.cos(a), zc + rz * q * math.sin(a)))

    def P3(u, z, off):
        return (u, c + out * off, z) if axis == 'y' else (c + out * off, u, z)
    fan(bm, [P3(uc + (u - uc) * 1.14, zc + (z - zc) * 1.14 + 0.06, 0.05) for u, z in pts], mi_rim)
    fan(bm, [P3(u, z, 0.10) for u, z in pts], mi_core)
    return pts


def drum_patch(bm, R_, ph0, ph1, z0, z1, seed, mi_rim, mi_core, n=9):
    """드럼(원통) 위 '뜯긴 겉면': 칸마다 위·아래 끝이 들쭉날쭉한 세로 띠 조각(테는 짙은 깊이색)"""
    for i in range(n):
        a0 = math.radians(ph0 + (ph1 - ph0) * i / n)
        a1 = math.radians(ph0 + (ph1 - ph0) * (i + 1) / n)
        f = math.sin(math.pi * (i + 0.5) / n) ** 0.6
        zm = (z0 + z1) / 2.0
        lo = zm - (zm - z0) * f * (0.8 + 0.25 * _h(seed, i, 1))
        hi = zm + (z1 - zm) * f * (0.8 + 0.25 * _h(seed, i, 2))
        for (rr, zl, zh, aa0, aa1, mi) in ((R_ + 0.10, lo - 0.14, hi + 0.18, a0 - 0.012, a1 + 0.012, mi_rim), (R_ + 0.15, lo, hi, a0, a1, mi_core)):
            vs = [bm.verts.new((rr * math.cos(aa0), rr * math.sin(aa0), zl)), bm.verts.new((rr * math.cos(aa1), rr * math.sin(aa1), zl)),
                  bm.verts.new((rr * math.cos(aa1), rr * math.sin(aa1), zh)), bm.verts.new((rr * math.cos(aa0), rr * math.sin(aa0), zh))]
            ff = bm.faces.new(vs)
            ff.material_index = mi


def _met_core(Ly, M, g, LC):
    P, R_, Z = g['P'], MET_R, MZ
    lot = [LC(X, Y) for X, Y in g['poly']]
    # L0 덩어리: 대지 흙 바닥 · 기단 속 콘크리트 · 드럼 속 · 꼭대기 흙 둔덕(낮게, 폐허 위 흙·풀)
    b0 = Ly(0, 'Mass', [M['core'], M['grass'], M['earth']])
    G.prism(b0, lot, 0.0, MET_ZLOT - 0.03, 2)
    G.box(b0, -P + 0.12, P - 0.12, -P + 0.12, P - 0.12, 0.9, Z['pod_c'], 0)
    G.cyl(b0, 0, 0, R_ - 0.15, Z['pod_t'], Z['attic'] - 0.1, 64, 0, bottom=True)
    lathe(b0, 0, 0, [(R_ - 0.45, Z['attic'] - 0.05), (R_ - 1.6, Z['attic'] + 0.35), (R_ - 4.5, Z['attic'] + 0.6),
                     (R_ - 8.5, Z['cap'] - 0.15), (0.0, Z['cap'])], n=36, mi=1, rj=lambda k, j: 1.0 + 0.03 * _j(7, k, j))
    # L1 깊이색: 기단 코니스 밑 그늘 줄 · 프리즈 아래 홈 · 비문판 테두리 · 드럼 굽 위 홈
    b1 = Ly(1, 'Shade', [M['deep'], M['mdeep'], M['deeper'], M['core_dk']])
    e = P + 0.16
    for (x0, x1, y0, y1) in ((-e, e, -e, -P + 0.1), (P - 0.1, e, -e, e), (-e, e, P - 0.1, e), (-e, -P + 0.1, -e, e)):
        G.box(b1, x0, x1, y0, y1, Z['pod_f'] - 0.3, Z['pod_f'] - 0.02, 0)
    G.ring(b1, 0, 0, R_ - 0.2, R_ + 0.1, Z['d_f'] - 0.24, Z['d_f'] - 0.02, 72, 1)
    G.ring(b1, 0, 0, R_ + 0.02, R_ + 0.12, 20.85, 24.95, 10, 2, TH_I - 13.0, TH_I + 13.0)
    G.ring(b1, 0, 0, R_ - 0.1, R_ + 0.09, Z['db2'], Z['db2'] + 0.22, 72, 0)
    # L2 부재: 기단 굽·굽 위 띠·코니스·윗단 띠, 드럼 굽 몰딩 2단·프리즈 띠(대리석)·코니스 2단
    b2 = Ly(2, 'Members', [M['trav_lo'], M['trav'], M['trav_hi'], M['marble2']])
    G.box(b2, -P - 0.7, P + 0.7, -P - 0.7, P + 0.7, MET_ZLOT, Z['plinth'], 0)
    G.box(b2, -P - 0.3, P + 0.3, -P - 0.3, P + 0.3, Z['plinth'], Z['band'], 1)
    G.box(b2, -P - 0.45, P + 0.45, -P - 0.45, P + 0.45, Z['pod_f'], Z['pod_c'], 2)
    G.box(b2, -P - 0.2, P + 0.2, -P - 0.2, P + 0.2, Z['pod_c'], Z['pod_t'], 1)
    G.ring(b2, 0, 0, R_ - 1.0, R_ + 0.6, Z['pod_t'], Z['db1'], 64, 0)
    G.ring(b2, 0, 0, R_ - 1.0, R_ + 0.32, Z['db1'], Z['db2'], 64, 1)
    G.ring(b2, 0, 0, R_ - 0.6, R_ + 0.12, Z['d_f'], Z['frieze'], 72, 3)
    G.ring(b2, 0, 0, R_ - 0.6, R_ + 0.55, Z['frieze'], Z['corn1'], 72, 2)
    G.ring(b2, 0, 0, R_ - 0.6, R_ + 0.3, Z['corn1'], Z['corn2'], 72, 1)
    # L3 표면 무늬: 드럼·기단·애틱 트래버틴 마름돌(블록 줄눈) · 대지 판석
    b3 = Ly(3, 'Facing', [M['face'], M['pod'], M['attic'], M['pave']])
    G.ring(b3, 0, 0, R_ - 0.13, R_ + 0.05, Z['db2'], Z['d_f'], 72, 0)
    f = P + 0.12
    for (x0, x1, y0, y1) in ((-f, f, -f, -P + 0.02), (-f, f, P - 0.02, f), (-f, -P + 0.02, -P, P), (P - 0.02, f, -P, P)):
        G.box(b3, x0, x1, y0, y1, Z['band'], Z['pod_f'], 1)
    G.ring(b3, 0, 0, R_ - 0.6, R_ + 0.08, Z['corn2'], Z['attic'], 72, 2)
    G.prism(b3, lot, MET_ZLOT - 0.03, MET_ZLOT, 3)
    # L4 형태 디테일: 소머리·꽃줄 프리즈, 비문판·비문 줄, 트로피 부조, 뜯긴 겉면 속 콘크리트(석회 반죽 + 덩이)
    b4 = Ly(4, 'Relief', [M['marble'], M['marble2'], M['deep'], M['trav_hi'], M['core'], M['core_dk'], M['aggr'], M['aggr2'], M['lime']])
    rz = R_ + 0.14
    zf = (Z['d_f'] + Z['frieze']) / 2.0
    angs = [a for a in range(-129, 46, 12) if abs(a - TH_I) > 9]
    for a in angs:
        t = math.radians(a)
        cx, cy = rz * math.cos(t), rz * math.sin(t)
        blob(b4, (cx, cy, zf - 0.12), 0.30, 0.30, 0.42, 7, 4, 0.06, a, 0)
        tx, ty = -math.sin(t), math.cos(t)
        for sg in (-1, 1):
            tube(b4, (cx, cy, zf + 0.18), (cx + sg * 0.42 * tx, cy + sg * 0.42 * ty, zf + 0.45), 0.07, 0.04, 5, 0)
    for a0, a1 in zip(angs[:-1], angs[1:]):
        if a1 - a0 > 13:
            continue
        for i in range(1, 7):
            a = math.radians(a0 + (a1 - a0) * i / 7.0)
            zz = zf + 0.22 - 0.6 * math.sin(math.pi * i / 7.0)
            blob(b4, (rz * math.cos(a), rz * math.sin(a), zz), 0.2, 0.2, 0.19, 6, 3, 0.1, a0 * 7 + i, 0)
    G.ring(b4, 0, 0, R_ + 0.05, R_ + 0.2, 21.05, 24.75, 10, 0, TH_I - 12.0, TH_I + 12.0)
    for (z0, z1, half) in ((23.95, 24.2, 10.2), (23.3, 23.55, 9.0), (22.65, 22.9, 10.0), (22.0, 22.2, 6.0)):
        G.ring(b4, 0, 0, R_ + 0.2, R_ + 0.23, z0, z1, 8, 2, TH_I - half, TH_I + half)
    t = math.radians(TH_I)
    cx, cy = (R_ + 0.16) * math.cos(t), (R_ + 0.16) * math.sin(t)
    tx, ty = -math.sin(t), math.cos(t)
    tube(b4, (cx, cy, zf - 1.05), (cx, cy, zf + 0.5), 0.07, 0.06, 5, 1)
    tube(b4, (cx - 0.5 * tx, cy - 0.5 * ty, zf), (cx + 0.5 * tx, cy + 0.5 * ty, zf), 0.06, 0.06, 5, 1)
    blob(b4, (cx, cy, zf + 0.35), 0.24, 0.24, 0.26, 6, 3, 0.05, 3.3, 0)
    blob(b4, (cx + 0.35 * tx, cy + 0.35 * ty, zf - 0.45), 0.26, 0.26, 0.3, 7, 3, 0.04, 4.4, 0)
    # 뜯긴 겉면: 기단 왼면(지역 y = −P, 보이는 앞-왼쪽 면) 2곳 · 오른면(지역 x = +P) 1곳 · 드럼 앞 1곳
    cf = P + 0.12
    for k, (uc, zc, ru, rz_) in enumerate(((-3.0, 4.5, 7.6, 2.55), (9.6, 3.6, 2.6, 1.6))):
        pts = face_patch(b4, 'y', -cf, uc, zc, ru, rz_, 11.0 + k, 5, 4, out=-1.0)
        for i in range(34 if k == 0 else 12):                        # 콘크리트 속 덩이(응회암·현무암) · 석회 반점
            u = uc + ru * 0.75 * _j(k, i, 1.3)
            zz = zc + rz_ * 0.7 * _j(k, i, 1.4)
            blob(b4, (u, -cf - 0.16, zz), 0.16 + 0.1 * _h(k, i), 0.05, 0.13 + 0.08 * _h(k, i, 2), 5, 2, 0.2, k * 20 + i, 6 + (i % 3 == 0) * 2 if i % 4 else 7)
    pts = face_patch(b4, 'x', cf, -2.5, 4.6, 7.2, 2.6, 14.0, 5, 4, out=1.0)
    for i in range(30):
        v = -2.5 + 7.2 * 0.75 * _j(3, i, 1.3)
        zz = 4.6 + 2.6 * 0.7 * _j(3, i, 1.4)
        blob(b4, (cf + 0.16, v, zz), 0.05, 0.16 + 0.1 * _h(3, i), 0.13 + 0.08 * _h(3, i, 2), 5, 2, 0.2, 60 + i, 6 if i % 2 else 7)
    drum_patch(b4, R_, -74.0, -40.0, 10.5, 13.9, 21.0, 5, 4, n=12)
    for i in range(10):
        a = math.radians(-71 + 28 * _h(i, 2.1))
        zz = 10.9 + 2.6 * _h(i, 2.2)
        blob(b4, ((R_ + 0.2) * math.cos(a), (R_ + 0.2) * math.sin(a), zz), 0.15, 0.15, 0.12, 5, 2, 0.2, 80 + i, 6 if i % 2 else 7)
    # L5 하이라이트(D9: 화면 0.25~0.4mm, 면색 명도 +10~15%): 보이는 두 변의 코니스·굽 윗선, 기단 앞 모서리, 드럼 코니스·애틱·굽 윗선
    b5 = Ly(5, 'Light', [M['hi'], M['trav_hi'], M['hi_m']])
    for (gz, zz) in ((P + 0.45, Z['pod_c']), (P + 0.7, Z['plinth']), (P + 0.2, Z['pod_t'])):
        G.box(b5, -gz, gz, -gz, -gz + 0.34, zz, zz + 0.03, 0)
        G.box(b5, gz - 0.34, gz, -gz, gz, zz, zz + 0.03, 0)
    G.box(b5, P - 0.24, P + 0.14, -P - 0.17, -P - 0.13, Z['band'] + 0.05, Z['pod_f'] - 0.3, 1)
    G.ring(b5, 0, 0, R_ + 0.22, R_ + 0.55, Z['corn1'], Z['corn1'] + 0.03, 40, 0, -138.0, 48.0)
    G.ring(b5, 0, 0, R_ - 0.25, R_ + 0.08, Z['attic'], Z['attic'] + 0.03, 40, 0, -138.0, 48.0)
    G.ring(b5, 0, 0, R_ + 0.27, R_ + 0.6, Z['db1'], Z['db1'] + 0.03, 40, 1, -138.0, 48.0)
    G.ring(b5, 0, 0, R_ + 0.07, R_ + 0.13, Z['d_f'] + 0.05, Z['frieze'] - 0.05, 6, 2, -124.0, -119.0)
    G.ring(b5, 0, 0, R_ + 0.05, R_ + 0.075, Z['db2'] + 0.3, Z['d_f'] - 0.3, 4, 1, -128.0, -122.0)
    # L6 얼룩·식생: 프리즈 밑 빗물 자국 · 기단 굽 이끼 · 대지 풀
    b6 = Ly(6, 'Life', [M['stain'], M['moss'], M['grass'], M['grass2'], M['soil']])
    for i, a in enumerate((-126, -104, -76, -54, -30, -8, 16, 36)):
        z0 = 19.5 + 2.6 * _h(i, 3.3)
        G.ring(b6, 0, 0, R_ + 0.05, R_ + 0.07, z0, Z['d_f'] - 0.3, 3, 0, a - 0.7 - 0.5 * _h(i, 1.1), a + 0.7)
    for i in range(18):
        side = i % 2
        u = -P + 2 * P * _h(i, 5.1)
        x, y = (u, -P - 0.9) if side == 0 else (P + 0.9, u)
        blob(b6, (x, y, MET_ZLOT), 0.5 + 0.3 * _h(i, 5.2), 0.5, 0.3, 6, 2, 0.25, i, 1 + (i % 3 == 0), zmin=MET_ZLOT)
    for i in range(22):
        X = g['X0'] + 1.0 + (g['X1'] - g['X0'] - 2.0) * _h(i, 7.1)
        Y = g['y_edge'] + 1.0 + (g['Yf'] - g['y_edge'] - 2.0) * _h(i, 7.2)
        x, y = LC(X, Y)
        if abs(x) < P + 1.3 and abs(y) < P + 1.3:
            continue
        if not _pip(X, Y, g['poly']):
            continue
        blob(b6, (x, y, MET_ZLOT), 0.8 + 0.7 * _h(i, 7.3), 0.6 + 0.5 * _h(i, 7.4), 0.1, 6, 2, 0.3, i + 50, 2 + (i % 2), zmin=MET_ZLOT)


def _met_ruin(Ly, M):
    """18:45 레퍼런스(피라네시) 잣대: 드럼 마름돌의 튀어나온 돌·빠진 돌, 아래 침식(콘크리트 속), 늘어진 덩굴·틈 수풀, 긴 빗물 줄, 흉벽 잡석.
    보이는 호(Blender 지역 각 −140° ~ 46°)에만"""
    R_, Z = MET_R, MZ
    b3 = Ly(3, 'Blocks', [M['trav'], M['trav_hi'], M['trav_lo']])
    b1 = Ly(1, 'Missing', [M['deeper'], M['core_dk']])
    rows = [1.5 * k for k in range(6, 18) if Z['db2'] + 0.2 < 1.5 * k and 1.5 * k + 1.5 < Z['d_f'] - 0.3]
    k = 0
    for zr in rows:
        a = -140.0 + 6.0 * _h(k, 21.1)
        while a < 46.0:
            w = math.degrees((2.2 + 2.2 * _h(k, 21.2)) / R_)
            u = _h(k, 21.3)
            n_ = max(2, int(w / 4))
            if u < 0.42:                                                  # 튀어나온 돌(밝은·짙은 두 단)
                G.ring(b3, 0, 0, R_ - 0.1, R_ + 0.07 + 0.08 * _h(k, 21.4), zr + 0.07, zr + 1.43, n_, 1 if u < 0.2 else 2, a + 0.3, a + w - 0.3)
            elif u < 0.5:                                                 # 빠진 돌(짙은 구멍)
                G.ring(b1, 0, 0, R_ - 0.05, R_ + 0.06, zr + 0.1, zr + 1.4, n_, k % 2, a + 0.4, a + w - 0.4)
            a += w + 0.2; k += 1
    bE = Ly(4, 'Erosion', [M['core'], M['core_dk'], M['aggr'], M['aggr2'], M['lime']])   # 드럼 밑동 침식(겉돌이 빠져 콘크리트 속)
    drum_patch(bE, R_, 4.0, 34.0, 10.2, 12.4, 33.0, 1, 0, n=10)
    drum_patch(bE, R_, -128.0, -106.0, 10.2, 11.8, 34.0, 1, 0, n=8)
    for i in range(26):
        a = math.radians((6.0 + 26.0 * _h(i, 23.1)) if i % 2 else (-126.0 + 18.0 * _h(i, 23.1)))
        zz = 10.5 + 1.5 * _h(i, 23.2)
        blob(bE, ((R_ + 0.2) * math.cos(a), (R_ + 0.2) * math.sin(a), zz), 0.14, 0.14, 0.11, 5, 2, 0.2, 400 + i, 2 + i % 3)
    b6 = Ly(6, 'Ivy', [M['grass'], M['grass2'], M['moss'], M['stain']])     # 코니스에서 늘어진 덩굴 · 틈 수풀 · 긴 빗물 줄
    for i in range(16):
        a = math.radians(-136.0 + 180.0 * _h(i, 24.1))
        L = 1.5 + 3.5 * _h(i, 24.2)
        nb = 2 + int(L / 1.1)
        for j in range(nb):
            t = j / max(1, nb - 1)
            zz = Z['corn1'] - 0.2 - L * t
            rr = R_ + 0.32 - 0.12 * t
            blob(b6, (rr * math.cos(a), rr * math.sin(a), zz), 0.55 - 0.25 * t, 0.55 - 0.25 * t, 0.6, 6, 3, 0.3, 500 + 10 * i + j, (i + j) % 3)
    for i in range(10):
        a = math.radians(-130.0 + 170.0 * _h(i, 25.1))
        zz = 12.0 + 11.0 * _h(i, 25.2)
        blob(b6, ((R_ + 0.3) * math.cos(a), (R_ + 0.3) * math.sin(a), zz), 0.4 + 0.3 * _h(i, 25.3), 0.4, 0.35, 6, 3, 0.3, 600 + i, i % 3)
    for i in range(18):
        a = -134.0 + 176.0 * _h(i, 26.1)
        z1 = Z['d_f'] - 0.3; z0 = z1 - 2.5 - 6.0 * _h(i, 26.2)
        G.ring(b6, 0, 0, R_ + 0.05, R_ + 0.075, z0, z1, 2, 3, a - 0.5 - 0.6 * _h(i, 26.3), a + 0.5)
    bR = Ly(4, 'Rubble', [M['core'], M['tuff'], M['tuff_top']])          # 흉벽 위·사이 잡석
    for i in range(18):
        a = math.radians(360.0 * _h(i, 27.1))
        rr = MET_R - 0.6 - 0.4 * _h(i, 27.2)
        blob(bR, (rr * math.cos(a), rr * math.sin(a), Z['attic'] + 0.78), 0.25 + 0.2 * _h(i, 27.3), 0.22, 0.18, 5, 2, 0.25, 700 + i, i % 3)


def _met_walls(Ly, M, g, LC):
    """L2 대지 담(응회암, 낮게 1.0) + 갓돌, L5 보이는 바깥 변 갓돌 윗선. 뒤-오른쪽 변은 R6b가 들어오는 자리를 비운다"""
    b2 = Ly(2, 'Wall', [M['tuff'], M['tuff_top']])
    b5 = Ly(5, 'WallLight', [M['tuff_hi']])
    t, hgt = 0.45, 1.0
    gap = (g['r6b'][0] - 0.4, g['r6b'][1] + 0.6)
    poly = g['poly']
    n = len(poly)
    cxy = (sum(p[0] for p in poly) / n, sum(p[1] for p in poly) / n)
    for i in range(n):
        (Xa, Ya), (Xb, Yb) = poly[i], poly[(i + 1) % n]
        segs = [((Xa, Ya), (Xb, Yb))]
        if abs(Ya - g['y_edge']) < 1e-6 and abs(Yb - g['y_edge']) < 1e-6:
            lo, hi_ = min(Xa, Xb), max(Xa, Xb)
            segs = [((x0, Ya), (x1, Ya)) for x0, x1 in ((lo, gap[0]), (gap[1], hi_)) if x1 - x0 > 0.6]
        for (Xa_, Ya_), (Xb_, Yb_) in segs:
            if abs(Ya_ - Yb_) < 1e-6:                                  # 평면 X 방향 변(Y 일정)
                inward = 1.0 if cxy[1] > Ya_ else -1.0
                Y0w, Y1w = sorted((Ya_, Ya_ + inward * t))
                X0w, X1w = sorted((Xa_, Xb_))
                pbox_l(b2, LC, X0w, X1w, Y0w, Y1w, 0.0, hgt, 0)
                pbox_l(b2, LC, X0w - 0.05, X1w + 0.05, Y0w - 0.05, Y1w + 0.05, hgt, hgt + 0.15, 1)
                if inward < 0:                                       # 바깥이 +Y(보이는 왼면 쪽) → 윗선
                    pbox_l(b5, LC, X0w, X1w, Y1w - 0.12, Y1w + 0.05, hgt + 0.15, hgt + 0.17, 0)
            else:                                                     # 평면 Y 방향 변(X 일정)
                inward = 1.0 if cxy[0] > Xa_ else -1.0
                X0w, X1w = sorted((Xa_, Xa_ + inward * t))
                Y0w, Y1w = sorted((Ya_, Yb_))
                pbox_l(b2, LC, X0w, X1w, Y0w, Y1w, 0.0, hgt, 0)
                pbox_l(b2, LC, X0w - 0.05, X1w + 0.05, Y0w - 0.05, Y1w + 0.05, hgt, hgt + 0.15, 1)
                if inward < 0:                                       # 바깥이 +X(보이는 오른면 쪽)
                    pbox_l(b5, LC, X1w - 0.12, X1w + 0.05, Y0w, Y1w, hgt + 0.15, hgt + 0.17, 0)


def pbox_l(bm, LC, X0, X1, Y0, Y1, z0, z1, mi):
    """평면 절대 상자 → 루트 지역 상자"""
    xa, ya = LC(X0, Y0)
    xb, yb = LC(X1, Y1)
    G.box(bm, min(xa, xb), max(xa, xb), min(ya, yb), max(ya, yb), z0, z1, mi)


def met_tree_specs(g):
    """둘레 나무(평면 절대 자리, D8 키): 뒤-왼쪽 변 밖 사이프러스 열 · 오른쪽 모서리 우산소나무 · 오른쪽-앞 변·왼쪽 앞 모서리 사이프러스"""
    X0, Ye, X1, Yf, Xl, Yn = g['X0'], g['y_edge'], g['X1'], g['Yf'], g['Xl'], g['Yn']
    hc = [H_NEAR * k for k in (2.6, 2.95, 2.75, 2.5)]
    return [('c', X0 - 2.6, Ye + 5.3, hc[0]), ('c', X0 - 2.8, Ye + 12.6, hc[1]), ('c', X0 - 2.7, Ye + 20.6, hc[2]),
            ('c', X0 - 2.2, Yn - 3.6, hc[3]), ('p', X1 - 3.6, Ye + 3.9, H_NEAR * K_PINE), ('c', X1 - 1.9, Ye + 17.5, hc[2]),
            ('c', Xl + 2.0, Yf - 2.0, hc[3]), ('o', X1 - 2.6, Ye + 27.0, H_NEAR * K_OLIVE)]


def build_metella(GC, ctx):
    g = met_layout(ctx)
    Xc, Yc = g['Xc'], g['Yc']

    def LC(X, Y):
        return (X - Xc, -(Y - Yc))
    root = G.new_root('SUB_Metella_root', GC, Xc, Yc, 0.0)
    M = metella_mats()
    Ly = Lay('Metella', root, GC)
    _met_core(Ly, M, g, LC)
    _met_walls(Ly, M, g, LC)
    _met_ruin(Ly, M)
    base = Ly.finish()
    # 꼭대기 식생(드럼 윗면 높이를 광선으로 잰다) · 둘레 나무 · 방문객(키 2.4)
    Ly = Lay('Metella', root, GC)
    T = Trees(Ly, 0.0, 'Tree')
    for i, (kd, dx, dy, h) in enumerate(MET_SUMMIT if DECOR else ()):   # 16:14: 꼭대기 나무 0(풀 결·풀 덩이는 남긴다)
        x, y = dx, -dy
        z = ray_z(base, x, y)
        T.put(kd, x, y, (z if z is not None else MZ['attic']) - 0.04, h, 31.0 + i)
    bt = Ly(3, 'Turf', [mat('met_turf1', '#8E9A56'), mat('met_turf2', '#A7AC66'), mat('met_turf3', '#B7A77A'), mat('met_turf4', '#7F8C4C')])
    for i in range(70):                                           # L3 풀 결: 풀 덩이 3색 + 흙 반점
        a = 2 * math.pi * _h(i, 8.1)
        rr = 0.8 + 11.4 * math.sqrt(_h(i, 8.2))
        x, y = rr * math.cos(a), rr * math.sin(a)
        z = ray_z(base, x, y)
        if z is None:
            continue
        k = 2 if i % 9 == 0 else (i % 4 if i % 4 != 2 else 3)
        blob(bt, (x, y, z - 0.02), 0.32 + 0.4 * _h(i, 8.3), 0.28 + 0.3 * _h(i, 8.4), 0.08 + 0.06 * _h(i, 8.5), 6, 2, 0.3, i + 300, k, zmin=z - 0.02)
    # L4 성가퀴(16:25 레퍼런스: 중세 카에타니 성의 톱니 흉벽 — 지금 모습). 애틱 테두리 위 흉벽 띠 + 톱니(군데군데 무너짐)
    br = Ly(4, 'Merlons', [M['tuff'], M['tuff_top'], M['core']])
    bh = Ly(5, 'MerlonTops', [M['tuff_hi']])
    rr_in, rr_out = MET_R - 1.0, MET_R - 0.15
    G.ring(br, 0, 0, rr_in, rr_out, MZ['attic'] - 0.05, MZ['attic'] + 0.75, 72, 0)                  # 흉벽 띠
    G.ring(bh, 0, 0, rr_in, rr_out, MZ['attic'] + 0.75, MZ['attic'] + 0.78, 72, 0)
    nm = 26
    for i in range(nm):
        a0 = 360.0 * i / nm
        if 70.0 < a0 < 130.0 and _h(i, 9.4) < 0.7:                 # 뒤쪽 일부 무너짐
            continue
        hh = (1.35 if _h(i, 9.2) > 0.2 else 0.55) + 0.25 * _h(i, 9.3)
        w = 360.0 / nm * 0.55
        G.ring(br, 0, 0, rr_in, rr_out, MZ['attic'] + 0.75, MZ['attic'] + 0.75 + hh, 4, 1 if _h(i, 9.5) > 0.5 else 0, a0, a0 + w)
        G.ring(bh, 0, 0, rr_in, rr_out, MZ['attic'] + 0.75 + hh, MZ['attic'] + 0.78 + hh, 4, 0, a0, a0 + w)
    bs = Ly(6, 'Summit', [M['grass'], M['grass2'], M['moss'], M['soil']])
    for i in range(16):
        a = 2 * math.pi * _h(i, 6.1)
        rr = 1.5 + 10.0 * math.sqrt(_h(i, 6.2))
        x, y = rr * math.cos(a), rr * math.sin(a)
        z = ray_z(base, x, y)
        if z is not None:
            blob(bs, (x, y, z), 0.55 + 0.35 * _h(i, 6.3), 0.5, 0.3 + 0.2 * _h(i, 6.4), 6, 3, 0.25, i + 30, i % 4)
    for i in range(22):                                           # 16:25 레퍼런스: 흉벽 위로 솟는 수풀 덩이(평평한 초록 원판 대신)
        a = 2 * math.pi * (i + 0.5 * _h(i, 6.7)) / 22.0
        rr = MET_R - 2.2 - 2.4 * _h(i, 6.8)
        x, y = rr * math.cos(a), rr * math.sin(a)
        z = ray_z(base, x, y)
        if z is not None:
            blob(bs, (x, y, z), 1.3 + 0.6 * _h(i, 6.9), 1.2 + 0.5 * _h(i, 7.0), 2.0 + 1.0 * _h(i, 7.1), 7, 3, 0.3, i + 90, i % 3)
    bands = [rect_scr(ctx.roads[k]) for k in ('R6a', 'R6b', 'R1') if k in ctx.roads]
    lab = ctx.label_block('메텔라')
    marks = list(ctx.marks)
    d_mark = next((m for m in ctx.D.get('marks', []) if m.get('letter') == 'D'), None)
    if d_mark:
        marks.append((min(d_mark['c'][0], 365.9), d_mark['c'][1]))   # d5: D 표지 map_pt x ≤ 365.9로 옮김(spec L5 draw_gaps)
    why = {}

    def clear(kd, X, Y, h):
        r = crown_r(kd, h)
        q = tree_scr(X, Y, MET_ZLOT, r, h)
        if min(poly_dist(q, b) for b in bands) < 2.0:
            return 'R6a·R6b 띠 2mm'
        if ctx.leads and min(line_dist(q, L) for L in ctx.leads) < 1.5:
            return '지시선 1.5mm'
        if any(pt_poly_d(m, q) < 2.6 for m in marks):
            return '짝 표지'
        if lab and poly_dist(q, lab) < 1.5:
            return '라벨 블록'
        if ctx.reserve_d(X, Y) < r + 1.0:
            return '히어로 예약 원'
        if max(p[0] for p in q) > g['box'][2] - 0.15:
            return '상자 오른쪽 변'
        return None
    kept = []
    for i, (kd, X, Y, h) in enumerate(met_tree_specs(g) if DECOR else ()):   # 16:14: 둘레 나무 0
        w = clear(kd, X, Y, h)
        if w:
            why['%s(%.1f, %.1f)' % (kd, X, Y)] = w
            continue
        x, y = LC(X, Y)
        T.put(kd, x, y, MET_ZLOT if _pip(X, Y, g['poly']) else 0.0, h, 1.3 + i)
        kept.append((kd, round(X, 1), round(Y, 1), round(h, 2)))
    bp = Ly(6, 'People', people_mats())
    ppl = [(g['Xl'] + 6.2, g['Yf'] - 3.0, 0, 0.0), (g['Xl'] + 8.6, g['Yf'] - 2.0, 1, 0.6), (g['X1'] - 3.4, Yc + 5.2, 2, 0.0), (g['X1'] - 2.6, Yc + 8.8, 3, 0.4)]
    np_ = 0
    for k, (X, Y, c, arm) in enumerate(ppl if DECOR else ()):             # 16:14: 방문객 0
        q = person_scr(X, Y, MET_ZLOT, H_NEAR)
        if (ctx.leads and min(line_dist(q, L) for L in ctx.leads) < 1.5) or (lab and poly_dist(q, lab) < 1.5):
            continue
        x, y = LC(X, Y)
        person(bp, x, y, MET_ZLOT, H_NEAR, c, k * 1.7, arm=arm)
        np_ += 1
    Ly.finish()
    s, bb = G.fit_to_box(root, g['box'])
    bpy.context.view_layer.update()
    mw = root.matrix_world
    edge_Y = -(mw @ Vector((0.0, -(g['y_edge'] - Yc), 0.0))).y
    corners = [(lambda v: (v.x, -v.y))(mw @ Vector((*LC(X, Y), 0.0))) for X, Y in g['poly']]
    REPORT['Metella'] = dict(scale=round(root.scale.x, 4), bbox=[round(v, 2) for v in bb], box=g['box'],
                             bbox_err=[round(bb[i] - g['box'][i], 2) for i in range(4)], area=round((bb[2] - bb[0]) * (bb[3] - bb[1]), 1),
                             lot_back_right_Y=round(edge_Y, 2), r6b_end_Y=g['y_edge'], lot_plan=[[round(a, 2), round(b, 2)] for a, b in corners],
                             reserve_min_mm=round(min(ctx.reserve_d(X, Y) for X, Y in corners), 2), trees=kept, trees_dropped=why, people=np_,
                             person_h=round(H_NEAR * root.scale.x, 3))
    REPORT['_met_geo'] = dict(P=g['P'], R=MET_R, Z=MZ)
    return root


# ───────────────────────── 2. 아피아 가도 소품: 짐수레(소 두 마리·마부) ─────────────────────────
def cart_mats():
    return dict(
        wood=mat('wood', '#A97B4F'), wood_dk=mat('wood_dk', '#7E5A39'), wood_hi=mat('wood_hi', hi_of('#A97B4F', 1.15)), wood_deep=mat('wood_deep', '#5E4330'),
        planks=blk('CartPlanks', '#A97B4F', '#B5875A', '#9C7046', '#6E4E33', 0.7, 0.07, 0.012),
        iron=mat('iron', '#6A5B4E'), terra=mat('terra', '#B4623E'), terra_hi=mat('terra_hi', '#CB7E56'), terra_dk=mat('terra_dk', '#7C3F28'),
        sack=mat('sack', '#D7C095'), sack_dk=mat('sack_dk', '#B49A70'), rope=mat('rope', '#8E7550'),
        ox=mat('ox', '#D6CAB3'), ox_dk=mat('ox_dk', '#A3957E'), horn=mat('horn', '#EEE6D2'), hoof=mat('hoof', '#4E3E31'),
        dust=mat('dust', '#CDB48C'),
    )


def _wheel(b_rim, b_sp, x, y, z, r, wdt, mi_rim, mi_sp, mi_hub):
    Mx = Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.pi / 2, 4, 'Y')
    xb = XB(b_rim, Mx)
    G.ring(xb, 0, 0, r * 0.84, r, -wdt / 2, wdt / 2, 18, mi_rim)
    xs = XB(b_sp, Mx)
    G.cyl(xs, 0, 0, r * 0.2, -wdt * 0.9, wdt * 0.9, 10, mi_hub, bottom=True)
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.2
        tube(b_sp, (x, y, z), (x, y + r * 0.86 * math.cos(a), z + r * 0.86 * math.sin(a)), r * 0.05, r * 0.04, 4, mi_sp)


def _ox(bm, x, y, z, s, seed, M_idx):
    """소 한 마리(앞이 +y): 몸통·목·머리·뿔(리라 모양)·다리 4·꼬리. M_idx = (몸, 짙은, 뿔, 발굽)"""
    mb, md, mh, mf = M_idx
    blob(bm, (x, y, z + 1.02 * s), 0.36 * s, 0.92 * s, 0.4 * s, 10, 4, 0.04, seed, mb)
    blob(bm, (x, y + 0.85 * s, z + 1.18 * s), 0.27 * s, 0.38 * s, 0.33 * s, 8, 3, 0.04, seed + 1, mb)
    blob(bm, (x, y + 1.32 * s, z + 1.1 * s), 0.17 * s, 0.32 * s, 0.17 * s, 8, 3, 0.04, seed + 2, mb)
    blob(bm, (x, y + 1.6 * s, z + 1.03 * s), 0.12 * s, 0.1 * s, 0.1 * s, 6, 3, 0.04, seed + 3, md)
    for sg in (-1, 1):
        p0 = (x + sg * 0.1 * s, y + 1.28 * s, z + 1.26 * s)
        p1 = (x + sg * 0.32 * s, y + 1.22 * s, z + 1.42 * s)
        p2 = (x + sg * 0.3 * s, y + 1.3 * s, z + 1.68 * s)
        tube(bm, p0, p1, 0.045 * s, 0.035 * s, 5, mh)
        tube(bm, p1, p2, 0.035 * s, 0.015 * s, 5, mh)
    for sx_ in (-1, 1):
        for sy_ in (-1, 1):
            lx, ly = x + sx_ * 0.2 * s, y + sy_ * 0.62 * s
            tube(bm, (lx, ly, z + 0.75 * s), (lx, ly, z + 0.1 * s), 0.08 * s, 0.06 * s, 5, md)
            tube(bm, (lx, ly, z + 0.1 * s), (lx, ly, z), 0.065 * s, 0.07 * s, 5, mf)
    tube(bm, (x, y - 0.9 * s, z + 1.15 * s), (x + 0.05 * s, y - 1.0 * s, z + 0.55 * s), 0.03 * s, 0.02 * s, 4, md)


def build_cart(GC, ctx):
    """지역 1 = 사람 키(D8 원형 정규화) → 루트 배율 2.4. 짐칸 길이 2.2 · 암포라 0.45 · 소 축척 0.62 · 마부 1.0"""
    P = ctx.prop('아피아 가도 수레')
    X0, Y0 = P['plan']
    r1 = ctx.roads['R1']
    xc = (r1[0] + r1[1]) / 2.0
    X0 = max(X0, xc + 0.8 + 0.72 * H_NEAR + 0.2)                     # 흰 중앙선(1.6)과 바퀴 사이 여유
    z_road = ROAD_TOP['R1']
    root = G.new_root('SUB_AppiaCart_root', GC, X0, Y0, z_road)
    root.scale = (H_NEAR, H_NEAR, H_NEAR)
    M = cart_mats()
    Ly = Lay('AppiaCart', root, GC)
    b0 = Ly(0, 'Body', [M['wood'], M['wood_dk']])                    # L0 짐칸 바닥 판·차축
    G.box(b0, -0.52, 0.52, -1.1, 1.1, 0.46, 0.58, 0)
    G.box(b0, -0.74, 0.74, -0.16, -0.06, 0.36, 0.44, 1)
    b1 = Ly(1, 'Shade', [M['wood_deep']])                             # L1 짐칸 속
    G.box(b1, -0.47, 0.47, -1.04, 1.04, 0.58, 0.60, 0)
    b2 = Ly(2, 'Members', [M['wood_dk'], M['wood'], M['iron']])       # L2 바퀴·끌채·멍에·말뚝
    for sx_ in (-1, 1):
        _wheel(b2, b2, sx_ * 0.66, -0.11, 0.40, 0.40, 0.08, 2, 0, 0)
    tube(b2, (0.0, 1.05, 0.52), (0.0, 2.98, 0.74), 0.045, 0.04, 6, 0)
    G.box(b2, -0.60, 0.60, 2.92, 3.0, 0.76, 0.83, 0)
    for sx_ in (-1, 1):
        for yy in (-1.06, -0.35, 0.35, 1.06):
            G.box(b2, sx_ * 0.55 - 0.03, sx_ * 0.55 + 0.03, yy - 0.03, yy + 0.03, 0.56, 0.92, 0)
    b3 = Ly(3, 'Planks', [M['planks']])                               # L3 옆판·앞뒤판 널빤지
    for sx_ in (-1, 1):
        G.box(b3, sx_ * 0.55 - 0.02, sx_ * 0.55 + 0.02, -1.06, 1.06, 0.58, 0.86, 0)
    for yy in (-1.08, 1.08):
        G.box(b3, -0.53, 0.53, yy - 0.02, yy + 0.02, 0.58, 0.82, 0)
    b4 = Ly(4, 'Load', [M['terra'], M['terra_dk'], M['sack'], M['sack_dk'], M['rope']])   # L4 짐
    for i, (x, y) in enumerate(((-0.24, -0.66), (0.0, -0.72), (0.24, -0.64), (-0.12, -0.25))):
        amphora(b4, x, y, 0.60, 0.45, 0, 1, i)
    for i, (x, y, r) in enumerate(((-0.2, 0.38, 0.22), (0.2, 0.36, 0.21), (0.0, 0.74, 0.19))):
        blob(b4, (x, y, 0.74 + 0.03 * i), r, r * 1.1, r * 0.7, 8, 3, 0.12, i + 5, 2 if i != 1 else 3)
    tube(b4, (-0.54, 0.1, 0.93), (0.54, 0.1, 0.93), 0.016, 0.016, 4, 4)
    b5 = Ly(5, 'Light', [M['wood_hi']])                               # L5 옆판·멍에 윗선
    for sx_ in (-1, 1):
        G.box(b5, sx_ * 0.55 - 0.035, sx_ * 0.55 + 0.035, -1.08, 1.08, 0.86, 0.885, 0)
    G.box(b5, -0.60, 0.60, 2.92, 3.0, 0.83, 0.845, 0)
    b6 = Ly(6, 'Oxen', [M['ox'], M['ox_dk'], M['horn'], M['hoof'], M['dust']])   # L6 소 두 마리 · 바큇자국 먼지
    for k, sx_ in enumerate((-0.30, 0.30)):
        _ox(b6, sx_, 2.55, 0.0, 0.62, k + 0.5, (0, 1, 2, 3))
    for sx_ in (-0.66, 0.66):
        blob(b6, (sx_, -1.5, 0.0), 0.1, 0.55, 0.015, 6, 2, 0.2, sx_, 4, zmin=0.0)
    bp = Ly(6, 'People', people_mats() + [M['wood_dk']])
    person(bp, -0.98, 1.75, 0.0, 1.0, 5, 2.2, arm=0.9)
    tube(bp, (-0.86, 1.66, 0.62), (-0.72, 2.6, 0.96), 0.014, 0.01, 4, len(CLOTH) + 3)
    Ly.finish()
    bb = kids_bbox(root)
    REPORT['AppiaCart'] = dict(scale=H_NEAR, bbox=[round(v, 1) for v in bb], spec_box=P['box'], z_road=z_road,
                               plan=[round(root.location.x, 2), round(-root.location.y, 2)], person_h=H_NEAR, cart_len_mm=round(2.2 * H_NEAR, 2))
    return root


# ───────────────────────── 3. 아피아 가도 소품: 사이프러스·우산소나무 열 · 이정표 · 길손 ─────────────────────────
def build_appia_trees(GC, ctx):
    """spec planted '아피아 가도 둘레 사이프러스·소나무 열'. 뒤쪽 변은 높은 열, 앞쪽 변은 길·바닥 글을 가리지 않게 길에서 띄운다(D8 키)"""
    root = G.new_root('SUB_AppiaTrees_root', GC, 0.0, 0.0, 0.0)
    Ly = Lay('AppiaTrees', root, GC)
    T = Trees(Ly, 0.0, 'Tree')
    r1 = ctx.roads['R1']
    pb = next(p for p in ctx.CM['planted'] if '아피아' in p['name'])['box']
    aq_lab = ctx.label_block('수도교')
    texts = ctx.floor_blocks(('VIA APPIA', '아피아 가도 →'))
    cb = REPORT.get('AppiaCart', {}).get('bbox') or ctx.prop('아피아 가도 수레')['box']
    met_box = ctx.lm['L5']['projected_box']
    bands = [rect_scr(ctx.roads[k]) for k in ('R6a', 'R6b') if k in ctx.roads]
    placed, skipped = [], []
    hc = [H_NEAR * k for k in (2.75, 3.0, 2.6, 2.85)]
    hp = H_NEAR * K_PINE

    def ok(kind, X, Y, h, side):
        r = crown_r(kind, h)
        q = tree_scr(X, Y, 0.0, r, h)
        xs = [p[0] for p in q]
        ys = [p[1] for p in q]
        cx, cy = R.to_screen(X, Y)
        if not (pb[0] - 1.0 <= cx <= pb[2] + 1.0 and pb[1] - 1.0 <= cy <= pb[3] + 1.0):
            return False
        if min(ys) < pb[1] - 1.5 or max(xs) > 423.0:
            return False
        if aq_lab and poly_dist(q, aq_lab) < 2.0:
            return False
        if poly_dist(q, rbox(cb)) < 1.0 or poly_dist(q, rbox(met_box)) < 1.0:
            return False
        if any(poly_dist(q, b) < 2.0 for b in bands):
            return False
        if side == 'front' and poly_dist(q, rect_scr(r1)) < 1.0:
            return False
        if any(poly_dist(q, t) < 1.5 for t in texts):
            return False
        if ctx.leads and min(line_dist(q, L) for L in ctx.leads) < 1.5:
            return False
        if ctx.reserve_d(X, Y) < r + 0.5:
            return False
        return True
    Xb = r1[0] - 3.0                                                 # 뒤쪽 변 열: 사이프러스·우산소나무 번갈아
    k = 0
    Y = 64.0
    while Y > 4.0:
        kind = 'c' if k % 2 == 0 else 'p'
        h = hc[k % 4] if kind == 'c' else hp
        X = Xb - (1.2 if kind == 'p' else 0.0)
        if ok(kind, X, Y, h, 'back'):
            placed.append((kind, X, Y, h))
        else:
            skipped.append((kind, round(X, 1), round(Y, 1)))
        Y -= 6.4
        k += 1
    for (kind, dX, Y) in (('p', -8.0, 47.0), ('c', -6.2, 36.0), ('p', -8.4, 26.0), ('c', -13.0, 44.0), ('c', -12.0, 16.0)):
        h = hp if kind == 'p' else hc[2]
        if ok(kind, Xb + dX, Y, h, 'back'):
            placed.append((kind, Xb + dX, Y, h))
        else:
            skipped.append((kind, round(Xb + dX, 1), Y))
    for (kind, Y) in (('c', 60.0), ('p', 50.0), ('c', 41.0), ('c', 30.0), ('p', 22.0), ('c', 12.0)):   # 앞쪽 변: 길 오른쪽 변에서 띄운다
        h = hp if kind == 'p' else hc[3]
        r = crown_r(kind, h)
        X = r1[1] + h * 1.15 + 1.6 + 1.3 * r
        if ok(kind, X, Y, h, 'front'):
            placed.append((kind, X, Y, h))
        else:
            skipped.append((kind, round(X, 1), Y))
    for i, (kind, X, Y, h) in enumerate(placed):
        T.put(kind, X, -Y, 0.0, h, 11.0 + i)
    # L6 길가: 이정표(밀리아리움) 2 · 풀 띠 · 길손 둘(길 윗면, 키 2.4)
    M = dict(stone=mat('stone', '#D9CCB2'), stone_dk=mat('stone_dk', '#A99A80'), stone_hi=mat('stone_hi', hi_of('#D9CCB2', 1.12)))
    b6 = Ly(6, 'Roadside', [M['stone'], M['stone_dk'], M['stone_hi']] + tree_mats()[6])
    for (X, Y) in ((r1[0] - 0.9, 68.0), (r1[1] + 0.9, 33.0)):
        G.cyl(b6, X, -Y, 0.3, 0.0, 0.18, 10, 1, bottom=True)
        G.cyl(b6, X, -Y, 0.22, 0.18, 1.05, 10, 0, r_top=0.2, bottom=True)
        G.cyl(b6, X, -Y, 0.21, 1.05, 1.09, 10, 2, bottom=True)
    for i in range(26):
        side = i % 2
        Y = 4.0 + (80.0 if side == 0 else 75.0) * _h(i, 8.1)
        X = (r1[0] - 0.7 - 1.2 * _h(i, 8.2)) if side == 0 else (r1[1] + 0.7 + 1.2 * _h(i, 8.2))
        if ctx.reserve_d(X, Y) < 1.0:
            continue
        blob(b6, (X, -Y, 0.0), 0.5 + 0.5 * _h(i, 8.3), 0.5 + 0.4 * _h(i, 8.4), 0.18, 6, 2, 0.3, i + 70, 3 + (i % 2), zmin=0.0)
    bp = Ly(6, 'People', people_mats())
    zr = ROAD_TOP['R1']
    npl = 0
    for (dX, Y, c, arm) in ((4.4, 80.5, 0, 0.0), (6.0, 79.4, 3, 0.7)):
        X = r1[0] + dX
        if ctx.reserve_d(X, Y) < 0.5:
            continue
        person(bp, X, -Y, zr, H_NEAR, c, 9.1 + dX, arm=arm)
        npl += 1
    Ly.finish()
    REPORT['AppiaTrees'] = dict(trees=len(placed), kinds={k: sum(1 for p in placed if p[0] == k) for k in ('c', 'p')}, skipped=len(skipped),
                                skipped_at=skipped, heights=sorted(set(round(p[3], 2) for p in placed)), people=npl, person_h=H_NEAR)
    return root


# ───────────────────────── 4. 교외 빌라(포도밭 농가, 라벨 없음, 가장 먼 쪽 축척 1.8) ─────────────────────────
def villa_mats(atmo=0.0, pre='Vil'):
    a = atmo
    return dict(
        plaster=mat(pre + '_plaster', '#ECDDBF', a), plaster2=mat(pre + '_plaster2', '#E2CDA6', a),
        brick=blk(pre + 'Brick', '#B86F4C', '#C98260', '#AD6646', '#8F5236', 0.75, 0.25, 0.05, a),
        roof=blk(pre + 'Roof', '#B5623F', '#C2704A', '#A85A3A', '#8A4A30', 0.45, 0.9, 0.06, a),
        roof_flat=mat(pre + '_roof', '#B9663F', a), ridge=mat(pre + '_ridge', hi_of('#C2704A', 1.14), a),
        dark=mat(pre + '_dark', '#5E4432', a), deep=mat(pre + '_deep', '#7A5A43', a),
        wood=mat(pre + '_wood', '#A97B4F', a), wood_dk=mat(pre + '_wood_dk', '#7E5A39', a),
        stone=mat(pre + '_stone', '#D3C3A2', a), hi=mat(pre + '_hi', hi_of('#ECDDBF', 1.06), a),
        earth=mat(pre + '_earth', '#CDB085', a), earth2=mat(pre + '_earth2', '#BE9E73', a),
        pave=blk(pre + 'Pave', '#D6C6A4', '#CAB894', '#E0D2B4', '#B09C78', 1.4, 0.9, 0.1, a),
        terra=mat(pre + '_terra', '#B4623E', a), terra_dk=mat(pre + '_terra_dk', '#6E3A25', a),
        vine=mat(pre + '_vine', '#6F8B45', a), vine2=mat(pre + '_vine2', '#8DA352', a), vine_dk=mat(pre + '_vine_dk', '#4E6634', a),
        water=mat(pre + '_water', '#6F98A3', a),
    )


def _villa_parts(Ly, M, s):
    """평면 지역(X ↘ 0~30, Y ↙ 0~24). 본채는 뒤-오른쪽 변, 작업동은 뒤-왼쪽 변, 마당은 앞. s = 예상 루트 배율(사람·나무 키를 D8에 맞춘다)"""
    vz = 1.9                                                         # 건물 높이 배율(사람 1.8mm에 2층 농가 비례)

    def Z(v):
        return 0.12 + (v - 0.12) * vz
    b0 = Ly(0, 'Mass', [M['plaster'], M['plaster2'], M['earth']])
    pbox(b0, 0.0, 30.0, 0.0, 24.0, 0.0, 0.12, 2)
    pbox(b0, 3.0, 21.0, 0.6, 8.0, 0.12, Z(5.6), 0)
    pbox(b0, 0.6, 7.2, 8.0, 21.6, 0.12, Z(3.8), 1)
    pbox(b0, 21.0, 29.0, 1.0, 7.0, 0.12, Z(3.4), 1)
    b3r = Ly(3, 'Roof', [M['roof']])
    pgable(b3r, 3.0, 21.0, 0.6, 8.0, Z(5.6), Z(5.6) + 1.7 * 1.3, 'X', 0, 0.45)
    pgable(b3r, 0.6, 7.2, 8.0, 21.6, Z(3.8), Z(3.8) + 1.3 * 1.3, 'Y', 0, 0.4)
    pgable(b3r, 21.0, 29.0, 1.0, 7.0, Z(3.4), Z(3.4) + 1.2 * 1.3, 'X', 0, 0.35)
    b3 = Ly(3, 'Surface', [M['brick'], M['pave']])
    pbox(b3, 2.95, 21.05, 7.95, 8.05, 0.12, Z(0.9), 0)
    pbox(b3, 7.15, 7.25, 8.0, 21.6, 0.12, Z(0.9), 0)
    pbox(b3, 13.0, 15.6, 10.4, 24.0, 0.12, 0.2, 1)
    b1 = Ly(1, 'Shade', [M['dark'], M['deep']])
    pbox(b1, 8.0, 20.4, 8.0, 8.06, 0.12, Z(3.1), 1)
    for X in (4.2, 6.6, 9.0, 11.4, 13.8, 16.2, 18.6):
        pbox(b1, X, X + 0.8, 8.0, 8.07, Z(4.15), Z(5.0), 0)
    pbox(b1, 13.6, 15.0, 8.0, 8.09, 0.12, Z(2.3), 0)
    for Y in (11.0, 14.0, 18.5):
        pbox(b1, 7.2, 7.27, Y, Y + 0.9, Z(1.7), Z(2.6), 0)
    pbox(b1, 7.2, 7.28, 15.4, 16.9, 0.12, Z(2.4), 0)
    pbox(b1, 23.6, 26.4, 7.0, 7.08, 0.12, Z(2.5), 0)
    b2 = Ly(2, 'Members', [M['stone'], M['wood'], M['wood_dk'], M['plaster2'], M['roof_flat']])
    for X in (8.6, 11.3, 14.0, 16.8, 19.7):
        G.cyl(b2, X, -10.0, 0.22, 0.12, Z(3.05), 8, 0, bottom=True)
    G.prism(b2, [(8.0, -8.0), (20.4, -8.0), (20.4, -10.6), (8.0, -10.6)], Z(3.05), Z(3.05) + 0.25, 4)
    for (X0w, X1w, Y0w, Y1w) in ((0.0, 13.0, 23.5, 24.0), (15.6, 30.0, 23.5, 24.0), (29.5, 30.0, 7.0, 24.0)):
        pbox(b2, X0w, X1w, Y0w, Y1w, 0.12, Z(1.9), 3)
    for X in (13.0, 15.6):
        pbox(b2, X - 0.25, X + 0.25, 23.3, 24.2, 0.12, Z(2.4), 0)
    for X in (22.2, 25.6, 28.8):
        for Y in (17.0, 22.2):
            pbox(b2, X - 0.12, X + 0.12, Y - 0.12, Y + 0.12, 0.12, Z(2.6), 1)
    for Y in (17.0, 22.2):
        pbox(b2, 22.0, 29.0, Y - 0.1, Y + 0.1, Z(2.6), Z(2.6) + 0.18, 2)
    pbox(b2, 13.45, 15.15, 8.0, 8.14, Z(2.3), Z(2.3) + 0.2, 1)
    b4 = Ly(4, 'Detail', [M['terra'], M['terra_dk'], M['stone'], M['wood_dk'], M['water']])
    for i in range(6):
        X = 17.6 + 1.85 * i
        lathe(b4, X, -14.2, [(0.62, 0.12), (0.7, 0.32), (0.55, 0.52), (0.36, 0.6)], n=10, mi=0)
        G.cyl(b4, X, -14.2, 0.3, 0.6, 0.62, 8, 1, bottom=True)
    G.ring(b4, 10.5, -17.0, 0.55, 0.85, 0.12, 0.95, 14, 2)
    G.cyl(b4, 10.5, -17.0, 0.55, 0.5, 0.6, 12, 4, bottom=True)
    for i, (X, Y) in enumerate(((24.0, 8.3), (24.7, 8.5), (25.4, 8.3), (24.35, 8.9), (25.05, 9.0))):
        amphora(b4, X, -Y, 0.12, 0.45 * H_FAR / s, 0, 1, i)
    pbox(b4, 17.0, 17.9, 2.0, 2.9, Z(5.6), Z(5.6) + 2.6, 2)
    b5 = Ly(5, 'Light', [M['ridge'], M['hi']])
    pbox(b5, 2.6, 21.4, 4.22, 4.38, Z(5.6) + 1.7 * 1.3 - 0.03, Z(5.6) + 1.7 * 1.3 + 0.08, 0)
    pbox(b5, 3.76, 4.04, 7.6, 22.0, Z(3.8) + 1.3 * 1.3 - 0.03, Z(3.8) + 1.3 * 1.3 + 0.08, 0)
    pbox(b5, 20.7, 29.3, 3.92, 4.08, Z(3.4) + 1.2 * 1.3 - 0.03, Z(3.4) + 1.2 * 1.3 + 0.08, 0)
    for (X0w, X1w, Y0w, Y1w) in ((0.0, 13.0, 23.8, 24.06), (15.6, 30.0, 23.8, 24.06), (29.76, 30.06, 7.0, 24.0)):
        pbox(b5, X0w, X1w, Y0w, Y1w, Z(1.9), Z(1.9) + 0.05, 1)
    T = Trees(Ly, 0.0, 'Tree')                                        # L6 식생·생활(D8 먼 쪽 키)
    T.put('c', -2.6, 1.2, 0.0, H_FAR * 3.0 / s, 4.1)
    T.put('c', 31.6, -3.0, 0.0, H_FAR * 2.6 / s, 4.7)
    T.put('o', 33.0, -21.0, 0.0, H_FAR * K_OLIVE / s, 5.3)
    T.put('o', -2.8, -25.5, 0.0, H_FAR * K_OLIVE / s * 0.92, 5.9)
    b6 = Ly(6, 'Vines', [M['vine'], M['vine2'], M['vine_dk']])
    for i in range(16):
        X = 22.2 + 6.6 * _h(i, 9.1)
        Y = 17.0 + 5.2 * _h(i, 9.2)
        blob(b6, (X, -Y, Z(2.6) + 0.25), 0.75, 0.75, 0.32, 6, 3, 0.25, i + 90, i % 3)
    for i in range(10):
        X = 1.0 + 28.0 * _h(i, 9.3)
        Y = 22.6 + 0.8 * _h(i, 9.4)
        blob(b6, (X, -Y, 0.12), 0.5, 0.4, 0.3, 6, 2, 0.3, i + 110, 2, zmin=0.12)
    bp = Ly(6, 'People', people_mats())
    person(bp, 16.0, -15.4, 0.12, H_FAR / s, 1, 6.6, arm=0.6)
    person(bp, 23.4, -11.0, 0.12, H_FAR / s, 3, 7.4)


def build_villa(GC, ctx):
    P = ctx.prop('교외 빌라')
    box = P['box']
    X0, Y0 = R.to_plan((box[0] + box[2]) / 2, (box[1] + box[3]) / 2 + 3.0)
    s_est = 0.46
    M = villa_mats()
    root = None
    for it in range(3):
        if root is not None:
            for o in list(root.children_recursive):
                me = o.data if o.type == 'MESH' else None
                bpy.data.objects.remove(o, do_unlink=True)
                if me is not None and me.users == 0:
                    bpy.data.meshes.remove(me)
        root = G.new_root('SUB_Villa_root', GC, X0, Y0, 0.0)
        Ly = Lay('Villa', root, GC)
        _villa_parts(Ly, M, s_est)
        Ly.finish()
        G.fit_to_box(root, box)
        s = root.scale.x
        if abs(s - s_est) / s_est < 0.025:
            break
        s_est = s
    bb = kids_bbox(root)
    REPORT['Villa'] = dict(scale=round(root.scale.x, 3), bbox=[round(v, 1) for v in bb], box=box,
                           person_h=round(H_FAR / s_est * root.scale.x, 2), iterations=it + 1)
    return root


# ───────────────────────── 5. 베수비오(79년 이전: 넓고 완만한 봉우리 하나, 잿빛 평평한 정상, 포도밭 비탈. 연기 없음) ─────────────────────────
VES_RB, VES_TT = 24.0, 0.24                    # 밑동 반지름(지역) · 정상 평탄부 비
VES_HK = 0.80                                  # 높이/밑동 반지름: 상자 비(40/58)보다 낮게 짓고(정상 평탄부 뒤 테두리 몫 포함) fit 뒤 z 배율로 높이를 맞춘다
VES_H = VES_RB * VES_HK
VES_N = 56
VES_TS = [1.0, 0.95, 0.9, 0.84, 0.77, 0.69, 0.61, 0.53, 0.46, 0.39, 0.33, 0.28, VES_TT, VES_TT * 0.6, 0.0]
VES_ATMO = 0.5                                 # 땅색 50% 혼합(spec V form, D9)


def _ves_z(t, a):
    """t = ρ/RB, a = 지역 방위(라디안). 오목한 사면 + 골 9갈래(cos(9a+0.7)=1인 곳이 골) · 능선 굴곡"""
    if t >= 1.0:
        return 0.0
    if t <= VES_TT:
        return VES_H + 0.25 * (1.0 - t / VES_TT)
    u = (1.0 - t) / (1.0 - VES_TT)
    g = 1.0 - 0.055 * (0.5 + 0.5 * math.cos(9 * a + 0.7)) - 0.025 * (0.5 + 0.5 * math.cos(4 * a + 2.1))
    return VES_H * (u ** 1.55) * (g if t < 0.97 else 1.0)


def _ves_r(a):
    return 1.0 + 0.03 * math.sin(5 * a + 1.1) + 0.015 * math.sin(11 * a + 0.4)


GULLY_A = [((2 * k * math.pi - 0.7) / 9.0) % (2 * math.pi) for k in range(9)]           # 골(낮은 곳)
RIDGE_A = [(((2 * k + 1) * math.pi - 0.7) / 9.0) % (2 * math.pi) for k in range(9)]     # 능선(높은 곳)


def ves_mats():
    a = VES_ATMO
    return dict(
        vine=mat('v_vine', '#7F9A5A', a), wood=mat('v_wood', '#8B975C', a), scrub=mat('v_scrub', '#9C9468', a), ash=mat('v_ash', '#A39889', a),
        gully=mat('v_gully', '#728058', a), pit=mat('v_pit', '#5E5148', a), rock=mat('v_rock', '#776A5E', a),
        wall=mat('v_wall', '#C9B48E', a), path=mat('v_path', '#D3BE95', a), vrow=mat('v_vrow', '#5E7A3F', a), vrow2=mat('v_vrow2', '#6C8A47', a),
        hi=mat('v_hi', '#D4CFA0', a), hi_ash=mat('v_hi_ash', '#CFC6B4', a), tree=mat('v_tree', '#55703A', a), tree2=mat('v_tree2', '#3F5A33', a),
    )


def build_vesuvius_cone(GC, ctx):
    """L0 원뿔(오목 사면·평평한 정상, 원형 밑동 = 설계 2D와 같은 밑동 타원)만 짓고 투영 상자에 맞춘다:
    fit_to_box(폭 맞춤) → 밑동 중심 화면 높이는 두고 z 배율로 상자 높이 → 아래 변을 상자 아래 변에. 면적 ≤ 2,320(상자 0.1mm 안쪽)"""
    box = ctx.V['projected_box']
    tb = (box[0] + 0.1, box[1] + 0.05, box[2] - 0.1, box[3] - 0.05)
    X0, Y0 = R.to_plan((box[0] + box[2]) / 2, (box[1] + box[3]) / 2 + 6.0)
    root = G.new_root('SUB_Vesuvius_root', GC, X0, Y0, 0.0)
    root.rotation_euler = (0.0, 0.0, math.radians(45.0))      # 지역 x = 화면 오른쪽, 지역 +y = 뒤(먼 쪽)
    M = ves_mats()
    ts, n = VES_TS, VES_N
    Ly = Lay('Vesuvius', root, GC)
    b0 = Ly(0, 'Cone', [M['vine'], M['wood'], M['scrub'], M['ash']])

    def band(k, j):
        t = ts[min(j, len(ts) - 2)]
        return 0 if t > 0.72 else (1 if t > 0.48 else (2 if t > VES_TT + 0.01 else 3))
    lathe(b0, 0.0, 0.0, [(VES_RB * t, 0.0) for t in ts], n=n, mi_fn=band,
          rj=lambda k, j: _ves_r(2 * math.pi * k / n) * (1.0 + (0.012 * _j(5, k, j) if 0 < j < len(ts) - 2 else 0.0)),
          zj=lambda k, j: _ves_z(ts[j], 2 * math.pi * k / n) + (0.15 * _j(6, k, j) if 0 < j < len(ts) - 3 else 0.0))
    cone = Ly.finish()
    G.fit_to_box(root, tb)
    for _ in range(2):
        bb = kids_bbox(root)
        yc = R.scr(root.matrix_world.translation)[1]
        up = yc - bb[1]
        want = (tb[3] - tb[1]) - (bb[3] - yc)
        root.scale.z *= want / max(1e-6, up)
        bpy.context.view_layer.update()
        bb = kids_bbox(root)
        d = tb[3] - bb[3]                                       # 평면 (d, d) = 화면 곧장 아래로
        root.location.x += d
        root.location.y -= d
        bpy.context.view_layer.update()
    return root, cone


def build_vesuvius_layers(GC, root, cone):
    """사면 위 레이어(광선으로 겉면 높이를 잰다): L1 골·정상 구멍 · L2 계단 담·길 · L3 포도 줄 · L4 바위·용암 혹 · L5 밝은 결 · L6 나무 점"""
    M = ves_mats()
    RB = VES_RB
    Ly = Lay('Vesuvius', root, GC)

    def P(t, a, dz=0.08):
        rr = RB * t * _ves_r(a)
        x, y = rr * math.cos(a), rr * math.sin(a)
        z = ray_z(cone, x, y)
        return (x, y, (z if z is not None else _ves_z(t, a)) + dz)

    def run(pts):
        out, cur = [], []
        for p in pts:
            if p is None:
                if len(cur) >= 2:
                    out.append(cur)
                cur = []
            else:
                cur.append(p)
        if len(cur) >= 2:
            out.append(cur)
        return out
    vis = [math.radians(d) for d in range(196, 346, 1)]           # 보이는 앞 반쪽(지역 −y 쪽)
    b1 = Ly(1, 'Gullies', [M['gully'], M['pit']])
    for kq, a in enumerate(GULLY_A):
        if not (math.radians(198) <= a <= math.radians(344)):
            continue
        for seg in run([P(t, a + 0.02 * math.sin(9 * t + kq), 0.1) for t in [0.3 + 0.04 * i for i in range(14)]]):
            ribbon(b1, seg, 0.35, 0.3, 0, w1=0.85)
    for (t, d, r) in ((0.10, 250, 0.9), (0.15, 300, 0.7), (0.06, 20, 0.6), (0.17, 215, 0.55)):
        q = P(t, math.radians(d), 0.04)
        lathe(b1, q[0], q[1], [(r, q[2] - 0.05), (r * 0.8, q[2] + 0.02), (0.0, q[2] + 0.03)], n=10, mi=1)
    b2 = Ly(2, 'Terraces', [M['wall'], M['path']])
    for t in (0.92, 0.84, 0.76):
        for seg in run([P(t, a, 0.12) for a in vis[::3]]):
            ribbon(b2, seg, 0.42, 0.3, 0)
    zig = [(0.985, 300), (0.86, 284), (0.74, 306), (0.62, 287), (0.5, 303), (0.4, 290), (0.31, 298), (VES_TT, 294)]
    pts = []
    for (t0, d0), (t1, d1) in zip(zig[:-1], zig[1:]):
        for i in range(6):
            f = i / 6.0
            pts.append(P(t0 + (t1 - t0) * f, math.radians(d0 + (d1 - d0) * f), 0.13))
    for seg in run(pts):
        ribbon(b2, seg, 0.45, 0.3, 1)
    b3 = Ly(3, 'Vines', [M['vrow'], M['vrow2']]) if DECOR else Ly(3, 'AshBands', [M['ash'], M['scrub']])   # 17:32: 포도밭 0 → 같은 줄을 화산재 띠로
    for i, t in enumerate((0.965, 0.945, 0.895, 0.875, 0.82, 0.80, 0.70, 0.68, 0.60)):
        d = 197 + 3 * (i % 2)
        while d < 343:
            for seg in run([P(t, math.radians(d + q), 0.12) for q in (0.0, 1.4, 2.8)]):
                ribbon(b3, seg, 0.32, 0.3, i % 2)
            d += 4.2
    b4 = Ly(4, 'Rocks', [M['rock'], M['scrub']])
    for i in range(11):
        q = P(VES_TT * (0.85 + 0.25 * _h(i, 2.2)), math.radians(190 + 165 * _h(i, 2.1)), 0.0)
        blob(b4, (q[0], q[1], q[2] + 0.1), 0.55 + 0.4 * _h(i, 2.3), 0.5, 0.45, 5, 3, 0.35, i + 0.5, 0)
    for kq, a in enumerate(RIDGE_A):
        if not (math.radians(200) <= a <= math.radians(342)):
            continue
        for t in (0.42, 0.52):
            blob(b4, P(t, a, 0.0), 1.1, 0.8, 0.45, 7, 3, 0.25, kq + t, 1)
    b5 = Ly(5, 'Light', [M['hi_ash'], M['hi']])
    for seg in run([P(VES_TT * 0.98, a, 0.1) for a in vis[::2]]):
        ribbon(b5, seg, 0.38, 0.25, 0)
    for kq, a in enumerate(RIDGE_A):
        if not (math.radians(196) <= a <= math.radians(268)):
            continue
        for seg in run([P(t, a, 0.12) for t in [0.3 + 0.05 * i for i in range(9)]]):
            ribbon(b5, seg, 0.5, 0.25, 1, w1=0.2)
    b6 = Ly(6, 'Trees', [M['tree'], M['tree2']]) if DECOR else Ly(6, 'Scrub', [M['scrub'], M['ash']])     # 17:32: 나무 소품 0 → 관목 점
    for i in range(52):
        q = P(0.46 + 0.46 * _h(i, 3.2), math.radians(196 + 150 * _h(i, 3.1)), 0.0)
        if i % 5 == 0:
            blob(b6, (q[0], q[1], q[2] + 0.6), 0.28, 0.28, 0.75, 5, 3, 0.1, i, 1)
        else:
            blob(b6, (q[0], q[1], q[2] + 0.35), 0.6, 0.6, 0.42, 6, 3, 0.2, i, 0)
    Ly.finish()
    bb = kids_bbox(root)
    REPORT['Vesuvius'] = dict(scale=[round(root.scale.x, 4), round(root.scale.z, 4)], bbox=[round(v, 2) for v in bb],
                              area=round((bb[2] - bb[0]) * (bb[3] - bb[1]), 1))
    return root


def ves_base(ves):
    """밑동 고리(z=0): 화면 점 목록(앞 반쪽 아래 윤곽 함수 yb(x)) + 평면 극좌표(중심 C, ρ(θ) 보간)"""
    bpy.context.view_layer.update()
    mw = ves.matrix_world
    C = (mw.translation.x, -mw.translation.y)
    scr, pol = [], []
    n = VES_N
    for k in range(n):
        a = 2 * math.pi * k / n
        rr = VES_RB * _ves_r(a)
        p = mw @ Vector((rr * math.cos(a), rr * math.sin(a), 0.0))
        scr.append(R.scr(p))
        pol.append((math.degrees(math.atan2(-p.y - C[1], p.x - C[0])) % 360.0, math.hypot(p.x - C[0], -p.y - C[1])))
    pol.sort()

    def rho(th):
        th %= 360.0
        m = len(pol)
        for i in range(m):
            t0, r0 = pol[i]
            t1, r1 = pol[(i + 1) % m]
            if i == m - 1:
                t1 += 360.0
            tt = th if th >= t0 else th + 360.0
            if t0 <= tt <= t1:
                return r0 + (r1 - r0) * (tt - t0) / max(1e-9, t1 - t0)
        return pol[0][1]

    def yb(x):
        best = None
        for i in range(n):
            (x1, y1), (x2, y2) = scr[i], scr[(i + 1) % n]
            if (x1 - x) * (x2 - x) <= 0 and abs(x1 - x2) > 1e-9:
                y = y1 + (y2 - y1) * (x - x1) / (x2 - x1)
                best = y if best is None else max(best, y)
        return best
    return C, rho, yb, scr


# ───────────────────────── 5b. 먼 둔덕(베수비오 뒤 양 옆, 빈 땅을 메우는 낮은 언덕 — 화산 아님) ─────────────────────────
def terr_levels(m):
    """계단 둔덕의 층별 윤곽(Blender xy)과 높이. 채석장 둔덕은 카메라 쪽을 곧은 단면으로 자른다(cut=True인 변)"""
    X, Y, R0, h, e, rot, seed, nl = m['X'], m['Y'], m['R'], m['h'], m['e'], m['rot'], m['seed'], m['nl']
    cr, sr = math.cos(rot), math.sin(rot)
    z00 = m.get('z0', 0.0)
    out = []
    for k in range(nl):
        f = 1.0 - (0.62 / max(1, nl)) * k
        rlev = R0 * f
        pts, cut = [], []
        for i in range(20):
            a = 2 * math.pi * i / 20
            rr = rlev * (1.0 + 0.09 * _j(seed, k, i) + 0.05 * math.sin(3 * a + seed))
            dx, dy = rr * math.cos(a) * e, rr * math.sin(a)
            bx, by = cr * dx - sr * dy, sr * dx + cr * dy
            c_ = bx * CAM_U[0] + by * CAM_U[1]
            cc = False
            if m.get('quarry') and c_ > rlev * 0.5:
                bx, by = bx - (c_ - rlev * 0.5) * CAM_U[0], by - (c_ - rlev * 0.5) * CAM_U[1]
                cc = True
            pts.append((X + bx, -Y + by))
            cut.append(cc)
        out.append((pts, z00 + h * k / nl, z00 + h * (k + 1) / nl, k, cut))
    return out


CAM_U = (math.cos(math.radians(-45.0)), math.sin(math.radians(-45.0)))   # Blender xy에서 카메라 쪽 수평 방향


def mound_scr(m):
    xs, ys = [], []
    for pts, z0, z1, k, cut in terr_levels(m):
        for (x, y) in pts:
            for z in (z0, z1):
                sx, sy = R.to_screen(x, -y, z)
                xs.append(sx)
                ys.append(sy)
    return (min(xs), min(ys), max(xs), max(ys))


def mound_poly(m):
    """둔덕의 화면 볼록 외곽(아래층 바닥 + 위층 윗면 점)"""
    pts = []
    lv = terr_levels(m)
    for (p, z0, z1, k, cut) in (lv[0], lv[-1]):
        for (x, y) in p:
            pts.append(R.to_screen(x, -y, z0 if k == 0 else z1))
    pts = sorted(set((round(a, 3), round(b, 3)) for a, b in pts))
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


def mound_mesh(Ly, mounds, M, part, mi_of):
    """둔덕 목록 → L0 계단 슬래브(윗층은 조금 밝게) + L2 턱 갓돌 + L3 윗면 결 + L5 윗선"""
    b0 = Ly(0, part, M['hill'] + M['hill_up'] + M['strata'])
    NH = len(M['hill'])
    STRATA = {0: 2 * NH + 2, 1: 2 * NH, 2: 2 * NH + 1}
    for m in mounds:
        base = mi_of(m)
        for pts, z0, z1, k, cut in terr_levels(m):
            top = base + (NH if (k == m['nl'] - 1 and m['nl'] > 1) or m.get('quiet') else 0)
            zz0 = z0 - (0.02 if k == 0 else 0.0)
            if m.get('quarry'):
                slab(b0, pts, zz0, z1, top, base, side_fn=lambda i, cut=cut, k=k, base=base: STRATA[min(k, 2)] if (cut[i] and cut[(i + 1) % len(cut)]) else base)
            else:
                slab(b0, pts, zz0, z1, top, base)


def build_far_fields(GC, ctx, ves):
    """베수비오 뒤쪽 반을 감싸는 낮은 먼 들(z 0.25, 대기 원근 50%): 지도 무대 위 변(y ≥ 93.8, D12)·라벨 블록 +1.5 밖까지.
    봉우리·둔덕이 아니라 평지 밭(화산은 1개뿐). L0 들판 · L1 밭고랑 그늘 · L2 산울타리 · L3 포도 줄 · L4 돌무더기 · L5 바깥 변 윗선 · L6 올리브"""
    C, rho, yb, scr = ves_base(ves)
    lab = ctx.label_block('베수비오')
    root = G.new_root('SUB_FarFields_root', GC, 0.0, 0.0, 0.0)
    A = 0.5
    M = dict(field=mat('ff_field', '#A9AA70', A), field2=mat('ff_field2', '#B9B07C', A), shade=mat('ff_shade', '#7A8650', A),
             hedge=mat('ff_hedge', '#6F7F45', A), vrow=mat('ff_vrow', '#6C8547', A), vrow2=mat('ff_vrow2', '#7D9350', A),
             stone=mat('ff_stone', '#CDBB93', A), hi=mat('ff_hi', hi_of('#B9B07C', 1.13), A))

    def PP(th, r):
        t = math.radians(th)
        return (C[0] + r * math.cos(t), C[1] + r * math.sin(t))
    ths = [134.0 + 2.0 * i for i in range(92)]
    secs = []
    for th in ths:
        rb = rho(th)
        r = rb + 0.6
        while r < rb + 26.0:
            X, Y = PP(th, r + 0.4)
            sx, sy = R.to_screen(X, Y, 0.3)
            if sy < 93.8 or sx > 424.0 or (lab and pt_poly_d((sx, sy), lab) < 1.6):
                break
            r += 0.4
        if r - rb > 1.4:
            secs.append((th, rb, r))
    Ly = Lay('FarFields', root, GC)
    runs, cur = [], []
    for i, s in enumerate(secs):
        if cur and abs(s[0] - cur[-1][0] - 2.0) > 1e-6:
            runs.append(cur)
            cur = []
        cur.append(s)
    if cur:
        runs.append(cur)
    b0 = Ly(0, 'Field', [M['field'], M['field2']])
    b1 = Ly(1, 'Furrows', [M['shade']])
    b2 = Ly(2, 'Hedges', [M['hedge']])
    b3 = Ly(3, 'Vines', [M['vrow'], M['vrow2']])
    b4 = Ly(4, 'Stones', [M['stone']])
    b5 = Ly(5, 'Light', [M['hi']])
    T = Trees(Ly, A, 'Tree')
    nrow = nt = 0
    for run_ in runs:
        if len(run_) < 2:
            continue
        inner = [(lambda p: (p[0], -p[1]))(PP(th, rb + 0.15)) for th, rb, ro in run_]
        outer = [(lambda p: (p[0], -p[1]))(PP(th, ro)) for th, rb, ro in run_]
        arc_slab(b0, inner, outer, -0.02, 0.25, 0, 1)
        for k in range(16):                                           # 호를 따르는 밭 줄: 포도 3줄 + 고랑 그늘 1 + 산울타리(4줄마다)
            pts = []
            for th, rb, ro in run_:
                r = rb + 1.0 + 1.25 * k
                if r > ro - 0.5:
                    if len(pts) >= 2:
                        (ribbon(b2, pts, 0.32, 0.3, 0) if k % 4 == 3 else ribbon(b1, [(p[0], p[1], 0.27) for p in pts], 0.4, 0.03, 0) if k % 4 == 2 else ribbon(b3, pts, 0.28, 0.14, k % 2))
                        nrow += 1
                    pts = []
                    continue
                X, Y = PP(th, r)
                pts.append((X, -Y, 0.38 if k % 4 != 3 else 0.55))
            if len(pts) >= 2:
                (ribbon(b2, pts, 0.32, 0.3, 0) if k % 4 == 3 else ribbon(b1, [(p[0], p[1], 0.27) for p in pts], 0.4, 0.03, 0) if k % 4 == 2 else ribbon(b3, pts, 0.28, 0.14, k % 2))
                nrow += 1
        ribbon(b5, [(p[0], p[1], 0.255) for p in outer], 0.18, 0.02, 0)
        for j, (th, rb, ro) in enumerate(run_[::7]):
            if ro - rb < 6.0:
                continue
            X, Y = PP(th, rb + (ro - rb) * (0.45 + 0.3 * _h(j, th)))
            blob(b4, (X, -Y, 0.25), 0.35, 0.3, 0.2, 5, 2, 0.3, j + th, 0, zmin=0.25)
            if _h(j, th, 2.0) < 0.55:
                X2, Y2 = PP(th + 2.0, rb + (ro - rb) * 0.7)
                q = tree_scr(X2, Y2, 0.25, crown_r('o', H_FAR * K_OLIVE * 0.8), H_FAR * K_OLIVE * 0.8)
                if min(p[1] for p in q) > 93.8 and not (lab and poly_dist(q, lab) < 1.5):
                    T.put('o', X2, -Y2, 0.25, H_FAR * K_OLIVE * 0.8, j + th * 0.1)
                    nt += 1
    Ly.finish()
    REPORT['FarFields'] = dict(runs=len(runs), sections=len(secs), rows=nrow, trees=nt, bbox=[round(v, 1) for v in kids_bbox(root)] if secs else None)
    return root


def build_far_hills(GC, ctx, ves):
    """(b5에서 쓰지 않음: 정상 높이의 계단 둔덕이 봉우리처럼 읽혀 build_far_fields로 바꿨다)"""
    C, rho, yb, scr = ves_base(ves)
    lab = ctx.label_block('베수비오')
    box = ctx.V['projected_box']
    root = G.new_root('SUB_FarHills_root', GC, 0.0, 0.0, 0.0)
    A = 0.48
    M = dict(hill=[mat('fh%d' % i, c, A) for i, c in enumerate(('#97A064', '#A3A56C', '#8E9A5E'))],
             hill_up=[mat('fhU%d' % i, hexmix(c, '#D2D49A', 0.22), A) for i, c in enumerate(('#97A064', '#A3A56C', '#8E9A5E'))],
             strata=[mat('fh_s%d' % i, c, A) for i, c in enumerate(('#9C5B42', '#C2A276', '#A8957A'))],
             shade=mat('fh_shade', '#6E7B4A', A), cap=mat('fh_cap', '#CDBB93', A), vrow=mat('fh_vrow', '#6C8547', A),
             grove=mat('fh_grove', '#7C8C55', A), hi=mat('fh_hi', hi_of('#A3A56C', 1.13), A), rock=mat('fh_rock', '#9A8C7A', A))
    mounds = []
    for (th, R0, h, nl, e) in ((202.0, 5.4, 2.6, 2, 1.25), (214.0, 4.6, 2.0, 2, 1.1), (-82.0, 5.2, 2.8, 2, 1.2), (-100.0, 4.8, 2.2, 2, 1.15), (-64.0, 5.0, 2.4, 2, 1.2)):
        t = math.radians(th)
        rr = rho(th) + R0 * e + 0.8
        X, Y = C[0] + rr * math.cos(t), C[1] + rr * math.sin(t)
        m = dict(X=X, Y=Y, R=R0, h=h, e=e, rot=math.radians(th), seed=th * 0.13, nl=nl, hue=int(abs(th)) % 3)
        sb = mound_scr(m)
        if sb[1] < 93.5 or sb[0] > 423.0:
            continue
        if lab and poly_dist(mound_poly(m), lab) < 1.5:
            continue
        mounds.append(m)
    Ly = Lay('FarHills', root, GC)
    mound_mesh(Ly, mounds, M, 'Hills', lambda m: m['hue'])
    hills = Ly.finish()
    Ly = Lay('FarHills', root, GC)
    b1 = Ly(1, 'Shade', [M['shade']])
    b2 = Ly(2, 'Terraces', [M['cap']])
    b3 = Ly(3, 'Fields', [M['vrow'], M['grove']])
    b4 = Ly(4, 'Rocks', [M['rock']])
    b5 = Ly(5, 'Light', [M['hi']])
    T = Trees(Ly, A, 'Tree')
    for i, m in enumerate(mounds):
        lv = terr_levels(m)
        for pts, z0, z1, k, cut in lv:
            n = len(pts)
            cx = sum(p[0] for p in pts) / n
            cy = sum(p[1] for p in pts) / n
            for j in range(n):
                a, b = pts[j], pts[(j + 1) % n]
                d = ((a[0] + b[0]) / 2 - cx) * CAM_U[0] + ((a[1] + b[1]) / 2 - cy) * CAM_U[1]
                if d <= 0.0:
                    continue
                ribbon(b2, [(a[0], a[1], z1 + 0.02), (b[0], b[1], z1 + 0.02)], 0.2, 0.1, 0)        # 턱 갓돌(보이는 앞쪽)
                ribbon(b1, [(a[0], a[1], z0 + 0.05), (b[0], b[1], z0 + 0.05)], 0.12, 0.05, 0) if k > 0 else None
        pts, z0, z1, k, cut = lv[-1]
        n = len(pts)
        cx = sum(p[0] for p in pts) / n
        cy = sum(p[1] for p in pts) / n
        r = min(math.hypot(p[0] - cx, p[1] - cy) for p in pts)
        for q in range(-2, 3):
            off = q * r * 0.3
            L_ = math.sqrt(max(0.0, (r * 0.8) ** 2 - off ** 2))
            if L_ > 0.5:
                ribbon(b3, [(cx - L_, cy + off, z1 + 0.08), (cx + L_, cy + off, z1 + 0.08)], 0.26, 0.1, 0)
        for j in range(n):
            a, b = pts[j], pts[(j + 1) % n]
            ang = math.degrees(math.atan2((a[1] + b[1]) / 2 - cy, (a[0] + b[0]) / 2 - cx))
            if -150.0 <= ang <= -60.0:
                ribbon(b5, [(a[0], a[1], z1 + 0.015), (b[0], b[1], z1 + 0.015)], 0.18, 0.05, 0)
        blob(b4, (cx + 0.4 * r, cy - 0.2 * r, z1), 0.5, 0.4, 0.3, 5, 2, 0.3, i + 0.7, 0)
        T.put('o', cx - 0.3 * r, cy + 0.2 * r, z1, H_FAR * K_OLIVE * 0.8, i + 3.3)
    Ly.finish()
    REPORT['FarHills'] = dict(mounds=len(mounds), bbox=[round(v, 1) for v in kids_bbox(root)] if mounds else None)
    return root


# ───────────────────────── 6. 알바노 구릉 띠(낮은 구릉 지면 결, 화산 그림이 아니다) ─────────────────────────
RIDGE_TH = (-56.0, 134.0)              # 앞 능선이 감싸는 평면 방위(베수비오 중심 기준, 도). 45° = 카메라 쪽
FARM_TH = (16.0, 84.0)                 # 농장이 얹히는 능선 구간(윗면 평평)
FARM_C_TH = 62.0                       # 농장 집채 자리
RIDGE_ZF = 4.2                         # 농장 구간 능선 윗면
RIDGE_GAP = 0.3                        # 산 밑동과 능선 안쪽 변 사이(평면). 양 끝(밑동 윤곽이 세로로 서는 곳)은 0.1


def ridge_gap(th):
    """능선 안쪽 변과 밑동 사이. 왼쪽 끝(θ 116~134°: 밑동 윤곽이 화면에서 세로로 서는 곳)은 밑동 안 0.25까지 넣어
    세로 윤곽 기둥을 덮는다(안쪽 면은 카메라에서 등을 돌린 면이라 보이지 않는다). 오른쪽 끝은 0.1"""
    return RIDGE_GAP - 0.55 * smooth(114.0, 122.0, th) - 0.2 * bump(th, -46.0, 16.0)


def ridge_spec(th):
    """앞 능선 단면: 위층 높이 zU·폭 wU, 아래층 높이 zL·폭 wL(평면 mm, 밑동에서 바깥으로).
    덮개(D3·spec ridge) 3~5mm: 가운데 약 4.0, 밑동 윤곽이 세로로 서는 양 끝(θ ≈ 130°, −40°)은 위층을 0.5~0.6 높인다"""
    t = math.radians(th)
    zU = 4.15 + 0.22 * math.sin(3 * t + 0.4) + 0.12 * math.sin(7 * t + 1.1)
    zU += 0.6 * bump(th, -40.0, 18.0) + 0.5 * bump(th, 127.0, 9.0)
    zL = 2.0 + 0.18 * math.sin(5 * t + 0.3)
    wU = 4.4 + 4.6 * bump(th, 50.0, 48.0)
    wL = wU + 4.2 + 1.0 * math.sin(4 * t + 0.9)
    f = smooth(FARM_TH[0] - 8.0, FARM_TH[0], th) * (1.0 - smooth(FARM_TH[1], FARM_TH[1] + 8.0, th))
    zU = zU * (1 - f) + RIDGE_ZF * f
    e = smooth(130.5, RIDGE_TH[1], th)                       # 왼쪽 끝: 짧게 낮아지고 좁아진다(베수비오 라벨 블록 밑)
    zU = zU * (1 - e) + 2.2 * e
    zL = min(zL * (1 - e) + 1.0 * e, zU - 0.5)
    wn = 1.0 - 0.75 * smooth(122.0, 131.0, th)               # 라벨 블록 쪽으로 좁힌다
    wU = wU * wn
    wL = wU + (wL - wU) * (1 - 0.75 * smooth(122.0, 132.0, th))
    return zU, zL, wU, wL


def alb_mats():
    M = {}
    rows = (0.40, 0.36, 0.32, 0.28)                        # 대기 원근(앞 능선 → 들): D9 알바노 26~46%
    hues = ('#8F9B5C', '#A0A668', '#879659')
    M['hill'] = [mat('alb%d_%d' % (r, h), c, a) for r, a in enumerate(rows) for h, c in enumerate(hues)]
    M['hill_up'] = [mat('albU%d_%d' % (r, h), hexmix(c, '#D2D49A', 0.22), a) for r, a in enumerate(rows) for h, c in enumerate(hues)]
    M['strata'] = [mat('alb_pozz', '#9C5B42', 0.2), mat('alb_ashl', '#C2A276', 0.2), mat('alb_tuff', '#A8957A', 0.2)]
    a = 0.34
    M['ridge_top'] = mat('alb_rtop', '#93A05F', a)
    M['ridge_top2'] = mat('alb_rtop2', '#A6AC6C', a)
    M['ridge_side'] = mat('alb_rside', '#7C8A50', a)
    M['ridge_side2'] = mat('alb_rside2', '#8C8D58', a)
    M['shade'] = mat('alb_shade', '#5E6B3E', a)
    M['cap'] = mat('alb_cap', '#CDBB93', a)
    M['path'] = mat('alb_path', '#D5C29B', 0.3)
    M['vrow'] = mat('alb_vrow', '#647F41', a)
    M['vrow2'] = mat('alb_vrow2', '#728C48', 0.3)
    M['furrow'] = mat('alb_furrow', '#B3966C', 0.3)
    M['grove'] = mat('alb_grove', '#7C8C55', 0.3)
    M['plain'] = mat('alb_plain', '#B3B07C', 0.3)
    M['parcels'] = [mat('alb_pc%d' % i, c, 0.3) for i, c in enumerate(('#A5AC6B', '#BBAF7F', '#93A05C', '#C9BC8A', '#AFA36F'))]
    M['quiet'] = [mat('alb_q%d' % i, c, 0.36) for i, c in enumerate(('#BDB887', '#C4BA8D', '#B6B482'))]
    M['hedge'] = mat('alb_hedge', '#6F7F45', 0.3)
    M['pozz'] = mat('alb_pozz2', '#9C5B42', 0.16)
    M['ashl'] = mat('alb_ashl2', '#C2A276', 0.16)
    M['tuff'] = mat('alb_tuff2', '#A8957A', 0.16)
    M['qfloor'] = mat('alb_qfloor', '#C9B08A', 0.16)
    M['qdeep'] = mat('alb_qdeep', '#6E4A36', 0.16)
    M['hi'] = mat('alb_hi', hi_of('#A0A668', 1.13), a)
    M['hi2'] = mat('alb_hi2', hi_of('#B3B07C', 1.12), 0.3)
    M['sheep'] = mat('alb_sheep', '#F1EBDD', 0.15)
    return M


def build_albani(GC, ctx, ves):
    """알바노 구릉 띠: ① 베수비오 밑동 앞쪽을 감싸는 앞 능선(덮개 3~5mm, x 360~418 연속, 농장 구간은 평평한 계단 윗면)
    ② 능선 앞 들(수도교 뒤까지, COLLI ALBANI 바닥 글 블록 +1.5mm 안은 높이 ≤ 1mm) ③ 왼쪽 낮은 둔덕(라벨 블록 밑) ④ 오른쪽 포촐라나 채석장"""
    C, rho, yb, scr = ves_base(ves)
    band = next(t for t in ctx.CM['terrain'] if t['name'].startswith('알바노'))['box']
    rc = next(t for t in ctx.CM['terrain'] if t['name'].startswith('알바노')).get('ridge', {})
    cov_rng = rc.get('cover_vesuvius_base_mm', [3.0, 5.0])
    cov_x = rc.get('cover_x_range', [ctx.V['projected_box'][0], ctx.V['projected_box'][2]])
    vlab = ctx.label_block('베수비오')
    texts = ctx.floor_blocks(('COLLI ALBANI', '알바노 구릉'))
    baths = ctx.lm['L3']['projected_box']
    baths_poly = rbox((baths[0] - 2.0, baths[1] - 2.0, baths[2] + 2.0, baths[3] + 2.0))
    x_left = baths[2] + 2.0
    Yb = ctx.aq_back_Y()
    root = G.new_root('SUB_Albani_root', GC, 0.0, 0.0, 0.0)
    M = alb_mats()

    def U(th):
        t = math.radians(th)
        return math.cos(t), math.sin(t)

    def PP(th, r):                                            # 평면 극좌표 → 평면 (X, Y)
        c, s = U(th)
        return (C[0] + r * c, C[1] + r * s)

    def keep_out(poly_s, tall):
        if vlab and poly_dist(poly_s, vlab) < 1.5:
            return True
        if poly_dist(poly_s, baths_poly) < 0.0 + 1e-9:
            return True
        if tall and any(poly_dist(poly_s, t) < 1.5 for t in texts):
            return True
        return False
    # ① 앞 능선 단면 표본
    ths = [RIDGE_TH[0] + 2.0 * i for i in range(int((RIDGE_TH[1] - RIDGE_TH[0]) / 2.0) + 1)]
    secs = []
    for th in ths:
        zU, zL, wU, wL = ridge_spec(th)
        rb = rho(th)
        gp = ridge_gap(th)
        for _ in range(40):                                   # 비움 영역(라벨·바닥 글·욕장)에 걸리면 폭을 줄인다
            Xo, Yo = PP(th, rb + wL)
            Xi, Yi = PP(th, rb + gp)
            ps = [R.to_screen(Xi, Yi, zL), R.to_screen(Xo, Yo, zL), R.to_screen(Xo, Yo, 0.0), R.to_screen(Xi, Yi, 0.0)]
            if not keep_out(ps, zL > 1.0) or wL <= wU + 1.0:
                break
            wL -= 0.4
        for _ in range(60):                                   # 위층: 폭을 줄이고, 그래도 걸리면 높이를 낮춘다
            Xo, Yo = PP(th, rb + wU)
            Xi, Yi = PP(th, rb + gp)
            ps = [R.to_screen(Xi, Yi, zU), R.to_screen(Xo, Yo, zU), R.to_screen(Xo, Yo, zL), R.to_screen(Xi, Yi, zL)]
            if not keep_out(ps, True):
                break
            if wU > 0.9:
                wU -= 0.3
                wL = max(wL, wU + 1.0)
            elif zU > 2.6:
                zU -= 0.15
                zL = min(zL, zU - 0.5)
            else:
                break
        secs.append(dict(th=th, rb=rb, zU=zU, zL=zL, wU=wU, wL=wL, gap=gp))
    Ly = Lay('Albani', root, GC)
    bL = Ly(0, 'RidgeLow', [M['ridge_top2'], M['ridge_side2']])
    bU = Ly(0, 'RidgeHigh', [M['ridge_top'], M['ridge_side']])

    def bl(X, Y):
        return (X, -Y)
    inner = [bl(*PP(s['th'], s['rb'] + s['gap'])) for s in secs]
    outL = [bl(*PP(s['th'], s['rb'] + s['wL'])) for s in secs]
    outU = [bl(*PP(s['th'], s['rb'] + s['wU'])) for s in secs]
    arc_slab(bL, inner, outL, -0.02, [s['zL'] for s in secs], 0, 1)
    arc_slab(bU, inner, outU, [s['zL'] - 0.01 for s in secs], [s['zU'] for s in secs], 0, 1)
    # ② 능선 앞 들: 뒤 변 = 라벨 블록 밑선(왼쪽) → 능선 아래층 바깥 변(0.6 안쪽), 앞 변 = 수도교 뒤 평면 Y
    back = []
    lab_lo = None
    if vlab:
        pv = sorted(vlab, key=lambda p: (p[0], -p[1]))
        lab_lo = (pv[0], max(vlab, key=lambda p: (p[0], p[1])))      # 블록 왼쪽 아래 · 오른쪽 아래 꼭짓점
    xr0 = R.to_screen(*PP(secs[-1]['th'], secs[-1]['rb'] + secs[-1]['wL']))[0]

    def y_label_low(x):
        if not lab_lo:
            return band[1]
        (x0, y0), (x1, y1) = lab_lo
        return (y0 + (y1 - y0) * (x - x0) / max(1e-6, x1 - x0)) + 1.5 + 0.6
    x = x_left + 0.2
    while x < xr0 - 0.3:
        back.append(R.to_plan(x, y_label_low(x)))
        x += 2.0
    for s in reversed(secs):
        X, Y = PP(s['th'], s['rb'] + s['wL'] - 0.6)
        if R.to_screen(X, Y)[0] > 424.0:
            break
        back.append((X, Y))
    xe = R.to_screen(*back[-1])[0]
    back.append(R.to_plan(424.0, R.to_screen(*back[-1])[1]))
    front = [(X, Yb) for X in (R.to_plan(424.0, 0.57735 * 424.0 + Yb)[0], R.to_plan(x_left + 0.2, 0.57735 * (x_left + 0.2) + Yb)[0])]
    plain = back + front
    if DECOR:                                                        # 17:32: 먼 들 0 → 들 바탕 판도 짓지 않는다(능선·둔덕만 땅 위에)
        bP = Ly(0, 'Plain', [M['plain']])
        slab(bP, [bl(X, Y) for X, Y in plain], -0.02, 0.30, 0)
    ridge_obs = Ly.finish()

    def in_plain(X, Y):
        return _pip(X, Y, plain)

    def under_ridge(X, Y, pad=0.0):
        th = math.degrees(math.atan2(Y - C[1], X - C[0]))
        if not (RIDGE_TH[0] <= th <= RIDGE_TH[1]):
            return math.hypot(X - C[0], Y - C[1]) < rho(th) + pad
        sp = ridge_spec(th)
        return math.hypot(X - C[0], Y - C[1]) < rho(th) + sp[3] + pad

    def in_text(poly_s, m=1.5):
        return any(poly_dist(poly_s, t) < m for t in texts)
    # ③ 왼쪽 낮은 둔덕(라벨 블록 밑·수도교 뒤) · ④ 채석장
    mounds = []

    def add(x, y, R0, h, row, nl, quarry=False, e=1.15):
        X, Y = R.to_plan(x, y)
        m = dict(X=X, Y=Y, R=R0, h=h, row=row, e=e, rot=math.pi * _h(x, y, 2.2), seed=x * 0.37 + y * 0.11, nl=nl,
                 hue=int(3 * _h(x, y, 3.3)) % 3, quarry=quarry, z0=0.28)
        poly_s = mound_poly(m)
        if vlab and poly_dist(poly_s, vlab) < 1.5:
            return None
        if poly_dist(poly_s, baths_poly) < 0.3:
            return None
        if in_text(poly_s):
            return None
        if Y + R0 * e * 1.15 > Yb:
            return None
        if any(under_ridge(X + dx, Y + dy, 0.4) for dx, dy in ((0, 0), (R0 * e, 0), (-R0 * e, 0), (0, R0 * e), (0, -R0 * e))):
            return None
        if any(math.hypot(X - o['X'], Y - o['Y']) < (R0 + o['R']) * 0.9 for o in mounds):
            return None
        mounds.append(m)
        return m
    for (x, y, R0, h, nl) in ((x_left + 5.5, 133.5, 4.2, 2.2, 2), (x_left + 12.0, 128.0, 4.0, 2.6, 2), (x_left + 9.0, 139.0, 4.6, 1.8, 2),
                              (x_left + 17.5, 136.0, 3.8, 2.0, 2), (x_left + 3.0, 141.0, 3.6, 1.6, 2), (x_left + 15.0, 143.5, 4.0, 1.4, 2)):
        add(x, y, R0, h, 2, nl)
    qx = band[2] - 6.5
    qm = add(qx, 150.0, 6.0, 3.4, 3, 3, True, 1.1) or add(qx, 147.0, 5.6, 3.2, 3, 3, True, 1.1)
    Ly = Lay('Albani', root, GC)
    mound_mesh(Ly, mounds, M, 'Hills', lambda m: 3 * min(m['row'], 3) + m['hue'])
    ridge_obs += Ly.finish()
    # ── 레이어(능선·들·둔덕 위) ──
    Ly = Lay('Albani', root, GC)
    # L1 깊이색: 위층 앞면 밑(아래층 윗면 위) 그늘 띠 · 능선 앞면 골짜기 홈 · 채석장 속
    b1 = Ly(1, 'Shade', [M['shade'], M['qdeep']])
    for i in range(len(secs) - 1):
        s0, s1 = secs[i], secs[i + 1]
        if not (FARM_TH[0] <= s0['th'] <= FARM_TH[1]):
            pa = PP(s0['th'], s0['rb'] + s0['wU'] + 0.18)
            pb = PP(s1['th'], s1['rb'] + s1['wU'] + 0.18)
            ribbon(b1, [(pa[0], -pa[1], s0['zL'] + 0.04), (pb[0], -pb[1], s1['zL'] + 0.04)], 0.36, 0.03, 0)
    for k in range(9):
        th = RIDGE_TH[0] + 18.0 + 20.0 * k + 5.0 * _j(k, 4.4)
        if FARM_TH[0] - 4 < th < FARM_TH[1] + 4 or th > RIDGE_TH[1] - 6:
            continue
        zU, zL, wU, wL = ridge_spec(th)
        rb = rho(th)
        for (r0, r1, z) in ((rb + wU - 0.05, rb + wU + 0.02, zU), (rb + wL - 0.05, rb + wL + 0.02, zL)):
            pa, pb = PP(th - 0.9, r1 + 0.05), PP(th + 0.9, r1 + 0.05)
            fan(b1, [(pa[0], -pa[1], z * 0.15), (pb[0], -pb[1], z * 0.15), (pb[0], -pb[1], z - 0.25), ((pa[0] + pb[0]) / 2, -(pa[1] + pb[1]) / 2, z - 0.05), (pa[0], -pa[1], z - 0.25)], 0)
    # L2 부재: 계단 턱 갓돌(능선 두 층 바깥 윗변) · 흙길(들 → 능선)
    b2 = Ly(2, 'Terraces', [M['cap'], M['path']])
    for key_w, key_z in (('wU', 'zU'), ('wL', 'zL')):
        run_ = []
        for s in secs:
            if key_w == 'wU' and FARM_TH[0] + 2 <= s['th'] <= FARM_TH[1] - 2:
                if len(run_) >= 2:
                    ribbon(b2, run_, 0.22, 0.08, 0)
                run_ = []
                continue
            X, Y = PP(s['th'], s['rb'] + s[key_w] - 0.12)
            run_.append((X, -Y, s[key_z] + 0.02))
        if len(run_) >= 2:
            ribbon(b2, run_, 0.22, 0.08, 0)
    path = []
    for i in range(8):
        th = 104.0 - 3.0 * i
        r = rho(th) + 14.0 - 1.6 * i
        X, Y = PP(th, r)
        z = 0.32 if not under_ridge(X, Y) else (ridge_spec(th)[1] + 0.03 if r > rho(th) + ridge_spec(th)[2] else ridge_spec(th)[0] + 0.03)
        path.append((X, -Y, z))
    ribbon(b2, path, 0.55, 0.06, 1)
    # L3 표면 무늬: 능선 위 포도 줄(농장 구간 밖) · 들 구획(포도·밭고랑·풀; 글 자리는 고요한 구획) · 둔덕 윗면 결
    b3 = Ly(3, 'Fields' if DECOR else 'MoundGrain', [M['vrow'], M['vrow2'], M['furrow'], M['grove'], M['hedge']] + M['parcels'] + M['quiet'])
    NPC = len(M['parcels'])
    for (key_r0, key_r1, key_z, step) in ((('gap', 'wU', 'zU', 1.05), ('wU', 'wL', 'zL', 1.0)) if DECOR else ()):   # 17:32: 능선 포도 줄 0
        for j in range(6):
            rows = []
            for s in secs:
                if FARM_TH[0] - 3 <= s['th'] <= FARM_TH[1] + 3:
                    if len(rows) >= 2:
                        ribbon(b3, rows, 0.3, 0.16, j % 2)
                    rows = []
                    continue
                r0 = s['rb'] + (s['gap'] if key_r0 == 'gap' else s[key_r0]) + 0.55 + step * j
                if r0 > s['rb'] + s[key_r1] - 0.45:
                    if len(rows) >= 2:
                        ribbon(b3, rows, 0.3, 0.16, j % 2)
                    rows = []
                    continue
                X, Y = PP(s['th'], r0)
                rows.append((X, -Y, s[key_z] + 0.14))
            if len(rows) >= 2:
                ribbon(b3, rows, 0.3, 0.16, j % 2)
    # 들 구획: 평면 축 격자(5.5mm) 칸마다 무늬. 글 블록 +1.5 안은 고요한 칸(무늬 없음, 높이 ≤ 0.4)
    gx0 = min(p[0] for p in plain)
    gx1 = max(p[0] for p in plain)
    gy0 = min(p[1] for p in plain)
    gy1 = max(p[1] for p in plain)
    cell = 4.4
    npar = nq = 0
    Xg = gx0 if DECOR else gx1                                       # 17:32: 먼 들 구획 0(들 바탕 L0만)
    while Xg < gx1:
        Yg = gy0
        while Yg < gy1:
            cs = [(Xg + 0.25, Yg + 0.25), (Xg + cell - 0.25, Yg + 0.25), (Xg + cell - 0.25, Yg + cell - 0.25), (Xg + 0.25, Yg + cell - 0.25)]
            if all(in_plain(X, Y) and not under_ridge(X, Y, 0.3) for X, Y in cs) and not any(_pip(cx_, cy_, rect_plan) for rect_plan in [] for cx_, cy_ in cs):
                sp = [R.to_screen(X, Y, 0.3) for X, Y in cs]
                sx_ = sum(p[0] for p in sp) / 4
                sy_ = sum(p[1] for p in sp) / 4
                vis = sy_ < ctx.aq_top_y(sx_) + 6.0 or True
                if not any(math.hypot(X - m['X'], Y - m['Y']) < m['R'] * m['e'] + 0.6 for m in mounds for X, Y in cs):
                    quiet = in_text(sp, 1.5)
                    k = int(NPC * _h(Xg, Yg, 1.7)) % NPC
                    if quiet:
                        pbox(b3, Xg + 0.25, Xg + cell - 0.25, Yg + 0.25, Yg + cell - 0.25, 0.30, 0.34, 5 + NPC + (int(3 * _h(Xg, Yg, 2.9)) % 3))
                        nq += 1
                    else:
                        pbox(b3, Xg + 0.25, Xg + cell - 0.25, Yg + 0.25, Yg + cell - 0.25, 0.30, 0.34, 5 + k)
                        sel = _h(Xg, Yg, 3.1)
                        if sel < 0.4:                              # 포도 줄(평면 X 방향 = 화면 ↘)
                            for q in range(5):
                                yy = Yg + 0.9 + q * (cell - 1.8) / 4
                                ribbon(b3, [(Xg + 0.6, -yy, 0.5), (Xg + cell - 0.6, -yy, 0.5)], 0.26, 0.16, 0)
                        elif sel < 0.65:                           # 밭고랑(평면 Y 방향 = 화면 ↗)
                            for q in range(6):
                                xx = Xg + 0.8 + q * (cell - 1.6) / 5
                                ribbon(b3, [(xx, -(Yg + 0.6), 0.4), (xx, -(Yg + cell - 0.6), 0.4)], 0.22, 0.06, 2)
                        elif sel < 0.85:                           # 올리브 숲 점무늬
                            for q in range(7):
                                blob(b3, (Xg + 0.8 + (cell - 1.6) * _h(Xg, Yg, q, 1.1), -(Yg + 0.8 + (cell - 1.6) * _h(Xg, Yg, q, 1.2)), 0.36),
                                     0.42, 0.42, 0.24, 6, 2, 0.2, Xg + Yg + q, 3)
                        if _h(Xg, Yg, 4.1) < 0.45:                 # 산울타리(앞 변)
                            ribbon(b3, [(Xg + 0.25, -(Yg + cell - 0.25), 0.62), (Xg + cell - 0.25, -(Yg + cell - 0.25), 0.62)], 0.3, 0.3, 4)
                        npar += 1
            Yg += cell
        Xg += cell
    for i, m in enumerate(mounds):                                  # 둔덕 윗면 결
        pts, z0, z1, k, cut = terr_levels(m)[-1]
        n = len(pts)
        cx, cy = sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n
        r = min(math.hypot(p[0] - cx, p[1] - cy) for p in pts)
        if r < 1.3 or m.get('quarry'):
            continue
        for q in range(-3, 4):
            off = q * r * 0.24
            L_ = math.sqrt(max(0.0, (r * 0.8) ** 2 - off ** 2))
            if L_ < 0.6:
                continue
            if i % 2:
                ribbon(b3, [(cx - L_, cy + off, z1 + 0.08), (cx + L_, cy + off, z1 + 0.08)], 0.26, 0.12, 0)
            else:
                ribbon(b3, [(cx + off, cy - L_, z1 + 0.06), (cx + off, cy + L_, z1 + 0.06)], 0.24, 0.1, 2)
    # L4 형태 디테일: 채석장 단면 앞 바닥·흙더미·돌덩이(포촐라나 붉은 갈색·회갈색 재·응회암)
    b4 = Ly(4, 'Quarry', [M['qfloor'], M['pozz'], M['ashl'], M['tuff'], M['qdeep']])
    if qm:
        QX, QY = qm['X'], qm['Y']
        z0q = qm['z0']
        fl = [(QX + CAM_U[0] * qm['R'] * 0.5 + CAM_U[1] * qm['R'] * s_ * 0.9, -QY + CAM_U[1] * qm['R'] * 0.5 - CAM_U[0] * qm['R'] * s_ * 0.9) for s_ in (-1, 1)]
        far = [(x_ + CAM_U[0] * qm['R'] * 0.55, y_ + CAM_U[1] * qm['R'] * 0.55) for x_, y_ in fl[::-1]]
        slab(b4, fl + far, z0q, z0q + 0.06, 0)
        for i in range(7):
            u = qm['R'] * (0.62 + 0.3 * _h(i, 4.2))
            v = qm['R'] * 0.6 * _j(i, 4.1)
            x_, y_ = QX + CAM_U[0] * u + CAM_U[1] * v, -QY + CAM_U[1] * u - CAM_U[0] * v
            blob(b4, (x_, y_, z0q + 0.06), 0.6 + 0.45 * _h(i, 4.3), 0.5, 0.3 + 0.2 * _h(i, 4.4), 7, 3, 0.25, i + 3.3, 1 + i % 3, zmin=z0q + 0.06)
        for k in range(3):                                          # 단면 층 사이 짙은 홈(곡괭이 자국)
            pts, z0, z1, kk, cut = terr_levels(qm)[k]
            seg = [(pts[i][0] + CAM_U[0] * 0.03, pts[i][1] + CAM_U[1] * 0.03, z0 + 0.06) for i in range(len(pts)) if cut[i]]
            if len(seg) >= 2:
                ribbon(b4, seg, 0.08, 0.05, 4)
    # L5 하이라이트: 능선 두 층 바깥 윗선 · 둔덕 윗층 앞 윗선 · 들 구획 앞 변 가는 선
    b5 = Ly(5, 'Light', [M['hi'], M['hi2']])
    for key_w, key_z in (('wU', 'zU'), ('wL', 'zL')):
        run_ = []
        for s in secs:
            X, Y = PP(s['th'], s['rb'] + s[key_w] - 0.02)
            run_.append((X, -Y, s[key_z] + 0.105))
        ribbon(b5, run_, 0.12, 0.04, 0)
    for m in mounds:
        pts, z0, z1, k, cut = terr_levels(m)[-1]
        n = len(pts)
        cx, cy = sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            ang = math.degrees(math.atan2((a[1] + b[1]) / 2 - cy, (a[0] + b[0]) / 2 - cx))
            if -150.0 <= ang <= -60.0 and not (m.get('quarry') and cut[i]):
                ribbon(b5, [(a[0], a[1], z1 + 0.015), (b[0], b[1], z1 + 0.015)], 0.18, 0.06, 0)
    # L6 식생·생활(D8 먼 쪽 키 1.8): 둔덕 위 올리브·우산소나무 · 능선 오른쪽 끝 사이프러스 · 양 떼와 목자 · 채석장 일꾼·짐수레
    T = Trees(Ly, 0.30, 'Tree')
    nt = 0
    for i, m in enumerate(mounds if DECOR else ()):                 # 17:32: 나무 0
        if m.get('quarry') or _h(i, 6.1) > 0.75:
            continue
        pts, z0, z1, k, cut = terr_levels(m)[-1]
        n = len(pts)
        cx, cy = sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n
        kd = 'o' if _h(i, 6.5) < 0.65 else 'p'
        h = H_FAR * (K_OLIVE if kd == 'o' else K_PINE)
        q = tree_scr(cx, -cy, z1, crown_r(kd, h), h)
        if (vlab and poly_dist(q, vlab) < 1.5) or in_text(q) or (ctx.leads and min(line_dist(q, L) for L in ctx.leads) < 1.0):
            continue
        T.put(kd, cx, cy, z1, h, i + 0.3)
        nt += 1
    for th in ((-28.0, -18.0) if DECOR else ()):
        s = ridge_spec(th)
        X, Y = PP(th, rho(th) + s[2] * 0.55)
        h = H_FAR * 2.8
        q = tree_scr(X, Y, s[0], crown_r('c', h), h)
        if R.to_screen(X, Y)[0] < 419.0 and not in_text(q):
            T.put('c', X, -Y, s[0], h, th)
            nt += 1
    b6 = Ly(6, 'Life', [M['sheep']] + people_mats(0.15) + [M['pozz'], tree_mats(0.15)[2][1]])
    left = [m for m in mounds if not m.get('quarry')]
    if not DECOR:                                                    # 17:32: 양·목자·일꾼 0 → L6은 둔덕 위 관목 덩이
        bsc = Ly(6, 'Scrub', [tree_mats(0.15)[2][1], M['plain']])
        for i, m in enumerate(left):
            pts, z0, z1, k, cut = terr_levels(m)[-1]
            n_ = len(pts); cx, cy = sum(p[0] for p in pts) / n_, sum(p[1] for p in pts) / n_
            for q in range(5):
                a_ = 2 * math.pi * _h(i, q, 6.7); rr = 0.45 * m['R'] * math.sqrt(_h(i, q, 6.8))
                blob(bsc, (cx + rr * math.cos(a_), cy + rr * math.sin(a_), z1 + 0.05), 0.55, 0.45, 0.3, 6, 3, 0.25, i * 7 + q, q % 2)
        left = []
    if left:
        m0 = min(left, key=lambda m: m['h'])
        hills = [o for o in ridge_obs]

        def Zg(x, y):
            z = ray_z(hills, x, y)
            return z if z is not None else 0.3
        sxc, syc = m0['X'] + m0['R'] * 1.3, m0['Y'] + m0['R'] * 0.2
        for q in range(8):
            x = sxc + 1.6 * _j(q, 7.1)
            y = -(syc + 1.2 * _j(q, 7.2))
            z = Zg(x, y)
            blob(b6, (x, y, z + 0.22), 0.3, 0.21, 0.21, 6, 3, 0.15, q + 0.1, 0)
            blob(b6, (x + 0.24, y - 0.09, z + 0.3), 0.1, 0.09, 0.1, 5, 2, 0.1, q + 0.2, 1 + HAIR)
        person(b6, sxc - 2.4, -(syc - 0.6), Zg(sxc - 2.4, -(syc - 0.6)), H_FAR, 1 + 5, 7.7, arm=0.8)
    if qm and DECOR:                                                 # 17:32: 채석장 일꾼 0
        QX, QY = qm['X'], qm['Y']
        for k, v in enumerate((-1.4, 1.1)):
            u = qm['R'] * 0.72
            px, py = QX + CAM_U[0] * u + CAM_U[1] * v, -QY + CAM_U[1] * u - CAM_U[0] * v
            person(b6, px, py, qm['z0'] + 0.06, H_FAR, 1 + (0, 3)[k], 8.1 + k, arm=0.9 if k == 0 else 0.0)
        u, v = qm['R'] * 0.98, -2.6
        px, py = QX + CAM_U[0] * u + CAM_U[1] * v, -QY + CAM_U[1] * u - CAM_U[0] * v
        z0q = qm['z0'] + 0.06
        G.box(b6, px - 0.4, px + 0.4, py - 0.62, py + 0.62, z0q + 0.25, z0q + 0.55, len(CLOTH) + 4)
        blob(b6, (px, py, z0q + 0.62), 0.32, 0.52, 0.2, 6, 2, 0.2, 5.5, len(CLOTH) + 3)
        for sy_ in (-0.42, 0.42):
            G.cyl(XB(b6, Matrix.Translation((px - 0.42, py + sy_, z0q + 0.25)) @ Matrix.Rotation(math.pi / 2, 4, 'Y')), 0, 0, 0.25, -0.05, 0.05, 10, len(CLOTH) + 4, bottom=True)
    Ly.finish()
    REPORT['Albani'] = dict(sections=len(secs), mounds=len(mounds), quarry=bool(qm), parcels=npar, quiet_parcels=nq, trees=nt,
                            bbox=[round(v, 1) for v in kids_bbox(root)])
    REPORT['_ridge'] = dict(C=C, secs=secs, cov_rng=cov_rng, cov_x=cov_x)
    return root


def ridge_cover(ves):
    """앞 능선 덮개(화면 mm): x마다 (산 밑동 앞 윤곽 y) − (능선 윗면 실루엣 y). 능선 윗면 = 위·아래층 윗면 꺾은선의 최소 y"""
    info = REPORT.get('_ridge')
    if not info:
        return None
    C, rho, yb, scr = ves_base(ves)
    secs = info['secs']
    tops = []
    for key_w, key_z in (('wU', 'zU'), ('wL', 'zL')):
        for rr_key in ('in', 'out'):
            line = []
            for s in secs:
                r = s['rb'] + (s['gap'] if rr_key == 'in' else s[key_w])
                t = math.radians(s['th'])
                X, Y = C[0] + r * math.cos(t), C[1] + r * math.sin(t)
                line.append(R.to_screen(X, Y, s[key_z]))
            tops.append(line)

    quads = []                                               # 윗면 사각형(위층·아래층): 안쪽 i·바깥 i·바깥 i+1·안쪽 i+1
    for lv in ((0, 1), (2, 3)):
        A_, B_ = tops[lv[0]], tops[lv[1]]
        for i in range(len(A_) - 1):
            quads.append([A_[i], B_[i], B_[i + 1], A_[i + 1]])

    def ytop(x):
        best = None
        for q in quads:
            for (x1, y1), (x2, y2) in zip(q, q[1:] + q[:1]):
                if (x1 - x) * (x2 - x) <= 0 and abs(x1 - x2) > 1e-9:
                    y = y1 + (y2 - y1) * (x - x1) / (x2 - x1)
                    best = y if best is None else min(best, y)
        return best
    x0, x1 = info['cov_x']
    out = []
    x = x0 + 1.0                                              # 설계 실측(drawn vesuvius_cover_mm: x 361~417)과 같은 범위
    while x <= x1 - 1.0 + 1e-6:
        b, t = yb(x), ytop(x)
        if b is not None and t is not None:
            out.append((round(x, 1), round(b - t, 2)))
        x += 1.0
    return out


# ───────────────────────── 7. 포도밭 농장(앞 능선 위 평평한 계단에 얹힌다, 대기 원근 25%) ─────────────────────────
FARM_ATMO = 0.25


def build_farm(GC, ctx, ves):
    """농장 집채(본채·헛간·마당)는 능선 위층 윗면(평평, RIDGE_ZF)에, 포도 줄은 능선 두 층 윗면을 따라 호로 둔다.
    농장 지면 = 능선 윗면(따로 뜬 밭판 없음). 대지 상자 [366,122,408,144] 안. 사람 키 1.8, 나무 D8 먼 쪽 키"""
    info = REPORT.get('_ridge')
    C, rho, yb, scr = ves_base(ves)
    box = ctx.prop('포도밭 농장')['box']
    th = FARM_C_TH
    zU = RIDGE_ZF
    _, zL, wU, wL = ridge_spec(th)
    rb = rho(th)
    rc_ = rb + ridge_gap(th) + 0.25 + (wU - ridge_gap(th) - 0.5) * 0.5
    t = math.radians(th)
    Xc, Yc = C[0] + rc_ * math.cos(t), C[1] + rc_ * math.sin(t)
    root = G.new_root('SUB_Farm_root', GC, Xc, Yc, zU)
    M = villa_mats(FARM_ATMO, 'Farm')
    M2 = dict(vine=mat('farm_vine', '#6F8B45', 0.3), vine2=mat('farm_vine2', '#8DA352', 0.3), post=mat('farm_post', '#8E6E4C', 0.3),
              yard=mat('farm_yard', '#CDB487', FARM_ATMO), yard2=mat('farm_yard2', '#BFA477', FARM_ATMO))

    def inside_top(X, Y, m=0.35):
        a = math.degrees(math.atan2(Y - C[1], X - C[0]))
        r = math.hypot(X - C[0], Y - C[1])
        rbb = rho(a)
        _, _, wu, _ = ridge_spec(a)
        return rbb + ridge_gap(a) + m <= r <= rbb + wu - m
    # 집채 평면(지역 X ↘, Y ↙, 단위 mm): 마당 6.0×4.4 · 본채 4.2×2.4 · 헛간 2.4×2.0
    yard = (-3.0, 3.0, -2.2, 2.2)
    for k in range(12):                                     # 마당 네 모서리가 능선 윗면 안에 들 때까지 줄인다
        cs = [(Xc + x, Yc + y) for x in (yard[0], yard[1]) for y in (yard[2], yard[3])]
        if all(inside_top(X, Y) for X, Y in cs):
            break
        yard = tuple(v * 0.93 for v in yard)
    sc = (yard[1] - yard[0]) / 6.0
    Ly = Lay('Farm', root, GC)
    b0 = Ly(0, 'Mass', [M['plaster'], M['plaster2'], M2['yard']])
    pbox(b0, yard[0], yard[1], yard[2], yard[3], 0.0, 0.06, 2)                            # 마당(능선 윗면 위 0.06)
    hx0, hx1, hy0, hy1 = yard[0] + 0.4 * sc, yard[0] + 4.6 * sc, yard[2] + 0.2 * sc, yard[2] + 2.6 * sc
    bx0, bx1, by0, by1 = yard[1] - 2.6 * sc, yard[1] - 0.2 * sc, yard[2] + 0.4 * sc, yard[2] + 2.4 * sc
    HH, BH = 2.7, 1.9
    pbox(b0, hx0, hx1, hy0, hy1, 0.06, HH, 0)
    pbox(b0, bx0, bx1, by0, by1, 0.06, BH, 1)
    b3r = Ly(3, 'Roof', [M['roof']])
    pgable(b3r, hx0, hx1, hy0, hy1, HH, HH + 1.25, 'X', 0, 0.22)
    pgable(b3r, bx0, bx1, by0, by1, BH, BH + 0.95, 'X', 0, 0.18)
    b1 = Ly(1, 'Shade', [M['dark'], M['deep']])
    for i in range(3):
        X = hx0 + (hx1 - hx0) * (0.18 + 0.28 * i)
        pbox(b1, X, X + 0.45, hy1, hy1 + 0.05, 1.5, 2.15, 0)
    pbox(b1, hx0 + (hx1 - hx0) * 0.42, hx0 + (hx1 - hx0) * 0.58, hy1, hy1 + 0.06, 0.06, 1.4, 0)
    pbox(b1, hx1, hx1 + 0.05, hy0 + 0.6, hy0 + 1.1, 1.5, 2.1, 0)
    pbox(b1, bx0 + 0.5, bx1 - 0.5, by1, by1 + 0.05, 0.06, 1.3, 0)
    b2 = Ly(2, 'Members', [M['wood'], M['wood_dk'], M['stone']])
    for X in (yard[0] + 0.05, yard[1] - 0.05):                                            # 마당 울타리(낮은 돌담)
        pbox(b2, X - 0.08, X + 0.08, yard[2], yard[3], 0.06, 0.5, 2)
    pbox(b2, yard[0], yard[1], yard[3] - 0.16, yard[3], 0.06, 0.5, 2)
    pbox(b2, hx0 + (hx1 - hx0) * 0.4, hx0 + (hx1 - hx0) * 0.6, hy1, hy1 + 0.1, 1.4, 1.52, 1)
    b3 = Ly(3, 'Vines', [M2['vine'], M2['vine2'], M2['post'], M['earth2']])
    b2p = Ly(2, 'Posts', [M2['post']])
    nrow = 0
    for (lv, zr, r0f, r1f, step) in (('U', zU, 'gap', 'wU', 1.05), ('L', None, 'wU', 'wL', 1.0)):
        for j in range(6):
            rows = []
            th_ = FARM_TH[0]
            while th_ <= FARM_TH[1] + 1e-6:
                zu, zl, wu, wl = ridge_spec(th_)
                rbb = rho(th_)
                base_r = rbb + (ridge_gap(th_) if r0f == 'gap' else wu)
                lim = rbb + (wu if r1f == 'wU' else wl)
                r = base_r + 0.55 + step * j
                X, Y = C[0] + r * math.cos(math.radians(th_)), C[1] + r * math.sin(math.radians(th_))
                sxy = R.to_screen(X, Y)
                zrow = (zr if zr is not None else zl) + 0.34
                ok = r <= lim - 0.45 and box[0] + 0.5 <= sxy[0] <= box[2] - 0.5 and R.to_screen(X, Y, zrow - 0.34)[1] <= box[3] - 0.45
                if ok and lv == 'U' and yard[0] - 0.6 <= X - Xc <= yard[1] + 0.6 and yard[2] - 0.6 <= Y - Yc <= yard[3] + 0.6:
                    ok = False
                if ok:
                    rows.append((X - Xc, -(Y - Yc), (zr if zr is not None else zl) - zU + 0.14))
                elif len(rows) >= 2:
                    ribbon(b3, rows, 0.3, 0.2, j % 2)
                    for p in rows[::3]:
                        G.box(b2p, p[0] - 0.05, p[0] + 0.05, p[1] - 0.05, p[1] + 0.05, p[2] - 0.2, p[2] + 0.12, 0)
                    nrow += 1
                    rows = []
                else:
                    rows = []
                th_ += 2.0
            if len(rows) >= 2:
                ribbon(b3, rows, 0.3, 0.2, j % 2)
                for p in rows[::3]:
                    G.box(b2p, p[0] - 0.05, p[0] + 0.05, p[1] - 0.05, p[1] + 0.05, p[2] - 0.2, p[2] + 0.12, 0)
                nrow += 1
    b3m = Ly(3, 'Yard', [M2['yard2']])
    for i in range(6):                                                                    # 마당 흙 결(바퀴 자국·짚)
        x0 = yard[0] + 0.5 + (yard[1] - yard[0] - 1.0) * _h(i, 5.1)
        pbox(b3m, x0, x0 + 0.9, yard[3] - 1.4 + 0.3 * _h(i, 5.2), yard[3] - 1.1 + 0.3 * _h(i, 5.2), 0.06, 0.075, 0)
    b4 = Ly(4, 'Detail', [M['terra'], M['terra_dk'], M['stone'], M['wood_dk']])
    for i in range(3):                                                                    # 돌리아 3 · 굴뚝 · 압착 통
        X = bx0 - 0.6 - 0.75 * i
        lathe(b4, X, -(yard[3] - 0.8), [(0.28, 0.06), (0.33, 0.2), (0.26, 0.34), (0.16, 0.4)], n=9, mi=0)
        G.cyl(b4, X, -(yard[3] - 0.8), 0.13, 0.4, 0.42, 8, 1, bottom=True)
    pbox(b4, hx1 - 0.9, hx1 - 0.5, hy0 + 0.6, hy0 + 1.0, HH, HH + 1.6, 2)
    G.cyl(b4, yard[0] + 1.0, -(yard[3] - 0.9), 0.32, 0.06, 0.48, 10, 3, bottom=True)
    b5 = Ly(5, 'Light', [M['ridge'], M['hi']])
    pbox(b5, hx0 - 0.2, hx1 + 0.2, (hy0 + hy1) / 2 - 0.08, (hy0 + hy1) / 2 + 0.08, HH + 1.22, HH + 1.29, 0)
    pbox(b5, bx0 - 0.15, bx1 + 0.15, (by0 + by1) / 2 - 0.07, (by0 + by1) / 2 + 0.07, BH + 0.92, BH + 0.98, 0)
    pbox(b5, yard[0], yard[1], yard[3] - 0.16, yard[3], 0.5, 0.53, 1)
    T = Trees(Ly, FARM_ATMO, 'Tree')                                                      # L6: 사이프러스·올리브(D8 먼 쪽 키)
    T.put('c', bx1 + 0.9, -(by0 + 0.4), 0.06, H_FAR * 2.9, 8.3)
    T.put('o', hx0 - 0.4, -(yard[3] - 0.6), 0.06, H_FAR * K_OLIVE, 8.9)
    T.bush(yard[0] + 0.5, -(yard[2] + 0.4), 0.06, 0.45, 9.4)
    bp = Ly(6, 'People', people_mats(FARM_ATMO) + [M['wood']])
    workers = 0
    for k, (dth, dr) in enumerate(((-26.0, 1.6), (18.0, 2.6))):
        th_ = th + dth
        zu, zl, wu, wl = ridge_spec(th_)
        rbb = rho(th_)
        r = rbb + ridge_gap(th_) + dr
        X, Y = C[0] + r * math.cos(math.radians(th_)), C[1] + r * math.sin(math.radians(th_))
        person(bp, X - Xc, -(Y - Yc), (zu if r < rbb + wu else zl) - zU + 0.06, H_FAR, (0, 3)[k], 3.3 + k, arm=0.5 if k == 0 else 0.0)
        workers += 1
    G.cyl(bp, yard[0] + 2.0, -(yard[3] - 0.6), 0.2, 0.06, 0.34, 8, len(CLOTH) + 3, r_top=0.26, bottom=True)
    Ly.finish()
    bb = kids_bbox(root)
    REPORT['Farm'] = dict(bbox=[round(v, 1) for v in bb], box=box, yard_scale=round(sc, 3), rows=nrow, workers=workers, person_h=H_FAR,
                          on_ridge_z=zU, plan=[round(Xc, 2), round(Yc, 2)])
    return root


# ───────────────────────── 8. 앵커(D11) ─────────────────────────
def _ray_first(obs, x, y):
    """화면 점 (x, y)를 지나는 카메라 광선이 obs 중 처음 맞는 점(월드)과 오브젝트"""
    o = R.P(*R.to_plan(x, y), 0.0) - R.FWD * 900.0
    best = None
    for ob in obs:
        mi = ob.matrix_world.inverted()
        lo = mi @ o
        ld = (mi.to_3x3() @ R.FWD).normalized()
        ok, loc, nor, idx = ob.ray_cast(lo, ld)
        if ok:
            w = ob.matrix_world @ loc
            d = (w - o).length
            if best is None or d < best[0]:
                best = (d, w, ob)
    return best


def _anchor(GC, name, w, target, src, hit):
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, None)
    if ob.name not in GC.objects:
        GC.objects.link(ob)
    ob.empty_display_type = 'SPHERE'
    ob.empty_display_size = 0.5
    ob.location = w
    ob.hide_render = True
    own = bpy.data.objects.get('SUB_Metella_root' if name.startswith('ANCHOR_L5') else ('SUB_Vesuvius_root' if name.startswith('ANCHOR_V') else ''))
    if own is not None:                                                  # b5·b6: 대상 루트 자식으로(월드 자리 유지) → sil on_sil 판정
        bpy.context.view_layer.update()
        ob.parent = own; ob.matrix_parent_inverse = own.matrix_world.inverted()
    ob['target'] = target
    ob['source'] = src
    ob['hit'] = hit
    sx, sy = R.scr(w)
    return dict(name=name, world=[round(w.x, 3), round(w.y, 3), round(w.z, 3)], screen=[round(sx, 2), round(sy, 2)], target=target, hit=hit, source=src)


def build_anchors(GC, ctx):
    mine = [o for o in GC.all_objects if o.type == 'MESH' and not o.hide_render]
    out = []
    # L5_label: 라벨 지시선 끝(drawn) → 기단 왼면. 기단 아래 변에서 2.5mm 위부터 찾는다(보이는 면 위)
    lab = next((l for l in ctx.D.get('labels', []) if '메텔라' in l.get('name', '')), None)
    tgt = tuple(lab['leader']['pts'][-1]) if lab and lab.get('leader') else tuple(ctx.lm['L5'].get('target_pt', (381.3, 347.2)))
    best = None
    for k in range(25):
        y = tgt[1] - 2.6 + 0.2 * k
        h = _ray_first(mine, tgt[0], y)
        if h and h[2].name.startswith('SUB_Metella_L') and any(p in h[2].name for p in ('_Facing', '_Members', '_Relief', '_Mass', '_Light', '_Shade')):
            best = h
            break
    if best:
        out.append(_anchor(GC, 'ANCHOR_L5_label', best[1], '메텔라 기단(라벨 지시선 끝)', 'drawn 라벨 지시선 끝 %s' % (tgt,), best[2].name))
    # L5_c4: C4 지시선 시작(drawn) → 드럼 면
    c4 = next((L for L in ctx.D.get('leaders', []) if 'C4' in L.get('name', '')), None)
    tgt = tuple(c4['pts'][0]) if c4 else (370.5, 316.0)
    best = None
    for k in range(16):
        h = _ray_first(mine, tgt[0] + 0.2 * k, tgt[1])
        if h and h[2].name.startswith('SUB_Metella_L') and any(p in h[2].name for p in ('_Facing', '_Relief', '_Shade', '_Light', '_Life')) and h[1].z > 10.0 * h[2].matrix_world.to_scale().z:
            best = h
            break
    if best:
        out.append(_anchor(GC, 'ANCHOR_L5_c4', best[1], '메텔라 드럼(C4 지시선 시작)', 'drawn C4 지시선 시작 %s' % (tgt,), best[2].name))
    # V_label: 베수비오 라벨 지시선 끝 → 산 왼쪽 비탈(농장·능선 실루엣 밖). 위로 올라가며 산 메시에 처음 맞는 점
    if bpy.data.objects.get('SUB_Vesuvius_root') is None:            # d5: 베수비오 삭제 → V_label 앵커 0
        REPORT['anchors'] = out
        return out
    vl = next((l for l in ctx.D.get('labels', []) if '베수비오' in l.get('name', '')), None)
    sl_ = ctx.slot('베수비오') or {}
    if vl and vl.get('leader'):
        tgt = tuple(vl['leader']['pts'][-1])
    elif sl_.get('target_pt'):
        tgt = tuple(sl_['target_pt'])
    else:                                                             # 18:45 지형 v2 임시 자리: 산 상자 왼쪽 30%·위에서 55%
        vb_ = kids_bbox(bpy.data.objects['SUB_Vesuvius_root'])
        tgt = (vb_[0] + 0.3 * (vb_[2] - vb_[0]), vb_[1] + 0.55 * (vb_[3] - vb_[1]))
    best = None
    for k in range(40):
        h = _ray_first(mine, tgt[0], tgt[1] - 1.2 - 0.25 * k)
        if h and h[2].name.startswith('SUB_Vesuvius_L'):
            best = h
            break
    if best:
        out.append(_anchor(GC, 'ANCHOR_V_label', best[1], '베수비오 왼쪽 비탈(라벨 지시선 끝)', 'drawn 베수비오 지시선 끝 %s' % (tgt,), best[2].name))
    REPORT['anchors'] = out
    return out


# ───────────────────────── 9. 감사·실측 ─────────────────────────
def audit(GC):
    """루트마다 L0~L6 메시가 1개 이상(면 0 메시 금지)인지 센다(D10). bglobal roma_kit.layer_audit가 있으면 그 결과도 붙인다"""
    out = {}
    for r in sorted([o for o in GC.objects if o.type == 'EMPTY' and o.name.endswith('_root')], key=lambda o: o.name):
        cnt = [0] * 8
        empty = []
        for o in r.children_recursive:
            if o.type != 'MESH':
                continue
            m = re.search(r'_L(\d)_', o.name)
            if not m:
                continue
            if len(o.data.polygons) == 0:
                empty.append(o.name)
                continue
            cnt[int(m.group(1))] += 1
        out[r.name] = dict(L0_L6=cnt[:7], missing=[n for n in range(7) if cnt[n] == 0], empty=empty)
    ext = None
    if hasattr(R, 'layer_audit'):
        try:
            ext = R.layer_audit(GC)
        except Exception as e:
            ext = 'layer_audit 오류: %s' % e
    return out, ext


def measure(GC, ctx, ves):
    """실측: 루트별 화면 상자, 베수비오 면적, 메텔라 오차, 덮개, 글 블록·P2 자리 높이 위반, 예약 원 침범"""
    res = {}
    roots = sorted([o for o in GC.objects if o.type == 'EMPTY' and o.name.endswith('_root')], key=lambda o: o.name)
    for r in roots:
        try:
            bb = kids_bbox(r)
            res[r.name] = [round(v, 2) for v in bb]
        except ValueError:
            res[r.name] = None
    texts = ctx.floor_blocks(('COLLI ALBANI', '알바노 구릉'))
    bad_text, bad_p2, bad_res = [], 0, 0
    p2 = (302.0, 20.0, 402.0, 92.0)
    for o in GC.all_objects:
        if o.type != 'MESH' or o.hide_render:
            continue
        mw = o.matrix_world
        vs = [mw @ v.co for v in o.data.vertices]
        for w in vs[::max(1, len(vs) // 400)]:
            sx, sy = R.scr(w)
            if p2[0] <= sx <= p2[2] and p2[1] <= sy <= p2[3]:
                bad_p2 += 1
            if w.z > 1.0 and any(pt_poly_d((sx, sy), t) < 1.5 for t in texts):
                bad_text.append(o.name)
            if not o.name.startswith('SUB_AppiaTrees') and ctx.reserve_d(w.x, -w.y) < 0.5 and w.z < 0.5:
                bad_res += 1
    cov = ridge_cover(ves) if ves else None
    cv = [c for x, c in cov] if cov else []
    res['_checks'] = dict(colli_albani_block_over_1mm=sorted(set(bad_text))[:12], colli_albani_block_violations=len(bad_text),
                          p2_zone_vertices=bad_p2, hero_reserve_ground_vertices=bad_res,
                          ridge_cover_mm=[min(cv), max(cv)] if cv else None, ridge_cover_samples=len(cv),
                          ridge_cover_bad=[c for c in (cov or []) if not (3.0 <= c[1] <= 5.0)][:10])
    return res


# ───────────────────────── 짓기 ─────────────────────────
# ═════════════════════ 18:45 지형 고도화 v2(메인): 상자 하나에 맞춰 짓는 화산 · 화산 구릉 산맥 ═════════════════════
# 자리는 spec terrain/background 상자에서 읽고, 없으면 짓지 않는다(TERRAIN_USE_TEMP = True면 임시 자리 = d4 상자).
# 층: L0 높이장(면 톤 3 × 높이 띠 3, 대기 원근 혼합) · L1 골짜기 그늘 띠·분화구 속 · L2 오솔길 · L3 용암·화산재 줄(구릉은 응회암 띠·화구호)
#     · L4 바위 노두·분화구 테 · L5 능선 하이라이트 · L6 사면 수풀 점(나무 오브젝트 아님)
TERRAIN_V2 = True
TERRAIN_USE_TEMP = False
TERRAIN_TEMP = {'vesuvius': (360.0, 98.0, 418.0, 138.0), 'albani': (318.0, 122.0, 420.0, 162.0)}
T_ATMO = 0.32                                          # 먼 배경: 땅색 32% 혼합
T_LIGHT = Vector((-0.62, 0.18, 0.76)).normalized()     # 면 톤을 고르는 고정 방향(화면 왼쪽 위). 렌더 조명이 아니다
T_VIS = (-150.0, 60.0)                                 # 카메라에 보이는 방위(Blender 지역 각)


def ter_mats(kind):
    a = T_ATMO
    if kind == 'volcano':
        bands = (('#A7AE79', '#8E9A63', '#76825A'), ('#B9A989', '#A08F72', '#857660'), ('#C9C1B2', '#ADA597', '#918A7E'))
        extra = dict(valley='#6E6A57', pit='#5E554C', path='#D2C2A0', lava='#776B63', ash='#C2B9AA', rock='#857A6E', rock2='#A39888',
                     rim='#6F665D', ridge='#E2DAC6', ridge2='#D3C9B2', scrub='#7E8B55', scrub2='#93985F')
    else:
        bands = (('#AEB47F', '#96A06B', '#7F8A5C'), ('#B8B289', '#A19B77', '#8A8466'), ('#C3BC9D', '#ABA486', '#948E73'))
        extra = dict(valley='#6F7356', pit='#5F5A4C', path='#D4C6A4', lava='#9C9070', ash='#C7BC9A', rock='#8C8170', rock2='#A89D89',
                     rim='#77705F', ridge='#E3DCC5', ridge2='#D2CAB0', scrub='#7A8A52', scrub2='#8F995C', lake='#93AEB8', lake_hi='#C7D7DA')
    tag = 'tv' if kind == 'volcano' else 'ta'
    ms = [mat('%s_b%d%d' % (tag, i, j), bands[i][j], a) for i in range(3) for j in range(3)]
    ms.append(mat('%s_skirt' % tag, bands[0][1], 0.62))                         # 9: 산자락(땅색에 가깝게 스며든다)
    return ms, {k: mat('%s_%s' % (tag, k), v, a) for k, v in extra.items()}


def _hf_tone(bm, H, base_mi=0, jit=None):
    """면 톤(고정 방향과 기울기) × 높이 띠로 재질 번호를 정한다"""
    bm.normal_update()
    lx, ly = T_LIGHT.x, T_LIGHT.y
    ll = math.hypot(lx, ly)
    for f in bm.faces:
        if f.normal.z < 0.05:
            continue
        sl = math.hypot(f.normal.x, f.normal.y)                                  # 기울기(수평 성분)와 사면 방위로 밝은·중간·그늘 면
        d = (f.normal.x * lx + f.normal.y * ly) / max(1e-6, sl * ll)
        tone = 1 if sl < 0.06 else (0 if d > 0.3 else (2 if d < -0.3 else 1))
        zr = f.calc_center_median().z / max(1e-6, H)
        if zr < 0.045:
            f.material_index = base_mi + 9
            continue
        zc = zr + (jit(f) if jit else 0.0)
        band = 0 if zc < 0.34 else (1 if zc < 0.7 else 2)
        f.material_index = base_mi + band * 3 + tone


def _polar_hf(bm, zf, rmax, nr=26, na=72, sx=1.0, sy=1.0, mi_side=0):
    """극좌표 높이장(바깥 테 z 0 + 바닥 마개): zf(t, a) — t = 0(가운데) ~ 1(테). sx·sy = 타원 배율"""
    rows = []
    for i in range(nr + 1):
        t = 1.0 - i / nr
        if i == nr:
            rows.append([bm.verts.new((0.0, 0.0, zf(0.0, 0.0)))])
            continue
        rows.append([bm.verts.new((rmax * t * sx * math.cos(2 * math.pi * k / na), rmax * t * sy * math.sin(2 * math.pi * k / na),
                                   zf(t, 2 * math.pi * k / na))) for k in range(na)])
    for i in range(nr - 1):
        for k in range(na):
            bm.faces.new([rows[i][k], rows[i][(k + 1) % na], rows[i + 1][(k + 1) % na], rows[i + 1][k]])
    for k in range(na):
        bm.faces.new([rows[nr - 1][k], rows[nr - 1][(k + 1) % na], rows[nr][0]])
    f = bm.faces.new(rows[0][::-1]); f.material_index = mi_side


def _vis_ang(deg):
    d = (deg + 180.0) % 360.0 - 180.0
    return T_VIS[0] <= d <= T_VIS[1]


def _fit_terrain(root, box):
    """폭으로 평면 배율, 높이로 z 배율(이분법), 가운데 x·아래 y를 상자에 맞춘다"""
    bpy.context.view_layer.update()
    bb = kids_bbox(root)
    s0 = root.scale.x
    s = s0 * (box[2] - box[0]) / max(1e-6, bb[2] - bb[0])
    root.scale = (s, s, s)
    bpy.context.view_layer.update()

    def hgt(kz):
        root.scale.z = s * kz
        bpy.context.view_layer.update()
        b = kids_bbox(root)
        return b[3] - b[1]
    lo, hi = 0.3, 8.0
    want = box[3] - box[1]
    if hgt(hi) <= want:
        kz = hi
    elif hgt(lo) >= want:
        kz = lo
    else:
        for _ in range(28):
            mid = 0.5 * (lo + hi)
            if hgt(mid) < want:
                lo = mid
            else:
                hi = mid
        kz = 0.5 * (lo + hi)
    hgt(kz)
    b = kids_bbox(root)
    dx = (box[0] + box[2]) / 2 - (b[0] + b[2]) / 2
    dy = box[3] - b[3]
    dX, dY = R.to_plan(dx, dy)
    root.location = root.location + Vector((dX, -dY, 0.0))
    bpy.context.view_layer.update()
    return s, kz, kids_bbox(root)


def build_volcano_v2(GC, box, name='Vesuvius'):
    """79년 이전 베수비오: 넓고 완만한 봉우리 하나, 잿빛 평평한 정상과 얕은 분화구, 오목한 사면에 골 14갈래(골은 아래로 깊어진다)"""
    RB, H, TT = 24.0, 17.0, 0.17
    NG = 14

    def zf(t, a):
        if t >= 1.0:
            return 0.0
        rim = H * (1.0 - TT) ** 1.45
        if t <= TT:
            dep = 0.9 * (1.0 - (t / TT) ** 2) if t < TT * 0.8 else 0.0
            return rim + 0.25 - dep
        g = 1.0 - (0.16 * ((t - TT) / (1.0 - TT)) ** 0.7) * (0.5 + 0.5 * math.cos(NG * a + 0.8 * math.sin(3 * a)))
        return H * (1.0 - t) ** 1.45 * g + 0.2 * _j(int(a * 30), int(t * 40), 3.3) * t * (1.0 - t)
    root = G.new_root('SUB_%s_root' % name, GC, 0.0, 0.0, 0.0)
    BM, X = ter_mats('volcano')
    Ly = Lay(name, root, GC)
    b0 = Ly(0, 'Mass', BM)
    _polar_hf(b0, zf, RB, nr=28, na=84)
    _hf_tone(b0, H, 0, jit=lambda f: 0.05 * _j(int(f.calc_center_median().x * 3), int(f.calc_center_median().y * 3), 7.7))
    mass = Ly.finish()
    Ly = Lay(name, root, GC)

    def P(t, a, dz=0.06):
        x, y = RB * t * math.cos(a), RB * t * math.sin(a)
        z = ray_z(mass, x, y)
        return (x, y, (z if z is not None else zf(t, a)) + dz)
    def _solve(c):                                                               # NG·a + 0.8·sin 3a = c 인 방위(뉴턴)
        a = c / NG
        for _ in range(8):
            a -= (NG * a + 0.8 * math.sin(3 * a) - c) / (NG + 2.4 * math.cos(3 * a))
        return a % (2 * math.pi)
    gul = [_solve(2 * k * math.pi) for k in range(NG)]                          # cos = +1 → g 최소 = 골(낮음)
    rid = [_solve((2 * k + 1) * math.pi) for k in range(NG)]                    # cos = −1 → 능선(높음)
    b1 = Ly(1, 'Valleys', [X['valley'], X['pit']])
    for kq, a in enumerate(gul):
        if not _vis_ang(math.degrees(a)):
            continue
        ribbon(b1, [P(TT + 0.06 + 0.055 * i, a + 0.03 * math.sin(7 * i + kq), 0.08) for i in range(15)], 0.25, 0.06, 0, w1=1.1)
    lathe(b1, 0.0, 0.0, [(RB * TT * 0.78, zf(TT * 0.78, 0) + 0.02), (RB * TT * 0.5, zf(0.0, 0) + 0.03), (0.0, zf(0.0, 0) + 0.04)], n=24, mi=1)
    b2 = Ly(2, 'Paths', [X['path']])
    zig = [(0.97, -40), (0.84, -62), (0.72, -38), (0.6, -60), (0.48, -40), (0.37, -58), (0.27, -44), (TT + 0.02, -52)]
    pts = []
    for (t0, d0), (t1, d1) in zip(zig[:-1], zig[1:]):
        for i in range(5):
            f_ = i / 5.0
            pts.append(P(t0 + (t1 - t0) * f_, math.radians(d0 + (d1 - d0) * f_), 0.1))
    ribbon(b2, pts, 0.32, 0.06, 0)
    b3 = Ly(3, 'LavaAsh', [X['lava'], X['ash']])
    for k in range(16):
        a = math.radians(T_VIS[0] + 8.0 + (T_VIS[1] - T_VIS[0] - 16.0) * (k + 0.5 * _h(k, 1.3)) / 16.0)
        t1 = 0.42 + 0.3 * _h(k, 1.4)
        ribbon(b3, [P(TT + 0.01 + (t1 - TT) * i / 9.0, a + 0.05 * math.sin(3 * i + k), 0.07) for i in range(10)],
               0.4 if k % 2 else 0.28, 0.05, k % 2, w1=0.1)
    b4 = Ly(4, 'RocksRim', [X['rim'], X['rock'], X['rock2']])
    for k in range(26):                                                          # 분화구 테(들쭉날쭉 바위 덩이)
        a = 2 * math.pi * k / 26
        q = P(TT * 0.92, a, 0.0)
        blob(b4, (q[0], q[1], q[2] + 0.1), 0.75, 0.55, 0.35 + 0.25 * _h(k, 2.5), 5, 2, 0.3, 300 + k, 0)
    for k in range(30):                                                          # 위 사면 바위 노두
        a = math.radians(T_VIS[0] + (T_VIS[1] - T_VIS[0]) * _h(k, 2.6))
        q = P(TT + 0.05 + 0.4 * _h(k, 2.7), a, 0.0)
        blob(b4, (q[0], q[1], q[2] + 0.12), 0.45 + 0.35 * _h(k, 2.8), 0.35, 0.3, 5, 2, 0.3, 330 + k, 1 + k % 2)
    b5 = Ly(5, 'Ridges', [X['ridge'], X['ridge2']])
    for kq, a in enumerate(rid):
        if not _vis_ang(math.degrees(a)):
            continue
        ribbon(b5, [P(TT + 0.04 + 0.05 * i, a, 0.1) for i in range(10)], 0.16, 0.05, 1, w1=0.04)
    ribbon(b5, [P(TT * 0.98, math.radians(d), 0.14) for d in range(int(T_VIS[0]), int(T_VIS[1]) + 1, 6)], 0.28, 0.05, 0)
    b6 = Ly(6, 'Scrub', [X['scrub'], X['scrub2']])
    for k in range(90):
        a = math.radians(T_VIS[0] + (T_VIS[1] - T_VIS[0]) * _h(k, 3.1))
        q = P(0.45 + 0.52 * _h(k, 3.2), a, 0.0)
        blob(b6, (q[0], q[1], q[2] + 0.25), 0.42 + 0.25 * _h(k, 3.3), 0.38, 0.32, 6, 2, 0.2, 400 + k, k % 2)
    Ly.finish()
    s, kz, bb = _fit_terrain(root, box)
    REPORT[name] = dict(scale=round(s, 4), kz=round(kz, 3), bbox=[round(v, 2) for v in bb], box=list(box))
    return root


def build_hills_v2(GC, box, name='Albani'):
    """알바노 구릉(화산 구릉 산맥): 타원 산괴 + 바깥 칼데라 테 + 가운데 봉우리(몬테 카보) + 앞-왼쪽 화구호 둘(알바노 긴 타원 · 네미 둥근)"""
    RA, SY, H = 30.0, 0.45, 10.0
    ROT = 45.0                                                                   # 산괴 긴 축을 화면 가로(평면 45°)로: 지역 −y = 카메라 쪽(앞)
    V0, V1 = T_VIS[0] - ROT, T_VIS[1] - ROT                                      # 지역 각으로 본 보이는 방위
    lakes = [(-0.36, -0.12, 0.14, 0.085, 0.5), (-0.06, -0.46, 0.085, 0.085, 0.0)]   # (x, y 비율, rx, ry, 돌림)

    def lake_d(x, y):
        out = 0.0
        for (lx, ly, rx, ry, rt) in lakes:
            c, s_ = math.cos(rt), math.sin(rt)
            u = ((x - lx) * c + (y - ly) * s_) / rx; v = (-(x - lx) * s_ + (y - ly) * c) / ry
            q = u * u + v * v
            if q < 2.2:
                out = max(out, math.exp(-q * 1.2))
        return out

    def zf(t, a):
        if t >= 1.0:
            return 0.0
        x, y = t * math.cos(a), t * math.sin(a)
        r = math.hypot(x, y)
        z = H * 0.3 * (1.0 - r * r) ** 0.9
        z += H * 0.55 * math.exp(-((r - 0.6) / 0.12) ** 2) * (0.62 + 0.38 * math.cos(5 * a + 0.4)) * (0.8 + 0.2 * math.cos(11 * a + 1.1))   # 칼데라 테 봉우리들
        z += H * 0.8 * math.exp(-(((x - 0.12) ** 2 + (y - 0.06) ** 2) / 0.03))
        z += H * 0.16 * math.sin(9 * a + 1.3) * math.exp(-((r - 0.8) / 0.1) ** 2)
        z += H * 0.05 * math.cos(23 * a) * r * (1.0 - r)                       # 바깥 사면 골·능선 결
        z -= H * 0.55 * lake_d(x, y)
        return max(0.0, z * (1.0 if t < 0.9 else ((1.0 - t) / 0.1) ** 0.7))
    root = G.new_root('SUB_%s_root' % name, GC, 0.0, 0.0, 0.0)
    root.rotation_euler = (0.0, 0.0, math.radians(ROT))
    BM, X = ter_mats('hills')
    Ly = Lay(name, root, GC)
    b0 = Ly(0, 'Mass', BM)
    _polar_hf(b0, zf, RA, nr=30, na=96, sx=1.0, sy=SY)
    _hf_tone(b0, H * 1.2, 0, jit=lambda f: 0.06 * _j(int(f.calc_center_median().x * 2), int(f.calc_center_median().y * 2), 8.8))
    mass = Ly.finish()
    Ly = Lay(name, root, GC)

    def P(t, a, dz=0.06):
        x, y = RA * t * math.cos(a), RA * t * SY * math.sin(a)
        z = ray_z(mass, x, y)
        return (x, y, (z if z is not None else 0.0) + dz)

    def Pxy(x, y, dz=0.06):
        z = ray_z(mass, x * RA, y * RA * SY)
        return (x * RA, y * RA * SY, (z if z is not None else 0.0) + dz)
    b1 = Ly(1, 'Valleys', [X['valley'], X['pit']])
    for k in range(26):                                                          # 산괴 바깥 사면의 골(방사 띠)
        a = math.radians(V0 + 6.0 + (V1 - V0 - 12.0) * (k + 0.5) / 26.0 + 2.5 * _j(k, 4.1))
        ribbon(b1, [P(0.66 + 0.03 * i, a + 0.02 * math.sin(5 * i + k), 0.07) for i in range(10)], 0.3, 0.05, 0, w1=0.9)
    for k in range(10):                                                          # 칼데라 테 안쪽 그늘(가운데 쪽 사면)
        a = math.radians(V0 + 10.0 + (V1 - V0 - 20.0) * k / 9.0)
        ribbon(b1, [P(0.42 + 0.03 * i, a, 0.07) for i in range(5)], 0.5, 0.05, 0, w1=0.3)
    b2 = Ly(2, 'Paths', [X['path']])                                              # 테 위 옛길(비아 사크라 몬테 카보 쪽)
    ribbon(b2, [P(0.58, math.radians(d), 0.1) for d in range(int(V0) + 10, int(V1) - 19, 6)], 0.32, 0.05, 0)
    ribbon(b2, [Pxy(0.12 + (0.0 - 0.12) * i / 8.0, 0.06 + (-0.35 - 0.06) * i / 8.0, 0.1) for i in range(9)], 0.28, 0.05, 0)
    b3 = Ly(3, 'TuffLakes', [X['lava'], X['ash'], X['lake'], X['lake_hi']])
    for i, rr in enumerate((0.7, 0.75, 0.8, 0.85, 0.9)):                         # 응회암 층 띠(등고선처럼)
        ribbon(b3, [P(rr, math.radians(d), 0.08) for d in range(int(V0), int(V1) + 1, 5)], 0.4, 0.05, i % 2)
    for (lx, ly, rx, ry, rt) in lakes:                                           # 화구호 수면(평평한 판)
        zc = Pxy(lx, ly, 0.0)[2]
        pts = []
        for k in range(28):
            th = 2 * math.pi * k / 28
            u, v = rx * 0.78 * math.cos(th), ry * 0.78 * math.sin(th)
            c, s_ = math.cos(rt), math.sin(rt)
            pts.append(((lx + u * c - v * s_) * RA, (ly + u * s_ + v * c) * RA * SY))
        G.prism(b3, pts, zc + 0.02, zc + 0.12, 2)
        G.prism(b3, [(p[0] * 0.98 + (lx * RA) * 0.02, p[1] * 0.98 + (ly * RA * SY) * 0.02) for p in pts[2:9]] + [((lx - rx * 0.3) * RA, (ly + ry * 0.2) * RA * SY)], zc + 0.12, zc + 0.14, 3)
    b4 = Ly(4, 'RocksRim', [X['rim'], X['rock'], X['rock2']])
    for k in range(70):                                                          # 칼데라 테·바깥 사면 바위 노두
        a = math.radians(V0 + (V1 - V0) * _h(k, 5.1))
        q = P((0.6 + 0.04 * _j(k, 5.2)) if k < 40 else (0.7 + 0.2 * _h(k, 5.5)), a, 0.0)
        blob(b4, (q[0], q[1], q[2] + 0.12), 0.55 + 0.3 * _h(k, 5.3), 0.4, 0.3 + 0.2 * _h(k, 5.4), 5, 2, 0.3, 500 + k, k % 3)
    for (lx, ly, rx, ry, rt) in lakes:                                           # 화구호 테(짙은 바위 고리)
        for k in range(14):
            th = 2 * math.pi * k / 14
            q = Pxy(lx + rx * 1.05 * math.cos(th), ly + ry * 1.05 * math.sin(th), 0.0)
            blob(b4, (q[0], q[1], q[2] + 0.08), 0.4, 0.3, 0.22, 5, 2, 0.3, 560 + k + lx * 50, 0)
    b5 = Ly(5, 'Ridges', [X['ridge'], X['ridge2']])
    ribbon(b5, [P(0.6, math.radians(d), 0.14) for d in range(int(V0), int(V1) + 1, 5)], 0.26, 0.05, 0)
    for k in range(9):
        a = math.radians(V0 + 12.0 + (V1 - V0 - 24.0) * k / 8.0)
        ribbon(b5, [P(0.62 + 0.035 * i, a, 0.1) for i in range(8)], 0.24, 0.05, 1, w1=0.06)
    ribbon(b5, [Pxy(0.12 + 0.06 * math.cos(math.radians(d)), 0.06 + 0.06 * math.sin(math.radians(d)), 0.12) for d in range(int(V0), int(V1) + 1, 15)], 0.24, 0.05, 0)
    b6 = Ly(6, 'Scrub', [X['scrub'], X['scrub2']])
    for k in range(240):
        a = math.radians(V0 + (V1 - V0) * _h(k, 6.1))
        t = 0.3 + 0.62 * _h(k, 6.2)
        x, y = t * math.cos(a), t * math.sin(a)
        if lake_d(x, y) > 0.25:
            continue
        q = P(t, a, 0.0)
        blob(b6, (q[0], q[1], q[2] + 0.22), 0.38 + 0.22 * _h(k, 6.3), 0.34, 0.28, 6, 2, 0.2, 600 + k, k % 2)
    Ly.finish()
    s, kz, bb = _fit_terrain(root, box)
    REPORT[name] = dict(scale=round(s, 4), kz=round(kz, 3), bbox=[round(v, 2) for v in bb], box=list(box))
    return root


def build_range_v2(GC, box, name='Albani'):
    """20:10 메인: 산맥(여러 봉우리가 이어진 띠). 상자가 가로로 길면(가로:세로 ≥ 2) 이것으로 짓는다.
    굽은 능선 줄 위에 봉우리 N개(상자 비율 × 1.9), 봉우리마다 앞뒤로 뻗는 지능선 · 그 사이 골, 능선 하이라이트·바위·수풀"""
    aspect = (box[2] - box[0]) / max(1e-6, box[3] - box[1])
    RA, SY, H = 30.0, 0.34, 10.0
    ROT = 45.0                                                                   # 긴 축 = 화면 가로, 지역 −y = 카메라 쪽(앞)
    NP = max(4, int(round(aspect * 1.9)))                                      # 20:50 설계: 84×26(비율 3.2) → 봉우리 6
    peaks = [(-0.84 + 1.68 * (i + 0.5) / NP + 0.07 * _j(i, 11.1), 0.4 + 0.6 * _h(i, 11.2) ** 0.8) for i in range(NP)]
    wx = 1.3 / NP

    def yr(x):
        return 0.16 * math.sin(2.3 * x + 0.5)

    def zxy(x, y):
        d = y - yr(x)
        base = 0.5 * math.exp(-(d / 0.52) ** 2) * max(0.0, 1.0 - x * x) ** 0.5   # 이어진 능선(안부가 높다)
        pk = 0.75 * max(h * math.exp(-((x - px) / wx) ** 2) for px, h in peaks) * math.exp(-(d / 0.45) ** 2)
        spur = sum(0.14 * h * math.exp(-((x - px) / (wx * 0.32)) ** 2) * math.exp(-(abs(d) / 0.7) ** 1.4) for px, h in peaks)
        spur += sum(0.08 * math.exp(-((x - xm) / (wx * 0.25)) ** 2) * math.exp(-(abs(d) / 0.55) ** 1.4) for xm in [px + wx * 0.7 for px, h in peaks])
        return H * (base + pk + spur)

    def zf(t, a):
        if t >= 1.0:
            return 0.0
        z = zxy(t * math.cos(a), t * math.sin(a))
        return max(0.0, z * (1.0 if t < 0.88 else ((1.0 - t) / 0.12) ** 0.8))
    root = G.new_root('SUB_%s_root' % name, GC, 0.0, 0.0, 0.0)
    root.rotation_euler = (0.0, 0.0, math.radians(ROT))
    BM, X = ter_mats('hills')
    Ly = Lay(name, root, GC)
    b0 = Ly(0, 'Mass', BM)
    _polar_hf(b0, zf, RA, nr=34, na=120, sx=1.0, sy=SY)
    _hf_tone(b0, H * 1.1, 0, jit=lambda f: 0.05 * _j(int(f.calc_center_median().x * 2), int(f.calc_center_median().y * 2), 9.9))
    mass = Ly.finish()
    Ly = Lay(name, root, GC)

    def Pxy(x, y, dz=0.06):
        z = ray_z(mass, x * RA, y * RA * SY)
        return (x * RA, y * RA * SY, (z if z is not None else 0.0) + dz)
    mids = [(peaks[i][0] + peaks[i + 1][0]) / 2 for i in range(NP - 1)]
    b1 = Ly(1, 'Valleys', [X['valley'], X['pit']])
    for k, xm in enumerate(mids):                                                # 봉우리 사이 골(앞 사면, 능선 → 기슭)
        ribbon(b1, [Pxy(xm + 0.02 * math.sin(3 * i + k), yr(xm) - 0.1 - 0.08 * i, 0.07) for i in range(10)], 0.2, 0.05, 0, w1=0.7)
    for k, (px, h) in enumerate(peaks):                                          # 지능선 옆 작은 골
        for sg in (-1, 1):
            xg = px + sg * wx * 0.55
            ribbon(b1, [Pxy(xg, yr(xg) - 0.2 - 0.07 * i, 0.07) for i in range(8)], 0.18, 0.05, 0, w1=0.5)
    b2 = Ly(2, 'Paths', [X['path']])                                              # 기슭 옛길
    ribbon(b2, [Pxy(-0.85 + 1.7 * i / 30, -0.72 + 0.05 * math.sin(4 * i / 30.0 * math.pi), 0.1) for i in range(31)], 0.3, 0.05, 0)
    b3 = Ly(3, 'Strata', [X['lava'], X['ash']])                                   # 응회암 층 띠(앞 사면 등고선)
    for i, off in enumerate((0.3, 0.45, 0.6)):
        ribbon(b3, [Pxy(-0.85 + 1.7 * j / 40, yr(-0.85 + 1.7 * j / 40) - off, 0.08) for j in range(41)], 0.35, 0.05, i % 2)
    b4 = Ly(4, 'Rocks', [X['rim'], X['rock'], X['rock2']])
    for k, (px, h) in enumerate(peaks):                                          # 봉우리 바위 노두
        for j in range(5):
            x = px + wx * 0.6 * _j(k, j, 12.1); y = yr(x) + 0.12 * _j(k, j, 12.2) - 0.04
            q = Pxy(x, y, 0.0)
            blob(b4, (q[0], q[1], q[2] + 0.1), 0.5 + 0.3 * _h(k, j, 12.3), 0.4, 0.3, 5, 2, 0.3, 700 + 10 * k + j, (k + j) % 3)
    b5 = Ly(5, 'Ridges', [X['ridge'], X['ridge2']])
    ribbon(b5, [Pxy(-0.86 + 1.72 * j / 60, yr(-0.86 + 1.72 * j / 60), 0.14) for j in range(61)], 0.24, 0.05, 0)   # 주 능선
    for k, (px, h) in enumerate(peaks):                                          # 지능선(앞으로)
        ribbon(b5, [Pxy(px + 0.01 * math.sin(2 * i), yr(px) - 0.07 * i, 0.12) for i in range(5)], 0.13, 0.05, 1, w1=0.03)
    b6 = Ly(6, 'Scrub', [X['scrub'], X['scrub2']])
    for k in range(int(70 * aspect)):
        x = -0.9 + 1.8 * _h(k, 13.1); y = yr(x) - 0.15 - 0.75 * _h(k, 13.2)
        if x * x + (y / 1.0) ** 2 > 0.85:
            continue
        q = Pxy(x, y, 0.0)
        blob(b6, (q[0], q[1], q[2] + 0.2), 0.36 + 0.2 * _h(k, 13.3), 0.32, 0.26, 6, 2, 0.2, 800 + k, k % 2)
    Ly.finish()
    s, kz, bb = _fit_terrain(root, box)
    REPORT[name] = dict(scale=round(s, 4), kz=round(kz, 3), bbox=[round(v, 2) for v in bb], box=list(box), form='range', peaks=NP)
    return root


def terrain_boxes(ctx):
    """spec의 지형 상자: background V(projected_box) · terrain '베수비오'(projected_box/box) · terrain '알바노'(box). 없으면 임시 자리(TERRAIN_USE_TEMP)"""
    out = {}
    CM = ctx.CM
    cands = list(CM.get('background') or []) + list(CM.get('terrain') or [])
    for t in cands:
        nm = str(t.get('name', ''))
        bx_ = t.get('projected_box') or t.get('box')
        if not bx_:
            continue
        if nm.startswith('베수비오') and 'vesuvius' not in out:
            out['vesuvius'] = tuple(bx_)
        elif nm.startswith('알바노') and 'albani' not in out:
            out['albani'] = tuple(bx_)
    try:                                                              # 20:01 d5: spec terrain box는 null, 설계가 blender_changes.json terrain[].box.screen_box에 상자를 준다
        import os
        bc = json.load(open(os.path.join(os.path.dirname(SPEC), 'blender_changes.json'), encoding='utf-8'))
        for t in bc.get('terrain') or []:
            nm = str(t.get('name', ''))
            sb_ = (t.get('box') or {}).get('screen_box')
            if not sb_:
                continue
            if nm.startswith('베수비오') and 'vesuvius' not in out:
                out['vesuvius'] = tuple(sb_)
            elif nm.startswith('알바노') and 'albani' not in out:
                out['albani'] = tuple(sb_)
    except Exception:
        pass
    if TERRAIN_USE_TEMP:
        for k, v in TERRAIN_TEMP.items():
            out.setdefault(k, v)
    return out


def build(parts=None):
    """LM_Suburb만 지우고 다시 짓는다. 순서: 베수비오 → 먼 들 → 알바노(앞 능선·들·둔덕·채석장) → 농장(능선 위) → 메텔라 → 수레 → 가로수 → 빌라 → 앵커"""
    global _MC
    if parts is None:                                  # 16:14 core만: 메텔라 무덤(+대지)
        parts = ('vesuvius', 'farfields', 'albani', 'farm', 'metella', 'cart', 'appia_trees', 'villa') if DECOR else \
            ((('vesuvius', 'albani') if TERRAIN else ()) + ('metella',))
    _MC = {}
    REPORT.clear()
    ctx = Ctx()
    GC = R.coll(COLL, R.coll('ROMA_MAP'))
    R.clear_coll(COLL)
    ves = None
    if ctx.V is None:                                                  # 베수비오 spec이 없으면 베수비오·그에 기대는 지형 0
        parts = tuple(p_ for p_ in parts if p_ not in ('vesuvius', 'albani', 'farfields', 'farm'))
    if not any(str(t.get('name', '')).startswith('알바노') for t in _terrain_list(ctx.CM)):
        parts = tuple(p_ for p_ in parts if p_ != 'albani')            # 알바노 spec이 없으면 알바노 0
    if TERRAIN and TERRAIN_V2 and not DECOR:                          # 18:45 지형 v2: spec 상자(없으면 임시 자리)에 맞춰 화산·구릉 산맥
        tb_ = terrain_boxes(ctx)
        if 'vesuvius' in tb_:
            build_volcano_v2(GC, tb_['vesuvius'])
        if 'albani' in tb_:
            ab_ = tb_['albani']
            if (ab_[2] - ab_[0]) / max(1e-6, ab_[3] - ab_[1]) >= 2.0:     # 20:10: 가로로 긴 상자 = 산맥 띠
                build_range_v2(GC, ab_)
            else:
                build_hills_v2(GC, ab_)
        parts = tuple(p_ for p_ in parts if p_ not in ('vesuvius', 'albani', 'farfields', 'farm'))
    if 'vesuvius' in parts:
        ves, cone = build_vesuvius_cone(GC, ctx)
        build_vesuvius_layers(GC, ves, cone)
    if ves is not None and 'farfields' in parts:
        build_far_fields(GC, ctx, ves)
    if ves is not None and 'albani' in parts:
        build_albani(GC, ctx, ves)
    if ves is not None and 'farm' in parts and '_ridge' in REPORT:
        build_farm(GC, ctx, ves)
    if 'metella' in parts:
        build_metella(GC, ctx)
    if 'cart' in parts:
        build_cart(GC, ctx)
    if 'appia_trees' in parts:
        build_appia_trees(GC, ctx)
    if 'villa' in parts:
        build_villa(GC, ctx)
    build_anchors(GC, ctx)
    REPORT['_ctx'] = dict(hero_c=ctx.hero_c, hero_r=ctx.hero_r, hero_src=ctx.hero_src, ground=ground_hex(), pal_ground=FL.PAL.get('ground'))
    REPORT['_ves'] = ves
    return GC


def test_render(path, crop=(300.0, 88.0, 424.0, 372.0), max_layer=6, ppm=8.0, samples=16):
    """시험 렌더: LM_Suburb의 L(max_layer+1)~ 층만 잠깐 숨기고 render_region으로 렌더한 뒤 숨김·장면 렌더 설정을 모두 되돌린다"""
    sc = bpy.context.scene
    rs = sc.render
    keep = (rs.resolution_x, rs.resolution_y, rs.resolution_percentage, rs.use_border, rs.use_crop_to_border,
            rs.border_min_x, rs.border_max_x, rs.border_min_y, rs.border_max_y, rs.filepath,
            rs.image_settings.file_format, rs.image_settings.color_mode, getattr(sc.cycles, 'samples', None) if hasattr(sc, 'cycles') else None)
    obs = list(bpy.data.collections[COLL].all_objects)
    hid = []
    for o in obs:
        m = re.search(r'_L(\d)_', o.name)
        if o.type == 'MESH' and m and int(m.group(1)) > max_layer and not o.hide_render:
            hid.append(o)
    for o in hid:
        o.hide_render = True
    try:
        R.render_region(crop, ppm, samples, path)
    finally:
        for o in hid:
            o.hide_render = False
        (rs.resolution_x, rs.resolution_y, rs.resolution_percentage, rs.use_border, rs.use_crop_to_border,
         rs.border_min_x, rs.border_max_x, rs.border_min_y, rs.border_max_y, rs.filepath) = keep[:10]
        rs.image_settings.file_format, rs.image_settings.color_mode = keep[10], keep[11]
        if keep[12] is not None:
            sc.cycles.samples = keep[12]
    return len(hid)


def report(GC=None):
    """build() 뒤 실측·감사 요약(JSON에 담을 dict)"""
    GC = GC or bpy.data.collections.get(COLL)
    ctx = Ctx()
    ves = REPORT.get('_ves') or bpy.data.objects.get('SUB_Vesuvius_root')
    au, ext = audit(GC)
    ms = measure(GC, ctx, ves)
    out = {k: v for k, v in REPORT.items() if not k.startswith('_')}
    out['ctx'] = REPORT.get('_ctx')
    out['audit'] = au
    out['layer_audit_bglobal'] = ext
    out['measure'] = ms
    return out
