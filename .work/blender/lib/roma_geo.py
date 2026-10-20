
# roma_geo — 랜드마크 공용 형상(bmesh, 지역 mm, uv = mm)
import bpy, bmesh, math
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
import roma_kit as R

def _uv(bm):
    return bm.loops.layers.uv.verify()

def uv_box(bm, faces):
    uvl = _uv(bm)
    for f in faces:
        f.normal_update()
        n = f.normal
        ax = max(range(3), key=lambda k: abs(n[k]))
        for lp in f.loops:
            c = lp.vert.co
            if ax == 0: lp[uvl].uv = (c.y, c.z)
            elif ax == 1: lp[uvl].uv = (c.x, c.z)
            else: lp[uvl].uv = (c.x, c.y)

def uv_cyl(bm, faces, cx, cy, r):
    uvl = _uv(bm)
    for f in faces:
        f.normal_update()
        top = abs(f.normal.z) > 0.7
        for lp in f.loops:
            c = lp.vert.co
            if top:
                lp[uvl].uv = (c.x, c.y)
            else:
                a = math.atan2(c.y - cy, c.x - cx)
                lp[uvl].uv = (a * r, c.z)

def box(bm, x0, x1, y0, y1, z0, z1, mi=0):
    vs = [bm.verts.new(c) for c in [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]]
    fs = [bm.faces.new([vs[k] for k in q]) for q in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]]
    for f in fs: f.material_index = mi
    uv_box(bm, fs)
    return fs

def prism(bm, pts, z0, z1, mi=0, top=True, bottom=True):
    lo = [bm.verts.new((x, y, z0)) for x, y in pts]
    hi = [bm.verts.new((x, y, z1)) for x, y in pts]
    fs = []
    n = len(pts)
    for k in range(n):
        fs.append(bm.faces.new([lo[k], lo[(k+1)%n], hi[(k+1)%n], hi[k]]))
    if top: fs.append(bm.faces.new(hi))
    if bottom: fs.append(bm.faces.new(lo[::-1]))
    for f in fs: f.material_index = mi
    uv_box(bm, fs)
    return fs

def cyl(bm, cx, cy, r, z0, z1, n=32, mi=0, r_top=None, top=True, bottom=False, a0=0.0, a1=360.0):
    rt = r if r_top is None else r_top
    full = abs(a1 - a0) >= 359.99
    m = n if full else n + 1
    ang = [math.radians(a0 + (a1 - a0) * k / n) for k in range(m)]
    lo = [bm.verts.new((cx + r*math.cos(a), cy + r*math.sin(a), z0)) for a in ang]
    hi = [bm.verts.new((cx + rt*math.cos(a), cy + rt*math.sin(a), z1)) for a in ang]
    fs = []
    seg = n if full else n
    for k in range(seg):
        k2 = (k + 1) % m
        fs.append(bm.faces.new([lo[k], lo[k2], hi[k2], hi[k]]))
    if full:
        if top: fs.append(bm.faces.new(hi))
        if bottom: fs.append(bm.faces.new(lo[::-1]))
    for f in fs: f.material_index = mi
    uv_cyl(bm, fs, cx, cy, r)
    return fs

def ring(bm, cx, cy, r0, r1, z0, z1, n=48, mi=0, a0=0.0, a1=360.0):
    """두께 있는 고리(부채꼴) 입체"""
    full = abs(a1 - a0) >= 359.99
    m = n if full else n + 1
    ang = [math.radians(a0 + (a1 - a0) * k / n) for k in range(m)]
    def P(r, a, z): return bm.verts.new((cx + r*math.cos(a), cy + r*math.sin(a), z))
    io = [[P(r0, a, z0), P(r1, a, z0), P(r1, a, z1), P(r0, a, z1)] for a in ang]
    fs = []
    for k in range(n):
        k2 = (k + 1) % m
        A, Bq = io[k], io[k2]
        for (i, j) in ((0, 1), (1, 2), (2, 3), (3, 0)):
            fs.append(bm.faces.new([A[i], Bq[i], Bq[j], A[j]]))
    if not full:
        fs.append(bm.faces.new(io[0][::-1])); fs.append(bm.faces.new(io[-1]))
    for f in fs: f.material_index = mi
    uv_cyl(bm, fs, cx, cy, (r0 + r1) / 2)
    return fs

