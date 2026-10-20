# roma_terrain_persp — 21:45 사용자: 산맥·화산을 작은 모서리 판이 아니라 실제 지리 크기로 창 밖까지 이어지는 큰 지형으로.
# 등각 정사영에는 원근이 없으므로 '거리 배율'로 원근 축소를 흉내 낸다. 담당: Blender-보완
#   · 지형은 실제 지리 평면(참 좌표)에서 정의한다: 알바노 구릉(남동) · 아펜니노(동·북동 멀리) · 베수비오(남동 아주 멀리)
#   · 지도 중심 c(Core 군집)에서 그린 거리 d의 배율 s(d): 군집 가장자리 1.0 → 창 가장자리 0.55 → 창 밖 0.4
#   · 그린 거리 d ↔ 참 거리 D = ∫0^d 1/s(r) dr(방위마다). 그린 점 p의 높이 = s(d) · H참(c + D·u) → 평면 크기·높이가 함께 줄고 땅(Z 0)에 붙는다
#   · 대기 원근: L0 색 = 지형색과 엷은 대기색을 거리 함수 a(s)로 섞는다(6단계 양자화)
#   · 땅 판 위로 솟아 이어진다(평평한 곳 Z < 0.06은 짓지 않아 땅 판이 그대로 보인다). 별도 섬 블록이 아니다
import bpy, bmesh, math, json
from mathutils import Vector
import roma_kit as R, roma_flat as FL, roma_geo as G
import roma_pkg_ground as GR

COLL = 'MAP_TerrainP'
V = GR.V
hsh = R.hash01
Acc = GR.Acc
WINDOW_PLAN = [(92.0, 92.0), (334.49, -150.49), (720.49, 235.51), (478.0, 478.0)]   # 화면 창 [0, 92, 420, 478]의 평면 사변형
HAZE_HEX = '#E6DFCF'          # 대기색(땅색과 하늘색 사이)
NH = 6                        # 대기 원근 단계


def _ray_poly(c, u, poly):
    """c에서 방향 u로 나간 반직선이 다각형 경계와 처음 만나는 거리(없으면 None)"""
    best = None
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        ex, ey = b[0] - a[0], b[1] - a[1]
        den = u[0] * ey - u[1] * ex
        if abs(den) < 1e-12:
            continue
        t = ((a[0] - c[0]) * ey - (a[1] - c[1]) * ex) / den
        v = ((a[0] - c[0]) * u[1] - (a[1] - c[1]) * u[0]) / den
        if t > 0 and -1e-9 <= v <= 1 + 1e-9:
            best = t if best is None else min(best, t)
    return best


