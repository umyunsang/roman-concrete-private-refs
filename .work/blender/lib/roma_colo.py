
# roma_colo — 콜로세움 히어로 외벽(LocalBanana 디오라마 수준). 단위: 설계 평면 mm. 지역 좌표: 히어로 군 중심(HERO_root) 기준. 담당: hero
# 기준(설계 기준선 8.1 · 기획 결정 D2): 외곽 타원 반축 44.0×36.6, 장축 평면 방위 315°(화면 가로), 아치 40칸, 층 윗선 z 11.5·24.5·37.0·53.0
#   외벽 높이(평면 방위 θ, roma_kit.plan_az): 100~104° 41 · 104~108° 46 · 108~112° 50(경사 부벽) · 112~205° 53 · 205~209° 44(수직 절단)
#   209~322° 37(일부 33.5) · 322~330° 31 · 330~338° 27 · 338~18° 24.5(18.0~24.5 들쭉날쭉) · 18~72° 14.0~17.0 · 72~80° 30 · 80~100° 37
#   둘째 고리 37(정면 10~80°만 9~12). 외벽 두께 2.4 · 바깥 회랑 2.8 · 둘째 고리 1.6
#   칸 경계와 구간 경계가 어긋나는 경사 부벽(100~112°)·수직 절단(205~209°)은 칸 안에서 윗선을 계단으로 나눈다(bay_profile)
# 건물 화면 상자 [192.6, 226.4, 300.4, 330.1]은 외벽 바깥면 타원이다 → 코니스·기단 계단 돌출을 0.75 이하로 둔다(화면 ±0.9)
import bpy, bmesh, math, random
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
import roma_kit as R

A, B, ROT = 44.0, 36.6, 45.0           # 외곽 타원 반축(LocalBanana: 콜로세움 폭 = 조경 영역 폭의 0.53)
NB = 40                                 # 아치 칸 수(LocalBanana에 보이는 칸 수. 실제 80)
E = R.Ell(A, B, ROT)
CX, CY = -15.8, 11.8        # 히어로 군 중심 → 타원 중심(Blender 지역 축: 평면 (−15.8, −11.8))
W = E.L / NB
# 층(외벽): z0, z1, 개구 바닥 ob, 아치 기둥머리 높이 sp, 엔타블러처 높이 ent, 기둥 양식
ST = [dict(z0=0.0, z1=11.5, ob=0.0, sp=5.5, ent=1.45, order='T'),
      dict(z0=11.5, z1=24.5, ob=12.7, sp=18.2, ent=1.45, order='I'),
      dict(z0=24.5, z1=37.0, ob=25.7, sp=30.9, ent=1.45, order='C'),
      dict(z0=37.0, z1=53.0, ob=None, sp=None, ent=1.3, order='A')]
T1 = 2.4          # 외벽 두께
G1 = 2.8          # 바깥 회랑 폭
D2 = T1 + G1      # 둘째 고리 바깥면 깊이
T2 = 1.6
OW = 0.64 * W     # 아치 폭
RA = OW / 2.0
CORNICE = 0.72    # 코니스 돌출(바깥면에서). 화면 상자 ±1.0 안
ENTAB = 0.50      # 엔타블러처 돌출

def rnd(i, k=0):
    return R.hash01(i * 7.13 + k * 1.91, k + 3.3)

H4, H3, H2S = 53.0, 37.0, 24.5
FRONT_MAX = 17.0

def h1(th, i):
    """외벽 높이(칸 가운데 θ 기준). D2 표 그대로"""
    th %= 360.0
    r = rnd(i, 4)
    if 100.0 <= th < 205.0:
        if th < 104.0: return 41.0
        if th < 108.0: return 46.0
        if th < 112.0: return 50.0
        return H4
    if 205.0 <= th < 322.0:
        if th < 209.0: return 44.0
        return H3 if r > 0.25 else H3 - 3.5
    if 322.0 <= th < 338.0:
        return 31.0 if th < 330.0 else 27.0
    if 18.0 <= th < 72.0:
        return min(FRONT_MAX, 14.0 + 3.0 * rnd(i, 8))      # 정면(경기장 앞): 1층 + 부서진 2층 토막(상한 17.0)
    if th >= 338.0 or th < 18.0:
        return H2S - (0.0 if r > 0.55 else (2.0 + 4.5 * rnd(i, 7)))
    # 72~100: 3층으로 올라간다(72~80 30, 80~100 37 — 일부 칸은 2.5 낮게 무너졌다)
    if th < 80.0:
        return 30.0
    return H3 - (0.0 if r > 0.4 else 2.5)

