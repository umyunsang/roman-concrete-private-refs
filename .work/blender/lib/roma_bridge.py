# roma_bridge — 22:10·22:33 사용자: 하드리아누스 영묘 앞 다리를 레퍼런스(buildings/하드리아누스-영묘-다리/user_hadrian_bridge.jpg)대로. 담당: Blender-보완
# 물길(평면 X 방향으로 흐름)을 평면 Y 방향으로 직각으로 건너는 3아치 돌다리(가운데 아치가 가장 큼). 보이는 앞면 = 평면 +X 면.
# - 아치 발치(교각 밑)는 수면 아래, 교각 앞 물가르개 + 고깔 갓, 교각·교대 앞면 벽감(아이디큘라: 벽기둥 · 문턱 · 상인방 · 삼각 박공)
# - 거친 마름돌 홍예(긴·짧은 돌 번갈아, 쐐기돌), 아치 받침 띠, 처마 띠, 난간(받침 + 동자 기둥 줄 + 손잡이, 기둥받침 기둥)
# - 상판은 가운데가 살짝 솟은 활 모양, 양 끝은 둑 위 길로 이어지며 난간이 바깥으로 벌어져 넓어진다(교대는 둑에 묻힘)
# - 수면 반영(roma_aq_valley 방식: 높이 h인 점을 평면 (+h, +h)로 옮겨 수면에 그리면 화면에서 정확히 뒤집힌 실루엣) · 물가르개 둘레·아치 밑 물결
# 조명·AO·그림자 없음(방출 재질). 평면 (X, Y) → Blender (X, −Y, Z).
import bpy, bmesh, math
from mathutils import Vector
import roma_kit as R, roma_flat as FL, roma_geo as G
import roma_pkg_ground as GR

hsh = R.hash01
DEFS = {
    'stone': ('b', '#CDB48A', '#C3A97F', '#D6BF97', '#A88E68', 0.62, 0.3, 0.06),     # 풍화된 황토빛 사암·석회암 마름돌
    'deck': ('b', '#C9B591', '#BFAA85', '#D2BF9C', '#A7916D', 0.5, 0.5, 0.05),
    'rust1': ('f', '#C2A77C'), 'rust2': ('f', '#D3BC93'), 'key': ('f', '#DBC7A0'),
    'trim': ('f', '#D8C49E'), 'bal': ('f', '#D5C29C'), 'bal_dk': ('f', '#BCA57E'),
    'deep': ('f', '#5B4837'), 'niche': ('f', '#6A5643'), 'niche2': ('f', '#7E6850'),
    'hi': ('f', '#ECDFC1'), 'hi2': ('f', '#E3D3B0'),
    'stain1': ('f', '#A88F69'), 'stain2': ('f', '#8B7A64'), 'moss': ('f', '#7D8A4D'), 'moss2': ('f', '#98A061'),
}
M = {}


def mats():
    for k, d in DEFS.items():
        M[k] = FL.flat('F_hb_' + k, d[1]) if d[0] == 'f' else FL.blocks('F_hb_' + k, *d[1:])
    GM = GR.mats()
    for k in ('r_wave', 'foam', 'rock', 'rock_top'):
        M[k] = GM[k]
    M['water'] = GM['river']
    M['reflect'] = FL.flat('F_hb_reflect', FL.shade(FL.mix_hex('#C9B089', GR.WATER_HEX, 0.5), 0.9))
    M['reflect_lt'] = FL.flat('F_hb_reflectLt', FL.mix_hex('#D8C39C', GR.WATER_HEX, 0.45))
    return M


class Parts:
    """층·부분별 bmesh(재질 열쇠 목록) → 루트 아래 오브젝트 '{pk}_L{n}_{part}'"""
    def __init__(self, pk, coll, root):
        self.pk, self.coll, self.root, self.p = pk, coll, root, {}

    def bm(self, layer, part, *keys):
        k = (layer, part)
        if k not in self.p:
            self.p[k] = [bmesh.new(), list(keys)]
        return self.p[k][0]

    def mi(self, layer, part, key):
        return self.p[(layer, part)][1].index(key)

    def done(self):
        obs = []
        for (ly, part), (bm, keys) in self.p.items():
            if len(bm.faces) == 0:
                bm.free(); continue
            obs.append(G.finish(bm, '%s_L%d_%s' % (self.pk, ly, part), [M[k] for k in keys], self.coll, self.root))
        self.p = {}
        return obs


