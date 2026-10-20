
# roma_kit — 로마 콘크리트 포스터 중앙 지도용 공용 도구(실행 중인 Blender 안에서 쓴다)
import bpy, bmesh, math, random, bisect
from mathutils import Vector, Matrix

C30 = math.cos(math.radians(30.0))
K = math.sqrt(1.5)                       # 화면 mm / 카메라 평면 BU
RIGHT = Vector((1, 1, 0)).normalized()   # 카메라 오른쪽
UP = Vector((-1, 1, 2)).normalized()     # 카메라 위
FWD = Vector((-1, 1, -1)).normalized()   # 카메라가 보는 방향

def to_screen(X, Y, Z=0.0):
    return (C30 * (X - Y), 0.5 * (X + Y) - Z)

def to_plan(x, y):
    a = x / C30
    return ((a + 2 * y) / 2.0, (2 * y - a) / 2.0)

def P(X, Y, Z=0.0):
    """설계 평면(Y 아래로) → Blender 월드"""
    return Vector((X, -Y, Z))

def scr(v):
    """Blender 월드 점 → 포스터 화면 mm"""
    return (K * v.dot(RIGHT), -K * v.dot(UP))

def plan_az(dx, dy):
    """Blender 상대 벡터 → 설계 평면 방위각(X→Y 반시계, 도)"""
    return (-math.degrees(math.atan2(dy, dx))) % 360.0

def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c

def clear_coll(name):
    c = bpy.data.collections.get(name)
    if not c:
        return
    for ob in list(c.all_objects):
        me = ob.data if ob.type == 'MESH' else None
        bpy.data.objects.remove(ob, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)

def frame_camera(x0, y0, x1, y1, ppm=8.0, name='CAM_ISO', dist=2500.0):
    """포스터 화면 사각형(mm)을 정확히 담는 등각 정사영 카메라"""
    cam = bpy.data.objects.get(name)
    if cam is None:
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        bpy.context.scene.collection.objects.link(cam)
    cd = cam.data
    cd.type = 'ORTHO'
    cd.sensor_fit = 'HORIZONTAL'
    cd.ortho_scale = (x1 - x0) / K
    cd.clip_start = 1.0
    cd.clip_end = dist * 2 + 3000
    cam.rotation_mode = 'XYZ'
    cam.rotation_euler = (math.radians(54.7356103), 0.0, math.radians(45.0))
    X, Y = to_plan((x0 + x1) / 2, (y0 + y1) / 2)
    cam.location = P(X, Y, 0) - FWD * dist
    sc = bpy.context.scene
    sc.camera = cam
    sc.render.resolution_x = int(round((x1 - x0) * ppm))
    sc.render.resolution_y = int(round((y1 - y0) * ppm))
    sc.render.resolution_percentage = 100
    return cam

