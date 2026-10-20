
# roma_flat — 벡터 일러스트 재질: 조명·그림자·AO 없음. 면 방향에 따라 정해진 평면 톤(윗면 1.0 · 왼면 0.86 · 오른면 0.68). 담당: bglobal
# L7 외곽선 결정(b1 결정 유지, b5 D9 재확인): 쓰지 않는다. 203X·LocalBanana 모두 검은 외곽선이 없고, 경계는 ISO_TONE 면 톤 차이와
#   L5 밝은 띠(코니스·모서리·잎 윗면)로 만든다. 그래서 공용 외곽선 재질·Line Art·Freestyle을 두지 않는다(OUTLINE = False).
#   모서리를 세울 때는 edge_light()로 L5 하이라이트 띠(화면 0.25~0.4mm, 면색 명도 +10~15%)를 쌓는다.
# b5 팔레트 확정(D9): 'ground' #ECD8AC = 렌더 RGB (236, 216, 172) = 설계 GROUND · 'slab' 판석 길·광장 판석 한 값 · 'water' 물 한 값.
#   hero·ground·coast는 PAL['slab']·PAL['water']를 그대로 쓴다(값을 패키지 안에 따로 두지 않는다).
import bpy, bmesh, math

OUTLINE = False

def srgb(h):
    h = h.lstrip('#')
    c = [int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)

def shade(hexcol, k, toward=None):
    """평면색 변형(16진 → 16진). k < 1: 같은 색상으로 어둡게(곱) · k > 1: toward 색(기본 흰색) 쪽으로 (k − 1)만큼 섞어 밝게.
    L1 깊이색·L5 하이라이트를 바탕색에서 만들 때 쓴다(빛 계산이 아니라 색 지정)"""
    h = hexcol.lstrip('#')
    c = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    if k <= 1.0:
        o = [x * k for x in c]
    else:
        t = min(1.0, k - 1.0)
        th = (toward or '#FFFFFF').lstrip('#')
        tc = [int(th[i:i + 2], 16) for i in (0, 2, 4)]
        o = [x + (y - x) * t for x, y in zip(c, tc)]
    return '#%02X%02X%02X' % tuple(int(round(max(0, min(255, x)))) for x in o)

def mix_hex(a, b, t):
    """두 16진 색을 t(0→a, 1→b)로 섞는다"""
    a, b = a.lstrip('#'), b.lstrip('#')
    ca = [int(a[i:i + 2], 16) for i in (0, 2, 4)]; cb = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return '#%02X%02X%02X' % tuple(int(round(x + (y - x) * t)) for x, y in zip(ca, cb))

TONE_TOP, TONE_L, TONE_R = 1.0, 0.86, 0.68

def tone_group():
    g = bpy.data.node_groups.get('ISO_TONE')
    if g:
        return g
    g = bpy.data.node_groups.new('ISO_TONE', 'ShaderNodeTree')
    g.interface.new_socket('Color', in_out='INPUT', socket_type='NodeSocketColor')
    g.interface.new_socket('Tone', in_out='OUTPUT', socket_type='NodeSocketFloat')
    g.interface.new_socket('Color', in_out='OUTPUT', socket_type='NodeSocketColor')
    N = g.nodes
    gi = N.new('NodeGroupInput'); go = N.new('NodeGroupOutput')
    geo = N.new('ShaderNodeNewGeometry')
    sep = N.new('ShaderNodeSeparateXYZ'); g.links.new(geo.outputs['True Normal'], sep.inputs[0])
    at = N.new('ShaderNodeMath'); at.operation = 'ARCTAN2'
    g.links.new(sep.outputs['Y'], at.inputs[0]); g.links.new(sep.outputs['X'], at.inputs[1])
    # 가로 방위 φ: 왼면(−90°)=0.86, 오른면(0°)=0.68, 선형 · 0.58~0.95로 자름
    mr = N.new('ShaderNodeMapRange'); mr.clamp = True
    mr.inputs['From Min'].default_value = -math.radians(135); mr.inputs['From Max'].default_value = math.radians(45)
    mr.inputs['To Min'].default_value = TONE_L + (TONE_L - TONE_R) * 0.5; mr.inputs['To Max'].default_value = TONE_R - (TONE_L - TONE_R) * 0.5
    g.links.new(at.outputs[0], mr.inputs['Value'])
    cz = N.new('ShaderNodeMath'); cz.operation = 'MAXIMUM'; cz.inputs[1].default_value = 0.0
    g.links.new(sep.outputs['Z'], cz.inputs[0])
    mx = N.new('ShaderNodeMix'); mx.data_type = 'FLOAT'
    g.links.new(cz.outputs[0], mx.inputs['Factor'])
    g.links.new(mr.outputs['Result'], mx.inputs['A'])
    mx.inputs['B'].default_value = TONE_TOP
    mul = N.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
    mul.inputs['Factor'].default_value = 1.0
    g.links.new(gi.outputs['Color'], mul.inputs['A'])
    cv = N.new('ShaderNodeCombineColor')
    for k in ('Red', 'Green', 'Blue'):
        g.links.new(mx.outputs['Result'], cv.inputs[k])
    g.links.new(cv.outputs['Color'], mul.inputs['B'])
    g.links.new(mx.outputs['Result'], go.inputs['Tone'])
    g.links.new(mul.outputs['Result'], go.inputs['Color'])
    return g

