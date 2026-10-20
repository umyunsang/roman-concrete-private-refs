# roma_pkg_ground — 땅 판·해안 지층 단면(3겹)·강둑·테베레 물결·하구 폭포·바다 물결·길(판석·흰 중앙선)·밭·포도밭·목초지·
#                    시내 지붕 블록(집 수백 채)·나무 무리·심은 지면(spec planted). 담당: ground
# 팔각 받침은 없다(사용자 06:06, "8각형 받침대 제거해"). 땅 판에 팔각 단·팔각 홈·팔각 단면을 두지 않는다.
#   콜로세움 군(평면 반지름 90, hero 조경)은 지도 땅(Z=0)에 바로 놓이고, 길·집·나무가 그 가장자리까지 이어진다.
# 다시 짓는 순서상 맨 마지막: 다른 패키지의 숨긴 절단체 X_CUT_*로 땅 판을 파낸다.
# 벡터 일러스트: 방출 + ISO_TONE 평면 톤만 쓴다(조명·AO·그림자·Principled·실사 텍스처 0).
# 오브젝트마다 표현 레이어 L0~L6: 이름 GROUND_{Obj}_L{n}_{part}, 루트 Empty GROUND_{Obj}_root
#   Land   L0 땅 판 · L1 강바닥·물길 깊이색 · L2 강둑 돌 · L3 땅 결(얼룩 조각) · L4 —(지형 단차는 Coast·River) · L5 해안 윗선 · L6 풀 포기
#   Coast  L0 지층 단면 면 · L1 윗선 밑 짙은 띠·해식굴 · L2 3겹 지층(표토·붉은 화산재·노란 응회암) · L3 자갈·줄무늬 · L4 바위 · L5 윗선 · L6 매달린 풀·물자국·포말
#   River  L0 물 · L1 둑 쪽 짙은 물 · L2 둑 경계석·석축 · L3 물결 · L4 계단·계선주 · L5 반짝임 · L6 갈대
#   Falls  L0 물 막 · L1 뒤 홈 · L2 입술 돌 · L3 물줄기 결 · L4 가운데 바위 · L5 입술 하이라이트 · L6 물보라
#   Sea    L0 바다 · L1 얕은 물·깊은 물 색 · L2 해안 포말선 · L3 물결 · L4 물 위 바위섬 · L5 반짝임 · L6 갈매기
#   Roads  L0 길 판 · L1 길 옆면·바퀴 자국 · L2 연석 · L3 다각 판석(재질) · L4 흰 중앙선·이정표·징검돌 · L5 연석 윗선 · L6 풀·사람
#   Fields L0 밭 판 · L1 고랑 그늘·포도 이랑 흙 · L2 생울타리·돌담 · L3 고랑 무늬·포도 줄 · L4 건초 더미·오두막 · L5 이랑 윗선 · L6 양·일꾼·나무
#   City   L0 벽·지붕 덩어리 · L1 창·문·안뜰 깊이색 · L2 처마띠·문틀·블록 연석 · L3 기와·벽돌 무늬 · L4 발코니·안뜰 빗물받이·옥상 · L5 용마루·처마 하이라이트 · L6 차양·화분·정원·사람
#   Trees  L0 수관 · L1 수관 아래 그늘 · L2 줄기 · L3 잎 면(다면체) · L4 수관 덩이 · L5 꼭대기 하이라이트 · L6 밑동 풀
import bpy, bmesh, json, math
from mathutils import Vector
import roma_kit as R, roma_flat as FL, roma_geo as G

COLL = 'MAP_Ground'
SPEC = '/Users/um-yunsang/roman-concrete-private-refs/.work/design/current/out/spec.json'
DRAWN = '/Users/um-yunsang/roman-concrete-private-refs/.work/design/current/out/drawn.json'
LAND_T = 10.0          # 땅 판 두께(해안 지층 단면 10 mm)
RIVER_Z = -2.0         # 강 수면
RIVER_BED = -3.2       # 강바닥(물길만 판다. 땅 판을 뚫지 않는다)
SEA_Z = -9.7           # 바다 수면
COAST_Y = 380.0        # 해안선(평면 Y)
DECOR = False          # 16:14 사용자 결정(core 정보 오브젝트만): 땅 판(땅 결 L3~L6 포함)·강·하구 폭포·바다·해안 단면만 짓는다.
#   시내 집·지붕 블록·나무 무리·밭·포도밭·길 전부(R1~R7·아피아 가도·진입 경사)·풀 덤불은 짓지 않는다(코드는 보관).
#   비움 구역도 지운 대상(배경 베수비오·소품 상자·공사장·길·히어로 예약 원)을 빼고, 랜드마크 상자·네로 받침·라벨·바닥 글만 남긴다
# b5 공통 결정(D1·D3): spec(current)에 열쇠가 있으면 그 값을, 없으면 결정 상수를 쓴다(_spec_consts가 덮어쓴다)
HERO_C = (462.34, 173.66)    # 조경(히어로 군) 중심 평면 = 화면 (250, 318)
HERO_R = 90.0                # 조경 예약 반지름(평면). hero 담당 구역
HERO_KEEP = 90.5             # 집·나무·소품·밭·땅 결 0(D14 '조경 R 90.5 안')
HERO_RING = 3.0              # 조경 경계와 첫 집 줄의 빈 띠 ≤ 3 mm(평면)
HERO_BLDG = (192.6, 226.4, 300.4, 330.1)   # 콜로세움 건물 화면 상자(D2)
NERO_YARD = (172.0, 196.0, 198.0, 228.0)   # 네로 거상 받침 둘레 포장 마당(hero가 짓고 ground는 비운다, D6)
WORKSITE = (206.0, 384.0, 252.0, 412.0)    # 공사장(hero 구역, D14)
R7_NORTH_Y = 250.4           # 다리 길 R7 북쪽 끝(평면 Y, D3)
R7_RAMP = (294.76, 304.76, 3.0)            # R7 남쪽 진입 경사: 평면 Y 구간 → 끝 높이(다리 상판 3.0, D7)
STAGE = (0.0, 92.0, 420.0, 505.0)          # 지도 무대(화면 mm, D12): 땅 판 윗면 = 이 사각형을 평면으로 되돌린 평행사변형
TOP_MIN = 93.0               # 위 변 근처 오브젝트의 화면 윗끝 ≥ 93(D12)
GROUND_HEX = '#ECD8AC'       # 땅 윗면 렌더 RGB (236, 216, 172)(D9, = 설계 GROUND)
WATER_HEX = FL.PAL['water']   # 물 = PAL 'water' 한 값 #92B6D0(hero·ground·coast 공용, D9)
H_PERSON = 2.4               # 사람 키(화면 mm, D8): 지도 일반 2.4 · 조경 경계 밖 15 mm 안 길 위 3.4
H_PERSON_NEAR = 3.4
APPIA_ROW_BY_SUBURB = True   # 통합(b1): 아피아 가도 가로수 열은 suburb가 짓는다(build_trees 1번 단계를 건너뛴다)
PAPER = '#E7D0A0'      # 합성 바탕 종이색(tools/compose.py)
OTHER_COLLS = ('HERO_Colosseum', 'LM_City', 'LM_Baths', 'LM_Suburb', 'LM_Coast')   # 다른 패키지(읽기만: 실제 지은 자리 비움)


def _spec_consts(S_):
    """d5에 새로 생기는 열쇠(core_map.hero.landscape·colosseum, frame.stage)가 있으면 그 값으로 바꾼다(D1)"""
    global HERO_C, HERO_R, HERO_BLDG, STAGE
    CM = S_.get('core_map', {})
    hero = CM.get('hero', {})
    land = hero.get('landscape') or {}
    c = land.get('center_plan') or land.get('center')
    if c and len(c) == 2:
        HERO_C = (float(c[0]), float(c[1]))
    r = land.get('reserve_R_plan') or land.get('reserve_R')
    if r:
        HERO_R = float(r)
    colo = hero.get('colosseum') or {}
    b = colo.get('projected_box') or colo.get('screen_box')
    if b and len(b) == 4:
        HERO_BLDG = tuple(float(v) for v in b)
    try:
        st = S_['frame']['stage']['rect']
        STAGE = tuple(float(v) for v in st)
    except Exception:
        pass
C30 = R.C30
hsh = R.hash01
# 테베레(평면): ↘ 팔 Y=314 ±9.25, ↙ 팔 X=533.4 ±11.55
A1_Y0, A1_Y1 = 304.75, 323.25
A2_X0, A2_X1 = 521.85, 544.95


def V(X, Y, Z=0.0):
    """설계 평면 → Blender"""
    return (X, -Y, Z)


def S(X, Y, Z=0.0):
    """설계 평면 → 포스터 화면 mm"""
    return (C30 * (X - Y), 0.5 * (X + Y) - Z)


# ───────────────────────── 재질(평면색 × ISO_TONE) ─────────────────────────
def _sock(node, ident, out=False):
    socks = node.outputs if out else node.inputs
    for s in socks:
        if s.identifier == ident:
            return s
    for s in socks:
        if s.name == ident:
            return s
    raise KeyError(ident)


def _m(nt, op, a, b=None):
    n = nt.nodes.new('ShaderNodeMath'); n.operation = op
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = float(v)
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def _mixc(nt, fac, a, b):
    n = nt.nodes.new('ShaderNodeMix'); n.data_type = 'RGBA'; n.clamp_factor = True
    fs = _sock(n, 'Factor_Float')
    if isinstance(fac, (int, float)):
        fs.default_value = fac
    else:
        nt.links.new(fac, fs)
    for ident, v in (('A_Color', a), ('B_Color', b)):
        s = _sock(n, ident)
        if isinstance(v, str):
            s.default_value = (*FL.srgb(v), 1.0)
        else:
            nt.links.new(v, s)
    return _sock(n, 'Result_Color', out=True)


def _pos(nt):
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    return sep.outputs['X'], sep.outputs['Y'], sep.outputs['Z']


def _ramp(nt, fac, stops):
    rp = nt.nodes.new('ShaderNodeValToRGB'); cr = rp.color_ramp; cr.interpolation = 'CONSTANT'
    cr.elements[0].position = stops[0][0]; cr.elements[0].color = (*FL.srgb(stops[0][1]), 1)
    for p, hx in stops[1:]:
        e = cr.elements.new(p); e.color = (*FL.srgb(hx), 1)
    nt.links.new(fac, rp.inputs['Fac'])
    return rp.outputs['Color']


def _fade(nt, col, y0=522.0, y1=566.0):
    """화면 y가 y0→y1로 갈수록 종이색으로 흐린다(홍콩 앞바다 선례, 하단 띠 밑 바다)"""
    x, y, z = _pos(nt)
    ys = _m(nt, 'SUBTRACT', _m(nt, 'MULTIPLY', _m(nt, 'SUBTRACT', x, y), 0.5), z)
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.interpolation_type = 'SMOOTHSTEP'; mr.clamp = True
    mr.inputs['From Min'].default_value = y0; mr.inputs['From Max'].default_value = y1
    mr.inputs['To Min'].default_value = 0.0; mr.inputs['To Max'].default_value = 1.0
    nt.links.new(ys, mr.inputs['Value'])
    return _mixc(nt, mr.outputs['Result'], col, PAPER)


def flat_fade(name, hexcol):
    m, nt, tg = FL._base(name)
    nt.links.new(_fade(nt, hexcol), tg.inputs['Color'])
    m.diffuse_color = (*FL.srgb(hexcol), 1)
    return m


def stripes(name, c0, c1, pitch, frac, axis='X'):
    """평행 줄무늬(L3 밭고랑·물줄기): axis='X'면 월드 X를 따라 줄이 바뀐다"""
    m, nt, tg = FL._base(name)
    x, y, z = _pos(nt)
    u = {'X': x, 'Y': y, 'Z': z}[axis]
    f = _m(nt, 'FRACT', _m(nt, 'MULTIPLY', u, 1.0 / pitch))
    k = _m(nt, 'LESS_THAN', f, frac)
    nt.links.new(_mixc(nt, k, c0, c1), tg.inputs['Color'])
    m.diffuse_color = (*FL.srgb(c0), 1)
    return m


def strata(name):
    """해안 지층 단면 3겹(L2) + 윗선 밑 짙은 띠(L1) + 자갈(L3) + 응회암 줄(L3). 경계는 물결 모양"""
    m, nt, tg = FL._base(name)
    x, y, z = _pos(nt)
    s = _m(nt, 'SUBTRACT', x, y)
    w = _m(nt, 'ADD', _m(nt, 'MULTIPLY', _m(nt, 'SINE', _m(nt, 'MULTIPLY', s, 0.19)), 0.38),
           _m(nt, 'MULTIPLY', _m(nt, 'SINE', _m(nt, 'ADD', _m(nt, 'MULTIPLY', s, 0.53), 1.7)), 0.22))
    zz = _m(nt, 'ADD', z, w)
    fac = _m(nt, 'MULTIPLY', _m(nt, 'ADD', zz, 10.0), 0.1)
    lay = _ramp(nt, fac, [(0.0, '#C7A36C'), (0.37, '#A8603F'), (0.74, '#8E6A49'), (0.945, '#654630')])
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.voronoi_dimensions = '3D'; vo.feature = 'F1'
    vo.inputs['Scale'].default_value = 0.9
    geo = nt.nodes.new('ShaderNodeNewGeometry'); nt.links.new(geo.outputs['Position'], vo.inputs['Vector'])
    sc = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(vo.outputs['Color'], sc.inputs[0])
    peb = _m(nt, 'MULTIPLY', _m(nt, 'LESS_THAN', vo.outputs['Distance'], 0.17), _m(nt, 'GREATER_THAN', sc.outputs[0], 0.45))
    peb = _m(nt, 'MULTIPLY', peb, _m(nt, 'LESS_THAN', zz, -0.9))
    light = _mixc(nt, 0.38, lay, '#F2E4C6')
    col = _mixc(nt, peb, lay, light)
    lines = _m(nt, 'MULTIPLY', _m(nt, 'LESS_THAN', _m(nt, 'FRACT', _m(nt, 'MULTIPLY', _m(nt, 'ADD', zz, 20.0), 0.9)), 0.1),
               _m(nt, 'LESS_THAN', zz, -6.9))
    col = _mixc(nt, lines, col, '#AE8A57')
    nt.links.new(col, tg.inputs['Color'])
    m.diffuse_color = (*FL.srgb('#A8603F'), 1)
    return m


def basalt(name, c=('#ACA394', '#9F978A', '#B8B0A0'), joint='#857C70', scale=0.78):
    """로마 가도 다각 판석(L3): 셀마다 3색 중 하나 + 가는 줄눈"""
    m, nt, tg = FL._base(name)
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    v1 = nt.nodes.new('ShaderNodeTexVoronoi'); v1.voronoi_dimensions = '2D'; v1.feature = 'F1'
    v1.inputs['Scale'].default_value = scale; nt.links.new(geo.outputs['Position'], v1.inputs['Vector'])
    sc = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(v1.outputs['Color'], sc.inputs[0])
    col = _ramp(nt, sc.outputs[0], [(0.0, c[0]), (0.4, c[1]), (0.72, c[2])])
    v2 = nt.nodes.new('ShaderNodeTexVoronoi'); v2.voronoi_dimensions = '2D'; v2.feature = 'DISTANCE_TO_EDGE'
    v2.inputs['Scale'].default_value = scale; nt.links.new(geo.outputs['Position'], v2.inputs['Vector'])
    j = _m(nt, 'LESS_THAN', v2.outputs['Distance'], 0.065)
    nt.links.new(_mixc(nt, j, col, joint), tg.inputs['Color'])
    m.diffuse_color = (*FL.srgb(c[0]), 1)
    return m


def holdout(name):
    """땅 판 아래 변(푸터 윗선 y 568) 옆면: 투명(단면은 해안선에 한 번만 보인다)"""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial'); ho = nt.nodes.new('ShaderNodeHoldout')
    nt.links.new(ho.outputs[0], out.inputs['Surface'])
    return m


def var_mat(name, stops):
    """개체마다 다른 평면색(나무 복제용): Object Info Random → 경계가 또렷한 색"""
    m, nt, tg = FL._base(name)
    oi = nt.nodes.new('ShaderNodeObjectInfo')
    nt.links.new(_ramp(nt, oi.outputs['Random'], stops), tg.inputs['Color'])
    m.diffuse_color = (*FL.srgb(stops[0][1]), 1)
    return m


def mats():
    global WATER_HEX
    F = FL.flat
    M = {}
    WATER_HEX = FL.PAL.get('water', WATER_HEX)
    M['land'] = F('F_ground_land', GROUND_HEX)                 # D9: 렌더 RGB (236, 216, 172)
    M['land_patch'] = F('F_ground_landPatch', '#DCC59C')
    M['land_patch2'] = F('F_ground_landPatch2', '#F2E2BC')
    M['land_dot'] = F('F_ground_landDot', '#CDB48B')
    M['strata'] = strata('F_ground_strata')
    M['bank'] = F('F_ground_bank', '#957052')
    M['quay'] = FL.blocks('F_ground_quay', '#C9B189', '#BEA57E', '#D4BE98', '#9A8262', 1.5, 0.7, 0.06)
    M['bed'] = F('F_ground_bed', '#6E5038')
    M['hold'] = holdout('F_ground_holdout')
    M['lip'] = F('F_ground_lip', '#F3E6C9')
    M['root_dk'] = F('F_ground_rootDark', '#5E4430')
    M['stain'] = F('F_ground_stain', '#7A5A40')
    M['cave'] = F('F_ground_cave', '#4E3828')
    M['rock'] = FL.blocks('F_ground_rock', '#B49670', '#A68862', '#C2A57E', '#8C7152', 1.1, 0.8, 0.07)
    M['rock_top'] = F('F_ground_rockTop', '#CDB38B')
    M['tuft'] = F('F_ground_tuft', '#869447')
    M['tuft2'] = F('F_ground_tuft2', '#9AA556')
    M['tuft3'] = F('F_ground_tuft3', '#6F7F3A')
    # 물
    M['r_deep'] = F('F_ground_riverDeep', FL.shade(WATER_HEX, 0.86))
    M['river'] = F('F_ground_river', WATER_HEX)                # 물 = PAL 'water' 한 값(D9)
    M['r_wave'] = F('F_ground_riverWave', '#B6D8DC')
    M['glint'] = F('F_ground_glint', '#EEF6F2')
    M['reed'] = F('F_ground_reed', '#7E8E43')
    M['reed2'] = F('F_ground_reed2', '#A3A25A')
    M['fall'] = stripes('F_ground_fall', '#A7D0D6', '#E2F0EF', 0.62, 0.32, 'X')
    M['fall_lip'] = F('F_ground_fallLip', '#F1F8F5')
    # 바다: PAL 'water' 한 값(L0). 얕은 물·깊은 물은 L1 띠 메시로 따로 쌓는다. 하단 띠 밑 흐림은 합성(compose.py, 62 mm)이 한 번만 한다
    M['foam'] = F('F_ground_foam', '#F1F3EC')
    M['sea'] = F('F_ground_sea', WATER_HEX)
    M['s_shallow'] = F('F_ground_seaShallow', FL.mix_hex(WATER_HEX, '#E6F1EE', 0.30))
    M['s_shallow2'] = F('F_ground_seaShallow2', FL.mix_hex(WATER_HEX, '#E6F1EE', 0.15))
    M['s_deep'] = F('F_ground_seaDeep', FL.shade(WATER_HEX, 0.9))
    M['s_wave'] = F('F_ground_seaWave', FL.mix_hex(WATER_HEX, '#FFFFFF', 0.38))
    M['s_glint'] = F('F_ground_seaGlint', '#E8F3F2')
    M['gull'] = F('F_ground_gull', '#F7F5EE')
    # 길
    M['basalt'] = basalt('F_ground_basalt')
    M['road_side'] = F('F_ground_roadSide', '#8C8476')
    M['curb'] = FL.blocks('F_ground_curb', '#DCCBA6', '#D3C19B', '#E4D5B3', '#B8A580', 1.7, 0.9, 0.08)
    M['curb_hi'] = F('F_ground_curbHi', '#F2E7CF')
    M['cline'] = F('F_ground_centerLine', '#F6F2E8')
    M['rut'] = F('F_ground_rut', '#827C72')
    M['mile'] = F('F_ground_milestone', '#E8DDC5')
    # 밭
    M['wheatX'] = stripes('F_ground_wheatX', '#D8BD72', '#C4A65B', 0.95, 0.34, 'X')
    M['wheatY'] = stripes('F_ground_wheatY', '#D8BD72', '#C4A65B', 0.95, 0.34, 'Y')
    M['greenX'] = stripes('F_ground_greenX', '#AAB065', '#949C52', 0.9, 0.36, 'X')
    M['greenY'] = stripes('F_ground_greenY', '#AAB065', '#949C52', 0.9, 0.36, 'Y')
    M['plowX'] = stripes('F_ground_plowX', '#B88E62', '#9F7851', 0.8, 0.4, 'X')
    M['plowY'] = stripes('F_ground_plowY', '#B88E62', '#9F7851', 0.8, 0.4, 'Y')
    M['pasture'] = F('F_ground_pasture', '#B2B46E')
    M['pasture2'] = F('F_ground_pasture2', '#A4AA62')
    M['fallow'] = F('F_ground_fallow', '#CDB883')
    M['field_side'] = F('F_ground_fieldSide', '#A3845C')
    M['far1'] = stripes('F_ground_far1', '#DCCB98', '#D3C08A', 1.1, 0.3, 'X')
    M['far2'] = stripes('F_ground_far2', '#CFC791', '#C6BE86', 1.1, 0.3, 'Y')
    M['far3'] = F('F_ground_far3', '#D9C291')
    M['vine_soil'] = F('F_ground_vineSoil', '#C09D73')
    M['vine'] = F('F_ground_vine', '#7E8E43')
    M['vine_hi'] = F('F_ground_vineHi', '#A2AD5C')
    M['grape'] = F('F_ground_grape', '#6A3E5C')
    M['stake'] = F('F_ground_stake', '#7E5E41')
    M['hedge'] = F('F_ground_hedge', '#6E7E3C')
    M['hedge_hi'] = F('F_ground_hedgeHi', '#8E9B4E')
    M['wall'] = FL.blocks('F_ground_fieldWall', '#CDB792', '#C2AB86', '#D6C29F', '#A28C69', 0.9, 0.45, 0.08)
    M['hay'] = F('F_ground_hay', '#D9B862')
    M['hay_hi'] = F('F_ground_hayHi', '#EBD088')
    M['sheep'] = F('F_ground_sheep', '#F3EEE3')
    M['sheep_hd'] = F('F_ground_sheepHead', '#4E3D30')
    # 시내 집
    M['plaster'] = [F('F_ground_plaster%d' % i, c) for i, c in enumerate(('#E9D6B1', '#DFC398', '#EEE2CA', '#DAB089', '#E5CDA4'))]
    M['brick'] = FL.blocks('F_ground_brickWall', '#B9714E', '#C47D58', '#AD6646', '#94573B', 0.62, 0.22, 0.05)
    M['tile'] = {}
    for pal, cs in (('a', ('#C2704A', '#B5623F', '#CC7E55')), ('b', ('#A85A3A', '#9E5236', '#B3633F'))):
        for o, (bw, rh) in (('X', (0.42, 0.75)), ('Y', (0.75, 0.42))):
            M['tile'][pal + o + 'L'] = FL.blocks('F_ground_tile%s%sL' % (pal, o), cs[0], cs[1], cs[2], '#8E4A30', bw, rh, 0.09)
            dk = tuple('#%02X%02X%02X' % tuple(int(int(c[i:i + 2], 16) * 0.84) for i in (1, 3, 5)) for c in cs)
            M['tile'][pal + o + 'D'] = FL.blocks('F_ground_tile%s%sD' % (pal, o), dk[0], dk[1], dk[2], '#76402A', bw, rh, 0.09)
    M['fascia'] = F('F_ground_fascia', '#8E4A30')
    M['ridge'] = F('F_ground_ridge', '#E39A70')
    M['eave_dk'] = F('F_ground_eaveDark', '#9C7A58')
    M['cornice'] = F('F_ground_cornice', '#F0E3C8')
    M['win'] = F('F_ground_window', '#5C4232')
    M['shop'] = F('F_ground_shop', '#4C3627')
    M['door'] = F('F_ground_door', '#6A4630')
    M['frame'] = F('F_ground_frame', '#F2E8D2')
    M['atrium'] = F('F_ground_atrium', '#8C6B4B')
    M['atrium_fl'] = F('F_ground_atriumFloor', '#B79A76')
    M['pool'] = F('F_ground_impluvium', WATER_HEX)               # 물 한 값(PAL 'water')
    M['garden'] = F('F_ground_garden', '#97A257')
    M['terrace'] = F('F_ground_terrace', '#D9C29C')
    M['balc'] = F('F_ground_balcony', '#8E6640')
    M['awn'] = [F('F_ground_awnRed', '#B8402E'), F('F_ground_awnWhite', '#EFE7D6'), F('F_ground_awnOchre', '#C99B45')]
    M['plant'] = [F('F_ground_plant0', '#6F8A3E'), F('F_ground_plant1', '#8E9F4C')]
    M['pot'] = F('F_ground_pot', '#B4623E')
    M['kerb'] = F('F_ground_blockKerb', '#D2BC95')
    M['kerb_side'] = F('F_ground_blockKerbSide', '#B79E77')
    M['marble'] = F('F_ground_marble', '#F1EBDD')
    M['base_stain'] = F('F_ground_baseStain', '#C4A783')
    # 사람(L6)
    M['cloth'] = var_mat('F_ground_cloth', [(0.0, '#EFE8DA'), (0.22, '#B13A2C'), (0.38, '#3E5D8C'), (0.52, '#C99B45'), (0.66, '#EFE8DA'), (0.8, '#5F7B4A')])
    M['skin'] = F('F_ground_skin', '#D8A07C')
    # 나무
    M['t_round'] = var_mat('F_ground_treeRound', [(0.0, '#7D8E42'), (0.35, '#6E8139'), (0.7, '#8A9A4C')])
    M['t_round_hi'] = var_mat('F_ground_treeRoundHi', [(0.0, '#A2AE5C'), (0.35, '#94A253'), (0.7, '#ADB766')])
    M['t_round_lo'] = var_mat('F_ground_treeRoundLo', [(0.0, '#5C6E32'), (0.5, '#55672E')])
    M['t_pine'] = var_mat('F_ground_treePine', [(0.0, '#5E7A3E'), (0.5, '#6C8846'), (0.8, '#557236')])
    M['t_pine_hi'] = var_mat('F_ground_treePineHi', [(0.0, '#86A05A'), (0.5, '#91AA62')])
    M['t_pine_lo'] = F('F_ground_treePineLo', '#46602F')
    M['t_cyp'] = var_mat('F_ground_treeCypress', [(0.0, '#3E5A33'), (0.5, '#4E6C3C'), (0.8, '#365030')])
    M['t_cyp_hi'] = F('F_ground_treeCypressHi', '#6A8A4C')
    M['t_olive'] = var_mat('F_ground_treeOlive', [(0.0, '#8D946A'), (0.5, '#A3A87C'), (0.8, '#7F8760')])
    M['t_olive_hi'] = F('F_ground_treeOliveHi', '#BABE93')
    M['t_olive_lo'] = F('F_ground_treeOliveLo', '#6C7350')
    M['bark'] = F('F_ground_bark', '#6B5240')
    M['t_ground'] = F('F_ground_treeGround', '#A7AA62')
    return M