def h2(th, i):
    """둘째 고리(안쪽 아케이드) 37. 정면 10~80°만 9~12로 낮게 무너짐"""
    th %= 360.0
    if 100.0 <= th < 209.0:
        return H3
    if 10.0 <= th < 80.0:
        return 9.0 + 3.0 * rnd(i, 6)
    return H3 - (0.0 if rnd(i, 5) > 0.35 else 2.0 + 3.0 * rnd(i, 6))

# ── 칸 안 윗선: D2 표의 구간 경계가 아치 칸 경계와 어긋나는 자리는 칸을 그 방위에서 나눠 구간마다 제 높이로 자른다 ──
STEP_TH = (18.0, 72.0, 80.0, 100.0, 104.0, 108.0, 112.0, 205.0, 209.0, 322.0, 330.0, 338.0)

def h1_step(th):
    """칸 안 계단 구간의 높이(없으면 None)"""
    th %= 360.0
    if 100.0 <= th < 104.0: return 41.0
    if 104.0 <= th < 108.0: return 46.0
    if 108.0 <= th < 112.0: return 50.0
    if 205.0 <= th < 209.0: return 44.0
    return None

def s_of_th(th, s0, s1):
    """칸 [s0, s1] 안에서 방위 th의 호 길이(az는 s가 늘면 줄어든다)"""
    a, b = s0, s1
    for _ in range(40):
        m = 0.5 * (a + b)
        d = ((E.az(m) - th + 180.0) % 360.0) - 180.0
        if d > 0: a = m
        else: b = m
    return 0.5 * (a + b)

def bay_profile(i):
    """칸 i 외벽 윗선 [(x0, x1, h)] — x는 칸 지역(−W/2 → W/2, θ가 줄어드는 쪽). 보통 칸은 한 토막"""
    s0, s1 = i * W, (i + 1) * W
    th0, th1 = E.az(s0), E.az(s1)
    base = h1(E.az((i + 0.5) * W), i)
    if th0 < th1:          # 0°/360° 경계를 지나는 칸
        return [(-W / 2, W / 2, base)]
    cuts = [t for t in STEP_TH if th1 < t < th0]
    xc = sorted(s_of_th(t, s0, s1) - (s0 + W / 2) for t in cuts)
    xc = [x for x in xc if abs(x) < W / 2 - 0.02]
    if not xc:
        return [(-W / 2, W / 2, base)]
    xs = [-W / 2] + xc + [W / 2]
    segs = []
    for xa, xb in zip(xs, xs[1:]):
        thm = E.az(s0 + W / 2 + 0.5 * (xa + xb))
        h = h1_step(thm)
        if h is None:
            h = h1(thm, i)
        if segs and abs(segs[-1][2] - h) < 1e-6:
            segs[-1] = (segs[-1][0], xb, h)
        else:
            segs.append((xa, xb, h))
    return segs

def h_at(segs, x):
    return next((h for (xa, xb, h) in segs if xa - 1e-6 <= x <= xb + 1e-6), segs[-1][2])

def group_segs(segs, z1):
    """층 윗선(z1)까지 남은 토막은 하나로 묶는다(build_outer 나눔과 같은 순서)"""
    grp = []
    for (xa, xb, h) in segs:
        hh = z1 if h >= z1 - 0.05 else h
        if grp and abs(grp[-1][2] - hh) < 1e-6:
            grp[-1] = (grp[-1][0], xb, hh)
        else:
            grp.append((xa, xb, hh))
    return grp

