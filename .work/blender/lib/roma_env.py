# roma_env — 23:29 사용자: "각 core 오브젝트 레퍼런스 이미지에 맞게 디오라마의 지형과 주변 환경을 똑같이". 담당: Blender-보완
# 건물마다 레퍼런스 속 둘레(땅·유적·풀·물가)를 디오라마 블록 윗면에 짓는다. 사람·장식 소품(노점·수레·나무) 0.
# 조각은 그 자리 블록 루트(DIO_Block_*_root) 아래 L0~L6 이름으로 붙는다(블록 층 감사 그대로). 평면 (X, Y) → Blender (X, −Y, Z).
import bpy, math
from mathutils import Vector
import roma_kit as R, roma_flat as FL
import roma_pkg_ground as GR
import roma_diorama as DI

V = GR.V
hsh = R.hash01
Acc = GR.Acc
COLL = 'MAP_Diorama'
EXTRA = {'env_trav': '#E3D6B9', 'env_trav2': '#CFC0A0', 'env_trav_dk': '#A89878', 'env_col': '#E8DDC6', 'env_col2': '#D4C6AA',
         'env_grass': '#9DAE5C', 'env_grass2': '#869A4C', 'env_grass3': '#B4BF72', 'env_dry': '#C2B47A', 'env_dry2': '#A99B62',
         'env_brick': '#B06A48', 'env_brick2': '#9A5A3C', 'env_brick_hi': '#CB8560', 'env_deep': '#4E3A2C', 'env_field': '#B9BE78', 'env_field2': '#A4AE68',
         'env_stone': '#C9B996', 'env_stone2': '#B2A17F', 'env_stain': '#857562', 'env_ivy': '#6E8445'}


def mats():
    M = DI.mats()
    for k, hx in EXTRA.items():
        M[k] = FL.flat('F_env_' + k, hx)
    return M


def plan_bbox(root):
    xs, ys = [], []
    for o in root.children_recursive:
        if o.type != 'MESH' or o.hide_render or o.name.startswith('X_CUT_'):
            continue
        mw = o.matrix_world
        for c in o.bound_box:
            w = mw @ Vector(c); xs.append(w.x); ys.append(-w.y)
    return min(xs), max(xs), min(ys), max(ys)


def _finish(A, tag, block_root):
    GC = bpy.data.collections[COLL]
    obs = []
    for k, ac in enumerate(A):
        ob = ac.obj('DIO_Env_%s_L%d_%s' % (tag, k, ('Ground', 'Shade', 'Members', 'Surface', 'Ruins', 'Light', 'Growth')[k]), GC, block_root)
        if ob is not None:
            obs.append(ob)
    return obs


