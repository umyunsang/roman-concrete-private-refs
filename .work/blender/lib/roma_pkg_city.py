# roma_pkg_city — 판테온·트라야누스 시장·막센티우스 바실리카·마르켈루스 극장. 담당: city
# 오브젝트마다 표현 레이어 L0~L6(필수)를 쌓는다. 이름: {PKG}_{Obj}_L{n}_{part}, 루트 {PKG}_{Obj}_root. 지침: .work/blender/지침-일러스트-모델.md
# 받침(팔각·네모 기단)은 없다(사용자 06:06): 모든 건물은 지도 땅(Z=0) 위에 바로 서고, 바닥 포장은 땅에 묻힌 얇은 판(윗면 ≤ 0.3)이다(D13).
# b5 회차 결정(기획자 decisions)
#   D1 위치·크기의 원천은 spec(current). 상자·좌표 하드코딩 금지 → 상자는 spec landmarks[].projected_box, 평면 기하는 spec plan에서 읽는다.
#   D4 비교는 같은 종류끼리: 이 패키지는 실제 메시 외곽(화면 mm)을 재서 보고한다(예정 상자로 통과를 보고하지 않는다).
#   D8 사람 키 2.4mm(표준 랜드마크·길), 소품은 사람 키 비례(노점 높이 1.4·폭 1.8, 암포라 0.45, 사이프러스 2.5~3.0, 올리브 2.2, 우산소나무 3.0)
#   D9 벡터 일러스트: 조명·AO·그림자·Principled 0. 면 톤은 ISO_TONE만. 외곽선(L7) 없음. 점선 복원선만 정보 잉크 평면색(INK_L)
#   D11 지시선·라벨·짝 표지가 가리키는 점마다 숨긴 Empty ANCHOR_{대상}_{역할}(보이는 면 위 3D 점)
# 짓는 방식(건물별)
#   L1 판테온: 실제 치수(m)로 짓고 루트 축척 (s, s, s·kz)로 spec 상자에 맞춘다(fit_skz). 가로 s는 상자 폭, kz는 상자 높이에서 정한다
#     (d4 설계 그림과 같은 높이 과장. 콜로세움 히어로도 LocalBanana 비례로 높이를 키웠다). 사람·나무는 세로 늘림을 되돌려 원형 비례를 지킨다.
#   L2 트라야누스 시장: d4 설계 배치(마당 60×50.85 · 언덕 테라스 · 대회랑 · 오른쪽 동 · 반원)를 지역 평면 mm로 짓고 fit_skz로 맞춘다(s≈1, kz≈1).
#   L7 막센티우스 바실리카 · L9 마르켈루스 극장: spec plan(평면 원본)을 전역 등각 그대로(배율·높이 과장 없음) 평면 좌표에 짓는다.
# 지역 좌표: 루트 기준 Blender 축(x = 평면 +X, y = 평면 −Y). 보이는 면: 윗면 · 왼면(법선 −y) · 오른면(법선 +x). 앞 = (+x, −y) 쪽.
import bpy, bmesh, math, json, os, re
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import tessellate_polygon
import roma_kit as R, roma_flat as FL, roma_geo as G

COLL = 'LM_City'
DESIGN_OUT = '/Users/um-yunsang/roman-concrete-private-refs/.work/design/current/out'
SPEC = DESIGN_OUT + '/spec.json'
DECOR = False      # 16:14 사용자 결정(core 정보 오브젝트만): 건물 둘레 사람·노점·수레·암포라·나무·덤불(*_life)을 짓지 않는다. 코드는 보관
DRAWN = DESIGN_OUT + '/drawn.json'
PK = 'CITY'
H_PERSON = 2.4                     # D8 사람 키(화면 mm, 발~머리) — 표준 랜드마크·길
PROP_K = {'stall': 1.4, 'amphora': 0.45, 'cart': 0.44 / 1.475 * 2.2, 'cypress': 2.75, 'olive': 2.2, 'pine': 3.0, 'bush': 0.62}
MMK = 0.645                        # 평면 mm / 실제 m(spec L7 측랑 칸 15.17mm = 23.5 m). mm 단위 건물의 무늬 크기 환산
INK_L = '#3A2A1C'                  # 정보 잉크(58, 42, 28)
# D11 앵커 잠정 점: decisions에 괄호로 적힌 점(그 밖은 spec labels[].target_pt · detail leaders 끝 · pair_marks map_pt에서 읽는다)
ANCHOR_DECISION = {'L1_m4': (78.4, 204.6), 'L2_m3': (76.2, 111.7), 'L7_label': (212.0, 170.0), 'L7_m2': (225.0, 177.0)}

# ───────────────────────── 재질(평면색 × ISO_TONE, 조명·AO·그림자 0) ─────────────────────────
# ('b', c1, c2, c3, 줄눈, 블록폭, 줄높이, 줄눈폭)은 실제 m 단위. mm 단위 건물(L2·L7·L9)은 같은 무늬를 MMK배로 줄인 '@mm' 재질을 쓴다
DEFS = {
    # 벽돌·트래버틴·대리석(L0·L2·L3)
    'brick': ('b', '#BE7752', '#B36C49', '#C8855F', '#9A5A3D', 1.6, 0.8, 0.07),
    'brick_dk': ('f', '#A35C3E'), 'brick_hi': ('f', '#D99772'), 'brick_core': ('b', '#B5704E', '#A9643F', '#C2805A', '#8F5236', 0.9, 0.45, 0.08),
    'trav': ('b', '#DCC09A', '#D2B48C', '#E5CDA8', '#B89772', 2.2, 1.0, 0.05),
    'trav_f': ('f', '#DCC29C'), 'marble': ('f', '#ECE2CF'), 'marble_hi': ('f', '#F8F1E3'),
    'marble_fl': ('b', '#EDE3CF', '#E3D6BD', '#F3EBDC', '#C9B99C', 2.6, 2.6, 0.05),
    'seat': ('b', '#E2CCA6', '#D8BF97', '#EAD7B6', '#BFA27C', 2.4, 3.0, 0.06),
    'seat_lt': ('b', '#EBDABA', '#E1CDAA', '#F1E3C8', '#C9AF8A', 2.4, 3.0, 0.06),
    'gran_g': ('f', '#B1A99C'), 'gran_r': ('f', '#C39483'),
    'lead': ('f', '#CABEA8'), 'lead_dk': ('f', '#B1A38C'), 'lead_ring': ('f', '#DBCEB5'),
    'bronze': ('f', '#82603E'), 'bronze_hi': ('f', '#AC8655'), 'bronze_dk': ('f', '#5E4330'),
    'tile': ('b', '#B9663F', '#C6744B', '#AD5C3A', '#8E4A30', 0.9, 1.3, 0.08),
    'plaster': ('f', '#E4CEA9'), 'stucco': ('b', '#E4CEA9', '#DCC49D', '#EAD6B5', '#C9AF8A', 2.4, 1.2, 0.05), 'concrete': ('b', '#C9B496', '#BFA988', '#D3C0A3', '#A8916F', 1.4, 0.7, 0.05),
    'roofslab': ('b', '#D9C3A0', '#CFB893', '#E2CEAE', '#B59C77', 3.0, 3.0, 0.05),
    'planks': ('b', '#B58A5C', '#A97E52', '#C09668', '#8A6440', 6.0, 0.9, 0.06),
    'coffer': ('f', '#9C6E50'), 'coffer_rim': ('f', '#C99A74'),
    # L1 깊이색(빛 계산이 아니라 색 지정)
    'deep': ('f', '#5A3F2E'), 'deeper': ('f', '#46301F'), 'shade': ('f', '#93725A'), 'shade_lt': ('f', '#B9987A'),
    'portico_floor': ('f', '#C6AB88'),
    # 바닥(L3)
    'pave': ('b', '#E3D2B3', '#D9C6A4', '#ECDEC4', '#C4AF8C', 3.2, 3.2, 0.035),
    'cobble': ('b', '#C4BAA9', '#AFA595', '#D2C9B9', '#8F8676', 1.7, 1.1, 0.05),
    'soil': ('f', '#B48B64'), 'ground': ('f', '#ECD8AC'),                  # D9: 땅 윗면 (236, 216, 172)
    # L5 하이라이트
    'hi': ('f', '#F8EFDD'), 'hi_brick': ('f', '#DDA07C'), 'hi_lead': ('f', '#E6DCC9'), 'hi_tile': ('f', '#D98B62'),
    # L6 얼룩·식생·생활
    'stain': ('f', '#B49573'), 'mc_joint': ('f', '#C9B48F'), 'mc_lt': ('f', '#ECE0C8'), 'mc_dk': ('f', '#BDA27C'), 'stain_brick': ('f', '#A2603F'), 'stain_lead': ('f', '#ACA08B'),
    'moss': ('f', '#8E9A52'), 'grass1': ('f', '#9BA35C'), 'grass2': ('f', '#7D8B45'), 'grass3': ('f', '#B4B56E'),
    'awning_r': ('f', '#B8402E'), 'awning_w': ('f', '#EFE7D6'), 'wood': ('f', '#A97B4F'), 'terra': ('f', '#B4623E'),
    # 17:48 판테온 고도화(레퍼런스 user_pantheon: 풍화된 황갈색 벽돌 콘크리트 원통 · 회반죽 조각 · 짙은 현관 속)
    'pan_brick': ('b', '#B08562', '#A57A58', '#BA9070', '#8D6A4C', 1.6, 0.8, 0.07), 'pan_brick_hi': ('f', '#CDA886'), 'pan_brick_dk': ('f', '#8C6A50'),
    'max_brick': ('b', '#9E6A4E', '#946247', '#A87557', '#7A4E38', 1.6, 0.8, 0.07), 'max_shade': ('f', '#6E4330'), 'max_shade2': ('f', '#57352A'),     # 17:48 바실리카 풍화 벽돌(레퍼런스 사진)
    'pan_tymp': ('f', '#CFC1A6'), 'pan_lead': ('f', '#BEB8AD'), 'pan_lead_ring': ('f', '#CBC4B6'), 'gran_g2': ('f', '#9E978C'), 'pan_tymp_dk': ('f', '#8F7E66'), 'pan_stucco': ('f', '#D8C7A8'), 'pan_stucco2': ('f', '#C9B391'), 'stain_dk': ('f', '#7E644C'), 'portico_dk': ('f', '#5E4636'),
    'water': ('f', FL.PAL['water']), 'ghost': ('f', '#E9DBC1'),     # b5: 물 한 값(PAL 'water' #92B6D0)
    # 22:05 아크로폴리스(레퍼런스 user_acropolis: 풍화된 펜텔리콘 대리석, 따뜻한 크림·황토 흰색 · 갓 깨진 꿀빛 면 · 회색 때)
    'ac_m': ('b', '#F6F3EC', '#EEEAE1', '#FBF9F4', '#D9D2C3', 1.25, 0.55, 0.05), 'ac_pave': ('b', '#F4F0E8', '#ECE7DD', '#FAF8F3', '#D9D2C3', 2.4, 1.2, 0.04),   # 00:08·00:23 사용자: 아크로폴리스(파르테논)만 흰색, 받침대는 이전 색
    'ac_found': ('b', '#F3EFE7', '#EBE6DC', '#F7F4EE', '#D9D2C3', 1.6, 0.6, 0.07),
    'ac_f1': ('f', '#F6F3EC'), 'ac_f2': ('f', '#E8E3D8'), 'ac_cap': ('f', '#F3EFE7'), 'ac_cap2': ('f', '#E5DFD3'), 'ac_tri': ('f', '#EFEBE2'),
    'ac_lt': ('f', '#FCFBF8'), 'ac_hi2': ('f', '#FFFEFB'), 'ac_break': ('f', '#F4EFE6'), 'ac_joint': ('f', '#D9D2C3'),
    'ac_och': ('f', '#E7DCC4'), 'ac_och2': ('f', '#DDD1B8'), 'ac_grey': ('f', '#D3CEC4'), 'ac_grey2': ('f', '#C2BDB3'),
    'ac_shade': ('f', '#EDE9E0'), 'ac_shade2': ('f', '#D6D0C4'), 'ac_deep': ('f', '#8E877C'),
    'ac_rock3': ('f', '#D4C7AE'), 'ac_rock_dk': ('f', '#C9C0AE'), 'ac_rock_hi': ('f', '#E0D5BF'), 'ac_plateau2': ('f', '#C4B394'),   # 00:23 사용자: 받침대(대지 바위)는 이전 색
}
M = {}


def ink_mat():
    """정보 잉크 평면색(INK_L). 선 그림이라 면 톤(ISO_TONE)을 곱하지 않는 순수 방출색 — 빛 계산 0"""
    name = 'F_city_ink'
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (*FL.srgb(INK_L), 1.0); em.inputs['Strength'].default_value = 1.0
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    m.diffuse_color = (*FL.srgb(INK_L), 1.0)
    return m


def mats():
    for k, d in DEFS.items():
        n = 'F_city_' + k
        if d[0] == 'f':
            M[k] = FL.flat(n, d[1])
        else:
            M[k] = FL.blocks(n, *d[1:])
            c1, c2, c3, jt, bw, rh, jw = d[1:]
            M[k + '@mm'] = FL.blocks(n + '_mm', c1, c2, c3, jt, bw * MMK, rh * MMK, jw * MMK)
    M['ink'] = ink_mat()
    return M


# ───────────────────────── 원형 소품(사람·나무·노점) 크기 ─────────────────────────
_PH = {}


def proto_h(proto):
    """원형 높이(BU). 사람은 키 1.0(D8 정규화, 바구니 등 짐은 키에 넣지 않는다)"""
    if proto.startswith('person'):
        return 1.0
    if proto not in _PH:
        ob = bpy.data.objects['P_' + proto]
        zs = [v.co.z for v in ob.data.vertices]
        _PH[proto] = max(zs) - min(0.0, min(zs))
    return _PH[proto]


def tree_h(proto, k=None):
    """D8 나무 높이(사람 키 비례, 표준 랜드마크 둘레)"""
    if proto.startswith('cypress'):
        return H_PERSON * (k if k else PROP_K['cypress'])
    if proto.startswith('olive'):
        return H_PERSON * PROP_K['olive']
    if proto.startswith('pine'):
        return H_PERSON * PROP_K['pine']
    if proto.startswith('bush'):
        return H_PERSON * (k if k else PROP_K['bush'])
    return H_PERSON


# ───────────────────────── 오브젝트 = 표현 레이어 묶음 ─────────────────────────
USER_REMOVED = {'Acropolis': {'L4_Fragments'}, 'TrajanMarket': {'L4_ForumRuins'}}   # 23:56 사용자: 하이드 처리한 객체 삭제


class Obj:
    """한 오브젝트(루트 Empty) 아래 L0~L6 부분 메시를 모은다. part 하나 = bmesh 하나 + 재질 목록.
    mm=True면 지역 단위가 평면 mm(무늬도 '@mm' 재질)"""
    def __init__(self, name, coll, mm=False, X=0.0, Y=0.0):
        self.name, self.coll, self.mm = name, coll, mm
        self.root = G.new_root('%s_%s_root' % (PK, name), coll, X, Y)
        self.parts = {}
        self.layers = set()
        self.props = []

    def mat(self, k):
        if self.mm and (k + '@mm') in M:
            return M[k + '@mm']
        return M[k]

    def bm(self, layer, part, *mk):
        key = 'L%d_%s' % (layer, part)
        if key not in self.parts:
            self.parts[key] = [bmesh.new(), [self.mat(k) for k in mk]]
        self.layers.add(layer)
        return self.parts[key][0]

    def done(self):
        obs = []
        for key, (bm, ms) in self.parts.items():
            if len(bm.faces) == 0 or key in USER_REMOVED.get(self.name, ()):     # 23:56 사용자가 숨겨 지우라고 한 부분은 짓지 않는다
                bm.free(); continue
            obs.append(G.finish(bm, '%s_%s_%s' % (PK, self.name, key), ms, self.coll, self.root))
        self.parts = {}
        return obs

    def prop(self, proto, x, y, h_mm, rot=0.0, z=0.0, tag=None):
        """원형 링크 복제: 화면 높이 h_mm(사람은 키)로, 루트 지역 좌표 (x, y, z)에. 루트 세로 늘림(kz)은 되돌린다"""
        import roma_props as RP
        nm = '%s_%s_L6_%s' % (PK, self.name, tag or proto)
        ob = RP.place(proto, x, y, z, 1.0, rot, self.coll, name=nm, parent=self.root, local=True)
        ob['h_mm'] = float(h_mm); ob['proto_h'] = float(proto_h(proto))
        self.props.append(ob)
        self.layers.add(6)
        set_prop_scale(ob, self.root)
        return ob

    def refresh_props(self):
        for ob in self.props:
            set_prop_scale(ob, self.root)


def set_prop_scale(ob, root):
    k = ob['h_mm'] / ob['proto_h']
    sx, sz = root.scale.x, root.scale.z
    ob.scale = (k / sx, k / sx, k / sz)


def ensure_protos():
    import roma_props as RP
    if bpy.data.objects.get('P_person0') is None:
        RP.build_protos()


# ───────────────────────── 맞추기: 가로 축척 s + 세로 배율 kz + 평면 이동 ─────────────────────────
def _root_local_pts(root):
    bpy.context.view_layer.update()
    inv = root.matrix_world.inverted()
    out = []
    for o in root.children_recursive:
        if o.type != 'MESH' or o.hide_render or len(o.data.vertices) == 0:
            continue
        n = len(o.data.vertices)
        co = np.empty(n * 3, dtype=np.float64)
        o.data.vertices.foreach_get('co', co)
        co = co.reshape(n, 3)
        Mx = np.array(inv @ o.matrix_world)
        out.append(co @ Mx[:3, :3].T + Mx[:3, 3])
    return np.concatenate(out) if out else np.zeros((0, 3))


AK_DRAW = (1.28, 4.0)    # 00:26 사용자 '아크로폴리스 스케일을 1.3배 정도': 평면 가운데 둘레 배율 · 평면 X 이동(길 RB X 213.5 ~ 길 T1 X 311.5 사이 가운데, 1.3배는 두 길에 닿아 1.28)


MC_DRAW = (1.2, 0.9, -3.0)   # 00:39 사용자 '극장 스케일을 1.2배 정도': 평면 (X 최대, Y 최소) 모서리 둘레 배율 · 평면 이동(길 T1 X 311.5 · 운하 둑 Y 191 쪽으로 붙여 왼쪽 넘침을 줄인다)


def corner_draw(root, k, dX, dY):
    """루트를 메시 평면 외곽의 (X 최대, Y 최소) 모서리(지면) 둘레로 k배 하고 평면 (dX, dY) 옮긴다. 반환: 화면 외곽"""
    xs, ys = [], []
    for o in root.children_recursive:
        if o.type == 'MESH' and not o.hide_render:
            mw = o.matrix_world
            for c in o.bound_box:
                w = mw @ Vector(c); xs.append(w.x); ys.append(w.y)
    pv = Vector((max(xs), max(ys), 0.0))                                      # Blender y 최대 = 평면 Y 최소
    root.scale = tuple(v * k for v in root.scale)
    root.location = pv + (Vector(root.location) - pv) * k + Vector((dX, -dY, 0.0))
    bpy.context.view_layer.update()
    return screen_box(root)


def ak_draw(root, k, dX):
    """루트를 메시 평면 외곽 가운데(지면) 둘레로 k배 하고 평면 X로 dX 옮긴다. 반환: 화면 외곽"""
    xs, ys = [], []
    for o in root.children_recursive:
        if o.type == 'MESH' and not o.hide_render:
            mw = o.matrix_world
            for c in o.bound_box:
                w = mw @ Vector(c); xs.append(w.x); ys.append(w.y)
    pv = Vector((0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys)), 0.0))
    root.scale = tuple(v * k for v in root.scale)
    root.location = pv + (Vector(root.location) - pv) * k + Vector((dX, 0.0, 0.0))
    bpy.context.view_layer.update()
    return screen_box(root)


def fit_skz(root, box, kz_min=0.85, kz_max=2.2):
    """루트 아래 메시의 화면 외곽을 box(화면 mm)에 맞춘다. 화면 x는 높이와 무관하므로 s는 폭으로, kz는 높이로 정한다(이분법).
    루트에 회전이 없다고 본다. 반환: (s, kz, 화면 외곽)"""
    P = _root_local_pts(root)
    k = R.K
    u = (P[:, 0] + P[:, 1]) / math.sqrt(2.0)
    a = -(-P[:, 0] + P[:, 1]) / math.sqrt(6.0)
    c = -(2.0 * P[:, 2]) / math.sqrt(6.0)
    bw, bh = box[2] - box[0], box[3] - box[1]
    s = bw / (k * (u.max() - u.min()))

    def hgt(kz):
        y = a + kz * c
        return k * s * (y.max() - y.min())
    lo, hi = kz_min, kz_max
    if hgt(hi) <= bh:
        kz = hi
    elif hgt(lo) >= bh:
        kz = lo
    else:
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if hgt(mid) < bh:
                lo = mid
            else:
                hi = mid
        kz = 0.5 * (lo + hi)
    root.scale = (s, s, s * kz)
    bpy.context.view_layer.update()
    ox, oy = R.scr(root.matrix_world.translation)
    xs = ox + k * s * u
    ys = oy + k * s * (a + kz * c)
    dx = (box[0] + box[2]) / 2 - (xs.min() + xs.max()) / 2
    dy = (box[1] + box[3]) / 2 - (ys.min() + ys.max()) / 2
    dX, dY = R.to_plan(dx, dy)
    root.location = root.location + Vector((dX, -dY, 0.0))
    bpy.context.view_layer.update()
    return s, kz, screen_box(root)


def screen_box(root):
    P = _root_local_pts(root)
    if len(P) == 0:
        return None
    Mw = np.array(root.matrix_world)
    W = P @ Mw[:3, :3].T + Mw[:3, 3]
    k = R.K
    xs = k * (W[:, 0] + W[:, 1]) / math.sqrt(2.0)
    ys = -k * (-W[:, 0] + W[:, 1] + 2.0 * W[:, 2]) / math.sqrt(6.0)
    return (float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max()))


def place_plan(root, X0, Y0):
    """평면 원본 건물(L7·L9): 축척 1, 지역 원점을 평면 (X0, Y0)에"""
    root.scale = (1.0, 1.0, 1.0)
    root.location = R.P(X0, Y0, 0.0)
    bpy.context.view_layer.update()


# ───────────────────────── 앵커(D11): 보이는 면 위의 3D 점 ─────────────────────────
def _bvh(root, name_ok=None):
    vs, ps, owners = [], [], []
    deps = bpy.context.evaluated_depsgraph_get()
    for o in root.children_recursive:
        if o.type != 'MESH' or o.hide_render:
            continue
        me = o.data
        mw = o.matrix_world
        base = len(vs)
        vs.extend([mw @ v.co for v in me.vertices])
        for p in me.polygons:
            ps.append([base + i for i in p.vertices])
            owners.append(o.name)
    return BVHTree.FromPolygons(vs, ps, all_triangles=False), owners


def _ray(bvh, sx, sy):
    X, Y = R.to_plan(sx, sy)
    org = R.P(X, Y, 0.0) - R.FWD * 400.0
    return bvh.ray_cast(org, R.FWD, 900.0)


def put_anchor(o, role, pt, ok=lambda n: True, search=3.0, bvh=None):
    """ANCHOR_{대상}_{역할}: 화면 잠정 점 pt를 지나는 시선이 이 오브젝트에 처음 닿는 점(맞는 부분 ok). 없으면 search mm 안 가장 가까운 점"""
    if bvh is None:
        bvh = _bvh(o.root)
    tree, owners = bvh
    best = None
    for rr in [0.0] + [0.25 * i for i in range(1, int(search / 0.25) + 1)]:
        nang = 1 if rr == 0 else max(8, int(2 * math.pi * rr / 0.25))
        for j in range(nang):
            t = 2 * math.pi * j / nang
            sx, sy = pt[0] + rr * math.cos(t), pt[1] + rr * math.sin(t)
            loc, nrm, idx, dist = _ray(tree, sx, sy)
            if loc is None:
                continue
            if not ok(owners[idx]):
                continue
            best = (loc, (sx, sy), rr, owners[idx])
            break
        if best:
            break
    nm = 'ANCHOR_%s' % role
    old = bpy.data.objects.get(nm)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    em = bpy.data.objects.new(nm, None)
    o.coll.objects.link(em)
    em.empty_display_size = 1.5
    em.hide_render = True
    em['tentative'] = list(pt)
    if best is None:
        em['found'] = False
        X, Y = R.to_plan(*pt)
        w = R.P(X, Y, 0.0)
    else:
        w = best[0]
        em['found'] = True
        em['offset_mm'] = round(best[2], 3)
        em['surface'] = best[3]
    em.parent = o.root
    em.matrix_parent_inverse.identity()
    em.location = o.root.matrix_world.inverted() @ w
    bpy.context.view_layer.update()
    s = R.scr(em.matrix_world.translation)
    em['screen'] = [round(s[0], 2), round(s[1], 2)]
    return em


# ───────────────────────── 형상 도구 ─────────────────────────
def plane_map(o, eu, ev, en):
    o, eu, ev, en = Vector(o), Vector(eu), Vector(ev), Vector(en)
    return lambda u, v, d: o + eu * u + ev * v + en * d


def map_front(y0):
    """왼면(법선 −y) 평면 y = y0: u = x, v = z, d = −y 쪽으로 내민 거리"""
    return lambda u, v, d: Vector((u, y0 - d, v))


def map_right(x0):
    """오른면(법선 +x) 평면 x = x0: u = y, v = z"""
    return lambda u, v, d: Vector((x0 + d, u, v))


def map_cyl(cx, cy, r, phi0_deg):
    """원통 면: u = 호 길이(phi0에서 반시계), v = z, d = 바깥으로"""
    p0 = math.radians(phi0_deg)
    def f(u, v, d):
        a = p0 + u / r
        return Vector((cx + (r + d) * math.cos(a), cy + (r + d) * math.sin(a), v))
    return f


def uz_prism(bm, loop, fmap, d0, d1, mi=0, uv=False):
    """(u, v) 볼록 다각형을 깊이 d0~d1로 내민 닫힌 입체(문·창·띠·얼룩·글자 등 덧붙임)"""
    F = [bm.verts.new(fmap(u, v, d1)) for u, v in loop]
    B = [bm.verts.new(fmap(u, v, d0)) for u, v in loop]
    fs = [bm.faces.new(F), bm.faces.new(B[::-1])]
    n = len(loop)
    for i in range(n):
        j = (i + 1) % n
        fs.append(bm.faces.new([F[i], B[i], B[j], F[j]]))
    for f in fs:
        f.material_index = mi
    if uv:
        G.uv_box(bm, fs)
    return fs


def rect(u0, u1, v0, v1):
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def arch_loop(u0, u1, v0, vs, n=8):
    """네모 + 반원 아치(볼록)"""
    rr = (u1 - u0) / 2; cu = (u0 + u1) / 2
    return [(u0, v0), (u1, v0)] + [(cu + rr * math.cos(math.pi * j / n), vs + rr * math.sin(math.pi * j / n)) for j in range(n + 1)]


def arch_band(bm, fmap, cu, vs, r_in, r_out, d0, d1, mi, n=8, a0=0.0, a1=180.0):
    """아치 띠(홍예·막힌 아치 윤곽): 조각 n개"""
    for j in range(n):
        t0 = math.radians(a0 + (a1 - a0) * j / n); t1 = math.radians(a0 + (a1 - a0) * (j + 1) / n)
        lp = [(cu + r_in * math.cos(t0), vs + r_in * math.sin(t0)), (cu + r_out * math.cos(t0), vs + r_out * math.sin(t0)),
              (cu + r_out * math.cos(t1), vs + r_out * math.sin(t1)), (cu + r_in * math.cos(t1), vs + r_in * math.sin(t1))]
        uz_prism(bm, lp, fmap, d0, d1, mi)


def wedge_x(bm, x0, x1, y0, y1, z0, z_at_x0, z_at_x1, mi=0):
    """윗면이 x 방향으로 기운 쐐기(외쪽 지붕)"""
    v = [bm.verts.new(c) for c in [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                     (x0, y0, z_at_x0), (x1, y0, z_at_x1), (x1, y1, z_at_x1), (x0, y1, z_at_x0)]]
    fs = [bm.faces.new([v[k] for k in q]) for q in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]]
    for f in fs:
        f.material_index = mi
    G.uv_box(bm, fs)
    return fs


def wedge_y(bm, x0, x1, y0, y1, z0, z_at_y0, z_at_y1, mi=0):
    v = [bm.verts.new(c) for c in [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                     (x0, y0, z_at_y0), (x1, y0, z_at_y0), (x1, y1, z_at_y1), (x0, y1, z_at_y1)]]
    fs = [bm.faces.new([v[k] for k in q]) for q in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]]
    for f in fs:
        f.material_index = mi
    G.uv_box(bm, fs)
    return fs


def column(bs, bc, x, y, z0, h, r, n=12, shaft_mi=0, cap_mi=0, order='C'):
    """기둥: 주춧돌·몸통(bs)·주두(bc). order 'C' 코린트(종 모양 주두) · 'D' 도리아 · 'I' 이오니아"""
    G.box(bc, x - r * 1.32, x + r * 1.32, y - r * 1.32, y + r * 1.32, z0, z0 + r * 0.4, cap_mi)
    G.cyl(bc, x, y, r * 1.22, z0 + r * 0.4, z0 + r * 0.8, n, cap_mi, r_top=r * 1.08, bottom=True)
    zc = z0 + h - (r * 1.9 if order == 'C' else r * 0.9)
    G.cyl(bs, x, y, r, z0 + r * 0.8, zc, n, shaft_mi, r_top=r * 0.87, bottom=True)
    if order == 'C':
        G.cyl(bc, x, y, r * 0.88, zc, z0 + h - r * 0.42, n, cap_mi, r_top=r * 1.32, bottom=True)
    elif order == 'I':
        G.cyl(bc, x, y, r * 0.9, zc, zc + r * 0.35, n, cap_mi, r_top=r * 1.05, bottom=True)
        G.box(bc, x - r * 1.45, x + r * 1.45, y - r * 0.6, y + r * 0.6, zc + r * 0.2, z0 + h - r * 0.42, cap_mi)  # 소용돌이
    else:
        G.cyl(bc, x, y, r * 0.9, zc, zc + r * 0.45, n, cap_mi, r_top=r * 1.18, bottom=True)
    G.box(bc, x - r * 1.4, x + r * 1.4, y - r * 1.4, y + r * 1.4, z0 + h - r * 0.42, z0 + h, cap_mi)


def column_hi(bh, x, y, z0, z1, r, phi=-110.0, w=0.32, mi=0):
    """L5 기둥 밝은 쪽 세로 띠(왼쪽 앞)"""
    a = math.radians(phi)
    nx, ny = math.cos(a), math.sin(a)
    tx, ty = -ny, nx
    o = Vector((x + nx * r * 0.93, y + ny * r * 0.93, z0))
    uz_prism(bh, rect(-w / 2, w / 2, 0.0, z1 - z0), plane_map(o, (tx, ty, 0), (0, 0, 1), (nx, ny, 0)), 0.0, r * 0.12, mi)


def tufts(bm, pts, mi_list, seed=0.0, z=0.0):
    """L6 풀 포기: 낮은 육각 덩이"""
    for k, it in enumerate(pts):
        x, y, s = it[:3]
        zz = it[3] if len(it) > 3 else z
        h = R.hash01(x * 1.7 + seed, y * 2.3, k)
        G.cyl(bm, x, y, s * (0.8 + 0.4 * h), zz, zz + s * (0.55 + 0.5 * h), 6, mi_list[k % len(mi_list)], r_top=s * 0.35, bottom=True)


def shell_of_rev(bm, prof_out, prof_in, n, mi=0, a0=0.0, a1=360.0, cx=0.0, cy=0.0):
    """회전체 껍질(바깥 윤곽 prof_out·안 윤곽 prof_in: [(r, z)] 아래→위). 위·아래 끝은 고리 면으로 닫는다"""
    full = abs(a1 - a0) >= 359.99
    m = n if full else n + 1
    ang = [math.radians(a0 + (a1 - a0) * k / n) for k in range(m)]
    def rows(prof):
        return [[bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), z)) for a in ang] for r, z in prof]
    O, I = rows(prof_out), rows(prof_in)
    fs = []
    def band(A, B, rev=False):
        for k in range(n):
            k2 = (k + 1) % m
            q = [A[k], A[k2], B[k2], B[k]]
            fs.append(bm.faces.new(q[::-1] if rev else q))
    for j in range(len(O) - 1):
        band(O[j], O[j + 1])
    for j in range(len(I) - 1):
        band(I[j], I[j + 1], True)
    band(I[0], O[0])
    band(O[-1], I[-1])
    if not full:
        for k in (0, m - 1):
            for j in range(len(O) - 1):
                try:
                    fs.append(bm.faces.new([O[j][k], O[j + 1][k], I[j + 1][k], I[j][k]]))
                except ValueError:
                    pass
    for f in fs:
        f.material_index = mi
    G.uv_cyl(bm, fs, cx, cy, prof_out[0][0])
    return fs