def wall_top(i, x):
    """외벽 칸 i의 실제 윗선 높이(칸 지역 x). 무너진 윗선의 기울기까지 build_outer와 같다"""
    segs = bay_profile(i)
    if len(segs) == 1:
        H = segs[0][2]
        for k, s in enumerate(ST):
            if s['z0'] < H < s['z1'] - 0.05:
                a = math.radians((rnd(i * 4 + k, 9) * 2 - 1) * 14.0)
                return H - math.tan(a) * x
        return H
    h = h_at(segs, x)
    for k, s in enumerate(ST):
        if s['z0'] < h < s['z1'] - 0.05:
            if s['ob'] is None:
                return h
            for j, (xa, xb, hh) in enumerate(group_segs(segs, s['z1'])):
                if xa - 1e-6 <= x <= xb + 1e-6:
                    a = math.radians((rnd(i * 4 + k + 17 * j, 9) * 2 - 1) * 6.0)
                    return hh - math.tan(a) * (x - 0.5 * (xa + xb))
    return h

def piece(bm, xa, xb):
    """칸 입체에서 xa ≤ x ≤ xb 부분만 남긴 새 bmesh(자른 면은 막는다)"""
    b = bm.copy()
    for (xc, nx) in ((xb, 1.0), (xa, -1.0)):
        if (nx > 0 and xc >= W / 2 - 1e-6) or (nx < 0 and xc <= -W / 2 + 1e-6):
            continue
        geom = b.verts[:] + b.edges[:] + b.faces[:]
        res = bmesh.ops.bisect_plane(b, geom=geom, dist=1e-5, plane_co=Vector((xc, 0.0, 0.0)), plane_no=Vector((nx, 0.0, 0.0)), clear_outer=True)
        ce = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
        if ce:
            try: bmesh.ops.holes_fill(b, edges=ce, sides=0)
            except Exception: pass
    return b

def cut_top_at(bm, h, xm, seed, tilt=6.0):
    """토막 가운데 xm을 축으로 조금 기운 평면으로 윗선을 자른다(구간 높이 ±0.3 안)"""
    a = math.radians((rnd(seed, 9) * 2 - 1) * tilt)
    no = Vector((math.sin(a), 0.0, math.cos(a)))
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=Vector((xm, 0.0, h)), plane_no=no, clear_outer=True)
    ce = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
    if ce:
        try: bmesh.ops.holes_fill(bm, edges=ce, sides=0)
        except Exception: pass

class Acc:
    """여러 칸을 한 메시로 모은다(지역 → 타원 감기 → uv)"""
    def __init__(self):
        self.v = []; self.f = []; self.uv = []; self.mi = []
    def add_bm(self, bm, sc, d0, mi=0):
        base = len(self.v)
        for vt in bm.verts:
            x, y, z = vt.co
            p = E.M(sc + x, d0 + y, z); self.v.append(Vector((p.x + CX, p.y + CY, p.z)))
            self.uv.append((sc + x + 0.37 * y, z))
        for fc in bm.faces:
            self.f.append([base + vt.index for vt in fc.verts])
            self.mi.append(mi if not hasattr(fc, 'material_index') or fc.material_index == 0 else fc.material_index)
    def obj(self, name, mats, coll, parent, smooth=False):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(p) for p in self.v], [], self.f)
        uvl = me.uv_layers.new(name='UVMap')
        for poly in me.polygons:
            poly.material_index = self.mi[poly.index]
            poly.use_smooth = smooth
            for li in poly.loop_indices:
                uvl.data[li].uv = self.uv[me.loops[li].vertex_index]
        me.validate(clean_customdata=False); me.update()
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(name, me); coll.objects.link(ob); ob.parent = parent
        for m in mats: me.materials.append(m)
        return ob