def dome(bm, cx, cy, r, z0, n=48, rings=12, oculus=0.0, mi=0, hk=1.0):
    """반구 돔 겉면(오큘러스 구멍 선택). hk = 높이/반지름"""
    a_top = math.asin(oculus / r) if oculus > 0 else 0.0
    rows = []
    for j in range(rings + 1):
        phi = (math.pi / 2 - a_top) * j / rings      # 0 = 밑동
        rr = r * math.cos(phi); zz = z0 + r * hk * math.sin(phi)
        rows.append([bm.verts.new((cx + rr*math.cos(2*math.pi*k/n), cy + rr*math.sin(2*math.pi*k/n), zz)) for k in range(n)])
    fs = []
    for j in range(rings):
        for k in range(n):
            k2 = (k + 1) % n
            fs.append(bm.faces.new([rows[j][k], rows[j][k2], rows[j+1][k2], rows[j+1][k]]))
    if oculus <= 0:
        top = bm.verts.new((cx, cy, z0 + r * hk))
        for k in range(n):
            fs.append(bm.faces.new([rows[-1][k], rows[-1][(k+1)%n], top]))
    for f in fs: f.material_index = mi
    uv_cyl(bm, fs, cx, cy, r)
    return fs, rows

def gable(bm, x0, x1, y0, y1, z0, z1, axis='X', mi=0, over=0.0):
    """박공지붕(용마루가 axis 방향)"""
    if axis == 'X':
        ym = (y0 + y1) / 2
        p = [(x0-over, y0-over, z0), (x1+over, y0-over, z0), (x1+over, ym, z1), (x0-over, ym, z1), (x1+over, y1+over, z0), (x0-over, y1+over, z0)]
        vs = [bm.verts.new(c) for c in p]
        fq = [(0,1,2,3), (3,2,4,5), (0,3,5), (1,4,2), (0,5,4,1)]
    else:
        xm = (x0 + x1) / 2
        p = [(x0-over, y0-over, z0), (xm, y0-over, z1), (x1+over, y0-over, z0), (x1+over, y1+over, z0), (xm, y1+over, z1), (x0-over, y1+over, z0)]
        vs = [bm.verts.new(c) for c in p]
        fq = [(0,1,4,5), (1,2,3,4), (0,2,1), (3,5,4), (0,5,3,2)]
    fs = [bm.faces.new([vs[k] for k in q]) for q in fq]
    for f in fs: f.material_index = mi
    uv_box(bm, fs)
    return fs

def column(bm, x, y, r, z0, z1, n=12, mi=0, mi_cap=None, base=True, cap=True):
    mc = mi if mi_cap is None else mi_cap
    zb, zc = z0, z1
    if base:
        box(bm, x - r*1.35, x + r*1.35, y - r*1.35, y + r*1.35, z0, z0 + r*0.55, mc); zb = z0 + r*0.55
    if cap:
        zc = z1 - r*0.75
        box(bm, x - r*1.4, x + r*1.4, y - r*1.4, y + r*1.4, zc + r*0.35, z1, mc)
        cyl(bm, x, y, r*1.0, zc, zc + r*0.35, n, mc, r_top=r*1.3)
    cyl(bm, x, y, r, zb, zc, n, mi, r_top=r*0.88)