def sweep_yz(bm, pts, x0, x1, X0, Y0, kinds=None, mi_face=0, mi_of=None):
    """(y, z) 단순 다각형(평면 Y는 Y0 기준)을 평면 X 방향 X0+x0 ~ X0+x1로 내민 닫힌 입체. 변 i 옆면 재질 = mi_of(kinds[i])"""
    n = len(pts)
    A = [bm.verts.new((X0 + x1, -(Y0 + y), z)) for y, z in pts]
    B = [bm.verts.new((X0 + x0, -(Y0 + y), z)) for y, z in pts]
    fs = [bm.faces.new(A), bm.faces.new(B[::-1])]
    for f in fs:
        f.material_index = mi_face
    for i in range(n):
        j = (i + 1) % n
        f = bm.faces.new([A[i], B[i], B[j], A[j]])
        f.material_index = mi_of(kinds[i]) if (mi_of and kinds) else mi_face
        fs.append(f)
    return fs


def layout(W=12.0, z_w=-3.0, z_b=0.0, BW=2.4, hump=0.45, P=1.05, A=0.9, E=1.6, k_mid=1.35):
    """물길 폭 W(수면 z_w, 둑 윗면 z_b)를 건너는 다리 치수. y는 다리 축(평면 Y) 위 물길 가운데 기준"""
    s1 = (W - 2 * P - 2 * A) / (2 + k_mid); s2 = k_mid * s1
    h = W / 2.0
    spans = [(-h + A, -h + A + s1), (-s2 / 2, s2 / 2), (h - A - s1, h - A)]
    piers = [(-s2 / 2 - P, -s2 / 2), (s2 / 2, s2 / 2 + P)]
    Ye = h + E
    z_s = max(z_w + 0.5, z_b + hump - 1.05 - s2 / 2)
    return dict(W=W, h=h, z_w=z_w, z_b=z_b, BW=BW, hump=hump, P=P, A=A, E=E, Ye=Ye, spans=spans, piers=piers, z_s=z_s, zb0=z_w - 0.8,
                abut=[(-h, -h + A), (h - A, h)])


def z_top(L, y):
    t = min(1.0, abs(y) / L['Ye'])
    return L['z_b'] + L['hump'] * (1.0 - t * t)


def body_outline(L):
    """앞에서 본 몸 윤곽(y, z)과 변 종류(점 i에서 시작하는 변: bottom · arch · end · deck)"""
    zb0, z_s, Ye = L['zb0'], L['z_s'], L['Ye']
    P, K = [], []
    add = lambda p, k: (P.append(p), K.append(k))
    add((-Ye, zb0), 'bottom')
    for (a, b) in L['spans']:
        r = (b - a) / 2; c = (a + b) / 2
        add((a, zb0), 'arch'); add((a, z_s), 'arch')
        for k in range(1, 16):
            add((c + r * math.cos(math.pi * (1 - k / 16.0)), z_s + r * math.sin(math.pi * (1 - k / 16.0))), 'arch')
        add((b, z_s), 'arch'); add((b, zb0), 'bottom')
    add((Ye, zb0), 'end')
    for k in range(49):
        y = Ye - 2 * Ye * k / 48.0
        add((y, z_top(L, y)), 'deck' if k < 48 else 'end')
    return P, K


