
# roma_layers — 표현 레이어 도구(한 오브젝트에 레이어를 쌓는다). 담당: hero
# Obj: 오브젝트 하나 = 루트 Empty {PKG}_{Obj}_root + 레이어별 메시 {PKG}_{Obj}_L{n}_{part}
# 평면 도형: flat_poly(구멍 가능 윗면) · blob(불규칙 외곽) · obox(돌린 상자) · rod(두 점 원기둥) · tuft(풀 포기) · ell_band(콜로세움 타원 띠)
import bpy, bmesh, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.geometry import tessellate_polygon
import roma_kit as R, roma_geo as G


def _C():
    """roma_colo는 이 모듈 다음에 불러오므로 부를 때 최신 모듈을 쓴다"""
    import sys
    return sys.modules['roma_colo']


def depth_colors(walls, m_face, m_soffit, m_deep):
    """L1 깊이색: 지붕 아래 회랑을 향한 면 = 짙은 색, 아치 안쪽 면·기둥 옆면 = 중간 깊이색"""
    C = _C()
    me = walls.data
    me.materials.clear()
    for m in (m_face, m_soffit, m_deep):
        me.materials.append(m)
    roof = []
    for i in range(C.NB):
        sc_ = (i + 0.5) * C.W; th = C.E.az(sc_)
        H1, H2 = C.h1(th, i), C.h2(th, i); rz = 0.0
        for s in C.ST[:3]:
            if min(H1, H2) >= s['z1'] - 0.05: rz = s['z1']
        roof.append(rz)
    n = len(me.polygons)
    cen = np.empty(n*3, np.float32); me.polygons.foreach_get('center', cen); cen = cen.reshape(-1, 3)
    nor = np.empty(n*3, np.float32); me.polygons.foreach_get('normal', nor); nor = nor.reshape(-1, 3)
    mi = np.empty(n, np.int32); me.polygons.foreach_get('material_index', mi)
    rad = cen[:, :2] - np.array([C.CX, C.CY]); rad /= np.linalg.norm(rad, axis=1)[:, None] + 1e-9
    radial = (nor[:, :2] * rad).sum(1)
    ang = np.degrees(np.arctan2(rad[:, 1], rad[:, 0])) - C.ROT
    t = np.radians(ang)
    tt = np.degrees(np.arctan2(np.sin(t) / C.B, np.cos(t) / C.A)) % 360.0
    bay = np.clip((tt / 360.0 * C.NB).astype(int), 0, C.NB - 1)
    rz = np.array(roof)[bay]
    corridor = ((mi == 0) & (radial < -0.6)) | ((mi == 1) & (radial > 0.6))
    inside = corridor & (cen[:, 2] < rz - 0.05)
    soffit = (np.abs(radial) < 0.6) & (nor[:, 2] < 0.6)
    new = np.zeros(n, np.int32); new[soffit] = 1; new[inside] = 2
    me.polygons.foreach_set('material_index', new); me.update()
    return int(inside.sum()), int(soffit.sum())


class Obj:
    """표현 레이어 묶음. bm(n, part, mats)로 레이어 메시를 받아 쌓고 done()으로 오브젝트를 만든다"""
    def __init__(self, pkg, name, coll, parent, loc=(0.0, 0.0, 0.0), rot=0.0, scale=1.0):
        self.pkg, self.name, self.coll = pkg, name, coll
        self.root = bpy.data.objects.new('%s_%s_root' % (pkg, name), None)
        coll.objects.link(self.root)
        self.root.parent = parent
        self.root.location = Vector(loc)
        self.root.rotation_euler = (0.0, 0.0, math.radians(rot))
        self.root.scale = (scale, scale, scale)
        self.root.empty_display_size = 3.0
        self.parts = {}
        self.n_place = 0

    def bm(self, n, part, mats, closed=True):
        """closed=True: 닫힌 입체(법선 다시 계산) · False: 위를 보는 평면 조각(법선 그대로)"""
        k = (n, part)
        if k not in self.parts:
            b = bmesh.new(); b.loops.layers.uv.verify()
            self.parts[k] = [b, list(mats), closed]
        return self.parts[k][0]

    def place(self, proto, x, y, z, s, rot, n=6, part='Life'):
        """원형 링크 복제(루트 지역 좌표)"""
        import roma_props as RP
        self.n_place += 1
        nm = '%s_%s_L%d_%s_%02d' % (self.pkg, self.name, n, part, self.n_place)
        return RP.place(proto, x, y, z, s, rot, self.coll, name=nm, parent=self.root, local=True)

    def done(self):
        obs = []
        for (n, part), (b, mats, closed) in sorted(self.parts.items()):
            if not b.faces:
                b.free(); continue
            nm = '%s_%s_L%d_%s' % (self.pkg, self.name, n, part)
            obs.append(R.bm_to_obj(b, nm, mats, self.coll, self.root, False, closed))
        return obs


