# roma_pkg_coast — 포르투스(육각 내항·클라우디우스 외항·방파제·등대·운하·배)·하드리아누스 영묘+아일리우스 다리·오스티아·테베레 하역장·석회 가마·바지선·화산재 운반선. 담당: coast
# 오브젝트마다 표현 레이어 L0~L6(필수)를 쌓는다. 이름: {PKG}_{Obj}_L{n}_{part}, 루트 {PKG}_{Obj}_root. 지침: .work/blender/지침-일러스트-모델.md
# b5(통합 루프 1회차, 2026-10-19): 앞선 워커(06:25~ 오프라인)의 레이어 도구·창고·배 함수를 이어 쓰고, 위치·크기를 spec(current)+기획 결정(decisions)으로 바꿨다.
#   - 좌표 하드코딩 0: 육각 내항·외항·등대·운하(portus_geometry), 영묘·다리(L8 plan), 하역장(props 상자 → 평면 역산), 강둑(river), 해안선(sea_coast), 길 띠(roads R4·R7).
#   - D7: 다리 상판 보행면 3.0, 영묘 기단 북쪽 변 안쪽에 디딤 2단(윗면 3.67·4.33, 길이 2.0) → 기단 윗면 5.0. 다리 북쪽 끝 3.0은 ground R7 경사(0→3.0)와 만난다.
#   - D8: 사람 키 2.4(발~머리, 폭 = 키 × 0.32). 소품은 사람 키 비례(암포라 0.45·우산소나무 3.0·사이프러스 2.75·올리브 2.2).
#     fit_to_box로 축척하는 오브젝트(가마·오스티아·배)는 축척을 되돌려(1/s) 사람 키를 지킨다(2회 짓기).
#   - D9: 벡터 일러스트(방출 × ISO_TONE). 조명·AO·그림자·Principled 0. 물은 PAL 'water' 한 값(ground·hero와 같다). L7 외곽선 0.
#   - D11: 숨긴 앵커 6개 ANCHOR_{대상}_{역할}(L6_label·L6_c2·L8_label·BARGE1_label·ASH_label·EMP_label)를 보이는 면 위 3D 점에 둔다.
#   - D13: 겹치는 면의 간격 ≥ 0.05(DEC). 땅 파기는 X_CUT_Coast*(육각 수면·운하·하역장 아랫단)로만 한다.
# 높이: 땅 윗면 Z 0, 강 수면 −2, 바다 수면 −9.7(D13).
#  - 외항 방파제·등대섬 윗면은 땅과 같은 높이(Z 0, 등대섬 1.0)다(203X 홍콩처럼 땅 판의 팔이 바다로 뻗고, 바다 쪽 면은 콘크리트 층 단면 9.7mm를 보인다).
#    spec 화면 좌표(수면 높이 0으로 계산한 방파제 끝·등대 기저)는 윗면 외곽과 겹친다. 바다 쪽 옆면은 그 아래로 9.7mm 더 보인다(보고서에 두 상자를 함께 적는다).
#  - 육각 내항·운하 수면은 강보다 0.06 아래(WATER_Z). 외항 쪽 운하는 해안 단면에서 바다(−9.7)로 떨어진다(작은 물막이 폭포).
# 팔각 받침은 없다(사용자 06:06): 이 패키지의 모든 건물·소품은 받침 없이 지도 땅(Z 0)이나 물 위에 바로 놓인다.
import bpy, bmesh, math, json, re
from mathutils import Vector, Matrix
import roma_kit as R, roma_flat as FL, roma_geo as G

COLL = 'LM_Coast'
SPEC = '/Users/um-yunsang/roman-concrete-private-refs/.work/design/current/out/spec.json'
PKG = 'COAST'
DECOR = False      # 16:14 사용자 결정(core 정보 오브젝트만): 포르투스 구조물(육각 내항·운하·외항 방파제·등대)과 하드리아누스 영묘·아일리우스 다리만 짓는다.
#   바지선·화산재 운반선·포르투스 안의 배·오스티아·테베레 하역장·석회 가마, 구조물 위 사람·짐(암포라·자루)·나무는 짓지 않는다(코드는 보관)
C30 = math.cos(math.radians(30.0))

# ───────────────────────── 기획 결정(decisions) 상수: spec(current)와 다르면 이 값을 따른다 ─────────────────────────
RIVER_Z = -2.0             # D13 강 수면
SEA_Z = -9.7               # D13 바다 수면
WATER_Z = RIVER_Z - 0.06   # 육각 내항·운하 수면(ground 강 물 면 −2.0~−1.994와 겹치는 띠에서 0.06 아래 → z-파이팅 0)
PLAT_Z = 0.25              # 부두 포장 몸 윗면(+ 판석 무늬 0.05 = 보행면 0.30, ground 길 윗면과 같다. D13 포장 턱 ≤ 0.3)
DEC = 0.05                 # 겹치는 면 사이 최소 간격(D13 ≥ 0.05)
HEX_SEA = True             # 00:25 사용자 '육각형 내부 공간은 땅이 아니라 바다와 연결된 물': 육각 내항·외항 운하 수면 = 디오라마 바다(DI.WATER_Z) — 제 수면판·물막이 폭포 0
PORTUS_FIT = dict(s=1.256, pivot=(472.4, 380.0), canal_keep=(355.0, 385.0, 480.0))   # b7: 포르투스 네 루트 배율·기준점(평면) · 운하는 외항 쪽(평면 Y 355~385, X ≤ 480)만
H_PERSON = 2.4             # D8 지도(표준 랜드마크·길·하역장·항구) 사람 키(발~머리)
K_AMPH, K_PINE, K_CYP, K_OLIVE = 0.45, 3.0, 2.75, 2.2       # D8 소품 비례(사람 키 대비, 히어로 밖)
L6_BOX = (5.0, 372.0, 102.0, 434.8)                          # D4 상자 정정(포르투스)
HERO_C, HERO_R = (462.34, 173.66), 90.5                       # D3 조경 중심·D14 예약 반지름(+0.5)
EMP_OVER = 0.19            # 하역장 부두 앞면이 강 쪽으로 걸치는 폭(D14 ≤ 0.5)
STEP_Z = (3.67, 4.33)      # D7 영묘 디딤 윗면
STEP_D = 2.0               # D7 디딤 길이(평면)
BR_WALK = 3.0              # D7 다리 보행면(상판 높이)
PH = H_PERSON / 0.97       # person()의 h(머리끝 = 0.97h)

GEO = {}                   # spec에서 읽은 기하(load_geo가 채우고 전역에도 올린다)


def load_geo(S):
    """spec(current) core_map에서 coast 기하를 읽는다(하드코딩 0). 결과를 모듈 전역에도 올린다"""
    CM = S['core_map']
    PG = CM['portus_geometry']
    g = {}
    g['HEX_C'] = tuple(float(v) for v in PG['hexagon_plan_center'])
    g['HEX_R'] = float(PG['hexagon_plan_R'])
    g['HEX_W'] = float(PG.get('hexagon_water_R', 15.2))
    g['BAS_C'] = tuple(float(v) for v in PG['claudian_basin_plan_center'])
    mo = PG['moles']
    g['R_OUT'] = float(mo['r_out']); g['R_IN'] = float(mo['r_in'])
    g['ARM_A'] = tuple(sorted(float(v) for v in mo['arm_a_deg']))
    g['ARM_B'] = tuple(sorted(float(v) for v in mo['arm_b_deg']))
    g['COLON'] = tuple(float(v) for v in mo.get('colonnade_deg', [12.0, 54.0]))
    lh = PG['lighthouse']
    a = math.radians(float(lh['plan_angle_deg'])); rr = float(lh['plan_r'])
    g['LH_P'] = (g['BAS_C'][0] + rr * math.cos(a), g['BAS_C'][1] + rr * math.sin(a))
    g['LH_ISLAND_R'] = float(lh['island_r'])
    g['LH_TIERS'] = [tuple(float(v) for v in t) for t in lh['tiers']]
    g['LH_LANTERN'] = tuple(float(v) for v in lh['lantern'])
    g['LH_APEX'] = float(lh['apex_z'])
    can = {c['name']: c for c in PG['canals']}
    cr = next(c for n, c in can.items() if '강' in n); cs = next(c for n, c in can.items() if '외항' in n)
    g['CANAL_X'] = tuple(float(v) for v in cr['plan_x'])
    g['CANAL_RIVER_Y'] = tuple(sorted(float(v) for v in cr['plan_y']))
    g['CANAL_SEA_Y'] = tuple(sorted(float(v) for v in cs['plan_y']))
    g['COAST_Y'] = float(re.search(r'평면 Y = ([\d.]+)', CM['sea_coast']['coastline']['equation']).group(1))
    rv = CM['river']
    y1 = float(re.search(r'Y = ([\d.]+)', rv['plan']['arm1']).group(1))
    x2 = float(re.search(r'X = ([\d.]+)', rv['plan']['arm2']).group(1))
    ws = rv['width_screen_perp_mm']
    w1 = float(next(v for k, v in ws.items() if '↘' in k)); w2 = float(next(v for k, v in ws.items() if '↙' in k))
    g['BANK_N'] = y1 - w1 / C30 / 2.0; g['BANK_S'] = y1 + w1 / C30 / 2.0
    g['ARM2_X'] = (x2 - w2 / C30 / 2.0, x2 + w2 / C30 / 2.0)
    L8_ = next(L for L in CM['landmarks'] if L['id'] == 'L8')
    L8 = L8_['plan']
    g['MZ_SCALE'] = float(L8_.get('draw_scale') or 1.0)                 # 20:01 d5: 영묘 0.94(원통 중심 = draw_pivot 둘레)
    g['L6_BOX'] = tuple(next(L for L in CM['landmarks'] if L['id'] == 'L6')['projected_box'])
    ec = PG.get('east_canal')                                            # 20:25 d5: 육각 동쪽 변 → 강 서쪽 둑 운하
    g['EC_X'] = tuple(float(v) for v in ec['plan_x']) if ec else None
    g['EC_Y'] = tuple(float(v) for v in ec['plan_y']) if ec else None   # 20:01 d5: 포르투스 상자(땅 결 범위)
    b = L8['base']; g['MZ_X'] = tuple(b['X']); g['MZ_Y'] = tuple(b['Y']); g['MZ_H'] = float(b['h'])
    d = L8['drum']; g['MZ_C'] = tuple(d['c']); g['MZ_R'] = float(d['r']); g['MZ_DZ'] = tuple(d['z'])
    t = L8['top']; g['MZ_PAR'] = (float(t['parapet']['r']),) + tuple(float(v) for v in t['parapet']['z'])
    g['MZ_MOUND'] = (float(t['mound']['r_max']), float(t['mound']['z_top']))
    br = L8['bridge']; g['BR_X'] = tuple(br['deck_X']); g['BR_Y'] = tuple(br['deck_Y']); g['BR_H'] = float(br['h'])
    g['BR_PIERS'] = [tuple(p) for p in br['piers_Y']]; g['BR_CUT_X'] = tuple(br['cutwater_X'])
    roads = {r_['id']: r_ for r_ in CM['roads']}

    def band(rid):
        if rid not in roads or len(roads[rid].get('plan_pts', [])) != 2:      # 16:14 길 0 · d5에서 빠지면 d4 띠 자리
            return {'R4': (456.57, 468.11), 'R7': (484.98, 494.22)}[rid]
        r_ = roads[rid]; (X0, Y0), (X1, Y1) = r_['plan_pts']; hw = float(r_['w_screen_perp_mm']) / C30 / 2.0
        return (X0 - hw, X0 + hw) if abs(X0 - X1) < 1e-6 else (Y0 - hw, Y0 + hw)
    g['R4_X'] = band('R4'); g['R7_X'] = band('R7')
    props = CM['props']

    D4_PROPS = {'테베레 하역장': (107.4, 348.0, 154.2, 389.0), '석회 가마': (118.0, 296.0, 146.0, 328.0), '오스티아': (214.0, 466.0, 238.0, 482.0),
                '바지선 1': (64.0, 348.0, 100.0, 368.0), '바지선 2': (128.0, 440.0, 158.0, 462.0), '화산재 운반선': (112.0, 476.0, 152.0, 500.0)}

    def pb(key):
        p_ = next((p for p in props if p['name'].startswith(key)), None)      # d5: 지운 소품은 spec에 없다 → d4 상자(짓지 않는 오브젝트용)
        return tuple(float(v) for v in p_['box']) if p_ else D4_PROPS[key]
    g['BOX_EMP'] = pb('테베레 하역장'); g['BOX_KILN'] = pb('석회 가마'); g['BOX_OSTIA'] = pb('오스티아')
    g['BOX_BARGE1'] = pb('바지선 1'); g['BOX_BARGE2'] = pb('바지선 2'); g['BOX_ASH'] = pb('화산재 운반선')
    # 하역장: props 상자 [x0, y0, x1, y1]를 평면으로 되돌린다(앞면 = 북쪽 둑 + 걸침, 오른쪽 아래 = 강 수면의 앞면 밑)
    bx = g['BOX_EMP']; edge = g['BANK_N'] + EMP_OVER
    xa = bx[0] / C30 + edge
    xb = 2.0 * (bx[3] + RIVER_Z) - edge
    yb = xb - bx[2] / C30
    g['EMP_EDGE'] = edge; g['EMP_X'] = (xa, xb); g['EMP_YB'] = yb; g['EMP_ZMAX'] = 0.5 * (xa + yb) - bx[1]
    # 라벨·지시선 대상점(spec labels·detail)
    slots = CM['labels']['slots']

    def slot(key, field, dflt):
        s_ = next((s for s in slots if key in s['name']), None)
        return tuple(s_[field]) if s_ and s_.get(field) else dflt
    g['T_L6'] = slot('포르투스', 'target_pt', (37.6, 434.6)); g['T_L8'] = slot('하드리아누스', 'target_pt', (138.0, 423.8))
    g['T_ASH'] = slot('화산재', 'target_pt', (144.25, 494.95)); g['BOX_BARGE_LAB'] = slot('바지선', 'box', (84.0, 338.0, 120.0, 348.0))
    g['BOX_EMP_TAG'] = slot('하역장', 'box', (118.0, 340.0, 144.0, 346.0))
    c2 = next((l for l in S['detail']['leaders'] if 'C2' in l['name']), None)
    g['T_C2'] = tuple(c2['pts'][0]) if c2 else None                   # 20:25 d5: ❺ 근거 표지 삭제 → C2 앵커 0
    g['ASH_FIT'] = (g['BOX_ASH'][0] + 0.6, g['BOX_ASH'][1] + 0.6, g['T_ASH'][0] + 0.25, g['BOX_ASH'][3] - 0.6)
    GEO.clear(); GEO.update(g)
    globals().update(g)
    return g


# ───────────────────────── 재질(평면색 × ISO_TONE, 조명 없음) ─────────────────────────
def smoke_mat(name, hexcol, alpha):
    """김·연기: 평면색 × ISO_TONE을 불투명도 alpha(≤ 0.4)로 겹친다(빛 계산 없음, Transparent + Mix)"""
    m = FL.flat(name, hexcol)
    nt = m.node_tree
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    em = next(n for n in nt.nodes if n.type == 'EMISSION')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = alpha
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface'])
    for attr, val in (('blend_method', 'BLEND'), ('surface_render_method', 'BLENDED')):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
    return m


def mats():
    P = FL.PAL
    def fl(n, h):
        return FL.flat(n, h)            # 다시 지을 때 색을 새로 반영한다(같은 재질 블록을 고쳐 쓴다)
    def bl(n, *a):
        return FL.blocks(n, *a)
    water = P['water']                  # D9: 물은 PAL 'water' 한 값
    slab = P.get('slab', '#D9CDB4')     # D9: 판석은 PAL 'slab'(bglobal이 더하기 전에는 대체값)
    return {
        # 돌·콘크리트
        'quay': bl('F_coast_QuayBlocks', '#D6BE97', '#CDB28A', '#DFC9A6', '#A88C66', 2.2, 1.0, 0.09),
        'pave': bl('F_coast_Pave', '#E3D3B4', '#D8C5A2', '#EADDC2', '#B8A27E', 1.6, 1.6, 0.1),
        'slab': bl('F_coast_Slab', FL.shade(slab, 1.04), slab, FL.shade(slab, 0.95), FL.shade(slab, 0.8), 1.5, 1.5, 0.1),
        'conc': bl('F_coast_ConcLifts', '#B7AA94', '#ADA08A', '#C1B59F', '#8A7E6C', 3.4, 1.15, 0.08),
        'conc_core': bl('F_coast_ConcCore', '#A99C86', '#9D907A', '#B5A891', '#7F725F', 0.55, 0.42, 0.12),
        'conc_flat': fl('F_coast_conc', '#B3A68F'),
        'trav': bl('F_coast_TravBlocks', '#DCC39C', '#D2B68D', '#E6D1AE', '#AF9068', 1.9, 0.95, 0.08),
        'marble': bl('F_coast_Marble', '#EEE6D6', '#E6DCC8', '#F4EEE2', '#C9BCA4', 2.0, 1.0, 0.07),
        'brick': bl('F_coast_Brick', '#B86F4C', '#C47C58', '#AD6646', '#8E5236', 0.75, 0.26, 0.08),
        'plaster': fl('F_coast_plaster', '#E4CFA8'),
        'brick_flat': fl('F_coast_brick_flat', '#B5704E'),
        'roof_flat': fl('F_coast_roof_flat', '#BC6742'),
        'quay_flat': fl('F_coast_quay_flat', '#D3BA93'),
        'pave_flat': fl('F_coast_pave_flat', '#DCCAA8'),
        'trav_flat': fl('F_coast_trav_flat', '#D8BE95'),
        'marble_flat': fl('F_coast_marble_flat', '#EAE1CF'),
        'marble_lt': fl('F_coast_marble_lt', '#F3EDE1'),
        'joint': fl('F_coast_joint', '#BFAE90'),
        'plaster2': fl('F_coast_plaster2', '#DDBF94'),
        'roof': bl('F_coast_RoofTiles', '#B9643F', '#C4704A', '#AE5B38', '#8E4A2F', 0.55, 40.0, 0.18),
        'roof_ridge': fl('F_coast_roof_ridge', '#D88A5E'),
        'roof_dk': fl('F_coast_roof_dk', '#8E4A2F'),
        # 깊이색(L1)
        'deep': fl('F_coast_deep', '#5E4331'),
        'deeper': fl('F_coast_deeper', '#4A3426'),
        'arch_in': fl('F_coast_arch_in', '#8A6A4C'),
        'wet': fl('F_coast_wet', '#6F6656'),
        'core_dk': fl('F_coast_core_dk', '#6B604F'),
        # 하이라이트(L5)
        'hi': fl('F_coast_hi', '#F6EEDC'),
        'hi_warm': fl('F_coast_hi_warm', '#F2DDB8'),
        'hi_roof': fl('F_coast_hi_roof', '#E6A27A'),
        'hi_marble': fl('F_coast_hi_marble', '#FBF7EE'),
        # 물(내항·운하·폭포·물결)
        'water': fl('F_coast_water', water),
        'water_lt': fl('F_coast_water_lt', FL.shade(water, 1.38)),
        'water_dk': fl('F_coast_water_dk', FL.shade(water, 0.86)),
        'foam': fl('F_coast_foam', '#E9F3F1'),
        'fall': fl('F_coast_fall', FL.shade(water, 1.26)),
        # 얼룩·식생·생활(L6)
        'algae': fl('F_coast_algae', '#5F6B4C'),
        'stain': fl('F_coast_stain', '#A88F70'),
        'stain_m': fl('F_coast_stain_m', '#CFC2A8'),
        'moss': fl('F_coast_moss', P['moss']),
        'grass': fl('F_coast_grass', P['grass1']),
        'grass2': fl('F_coast_grass2', P['grass2']),
        'grass3': fl('F_coast_grass3', P['grass3']),
        'pine': fl('F_coast_pine', P.get('pine1', '#5E7A3E')),
        'pine2': fl('F_coast_pine2', P.get('pine2', '#6E8A48')),
        'pine_hi': fl('F_coast_pine_hi', FL.mix_hex(P.get('pine2', '#6E8A48'), P.get('leaf_lt', '#D9DD8E'), 0.35)),
        'cypress': fl('F_coast_cypress', P['cypress1']),
        'cypress2': fl('F_coast_cypress2', P['cypress2']),
        'olive': fl('F_coast_olive', P['olive1']),
        'olive2': fl('F_coast_olive2', P['olive2']),
        'bark': fl('F_coast_bark', P['bark']),
        'flower_y': fl('F_coast_flower_y', P.get('flower_y', '#E8C24A')),
        'flower_w': fl('F_coast_flower_w', P.get('flower_w', '#F1EBDD')),
        'wood': bl('F_coast_Planks', '#A97B4F', '#9E7146', '#B5885A', '#7E5A39', 3.0, 0.42, 0.08),
        'wood_flat': fl('F_coast_wood', '#A97B4F'),
        'wood_dk': fl('F_coast_wood_dk', '#6E4F33'),
        'sail': fl('F_coast_sail', '#F1E8D4'),
        'sail_st': fl('F_coast_sail_stripe', '#B8402E'),
        'cloth_r': fl('F_coast_cloth_r', P['c_red']),
        'cloth_b': fl('F_coast_cloth_b', P['c_blue']),
        'cloth_w': fl('F_coast_cloth_w', P['c_white']),
        'cloth_o': fl('F_coast_cloth_o', P['c_ochre']),
        'cloth_g': fl('F_coast_cloth_g', P['c_green']),
        'skin': fl('F_coast_skin', P['skin']),
        'skin2': fl('F_coast_skin2', P.get('skin2', '#C68A63')),
        'hair': fl('F_coast_hair', P['hair']),
        'terra': fl('F_coast_terra', P['terra']),
        'terra2': fl('F_coast_terra2', P.get('terra2', '#C27547')),
        'lime': fl('F_coast_lime', P['lime']),
        'pozz': fl('F_coast_pozz', P['pozz']),
        'aggr': fl('F_coast_aggr', P['aggr']),
        'sack': fl('F_coast_sack', '#D9C6A0'),
        'iron': fl('F_coast_iron', '#4E4A45'),
        'bronze': fl('F_coast_bronze', '#7A8E6A'),
        'gold': fl('F_coast_gold', '#D9B25A'),
        'fire': fl('F_coast_fire', '#F0A23A'),
        'fire2': fl('F_coast_fire2', '#F7D46A'),
        'smoke': smoke_mat('F_coast_smoke', '#EFE9DE', 0.4),
        'soil': fl('F_coast_soil', P['soil']),
        'soil_dk': fl('F_coast_soil_dk', P['soil_dk']),
        'eye': fl('F_coast_eye', '#2E2A26'),
    }


# ───────────────────────── 레이어 도구 ─────────────────────────
class Lay:
    """표현 레이어 하나 = 메시 하나(bmesh + 재질 키 목록)"""
    def __init__(self, recalc=False):
        self.bm = bmesh.new(); self.keys = []; self.recalc = recalc
    def mi(self, key):
        if key not in self.keys:
            self.keys.append(key)
        return self.keys.index(key)


class Obj:
    """오브젝트 하나 = 루트 Empty + 레이어 메시들({PKG}_{Obj}_L{n}_{part})"""
    def __init__(self, ctx, name, X=0.0, Y=0.0, Z=0.0, rot=0.0):
        self.ctx = ctx; self.name = '%s_%s' % (PKG, name); self.L = {}
        self.root = bpy.data.objects.new(self.name + '_root', None)
        ctx['coll'].objects.link(self.root)
        self.root.location = R.P(X, Y, Z); self.root.rotation_euler = (0, 0, math.radians(rot))
        self.root.empty_display_size = 4
    def lay(self, n, part, recalc=False):
        k = (n, part)
        if k not in self.L:
            self.L[k] = Lay(recalc)
        return self.L[k]
    def finish(self):
        M = self.ctx['M']; out = []
        for (n, part), ly in sorted(self.L.items(), key=lambda kv: (kv[0][0], kv[0][1])):
            if len(ly.bm.faces) == 0:
                ly.bm.free(); continue
            ob = R.bm_to_obj(ly.bm, '%s_L%d_%s' % (self.name, n, part), [M[k] for k in ly.keys], self.ctx['coll'], self.root, False, ly.recalc)
            out.append(ob)
        self.layers = sorted({int(m.group(1)) for m in (re.search(r'_L(\d)_', o.name) for o in out) if m})
        return out


def kill_obj(root):
    """루트 Empty와 그 아래 오브젝트·메시를 지운다(fit 2회 짓기용)"""
    obs = [root] + list(root.children_recursive)
    for o in obs:
        me = o.data if o.type == 'MESH' else None
        bpy.data.objects.remove(o, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)


def bp(X, Y, Z=0.0):
    """평면 좌표(Y 아래) → Blender 축"""
    return (X, -Y, Z)


def box(ly, key, x0, x1, y0, y1, z0, z1):
    """Blender 축 상자(지역)"""
    if x1 < x0: x0, x1 = x1, x0
    if y1 < y0: y0, y1 = y1, y0
    if z1 < z0: z0, z1 = z1, z0
    return G.box(ly.bm, x0, x1, y0, y1, z0, z1, ly.mi(key))


def pbox(ly, key, X0, X1, Y0, Y1, z0, z1):
    """평면 축 상자(X0..X1, Y0..Y1 평면)"""
    return box(ly, key, X0, X1, -Y1, -Y0, z0, z1)


def obox(ly, key, cx, cy, ux, uy, hl, hw, z0, z1, uvbox=True):
    """방향 상자: 중심(cx, cy) Blender 축, 길이 방향 단위벡터(ux, uy), 반길이 hl, 반폭 hw"""
    vx, vy = -uy, ux
    pts = [(cx - ux * hl - vx * hw, cy - uy * hl - vy * hw), (cx + ux * hl - vx * hw, cy + uy * hl - vy * hw),
           (cx + ux * hl + vx * hw, cy + uy * hl + vy * hw), (cx - ux * hl + vx * hw, cy - uy * hl + vy * hw)]
    return prism(ly, key, pts, z0, z1)