def build(GC, X0, Y0, L, pk='HB_Bridge', water_poly=None, seed=0.0):
    """다리 한 채. 루트 '{pk}_root'(평면 X0, Y0 · 회전 0). water_poly(볼록, 평면)가 있으면 그 안에 반영·물결을 자른다. 반환: 루트"""
    if not M:
        mats()
    root = bpy.data.objects.new(pk + '_root', None); GC.objects.link(root)
    Pt = Parts(pk, GC, root)
    BW, zb0, z_s, z_w, Ye = L['BW'], L['zb0'], L['z_s'], L['z_w'], L['Ye']
    xf = BW / 2.0                                                            # 앞면(평면 +X) 지역 x
    Xf = X0 + xf
    fm = lambda u, v, d: Vector((Xf + d, -(Y0 + u), v))                       # 앞면: u = 평면 y(Y0 기준), v = z, d = 앞으로
    # ── L0 몸(앞·뒷면 마름돌 · 아치 속 짙게 · 상판 포장)
    b0 = Pt.bm(0, 'Body', 'stone', 'deep', 'deck')
    Pq, Kq = body_outline(L)
    sweep_yz(b0, Pq, -xf, xf, X0, Y0, Kq, 0, lambda k: {'arch': 1, 'deck': 2}.get(k, 0))
    # ── L2 처마 띠(활 모양) · 아치 받침 띠 · 홍예(거친 마름돌) · 물가르개 · 벽감 틀 / L1 벽감 속
    b2 = Pt.bm(2, 'Members', 'trim', 'rust1', 'rust2', 'key', 'stone')
    b1 = Pt.bm(1, 'Depth', 'niche', 'niche2', 'deep')
    ys = [-Ye + 2 * Ye * k / 60.0 for k in range(61)]
    band = lambda d0, d1: [(y, z_top(L, y) + d0) for y in ys] + [(y, z_top(L, y) + d1) for y in ys[::-1]]
    sweep_yz(b2, band(-0.44, -0.22), xf, xf + 0.15, X0, Y0)                   # 처마 띠
    sweep_yz(b2, band(-0.5, -0.44), xf, xf + 0.07, X0, Y0)                    # 띠 밑 작은 쇠시리
    for (p0, p1) in L['piers'] + L['abut']:
        uz = lambda lp, d0, d1, mi: _uz(b2, lp, fm, d0, d1, mi)
        uz([(p0 - 0.12, z_s - 0.14), (p1 + 0.12, z_s - 0.14), (p1 + 0.12, z_s + 0.02), (p0 - 0.12, z_s + 0.02)], 0.0, 0.07, 0)
    for ai, (a, b) in enumerate(L['spans']):
        r = (b - a) / 2.0; c = (a + b) / 2.0
        nv = 15 if ai == 1 else 11
        for k in range(nv):
            g0 = 180.0 * k / nv + 0.6; g1 = 180.0 * (k + 1) / nv - 0.6
            mid = k == nv // 2
            r_out = r + (0.62 if mid else (0.46 if k % 2 else 0.34))
            _band(b2, fm, c, z_s, r + 0.01, r_out, 0.0, 0.12 if mid else 0.07, 3 if mid else 1 + k % 2, g0, g1)
    for pi_, (p0, p1) in enumerate(L['piers']):                              # 물가르개(앞으로 뾰족) + 고깔 갓
        pc = (p0 + p1) / 2.0; zc = z_s - 0.15
        tri = [(Xf, -(Y0 + p0)), (Xf + 0.8, -(Y0 + pc)), (Xf, -(Y0 + p1))]
        G.prism(b2, tri, zb0, zc, 4)
        v = [b2.verts.new((x, y, zc)) for x, y in tri]
        ap = b2.verts.new((Xf + 0.14, -(Y0 + pc), zc + 0.5))
        for i in range(3):
            f = b2.faces.new([v[i], v[(i + 1) % 3], ap]); f.material_index = 0
    for (p0, p1) in L['piers'] + L['abut']:                                  # 벽감(아이디큘라)
        pc = (p0 + p1) / 2.0; w = min(0.52, (p1 - p0) * 0.42)
        n0 = z_s + 0.55; n1 = min(z_top(L, pc) - 0.95, n0 + 1.25)
        if n1 - n0 < 0.6:
            continue
        _uz(b1, _arch_loop(pc - w / 2, pc + w / 2, n0, n1 - w / 2), fm, 0.0, 0.012, 0)
        _uz(b1, _arch_loop(pc - w / 2 + 0.06, pc + w / 2 - 0.06, n0, n0 + (n1 - n0) * 0.45), fm, 0.0, 0.016, 1)   # 벽감 속 빈 받침(조금 밝게)
        for sx in (-1, 1):
            q0 = pc + sx * (w / 2 + 0.03); q1 = pc + sx * (w / 2 + 0.15)
            _uz(b2, [(min(q0, q1), n0 - 0.05), (max(q0, q1), n0 - 0.05), (max(q0, q1), n1 + 0.02), (min(q0, q1), n1 + 0.02)], fm, 0.0, 0.05, 0)
        _uz(b2, [(pc - w / 2 - 0.22, n0 - 0.16), (pc + w / 2 + 0.22, n0 - 0.16), (pc + w / 2 + 0.22, n0 - 0.04), (pc - w / 2 - 0.22, n0 - 0.04)], fm, 0.0, 0.08, 0)
        _uz(b2, [(pc - w / 2 - 0.22, n1 + 0.02), (pc + w / 2 + 0.22, n1 + 0.02), (pc + w / 2 + 0.22, n1 + 0.14), (pc - w / 2 - 0.22, n1 + 0.14)], fm, 0.0, 0.08, 0)
        _uz(b2, [(pc - w / 2 - 0.26, n1 + 0.14), (pc + w / 2 + 0.26, n1 + 0.14), (pc, n1 + 0.48)], fm, 0.0, 0.09, 0)
    # ── L4 난간: 받침·손잡이(활 모양) · 동자 기둥 줄 · 기둥받침 기둥 / 양 끝 벌어진 난간(둑 위)
    b4 = Pt.bm(4, 'Balustrade', 'bal', 'bal_dk', 'trim')
    for sx in (1, -1):
        xa, xb = (xf - 0.28, xf + 0.02) if sx > 0 else (-xf - 0.02, -xf + 0.28)
        sweep_yz(b4, band(0.0, 0.12), xa, xb, X0, Y0, None, 2)
        sweep_yz(b4, band(0.44, 0.56), xa - 0.02 * sx, xb + 0.02 * sx, X0, Y0, None, 2)
        y = -Ye + 0.2; k = 0
        while y < Ye - 0.15:
            zt = z_top(L, y)
            xc = X0 + (xf - 0.13 if sx > 0 else -xf + 0.13)
            G.cyl(b4, xc, -(Y0 + y), 0.055, zt + 0.12, zt + 0.44, 6, 0 if sx > 0 else 1, r_top=0.04, top=False)
            y += 0.19; k += 1
        posts = sorted(set([-Ye + 0.12, Ye - 0.12, 0.0] + [(p0 + p1) / 2.0 for p0, p1 in L['piers']] + [s * L['h'] for s in (-1, 1)]))
        for y in posts:
            zt = z_top(L, y)
            G.box(b4, X0 + xa - 0.03, X0 + xb + 0.03, -(Y0 + y) - 0.17, -(Y0 + y) + 0.17, zt, zt + 0.64, 2)
    for sy in (-1, 1):                                                       # 양 끝: 둑 위로 벌어지는 난간(평면 45°)
        for sx in (1, -1):
            p0 = (X0 + sx * xf, Y0 + sy * Ye); p1 = (X0 + sx * (xf + 1.5), Y0 + sy * (Ye + 1.5))
            _bal_seg(b4, p0, p1, L['z_b'])
    # ── L3 상판 판석 줄 · 끝 넓어진 길 판석 · 물결
    b3 = Pt.bm(3, 'Paving', 'deck', 'bal_dk', 'hi2')
    y = -Ye + 0.3
    while y < Ye - 0.2:
        zt = z_top(L, y)
        G.box(b3, X0 - xf + 0.3, X0 + xf - 0.3, -(Y0 + y) - 0.02, -(Y0 + y) + 0.02, zt, zt + 0.012, 1)
        y += 0.55
    for sy in (-1, 1):
        y0 = Y0 + sy * Ye; y1 = Y0 + sy * (Ye + 1.5)
        pts = [(X0 - xf, y0), (X0 + xf, y0), (X0 + xf + 1.5, y1), (X0 - xf - 1.5, y1)]
        G.prism(b3, [(x, -y) for x, y in pts], L['z_b'], L['z_b'] + 0.03, 0)
    # ── L5 하이라이트(처마 띠 윗선 · 손잡이 윗선 · 물가르개 갓 앞면 · 쐐기돌)
    b5 = Pt.bm(5, 'Highlights', 'hi', 'hi2')
    sweep_yz(b5, band(-0.245, -0.215), xf + 0.15, xf + 0.165, X0, Y0, None, 0)
    sweep_yz(b5, band(0.545, 0.565), xf - 0.3, xf + 0.04, X0, Y0, None, 0)
    for ai, (a, b) in enumerate(L['spans']):
        r = (b - a) / 2.0; c = (a + b) / 2.0
        _band(b5, fm, c, z_s, r + 0.42, r + 0.6, 0.12, 0.135, 1, 85.0, 95.0)
    # ── L6 2단 얼룩(처마 밑 짙은 물때 · 황토 씻김) · 물가 이끼 띠 · 교대 덩굴
    b6 = Pt.bm(6, 'Weather', 'stain1', 'stain2', 'moss', 'moss2')
    for j in range(int(2 * Ye / 0.7)):
        u = -Ye + 0.3 + (2 * Ye - 0.6) * hsh(j, seed, 61.1)
        zt = z_top(L, u) - 0.5
        if any(a + 0.05 < u < b - 0.05 for a, b in L['spans']):
            r_ = next((b - a) / 2.0 for a, b in L['spans'] if a < u < b); c_ = next((a + b) / 2.0 for a, b in L['spans'] if a < u < b)
            zlo = z_s + math.sqrt(max(0.0, r_ * r_ - (u - c_) ** 2)) + 0.5
        else:
            zlo = z_w + 0.1
        if zt - zlo < 0.3:
            continue
        w = 0.15 + 0.35 * hsh(j, seed, 61.2); Ls = (zt - zlo) * (0.3 + 0.7 * hsh(j, seed, 61.3))
        _uz(b6, [(u, zt - Ls), (u + w * 0.6, zt - Ls * 0.85), (u + w, zt), (u, zt)], fm, 0.0, 0.18, j % 2)
    for (p0, p1) in L['piers'] + L['abut']:
        _uz(b6, [(p0, z_w - 0.05), (p1, z_w - 0.05), (p1, z_w + 0.35 + 0.2 * hsh(p0, 61.4)), (p0, z_w + 0.28)], fm, 0.0, 0.02, 2)
    for (p0, p1) in L['piers']:
        pc = (p0 + p1) / 2.0
        for sy in (-1, 1):
            q = pc + sy * (p1 - p0) / 4.0
            _uz(b6, [(q - 0.25, z_w - 0.05), (q + 0.25, z_w - 0.05), (q + 0.2, z_w + 0.4), (q - 0.2, z_w + 0.35)], lambda u, v, d, pc=pc, p0=p0, p1=p1: Vector((Xf + 0.8 * (1 - abs(u - pc) / ((p1 - p0) / 2)) + 0.03 + d, -(Y0 + u), v)), 0.0, 0.02, 3)
    for sy in (-1, 1):
        a = sy * (L['h'] - L['A'] * 0.5)
        _uz(b6, [(a - 0.5, z_s + 0.7), (a + 0.5, z_s + 0.7), (a + 0.3, z_top(L, a) - 0.5), (a - 0.35, z_top(L, a) - 0.6)], fm, 0.0, 0.11, 3)
    Pt.done()
    # ── 물: 반영(L5) · 물결(L3) — 수면 위 평면 일러스트
    if water_poly is not None:
        reflection(GC, pk, root, X0, Y0, L, water_poly)
        ripples(GC, pk, root, X0, Y0, L, water_poly, seed)
    return root