def wall_holes(bm, axis, c0, c1, t0, t1, z0, z1, holes, mi=0, n=10):
    """곧은 벽(축 axis='X'면 길이 방향 x, 두께 y). holes: [('arch', u0, u1, z_bot, z_spring) | ('rect', u0, u1, zb, zt)]"""
    outer = [(c0, z0), (c1, z0), (c1, z1), (c0, z1)]
    hl = []
    for h in holes:
        kind, u0, u1, zb, zs = h
        if kind == 'arch':
            rr = (u1 - u0) / 2; cu = (u0 + u1) / 2
            arc = [(cu + rr*math.cos(math.pi - math.pi*k/n), zs + rr*math.sin(math.pi - math.pi*k/n)) for k in range(n + 1)]
            if zb <= z0 + 1e-6:
                continue
            hl.append([(u0, zb)] + arc[1:-1] + [(u1, zb)] if False else [(u0, zb)] + arc + [(u1, zb)])
        else:
            hl.append([(u0, zb), (u1, zb), (u1, zs), (u0, zs)])
    # 바닥에 닿는 아치는 외곽선에 끼운다
    ground = sorted([h for h in holes if h[0] == 'arch' and h[3] <= z0 + 1e-6], key=lambda h: h[1])
    if ground:
        pts = [(c0, z0)]
        for _, u0, u1, zb, zs in ground:
            rr = (u1 - u0) / 2; cu = (u0 + u1) / 2
            pts += [(u0, z0)] + [(cu + rr*math.cos(math.pi - math.pi*k/n), zs + rr*math.sin(math.pi - math.pi*k/n)) for k in range(n + 1)] + [(u1, z0)]
        pts += [(c1, z0), (c1, z1), (c0, z1)]
        outer = pts
    # 중복점 정리
    def dedup(lp):
        out = []
        for p in lp:
            if not out or (abs(out[-1][0]-p[0]) > 1e-6 or abs(out[-1][1]-p[1]) > 1e-6):
                out.append(p)
        if len(out) > 2 and abs(out[0][0]-out[-1][0]) < 1e-6 and abs(out[0][1]-out[-1][1]) < 1e-6:
            out.pop()
        return out
    loops = [dedup(outer)] + [dedup(h) for h in hl]
    tris = tessellate_polygon([[(p[0], p[1], 0.0) for p in lp] for lp in loops])
    flat = [p for lp in loops for p in lp]
    def V(u, t, z):
        return bm.verts.new((u, t, z) if axis == 'X' else (t, u, z))
    fv = [V(p[0], t0, p[1]) for p in flat]
    bv = [V(p[0], t1, p[1]) for p in flat]
    fs = []
    for tr in tris:
        try: fs.append(bm.faces.new([fv[tr[0]], fv[tr[1]], fv[tr[2]]]))
        except ValueError: pass
        try: fs.append(bm.faces.new([bv[tr[2]], bv[tr[1]], bv[tr[0]]]))
        except ValueError: pass
    off = 0
    for lp in loops:
        m = len(lp)
        for k in range(m):
            a, b = off + k, off + (k + 1) % m
            try: fs.append(bm.faces.new([fv[a], fv[b], bv[b], bv[a]]))
            except ValueError: pass
        off += m
    for f in fs: f.material_index = mi
    uv_box(bm, fs)
    return fs

def finish(bm, name, mats, coll, parent=None, smooth=False):
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    ob = R.bm_to_obj(bm, name, mats, coll, parent, smooth)
    return ob

def screen_bbox(obs):
    xs, ys = [], []
    for ob in obs:
        if ob.type != 'MESH':
            continue
        mw = ob.matrix_world
        for v in ob.data.vertices:
            sx, sy = R.scr(mw @ v.co)
            xs.append(sx); ys.append(sy)
    return min(xs), min(ys), max(xs), max(ys)

def fit_to_box(root, box, grow=1.0, mode='fit'):
    """root 아래 메시들의 화면 외곽이 box(화면 mm)에 맞도록 균일 축척 + 평면 이동(지면 Z 유지)"""
    bpy.context.view_layer.update()
    kids = [o for o in root.children_recursive if o.type == 'MESH' and not o.hide_render]
    x0, y0, x1, y1 = screen_bbox(kids)
    bw, bh = box[2] - box[0], box[3] - box[1]
    s = min(bw / (x1 - x0), bh / (y1 - y0)) * grow
    root.scale = root.scale * s
    bpy.context.view_layer.update()
    x0, y0, x1, y1 = screen_bbox(kids)
    dx = (box[0] + box[2]) / 2 - (x0 + x1) / 2
    dy = (box[1] + box[3]) / 2 - (y0 + y1) / 2
    dX, dY = R.to_plan(dx, dy)
    root.location = root.location + Vector((dX, -dY, 0.0))
    bpy.context.view_layer.update()
    return s, screen_bbox(kids)

def new_root(name, coll, X, Y, Z=0.0):
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, None)
        coll.objects.link(ob)
    ob.location = R.P(X, Y, Z); ob.scale = (1, 1, 1); ob.empty_display_size = 8
    return ob