def _dedup(lp):
    out = []
    for q in lp:
        if not out or abs(out[-1][0] - q[0]) > 1e-6 or abs(out[-1][1] - q[1]) > 1e-6:
            out.append(q)
    if len(out) > 2 and abs(out[0][0] - out[-1][0]) < 1e-6 and abs(out[0][1] - out[-1][1]) < 1e-6:
        out.pop()
    return out


def arc_wall(bm, cx, cy, Rf, Rb, a0, a1, z0, z1, nb, holes=None, mi=0, mj=None, mt=None, ends=True):
    """곡면 벽 nb칸(칸 경계마다 정점 → 긴 현이 생기지 않는다). Rf: 보이는 면 반지름(호 길이 기준), Rb: 뒷면 반지름.
    holes(k, Lb) → [('arch', u0, u1, zb, zs) | ('rect', u0, u1, zb, zt)] (u: 칸 안 호 길이). zb ≤ z0이면 바닥에 닿는 구멍.
    mi: 앞·뒷면, mj: 구멍 속 면(깊이색), mt: 윗면"""
    mj = mi if mj is None else mj
    mt = mi if mt is None else mt
    A0 = math.radians(a0); dA = math.radians(a1 - a0) / nb
    Lb = abs(dA) * Rf
    sg = 1.0 if a1 >= a0 else -1.0
    uvl = bm.loops.layers.uv.verify()
    def P(k, u, z, r):
        a = A0 + k * dA + sg * u / Rf
        return (cx + r * math.cos(a), cy + r * math.sin(a), z)
    for k in range(nb):
        hs = holes(k, Lb) if holes else []
        gr = sorted([h for h in hs if h[3] <= z0 + 1e-6], key=lambda h: h[1])
        inn = [h for h in hs if h[3] > z0 + 1e-6]
        outer = [(0.0, z0)]
        for kind, u0, u1, zb, zs in gr:
            if kind == 'arch':
                rr = (u1 - u0) / 2; cu = (u0 + u1) / 2
                outer += [(u0, z0)] + [(cu - rr * math.cos(math.pi * j / 8), zs + rr * math.sin(math.pi * j / 8)) for j in range(9)] + [(u1, z0)]
            else:
                outer += [(u0, z0), (u0, zs), (u1, zs), (u1, z0)]
        outer += [(Lb, z0), (Lb, z1), (0.0, z1)]
        loops = [_dedup(outer)]
        for kind, u0, u1, zb, zs in inn:
            loops.append(_dedup(arch_loop(u0, u1, zb, zs) if kind == 'arch' else rect(u0, u1, zb, zs)))
        tris = tessellate_polygon([[(q[0], q[1], 0.0) for q in lp] for lp in loops])
        flat = [q for lp in loops for q in lp]
        F = [bm.verts.new(P(k, u, z, Rf)) for u, z in flat]
        B = [bm.verts.new(P(k, u, z, Rb)) for u, z in flat]
        fs = []
        for t in tris:
            for vs_ in ([F[t[0]], F[t[1]], F[t[2]]], [B[t[2]], B[t[1]], B[t[0]]]):
                try:
                    fs.append((bm.faces.new(vs_), mi))
                except ValueError:
                    pass
        off = 0
        for li, lp in enumerate(loops):
            m = len(lp)
            for i in range(m):
                a, b2 = off + i, off + (i + 1) % m
                pa, pb = flat[a], flat[b2]
                if li == 0:
                    if abs(pa[0]) < 1e-6 and abs(pb[0]) < 1e-6 and not (ends and k == 0):
                        continue
                    if abs(pa[0] - Lb) < 1e-6 and abs(pb[0] - Lb) < 1e-6 and not (ends and k == nb - 1):
                        continue
                    if abs(pa[1] - z1) < 1e-6 and abs(pb[1] - z1) < 1e-6:
                        mm = mt
                    elif abs(pa[1] - z0) < 1e-6 and abs(pb[1] - z0) < 1e-6:
                        mm = mi
                    elif (abs(pa[0]) < 1e-6 and abs(pb[0]) < 1e-6) or (abs(pa[0] - Lb) < 1e-6 and abs(pb[0] - Lb) < 1e-6):
                        mm = mi
                    else:
                        mm = mj
                else:
                    mm = mj
                try:
                    fs.append((bm.faces.new([F[a], F[b2], B[b2], B[a]]), mm))
                except ValueError:
                    pass
            off += m
        for f, mm in fs:
            f.material_index = mm
            for lp_ in f.loops:
                c = lp_.vert.co
                ang = math.atan2(c.y - cy, c.x - cx) - A0
                ang = (ang + math.pi) % (2 * math.pi) - math.pi
                lp_[uvl].uv = (sg * ang * Rf, c.z)
    return Lb


def barrel_y(bm, y0, y1, xc, zs, r_in, r_out, n=24, mi=0):
    """축이 y인 원통 볼트(두께 있는 반고리 단면을 y0~y1로 민 입체)"""
    ang = [math.radians(180.0 * k / n) for k in range(n + 1)]
    def ring_at(y):
        return [[bm.verts.new((xc + r * math.cos(a), y, zs + r * math.sin(a))) for a in ang] for r in (r_in, r_out)]
    A, B = ring_at(y0), ring_at(y1)
    fs = []
    for k in range(n):
        fs.append(bm.faces.new([A[0][k], A[0][k + 1], B[0][k + 1], B[0][k]]))
        fs.append(bm.faces.new([A[1][k + 1], A[1][k], B[1][k], B[1][k + 1]]))
        fs.append(bm.faces.new([A[0][k + 1], A[0][k], A[1][k], A[1][k + 1]]))
        fs.append(bm.faces.new([B[0][k], B[0][k + 1], B[1][k + 1], B[1][k]]))
    for S_ in (0, n):
        fs.append(bm.faces.new([A[0][S_], A[1][S_], B[1][S_], B[0][S_]]))
    for f in fs:
        f.material_index = mi
    G.uv_box(bm, fs)
    return fs


def map_barrel_y(xc, zs, r):
    """축이 y인 볼트 안쪽 면: u = y, v = 호 길이(+x 받침에서), d = 축 쪽으로"""
    return lambda u, v, d: Vector((xc + (r - d) * math.cos(v / r), u, zs + (r - d) * math.sin(v / r)))


def octagon(cu, cv, w):
    k = w / 2; c = k * 0.414
    return [(cu - c, cv - k), (cu + c, cv - k), (cu + k, cv - c), (cu + k, cv + c), (cu + c, cv + k), (cu - c, cv + k), (cu - k, cv + c), (cu - k, cv - c)]


def tube_chain(bm, pts, r, n=6, mi=0):
    """점 목록을 잇는 가는 관(점선 한 토막). 끝은 막는다"""
    rings = []
    for i, p in enumerate(pts):
        p = Vector(p)
        if i == 0:
            t = (Vector(pts[1]) - p).normalized()
        elif i == len(pts) - 1:
            t = (p - Vector(pts[i - 1])).normalized()
        else:
            t = (Vector(pts[i + 1]) - Vector(pts[i - 1])).normalized()
        a = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
        e1 = t.cross(a).normalized(); e2 = t.cross(e1).normalized()
        rings.append([bm.verts.new(p + (e1 * math.cos(2 * math.pi * j / n) + e2 * math.sin(2 * math.pi * j / n)) * r) for j in range(n)])
    fs = []
    for i in range(len(rings) - 1):
        A, B = rings[i], rings[i + 1]
        for j in range(n):
            fs.append(bm.faces.new([A[j], A[(j + 1) % n], B[(j + 1) % n], B[j]]))
    fs.append(bm.faces.new(rings[0][::-1])); fs.append(bm.faces.new(rings[-1]))
    for f in fs:
        f.material_index = mi
    return fs


def dashed_curve(bm, pts_world_local, to_screen, r, dash, gap, mi=0, phase=0.0):
    """3D 곡선(지역 좌표 점 목록)을 화면 길이 기준 대시 dash·gap(mm)으로 끊어 가는 관으로 짓는다"""
    S = [to_screen(p) for p in pts_world_local]
    L = [0.0]
    for i in range(1, len(S)):
        L.append(L[-1] + math.hypot(S[i][0] - S[i - 1][0], S[i][1] - S[i - 1][1]))
    tot = L[-1]
    per = dash + gap
    t0 = -phase
    nd = 0
    while t0 < tot:
        a, b = max(0.0, t0), min(tot, t0 + dash)
        if b - a > 0.15:
            seg = []
            def at(t):
                for i in range(1, len(L)):
                    if L[i] >= t:
                        f = (t - L[i - 1]) / max(1e-9, L[i] - L[i - 1])
                        return Vector(pts_world_local[i - 1]).lerp(Vector(pts_world_local[i]), f)
                return Vector(pts_world_local[-1])
            steps = max(2, int((b - a) / 0.3) + 1)
            for j in range(steps + 1):
                seg.append(at(a + (b - a) * j / steps))
            tube_chain(bm, seg, r, 6, mi)
            nd += 1
        t0 += per
    return nd


def bx(b, u0, u1, v0, v1, z0, z1, mi=0):
    """평면 (u, v) 상자 → 지역 Blender 상자(y = −v)"""
    return G.box(b, u0, u1, -v1, -v0, z0, z1, mi)


def _rbox(bm, cu, cv, w, d, z0, z1, ang, mi=0):
    """평면 (u, v) 중심의 돌린 상자(지역 Blender, y = −v): 깨진 판석·대리석 조각"""
    ca, sa = math.cos(ang), math.sin(ang)
    pts = [(cu + x * ca - y * sa, -(cv + x * sa + y * ca)) for x, y in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2))]
    return G.prism(bm, pts[::-1], z0, z1, mi)


def soil_patch(bm, cx, cy, rx, ry, z, n=9, mi=0, seed=0.0):
    """L6 낮은 풀밭·흙 조각(불규칙 다각형 판, 두께 0.06)"""
    pts = []
    for j in range(n):
        a = 2 * math.pi * j / n
        k = 0.75 + 0.45 * R.hash01(seed, j, 3.1)
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    G.prism(bm, pts, z, z + 0.06, mi)


# ═════════════════════════ 판테온(Pantheon) ═════════════════════════
# 실제 비례(m): 원통 바깥 지름 56 · 안 지름 43.3 · 오큘러스 약 8.9 · 현관 폭 33(정면 회색 화강암 8주, 안쪽 분홍 화강암 8주, 전체 16주)
# 현관 앞(−y, 화면 왼쪽 아래)으로 열주 앞마당. 마당 비례는 d4 설계 그림과 같다(원통 반지름 28 m에 마당 ±34.2 · 뒤 34.2 · 앞 69.7).
# 받침 없음: 판석 포장(윗면 +0.2 m)만 땅에 깐다. 높이는 fit_skz가 spec 상자 높이로 정한다(kz).
PAN_RO = 28.0
PAN_HALF, PAN_BACK, PAN_FORE = 31.5, 31.5, 54.0   # 앞마당 반폭·뒤·앞(옛 값 34.2, 34.2, 69.7). 18:06 마당을 줄여 건물을 크게: s 0.737 → 0.855, kz 1.258
PAN_FORE_PORTICO = False # 16:25 레퍼런스: 앞마당 주랑 0
PAN_COL_R = 1.15         # 기둥 반지름(실제 0.76). 18:05 현관을 주인공으로: 1.0 → 1.15
PAN_PORT_Z = 1.2         # 18:05 현관·중간 블록만 세로 1.2배: 박공 꼭대기 24.9 → 29.9(원통 맨 위 코니스 30.6 높이). 폭(원통 지름의 0.6)·깊이(15.4)는 실제 그대로
PAN_PORT_PARTS = ('Block', 'Podium', 'Pediment', 'ColumnsGrey', 'ColumnsInner', 'Capitals', 'Entablature', 'BlockCornice', 'Depth',
                  'PorticoSeams', 'Doors', 'Inscription', 'PedimentWreath', 'PorticoHi', 'Dentils', 'PedimentShade', 'PedimentWeather', 'Acanthus')
PAN_ROT = 90.0           # 18:06 사용자: 현관 정면 바깥 법선 = Blender 월드 +X(격자와 나란히, 원통은 −X 쪽 뒤). 지역 −y 법선을 Z축 반시계 90°
                         # 원통의 보이는 쪽 장식(얼룩·홍예·띠·풀)은 각도에 -PAN_ROT를 더해 지어, 돌린 뒤에도 보이는 쪽에 남는다


def _pan_dome_profile():
    zc, Rs = 13.37, 31.57
    ab, at = math.atan2(36.2 - zc, 21.8), math.atan2(44.6 - zc, 4.6)
    out = [(Rs * math.cos(ab + (at - ab) * j / 10), zc + Rs * math.sin(ab + (at - ab) * j / 10)) for j in range(11)]
    inn = [(max(r - 1.6, 2.6), z - 1.2) for r, z in out]
    return out, inn, (zc, Rs, ab, at)


def build_pantheon(GC, box):
    o = Obj('Pantheon', GC)
    RO = PAN_RO
    VA = -PAN_ROT
    # ── L0 덩어리: 원통 3단·돔 계단 고리 3단·돔 껍질·중간 블록·현관 기단·박공
    b = o.bm(0, 'Drum', 'pan_brick')
    G.cyl(b, 0, 0, RO, 0.0, 12.6, 72, 0, bottom=True)
    G.cyl(b, 0, 0, RO, 13.4, 24.6, 72, 0, bottom=True)
    G.cyl(b, 0, 0, RO - 0.35, 25.4, 30.6, 72, 0, bottom=True)
    b = o.bm(0, 'DomeSteps', 'pan_lead_ring')                            # 18:05 돔 비중 줄이기: 납 색을 차분한 회색으로
    STEPS = [(27.2 - 1.8 * k, 31.3 + 1.633 * k, 31.3 + 1.633 * (k + 1)) for k in range(3)]   # 계단 고리 3단(바깥 반지름, 아래, 위)
    for r1, z0, z1 in STEPS:
        G.ring(b, 0, 0, r1 - 4.0, r1, z0, z1, 72, 0)
    prof_o, prof_i, (zc, Rs, ab, at) = _pan_dome_profile()
    b = o.bm(0, 'DomeShell', 'pan_lead')
    shell_of_rev(b, prof_o, prof_i, 72, 0)
    b = o.bm(0, 'Block', 'pan_brick')
    G.box(b, -17.6, 17.6, -31.6, -21.0, 0.0, 24.6, 0)                      # 중간 블록
    b = o.bm(0, 'Podium', 'marble', 'trav')
    G.box(b, -17.2, 17.2, -47.8, -31.6, 0.0, 1.3, 1)                       # 현관 기단(낮은 계단 기단, 받침 아님)
    for k in range(1, 6):
        G.box(b, -16.0, 16.0, -47.8 - 0.5 * k, -47.8, 0.0, 1.3 - 0.26 * k, 0)   # 앞 계단 5단
    b = o.bm(0, 'Pediment', 'lead', 'pan_tymp')                         # 17:48: 박공면은 풍화된 회갈색(레퍼런스)
    fs = G.gable(b, -16.4, 16.4, -47.0, -31.6, 18.9, 24.9, 'Y', 1, 0.0)
    fs[0].material_index = 0; fs[1].material_index = 0                     # 지붕 비탈(납판)
    fs = G.gable(b, -17.6, 17.6, -31.6, -21.5, 25.4, 30.6, 'Y', 1, 0.0)    # 중간 블록 위 둘째 박공
    fs[0].material_index = 0; fs[1].material_index = 0
    # ── L3 앞마당 포장(판석 무늬) — 얇게 땅에 묻는다(받침 아님)
    b = o.bm(3, 'Paving', 'pave', 'cobble')
    G.box(b, -PAN_HALF, PAN_HALF, -PAN_FORE, PAN_BACK, 0.0, 0.2, 0)
    if PAN_ROT == 0.0:
        G.box(b, -PAN_HALF - 3.6, -PAN_HALF + 4.0, PAN_BACK - 4.0, PAN_BACK + 3.0, 0.0, 0.26, 1)     # 뒤-왼쪽 모서리 → 시내 길 1(R2) 접속 판석(돔 뒤에 숨는다)
    G.ring(b, 0, 0, RO + 0.3, RO + 2.6, 0.2, 0.26, 72, 1)                   # 원통 둘레 회색 판석 띠
    G.box(b, -19.0, 19.0, -PAN_FORE + 0.5, -50.5, 0.2, 0.26, 1)             # 현관 앞 회색 판석 길(가운데)
    # ── L1 깊이색: 현관 안 벽·바닥, 벽감·문틈, 오큘러스 속
    b = o.bm(1, 'Depth', 'portico_dk', 'portico_floor', 'deep')         # 17:48: 현관 속은 짙은 그늘색
    uz_prism(b, rect(-16.2, 16.2, 1.3, 18.05), map_front(-31.6), 0.0, 0.04, 0)
    G.box(b, -16.2, 16.2, -46.0, -31.6, 1.3, 1.34, 1)
    for cx in (-10.6, 10.6):
        uz_prism(b, arch_loop(cx - 2.3, cx + 2.3, 1.9, 9.0), map_front(-31.6), 0.04, 0.1, 2)
    G.cyl(o.bm(1, 'OculusDepth', 'deep'), 0, 0, 4.4, 41.5, 44.45, 36, 0, bottom=True)   # 오큘러스 속(짙은 색)
    # ── L2 부재: 원통 코니스 3단, 현관 기둥 16, 엔타블러처, 박공 처마, 오큘러스 청동 고리, 앞마당 열주
    b = o.bm(2, 'Cornices', 'marble')
    for z0, z1 in ((12.6, 13.4), (24.6, 25.4)):
        G.ring(b, 0, 0, RO - 1.0, RO + 0.5, z0, z1, 72, 0)
    G.ring(b, 0, 0, RO - 1.4, RO + 0.2, 30.6, 31.3, 72, 0)
    G.box(o.bm(2, 'BlockCornice', 'marble'), -18.1, 18.1, -32.1, -21.0, 24.6, 25.4, 0)   # 중간 블록 코니스
    b = o.bm(2, 'OculusRing', 'bronze')
    G.ring(b, 0, 0, 4.3, 5.0, 44.3, 44.95, 48, 0)
    bs = o.bm(2, 'ColumnsGrey', 'gran_g')
    bsr = o.bm(2, 'ColumnsInner', 'gran_g2')                             # 18:05 안쪽 줄도 회색 화강암(레퍼런스, 분홍 빼기)
    bc = o.bm(2, 'Capitals', 'marble')
    xs = [-14.7 + 4.2 * k for k in range(8)]
    for x in xs:
        column(bs, bc, x, -46.2, 1.3, 14.25, PAN_COL_R)
    for y in (-41.8, -37.4):
        for k in (0, 2, 5, 7):
            column(bsr, bc, xs[k], y, 1.3, 14.25, PAN_COL_R)
    b = o.bm(2, 'Entablature', 'marble')
    G.box(b, -16.3, 16.3, -47.0, -31.6, 15.55, 16.85, 0)                   # 아키트레이브
    G.box(b, -16.2, 16.2, -46.9, -31.6, 16.85, 18.05, 0)                   # 프리즈(명문 띠)
    G.box(b, -16.8, 16.8, -47.5, -31.6, 18.05, 18.9, 0)                    # 코니스
    sl = (24.9 - 18.9) / 16.4
    for sx in (-1, 1):                                                       # 경사 처마(현관 박공)
        lp = [(sx * 16.9, 18.9 - 0.5 * sl), (0.0, 24.9), (0.0, 25.7), (sx * 16.9, 18.9 - 0.5 * sl + 0.8)]
        uz_prism(b, lp if sx < 0 else lp[::-1], map_front(-47.0), -0.3, 0.55, 0)
    sl2 = (30.6 - 25.4) / 17.6
    for sx in (-1, 1):                                                       # 둘째 박공 처마
        lp = [(sx * 18.1, 25.4 - 0.5 * sl2), (0.0, 30.6), (0.0, 31.3), (sx * 18.1, 25.4 - 0.5 * sl2 + 0.7)]
        uz_prism(b, lp if sx < 0 else lp[::-1], map_front(-31.6), -0.3, 0.45, 0)
    if PAN_FORE_PORTICO:              # 16:25 레퍼런스(user_pantheon)에 없는 앞마당 양옆 작은 주랑은 짓지 않는다(코드 보관)
        # 앞마당 열주(포르티쿠스): 왼쪽은 기둥이 마당을 보고, 오른쪽은 뒷벽 바깥이 보인다
        bw = o.bm(2, 'ForeWalls', 'stucco')
        bfc = o.bm(2, 'ForeColumns', 'marble')
        bft = o.bm(3, 'ForeRoofTiles', 'tile')
        XW = PAN_HALF - 1.6
        for sx in (-1, 1):
            xw0, xw1 = (-XW - 0.8, -XW) if sx < 0 else (XW, XW + 0.8)
            G.box(bw, xw0, xw1, -PAN_FORE + 1.2, -51.0, 0.0, 7.6, 0)
            xc = -(XW - 4.4) if sx < 0 else (XW - 4.4)
            for k in range(6):
                y = -53.0 - 2.9 * k
                column(bfc, bfc, xc, y, 0.0, 6.6, 0.5, 10)
            G.box(bfc, min(xw0, xc - 0.6 * sx), max(xw1, xc - 0.6 * sx), -PAN_FORE + 1.2, -51.0, 6.6, 7.3, 0)
            x_in, x_out = (xc + 0.8, xw0 - 0.5) if sx < 0 else (xc - 0.8, xw1 + 0.5)
            lo, hi = 7.3, 9.0
            if sx < 0:
                wedge_x(bft, x_out, x_in, -PAN_FORE + 0.8, -50.6, 7.3, hi, lo, 0)
            else:
                wedge_x(bft, x_in, x_out, -PAN_FORE + 0.8, -50.6, 7.3, lo, hi, 0)
        bwd = o.bm(4, 'ForeWallDetail', 'deep', 'stain')
        for yy in (-54.0, -58.5, -63.0, -67.0):                                  # 오른쪽 열주 뒷벽 바깥(보이는 면): 작은 창 · 빗물 자국
            uz_prism(bwd, rect(yy - 0.7, yy + 0.7, 3.6, 5.6), map_right(XW + 0.8), 0.0, 0.05, 0)
            uz_prism(bwd, [(yy + 1.2, 7.6 - 3.2), (yy + 1.8, 7.6 - 2.4), (yy + 1.8, 7.55), (yy + 1.2, 7.55)], map_right(XW + 0.8), 0.0, 0.04, 1)
    # ── L3 표면 무늬: 원통 벽돌(재질), 돔 납판 줄, 현관 지붕 이음 줄
    b = o.bm(3, 'LeadSeams', 'lead_dk')
    for k in range(36):
        phi = 360.0 * k / 36
        a = math.radians(phi)
        for j in range(8):
            t0, t1 = ab + (at - ab) * j / 8, ab + (at - ab) * (j + 1) / 8
            def fm(u, v, d, a=a):
                r = Rs * math.cos(v) + d * math.cos(v); z = zc + Rs * math.sin(v) + d * math.sin(v)
                aa = a + u / max(r, 1.0)
                return Vector((r * math.cos(aa), r * math.sin(aa), z))
            uz_prism(b, [(-0.2, t0), (0.2, t0), (0.2, t1), (-0.2, t1)], fm, 0.0, 0.1, 0)
    b = o.bm(3, 'PorticoSeams', 'lead_dk')
    for sx in (-1, 1):                                                       # 현관 지붕 이음(비탈마다)
        nrm = Vector((sx * 6.0, 0.0, 16.4)).normalized()
        o0 = Vector((sx * 16.4, 0.0, 18.9)); ev = (Vector((0.0, 0.0, 24.9)) - o0)
        L = ev.length; ev = ev.normalized()
        fm = plane_map(o0, (0, 1, 0), ev, nrm)
        for k in range(6):
            yk = -45.2 + 2.4 * k
            uz_prism(b, rect(yk - 0.14, yk + 0.14, 0.0, L), fm, 0.0, 0.09, 0)
    # ── L4 형태 디테일: 청동 문, 문틀, 명문 글자, 박공 화환 자리, 원통 막힌 아치(벽돌 홍예)
    b = o.bm(4, 'Doors', 'marble', 'bronze', 'bronze_hi', 'deep')
    fm = map_front(-31.6)
    uz_prism(b, rect(-4.4, 4.4, 1.3, 13.6), fm, 0.04, 0.26, 0)
    uz_prism(b, rect(-3.6, 3.6, 1.3, 11.6), fm, 0.26, 0.33, 1)
    uz_prism(b, rect(-3.6, 3.6, 11.85, 13.15), fm, 0.26, 0.31, 3)
    uz_prism(b, rect(-0.09, 0.09, 1.3, 11.6), fm, 0.33, 0.37, 3)
    for zz in (4.6, 8.1):
        uz_prism(b, rect(-3.6, 3.6, zz - 0.12, zz + 0.12), fm, 0.33, 0.37, 2)
    for cx in (-1.8, 1.8):
        for z0_, z1_ in ((1.9, 4.2), (5.0, 7.7), (8.5, 11.1)):
            uz_prism(b, rect(cx - 1.25, cx + 1.25, z0_, z1_), fm, 0.33, 0.35, 2)
    b = o.bm(4, 'Inscription', 'bronze_dk')
    txt = 'M.AGRIPPA.L.F.COS.TERTIVM.FECIT'
    adv = [0.36 if c == '.' else 0.62 for c in txt]
    x = -sum(adv) / 2
    for c, a_ in zip(txt, adv):
        if c == '.':
            uz_prism(b, rect(x + 0.1, x + 0.26, 17.35, 17.52), map_front(-46.9), 0.0, 0.06, 0)
        else:
            uz_prism(b, rect(x + 0.08, x + 0.52, 17.05, 17.85), map_front(-46.9), 0.0, 0.06, 0)
        x += a_
    b = o.bm(4, 'PedimentWreath', 'bronze', 'deep')
    arch_band(b, map_front(-47.0), 0.0, 21.2, 1.0, 1.45, 0.0, 0.16, 0, 12, 0.0, 360.0)
    for k in range(14):                                                      # 청동 독수리 장식이 박혔던 구멍 자리(부조 자리)
        a_ = math.radians(180.0 * k / 13)
        cx, cz = 8.5 * math.cos(a_) * 0.95, 19.6 + 2.0 * math.sin(a_) * 0.6
        uz_prism(b, rect(cx - 0.13, cx + 0.13, cz - 0.13, cz + 0.13), map_front(-47.0), 0.0, 0.05, 1)
    b = o.bm(4, 'ReliefArches', 'pan_brick_dk')
    for k in range(9):                                                       # 원통 바깥 막힌 아치(홍예) — 보이는 쪽
        phi = -150.0 + 24.0 * k + VA
        fm = map_cyl(0, 0, RO, phi)
        arch_band(b, fm, 0.0, 17.5, 3.2, 4.0, 0.0, 0.12, 0, 9)
        arch_band(b, fm, 0.0, 6.0, 2.0, 2.7, 0.0, 0.12, 0, 7)
    b = o.bm(3, 'BrickBands', 'pan_brick_hi')
    for zb in (4.2, 8.4, 16.6, 20.8, 27.4):                                  # 원통 벽돌 띠(큰 벽돌 줄, 1층·2층·3층)
        G.ring(b, 0, 0, RO - 0.05, RO + 0.06, zb, zb + 0.32, 72, 0, -170.0 + VA, 80.0 + VA)
    # ── L5 하이라이트: 코니스 윗선, 계단 고리 윗선, 기둥 밝은 띠, 박공 윗선
    b = o.bm(5, 'Highlights', 'hi', 'hi_lead')
    for zt, rr in ((13.4, RO + 0.5), (25.4, RO + 0.5), (31.3, RO + 0.2)):
        G.ring(b, 0, 0, rr - 0.08, rr + 0.06, zt - 0.24, zt + 0.05, 72, 0)
    for r1, z0, z1 in STEPS:
        G.ring(b, 0, 0, r1 - 0.06, r1 + 0.06, z1 - 0.2, z1 + 0.05, 72, 1)
    G.ring(b, 0, 0, 4.95, 5.08, 44.75, 45.0, 48, 0)
    b = o.bm(5, 'PorticoHi', 'hi', 'hi_lead')
    for x in xs:
        column_hi(b, x, -46.2, 2.6, 13.3, PAN_COL_R)
    G.box(b, -16.85, 16.85, -47.56, -47.44, 18.62, 18.92, 0)
    for sx in (-1, 1):
        lp = [(sx * 16.9, 18.9 - 0.5 * sl + 0.62), (0.0, 25.52), (0.0, 25.72), (sx * 16.9, 18.9 - 0.5 * sl + 0.82)]
        uz_prism(b, lp if sx < 0 else lp[::-1], map_front(-47.0), 0.5, 0.58, 0)
    # ── L6 얼룩·식생·생활: 빗물 자국, 계단 고리 이끼, 밑동 풀
    # 17:48 L3 회반죽이 남은 조각(원통 보이는 쪽) · L4 박공 이빨장식·주두 아칸서스
    bst = o.bm(3, 'StuccoPatches', 'pan_stucco', 'pan_stucco2')
    for k in range(22):
        phi = -150.0 + 220.0 * R.hash01(k, 31) + VA
        zc = 1.2 + 28.0 * R.hash01(k, 32)
        if any(abs(zc - zb) < 1.2 for zb in (12.6, 13.4, 24.6, 25.4)):
            continue
        w = 1.4 + 2.6 * R.hash01(k, 33); h = 0.9 + 2.0 * R.hash01(k, 34)
        pts = [(-w / 2, zc - h / 2), (w * 0.3, zc - h / 2 - 0.3), (w / 2, zc - h * 0.1), (w * 0.35, zc + h / 2), (-w * 0.4, zc + h / 2 + 0.2), (-w / 2 - 0.2, zc)]
        uz_prism(bst, pts, map_cyl(0, 0, RO, phi), 0.0, 0.07, k % 2)
    bde = o.bm(4, 'Dentils', 'marble', 'deep')
    u = -16.5
    while u < 16.5:                                                          # 가로 처마 밑 이빨장식
        uz_prism(bde, rect(u, u + 0.32, 17.72, 18.05), map_front(-47.5), 0.0, 0.14, 0)
        u += 0.6
    for sx in (-1, 1):                                                       # 경사 처마 밑 이빨장식
        for k in range(26):
            t = (k + 0.5) / 26.0
            x = sx * 16.4 * (1.0 - t); z = 18.9 + (24.9 - 18.9) * t - 0.35
            uz_prism(bde, [(x - 0.15, z - 0.3), (x + 0.15, z - 0.3), (x + 0.15, z), (x - 0.15, z)], map_front(-47.0), 0.0, 0.14, 0)
    bsh = o.bm(1, 'PedimentShade', 'pan_tymp_dk', 'portico_dk')           # 경사 처마 밑 그늘 띠 · 가로 처마 밑 그늘(박공면 앞 0.03)
    for sx in (-1, 1):
        lp = [(sx * 16.2, 18.9 + 0.05), (0.0, 24.9 - 0.75), (0.0, 24.9 - 0.25), (sx * 16.2, 18.9 + 0.55)]
        uz_prism(bsh, lp if sx < 0 else lp[::-1], map_front(-47.0), 0.0, 0.03, 0)
    uz_prism(bsh, rect(-16.2, 16.2, 15.25, 15.55), map_front(-47.0), 0.0, 0.03, 1)
    btw = o.bm(6, 'PedimentWeather', 'stain_dk', 'pan_stucco')              # 박공면 풍화 얼룩(세로 줄·밝은 반점)
    for k in range(11):
        cx = -12.0 + 24.0 * R.hash01(k, 51); top = 18.9 + (24.9 - 18.9) * (1.0 - abs(cx) / 16.4) - 0.9
        L = 1.2 + 2.2 * R.hash01(k, 52); w = 0.25 + 0.3 * R.hash01(k, 53)
        if top - L < 19.1:
            L = top - 19.1
        if L > 0.3:
            uz_prism(btw, [(cx - w / 2, top - L), (cx + w / 2, top - L * 0.85), (cx + w / 2, top), (cx - w / 2, top)], map_front(-47.0), 0.0, 0.035, k % 2)
    bac = o.bm(4, 'Acanthus', 'marble', 'stain')
    zc_ = 1.3 + 14.25 - PAN_COL_R * 1.9
    for x in xs:                                                             # 앞줄 코린트 주두 아칸서스 잎(2단)
        for j in range(10):
            a_ = 2 * math.pi * (j + 0.5 * (j % 2)) / 10
            for (zz, hh, rr) in ((zc_, 0.7, 0.92), (zc_ + 0.55, 0.75, 1.08)):
                G.cyl(bac, x + PAN_COL_R * rr * math.cos(a_), -46.2 + PAN_COL_R * rr * math.sin(a_), 0.2, zz, zz + hh, 5, 0, r_top=0.03, bottom=True)
    b = o.bm(6, 'Stains', 'stain_brick', 'stain_lead', 'moss', 'stain_dk', 'pan_stucco')
    for k in range(36):                                                      # 17:48: 14 → 36(짙은 풍화 줄 · 밝은 얼룩)
        phi = -140.0 + 13.5 * k + 4.0 * R.hash01(k, 1)
        w = 0.7 + 0.7 * R.hash01(k, 2); L = 2.5 + 4.0 * R.hash01(k, 3)
        ztop = (12.5, 24.5, 30.4)[k % 3]
        phi = -150.0 + 220.0 * R.hash01(k, 41) + VA
        uz_prism(b, [(-w / 2, ztop - L), (w / 2, ztop - L * 0.8), (w / 2, ztop), (-w / 2, ztop)], map_cyl(0, 0, RO, phi), 0.0, 0.09, 3 if k % 3 else 0)
    for k in range(10):
        a0 = -150.0 + 30.0 * k + 9.0 * R.hash01(k, 5) + VA; kk = k % 3
        r1, z0, z1 = STEPS[kk]
        G.ring(b, 0, 0, r1 - 1.2, r1 - 0.05, z1, z1 + 0.07, 4, 2, a0, a0 + 6.0 + 6.0 * R.hash01(k, 6))
    for k in range(8):                                                       # 돔 비탈 빗물 얼룩
        phi = -150.0 + 22.0 * k + VA
        a = math.radians(phi)
        def fm(u, v, d, a=a):
            r = (Rs + d) * math.cos(v); z = zc + (Rs + d) * math.sin(v)
            aa = a + u / max(r, 1.0)
            return Vector((r * math.cos(aa), r * math.sin(aa), z))
        t0 = ab + 0.05; t1 = ab + (at - ab) * (0.35 + 0.25 * R.hash01(k, 8))
        uz_prism(b, [(-0.6, t0), (0.6, t0), (0.35, t1), (-0.35, t1)], fm, 0.0, 0.06, 1)
    b = o.bm(6, 'Grass', 'grass1', 'grass2', 'grass3')
    pts = []
    for k in range(26):
        phi = math.radians(-160.0 + 210.0 * k / 25 + VA)
        if -3.5 < math.degrees(phi) + 90 < 3.5:
            continue
        rr = RO + 2.8 + 0.8 * R.hash01(k, 9)
        x, y = rr * math.cos(phi), rr * math.sin(phi)
        if -21.0 < x < 21.0 and y < -20.0:
            continue
        if abs(x) > PAN_HALF - 1.0 or y > PAN_BACK - 1.0:
            continue
        pts.append((x, y, 0.6 + 0.5 * R.hash01(k, 10), 0.2))
    XW = PAN_HALF - 1.6                                                       # 앞마당 가장자리(주랑을 짓지 않아도 풀 자리는 같다)
    for x, y in ((-XW + 0.6, -52.5), (-XW + 0.6, -62.0), (XW - 0.6, -56.0), (XW - 0.6, -66.0), (-12.0, -68.6), (14.0, -68.8),
                 (-24.0, 32.5), (25.0, 32.6), (-32.6, 10.0), (32.6, -12.0)):
        if y > -PAN_FORE + 0.8:                                               # 앞마당을 줄이면 바깥 풀은 뺀다
            pts.append((x, y, 0.7, 0.2))
    tufts(b, pts, [0, 1, 2], 3.0)
    if PAN_PORT_Z != 1.0:                                                    # 현관·중간 블록 세로 늘림(원통·돔은 그대로)
        for key, (bm_, _ms) in o.parts.items():
            if key.split('_', 1)[1] in PAN_PORT_PARTS:
                for v in bm_.verts:
                    v.co.z *= PAN_PORT_Z
    if PAN_ROT:                                                              # 17:58 현관을 카메라 쪽으로: 모든 부분을 원통 중심 둘레로 돌린다(루트는 돌리지 않아 fit_skz 그대로)
        Mr = Matrix.Rotation(math.radians(PAN_ROT), 4, 'Z')
        for bm_, _ms in o.parts.values():
            bmesh.ops.rotate(bm_, verts=bm_.verts, cent=(0.0, 0.0, 0.0), matrix=Mr)
    o.done()
    return o