def _uz(bm, loop, fmap, d0, d1, mi):
    F = [bm.verts.new(fmap(u, v, d1)) for u, v in loop]
    B = [bm.verts.new(fmap(u, v, d0)) for u, v in loop]
    fs = [bm.faces.new(F), bm.faces.new(B[::-1])]
    n = len(loop)
    for i in range(n):
        j = (i + 1) % n
        fs.append(bm.faces.new([F[i], B[i], B[j], F[j]]))
    for f in fs:
        f.material_index = mi
    return fs


def _arch_loop(u0, u1, v0, vs, n=8):
    rr = (u1 - u0) / 2; cu = (u0 + u1) / 2
    return [(u0, v0), (u1, v0)] + [(cu + rr * math.cos(math.pi * j / n), vs + rr * math.sin(math.pi * j / n)) for j in range(n + 1)]


def _band(bm, fmap, cu, vs, r_in, r_out, d0, d1, mi, a0, a1):
    t0, t1 = math.radians(a0), math.radians(a1)
    lp = [(cu + r_in * math.cos(t0), vs + r_in * math.sin(t0)), (cu + r_out * math.cos(t0), vs + r_out * math.sin(t0)),
          (cu + r_out * math.cos(t1), vs + r_out * math.sin(t1)), (cu + r_in * math.cos(t1), vs + r_in * math.sin(t1))]
    return _uz(bm, lp, fmap, d0, d1, mi)


