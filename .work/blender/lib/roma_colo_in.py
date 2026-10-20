
# roma_colo_in — 콜로세움 내부(관람석·경기장·하이포게움). L0 덩어리 층
import bpy, bmesh, math
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
import roma_kit as R, roma_colo as C

D3A, D3B = 9.2, 10.4          # 셋째 고리벽
DC0, DC1 = 10.4, 22.7         # 관람석(바깥 → 안)
DP0, DP1 = 22.7, 23.9         # 포디움 벽
ZC_TOP, ZC_BOT = 24.0, 4.4    # 관람석 윗선·아랫선 높이
Z_FLOOR, Z_PIT = 0.6, -4.0
U_SPLIT = -2.0                # 나무 바닥 경계(경기장 장축 좌표, 오른쪽이 바닥)

def zc(d):
    return ZC_BOT + (DC1 - d) / (DC1 - DC0) * (ZC_TOP - ZC_BOT)

def prism_x(bm, prof, x0, x1):
    """(y,z) 단면을 x0~x1로 밀어낸 닫힌 입체(오목 단면 가능)"""
    tris = tessellate_polygon([[(p[0], p[1], 0.0) for p in prof]])
    a = [bm.verts.new((x0, y, z)) for y, z in prof]
    b = [bm.verts.new((x1, y, z)) for y, z in prof]
    for t in tris:
        try: bm.faces.new([a[t[2]], a[t[1]], a[t[0]]])
        except ValueError: pass
        try: bm.faces.new([b[t[0]], b[t[1]], b[t[2]]])
        except ValueError: pass
    n = len(prof)
    for k in range(n):
        try: bm.faces.new([a[k], a[(k+1)%n], b[(k+1)%n], b[k]])
        except ValueError: pass

def seat_sector(th):
    th %= 360.0
    return (238.0 <= th < 360.0) or (th < 48.0)