def solid_from_2d(bm, outer, holes, y0, y1):
    """2D(x,z) 외곽+구멍을 y0~y1 두께의 닫힌 입체로"""
    loops = [outer] + holes
    flat = [p for lp in loops for p in lp]
    tris = tessellate_polygon([[(p[0], p[1], 0.0) for p in lp] for lp in loops])
    fv = [bm.verts.new((p[0], y0, p[1])) for p in flat]
    bv = [bm.verts.new((p[0], y1, p[1])) for p in flat]
    for t in tris:
        try: bm.faces.new([fv[t[0]], fv[t[1]], fv[t[2]]])
        except ValueError: pass
        try: bm.faces.new([bv[t[2]], bv[t[1]], bv[t[0]]])
        except ValueError: pass
    off = 0
    for lp in loops:
        n = len(lp)
        for k in range(n):
            a, b = off + k, off + (k + 1) % n
            try: bm.faces.new([fv[a], fv[b], bv[b], bv[a]])
            except ValueError: pass
        off += n

def arch_pts(cx, sp, r, n=12):
    return [(cx + r * math.cos(math.pi - math.pi * k / n), sp + r * math.sin(math.pi - math.pi * k / n)) for k in range(n + 1)]

def bay_panel(z0, z1, ob, sp, t, w=None, ra=None, window=None):
    """한 칸 벽(닫힌 입체). ob=None이면 막힌 벽(window=(폭, z아래, z위) 직사각 창)"""
    w = w or W; ra = ra or RA
    bm = bmesh.new()
    x0, x1 = -w / 2, w / 2
    if ob is None:
        holes = []
        if window:
            ww, wz0, wz1 = window
            holes = [[(-ww/2, wz0), (ww/2, wz0), (ww/2, wz1), (-ww/2, wz1)]]
        solid_from_2d(bm, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)], holes, 0.0, t)
    elif ob <= z0 + 1e-6:
        arc = arch_pts(0.0, sp, ra)
        outer = [(x0, z0), (-ra, z0)] + arc + [(ra, z0), (x1, z0), (x1, z1), (x0, z1)]
        outer = [outer[0], outer[1]] + [p for p in arc] + [outer[-4], outer[-3], outer[-2], outer[-1]]
        solid_from_2d(bm, outer, [], 0.0, t)
    else:
        arc = arch_pts(0.0, sp, ra)
        hole = [(-ra, ob)] + arc + [(ra, ob)]
        hole = [hole[0]] + arc + [hole[-1]]
        solid_from_2d(bm, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)], [hole], 0.0, t)
    return bm

def step_panel(z0, segs, t, window=None):
    """다락(막힌 벽) 한 칸을 칸 안 계단 윗선으로 자른 입체. segs = [(x0, x1, h)], h ≤ z0인 토막은 비운다"""
    bm = bmesh.new()
    runs, cur = [], []
    for (xa, xb, h) in segs:                      # h > z0인 이어진 토막끼리 묶는다
        if h > z0 + 0.05:
            cur.append((xa, xb, h))
        elif cur:
            runs.append(cur); cur = []
    if cur:
        runs.append(cur)
    for run in runs:
        xa0, xb1 = run[0][0], run[-1][1]
        outer = [(xa0, z0), (xb1, z0)]
        for (xa, xb, h) in reversed(run):          # 오른쪽 끝에서 왼쪽으로 윗선을 따라간다
            outer += [(xb, h), (xa, h)]
        ded = []
        for p in outer:
            if not ded or abs(ded[-1][0] - p[0]) > 1e-6 or abs(ded[-1][1] - p[1]) > 1e-6:
                ded.append(p)
        holes = []
        if window:
            ww, wz0, wz1 = window
            if xa0 < -ww / 2 - 0.3 and xb1 > ww / 2 + 0.3 and all(h > wz1 + 0.4 for (xa, xb, h) in run if xb > -ww / 2 and xa < ww / 2):
                holes = [[(-ww / 2, wz0), (ww / 2, wz0), (ww / 2, wz1), (-ww / 2, wz1)]]
        solid_from_2d(bm, ded, holes, 0.0, t)
    return bm