def _bal_seg(bm, p0, p1, z0):
    """평면 선분 p0→p1 위 난간(받침 · 손잡이 · 동자 기둥 · 끝 기둥), 바닥 z0"""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    Ls = math.hypot(dx, dy); ux, uy = dx / Ls, dy / Ls; nx, ny = -uy, ux
    def slab(za, zb_, hw, mi):
        pts = [(p0[0] + nx * hw, p0[1] + ny * hw), (p1[0] + nx * hw, p1[1] + ny * hw), (p1[0] - nx * hw, p1[1] - ny * hw), (p0[0] - nx * hw, p0[1] - ny * hw)]
        G.prism(bm, [(x, -y) for x, y in pts], za, zb_, mi)
    slab(z0, z0 + 0.12, 0.15, 2)
    slab(z0 + 0.44, z0 + 0.56, 0.16, 2)
    s = 0.2
    while s < Ls - 0.1:
        G.cyl(bm, p0[0] + ux * s, -(p0[1] + uy * s), 0.055, z0 + 0.12, z0 + 0.44, 6, 0, r_top=0.04, top=False)
        s += 0.19
    G.box(bm, p1[0] - 0.18, p1[0] + 0.18, -p1[1] - 0.18, -p1[1] + 0.18, z0, z0 + 0.68, 2)


