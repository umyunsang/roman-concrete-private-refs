# roma_aq_valley — 21:55 사용자: 수도교를 레퍼런스(퐁 뒤 가르)처럼 산과 산 사이 골짜기의 물 위를 가로지르게. 담당: Blender-보완
#   · 아래층 아치 발치가 수면 아래에 선다(수도교 루트를 dz만큼 내린다) · 교각 둘레 물결 고리(L3)·바위(L4)
#   · 수면 반영 = 평면 일러스트(L5): 높이 h인 점을 평면 (+h, +h)로 옮겨 수면 높이에 그리면 화면에서 정확히 수직으로 뒤집힌 실루엣이 된다.
#     아래·가운데 단 앞면(교각 + 아치 위 벽)을 그렇게 옮기고 수면 다각형으로 잘라, 수면색과 돌색을 섞어 어둡게 칠한다
#   · 양 끝은 지형 비탈에 묻힌다(골짜기 지형 높이장 · 또는 roma_terrain_persp 지형)
import bpy, bmesh, math
from mathutils import Vector
import roma_kit as R, roma_flat as FL, roma_geo as G
import roma_pkg_ground as GR

V = GR.V
hsh = R.hash01
Acc = GR.Acc


def _clip(poly, region):
    """평면 다각형 poly를 볼록 다각형 region(반시계·시계 상관없음) 안으로 자른다"""
    n = len(region)
    A = sum(region[i][0] * region[(i + 1) % n][1] - region[(i + 1) % n][0] * region[i][1] for i in range(n))
    sg = 1.0 if A > 0 else -1.0
    out = list(poly)
    for i in range(n):
        a, b = region[i], region[(i + 1) % n]
        ex, ey = b[0] - a[0], b[1] - a[1]
        f = lambda p, a=a, ex=ex, ey=ey: -sg * (ex * (p[1] - a[1]) - ey * (p[0] - a[0]))   # 안쪽이 ≤ 0
        out = GR.clip_half(out, f)
        if len(out) < 3:
            return []
    return out


def reflection(GC, name, aroot, AQI, dz, z_w, water_poly, parent=None, hex_stone='#C9AE86', u_range=None):
    """수도교 아래·가운데 단 앞면 실루엣의 수면 반영(L5). 반환: 오브젝트"""
    a5 = Acc()
    mt = FL.flat('F_aqv_reflect', FL.shade(FL.mix_hex(hex_stone, GR.WATER_HEX, 0.55), 0.82))
    X0, Y0 = AQI['X0'], AQI['Y0']
    zwl = z_w - dz                                                            # 수면의 지역 높이

    def put(poly_uz, Tf):
        if u_range is not None:                                               # 지형에 묻힌 구간(물 위로 드러나지 않은 교각)의 반영은 그리지 않는다
            poly_uz = GR.clip_half(poly_uz, lambda p: u_range[0] - p[0])
            poly_uz = GR.clip_half(poly_uz, lambda p: p[0] - u_range[1]) if len(poly_uz) >= 3 else []
            if len(poly_uz) < 3:
                return
        pts = []
        for u, z in poly_uz:
            h = max(0.0, (z + dz) - z_w)
            pts.append((X0 + u + h, Y0 + Tf + h))
        cl = _clip(pts, water_poly)
        if len(cl) >= 3:
            a5.face([V(x, y, z_w + 0.012) for x, y in cl], mt, (0, 0, 1))

    def tier(spans, zb, zs_spring, ztop, Tf, U0, LA):
        edges = [U0] + [v for ab in spans for v in ab] + [LA]
        for i in range(0, len(edges) - 1, 2):                                 # 교각(아치 사이)
            p0, p1 = edges[i], edges[i + 1]
            if p1 - p0 > 0.05:
                put([(p0, zb), (p1, zb), (p1, ztop), (p0, ztop)], Tf)
        for (a, b) in spans:                                                   # 아치 위 벽(홍예 위 ~ 띠)
            cu, rr = (a + b) / 2.0, (b - a) / 2.0
            arc = [(cu + rr * math.cos(math.pi * k / 12), zs_spring + rr * math.sin(math.pi * k / 12)) for k in range(12, -1, -1)]
            put([(a, zs_spring)] + arc[1:-1] + [(b, zs_spring), (b, ztop), (a, ztop)], Tf)
    tier(AQI['lo'], zwl, AQI['S1'], AQI['ZSC0'], AQI['T_lo'], AQI['U0'], AQI['LA'])
    put([(AQI['U0'], AQI['ZSC0']), (AQI['LA'], AQI['ZSC0']), (AQI['LA'], AQI['ZSC1']), (AQI['U0'], AQI['ZSC1'])], AQI['T_lo'] + 0.25)
    tier(AQI['hi'], AQI['ZSC1'], AQI['S2'], AQI['ZC0'], AQI['T'], AQI['U0'], AQI['LA'])
    return a5.obj(name + '_L5_Reflection', GC, parent)


