# roma_diorama — 20:40 사용자(203X 15편 비교) 지도 구조: 디오라마 땅 블록 · 축 정렬 판석 도로망(다리) · 블록 사이 물길. 담당: Blender-보완
# 땅 = 분리된 블록 3~4개(spec: 외곽 평면 다각형 + 윗면 높이). 블록은 수면 위로 들린 판이고, 보이는 잘린 옆면에 지층 단면(L0 재질)과
# 지층 경계선(L2)·자갈(L3)·박힌 돌과 물가 바위(L4)·윗선(L5)·매달린 풀과 뿌리·물자국(L6)·물가 해식굴과 윗선 밑 그늘(L1)을 쌓는다.
# 강·운하·바다 = 블록 사이의 물(한 수면). 블록 경계 = 강둑. 도로 = 평면 X·Y축 구간만(꺾임은 직각), 물 위 구간은 아치 다리.
# 조명·AO·그림자 없음(방출 재질). 평면 좌표(Y 아래) → Blender (X, −Y, Z)는 roma_pkg_ground.V.
import bpy, bmesh, math, json
from mathutils import Vector
import roma_kit as R, roma_flat as FL, roma_geo as G
import roma_pkg_ground as GR

COLL = 'MAP_Diorama'
WATER_Z = -7.0                 # 물길·바다 수면(블록 윗면 0 기준 들린 높이 7)
SIDE_PAD = 0.4                 # 옆면은 수면 아래 0.4까지(물가 이음 틈 0)
ROAD_T = 0.25                  # 판석 두께
ROAD_KERB = (0.3, 0.12)        # 갓돌 폭·높이
V = GR.V
hsh = R.hash01
Acc = GR.Acc


def mats():
    M = GR.mats()
    F = FL.flat
    sl = FL.PAL['slab']
    M['slab'] = F('F_dio_slab', sl)
    M['slab_side'] = F('F_dio_slabSide', FL.shade(sl, 0.8))
    M['slab_joint'] = F('F_dio_slabJoint', FL.shade(sl, 0.86))
    M['slab_wear'] = F('F_dio_slabWear', FL.shade(sl, 0.92))
    M['slab_hi'] = F('F_dio_slabHi', FL.mix_hex(sl, '#FFFFFF', 0.35))
    M['road_shade'] = F('F_dio_roadShade', '#B79E78')
    M['bridge'] = FL.blocks('F_dio_bridge', '#CFB98F', '#C4AD83', '#D9C59E', '#A48D68', 1.4, 0.7, 0.06)
    M['bridge_dk'] = F('F_dio_bridgeDeep', '#6F5A44')
    M['vous'] = F('F_dio_vous', '#E2D2B0')
    M['under_lip'] = F('F_dio_underLip', '#8A6545')
    M['moss_w'] = F('F_dio_mossWater', '#6E8A5A')
    # 22:22 성벽 마름돌(아크로폴리스 user_acropolis_hill): 따뜻한 회갈 석회암 3톤 + 짙은 줄눈·판 경계 + 2단 얼룩
    for k, hx in (('ash_a', '#B9A68A'), ('ash_b', '#AD9A7E'), ('ash_lt', '#C9B99D'), ('ash_dk', '#968470'), ('ash_joint', '#6E604F'),     # 00:23 사용자: 받침대(성벽·둑 성벽·바위 언덕)는 이전 색 그대로
                  ('ash_seam', '#5A4D40'), ('ash_stain', '#857562'), ('ash_wash', '#C4AC84'), ('ash_cope', '#DCCFB6'), ('ash_chip', '#D0C0A4'),
                  ('lime', '#B8AC94'), ('lime_top', '#C9BEA6'), ('lime_dk', '#968A76'), ('marble_blk', '#E6D6B6'), ('marble_blk_s', '#CDB995'),
                  ('ak_top', '#CFC1A2'),
                  # 22:23 블록 종류별 땅(레퍼런스-지형표.md)
                  ('pv_soil', '#9C7656'), ('pv_soil_dk', '#7E5E44'), ('pv_bed', '#8C8274'), ('pv_a', '#B8AE9C'), ('pv_b', '#A79C89'), ('pv_c', '#C7BDAA'),
                  ('pv_drain', '#6B5E4E'), ('pv_rim', '#D8CCB2'), ('pv_top', '#CFC2A8'),
                  ('q_joint', '#857A68'), ('q_a', '#CFC4AC'), ('q_b', '#C2B79E'), ('q_c', '#DAD0BA'), ('q_ring', '#4F473D'), ('q_cope', '#E4DBC6'),
                  ('q_wet', '#6F7458'), ('q_land', '#CBC596'), ('q_slab', '#D6CDB6'),
                  ('bw_bond', '#D2B28E'), ('bw_door', '#4E3A2C'), ('bw_frame', '#E0CFAE'), ('bw_terrace', '#C9AE8A'), ('bw_joint', '#7E4A33'),
                  ('rk_dark', '#7D7262'), ('rk_a', '#CFC6B4'), ('rk_b', '#BDB39F'), ('rk_c', '#DED6C6'),
                  ('gb_grass', '#A6B565'), ('gb_grass2', '#93A456'), ('gb_grass3', '#B9C478'), ('gb_reed', '#B6A86A'), ('gb_reed2', '#8E8F4E'),
                  ('gb_wet', '#7F8C5A'), ('lawn', '#ADBB6C'),
                  ('md_earth', '#A7835F'), ('md_earth2', '#8F6F50'), ('md_rubble', '#BFAE92'), ('md_rubble2', '#A39376'), ('md_basalt', '#6F6B66'),
                  ('md_basalt2', '#85807A'), ('md_wall', '#B9A385'), ('md_ground', '#CDB78E'),
                  ('rw_a', '#DCCDAA'), ('rw_b', '#D0C09C'), ('rw_c', '#E6D9BC'), ('rw_joint', '#9C8C70'), ('rw_flood', '#8E8770'), ('rw_flood2', '#B9A57E'),
                  ('fr_conc', '#A69885'), ('fr_conc2', '#8E8170'), ('fr_dot', '#C9BEAC'), ('fr_slab', '#E8E2D6'), ('fr_slab2', '#D9D2C3'), ('fr_slab3', '#F1ECE2'),
                  ('fr_earth', '#BFA37E'),
                  ('pl_trav', '#E2D5B8'), ('pl_trav2', '#D5C7A8'), ('pl_step', '#DCCFB2'), ('pl_line', '#BBAA88'), ('pl_face', '#CDBE9E')):
        M[k] = F('F_dio_' + k, hx)
    M['bw_brick'] = FL.blocks('F_dio_bwBrick', '#B26B4A', '#A86245', '#BC7656', '#8E5038', 0.36, 0.13, 0.12)
    import roma_env as EN_                                              # 23:43: 블록 지형 재질(마른 풀·밭 풀·트래버틴 등)도 블록이 쓴다
    for k, hx in EN_.EXTRA.items():
        M[k] = F('F_env_' + k, hx)
    return M


def _ccw(poly):
    return sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly))) > 0