def _clip(poly, region):
    import roma_aq_valley as AQ
    return AQ._clip(poly, region)


def reflection(GC, pk, root, X0, Y0, L, water_poly):
    """앞면 실루엣(몸 + 처마 + 난간)의 수면 반영(L5): 수면 위 높이 h인 앞면 점 (y, z) → 평면 (Xf + h, Y0 + y + h)"""
    a5 = GR.Acc()
    z_w, xf = L['z_w'], L['BW'] / 2.0
    Xf = X0 + xf
    Pq, _ = body_outline(L)
    Ye = L['Ye']
    ys = [-Ye + 2 * Ye * k / 60.0 for k in range(61)]
    top = [(y, z_top(L, y) + 0.56) for y in ys]
    above = GR.clip_half([(y, z) for y, z in Pq], lambda p: z_w - p[1])        # 수면 위만
    parts = [above, [(y, z_top(L, y)) for y in ys] + top[::-1]]
    for (p0, p1) in L['piers']:                                               # 물가르개 앞 끝(앞으로 0.8) 반영
        pc = (p0 + p1) / 2.0; zc = L['z_s'] - 0.15
        h = zc - z_w
        pts = [(Xf, Y0 + p0), (Xf + h, Y0 + p0 + h), (Xf + 0.8 + h, Y0 + pc + h), (Xf + 0.8, Y0 + pc)]
        cl = _clip(pts, water_poly)
        if len(cl) >= 3:
            a5.face([GR.V(x, y, z_w + 0.012) for x, y in cl], M['reflect'], (0, 0, 1))
    for poly in parts:
        if len(poly) < 3:
            continue
        pts = [(Xf + max(0.0, z - z_w), Y0 + y + max(0.0, z - z_w)) for y, z in poly]
        cl = _clip(pts, water_poly)
        if len(cl) >= 3:
            a5.face([GR.V(x, y, z_w + 0.012) for x, y in cl], M['reflect'], (0, 0, 1))
    def mapped(poly, z_add, mat):
        pts = [(Xf + max(0.0, z - z_w), Y0 + y + max(0.0, z - z_w)) for y, z in poly]
        cl = _clip(pts, water_poly)
        if len(cl) >= 3:
            a5.face([GR.V(x, y, z_w + z_add) for x, y in cl], mat, (0, 0, 1))
    for (a, b) in L['spans']:                                                 # 홍예 고리 · 처마 띠 반영(밝게)
        r = (b - a) / 2.0; c = (a + b) / 2.0
        for k in range(8):
            t0, t1 = math.pi * k / 8, math.pi * (k + 1) / 8
            mapped([(c + r * math.cos(t0), L['z_s'] + r * math.sin(t0)), (c + (r + 0.4) * math.cos(t0), L['z_s'] + (r + 0.4) * math.sin(t0)),
                    (c + (r + 0.4) * math.cos(t1), L['z_s'] + (r + 0.4) * math.sin(t1)), (c + r * math.cos(t1), L['z_s'] + r * math.sin(t1))], 0.016, M['reflect_lt'])
    for k in range(60):
        ya, yb = ys[k], ys[k + 1]
        mapped([(ya, z_top(L, ya) - 0.44), (yb, z_top(L, yb) - 0.44), (yb, z_top(L, yb) - 0.22), (ya, z_top(L, ya) - 0.22)], 0.016, M['reflect_lt'])
    for j in range(26):                                                       # 반영을 끊는 화면 가로 물결 줄(평면 (1, −1) 방향)
        cx = Xf + 0.4 + 3.6 * hsh(j, 81.1); cy = Y0 - L['h'] + 0.5 + (2 * L['h'] - 1.0) * hsh(j, 81.2); w = 0.3 + 0.7 * hsh(j, 81.3)
        ux, uy = 0.7071 * w, -0.7071 * w; nx, ny = 0.035, 0.035
        cl = _clip([(cx - ux - nx, cy - uy - ny), (cx + ux - nx, cy + uy - ny), (cx + ux + nx, cy + uy + ny), (cx - ux + nx, cy - uy + ny)], water_poly)
        if len(cl) >= 3:
            a5.face([GR.V(x, y, z_w + 0.02) for x, y in cl], M['r_wave'], (0, 0, 1))
    return a5.obj(pk + '_L5_Reflection', GC, root)