def pantheon_life(o):
    """L6 생활(맞춘 뒤 화면 크기로): 앞마당 사람·노점·암포라, 마당 가장자리 나무·덤불(D8 크기). 라벨 비움 구역(상자 왼쪽 위)은 비운다"""
    ensure_protos()
    ppl = [(-8.0, -56.0), (-6.2, -57.5), (-7.0, -59.0), (6.0, -62.0), (7.8, -60.6), (-17.0, -66.0), (-18.6, -64.6),
           (13.0, -67.0), (14.6, -66.0), (0.5, -51.0), (2.2, -52.4), (-22.0, -55.0), (20.0, -57.0), (-3.0, -66.8),
           (30.5, -20.0), (31.6, -22.4), (-24.0, -18.0)]
    for k, (x, y) in enumerate(ppl):
        o.prop('person%d' % (k % 3), x, y, H_PERSON, 360.0 * R.hash01(k, 11), z=0.2, tag='person%02d' % k)
    st_h = H_PERSON * PROP_K['stall']
    o.prop('stall', -23.0, -59.5, st_h, 90.0, z=0.2, tag='stall0')
    o.prop('stall', -23.0, -66.0, st_h, 90.0, z=0.2, tag='stall1')
    for k, (x, y) in enumerate(((-21.2, -57.6), (-21.0, -56.9), (-21.2, -68.6), (22.5, -62.0))):
        o.prop('amphora', x, y, H_PERSON * PROP_K['amphora'], 0.0, z=0.2, tag='amphora%d' % k)
    trees = [('pine0', 29.0, 26.5), ('pine2', 30.5, 12.0), ('cypress1', -31.5, -44.0), ('cypress2', -31.4, -47.5),
             ('cypress0', 31.4, -45.0), ('cypress3', 31.6, -48.5), ('olive1', -30.0, -6.0), ('olive2', 30.8, -30.0)]
    for k, (pr, x, y) in enumerate(trees):
        o.prop(pr, x, y, tree_h(pr), 37.0 * k, z=0.2, tag='tree%d' % k)
    for k, (pr, x, y) in enumerate((('cypress2', 4.0, 37.6), ('cypress0', 7.4, 38.6), ('cypress1', -6.0, 56.0), ('cypress3', -3.0, 58.5))):
        o.prop(pr, x, y, tree_h(pr), 29.0 * k, z=0.0, tag='treeB%d' % k)
    for k, (pr, x, y) in enumerate((('bush2', 11.0, 36.6), ('bush1', 0.6, 36.4))):
        o.prop(pr, x, y, tree_h(pr), 19.0 * k, z=0.0, tag='greenB%d' % k)
    for k, (pr, x, y) in enumerate((('bush0', -31.8, 18.0), ('bush1', -31.5, 24.5), ('bush2', 31.8, -2.0), ('bush3', 32.0, -22.0),
                                    ('bush1', -32.0, -30.0), ('bush0', -32.2, -38.0), ('bush2', 32.0, -38.5), ('bush3', -9.0, 32.6),
                                    ('bush0', 10.0, 32.8), ('bush1', 20.0, 32.5))):
        o.prop(pr, x, y, tree_h(pr), 47.0 * k, z=0.2, tag='green%02d' % k)


def pantheon_anchors(o, A):
    bvh = _bvh(o.root)
    dome = lambda n: ('Dome' in n) or ('Lead' in n) or ('Oculus' in n) or ('Highlights' in n) or ('Stains' in n)
    out = {}
    for role in ('L1_label', 'L1_c1', 'L1_m4'):
        if role in A:
            out[role] = put_anchor(o, role, A[role], dome, bvh=bvh)
    return out


# ═════════════════════════ 아테네 아크로폴리스(22:05 사용자: core의 판테온 → 아크로폴리스) ═════════════════════════
# 레퍼런스 user_acropolis.jpg(북서 모서리에서 본 파르테논 유적): 도리스 홈 기둥, 트리글리프만 남은 톱니 윗변, 지붕 0, 3단 기단, 앞에 흩어진 대리석 덩이.
# 지역 단위 = 실제 m, Blender (x, y) = 평면 (u, −v). 장축 = 평면 X.
# 서쪽 정면 8주(박공 흔적)가 +x(화면 오른쪽 아래 면), 북쪽 측면 17주가 −y(화면 왼쪽 아래 면).
# 받침 = 높은 디오라마 블록(22:22 사용자, 레퍼런스 user_acropolis_hill): 옆면은 수직 마름돌 성벽(roma_diorama.side_ashlar),
# 윗 가장자리에 석회암 노두·대리석 덩이(top_ashlar), 평평한 윗면에 파르테논. 평면 윤곽은 축 정렬(직각 꺾임), 정면 쪽(+u, +v)만 넓혀 흩어진 덩이 자리.
# HT는 fit_skz의 kz가 1 가까이 되게 정했다(L1 상자 121 × 117 mm).
PANTHEON = False         # 22:05 사용자: 판테온 모형은 보관(True = 옛 판테온)
AK = dict(LX=69.5, LY=30.9, CI=1.6, R0=0.95, R1=0.74, CH=10.43, EU=0.35, ST=0.55, TR=0.7, AH=1.35, FH=1.35, GH=0.6, PH=3.6,
          HT=22.0, U=1.1, OUT=0.88, INN=0.92)
AK_BLOCK = [(-41.0, -21.0), (41.0, -21.0), (41.0, -10.0), (52.0, -10.0), (52.0, 30.0), (-12.0, 30.0), (-12.0, 21.5), (-41.0, 21.5)]   # 평면 (u, v)


def _ak_inside(P, x, y):
    c = False
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        if (a[1] > y) != (b[1] > y) and x < a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]):
            c = not c
    return c


def _ak_cylpatch(bm, x, y, rz, phi, loop, mi, dd=0.035):
    """원통 겉에 붙인 납작한 덧칠 한 장: loop = [(접선 거리 t, z)] 반시계, rz(z) = 그 높이 반지름, 방위 phi°"""
    a = math.radians(phi)
    nx, ny = math.cos(a), math.sin(a)
    tx, ty = -ny, nx
    F = [bm.verts.new((x + nx * (rz(z) + dd) + tx * t, y + ny * (rz(z) + dd) + ty * t, z)) for t, z in loop]
    B = [bm.verts.new((x + nx * (rz(z) + dd - 0.012) + tx * t, y + ny * (rz(z) + dd - 0.012) + ty * t, z)) for t, z in loop]
    fs = [bm.faces.new(F), bm.faces.new(B[::-1])]
    for i in range(len(loop)):
        j = (i + 1) % len(loop)
        fs.append(bm.faces.new([F[i], B[i], B[j], F[j]]))
    for f in fs:
        f.material_index = mi
    return fs[0]


def _ak_drum(bm, x, y, z, r, L, ang, n=16, mi=0, mi_end=None):
    """눕힌 기둥 북: 축이 수평(Blender 각 ang), 바닥 z에 놓인다. 옆면은 두 색 번갈아(홈)"""
    ax, ay = math.cos(ang), math.sin(ang)
    ex, ey = -ay, ax
    rings = []
    for s in (-0.5, 0.5):
        cx, cy = x + ax * L * s, y + ay * L * s
        rings.append([bm.verts.new((cx + ex * r * math.cos(t), cy + ey * r * math.cos(t), z + r + r * math.sin(t)))
                      for t in [2.0 * math.pi * k / n for k in range(n)]])
    fs = [bm.faces.new([rings[0][k], rings[0][(k + 1) % n], rings[1][(k + 1) % n], rings[1][k]]) for k in range(n)]
    for k, f in enumerate(fs):
        f.material_index = mi + k % 2
    for rg in (rings[0][::-1], rings[1]):
        f = bm.faces.new(rg); f.material_index = mi if mi_end is None else mi_end; fs.append(f)
    bmesh.ops.recalc_face_normals(bm, faces=fs)
    return fs


def build_acropolis(GC):
    o = Obj('Acropolis', GC)
    hs_ = R.hash01
    HT = AK['HT']
    HX, HY = AK['LX'] / 2.0, AK['LY'] / 2.0
    ST, TR, EU = AK['ST'], AK['TR'], AK['EU']
    e0 = 3 * TR + 0.4
    # ── 받침 블록: L0 덩어리(짙은 줄눈 바탕) · 옆면 마름돌 성벽 L1~L6 · 윗 가장자리 노두·덩이
    import roma_diorama as DI, roma_pkg_ground as GR
    DM = DI.mats()
    U = AK['U']
    POLYB = [(u, -v) for u, v in AK_BLOCK]
    A7 = [GR.Acc() for _ in range(7)]
    A7[0].prism(AK_BLOCK, 0.0, HT, DM['ak_top'], DM['ash_joint'])
    for e, (a, t, n, L) in enumerate(DI.vis_edges(AK_BLOCK)):
        DI.side_ashlar(A7, DM, a, t, n, L, 0.0, HT, 11.0 * e + 3.0, U)
    DI.top_ashlar(A7, DM, AK_BLOCK, HT, 5.0, U, keep_out=lambda X, Y: abs(X) < HX + e0 + 0.6 and abs(Y) < HY + e0 + 0.6)
    for k, (ac, nm) in enumerate(zip(A7, ('Wall', 'WallSeams', 'Ashlar', 'WallChips', 'Outcrops', 'WallLip', 'WallStains'))):
        ac.obj('%s_Acropolis_L%d_%s' % (PK, k, nm), GC, o.root)

    def inside(x, y, m):
        return all(_ak_inside(POLYB, x + dx, y + dy) for dx, dy in ((m, 0.0), (-m, 0.0), (0.0, m), (0.0, -m), (0.0, 0.0)))

    def off_temple(x, y, m):
        return not (-HX - e0 - m < x < HX + e0 + m and -HY - e0 - m < y < HY + e0 + m)

    bdep = o.bm(1, 'Depth', 'ac_deep', 'ac_rock_dk', 'ac_shade', 'ac_shade2')
    bst = o.bm(3, 'Plateau', 'ac_plateau2', 'ac_rock3', 'grass3', 'ac_rock_hi')
    b5 = o.bm(5, 'Highlights', 'ac_lt', 'ac_rock_hi', 'ac_hi2')
    k = 0; n_ = 0
    while n_ < 45 and k < 800:                                                          # L3 윗면 맨바위·흙 조각
        x = -42.0 + 96.0 * hs_(k, 461); y = -31.0 + 53.0 * hs_(k, 462); k += 1
        if not inside(x, y, 2.0) or not off_temple(x, y, 0.3):
            continue
        soil_patch(bst, x, y, 0.8 + 2.2 * hs_(k, 463), 0.6 + 1.4 * hs_(k, 464), HT, 8, (0, 1, 0, 2, 1, 3)[n_ % 6], seed=k * 1.3)
        n_ += 1

    # ═══ 파르테논 ═══
    ZE = HT + EU; ZS = ZE + 3 * ST
    CH, R0, R1 = AK['CH'], AK['R0'], AK['R1']
    UC, VC = HX - AK['CI'], HY - AK['CI']
    OUT, INN, FH = AK['OUT'], AK['INN'], AK['FH']
    ZA0 = ZS + CH; ZA1 = ZA0 + AK['AH']; ZF1 = ZA1 + FH; ZG1 = ZF1 + AK['GH']
    ZI = ZS + 0.7
    xs = [-UC + 2.0 * UC * j / 16.0 for j in range(17)]
    ys = [-VC + 2.0 * VC * i / 7.0 for i in range(8)]
    # ── L0 기단: 거친 기초 + 3단 + 안쪽 2단(내실 바닥)
    bc = o.bm(0, 'Crepis', 'ac_m', 'ac_found', 'ac_pave')
    G.box(bc, -HX - e0, HX + e0, -HY - e0, HY + e0, HT - 0.5, ZE, 1)
    for s_ in range(3):
        e = (2 - s_) * TR
        G.box(bc, -HX - e, HX + e, -HY - e, HY + e, ZE + s_ * ST, ZE + (s_ + 1) * ST, 2 if s_ == 2 else 0)
    G.box(bc, -30.6, 30.6, -11.6, 11.6, ZS, ZS + 0.35, 2)
    G.box(bc, -30.0, 30.0, -11.0, 11.0, ZS + 0.35, ZI, 2)
    bj3 = o.bm(3, 'Joints', 'ac_joint', 'ac_f2', 'ac_cap')
    b4 = o.bm(4, 'Breaks', 'ac_break', 'ac_cap2', 'ac_m')
    b6 = o.bm(6, 'Weather', 'ac_och', 'ac_och2', 'ac_grey', 'ac_grey2', 'moss', 'grass1', 'grass2')
    for s_ in range(3):
        e = (2 - s_) * TR; z0, z1 = ZE + s_ * ST, ZE + (s_ + 1) * ST
        x = -HX - e + 0.6; k = 0
        while x < HX + e - 0.3:                                                          # 북쪽 면(−y) 돌 이음매
            G.box(bj3, x - 0.03, x + 0.03, -HY - e - 0.02, -HY - e + 0.01, z0 + 0.03, z1 - 0.03, 0)
            x += 1.05 + 0.5 * hs_(s_, k, 471); k += 1
        y = -HY - e + 0.6
        while y < HY + e - 0.3:                                                          # 서쪽 면(+x)
            G.box(bj3, HX + e - 0.01, HX + e + 0.02, y - 0.03, y + 0.03, z0 + 0.03, z1 - 0.03, 0)
            y += 1.05 + 0.5 * hs_(s_, k, 472); k += 1
        G.box(b5, -HX - e, HX + e, -HY - e - 0.025, -HY - e + 0.08, z1 - 0.07, z1 + 0.004, 0)
        G.box(b5, HX + e - 0.08, HX + e + 0.025, -HY - e, HY + e, z1 - 0.07, z1 + 0.004, 0)
        for j in range(10):                                                              # 떨어져 나간 모서리(갓 깨진 돌빛)
            x = -HX - e + (2 * HX + 2 * e) * hs_(s_, j, 473); w_ = 0.3 + 0.7 * hs_(s_, j, 474)
            G.box(b4, x - w_, x + w_, -HY - e - 0.03, -HY - e + 0.25 + 0.3 * hs_(s_, j, 475), z1 - 0.12 - 0.25 * hs_(s_, j, 476), z1 + 0.005, 0)
        for j in range(6):
            y = -HY - e + (2 * HY + 2 * e) * hs_(s_, j, 477); w_ = 0.3 + 0.6 * hs_(s_, j, 478)
            G.box(b4, HX + e - 0.25 - 0.3 * hs_(s_, j, 479), HX + e + 0.03, y - w_, y + w_, z1 - 0.12 - 0.25 * hs_(s_, j, 480), z1 + 0.005, 0)
        fmN, fmW = map_front(-HY - e), map_right(HX + e)
        for j in range(14):                                                              # 2단 얼룩(황토 녹 · 회색 때)
            c = -HX - e + (2 * HX + 2 * e) * hs_(s_, j, 481); w_ = 0.5 + 1.4 * hs_(s_, j, 482); hh = 0.15 + 0.3 * hs_(s_, j, 483)
            uz_prism(b6, [(c, z0 + 0.04), (c + w_, z0 + 0.04), (c + w_ * 0.8, z0 + hh), (c + 0.15, z0 + hh * 0.85)], fmN, 0.0, 0.03, j % 4)
        for j in range(7):
            c = -HY - e + (2 * HY + 2 * e) * hs_(s_, j, 484); w_ = 0.5 + 1.2 * hs_(s_, j, 485); hh = 0.15 + 0.3 * hs_(s_, j, 486)
            uz_prism(b6, [(c, z0 + 0.04), (c + w_, z0 + 0.04), (c + w_ * 0.8, z0 + hh), (c + 0.15, z0 + hh * 0.85)], fmW, 0.0, 0.03, (j + 1) % 4)
    # ── 기둥: L0 홈 20줄 몸통 · L3 북 이음매·고리 · L1 목 홈 · L2 에키누스·아바쿠스 · L5 밝은 세로 띠 · L6 2단 얼룩
    bcol = o.bm(0, 'Columns', 'ac_f1', 'ac_f2', 'ac_break')
    bcap = o.bm(2, 'Capitals', 'ac_cap', 'ac_m', 'ac_cap2')
    bdr = o.bm(3, 'Drums', 'ac_joint', 'ac_cap2')

    def column_d(x, y, z0, hd, r0, r1, h=None, seed=0.0):
        full = h is None
        hs = hd if full else h
        rt = r0 + (r1 - r0) * hs / hd
        rz = lambda z: r0 + (r1 - r0) * (z - z0) / hd
        fs = G.cyl(bcol, x, y, r0, z0, z0 + hs, 20, 0, r_top=rt, top=True)
        for i_ in range(20):
            fs[i_].material_index = i_ % 2
        if not full:
            fs[-1].material_index = 2
            G.box(bcol, x - r0 * 0.55, x + r0 * 0.25, y - r0 * 0.5, y + r0 * 0.35, z0 + hs, z0 + hs + 0.3 + 0.3 * hs_(seed, 491), 2)
        z = z0 + 0.95 + 0.2 * hs_(seed, 492); k = 0
        while z < z0 + hs - 0.45:
            rr = rz(z)
            G.ring(bdr, x, y, rr - 0.02, rr + 0.03, z - 0.045, z + 0.045, 6, 0, -145.0, 55.0)
            z += 0.82 + 0.25 * hs_(seed, k, 493); k += 1
        if full:
            ze = z0 + hs
            G.ring(bdep, x, y, rt - 0.02, rt + 0.028, ze - 0.62, ze - 0.55, 8, 0, -145.0, 55.0)
            for a_ in range(3):
                G.ring(bdr, x, y, rt - 0.01, rt + 0.035, ze - 0.2 + a_ * 0.065, ze - 0.165 + a_ * 0.065, 6, 1, -145.0, 55.0)
            G.cyl(bcap, x, y, rt + 0.01, ze, ze + 0.5, 20, 0, r_top=r1 * 1.38, top=True)
            ab = r1 * 1.42
            G.box(bcap, x - ab, x + ab, y - ab, y + ab, ze + 0.5, ze + 0.85, 1)
        _ak_cylpatch(b5, x, y, rz, -105.0, rect(-0.13, 0.13, z0 + 0.25, z0 + hs - 0.25), 0, 0.03)
        for j in range(3):
            zc = z0 + 0.6 + max(0.1, hs - 1.6) * hs_(seed, j, 494); hh = 0.5 + 1.6 * hs_(seed, j, 495)
            hh = min(hh, max(0.2, z0 + hs - 0.1 - zc))
            ph = -125.0 + 150.0 * hs_(seed, j, 496); w_ = 0.18 + 0.3 * hs_(seed, j, 497)
            lp = [(-w_ / 2, zc), (w_ / 2, zc + 0.08), (w_ * 0.4, zc + hh), (-w_ * 0.3, zc + hh * 0.9)]
            _ak_cylpatch(b6, x, y, rz, ph, lp, j if j < 2 else (2 if hs_(seed, j, 498) < 0.5 else 3), 0.04)

    HD = CH - 0.85
    cols = [(x, -VC, 'N', j) for j, x in enumerate(xs)] + [(x, VC, 'S', j) for j, x in enumerate(xs)] + \
           [(UC, y, 'W', i) for i, y in enumerate(ys) if 0 < i < 7] + [(-UC, y, 'E', i) for i, y in enumerate(ys) if 0 < i < 7]
    for (x, y, sd, j) in cols:
        stump = sd == 'S' and 5 <= j <= 10                                              # 남쪽 가운데 6주 = 그루터기(1687 폭발)
        column_d(x, y, ZS, HD, R0, R1, (1.6 + 4.8 * hs_(j, 499)) if stump else None, seed=x * 3.1 + y * 7.7)
    yp = [-9.75 + 3.9 * k for k in range(6)]
    for k, y in enumerate(yp):                                                           # 안쪽 현관 6주: 서쪽 온전 · 동쪽 그루터기
        column_d(29.0, y, ZI, CH - 0.7 - 0.85, 0.85, 0.66, None, seed=100.0 + k)
        column_d(-29.0, y, ZI, CH - 0.7 - 0.85, 0.85, 0.66, 0.8 + 2.6 * hs_(k, 500), seed=200.0 + k)
    # ── 엔타블러처(일부만 남음): L2 아키트레이브·프리즈(트리글리프·메토프)·코니스 · L1 트리글리프 홈 · L4 레굴라·구타이·부조 덩이
    ba = o.bm(2, 'Architrave', 'ac_m', 'ac_shade', 'ac_break')
    bfz = o.bm(2, 'Frieze', 'ac_m', 'ac_tri', 'ac_shade', 'ac_break')
    bgs = o.bm(2, 'Cornice', 'ac_m', 'ac_lt', 'ac_break')
    bgu = o.bm(4, 'Guttae', 'ac_cap', 'ac_cap2')
    SD = {'N': ('x', -VC, -1, xs), 'S': ('x', VC, 1, xs), 'W': ('y', UC, 1, ys), 'E': ('y', -UC, -1, ys)}
    INNER = {'N': 4, 'S': 2, 'W': 5, 'E': 3}                                             # G.box 면 순서 [아래, 위, −y, +x, +y, −x] 중 안쪽 면

    def sbox(bm, sd, a, b, d0, d1, z0, z1, mi):
        ax, line, sg, _ = SD[sd]
        c0, c1 = sorted((line + sg * d0, line + sg * d1))
        return G.box(bm, a, b, c0, c1, z0, z1, mi) if ax == 'x' else G.box(bm, c0, c1, a, b, z0, z1, mi)

    def ends(sd):
        return (UC if SD[sd][0] == 'x' else VC) + OUT

    def span(sd, j):
        p = SD[sd][3]; n = len(p) - 1; E_ = ends(sd)
        return (-E_ if j == 0 else p[j]), (E_ if j == n - 1 else p[j + 1])

    def span_of(sd, t):
        p = SD[sd][3]
        for j in range(len(p) - 1):
            if t <= p[j + 1]:
                return j
        return len(p) - 2

    def face_map(sd, d):
        return map_front(-VC - d) if sd == 'N' else map_right(UC + d)

    arch_ok = {'N': [True] * 16, 'S': [not (4 <= j <= 10) for j in range(16)], 'W': [True] * 7, 'E': [True] * 7}
    FKEEP = {'N': lambda j: j >= 13 or j == 7, 'S': lambda j: j >= 14, 'W': lambda j: True, 'E': lambda j: False}
    for sd in 'NSWE':
        n = len(SD[sd][3]) - 1
        for j in range(n):
            if not arch_ok[sd][j]:
                continue
            a, b = span(sd, j)
            fs = sbox(ba, sd, a, b, -INN, OUT, ZA0, ZA1, 0)
            if sd in 'SE':
                fs[INNER[sd]].material_index = 1
            if sd in 'NW':
                sbox(ba, sd, a, b, OUT - 0.02, OUT + 0.08, ZA1 - 0.16, ZA1, 0)
                sbox(b5, sd, a, b, OUT + 0.0, OUT + 0.09, ZA1 - 0.035, ZA1 + 0.004, 2)
                if j > 0:
                    pj = SD[sd][3][j]
                    sbox(bj3, sd, pj - 0.025, pj + 0.025, OUT - 0.01, OUT + 0.012, ZA0 + 0.04, ZA1 - 0.2, 0)
            for side, nb in ((-1, j - 1), (1, j + 1)):
                if 0 <= nb < n and not arch_ok[sd][nb]:
                    e_ = b if side > 0 else a
                    q0, q1 = (e_, e_ + 0.5) if side > 0 else (e_ - 0.5, e_)
                    sbox(ba, sd, q0, q1, -INN * 0.5, OUT * 0.6, ZA0, ZA0 + 0.6 + 0.4 * hs_(j, 501), 2)
        p = SD[sd][3]; E_ = ends(sd)
        T = sorted([-E_ + 0.42, E_ - 0.42] + [p[j] for j in range(1, len(p) - 1)] + [(p[j] + p[j + 1]) / 2.0 for j in range(len(p) - 1)])
        for k, t in enumerate(T):
            j = span_of(sd, t)
            if not arch_ok[sd][j]:
                continue
            h = hs_(k, ord(sd), 431)
            if FKEEP[sd](j) or (j > 0 and FKEEP[sd](j - 1) and abs(t - p[j]) < 0.05):
                kt = 1.0
            elif sd == 'N':
                kt = 0.0 if h < 0.12 else (1.0 if h > 0.32 else 0.4 + 0.5 * h)
            elif sd == 'E':
                kt = 0.0 if h < 0.2 else (1.0 if h > 0.45 else 0.5)
            else:
                kt = 0.0 if h < 0.4 else (1.0 if h > 0.7 else 0.5)
            if sd in 'NW':                                                               # 띠 밑 레굴라 + 구타이 6
                sbox(bgu, sd, t - 0.42, t + 0.42, OUT, OUT + 0.07, ZA1 - 0.27, ZA1 - 0.17, 0)
                for g in range(6):
                    c = t - 0.35 + 0.14 * g
                    gx, gy = (c, SD[sd][1] + SD[sd][2] * (OUT + 0.04)) if SD[sd][0] == 'x' else (SD[sd][1] + SD[sd][2] * (OUT + 0.04), c)
                    G.cyl(bgu, gx, gy, 0.045, ZA1 - 0.37, ZA1 - 0.27, 5, 1, r_top=0.055, top=False, bottom=True)
            if kt <= 0.0:
                continue
            zt = ZA1 + FH * kt
            fs = sbox(bfz, sd, t - 0.42, t + 0.42, -INN + 0.25, OUT, ZA1, zt, 1)
            if kt < 1.0:
                fs[1].material_index = 3
            if sd in 'NW' and zt > ZA1 + 0.4:
                for g in (-0.21, 0.21):
                    sbox(bdep, sd, t + g - 0.055, t + g + 0.055, OUT, OUT + 0.012, ZA1 + 0.1, min(zt - 0.05, ZF1 - 0.2), 0)
                if kt >= 1.0:
                    sbox(bfz, sd, t - 0.45, t + 0.45, OUT, OUT + 0.04, ZF1 - 0.2, ZF1, 0)
        for k in range(len(T) - 1):
            m0, m1 = T[k] + 0.42, T[k + 1] - 0.42
            mid = 0.5 * (m0 + m1); j = span_of(sd, mid)
            if not arch_ok[sd][j]:
                continue
            h = hs_(k, ord(sd), 441)
            if FKEEP[sd](j):
                km = 1.0
            elif sd == 'N':
                km = 0.0 if h < 0.82 else 0.55
            elif sd == 'E':
                km = 1.0 if h < 0.35 else 0.0
            else:
                km = 1.0 if h < 0.18 else 0.0
            if km <= 0.0:
                continue
            fs = sbox(bfz, sd, m0, m1, -INN + 0.25, OUT - 0.1, ZA1, ZA1 + FH * km, 0)
            if km < 1.0:
                fs[1].material_index = 3
            if sd in 'NW' and km >= 1.0:                                                 # 닳은 메토프 부조 덩이
                fm = face_map(sd, OUT - 0.1)
                for q in range(2):
                    cu = m0 + 0.25 + (m1 - m0 - 0.5) * hs_(k, q, 442); cz = ZA1 + 0.35 + 0.6 * hs_(k, q, 443); rr = 0.16 + 0.18 * hs_(k, q, 444)
                    uz_prism(bgu, [(cu + rr * math.cos(2 * math.pi * a_ / 5 + q), cz + rr * 1.3 * math.sin(2 * math.pi * a_ / 5 + q)) for a_ in range(5)],
                             fm, 0.0, 0.07, 1)
        n = len(p) - 1
        for j in range(n):                                                                # 코니스(남은 칸만)
            if not FKEEP[sd](j) or not arch_ok[sd][j]:
                continue
            a, b = span(sd, j)
            if j == 0:
                a -= 0.6
            if j == n - 1:
                b += 0.6
            sbox(bgs, sd, a, b, -INN + 0.2, OUT + 0.6, ZF1, ZG1, 0)
            if sd in 'NW':
                sbox(b5, sd, a, b, OUT + 0.54, OUT + 0.62, ZG1 - 0.09, ZG1 + 0.004, 0)
                for q in range(3):
                    c = a + (b - a) * hs_(j, q, ord(sd), 451); w_ = 0.2 + 0.35 * hs_(j, q, 452)
                    sbox(b4, sd, c - w_, c + w_, OUT + 0.25, OUT + 0.63, ZG1 - 0.18 - 0.2 * hs_(j, q, 453), ZG1 + 0.006, 0)
        if sd in 'NW':                                                                    # 아키트레이브 2단 얼룩(회색 때 · 황토)
            fm = face_map(sd, OUT)
            for q in range(30 if sd == 'N' else 14):
                c = -E_ + 2 * E_ * hs_(q, ord(sd), 541)
                if not arch_ok[sd][span_of(sd, c)]:
                    continue
                w_ = 0.3 + 0.8 * hs_(q, 542); L_ = 0.3 + 0.8 * hs_(q, 543)
                uz_prism(b6, [(c, ZA0 + 0.05), (c + w_, ZA0 + 0.05), (c + w_ * 0.8, ZA0 + L_), (c + 0.1, ZA0 + L_ * 0.8)], fm, 0.0, 0.03, (2, 3, 0, 1)[q % 4])
    # ── 서쪽 박공 흔적(북쪽 절반만 비탈 처마까지, 가운데부터 깨짐) · 북쪽 구석 조각 덩이(케크롭스 무리)
    bpd = o.bm(2, 'Pediment', 'ac_m', 'ac_break', 'ac_lt')
    W_ = VC + OUT + 0.6; PH = AK['PH']
    rake = lambda y: ZG1 + PH * (1.0 - abs(y) / W_)
    xt0, xt1 = UC - 0.35, UC + OUT - 0.3
    JAG = [(-2.4, None), (-1.6, ZG1 + 1.75), (-0.4, ZG1 + 2.05), (0.6, ZG1 + 1.0), (1.8, ZG1 + 1.3), (3.0, ZG1 + 0.5), (4.2, ZG1 + 0.25)]

    def tt(y, k):
        if y <= -2.4:
            return max(ZG1 + 0.12, rake(y) - 0.55)
        if y <= 4.2:
            for (ya, za), (yb, zb_) in zip(JAG, JAG[1:]):
                za = rake(-2.4) - 0.55 if za is None else za
                if ya <= y <= yb:
                    return za + (zb_ - za) * (y - ya) / (yb - ya)
        if y >= 12.0:
            return max(ZG1 + 0.12, rake(y) - 0.55)
        return ZG1 + 0.1 + 0.3 * hs_(k, 461)
    y_a, y_b = -(VC + OUT) + 0.3, (VC + OUT) - 0.3
    Yb = sorted(set([y_a, y_b] + [y for y, _ in JAG] + [y_a + 0.9 * q for q in range(60) if y_a + 0.9 * q < y_b]))
    fmP = map_right(xt0)
    for q in range(len(Yb) - 1):
        ya, yb = Yb[q], Yb[q + 1]
        fs = uz_prism(bpd, [(ya, ZG1), (yb, ZG1), (yb, tt(yb, q + 1)), (ya, tt(ya, q))], fmP, 0.0, xt1 - xt0, 0)
        if ya > -2.5:
            fs[4].material_index = 1
    yq = [-W_ + 0.8 * q for q in range(40) if -W_ + 0.8 * q < -5.0] + [-5.0]
    for q in range(len(yq) - 1):
        ya, yb = yq[q], yq[q + 1]
        uz_prism(bpd, [(ya, rake(ya) - 0.55), (yb, rake(yb) - 0.55), (yb, rake(yb) + 0.05), (ya, rake(ya) + 0.05)], map_right(xt0 - 0.2), 0.0,
                 UC + OUT + 0.6 - (xt0 - 0.2), 0)
        uz_prism(b5, [(ya, rake(ya) - 0.04), (yb, rake(yb) - 0.04), (yb, rake(yb) + 0.06), (ya, rake(ya) + 0.06)], map_right(UC + OUT + 0.55), 0.0, 0.08, 0)
    uz_prism(bpd, [(-5.0, rake(-5.0) - 0.55), (-4.6, rake(-4.6) - 0.6), (-4.4, rake(-4.6) + 0.02), (-5.0, rake(-5.0) + 0.05)], map_right(xt0 - 0.2), 0.0, 1.6, 1)
    for q in range(3):
        y = -11.0 + 1.5 * q; hh = 0.5 + 0.35 * hs_(q, 462)
        G.cyl(bgu, xt1 + 0.35, y, 0.35 + 0.15 * hs_(q, 463), ZG1, ZG1 + hh, 6, 1, r_top=0.2, top=True)
    # ── 내실: 낮게 남은 벽(L2) · 안쪽 바닥 깊이색(L1) · 서쪽 현관 아키트레이브 조각
    bw = o.bm(2, 'Cella', 'ac_m', 'ac_break', 'ac_shade')

    def wall(axis, t0, t1, a0, a1, prof, seed, gaps=(), inner=None):
        a = a0; k = 0
        while a < a1 - 0.05:
            b = min(a1, a + 1.2 + 0.25 * hs_(seed, k, 511))
            if a1 - b < 0.4:
                b = a1
            mid = 0.5 * (a + b)
            if not any(g0 < mid < g1 for g0, g1 in gaps):
                h = prof(mid, k)
                if h > 0.05:
                    fs = G.box(bw, a, b, t0, t1, ZI, ZI + h, 0) if axis == 'x' else G.box(bw, t0, t1, a, b, ZI, ZI + h, 0)
                    fs[1].material_index = 1
                    if inner is not None:
                        fs[inner].material_index = 2
            a = b; k += 1
    jr = lambda s, k, lo, hi: lo + (hi - lo) * hs_(s, k, 512)
    wall('x', -10.9, -9.7, -28.6, 28.6, lambda m, k: jr(1, k, 3.6, 4.4) if m > 25.4 else (0.3 if -8 < m < -3 else jr(1, k, 0.6, 2.6)), 1)
    wall('x', 9.7, 10.9, -28.6, 28.6, lambda m, k: jr(2, k, 3.4, 4.2) if m > 25.4 else (0.25 if -6 < m < 2 else jr(2, k, 1.0, 3.2)), 2, inner=2)
    wall('y', 24.3, 25.5, -9.7, 9.7, lambda m, k: jr(3, k, 3.6, 4.6), 3, gaps=((-2.45, 2.45),))
    wall('y', -25.5, -24.3, -9.7, 9.7, lambda m, k: jr(4, k, 0.9, 2.4), 4, gaps=((-2.45, 2.45),), inner=3)
    wall('y', 5.4, 6.6, -9.7, 9.7, lambda m, k: jr(5, k, 0.3, 1.1), 5, gaps=((-2.0, 2.0),))
    G.box(bdep, -24.3, 24.3, -9.7, 9.7, ZI, ZI + 0.008, 2)
    G.box(ba, 28.15, 29.85, -10.6, 2.0, ZA0, ZA1, 0)
    G.box(ba, 28.3, 29.7, 2.0, 2.5, ZA0, ZA0 + 0.7, 2)
    # ── L3 판석 두 톤 조각(주랑 바닥 · 내실 바닥)
    for gx in range(58):
        for gy in range(27):
            x0 = -HX + 0.1 + gx * 1.2; y0 = -HY + 0.1 + gy * 1.14
            x1, y1 = x0 + 1.2, y0 + 1.14
            if x1 > HX or y1 > HY or hs_(gx, gy, 521) > 0.15:
                continue
            cx_, cy_ = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
            if -24.3 < cx_ < 24.3 and -9.7 < cy_ < 9.7:
                z = ZI + 0.009
            elif -30.6 < cx_ < 30.6 and -11.6 < cy_ < 11.6:
                continue
            else:
                z = ZS
            G.box(bj3, x0 + 0.05, x1 - 0.05, y0 + 0.05, y1 - 0.05, z, z + 0.012, 1 + (gx + gy) % 2)
    # ── L4 앞에 흩어진 대리석 덩이 · 기둥 북 · 주두 · 잔돌
    bfr = o.bm(4, 'Fragments', 'ac_m', 'ac_f1', 'ac_f2', 'ac_break', 'ac_cap', 'ac_found')
    placed = []; k = 0
    while len(placed) < 70 and k < 4000:
        x = -42.0 + 96.0 * hs_(k, 531); y = -32.0 + 55.0 * hs_(k, 532); k += 1
        if not inside(x, y, 1.6) or not off_temple(x, y, 0.6):
            continue
        dx = max(0.0, x - (HX + e0), -(HX + e0) - x); dy = max(0.0, y - (HY + e0), -(HY + e0) - y)
        front = x > HX + e0 or y < -HY - e0
        if hs_(k, 533) > (0.95 if front else 0.25) * math.exp(-math.hypot(dx, dy) / 7.0):
            continue
        if any((x - px) ** 2 + (y - py) ** 2 < (pr + 1.0) ** 2 for px, py, pr in placed):
            continue
        t = hs_(k, 534); ang = math.pi * hs_(k, 535)
        if t < 0.55:
            w_ = 1.2 + 1.4 * hs_(k, 536); d_ = 0.7 + 0.6 * hs_(k, 537); hh = 0.55 + 0.5 * hs_(k, 538)
            fs = _rbox(bfr, x, -y, w_, d_, HT, HT + hh, ang, 0)
            if hs_(k, 539) < 0.3:
                fs[4].material_index = 3
            if hs_(k, 540) < 0.3:
                _rbox(bfr, x + 0.2, -y, w_ * 0.8, d_ * 0.9, HT + hh, HT + hh * 1.9, ang + 0.2, 5)
            placed.append((x, y, 0.5 * max(w_, d_)))
        elif t < 0.78:
            _ak_drum(bfr, x, y, HT, 0.88, 0.8 + 0.4 * hs_(k, 541), ang, 16, 1, 3)
            placed.append((x, y, 0.9))
        elif t < 0.88:
            fs = G.cyl(bfr, x, y, 0.88, HT, HT + 0.85 + 0.3 * hs_(k, 542), 20, 1, top=True)
            for i_ in range(20):
                fs[i_].material_index = 1 + i_ % 2
            fs[-1].material_index = 3
            placed.append((x, y, 0.9))
        else:
            _rbox(bfr, x, -y, 2.0, 2.0, HT, HT + 0.35, ang, 4)
            G.cyl(bfr, x, y, 1.0, HT + 0.35, HT + 0.75, 16, 4, r_top=0.72, top=True)
            placed.append((x, y, 1.4))
    for q in range(16):                                                                  # 내실 바닥에 쌓아 둔 대리석 덩이(복원 현장, 크레인 0)
        x = -22.0 + 44.0 * hs_(q, 556); y = -8.0 + 16.0 * hs_(q, 557)
        if 4.6 < x < 7.4:
            continue
        w_ = 1.0 + 1.2 * hs_(q, 558); d_ = 0.6 + 0.5 * hs_(q, 559); hh = 0.5 + 0.4 * hs_(q, 560)
        fs = _rbox(bfr, x, -y, w_, d_, ZI, ZI + hh, (0.0, 1.5708)[q % 2] + 0.1 * hs_(q, 561), 0)
        if q % 3 == 0:
            _rbox(bfr, x, -y, w_ * 0.9, d_, ZI + hh, ZI + 2 * hh, (0.0, 1.5708)[q % 2], 5)
    for q in range(160):
        x = -42.0 + 96.0 * hs_(q, 551); y = -34.0 + 58.0 * hs_(q, 552)
        if not inside(x, y, 1.0) or not off_temple(x, y, 0.1):
            continue
        s_ = 0.15 + 0.3 * hs_(q, 553)
        _rbox(bfr, x, -y, s_ * 1.4, s_, HT, HT + s_ * 0.7, 3.0 * hs_(q, 554), (0, 3, 5)[q % 3])
    # ── L6 풀: 계단 틈 · 꼭대기
    pts = []
    for q in range(40):
        s_ = q % 3; e = (2 - s_) * TR
        if q % 2:
            pts.append((-HX - e + (2 * HX + 2 * e) * hs_(q, 561), -HY - e + 0.25, 0.18 + 0.15 * hs_(q, 562), ZE + (s_ + 1) * ST - 0.0 - ST))
        else:
            pts.append((HX + e - 0.25, -HY - e + (2 * HY + 2 * e) * hs_(q, 563), 0.18 + 0.15 * hs_(q, 564), ZE + s_ * ST))
    for q in range(90):
        x = -44.0 + 100.0 * hs_(q, 565); y = -36.0 + 62.0 * hs_(q, 566)
        if inside(x, y, 1.0) and off_temple(x, y, 0.2):
            pts.append((x, y, 0.22 + 0.25 * hs_(q, 567), HT))
    tufts(b6, pts, [4, 5, 6], 31.0)
    o.done()
    return o


