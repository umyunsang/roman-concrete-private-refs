# roma_mausoleum — 22:10 사용자: 하드리아누스 영묘를 레퍼런스(buildings/하드리아누스-영묘-다리/user_hadrian_bridge.jpg)대로. 담당: Blender-보완
# 풀 언덕(둔덕) 위 축대 기단(거친 마름돌 옹벽 + 난간 + 앞 계단) → 둥근 받침(3단) → 원형 신전형 영묘:
# 둘레 기둥 회랑(토스카나식 20주) · 원통 내실 · 엔타블러처 고리 · 다락 드럼(작은 네모 창) · 얕은 돔(회청색 납판, 갈빗대) · 꼭대기 작은 등탑.
# 재질은 다리와 같은 풍화된 황토빛 사암·석회암(roma_bridge.M), 돔은 회청색 납판. 축은 X·Y축(앞 계단 = 평면 +X 면). 조명 0, 사람 0.
import bpy, bmesh, math
from mathutils import Vector
import roma_kit as R, roma_flat as FL, roma_geo as G
import roma_bridge as BR

hsh = R.hash01
EXTRA = {'lead': '#8F9AA2', 'lead2': '#A3ADB3', 'lead_rib': '#B8C0C4', 'lead_dk': '#77828A', 'grass': '#A6B565', 'grass2': '#93A456', 'grass3': '#B9C478',
         'cella': '#C7AD84', 'col': '#D9C6A0', 'col2': '#CBB68E', 'win': '#5B4837'}


def mats():
    M = BR.mats()
    for k, hx in EXTRA.items():
        M[k] = FL.flat('F_hm_' + k, hx)
    return M