# ───────────────────────── 메시 누적기 ─────────────────────────
class Acc:
    """여러 조각을 한 메시로 모은다. 면마다 원하는 법선 방향을 지정해 ISO_TONE 톤이 정확하게 나온다"""
    def __init__(self):
        self.bm = bmesh.new(); self.mats = []; self.idx = {}

    def mi(self, mat):
        k = mat.name
        if k not in self.idx:
            self.idx[k] = len(self.mats); self.mats.append(mat)
        return self.idx[k]

    def face(self, pts, mat, want=None):
        bm = self.bm
        f = bm.faces.new([bm.verts.new(p) for p in pts])
        f.material_index = self.mi(mat)
        if want is not None:
            f.normal_update()
            if f.normal.dot(Vector(want)) < 0:
                f.normal_flip()
        return f

    def box(self, X0, X1, Y0, Y1, Z0, Z1, mat, side=None, sides='ES', top=True):
        """평면 상자. 보이는 면만(윗면·동(+X)·남(+Y)). sides에 'W','N'을 더하면 뒤쪽 면도"""
        sd = side or mat
        if top:
            self.face([V(X0, Y0, Z1), V(X1, Y0, Z1), V(X1, Y1, Z1), V(X0, Y1, Z1)], mat, (0, 0, 1))
        if 'E' in sides:
            self.face([V(X1, Y0, Z0), V(X1, Y1, Z0), V(X1, Y1, Z1), V(X1, Y0, Z1)], sd, (1, 0, 0))
        if 'S' in sides:
            self.face([V(X0, Y1, Z0), V(X1, Y1, Z0), V(X1, Y1, Z1), V(X0, Y1, Z1)], sd, (0, -1, 0))
        if 'W' in sides:
            self.face([V(X0, Y0, Z0), V(X0, Y1, Z0), V(X0, Y1, Z1), V(X0, Y0, Z1)], sd, (-1, 0, 0))
        if 'N' in sides:
            self.face([V(X0, Y0, Z0), V(X1, Y0, Z0), V(X1, Y0, Z1), V(X0, Y0, Z1)], sd, (0, 1, 0))

    def prism(self, pts, Z0, Z1, mat_top, mat_side, top=True):
        """평면 다각형 기둥(보이는 옆면만: 바깥 법선 nx+ny>0)"""
        if top:
            self.face([V(X, Y, Z1) for X, Y in pts], mat_top, (0, 0, 1))
        if mat_side is None or Z1 - Z0 < 1e-6:
            return
        n = len(pts); A = 0.0
        for k in range(n):
            (Xa, Ya), (Xb, Yb) = pts[k], pts[(k + 1) % n]
            A += Xa * Yb - Xb * Ya
        sg = 1.0 if A > 0 else -1.0
        for k in range(n):
            (Xa, Ya), (Xb, Yb) = pts[k], pts[(k + 1) % n]
            dx, dy = Xb - Xa, Yb - Ya
            nx, ny = sg * dy, -sg * dx
            if nx + ny <= 1e-9:
                continue
            self.face([V(Xa, Ya, Z0), V(Xb, Yb, Z0), V(Xb, Yb, Z1), V(Xa, Ya, Z1)], mat_side, (nx, -ny, 0))

    def blob(self, cx, cy, cz, rx, ry, rz, mat, sub=1, jit=0.16, seed=0.0, mat_hi=None, mat_lo=None):
        """잎 덩이(L0/L3 다면체). 윗면 쪽 면은 하이라이트(L5), 아래쪽은 그늘색(L1)"""
        bm = self.bm
        res = bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
        vs = res['verts']
        for v in vs:
            d = v.co.copy()
            j = 1.0 + jit * (hsh(d.x * 13.1 + seed, d.y * 7.7, d.z * 5.3) * 2 - 1)
            v.co = Vector((cx + d.x * rx * j, -(cy) + d.y * ry * j, cz + d.z * rz * j))
        fs = list({f for v in vs for f in v.link_faces})
        i0, ih, il = self.mi(mat), self.mi(mat_hi or mat), self.mi(mat_lo or mat)
        for f in fs:
            f.normal_update()
            nz = f.normal.z
            if mat_hi is not None and nz > 0.5 and (f.normal.x + f.normal.y) < 0.35:
                f.material_index = ih
            elif mat_lo is not None and nz < -0.15:
                f.material_index = il
            else:
                f.material_index = i0
        return fs

    def cyl(self, X, Y, r, Z0, Z1, mat, n=8, top=True):
        pts = [(X + r * math.cos(2 * math.pi * k / n), Y + r * math.sin(2 * math.pi * k / n)) for k in range(n)]
        self.prism(pts, Z0, Z1, mat, mat, top)

    def obj(self, name, coll, parent=None):
        bm = self.bm
        if not bm.faces:
            bm.free(); return None
        G.uv_box(bm, bm.faces[:])
        ob = R.bm_to_obj(bm, name, self.mats, coll, parent, False, recalc=False)
        return ob


# ───────────────────────── 기하 도구 ─────────────────────────
def clip_half(poly, f):
    """f(p) <= 0 인 쪽만 남김(Sutherland–Hodgman, 선형 f). 겹친 점은 하나로"""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        fa, fb = f(a), f(b)
        if fa <= 0:
            out.append(a)
        if (fa <= 0) != (fb <= 0):
            t = fa / (fa - fb)
            out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
    ded = []
    for p in out:
        if not ded or abs(ded[-1][0] - p[0]) > 1e-4 or abs(ded[-1][1] - p[1]) > 1e-4:
            ded.append(p)
    if len(ded) > 2 and abs(ded[0][0] - ded[-1][0]) < 1e-4 and abs(ded[0][1] - ded[-1][1]) < 1e-4:
        ded.pop()
    return ded


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    qx, qy = ax + t * dx, ay + t * dy
    return math.hypot(px - qx, py - qy)


def pip(x, y, poly):
    ins = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]; xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            ins = not ins
        j = i
    return ins


def sbox(X0, X1, Y0, Y1, h):
    """평면 상자(높이 h)의 화면 외곽"""
    return (C30 * (X0 - Y1), 0.5 * (X0 + Y0) - h, C30 * (X1 - Y0), 0.5 * (X1 + Y1))


def ov(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def scene_boxes(m=2.0, amax=2500.0):
    """다른 패키지(OTHER_COLLS)가 실제로 지은 보이는 메시의 화면 외곽(+m). 읽기만 한다.
    큰 덩어리(랜드마크 본체, 화면 넓이 > amax)는 spec 투영 상자로 막으므로 뺀다 — 길게 뻗은 열(가로수 등)이 큰 사각형으로 막지 않게"""
    out = []
    for cn in OTHER_COLLS:
        c = bpy.data.collections.get(cn)
        if c is None:
            continue
        for ob in c.all_objects:
            if ob.type != 'MESH' or ob.hide_render or ob.name.startswith('X_CUT_'):
                continue
            mw = ob.matrix_world
            pts = [R.scr(mw @ Vector(cr)) for cr in ob.bound_box]
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            b = (min(xs), min(ys), max(xs), max(ys))
            if (b[2] - b[0]) * (b[3] - b[1]) > amax or b[2] < -5 or b[0] > 425 or b[3] < 85 or b[1] > 510:
                continue
            out.append((b[0] - m, b[1] - m, b[2] + m, b[3] + m))
    return out


def _drawn():
    try:
        return json.load(open(DRAWN, encoding='utf-8'))
    except Exception:
        return {}


def floor_text_boxes(CM):
    """바닥 글 블록(화면 상자). 설계 drawn.json의 실제 그린 외곽이 우선, 없으면 spec 기준점·길이로 어림"""
    D = _drawn()
    bx = [tuple(t['bbox']) for t in D.get('texts', []) if t.get('layer') == '바닥 글' and t.get('bbox')]
    if bx:
        return bx
    for f in CM['labels'].get('floor_text', []):
        (ax, ay), L = f['anchor'], f.get('len', 30.0)
        up = '↗' in f.get('baseline', '')
        ex, ey = C30 * L, (-0.5 if up else 0.5) * L
        bx.append((min(ax, ax + ex) - 1.0, min(ay, ay + ey) - 4.0, max(ax, ax + ex) + 1.0, max(ay, ay + ey) + 9.0))
    return bx


def leader_lines(S_):
    """정보 층 지시선(화면 폴리라인). drawn.json 라벨·지시선 + spec Detail 지시선. 옛 '기초 절개 → Z1'은 D5 새 지시선으로 바꾼다"""
    D = _drawn()
    out = []
    for L in D.get('labels', []):
        ld = L.get('leader') or {}
        if ld.get('pts'):
            out.append([tuple(p) for p in ld['pts']])
    src = D.get('leaders') or S_.get('detail', {}).get('leaders', [])
    for L in src:
        if '기초 절개' in L.get('name', '') or '기초 절개' in L.get('target', ''):
            continue
        if L.get('pts'):
            out.append([tuple(p) for p in L['pts']])
    out.append([(232.0, 396.8), (272.38, 420.11)])       # D5: 공사장 거푸집 오른쪽 면 → Z1 원(↘30°, 꺾임 0)
    return out


def rb(theta):
    """조경 경계(판석 경계였던 선) 반지름(평면): 84.5 + 3·sin(3θ+0.7) + 1.5·sin(7θ+0.2) (D3)"""
    return 84.5 + 3.0 * math.sin(3 * theta + 0.7) + 1.5 * math.sin(7 * theta + 0.2)


class World:
    """금지 구역(화면 상자·지시선·길·강·히어로 군)과 점유(평면 격자)"""
    def __init__(self, S_, CM):
        self.CM = CM
        # D14 비움 구역(집·나무·소품·밭·땅 결 0). 상자·좌표 하드코딩 없이 spec(current)·drawn.json·장면에서 읽는다(D1)
        lm = [L['projected_box'] for L in CM['landmarks']] + ([b['projected_box'] for b in CM['background']] if DECOR else [])
        self.k_land = [(b[0] - 2.0, b[1] - 2.0, b[2] + 2.0, b[3] + 2.0) for b in lm]          # 랜드마크 투영 상자 +2 mm
        hb = HERO_BLDG                                                                           # 콜로세움 건물 + 윗선 위 5 mm(실루엣 또렷)
        self.k_land.append((hb[0] - 3.0, hb[1] - 5.0, hb[2] + 3.0, hb[3] + 2.0))
        pr = [p['box'] for p in CM['props'] if DECOR or '네로' in p.get('name', '')]      # 16:14: 지운 소품 상자는 비우지 않는다
        nb = CM.get('nero_colossus', {}).get('box')
        pr += ([NERO_YARD, WORKSITE] if DECOR else [NERO_YARD]) + ([nb] if nb else [])
        hz = CM['hero'].get('worksite', {}).get('box')
        if hz and DECOR:
            pr.append(hz)
        br = CM.get('bridge', {}).get('polys_screen') or []
        for pl in br:
            xs = [p[0] for p in pl]; ys = [p[1] for p in pl]
            pr.append((min(xs), min(ys), max(xs), max(ys)))
        self.k_prop = [(b[0] - 2.0, b[1] - 2.0, b[2] + 2.0, b[3] + 2.0) for b in pr]
        self.k_prop += scene_boxes(2.0)          # 다른 패키지가 실제로 지은 작은 오브젝트(소품·나무·사람·부속 건물) +2 mm
        # 라벨: 글 블록·말풍선·깃대 자리(D14). 설계가 실제로 그린 글 블록(drawn.json labels[].poly, 정보 층 글자 외곽)이 우선이고,
        #   없으면 spec labels[].block_poly, 그것도 없으면 슬롯 상자. 슬롯 상자 전체를 비우면 지도 20%가 빈다(b5 시험 1회차 실측)
        lab = []
        D = _drawn()
        for L in D.get('labels', []):
            pl = L.get('poly')
            if pl:
                xs = [p[0] for p in pl]; ys = [p[1] for p in pl]
                lab.append((min(xs), min(ys), max(xs), max(ys)))
        for t in D.get('texts', []):
            ly = t.get('layer', '')
            if t.get('bbox') and (ly.startswith('지도 라벨') or ly.startswith('말풍선') or ly.startswith('지도 소품 글') or ly.startswith('짝 표지 map')):
                lab.append(tuple(t['bbox']))
        if not lab:
            for s in CM['labels']['slots']:
                bp = s.get('block_poly')
                if bp:
                    xs = [p[0] for p in bp]; ys = [p[1] for p in bp]
                    lab.append((min(xs), min(ys), max(xs), max(ys)))
                elif s.get('box'):
                    lab.append(tuple(s['box']))
        pans = [p['rect'] for p in S_['basic']['panels']] + [S_['detail']['panel']['rect'], S_['support']['panel']['rect']]
        det = []
        for me in S_['detail']['map_elements']:
            if 'circle' in me:
                c = me['circle']['c']; r = me['circle']['d'] / 2
                det.append((c[0] - r, c[1] - r, c[0] + r, c[1] + r))
                if me.get('text_box'):                    # d5: 글 상자가 없는 원형 표지도 있다
                    det.append(me['text_box'])
            elif 'box' in me:
                det.append(me['box'])
        ttl = S_.get('frame', {}).get('title', {}).get('rect')
        self.k_info = [(b[0] - 1.5, b[1] - 1.5, b[2] + 1.5, b[3] + 1.5) for b in lab + pans + det + ([ttl] if ttl else [])]
        self.k_text = [(b[0] - 1.5, b[1] - 1.5, b[2] + 1.5, b[3] + 1.5) for b in floor_text_boxes(CM)]   # 바닥 글 블록 +1.5 mm
        self.leaders = leader_lines(S_)
        self.roads = []
        for r in CM['roads']:
            if len(r.get('plan_pts', [])) != 2 or r.get('id') in ROUTE_IDS:      # d5 R_route(꺾은선)는 build_route가 맡는다
                continue
            (X0, Y0), (X1, Y1) = r['plan_pts']; hw = r['w_screen_perp_mm'] / C30 / 2.0
            if abs(X0 - X1) < 1e-6:
                lo, hi = min(Y0, Y1), max(Y0, Y1)
                if r['id'] == 'R7':
                    lo = min(lo, R7_NORTH_Y)          # D3: R7 북쪽 끝 (489.6, 250.4)
                rect = (X0 - hw, X0 + hw, lo, hi); ax = 'Y'
            else:
                rect = (min(X0, X1), max(X0, X1), Y0 - hw, Y0 + hw); ax = 'X'
            self.roads.append({'id': r['id'], 'rect': rect, 'axis': ax, 'hw': hw, 'cl': r.get('center_line', False)})
        if not DECOR:
            self.roads = []                    # 16:14: 길 0 → 땅 결이 길 자리도 채운다
        self.occ = {}
        self.CELL = 6.0

    # 평면 사각형 점유
    def _cells(self, X0, X1, Y0, Y1):
        c = self.CELL
        for i in range(int(math.floor(X0 / c)), int(math.floor(X1 / c)) + 1):
            for j in range(int(math.floor(Y0 / c)), int(math.floor(Y1 / c)) + 1):
                yield (i, j)

    def occupy(self, X0, X1, Y0, Y1, tag='x'):
        r = (X0, X1, Y0, Y1, tag)
        for k in self._cells(X0, X1, Y0, Y1):
            self.occ.setdefault(k, []).append(r)

    def occupied(self, X0, X1, Y0, Y1, ignore=()):
        for k in self._cells(X0, X1, Y0, Y1):
            for r in self.occ.get(k, ()):
                if r[4] in ignore:
                    continue
                if X0 < r[1] and r[0] < X1 and Y0 < r[3] and r[2] < Y1:
                    return True
        return False

    def road_hit(self, X0, X1, Y0, Y1, m):
        for rd in self.roads:
            a = rd['rect']
            if X0 < a[1] + m and a[0] - m < X1 and Y0 < a[3] + m and a[2] - m < Y1:
                return True
        return False

    def river_hit(self, X0, X1, Y0, Y1, m):
        if GENERIC_RIVER and RV is not None:
            cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2
            hd = 0.5 * math.hypot(X1 - X0, Y1 - Y0)
            if RV.near(cx, cy, m + hd):
                return True
            return any(X0 - m <= px <= X1 + m and Y0 - m <= py <= Y1 + m for px, py in RV.rp)
        if Y1 > A1_Y0 - m and Y0 < A1_Y1 + m and X0 < A2_X1 + m:
            return True
        if X1 > A2_X0 - m and X0 < A2_X1 + m and Y1 > A1_Y0 - m:
            return True
        return False

    def river_near(self, X, Y, m):
        """실제 강 다각형(spec polygon_screen → 평면) 안이거나 경계에서 m 안이면 True(굽이 바깥 모서리 둥근 부분의 땅을 살린다)"""
        if GENERIC_RIVER and RV is not None:
            return RV.near(X, Y, m)
        rp = getattr(self, 'rp', None)
        if not rp:
            return True
        if pip(X, Y, rp):
            return True
        n = len(rp)
        for i in range(n):
            (ax, ay), (bx, by) = rp[i], rp[(i + 1) % n]
            if seg_dist(X, Y, ax, ay, bx, by) < m:
                return True
        return False

    def hero_hit(self, X0, X1, Y0, Y1, r):
        cx = min(max(HERO_C[0], X0), X1); cy = min(max(HERO_C[1], Y0), Y1)
        return math.hypot(cx - HERO_C[0], cy - HERO_C[1]) < r

    def screen_hit(self, sb, lists):
        for L in lists:
            if L is self.k_land:
                if self.land_hit(sb):
                    return True
                continue
            for b in L:
                if ov(sb, b):
                    return True
        return False

    def land_hit(self, sb):
        """랜드마크 투영 상자 +2 mm와 겹치는가(D14: 모서리 예외 없음 — 사용자 13:33 '건물 실루엣이 땅 위에서 또렷하게')"""
        for b in self.k_land:
            if ov(sb, b):
                return True
        return False

    def leader_hit(self, sb, m=2.0):
        cx, cy = (sb[0] + sb[2]) / 2, (sb[1] + sb[3]) / 2
        rr = math.hypot(sb[2] - sb[0], sb[3] - sb[1]) / 2
        for pl in self.leaders:
            for (ax, ay), (bx, by) in zip(pl[:-1], pl[1:]):
                if seg_dist(cx, cy, ax, ay, bx, by) < rr + m:
                    return True
        return False

    def stage_ok(self, sb):
        """무대 [0, 92]~[420, 505] 안(D12·사용자 13:40): 땅 위 요소는 y 505에서 멈추고, 화면 윗끝 ≥ 93. 좌우는 블리드"""
        x0, y0, x1, y1 = sb
        if x0 < STAGE[0] - 3.0 or x1 > STAGE[2] + 3.0 or y1 > STAGE[3]:
            return False
        return y0 >= TOP_MIN


# ───────────────────────── 땅 판(L0)·물길·절단체 ─────────────────────────
# ───────────────────────── 강 일반 기하(17:22 사용자: 강 경로 재설계 대비) ─────────────────────────
#   spec core_map.river에 centerline_plan(평면 꺾은선)·width_plan(한 값 또는 점마다)이 있으면 그것으로 강 다각형을 만들고,
#   없으면 polygon_screen(화면 다각형)을 평면으로 되돌린다. 둑·하구·물결·경계석·계단·갈대는 모두 이 다각형에서 계산한다(옛 두 팔 상수 A1·A2 대신)
GENERIC_RIVER = True
RV = None


def plan_width(ws, d):
    """화면 수직 폭 ws(mm) → 평면 폭: 화면 야코비안 J = [[C30, −C30], [0.5, 0.5]], det = C30 → w_p = ws·|J·d| / det"""
    jx, jy = C30 * (d[0] - d[1]), 0.5 * (d[0] + d[1])
    return ws * math.hypot(jx, jy) / C30


def river_poly_from_centerline(cl, widths, screen=True):
    """평면 꺾은선 cl과 폭(한 값 또는 꼭짓점마다)으로 강 다각형(왼쪽 변 + 뒤집은 오른쪽 변). 꺾이는 곳은 마이터(최대 2배).
    screen=True면 폭은 화면 수직 폭(mm, 설계 d5 width_plan) → 꼭짓점의 흐름 방향으로 평면 폭을 구한다"""
    n = len(cl)
    ws = [float(widths)] * n if not isinstance(widths, (list, tuple)) else [float(w) for w in widths]
    L, Rr = [], []
    for i in range(n):
        segs = []
        if i > 0:
            segs.append((cl[i - 1], cl[i]))
        if i < n - 1:
            segs.append((cl[i], cl[i + 1]))
        nx = ny = 0.0
        for (a, b) in segs:
            dx, dy = b[0] - a[0], b[1] - a[1]; l_ = math.hypot(dx, dy) or 1.0
            nx += -dy / l_; ny += dx / l_
        l_ = math.hypot(nx, ny) or 1.0
        nx, ny = nx / l_, ny / l_
        k = 1.0
        if len(segs) == 2:
            (a, b) = segs[0]; dx, dy = b[0] - a[0], b[1] - a[1]; l0 = math.hypot(dx, dy) or 1.0
            cosh = abs(nx * (-dy / l0) + ny * (dx / l0))
            k = min(2.0, 1.0 / max(cosh, 0.5))
        if screen:
            dx_, dy_ = ny, -nx                                     # 흐름 방향(법선에 수직)
            w_i = plan_width(ws[i], (dx_, dy_))
        else:
            w_i = ws[i]
        h = w_i / 2.0 * k
        L.append((cl[i][0] + nx * h, cl[i][1] + ny * h)); Rr.append((cl[i][0] - nx * h, cl[i][1] - ny * h))
    return L + Rr[::-1]


def _poly_of(rv):
    cl = rv.get('centerline_plan')
    if cl and len(cl) >= 2:
        w = rv.get('width_plan')                                       # 설계 d5: 꼭짓점별 화면 수직 폭 mm
        if w is None:
            ws = rv.get('width_screen_perp_mm')
            w = ws if isinstance(ws, (int, float)) else 16.0
        return river_poly_from_centerline([tuple(p) for p in cl], w, screen=True)
    if rv.get('polygon_screen'):
        return [R.to_plan(x, y) for x, y in rv['polygon_screen']]
    return None


def river_polygons(CM):
    """[본류, 지류…] 평면 다각형. 지류 = river 안에서 centerline_plan을 가진 dict(목록·사전 어디든, 예: tributaries·aniene).
    지류 첫 점이 본류 밖이면 거꾸로 3 mm 늘여 본류 물 안에서 시작하게 한다(합류부 틈 0)"""
    rv = CM.get('river', {})
    main = _poly_of(rv)
    polys = [main] if main else []
    tribs = []
    def walk(o, depth=0):
        if depth > 3:
            return
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, dict) and v.get('centerline_plan') and v is not rv:
                    tribs.append(v)
                elif isinstance(v, list):
                    for it in v:
                        if isinstance(it, dict) and it.get('centerline_plan'):
                            tribs.append(it)
    walk(rv)
    for tv in tribs:
        cl = [tuple(p) for p in tv['centerline_plan']]
        if len(cl) < 2:
            continue
        if main and not pip(cl[0][0], cl[0][1], main):
            dx, dy = cl[0][0] - cl[1][0], cl[0][1] - cl[1][1]; l_ = math.hypot(dx, dy) or 1.0
            cl = [(cl[0][0] + dx / l_ * 3.0, cl[0][1] + dy / l_ * 3.0)] + cl
            tv = dict(tv); w = tv.get('width_plan')
            if isinstance(w, (list, tuple)):
                tv['width_plan'] = [w[0]] + list(w)
        w = tv.get('width_plan', tv.get('width_screen_perp_mm', 7.5))
        polys.append(river_poly_from_centerline(cl, w, screen=True))
    return polys