def acropolis_anchors(o, A):
    bvh = _bvh(o.root)
    ok = lambda n: any(s in n for s in ('Columns', 'Capitals', 'Architrave', 'Frieze', 'Cornice', 'Pediment', 'Cella', 'Crepis', 'Wall', 'Ashlar'))
    out = {}
    for role in ('L1_label', 'L1_c1', 'L1_m4'):
        if role in A:
            out[role] = put_anchor(o, role, A[role], ok, bvh=bvh)
    return out


# ═════════════════════════ 트라야누스 시장(Mercati di Traiano) ═════════════════════════
# d4 설계 배치(지역 평면 mm, u = 평면 +X · v = 평면 +Y, 높이 화면 mm): 마당 60×50.85, 뒤 언덕 테라스(비아 비베라티카 높이 9.85),
# 테라스 위 대회랑(Aula Grande, 교차 볼트 6칸, 넷째 칸 지붕을 걷어 볼트를 보인다)과 오른쪽 상점 동, 앞 반원(Grande Emiciclo) 3층.
# 반원: 1층 상점 11칸(트래버틴 문틀) · 2층 아치 창 + 벽돌 붙임기둥 + 삼각/활꼴 페디먼트 교대 · 3층 물러난 테라스 뒤 네모 창.
MK_W, MK_D = 60.0, 50.85
MK_TV, MK_ZT = 19.0, 9.85
MK_HC = (30.0, 34.0)             # 18:20 반원 중심(지름선 v = 34, 가운데 u = 30). 옛 (31, 34)
MK_ARC = (0.0, 180.0)            # 18:20 직각 원칙: 반원 호(Blender 각) 0°~180° → 열린 쪽 = −Y(평면 +v). 옛 45°~225°(카메라 대각)
MK_HALLS = ((8.6, 15.6, 34.0, 40.2, 8.4), (44.4, 51.4, 34.0, 40.2, 9.6))   # 반원 두 끝 반돔 홀(u0, u1, v0, v1, 높이)
MK_SWAP = False                  # True = 평면 u↔v 뒤집기(열린 쪽 +X, 뒤 블록이 왼쪽). 카메라가 u = v 대칭이라 보이는 면 성질은 같다
MK_R = (14.0, 15.6, 17.2, 21.0)
MK_Z = (7.66, 13.57, 18.39)
MK_AU = (3.0, 31.0, 2.0, 14.0, 29.55)
MK_RB = (36.0, 57.0, 2.0, 12.5, 21.9)
MK_NB = 17                       # 17:48 고도화: 11 → 17칸(레퍼런스 반원의 촘촘한 문·창 리듬)
MK_OPEN = 3                      # 지붕을 걷은 칸(0부터)
MK_RBS = ((9.0, 12.5, 4.6), (5.5, 9.0, 8.2), (2.0, 5.5, None))   # 18:05 오른쪽 동 계단식 3단: (앞 v0, v1, 테라스 위 높이 · None = ZRB)
MK_WP = 2.5                      # 18:05 뒤 블록 창 간격(화면 mm)


