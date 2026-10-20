
# roma_props — 지도 소품 원형(링크 복제로 배치). 담당: bglobal
# b5(2026-10-19, D8·D10) 바꾼 것
#   - 모든 원형의 키(땅 z 0 → 꼭대기)를 1.0으로 정규화한다. 사람은 발~머리(머리칼 꼭대기)가 1.0이고, 머리에 인 바구니 같은 짐은 키에 넣지 않는다.
#     패키지는 배율만 곱한다: 배율 = 원하는 화면 높이(mm) = 사람 키 × D8 비례(노점 1.4 · 암포라 0.45 · 사이프러스 3.3~4.3 · 올리브 2.9 …).
#     가로 크기가 필요하면 proto_info(이름)['w'·'d'](키 1.0 기준 폭·깊이)를 쓴다. 수레 길이 2.2 → 배율 = 2.2 × 사람 키 ÷ proto_info('cart')['w'].
#   - 원형마다 표현 레이어를 면 단위로 표시해(_L) 두 가지로 만든다.
#       ① P_{이름}: 한 메시(재질 칸이 층을 나눈다). place()가 링크 복제한다 — 다른 패키지가 src.data·정점 높이를 읽으므로 그대로 둔다.
#       ② PROTO_{Obj}_root 아래 PROTO_{Obj}_L{n}_{부분}: 층마다 따로 나눈 메시(L0~L6 각 1개 이상, 빈 메시 0). place_layered()가 이 구조로 배치한다.
#   - 집 원형 3종: 붉은 기와 박공(house0~3) · 평지붕 인술라(house_flat0·1) · 안뜰 도무스(house_atrium0)
#   - 노점 차양은 흰·빨간 줄무늬만 쓴다(황토색 변형 삭제, D3 '흰·빨간 줄무늬 차양')
# 표현 레이어: L0 덩어리 · L1 깊이색(속·그늘진 안쪽을 짙은 평면색으로) · L2 부재(띠·기둥·테) · L3 표면 무늬(주름·잎결·판자·기와 줄)
#   L4 형태 디테일(팔·손·창·문·손잡이·바퀴) · L5 하이라이트(위를 보는 면·윗선에만 밝은 색 → 배치 때 돌려도 빛 방향이 같다)
#   L6 생활·식생(짐·과일·꽃·화분·밑동 풀·얼룩). L7 외곽선은 쓰지 않는다(roma_flat.OUTLINE = False).
# 조명·AO·그림자 없음. 색은 roma_flat 평면색 × ISO_TONE. 개체마다 다른 색은 var_mat(Object Info Random) — 같은 개체의
#   짙은(_DK)·밝은(_HI) 변형은 같은 위치의 색 띠를 쓰므로 바탕색과 짝이 맞는다.
# 이름·인자는 바꾸지 않는다(다른 패키지가 쓴다): var_mat · build_mats · _blob · mk_* · make_proto · build_protos · place
#   (build_protos(only=None)·place_layered·proto_info·proto_height·make_layered는 새로 더한 것)
import bpy, bmesh, math, random, re
from mathutils import Vector, Matrix
import roma_kit as R, roma_geo as G, roma_flat as FL

RAND_PROP = 'roma_rand'     # 오브젝트 사용자 속성: 1.0 + 난수(0~1). 있으면 Object Info Random 대신 쓴다(층별 배치에서 층 메시들이 같은 색 띠를 고르게)

def var_mat(name, stops_hex):
    """개체마다 다른 평면색(Object Info Random → 경계가 또렷한 색 띠) × ISO_TONE. 조명 없음.
    오브젝트에 'roma_rand'(1~2) 속성이 있으면 그 값 − 1을 난수로 쓴다(place_layered가 한 개체의 층 메시들에 같은 값을 준다)"""
    m, nt, tg = FL._base(name)
    oi = nt.nodes.new('ShaderNodeObjectInfo')
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'OBJECT'; at.attribute_name = RAND_PROP
    gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.5
    sb = nt.nodes.new('ShaderNodeMath'); sb.operation = 'SUBTRACT'; sb.inputs[1].default_value = 1.0
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'FLOAT'
    nt.links.new(at.outputs['Fac'], gt.inputs[0]); nt.links.new(at.outputs['Fac'], sb.inputs[0])
    nt.links.new(gt.outputs[0], mx.inputs['Factor'])
    nt.links.new(oi.outputs['Random'], mx.inputs['A']); nt.links.new(sb.outputs[0], mx.inputs['B'])
    rp = nt.nodes.new('ShaderNodeValToRGB'); cr = rp.color_ramp; cr.interpolation = 'CONSTANT'
    cr.elements[0].position = stops_hex[0][0]; cr.elements[0].color = (*FL.srgb(stops_hex[0][1]), 1)
    for pos, hx in stops_hex[1:]:
        e = cr.elements.new(pos); e.color = (*FL.srgb(hx), 1)
    nt.links.new(mx.outputs['Result'], rp.inputs['Fac'])
    nt.links.new(rp.outputs['Color'], tg.inputs['Color'])
    m.diffuse_color = (*FL.srgb(stops_hex[0][1]), 1)
    return m

def _shift(stops, k, toward=None):
    return [(p, FL.shade(h, k, toward)) for p, h in stops]

def _vset(M, key, name, stops, dk=0.72, hi=1.26, toward=None):
    """var_mat 세 벌: 바탕 · 짙은(L1·L3) · 밝은(L5). 색 띠 위치가 같아 한 개체 안에서 짝이 맞는다"""
    M[key] = var_mat(name, stops)
    M[key + '_DK'] = var_mat(name + 'Dk', _shift(stops, dk))
    M[key + '_HI'] = var_mat(name + 'Hi', _shift(stops, hi, toward))

def build_mats():
    P = FL.PAL
    M = {}
    cyp = [(0.0, P['cypress1']), (0.5, P['cypress2']), (0.8, P['cypress3'])]
    pine = [(0.0, P['pine1']), (0.5, P['pine2']), (0.8, P['pine3'])]
    oli = [(0.0, '#7E8A58'), (0.5, '#939A69'), (0.8, '#6A744E')]            # 은빛 세이지(LocalBanana 올리브, PAL olive보다 한 단 짙게)
    bush = [(0.0, P['grass2']), (0.5, P['grass1']), (0.8, '#6E7D3C')]
    _vset(M, 'FOL_CYP', 'F_FolCypress', cyp, 0.66, 1.30, P['leaf_lt'])
    _vset(M, 'FOL_PINE', 'F_FolPine', pine, 0.66, 1.30, P['leaf_lt'])
    _vset(M, 'FOL_OLIVE', 'F_FolOlive', oli, 0.70, 1.30, '#C8CE96')
    _vset(M, 'FOL_BUSH', 'F_FolBush', bush, 0.68, 1.30, P['leaf_lt'])
    cloth = [(0.0, P['c_white']), (0.2, P['c_red']), (0.35, P['c_blue']), (0.5, P['c_ochre']), (0.62, P['c_white']), (0.75, P['c_green']), (0.88, P['c_brown'])]
    _vset(M, 'CLOTH', 'F_Cloth', cloth, 0.76, 1.24, '#FFF8EA')
    # 띠·클라비·숄: 같은 Random에서 옷과 다른 색이 나오게 순서를 어긋나게 둔다
    M['ACCENT'] = var_mat('F_ClothAccent', [(0.0, P['c_red']), (0.2, P['c_ochre']), (0.35, P['c_cream']), (0.5, P['c_wine']), (0.62, P['c_blue']),
                                            (0.75, P['c_red']), (0.88, P['c_ochre'])])
    M['PLASTER'] = var_mat('F_Plaster', [(0.0, P['plaster1']), (0.3, P['plaster2']), (0.55, P['plaster3']), (0.8, P['plaster4'])])
    M['PLASTER_DK'] = var_mat('F_PlasterDk', _shift([(0.0, P['plaster1']), (0.3, P['plaster2']), (0.55, P['plaster3']), (0.8, P['plaster4'])], 0.80))
    M['PLASTER_HI'] = var_mat('F_PlasterHi', _shift([(0.0, P['plaster1']), (0.3, P['plaster2']), (0.55, P['plaster3']), (0.8, P['plaster4'])], 1.30, '#FFF8EA'))
    roof = [(0.0, P['roof1']), (0.4, P['roof2']), (0.75, P['roof3'])]
    M['ROOF'] = var_mat('F_RoofTile', roof)
    M['ROOF_DK'] = var_mat('F_RoofTileDk', _shift(roof, 0.72))
    M['ROOF_HI'] = var_mat('F_RoofTileHi', _shift(roof, 1.25, '#F3D2B0'))
    # 노점 차양: 흰·빨간 줄무늬만(D3). 두 재질의 색 띠가 서로 엇갈려 어느 개체든 빨강/흰 줄이 번갈아 나온다
    M['AWNING'] = var_mat('F_Awning', [(0.0, P['awning_r']), (0.5, P['awning_w'])])
    M['AWNING2'] = var_mat('F_Awning2', [(0.0, P['awning_w']), (0.5, P['awning_r'])])
    M['SAIL'] = var_mat('F_P_Sail', [(0.0, P['awning_r']), (0.5, P['c_ochre'])])     # 돛 줄(빨강 또는 황토) — 흰 줄과 늘 번갈아 보인다
    for k, hk in (('BARK', 'bark'), ('SKIN', 'skin'), ('HAIR', 'hair'), ('TERRA', 'terra'), ('TIMBER', 'wood'), ('C_WHITE', 'c_white'), ('LIME', 'lime')):
        M[k] = bpy.data.materials.get('F_' + hk) or FL.flat('F_' + hk, P[hk])
    M['TRAV'] = bpy.data.materials.get('F_trav') or FL.flat('F_trav', P['trav'])
    M['DARK'] = bpy.data.materials.get('F_trav_deeper') or FL.flat('F_trav_deeper', P['trav_deeper'])
    # 소품 전용 새 재질(접두사 F_P_: 다른 패키지 재질과 이름이 겹치지 않게)
    M['SKIN_V'] = var_mat('F_P_Skin', [(0.0, P['skin']), (0.3, P['skin2']), (0.55, P['skin3']), (0.8, P['skin4'])])
    hair = [(0.0, P['hair']), (0.3, P['hair2']), (0.55, P['hair3']), (0.78, P['hair4']), (0.9, P['hair'])]
    M['HAIR_V'] = var_mat('F_P_Hair', hair)
    M['HAIR_HI'] = var_mat('F_P_HairHi', _shift(hair, 1.28, '#C9A27A'))
    M['LEATHER'] = FL.flat('F_P_Leather', P['leather'])
    goods = [(0.0, P['wicker']), (0.35, P['terra']), (0.6, P['linen']), (0.8, '#A8743F')]
    M['GOODS'] = var_mat('F_P_Goods', goods)
    M['GOODS_DK'] = var_mat('F_P_GoodsDk', _shift(goods, 0.62))
    M['FRUIT'] = var_mat('F_P_Fruit', [(0.0, P['fruit_r']), (0.25, P['fruit_o']), (0.5, P['fruit_g']), (0.75, P['fruit_y'])])
    M['FLOWER'] = var_mat('F_P_Flower', [(0.0, P['flower_p']), (0.3, P['flower_y']), (0.55, P['flower_w']), (0.8, P['flower_r'])])
    M['GRASS_V'] = var_mat('F_P_Grass', [(0.0, P['grass1']), (0.4, P['grass2']), (0.75, P['grass3'])])
    M['BARK_DK'] = FL.flat('F_P_BarkDk', P['bark_dk'])
    M['WOOD_DK'] = FL.flat('F_P_WoodDk', P['wood_dk'])
    M['WOOD_HI'] = FL.flat('F_P_WoodHi', P['wood_hi'])
    terra = [(0.0, P['terra']), (0.3, P['terra2']), (0.6, P['terra3']), (0.8, P['terra4'])]
    M['TERRA_V'] = var_mat('F_P_Terra', terra)
    M['TERRA_DK'] = var_mat('F_P_TerraDk', _shift(terra, 0.74))
    M['TERRA_HI'] = var_mat('F_P_TerraHi', _shift(terra, 1.24, '#F2C9A0'))
    M['VOID'] = FL.flat('F_P_Void', P['void'])
    M['SHUTTER'] = var_mat('F_P_Shutter', [(0.0, P['shutter_g']), (0.3, P['wood_dk']), (0.6, P['shutter_b']), (0.8, P['wood'])])
    M['SACK'] = var_mat('F_P_Sack', [(0.0, P['sack']), (0.4, P['lime']), (0.7, P['pozz'])])
    M['LINEN'] = FL.flat('F_P_Linen', P['linen'])
    M['WATER'] = FL.flat('F_P_Water', P['water'])                     # 안뜰 임플루비움 물(PAL 'water' 한 값, D9)
    M['WATER_HI'] = FL.flat('F_P_WaterHi', FL.mix_hex(P['water'], '#FFFFFF', 0.45))
    return M

PROTO = None
M = None
PROTO_INFO = {}          # 원형 이름 → {'h': 1.0, 'h_max', 'w', 'd', 'x0', 'x1', 'y0', 'y1', 'src_h', 'layers', 'meshes'}

def _proto_coll():
    c = bpy.data.collections.get('PROTO')
    if c is None:
        c = bpy.data.collections.new('PROTO')
        bpy.context.scene.collection.children.link(c)
    c.hide_render = True; c.hide_viewport = True
    return c