def river_polygon(CM):
    ps = river_polygons(CM)
    return ps[0] if ps else []


def _seg_cross_t(a, b, c, d):
    """선분 ab가 선분 cd와 만나는 ab 위 매개변수 t(0 < t < 1), 없으면 None"""
    rx, ry = b[0] - a[0], b[1] - a[1]; sx, sy = d[0] - c[0], d[1] - c[1]
    den = rx * sy - ry * sx
    if abs(den) < 1e-12:
        return None
    t = ((c[0] - a[0]) * sy - (c[1] - a[1]) * sx) / den
    u = ((c[0] - a[0]) * ry - (c[1] - a[1]) * rx) / den
    return t if (0.0 < t < 1.0 and -1e-9 <= u <= 1.0 + 1e-9) else None


class RiverGeo:
    """강 다각형들(평면: 본류 + 지류) 질의: 안·둑까지 거리·흐름 방향·하구 구간(해안선 평면 Y = COAST_Y와 만나는 X 범위)·둑 변.
    다른 강 다각형 안에 든 변(합류부)은 내부 변이라 둑·경계석·갈대에서 뺀다"""
    def __init__(self, polys):
        if polys and isinstance(polys[0][0], (int, float)):
            polys = [polys]
        self.polys = [p for p in polys if p and len(p) >= 3]
        self.rp = self.polys[0] if self.polys else []
        self.edges, self.ccws = [], []
        for pi, rp in enumerate(self.polys):
            n = len(rp)
            A = sum(rp[i][0] * rp[(i + 1) % n][1] - rp[(i + 1) % n][0] * rp[i][1] for i in range(n))
            others = [q for qi, q in enumerate(self.polys) if qi != pi]
            for i in range(n):
                a, b = rp[i], rp[(i + 1) % n]
                ts = [0.0, 1.0]                                       # 20:01: 다른 강 다각형 변과 만나는 점에서 나눈다(긴 변이 합류부를 가로지를 때)
                for q in others:
                    for j in range(len(q)):
                        t_ = _seg_cross_t(a, b, q[j], q[(j + 1) % len(q)])
                        if t_ is not None:
                            ts.append(t_)
                ts = sorted(set(round(t_, 9) for t_ in ts))
                for t0, t1 in zip(ts[:-1], ts[1:]):
                    if t1 - t0 < 1e-6:
                        continue
                    pa = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
                    pb = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
                    m = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
                    if any(pip(m[0], m[1], q) for q in others):
                        continue                                      # 합류부 내부 변
                    self.edges.append((pa, pb)); self.ccws.append(A > 0)
        self._ccw = {id(e): c for e, c in zip(self.edges, self.ccws)}
        self.ccw = self.ccws[0] if self.ccws else True
        xs = []
        for (a, b) in self.edges:
            if (a[1] - COAST_Y) * (b[1] - COAST_Y) < 0:
                t = (COAST_Y - a[1]) / (b[1] - a[1]); xs.append(a[0] + (b[0] - a[0]) * t)
        self.mouth = (min(xs), max(xs)) if len(xs) >= 2 else None

    def inside(self, X, Y):
        return any(pip(X, Y, q) for q in self.polys)

    def dist_edge(self, X, Y):
        return min(seg_dist(X, Y, a[0], a[1], b[0], b[1]) for (a, b) in self.edges)

    def near(self, X, Y, m):
        return self.inside(X, Y) or self.dist_edge(X, Y) < m

    def flow(self, X, Y):
        best = None
        for (a, b) in self.edges:
            d = seg_dist(X, Y, a[0], a[1], b[0], b[1])
            if best is None or d < best[0]:
                best = (d, a, b)
        _, a, b = best
        dx, dy = b[0] - a[0], b[1] - a[1]; l_ = math.hypot(dx, dy) or 1.0
        return dx / l_, dy / l_

    def out_normal(self, a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]; l_ = math.hypot(dx, dy) or 1.0
        nx, ny = dy / l_, -dx / l_
        mx, my = (a[0] + b[0]) / 2 + nx * 0.2, (a[1] + b[1]) / 2 + ny * 0.2
        if self.inside(mx, my):                                       # 바깥(땅) 쪽 법선: 0.2 밖이 물이면 뒤집는다
            nx, ny = -nx, -ny
        return nx, ny

    def bank_edges(self, ymax=None):
        """땅 쪽 둑 변(해안선 위, 길이 > 0.3). 긴 변은 3 mm 이하 조각으로 나눈다"""
        ymax = COAST_Y - 0.5 if ymax is None else ymax
        out = []
        for (a, b) in self.edges:
            if a[1] > ymax or b[1] > ymax:
                continue
            L_ = math.hypot(b[0] - a[0], b[1] - a[1])
            if L_ < 0.3:
                continue
            k = max(1, int(L_ / 3.0))
            for j in range(k):
                t0, t1 = j / k, (j + 1) / k
                out.append(((a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0), (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)))
        return out


def build_land(GC, M, CM, root, coast_root=None):
    # D12: 무대 [0, 92]~[420, 505]를 평면으로 되돌린 평행사변형(Z 0~−10). 위 변 = 화면 y 92 수평선, 좌우 3 mm 블리드,
    #   아래 변 = 화면 y 505(사용자 13:40: 땅 판은 무대 아랫선에서 멈춘다). 해안선(평면 Y 380) 아래는 바다
    x0, y0, x1, y1 = STAGE
    SO = [(x0 - 3.0, y0), (x1 + 3.0, y0), (x1 + 3.0, y1), (x0 - 3.0, y1)]
    land = clip_half([R.to_plan(x, y) for x, y in SO], lambda p: p[1] - COAST_Y)
    XY_BOT = 2.0 * y1           # 아래 변: 평면 X + Y = 2·505
    bm = bmesh.new()
    top = [bm.verts.new(V(X, Y, 0.0)) for X, Y in land]
    bot = [bm.verts.new(V(X, Y, -LAND_T)) for X, Y in land]
    bm.faces.new(top); bm.faces.new(bot[::-1])
    for k in range(len(top)):
        bm.faces.new([top[k], bot[k], bot[(k + 1) % len(top)], top[(k + 1) % len(top)]])
    mats_ = [M['land'], M['strata'], M['bank'], M['quay'], M['bed'], M['hold'], M['strata']]
    landob = R.bm_to_obj(bm, 'GROUND_Land_L0_Slab', mats_, GC, root)
    landob.parent = None
    # 물길: 강바닥(−3.2)까지만 판다 → 하구에서 땅 판이 뚫리지 않는다
    polys = river_polygons(CM) if GENERIC_RIVER else [[R.to_plan(x, y) for x, y in CM['river']['polygon_screen']]]
    rp = polys[0]
    global RV, A2_X0, A2_X1
    RV = RiverGeo(polys)
    if GENERIC_RIVER and RV.mouth:                                     # 하구 구간 = 강이 해안선과 만나는 X 범위(폭포·해안 단면·바다가 쓴다)
        A2_X0, A2_X1 = RV.mouth
    elif GENERIC_RIVER:                                                # 강이 바다에 닿지 않으면 해안 단면·바다에 빈 구간 0
        A2_X0, A2_X1 = -1.0e6, -1.0e6 + 0.1
    cutters = []
    for pi, poly in enumerate(polys):                                 # 본류 + 지류: 강마다 절단체(차례로 파서 합류부가 합쳐진다)
        bm = bmesh.new()
        vt = [bm.verts.new(V(X, Y, 2.0)) for X, Y in poly]
        vb = [bm.verts.new(V(X, Y, RIVER_BED)) for X, Y in poly]
        bm.faces.new(vt); bm.faces.new(vb[::-1])
        for k in range(len(vt)):
            bm.faces.new([vt[k], vb[k], vb[(k + 1) % len(vt)], vt[(k + 1) % len(vt)]])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        cutters.append(R.bm_to_obj(bm, 'GROUND_tmp_RiverCutter%d' % pi, M['bank'], GC))
    n_riv = len(cutters)
    scn = bpy.context.scene.objects
    cutters += [o for o in bpy.data.objects if o.name.startswith('X_CUT_') and o.type == 'MESH' and o.name in scn]
    for cut in cutters:
        md = landob.modifiers.new(cut.name, 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = cut; md.solver = 'EXACT'
        dg = bpy.context.evaluated_depsgraph_get()
        me2 = bpy.data.meshes.new_from_object(landob.evaluated_get(dg))
        landob.modifiers.clear(); old = landob.data; landob.data = me2; bpy.data.meshes.remove(old)
    for c0 in cutters[:n_riv]:
        cme = c0.data; bpy.data.objects.remove(c0, do_unlink=True); bpy.data.meshes.remove(cme)
    # 화면 y 505 아래로 내려가는 땅 판 부분(아래 변 옆면·해안 단면 모서리)을 자른다: 평면 0.5X + 0.5Y − Z = 505.
    #   자른 면은 카메라 시선과 나란해(법선·시선 내적 0) 화면에 보이지 않는다 → 땅은 y 505에서 칼같이 멈춘다(사용자 13:40)
    bm = bmesh.new(); bm.from_mesh(landob.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-5,
                           plane_co=Vector((y1 * 2.0, 0.0, 0.0)), plane_no=Vector((0.5, -0.5, -1.0)), clear_outer=True)
    bm.to_mesh(landob.data); bm.free()
    me = landob.data
    me.materials.clear()
    for m_ in mats_:
        me.materials.append(m_)
    # 면 분류: 윗면 땅 · 바닥(강바닥/구덩이 바닥) · 해안 단면(지층) · 강둑(시내 구간은 석축) · 아래 변(투명)
    for p in me.polygons:
        c = p.center; n = p.normal
        X, Y = c.x, -c.y
        if n.z > 0.9:
            p.material_index = 0 if c.z > -0.05 else 4
        elif n.z < -0.9:
            p.material_index = 1
        else:
            if X + Y > XY_BOT - 0.6 and abs(n.x - n.y) > 1.0:
                p.material_index = 5          # 아래 변 옆면: 투명(땅 판은 y 505에서 멈춘다)
            elif GENERIC_RIVER and Y < COAST_Y - 0.05 and c.z > RIVER_BED - 0.05 and RV.dist_edge(X, Y) < 0.8:
                near_mouth = RV.mouth is not None and RV.mouth[0] - 25.0 < X < RV.mouth[1] + 25.0 and Y > COAST_Y - 25.0
                p.material_index = 2 if near_mouth else 3      # 둑: 하구 가까이는 흙, 그 밖은 석축(일반 강)
            elif (not GENERIC_RIVER) and Y < COAST_Y - 0.05 and c.z > RIVER_BED - 0.05 and (Y > A1_Y0 - 0.6 or X > A2_X0 - 0.6) and not (Y < A1_Y0 - 0.6):
                # 석축(L2 둑 돌)은 시내 구간 북쪽 둑. 하역장 X 429~470(coast 부두)에는 둑 돌을 두지 않는다(D14)
                quay = (n.y < -0.5 and 318.0 < X < 506.0 and not (429.0 <= X <= 470.0))
                p.material_index = 3 if quay else 2
            elif abs(Y - COAST_Y) < 0.3 and n.y < -0.5:
                p.material_index = 6          # 해안선 앞면 지층 단면 10 mm(3겹) → GROUND_Coast_L0_Section
            else:
                p.material_index = 1
        p.use_smooth = False
    bm = bmesh.new(); bm.from_mesh(me); G.uv_box(bm, bm.faces[:])
    # 다른 패키지 절단체(X_CUT_*) 구덩이의 바닥은 그 패키지가 직접 깐다(예: hero H_L0_PitFloor) → 땅 판 쪽 바닥 면은 지운다
    def _river_face(f):                       # 굽은 강(오목 다각형)은 면 중심이 강 밖일 수 있다 → 꼭짓점이 둑에 닿으면 강바닥
        return any(RV.near(v.co.x, -v.co.y, 0.3) for v in f.verts)
    pit_floor = [f for f in bm.faces if f.material_index == 4 and
                 ((not _river_face(f)) if GENERIC_RIVER else -f.calc_center_median().y < A1_Y0 - 1.0)]
    if pit_floor:
        bmesh.ops.delete(bm, geom=pit_floor, context='FACES')
    bm.to_mesh(me); bm.free()
    # 레이어 분리: L1 강바닥 / L2 강둑 벽(흙·석축). 해안 단면(지층 재질)은 땅 판에 남는다
    def split(name, idxs, parent):
        bm = bmesh.new(); bm.from_mesh(me)
        kill = [f for f in bm.faces if f.material_index not in idxs]
        bmesh.ops.delete(bm, geom=kill, context='FACES')
        if not bm.faces:
            bm.free(); return None
        me2 = bpy.data.meshes.new(name); bm.to_mesh(me2); bm.free()
        for m_ in mats_:
            me2.materials.append(m_)
        ob = bpy.data.objects.new(name, me2); GC.objects.link(ob); ob.parent = parent
        return ob
    parts = {'bed': split('GROUND_Land_L1_ChannelBed', (4,), root), 'bank': split('GROUND_Land_L2_BankWalls', (2, 3), root),
             'coast': split('GROUND_Coast_L0_Section', (6,), coast_root or root)}
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in (2, 3, 4, 6)], context='FACES')
    bm.to_mesh(me); bm.free()
    return landob, rp


SIL_PAD = 1.2          # 땅 결 조각 화면 상자(+0.8)에서 이만큼 더 밖까지 건물이 없어야 한다(실루엣과 약 2 mm)


class SilCover:
    """다른 패키지(OTHER_COLLS)가 지은 보이는 메시의 BVH. 땅 점에서 카메라 쪽으로 쏜 광선이 건물에 맞으면 그 점은 건물 실루엣 안이다"""
    def __init__(self):
        import numpy as np
        from mathutils.bvhtree import BVHTree
        vs, ts = [], []
        for cn in OTHER_COLLS:
            c = bpy.data.collections.get(cn)
            if c is None:
                continue
            for ob in c.all_objects:
                if ob.type != 'MESH' or ob.hide_render or ob.name.startswith('X_CUT_') or not ob.data.polygons:
                    continue
                me = ob.data
                me.calc_loop_triangles()
                n = len(me.vertices)
                co = np.empty(n * 3, np.float64); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
                Mw = np.array(ob.matrix_world)
                w = co @ Mw[:3, :3].T + Mw[:3, 3]
                t = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get('vertices', t)
                base = len(vs)
                vs.extend(map(tuple, w.tolist()))
                ts.extend(map(tuple, (t.reshape(-1, 3) + base).tolist()))
        self.bvh = BVHTree.FromPolygons(vs, ts, all_triangles=True) if ts else None
        self.d = Vector((1.0, -1.0, 1.0)).normalized()          # 땅 → 카메라(−FWD)

    def hit(self, sx, sy):
        if self.bvh is None:
            return False
        X, Y = R.to_plan(sx, sy)
        return self.bvh.ray_cast(Vector((X, -Y, 0.02)), self.d, 2000.0)[0] is not None

    def covered(self, sb, pad):
        x0, y0, x1, y1 = sb[0] - pad, sb[1] - pad, sb[2] + pad, sb[3] + pad
        xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
        return any(self.hit(x, y) for (x, y) in ((xm, ym), (x0, y0), (x1, y0), (x0, y1), (x1, y1), (xm, y0), (xm, y1), (x0, ym), (x1, ym)))


def build_land_layers(GC, M, W, root, pitch=3.6):
    """땅 판 겉 레이어(D10 '6×6 mm보다 큰 빈 단색 면 0'): 화면 격자(피치 3.6 mm, 흔듦)마다 하나씩
    L3 짙은 흙 조각 · L4 돌멩이 · L5 밝은 흙 조각 · L6 풀 포기. 비움 구역(조경 R 90.5·랜드마크·라벨·바닥 글·공사장·네로 마당)과
    집·밭·나무·길·강 자리는 건너뛴다(L1 강바닥·L2 강둑 석축은 땅 판 면 재질)"""
    a3 = Acc(); a4 = Acc(); a5 = Acc(); a6 = Acc()
    k = 0
    x0s, y0s, x1s, y1s = STAGE
    sil = None if DECOR else SilCover()       # 16:14: 랜드마크 상자 대신 실제 실루엣 + 2 mm만 비운다(상자 안·실루엣 밖 땅도 땅 결)
    gy = y0s + 1.5; row = 0
    while gy < y1s - 0.5:
        gx = x0s - 1.0 + (pitch * 0.5 if row % 2 else 0.0)
        while gx < x1s + 1.0:
            i = row * 1000 + int(gx * 3)
            sx = gx + pitch * 0.55 * (hsh(i, 1.3) - 0.5); sy = gy + pitch * 0.55 * (hsh(i, 2.3) - 0.5)
            gx += pitch
            X, Y = R.to_plan(sx, sy)
            r = hsh(i, 5.5)
            w = 1.2 + 1.6 * hsh(i, 1.7); d = 0.9 + 1.2 * hsh(i, 2.9)
            X0, X1, Y0, Y1 = X - w / 2, X + w / 2, Y - d / 2, Y + d / 2
            sb = sbox(X0, X1, Y0, Y1, 0.8)
            if not W.stage_ok(sb) or Y1 > COAST_Y - 1.2 or W.road_hit(X0, X1, Y0, Y1, 0.5):
                continue
            if W.river_hit(X0, X1, Y0, Y1, 0.9) and W.river_near(X, Y, 0.9 + 0.5 * max(w, d)):
                continue
            if (DECOR and W.hero_hit(X0, X1, Y0, Y1, HERO_KEEP)) or W.occupied(X0, X1, Y0, Y1):   # 16:14: 예약 원 안도 땅 결(콜로세움은 k_land 상자가 비운다)
                continue
            if sil is not None:
                if W.screen_hit(sb, (W.k_text,)) or sil.covered(sb, SIL_PAD):
                    continue
            elif W.screen_hit(sb, (W.k_land, W.k_prop, W.k_text)):
                continue
            if W.screen_hit(sb, (W.k_info,)):
                continue          # 라벨·패널 밑 고요한 영역은 평지 땅 그대로(D10 예외: 라벨 비움 구역의 평지 땅)
            quiet = False
            if r < 0.34:
                pts = []
                for t in range(10):       # 둥근 얼룩(흙결): 반지름을 흔든 타원
                    a_ = 2 * math.pi * t / 10; rr = 0.78 + 0.32 * hsh(i, t, 8.2)
                    pts.append((X + 0.5 * w * rr * math.cos(a_), Y + 0.5 * d * rr * math.sin(a_)))
                if quiet:
                    a5.prism(pts, 0.0, 0.05, M['land_patch2'], None)
                elif hsh(i, 9.1) < 0.55:
                    a3.prism(pts, 0.0, 0.05, M['land_patch'], None)
                else:
                    a5.prism(pts, 0.0, 0.05, M['land_patch2'], None)
            elif r < 0.52:
                for t in range(2 + int(3 * hsh(i, 6.1))):
                    tx = X0 + w * hsh(i, t, 1.7); ty = Y0 + d * hsh(i, t, 2.7); rr = 0.16 + 0.2 * hsh(i, t, 3.7)
                    a4.blob(tx, ty, rr * 0.3, rr * 1.2, rr, rr * 0.6, M['rock'] if t % 2 else M['land_dot'], 0, 0.2, i + t, M['rock_top'])
            else:
                for t in range(3 + int(4 * hsh(i, 6.6))):
                    tx = X0 + w * hsh(i, t, 1.1); ty = Y0 + d * hsh(i, t, 2.2)
                    hh = 0.4 + 0.4 * hsh(i, t, 3.3)
                    mt = (M['tuft'], M['tuft2'], M['tuft3'])[int(3 * hsh(i, t, 4.4)) % 3]
                    a6.face([V(tx - 0.26, ty, 0.0), V(tx + 0.26, ty, 0.0), V(tx + 0.05, ty, hh)], mt, (0, -1, 0))
                    a6.face([V(tx, ty - 0.22, 0.0), V(tx, ty + 0.22, 0.0), V(tx + 0.02, ty, hh * 0.85)], mt, (1, 0, 0))
            k += 1
        gy += pitch * 0.866; row += 1
    a3.obj('GROUND_Land_L3_SoilPatches', GC, root); a4.obj('GROUND_Land_L4_Stones', GC, root)
    a5.obj('GROUND_Land_L5_LightPatches', GC, root); a6.obj('GROUND_Land_L6_Tufts', GC, root)
    return k