def build_market(GC, box):
    o = Obj('TrajanMarket', GC, mm=True)
    W, D, TV, ZT = MK_W, MK_D, MK_TV, MK_ZT
    hcx, hcy = MK_HC[0], -MK_HC[1]
    R1, R2, R3, RB = MK_R
    Z1, Z2, Z3 = MK_Z
    (A0, A1), NB = MK_ARC, MK_NB
    au0, au1, av0, av1, ZA = MK_AU
    rb0, rb1, rbv0, rbv1, ZRB = MK_RB
    BAY = (au1 - au0) / 6.0
    ZM = ZA - 2.9                # 대회랑 덩어리 윗면(걷은 칸에서 보이는 볼트 밑동 높이)
    # ── L0 덩어리
    b = o.bm(0, 'Hemicycle', 'brick', 'shade')
    def doors(k, Lb):
        c = Lb / 2; dh = min(1.0, 0.34 * Lb); sw = min(0.55, 0.2 * Lb)
        return [('rect', c - dh, c + dh, 0.0, 3.35), ('rect', c - sw, c + sw, 4.15, 4.85)]
    def win2(k, Lb):
        c = Lb / 2; wh = min(0.8, 0.28 * Lb)
        return [('arch', c - wh, c + wh, Z1 + 1.35, Z1 + 3.35)]
    def win3(k, Lb):
        c = Lb / 2
        return [('rect', c - 0.55, c + 0.55, Z2 + 1.1, Z2 + 2.9)]
    arc_wall(b, hcx, hcy, R1, R1 + 1.0, A0, A1, 0.0, Z1, NB, doors, 0, 1, 0)
    arc_wall(b, hcx, hcy, R2, R2 + 0.8, A0, A1, Z1, Z2, NB, win2, 0, 1, 0)
    arc_wall(b, hcx, hcy, R3, R3 + 0.7, A0, A1, Z2, Z3, NB, win3, 0, 1, 0)
    G.ring(b, hcx, hcy, R1 + 1.4, RB, 0.0, Z1, 60, 0, A0, A1)
    G.ring(b, hcx, hcy, R2 + 1.1, RB, Z1, Z2, 60, 0, A0, A1)
    G.ring(b, hcx, hcy, R3 + 1.0, RB, Z2, Z3, 60, 0, A0, A1)
    b = o.bm(0, 'Terrace', 'brick', 'brick_core')
    fs = bx(b, 0.0, W, 0.0, TV, 0.0, ZT, 0); fs[1].material_index = 1
    b = o.bm(0, 'EndHalls', 'brick', 'concrete')
    for (x0_, x1_, y0_, y1_, zt_) in MK_HALLS:                                     # 반원 두 끝 홀
        bx(b, x0_, x1_, y0_, y1_, 0.0, zt_, 0)
    for (cu, cv, z0) in [((h[0] + h[1]) / 2, (h[2] + h[3]) / 2, h[4]) for h in MK_HALLS]:   # 끝 홀 낮은 돔
        G.cyl(b, cu, -cv, 2.45, z0, z0 + 0.5, 32, 1, bottom=True)
        fs_, rows_ = G.dome(b, cu, -cv, 2.3, z0 + 0.5, 32, 6, 0.0, 1, 0.55)
        b.faces.new(rows_[0][::-1]).material_index = 1
    b = o.bm(0, 'Aula', 'brick', 'concrete')
    fs = bx(b, au0, au1, av0, av1, ZT, ZM, 0); fs[1].material_index = 1         # 대회랑 덩어리(벽·안쪽 상점)
    for vv0, vv1 in ((av0, av0 + 0.8), (av1 - 0.8, av1)):                         # 긴 바깥벽(지붕 높이까지)
        bx(b, au0, au1, vv0, vv1, ZM - 0.1, ZA, 0)
    for uu0, uu1 in ((au0, au0 + 0.8), (au1 - 0.8, au1)):                         # 끝 벽
        bx(b, uu0, uu1, av0, av1, ZM - 0.1, ZA, 0)
    RBS = [(sv0, sv1, ZRB if sh is None else ZT + sh) for sv0, sv1, sh in MK_RBS]   # 18:05 언덕을 따라 올라가는 계단식 3단(앞이 낮다)
    b = o.bm(0, 'RightBlock', 'brick', 'roofslab')
    for sv0, sv1, sz in RBS:
        fs = bx(b, rb0, rb1, sv0, sv1, ZT - 0.2, sz, 0)
        if sz < ZRB:
            fs[1].material_index = 1                                               # 아래 두 단 옥상 테라스 판
    # ── L0·L3 지붕: 대회랑 평지붕 판(걷은 칸 빼고) · 오른쪽 동 기와 박공
    b = o.bm(3, 'AulaRoof', 'roofslab', 'concrete')
    ko0, ko1 = au0 + BAY * MK_OPEN, au0 + BAY * (MK_OPEN + 1)
    for u0_, u1_ in ((au0 + 0.4, ko0 + 0.2), (ko1 - 0.2, au1 - 0.4)):
        bx(b, u0_, u1_, av0 + 0.4, av1 - 0.4, ZA - 0.7, ZA - 0.05, 0)
    b = o.bm(3, 'RightRoof', 'tile', 'brick')
    fs = G.gable(b, rb0, rb1, -RBS[2][1], -RBS[2][0], ZRB, ZRB + 1.8, 'X', 0, 0.25)   # 맨 뒤 단만 기와 박공
    fs[2].material_index = 1; fs[3].material_index = 1
    # 걷은 칸: 교차 볼트 바깥면(홈 주름)과 둘레 칸막이(안쪽 면은 깊이색)
    b = o.bm(4, 'OpenBay', 'concrete', 'deep', 'brick_core')
    ia0, ia1 = ko0 + 0.2, ko1 - 0.2
    iv0, iv1 = av0 + 0.8, av1 - 0.8
    nv0, nv1 = av0 + 2.2, av1 - 2.2                                               # 가운데 신랑(교차 볼트 칸)
    bx(b, ia0, ia1, iv0, nv0, ZM, ZM + 0.9, 2)                                     # 양옆 상점 위 낮은 볼트 지붕(속살)
    bx(b, ia0, ia1, nv1, iv1, ZM, ZM + 0.9, 2)
    _pillow(b, ia0, ia1, -nv1, -nv0, ZM, (nv1 - nv0) / 2, (ia1 - ia0) / 2, 0.15, 8, 10, 0)
    for uu in (ko0 - 0.05, ko1 - 0.35):                                           # 칸 사이 가로 아치 벽(지붕 아래까지)
        bx(b, uu, uu + 0.4, iv0, iv1, ZM, ZA - 0.05, 0)
    bg = o.bm(4, 'Groins', 'deeper', 'hi')
    xa_, xb_, ya_, yb_ = ia0, ia1, -nv1, -nv0
    xc_, yc_ = (xa_ + xb_) / 2, (ya_ + yb_) / 2
    ry_, rx_ = (yb_ - ya_) / 2, (xb_ - xa_) / 2
    hh_ = min(ry_, rx_ * 1.6)
    def zf_(x, y):
        a = max(0.0, 1.0 - ((y - yc_) / ry_) ** 2); c = max(0.0, 1.0 - ((x - xc_) / rx_) ** 2)
        return ZM + 0.15 + hh_ * 0.42 * max(math.sqrt(a), math.sqrt(c))
    for (p0, p1) in (((xa_ + 0.15, ya_ + 0.15), (xb_ - 0.15, yb_ - 0.15)), ((xb_ - 0.15, ya_ + 0.15), (xa_ + 0.15, yb_ - 0.15))):
        pts_ = [(p0[0] + (p1[0] - p0[0]) * j / 16, p0[1] + (p1[1] - p0[1]) * j / 16) for j in range(17)]
        tube_chain(bg, [(x, y, zf_(x, y) + 0.04) for x, y in pts_], 0.07, 5, 0)
    for xx in (xa_ + 0.12, xb_ - 0.12):
        pts_ = [(xx, ya_ + (yb_ - ya_) * j / 16) for j in range(17)]
        tube_chain(bg, [(x, y, zf_(x, y) + 0.04) for x, y in pts_], 0.06, 5, 1)
    # ── L3 바닥: 마당 판석 · 반원 앞 굽은 길(회색 판석) · 테라스 위 길(비아 비베라티카)
    b = o.bm(3, 'Paving', 'pave', 'cobble', 'ground')
    bx(b, 0.0, W, 0.0, D, 0.0, 0.2, 0)
    G.ring(b, hcx, hcy, R1 - 2.6, R1 - 0.05, 0.2, 0.27, 60, 1, A0, A1)
    bx(b, 0.2, W - 0.2, av1 + 0.05, TV - 0.15, ZT, ZT + 0.12, 1)                   # 비아 비베라티카
    bx(b, au1 + 0.05, rb0 - 0.05, av0 + 0.2, av1 + 0.0, ZT, ZT + 0.12, 1)          # 대회랑과 오른쪽 동 사이 골목
    bx(b, 0.2, au0 - 0.05, 0.2, av1, ZT, ZT + 0.1, 1)
    bx(b, rb1 + 0.05, W - 0.2, 0.2, av1, ZT, ZT + 0.1, 1)
    G.ring(b, hcx, hcy, R3 + 0.3, RB - 0.05, Z3, Z3 + 0.1, 60, 1, A0, A1)          # 반원 윗면 길
    # ── L1 깊이색: 상점·창 속, 끝 홀 문, 테라스 상점 아치
    b = o.bm(1, 'Depth', 'deep', 'deeper')
    G.ring(b, hcx, hcy, R1 + 1.0, R1 + 1.4, 0.0, Z1 - 0.1, 60, 1, A0, A1)
    G.ring(b, hcx, hcy, R2 + 0.8, R2 + 1.1, Z1, Z2 - 0.1, 60, 0, A0, A1)
    G.ring(b, hcx, hcy, R3 + 0.7, R3 + 1.0, Z2, Z3 - 0.1, 60, 0, A0, A1)
    fmT = map_front(-TV)
    for uc in (2.6, 6.8, 11.0, 49.8, 53.0):                                       # 테라스 앞면 상점 아치(반원 뒤 가운데는 가려진다)
        uz_prism(b, arch_loop(uc - 1.2, uc + 1.2, 0.0, 2.9), fmT, 0.0, 0.05, 0)
        uz_prism(b, arch_loop(uc - 0.8, uc + 0.8, 5.0, 6.9), fmT, 0.0, 0.05, 0)
    fmTR = map_right(W)
    for vc in (2.6, 7.0, 11.4, 15.8):
        uz_prism(b, arch_loop(-vc - 1.2, -vc + 1.2, 0.0, 2.9), fmTR, 0.0, 0.05, 0)
        uz_prism(b, arch_loop(-vc - 0.8, -vc + 0.8, 5.0, 6.9), fmTR, 0.0, 0.05, 0)
    for (x0_, x1_, y0_, y1_, zt_) in MK_HALLS:                                     # 끝 홀 문·창(보이는 앞면·오른면)
        for (fm_, us) in ((map_front(-y1_), (x0_ + 1.7, x1_ - 1.7)), (map_right(x1_), (-(y0_ + 1.8), -(y1_ - 1.7)))):
            for uc in us:
                uz_prism(b, arch_loop(uc - 0.75, uc + 0.75, 0.0, 2.8), fm_, 0.0, 0.05, 1)
                uz_prism(b, arch_loop(uc - 0.55, uc + 0.55, 4.4, 6.2), fm_, 0.0, 0.05, 0)
    # ── L2 부재: 트래버틴 문틀·층 코니스·테라스 난간·붙임기둥·주두·대회랑 띠·처마
    b = o.bm(2, 'Members', 'trav_f', 'brick_hi', 'brick')
    fm1 = map_cyl(hcx, hcy, R1, A0)
    Lb1 = math.radians(A1 - A0) / NB * R1
    dh1 = min(1.0, 0.34 * Lb1)
    for k in range(NB):
        c = k * Lb1 + Lb1 / 2
        uz_prism(b, rect(c - dh1 - 0.22, c - dh1, 0.0, 3.35), fm1, -0.16, 0.0, 0)
        uz_prism(b, rect(c + dh1, c + dh1 + 0.22, 0.0, 3.35), fm1, -0.16, 0.0, 0)
        uz_prism(b, rect(c - dh1 - 0.22, c + dh1 + 0.22, 3.35, 3.7), fm1, -0.18, 0.0, 0)
    fm2 = map_cyl(hcx, hcy, R2, A0)
    Lb2 = math.radians(A1 - A0) / NB * R2
    for k in range(NB + 1):
        u = k * Lb2
        uz_prism(b, rect(u - 0.24, u + 0.24, Z1 + 0.6, Z2 - 0.9), fm2, -0.18, 0.0, 1)
        uz_prism(b, rect(u - 0.32, u + 0.32, Z2 - 0.9, Z2 - 0.6), fm2, -0.24, 0.0, 0)
        uz_prism(b, rect(u - 0.3, u + 0.3, Z1 + 0.35, Z1 + 0.6), fm2, -0.22, 0.0, 0)
    G.ring(b, hcx, hcy, R1 - 0.25, R1 + 0.3, Z1 - 0.32, Z1, 60, 0, A0, A1)          # 1층 코니스
    G.ring(b, hcx, hcy, R1 + 0.05, R1 + 0.3, Z1, Z1 + 0.5, 60, 2, A0, A1)           # 1층 위 테라스 난간
    G.ring(b, hcx, hcy, R2 - 0.22, R2 + 0.3, Z2 - 0.3, Z2, 60, 0, A0, A1)
    G.ring(b, hcx, hcy, R2 + 0.05, R2 + 0.3, Z2, Z2 + 0.45, 60, 2, A0, A1)
    G.ring(b, hcx, hcy, R3 - 0.2, R3 + 0.3, Z3 - 0.3, Z3, 60, 0, A0, A1)
    fA = map_front(-av1)
    for zz0, zz1 in ((ZT + 3.45, ZT + 3.8), (ZT + 8.2, ZT + 8.55), (ZT + 14.4, ZT + 14.75)):
        uz_prism(b, rect(au0, au1, zz0, zz1), fA, 0.0, 0.16, 0)                     # 대회랑 층 띠
    uz_prism(b, rect(au0 - 0.2, au1 + 0.2, ZA - 0.55, ZA), fA, 0.0, 0.3, 0)       # 처마 코니스
    uz_prism(b, rect(-av1 - 0.3, -av0 + 0.3, ZA - 0.55, ZA), map_right(au1), 0.0, 0.3, 0)
    for zz0, zz1 in ((ZT + 3.45, ZT + 3.8), (ZT + 8.2, ZT + 8.55), (ZT + 14.4, ZT + 14.75)):
        uz_prism(b, rect(-av1, -av0, zz0, zz1), map_right(au1), 0.0, 0.16, 0)
    for ti, (sv0, sv1, sz) in enumerate(RBS):                                      # 단마다 처마 코니스 · 층 띠 · 옥상 난간
        zv = ZT if ti == 0 else RBS[ti - 1][2] + 0.6                                # 앞 단 위로 보이는 높이부터
        uz_prism(b, rect(rb0 - 0.2, rb1 + 0.2, sz - 0.45, sz), map_front(-sv1), 0.0, 0.26, 0)
        uz_prism(b, rect(-sv1 - 0.25, -sv0 + 0.25, sz - 0.45, sz), map_right(rb1), 0.0, 0.26, 0)
        for zz in (ZT + 2.55, ZT + 4.95, ZT + 8.6):
            if zz < sz - 1.0:
                if zz > zv:
                    uz_prism(b, rect(rb0, rb1, zz, zz + 0.26), map_front(-sv1), 0.0, 0.14, 0)
                uz_prism(b, rect(-sv1, -sv0, zz, zz + 0.26), map_right(rb1), 0.0, 0.14, 0)
        if sz < ZRB:
            bx(b, rb0, rb1, sv1 - 0.28, sv1, sz, sz + 0.6, 2)
            bx(b, rb1 - 0.28, rb1, sv0, sv1 - 0.28, sz, sz + 0.6, 2)
    uz_prism(b, rect(0.0, W, ZT - 0.4, ZT), fmT, 0.0, 0.22, 0)                    # 테라스 윗선 난간 밑 띠
    bx(b, 0.0, W, TV - 0.28, TV, ZT, ZT + 0.5, 2)                                  # 비아 비베라티카 난간
    for zz0 in (0.0,):
        uz_prism(b, rect(0.0, W, zz0, zz0 + 0.35), fmT, 0.0, 0.14, 0)              # 굽도리
    # 계단: 마당 → 테라스 위 길(오른쪽 앞, v 19 → 23.5)
    for s_ in range(10):
        bx(b, 55.4, 59.0, TV + 0.45 * (9 - s_), TV + 0.45 * (10 - s_), 0.0, ZT * (s_ + 1) / 10.0, 0)
    # ── L3 표면 무늬: 벽돌(재질) + 지붕 판 줄 · 대회랑 지붕 칸 줄
    b = o.bm(3, 'RoofJoints', 'trav_f')
    for i in range(1, 6):
        uu = au0 + BAY * i
        if i in (MK_OPEN, MK_OPEN + 1):
            continue
        bx(b, uu - 0.1, uu + 0.1, av0 + 0.4, av1 - 0.4, ZA - 0.05, ZA + 0.06, 0)
    # ── L4 형태 디테일: 창 페디먼트(삼각·활꼴 교대), 대회랑·오른쪽 동의 문과 창, 끝면 큰 아치, 걷은 칸 안쪽 면
    b = o.bm(4, 'Details', 'brick_hi', 'deep', 'trav_f', 'deeper')
    pw = min(0.8, 0.28 * Lb2) + 0.15
    for k in range(NB):
        c = k * Lb2 + Lb2 / 2
        zp = Z1 + 4.4                                                        # 18:05 벽돌 처마 띠(홍예) 위로
        if k % 2 == 0:
            lp = [(c - pw, zp), (c + pw, zp), (c, zp + 0.5)]
        else:
            lp = [(c - pw, zp), (c + pw, zp), (c + pw * 0.8, zp + 0.3), (c + pw * 0.3, zp + 0.42), (c - pw * 0.3, zp + 0.42), (c - pw * 0.8, zp + 0.3)]
        uz_prism(b, lp, fm2, -0.2, -0.01, 0)
    def win_grid(fmap, us, rows, rec=None):
        """18:05 창 줄: 구멍(짙은 색) · 트래버틴 창턱 · 벽돌 아치 머리(네모 창은 덜어내기 아치, 아치 창은 처마 띠). 'd' = 문(창턱 없이 트래버틴 인방)"""
        for u in us:
            for z0_, z1_, w, kind in rows:
                lp = arch_loop(u - w / 2, u + w / 2, z0_, z1_ - w / 2) if kind == 'a' else rect(u - w / 2, u + w / 2, z0_, z1_)
                uz_prism(b, lp, fmap, 0.0, 0.05, 3 if kind == 'd' else 1)
                if kind == 'd':
                    uz_prism(b, rect(u - w / 2 - 0.18, u + w / 2 + 0.18, z1_, z1_ + 0.24), fmap, 0.0, 0.12, 2)
                else:
                    uz_prism(b, rect(u - w / 2 - 0.2, u + w / 2 + 0.2, z0_ - 0.15, z0_), fmap, 0.0, 0.12, 2)
                    arch_band(b, fmap, u, z1_ - w / 2 if kind == 'a' else z1_, w / 2 + 0.03, w / 2 + 0.24, 0.0, 0.1, 0, 6)
                if rec is not None:
                    rec.append((u - w / 2 - 0.3, u + w / 2 + 0.3, z0_ - 0.2, z1_ + (0.3 if kind == 'a' else 0.55)))
    def holes_on(fmap, us, rows, d=0.05, mi=1):
        for u in us:
            for z0_, z1_, w, kind in rows:
                lp = arch_loop(u - w / 2, u + w / 2, z0_, z1_ - w / 2) if kind == 'a' else rect(u - w / 2, u + w / 2, z0_, z1_)
                uz_prism(b, lp, fmap, 0.0, d, mi)
    us6 = [au0 + BAY * (i + 0.5) for i in range(6)]
    holes_on(fA, us6, [(ZT + 0.0, ZT + 2.9, 1.7, 'r')])
    us12 = [au0 + BAY * (i + 0.5) / 2.0 for i in range(12)]                       # 17:48: 위층 창 6 → 12칸(레퍼런스의 촘촘한 창 줄)
    holes_on(fA, us12, [(ZT + 4.6, ZT + 6.6, 0.8, 'r'), (ZT + 9.6, ZT + 12.6, 1.0, 'a'), (ZT + 15.6, ZT + 17.0, 0.7, 'r')])
    for u in us12:                                                                 # 창턱(트래버틴, L4)
        for zz in (ZT + 4.6, ZT + 9.6, ZT + 15.6):
            uz_prism(b, rect(u - 0.6, u + 0.6, zz - 0.18, zz), fA, 0.0, 0.12, 2)
    for u in us6:                                                                  # 상점 문틀(트래버틴)
        uz_prism(b, rect(u - 1.05, u - 0.85, ZT, ZT + 2.9), fA, 0.0, 0.1, 2)
        uz_prism(b, rect(u + 0.85, u + 1.05, ZT, ZT + 2.9), fA, 0.0, 0.1, 2)
        uz_prism(b, rect(u - 1.05, u + 1.05, ZT + 2.9, ZT + 3.2), fA, 0.0, 0.12, 2)
    fAR = map_right(au1)
    vc = -(av0 + av1) / 2
    uz_prism(b, arch_loop(vc - 2.3, vc + 2.3, ZT, ZT + 5.8), fAR, 0.0, 0.06, 3)    # 대회랑 끝 큰 아치 문
    arch_band(b, fAR, vc, ZT + 5.8, 2.3, 2.75, 0.0, 0.14, 0, 9)
    HOLES = {'fA': [], 'fAR': [(vc - 3.0, vc + 3.0, ZT, ZT + 8.8)]}                  # 18:05 얼룩 놓을 때 피할 창 자리(면별)
    vsA = [-(av0 + 1.0 + MK_WP * i) for i in range(int((av1 - av0 - 1.0) / MK_WP) + 1)]   # 대회랑 오른면 창 기둥(간격 2.5)
    win_grid(fAR, [v for v in vsA if abs(v - vc) > 3.4], [(ZT + 6.9, ZT + 8.1, 0.7, 'r')], HOLES['fAR'])
    win_grid(fAR, vsA, [(ZT + 9.6, ZT + 12.4, 1.0, 'a'), (ZT + 15.6, ZT + 17.0, 0.8, 'r')], HOLES['fAR'])
    for u in us12:                                                                 # 대회랑 앞면 네모 창 위 덜어내기 아치 · 아치 창 처마 띠
        for zz, w, kind in ((ZT + 6.6, 0.8, 'r'), (ZT + 12.6, 1.0, 'a'), (ZT + 17.0, 0.7, 'r')):
            arch_band(b, fA, u, zz - (w / 2 if kind == 'a' else 0.0), w / 2 + 0.03, w / 2 + 0.24, 0.0, 0.1, 0, 6)
            HOLES['fA'].append((u - w / 2 - 0.35, u + w / 2 + 0.35, zz - (2.0 if kind == 'r' else 3.0) - 0.4, zz + 0.4))
    for u in us6:
        HOLES['fA'].append((u - 1.3, u + 1.3, ZT, ZT + 3.4))
    fRB = map_front(-RBS[0][1])
    fRR = map_right(rb1)
    usR = [rb0 + 1.25 + MK_WP * i for i in range(int((rb1 - rb0) / MK_WP))]        # 18:05 단마다 창 줄(간격 2.5)
    RB_ROWS = ([(ZT, ZT + 2.3, 1.3, 'd'), (ZT + 2.95, ZT + 4.0, 0.7, 'r')],
               [(ZT + 5.55, ZT + 7.5, 0.9, 'a')],
               [(ZT + 9.05, ZT + 10.95, 0.9, 'a')])
    for ti, (sv0, sv1, sz) in enumerate(RBS):
        HOLES['RB%d' % ti] = []
        win_grid(map_front(-sv1), usR, RB_ROWS[ti], HOLES['RB%d' % ti])
    HOLES['RR'] = []
    for ti, (sv0, sv1, sz) in enumerate(RBS):                                      # 오른면: 단마다 창 기둥, 그 단 높이까지 모든 층
        rows_ = [r_ for t_ in range(ti + 1) for r_ in RB_ROWS[t_]] if ti else RB_ROWS[0]
        win_grid(fRR, [-(sv0 + sv1) / 2], rows_, HOLES['RR'])
    # 걷은 칸 둘레 안쪽 면(지붕 판 단면·바깥벽 안쪽) — 깊이색
    uz_prism(b, rect(ia0, ia1, ZM, ZA - 0.05), map_front(-(av0 + 0.8)), 0.01, 0.05, 1)
    uz_prism(b, rect(-(av1 - 0.8), -(av0 + 0.8), ZM, ZA - 0.05), map_right(ko0 + 0.35), 0.01, 0.05, 1)
    # 18:05 앞마당 = 트라야누스 포룸 폐허(콜로세움 둘레 폐허 밀도): 기둥 토막 5줄 · 떨어진 주두 · 쓰러진 기둥 북 · 깨진 판석 · 대리석 조각 · 빠진 판석 자리
    bru = o.bm(4, 'ForumRuins', 'marble', 'gran_g', 'trav_f', 'deep', 'marble_hi')
    halls_ = [h[:4] for h in MK_HALLS]
    def free_(uu, vv, m=0.6):
        dd_ = math.hypot(uu - MK_HC[0], vv - MK_HC[1]); ang_ = math.degrees(math.atan2(-(vv - MK_HC[1]), uu - MK_HC[0])) % 360.0
        if (R1 - 3.0 <= dd_ <= RB + 1.5 + m) and (A0 - 8.0 <= ang_ <= A1 + 8.0):           # 반원 벽 띠와 가게 앞 길(3)
            return False
        if any(x0 - 1.0 - m <= uu <= x1 + 1.0 + m and y0 - 1.0 - m <= vv <= y1 + 1.0 + m for (x0, x1, y0, y1) in halls_):
            return False
        if 54.6 <= uu <= 59.8 and vv <= TV + 5.5:                                          # 테라스 계단
            return False
        return 0.8 + m <= uu <= W - 0.8 - m and TV + 1.2 + m <= vv <= D - 0.8 - m
    k = 0
    for ri, vv in enumerate((36.0, 39.6, 43.2, 46.8, 49.9)):
        uu = 3.0 + 1.8 * (ri % 2)
        while uu < W - 2.0:
            if free_(uu, vv):
                hh = 0.4 + 2.8 * R.hash01(k, 61) ** 1.5
                G.box(bru, uu - 0.62, uu + 0.62, -vv - 0.62, -vv + 0.62, 0.2, 0.52, 2)                  # 주춧돌
                G.cyl(bru, uu, -vv, 0.44, 0.52, 0.52 + hh, 16, 1 if k % 3 else 0, r_top=0.41, bottom=True)
                G.cyl(bru, uu, -vv, 0.41, 0.52 + hh, 0.57 + hh, 16, 4 if k % 2 else 0)                    # 부러진 윗면(밝은 대리석)
                if k % 4 == 1 and free_(uu + 1.0, vv + 0.4, 0.2):                                         # 옆에 떨어진 주두 덩이
                    _rbox(bru, uu + 1.0, vv + 0.4, 0.9, 0.9, 0.2, 0.75, 0.3 + R.hash01(k, 62), 0)
            uu += 3.6; k += 1
    nd_ = 0
    for j in range(60):                                                                   # 쓰러진 기둥 북 · 깨진 판석 틈
        if nd_ >= 18:
            break
        uu = 2.0 + (W - 4.0) * R.hash01(j, 63); vv = TV + 2.0 + (D - TV - 3.0) * R.hash01(j, 64)
        if not free_(uu, vv, 1.4):
            continue
        a_ = math.radians(180.0 * R.hash01(j, 65)); L_ = 1.4 + 1.2 * R.hash01(j, 66)
        n_ = 12
        ring_ = [(uu + 0.42 * math.cos(2 * math.pi * q / n_) * -math.sin(a_), -vv + 0.42 * math.cos(2 * math.pi * q / n_) * math.cos(a_), 0.2 + 0.42 + 0.42 * math.sin(2 * math.pi * q / n_)) for q in range(n_)]
        lo_ = [bru.verts.new(v_) for v_ in ring_]
        hi_ = [bru.verts.new((v_[0] + math.cos(a_) * L_, v_[1] + math.sin(a_) * L_, v_[2])) for v_ in ring_]
        for q in range(n_):
            bru.faces.new([lo_[q], lo_[(q + 1) % n_], hi_[(q + 1) % n_], hi_[q]]).material_index = 0
        bru.faces.new(lo_[::-1]).material_index = 4; bru.faces.new(hi_).material_index = 4
        nd_ += 1
    nf_ = 0
    for j in range(320):                                                                  # 깨진 판석(큰 것)·대리석 조각(작은 것)
        if nf_ >= 110:
            break
        uu = 1.5 + (W - 3.0) * R.hash01(j, 121); vv = TV + 1.5 + (D - TV - 2.5) * R.hash01(j, 122)
        if not free_(uu, vv, 0.3):
            continue
        big = j % 3 == 0
        w_ = (0.9 + 1.2 * R.hash01(j, 123)) if big else (0.25 + 0.35 * R.hash01(j, 123))
        d_ = (0.5 + 0.8 * R.hash01(j, 124)) if big else (0.2 + 0.3 * R.hash01(j, 124))
        h_ = (0.12 + 0.12 * R.hash01(j, 125)) if big else (0.18 + 0.3 * R.hash01(j, 125))
        _rbox(bru, uu, vv, w_, d_, 0.2, 0.2 + h_, math.pi * R.hash01(j, 126), (0, 2, 1, 4)[j % 4])
        nf_ += 1
    bfh = o.bm(1, 'ForumHoles', 'deep', 'shade')                                          # L1 빠진 판석 자리(짙은 흙·그늘)
    nh_ = 0
    for j in range(120):
        if nh_ >= 24:
            break
        uu = 2.0 + (W - 4.0) * R.hash01(j, 131); vv = TV + 2.0 + (D - TV - 3.0) * R.hash01(j, 132)
        if not free_(uu, vv, 0.8):
            continue
        _rbox(bfh, uu, vv, 1.6 * (1 + j % 2), 1.6, 0.2, 0.225, 0.0, j % 2)
        nh_ += 1
    # ── L5 하이라이트: 코니스·난간·처마 윗선, 지붕 용마루·가장자리
    b = o.bm(5, 'Highlights', 'hi', 'hi_brick', 'hi_tile')
    for zt in (Z1, Z2, Z3):
        G.ring(b, hcx, hcy, R1 - 0.32 if zt == Z1 else (R2 - 0.29 if zt == Z2 else R3 - 0.27), R1 - 0.2 if zt == Z1 else (R2 - 0.17 if zt == Z2 else R3 - 0.15),
               zt - 0.1, zt + 0.05, 60, 0, A0, A1)
    G.ring(b, hcx, hcy, R1 + 0.02, R1 + 0.12, Z1 + 0.42, Z1 + 0.55, 60, 1, A0, A1)
    for k in range(NB + 1):
        u = k * Lb2
        uz_prism(b, rect(u - 0.24, u - 0.13, Z1 + 0.65, Z2 - 0.95), fm2, -0.22, -0.17, 1)
    bx(b, au0 - 0.2, au1 + 0.2, av1 + 0.22, av1 + 0.32, ZA - 0.12, ZA + 0.05, 0)
    bx(b, au1 + 0.22, au1 + 0.32, av0 - 0.3, av1 + 0.3, ZA - 0.12, ZA + 0.05, 0)
    vm_ = (RBS[2][0] + RBS[2][1]) / 2
    bx(b, rb0 - 0.25, rb1 + 0.25, vm_ - 0.08, vm_ + 0.08, ZRB + 1.75, ZRB + 1.87, 2)
    for sv0, sv1, sz in RBS[:2]:                                                   # 옥상 난간 윗선
        bx(b, rb0, rb1, sv1 - 0.3, sv1 + 0.02, sz + 0.58, sz + 0.66, 0)
    bx(b, 0.0, W, TV - 0.28, TV - 0.02, ZT + 0.45, ZT + 0.56, 0)
    # ── L6 얼룩·식생·생활: 빗물 자국, 테라스 이끼·풀, 언덕 덤불
    b = o.bm(6, 'Stains', 'stain_brick', 'moss', 'stain')
    for k in range(NB):
        c = k * Lb1 + Lb1 * (0.2 + 0.6 * R.hash01(k, 21))
        L = 1.2 + 1.6 * R.hash01(k, 22)
        uz_prism(b, [(c - 0.3, Z1 - 0.35 - L), (c + 0.3, Z1 - 0.35 - L * 0.7), (c + 0.3, Z1 - 0.35), (c - 0.3, Z1 - 0.35)], fm1, -0.04, 0.0, 0)
    for k in range(10):
        u = 1.0 + 5.8 * k + 2.0 * R.hash01(k, 26)
        if 15.5 < u < 46.5:
            continue
        L = 1.5 + 2.5 * R.hash01(k, 27)
        uz_prism(b, [(u - 0.35, ZT - 0.45 - L), (u + 0.35, ZT - 0.45 - L * 0.7), (u + 0.35, ZT - 0.45), (u - 0.35, ZT - 0.45)], fmT, 0.0, 0.03, 0)
    for k in range(6):
        u = au0 + 1.0 + 4.6 * k + 1.5 * R.hash01(k, 28)
        L = 2.0 + 3.0 * R.hash01(k, 29)
        uz_prism(b, [(u - 0.35, ZA - 0.6 - L), (u + 0.35, ZA - 0.6 - L * 0.7), (u + 0.35, ZA - 0.6), (u - 0.35, ZA - 0.6)], fA, 0.0, 0.04, 0)
    for k in range(9):
        a0_ = A0 + 5.0 + 19.0 * k + 5.0 * R.hash01(k, 23)
        G.ring(b, hcx, hcy, R1 + 0.35, R2 - 0.1, Z1, Z1 + 0.05, 4, 1, a0_, a0_ + 4.0 + 5.0 * R.hash01(k, 24))
    bwx = o.bm(6, 'Weathering', 'stain_dk', 'stain', 'pan_stucco')            # 17:48: 벽돌면 풍화(콜로세움 수준) — 짙은 빗물 줄 · 밝은 얼룩
    for k in range(24):                                                          # 대회랑 앞면(층 띠 밑에서 흘러내림)
        u = au0 + 0.6 + (au1 - au0 - 1.2) * R.hash01(k, 71)
        zt = (ZT + 3.45, ZT + 8.2, ZT + 14.4, ZA - 0.55)[k % 4]
        L = 1.0 + 2.6 * R.hash01(k, 72); w = 0.18 + 0.3 * R.hash01(k, 73)
        uz_prism(bwx, [(u - w / 2, zt - L), (u + w / 2, zt - L * 0.8), (u + w / 2, zt), (u - w / 2, zt)], fA, 0.0, 0.06, 0 if k % 3 else 1)
    for k in range(16):                                                          # 오른쪽 동 앞면·오른면
        u = rb0 + 0.6 + (rb1 - rb0 - 1.2) * R.hash01(k, 74)
        sv0_, sv1_, sz_ = RBS[k % 3]; zt = sz_ - 0.45                               # 단마다 처마 밑에서 흘러내림
        L = 0.8 + 1.8 * R.hash01(k, 75); w = 0.2 + 0.25 * R.hash01(k, 76)
        uz_prism(bwx, [(u - w / 2, zt - L), (u + w / 2, zt - L * 0.8), (u + w / 2, zt), (u - w / 2, zt)], map_front(-sv1_), 0.0, 0.06, 0)
    for k in range(10):                                                          # 밝은 회반죽 얼룩(대회랑·반원 2층)
        u = au0 + 1.0 + (au1 - au0 - 2.0) * R.hash01(k, 77); zc = ZT + 1.0 + (ZA - ZT - 3.0) * R.hash01(k, 78)
        w = 0.8 + 1.4 * R.hash01(k, 79); h = 0.6 + 1.0 * R.hash01(k, 80)
        uz_prism(bwx, [(u - w / 2, zc - h / 2), (u + w * 0.4, zc - h / 2 - 0.2), (u + w / 2, zc + h * 0.3), (u - w * 0.3, zc + h / 2)], fA, 0.0, 0.05, 2)
    for k in range(NB):
        c = k * Lb2 + Lb2 * (0.15 + 0.7 * R.hash01(k, 81))
        L = 0.8 + 1.6 * R.hash01(k, 82)
        uz_prism(bwx, [(c - 0.2, Z2 - 0.3 - L), (c + 0.2, Z2 - 0.3 - L * 0.7), (c + 0.2, Z2 - 0.3), (c - 0.2, Z2 - 0.3)], fm2, -0.26, -0.22, 0)
    b = o.bm(6, 'Grass', 'grass1', 'grass2', 'grass3')
    pts = []
    for k in range(26):
        u = 0.6 + (W - 1.2) * R.hash01(k, 31); v = 0.6 + (av0 - 0.8) * R.hash01(k, 32)
        pts.append((u, -v, 0.45 + 0.3 * R.hash01(k, 33), ZT + 0.1))
    for k in range(14):
        a = math.radians(A0 + 6.0 + (A1 - A0 - 12.0) * R.hash01(k, 34)); rr = R3 + 1.3 + (RB - R3 - 1.8) * R.hash01(k, 35)
        pts.append((hcx + rr * math.cos(a), hcy + rr * math.sin(a), 0.4 + 0.3 * R.hash01(k, 36), Z3 + 0.1))
    for (u, v) in ((0.6, 20.0), (1.2, 26.0), (59.2, 22.0), (58.8, 30.0), (0.8, 40.0), (59.0, 44.0), (20.0, 50.3), (35.0, 50.2)):
        pts.append((u, -v, 0.6, 0.2))
    tufts(b, pts, [0, 1, 2], 7.0)
    # ══ 18:05 메인 추가 고도화(콜로세움 잣대): 반원 3단 입면 · 폐허 윗변 · 벽돌 켜 선 · 2단 얼룩 ══
    fm3 = map_cyl(hcx, hcy, R3, A0)
    Lb3 = math.radians(A1 - A0) / NB * R3
    wh2 = min(0.8, 0.28 * Lb2)
    sw1 = min(0.55, 0.2 * Lb1)
    # L4 창마다 벽돌 처마 띠(2층 아치 창 홍예) · 창턱 · 3층 네모 창 덜어내기 아치 · 1층 작은 창 아치
    bh = o.bm(4, 'Hoods', 'brick_hi', 'brick_dk', 'trav_f')
    for k in range(NB):
        c = k * Lb2 + Lb2 / 2
        arch_band(bh, fm2, c, Z1 + 3.35, wh2 + 0.02, wh2 + 0.22, -0.14, -0.005, 0, 8)
        uz_prism(bh, rect(c - wh2 - 0.3, c + wh2 + 0.3, Z1 + 1.13, Z1 + 1.32), fm2, -0.16, -0.005, 2)
        c3 = k * Lb3 + Lb3 / 2
        arch_band(bh, fm3, c3, Z2 + 2.9, 0.58, 0.8, -0.12, -0.005, 0, 6)
        uz_prism(bh, rect(c3 - 0.75, c3 + 0.75, Z2 + 0.93, Z2 + 1.1), fm3, -0.14, -0.005, 2)
        c1 = k * Lb1 + Lb1 / 2
        arch_band(bh, fm1, c1, 4.85, sw1 + 0.03, sw1 + 0.2, -0.12, -0.005, 0, 6)
    # L4 층 코니스 밑 이빨장식(세 단 모두) — 단 사이 띠를 콜로세움처럼 또렷하게
    bd = o.bm(4, 'Dentils', 'trav_f', 'brick_hi')
    for (rf, z0d, z1d, mi_) in ((R1, Z1 - 0.62, Z1 - 0.36, 0), (R2, Z2 - 0.56, Z2 - 0.32, 1), (R3, Z3 - 0.56, Z3 - 0.32, 1)):
        n_ = int(math.radians(A1 - A0) * rf / 0.5)
        da_ = math.degrees(0.12 / rf)
        for j in range(n_):
            a_ = A0 + (A1 - A0) * (j + 0.5) / n_
            G.ring(bd, hcx, hcy, rf - 0.15, rf + 0.01, z0d, z1d, 1, mi_, a_ - da_, a_ + da_)
    # L2 테라스 난간 기둥(1·2층 위, 칸 경계마다)
    bpp = o.bm(2, 'ParapetPosts', 'trav_f')
    for (rp, zp0, zp1) in ((R1, Z1, Z1 + 0.82), (R2, Z2, Z2 + 0.75)):
        da_ = math.degrees(0.2 / rp)
        for k in range(NB + 1):
            a_ = A0 + (A1 - A0) * k / NB
            G.ring(bpp, hcx, hcy, rp - 0.02, rp + 0.36, zp0, zp1, 1, 0, max(A0, a_ - da_), min(A1, a_ + da_))
    # L3 윗면·테라스 판석 줄(민무늬 윗면 없애기)
    bj = o.bm(3, 'TopJoints', 'shade', 'brick_dk')
    for j in range(36):
        a_ = A0 + (A1 - A0) * (j + 0.5) / 36
        G.ring(bj, hcx, hcy, R3 + 0.75, RB - 0.1, Z3 + 0.1, Z3 + 0.135, 1, 0, a_ - 0.25, a_ + 0.25)
    for rr_ in ((R3 + RB) / 2 - 0.4, (R3 + RB) / 2 + 0.9):
        G.ring(bj, hcx, hcy, rr_, rr_ + 0.1, Z3 + 0.1, Z3 + 0.135, 48, 0, A0, A1)
    for (rr0, rr1, zz) in ((R1 + 0.35, R2 - 0.05, Z1), (R2 + 0.35, R3 - 0.05, Z2)):
        for j in range(NB * 2):
            a_ = A0 + (A1 - A0) * (j + 0.5) / (NB * 2)
            G.ring(bj, hcx, hcy, rr0, rr1, zz + 0.02, zz + 0.055, 1, 1, a_ - 0.2, a_ + 0.2)
    # L4 폐허 윗변: 3층 벽 위 들쭉날쭉한 덩이 · 반원 두 끝의 부서진 윗층 벽 · 테라스 앞 난간 · 끝 홀 윗변
    bl = o.bm(4, 'RuinEdges', 'brick', 'brick_core', 'concrete')
    a_ = A0 + 2.0; k = 0
    while a_ < A1 - 4.0:
        w_ = 1.5 + 4.0 * R.hash01(k, 91); h_ = 0.25 + 0.95 * R.hash01(k, 92) ** 1.5
        G.ring(bl, hcx, hcy, R3 - 0.02, R3 + 0.72, Z3, Z3 + h_, 2, k % 2, a_, min(a_ + w_, A1 - 1.0))
        if h_ > 0.7:
            G.ring(bl, hcx, hcy, R3 + 0.08, R3 + 0.6, Z3 + h_, Z3 + h_ + 0.15 + 0.35 * R.hash01(k, 93), 1, 1, a_ + w_ * 0.2, a_ + w_ * 0.6)
        a_ += w_ + 1.0 + 4.0 * R.hash01(k, 94); k += 1
    for (ae, sg) in ((A0, 1.0), (A1, -1.0)):
        for j, (da, hh) in enumerate(((0.0, 2.4), (3.0, 1.6), (6.0, 1.0), (9.0, 0.45))):
            g0, g1 = ae + sg * da, ae + sg * (da + 3.0)
            G.ring(bl, hcx, hcy, R3 - 0.02, RB, Z3, Z3 + hh, 2, 1 if j % 2 else 0, min(g0, g1), max(g0, g1))
    for k in range(12):
        u_ = (0.6 + 13.0 * R.hash01(k, 95)) if k % 2 == 0 else (47.5 + 6.5 * R.hash01(k, 95))
        w_ = 0.6 + 1.4 * R.hash01(k, 96); h_ = 0.2 + 0.6 * R.hash01(k, 97)
        bx(bl, u_, u_ + w_, TV - 0.32, TV + 0.02, ZT + 0.5, ZT + 0.5 + h_, k % 2)
    for hi_, (x0_, x1_, y0_, y1_, zt_) in enumerate(MK_HALLS):
        for k in range(8):
            t_ = R.hash01(k + 10 * hi_, 98); ww_ = 0.6 + 0.7 * R.hash01(k + 10 * hi_, 99); hh_ = 0.3 + 0.8 * R.hash01(k + 10 * hi_, 100)
            if k % 2 == 0:
                u_ = x0_ + (x1_ - x0_ - 1.4) * t_
                bx(bl, u_, u_ + ww_, y1_ - 0.5, y1_, zt_, zt_ + hh_, 0)
            else:
                v_ = y0_ + (y1_ - y0_ - 1.4) * t_
                bx(bl, x1_ - 0.5, x1_, v_, v_ + ww_, zt_, zt_ + hh_, 0)
    # L3 벽돌 켜 선(평평한 벽: 대회랑 앞·오른면, 오른쪽 동 각 단 앞·오른면, 테라스 앞·오른면). 창·띠가 앞에 나와 덮는다
    bcs = o.bm(3, 'Courses', 'brick_dk')
    def courses(fm, u0, u1, z0, z1, step=0.9):
        z = z0 + step * 0.5
        while z < z1 - 0.1:
            uz_prism(bcs, rect(u0, u1, z, z + 0.07), fm, 0.0, 0.025, 0)
            z += step
    courses(fA, au0, au1, ZT + 0.3, ZA - 0.6)
    courses(fAR, -av1, -av0, ZT + 0.3, ZA - 0.6)
    for ti, (sv0, sv1, sz) in enumerate(RBS):
        courses(map_front(-sv1), rb0, rb1, ZT + 0.3 if ti == 0 else RBS[ti - 1][2] + 0.6, sz - 0.5)
        courses(fRR, -sv1, -sv0, ZT + 0.3, sz - 0.5)
    for (u0_, u1_) in ((0.0, 15.8), (46.2, 55.2)):
        courses(fmT, u0_, u1_, 0.4, ZT - 0.5)
    courses(fmTR, -TV, 0.0, 0.4, ZT - 0.5)
    # L6 2단 얼룩(밝은·짙은 벽돌) · 회반죽 떨어진 자리(벽돌 속) · 남은 회반죽 — 콜로세움의 돌 얼룩 조각처럼
    bpt = o.bm(6, 'Patches', 'brick_hi', 'brick_dk', 'brick_core', 'pan_stucco')
    def jag(u, z, w, h, k):
        return [(u - w / 2, z - h / 2), (u + w * (0.15 + 0.2 * R.hash01(k, 111)), z - h / 2 - 0.06), (u + w / 2, z - h * 0.1),
                (u + w * 0.3, z + h / 2), (u - w * (0.1 + 0.2 * R.hash01(k, 112)), z + h / 2 + 0.05), (u - w / 2 - 0.05, z + h * 0.05)]
    def patches(fm, u0, u1, z0, z1, n, seed, holes, dd=(0.0, 0.035)):
        k = m = 0
        while m < n and k < n * 8:
            u = u0 + (u1 - u0) * R.hash01(k, seed); z = z0 + (z1 - z0) * R.hash01(k, seed + 1)
            w = 0.45 + 1.1 * R.hash01(k, seed + 2); h = 0.28 + 0.5 * R.hash01(k, seed + 3)
            k += 1
            if u - w / 2 < u0 or u + w / 2 > u1 or z - h / 2 < z0 or z + h / 2 > z1:
                continue
            if any(not (u + w / 2 + 0.08 < a or u - w / 2 - 0.08 > b_ or z + h / 2 + 0.08 < c or z - h / 2 - 0.08 > d) for a, b_, c, d in holes):
                continue
            uz_prism(bpt, jag(u, z, w, h, k), fm, dd[0], dd[1], (0, 1, 1, 2, 0, 3)[m % 6])
            m += 1
    inner = (-0.045, -0.01)
    h1 = [(k * Lb1 + Lb1 / 2 - dh1 - 0.3, k * Lb1 + Lb1 / 2 + dh1 + 0.3, 0.0, 3.8) for k in range(NB)] + \
         [(k * Lb1 + Lb1 / 2 - sw1 - 0.3, k * Lb1 + Lb1 / 2 + sw1 + 0.3, 3.9, 5.15) for k in range(NB)]
    patches(fm1, 0.0, NB * Lb1, 0.3, Z1 - 0.7, 46, 141, h1, inner)
    h2 = [(k * Lb2 + Lb2 / 2 - wh2 - 0.32, k * Lb2 + Lb2 / 2 + wh2 + 0.32, Z1 + 1.05, Z1 + 4.95) for k in range(NB)] + \
         [(k * Lb2 - 0.34, k * Lb2 + 0.34, Z1 + 0.3, Z2 - 0.55) for k in range(NB + 1)]
    patches(fm2, 0.0, NB * Lb2, Z1 + 0.6, Z2 - 0.65, 30, 151, h2, inner)
    h3 = [(k * Lb3 + Lb3 / 2 - 0.85, k * Lb3 + Lb3 / 2 + 0.85, Z2 + 0.85, Z2 + 3.75) for k in range(NB)]
    patches(fm3, 0.0, NB * Lb3, Z2 + 0.3, Z3 - 0.65, 44, 161, h3, inner)
    bandA = [(au0, au1, ZT + zb - 0.05, ZT + zb + 0.4) for zb in (3.45, 8.2, 14.4)]
    patches(fA, au0 + 0.2, au1 - 0.2, ZT + 0.3, ZA - 0.7, 64, 171, HOLES['fA'] + bandA)
    patches(fAR, -av1 + 0.2, -av0 - 0.2, ZT + 0.3, ZA - 0.7, 26, 181, HOLES['fAR'] + [(-av1, -av0, ZT + zb - 0.05, ZT + zb + 0.4) for zb in (3.45, 8.2, 14.4)])
    for ti, (sv0, sv1, sz) in enumerate(RBS):
        zv = ZT + 0.2 if ti == 0 else RBS[ti - 1][2] + 0.7
        patches(map_front(-sv1), rb0 + 0.2, rb1 - 0.2, zv, sz - 0.55, 14, 191 + 10 * ti, HOLES['RB%d' % ti])
    patches(fRR, -RBS[0][1] + 0.2, -RBS[2][0] - 0.2, ZT + 0.2, RBS[2][2] - 0.55, 18, 221, HOLES['RR'])
    hT = [(uc - 1.4, uc + 1.4, 0.0, 4.2) for uc in (2.6, 6.8, 11.0, 49.8, 53.0)] + [(uc - 1.0, uc + 1.0, 4.9, 7.8) for uc in (2.6, 6.8, 11.0, 49.8, 53.0)]
    for (u0_, u1_, sd) in ((0.2, 15.6, 231), (46.4, 55.0, 241)):
        patches(fmT, u0_, u1_, 0.4, ZT - 0.6, 14, sd, hT)
    fmO = map_cyl(hcx, hcy, RB, A0)                                                # 반원 가까운 끝 볼록 바깥 벽(호 A0 ~ A0 + 50°): 켜 선 · 얼룩
    LO = math.radians(50.0) * RB
    z = 0.75
    while z < Z3 - 0.4:
        G.ring(bcs, hcx, hcy, RB - 0.01, RB + 0.025, z, z + 0.07, 12, 0, A0, A0 + 50.0)
        z += 0.9
    patches(fmO, 0.2, LO - 0.2, 0.3, Z3 - 0.5, 24, 251, [])
    if MK_SWAP:                                                                    # 평면 u↔v 뒤집기: Blender (x, y) → (−y, −x), 면 방향을 되돌린다
        for bm_, _ms in o.parts.values():
            for v in bm_.verts:
                v.co.x, v.co.y = -v.co.y, -v.co.x
            bmesh.ops.reverse_faces(bm_, faces=list(bm_.faces))
    o.done()
    return o