def ripples(GC, pk, root, X0, Y0, L, water_poly, seed=0.0):
    """물가르개 앞 초승달 물결 2~3겹 · 아치 밑 가로 물결 줄(L3)"""
    a3 = GR.Acc()
    z_w, Xf = L['z_w'], X0 + L['BW'] / 2.0
    for (p0, p1) in L['piers']:
        pc = (p0 + p1) / 2.0; hw = (p1 - p0) / 2.0
        for k in range(3):
            r0 = hw + 0.35 + 0.5 * k; r1 = r0 + 0.12
            o = [(Xf + 0.4 + r1 * 0.9 * math.sin(math.pi * j / 10), Y0 + pc - r1 * math.cos(math.pi * j / 10)) for j in range(11)]
            i_ = [(Xf + 0.4 + r0 * 0.9 * math.sin(math.pi * j / 10), Y0 + pc - r0 * math.cos(math.pi * j / 10)) for j in range(10, -1, -1)]
            a3.face([GR.V(x, y, z_w + 0.02) for x, y in o + i_], M['foam'] if k == 0 else M['r_wave'], (0, 0, 1))
    for (a, b) in L['spans']:
        for k in range(5):
            u0 = a + (b - a) * (0.1 + 0.6 * hsh(k, a, seed, 71.1)); w = (b - a) * (0.15 + 0.25 * hsh(k, a, 71.2))
            x = Xf + 0.3 + 2.4 * hsh(k, a, 71.3)
            pts = [(x, Y0 + u0), (x + 0.07, Y0 + u0), (x + 0.07, Y0 + u0 + w), (x, Y0 + u0 + w)]
            cl = _clip(pts, water_poly)
            if len(cl) >= 3:
                a3.face([GR.V(px, py, z_w + 0.02) for px, py in cl], M['r_wave'], (0, 0, 1))
    return a3.obj(pk + '_L3_Ripples', GC, root)