# ───────────────────────── 해안 지층 단면 ─────────────────────────
def _strata_w(s):
    """지층 경계 물결(재질 strata와 같은 식): s = 평면 X + Y"""
    return 0.38 * math.sin(s * 0.19) + 0.22 * math.sin(s * 0.53 + 1.7)


def coast_xmax():
    """해안선(평면 Y = COAST_Y)이 무대 아랫선(화면 y1)과 만나는 평면 X: 0.5·(X + COAST_Y) = y1"""
    return 2.0 * STAGE[3] - COAST_Y


FALL_GAP = (435.0, 439.0)   # 외항 쪽 운하 폭포(coast, 평면 X 435.5~438.5, Y 380.05) 앞 해안 단면 덧장식 빼는 구간


def build_coast(GC, M, root):
    a1 = Acc(); a2 = Acc(); a3 = Acc(); a4 = Acc(); a5 = Acc(); a6 = Acc()
    yf = COAST_Y + 0.04
    xm = coast_xmax()                   # 17:34: 땅이 끝나는 화면 y1(무대 아랫선)에서 해안 단면도 멈춘다(하단 띠 밑 바다 위에 떠 있지 않게)
    segs = [q for q in ((376.0, min(A2_X0 - 0.3, xm)), (A2_X1 + 0.3, min(757.0, xm))) if q[1] - q[0] > 0.3]
    fg = FALL_GAP                       # coast 요청: 외항 쪽 운하 폭포 앞은 덧장식(지층선·자갈·매달린 풀·물자국) 0(폭포 판과 간격 < 0.05)
    segs_d = []
    for X0, X1 in segs:
        segs_d += [q for q in ((X0, min(X1, fg[0] - 0.6)), (max(X0, fg[1]), X1)) if q[1] - q[0] > 0.3]   # 풀 폭(≤ 1.2)이 넘어가지 않게 −0.6
    # L2 3겹 지층의 경계선(표토|붉은 화산재 −2.6, 화산재|응회암 −6.3) — 단면 재질의 띠와 같은 물결
    for X0, X1 in segs_d:
        for zc in (-2.6, -6.3):
            n = max(2, int((X1 - X0) / 0.8))
            up = [(X0 + (X1 - X0) * t / n, zc - _strata_w(X0 + (X1 - X0) * t / n + COAST_Y) + 0.09) for t in range(n + 1)]
            lo = [(x, z - 0.2) for x, z in up]
            a2.face([V(x, yf - 0.02, z) for x, z in up] + [V(x, yf - 0.02, z) for x, z in lo[::-1]], M['root_dk'], (0, -1, 0))
    # L3 자갈(응회암·화산재 층의 밝은 돌 조각)
    for j in range(170):
        X = 378.0 + 376.0 * hsh(j, 2.4)
        if A2_X0 - 0.8 < X < A2_X1 + 0.8 or fg[0] - 0.4 < X < fg[1] + 0.4 or X > xm - 0.4:
            continue
        z = -3.2 - 6.0 * hsh(j, 3.6)
        if z < SEA_Z + 0.4:
            continue
        r = 0.18 + 0.3 * hsh(j, 4.8)
        a3.face([V(X + r * math.cos(2 * math.pi * k / 6), yf - 0.01, z + r * 0.7 * math.sin(2 * math.pi * k / 6)) for k in range(6)],
                M['rock_top'] if z < -6.4 else M['land_patch2'], (0, -1, 0))
    # L5 해안 윗선(땅 윗면 가장자리의 밝은 띠). 하구 제외
    for X0, X1 in segs:
        a5.face([V(X0, COAST_Y - 0.55, 0.05), V(X1, COAST_Y - 0.55, 0.05), V(X1, COAST_Y, 0.05), V(X0, COAST_Y, 0.05)], M['lip'], (0, 0, 1))
    # L6 매달린 풀(윗선 위로 솟고 단면으로 늘어진다)
    i = 0
    for X0, X1 in segs_d:
        X = X0
        while X < X1 - 0.6:
            w = 0.5 + 0.7 * hsh(i, 1.3)
            if hsh(i, 2.7) < 0.78:
                hang = 0.35 + 0.9 * hsh(i, 3.9); up = 0.25 + 0.35 * hsh(i, 4.1)
                mt = (M['tuft'], M['tuft2'], M['tuft3'])[i % 3]
                a6.face([V(X, yf, -hang * 0.5), V(X + w, yf, -hang * 0.3), V(X + w * 0.55, yf, -hang), ], mt, (0, -1, 0))
                a6.face([V(X, yf, 0.0), V(X + w, yf, 0.0), V(X + w * 0.5, yf, up)], mt, (0, -1, 0))
                a6.face([V(X + w * 0.1, yf, -0.05), V(X + w * 0.9, yf, -0.05), V(X + w * 0.9, yf, -hang * 0.42), V(X + w * 0.1, yf, -hang * 0.36)], mt, (0, -1, 0))
            X += w + 0.15 + 0.9 * hsh(i, 5.2); i += 1
    # L6 물자국(빗물 흘러내린 짙은 줄)
    for j in range(95):
        X = 378.0 + 376.0 * hsh(j, 8.1)
        if A2_X0 - 1.0 < X < A2_X1 + 1.0 or fg[0] - 0.5 < X < fg[1] or X > xm - 0.6:
            continue
        w = 0.18 + 0.32 * hsh(j, 8.7); z1 = -0.9 - 1.0 * hsh(j, 9.3); z0 = z1 - 1.5 - 4.5 * hsh(j, 9.9)
        a6.face([V(X, yf + 0.01, z0), V(X + w, yf + 0.01, z0 + 0.3), V(X + w, yf + 0.01, z1), V(X, yf + 0.01, z1)], M['stain'], (0, -1, 0))
    # L1 해식굴(물가의 짙은 홈)
    for j, X in enumerate(x_ for x_ in (392.0, 476.0, 503.0, 566.0, 611.0, 664.0, 703.0) if x_ < xm - 4.0):
        w = 2.2 + 1.6 * hsh(j, 1.1); hh = 1.2 + 1.2 * hsh(j, 2.2)
        pts = [V(X + w * (0.5 - 0.5 * math.cos(math.pi * t / 8)), yf + 0.015, SEA_Z + hh * math.sin(math.pi * t / 8)) for t in range(9)]
        a1.face(pts, M['cave'], (0, -1, 0))
    # L4 바위(물가에 무너진 덩이)
    for j in range(46):
        X = 380.0 + 372.0 * hsh(j, 4.4)
        if A2_X0 - 4.0 < X < A2_X1 + 4.0 or 404.0 < X < 472.0 or X > xm - 1.0:
            continue
        r = 0.6 + 1.0 * hsh(j, 4.9)
        a4.blob(X, COAST_Y + 0.4 + 1.2 * hsh(j, 5.3), SEA_Z + r * 0.25, r * 1.2, r * 0.9, r * 0.7, M['rock'], 1, 0.2, j, M['rock_top'], None)
    a1.obj('GROUND_Coast_L1_Caves', GC, root); a2.obj('GROUND_Coast_L2_StrataLines', GC, root); a3.obj('GROUND_Coast_L3_Pebbles', GC, root)
    a4.obj('GROUND_Coast_L4_Rocks', GC, root); a5.obj('GROUND_Coast_L5_Lip', GC, root); a6.obj('GROUND_Coast_L6_GrassStains', GC, root)


# ───────────────────────── 테베레강 ─────────────────────────
def build_river(GC, M, rp, root):
    clipY = lambda p: p[1] - COAST_Y
    water = clip_half(rp, clipY)
    a1 = Acc(); a0 = Acc(); a3 = Acc(); a5 = Acc(); a2 = Acc(); a4 = Acc(); a6 = Acc()
    a1.face([V(X, Y, RIVER_Z) for X, Y in water], M['r_deep'], (0, 0, 1))
    sh = 1.55     # 화면 아래로 1.55mm 민 물 면 → 보이는 둑(먼 쪽) 밑에 짙은 물 띠(L1)
    w2 = clip_half([(X + sh, Y + sh) for X, Y in rp], clipY)
    a0.face([V(X, Y, RIVER_Z + 0.05) for X, Y in w2], M['river'], (0, 0, 1))
    # L3 물결(흐름 방향 짧은 둥근 획), L5 반짝임
    def dash(X, Y, L, w, along, mat, acc, z):
        if along == 'X':
            pts = [(X - L / 2, Y), (X - L / 2 + w, Y - w / 2), (X + L / 2 - w, Y - w / 2), (X + L / 2, Y), (X + L / 2 - w, Y + w / 2), (X - L / 2 + w, Y + w / 2)]
        else:
            pts = [(X, Y - L / 2), (X + w / 2, Y - L / 2 + w), (X + w / 2, Y + L / 2 - w), (X, Y + L / 2), (X - w / 2, Y + L / 2 - w), (X - w / 2, Y - L / 2 + w)]
        acc.face([V(px, py, z) for px, py in pts], mat, (0, 0, 1))
    i = 0
    X = 300.0
    while X < A2_X0 - 3.0:
        for row, yy in enumerate((308.6, 312.4, 316.0, 319.6)):
            if hsh(i, row, 1.7) < 0.42:
                x = X + 4.0 * hsh(i, row, 2.3); sx = C30 * (x - yy)
                if sx < 58.0:      # TIBERIS 바닥 글 자리
                    continue
                L = 2.6 + 3.2 * hsh(i, row, 3.1)
                dash(x, yy + 0.8 * (hsh(i, row, 4.4) - 0.5), L, 0.42, 'X', M['r_wave'], a3, RIVER_Z + 0.10)
                if hsh(i, row, 5.5) < 0.18:
                    dash(x + L * 0.7, yy - 0.9, 1.1, 0.26, 'X', M['glint'], a5, RIVER_Z + 0.15)
        X += 6.5; i += 1
    Y = 330.0
    while Y < COAST_Y - 2.5:
        for col, xx in enumerate((525.4, 530.0, 534.6, 539.2)):
            if hsh(i, col, 1.9) < 0.45:
                y = Y + 4.0 * hsh(i, col, 2.1)
                L = 2.6 + 3.0 * hsh(i, col, 3.7)
                if y + L / 2 > COAST_Y - 1.0:
                    continue
                dash(xx + 0.8 * (hsh(i, col, 4.8) - 0.5), y, L, 0.42, 'Y', M['r_wave'], a3, RIVER_Z + 0.10)
                if hsh(i, col, 6.1) < 0.2:
                    dash(xx - 0.9, y + L * 0.6, 1.1, 0.26, 'Y', M['glint'], a5, RIVER_Z + 0.15)
        Y += 6.5; i += 1
    # L2 둑 경계석(시내 구간). 하역장(coast, 평면 X 약 429~483)·아일리우스 다리 자리는 비운다. 석축은 땅 판 둑 면(F_ground_quay)
    # 통합(b1): 오른쪽 둑 경계석은 X 435.0에서 끊는다 — coast 강 쪽 운하(X 435.2~438.8) 입구를 가로막지 않게
    for X0, X1, Y0, Y1 in ((318.0, 426.0, A1_Y0 - 0.8, A1_Y0), (318.0, 435.0, A1_Y1, A1_Y1 + 0.8)):
        a2.box(X0, X1, Y0, Y1, 0.0, 0.32, M['curb'], M['curb'], 'ES')
        a5.face([V(X0, Y0 + 0.0, 0.325), V(X1, Y0, 0.325), V(X1, Y0 + 0.22, 0.325), V(X0, Y0 + 0.22, 0.325)], M['curb_hi'], (0, 0, 1))
    # L4 계단(석축에서 물로 내려가는 층계) · 계선주
    for k, X in enumerate((346.0, 397.0)):
        for s in range(5):
            z = -0.4 * (s + 1)
            a4.box(X, X + 3.2, A1_Y0, A1_Y0 + 0.45 * (s + 1), z - 0.4, z, M['quay'], M['quay'], 'ES')
    for k in range(8):
        X = 326.0 + 13.0 * k + 2.0 * hsh(k, 7.7)
        if X > 424.0:
            break
        a4.cyl(X, A1_Y0 - 0.45, 0.22, 0.32, 0.9, M['bark'], 6)
    # L6 갈대(자연 둑): ↘ 팔 서쪽 끝·↙ 팔 양쪽
    def reed(X, Y, seed):
        for t in range(4):
            dx = 0.5 * (hsh(seed, t, 1.1) - 0.5); dy = 0.5 * (hsh(seed, t, 2.1) - 0.5)
            hh = 0.9 + 0.9 * hsh(seed, t, 3.1)
            mt = M['reed'] if t % 2 == 0 else M['reed2']
            a6.face([V(X + dx - 0.16, Y + dy, RIVER_Z), V(X + dx + 0.16, Y + dy, RIVER_Z), V(X + dx + 0.05, Y + dy, RIVER_Z + hh)], mt, (0, -1, 0))
    j = 0
    X = 300.0
    while X < 316.0:
        reed(X, A1_Y0 + 0.5, j); reed(X + 2.0, A1_Y1 - 0.4, j + 50); X += 3.0 + 3.0 * hsh(j, 9.9); j += 1
    Y = 330.0
    while Y < COAST_Y - 3.0:
        if hsh(j, 4.2) < 0.55:
            reed(A2_X0 + 0.5, Y, j)
        if hsh(j, 4.9) < 0.45:
            reed(A2_X1 - 0.4, Y + 1.5, j + 80)
        Y += 3.2 + 2.5 * hsh(j, 5.6); j += 1
    a1.obj('GROUND_River_L1_DeepWater', GC, root); a0.obj('GROUND_River_L0_Water', GC, root); a3.obj('GROUND_River_L3_Waves', GC, root)
    a5.obj('GROUND_River_L5_Glints', GC, root); a2.obj('GROUND_River_L2_Kerbs', GC, root); a4.obj('GROUND_River_L4_StairsBollards', GC, root)
    a6.obj('GROUND_River_L6_Reeds', GC, root)


def build_river_generic(GC, M, W, root):
    """일반 강(RiverGeo): L0 물 · L1 깊은 물 띠 · L2 둑 경계석 · L3 물결(흐름 방향) · L4 물로 내려가는 계단·계선주 · L5 반짝임·경계석 윗선 · L6 갈대.
    석축 벽은 땅 판 둑 면(build_land)이 맡는다. 다리·건물 실루엣·절단체 자리는 경계석·계단을 비운다"""
    rp = RV.rp
    x0s, y0s, x1s, y1s = STAGE
    def clip_stage(poly):                     # 해안선 + 무대 평행사변형(위 변 y0, 좌우 블리드 3, 아래 변 y1) 안만
        for f in (lambda p: p[1] - COAST_Y, lambda p: y0s - 0.5 * (p[0] + p[1]), lambda p: 0.5 * (p[0] + p[1]) - y1s,
                  lambda p: (x0s - 3.0) - C30 * (p[0] - p[1]), lambda p: C30 * (p[0] - p[1]) - (x1s + 3.0)):
            poly = clip_half(poly, f)
            if len(poly) < 3:
                return []
        return poly
    a1 = Acc(); a0 = Acc(); a3 = Acc(); a5 = Acc(); a2 = Acc(); a4 = Acc(); a6 = Acc()
    sh = 1.55
    for pi, poly in enumerate(RV.polys):                              # 본류 + 지류(합류부는 같은 물 높이·같은 색으로 겹친다)
        water = clip_stage(poly)
        if water:
            a1.face([V(X, Y, RIVER_Z + 0.002 * pi) for X, Y in water], M['r_deep'], (0, 0, 1))
        w2_ = clip_stage([(X + sh, Y + sh) for X, Y in poly])
        if w2_:
            a0.face([V(X, Y, RIVER_Z + 0.05 + 0.002 * pi) for X, Y in w2_], M['river'], (0, 0, 1))
    w2 = None
    def dash(X, Y, L, w, d, mat, acc, z):
        dx, dy = d; nx, ny = -dy, dx
        pts = [(X - dx * L / 2, Y - dy * L / 2), (X - dx * (L / 2 - w) + nx * w / 2, Y - dy * (L / 2 - w) + ny * w / 2),
               (X + dx * (L / 2 - w) + nx * w / 2, Y + dy * (L / 2 - w) + ny * w / 2), (X + dx * L / 2, Y + dy * L / 2),
               (X + dx * (L / 2 - w) - nx * w / 2, Y + dy * (L / 2 - w) - ny * w / 2), (X - dx * (L / 2 - w) - nx * w / 2, Y - dy * (L / 2 - w) - ny * w / 2)]
        acc.face([V(px, py, z) for px, py in pts], mat, (0, 0, 1))
    xs = [p[0] for q in RV.polys for p in q]; ys = [p[1] for q in RV.polys for p in q]
    i = 0
    Y = min(ys) + 1.0
    while Y < min(max(ys), COAST_Y - 1.5):
        X = min(xs) + 1.0 + (1.6 if i % 2 else 0.0)
        while X < max(xs):
            j = int(X * 7.0) + i * 131
            if hsh(j, 1.7) < 0.36 and RV.inside(X, Y) and RV.dist_edge(X, Y) > 1.1:
                sb = sbox(X - 2.0, X + 2.0, Y - 2.0, Y + 2.0, 0.2)
                if W.stage_ok(sb) and not W.screen_hit(sb, (W.k_text,)):
                    d = RV.flow(X, Y)
                    L = 2.6 + 3.2 * hsh(j, 3.1)
                    dash(X, Y, L, 0.42, d, M['r_wave'], a3, RIVER_Z + 0.10)
                    if hsh(j, 5.5) < 0.18:
                        dash(X + d[0] * L * 0.7 - d[1] * 0.9, Y + d[1] * L * 0.7 + d[0] * 0.9, 1.1, 0.26, d, M['glint'], a5, RIVER_Z + 0.15)
            X += 3.4
        Y += 3.2; i += 1
    sil = SilCover()
    cuts = [o for o in bpy.data.objects if o.name.startswith('X_CUT_') and o.type == 'MESH']
    def blocked(X, Y, pad=0.6):
        sx, sy = S(X, Y)
        if sil.covered((sx - 0.3, sy - 0.3, sx + 0.3, sy + 0.3), pad):
            return True
        for o in cuts:
            bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
            if min(v.x for v in bb) - pad < X < max(v.x for v in bb) + pad and min(-v.y for v in bb) - pad < Y < max(-v.y for v in bb) + pad:
                return True
        return False
    k = 0
    for (a, b) in RV.bank_edges():
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        on, onn = RV.out_normal(a, b)
        if not W.stage_ok(sbox(min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1]), 0.5)) or blocked(mx + on * 0.4, my + onn * 0.4):
            k += 1; continue
        near_mouth = RV.mouth is not None and RV.mouth[0] - 25.0 < mx < RV.mouth[1] + 25.0 and my > COAST_Y - 25.0
        if not near_mouth:                                                   # L2 경계석(땅 쪽 0.8) + L5 윗선
            q = [a, b, (b[0] + on * 0.8, b[1] + onn * 0.8), (a[0] + on * 0.8, a[1] + onn * 0.8)]
            a2.prism(q, 0.0, 0.32, M['curb'], M['curb'])
            a5.face([V(a[0] + on * 0.05, a[1] + onn * 0.05, 0.325), V(b[0] + on * 0.05, b[1] + onn * 0.05, 0.325),
                     V(b[0] + on * 0.27, b[1] + onn * 0.27, 0.325), V(a[0] + on * 0.27, a[1] + onn * 0.27, 0.325)], M['curb_hi'], (0, 0, 1))
            if hsh(k, 7.7) < 0.22:                                           # L4 계선주
                a4.cyl(mx + on * 0.45, my + onn * 0.45, 0.22, 0.32, 0.9, M['bark'], 6)
            if k % 17 == 5:                                                  # L4 물로 내려가는 계단(5단)
                for st in range(5):
                    z = -0.4 * (st + 1); d_in = 0.45 * (st + 1)
                    qs = [a, b, (b[0] - on * d_in, b[1] - onn * d_in), (a[0] - on * d_in, a[1] - onn * d_in)]
                    a4.prism(qs, z - 0.4, z, M['quay'], M['quay'])
        else:                                                                # L6 갈대(하구 가까운 자연 둑)
            for t in range(2):
                if hsh(k, t, 4.2) < 0.5:
                    u = 0.25 + 0.5 * t
                    X = a[0] + (b[0] - a[0]) * u - on * 0.45; Y = a[1] + (b[1] - a[1]) * u - onn * 0.45
                    for r_ in range(4):
                        dx = 0.5 * (hsh(k, t, r_, 1.1) - 0.5); dy = 0.5 * (hsh(k, t, r_, 2.1) - 0.5)
                        hh = 0.9 + 0.9 * hsh(k, t, r_, 3.1)
                        mt = M['reed'] if r_ % 2 == 0 else M['reed2']
                        a6.face([V(X + dx - 0.16, Y + dy, RIVER_Z), V(X + dx + 0.16, Y + dy, RIVER_Z), V(X + dx + 0.05, Y + dy, RIVER_Z + hh)], mt, (0, -1, 0))
        k += 1
    if not a6.bm.faces:                                                      # 갈대가 없으면(하구 둑이 무대 밖) 상류 끝에 몇 포기(L6 0 방지)
        for (a, b) in RV.bank_edges()[:6]:
            on, onn = RV.out_normal(a, b)
            X = (a[0] + b[0]) / 2 - on * 0.45; Y = (a[1] + b[1]) / 2 - onn * 0.45
            a6.face([V(X - 0.16, Y, RIVER_Z), V(X + 0.16, Y, RIVER_Z), V(X + 0.05, Y, RIVER_Z + 1.2)], M['reed'], (0, -1, 0))
    a1.obj('GROUND_River_L1_DeepWater', GC, root); a0.obj('GROUND_River_L0_Water', GC, root); a3.obj('GROUND_River_L3_Waves', GC, root)
    a5.obj('GROUND_River_L5_Glints', GC, root); a2.obj('GROUND_River_L2_Kerbs', GC, root); a4.obj('GROUND_River_L4_StairsBollards', GC, root)
    a6.obj('GROUND_River_L6_Reeds', GC, root)