def up_faces(faces):
    for f in faces:
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()


def flat_poly(bm, loops, z, mi=0, uv_off=(0.0, 0.0)):
    """평면 다각형(loops[0] 바깥, 나머지 구멍)을 높이 z의 윗면 한 겹으로. uv = (x, y) mm"""
    loops = [lp for lp in loops if len(lp) >= 3]
    flat = [p for lp in loops for p in lp]
    tris = tessellate_polygon([[(p[0], p[1], 0.0) for p in lp] for lp in loops])
    vs = [bm.verts.new((p[0], p[1], z)) for p in flat]
    uvl = bm.loops.layers.uv.verify()
    out = []
    for t in tris:
        try:
            f = bm.faces.new([vs[t[0]], vs[t[1]], vs[t[2]]])
        except ValueError:
            continue
        f.material_index = mi
        out.append(f)
    up_faces(out)
    for f in out:
        for lp in f.loops:
            lp[uvl].uv = (lp.vert.co.x + uv_off[0], lp.vert.co.y + uv_off[1])
    return out


def blob(cx, cy, rx, ry, n=14, seed=0.0, jit=0.22, rot=0.0):
    """불규칙한 닫힌 외곽(풀밭·흙 자국)"""
    cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        j = 1.0 + jit * (R.hash01(seed * 3.7 + 1.3, k) * 2 - 1)
        x, y = rx * j * math.cos(a), ry * j * math.sin(a)
        pts.append((cx + cr * x - sr * y, cy + sr * x + cr * y))
    return pts


def obox(bm, cx, cy, z0, w, d, h, ang=0.0, mi=0, tilt=(0.0, 0.0)):
    """평면 회전 ang°·기울기 tilt(°, X축·Y축)의 상자. 중심 (cx, cy), 바닥 z0"""
    M = (Matrix.Translation((cx, cy, z0)) @ Matrix.Rotation(math.radians(ang), 4, 'Z')
         @ Matrix.Rotation(math.radians(tilt[0]), 4, 'X') @ Matrix.Rotation(math.radians(tilt[1]), 4, 'Y'))
    pts = [(-w/2, -d/2, 0), (w/2, -d/2, 0), (w/2, d/2, 0), (-w/2, d/2, 0), (-w/2, -d/2, h), (w/2, -d/2, h), (w/2, d/2, h), (-w/2, d/2, h)]
    vs = [bm.verts.new(M @ Vector(p)) for p in pts]
    fs = [bm.faces.new([vs[k] for k in q]) for q in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]]
    for f in fs:
        f.material_index = mi
    G.uv_box(bm, fs)
    return fs