def _blob(bm, cx, cy, cz, rx, ry, rz, sub=2, jitter=0.18, seed=0, mi=0):
    """울퉁불퉁한 잎 덩어리(아이코스피어 + 해시 변위). roma_layers.lump가 쓴다 — 모양을 바꾸지 않는다"""
    res = bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    vs = res['verts']
    for v in vs:
        d = v.co.copy()
        j = 1.0 + jitter * (R.hash01(d.x * 13.1 + seed, d.y * 7.7, d.z * 5.3) * 2 - 1)
        v.co = Vector((cx + d.x * rx * j, cy + d.y * ry * j, cz + d.z * rz * j))
    fs = list({f for v in vs for f in v.link_faces})
    for f in fs: f.material_index = mi
    return fs

def _trunk(bm, h, r, mi, lean=(0, 0)):
    G.cyl(bm, 0, 0, r, 0, h, 6, mi, r_top=r * 0.6)
    if lean != (0, 0):
        pass

# ───────────────────────── 표현 레이어 표시(면 단위) ─────────────────────────
# _L(bm, n, 부분, bymat) 뒤에 만드는 면은 L{n}·부분으로 표시된다(bmesh 면 정수 층 'roma_lay').
# bymat = {재질 번호: (층, 부분)}: 한 부분 안에서 재질별로 층을 가른다(예: 위를 보는 밝은 면 → L5, 아래를 보는 짙은 면 → L1).
_LT = {}
LAY = 'roma_lay'

def _lay(bm):
    return bm.faces.layers.int.get(LAY) or bm.faces.layers.int.new(LAY)

def _state(bm, create=True):
    st = _LT.get(id(bm))
    if st is not None and st['bm'] is bm:
        return st
    if not create:
        return None
    st = {'bm': bm, 'keys': [], 'cur': 0, 'bymat': None, 'done': 0}
    _LT[id(bm)] = st
    _lay(bm)
    return st

def _code(st, n, part):
    k = (int(n), str(part))
    if k not in st['keys']:
        st['keys'].append(k)
    return st['keys'].index(k) + 1

def _flush(bm):
    st = _state(bm, False)
    if st is None:
        return
    lay = _lay(bm)
    bm.faces.ensure_lookup_table()
    nf = len(bm.faces)
    cur, bym = st['cur'], st['bymat']
    for i in range(st['done'], nf):
        f = bm.faces[i]
        if f[lay] == 0:
            f[lay] = bym.get(f.material_index, cur) if bym else cur
    st['done'] = nf

def _L(bm, n, part, bymat=None):
    """이후에 만드는 면을 표현 레이어 L{n}·part로 표시한다(원형을 층 메시로 나눌 때 쓴다)"""
    st = _state(bm)
    _flush(bm)
    st['cur'] = _code(st, n, part)
    st['bymat'] = {mi: _code(st, *v) for mi, v in bymat.items()} if bymat else None

def layer_keys(bm):
    """bm의 표현 레이어 표 {코드: (층, 부분)}"""
    _flush(bm)
    st = _state(bm, False)
    return {i + 1: k for i, k in enumerate(st['keys'])} if st else {}

def _split(bm):
    """표시된 bm → {(층, 부분): 새 bmesh}. 원본 bm은 그대로 둔다"""
    keys = layer_keys(bm)
    lay = _lay(bm)
    codes = sorted({f[lay] for f in bm.faces})
    out = {}
    for c in codes:
        key = keys.get(c, (0, 'Untagged'))
        b2 = bm.copy()
        l2 = b2.faces.layers.int.get(LAY)
        dl = [f for f in b2.faces if f[l2] != c]
        if dl:
            bmesh.ops.delete(b2, geom=dl, context='FACES')
        if len(b2.faces) == 0:
            b2.free(); continue
        out[key] = b2
    return out

def _normalize(bm, ref_parts=None):
    """키(땅 z 0 → 꼭대기)를 1.0으로(균일 축척). ref_parts가 있으면 그 부분 면의 꼭대기로 잰다(사람: 머리·머리칼, 짐 제외).
    반환: 정규화 전 키"""
    keys = layer_keys(bm)
    lay = _lay(bm)
    zt = 0.0
    if ref_parts:
        for f in bm.faces:
            k = keys.get(f[lay])
            if k and k[1] in ref_parts:
                for v in f.verts:
                    zt = max(zt, v.co.z)
    if zt <= 1e-6:
        zt = max(v.co.z for v in bm.verts)
    s = 1.0 / zt
    for v in bm.verts:
        v.co = v.co * s
    return zt

# ───────────────────────── 형상 도구(지역 단위) ─────────────────────────
def _lathe(bm, prof, n=12, mi=0, cx=0.0, cy=0.0, sx=1.0, sy=1.0, phase=0.0, ridge=0.0, mif=None, cap_top=True, cap_bot=False, cap_mi=None):
    """회전체. prof = [(r, z), …] 아래→위, r = 0이면 꼭짓점 하나. mif(j, k, a) → 면 재질 번호(줄·주름·띠를 면 단위로 칠한다).
    모든 고리가 같은 모양의 균일 축척이라 옆면 사각형은 평면이다(면 깨짐 없음)"""
    rows = []
    for (r, z) in prof:
        if r <= 1e-7:
            rows.append([bm.verts.new((cx, cy, z))]); continue
        row = []
        for k in range(n):
            a = phase + 2.0 * math.pi * k / n
            rr = r * (1.0 + (ridge if k % 2 == 0 else -ridge))
            row.append(bm.verts.new((cx + rr * sx * math.cos(a), cy + rr * sy * math.sin(a), z)))
        rows.append(row)
    fs = []
    for j in range(len(rows) - 1):
        A, B = rows[j], rows[j + 1]
        if len(A) == 1 and len(B) == 1:
            continue
        for k in range(n):
            ac = phase + 2.0 * math.pi * (k + 0.5) / n
            k2 = (k + 1) % n
            if len(A) == 1:
                vs = [A[0], B[k2], B[k]]
            elif len(B) == 1:
                vs = [A[k], A[k2], B[0]]
            else:
                vs = [A[k], A[k2], B[k2], B[k]]
            f = bm.faces.new(vs)
            f.material_index = mif(j, k, ac) if mif else mi
            fs.append(f)
    cm = mi if cap_mi is None else cap_mi
    if cap_top and len(rows[-1]) > 2:
        f = bm.faces.new(rows[-1]); f.material_index = cm; fs.append(f)
    if cap_bot and len(rows[0]) > 2:
        f = bm.faces.new(rows[0][::-1]); f.material_index = cm; fs.append(f)
    return fs

def _tube(bm, p0, p1, r0, r1=None, n=6, mi=0, cap0=True, cap1=True, mif=None):
    """두 점 사이 원기둥(팔·다리·가지·끌채). mif(k) → 옆면 재질(껍질 결 등)"""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0; L = d.length
    if L < 1e-9:
        return []
    w = d / L
    a = Vector((1.0, 0.0, 0.0)) if abs(w.x) < 0.9 else Vector((0.0, 1.0, 0.0))
    u = w.cross(a).normalized(); v = w.cross(u)
    r1 = r0 if r1 is None else r1
    angs = [2.0 * math.pi * k / n for k in range(n)]
    A = [bm.verts.new(p0 + (u * math.cos(t) + v * math.sin(t)) * r0) for t in angs]
    B = [bm.verts.new(p1 + (u * math.cos(t) + v * math.sin(t)) * r1) for t in angs]
    fs = []
    for k in range(n):
        k2 = (k + 1) % n
        f = bm.faces.new([A[k], A[k2], B[k2], B[k]]); f.material_index = mif(k) if mif else mi; fs.append(f)
    if cap0:
        f = bm.faces.new(A[::-1]); f.material_index = mi; fs.append(f)
    if cap1:
        f = bm.faces.new(B); f.material_index = mi; fs.append(f)
    return fs

def _chain(bm, pts, rs, n=6, mi=0, mif=None):
    """꺾인 관(줄기·손잡이): 점 목록과 반지름 목록. 마디마다 관을 잇는다"""
    for i in range(len(pts) - 1):
        _tube(bm, pts[i], pts[i + 1], rs[i], rs[i + 1], n, mi, i == 0, True, mif)

def _clump(bm, c, rx, ry, rz, sub=2, jit=0.18, seed=0.0, mi=0, mi_top=None, top=0.55, mi_bot=None, bot=-0.35):
    """잎·머리 덩어리. 위를 보는 면(법선 z > top)은 mi_top(L5), 아래를 보는 면은 mi_bot(L1)으로 칠한다(돌려도 변하지 않는다)"""
    res = bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    vs = res['verts']
    for v in vs:
        d = v.co.copy()
        j = 1.0 + jit * (R.hash01(d.x * 13.1 + seed, d.y * 7.7 + seed * 0.37, d.z * 5.3) * 2 - 1)
        v.co = Vector((c[0] + d.x * rx * j, c[1] + d.y * ry * j, c[2] + d.z * rz * j))
    fs = list({f for v in vs for f in v.link_faces})
    cen = Vector(c)
    for f in fs:
        f.normal_update()
        n = f.normal
        if n.dot(f.calc_center_median() - cen) < 0:
            n = -n
        m = mi
        if mi_top is not None and n.z > top:
            m = mi_top
        elif mi_bot is not None and n.z < bot:
            m = mi_bot
        f.material_index = m
    return fs

def _band(bm, rx0, ry0, rx1, ry1, zc, slope, h, n=16, mi=0, cx=0.0, cy=0.0, mi_top=None):
    """몸을 두르는 띠(허리띠·토가 자락·숄): 기울기 slope(z = zc + slope·x). 바깥면·윗면·아랫면만(안쪽은 몸속)"""
    O0, O1, I0, I1 = [], [], [], []
    for k in range(n):
        a = 2.0 * math.pi * k / n
        z0 = zc + slope * rx1 * math.cos(a) - h / 2
        ox, oy = cx + rx1 * math.cos(a), cy + ry1 * math.sin(a)
        ix, iy = cx + rx0 * math.cos(a), cy + ry0 * math.sin(a)
        O0.append(bm.verts.new((ox, oy, z0))); O1.append(bm.verts.new((ox, oy, z0 + h)))
        I0.append(bm.verts.new((ix, iy, z0))); I1.append(bm.verts.new((ix, iy, z0 + h)))
    fs = []
    for k in range(n):
        k2 = (k + 1) % n
        for q, mm in (([O0[k], O0[k2], O1[k2], O1[k]], mi), ([O1[k], O1[k2], I1[k2], I1[k]], mi if mi_top is None else mi_top),
                      ([I0[k], I0[k2], O0[k2], O0[k]], mi)):
            f = bm.faces.new(q); f.material_index = mm; fs.append(f)
    return fs

def _quad(bm, pts, mi):
    f = bm.faces.new([bm.verts.new(p) for p in pts]); f.material_index = mi
    return f

def _blades(bm, x, y, z, h, n, seed, mi, spread=1.0):
    """밑동 풀 잎(L6): 엇갈린 가는 세모 n장"""
    for k in range(n):
        a = 2.0 * math.pi * (k / n + R.hash01(seed, k) * 0.3)
        rr = (0.25 + 0.75 * R.hash01(seed, k, 2)) * h * 0.5 * spread
        bx, by = x + rr * math.cos(a), y + rr * math.sin(a)
        hh = h * (0.6 + 0.4 * R.hash01(seed, k, 3))
        w = h * 0.16
        tx, ty = bx + 0.25 * h * math.cos(a), by + 0.25 * h * math.sin(a)
        _quad(bm, [(bx - w * math.sin(a), by + w * math.cos(a), z), (bx + w * math.sin(a), by - w * math.cos(a), z), (tx, ty, z + hh)], mi)

def _wall_slab(bm, side, box, u0, u1, z0, z1, d, mi):
    """곧은 벽 면에 붙인 얇은 판(창·문·띠·얼룩). side: F(−y) B(+y) R(+x) L(−x), box = (X0, X1, Y0, Y1)"""
    X0, X1, Y0, Y1 = box
    e = 0.002
    if side == 'F':
        return G.box(bm, u0, u1, Y0 - d, Y0 + e, z0, z1, mi)
    if side == 'B':
        return G.box(bm, u0, u1, Y1 - e, Y1 + d, z0, z1, mi)
    if side == 'R':
        return G.box(bm, X1 - e, X1 + d, u0, u1, z0, z1, mi)
    return G.box(bm, X0 - d, X0 + e, u0, u1, z0, z1, mi)

def _side_span(side, box):
    X0, X1, Y0, Y1 = box
    return (X0, X1) if side in ('F', 'B') else (Y0, Y1)

def _side_pt(side, box, u, d):
    """벽 면 side의 위치 u에서 바깥으로 d만큼 나간 평면 점"""
    X0, X1, Y0, Y1 = box
    if side == 'F':
        return u, Y0 - d
    if side == 'B':
        return u, Y1 + d
    if side == 'R':
        return X1 + d, u
    return X0 - d, u

def _tile_quad(bm, p00, p10, p11, p01, nst, mi_a, mi_b, frac=0.78):
    """평면 사각 지붕면(p00–p10 처마, p01–p11 용마루 쪽)을 기와 골 띠로 나눈다: 각 띠의 앞 frac는 mi_a(L0), 나머지는 mi_b(L3 기와 골)"""
    A = [Vector(p) for p in (p00, p10, p11, p01)]
    def P_(u, v):
        e = A[0].lerp(A[1], u); r = A[3].lerp(A[2], u)
        return tuple(e.lerp(r, v))
    for i in range(nst):
        u0 = i / nst; u1 = (i + 1) / nst; um = u0 + (u1 - u0) * frac
        _quad(bm, [P_(u0, 0.0), P_(um, 0.0), P_(um, 1.0), P_(u0, 1.0)], mi_a)
        _quad(bm, [P_(um, 0.0), P_(u1, 0.0), P_(u1, 1.0), P_(um, 1.0)], mi_b)