def _column(A, M, X, Y, z, r, h, broken=True, seed=0.0):
    """유적 기둥(받침 + 몸통 + 깨진 윗면) — 몸통 두 톤 띠(홈 대신)"""
    A[2].box(X - r * 1.4, X + r * 1.4, Y - r * 1.4, Y + r * 1.4, z, z + r * 0.6, M['env_trav'], M['env_trav2'])
    n = 10
    pts = [(X + r * math.cos(2 * math.pi * k / n), Y + r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    A[0].prism(pts, z + r * 0.6, z + h, M['env_col'], M['env_col2'])
    A[5].face([V(X + r * 0.9 * math.cos(-2.2), Y + r * 0.9 * math.sin(-2.2), z + h + 0.01), V(X + r * 0.9 * math.cos(-0.6), Y + r * 0.9 * math.sin(-0.6), z + h + 0.01),
               V(X, Y, z + h + 0.01)], M['hi'] if 'hi' in M else M['ash_cope'], (0, 0, 1))
    if broken and hsh(X, Y, seed) < 0.6:
        A[4].box(X - r * 0.5, X + r * 0.3, Y - r * 0.4, Y + r * 0.5, z + h, z + h + r * 0.5, M['env_col'], M['env_col2'])


def _drum_lying(A, M, X, Y, z, r, L, ang):
    """눕힌 기둥 토막(평면 방향 ang)"""
    ca, sa = math.cos(ang), math.sin(ang)
    n = 10
    for k in range(n):
        t0, t1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        pts = []
        for (t, s) in ((t0, -0.5), (t0, 0.5), (t1, 0.5), (t1, -0.5)):
            ox, oz = r * math.cos(t), r + r * math.sin(t)
            pts.append(V(X + ca * L * s - sa * ox, Y + sa * L * s + ca * ox, z + oz))
        A[4].face(pts, M['env_col'] if k % 2 else M['env_col2'], None)
    for s in (-0.5, 0.5):
        A[4].face([V(X + ca * L * s - sa * r * math.cos(2 * math.pi * k / n), Y + sa * L * s + ca * r * math.cos(2 * math.pi * k / n), z + r + r * math.sin(2 * math.pi * k / n))
                   for k in range(n)], M['env_trav2'], None)


def _patch(A, li, X, Y, z, rx, ry, mat, k=8, seed=0.0):
    A[li].face([V(X + rx * (0.75 + 0.45 * hsh(q, seed, 7.1)) * math.cos(2 * math.pi * q / k), Y + ry * (0.75 + 0.45 * hsh(q, seed, 7.2)) * math.sin(2 * math.pi * q / k), z)
                for q in range(k)], mat, (0, 0, 1))


def _shrub(A, X, Y, z, r, M, seed=0.0, dry=False):
    A[6].blob(X, Y, z + r * 0.45, r, r * 0.85, r * 0.65, M['env_dry'] if dry else M['env_grass2'], 1, 0.25, seed, M['env_dry2'] if dry else M['env_grass3'], None)


def _ruin_wall(A, M, X0, Y0, X1, Y1, z, h, t=0.9, seed=0.0, mat='env_stone', crenel=False):
    """무너진 벽(평면 선분 위, 윗선 들쭉날쭉) · 갓 깨진 윗면 · 얼룩"""
    L = math.hypot(X1 - X0, Y1 - Y0); ux, uy = (X1 - X0) / L, (Y1 - Y0) / L; nx, ny = -uy, ux
    s = 0.0; k = 0
    while s < L - 0.2:
        w = min(L - s, 1.2 + 1.6 * hsh(k, seed, 8.1))
        hh = h * (0.35 + 0.65 * hsh(k, seed, 8.2) ** 0.7)
        pts = [(X0 + ux * a + nx * b, Y0 + uy * a + ny * b) for a, b in ((s, -t / 2), (s + w, -t / 2), (s + w, t / 2), (s, t / 2))]
        A[0].prism(pts, z, z + hh, M[mat + '2'] if mat + '2' in M else M[mat], M[mat])
        if crenel and hh > 0.7 * h:
            for c in range(int(w / 0.8)):
                a0 = s + 0.15 + 0.8 * c
                cp = [(X0 + ux * a + nx * b, Y0 + uy * a + ny * b) for a, b in ((a0, -t / 2), (a0 + 0.45, -t / 2), (a0 + 0.45, t / 2), (a0, t / 2))]
                A[2].prism(cp, z + hh, z + hh + 0.55, M[mat], M[mat])
        if hsh(k, seed, 8.3) < 0.5:
            A[6].face([V(X0 + ux * (s + 0.2) + nx * (t / 2 + 0.02), Y0 + uy * (s + 0.2) + ny * (t / 2 + 0.02), z + hh * 0.9),
                       V(X0 + ux * (s + 0.6) + nx * (t / 2 + 0.02), Y0 + uy * (s + 0.6) + ny * (t / 2 + 0.02), z + hh * 0.9),
                       V(X0 + ux * (s + 0.5) + nx * (t / 2 + 0.02), Y0 + uy * (s + 0.5) + ny * (t / 2 + 0.02), z + 0.1)], M['env_stain'], (nx, -ny, 0))
        s += w + 0.05; k += 1
    return L


def _arch_ruin(A, M, X, Y, z, w, h, axis='X', seed=0.0, mat='env_stone'):
    """홀로 선 아치 유적: 두 교각 + 반원 아치 고리(조각) + 아치 속 그늘(L1)"""
    pw, t = 0.9, 1.0
    r = (w - 2 * pw) / 2.0
    zs = z + h - r - 0.6
    def P(u, v):
        return (X + u, Y + v) if axis == 'X' else (X + v, Y + u)
    for u0 in (-w / 2, w / 2 - pw):
        A[0].prism([P(u0, -t / 2), P(u0 + pw, -t / 2), P(u0 + pw, t / 2), P(u0, t / 2)], z, zs, M[mat + '2'], M[mat])
    n = 7
    for k in range(n):
        a0, a1 = math.pi * k / n, math.pi * (k + 1) / n
        if hsh(k, seed, 9.1) < 0.15:
            continue
        r0, r1 = r, r + 0.6
        quad = [(r0 * math.cos(a0), r0 * math.sin(a0)), (r1 * math.cos(a0), r1 * math.sin(a0)), (r1 * math.cos(a1), r1 * math.sin(a1)), (r0 * math.cos(a1), r0 * math.sin(a1))]
        for vv in (-t / 2, t / 2):
            pass
        pts_f = [V(*P(cu, -t / 2), zs + cz) for cu, cz in quad]
        pts_b = [V(*P(cu, t / 2), zs + cz) for cu, cz in quad]
        A[2].face(pts_f, M[mat], (1, 0, 0) if axis == 'Y' else (0, 1, 0))
        A[2].face(pts_b, M[mat], (1, 0, 0) if axis == 'Y' else (0, 1, 0))
        A[2].face([pts_f[1], pts_f[2], pts_b[2], pts_b[1]], M[mat + '2'], (0, 0, 1))
    A[1].face([V(*P(-r, t / 2 + 0.02), z), V(*P(r, t / 2 + 0.02), z), V(*P(r, t / 2 + 0.02), zs), V(*P(-r, t / 2 + 0.02), zs)], M['env_deep'], (0, -1, 0) if axis == 'X' else (1, 0, 0))


# ───────────────────────── 콜로세움 섬(아레나-참조-localbanana): 자갈 포장 위 유적·기둥·풀 무리 ─────────────────────────
def env_colosseum(M, block_root, colo_root, rect, seed=1.0):
    A = [Acc() for _ in range(7)]
    x0, x1, y0, y1 = rect
    bx = plan_bbox(colo_root)
    cx, cy = 0.5 * (bx[0] + bx[1]), 0.5 * (bx[2] + bx[3]); rx, ry = 0.5 * (bx[1] - bx[0]) + 2.5, 0.5 * (bx[3] - bx[2]) + 2.5
    free = lambda X, Y, m=0.0: x0 + 2.5 + m < X < x1 - 2.5 - m and y0 + 2.5 + m < Y < y1 - 2.5 - m and ((X - cx) / (rx + m)) ** 2 + ((Y - cy) / (ry + m)) ** 2 > 1.0
    z = 0.12 * 0.9
    # 모서리 유적 무리: 기둥 그루터기 줄 · 쓰러진 기둥 · 낮은 벽 · 작은 신전 앞면 · 아치 유적
    corners = [(x0 + 9, y0 + 9), (x1 - 10, y0 + 9), (x0 + 9, y1 - 10), (x1 - 10, y1 - 10), (x0 + 9, 0.5 * (y0 + y1)), (0.5 * (x0 + x1), y1 - 8)]
    for ci, (X, Y) in enumerate(corners):
        if not free(X, Y, 1.0):
            continue
        kind = ci % 3
        if kind == 0:                                                          # 기둥 줄(열주 유적)
            for k in range(5):
                Xk, Yk = X - 4 + 2.0 * k, Y
                if free(Xk, Yk):
                    _column(A, M, Xk, Yk, z, 0.45, 1.0 + 3.2 * hsh(k, ci, seed), True, seed + k)
            A[2].box(X - 5, X + 5, Y - 1.2, Y + 1.2, z, z + 0.25, M['env_trav'], M['env_trav2'])
            _drum_lying(A, M, X + 2, Y + 3.0, z, 0.45, 1.6, 0.6)
            _drum_lying(A, M, X - 2.5, Y + 3.4, z, 0.45, 1.2, 2.2)
        elif kind == 1:                                                        # 작은 신전 앞면(기단 + 기둥 4 + 엔타블러처 조각)
            A[0].box(X - 4, X + 4, Y - 3, Y + 3, z, z + 0.8, M['env_trav'], M['env_trav2'])
            A[3].box(X - 3.6, X + 3.6, Y - 2.6, Y + 2.6, z + 0.8, z + 0.85, M['env_trav2'], M['env_trav2'])
            for k in range(4):
                _column(A, M, X - 3 + 2 * k, Y + 2.0, z + 0.8, 0.42, 4.2, False, seed + 10 + k)
            A[2].box(X - 3.5, X + 1.2, Y + 1.5, Y + 2.5, z + 5.0, z + 5.6, M['env_trav'], M['env_trav2'])
            A[4].box(X + 1.2, X + 2.4, Y + 1.6, Y + 2.4, z + 0.85, z + 1.3, M['env_trav'], M['env_trav2'])
        else:                                                                  # 무너진 벽 + 아치 유적
            _ruin_wall(A, M, X - 5, Y, X + 4, Y, z, 2.6, 0.8, seed + ci, 'env_stone')
            _arch_ruin(A, M, X, Y + 3.5, z, 4.2, 4.6, 'X', seed + ci)
    # 풀·덤불 무리 · 흙 드러난 자리 · 흩어진 돌
    for k in range(70):
        X = x0 + 3 + (x1 - x0 - 6) * hsh(k, seed, 2.1); Y = y0 + 3 + (y1 - y0 - 6) * hsh(k, seed, 2.2)
        if not free(X, Y, 0.5):
            continue
        r = 0.6 + 1.6 * hsh(k, seed, 2.3)
        _patch(A, 3, X, Y, z + 0.02, r * 1.6, r * 1.1, M['env_grass'] if k % 3 else M['env_dry'], 9, seed + k)
        for q in range(2):
            _shrub(A, X + r * (hsh(k, q, 2.4) - 0.5), Y + r * (hsh(k, q, 2.5) - 0.5), z, 0.35 + 0.5 * hsh(k, q, 2.6), M, seed + k + q, k % 4 == 0)
    for k in range(60):
        X = x0 + 3 + (x1 - x0 - 6) * hsh(k, seed, 3.1); Y = y0 + 3 + (y1 - y0 - 6) * hsh(k, seed, 3.2)
        if not free(X, Y, 0.3):
            continue
        w = 0.3 + 0.7 * hsh(k, 3.3)
        A[4].box(X - w, X + w, Y - w * 0.6, Y + w * 0.6, z, z + 0.25 + 0.4 * hsh(k, 3.4), M['env_stone'], M['env_stone2'])
    for k in range(30):
        X = x0 + 3 + (x1 - x0 - 6) * hsh(k, seed, 4.1); Y = y0 + 3 + (y1 - y0 - 6) * hsh(k, seed, 4.2)
        if free(X, Y, 0.5):
            _patch(A, 3, X, Y, z + 0.015, 1.5 + 2.5 * hsh(k, 4.3), 1.0 + 1.5 * hsh(k, 4.4), M['pv_bed'], 7, seed + 40 + k)
    _patch(A, 5, x0 + 4, y0 + 4, z + 0.03, 0.8, 0.5, M['ash_cope'], 6, 1.0)
    return _finish(A, 'Colosseum', block_root)


# ───────────────────────── 아크로폴리스(user_acropolis_hill): 성벽 발치 석회암 너덜·노두·떨어진 덩이·마른 풀 ─────────────────────────
def env_acropolis(M, block_root, acro_root, seed=2.0):
    A = [Acc() for _ in range(7)]
    bx = plan_bbox(acro_root)
    X0, X1, Y0, Y1 = bx
    for side in ('E', 'S'):                                                    # 보이는 두 변(+X · +Y) 발치
        Lr = (Y1 - Y0) if side == 'E' else (X1 - X0)
        for k in range(int(Lr / 1.6)):
            t = (k + 0.5) / int(Lr / 1.6)
            d = 0.6 + 4.5 * hsh(k, side == 'E', seed, 5.1) ** 1.6
            X, Y = (X1 + d, Y0 + Lr * t) if side == 'E' else (X0 + Lr * t, Y1 + d)
            r = 0.5 + 1.4 * hsh(k, seed, 5.2) * (1.0 - d / 6.0)
            A[4].blob(X, Y, 0.1 + r * 0.25, r * 1.3, r, r * 0.7, M['lime'], 1, 0.3, seed + k, M['lime_top'], M['lime_dk'])
            if hsh(k, 5.3) < 0.5:
                _patch(A, 3, X + 1.0, Y + 1.0, 0.03, 1.2 + 1.5 * hsh(k, 5.4), 0.9, M['env_stone2'] if k % 2 else M['lime_top'], 7, seed + k)
            if hsh(k, 5.5) < 0.45:
                _shrub(A, X + 1.5 * hsh(k, 5.6), Y + 1.5 * hsh(k, 5.7), 0.0, 0.35 + 0.4 * hsh(k, 5.8), M, seed + 20 + k, k % 2 == 0)
            if hsh(k, 5.9) < 0.25:
                w = 0.6 + 0.6 * hsh(k, 6.1)
                A[2].box(X + 2.0 - w, X + 2.0 + w, Y + 1.0 - w * 0.6, Y + 1.0 + w * 0.6, 0.0, 0.5 + 0.4 * hsh(k, 6.2), M['marble_blk'], M['marble_blk_s'])
    A[1].face([V(X1, Y0, 0.02), V(X1 + 0.8, Y0, 0.02), V(X1 + 0.8, Y1, 0.02), V(X1, Y1, 0.02)], M['env_dry2'], (0, 0, 1))
    A[5].face([V(X1 + 5.3, Y0, 0.02), V(X1 + 5.5, Y0, 0.02), V(X1 + 5.5, Y1 + 5.5, 0.02), V(X1 + 5.3, Y1 + 5.5, 0.02)], M['ash_cope'], (0, 0, 1))
    A[6].face([V(X1 + 1, Y1 + 1, 0.025), V(X1 + 2, Y1 + 1, 0.025), V(X1 + 1.5, Y1 + 2, 0.025)], M['env_grass2'], (0, 0, 1))
    return _finish(A, 'Acropolis', block_root)


# ───────────────────────── 트라야누스 시장(user_trajan_markets): 뒤쪽 토레 델레 밀리치에(벽돌 탑) ─────────────────────────
def env_market(M, block_root, market_root, lot, seed=3.0):
    A = [Acc() for _ in range(7)]
    x0, x1, y0, y1, zl = lot
    bx = plan_bbox(market_root)
    X, Y = max(x0 + 4.5, bx[0] + 2.0), max(y0 + 4.5, bx[2] - 0.5)
    X = min(X, x1 - 5); Y = min(Y, y1 - 5)
    w1, w2, h1, h2 = 4.2, 3.4, 14.0, 21.0
    A[0].box(X - w1, X + w1, Y - w1, Y + w1, zl, zl + h1, M['env_brick'], M['env_brick'], sides='ES')
    A[0].box(X - w2, X + w2, Y - w2, Y + w2, zl + h1, zl + h2, M['env_brick'], M['env_brick'], sides='ES')
    for zz in (zl + 4.0, zl + 8.0, zl + h1 - 0.3, zl + h1 + 3.5):                # 띠돌(L2)
        ww = w1 if zz < zl + h1 else w2
        A[2].box(X - ww - 0.12, X + ww + 0.12, Y - ww - 0.12, Y + ww + 0.12, zz, zz + 0.3, M['bw_frame'], M['bw_frame'], sides='ES')
    for c in range(-3, 4):                                                     # 흉벽 톱니(L2)
        for (dx, dy) in ((w2, c * 0.95), (c * 0.95, w2)):
            A[2].box(X + dx - 0.25, X + dx + 0.12, Y + dy - 0.3, Y + dy + 0.3, zl + h2, zl + h2 + 0.7, M['env_brick2'], M['env_brick'])
    for row, zz in enumerate((zl + 2.0, zl + 6.0, zl + 10.0, zl + 16.5, zl + 19.0)):   # 창(L1)
        ww = w1 if zz < zl + h1 else w2
        for c in (-0.5, 0.5) if ww > 4 else (0.0,):
            A[1].face([V(X + ww + 0.02, Y + c * 2.8 - 0.35, zz), V(X + ww + 0.02, Y + c * 2.8 + 0.35, zz), V(X + ww + 0.02, Y + c * 2.8 + 0.35, zz + 1.1), V(X + ww + 0.02, Y + c * 2.8 - 0.35, zz + 1.1)],
                      M['env_deep'], (1, 0, 0))
            A[1].face([V(X + c * 2.8 - 0.35, Y + ww + 0.02, zz), V(X + c * 2.8 + 0.35, Y + ww + 0.02, zz), V(X + c * 2.8 + 0.35, Y + ww + 0.02, zz + 1.1), V(X + c * 2.8 - 0.35, Y + ww + 0.02, zz + 1.1)],
                      M['env_deep'], (0, -1, 0))
    for k in range(int(h1 / 0.55)):                                            # 벽돌 켜(L3)
        zz = zl + 0.3 + 0.55 * k
        A[3].face([V(X + w1 + 0.01, Y - w1, zz), V(X + w1 + 0.01, Y + w1, zz), V(X + w1 + 0.01, Y + w1, zz + 0.06), V(X + w1 + 0.01, Y - w1, zz + 0.06)], M['env_brick2'], (1, 0, 0))
        A[3].face([V(X - w1, Y + w1 + 0.01, zz), V(X + w1, Y + w1 + 0.01, zz), V(X + w1, Y + w1 + 0.01, zz + 0.06), V(X - w1, Y + w1 + 0.01, zz + 0.06)], M['env_brick2'], (0, -1, 0))
    A[4].box(X - w1 - 0.6, X + w1 + 0.6, Y - w1 - 0.6, Y + w1 + 0.6, zl, zl + 1.0, M['env_stone'], M['env_stone2'])    # 밑동 돌
    A[5].box(X + w2 - 0.05, X + w2 + 0.02, Y - w2, Y + w2, zl + h1, zl + h2, M['env_brick_hi'], M['env_brick_hi'], sides='E')
    for k in range(8):                                                         # 얼룩 · 꼭대기 풀
        zz = zl + 2 + (h2 - 4) * hsh(k, seed, 6.3)
        A[6].face([V(X + w1 + 0.03, Y - 2 + 4 * hsh(k, 6.4), zz), V(X + w1 + 0.03, Y - 1.5 + 4 * hsh(k, 6.4), zz), V(X + w1 + 0.03, Y - 1.7 + 4 * hsh(k, 6.4), zz - 2.5)],
                  M['env_stain'], (1, 0, 0))
    _shrub(A, X, Y, zl + h2 + 0.1, 0.8, M, seed)
    return _finish(A, 'MarketTower', block_root)


# ───────────────────────── 메텔라(user_metella, 피라네시): 무너진 카에타니 성벽·아치 · 잔해 더미 · 덤불·담쟁이 ─────────────────────────
ZF = None


def env_metella(M, block_root, lot, met_root, seed=4.0):
    A = [Acc() for _ in range(7)]
    x0, x1, y0, y1, zl = lot
    bx = plan_bbox(met_root)
    _ruin_wall(A, M, x0 + 2.0, y0 + 2.0, x1 - 2.0, y0 + 2.0, 0.0, 6.5 + zl, 1.2, seed, 'env_stone', True)      # 뒤 성벽(흉벽 톱니) — 둔덕 땅을 뚫고 선다
    _ruin_wall(A, M, x0 + 2.0, y0 + 2.0, x0 + 2.0, y1 - 8.0, 0.0, 5.5 + zl, 1.2, seed + 1, 'env_stone', True)
    _arch_ruin(A, M, x0 + 2.0, y1 - 13.0, 0.0, 6.0, 7.5 + zl, 'Y', seed)
    _arch_ruin(A, M, x1 - 9.0, y0 + 2.0, 0.0, 5.4, 6.8 + zl, 'X', seed + 2)
    for k in range(26):                                                        # 잔해 더미 · 덤불 · 담쟁이
        X = x0 + 3 + (x1 - x0 - 6) * hsh(k, seed, 7.1); Y = y0 + 3 + (y1 - y0 - 6) * hsh(k, seed, 7.2)
        if bx[0] - 1 < X < bx[1] + 1 and bx[2] - 1 < Y < bx[3] + 1:
            continue
        zk = ZF(X, Y) if ZF else zl
        if k % 3 == 0:
            for q in range(4):
                r = 0.4 + 0.5 * hsh(k, q, 7.3)
                A[4].blob(X + 1.2 * (hsh(k, q, 7.4) - 0.5), Y + 1.2 * (hsh(k, q, 7.5) - 0.5), zk + r * 0.3, r * 1.2, r, r * 0.6, M['md_rubble'], 1, 0.3, seed + k + q, M['md_rubble2'], None)
        else:
            _shrub(A, X, Y, zk, 0.5 + 0.8 * hsh(k, 7.6), M, seed + k, k % 4 == 1)
    for k in range(10):
        X = x0 + 2.6; Y = y0 + 4 + (y1 - y0 - 14) * hsh(k, 7.7); zz = zl + 1 + 3 * hsh(k, 7.8)
        A[6].face([V(X, Y, zz), V(X, Y + 0.9, zz + 0.3), V(X, Y + 0.5, zz - 1.6)], M['env_ivy'], (1, 0, 0))
    _patch(A, 3, 0.5 * (x0 + x1) + 8, y1 - 6, (ZF(0.5 * (x0 + x1) + 8, y1 - 6) if ZF else zl) + 0.04, 3.0, 2.0, M['env_dry'], 8, seed)
    _patch(A, 5, x0 + 2.0, y0 + 2.0, zl + 6.6, 0.4, 0.4, M['ash_cope'], 5, seed)
    return _finish(A, 'Metella', block_root)


# ───────────────────────── 포르투스(판화): 해안 평야 풀밭 · 해안 쪽 낮은 성벽 ─────────────────────────
def env_portus(M, block_root, hex_root, seed=5.0):
    A = [Acc() for _ in range(7)]
    bx = plan_bbox(hex_root)
    X0, X1, Y0, Y1 = bx
    meadows = [(X0 - 14, Y0 + 6, 9.0, 12.0), (X1 + 14, Y0 + 14, 11.0, 9.0), (X0 - 14, Y1 - 4, 8.0, 6.0), (X1 + 10, Y1 - 6, 7.0, 6.0)]   # 레퍼런스 판화의 초지(밭 줄 0)
    for fi, (mx, my, rx, ry) in enumerate(meadows):
        if my + ry * 0.7 > 378.0:
            my = 378.0 - ry * 0.7
        _patch(A, 3, mx, my, 0.02, rx, ry, M['env_field'] if fi % 2 else M['env_field2'], 14, seed + fi)
        _patch(A, 1, mx + rx * 0.2, my + ry * 0.25, 0.025, rx * 0.45, ry * 0.35, M['env_grass2'], 10, seed + fi + 0.5)
        for k in range(14):
            a = 2 * math.pi * hsh(k, fi, 8.1); t = hsh(k, fi, 8.2) ** 0.6
            _shrub(A, mx + rx * 0.9 * t * math.cos(a), my + ry * 0.9 * t * math.sin(a), 0.0, 0.4 + 0.5 * hsh(k, fi, 8.3), M, seed + fi * 10 + k, k % 4 == 0)
    _ruin_wall(A, M, X0 - 20, 376.0, X0 - 2, 376.0, 0.0, 2.2, 1.0, seed, 'env_stone', True)
    A[0].face([V(X0 - 24, Y0 - 8, 0.01), V(X0 - 4, Y0 - 8, 0.01), V(X0 - 4, Y0 - 6, 0.01), V(X0 - 24, Y0 - 6, 0.01)], M['env_dry'], (0, 0, 1))
    A[2].box(X0 - 24, X0 - 4, Y0 - 6.4, Y0 - 6.0, 0.0, 0.5, M['env_stone'], M['env_stone2'])
    A[4].box(X0 - 12, X0 - 11, Y0 - 6.5, Y0 - 5.9, 0.0, 0.9, M['env_stone'], M['env_stone2'])
    A[5].face([V(X0 - 24, Y0 - 6.4, 0.52), V(X0 - 4, Y0 - 6.4, 0.52), V(X0 - 4, Y0 - 6.2, 0.52), V(X0 - 24, Y0 - 6.2, 0.52)], M['ash_cope'], (0, 0, 1))
    return _finish(A, 'Portus', block_root)


# ───────────────────────── 영묘(user_hadrian_bridge, Castle Howard): 언덕 따라 긴 테라스 벽(부벽·난간) · 둘레 잔디 ─────────────────────────
def env_mausoleum(M, block_root, maus_root, seed=6.0):
    A = [Acc() for _ in range(7)]
    bx = plan_bbox(maus_root)
    X0, X1, Y0, Y1 = bx
    cy = 0.5 * (Y0 + Y1)
    xa, xb = X1 - 2.0, min(X1 + 34.0, 566.0)
    for (y_, h_) in ((cy - 1.0, 2.6),):
        A[0].box(xa, xb, y_ - 0.9, y_ + 0.9, 0.0, h_, M['ash_a'], M['ash_b'])                     # 긴 테라스 벽
        A[2].box(xa, xb, y_ - 1.05, y_ + 1.05, h_, h_ + 0.25, M['ash_cope'], M['ash_cope'])       # 갓돌
        x = xa + 2.0
        while x < xb - 1.0:
            A[2].box(x - 0.45, x + 0.45, y_ + 0.9, y_ + 1.7, 0.0, h_ - 0.3, M['ash_a'], M['ash_b'])   # 부벽
            A[4].box(x - 0.35, x + 0.35, y_ - 0.5, y_ + 0.5, h_ + 0.25, h_ + 1.0, M['ash_cope'], M['ash_a'])  # 난간 기둥받침
            x += 3.2
        x = xa + 0.6
        while x < xb - 0.4:                                                     # 동자 기둥
            A[4].cyl(x, y_, 0.12, h_ + 0.25, h_ + 0.85, M['ash_lt'], 6, True)
            x += 0.5
        A[4].box(xa, xb, y_ - 0.25, y_ + 0.25, h_ + 0.85, h_ + 1.0, M['ash_cope'], M['ash_cope'])
        for k in range(int((xb - xa) / 0.9)):                                   # 켜(L3) · 얼룩(L6)
            xx = xa + 0.9 * k
            A[3].face([V(xx, y_ + 0.91, 0.1), V(xx + 0.05, y_ + 0.91, 0.1), V(xx + 0.05, y_ + 0.91, h_ - 0.1), V(xx, y_ + 0.91, h_ - 0.1)], M['ash_joint'], (0, -1, 0))
        for k in range(10):
            xx = xa + (xb - xa) * hsh(k, seed, 9.1)
            A[6].face([V(xx, y_ + 0.93, h_ - 0.2), V(xx + 0.8, y_ + 0.93, h_ - 0.2), V(xx + 0.5, y_ + 0.93, h_ - 1.6)], M['ash_stain'], (0, -1, 0))
        A[5].face([V(xa, y_ + 1.05, h_ + 0.26), V(xb, y_ + 1.05, h_ + 0.26), V(xb, y_ + 0.85, h_ + 0.26), V(xa, y_ + 0.85, h_ + 0.26)], M['hi'] if 'hi' in M else M['ash_cope'], (0, 0, 1))
        A[1].face([V(xa, y_ + 1.75, 0.02), V(xb, y_ + 1.75, 0.02), V(xb, y_ + 2.6, 0.02), V(xa, y_ + 2.6, 0.02)], M['gb_grass2'], (0, 0, 1))
    return _finish(A, 'Mausoleum', block_root)


# ───────────────────────── 네로 받침(user_nero_base): 판석 마당 · 뒤 주랑 ─────────────────────────
def env_nero(M, block_root, center, seed=7.0, half=11.0):
    A = [Acc() for _ in range(7)]
    cx, cy = center
    A[0].face([V(cx - half, cy - half, 0.02), V(cx + half, cy - half, 0.02), V(cx + half, cy + half, 0.02), V(cx - half, cy + half, 0.02)], M['env_trav'], (0, 0, 1))
    g = 1.6
    x = cx - half + g
    while x < cx + half:
        A[3].face([V(x - 0.04, cy - half, 0.03), V(x + 0.04, cy - half, 0.03), V(x + 0.04, cy + half, 0.03), V(x - 0.04, cy + half, 0.03)], M['env_trav_dk'], (0, 0, 1))
        x += g
    y = cy - half + g
    while y < cy + half:
        A[3].face([V(cx - half, y - 0.04, 0.03), V(cx + half, y - 0.04, 0.03), V(cx + half, y + 0.04, 0.03), V(cx - half, y + 0.04, 0.03)], M['env_trav_dk'], (0, 0, 1))
        y += g
    for k in range(10):                                                         # 두 톤 판석
        X = cx - half + 1 + (2 * half - 2) * hsh(k, seed, 1.1); Y = cy - half + 1 + (2 * half - 2) * hsh(k, seed, 1.2)
        A[1].face([V(X, Y, 0.025), V(X + 1.5, Y, 0.025), V(X + 1.5, Y + 1.5, 0.025), V(X, Y + 1.5, 0.025)], M['env_trav2'], (0, 0, 1))
    xs = cx - half + 0.8                                                        # 뒤 주랑(−X 변, 평면 Y 방향 열주)
    A[2].box(xs - 1.0, xs + 1.0, cy - half, cy + half, 0.0, 0.5, M['env_trav'], M['env_trav2'])
    y = cy - half + 1.0
    while y < cy + half - 0.5:
        A[0].cyl(xs, y, 0.32, 0.5, 5.6, M['env_col'], 10, True)
        A[4].box(xs - 0.45, xs + 0.45, y - 0.45, y + 0.45, 5.6, 5.9, M['env_trav'], M['env_trav2'])
        y += 2.2
    A[2].box(xs - 0.6, xs + 0.6, cy - half, cy + half, 5.9, 6.6, M['env_trav'], M['env_trav2'])
    A[5].face([V(xs + 0.6, cy - half, 6.61), V(xs + 0.6, cy + half, 6.61), V(xs + 0.4, cy + half, 6.61), V(xs + 0.4, cy - half, 6.61)], M['ash_cope'], (0, 0, 1))
    for k in range(6):
        _shrub(A, cx - half + 0.5 + (2 * half - 1) * hsh(k, 1.3), cy + half - 0.6, 0.0, 0.3 + 0.3 * hsh(k, 1.4), M, seed + k)
    return _finish(A, 'Nero', block_root)


# ───────────────────────── 마르켈루스(입지: 테베레 범람원): 무대 쪽 트래버틴 포장 ─────────────────────────
def env_marcellus(M, block_root, mc_root, seed=8.0):
    A = [Acc() for _ in range(7)]
    X0, X1, Y0, Y1 = plan_bbox(mc_root)
    a, b, c, d = X0 - 4, X1 + 2, Y1 - 1, Y1 + 6
    A[0].face([V(a, c, 0.02), V(b, c, 0.02), V(b, d, 0.02), V(a, d, 0.02)], M['env_trav'], (0, 0, 1))
    x = a + 1.4
    while x < b:
        A[3].face([V(x - 0.04, c, 0.03), V(x + 0.04, c, 0.03), V(x + 0.04, d, 0.03), V(x - 0.04, d, 0.03)], M['env_trav_dk'], (0, 0, 1))
        x += 1.4
    for k in range(8):
        X = a + (b - a) * hsh(k, seed, 2.1)
        A[4].box(X - 0.5, X + 0.5, d - 1.2, d - 0.4, 0.0, 0.4, M['env_stone'], M['env_stone2'])
        _shrub(A, X + 1.2, d + 0.6, 0.0, 0.35, M, seed + k)
    A[1].face([V(a, c - 0.6, 0.025), V(b, c - 0.6, 0.025), V(b, c, 0.025), V(a, c, 0.025)], M['env_trav_dk'], (0, 0, 1))
    A[2].box(a, b, d, d + 0.4, 0.0, 0.35, M['env_trav'], M['env_trav2'])
    A[5].face([V(a, d, 0.36), V(b, d, 0.36), V(b, d + 0.15, 0.36), V(a, d + 0.15, 0.36)], M['ash_cope'], (0, 0, 1))
    return _finish(A, 'Marcellus', block_root)


# ───────────────────────── 지형 맞춤(23:39 사용자: 배치한 core에 맞게 땅을 바꿔 자연스럽게) ─────────────────────────
def _road_d(X, Y, roads):
    best = 1e9
    for r in roads:
        pts = r['pts']
        for (ax, ay), (bx_, by) in zip(pts, pts[1:]):
            ex, ey = bx_ - ax, by - ay; L2 = ex * ex + ey * ey or 1e-9
            t = max(0.0, min(1.0, ((X - ax) * ex + (Y - ay) * ey) / L2))
            best = min(best, math.hypot(X - ax - ex * t, Y - ay - ey * t) - 0.5 * r.get('w', 7.0))
    return best


def _hill(A, M, bbox, Hh, D, ok, seed=0.0, step=1.1, rocky=True, z0=0.0, path_side=None):
    """상자(bbox) 둘레로 솟는 언덕(바깥 거리 d에서 Hh·(1 − d/D)^1.35, 상자 안 Hh). ok(X, Y)가 거짓이면 그 칸은 짓지 않는다(블록 밖·길·물).
    재질: 가파른 곳 석회암 바위(3톤) · 완만한 곳 마른 풀 · 바닥 가장자리 흙빛. 덧층: 너덜(L3) · 노두(L4) · 덤불(L6) · 골 그늘(L1) · 등성이 밝은 선(L5) · 오르막 길(L2)"""
    x0, x1, y0, y1 = bbox
    cxh, cyh = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
    def zf(X, Y):
        dx = max(x0 - X, 0.0, X - x1); dy = max(y0 - Y, 0.0, Y - y1)
        a = math.atan2(Y - cyh, X - cxh)
        Dl = D * (0.8 + 0.25 * math.sin(3 * a + seed) + 0.12 * math.sin(7 * a + 2 * seed))   # 방향마다 다른 자락 길이(둥글고 불규칙)
        d = (dx ** 2.4 + dy ** 2.4) ** (1 / 2.4) + 0.35 * min(dx, dy)                         # 둥근 모서리
        if d >= Dl:
            return 0.0
        n = 1.0 + 0.05 * math.sin(X * 0.21 + seed) * math.sin(Y * 0.17 + 0.6 * seed)
        q = 1.0 - d / Dl
        return z0 + Hh * (q ** 1.25) * (0.75 + 0.25 * q) * n / (0.75 + 0.25)
    xs = [x0 - D + step * i for i in range(int((x1 - x0 + 2 * D) / step) + 1)]
    ys = [y0 - D + step * j for j in range(int((y1 - y0 + 2 * D) / step) + 1)]
    Lx, Ly = -0.62, 0.18
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            Xa, Xb, Ya, Yb = xs[i], xs[i + 1], ys[j], ys[j + 1]
            Xm, Ym = 0.5 * (Xa + Xb), 0.5 * (Ya + Yb)
            if x0 + 0.5 < Xm < x1 - 0.5 and y0 + 0.5 < Ym < y1 - 0.5:
                continue
            if not ok(Xm, Ym):
                continue
            zz = [zf(Xa, Ya), zf(Xb, Ya), zf(Xb, Yb), zf(Xa, Yb)]
            if max(zz) < 0.04:
                continue
            p = [V(Xa, Ya, zz[0] + 0.02), V(Xb, Ya, zz[1] + 0.02), V(Xb, Yb, zz[2] + 0.02), V(Xa, Yb, zz[3] + 0.02)]
            for tri in ((0, 1, 2), (0, 2, 3)):
                tp = [p[t] for t in tri]
                nrm = (Vector(tp[1]) - Vector(tp[0])).cross(Vector(tp[2]) - Vector(tp[0]))
                if nrm.length < 1e-9:
                    continue
                nrm.normalize()
                if nrm.z < 0:
                    nrm = -nrm
                sl = math.hypot(nrm.x, nrm.y)
                dd = (nrm.x * Lx + nrm.y * Ly) / max(1e-6, sl * math.hypot(Lx, Ly))
                hz = max(zz[t] for t in tri) / max(Hh, 1e-6)
                if rocky and sl > 0.42:
                    mt = M['lime_top'] if dd > 0.55 else (M['lime_dk'] if dd < -0.55 else M['lime'])
                elif hz > 0.25:
                    mt = M['env_dry'] if dd > -0.2 else M['env_dry2']
                else:
                    mt = M['md_ground'] if dd > -0.2 else M['md_earth']
                A[0].face(tp, mt, (0, 0, 1))
    # 덧층
    for k in range(int((x1 - x0 + y1 - y0) * 2.2)):
        a = 2 * math.pi * hsh(k, seed, 1.1); t = hsh(k, seed, 1.2)
        X = 0.5 * (x0 + x1) + math.cos(a) * (0.5 * (x1 - x0) + D * t); Y = 0.5 * (y0 + y1) + math.sin(a) * (0.5 * (y1 - y0) + D * t)
        if (x0 < X < x1 and y0 < Y < y1) or not ok(X, Y):
            continue
        z = zf(X, Y)
        if z < 0.1:
            continue
        r = 0.4 + 1.2 * hsh(k, 1.3) * (0.4 + z / Hh)
        u = hsh(k, 1.4)
        if rocky and u < 0.35:
            A[4].blob(X, Y, z + r * 0.15, r * 1.3, r, r * 0.6, M['lime'], 1, 0.3, seed + k, M['lime_top'], M['lime_dk'])
        elif u < 0.6:
            _patch(A, 3, X, Y, z + 0.03, r * 1.5, r, M['lime_top'] if rocky else M['env_stone2'], 7, seed + k)
        elif u < 0.88:
            _shrub(A, X, Y, z, 0.35 + 0.45 * hsh(k, 1.5), M, seed + k, k % 3 == 0)
        else:
            A[1].face([V(X - 0.15, Y, z + 0.05), V(X + 0.15, Y, z + 0.05), V(X + 0.4, Y + 1.6, max(0.05, zf(X + 0.4, Y + 1.6)) + 0.05), V(X + 0.1, Y + 1.6, max(0.05, zf(X + 0.1, Y + 1.6)) + 0.05)],
                      M['lime_dk'], (0, 0, 1))
    for k in range(int((x1 - x0) / 2.0)):                                       # 상자 앞 두 변 위 등성이 밝은 선
        X = x0 + 2.0 * k + 1.0
        A[5].face([V(X, y1 + 0.2, Hh + 0.05), V(X + 1.6, y1 + 0.2, Hh + 0.05), V(X + 1.6, y1 + 0.6, zf(X + 1.6, y1 + 0.6) + 0.05), V(X, y1 + 0.6, zf(X, y1 + 0.6) + 0.05)], M['lime_top'], (0, 0, 1))
    if path_side == 'E':                                                        # 지그재그 오르막 길(+X 비탈)
        pts = []
        for q in range(7):
            d = D * (1.0 - q / 6.0) * 0.95
            Y = y0 + (y1 - y0) * (0.35 + 0.3 * (q % 2))
            pts.append((x1 + d, Y))
        for (ax, ay), (bx_, by) in zip(pts, pts[1:]):
            if not (ok(ax, ay) and ok(bx_, by)):
                continue
            n = 6
            for s_ in range(n):
                t0, t1 = s_ / n, (s_ + 1) / n
                Xa, Ya = ax + (bx_ - ax) * t0, ay + (by - ay) * t0; Xb, Yb = ax + (bx_ - ax) * t1, ay + (by - ay) * t1
                A[2].face([V(Xa, Ya - 0.7, zf(Xa, Ya - 0.7) + 0.06), V(Xb, Yb - 0.7, zf(Xb, Yb - 0.7) + 0.06), V(Xb, Yb + 0.7, zf(Xb, Yb + 0.7) + 0.06), V(Xa, Ya + 0.7, zf(Xa, Ya + 0.7) + 0.06)],
                          M['env_trav2'], (0, 0, 1))
    return zf


def env_terrain(M, spec_dio):
    """건물 둘레 땅 맞춤: 아크로폴리스 바위 언덕(성벽이 언덕 꼭대기 성채) · 시장 뒤 비탈 언덕 · 막센티우스 포룸 유적 기둥"""
    g = lambda n: bpy.data.objects.get(n)
    roads = spec_dio.get('roads') or []
    blocks = {b['id']: [tuple(p) for p in b['poly']] for b in spec_dio.get('blocks', [])}
    out = {}
    def ok_in(bid, margin_road=1.2, extra=None):
        P = blocks[bid]
        return lambda X, Y: GR.pip(X, Y, P) and _road_d(X, Y, roads) > margin_road and (extra is None or extra(X, Y))
    ac = g('CITY_Acropolis_root')
    if ac:
        A = [Acc() for _ in range(7)]
        bb = plan_bbox(ac)
        bb = (bb[0] + 1.5, bb[1] - 1.5, bb[2] + 1.5, bb[3] - 1.5)
        _hill(A, M, bb, 8.5, 24.0, ok_in('C'), 11.0, 1.1, True, 0.0, 'E')
        out['acropolis_hill'] = len(_finish(A, 'AcropolisHill', g('DIO_Block_C_root')))
    mk = g('CITY_TrajanMarket_root')
    lots = {lt['id']: lt for lt in spec_dio.get('lots', [])}
    if mk and 'market' in lots:
        A = [Acc() for _ in range(7)]
        r = lots['market']['rect']; zl = float(lots['market']['z'])
        bb = (r[0], r[1], r[2], r[3])
        inside_lot = lambda X, Y: not (r[0] - 0.5 < X < r[1] + 0.5 and r[2] - 0.5 < Y < r[3] + 0.5)
        back = lambda X, Y: (X < r[0] + 6 or Y < r[2] + 6)                         # 뒤(−X · −Y) 쪽만: 퀴리날레 비탈
        _hill(A, M, bb, zl + 4.0, 20.0, ok_in('C', 1.2, lambda X, Y: inside_lot(X, Y) and back(X, Y)), 13.0, 1.2, False)
        out['market_hill'] = len(_finish(A, 'MarketHill', g('DIO_Block_C_root')))
    mx = g('CITY_Maxentius_root')
    if mx and 'basilica' in lots:
        A = [Acc() for _ in range(7)]
        r = lots['basilica']['rect']; zl = float(lots['basilica']['z'])
        k = 0
        for (X, Y) in [(r[0] + 2 + 3.2 * i, r[3] + 2.2) for i in range(int((r[1] - r[0] - 2) / 3.2))] + [(r[1] + 2.2, r[2] + 2 + 3.2 * j) for j in range(int((r[3] - r[2] - 2) / 3.2))]:
            if not ok_in('B')(X, Y):
                continue
            _column(A, M, X, Y, 0.0, 0.42, 0.8 + 2.6 * hsh(k, 21.1), True, 21.0 + k)
            if k % 3 == 0:
                _drum_lying(A, M, X + 1.0, Y + 1.2, 0.0, 0.42, 1.2, 0.4 + k)
            k += 1
        _patch(A, 3, r[1] + 3, r[3] + 3, 0.02, 4.0, 2.5, M['fr_slab2'], 8, 21.0)
        _patch(A, 6, r[1] + 5, r[3] + 1, 0.025, 1.6, 1.0, M['env_grass2'], 7, 22.0)
        A[0].face([V(r[0], r[3] + 0.5, 0.012), V(r[1] + 4, r[3] + 0.5, 0.012), V(r[1] + 4, r[3] + 4, 0.012), V(r[0], r[3] + 4, 0.012)], M['fr_slab3'], (0, 0, 1))
        A[1].face([V(r[0], r[3] + 0.5, 0.02), V(r[1] + 4, r[3] + 0.5, 0.02), V(r[1] + 4, r[3] + 0.9, 0.02), V(r[0], r[3] + 0.9, 0.02)], M['fr_conc2'], (0, 0, 1))
        A[5].face([V(r[0], r[3] + 3.8, 0.02), V(r[1] + 4, r[3] + 3.8, 0.02), V(r[1] + 4, r[3] + 4, 0.02), V(r[0], r[3] + 4, 0.02)], M['ash_cope'], (0, 0, 1))
        A[2].box(r[1] + 0.5, r[1] + 1.2, r[2], r[3] + 4, 0.0, 0.6, M['env_trav'], M['env_trav2'])
        out['maxentius_forum'] = len(_finish(A, 'MaxentiusForum', g('DIO_Block_B_root')))
    return out


def env_groundcover(M, spec_dio, keep_roots, seed=9.0):
    """23:40 사용자: 모든 디오라마 고도화 — 블록 윗면 넓은 땅에 풀 포기(L6)·흙·마른 풀 얼룩(L3)·잔돌(L4)·밝은 돌(L5)·그늘 흙(L1)"""
    g = lambda n: bpy.data.objects.get(n)
    roads = spec_dio.get('roads') or []
    lots = [lt['rect'] for lt in spec_dio.get('lots', []) if float(lt.get('z') or 0) > 0]
    boxes = []
    for rn in keep_roots:
        r = g(rn)
        if r is not None:
            b = plan_bbox(r); boxes.append((b[0] - 2.5, b[1] + 2.5, b[2] - 2.5, b[3] + 2.5))
    out = 0
    for b in spec_dio.get('blocks', []):
        P = [tuple(p) for p in b['poly']]
        FT = b.get('features') or []
        root = g('DIO_Block_%s_root' % b['id'])
        if root is None:
            continue
        xs = [p[0] for p in P]; ys = [p[1] for p in P]
        A = [Acc() for _ in range(7)]
        n = int((max(xs) - min(xs)) * (max(ys) - min(ys)) / 40.0)
        for k in range(n):
            X = min(xs) + (max(xs) - min(xs)) * hsh(k, seed, ord(b['id']), 1.1); Y = min(ys) + (max(ys) - min(ys)) * hsh(k, seed, ord(b['id']), 1.2)
            if not GR.pip(X, Y, P) or _road_d(X, Y, roads) < 0.8:
                continue
            if any(x0 < X < x1 and y0 < Y < y1 for x0, x1, y0, y1 in boxes) or any(r[0] - 1 < X < r[1] + 1 and r[2] - 1 < Y < r[3] + 1 for r in lots):
                continue
            # 블록 가장자리 1.5 안은 비운다(옆면 윗선)
            if min(min(abs(X - p0[0]) if abs(p0[0] - p1[0]) < 1e-6 and min(p0[1], p1[1]) - 1 < Y < max(p0[1], p1[1]) + 1 else 1e9,
                       abs(Y - p0[1]) if abs(p0[1] - p1[1]) < 1e-6 and min(p0[0], p1[0]) - 1 < X < max(p0[0], p1[0]) + 1 else 1e9) for p0, p1 in zip(P, P[1:] + P[:1])) < 1.5:
                continue
            u = hsh(k, ord(b['id']), 1.3)
            if FT and DI._in_feat(FT, X, Y) is not None:
                continue                                                       # 지형 특징 안은 그 특징의 장식이 맡는다
            if u < 0.42:                                                          # 가벼운 풀 포기(육각 기둥, 면 4개)
                for q in range(3):
                    r_ = 0.18 + 0.22 * hsh(k, q, 1.6)
                    A[6].cyl(X + 0.6 * (hsh(k, q, 1.4) - 0.5), Y + 0.6 * (hsh(k, q, 1.5) - 0.5), r_, 0.0, r_ * 0.9, M['env_dry'] if q == 2 else (M['env_grass2'] if q else M['env_grass']), 6, True)
            elif u < 0.66:
                _patch(A, 3, X, Y, 0.012, 0.8 + 1.6 * hsh(k, 1.7), 0.5 + 1.0 * hsh(k, 1.8), M['env_dry'] if k % 3 else M['md_ground'], 7, seed + k)
            elif u < 0.82:
                w = 0.15 + 0.3 * hsh(k, 1.9)
                A[4].box(X - w, X + w, Y - w * 0.7, Y + w * 0.7, 0.0, 0.1 + 0.2 * hsh(k, 2.1), M['env_stone'], M['env_stone2'])
                A[5].face([V(X - w * 0.6, Y - w * 0.4, 0.31), V(X + w * 0.2, Y - w * 0.4, 0.31), V(X - w * 0.2, Y, 0.31)], M['ash_cope'], (0, 0, 1)) if hsh(k, 2.2) < 0.2 else None
            elif u < 0.92:
                _patch(A, 1, X, Y, 0.01, 0.6 + 0.8 * hsh(k, 2.3), 0.4 + 0.5 * hsh(k, 2.4), M['md_earth'], 6, seed + k)
            else:
                _patch(A, 6, X, Y, 0.014, 1.0 + 1.4 * hsh(k, 2.5), 0.7 + 0.9 * hsh(k, 2.6), M['env_grass'], 8, seed + k)
        A[0].face([V(min(xs) + 0.5, min(ys) + 0.5, 0.004), V(min(xs) + 0.9, min(ys) + 0.5, 0.004), V(min(xs) + 0.7, min(ys) + 0.9, 0.004)], M['md_ground'], (0, 0, 1))
        A[2].face([V(min(xs) + 1.5, min(ys) + 0.5, 0.004), V(min(xs) + 1.9, min(ys) + 0.5, 0.004), V(min(xs) + 1.7, min(ys) + 0.9, 0.004)], M['md_ground'], (0, 0, 1))
        out += len(_finish(A, 'Cover%s' % b['id'], root))
    return out


def _ss(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def _rect_fade(X, Y, rect, w, open_sides=''):
    """사각형 가장자리 w 안에서 0으로(open_sides에 든 변 'x0','x1','y0','y1'은 블록 끝이라 줄이지 않는다)"""
    x0, x1, y0, y1 = rect
    f = 1.0
    if 'x0' not in open_sides: f *= _ss((X - x0) / w)
    if 'x1' not in open_sides: f *= _ss((x1 - X) / w)
    if 'y0' not in open_sides: f *= _ss((Y - y0) / w)
    if 'y1' not in open_sides: f *= _ss((y1 - Y) / w)
    return f


def _round_hill(core, Hh, D, seed):
    """core 사각형(윗면 Hh) 둘레로 둥글고 불규칙하게 내려가는 언덕"""
    x0, x1, y0, y1 = core
    cx, cy = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
    def z(X, Y):
        dx = max(x0 - X, 0.0, X - x1); dy = max(y0 - Y, 0.0, Y - y1)
        if dx == 0.0 and dy == 0.0:
            return Hh
        a = math.atan2(Y - cy, X - cx)
        Dl = D * (0.8 + 0.22 * math.sin(3 * a + seed) + 0.1 * math.sin(7 * a + 2 * seed))
        d = (dx ** 2.4 + dy ** 2.4) ** (1 / 2.4) + 0.3 * min(dx, dy)
        if d >= Dl:
            return 0.0
        q = 1.0 - d / Dl
        return Hh * (q ** 1.3) * (1.0 + 0.04 * math.sin(X * 0.23 + seed) * math.sin(Y * 0.19))
    return z


def _mat_rocky(Hh, low='land'):
    """높이·경사로만 정한다(방향 명암은 면 톤이 맡는다): 위쪽·가파른 곳 석회암 · 가운데 마른 풀 · 아래 흙 · 가장자리 땅"""
    def m(X, Y, z, sl, dd):
        if z < 0.45:
            return low
        h = z / max(Hh, 1e-6)
        n_ = 0.08 * math.sin(X * 0.7 + Y * 0.5)
        if sl > 0.55 or h + n_ > 0.62:
            return 'lime_top' if sl < 0.25 else 'lime'
        if h + n_ > 0.28:
            return 'env_dry'
        return 'md_ground'
    return m


def _mat_grass(Hh, low='land'):
    def m(X, Y, z, sl, dd):
        if z < 0.12:
            return low
        if sl > 0.7:
            return 'gb_grass2'
        return 'gb_grass3' if (z / max(Hh, 1e-6)) > 0.8 and sl < 0.2 else 'gb_grass'
    return m


def _deco_scatter(rect, n, seed, rocky=True, rubble=False):
    def deco(A, M, zf):
        x0, x1, y0, y1 = rect
        for k in range(n):
            X = x0 + (x1 - x0) * hsh(k, seed, 31.1); Y = y0 + (y1 - y0) * hsh(k, seed, 31.2)
            z = zf(X, Y)
            if z < 0.25:
                continue
            u = hsh(k, seed, 31.3); r = 0.35 + 0.9 * hsh(k, seed, 31.4)
            gx = zf(X + 0.6, Y) - zf(X - 0.6, Y); gy = zf(X, Y + 0.6) - zf(X, Y - 0.6)
            steep = math.hypot(gx, gy) > 0.9
            if rubble and u < 0.3:
                A[4].blob(X, Y, z + r * 0.2, r * 1.2, r, r * 0.6, M['md_rubble'], 1, 0.3, seed + k, M['md_rubble2'], None)
            elif rocky and steep and u < 0.55:
                A[4].blob(X, Y, z + r * 0.15, r * 1.3, r, r * 0.55, M['lime'], 1, 0.3, seed + k, M['lime_top'], M['lime_dk'])
            elif u < 0.75:
                _shrub(A, X, Y, z, 0.3 + 0.45 * hsh(k, 31.5), M, seed + k, rocky and k % 3 == 0)
            elif u < 0.9:
                _patch(A, 3, X, Y, z + 0.04, r * 1.4, r, M['lime_top'] if rocky else M['gb_grass3'], 7, seed + k)
            else:
                A[1].face([V(X - 0.12, Y, z + 0.05), V(X + 0.12, Y, z + 0.05), V(X + 0.35 + gx * 0.2, Y + 1.4, zf(X + 0.35, Y + 1.4) + 0.05), V(X + 0.1, Y + 1.4, zf(X + 0.1, Y + 1.4) + 0.05)],
                          M['lime_dk'] if rocky else M['gb_grass2'], (0, 0, 1))
        A[5].face([V(x0 + 0.3, y0 + 0.3, zf(x0 + 0.3, y0 + 0.3) + 0.03), V(x0 + 0.6, y0 + 0.3, zf(x0 + 0.6, y0 + 0.3) + 0.03), V(x0 + 0.45, y0 + 0.6, zf(x0 + 0.45, y0 + 0.6) + 0.03)], M['ash_cope'], (0, 0, 1))
        A[2].face([V(x0 + 0.8, y0 + 0.3, zf(x0 + 0.8, y0 + 0.3) + 0.03), V(x0 + 1.1, y0 + 0.3, zf(x0 + 1.1, y0 + 0.3) + 0.03), V(x0 + 0.95, y0 + 0.6, zf(x0 + 0.95, y0 + 0.6) + 0.03)], M['md_ground'], (0, 0, 1))
        A[6].face([V(x0 + 1.3, y0 + 0.3, zf(x0 + 1.3, y0 + 0.3) + 0.03), V(x0 + 1.6, y0 + 0.3, zf(x0 + 1.6, y0 + 0.3) + 0.03), V(x0 + 1.45, y0 + 0.6, zf(x0 + 1.45, y0 + 0.6) + 0.03)], M['gb_grass2'], (0, 0, 1))
    return deco


def block_features(spec_dio):
    """23:43 사용자: 블록 자체 지형 — 블록 id → 지형 특징 목록(사각형 rect · 높이 z · 합치기 op · 재질 mat · 칸 step · 장식 deco)"""
    import roma_aq_valley as AQ
    g = lambda n: bpy.data.objects.get(n)
    roads = spec_dio.get('roads') or []
    lots = {lt['id']: lt for lt in spec_dio.get('lots', [])}
    F = {'A': [], 'B': [], 'C': [], 'E': []}
    rf = lambda X, Y: _ss((_road_d(X, Y, roads) - 0.6) / 3.5)
    ac = g('CITY_Acropolis_root')
    if ac:                                                                     # C: 아크로폴리스 바위 언덕(성벽 = 언덕 꼭대기 성채)
        mw = ac.matrix_world                                                   # 언덕 꼭대기 = 성벽 본체 직사각형(보루 꺾임 바깥은 비탈)
        cs = [mw @ Vector((u, -v, 0.0)) for u, v in ((-41.0, -21.0), (41.0, 21.5))]
        core = (min(c.x for c in cs) + 0.8, max(c.x for c in cs) - 0.8, min(-c.y for c in cs) + 0.8, max(-c.y for c in cs) - 0.8)
        bx = plan_bbox(ac)
        KA = 1.5                                                               # 00:35 사용자 '아크로폴리스 지형 스케일은 1.5배': 언덕 높이·자락·범위 1.5배(장식은 같은 밀도)
        m_ = 24.0 * KA
        rect = (bx[0] - m_, min(bx[1] + m_, 316.0), bx[2] - m_, min(bx[3] + m_, 179.0))
        hz = _round_hill(core, 9.0 * KA, 24.0 * KA, 11.0)
        na = int(520 * (rect[1] - rect[0]) * (rect[3] - rect[2]) / (123.0 * 91.0))
        F['C'].append(dict(rect=rect, step=0.6, op='max', mat=_mat_rocky(9.0 * KA),
                           z=lambda X, Y, hz=hz, rect=rect: hz(X, Y) * rf(X, Y) * _rect_fade(X, Y, rect, 4.0, 'y1'),
                           deco=_deco_scatter(rect, na, 41.0, True)))
    VV = dict(x0=350.0, r0=387.0, r1=403.0, x1=440.0)                         # C: 수도교 골짜기(석회암 판 층계 · 강) + 양 끝 풀 언덕
    K, KH = 2.5, 2.5                                                           # 00:08 사용자: 수도교 양 끝 산 2.5배(바닥 넓이·높이). 확대 창(수로 방수층)은 수도교 동쪽 끝 자리라 2.0배여도 자락이 테에 걸린다 → 2.5배(대상점·라벨 칸은 비어 있음)
    hw = _round_hill((336.0 - 4.0 * K, 336.0 + 4.0 * K, -19.25 - 3.75 * K, -19.25 + 3.75 * K), 12.0 * KH, 24.0 * K, 3.0)
    he = _round_hill((453.0 - 4.0 * K, 453.0 + 4.0 * K, -19.25 - 3.75 * K, -19.25 + 3.75 * K), 11.0 * KH, 22.0 * K, 5.0)
    rectq = (336.0 - 4.0 * K - 24.0 * K - 2.0, 453.0 + 4.0 * K + 22.0 * K + 2.0, -19.25 - 3.75 * K - 24.0 * K - 2.0, min(-19.25 + 3.75 * K + 24.0 * K + 2.0, 60.0))
    def zq(X, Y):
        wy = _ss((Y + 52.0) / 10.0) * _ss((12.0 - Y) / 10.0)
        v = AQ.b7_valley_z(X, VV) * wy if VV['x0'] <= X <= VV['x1'] else 0.0      # 골짜기(음수) + 양 끝 언덕(양수, 골짜기 쪽 자락은 끊어 물·아치가 보이게)
        h = max(hw(X, Y) * _ss((372.0 - X) / 18.0), he(X, Y) * _ss((X - 418.0) / 18.0))
        return v + h * rf(X, Y) * _rect_fade(X, Y, rectq, 4.0)
    def mq(X, Y, z, sl, dd):
        if z < -1.2:
            return 'rk_c' if sl < 0.2 else ('rk_dark' if z < -6.9 else 'rk_b')
        if -1.2 <= z < -0.12:
            return 'gb_grass2' if sl > 0.3 else 'gb_grass'
        if z >= 0.12:
            if sl > 0.62 and z > 6.0:                                         # 큰 언덕 골짜기 쪽 벼랑 = 석회암 판 층(켜 4.5 · 짙은 틈)
                return 'rk_dark' if z % 4.5 < 0.7 else ('rk_a' if int(z / 4.5) % 2 else 'rk_b')
            if sl > 0.62:
                return 'gb_grass2'
            return 'gb_grass3' if z > 15.0 and sl < 0.25 else 'gb_grass'
        return 'land'
    nq = int(260 * (rectq[1] - rectq[0]) * (rectq[3] - rectq[2]) / (154.0 * 64.0))   # 장식 밀도는 1배 때와 같게
    F['C'].append(dict(rect=rectq, step=0.7, op='set', mat=mq, z=zq, deco=_deco_scatter(rectq, nq, 43.0, True)))
    if 'market' in lots:                                                      # C: 시장 뒤 퀴리날레 비탈(대지 z 8에서 바깥으로)
        r = lots['market']['rect']; zl = float(lots['market']['z'])
        rect = (r[0] - 22.0, min(r[1], 552.0), r[2] - 22.0, r[3])
        def zm(X, Y, r=r, zl=zl, rect=rect):
            if r[0] <= X <= r[1] and r[2] <= Y <= r[3]:
                return 0.0
            dx = max(r[0] - X, 0.0); dy = max(r[2] - Y, 0.0)
            d = math.hypot(dx, dy)
            q = max(0.0, 1.0 - d / 20.0)
            return zl * q ** 1.15 * rf(X, Y) * _rect_fade(X, Y, rect, 3.0, 'x1y1')
        F['C'].append(dict(rect=rect, step=0.8, op='max', mat=_mat_grass(zl), z=zm, deco=_deco_scatter(rect, 180, 47.0, False)))
    mz = g('COAST_HadrianMausoleum_root')
    if mz:                                                                     # B: 영묘 풀 언덕(모델 둔덕 대신 블록 땅)
        bx = plan_bbox(mz)
        cx, cy = 0.5 * (bx[0] + bx[1]), 0.5 * (bx[2] + bx[3])
        s_ = 1.12
        core = (cx - 19.0, cx + 19.0, cy - 19.0, cy + 19.0)
        rect = (cx - 30.0, cx + 30.0, cy - 30.0, min(cy + 30.0, 285.6))
        def zh(X, Y, core=core, rect=rect):
            dx = max(core[0] - X, 0.0, X - core[1]); dy = max(core[2] - Y, 0.0, Y - core[3])
            d = (dx ** 2.6 + dy ** 2.6) ** (1 / 2.6)
            q = max(0.0, 1.0 - d / 8.6)
            return 3.0 * s_ * (q ** 1.1) * _rect_fade(X, Y, rect, 2.0)
        F['B'].append(dict(rect=rect, step=0.7, op='max', mat=_mat_grass(3.36), z=zh, deco=_deco_scatter(rect, 120, 51.0, False)))
    hx = g('COAST_PortusHex_root')
    if hx:                                                                     # B: 포르투스 둘레 해안 초지(블록 땅 재질 영역)
        bx = plan_bbox(hx)
        for k, rect in enumerate(((bx[0] - 28.0, bx[0] - 2.0, bx[2] - 4.0, min(bx[3], 379.0)), (bx[1] + 2.0, min(bx[1] + 30.0, 568.0), bx[2] - 2.0, min(bx[3], 379.0)))):
            def mm(X, Y, z, sl, dd, k=k):
                n_ = 0.5 + 0.5 * math.sin(X * 0.09 + k) * math.sin(Y * 0.075 + 2 * k) + 0.12 * math.sin(X * 0.31 + Y * 0.23)
                return ('env_field' if n_ > 0.62 else 'env_field2') if n_ > 0.42 else 'land'
            F['B'].append(dict(rect=rect, step=0.8, op='max', mat=mm, z=lambda X, Y: 0.0, deco=_deco_scatter(rect, 0, 53.0 + k, False)))
    mc = g('CITY_Marcellus_root')
    if mc:                                                                     # B: 극장 무대 쪽 트래버틴 포장(재질 영역)
        X0, X1, Y0, Y1 = plan_bbox(mc)
        rect = (X0 - 4.0, X1 + 2.0, Y1 - 1.0, Y1 + 6.0)
        F['B'].append(dict(rect=rect, step=1.4, op='max', z=lambda X, Y: 0.0, mat=lambda X, Y, z, sl, dd: 'env_trav' if (int(X / 1.4) + int(Y / 1.4)) % 5 else 'env_trav2'))
    if 'metella' in lots and g('SUB_Metella_root'):                          # E: 메텔라 둔덕(대지 상자 대신 블록 땅)
        r = lots['metella']['rect']; zl = float(lots['metella']['z'])
        bx = plan_bbox(g('SUB_Metella_root'))
        core = (bx[0] - 1.0, bx[1] + 1.0, bx[2] - 1.0, bx[3] + 1.0)
        rect = (max(r[0] - 12.0, 597.0), r[1] + 12.0, r[2] - 12.0, min(r[3] + 12.0, 379.0))
        hz = _round_hill(core, zl, 18.0, 7.0)
        F['E'].append(dict(rect=rect, step=0.7, op='max', mat=lambda X, Y, z, sl, dd: ('md_earth' if sl > 0.35 else 'md_ground') if z > 0.15 else 'md_ground',
                           z=lambda X, Y, hz=hz, rect=rect: hz(X, Y) * rf(X, Y) * _rect_fade(X, Y, rect, 3.0), deco=_deco_scatter(rect, 160, 57.0, False, True)))
    return F


NERO_ENV = False


def build_all(spec_dio):
    """b7: 블록(지형 포함) 짓기 뒤에 부른다. 블록 위 장식(유적·탑·주랑·덤불)만 — 땅 모양은 block_features가 블록 안에서 짓는다"""
    M = mats()
    g = lambda n: bpy.data.objects.get(n)
    lots = {lt['id']: lt for lt in spec_dio.get('lots', [])}
    out = {}
    if g('HERO_Colosseum_root'):
        out['colosseum'] = len(env_colosseum(M, g('DIO_Block_A_root'), g('HERO_Colosseum_root'), (356.0, 472.0, 91.0, 208.0)))
    if g('CITY_TrajanMarket_root') and 'market' in lots:
        r = lots['market']['rect']; out['market'] = len(env_market(M, g('DIO_Block_Lot_market_root'), g('CITY_TrajanMarket_root'), (r[0], r[1], r[2], r[3], float(lots['market']['z']))))
    if g('SUB_Metella_root') and 'metella' in lots:
        r = lots['metella']['rect']; out['metella'] = len(env_metella(M, g('DIO_Block_E_root'), (r[0], r[1], r[2], r[3], float(lots['metella']['z'])), g('SUB_Metella_root')))
    if g('COAST_HadrianMausoleum_root'):
        out['mausoleum'] = len(env_mausoleum(M, g('DIO_Block_B_root'), g('COAST_HadrianMausoleum_root')))
    if NERO_ENV and g('HERO_NeroBase_root'):                                # 00:05 사용자: 네로 삭제 → 판석 마당·주랑 0
        bx = plan_bbox(g('HERO_NeroBase_root'))
        out['nero'] = len(env_nero(M, g('DIO_Block_C_root'), (0.5 * (bx[0] + bx[1]), 0.5 * (bx[2] + bx[3]))))
    keep = ['HERO_Colosseum_root', 'CITY_Acropolis_root', 'CITY_TrajanMarket_root', 'CITY_Maxentius_root', 'CITY_Marcellus_root', 'BATHS_Aqueduct_root', 'SUB_Metella_root',
            'COAST_PortusHex_root', 'COAST_PortusClaudius_root', 'COAST_HadrianMausoleum_root', 'COAST_PonsAelius_root', 'HERO_NeroBase_root', 'HERO_NeroYard_root']
    out['groundcover'] = env_groundcover(M, spec_dio, keep)
    return out


def portus_notch(spec_dio):
    """00:25 사용자 '포르투스 육각형 내부 공간은 땅이 아니라 바다와 연결된 물': 블록 B 해안선(평면 Y = COAST)에서 외항 운하를 지나
    육각 내항까지 블록 윤곽에 홈을 낸다(디오라마 바다 수면이 그대로 들어온다). 반환: 홈 변 목록(평면) — 그 변은 장식 없는 단면만"""
    import roma_pkg_coast as CO
    if not CO.HEX_SEA or not CO.PORTUS_FIT or not CO.GEO:
        return []
    s_ = CO.PORTUS_FIT['s']; px, py = CO.PORTUS_FIT['pivot']
    wp = lambda X, Y: (px + s_ * (X - px), py + s_ * (Y - py))
    r = CO.HEX_W
    v = [CO.hexv(r, k) for k in range(6)]
    t30 = math.tan(math.radians(30.0))
    xw0, xw1 = CO.CANAL_X[0] - 0.35, CO.CANAL_X[1] + 0.35
    yS = lambda X: v[1][1] - abs(X - v[1][0]) * t30
    coast = wp(0.0, CO.COAST_Y)[1]
    B = next(b for b in spec_dio['blocks'] if b['id'] == 'B')
    P = [tuple(p) for p in B['poly']]
    i = next(k for k in range(len(P)) if abs(P[k][1] - coast) < 1e-6 and abs(P[(k + 1) % len(P)][1] - coast) < 1e-6
             and min(P[k][0], P[(k + 1) % len(P)][0]) < wp(xw0, 0)[0] and max(P[k][0], P[(k + 1) % len(P)][0]) > wp(xw1, 0)[0])
    a_, b_ = P[i], P[(i + 1) % len(P)]
    seq = [(xw1, CO.COAST_Y), (xw1, yS(xw1)), v[0], v[5], v[4], v[3], v[2], (xw0, yS(xw0)), (xw0, CO.COAST_Y)]
    notch = [wp(X, Y) for X, Y in seq]
    notch = [(x, coast if k in (0, len(notch) - 1) else y) for k, (x, y) in enumerate(notch)]
    if a_[0] < b_[0]:
        notch = notch[::-1]
    B['poly'] = P[:i + 1] + notch + P[i + 1:]
    segs = [(notch[k], notch[k + 1]) for k in range(len(notch) - 1)]
    def plain(pt):
        for (x0, y0), (x1, y1) in segs:
            dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy
            t = max(0.0, min(1.0, ((pt[0] - x0) * dx + (pt[1] - y0) * dy) / L2)) if L2 > 0 else 0.0
            if math.hypot(x0 + t * dx - pt[0], y0 + t * dy - pt[1]) < 0.05:
                return True
        return False
    B['plain_edge'] = plain
    return segs


def portus_quay_detail(M, hex_root, seed=61.0):
    """23:51 사용자: 포르투스 표현 층 누적 — 육각 내항 부두 가장자리 계선주(L4)·내려가는 계단(L2)·물결(L3)·물때 띠(L6)·갓돌 밝은 선(L5)·계선 고리(L1)"""
    cut = bpy.data.objects.get('X_CUT_CoastHex')
    if cut is None:
        return []
    mw = cut.matrix_world
    top = next(f for f in cut.data.polygons if (mw.to_3x3() @ f.normal).z > 0.9)
    ring = [((mw @ cut.data.vertices[k].co).x, -(mw @ cut.data.vertices[k].co).y) for k in top.vertices]
    zs = sorted(set(round((mw @ v.co).z, 3) for v in cut.data.vertices))
    zq = 0.32                                                                  # 부두 윗면(배율 뒤)
    import roma_diorama as DI, roma_pkg_coast as CO
    zw = DI.WATER_Z if CO.HEX_SEA else -2.72                                   # 00:25 사용자: 내항 = 바다와 이어진 물(디오라마 바다 수면)
    cx = sum(p[0] for p in ring) / len(ring); cy = sum(p[1] for p in ring) / len(ring)
    A = [Acc() for _ in range(7)]
    n = len(ring)
    for i in range(n):
        (ax, ay), (bx_, by) = ring[i], ring[(i + 1) % n]
        L = math.hypot(bx_ - ax, by - ay); ux, uy = (bx_ - ax) / L, (by - ay) / L
        ox, oy = ax - cx, ay - cy
        nx, ny = -uy, ux
        if nx * ox + ny * oy < 0:
            nx, ny = -nx, -ny                                                  # 바깥(부두 쪽) 법선
        s_ = 1.5; k = 0
        while s_ < L - 1.0:
            X, Y = ax + ux * s_ + nx * 0.7, ay + uy * s_ + ny * 0.7
            A[4].cyl(X, Y, 0.22, zq, zq + 0.55, M['env_stone'], 8, True)
            A[4].cyl(X, Y, 0.28, zq + 0.45, zq + 0.6, M['env_stone2'], 8, True)
            A[1].face([V(ax + ux * s_ - 0.2, ay + uy * s_ + 0.0, zq - 0.5), V(ax + ux * s_ + 0.2, ay + uy * s_, zq - 0.5), V(ax + ux * s_ + 0.2, ay + uy * s_, zq - 0.2), V(ax + ux * s_ - 0.2, ay + uy * s_, zq - 0.2)],
                      M['env_deep'], (-nx, ny, 0))
            s_ += 2.6; k += 1
        m = L * 0.5                                                             # 물로 내려가는 계단: 변 가운데 오른쪽에서 안벽을 따라 바다 수면까지(돌 덩어리 단)
        d0, d1 = 0.36, 1.45                                                     # 안벽 안쪽 면(고리 안 0.33) 앞
        q = 0
        while True:
            zt_ = zq - 0.55 * (q + 1)
            u0_, u1_ = m + 1.6 + 0.45 * q, m + 1.6 + 0.45 * (q + 1)
            if zt_ < zw + 0.05 or u1_ > L - 1.0:
                break
            P = [(ax + ux * u_ - nx * d_, ay + uy * u_ - ny * d_) for u_, d_ in ((u0_, d0), (u1_, d0), (u1_, d1), (u0_, d1))]
            A[2].face([V(x, y, zt_) for x, y in P], M['env_stone'], (0, 0, 1))
            for i_ in range(4):
                (xa_, ya_), (xb_, yb_) = P[i_], P[(i_ + 1) % 4]
                A[2].face([V(xa_, ya_, zw - 0.2), V(xb_, yb_, zw - 0.2), V(xb_, yb_, zt_), V(xa_, ya_, zt_)], M['env_stone2'], (yb_ - ya_, xb_ - xa_, 0))
            q += 1
        A[6].face([V(ax - nx * 0.36, ay - ny * 0.36, zw + 0.02), V(bx_ - nx * 0.36, by - ny * 0.36, zw + 0.02), V(bx_ - nx * 0.36, by - ny * 0.36, zw + 0.45), V(ax - nx * 0.36, ay - ny * 0.36, zw + 0.4)],
                  M['q_wet'] if 'q_wet' in M else M['env_grass2'], (-nx, ny, 0))
        A[5].face([V(ax, ay, zq + 0.02), V(bx_, by, zq + 0.02), V(bx_ + nx * 0.25, by + ny * 0.25, zq + 0.02), V(ax + nx * 0.25, ay + ny * 0.25, zq + 0.02)], M['ash_cope'], (0, 0, 1))
    for k in range(24):                                                         # 내항 물결
        a = 2 * math.pi * hsh(k, seed, 1.1); r = 3.0 + 9.0 * hsh(k, seed, 1.2)
        X, Y = cx + r * math.cos(a), cy + r * math.sin(a); w = 0.6 + 1.0 * hsh(k, 1.3)
        A[3].face([V(X - w, Y + w, zw + 0.03), V(X - w + 0.12, Y + w + 0.12, zw + 0.03), V(X + w + 0.12, Y - w + 0.12, zw + 0.03), V(X + w, Y - w, zw + 0.03)], M['r_wave'], (0, 0, 1))
    GC = hex_root.users_collection[0]
    obs = []
    for k, ac in enumerate(A):
        ob = ac.obj('COAST_PortusHex_L%d_QuayDetail' % k, GC, None)
        if ob is not None:
            mw_ = ob.matrix_world.copy(); ob.parent = hex_root; ob.matrix_world = mw_
            obs.append(ob)
    return obs