def prism(ly, key, pts, z0, z1, top=True, bottom=True):
    """다각형 기둥(Blender 축 점). 반시계로 정렬해 바깥 법선을 맞춘다"""
    a = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % len(pts)]
        a += x0 * y1 - x1 * y0
    if a < 0:
        pts = pts[::-1]
    return G.prism(ly.bm, pts, z0, z1, ly.mi(key), top, bottom)


def cyl(ly, key, cx, cy, r, z0, z1, n=16, r_top=None, top=True, bottom=True):
    return G.cyl(ly.bm, cx, cy, r, z0, z1, n, ly.mi(key), r_top=r_top, top=top, bottom=bottom)


def cone(ly, key, cx, cy, r, z0, z1, n=12):
    bm = ly.bm; mi = ly.mi(key)
    ring = [bm.verts.new((cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n), z0)) for k in range(n)]
    tip = bm.verts.new((cx, cy, z1))
    fs = [bm.faces.new([ring[k], ring[(k + 1) % n], tip]) for k in range(n)]
    fs.append(bm.faces.new(ring[::-1]))
    for f in fs: f.material_index = mi
    G.uv_box(bm, fs)
    return fs


def arc(ly, key, cxB, cyB, r0, r1, th0, th1, z0, z1, n=None):
    """평면 각 th0→th1(도, X→Y)의 고리 조각. 중심은 Blender 축. 각을 오름차순으로 맞춰 바깥 법선을 지킨다"""
    if th1 < th0:
        th0, th1 = th1, th0
    if n is None:
        n = max(2, int(abs(th1 - th0) / 3.0))
    return G.ring(ly.bm, cxB, cyB, r0, r1, z0, z1, n, ly.mi(key), a0=-th1, a1=-th0)


def plan_dir(th):
    """평면 각 th(도) → Blender 단위벡터"""
    t = math.radians(th)
    return (math.cos(t), -math.sin(t))


def arch_panel(ly, key, cx, cy, ux, uy, nx, ny, w, zb, zs, d=0.10, n=8):
    """아치 모양 판(L1 깊이색·막힌 아치): 중심 (cx, cy) Blender 축, 접선 (ux, uy), 바깥 법선 (nx, ny), 폭 w, 바닥 zb, 기둥머리 zs"""
    bm = ly.bm; mi = ly.mi(key)
    r = w / 2.0
    outline = [(-r, zb), (r, zb), (r, zs)] + [(r * math.cos(math.pi * k / n), zs + r * math.sin(math.pi * k / n)) for k in range(1, n)] + [(-r, zs)]
    if uy * nx - ux * ny < 0:          # 바깥 법선이 접선의 오른쪽이 아니면 외곽 순서를 뒤집는다(앞면 법선 = n)
        outline = [(-t, z) for t, z in outline]
    def V(t, z, o):
        return bm.verts.new((cx + ux * t + nx * o, cy + uy * t + ny * o, z))
    fr = [V(t, z, d) for t, z in outline]
    bk = [V(t, z, -0.02) for t, z in outline]
    fs = [bm.faces.new(fr), bm.faces.new(bk[::-1])]
    m = len(outline)
    for k in range(m):
        fs.append(bm.faces.new([bk[k], bk[(k + 1) % m], fr[(k + 1) % m], fr[k]]))
    for f in fs: f.material_index = mi
    G.uv_box(bm, fs)
    return fs


def rect_panel(ly, key, cx, cy, ux, uy, nx, ny, w, z0, z1, d=0.10):
    """네모 판(문·창·띠): 접선 폭 w, 높이 z0..z1, 법선 쪽 두께 d(면에서 앞면까지)"""
    hw = w / 2.0
    pts = [(cx - ux * hw - nx * 0.02, cy - uy * hw - ny * 0.02), (cx + ux * hw - nx * 0.02, cy + uy * hw - ny * 0.02),
           (cx + ux * hw + nx * d, cy + uy * hw + ny * d), (cx - ux * hw + nx * d, cy - uy * hw + ny * d)]
    return prism(ly, key, pts, z0, z1)


def flat_poly(ly, key, pts, z):
    """수평 판 한 장(윗면 법선 +Z, Blender 축 점)"""
    a = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % len(pts)]
        a += x0 * y1 - x1 * y0
    if a < 0:
        pts = pts[::-1]
    bm = ly.bm
    f = bm.faces.new([bm.verts.new((x, y, z)) for x, y in pts]); f.material_index = ly.mi(key)
    G.uv_box(bm, [f])
    return f


def vsheet(ly, key, p0, p1, z0, z1, toward):
    """수직 판 한 장(폭포·물막이). toward = 법선이 향할 Blender 방향(x, y)"""
    bm = ly.bm
    a = bm.verts.new((p0[0], p0[1], z0)); b = bm.verts.new((p1[0], p1[1], z0))
    c = bm.verts.new((p1[0], p1[1], z1)); d = bm.verts.new((p0[0], p0[1], z1))
    f = bm.faces.new([a, b, c, d]); f.normal_update()
    if f.normal.x * toward[0] + f.normal.y * toward[1] < 0:
        f.normal_flip()
    f.material_index = ly.mi(key)
    G.uv_box(bm, [f])
    return f


def seg_box(ly, key, p0, p1, r):
    """두 점 사이 네모 단면 막대(밧줄·활대·기중기 팔·노). 반폭 r(Blender 축 점)"""
    a = Vector(p0); b = Vector(p1); d = b - a
    if d.length < 1e-6:
        return
    dn = d.normalized()
    ref = Vector((0, 0, 1)) if abs(dn.z) < 0.9 else Vector((1, 0, 0))
    e1 = dn.cross(ref).normalized() * r; e2 = dn.cross(e1).normalized() * r
    if e1.cross(e2).dot(dn) < 0:
        e2 = -e2
    bm = ly.bm; mi = ly.mi(key)
    off = [e1 + e2, -e1 + e2, -e1 - e2, e1 - e2]
    lo = [bm.verts.new(a + o) for o in off]; hi = [bm.verts.new(b + o) for o in off]
    fs = [bm.faces.new(lo[::-1]), bm.faces.new(hi)]
    for k in range(4):
        fs.append(bm.faces.new([lo[k], lo[(k + 1) % 4], hi[(k + 1) % 4], hi[k]]))
    for f in fs: f.material_index = mi
    G.uv_box(bm, fs)


def hsh(*k):
    return R.hash01(*k)


class Fr:
    """지역 틀: 원점 (x, y, z) Blender 축, 방향 hd(Blender 라디안, u축), v는 u의 왼쪽, 축척 s"""
    def __init__(self, x, y, z=0.0, hd=0.0, s=1.0):
        self.o = (x, y, z); self.c = math.cos(hd); self.s_ = math.sin(hd); self.k = s
    def p(self, u, v, w=0.0):
        k = self.k
        return (self.o[0] + k * (u * self.c - v * self.s_), self.o[1] + k * (u * self.s_ + v * self.c), self.o[2] + k * w)
    def d(self, u, v):
        return (u * self.c - v * self.s_, u * self.s_ + v * self.c)


def fbox(ly, key, F, u0, u1, v0, v1, w0, w1):
    pts = [F.p(u0, v0)[:2], F.p(u1, v0)[:2], F.p(u1, v1)[:2], F.p(u0, v1)[:2]]
    z0 = F.o[2] + F.k * w0; z1 = F.o[2] + F.k * w1
    return prism(ly, key, pts, z0, z1)


def fpoly(ly, key, F, uv, w0, w1):
    pts = [F.p(u, v)[:2] for u, v in uv]
    return prism(ly, key, pts, F.o[2] + F.k * w0, F.o[2] + F.k * w1)


def fcyl(ly, key, F, u, v, r, w0, w1, n=10, r_top=None):
    x, y, _ = F.p(u, v)
    return cyl(ly, key, x, y, r * F.k, F.o[2] + F.k * w0, F.o[2] + F.k * w1, n, None if r_top is None else r_top * F.k)


def fgable(ly, key, F, u0, u1, v0, v1, w0, w1, over=0.0):
    """박공지붕: 용마루가 u 방향(틀 기준)"""
    bm = ly.bm; mi = ly.mi(key)
    vm = (v0 + v1) / 2.0
    q = [(u0 - over, v0 - over, w0), (u1 + over, v0 - over, w0), (u1 + over, vm, w1), (u0 - over, vm, w1), (u1 + over, v1 + over, w0), (u0 - over, v1 + over, w0)]
    vs = [bm.verts.new(F.p(u, v, w)) for u, v, w in q]
    fs = [bm.faces.new([vs[k] for k in t]) for t in [(0, 1, 2, 3), (3, 2, 4, 5), (0, 3, 5), (1, 4, 2), (0, 5, 4, 1)]]
    for f in fs: f.material_index = mi
    G.uv_box(bm, fs)
    return fs


def roof_tiles(ly, key, F, u0, u1, v0, v1, w0, w1, over=0.0, step=0.45, t=0.08):
    """L3 기와 줄: 박공 두 경사면 위에 얇은 띠(용마루와 직각)를 step 간격으로(지붕 면에서 t 위)"""
    vm = (v0 + v1) / 2.0
    n = max(2, int((u1 - u0 + 2 * over) / step))
    for side in (0, 1):
        va, vb = (v0 - over, vm) if side == 0 else (v1 + over, vm)
        for k in range(n + 1):
            u = u0 - over + (u1 - u0 + 2 * over) * k / n
            a = F.p(u - 0.06, va, w0 + t); b = F.p(u + 0.06, va, w0 + t)
            c = F.p(u + 0.06, vb, w1 + t); d = F.p(u - 0.06, vb, w1 + t)
            bm = ly.bm
            vs = [bm.verts.new(p) for p in (a, b, c, d)]
            f = bm.faces.new(vs); f.normal_update()
            if f.normal.z < 0: f.normal_flip()
            f.material_index = ly.mi(key)


# ───────────────────────── 생활 소품(L6): 사람 키 H_PERSON(D8) ─────────────────────────
CLOTH = ('cloth_w', 'cloth_r', 'cloth_b', 'cloth_o', 'cloth_w', 'sack', 'cloth_g')


def person(ly, x, y, z, h=PH, seed=0.0, carry=None):
    """사람 1명(머리끝 0.97h = 키): 옷·띠·피부·머리카락 평면색. 폭 = 키 × 0.32. carry='sack'|'amph'면 어깨 짐"""
    if not DECOR:      # 16:14 꾸미기 소품 0
        return
    ck = CLOTH[int(hsh(seed, 1) * len(CLOTH)) % len(CLOTH)]
    sk = 'skin' if hsh(seed, 2) < 0.6 else 'skin2'
    cyl(ly, ck, x, y, 0.155 * h, z, z + 0.62 * h, 8, r_top=0.11 * h)
    cyl(ly, 'wood_dk' if ck != 'sack' else 'cloth_r', x, y, 0.118 * h, z + 0.5 * h, z + 0.56 * h, 8)
    cyl(ly, ck, x, y, 0.12 * h, z + 0.56 * h, z + 0.72 * h, 8, r_top=0.13 * h)
    cyl(ly, sk, x, y, 0.085 * h, z + 0.72 * h, z + 0.92 * h, 8, r_top=0.075 * h)
    cyl(ly, 'hair', x, y + 0.01 * h, 0.08 * h, z + 0.88 * h, z + 0.97 * h, 8, r_top=0.045 * h)
    if carry == 'sack':
        box(ly, 'sack', x - 0.15 * h, x + 0.15 * h, y - 0.11 * h, y + 0.11 * h, z + 0.95 * h, z + 1.12 * h)
    elif carry == 'amph':
        cyl(ly, 'terra', x, y, 0.07 * h, z + 0.9 * h, z + 1.16 * h, 8, r_top=0.035 * h)


def crowd(ly, pts, z, h, seed, carry_every=0, carry='sack'):
    for i, (x, y) in enumerate(pts):
        c = carry if (carry_every and i % carry_every == 0) else None
        person(ly, x, y, z, h * (0.95 + 0.1 * hsh(seed, i)), seed + i * 1.7, c)


def amphora(ly, x, y, z, h=K_AMPH * H_PERSON, lying=False):
    if not DECOR:      # 16:14 꾸미기 소품 0
        return
    key = 'terra' if hsh(x, y) < 0.6 else 'terra2'
    if lying:
        box(ly, key, x - 0.45 * h, x + 0.45 * h, y - 0.13 * h, y + 0.13 * h, z, z + 0.26 * h)
    else:
        cyl(ly, key, x, y, 0.05 * h, z, z + 0.15 * h, 6, r_top=0.17 * h)
        cyl(ly, key, x, y, 0.17 * h, z + 0.15 * h, z + 0.62 * h, 8, r_top=0.12 * h)
        cyl(ly, key, x, y, 0.12 * h, z + 0.62 * h, z + 0.82 * h, 8, r_top=0.05 * h)
        cyl(ly, key, x, y, 0.06 * h, z + 0.82 * h, z + 1.0 * h, 6, r_top=0.07 * h)


def amph_stack(ly, x, y, z, h, nu=3, nv=2, ux=1.0, uy=0.0):
    if not DECOR:      # 16:14 꾸미기 소품 0
        return
    vx, vy = -uy, ux
    for i in range(nu):
        for j in range(nv):
            amphora(ly, x + ux * i * 0.38 * h + vx * j * 0.38 * h, y + uy * i * 0.38 * h + vy * j * 0.38 * h, z, h)


def sacks(ly, key, x, y, z, s, n=4, seed=0.0, ux=1.0, uy=0.0):
    """자루 더미(생석회 흰색·화산재 붉은 갈색)"""
    if not DECOR:      # 16:14 꾸미기 소품 0
        return
    vx, vy = -uy, ux
    for i in range(n):
        a = (i % 3) * 0.55 * s; b = (i // 3) * 0.45 * s
        cx_ = x + ux * a + vx * b; cy_ = y + uy * a + vy * b
        obox(ly, key, cx_, cy_, ux, uy, 0.26 * s, 0.2 * s, z, z + 0.3 * s * (0.85 + 0.3 * hsh(seed, i)))
    obox(ly, key, x + ux * 0.27 * s + vx * 0.2 * s, y + uy * 0.27 * s + vy * 0.2 * s, ux, uy, 0.26 * s, 0.2 * s, z + 0.3 * s, z + 0.56 * s)


def heap(ly, key, x, y, z, r, h, n=10):
    """원뿔 더미(석회·화산재·골재)"""
    cone(ly, key, x, y, r, z, z + h, n)


def blob(ly, key, x, y, z, rx, ry, rz, seed=0.0, sub=1):
    """울퉁불퉁한 잎 덩어리(아이코스피어 변위, 평면색)"""
    bm = ly.bm
    res = bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    for v in res['verts']:
        d = v.co.copy()
        j = 1.0 + 0.2 * (hsh(d.x * 13.1 + seed, d.y * 7.7, d.z * 5.3) * 2 - 1)
        v.co = Vector((x + d.x * rx * j, y + d.y * ry * j, z + d.z * rz * j))
    mi = ly.mi(key)
    for f in {f for v in res['verts'] for f in v.link_faces}:
        f.material_index = mi


def pine(ly, x, y, z, h, seed=0.0):
    """우산소나무(로마 해안): 줄기 + 갈래 가지 2 + 넓은 반구 수관(아래 짙은 잎 · 가운데 덩이 3 · 윗면 밝은 잎). 키 ≈ 0.92h"""
    if not DECOR:      # 16:14 꾸미기 소품 0
        return
    t = 0.58 * h
    cyl(ly, 'bark', x, y, 0.05 * h, z, z + t, 6, r_top=0.035 * h)
    seg_box(ly, 'bark', (x, y, z + t * 0.82), (x + 0.13 * h, y + 0.05 * h, z + t + 0.09 * h), 0.022 * h)
    seg_box(ly, 'bark', (x, y, z + t * 0.88), (x - 0.11 * h, y - 0.06 * h, z + t + 0.07 * h), 0.02 * h)
    blob(ly, 'pine', x, y, z + t + 0.1 * h, 0.44 * h, 0.44 * h, 0.13 * h, seed)
    for k in range(3):
        a = 2 * math.pi * k / 3 + seed
        blob(ly, 'pine2', x + 0.17 * h * math.cos(a), y + 0.17 * h * math.sin(a), z + t + 0.18 * h, 0.27 * h, 0.27 * h, 0.11 * h, seed + k)
    blob(ly, 'pine_hi', x - 0.06 * h, y + 0.06 * h, z + t + 0.26 * h, 0.22 * h, 0.22 * h, 0.07 * h, seed + 7)


def cypress(ly, x, y, z, h, seed=0.0):
    cyl(ly, 'bark', x, y, 0.04 * h, z, z + 0.15 * h, 6)
    blob(ly, 'cypress', x, y, z + 0.55 * h, 0.13 * h, 0.13 * h, 0.45 * h, seed)
    blob(ly, 'cypress2', x - 0.03 * h, y + 0.03 * h, z + 0.62 * h, 0.08 * h, 0.08 * h, 0.3 * h, seed + 3)


def bush(ly, x, y, z, s, seed=0.0, key='grass2'):
    if not DECOR:      # 16:14 꾸미기 소품 0
        return
    blob(ly, key, x, y, z + 0.25 * s, 0.4 * s, 0.4 * s, 0.3 * s, seed)


def grass_patch(ly, key, cx, cy, z, rx, ry, seed=0.0, n=9):
    """풀 덩이(얇은 불규칙 다각형 판, 바탕 위 DEC)"""
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        f = 0.7 + 0.5 * hsh(seed, k)
        pts.append((cx + rx * f * math.cos(a), cy + ry * f * math.sin(a)))
    prism(ly, key, pts, z, z + DEC)


def tufts(ly, x, y, z, s, seed=0.0, n=4):
    """풀 포기(세운 삼각 잎 몇 장)"""
    bm = ly.bm
    for t in range(n):
        dx = (hsh(seed, t, 1) - 0.5) * 0.6 * s; dy = (hsh(seed, t, 2) - 0.5) * 0.6 * s
        hh = (0.45 + 0.4 * hsh(seed, t, 3)) * s
        key = ('grass', 'grass2', 'grass3')[t % 3]
        vs = [bm.verts.new((x + dx - 0.16 * s, y + dy, z)), bm.verts.new((x + dx + 0.16 * s, y + dy, z)), bm.verts.new((x + dx + 0.03 * s, y + dy, z + hh))]
        f = bm.faces.new(vs); f.normal_update()
        if f.normal.y > 0: f.normal_flip()
        f.material_index = ly.mi(key)


# ───────────────────────── 배(L0 선체 · L1 짐칸 · L2 돛대·난간·노 · L3 판자 줄 · L4 돛·선실·고물 장식 · L5 뱃전 하이라이트 · L6 선원·짐·물결) ─────────────────────────
def _hull_rows(L, B, n=9, stern=0.5):
    rows = []
    for k in range(n + 1):
        t = -1.0 + 2.0 * k / n
        if t < 0:
            hb = B / 2.0 * (1.0 - (abs(t) ** 2.6) * (1.0 - stern))
        else:
            hb = B / 2.0 * max(0.0, 1.0 - t ** 1.7)
        rows.append((t * L / 2.0, hb, t))
    return rows


def _outline(rows, f=1.0, g=1.0):
    st = [(u * g, -hb * f) for u, hb, t in rows]
    po = [(u * g, hb * f) for u, hb, t in rows[::-1] if hb > 1e-4]
    return st + po


def hull(ly, key, F, L, B, H, sheer=0.3, n=9, stern=0.5, keel=-0.3):
    """선체 로프트: 바닥(좁게) → 허리 → 뱃전(이물·고물이 솟는다)"""
    rows = _hull_rows(L, B, n, stern)
    bm = ly.bm; mi = ly.mi(key)
    specs = [(keel * H, 0.5, 0.86, 0.0), (0.45 * H, 0.94, 0.98, 0.3), (H, 1.0, 1.0, 1.0)]
    rings = []
    for w, f, g, sh in specs:
        pts = _outline(rows, f, g)
        ring = []
        for (u, v) in pts:
            t = (2.0 * u / L) if L else 0.0
            ww = w + sh * sheer * H * (t * t) * (1.4 if t < 0 else 1.0)
            ring.append(bm.verts.new(F.p(u, v, ww)))
        rings.append(ring)
    fs = []
    m = len(rings[0])
    for a, b in ((0, 1), (1, 2)):
        for k in range(m):
            fs.append(bm.faces.new([rings[a][k], rings[a][(k + 1) % m], rings[b][(k + 1) % m], rings[b][k]]))
    fs.append(bm.faces.new(rings[0][::-1])); fs.append(bm.faces.new(rings[2]))
    for f_ in fs: f_.material_index = mi
    G.uv_box(bm, fs)
    return rows


def ship(O, F, L, B, H, kind='merchant', seed=0.0, cargo='amph', crew=3, wake=1.0, sail=True, mast=3.6, crew_h=None, amph_h=None, goose=True, oars=True):
    """배 한 척을 O의 레이어에 쌓는다. F: 수면(w=0) 위 틀, u = 이물 방향. crew_h = 선원 h(머리끝 0.97h, 틀 축척 전)"""
    if crew_h is None:
        crew_h = PH / F.k
    if amph_h is None:
        amph_h = K_AMPH * H_PERSON / F.k
    l0 = O.lay(0, 'Hulls', recalc=True); l1 = O.lay(1, 'Holds', recalc=True); l2 = O.lay(2, 'Rigging'); l3 = O.lay(3, 'Planks')
    l4 = O.lay(4, 'SailsCabins'); l5 = O.lay(5, 'Gunwale'); l6 = O.lay(6, 'CrewCargo')
    stern = 0.62 if kind == 'barge' else 0.42
    sheer = 0.12 if kind == 'barge' else 0.32
    rows = hull(l0, 'wood_flat', F, L, B, H, sheer, 9, stern)
    # L1 짐칸(뱃전 안 깊은 색)
    inner = [(u * 0.9, v * 0.78) for u, v in _outline(rows)]
    fpoly(l1, 'deep', F, inner, H * 0.82, H + DEC / F.k)
    # L3 판자 줄(뱃전 아래 두 줄, 선체 면에서 0.05 앞)
    for wf in (0.42, 0.72):
        for side in (-1, 1):
            pts = []
            for u, hb, t in rows:
                if hb < 0.05 * B:
                    continue
                pts.append((u, side * (hb * (0.95 if wf < 0.5 else 0.99) + DEC / F.k)))
            for k in range(len(pts) - 1):
                (ua, va), (ub, vb) = pts[k], pts[k + 1]
                fpoly(l3, 'wood_dk', F, [(ua, va), (ub, vb), (ub, vb + side * 0.035), (ua, va + side * 0.035)], H * wf, H * wf + 0.07 * H)
    # L5 뱃전 윗선
    gpts = _outline(rows, 1.0, 1.0)
    for k in range(len(gpts)):
        (ua, va), (ub, vb) = gpts[k], gpts[(k + 1) % len(gpts)]
        if abs(ua - ub) + abs(va - vb) < 1e-4:
            continue
        cu = (ua + ub) / 2
        t = 2 * cu / L
        ww = H + sheer * H * t * t * (1.4 if t < 0 else 1.0)
        fpoly(l5, 'hi_warm', F, [(ua, va), (ub, vb), (ub * 0.97, vb * 0.9), (ua * 0.97, va * 0.9)], ww - 0.02, ww + DEC + 0.03 * H)
    if kind == 'barge':
        # 선실(고물), 견인 돛대, 키잡이 노
        fbox(l4, 'wood', F, -L * 0.48, -L * 0.3, -B * 0.32, B * 0.32, H * 0.9, H * 1.9)
        fgable(l4, 'roof', F, -L * 0.49, -L * 0.29, -B * 0.36, B * 0.36, H * 1.9, H * 2.25)
        fcyl(l2, 'wood_dk', F, L * 0.18, 0, 0.06 * B, H, H + mast * B, 6)
        fbox(l2, 'wood_dk', F, -L * 0.62, -L * 0.42, -0.04 * B, 0.04 * B, H * 0.6, H * 0.9)
        fbox(l2, 'wood_dk', F, -L * 0.45, -L * 0.40, -0.03 * B, 0.03 * B, H * 0.9, H * 1.7)
    else:
        # 돛대·활대·돛(L2·L4), 앞 돛대(아르테몬), 고물 거위목 장식, 선실, 키잡이 노 2
        mh = mast * B
        fcyl(l2, 'wood_dk', F, L * 0.05, 0, 0.055 * B, H, H + mh, 6)
        fbox(l2, 'wood_dk', F, L * 0.03, L * 0.07, -B * 1.05, B * 1.05, H + mh * 0.88, H + mh * 0.93)
        if sail:
            fbox(l4, 'sail', F, L * 0.075, L * 0.105, -B * 0.98, B * 0.98, H + mh * 0.3, H + mh * 0.88)
            fbox(l4, 'sail_st', F, L * 0.105 + DEC / F.k, L * 0.11 + DEC / F.k, -B * 0.98, B * 0.98, H + mh * 0.55, H + mh * 0.62)
        else:
            fbox(l4, 'sail', F, L * 0.06, L * 0.1, -B * 0.95, B * 0.95, H + mh * 0.8, H + mh * 0.9)
        seg_box(l2, 'wood_dk', F.p(L * 0.37, 0, H), F.p(L * 0.61, 0, H + 1.3 * B), 0.04 * B * F.k)
        seg_box(l2, 'wood_dk', F.p(L * 0.05, 0, H + mh), F.p(L * 0.5, 0, H * 1.1), 0.012 * B * F.k)
        seg_box(l2, 'wood_dk', F.p(L * 0.05, 0, H + mh), F.p(-L * 0.47, 0, H * 1.3), 0.012 * B * F.k)
        if sail:
            fbox(l4, 'sail', F, L * 0.52, L * 0.55, -B * 0.4, B * 0.4, H + 0.55 * B, H + 1.15 * B)
        if goose:
            for k in range(5):
                t = k / 4.0
                u = -L * 0.5 - 0.08 * L * math.sin(t * 2.2)
                w = H * (1 + sheer * 1.4) + t * 1.1 * B
                fbox(l4, 'wood', F, u - 0.06 * B, u + 0.06 * B, -0.06 * B, 0.06 * B, w, w + 0.3 * B)
            fbox(l4, 'gold', F, -L * 0.5 - 0.16 * L, -L * 0.5 - 0.12 * L, -0.07 * B, 0.07 * B, H * (1 + sheer * 1.4) + 1.1 * B, H * (1 + sheer * 1.4) + 1.35 * B)
        else:
            # 낮은 고물 난간(화물선): 선체 끝을 넘지 않는다
            fbox(l4, 'wood', F, -L * 0.47, -L * 0.4, -B * 0.32, B * 0.32, H * (1 + sheer), H * (1 + sheer) + 0.35 * B)
            fbox(l4, 'gold', F, -L * 0.475, -L * 0.455, -B * 0.2, B * 0.2, H * (1 + sheer) + 0.35 * B, H * (1 + sheer) + 0.45 * B)
        fbox(l4, 'wood', F, -L * 0.42, -L * 0.24, -B * 0.3, B * 0.3, H * 0.95, H * 1.75)
        fbox(l4, 'roof_dk', F, -L * 0.44, -L * 0.22, -B * 0.34, B * 0.34, H * 1.75, H * 1.88)
        for side in ((-1, 1) if oars else ()):
            fbox(l2, 'wood_dk', F, -L * 0.5, -L * 0.36, side * B * 0.5 - 0.04 * B, side * B * 0.5 + 0.04 * B, -0.1 * H, H * 0.9)
        for side in (-1, 1):
            u = L * 0.36
            hb = [r for r in rows if r[0] >= u][0][1]
            fbox(l4, 'eye', F, u - 0.05 * B, u + 0.05 * B, side * (hb + DEC / F.k) - 0.02, side * (hb + DEC / F.k) + 0.02, H * 0.55, H * 0.68)
    # L6 짐·선원
    if cargo == 'amph':
        for i in range(4):
            for j in (-1, 1):
                amphora(l6, *F.p(-L * 0.12 + i * L * 0.09, j * B * 0.16)[:2], F.o[2] + F.k * H * 0.85, amph_h * F.k)
    elif cargo in ('lime', 'pozz', 'sacks'):
        key = {'lime': 'lime', 'pozz': 'pozz', 'sacks': 'sack'}[cargo]
        for i in range(4):
            for j in (-1, 1):
                x, y, _ = F.p(-L * 0.18 + i * L * 0.11, j * B * 0.17)
                ux, uy = F.d(1, 0)
                obox(l6, key, x, y, ux, uy, 0.17 * B * F.k, 0.14 * B * F.k, F.o[2] + F.k * H * 0.85, F.o[2] + F.k * (H * 0.85 + 0.22 * B))
        x, y, _ = F.p(-L * 0.02, 0)
        heap(l6, key, x, y, F.o[2] + F.k * H * 0.85, 0.3 * B * F.k, 0.42 * B * F.k, 8)
    for i in range(crew):
        u = (-L * 0.32 + L * 0.5 * hsh(seed, i, 3)) if i else -L * 0.36
        v = (hsh(seed, i, 5) - 0.5) * B * 0.5
        person(l6, *F.p(u, v)[:2], F.o[2] + F.k * H * 0.9, crew_h * F.k, seed + i)
    # 물결(뱃머리 물결·뒤 물살): 수면 위 DEC
    if wake > 0:
        w0 = 0.11 / F.k                    # 물 위 물결·잔물결(+0.05)보다 위
        for side in (-1, 1):
            fpoly(l6, 'foam', F, [(L * 0.5, 0), (L * 0.42, side * B * 0.55), (L * 0.18, side * B * 0.62), (L * 0.3, side * B * 0.5)], w0 - 0.01, w0)
            for k in range(3):
                u0 = -L * 0.55 - k * L * 0.32 * wake
                fpoly(l6, 'foam', F, [(u0, side * B * (0.3 + 0.18 * k)), (u0 - L * 0.24 * wake, side * B * (0.42 + 0.22 * k)),
                                      (u0 - L * 0.22 * wake, side * B * (0.5 + 0.22 * k)), (u0 + 0.02, side * B * (0.4 + 0.18 * k))], w0 - 0.01, w0)


# ───────────────────────── 평면 다각형 도구 ─────────────────────────
def clip_half(poly, nx, ny, c):
    """볼록 다각형을 반평면 nx·x + ny·y ≤ c 로 자른다(평면 좌표)"""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        da = nx * a[0] + ny * a[1] - c; db = nx * b[0] + ny * b[1] - c
        if da <= 0:
            out.append(a)
        if (da <= 0) != (db <= 0):
            t = da / (da - db)
            out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
    return out


def minus_strip_y(poly, y0, y1):
    """볼록 다각형에서 평면 Y 띠(y0..y1)를 뺀 조각들(0~2개)"""
    out = []
    l = clip_half(poly, 0.0, 1.0, y0)
    if len(l) >= 3: out.append(l)
    r = clip_half(poly, 0.0, -1.0, -y1)
    if len(r) >= 3: out.append(r)
    return out


def minus_strip(poly, x0, x1):
    """볼록 다각형에서 평면 X 띠(x0..x1)를 뺀 조각들(0~2개)"""
    out = []
    l = clip_half(poly, 1.0, 0.0, x0)
    if len(l) >= 3: out.append(l)
    r = clip_half(poly, -1.0, 0.0, -x1)
    if len(r) >= 3: out.append(r)
    return out


def to_b(poly):
    return [(x, -y) for x, y in poly]


def ppoly(ly, key, poly_plan, z0, z1):
    """평면 다각형 → 기둥(Blender)"""
    return prism(ly, key, to_b(poly_plan), z0, z1)


def polar(c, r, deg):
    t = math.radians(deg)
    return (c[0] + r * math.cos(t), c[1] + r * math.sin(t))


def screen_of(ob_list):
    xs, ys = [], []
    bpy.context.view_layer.update()
    for ob in ob_list:
        if ob.type != 'MESH' or ob.hide_render:
            continue
        mw = ob.matrix_world
        for v in ob.data.vertices:
            sx, sy = R.scr(mw @ v.co)
            xs.append(sx); ys.append(sy)
    return (round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2)) if xs else None


