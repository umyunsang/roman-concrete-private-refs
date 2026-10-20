# roma_render — 회차 렌더(지도 전체 + 요소별 확대)와 실루엣·앵커 내보내기. 조명·AO·그림자 없는 평면 일러스트(EEVEE, 방출 재질). 담당: bglobal
# b5(bglobal) 더한 것: CROPS 갱신(hero·suburb_far·nero_basilica) · export_sil(n, roots=None) → rounds/b{n}/sil.json(D11)
import bpy, os, json, math, time
import roma_kit as R
BZ = '/Users/um-yunsang/roman-concrete-private-refs/.work/blender'
PAGE = (420.0, 594.0)
# 요소별 확대 상자(포스터 화면 mm). 비평가·워커가 같은 상자를 본다
CROPS_B6 = {                                # 20:01 d5 배치(b6, 보관)
    'hero': (226.0, 204.0, 424.0, 364.0), 'city': (0.0, 112.0, 248.0, 392.0), 'baths': (240.0, 98.0, 424.0, 222.0),
    'suburb_far': (262.0, 378.0, 424.0, 474.0), 'coast': (0.0, 308.0, 292.0, 480.0), 'nero': (226.0, 270.0, 264.0, 314.0), 'river': (120.0, 92.0, 424.0, 360.0),
}
CROPS = {                                   # b7(d7 14차 배치) — 건물별 비교 그림 10장용
    'hero': (166.0, 196.0, 294.0, 322.0),
    'acropolis': (50.0, 118.0, 180.0, 238.0),
    'band_aqueduct': (240.0, 92.0, 424.0, 232.0),
    'market': (262.0, 272.0, 394.0, 382.0),
    'maxentius': (4.0, 274.0, 98.0, 348.0),
    'marcellus': (0.0, 220.0, 86.0, 286.0),
    'mausoleum_bridge': (120.0, 318.0, 252.0, 400.0),
    'portus': (0.0, 360.0, 175.0, 478.0),
    'metella': (286.0, 384.0, 424.0, 478.0),
}

def render_round(n, ppm_full=3.0, ppm_crop=8.0, samples=32, crops=True):
    d = os.path.join(BZ, 'rounds', 'b%d' % n)
    os.makedirs(os.path.join(d, 'crops'), exist_ok=True)
    R.render_region((0.0, 0.0, 420.0, 594.0), ppm_full, samples, os.path.join(d, 'map.png'))
    if crops:
        for k, b in CROPS.items():
            R.render_region(b, ppm_crop, samples, os.path.join(d, 'crops', k + '.png'))
    return d

# ───────────────────────── 실루엣·앵커 내보내기(D11) ─────────────────────────
SIL_SKIP_COLLS = ('PROTO',)
SIL_SKIP_PREFIX = ('GROUND_',)          # 땅 채움(땅 판·길·밭·나무 무리)은 기본 목록에서 뺀다(이름을 주면 잰다)
_RENDER_TYPES = {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'VOLUME', 'POINTCLOUD', 'CURVES', 'GPENCIL', 'GREASEPENCIL'}

def sil_roots():
    """기본 측정 대상: PROTO 밖 컬렉션의 '*_root' 오브젝트(중첩 루트 포함, GROUND_* 제외)"""
    out = []
    for o in bpy.context.scene.objects:
        if not o.name.endswith('_root') or o.name.startswith(SIL_SKIP_PREFIX):
            continue
        if any(c.name in SIL_SKIP_COLLS for c in o.users_collection):
            continue
        out.append(o.name)
    return sorted(out)

def _root_kids(root):
    return [root] + list(root.children_recursive)

def _screen_box(obs):
    import numpy as np
    xs0, ys0, xs1, ys1 = [], [], [], []
    rt = np.array(R.RIGHT, np.float64); up = np.array(R.UP, np.float64)
    for o in obs:
        if o.type != 'MESH' or o.hide_render or len(o.data.vertices) == 0:
            continue
        n = len(o.data.vertices)
        co = np.empty(n * 3, np.float64); o.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        M = np.array(o.matrix_world, np.float64)
        w = co @ M[:3, :3].T + M[:3, 3]
        sx = R.K * (w @ rt); sy = -R.K * (w @ up)
        xs0.append(sx.min()); xs1.append(sx.max()); ys0.append(sy.min()); ys1.append(sy.max())
    if not xs0:
        return None
    return (float(min(xs0)), float(min(ys0)), float(max(xs1)), float(max(ys1)))