def _base(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Strength'].default_value = 1.0
    tg = nt.nodes.new('ShaderNodeGroup'); tg.node_tree = tone_group()
    nt.links.new(tg.outputs['Color'], em.inputs['Color']); nt.links.new(em.outputs[0], out.inputs['Surface'])
    m.diffuse_color = (0.5, 0.5, 0.5, 1)
    return m, nt, tg

def flat(name, hexcol):
    m, nt, tg = _base(name)
    tg.inputs['Color'].default_value = (*srgb(hexcol), 1.0)
    m.diffuse_color = (*srgb(hexcol), 1.0)
    return m

def blocks(name, c1, c2, c3, joint, bw, rh, jw=0.05, uv=True):
    """돌 블록 무늬 레이어(L3): 블록마다 3색 중 하나, 줄눈은 가는 짙은 선. 경계가 또렷한 평면색"""
    m, nt, tg = _base(name)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    br = nt.nodes.new('ShaderNodeTexBrick')
    nt.links.new(tc.outputs['UV' if uv else 'Object'], br.inputs['Vector'])
    br.inputs['Scale'].default_value = 1.0; br.inputs['Brick Width'].default_value = bw; br.inputs['Row Height'].default_value = rh
    br.inputs['Mortar Size'].default_value = jw; br.inputs['Mortar Smooth'].default_value = 0.0
    br.inputs['Color1'].default_value = (0, 0, 0, 1); br.inputs['Color2'].default_value = (1, 1, 1, 1); br.inputs['Bias'].default_value = 0.0
    br.offset = 0.5
    rp = nt.nodes.new('ShaderNodeValToRGB'); cr = rp.color_ramp; cr.interpolation = 'CONSTANT'
    cr.elements[0].position = 0.0; cr.elements[0].color = (*srgb(c1), 1)
    e = cr.elements.new(0.45); e.color = (*srgb(c2), 1)
    e = cr.elements.new(0.80); e.color = (*srgb(c3), 1)
    bw_ = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(br.outputs['Color'], bw_.inputs[0]); nt.links.new(bw_.outputs[0], rp.inputs['Fac'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    nt.links.new(br.outputs['Fac'], mx.inputs['Factor'])
    nt.links.new(rp.outputs['Color'], mx.inputs['A']); mx.inputs['B'].default_value = (*srgb(joint), 1)
    nt.links.new(mx.outputs['Result'], tg.inputs['Color'])
    m.diffuse_color = (*srgb(c2), 1.0)
    return m

PAL = {
    'trav': '#D8B98E', 'trav_hi': '#E8D0A8', 'trav_lo': '#C9A57A', 'trav_deep': '#8C6B4B', 'trav_deeper': '#6E5038',
    'joint': '#B39169', 'brick': '#B86F4C', 'brick_hi': '#C98260', 'brick_joint': '#9A5A3D', 'tuff': '#A8957A',
    'outline': '#5E4430', 'soil': '#9A7352', 'soil_dk': '#7E5B40', 'soil_lt': '#B38A63',
    'cobble1': '#C2B8A8', 'cobble2': '#ABA293', 'cobble3': '#D1C8B8', 'cobble_joint': '#8E8576', 'pave': '#E2D1B2', 'pave_joint': '#C2AD8A',
    'grass1': '#9BA35C', 'grass2': '#7D8B45', 'grass3': '#B4B56E', 'dirt': '#C7A77B',
    'cypress1': '#3E5A33', 'cypress2': '#4E6C3C', 'cypress3': '#2F4729', 'olive1': '#8D946A', 'olive2': '#A3A87C', 'olive3': '#737B54',
    'bark': '#6B5240', 'wood': '#A97B4F', 'wood_dk': '#7E5A39', 'awning_r': '#B8402E', 'awning_w': '#EFE7D6', 'terra': '#B4623E',
    'skin': '#D8A07C', 'c_white': '#EFE8DA', 'c_red': '#B13A2C', 'c_blue': '#3E5D8C', 'c_ochre': '#C99B45', 'c_green': '#5F7B4A', 'hair': '#3B2A20',
    'moss': '#8E9A52', 'stain': '#B89874', 'lime': '#F2EFE6', 'pozz': '#9C5B42', 'aggr': '#9A958B', 'water': '#7FB3BD', 'ground': '#E3CFA8',
}
# b5 확정 값(D9, bglobal): 위 옛 값을 덮어쓴다
#   ground: 땅 윗면 = 설계 GROUND (236, 216, 172). 윗면 톤 1.0이라 렌더 RGB가 이 값이다(sample_rgb로 실측)
#   slab:   판석 길·광장 판석 한 값 = 설계 길 색 ROAD_C (212, 194, 156). 무늬(줄눈·짙은 판)는 shade()·mix_hex()로 이 값에서 만든다
#   water:  물(강·바다·내항·운하·욕장 물) 한 값 = 설계 바다 SEA_C (146, 182, 208). 얕은·깊은 띠는 이 값에서 섞는다
PAL.update({'ground': '#ECD8AC', 'slab': '#D4C29C', 'water': '#92B6D0'})
# 소품 원형용 추가 색(global, 2026-10-19 · 기존 키 값은 바꾸지 않는다). LocalBanana 미니어처의 따뜻한 색을 203X식 평면색으로
PAL.update({
    'pine1': '#5E7A3E', 'pine2': '#6C8846', 'pine3': '#526D37',
    'leaf_lt': '#D9DD8E',          # 잎 하이라이트를 섞는 쪽(햇빛 받은 연두)
    'bark_dk': '#4F3B2E', 'wood_hi': '#C99A68', 'leather': '#7A5236', 'void': '#4E3A2B',
    'skin2': '#C68A63', 'skin3': '#E2B48F', 'skin4': '#B27752',
    'hair2': '#241A14', 'hair3': '#6B4428', 'hair4': '#8E857B',
    'c_cream': '#E9DDC4', 'c_wine': '#7A3B2A', 'c_brown': '#8C5236',
    'wicker': '#C9A060', 'linen': '#EFE7D6', 'sack': '#D9C7A0',
    'fruit_r': '#C0392B', 'fruit_o': '#E08A2E', 'fruit_g': '#8DA047', 'fruit_y': '#E3C04A',
    'flower_p': '#D9788A', 'flower_y': '#E8C24A', 'flower_w': '#F1EBDD', 'flower_r': '#C2453A',
    'plaster1': '#E6D2AE', 'plaster2': '#D9B98E', 'plaster3': '#EDE0C6', 'plaster4': '#D4A983',
    'roof1': '#B5623F', 'roof2': '#C2704A', 'roof3': '#A85A3A',
    'shutter_g': '#5F7B4A', 'shutter_b': '#3E5D8C', 'terra2': '#C27547', 'terra3': '#A65735', 'terra4': '#C98A5A',
})

# ───────────────────────── L5 하이라이트 도우미(모서리 띠) ─────────────────────────
def _srgb_to_lab(h):
    c = srgb(h)
    X = 0.4124564 * c[0] + 0.3575761 * c[1] + 0.1804375 * c[2]
    Y = 0.2126729 * c[0] + 0.7151522 * c[1] + 0.0721750 * c[2]
    Z = 0.0193339 * c[0] + 0.1191920 * c[1] + 0.9503041 * c[2]
    def f(t):
        return t ** (1.0 / 3.0) if t > 216.0 / 24389.0 else (24389.0 / 27.0 * t + 16.0) / 116.0
    fx, fy, fz = f(X / 0.95047), f(Y / 1.0), f(Z / 1.08883)
    return 116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz)

def _lab_to_hex(L, a, b):
    fy = (L + 16.0) / 116.0; fx = fy + a / 500.0; fz = fy - b / 200.0
    def fi(t):
        return t ** 3 if t ** 3 > 216.0 / 24389.0 else (116.0 * t - 16.0) * 27.0 / 24389.0
    X, Y, Z = fi(fx) * 0.95047, fi(fy), fi(fz) * 1.08883
    r = 3.2404542 * X - 1.5371385 * Y - 0.4985314 * Z
    g = -0.9692660 * X + 1.8760108 * Y + 0.0415560 * Z
    bb = 0.0556434 * X - 0.2040259 * Y + 1.0572252 * Z
    def enc(x):
        x = max(0.0, min(1.0, x))
        return 1.055 * x ** (1 / 2.4) - 0.055 if x > 0.0031308 else 12.92 * x
    return '#%02X%02X%02X' % tuple(int(round(enc(x) * 255)) for x in (r, g, bb))

def light_hex(hexcol, k=0.12):
    """면색의 명도(CIELAB L*)를 k만큼(0.10~0.15 = +10~15%) 올린 하이라이트 색. 색상·채도는 그대로 둔다(빛 계산이 아니라 색 지정)"""
    L, a, b = _srgb_to_lab(hexcol)
    return _lab_to_hex(min(100.0, L * (1.0 + k)), a, b)

def edge_light_mat(name, base_hex, k=0.12):
    """L5 하이라이트 띠 재질: 바탕색을 light_hex로 밝힌 평면색(× ISO_TONE)"""
    return flat(name, light_hex(base_hex, k))

EDGE_W_MM = 0.32           # 하이라이트 띠의 화면 폭(0.25~0.4mm)
_ISO_PERP = 0.8660254      # 축에 나란한 모서리에서 띠 폭(평면·세로 w) → 화면 수직 폭 = 0.866·w

def edge_light(src, dst=None, mi=0, width_mm=EDGE_W_MM, scale=1.0, lift_mm=0.06, top=True, corners=False,
               visible_only=True, min_len=0.0, max_bands=20000):
    """L5 하이라이트 띠: src bmesh의 볼록한 '윗면–옆면' 모서리마다 윗면 위에 가는 띠(사각 면)를 dst bmesh에 만든다.
    - width_mm: 화면 폭(mm, 0.25~0.4). scale: 이 bmesh 지역 단위 1의 최종 월드 mm(fit_to_box 뒤 축척을 알면 준다).
      지역 띠 폭 = width_mm / 0.866 / scale. lift_mm: 윗면에서 띄우는 높이(z-파이팅 0, D13 ≥ 0.05mm)
    - top=True: 윗면(법선 z > 0.75)과 옆면(|z| < 0.35) 사이 볼록 모서리 · corners=True: 보이는 두 옆면(왼면 −Y · 오른면 +X) 사이의
      볼록한 세로 모서리에도 오른면 쪽에 세로 띠를 만든다
    - visible_only=True: 카메라가 보는 옆면(법선이 −Y 또는 +X 쪽)에 붙은 모서리만(배치 때 돌리지 않는 랜드마크용)
    - 재질 칸 mi에는 edge_light_mat(…)으로 만든 밝은 평면색을 둔다. 반환: 만든 면 수"""
    from mathutils import Vector
    dst = src if dst is None else dst
    w = width_mm / _ISO_PERP / max(1e-9, scale)
    lift = lift_mm / max(1e-9, scale)
    view = Vector((0.70710678, -0.70710678, 0.0))
    made = 0
    edges = list(src.edges)
    for e in edges:
        if made >= max_bands:
            break
        if len(e.link_faces) != 2:
            continue
        p0, p1 = e.verts[0].co.copy(), e.verts[1].co.copy()
        L = (p1 - p0).length
        if L < max(1e-9, min_len):
            continue
        fa, fb = e.link_faces
        na, nb = fa.normal, fb.normal
        mid = (p0 + p1) * 0.5
        if top:
            ft, fs = (fa, fb) if na.z > nb.z else (fb, fa)
            nt, ns = ft.normal, fs.normal
            if nt.z > 0.75 and abs(ns.z) < 0.35 and abs(p1.z - p0.z) < 0.25 * L:
                if visible_only and ns.dot(view) < 0.2:
                    continue
                ct = ft.calc_center_median()
                if (ct - mid).dot(ns) >= 0:                       # 오목한 모서리(안쪽 구석)는 건너뛴다
                    continue
                d = (p1 - p0).normalized()
                into = (ct - mid) - d * (ct - mid).dot(d)
                into.z = 0.0
                if into.length < 1e-9:
                    continue
                into.normalize()
                ww = min(w, 0.45 * (ct - mid).length * 2.0)
                up = Vector((0.0, 0.0, lift))
                vs = [dst.verts.new(p0 + up), dst.verts.new(p1 + up), dst.verts.new(p1 + into * ww + up), dst.verts.new(p0 + into * ww + up)]
                f = dst.faces.new(vs); f.material_index = mi; made += 1
                continue
        if corners and abs(na.z) < 0.35 and abs(nb.z) < 0.35 and abs(p1.z - p0.z) > 0.6 * L:
            if na.dot(view) <= 0.0 or nb.dot(view) <= 0.0:
                continue
            fr, fl = (fa, fb) if na.x > nb.x else (fb, fa)     # 오른면(+X 쪽) 위에 띠
            nr = fr.normal
            cr = fr.calc_center_median()
            if (cr - mid).dot(fl.normal) >= 0:
                continue
            into = (cr - mid); into.z = 0.0
            if into.length < 1e-9:
                continue
            into.normalize()
            out = nr * lift
            vs = [dst.verts.new(p0 + out), dst.verts.new(p1 + out), dst.verts.new(p1 + into * w + out), dst.verts.new(p0 + into * w + out)]
            f = dst.faces.new(vs); f.material_index = mi; made += 1
    return made