def mesh_obj(name, verts, faces, mat=None, coll_=None, parent=None, smooth=False, uvs=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    if uvs is not None:
        uvl = me.uv_layers.new(name='UVMap')
        for poly in me.polygons:
            for li in poly.loop_indices:
                vi = me.loops[li].vertex_index
                uvl.data[li].uv = uvs[vi]
    me.validate(clean_customdata=False)
    me.update()
    ob = bpy.data.objects.new(name, me)
    (coll_ or bpy.context.scene.collection).objects.link(ob)
    if mat is not None:
        me.materials.append(mat)
    if parent is not None:
        ob.parent = parent
    for p in me.polygons:
        p.use_smooth = smooth
    return ob

def bm_to_obj(bm, name, mat=None, coll_=None, parent=None, smooth=False, recalc=True):
    if recalc:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    (coll_ or bpy.context.scene.collection).objects.link(ob)
    if mat is not None:
        if isinstance(mat, (list, tuple)):
            for m in mat:
                me.materials.append(m)
        else:
            me.materials.append(mat)
    if parent is not None:
        ob.parent = parent
    for p in me.polygons:
        p.use_smooth = smooth
    return ob

class Ell:
    """타원(반축 a, b, Blender 회전 rot도). 호 길이 s ↔ 점·접선·바깥 법선. M(s, d, z): d는 안쪽 깊이"""
    def __init__(self, a, b, rot_deg=45.0, n=6000):
        self.a, self.b = a, b
        self.rot = math.radians(rot_deg)
        self.cr, self.sr = math.cos(self.rot), math.sin(self.rot)
        self.ts = [2 * math.pi * i / n for i in range(n + 1)]
        pts = [self._p(t) for t in self.ts]
        self.cum = [0.0]
        for i in range(n):
            self.cum.append(self.cum[-1] + (pts[i + 1] - pts[i]).length)
        self.L = self.cum[-1]
    def _p(self, t):
        x, y = self.a * math.cos(t), self.b * math.sin(t)
        return Vector((self.cr * x - self.sr * y, self.sr * x + self.cr * y, 0.0))
    def t_of_s(self, s):
        s %= self.L
        i = bisect.bisect_right(self.cum, s) - 1
        i = min(max(i, 0), len(self.cum) - 2)
        f = (s - self.cum[i]) / max(1e-12, self.cum[i + 1] - self.cum[i])
        return self.ts[i] + f * (self.ts[i + 1] - self.ts[i])
    def frame(self, s):
        t = self.t_of_s(s)
        p = self._p(t)
        dx, dy = -self.a * math.sin(t), self.b * math.cos(t)
        T = Vector((self.cr * dx - self.sr * dy, self.sr * dx + self.cr * dy, 0.0)).normalized()
        N = Vector((T.y, -T.x, 0.0))
        return p, T, N
    def M(self, s, d, z):
        p, T, N = self.frame(s)
        return Vector((p.x - N.x * d, p.y - N.y * d, z))
    def az(self, s):
        p, T, N = self.frame(s)
        return plan_az(p.x, p.y)

def hash01(*k):
    h = 2166136261
    for v in k:
        h = ((h ^ (int(v * 1000003) & 0xffffffff)) * 16777619) & 0xffffffff
    return (h % 100000) / 100000.0


def render_region(box, ppm, samples, path, page=(420.0, 594.0)):
    """포스터 전체 카메라 그대로, 화면 상자(mm)만 테두리 렌더. samples는 EEVEE 표본 수(Cycles 값도 함께).
    b5(bglobal): 렌더하는 동안만 해상도·테두리·파일 설정·표본 수를 바꾸고, 끝나면(오류가 나도) 원래 값으로 되돌린다"""
    sc = bpy.context.scene
    rd = sc.render
    ims = rd.image_settings
    keep = dict(rx=rd.resolution_x, ry=rd.resolution_y, rp=rd.resolution_percentage, ub=rd.use_border, uc=rd.use_crop_to_border,
                b=(rd.border_min_x, rd.border_max_x, rd.border_min_y, rd.border_max_y), fp=rd.filepath,
                ff=ims.file_format, cm=ims.color_mode, cd=ims.color_depth)
    cyc = getattr(sc, 'cycles', None)
    eev = getattr(sc, 'eevee', None)
    keep_cs = getattr(cyc, 'samples', None) if cyc is not None else None
    keep_es = getattr(eev, 'taa_render_samples', None) if eev is not None else None
    keep_cam = sc.camera                                   # 17:34: 장면 카메라가 CAM_MAPWIN(지도 창)이어도 포스터 렌더는 CAM_ISO로
    iso = bpy.data.objects.get('CAM_ISO')
    try:
        if iso is not None:
            sc.camera = iso
        rd.resolution_x = int(round(page[0] * ppm)); rd.resolution_y = int(round(page[1] * ppm)); rd.resolution_percentage = 100
        rd.use_border = True; rd.use_crop_to_border = True
        rd.border_min_x = box[0] / page[0]; rd.border_max_x = box[2] / page[0]
        rd.border_min_y = 1.0 - box[3] / page[1]; rd.border_max_y = 1.0 - box[1] / page[1]
        if keep_cs is not None:
            cyc.samples = samples
        if keep_es is not None:
            eev.taa_render_samples = max(1, int(samples))
        ims.file_format = 'PNG'; ims.color_mode = 'RGBA'; ims.color_depth = '8'
        rd.filepath = path
        bpy.ops.render.render(write_still=True)
    finally:
        rd.resolution_x, rd.resolution_y, rd.resolution_percentage = keep['rx'], keep['ry'], keep['rp']
        rd.border_min_x, rd.border_max_x, rd.border_min_y, rd.border_max_y = keep['b']
        rd.use_border, rd.use_crop_to_border = keep['ub'], keep['uc']
        rd.filepath = keep['fp']
        try:
            ims.file_format = keep['ff']; ims.color_mode = keep['cm']; ims.color_depth = keep['cd']
        except Exception:
            pass
        if keep_cs is not None:
            cyc.samples = keep_cs
        if keep_es is not None:
            eev.taa_render_samples = keep_es
        sc.camera = keep_cam
    return path

# ───────────────────────── 렌더 결과 읽기 · 색 실측 · 표현 레이어 감사(bglobal, b5) ─────────────────────────
WORK = '/Users/um-yunsang/roman-concrete-private-refs/.work/blender/rounds/work'

def png_rgba(path):
    """PNG → numpy uint8 배열 (높이, 폭, 4), 위 행부터. Blender 이미지 버퍼 값을 그대로 읽는다(색 관리 변환 없음)"""
    import numpy as np
    img = bpy.data.images.load(path, check_existing=False)
    try:
        w, h = img.size
        a = np.empty(w * h * 4, np.float32)
        img.pixels.foreach_get(a)
        a = np.clip(a.reshape(h, w, 4)[::-1] * 255.0 + 0.5, 0, 255).astype(np.uint8)
    finally:
        bpy.data.images.remove(img)
    return a

def sample_rgb(box, ppm=4.0, samples=8, path=None, src=None, src_box=(0.0, 0.0, 420.0, 594.0), alpha_min=250):
    """화면 상자 box(mm)의 렌더 RGB(sRGB 0~255)를 잰다. src가 없으면 그 상자만 렌더해(render_region) 읽고,
    src(PNG 경로)를 주면 그 그림(src_box를 담은 렌더, 예: rounds/bN/map.png = 전체 쪽)에서 box 부분만 잘라 잰다.
    불투명 화소(알파 ≥ alpha_min)만 센다. 반환: {'median', 'mean', 'mode', 'mode_frac', 'n', 'opaque_frac', 'box', 'src'}"""
    import numpy as np
    if src is None:
        p = path or (WORK + '/bglobal_sample.png')
        render_region(box, ppm, samples, p)
        a = png_rgba(p)
    else:
        p = src
        A = png_rgba(src)
        H, W = A.shape[:2]
        kx = W / (src_box[2] - src_box[0]); ky = H / (src_box[3] - src_box[1])
        x0 = int(round((box[0] - src_box[0]) * kx)); x1 = int(round((box[2] - src_box[0]) * kx))
        y0 = int(round((box[1] - src_box[1]) * ky)); y1 = int(round((box[3] - src_box[1]) * ky))
        a = A[max(0, y0):max(0, y1), max(0, x0):max(0, x1)]
    px = a.reshape(-1, 4)
    op = px[px[:, 3] >= alpha_min][:, :3].astype(np.int64)
    out = {'box': [float(v) for v in box], 'src': p, 'n': int(len(op)), 'opaque_frac': round(len(op) / max(1, len(px)), 4)}
    if len(op) == 0:
        out.update(median=None, mean=None, mode=None, mode_frac=0.0)
        return out
    key = op[:, 0] * 65536 + op[:, 1] * 256 + op[:, 2]
    u, c = np.unique(key, return_counts=True)
    m = int(u[np.argmax(c)])
    out['median'] = [int(v) for v in np.median(op, axis=0)]
    out['mean'] = [round(float(v), 1) for v in op.mean(axis=0)]
    out['mode'] = [m // 65536, (m // 256) % 256, m % 256]
    out['mode_frac'] = round(float(c.max()) / len(op), 4)
    return out

def layer_audit(coll, roots=None, need=tuple(range(7)), detail=False):
    """표현 레이어 감사(D10). coll(이름 또는 컬렉션)의 루트(이름이 '_root'로 끝나는 오브젝트)마다:
    층별 메시 수(이름의 '_L{n}_'), 빠진 층, 빈 메시(면 0), 층 표시가 없는 메시. 그리고 루트 밖 메시, 조명, Principled·이미지 텍스처 재질.
    반환(JSON으로 쓸 수 있는 dict): {'coll', 'n_roots', 'ok', 'fail', 'roots': {루트: {...}}, 'loose', 'lights', 'principled', 'image_tex'}"""
    import re
    c = bpy.data.collections.get(coll) if isinstance(coll, str) else coll
    if c is None:
        return {'coll': coll, 'error': '컬렉션 없음'}
    obs = list(c.all_objects)
    if roots is None:
        rts = [o for o in obs if o.name.endswith('_root')]
    else:
        rts = [bpy.data.objects[r] if isinstance(r, str) else r for r in roots]
    rx = re.compile(r'_L(\d)_')
    res = {}
    under = set()
    for r in sorted(rts, key=lambda o: o.name):
        ms = [o for o in r.children_recursive if o.type == 'MESH']
        cnt, empty, untag = {}, [], []
        faces = 0
        for o in ms:
            under.add(o.name)
            nf = len(o.data.polygons)
            faces += nf
            m = rx.search(o.name)
            if not m:
                untag.append(o.name)
                continue
            n = int(m.group(1))
            cnt[n] = cnt.get(n, 0) + 1
            if nf == 0:
                empty.append(o.name)
        miss = [n for n in need if cnt.get(n, 0) == 0]
        ent = {'meshes': len(ms), 'faces': faces, 'layers': {('L%d' % k): v for k, v in sorted(cnt.items())},
               'missing': ['L%d' % n for n in miss], 'empty': empty, 'untagged': untag[:20] if not detail else untag,
               'n_untagged': len(untag), 'ok': (not miss) and (not empty)}
        res[r.name] = ent
    loose = [o.name for o in obs if o.type == 'MESH' and o.name not in under
             and not o.name.startswith(('P_', 'X_CUT_')) and not o.name.endswith('_prev')]
    used = set()
    for o in obs:
        if o.type == 'MESH':
            for s in o.material_slots:
                if s.material is not None:
                    used.add(s.material)
    princ = sorted(m.name for m in used if m.node_tree and any(n.type == 'BSDF_PRINCIPLED' for n in m.node_tree.nodes))
    imgt = sorted(m.name for m in used if m.node_tree and any(n.type == 'TEX_IMAGE' for n in m.node_tree.nodes))
    lights = sorted(o.name for o in bpy.context.scene.objects if o.type == 'LIGHT')
    ok = sorted(k for k, v in res.items() if v['ok'])
    fail = {k: {'missing': v['missing'], 'empty': v['empty'][:5]} for k, v in res.items() if not v['ok']}
    return {'coll': c.name, 'n_roots': len(res), 'ok': len(ok), 'fail': fail, 'roots': res, 'loose': loose[:30], 'n_loose': len(loose),
            'lights': lights, 'principled': princ, 'image_tex': imgt}


# ───────────────────────── 지도 창(설계 window_rect_mm) 카메라 · 뷰포트 · 창 안 검사(17:34 사용자) ─────────────────────────
MAP_WINDOW = (0.0, 92.0, 420.0, 478.0)          # 포스터 화면 mm(x0, y0, x1, y1). 설계 d5 frame.stage.rect / window_rect_mm


def map_window_rect(spec=None):
    """설계 spec의 지도 창(window_rect_mm → frame.stage.rect 순). 없으면 MAP_WINDOW"""
    try:
        S = spec or __import__('json').load(open('/Users/um-yunsang/roman-concrete-private-refs/.work/design/current/out/spec.json', encoding='utf-8'))
        r = (S.get('frame', {}).get('window_rect_mm') or S.get('core_map', {}).get('window_rect_mm')
             or S.get('frame', {}).get('stage', {}).get('rect'))
        if r and len(r) == 4:
            return tuple(float(v) for v in r)
    except Exception:
        pass
    return MAP_WINDOW


def map_window_camera(rect=None, name='CAM_MAPWIN', dist=2500.0, ppm=3.0, set_scene=True):
    """CAM_ISO와 같은 회전·정사영(1 화면 mm = 1 mm)으로 지도 창 rect만 정확히 담는 카메라.
    ortho_scale = 창 폭 / K(가로 맞춤), 창 가운데를 겨눈다. set_scene이면 장면 카메라·해상도(창 비율)를 이 카메라로 둔다
    (render_region은 렌더하는 동안 CAM_ISO로 바꿨다가 되돌린다)"""
    x0, y0, x1, y1 = rect or map_window_rect()
    cam = bpy.data.objects.get(name)
    if cam is None:
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        bpy.context.scene.collection.objects.link(cam)
    cd = cam.data
    cd.type = 'ORTHO'; cd.sensor_fit = 'HORIZONTAL'
    cd.ortho_scale = (x1 - x0) / K
    cd.shift_x = 0.0; cd.shift_y = 0.0
    cd.clip_start = 1.0; cd.clip_end = dist * 2 + 3000
    cd.show_passepartout = True; cd.passepartout_alpha = 0.9
    cd.show_limits = False
    cam.rotation_mode = 'XYZ'
    cam.rotation_euler = (math.radians(54.7356103), 0.0, math.radians(45.0))
    X, Y = to_plan((x0 + x1) / 2, (y0 + y1) / 2)
    cam.location = P(X, Y, 0) - FWD * dist
    if set_scene:
        sc = bpy.context.scene
        sc.camera = cam
        sc.render.resolution_x = int(round((x1 - x0) * ppm))
        sc.render.resolution_y = int(round((y1 - y0) * ppm))
        sc.render.resolution_percentage = 100
    return cam


def viewport_to_camera(cam_name='CAM_MAPWIN'):
    """3D 뷰포트를 장면 카메라(지도 창) 시점으로: 카메라 보기 + 프레임 맞춤"""
    cam = bpy.data.objects.get(cam_name)
    done = 0
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            sp = area.spaces.active
            r3 = sp.region_3d
            if cam is not None:
                sp.camera = cam
                sp.use_local_camera = False
            r3.view_perspective = 'CAMERA'
            region = next((rg for rg in area.regions if rg.type == 'WINDOW'), None)
            if region is not None:
                try:
                    with bpy.context.temp_override(window=win, area=area, region=region):
                        bpy.ops.view3d.view_center_camera()
                except Exception:
                    pass
            done += 1
    return done


def _screen_bbox(obs, top_only=False):
    import numpy as np
    xs0 = ys0 = 1e9; xs1 = ys1 = -1e9; n = 0
    Rv = np.array(RIGHT); Uv = np.array(UP)
    for ob in obs:
        if ob.type != 'MESH' or ob.hide_render or not ob.data.vertices:
            continue
        nv = len(ob.data.vertices)
        co = np.empty(nv * 3); ob.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        M = np.array(ob.matrix_world); w = co @ M[:3, :3].T + M[:3, 3]
        if top_only:
            w = w[w[:, 2] > -0.1]
            if not len(w):
                continue
        sx = K * (w @ Rv); sy = -K * (w @ Uv)
        xs0 = min(xs0, sx.min()); xs1 = max(xs1, sx.max()); ys0 = min(ys0, sy.min()); ys1 = max(ys1, sy.max()); n += 1
    return (round(float(xs0), 2), round(float(ys0), 2), round(float(xs1), 2), round(float(ys1), 2)) if n else None


def check_in_window(rect=None, margin=0.0, colls=('HERO_Colosseum', 'LM_City', 'LM_Baths', 'LM_Suburb', 'LM_Coast', 'MAP_Ground')):
    """루트마다 투영 실루엣(높이 포함, 메시 꼭짓점) 상자가 지도 창(+margin) 안인지. 반환:
    {'rect', 'outside': {루트: {'bbox', 'over': [왼, 위, 오른, 아래] mm}}, 'land_below': 땅 윗면이 창 아래로 내려간 양,
     'water_cut': 강·바다가 창 경계에서 끊기는지(창 밖으로 나간 양)}"""
    x0, y0, x1, y1 = rect or map_window_rect()
    out = {'rect': [x0, y0, x1, y1], 'outside': {}, 'inside': [], 'land_below': None, 'water_beyond': {}}
    for cn in colls:
        c = bpy.data.collections.get(cn)
        if c is None:
            continue
        for rt in [o for o in c.objects if o.name.endswith('_root')]:
            if rt.name in ('HERO_root',):
                continue
            bb = _screen_bbox(list(rt.children_recursive))
            if bb is None:
                continue
            over = [round(max(0.0, (x0 - margin) - bb[0]), 2), round(max(0.0, (y0 - margin) - bb[1]), 2),
                    round(max(0.0, bb[2] - (x1 + margin)), 2), round(max(0.0, bb[3] - (y1 + margin)), 2)]
            if any(v > 0.01 for v in over):
                out['outside'][rt.name] = {'bbox': list(bb), 'over': over}
            else:
                out['inside'].append(rt.name)
    land = bpy.data.objects.get('GROUND_Land_L0_Slab')
    if land is not None:
        bb = _screen_bbox([land], top_only=True)
        out['land_below'] = round(max(0.0, bb[3] - y1), 2) if bb else None
    for nm in ('GROUND_River_root', 'GROUND_Sea_root', 'GROUND_Falls_root'):
        rt = bpy.data.objects.get(nm)
        if rt is not None:
            bb = _screen_bbox(list(rt.children_recursive))
            if bb:
                out['water_beyond'][nm] = {'bbox': list(bb), 'beyond': [round(max(0.0, x0 - bb[0]), 2), round(max(0.0, y0 - bb[1]), 2),
                                                                          round(max(0.0, bb[2] - x1), 2), round(max(0.0, bb[3] - y1), 2)]}
    return out