def _snap(b, ppm, pad):
    x0 = max(0.0, math.floor((b[0] - pad) * ppm) / ppm); y0 = max(0.0, math.floor((b[1] - pad) * ppm) / ppm)
    x1 = min(PAGE[0], math.ceil((b[2] + pad) * ppm) / ppm); y1 = min(PAGE[1], math.ceil((b[3] + pad) * ppm) / ppm)
    return (x0, y0, x1, y1)

def _components(mask):
    """8-연결 성분(가로 런 + 합집합 찾기). 반환: (런 목록[(행, 시작, 끝)], 런별 성분 번호, {성분: 넓이 px})"""
    import numpy as np
    H, W = mask.shape
    runs, rows = [], []
    for y in range(H):
        r = mask[y]
        if not r.any():
            rows.append([]); continue
        d = np.diff(np.concatenate(([0], r.astype(np.int8), [0])))
        st = np.nonzero(d == 1)[0]; en = np.nonzero(d == -1)[0]
        cur = []
        for s, e in zip(st, en):
            cur.append(len(runs)); runs.append((y, int(s), int(e)))
        rows.append(cur)
    par = list(range(len(runs)))
    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for y in range(1, H):
        prev, cur = rows[y - 1], rows[y]
        if not prev or not cur:
            continue
        j = 0
        for i in cur:
            _, s, e = runs[i]
            while j < len(prev) and runs[prev[j]][2] < s:
                j += 1
            k = j
            while k < len(prev) and runs[prev[k]][1] <= e:
                a, b = find(i), find(prev[k])
                if a != b:
                    par[a] = b
                k += 1
    lab = [find(i) for i in range(len(runs))]
    area = {}
    for (y, s, e), l in zip(runs, lab):
        area[l] = area.get(l, 0) + (e - s)
    return runs, lab, area

_NB = [(0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1)]     # (dy, dx): 서·북서·북·북동·동·남동·남·남서(화면 시계 방향)

def _trace(m):
    """이진 그림 m(성분 하나)의 바깥 윤곽(무어 이웃 추적). 반환: [(행, 열), …]"""
    import numpy as np
    H, W = m.shape
    ys, xs = np.nonzero(m)
    if len(ys) == 0:
        return []
    i0 = int(np.argmin(ys * W + xs)); sy, sx = int(ys[i0]), int(xs[i0])
    def inside(y, x):
        return 0 <= y < H and 0 <= x < W and bool(m[y, x])
    out = [(sy, sx)]
    cy, cx, b = sy, sx, 0
    first = None
    for _ in range(4 * int(m.sum()) + 16):
        nxt = None
        for k in range(8):
            d = (b + 1 + k) % 8
            ny, nx = cy + _NB[d][0], cx + _NB[d][1]
            if inside(ny, nx):
                pd = (d - 1) % 8
                py, px = cy + _NB[pd][0], cx + _NB[pd][1]
                nxt = (ny, nx, _NB.index((py - ny, px - nx)))
                break
        if nxt is None:
            break
        if first is None:
            first = nxt[:2]
        elif (cy, cx) == (sy, sx) and nxt[:2] == first:
            break
        cy, cx, b = nxt
        if (cy, cx) == (sy, sx) and len(out) > 1:
            continue
        out.append((cy, cx))
    return out