class Field:
    """거리 배율 s(d)·참 거리 D(d)·참 높이 H(q)를 방위마다 표로 갖는다"""
    def __init__(self, P):
        self.c = tuple(P['center']); self.d0 = float(P['d0'])
        self.s_edge, self.s_out = float(P.get('s_edge', 0.55)), float(P.get('s_out', 0.4))
        self.t_out = float(P.get('t_out', 1.6))
        self.feats = P['features']
        self.window = [tuple(p) for p in P.get('window', WINDOW_PLAN)]

    def s_of(self, r, edge):
        t = (r - self.d0) / max(1e-6, edge - self.d0)
        if t <= 0.0:
            return 1.0
        if t <= 1.0:
            return 1.0 - (1.0 - self.s_edge) * (3 * t * t - 2 * t * t * t)
        if t <= self.t_out:
            return self.s_edge - (self.s_edge - self.s_out) * (t - 1.0) / (self.t_out - 1.0)
        return self.s_out

    def ray_table(self, th, r_max, dr):
        u = (math.cos(th), math.sin(th))
        edge = _ray_poly(self.c, u, self.window) or (self.d0 + 200.0)
        edge = max(edge, self.d0 + 20.0)
        rs, ss, Ds = [0.0], [1.0], [0.0]
        r = 0.0
        while r < r_max:
            r2 = r + dr
            s1, s2 = self.s_of(r, edge), self.s_of(r2, edge)
            Ds.append(Ds[-1] + dr * 0.5 * (1.0 / s1 + 1.0 / s2)); rs.append(r2); ss.append(s2)
            r = r2
        return u, rs, ss, Ds, edge

    def H(self, X, Y):
        """참 평면 (X, Y)의 참 높이와 지형 종류 번호(가장 높은 기여)"""
        z, kind = 0.0, -1
        for k, f in enumerate(self.feats):
            if f['kind'] in ('cone', 'massif'):
                dx, dy = X - f['c'][0], Y - f['c'][1]
            if f['kind'] == 'cone':
                rr = math.hypot(dx, dy) / f['r']
                if rr < 1.0:
                    a = math.atan2(dy, dx)
                    g = 1.0 - 0.12 * rr * (0.5 + 0.5 * math.cos(14 * a))
                    hz = f['h'] * ((1.0 - rr) ** 1.5) * g
                    if rr < 0.12:
                        hz = f['h'] * (0.88 ** 1.5) - f['h'] * 0.06 * (1.0 - rr / 0.12)
                else:
                    hz = 0.0
            elif f['kind'] == 'massif':
                rr = math.hypot(dx, dy) / f['r']
                if rr < 1.0:
                    a = math.atan2(dy, dx)
                    hz = f['h'] * (0.32 * (1 - rr * rr) ** 0.9 + 0.5 * math.exp(-((rr - 0.58) / 0.14) ** 2) * (0.65 + 0.35 * math.cos(5 * a + 0.4))
                                   + 0.75 * math.exp(-(rr / 0.2) ** 2))
                    hz *= 1.0 if rr < 0.88 else ((1.0 - rr) / 0.12) ** 0.8
                else:
                    hz = 0.0
            else:                                                           # 'range': 굽은 능선 띠(능선 점 목록 + 폭)
                best = None
                pts = f['ridge']
                for i in range(len(pts) - 1):
                    ax, ay = pts[i]; bx, by = pts[i + 1]
                    ex, ey = bx - ax, by - ay; L2 = ex * ex + ey * ey
                    t = max(0.0, min(1.0, ((X - ax) * ex + (Y - ay) * ey) / L2))
                    d = math.hypot(X - ax - ex * t, Y - ay - ey * t)
                    if best is None or d < best[0]:
                        best = (d, i + t)
                d, sidx = best
                w = f['w']
                if d < w:
                    q = d / w
                    pk = 0.55 + 0.45 * (0.5 + 0.5 * math.cos(sidx * f.get('peaks_per_seg', 3.0) * 2 * math.pi + 0.7)) * (0.7 + 0.3 * math.sin(sidx * 5.3))
                    spur = 0.08 * math.cos(sidx * 9.0) * q * (1 - q)
                    hz = f['h'] * (pk * math.exp(-(q / 0.42) ** 2) + 0.18 * (1 - q * q) + spur)
                    hz *= 1.0 if q < 0.85 else ((1.0 - q) / 0.15) ** 0.8
                else:
                    hz = 0.0
            if hz > z:
                z, kind = hz, k
        return z, kind


def mats(colors):
    """색 표: 지형마다 높이 띠 3 × 면 톤 3 × 대기 단계 NH"""
    M = {}
    for name, bands in colors.items():
        for i in range(3):
            for j in range(3):
                for h in range(NH):
                    a = 0.12 + 0.55 * h / (NH - 1)
                    M[(name, i, j, h)] = FL.flat('F_tp_%s_%d%d_h%d' % (name, i, j, h), FL.mix_hex(bands[i][j], HAZE_HEX, a))
    for name, bands in colors.items():                                     # 산자락(땅색에 스며든다)
        for h in range(NH):
            a = 0.12 + 0.55 * h / (NH - 1)
            M[(name, 'skirt', h)] = FL.flat('F_tp_%s_skirt_h%d' % (name, h), FL.mix_hex(FL.mix_hex(bands[0][1], GR.GROUND_HEX, 0.62), HAZE_HEX, a * 0.5))
    extra = dict(valley='#6E6A57', rock='#857A6E', rock2='#A39888', ridge='#E2DAC6', ash='#B8AE9C', scrub='#7E8B55', scrub2='#93985F', path='#D2C2A0')
    for k, v in extra.items():
        for h in range(NH):
            a = 0.12 + 0.55 * h / (NH - 1)
            M[(k, h)] = FL.flat('F_tp_%s_h%d' % (k, h), FL.mix_hex(v, HAZE_HEX, a))
    return M


COLORS = {
    'volcano': (('#A7AE79', '#8E9A63', '#76825A'), ('#B9A989', '#A08F72', '#857660'), ('#C9C1B2', '#ADA597', '#918A7E')),
    'hills': (('#AEB47F', '#96A06B', '#7F8A5C'), ('#B8B289', '#A19B77', '#8A8466'), ('#C3BC9D', '#ABA486', '#948E73')),
    'range': (('#A8AE80', '#8F9868', '#78825A'), ('#B3AA8C', '#9B9277', '#827A64'), ('#D7D3CB', '#BDB8AE', '#A19C92')),
}


def haze_level(s):
    return max(0, min(NH - 1, int(round((1.0 - (s - 0.4) / 0.6) * (NH - 1)))))