def screen_of_z(ob_list, zmin):
    """월드 Z ≥ zmin 정점만 잰 화면 상자(바다 쪽 옆면을 뺀 '윗면 기준' 상자)"""
    xs, ys = [], []
    for ob in ob_list:
        if ob.type != 'MESH' or ob.hide_render:
            continue
        mw = ob.matrix_world
        for v in ob.data.vertices:
            w = mw @ v.co
            if w.z < zmin:
                continue
            sx, sy = R.scr(w)
            xs.append(sx); ys.append(sy)
    return (round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2)) if xs else None


def face_poly(ly, key, cx, cy, tx, ty, nx, ny, outline, d=0.10):
    """면 위 다각형 판: outline = [(t, z)], 접선 (tx, ty), 바깥 법선 (nx, ny), 두께 d(앞으로)"""
    if ty * nx - tx * ny < 0:
        outline = [(-t, z) for t, z in outline]
    a = 0.0
    for i in range(len(outline)):
        t0, z0 = outline[i]; t1, z1 = outline[(i + 1) % len(outline)]
        a += t0 * z1 - t1 * z0
    if a < 0:
        outline = outline[::-1]
    bm = ly.bm; mi = ly.mi(key)
    fr = [bm.verts.new((cx + tx * t + nx * d, cy + ty * t + ny * d, z)) for t, z in outline]
    bk = [bm.verts.new((cx + tx * t - nx * 0.02, cy + ty * t - ny * 0.02, z)) for t, z in outline]
    fs = [bm.faces.new(fr), bm.faces.new(bk[::-1])]
    m = len(outline)
    for k in range(m):
        fs.append(bm.faces.new([bk[k], bk[(k + 1) % m], fr[(k + 1) % m], fr[k]]))
    for f in fs: f.material_index = mi
    G.uv_box(bm, fs)


def arch_ring(ly, key, cx, cy, tx, ty, nx, ny, r0, r1, zs, d=0.10, n=10):
    """아치 둘레 홍예석 띠(반고리)"""
    out = [(r1 * math.cos(math.pi * k / n), zs + r1 * math.sin(math.pi * k / n)) for k in range(n + 1)]
    inn = [(r0 * math.cos(math.pi * k / n), zs + r0 * math.sin(math.pi * k / n)) for k in range(n + 1)][::-1]
    face_poly(ly, key, cx, cy, tx, ty, nx, ny, out + inn, d)


def disk_panel(ly, key, cx, cy, nx, ny, zc, r, d=0.10, n=10):
    """면 위 원판(둥근 장식·배수구·고리 자리): 법선 (nx, ny), 중심 높이 zc"""
    tx, ty = -ny, nx
    face_poly(ly, key, cx, cy, tx, ty, nx, ny, [(r * math.cos(2 * math.pi * k / n), zc + r * math.sin(2 * math.pi * k / n)) for k in range(n)], d)


# ───────────────────────── 창고 한 동(L0 벽·지붕 · L1 아치 문 · L2 코니스·벽기둥 · L3 벽돌면·기와 줄 · L4 창 · L5 용마루·코니스 윗선) ─────────────────────────
def _vis(nx, ny):
    """Blender 수평 법선이 카메라 쪽(왼면 −Y, 오른면 +X)인가"""
    return nx - ny > 0.05