def _rdp(pts, eps):
    if len(pts) < 3:
        return list(pts)
    keep = [False] * len(pts); keep[0] = keep[-1] = True
    st = [(0, len(pts) - 1)]
    while st:
        a, b = st.pop()
        ax, ay = pts[a]; bx, by = pts[b]
        dx, dy = bx - ax, by - ay; L = math.hypot(dx, dy)
        best, bi = -1.0, -1
        for i in range(a + 1, b):
            px, py = pts[i]
            dd = abs(dy * (px - ax) - dx * (py - ay)) / L if L > 1e-12 else math.hypot(px - ax, py - ay)
            if dd > best:
                best, bi = dd, i
        if bi > 0 and best > eps:
            keep[bi] = True; st.append((a, bi)); st.append((bi, b))
    return [p for p, k in zip(pts, keep) if k]

def _simplify(poly, max_pts=96, eps=0.5):
    """닫힌 윤곽 → max_pts 점 이하(RDP, 허용 오차를 키워 가며)"""
    if len(poly) <= max_pts:
        return poly
    far = max(range(len(poly)), key=lambda i: (poly[i][0] - poly[0][0]) ** 2 + (poly[i][1] - poly[0][1]) ** 2)
    out = poly
    while True:
        a = _rdp(poly[:far + 1], eps); b = _rdp(poly[far:] + [poly[0]], eps)
        out = a[:-1] + b[:-1]
        if len(out) <= max_pts or eps > 1e4:
            return out
        eps *= 1.4

def _sil_one(root, ppm, pad, samples, max_pts, tmp):
    """루트 하나만 보이게(다른 오브젝트 hide_render를 잠깐 켜고 try/finally로 되돌림) 알파 렌더 → 실루엣"""
    import numpy as np
    sc = bpy.context.scene
    keep = set(o.name for o in _root_kids(root))
    sb = _screen_box(_root_kids(root))
    if sb is None:
        return {'id': root.name, 'error': '보이는 메시 없음'}, None, None
    rb = _snap(sb, ppm, pad)
    changed = []
    ft = sc.render.film_transparent
    try:
        for o in sc.objects:
            if o.name in keep or o.hide_render:
                continue
            if o.type in _RENDER_TYPES or (o.type == 'EMPTY' and o.instance_type == 'COLLECTION' and o.instance_collection is not None):
                o.hide_render = True; changed.append(o)
        sc.render.film_transparent = True
        R.render_region(rb, ppm, samples, tmp)
    finally:
        for o in changed:
            o.hide_render = False
        sc.render.film_transparent = ft
    a = R.png_rgba(tmp)
    mask = a[:, :, 3] >= 128
    H, W = mask.shape
    ent = {'id': root.name, 'coll': [c.name for c in root.users_collection], 'render_box': [round(v, 3) for v in rb],
           'proj_box': [round(v, 3) for v in sb], 'px': [W, H], 'ppm': ppm}
    if not mask.any():
        ent['error'] = '렌더에 불투명 화소 없음'
        return ent, rb, mask
    ys, xs = np.nonzero(mask)
    box = [rb[0] + xs.min() / ppm, rb[1] + ys.min() / ppm, rb[0] + (xs.max() + 1) / ppm, rb[1] + (ys.max() + 1) / ppm]
    runs, lab, area = _components(mask)
    best = max(area, key=area.get)
    mm = np.zeros_like(mask)
    for (y, s, e), l in zip(runs, lab):
        if l == best:
            mm[y, s:e] = True
    cont = _trace(mm)
    poly = _simplify([(rb[0] + (x + 0.5) / ppm, rb[1] + (y + 0.5) / ppm) for (y, x) in cont], max_pts)
    ys2, xs2 = np.nonzero(mm)
    ent.update({
        'box': [round(v, 3) for v in box],
        'box_area': round((box[2] - box[0]) * (box[3] - box[1]), 1),
        'area': round(float(mask.sum()) / (ppm * ppm), 1),
        'area_main': round(area[best] / (ppm * ppm), 1),
        'box_main': [round(rb[0] + xs2.min() / ppm, 3), round(rb[1] + ys2.min() / ppm, 3),
                     round(rb[0] + (xs2.max() + 1) / ppm, 3), round(rb[1] + (ys2.max() + 1) / ppm, 3)],
        'components': len(area),
        'poly': [[round(x, 2), round(y, 2)] for x, y in poly],
        'n_poly': len(poly),
    })
    return ent, rb, mask