def pier_water(GC, name, AQI, dz, z_w, parent=None):
    """교각 둘레 물결 고리(L3, 밝은 초승달 2~3겹) · 교각 발치 바위(L4)"""
    a3 = Acc(); a4 = Acc()
    M = GR.mats()
    X0, Y0, T = AQI['X0'], AQI['Y0'], AQI['T_lo']
    edges = [AQI['U0']] + [v for ab in AQI['lo'] for v in ab] + [AQI['LA']]
    for i in range(0, len(edges) - 1, 2):
        p0, p1 = edges[i], edges[i + 1]
        if p1 - p0 < 0.3:
            continue
        uc = (p0 + p1) / 2.0; hw = (p1 - p0) / 2.0
        for k in range(3):
            r0 = hw + 0.35 + 0.55 * k; r1 = r0 + 0.16
            pts_o = [(X0 + uc + r1 * math.cos(math.pi * j / 10), Y0 + T + 0.15 + 0.6 * r1 * math.sin(math.pi * j / 10)) for j in range(11)]
            pts_i = [(X0 + uc + r0 * math.cos(math.pi * j / 10), Y0 + T + 0.15 + 0.6 * r0 * math.sin(math.pi * j / 10)) for j in range(10, -1, -1)]
            a3.face([V(x, y, z_w + 0.02) for x, y in pts_o + pts_i], M['r_wave'] if k else M['foam'], (0, 0, 1))
        for j in range(3):
            r = 0.4 + 0.5 * hsh(i, j, 7.7)
            x = X0 + uc + (hw + 0.4) * (-1 + 2 * hsh(i, j, 8.8)); y = Y0 + T + 0.4 + 0.6 * hsh(i, j, 9.9)
            a4.blob(x, y, z_w + 0.1, r * 1.2, r * 0.9, r * 0.6, M['rock'], 1, 0.2, i * 10 + j, M['rock_top'], None)
    return a3.obj(name + '_L3_PierRipples', GC, parent), a4.obj(name + '_L4_PierRocks', GC, parent)


def water_span(X0, LA, H_top, z_floor, z_w, Y0=0.0):
    """골짜기 지형(valley_terrain과 같은 식)이 수도교 줄(평면 Y0)에서 수면 아래인 지역 u 범위"""
    sm = lambda t: 0.0 if t <= 0 else (1.0 if t >= 1 else t * t * (3 - 2 * t))
    und = 1.0 + 0.12 * math.sin(Y0 * 0.13 + 0.7) + 0.06 * math.sin(Y0 * 0.37)
    top = H_top * und
    def z(u):
        X = X0 + u
        hl = z_floor + (top - z_floor) * (1.0 - sm((X - (X0 + 8.0)) / 22.0)); hr = z_floor + (top - z_floor) * (1.0 - sm(((X0 + LA - 8.0) - X) / 22.0))
        return max(hl, hr)
    us = [i * 0.1 for i in range(int(LA * 10) + 1)]
    wet = [u for u in us if z(u) < z_w]
    return (min(wet), max(wet)) if wet else None