def market_life(o):
    ensure_protos()
    hc = MK_HC
    ppl = [(29.0, 38.0), (30.6, 39.4), (25.0, 30.6), (36.0, 41.5), (37.4, 42.4), (22.0, 41.0), (33.0, 46.5), (44.0, 44.0),
           (12.0, 30.0), (13.4, 31.0), (52.0, 37.0), (8.0, 44.0), (26.0, 47.0)]
    for k, (u, v) in enumerate(ppl):
        o.prop('person%d' % (k % 3), u, -v, H_PERSON, 360.0 * R.hash01(k, 41), z=0.2, tag='person%02d' % k)
    for k, (u, v) in enumerate(((6.0, 16.8), (7.5, 17.4), (34.0, 16.0), (44.0, 17.2), (22.0, 16.5))):
        o.prop('person%d' % ((k + 1) % 3), u, -v, H_PERSON, 360.0 * R.hash01(k, 42), z=MK_ZT + 0.12, tag='personT%02d' % k)
    st_h = H_PERSON * PROP_K['stall']
    for k, (u, v, rot) in enumerate(((24.0, 37.0, 30.0), (38.5, 37.5, -30.0), (31.0, 43.0, 0.0))):
        o.prop('stall', u, -v, st_h, rot, z=0.2, tag='stall%d' % k)
    for k, (u, v) in enumerate(((22.6, 36.0), (23.2, 35.4), (40.2, 36.8), (32.6, 44.2))):
        o.prop('amphora', u, -v, H_PERSON * PROP_K['amphora'], 0.0, z=0.2, tag='amphora%d' % k)
    trees = [('pine0', 53.5, 44.0), ('cypress1', 5.0, 46.2), ('cypress2', 3.4, 44.6), ('olive2', 57.0, 27.5), ('olive3', 2.6, 23.0),
             ('pine2', 58.0, 49.0)]
    for k, (pr, u, v) in enumerate(trees):
        o.prop(pr, u, -v, tree_h(pr), 41.0 * k, z=0.2, tag='tree%d' % k)
    for k, (pr, u, v, z) in enumerate((('bush0', 1.2, 21.5, 0.2), ('bush1', 58.8, 25.0, 0.2), ('bush2', 10.5, 49.6, 0.2), ('bush3', 50.0, 49.8, 0.2),
                                        ('bush1', 1.4, 3.0, MK_ZT + 0.1), ('bush0', 59.0, 4.5, MK_ZT + 0.1), ('bush2', 33.5, 3.0, MK_ZT + 0.1))):
        o.prop(pr, u, -v, tree_h(pr), 47.0 * k, z=z, tag='green%02d' % k)


def market_anchors(o, A):
    bvh = _bvh(o.root)
    out = {}
    if 'L2_m3' in A:
        out['L2_m3'] = put_anchor(o, 'L2_m3', A['L2_m3'], lambda n: ('AulaRoof' in n) or ('OpenBay' in n) or ('RoofJoints' in n), bvh=bvh)
    if 'L2_label' in A:
        out['L2_label'] = put_anchor(o, 'L2_label', A['L2_label'], lambda n: any(t in n for t in ('RightBlock', 'Details', 'Members', 'EndHalls', 'Hemicycle', 'Courses', 'Patches', 'RuinEdges')), bvh=bvh)   # 18:20 반원 −Y: 왼쪽 끝 홀도 라벨 면
    return out


def _pillow(bm, xa, xb, ya, yb, zs, ry, rx, T, nx=8, ny=10, mi=0, mside=None):
    """교차 볼트 바깥면(두 원통의 합집합 윗면)을 높이장으로 만든 닫힌 입체. 홈(groin)이 대각선 주름으로 보인다"""
    xc, yc = (xa + xb) / 2, (ya + yb) / 2
    hh = min(ry, rx * 1.6)
    def zf(x, y):
        a = max(0.0, 1.0 - ((y - yc) / ry) ** 2); b = max(0.0, 1.0 - ((x - xc) / rx) ** 2)
        return zs + T + hh * 0.42 * max(math.sqrt(a), math.sqrt(b))
    X = [xa + (xb - xa) * i / nx for i in range(nx + 1)]
    Y = [ya + (yb - ya) * j / ny for j in range(ny + 1)]
    top = [[bm.verts.new((x, y, zf(x, y))) for x in X] for y in Y]
    fs = []
    for j in range(ny):
        for i in range(nx):
            fs.append(bm.faces.new([top[j][i], top[j][i + 1], top[j + 1][i + 1], top[j + 1][i]]))
    ring = [top[0][i] for i in range(nx + 1)] + [top[j][nx] for j in range(1, ny + 1)] + \
           [top[ny][i] for i in range(nx - 1, -1, -1)] + [top[j][0] for j in range(ny - 1, 0, -1)]
    bot = [bm.verts.new((v.co.x, v.co.y, zs)) for v in ring]
    side = []
    for k in range(len(ring)):
        k2 = (k + 1) % len(ring)
        side.append(bm.faces.new([ring[k2], ring[k], bot[k], bot[k2]]))
    fs.append(bm.faces.new(bot[::-1]))
    for f in fs:
        f.material_index = mi
    for f in side:
        f.material_index = mi if mside is None else mside
    G.uv_box(bm, fs + side)
    return fs + side


# ═════════════════════════ 막센티우스 바실리카(Basilica of Maxentius) ═════════════════════════
# spec L7 plan(평면 mm)을 그대로 짓는다. 루트 = 측랑 뒤-왼쪽 모서리 평면 (aisle X0, Y0), 지역 (u, w) = (X − X0, Y − Y0) → Blender (u, −w).
# 남은 것: 북쪽 측랑 3칸(두꺼운 칸막이 벽 위 팔각 코퍼 배럴 볼트, 볼트 축 = 평면 Y, 열린 면 +Y = 신랑 쪽 화면 왼쪽 아래), 가운데 칸 뒤벽 앱스.
# 신랑·남쪽 측랑: 대리석 바닥·기둥 밑동·낮은 벽 자국(평면 Y ≥ 60, 높이 ≤ 4). 무너진 신랑 교차 볼트 3칸은 정보 잉크 점선 복원(관 지름 0.245 BU = 화면 0.30mm).
def _maxentius_plan(LM7):
    pl = LM7['plan']
    ais, nav, dsh, pav = pl['aisle'], pl['nave_ruins'], pl['nave_vault_dashed'], pl['paving']
    prof = dsh.get('profile', '')
    m = re.search(r'z\(Y\)\s*=\s*([\d.]+)\s*·\s*sin\(π·\(Y\s*−\s*([\d.]+)\)/([\d.]+)\)', prof)
    if m:
        amp, y_a, span = float(m.group(1)), float(m.group(2)), float(m.group(3))
    else:
        amp, y_a = dsh.get('h_max', 10.0) - 1.0, nav['Y'][0] + 1.0
        span = nav['Y'][1] - y_a
    xs_d = [nav['X'][0] + (nav['X'][1] - nav['X'][0]) * i / dsh['bays'] for i in range(dsh['bays'] + 1)]
    m_ = re.search(r'Y\s*≥\s*([\d.]+)', nav.get('place_rule', ''))
    ry_ = float(m_.group(1)) if m_ else nav['Y'][0] + 4.5
    if ry_ < nav['Y'][0] - 0.01:                     # 20:01 d5: 문구 속 Y(≥ 60, 56.5)가 옛 좌표계 → 열린 면(Y0 + 4.5 = 규칙)에 맞춰 같은 만큼 옮긴다
        d_ = nav['Y'][0] - (ry_ - 4.5)
        ry_ += d_; y_a += d_
    return dict(AX=ais['X'], AY=ais['Y'], AH=ais['h'], NB=ais['bays'], NX=nav['X'], NY=nav['Y'], NH=nav['h_max'],
                rule_y=ry_,
                amp=amp, y_a=y_a, span=span, xs_d=xs_d, dash=dsh.get('dash_mm', [1.2, 0.8]), rects=pav['rects_plan'])


def build_maxentius(GC, LM7):
    P_ = _maxentius_plan(LM7)
    X0, Y0 = P_['AX'][0], P_['AY'][0]
    o = Obj('Maxentius', GC, mm=True, X=X0, Y=Y0)
    place_plan(o.root, X0, Y0)
    LU = P_['AX'][1] - X0                      # 측랑 길이(u)
    WD = P_['AY'][1] - Y0                      # 측랑 깊이(w)
    H = P_['AH']
    NB = P_['NB']
    bay = LU / NB
    TD, TE, TB = 2.2, 1.1, 1.8                 # 칸막이 벽·끝 벽·뒤벽 두께
    span = (LU - 2 * TE - (NB - 1) * TD) / NB
    bays = [(TE + i * (span + TD), TE + i * (span + TD) + span) for i in range(NB)]
    divs = [(b1, b1 + TD) for (b0, b1) in bays[:-1]]
    RV = span / 2
    ZS = H - 0.5 - RV - 1.0                    # 볼트 받침 높이(안쪽 꼭대기 H − 1.5)
    TV = 0.7
    tops = [H - 0.15 - 0.55 * R.hash01(i, 1) for i in range(12)]
    # ── L0 덩어리: 뒤벽(가운데 칸 앱스 구멍)·끝 벽·칸막이 벽·볼트·앞 홍예 벽·지붕 덩어리
    b = o.bm(0, 'Shell', 'max_brick', 'brick_core')
    ca = (bays[1][0] + bays[1][1]) / 2
    AR = min(4.2, span / 2 - 1.6)
    fs = G.wall_holes(b, 'X', 0.05, LU - 0.05, -TB, 0.0, 0.0, H - 0.3, [('arch', ca - AR, ca + AR, 0.0, ZS - 0.5)], 0)
    for (u0, u1) in [(0.0, TE + 0.2), (LU - TE - 0.2, LU)] + [(d0, d1) for d0, d1 in divs]:
        fs = bx(b, u0, u1, 0.3, WD + 0.12, 0.0, H - 0.3 + 0.2 * R.hash01(u0, 2), 0); fs[1].material_index = 1
    b = o.bm(0, 'Vaults', 'concrete')
    for (u0, u1) in bays:
        barrel_y(b, -(TB - 0.2), -(WD - 0.75), (u0 + u1) / 2, ZS, RV, RV + TV, 28, 0)
    b = o.bm(0, 'FrontArches', 'max_brick')
    for i, (u0, u1) in enumerate(bays):
        G.wall_holes(b, 'X', u0 - 0.3, u1 + 0.3, -WD, -(WD - 0.8), 0.0, tops[i] - 0.25, [('arch', u0 + 0.18, u1 - 0.18, 0.0, ZS)], 0, 14)
    b = o.bm(0, 'RoofMass', 'max_brick', 'brick_core')
    for i, (u0, u1) in enumerate(bays):
        fs = bx(b, u0 - 0.25, u1 + 0.25, TB - 0.25, WD - 0.6, ZS + RV * 0.72, tops[i], 0); fs[1].material_index = 1
    for k, (d0, d1) in enumerate([(-0.0, TE)] + divs + [(LU - TE, LU)]):
        zt = H - 0.1 + (0.9 if 0 < k < NB else 0.2) * R.hash01(k, 3)
        fs = bx(b, d0 - 0.15, d1 + 0.15, 0.1, WD - 0.65, H - 1.2, zt, 0); fs[1].material_index = 1
    # 17:48 레퍼런스: 무너진 윗변(들쭉날쭉한 잔해 덩이·깎인 홈, L4) · 윗면 수풀 덩이(L6) · 앞면 짙은 빗물 줄(L6)
    bbt = o.bm(4, 'BrokenTop', 'max_brick', 'brick_core')
    bsc = o.bm(6, 'TopScrub', 'grass2', 'moss', 'grass1')
    bsk = o.bm(6, 'FrontStreaks', 'stain_dk', 'stain_brick')
    for i, (u0, u1) in enumerate(bays):
        zt = tops[i]
        u = u0 - 0.2
        k = 0
        while u < u1 + 0.2:                                                              # 앞·뒤 윗변 덩이(높이 들쭉날쭉, 군데군데 빔)
            w_ = 0.7 + 0.9 * R.hash01(i, k, 91); h_ = 0.25 + 1.1 * R.hash01(i, k, 92) ** 1.5
            for (w0, w1) in ((WD - 1.6, WD - 0.6), (TB - 0.25, TB + 0.9)):
                if R.hash01(i, k, w0, 93) > 0.22:
                    fs = bx(bbt, u, min(u1 + 0.25, u + w_), w0, w1, zt - 0.05, zt + h_ * (1.0 if w0 > 5 else 0.7), 0)
                    fs[1].material_index = 1 if R.hash01(i, k, 94) < 0.35 else 0
            u += w_ + 0.05; k += 1
        for j in range(5):                                                               # 윗면 수풀 덩이
            cu = u0 + 0.8 + (u1 - u0 - 1.6) * R.hash01(i, j, 95); cw = TB + 1.2 + (WD - TB - 3.4) * R.hash01(i, j, 96)
            rr = 0.6 + 0.8 * R.hash01(i, j, 97)
            G.cyl(bsc, cu, -cw, rr, zt, zt + 0.35 + 0.4 * R.hash01(i, j, 98), 8, j % 3, r_top=rr * 0.6, bottom=True)
        for j in range(6):                                                               # 앞면 빗물 줄(홍예 양옆·윗변에서)
            cu = u0 + (u1 - u0) * R.hash01(i, j, 99)
            if abs(cu - (u0 + u1) / 2) < RV - 0.4:
                zt2 = ZS + RV + 0.8
            else:
                zt2 = zt - 0.2
            L = 1.2 + 2.8 * R.hash01(i, j, 100); w2 = 0.2 + 0.25 * R.hash01(i, j, 101)
            uz_prism(bsk, [(cu - w2 / 2, zt2 - L), (cu + w2 / 2, zt2 - L * 0.85), (cu + w2 / 2, zt2), (cu - w2 / 2, zt2)], map_front(-WD), 0.0, 0.03, j % 2)
    # 칸막이 벽 앞 끝: 신랑 교차 볼트가 뻗던 부서진 받침(평면 Y 55.5 앞으로 1.6)
    b = o.bm(4, 'Springers', 'max_brick', 'brick_core')
    for k, (d0, d1) in enumerate(divs):
        zt = H + 1.3 + 0.9 * R.hash01(k, 4)
        fs = bx(b, d0 - 0.3, d1 + 0.3, WD - 2.2, WD + 0.2, H - 1.6, zt, 0); fs[1].material_index = 1
        fs = wedge_y(b, d0 - 0.1, d1 + 0.1, -(WD + 1.7), -(WD + 0.2), H - 2.6, zt - 1.6, zt - 0.4, 0); fs[1].material_index = 1
    # ── L0·L1 앱스(가운데 칸 뒤벽): 반원 벽 + 반돔(안쪽 깊이색)
    b = o.bm(1, 'Apse', 'shade', 'deep', 'brick')
    arc_wall(b, ca, -TB + 0.05, AR, AR + 0.8, 0.0, 180.0, 0.0, ZS - 0.5, 9, None, 0, 0, 2)
    prof_o = [(max(0.08, (AR + 0.8) * math.cos(math.radians(9.0 * j))), ZS - 0.5 + (AR + 0.8) * math.sin(math.radians(9.0 * j))) for j in range(11)]
    prof_i = [(max(0.05, AR * math.cos(math.radians(9.0 * j))), ZS - 0.5 + AR * math.sin(math.radians(9.0 * j))) for j in range(11)]
    shell_of_rev(b, prof_o, prof_i, 12, 1, 0.0, 180.0, ca, -TB + 0.05)
    for k in range(5):                                                                   # 앱스 벽감 2단
        a = 18.0 + 36.0 * k
        for zb, zt in ((1.2, 3.6), (4.4, 6.0)):
            uz_prism(b, arch_loop(-0.45, 0.45, zb, zt - 0.45), map_cyl(ca, -TB + 0.05, AR, a), 0.0, 0.05, 1)
    # ── L1 깊이색: 뒤벽 안쪽 창 2단, 칸막이 벽 통로, 앞 홍예 안쪽
    b = o.bm(1, 'Depth', 'deep', 'deeper', 'shade')
    fB = map_front(-TB)
    for i, (u0, u1) in enumerate(bays):
        if i == 1:
            continue
        c = (u0 + u1) / 2
        for du in (-3.4, 0.0, 3.4):
            uz_prism(b, arch_loop(c + du - 0.85, c + du + 0.85, 1.6, 4.2), fB, 0.0, 0.05, 0)
            uz_prism(b, arch_loop(c + du - 0.75, c + du + 0.75, 6.0, 8.2), fB, 0.0, 0.05, 0)
    for (d0, d1) in [(0.0, TE)] + divs:                                                   # 오른쪽(+x)을 보는 칸막이 면: 아치 통로
        fmR = map_right(d1)
        uz_prism(b, arch_loop(-(WD - 2.6) , -(TB + 2.6), 0.0, 4.6), fmR, 0.0, 0.05, 1)
        uz_prism(b, arch_loop(-(WD - 4.2), -(TB + 4.2), 6.4, 8.0), fmR, 0.0, 0.05, 1)
    # ── L2 부재: 앞 홍예 띠(벽돌)·받침 띠(트래버틴)·처마 띠·대리석 기둥 받침
    b = o.bm(2, 'Members', 'brick_hi', 'trav_f', 'marble', 'gran_r')
    fF = map_front(-WD)
    for (u0, u1) in bays:
        c = (u0 + u1) / 2
        arch_band(b, fF, c, ZS, RV - 0.18, RV + 0.62, 0.0, 0.14, 0, 14)
        for uu in (u0, u1):
            uz_prism(b, rect(uu - 0.55, uu + 0.55, ZS - 0.45, ZS), fF, 0.0, 0.22, 1)
    for (d0, d1) in divs:
        uz_prism(b, rect(d0 - 0.2, d1 + 0.2, 0.0, 0.5), fF, 0.0, 0.2, 1)
    fE = map_right(LU)
    uz_prism(b, rect(-WD + 0.4, -0.2, H - 1.4, H - 0.95), fE, 0.0, 0.18, 1)
    uz_prism(b, rect(-WD + 0.4, -0.2, 0.0, 0.45), fE, 0.0, 0.16, 1)
    # ── L3 표면 무늬: 볼트 팔각 코퍼(+ 작은 마름모), 대리석 바닥·포장(재질)
    b = o.bm(3, 'Coffers', 'coffer', 'coffer_rim')
    for (u0, u1) in bays:
        xc = (u0 + u1) / 2
        fmv = map_barrel_y(xc, ZS, RV)
        na = 9; nax = 5
        for i in range(nax):
            yy = -(TB + 0.9) - (WD - TB - 2.1) * i / (nax - 1)
            for j in range(na):
                v = math.pi * RV * (j + 0.5) / na
                uz_prism(b, octagon(yy, v, 1.35), fmv, 0.02, 0.1, 0)
                if i < nax - 1 and j < na - 1:
                    vv = math.pi * RV * (j + 1.0) / na; yy2 = yy - (WD - TB - 2.1) / (nax - 1) / 2
                    uz_prism(b, [(yy2, vv - 0.32), (yy2 + 0.32, vv), (yy2, vv + 0.32), (yy2 - 0.32, vv)], fmv, 0.02, 0.07, 1)
    b = o.bm(3, 'Paving', 'pave', 'marble_fl')
    for i, (XA, XB, YA, YB) in enumerate(P_['rects']):
        bx(b, XA - X0, XB - X0, YA - Y0, YB - Y0, 0.0, 0.2 + 0.06 * i, 0 if i == 0 else 1)
    # ── L4 형태 디테일: 동쪽 끝벽(오른면) 창 2단·문, 무너진 윗면 속살·쓰러진 기둥·잔해, 남쪽 현관 반암 기둥 토막
    b = o.bm(4, 'EastWall', 'deep', 'trav_f', 'stain_brick')
    for vv in (-2.9, -6.0, -9.1):
        uz_prism(b, arch_loop(vv - 0.75, vv + 0.75, 1.8, 4.4), fE, 0.0, 0.05, 0)
        uz_prism(b, rect(vv - 0.95, vv + 0.95, 1.55, 1.8), fE, 0.0, 0.14, 1)
        uz_prism(b, arch_loop(vv - 0.65, vv + 0.65, 7.0, 9.2), fE, 0.0, 0.05, 0)
    for k in range(6):
        vv = -0.8 - 1.9 * k - 0.6 * R.hash01(k, 70); L = 1.5 + 3.0 * R.hash01(k, 71)
        uz_prism(b, [(vv - 0.3, H - 1.5 - L), (vv + 0.3, H - 1.5 - L * 0.7), (vv + 0.3, H - 1.5), (vv - 0.3, H - 1.5)], fE, 0.0, 0.03, 2)
    # 신랑·남쪽 측랑 유적(평면 Y ≥ rule_y, 높이 ≤ NH)
    nu0, nu1 = P_['NX'][0] - X0, P_['NX'][1] - X0
    nw0, nw1 = P_['rule_y'] - Y0, P_['NY'][1] - Y0
    hmax = P_['NH']
    xs_d = [x - X0 for x in P_['xs_d']]
    b = o.bm(0, 'RuinWalls', 'brick', 'brick_core')
    def stub(u0, u1, w0, w1, zt):
        fs = bx(b, u0, u1, w0, w1, 0.0, min(zt, hmax - 0.1), 0); fs[1].material_index = 1
    wS0 = nw1 - 0.95
    gap_c = (nu0 + nu1) / 2
    kk = 0
    for i in range(len(xs_d) - 1):                                                      # 남벽: 점선 리브 발(칸 경계 ±1.2)과 현관 자리는 비운다
        a0_, b0_ = xs_d[i] + 1.2, xs_d[i + 1] - 1.2
        for j in range(3):
            a_, b_ = a0_ + (b0_ - a0_) * j / 3, a0_ + (b0_ - a0_) * (j + 1) / 3
            kk += 1
            if abs((a_ + b_) / 2 - gap_c) < 2.6:
                continue
            stub(a_ + 0.05, b_ - 0.05, wS0, nw1 - 0.05, 0.7 + 1.9 * R.hash01(kk, 3))
    w_ns = nw0 + 0.62 * (nw1 - nw0)                                                     # 신랑/남쪽 측랑 경계 기둥 자리
    for uu in xs_d:
        stub(uu - 0.8, uu + 0.8, w_ns - 0.8, w_ns + 0.8, 1.2 + 1.4 * R.hash01(uu, 5))
        stub(uu - 0.32, uu + 0.32, w_ns + 0.8, wS0, 0.6 + 1.0 * R.hash01(uu, 6))           # 남쪽 측랑 칸 벽 자국
    w_end = nw0 + 0.75 * (nw1 - nw0)
    for (uu0, uu1) in ((nu0 + 0.35, nu0 + 1.25), (nu1 - 1.25, nu1 - 0.35)):              # 서·동 끝벽 자국(점선 가로 아치 발 쪽은 비운다)
        for k in range(4):
            a_ = nw0 + (w_end - nw0) * k / 4
            stub(uu0, uu1, a_ + 0.1, a_ + (w_end - nw0) / 4 - 0.1, 0.6 + 1.0 * R.hash01(uu0, k))
    b2 = o.bm(2, 'ColumnStubs', 'marble', 'gran_g', 'gran_r')
    for k, uu in enumerate(xs_d):                                                        # 신랑 대리석 기둥 밑동(점선 가로 아치가 여기서 뻗는다)
        for ww in (nw0 + 0.6, w_ns, wS0 - 0.6):
            G.box(b2, uu - 0.62, uu + 0.62, -(ww + 0.62), -(ww - 0.62), 0.0, 0.62, 0)
            if ww == wS0 - 0.6:
                continue
            G.cyl(b2, uu, -ww, 0.46, 0.62, min(2.8, 0.62 + 0.6 + 1.8 * R.hash01(k, ww)), 14, 1 if ww != w_ns else 0, bottom=True)
    # 16:25 레퍼런스(user_maxentius): 교각 앞에 선 코린트 기둥 — 신랑 북쪽 줄 2개를 주두까지 세운다(14.5 m ≈ 9.4 mm, 나머지는 밑동)
    bcl = o.bm(4, 'CorinthLeaves', 'marble_hi')
    b5c = o.bm(5, 'ColumnLight', 'marble_hi')
    for k, uu in enumerate(xs_d):
        if k not in (1, 3):
            continue
        ww = nw0 + 0.6
        G.cyl(b2, uu, -ww, 0.5, 0.62, 0.62 + 9.4, 14, 0, r_top=0.42, bottom=True)          # 밑동(0.46)을 덮는다
        G.cyl(b2, uu, -ww, 0.4, 0.62 + 9.4, 0.62 + 10.5, 14, 0, r_top=0.62)            # 코린트 종
        G.box(b2, uu - 0.72, uu + 0.72, -(ww + 0.72), -(ww - 0.72), 0.62 + 10.5, 0.62 + 10.8, 0)   # 대판
        for j in range(8):
            t = 2 * math.pi * (j + 0.5) / 8
            G.cyl(bcl, uu + 0.45 * math.cos(t), -ww + 0.45 * math.sin(t), 0.12, 0.62 + 9.4, 0.62 + 10.1, 5, 0, r_top=0.02)
        G.box(b5c, uu - 0.05, uu + 0.05, -(ww + 0.46), -(ww + 0.4), 1.0, 9.6, 0)
        G.box(b5c, uu - 0.72, uu + 0.72, -(ww + 0.72), -(ww + 0.55), 0.62 + 10.8, 0.62 + 10.83, 0)
    for k, uu in enumerate((gap_c - 1.9, gap_c - 0.65, gap_c + 0.65, gap_c + 1.9)):     # 남쪽 현관 반암 기둥 토막
        G.cyl(b2, uu, -(nw1 - 0.6), 0.36, 0.2, 0.9 + 1.4 * R.hash01(k, 7), 12, 2, bottom=True)
    b = o.bm(4, 'Rubble', 'marble', 'brick_core', 'trav_f')
    for k in range(3):                                                                   # 쓰러진 기둥 북 3개
        uu = nu0 + 9.0 + 9.5 * k; ww = nw0 + 4.0 + 3.0 * R.hash01(k, 8)
        n = 12
        lo = [b.verts.new((uu + 0.45 * math.cos(2 * math.pi * j / n), -ww, 0.65 + 0.45 * math.sin(2 * math.pi * j / n))) for j in range(n)]
        hi = [b.verts.new((uu + 0.45 * math.cos(2 * math.pi * j / n), -ww - 2.2, 0.65 + 0.45 * math.sin(2 * math.pi * j / n))) for j in range(n)]
        for j in range(n):
            b.faces.new([lo[j], lo[(j + 1) % n], hi[(j + 1) % n], hi[j]]).material_index = 0
        b.faces.new(lo[::-1]).material_index = 0; b.faces.new(hi).material_index = 0
    for k in range(26):
        uu = nu0 + 1.5 + (nu1 - nu0 - 3.0) * R.hash01(k, 9); ww = nw0 + 1.2 + (nw1 - nw0 - 2.6) * R.hash01(k, 10)
        w_ = 0.35 + 0.7 * R.hash01(k, 11); h = 0.2 + 0.45 * R.hash01(k, 12)
        G.box(b, uu - w_ / 2, uu + w_ / 2, -(ww + w_ * 0.4), -(ww - w_ * 0.4), 0.2, 0.2 + h, 1 if k % 3 else 2)
    for k in range(10):                                                                  # 측랑 윗면 잔해·속살
        uu = 1.0 + (LU - 2.0) * R.hash01(k, 13); ww = TB + 0.4 + (WD - TB - 1.6) * R.hash01(k, 14)
        zt = max(tops) + 0.05
        G.box(b, uu - 0.4, uu + 0.4, -(ww + 0.3), -(ww - 0.3), H - 1.0, H - 0.6 + 0.3 * R.hash01(k, 15), 1)
    # 무너진 신랑 교차 볼트 점선 복원(L4, 정보 잉크): 가로 아치 4 + 마루선 1 + 칸마다 대각 리브 2 — spec 평면 좌표 그대로
    b = o.bm(4, 'NaveVaultDashed', 'ink')
    amp, y_a, spn = P_['amp'], P_['y_a'], P_['span']
    def z_of(Y):
        return amp * math.sin(math.pi * (Y - y_a) / spn)
    rt = 0.1225
    to_scr = lambda p: R.scr(o.root.matrix_world @ Vector(p))
    curves = []
    for xd in xs_d:
        curves.append([(xd, -(y_a + spn * j / 48 - Y0), z_of(y_a + spn * j / 48)) for j in range(49)])
    ym = y_a + spn / 2
    curves.append([(xs_d[0] + (xs_d[-1] - xs_d[0]) * j / 48, -(ym - Y0), amp) for j in range(49)])
    for i in range(len(xs_d) - 1):
        for (xa, xb) in ((xs_d[i], xs_d[i + 1]), (xs_d[i + 1], xs_d[i])):
            curves.append([(xa + (xb - xa) * j / 48, -(y_a + spn * j / 48 - Y0), z_of(y_a + spn * j / 48)) for j in range(49)])
    nd = 0
    for ci, cv in enumerate(curves):
        nd += dashed_curve(b, cv, to_scr, rt, P_['dash'][0], P_['dash'][1], 0, phase=0.0)
    # ── L5 하이라이트: 홍예 띠 윗선, 처마 띠·끝벽 윗선, 무너진 윗면 모서리
    b = o.bm(5, 'Highlights', 'hi', 'hi_brick')
    for (u0, u1) in bays:
        c = (u0 + u1) / 2
        arch_band(b, fF, c, ZS, RV + 0.5, RV + 0.64, 0.14, 0.19, 1, 14)
    for i, (u0, u1) in enumerate(bays):
        bx(b, u0 + 0.1, u1 - 0.1, WD - 0.72, WD - 0.58, tops[i] - 0.14, tops[i] + 0.05, 1)
        bx(b, u0 - 0.2, u1 + 0.2, WD - 0.12, WD + 0.02, tops[i] - 0.25 - 0.12, tops[i] - 0.25 + 0.05, 1)
    uz_prism(b, rect(-WD + 0.4, -0.2, H - 1.0, H - 0.95), fE, 0.18, 0.22, 0)
    for (d0, d1) in divs:
        uz_prism(b, rect(d0 + 0.02, d0 + 0.16, 0.5, H - 1.4), fF, 0.12, 0.16, 1)
    # ── L6 얼룩·식생·생활: 빗물 자국, 무너진 윗면 풀·덤불, 바닥 틈 풀
    b = o.bm(6, 'Stains', 'stain_brick', 'moss')
    for k in range(14):
        uu = 0.6 + (LU - 1.2) * R.hash01(k, 16)
        bayk = [(u0, u1) for u0, u1 in bays if u0 + 0.4 < uu < u1 - 0.4]
        if bayk:
            c = (bayk[0][0] + bayk[0][1]) / 2
            zlow = ZS + math.sqrt(max(0.0, (RV + 0.7) ** 2 - (uu - c) ** 2)) + 0.2
            zt = H - 1.0
            if zlow > zt - 0.5:
                continue
            L = min(zt - zlow, 1.0 + 2.0 * R.hash01(k, 17))
            uz_prism(b, [(uu - 0.3, zt - L * 0.6), (uu + 0.3, zt - L), (uu + 0.3, zt), (uu - 0.3, zt)], fF, 0.0, 0.04, 0)
        else:
            zt, L = ZS - 0.6, 1.5 + 2.5 * R.hash01(k, 18)
            uz_prism(b, [(uu - 0.28, zt - L), (uu + 0.28, zt - L * 0.7), (uu + 0.28, zt), (uu - 0.28, zt)], fF, 0.0, 0.04, 0)
    b = o.bm(6, 'Grass', 'grass1', 'grass2', 'grass3', 'moss')
    pts = []
    for i, (u0, u1) in enumerate(bays):
        for j in range(4):
            pts.append((u0 + (u1 - u0) * R.hash01(i, j), -(TB + (WD - TB - 1.2) * R.hash01(j, i, 3)), 0.45 + 0.35 * R.hash01(i, j, 4), tops[i]))
    for k in range(34):
        uu = nu0 + 0.8 + (nu1 - nu0 - 1.6) * R.hash01(k, 19); ww = nw0 - 3.0 + (nw1 - nw0 + 1.0) * R.hash01(k, 20)
        pts.append((uu, -ww, 0.3 + 0.35 * R.hash01(k, 21), 0.2))
    for k in range(10):
        uu = -15.5 + 14.5 * R.hash01(k, 22); ww = 0.6 + 17.0 * R.hash01(k, 23)
        pts.append((uu, -ww, 0.3 + 0.3 * R.hash01(k, 24), 0.2))
    tufts(b, pts, [0, 1, 2, 3], 11.0)
    o.done()
    return o, P_, nd