# ───────────────────────── 나무·덤불 ─────────────────────────
CYP_PROF = [(0.030, 0.05), (0.075, 0.10), (0.100, 0.18), (0.108, 0.30), (0.100, 0.46), (0.084, 0.62), (0.060, 0.77), (0.034, 0.89), (0.0, 0.985)]

def _prof_r(prof, z):
    for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / max(1e-9, z1 - z0)
    return prof[-1][0] if z > prof[-1][1] else prof[0][0]

def mk_cypress(seed):
    """사이프러스(키 1.0으로 정규화, 폭 약 0.25). 재질: 0 잎 1 줄기 2 잎 짙은 3 잎 밝은 4 풀
    L0 불꽃 모양 잎 다발 · L1 다발 사이로 보이는 짙은 속·다발 아랫면 · L2 줄기 · L3 다발 사이 작은 비늘 뭉치(잎결)
    L4 뾰족한 끝·옆으로 삐친 잔가지 다발(들쭉날쭉한 윤곽) · L5 위를 보는 잎 면 밝은 연두 · L6 밑동 풀"""
    bm = bmesh.new()
    FO, BK, FD, FH, GR = range(5)
    lt = {FH: (5, 'LeafLight'), FD: (1, 'LeafShade')}
    h = 0.96 + 0.08 * R.hash01(seed, 1); w = 0.92 + 0.16 * R.hash01(seed, 2)
    _L(bm, 1, 'Core')
    _lathe(bm, [(r * w * 0.80, z * h) for r, z in CYP_PROF], 10, FD)
    _L(bm, 2, 'Trunk')
    _tube(bm, (0, 0, 0), (0, 0, 0.075 * h), 0.026, 0.020, 6, BK, False)
    _L(bm, 0, 'Foliage', lt)
    n = 30
    for i in range(n):
        t = (i + 0.5) / n
        z = (0.075 + 0.85 * t) * h
        a = i * 2.39996 + seed
        rz = _prof_r(CYP_PROF, z / h) * w
        s = max(0.026, rz * 0.62)
        _clump(bm, (rz * 0.55 * math.cos(a), rz * 0.55 * math.sin(a), z), s, s, s * 1.75, 2 if s > 0.045 else 1, 0.16, seed * 7.0 + i, FO, FH, 0.62, FD, -0.20)
    _L(bm, 3, 'LeafScales', lt)
    for i in range(22):
        t = (i + 0.3) / 22
        z = (0.10 + 0.80 * t) * h
        a = i * 2.39996 + seed + 1.2
        rz = _prof_r(CYP_PROF, z / h) * w
        s = max(0.016, rz * 0.30)
        _clump(bm, (rz * 0.90 * math.cos(a), rz * 0.90 * math.sin(a), z), s, s, s * 1.5, 1, 0.12, seed * 11.0 + i,
               FO if i % 3 else FH, FH, 0.55, FD, -0.30)
    _L(bm, 4, 'Tip', {FH: (5, 'LeafLight')})
    _clump(bm, (0.0, 0.0, 0.955 * h), 0.020, 0.020, 0.055, 1, 0.1, seed + 99.0, FO, FH, 0.5)
    for k in range(4):
        z = (0.30 + 0.15 * k) * h
        a = seed * 1.7 + k * 1.9
        rz = _prof_r(CYP_PROF, z / h) * w
        _clump(bm, ((rz + 0.012) * math.cos(a), (rz + 0.012) * math.sin(a), z), 0.026, 0.026, 0.05, 1, 0.15, seed * 13.0 + k, FO, FH, 0.55)
    _L(bm, 6, 'Grass')
    _blades(bm, 0.0, 0.0, 0.0, 0.07, 6, seed + 5.0, GR)
    _flush(bm)
    return bm

def mk_pine(seed):
    """우산소나무(키 1.0으로 정규화, 폭 약 0.88). 재질: 0 잎 1 줄기 2 잎 짙은 3 잎 밝은 4 줄기 짙은 5 풀
    L0 납작한 우산 갓 · L1 갓 아래 짙은 띠 · L2 기울어진 줄기와 갈래 가지 · L3 줄기 껍질 결·갓 위 잎 뭉치 · L4 들쭉날쭉한 갓 둘레 뭉치
    L5 위를 보는 갓 면 밝은 색 · L6 밑동 풀"""
    bm = bmesh.new()
    FO, BK, FD, FH, BD, GR = range(6)
    lt = {FH: (5, 'CanopyLight'), FD: (1, 'CanopyShade')}
    lx = 0.04 * (R.hash01(seed, 1) - 0.5)
    bark = lambda k: BD if k % 3 == 0 else BK
    top = (0.05 + lx, 0.01, 0.585)
    _L(bm, 2, 'Trunk', {BD: (3, 'BarkGrain')})
    _chain(bm, [(0, 0, 0), (0.02 + lx * 0.5, 0.0, 0.30), top], [0.034, 0.027, 0.020], 7, BK, bark)
    _L(bm, 2, 'Branches')
    for k, (bx, by, bz) in enumerate(((-0.11, 0.05, 0.675), (0.19, -0.04, 0.665), (0.05, 0.16, 0.675), (0.02, -0.15, 0.67))):
        _tube(bm, top, (bx + lx, by, bz), 0.016, 0.009, 5, BK)
    cx0, cy0 = 0.04 + lx, 0.01
    _L(bm, 1, 'CanopyShade')
    _clump(bm, (cx0, cy0, 0.676), 0.345, 0.32, 0.028, 2, 0.08, seed + 3.0, FD)
    _L(bm, 0, 'Canopy', lt)
    for k in range(8):
        a = 2 * math.pi * k / 8 + seed
        rr = 0.19 + 0.035 * R.hash01(seed, k)
        _clump(bm, (cx0 + rr * math.cos(a), cy0 + rr * math.sin(a), 0.705 + 0.012 * R.hash01(seed, k, 5)),
               0.15 + 0.03 * R.hash01(seed, k, 6), 0.14 + 0.03 * R.hash01(seed, k, 7), 0.042, 2, 0.10, seed * 3.0 + k, FO, FH, 0.86, FD, -0.08)
    for k in range(4):
        a = 2 * math.pi * (k + 0.5) / 4 + seed
        _clump(bm, (cx0 + 0.085 * math.cos(a), cy0 + 0.085 * math.sin(a), 0.742), 0.15, 0.14, 0.040, 2, 0.10, seed * 4.0 + k, FO, FH, 0.86, FD, -0.08)
    _clump(bm, (cx0, cy0, 0.768), 0.12, 0.11, 0.036, 2, 0.10, seed + 9.0, FO, FH, 0.86)
    _L(bm, 3, 'NeedleTufts', {FH: (5, 'CanopyLight')})
    for k in range(12):
        a = 2 * math.pi * R.hash01(seed, k, 11); rr = 0.27 * math.sqrt(R.hash01(seed, k, 12))
        _clump(bm, (cx0 + rr * math.cos(a), cy0 + rr * math.sin(a), 0.792 - 0.24 * rr * rr / 0.27), 0.05, 0.046, 0.022, 1, 0.12,
               seed * 5.0 + k, FO if k % 3 else FH, FH, 0.75)
    _L(bm, 4, 'RimTufts', lt)
    for k in range(7):
        a = 2 * math.pi * (k + 0.3) / 7 + seed * 1.3
        rr = 0.325 + 0.03 * R.hash01(seed, k, 21)
        _clump(bm, (cx0 + rr * math.cos(a), cy0 + rr * math.sin(a), 0.698), 0.062, 0.056, 0.030, 1, 0.15, seed * 9.0 + k, FO, FH, 0.8, FD, -0.1)
    _L(bm, 6, 'Grass')
    _blades(bm, 0.0, 0.0, 0.0, 0.06, 5, seed + 7.0, GR)
    _flush(bm)
    return bm

def mk_olive(seed):
    """올리브(키 1.0으로 정규화, 폭 약 1.1). 재질: 0 잎 1 줄기 2 잎 짙은 3 잎 밝은(은빛) 4 줄기 짙은 5 풀
    L0 넓고 들쭉날쭉한 잎 덩어리 · L1 갓 속 짙은 덩어리·덩어리 아랫면 · L2 두 갈래로 비틀린 줄기·덩어리로 가는 가지 · L3 껍질 결·은빛 잎 뭉치
    L4 굵은 밑동 혹 · L5 위를 보는 잎 면 은빛 · L6 밑동 풀"""
    bm = bmesh.new()
    FO, BK, FD, FH, BD, GR = range(6)
    bark = lambda k: BD if k % 2 == 0 else BK
    _L(bm, 2, 'Trunk', {BD: (3, 'BarkGrain')})
    _chain(bm, [(0, 0, 0), (-0.02, 0.01, 0.11), (-0.07, 0.03, 0.25), (-0.10, 0.03, 0.33)], [0.050, 0.038, 0.026, 0.016], 7, BK, bark)
    _chain(bm, [(-0.02, 0.01, 0.10), (0.05, -0.03, 0.20), (0.11, -0.02, 0.30)], [0.030, 0.022, 0.014], 6, BK, bark)
    _L(bm, 4, 'RootKnob')
    _clump(bm, (0.0, 0.005, 0.025), 0.065, 0.06, 0.03, 1, 0.25, seed + 1.0, BD)
    _L(bm, 1, 'CrownShade')
    _clump(bm, (0.0, 0.0, 0.37), 0.20, 0.18, 0.09, 2, 0.12, seed, FD)
    lobes = []
    for k in range(5):
        a = 2 * math.pi * k / 5 + seed * 0.7
        rr = 0.165 + 0.04 * R.hash01(seed, k)
        lobes.append((rr * math.cos(a), rr * math.sin(a), 0.335 + 0.08 * R.hash01(seed, k, 4), 0.115 + 0.025 * R.hash01(seed, k, 5)))
    lobes.append((0.015, -0.01, 0.455, 0.125))
    _L(bm, 0, 'Crown', {FH: (5, 'LeafLight'), FD: (1, 'CrownShade')})
    for k, (x, y, z, s) in enumerate(lobes):
        _clump(bm, (x, y, z), s, s * 0.95, s * 0.70, 2, 0.12, seed * 3.0 + k, FO, FH, 0.70, FD, -0.15)
    _L(bm, 2, 'Branches')
    for k, (x, y, z, s) in enumerate(lobes):
        _tube(bm, (x * 0.35, y * 0.35, 0.22), (x * 0.8, y * 0.8, z - s * 0.45), 0.014, 0.009, 5, BK)
    _L(bm, 3, 'LeafTufts', {FH: (5, 'LeafLight')})
    for k, (x, y, z, s) in enumerate(lobes):
        for j in range(3):
            b = 2 * math.pi * R.hash01(seed, k, j, 21)
            q = s * 0.62
            _clump(bm, (x + q * math.cos(b), y + q * math.sin(b), z + s * 0.38), s * 0.42, s * 0.40, s * 0.28, 1, 0.10,
                   seed * 5.0 + k * 3 + j, FH if (k + j) % 2 else FO, FH, 0.6)
    _L(bm, 6, 'Grass')
    _blades(bm, 0.0, 0.0, 0.0, 0.06, 6, seed + 3.0, GR)
    _flush(bm)
    return bm