def valley_terrain(GC, name, X0, Y0, LA, H_top, z_floor, half_w=40.0, step=1.5, parent=None):
    """골짜기 높이장(시험·임시): 수도교 양 끝(평면 X0, X0 + LA)은 언덕 비탈(H_top)에 묻히고 가운데는 수면 아래 바닥(z_floor)"""
    import roma_pkg_suburb as SB
    BM, X = SB.ter_mats('hills')
    a0 = Acc()
    for m in BM:
        a0.mi(m)
    xs = [X0 - 34.0 + step * i for i in range(int((LA + 68.0) / step) + 1)]
    ys = [Y0 - half_w + step * j for j in range(int(2 * half_w / step) + 1)]

    def zf(Xp, Yp):
        sl = (Xp - (X0 + 8.0)) / 22.0; sr = ((X0 + LA - 8.0) - Xp) / 22.0
        sm = lambda t: 0.0 if t <= 0 else (1.0 if t >= 1 else t * t * (3 - 2 * t))
        und = 1.0 + 0.12 * math.sin(Yp * 0.13 + 0.7) + 0.06 * math.sin(Yp * 0.37)
        top = H_top * und
        hl = z_floor + (top - z_floor) * (1.0 - sm(sl)); hr = z_floor + (top - z_floor) * (1.0 - sm(sr))
        return max(hl, hr) + 0.4 * math.sin(Xp * 0.31) * math.sin(Yp * 0.27)
    bm = a0.bm
    grid = [[bm.verts.new(V(x, y, zf(x, y))) for x in xs] for y in ys]
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new([grid[j][i], grid[j + 1][i], grid[j + 1][i + 1], grid[j][i + 1]])      # 위를 보는 면(평면 Y → Blender −y)
    SB._hf_tone(bm, H_top, 0, jit=lambda f: 0.05 * SB._j(int(f.calc_center_median().x * 2), int(f.calc_center_median().y * 2), 4.4))
    return a0.obj(name + '_L0_Valley', GC, parent)


# ───────────────────────── b7(23:29 사용자): 레퍼런스(퐁 뒤 가르)대로 수도교 골짜기 — 블록 C의 골짜기 홈 안 ─────────────────────────
def b7_valley_z(X, VV):
    """골짜기 단면 높이(평면 X): 둑 위 0 → 석회암 판 층계 → 강바닥 −7.2. V = dict(x0, r0, r1, x1)"""
    x0, r0, r1, x1 = VV['x0'], VV['r0'], VV['r1'], VV['x1']
    if r0 <= X <= r1:
        return -7.25
    t = (X - x0) / (r0 - x0) if X < r0 else (x1 - X) / (x1 - r1)
    t = max(0.0, min(1.0, t))
    steps = 4
    k = min(steps - 1, int(t * steps)); f = t * steps - k
    lip = 0.0 if f < 0.72 else (f - 0.72) / 0.28                          # 판마다 평평한 윗면 + 짧은 턱(석회암 판 층계)
    return -7.0 * ((k + lip) / steps) ** 1.15