def build(GC, X0, Y0, z0=0.0, Rp=2.6, pk='HM_Mausoleum', seed=0.0, mound=True):
    """루트 '{pk}_root'(평면 X0, Y0). Rp = 기둥 원 반지름(평면 mm). 반환: 루트"""
    M = mats()
    root = bpy.data.objects.new(pk + '_root', None); GC.objects.link(root)
    Pt = BR.Parts(pk, GC, root)
    B = lambda x, y: (X0 + x, -(Y0 + y))
    # ── 치수
    HB = 1.3; SQ = Rp + 2.5                                   # 축대 높이 · 반변
    zt = z0 + (2.2 if mound else 0.0)                          # 둔덕 위
    zB = zt + HB                                               # 축대 윗면
    Rpod = Rp + 0.9; zP = zB + 0.75                            # 둥근 받침
    Hc = 1.55 * Rp; rc = 0.19                                  # 기둥 높이 · 반지름
    zE0 = zP + Hc; zE1 = zE0 + 0.75                            # 엔타블러처
    Ra = Rp - 0.55; zA1 = zE1 + 0.95                           # 다락 드럼
    Rc = Rp - 0.75                                             # 내실 원통
    b0 = Pt.bm(0, 'Mass', 'stone', 'grass', 'grass2', 'cella', 'lead')
    # ── L0 둔덕(풀, 낮은 원뿔대) · 축대 덩어리 · 둥근 받침 3단 · 내실 원통 · 다락 드럼 · 돔
    if mound:
        G.cyl(b0, X0, -Y0, SQ + 5.0, z0, zt, 40, 1, r_top=SQ + 1.2, top=True, bottom=False)
    fs = G.box(b0, *_bb(B, -SQ, SQ, -SQ, SQ), zt - 0.3, zB, 0)
    fs[1].material_index = 2                                   # 축대 윗면 = 풀(레퍼런스 테라스)
    for k in range(3):
        G.cyl(b0, X0, -Y0, Rpod + (2 - k) * 0.3, zB + k * 0.25, zB + (k + 1) * 0.25, 40, 0, top=True)
    G.cyl(b0, X0, -Y0, Rc, zP, zE1, 40, 3, top=False)
    G.cyl(b0, X0, -Y0, Ra, zE1, zA1, 40, 0, top=True)
    G.dome(b0, X0, -Y0, Ra + 0.12, zA1 + 0.2, 40, 10, 0.0, 4, 0.42)
    G.cyl(b0, X0, -Y0, Ra + 0.18, zA1, zA1 + 0.2, 40, 0, top=False)
    # ── L2 둘레 기둥 20 · 엔타블러처 고리(아키트레이브 · 프리즈 · 코니스) · 다락 처마 · 등탑 · 축대 난간 · 앞 계단
    b2 = Pt.bm(2, 'Members', 'col', 'col2', 'trim', 'stone', 'lead2')
    NC = 20
    for i in range(NC):
        a = 2 * math.pi * (i + 0.5) / NC
        x, y = X0 + Rp * math.cos(a), -Y0 + Rp * math.sin(a)
        G.box(b2, x - rc * 1.35, x + rc * 1.35, y - rc * 1.35, y + rc * 1.35, zP, zP + 0.14, 2)
        fs = G.cyl(b2, x, y, rc, zP + 0.14, zE0 - 0.2, 10, 0, r_top=rc * 0.86, top=False)
        for j, f in enumerate(fs[:10]):
            f.material_index = 0 if j in (0, 1, 2, 7, 8, 9) else 1
        G.cyl(b2, x, y, rc * 0.95, zE0 - 0.2, zE0 - 0.1, 10, 2, r_top=rc * 1.25, top=True)
        G.box(b2, x - rc * 1.3, x + rc * 1.3, y - rc * 1.3, y + rc * 1.3, zE0 - 0.1, zE0, 2)
    G.ring(b2, X0, -Y0, Rc, Rp + 0.28, zE0, zE0 + 0.3, 48, 3)
    G.ring(b2, X0, -Y0, Rc, Rp + 0.24, zE0 + 0.3, zE0 + 0.55, 48, 3)
    G.ring(b2, X0, -Y0, Rc, Rp + 0.48, zE0 + 0.55, zE1, 48, 2)
    G.ring(b2, X0, -Y0, Ra - 0.05, Ra + 0.25, zA1 - 0.15, zA1, 48, 2)
    G.cyl(b2, X0, -Y0, 0.42, zA1 + 0.2 + (Ra + 0.12) * 0.42 - 0.05, zA1 + 0.2 + (Ra + 0.12) * 0.42 + 0.45, 12, 2, top=True)
    G.cyl(b2, X0, -Y0, 0.5, zA1 + 0.2 + (Ra + 0.12) * 0.42 + 0.45, zA1 + 0.2 + (Ra + 0.12) * 0.42 + 0.58, 12, 4, top=True)
    G.cyl(b2, X0, -Y0, 0.28, zA1 + 0.2 + (Ra + 0.12) * 0.42 + 0.58, zA1 + 0.2 + (Ra + 0.12) * 0.42 + 0.95, 12, 4, r_top=0.03, top=True)
    for (x0, x1, y0, y1) in ((SQ - 0.28, SQ, -SQ, SQ), (-SQ, SQ, SQ - 0.28, SQ), (-SQ, -SQ + 0.28, -SQ, SQ), (-SQ, SQ, -SQ, -SQ + 0.28)):   # 난간 받침 · 손잡이
        if x0 > 0 and y0 < 0:                                                  # 앞(+X) 난간은 계단 자리에서 끊는다
            for (ya, yb) in ((-SQ, -1.3), (1.3, SQ)):
                G.box(b2, *_bb(B, x0, x1, ya, yb), zB, zB + 0.1, 2); G.box(b2, *_bb(B, x0 - 0.02, x1 + 0.02, ya, yb), zB + 0.4, zB + 0.5, 2)
        else:
            G.box(b2, *_bb(B, x0, x1, y0, y1), zB, zB + 0.1, 2); G.box(b2, *_bb(B, x0 - 0.02, x1 + 0.02, y0, y1), zB + 0.4, zB + 0.5, 2)
    ns = 7
    for k in range(ns):                                                        # 앞(+X) 계단: 축대 윗면 → 둔덕
        u0 = SQ + k * 0.42
        G.box(b2, *_bb(B, SQ - 0.02, u0 + 0.42, -1.2, 1.2), zt - 0.2, zB - (k + 1) * HB / (ns + 1) + 0.02, 3)
    for sy in (-1.3, 1.3):
        G.box(b2, *_bb(B, SQ - 0.02, SQ + ns * 0.42, sy - 0.14, sy + 0.14), zt - 0.2, zB - 0.1, 2)
    # ── L4 동자 기둥(난간) · 축대 모서리 기둥받침 · 받침 위 단지(장식 단지 대신 빈 받침돌)
    b4 = Pt.bm(4, 'Balusters', 'trim', 'col2')
    for (xa, ya, xb, yb) in ((SQ - 0.14, -SQ, SQ - 0.14, -1.3), (SQ - 0.14, 1.3, SQ - 0.14, SQ), (-SQ, SQ - 0.14, SQ, SQ - 0.14),
                             (-SQ + 0.14, -SQ, -SQ + 0.14, SQ), (-SQ, -SQ + 0.14, SQ, -SQ + 0.14)):
        Ls = math.hypot(xb - xa, yb - ya); n_ = int(Ls / 0.19)
        for q in range(1, n_):
            x = xa + (xb - xa) * q / n_; y = ya + (yb - ya) * q / n_
            G.cyl(b4, X0 + x, -(Y0 + y), 0.05, zB + 0.1, zB + 0.4, 6, q % 2, r_top=0.035, top=False)
    for (x, y) in ((SQ, SQ), (SQ, -SQ), (-SQ, SQ), (-SQ, -SQ), (SQ, 1.3), (SQ, -1.3)):
        G.box(b4, *_bb(B, x - 0.2, x + 0.2, y - 0.2, y + 0.2), zB, zB + 0.62, 0)
    # ── L3 축대 거친 마름돌 켜(보이는 +X · +Y 면) · 돔 납판 갈빗대 · 받침 돌 줄
    b3 = Pt.bm(3, 'Courses', 'stone', 'rust1', 'rust2', 'lead_rib', 'trim')
    for face in ('X', 'Y'):
        z = zt - 0.3; c = 0
        while z < zB - 0.25:
            hc = 0.32 + 0.12 * hsh(c, seed, 91.1); s = -SQ; j = 0
            while s < SQ - 0.1:
                l = 0.5 + 0.6 * hsh(j, c, seed, 91.2); se = min(SQ, s + l)
                if face == 'X':
                    G.box(b3, X0 + SQ, X0 + SQ + 0.05, -(Y0 + se - 0.03), -(Y0 + s + 0.03), z + 0.03, z + hc - 0.03, 1 + (j + c) % 2)
                else:
                    G.box(b3, X0 + s + 0.03, X0 + se - 0.03, -(Y0 + SQ + 0.05), -(Y0 + SQ), z + 0.03, z + hc - 0.03, 1 + (j + c) % 2)
                s = se; j += 1
            z += hc; c += 1
    zd = zA1 + 0.2; Rd = Ra + 0.12
    for i in range(16):                                                        # 돔 갈빗대(보이는 반쪽)
        a = 2 * math.pi * i / 16
        if math.cos(a) - math.sin(a) < -0.4:
            continue
        pts = [(Rd * math.cos(math.pi / 2 * q / 8), zd + Rd * 0.42 * math.sin(math.pi / 2 * q / 8)) for q in range(9)]
        for q in range(8):
            (r0, h0), (r1, h1) = pts[q], pts[q + 1]
            ca, sa = math.cos(a), math.sin(a); w = 0.05
            v = [b3.verts.new((X0 + (r + 0.02) * ca + sx * w * -sa, -Y0 + (r + 0.02) * sa + sx * w * ca, h + 0.02)) for (r, h) in ((r0, h0), (r1, h1)) for sx in (-1, 1)]
            f = b3.faces.new([v[0], v[1], v[3], v[2]]); f.material_index = 3
    # ── L1 기둥 사이 회랑 속 깊이색 · 다락 창 · 축대 문
    b1 = Pt.bm(1, 'Depth', 'win', 'cella')
    G.cyl(b1, X0, -Y0, Rc + 0.02, zP + 0.05, zE0 - 0.3, 40, 1, top=False)
    for i in range(8):
        a = 2 * math.pi * (i + 0.5) / 8
        if math.cos(a) - math.sin(a) < -0.2:
            continue
        x, y = X0 + (Ra + 0.01) * math.cos(a), -Y0 + (Ra + 0.01) * math.sin(a)
        tx, ty = -math.sin(a), math.cos(a)
        zc = 0.5 * (zE1 + zA1)
        v = [b1.verts.new((x + tx * s * 0.22 + math.cos(a) * 0.02, y + ty * s * 0.22 + math.sin(a) * 0.02, zc + h)) for s, h in ((-1, -0.25), (1, -0.25), (1, 0.25), (-1, 0.25))]
        f = b1.faces.new(v); f.material_index = 0
    G.box(b1, *_bb(B, Rc - 0.1, Rc + 0.05, -0.35, 0.35), zP, zP + 1.6, 0)
    # ── L5 하이라이트(코니스 윗선 · 받침 단 윗선 · 돔 밝은 쪽)
    b5 = Pt.bm(5, 'Highlights', 'hi', 'lead_rib')
    G.ring(b5, X0, -Y0, Rp + 0.4, Rp + 0.5, zE1 - 0.03, zE1 + 0.005, 48, 0, -145.0, 55.0)
    for k in range(3):
        G.ring(b5, X0, -Y0, Rpod + (2 - k) * 0.3 - 0.06, Rpod + (2 - k) * 0.3 + 0.005, zB + (k + 1) * 0.25 - 0.04, zB + (k + 1) * 0.25 + 0.004, 48, 0, -145.0, 55.0)
    G.box(b5, *_bb(B, SQ - 0.3, SQ + 0.03, -SQ, -1.3), zB + 0.5, zB + 0.515, 0)
    # ── L6 2단 얼룩(엔타블러처 밑 물때 · 축대 황토) · 축대 발치 이끼 · 둔덕 풀결
    b6 = Pt.bm(6, 'Weather', 'stain1', 'stain2', 'moss', 'grass3', 'grass2')
    for j in range(18):
        a = math.radians(-145.0 + 200.0 * hsh(j, seed, 92.1))
        r = Rc + 0.02
        x, y = X0 + r * math.cos(a), -Y0 + r * math.sin(a)
        tx, ty = -math.sin(a), math.cos(a); w = 0.12 + 0.2 * hsh(j, 92.2); L_ = 0.6 + 1.6 * hsh(j, 92.3)
        v = [b6.verts.new((x + tx * s * w + math.cos(a) * 0.015, y + ty * s * w + math.sin(a) * 0.015, zE0 - 0.32 - h)) for s, h in ((-1, 0.0), (1, 0.0), (0.6, L_), (-0.4, L_ * 0.8))]
        f = b6.faces.new(v); f.material_index = j % 2
    for j in range(14):
        s = -SQ + 2 * SQ * hsh(j, seed, 92.4); w = 0.3 + 0.6 * hsh(j, 92.5); L_ = 0.3 + 0.8 * hsh(j, 92.6)
        G.box(b6, X0 + SQ + 0.05, X0 + SQ + 0.07, -(Y0 + s + w), -(Y0 + s), zB - 0.12 - L_, zB - 0.12, j % 2)
        G.box(b6, X0 + s, X0 + s + w, -(Y0 + SQ + 0.07), -(Y0 + SQ + 0.05), zt - 0.3, zt + 0.15 + 0.3 * hsh(j, 92.7), 2)
    if mound:
        for j in range(40):
            a = 2 * math.pi * hsh(j, seed, 92.8); t = hsh(j, 92.9)
            r = (SQ + 1.2) + 3.8 * t; z = zt - (zt - z0) * t
            x, y = X0 + r * math.cos(a), -Y0 + r * math.sin(a)
            if math.cos(a) - math.sin(a) < -0.3:
                continue
            G.cyl(b6, x, y, 0.25 + 0.3 * hsh(j, 93.1), z, z + 0.12, 6, 3 + j % 2, r_top=0.2, top=True)
    Pt.done()
    return root, dict(zB=zB, zt=zt, SQ=SQ, top=zA1 + 0.2 + (Ra + 0.12) * 0.42 + 0.95)