def mk_bush(seed, flowers=None):
    """덤불(키 1.0으로 정규화, 폭 약 2.0). 재질: 0 잎 1 잎 짙은 2 잎 밝은 3 꽃 4 풀
    L0 잎 덩어리 4+1 · L1 속 짙은 덩어리·덩어리 아랫면 · L2 덩어리 사이 굵은 잎 뭉치 · L3 잎결 작은 뭉치 · L4 삐친 잔가지 뭉치(들쭉날쭉한 윤곽)
    L5 위를 보는 면 밝은 연두 · L6 꽃(flowers=True일 때)·밑동 풀"""
    bm = bmesh.new()
    FO, FD, FH, FW, GR = range(5)
    if flowers is None:
        flowers = R.hash01(seed, 77) > 0.5
    _L(bm, 1, 'InnerShade')
    _clump(bm, (0.0, 0.0, 0.10), 0.22, 0.20, 0.10, 2, 0.15, seed, FD)
    _L(bm, 0, 'Foliage', {FH: (5, 'LeafLight'), FD: (1, 'InnerShade')})
    for k in range(4):
        a = 2 * math.pi * k / 4 + seed
        rr = 0.12 + 0.02 * R.hash01(seed, k)
        _clump(bm, (rr * math.cos(a), rr * math.sin(a), 0.12 + 0.03 * R.hash01(seed, k, 2)),
               0.15 + 0.03 * R.hash01(seed, k, 3), 0.15 + 0.03 * R.hash01(seed, k, 4), 0.12 + 0.02 * R.hash01(seed, k, 5),
               2, 0.24, seed * 3.0 + k, FO, FH, 0.68, FD, -0.15)
    _clump(bm, (0.0, 0.0, 0.17), 0.15, 0.14, 0.11, 2, 0.2, seed + 8.0, FO, FH, 0.68)
    _L(bm, 2, 'MidTufts', {FH: (5, 'LeafLight')})
    for k in range(4):
        a = 2 * math.pi * (k + 0.5) / 4 + seed
        _clump(bm, (0.2 * math.cos(a), 0.2 * math.sin(a), 0.07), 0.08, 0.075, 0.07, 1, 0.2, seed * 4.0 + k, FO, FH, 0.6)
    _L(bm, 3, 'LeafTexture', {FH: (5, 'LeafLight')})
    for k in range(8):
        a = 2 * math.pi * R.hash01(seed, k, 31); rr = 0.2 * math.sqrt(R.hash01(seed, k, 32))
        _clump(bm, (rr * math.cos(a), rr * math.sin(a), 0.24 - 0.35 * rr * rr), 0.045, 0.042, 0.035, 1, 0.2, seed * 6.0 + k,
               FH if k % 3 == 0 else FO, FH, 0.6)
    _L(bm, 4, 'Sprigs', {FH: (5, 'LeafLight')})
    for k in range(3):
        a = 2 * math.pi * (k + 0.2) / 3 + seed * 1.9
        _clump(bm, (0.26 * math.cos(a), 0.26 * math.sin(a), 0.16), 0.035, 0.032, 0.06, 1, 0.2, seed * 8.0 + k, FO, FH, 0.6)
    if flowers:
        _L(bm, 6, 'Flowers')
        for k in range(9):
            a = 2 * math.pi * R.hash01(seed, k, 41); rr = 0.22 * math.sqrt(R.hash01(seed, k, 42))
            _clump(bm, (rr * math.cos(a), rr * math.sin(a), 0.255 - 0.4 * rr * rr), 0.022, 0.022, 0.018, 1, 0.0, seed + k, FW)
    _L(bm, 6, 'Grass')
    _blades(bm, 0.0, 0.0, 0.0, 0.07, 6, seed + 9.0, GR, 3.5)
    _flush(bm)
    # b6(bglobal): 덩어리 아랫면이 z 0 밑으로 내려간다(축척 1당 약 −0.1). 최저점을 z 0으로 올려 땅 밑이 보이지 않게 한다
    z0 = min(v.co.z for v in bm.verts)
    if z0 < 0.0:
        for v in bm.verts:
            v.co.z -= z0
    return bm

# ───────────────────────── 사람 ─────────────────────────
PERSON_REF = ('Head', 'Hair', 'HairLight')      # 키를 재는 부분(발 → 머리칼 꼭대기). 짐(L6)은 키에 넣지 않는다