# ───────────────────────── 하구 폭포(강 수면 −2 → 바다 −9.7) ─────────────────────────
def build_falls(GC, M, root):
    if GENERIC_RIVER and (RV is None or RV.mouth is None):      # 강이 해안선과 만나지 않으면 폭포 0
        return 0
    a0 = Acc(); a1 = Acc(); a2 = Acc(); a4 = Acc(); a5 = Acc(); a6 = Acc()
    X0, X1 = A2_X0 + 0.05, A2_X1 - 0.05
    prof = [(COAST_Y, RIVER_Z), (COAST_Y + 0.35, RIVER_Z - 0.35), (COAST_Y + 0.6, RIVER_Z - 1.2), (COAST_Y + 0.9, SEA_Z + 0.02)]
    a1.face([V(X0, COAST_Y + 0.02, RIVER_BED), V(X1, COAST_Y + 0.02, RIVER_BED), V(X1, COAST_Y + 0.02, RIVER_Z), V(X0, COAST_Y + 0.02, RIVER_Z)], M['cave'], (0, -1, 0))
    for (ya, za), (yb, zb) in zip(prof[:-1], prof[1:]):
        a0.face([V(X0, ya, za), V(X1, ya, za), V(X1, yb, zb), V(X0, yb, zb)], M['fall'], (0, -1, 0.3))
    a5.face([V(X0, COAST_Y - 0.6, RIVER_Z + 0.02), V(X1, COAST_Y - 0.6, RIVER_Z + 0.02), V(X1, COAST_Y + 0.36, RIVER_Z - 0.33), V(X0, COAST_Y + 0.36, RIVER_Z - 0.33)], M['fall_lip'], (0, -1, 1))
    # L2 입술 돌(양옆), L4 가운데 바위
    for j, X in enumerate((X0 + 0.3, X0 + 1.4, X1 - 1.5, X1 - 0.4)):
        a2.blob(X, COAST_Y + 0.2, RIVER_Z - 0.1, 0.75, 0.55, 0.45, M['rock'], 1, 0.2, j + 3, M['rock_top'])
    for j, (X, Z) in enumerate(((X0 + 7.0, -5.6), (X1 - 6.0, -7.4))):
        a4.blob(X, COAST_Y + 1.0, Z, 0.9, 0.6, 0.7, M['rock'], 1, 0.25, j + 9, M['rock_top'])
    # L6 물보라(바다 위 흰 거품 덩이)
    for j in range(26):
        X = X0 - 1.5 + (X1 - X0 + 3.0) * hsh(j, 6.1); Y = COAST_Y + 1.0 + 3.2 * hsh(j, 6.9)
        r = 0.5 + 0.9 * hsh(j, 7.5) * (1.0 - (Y - COAST_Y - 1.0) / 4.0)
        a6.blob(X, Y, SEA_Z + 0.05, r * 1.3, r, r * 0.35, M['foam'], 1, 0.25, j + 20)
    # L3 물줄기 결(물 막 위 밝은 세로 줄)
    a3 = Acc()
    for k in range(11):
        X = X0 + 0.8 + (X1 - X0 - 1.6) * (k + 0.3 + 0.4 * hsh(k, 5.7)) / 11.0
        w = 0.12 + 0.12 * hsh(k, 6.3)
        for (ya, za), (yb, zb) in zip(prof[:-1], prof[1:]):
            a3.face([V(X - w, ya + 0.03, za + 0.01), V(X + w, ya + 0.03, za + 0.01), V(X + w, yb + 0.03, zb + 0.01), V(X - w, yb + 0.03, zb + 0.01)],
                    M['fall_lip'] if k % 3 else M['r_wave'], (0, -1, 0.3))
    a3.obj('GROUND_Falls_L3_Streaks', GC, root)
    a0.obj('GROUND_Falls_L0_Sheet', GC, root); a1.obj('GROUND_Falls_L1_Recess', GC, root); a2.obj('GROUND_Falls_L2_LipStones', GC, root)
    a4.obj('GROUND_Falls_L4_Rocks', GC, root); a5.obj('GROUND_Falls_L5_Lip', GC, root); a6.obj('GROUND_Falls_L6_Spray', GC, root)


# ───────────────────────── 바다 ─────────────────────────
def build_sea(GC, M, W, root):
    """바다(Z −9.7): 왼쪽 변·아래 변 밖으로 블리드해 화면 y 594까지(D12). 하단 띠 밑 흐림은 합성이 한다"""
    poly = [(250.0, COAST_Y - 2.0), (1100.0, COAST_Y - 2.0), (1100.0, 900.0), (250.0, 900.0)]
    ylim = 2.0 * (596.0 + SEA_Z)                       # 화면 y = 0.5(X+Y) − Z ≤ 596
    poly = clip_half(poly, lambda p: (p[0] + p[1]) - ylim)
    poly = clip_half(poly, lambda p: -(p[0] - p[1]) - 4.0 / C30)       # 화면 x ≥ −4
    poly = clip_half(poly, lambda p: (p[0] - p[1]) - 424.0 / C30)      # 화면 x ≤ 424
    a0 = Acc(); a0.face([V(X, Y, SEA_Z) for X, Y in poly], M['sea'], (0, 0, 1))
    # 하단 띠 밑(땅 판이 끝난 y 505 아래): 바다 가장자리를 해안선 연장선(화면 y = tan30·x + 380, 설계 sea_under_bottom_band)에 맞춘다.
    #   수면 −9.7에서 그 선은 평면 Y = 380 + SEA_Z. 땅 판 안(X + Y < 2·(505 + SEA_Z))은 건드리지 않는다(관통 0)
    xy_cut = 2.0 * (STAGE[3] + SEA_Z) + 0.05
    ext = [(200.0, COAST_Y + SEA_Z), (1100.0, COAST_Y + SEA_Z), (1100.0, COAST_Y - 2.0), (200.0, COAST_Y - 2.0)]
    for fn in (lambda p: xy_cut - (p[0] + p[1]), lambda p: (p[0] + p[1]) - ylim, lambda p: (p[0] - p[1]) - 424.0 / C30):
        ext = clip_half(ext, fn)
    if len(ext) >= 3:
        a0.face([V(X, Y, SEA_Z) for X, Y in ext], M['sea'], (0, 0, 1))
    a0.obj('GROUND_Sea_L0_Water', GC, root)
    a1 = Acc(); a2 = Acc(); a3 = Acc(); a4 = Acc(); a5 = Acc(); a6 = Acc()
    # L1 얕은 물 띠(해안선 앞 0~3.2 mm·3.2~7 mm, 물결 바깥 변) · 먼 바다 짙은 띠(해안에서 70 mm 밖)
    for X0, X1 in ((300.0, min(A2_X0 - 0.6, coast_xmax())), (A2_X1 + 0.6, min(1000.0, coast_xmax()))):
        if X1 - X0 < 0.5:
            continue
        n = max(2, int((X1 - X0) / 2.0))
        for (d0, d1, mt, z) in ((0.0, 3.2, M['s_shallow'], 0.05), (3.2, 7.0, M['s_shallow2'], 0.05)):
            outer = [(X0 + (X1 - X0) * t / n, COAST_Y + d1 + 0.5 * math.sin(t * 0.9 + d1) + 0.3 * hsh(t, d1)) for t in range(n + 1)]
            inner = [(X0 + (X1 - X0) * t / n, COAST_Y + d0 + (0.5 * math.sin(t * 0.9 + d0) if d0 > 0 else 0.0)) for t in range(n + 1)]
            pts = clip_half(clip_half(inner + outer[::-1], lambda p: (p[0] + p[1]) - ylim), lambda p: -(p[0] - p[1]) - 4.0 / C30)
            if len(pts) >= 3:
                a1.face([V(X, Y, SEA_Z + z) for X, Y in pts], mt, (0, 0, 1))
    dp = clip_half(clip_half([(250.0, COAST_Y + 70.0), (1100.0, COAST_Y + 70.0), (1100.0, 900.0), (250.0, 900.0)],
                             lambda p: (p[0] + p[1]) - ylim), lambda p: -(p[0] - p[1]) - 4.0 / C30)
    if len(dp) >= 3:
        a1.face([V(X, Y, SEA_Z + 0.05) for X, Y in dp], M['s_deep'], (0, 0, 1))
    # L2 해안 포말선(절벽 발치, 물결 모양 바깥 변)
    for X0, X1 in ((300.0, min(A2_X0 - 1.0, coast_xmax())), (A2_X1 + 1.0, min(640.0, coast_xmax()))):
        if X1 - X0 < 0.5:
            continue
        n = max(2, int((X1 - X0) / 1.3))
        outer = [(X0 + (X1 - X0) * t / n, COAST_Y + 0.38 + 0.22 * math.sin(t * 1.9) + 0.12 * hsh(t, 3.3)) for t in range(n + 1)]
        pts = [(X0, COAST_Y + 0.02)] + [(X1, COAST_Y + 0.02)] + outer[::-1]
        pts = clip_half(pts, lambda p: -(p[0] - p[1]) - 4.0 / C30)
        if len(pts) >= 3:
            a2.face([V(X, Y, SEA_Z + 0.10) for X, Y in pts], M['foam'], (0, 0, 1))
    # L3 물결 줄(해안선과 나란한 ↘ 짧은 획), L5 반짝임. 바닥 글·배·항구 자리는 비운다
    keep = W.k_text + [(b[0] + 1.0, b[1] + 1.0, b[2] - 1.0, b[3] - 1.0) for b in W.k_prop] + W.k_land
    for row in range(40):
        Y = COAST_Y + 5.0 + row * 6.4
        for c in range(70):
            X = 300.0 + c * 9.0 + 6.0 * hsh(row, c, 1.1)
            if hsh(row, c, 2.2) > 0.36:
                continue
            L = 2.4 + 3.4 * hsh(row, c, 3.3)
            sx, sy = S(X, Y, SEA_Z)
            if sx < 1.0 or sx > 419.0 or sy > 592.0:
                continue
            sbx = (sx - L, sy - 1.0, sx + L, sy + 1.0)
            if any(ov(sbx, b) for b in keep):
                continue
            w = 0.46
            pts = [(X - L / 2, Y), (X - L / 2 + w, Y - w / 2), (X + L / 2 - w, Y - w / 2), (X + L / 2, Y), (X + L / 2 - w, Y + w / 2), (X - L / 2 + w, Y + w / 2)]
            a3.face([V(px, py, SEA_Z + 0.15) for px, py in pts], M['s_wave'], (0, 0, 1))
            if hsh(row, c, 4.4) < 0.12 and row < 14:
                g = [(X + L * 0.6, Y - 1.0), (X + L * 0.6 + 0.9, Y - 1.13), (X + L * 0.6 + 1.8, Y - 1.0), (X + L * 0.6 + 0.9, Y - 0.87)]
                a5.face([V(px, py, SEA_Z + 0.20) for px, py in g], M['s_glint'], (0, 0, 1))
    # L4 물 위 바위섬(오스티아 앞 빈 바다), L6 갈매기
    for j, (X, Y) in enumerate(((604.0, 384.6), (611.5, 386.2))):
        sb = sbox(X - 2, X + 2, Y - 2, Y + 2, 2.0)
        if any(ov(sb, b) for b in keep):
            continue
        a4.blob(X, Y, SEA_Z + 0.3, 1.1, 0.8, 0.85, M['rock'], 1, 0.22, j + 40, M['rock_top'])
        a2.face([V(X - 1.7 + 3.4 * t / 10, Y + 1.0 + 0.22 * math.sin(t * 2.0), SEA_Z + 0.10) for t in range(11)] +
                [V(X + 1.7 - 3.4 * t / 10, Y + 0.6, SEA_Z + 0.10) for t in range(11)], M['foam'], (0, 0, 1))
    for j, (X, Y, Z) in enumerate(((615.6, 390.4, 5.0), (609.0, 393.5, 5.8), (622.0, 392.0, 4.4), (560.0, 470.0, 6.0), (575.0, 474.0, 5.2))):
        a6.face([V(X - 0.9, Y, Z + 0.3), V(X, Y, Z), V(X + 0.9, Y, Z + 0.3), V(X, Y, Z + 0.12)], M['gull'], (0, -1, 0))
    a1.obj('GROUND_Sea_L1_ShallowDeep', GC, root)
    a2.obj('GROUND_Sea_L2_Surf', GC, root); a3.obj('GROUND_Sea_L3_Waves', GC, root); a4.obj('GROUND_Sea_L4_Islets', GC, root)
    a5.obj('GROUND_Sea_L5_Glints', GC, root); a6.obj('GROUND_Sea_L6_Gulls', GC, root)


# ───────────────────────── 길 ─────────────────────────
ROAD_Z = {'R1': 0.30, 'R2': 0.31, 'R3': 0.285, 'R4': 0.30, 'R5': 0.29, 'R6a': 0.29, 'R6b': 0.295, 'R7': 0.30}


def _trim(ax, c, lo, hi, me, roads):
    """연석 구간 [lo,hi]에서 다른 길과 겹치는 부분을 뺀다"""
    segs = [(lo, hi)]
    for rd in roads:
        if rd is me:
            continue
        a = rd['rect']
        if ax == 'Y':        # 연석이 X=c, Y를 따라
            if not (a[0] - 0.05 < c < a[1] + 0.05):
                continue
            cut = (a[2], a[3])
        else:
            if not (a[2] - 0.05 < c < a[3] + 0.05):
                continue
            cut = (a[0], a[1])
        out = []
        for s0, s1 in segs:
            if cut[1] <= s0 or cut[0] >= s1:
                out.append((s0, s1)); continue
            if cut[0] > s0:
                out.append((s0, cut[0]))
            if cut[1] < s1:
                out.append((cut[1], s1))
        segs = out
    return [s for s in segs if s[1] - s[0] > 0.3]


def build_ramp(rd, z, M, a0, a2, a5):
    """D7: R7 남쪽 끝 진입 경사(평면 Y 294.76→304.76, 길 윗면 z → 다리 상판 3.0). 양 끝 보행면 높이 차 0"""
    X0, X1 = rd['rect'][0], rd['rect'][1]
    ya, yb, zt = R7_RAMP
    top = lambda y: z + (zt - z) * (y - ya) / (yb - ya)
    a0.face([V(X0, ya, z), V(X1, ya, z), V(X1, yb, zt), V(X0, yb, zt)], M['basalt'], (0, 0, 1))
    a0.face([V(X1, ya, 0.0), V(X1, yb, 0.0), V(X1, yb, zt), V(X1, ya, z)], M['road_side'], (1, 0, 0))
    a0.face([V(X0, yb, 0.0), V(X1, yb, 0.0), V(X1, yb, zt), V(X0, yb, zt)], M['quay'], (0, -1, 0))
    for (xa, xb, outer) in ((X0, X0 + 0.55, False), (X1 - 0.55, X1, True)):     # L2 난간(경사를 따라)
        n = 5
        for k in range(n):
            y_a = ya + (yb - ya) * k / n; y_b = ya + (yb - ya) * (k + 1) / n
            ta, tb = top(y_a), top(y_b)
            a2.face([V(xa, y_a, ta + 0.55), V(xb, y_a, ta + 0.55), V(xb, y_b, tb + 0.55), V(xa, y_b, tb + 0.55)], M['curb'], (0, 0, 1))
            a2.face([V(xb, y_a, 0.0 if outer else ta), V(xb, y_b, 0.0 if outer else tb), V(xb, y_b, tb + 0.55), V(xb, y_a, ta + 0.55)], M['curb'], (1, 0, 0))
            a5.face([V(xa, y_a, ta + 0.556), V(xa + 0.2, y_a, ta + 0.556), V(xa + 0.2, y_b, tb + 0.556), V(xa, y_b, tb + 0.556)], M['curb_hi'], (0, 0, 1))
        a2.face([V(xa, yb, tb), V(xb, yb, tb), V(xb, yb, tb + 0.55), V(xa, yb, tb + 0.55)], M['curb'], (0, -1, 0))


def build_roads(GC, M, W, root):
    a0 = Acc(); a1 = Acc(); a2 = Acc(); a3 = Acc(); a4 = Acc(); a5 = Acc(); a6 = Acc()
    for rd in W.roads:
        X0, X1, Y0, Y1 = rd['rect']; z = ROAD_Z.get(rd['id'], 0.3)
        if rd['id'] == 'R4':
            # 통합(b1): 하역장 길 끝은 coast 부두 앞 띠(평면 Y 300.0~303.65, 포장 윗면 0.32)가 잇는다.
            #   예전 끝 Y 304.76은 X_CUT_CoastEmporium 아랫단(Y 303.63~) 위로 길 판·연석이 떠 있었다
            Y1 = min(Y1, 300.0)
        if rd['id'] == 'R7':
            build_ramp(rd, z, M, a0, a2, a5)
            Y1 = min(Y1, R7_RAMP[0])
        a0.box(X0, X1, Y0, Y1, 0.0, z, M['basalt'], M['road_side'], 'ES')
        # L3 판석 무늬: 밝고 짙은 다각 판석 몇 장(길 판 재질의 결 위에 또렷한 판석)
        Lr = (Y1 - Y0) if rd['axis'] == 'Y' else (X1 - X0)
        for k in range(int(Lr / 1.6)):
            if hsh(k, 4.4, len(rd['id']) + X0) > 0.42:
                continue
            u = (k + 0.5) * 1.6
            v = 0.15 + 0.7 * hsh(k, 5.5, X0)
            if rd['axis'] == 'Y':
                cx, cy = X0 + (X1 - X0) * v, Y0 + u
            else:
                cx, cy = X0 + u, Y0 + (Y1 - Y0) * v
            r_ = 0.32 + 0.22 * hsh(k, 6.6, X0)
            mt = M['curb_hi'] if hsh(k, 7.7, X0) < 0.5 else M['road_side']
            a3.face([V(cx + r_ * math.cos(2 * math.pi * t / 6 + 0.3 * k), cy + r_ * 0.85 * math.sin(2 * math.pi * t / 6 + 0.3 * k), z + 0.05) for t in range(6)], mt, (0, 0, 1))
        W.occupy(X0 - 0.4, X1 + 0.4, Y0 - 0.4, Y1 + 0.4, 'road')
        cw = 1.0 if rd['hw'] > 6 else 0.7
        zc = z + 0.18
        if rd['axis'] == 'Y':
            for c0, c1 in ((X0, X0 + cw), (X1 - cw, X1)):
                for s0, s1 in _trim('Y', (c0 + c1) / 2, Y0, Y1, rd, W.roads):
                    a2.box(c0, c1, s0, s1, z - 0.05, zc, M['curb'], M['curb'], 'ES')
                    a5.face([V(c0, s0, zc + 0.05), V(c0 + 0.2, s0, zc + 0.05), V(c0 + 0.2, s1, zc + 0.05), V(c0, s1, zc + 0.05)], M['curb_hi'], (0, 0, 1))
            if rd['cl']:
                Xm = (X0 + X1) / 2; hw = 1.6 / C30 / 2
                Y = Y0 + 1.5
                while Y < Y1 - 1.0:
                    a4.box(Xm - hw, Xm + hw, Y, min(Y + 6.5, Y1 - 0.8), z, z + 0.15, M['cline'], None, '')
                    Y += 9.5
                for off in (-5.2, -3.4, 3.4, 5.2):       # L1 바퀴 자국
                    a1.box(Xm + off - 0.12, Xm + off + 0.12, Y0 + 0.5, Y1 - 0.5, z, z + 0.10, M['rut'], None, '')
                for k in range(int((Y1 - Y0) / 24.0) + 1):   # L4 이정표
                    Yk = Y1 - 6.0 - 24.0 * k
                    if Yk < Y0 + 2:
                        break
                    a4.cyl(X1 + 0.9, Yk, 0.36, 0.0, 1.25, M['mile'], 8)
        else:
            for c0, c1 in ((Y0, Y0 + cw), (Y1 - cw, Y1)):
                for s0, s1 in _trim('X', (c0 + c1) / 2, X0, X1, rd, W.roads):
                    a2.box(s0, s1, c0, c1, z - 0.05, zc, M['curb'], M['curb'], 'ES')
                    a5.face([V(s0, c0, zc + 0.05), V(s1, c0, zc + 0.05), V(s1, c0 + 0.2, zc + 0.05), V(s0, c0 + 0.2, zc + 0.05)], M['curb_hi'], (0, 0, 1))
        # L4 징검돌(시내 길 건널목: 폼페이식 돋운 돌 3개)
        if rd['id'] in ('R2', 'R3', 'R4'):
            n = 2 if rd['id'] != 'R4' else 1
            for k in range(n):
                if rd['axis'] == 'Y':
                    Yk = Y0 + (Y1 - Y0) * (0.3 + 0.4 * k)
                    for t in range(3):
                        Xk = X0 + (X1 - X0) * (0.25 + 0.25 * t)
                        a4.box(Xk - 0.55, Xk + 0.55, Yk - 0.4, Yk + 0.4, z, z + 0.22, M['curb'], M['curb'], 'ES')
                else:
                    Xk = X0 + (X1 - X0) * (0.3 + 0.4 * k)
                    for t in range(3):
                        Yk = Y0 + (Y1 - Y0) * (0.25 + 0.25 * t)
                        a4.box(Xk - 0.4, Xk + 0.4, Yk - 0.55, Yk + 0.55, z, z + 0.22, M['curb'], M['curb'], 'ES')
        # L6 길가 풀 포기
        L = (Y1 - Y0) if rd['axis'] == 'Y' else (X1 - X0)
        for k in range(int(L / 3.0)):
            t = hsh(k, 3.3, len(rd['id']))
            if t > 0.55:
                continue
            u = (k + 0.5) * 3.0
            if rd['axis'] == 'Y':
                px, py = (X1 + 0.35 if hsh(k, 1.9) < 0.5 else X0 - 0.35), Y0 + u
            else:
                px, py = X0 + u, (Y1 + 0.35 if hsh(k, 1.9) < 0.5 else Y0 - 0.35)
            hh = 0.4 + 0.35 * hsh(k, 7.1)
            mt = (M['tuft'], M['tuft2'], M['tuft3'])[k % 3]
            a6.face([V(px - 0.28, py, 0.0), V(px + 0.28, py, 0.0), V(px, py, hh)], mt, (0, -1, 0))
            a6.face([V(px, py - 0.25, 0.0), V(px, py + 0.25, 0.0), V(px, py, hh * 0.8)], mt, (1, 0, 0))
    # L1 바퀴 자국(중앙선 없는 길도 두 줄)
    for rd in W.roads:
        if rd['cl']:
            continue
        X0, X1, Y0, Y1 = rd['rect']; z = ROAD_Z.get(rd['id'], 0.3)
        if rd['id'] == 'R4':
            Y1 = min(Y1, 300.0)
        if rd['id'] == 'R7':
            Y1 = min(Y1, R7_RAMP[0])
        for off in (-1.3, 1.3):
            if rd['axis'] == 'Y':
                Xm = (X0 + X1) / 2
                a1.box(Xm + off - 0.11, Xm + off + 0.11, Y0 + 0.6, Y1 - 0.6, z, z + 0.10, M['rut'], None, '')
            else:
                Ym = (Y0 + Y1) / 2
                a1.box(X0 + 0.6, X1 - 0.6, Ym + off - 0.11, Ym + off + 0.11, z, z + 0.10, M['rut'], None, '')
    a0.obj('GROUND_Roads_L0_Slab', GC, root); a1.obj('GROUND_Roads_L1_Ruts', GC, root); a2.obj('GROUND_Roads_L2_Curbs', GC, root)
    a3.obj('GROUND_Roads_L3_Pavers', GC, root)
    a4.obj('GROUND_Roads_L4_CenterLineMilestones', GC, root); a5.obj('GROUND_Roads_L5_CurbHighlight', GC, root); a6.obj('GROUND_Roads_L6_Verge', GC, root)
    return road_people(GC, W, root)


# ───────────────────────── 입구·출구 길(16:41 사용자: 읽기 순서 길, 16:14 '길 0'의 예외) ─────────────────────────
ROUTE_IDS = ('R_route', 'route', 'R_ROUTE')
ROUTE_Z = 0.30


def route_spec(CM):
    for r in CM.get('roads', []) or []:
        if r.get('id') in ROUTE_IDS:
            return r
    return None