def maxentius_life(o, P_):
    ensure_protos()
    X0, Y0 = P_['AX'][0], P_['AY'][0]
    nu0, nu1 = P_['NX'][0] - X0, P_['NX'][1] - X0
    nw0, nw1 = P_['rule_y'] - Y0, P_['NY'][1] - Y0
    ppl = [(6.0, 22.0), (7.4, 23.0), (17.0, 27.5), (24.0, 21.0), (25.4, 22.2), (33.0, 26.0), (38.0, 35.0), (12.0, 36.5),
           (13.2, 37.4), (28.0, 39.0), (20.0, 14.2), (21.4, 14.8), (-6.0, 6.0), (-7.2, 7.8), (-10.0, 12.0)]
    for k, (u, w) in enumerate(ppl):
        o.prop('person%d' % (k % 3), u, -w, H_PERSON, 360.0 * R.hash01(k, 61), z=0.2, tag='person%02d' % k)
    trees = [('cypress0', -15.2, 1.6), ('cypress1', -13.4, 0.9), ('olive1', -14.6, 16.6), ('pine1', nu1 + 1.4, nw1 - 1.0),
             ('cypress2', nu0 + 1.0, nw1 - 1.2), ('olive3', nu1 + 1.6, nw0 + 6.0)]
    for k, (pr, u, w) in enumerate(trees):
        o.prop(pr, u, -w, tree_h(pr), 53.0 * k, z=0.2, tag='tree%d' % k)
    for k, (pr, u, w) in enumerate((('bush0', -15.6, 6.0), ('bush1', -12.0, 17.8), ('bush2', nu1 - 0.6, nw0 + 1.0), ('bush3', nu0 + 0.8, nw0 + 9.0),
                                    ('bush1', nu0 + 18.0, nw1 - 1.4), ('bush0', 44.8, 17.4))):
        o.prop(pr, u, -w, tree_h(pr), 47.0 * k, z=0.2, tag='green%02d' % k)


# ═══ 21:57 사용자: 막센티우스 바실리카 Core를 레퍼런스(user_maxentius)대로 새로 짓는다(옛 측랑·신랑 유적 모형은 MAX_V2 = False로 보관) ═══
# 앞(평면 +Y = 카메라 쪽 왼쪽 아래): 키 큰 정사각 벽돌 교각 위 큰 반원 아치 4개가 줄지은 깊은 아케이드(두께 6, 아치 속 따뜻한 그늘)
#   교각 머리 = 트래버틴 기둥머리(잎 장식 2단) + 처마돌, 아치 = 벽돌 켜 홍예 2겹 + 트래버틴 테, 위 = 처마 띠 + 무너진 들쭉날쭉한 윗변
# 뒤: 안뜰을 반원으로 두른 3층 아케이드(층마다 아치 줄 · 붙임기둥 · 층 띠, 맨 위 난간), 안뜰 판석 · 잔해
# 평면 축 정렬(사용자 18:06): 아케이드 축 = 평면 X, 반원 지름 = 아케이드 뒷면. 지역 (u, v) = 평면 (X, Y) → Blender (u, −v). 상자 맞춤은 fit_skz
MAX_V2 = True
MV = dict(W=64.0, YB=28.0, YF=34.0, H=18.0, NB=4, PW=3.0, ZS=9.5, RC=28.0, RT=4.0, TZ=(0.0, 6.0, 11.5, 16.0), NR=13)


def build_maxentius_v2(GC, LM7):
    o = Obj('Maxentius', GC)
    W, YB, YF, H, NB, PW, ZS = MV['W'], MV['YB'], MV['YF'], MV['H'], MV['NB'], MV['PW'], MV['ZS']
    span = (W - PW * (NB + 1)) / NB; RA = span / 2.0
    arches = [(PW + k * (span + PW), PW + k * (span + PW) + span) for k in range(NB)]
    piers = [(k * (span + PW), k * (span + PW) + PW) for k in range(NB + 1)]
    fmF = map_front(-YF)
    # ── L0 앞 아케이드 덩어리(큰 아치 4 관통) · 위 벽(attic)
    b = o.bm(0, 'Shell', 'max_brick', 'max_shade', 'brick_core')
    n0 = len(b.faces)
    G.wall_holes(b, 'X', 0.0, W, -YF, -YB, 0.0, H - 2.0, [('arch', a, c, 0.0, ZS) for a, c in arches], 0, 16)
    b.faces.ensure_lookup_table()
    for f in list(b.faces)[n0:]:
        f.normal_update()
        cen = f.calc_center_median()
        if -YF + 0.01 < cen.y < -YB - 0.01 and 0.01 < cen.x < W - 0.01 and abs(f.normal.z) < 0.99:
            f.material_index = 1                                                  # 아치 속(홍예 안쪽 면) 따뜻한 짙은 그늘
    fs = bx(b, 0.0, W, YB, YF, H - 2.0, H - 0.3, 0); fs[1].material_index = 2
    # ── L0·L1 안뜰 반원 3층 아케이드: 앞 벽(아치 구멍) + 그늘 띠 + 뒤 덩어리
    cx, cy = W / 2.0, -YB
    RC, RT, TZ, NR = MV['RC'], MV['RT'], MV['TZ'], MV['NR']
    Rf = RC - RT
    br = o.bm(0, 'Ring', 'max_brick', 'max_shade', 'brick_core')
    bd = o.bm(1, 'Depth', 'max_shade', 'max_shade2')

    def tier(k):
        z0, z1 = TZ[k], TZ[k + 1]
        def holes(i, L):
            c = L / 2.0
            w = min((1.5, 1.3, 0.9)[k], 0.34 * L)
            zb = z0 if k == 0 else z0 + 0.8
            zs = z1 - 1.0 - w
            return [('arch', c - w, c + w, zb, zs)]
        return z0, z1, holes
    for k in range(3):
        z0, z1, holes = tier(k)
        arc_wall(br, cx, cy, Rf, Rf + 0.8, 0.0, 180.0, z0, z1, NR, holes, 0, 1, 2)
        G.ring(bd, cx, cy, Rf + 0.8, Rf + 1.1, z0, z1 - 0.1, 60, k % 2, 0.0, 180.0)
    G.ring(br, cx, cy, Rf + 1.1, RC, 0.0, TZ[3], 60, 0, 0.0, 180.0)
    # ── L2 부재: 교각 받침·기둥머리·처마돌, 아치 트래버틴 테, 처마 띠 / 고리 층 띠·붙임기둥·맨 위 난간
    b2 = o.bm(2, 'Members', 'trav_f', 'marble', 'max_brick')
    for (p0, p1) in piers:
        uz_prism(b2, rect(p0 - 0.25, p1 + 0.25, 0.0, 0.8), fmF, 0.0, 0.3, 0)
        uz_prism(b2, rect(p0 - 0.15, p1 + 0.15, ZS - 1.7, ZS - 0.45), fmF, 0.0, 0.42, 0)
        uz_prism(b2, rect(p0 - 0.5, p1 + 0.5, ZS - 0.45, ZS), fmF, 0.0, 0.62, 1)
    for (a, c) in arches:
        arch_band(b2, fmF, (a + c) / 2.0, ZS, RA + 1.05, RA + 1.3, 0.0, 0.12, 0, 16)
    uz_prism(b2, rect(-0.2, W + 0.2, H - 2.0, H - 1.55), fmF, 0.0, 0.4, 0)
    fR = map_cyl(cx, cy, Rf, 0.0)
    Lb = math.pi * Rf / NR
    for k in range(3):
        z0, z1 = TZ[k], TZ[k + 1]
        G.ring(b2, cx, cy, Rf - 0.3, Rf + 0.1, z1 - 0.38, z1, 60, 0, 0.0, 180.0)
        for i in range(NR + 1):
            uz_prism(b2, rect(i * Lb - 0.22, i * Lb + 0.22, z0 + 0.25, z1 - 0.45), fR, -0.18, 0.0, 2)
    G.ring(b2, cx, cy, Rf - 0.05, Rf + 0.35, TZ[3], TZ[3] + 0.7, 60, 0, 0.0, 180.0)
    da = math.degrees(0.16 / Rf)
    for i in range(NR * 2 + 1):
        a_ = 180.0 * i / (NR * 2)
        G.ring(b2, cx, cy, Rf - 0.12, Rf + 0.42, TZ[3], TZ[3] + 1.0, 1, 1, max(0.0, a_ - da), min(180.0, a_ + da))
    # ── L3 벽돌 켜 홍예(2겹, 밝고 짙게 번갈아) · 안뜰·앞 판석
    bv = o.bm(3, 'Voussoirs', 'brick_hi', 'brick_dk')
    for (a, c) in arches:
        for row, (r0, r1) in enumerate(((RA + 0.02, RA + 0.52), (RA + 0.54, RA + 1.03))):
            nv = 15 + 2 * row
            for j in range(nv):
                g0 = 180.0 * j / nv + 0.5; g1 = 180.0 * (j + 1) / nv - 0.5
                arch_band(bv, fmF, (a + c) / 2.0, ZS, r0, r1, 0.0, 0.08, (j + row) % 2, 1, g0, g1)
    bp = o.bm(3, 'Paving', 'pave', 'cobble')
    G.prism(bp, [(cx + (Rf + 0.1) * math.cos(math.radians(a_)), cy + (Rf + 0.1) * math.sin(math.radians(a_))) for a_ in range(0, 181, 6)], 0.0, 0.15, 0)
    bx(bp, -2.0, W + 2.0, YF, YF + 4.0, 0.0, 0.15, 1)
    # ── L4 기둥머리 잎 장식 2단 · 무너진 윗변(아케이드·고리) · 안뜰 잔해
    bl = o.bm(4, 'Detail', 'trav_f', 'max_brick', 'brick_core', 'concrete')
    for (p0, p1) in piers:
        for zz in (ZS - 1.6, ZS - 1.12):
            for i in range(5):
                x = p0 - 0.1 + (p1 - p0 + 0.2) * (i + 0.5) / 5.0
                G.cyl(bl, x, -YF - 0.45, 0.17, zz, zz + 0.42, 5, 0, r_top=0.03, bottom=True)
    u = 0.0; k = 0
    while u < W - 0.5:
        w_ = 1.2 + 3.0 * R.hash01(k, 301); h_ = 0.3 + 1.5 * R.hash01(k, 302) ** 1.4
        for (v0, v1) in ((YF - 0.9, YF), (YB, YB + 0.9)):
            fs = bx(bl, u, min(W, u + w_), v0, v1, H - 0.3, H - 0.3 + h_ * (1.0 if v0 > YB + 1 else 0.7), 1); fs[1].material_index = 2
        u += w_ + 0.4 + 1.6 * R.hash01(k, 303); k += 1
    a_ = 2.0; k = 0
    while a_ < 176.0:
        w_ = 3.0 + 7.0 * R.hash01(k, 311); h_ = 0.25 + 1.0 * R.hash01(k, 312) ** 1.5
        G.ring(bl, cx, cy, Rf + 0.35, Rf + 1.4, TZ[3], TZ[3] + h_, 2, 1 + k % 2, a_, min(178.0, a_ + w_))
        a_ += w_ + 2.0 + 6.0 * R.hash01(k, 313); k += 1
    for j in range(40):
        rr = (Rf - 3.0) * math.sqrt(R.hash01(j, 321)); t_ = math.radians(180.0 * R.hash01(j, 322))
        x, y = cx + rr * math.cos(t_), cy + rr * math.sin(t_)
        w_ = 0.3 + 0.6 * R.hash01(j, 323)
        G.box(bl, x - w_, x + w_, y - w_ * 0.6, y + w_ * 0.6, 0.15, 0.15 + 0.2 + 0.4 * R.hash01(j, 324), (0, 3, 2)[j % 3])
    # ── L5 하이라이트: 처마돌·처마 띠·층 띠·난간 윗선
    b5 = o.bm(5, 'Highlights', 'hi', 'marble_hi')
    for (p0, p1) in piers:
        uz_prism(b5, rect(p0 - 0.5, p1 + 0.5, ZS - 0.04, ZS + 0.03), fmF, 0.0, 0.66, 1)
    uz_prism(b5, rect(-0.2, W + 0.2, H - 1.59, H - 1.52), fmF, 0.0, 0.44, 0)
    for k in range(3):
        G.ring(b5, cx, cy, Rf - 0.32, Rf - 0.22, TZ[k + 1] - 0.04, TZ[k + 1] + 0.03, 60, 0, 0.0, 180.0)
    G.ring(b5, cx, cy, Rf - 0.07, Rf + 0.05, TZ[3] + 0.7, TZ[3] + 0.74, 60, 1, 0.0, 180.0)
    # ── L6 2단 벽돌 얼룩 · 빗물 줄 · 틈 수풀 · 교각 밑 이끼
    b6 = o.bm(6, 'Weather', 'brick_hi', 'brick_dk', 'stain_dk', 'moss', 'grass2')
    for (p0, p1) in piers:
        for j in range(5):
            x = p0 + 0.2 + (p1 - p0 - 0.6) * R.hash01(int(p0 * 10), j, 331); z = 1.2 + (ZS - 3.2) * R.hash01(int(p0 * 10), j, 332)
            w_ = 0.3 + 0.4 * R.hash01(int(p0 * 10), j, 333); h_ = 0.3 + 0.6 * R.hash01(int(p0 * 10), j, 334)
            uz_prism(b6, [(x, z), (x + w_, z - 0.05), (x + w_ + 0.05, z + h_ * 0.6), (x + w_ * 0.4, z + h_), (x - 0.05, z + h_ * 0.5)], fmF, 0.0, 0.03, j % 2)
        L_ = 1.5 + 2.5 * R.hash01(int(p0 * 10), 335)
        uz_prism(b6, [(p0 + 0.6, ZS - 1.7 - L_), (p0 + 0.85, ZS - 1.7 - L_ * 0.8), (p0 + 0.85, ZS - 1.75), (p0 + 0.6, ZS - 1.75)], fmF, 0.0, 0.04, 2)
        uz_prism(b6, rect(p0 - 0.25, p1 + 0.25, 0.0, 0.35 + 0.3 * R.hash01(int(p0 * 10), 336)), fmF, 0.3, 0.33, 3)
    for j in range(16):
        x = 0.5 + (W - 1.0) * R.hash01(j, 341); z = H - 1.5 - 0.3 * R.hash01(j, 342)
        L_ = 1.0 + 2.5 * R.hash01(j, 343)
        uz_prism(b6, [(x, z - L_), (x + 0.3, z - L_ * 0.8), (x + 0.3, z), (x, z)], fmF, 0.0, 0.04, 2)
    pts = []
    for j in range(30):
        x = 0.5 + (W - 1.0) * R.hash01(j, 351); v = YB + 0.4 + (YF - YB - 0.8) * R.hash01(j, 352)
        pts.append((x, -v, 0.35 + 0.35 * R.hash01(j, 353), H - 0.3))
    for j in range(36):
        t_ = math.radians(4.0 + 172.0 * R.hash01(j, 354)); rr = Rf + 0.5 + 0.9 * R.hash01(j, 355)
        pts.append((cx + rr * math.cos(t_), cy + rr * math.sin(t_), 0.3 + 0.3 * R.hash01(j, 356), TZ[3] + 0.05))
    for j in range(24):
        t_ = math.radians(4.0 + 172.0 * R.hash01(j, 357)); k_ = 1 + j % 2
        rr = Rf + 0.25
        pts.append((cx + rr * math.cos(t_), cy + rr * math.sin(t_), 0.25 + 0.25 * R.hash01(j, 358), TZ[k_] + 0.02))
    tufts(b6, pts, [3, 4, 3], 21.0)
    # 콜로세움 잣대 보강: L3 교각·처마 벽돌 켜 선 · L4 안뜰 아치 홍예 처마 띠 · L6 안뜰 벽 2단 얼룩
    bc = o.bm(3, 'Courses', 'brick_dk')
    for (p0, p1) in piers:
        z = 1.2
        while z < ZS - 1.9:
            uz_prism(bc, rect(p0 + 0.05, p1 - 0.05, z, z + 0.07), fmF, 0.0, 0.025, 0)
            z += 0.7
    z = ZS + 0.3
    while z < H - 2.1:
        for (p0, p1) in piers:
            uz_prism(bc, rect(p0 - 0.3, p1 + 0.3, z, z + 0.07), fmF, 0.0, 0.025, 0)
        z += 0.7
    bh = o.bm(4, 'Hoods', 'brick_hi', 'trav_f')
    for k in range(3):
        z0, z1, holes = tier(k)
        for i in range(NR):
            for (_, u0, u1, zb, zs) in holes(i, Lb):
                arch_band(bh, fR, i * Lb + (u0 + u1) / 2.0, zs, (u1 - u0) / 2.0 + 0.03, (u1 - u0) / 2.0 + 0.24, -0.12, -0.005, k % 2, 6)
    for k in range(3):
        z0, z1 = TZ[k], TZ[k + 1]
        for i in range(NR):
            for j in range(2):
                u = i * Lb + (-0.55 + 1.1 * R.hash01(i, k, j, 361))                    # 칸 경계(교각) 띠 안에만(아치 구멍과 겹침 0)
                zc = z0 + 0.6 + (z1 - z0 - 1.4) * R.hash01(i, k, j, 362)
                w_ = 0.3 + 0.25 * R.hash01(i, k, j, 363); h_ = 0.3 + 0.4 * R.hash01(i, k, j, 364)
                uz_prism(b6, [(u - w_ / 2, zc - h_ / 2), (u + w_ / 2, zc - h_ / 2 - 0.05), (u + w_ / 2 + 0.05, zc + h_ * 0.2), (u, zc + h_ / 2), (u - w_ / 2 - 0.05, zc)],
                         fR, -0.045, -0.01, (i + j + k) % 2)
    o.done()
    return o


def maxentius_anchors(o, A):
    bvh = _bvh(o.root)
    out = {}
    inner = lambda n: any(s in n for s in ('Vaults', 'Coffers', 'Depth', 'Shell', 'Apse', 'Paving', 'Members', 'FrontArches', 'Ring', 'Voussoirs', 'Detail'))
    for role in ('L7_label', 'L7_m2'):
        if role in A:
            out[role] = put_anchor(o, role, A[role], inner, bvh=bvh)
    return out


# ═════════════════════════ 마르켈루스 극장(Theatrum Marcelli) ═════════════════════════
# spec L9 plan(평면 mm)을 그대로 짓는다: 지름(무대 쪽) 평면 X = c.X, 곡면(바깥 아케이드)은 +X(화면 오른쪽 아래), 반지름 r.
# 바깥 아케이드 2단(아래 도리스·위 이오니아 반기둥, 트래버틴) — 3단(추정)은 짓지 않는다. 관람석은 곡면에서 지름 쪽으로 내려간다.
# 무대 쪽 벽은 낮은 유적(높이 ≤ stage_wall.h_max). 지름 쪽 앞 끝 포장은 테베레 북쪽 둑(강 ↘ 팔 평면 Y − 반폭)에 닿는다(둑 경계석 앞).
# 곁에 아폴로 소시아누스 신전 기둥 3개. 루트 = 반원 중심, 지역 (u, w) = (X − cX, Y − cY) → Blender (u, −w). 평면 방위 θ ↔ Blender −θ.
MC_NB = 27


def _marcellus_plan(LM9, CM):
    pl = LM9['plan']
    p = pl['plan']; ar = pl['arcade']; sw = pl.get('stage_wall', {})
    cx, cy = p['c']; r = p['r']
    # 테베레 북쪽 둑(강 ↘ 팔 평면 Y = arm1 − 화면 수직 폭/2 ÷ cos30)
    riv = CM['river']
    m = re.search(r'Y\s*=\s*([\d.]+)', riv['plan']['arm1'])
    yc = float(m.group(1)) if m else 314.0
    wv = riv['width_screen_perp_mm'].get('↘ 팔', 16.0)
    bank = yc - wv / 2.0 / math.cos(math.radians(30.0))
    return dict(cx=cx, cy=cy, r=r, h=ar['h'], tiers=ar['tier_h'], hs=sw.get('h_max', 4.0), dY=p['diameter_Y'], bank=bank, wings=pl.get('side_wings'))