def mk_person(seed, pose=0):
    """키 1 사람(발~머리). pose 0: 토가 자락을 두른 남자(두루마리) · 1: 머리에 과일 바구니를 인 일꾼 · 2: 발목까지 오는 스톨라에 숄, 항아리를 든 여자
    재질: 0 옷 1 피부 2 머리카락 3 옷 짙은 4 옷 밝은 5 띠·장식 6 가죽 7 짐 8 머리칼 밝은 9 과일 10 짐 짙은
    L0 튜닉(몸통·치마)·머리 · L1 겨드랑이 옆·목둘레 짙은 색·바구니 속 · L2 단·허리띠·토가 자락·숄 · L3 치마 주름(엇갈린 면)·클라비 두 줄
    L4 다리·샌들·팔·손·머리칼(쪽) · L5 어깨 윗면·머리칼 윗면 밝은 색 · L6 짐(두루마리·바구니와 과일·항아리)"""
    bm = bmesh.new()
    CL, SK, HR, DK, HI, AC, LE, GD, HH, FR, GK = range(11)
    woman = pose == 2
    N = 16
    PH = -math.pi / 2 - math.pi / N               # 면 0의 가운데가 앞(−y)
    clavi = {1, N - 1, N // 2 - 1, N // 2 + 1}    # 앞뒤 클라비(가운데에서 ±22.5°)
    sy = 0.80
    hem = 0.06 if woman else 0.30
    if woman:
        skirt = [(0.150, hem), (0.137, 0.20), (0.121, 0.36), (0.106, 0.50), (0.100, 0.56)]
    else:
        skirt = [(0.128, hem), (0.113, 0.42), (0.103, 0.52), (0.100, 0.56)]
    def mskirt(j, k, a):
        if (not woman) and k in clavi:
            return AC
        return DK if k % 4 == 2 else CL
    _L(bm, 0, 'Tunic', {DK: (3, 'Folds'), AC: (3, 'Clavi')})
    _lathe(bm, skirt, N, CL, sy=sy, phase=PH, ridge=0.05, mif=mskirt, cap_top=False, cap_bot=True, cap_mi=DK)
    torso = [(0.100, 0.55), (0.108, 0.64), (0.117, 0.73), (0.113, 0.785), (0.076, 0.815), (0.042, 0.83)]
    def mtorso(j, k, a):
        if j >= 3:
            return HI
        if (not woman) and k in clavi:
            return AC
        if j <= 1 and k in (N // 4, 3 * N // 4):
            return DK
        return CL
    _L(bm, 0, 'Tunic', {HI: (5, 'Shoulder'), AC: (3, 'Clavi'), DK: (1, 'Shade')})
    _lathe(bm, torso, N, CL, sy=sy, phase=PH, mif=mtorso, cap_top=True, cap_mi=DK)
    _L(bm, 2, 'Hem')
    _band(bm, skirt[0][0] * 0.97, skirt[0][0] * sy * 0.97, skirt[0][0] * 1.09, skirt[0][0] * sy * 1.09, hem + 0.022, 0.0, 0.032, N,
          AC if woman else DK)
    _L(bm, 2, 'Belt', {HI: (5, 'Shoulder')})
    if woman:
        _band(bm, 0.104, 0.083, 0.119, 0.096, 0.675, 0.0, 0.03, N, AC, mi_top=HI)
    else:
        _band(bm, 0.098, 0.079, 0.108, 0.088, 0.555, 0.0, 0.038, N, LE)
    _L(bm, 2, 'Sash')
    if pose == 0:
        _band(bm, 0.110, 0.087, 0.126, 0.101, 0.665, 0.95, 0.075, N, HI, mi_top=HI)
    elif woman:
        _band(bm, 0.113, 0.090, 0.128, 0.104, 0.745, -0.45, 0.06, N, AC, mi_top=AC)
    _L(bm, 4, 'Legs')
    for sx in (-1, 1):
        x = 0.045 * sx
        if not woman:
            _tube(bm, (x, 0.0, 0.025), (x * 1.08, 0.0, hem + 0.04), 0.025, 0.031, 6, SK, False)
            G.box(bm, x - 0.028, x + 0.028, -0.058, 0.030, 0.0, 0.028, LE)
        else:
            G.box(bm, x - 0.026, x + 0.026, -0.150, -0.080, 0.0, 0.026, LE)                                  # 치마 밑으로 나온 발끝
    _L(bm, 0, 'Head')
    _tube(bm, (0, 0, 0.80), (0, 0, 0.865), 0.031, 0.029, 6, SK, False, False)
    _clump(bm, (0.0, -0.004, 0.915), 0.069, 0.073, 0.080, 2, 0.0, seed, SK)
    _L(bm, 4, 'Hair', {HH: (5, 'HairLight')})
    if woman:
        _clump(bm, (0.0, 0.012, 0.950), 0.075, 0.079, 0.058, 2, 0.10, seed + 3.0, HR, HH, 0.80)
        _clump(bm, (0.0, 0.074, 0.925), 0.036, 0.034, 0.034, 1, 0.05, seed + 4.0, HR, HH, 0.75)        # 쪽
    else:
        _clump(bm, (0.0, 0.016, 0.947), 0.075, 0.078, 0.056, 2, 0.14, seed + 3.0, HR, HH, 0.80)
    def arm(sx, sh, el, ha):
        _tube(bm, sh, el, 0.037, 0.032, 6, CL)
        _tube(bm, el, ha, 0.025, 0.021, 6, SK)
        _clump(bm, ha, 0.026, 0.026, 0.028, 1, 0.0, seed + sx, SK)
    shR, shL = (0.110, 0.0, 0.772), (-0.110, 0.0, 0.772)
    _L(bm, 4, 'Arms')
    if pose == 0:
        arm(1, shR, (0.140, 0.0, 0.665), (0.135, -0.022, 0.515))
        arm(-1, shL, (-0.138, -0.012, 0.660), (-0.080, -0.104, 0.600))
        _L(bm, 6, 'Load')
        _tube(bm, (-0.115, -0.112, 0.596), (-0.035, -0.105, 0.604), 0.017, 0.017, 6, GD)                   # 두루마리
    elif pose == 1:
        arm(1, shR, (0.152, 0.0, 0.842), (0.088, 0.004, 0.990))
        arm(-1, shL, (-0.140, 0.0, 0.665), (-0.136, -0.020, 0.515))
        _L(bm, 6, 'Load', {GK: (1, 'LoadVoid')})
        _lathe(bm, [(0.070, 0.990), (0.096, 1.045), (0.103, 1.068)], 12, GD, cap_top=False, cap_bot=True)  # 바구니
        _lathe(bm, [(0.090, 1.050), (0.0, 1.050)], 12, GK, cap_top=False)                                   # 바구니 속(L1)
        for k in range(5):
            a = 2 * math.pi * k / 5 + seed
            _clump(bm, (0.045 * math.cos(a), 0.045 * math.sin(a), 1.068), 0.030, 0.030, 0.028, 1, 0.0, seed + k * 3.0, FR)
        _clump(bm, (0.0, 0.0, 1.085), 0.032, 0.032, 0.030, 1, 0.0, seed + 31.0, FR)
    else:
        arm(1, shR, (0.142, 0.0, 0.665), (0.150, -0.025, 0.525))
        arm(-1, shL, (-0.134, -0.014, 0.660), (-0.075, -0.112, 0.620))
        _L(bm, 6, 'Load', {GK: (1, 'LoadVoid')})
        _lathe(bm, [(0.0, 0.43), (0.040, 0.445), (0.058, 0.49), (0.052, 0.54), (0.024, 0.575), (0.026, 0.60)], 10, GD,
               cx=0.158, cy=-0.035, cap_top=False)                                                         # 항아리
        _lathe(bm, [(0.020, 0.598), (0.0, 0.598)], 10, GK, cx=0.158, cy=-0.035, cap_top=False)              # 항아리 입(L1)
    _flush(bm)
    return bm

# ───────────────────────── 집 ─────────────────────────
def _house_shell(bm, BOX, h, two, seed, mats_idx, door_side='F'):
    """집 벽 공통(박공·평지붕 집): 벽·굽도리·처마 밑 짙은 띠·코니스 윗선·층 띠·창·문·가게·덧문·얼룩·화분·발코니·문 옆 화분.
    mats_idx = (PL, DK, PD, PH, TB, SH, VD, FO, TC)"""
    PL, DK, PD, PH, TB, SH, VD, FO, TC = mats_idx
    X0, X1, Y0, Y1 = BOX
    _L(bm, 0, 'Walls')
    G.box(bm, X0, X1, Y0, Y1, 0.0, h, PL)
    _L(bm, 2, 'Plinth')
    G.box(bm, X0 - 0.008, X1 + 0.008, Y0 - 0.008, Y1 + 0.008, 0.0, 0.045, PD)
    _L(bm, 1, 'EaveShade')
    G.box(bm, X0 - 0.012, X1 + 0.012, Y0 - 0.012, Y1 + 0.012, h - 0.034, h - 0.016, PD)
    _L(bm, 5, 'CorniceLight')
    G.box(bm, X0 - 0.016, X1 + 0.016, Y0 - 0.016, Y1 + 0.016, h - 0.016, h, PH)
    if two:
        _L(bm, 2, 'FloorBand')
        zf = h * 0.48
        G.box(bm, X0 - 0.010, X1 + 0.010, Y0 - 0.010, Y1 + 0.010, zf - 0.011, zf + 0.011, PH)
    floors = [h * 0.26, h * 0.70] if two else [h * 0.56]
    wh = 0.10 if two else 0.12
    for si, side in enumerate(('F', 'R', 'B', 'L')):
        c0, c1 = _side_span(side, BOX)
        L = c1 - c0
        nw = 3 if L > 0.9 else 2
        for fi, zc in enumerate(floors):
            for k in range(nw):
                u = c0 + L * (k + 0.5) / nw
                if fi == 0 and side == door_side and k == nw - 1:
                    _L(bm, 1, 'Openings')                                                                   # 문 속
                    _wall_slab(bm, side, BOX, u - 0.065, u + 0.065, 0.04, 0.26, 0.004, VD)
                    _L(bm, 2, 'Frames')                                                                     # 상인방·문틀
                    _wall_slab(bm, side, BOX, u - 0.085, u + 0.085, 0.26, 0.285, 0.012, PH)
                    _wall_slab(bm, side, BOX, u - 0.085, u - 0.065, 0.04, 0.26, 0.010, PH)
                    _wall_slab(bm, side, BOX, u + 0.065, u + 0.085, 0.04, 0.26, 0.010, PH)
                    _L(bm, 4, 'Door')                                                                       # 반쯤 열린 나무 문짝
                    _wall_slab(bm, side, BOX, u - 0.062, u + 0.004, 0.042, 0.255, 0.009, TB)
                    _L(bm, 6, 'Planters')                                                                   # 문 옆 화분(늘 있다)
                    px, py = _side_pt(side, BOX, u + 0.13, 0.035)
                    G.box(bm, px - 0.022, px + 0.022, py - 0.022, py + 0.022, 0.0, 0.040, TC)
                    _clump(bm, (px, py, 0.075), 0.034, 0.032, 0.040, 1, 0.2, seed + 50.0 + si, FO)
                    continue
                if fi == 0 and side == 'R' and k == 0 and two:
                    _L(bm, 1, 'Openings')                                                                   # 가게(타베르나) 넓은 입구
                    _wall_slab(bm, side, BOX, u - 0.13, u + 0.13, 0.04, 0.25, 0.004, VD)
                    _L(bm, 2, 'Frames')
                    _wall_slab(bm, side, BOX, u - 0.15, u + 0.15, 0.25, 0.272, 0.012, PH)
                    _L(bm, 4, 'Shop')                                                                       # 계산대
                    _wall_slab(bm, side, BOX, u - 0.12, u + 0.12, 0.04, 0.11, 0.05, TB)
                    continue
                _L(bm, 1, 'Openings')                                                                       # 창 속
                _wall_slab(bm, side, BOX, u - 0.045, u + 0.045, zc - wh / 2, zc + wh / 2, 0.004, DK)
                _L(bm, 2, 'Frames')                                                                         # 창턱·상인방
                _wall_slab(bm, side, BOX, u - 0.058, u + 0.058, zc - wh / 2 - 0.016, zc - wh / 2, 0.016, PH)
                _wall_slab(bm, side, BOX, u - 0.052, u + 0.052, zc + wh / 2, zc + wh / 2 + 0.010, 0.008, PH)
                hs = R.hash01(seed, si, fi, k)
                if hs > 0.45:
                    _L(bm, 4, 'Shutters')
                    _wall_slab(bm, side, BOX, u - 0.085, u - 0.048, zc - wh / 2, zc + wh / 2, 0.008, SH)
                    _wall_slab(bm, side, BOX, u + 0.048, u + 0.085, zc - wh / 2, zc + wh / 2, 0.008, SH)
                if hs < 0.35:
                    _L(bm, 6, 'Stains')                                                                     # 빗물 자국
                    _wall_slab(bm, side, BOX, u - 0.012, u + 0.012, max(0.05, zc - wh / 2 - 0.13), zc - wh / 2 - 0.016, 0.003, PD)
                if fi == len(floors) - 1 and 0.62 < hs < 0.8:
                    _L(bm, 6, 'Planters')                                                                   # 창턱 화분
                    px, py = _side_pt(side, BOX, u, 0.03)
                    zs = zc - wh / 2
                    G.box(bm, px - 0.018, px + 0.018, py - 0.014, py + 0.014, zs, zs + 0.028, TC)
                    _clump(bm, (px, py, zs + 0.05), 0.03, 0.026, 0.03, 1, 0.2, seed + k + si, FO)
    _L(bm, 6, 'Stains')                                                                                     # 모서리 굽도리 위 이끼 얼룩(늘 있다)
    _wall_slab(bm, 'F', BOX, X0 + 0.02, X0 + 0.11, 0.045, 0.085, 0.003, FO)
    _wall_slab(bm, 'R', BOX, Y1 - 0.10, Y1 - 0.02, 0.045, 0.075, 0.003, FO)
    if two:
        _L(bm, 4, 'Balcony')                                                                                # 나무 발코니(앞)
        zb = h * 0.48 + 0.011
        G.box(bm, X0 + 0.06, X1 - 0.06, Y0 - 0.075, Y0, zb, zb + 0.016, TB)
        G.box(bm, X0 + 0.06, X1 - 0.06, Y0 - 0.075, Y0 - 0.065, zb + 0.016, zb + 0.07, TB)
        for k in range(7):
            x = X0 + 0.07 + (X1 - X0 - 0.14) * k / 6
            G.box(bm, x - 0.006, x + 0.006, Y0 - 0.073, Y0 - 0.061, zb, zb + 0.07, TB)

def mk_house(seed):
    """로마 집(인술라/도무스) — 붉은 기와 박공. 폭 1 × 깊이 0.8 × 벽 높이 0.45~0.8 + 박공(키 1.0으로 정규화).
    재질: 0 회반죽 1 기와 2 창 속 3 회반죽 짙은 4 회반죽 밝은 5 기와 짙은 6 기와 밝은 7 나무 8 덧문 9 문 속 10 화분 잎 11 화분
    L0 벽·지붕 기와면 · L1 창·문·가게 속, 처마 밑 짙은 띠 · L2 굽도리·층 띠·창턱·문틀·처마 끝·박공 끝 테 · L3 기와 골 줄
    L4 문짝·덧문·발코니·가게 계산대 · L5 코니스 윗선·용마루 · L6 빗물 자국·이끼·화분"""
    bm = bmesh.new()
    PL, RF, DK, PD, PH, RD, RH, TB, SH, VD, FO, TC = range(12)
    h = 0.45 + 0.35 * R.hash01(seed, 1)
    two = h >= 0.6
    BOX = (-0.5, 0.5, -0.4, 0.4)
    X0, X1, Y0, Y1 = BOX
    _house_shell(bm, BOX, h, two, seed, (PL, DK, PD, PH, TB, SH, VD, FO, TC))
    # 지붕: 박공(용마루 방향 X 또는 Y). L0 기와면 · L3 기와 골 줄 · L2 처마 끝 · L5 용마루
    rh = 0.22; ov = 0.045
    ax = 'X' if R.hash01(seed, 2) > 0.5 else 'Y'
    nst = 9
    if ax == 'X':
        a0, a1, b0, b1 = X0 - ov, X1 + ov, Y0 - ov, Y1 + ov
    else:
        a0, a1, b0, b1 = Y0 - ov, Y1 + ov, X0 - ov, X1 + ov
    bm_ = (b0 + b1) / 2
    ze = h - rh * ov / (bm_ - b0)            # 처마 끝 높이: 벽 선에서 지붕이 벽 윗면(h)에 닿는다(틈 없음)
    zr = ze + rh
    def RP_(a, b, z):
        return (a, b, z) if ax == 'X' else (b, a, z)
    _L(bm, 0, 'Roof', {RD: (3, 'TileRows')})
    for i in range(nst):
        u0 = a0 + (a1 - a0) * i / nst; u1 = a0 + (a1 - a0) * (i + 1) / nst
        um = u0 + (u1 - u0) * 0.78
        for (ea, eb) in ((b0, bm_), (b1, bm_)):
            _quad(bm, [RP_(u0, ea, ze), RP_(um, ea, ze), RP_(um, eb, zr), RP_(u0, eb, zr)], RF)
            _quad(bm, [RP_(um, ea, ze), RP_(u1, ea, ze), RP_(u1, eb, zr), RP_(um, eb, zr)], RD)
    _L(bm, 2, 'EaveEdge')
    for ea in (b0, b1):
        _quad(bm, [RP_(a0, ea, ze - 0.022), RP_(a1, ea, ze - 0.022), RP_(a1, ea, ze), RP_(a0, ea, ze)], RD)
    _L(bm, 0, 'Walls')
    for ga in (a0 + ov, a1 - ov):                                                                            # 박공벽
        _quad(bm, [RP_(ga, b0 + ov, h), RP_(ga, b1 - ov, h), RP_(ga, bm_, zr)], PL)
    _L(bm, 2, 'GableTrim')
    for ga in (a0, a1):
        _quad(bm, [RP_(ga, b0, ze - 0.02), RP_(ga, bm_, zr - 0.02), RP_(ga, bm_, zr), RP_(ga, b0, ze)], RD)
        _quad(bm, [RP_(ga, b1, ze - 0.02), RP_(ga, bm_, zr - 0.02), RP_(ga, bm_, zr), RP_(ga, b1, ze)], RD)
    _L(bm, 5, 'Ridge')
    if ax == 'X':
        G.box(bm, a0, a1, bm_ - 0.018, bm_ + 0.018, zr - 0.012, zr + 0.014, RH)
    else:
        G.box(bm, bm_ - 0.018, bm_ + 0.018, a0, a1, zr - 0.012, zr + 0.014, RH)
    _flush(bm)
    return bm

def mk_house_flat(seed):
    """평지붕 인술라(2~3층, 지붕 테라스). 폭 1 × 깊이 0.8 × 높이 0.75~0.95(키 1.0으로 정규화). 재질은 mk_house와 같은 12칸.
    L0 벽·테라스 바닥 · L1 창·문·가게 속·처마 밑 띠·난간 안쪽 그늘 · L2 굽도리·층 띠·창턱·문틀·난간·코니스 · L3 테라스 바닥 줄눈(코치오페스토 판)
    L4 문짝·덧문·발코니·계단 지붕집(작은 기와 외쪽 지붕) · L5 난간 윗선·코니스 윗선·계단집 용마루 · L6 얼룩·이끼·화분(문 옆·테라스)"""
    bm = bmesh.new()
    PL, RF, DK, PD, PH, RD, RH, TB, SH, VD, FO, TC = range(12)
    h = 0.75 + 0.20 * R.hash01(seed, 1)
    BOX = (-0.5, 0.5, -0.4, 0.4)
    X0, X1, Y0, Y1 = BOX
    _house_shell(bm, BOX, h, True, seed, (PL, DK, PD, PH, TB, SH, VD, FO, TC))
    pt, ph_ = 0.035, 0.055                                                                                   # 난간 두께·높이
    zt0 = h + 0.014                                                                                          # 테라스 윗면(벽 윗면보다 0.014 위: z-파이팅 0)
    _L(bm, 0, 'Terrace')
    G.box(bm, X0 + pt, X1 - pt, Y0 + pt, Y1 - pt, h, zt0, TC)                                               # 테라스 바닥
    _L(bm, 3, 'TerraceTiles')
    for k in range(1, 6):                                                                                    # 판 줄눈
        x = X0 + pt + (X1 - X0 - 2 * pt) * k / 6
        G.box(bm, x - 0.004, x + 0.004, Y0 + pt, Y1 - pt, zt0, zt0 + 0.010, PD)
    for k in range(1, 4):
        y = Y0 + pt + (Y1 - Y0 - 2 * pt) * k / 4
        G.box(bm, X0 + pt, X1 - pt, y - 0.004, y + 0.004, zt0, zt0 + 0.010, PD)
    _L(bm, 2, 'Parapet')                                                                                     # 난간 벽 네 변
    for (x0, x1, y0, y1) in ((X0, X1, Y0, Y0 + pt), (X0, X1, Y1 - pt, Y1), (X0, X0 + pt, Y0, Y1), (X1 - pt, X1, Y0, Y1)):
        G.box(bm, x0, x1, y0, y1, h, h + ph_, PL)
    _L(bm, 1, 'ParapetShade')                                                                                # 난간 안쪽 그늘(뒤·오른쪽 난간의 안쪽 면이 보인다)
    G.box(bm, X0 + pt, X1 - pt, Y1 - pt - 0.004, Y1 - pt, h + 0.006, h + ph_ - 0.008, PD)
    G.box(bm, X0 + pt, X0 + pt + 0.004, Y0 + pt, Y1 - pt, h + 0.006, h + ph_ - 0.008, PD)
    _L(bm, 5, 'ParapetLight')                                                                                # 난간 윗선
    for (x0, x1, y0, y1) in ((X0, X1, Y0, Y0 + pt), (X0, X1, Y1 - pt, Y1), (X0, X0 + pt, Y0, Y1), (X1 - pt, X1, Y0, Y1)):
        G.box(bm, x0 - 0.006, x1 + 0.006, y0 - 0.006, y1 + 0.006, h + ph_, h + ph_ + 0.012, PH)
    # L4 계단 지붕집(뒤-왼쪽 모서리): 작은 상자 + 기와 외쪽 지붕
    hx0, hx1, hy0, hy1 = X0 + pt + 0.04, X0 + pt + 0.30, Y1 - pt - 0.24, Y1 - pt - 0.02
    zt = h + 0.13
    _L(bm, 4, 'StairHut')
    G.box(bm, hx0, hx1, hy0, hy1, h + 0.006, zt, PL)
    _L(bm, 1, 'Openings')
    G.box(bm, hx0 + 0.07, hx0 + 0.16, hy0 - 0.004, hy0 + 0.002, h + 0.01, zt - 0.03, VD)                   # 계단집 문(앞)
    _L(bm, 4, 'StairHut', {RD: (3, 'TileRows')})
    _tile_quad(bm, (hx0 - 0.02, hy0 - 0.03, zt), (hx1 + 0.02, hy0 - 0.03, zt), (hx1 + 0.02, hy1 + 0.02, zt + 0.05), (hx0 - 0.02, hy1 + 0.02, zt + 0.05), 5, RF, RD)
    _L(bm, 5, 'Ridge')
    G.box(bm, hx0 - 0.022, hx1 + 0.022, hy1 + 0.005, hy1 + 0.025, zt + 0.045, zt + 0.06, RH)
    # L6 테라스 화분 3 · 빨래 막대
    _L(bm, 6, 'Planters')
    for k in range(3):
        px = X1 - pt - 0.06 - 0.12 * k; py = Y0 + pt + 0.07 + 0.05 * (k % 2)
        G.box(bm, px - 0.025, px + 0.025, py - 0.025, py + 0.025, h + 0.006, h + 0.05, TC)
        _clump(bm, (px, py, h + 0.085), 0.038, 0.036, 0.042, 1, 0.2, seed + 60.0 + k, FO)
    _L(bm, 6, 'Laundry')
    _tube(bm, (X0 + 0.40, Y0 + 0.30, h + 0.11), (X1 - 0.12, Y0 + 0.30, h + 0.11), 0.004, 0.004, 4, TB)
    for k in range(3):
        x = X0 + 0.46 + 0.12 * k
        G.box(bm, x - 0.03, x + 0.03, Y0 + 0.297, Y0 + 0.303, h + 0.05, h + 0.108, TC if k % 2 else PH)
    _flush(bm)
    return bm

def mk_house_atrium(seed):
    """안뜰 도무스(아트리움): 단층 고리 건물 + 안쪽으로 기운 기와 지붕(콤플루비움) + 안뜰 물받이(임플루비움). 폭 1.2 × 깊이 1.0(키 1.0으로 정규화).
    재질: mk_house 12칸 + 12 물 + 13 물 밝은
    L0 바깥벽·고리 지붕 기와면 · L1 안뜰 바닥 그늘·문 속·창 속·안쪽 처마 밑 · L2 굽도리·코니스·안뜰 네 기둥·문틀 · L3 기와 골 줄·안뜰 바닥 판 줄눈
    L4 문짝·작은 창 덧문·문 옆 벤치 · L5 용마루 고리·코니스 윗선 · L6 임플루비움 물·물결·안뜰 화분·이끼"""
    bm = bmesh.new()
    PL, RF, DK, PD, PH, RD, RH, TB, SH, VD, FO, TC, WA, WH = range(14)
    h = 0.40 + 0.08 * R.hash01(seed, 1)
    A, B = 0.60, 0.50                    # 바깥 반폭
    a, b = 0.17, 0.14                    # 안뜰 구멍 반폭
    ra, rb = (A + a) / 2, (B + b) / 2    # 용마루 고리
    rh = 0.16
    _L(bm, 0, 'Walls')
    for (x0, x1, y0, y1) in ((-A, A, -B, -b), (-A, A, b, B), (-A, -a, -b, b), (a, A, -b, b)):               # 고리 벽(안뜰 둘레까지)
        G.box(bm, x0, x1, y0, y1, 0.0, h, PL)
    ring = lambda e, w: ((-A - e, A + e, -B - e, -B + w), (-A - e, A + e, B - w, B + e), (-A - e, -A + w, -B + w, B - w), (A - w, A + e, -B + w, B - w))
    _L(bm, 2, 'Plinth')                                                                                      # 바깥 굽도리(고리: 안뜰을 덮지 않는다)
    for (x0, x1, y0, y1) in ring(0.008, 0.02):
        G.box(bm, x0, x1, y0, y1, 0.0, 0.04, PD)
    _L(bm, 1, 'CourtShade')                                                                                  # 안뜰 바닥(그늘진 안쪽)
    G.box(bm, -a, a, -b, b, 0.0, 0.012, DK)
    _L(bm, 3, 'CourtPaving')
    for k in range(1, 4):
        x = -a + 2 * a * k / 4
        G.box(bm, x - 0.003, x + 0.003, -b, b, 0.012, 0.014, PD)
    _L(bm, 1, 'EaveShade')                                                                                   # 안쪽 처마 밑 짙은 띠
    for (x0, x1, y0, y1) in ((-a, a, -b, -b + 0.006), (-a, a, b - 0.006, b), (-a, -a + 0.006, -b, b), (a - 0.006, a, -b, b)):
        G.box(bm, x0, x1, y0, y1, h - 0.05, h, VD)
    _L(bm, 5, 'CorniceLight')                                                                                # 바깥 코니스 윗선(고리)
    for (x0, x1, y0, y1) in ring(0.014, 0.02):
        G.box(bm, x0, x1, y0, y1, h - 0.014, h, PH)
    # 고리 지붕: 바깥 처마(z h) → 용마루(z h + rh) → 안쪽 처마(z h). 8면, 모두 평면
    O = [(-A, -B), (A, -B), (A, B), (-A, B)]
    Rg = [(-ra, -rb), (ra, -rb), (ra, rb), (-ra, rb)]
    I = [(-a, -b), (a, -b), (a, b), (-a, b)]
    zr = h + rh
    _L(bm, 0, 'Roof', {RD: (3, 'TileRows')})
    for i in range(4):
        j = (i + 1) % 4
        _tile_quad(bm, (*O[i], h), (*O[j], h), (*Rg[j], zr), (*Rg[i], zr), 8, RF, RD)                       # 바깥 비탈
        _tile_quad(bm, (*I[j], h), (*I[i], h), (*Rg[i], zr), (*Rg[j], zr), 4, RF, RD)                       # 안쪽 비탈(안뜰로 기운다)
    _L(bm, 5, 'Ridge')
    for i in range(4):
        j = (i + 1) % 4
        p, q = Vector((*Rg[i], zr)), Vector((*Rg[j], zr))
        _tube(bm, p, q, 0.012, 0.012, 4, RH)
    _L(bm, 2, 'Columns')                                                                                     # 안뜰 네 모서리 기둥(테트라스틸)
    for (x, y) in ((-a + 0.025, -b + 0.025), (a - 0.025, -b + 0.025), (a - 0.025, b - 0.025), (-a + 0.025, b - 0.025)):
        G.cyl(bm, x, y, 0.012, 0.012, h - 0.05, 8, PH)
    # 문(앞 −y) · 창
    _L(bm, 1, 'Openings')
    _wall_slab(bm, 'F', (-A, A, -B, B), -0.07, 0.07, 0.04, 0.27, 0.004, VD)
    for u in (-0.40, 0.40):
        _wall_slab(bm, 'F', (-A, A, -B, B), u - 0.035, u + 0.035, 0.20, 0.29, 0.004, DK)
    for u in (-0.25, 0.10):
        _wall_slab(bm, 'R', (-A, A, -B, B), u - 0.035, u + 0.035, 0.20, 0.29, 0.004, DK)
    _L(bm, 2, 'Frames')
    _wall_slab(bm, 'F', (-A, A, -B, B), -0.09, 0.09, 0.27, 0.295, 0.012, PH)
    _wall_slab(bm, 'F', (-A, A, -B, B), -0.09, -0.07, 0.04, 0.27, 0.010, PH)
    _wall_slab(bm, 'F', (-A, A, -B, B), 0.07, 0.09, 0.04, 0.27, 0.010, PH)
    _L(bm, 4, 'Door')
    _wall_slab(bm, 'F', (-A, A, -B, B), -0.067, -0.005, 0.042, 0.265, 0.009, TB)
    _wall_slab(bm, 'F', (-A, A, -B, B), 0.03, 0.067, 0.042, 0.265, 0.009, TB)
    _L(bm, 4, 'Shutters')
    for u in (-0.40, 0.40):
        _wall_slab(bm, 'F', (-A, A, -B, B), u - 0.065, u - 0.038, 0.20, 0.29, 0.008, SH)
    _L(bm, 4, 'Bench')                                                                                       # 문 옆 돌 벤치
    G.box(bm, 0.14, 0.32, -B - 0.05, -B - 0.004, 0.0, 0.05, PH)
    # L6 임플루비움(물)·물결·안뜰 화분·이끼
    ia, ib = a * 0.55, b * 0.55
    _L(bm, 2, 'Curb')                                                                                        # 물받이 테(고리, 물을 덮지 않는다)
    for (x0, x1, y0, y1) in ((-ia - 0.014, ia + 0.014, -ib - 0.014, -ib), (-ia - 0.014, ia + 0.014, ib, ib + 0.014),
                             (-ia - 0.014, -ia, -ib, ib), (ia, ia + 0.014, -ib, ib)):
        G.box(bm, x0, x1, y0, y1, 0.012, 0.034, PH)
    _L(bm, 6, 'Impluvium', {WH: (6, 'Ripples')})
    G.box(bm, -ia, ia, -ib, ib, 0.012, 0.024, WA)
    G.box(bm, -ia * 0.6, ia * 0.2, -ib * 0.2, ib * 0.1, 0.024, 0.030, WH)
    _L(bm, 6, 'Planters')
    for (x, y) in ((-a + 0.05, b - 0.05), (a - 0.05, b - 0.05)):
        G.box(bm, x - 0.016, x + 0.016, y - 0.016, y + 0.016, 0.012, 0.04, TC)
        _clump(bm, (x, y, 0.07), 0.026, 0.024, 0.032, 1, 0.2, seed + x * 10, FO)
    _L(bm, 6, 'Stains')
    _wall_slab(bm, 'F', (-A, A, -B, B), -A + 0.02, -A + 0.13, 0.04, 0.08, 0.003, FO)
    _flush(bm)
    return bm

# ───────────────────────── 노점·암포라·수레·배 ─────────────────────────
def mk_stall(seed):
    """노점(키 1.0으로 정규화, 폭 약 1.46): 흰·빨간 줄무늬 차양 + 나무 계산대 + 물건.
    재질: 0 나무 1 차양 2 질그릇 3 나무 짙은 4 차양 둘째 색 5 나무 밝은 6 짐(바구니·천) 7 짐 짙은 8 과일 9 속 10 질그릇 짙은 11 아마천
    L0 계산대·차양 덩어리 · L1 윗판 밑 짙은 홈·항아리 입·바구니 속 · L2 윗판·기둥 4 · L3 차양 줄무늬·앞판 판자 줄
    L4 차양 끝 술 장식·항아리·바구니·천 두루마리 · L5 용마루 밝은 색 · L6 과일·땅의 암포라·과일 상자"""
    bm = bmesh.new()
    TB, AW, TC, WD, AW2, WH, GD, GDD, FR, VD, TCD, LN = range(12)
    _L(bm, 0, 'Counter')
    G.box(bm, -0.48, 0.48, -0.25, 0.22, 0.0, 0.31, TB)
    _L(bm, 3, 'Planks')
    for k in range(7):
        x = -0.48 + 0.96 * (k + 1) / 8
        G.box(bm, x - 0.006, x + 0.006, -0.256, -0.248, 0.02, 0.30, WD)
    _L(bm, 2, 'Board')
    G.box(bm, -0.5, 0.5, -0.285, 0.24, 0.31, 0.345, WH)
    _L(bm, 1, 'Groove')
    G.box(bm, -0.47, 0.47, -0.262, -0.25, 0.285, 0.31, VD)
    _L(bm, 2, 'Posts')
    for x in (-0.47, 0.47):
        for y in (-0.25, 0.21):
            G.box(bm, x - 0.02, x + 0.02, y - 0.02, y + 0.02, 0.345, 0.775, WD)
    ye0, ye1, yr, ze, zr = -0.40, 0.38, -0.01, 0.765, 0.94
    xs = [-0.56 + 1.12 * i / 8 for i in range(9)]
    _L(bm, 0, 'Awning', {AW2: (3, 'Stripes')})
    for i in range(8):
        mi = AW if i % 2 == 0 else AW2
        _quad(bm, [(xs[i], ye0, ze), (xs[i + 1], ye0, ze), (xs[i + 1], yr, zr), (xs[i], yr, zr)], mi)
        _quad(bm, [(xs[i], yr, zr), (xs[i + 1], yr, zr), (xs[i + 1], ye1, ze), (xs[i], ye1, ze)], mi)
    for xg in (-0.56, 0.56):
        _quad(bm, [(xg, ye0, ze), (xg, ye1, ze), (xg, yr, zr)], AW)
    _L(bm, 5, 'Ridge')
    G.box(bm, -0.58, 0.58, yr - 0.014, yr + 0.014, zr - 0.006, zr + 0.016, WH)
    _L(bm, 4, 'Fringe')
    for ye in (ye0, ye1):
        for i in range(14):
            x0 = -0.56 + 1.12 * i / 14; x1 = -0.56 + 1.12 * (i + 1) / 14
            _quad(bm, [(x0, ye, ze), (x1, ye, ze), ((x0 + x1) / 2, ye, ze - 0.06)], AW2 if i % 2 == 0 else AW)
    _L(bm, 4, 'Goods', {VD: (1, 'JarMouths'), GDD: (1, 'JarMouths')})
    for k, (x, y) in enumerate(((-0.36, -0.04), (-0.24, 0.06))):
        _lathe(bm, [(0.0, 0.345), (0.04, 0.355), (0.055, 0.40), (0.05, 0.45), (0.025, 0.48), (0.03, 0.495)], 10, TC, cx=x, cy=y,
               mif=lambda j, kk, a: TCD if j == 2 else TC, cap_top=False)
        _lathe(bm, [(0.024, 0.493), (0.0, 0.493)], 10, VD, cx=x, cy=y, cap_top=False)
    _lathe(bm, [(0.075, 0.345), (0.10, 0.40), (0.105, 0.415)], 12, GD, cx=0.02, cy=-0.05, cap_top=False, cap_bot=False)
    _lathe(bm, [(0.098, 0.40), (0.0, 0.40)], 12, GDD, cx=0.02, cy=-0.05, cap_top=False)
    for k, y in enumerate((-0.12, -0.04, 0.04)):
        _tube(bm, (0.20, y, 0.375), (0.40, y, 0.375), 0.032, 0.032, 8, (LN, AW2, GD)[k])
    _L(bm, 6, 'Fruit')
    for k in range(7):
        a = 2 * math.pi * k / 7 + seed
        _clump(bm, (0.02 + 0.055 * math.cos(a), -0.05 + 0.055 * math.sin(a), 0.418), 0.032, 0.032, 0.03, 1, 0.0, seed + k, FR)
    _clump(bm, (0.02, -0.05, 0.44), 0.034, 0.034, 0.032, 1, 0.0, seed + 17.0, FR)
    _L(bm, 6, 'GroundGoods', {VD: (1, 'JarMouths')})
    for k, (x, y) in enumerate(((0.60, -0.14), (0.63, 0.04))):
        _lathe(bm, [(0.0, 0.0), (0.03, 0.02), (0.062, 0.10), (0.06, 0.17), (0.034, 0.225), (0.02, 0.27), (0.03, 0.285)], 10, TC,
               cx=x, cy=y, mif=lambda j, kk, a: TCD if j == 3 else TC, cap_top=False)
        _lathe(bm, [(0.02, 0.283), (0.0, 0.283)], 10, VD, cx=x, cy=y, cap_top=False)
    G.box(bm, -0.70, -0.55, -0.12, 0.04, 0.0, 0.10, WD)
    G.box(bm, -0.69, -0.56, -0.11, 0.03, 0.10, 0.104, VD)
    for k in range(4):
        _clump(bm, (-0.66 + 0.06 * (k % 2), -0.08 + 0.07 * (k // 2), 0.118), 0.032, 0.032, 0.026, 1, 0.0, seed + 40 + k, FR)
    _flush(bm)
    return bm

def mk_amphora(seed):
    """암포라(키 1.0으로 정규화). 재질: 0 질그릇 1 질그릇 짙은 2 질그릇 밝은 3 입 속 4 흰 글씨
    L0 몸통 · L1 입 속 · L2 목 테·손잡이 둘 · L3 칠한 띠 두 줄 · L4 뾰족한 굽 · L5 위를 보는 어깨 면·입술 윗면 · L6 붓글씨 표(티툴루스)·마개 끈"""
    bm = bmesh.new()
    TC, TD, TH, VD, WH = range(5)
    _L(bm, 4, 'Toe')
    _lathe(bm, [(0.0, 0.0), (0.022, 0.015), (0.03, 0.05)], 12, TC, cap_top=False)
    prof = [(0.03, 0.05), (0.075, 0.10), (0.125, 0.17), (0.155, 0.27), (0.157, 0.30), (0.157, 0.33),
            (0.152, 0.40), (0.150, 0.42), (0.146, 0.44), (0.118, 0.52), (0.065, 0.59), (0.046, 0.64), (0.046, 0.69), (0.064, 0.705), (0.064, 0.75)]
    def mamph(j, k, a):
        if j in (4, 7):
            return TD                                            # 칠한 띠(L3)
        if j in (8, 9):
            return TH                                            # 어깨(위를 본다, L5)
        if j == 13:
            return TH                                            # 입술 테 윗면 쪽
        return TC
    _L(bm, 0, 'Body', {TD: (3, 'Bands'), TH: (5, 'ShoulderLight')})
    _lathe(bm, prof, 12, TC, mif=mamph, cap_top=False)
    _L(bm, 1, 'Mouth', {TH: (5, 'ShoulderLight')})
    _lathe(bm, [(0.064, 0.75), (0.044, 0.75), (0.040, 0.715), (0.0, 0.715)], 12, VD, cap_top=False,
           mif=lambda j, k, a: TH if j == 0 else VD)
    _L(bm, 2, 'Handles')
    for sx in (-1, 1):
        _chain(bm, [(sx * 0.046, 0.0, 0.665), (sx * 0.11, 0.0, 0.66), (sx * 0.125, 0.0, 0.60), (sx * 0.112, 0.0, 0.53)],
               [0.016, 0.016, 0.016, 0.016], 6, TC)
    _L(bm, 2, 'NeckRing')
    _lathe(bm, [(0.050, 0.685), (0.052, 0.69), (0.052, 0.70), (0.050, 0.705)], 12, TC, cap_top=False)
    _L(bm, 6, 'Titulus')
    G.box(bm, -0.035, 0.035, -0.159, -0.150, 0.33, 0.37, WH)
    _flush(bm)
    return bm

def mk_cart(seed):
    """짐수레(플라우스트룸, 키 1.0으로 정규화, 길이 약 3.35): 통바퀴 둘(세운 바퀴, 축 y) + 짐칸 + 끌채 + 짐(석회·포촐라나 자루).
    재질: 0 나무 1 석회 2 나무 짙은 3 속 4 나무 밝은 5 자루 6 질그릇 7 가죽
    L0 짐칸 바닥 · L1 짐칸 바닥 속 · L2 옆판·끌채·멍에·굴대 · L3 옆판 판자 줄·통판 이음 띠 · L4 통바퀴·바퀴 테·바퀴통 · L5 옆판 윗선 · L6 짐(자루·누운 암포라)"""
    bm = bmesh.new()
    TB, LM, WD, VD, WH, SK, TC, LE = range(8)
    zb = 0.20
    _L(bm, 0, 'Bed')
    G.box(bm, -0.45, 0.45, -0.24, 0.24, zb, zb + 0.04, TB)
    _L(bm, 1, 'BedShade')
    G.box(bm, -0.42, 0.42, -0.21, 0.21, zb + 0.04, zb + 0.044, VD)
    for (x0, x1, y0, y1) in ((-0.45, 0.45, -0.24, -0.21), (-0.45, 0.45, 0.21, 0.24), (-0.45, -0.42, -0.21, 0.21), (0.42, 0.45, -0.21, 0.21)):
        _L(bm, 2, 'Sides')
        G.box(bm, x0, x1, y0, y1, zb + 0.04, zb + 0.17, TB)
        _L(bm, 5, 'RimLight')
        G.box(bm, x0 - 0.004, x1 + 0.004, y0 - 0.004, y1 + 0.004, zb + 0.17, zb + 0.185, WH)
        _L(bm, 3, 'Planks')
        G.box(bm, x0 - 0.003, x1 + 0.003, y0 - 0.003, y1 + 0.003, zb + 0.10, zb + 0.108, WD)
    _L(bm, 2, 'Shaft')
    _tube(bm, (0.45, 0.0, zb + 0.06), (1.02, 0.0, zb + 0.10), 0.02, 0.016, 6, WD)
    G.box(bm, 0.98, 1.02, -0.20, 0.20, zb + 0.09, zb + 0.13, WD)
    _tube(bm, (0.0, -0.31, 0.22), (0.0, 0.31, 0.22), 0.022, 0.022, 6, VD)
    for sy in (-1, 1):
        y = 0.285 * sy
        _L(bm, 4, 'Wheels')
        _tube(bm, (0.0, y - 0.025, 0.22), (0.0, y + 0.025, 0.22), 0.22, 0.22, 16, WD)                     # 바퀴 테
        _tube(bm, (0.0, y - 0.033, 0.22), (0.0, y + 0.033, 0.22), 0.175, 0.175, 16, TB)                   # 통판
        _tube(bm, (0.0, y - 0.05, 0.22), (0.0, y + 0.05, 0.22), 0.05, 0.05, 8, WD)                        # 바퀴통
        _L(bm, 3, 'WheelBoards')
        for k in range(2):
            G.box(bm, -0.012 + (k - 0.5) * 0.12, 0.012 + (k - 0.5) * 0.12, y - 0.036, y + 0.036, 0.06, 0.38, WD)
    _L(bm, 6, 'Load')
    for k in range(4):
        x = -0.30 + 0.2 * k
        _clump(bm, (x, -0.02 + 0.06 * (k % 2), zb + 0.12), 0.095, 0.13, 0.07, 2, 0.12, seed + k, SK, SK, 0.8)
    _tube(bm, (-0.38, 0.14, zb + 0.10), (-0.10, 0.17, zb + 0.10), 0.045, 0.02, 8, TC)                       # 누운 암포라
    _flush(bm)
    return bm

def _hull(bm, pts, z0, z1, mis, scale=(0.9, 0.96, 1.0)):
    """배 몸통: 판자 띠(strake)를 겹겹이(위로 갈수록 넓게). mis = 띠마다 재질"""
    n = len(mis)
    for i in range(n):
        za = z0 + (z1 - z0) * i / n; zb = z0 + (z1 - z0) * (i + 1) / n
        s = scale[min(i, len(scale) - 1)]
        G.prism(bm, [(x * s, y * s) for x, y in pts], za, zb, mis[i])

def _rim(bm, outer, inner, z0, z1, mi, mi_top=None):
    """뱃전 테(바깥 다각형과 안쪽 다각형 사이 고리). mi_top이 있으면 윗면만 그 재질(L5 윗선)"""
    n = len(outer)
    O0 = [bm.verts.new((x, y, z0)) for x, y in outer]; O1 = [bm.verts.new((x, y, z1)) for x, y in outer]
    I1 = [bm.verts.new((x, y, z1)) for x, y in inner]; I0 = [bm.verts.new((x, y, z0)) for x, y in inner]
    mt = mi if mi_top is None else mi_top
    for k in range(n):
        k2 = (k + 1) % n
        for q, mm in (([O0[k], O0[k2], O1[k2], O1[k]], mi), ([O1[k], O1[k2], I1[k2], I1[k]], mt), ([I1[k], I1[k2], I0[k2], I0[k]], mi)):
            f = bm.faces.new(q); f.material_index = mm

def mk_barge(seed):
    """강 바지선(코디카리아, 키 1.0 = 끄는 돛대 꼭대기): 판자 띠 몸통 + 짙은 짐칸 + 뱃전 테 + 끄는 돛대 + 키 노 + 짐(석회 자루·암포라).
    재질: 0 나무 1 석회 2 나무 짙은 3 속 4 나무 밝은 5 자루 6 질그릇
    L0 몸통·갑판 · L1 갑판 판자 틈·짐칸 속 · L2 뱃전 테·끄는 돛대 · L3 판자 띠(짙은 아래 띠) · L4 키 노·노 받침 · L5 뱃전 윗선 · L6 짐"""
    bm = bmesh.new()
    TB, LM, WD, VD, WH, SK, TC = range(7)
    pts = [(-1.0, -0.21), (0.70, -0.21), (0.92, -0.10), (1.0, 0.0), (0.92, 0.10), (0.70, 0.21), (-1.0, 0.21), (-1.08, 0.0)]
    _L(bm, 0, 'Hull', {WD: (3, 'Strakes')})
    _hull(bm, pts, 0.0, 0.18, [WD, TB, TB], (0.90, 0.96, 1.0))
    inner = [(x * 0.90, y * 0.80) for x, y in pts]
    _L(bm, 0, 'Deck')
    G.prism(bm, inner, 0.18, 0.183, WD)
    _L(bm, 1, 'Hold')
    for k in range(10):
        x = -0.86 + 0.15 * k
        G.box(bm, x - 0.007, x + 0.007, -0.160, 0.160, 0.183, 0.186, VD)
    _L(bm, 2, 'Gunwale', {WH: (5, 'GunwaleLight')})
    _rim(bm, pts, inner, 0.18, 0.205, TB, WH)
    _L(bm, 2, 'Mast')
    _tube(bm, (0.42, 0.0, 0.18), (0.42, 0.0, 0.74), 0.02, 0.015, 6, WD)
    _L(bm, 4, 'SteeringOar')
    _tube(bm, (-0.95, 0.17, 0.36), (-1.13, 0.25, 0.02), 0.014, 0.014, 6, WD)
    G.box(bm, -1.19, -1.07, 0.235, 0.265, 0.0, 0.12, WD)
    _L(bm, 6, 'Load')
    for k in range(6):
        x = -0.78 + 0.22 * k
        _clump(bm, (x, -0.06 + 0.12 * (k % 2), 0.235), 0.10, 0.09, 0.055, 2, 0.12, seed + k, SK, SK, 0.8)
    for k in range(3):
        x = 0.55 + 0.1 * k; y = -0.08 + 0.08 * k
        _lathe(bm, [(0.0, 0.183), (0.03, 0.20), (0.05, 0.26), (0.03, 0.32), (0.018, 0.36), (0.024, 0.37)], 8, TC, cx=x, cy=y, cap_top=True)
    _flush(bm)
    return bm

def mk_ship(seed):
    """상선(코르비타, 키 1.0 = 돛대 꼭대기): 판자 띠 몸통 + 백조 목 고물 + 돛대·활대·줄무늬 네모 돛 + 고물 선실 + 짐.
    재질: 0 나무 1 흰 돛 2 질그릇 3 나무 짙은 4 속 5 나무 밝은 6 돛 줄무늬 7 자루
    L0 몸통·갑판·돛 · L1 갑판 판자 틈·짐칸 입구 · L2 뱃전 테·돛대·활대 · L3 판자 띠·돛 줄무늬 · L4 백조 목·이물 장식·선실·키 노
    L5 뱃전 윗선·선실 지붕 윗선 · L6 짐(암포라·자루)"""
    bm = bmesh.new()
    TB, WT, TC, WD, VD, WH, AW, SK = range(8)
    pts = [(-1.0, -0.26), (0.55, -0.26), (0.90, -0.14), (1.05, 0.0), (0.90, 0.14), (0.55, 0.26), (-1.0, 0.26), (-1.12, 0.0)]
    _L(bm, 0, 'Hull', {WD: (3, 'Strakes')})
    _hull(bm, pts, 0.0, 0.26, [WD, TB, WD, TB], (0.86, 0.92, 0.97, 1.0))
    inner = [(x * 0.90, y * 0.82) for x, y in pts]
    _L(bm, 0, 'Deck')
    G.prism(bm, inner, 0.26, 0.263, WD)
    _L(bm, 1, 'Hold')
    for k in range(7):
        x = -0.42 + 0.13 * k
        G.box(bm, x - 0.007, x + 0.007, -0.20, 0.20, 0.263, 0.266, VD)
    G.box(bm, -0.30, -0.08, -0.10, 0.10, 0.263, 0.268, VD)
    _L(bm, 2, 'Gunwale', {WH: (5, 'GunwaleLight')})
    _rim(bm, pts, inner, 0.26, 0.29, TB, WH)
    _L(bm, 4, 'SwanNeck')
    _chain(bm, [(-1.08, 0.0, 0.26), (-1.20, 0.0, 0.42), (-1.18, 0.0, 0.56), (-1.08, 0.0, 0.62)], [0.035, 0.03, 0.026, 0.02], 6, WD)
    _tube(bm, (1.02, 0.0, 0.25), (1.16, 0.0, 0.38), 0.025, 0.018, 6, WD)
    _L(bm, 4, 'Cabin')
    G.box(bm, -0.88, -0.52, -0.16, 0.16, 0.26, 0.40, TB)
    _L(bm, 5, 'CabinRoofLight')
    G.box(bm, -0.90, -0.50, -0.18, 0.18, 0.40, 0.425, WH)
    _L(bm, 4, 'SteeringOar')
    _tube(bm, (-0.95, 0.22, 0.42), (-1.15, 0.30, 0.03), 0.014, 0.014, 6, WD)
    _L(bm, 2, 'Mast')
    _tube(bm, (0.0, 0.0, 0.26), (0.0, 0.0, 1.52), 0.03, 0.022, 6, WD)
    _tube(bm, (0.04, -0.68, 1.37), (0.04, 0.68, 1.37), 0.016, 0.016, 6, WH)
    ys = [-0.62 + 1.24 * i / 6 for i in range(7)]
    _L(bm, 0, 'Sail', {AW: (3, 'SailStripes')})
    for i in range(6):
        G.box(bm, 0.046, 0.064, ys[i], ys[i + 1], 0.66, 1.355, WT if i % 2 == 0 else AW)
    _L(bm, 6, 'Load')
    for k in range(4):
        x = 0.15 + 0.11 * k; y = -0.10 + 0.07 * (k % 3)
        _lathe(bm, [(0.0, 0.263), (0.03, 0.28), (0.05, 0.34), (0.03, 0.40), (0.018, 0.44), (0.024, 0.45)], 8, TC, cx=x, cy=y, cap_top=True)
    for k in range(2):
        _clump(bm, (-0.30 + 0.16 * k, 0.05 - 0.1 * k, 0.31), 0.09, 0.08, 0.05, 2, 0.12, seed + k, SK, SK, 0.8)
    _flush(bm)
    return bm

# ───────────────────────── 원형 만들기 ─────────────────────────
def _obj_name(key):
    """원형 이름(cypress0·house_flat0) → 오브젝트 이름 조각(Cypress0·HouseFlat0)"""
    return ''.join(p[:1].upper() + p[1:] for p in key.split('_'))

def _remove_tree(ob):
    for ch in list(ob.children_recursive):
        me = ch.data if ch.type == 'MESH' else None
        bpy.data.objects.remove(ch, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)

def make_proto(name, bm, mats, smooth=False):
    """한 메시 원형 P_{이름}(place가 링크 복제한다). 옛 원형 메시를 이미 배치된 복제가 쓰고 있으면 이름만 '_prev'로 비킨다
    (각 패키지가 다시 지을 때 새 원형을 쓴다. 쓰는 곳이 없어진 옛 메시는 저장 때 사라진다)"""
    old = bpy.data.objects.get(name)
    if old:
        me = old.data; bpy.data.objects.remove(old, do_unlink=True)
        if me is not None:
            if me.users == 0:
                bpy.data.meshes.remove(me)
            else:
                me.name = name + '_prev'
    ob = R.bm_to_obj(bm, name, mats, _proto_coll(), None, smooth)
    ob.data.name = name
    return ob

def make_layered(key, bm, mats, smooth=False):
    """표시된 원형 bm을 표현 레이어 메시로 나눠 PROTO_{Obj}_root 아래에 둔다(이름 PROTO_{Obj}_L{n}_{부분}). bm은 그대로 둔다.
    반환: (루트, [층 메시])"""
    c = _proto_coll()
    obj = _obj_name(key)
    rname = 'PROTO_%s_root' % obj
    root = bpy.data.objects.get(rname)
    if root is None:
        root = bpy.data.objects.new(rname, None)
        c.objects.link(root)
    else:
        _remove_tree(root)
    root.location = (0.0, 0.0, 0.0); root.rotation_euler = (0.0, 0.0, 0.0); root.scale = (1.0, 1.0, 1.0)
    root.empty_display_size = 0.5
    parts = _split(bm)
    obs = []
    for (n, part), b2 in sorted(parts.items()):
        nm = 'PROTO_%s_L%d_%s' % (obj, n, part)
        old = bpy.data.objects.get(nm)
        if old is not None:
            me = old.data; bpy.data.objects.remove(old, do_unlink=True)
            if me is not None and me.users == 0:
                bpy.data.meshes.remove(me)
        ob = R.bm_to_obj(b2, nm, mats, c, root, smooth, recalc=False)
        ob.data.name = nm
        obs.append(ob)
    return root, obs

def _make(key, bm, mats, smooth=False, ref=None):
    """원형 하나: 키 1.0 정규화 → 법선 정리 → P_{key}(한 메시) + PROTO_{Obj}_root(층 메시). PROTO_INFO에 크기를 적는다"""
    h0 = _normalize(bm, ref)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    xs = [v.co.x for v in bm.verts]; ys = [v.co.y for v in bm.verts]; zs = [v.co.z for v in bm.verts]
    full = bm.copy()
    ob = make_proto('P_' + key, full, mats, smooth)
    root, obs = make_layered(key, bm, mats, smooth)
    bm.free()
    _LT.pop(id(bm), None)
    layers = sorted({int(m.group(1)) for m in (re.search(r'_L(\d)_', o.name) for o in obs) if m})
    info = {'h': 1.0, 'h_max': round(max(zs), 4), 'w': round(max(xs) - min(xs), 4), 'd': round(max(ys) - min(ys), 4),
            'x0': round(min(xs), 4), 'x1': round(max(xs), 4), 'y0': round(min(ys), 4), 'y1': round(max(ys), 4),
            'src_h': round(h0, 4), 'layers': layers, 'meshes': len(obs), 'root': root.name}
    for k in ('h', 'h_max', 'w', 'd', 'src_h'):
        ob[k] = info[k]
    PROTO_INFO[key] = info
    return ob

def _jobs():
    """(원형 이름, 만들기, 재질 열쇠 목록, 매끈, 키 재는 부분)"""
    tree = lambda k: [k, 'BARK', k + '_DK', k + '_HI', 'BARK_DK', 'GRASS_V']
    house = ['PLASTER', 'ROOF', 'DARK', 'PLASTER_DK', 'PLASTER_HI', 'ROOF_DK', 'ROOF_HI', 'TIMBER', 'SHUTTER', 'VOID', 'FOL_BUSH', 'TERRA_V']
    J = []
    for i in range(4):
        J.append(('cypress%d' % i, lambda i=i: mk_cypress(i * 3.1 + 1), ['FOL_CYP', 'BARK', 'FOL_CYP_DK', 'FOL_CYP_HI', 'GRASS_V'], True, None))
        J.append(('pine%d' % i, lambda i=i: mk_pine(i * 2.3 + 1), tree('FOL_PINE'), True, None))
        J.append(('olive%d' % i, lambda i=i: mk_olive(i * 1.7 + 1), tree('FOL_OLIVE'), True, None))
        J.append(('bush%d' % i, lambda i=i: mk_bush(i * 1.3 + 1, i in (1, 3)), ['FOL_BUSH', 'FOL_BUSH_DK', 'FOL_BUSH_HI', 'FLOWER', 'GRASS_V'], True, None))
        J.append(('house%d' % i, lambda i=i: mk_house(i * 5.0 + 2), house, False, None))
    J.append(('house_flat0', lambda: mk_house_flat(3.0), house, False, None))
    J.append(('house_flat1', lambda: mk_house_flat(8.0), house, False, None))
    J.append(('house_atrium0', lambda: mk_house_atrium(4.0), house + ['WATER', 'WATER_HI'], False, None))
    person = ['CLOTH', 'SKIN_V', 'HAIR_V', 'CLOTH_DK', 'CLOTH_HI', 'ACCENT', 'LEATHER', 'GOODS', 'HAIR_HI', 'FRUIT', 'GOODS_DK']
    for i in range(3):
        J.append(('person%d' % i, lambda i=i: mk_person(i, i), person, True, PERSON_REF))
    J.append(('stall', lambda: mk_stall(0), ['TIMBER', 'AWNING', 'TERRA_V', 'WOOD_DK', 'AWNING2', 'WOOD_HI', 'GOODS', 'GOODS_DK', 'FRUIT', 'VOID', 'TERRA_DK', 'LINEN'], False, None))
    J.append(('amphora', lambda: mk_amphora(0), ['TERRA_V', 'TERRA_DK', 'TERRA_HI', 'VOID', 'LINEN'], True, None))
    J.append(('cart', lambda: mk_cart(0), ['TIMBER', 'LIME', 'WOOD_DK', 'VOID', 'WOOD_HI', 'SACK', 'TERRA_V', 'LEATHER'], False, None))
    J.append(('barge', lambda: mk_barge(0), ['TIMBER', 'LIME', 'WOOD_DK', 'VOID', 'WOOD_HI', 'SACK', 'TERRA_V'], False, None))
    J.append(('ship', lambda: mk_ship(0), ['TIMBER', 'C_WHITE', 'TERRA_V', 'WOOD_DK', 'VOID', 'WOOD_HI', 'SAIL', 'SACK'], False, None))
    return J

PROTO_NAMES = [j[0] for j in _jobs()]

def build_protos(only=None):
    """원형을 모두(또는 only에 든 이름·앞머리만) 다시 짓는다. 반환 {이름: P_ 오브젝트}. 한 번에 다 지으면 약 20~40초"""
    global M
    if M is None or only is None or 'SAIL' not in M or bpy.data.materials.get('F_P_Water') is None:
        M = build_mats()
    P = {}
    for key, fn, mk, smooth, ref in _jobs():
        if only and not any(key == o or key.startswith(o) for o in only):
            continue
        P[key] = _make(key, fn(), [M[k] for k in mk], smooth, ref)
    return P

def proto_info(name):
    """원형 크기(키 1.0 기준): {'h', 'h_max', 'w'(x 길이), 'd'(y 길이), …}. 장면의 P_ 오브젝트 사용자 속성에서도 읽는다"""
    key = name[2:] if name.startswith('P_') else name
    if key in PROTO_INFO:
        return PROTO_INFO[key]
    ob = bpy.data.objects.get('P_' + key)
    if ob is None:
        return None
    vs = ob.data.vertices
    xs = [v.co.x for v in vs]; ys = [v.co.y for v in vs]; zs = [v.co.z for v in vs]
    return {'h': float(ob.get('h', max(zs))), 'h_max': max(zs), 'w': max(xs) - min(xs), 'd': max(ys) - min(ys),
            'x0': min(xs), 'x1': max(xs), 'y0': min(ys), 'y1': max(ys)}

def proto_height(name):
    """원형의 키(정규화한 원형은 1.0. 사람은 발~머리, 짐 제외)"""
    i = proto_info(name)
    return i['h'] if i else 1.0

def place(proto, X, Y, Z, s, rot_deg, coll, name=None, parent=None, local=False):
    """원형의 링크 복제. local=True면 parent 기준 지역 좌표(Blender 축). s = 화면 높이(mm) — 원형 키가 1.0이다"""
    src = bpy.data.objects[proto if proto.startswith('P_') else 'P_' + proto]
    ob = bpy.data.objects.new(name or src.name[2:], src.data)
    coll.objects.link(ob)
    if parent is not None:
        ob.parent = parent
    ob.location = Vector((X, Y, Z)) if local else R.P(X, Y, Z)
    ob.rotation_euler = (0, 0, math.radians(rot_deg))
    ob.scale = (s, s, s)
    return ob

def place_layered(proto, X, Y, Z, s, rot_deg, coll, name=None, parent=None, local=False):
    """원형을 표현 레이어 구조 그대로 배치한다: 루트 Empty '{name}_root' + 층 메시 링크 복제 '{name}_L{n}_{부분}'.
    name은 '{PKG}_{Obj}' 꼴로 준다(예: 'HERO_Stall03'). 반환: 루트"""
    key = proto[2:] if proto.startswith('P_') else proto
    obj = _obj_name(key)
    src = bpy.data.objects.get('PROTO_%s_root' % obj)
    if src is None:
        build_protos(only=[key])
        src = bpy.data.objects['PROTO_%s_root' % obj]
    nm = name or ('PROTO_' + obj + '_inst')
    r = bpy.data.objects.new(nm + '_root', None)
    coll.objects.link(r)
    r.empty_display_size = 0.5
    if parent is not None:
        r.parent = parent
    r.location = Vector((X, Y, Z)) if local else R.P(X, Y, Z)
    r.rotation_euler = (0, 0, math.radians(rot_deg))
    r.scale = (s, s, s)
    import zlib
    rnd = 1.0 + (zlib.crc32(nm.encode('utf-8')) % 100000) / 100000.0      # 한 개체의 층 메시가 같은 색 띠를 고른다(var_mat)
    r[RAND_PROP] = rnd
    pre = 'PROTO_%s_' % obj
    for ch in src.children:
        o = bpy.data.objects.new('%s_%s' % (nm, ch.name[len(pre):]), ch.data)
        coll.objects.link(o)
        o.parent = r
        o[RAND_PROP] = rnd
    return r