def build(HC, root, F):
    W = C.W
    sub, seats, fins, rings, deep = C.Acc(), C.Acc(), C.Acc(), C.Acc(), C.Acc()
    caps = C.Acc()          # L5 하이라이트: 방사벽 갓돌 · 포디움 난간 윗선
    for i in range(C.NB):
        sc = (i + 0.5) * W
        th = C.E.az(sc)
        H2 = C.h2(th, i)
        ztop = min(ZC_TOP, H2 - 9.0) if not (100.0 <= th % 360 < 209.0) else ZC_TOP
        ztop = max(ztop, 12.0)
        if 8.0 <= th % 360 < 82.0:
            ztop = 6.0                     # 정면: 관람석이 무너져 경기장이 보인다
        k = (ztop - ZC_BOT) / (ZC_TOP - ZC_BOT)
        def zt(d): return ZC_BOT + (DC1 - d) / (DC1 - DC0) * (ztop - ZC_BOT)
        # 셋째 고리벽(출입구 아치) — 높이 ztop+1.5
        bm = C.bay_panel(0.0, ztop + 1.5, 0.0, min(ztop - 3.0, 9.0), D3B - D3A, w=W, ra=W * 0.22)
        bm.verts.index_update(); rings.add_bm(bm, sc, D3A, 0); bm.free()
        # 관람석 세 띠: 위(10.4~15.5) 볼트 무너짐 → 짙은 빈칸, 가운데(15.5~19.5) 볼트 군데군데, 아래(19.5~22.7) 계단석
        DU, DM = 15.5, 19.5
        r_ = C.rnd(i, 21)
        # 위 띠: 짙은 빈칸 바닥(볼트 밑) + 띠 끝 낮은 벽(발테우스)
        prof = [(0.0, zt(DC0) - 5.0), (DU - DC0, zt(DU) - 5.0), (DU - DC0, zt(DU) - 4.4), (0.0, zt(DC0) - 4.4)]
        bm = bmesh.new(); prism_x(bm, prof, -W / 2, W / 2); bm.verts.index_update(); deep.add_bm(bm, sc, DC0, 0); bm.free()
        if r_ > 0.72:      # 몇 칸은 위 띠 볼트가 남아 있다
            prof = [(0.0, zt(DC0) - 0.8), (DU - DC0, zt(DU) - 0.8), (DU - DC0, zt(DU)), (0.0, zt(DC0))]
            bm = bmesh.new(); prism_x(bm, prof, -W / 2, W / 2); bm.verts.index_update(); sub.add_bm(bm, sc, DC0, 0); bm.free()
        bm = bmesh.new(); C.box(bm, -W / 2, W / 2, DU - DC0 - 0.5, DU - DC0, zt(DU) - 4.5, zt(DU) + 0.9); bm.verts.index_update(); rings.add_bm(bm, sc, DC0, 1); bm.free()
        # 가운데 띠: 볼트(60%), 없으면 짙은 빈칸
        if C.rnd(i, 22) > 0.4 or seat_sector(th):
            prof = [(0.0, zt(DU) - 0.8), (DM - DU, zt(DM) - 0.8), (DM - DU, zt(DM)), (0.0, zt(DU))]
            bm = bmesh.new(); prism_x(bm, prof, -W / 2, W / 2); bm.verts.index_update(); sub.add_bm(bm, sc, DU, 0); bm.free()
        else:
            prof = [(0.0, zt(DU) - 4.0), (DM - DU, zt(DM) - 4.0), (DM - DU, zt(DM) - 3.4), (0.0, zt(DU) - 3.4)]
            bm = bmesh.new(); prism_x(bm, prof, -W / 2, W / 2); bm.verts.index_update(); deep.add_bm(bm, sc, DU, 0); bm.free()
        # 아래 띠: 계단석(모든 구역) — 남은 구역은 위·가운데 띠까지 계단석
        d_from = DC0 + 1.0 if seat_sector(th) else DM
        nst = int(round((DC1 - d_from) / 0.56))
        prof = []
        for j in range(nst):
            d0 = d_from + j * (DC1 - d_from) / nst; d1 = d_from + (j + 1) * (DC1 - d_from) / nst
            z = zt(d0)
            prof += [(d0 - DC0, z + 0.06), (d1 - DC0, z + 0.06)]
        prof = prof + [(DC1 - DC0, ZC_BOT - 0.3), (d_from - DC0, ZC_BOT - 0.3)]
        bm = bmesh.new(); prism_x(bm, prof, -W / 2 + 0.45, W / 2 - 0.45); bm.verts.index_update(); seats.add_bm(bm, sc, DC0, 0); bm.free()
        for dd in ((3.0, 6.2, 9.4) if seat_sector(th) else (DM - DC0 + 1.4,)):
            if DC0 + dd < d_from: continue
            bm = bmesh.new(); z = zt(DC0 + dd)
            C.box(bm, -W / 2, W / 2, dd - 0.35, dd + 0.15, z - 0.3, z + 1.1); bm.verts.index_update(); seats.add_bm(bm, sc, DC0, 1); bm.free()
        # 방사벽(칸 경계): 두껍고 높게, 윗선 2단, 아래 통로 아치
        Lf = DC1 - DC0 - 1.2
        hi = 2.6 if not seat_sector(th) else 1.6
        zA, zB = zt(DC0) + hi, zt(DC1 - 1.2) + hi * 0.6
        prof = [(0.0, 0.0), (Lf, 0.0), (Lf, zB), (Lf * 0.55, zB + (zA - zB) * 0.45), (Lf * 0.55, zB + (zA - zB) * 0.45 + 0.9), (0.0, zA)]
        ym, aw = (DU - DC0) * 0.5, 2.0
        ah = min(zt(DC0 + ym) - 5.6, 6.0)
        if ah > 1.8:
            arc = [(ym + aw / 2 * math.cos(math.pi * k / 10), ah - aw / 2 + aw / 2 * math.sin(math.pi * k / 10)) for k in range(11)]
            prof = [(0.0, 0.0), (ym - aw / 2, 0.0), (ym - aw / 2, ah - aw / 2)] + arc[::-1][1:-1] + [(ym + aw / 2, ah - aw / 2), (ym + aw / 2, 0.0)] + prof[1:]
        bm = bmesh.new(); prism_x(bm, prof, -W / 2 - 0.5, -W / 2 + 0.5); bm.verts.index_update(); fins.add_bm(bm, sc, DC0, 0); bm.free()
        # 방사벽 윗면 밝은 갓돌(L5 하이라이트 층): 비탈진 두 윗선 위 얇은 판
        zm = zB + (zA - zB) * 0.45
        bm = bmesh.new()
        for (y0, z0), (y1, z1) in (((Lf, zB), (Lf * 0.55, zm)), ((Lf * 0.55, zm + 0.9), (0.0, zA))):
            prism_x(bm, [(y0, z0 - 0.02), (y1, z1 - 0.02), (y1, z1 + 0.2), (y0, z0 + 0.2)], -W / 2 - 0.56, -W / 2 + 0.56)
        bm.verts.index_update(); caps.add_bm(bm, sc, DC0, 0); bm.free()
        # 포디움 벽(구덩이 바닥부터)과 위 난간
        bm = bmesh.new(); C.box(bm, -W / 2, W / 2, 0.0, DP1 - DP0, Z_PIT, ZC_BOT); bm.verts.index_update(); rings.add_bm(bm, sc, DP0, 1); bm.free()
        bm = bmesh.new(); C.box(bm, -W / 2, W / 2, 0.75, DP1 - DP0, ZC_BOT, ZC_BOT + 0.7); bm.verts.index_update(); rings.add_bm(bm, sc, DP0, 2); bm.free()
        bm = bmesh.new(); C.box(bm, -W / 2, W / 2, 0.68, DP1 - DP0 + 0.05, ZC_BOT + 0.7, ZC_BOT + 0.86); bm.verts.index_update(); caps.add_bm(bm, sc, DP0, 1); bm.free()
    out = {}
    out['sub'] = sub.obj('H_L0_CaveaVaults', [F['vault']], HC, root)
    out['seats'] = seats.obj('H_L0_Seats', [F['seat'], F['trav_hi']], HC, root)
    out['fins'] = fins.obj('H_L0_RadialWalls', [F['brick']], HC, root)
    out['rings'] = rings.obj('H_L0_InnerRings', [F['tuff'], F['trav'], F['trav_hi']], HC, root)
    out['deep'] = deep.obj('H_L1_CaveaCavities', [F['deep']], HC, root)
    out['caps'] = caps.obj('H_L5_Caps', [F['trav_hi'], F.get('hi', F['trav_hi'])], HC, root)
    return out