# ───────────────────────── 시험 장면(시험 물길 폭 W · 둑 석축 · 둑 위 길) — 끝나면 clear_test()로 지운다 ─────────────────────────
TEST_COLL = 'TEST_Bridge'


def test_scene(X0=150.0, Y0=110.0, W=12.0, z_w=-3.0, half_x=16.0, bank=14.0):
    import roma_diorama as DI
    GC = R.coll(TEST_COLL, bpy.context.scene.collection)
    R.clear_coll(TEST_COLL)
    DM = DI.mats()
    keep = DI.WATER_Z
    DI.WATER_Z = z_w
    try:
        h = W / 2.0
        for bid, (ya, yb) in (('TB_N', (Y0 - h - bank, Y0 - h)), ('TB_S', (Y0 + h, Y0 + h + bank))):
            DI.build_block(GC, DM, {'id': bid, 'poly': [(X0 - half_x, ya), (X0 + half_x, ya), (X0 + half_x, yb), (X0 - half_x, yb)], 'z': 0.0,
                                    'kind': 'ashlar', 'unit': 0.34}, seed=3.0 if bid == 'TB_N' else 9.0)
    finally:
        DI.WATER_Z = keep
    L = layout(W, z_w, 0.0)
    wp = [(X0 - half_x, Y0 - h), (X0 + half_x, Y0 - h), (X0 + half_x, Y0 + h), (X0 - half_x, Y0 + h)]
    aw = GR.Acc()
    aw.face([GR.V(x, y, z_w) for x, y in wp], mats()['water'], (0, 0, 1))
    aw.obj('TB_L0_Water', GC)
    ar = GR.Acc()
    for (ya, yb) in ((Y0 - h - bank, Y0 - L['Ye'] - 1.5), (Y0 + L['Ye'] + 1.5, Y0 + h + bank)):
        ar.box(X0 - L['BW'] / 2 - 0.4, X0 + L['BW'] / 2 + 0.4, ya, yb, 0.0, 0.03, DM['slab'], DM['slab_side'])
    ar.obj('TB_L3_Road', GC)
    root = build(GC, X0, Y0, L, 'TB_Bridge', wp)
    return GC, root, L


def render_test(path, pad=2.0, ppm=10.0, samples=16):
    """시험 장면만 보이게(다른 컬렉션 렌더 숨김, 끝나면 되돌림) 화면 상자 렌더"""
    sc = bpy.context.scene
    GC = bpy.data.collections[TEST_COLL]
    xs, ys = [], []
    for ob in GC.all_objects:
        if ob.type != 'MESH':
            continue
        for c in ob.bound_box:
            x, y = R.scr(ob.matrix_world @ Vector(c)); xs.append(x); ys.append(y)
    box = (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
    keep = {}
    for c in sc.collection.children:
        if c.name != TEST_COLL:
            keep[c.name] = c.hide_render; c.hide_render = True
    try:
        R.render_region(box, ppm, samples, path)
    finally:
        for k, v in keep.items():
            bpy.data.collections[k].hide_render = v
    return box


def clear_test():
    c = bpy.data.collections.get(TEST_COLL)
    if c is None:
        return
    R.clear_coll(TEST_COLL)
    bpy.data.collections.remove(c)