def build_marcellus(GC, LM9, CM):
    P_ = _marcellus_plan(LM9, CM)
    cx, cy, RO = P_['cx'], P_['cy'], P_['r']
    o = Obj('Marcellus', GC, mm=True, X=cx, Y=cy)
    place_plan(o.root, cx, cy)
    T1, T2 = P_['tiers'][0], P_['tiers'][0] + P_['tiers'][1]
    NB = MC_NB
    A0, A1 = 90.0, -90.0                         # Blender 방위(평면 θ −90 → +90)
    Lb = math.radians(180.0 / NB) * RO
    RW = RO - 1.1                                # 바깥벽 뒷면
    RA = RW - 1.5                                # 바깥 회랑 안쪽(안 고리 벽 바깥)
    RI = RA - 0.6                                # 안 고리 벽 안쪽 = 관람석 위 끝
    ROR = 0.27 * RO                              # 오케스트라 반지름
    HS = P_['hs']
    bank_gap = 0.85                              # 둑 경계석(땅 패키지, 둑선 안쪽 0.8) 앞에서 멈춘다
    w_front = (P_['bank'] - bank_gap) - cy        # 앞 포장 끝(지역 w)
    # ── L0 덩어리: 아케이드 2단(아치), 회랑 깊이색, 안 고리 벽
    b = o.bm(0, 'Arcade', 'trav', 'shade')
    def t1(k, L):
        return [('arch', 0.85, L - 0.85, 0.0, T1 * 0.55)]
    def t2(k, L):
        return [('arch', 0.95, L - 0.95, T1 + 0.9, T1 + T2 * 0.0 + (T2 - T1) * 0.53)]
    arc_wall(b, 0, 0, RO, RW, A0, A1, 0.0, T1, NB, t1, 0, 1, 0)
    arc_wall(b, 0, 0, RO - 0.15, RW, A0, A1, T1, T2, NB, t2, 0, 1, 0)
    b = o.bm(0, 'InnerRing', 'concrete', 'trav')
    G.ring(b, 0, 0, RI, RA, 0.0, T2 - 0.4, 72, 0, -90.0, 90.0)
    # ── L0·L3 관람석(카베아): 두 마이아눔 + 가로 통로, 계단석 돌 무늬
    b = o.bm(0, 'Seats', 'seat', 'seat_lt')
    r_p0, r_p1 = ROR + 0.48 * (RI - ROR), ROR + 0.53 * (RI - ROR)
    z_low, z_mid, z_top = 0.55, 0.5 * (T2 - 0.6), T2 - 0.75
    ruin = (58.0, 80.0)                                                                  # Blender 방위: 위 관람석이 무너진 구간(뒤-오른쪽)
    n1 = 11; n2 = 11
    rows = []
    for i in range(n1):
        r0 = ROR + (r_p0 - ROR) * i / n1; r1 = ROR + (r_p0 - ROR) * (i + 1) / n1
        rows.append((r0, r1, z_low + (z_mid - z_low) * (i + 1) / n1, i))
    rows.append((r_p0, r_p1, z_mid, n1))                                                 # 가로 통로(프라이킨크티오)
    for i in range(n2):
        r0 = r_p1 + (RI - r_p1) * i / n2; r1 = r_p1 + (RI - r_p1) * (i + 1) / n2
        rows.append((r0, min(r1 + 0.05, RI + 0.05), z_mid + (z_top - z_mid) * (i + 1) / n2, n1 + 1 + i))
    for r0, r1, z1, i in rows:
        mi = 0 if i % 2 else 1
        if i > n1:
            G.ring(b, 0, 0, r0, r1, 0.0, z1, 40, mi, -90.0, ruin[0])
            G.ring(b, 0, 0, r0, r1, 0.0, z1, 8, mi, ruin[1], 90.0)
            G.ring(b, 0, 0, r0, r1, 0.0, z_mid + 0.05, 6, 1, ruin[0], ruin[1])           # 무너진 구간: 통로 높이 아래 덩어리만
        else:
            G.ring(b, 0, 0, r0, r1, 0.0, z1, 56, mi, -90.0, 90.0)
    # ── L4 무너진 위 관람석 밑 콘크리트 방사 벽·복도 볼트 토막(콘크리트 이야기)
    b = o.bm(4, 'Radial', 'concrete', 'brick_core')
    for k in range(6):
        a = math.radians(ruin[0] + 1.6 + (ruin[1] - ruin[0] - 3.2) * k / 5)
        en = (-math.sin(a), math.cos(a), 0.0)
        fmap = plane_map((r_p1 * math.cos(a), r_p1 * math.sin(a), 0.0), (math.cos(a), math.sin(a), 0.0), (0, 0, 1), en)
        z_in = z_mid + 0.4 - 0.5 * R.hash01(k, 42)
        z_out = z_top - 0.4 - 1.6 * R.hash01(k, 43)
        uz_prism(b, [(0.0, 0.0), (RI - r_p1, 0.0), (RI - r_p1, z_out), (0.0, z_in)], fmap, -0.22, 0.22, 0, True)
        uz_prism(b, [(0.1, z_in - 0.15), (RI - r_p1 - 0.1, z_out - 0.15), (RI - r_p1 - 0.1, z_out + 0.05), (0.1, z_in + 0.05)], fmap, -0.24, 0.24, 1)
    for k in range(5):
        a0 = ruin[0] + 1.6 + (ruin[1] - ruin[0] - 3.2) * k / 5 + 0.4; a1 = a0 + (ruin[1] - ruin[0] - 3.2) / 5 - 0.8
        G.ring(b, 0, 0, RI - 2.4, RI, z_top - 2.4 + 0.8 * R.hash01(k, 44), z_top - 1.6, 4, 0, a0, a1)
    b = o.bm(4, 'RadialStairs', 'marble_hi', 'trav_f')
    for a_st in (-62.0, -34.0, -6.0, 22.0, 46.0, 84.0):                                   # Blender 방위(무너진 구간 밖): 줄마다 반 단 계단
        for idx, (r0, r1, z1, i) in enumerate(rows):
            if i == n1 or idx == len(rows) - 1:
                continue
            if i > n1 and ruin[0] - 1.0 < a_st < ruin[1] + 1.0:
                continue
            z_next = rows[idx + 1][2]
            G.ring(b, 0, 0, r0 - 0.01, r1 + 0.01, z1, z1 + 0.06, 2, 0, a_st - 0.85, a_st + 0.85)
            G.ring(b, 0, 0, (r0 + r1) / 2, r1 + 0.01, z1 + 0.06, z1 + 0.5 * (z_next - z1) + 0.06, 2, 1, a_st - 0.85, a_st + 0.85)
    # ── L1 깊이색: 바깥 회랑 속(아치 너머)·통로 입구(보미토리움)
    b = o.bm(1, 'Depth', 'deep', 'deeper')
    G.ring(b, 0, 0, RA, RW, 0.0, T1 - 0.4, 72, 0, -90.0, 90.0)
    G.ring(b, 0, 0, RA, RW, T1, T2 - 0.45, 72, 1, -90.0, 90.0)
    for k in range(7):
        a = -78.0 + 26.0 * k
        if ruin[0] - 2 < a < ruin[1] + 2:
            continue
        uz_prism(b, arch_loop(-0.45, 0.45, z_mid, z_mid + 0.9), map_cyl(0, 0, r_p1 - 0.02, a), -0.04, 0.0, 1)
    # ── L2 부재: 반기둥(아래 도리스·위 이오니아)·엔타블러처·코니스·맨 위 통로·회랑 바닥
    b = o.bm(2, 'Orders', 'trav_f', 'marble', 'brick_core')
    fmo = map_cyl(0, 0, RO, -90.0)
    for k in range(NB + 1):
        u = k * Lb
        uz_prism(b, rect(u - 0.3, u + 0.3, 0.15, T1 - 1.05), fmo, 0.0, 0.3, 0)        # 도리스 반기둥
        uz_prism(b, rect(u - 0.42, u + 0.42, T1 - 1.05, T1 - 0.85), fmo, 0.0, 0.42, 0)
        uz_prism(b, rect(u - 0.42, u + 0.42, 0.0, 0.2), fmo, 0.0, 0.42, 0)
        uz_prism(b, rect(u - 0.27, u + 0.27, T1 + 0.25, T2 - 1.0), fmo, 0.0, 0.26, 0)  # 이오니아 반기둥
        uz_prism(b, rect(u - 0.48, u + 0.48, T2 - 1.0, T2 - 0.82), fmo, 0.0, 0.36, 0)  # 소용돌이 주두
        uz_prism(b, rect(u - 0.36, u + 0.36, T1 + 0.05, T1 + 0.25), fmo, 0.0, 0.34, 0)
    G.ring(b, 0, 0, RO - 0.2, RO + 0.42, T1 - 0.85, T1 - 0.2, 72, 0, -90.0, 90.0)        # 도리스 엔타블러처(아키트레이브·프리즈)
    G.ring(b, 0, 0, RO - 0.2, RO + 0.6, T1 - 0.2, T1 + 0.05, 72, 0, -90.0, 90.0)          # 코니스
    G.ring(b, 0, 0, RO - 0.3, RO + 0.36, T2 - 0.82, T2 - 0.25, 72, 0, -90.0, 90.0)
    G.ring(b, 0, 0, RO - 0.3, RO + 0.5, T2 - 0.25, T2, 72, 0, -90.0, 90.0)
    G.ring(b, 0, 0, RA - 0.05, RO - 0.25, T2 - 0.45, T2 - 0.05, 72, 1, -90.0, 90.0)        # 맨 위 통로(회랑 지붕)
    G.ring(b, 0, 0, RA, RW, T1 - 0.4, T1, 72, 2, -90.0, 90.0)                              # 위층 회랑 바닥
    for k in range(NB):                                                                     # 아치 받침 띠(임포스트)
        u0 = k * Lb
        uz_prism(b, rect(u0 + 0.75, u0 + 0.92, T1 * 0.55 - 0.15, T1 * 0.55), fmo, 0.0, 0.12, 0)
        uz_prism(b, rect(u0 + Lb - 0.92, u0 + Lb - 0.75, T1 * 0.55 - 0.15, T1 * 0.55), fmo, 0.0, 0.12, 0)
    # 16:25 레퍼런스(user_marcellus): 맨 위 다락층(막힌 벽 + 코린트 벽기둥 + 작은 창). 화면 앞·왼쪽 구간(방위 −90°~+30°)만, 끝 3칸은 무너진 계단꼴
    #   (뒤 끝은 그대로 2단이라 상자 위 변이 바뀌지 않는다)
    H3 = 0.42 * (T2 - T1); T3 = T2 + H3
    ba = o.bm(0, 'Attic', 'trav')
    bo = o.bm(2, 'AtticOrders', 'trav_f', 'marble')
    bw_ = o.bm(1, 'AtticWindows', 'deeper')
    nb3 = int(NB * 120.0 / 180.0)
    for k in range(nb3):
        a0_, a1_ = -90.0 + 180.0 * k / NB, -90.0 + 180.0 * (k + 1) / NB
        zt = T3 if k < nb3 - 3 else T2 + H3 * (0.7, 0.45, 0.2)[k - (nb3 - 3)]
        G.ring(ba, 0, 0, RO - 0.15, RW, T2, zt, 3, 0, a0_, a1_)
        u = k * Lb
        if zt >= T3 - 1e-6:
            uz_prism(bo, rect(u - 0.24, u + 0.24, T2 + 0.15, T3 - 0.55), fmo, 0.0, 0.22, 0)          # 코린트 벽기둥
            uz_prism(bo, rect(u - 0.36, u + 0.36, T3 - 0.55, T3 - 0.35), fmo, 0.0, 0.3, 0)          # 주두
            uz_prism(bw_, rect(u + 0.36 * Lb, u + 0.64 * Lb, T2 + 0.7, T2 + 0.7 + 0.32 * H3), fmo, 0.0, 0.03, 0)   # 작은 창
    G.ring(bo, 0, 0, RO - 0.3, RO + 0.4, T3 - 0.35, T3, 60, 1, -90.0, -90.0 + 180.0 * (nb3 - 3) / NB)       # 다락 코니스
    b5a = o.bm(5, 'AtticLight', 'marble_hi')
    G.ring(b5a, 0, 0, RO + 0.1, RO + 0.4, T3, T3 + 0.04, 60, 0, -90.0, -90.0 + 180.0 * (nb3 - 3) / NB)
    # 설계 d5 ④: 지름 양 끝 곁채(베르수라) — spec L9 plan.side_wings(평면 X·Y 범위, 높이). 트래버틴 덩어리 + 아치 문 + 코니스 + 창
    wg = P_.get('wings')
    if wg:
        u0w, u1w = wg['X'][0] - cx, wg['X'][1] - cx; hw_ = float(wg.get('h', 8.0))
        bw0 = o.bm(0, 'Wings', 'trav', 'concrete')
        bw1 = o.bm(1, 'WingDoors', 'deep', 'deeper')
        bw2 = o.bm(2, 'WingCornice', 'trav_f', 'marble')
        bw4 = o.bm(4, 'WingWindows', 'deeper', 'trav_f')
        bw5 = o.bm(5, 'WingLight', 'marble_hi')
        bw6 = o.bm(6, 'WingStains', 'stain', 'moss')
        for key in ('wing_Y_minus', 'wing_Y_plus'):
            w0, w1 = wg[key][0] - cy, wg[key][1] - cy
            G.box(bw0, u0w, u1w, -w1, -w0, 0.0, hw_ - 0.6, 0)                                        # 몸
            G.box(bw2, u0w - 0.25, u1w + 0.25, -w1 - 0.25, -w0 + 0.25, hw_ - 0.6, hw_ - 0.2, 0)       # 코니스
            G.box(bw2, u0w - 0.1, u1w + 0.1, -w1 - 0.1, -w0 + 0.1, hw_ - 0.2, hw_, 1)                 # 갓돌
            G.box(bw5, u1w - 0.05, u1w + 0.27, -w1 - 0.25, -w0 + 0.25, hw_, hw_ + 0.04, 0)            # 윗선(오른면 쪽)
            G.box(bw5, u0w - 0.25, u1w + 0.25, -w1 - 0.27, -w1 + 0.05, hw_, hw_ + 0.04, 0)            # 윗선(왼면 쪽)
            wm = (w0 + w1) / 2.0
            for k_, wc in enumerate((wm - 2.0, wm + 2.0)):                                            # +X 면(곡면 쪽) 아치 문 2 · 위 네모 창
                uz_prism(bw1, arch_loop(-wc - 0.8, -wc + 0.8, 0.0, 2.6), map_right(u1w), 0.0, 0.04, 0)
                uz_prism(bw4, rect(-wc - 0.45, -wc + 0.45, 4.4, 5.6), map_right(u1w), 0.0, 0.05, 0)
                uz_prism(bw4, rect(-wc - 0.6, -wc + 0.6, 4.2, 4.4), map_right(u1w), 0.0, 0.12, 1)
            for k_, uc in enumerate(((u0w + u1w) / 2.0,)):                                             # +Y 면(앞) 아치 문
                uz_prism(bw1, arch_loop(uc - 0.7, uc + 0.7, 0.0, 2.4), map_front(-w1), 0.0, 0.04, 1)
            G.box(bw6, u1w + 0.01, u1w + 0.05, -wm - 0.3, -wm + 0.3, 1.0, hw_ - 0.8, 0)              # 빗물 자국
            G.box(bw6, u0w, u1w, -w1 - 0.06, -w1 + 0.4, 0.0, 0.25, 1)                                # 밑동 이끼
    # 오케스트라 앞 귀빈석(프로헤드리아) 2단
    G.ring(b, 0, 0, ROR - 1.4, ROR - 0.7, 0.2, 0.55, 40, 1, -90.0, 90.0)
    G.ring(b, 0, 0, ROR - 0.7, ROR + 0.02, 0.2, 0.75, 40, 1, -90.0, 90.0)
    # ══ 18:25 콜로세움 잣대 고도화(레퍼런스 user_marcellus 입면): 홍예돌·쐐기돌 · 위층 임포스트 · 트래버틴 켜 선 · 꺾쇠 구멍 · 2단 얼룩 · 좌석 앞선 ══
    vis_k = [k for k in range(NB) if -90.0 + 180.0 * (k + 0.5) / NB < 50.0]          # 카메라에 보이는 바깥 칸(Blender 방위 −90° ~ +50°)
    r1a, vs1 = (Lb - 1.7) / 2, T1 * 0.55
    r2a, vs2 = (Lb - 1.9) / 2, T1 + (T2 - T1) * 0.53
    bv = o.bm(3, 'Voussoirs', 'trav_f', 'marble', 'trav')
    for k in vis_k:
        cu = k * Lb + Lb / 2
        for (ra, vs_, dr) in ((r1a, vs1, 0.42), (r2a, vs2, 0.38)):
            nv = 9
            for j in range(nv):
                key_ = j == nv // 2
                a0 = 180.0 * j / nv + 1.2; a1 = 180.0 * (j + 1) / nv - 1.2
                arch_band(bv, fmo, cu, vs_, ra, ra + dr + (0.16 if key_ else 0.0), 0.0, 0.11 if key_ else 0.07, 1 if key_ else (0 if j % 2 else 2), 1, a0, a1)
    bim = o.bm(2, 'Imposts2', 'trav_f')
    for k in vis_k:
        u0 = k * Lb
        uz_prism(bim, rect(u0 + 0.78, u0 + 0.95, vs2 - 0.14, vs2), fmo, 0.0, 0.11, 0)
        uz_prism(bim, rect(u0 + Lb - 0.95, u0 + Lb - 0.78, vs2 - 0.14, vs2), fmo, 0.0, 0.11, 0)
    bjn = o.bm(3, 'Joints', 'mc_joint')                                                    # 트래버틴 켜 선(아치 사이 교각 면)
    for k in vis_k + [max(vis_k) + 1]:
        u = k * Lb
        for (z0, z1, hw) in ((0.25, T1 - 0.9, 0.85), (T1 + 0.3, T2 - 1.05, 0.95)):
            z = z0 + 0.5
            while z < z1:
                for (ua, ub) in ((u - hw, u - 0.31), (u + 0.31, u + hw)):
                    if 0.0 <= ua and ub <= NB * Lb:
                        uz_prism(bjn, rect(ua, ub, z, z + 0.05), fmo, 0.0, 0.02, 0)
                z += 0.55
    def in_arch(ul, z, ra, base, vs_):
        d_ = ul - Lb / 2
        return abs(d_) < ra + 0.08 and base - 0.05 < z < vs_ + math.sqrt(max(0.0, (ra + 0.08) ** 2 - d_ * d_))
    umax = (max(vis_k) + 1) * Lb
    bch = o.bm(4, 'CrampHoles', 'deep', 'shade')                                           # 꺾쇠를 뽑아 간 구멍(콜로세움과 같은 풍화 표지)
    n_ok = j = 0
    while n_ok < 320 and j < 4000:
        u = umax * R.hash01(j, 141); z = 0.3 + (T2 - 0.5) * R.hash01(j, 142); j += 1
        ul = u % Lb
        if ul < 0.34 or ul > Lb - 0.34 or in_arch(ul, z, r1a, 0.0, vs1) or in_arch(ul, z, r2a, T1 + 0.9, vs2):
            continue
        if T1 - 0.9 < z < T1 + 0.3 or z > T2 - 1.05:
            continue
        w_ = 0.07 + 0.06 * R.hash01(j, 143)
        uz_prism(bch, rect(u - w_, u + w_, z - w_ * 1.2, z + w_ * 1.2), fmo, 0.0, 0.03, j % 2)
        n_ok += 1
    bpm = o.bm(6, 'Patches', 'mc_lt', 'mc_dk', 'stain')                                     # 밝은·짙은 트래버틴 2단 얼룩
    n_ok = j = 0
    while n_ok < 120 and j < 3000:
        u = umax * R.hash01(j, 151); z = 0.3 + (T2 - 0.6) * R.hash01(j, 152); j += 1
        w = 0.25 + 0.5 * R.hash01(j, 153); h = 0.25 + 0.6 * R.hash01(j, 154)
        ul = u % Lb
        if any(in_arch(ul + du, z + dz, r1a, 0.0, vs1) or in_arch(ul + du, z + dz, r2a, T1 + 0.9, vs2) for du in (-w / 2, w / 2) for dz in (-h / 2, h / 2)):
            continue
        if (T1 - 0.9 < z + h / 2 and z - h / 2 < T1 + 0.3) or z + h / 2 > T2 - 1.05:
            continue
        pts = [(u - w / 2, z - h / 2), (u + w * 0.3, z - h / 2 - 0.05), (u + w / 2, z), (u + w * 0.2, z + h / 2), (u - w * 0.35, z + h / 2 + 0.04), (u - w / 2 - 0.04, z + 0.05)]
        uz_prism(bpm, pts, fmo, 0.0, 0.025, (0, 1, 1, 2)[n_ok % 4])
        n_ok += 1
    bse = o.bm(5, 'SeatEdges', 'marble_hi')                                                # 줄마다 좌석 앞선(전엔 세 줄에 하나)
    for idx, (r0, r1, z1, i) in enumerate(rows):
        if idx % 3 == 0:
            continue
        G.ring(bse, 0, 0, r0 - 0.01, r0 + 0.08, z1 - 0.02, z1 + 0.04, 40, 0, -90.0, ruin[0] if i > n1 else 90.0)
    # ── L3 표면 무늬: 프리즈 트리글리프, 오케스트라 대리석 판, 무대 널, 앞 포장(둑까지)
    b = o.bm(3, 'Triglyphs', 'shade')
    for k in range(NB * 3):
        u = (k + 0.5) * Lb / 3
        uz_prism(b, rect(u - 0.16, u + 0.16, T1 - 0.7, T1 - 0.32), fmo, 0.42, 0.47, 0)
    b = o.bm(3, 'Floors', 'marble_fl', 'planks', 'pave')
    orch = [(0.06, -(ROR - 1.4))] + [((ROR - 1.4) * math.cos(math.radians(a)), (ROR - 1.4) * math.sin(math.radians(a))) for a in range(-90, 91, 6)] + [(0.06, ROR - 1.4)]
    orch = [(max(0.06, x), y) for x, y in orch]
    G.prism(b, _dedup(orch), 0.0, 0.22, 0)
    SW = 2.6                                                                                  # 무대(풀피툼) 폭
    wst = min(P_['dY'][1] - cy, RO) - 1.2
    bx(b, -SW, -0.03, -wst, wst - 1.2, 0.0, 1.15, 1)
    apr = [(-1.6, w_front - 4.0), (-1.6, w_front), (12.0, w_front), (12.0, w_front - 4.6)]
    if w_front < RO + 6.0:                                                                  # 20:01 d5: 강이 멀면(둑이 지름 끝보다 6 넘게 바깥) 둑까지 앞 포장 0
        G.prism(b, [(x, -y) for x, y in apr], 0.0, 0.2, 2)
    # ── L0 무대 뒷벽(스카이나이 프론스) 낮은 유적 + 문 3개(L1) + 앞 기둥 토막(L2)
    b = o.bm(0, 'StageWall', 'brick', 'brick_core')
    segs = []
    nsg = 9
    for k in range(nsg):
        w0 = -wst + 0.6 + (2 * wst - 2.4) * k / nsg; w1 = -wst + 0.6 + (2 * wst - 2.4) * (k + 1) / nsg
        zt = 1.6 + (HS - 1.9) * R.hash01(k, 41)
        segs.append((w0, w1, zt))
        fs = bx(b, -SW - 1.1, -SW, w0 + 0.03, w1 - 0.03, 0.0, zt, 0); fs[1].material_index = 1
    b = o.bm(1, 'StageDoors', 'deeper')
    for wc, ww in ((-wst * 0.5, 1.2), (0.0, 1.6), (wst * 0.5, 1.2)):
        zt = min([zt for w0, w1, zt in segs if w0 <= wc + ww / 2 + 0.01 and w1 >= wc - ww / 2 - 0.01] + [HS])
        uz_prism(b, rect(-wc - ww / 2, -wc + ww / 2, 1.15, min(1.15 + 2.0, zt - 0.4)), map_right(-SW), 0.0, 0.05, 0)
    b = o.bm(2, 'StageColumns', 'marble', 'gran_r')
    for k in range(9):
        wc = -wst + 2.0 + (2 * wst - 4.0) * k / 8
        G.cyl(b, -SW + 0.45, -wc, 0.24, 1.15, 1.15 + 0.6 + 1.6 * R.hash01(k, 45), 10, k % 2, bottom=True)
    # 무대 앞벽 벽감(L4)
    b = o.bm(4, 'Ruins', 'deep', 'trav', 'brick_core')
    for k in range(8):
        wc = -wst + 2.5 + (2 * wst - 5.0) * k / 7
        lp = arch_loop(-wc - 0.35, -wc + 0.35, 0.25, 0.7) if k % 2 else rect(-wc - 0.4, -wc + 0.4, 0.25, 0.85)
        uz_prism(b, lp, map_right(-0.03), 0.0, 0.04, 0)
    for k in range(16):                                                                      # 잔해 블록(무너진 구간·무대 둘레)
        if k < 10:
            a = math.radians(ruin[0] + (ruin[1] - ruin[0]) * R.hash01(k, 47)); rr = r_p1 + 0.6 + (RI - r_p1 - 1.2) * R.hash01(k, 48)
            x, y, z0 = rr * math.cos(a), rr * math.sin(a), z_mid + 0.05
        else:
            x, y, z0 = -SW - 0.5 + 1.2 * R.hash01(k, 49), -(-wst + 2 * wst * R.hash01(k, 50)), 0.0
        w_ = 0.35 + 0.5 * R.hash01(k, 51)
        G.box(b, x - w_ / 2, x + w_ / 2, y - w_ * 0.4, y + w_ * 0.4, z0, z0 + 0.25 + 0.45 * R.hash01(k, 52), 1 + k % 2)
    # 아폴로 소시아누스 신전(극장 뒤 끝 곁): 기단 유적 + 기둥 3개 + 엔타블러처 토막
    b = o.bm(2, 'ApolloColumns', 'marble', 'trav_f')
    ap_w = -(P_['dY'][1] - P_['dY'][0]) / 2 + 9.5                                            # 지름 뒤 끝에서 9.5 앞
    for uu in (-10.2, -8.6, -7.0):
        column(b, b, uu, -ap_w, 1.7, 8.2, 0.42, 12, 0, 1)
    G.box(b, -10.75, -6.45, -(ap_w + 0.55), -(ap_w - 0.55), 9.9, 10.6, 0)
    b = o.bm(0, 'ApolloPodium', 'brick_core', 'trav')
    fs = bx(b, -11.6, -4.2, ap_w - 10.5, ap_w + 0.9, 0.0, 1.7, 0); fs[1].material_index = 1
    for k in range(4):
        bx(b, -11.6 + 1.8 * k, -11.6 + 1.8 * k + 1.5, ap_w + 0.9, ap_w + 2.1 - 0.25 * k, 0.0, 1.2 - 0.25 * k, 1)
    # ── L5 하이라이트: 코니스 윗선·통로 가장자리·반기둥 밝은 띠·좌석 앞 모서리
    b = o.bm(5, 'Highlights', 'hi', 'marble_hi')
    G.ring(b, 0, 0, RO + 0.48, RO + 0.6, T1 - 0.08, T1 + 0.1, 72, 0, -90.0, 90.0)
    G.ring(b, 0, 0, RO + 0.38, RO + 0.5, T2 - 0.1, T2 + 0.05, 72, 0, -90.0, 90.0)
    G.ring(b, 0, 0, RA - 0.05, RA + 0.1, T2 - 0.06, T2 - 0.03, 72, 1, -90.0, 90.0)
    for k in range(NB + 1):
        u = k * Lb
        uz_prism(b, rect(u - 0.3, u - 0.18, 0.4, T1 - 1.15), fmo, 0.3, 0.33, 1)
    for r0, r1, z1, i in rows[::3]:
        G.ring(b, 0, 0, r0 - 0.01, r0 + 0.1, z1 - 0.02, z1 + 0.05, 40, 1, -90.0, ruin[0] if i > n1 else 90.0)
    # ── L6 얼룩·식생·생활: 빗물 자국, 관람석 풀, 둘레 덤불
    b = o.bm(6, 'Stains', 'stain', 'moss')
    for k in range(NB):
        u = (k + 0.15 + 0.7 * R.hash01(k, 53)) * Lb
        L = 0.9 + 1.6 * R.hash01(k, 54)
        uz_prism(b, [(u - 0.22, T1 - 0.9 - L), (u + 0.22, T1 - 0.9 - L * 0.7), (u + 0.22, T1 - 0.9), (u - 0.22, T1 - 0.9)], fmo, 0.02, 0.05, 0)
        if R.hash01(k, 55) > 0.55:
            uz_prism(b, rect(u - 0.7, u + 0.7, 0.0, 0.35 + 0.35 * R.hash01(k, 56)), fmo, 0.02, 0.06, 1)
    b = o.bm(6, 'Grass', 'grass1', 'grass2', 'grass3')
    pts = []
    for k in range(40):
        a = math.radians(-88.0 + 176.0 * R.hash01(k, 57)); rr = ROR + 0.5 + (RI - ROR - 1.0) * R.hash01(k, 58)
        zz = 0.0
        for r0, r1, z1, i in rows:
            if r0 <= rr < r1:
                zz = z1 if not (i > n1 and ruin[0] <= math.degrees(a) <= ruin[1]) else z_mid + 0.05
        pts.append((rr * math.cos(a), rr * math.sin(a), 0.22 + 0.2 * R.hash01(k, 59), zz))
    for k in range(10):
        a = math.radians(ruin[0] + (ruin[1] - ruin[0]) * R.hash01(k, 60)); rr = r_p1 + 0.5 + (RI - r_p1 - 1.0) * R.hash01(k, 61)
        pts.append((rr * math.cos(a), rr * math.sin(a), 0.35 + 0.3 * R.hash01(k, 62), z_mid + 0.05))
    for k in range(14):
        t_ = -80.0 + 165.0 * R.hash01(k, 63)
        if -60.0 < t_ < -30.0 or 30.0 < t_ < 60.0:                                     # 화면 맨 아래·맨 오른쪽(평면 θ ±45°) 둘레는 비운다(상자 변·바지선 라벨)
            continue
        a = math.radians(t_); rr = RO + 0.7 + 0.4 * R.hash01(k, 64)
        pts.append((rr * math.cos(a), rr * math.sin(a), 0.35 + 0.25 * R.hash01(k, 65), 0.0))
    tufts(b, pts, [0, 1, 2], 13.0)
    # 판테온 광장 앞-왼쪽 변(평면 Y ≈ 253.85)과 무대 사이 정원: 지시선(평면 Y 273.3 선) 뒤쪽만 쓴다. 지역 (u, w)
    bgd = o.bm(3, 'GardenGrass', 'grass1', 'grass2', 'grass3')
    for k, (u, w, rx, ry) in enumerate(GARDEN_PATCHES if DECOR else ()):                  # 16:14: 극장과 판테온 사이 꾸미기 정원 0
        soil_patch(bgd, u, -w, rx, ry, 0.0, 9, k % 3, 3.7 * k)
    bgw = o.bm(2, 'GardenWall', 'brick', 'brick_hi')
    for (u0, u1) in ((-31.0, -22.0), (-20.0, -12.0), (-10.0, -4.0)) if DECOR else ():      # 라벨 글 블록(화면 x ≤ 30)과 1.5mm 이상(16:14 정원 담 0)
        bx(bgw, u0, u1, 6.2, 6.7, 0.0, 0.55, 0)
        bx(bgw, u0, u1, 6.15, 6.75, 0.55, 0.62, 1)
    o.done()
    return o, P_


GARDEN_PATCHES = [(-36.0, -6.0, 3.2, 2.2), (-27.0, -3.0, 3.6, 2.4), (-18.0, -4.5, 3.0, 2.0), (-31.0, 2.6, 2.6, 1.8), (-12.0, 1.0, 2.8, 2.0),
                  (-42.0, -9.0, 2.4, 1.6)]


def marcellus_life(o, P_):
    ensure_protos()
    RO = P_['r']
    w_front = (P_['bank'] - 0.85) - P_['cy']
    ppl = [(3.0, -2.0), (4.2, -1.2), (6.0, 4.0), (-1.4, -8.0), (-1.4, 9.0), (4.0, w_front - 0.55), (7.0, w_front - 0.45), (10.0, w_front - 0.75)]
    for k, (u, w) in enumerate(ppl):
        zz = 1.15 if u < 0 else (0.2 if w > P_['r'] - 1.0 else 0.22)
        o.prop('person%d' % (k % 3), u, -w, H_PERSON, 360.0 * R.hash01(k, 66), z=zz, tag='person%02d' % k)
    ap_w = -(P_['dY'][1] - P_['dY'][0]) / 2 + 9.5
    trees = [('pine1', -13.6, ap_w + 3.0), ('cypress1', -13.0, ap_w - 1.5), ('cypress3', -11.6, ap_w - 3.3), ('pine2', -16.0, ap_w + 11.0),
             ('olive2', -14.0, ap_w + 17.5)]
    for k, (pr, u, w) in enumerate(trees):
        o.prop(pr, u, -w, tree_h(pr), 61.0 * k, z=0.0, tag='tree%d' % k)
    garden = [('pine0', -36.0, -6.8), ('pine3', -22.0, -2.8), ('cypress0', -28.0, 3.2), ('cypress2', -26.6, 1.9), ('cypress1', -12.0, 1.2),
              ('cypress3', -10.6, -0.2), ('olive1', -18.0, -6.2), ('olive3', -39.5, -6.0)]
    for k, (pr, u, w) in enumerate(garden):
        o.prop(pr, u, -w, tree_h(pr), 37.0 * k, z=0.0, tag='treeG%d' % k)
    for k, (u, w) in enumerate(((-33.0, -2.0), (-24.0, -6.4), (-15.0, -2.0), (-8.0, -4.0), (-38.5, -3.5), (-20.0, 4.6))):
        o.prop('bush%d' % (k % 4), u, -w, tree_h('bush0'), 23.0 * k, z=0.0, tag='greenG%d' % k)
    bp = [(RO + 1.2, 20.0), (RO + 1.2, 70.0), (RO + 1.2, -8.7), (RO + 1.4, 64.7)]
    bush = [('bush%d' % (k % 4), r * math.cos(math.radians(t)), r * math.sin(math.radians(t))) for k, (r, t) in enumerate(bp)]
    for k, (pr, u, w) in enumerate(bush + [('bush3', -5.0, ap_w - 1.5), ('bush1', -13.0, ap_w + 7.0)]):
        o.prop(pr, u, -w, tree_h(pr), 47.0 * k, z=0.0, tag='green%02d' % k)


def marcellus_anchors(o, A):
    bvh = _bvh(o.root)
    out = {}
    ok = lambda n: any(s in n for s in ('Orders', 'Arcade', 'Seats', 'InnerRing', 'Highlights', 'Grass', 'Stains'))
    if 'L9_label' in A:
        out['L9_label'] = put_anchor(o, 'L9_label', A['L9_label'], ok, bvh=bvh)
    return out


# ═════════════════════════ 사양 읽기 · 짓기 · 검사 ═════════════════════════
def load_spec():
    S = json.load(open(SPEC, encoding='utf-8'))
    return S, S['core_map']


def anchor_points(S, CM):
    """D11 앵커 잠정 점: d5의 blender_anchor 열쇠 → decisions 괄호 점 → spec target_pt·leaders·pair_marks → drawn.json 지시선 끝"""
    A = dict(ANCHOR_DECISION)
    slots = {s.get('landmark') or s['name']: s for s in CM['labels']['slots']}
    def slot_by(prefix):
        for s in CM['labels']['slots']:
            if s['name'].startswith(prefix):
                return s
        return None
    for role, pref in (('L1_label', '판테온'), ('L2_label', '트라야누스 시장'), ('L7_label', '막센티우스'), ('L9_label', '마르켈루스')):
        s = slot_by(pref)
        if s is None:
            continue
        if isinstance(s.get('blender_anchor'), (list, tuple)):       # d5: blender_anchor가 앵커 이름(문자열)이면 target_pt를 쓴다
            A[role] = tuple(s['blender_anchor'])
        elif isinstance(s.get('blender_anchor'), str) and s.get('target_pt'):   # d5 지정 점이 d4 결정 점보다 우선
            A[role] = tuple(s['target_pt'])
        elif role not in A and s.get('target_pt'):
            A[role] = tuple(s['target_pt'])
    for ld in S['detail']['leaders']:
        if '판테온' in ld['name']:
            ba = ld.get('blender_anchor')
            A['L1_c1'] = tuple(ba if isinstance(ba, (list, tuple)) else ld['pts'][0])
    for pm in S['pair_marks']['raw']:
        role = {2: 'L7_m2', 3: 'L2_m3', 4: 'L1_m4'}.get(pm['n'])
        if role and isinstance(pm.get('blender_anchor'), (list, tuple)):
            A[role] = tuple(pm['blender_anchor'])
        elif role and isinstance(pm.get('blender_anchor'), str) and pm.get('map_pt'):    # d5 지정 점 우선(시장 +10 이동 등)
            A[role] = tuple(pm['map_pt'])
        elif role and role not in A:
            A[role] = tuple(pm['map_pt'])
    if 'L2_label' not in A and os.path.exists(DRAWN):
        D = json.load(open(DRAWN, encoding='utf-8'))
        for l in D.get('labels', []):
            if l.get('name', '').startswith('트라야누스') and l.get('leader'):
                A['L2_label'] = tuple(l['leader']['pts'][-1])
    return A


def _clear_one(name):
    """한 건물의 루트·자식·앵커만 지운다(나눠 짓기)"""
    root = bpy.data.objects.get('%s_%s_root' % (PK, name))
    if root is None:
        return
    for ob in list(root.children_recursive) + [root]:
        me = ob.data if ob.type == 'MESH' else None
        bpy.data.objects.remove(ob, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)


MAX_SHRINK = 0.9964   # 1단계 요청: 바실리카 오른쪽 끝 ↔ 욕장 앞-왼쪽 벽 실루엣 간격 1.79 → 2.0 mm 이상(상자 왼쪽 아래 모서리 기준 균일 축소)


def shrink_about(root, sx, sy, s):
    """루트를 화면 점 (sx, sy)(땅 Z 0)를 고정점으로 균일 축척 s배(정사영이라 화면에서도 같은 비율)"""
    if abs(s - 1.0) < 1e-9:
        return
    X, Y = R.to_plan(sx, sy)
    A = R.P(X, Y, 0.0)
    root.location = A + (root.location - A) * s
    root.scale = root.scale * s
    bpy.context.view_layer.update()


def lot_z(S, lot_id):
    """d7 core_map.diorama.lots에서 건물 대지 높이(없으면 0)"""
    for lt in (S['core_map'].get('diorama') or {}).get('lots', []) or []:
        if lt.get('id') == lot_id:
            return float(lt.get('z') or 0.0)
    return 0.0


def build(only=None):
    """건물마다 따로 부를 수 있다(명령 하나 90초 이하): build(['Pantheon']) 등. only가 없으면 넷 다(컬렉션을 비우고)."""
    S, CM = load_spec()
    LM = {l['id']: l for l in CM['landmarks']}
    GC = R.coll(COLL, R.coll('ROMA_MAP'))
    names = only or ['Pantheon', 'TrajanMarket', 'Maxentius', 'Marcellus']
    if not only:
        R.clear_coll(COLL)
    else:
        for n in names:
            _clear_one(n)
            if n == 'Pantheon':
                _clear_one('Acropolis')
    mats()
    A = anchor_points(S, CM)
    out = {}
    for name in names:
        if name == 'Pantheon' and not PANTHEON:                               # 22:05 사용자: core의 판테온 → 아테네 아크로폴리스(같은 L1 자리)
            o = build_acropolis(GC)
            s, kz, bb = fit_skz(o.root, LM['L1']['projected_box'])
            if AK_DRAW:
                bb = ak_draw(o.root, *AK_DRAW)
            an = acropolis_anchors(o, A)
            out[name] = dict(id='L1', model='Acropolis', s=s, kz=kz, box=bb, spec_box=LM['L1']['projected_box'])
        elif name == 'Pantheon':
            o = build_pantheon(GC, LM['L1']['projected_box'])
            s, kz, bb = fit_skz(o.root, LM['L1']['projected_box'])
            if DECOR:
                pantheon_life(o)
            s, kz, bb = fit_skz(o.root, LM['L1']['projected_box']); o.refresh_props()
            an = pantheon_anchors(o, A)
            out[name] = dict(id='L1', s=s, kz=kz, box=bb, spec_box=LM['L1']['projected_box'])
        elif name == 'TrajanMarket':
            o = build_market(GC, LM['L2']['projected_box'])
            o.root.location.z = lot_z(S, 'market')                         # d7: 계단식 벽돌 옹벽 대지 위(z 8)
            s, kz, bb = fit_skz(o.root, LM['L2']['projected_box'])
            if DECOR:
                market_life(o)
            s, kz, bb = fit_skz(o.root, LM['L2']['projected_box']); o.refresh_props()
            an = market_anchors(o, A)
            out[name] = dict(id='L2', s=s, kz=kz, box=bb, spec_box=LM['L2']['projected_box'])
        elif name == 'Maxentius' and MAX_V2:                                  # 21:57 사용자: 레퍼런스 모형(큰 아케이드 + 3층 반원 안뜰)
            o = build_maxentius_v2(GC, LM['L7'])
            o.root.location.z = lot_z(S, 'basilica')                       # d7: 포룸 판석 폐허 대지 위(z 2)
            s, kz, bb = fit_skz(o.root, LM['L7']['projected_box'])
            an = maxentius_anchors(o, A)
            out[name] = dict(id='L7', s=s, kz=kz, box=bb, spec_box=LM['L7']['projected_box'])
        elif name == 'Maxentius':
            o, P_, nd = build_maxentius(GC, LM['L7'])
            shrink_about(o.root, LM['L7']['projected_box'][0], LM['L7']['projected_box'][3], MAX_SHRINK)
            if DECOR:
                maxentius_life(o, P_)
            bb = screen_box(o.root)
            an = maxentius_anchors(o, A)
            out[name] = dict(id='L7', s=1.0, kz=1.0, box=bb, spec_box=LM['L7']['projected_box'], dashes=nd)
        elif name == 'Marcellus':
            o, P_ = build_marcellus(GC, LM['L9'], CM)
            ds = float(LM['L9'].get('draw_scale') or 1.0)                               # 20:01 d5: 극장 중심(draw_pivot = 중심의 화면 점) 둘레 배율
            if abs(ds - 1.0) > 1e-6:
                o.root.scale = (ds, ds, ds)
                bpy.context.view_layer.update()
            if DECOR:
                marcellus_life(o, P_)
            bb = corner_draw(o.root, *MC_DRAW) if MC_DRAW else screen_box(o.root)
            an = marcellus_anchors(o, A)
            out[name] = dict(id='L9', s=1.0, kz=1.0, box=bb, spec_box=LM['L9']['projected_box'], bank=P_['bank'])
        else:
            continue
        out[name]['layers'] = sorted(o.layers)
        out[name]['anchors'] = {k: dict(screen=list(v['screen']), tentative=list(v['tentative']), found=bool(v['found']),
                                        offset=v.get('offset_mm'), surface=v.get('surface')) for k, v in an.items()}
    return out


def layer_audit_city():
    """루트별 L0~L6 메시 수(빈 메시 제외). bglobal의 roma_kit.layer_audit가 있으면 그것을 쓴다"""
    c = bpy.data.collections.get(COLL)
    if hasattr(R, 'layer_audit'):
        try:
            return R.layer_audit(c)
        except Exception:
            pass
    res = {}
    for r in [o for o in c.objects if o.type == 'EMPTY' and o.name.endswith('_root')]:
        cnt = {('L%d' % i): 0 for i in range(7)}
        for ob in r.children_recursive:
            if ob.type != 'MESH' or len(ob.data.polygons) == 0:
                continue
            m = re.search(r'_L(\d)_', ob.name)
            if m and ('L' + m.group(1)) in cnt:
                cnt['L' + m.group(1)] += 1
        res[r.name] = dict(counts=cnt, missing=[k for k, v in cnt.items() if v == 0])
    return res


def person_heights():
    """L6 사람 화면 키(발~머리)"""
    c = bpy.data.collections.get(COLL)
    hs = []
    for ob in c.all_objects:
        if ob.type == 'MESH' and '_L6_person' in ob.name:
            k = ob.matrix_world.to_scale().z
            hs.append(round(k * 1.0, 3))
    return (min(hs), max(hs), len(hs)) if hs else None