def cut_top(bm, h, i, tilt=14.0):
    """무너진 윗선: 기운 평면으로 자르고 막는다"""
    a = math.radians((rnd(i, 9) * 2 - 1) * tilt)
    no = Vector((math.sin(a), 0.0, math.cos(a)))
    co = Vector((0.0, 0.0, h))
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=co, plane_no=no, clear_outer=True)
    cut_e = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
    if cut_e:
        try: bmesh.ops.holes_fill(bm, edges=cut_e, sides=0)
        except Exception: pass

def box(bm, x0, x1, y0, y1, z0, z1, mi=0):
    vs = [bm.verts.new(c) for c in [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]]
    for q in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
        f = bm.faces.new([vs[k] for k in q]); f.material_index = mi

def half_col(bm, x, y_face, rc, z0, z1, n=8):
    """바깥면(y<0 쪽)으로 튀어나온 반원기둥"""
    pts = [(x + rc * math.cos(math.pi * k / n), y_face - rc * math.sin(math.pi * k / n)) for k in range(n + 1)]
    lo = [bm.verts.new((px, py, z0)) for px, py in pts]
    hi = [bm.verts.new((px, py, z1)) for px, py in pts]
    for k in range(n):
        bm.faces.new([lo[k], lo[k+1], hi[k+1], hi[k]])
    bm.faces.new(lo[::-1]); bm.faces.new(hi)
    bm.faces.new([lo[0], hi[0], hi[-1], lo[-1]])

def voussoirs(bm, sp, ra, n=9, w=0.42, y0=-0.07, y1=-0.005):
    """L3 홍예석 고리: 아치 둘레 쐐기돌 n개(번갈아 두 색 = 재질 번호 0/1). 가운데(이맛돌)는 L2 쐐기돌이 있어 비운다"""
    for k in range(n):
        if k == n // 2:
            continue
        t0 = math.pi - k * math.pi / n - 0.02; t1 = math.pi - (k + 1) * math.pi / n + 0.02
        pts = [(ra * math.cos(t0), sp + ra * math.sin(t0)), ((ra + w) * math.cos(t0), sp + (ra + w) * math.sin(t0)),
               ((ra + w) * math.cos(t1), sp + (ra + w) * math.sin(t1)), (ra * math.cos(t1), sp + ra * math.sin(t1))]
        before = set(bm.faces)
        solid_from_2d(bm, pts, [], y0, y1)
        for f in bm.faces:
            if f not in before:
                f.material_index = k % 2