def b7_valley(GC, root, AQI, VV, z_w=-7.0, seed=0.0, terrain=True):
    """골짜기 지형(L0) · 판 바위·물가 바위(L4) · 층리 선(L3) · 판 윗선(L5) · 풀·덤불(L6) · 판 틈 그늘(L1) · 교각 연장(L0) · 양 끝 풀 언덕(L0·L4·L6)
    · 수면 반영(L5) · 교각 물결(L3). 모두 root(수도교 루트) 아래, 월드 변환 그대로"""
    import roma_diorama as DI
    DM = DI.mats(); GM = GR.mats()
    A = [Acc() for _ in range(7)]
    x0, x1, y0, y1 = VV['x0'], VV['x1'], VV['y0'], VV['y1']
    nx = int((x1 - x0) / 0.8) + 1
    xs = [x0 + (x1 - x0) * i / (nx - 1) for i in range(nx)]
    ys = [y0 + (y1 - y0) * j / 8 for j in range(9)]
    zf = lambda X, Y: b7_valley_z(X, VV) + (0.0 if abs(b7_valley_z(X, VV)) < 1e-6 else 0.12 * math.sin(Y * 0.31 + X * 0.07))
    for i in range(nx - 1):
        if not terrain:                                                        # 23:43: 골짜기 땅은 블록 C가 짓는다(여기는 판 바위·덤불·교각만)
            break
        Xa, Xb = xs[i], xs[i + 1]
        za, zb_ = b7_valley_z(Xa, VV), b7_valley_z(Xb, VV)
        flat = abs(za - zb_) < 0.05
        deep = min(za, zb_) < -5.5
        mt = (DM['rk_c'] if flat else DM['rk_b']) if min(za, zb_) < -1.2 else (DM['gb_grass'] if flat else DM['gb_grass2'])
        if min(za, zb_) <= -7.2:
            mt = DM['rk_dark']
        for j in range(8):
            Ya, Yb = ys[j], ys[j + 1]
            A[0].face([V(Xa, Ya, zf(Xa, Ya)), V(Xb, Ya, zf(Xb, Ya)), V(Xb, Yb, zf(Xb, Yb)), V(Xa, Yb, zf(Xa, Yb))], mt, (0, 0, 1))
        if not flat and za != zb_ and min(za, zb_) > -7.2:                  # 턱 = 판 바위 앞면 그늘(L1) · 판 윗선 밝게(L5)
            zt_ = max(za, zb_)
            A[5].face([V(Xa, y0, zt_ + 0.03), V(Xa + 0.25, y0, zt_ + 0.03), V(Xa + 0.25, y1, zt_ + 0.03), V(Xa, y1, zt_ + 0.03)], DM['rk_c'], (0, 0, 1))
            zl_ = min(za, zb_); Xl = Xb if zb_ < za else Xa
            A[1].face([V(Xl - 0.2, y0, zl_ + 0.03), V(Xl + 0.2, y0, zl_ + 0.03), V(Xl + 0.2, y1, zl_ + 0.03), V(Xl - 0.2, y1, zl_ + 0.03)], DM['rk_dark'], (0, 0, 1))
    # 판 바위(L4): 둑 판마다 덩어리 판 · 물가 바위
    for k in range(70):
        side = k % 2
        t = hsh(k, seed, 1.1)
        X = (VV['x0'] + (VV['r0'] - VV['x0']) * (0.15 + 0.85 * t)) if side == 0 else (VV['x1'] - (VV['x1'] - VV['r1']) * (0.15 + 0.85 * t))
        Y = y0 + 1.0 + (y1 - y0 - 2.0) * hsh(k, seed, 1.2)
        z = b7_valley_z(X, VV)
        w = 1.2 + 2.6 * hsh(k, 1.3); d = 0.8 + 1.6 * hsh(k, 1.4); h = 0.25 + 0.5 * hsh(k, 1.5)
        A[4].box(X - w / 2, X + w / 2, Y - d / 2, Y + d / 2, z, z + h, DM['rk_a'] if k % 3 else DM['rk_c'], DM['rk_b'])
    for k in range(36):
        side = k % 2
        X = (VV['r0'] - 0.6 - 2.2 * hsh(k, 2.1)) if side == 0 else (VV['r1'] + 0.6 + 2.2 * hsh(k, 2.1))
        Y = y0 + 0.8 + (y1 - y0 - 1.6) * hsh(k, 2.2); r = 0.5 + 1.1 * hsh(k, 2.3)
        A[4].blob(X, Y, z_w + 0.2, r * 1.3, r, r * 0.6, DM['rk_b'], 1, 0.25, seed + k, DM['rk_c'], DM['rk_dark'])
    # 층리 선(L3): 판 앞 면을 따라 가는 줄
    for i in range(nx - 1):
        Xa = xs[i]; za, zb_ = b7_valley_z(Xa, VV), b7_valley_z(xs[i + 1], VV)
        if not terrain:
            break
        if abs(za - zb_) > 0.2 and min(za, zb_) > -7.2:
            zm = 0.5 * (za + zb_)
            A[3].face([V(Xa, y0, zm + 0.04), V(xs[i + 1], y0, zm + 0.04), V(xs[i + 1], y1, zm + 0.04), V(Xa, y1, zm + 0.04)], DM['rk_dark'], (0, 0, 1))
    # 풀·덤불(L6): 위쪽 둑과 판 윗면
    for k in range(90):
        side = k % 2
        t = hsh(k, 3.1) ** 0.7
        X = (VV['x0'] + (VV['r0'] - VV['x0']) * 0.85 * t) if side == 0 else (VV['x1'] - (VV['x1'] - VV['r1']) * 0.85 * t)
        Y = y0 + 0.6 + (y1 - y0 - 1.2) * hsh(k, 3.2)
        z = b7_valley_z(X, VV)
        r = 0.35 + 0.7 * hsh(k, 3.3)
        A[6].blob(X, Y, z + r * 0.4, r, r * 0.85, r * 0.7, DM['gb_grass2'] if k % 3 else DM['tuft'], 1, 0.25, seed + 50 + k, DM['gb_grass3'], None)
    # 양 끝 풀 언덕(수도교 끝을 묻는다): 극좌표 둔덕
    for (cx, cy, rr, hh) in (VV.get('hills', []) if terrain else []):
        NA, NR = 40, 8
        P = [[(cx + rr * (j / NR) * math.cos(2 * math.pi * i / NA), cy + rr * (j / NR) * 0.8 * math.sin(2 * math.pi * i / NA),
               hh * (1.0 - (j / NR) ** 2) ** 1.3 * (1.0 + 0.08 * math.sin(3 * i))) for j in range(NR + 1)] for i in range(NA)]
        for i in range(NA):
            i2 = (i + 1) % NA
            for j in range(NR):
                q = [P[i][j], P[i2][j], P[i2][j + 1], P[i][j + 1]]
                mt = DM['gb_grass'] if j > 1 else DM['gb_grass2']
                A[0].face([V(x, y, z + 0.02) for x, y, z in q], mt, (0, 0, 1))
        for k in range(14):
            a = 2 * math.pi * hsh(k, cx, 4.1); r_ = rr * (0.2 + 0.7 * hsh(k, cx, 4.2))
            X, Y = cx + r_ * math.cos(a), cy + r_ * 0.8 * math.sin(a)
            z = hh * (1.0 - (r_ / rr) ** 2) ** 1.3
            if k % 3 == 0:
                A[4].blob(X, Y, z, 1.0, 0.8, 0.5, DM['rk_a'], 1, 0.25, k + cx, DM['rk_c'], DM['rk_dark'])
            else:
                A[6].blob(X, Y, z + 0.3, 0.7, 0.6, 0.5, DM['gb_grass2'], 1, 0.25, k + cx + 0.5, DM['gb_grass3'], None)
    # 교각 연장(L0): 골짜기 안 교각은 땅(또는 물 밑)까지
    l0 = next(o for o in root.children_recursive if o.type == 'MESH' and '_L0_' in o.name)
    mat = l0.data.materials[0]
    X0, Y0 = AQI['X0'], AQI['Y0']; TL = AQI.get('T_lo', AQI['T'])
    edges = [AQI['U0']] + [v for ab in AQI['lo'] for v in ab] + [AQI['LA']]
    for i in range(0, len(edges) - 1, 2):
        p0, p1 = edges[i], edges[i + 1]
        Xa, Xb = X0 + p0, X0 + p1
        if Xb < x0 or Xa > x1:
            continue
        zlo = min(b7_valley_z(Xa, VV), b7_valley_z(Xb, VV)) - 0.4
        A[0].box(Xa, Xb, Y0 - TL - 0.05, Y0 + TL + 0.05, zlo, 0.05, mat, mat, sides='ESWN')
        A[2].box(Xa - 0.35, Xb + 0.35, Y0 - TL - 0.4, Y0 + TL + 0.4, zlo, zlo + 1.4, DM['rk_c'], DM['rk_b'], sides='ES')   # 교각 받침돌
    names = ('L0_Valley', 'L1_LedgeShade', 'L2_PierFootings', 'L3_Bedding', 'L4_Slabs', 'L5_LedgeLight', 'L6_Scrub')
    obs = []
    for nm_, ac in zip(names, A):
        ob = ac.obj('BATHS_Aqueduct_%s' % nm_, GC, None)
        if ob is not None:
            mw = ob.matrix_world.copy(); ob.parent = root; ob.matrix_world = mw
            obs.append(ob)
    return obs