def _bb(B, x0, x1, y0, y1):
    """평면 상자(X0 기준 x0~x1, Y0 기준 y0~y1) → Blender G.box 인자(x0, x1, yb0, yb1)"""
    (ax, ay), (bx_, by) = B(x0, y0), B(x1, y1)
    return min(ax, bx_), max(ax, bx_), min(ay, by), max(ay, by)


# ───────────────────────── 시험: 레퍼런스 구도(물 위 다리가 앞, 언덕 위 영묘가 뒤) ─────────────────────────
def test_scene(X0=150.0, Y0=110.0, W=12.0, z_w=-3.0):
    import roma_diorama as DI, roma_pkg_ground as GR
    GC = R.coll(BR.TEST_COLL, bpy.context.scene.collection)
    R.clear_coll(BR.TEST_COLL)
    DM = DI.mats()
    keep = DI.WATER_Z
    DI.WATER_Z = z_w
    h = W / 2.0
    try:
        DI.build_block(GC, DM, {'id': 'TH_N', 'poly': [(X0 - 22.0, Y0 - h - 20.0), (X0 + 14.0, Y0 - h - 20.0), (X0 + 14.0, Y0 - h), (X0 - 22.0, Y0 - h)], 'z': 0.0,
                                'kind': 'grass', 'unit': 0.6}, seed=3.0)
        DI.build_block(GC, DM, {'id': 'TH_S', 'poly': [(X0 - 22.0, Y0 + h), (X0 + 14.0, Y0 + h), (X0 + 14.0, Y0 + h + 10.0), (X0 - 22.0, Y0 + h + 10.0)], 'z': 0.0,
                                'kind': 'grass', 'unit': 0.6}, seed=9.0)
    finally:
        DI.WATER_Z = keep
    L = BR.layout(W, z_w, 0.0)
    wp = [(X0 - 22.0, Y0 - h), (X0 + 14.0, Y0 - h), (X0 + 14.0, Y0 + h), (X0 - 22.0, Y0 + h)]
    aw = GR.Acc()
    aw.face([GR.V(x, y, z_w) for x, y in wp], BR.mats()['water'], (0, 0, 1))
    aw.obj('TH_L0_Water', GC)
    ar = GR.Acc()
    ar.box(X0 - L['BW'] / 2 - 0.4, X0 + L['BW'] / 2 + 0.4, Y0 + L['Ye'] + 1.5, Y0 + h + 10.0, 0.0, 0.03, DM['slab'], DM['slab_side'])
    ar.box(X0 - L['BW'] / 2 - 0.4, X0 + L['BW'] / 2 + 0.4, Y0 - h - 9.0, Y0 - L['Ye'] - 1.5, 0.0, 0.03, DM['slab'], DM['slab_side'])
    ar.obj('TH_L3_Road', GC)
    BR.build(GC, X0, Y0, L, 'TH_Bridge', wp)
    mroot, info = build(GC, X0 - 12.0, Y0 - h - 12.0, 0.0, 2.0, 'TH_Mausoleum')
    return GC, L, info