def build_outer(HC, root, M):
    """M: TRAV·TRAV_IN·TUFF(+ HI: L5 코니스 윗선·계단 윗선 · STAIN: L6 빗물 자국 · VOUS: L3 홍예석(2색) · HOLE: L4 꺾쇠 구멍)"""
    walls, deco, vaults = Acc(), Acc(), Acc()
    hl = Acc() if 'HI' in M else None
    st = Acc() if 'STAIN' in M else None
    vs = Acc() if 'VOUS' in M else None
    ho = Acc() if 'HOLE' in M else None
    eh = Acc() if 'HI' in M else None            # L5 계단 윗선(경사 부벽·수직 절단 토막의 밝은 모서리)
    for i in range(NB):
        sc = (i + 0.5) * W
        th = E.az(sc)
        segs = bay_profile(i)
        special = len(segs) > 1
        H1 = max(h for (_, _, h) in segs)
        H2 = h2(th, i)
        def hx(x):
            return h_at(segs, x)
        def hmin(x0, x1):
            return min([h for (xa, xb, h) in segs if xb > x0 and xa < x1] or [hx(0.5 * (x0 + x1))])
        for k, s in enumerate(ST):
            if s['z0'] >= H1 - 0.2:
                break
            z0, z1 = s['z0'], s['z1']
            win = (0.34 * W, z0 + 6.4, z0 + 9.6) if (s['order'] == 'A' and i % 2 == 0) else None
            # ── 벽 입체 ──
            if not special:
                bm = bay_panel(z0, z1, s['ob'], s['sp'], T1, window=win)
                if H1 < z1 - 0.05:
                    cut_top(bm, H1, i * 4 + k)
                bm.verts.index_update(); bm.faces.index_update()
                walls.add_bm(bm, sc, 0.0, 0); bm.free()
            elif s['ob'] is None:
                bm = step_panel(z0, [(xa, xb, min(h, z1)) for (xa, xb, h) in segs], T1, window=win)
                bm.verts.index_update(); bm.faces.index_update()
                walls.add_bm(bm, sc, 0.0, 0); bm.free()
            else:
                full_bm = bay_panel(z0, z1, s['ob'], s['sp'], T1, window=win)
                for j, (xa, xb, h) in enumerate(group_segs(segs, z1)):
                    if h <= z0 + 0.05:
                        continue
                    pc = piece(full_bm, xa, xb)
                    if h < z1 - 0.05:
                        cut_top_at(pc, h, 0.5 * (xa + xb), i * 4 + k + 17 * j)
                    pc.verts.index_update(); pc.faces.index_update()
                    if len(pc.verts):
                        walls.add_bm(pc, sc, 0.0, 0)
                    pc.free()
                full_bm.free()
            # ── 장식: 반원기둥(칸 왼쪽 끝), 엔타블러처, 문설주 띠, 쐐기돌 ──
            bm = bmesh.new()
            hleft = hx(-W / 2 + 0.01)
            ztop = min(z1 - s['ent'], hleft)
            trunc_left = hleft < z1 - 0.05
            if s['order'] in 'TIC':
                rc = 0.52 if s['order'] == 'T' else 0.48
                cz0 = z0 + (0.0 if s['order'] == 'T' else 1.25)
                if ztop - cz0 > 0.6:
                    half_col(bm, -W / 2, 0.02, rc, cz0, ztop)
                    if not trunc_left:
                        box(bm, -W/2 - 0.7, -W/2 + 0.7, -0.62, 0.15, ztop - 0.45, ztop)    # 주두
                    box(bm, -W/2 - 0.66, -W/2 + 0.66, -0.6, 0.1, cz0, cz0 + 0.35)            # 주초
                if s['ob'] is not None and s['ob'] > z0:
                    for (xa, xb, h) in segs:                                                 # 기단 띠
                        if h > s['ob']:
                            box(bm, xa, xb, -0.35, 0.1, z0, z0 + 1.25)
                for sx in (-1, 1):                                                           # 홍예 받침 띠
                    x_in, x_out = sx * RA, sx * (W / 2 - 0.55)
                    if hmin(min(x_in, x_out), max(x_in, x_out)) > s['sp'] + 0.3:
                        box(bm, min(x_in, x_out), max(x_in, x_out), -0.12, 0.05, s['sp'] - 0.32, s['sp'])
                if hmin(-RA - 0.45, RA + 0.45) > s['sp'] + RA + 0.6:
                    box(bm, -0.28, 0.28, -0.14, 0.05, s['sp'] + RA - 0.15, s['sp'] + RA + 0.55)          # 쐐기돌
                    if vs is not None:                                                               # L3 홍예석 고리
                        bv = bmesh.new(); voussoirs(bv, s['sp'], RA); bv.verts.index_update(); bv.faces.index_update()
                        vs.add_bm(bv, sc, 0.0, 0); bv.free()
            else:
                if ztop - z0 > 0.6:
                    box(bm, -W/2 - 0.45, -W/2 + 0.45, -0.32, 0.05, z0, ztop)                           # 벽기둥
                for cx in (-0.25 * W, 0.25 * W):                                                       # 까치발(그 자리 윗선이 넉넉할 때만)
                    if hmin(cx - 0.25, cx + 0.25) > z0 + 12.7:
                        box(bm, cx - 0.22, cx + 0.22, -0.55, 0.05, z0 + 11.6, z0 + 12.4)
            full = [(xa, xb) for (xa, xb, h) in segs if h >= z1 - 0.05]                                # 층 윗선까지 남은 토막
            for (xa, xb) in full:
                box(bm, xa, xb, -ENTAB, 0.12, z1 - s['ent'], z1 - 0.42)                                # 엔타블러처
                box(bm, xa, xb, -CORNICE, 0.12, z1 - 0.42, z1)                                         # 코니스
                if hl is not None:                                                                     # L5 코니스 앞 윗선(밝은 띠)
                    bh = bmesh.new()
                    box(bh, xa, xb, -CORNICE - 0.06, -CORNICE + 0.04, z1 - 0.36, z1 + 0.02)
                    bh.verts.index_update(); hl.add_bm(bh, sc, 0.0, 0); bh.free()
            if special and s['ob'] is None and eh is not None:                                         # L5 계단 토막 윗선(다락)
                be = bmesh.new()
                for (xa, xb, h) in segs:
                    if z0 + 0.3 < h < z1 - 0.05:
                        box(be, xa + 0.02, xb - 0.02, -0.06, 0.28, h, h + 0.05)          # 윗면 바깥 모서리 띠
                        box(be, xa, xb, -0.08, -0.02, h - 0.3, h + 0.05)                 # 바깥면 윗선
                be.verts.index_update()
                if len(be.verts):
                    eh.add_bm(be, sc, 0.0, 0)
                be.free()
            if st is not None and full:                                                                # L6 빗물 자국(엔타블러처 밑 세로 줄)
                bs = bmesh.new(); zt = z1 - s['ent']
                if s['order'] in 'TIC':
                    if rnd(i, 200 + k) > 0.25 and any(xa <= RA + 0.1 and xb >= RA + 0.6 for (xa, xb) in full):
                        L_ = 1.4 + 3.4 * rnd(i, 210 + k); w_ = 0.22 + 0.16 * rnd(i, 220 + k)
                        box(bs, RA + 0.1, RA + 0.1 + w_, -0.075, -0.015, zt - L_, zt)
                    if rnd(i, 205 + k) > 0.55 and any(xa <= -RA - 0.7 for (xa, xb) in full):
                        L_ = 1.0 + 2.6 * rnd(i, 215 + k); w_ = 0.18 + 0.14 * rnd(i, 225 + k)
                        box(bs, -RA - 0.1 - w_, -RA - 0.1, -0.075, -0.015, zt - L_, zt)
                else:
                    for j, x_ in enumerate((-W/2 + 0.75, 0.22 * W, 0.36 * W)):
                        if rnd(i, 230 + j) > 0.5 and any(xa <= x_ <= xb - 0.3 for (xa, xb) in full):
                            L_ = 2.5 + 5.0 * rnd(i, 240 + j); w_ = 0.25 + 0.2 * rnd(i, 250 + j)
                            box(bs, x_, x_ + w_, -0.075, -0.015, zt - L_, zt)
                bs.verts.index_update()
                if len(bs.verts):
                    st.add_bm(bs, sc, 0.0, 0)
                bs.free()
            if ho is not None:                                                                         # L4 꺾쇠 구멍(중세에 쇠를 뽑아 간 자국)
                bo = bmesh.new()
                if s['order'] in 'TIC':
                    for j in range(4):
                        if rnd(i, 300 + 10 * k + j) < 0.25:
                            continue
                        x_ = (-1 if j % 2 == 0 else 1) * (RA * 0.55 + (W / 2 - 0.9 - RA * 0.55) * rnd(i, 310 + 10 * k + j))
                        ztp = min(z1 - s['ent'], hx(x_)) - 0.6
                        z_ = s['sp'] + RA * 0.8 + (ztp - s['sp'] - RA * 0.8) * rnd(i, 320 + 10 * k + j)
                        if s['sp'] + RA * 0.8 < z_ < ztp and abs(x_) > 0.45:
                            box(bo, x_ - 0.15, x_ + 0.15, -0.08, -0.02, z_ - 0.12, z_ + 0.12)
                else:
                    for j in range(7):
                        if rnd(i, 340 + j) < 0.25:
                            continue
                        x_ = -W / 2 + 0.75 + (W - 1.5) * rnd(i, 350 + j)
                        ztp = min(z1 - s['ent'], hx(x_)) - 0.8
                        z_ = z0 + 1.0 + (min(ztp, z0 + 14.5) - z0 - 1.0) * rnd(i, 360 + j)
                        if win and abs(x_) < win[0] / 2 + 0.35 and win[1] - 0.4 < z_ < win[2] + 0.4:
                            continue
                        if z0 + 0.8 < z_ < ztp:
                            box(bo, x_ - 0.16, x_ + 0.16, -0.08, -0.02, z_ - 0.13, z_ + 0.13)
                bo.verts.index_update()
                if len(bo.verts):
                    ho.add_bm(bo, sc, 0.0, 0)
                bo.free()
            bm.verts.index_update(); bm.faces.index_update()
            if len(bm.verts):
                deco.add_bm(bm, sc, 0.0, 0)
            bm.free()
        # L6 1층 기둥 사이 습기 얼룩(땅에서 튄 물·이끼 기운): 기둥 바깥면 아랫단
        if st is not None and 'DAMP' in M and rnd(i, 260) > 0.35 and H1 > 3.0:
            bd = bmesh.new()
            for sx in (-1, 1):
                if rnd(i, 261 + sx) > 0.3:
                    x0_, x1_ = (RA + 0.08, W / 2 - 0.62) if sx > 0 else (-W / 2 + 0.62, -RA - 0.08)
                    box(bd, x0_, x1_, -0.075, -0.015, 0.56, 0.95 + 0.9 * rnd(i, 262 + sx))
            bd.verts.index_update()
            if len(bd.verts):
                st.add_bm(bd, sc, 0.0, 1)
            bd.free()
        # 기단 계단 2단(돌출 0.75: 화면 상자 ±1.0 안)
        bm = bmesh.new(); box(bm, -W/2, W/2, -0.75, 0.2, 0.0, 0.30); box(bm, -W/2, W/2, -0.38, 0.2, 0.30, 0.55)
        bm.verts.index_update(); deco.add_bm(bm, sc, 0.0, 0); bm.free()
        # 둘째 고리(안쪽 아케이드, 기둥 없음)
        for k, s in enumerate(ST[:3]):
            if s['z0'] >= H2 - 0.2:
                break
            ob = s['ob'] if s['ob'] is None else (s['z0'] if k == 0 else s['z0'] + 0.9)
            bm = bay_panel(s['z0'], s['z1'], ob, s['sp'] - 0.6, T2, ra=RA * 0.92)
            if H2 < s['z1'] - 0.05:
                cut_top(bm, H2, i * 4 + k + 101, 20.0)
            bm.verts.index_update(); walls.add_bm(bm, sc, D2, 1); bm.free()
        # 회랑 천장 볼트(두 고리가 모두 남은 층)
        Hv = min(min(h for (_, _, h) in segs), H2)
        for s in ST[:3]:
            if Hv >= s['z1'] + 0.4 or (s['z1'] <= Hv + 0.05):
                bm = bmesh.new(); box(bm, -W/2, W/2, T1 - 0.05, D2 + 0.05, s['z1'] - 0.9, s['z1']); bm.verts.index_update()
                vaults.add_bm(bm, sc, 0.0, 0); bm.free()
    ow = walls.obj('H_Walls', [M['TRAV'], M['TRAV_IN']], HC, root)
    od = deco.obj('H_Orders', [M['TRAV']], HC, root)
    ov = vaults.obj('H_Vaults', [M['TUFF']], HC, root)
    extra = {}
    if hl is not None and hl.f:
        extra['cornice'] = hl.obj('H_L5_CorniceLines', [M['HI']], HC, root)
    if eh is not None and eh.f:
        extra['steps'] = eh.obj('H_L5_StepEdges', [M['HI']], HC, root)
    if st is not None and st.f:
        extra['stains'] = st.obj('H_L6_Stains', [M['STAIN'], M.get('DAMP', M['STAIN'])], HC, root)
    if vs is not None and vs.f:
        extra['vous'] = vs.obj('H_L3_Voussoirs', list(M['VOUS']), HC, root)
    if ho is not None and ho.f:
        extra['holes'] = ho.obj('H_L4_CrampHoles', [M['HOLE']], HC, root)
    build_outer.extra = extra
    return ow, od, ov