def _owner_root(o):
    p = o.parent
    while p is not None:
        if p.name.endswith('_root'):
            return p.name
        p = p.parent
    return None

def export_sil(n, roots=None, ppm=3.0, pad=1.0, samples=8, max_pts=96, budget_s=70.0, out=None):
    """D11: 루트마다 알파 렌더(3 px/mm)로 실루엣 {id, box, poly(≤96점), area}을 재고, ANCHOR_* Empty의 화면 좌표와 함께
    .work/blender/rounds/b{n}/sil.json에 쓴다(있으면 루트별로 덮어써 합친다). 다른 오브젝트는 잠깐 hide_render로 숨겼다 되돌린다.
    roots: None이면 sil_roots() 전부를 budget_s(초) 안에서 차례로 — 명령 하나 90초 규칙에 맞춰 남은 것은 'pending'으로 돌려준다.
    한 명령에 루트 하나씩 부르려면 roots=['HERO_Colosseum_root'] 꼴로 준다. out을 주면 그 경로에 쓴다(시험용).
    반환: {'path', 'done', 'pending', 'anchors'}"""
    import numpy as np
    t0 = time.time()
    if out:
        path = out
        os.makedirs(os.path.dirname(path), exist_ok=True)
    else:
        d = os.path.join(BZ, 'rounds', 'b%d' % n)
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, 'sil.json')
    data = {}
    if os.path.exists(path):
        try:
            data = json.load(open(path, encoding='utf-8'))
        except Exception:
            data = {}
    data.setdefault('roots', {}); data.setdefault('anchors', {})
    data.update({'round': 'b%d' % n, 'ppm': ppm, 'page_mm': list(PAGE), 'unit': '포스터 화면 mm(왼쪽 위 원점, y 아래로)',
                 'note': 'box = 실제로 그린 외곽 상자(알파 ≥ 0.5), area = 실루엣 넓이 mm², poly = 가장 큰 성분의 바깥 윤곽(≤96점). '
                         'anchors: ANCHOR_* Empty의 화면 점(pt)과 그 루트 실루엣 위 여부(on_sil)'})
    todo = list(roots) if roots else sil_roots()
    tmp = os.path.join(R.WORK, 'bglobal_sil_tmp.png')
    done, pending, masks = [], [], {}
    for i, rn in enumerate(todo):
        if done and time.time() - t0 > budget_s:
            pending = todo[i:]
            break
        root = bpy.data.objects.get(rn)
        if root is None:
            data['roots'][rn] = {'id': rn, 'error': '루트 없음'}
            continue
        ent, rb, mask = _sil_one(root, ppm, pad, samples, max_pts, tmp)
        ent['t_s'] = round(time.time() - t0, 2)
        data['roots'][rn] = ent
        if rb is not None and mask is not None:
            masks[rn] = (rb, mask)
        done.append(rn)
    anc = data['anchors']
    for o in bpy.context.scene.objects:
        if not o.name.startswith('ANCHOR_'):
            continue
        w = o.matrix_world.translation
        x, y = R.scr(w)
        own = _owner_root(o)
        e = anc.get(o.name, {})
        e.update({'pt': [round(x, 3), round(y, 3)], 'world': [round(w.x, 3), round(w.y, 3), round(w.z, 3)], 'root': own})
        if own in masks:
            rb, mask = masks[own]
            px, py = int((x - rb[0]) * ppm), int((y - rb[1]) * ppm)
            H, W = mask.shape
            win = mask[max(0, py - 1):min(H, py + 2), max(0, px - 1):min(W, px + 2)]
            e['on_sil'] = bool(win.any()) if win.size else False
        anc[o.name] = e
    names = set(o.name for o in bpy.context.scene.objects if o.name.startswith('ANCHOR_'))
    for k in list(anc.keys()):
        if k not in names:
            anc.pop(k)
    data['updated'] = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return {'path': path, 'done': done, 'pending': pending, 'anchors': len(anc), 't_s': round(time.time() - t0, 2)}