def whouse(O, F, u0, u1, v0, v1, z0, H, rh, seed=0.0, wall='brick_flat', bays=1.25, two=True, roof=True, tag='Store'):
    """면별 덧판 간격: 벽 0 → 벽돌면 0.05 → 아치·창·벽기둥 0.10 → 창턱 0.15 · 코니스 띠 0.08 → 코니스 윗선 0.13(D13)"""
    l0 = O.lay(0, tag + 'Mass', recalc=True); l1 = O.lay(1, tag + 'Openings', recalc=True); l2 = O.lay(2, tag + 'Cornice', recalc=True)
    l3 = O.lay(3, tag + 'BrickTiles'); l4 = O.lay(4, tag + 'Windows', recalc=True); l5 = O.lay(5, tag + 'Ridge', recalc=True)
    l6 = O.lay(6, tag + 'Stains', recalc=True)
    fbox(l0, wall, F, u0, u1, v0, v1, z0, z0 + H)
    if roof:
        fgable(l0, 'roof_flat', F, u0, u1, v0, v1, z0 + H, z0 + H + rh, 0.12)
        roof_tiles(l3, 'roof_dk', F, u0, u1, v0, v1, z0 + H, z0 + H + rh, 0.12, 0.42, 0.08)
        vm = (v0 + v1) / 2
        fbox(l5, 'hi_roof', F, u0 - 0.12, u1 + 0.12, vm - 0.07, vm + 0.07, z0 + H + rh - 0.05, z0 + H + rh + 0.09)
    fbox(l2, 'trav_flat', F, u0 - 0.08, u1 + 0.08, v0 - 0.08, v1 + 0.08, z0 + H - 0.2, z0 + H)
    fbox(l2, 'quay_flat', F, u0 - 0.06, u1 + 0.06, v0 - 0.06, v1 + 0.06, z0, z0 + 0.14)
    if two:
        fbox(l2, 'trav_flat', F, u0 - 0.1, u1 + 0.1, v0 - 0.1, v1 + 0.1, z0 + H * 0.52 - 0.08, z0 + H * 0.52 + 0.04)
    faces = [((0, -1), (u0 + u1) / 2, v0, (1, 0), u1 - u0), ((0, 1), (u0 + u1) / 2, v1, (1, 0), u1 - u0),
             ((-1, 0), u0, (v0 + v1) / 2, (0, 1), v1 - v0), ((1, 0), u1, (v0 + v1) / 2, (0, 1), v1 - v0)]
    for (nu, nv), cu, cv, (tu, tv), ln in faces:
        nx, ny = F.d(nu, nv)
        if not _vis(nx, ny):
            continue
        tx, ty = F.d(tu, tv)
        cx, cy, _ = F.p(cu, cv)
        zl = z0 + H * 0.52 - 0.08 if two else z0 + H - 0.2
        rect_panel(l3, 'brick', cx, cy, tx, ty, nx, ny, ln - 0.1, z0 + 0.14, zl, DEC)
        if two:
            rect_panel(l3, 'brick', cx, cy, tx, ty, nx, ny, ln - 0.1, z0 + H * 0.52 + 0.04, z0 + H - 0.2, DEC)
        nb = max(1, int(ln / bays))
        for b in range(nb):
            t = -ln / 2 + ln * (b + 0.5) / nb
            px, py = cx + tx * t, cy + ty * t
            zs = z0 + (min(H * 0.3, 1.5) if two else min(H * 0.45, 1.6))
            aw = min(0.62 * ln / nb, 0.9)
            arch_panel(l1, 'deep', px, py, tx, ty, nx, ny, aw, z0 + 0.14, zs, 0.10)
            if two:
                rect_panel(l4, 'deeper', px, py, tx, ty, nx, ny, 0.32, z0 + H * 0.64, z0 + H * 0.82, 0.10)
                rect_panel(l4, 'trav_flat', px, py, tx, ty, nx, ny, 0.42, z0 + H * 0.62, z0 + H * 0.64, 0.15)
            if b > 0:
                tb = -ln / 2 + ln * b / nb
                rect_panel(l2, 'plaster', cx + tx * tb, cy + ty * tb, tx, ty, nx, ny, 0.12, z0 + 0.14, z0 + H - 0.2, 0.10)
            arch_ring(l4, 'trav_flat', px, py, tx, ty, nx, ny, aw / 2 + 0.02, aw / 2 + 0.13, zs, 0.12, 5)   # 18:50 아치마다 트래버틴 홍예
            if not two and H >= 2.5:                                                                        # 1층 창고 높은 창(환기창)
                rect_panel(l4, 'deeper', px, py, tx, ty, nx, ny, 0.24, z0 + H * 0.74, z0 + H * 0.86, 0.10)
        zz = z0 + 0.45                                                                                     # 18:50 L3 벽돌 켜 선(창·띠·벽기둥이 앞에서 덮는다)
        while zz < z0 + H - 0.3:
            rect_panel(l3, 'joint', cx, cy, tx, ty, nx, ny, ln - 0.12, zz, zz + 0.03, 0.07)
            zz += 0.42
        for s_ in range(max(1, nb // 2)):                                                                  # L6 처마 밑 빗물 줄
            t = -ln / 2 + ln * (s_ + 0.2 + 0.6 * hsh(seed, s_, 3.1)) / max(1, nb // 2)
            L_ = 0.5 + 0.9 * hsh(seed, s_, 3.2)
            rect_panel(l6, 'stain', cx + tx * t, cy + ty * t, tx, ty, nx, ny, 0.1, z0 + H - 0.2 - L_, z0 + H - 0.21, 0.09)
        rect_panel(l5, 'hi', cx, cy, tx, ty, nx, ny, ln + 0.16, z0 + H - 0.06, z0 + H + 0.01, 0.13)


# ───────────────────────── 포르투스: 트라야누스 육각 내항(육지) ─────────────────────────
def hexv(r, k):
    return polar(HEX_C, r, 30.0 + 60.0 * k)


def hex_side(r0, r1, k):
    return [hexv(r0, k), hexv(r0, k + 1), hexv(r1, k + 1), hexv(r1, k)]


def river_canal_ok():
    """강 쪽 운하가 성립하는가: 육각 북쪽(270°) 꼭짓점과 강 남쪽 둑(BANK_S)이 25 안. 20:01 d5 새 강은 육각 동쪽을 지나 북쪽 운하 자리가 땅을 가로지른다 → 짓지 않는다"""
    return (hexv(HEX_W - 0.3, 4)[1] - BANK_S) < 25.0


def hex_ring(ly, key, r0, r1, z0, z1, gap=None, ygap=None):
    """육각 고리(꼭짓점 반지름 r0..r1). gap = 뺄 평면 X 띠(운하). 강 쪽 운하가 없으면 남쪽 꼭짓점(변 0·1)만 뺀다"""
    gks = (0, 1, 3, 4) if river_canal_ok() else (0, 1)
    for k in range(6):
        polys = [hex_side(r0, r1, k)] if (gap is None or k not in gks) else minus_strip(hex_side(r0, r1, k), gap[0], gap[1])
        if ygap is not None and k == 5:                                 # 동쪽 변(330°→30°): 동쪽 운하 Y 띠
            polys = [q for p_ in polys for q in minus_strip_y(p_, ygap[0], ygap[1])]
        for poly in polys:
            ppoly(ly, key, poly, z0, z1)


def hex_frame(k, z=0.0):
    """변 k(중심 방위 60+60k)의 틀: u = 변 방향(꼭짓점 k+1 쪽), v = 바깥(변심 거리)"""
    phi = math.radians(60.0 + 60.0 * k)
    ux, uy = -math.sin(phi), -math.cos(phi)          # Blender 축(평면 (−sinφ, cosφ))
    cx, cy = bp(*HEX_C)[:2]
    return Fr(cx, cy, z, math.atan2(uy, ux))


def harbour_water_poly(rw):
    """육각 수면 + 두 운하 수면(한 장, 겹침 0): 꼭짓점 90°·270°에 운하 혀를 붙인다(평면 좌표)"""
    x0, x1 = CANAL_X
    t30 = math.tan(math.radians(30.0))
    v = [hexv(rw, k) for k in range(6)]
    yn = v[4][1] + (CANAL_X[1] - CANAL_X[0]) / 2.0 * t30      # 강 쪽(북) 혀가 육각 변과 만나는 Y
    ys = v[1][1] - (CANAL_X[1] - CANAL_X[0]) / 2.0 * t30      # 외항 쪽(남)
    river_end = BANK_S - 0.3                                   # 강 물 면 아래로 0.3 겹친다(강 물보다 0.06 아래)
    out = [v[0], (x1, ys), (x1, COAST_Y + 0.05), (x0, COAST_Y + 0.05), (x0, ys), v[2], v[3], (x0, yn), (x0, river_end), (x1, river_end), (x1, yn), v[5]]
    if not river_canal_ok():                                   # 강 쪽 혀 0
        out = [v[0], (x1, ys), (x1, COAST_Y + 0.05), (x0, COAST_Y + 0.05), (x0, ys), v[2], v[3], v[4], v[5]]
    if EC_Y:                                                   # 20:25 동쪽 운하 혀: 동쪽 변(v5 → v0, 평면 X 일정) → 강 안 1.5
        xe = v[5][0]
        out += [(xe, EC_Y[0]), (EC_X[1] + 1.5, EC_Y[0]), (EC_X[1] + 1.5, EC_Y[1]), (xe, EC_Y[1])]
    return out


def build_hex(ctx):
    O = Obj(ctx, 'PortusHex')
    l0 = O.lay(0, 'Platform', recalc=True); l0w = O.lay(0, 'Water'); l1 = O.lay(1, 'QuayDepth', recalc=True); l2 = O.lay(2, 'CopingWall', recalc=True)
    l3 = O.lay(3, 'Paving', recalc=True); l4 = O.lay(4, 'TowersStairs', recalc=True); l5 = O.lay(5, 'EdgeLight', recalc=True); l6 = O.lay(6, 'Life')
    x0, x1 = CANAL_X
    gap = (x0 - 0.35, x1 + 0.35)                 # 운하 + 벽(0.3) + 박힘(0.05)
    rw = HEX_W - 0.3                             # 안벽 안쪽 면 = 수면 외곽
    ECG = (EC_Y[0] - 0.35, EC_Y[1] + 0.35) if EC_Y else None   # 20:25 동쪽 운하 틈(벽 0.35 포함)
    zt = PLAT_Z + DEC                            # 보행면 0.30
    # L0 포장 몸(안벽 바깥 HEX_W + 0.05 → 바깥 HEX_R) · L3 판석 무늬 판(+0.05)
    hex_ring(l0, 'pave_flat', HEX_W + 0.05, HEX_R, 0.0, PLAT_Z, gap, ECG)
    hex_ring(l3, 'pave', HEX_W + 0.05, HEX_R, PLAT_Z, zt, gap, ECG)
    # L0 안벽(돌 블록, 땅 판 절단면에 0.05 박힌다)
    hex_ring(l0, 'quay', rw, HEX_W + 0.05, RIVER_Z - 0.5, zt, gap, ECG)
    # L1 젖은 아랫단(안벽 안쪽 면 앞 0.06)
    hex_ring(l1, 'wet', rw - 0.06, rw, WATER_Z - 0.05, WATER_Z + 0.6, gap, ECG)
    # L0 수면(운하 혀 포함 한 장) — HEX_SEA면 디오라마 바다가 블록 B 홈으로 들어온다
    if not HEX_SEA:
        flat_poly(l0w, 'water', to_b(harbour_water_poly(rw)), WATER_Z)
    # L2 갓돌 띠 · L5 갓돌 앞 모서리 밝은 띠
    hex_ring(l2, 'trav_flat', rw - 0.12, HEX_W + 0.35, zt, zt + 0.14, gap, ECG)
    hex_ring(l5, 'hi', rw - 0.12, rw + 0.08, zt + 0.14, zt + 0.19, gap, ECG)
    # L2 바깥 성벽(낮은 담, 사람 키 2/3) · L5 담 윗선
    wall_gap = (gap[0] - 2.2, gap[1] + 2.2)
    hex_ring(l2, 'brick_flat', HEX_R - 0.6, HEX_R - 0.05, zt, zt + 1.6, wall_gap, ECG)
    hex_ring(l5, 'hi_warm', HEX_R - 0.6, HEX_R - 0.05, zt + 1.6, zt + 1.65, wall_gap, ECG)
    # L4 모서리 탑(꼭짓점) · 운하 문 탑 쌍 · L5 탑 윗선 · L1 탑 창
    TW = 6.3                                     # 탑 윗면(뒤 210° 꼭짓점 탑 윗끝이 L6 상자 위 변 372 ±1에 온다)
    t30 = math.tan(math.radians(30.0))
    for k in range(6):
        X, Y = hexv(HEX_R - 0.6, k)
        sg = 1.0 if k == 1 else -1.0           # 운하 꼭짓점: 남(90°)은 변이 위로, 북(270°)은 아래로 꺾인다
        spots = [(X + sx * 3.3, Y - sg * 3.3 * t30) for sx in (-1, 1)] if (k == 1 or (k == 4 and river_canal_ok())) else [(X, Y)]
        for (Xs, Ys) in spots:
            hw_ = 0.95
            pbox(l4, 'brick_flat', Xs - hw_, Xs + hw_, Ys - hw_, Ys + hw_, 0.0, zt + TW - 0.5)
            pbox(l4, 'trav_flat', Xs - hw_ - 0.12, Xs + hw_ + 0.12, Ys - hw_ - 0.12, Ys + hw_ + 0.12, zt + TW - 0.5, zt + TW - 0.25)
            for mx in (-1, 1):                     # 흉벽 이빨(앞 두 모서리)
                pbox(l4, 'brick_flat', Xs + mx * 0.7 - 0.25, Xs + mx * 0.7 + 0.25, Ys + 0.7 - 0.25, Ys + 0.7 + 0.25, zt + TW - 0.25, zt + TW)
            pbox(l5, 'hi', Xs - hw_ - 0.12, Xs + hw_ + 0.12, Ys - hw_ - 0.12, Ys + hw_ + 0.12, zt + TW - 0.25, zt + TW - 0.2)
            for face in ((0, -1), (1, 0)):
                nx, ny = face; tx, ty = (1, 0) if face == (0, -1) else (0, 1)
                fx, fy = Xs + nx * hw_, -Ys + ny * hw_
                arch_panel(l1, 'deeper', fx, fy, tx, ty, nx, ny, 0.42, zt + TW * 0.55, zt + TW * 0.68, 0.10)
                rect_panel(l4, 'trav_flat', fx, fy, tx, ty, nx, ny, 1.95, zt + TW * 0.3, zt + TW * 0.33, 0.12)
    # 창고 고리(L0~L5): 뒤쪽 세 변(2·3·4)은 2층, 앞쪽 세 변(5·0·1)은 1층(내항 수면이 보이게)
    for k in range(6):
        F = hex_frame(k, zt)
        back = k in (2, 3, 4)
        H = 4.4 if back else 2.7
        rh = 1.5 if back else 1.1
        a0, a1 = 15.35, 19.55
        segs = [(-8.2, -2.95), (-2.65, 2.65), (2.95, 8.2)]
        if k in (0, 3):
            segs[2] = (2.95, 6.2)
        if k in (1, 4):
            segs[0] = (-6.2, -2.95)
        for j, (u0, u1) in enumerate(segs):
            whouse(O, F, u0, u1, a0, a1, 0.0, H - (0.5 if j == 1 and not back else 0.0), rh, seed=k * 3 + j, two=back, tag='Horrea')
    # L4 계단(수면으로 내려가는 돌계단, 뒤쪽 변 가운데) + 계선주
    ap = rw * math.cos(math.radians(30.0))          # 안벽 안쪽 면의 변심 거리
    nst = max(5, int(math.ceil((zt - 0.18 - WATER_Z) / 0.44)))                # 수면까지 내려가는 단 수
    for k in (2, 3, 4):
        F = hex_frame(k, 0.0)
        for st in range(nst):
            if zt - 0.18 - 0.44 * st <= WATER_Z + 0.05:
                break
            fbox(l4, 'quay_flat', F, -1.0, 1.0, ap - 0.32 - st * 0.26, ap + 0.05, WATER_Z - 0.05, zt - 0.18 - 0.44 * st)
    for k in range(6):
        F = hex_frame(k, 0.0)
        for b in range(6):
            u = -6.0 + 2.4 * b
            if abs(u) < 1.4:
                continue
            fcyl(l4, 'quay_flat', F, u, ap + 0.32, 0.12, zt + 0.14, zt + 0.5, 8)
    # L6 사람(하역 일꾼, 키 2.4)·암포라·자루·풀·물결
    for k in range(6):
        F = hex_frame(k, zt)
        for i in range(3):
            u = -5.6 + 5.0 * i + 1.1 * hsh(k, i)
            x, y, z = F.p(u, ap + 1.05 + 0.25 * hsh(k, i, 2))
            person(l6, x, y, z, PH, k * 10 + i, 'sack' if i % 2 == 0 else 'amph')
        ux, uy = F.d(1, 0)
        x, y, z = F.p(4.4, ap + 1.15)
        amph_stack(l6, x, y, z, K_AMPH * H_PERSON, 3, 2, ux, uy)
        x, y, z = F.p(-3.6, ap + 1.0)
        sacks(l6, 'sack' if k % 2 else 'lime', x, y, z, 0.95, 4, k, ux, uy)
        if k not in (1, 4):
            X, Y = hexv(HEX_R - 1.7, k)
            grass_patch(l6, 'grass', X, -Y, zt, 0.8, 0.6, k)
            tufts(l6, X + 0.4, -Y - 0.2, zt, 1.1, k + 3)
    for i in range(16):
        a = 2 * math.pi * hsh(i, 5.5); r = 2.0 + (rw * 0.78 - 2.0) * hsh(i, 6.6)
        x, y = bp(*polar(HEX_C, r, math.degrees(a)))[:2]
        L_ = 0.8 + 0.7 * hsh(i, 7.7)
        flat_poly(l6, 'water_lt', [(x - L_, y - 0.06), (x + L_, y - 0.06), (x + L_ * 0.8, y + 0.06), (x - L_ * 0.8, y + 0.06)], WATER_Z + DEC)
    # L4 바깥 건물(판화처럼 육각 둘레에 붙은 신전·창고): 서쪽 땅 띠, 육각 중심 기준 상대 자리
    hx, hy = HEX_C
    # 자리: 윗끝이 L6 상자 위 변(372)보다 아래에 오도록 X + Y ≥ 744 + 2·윗면 높이(평면)
    Ft = Fr(*bp(hx - 32.5, hy + 2.5)[:2], 0.0, math.radians(90.0), 1.25)
    lt = O.lay(4, 'OuterTemple', recalc=True)
    fbox(lt, 'marble_flat', Ft, -3.0, 3.0, -2.1, 2.1, 0.0, 0.9)
    fbox(lt, 'brick_flat', Ft, -1.2, 2.6, -1.4, 1.4, 0.9, 3.2)
    for k in range(4):
        fcyl(lt, 'marble_flat', Ft, -2.4, -1.2 + 0.8 * k, 0.15, 0.9, 3.05, 8, 0.12)
    fbox(lt, 'marble_flat', Ft, -2.75, 2.75, -1.7, 1.7, 3.05, 3.35)
    fgable(lt, 'roof_flat', Ft, -2.75, 2.75, -1.7, 1.7, 3.35, 4.1, 0.05)
    roof_tiles(O.lay(3, 'OuterTempleTiles'), 'roof_dk', Ft, -2.75, 2.75, -1.7, 1.7, 3.35, 4.1, 0.05, 0.4, 0.08)
    for st in range(3):
        fbox(lt, 'quay_flat', Ft, -3.0 - 0.3 * (3 - st), -3.0, -1.3, 1.3, 0.0, 0.3 * (st + 1))
    face_poly(O.lay(1, 'OuterTempleShade'), 'deep', *Ft.p(-1.2, 0.0)[:2], *Ft.d(0, 1), *Ft.d(-1, 0), [(-1.5, 1.12), (1.5, 1.12), (1.5, 3.8), (-1.5, 3.8)], 0.10)
    for i, (dX, dY, w, d, H) in enumerate(((-37.5, 4.0, 3.4, 2.4, 2.9), (-35.0, 9.5, 3.8, 2.6, 3.1), (-29.4, 11.8, 2.8, 2.2, 2.6))):
        whouse(O, Fr(*bp(hx + dX, hy + dY)[:2], 0.0, 0.0), -w / 2, w / 2, -d / 2, d / 2, 0.0, H, 1.0, 40 + i, two=False, bays=1.1, tag='OuterStore')   # 18:50 직각 원칙: 30° 돌림 → 0°
    # 18:55 레퍼런스(포르투스 복원도): 육각 앞쪽 두 모서리 빈 땅에 2층 창고(격자와 나란히, 해안선 1.6 · 육각 바깥 변 1.2 · 운하와 떨어짐)
    for i, (dX_, dY_, w, d) in enumerate(((-16.0, 21.9, 8.0, 5.8), (15.0, 22.1, 8.0, 5.4))):     # 20:01: 육각 중심 기준(포르투스가 옮겨도 따라간다)
        whouse(O, Fr(*bp(hx + dX_, hy + dY_)[:2], 0.0, 0.0), -w / 2, w / 2, -d / 2, d / 2, 0.0, 3.2, 1.2, 60 + i, two=True, bays=1.25, tag='OuterHorrea')
    # L6 육각 내항 앞-왼쪽 우산소나무(뒤쪽 변 위로 솟지 않게 앞 부채꼴만)·덤불
    for i, (ang, dr) in enumerate(((128.0, 3.0), (152.0, 4.4))):
        X, Y = polar(HEX_C, HEX_R + dr, ang)
        if Y > COAST_Y - 2.8:
            continue
        pine(l6, X, -Y, 0.0, K_PINE * H_PERSON * (0.9 + 0.15 * hsh(i, 8)), i * 0.9)
        bush(l6, X + 1.3, -Y - 0.7, 0.0, 1.1, i)
    # L6 물때 띠: 안벽 수면선(젖은 띠 앞 0.06)
    hex_ring(l6, 'algae', rw - 0.12, rw - 0.06, WATER_Z - 0.02, WATER_Z + 0.24, gap, ECG)
    # L6 항구 둘레 땅 결(풀 덩이·흙 얼룩·풀 포기): 육각 포장 밖 ~ 해안·강둑 안, 운하·영묘 기단·바깥 건물 자리는 비운다
    hx, hy = HEX_C
    for i in range(70):
        a = 2 * math.pi * hsh(i, 3.3); r = HEX_R + 1.2 + 9.0 * hsh(i, 4.4)
        X, Y = polar(HEX_C, r, math.degrees(a))
        if Y > COAST_Y - 1.6 or Y < BANK_S + 1.2 or X > MZ_X[0] - 1.6:
            continue
        if gap[0] - 1.0 < X < gap[1] + 1.0:
            continue
        if hx - 41.0 < X < hx - 25.0 and hy - 1.0 < Y < hy + 15.0:
            continue
        sx_, sy_ = R.to_screen(X, Y)
        if not (L6_BOX[0] + 1.5 < sx_ < L6_BOX[2] - 2.5 and L6_BOX[1] + 2.5 < sy_ < L6_BOX[3] - 1.5):
            continue                         # 포르투스 실측 상자(D4) 안에서만
        if hsh(i, 5.5) < 0.45:
            grass_patch(l6, 'grass' if i % 3 else 'grass3', X, -Y, 0.0, 0.9 + 0.6 * hsh(i, 6), 0.5 + 0.3 * hsh(i, 7), i)
        elif hsh(i, 5.5) < 0.7:
            grass_patch(l6, 'soil', X, -Y, 0.0, 0.8 + 0.5 * hsh(i, 8), 0.45 + 0.25 * hsh(i, 9), i + 100)
        tufts(l6, X + 0.4, -Y - 0.3, 0.0, 1.0, i + 200)
    O.finish()
    # 땅 절단체(숨김): 육각 수면
    cl = Lay()
    prism(cl, 'soil', to_b([hexv(HEX_W, k) for k in range(6)]), RIVER_Z - 0.5, 2.0)
    cut = R.bm_to_obj(cl.bm, 'X_CUT_CoastHex', ctx['M']['soil'], ctx['coll'], O.root)
    cut.hide_render = True; cut.display_type = 'WIRE'
    return O


# ───────────────────────── 포르투스: 운하 2개(강 ↔ 육각 내항 ↔ 외항) ─────────────────────────
def canal_specs(rw):
    """운하 벽 평면 다각형(서·동): 강 쪽은 강 남쪽 둑 → 육각 수면 변, 외항 쪽은 육각 수면 변 → 해안선"""
    x0, x1 = CANAL_X
    t30 = math.tan(math.radians(30.0))
    vn = hexv(rw, 4); vs = hexv(rw, 1)
    def yN(X): return vn[1] + abs(X - vn[0]) * t30
    def yS(X): return vs[1] - abs(X - vs[0]) * t30
    xw0, xe1 = x0 - 0.35, x1 + 0.35
    walls = {
        'River': [[(xw0, BANK_S), (x0, BANK_S), (x0, yN(x0)), (xw0, yN(xw0))], [(x1, BANK_S), (xe1, BANK_S), (xe1, yN(xe1)), (x1, yN(x1))]],
        'Sea': [[(xw0, yS(xw0)), (x0, yS(x0)), (x0, COAST_Y), (xw0, COAST_Y)], [(x1, yS(x1)), (xe1, yS(xe1)), (xe1, COAST_Y), (x1, COAST_Y)]],
    }
    spans = {'River': (BANK_S, yN(x0)), 'Sea': (yS(x0), COAST_Y)}
    if not river_canal_ok():
        walls.pop('River'); spans.pop('River')
    return walls, spans


def build_canals(ctx):
    O = Obj(ctx, 'PortusCanals')
    l0 = O.lay(0, 'Walls', recalc=True); l1 = O.lay(1, 'ArchShade', recalc=True); l2 = O.lay(2, 'Coping', recalc=True)
    l3 = O.lay(3, 'Masonry', recalc=True); l4 = O.lay(4, 'Bridges', recalc=True); l5 = O.lay(5, 'Light', recalc=True); l6 = O.lay(6, 'Life')
    x0, x1 = CANAL_X
    rw = HEX_W - 0.3
    zt = PLAT_Z + DEC
    walls, spans = canal_specs(rw)
    for name in [n_ for n_ in ('River', 'Sea') if n_ in spans]:
        wa, wb = spans[name]
        for wpoly in walls[name]:
            ppoly(l0, 'quay_flat', wpoly, RIVER_Z - 0.5, zt)
        # L3 돌 쌓기 무늬(보이는 서쪽 벽 안쪽 면, 법선 +X, 0.05 앞)
        pbox(l3, 'quay', x0 - 0.01, x0 + DEC, wa + 0.05, wb - 0.05, WATER_Z - 0.02, PLAT_Z)
        # L2 갓돌(벽 위, 물 쪽으로 0.08 나온다), L5 갓돌 윗선
        pbox(l2, 'trav_flat', x0 - 0.42, x0 + 0.08, wa, wb, zt, zt + 0.14)
        pbox(l2, 'trav_flat', x1 - 0.08, x1 + 0.42, wa, wb, zt, zt + 0.14)
        pbox(l5, 'hi', x0 - 0.02, x0 + 0.08, wa, wb, zt + 0.14, zt + 0.19)
        pbox(l5, 'hi', x1 - 0.08, x1 + 0.02, wa, wb, zt + 0.14, zt + 0.19)
        yy = wa + 0.4                                                     # 18:50 갓돌 줄눈(0.8마다) · 계선주(2.4마다)
        while yy < wb - 0.2:
            pbox(l3, 'joint', x0 - 0.42, x0 + 0.08, yy, yy + 0.05, zt + 0.14, zt + 0.15)
            pbox(l3, 'joint', x1 - 0.08, x1 + 0.42, yy, yy + 0.05, zt + 0.14, zt + 0.15)
            yy += 0.8
        yy = wa + 1.2
        while yy < wb - 0.8:
            for xb in (x0 - 0.2, x1 + 0.2):
                cyl(l4, 'quay_flat', xb, -yy, 0.12, zt + 0.14, zt + 0.5, 8)
                cyl(l5, 'hi', xb, -yy, 0.13, zt + 0.5, zt + 0.53, 8)
            yy += 2.4
        # L6 물때 띠(서쪽 벽 수면선, 무늬 판 앞 0.05)
        pbox(l6, 'algae', x0 + DEC, x0 + 2 * DEC, wa + 0.05, wb - 0.05, WATER_Z - 0.03, WATER_Z + 0.22)
        # L4 아치 돌다리(실제 아치 구멍) + L1 홍예 안 그늘 + L3 홍예석 + L6 다리 위 사람
        yc = wa + 3.2 if name == 'River' else wb - 1.6
        G.wall_holes(l4.bm, 'X', x0 - 0.7, x1 + 0.7, -(yc + 0.6), -(yc - 0.6), RIVER_Z - 0.1, zt + 0.45,
                     [('arch', x0 + 0.05, x1 - 0.05, RIVER_Z - 0.1, -1.0)], l4.mi('quay'), 10)
        pbox(l4, 'trav_flat', x0 - 0.75, x1 + 0.75, yc - 0.62, yc - 0.48, zt + 0.45, zt + 1.0)
        pbox(l4, 'trav_flat', x0 - 0.75, x1 + 0.75, yc + 0.48, yc + 0.62, zt + 0.45, zt + 1.0)
        pbox(l5, 'hi', x0 - 0.75, x1 + 0.75, yc + 0.48, yc + 0.62, zt + 1.0, zt + 1.05)
        cx, cy, _ = bp((x0 + x1) / 2, yc + 0.6)
        arch_ring(l3, 'trav_flat', cx, cy, 1, 0, 0, -1, 1.45, 1.7, -1.0, 0.10)
        cx2, cy2, _ = bp((x0 + x1) / 2, yc)
        arch_panel(l1, 'deeper', cx2, cy2, 1, 0, 0, -1, (x1 - x0) - 0.12, WATER_Z + 0.01, -1.0, 0.005)
        person(l6, bp(x0 + 0.7, yc)[0], bp(x0 + 0.7, yc)[1], zt + 0.45, PH, 40 + yc)
    if EC_Y:                                                         # 20:25 d5: 동쪽 운하(육각 수면 동쪽 변 → 강 서쪽 둑), 운하 축 = 평면 X
        xe = hexv(rw, 5)[0]
        xa_, xb_ = xe, EC_X[1] + 0.6
        for (ya_, yb_) in ((EC_Y[0] - 0.35, EC_Y[0]), (EC_Y[1], EC_Y[1] + 0.35)):
            ppoly(l0, 'quay_flat', [(xa_, ya_), (xb_, ya_), (xb_, yb_), (xa_, yb_)], RIVER_Z - 0.5, zt)
        pbox(l3, 'quay', xa_ + 0.05, xb_ - 0.05, EC_Y[0] - DEC, EC_Y[0] + 0.01, WATER_Z - 0.02, PLAT_Z)        # 보이는 남쪽 벽 안쪽 면 돌 무늬(법선 +Y)
        pbox(l2, 'trav_flat', xa_, xb_, EC_Y[0] - 0.42, EC_Y[0] + 0.08, zt, zt + 0.14)
        pbox(l2, 'trav_flat', xa_, xb_, EC_Y[1] - 0.08, EC_Y[1] + 0.42, zt, zt + 0.14)
        pbox(l5, 'hi', xa_, xb_, EC_Y[1] - 0.02, EC_Y[1] + 0.08, zt + 0.14, zt + 0.19)
        pbox(l6, 'algae', xa_ + 0.05, xb_ - 0.05, EC_Y[0] + DEC, EC_Y[0] + 2 * DEC, WATER_Z - 0.03, WATER_Z + 0.22)
        xx = xa_ + 0.4
        while xx < xb_ - 0.2:
            pbox(l3, 'joint', xx, xx + 0.05, EC_Y[0] - 0.42, EC_Y[0] + 0.08, zt + 0.14, zt + 0.15)
            pbox(l3, 'joint', xx, xx + 0.05, EC_Y[1] - 0.08, EC_Y[1] + 0.42, zt + 0.14, zt + 0.15)
            xx += 0.8
        xx = xa_ + 1.2
        while xx < xb_ - 0.8:
            for yb2 in (EC_Y[0] - 0.2, EC_Y[1] + 0.2):
                cyl(l4, 'quay_flat', xx, -yb2, 0.12, zt + 0.14, zt + 0.5, 8)
            xx += 2.4
    # 외항 쪽 운하 물막이 폭포(해안 단면 앞, 바다로 떨어진다) + 물줄기 결 + 물보라 — HEX_SEA면 운하가 바다와 같은 수면이라 0
    if not HEX_SEA:
        l0f = O.lay(0, 'Cascade')
        vsheet(l0f, 'fall', bp(x0, COAST_Y + 0.05), bp(x1, COAST_Y + 0.05), SEA_Z, WATER_Z, (0, -1))
        for k in range(3):
            xa = x0 + 0.5 + k * 0.9
            vsheet(l3, 'water_lt', bp(xa, COAST_Y + 0.05 + DEC), bp(xa + 0.22, COAST_Y + 0.05 + DEC), SEA_Z + 0.4, WATER_Z - 0.4, (0, -1))
        foam = [bp((x0 + x1) / 2 + 2.3 * math.cos(math.radians(a)), COAST_Y + 0.1 + 1.5 * math.sin(math.radians(a)))[:2] for a in range(0, 181, 20)]
        flat_poly(l6, 'foam', foam, SEA_Z + 0.07)
    # 강 쪽 운하의 작은 거룻배(사람 키 2.4)
    if 'River' in spans and DECOR:
        ya, yb = spans['River']
        F = Fr(*bp((x0 + x1) / 2, (ya + yb) / 2 + 2.0)[:2], WATER_Z, math.radians(-90.0))
        ship(O, F, 4.4, 1.6, 0.55, 'barge', 7.0, 'sacks', 1, 0.6, True, 1.5)
    O.finish()
    # 절단체(숨김): 강 물길 안 → 육각 수면, 육각 수면 → 해안선 밖
    cl = Lay()
    if 'River' in spans:
        pbox(cl, 'soil', x0 - 0.35, x1 + 0.35, BANK_S - 1.5, spans['River'][1] + 0.5, RIVER_Z - 0.5, 2.0)
    if EC_Y:                                                         # 동쪽 운하 물길(육각 수면 → 강 안 1.5)
        pbox(cl, 'soil', hexv(rw, 5)[0] - 0.5, EC_X[1] + 1.5, EC_Y[0] - 0.35, EC_Y[1] + 0.35, RIVER_Z - 0.5, 2.0)
    pbox(cl, 'soil', x0 - 0.35, x1 + 0.35, spans['Sea'][0] - 0.5, COAST_Y + 1.0, RIVER_Z - 0.5, 2.0)
    cut = R.bm_to_obj(cl.bm, 'X_CUT_CoastCanals', ctx['M']['soil'], ctx['coll'], O.root)
    cut.hide_render = True; cut.display_type = 'WIRE'
    return O


# ───────────────────────── 포르투스: 클라우디우스 외항(바다) — 방파제 두 팔 ─────────────────────────
MOLE_TOP = 0.0


def _arm_vis_outer(th):
    t = math.radians(th)
    return math.cos(t) + math.sin(t) > 0.05      # 바깥 면이 카메라 쪽


def _arm_vis_inner(th):
    t = math.radians(th)
    return -(math.cos(t) + math.sin(t)) > 0.05


def _spans(a0, a1, test, step=1.0):
    """[a0, a1] 안에서 test가 참인 구간들"""
    out = []; cur = None
    a = a0
    while a <= a1 + 1e-6:
        ok = test(a)
        if ok and cur is None: cur = [a, a]
        if ok: cur[1] = a
        if not ok and cur is not None: out.append(tuple(cur)); cur = None
        a += step
    if cur is not None: out.append(tuple(cur))
    return [s for s in out if s[1] - s[0] > 0.5]


def build_claudius(ctx):
    O = Obj(ctx, 'PortusClaudius')
    l0 = O.lay(0, 'Moles', recalc=True); l1 = O.lay(1, 'Vaults', recalc=True); l2 = O.lay(2, 'Coping', recalc=True); l3 = O.lay(3, 'ConcLifts', recalc=True)
    l4 = O.lay(4, 'RiprapStairs', recalc=True); l5 = O.lay(5, 'EdgeLight', recalc=True); l6 = O.lay(6, 'Life')
    cx, cy = BAS_C[0], -BAS_C[1]
    BOT = SEA_Z - 0.06                                   # 수면 바로 아래(물 경계 틈 0, 단독 실루엣 = 합성 실루엣)
    LAND = SEA_Z + 1.1                                   # 안쪽 배 대는 단(수면 위 1.1)
    ZC = MOLE_TOP + 0.12                                 # 갓돌 윗면
    for a0, a1 in (ARM_A, ARM_B):
        # 안쪽 배 대는 단은 입구 쪽 끝(팔 A 123°·팔 B 57°)에서 9°, 운하 쪽 끝에서 3° 앞에서 멈춘다(등대 탑–팔 끝 물 ≥ 4mm)
        e0 = 9.0 if a0 == ARM_A[0] else 3.0
        e1 = 9.0 if a1 == ARM_B[1] else 3.0
        # L0 방파제 몸(바다 밑 → 윗면 Z 0), 안쪽 배 대는 단
        arc(l0, 'conc_flat', cx, cy, R_IN, R_OUT, a0, a1, BOT, MOLE_TOP)
        arc(l0, 'conc_flat', cx, cy, R_IN - 0.75, R_IN, a0 + e0, a1 - e1, BOT, LAND)
        # L2 갓돌(윗면 전체 테)
        arc(l2, 'trav_flat', cx, cy, R_IN - 0.06, R_OUT + 0.14, a0, a1, MOLE_TOP - 0.42, ZC)
        arc(l2, 'trav_flat', cx, cy, R_IN - 0.87, R_IN - 0.7, a0 + e0, a1 - e1, LAND - 0.25, LAND + 0.08)
        # L3 윗면 판석(갓돌 위 0.05), 콘크리트 층 줄(보이는 바깥 면 덧판 0.05)
        arc(l3, 'pave', cx, cy, R_IN + 0.12, R_OUT - 0.12, a0, a1, ZC, ZC + DEC)
        for s0, s1 in _spans(a0, a1, _arm_vis_outer):
            arc(l3, 'conc', cx, cy, R_OUT - 0.02, R_OUT + DEC, s0, s1, SEA_Z - 0.02, MOLE_TOP - 0.42)
            arc(l2, 'trav_flat', cx, cy, R_OUT - 0.02, R_OUT + 0.15, s0, s1, -4.4, -4.12)
            arc(l5, 'hi', cx, cy, R_OUT + 0.05, R_OUT + 0.2, s0, s1, -4.12, -4.07)
            # L1 바깥 면 막힌 아치(약 4.5°마다), L6 아치 밑 물자국
            n = int((s1 - s0) / 4.5)
            for i in range(n):
                th = s0 + (s1 - s0) * (i + 0.5) / n
                ux, uy = plan_dir(th + 90.0); nx, ny = plan_dir(th)
                px, py = cx + nx * R_OUT, cy + ny * R_OUT
                arch_panel(l1, 'arch_in', px, py, ux, uy, nx, ny, 1.25, -8.05, -5.5, 0.10)
                arch_panel(l1, 'deep', px, py, ux, uy, nx, ny, 0.95, -8.05, -5.5, 0.15)
                rect_panel(l6, 'wet', px + ux * 0.35, py + uy * 0.35, ux, uy, nx, ny, 0.12, -9.5, -8.1, 0.15)
                rect_panel(l6, 'stain', px - ux * 0.66, py - uy * 0.66, ux, uy, nx, ny, 0.1, -3.9, -1.2, 0.12)
            # L4 바깥 발치 사석(불규칙 블록)
            m = int((s1 - s0) / 1.4)
            for i in range(m):
                th = s0 + (s1 - s0) * (i + hsh(i, a0)) / m
                ux, uy = plan_dir(th + 90.0); nx, ny = plan_dir(th)
                rr = R_OUT + 0.24 + 0.14 * hsh(i, 2, a0)
                w = 0.5 + 0.5 * hsh(i, 3, a0); h = 0.35 + 0.5 * hsh(i, 4, a0)
                obox(l4, 'aggr' if i % 3 else 'conc_flat', cx + nx * rr, cy + ny * rr, ux, uy, w / 2, 0.22, SEA_Z - 0.06, SEA_Z + h)
            # L6 물때 띠(수면선, 층 덧판 앞 0.05)
            arc(l6, 'algae', cx, cy, R_OUT + DEC, R_OUT + 2 * DEC, s0, s1, SEA_Z - 0.02, SEA_Z + 0.55)
        for s0, s1 in _spans(a0 + e0, a1 - e1, _arm_vis_inner):
            arc(l3, 'conc', cx, cy, R_IN - DEC, R_IN + 0.02, s0, s1, LAND + 0.08, MOLE_TOP - 0.42)
            arc(l2, 'trav_flat', cx, cy, R_IN - 0.15, R_IN + 0.02, s0, s1, -3.9, -3.62)
            arc(l5, 'hi', cx, cy, R_IN - 0.2, R_IN - 0.08, s0, s1, -3.62, -3.57)
            arc(l5, 'hi', cx, cy, R_IN - 0.87, R_IN - 0.7, s0, s1, LAND + 0.08, LAND + 0.13)
            # L1 안쪽 면 창고 볼트 입구(배 대는 단 위), L4 위층 창
            n = int((s1 - s0) / 4.0)
            for i in range(n):
                th = s0 + (s1 - s0) * (i + 0.5) / n
                ux, uy = plan_dir(th + 90.0); nx, ny = plan_dir(th + 180.0)
                px, py = cx - nx * R_IN, cy - ny * R_IN
                arch_panel(l1, 'arch_in', px, py, ux, uy, nx, ny, 1.15, LAND + 0.08, -6.2, 0.10)
                arch_panel(l1, 'deeper', px, py, ux, uy, nx, ny, 0.9, LAND + 0.08, -6.2, 0.15)
                rect_panel(l4, 'deep', px, py, ux, uy, nx, ny, 0.32, -2.8, -1.9, 0.10)
                rect_panel(l4, 'trav_flat', px, py, ux, uy, nx, ny, 0.44, -2.9, -2.8, 0.15)
                if i % 3 == 1:
                    rect_panel(l6, 'wet', px + ux * 0.7, py + uy * 0.7, ux, uy, nx, ny, 0.1, LAND + 0.1, -3.9, 0.10)
            # L4 배 대는 단으로 내려가는 계단(안쪽 면에 붙는다)
            for th in [t for t in range(int(s0) + 10, int(s1) - 6, 38)]:
                ux, uy = plan_dir(th + 90.0); nx, ny = plan_dir(th + 180.0)
                for st in range(9):
                    rr = R_IN - 0.05
                    px, py = cx - nx * rr, cy - ny * rr
                    zt_ = MOLE_TOP - 0.42 - st * 0.82
                    obox(l4, 'quay_flat', px + ux * (st * 0.4), py + uy * (st * 0.4), ux, uy, 0.21, 0.24, LAND, zt_)
            for th in range(int(s0) + 3, int(s1), 9):
                nx, ny = plan_dir(th)
                rr = R_IN - 0.62
                cyl(l4, 'quay_flat', cx + nx * rr, cy + ny * rr, 0.09, LAND + 0.08, LAND + 0.38, 8)
            arc(l6, 'algae', cx, cy, R_IN - 0.87 - DEC, R_IN - 0.87, s0, s1, SEA_Z - 0.02, SEA_Z + 0.45)
        # L5 윗면 바깥·안쪽 모서리 밝은 띠(판석과 겹치지 않는 가장자리)
        arc(l5, 'hi', cx, cy, R_OUT - 0.12, R_OUT + 0.14, a0, a1, ZC, ZC + DEC)
        arc(l5, 'hi', cx, cy, R_IN - 0.06, R_IN + 0.12, a0, a1, ZC, ZC + DEC)
        # L2 끝 마구리(팔 끝 면의 갓돌 머리)
        for th, sg in ((a0, 1.0), (a1, -1.0)):          # 끝 머리는 팔 안쪽으로 들인다(입구 폭 spec 유지)
            nx, ny = plan_dir(th); tx_, ty_ = plan_dir(th + 90.0)
            pm = cx + nx * (R_IN + R_OUT) / 2 + sg * tx_ * 0.13, cy + ny * (R_IN + R_OUT) / 2 + sg * ty_ * 0.13
            obox(l2, 'trav_flat', pm[0], pm[1], nx, ny, (R_OUT - R_IN) / 2 + 0.1, 0.12, MOLE_TOP - 0.42, ZC + 0.03)
    # 해안 이음(팔 뿌리 → 해안 단면까지 채움, 윗면 Z 0)
    for a0, a1 in ((248.0, ARM_A[1]), (ARM_B[0], 292.0)):
        pts = [polar(BAS_C, R_OUT - 0.01, a0 + (a1 - a0) * k / 8) for k in range(9)]
        poly = pts + [(pts[-1][0], COAST_Y), (pts[0][0], COAST_Y)]
        ppoly(l0, 'conc_flat', poly, BOT, MOLE_TOP)
        ppoly(l3, 'pave', poly, MOLE_TOP, MOLE_TOP + DEC)
    # 팔 A 창고(150~210°): 방파제 위 작은 창고 줄(사람 키 2.4에 맞춘 높이)
    for th in range(152, 210, 7):
        nx, ny = plan_dir(th)
        F = Fr(cx + nx * 19.75, cy + ny * 19.75, ZC + DEC, math.atan2(*plan_dir(th + 90.0)[::-1]))
        whouse(O, F, -1.1, 1.1, -0.72, 0.72, 0.0, 2.8, 1.0, th, two=False, bays=0.95, tag='ArmAStore')
    # 팔 B 열주(spec colonnade_deg): 기둥 + 들보 + 지붕 + 뒷벽(바깥 면의 작은 창)
    c0, c1 = COLON
    lc = O.lay(2, 'Colonnade', recalc=True); lr = O.lay(0, 'ColonnadeRoof', recalc=True); lw = O.lay(3, 'ColonnadeTiles'); lh = O.lay(5, 'ColonnadeLight', recalc=True)
    ncol = int((c1 - c0) / 1.75) + 1
    zb = ZC + DEC
    for k in range(ncol):
        th = c0 + (c1 - c0) * k / (ncol - 1)
        nx, ny = plan_dir(th)
        cyl(lc, 'marble_flat', cx + nx * 18.85, cy + ny * 18.85, 0.15, zb, zb + 3.2, 8, r_top=0.12)
        cyl(lc, 'marble_flat', cx + nx * 18.85, cy + ny * 18.85, 0.21, zb, zb + 0.3, 8)
    arc(lc, 'marble_flat', cx, cy, 18.6, 19.12, c0 - 1.0, c1 + 1.0, zb + 3.2, zb + 3.55)
    arc(lh, 'hi', cx, cy, 18.55, 18.68, c0 - 1.0, c1 + 1.0, zb + 3.55, zb + 3.6)
    arc(lr, 'brick_flat', cx, cy, 20.35, 20.85, c0 - 1.0, c1 + 1.0, zb, zb + 3.8)
    arc(lr, 'roof_flat', cx, cy, 18.5, 20.95, c0 - 1.0, c1 + 1.0, zb + 3.55, zb + 3.8)
    arc(lw, 'roof', cx, cy, 18.55, 20.9, c0 - 1.0, c1 + 1.0, zb + 3.8, zb + 3.8 + DEC)
    arc(lh, 'hi_roof', cx, cy, 18.5, 18.62, c0 - 1.0, c1 + 1.0, zb + 3.8 + DEC, zb + 3.8 + 2 * DEC)
    for th in [c0 + 2.0 + 3.5 * k for k in range(int((c1 - c0 - 2.0) / 3.5) + 1)]:
        ux, uy = plan_dir(th + 90.0); nx, ny = plan_dir(th)
        px, py = cx + nx * 20.85, cy + ny * 20.85
        rect_panel(O.lay(4, 'ColonnadeWindows', recalc=True), 'deeper', px, py, ux, uy, nx, ny, 0.34, zb + 1.6, zb + 2.6, 0.10)
    # L6 사람(키 2.4)·짐(방파제 위)
    for i, th in enumerate(range(128, 150, 7)):
        nx, ny = plan_dir(th)
        person(l6, cx + nx * 19.7, cy + ny * 19.7, ZC + DEC, PH, 70 + i, 'sack' if i % 2 == 0 else None)
    for i, th in enumerate(range(214, 262, 9)):
        nx, ny = plan_dir(th + 2.0 * hsh(i))
        person(l6, cx + nx * 19.7, cy + ny * 19.7, ZC + DEC, PH, 80 + i, 'amph' if i % 3 == 0 else None)
    for i, th in enumerate((288, 299, 310, 343, 352)):      # C2 지시선 끝(약 324°) 둘레 ±10°는 비운다
        nx, ny = plan_dir(th)
        person(l6, cx + nx * 19.6, cy + ny * 19.6, ZC + DEC, PH, 90 + i)
    for th in (232.0, 300.0):
        nx, ny = plan_dir(th); ux, uy = plan_dir(th + 90.0)
        amph_stack(l6, cx + nx * 19.3, cy + ny * 19.3, ZC + DEC, K_AMPH * H_PERSON, 3, 2, ux, uy)
    # L6 외항 잔물결(밝은 짧은 띠)과 짙은 물 띠: 바다 수면 위 DEC
    for i in range(22):
        a = 2 * math.pi * hsh(i, 5); r = 3.0 + (R_IN - 5.0) * hsh(i, 6)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        L_ = 0.8 + 0.9 * hsh(i, 9)
        key = 'water_lt' if i % 3 else 'foam'
        flat_poly(l6, key, [(x - L_, y - 0.06), (x + L_, y - 0.06), (x + L_ * 0.8, y + 0.06), (x - L_ * 0.8, y + 0.06)], SEA_Z + DEC)
    O.finish()
    return O


# ───────────────────────── 포르투스: 등대(입구 인공섬 + 3층 팔각 탑 + 등롱) ─────────────────────────
LH_ROT = 22.5    # 18:10 메인: 팔각 탑 면을 격자와 나란히(꼭짓점 0°·45° → 22.5°·67.5°). 탑 끝–팔 끝 간격은 꼭짓점 0.82r → 면 0.758r로 넓어진다


def build_lighthouse(ctx):
    O = Obj(ctx, 'PortusLighthouse')
    l0 = O.lay(0, 'IslandTower', recalc=True); l1 = O.lay(1, 'Openings', recalc=True); l2 = O.lay(2, 'Cornices', recalc=True); l3 = O.lay(3, 'Masonry', recalc=True)
    l4 = O.lay(4, 'WindowsFire', recalc=True); l5 = O.lay(5, 'Light', recalc=True); l6 = O.lay(6, 'Life')
    X, Y = LH_P
    cx, cy = X, -Y
    BOT = SEA_Z - 0.06
    top = LH_TIERS[0][1]                      # 섬 윗면 = 1층 탑 바닥
    rI = LH_ISLAND_R
    # 팔각 탑 층(꼭짓점 반지름 0.82·r, 꼭짓점 평면 0°·45°…: 설계 탑–팔 끝 간격 정의와 같다)
    tiers = [(0.82 * r, z0, z1) for (r, z0, z1) in LH_TIERS]
    rl, zl0, zl1 = LH_LANTERN
    # L0 섬(콘크리트 원통) + 탑 3층 + 등롱 + 지붕
    cyl(l0, 'conc_flat', cx, cy, rI, BOT, top, 48)
    for rr, z0, z1 in tiers:
        cyl(l0, 'trav_flat', cx, cy, rr, z0, z1, 8)
    cyl(l0, 'marble_flat', cx, cy, rl * 0.78, zl0, zl1, 16)
    cone(l0, 'roof_flat', cx, cy, rl * 1.05, zl1 + 0.2, LH_APEX, 16)
    # L2 층마다 코니스·받침, 섬 테두리 갓돌, 등롱 기둥 8, 등롱 받침 테
    cov = [0.14, 0.22, 0.22]                  # 코니스 내밀기(1층은 팔 A 끝과 보이는 물 ≥ 4mm를 지키게 작게)
    for (rr, z0, z1), co in zip(tiers, cov):
        cyl(l2, 'marble_flat', cx, cy, rr + co, z1 - 0.35, z1, 8)
        cyl(l2, 'quay_flat', cx, cy, rr + min(co, 0.12), z0, z0 + 0.3, 8)
    G.ring(l2.bm, cx, cy, rI - 0.35, rI + 0.1, top - 0.3, top + 0.1, 48, l2.mi('trav_flat'))
    cyl(l2, 'marble_flat', cx, cy, rl * 1.12, zl1, zl1 + 0.2, 16)
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        cyl(l2, 'marble_flat', cx + rl * 0.95 * math.cos(a), cy + rl * 0.95 * math.sin(a), 0.11, zl0, zl1, 6)
    # L3 돌 쌓기 덧판(층마다 팔각 껍질 0.05 바깥), 섬 콘크리트 층 줄(보이는 반쪽)
    for rr, z0, z1 in tiers:
        cyl(l3, 'trav', cx, cy, rr + DEC / math.cos(math.pi / 8), z0 + 0.3, z1 - 0.35, 8, top=False, bottom=False)
    G.ring(l3.bm, cx, cy, rI - 0.02, rI + DEC, SEA_Z + 0.02, top - 0.3, 48, l3.mi('conc'), a0=-150, a1=60)
    # L1 문·창(아치형, 짙은 색): 카메라 쪽 팔각 면 4개(평면 법선 337.5°·22.5°·67.5°·112.5°), 등롱 속
    for li, (rr, z0, z1) in enumerate(tiers):
        hgt = z1 - z0
        ap_ = rr * math.cos(math.pi / 8) + DEC
        for fa in (-22.5, 22.5, 67.5, 112.5):
            nx, ny = plan_dir(fa); tx, ty = -ny, nx
            fx, fy = cx + nx * ap_, cy + ny * ap_
            arch_panel(l1, 'deeper', fx, fy, tx, ty, nx, ny, 0.5, z0 + hgt * 0.42, z0 + hgt * 0.62, 0.10)
            rect_panel(l4, 'marble_flat', fx, fy, tx, ty, nx, ny, 0.72, z0 + hgt * 0.40, z0 + hgt * 0.42, 0.15)
            if li == 0 and fa == 67.5:
                arch_panel(l1, 'deeper', fx, fy, tx, ty, nx, ny, 0.85, z0 + 0.3, z0 + 1.6, 0.10)
    cyl(l1, 'deeper', cx, cy, rl * 0.78 + DEC, zl0 + 0.3, zl1 - 0.35, 16)
    # L4 등롱 불, 탑 입구 계단, 섬 계단
    blob(l4, 'fire', cx + 0.1, cy - 0.25, zl0 + 1.65, 0.8, 0.8, 0.95, 3.0)
    blob(l4, 'fire2', cx + 0.3, cy - 0.5, zl0 + 1.75, 0.5, 0.5, 0.65, 4.0)
    nx, ny = plan_dir(67.5)
    ap0 = tiers[0][0] * math.cos(math.pi / 8)
    for st in range(3):
        obox(l4, 'quay_flat', cx + nx * (ap0 + 0.2 + 0.25 * st), cy + ny * (ap0 + 0.2 + 0.25 * st), -ny, nx, 0.55, 0.14, top, top + 0.28 - 0.09 * st)
    for st in range(8):
        a = math.radians(-100 + st * 7)
        obox(l4, 'quay_flat', cx + (rI + 0.18) * math.cos(a), cy + (rI + 0.18) * math.sin(a), -math.sin(a), math.cos(a), 0.3, 0.2, SEA_Z + 0.2, top - 0.15 - st * 1.2)
    # L5 코니스 윗선·앞 모서리 밝은 띠(평면 45° 꼭짓점 세로 띠)
    for (rr, z0, z1), co in zip(tiers, cov):
        cyl(l5, 'hi', cx, cy, rr + co + DEC / math.cos(math.pi / 8), z1 - 0.05, z1 + 0.02, 8)
        nx, ny = plan_dir(45.0)
        rect_panel(l5, 'hi_warm', cx + nx * (rr + DEC), cy + ny * (rr + DEC), -ny, nx, nx, ny, 0.12, z0 + 0.3, z1 - 0.35, 0.10)
    G.ring(l5.bm, cx, cy, rI + 0.06, rI + 0.16, top + 0.1, top + 0.15, 48, l5.mi('hi'))
    # L6 물때·빗물 자국·사람·물보라
    G.ring(l6.bm, cx, cy, rI + DEC + 0.03, rI + 2 * DEC + 0.03, SEA_Z - 0.02, SEA_Z + 0.5, 48, l6.mi('algae'), a0=-150, a1=60)
    for rr, z0, z1 in tiers:
        for fa in (-22.5, 22.5, 67.5):
            nx, ny = plan_dir(fa); tx, ty = -ny, nx
            ap_ = rr * math.cos(math.pi / 8) + DEC
            rect_panel(l6, 'stain', cx + nx * ap_ + tx * 0.35, cy + ny * ap_ + ty * 0.35, tx, ty, nx, ny, 0.1, z1 - 1.6, z1 - 0.36, 0.15)
    for i, ang in enumerate((25.0, 52.0, 100.0)):          # 팔 A 끝 쪽(약 130°)은 비워 보이는 물 ≥ 4mm
        nx, ny = plan_dir(ang)
        rr = (tiers[0][0] + rI) / 2
        person(l6, cx + nx * rr, cy + ny * rr, top + 0.1, PH, 120 + i)
    G.ring(l6.bm, cx, cy, rI + 0.1, rI + 0.5, SEA_Z + 0.01, SEA_Z + 0.07, 48, l6.mi('foam'))
    if LH_ROT:                                # 18:10 직각 구조: 팔각 면이 X·Y축과 나란하게 섬 중심 둘레로 돌린다(입구 면 → 카메라 정면 평면 45°)
        Mr = Matrix.Rotation(math.radians(LH_ROT), 4, 'Z')
        for ly in O.L.values():
            bmesh.ops.rotate(ly.bm, verts=ly.bm.verts, cent=(cx, cy, 0.0), matrix=Mr)
    O.finish()
    return O


# ───────────────────────── 포르투스 두 항구 수면의 범선들(중심 기준 상대 자리) ─────────────────────────
HEX_SHIPS = [((-8.4, -4.0), 25.0, 1.0), ((0.0, -9.6), 175.0, 2.0), ((8.4, -4.8), 300.0, 3.0), ((-2.5, 5.0), 80.0, 4.0)]
BAS_SHIPS = [((-9.5, -7.6), 35.0, 5.0, True), ((2.0, -10.6), 165.0, 6.0, False), ((-12.0, 0.4), 70.0, 7.0, True), ((-3.8, -1.8), 200.0, 8.0, False)]


SHIPS = True     # 00:41 사용자 '꾸미기 요소로 항구 주위와 강 위에 로마시대때의 배' · 00:44 메인: 실제 비율, 평면 X/Y 축 정렬, 사람 0
SHIP_M = 79.6 / 188.0    # 평면 단위 / m(콜로세움 장축 188 m = 평면 79.6). 상선(코르비타) 25 m · 바지선(나비스 카우디카리아) 15 m
SHIP_FLEET = [           # (이름, 평면 X, 평면 Y, 방위°(0 = +X, 90 = +Y), 'mer'|'bar', 돛, 짐, 씨앗) — 물은 디오라마 바다(DI.WATER_Z)
    ('hex1', 463.4, 346.0, 90.0, 'mer', False, 'amph', 11.0), ('hex2', 469.2, 348.0, 270.0, 'mer', True, 'amph', 12.0), ('hex3', 475.0, 345.0, 90.0, 'mer', False, 'sacks', 13.0),
    ('bas1', 462.0, 398.0, 0.0, 'mer', False, 'pozz', 14.0), ('bas2', 478.5, 397.0, 90.0, 'mer', True, 'amph', 15.0),
    ('sea1', 425.0, 396.0, 0.0, 'mer', True, 'amph', 16.0), ('sea2', 522.0, 393.0, 180.0, 'mer', True, 'sacks', 17.0),
    ('tiberA', 582.5, 250.0, 90.0, 'bar', False, 'pozz', 18.0), ('tiberC', 582.0, 140.0, 270.0, 'bar', False, 'lime', 19.0),
    ('armB2', 520.0, 287.1, 180.0, 'bar', False, 'sacks', 20.0), ('canalAB', 420.0, 211.5, 0.0, 'bar', False, 'pozz', 21.0),
]


def ship_dims(kd):
    if kd == 'mer':
        L = 25.0 * SHIP_M
        return dict(L=L, B=L / 3.3, H=2.5 * SHIP_M, mast=1.6, kind='merchant')
    L = 15.0 * SHIP_M
    return dict(L=L, B=L / 3.4, H=1.2 * SHIP_M, mast=1.1, kind='barge')


def build_roman_ships(ctx):
    """로마 배(꾸미기): 상선은 돛대·줄무늬 돛·앞 돛대·거위목 고물·선실·키잡이 노, 바지선은 견인 돛대·선실·짐(포촐라나·석회·자루). 사람·암포라 0(DECOR)"""
    import roma_diorama as DI
    O = Obj(ctx, 'RomanShips')
    for nm, X, Y, hd, kd, sail, cargo, sd in SHIP_FLEET:
        d = ship_dims(kd)
        F = Fr(X, -Y, DI.WATER_Z, math.radians(-hd))
        moving = sail or kd == 'bar'
        ship(O, F, d['L'], d['B'], d['H'], d['kind'], sd, cargo, 0, 0.6 if moving else 0.0, sail, d['mast'], goose=(kd == 'mer'), oars=True)
    O.finish()
    return O


def build_harbour_ships(ctx):
    O = Obj(ctx, 'PortusShips')
    for (dX, dY), hd, sd in HEX_SHIPS:
        F = Fr(HEX_C[0] + dX, -(HEX_C[1] + dY), WATER_Z, math.radians(-hd))
        ship(O, F, 5.8, 1.7, 0.55, 'merchant', sd, 'amph', 2, 0.6, True, 3.0)
    for (dX, dY), hd, sd, sl in BAS_SHIPS:
        F = Fr(BAS_C[0] + dX, -(BAS_C[1] + dY), SEA_Z, math.radians(-hd))
        ship(O, F, 6.8, 2.0, 0.65, 'merchant', sd, 'amph' if sd % 2 else 'sacks', 3, 0.8, sl, 3.2)
    O.finish()
    return O


# ───────────────────────── 하드리아누스 영묘(테베레 남쪽 둑, spec L8 plan) ─────────────────────────
def podium_polys():
    """기단 3켜(평면): 0~디딤1 · 디딤1~디딤2 · 디딤2~윗면. 북쪽 변 안쪽에 상판 폭 디딤 홈(D7)"""
    X0, X1 = MZ_X; Y0, Y1 = MZ_Y
    s0, s1 = BR_X
    sq = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]
    def notch(d):
        return [(X0, Y0), (s0, Y0), (s0, Y0 + d), (s1, Y0 + d), (s1, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]
    return [(sq, 0.0, STEP_Z[0]), (notch(STEP_D), STEP_Z[0], STEP_Z[1]), (notch(2 * STEP_D), STEP_Z[1], MZ_H - DEC)]


def build_mausoleum(ctx):
    O = Obj(ctx, 'HadrianMausoleum')
    l0 = O.lay(0, 'PodiumDrum', recalc=True); l0m = O.lay(0, 'Mound', recalc=True); l1 = O.lay(1, 'NichesDoors', recalc=True)
    l2 = O.lay(2, 'CornicePilasters', recalc=True); l3 = O.lay(3, 'MarbleFacing', recalc=True); l3p = O.lay(3, 'TerraceSlabs', recalc=True)
    l4 = O.lay(4, 'TituliFriezeCore', recalc=True); l5 = O.lay(5, 'Light', recalc=True); l6 = O.lay(6, 'Life')
    X0, X1 = MZ_X; Y0, Y1 = MZ_Y; Hp = MZ_H
    Xc, Yc = MZ_C; cx, cy = Xc, -Yc
    Rd = MZ_R; zd0, zd1 = MZ_DZ
    rp, zp0, zp1 = MZ_PAR
    rm, zm = MZ_MOUND
    s0, s1 = BR_X
    # L0 기단(겉은 대리석, 디딤 홈 포함 3켜) · 원통 · 정상 테두리 난간 · 흙 둔덕
    for i_, (poly, za, zb) in enumerate(podium_polys()):
        ppoly(l0, 'joint' if i_ == 2 else 'marble_flat', poly, za, zb)     # 윗켜 몸 = 판석 줄눈색(옆면은 덧판·코니스가 덮는다)
    cyl(l0, 'marble_flat', cx, cy, Rd, zd0 - DEC, zd1, 96)
    G.ring(l0.bm, cx, cy, rp - 0.9, rp, zp0, zp1, 96, l0.mi('marble_flat'))
    cyl(l0, 'pave_flat', cx, cy, rp - 0.9, zd1, zd1 + DEC, 96)
    # 둔덕: 구면 모자(r_max → 꼭대기 z_top), 풀
    bm = l0m.bm; mi = l0m.mi('grass2')
    rings = 6; nn = 48
    rows = []
    zmb = zd1 + DEC
    for j in range(rings + 1):
        t = j / rings
        rr = rm * math.cos(t * math.pi / 2)
        zz = zmb + (zm - zmb) * math.sin(t * math.pi / 2)
        rows.append([bm.verts.new((cx + rr * math.cos(2 * math.pi * k / nn), cy + rr * math.sin(2 * math.pi * k / nn), zz)) for k in range(nn)] if j < rings else [bm.verts.new((cx, cy, zm))])
    fs = []
    for j in range(rings - 1):
        for k in range(nn):
            fs.append(bm.faces.new([rows[j][k], rows[j][(k + 1) % nn], rows[j + 1][(k + 1) % nn], rows[j + 1][k]]))
    for k in range(nn):
        fs.append(bm.faces.new([rows[rings - 1][k], rows[rings - 1][(k + 1) % nn], rows[rings][0]]))
    fs.append(bm.faces.new(rows[0][::-1]))
    for f in fs: f.material_index = mi
    G.uv_box(bm, fs)
    # 보이는 기단 면 2개: 남쪽(평면 +Y, Blender 법선 −Y)·동쪽(평면 +X, 법선 +X)
    faces = [((0, -1), ((X0 + X1) / 2, -Y1), (1, 0), X1 - X0), ((1, 0), (X1, -(Y0 + Y1) / 2), (0, 1), Y1 - Y0)]
    for (nx, ny), (fx, fy), (tx, ty), ln in faces:
        # L3 대리석 덧판(받침 띠 위 ~ 코니스 아래, 0.05 앞)
        rect_panel(l3, 'marble', fx, fy, tx, ty, nx, ny, ln - 0.1, 0.55, Hp - 0.5, DEC)
        # L2 벽기둥(9개, 0.12 나옴) · L5 벽기둥 왼쪽 밝은 띠
        npil = 9
        for i in range(npil):
            t = -ln / 2 + 1.6 + (ln - 3.2) * i / (npil - 1)
            rect_panel(l2, 'trav_flat', fx + tx * t, fy + ty * t, tx, ty, nx, ny, 0.55, 0.55, Hp - 0.5, 0.15)
            rect_panel(l5, 'hi_marble', fx + tx * (t - 0.2), fy + ty * (t - 0.2), tx, ty, nx, ny, 0.1, 0.55, Hp - 0.5, 0.20)
            if i < npil - 1:
                tm = -ln / 2 + 1.6 + (ln - 3.2) * (i + 0.5) / (npil - 1)
                if i in (3, 4):
                    # L4 비문판(가운데 두 칸: 묻힌 황제 이름판 자리) + 글줄
                    rect_panel(l4, 'marble_lt', fx + tx * tm, fy + ty * tm, tx, ty, nx, ny, 3.2, 1.5, 3.9, 0.12)
                    for j in range(4):
                        rect_panel(l4, 'deep', fx + tx * tm, fy + ty * tm, tx, ty, nx, ny, 2.5 - 0.35 * j, 3.45 - 0.55 * j, 3.57 - 0.55 * j, 0.17)
                else:
                    # L1 막힌 벽감(짙은 색) + L4 벽감 아래 받침돌
                    arch_panel(l1, 'deep', fx + tx * tm, fy + ty * tm, tx, ty, nx, ny, 1.1, 1.3, 3.3, 0.10)
                    rect_panel(l4, 'trav_flat', fx + tx * tm, fy + ty * tm, tx, ty, nx, ny, 1.5, 1.18, 1.3, 0.15)
        # L6 빗물 자국(코니스 밑), 이끼(발치): 모든 덧판 앞(0.25)
        for i in range(12):
            t = -ln / 2 + 1.0 + (ln - 2.0) * hsh(i, nx, 3.3)
            hgt = 0.9 + 1.4 * hsh(i, ny, 4.4)
            rect_panel(l6, 'stain', fx + tx * t, fy + ty * t, tx, ty, nx, ny, 0.12, Hp - 0.5 - hgt, Hp - 0.52, 0.25)
        for i in range(10):
            t = -ln / 2 + 0.8 + (ln - 1.6) * hsh(i, nx, 5.5)
            rect_panel(l6, 'moss', fx + tx * t, fy + ty * t, tx, ty, nx, ny, 0.6 + 0.8 * hsh(i, 6.6), 0.55, 0.85 + 0.3 * hsh(i, 7.7), 0.25)
    # L4 기단 면의 콘크리트 속 드러난 자리(대리석 판이 떨어진 곳: 겉 대리석·속 콘크리트) — 벽기둥·벽감 사이 빈 칸
    fx, fy = X1, -(Y0 + Y1) / 2
    for (t, z0, w, h) in ((-11.46, 1.6, 1.3, 2.0), (6.24, 1.4, 1.2, 1.6)):
        face_poly(l4, 'conc_core', fx, fy, 0, 1, 1, 0, [(t - w / 2, z0), (t + w / 2, z0 + 0.2), (t + w / 2 - 0.2, z0 + h), (t - w / 2 + 0.25, z0 + h - 0.15)], 0.15)
        face_poly(l1, 'core_dk', fx, fy, 0, 1, 1, 0, [(t - w / 2 + 0.05, z0 + h - 0.15), (t + w / 2 - 0.2, z0 + h), (t + w / 2 - 0.2, z0 + h + 0.1), (t - w / 2 + 0.05, z0 + h - 0.05)], 0.20)
    # L2 기단 코니스(사방 0.25 나온 띠 4개: 윗면이 기단 윗면과 같은 높이로 붙는다, 디딤 홈은 비운다)·받침 띠(0.18) · L5 코니스 윗선(보이는 두 면)
    cz0, cz1, co = Hp - 0.5, Hp - DEC, 0.25
    pbox(l2, 'trav_flat', X0 - co, X1 + co, Y1, Y1 + co, cz0, cz1)
    pbox(l2, 'trav_flat', X1, X1 + co, Y0 - co, Y1, cz0, cz1)
    pbox(l2, 'trav_flat', X0 - co, X0, Y0 - co, Y1, cz0, cz1)
    pbox(l2, 'trav_flat', X0, s0, Y0 - co, Y0, cz0, cz1)
    pbox(l2, 'trav_flat', s1, X1, Y0 - co, Y0, cz0, cz1)
    ppoly(l2, 'trav_flat', [(X0 - 0.18, Y0 - 0.18), (X1 + 0.18, Y0 - 0.18), (X1 + 0.18, Y1 + 0.18), (X0 - 0.18, Y1 + 0.18)], 0.0, 0.55)
    pbox(l5, 'hi_marble', X0 - 0.25, X1 + 0.25, Y1 + 0.25 - 0.1, Y1 + 0.25 + DEC, Hp - DEC - 0.07, Hp - DEC + 0.02)
    pbox(l5, 'hi_marble', X1 + 0.25 - 0.1, X1 + 0.25 + DEC, Y0 - 0.25, Y1 + 0.25, Hp - DEC - 0.07, Hp - DEC + 0.02)
    pbox(l5, 'hi', X0 - 0.18, X1 + 0.18, Y1 + 0.18 - 0.08, Y1 + 0.18 + DEC, 0.5, 0.57)
    # L3 기단 윗면 판석(따로 놓은 판, 줄눈 = 아래 대리석 면): 원통·디딤 홈을 피한다
    step = 1.5; gapj = 0.14
    nxs = int((X1 - X0) / step); nys = int((Y1 - Y0) / step)
    for i in range(nxs):
        for j in range(nys):
            ax, ay = X0 + 0.1 + i * step, Y0 + 0.1 + j * step
            bx_, by_ = ax + step - gapj, ay + step - gapj
            if bx_ > X1 - 0.1 or by_ > Y1 - 0.1:
                continue
            if ax < s1 + 0.1 and bx_ > s0 - 0.1 and ay < Y0 + 2 * STEP_D + 0.1:
                continue
            if any(math.hypot(px - Xc, py - Yc) < Rd + 0.15 for px, py in ((ax, ay), (bx_, ay), (bx_, by_), (ax, by_))):
                continue
            hv = hsh(i, j, 7.7)
            pbox(l3p, 'marble_flat' if hv < 0.62 else ('marble_lt' if hv < 0.86 else 'stain_m'), ax, bx_, ay, by_, Hp - DEC, Hp)
    # 원통: L2 밑동 몰딩·윗 코니스·허리 띠·벽기둥 · L3 대리석 블록 덧판 · L1 벽감·창 · L4 띠 장식(화환 원반)·콘크리트 속 · L5·L6
    G.ring(l2.bm, cx, cy, Rd - 0.02, Rd + 0.28, zd0, zd0 + 0.7, 96, l2.mi('trav_flat'))
    G.ring(l2.bm, cx, cy, Rd - 0.02, Rd + 0.32, zd1 - 0.6, zd1, 96, l2.mi('trav_flat'))
    G.ring(l2.bm, cx, cy, Rd - 0.02, Rd + 0.22, (zd0 + zd1) / 2 - 0.15, (zd0 + zd1) / 2 + 0.1, 96, l2.mi('trav_flat'))
    G.ring(l3.bm, cx, cy, Rd - 0.02, Rd + DEC, zd0 + 0.7, zd1 - 0.6, 96, l3.mi('marble'), a0=-150, a1=60)
    G.ring(l3.bm, cx, cy, rp - 0.02, rp + DEC, zp0 + 0.1, zp1 - 0.1, 96, l3.mi('marble'), a0=-150, a1=60)
    breach = [(62.0, zd1 - 3.0, 2.2, 1.9), (18.0, zd1 - 2.4, 1.3, 1.2)]      # 평면 방위(도) · 아래 z · 폭 · 높이
    npl = 24
    for k in range(npl):
        a = math.radians(-150 + 210 * (k + 0.5) / npl)
        nx, ny = math.cos(a), math.sin(a); tx, ty = -ny, nx
        px, py = cx + nx * Rd, cy + ny * Rd
        rect_panel(l2, 'trav_flat', px, py, tx, ty, nx, ny, 0.45, zd0 + 0.7, zd1 - 0.6, 0.15)
        rect_panel(l5, 'hi_marble', px - tx * 0.17, py - ty * 0.17, tx, ty, nx, ny, 0.08, zd0 + 0.7, zd1 - 0.6, 0.20)
        amd = -150 + 210 * (k + 1.0) / npl
        am = math.radians(amd)
        mx, my = math.cos(am), math.sin(am)
        if k < npl - 1:
            qx, qy = cx + mx * Rd, cy + my * Rd
            arch_panel(l1, 'deep', qx, qy, -my, mx, mx, my, 0.85, zd0 + 1.6, zd0 + 4.4, 0.10)
            rect_panel(l4, 'trav_flat', qx, qy, -my, mx, mx, my, 1.1, zd0 + 1.48, zd0 + 1.6, 0.15)
            if any(abs(amd + bd) < 5.5 for bd, _, _, _ in breach):
                continue                      # 콘크리트 속 자리와 겹치는 칸은 창·원반을 두지 않는다
            rect_panel(l1, 'deeper', qx, qy, -my, mx, mx, my, 0.42, zd1 - 3.3, zd1 - 2.3, 0.10)
            disk_panel(l4, 'marble_lt', qx, qy, mx, my, zd1 - 1.1, 0.28, 0.15, 8)
            # L6 빗물 자국(코니스 밑으로 흐른 짙은 줄)
            if k % 2 == 0:
                rect_panel(l6, 'stain', qx + (-my) * 0.55, qy + mx * 0.55, -my, mx, mx, my, 0.12, zd1 - 0.6 - 1.6 - 1.2 * hsh(k, 2.2), zd1 - 0.62, 0.25)
    # L4 원통 위쪽 테두리 띠의 콘크리트 속 이음 자국(대리석이 벗겨진 작은 자리, 평면 약 60° 쪽 앞-왼쪽)
    for (deg, z0, w, h) in breach:
        a = math.radians(-deg)
        nx, ny = math.cos(a), math.sin(a); tx, ty = -ny, nx
        px, py = cx + nx * Rd, cy + ny * Rd
        face_poly(l4, 'conc_core', px, py, tx, ty, nx, ny, [(-w / 2, z0), (w / 2, z0 + 0.25), (w / 2 - 0.25, z0 + h), (-w / 2 + 0.35, z0 + h - 0.2)], 0.15)
        face_poly(l1, 'core_dk', px, py, tx, ty, nx, ny, [(-w / 2 + 0.3, z0 + h - 0.22), (w / 2 - 0.25, z0 + h), (w / 2 - 0.25, z0 + h + 0.1), (-w / 2 + 0.3, z0 + h - 0.1)], 0.20)
    # L5 원통 코니스 윗선·밑동 윗선·난간 윗선
    G.ring(l5.bm, cx, cy, Rd + 0.2, Rd + 0.32 + DEC, zd1 - 0.05, zd1 + DEC, 96, l5.mi('hi_marble'), a0=-150, a1=60)
    G.ring(l5.bm, cx, cy, Rd + 0.18, Rd + 0.3, zd0 + 0.7, zd0 + 0.7 + DEC, 96, l5.mi('hi'), a0=-150, a1=60)
    G.ring(l5.bm, cx, cy, rp - 0.9, rp + 0.02, zp1, zp1 + DEC, 96, l5.mi('hi_marble'), a0=-150, a1=60)
    # L5 디딤 앞코(평면 북쪽 변) 밝은 띠
    for d, z in ((0.0, STEP_Z[0]), (STEP_D, STEP_Z[1])):
        pbox(l5, 'hi_marble', s0 + 0.05, s1 - 0.05, Y0 + d, Y0 + d + 0.18, z, z + DEC)
    # L6 둔덕 풀 포기·꽃, 원통 밑 풀, 기단 테라스·디딤의 사람(키 2.4, L8 지시선 끝 자리 비움)
    for k in range(26):
        a = 2 * math.pi * hsh(k, 1.1); r = rm * 0.85 * math.sqrt(hsh(k, 2.2))
        z = zmb + (zm - zmb) * math.sqrt(max(0.0, 1.0 - (r / rm) ** 2))
        if k % 3 == 0:
            blob(l6, 'flower_y' if k % 2 else 'flower_w', cx + r * math.cos(a), cy + r * math.sin(a), z, 0.22, 0.22, 0.12, k)
        else:
            blob(l6, 'grass3' if k % 2 else 'grass', cx + r * math.cos(a), cy + r * math.sin(a), z, 0.5, 0.5, 0.18, k)
    for k in range(18):
        a = math.radians(-150 + 210 * hsh(k, 3.3))
        tufts(l6, cx + (Rd + 0.45) * math.cos(a), cy + (Rd + 0.45) * math.sin(a), Hp, 1.0, k + 9)
    # 16:25 레퍼런스(user_hadrian_bridge): 원통 위쪽을 두른 독립 주열(보이는 호 −150°~60°) + 둔덕 위 원형 정자와 낮은 돔
    zm_mid = (zd0 + zd1) / 2 + 0.1
    G.ring(l2.bm, cx, cy, Rd - 0.02, Rd + 1.55, zm_mid - 0.15, zm_mid + 0.1, 96, l2.mi('trav_flat'), a0=-150, a1=60)   # 주열 바닥 띠
    G.ring(l2.bm, cx, cy, Rd - 0.02, Rd + 1.6, zd1 - 0.6, zd1 - 0.05, 96, l2.mi('trav_flat'), a0=-150, a1=60)        # 주열 엔타블러처
    G.ring(l5.bm, cx, cy, Rd + 1.4, Rd + 1.6 + DEC, zd1 - 0.05, zd1 - 0.02, 96, l5.mi('hi_marble'), a0=-150, a1=60)
    ncol = 15
    for k in range(ncol):
        a = math.radians(-150 + 210 * (k + 0.5) / ncol)
        qx, qy = cx + (Rd + 1.05) * math.cos(a), cy + (Rd + 1.05) * math.sin(a)
        cyl(l2, 'marble_flat', qx, qy, 0.32, zm_mid + 0.1, zd1 - 0.85, 10)
        cyl(l2, 'trav_flat', qx, qy, 0.34, zd1 - 0.85, zd1 - 0.6, 10)
        G.box(l5.bm, qx - 0.04, qx + 0.04, qy - 0.32, qy - 0.26, zm_mid + 0.3, zd1 - 0.9, l5.mi('hi_marble'))
    # 18:30 레퍼런스(user_hadrian_bridge)의 원형 정자: 반지름 3.2 → 4.3, 기둥 10 → 16, 다락 띠 · 낮은 돔 · 등롱, 둘레 계단 3단. 꼭대기 높이(zt0 + 5.55)는 그대로(상자 위 변)
    zt0 = zm - 0.6; rt = 4.3
    cyl(l2, 'trav_flat', cx, cy, rt + 0.95, zt0 - 0.5, zt0 - 0.15, 40)                    # 계단 3단
    cyl(l2, 'trav_flat', cx, cy, rt + 0.65, zt0 - 0.3, zt0 + 0.1, 40)
    cyl(l2, 'trav_flat', cx, cy, rt + 0.35, zt0 - 0.1, zt0 + 0.35, 40)                   # 정자 기단
    cyl(l0, 'marble_flat', cx, cy, rt - 0.6, zt0, zt0 + 3.4, 40)                          # 정자 원통(속)
    ncl = 16
    for k in range(ncl):
        a = 2 * math.pi * (k + 0.5) / ncl
        qx, qy = cx + rt * math.cos(a), cy + rt * math.sin(a)
        cyl(l2, 'marble_flat', qx, qy, 0.26, zt0 + 0.35, zt0 + 2.78, 10)
        cyl(l2, 'trav_flat', qx, qy, 0.34, zt0 + 2.78, zt0 + 3.0, 10)                     # 주두
        cyl(l2, 'trav_flat', qx, qy, 0.33, zt0 + 0.35, zt0 + 0.5, 10)                     # 주초
        G.box(l5.bm, qx - 0.04, qx + 0.04, qy - 0.26, qy - 0.2, zt0 + 0.55, zt0 + 2.7, l5.mi('hi_marble'))
    G.ring(l2.bm, cx, cy, rt - 0.6, rt + 0.42, zt0 + 3.0, zt0 + 3.4, 40, l2.mi('trav_flat'))   # 엔타블러처
    cyl(l0, 'marble_flat', cx, cy, rt - 0.2, zt0 + 3.4, zt0 + 3.85, 40)                   # 다락 띠
    G.ring(l2.bm, cx, cy, rt - 0.25, rt + 0.05, zt0 + 3.75, zt0 + 3.88, 40, l2.mi('trav_flat'))
    bmd = l0.bm; nn = 32; rows_ = []
    for j in range(5):                                                                    # 낮은 돔(구면 모자, 높이 1.2)
        t = j / 4.0
        rr = (rt - 0.15) * math.cos(t * math.pi / 2); zz = zt0 + 3.85 + 1.2 * math.sin(t * math.pi / 2)
        rows_.append([bmd.verts.new((cx + rr * math.cos(2 * math.pi * k / nn), cy + rr * math.sin(2 * math.pi * k / nn), zz)) for k in range(nn)] if j < 4 else [bmd.verts.new((cx, cy, zz))])
    for j in range(3):
        for k in range(nn):
            f = bmd.faces.new([rows_[j][k], rows_[j][(k + 1) % nn], rows_[j + 1][(k + 1) % nn], rows_[j + 1][k]]); f.material_index = l0.mi('marble_lt')
    for k in range(nn):
        f = bmd.faces.new([rows_[3][k], rows_[3][(k + 1) % nn], rows_[4][0]]); f.material_index = l0.mi('marble_lt')
    f = bmd.faces.new(rows_[0][::-1]); f.material_index = l0.mi('marble_lt')
    cyl(l2, 'marble_flat', cx, cy, 0.55, zt0 + 4.9, zt0 + 5.4, 12)                       # 등롱
    cone(l2, 'trav_flat', cx, cy, 0.66, zt0 + 5.4, zt0 + 5.55, 12)
    for k in range(ncl):                                                                  # L3 정자 속 벽 줄눈(기둥 사이) · L4 다락 작은 창
        a = 2 * math.pi * k / ncl
        G.box(l3.bm, cx + (rt - 0.55) * math.cos(a) - 0.05, cx + (rt - 0.55) * math.cos(a) + 0.05, cy + (rt - 0.55) * math.sin(a) - 0.05, cy + (rt - 0.55) * math.sin(a) + 0.05, zt0 + 0.4, zt0 + 2.9, l3.mi('joint'))
        if -150.0 < math.degrees(a) - 360.0 * (math.degrees(a) > 180.0) < 60.0:
            nx_, ny_ = math.cos(a), math.sin(a)
            rect_panel(l4, 'deep', cx + nx_ * (rt - 0.2), cy + ny_ * (rt - 0.2), -ny_, nx_, nx_, ny_, 0.34, zt0 + 3.48, zt0 + 3.7, 0.04)
    G.ring(l1.bm, cx, cy, rt - 0.62, rt - 0.58, zt0 + 0.4, zt0 + 2.9, 40, l1.mi('deep'), a0=-150, a1=60)
    G.ring(l5.bm, cx, cy, rt + 0.22, rt + 0.42 + DEC, zt0 + 3.4, zt0 + 3.43, 40, l5.mi('hi_marble'), a0=-150, a1=60)
    G.ring(l5.bm, cx, cy, rt - 0.2, rt + 0.05 + DEC, zt0 + 3.88, zt0 + 3.91, 40, l5.mi('hi_marble'), a0=-150, a1=60)
    # 18:30 기단 윗면 둘레 난간 담(밑단 · 동자 · 손잡이 · 받침 기둥). 북쪽 디딤 홈은 비운다
    zr0, zr1 = Hp + 0.62, Hp + 0.78
    ins, th = 0.35, 0.3
    for kind, a0_, a1_, b0, b1 in (('x', X0 + ins, X1 - ins, Y1 - ins - th, Y1 - ins), ('x', X0 + ins, X1 - ins, Y0 + ins, Y0 + ins + th),
                                    ('y', Y0 + ins + th, Y1 - ins - th, X1 - ins - th, X1 - ins), ('y', Y0 + ins + th, Y1 - ins - th, X0 + ins, X0 + ins + th)):
        segs = [(a0_, s0 - 0.25), (s1 + 0.25, a1_)] if (kind == 'x' and b0 < Y0 + 1.0) else [(a0_, a1_)]
        for (c0, c1) in segs:
            if c1 - c0 < 0.6:
                continue
            P = (lambda t, b0=b0, b1=b1: (t, (b0 + b1) / 2)) if kind == 'x' else (lambda t, b0=b0, b1=b1: ((b0 + b1) / 2, t))
            if kind == 'x':
                pbox(l2, 'trav_flat', c0, c1, b0, b1, Hp, Hp + 0.16)
                pbox(l2, 'trav_flat', c0 - 0.03, c1 + 0.03, b0 - 0.03, b1 + 0.03, zr0, zr1)
                pbox(l5, 'hi_marble', c0, c1, b1 - 0.06, b1 + 0.03 + DEC, zr1, zr1 + DEC)
            else:
                pbox(l2, 'trav_flat', b0, b1, c0, c1, Hp, Hp + 0.16)
                pbox(l2, 'trav_flat', b0 - 0.03, b1 + 0.03, c0 - 0.03, c1 + 0.03, zr0, zr1)
                pbox(l5, 'hi_marble', b1 - 0.06, b1 + 0.03 + DEC, c0, c1, zr1, zr1 + DEC)
            n_ = int((c1 - c0) / 0.42)
            for i in range(n_):
                px, py = P(c0 + (c1 - c0) * (i + 0.5) / n_)
                cyl(l4, 'marble_flat', px, -py, 0.085, Hp + 0.16, zr0, 6)
            m_ = max(1, int((c1 - c0) / 3.4))
            for i in range(m_ + 1):
                px, py = P(c0 + (c1 - c0) * i / m_)
                pbox(l2, 'marble_flat', px - 0.22, px + 0.22, py - 0.22, py + 0.22, Hp, zr1 + 0.12)
    anchor_L8 = R.to_plan(T_L8[0], T_L8[1] + Hp)
    visitors = [(Xc + 18.6, Yc + 12.0), (Xc + 19.4, Yc - 9.5), (Xc - 4.0, Yc + 19.6), (Xc + 6.5, Yc + 19.0), (Xc - 16.0, Yc + 17.2), (Xc + 20.2, Yc + 3.6), (Xc - 19.8, Yc + 8.5)]
    for i, (vx, vy) in enumerate(visitors):
        if math.hypot(vx - anchor_L8[0], vy - anchor_L8[1]) < 2.5:
            continue
        person(l6, vx, -vy, Hp, PH, 200 + i, 'amph' if i == 3 else None)
    person(l6, (s0 + s1) / 2 - 1.2, -(Y0 + STEP_D * 1.5), STEP_Z[1], PH, 230)
    O.finish()
    return O


# ───────────────────────── 아일리우스 다리(폰스 아일리우스: 영묘 앞에서 테베레 ↘ 팔을 건넌다) ─────────────────────────
def build_bridge(ctx):
    O = Obj(ctx, 'PonsAelius')
    l0 = O.lay(0, 'Body', recalc=True); l1 = O.lay(1, 'ArchShade', recalc=True); l2 = O.lay(2, 'ParapetCutwaters', recalc=True)
    l3 = O.lay(3, 'VoussoirsDeck', recalc=True); l4 = O.lay(4, 'PostsRoundels', recalc=True); l5 = O.lay(5, 'Light', recalc=True); l6 = O.lay(6, 'Life')
    x0, x1 = BR_X
    ya, yb = BR_Y                         # 북쪽 둑 → 기단 북쪽 변
    zwalk = BR_WALK; zdeck = zwalk - DEC  # 상판 몸 윗면(+ 판석 0.05 = 보행면 3.0)
    zbot = RIVER_Z - 0.5
    p1, p2 = BR_PIERS
    spans = [(ya + 0.3, p1[0]), (p1[1], p2[0]), (p2[1], BANK_S - 0.3)]
    crown = zwalk - 0.45
    holes = []
    for s_0, s_1 in spans:
        r = (s_1 - s_0) / 2.0
        holes.append(('arch', -s_1, -s_0, zbot, crown - r))
    holes.sort(key=lambda h: h[1])
    # 강 위 몸(아치 3·교각 2, 양 끝 둑 받침 0.3) + 남쪽 둑 위 받침(땅 윗면 Z 0부터, 기단 북쪽 변까지)
    G.wall_holes(l0.bm, 'Y', -BANK_S, -ya, x0, x1, zbot, zdeck, holes, l0.mi('trav'), 14)
    pbox(l0, 'trav', x0, x1, BANK_S, yb, 0.0, zdeck)
    # L3 상판 판석(보행면 3.0)
    pbox(l3, 'slab', x0 + 0.35, x1 - 0.35, ya, yb, zdeck, zwalk)
    # L1 아치 속 그늘(상판 몸 가운데 면)
    for s_0, s_1 in spans:
        r = (s_1 - s_0) / 2.0
        arch_panel(l1, 'deeper', (x0 + x1) / 2, -(s_0 + s_1) / 2, 0, 1, 1, 0, s_1 - s_0 - 0.1, RIVER_Z + 0.01, crown - r, 0.005)
    # L2 난간(사람 키 0.42, 동·서 변) · 물가르개(교각 하류 +X 쪽은 둥근 끝, 상류 −X 쪽은 뾰족) · 처마 띠
    zpar = zwalk + 1.0
    for (xa_, xb_) in ((x0, x0 + 0.35), (x1 - 0.35, x1)):            # 16:25 레퍼런스: 난간 = 밑단 + 동자 + 손잡이(발루스트레이드)
        pbox(l2, 'trav_flat', xa_, xb_, ya, yb, zdeck, zdeck + 0.25)
        pbox(l2, 'trav_flat', xa_ - 0.03, xb_ + 0.03, ya, yb, zpar - 0.2, zpar)
        yy_ = ya + 0.45
        while yy_ < yb - 0.45:
            cyl(l4, 'marble_flat', (xa_ + xb_) / 2, -yy_, 0.1, zdeck + 0.25, zpar - 0.2, 6)
            yy_ += 0.4
    pbox(l2, 'marble_flat', x1, x1 + 0.15, ya, yb, zdeck - 0.4, zdeck - 0.12)
    cxw, cxe = BR_CUT_X
    for pa, pb in (p1, p2):
        pm = (pa + pb) / 2
        prism(l2, 'trav_flat', [(x1, -pa), (cxe, -pm), (x1, -pb)], zbot, crown - (spans[1][1] - spans[1][0]) / 2 + 0.2)
        prism(l2, 'trav_flat', [(x0, -pb), (cxw, -pm), (x0, -pa)], zbot, crown - (spans[1][1] - spans[1][0]) / 2 + 0.2)
        cone_top = crown - (spans[1][1] - spans[1][0]) / 2 + 0.2
        prism(l2, 'trav_flat', [(x1, -pa - 0.25), (x1 + (cxe - x1) * 0.65, -pm), (x1, -pb + 0.25)], cone_top, cone_top + 0.55)
    # L3 홍예석 띠(보이는 +X 면) + 상판 몸 블록 무늬는 L0 재질(trav)
    for s_0, s_1 in spans:
        r = (s_1 - s_0) / 2.0
        arch_ring(l3, 'marble_flat', x1, -(s_0 + s_1) / 2, 0, 1, 1, 0, r, r + 0.38, crown - r, 0.10)
    # L4 난간 끝 기둥 4 · 아치 사이 둥근 장식(교각 위 벽면) · 배수구
    for yy in (ya + 0.3, yb - 0.3):
        for xx in (x0 + 0.175, x1 - 0.175):
            pbox(l4, 'marble_flat', xx - 0.32, xx + 0.32, yy - 0.32, yy + 0.32, zdeck, zpar + 0.45)
            pbox(l4, 'trav_flat', xx - 0.4, xx + 0.4, yy - 0.4, yy + 0.4, zpar + 0.45, zpar + 0.6)
    for pa, pb in (p1, p2):
        pm = (pa + pb) / 2
        disk_panel(l4, 'marble_lt', x1, -pm, 1, 0, crown - 0.8, 0.46, 0.10, 10)
        disk_panel(l4, 'deep', x1, -pm, 1, 0, crown - 0.8, 0.3, 0.15, 10)
        for sg in (-1, 1):                                               # 16:25 레퍼런스: 교각 위 아이디큘라 틀(벽기둥 둘 + 처마)
            rect_panel(l2, 'marble_flat', x1, -(pm + sg * 0.72), 0, 1, 1, 0, 0.22, crown - 1.6, crown - 0.15, 0.12)
        rect_panel(l2, 'trav_flat', x1, -pm, 0, 1, 1, 0, 1.8, crown - 0.15, crown + 0.05, 0.16)
    # 18:30 레퍼런스 다리: 홍예돌 줄눈(아치마다 11). 교각 면은 물가르개가 가린다
    for s_0, s_1 in spans:
        r = (s_1 - s_0) / 2.0; zs_ = crown - r; cm_ = -(s_0 + s_1) / 2
        for j in range(1, 12):
            th_ = math.pi * j / 12
            c_, s_ = math.cos(th_), math.sin(th_)
            q = [(r * c_ - 0.025 * s_, zs_ + r * s_ + 0.025 * c_), ((r + 0.38) * c_ - 0.025 * s_, zs_ + (r + 0.38) * s_ + 0.025 * c_),
                 ((r + 0.38) * c_ + 0.025 * s_, zs_ + (r + 0.38) * s_ - 0.025 * c_), (r * c_ + 0.025 * s_, zs_ + r * s_ - 0.025 * c_)]
            face_poly(l3, 'joint', x1, cm_, 0, 1, 1, 0, q, 0.11)
    # L5 난간 윗선·처마 윗선·물가르개 모서리
    pbox(l5, 'hi', x1 - 0.35, x1 + 0.02, ya, yb, zpar, zpar + DEC)
    pbox(l5, 'hi', x0, x0 + 0.35, ya, yb, zpar, zpar + DEC)
    pbox(l5, 'hi_warm', x1 + 0.1, x1 + 0.15 + DEC, ya, yb, zdeck - 0.16, zdeck - 0.12)
    for pa, pb in (p1, p2):
        pm = (pa + pb) / 2
        pbox(l5, 'hi', x1 + 0.5, x1 + 0.72, pm - 0.08, pm + 0.08, cone_top + 0.5, cone_top + 0.55)
    # L6 사람(키 2.4)·물때·물결
    for i, yy in enumerate((ya + 3.0, ya + 8.5, ya + 13.6, yb - 3.2)):
        person(l6, (x0 + x1) / 2 + (1.2 if i % 2 else -1.0), -yy, zwalk, PH, 300 + i, 'sack' if i == 1 else None)
    for pa, pb in (p1, p2):
        pm = (pa + pb) / 2
        prism(l6, 'algae', [(x1 + DEC, -pa + DEC), (cxe + DEC, -pm), (x1 + DEC, -pb - DEC)], RIVER_Z - 0.02, RIVER_Z + 0.35)
        flat_poly(l6, 'foam', [(cxe, -pm), (cxe + 1.4, -pm - 1.2), (cxe + 1.7, -pm - 0.9), (cxe + 0.3, -pm + 0.2)], RIVER_Z + 0.07)
        flat_poly(l6, 'foam', [(cxe, -pm), (cxe + 1.4, -pm + 1.3), (cxe + 1.1, -pm + 1.6), (cxe + 0.1, -pm + 0.4)], RIVER_Z + 0.07)
    O.finish()
    return O


# ───────────────────────── 테베레 하역장(엠포리움: 돌 부두·기중기·창고) — 강 북쪽 둑 ─────────────────────────
def treadwheel_crane(O, x, y, z, s, seed=0.0):
    """디딤바퀴 기중기: A자 다리 2·팔·바퀴·밧줄·짐(강 쪽으로 기운다). Blender 축, 축척 s"""
    l2 = O.lay(2, 'CraneFrames', recalc=True); l4 = O.lay(4, 'CraneWheelLoad', recalc=True); l5 = O.lay(5, 'CraneLight', recalc=True); l6 = O.lay(6, 'CraneWorkers')
    k = s
    foot = [(x - 0.9 * k, y + 0.5 * k), (x + 0.9 * k, y + 0.5 * k)]
    top = (x, y - 2.5 * k, z + 4.4 * k)
    for fx, fy in foot:
        seg_box(l2, 'wood_dk', (fx, fy, z), top, 0.09 * k)
    seg_box(l2, 'wood_dk', (x, y + 1.3 * k, z), top, 0.08 * k)
    seg_box(l2, 'wood_dk', (x - 0.9 * k, y + 0.5 * k, z + 0.9 * k), (x + 0.9 * k, y + 0.5 * k, z + 0.9 * k), 0.05 * k)
    n = 16; rr = 0.95 * k; cxw, cyw, czw = x + 1.15 * k, y + 0.45 * k, z + rr + 0.05
    for i in range(n):
        a0 = 2 * math.pi * i / n; a1 = 2 * math.pi * (i + 1) / n
        p0 = (cxw, cyw + rr * math.cos(a0), czw + rr * math.sin(a0)); p1 = (cxw, cyw + rr * math.cos(a1), czw + rr * math.sin(a1))
        seg_box(l4, 'wood', p0, p1, 0.07 * k)
        if i % 4 == 0:
            seg_box(l4, 'wood_dk', (cxw, cyw, czw), p0, 0.03 * k)
    person(l6, cxw, cyw, czw - rr + 0.07 * k, PH, seed)
    hook = (top[0], top[1] - 0.1 * k, top[2] - 2.2 * k)
    seg_box(l2, 'wood_dk', top, hook, 0.025 * k)
    obox(l4, 'lime', hook[0], hook[1], 1, 0, 0.32 * k, 0.26 * k, hook[2] - 0.5 * k, hook[2])
    seg_box(l5, 'hi_warm', (top[0] - 0.05 * k, top[1], top[2]), (top[0] + 0.05 * k, top[1], top[2] + 0.12 * k), 0.06 * k)


def build_emporium(ctx):
    O = Obj(ctx, 'TiberEmporium')
    l0 = O.lay(0, 'QuayStores', recalc=True); l1 = O.lay(1, 'QuayDepth', recalc=True); l2 = O.lay(2, 'Coping', recalc=True); l3 = O.lay(3, 'Paving', recalc=True)
    l4 = O.lay(4, 'StairsRings', recalc=True); l5 = O.lay(5, 'EdgeLight', recalc=True); l6 = O.lay(6, 'Goods')
    xa, xb = EMP_X
    edge = EMP_EDGE
    yq = EMP_YB                                # 부두 뒷선(props 상자에서 역산)
    r4a, r4b = R4_X
    zt = PLAT_Z + DEC
    yl = edge - 1.3                            # 윗단 앞선(아랫단 뒤 벽)
    # L0 돌 부두(윗단 보행면 0.30 = ground 길 R4 윗면, 아랫단 배 대는 단 −1.2) + 강 쪽 벽
    #  윗단: 하역장 길(R4, ground가 Y 300.0까지 짓는다)이 닿는 자리는 Y 300.0부터(길과 겹침 0)
    for x0_, x1_, yy in ((xa, r4a, yq), (r4a, r4b, 300.0), (r4b, xb, yq)):
        if x1_ - x0_ < 0.2:
            continue
        pbox(l0, 'quay_flat', x0_, x1_, yy, yl, 0.0, PLAT_Z)
        pbox(l3, 'pave', x0_, x1_, yy, yl - 0.12, PLAT_Z, zt)
    pbox(l0, 'quay', xa, xb, yl, edge - 1.0, RIVER_Z - 0.5, zt)
    pbox(l0, 'quay_flat', xa, xb, edge - 1.0, edge, RIVER_Z - 0.5, RIVER_Z + 0.8)
    # L1 젖은 아랫단 앞면(0.06 앞)
    pbox(l1, 'wet', xa, xb, edge, edge + 0.06, RIVER_Z - 0.03, RIVER_Z + 0.6)
    # L2 갓돌 두 줄
    pbox(l2, 'trav_flat', xa, xb, yl - 0.12, yl + 0.42, zt, zt + 0.14)
    pbox(l2, 'trav_flat', xa, xb, edge - 0.12, edge + 0.12, RIVER_Z + 0.8, RIVER_Z + 0.92)
    # L3 아랫단 뒤 벽 돌 무늬(0.05 앞)
    pbox(l3, 'quay', xa + 0.05, xb - 0.05, yl + 0.3, yl + 0.3 + DEC, RIVER_Z + 0.92, PLAT_Z)
    # L4 계단 3곳(윗단 → 아랫단), 계선 고리(짙은 점)
    for xs in (xa + 3.0, xa + 20.5, r4a + 1.0):
        for st in range(3):
            pbox(l4, 'quay_flat', xs, xs + 1.6, yl + 0.3, yl + 0.3 + 0.25 * (st + 1), RIVER_Z + 0.8, PLAT_Z - 0.375 * (st + 1))
    for i in range(int((xb - xa - 2.0) / 4.0) + 1):
        xx = xa + 2.0 + 4.0 * i
        pbox(l4, 'iron', xx - 0.12, xx + 0.12, edge + 0.06, edge + 0.12, RIVER_Z + 0.35, RIVER_Z + 0.55)
    # L5 갓돌 앞 모서리
    pbox(l5, 'hi', xa, xb, yl + 0.3, yl + 0.42, zt + 0.14, zt + 0.19)
    pbox(l5, 'hi', xa, xb, edge + 0.0, edge + 0.12, RIVER_Z + 0.92, RIVER_Z + 0.97)
    # 창고(포르티쿠스 아이밀리아처럼 볼트 칸이 이어진 긴 창고, 박공은 강과 직각) — 하역장 길 자리는 비운다
    ztop_max = EMP_ZMAX - 0.6
    for x0_, x1_ in ((xa + 0.9, r4a - 0.6), (r4b + 0.6, xb - 0.5)):
        if x1_ - x0_ < 3.0:
            continue
        n = max(1, int((x1_ - x0_) / 5.2))
        w = (x1_ - x0_) / n
        for i in range(n):
            u0 = x0_ + w * i + 0.08; u1 = x0_ + w * (i + 1) - 0.08
            d0 = yq + 0.5; d1 = yl - 3.9
            F = Fr((u0 + u1) / 2, -(d0 + d1) / 2, zt, math.radians(90.0))
            H = min(5.0, ztop_max - zt - 1.6)
            whouse(O, F, -(d1 - d0) / 2, (d1 - d0) / 2, -(u1 - u0) / 2, (u1 - u0) / 2, 0.0, H, 1.6, i, two=True, bays=1.45, tag='Porticus')
    # 기중기 2대(부두 앞, 강 쪽으로)
    treadwheel_crane(O, xa + 8.6, -(edge - 2.0), zt, 1.8, 1.0)
    treadwheel_crane(O, xa + 20.6, -(edge - 2.0), zt, 1.8, 2.0)
    # L6 짐: 암포라 더미, 생석회 자루, 화산재·골재 더미, 목재, 일꾼(키 2.4), 매어 둔 거룻배
    ah = K_AMPH * H_PERSON
    amph_stack(l6, xa + 1.6, -(yl - 1.0), zt, ah, 4, 2)
    amph_stack(l6, xa + 14.0, -(yl - 1.1), zt, ah, 3, 2)
    sacks(l6, 'lime', xa + 4.6, -(yl - 0.9), zt, 1.0, 5, 1.0)
    sacks(l6, 'lime', xa + 24.0, -(yl - 1.0), zt, 1.0, 4, 2.0)
    heap(l6, 'pozz', r4a - 2.2, -(yl - 1.2), zt, 1.05, 0.9, 10)
    heap(l6, 'aggr', r4b + 0.2, -(yl - 2.9), zt, 0.75, 0.62, 10)
    heap(l6, 'lime', xa + 17.4, -(yl - 1.3), zt, 0.85, 0.7, 10)
    for i in range(4):
        pbox(l6, 'wood_flat', xa + 11.0, xa + 13.6, yl - 2.0, yl - 2.0 + 0.35, zt + 0.25 * i, zt + 0.25 * i + 0.24)
    crowd(l6, [(xa + 3.4, -(yl - 0.9)), (xa + 6.4, -(yl - 1.3)), (xa + 11.4, -(yl - 0.7)), (xa + 15.6, -(yl - 1.0)),
               (xa + 19.0, -(yl - 2.2)), (r4a + 1.6, -(yl - 1.6)), (r4a + 4.4, -(yl - 2.4)), (xa + 26.0, -(yl - 1.4))],
          zt, PH, 500, 2, 'sack')
    # 창고 뒤 덤불·사이프러스 쌍(props 상자 안)
    for i, xx in enumerate((xa + 2.0, xa + 8.5, xa + 15.0, xa + 22.5)):
        bush(l6, xx, -(yq - 0.6), 0.0, 1.0, i)
        tufts(l6, xx + 1.2, -(yq - 0.4), 0.0, 1.0, i + 30)
    for dd in (0.0, 1.2):
        cypress(l6, r4a - 3.0 + dd, -(yq - 0.4 + dd * 0.4), 0.0, 2.6 * H_PERSON * (1.0 + 0.08 * dd), dd + 9)
    # 매어 둔 거룻배(기중기 앞, 아랫단 앞 강물 위)
    F = Fr(xa + 9.0, -(edge + 1.6), RIVER_Z, math.radians(180.0))
    ship(O, F, 8.0, 2.4, 0.6, 'barge', 11.0, 'lime', 2, 0.0, True, 1.5)
    O.finish()
    # 땅 절단체(숨김): 아랫단(배 대는 단) 자리
    cl = Lay()
    pbox(cl, 'soil', xa - 0.01, xb + 0.01, yl - 0.02, edge + 0.6, RIVER_Z - 0.5, 2.0)
    cut = R.bm_to_obj(cl.bm, 'X_CUT_CoastEmporium', ctx['M']['soil'], ctx['coll'], O.root)
    cut.hide_render = True; cut.display_type = 'WIRE'
    return O


# ───────────────────────── fit_to_box 오브젝트: 사람 키를 지키는 2회 짓기 ─────────────────────────
def fit_build(fn, box_, grow, tol=0.04):
    """fn(lk) → Obj. lk = 생활 소품 배율(1/s). 상자에 맞춘 축척 s만큼 사람·소품을 되돌려 키 2.4를 지킨다"""
    O = fn(1.0)
    s, bb = G.fit_to_box(O.root, box_, grow)
    s1, lk = s, 1.0
    if abs(s - 1.0) > tol:
        kill_obj(O.root)
        lk = 1.0 / s
        O = fn(lk)
        s2, bb = G.fit_to_box(O.root, box_, grow)
        s = s2
    O.fit_scale = s
    O.person_h = round(H_PERSON * lk * s, 3)          # 최종 사람 키(화면 mm)
    O.fit_box = tuple(round(v, 2) for v in box_)
    return O


def footprint_min_dist(root, center, zmax=0.3):
    """땅에 닿는 정점(Z ≤ zmax)과 평면 점 center의 최소 거리"""
    bpy.context.view_layer.update()
    dmin = 1e9
    for o in root.children_recursive:
        if o.type != 'MESH':
            continue
        mw = o.matrix_world
        for v in o.data.vertices:
            w = mw @ v.co
            if w.z <= zmax:
                dmin = min(dmin, math.hypot(w.x - center[0], -w.y - center[1]))
    return dmin


def safe_box(fn, box_, grow, center, rmin, step=0.5):
    """spec 상자 안에서 오른쪽 변만 줄여, 땅 발자국이 예약 원(center, rmin) 밖에 들게 하는 상자(D14 조경 R 90.5)"""
    O = fn(1.0)
    bx = list(box_)
    for _ in range(40):
        G.fit_to_box(O.root, tuple(bx), grow)
        if footprint_min_dist(O.root, center) >= rmin:
            break
        bx[2] -= step
    kill_obj(O.root)
    return tuple(bx)


# ───────────────────────── 석회 가마(강 북쪽 둑): 돌 가마 + 뒤쪽 흙 비탈 + 불 아궁이 + 연기 ─────────────────────────
def build_kiln(ctx, lk=1.0):
    O = Obj(ctx, 'LimeKiln')
    l0 = O.lay(0, 'KilnMound', recalc=True); l1 = O.lay(1, 'MouthStoke', recalc=True); l2 = O.lay(2, 'Bands', recalc=True); l3 = O.lay(3, 'Masonry', recalc=True)
    l4 = O.lay(4, 'FireShedPiles', recalc=True); l5 = O.lay(5, 'Light', recalc=True); l6 = O.lay(6, 'SmokeWorkers')
    R0, RT, HK = 3.0, 2.55, 4.6
    # L0 작업 마당(다진 흙, 불규칙 외곽) · L4 석회석 블록 더미 3 · L6 풀
    yard = []
    for k in range(18):
        a = 2 * math.pi * k / 18
        rr = 6.6 * (0.82 + 0.3 * hsh(k, 4.4))
        yard.append((0.6 + rr * math.cos(a), -0.4 + rr * 0.8 * math.sin(a)))
    prism(O.lay(0, 'Yard', recalc=True), 'soil_dk', yard, 0.0, DEC)
    for j, (bx_, by_) in enumerate(((-5.2, 1.6), (-4.6, -2.0), (6.2, -2.6))):
        for k in range(6 if j < 2 else 4):
            ox = (k % 3) * 0.62; oy = (k // 3) * 0.55; oz = 0.0 if k < 3 else 0.42
            box(l4, 'aggr' if (k + j) % 3 else 'lime', bx_ + ox - 0.28, bx_ + ox + 0.28, by_ + oy - 0.24, by_ + oy + 0.24, DEC + oz, DEC + oz + 0.42)
    cyl(l0, 'quay_flat', 0, 0, R0, 0.0, HK, 32, r_top=RT)
    prism(l0, 'soil', [(-R0 * 0.3, R0 * 0.9), (-R0 * 1.9, R0 * 1.7), (-R0 * 2.1, R0 * 0.3), (-R0 * 0.9, -R0 * 0.2)], 0.0, 0.18)
    xprism(O.lay(0, 'Ramp', recalc=True), 'soil', [(R0 * 0.8, 0.0), (R0 * 2.5, 0.0), (R0 * 0.8, HK - 0.4)], -1.2, 1.2)
    cyl(l1, 'deeper', 0, 0, RT - 0.45, HK - 0.02, HK + DEC, 24)
    arch_panel(l1, 'arch_in', 0.0, -R0 + 0.05, 1, 0, 0, -1, 1.95, 0.0, 0.9, 0.10)
    arch_panel(l1, 'deeper', 0.0, -R0 + 0.05, 1, 0, 0, -1, 1.5, 0.0, 0.9, 0.16)
    cyl(l2, 'trav_flat', 0, 0, R0 - 0.02 + 0.12, 1.6, 1.85, 32, r_top=R0 - 0.1 + 0.12)
    cyl(l2, 'trav_flat', 0, 0, R0 - 0.2 + 0.12, 3.2, 3.45, 32, r_top=R0 - 0.28 + 0.12)
    G.ring(l2.bm, 0, 0, RT - 0.45, RT + 0.15, HK, HK + 0.3, 32, l2.mi('trav_flat'))
    G.ring(l3.bm, 0, 0, R0 - 0.02, R0 + DEC, 0.05, 1.6, 32, l3.mi('quay'), a0=-150, a1=60)
    G.ring(l3.bm, 0, 0, R0 - 0.2, R0 - 0.2 + DEC + 0.02, 1.85, 3.2, 32, l3.mi('quay'), a0=-150, a1=60)
    arch_ring(l3, 'brick', 0.0, -R0 + 0.05, 1, 0, 0, -1, 0.75, 1.05, 0.9, 0.12)
    blob(l4, 'fire', 0.0, -R0 - 0.12, 0.55, 0.55, 0.12, 0.45, 1.0)
    blob(l4, 'fire2', 0.1, -R0 - 0.2, 0.45, 0.32, 0.1, 0.3, 2.0)
    for i in range(4):
        for j in range(4 - i):
            seg_box(l4, 'wood_flat', (3.3 + 0.36 * j + 0.18 * i, -3.6, 0.17 + 0.3 * i), (3.3 + 0.36 * j + 0.18 * i, -1.0, 0.17 + 0.3 * i), 0.16)
    heap(l4, 'aggr', -2.9, -3.2, 0.0, 1.4, 1.1, 10)
    heap(l4, 'lime', 4.2, 0.4, 0.0, 1.1, 0.9, 10)
    F = Fr(4.6, 2.8, 0.0, 0.0)
    for (u, v) in ((-1.4, -1.0), (1.4, -1.0), (1.4, 1.0), (-1.4, 1.0)):
        fbox(l4, 'wood_dk', F, u - 0.1, u + 0.1, v - 0.1, v + 0.1, 0.0, 2.2)
    fgable(l4, 'roof_flat', F, -1.6, 1.6, -1.2, 1.2, 2.2, 2.9, 0.1)
    roof_tiles(l3, 'roof_dk', F, -1.6, 1.6, -1.2, 1.2, 2.2, 2.9, 0.1, 0.4, 0.08)
    sacks(l4, 'lime', 4.0, 2.4, 0.0, 0.8 * lk * 1.4, 5, 3.0)
    for dy in (-0.55, 0.05):
        seg_box(l4, 'wood_dk', (3.75, dy - 0.6, 0.0), (2.62, dy - 0.25, HK + 0.25), 0.06)
    for k in range(1, 7):
        t = k / 7.0
        x = 3.75 + (2.62 - 3.75) * t; yo = -0.6 + 0.35 * t; z = (HK + 0.25) * t
        seg_box(l4, 'wood_dk', (x, -0.55 + yo, z), (x, 0.05 + yo, z), 0.035)
    G.ring(l5.bm, 0, 0, RT + 0.05, RT + 0.17, HK + 0.3, HK + 0.3 + DEC, 32, l5.mi('hi'), a0=-150, a1=60)
    G.ring(l5.bm, 0, 0, R0 + 0.06, R0 + 0.12, 1.85, 1.85 + DEC, 32, l5.mi('hi_warm'), a0=-150, a1=60)
    G.ring(l5.bm, 0, 0, R0 - 0.12, R0 - 0.06, 3.45, 3.45 + DEC, 32, l5.mi('hi_warm'), a0=-150, a1=60)
    puffs = [(0.0, 0.0, 5.5, 1.0), (0.45, 0.25, 6.9, 1.2), (1.15, 0.6, 8.3, 1.4), (2.05, 1.0, 9.8, 1.55), (3.1, 1.45, 11.2, 1.6), (4.2, 1.9, 12.4, 1.4)]
    for i, (x, y, z, r) in enumerate(puffs):
        blob(l6, 'smoke', x, -y, z, r, r, r * 0.75, i * 2.3, 2)
    G.ring(l6.bm, 0, 0, RT + 0.17, RT + 0.17 + DEC, HK - 0.9, HK, 32, l6.mi('stain'), a0=-120, a1=30)
    crowd(l6, [(1.6, -4.0), (-1.4, -4.2), (3.2, -1.3), (-4.4, -0.4)], DEC, PH * lk, 600, 1, 'sack')
    for k in range(9):
        a = 2 * math.pi * k / 9 + 0.3
        gx, gy = 0.6 + 7.4 * math.cos(a), -0.4 + 6.0 * math.sin(a)
        grass_patch(l6, 'grass' if k % 2 else 'grass2', gx, gy, DEC, 0.9, 0.5, k + 40)
        tufts(l6, gx + 0.3, gy - 0.2, DEC, 0.9, k + 70)
    O.finish()
    return O


def xprism(ly, key, prof, x0, x1):
    """(Blender y, z) 옆모습 다각형을 x0..x1로 민 입체(경사로·옆 단면). 레이어는 recalc=True로 만든다"""
    bm = ly.bm; mi = ly.mi(key)
    a = [bm.verts.new((x0, y, z)) for y, z in prof]; b = [bm.verts.new((x1, y, z)) for y, z in prof]
    fs = [bm.faces.new(a[::-1]), bm.faces.new(b)]
    n = len(prof)
    for k in range(n):
        fs.append(bm.faces.new([a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]]))
    for f in fs: f.material_index = mi
    G.uv_box(bm, fs)


# ───────────────────────── 오스티아(하구 동쪽 둑): 창고 2·인술라 2·카피톨리움·소나무 ─────────────────────────
def courtyard_horreum(O, cx, cy, w, d, H, rh, seed, tag):
    """안마당을 둘러싼 창고(네 동)"""
    t = 1.5
    F0 = Fr(cx, cy - d / 2 + t / 2, 0.0, 0.0)
    whouse(O, F0, -w / 2, w / 2, -t / 2, t / 2, 0.0, H, rh, seed, two=False, bays=1.1, tag=tag)
    F1 = Fr(cx, cy + d / 2 - t / 2, 0.0, 0.0)
    whouse(O, F1, -w / 2, w / 2, -t / 2, t / 2, 0.0, H, rh, seed + 1, two=False, bays=1.1, tag=tag)
    for sx in (-1, 1):
        F2 = Fr(cx + sx * (w / 2 - t / 2), cy, 0.0, math.radians(90.0))
        whouse(O, F2, -(d / 2 - t), d / 2 - t, -t / 2, t / 2, 0.0, H * 0.92, rh * 0.9, seed + 2 + sx, two=False, bays=1.1, tag=tag)
    pbox(O.lay(3, tag + 'Court', recalc=True), 'pave', cx - w / 2 + t, cx + w / 2 - t, -(cy + d / 2 - t), -(cy - d / 2 + t), 0.0, DEC)


def build_ostia(ctx, lk=1.0):
    """오스티아(창고 몇 채): props 상자 24×16mm에 축척 ≈ 1로 들어가는 작은 구성(창고 안마당 1·인술라 1·카피톨리움·소나무 2)"""
    O = Obj(ctx, 'Ostia')
    l0 = O.lay(0, 'Ground', recalc=True); l2 = O.lay(2, 'TempleColumns', recalc=True); l4 = O.lay(4, 'Balconies', recalc=True); l5 = O.lay(5, 'Light', recalc=True); l6 = O.lay(6, 'PinesPeople')
    box(l0, 'pave_flat', -6.0, 6.6, -1.5, 0.0, 0.0, 0.08)
    box(O.lay(3, 'Decumanus', recalc=True), 'slab', -6.0, 6.6, -1.5, 0.0, 0.08, 0.08 + DEC)
    courtyard_horreum(O, -2.4, 3.3, 6.0, 4.8, 2.4, 0.9, 1.0, 'Horrea')
    for i, (cx, cy, w, d, H) in enumerate(((-3.0, -3.7, 4.2, 2.6, 4.2),)):
        F = Fr(cx, cy, 0.0, 0.0)
        whouse(O, F, -w / 2, w / 2, -d / 2, d / 2, 0.0, H, 1.0, 10 + i, two=True, bays=1.05, tag='Insula')
        fbox(l4, 'wood', F, -w / 2 + 0.2, w / 2 - 0.2, -d / 2 - 0.45, -d / 2, H * 0.5, H * 0.5 + 0.12)
        for k in range(6):
            uu = -w / 2 + 0.3 + (w - 0.6) * k / 5
            fbox(l4, 'wood_dk', F, uu - 0.04, uu + 0.04, -d / 2 - 0.42, -d / 2 - 0.36, H * 0.5 + 0.12, H * 0.5 + 0.55)
        fbox(l4, 'wood_dk', F, -w / 2 + 0.2, w / 2 - 0.2, -d / 2 - 0.45, -d / 2 - 0.36, H * 0.5 + 0.5, H * 0.5 + 0.58)
        fbox(l5, 'hi_warm', F, -w / 2 + 0.2, w / 2 - 0.2, -d / 2 - 0.5, -d / 2 - 0.4, H * 0.5 + 0.12, H * 0.5 + 0.12 + DEC)
    tx, ty = 3.7, -4.1
    lt0 = O.lay(0, 'Temple', recalc=True)
    box(lt0, 'marble_flat', tx - 1.7, tx + 1.7, ty - 2.4, ty + 2.4, 0.0, 1.1)
    for st in range(4):
        box(O.lay(4, 'TempleSteps', recalc=True), 'quay_flat', tx - 1.2, tx + 1.2, ty - 2.4 - 0.25 * (4 - st), ty - 2.4, 0.0, 0.28 * (st + 1) - 0.02)
    box(lt0, 'brick_flat', tx - 1.2, tx + 1.2, ty - 0.6, ty + 2.0, 1.1, 3.4)
    for k in range(4):
        cyl(l2, 'marble_flat', tx - 1.05 + 0.7 * k, ty - 2.0, 0.17, 1.1, 3.25, 10, r_top=0.14)
    box(l2, 'marble_flat', tx - 1.35, tx + 1.35, ty - 2.25, ty + 2.15, 3.25, 3.6)
    Ft = Fr(tx, ty, 0.0, math.radians(90.0))
    fgable(lt0, 'roof_flat', Ft, -2.3, 2.2, -1.4, 1.4, 3.6, 4.4, 0.05)
    roof_tiles(O.lay(3, 'TempleTiles'), 'roof_dk', Ft, -2.3, 2.2, -1.4, 1.4, 3.6, 4.4, 0.05, 0.4, 0.08)
    face_poly(O.lay(1, 'TempleShade', recalc=True), 'deep', tx, ty - 0.6, 1, 0, 0, -1, [(-1.1, 1.1), (1.1, 1.1), (1.1, 3.25), (-1.1, 3.25)], 0.10)
    face_poly(O.lay(4, 'Pediment', recalc=True), 'marble', tx, ty - 2.35, 1, 0, 0, -1, [(-1.3, 3.62), (1.3, 3.62), (0.0, 4.3)], 0.10)
    box(l5, 'hi', tx - 1.35, tx + 1.35, ty - 2.32, ty - 2.2, 3.6, 3.6 + DEC)
    for i, (x, y, h) in enumerate(((5.6, 2.6, 0.95), (-6.6, -6.2, 0.9))):
        pine(l6, x, y, 0.0, K_PINE * H_PERSON * lk * h, i * 1.3)
    crowd(l6, [(-4.2, -0.8), (0.6, -0.7), (4.4, -0.9)], 0.08 + DEC, PH * lk, 700, 3, 'amph')
    for k in range(4):
        grass_patch(l6, 'grass', -5.0 + 3.4 * k, -6.4 + 0.6 * hsh(k), 0.0, 0.9, 0.42, k + 60)
        tufts(l6, -4.6 + 3.4 * k, -6.8, 0.0, 0.9, k + 90)
    O.finish()
    return O


# ───────────────────────── 바지선 2척(테베레)·화산재 운반선(바다): props 상자에 맞춘다 ─────────────────────────
def build_boat(ctx, name, box_, hd_plan, kind, seed, cargo, z_water, L, B, H, mast, crew, poles=0, lk=1.0, sail=True, wake=0.3, goose=True, oars=True):
    cx, cy = (box_[0] + box_[2]) / 2, (box_[1] + box_[3]) / 2
    X, Y = R.to_plan(cx, cy + z_water)
    O = Obj(ctx, name, X, Y, z_water)
    F = Fr(0.0, 0.0, 0.0, math.radians(-hd_plan))
    ship(O, F, L, B, H, kind, seed, cargo, crew, wake, sail, mast, crew_h=PH * lk, amph_h=K_AMPH * H_PERSON * lk, goose=goose, oars=oars)
    l2 = O.lay(2, 'Rigging')
    for i in range(poles):
        u = -L * 0.1 + L * 0.3 * i
        side = 1 if i % 2 else -1
        a = F.p(u, side * B * 0.42, H + 0.9 * PH * lk * 0.62)
        b = F.p(u - L * 0.18, side * B * 0.95, -0.6)
        seg_box(l2, 'wood_dk', a, b, 0.03 * B)
        person(O.lay(6, 'CrewCargo'), *F.p(u, side * B * 0.3)[:2], H * 0.9, PH * lk, seed + 30 + i)
    O.finish()
    return O


# ───────────────────────── 앵커(D11): 숨긴 Empty, 보이는 면 위 3D 점 ─────────────────────────
VIEW = Vector((1.0, -1.0, 1.0)).normalized()        # 카메라 쪽(−FWD)


ANCHOR_OWNER = {'ANCHOR_L6_label': 'COAST_PortusClaudius_root', 'ANCHOR_L6_c2': 'COAST_PortusClaudius_root', 'ANCHOR_L8_label': 'COAST_HadrianMausoleum_root'}


def put_anchor(ctx, name, world):
    ob = bpy.data.objects.get(name)
    if ob is not None:
        bpy.data.objects.remove(ob, do_unlink=True)
    ob = bpy.data.objects.new(name, None)
    ctx['coll'].objects.link(ob)
    ob.location = Vector(world); ob.empty_display_type = 'SPHERE'; ob.empty_display_size = 0.6
    ob.hide_render = True
    owner = bpy.data.objects.get(ANCHOR_OWNER.get(name, ''))           # b5: sil.json on_sil 판정이 되게 대상 루트 자식으로(월드 자리 유지)
    if owner is not None:
        bpy.context.view_layer.update()
        ob.parent = owner; ob.matrix_parent_inverse = owner.matrix_world.inverted()
    sx, sy = R.scr(Vector(world))
    return {'name': name, 'world': [round(v, 3) for v in world], 'screen': [round(sx, 2), round(sy, 2)]}


def visible_point(obs, tx, ty=None, mode='top_y', tol=0.35, need_up=False):
    """메시들의 카메라 쪽 면 점 중 화면 x≈tx(±tol)에서 가장 위(mode='top_y') 또는 (tx, ty)에 가장 가까운(mode='near') 점(가려짐은 ray_cast로 거른다)"""
    dg = bpy.context.evaluated_depsgraph_get()
    cuts = [o for o in bpy.data.objects if o.name.startswith('X_CUT_Coast')]
    hid = [(o, o.hide_viewport) for o in cuts]
    for o, _ in hid:
        o.hide_viewport = True
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    best = None
    try:
        for ob in obs:
            if ob.type != 'MESH' or ob.hide_render:
                continue
            mw = ob.matrix_world; nm = mw.to_3x3().inverted().transposed()
            me = ob.data
            for p in me.polygons:
                n = (nm @ p.normal).normalized()
                if n.dot(VIEW) < 0.15 or (need_up and n.z < 0.7):
                    continue
                pts = [mw @ p.center] + [mw @ (me.vertices[v].co * 0.6 + p.center * 0.4) for v in p.vertices]
                for w in pts:
                    sx, sy = R.scr(w)
                    if abs(sx - tx) > tol:
                        continue
                    key = sy if mode == 'top_y' else math.hypot(sx - tx, sy - ty)
                    if best is not None and key >= best[0]:
                        continue
                    hit = bpy.context.scene.ray_cast(dg, w + VIEW * 0.02, VIEW)
                    if hit[0]:
                        continue
                    best = (key, w.copy())
    finally:
        for o, h in hid:
            o.hide_viewport = h
    return None if best is None else best[1]


FWD_V = Vector((-1.0, 1.0, -1.0)).normalized()      # 카메라가 보는 방향


def scan_down(tx, y0, y1, accept, step=0.05):
    """화면 x = tx를 y0 → y1로 내려가며 카메라 광선을 쏴, 처음 맞는 오브젝트가 accept(ob)인 첫 점(깃대가 위에서 내려와 처음 닿는 면)"""
    cuts = [o for o in bpy.data.objects if o.name.startswith('X_CUT_')]
    hid = [(o, o.hide_viewport) for o in cuts]
    for o, _ in hid:
        o.hide_viewport = True
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    try:
        y = y0
        while y <= y1:
            X, Y = R.to_plan(tx, y)
            p = R.P(X, Y, 0.0)
            hit = bpy.context.scene.ray_cast(dg, p - FWD_V * 3000.0, FWD_V)
            if hit[0] and accept(hit[4]):
                ob = hit[4]
                try:
                    me = ob.original.data
                    mat = me.materials[me.polygons[hit[3]].material_index].name
                except Exception:
                    mat = ''
                if not any(t in mat for t in ('foam', 'water', 'fall')):
                    return hit[1].copy()
            y += step
    finally:
        for o, h in hid:
            o.hide_viewport = h
    return None


def build_anchors(ctx, objs):
    out = []
    # L6_label: 외항 방파제(팔 B) 바깥 면 위, 화면 x = 라벨 대상점 x, 윗면 1mm 아래(Z −1)
    cx, cy = BAS_C[0], -BAS_C[1]
    tx = T_L6[0]
    best = None
    for th10 in range(0, 900):
        th = th10 * 0.1
        X, Y = polar(BAS_C, R_OUT + DEC, th)
        sx, _ = R.to_screen(X, Y, -1.0)
        if best is None or abs(sx - tx) < best[0]:
            best = (abs(sx - tx), X, Y)
    out.append(put_anchor(ctx, 'ANCHOR_L6_label', (best[1], -best[2], -1.0)))
    if T_C2 is None:                                                 # 20:25 d5: C2 표지 폐기 → 앵커 지움
        old = bpy.data.objects.get('ANCHOR_L6_c2')
        if old is not None:
            bpy.data.objects.remove(old, do_unlink=True)
    else:
        # L6_c2: 외항 방파제 윗면(바깥 모서리 밝은 띠) 위, 화면 x = C2 지시선 x
        tx = T_C2[0]; best = None
        for th10 in range(-900, 0):
            th = th10 * 0.1
            X, Y = polar(BAS_C, R_OUT - 0.02, th)
            sx, sy = R.to_screen(X, Y, MOLE_TOP + 0.12 + DEC)
            if best is None or abs(sx - tx) + 0.02 * abs(sy - T_C2[1]) < best[0]:
                best = (abs(sx - tx) + 0.02 * abs(sy - T_C2[1]), X, Y)
        out.append(put_anchor(ctx, 'ANCHOR_L6_c2', (best[1], -best[2], MOLE_TOP + 0.12 + DEC)))
    # L8_label: 기단 윗면(원통 오른쪽 앞) — spec target_pt를 기단 윗면 높이로 되돌린 평면점
    X, Y = R.to_plan(T_L8[0], T_L8[1] + MZ_H)
    zl8 = MZ_H * MZ_SCALE                                            # 20:01 d5: 영묘 배율 뒤 기단 윗면
    X, Y = R.to_plan(T_L8[0], T_L8[1] + zl8)
    out.append(put_anchor(ctx, 'ANCHOR_L8_label', (X, -Y, zl8)))
    # BARGE1_label: 바지선 1 갑판(깃대 x = 라벨 블록 왼쪽 변 + 1, 위에서 내려와 처음 닿는 선체·짐칸·뱃전 면)
    def deck_of(prefix):
        return lambda ob: ob is not None and ob.name.startswith(prefix) and any(t in ob.name for t in ('_L0_Hulls', '_L1_Holds', '_L5_Gunwale', '_L6_CrewCargo'))
    O = objs.get('Barge1')
    if O is not None:
        bx = BOX_BARGE1
        tx = min(max(BOX_BARGE_LAB[0] + 1.0, bx[0] + 2.0), bx[2] - 2.0)
        w = scan_down(tx, bx[1], bx[3], deck_of('COAST_Barge1_'))
        if w is not None:
            out.append(put_anchor(ctx, 'ANCHOR_BARGE1_label', tuple(w)))
    # ASH_label: 화산재 운반선 선체 접점(깃대 x 144.25에서 위에서 내려와 처음 닿는 선체·뱃전 점)
    O = objs.get('AshShip')
    if O is not None:
        bx = BOX_ASH
        tx = min(max(T_ASH[0], bx[0] + 2.0), bx[2] - 1.0)
        w = None
        for k in range(16):                      # 깃대 x에서 왼쪽으로 0.25mm씩: 선체가 처음 닿는 가장 가까운 x
            w = scan_down(tx - 0.25 * k, bx[1], bx[3], deck_of('COAST_AshShip_'))
            if w is not None:
                break
        if w is not None:
            out.append(put_anchor(ctx, 'ANCHOR_ASH_label', tuple(w)))
    # EMP_label: 하역장 태그 아래 변 가운데 x에서 가장 위 지붕 면
    O = objs.get('TiberEmporium')
    if O is not None:
        kids = [o for o in O.root.children_recursive if o.type == 'MESH' and ('Porticus' in o.name)]
        w = visible_point(kids, (BOX_EMP_TAG[0] + BOX_EMP_TAG[2]) / 2, mode='top_y')
        if w is not None:
            out.append(put_anchor(ctx, 'ANCHOR_EMP_label', tuple(w)))
    return out


# ───────────────────────── 짓기 ─────────────────────────
def audit(roots):
    """루트별 표현 레이어(L0~L6) 확인: 빈 메시 0, 층마다 1개 이상"""
    rep = {}
    for r in roots:
        kids = [o for o in r.children_recursive if o.type == 'MESH' and not o.hide_render]
        lay = {}
        for o in kids:
            m = re.search(r'_L(\d)_', o.name)
            if m and len(o.data.polygons) > 0:
                lay.setdefault(int(m.group(1)), 0)
                lay[int(m.group(1))] += 1
        miss = [n for n in range(7) if n not in lay]
        rep[r.name] = {'layers': sorted(lay), 'missing': miss, 'meshes': len(kids)}
    return rep


def _scaled_mausoleum(ctx):
    """20:01 d5: 영묘를 원통 중심(평면 MZ_C, Z 0 = spec draw_pivot) 둘레로 MZ_SCALE 배율. 다리 상판 남쪽 끝은 줄어든 기단 북쪽 변까지 늘인다"""
    global BR_Y
    O = build_mausoleum(ctx)
    s = MZ_SCALE
    if abs(s - 1.0) > 1e-6:
        cx, cy = MZ_C
        r = O.root
        r.scale = (s, s, s)
        r.location = Vector((cx * (1.0 - s), -cy * (1.0 - s), 0.0)) + Vector(r.location) * s
        bpy.context.view_layer.update()
        y_n = cy - (cy - MZ_Y[0]) * s
        BR_Y = (BR_Y[0], max(BR_Y[1], y_n))
    return O


HADRIAN_V2 = True     # 22:10·22:33 사용자(레퍼런스 user_hadrian_bridge): 풀 둔덕 + 축대 + 원형 신전(roma_mausoleum) · 3아치 돌다리(roma_bridge). 옛 영묘·다리 코드는 보관


class _Wrap:
    def __init__(self, root):
        self.root = root


def _mausoleum_v2(ctx):
    """d7 L8 plan으로 짓고, 원통 중심(MZ_C, Z 0) 둘레로 draw_scale(MZ_SCALE)배"""
    import roma_mausoleum as HM
    S = json.load(open(SPEC, encoding='utf-8'))
    L8 = next(L for L in S['core_map']['landmarks'] if L['id'] == 'L8')
    root, info = HM.build_spec(ctx['coll'], L8['plan'], '%s_HadrianMausoleum' % PKG)
    s = MZ_SCALE
    if abs(s - 1.0) > 1e-6:
        cx, cy = MZ_C
        root.scale = (s, s, s)
        root.location = Vector((cx * (1.0 - s), -cy * (1.0 - s), 0.0))
        bpy.context.view_layer.update()
    return _Wrap(root)


def _bridge_v2(ctx):
    """d7 bridge.spec: 축 평면 Y, 물길 canal_h6(평면 X 방향) 폭 12, 다리 자리 수면 −3(국소) · 하구 보(−3 → 디오라마 수면 −7)"""
    import os, roma_bridge as BR, roma_diorama as DI
    S = json.load(open(SPEC, encoding='utf-8'))
    bs = S['core_map']['bridge']['spec']
    wy0, wy1 = bs['water_Y']; W = wy1 - wy0; zw = float(bs.get('water_z_local', -3.0))
    BW = bs['deck_X'][1] - bs['deck_X'][0]
    E = float(bs.get('abutment', 4.0)); hump = float(bs.get('h', 3.0))
    L = BR.layout(W, zw, 0.0, BW, hump, 1.2, 0.0, E, 2.0)
    BC = None
    try:
        BC = json.load(open(os.path.join(os.path.dirname(SPEC), 'blender_changes.json'), encoding='utf-8'))
    except Exception:
        BC = None
    canal = next((c for c in (BC or {}).get('water_rects', []) if c.get('id') == 'canal_h6'), None)
    cx0, cx1 = canal['plan_X'] if canal else (380.0, 569.5)
    wp = [(cx0, wy0), (cx1, wy0), (cx1, wy1), (cx0, wy1)]
    X0 = float(bs['center_X']); Y0 = 0.5 * (wy0 + wy1)
    root = BR.build(ctx['coll'], X0, Y0, L, '%s_PonsAelius' % PKG, wp)
    import roma_pkg_ground as GR
    aw = GR.Acc()
    aw.face([GR.V(x, y, zw) for x, y in wp], BR.mats()['water'], (0, 0, 1))
    aw.obj('%s_PonsAelius_L0_CanalWater' % PKG, ctx['coll'], root)
    a2 = GR.Acc(); a6 = GR.Acc()                                                    # 하구 보: 운하 끝(평면 X cx1)의 돌 턱 + 떨어지는 물(−3 → −7)
    Mb = BR.mats()
    zlo = DI.WATER_Z
    a2.box(cx1 - 0.9, cx1, wy0, wy1, zlo - 0.2, zw + 0.12, Mb['stone'], Mb['stone'], sides='ES')
    a2.box(cx1 - 0.9, cx1 + 0.05, wy0, wy1, zw + 0.12, zw + 0.25, Mb['trim'], Mb['trim'], sides='ES')
    for k in range(6):
        y0 = wy0 + W * k / 6 + 0.15; y1 = wy0 + W * (k + 1) / 6 - 0.15
        a6.face([GR.V(cx1 + 0.02, y0, zw + 0.1), GR.V(cx1 + 0.02, y1, zw + 0.1), GR.V(cx1 + 0.4, y1, zlo + 0.05), GR.V(cx1 + 0.4, y0, zlo + 0.05)],
                Mb['foam'] if k % 2 else Mb['r_wave'], (1, 0, 0.5))
    a2.obj('%s_PonsAelius_L2_Weir' % PKG, ctx['coll'], root)
    a6.obj('%s_PonsAelius_L6_WeirFoam' % PKG, ctx['coll'], root)
    return _Wrap(root)


def build(only=None):
    """LM_Coast를 지우고 다시 짓는다. only = 오브젝트 이름 목록(시험용, 없으면 전부)"""
    S = json.load(open(SPEC, encoding='utf-8'))
    load_geo(S)
    GC = R.coll(COLL, R.coll('ROMA_MAP'))
    if only:
        for nm in only:
            r = bpy.data.objects.get('%s_%s_root' % (PKG, nm))
            if r is not None:
                kill_obj(r)
    else:
        R.clear_coll(COLL)
    M = mats()
    ctx = {'coll': GC, 'M': M}
    def sea_level(fn):                                                   # 00:25 HEX_SEA: 내항·운하를 디오라마 바다 높이로(배율 뒤 월드 z = DI.WATER_Z)
        def run():
            if not HEX_SEA:
                return fn()
            import roma_diorama as DI
            g = globals(); old = {k: g[k] for k in ('WATER_Z', 'RIVER_Z')}
            wz = DI.WATER_Z / (PORTUS_FIT['s'] if PORTUS_FIT else 1.0)
            g.update(WATER_Z=wz, RIVER_Z=wz + 0.06)
            try:
                return fn()
            finally:
                g.update(old)
        return run
    jobs = [
        ('PortusHex', sea_level(lambda: build_hex(ctx))),
        ('PortusCanals', sea_level(lambda: build_canals(ctx))),
        ('PortusClaudius', lambda: build_claudius(ctx)),
        ('PortusLighthouse', lambda: build_lighthouse(ctx)),
        ('HadrianMausoleum', lambda: (_mausoleum_v2(ctx) if HADRIAN_V2 else _scaled_mausoleum(ctx))),
        ('PonsAelius', lambda: (_bridge_v2(ctx) if HADRIAN_V2 else build_bridge(ctx))),
    ]
    if SHIPS:                     # 00:41 사용자: 항구 주위·강 위 로마 배(평면 좌표, 디오라마 바다 수면)
        jobs.append(('RomanShips', lambda: build_roman_ships(ctx)))
    if DECOR:                     # 16:14 core만: 배·하역장·가마·오스티아는 짓지 않는다
        jobs[5:5] = [('PortusShips', lambda: build_harbour_ships(ctx))]
        jobs += [
            ('TiberEmporium', lambda: build_emporium(ctx)),
            ('LimeKiln', lambda: fit_build(lambda lk: build_kiln(ctx, lk), safe_box(lambda lk: build_kiln(ctx, lk), BOX_KILN, 0.94, HERO_C, HERO_R + 0.3), 0.94)),
            ('Ostia', lambda: fit_build(lambda lk: build_ostia(ctx, lk), BOX_OSTIA, 0.96)),
            ('Barge1', lambda: fit_build(lambda lk: build_boat(ctx, 'Barge1', BOX_BARGE1, 180.0, 'barge', 21.0, 'lime', RIVER_Z, 24.0, 5.6, 1.2, 1.6, 3, 2, lk), BOX_BARGE1, 0.92)),
            ('Barge2', lambda: fit_build(lambda lk: build_boat(ctx, 'Barge2', BOX_BARGE2, 90.0, 'barge', 23.0, 'amph', RIVER_Z, 20.0, 5.0, 1.1, 1.6, 2, 1, lk), BOX_BARGE2, 0.92)),
            # 화산재 운반선: spec 상자 안, 오른쪽 변만 깃대 x + 0.8(고물이 깃대에 닿고, 오른쪽 라벨 글 블록과 2mm 이상)
            ('AshShip', lambda: fit_build(lambda lk: build_boat(ctx, 'AshShip', ASH_FIT, 160.0, 'merchant', 25.0, 'pozz', SEA_Z, 26.0, 6.4, 2.0, 2.0, 4, 0, lk, True, 0.0, False, False), ASH_FIT, 1.0)),
        ]
    rep = {}; objs = {}
    for name, fn in jobs:
        if only and name not in only:
            continue
        O = fn()
        objs[name] = O
        kids = [o for o in O.root.children_recursive if o.type == 'MESH' and not o.hide_render]
        rep[name] = {'screen': screen_of(kids), 'layers': sorted({int(m.group(1)) for m in (re.search(r'_L(\d)_', o.name) for o in kids) if m}),
                     'meshes': len(kids), 'faces': sum(len(o.data.polygons) for o in kids), 'fit_scale': round(getattr(O, 'fit_scale', 1.0), 3),
                     'person_h': getattr(O, 'person_h', H_PERSON), 'fit_box': getattr(O, 'fit_box', None)}
    if PORTUS_FIT:                                                       # b7: 포르투스 네 루트 배율(기준점 둘레) · 운하는 외항 쪽만 남긴다
        place_portus([n_ for n_ in objs if n_.startswith('Portus')])
    if not only:
        rep['_anchors'] = build_anchors(ctx, objs)
    return rep


def place_portus(names):
    """방금 지은 포르투스 루트(모델 좌표, 원점)를 PORTUS_FIT 배율·기준점으로 옮긴다. 운하는 canal_keep 밖 면과 운하 절단체를 지운다"""
    s_ = PORTUS_FIT['s']; pv = Vector((PORTUS_FIT['pivot'][0], -PORTUS_FIT['pivot'][1], 0.0))
    for nm in names:
        r = bpy.data.objects.get('%s_%s_root' % (PKG, nm))
        if r is None:
            continue
        r.scale = (s_,) * 3
        r.location = pv + (Vector(r.location) - pv) * s_
    bpy.context.view_layer.update()
    cr = bpy.data.objects.get('%s_PortusCanals_root' % PKG)
    if cr is None or 'PortusCanals' not in names:
        return
    y0, y1, xm = PORTUS_FIT['canal_keep']
    for o in list(cr.children_recursive):
        if o.type != 'MESH':
            continue
        if o.name.startswith('X_CUT_'):
            me = o.data; bpy.data.objects.remove(o, do_unlink=True); bpy.data.meshes.remove(me); continue
        bm = bmesh.new(); bm.from_mesh(o.data)
        mw = o.matrix_world
        kill = [f for f in bm.faces if not (y0 <= -(mw @ f.calc_center_median()).y <= y1 and (mw @ f.calc_center_median()).x <= xm)]
        bmesh.ops.delete(bm, geom=kill, context='FACES')
        bm.to_mesh(o.data); bm.free(); o.data.update()