def arena_uv(u, v, z):
    c, s = math.cos(C.E.rot), math.sin(C.E.rot)
    return Vector((C.CX + c * u - s * v, C.CY + s * u + c * v, z))

def arena_poly(n=96):
    a, b = C.A - DP1, C.B - DP1
    return a, b

def build_arena(HC, root, F):
    a = C.A - DP1 + 0.05; b = C.B - DP1 + 0.05
    # 나무 바닥(오른쪽): u ≥ U_SPLIT
    pts = []
    t0 = math.acos(max(-1.0, min(1.0, U_SPLIT / a)))
    for k in range(65):
        t = -t0 + 2 * t0 * k / 64
        pts.append((a * math.cos(t), b * math.sin(t)))
    bm = bmesh.new()
    tris = tessellate_polygon([[(p[0], p[1], 0.0) for p in pts]])
    top = [bm.verts.new(arena_uv(u, v, Z_FLOOR)) for u, v in pts]
    bot = [bm.verts.new(arena_uv(u, v, Z_FLOOR - 0.5)) for u, v in pts]
    for t in tris:
        bm.faces.new([top[t[0]], top[t[1]], top[t[2]]]); bm.faces.new([bot[t[2]], bot[t[1]], bot[t[0]]])
    for k in range(len(pts)):
        try: bm.faces.new([top[k], bot[k], bot[(k+1)%len(pts)], top[(k+1)%len(pts)]])
        except ValueError: pass
    uvl = bm.loops.layers.uv.verify()
    for f in bm.faces:
        for lp in f.loops:
            co = lp.vert.co - Vector((C.CX, C.CY, 0))
            c, s = math.cos(-C.E.rot), math.sin(-C.E.rot)
            lp[uvl].uv = (c * co.x - s * co.y, s * co.x + c * co.y)
    floor = R.bm_to_obj(bm, 'H_L0_ArenaFloor', F['wood'], HC, root)
    # 경계 난간(기둥 + 띠)
    bm = bmesh.new()
    vh = b * math.sqrt(max(0.0, 1 - (U_SPLIT / a) ** 2))
    import roma_geo as G
    nseg = 26
    for k in range(nseg + 1):
        v = -vh + 2 * vh * k / nseg
        p = arena_uv(U_SPLIT + 0.1, v, Z_FLOOR)
        G.box(bm, p.x - 0.09, p.x + 0.09, p.y - 0.09, p.y + 0.09, Z_FLOOR, Z_FLOOR + 1.0, 0)
    p0, p1 = arena_uv(U_SPLIT + 0.1, -vh, 0), arena_uv(U_SPLIT + 0.1, vh, 0)
    d = (p1 - p0); L = d.length; d.normalize(); nrm = Vector((-d.y, d.x, 0))
    for zz, hh in ((Z_FLOOR + 0.82, 0.18), (Z_FLOOR + 0.40, 0.10)):
        q = [p0 - nrm * 0.07, p1 - nrm * 0.07, p1 + nrm * 0.07, p0 + nrm * 0.07]
        lo = [bm.verts.new((v_.x, v_.y, zz)) for v_ in q]; hi = [bm.verts.new((v_.x, v_.y, zz + hh)) for v_ in q]
        for qq in ((0,1,2,3),):
            bm.faces.new([lo[3], lo[2], lo[1], lo[0]]); bm.faces.new(hi)
        for k in range(4):
            bm.faces.new([lo[k], lo[(k+1)%4], hi[(k+1)%4], hi[k]])
    R.bm_to_obj(bm, 'H_L0_ArenaRail', F['wood_dk'], HC, root)
    # 하이포게움(왼쪽): 바닥 + 장축 평행 벽 + 가로벽 + 동심 벽
    bm = bmesh.new()
    pit = []
    for k in range(65):
        t = t0 + (2 * math.pi - 2 * t0) * k / 64
        pit.append((a * math.cos(t), b * math.sin(t)))
    tris = tessellate_polygon([[(p[0], p[1], 0.0) for p in pit]])
    vs = [bm.verts.new(arena_uv(u, v, Z_PIT)) for u, v in pit]
    for t in tris: bm.faces.new([vs[t[0]], vs[t[1]], vs[t[2]]])
    R.bm_to_obj(bm, 'H_L0_PitFloor', F['trav_deeper'], HC, root)
    bm = bmesh.new()
    zt_ = Z_FLOOR - 0.15
    ZB = (Z_PIT, zt_ - 2.2, zt_ - 0.45, zt_)           # 벽 아래 → 위: 깊이색 3단(짙음 → 중간 → 윗단 0.45만 벽돌). LocalBanana의 '밝은 벽 윗선 + 짙은 통로'(빛 계산 아님)
    def wall(u0, v0, u1, v1, t=0.45):
        p0, p1 = arena_uv(u0, v0, 0), arena_uv(u1, v1, 0)
        d = p1 - p0
        if d.length < 0.2: return
        d.normalize(); nrm = Vector((-d.y, d.x, 0)) * (t / 2)
        q = [p0 - nrm, p1 - nrm, p1 + nrm, p0 + nrm]
        rings = [[bm.verts.new((v_.x, v_.y, z)) for v_ in q] for z in ZB]
        f = bm.faces.new([rings[0][3], rings[0][2], rings[0][1], rings[0][0]]); f.material_index = 2
        f = bm.faces.new(rings[-1]); f.material_index = 0
        for b in range(3):
            lo, hi = rings[b], rings[b + 1]
            for k in range(4):
                f = bm.faces.new([lo[k], lo[(k+1)%4], hi[(k+1)%4], hi[k]]); f.material_index = (2, 1, 0)[b]
    def v_at(u, frac):
        return b * frac * math.sqrt(max(0.0, 1 - (u / a) ** 2))
    # 동심 타원 벽(경기장 반축의 0.86·0.72·0.58·0.44·0.30배) — 왼쪽 반
    for fr in (0.86, 0.72, 0.58, 0.44, 0.30):
        pts2 = []
        for k in range(33):
            t = t0 + (2 * math.pi - 2 * t0) * k / 32
            pts2.append((a * fr * math.cos(t), b * fr * math.sin(t)))
        for k in range(32):
            wall(pts2[k][0], pts2[k][1], pts2[k+1][0], pts2[k+1][1], 0.55)
    # 중앙 통로(장축 따라 ±0.9)
    for sgn in (-1, 1):
        wall(U_SPLIT - 0.2, sgn * 0.9, -a * 0.97, sgn * 0.9, 0.5)
    # 방사 칸막이(12° 간격, 안쪽 0.30 고리 ~ 바깥 0.97)
    ang = math.degrees(t0) + 10.0
    while ang < 360.0 - math.degrees(t0) - 6.0:
        t = math.radians(ang)
        wall(a * 0.33 * math.cos(t), b * 0.33 * math.sin(t), a * 0.97 * math.cos(t), b * 0.97 * math.sin(t), 0.45)
        ang += 12.0
    hy = R.bm_to_obj(bm, 'H_L0_Hypogeum', [F['tuff'], F.get('hypo_mid', F['tuff']), F.get('hypo_deep', F['deep'])], HC, root)
    return floor, hy