def build_route(GC, M, W, CM, root):
    """설계 d5 core_map.roads의 R_route(평면 꺾은선). 땅 위 구간만 폭 5 mm 판석 길(PAL 'slab' #D6CEBD, 가장자리 #B9AE98).
    강·바다 구간은 짓지 않는다(정보 층이 점선). 구간 종류가 spec에 있으면(segments[].kind) 그것을, 없으면 강·바다 위치로 가른다.
    L0 판석 바탕 · L1 가장자리 그늘 줄 · L2 가장자리 돌 · L3 판석 줄눈 · L4 깨진 판석 · L5 가장자리 윗면 밝은 띠 · L6 닳은 자국·풀"""
    r = route_spec(CM)
    if r is None:
        return 0
    pts = [tuple(p) for p in r.get('plan_pts', [])]
    hw = float(r.get('w_screen_perp_mm', 5.0)) / C30 / 2.0
    kinds = [str(sg.get('kind', 'land')) for sg in r.get('segments', [])] if r.get('segments') else None
    slab, edge = '#D6CEBD', '#B9AE98'
    mS = M.setdefault('route_slab', FL.flat('F_ground_routeSlab', slab))
    mE = M.setdefault('route_edge', FL.flat('F_ground_routeEdge', edge))
    mJ = M.setdefault('route_joint', FL.flat('F_ground_routeJoint', FL.shade(slab, 0.82)))
    mD = M.setdefault('route_dk', FL.flat('F_ground_routeDk', FL.shade(slab, 0.88)))
    mH = M.setdefault('route_hi', FL.flat('F_ground_routeHi', FL.shade(slab, 1.1, '#FFFFFF')))
    mW = M.setdefault('route_worn', FL.flat('F_ground_routeWorn', FL.mix_hex(slab, '#A99C84', 0.35)))
    a = [Acc() for _ in range(7)]
    n_ok = 0
    for i in range(len(pts) - 1):
        (X0, Y0), (X1, Y1) = pts[i], pts[i + 1]
        Xm, Ym = (X0 + X1) / 2, (Y0 + Y1) / 2
        if kinds is not None and i < len(kinds):
            if kinds[i] != 'land':
                continue
        elif Ym > COAST_Y - 1.0 or W.river_near(Xm, Ym, hw + 0.4):
            continue
        L_ = math.hypot(X1 - X0, Y1 - Y0)
        if L_ < 1e-6:
            continue
        dx, dy = (X1 - X0) / L_, (Y1 - Y0) / L_
        nx, ny = -dy, dx
        e = hw                                                                  # 끝을 반폭만큼 늘여 꺾이는 곳을 메운다
        A0 = (X0 - dx * e, Y0 - dy * e); A1 = (X1 + dx * e, Y1 + dy * e)
        def q(o0, o1):
            return [(A0[0] + nx * o0, A0[1] + ny * o0), (A1[0] + nx * o0, A1[1] + ny * o0), (A1[0] + nx * o1, A1[1] + ny * o1), (A0[0] + nx * o1, A0[1] + ny * o1)]
        a[0].prism(q(-hw, hw), 0.0, ROUTE_Z, mS, mD)
        for sg in (-1, 1):
            o_in, o_out = sg * (hw - 0.55), sg * hw
            a[2].prism(q(min(o_in, o_out), max(o_in, o_out)), ROUTE_Z - 0.05, ROUTE_Z + 0.12, mE, mE)
            o_l = sg * (hw - 0.75)
            a[1].prism(q(min(o_l, o_in), max(o_l, o_in)), ROUTE_Z, ROUTE_Z + 0.02, mD, None)
        a[5].prism(q(hw - 0.55, hw - 0.35) if (nx + ny) > 0 else q(-hw + 0.35, -hw + 0.55), ROUTE_Z + 0.12, ROUTE_Z + 0.15, mH, None)
        k = 0; u = 0.8
        while u < L_ - 0.4:                                                     # 판석 가로 줄눈 + 반 칸 어긋난 세로 줄눈
            cx, cy = X0 + dx * u, Y0 + dy * u
            a[3].prism([(cx + nx * (-hw + 0.55) - dx * 0.04, cy + ny * (-hw + 0.55) - dy * 0.04), (cx + nx * (hw - 0.55) - dx * 0.04, cy + ny * (hw - 0.55) - dy * 0.04),
                        (cx + nx * (hw - 0.55) + dx * 0.04, cy + ny * (hw - 0.55) + dy * 0.04), (cx + nx * (-hw + 0.55) + dx * 0.04, cy + ny * (-hw + 0.55) + dy * 0.04)],
                       ROUTE_Z, ROUTE_Z + 0.03, mJ, None)
            off = 0.0 if k % 2 else 0.6
            mx, my = cx + nx * off + dx * 0.8, cy + ny * off + dy * 0.8
            a[3].prism([(mx - nx * 0.04, my - ny * 0.04), (mx + dx * 1.5 - nx * 0.04, my + dy * 1.5 - ny * 0.04), (mx + dx * 1.5 + nx * 0.04, my + dy * 1.5 + ny * 0.04), (mx + nx * 0.04, my + ny * 0.04)],
                       ROUTE_Z, ROUTE_Z + 0.03, mJ, None)
            if hsh(i, k, 4.2) < 0.12:                                           # 깨진 판석(L4)
                a[4].box(cx + nx * 0.3, cx + nx * 0.3 + 0.7, cy + ny * 0.3, cy + ny * 0.3 + 0.5, ROUTE_Z, ROUTE_Z + 0.06, mD, mJ)
            if hsh(i, k, 6.1) < 0.35:                                           # 닳은 자국(L6, 가운데 바퀴·발길)
                wx, wy = cx + dx * 0.8, cy + dy * 0.8
                a[6].prism([(wx + dx * 0.9 * math.cos(t) * 1.0 + nx * 0.5 * math.sin(t), wy + dy * 0.9 * math.cos(t) + ny * 0.5 * math.sin(t)) for t in [2 * math.pi * j / 10 for j in range(10)]],
                           ROUTE_Z + 0.04, ROUTE_Z + 0.05, mW, None)
            u += 1.6; k += 1
        for j in range(int(L_ / 2.5)):                                          # 가장자리 풀 포기(L6)
            if hsh(i, j, 7.3) > 0.5:
                continue
            u = (j + 0.5) * 2.5; sg = 1 if hsh(i, j, 7.9) < 0.5 else -1
            px, py = X0 + dx * u + nx * sg * (hw + 0.3), Y0 + dy * u + ny * sg * (hw + 0.3)
            hh = 0.4 + 0.3 * hsh(i, j, 8.2)
            a[6].face([V(px - 0.26, py, 0.0), V(px + 0.26, py, 0.0), V(px, py, hh)], M['tuft'], (0, -1, 0))
        X_lo, X_hi = min(A0[0], A1[0]) - hw, max(A0[0], A1[0]) + hw
        Y_lo, Y_hi = min(A0[1], A1[1]) - hw, max(A0[1], A1[1]) + hw
        W.occupy(X_lo - 0.3, X_hi + 0.3, Y_lo - 0.3, Y_hi + 0.3, 'route')      # 땅 결 조각이 길 위에 오지 않게
        n_ok += 1
    names = ('L0_Slab', 'L1_EdgeShade', 'L2_EdgeStones', 'L3_Joints', 'L4_Broken', 'L5_EdgeLight', 'L6_WearGrass')
    for k, nm in enumerate(names):
        a[k].obj('GROUND_Route_%s' % nm, GC, root)
    return n_ok


def road_people(GC, W, root):
    """L6 길 위 사람(D8): 조경 경계 밖 15 mm 안 길 위 3.4, 그 밖 2.4(원형 키 1.0 정규화 → 배율만 곱한다)"""
    pts = []
    for rd in W.roads:
        X0, X1, Y0, Y1 = rd['rect']; z = ROAD_Z.get(rd['id'], 0.3)
        if rd['id'] == 'R7':
            Y1 = min(Y1, R7_RAMP[0])
        Lr = (Y1 - Y0) if rd['axis'] == 'Y' else (X1 - X0)
        for k in range(int(Lr / 7.0)):
            if hsh(k, 8.1, X0 + Y0) > 0.5:
                continue
            u = (k + 0.5) * 7.0 + 2.0 * (hsh(k, 8.7, X0) - 0.5)
            v = 0.2 + 0.6 * hsh(k, 9.2, Y0)
            X, Y = (X0 + (X1 - X0) * v, Y0 + u) if rd['axis'] == 'Y' else (X0 + u, Y0 + (Y1 - Y0) * v)
            d = math.hypot(X - HERO_C[0], Y - HERO_C[1]); th = math.atan2(Y - HERO_C[1], X - HERO_C[0])
            if d < HERO_KEEP + 0.5:
                continue
            h = H_PERSON_NEAR if d < rb(th) + 15.0 else H_PERSON
            sx, sy = S(X, Y, z)
            sb = (sx - 0.6, sy - h, sx + 0.6, sy)
            if not W.stage_ok(sb) or W.screen_hit(sb, (W.k_land, W.k_prop, W.k_info, W.k_text)) or W.leader_hit(sb, 0.6):
                continue
            pts.append((X, Y, z, h))
    n = 0
    for k, (X, Y, Z, h) in enumerate(pts):
        src = bpy.data.objects.get('P_person%d' % (k % 3))
        if src is None:
            break
        ob = bpy.data.objects.new('GROUND_Roads_L6_Person_%03d' % k, src.data)
        GC.objects.link(ob); ob.parent = root
        ob.location = V(X, Y, Z); ob.rotation_euler = (0, 0, math.radians(360 * hsh(k, 2.2)))
        s = h * (0.96 + 0.08 * hsh(k, 3.3)) / max(0.5, src.dimensions.z); ob.scale = (s, s, s)
        n += 1
    return n


def place_people(GC, W, M, root, pts, name):
    """L6 사람(원형 P_person*가 있으면 링크 복제)"""
    n = 0
    for k, (X, Y, Z) in enumerate(pts):
        src = bpy.data.objects.get('P_person%d' % (k % 3))
        if src is None:
            break
        ob = bpy.data.objects.new('%s_%03d' % (name, k), src.data)
        GC.objects.link(ob); ob.parent = root
        ob.location = V(X, Y, Z); ob.rotation_euler = (0, 0, math.radians(360 * hsh(k, 2.2)))
        s = H_PERSON * (0.92 + 0.16 * hsh(k, 3.3)) / max(0.5, src.dimensions.z); ob.scale = (s, s, s)   # D8: 키 2.4(2.2~2.6)
        n += 1
    return n