def build(P, GC=None):
    """P = {'center', 'd0', 's_edge', 's_out', 'features': [{'name','kind','c','r'|'ridge','w','h','color'}], 'sector': [θ0, θ1](도), 'r_max', 'dr', 'dth'}"""
    GC = GC or R.coll(COLL, R.coll('ROMA_MAP'))
    F = Field(P)
    M = mats(COLORS)
    root = bpy.data.objects.new('TERR_Persp_root', None); GC.objects.link(root)
    th0, th1 = [math.radians(v) for v in P['sector']]
    dth = math.radians(P.get('dth', 0.75)); r_max = P.get('r_max', 640.0); dr = P.get('dr', 2.5)
    nth = int((th1 - th0) / dth) + 1
    rays = [F.ray_table(th0 + (th1 - th0) * i / (nth - 1), r_max, dr) for i in range(nth)]
    nr = len(rays[0][1])
    cx, cy = F.c
    grid = []                                                                 # [i][j] = (X, Y, z, s, kind, Ztrue_frac)
    for (u, rs, ss, Ds, edge) in rays:
        row = []
        for j in range(nr):
            r, s, D = rs[j], ss[j], Ds[j]
            ht, kind = F.H(cx + D * u[0], cy + D * u[1])
            hmax = F.feats[kind]['h'] if kind >= 0 else 1.0
            row.append((cx + r * u[0], cy + r * u[1], s * ht, s, kind, ht / hmax))
        grid.append(row)
    a0 = Acc(); a1 = Acc(); a2 = Acc(); a3 = Acc(); a4 = Acc(); a5 = Acc(); a6 = Acc()
    L = Vector((-0.62, 0.18, 0.76)).normalized()
    nf = 0
    for i in range(nth - 1):
        for j in range(nr - 1):
            q = [grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]]
            if max(p[2] for p in q) < 0.06:
                continue
            pts = [V(p[0], p[1], max(0.0, p[2]) + 0.01) for p in q]
            kd = max(q, key=lambda p: p[2])
            name = F.feats[kd[4]].get('color', 'hills') if kd[4] >= 0 else 'hills'
            hz = haze_level(sum(p[3] for p in q) / 4.0)
            for tri in ((0, 1, 2), (0, 2, 3)):                                  # 삼각형 둘: 평평하지 않은 사각면의 톤 줄무늬를 없앤다
                tp = [pts[t_] for t_ in tri]
                n = (Vector(tp[1]) - Vector(tp[0])).cross(Vector(tp[2]) - Vector(tp[0]))
                if n.length < 1e-9:
                    continue
                n.normalize()
                if n.z < 0:
                    n = -n
                fr = max(q[t_][5] for t_ in tri)
                if fr < 0.05:
                    a0.face(tp, M[(name, 'skirt', hz)], (0, 0, 1)); nf += 1
                    continue
                sl = math.hypot(n.x, n.y); d = (n.x * L.x + n.y * L.y) / max(1e-6, sl * math.hypot(L.x, L.y))
                tone = 1 if sl < 0.08 else (0 if d > 0.35 else (2 if d < -0.35 else 1))
                band = 0 if fr < 0.3 else (1 if fr < 0.68 else 2)
                a0.face(tp, M[(name, band, tone, hz)], (0, 0, 1))
                nf += 1
    # 덧층(거리 배율 s로 크기를 줄이고 같은 대기 단계 색): 표본 = 격자 점(엇갈려 듬성듬성)
    for i in range(1, nth - 1, 2):
        for j in range(1, nr - 1, 2):
            X, Y, z, s, kind, fr = grid[i][j]
            if z < 0.3 or kind < 0:
                continue
            hz = haze_level(s)
            zl, zr = grid[i - 1][j][2], grid[i + 1][j][2]; zi, zo = grid[i][j - 1][2], grid[i][j + 1][2]
            ridge = z >= max(zl, zr) and fr > 0.35                              # 방위 방향 극대 = 능선
            gully = z <= min(zl, zr) and fr > 0.15                              # 방위 방향 극소 = 골
            k = i * 1000 + j
            if ridge and hsh(k, 1.1) < 0.7:                                     # L5 능선 하이라이트(짧은 밝은 획)
                a5.face([V(X - 0.5 * s, Y, z + 0.05), V(X + 0.5 * s, Y, z + 0.05), V(X + 0.5 * s, Y + 0.25 * s, z + 0.05), V(X - 0.5 * s, Y + 0.25 * s, z + 0.05)], M[('ridge', hz)], (0, 0, 1))
            if gully and hsh(k, 1.2) < 0.8:                                     # L1 골 그늘(짙은 획)
                a1.face([V(X - 0.3 * s, Y - 0.6 * s, z + 0.04), V(X + 0.3 * s, Y - 0.6 * s, z + 0.04), V(X + 0.3 * s, Y + 0.6 * s, z + 0.04), V(X - 0.3 * s, Y + 0.6 * s, z + 0.04)], M[('valley', hz)], (0, 0, 1))
            if fr > 0.55 and hsh(k, 1.3) < 0.35:                                # L4 바위 노두
                a4.blob(X, Y, z + 0.15 * s, 0.7 * s, 0.5 * s, 0.4 * s, M[('rock', hz)], 1, 0.25, k, M[('rock2', hz)], None)
            if 0.25 < fr < 0.75 and hsh(k, 1.4) < 0.3:                          # L3 화산재·응회암 줄(내리막 방향 짧은 띠)
                gx, gy = zo - zi, zr - zl
                gl = math.hypot(gx, gy) or 1.0
                a3.face([V(X, Y, z + 0.03), V(X + 0.9 * s, Y + 0.2 * s, z + 0.03), V(X + 0.9 * s, Y + 0.35 * s, z + 0.03), V(X, Y + 0.15 * s, z + 0.03)], M[('ash', hz)], (0, 0, 1))
            if fr < 0.45 and hsh(k, 1.5) < 0.45:                                # L6 사면 수풀 점
                a6.blob(X, Y, z + 0.25 * s, 0.45 * s, 0.4 * s, 0.32 * s, M[('scrub', hz) if k % 2 else ('scrub2', hz)], 1, 0.2, k + 0.5)
    # L2 가까운 지형(배율이 가장 큰 지형) 기슭 → 꼭대기 오솔길
    best = None
    for i in range(nth):
        for j in range(nr):
            p = grid[i][j]
            if p[4] >= 0 and p[5] > 0.9 and (best is None or p[3] > best[0][3]):
                best = (p, i, j)
    if best:
        p, i, j = best
        pts = []
        for jj in range(max(1, j - 24), j + 1, 2):
            ii = i + (2 if (jj // 6) % 2 else -2)
            ii = max(0, min(nth - 1, ii))
            q = grid[ii][jj]
            if q[2] > 0.05:
                pts.append(V(q[0], q[1], q[2] + 0.12))
        if len(pts) >= 2:
            GR_ribbon = __import__('roma_pkg_suburb').ribbon
            GR_ribbon(a2.bm, pts, 0.35 * p[3], 0.05, a2.mi(M[('path', haze_level(p[3]))]))
    for nm_, ac in (('L0_Terrain', a0), ('L1_Gullies', a1), ('L2_Path', a2), ('L3_AshBands', a3), ('L4_Rocks', a4), ('L5_Ridges', a5), ('L6_Scrub', a6)):
        ac.obj('TERR_Persp_%s' % nm_, GC, root)
    return root, nf


def test_params():
    """임시 값(설계 사양 전 시험): 중심 = b6 Core 군집 평면 (411, 169), 군집 반지름 150, 남동 = 화면 오른쪽(평면 방위 −22°)"""
    c = (411.0, 169.0)

    def at(bearing_deg, D):
        t = math.radians(bearing_deg)
        return (c[0] + D * math.cos(t), c[1] + D * math.sin(t))
    ap = [at(b, 560.0 + 30.0 * math.sin(b * 0.09)) for b in range(-105, -30, 6)]
    return dict(center=c, d0=120.0, s_edge=0.55, s_out=0.4, t_out=1.6, sector=[-115.0, 10.0], r_max=560.0, dr=2.5, dth=0.75,
                features=[
                    dict(name='알바노 구릉', kind='massif', c=at(-22.0, 300.0), r=80.0, h=24.0, color='hills'),
                    dict(name='아펜니노', kind='range', ridge=ap, w=120.0, h=70.0, peaks_per_seg=1.4, color='range'),
                    dict(name='베수비오', kind='cone', c=at(-8.0, 900.0), r=110.0, h=60.0, color='volcano'),
                ])


# ───────────────────────── 22:34·22:35 산맥 띠(타이틀 아래 지도 창 윗변을 따라 화면 가로로 긴 능선) ─────────────────────────
# 화면 좌표로 정의한다: 능선 바닥선 y0(x), 앞 기슭까지 깊이 dep(x), 거리 배율 s(x)(가운데 s_mid → 양 끝 s_end, 위쪽 가장자리라 작고 연하다),
# 참 높이 H(x)(봉우리 가우스 합) → 그린 높이 s·H, 꼭대기는 창 윗선 top_y + margin 아래로 묶는다. 능선 뒤는 짓지 않는다(능선 = 하늘선).
# X·Y축 정렬 제약 없음(자연스러운 곡선 능선). 베수비오 = 띠 앞에 놓인 가장 작은 봉우리, 매끈한 원뿔 + 평평한 분화구 + 골 그늘.
def _plan_of(x, yg):
    """화면 점(x, 바닥 높이 0의 화면 y) → 평면 (X, Y)"""
    ox, oy = R.scr(Vector((0.0, 0.0, 0.0)))
    a = (x - ox) / 0.8660254; b = 2.0 * (yg - oy)
    return 0.5 * (a + b), 0.5 * (b - a)


def _tone(n, Lx=-0.62, Ly=0.18):
    sl = math.hypot(n.x, n.y)
    if sl < 0.08:
        return 1
    d = (n.x * Lx + n.y * Ly) / (sl * math.hypot(Lx, Ly))
    return 0 if d > 0.35 else (2 if d < -0.35 else 1)


def build_band(B, GC=None):
    GC = GC or R.coll(COLL, R.coll('ROMA_MAP'))
    M = mats(COLORS)
    tag = B.get('tag', 'Band')
    root = bpy.data.objects.new('TERR_%s_root' % tag, None); GC.objects.link(root)
    A = [Acc() for _ in range(7)]
    x0, x1, dx, NV = B['x0'], B['x1'], B.get('dx', 1.2), B.get('nv', 14)
    xm, half = 0.5 * (B['x0'] + B['x1']), 0.5 * (B['x1'] - B['x0'])
    s_of = lambda x: B['s_end'] + (B['s_mid'] - B['s_end']) * max(0.0, 1.0 - ((x - xm) / half) ** 2)
    y0 = lambda x: B['y_base'] + sum(a * math.sin(x * f + p) for a, f, p in B['y_waves'])
    dep = lambda x: B['depth'] * s_of(x) / B['s_mid']

    def Htrue(x):
        h = B['h_base'] * (1.0 + 0.15 * math.sin(x * 0.11) + 0.08 * math.sin(x * 0.37 + 1.3))
        for (xc, w, hh) in B['peaks']:
            h += hh * math.exp(-abs(x - xc) / w) * (1.0 + 0.25 * math.exp(-((x - xc) / (0.3 * w)) ** 2))      # 뾰족한 봉우리
        h += 2.2 * (abs(math.sin(x * 0.53 + 0.4)) + 0.6 * abs(math.sin(x * 1.31 + 1.1))) - 2.0                  # 능선 톱니
        for (xa, xb, nm) in B.get('zones', []):                                # 알바노 구릉: 낮고 둥글게(가장자리 15에서 부드럽게)
            e = min(1.0, max(0.0, min(x - xa + 15.0, xb + 15.0 - x) / 15.0))
            h *= 1.0 - (1.0 - B.get('zone_scale', 0.55)) * (e * e * (3 - 2 * e))
        return h

    def kind(x):
        for (xa, xb, nm) in B.get('zones', []):
            if xa <= x <= xb:
                return nm
        return 'range'
    xs = [x0 + dx * i for i in range(int((x1 - x0) / dx) + 1)]
    crest = {}
    for x in xs:
        cap = y0(x) - B['top_y'] - B['margin']                                 # 꼭대기는 창 윗선 아래(부드러운 상한, 평평한 잘림 없음)
        crest[x] = max(0.5, cap * math.tanh(s_of(x) * Htrue(x) / cap))
    grid = []
    for x in xs:
        row = []
        for k in range(NV + 1):
            t = k / NV
            ph = x * B.get('gully_f', 0.85) + 2.2 * math.sin(x * 0.13) + 1.4 * t * math.sin(x * 0.29)
            corr = 1.0 - 0.22 * (0.5 + 0.5 * math.cos(ph)) * 4.0 * t * (1.0 - t) * (0.6 + 0.4 * math.sin(x * 0.07 + 1.0))   # 골·능 주름(불규칙, 아래로 휘어짐)
            z = crest[x] * ((1.0 - t) ** 1.7) * corr
            yg = y0(x) + t * dep(x)
            X, Y = _plan_of(x, yg)
            row.append((X, Y, z, t))
        grid.append(row)
    hzb = (lambda x: B['haze_level']) if B.get('haze_level') is not None else (lambda x: int(round(2 + 2 * (B['s_mid'] - s_of(x)) / max(1e-6, B['s_mid'] - B['s_end']))))
    for i in range(len(xs) - 1):
        hz = hzb(xs[i])
        nm = kind(xs[i])
        hmax = max(crest[xs[i]], crest[xs[i + 1]])
        for k in range(NV):
            q = [grid[i][k], grid[i + 1][k], grid[i + 1][k + 1], grid[i][k + 1]]
            pts = [V(p[0], p[1], p[2] + 0.01) for p in q]
            for tri in ((0, 1, 2), (0, 2, 3)):
                tp = [pts[j] for j in tri]
                n = (Vector(tp[1]) - Vector(tp[0])).cross(Vector(tp[2]) - Vector(tp[0]))
                if n.length < 1e-9:
                    continue
                n.normalize()
                if n.z < 0:
                    n = -n
                fr = max(q[j][2] for j in tri) / max(hmax, 1e-6)
                if fr < 0.06:
                    A[0].face(tp, M[(nm, 'skirt', hz)], (0, 0, 1)); continue
                band = 0 if fr < 0.32 else (1 if fr < 0.7 else 2)
                A[0].face(tp, M[(nm, band, _tone(n), hz)], (0, 0, 1))
    # 덧층: 골 그늘(L1, 불규칙 간격 · 아래로 가늘어짐) · 능 밝은 획(L5) · 하늘선 밝은 선 · 바위(L4) · 너덜(L3) · 낮은 사면 수풀(L6)
    def stroke(acc, i, k0, k1, w0, mt, dz):
        pts = []                                                                 # 사면 따라 좌우로 휘며 내려가는 획(곧은 세로줄 X)
        for k in range(k0, k1 + 1):
            ii = i + int(round(1.6 * math.sin(k * 0.8 + i * 0.37) + 2.2 * (k - k0) / max(1, k1 - k0) * (hsh(i, 3.5) - 0.5)))
            pts.append(grid[max(0, min(len(xs) - 1, ii))][k])
        for q, (a_, b_) in enumerate(zip(pts, pts[1:])):
            w = w0 * (1.0 - 0.75 * q / max(1, len(pts) - 1)); w2 = w0 * (1.0 - 0.75 * (q + 1) / max(1, len(pts) - 1))
            acc.face([V(a_[0] - w, a_[1] + w, a_[2] + dz), V(a_[0] + w, a_[1] - w, a_[2] + dz), V(b_[0] + w2, b_[1] - w2, b_[2] + dz), V(b_[0] - w2, b_[1] + w2, b_[2] + dz)],
                     mt, (0, 0, 1))
    i = 2
    while i < len(xs) - 2:
        x = xs[i]; s = s_of(x); hz = hzb(x)
        if crest[x] > 2.5:
            L_ = int(NV * (0.35 + 0.4 * hsh(i, 3.1)))
            stroke(A[1], i, 1, L_, 0.3 * s, M[('valley', hz)], 0.04)
            j = min(len(xs) - 2, i + 1 + int(2 + 3 * hsh(i, 3.2)))
            if crest[xs[j]] > 2.5 and hsh(i, 3.6) < 0.55:
                stroke(A[5], j, 1, int(NV * (0.2 + 0.3 * hsh(i, 3.3))), 0.2 * s, M[('ridge', hz)], 0.05)
        i += int(5 + 9 * hsh(i, 3.4))
    for i in range(1, len(xs) - 1):
        x = xs[i]; s = s_of(x); hz = hzb(x)
        c0, c1 = grid[i][0], grid[i + 1][0]
        A[5].face([V(c0[0], c0[1], c0[2] - 0.05), V(c1[0], c1[1], c1[2] - 0.05), V(c1[0], c1[1], c1[2] - 0.05 - 0.35 * s), V(c0[0], c0[1], c0[2] - 0.05 - 0.35 * s)],
                  M[('ridge', hz)], (1, 1, 0))
        if hsh(i, 2.1) < 0.14 and crest[x] > 3.0:
            p = grid[i][1]
            A[4].blob(p[0], p[1], p[2] - 0.2 * s, 0.8 * s, 0.5 * s, 0.4 * s, M[('rock', hz)], 1, 0.25, i, M[('rock2', hz)], None)
        if hsh(i, 2.2) < 0.12:
            k = int(NV * (0.25 + 0.35 * hsh(i, 2.3))); p, p2 = grid[i][k], grid[i][k + 1]
            A[3].face([V(p[0], p[1], p[2] + 0.03), V(p[0] + 0.9 * s, p[1] - 0.9 * s, p[2] + 0.03), V(p2[0] + 0.9 * s, p2[1] - 0.9 * s, p2[2] + 0.03), V(p2[0], p2[1], p2[2] + 0.03)],
                      M[('ash', hz)], (0, 0, 1))
        if hsh(i, 2.4) < 0.35:
            k = int(NV * (0.6 + 0.35 * hsh(i, 2.5))); p = grid[i][min(NV - 1, k)]
            A[6].blob(p[0], p[1], p[2] + 0.2 * s, 0.5 * s, 0.4 * s, 0.32 * s, M[('scrub', hz) if i % 2 else ('scrub2', hz)], 1, 0.2, i + 0.5)
    for (xa, xb, nm) in B.get('zones', []):                                     # 알바노 구릉 오솔길(L2)
        pts = []
        for j in range(12):
            x = xa + (xb - xa) * (0.2 + 0.6 * j / 11)
            i = min(range(len(xs)), key=lambda q: abs(xs[q] - x))
            k = int(NV * (0.85 - 0.5 * j / 11 + 0.08 * math.sin(j * 1.9)))
            p = grid[i][max(1, min(NV, k))]
            pts.append(V(p[0], p[1], p[2] + 0.08))
        __import__('roma_pkg_suburb').ribbon(A[2].bm, pts, 0.35 * s_of(xa), 0.05, A[2].mi(M[('path', haze_level(s_of(xa)))]))
    if B.get('vesuvius'):
        _cone_smooth(A, M, B['vesuvius'], s_of, y0, dep, hzb)
    for nm_, ac in zip(('L0_Terrain', 'L1_Gullies', 'L2_Path', 'L3_Scree', 'L4_Rocks', 'L5_Ridges', 'L6_Scrub'), A):
        ac.obj('TERR_%s_%s' % (tag, nm_), GC, root)
    return root


def _cone_smooth(A, M, VS, s_of, y0, dep, hzb=None):
    """베수비오: 띠 앞쪽의 넓은 잘린 원뿔(극좌표 72 × 18) — 거의 곧은 사면(지수 1.15) + 넓고 평평한 분화구 정상(테 밝게, 바닥 짙게) + 보이는 사면 골 6줄(가늘어지는 획)"""
    x = VS['x']; s = s_of(x); hz = hzb(x) if hzb else haze_level(s)
    yg = y0(x) + VS.get('t', 0.75) * dep(x)
    cX, cY = _plan_of(x, yg)
    rp = VS['r_scr'] * s / 1.2247; h = min(VS['h'] * s, yg - VS['top_y'] - VS['margin'])
    rc, NA, NRr = 0.26, 72, 18
    def zf(rho, th):
        if rho <= rc:
            return h * (0.97 - 0.05 * (1.0 - (rho / rc) ** 2))
        g = 1.0 - 0.035 * (0.5 + 0.5 * math.cos(9 * th + 0.6)) * math.sin(math.pi * (rho - rc) / (1.0 - rc))
        return h * ((1.0 - rho) / (1.0 - rc)) ** 1.15 * g
    P = [[(cX + rp * (j / NRr) * math.cos(2 * math.pi * i / NA), cY + rp * (j / NRr) * math.sin(2 * math.pi * i / NA), zf(j / NRr, 2 * math.pi * i / NA))
          for j in range(NRr + 1)] for i in range(NA)]
    for i in range(NA):
        i2 = (i + 1) % NA
        for j in range(NRr):
            q = [P[i][j], P[i2][j], P[i2][j + 1], P[i][j + 1]]
            pts = [V(p[0], p[1], p[2] + 0.02) for p in q]
            for tri in ((0, 1, 2), (0, 2, 3)):
                tp = [pts[t_] for t_ in tri]
                n = (Vector(tp[1]) - Vector(tp[0])).cross(Vector(tp[2]) - Vector(tp[0]))
                if n.length < 1e-9:
                    continue
                n.normalize()
                if n.z < 0:
                    n = -n
                fr = max(q[t_][2] for t_ in tri) / h
                if fr < 0.05:
                    A[0].face(tp, M[('volcano', 'skirt', hz)], (0, 0, 1)); continue
                band = 0 if fr < 0.3 else (1 if fr < 0.78 else 2)
                A[0].face(tp, M[('volcano', band, _tone(n), hz)], (0, 0, 1))
    zc = zf(0.0, 0.0)
    A[1].face([V(cX + rp * rc * 0.8 * math.cos(2 * math.pi * k / 32), cY + rp * rc * 0.8 * math.sin(2 * math.pi * k / 32), zc + 0.05) for k in range(32)],
              M[('valley', hz)], (0, 0, 1))
    zr = zf(rc, 0.0)
    for k in range(32):                                                         # 분화구 테(밝은 고리, 앞쪽 반만)
        a0_, a1_ = 2 * math.pi * k / 32, 2 * math.pi * (k + 1) / 32
        if math.cos(a0_) - (-math.sin(a0_)) < -0.3:
            continue
        r0, r1 = rp * rc * 0.8, rp * rc * 1.02
        A[5].face([V(cX + r0 * math.cos(a0_), cY + r0 * math.sin(a0_), zr + 0.06), V(cX + r1 * math.cos(a0_), cY + r1 * math.sin(a0_), zr + 0.06),
                   V(cX + r1 * math.cos(a1_), cY + r1 * math.sin(a1_), zr + 0.06), V(cX + r0 * math.cos(a1_), cY + r0 * math.sin(a1_), zr + 0.06)], M[('ridge', hz)], (0, 0, 1))
    for g_ in range(6):                                                         # 보이는 사면 골 6줄(가늘어지는 짙은 획)
        th = math.radians(-60.0 + 25.0 * g_ + 6.0 * hsh(g_, 4.1))               # 평면 방위: 화면 앞쪽(+X, +Y 사이)
        i = int(round(th / (2 * math.pi) * NA)) % NA
        tx, ty = -math.sin(th), math.cos(th)
        j0 = int(NRr * rc) + 1; j1 = int(NRr * (0.62 + 0.25 * hsh(g_, 4.2)))
        for j in range(j0, j1):
            p, p2 = P[i][j], P[i][j + 1]
            w = 0.28 * s * (1.0 - 0.7 * (j - j0) / max(1, j1 - j0)); w2 = 0.28 * s * (1.0 - 0.7 * (j + 1 - j0) / max(1, j1 - j0))
            A[1].face([V(p[0] - tx * w, p[1] - ty * w, p[2] + 0.05), V(p[0] + tx * w, p[1] + ty * w, p[2] + 0.05),
                       V(p2[0] + tx * w2, p2[1] + ty * w2, p2[2] + 0.05), V(p2[0] - tx * w2, p2[1] - ty * w2, p2[2] + 0.05)], M[('valley', hz)], (0, 0, 1))


def band_test_params():
    """임시 값(설계-d5 range ridge 점 목록 전): 창 [0, 92, 420, 478] 윗변 아래 가로 띠. 왼쪽~가운데 = 아펜니노, 오른쪽 = 알바노 구릉(낮고 둥글게), 오른쪽 끝 앞 = 베수비오(가장 작음)"""
    return dict(x0=-6.0, x1=426.0, dx=1.2, nv=14, top_y=92.0, margin=2.0, s_mid=0.55, s_end=0.4,
                y_base=121.0, y_waves=[(3.0, 0.021, 0.5), (1.6, 0.057, 2.0)], depth=15.0, h_base=14.0,
                peaks=[(18.0, 9.0, 14.0), (52.0, 11.0, 22.0), (78.0, 8.0, 30.0), (104.0, 10.0, 18.0), (138.0, 9.0, 24.0), (171.0, 12.0, 36.0), (196.0, 8.0, 22.0),
                       (226.0, 10.0, 28.0), (252.0, 9.0, 16.0), (276.0, 8.0, 10.0), (410.0, 10.0, 14.0)],
                zones=[(285.0, 345.0, 'hills')], gully_f=0.85,
                vesuvius=dict(x=372.0, t=0.72, r_scr=50.0, h=30.0, top_y=92.0, margin=2.0))



def band_from_spec(T):
    """d7 core_map.terrain.band → 겹 띠 매개변수 목록(뒤 → 앞). 봉우리 높이·바닥선은 화면 mm 그대로(s = 1), 꼭대기 ≤ peak_min_y"""
    ys = T.get('y_waves') or [T.get('y_base', 120.0)]
    hz = T.get('haze') or [0.5] * len(ys)
    pk = T.get('peaks') or [[] for _ in ys]
    zones = [(z_['x'][0], z_['x'][1], 'hills' if '알바노' in z_['name'] else 'range') for z_ in T.get('zones', [])]
    margin = float(T.get('peak_min_y', T.get('y_top', 92.0) + 4.0)) - float(T.get('y_top', 92.0))
    out = []
    for i, yb in enumerate(ys):
        nxt = ys[i + 1] if i + 1 < len(ys) else yb + 6.0
        lvl = max(0, min(NH - 1, int(round((float(hz[i]) - 0.12) / 0.55 * (NH - 1) + 0.4))))
        B = dict(tag='Band%d' % i, x0=-6.0, x1=426.0, dx=1.2, nv=12, top_y=float(T.get('y_top', 92.0)), margin=margin, s_mid=1.0, s_end=1.0,
                 y_base=float(yb), y_waves=[(1.2, 0.031 + 0.01 * i, 0.7 * i), (0.6, 0.083, 1.9 + i)], depth=(nxt - yb) + 7.0, h_base=1.5 + 0.8 * i,
                 peaks=[(float(x), float(w) / 5.0, float(h) * 0.8) for x, w, h in pk[i]] + [(float(x) + 0.3 * float(w), float(w) / 9.0, float(h) * 0.35) for x, w, h in pk[i]],
                 zones=[(a, b, n) for a, b, n in zones if n == 'hills'], zone_scale=1.0, gully_f=0.85 + 0.1 * i, haze_level=lvl)
        out.append(B)
    V = T.get('vesuvius')
    if V and out:
        out[-1]['vesuvius'] = dict(x=float(V['x']), t=0.65, r_scr=float(V.get('r_scr', 21.0)), h=float(V.get('h', 14.0)), top_y=out[-1]['top_y'], margin=margin)
    return out


def build_band_spec(T, GC=None):
    """d7 산맥 띠(겹마다 build_band). 반환: 루트 목록"""
    return [build_band(B, GC) for B in band_from_spec(T)]