def rod(bm, p0, p1, r0, r1=None, n=8, mi=0, cap=True):
    """두 점 사이 원기둥(굵기 r0 → r1)"""
    r1 = r0 if r1 is None else r1
    a, b = Vector(p0), Vector(p1)
    ax = b - a
    if ax.length < 1e-6:
        return []
    ax.normalize()
    t = Vector((0, 0, 1)) if abs(ax.z) < 0.9 else Vector((1, 0, 0))
    u = ax.cross(t).normalized(); v = ax.cross(u).normalized()
    ring = [u * math.cos(2 * math.pi * k / n) + v * math.sin(2 * math.pi * k / n) for k in range(n)]
    lo = [bm.verts.new(a + q * r0) for q in ring]
    hi = [bm.verts.new(b + q * r1) for q in ring]
    fs = [bm.faces.new([lo[k], lo[(k + 1) % n], hi[(k + 1) % n], hi[k]]) for k in range(n)]
    if cap:
        fs.append(bm.faces.new(lo[::-1])); fs.append(bm.faces.new(hi))
    for f in fs:
        f.material_index = mi
    G.uv_box(bm, fs)
    return fs


def tuft(bm, x, y, z, s, seed, mi=0, blades=3):
    """풀 포기: 뾰족한 5각 뿔 잎 몇 장"""
    for k in range(blades):
        a = 2 * math.pi * (k / blades + 0.3 * R.hash01(seed, k))
        dx, dy = 0.32 * s * math.cos(a), 0.32 * s * math.sin(a)
        h = s * (0.8 + 0.7 * R.hash01(seed, k, 1))
        G.cyl(bm, x + dx, y + dy, 0.3 * s, z, z + h, 5, mi, r_top=0.03 * s, top=True, bottom=True)


def lump(bm, x, y, z, rx, ry, rz, seed, mi=0, sub=1):
    """울퉁불퉁한 덩어리(이끼·덤불·흙더미)"""
    import roma_props as RP
    return RP._blob(bm, x, y, z, rx, ry, rz, sub, 0.25, seed, mi)


def ell_pt(s, d, z):
    """콜로세움 외곽 타원 기준점(호 길이 s, 안쪽 깊이 d, 높이 z) → HERO_root 지역 좌표"""
    C = _C()
    p = C.E.M(s, d, z)
    return Vector((p.x + C.CX, p.y + C.CY, z))


def ell_band(bm, d0, d1, z, mi=0, n=200, side=False, mi_side=0):
    """콜로세움 타원 띠 윗면(깊이 d0~d1, d는 안쪽 +). uv = (s, d). side=True면 d1 가장자리 옆면(z 0~z)"""
    C = _C()
    uvl = bm.loops.layers.uv.verify()
    L = C.E.L
    ss = [L * k / n for k in range(n)]
    a = [bm.verts.new(ell_pt(s, d0, z)) for s in ss]
    b = [bm.verts.new(ell_pt(s, d1, z)) for s in ss]
    out = []
    for k in range(n):
        k2 = (k + 1) % n
        s0, s1 = ss[k], (ss[k2] if k2 else L)
        f = bm.faces.new([a[k], b[k], b[k2], a[k2]])
        f.material_index = mi
        up_faces([f])
        for lp in f.loops:
            v = lp.vert
            lp[uvl].uv = (s0 if (v == a[k] or v == b[k]) else s1, d0 if (v == a[k] or v == a[k2]) else d1)
        out.append(f)
    if side:
        lo = [bm.verts.new(ell_pt(s, d1, 0.0)) for s in ss]
        for k in range(n):
            k2 = (k + 1) % n
            s0, s1 = ss[k], (ss[k2] if k2 else L)
            f = bm.faces.new([b[k], b[k2], lo[k2], lo[k]])
            f.material_index = mi_side
            f.normal_update()
            c = f.calc_center_median()
            if (c.x - C.CX) * f.normal.x + (c.y - C.CY) * f.normal.y < 0:
                f.normal_flip()
            for lp in f.loops:
                v = lp.vert
                lp[uvl].uv = (s0 if (v == b[k] or v == lo[k]) else s1, v.co.z)
            out.append(f)
    return out


def ell_s_of_az(az_deg, n=720):
    """평면 방위각(°)에 가장 가까운 외곽 타원 호 길이 s"""
    C = _C()
    best, bs = 1e9, 0.0
    for k in range(n):
        s = C.E.L * k / n
        d = abs(((C.E.az(s) - az_deg) + 180.0) % 360.0 - 180.0)
        if d < best:
            best, bs = d, s
    return bs