def vis_edges(poly):
    """보이는 옆면 변(평면 바깥 법선 nx + ny > 0): [(a, 접선 t, 법선 n, 길이 L)]"""
    sg = 1.0 if _ccw(poly) else -1.0
    out = []
    for k in range(len(poly)):
        a, b = poly[k], poly[(k + 1) % len(poly)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L < 1e-6:
            continue
        nx, ny = sg * dy / L, -sg * dx / L
        if nx + ny > 1e-6:
            out.append((a, (dx / L, dy / L), (nx, ny), L))
    return out


def _on(a, t, n, s, z, eps=0.0):
    """옆면 위 점(평면 a + t·s + n·eps, 높이 z) → Blender"""
    return V(a[0] + t[0] * s + n[0] * eps, a[1] + t[1] * s + n[1] * eps, z)


# ───────────────────────── 옆면·윗면 종류(22:22 사용자: 블록 땅은 그 위 건물의 레퍼런스대로) ─────────────────────────
def _quad(acc, a, t, n, s0, s1, z0, z1, eps, mat):
    acc.face([_on(a, t, n, s0, z0, eps), _on(a, t, n, s1, z0, eps), _on(a, t, n, s1, z1, eps), _on(a, t, n, s0, z1, eps)], mat, (n[0], -n[1], 0))


def side_ashlar(A, M, a, t, n, L, z0, z1, sd, U=0.9):
    """성벽 마름돌(user_acropolis_hill): 수직 벽을 마디 판(6~13U, 판마다 내밂이 다름)으로 나누고, 판마다 수평 켜(높이 0.7~1.25U)에
    큰 직사각 돌(1.3~3U)을 쌓는다. 바탕 = 짙은 줄눈(L0), 판 경계 세로 그늘(L1), 돌(L2, 위로 갈수록 짙은 돌이 많다), 끼움돌(L3),
    발치 바위(L4), 갓돌 선(L5), 2단 얼룩(위에서 흘러내린 물때 · 황토 씻김)과 발치 이끼(L6)"""
    a0, a1, a2, a3, a4, a5, a6 = A
    H = z1 - z0
    cuts = [0.0]; k = 0
    while L - cuts[-1] > 9.0 * U:
        cuts.append(cuts[-1] + U * (6.0 + 7.0 * hsh(k, sd, 21.1))); k += 1
    cuts.append(L)
    g = 0.075 * U
    for p in range(len(cuts) - 1):
        s0, s1 = cuts[p], cuts[p + 1]
        ep = 0.02 + 0.2 * U * hsh(p, sd, 21.2)
        if p > 0:
            _quad(a1, a, t, n, s0 - 0.09 * U, s0 + 0.09 * U, z0, z1 - 0.05 * U, 0.01, M['ash_seam'])
        z = z0; c = 0
        while z < z1 - 0.25 * U:
            hc = U * (0.7 + 0.55 * hsh(c, p, sd, 21.4))
            ze = z1 if z1 - (z + hc) < 0.45 * U else z + hc
            fz = (z - z0) / max(H, 1e-6)
            s = s0; j = 0
            l0 = U * (0.4 + 1.2 * hsh(c, p, sd, 21.5))
            while s < s1 - 0.1 * U:
                l = l0 if j == 0 else U * (1.3 + 1.7 * hsh(j, c, p, sd + 21.6))
                se = s1 if s1 - (s + l) < 0.5 * U else s + l
                tn = hsh(j, c, p, sd + 21.7)
                mt = M['ash_dk'] if tn < 0.12 + 0.3 * fz else (M['ash_lt'] if tn > 0.86 - 0.1 * fz else (M['ash_a'] if tn > 0.5 else M['ash_b']))
                _quad(a2, a, t, n, s + g / 2, se - g / 2, z + g / 2, ze - g / 2, ep, mt)
                if hsh(j, c, p, sd + 21.8) < 0.08:
                    w = 0.25 * U + 0.2 * U * hsh(j, c, sd + 21.9)
                    sm = s + (se - s) * hsh(j, c, sd + 22.0)
                    _quad(a3, a, t, n, sm - w / 2, sm + w / 2, z + g, z + g + w * 0.8, ep + 0.01, M['ash_chip'])
                s = se; j += 1
            z = ze; c += 1
        _quad(a5, a, t, n, s0, s1, z1 - 0.12 * U, z1, ep + 0.012, M['ash_cope'])
    W = (n[0], -n[1], 0)
    for j in range(int(L / (2.6 * U))):                                           # 넓은 씻김 자국(6각, 위에서 아래로 좁아짐)
        s = (L - 2.0 * U) * hsh(j, sd, 23.1); w = U * (0.7 + 1.5 * hsh(j, sd, 23.2))
        Ls = H * (0.1 + 0.35 * hsh(j, sd, 23.3) ** 1.3); z_ = z1 - 0.15 * U - H * 0.25 * hsh(j, sd, 23.0) ** 2
        mt = M['ash_stain'] if hsh(j, sd, 23.4) < 0.55 else M['ash_wash']
        a6.face([_on(a, t, n, s + w * u_, z_ - Ls * f_, 0.26 * U) for u_, f_ in ((0.0, 0.0), (1.0, 0.0), (0.9, 0.45), (0.65, 1.0), (0.3, 0.8), (0.05, 0.5))], mt, W)
    for j in range(int(L / (1.6 * U))):
        s = (L - U) * hsh(j, sd, 23.5); w = U * (0.6 + 1.4 * hsh(j, sd, 23.6)); hh = U * (0.3 + 1.0 * hsh(j, sd, 23.7))
        a6.face([_on(a, t, n, s, z0, 0.27 * U), _on(a, t, n, s + w, z0, 0.27 * U), _on(a, t, n, s + w * 0.7, z0 + hh, 0.27 * U),
                 _on(a, t, n, s + w * 0.25, z0 + hh * 0.8, 0.27 * U)], (M['moss_w'], M['tuft2'], M['ash_stain'])[j % 3], W)
    for j in range(int(L / (3.0 * U))):
        s = (L - U) * hsh(j, sd, 23.8); r = U * (0.5 + 0.9 * hsh(j, sd, 23.9))
        X, Y = a[0] + t[0] * s + n[0] * r * 0.5, a[1] + t[1] * s + n[1] * r * 0.5
        a4.blob(X, Y, z0 + r * 0.25, r * 1.2, r * 0.9, r * 0.7, M['lime'], 1, 0.22, sd + 3.0 * j, M['lime_top'], M['lime_dk'])


def top_ashlar(A, M, poly, z1, sd, U=0.9, keep_out=None):
    """성벽 윗면 가장자리: 밝은 갓 띠(L5) · 드러난 석회암 노두(L4) · 흩어진 대리석 덩이(L4). keep_out(X, Y)면 건너뜀"""
    a4, a5 = A[4], A[5]
    for e, (a, t, n, L) in enumerate(vis_edges(poly)):
        a5.face([_on(a, t, n, 0.0, z1 + 0.02, -0.5 * U), _on(a, t, n, L, z1 + 0.02, -0.5 * U), _on(a, t, n, L, z1 + 0.02, 0.0), _on(a, t, n, 0.0, z1 + 0.02, 0.0)],
                M['ash_cope'], (0, 0, 1))
        for j in range(int(L / (2.6 * U))):
            s = 0.5 * U + (L - U) * hsh(j, e, sd, 24.1); d = U * (0.4 + 1.8 * hsh(j, e, sd, 24.2))
            X, Y = a[0] + t[0] * s - n[0] * d, a[1] + t[1] * s - n[1] * d
            if keep_out is not None and keep_out(X, Y):
                continue
            if hsh(j, e, sd, 24.3) < 0.6:
                r = U * (1.0 + 1.2 * hsh(j, e, sd, 24.4))                             # 납작하고 넓은 노두(바닥 바위가 드러남)
                a4.blob(X, Y, z1, r * 1.4, r, U * (0.22 + 0.4 * hsh(j, e, sd, 24.5)), M['lime'], 1, 0.3, sd + 7.0 * j + e, M['lime_top'], M['lime_dk'])
            else:
                w = U * (0.8 + 1.2 * hsh(j, e, sd, 24.6)); dd = U * (0.5 + 0.5 * hsh(j, e, sd, 24.7)); hh = U * (0.4 + 0.5 * hsh(j, e, sd, 24.8))
                a4.box(X - w / 2, X + w / 2, Y - dd / 2, Y + dd / 2, z1, z1 + hh, M['marble_blk'], M['marble_blk_s'])


def _pf(acc, a, t, n, pts, eps, mat):
    """옆면 위 (s, z) 다각형 한 장"""
    return acc.face([_on(a, t, n, s, z, eps) for s, z in pts], mat, (n[0], -n[1], 0))


def _lay(acc, a, t, n, s0, s1, z0, z1, ep, U, sd, tone, hr=(0.7, 0.55), lr=(1.3, 1.7), g=0.075):
    """수평 켜 돌 쌓기(공용): 켜 높이 U·(hr0 + hr1·난수), 돌 길이 U·(lr0 + lr1·난수), 줄눈 g·U. tone(난수, 높이 비율) → 재질"""
    H = max(z1 - z0, 1e-6)
    z = z0; c = 0
    while z < z1 - 0.25 * U:
        hc = U * (hr[0] + hr[1] * hsh(c, sd, 31.4))
        ze = z1 if z1 - (z + hc) < 0.45 * U else z + hc
        s = s0; j = 0
        l0 = U * (0.4 + 1.2 * hsh(c, sd, 31.5))
        while s < s1 - 0.1 * U:
            l = l0 if j == 0 else U * (lr[0] + lr[1] * hsh(j, c, sd + 31.6))
            se = s1 if s1 - (s + l) < 0.5 * U else s + l
            _quad(acc, a, t, n, s + g * U / 2, se - g * U / 2, z + g * U / 2, ze - g * U / 2, ep, tone(hsh(j, c, sd + 31.7), (z - z0) / H))
            s = se; j += 1
        z = ze; c += 1


def _box_e(acc, a, t, n, s0, s1, d0, d1, zb, zt, mt, ms, ends=True):
    """옆면 틀(변 방향 s, 바깥 d) 상자: 윗면 · 앞면 · 양 끝면(보이는 쪽은 법선으로 톤이 정해진다)"""
    acc.face([_on(a, t, n, s0, zt, d0), _on(a, t, n, s1, zt, d0), _on(a, t, n, s1, zt, d1), _on(a, t, n, s0, zt, d1)], mt, (0, 0, 1))
    _quad(acc, a, t, n, s0, s1, zb, zt, d1, ms)
    if ends:
        for s_, sg in ((s0, -1.0), (s1, 1.0)):
            acc.face([_on(a, t, n, s_, zb, d0), _on(a, t, n, s_, zb, d1), _on(a, t, n, s_, zt, d1), _on(a, t, n, s_, zt, d0)], ms, (sg * t[0], -sg * t[1], 0))


def _hang(A6, M, a, t, n, L, zt, sd, eps=0.03, mats=('tuft', 'tuft2', 'tuft3'), dens=0.72):
    """윗선에서 늘어진 풀(L6)"""
    s = 0.3; i = 0
    while s < L - 0.6:
        w = 0.5 + 0.7 * hsh(i, sd, 1.3)
        if hsh(i, sd, 2.7) < dens:
            hang = 0.35 + 0.9 * hsh(i, sd, 3.9); mt = M[mats[i % len(mats)]]
            _pf(A6, a, t, n, [(s, zt - hang * 0.5), (s + w, zt - hang * 0.3), (s + w * 0.55, zt - hang)], eps, mt)
        s += w + 0.15 + 0.9 * hsh(i, sd, 5.2); i += 1


def _cells(poly, step, fn, sd, jit=0.35):
    """윗면 격자 칸 중심(다각형 안)마다 fn(X, Y, i, j)"""
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    i = 0
    X = min(xs) + step / 2
    while X < max(xs):
        j = 0; Y = min(ys) + step / 2
        while Y < max(ys):
            Xj = X + step * jit * (hsh(i, j, sd, 51.1) - 0.5); Yj = Y + step * jit * (hsh(i, j, sd, 51.2) - 0.5)
            if GR.pip(Xj, Yj, poly):
                fn(Xj, Yj, i, j)
            Y += step; j += 1
        X += step; i += 1


def _stone(acc, X, Y, z, r, mat, k=6, sd=0.0, sq=1.0):
    acc.face([V(X + r * (0.8 + 0.35 * hsh(q, sd, 52.1)) * math.cos(2 * math.pi * q / k + sd), Y + sq * r * (0.8 + 0.35 * hsh(q, sd, 52.2)) * math.sin(2 * math.pi * q / k + sd), z)
              for q in range(k)], mat, (0, 0, 1))


def _rim(A, M, poly, z1, U, mat_lip='lip'):
    for e, (a, t, n, L) in enumerate(vis_edges(poly)):
        A[5].face([_on(a, t, n, 0.0, z1 + 0.02, -0.45 * U), _on(a, t, n, L, z1 + 0.02, -0.45 * U), _on(a, t, n, L, z1 + 0.02, 0.0), _on(a, t, n, 0.0, z1 + 0.02, 0.0)],
                  M[mat_lip], (0, 0, 1))


# ── 콜로세움(아레나-참조-localbanana): 얇은 디오라마 판 = 위 자갈 포장 켜 + 아래 갈색 흙(아래로 짙게) · 윗면 자갈 포장 · 옛 배수로 돌 테
def side_paved(A, M, a, t, n, L, z0, z1, sd, U=0.9):
    a0, a1, a2, a3, a4, a5, a6 = A
    H = z1 - z0; zc = z1 - 0.6 * U
    _quad(a2, a, t, n, 0.0, L, zc - 0.05 * U, z1, 0.01, M['pv_bed'])
    s = 0.0; j = 0
    while s < L - 0.2 * U:
        w = U * (0.45 + 0.35 * hsh(j, sd, 41.1)); se = min(L, s + w)
        _pf(a2, a, t, n, [(s + 0.04 * U, zc), (se - 0.04 * U, zc), (se - 0.02 * U, zc + 0.32 * U), (0.5 * (s + se), z1 - 0.03 * U), (s + 0.02 * U, zc + 0.32 * U)],
            0.02, (M['pv_a'], M['pv_b'], M['pv_c'])[j % 3])
        s = se; j += 1
    _quad(a1, a, t, n, 0.0, L, zc - 0.28 * U, zc - 0.05 * U, 0.012, M['under_lip'])
    _quad(a2, a, t, n, 0.0, L, z0, z0 + 0.38 * H, 0.008, M['pv_soil_dk'])
    for j in range(int(L * 0.5)):
        s = 0.4 + (L - 0.8) * hsh(j, sd, 41.2); z = z0 + 0.3 + (zc - z0 - 0.8) * hsh(j, sd, 41.3); r = 0.12 + 0.22 * hsh(j, sd, 41.4)
        _pf(a3, a, t, n, [(s + r * math.cos(2 * math.pi * k / 6), z + r * 0.7 * math.sin(2 * math.pi * k / 6)) for k in range(6)], 0.02, M['pv_c'] if j % 3 else M['rock_top'])
    for j in range(int(L / 6.0)):
        s = 1.0 + (L - 2.0) * hsh(j, sd, 41.5); z = z0 + 1.0 + (zc - z0 - 2.0) * hsh(j, sd, 41.6); r = 0.3 + 0.35 * hsh(j, sd, 41.7)
        X, Y = a[0] + t[0] * s + n[0] * 0.1, a[1] + t[1] * s + n[1] * 0.1
        a4.blob(X, Y, z, r * 1.1, r * 0.8, r * 0.7, M['rock'], 1, 0.2, sd + j, M['rock_top'], None)
    _hang(a6, M, a, t, n, L, z1, sd, dens=0.45)


def top_paved(A, M, poly, z1, sd, U=0.9, keep_out=None):
    """자갈 포장(회베이지 3톤 다각 돌) · 가장자리 안쪽 옛 배수로(짙은 도랑 + 밝은 돌 테)"""
    mats_ = (M['pv_a'], M['pv_b'], M['pv_c'])
    _cells(poly, 0.8 * U, lambda X, Y, i, j: (keep_out is None or not keep_out(X, Y)) and _stone(A[3], X, Y, z1 + 0.02, 0.34 * U, mats_[(i * 7 + j * 3) % 3], 6, hsh(i, j, sd)), sd)
    for e, (a, t, n, L) in enumerate(vis_edges(poly)):
        A[1].face([_on(a, t, n, 0.0, z1 + 0.03, -1.15 * U), _on(a, t, n, L, z1 + 0.03, -1.15 * U), _on(a, t, n, L, z1 + 0.03, -0.85 * U), _on(a, t, n, 0.0, z1 + 0.03, -0.85 * U)],
                  M['pv_drain'], (0, 0, 1))
        s = 0.0; k = 0
        while s < L - 0.3 * U:
            se = min(L, s + U * (0.9 + 0.5 * hsh(k, e, sd, 42.1)))
            for d0, d1 in ((-1.4 * U, -1.15 * U), (-0.85 * U, -0.6 * U)):
                A[4].box(*_xyrect(a, t, n, s + 0.04 * U, se - 0.04 * U, d0, d1), z1, z1 + 0.12 * U, M['pv_rim'], M['pv_b'])
            s = se; k += 1
    _rim(A, M, poly, z1, U)


def _xyrect(a, t, n, s0, s1, d0, d1):
    """변 틀 직사각(축 정렬 변 가정) → 평면 X0, X1, Y0, Y1"""
    pts = [(a[0] + t[0] * s + n[0] * d, a[1] + t[1] * s + n[1] * d) for s in (s0, s1) for d in (d0, d1)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return min(xs), max(xs), min(ys), max(ys)


# ── 포르투스(판화·복원도·평면도): 육각 내항 둘레 석축 부두 벽(규칙 켜 마름돌) · 계선주 · 물로 내려가는 계단 · 계선 고리 · 물때 띠 / 윗면 부두 판석 띠 + 평평한 해안 평야
def side_quay(A, M, a, t, n, L, z0, z1, sd, U=0.9):
    a0, a1, a2, a3, a4, a5, a6 = A
    tone = lambda h, f: M['q_c'] if h > 0.8 else (M['q_a'] if h > 0.4 else M['q_b'])
    _lay(a2, a, t, n, 0.0, L, z0, z1 - 0.3 * U, 0.03, U, sd, tone, hr=(0.8, 0.0), lr=(2.0, 1.2))
    _quad(a5, a, t, n, 0.0, L, z1 - 0.3 * U, z1, 0.09, M['q_cope'])
    _quad(a1, a, t, n, 0.0, L, z1 - 0.38 * U, z1 - 0.3 * U, 0.05, M['q_joint'])
    k = 0; s = 3.0 * U + 4.0 * U * hsh(sd, 43.1)
    while s < L - 3.0 * U:
        X = a[0] + t[0] * s + n[0] * 0.2; Y = a[1] + t[1] * s + n[1] * 0.2
        rr = 0.18 * U; zr = z1 - 1.3 * U
        _pf(a3, a, t, n, [(s + rr * math.cos(2 * math.pi * q / 8), zr + rr * math.sin(2 * math.pi * q / 8)) for q in range(8)], 0.06, M['q_ring'])
        if k % 3 == 1 and s < L - 6.0 * U:                                      # 물로 내려가는 계단(벽에 붙은 비탈 계단)
            ns = 9
            for q in range(ns):
                zt = z1 - (q + 1) * (z1 - z0 - 0.5) / ns
                _box_e(a4, a, t, n, s + q * 0.42 * U, s + (q + 1) * 0.42 * U + 0.6 * U, 0.0, 0.9 * U, z0, zt, M['q_slab'], M['q_b'], ends=(q == ns - 1))
        s += U * (5.0 + 3.0 * hsh(k, sd, 43.2)); k += 1
    _quad(a6, a, t, n, 0.0, L, z0, z0 + 0.4 * U + 0.55 * U, 0.08, M['q_wet'])
    for j in range(int(L / (1.8 * U))):
        s = (L - U) * hsh(j, sd, 43.3); w = U * (0.3 + 0.6 * hsh(j, sd, 43.4)); Ls = (z1 - z0) * (0.15 + 0.4 * hsh(j, sd, 43.5))
        _pf(a6, a, t, n, [(s, z1 - 0.35 * U - Ls), (s + w, z1 - 0.35 * U - Ls * 0.8), (s + w, z1 - 0.35 * U), (s, z1 - 0.35 * U)], 0.07, M['ash_stain'])


def top_quay(A, M, poly, z1, sd, U=0.9, keep_out=None):
    for e, (a, t, n, L) in enumerate(vis_edges(poly)):
        A[3].face([_on(a, t, n, 0.0, z1 + 0.02, -2.2 * U), _on(a, t, n, L, z1 + 0.02, -2.2 * U), _on(a, t, n, L, z1 + 0.02, 0.0), _on(a, t, n, 0.0, z1 + 0.02, 0.0)],
                  M['q_slab'], (0, 0, 1))
        s = 1.1 * U
        while s < L:
            A[3].face([_on(a, t, n, s - 0.03, z1 + 0.03, -2.2 * U), _on(a, t, n, s + 0.03, z1 + 0.03, -2.2 * U), _on(a, t, n, s + 0.03, z1 + 0.03, 0.0), _on(a, t, n, s - 0.03, z1 + 0.03, 0.0)],
                      M['q_joint'], (0, 0, 1))
            s += 1.1 * U
        s = 2.5 * U; k = 0
        while s < L - U:
            X = a[0] + t[0] * s - n[0] * 0.45 * U; Y = a[1] + t[1] * s - n[1] * 0.45 * U
            A[4].cyl(X, Y, 0.22 * U, z1, z1 + 0.6 * U, M['q_c'], 8)
            s += U * (4.0 + 2.0 * hsh(k, e, sd, 44.1)); k += 1
    _rim(A, M, poly, z1, U, 'q_cope')


# ── 트라야누스 시장(user_trajan_markets): 언덕 비탈을 깎은 계단식 옹벽(벽돌 마감) — 아래 단(앞으로 나온 테라스 벽, 가게 문 줄) + 위 벽(아치 창 줄)
def side_brick(A, M, a, t, n, L, z0, z1, sd, U=0.9):
    a0, a1, a2, a3, a4, a5, a6 = A
    H = z1 - z0; zm = z0 + 0.55 * H; TW = 1.6 * U
    _box_e(a0, a, t, n, 0.0, L, 0.0, TW, z0, zm, M['bw_terrace'], M['bw_brick'])          # 아래 테라스 벽(앞으로 나옴)
    _quad(a2, a, t, n, 0.0, L, zm, z1, 0.012, M['bw_brick'])                              # 위 벽 벽돌 마감
    for zz, d in [(z0 + q * 1.1 * U, TW + 0.012) for q in range(1, int((zm - z0) / (1.1 * U)) + 1)] + \
                 [(zm + q * 1.1 * U, 0.02) for q in range(1, int((z1 - zm) / (1.1 * U)) + 1)]:
        if zz < z1 - 0.2 * U:
            _quad(a3, a, t, n, 0.0, L, zz, zz + 0.09 * U, d, M['bw_bond'])                  # 기와 벽돌 띠(bipedales)
    s = 1.2 * U; k = 0
    while s < L - 2.2 * U:                                                                  # 가게 문(트래버틴 문틀) · 위 아치 창
        w = 1.0 * U; h = min(1.6 * U, zm - z0 - 0.8 * U)
        _quad(a2, a, t, n, s - 0.12 * U, s + w + 0.12 * U, z0 + 0.4 * U, z0 + 0.4 * U + h + 0.14 * U, TW + 0.02, M['bw_frame'])
        _quad(a1, a, t, n, s, s + w, z0 + 0.4 * U, z0 + 0.4 * U + h, TW + 0.035, M['bw_door'])
        zw = zm + 0.7 * U; hw = min(1.4 * U, z1 - zw - 0.7 * U)
        if hw > 0.5 * U:
            rr = 0.38 * U; c = s + w / 2
            _pf(a1, a, t, n, [(c - rr, zw), (c + rr, zw)] + [(c + rr * math.cos(math.pi * q / 8), zw + hw - rr + rr * math.sin(math.pi * q / 8)) for q in range(9)], 0.03, M['bw_door'])
            _quad(a2, a, t, n, c - rr - 0.12 * U, c + rr + 0.12 * U, zw - 0.14 * U, zw, 0.04, M['bw_frame'])
        s += 2.4 * U; k += 1
    _quad(a5, a, t, n, 0.0, L, z1 - 0.2 * U, z1, 0.05, M['bw_frame'])
    sx_ = 0.6 * U
    while sx_ < L - 0.4 * U:                                                               # L4 갓 아래 트래버틴 까치발
        _box_e(a4, a, t, n, sx_, sx_ + 0.22 * U, 0.0, 0.18 * U, z1 - 0.42 * U, z1 - 0.2 * U, M['bw_frame'], M['bw_frame'], ends=False)
        sx_ += 1.2 * U
    for j in range(int(L / (2.0 * U))):
        sx = (L - U) * hsh(j, sd, 45.1); w = U * (0.3 + 0.5 * hsh(j, sd, 45.2)); Ls = (z1 - zm) * (0.2 + 0.5 * hsh(j, sd, 45.3))
        _pf(a6, a, t, n, [(sx, z1 - 0.2 * U - Ls), (sx + w, z1 - 0.2 * U - Ls * 0.8), (sx + w, z1 - 0.2 * U), (sx, z1 - 0.2 * U)], 0.05, M['ash_stain'] if j % 2 else M['tuft2'])
    _hang(a6, M, a, t, n, L, z1, sd, 0.06, dens=0.35)


def top_brick(A, M, poly, z1, sd, U=0.9, keep_out=None):
    _rim(A, M, poly, z1, U, 'bw_frame')


# ── 수도교(user_aqueduct, 퐁 뒤 가르): 물가 석회암 판 바위 — 두꺼운 판이 층으로 튀어나오고 틈은 짙게, 물가 바위 · 판 위 풀 / 윗면 풀 + 노두
def side_rock(A, M, a, t, n, L, z0, z1, sd, U=0.9):
    a0, a1, a2, a3, a4, a5, a6 = A
    z = z0; c = 0
    while z < z1 - 0.3 * U:
        hc = U * (0.8 + 0.9 * hsh(c, sd, 46.1)); ze = min(z1, z + hc)
        s = -0.2 * U * hsh(c, sd, 46.2); j = 0
        while s < L - 0.3 * U:
            l = U * (2.0 + 3.5 * hsh(j, c, sd, 46.3)); se = min(L, s + l)
            ep = 0.05 + 0.55 * U * hsh(j, c, sd, 46.4)
            g = 0.08 * U; cr = 0.25 * U
            pts = [(s + g + cr, z + g), (se - g - cr, z + g), (se - g, z + g + cr), (se - g, ze - g - cr * 0.6), (se - g - cr, ze - g), (s + g + cr, ze - g), (s + g, ze - g - cr * 0.6), (s + g, z + g + cr)]
            _pf(a2, a, t, n, [(max(0.0, p[0]), p[1]) for p in pts], ep, (M['rk_a'], M['rk_b'], M['rk_c'])[(j + c) % 3])
            _pf(a5, a, t, n, [(max(0.0, s + g + cr), ze - g - 0.1 * U), (se - g - cr, ze - g - 0.1 * U), (se - g - cr, ze - g), (max(0.0, s + g + cr), ze - g)], ep + 0.01, M['rk_c'])
            if hsh(j, c, sd, 46.5) < 0.3 and ze < z1 - 0.1:
                X = a[0] + t[0] * (s + l * 0.5) + n[0] * ep * 0.6; Y = a[1] + t[1] * (s + l * 0.5) + n[1] * ep * 0.6
                A[6].blob(X, Y, ze, 0.3 * U, 0.25 * U, 0.25 * U, M['tuft2'], 0, 0.3, sd + j + c, M['tuft3'], None)
            s = se; j += 1
        z = ze; c += 1
    for j in range(int(L / (2.0 * U))):
        s = (L - U) * hsh(j, sd, 46.6); r = U * (0.5 + 0.9 * hsh(j, sd, 46.7))
        X, Y = a[0] + t[0] * s + n[0] * r * 0.8, a[1] + t[1] * s + n[1] * r * 0.8
        a4.blob(X, Y, z0 + 0.3 + r * 0.25, r * 1.2, r * 0.9, r * 0.6, M['rk_b'], 1, 0.25, sd + 5.0 * j, M['rk_c'], M['rk_dark'])
    _hang(a6, M, a, t, n, L, z1, sd, 0.6 * U)


def top_rock(A, M, poly, z1, sd, U=0.9, keep_out=None):
    A[3].face([V(X, Y, z1 + 0.01) for X, Y in _inset(poly, 0.3 * U)], M['lawn'], (0, 0, 1))
    _cells(poly, 3.0 * U, lambda X, Y, i, j: (hsh(i, j, sd, 47.1) < 0.25) and A[4].blob(X, Y, z1, U * 0.9, U * 0.7, U * 0.3, M['rk_a'], 1, 0.3, sd + i * 3 + j, M['rk_c'], M['rk_dark']), sd)
    _rim(A, M, poly, z1, U, 'gb_grass3')


def _inset(poly, d):
    """축 정렬 블록 윤곽을 d만큼 안으로(꼭짓점 이등분 방향, 볼록 가정)"""
    cx = sum(p[0] for p in poly) / len(poly); cy = sum(p[1] for p in poly) / len(poly)
    return [(p[0] + d * (1 if cx > p[0] else -1), p[1] + d * (1 if cy > p[1] else -1)) for p in poly]


# ── 하드리아누스 영묘·다리(user_hadrian_bridge): 물로 내려가는 풀 비탈(목초지) · 물가 갈대 · 젖은 띠 / 윗면 잔디
def side_grass(A, M, a, t, n, L, z0, z1, sd, U=0.9):
    a0, a1, a2, a3, a4, a5, a6 = A
    H = z1 - z0; out = 0.55 * H
    a0.face([_on(a, t, n, 0.0, z1, 0.0), _on(a, t, n, L, z1, 0.0), _on(a, t, n, L + out, z0, out), _on(a, t, n, -out, z0, out)], M['gb_grass'], (n[0], -n[1], 0.6))
    f = lambda s, z, e=0.03: _on(a, t, n, s, z, (z1 - z) / H * out + e)
    for j in range(int(L / (0.9 * U))):                                                       # 풀결(비탈 따라 밝은·짙은 줄)
        s = (L - 0.3) * hsh(j, sd, 48.1); w = 0.12 * U + 0.15 * U * hsh(j, sd, 48.2); zt = z1 - 0.2 - (H * 0.4) * hsh(j, sd, 48.3); zb_ = zt - H * (0.2 + 0.4 * hsh(j, sd, 48.4))
        A[3].face([f(s, zb_), f(s + w, zb_), f(s + w, zt), f(s, zt)], M['gb_grass3'] if j % 2 else M['gb_grass2'], (n[0], -n[1], 0.6))
    A[6].face([f(-out, z0 + 0.3, 0.05), f(L + out, z0 + 0.3, 0.05), f(L + out, z0 + 0.9 * U, 0.05), f(-out, z0 + 0.9 * U, 0.05)], M['gb_wet'], (n[0], -n[1], 0.6))
    s = 0.2; k = 0
    while s < L:                                                                                # 물가 갈대 무리
        if hsh(k, sd, 48.5) < 0.6:
            for q in range(5):
                x = s + 0.25 * U * q; hh = U * (0.9 + 0.9 * hsh(k, q, sd, 48.6))
                p0 = _on(a, t, n, x, z0 + 0.3, out + 0.3 * U); p1 = _on(a, t, n, x + 0.07 * U, z0 + 0.3, out + 0.3 * U)
                p2 = _on(a, t, n, x + 0.1 * U * (hsh(k, q, 48.7) - 0.5) * 3, z0 + 0.3 + hh, out + 0.3 * U)
                A[6].face([p0, p1, p2], M['gb_reed'] if q % 2 else M['gb_reed2'], (n[0], -n[1], 0))
        s += U * (1.4 + 1.6 * hsh(k, sd, 48.8)); k += 1
    for j in range(int(L / (5.0 * U))):
        s = (L - 1.0) * hsh(j, sd, 48.9); r = U * (0.35 + 0.4 * hsh(j, sd, 49.1))
        X, Y = a[0] + t[0] * s + n[0] * (out * 0.85), a[1] + t[1] * s + n[1] * (out * 0.85)
        a4.blob(X, Y, z0 + 0.6 + r * 0.3, r * 1.2, r * 0.9, r * 0.6, M['rk_b'], 1, 0.25, sd + 3.0 * j, M['rk_c'], None)


def top_grass(A, M, poly, z1, sd, U=0.9, keep_out=None):
    A[3].face([V(X, Y, z1 + 0.01) for X, Y in poly], M['lawn'], (0, 0, 1))
    _cells(poly, 2.6 * U, lambda X, Y, i, j: (hsh(i, j, sd, 49.2) < 0.4) and _stone(A[6], X, Y, z1 + 0.03, U * (0.5 + 0.6 * hsh(i, j, 49.3)), M['gb_grass3'] if (i + j) % 2 else M['gb_grass2'], 7, hsh(i, j, sd), 0.6), sd)
    _rim(A, M, poly, z1, U, 'gb_grass3')


# ── 메텔라(user_metella, 피라네시): 잔돌 섞인 흙 둔덕 — 흙 옆면에 박힌 잔돌·무너진 벽 조각, 늘어진 풀 / 윗면 거친 땅 · 아피아 가도 현무암 포장 조각 · 무너진 벽 그루터기
def side_mound(A, M, a, t, n, L, z0, z1, sd, U=0.9):
    a0, a1, a2, a3, a4, a5, a6 = A
    H = z1 - z0
    _quad(a2, a, t, n, 0.0, L, z0, z0 + 0.45 * H, 0.008, M['md_earth2'])
    for j in range(int(L * 1.1)):
        s = 0.3 + (L - 0.6) * hsh(j, sd, 53.1); z = z0 + 0.3 + (H - 0.8) * hsh(j, sd, 53.2); r = U * (0.15 + 0.3 * hsh(j, sd, 53.3))
        _pf(a3, a, t, n, [(s + r * math.cos(2 * math.pi * k / 5 + j), z + r * 0.75 * math.sin(2 * math.pi * k / 5 + j)) for k in range(5)], 0.02,
            M['md_rubble'] if j % 3 else M['md_rubble2'])
    for j in range(int(L / (3.5 * U))):
        s = 0.5 + (L - 1.0) * hsh(j, sd, 53.4); z = z0 + 0.8 + (H - 2.0) * hsh(j, sd, 53.5); r = U * (0.35 + 0.5 * hsh(j, sd, 53.6))
        X, Y = a[0] + t[0] * s + n[0] * 0.15, a[1] + t[1] * s + n[1] * 0.15
        a4.blob(X, Y, z, r * 1.2, r * 0.9, r * 0.7, M['md_rubble2'], 1, 0.3, sd + j, M['md_rubble'], None)
    for j in range(int(L / (7.0 * U))):                                                          # 흙에 묻힌 옛 벽 조각(망사 쌓기 무늬 = 마름모 줄)
        s = 1.0 + (L - 3.5 * U) * hsh(j, sd, 53.7); z = z0 + 0.6 + (H - 3.0) * hsh(j, sd, 53.8)
        _quad(a2, a, t, n, s, s + 2.4 * U, z, z + 1.4 * U, 0.04, M['md_wall'])
        for q in range(4):
            for r_ in range(2):
                cs = s + 0.3 * U + 0.55 * U * q + 0.27 * U * r_; cz = z + 0.35 * U + 0.6 * U * r_
                _pf(a3, a, t, n, [(cs, cz - 0.2 * U), (cs + 0.2 * U, cz), (cs, cz + 0.2 * U), (cs - 0.2 * U, cz)], 0.05, M['md_rubble2'])
    _quad(a1, a, t, n, 0.0, L, z1 - 0.4 * U, z1 - 0.05, 0.012, M['under_lip'])                # L1 윗선 밑 그늘
    _hang(a6, M, a, t, n, L, z1, sd, dens=0.8)


def top_mound(A, M, poly, z1, sd, U=0.9, keep_out=None):
    _cells(poly, 1.6 * U, lambda X, Y, i, j: (hsh(i, j, sd, 54.1) < 0.35) and _stone(A[3], X, Y, z1 + 0.02, U * (0.3 + 0.5 * hsh(i, j, 54.2)), M['md_ground'] if (i + j) % 2 else M['md_rubble'], 6, hsh(i, j, sd)), sd)
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    yc = min(ys) + (max(ys) - min(ys)) * 0.75                                                     # 아피아 가도 조각(평면 X 방향 띠, 현무암 다각 돌)
    X = min(xs) + 0.5 * U; k = 0
    while X < max(xs) - 0.5 * U:
        for q in range(4):
            Y = yc - 1.2 * U + 0.8 * U * q
            if GR.pip(X, Y, poly) and hsh(k, q, sd, 54.3) < 0.82:
                _stone(A[4], X, Y, z1 + 0.05, 0.36 * U, M['md_basalt'] if (k + q) % 2 else M['md_basalt2'], 6, hsh(k, q, sd))
        X += 0.75 * U; k += 1
    _rim(A, M, poly, z1, U, 'md_ground')


# ── 마르켈루스 극장(입지: 테베레 범람원, research 문서): 테베레 강둑 석축(큰 트래버틴 마름돌) · 2단 홍수 자국 · 계선 고리 · 강으로 내려가는 계단 / 윗면 트래버틴 판석 띠
def side_riverwall(A, M, a, t, n, L, z0, z1, sd, U=0.9):
    a0, a1, a2, a3, a4, a5, a6 = A
    H = z1 - z0
    tone = lambda h, f: M['rw_c'] if h > 0.78 else (M['rw_a'] if h > 0.38 else M['rw_b'])
    _lay(a2, a, t, n, 0.0, L, z0, z1 - 0.35 * U, 0.03, U * 1.15, sd, tone, hr=(0.95, 0.15), lr=(2.2, 1.4))
    _quad(a5, a, t, n, 0.0, L, z1 - 0.35 * U, z1, 0.1, M['pl_step'])
    _quad(a1, a, t, n, 0.0, L, z1 - 0.47 * U, z1 - 0.35 * U, 0.06, M['rw_joint'])           # L1 갓돌 밑 그늘
    for zf, mt in ((z0 + 0.32 * H, M['rw_flood']), (z0 + 0.58 * H, M['rw_flood2'])):            # 홍수 자국 2단(위 선이 물결처럼 들쭉날쭉)
        m = max(2, int(L / 0.9))
        up = [(L * q / m, zf + 0.25 * U * math.sin(q * 1.7 + sd)) for q in range(m + 1)]
        a6.face([_on(a, t, n, s, z, 0.07) for s, z in up] + [_on(a, t, n, s, z0 + 0.3, 0.07) for s, z in up[::-1]] if mt is M['rw_flood'] else
                [_on(a, t, n, s, z, 0.072) for s, z in up] + [_on(a, t, n, s, z - 0.35 * U, 0.072) for s, z in up[::-1]], mt, (n[0], -n[1], 0))
    s = 3.0 * U; k = 0
    while s < L - 3.0 * U:
        rr = 0.2 * U; zr = z1 - 1.4 * U
        _pf(a3, a, t, n, [(s + rr * math.cos(2 * math.pi * q / 8), zr + rr * math.sin(2 * math.pi * q / 8)) for q in range(8)], 0.08, M['q_ring'])
        if k % 4 == 2 and s < L - 7.0 * U:
            ns = 10
            for q in range(ns):
                zt = z1 - (q + 1) * (H - 0.5) / ns
                _box_e(a4, a, t, n, s + q * 0.45 * U, s + (q + 1) * 0.45 * U + 0.6 * U, 0.0, 1.0 * U, z0, zt, M['pl_step'], M['rw_b'], ends=(q == ns - 1))
        s += U * (5.5 + 2.5 * hsh(k, sd, 55.1)); k += 1


def top_riverwall(A, M, poly, z1, sd, U=0.9, keep_out=None):
    for e, (a, t, n, L) in enumerate(vis_edges(poly)):
        A[3].face([_on(a, t, n, 0.0, z1 + 0.02, -2.6 * U), _on(a, t, n, L, z1 + 0.02, -2.6 * U), _on(a, t, n, L, z1 + 0.02, 0.0), _on(a, t, n, 0.0, z1 + 0.02, 0.0)],
                  M['pl_trav'], (0, 0, 1))
        s = 1.3 * U
        while s < L:
            A[3].face([_on(a, t, n, s - 0.03, z1 + 0.03, -2.6 * U), _on(a, t, n, s + 0.03, z1 + 0.03, -2.6 * U), _on(a, t, n, s + 0.03, z1 + 0.03, 0.0), _on(a, t, n, s - 0.03, z1 + 0.03, 0.0)],
                      M['pl_line'], (0, 0, 1))
            s += 1.3 * U
    _rim(A, M, poly, z1, U, 'pl_step')


# ── 막센티우스(입지: 벨리아 쪽 포룸 가장자리): 포룸 바닥 판석 폐허 — 옆면 위 판석 두께 + 콘크리트 기초 켜(골재 점) + 아래 흙 지층 / 윗면 깨진 대리석 판석(빠지고 갈라짐) · 기둥 받침 그루터기
def side_forum(A, M, a, t, n, L, z0, z1, sd, U=0.9):
    a0, a1, a2, a3, a4, a5, a6 = A
    H = z1 - z0; zc = z1 - 0.3 * U; zf = zc - 1.5 * U
    s = 0.0; j = 0
    while s < L - 0.2 * U:
        se = min(L, s + U * (1.6 + 1.2 * hsh(j, sd, 56.1)))
        _quad(a2, a, t, n, s + 0.03 * U, se - 0.03 * U, zc, z1, 0.02, (M['fr_slab'], M['fr_slab2'], M['fr_slab3'])[j % 3])
        s = se; j += 1
    _quad(a2, a, t, n, 0.0, L, zf, zc, 0.012, M['fr_conc'])
    _quad(a1, a, t, n, 0.0, L, zf - 0.12 * U, zf, 0.014, M['fr_conc2'])
    for j in range(int(L * 1.6)):
        s = 0.2 + (L - 0.4) * hsh(j, sd, 56.2); z = zf + 0.15 * U + (zc - zf - 0.3 * U) * hsh(j, sd, 56.3); r = U * (0.05 + 0.08 * hsh(j, sd, 56.4))
        _pf(a3, a, t, n, [(s + r * math.cos(2 * math.pi * k / 5), z + r * math.sin(2 * math.pi * k / 5)) for k in range(5)], 0.025, M['fr_dot'] if j % 3 else M['fr_conc2'])
    zc2 = z0 + 0.45 * (zf - z0)
    m = max(2, int(L / 0.8))
    up = [(L * q / m, zc2 - GR._strata_w(a[0] + t[0] * L * q / m + a[1] + t[1] * L * q / m) + 0.09) for q in range(m + 1)]
    a2.face([_on(a, t, n, s_, z, 0.02) for s_, z in up] + [_on(a, t, n, s_, z - 0.2, 0.02) for s_, z in up[::-1]], M['root_dk'], (n[0], -n[1], 0))
    _hang(a6, M, a, t, n, L, z1, sd, dens=0.3)


def top_forum(A, M, poly, z1, sd, U=0.9, keep_out=None):
    A[3].face([V(X, Y, z1 + 0.005) for X, Y in poly], M['fr_earth'], (0, 0, 1))
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    sw, sh_ = 2.2 * U, 1.6 * U
    i = 0; X = min(xs)
    while X < max(xs) - 0.2:
        j = 0; Y = min(ys) + (0.5 * sh_ if i % 2 else 0.0)
        while Y < max(ys) - 0.2:
            h = hsh(i, j, sd, 57.1)
            cx, cy = X + sw / 2, Y + sh_ / 2
            if h < 0.78 and GR.pip(cx, cy, poly):
                g = 0.06 * U; mt = (M['fr_slab'], M['fr_slab2'], M['fr_slab3'])[(i + 2 * j) % 3]
                x0, x1, y0, y1 = X + g, min(max(xs), X + sw) - g, Y + g, min(max(ys), Y + sh_) - g
                if h < 0.2:                                                                      # 갈라진 판석: 두 조각
                    xm = x0 + (x1 - x0) * (0.35 + 0.3 * hsh(i, j, 57.2))
                    A[2].face([V(x0, y0, z1 + 0.04), V(xm, y0, z1 + 0.04), V(xm - 0.15 * U, y1, z1 + 0.04), V(x0, y1, z1 + 0.04)], mt, (0, 0, 1))
                    A[2].face([V(xm + 0.08 * U, y0, z1 + 0.04), V(x1, y0, z1 + 0.04), V(x1, y1, z1 + 0.04), V(xm - 0.07 * U, y1, z1 + 0.04)], mt, (0, 0, 1))
                else:
                    A[2].face([V(x0, y0, z1 + 0.04), V(x1, y0, z1 + 0.04), V(x1, y1, z1 + 0.04), V(x0, y1, z1 + 0.04)], mt, (0, 0, 1))
                if hsh(i, j, sd, 57.3) < 0.04:
                    A[4].box(cx - 0.45 * U, cx + 0.45 * U, cy - 0.45 * U, cy + 0.45 * U, z1, z1 + 0.35 * U, M['fr_slab3'], M['fr_slab2'])
                    A[4].cyl(cx, cy, 0.3 * U, z1 + 0.35 * U, z1 + 0.35 * U + U * (0.3 + 0.8 * hsh(i, j, 57.4)), M['fr_slab'], 10)
            Y += sh_; j += 1
        X += sw; i += 1
    _rim(A, M, poly, z1, U, 'fr_slab3')


# ── 네로 받침(user_nero_base): 판석 마당 — 가장자리 트래버틴 3단 계단 + 큰 마름돌 옆면 / 윗면 규칙 판석 격자
def side_plaza(A, M, a, t, n, L, z0, z1, sd, U=0.9):
    a0, a1, a2, a3, a4, a5, a6 = A
    sh, sd_ = 0.32 * U, 0.55 * U
    tone = lambda h, f: M['pl_trav'] if h > 0.6 else M['pl_face']
    _lay(a2, a, t, n, 0.0, L, z0, z1 - 3 * sh, 0.03 + 3 * sd_, U * 1.1, sd, tone, hr=(0.9, 0.1), lr=(2.0, 1.0))
    _box_e(a0, a, t, n, 0.0, L, 0.0, 3 * sd_, z0, z1 - 3 * sh, M['pl_step'], M['pl_face'], ends=False)
    for k in range(3):
        _box_e(a0, a, t, n, 0.0, L, 0.0, (k + 1) * sd_, z1 - (k + 1) * sh, z1 - k * sh, M['pl_step'], M['pl_trav2'])
        _quad(a5, a, t, n, 0.0, L, z1 - k * sh - 0.06 * U, z1 - k * sh, (k + 1) * sd_ + 0.01, M['ash_cope'])
    for j in range(int(L / (2.5 * U))):
        s = (L - U) * hsh(j, sd, 58.1); w = U * (0.4 + 0.8 * hsh(j, sd, 58.2)); Ls = (z1 - z0) * (0.1 + 0.3 * hsh(j, sd, 58.3))
        _pf(a6, a, t, n, [(s, z1 - 3 * sh - Ls), (s + w, z1 - 3 * sh - Ls * 0.8), (s + w, z1 - 3 * sh), (s, z1 - 3 * sh)], 3 * sd_ + 0.05, M['ash_stain'])
    s = 0.0
    while s < L:
        _quad(a3, a, t, n, s - 0.02, s + 0.02, z1 - sh, z1, sd_ + 0.012, M['pl_line'])
        s += 1.2 * U


def top_plaza(A, M, poly, z1, sd, U=0.9, keep_out=None):
    A[3].face([V(X, Y, z1 + 0.005) for X, Y in poly], M['pl_trav'], (0, 0, 1))
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    X = min(xs) + 1.2 * U
    while X < max(xs):
        A[3].face([V(X - 0.025, min(ys), z1 + 0.02), V(X + 0.025, min(ys), z1 + 0.02), V(X + 0.025, max(ys), z1 + 0.02), V(X - 0.025, max(ys), z1 + 0.02)], M['pl_line'], (0, 0, 1))
        X += 1.2 * U
    Y = min(ys) + 1.2 * U
    while Y < max(ys):
        A[3].face([V(min(xs), Y - 0.025, z1 + 0.02), V(max(xs), Y - 0.025, z1 + 0.02), V(max(xs), Y + 0.025, z1 + 0.02), V(min(xs), Y + 0.025, z1 + 0.02)], M['pl_line'], (0, 0, 1))
        Y += 1.2 * U
    _cells(poly, 1.2 * U, lambda X, Y, i, j: (hsh(i, j, sd, 59.1) < 0.18) and A[3].face([V(X - 0.5 * U, Y - 0.5 * U, z1 + 0.015), V(X + 0.5 * U, Y - 0.5 * U, z1 + 0.015), V(X + 0.5 * U, Y + 0.5 * U, z1 + 0.015), V(X - 0.5 * U, Y + 0.5 * U, z1 + 0.015)], M['pl_trav2'], (0, 0, 1)), sd, 0.0)
    _rim(A, M, poly, z1, U, 'pl_step')


# 종류 → (옆면 함수, 윗면 함수, 덩어리 옆면 재질, 덩어리 윗면 재질). 'strata'(기본) = 기존 흙 지층 판
SIDE_KINDS = {
    'ashlar': (side_ashlar, top_ashlar, 'ash_joint', 'ak_top'),            # 아크로폴리스: 성벽 마름돌
    'paved': (side_paved, top_paved, 'pv_soil', 'pv_top'),                 # 콜로세움: 자갈 포장 + 흙 단면
    'quay': (side_quay, top_quay, 'q_joint', 'q_land'),                    # 포르투스: 석축 부두
    'brick': (side_brick, top_brick, 'bw_joint', 'bw_terrace'),            # 트라야누스 시장: 계단식 벽돌 옹벽
    'rock': (side_rock, top_rock, 'rk_dark', 'lawn'),                      # 수도교: 석회암 판 바위 물가
    'grass': (side_grass, top_grass, 'gb_grass2', 'lawn'),                 # 하드리아누스: 풀 비탈 + 갈대
    'mound': (side_mound, top_mound, 'md_earth', 'md_ground'),             # 메텔라: 잔돌 섞인 흙 둔덕 + 아피아 가도
    'riverwall': (side_riverwall, top_riverwall, 'rw_joint', 'land'),      # 마르켈루스: 테베레 강둑 석축
    'forum': (side_forum, top_forum, 'strata', 'fr_earth'),                # 막센티우스: 포룸 판석 폐허
    'plaza': (side_plaza, top_plaza, 'pl_face', 'pl_trav'),                # 네로 받침: 판석 마당
}

KIND_ALIAS = {'earth': None, 'strata': None, 'riverbank': 'riverwall', 'travertine': 'paved', 'slab': 'forum', 'stone': 'riverwall'}   # d7 spec 이름 → 종류(None = 기본 흙 지층)
LOT_KIND = {'colosseum': 'paved', 'acropolis': 'ashlar', 'market': 'brick', 'aqueduct': 'rock', 'theatre': 'riverwall', 'basilica': 'forum',
            'mausoleum': 'grass', 'portus': 'quay', 'metella': 'mound'}       # 23:22 사용자: 디오라마 디자인은 내 것(레퍼런스-지형표) — spec은 배치만
BLOCK_KIND = {'A': 'paved', 'B': 'riverwall', 'C': None, 'E': 'mound'}       # 블록 기본(가까운 대지가 없는 가장자리)
EDGE_SEG, EDGE_REACH = 30.0, 25.0                                            # 가장자리 조각 길이 · 대지에서 닿는 거리(평면)
LOT_SKIP = {'acropolis', 'mausoleum', 'metella'}
USER_REMOVED_LOT_TOPS = {'portus'}                                                                                                # 건물 모델이 제 받침(성벽 블록·풀 언덕)을 함께 짓는다


def kind_of(k, lot_id=None):
    if lot_id in LOT_KIND:
        return LOT_KIND[lot_id]
    k = str(k or 'strata')
    return KIND_ALIAS.get(k, k) if k in KIND_ALIAS else k


# ───────────────────────── 23:43 사용자: 블록 자체를 꾸민다 — 윗면 높이장(언덕·골짜기·둔덕이 블록 땅) · 옆면 = 그 단면 ─────────────────────────
def _breaks(vals, lo, hi, step):
    raw = sorted(set([lo, hi] + [v for v in vals if lo - 1e-6 <= v <= hi + 1e-6] + [lo + step * k for k in range(int((hi - lo) / step) + 1)]))
    out = []
    for v in raw:
        if not out or v - out[-1] > 2e-3:
            out.append(v)
    return out


def field_z(feats, X, Y):
    """블록 지형 특징(features)을 차례로 합친 높이. 특징은 제 사각형(rect) 안에서만 작동하고 사각형 가장자리에서 0으로 맞물린다"""
    z = 0.0
    for f in feats:
        x0, x1, y0, y1 = f['rect']
        if x0 <= X <= x1 and y0 <= Y <= y1:
            v = f['z'](X, Y)
            op = f.get('op', 'max')
            z = max(z, v) if op == 'max' else (min(z, v) if op == 'min' else v)
    return z


def _in_feat(feats, X, Y):
    for f in feats:
        x0, x1, y0, y1 = f['rect']
        if x0 < X < x1 and y0 < Y < y1:
            return f
    return None


def _slant_edges(poly):
    n = len(poly)
    return [(poly[k], poly[(k + 1) % n]) for k in range(n) if abs(poly[k][0] - poly[(k + 1) % n][0]) > 1e-6 and abs(poly[k][1] - poly[(k + 1) % n][1]) > 1e-6]


def _cell_cut(poly, slant, a, b, c, d):
    """00:25: 빗변(육각 내항 홈 등)이 지나는 칸이면 칸 ∩ 윤곽 다각형(평면) — 아니면 None(칸 가운데 판정 그대로)"""
    if not any(min(p[0], q[0]) < b and max(p[0], q[0]) > a and min(p[1], q[1]) < d and max(p[1], q[1]) > c for p, q in slant):
        return None
    out = list(poly)
    for f in (lambda p: a - p[0], lambda p: p[0] - b, lambda p: c - p[1], lambda p: p[1] - d):
        out = GR.clip_half(out, f)
        if len(out) < 3:
            return []
    return out


def _field_top(A, M, poly, feats, holes, top_mat, seed=0.0):
    """평평한 칸(사각형 격자, 굽은 구멍은 칸 안 삼각분할) + 특징 사각형마다 높이장 칸(재질 = 특징 mat(X, Y, z, 기울기 방향))"""
    from mathutils.geometry import tessellate_polygon
    slant = _slant_edges(poly)
    X0, X1 = min(p[0] for p in poly), max(p[0] for p in poly); Y0, Y1 = min(p[1] for p in poly), max(p[1] for p in poly)
    hx = [v for h in holes for v in (min(p[0] for p in h) - 0.6, max(p[0] for p in h) + 0.6)]
    hy = [v for h in holes for v in (min(p[1] for p in h) - 0.6, max(p[1] for p in h) + 0.6)]
    gx = _breaks([p[0] for p in poly] + [v for f in feats for v in f['rect'][:2]] + hx, X0, X1, 40.0)
    gy = _breaks([p[1] for p in poly] + [v for f in feats for v in f['rect'][2:]] + hy, Y0, Y1, 40.0)
    for i in range(len(gx) - 1):
        for j in range(len(gy) - 1):
            a, b, c, d = gx[i], gx[i + 1], gy[j], gy[j + 1]
            cx, cy = 0.5 * (a + b), 0.5 * (c + d)
            if _in_feat(feats, cx, cy):
                continue
            cut = _cell_cut(poly, slant, a, b, c, d) if slant else None
            if cut is not None:
                if len(cut) >= 3:
                    lp = [Vector((x, y, 0.0)) for x, y in cut]
                    for tri in tessellate_polygon([lp]):
                        A[0].face([V(lp[k].x, lp[k].y, 0.0) for k in tri], top_mat, (0, 0, 1))
                continue
            if not GR.pip(cx, cy, poly):
                continue
            hin = [h for h in holes if all(a < p[0] < b and c < p[1] < d for p in h)]
            if hin:
                loops = [[Vector((a, c, 0)), Vector((b, c, 0)), Vector((b, d, 0)), Vector((a, d, 0))]] + [[Vector((x, y, 0)) for x, y in h] for h in hin]
                flat = [p_ for lp in loops for p_ in lp]
                for tri in tessellate_polygon(loops):
                    A[0].face([V(flat[k].x, flat[k].y, 0.0) for k in tri], top_mat, (0, 0, 1))
            else:
                A[0].face([V(a, c, 0.0), V(b, c, 0.0), V(b, d, 0.0), V(a, d, 0.0)], top_mat, (0, 0, 1))
    Lx, Ly = -0.62, 0.18
    for f in feats:
        x0, x1, y0, y1 = f['rect']; st = f.get('step', 1.2)
        fx = _breaks([p[0] for p in poly], x0, x1, st); fy = _breaks([p[1] for p in poly], y0, y1, st)
        Z = [[field_z(feats, X, Y) if _in_feat(feats, X, Y) in (None, f) else f['z'](X, Y) for Y in fy] for X in fx]
        for i in range(len(fx) - 1):
            for j in range(len(fy) - 1):
                a, b, c, d = fx[i], fx[i + 1], fy[j], fy[j + 1]
                cx, cy = 0.5 * (a + b), 0.5 * (c + d)
                if _in_feat(feats, cx, cy) is not f:
                    continue
                cut = _cell_cut(poly, slant, a, b, c, d) if slant else None
                if cut is None and not GR.pip(cx, cy, poly):
                    continue
                if any(GR.pip(cx, cy, h) for h in holes):
                    continue
                if cut is not None:                                          # 빗변 칸: 잘린 다각형을 삼각분할(꼭짓점 높이 = 높이장)
                    if len(cut) < 3:
                        continue
                    lp = [Vector((x, y, 0.0)) for x, y in cut]
                    zf_ = lambda X, Y: field_z(feats, X, Y) if _in_feat(feats, X, Y) in (None, f) else f['z'](X, Y)
                    pts = [V(p_.x, p_.y, zf_(p_.x, p_.y)) for p_ in lp]
                    tris = [tuple(t_) for t_ in tessellate_polygon([lp])]
                else:
                    zz = [Z[i][j], Z[i + 1][j], Z[i + 1][j + 1], Z[i][j + 1]]
                    pts = [V(a, c, zz[0]), V(b, c, zz[1]), V(b, d, zz[2]), V(a, d, zz[3])]
                    tris = ((0, 1, 2), (0, 2, 3))
                for tri in tris:
                    tp = [pts[k] for k in tri]
                    nr = (Vector(tp[1]) - Vector(tp[0])).cross(Vector(tp[2]) - Vector(tp[0]))
                    if nr.length < 1e-9:
                        continue
                    nr.normalize()
                    if nr.z < 0:
                        nr = -nr
                    sl = math.hypot(nr.x, nr.y)
                    dd = (nr.x * Lx + nr.y * Ly) / max(1e-6, sl * math.hypot(Lx, Ly)) if sl > 1e-6 else 0.0
                    zc = sum(p_[2] for p_ in tp) / 3.0
                    mk = f['mat'](cx, cy, zc, sl, dd)
                    A[0].face(tp, M[mk] if isinstance(mk, str) else mk, (0, 0, 1))
        if f.get('deco'):
            f['deco'](A, M, lambda X, Y: field_z(feats, X, Y))


def _profile(feats, a, t, L, ds=0.8):
    m = max(2, int(L / ds))
    return [(L * k / m, field_z(feats, a[0] + t[0] * L * k / m, a[1] + t[1] * L * k / m)) for k in range(m + 1)]


# ───────────────────────── 땅 블록 ─────────────────────────
def build_block(GC, M, blk, seed=0.0):
    """blk = {'id', 'poly': [(X, Y)…] 평면, 'z': 윗면 높이(기본 0)}. 루트 DIO_Block_{id}_root, 층 L0~L6"""
    bid, poly, zt = str(blk['id']), [tuple(p) for p in blk['poly']], float(blk.get('z', 0.0))
    zb = float(blk['z0']) if blk.get('z0') is not None else WATER_Z - SIDE_PAD           # 대지(lot)는 블록 윗면(z0)에서 솟는다
    H = zt - (zb if blk.get('z0') is not None else WATER_Z)
    root = bpy.data.objects.new('DIO_Block_%s_root' % bid, None); GC.objects.link(root)
    a0, a1, a2, a3, a4, a5, a6 = (Acc() for _ in range(7))
    # L0 윗면(땅) + 보이는 옆면(지층 단면 재질 — 위치 기반이라 어느 면에도 같은 띠)
    kind = kind_of(blk.get('kind'), blk.get('lot'))
    SK = SIDE_KINDS.get(kind) if kind else None
    U = float(blk.get('unit') or 0.9)
    holes = [h for h in (blk.get('holes') or []) if len(h) >= 3]
    feats = blk.get('features') or []
    if feats:                                                            # 23:43: 블록 윗면 = 높이장(지형 특징이 블록 땅의 일부) · 옆면은 아래 조각마다 단면 커튼
        _field_top((a0, a1, a2, a3, a4, a5, a6), M, poly, feats, holes, M[SK[3]] if SK else M['land'], seed)
        holes_ = holes; holes = []
    else:
        a0.prism(poly, zb, zt, M[SK[3]] if SK else M['land'], M[SK[2]] if SK else M['strata'], top=not holes)
    if holes:                                                            # 콜로세움 하이포게움 등: 윗면을 구멍 낸 다각형으로 삼각분할
        from mathutils.geometry import tessellate_polygon
        loops = [[Vector((X, Y, 0.0)) for X, Y in poly]] + [[Vector((X, Y, 0.0)) for X, Y in h] for h in holes]
        flat = [p_ for lp in loops for p_ in lp]
        for tri in tessellate_polygon(loops):
            a0.face([V(flat[k].x, flat[k].y, zt) for k in tri], M[SK[3]] if SK else M['land'], (0, 0, 1))
    edges = vis_edges(poly)
    pieces = []                                                          # 23:22: 가장자리를 조각내 가까운 건물 대지의 땅 종류로(없으면 블록 기본)
    for (a, t, n, L) in edges:
        ek = blk.get('edge_kind')
        if ek is None:
            pieces.append((a, t, n, L, kind)); continue
        ns = max(1, int(math.ceil(L / EDGE_SEG)))
        for q in range(ns):
            s0 = L * q / ns; Ls = L / ns
            a_ = (a[0] + t[0] * s0, a[1] + t[1] * s0)
            k_ = ek((a_[0] + t[0] * Ls / 2, a_[1] + t[1] * Ls / 2))
            pieces.append((a_, t, n, Ls, k_ if k_ is not None else kind))
    i = 0
    zt_flat = zt
    for e, (a, t, n, L, kd) in enumerate(pieces):
        sd = seed + 31.0 * e
        SKe = SIDE_KINDS.get(kd) if kd else None
        zt = zt_flat
        if feats:                                                            # 단면 커튼(위 변 = 지형 높이) · 지형이 솟은 단면은 석회암 층 줄
            pr = _profile(feats, a, t, L)
            a0.face([_on(a, t, n, 0.0, zb, 0.0), _on(a, t, n, L, zb, 0.0)] + [_on(a, t, n, s_, z_, 0.0) for s_, z_ in pr[::-1]], M[SKe[2]] if SKe else (M[SK[2]] if SK else M['strata']),
                    (n[0], -n[1], 0))
            zmin = min(z_ for _, z_ in pr); zmax = max(z_ for _, z_ in pr)
            if zmax > 0.3:
                for off in (0.25, 1.1, 2.3):
                    seg = [(s_, z_ - off) for s_, z_ in pr if z_ - off > 0.15]
                    if len(seg) >= 2:
                        a2.face([_on(a, t, n, s_, z_, 0.02) for s_, z_ in seg] + [_on(a, t, n, s_, z_ - 0.14, 0.02) for s_, z_ in seg[::-1]], M['lime_dk'] if off > 0.5 else M['lime_top'],
                                (n[0], -n[1], 0))
            if zmin < -0.3:                                                  # 골짜기로 내려간 조각: 옆면 장식은 짓지 않는다(떠 보이지 않게)
                continue
            zt = 0.0
        if blk.get('plain_edge') and blk['plain_edge']((a[0] + t[0] * L / 2, a[1] + t[1] * L / 2)):
            continue                                                         # 00:25 포르투스 홈: 건물 모델 안벽이 앞에 선다 → 단면 면만
        if SKe:                                                              # 22:22 종류별 옆면(성벽 마름돌 등)
            SKe[0]((a0, a1, a2, a3, a4, a5, a6), M, a, t, n, L, zb, zt, sd, U)
            continue
        # L1 윗선 밑 그늘 띠(0.35) · 물가 해식굴
        a1.face([_on(a, t, n, 0.0, zt - 0.05, 0.012), _on(a, t, n, L, zt - 0.05, 0.012), _on(a, t, n, L, zt - 0.4, 0.012), _on(a, t, n, 0.0, zt - 0.4, 0.012)],
                M['under_lip'], (n[0], -n[1], 0))
        for j in range(max(0, int(L / 26.0))):
            s0 = 4.0 + (L - 10.0) * hsh(j, sd, 1.1); w = 2.0 + 1.6 * hsh(j, sd, 1.2); hh = 1.0 + 1.1 * hsh(j, sd, 1.3)
            a1.face([_on(a, t, n, s0 + w * (0.5 - 0.5 * math.cos(math.pi * q / 8)), WATER_Z + hh * math.sin(math.pi * q / 8), 0.015) for q in range(9)],
                    M['cave'], (n[0], -n[1], 0))
        # L2 지층 경계선(위 −0.26H · 아래 −0.63H, 단면 재질과 같은 물결)
        for zc in (zt - 0.26 * H, zt - 0.63 * H):
            m = max(2, int(L / 0.8))
            up = []
            for q in range(m + 1):
                s = L * q / m
                X, Y = a[0] + t[0] * s, a[1] + t[1] * s
                up.append((s, zc - GR._strata_w(X + Y) + 0.09))
            a2.face([_on(a, t, n, s, z, 0.02) for s, z in up] + [_on(a, t, n, s, z - 0.2, 0.02) for s, z in up[::-1]], M['root_dk'], (n[0], -n[1], 0))
        # L3 자갈(밝은 돌 조각)
        for j in range(int(L * 0.55)):
            s = 0.6 + (L - 1.2) * hsh(j, sd, 2.4); z = zt - 1.4 - (H - 2.2) * hsh(j, sd, 3.6); r = 0.16 + 0.28 * hsh(j, sd, 4.8)
            a3.face([_on(a, t, n, s + r * math.cos(2 * math.pi * k / 6), z + r * 0.7 * math.sin(2 * math.pi * k / 6), 0.025) for k in range(6)],
                    M['rock_top'] if z < zt - 0.63 * H else M['land_patch2'], (n[0], -n[1], 0))
        # L4 박힌 돌(옆면에서 튀어나온 덩이) · 물가 바위
        for j in range(int(L / 7.0)):
            s = 1.0 + (L - 2.0) * hsh(j, sd, 5.1); z = zt - 1.6 - (H - 3.0) * hsh(j, sd, 5.2); r = 0.35 + 0.4 * hsh(j, sd, 5.3)
            X, Y = a[0] + t[0] * s + n[0] * 0.1, a[1] + t[1] * s + n[1] * 0.1
            a4.blob(X, Y, z, r * 1.1, r * 0.8, r * 0.7, M['rock'], 1, 0.2, sd + j, M['rock_top'], None)
        for j in range(int(L / 9.0)):
            s = 1.5 + (L - 3.0) * hsh(j, sd, 6.1); r = 0.6 + 0.9 * hsh(j, sd, 6.2)
            X, Y = a[0] + t[0] * s + n[0] * (0.4 + 0.8 * hsh(j, sd, 6.3)), a[1] + t[1] * s + n[1] * (0.4 + 0.8 * hsh(j, sd, 6.3))
            a4.blob(X, Y, WATER_Z + r * 0.25, r * 1.2, r * 0.9, r * 0.7, M['rock'], 1, 0.2, sd + 50 + j, M['rock_top'], None)
        # L5 윗선(땅 윗면 가장자리 밝은 띠, 0.55 안쪽)
        a5.face([_on(a, t, n, 0.0, zt + 0.04, -0.55), _on(a, t, n, L, zt + 0.04, -0.55), _on(a, t, n, L, zt + 0.04, 0.0), _on(a, t, n, 0.0, zt + 0.04, 0.0)], M['lip'], (0, 0, 1))
        # L6 매달린 풀·뿌리(윗선에서 늘어짐) · 물자국(빗물 짙은 줄) · 물때(수면 위 이끼 띠)
        s = 0.3
        while s < L - 0.6:
            w = 0.5 + 0.7 * hsh(i, 1.3)
            if hsh(i, 2.7) < 0.72:
                hang = 0.35 + 0.9 * hsh(i, 3.9); upz = 0.25 + 0.35 * hsh(i, 4.1)
                mt = (M['tuft'], M['tuft2'], M['tuft3'])[i % 3]
                a6.face([_on(a, t, n, s, zt - hang * 0.5, 0.03), _on(a, t, n, s + w, zt - hang * 0.3, 0.03), _on(a, t, n, s + w * 0.55, zt - hang, 0.03)], mt, (n[0], -n[1], 0))
                a6.face([_on(a, t, n, s, zt, 0.03), _on(a, t, n, s + w, zt, 0.03), _on(a, t, n, s + w * 0.5, zt + upz, 0.03)], mt, (n[0], -n[1], 0))
            elif hsh(i, 2.9) < 0.5:                                          # 뿌리(가는 짙은 줄)
                rl = 0.8 + 1.6 * hsh(i, 3.3)
                a6.face([_on(a, t, n, s, zt - 0.1, 0.03), _on(a, t, n, s + 0.07, zt - 0.1, 0.03), _on(a, t, n, s + 0.2, zt - rl, 0.03), _on(a, t, n, s + 0.13, zt - rl, 0.03)],
                        M['root_dk'], (n[0], -n[1], 0))
            s += w + 0.15 + 0.9 * hsh(i, 5.2); i += 1
        for j in range(int(L / 4.5)):
            s = 0.6 + (L - 1.2) * hsh(j, sd, 8.1); w = 0.18 + 0.32 * hsh(j, sd, 8.7)
            z1 = zt - 0.9 - 1.0 * hsh(j, sd, 9.3); z0 = z1 - 1.5 - (H - 4.0) * 0.6 * hsh(j, sd, 9.9)
            a6.face([_on(a, t, n, s, z0, 0.035), _on(a, t, n, s + w, z0 + 0.3, 0.035), _on(a, t, n, s + w, z1, 0.035), _on(a, t, n, s, z1, 0.035)], M['stain'], (n[0], -n[1], 0))
        a6.face([_on(a, t, n, 0.0, WATER_Z + 0.02, 0.03), _on(a, t, n, L, WATER_Z + 0.02, 0.03), _on(a, t, n, L, WATER_Z + 0.55, 0.03), _on(a, t, n, 0.0, WATER_Z + 0.45, 0.03)],
                M['moss_w'], (n[0], -n[1], 0))
    zt = zt_flat if pieces else zt
    hk = holes if holes else (holes_ if feats else [])
    if SK:
        SK[1]((a0, a1, a2, a3, a4, a5, a6), M, poly, zt, seed, U, (lambda X, Y: any(GR.pip(X, Y, h) for h in hk) or _in_feat(feats, X, Y) is not None) if (hk or feats) else None)
    # L3 땅 윗면 결(흙 얼룩) · L6 윗면 풀 포기(기본 지층 판만)
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    for j in range(0 if SK else int((max(xs) - min(xs)) * (max(ys) - min(ys)) / 260.0)):
        X = min(xs) + (max(xs) - min(xs)) * hsh(j, seed, 11.1); Y = min(ys) + (max(ys) - min(ys)) * hsh(j, seed, 11.2)
        if not GR.pip(X, Y, poly):
            continue
        r = 0.6 + 1.2 * hsh(j, seed, 11.3)
        a3.face([V(X + r * math.cos(2 * math.pi * k / 7), Y + r * 0.6 * math.sin(2 * math.pi * k / 7), zt + 0.02) for k in range(7)],
                M['land_patch'] if j % 3 else M['land_dot'], (0, 0, 1))
    for nm_, ac in (('L0_Mass', a0), ('L1_ShadeCaves', a1), ('L2_StrataLines', a2), ('L3_PebblesSoil', a3), ('L4_Stones', a4), ('L5_Lip', a5), ('L6_GrassRootsStains', a6)):
        ac.obj('DIO_Block_%s_%s' % (bid, nm_), GC, root)
    return root


# ───────────────────────── 물(블록 사이 강·운하·바다, 한 수면) ─────────────────────────
def build_water(GC, M, area, blocks, seed=0.0):
    """area = 평면 다각형(무대 전체). 블록이 위에 얹혀 물은 블록 사이·바깥에만 보인다"""
    root = bpy.data.objects.new('DIO_Water_root', None); GC.objects.link(root)
    a0, a1, a2, a3, a4, a5, a6 = (Acc() for _ in range(7))
    a0.face([V(X, Y, WATER_Z) for X, Y in area], M['river'], (0, 0, 1))
    polys = [[tuple(p) for p in b['poly']] for b in blocks]

    def in_land(X, Y, m=0.0):
        return any(GR.pip(X, Y, q) for q in polys) or (m > 0 and any(GR.pip(X + dx, Y + dy, q) for q in polys for dx, dy in ((m, 0), (-m, 0), (0, m), (0, -m))))
    for bi, q in enumerate(polys):
        for (a, t, n, L) in vis_edges(q):                                     # L1 블록 발치 앞 물 그늘 띠 · L6 물거품 줄
            a1.face([V(a[0] + t[0] * s + n[0] * d, a[1] + t[1] * s + n[1] * d, WATER_Z + 0.01) for s, d in ((0, 0), (L, 0), (L, 1.1), (0, 1.1))], M['r_deep'], (0, 0, 1))
            k = 0; s = 0.4
            while s < L - 0.8:
                w = 0.8 + 1.6 * hsh(k, bi, 7.1)
                d = 1.2 + 0.4 * hsh(k, bi, 7.2)
                a6.face([V(a[0] + t[0] * u + n[0] * dd, a[1] + t[1] * u + n[1] * dd, WATER_Z + 0.03) for u, dd in ((s, d), (s + w, d), (s + w, d + 0.16), (s, d + 0.16))], M['foam'], (0, 0, 1))
                s += w + 0.6 + 1.4 * hsh(k, bi, 7.3); k += 1
    xs = [p[0] for p in area]; ys = [p[1] for p in area]
    for j in range(900):                                                     # L3 물결 · L5 반짝임(블록 밖 물에만)
        X = min(xs) + (max(xs) - min(xs)) * hsh(j, seed, 12.1); Y = min(ys) + (max(ys) - min(ys)) * hsh(j, seed, 12.2)
        if not GR.pip(X, Y, area) or in_land(X, Y, 1.6):
            continue
        Lw = 0.8 + 1.4 * hsh(j, seed, 12.3)
        if j % 4:
            a3.face([V(X, Y, WATER_Z + 0.02), V(X + Lw, Y - Lw * 0.15, WATER_Z + 0.02), V(X + Lw, Y - Lw * 0.15 + 0.14, WATER_Z + 0.02), V(X, Y + 0.14, WATER_Z + 0.02)], M['r_wave'], (0, 0, 1))
        else:
            a5.face([V(X, Y, WATER_Z + 0.025), V(X + 0.4, Y - 0.05, WATER_Z + 0.025), V(X + 0.4, Y + 0.07, WATER_Z + 0.025), V(X, Y + 0.12, WATER_Z + 0.025)], M['glint'], (0, 0, 1))
    for bi, q in enumerate(polys):                                           # L2 물가 돌계단 · L4 계선주(블록마다 한 곳)
        ve = vis_edges(q)
        if not ve:
            continue
        a, t, n, L = max(ve, key=lambda e: e[3])
        s0 = L * (0.3 + 0.4 * hsh(bi, 13.1))
        for st in range(5):
            d0 = 0.05 + 0.45 * st
            pts = [(s0, d0), (s0 + 2.4, d0), (s0 + 2.4, d0 + 0.45), (s0, d0 + 0.45)]
            a2.face([V(a[0] + t[0] * u + n[0] * dd, a[1] + t[1] * u + n[1] * dd, WATER_Z + (st + 1) * 0.9) for u, dd in pts], M['rock_top'], (0, 0, 1))
        for k in range(3):
            u = s0 + 4.0 + 2.2 * k
            if u < L - 1.0:
                a4.cyl(a[0] + t[0] * u + n[0] * 0.6, a[1] + t[1] * u + n[1] * 0.6, 0.18, WATER_Z - 0.2, WATER_Z + 1.2, M['bridge_dk'])
    for nm_, ac in (('L0_Water', a0), ('L1_FootShade', a1), ('L2_Landings', a2), ('L3_Waves', a3), ('L4_Posts', a4), ('L5_Glints', a5), ('L6_Foam', a6)):
        ac.obj('DIO_Water_%s' % nm_, GC, root)
    return root


# ───────────────────────── 도로망(평면 X·Y축 구간, 직각 꺾임, 물 위는 아치 다리) ─────────────────────────
def _block_at(blocks, X, Y):
    for b in blocks:
        if GR.pip(X, Y, b['poly']):
            return b
    return None


def _runs(blocks, p0, p1, step=0.25):
    """축 정렬 선분 p0→p1을 땅(블록 안)·물 구간으로 나눈다: [(s0, s1, block 또는 None)]"""
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    n = max(1, int(L / step))
    out = []
    cur = None
    for i in range(n + 1):
        s = L * i / n
        X, Y = p0[0] + (p1[0] - p0[0]) * s / L, p0[1] + (p1[1] - p0[1]) * s / L
        b = _block_at(blocks, X, Y)
        key = id(b) if b else None
        if cur is None or cur[2] != key:
            if cur is not None:
                out.append((cur[0], s, cur[3]))
            cur = [s, s, key, b]
    out.append((cur[0], L, cur[3]))
    return [(a, b_, blk) for a, b_, blk in out if b_ - a > 1e-6], L


def build_roads(GC, M, roads, blocks):
    """roads = [{'id', 'pts': [(X, Y)…] 평면 꺾은선(X·Y축 구간만), 'w': 평면 폭}]. 루트 DIO_Roads_root, 층 L0~L6"""
    root = bpy.data.objects.new('DIO_Roads_root', None); GC.objects.link(root)
    a0, a1, a2, a3, a4, a5, a6 = (Acc() for _ in range(7))
    warn = []
    for ri, rd in enumerate(roads):
        pts = [tuple(p) for p in rd['pts']]; w = float(rd.get('w', 6.0)); hw = w / 2.0
        for k in range(len(pts) - 1):
            p0, p1 = pts[k], pts[k + 1]
            ax = 'X' if abs(p1[1] - p0[1]) < 1e-6 else ('Y' if abs(p1[0] - p0[0]) < 1e-6 else None)
            if ax is None:
                warn.append('%s 구간 %d 축 정렬 아님(건너뜀)' % (rd.get('id'), k)); continue
            runs, L = _runs(blocks, p0, p1)
            d = ((p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L)
            ext0 = hw if k > 0 else 0.0                                       # 직각 꺾임: 앞 구간 끝을 반폭만큼 늘여 모서리를 메운다
            for (s0, s1, blk) in runs:
                if blk is None:
                    continue
                zt = float(blk.get('z', 0.0))
                ss0 = s0 - (ext0 if s0 < 1e-6 else 0.0); ss1 = s1 + (hw if (s1 > L - 1e-6 and k < len(pts) - 2) else 0.0)
                qa = (p0[0] + d[0] * ss0, p0[1] + d[1] * ss0); qb = (p0[0] + d[0] * ss1, p0[1] + d[1] * ss1)
                X0, X1 = sorted((qa[0], qb[0])); Y0, Y1 = sorted((qa[1], qb[1]))
                if ax == 'X':
                    Y0, Y1 = p0[1] - hw, p0[1] + hw
                else:
                    X0, X1 = p0[0] - hw, p0[0] + hw
                a0.box(X0, X1, Y0, Y1, zt, zt + ROAD_T, M['slab'], M['slab_side'])            # L0 판석 길 몸(윗면 PAL slab)
                if ax == 'X':                                                   # L1 길 앞(보이는 +Y 쪽) 땅 위 그늘 띠
                    a1.face([V(X0, Y1, zt + 0.01), V(X1, Y1, zt + 0.01), V(X1, Y1 + 0.35, zt + 0.01), V(X0, Y1 + 0.35, zt + 0.01)], M['road_shade'], (0, 0, 1))
                    kb = [(X0, X1, Y0, Y0 + ROAD_KERB[0]), (X0, X1, Y1 - ROAD_KERB[0], Y1)]
                else:
                    a1.face([V(X1, Y0, zt + 0.01), V(X1 + 0.35, Y0, zt + 0.01), V(X1 + 0.35, Y1, zt + 0.01), V(X1, Y1, zt + 0.01)], M['road_shade'], (0, 0, 1))
                    kb = [(X0, X0 + ROAD_KERB[0], Y0, Y1), (X1 - ROAD_KERB[0], X1, Y0, Y1)]
                for (x0, x1, y0, y1) in kb:                                     # L2 갓돌 · L5 갓돌 윗선
                    a2.box(x0, x1, y0, y1, zt + ROAD_T, zt + ROAD_T + ROAD_KERB[1], M['curb'])
                    a5.box(x0, x1, y0, y1, zt + ROAD_T + ROAD_KERB[1], zt + ROAD_T + ROAD_KERB[1] + 0.02, M['curb_hi'], sides='')
                ln = (X1 - X0) if ax == 'X' else (Y1 - Y0)
                m = int(ln / 1.4)
                for j in range(1, m):                                           # L3 판석 줄눈(가로) + 가운데 세로 줄눈
                    if ax == 'X':
                        xj = X0 + ln * j / m
                        a3.face([V(xj - 0.05, Y0 + 0.3, zt + ROAD_T + 0.01), V(xj + 0.05, Y0 + 0.3, zt + ROAD_T + 0.01), V(xj + 0.05, Y1 - 0.3, zt + ROAD_T + 0.01), V(xj - 0.05, Y1 - 0.3, zt + ROAD_T + 0.01)], M['slab_joint'], (0, 0, 1))
                    else:
                        yj = Y0 + ln * j / m
                        a3.face([V(X0 + 0.3, yj - 0.05, zt + ROAD_T + 0.01), V(X1 - 0.3, yj - 0.05, zt + ROAD_T + 0.01), V(X1 - 0.3, yj + 0.05, zt + ROAD_T + 0.01), V(X0 + 0.3, yj + 0.05, zt + ROAD_T + 0.01)], M['slab_joint'], (0, 0, 1))
                if ax == 'X':
                    a3.face([V(X0, p0[1] - 0.04, zt + ROAD_T + 0.012), V(X1, p0[1] - 0.04, zt + ROAD_T + 0.012), V(X1, p0[1] + 0.04, zt + ROAD_T + 0.012), V(X0, p0[1] + 0.04, zt + ROAD_T + 0.012)], M['slab_joint'], (0, 0, 1))
                else:
                    a3.face([V(p0[0] - 0.04, Y0, zt + ROAD_T + 0.012), V(p0[0] + 0.04, Y0, zt + ROAD_T + 0.012), V(p0[0] + 0.04, Y1, zt + ROAD_T + 0.012), V(p0[0] - 0.04, Y1, zt + ROAD_T + 0.012)], M['slab_joint'], (0, 0, 1))
                for j in range(int(ln * (Y1 - Y0 if ax == 'X' else X1 - X0) / 6.0)):     # L6 닳은 자국·줄눈 풀
                    u = hsh(j, ri, k, 14.1); v = hsh(j, ri, k, 14.2)
                    X = X0 + (X1 - X0) * (u if ax == 'X' else (0.15 + 0.7 * v)); Y = Y0 + (Y1 - Y0) * ((0.15 + 0.7 * v) if ax == 'X' else u)
                    r = 0.25 + 0.35 * hsh(j, ri, k, 14.3)
                    mt = M['slab_wear'] if j % 3 else M['tuft']
                    a6.face([V(X + r * math.cos(2 * math.pi * q / 6), Y + r * 0.6 * math.sin(2 * math.pi * q / 6), zt + ROAD_T + 0.015) for q in range(6)], mt, (0, 0, 1))
            for (s0, s1, blk) in runs:                                          # 물 위 구간 → 아치 다리(양쪽 둑 블록 높이 중 높은 쪽 + 판석)
                if blk is not None:
                    continue
                qa = (p0[0] + d[0] * s0, p0[1] + d[1] * s0); qb = (p0[0] + d[0] * s1, p0[1] + d[1] * s1)
                bA = _block_at(blocks, p0[0] + d[0] * (s0 - 0.5), p0[1] + d[1] * (s0 - 0.5)); bB = _block_at(blocks, p0[0] + d[0] * (s1 + 0.5), p0[1] + d[1] * (s1 + 0.5))
                zt = max(float((bA or {}).get('z', 0.0)), float((bB or {}).get('z', 0.0)))
                span = s1 - s0
                na = max(1, int(round(span / 7.0)))
                holes = []
                pw = 1.2
                aw = (span - pw * (na + 1)) / na
                for j in range(na):
                    u0 = s0 + pw + j * (aw + pw); u1 = u0 + aw
                    holes.append((u0, u1))
                if ax == 'X':
                    Y0, Y1 = p0[1] - hw, p0[1] + hw
                    sgn = 1.0 if d[0] > 0 else -1.0
                    hb = [('arch', min(p0[0] + sgn * u0, p0[0] + sgn * u1), max(p0[0] + sgn * u0, p0[0] + sgn * u1), WATER_Z - 0.3, zt - 1.2 - aw / 2.0) for u0, u1 in holes]
                    G.wall_holes(a0.bm, 'X', min(qa[0], qb[0]), max(qa[0], qb[0]), -Y1, -Y0, WATER_Z - SIDE_PAD, zt + ROAD_T, hb, a0.mi(M['bridge']), 12)
                else:
                    X0, X1 = p0[0] - hw, p0[0] + hw
                    sgn = 1.0 if d[1] > 0 else -1.0
                    hb = [('arch', min(-(p0[1] + sgn * u0), -(p0[1] + sgn * u1)), max(-(p0[1] + sgn * u0), -(p0[1] + sgn * u1)), WATER_Z - 0.3, zt - 1.2 - aw / 2.0) for u0, u1 in holes]
                    G.wall_holes(a0.bm, 'Y', min(-qa[1], -qb[1]), max(-qa[1], -qb[1]), X0, X1, WATER_Z - SIDE_PAD, zt + ROAD_T, hb, a0.mi(M['bridge']), 12)
                Xa, Xb = sorted((qa[0], qb[0])); Ya, Yb = sorted((qa[1], qb[1]))
                if ax == 'X':
                    Ya, Yb = Y0, Y1
                else:
                    Xa, Xb = X0, X1
                a0.box(Xa, Xb, Ya, Yb, zt + ROAD_T - 0.02, zt + ROAD_T, M['slab'], M['bridge'], sides='')
                for j, (u0, u1) in enumerate(holes):                            # L1 아치 속 그늘 · L4 홍예석
                    cu = s0 + (u0 + u1) / 2.0 - s0; rr = (u1 - u0) / 2.0; zs = zt - 1.2 - aw / 2.0
                    for q in range(9):
                        th0, th1 = math.pi * q / 9, math.pi * (q + 1) / 9
                        if ax == 'X':
                            yf = Y1 + 0.04
                            c0 = p0[0] + d[0] * cu
                            pts_ = [(c0 - (rr + 0.02) * math.cos(th0), zs + (rr + 0.02) * math.sin(th0)), (c0 - (rr + 0.4) * math.cos(th0), zs + (rr + 0.4) * math.sin(th0)),
                                    (c0 - (rr + 0.4) * math.cos(th1), zs + (rr + 0.4) * math.sin(th1)), (c0 - (rr + 0.02) * math.cos(th1), zs + (rr + 0.02) * math.sin(th1))]
                            a4.face([V(x, yf, z) for x, z in pts_], M['vous'] if q % 2 else M['bridge_dk'], (0, -1, 0))
                        else:
                            xf = X1 + 0.04
                            c0 = p0[1] + d[1] * cu
                            pts_ = [(c0 - (rr + 0.02) * math.cos(th0), zs + (rr + 0.02) * math.sin(th0)), (c0 - (rr + 0.4) * math.cos(th0), zs + (rr + 0.4) * math.sin(th0)),
                                    (c0 - (rr + 0.4) * math.cos(th1), zs + (rr + 0.4) * math.sin(th1)), (c0 - (rr + 0.02) * math.cos(th1), zs + (rr + 0.02) * math.sin(th1))]
                            a4.face([V(xf, y, z) for y, z in pts_], M['vous'] if q % 2 else M['bridge_dk'], (1, 0, 0))
                if ax == 'X':                                                   # L2 다리 난간 · L5 난간 윗선
                    for (y0, y1) in ((Y0, Y0 + 0.35), (Y1 - 0.35, Y1)):
                        a2.box(Xa, Xb, y0, y1, zt + ROAD_T, zt + ROAD_T + 0.9, M['bridge'])
                        a5.box(Xa, Xb, y0, y1, zt + ROAD_T + 0.9, zt + ROAD_T + 0.94, M['curb_hi'], sides='')
                else:
                    for (x0, x1) in ((X0, X0 + 0.35), (X1 - 0.35, X1)):
                        a2.box(x0, x1, Ya, Yb, zt + ROAD_T, zt + ROAD_T + 0.9, M['bridge'])
                        a5.box(x0, x1, Ya, Yb, zt + ROAD_T + 0.9, zt + ROAD_T + 0.94, M['curb_hi'], sides='')
    for nm_, ac in (('L0_SlabsBridges', a0), ('L1_Shade', a1), ('L2_KerbsParapets', a2), ('L3_Joints', a3), ('L4_Voussoirs', a4), ('L5_Light', a5), ('L6_WearGrass', a6)):
        ac.obj('DIO_Roads_%s' % nm_, GC, root)
    return root, warn


def build(spec=None, clear=True):
    """spec = {'blocks': [...], 'roads': [...], 'area': 평면 다각형(물 범위)}. 없으면 design current spec의 core_map.diorama"""
    if spec is None:
        S = json.load(open(GR.SPEC, encoding='utf-8'))
        spec = S['core_map'].get('diorama') or {}
    global WATER_Z
    if spec.get('water_z') is not None:                                  # 블록 들린 높이(수면 높이)를 spec이 정할 수 있다
        WATER_Z = float(spec['water_z'])
    GC = R.coll(COLL, R.coll('ROMA_MAP'))
    if clear:
        R.clear_coll(COLL)
    M = mats()
    blocks = [dict(b) for b in (spec.get('blocks') or [])]
    lots = spec.get('lots') or []

    def edge_kind(pt):
        best = None
        for lt in lots:
            x0, x1, y0, y1 = lt['rect']
            dx = max(x0 - pt[0], 0.0, pt[0] - x1); dy = max(y0 - pt[1], 0.0, pt[1] - y1)
            d = math.hypot(dx, dy)
            if d <= EDGE_REACH and (best is None or d < best[0]):
                best = (d, LOT_KIND.get(lt['id']))
        return best[1] if best else None
    for b in blocks:
        if b['id'] in BLOCK_KIND:
            b['kind'] = BLOCK_KIND[b['id']] or 'strata'
        b['edge_kind'] = edge_kind
    for cut in [o for o in bpy.data.objects if o.name.startswith('X_CUT_') and o.type == 'MESH' and o.name in bpy.context.scene.objects]:
        mw = cut.matrix_world
        for f in cut.data.polygons:                                          # 절단체 윗면(법선 위) 다각형마다 구멍 하나(블록 안에 다 들어갈 때만)
            nw = (mw.to_3x3() @ f.normal)
            if nw.z < 0.9:
                continue
            ring = [((mw @ cut.data.vertices[k].co).x, -(mw @ cut.data.vertices[k].co).y) for k in f.vertices]
            for b in blocks:
                bp = [tuple(p) for p in b['poly']]
                if all(GR.pip(x, y, bp) for x, y in ring):
                    b.setdefault('holes', []).append(ring)
    for i, b in enumerate(blocks):
        build_block(GC, M, b, seed=17.0 * i)
    for i, lt in enumerate(spec.get('lots') or []):                     # d7: 건물별 땅(높이 z > 0이면 블록 윗면에서 솟은 대지, 0이면 윗면 무늬만)
        if lt['id'] in LOT_SKIP:
            continue
        x0, x1, y0, y1 = lt['rect']
        poly = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        k = kind_of(lt.get('kind') or lt.get('style'), lt['id'])
        if float(lt.get('z', 0.0)) > 0.0:
            build_block(GC, M, {'id': 'Lot_' + lt['id'], 'poly': poly, 'z': float(lt['z']), 'z0': 0.0, 'kind': k, 'lot': lt['id'], 'unit': 0.9}, seed=31.0 * i + 5.0)
        elif k == 'quay' and lt['id'] not in USER_REMOVED_LOT_TOPS:        # 23:56 사용자: 포르투스 부두 판석·갓돌(숨김) 삭제
            A = [Acc() for _ in range(7)]
            top_quay(A, M, poly, 0.0, 31.0 * i, 0.9)
            r_ = next((bpy.data.objects.get('DIO_Block_%s_root' % b['id']) for b in blocks if GR.pip(0.5 * (x0 + x1), 0.5 * (y0 + y1), [tuple(p) for p in b['poly']])), None)
            for n_, ac in zip(('L0_x', 'L1_x', 'L2_x', 'L3_QuayPaving', 'L4_Bollards', 'L5_Coping', 'L6_x'), A):
                ac.obj('DIO_Lot_%s_%s' % (lt['id'], n_), GC, r_)
    if spec.get('area'):
        area = [tuple(p) for p in spec['area']]
        ymax = max(p[1] for p in area)
        if spec.get('sea_ext_Y') and spec['sea_ext_Y'] > ymax:              # b7: 하단 띠 밑까지 바다(spec sea_under_bottom_band)
            area = [(x, (spec['sea_ext_Y'] if abs(y - ymax) < 1e-6 else y)) for x, y in area]
        build_water(GC, M, area, blocks)
    warn = []
    if spec.get('roads'):
        _, warn = build_roads(GC, M, spec['roads'], blocks)
    return GC, warn


# ───────────────────────── 블록 종류 시험(diorama_kinds_test.png) — 끝나면 kinds_clear() ─────────────────────────
KIND_TEST = [('ashlar', '아크로폴리스: 성벽 마름돌', 5.0), ('paved', '콜로세움: 자갈 포장 + 흙 단면', 0.0), ('quay', '포르투스: 석축 부두', 0.0),
             ('brick', '트라야누스 시장: 계단식 벽돌 옹벽', 2.0), ('rock', '수도교: 석회암 판 바위 물가', 0.0), ('grass', '하드리아누스: 풀 비탈 + 갈대', 0.0),
             ('mound', '메텔라: 잔돌 흙 둔덕 + 아피아 가도', 0.0), ('riverwall', '마르켈루스: 테베레 강둑 석축', 0.0), ('forum', '막센티우스: 포룸 판석 폐허', 0.0),
             ('plaza', '네로 받침: 판석 마당', 0.0)]


def kinds_test(X0=40.0, Y0=40.0, bw=22.0, bd=16.0, gap=9.0, ncol=5, U=0.9):
    """종류별 블록 10개(2줄 × 5)를 시험 컬렉션에 짓는다. 반환: [(kind, 이름, 블록 윗면 앞 모서리 평면 점, z)]"""
    GC = R.coll('TEST_Kinds', bpy.context.scene.collection)
    R.clear_coll('TEST_Kinds')
    M = mats()
    out = []
    for i, (kind, label, zt) in enumerate(KIND_TEST):
        r_, c_ = divmod(i, ncol)
        x0 = X0 + c_ * (bw + gap); y0 = Y0 + r_ * (bd + gap)
        build_block(GC, M, {'id': 'K_' + kind, 'poly': [(x0, y0), (x0 + bw, y0), (x0 + bw, y0 + bd), (x0, y0 + bd)], 'z': zt, 'kind': kind, 'unit': U}, seed=13.0 * i)
        out.append((kind, label, (x0 + bw, y0 + bd), zt))
    xs = (X0 - gap, X0 + ncol * (bw + gap)); ys = (Y0 - gap, Y0 + 2 * (bd + gap))
    aw = Acc()
    aw.face([V(xs[0], ys[0], WATER_Z), V(xs[1], ys[0], WATER_Z), V(xs[1], ys[1], WATER_Z), V(xs[0], ys[1], WATER_Z)], M['river'], (0, 0, 1))
    aw.obj('K_L0_Water', GC)
    return out


def kinds_clear():
    c = bpy.data.collections.get('TEST_Kinds')
    if c is not None:
        R.clear_coll('TEST_Kinds')
        bpy.data.collections.remove(c)