# ───────────────────────── d7 spec(L8 plan)로 짓기: 평면 좌표 그대로(정면 = 평면 +Y, 다리 쪽) ─────────────────────────
MOUND = False


def build_spec(GC, P, pk='COAST_HadrianMausoleum'):
    """P = spec L8 plan(base · drum · top · steps). 반환: (루트, 정보). 루트는 원점(회전 0), 기하는 평면 절대 좌표"""
    M = mats()
    root = bpy.data.objects.new(pk + '_root', None); GC.objects.link(root)
    Pt = BR.Parts(pk, GC, root)
    b, d, tp, st = P['base'], P['drum'], P['top'], P.get('steps', {})
    (X0b, X1b), (Y0b, Y1b) = b['X'], b['Y']
    cx, cy = d['c']; Rp = float(d['r'])
    zB = float(b['h']); zt = float(st.get('bottom_z', 3.0))                      # 축대 윗면 · 둔덕 윗면
    SQ = 13.0 if not st else (st['Y'][0] - cy)                                     # 축대 반변(디딤 시작 = 축대 앞 변)
    MT = SQ + 4.0                                                                  # 둔덕 윗면 반변
    zE1 = float(d['z'][1]); zPar0 = float(tp['parapet']['z'][0])
    Rd = float(tp['mound']['r_max']); zD1 = float(tp['mound']['z_top'])
    NC = 20; rc = 0.58                                                             # 23:20 사용자: 세부는 내 모델(기둥 20) — d7은 배치만
    zP = zB + 0.5; zE0 = zPar0 - 1.2
    Rc = Rp - 3.0
    V3 = lambda x, y, z: (x, -y, z)
    bb = lambda x0, x1, y0, y1: (x0, x1, -y1, -y0)
    # ── L0 둔덕(정사각 뿔대, 풀) · 축대 · 받침 2단 · 내실 · 패러핏 위 납판 고리 · 돔
    b0 = Pt.bm(0, 'Mass', 'stone', 'grass', 'grass2', 'cella', 'lead')
    if MOUND:                                                                      # 23:43: b7은 블록 B의 땅(지형 특징)이 둔덕을 맡는다
        lo = [b0.verts.new(V3(x, y, 0.0)) for x, y in ((X0b, Y0b), (X1b, Y0b), (X1b, Y1b), (X0b, Y1b))]
        hi = [b0.verts.new(V3(x, y, zt)) for x, y in ((cx - MT, cy - MT), (cx + MT, cy - MT), (cx + MT, cy + MT), (cx - MT, cy + MT))]
        for i in range(4):
            j = (i + 1) % 4
            f = b0.faces.new([lo[i], lo[j], hi[j], hi[i]]); f.material_index = 1 + i % 2
        f = b0.faces.new(hi); f.material_index = 1
    fs = G.box(b0, *bb(cx - SQ, cx + SQ, cy - SQ, cy + SQ), zt - 0.3, zB, 0)
    fs[1].material_index = 2
    for k in range(2):
        G.cyl(b0, cx, -cy, Rp + 0.9 - 0.35 * k, zB + 0.25 * k, zB + 0.25 * (k + 1), 48, 0, top=True)
    G.cyl(b0, cx, -cy, Rc, zP, zPar0, 48, 3, top=False)
    G.ring(b0, cx, -cy, Rd - 0.1, Rp + 0.3, zE1 - 0.05, zE1 + 0.15, 48, 4)
    G.dome(b0, cx, -cy, Rd, zE1, 48, 12, 0.0, 4, (zD1 - zE1) / Rd)
    # ── L2 기둥 18 · 엔타블러처 · 패러핏 · 등롱 · 축대 난간 받침/손잡이 · 앞(+Y) 디딤 2단 · 진입 경사
    b2 = Pt.bm(2, 'Members', 'col', 'col2', 'trim', 'stone', 'lead2')
    for i in range(NC):
        a = 2 * math.pi * (i + 0.5) / NC
        x, y = cx + Rp * math.cos(a), -cy + Rp * math.sin(a)
        G.box(b2, x - rc * 1.35, x + rc * 1.35, y - rc * 1.35, y + rc * 1.35, zP, zP + 0.4, 2)
        fs = G.cyl(b2, x, y, rc, zP + 0.4, zE0 - 0.5, 12, 0, r_top=rc * 0.86, top=False)
        for j, f in enumerate(fs[:12]):
            f.material_index = 0 if j in (0, 1, 2, 9, 10, 11) else 1
        G.cyl(b2, x, y, rc * 0.95, zE0 - 0.5, zE0 - 0.25, 12, 2, r_top=rc * 1.3, top=True)
        G.box(b2, x - rc * 1.35, x + rc * 1.35, y - rc * 1.35, y + rc * 1.35, zE0 - 0.25, zE0, 2)
    G.ring(b2, cx, -cy, Rc, Rp + 0.75, zE0, zE0 + 0.45, 60, 3)
    G.ring(b2, cx, -cy, Rc, Rp + 0.7, zE0 + 0.45, zE0 + 0.9, 60, 3)
    G.ring(b2, cx, -cy, Rc, Rp + 1.05, zE0 + 0.9, zPar0, 60, 2)
    G.ring(b2, cx, -cy, Rp - 0.4, Rp + 0.3, zPar0, zE1, 60, 3)
    G.ring(b2, cx, -cy, Rp - 0.45, Rp + 0.45, zE1 - 0.15, zE1, 60, 2)
    G.cyl(b2, cx, -cy, 1.0, zD1 - 0.1, zD1 + 0.6, 12, 2, top=True)
    G.cyl(b2, cx, -cy, 1.2, zD1 + 0.6, zD1 + 0.75, 12, 4, top=True)
    G.cyl(b2, cx, -cy, 0.7, zD1 + 0.75, zD1 + 1.3, 12, 4, r_top=0.05, top=True)
    sx0, sx1 = st.get('X', [cx - 3.5, cx + 3.5])
    for (x0, x1, y0, y1) in ((cx - SQ, cx + SQ, cy - SQ, cy - SQ + 0.5), (cx - SQ, cx - SQ + 0.5, cy - SQ, cy + SQ), (cx + SQ - 0.5, cx + SQ, cy - SQ, cy + SQ),
                             (cx - SQ, sx0, cy + SQ - 0.5, cy + SQ), (sx1, cx + SQ, cy + SQ - 0.5, cy + SQ)):
        G.box(b2, *bb(x0, x1, y0, y1), zB, zB + 0.2, 2)
        G.box(b2, *bb(x0 - 0.05, x1 + 0.05, y0 - 0.05, y1 + 0.05), zB + 0.75, zB + 0.95, 2)
    for tr in st.get('treads', [{'Y': [cy + SQ + 2.0, cy + SQ + 4.0], 'z': zt + 0.67}, {'Y': [cy + SQ, cy + SQ + 2.0], 'z': zt + 1.33}]):
        G.box(b2, *bb(sx0, sx1, tr['Y'][0], tr['Y'][1]), zt - 0.2, tr['z'], 3)
    for x in (sx0 - 0.4, sx1 + 0.4):
        G.box(b2, *bb(x - 0.4, x + 0.4, cy + SQ, cy + SQ + 4.0), zt - 0.2, zB + 0.2, 2)
    yr0, yr1 = cy + MT, Y1b                                                        # 둔덕 앞 비탈의 진입 경사(다리 북쪽 끝 z 0 → 둔덕 윗면 z 3)
    ram = [b2.verts.new(V3(x, y, z)) for x, y, z in ((sx0, yr1, 0.02), (sx1, yr1, 0.02), (sx1, yr0, zt + 0.02), (sx0, yr0, zt + 0.02))]
    f = b2.faces.new(ram); f.material_index = 3
    # ── L4 동자 기둥 · 모서리 기둥받침 · 패러핏 무늬 판
    b4 = Pt.bm(4, 'Balusters', 'trim', 'col2')
    for (xa, ya, xb, yb) in ((cx - SQ + 0.25, cy - SQ + 0.25, cx + SQ - 0.25, cy - SQ + 0.25), (cx - SQ + 0.25, cy - SQ + 0.25, cx - SQ + 0.25, cy + SQ - 0.25),
                             (cx + SQ - 0.25, cy - SQ + 0.25, cx + SQ - 0.25, cy + SQ - 0.25), (cx - SQ + 0.25, cy + SQ - 0.25, sx0, cy + SQ - 0.25),
                             (sx1, cy + SQ - 0.25, cx + SQ - 0.25, cy + SQ - 0.25)):
        Ls = math.hypot(xb - xa, yb - ya); n_ = max(2, int(Ls / 0.45))
        for q in range(1, n_):
            x = xa + (xb - xa) * q / n_; y = ya + (yb - ya) * q / n_
            G.cyl(b4, x, -y, 0.13, zB + 0.2, zB + 0.75, 6, q % 2, r_top=0.09, top=False)
    for (x, y) in ((cx - SQ, cy - SQ), (cx + SQ, cy - SQ), (cx - SQ, cy + SQ), (cx + SQ, cy + SQ), (sx0, cy + SQ), (sx1, cy + SQ)):
        G.box(b4, *bb(x - 0.45, x + 0.45, y - 0.45, y + 0.45), zB, zB + 1.2, 0)
    for i in range(36):                                                             # 패러핏 판 무늬(보이는 반)
        a = 2 * math.pi * (i + 0.5) / 36
        if math.cos(a) - math.sin(a) < -0.3:
            continue
        x, y = cx + (Rp + 0.31) * math.cos(a), -cy + (Rp + 0.31) * math.sin(a)
        tx, ty = -math.sin(a), math.cos(a)
        v = [b4.verts.new((x + tx * s * 0.6 + math.cos(a) * 0.02, y + ty * s * 0.6 + math.sin(a) * 0.02, zPar0 + h)) for s, h in ((-1, 0.3), (1, 0.3), (1, 1.2), (-1, 1.2))]
        f = b4.faces.new(v); f.material_index = 1
    # ── L3 축대 거친 마름돌 켜(보이는 +X · +Y 면) · 돔 갈빗대 · 받침 돌 줄
    b3 = Pt.bm(3, 'Courses', 'stone', 'rust1', 'rust2', 'lead_rib', 'trim')
    for face in ('X', 'Y'):
        z = zt - 0.3; c = 0
        while z < zB - 0.2:
            hc = 0.5 + 0.2 * hsh(c, 91.1); s = -SQ; j = 0
            while s < SQ - 0.1:
                l = 1.0 + 1.2 * hsh(j, c, 91.2); se = min(SQ, s + l)
                if face == 'X':
                    G.box(b3, cx + SQ, cx + SQ + 0.06, -(cy + se - 0.05), -(cy + s + 0.05), z + 0.05, min(zB, z + hc) - 0.05, 1 + (j + c) % 2)
                elif not (sx0 - 0.9 < cx + s < sx1 + 0.9 or sx0 - 0.9 < cx + se < sx1 + 0.9):
                    G.box(b3, cx + s + 0.05, cx + se - 0.05, -(cy + SQ + 0.06), -(cy + SQ), z + 0.05, min(zB, z + hc) - 0.05, 1 + (j + c) % 2)
                s = se; j += 1
            z += hc; c += 1
    hk = (zD1 - zE1) / Rd
    for i in range(20):
        a = 2 * math.pi * i / 20
        if math.cos(a) - math.sin(a) < -0.4:
            continue
        pts = [(Rd * math.cos(math.pi / 2 * q / 10), zE1 + Rd * hk * math.sin(math.pi / 2 * q / 10)) for q in range(11)]
        ca, sa = math.cos(a), math.sin(a); w = 0.16
        for q in range(10):
            (r0, h0), (r1, h1) = pts[q], pts[q + 1]
            v = [b3.verts.new((cx + (r + 0.05) * ca + sx_ * w * -sa, -cy + (r + 0.05) * sa + sx_ * w * ca, h + 0.05)) for (r, h) in ((r0, h0), (r1, h1)) for sx_ in (-1, 1)]
            f = b3.faces.new([v[0], v[1], v[3], v[2]]); f.material_index = 3
    # ── L1 회랑 속 깊이색 · 내실 문 · 둔덕 비탈 그늘 띠
    b1 = Pt.bm(1, 'Depth', 'win', 'cella')
    G.cyl(b1, cx, -cy, Rc + 0.03, zP + 0.1, zE0 - 0.6, 48, 1, top=False)
    G.box(b1, *bb(cx - 1.1, cx + 1.1, cy + Rc - 0.2, cy + Rc + 0.05), zP, zP + 4.2, 0)
    # ── L5 하이라이트(코니스 · 받침 단 · 축대 난간 윗선 · 돔 밝은 쪽 띠)
    b5 = Pt.bm(5, 'Highlights', 'hi', 'lead_rib')
    G.ring(b5, cx, -cy, Rp + 0.95, Rp + 1.1, zPar0 - 0.06, zPar0 + 0.005, 60, 0, -145.0, 55.0)
    for k in range(2):
        G.ring(b5, cx, -cy, Rp + 0.9 - 0.35 * k - 0.12, Rp + 0.9 - 0.35 * k + 0.005, zB + 0.25 * (k + 1) - 0.05, zB + 0.25 * (k + 1) + 0.004, 60, 0, -145.0, 55.0)
    G.box(b5, *bb(cx + SQ - 0.5, cx + SQ + 0.06, cy - SQ, cy + SQ), zB + 0.95, zB + 0.97, 0)
    # ── L6 2단 얼룩(엔타블러처 밑 물때 · 축대 황토) · 발치 이끼 · 둔덕 풀결
    b6 = Pt.bm(6, 'Weather', 'stain1', 'stain2', 'moss', 'grass3', 'grass2')
    for j in range(26):
        a = math.radians(-145.0 + 200.0 * hsh(j, 92.1))
        r = Rc + 0.04
        x, y = cx + r * math.cos(a), -cy + r * math.sin(a)
        tx, ty = -math.sin(a), math.cos(a); w = 0.4 + 0.6 * hsh(j, 92.2); L_ = 1.5 + 4.0 * hsh(j, 92.3)
        v = [b6.verts.new((x + tx * s * w + math.cos(a) * 0.02, y + ty * s * w + math.sin(a) * 0.02, zE0 - 0.7 - h)) for s, h in ((-1, 0.0), (1, 0.0), (0.6, L_), (-0.4, L_ * 0.8))]
        f = b6.faces.new(v); f.material_index = j % 2
    for j in range(22):
        s = -SQ + 2 * SQ * hsh(j, 92.4); w = 0.8 + 1.4 * hsh(j, 92.5); L_ = 0.4 + 1.0 * hsh(j, 92.6)
        G.box(b6, cx + SQ + 0.06, cx + SQ + 0.09, -(cy + s + w), -(cy + s), zB - 0.2 - L_, zB - 0.2, j % 2)
        G.box(b6, cx + s, cx + s + w, -(cy + SQ + 0.09), -(cy + SQ + 0.06), zt - 0.3, zt + 0.2 + 0.4 * hsh(j, 92.7), 2)
    for j in range(70 if MOUND else 0):                                              # 둔덕 비탈 풀결(보이는 +X · +Y 비탈)
        t = hsh(j, 92.8); u = -1 + 2 * hsh(j, 92.9); side = j % 2
        if side == 0:
            x = cx + MT + (X1b - (cx + MT)) * t; y = cy + u * (MT + (Y1b - cy - MT) * t)
        else:
            y = cy + MT + (Y1b - (cy + MT)) * t; x = cx + u * (MT + (X1b - cx - MT) * t)
        z = zt * (1.0 - t)
        G.cyl(b6, x, -y, 0.5 + 0.6 * hsh(j, 93.1), z, z + 0.15, 6, 3 + j % 2, r_top=0.4, top=True)
    # ── 23:51 사용자: 콜로세움 수준으로 표현 층 누적(레퍼런스 Castle Howard 영묘)
    vis = lambda a_: math.cos(a_) - math.sin(a_) > -0.35
    b1x = Pt.bm(1, 'Niches', 'win', 'cella')
    b2x = Pt.bm(2, 'Dentils', 'trim', 'col2', 'stone')
    b3x = Pt.bm(3, 'Joints', 'lead_rib', 'stone', 'rust1')
    b4x = Pt.bm(4, 'Mouldings', 'trim', 'col2')
    b5x = Pt.bm(5, 'ColLight', 'hi', 'lead_rib')
    b6x = Pt.bm(6, 'Stains', 'stain1', 'stain2', 'moss', 'grass2')
    hc = zE0 - zP
    for i in range(NC):
        a_ = 2 * math.pi * (i + 0.5) / NC
        x, y = cx + Rp * math.cos(a_), -cy + Rp * math.sin(a_)
        am = 2 * math.pi * (i + 1.0) / NC                                       # 기둥 사이 내실 벽감(아치 머리, 짙게)
        if vis(am):
            nx_, ny_ = math.cos(am), math.sin(am); tx_, ty_ = -ny_, nx_
            rr = Rc + 0.03; xc, yc = cx + rr * nx_, -cy + rr * ny_
            wn, z0n, z1n = 0.9, zP + 1.2, zP + 0.62 * hc
            pts = [(-wn, z0n), (wn, z0n), (wn, z1n)] + [(wn * math.cos(math.pi * k / 8), z1n + wn * math.sin(math.pi * k / 8)) for k in range(1, 8)] + [(-wn, z1n)]
            f = b1x.faces.new([b1x.verts.new((xc + tx_ * u + nx_ * 0.01, yc + ty_ * u + ny_ * 0.01, z)) for u, z in pts]); f.material_index = 0
            f = b4x.faces.new([b4x.verts.new((xc + tx_ * u + nx_ * 0.04, yc + ty_ * u + ny_ * 0.04, z)) for u, z in ((-wn - 0.25, z0n - 0.25), (wn + 0.25, z0n - 0.25), (wn + 0.25, z0n), (-wn - 0.25, z0n))]); f.material_index = 0
        if not vis(a_):
            continue
        rz = lambda z: rc + (rc * 0.86 - rc) * (z - zP - 0.4) / max(1e-6, hc - 0.9)
        z = zP + 1.0                                                            # 기둥 북 이음매(보이는 반 바퀴)
        while z < zE0 - 0.8:
            G.ring(b3x, x, y, rz(z) - 0.01, rz(z) + 0.03, z - 0.04, z + 0.04, 6, 1, -145.0, 55.0)
            z += 1.05
        vx, vy = math.cos(math.radians(-105.0)), math.sin(math.radians(-105.0)); tx_, ty_ = -vy, vx
        v = [b5x.verts.new((x + vx * (rz(zz) + 0.03) + tx_ * u, y + vy * (rz(zz) + 0.03) + ty_ * u, zz)) for zz, u in ((zP + 0.6, -0.09), (zP + 0.6, 0.09), (zE0 - 0.6, 0.09), (zE0 - 0.6, -0.09))]
        f = b5x.faces.new(v); f.material_index = 0
        for j in range(2):                                                     # 2단 얼룩
            ph = math.radians(-125.0 + 150.0 * hsh(i, j, 95.1)); px, py = math.cos(ph), math.sin(ph); qx, qy = -py, px
            zc = zP + 1.0 + (hc - 3.0) * hsh(i, j, 95.2); hh = 0.8 + 1.8 * hsh(i, j, 95.3); w = 0.14 + 0.16 * hsh(i, j, 95.4)
            v = [b6x.verts.new((x + px * (rz(zz) + 0.045) + qx * u, y + py * (rz(zz) + 0.045) + qy * u, zz)) for zz, u in ((zc, -w), (zc + 0.1, w), (zc + hh, w * 0.6), (zc + hh * 0.9, -w * 0.5))]
            f = b6x.faces.new(v); f.material_index = j
    for k in range(72):                                                         # 코니스 밑 까치발(덴틸) 고리 · 다락 벽기둥
        a_ = 2 * math.pi * (k + 0.5) / 72
        if not vis(a_):
            continue
        r0 = Rp + 0.62; x, y = cx + r0 * math.cos(a_), -cy + r0 * math.sin(a_)
        G.box(b2x, x - 0.16, x + 0.16, y - 0.16, y + 0.16, zE0 + 0.9 - 0.32, zE0 + 0.9 - 0.05, 0)
        if k % 4 == 0:
            r1 = Rp + 0.3; x1, y1 = cx + r1 * math.cos(a_), -cy + r1 * math.sin(a_)
            G.box(b2x, x1 - 0.22, x1 + 0.22, y1 - 0.22, y1 + 0.22, zPar0, zE1 - 0.2, 1)
    for zz in [zP + 0.6 + 0.62 * q for q in range(int((zPar0 - zP - 1.0) / 0.62))]:   # 내실 벽 켜(보이는 반)
        G.ring(b3x, cx, -cy, Rc - 0.005, Rc + 0.02, zz, zz + 0.05, 24, 1, -145.0, 55.0)
    for q in range(1, 6):                                                       # 돔 납판 가로 이음
        t_ = q / 6.0; r_ = Rd * math.cos(math.pi / 2 * t_); z_ = zE1 + Rd * ((zD1 - zE1) / Rd) * math.sin(math.pi / 2 * t_)
        G.ring(b3x, cx, -cy, r_ - 0.02, r_ + 0.06, z_ - 0.05, z_ + 0.04, 30, 0, -145.0, 55.0)
    for j in range(16):                                                         # 돔 이끼·얼룩 · 받침 이끼
        a_ = math.radians(-140.0 + 190.0 * hsh(j, 96.1)); t_ = 0.15 + 0.6 * hsh(j, 96.2)
        r_ = Rd * math.cos(math.pi / 2 * t_) + 0.08; z_ = zE1 + (zD1 - zE1) * math.sin(math.pi / 2 * t_)
        G.box(b6x, cx + r_ * math.cos(a_) - 0.35, cx + r_ * math.cos(a_) + 0.35, -cy + r_ * math.sin(a_) - 0.25, -cy + r_ * math.sin(a_) + 0.25, z_ - 0.05, z_ + 0.08, 2 + j % 2)
        G.ring(b6x, cx, -cy, Rp + 0.85, Rp + 0.95, zB + 0.02, zB + 0.12 + 0.1 * hsh(j, 96.3), 3, 2, math.degrees(a_) - 4, math.degrees(a_) + 4)
    Pt.done()
    return root, dict(zB=zB, zt=zt, SQ=SQ, MT=MT, top=zD1 + 1.3)