# ───────────────────────── 시내 지붕 블록(집 수백 채) ─────────────────────────
class City:
    def __init__(self, M):
        self.M = M
        self.a = {k: Acc() for k in ('L0', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6')}
        self.n = 0
        self.people = []

    def walls(self, X0, X1, Y0, Y1, z0, h, wm):
        a = self.a['L0']
        a.face([V(X1, Y0, z0), V(X1, Y1, z0), V(X1, Y1, h), V(X1, Y0, h)], wm, (1, 0, 0))
        a.face([V(X0, Y1, z0), V(X1, Y1, z0), V(X1, Y1, h), V(X0, Y1, h)], wm, (0, -1, 0))

    def openings(self, X0, X1, Y0, Y1, z0, h, seed, shop_s, shop_e):
        """L1 창·문(짙은 색) · L2 창턱·문틀 · L6 차양·화분 · 벽 밑 얼룩"""
        M = self.M; a1 = self.a['L1']; a2 = self.a['L2']; a6 = self.a['L6']
        e = 0.03
        fl = 1.55
        nfl = max(1, int((h - z0) / fl))
        for wall in ('S', 'E'):
            L = (X1 - X0) if wall == 'S' else (Y1 - Y0)
            nw = max(1, int((L - 0.6) / 1.25))
            pitch = (L - 0.6) / nw
            shop = shop_s if wall == 'S' else shop_e
            for f in range(nfl):
                zb = z0 + f * fl
                for k in range(nw):
                    u0 = 0.3 + pitch * k + pitch * 0.5
                    if f == 0:
                        if shop and k % 2 == 0:
                            w, zz0, zz1, mt = min(1.05, pitch * 0.82), zb + 0.05, zb + 1.05, M['shop']
                        elif (k == nw // 2):
                            w, zz0, zz1, mt = 0.6, zb + 0.02, zb + 1.08, M['door']
                        else:
                            if hsh(seed, k, wall == 'S') < 0.5:
                                continue
                            w, zz0, zz1, mt = 0.34, zb + 0.6, zb + 1.05, M['win']
                    else:
                        if hsh(seed, f, k, 1.3) < 0.18:
                            continue
                        w, zz0, zz1, mt = 0.38, zb + 0.45, zb + 1.05, M['win']
                    ua, ub = u0 - w / 2, u0 + w / 2
                    if wall == 'S':
                        xa, xb = X0 + ua, X0 + ub
                        a1.face([V(xa, Y1 + e, zz0), V(xb, Y1 + e, zz0), V(xb, Y1 + e, zz1), V(xa, Y1 + e, zz1)], mt, (0, -1, 0))
                        a2.face([V(xa - 0.06, Y1 + e * 1.5, zz0 - 0.12), V(xb + 0.06, Y1 + e * 1.5, zz0 - 0.12), V(xb + 0.06, Y1 + e * 1.5, zz0), V(xa - 0.06, Y1 + e * 1.5, zz0)], M['frame'], (0, -1, 0))
                        if f == 0 and mt is M['shop']:
                            am = M['awn'][int(3 * hsh(seed, k, 7.7)) % 3]
                            a6.face([V(xa - 0.1, Y1, zz1 + 0.18), V(xb + 0.1, Y1, zz1 + 0.18), V(xb + 0.1, Y1 + 0.55, zz1 - 0.12), V(xa - 0.1, Y1 + 0.55, zz1 - 0.12)], am, (0, -1, 1))
                    else:
                        ya, yb = Y0 + ua, Y0 + ub
                        a1.face([V(X1 + e, ya, zz0), V(X1 + e, yb, zz0), V(X1 + e, yb, zz1), V(X1 + e, ya, zz1)], mt, (1, 0, 0))
                        a2.face([V(X1 + e * 1.5, ya - 0.06, zz0 - 0.12), V(X1 + e * 1.5, yb + 0.06, zz0 - 0.12), V(X1 + e * 1.5, yb + 0.06, zz0), V(X1 + e * 1.5, ya - 0.06, zz0)], M['frame'], (1, 0, 0))
                        if f == 0 and mt is M['shop']:
                            am = M['awn'][int(3 * hsh(seed, k, 8.8)) % 3]
                            a6.face([V(X1, ya - 0.1, zz1 + 0.18), V(X1, yb + 0.1, zz1 + 0.18), V(X1 + 0.55, yb + 0.1, zz1 - 0.12), V(X1 + 0.55, ya - 0.1, zz1 - 0.12)], am, (1, 0, 1))
        # 벽 밑 얼룩(L6)
        a6.face([V(X0, Y1 + 0.02, z0), V(X1, Y1 + 0.02, z0), V(X1, Y1 + 0.02, z0 + 0.28), V(X0, Y1 + 0.02, z0 + 0.22)], M['base_stain'], (0, -1, 0))
        a6.face([V(X1 + 0.02, Y0, z0), V(X1 + 0.02, Y1, z0), V(X1 + 0.02, Y1, z0 + 0.22), V(X1 + 0.02, Y0, z0 + 0.28)], M['base_stain'], (1, 0, 0))

    def eaves(self, X0, X1, Y0, Y1, h):
        """L1 처마 밑 짙은 띠 · L2 처마띠(코니스)"""
        M = self.M; a1 = self.a['L1']; a2 = self.a['L2']
        a1.face([V(X0, Y1 + 0.025, h - 0.32), V(X1, Y1 + 0.025, h - 0.32), V(X1, Y1 + 0.025, h), V(X0, Y1 + 0.025, h)], M['eave_dk'], (0, -1, 0))
        a1.face([V(X1 + 0.025, Y0, h - 0.32), V(X1 + 0.025, Y1, h - 0.32), V(X1 + 0.025, Y1, h), V(X1 + 0.025, Y0, h)], M['eave_dk'], (1, 0, 0))
        a2.box(X0, X1 + 0.08, Y0, Y1 + 0.08, h - 0.5, h - 0.36, M['cornice'], M['cornice'], 'ES', top=False)

    def gable(self, X0, X1, Y0, Y1, h, axis, pal, o=0.22, wm=None):
        M = self.M; a3 = self.a['L3']; a5 = self.a['L5']; a2 = self.a['L2']
        wm = wm or M['plaster'][0]
        if axis == 'X':
            ym = (Y0 + Y1) / 2; rise = (Y1 - Y0) * 0.5 * 0.5
            tL, tD = M['tile'][pal + 'XL'], M['tile'][pal + 'XD']
            a3.face([V(X0 - o, Y1 + o, h), V(X1 + o, Y1 + o, h), V(X1 + o, ym, h + rise), V(X0 - o, ym, h + rise)], tL, (0, -1, 1))
            a3.face([V(X0 - o, ym, h + rise), V(X1 + o, ym, h + rise), V(X1 + o, Y0 - o, h), V(X0 - o, Y0 - o, h)], tD, (0, 1, 1))
            self.a['L0'].face([V(X1, Y0, h), V(X1, Y1, h), V(X1, ym, h + rise)], wm, (1, 0, 0))
            a2.face([V(X0 - o, Y1 + o, h - 0.14), V(X1 + o, Y1 + o, h - 0.14), V(X1 + o, Y1 + o, h), V(X0 - o, Y1 + o, h)], M['fascia'], (0, -1, 0))
            a2.face([V(X1 + o, Y1 + o, h - 0.14), V(X1 + o, ym, h + rise - 0.14), V(X1 + o, ym, h + rise), V(X1 + o, Y1 + o, h)], M['fascia'], (1, 0, 0))
            a2.face([V(X1 + o, ym, h + rise - 0.14), V(X1 + o, Y0 - o, h - 0.14), V(X1 + o, Y0 - o, h), V(X1 + o, ym, h + rise)], M['fascia'], (1, 0, 0))
            a5.face([V(X0 - o, ym - 0.11, h + rise + 0.012), V(X1 + o, ym - 0.11, h + rise + 0.012), V(X1 + o, ym + 0.11, h + rise + 0.012), V(X0 - o, ym + 0.11, h + rise + 0.012)], M['ridge'], (0, 0, 1))
        else:
            xm = (X0 + X1) / 2; rise = (X1 - X0) * 0.5 * 0.5
            tL, tD = M['tile'][pal + 'YL'], M['tile'][pal + 'YD']
            a3.face([V(X0 - o, Y0 - o, h), V(xm, Y0 - o, h + rise), V(xm, Y1 + o, h + rise), V(X0 - o, Y1 + o, h)], tL, (-1, 0, 1))
            a3.face([V(xm, Y0 - o, h + rise), V(X1 + o, Y0 - o, h), V(X1 + o, Y1 + o, h), V(xm, Y1 + o, h + rise)], tD, (1, 0, 1))
            self.a['L0'].face([V(X0, Y1, h), V(X1, Y1, h), V(xm, Y1, h + rise)], wm, (0, -1, 0))
            a2.face([V(X1 + o, Y0 - o, h - 0.14), V(X1 + o, Y1 + o, h - 0.14), V(X1 + o, Y1 + o, h), V(X1 + o, Y0 - o, h)], M['fascia'], (1, 0, 0))
            a2.face([V(X0 - o, Y1 + o, h - 0.14), V(xm, Y1 + o, h + rise - 0.14), V(xm, Y1 + o, h + rise), V(X0 - o, Y1 + o, h)], M['fascia'], (0, -1, 0))
            a2.face([V(xm, Y1 + o, h + rise - 0.14), V(X1 + o, Y1 + o, h - 0.14), V(X1 + o, Y1 + o, h), V(xm, Y1 + o, h + rise)], M['fascia'], (0, -1, 0))
            a5.face([V(xm - 0.11, Y0 - o, h + rise + 0.012), V(xm + 0.11, Y0 - o, h + rise + 0.012), V(xm + 0.11, Y1 + o, h + rise + 0.012), V(xm - 0.11, Y1 + o, h + rise + 0.012)], M['ridge'], (0, 0, 1))
        return rise

    def terrace(self, X0, X1, Y0, Y1, h, seed):
        """평지붕 옥상(L4) + 난간 + 화분·덩굴(L6)"""
        M = self.M
        self.a['L4'].face([V(X0, Y0, h), V(X1, Y0, h), V(X1, Y1, h), V(X0, Y1, h)], M['terrace'], (0, 0, 1))
        for (a, b, c, d) in ((X0, X1, Y0, Y0 + 0.22), (X0, X0 + 0.22, Y0, Y1)):
            self.a['L2'].box(a, b, c, d, h, h + 0.45, M['cornice'], M['cornice'], 'ES')
        self.a['L2'].box(X0, X1, Y1 - 0.22, Y1, h, h + 0.45, M['cornice'], M['cornice'], 'ES')
        self.a['L2'].box(X1 - 0.22, X1, Y0, Y1, h, h + 0.45, M['cornice'], M['cornice'], 'ES')
        for k in range(2 + int(3 * hsh(seed, 4.4))):
            px = X0 + 0.7 + (X1 - X0 - 1.4) * hsh(seed, k, 1.1); py = Y0 + 0.7 + (Y1 - Y0 - 1.4) * hsh(seed, k, 2.2)
            self.a['L6'].box(px - 0.18, px + 0.18, py - 0.18, py + 0.18, h, h + 0.3, M['pot'], M['pot'])
            self.a['L6'].blob(px, py, h + 0.55, 0.34, 0.34, 0.3, M['plant'][k % 2], 0, 0.15, seed + k, M['plant'][1], None)
        # 덩굴 시렁(퍼걸러)
        if hsh(seed, 9.1) < 0.5:
            px = X0 + (X1 - X0) * 0.55
            self.a['L4'].box(px, px + 1.6, Y0 + 0.5, Y0 + 2.1, h + 1.0, h + 1.08, M['balc'], M['balc'])
            self.a['L6'].face([V(px, Y0 + 0.5, h + 1.09), V(px + 1.6, Y0 + 0.5, h + 1.09), V(px + 1.6, Y0 + 2.1, h + 1.09), V(px, Y0 + 2.1, h + 1.09)], M['plant'][0], (0, 0, 1))

    def atrium(self, X0, X1, Y0, Y1, h, pal, seed):
        """도무스: 안쪽(콤플루비움)으로 기운 지붕 고리 + 아트리움 구멍(L1) + 빗물받이 못(L4)"""
        M = self.M; a3 = self.a['L3']
        w, d = X1 - X0, Y1 - Y0
        ax0, ax1 = X0 + w * 0.33, X1 - w * 0.33
        ay0, ay1 = Y0 + d * 0.33, Y1 - d * 0.33
        hr = h - 0.45
        tX = M['tile'][pal + 'XL']; tY = M['tile'][pal + 'YL']; tXd = M['tile'][pal + 'XD']; tYd = M['tile'][pal + 'YD']
        o = 0.2
        a3.face([V(X0 - o, Y1 + o, h), V(X1 + o, Y1 + o, h), V(ax1, ay1, hr), V(ax0, ay1, hr)], tXd, (0, 1, 1))
        a3.face([V(X1 + o, Y0 - o, h), V(X1 + o, Y1 + o, h), V(ax1, ay1, hr), V(ax1, ay0, hr)], tY, (-1, 0, 1))
        a3.face([V(X0 - o, Y0 - o, h), V(X1 + o, Y0 - o, h), V(ax1, ay0, hr), V(ax0, ay0, hr)], tX, (0, -1, 1))
        a3.face([V(X0 - o, Y0 - o, h), V(X0 - o, Y1 + o, h), V(ax0, ay1, hr), V(ax0, ay0, hr)], tYd, (1, 0, 1))
        self.a['L2'].face([V(X0 - o, Y1 + o, h - 0.14), V(X1 + o, Y1 + o, h - 0.14), V(X1 + o, Y1 + o, h), V(X0 - o, Y1 + o, h)], M['fascia'], (0, -1, 0))
        self.a['L2'].face([V(X1 + o, Y0 - o, h - 0.14), V(X1 + o, Y1 + o, h - 0.14), V(X1 + o, Y1 + o, h), V(X1 + o, Y0 - o, h)], M['fascia'], (1, 0, 0))
        a1 = self.a['L1']
        a1.face([V(ax0, ay0, 0.25), V(ax1, ay0, 0.25), V(ax1, ay0, hr), V(ax0, ay0, hr)], M['atrium'], (0, -1, 0))
        a1.face([V(ax0, ay0, 0.25), V(ax0, ay1, 0.25), V(ax0, ay1, hr), V(ax0, ay0, hr)], M['atrium'], (1, 0, 0))
        a1.face([V(ax0, ay0, 0.25), V(ax1, ay0, 0.25), V(ax1, ay1, 0.25), V(ax0, ay1, 0.25)], M['atrium_fl'], (0, 0, 1))
        cx, cy = (ax0 + ax1) / 2, (ay0 + ay1) / 2; pw = (ax1 - ax0) * 0.28; pd = (ay1 - ay0) * 0.28
        self.a['L4'].box(cx - pw, cx + pw, cy - pd, cy + pd, 0.25, 0.3, M['pool'], M['marble'])
        self.a['L5'].face([V(X0 - o, Y1 + o - 0.16, h + 0.01), V(X1 + o, Y1 + o - 0.16, h + 0.01), V(X1 + o, Y1 + o, h + 0.01), V(X0 - o, Y1 + o, h + 0.01)], M['ridge'], (0, 0, 1))

    def garden(self, X0, X1, Y0, Y1, seed):
        """정원 블록(L6): 담 + 잔디 + 관목·작은 나무"""
        M = self.M
        self.a['L6'].face([V(X0, Y0, 0.14), V(X1, Y0, 0.14), V(X1, Y1, 0.14), V(X0, Y1, 0.14)], M['garden'], (0, 0, 1))
        self.a['L2'].box(X0, X1, Y1 - 0.3, Y1, 0.0, 0.9, M['plaster'][2], M['plaster'][2], 'ES')
        self.a['L2'].box(X1 - 0.3, X1, Y0, Y1, 0.0, 0.9, M['plaster'][2], M['plaster'][2], 'ES')
        for k in range(3 + int(3 * hsh(seed, 3.3))):
            px = X0 + 1.0 + (X1 - X0 - 2.0) * hsh(seed, k, 1.4); py = Y0 + 1.0 + (Y1 - Y0 - 2.0) * hsh(seed, k, 2.6)
            r = 0.6 + 0.6 * hsh(seed, k, 3.9)
            self.a['L6'].blob(px, py, 0.14 + r * 0.9, r, r, r * 0.9, M['plant'][k % 2], 1, 0.18, seed + k * 3, M['plant'][1], None)
        self.a['L4'].cyl((X0 + X1) / 2, (Y0 + Y1) / 2, 0.45, 0.14, 0.5, M['marble'], 8)

    def temple(self, X0, X1, Y0, Y1, seed):
        """작은 신전(L2 기둥·L4 박공): 대리석 기단 + 앞 기둥 4 + 박공"""
        M = self.M
        h0 = 0.8
        self.a['L0'].box(X0, X1, Y0, Y1, 0.0, h0, M['marble'], M['marble'])
        cx0, cx1 = X0 + 0.6, X1 - 0.6
        cy0, cy1 = Y0 + (Y1 - Y0) * 0.35, Y1 - 0.6
        self.a['L0'].box(cx0, cx1, Y0 + 0.4, cy0, h0, h0 + 3.0, M['marble'], M['marble'])
        for k in range(4):
            x = cx0 + 0.25 + (cx1 - cx0 - 0.5) * k / 3
            self.a['L2'].cyl(x, cy1 - 0.25, 0.22, h0, h0 + 3.0, M['marble'], 8)
            self.a['L2'].cyl(x, cy0 + 0.6, 0.22, h0, h0 + 3.0, M['marble'], 8)
        self.a['L1'].face([V(cx0 + 0.2, cy0 + 0.01, h0), V(cx1 - 0.2, cy0 + 0.01, h0), V(cx1 - 0.2, cy0 + 0.01, h0 + 2.6), V(cx0 + 0.2, cy0 + 0.01, h0 + 2.6)], M['win'], (0, -1, 0))
        self.a['L2'].box(cx0 - 0.15, cx1 + 0.15, Y0 + 0.25, cy1 + 0.15, h0 + 3.0, h0 + 3.4, M['cornice'], M['cornice'])
        self.gable(cx0, cx1, Y0 + 0.4, cy1, h0 + 3.4, 'Y', 'a', 0.15, M['marble'])
        for s in range(3):
            self.a['L4'].box(cx0, cx1, Y1 + 0.0 + 0.35 * s, Y1 + 0.35 * (s + 1), 0.0, h0 * (1 - s / 3.0), M['marble'], M['marble'])

    def house(self, X0, X1, Y0, Y1, kind, seed, z0, shop_s, shop_e):
        M = self.M
        pal = 'a' if hsh(seed, 1.7) < 0.6 else 'b'
        if kind == 'ins':
            h = z0 + 3.6 + 2.4 * hsh(seed, 2.1)
            wm = M['brick'] if hsh(seed, 3.1) < 0.45 else M['plaster'][int(5 * hsh(seed, 4.1)) % 5]
        elif kind == 'dom':
            h = z0 + 2.5 + 0.9 * hsh(seed, 2.3)
            wm = M['plaster'][int(5 * hsh(seed, 4.3)) % 5]
        else:
            h = z0 + 2.7 + 1.4 * hsh(seed, 2.5)
            wm = M['plaster'][int(5 * hsh(seed, 4.5)) % 5] if hsh(seed, 3.5) < 0.75 else M['brick']
        self.walls(X0, X1, Y0, Y1, z0, h, wm)
        self.openings(X0, X1, Y0, Y1, z0, h, seed, shop_s, shop_e)
        self.eaves(X0, X1, Y0, Y1, h)
        if kind == 'dom' and min(X1 - X0, Y1 - Y0) > 5.0:
            self.atrium(X0, X1, Y0, Y1, h, pal, seed)
            top = h + 0.7
        elif kind == 'ins' and hsh(seed, 5.7) < 0.22:
            self.terrace(X0, X1, Y0, Y1, h, seed)
            top = h + 1.1
        else:
            axis = 'X' if (X1 - X0) >= (Y1 - Y0) else 'Y'
            if hsh(seed, 6.3) < 0.25:
                axis = 'Y' if axis == 'X' else 'X'
            top = h + self.gable(X0, X1, Y0, Y1, h, axis, pal, 0.22, wm)
            # L4 발코니(인술라 2층 나무 발코니)
            if kind == 'ins' and hsh(seed, 7.9) < 0.45:
                zb = z0 + 1.55 * 2 - 0.05
                self.a['L4'].box(X0 + 0.4, X1 - 0.4, Y1, Y1 + 0.5, zb, zb + 0.12, M['balc'], M['balc'])
                self.a['L4'].face([V(X0 + 0.4, Y1 + 0.5, zb + 0.12), V(X1 - 0.4, Y1 + 0.5, zb + 0.12), V(X1 - 0.4, Y1 + 0.5, zb + 0.5), V(X0 + 0.4, Y1 + 0.5, zb + 0.5)], M['balc'], (0, -1, 0))
                if hsh(seed, 8.3) < 0.6:
                    for k in range(int((X1 - X0) / 1.8)):
                        px = X0 + 0.9 + 1.8 * k
                        self.a['L6'].blob(px, Y1 + 0.3, zb + 0.62, 0.22, 0.2, 0.18, M['plant'][k % 2], 0, 0.1, seed + k)
        self.n += 1
        return top


def build_city(GC, M, W, root):
    """시내 지붕의 바다: 평면 격자(길과 같은 축) 블록 → 집 2~6채/블록, 도무스·정원·작은 신전 섞음"""
    C = City(M)
    PX, PY = 10.4, 9.8
    X0g, Y0g = 269.83 - 5.2, 118.18 - 4.9
    blocks = 0
    for i in range(-17, 36):
        for j in range(-31, 22):
            bx0 = X0g + i * PX; by0 = Y0g + j * PY
            st = 1.5 + (1.0 if i % 4 == 0 else 0.0)
            sy = 1.5 + (1.0 if j % 4 == 0 else 0.0)
            BX0, BX1 = bx0 + st / 2, bx0 + PX - 0.75
            BY0, BY1 = by0 + sy / 2, by0 + PY - 0.75
            seed = i * 131.0 + j * 17.0
            if BY1 > A1_Y0 - 2.0 or BY0 > A1_Y0:
                continue
            sbb = sbox(BX0, BX1, BY0, BY1, 0.0)
            if sbb[2] < -6 or sbb[0] > 352.0 or sbb[3] < 90.0:
                continue
            if sbb[3] > (404.0 if sbb[2] < 206.0 else 384.0):
                continue          # 히어로 앞(지시선 A·Z1 둘레)은 목초지로 비운다. 강 굽이 안쪽 도심은 채운다
            if sbb[0] > 296.0 and sbb[1] < 170.0:
                continue
            r = hsh(seed, 0.3)
            kind = 'ins' if r < 0.56 else ('dom' if r < 0.875 else ('garden' if r < 0.975 else 'temple'))
            lots = []
            if kind == 'ins':
                # 설계 d4 지붕 크기(평면 5~8 mm, 높이 3.4~5.8)에 맞춰 블록당 1~4채(예전 4~9채): 설계 = 와이어프레임 청사진(사용자 13:40)
                nx = 1 if hsh(seed, 0.7) < 0.35 else 2
                ny = 1 if hsh(seed, 0.8) < 0.35 else 2
                cx = [BX0] + [BX0 + (BX1 - BX0) * (k + 0.35 + 0.3 * hsh(seed, k, 1.1)) / nx for k in range(nx - 1)] + [BX1]
                cy = [BY0] + [BY0 + (BY1 - BY0) * (k + 0.35 + 0.3 * hsh(seed, k, 2.1)) / ny for k in range(ny - 1)] + [BY1]
                for a in range(nx):
                    for b in range(ny):
                        lots.append((cx[a], cx[a + 1], cy[b], cy[b + 1], 'ins' if hsh(seed, a, b) < 0.7 else 'small'))
            elif kind == 'dom':
                sx = BX0 + (BX1 - BX0) * 0.72
                lots.append((BX0, sx, BY0, BY1, 'dom'))
                lots.append((sx, BX1, BY0, (BY0 + BY1) / 2, 'small'))
                lots.append((sx, BX1, (BY0 + BY1) / 2, BY1, 'small'))
            else:
                lots.append((BX0, BX1, BY0, BY1, kind))
            placed = 0
            for (x0, x1, y0, y1, kd) in lots:
                hmax = 9.0 if kd == 'ins' else 5.0
                sb = sbox(x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, hmax)
                if not W.stage_ok(sb) or y1 > A1_Y0 - 1.6:
                    continue
                if W.road_hit(x0, x1, y0, y1, 0.9) or W.river_hit(x0, x1, y0, y1, 1.6) or W.hero_hit(x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, HERO_KEEP):
                    continue
                if W.screen_hit(sb, (W.k_land, W.k_prop, W.k_info, W.k_text)) or W.leader_hit(sb, 1.5):
                    continue
                if W.occupied(x0, x1, y0, y1):
                    continue
                sd = int(seed * 7 + x0 * 3 + y0)
                near_road_s = W.road_hit(x0, x1, y1, y1 + 3.5, 0.0)
                near_road_e = W.road_hit(x1, x1 + 3.5, y0, y1, 0.0)
                # 블록 연석 판(L2)
                C.a['L2'].box(x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, 0.0, 0.12, M['kerb'], M['kerb_side'], 'ES')
                if kd == 'garden':
                    C.garden(x0, x1, y0, y1, sd)
                elif kd == 'temple':
                    C.temple(x0, x1, y0, y1, sd)
                else:
                    C.house(x0, x1, y0, y1, kd, sd, 0.12, near_road_s or hsh(sd, 1.9) < 0.25, near_road_e or hsh(sd, 2.9) < 0.25)
                W.occupy(x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, 'house')
                placed += 1
                if hsh(sd, 4.7) < 0.12:
                    C.people.append((x1 + 0.9, y1 + 0.8 * hsh(sd, 5.3), 0.0))
            blocks += 1 if placed else 0
    ring = ring_fill(C, W, M)
    rt = root
    for k, a in C.a.items():
        nm = {'L0': 'Masses', 'L1': 'Openings', 'L2': 'Members', 'L3': 'RoofTiles', 'L4': 'Details', 'L5': 'Highlights', 'L6': 'Life'}[k]
        a.obj('GROUND_City_%s_%s' % (k, nm), GC, rt)
    W.ring = ring
    np_ = place_people(GC, W, M, rt, C.people[:60], 'GROUND_City_L6_Person')
    return C.n, blocks, np_


def ring_fill(C, W, M):
    """조경 예약 원(R 90.5) 바로 밖 첫 집 줄: 빈 띠 ≤ 3 mm(평면, D14). 도시 조직이 콜로세움 군까지 이어진다(8.2)"""
    Rin = HERO_KEEP + 0.4
    th = 0.0; k = 0; n = 0; gaps = []
    while th < 2 * math.pi:
        w = 4.6 + 1.6 * hsh(k, 1.1); d = 4.0 + 1.4 * hsh(k, 2.2)
        ux, uy = math.cos(th), math.sin(th)
        hw, hd = w / 2, d / 2
        rc = Rin + 0.3 + hw * abs(ux) + hd * abs(uy)
        cx, cy = HERO_C[0] + rc * ux, HERO_C[1] + rc * uy
        x0, x1, y0, y1 = cx - hw, cx + hw, cy - hd, cy + hd
        th += (max(w, d) + 0.9) / rc; k += 1
        kd = 'dom' if hsh(k, 3.3) < 0.5 else 'small'          # 낮은 집(조경 둘레가 콜로세움 실루엣을 가리지 않게)
        sb = sbox(x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, 5.0)
        if not W.stage_ok(sb) or y1 > A1_Y0 - 1.6 and y0 < A1_Y1 + 1.6:
            continue
        if sb[3] > 384.0 and sb[0] > 206.0 and sb[2] < 318.0:
            continue          # 히어로 앞 목초지(공사장·Z1 둘레)
        if W.road_hit(x0, x1, y0, y1, 0.9) or W.river_hit(x0, x1, y0, y1, 1.6) or W.hero_hit(x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, HERO_KEEP):
            continue
        if W.screen_hit(sb, (W.k_land, W.k_prop, W.k_info, W.k_text)) or W.leader_hit(sb, 1.5) or W.occupied(x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3):
            continue
        sd = int(cx * 7 + cy * 3)
        C.a['L2'].box(x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, 0.0, 0.12, M['kerb'], M['kerb_side'], 'ES')
        C.house(x0, x1, y0, y1, kd, sd, 0.12, hsh(sd, 1.9) < 0.4, hsh(sd, 2.9) < 0.4)
        W.occupy(x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, 'house')
        qx = min(max(HERO_C[0], x0), x1); qy = min(max(HERO_C[1], y0), y1)
        gaps.append(round(math.hypot(qx - HERO_C[0], qy - HERO_C[1]) - HERO_KEEP, 2))
        n += 1
    return {'n': n, 'gap_max_mm': max(gaps) if gaps else None, 'gap_min_mm': min(gaps) if gaps else None}


# ───────────────────────── 밭·포도밭·목초지(spec planted·terrain) ─────────────────────────
def build_fields(GC, M, W, CM, root):
    A = {k: Acc() for k in ('L0', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6')}
    pl = {p['name']: p for p in CM['planted']}
    zones = []   # (화면 상자, 종류)
    for p in CM['planted']:
        nm = p['name']
        kind = 'vine' if '포도' in nm else ('far' if '먼' in nm else ('grain' if ('곡식' in nm or '밭' in nm) else None))
        if kind:
            zones.append((p['box'], kind, p.get('cover', 0.3)))
    for t in CM['terrain']:
        nm = t['name']
        if '캄파냐' in nm and '남동' in nm:
            zones.append((t['box'], 'mix', 0.3))
        elif '포르투스 띠' in nm:
            zones.append((t['box'], 'grain', 0.35))
    # 설계 d4 밭 청사진(render.py draw_fields 하구밭) + 히어로 앞 목초지(공사장·Z1 둘레, 낮고 고요하게)
    zones.append(((150.0, 425.0, 252.0, 505.0), 'grain', 0.3))
    zones.append(((252.0, 384.0, 318.0, 505.0), 'pasture', 0.3))
    sheep = 0; n = 0
    # L4 밭 오두막(작은 농가): 밭보다 먼저 자리를 잡는다
    huts = 0
    C = City(M)
    for zi, (zb, kind, cover) in enumerate(zones):
        if kind == 'far':
            continue
        for t in range(10):
            if huts >= 12:
                break
            sx = zb[0] + (zb[2] - zb[0]) * hsh(zi, t, 1.5); sy = zb[1] + (zb[3] - zb[1]) * hsh(zi, t, 2.5)
            X, Y = R.to_plan(sx, sy)
            x0, x1, y0, y1 = X, X + 3.8 + 1.2 * hsh(zi, t, 3.5), Y, Y + 3.0 + 0.8 * hsh(zi, t, 4.5)
            sb = sbox(x0, x1, y0, y1, 5.0)
            if not W.stage_ok(sb) or y1 > COAST_Y - 3.0 or W.screen_hit(sb, (W.k_land, W.k_prop, W.k_info, W.k_text)):
                continue
            if W.road_hit(x0, x1, y0, y1, 0.8) or W.river_hit(x0, x1, y0, y1, 1.5) or W.hero_hit(x0, x1, y0, y1, HERO_KEEP + 1.0):
                continue
            if W.leader_hit(sb, 1.0) or W.occupied(x0 - 1.5, x1 + 1.5, y0 - 1.5, y1 + 1.5):
                continue
            C.house(x0, x1, y0, y1, 'small', int(X * 7 + Y), 0.0, False, False)
            W.occupy(x0 - 0.6, x1 + 0.6, y0 - 0.6, y1 + 0.6, 'house'); huts += 1
            break
    for zi, (zb, kind, cover) in enumerate(zones):
        # 화면 상자 → 평면 마름모 외곽
        cs = [R.to_plan(x, y) for x, y in ((zb[0], zb[1]), (zb[2], zb[1]), (zb[2], zb[3]), (zb[0], zb[3]))]
        Xmin, Xmax = min(c[0] for c in cs), max(c[0] for c in cs)
        Ymin, Ymax = min(c[1] for c in cs), max(c[1] for c in cs)
        pw = 11.0 if kind != 'far' else 13.0
        pd = 8.5 if kind != 'far' else 9.0
        gap = 0.9
        X = Xmin
        ii = 0
        while X < Xmax:
            wx = pw * (0.75 + 0.5 * hsh(zi, ii, 1.3))
            Y = Ymin
            jj = 0
            while Y < Ymax:
                dy = pd * (0.75 + 0.5 * hsh(zi, ii, jj, 2.3))
                x0, x1, y0, y1 = X + gap / 2, X + wx - gap / 2, Y + gap / 2, Y + dy - gap / 2
                Y += dy; jj += 1
                corners = [S(x0, y0), S(x1, y0), S(x1, y1), S(x0, y1)]
                if not all(zb[0] <= cx <= zb[2] and zb[1] <= cy <= zb[3] for cx, cy in corners):
                    continue
                sb = sbox(x0, x1, y0, y1, 0.2)
                if not W.stage_ok(sb) or y1 > COAST_Y - 1.4:
                    continue
                if W.road_hit(x0, x1, y0, y1, 0.8) or W.river_hit(x0, x1, y0, y1, 1.0) or W.hero_hit(x0, x1, y0, y1, HERO_KEEP):
                    continue
                if W.screen_hit(sb, (W.k_land, W.k_prop)) or W.occupied(x0, x1, y0, y1):
                    continue
                if W.screen_hit(sb, (W.k_info, W.k_text)):
                    continue          # 패널·라벨·바닥 글 밑은 빈 땅(고요한 영역)
                if kind == 'far' and sb[3] > 62.0:
                    continue          # 알바노 구릉 띠(suburb)와 겹치지 않게
                quiet = W.leader_hit(sbox(x0, x1, y0, y1, 1.5), 1.0)
                sd = zi * 1000 + ii * 37 + jj
                r = hsh(sd, 0.9)
                ax = 'X' if hsh(sd, 1.9) < 0.5 else 'Y'
                if kind == 'far':
                    mt = (M['far1'], M['far2'], M['far3'])[int(3 * r) % 3]
                    A['L0'].box(x0, x1, y0, y1, 0.0, 0.06, mt, M['far3'])
                    W.occupy(x0, x1, y0, y1, 'field'); n += 1
                    continue
                if kind == 'vine' or (kind == 'mix' and r < 0.45):
                    sub = 'vine' if not quiet else 'pasture'
                elif kind == 'pasture':
                    sub = 'pasture' if r < 0.7 else 'fallow'
                else:
                    sub = ('wheat', 'green', 'plow', 'pasture', 'wheat')[int(5 * r) % 5]
                if sub == 'vine':
                    A['L1'].box(x0, x1, y0, y1, 0.0, 0.1, M['vine_soil'], M['field_side'])
                    pitch = 1.15
                    if ax == 'X':
                        yy = y0 + 0.6
                        while yy < y1 - 0.6:
                            A['L3'].box(x0 + 0.5, x1 - 0.5, yy - 0.22, yy + 0.22, 0.1, 0.78, M['vine'], M['vine'])
                            A['L5'].face([V(x0 + 0.5, yy - 0.22, 0.83), V(x1 - 0.5, yy - 0.22, 0.83), V(x1 - 0.5, yy - 0.05, 0.83), V(x0 + 0.5, yy - 0.05, 0.83)], M['vine_hi'], (0, 0, 1))
                            A['L4'].box(x1 - 0.48, x1 - 0.36, yy - 0.06, yy + 0.06, 0.1, 1.0, M['stake'], M['stake'])
                            if hsh(sd, yy, 3.1) < 0.5:
                                gx = x0 + 1.0 + (x1 - x0 - 2.0) * hsh(sd, yy, 4.1)
                                A['L6'].face([V(gx, yy + 0.23, 0.35), V(gx + 0.28, yy + 0.23, 0.35), V(gx + 0.28, yy + 0.23, 0.62), V(gx, yy + 0.23, 0.62)], M['grape'], (0, -1, 0))
                            yy += pitch
                    else:
                        xx = x0 + 0.6
                        while xx < x1 - 0.6:
                            A['L3'].box(xx - 0.22, xx + 0.22, y0 + 0.5, y1 - 0.5, 0.1, 0.78, M['vine'], M['vine'])
                            A['L5'].face([V(xx - 0.22, y0 + 0.5, 0.83), V(xx - 0.05, y0 + 0.5, 0.83), V(xx - 0.05, y1 - 0.5, 0.83), V(xx - 0.22, y1 - 0.5, 0.83)], M['vine_hi'], (0, 0, 1))
                            A['L4'].box(xx - 0.06, xx + 0.06, y1 - 0.48, y1 - 0.36, 0.1, 1.0, M['stake'], M['stake'])
                            if hsh(sd, xx, 3.7) < 0.5:
                                gy = y0 + 1.0 + (y1 - y0 - 2.0) * hsh(sd, xx, 4.7)
                                A['L6'].face([V(xx + 0.23, gy, 0.35), V(xx + 0.23, gy + 0.28, 0.35), V(xx + 0.23, gy + 0.28, 0.62), V(xx + 0.23, gy, 0.62)], M['grape'], (1, 0, 0))
                            xx += pitch
                else:
                    mt = {'wheat': M['wheat' + ax], 'green': M['green' + ax], 'plow': M['plow' + ax], 'pasture': M['pasture'] if r < 0.5 else M['pasture2'], 'fallow': M['fallow']}[sub]
                    A['L0'].box(x0, x1, y0, y1, 0.0, 0.12, mt, M['field_side'])
                    if not quiet:
                        if sub == 'wheat' and hsh(sd, 5.1) < 0.45:
                            for k in range(2 + int(3 * hsh(sd, 5.9))):
                                hx = x0 + 1.0 + (x1 - x0 - 2.0) * hsh(sd, k, 6.1); hy = y0 + 1.0 + (y1 - y0 - 2.0) * hsh(sd, k, 6.7)
                                A['L4'].blob(hx, hy, 0.35, 0.55, 0.55, 0.55, M['hay'], 1, 0.08, sd + k, M['hay_hi'], None)
                        if sub == 'pasture':
                            for k in range(2 + int(5 * hsh(sd, 7.3))):
                                sx_ = x0 + 0.8 + (x1 - x0 - 1.6) * hsh(sd, k, 7.9); sy_ = y0 + 0.8 + (y1 - y0 - 1.6) * hsh(sd, k, 8.3)
                                A['L6'].blob(sx_, sy_, 0.42, 0.42, 0.3, 0.26, M['sheep'], 0, 0.1, sd + k)
                                A['L6'].box(sx_ + 0.35, sx_ + 0.55, sy_ - 0.1, sy_ + 0.1, 0.32, 0.56, M['sheep_hd'], M['sheep_hd'])
                                sheep += 1
                # L2 생울타리·돌담(밭의 뒤 두 변)
                if not quiet and kind != 'far':
                    hm = M['hedge'] if hsh(sd, 9.3) < 0.65 else None
                    if hm is not None:
                        A['L2'].box(x0, x1, y0 - 0.5, y0 - 0.05, 0.0, 0.62, hm, hm)
                        A['L2'].box(x0 - 0.5, x0 - 0.05, y0 - 0.5, y1, 0.0, 0.62, hm, hm)
                        A['L5'].face([V(x0, y0 - 0.5, 0.67), V(x1, y0 - 0.5, 0.67), V(x1, y0 - 0.33, 0.67), V(x0, y0 - 0.33, 0.67)], M['hedge_hi'], (0, 0, 1))
                    else:
                        A['L2'].box(x0, x1, y0 - 0.42, y0 - 0.08, 0.0, 0.42, M['wall'], M['wall'])
                W.occupy(x0, x1, y0, y1, 'field'); n += 1
            X += wx; ii += 1
    nmz ={'L0': 'Parcels', 'L1': 'VineSoil', 'L2': 'HedgesWalls', 'L3': 'VineRows', 'L4': 'HayStakes', 'L5': 'RowHighlights', 'L6': 'SheepGrapes'}
    for k, a in A.items():
        a.obj('GROUND_Fields_%s_%s' % (k, nmz[k]), GC, root)
    nmh = {'L0': 'Masses', 'L1': 'Openings', 'L2': 'Members', 'L3': 'RoofTiles', 'L4': 'Details', 'L5': 'Highlights', 'L6': 'Life'}
    for k, a in C.a.items():
        a.obj('GROUND_Fields_Huts_%s_%s' % (k, nmh[k]), GC, root)
    return n, sheep, huts


# ───────────────────────── 나무 무리(층별 메시: L0 수관 · L1 수관 아래 그늘 · L2 줄기 · L3 잎 면 · L4 수관 덩이 · L5 꼭대기 하이라이트 · L6 밑동 풀) ─────────────────────────
# D8 비례(사람 키 2.4 기준, 화면 mm = 높이 BU): 사이프러스 2.5~3.0배(6.0~7.2) · 올리브 2.2배(5.3) · 우산소나무 3.0배(7.2)
TREE_R = {'umbrella': 2.6, 'cypress': 0.85, 'olive': 1.9, 'round': 1.8, 'poplar': 1.0}
TREE_H = {'umbrella': 7.2, 'cypress': 6.6, 'olive': 5.3, 'round': 5.4, 'poplar': 6.6}


class Trees:
    def __init__(self, M):
        self.M = M
        self.a = {k: Acc() for k in ('L0', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6')}
        self.n = 0

    def blob(self, lay, cx, cy, cz, rx, ry, rz, mat, mat_hi, mat_lo, sub=1, jit=0.16, seed=0.0, split=True):
        """잎 덩이: 아래쪽 면(nz < −0.15) → L1 그늘색, 왼쪽 위 면 → L5 하이라이트, 나머지 → lay 층(빛 계산이 아닌 색 지정)"""
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
        for v in bm.verts:
            d = v.co.copy()
            j = 1.0 + jit * (hsh(d.x * 13.1 + seed, d.y * 7.7, d.z * 5.3) * 2 - 1)
            v.co = Vector((cx + d.x * rx * j, -cy + d.y * ry * j, cz + d.z * rz * j))
        bm.normal_update()
        for f in bm.faces:
            nz = f.normal.z
            pts = [v.co.copy() for v in f.verts]
            if split and nz < -0.15:
                self.a['L1'].face(pts, mat_lo or mat)
            elif split and nz > 0.5 and (f.normal.x - f.normal.y) < 0.35:
                self.a['L5'].face(pts, mat_hi or mat)
            else:
                self.a[lay].face(pts, mat)
        bm.free()

    def facets(self, cx, cy, cz, rx, ry, rz, mat, seed, n=7):
        """L3 잎 면: 수관 겉에 작은 삼각 잎 조각(밝은·짙은 잎결)"""
        for k in range(n):
            t = 2 * math.pi * hsh(seed, k, 1.3); p = math.acos(1 - 2 * (0.15 + 0.6 * hsh(seed, k, 2.3)))
            nx, ny, nz = math.sin(p) * math.cos(t), math.sin(p) * math.sin(t), math.cos(p)
            if nx - ny < -0.2:          # 보이는 쪽(카메라 쪽 반구)만
                continue
            px, py, pz = cx + rx * 1.03 * nx, cy - ry * 1.03 * ny, cz + rz * 1.03 * nz
            s_ = 0.22 + 0.18 * hsh(seed, k, 3.3)
            self.a['L3'].face([V(px - s_, py, pz - s_ * 0.6), V(px + s_, py, pz - s_ * 0.4), V(px + s_ * 0.2, py - s_ * 0.3, pz + s_ * 0.8)], mat, (0.4, -0.4, 1.0))

    def base(self, X, Y, r, seed):
        """L6 밑동 풀: 둥근 풀밭 조각 + 풀 포기"""
        M = self.M
        pts = [(X + r * 1.15 * math.cos(2 * math.pi * k / 10), Y + r * 0.95 * math.sin(2 * math.pi * k / 10)) for k in range(10)]
        self.a['L6'].face([V(x, y, 0.02) for x, y in pts], M['t_ground'], (0, 0, 1))
        for t in range(3):
            tx = X + r * 1.1 * (hsh(seed, t, 4.1) - 0.5) * 2; ty = Y + r * 0.9 * (hsh(seed, t, 5.1) - 0.5) * 2
            hh = 0.45 + 0.35 * hsh(seed, t, 6.1)
            mt = (M['tuft'], M['tuft2'], M['tuft3'])[t % 3]
            self.a['L6'].face([V(tx - 0.28, ty, 0.0), V(tx + 0.28, ty, 0.0), V(tx + 0.04, ty, hh)], mt, (0, -1, 0))

    def add(self, kind, X, Y, s, seed):
        M = self.M; f = 1.0 if hsh(seed, 0.5) < 0.5 else -1.0
        H = TREE_H[kind] * s
        if kind == 'umbrella':          # 우산소나무: 긴 줄기 + 납작한 우산 수관
            self.base(X, Y, 1.4 * s, seed)
            self.a['L2'].cyl(X, Y, 0.2 * s, 0.0, H * 0.72, M['bark'], 6)
            self.a['L2'].box(X, X + 0.8 * s * f, Y - 0.09, Y + 0.09, H * 0.5, H * 0.53, M['bark'], M['bark'])
            self.blob('L0', X, Y, H * 0.8, 2.4 * s, 2.2 * s, 0.75 * s, M['t_pine'], M['t_pine_hi'], M['t_pine_lo'], 1, 0.14, seed)
            self.blob('L4', X + 0.8 * s * f, Y - 0.4 * s * f, H * 0.9, 1.25 * s, 1.15 * s, 0.45 * s, M['t_pine'], M['t_pine_hi'], M['t_pine_lo'], 1, 0.15, seed + 2)
            self.facets(X, Y, H * 0.8, 2.4 * s, 2.2 * s, 0.75 * s, M['t_pine_hi'], seed, 9)
        elif kind == 'cypress':         # 사이프러스: 좁고 높은 불꽃 모양
            self.base(X, Y, 0.7 * s, seed)
            self.a['L2'].cyl(X, Y, 0.14 * s, 0.0, 0.7 * s, M['bark'], 6)
            self.blob('L0', X, Y, H * 0.45, 0.78 * s, 0.78 * s, H * 0.42, M['t_cyp'], M['t_cyp_hi'], M['t_cyp'], 1, 0.12, seed)
            self.blob('L4', X, Y, H * 0.8, 0.5 * s, 0.5 * s, H * 0.2, M['t_cyp'], M['t_cyp_hi'], M['t_cyp'], 1, 0.14, seed + 3)
            self.facets(X, Y, H * 0.45, 0.78 * s, 0.78 * s, H * 0.42, M['t_cyp_hi'], seed, 6)
        elif kind == 'olive':           # 올리브: 갈라진 줄기 + 은록 덩이 셋
            self.base(X, Y, 1.2 * s, seed)
            self.a['L2'].cyl(X, Y, 0.24 * s, 0.0, H * 0.38, M['bark'], 6)
            self.a['L2'].box(X - 0.1, X + 0.1, Y, Y + 0.7 * s * f, H * 0.3, H * 0.34, M['bark'], M['bark'])
            self.blob('L0', X, Y, H * 0.66, 1.55 * s, 1.5 * s, 1.2 * s, M['t_olive'], M['t_olive_hi'], M['t_olive_lo'], 1, 0.2, seed)
            for k in range(2):
                ang = math.pi * k + 0.6 + 0.4 * f
                self.blob('L4', X + 1.0 * s * math.cos(ang), Y + 1.0 * s * math.sin(ang), H * 0.6, 0.9 * s, 0.85 * s, 0.7 * s,
                          M['t_olive'], M['t_olive_hi'], M['t_olive_lo'], 1, 0.22, seed + 5 + k)
            self.facets(X, Y, H * 0.66, 1.55 * s, 1.5 * s, 1.2 * s, M['t_olive_hi'], seed, 8)
        elif kind == 'poplar':          # 미루나무(강둑)
            self.base(X, Y, 0.8 * s, seed)
            self.a['L2'].cyl(X, Y, 0.13 * s, 0.0, H * 0.25, M['bark'], 6)
            self.blob('L0', X, Y, H * 0.58, 0.85 * s, 0.85 * s, H * 0.4, M['t_round'], M['t_round_hi'], M['t_round_lo'], 1, 0.14, seed)
            self.blob('L4', X, Y, H * 0.88, 0.5 * s, 0.5 * s, H * 0.14, M['t_round'], M['t_round_hi'], M['t_round_lo'], 1, 0.14, seed + 7)
            self.facets(X, Y, H * 0.58, 0.85 * s, 0.85 * s, H * 0.4, M['t_round_hi'], seed, 6)
        else:                           # 둥근 활엽수
            self.base(X, Y, 1.1 * s, seed)
            self.a['L2'].cyl(X, Y, 0.18 * s, 0.0, H * 0.4, M['bark'], 6)
            self.blob('L0', X, Y, H * 0.62, 1.5 * s, 1.5 * s, 1.35 * s, M['t_round'], M['t_round_hi'], M['t_round_lo'], 1, 0.16, seed)
            self.blob('L4', X - 0.6 * s * f, Y + 0.5 * s, H * 0.82, 0.85 * s, 0.85 * s, 0.7 * s, M['t_round'], M['t_round_hi'], M['t_round_lo'], 1, 0.16, seed + 9)
            self.facets(X, Y, H * 0.62, 1.5 * s, 1.5 * s, 1.35 * s, M['t_round_hi'], seed, 8)
        self.n += 1

    def objs(self, GC, root):
        nm = {'L0': 'Crowns', 'L1': 'CrownShade', 'L2': 'Trunks', 'L3': 'LeafFacets', 'L4': 'Clumps', 'L5': 'TopHighlights', 'L6': 'BaseGrass'}
        for k, a in self.a.items():
            a.obj('GROUND_Trees_%s_%s' % (k, nm[k]), GC, root)


def build_trees(GC, M, W, CM, root):
    T = Trees(M)
    def put(kind, X, Y, s=1.0, allow_field=False, check=True, texts=True):
        r = TREE_R[kind] * s; h = TREE_H[kind] * s
        x0, x1, y0, y1 = X - r, X + r, Y - r, Y + r
        if check:
            sb = sbox(x0, x1, y0, y1, h)
            if not W.stage_ok(sb) or y1 > COAST_Y - 1.0:
                return False
            if sb[2] > 296.0 and sb[1] < 168.0:
                return False      # 가장 먼 곳·알바노 구릉(suburb) 구역
            if sb[3] > 384.0 and sb[0] > 206.0 and sb[2] < 318.0:
                return False      # 히어로 앞 목초지(공사장·Z1 둘레)는 낮게 비운다(설계 d4 그대로)
            if W.road_hit(x0, x1, y0, y1, 0.3) or W.river_hit(x0, x1, y0, y1, 0.6) or W.hero_hit(x0, x1, y0, y1, HERO_KEEP):
                return False
            if W.screen_hit(sb, (W.k_land, W.k_prop, W.k_info) + ((W.k_text,) if texts else ())) or W.leader_hit(sb, 1.0):
                return False
            if W.occupied(x0, x1, y0, y1, ignore=('field',) if allow_field else ()):
                return False
        T.add(kind, X, Y, s * (0.92 + 0.16 * hsh(Y, X, 1.3)), X * 3.1 + Y)
        W.occupy(X - r * 0.8, X + r * 0.8, Y - r * 0.8, Y + r * 0.8, 'tree')
        return True
    # 1) 아피아 가도 가로수 열은 suburb(SUB_AppiaTrees)가 짓는다(APPIA_ROW_BY_SUBURB)
    # 2) spec planted 나무 구역
    for p in CM['planted']:
        nm = p['name']; zb = p['box']; cover = p.get('cover', 0.3)
        if '올리브' in nm:
            kinds, sc, step = ('olive',), 1.0, 4.6
        elif '소나무' in nm and '오스티아' in nm:
            kinds, sc, step = ('umbrella', 'umbrella', 'cypress'), 1.0, 6.4
        else:
            continue
        cs = [R.to_plan(x, y) for x, y in ((zb[0], zb[1]), (zb[2], zb[1]), (zb[2], zb[3]), (zb[0], zb[3]))]
        Xmin, Xmax = min(c[0] for c in cs), max(c[0] for c in cs); Ymin, Ymax = min(c[1] for c in cs), max(c[1] for c in cs)
        X = Xmin; i = 0
        while X < Xmax:
            Y = Ymin; j = 0
            while Y < Ymax:
                px, py = X + step * 0.6 * (hsh(i, j, 1.1) - 0.5), Y + step * 0.6 * (hsh(i, j, 2.1) - 0.5)
                sx, sy = S(px, py)
                if zb[0] <= sx <= zb[2] and zb[1] <= sy <= zb[3] and hsh(i, j, 3.1) < cover * 1.9:
                    put(kinds[int(len(kinds) * hsh(i, j, 4.1)) % len(kinds)], px, py, sc * (0.9 + 0.2 * hsh(i, j, 5.1)))
                Y += step; j += 1
            X += step; i += 1
    # 3) 설계 d4 나무 무리 자리(render.py draw_scatter의 나무 영역: 화면 상자, 종류) — 설계 = 와이어프레임 청사진(사용자 13:40)
    BLUE = [((0, 96, 18, 300), 'tree'), ((18, 182, 116, 198), 'cyp'), ((40, 290, 92, 336), 'tree'), ((146, 452, 236, 503), 'pine'),
            ((150, 226, 236, 262), 'olive'), ((296, 300, 356, 340), 'tree'), ((330, 386, 420, 505), 'cyp'), ((0, 290, 40, 326), 'tree'),
            ((112, 190, 228, 238), 'olive')]
    for bi, (zb, kd) in enumerate(BLUE):
        step = {'tree': 7.0, 'cyp': 8.5, 'pine': 7.5, 'olive': 6.5}[kd]
        y = zb[1] + 2.5; row = 0
        while y < zb[3]:
            x = zb[0] + (step / 2.0 if row % 2 else 0.0) + 1.5
            while x < zb[2]:
                xx = x + 1.6 * (hsh(bi, x, y) - 0.5); yy = y + 1.2 * (hsh(bi, y, x) - 0.5)
                X, Y = R.to_plan(xx, yy)
                r_ = hsh(bi, xx, yy, 7.7)
                kind = {'tree': ('round', 'umbrella', 'cypress', 'olive')[int(4 * r_) % 4], 'cyp': 'cypress' if r_ < 0.75 else 'umbrella',
                        'pine': 'umbrella' if r_ < 0.7 else 'cypress', 'olive': 'olive' if r_ < 0.8 else 'cypress'}[kd]
                if hsh(bi, xx, yy, 9.1) < 0.62:
                    put(kind, X, Y, 0.95 + 0.15 * hsh(bi, xx, 3.3), allow_field=True)
                x += step
            y += step * 0.72; row += 1
    # 4) 시내 나무 덩어리(언덕·빈 블록 자리) + 강둑 미루나무
    for s_ in range(420):
        X = 150.0 + 560.0 * hsh(s_, 7.7); Y = -230.0 + 600.0 * hsh(s_, 8.8)
        sx, sy = S(X, Y)
        city = Y < A1_Y0 - 2 and sx < 352.0 and not (sx > 296 and sy < 170)
        if not city and hsh(s_, 9.9) < 0.6:
            continue
        nn = 2 + int(4 * hsh(s_, 1.2))
        for t in range(nn):
            px = X + 3.6 * (hsh(s_, t, 2.2) - 0.5) * 2; py = Y + 3.6 * (hsh(s_, t, 3.3) - 0.5) * 2
            kind = ('round', 'umbrella', 'round', 'cypress', 'olive')[int(5 * hsh(s_, t, 4.4)) % 5]
            put(kind, px, py, 0.9 + 0.2 * hsh(s_, t, 5.5), allow_field=not city)
    j = 0
    Y = 328.0
    while Y < COAST_Y - 4.0:
        put('poplar', A2_X0 - 2.2, Y, 1.0); Y += 5.6 + 2.0 * hsh(j, 1.1); j += 1
    X = 300.0
    while X < 470.0:
        put('poplar', X, A1_Y1 + 2.2, 1.0, allow_field=True); X += 6.0 + 3.5 * hsh(j, 2.2); j += 1
    T.objs(GC, root)
    return T.n


# ───────────────────────── 짓기 ─────────────────────────
def _root(GC, name):
    ob = bpy.data.objects.new(name, None); GC.objects.link(ob); ob.empty_display_size = 6
    return ob


def build(stages=None, S_override=None):
    if stages is None:                 # 16:14 core만: 땅 판·해안 단면·강·폭포·바다
        stages = ('land', 'coast', 'river', 'falls', 'sea') + (('roads', 'city', 'fields', 'trees') if DECOR else ())
    S_ = S_override or json.load(open(SPEC, encoding='utf-8'))          # S_override: 시험용 spec(강 경로 시험)
    _spec_consts(S_)
    CM = S_['core_map']
    GC = R.coll(COLL, R.coll('ROMA_MAP'))
    R.clear_coll(COLL)
    for me in [m for m in bpy.data.meshes if m.name.startswith('GROUND_proto_') and m.users == 0]:
        bpy.data.meshes.remove(me)
    M = mats()
    W = World(S_, CM)
    if route_spec(CM) is not None and 'route' not in stages:
        stages = tuple(stages) + ('route',)                              # 16:41 입구·출구 길(설계 d5 R_route)
    roots = {k: _root(GC, 'GROUND_%s_root' % k) for k in ('Land', 'Coast', 'River', 'Falls', 'Sea', 'Roads', 'City', 'Fields', 'Trees', 'Route')
             if k in ('Land', 'Coast') or k.lower() in stages}          # 짓지 않는 단계의 빈 루트 0
    info = {'errors': {}, 'sec': {}}
    landob, rp = build_land(GC, M, CM, roots['Land'], roots['Coast'])      # 땅 판은 필수(실패하면 그대로 예외)
    W.rp = rp
    landob.parent = roots['Land']
    import time, traceback
    steps = [('coast', lambda: build_coast(GC, M, roots['Coast'])),
             ('river', lambda: (build_river_generic(GC, M, W, roots['River']) if GENERIC_RIVER else build_river(GC, M, rp, roots['River']))),
             ('falls', lambda: build_falls(GC, M, roots['Falls'])),
             ('sea', lambda: build_sea(GC, M, W, roots['Sea'])),
             ('roads', lambda: build_roads(GC, M, W, roots['Roads'])),
             ('city', lambda: build_city(GC, M, W, roots['City'])),
             ('fields', lambda: build_fields(GC, M, W, CM, roots['Fields'])),
             ('trees', lambda: build_trees(GC, M, W, CM, roots['Trees'])),
             ('route', lambda: build_route(GC, M, W, CM, roots['Route'])),
             ('patches', lambda: build_land_layers(GC, M, W, roots['Land']))]
    for nm, fn in steps:
        if nm != 'patches' and nm not in stages:
            continue
        t0 = time.time()
        try:
            r = fn()
            if r is not None:
                info[nm] = r
        except Exception:
            info['errors'][nm] = traceback.format_exc()[-1500:]
            print('[ground] %s 단계 오류:\n%s' % (nm, info['errors'][nm]))
        info['sec'][nm] = round(time.time() - t0, 2)
    info['ring'] = getattr(W, 'ring', None)
    GC['ground_excl'] = json.dumps({'land': W.k_land, 'prop': W.k_prop, 'info': W.k_info, 'text': W.k_text,
                                    'hero_c': HERO_C, 'hero_keep': HERO_KEEP, 'stage': STAGE})
    info['layers'] = layer_audit(GC)
    GC['ground_info'] = json.dumps(info, ensure_ascii=False)
    return GC


def layer_audit(GC):
    """루트마다 L0~L6 층 메시(빈 메시 금지)가 있는지(D10). bglobal roma_kit.layer_audit가 있으면 그것을 쓴다"""
    if hasattr(R, 'layer_audit'):
        try:
            return R.layer_audit(GC)
        except Exception:
            pass
    out = {}
    for ob in GC.objects:
        if ob.type != 'EMPTY' or not ob.name.endswith('_root'):
            continue
        have = set()
        for ch in ob.children_recursive:
            if ch.type != 'MESH' or not ch.data.polygons:
                continue
            nm = ch.name
            for n in range(8):
                if '_L%d_' % n in nm:
                    have.add(n)
        out[ob.name] = {'have': sorted(have), 'missing': [n for n in range(7) if n not in have]}
    return out
