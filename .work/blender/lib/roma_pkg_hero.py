# roma_pkg_hero — 콜로세움 히어로 + 히어로 군(인물 무리·노점·수레·길 연장) + 네로 거상 받침 + 기초 공사장. 담당: hero
# 사용자 결정(최신 우선, 설계 기준선 8절 · 와이어프레임 기준선 1절 · 지침 4절)
#   16:14 core 정보 오브젝트만: 콜로세움 건물(기단 계단 포함)과 네로 거상 받침(+ 자기 마당)만 짓는다. 인물 무리·노점·수레·공사장·
#         청동 거상(복원 추정)·경기장 관람객·광장 남은 조각·길 연장(HERO_Approach)·둘레 땅(HERO_Life)은 짓지 않는다(DECOR = False, 코드는 보관).
#         둘레 땅 결은 ground 땅 판 표현 층(L3~L6)이 맡는다
#   13:35 광장이 빠진 자리(예약 반지름 안)는 집·나무·밭으로 채우지 않는다: 땅색 바탕에 L3 흙 얼룩·L6 풀 포기만 드문드문(Core 실루엣이 땅 위에서 또렷)
#   13:33 판석 광장 제거: 'plaza' 단계·HERO_Plaza_root(판석 원판·경계석·문 앞 포장·닳은 판석 덮개)를 짓지 않는다(stage_plaza는 보관).
#         남기는 것 = 콜로세움 기단 계단 2단·인물 무리·노점·네로 받침·공사장(모두 땅 Z 0 위). 길 R1·R4·R7은 기단 발치까지 판석 길로 잇는다
#   12:49 'LocalBanana와 같은 주변 조경' 철회: 기둥 폐허·쓰러진 토막·단칸 아치·벽돌 담·작은 신전·열주·6주 신전 앞면·포장 고리·판석 갈래길·
#         노점 배치를 옮겨 오지 않는다(그 부품 코드는 맨 아래 '보관' 절에 두고 build()에서 부르지 않는다).
#         둘레는 승인 설계의 히어로 군이다: 광장 포장, 기초 공사장(거푸집·일꾼·재료 더미), 인물 무리, 네로 거상 받침, 문(아피아 가도·하역장 길·다리 길),
#         둘레 시내 지붕(ground)과 나무. 콜로세움 본체의 방향·부서진 정도·보이는 면·비례·LocalBanana급 디테일은 그대로다.
#   06:06 팔각 받침 없음: 콜로세움과 광장이 지도 땅(Z 0) 위에 바로 놓인다. 받침·옆면·지층·앞 변 절개 오브젝트는 0개다.
#   05:48 벡터 일러스트: 조명·AO·그림자·Principled 0. 면 톤은 ISO_TONE만, 모서리는 L5 하이라이트 띠(면색 명도 +10~15%), L7 외곽선 없음.
# 오브젝트(루트 → 레이어 메시 {PKG}_{Obj}_L{n}_{part}, 모든 루트에 L0~L6):
#   HERO_root(히어로 군 = 콜로세움 건물 + 인물·노점·공사장·네로, 위계 측정 단위)
#     ─ HERO_Colosseum_root · HERO_Life_root(인물·노점·수레·흙 얼룩·풀 포기) · HERO_NeroBase_root(받침) · HERO_NeroColossus_root(청동 거상, 추정)
#     · HERO_NeroYard_root(받침 둘레 포장 마당) · HERO_Worksite_root(기초 공사장)   ← 월드 자리는 그대로 두고 부모만 HERO_root
#   HERO_Approach_root(길 R1·R4·R7 연장: 문 선 → 기단 발치. HERO_root 밖 — 위계 측정에 납작한 길을 넣지 않는다)
#   ANCHOR_*(숨긴 Empty: 정보 층 지시선·라벨 끝, 보이는 면 위 3D 점) · X_CUT_HeroPit(숨긴 절단체: ground가 하이포게움 자리 땅을 Z −4.0까지 판다)
# 높이(D13): 땅 0 · 흙 얼룩(L3·L5) 0.05 · 노점 흙 마당 0.10 · 노점 밑 그늘 0.15 · 길 판 윗면 0.30(ground ROAD_Z와 같다) · 연석 0.25~0.48
#   겹칠 수 있는 평면끼리 Z 차 ≥ 0.05
# 다시 짓기: build() 한 번 또는 build(stage) 단계별(각 90초 안): 'colo_outer' → 'colo_inner' → 'grounds' → 'nero' → 'worksite' → 'anchors'
#   ('plaza'를 주면 'grounds'로 바꿔 짓는다)
import bpy, bmesh, math, json, colorsys
import numpy as np
from mathutils import Vector, Matrix
import roma_kit as R, roma_flat as FL, roma_geo as G, roma_colo as C, roma_colo_in as CI, roma_layers as LY

COLL = 'HERO_Colosseum'
SPEC_PATH = '/Users/um-yunsang/roman-concrete-private-refs/.work/design/current/out/spec.json'
C30 = math.cos(math.radians(30.0))

# ── 기획 결정(D2~D8) 상수: spec(d5)에 같은 열쇠가 있으면 spec 값을 쓴다 ──
D_HERO_PLAN = (462.34, 173.66)       # 조경(히어로 군) 중심 평면 = 화면 (250, 318)
D_COLO_OFF = (-15.8, -11.8)          # 조경 중심 → 외곽 타원 중심(평면). 타원 중심 평면 (446.54, 161.86) = 화면 (246.5, 304.2)
D_RES_R = 90.0                       # 예약 반지름(평면). 다른 패키지는 이 안에 아무것도 두지 않는다
D_NERO_PLAN = (327.0, 113.4)         # 네로 거상 받침 중심(spec nero_colossus.plan_center)
D_NERO_BASE = (8.3, 3.4)             # 받침 한 변·높이(16:25 레퍼런스: 넓고 낮은 받침 2.4:1. d4 5.0 → 3.4, 화면 받침 위 변 약 212.7)
D_NERO_TOP = 20.0                    # 거상 관 꼭대기 Z(화면 y 200.2)
D_NERO_YARD = 14.0                   # 받침 둘레 포장 마당 한 변(화면 [172, 196, 198, 228] 안)
D_WORKSITE_PLAN = (519.71, 260.29)   # 공사장 지역 원점(정보 층 draw_worksite와 같다) → ⑥ 지시선 끝 = 지역 (6.5, 9.0, 2.0)
D_R7_NORTH_Y = 250.4                 # 다리 길 R7 북쪽 끝(평면 Y, D3)
H_PERSON = 4.9                       # 사람 키(화면 mm, 발~머리, 히어로 조경·공사장·네로 마당, D8)
DECOR = False                        # 16:14 사용자 결정: 꾸미기 소품(사람·노점·수레·공사장) 0. True로 돌리면 보관 코드를 다시 짓는다
COLOSSUS = True                      # 16:29 사용자 "청동 거상도 넣자": 넓고 낮은 대리석 받침 위에 거상(레퍼런스 user_nero_base 자세)
HERO_LABEL_PT = (269.97, 244.0)      # 콜로세움 라벨 지시선 끝(잠정) → 가장 가까운 외벽 윗면 점으로 맞춘다


def spec():
    try:
        with open(SPEC_PATH, encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print('hero: spec 읽기 실패 —', e)
        return {}


def dig(d, *ks, default=None):
    for k in ks:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return default
    return d


def cfg():
    """spec(current)과 기획 결정 상수를 합친 배치 값(평면 mm)"""
    S = spec(); cm = S.get('core_map', {})
    hero = cm.get('hero', {})
    land = hero.get('landscape') or {}
    colo = hero.get('colosseum') or {}
    c = {}
    c['hero_plan'] = tuple(land.get('center_plan', D_HERO_PLAN))
    oc = colo.get('ellipse_center_plan') or colo.get('center_plan')
    c['colo_off'] = (oc[0] - c['hero_plan'][0], oc[1] - c['hero_plan'][1]) if oc else D_COLO_OFF
    c['colo_scale'] = float(colo.get('draw_scale') or dig(colo, 'map_raw', 'draw_scale', default=1.0) or 1.0)   # 20:01 d5: 콜로세움 그림 1.35배(타원 중심 기준)
    c['res_r'] = float(land.get('reserve_r_plan', D_RES_R))
    nero = cm.get('nero_colossus') or {}
    c['nero_plan'] = tuple(nero.get('plan_center', D_NERO_PLAN))
    c['nero_base'] = (float(dig(nero, 'base_plan_size', default=D_NERO_BASE[0]) or D_NERO_BASE[0]),
                      float(dig(nero, 'base_h', default=D_NERO_BASE[1]) or D_NERO_BASE[1]))
    c['nero_top'] = float(dig(nero, 'statue_top_z', default=D_NERO_TOP) or D_NERO_TOP)
    c['worksite_plan'] = tuple(dig(hero, 'worksite', 'blender_origin_plan', default=D_WORKSITE_PLAN) or D_WORKSITE_PLAN)
    rd = {}
    for r in cm.get('roads', []) or []:
        try:
            (X0, Y0), (X1, Y1) = r['plan_pts'][0], r['plan_pts'][-1]
            rd[r['id']] = dict(p0=(X0, Y0), p1=(X1, Y1), hw=r['w_screen_perp_mm'] / C30 / 2.0)
        except Exception:
            pass
    HX, HY = c['hero_plan']
    # R1 흰 중앙선 위상: ground는 길 낮은 끝(평면 Y 최소) + 1.5에서 9.5 간격으로 6.5 길이 줄을 긋는다 → 연장도 같은 위상
    c['r1_dash0'] = (min(rd['R1']['p0'][1], rd['R1']['p1'][1]) if 'R1' in rd else -15.9) + 1.5 - HY
    r1 = rd.get('R1', dict(p0=(483.1, 90.5), hw=9.24)); r4 = rd.get('R4', dict(p0=(462.34, 263.81), hw=5.77))
    r7 = rd.get('R7', dict(p0=(489.6, 263.81), hw=4.62)); r6 = rd.get('R6a', dict(p0=(483.1, 85.9), hw=4.62))
    c['r1'] = (r1['p0'][0] - HX, r1['p0'][1] - HY, r1['hw'])
    c['r4'] = (r4['p0'][0] - HX, r4['p0'][1] - HY, r4['hw'])
    c['r7'] = (r7['p0'][0] - HX, min(r7['p0'][1], D_R7_NORTH_Y) - HY, r7['hw'], r7['p0'][1] - HY)
    c['r6a_in'] = r6['p0'][1] + r6['hw'] - HY           # 메텔라 진입로 안쪽 변(평면 지역 Y)
    c['label_boxes'] = [sl['box'] for sl in dig(cm, 'labels', 'slots', default=[]) or [] if 'box' in sl]
    return c


CFG = None


def K():
    global CFG
    if CFG is None:
        CFG = cfg()
    return CFG


def pl(pX, pY, z=0.0):
    """평면 지역(pX, pY) → 루트 지역(Blender 축)"""
    return Vector((pX, -pY, z))


def plan_of_screen(x, y):
    """화면 mm(Z 0) → 히어로 군 지역 평면"""
    X, Y = R.to_plan(x, y)
    HX, HY = K()['hero_plan']
    return X - HX, Y - HY


def hls_hi(h, dl=0.12):
    """L5 하이라이트: 같은 색상·채도에서 명도 +dl(기본 12%)"""
    h = h.lstrip('#'); r, g, b = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    hh, ll, ss = colorsys.rgb_to_hls(r, g, b)
    r, g, b = colorsys.hls_to_rgb(hh, min(0.97, ll + dl), ss)
    return '#%02X%02X%02X' % (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def in_ell_screen(x, y, grow=0.0):
    """화면 점(Z 0)이 콜로세움 외곽 타원(바깥면 + grow mm) 안인가"""
    HX, HY = K()['hero_plan']; ox, oy = K()['colo_off']
    cx, cy = R.to_screen(HX + ox, HY + oy)
    ax = (C.A + grow) * math.sqrt(2.0) * C30; ay = (C.B + grow) * math.sqrt(2.0) * 0.5
    return ((x - cx) / ax) ** 2 + ((y - cy) / ay) ** 2 < 1.0


def rb(th):
    """광장 판석 바깥 경계 반지름(평면 방위 th°, D3): 84.5 + 3·sin(3θ+0.7) + 1.5·sin(7θ+0.2) ± 0.5 (79.5~89.5)"""
    t = math.radians(th)
    return 84.5 + 3.0 * math.sin(3 * t + 0.7) + 1.5 * math.sin(7 * t + 0.2) + 1.0 * (R.hash01(int(th * 10), 7) - 0.5)


# ───────────────────────── 재질 ─────────────────────────
def mats():
    P = FL.PAL
    g = bpy.data.materials.get
    def fl(n, h): return g(n) or FL.flat(n, h)            # 공용 이름(다른 패키지와 같이 쓰는 색): 없을 때만 만든다
    def bl(n, *a): return g(n) or FL.blocks(n, *a)
    def hf(n, h): return FL.flat(n, h)                    # hero 전용 이름: 매번 새 색으로 고친다
    def hb(n, *a): return FL.blocks(n, *a)
    slab = P.get('slab', '#D6CEBD')                      # 밝은 판석(트래버틴·석회암 포장). bglobal PAL 'slab'이 생기면 그 값을 쓴다
    ground = P.get('ground', '#E3CFA8')
    verge = FL.mix_hex(ground, '#C2A57C', 0.42)
    m = {
        'trav_blocks': bl('F_TravBlocks', P['trav_lo'], P['trav'], P['trav_hi'], P['joint'], 1.7, 0.85, 0.045),
        'trav': fl('F_trav', P['trav']), 'trav_hi': fl('F_trav_hi', P['trav_hi']),
        'trav_deep': fl('F_trav_deep', P['trav_deep']), 'trav_deeper': fl('F_trav_deeper', P['trav_deeper']),
        'tuff': fl('F_tuff', P['tuff']),
        'brick': bl('F_BrickBlocks', P['brick'], P['brick_hi'], P['brick'], P['brick_joint'], 0.75, 0.25, 0.05),
        'seat': bl('F_Seats', '#D9BE95', '#E3CBA5', '#CFAF84', '#B5946C', 2.4, 0.55, 0.06),
        'vault': bl('F_VaultTop', '#C9A783', '#BF9A74', '#D3B28D', '#A98463', 1.6, 0.9, 0.05),
        'wood': bl('F_WoodDeck', '#C49A68', '#B88D5C', '#CFA675', '#8E6640', 6.0, 0.55, 0.06),
        'wood_dk': fl('F_wood_dk', P['wood_dk']),
        'deep': fl('F_cavity', '#5B4130'),
        'hypo_mid': FL.flat('F_hero_hypoMid', '#6E4231'), 'hypo_deep': FL.flat('F_hero_hypoDeep', '#4C2F23'),
        'core': bl('F_RuinCore', '#B5704E', '#A9643F', '#C2805A', '#8F5236', 0.7, 0.24, 0.06),
        # hero 전용(F_hero_*)
        'trav_hero': hb('F_hero_travBlocks', '#CFA97E', '#D9BA90', '#E3C79F', '#AC8862', 1.7, 0.85, 0.045),   # 콜로세움 겉 트래버틴(조금 따뜻하고 짙게)
        'depth1': hf('F_hero_depth1', '#7E5D42'), 'depth2': hf('F_hero_depth2', '#553D2C'),                 # L1 아치 속·회랑 안(짙은 평면색)
        'damp': hf('F_hero_damp', '#B8946C'),
        'hi': hf('F_hero_hi', hls_hi('#D9BA90', 0.12)),              # 트래버틴 윗선(면색 명도 +12%)
        'hi_seat': hf('F_hero_hi_seat', hls_hi('#D9BE95', 0.11)),
        'stain': hf('F_hero_stain', '#B59673'),
        'vous1': hf('F_hero_vous1', '#CDAA7E'), 'vous2': hf('F_hero_vous2', '#E2C69C'),
        'hole': hf('F_hero_hole', '#6E523A'),
        'marble': hf('F_hero_marble', '#ECE3D1'), 'marble_lo': hf('F_hero_marble_lo', '#D3C3A6'),
        'marble_hi': hf('F_hero_marble_hi', hls_hi('#ECE3D1', 0.06)),
        'moss': hf('F_hero_moss', P['moss']), 'grass1': hf('F_hero_grass1', P['grass1']), 'grass2': hf('F_hero_grass2', P['grass2']),
        'grass3': hf('F_hero_grass3', P['grass3']), 'leafdot': hf('F_hero_leafdot', '#6F7D3B'),
        'dirt': hf('F_hero_dirt', '#D2B88E'), 'soil': hf('F_hero_soil', P['soil']), 'soil_dk': hf('F_hero_soil_dk', P['soil_dk']),
        'verge': hf('F_hero_verge', verge), 'verge_dk': hf('F_hero_verge_dk', FL.shade(verge, 0.9)),
        # 광장 판석(PAL 'slab' 한 값에서 무늬 색을 만든다: ground 길·coast와 같은 판석색)
        'slab': hf('F_hero_slab', slab),
        'slab_blocks': hb('F_hero_slabBlocks', FL.shade(slab, 0.96), slab, FL.shade(slab, 1.05), FL.shade(slab, 0.85), 2.6, 1.8, 0.07),
        'slab_ring': hb('F_hero_slabRing', FL.shade(slab, 1.05), FL.shade(slab, 0.97), slab, FL.shade(slab, 0.85), 2.2, 2.0, 0.07),
        'slab_wear': hf('F_hero_slabWear', FL.shade(slab, 0.9)),
        'path': hf('F_hero_path', FL.mix_hex(ground, '#A98A63', 0.40)), 'speck': hf('F_hero_speck', FL.mix_hex(ground, '#9C7E5A', 0.45)),
        'slab_hi': hf('F_hero_slab_hi', hls_hi(slab, 0.12)), 'slab_dk': hf('F_hero_slab_dk', FL.shade(slab, 0.72)),
        'kerb': hb('F_hero_kerb', '#DCCBA6', '#D3C19B', '#E4D5B3', '#B8A580', 1.7, 0.9, 0.08), 'kerb_hi': hf('F_hero_kerb_hi', hls_hi('#DCCBA6', 0.12)),
        'cippus': hf('F_hero_cippus', '#E4D1AE'), 'cippus_hi': hf('F_hero_cippus_hi', hls_hi('#E4D1AE', 0.11)),
        'rut': hf('F_hero_rut', FL.shade(slab, 0.66)),
        # 네로 받침·거상
        'brick_n': hb('F_hero_brickNero', '#B86F4C', '#C98260', '#AE6646', '#94563A', 0.62, 0.22, 0.05),
        'brick_hi': hf('F_hero_brick_hi', hls_hi('#B86F4C', 0.12)),
        'plates': hb('F_hero_plates', '#EAE2D2', '#E0D5C1', '#F1EBDF', '#C6B89E', 2.2, 1.4, 0.07),
        'bronze': hf('F_hero_bronze', '#9A7442'), 'bronze_hi': hf('F_hero_bronze_hi', hls_hi('#9A7442', 0.13)), 'bronze_dk': hf('F_hero_bronze_dk', '#5F4B2F'),
        'patina': hf('F_hero_patina', '#7FA08A'), 'gold': hf('F_hero_gold', '#D2A64E'),
        # 공사장
        'plank': hb('F_hero_plank', '#9C7046', '#A97B4F', '#B88A5C', '#76532F', 6.0, 0.8, 0.07),
        'wood_lt': hf('F_hero_wood_lt', hls_hi(P['wood'], 0.12)), 'wood_flat': hf('F_hero_wood', P['wood']),
        'lime': hf('F_hero_lime', '#F4F1E8'), 'ash': hf('F_hero_ash', '#96523C'), 'aggr': hf('F_hero_aggr', '#9C968C'),
        'lime_lo': hf('F_hero_lime_lo', '#DAD5C8'), 'ash_lo': hf('F_hero_ash_lo', '#7A412F'), 'aggr_lo': hf('F_hero_aggr_lo', '#7F7A71'),
        'concrete': hf('F_hero_concrete', '#BDB4A4'), 'concrete2': hf('F_hero_concrete2', '#968C7C'), 'concrete_wet': hf('F_hero_concreteWet', '#958C7E'),
        'layer_line': hf('F_hero_layerLine', '#6A6256'),
        'mortar': hf('F_hero_mortar', '#857D71'), 'pad': hf('F_hero_pad', '#D6BE96'), 'tuffchunk': hf('F_hero_tuffChunk', '#B39069'),
        # 히어로 군 땅(13:33·13:35): ground 땅 결·길과 같은 재질을 이름으로 함께 쓴다(문 선·예약 원 둘레 이음매 0). ground가 아직 없으면 같은 색 hero 재질
        'land_patch': g('F_ground_landPatch') or hf('F_hero_landPatch', '#DCC59C'),
        'land_patch2': g('F_ground_landPatch2') or hf('F_hero_landPatch2', '#F2E2BC'),
        'land_dot': g('F_ground_landDot') or hf('F_hero_landDot', '#CDB48B'),
        'trodden': hf('F_hero_trodden', FL.mix_hex(ground, '#C2A57C', 0.30)),
        'road': g('F_ground_basalt') or m_slab_blocks(slab),
        'road_side': g('F_ground_roadSide') or hf('F_hero_roadSide', '#8C8476'),
        'curb': g('F_ground_curb') or hb('F_hero_curb', '#DCCBA6', '#D3C19B', '#E4D5B3', '#B8A580', 1.7, 0.9, 0.08),
        'curb_hi': g('F_ground_curbHi') or hf('F_hero_curbHi', '#F2E7CF'),
        'road_rut': g('F_ground_rut') or hf('F_hero_roadRut', '#827C72'),
        'cline': g('F_ground_centerLine') or hf('F_hero_centerLine', '#F6F2E8'),
    }
    return m


def m_slab_blocks(slab):
    """ground 길 재질(F_ground_basalt)이 없을 때의 판석 길 재질(PAL 'slab' 한 값에서 무늬 색)"""
    return FL.blocks('F_hero_roadSlab', FL.shade(slab, 0.96), slab, FL.shade(slab, 1.05), FL.shade(slab, 0.85), 2.6, 1.8, 0.07)


PROTO_H = {}


def proto_h(name):
    """원형 키 = roma_props.proto_height(이름). 키 1.0 정규화 원형은 1.0이고, 사람은 발~머리(머리에 인 바구니 같은 짐은 넣지 않는다).
    b6: 예전에는 정점 최대 z를 써서 person1(바구니 꼭대기 1.109)이 4.42mm로 작아졌다(D17 4.6~5.2 밖)"""
    if name not in PROTO_H:
        import roma_props as RP
        PROTO_H[name] = float(RP.proto_height(name[2:] if name.startswith('P_') else name) or 1.0)
    return PROTO_H[name]


def protos():
    """roma_props 원형이 없으면 만든다(global 원형은 고치지 않는다)"""
    if not bpy.data.objects.get('P_person0'):
        import roma_props as RP
        RP.build_protos()
    PROTO_H.clear()


def person(O, k, x, y, z, rot, part='Person', h=H_PERSON, n=6):
    """사람 한 명(키 h mm, 원형 키로 배율을 정한다). 원형 person0~2를 돌려 쓴다"""
    pr = 'person%d' % (k % 3)
    hh = h * (0.96 + 0.08 * R.hash01(k, 83))
    return O.place(pr, x, y, z, hh / proto_h(pr), rot, n, part)


def new_faces(bm, fn, mi):
    """fn()이 새로 만든 면에만 재질 번호 mi를 준다"""
    before = set(bm.faces)
    fn()
    for f in bm.faces:
        if f not in before:
            f.material_index = mi


def life_ring(O, m, cx, cy, rx, ry, n, seed, z=0.0, s=0.7):
    """L6 오브젝트 둘레 풀 포기"""
    b6 = O.bm(6, 'Grass', [m['grass2'], m['grass1'], m['moss']])
    for j in range(n):
        a = 2 * math.pi * (j + 0.5 * R.hash01(seed, j)) / n
        rr = 1.0 + 0.25 * R.hash01(seed, j, 1)
        LY.tuft(b6, cx + rx * rr * math.cos(a), cy + ry * rr * math.sin(a), z, s * (0.7 + 0.6 * R.hash01(seed, j, 2)), seed * 13 + j, j % 2)
    return b6


# ───────────────────────── 콜로세움 ─────────────────────────
def colo_root(HC):
    return bpy.data.objects.get('HERO_Colosseum_root')


def apply_colo_scale():
    """d5 draw_scale: 콜로세움 루트를 외곽 타원 중심(지역 CX, CY, Z 0) 둘레로 균일 배율(화면 그림이 그 중심 둘레로 같은 배율)"""
    r = bpy.data.objects.get('HERO_Colosseum_root')
    s = K().get('colo_scale', 1.0)
    if r is None:
        return
    ox, oy = K()['colo_off']
    cx, cy = ox, -oy
    r.scale = (s, s, s)
    r.location = (cx * (1.0 - s), cy * (1.0 - s), 0.0)
    bpy.context.view_layer.update()


def build_pit_cutter(HC, root, m):
    """경기장 왼쪽(u < −2.0) 하이포게움 구덩이 절단체(숨김). ground가 땅 판을 Z −4.0까지 판다"""
    a = C.A - CI.DP1 + 0.05; b = C.B - CI.DP1 + 0.05
    t0 = math.acos(max(-1.0, min(1.0, CI.U_SPLIT / a)))
    pit = [(a * math.cos(t0 + (2 * math.pi - 2 * t0) * k / 64), b * math.sin(t0 + (2 * math.pi - 2 * t0) * k / 64)) for k in range(65)]
    bm = bmesh.new()
    lo = [bm.verts.new(CI.arena_uv(u, v, CI.Z_PIT + 0.02)) for u, v in pit]
    hi = [bm.verts.new(CI.arena_uv(u, v, 1.0)) for u, v in pit]
    bm.faces.new(lo[::-1]); bm.faces.new(hi)
    for k in range(len(pit)):
        bm.faces.new([lo[k], lo[(k + 1) % len(pit)], hi[(k + 1) % len(pit)], hi[k]])
    cut = R.bm_to_obj(bm, 'X_CUT_HeroPit', m['trav_deep'], HC, root)
    cut.hide_render = True; cut.display_type = 'WIRE'
    return cut


def special_bay(i):
    return len(C.bay_profile(i)) > 1


def build_ruin_layer(HC, root, m, ow):
    """L4: 깨진 윗면 = 벽돌 속살색, 무너진 윗선 위 돌 블록·잔해(칸 안 계단 칸 = 경사 부벽·수직 절단은 깔끔한 윗면으로 둔다)"""
    me = ow.data
    if m['core'].name not in [x.name for x in me.materials]:
        me.materials.append(m['core'])
    ci = [x.name for x in me.materials].index(m['core'].name)
    n = len(me.polygons)
    cen = np.empty(n * 3, np.float32); me.polygons.foreach_get('center', cen); cen = cen.reshape(-1, 3)
    nor = np.empty(n * 3, np.float32); me.polygons.foreach_get('normal', nor); nor = nor.reshape(-1, 3)
    mi = np.empty(n, np.int32); me.polygons.foreach_get('material_index', mi)
    levels = np.array([0.0] + [s['z1'] for s in C.ST] + [s['ob'] for s in C.ST if s['ob']])
    near_level = np.min(np.abs(cen[:, 2][:, None] - levels[None, :]), axis=1) < 0.12
    caps = (nor[:, 2] > 0.5) & (~near_level)
    mi[caps] = ci; me.polygons.foreach_set('material_index', mi); me.update()
    rub = C.Acc()
    for i in range(C.NB):
        sc = (i + 0.5) * C.W; th = C.E.az(sc)
        segs = C.bay_profile(i)
        # 바깥 고리: 무너진 토막마다 실제 윗선(기울기 포함) 위에 돌 블록
        for j0, (xa, xb, h) in enumerate(segs):
            ks = [k for k, s in enumerate(C.ST) if s['z0'] < h < s['z1'] - 0.05]
            if not ks or (C.ST[ks[0]]['ob'] is None and len(segs) > 1):
                continue
            nb = max(1, int((xb - xa) / C.W * (2 + int(C.rnd(i, 30 + j0) * 3)) + 0.5))
            for j in range(nb):
                if C.rnd(i, 70 + j + 7 * j0) < 0.25:
                    continue
                x = xa + (xb - xa) * (j + 0.3 + 0.4 * C.rnd(i, 40 + j + 7 * j0)) / nb
                z = C.wall_top(i, x)
                w = min(0.7 + 1.1 * C.rnd(i, 50 + j), 0.9 * (xb - xa)); hh = 0.45 + 0.5 * C.rnd(i, 60 + j)
                bm = bmesh.new()
                C.box(bm, x - w / 2, x + w / 2, 0.15 * C.rnd(i, 80 + j) - 0.1, C.T1 - 0.1 * C.rnd(i, 90 + j), z - 0.35, z - 0.35 + hh)
                if C.rnd(i, 95 + j) > 0.55:
                    w2 = w * 0.6
                    C.box(bm, x - w2 / 2 + 0.2, x + w2 / 2 + 0.2, 0.2, C.T1 - 0.25, z - 0.35 + hh, z - 0.35 + hh * 1.8)
                bm.verts.index_update(); rub.add_bm(bm, sc, 0.0, 0); bm.free()
        for ring, (Hf, d0, tw, kk0, tilt) in enumerate(((C.h1, 0.0, C.T1, 0, 14.0), (C.h2, C.D2, C.T2, 101, 20.0))):
            if ring == 0:
                continue
            H = Hf(th, i)
            for k, s in enumerate(C.ST if ring == 0 else C.ST[:3]):
                if s['z0'] >= H - 0.2:
                    break
                if not (H < s['z1'] - 0.05):
                    continue
                a = math.radians((C.rnd(i * 4 + k + kk0, 9) * 2 - 1) * tilt)
                nb = 2 + int(C.rnd(i, 30 + k) * 3)
                for j in range(nb):
                    if C.rnd(i, 70 + j) < 0.25:
                        continue
                    x = -C.W / 2 + C.W * (j + 0.3 + 0.4 * C.rnd(i, 40 + j)) / nb
                    z = H - math.tan(a) * x
                    w = 0.7 + 1.1 * C.rnd(i, 50 + j); hh = 0.45 + 0.5 * C.rnd(i, 60 + j)
                    bm = bmesh.new()
                    C.box(bm, x - w / 2, x + w / 2, 0.15 * C.rnd(i, 80 + j) - 0.1, tw - 0.1 * C.rnd(i, 90 + j), z - 0.35, z - 0.35 + hh)
                    if C.rnd(i, 95 + j) > 0.55:
                        w2 = w * 0.6
                        C.box(bm, x - w2 / 2 + 0.2, x + w2 / 2 + 0.2, 0.2, tw - 0.25, z - 0.35 + hh, z - 0.35 + hh * 1.8)
                    bm.verts.index_update(); rub.add_bm(bm, sc, d0, 0); bm.free()
    return rub.obj('H_L4_RuinBlocks', [m['trav_hero']], HC, root)


def build_rubble(HC, root, m):
    """L4 잔해 더미: 무너진 정면(18~72°) 회랑 바닥과 경기장 앞 관람석 발치에 돌 블록 무더기"""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.verify()
    for i in range(C.NB):
        sc = (i + 0.5) * C.W; th = C.E.az(sc) % 360.0
        if not (14.0 <= th < 78.0):
            continue
        for j in range(5):
            d = C.T1 + 0.4 + (C.G1 - 0.8) * C.rnd(i, 600 + j)          # 바깥 회랑 바닥
            x = (C.rnd(i, 610 + j) - 0.5) * C.W * 0.9
            p = LY.ell_pt(sc + x, d, 0.0)
            w = 0.5 + 0.7 * C.rnd(i, 620 + j)
            LY.obox(bm, p.x, p.y, 0.1, w, w * (0.5 + 0.4 * C.rnd(i, 630 + j)), 0.3 + 0.45 * C.rnd(i, 640 + j), 360.0 * C.rnd(i, 650 + j),
                    j % 3, (12.0 * (C.rnd(i, 660 + j) - 0.5), 12.0 * (C.rnd(i, 670 + j) - 0.5)))
        for j in range(3):
            d = C.D2 + C.T2 + 0.3 + 3.0 * C.rnd(i, 700 + j)                 # 둘째 고리 안쪽(셋째 고리 사이)
            x = (C.rnd(i, 710 + j) - 0.5) * C.W * 0.8
            p = LY.ell_pt(sc + x, d, 0.0)
            w = 0.6 + 0.6 * C.rnd(i, 720 + j)
            LY.obox(bm, p.x, p.y, 0.1, w, w * 0.7, 0.35 + 0.4 * C.rnd(i, 730 + j), 360.0 * C.rnd(i, 740 + j), (j + 1) % 3)
    return R.bm_to_obj(bm, 'H_L4_Rubble', [m['trav_hero'], m['core'], m['trav']], HC, root)


def build_colo_extra(HC, root, m):
    bm = bmesh.new()
    LY.ell_band(bm, 0.0, CI.DP0, 0.10, 0, 200)                       # 회랑·관람석 밑 바닥(트래버틴 판석)
    R.bm_to_obj(bm, 'H_L0_InnerFloor', [m['vault']], HC, root, False, False)
    # L6 이끼·풀: 깨진 윗면(바깥 고리·둘째 고리) 위
    bm = bmesh.new()
    levels = [0.0] + [s['z1'] for s in C.ST]
    for i in range(C.NB):
        sc = (i + 0.5) * C.W; th = C.E.az(sc)
        for ring, (Hf, d0, tw, kk0, tilt, sts) in enumerate(((C.h1, 0.0, C.T1, 0, 14.0, C.ST), (C.h2, C.D2, C.T2, 101, 20.0, C.ST[:3]))):
            H = Hf(th, i)
            if ring == 0:
                H = C.h_at(C.bay_profile(i), 0.0)
            if min(abs(H - lv) for lv in levels) < 0.12:
                continue
            ks = [kk for kk, s in enumerate(sts) if s['z0'] < H - 0.2]
            if not ks:
                continue
            a = math.radians((C.rnd(i * 4 + ks[-1] + kk0, 9) * 2 - 1) * tilt)
            for j in range(2):
                if C.rnd(i, 400 + 10 * ring + j) < 0.45:
                    continue
                x = (C.rnd(i, 410 + 10 * ring + j) - 0.5) * C.W * 0.7
                z = C.wall_top(i, x) if ring == 0 else H - math.tan(a) * x
                p = LY.ell_pt(sc + x, d0 + tw * 0.5, z)
                LY.lump(bm, p.x, p.y, z + 0.08, 0.5 + 0.25 * C.rnd(i, 420 + j), 0.5, 0.3, i * 7 + j + ring * 3, (i + j) % 2)
    R.bm_to_obj(bm, 'H_L6_Moss', [m['moss'], m['grass2']], HC, root, True)
    # L6 풀 포기: 기단 계단 발치(광장 쪽)·코니스 윗면 군데군데
    bm = bmesh.new()
    for i in range(C.NB):
        sc = (i + 0.5) * C.W; th = C.E.az(sc)
        H1 = max(h for (_, _, h) in C.bay_profile(i))
        for k, s in enumerate(C.ST[:3]):
            if H1 >= s['z1'] - 0.05 and C.rnd(i, 450 + k) > 0.62:
                x = (C.rnd(i, 460 + k) - 0.5) * C.W * 0.8
                p = LY.ell_pt(sc + x, -0.35, s['z1'])
                LY.tuft(bm, p.x, p.y, s['z1'], 0.35, 7500 + i * 3 + k, (i + k) % 2)
    R.bm_to_obj(bm, 'H_L6_Tufts', [m['grass2'], m['grass1']], HC, root)
    # L6 사람: 복원 나무 바닥 위 관람객(키 4.9) — 16:14 꾸미기 소품이라 짓지 않는다(DECOR)
    import roma_props as RP
    for k, (u, v) in enumerate(() if not DECOR else ((3.5, -5.0), (6.5, 1.5), (10.5, -2.5), (13.5, 3.5), (8.5, 6.0))):
        p = CI.arena_uv(u, v, CI.Z_FLOOR)
        pr = 'person%d' % (k % 3)
        RP.place(pr, p.x, p.y, p.z, H_PERSON * (0.96 + 0.08 * R.hash01(k, 83)) / proto_h(pr), 37.0 * k, HC,
                 name='H_L6_Person_%02d' % (k + 1), parent=root, local=True)


def rename_colo(root):
    """레거시 이름 H_* → HERO_Colosseum_*(이름 규칙 {PKG}_{Obj}_L{n}_{part})"""
    ren = {'H_Walls': 'H_L0_OuterWalls', 'H_Orders': 'H_L2_Orders', 'H_Vaults': 'H_L0_CorridorVaults'}
    for ob in list(root.children):
        nm = ren.get(ob.name, ob.name)
        if nm.startswith('H_L'):
            ob.name = 'HERO_Colosseum_' + nm[2:]
            if ob.data is not None and hasattr(ob.data, 'name') and ob.type == 'MESH' and ob.data.users == 1:
                ob.data.name = ob.name


def stage_colo_outer(HC, top, m):
    root = bpy.data.objects.new('HERO_Colosseum_root', None); HC.objects.link(root)
    root.parent = top; root.empty_display_size = 10
    ox, oy = K()['colo_off']
    C.CX, C.CY = ox, -oy                         # 타원 중심(Blender 지역 축)
    M = {'TRAV': m['trav_hero'], 'TRAV_IN': m['trav_hero'], 'TUFF': m['tuff'], 'HI': m['hi'], 'STAIN': m['stain'],
         'VOUS': (m['vous1'], m['vous2']), 'HOLE': m['hole'], 'DAMP': m['damp']}
    ow, od, ov = C.build_outer(HC, root, M)
    od.data.materials[0] = m['trav_hi']
    LY.depth_colors(ow, m['trav_hero'], m['depth1'], m['depth2'])
    build_ruin_layer(HC, root, m, ow)
    rename_colo(root)
    return root


def stage_colo_inner(HC, top, m):
    root = colo_root(HC)
    F = {'brick': m['brick'], 'tuff': m['tuff'], 'trav': m['trav'], 'trav_hi': m['trav_hi'], 'seat': m['seat'], 'vault': m['vault'],
         'trav_deeper': m['trav_deeper'], 'wood': m['wood'], 'wood_dk': m['wood_dk'], 'deep': m['deep'], 'hi': m['hi']}
    CI.build(HC, root, F)
    CI.build_arena(HC, root, F)
    hy = bpy.data.objects['H_L0_Hypogeum']                     # 재질 칸만 바꾼다(materials.clear()는 면 재질 번호를 0으로 되돌린다)
    for k_, mt in enumerate((m['brick'], m['hypo_mid'], m['hypo_deep'])):
        hy.data.materials[k_] = mt
    pf = bpy.data.objects['H_L0_PitFloor']; pf.data.materials[0] = m['hypo_deep']
    build_pit_cutter(HC, root, m)
    build_rubble(HC, root, m)
    build_colo_extra(HC, root, m)
    rename_colo(root)
    return root


# ───────────────────────── 광장(승인 설계 히어로 군) ─────────────────────────
def gates():
    k = K()
    x1, y1, hw1 = k['r1']
    x4, y4, hw4 = k['r4']
    x7, y7, hw7, y7_spec = k['r7']
    back_y = min(y1, k['r6a_in']) - 0.25                       # 아피아 가도·메텔라 진입로 안쪽 변 아래로 0.25 들어간다(빈틈 0)
    # 문 앞 포장: 길 시작점(spec plan_pts 첫 점)까지 판석을 늘인다. R7이 광장 안까지 연장되면(d5: 평면 Y 250.4) 길이 판석을 덮는다
    aprons = [(x7 - hw7 - 0.6, x7 + hw7 + 0.6, y7_spec + 0.3, 'R7'),
              (x4 - hw4 - 0.6, x4 + hw4 + 0.6, y4 + 0.3, 'R4')]
    return dict(back_y=back_y, back_x0=6.0, aprons=aprons, r1=(x1 - hw1, x1 + hw1, y1), r4=(x4, hw4, y4), r7=(x7, hw7, y7_spec))


def insert_apron(pts, x0, x1, yg):
    """광장 외곽(θ 증가, pY>0 쪽은 pX가 줄어든다)에 문 앞 포장 [x0, x1] × (경계 → yg)를 끼운다"""
    n = len(pts)
    def cross(xc):
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            if a[1] > 0 and b[1] > 0 and a[0] >= xc > b[0]:
                t = (a[0] - xc) / (a[0] - b[0])
                return i, a[1] + (b[1] - a[1]) * t
        return None, None
    i1, ya1 = cross(x1); i0, ya0 = cross(x0)
    if i1 is None or i0 is None or i0 < i1:
        return pts
    yg = max(yg, ya1, ya0)
    return pts[:i1 + 1] + [(x1, ya1), (x1, yg), (x0, yg), (x0, ya0)] + pts[i0 + 1:]


def plaza_outline(step=1.0):
    """광장 판석 외곽(평면 지역). 뒤-오른쪽은 아피아 가도·메텔라 진입로 안쪽 변에서 자르고, 앞-왼쪽 문 2곳은 길 시작까지 늘인다"""
    Gt = gates()
    pts = []
    for k in range(int(round(360.0 / step))):
        th = k * step; t = math.radians(th)
        r = rb(th)
        x, y = r * math.cos(t), r * math.sin(t)
        if x > Gt['back_x0'] and y < Gt['back_y']:
            y = Gt['back_y']
        pts.append((x, y))
    for (x0, x1, yg, _) in Gt['aprons']:
        pts = insert_apron(pts, x0, x1, yg)
    return pts


def outline_y_at(x):
    """판석 경계 rb(θ)와 세로선 pX = x의 교점 pY(앞쪽 반, θ 0~180°에서 pX가 줄어든다)"""
    lo, hi = 1.0, 179.0
    for _ in range(50):
        md = 0.5 * (lo + hi)
        if rb(md) * math.cos(math.radians(md)) > x:
            lo = md
        else:
            hi = md
    t = 0.5 * (lo + hi)
    return rb(t) * math.sin(math.radians(t))


def bl_loop(pts):
    return [(x, -y) for (x, y) in pts]


def ell_loop(d, n=160):
    return [tuple(LY.ell_pt(C.E.L * k / n, d, 0.0))[:2] for k in range(n)]


def on_apron(x, y, pad=0.0):
    for (x0, x1, yg, _) in gates()['aprons']:
        if x0 - pad <= x <= x1 + pad and y > 60.0:
            return True
    return False


def in_back_road(x, y, pad=0.0):
    Gt = gates()
    return x > Gt['back_x0'] - pad and y < Gt['back_y'] + pad


def r_out(th):
    """둘레 흙·풀 띠 바깥 반지름: 판석 경계 + 2.5 이상, 예약 반지름 90 안(첫 집 줄과의 빈 띠 ≤ 3mm)"""
    return min(89.6, max(rb(th) + 2.5, 88.4 + 0.9 * math.sin(math.radians(5 * th) + 1.3)))


def in_plaza(x, y, margin=1.0):
    """평면 지역 점이 판석 광장 안인가(콜로세움 기단 + margin 밖, 경계 − margin 안)"""
    r = math.hypot(x, y); th = math.degrees(math.atan2(y, x)) % 360.0
    if r > rb(th) - margin or in_back_road(x, y):
        return False
    sx, sy = R.to_screen(K()['hero_plan'][0] + x, K()['hero_plan'][1] + y)
    return not in_ell_screen(sx, sy, 0.9 + margin)


def screen_of(x, y, z=0.0):
    HX, HY = K()['hero_plan']
    return R.to_screen(HX + x, HY + y, z)


def blocked_label(sx, sy, top_h, pad=1.5):
    """키 top_h인 오브젝트가 라벨 글 상자와 겹치는가(화면 mm)"""
    for b in K()['label_boxes']:
        if sx + pad > b[0] and sx - pad < b[2] and sy > b[1] - pad and sy - top_h < b[3] + pad:
            return True
    return False


# 승인 설계 인물 무리(화면 mm, Z 0 발점). 4곳 + 흩어진 사람 = 22명
GROUPS = [('G1', (245.0, 351.0), 6, 4.2), ('G2', (277.0, 339.0), 3, 3.0), ('G3', (186.0, 322.0), 3, 3.0), ('G4', (197.0, 350.0), 3, 3.4)]
SCATTER = [(160.0, 318.0), (168.0, 340.0), (222.0, 362.0), (268.0, 368.0), (322.0, 326.0), (338.0, 312.0), (305.0, 345.0)]
STALLS = [((210.0, 364.0), 30.0), ((300.0, 359.0), -40.0)]          # 승인 설계 노점 2곳(흰·빨간 차양)
SCATTER2 = [(176.0, 304.0), (158.0, 332.0), (230.0, 344.0), (238.0, 372.0), (256.0, 343.0), (284.0, 360.0), (292.0, 336.0), (312.0, 352.0),
            (330.0, 342.0), (343.0, 322.0), (334.0, 300.0), (178.0, 342.0), (214.0, 350.0), (262.0, 376.0)]   # 흩어진 사람 더(광장 보이는 쪽)
TREES = [(80.0, 0.50, 'cypress0', 19.0), (82.6, 0.62, 'cypress2', 16.5), (99.0, 0.55, 'olive1', 14.5),
         (140.0, 0.55, 'cypress1', 17.5), (146.0, 0.5, 'cypress3', 15.5), (156.0, 0.6, 'olive2', 14.0),
         (171.0, 0.5, 'pine1', 14.5), (179.0, 0.45, 'cypress0', 20.0), (181.6, 0.62, 'cypress2', 17.0),
         (298.0, 0.5, 'cypress1', 20.0), (300.8, 0.62, 'cypress3', 17.0), (311.0, 0.45, 'cypress2', 18.5),
         (324.0, 0.55, 'cypress0', 18.0), (335.0, 0.5, 'cypress2', 19.0), (337.6, 0.62, 'cypress1', 16.0), (345.0, 0.55, 'olive0', 14.0)]


def stage_plaza(HC, top, m):
    """보관(13:33 판석 광장 제거): build()에서 부르지 않는다. 새 히어로 군 땅은 stage_grounds"""
    O = LY.Obj('HERO', 'Plaza', HC, top)
    Gt = gates()
    outline = plaza_outline()
    outer_bl = bl_loop(outline)
    # L0 덩어리: 판석 광장 바탕(0.10, 콜로세움 기단 밑으로 0.6 들어간 구멍) · 둘레 흙 띠(0.05)
    b0 = O.bm(0, 'Paving', [m['slab']], closed=False)
    LY.flat_poly(b0, [outer_bl, ell_loop(-0.6)], 0.10, 0)
    b0v = O.bm(0, 'Verge', [m['verge'], m['verge_dk']], closed=False)
    ths = [2.0 * k for k in range(180)]
    for k, th in enumerate(ths):
        th2 = th + 2.0
        q = []
        for a in (th, th2):
            t = math.radians(a)
            q.append((rb(a) - 0.4, r_out(a), t))
        mx = 0.5 * (q[0][1] + q[0][0]) * math.cos(q[0][2]); my = 0.5 * (q[0][1] + q[0][0]) * math.sin(q[0][2])
        if on_apron(mx, my, 1.0) or in_back_road(mx, my, 1.0):
            continue
        poly = [(q[0][0] * math.cos(q[0][2]), q[0][0] * math.sin(q[0][2])), (q[0][1] * math.cos(q[0][2]), q[0][1] * math.sin(q[0][2])),
                (q[1][1] * math.cos(q[1][2]), q[1][1] * math.sin(q[1][2])), (q[1][0] * math.cos(q[1][2]), q[1][0] * math.sin(q[1][2]))]
        poly = [(x, max(y, Gt['back_y']) if x > Gt['back_x0'] else y) for (x, y) in poly]
        LY.flat_poly(b0v, [bl_loop(poly)], 0.05, 0)
    # L1 깊이색: 빠진 판석(흙)·배수구(짙은 틈)·빠진 경계석 자리
    b1 = O.bm(1, 'Holes', [m['soil'], m['deep'], m['slab_dk']], closed=False)
    b1w = O.bm(1, 'Wear', [m['slab_wear']], closed=False)                             # 많이 밟혀 짙어진 판석(문 앞·노점 앞)
    wear_pts = [plan_of_screen(*p_) for p_ in ((186.0, 352.0), (214.0, 361.0), (300.0, 364.0), (248.0, 356.0), (281.0, 344.0),
                                              (166.0, 330.0), (330.0, 330.0), (232.0, 366.0), (190.0, 348.0), (320.0, 346.0), (262.0, 362.0))]
    for j, (x, y) in enumerate(wear_pts):
        if in_plaza(x, y, 2.0):
            LY.flat_poly(b1w, [[(px, -py) for px, py in LY.blob(x, y, 2.2 + 1.6 * R.hash01(j, 14), 1.3 + 0.8 * R.hash01(j, 15), 10, 40 + j, 0.25, 30.0 * j)]], 0.20, 0)
    nh = 0
    for j in range(500):
        if nh >= 10:
            break
        th = 360.0 * R.hash01(j, 11); r = 48.0 + 34.0 * R.hash01(j, 12)
        x, y = r * math.cos(math.radians(th)), r * math.sin(math.radians(th))
        if not in_plaza(x, y, 3.0) or on_apron(x, y, 3.0) or min(math.hypot(x - wx, y - wy) for (wx, wy) in wear_pts) < 7.0:
            continue
        sx_, sy_ = screen_of(x, y)
        if in_ell_screen(sx_, sy_, 12.5):
            continue
        nh += 1
        Yb = -y; rr_ = math.floor(Yb / 1.8); off_ = 1.3 if rr_ % 2 == 0 else 0.0  # 판석 한 장 자리: 벽돌 무늬 격자(2.6×1.8, 짝수 줄 반 칸 밀림)
        bx_ = math.floor((x + off_) / 2.6) * 2.6 - off_; by_ = rr_ * 1.8
        LY.flat_poly(b1, [[(bx_ + 0.04, by_ + 0.04), (bx_ + 2.56, by_ + 0.04), (bx_ + 2.56, by_ + 1.76), (bx_ + 0.04, by_ + 1.76)]], 0.20, 0)
    for az in (20.0, 65.0, 110.0, 160.0, 250.0, 300.0, 340.0):                      # 경계석 줄 바깥 배수구
        s = LY.ell_s_of_az(az)
        q = [tuple(LY.ell_pt(s + ds, d, 0.0))[:2] for ds, d in ((-1.3, -10.3), (1.3, -10.3), (1.3, -10.9), (-1.3, -10.9))]
        LY.flat_poly(b1, [q], 0.20, 1)
    # L2 부재: 경계석(cippi, 옛 트래버틴 포장 구역 끝) · 문 앞 연석
    b2 = O.bm(2, 'Cippi', [m['cippus']])
    b4 = O.bm(4, 'LooseStones', [m['slab_blocks'], m['cippus'], m['kerb']])
    b5 = O.bm(5, 'Highlights', [m['cippus_hi'], m['kerb_hi'], m['slab_hi']])
    for i in range(C.NB):
        p = LY.ell_pt((i + 0.25) * C.W, -9.5, 0.0)
        r_ = C.rnd(i, 500)
        if r_ < 0.16:                                                                # 빠진 경계석: 자리 구멍(L1)
            LY.flat_poly(b1, [[(p.x - 0.5, p.y - 0.5), (p.x + 0.5, p.y - 0.5), (p.x + 0.5, p.y + 0.5), (p.x - 0.5, p.y + 0.5)]], 0.20, 2)
            continue
        h = 2.4 + 0.3 * C.rnd(i, 501) if r_ > 0.3 else 1.1 + 0.4 * C.rnd(i, 502)    # 부러진 것은 낮다
        G.box(b2, p.x - 0.48, p.x + 0.48, p.y - 0.48, p.y + 0.48, 0.0, h - 0.18, 0)
        G.box(b2, p.x - 0.55, p.x + 0.55, p.y - 0.55, p.y + 0.55, 0.0, 0.32, 0)    # 밑동 턱
        if r_ > 0.3:
            G.cyl(b2, p.x, p.y, 0.5, h - 0.18, h, 10, 0, r_top=0.32)               # 둥근 머리
            G.cyl(b5, p.x, p.y, 0.33, h, h + 0.05, 10, 0)
        else:
            LY.obox(b4, p.x + 0.9, p.y - 0.6, 0.15, 0.9, 0.7, 0.45, 25.0 * i, 1, (10.0, 0.0))   # 부러진 머리 토막
            G.box(b5, p.x - 0.5, p.x + 0.5, p.y - 0.5, p.y + 0.5, h - 0.18, h - 0.13, 0)
    b2k = O.bm(2, 'Kerbs', [m['kerb']])
    for key in ('r7', 'r4'):                                                          # 문 앞 포장 양옆 연석(ground 길 연석 자리와 이어진다)
        xc, hw, yg = Gt[key]
        cw = 1.0 if hw > 6.0 else 0.7
        for (xa, xb) in ((xc - hw, xc - hw + cw), (xc + hw - cw, xc + hw)):
            ya = outline_y_at(0.5 * (xa + xb)) - 2.0
            if yg - ya < 1.0:                                                          # 길이 광장 안까지 들어오면 길 연석(ground)이 맡는다
                continue
            G.box(b2k, xa, xb, -yg, -ya, 0.0, 0.48, 0)
            G.box(b5, xa + 0.05, xb - 0.05, -yg, -ya, 0.48, 0.53, 1)
    xa, xb, yb = Gt['r1']                                                             # 아피아 가도 문: 길 연석이 광장 안 4mm까지 들어온다
    cw = 1.0
    for (x0_, x1_) in ((xa, xa + cw), (xb - cw, xb)):
        G.box(b2k, x0_, x1_, -yb - 4.0, -yb, 0.0, 0.48, 0)
        G.box(b5, x0_ + 0.05, x1_ - 0.05, -yb - 4.0, -yb, 0.48, 0.53, 1)
    # L3 표면 무늬: 옛 포장 구역(타원 따라 놓은 판석) · 바깥 광장(지도 축 판석)
    b3r = O.bm(3, 'PrecinctSlabs', [m['slab_ring']], closed=False)
    LY.ell_band(b3r, -0.6, -8.6, 0.15, 0, 200)
    b3 = O.bm(3, 'Slabs', [m['slab_blocks']], closed=False)
    LY.flat_poly(b3, [outer_bl, ell_loop(-8.6)], 0.15, 0)
    # L4 형태 디테일: 들뜬 판석·흩어진 돌(경계 밖으로 흩어져 지도에 녹아든다) · 문 앞 바퀴 자국
    for j in range(70):
        th = 360.0 * R.hash01(j, 21)
        r = rb(th) + (-1.5 + 5.0 * R.hash01(j, 22) ** 1.5)
        x, y = r * math.cos(math.radians(th)), r * math.sin(math.radians(th))
        if on_apron(x, y, 0.8) or in_back_road(x, y, 0.8) or r > 89.6:
            continue
        w = 0.9 + 0.8 * R.hash01(j, 23)
        z0 = 0.15 if r < rb(th) - 0.3 else 0.05
        LY.obox(b4, x, -y, z0, w, w * 0.7, 0.18 + 0.12 * R.hash01(j, 24), 360.0 * R.hash01(j, 25), 0)
    for j in range(30):
        th = 360.0 * R.hash01(j, 31); r = 45.0 + 38.0 * R.hash01(j, 32)
        x, y = r * math.cos(math.radians(th)), r * math.sin(math.radians(th))
        if not in_plaza(x, y, 2.5):
            continue
        w = 0.9 + 0.7 * R.hash01(j, 33)
        LY.obox(b4, x, -y, 0.15, w, w * 0.62, 0.12, 360.0 * R.hash01(j, 36), 0, (6.0 * (R.hash01(j, 37) - 0.5), 5.0 * (R.hash01(j, 38) - 0.5)))
    b4r = O.bm(4, 'Ruts', [m['rut']], closed=False)
    for (x0, x1, yg, nm) in Gt['aprons']:
        xm = 0.5 * (x0 + x1)
        y0_ = outline_y_at(xm) - 3.0
        if yg - y0_ < 2.0:
            continue
        for off in (-1.6, 1.6):
            LY.flat_poly(b4r, [[(xm + off - 0.12, -y0_), (xm + off + 0.12, -y0_), (xm + off + 0.12, -yg + 0.4), (xm + off - 0.12, -yg + 0.4)]], 0.20, 0)
    xa, xb, yb = Gt['r1']
    for off in (-3.2, 3.2):
        xm = 0.5 * (xa + xb) + off
        LY.flat_poly(b4r, [[(xm - 0.12, -Gt['back_y'] - 0.3), (xm + 0.12, -Gt['back_y'] - 0.3), (xm + 0.12, -Gt['back_y'] - 6.0), (xm - 0.12, -Gt['back_y'] - 6.0)]], 0.20, 0)
    # L5 하이라이트: 옛 포장 구역 바깥 경계 윗선(밝은 띠)
    b5r = O.bm(5, 'PrecinctLine', [m['slab_hi']], closed=False)
    LY.ell_band(b5r, -8.6, -8.9, 0.20, 0, 200)
    # L6 얼룩·식생·생활: 풀밭 조각·잎결(L3)·풀 포기·덤불·나무·사람·노점·암포라·수레
    b6l = O.bm(6, 'Lawn', [m['grass1'], m['grass2'], m['grass3']], closed=False)
    b3l = O.bm(3, 'LeafDots', [m['leafdot'], m['grass3']], closed=False)
    for k in range(64):
        th = 5.625 * k + 2.0 * R.hash01(k, 1)
        w = r_out(th) - rb(th)
        if w < 3.4:
            continue
        rr = rb(th) + 0.5 + w * 0.5
        x, y = rr * math.cos(math.radians(th)), rr * math.sin(math.radians(th))
        if on_apron(x, y, 2.0) or in_back_road(x, y, 2.0):
            continue
        rx = min(4.5, 1.6 + 3.0 * R.hash01(k, 2)); ry = min(w * 0.42, 2.6)
        bl = LY.blob(x, y, rx, ry, 14, k + 0.7, 0.22, th + 90.0)
        LY.flat_poly(b6l, [[(px, -py) for px, py in bl]], 0.15, k % 3)
        for j in range(int(rx * ry / 1.6)):
            a = 2 * math.pi * R.hash01(k, j, 3); q = math.sqrt(R.hash01(k, j, 4)) * 0.75
            cx_, cy_ = x + rx * q * math.cos(a), y + ry * q * math.sin(a)
            LY.flat_poly(b3l, [[(px, -py) for px, py in LY.blob(cx_, cy_, 0.42, 0.26, 6, k * 31 + j, 0.2, 40.0 * j)]], 0.20, j % 2)
    b3v = O.bm(3, 'VergeSpecks', [m['speck'], m['verge_dk']], closed=False)          # 흙 띠 점무늬(밟힌 흙·작은 자갈)
    for j in range(420):
        th = 360.0 * R.hash01(j, 121)
        r = rb(th) + 0.3 + (r_out(th) - rb(th) - 0.6) * R.hash01(j, 122)
        x, y = r * math.cos(math.radians(th)), r * math.sin(math.radians(th))
        if r_out(th) - rb(th) < 1.2 or on_apron(x, y, 0.5) or in_back_road(x, y, 0.5):
            continue
        LY.flat_poly(b3v, [[(px, -py) for px, py in LY.blob(x, y, 0.32 + 0.3 * R.hash01(j, 123), 0.2 + 0.15 * R.hash01(j, 124), 6, 5000 + j, 0.2, 60.0 * j)]], 0.10, j % 2)
    b6 = O.bm(6, 'Tufts', [m['grass2'], m['grass1'], m['moss']])
    for j in range(160):                                                            # 판석 경계·흙 띠
        th = 360.0 * R.hash01(j, 41)
        r = rb(th) - 0.4 + (r_out(th) - rb(th) + 0.4) * R.hash01(j, 42)
        x, y = r * math.cos(math.radians(th)), r * math.sin(math.radians(th))
        if on_apron(x, y, 0.5) or in_back_road(x, y, 0.5):
            continue
        z = 0.15 if r < rb(th) else 0.05
        LY.tuft(b6, x, -y, z, 0.38 + 0.32 * R.hash01(j, 43), j, j % 2, 3 if j % 3 else 2)
    nt = 0
    for j in range(900):                                                            # 판석 틈
        if nt >= 120:
            break
        th = 360.0 * R.hash01(j, 51); r = 40.0 + 48.0 * math.sqrt(R.hash01(j, 52))
        x, y = r * math.cos(math.radians(th)), r * math.sin(math.radians(th))
        if not in_plaza(x, y, 0.6):
            continue
        nt += 1
        LY.tuft(b6, x, -y, 0.15, 0.26 + 0.22 * R.hash01(j, 53), j + 1000, 2 if R.hash01(j, 54) > 0.8 else j % 2, 3 if j % 3 else 2)
    for j in range(120):                                                            # 콜로세움 기단 계단 발치
        s_ = C.E.L * R.hash01(j, 141)
        p = LY.ell_pt(s_, -0.95 - 0.25 * R.hash01(j, 142), 0.0)
        LY.tuft(b6, p.x, p.y, 0.15, 0.32 + 0.22 * R.hash01(j, 143), 7000 + j, j % 2)
    for i in range(C.NB):                                                           # 경계석 밑동
        if C.rnd(i, 500) < 0.16 or C.rnd(i, 505) < 0.5:
            continue
        p = LY.ell_pt((i + 0.25) * C.W, -9.5, 0.0)
        LY.tuft(b6, p.x + 0.55, p.y - 0.45, 0.15, 0.38, 2000 + i, i % 2)
    for k in range(40):                                                             # 덤불(흙 띠)
        th = 9.0 * k + 4.0 * R.hash01(k, 61)
        w = r_out(th) - rb(th)
        if w < 2.6 or R.hash01(k, 62) < 0.35:
            continue
        rr = rb(th) + w * (0.35 + 0.4 * R.hash01(k, 63))
        x, y = rr * math.cos(math.radians(th)), rr * math.sin(math.radians(th))
        sx, sy = screen_of(x, y)
        if on_apron(x, y, 2.5) or in_back_road(x, y, 2.5) or blocked_label(sx, sy, 3.0):
            continue
        O.place('bush%d' % (k % 4), x, -y, 0.05, 5.5 + 3.0 * R.hash01(k, 64), 360.0 * R.hash01(k, 65), 6, 'Bush')
    for (th, fr, pr, hgt) in TREES:                                                 # 둘레 나무(사이프러스 쌍·올리브·우산소나무)
        w = r_out(th) - rb(th)
        rr = rb(th) + max(1.2, w * fr)
        x, y = rr * math.cos(math.radians(th)), rr * math.sin(math.radians(th))
        if in_back_road(x, y, 1.5):
            y = Gt['back_y'] + 1.6
        sx, sy = screen_of(x, y)
        if blocked_label(sx, sy, hgt):
            continue
        O.place(pr, x, -y, 0.05, hgt / proto_h(pr), 360.0 * R.hash01(th, 66), 6, 'Tree')
    # 노점 2곳(흰·빨간 차양) + 암포라 무리 + 수레
    for k, ((sx, sy), rot) in enumerate(STALLS):
        x, y = plan_of_screen(sx, sy)
        O.place('stall', x, -y, 0.15, 6.6, rot, 6, 'Stall')
        for j in range(4):
            a = math.radians(rot) + math.pi * (0.9 + 0.35 * j); rr = 5.2 + 0.9 * (j % 2)
            O.place('amphora', x + rr * math.cos(a), -y + rr * math.sin(a), 0.15, 2.8 + 0.4 * R.hash01(k, j), 40.0 * j, 6, 'Amphora')
    cx_, cy_ = plan_of_screen(232.0, 368.0)
    O.place('cart', cx_, -cy_, 0.15, 7.3, -58.0, 6, 'Cart')
    for j in range(3):                                                              # 수레 옆 생석회 자루·통
        O.place('amphora', cx_ - 2.0 + 1.1 * j, -cy_ - 4.2 - 0.4 * j, 0.15, 2.6, 30.0 * j, 6, 'Amphora')
    # 인물 무리(키 4.9, 발점 간격 3.5~5)
    k = 0
    for (gid, (sx, sy), n, sp) in GROUPS:
        gx, gy = plan_of_screen(sx, sy)
        for j in range(n):
            a = 2 * math.pi * j / n + R.hash01(j, gx); rr = sp * (0.55 + 0.45 * (j % 2))
            x, y = gx + rr * math.cos(a), gy + rr * math.sin(a)
            person(O, k, x, -y, 0.15, 360.0 * R.hash01(k, 82)); k += 1
    for (sx, sy) in SCATTER + SCATTER2:
        x, y = plan_of_screen(sx, sy)
        if not in_plaza(x, y, 1.0):
            continue
        person(O, k, x, -y, 0.15, 360.0 * R.hash01(k, 82)); k += 1
    x4, hw4, y4 = gates()['r4']                                                     # 하역장 길 문 앞 수레(하역장에서 올라오는 짐)
    O.place('cart', x4 - 1.5, -(outline_y_at(x4) + 3.5), 0.15, 7.3, 90.0, 6, 'Cart')
    return O.done()


# ───────────────────────── 히어로 군 땅(13:33 광장 제거 · 13:35 예약 원 안 채우지 않기 · 16:08 표현 레이어 누적) ─────────────────────────
FOOT_G = 0.80                        # 길 끝 = 외곽 타원 + 0.80(기단 계단 돌출 0.75 바로 밖: 계단 윗면 0.30과 길 윗면 0.30이 겹치지 않는다)
Z_TROD, Z_GRAIN, Z_HOLLOW, Z_LIGHT, Z_RUT = 0.05, 0.10, 0.15, 0.20, 0.25   # 겹칠 수 있는 평면끼리 Z 차 0.05


def foot_y(x, side, g=FOOT_G):
    """평면 지역 세로선 pX = x와 (외곽 타원 + g)의 교점 pY. side −1 = 앞(pY 큰 쪽), +1 = 뒤. 닿지 않으면 None"""
    a, b = C.A + g, C.B + g
    cr, sr = C.E.cr, C.E.sr
    dx = x - C.CX
    A_ = sr * sr / a / a + cr * cr / b / b
    B_ = 2.0 * dx * (cr * sr / a / a - sr * cr / b / b)
    C_ = dx * dx * (cr * cr / a / a + sr * sr / b / b) - 1.0
    D = B_ * B_ - 4.0 * A_ * C_
    if D < 0.0:
        return None
    t = (-B_ + math.sqrt(D)) / (2.0 * A_) if side > 0 else (-B_ - math.sqrt(D)) / (2.0 * A_)
    return -(C.CY + t)                                            # Blender 지역 y → 평면 pY


def in_colo(x, y, g=0.0):
    """평면 지역 점이 (외곽 타원 + g) 안인가"""
    a, b = C.A + g, C.B + g
    px, py = x - C.CX, -y - C.CY
    u = C.E.cr * px + C.E.sr * py; v = -C.E.sr * px + C.E.cr * py
    return (u / a) ** 2 + (v / b) ** 2 < 1.0


def approaches():
    """길 연장 R1·R4·R7: (이름, 중심 x, 반폭, 문 선 y, 방향 side, 연석 폭, 길 윗면 Z). 문 선 = ground 길 시작(spec plan_pts 첫 점)"""
    k = K()
    x1, y1, hw1 = k['r1']; x4, y4, hw4 = k['r4']; x7, _, hw7, y7 = k['r7']
    out = []
    for (nm, xc, hw, yg, side) in (('R1', x1, hw1, y1, +1), ('R4', x4, hw4, y4, -1), ('R7', x7, hw7, y7, -1)):
        out.append(dict(id=nm, xc=xc, hw=hw, yg=yg, side=side, cw=1.0 if hw > 6.0 else 0.7, z=0.30))
    return out


def road_end(rd, x):
    """길 rd의 세로선 x에서 끝 pY(타원 발치). 타원 밖 x는 가장 가까운 닿는 x의 끝(접점)으로 자른다"""
    y = foot_y(x, rd['side'])
    if y is not None:
        return y
    lo, hi = rd['xc'] - rd['hw'], rd['xc'] + rd['hw']
    best = None
    for k in range(81):
        xx = lo + (hi - lo) * k / 80.0
        yy = foot_y(xx, rd['side'])
        if yy is not None and (best is None or abs(xx - x) < best[0]):
            best = (abs(xx - x), yy)
    return best[1] if best else rd['yg']


def road_poly(rd, xa, xb, n=24):
    """[xa, xb] 띠: 문 선 → 타원 발치(평면 지역 점 목록)"""
    yg = rd['yg']
    xs = [xa + (xb - xa) * k / n for k in range(n + 1)]
    ends = [road_end(rd, x) for x in xs]
    if rd['side'] < 0:              # 앞 문(R4·R7): 문 선 pY 큼 → 끝 pY 작음
        return [(xa, yg), (xb, yg)] + [(x, e) for x, e in reversed(list(zip(xs, ends)))]
    return [(xa, yg)] + [(x, e) for x, e in zip(xs, ends)] + [(xb, yg)]


def on_approach(x, y, pad=0.0):
    for rd in approaches():
        if rd['xc'] - rd['hw'] - pad <= x <= rd['xc'] + rd['hw'] + pad:
            e = road_end(rd, x)
            lo, hi = sorted((rd['yg'], e))
            if lo - pad <= y <= hi + pad:
                return True
    return False


def ground_free(x, y, pad=1.0, g=1.6):
    """예약 원 안 땅 점이 비어 있는가: 원 안(반지름 − pad) · 콜로세움 타원 + g 밖 · 길 연장 + pad 밖"""
    return math.hypot(x, y) < K()['res_r'] - pad and not in_colo(x, y, g) and not on_approach(x, y, pad)


def stage_approach(HC, top, m):
    """HERO_Approach_root: 길 R1·R4·R7을 문 선(ground 길 끝)에서 콜로세움 기단 발치까지 판석 길로 잇는다(연석 폭은 길 폭 그대로).
    HERO_root 밖(위계 측정에 납작한 길을 넣지 않는다). 지역 축 = 히어로 군 평면(Blender y = −pY)"""
    HX, HY = K()['hero_plan']
    O = LY.Obj('HERO', 'Approach', HC, None, loc=R.P(HX, HY, 0.0), rot=0.0)
    b0 = O.bm(0, 'Slab', [m['road'], m['road_side']])
    b1 = O.bm(1, 'Ruts', [m['road_rut']], closed=False)
    b2 = O.bm(2, 'Curbs', [m['curb']])
    b3 = O.bm(3, 'Pavers', [m['curb_hi'], m['road_side']], closed=False)
    b4 = O.bm(4, 'Detail', [m['cline'], m['curb'], m['road_side']])
    b5 = O.bm(5, 'CurbHighlight', [m['curb_hi']], closed=False)
    b6 = O.bm(6, 'Verge', [m['grass2'], m['grass1'], m['moss']])
    for rd in approaches():
        xc, hw, yg, z, cw = rd['xc'], rd['hw'], rd['yg'], rd['z'], rd['cw']
        xa, xb = xc - hw, xc + hw
        # L0 길 판(윗면 z + 보이는 동쪽 옆면)
        poly = road_poly(rd, xa, xb)
        LY.flat_poly(b0, [[(px, -py) for px, py in poly]], z, 0)
        ye = road_end(rd, xb)
        ya_, yb_ = sorted((yg, ye))
        G.box(b0, xb - 0.02, xb, -yb_, -ya_, 0.0, z, 1)
        # L2 연석(양 변, 길 폭 그대로) · L5 연석 윗선
        zc = z + 0.18
        for (c0, c1) in ((xa, xa + cw), (xb - cw, xb)):
            e = road_end(rd, 0.5 * (c0 + c1))
            lo, hi = sorted((yg, e))
            if hi - lo < 0.3:
                continue
            G.box(b2, c0, c1, -hi, -lo, z - 0.05, zc, 0)
            LY.flat_poly(b5, [[(c0, -lo), (c0 + 0.2, -lo), (c0 + 0.2, -hi), (c0, -hi)]], zc + 0.05, 0)
        # L1 바퀴 자국(R1: ±3.4·±5.2 · 나머지 ±1.3)
        for off in ((-5.2, -3.4, 3.4, 5.2) if rd['id'] == 'R1' else (-1.3, 1.3)):
            e = road_end(rd, xc + off)
            lo, hi = sorted((yg, e))
            lo += 0.5 if rd['side'] > 0 else 0.0; hi -= 0.5 if rd['side'] < 0 else 0.0
            if rd['side'] > 0:
                hi -= 0.6
            else:
                lo += 0.6
            if hi - lo > 0.5:
                LY.flat_poly(b1, [[(xc + off - 0.12, -lo), (xc + off + 0.12, -lo), (xc + off + 0.12, -hi), (xc + off - 0.12, -hi)]], z + 0.05, 0)
        # L3 판석 무늬(밝고 짙은 다각 판석, ground 길과 같은 결)
        lo, hi = sorted((yg, road_end(rd, xc)))
        for kk in range(int((hi - lo) / 1.6)):
            if R.hash01(kk, 44, len(rd['id']) + xc) > 0.42:
                continue
            u = lo + (kk + 0.5) * 1.6
            v = xa + cw + (xb - xa - 2 * cw) * (0.1 + 0.8 * R.hash01(kk, 55, xc))
            if (rd['side'] < 0 and u < road_end(rd, v) + 0.6) or (rd['side'] > 0 and u > road_end(rd, v) - 0.6):
                continue
            r_ = 0.32 + 0.22 * R.hash01(kk, 66, xc)
            LY.flat_poly(b3, [[(v + r_ * math.cos(2 * math.pi * t / 6 + 0.3 * kk), -u + r_ * 0.85 * math.sin(2 * math.pi * t / 6 + 0.3 * kk)) for t in range(6)]],
                         z + 0.10, 0 if R.hash01(kk, 77, xc) < 0.5 else 1)
        # L4 형태 디테일: R1 흰 중앙선(ground 위상 그대로) · 기단 발치 끝 돌턱(길 끝 연석 토막) · 들뜬 판석
        if rd['id'] == 'R1':
            w2 = 1.6 / C30 / 2
            y0 = K()['r1_dash0']
            n0 = math.ceil((lo - 6.5 - y0) / 9.5)
            for kk in range(n0, n0 + 40):
                ya = y0 + 9.5 * kk; yb = ya + 6.5
                ya = max(ya, lo); yb = min(yb, road_end(rd, xc) - 1.0)
                if yb - ya > 0.4:
                    G.box(b4, xc - w2, xc + w2, -yb, -ya, z, z + 0.15, 0)
        for kk in range(3):
            v = xa + cw + 0.8 + (xb - xa - 2 * cw - 1.6) * R.hash01(kk, 88, xc)
            u = lo + (hi - lo) * (0.25 + 0.5 * R.hash01(kk, 99, xc))
            LY.obox(b4, v, -u, z, 0.9, 0.6, 0.12, 30.0 * kk, 2, (5.0, -4.0))
        # L6 길가 풀 포기(양 변 바깥)
        for kk in range(int((hi - lo) / 2.2)):
            if R.hash01(kk, 33, xc) > 0.6:
                continue
            u = lo + (kk + 0.5) * 2.2
            px = xb + 0.35 if R.hash01(kk, 19, xc) < 0.5 else xa - 0.35
            if (rd['side'] < 0 and u < road_end(rd, px) + 0.8) or (rd['side'] > 0 and u > road_end(rd, px) - 0.8):
                continue
            LY.tuft(b6, px, -u, 0.0, 0.42 + 0.3 * R.hash01(kk, 21, xc), 8000 + kk + int(xc * 10), kk % 3)
    O.done()
    return O.root


# 노점·인물 무리 자리의 밟힌 흙 마당(화면 mm 중심, 평면 반축)
YARDS = [((245.0, 351.0), 9.0, 5.5), ((277.0, 339.0), 6.0, 4.0), ((186.0, 322.0), 6.0, 4.0), ((197.0, 350.0), 6.0, 4.2),
         ((210.0, 364.0), 7.0, 4.6), ((300.0, 359.0), 7.0, 4.6)]
STONE_PILES = [(168.0, 300.0), (330.0, 300.0), (322.0, 345.0)]     # 다듬은 트래버틴 석재 더미(보수용 재료, 화면 mm)


def stall_spots():
    """승인 설계 노점 2곳의 화면 자리. 길 연장·콜로세움에 걸리면 4 mm 간격 고리로 가장 가까운 빈 땅을 찾는다(화면 mm, 회전)"""
    out = []
    for ((sx, sy), rot) in STALLS:
        best = None
        for d in (0.0, 4.0, 8.0, 12.0, 16.0):
            for k in range(1 if d == 0.0 else 12):
                a = 2 * math.pi * k / 12.0
                cx, cy = sx + d * math.cos(a), sy + 0.6 * d * math.sin(a)
                x, y = plan_of_screen(cx, cy)
                if ground_free(x, y, 3.5, 4.0) and all(math.hypot(cx - q[0], cy - q[1]) > 14.0 for q in out):
                    best = (cx, cy, rot); break
            if best:
                break
        if best:
            out.append(best)
    return out


def stage_grounds(HC, top, m):
    """HERO_Life_root(HERO_root 아래): 광장이 빠진 예약 원 안 땅을 한 오브젝트로 표현 레이어를 쌓는다. 집·나무·밭 0.
    L0 밟힌 흙 마당 · L1 짙은 흙 구덩이(물 고인 자국) · L2 다듬은 석재 더미 · L3 흙 결·발길 · L4 잔돌·수레 바퀴 자국 · L5 밝은 흙 결·석재 윗선 ·
    L6 풀 포기(드문드문)·발자국·사람·노점·암포라·수레. 모두 땅(Z 0) 위"""
    O = LY.Obj('HERO', 'Life', HC, top)
    RR = K()['res_r']
    def P_(sx, sy):
        return plan_of_screen(sx, sy)
    def free(x, y, pad=1.0, g=1.6):
        return ground_free(x, y, pad, g)
    def blob_at(bm, x, y, rx, ry, seed, z, mi, n=12, jit=0.24, rot=0.0):
        LY.flat_poly(bm, [[(px, -py) for px, py in LY.blob(x, y, rx, ry, n, seed, jit, rot)]], z, mi)
    # L0 덩어리: 노점·인물 무리 밑 밟힌 흙 마당(땅보다 조금 짙고 노란 흙)
    b0 = O.bm(0, 'Trodden', [m['trodden'], m['land_patch']], closed=False)
    stalls = stall_spots()
    yards = []
    for j, ((sx, sy), rx, ry) in enumerate(YARDS[:4] + [((s_[0], s_[1]), 7.0, 4.6) for s_ in stalls]):
        x, y = P_(sx, sy)
        if not free(x, y, 2.0, 3.0):
            continue
        yards.append((x, y, rx, ry))
        blob_at(b0, x, y, rx, ry, 300 + j, Z_TROD, j % 2, 16, 0.22, 20.0 * j)
    # L3 표면 무늬: 흙 얼룩(드문드문) · 점무늬 · 발길(무리 사이 밟힌 줄)
    b3 = O.bm(3, 'EarthGrain', [m['land_patch'], m['land_dot'], m['speck']], closed=False)
    n3 = 0
    for j in range(600):
        if n3 >= 34:
            break
        th = 2 * math.pi * R.hash01(j, 201); r = RR * math.sqrt(0.18 + 0.8 * R.hash01(j, 202))
        x, y = r * math.cos(th), r * math.sin(th)
        if not free(x, y, 2.5, 2.5):
            continue
        n3 += 1
        blob_at(b3, x, y, 1.6 + 2.6 * R.hash01(j, 203), 0.7 + 1.0 * R.hash01(j, 204), 500 + j, Z_GRAIN, 0, 12, 0.3, 360.0 * R.hash01(j, 205))
    for j in range(900):                                                            # 점무늬(작은 흙덩이·자갈)
        th = 2 * math.pi * R.hash01(j, 211); r = RR * math.sqrt(0.1 + 0.88 * R.hash01(j, 212))
        x, y = r * math.cos(th), r * math.sin(th)
        if R.hash01(j, 213) > 0.45 or not free(x, y, 1.0, 1.4):
            continue
        blob_at(b3, x, y, 0.28 + 0.25 * R.hash01(j, 214), 0.17 + 0.12 * R.hash01(j, 215), 900 + j, Z_GRAIN, 1 + j % 2, 6, 0.2, 50.0 * j)
    trails = [(y_a, y_b) for y_a, y_b in zip(yards, yards[1:])]
    for k_, (a_, b_) in enumerate(trails):                                          # 발길(무리 → 무리, 폭 0.7의 밟힌 줄)
        n = 18
        for t in range(n):
            u0, u1 = t / n, (t + 0.62) / n
            xa_, ya_ = a_[0] + (b_[0] - a_[0]) * u0, a_[1] + (b_[1] - a_[1]) * u0 + 1.2 * math.sin(math.pi * u0)
            xb_, yb_ = a_[0] + (b_[0] - a_[0]) * u1, a_[1] + (b_[1] - a_[1]) * u1 + 1.2 * math.sin(math.pi * u1)
            if not (free(xa_, ya_, 0.5, 1.2) and free(xb_, yb_, 0.5, 1.2)):
                continue
            L_ = math.hypot(xb_ - xa_, yb_ - ya_) or 1.0
            nx, ny = -(yb_ - ya_) / L_ * 0.35, (xb_ - xa_) / L_ * 0.35
            LY.flat_poly(b3, [[(xa_ - nx, -(ya_ - ny)), (xb_ - nx, -(yb_ - ny)), (xb_ + nx, -(yb_ + ny)), (xa_ + nx, -(ya_ + ny))]], Z_GRAIN, 0)
    # L1 깊이색: 짙은 흙 구덩이·물 고였던 자국(마당 안·길 연장 옆)
    b1 = O.bm(1, 'Hollows', [m['soil'], m['soil_dk']], closed=False)
    for j, (x, y, rx, ry) in enumerate(yards):
        for i in range(2):
            a = 2 * math.pi * R.hash01(j, i, 221); q = 0.55 * R.hash01(j, i, 222)
            blob_at(b1, x + rx * q * math.cos(a), y + ry * q * math.sin(a), 0.7 + 0.5 * R.hash01(j, i, 223), 0.4 + 0.3 * R.hash01(j, i, 224),
                    700 + j * 7 + i, Z_HOLLOW, i % 2, 8, 0.25, 70.0 * i)
    for rd in approaches():                                                         # 길 끝 문 선 옆 수레가 돌아 나간 흙 패임
        for sgn in (-1, 1):
            x = rd['xc'] + sgn * (rd['hw'] + 1.6); y = rd['yg'] + (3.0 if rd['side'] < 0 else -3.0) * -1
            if free(x, y, 0.8, 1.6):
                blob_at(b1, x, y, 0.9, 0.5, 760 + int(x), Z_HOLLOW, 1, 8, 0.25, 15.0)
    # L2 부재: 다듬은 트래버틴 석재 더미(보수용, 3곳 × 4~5덩이) · 깔아 둔 굄목
    b2 = O.bm(2, 'StoneStock', [m['trav_blocks'], m['wood_flat']])
    b5 = O.bm(5, 'Highlights', [m['trav_hi'], m['land_patch2'], m['wood_lt']], closed=False)
    piles = []
    for j, (sx, sy) in enumerate(STONE_PILES):
        x, y = P_(sx, sy)
        if not free(x, y, 3.0, 3.0):
            continue
        piles.append((x, y))
        rot = 35.0 * j - 20.0
        LY.obox(b2, x, -y, 0.0, 4.2, 0.35, 0.18, rot, 1); LY.obox(b2, x + 0.4, -y - 1.4, 0.0, 4.2, 0.35, 0.18, rot, 1)
        blocks = ((-1.0, -0.6, 0.18, 1.6, 1.0, 0.9), (0.8, -0.5, 0.18, 1.5, 1.0, 0.85), (-0.1, 0.9, 0.0, 1.7, 1.1, 0.95),
                  (0.0, -0.55, 1.08, 1.4, 0.95, 0.8), (1.9, 1.1, 0.0, 1.0, 0.8, 0.6))
        cr_, sr_ = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        for i, (dx, dy, z0, w, d, h) in enumerate(blocks[:4 + j % 2]):
            bx_, by_ = x + cr_ * dx - sr_ * dy, -y + sr_ * dx + cr_ * dy
            LY.obox(b2, bx_, by_, z0, w, d, h, rot + 6.0 * (i - 2), 0)
            LY.obox(b5, bx_, by_, z0 + h, w * 0.92, d * 0.92, 0.04, rot + 6.0 * (i - 2), 0)       # L5 윗면 밝은 띠
    # L4 형태 디테일: 잔돌(석재 조각·자갈) · 수레 바퀴 자국(R4 문 선 → 노점)
    b4 = O.bm(4, 'Pebbles', [m['trav_blocks'], m['tuff'], m['land_dot']])
    n4 = 0
    for j in range(800):
        if n4 >= 70:
            break
        th = 2 * math.pi * R.hash01(j, 231); r = RR * math.sqrt(0.15 + 0.83 * R.hash01(j, 232))
        x, y = r * math.cos(th), r * math.sin(th)
        if not free(x, y, 1.0, 1.2):
            continue
        n4 += 1
        w = 0.35 + 0.45 * R.hash01(j, 233)
        LY.obox(b4, x, -y, 0.0, w, w * 0.7, 0.14 + 0.12 * R.hash01(j, 234), 360.0 * R.hash01(j, 235), j % 3, (8.0 * (R.hash01(j, 236) - 0.5), 0.0))
    for (x, y) in piles:                                                            # 석재 더미 둘레 깎아 낸 돌 부스러기
        for i in range(8):
            a = 2 * math.pi * i / 8 + 0.4; rr = 3.0 + 0.8 * R.hash01(i, x)
            LY.obox(b4, x + rr * math.cos(a), -y + rr * math.sin(a), 0.0, 0.4, 0.3, 0.12, 40.0 * i, 0)
    r4 = [rd for rd in approaches() if rd['id'] == 'R4'][0]
    # L5 하이라이트: 밝은 흙 결(햇볕에 마른 흙 줄, 드문드문)
    n5 = 0
    for j in range(600):
        if n5 >= 30:
            break
        th = 2 * math.pi * R.hash01(j, 241); r = RR * math.sqrt(0.18 + 0.8 * R.hash01(j, 242))
        x, y = r * math.cos(th), r * math.sin(th)
        if not free(x, y, 2.0, 2.0):
            continue
        n5 += 1
        blob_at(b5, x, y, 1.2 + 1.6 * R.hash01(j, 243), 0.35 + 0.3 * R.hash01(j, 244), 1100 + j, Z_LIGHT, 1, 10, 0.3, 360.0 * R.hash01(j, 245))
    # L6 얼룩·식생·생활: 풀 포기(드문드문 + 기단 계단 발치) · 발자국 · 사람 · 노점 · 암포라 · 수레
    b6 = O.bm(6, 'Tufts', [m['grass2'], m['grass1'], m['moss']])
    n6 = 0
    for j in range(1400):
        if n6 >= 130:
            break
        th = 2 * math.pi * R.hash01(j, 251); r = RR * math.sqrt(0.12 + 0.86 * R.hash01(j, 252))
        x, y = r * math.cos(th), r * math.sin(th)
        if not free(x, y, 0.6, 1.2) or any(math.hypot(x - q[0], y - q[1]) < max(q[2], q[3]) * 0.8 for q in yards):
            continue
        n6 += 1
        LY.tuft(b6, x, -y, 0.0, 0.3 + 0.3 * R.hash01(j, 253), 12000 + j, 2 if R.hash01(j, 254) > 0.8 else j % 2, 3 if j % 3 else 2)
    for j in range(110):                                                            # 기단 계단 발치(계단과 땅 사이)
        s_ = C.E.L * R.hash01(j, 141)
        p = LY.ell_pt(s_, -0.95 - 0.3 * R.hash01(j, 142), 0.0)
        if on_approach(p.x, -p.y, 0.4):
            continue
        LY.tuft(b6, p.x, p.y, 0.0, 0.32 + 0.22 * R.hash01(j, 143), 7000 + j, j % 2)
    b6f = O.bm(6, 'Footprints', [m['soil'], m['land_dot']], closed=False)          # 발자국(마당 사이 발길 위 짝 점)
    for k_, (a_, b_) in enumerate(trails):
        for t in range(1, 22):
            u = t / 22.0
            x = a_[0] + (b_[0] - a_[0]) * u; y = a_[1] + (b_[1] - a_[1]) * u + 1.2 * math.sin(math.pi * u)
            if not free(x, y, 0.5, 1.2):
                continue
            side = 0.18 if t % 2 else -0.18
            L_ = math.hypot(b_[0] - a_[0], b_[1] - a_[1]) or 1.0
            nx, ny = -(b_[1] - a_[1]) / L_, (b_[0] - a_[0]) / L_
            blob_at(b6f, x + nx * side, y + ny * side, 0.17, 0.1, 1300 + k_ * 40 + t, Z_HOLLOW, t % 2, 6, 0.1,
                    math.degrees(math.atan2(b_[1] - a_[1], b_[0] - a_[0])))
    # 노점 2곳(흰·빨간 차양, 키 6.86) + 암포라 무리(2.2) + 수레(3.22)
    for k, (sx, sy, rot) in enumerate(stalls):
        x, y = P_(sx, sy)
        O.place('stall', x, -y, Z_TROD, 6.86, rot, 6, 'Stall')
        for j in range(4):
            a = math.radians(rot) + math.pi * (0.9 + 0.35 * j); rr = 4.6 + 0.8 * (j % 2)
            O.place('amphora', x + rr * math.cos(a), -y + rr * math.sin(a), Z_TROD, 2.2, 40.0 * j, 6, 'Amphora')
    cx_, cy_ = P_(232.0, 368.0)
    if free(cx_, cy_, 2.0, 2.5):
        O.place('cart', cx_, -cy_, Z_TROD, 3.22, -58.0, 6, 'Cart')
        for j in range(3):                                                          # 수레 옆 생석회 자루·통
            O.place('amphora', cx_ - 2.0 + 1.1 * j, -cy_ - 3.2 - 0.4 * j, Z_TROD, 2.2, 30.0 * j, 6, 'Amphora')
    x4c, y4g = r4['xc'], r4['yg']                                                   # 하역장 길 연장 위 수레(하역장에서 올라오는 짐)
    O.place('cart', x4c - 1.5, -(y4g - 6.0), r4['z'], 3.22, 90.0, 6, 'Cart')
    # 인물 무리(키 4.6~5.2, 발점 간격 3.5~5) + 흩어진 사람
    k = 0
    for (gid, (sx, sy), n, sp) in GROUPS:
        gx, gy = P_(sx, sy)
        for j in range(n):
            a = 2 * math.pi * j / n + R.hash01(j, gx); rr = sp * (0.55 + 0.45 * (j % 2))
            x, y = gx + rr * math.cos(a), gy + rr * math.sin(a)
            if not free(x, y, 0.6, 1.4):
                continue
            person(O, k, x, -y, Z_TROD, 360.0 * R.hash01(k, 82)); k += 1
    for (sx, sy) in SCATTER + SCATTER2:
        x, y = P_(sx, sy)
        if not free(x, y, 0.8, 1.4):
            continue
        person(O, k, x, -y, Z_TROD, 360.0 * R.hash01(k, 82)); k += 1
    O.done()
    return O.root


def adopt(top, names):
    """루트를 월드 자리 그대로 HERO_root 아래로(위계 측정 단위 = 콜로세움 건물 + 인물·노점·공사장·네로)"""
    bpy.context.view_layer.update()
    for n in names:
        ob = bpy.data.objects.get(n)
        if ob is None or ob.parent is top:
            continue
        mw = ob.matrix_world.copy()
        ob.parent = top
        ob.matrix_parent_inverse = top.matrix_world.inverted()
        ob.matrix_world = mw


# ───────────────────────── 네로 거상 받침(벽돌 마감 콘크리트) · 청동 거상(추정) ─────────────────────────
def nero_root_loc():
    X, Y = K()['nero_plan']
    return R.P(X, Y, 0.0)


def stage_nero_yard(HC, top, m):
    """네로 받침 둘레 포장 마당(14×14, 화면 [172, 196, 198, 228] 안). 집·나무 0(ground가 비운다). 사람 키 4.9"""
    a = K()['nero_base'][0] / 2.0
    O = LY.Obj('HERO', 'NeroYard', HC, None, loc=nero_root_loc(), rot=0.0)
    yd = D_NERO_YARD / 2.0
    b0 = O.bm(0, 'Paving', [m['slab']], closed=False)                                  # L0 포장 바탕(0.10)
    LY.flat_poly(b0, [[(-yd, -yd), (yd, -yd), (yd, yd), (-yd, yd)]], 0.10, 0)
    b1 = O.bm(1, 'Holes', [m['soil_dk'], m['slab_dk']], closed=False)                 # L1 빠진 판석·갈라진 틈
    for j, (x, y) in enumerate(((-5.2, 3.8), (4.6, 5.1), (-4.4, -5.6), (5.6, -4.2))):
        LY.flat_poly(b1, [[(px, py) for px, py in LY.blob(x, y, 0.9, 0.55, 6, 90 + j, 0.15, 25.0 * j)]], 0.20, j % 2)
    b2 = O.bm(2, 'Kerb', [m['kerb']])                                                 # L2 마당 연석
    for (x0, x1, y0, y1) in ((-yd, yd, -yd, -yd + 0.55), (-yd, yd, yd - 0.55, yd), (-yd, -yd + 0.55, -yd, yd), (yd - 0.55, yd, -yd, yd)):
        G.box(b2, x0, x1, y0, y1, 0.0, 0.32, 0)
    b3 = O.bm(3, 'Slabs', [m['slab_blocks']], closed=False)                           # L3 판석 무늬(0.15)
    LY.flat_poly(b3, [[(-yd + 0.55, -yd + 0.55), (yd - 0.55, -yd + 0.55), (yd - 0.55, yd - 0.55), (-yd + 0.55, yd - 0.55)]], 0.15, 0)
    b4 = O.bm(4, 'Debris', [m['plates'], m['marble'], m['brick_n']])                  # L4 떨어진 대리석 판 조각 · 작은 제단(복원 상상)
    for j, (x, y, w, an) in enumerate(((-3.0, -5.3, 1.3, 20.0), (2.2, -5.7, 1.0, -30.0), (5.5, -2.0, 1.1, 60.0))):
        LY.obox(b4, x, y, 0.15, w, w * 0.6, 0.12, an, 0, (6.0, 0.0))
    G.box(b4, -0.9, 0.9, -a - 1.7, -a - 0.7, 0.15, 1.15, 1)
    LY.obox(b4, -5.6, 1.4, 0.15, 0.7, 0.45, 0.3, 15.0, 2)
    b5 = O.bm(5, 'Highlights', [m['kerb_hi'], m['marble_hi']])                         # L5 연석 윗선 · 제단 윗선
    G.box(b5, -yd, yd, -yd - 0.04, -yd + 0.2, 0.32, 0.37, 0); G.box(b5, yd - 0.2, yd + 0.04, -yd, yd, 0.32, 0.37, 0)
    G.box(b5, -0.92, 0.92, -a - 1.72, -a - 1.62, 1.15, 1.2, 1)
    b6 = O.bm(6, 'Tufts', [m['grass2'], m['grass1']])                                  # L6 풀 포기 · 올려다보는 사람 2
    for j in range(16):
        t = 2 * math.pi * R.hash01(j, 171)
        LY.tuft(b6, (yd - 0.8) * math.cos(t), (yd - 0.8) * math.sin(t), 0.15, 0.4, 3000 + j, j % 2)
    for k, (x, y, rot) in enumerate(((-3.4, -6.0, 200.0), (1.8, -6.3, 160.0)) if DECOR else ()):      # 16:14 사람 0
        person(O, 40 + k, x, y, 0.15, rot, 'Person')
    O.done()
    return O.root


def stage_nero(HC, top, m):
    """받침 한 변 8.3 · 높이 3.4(16:25 사용자 레퍼런스 user_nero_base: 넓고 낮은 대리석 받침, 폭:높이 ≈ 2.4:1).
    겉은 대리석 판 마감이고, 앞-왼쪽 면·오른쪽 면에 판이 떨어져 벽돌 마감 콘크리트 속(spec 주석 '콘크리트(벽돌 마감) 받침')이 드러난다"""
    sb, hb = K()['nero_base']
    a = sb / 2.0; ab = a - 0.22; ac = a - 0.02
    zp, zc = 0.45, hb - 0.42                      # 밑단 윗면 · 코니스 밑면
    O = LY.Obj('HERO', 'NeroBase', HC, None, loc=nero_root_loc(), rot=0.0)
    # L0: 받침 덩어리(밑단 트래버틴 · 몸통 대리석 판 · 윗단 대리석 코니스, 몸통보다 0.2 내민다)
    b0 = O.bm(0, 'Base', [m['trav_blocks'], m['plates'], m['marble']])
    G.box(b0, -a, a, -a, a, 0.0, zp, 0)
    G.box(b0, -ab, ab, -ab, ab, zp, zc, 1)
    G.box(b0, -ac, ac, -ac, ac, zc, hb, 2)
    # L1 깊이색: 판이 떨어진 자리의 속(짙은 콘크리트) · 코니스 밑 그늘 띠 · 고정 구멍
    b1 = O.bm(1, 'Depth', [m['core'], m['deep']])
    G.box(b1, -ab + 0.9, 0.6, -ab - 0.03, -ab - 0.005, zp + 0.35, zc - 0.25, 0)        # 앞-왼쪽 면(−y) 떨어진 자리
    G.box(b1, ab + 0.005, ab + 0.03, -0.4, ab - 1.2, zp + 0.5, zc - 0.45, 0)            # 오른쪽 면(+x) 떨어진 자리
    G.box(b1, -ab, ab, -ab - 0.05, -ab, zc - 0.12, zc, 1); G.box(b1, ab, ab + 0.05, -ab, ab, zc - 0.12, zc, 1)
    for (x, z) in ((1.6, zc - 0.5), (2.8, zp + 0.7)):
        G.box(b1, x - 0.14, x + 0.14, -ab - 0.04, -ab - 0.01, z - 0.12, z + 0.12, 1)
    # L2 부재: 밑단 쇠시리(둥근 띠) · 코니스 밑 쇠시리
    b2 = O.bm(2, 'Members', [m['marble'], m['marble_lo']])
    G.box(b2, -a + 0.1, a - 0.1, -a + 0.1, a - 0.1, zp, zp + 0.22, 1)
    G.box(b2, -ab - 0.1, ab + 0.1, -ab - 0.1, ab + 0.1, zc - 0.22, zc, 1)
    # L3 표면 무늬: 드러난 속의 벽돌 켜(벽돌 마감 콘크리트) — 몸통 판 줄눈은 재질(plates)
    b3 = O.bm(3, 'BrickCore', [m['brick_n']])
    G.box(b3, -ab + 1.0, 0.5, -ab - 0.04, -ab - 0.02, zp + 0.45, zc - 0.35, 0)
    G.box(b3, ab + 0.02, ab + 0.04, -0.3, ab - 1.3, zp + 0.6, zc - 0.55, 0)
    # L4 형태 디테일: 떨어진 판 가장자리(들쭉날쭉 판 조각) · 깨진 코니스 모서리 · 밑동에 떨어진 판 조각
    b4 = O.bm(4, 'Detail', [m['plates'], m['marble'], m['brick_n']])
    for k, (x0, x1, z0, z1) in enumerate(((-ab + 0.7, -ab + 1.05, zp + 0.3, zc - 0.9), (0.45, 0.75, zp + 0.9, zc - 0.2), (-0.6, 0.2, zc - 0.32, zc - 0.2))):
        G.box(b4, x0, x1, -ab - 0.06, -ab, z0, z1, 0)
    G.box(b4, ab, ab + 0.06, ab - 1.35, ab - 1.05, zp + 0.4, zc - 0.3, 0)
    LY.obox(b4, ac - 0.25, -ac + 0.25, hb - 0.5, 0.55, 0.55, 0.5, 45.0, 1)
    for k, (x, y, w, an) in enumerate(((-2.4, -a - 0.9, 1.0, 20.0), (1.2, -a - 1.3, 0.8, -35.0), (a + 0.9, 1.5, 0.9, 60.0))):
        LY.obox(b4, x, y, 0.15, w, w * 0.6, 0.12, an, 0, (6.0, 0.0))
    # L5 하이라이트: 코니스·밑단 윗선(면색 명도 +6~12%)
    b5 = O.bm(5, 'Highlights', [m['marble_hi'], m['brick_hi']])
    G.box(b5, -ac, ac, -ac - 0.05, -ac + 0.25, hb, hb + 0.05, 0); G.box(b5, ac - 0.25, ac + 0.05, -ac, ac, hb, hb + 0.05, 0)
    G.box(b5, -ac, ac, -ac - 0.08, -ac - 0.03, hb - 0.25, hb + 0.02, 0); G.box(b5, ac + 0.03, ac + 0.08, -ac, ac, hb - 0.25, hb + 0.02, 0)
    G.box(b5, -a, a, -a - 0.07, -a - 0.02, zp - 0.15, zp + 0.02, 0); G.box(b5, a + 0.02, a + 0.07, -a, a, zp - 0.15, zp + 0.02, 0)
    # L6 얼룩·식생: 빗물 자국 · 떨어진 자리 위 이끼 · 밑동 풀 포기
    b6s = O.bm(6, 'Stains', [m['stain'], m['moss']])
    for x in (-2.6, 1.9):
        G.box(b6s, x - 0.15, x + 0.15, -ab - 0.11, -ab - 0.07, zp + 0.3, zc - 0.25, 0)
    G.box(b6s, ab + 0.07, ab + 0.11, 1.9, 2.2, zp + 0.3, zc - 0.25, 0)
    G.box(b6s, -ab + 1.0, 0.5, -ab - 0.12, -ab - 0.06, zp + 0.3, zp + 0.42, 1)
    life_ring(O, m, 0.0, 0.0, a + 0.18, a + 0.18, 22, 63, 0.15, 0.55)
    O.done()
    return O.root


def stage_colossus(HC, top, m):
    """청동 거상(복원 추정, 태양신 모습): 발 Z 5.0 → 관 꼭대기 Z 20.0, 몸 폭 화면 3.8 안([183.1, 200.2, 186.9, 216.3]).
    지역 −y가 얼굴 쪽. 루트를 +45° 돌려 관객(평면 방위 45°, 화면 아래)을 본다"""
    sb, hb = K()['nero_base']; ztop = K()['nero_top']
    O = LY.Obj('HERO', 'NeroColossus', HC, None, loc=nero_root_loc() + Vector((0, 0, hb)), rot=45.0)
    s = (ztop - hb) / 15.0                     # 15 → 키
    def z(v): return v * s
    # 18:58 레퍼런스(user_nero_base) 자세로 다시: 맨몸 청동상, 오른다리(−x)에 무게·왼무릎 앞으로(콘트라포스토),
    # 오른손은 앞으로 내밀어 키 자루를 쥐고, 왼팔은 네모 기둥 머리에 팔꿈치를 얹는다. 망토 0
    # L0 덩어리: 발판·다리 두 마디·발·골반·허리·가슴·어깨 세모근·가슴 근육·목·머리
    b0 = O.bm(0, 'Body', [m['bronze']])
    G.box(b0, -1.25, 1.25, -1.05, 1.05, 0.0, z(0.35), 0)
    LY.rod(b0, (-0.5, 0.05, z(6.4)), (-0.52, -0.08, z(3.4)), 0.62, 0.42, 10, 0)
    LY.rod(b0, (-0.52, -0.08, z(3.4)), (-0.5, 0.0, z(0.55)), 0.42, 0.27, 10, 0)
    LY.rod(b0, (0.52, 0.0, z(6.3)), (0.66, -0.42, z(3.5)), 0.6, 0.42, 10, 0)
    LY.rod(b0, (0.66, -0.42, z(3.5)), (0.74, 0.12, z(0.6)), 0.42, 0.26, 10, 0)
    for (fx, fy) in ((-0.5, -0.22), (0.74, -0.02)):
        LY.obox(b0, fx, fy, z(0.35), 0.5, 0.95, z(0.3), 0.0, 0)
    LY.lump(b0, 0.0, 0.02, z(6.6), 1.18, 0.82, z(0.85), 71, 0, 2)
    G.cyl(b0, 0.0, 0.0, 1.0, z(7.0), z(8.6), 14, 0, r_top=0.98, bottom=True)
    G.cyl(b0, 0.0, 0.0, 0.98, z(8.6), z(10.6), 14, 0, r_top=1.32, bottom=True)
    G.cyl(b0, 0.0, 0.0, 1.32, z(10.6), z(11.4), 14, 0, r_top=1.0, bottom=True)
    for sx in (-1, 1):
        LY.lump(b0, sx * 1.3, 0.0, z(11.05), 0.48, 0.45, z(0.42), 72 + sx, 0, 2)
        LY.lump(b0, sx * 0.5, -0.82, z(10.15), 0.55, 0.32, z(0.45), 76 + sx, 0, 2)
    G.cyl(b0, 0.0, 0.0, 0.38, z(11.4), z(12.4), 10, 0)
    LY.lump(b0, 0.0, 0.0, z(13.05), 0.62, 0.6, 0.72 * s, 61, 0, 2)
    # L1 깊이색: 다리 사이·겨드랑이·가슴 근육 밑 그늘(짙은 청동)
    b1 = O.bm(1, 'Shade', [m['bronze_dk']])
    LY.obox(b1, 0.05, 0.05, z(0.7), 0.36, 0.8, z(5.2), 0.0, 0)
    for sx in (-1, 1):
        LY.obox(b1, sx * 1.02, 0.05, z(9.4), 0.16, 0.7, z(1.6), 0.0, 0)
        LY.obox(b1, sx * 0.5, -1.06, z(9.62), 0.9, 0.05, z(0.16), sx * 10.0, 0)
    # L2 부재: 두 마디 팔·손 · 키(자루·날) · 네모 기둥(받침·몸·머리)
    b2 = O.bm(2, 'Members', [m['bronze'], m['bronze_dk']])
    LY.rod(b2, (-1.4, 0.0, z(11.2)), (-1.78, -0.25, z(9.3)), 0.38, 0.3, 10, 0)
    LY.rod(b2, (-1.78, -0.25, z(9.3)), (-2.0, -0.95, z(8.75)), 0.3, 0.24, 10, 0)
    LY.lump(b2, -2.02, -1.02, z(8.7), 0.26, 0.26, z(0.22), 73, 0, 1)
    LY.rod(b2, (-2.05, -1.05, z(10.2)), (-2.75, -1.4, z(0.4)), 0.12, 0.12, 6, 1)
    LY.obox(b2, -2.68, -1.36, z(0.4), 0.24, 1.15, z(2.4), 20.0, 1, (0.0, -6.0))
    G.box(b2, 1.42, 2.48, -0.38, 0.68, 0.0, z(0.35), 1)
    G.box(b2, 1.55, 2.35, -0.25, 0.55, z(0.35), z(8.75), 1)
    G.box(b2, 1.45, 2.45, -0.35, 0.65, z(8.75), z(9.25), 1)
    LY.rod(b2, (1.4, 0.0, z(11.2)), (1.85, 0.12, z(9.45)), 0.38, 0.3, 10, 0)
    LY.rod(b2, (1.85, 0.12, z(9.45)), (1.35, -0.8, z(9.3)), 0.3, 0.24, 10, 0)
    LY.lump(b2, 1.25, -0.95, z(9.15), 0.24, 0.24, z(0.25), 74, 0, 1)
    # L3 표면 무늬: 해부 선(배 가운데·복근·엉덩이 V·무릎) · 기둥 세로 홈
    b3 = O.bm(3, 'Anatomy', [m['bronze_dk']])
    LY.obox(b3, 0.0, -1.03, z(7.2), 0.07, 0.05, z(2.3), 0.0, 0)
    for k in range(3):
        LY.obox(b3, 0.0, -1.03, z(7.75 + 0.55 * k), 0.85, 0.05, z(0.05), 0.0, 0)
    for sx in (-1, 1):
        LY.obox(b3, sx * 0.6, -0.95, z(6.75), 0.7, 0.05, z(0.07), sx * 30.0, 0)
    LY.obox(b3, -0.52, -0.52, z(3.4), 0.42, 0.05, z(0.06), 0.0, 0)
    LY.obox(b3, 0.66, -0.86, z(3.5), 0.42, 0.05, z(0.06), 0.0, 0)
    for k in range(4):
        xg = 1.68 + 0.18 * k
        G.box(b3, xg - 0.03, xg + 0.03, -0.28, -0.24, z(0.6), z(8.5), 0)
    # L4 형태 디테일: 햇살 관(7갈래) · 머리카락 · 얼굴(코·눈썹 그늘)
    b4 = O.bm(4, 'Crown', [m['gold'], m['bronze_dk']])
    for k in range(7):
        t = math.radians(-90.0 + (k - 3) * 28.0)
        LY.rod(b4, (0.55 * math.cos(t), 0.55 * math.sin(t), z(13.5)), (1.1 * math.cos(t), 1.1 * math.sin(t), ztop - hb), 0.12, 0.02, 5, 0)
    G.ring(b4, 0.0, 0.0, 0.58, 0.7, z(13.35), z(13.6), 12, 0)
    LY.lump(b4, 0.0, 0.12, z(13.3), 0.64, 0.56, z(0.32), 75, 1, 2)
    LY.obox(b4, 0.0, -0.6, z(12.85), 0.16, 0.1, z(0.28), 0.0, 1)
    LY.obox(b4, 0.0, -0.6, z(13.15), 0.5, 0.05, z(0.05), 0.0, 1)
    # L5 하이라이트: 다리·몸통·팔의 밝은 쪽 띠(명도 +13%)
    b5 = O.bm(5, 'Highlights', [m['bronze_hi']])
    t = math.radians(-115.0)
    for (cx, cy, r, za, zb) in ((-0.52, 0.0, 0.5, z(0.8), z(6.1)), (0.6, -0.2, 0.5, z(0.8), z(6.0)), (0.0, 0.0, 1.05, z(7.2), z(10.4))):
        LY.obox(b5, cx + (r + 0.03) * math.cos(t), cy + (r + 0.03) * math.sin(t), za, 0.24, 0.05, zb - za, -25.0, 0)
    for sx in (-1, 1):
        LY.lump(b5, sx * 0.42, -1.08, z(10.35), 0.22, 0.08, z(0.18), 78 + sx, 0, 1)
    LY.rod(b5, (-1.62, -0.42, z(10.6)), (-1.8, -0.55, z(9.4)), 0.08, 0.06, 5, 0)
    G.box(b5, -1.25, 1.25, -1.1, -0.98, z(0.3), z(0.38), 0)
    # L6 얼룩: 녹청 줄(빗물 자국)
    b6 = O.bm(6, 'Patina', [m['patina']])
    for (x, y, za, zb) in ((-0.3, -1.08, z(7.4), z(10.0)), (0.45, -1.02, z(7.8), z(9.8)), (-0.55, -0.45, z(1.0), z(4.8)), (0.7, -0.62, z(1.2), z(3.2))):
        LY.obox(b6, x, y - 0.03, za, 0.12, 0.05, zb - za, 0.0, 0)
    O.done()
    head = Vector((0.0, 0.0, z(13.1)))
    return O.root, head


# ───────────────────────── 기초 공사장(복원 장면) ─────────────────────────
def stage_worksite(HC, top, m):
    """정보 층 draw_worksite와 같은 지역 좌표·원점. 지역 (X, Y) = 평면 축, Blender (X, −Y).
    거푸집 오른쪽 널을 떼어 다져 넣은 4켜(줄무늬)·골재·석회 알갱이를 보인다(Z1 확대 창 출발점 = 오른쪽 면 (13.05, 4.5, 2.0))"""
    WX, WY = K()['worksite_plan']
    O = LY.Obj('HERO', 'Worksite', HC, None, loc=R.P(WX, WY, 0.0), rot=0.0)
    O.root.parent = None
    def bx(b, X0, Y0, Z0, X1, Y1, Z1, mi=0):
        G.box(b, X0, X1, -Y1, -Y0, Z0, Z1, mi)
    # L0: 다진 흙 바닥(0.10) + 광장 가장자리까지 흙길 · 거푸집 널(뒤·왼쪽·앞-왼쪽, 오른쪽은 떼어 냈다) · 다져 넣은 콘크리트 · 통 · 재료 더미
    b0p = O.bm(0, 'Pad', [m['pad'], m['path']], closed=False)
    LY.flat_poly(b0p, [[(-1.0, 1.0), (24.0, 1.0), (24.0, -14.0), (-1.0, -14.0)]], 0.10, 0)
    tr = [(-1.0, 1.0), (-8.6, 12.0), (-17.4, 26.6), (-5.4, 30.6), (2.4, 14.0), (8.0, 1.0)]
    LY.flat_poly(b0p, [tr], 0.10, 1)
    b0 = O.bm(0, 'Formwork', [m['plank'], m['concrete'], m['wood_flat'], m['lime'], m['ash'], m['aggr']])
    bx(b0, 0.0, 0.0, 0.0, 13.0, 0.6, 4.0, 0)                 # 뒤 널
    bx(b0, 0.0, 0.6, 0.0, 0.6, 8.4, 4.0, 0)                  # 왼쪽(뒤) 널
    bx(b0, 0.0, 8.4, 0.0, 13.0, 9.0, 4.0, 0)                 # 앞-왼쪽 널: 바깥면 Y = 9.0 이 ⑥ 지시선 끝
    bx(b0, 0.6, 0.6, 0.0, 13.0, 8.4, 3.2, 1)                 # 다져 넣은 콘크리트(오른쪽 면 X = 13.0이 드러난다)
    G.ring(b0, 17.5, -2.6, 1.7, 1.9, 0.0, 2.1, 24, 2)        # 반죽 통(벽)
    G.cyl(b0, 17.5, -2.6, 1.72, 0.0, 0.3, 24, 2, bottom=True)
    for (X, Y, r, h, mi) in ((16.0, 8.4, 2.8, 2.5, 3), (20.6, 6.4, 2.6, 2.3, 4), (21.6, 1.6, 2.2, 1.9, 5)):   # 생석회(흰)·화산재(붉은 갈색)·골재(회색)
        G.cyl(b0, X, -Y, r, 0.1, h * 0.55, 12, mi, r_top=r * 0.62, bottom=True)
        G.cyl(b0, X, -Y, r * 0.62, h * 0.55, h, 12, mi, r_top=r * 0.14)
    # L1 깊이색: 널 안쪽(보이는 면) · 통 속 반죽 · 막 다진 젖은 윗면
    b1 = O.bm(1, 'Depth', [m['wood_dk'], m['mortar'], m['concrete_wet']])
    bx(b1, 0.6, 0.6, 3.2, 13.0, 0.66, 4.0, 0)
    bx(b1, 0.6, 0.66, 3.2, 0.66, 8.4, 4.0, 0)
    G.cyl(b1, 17.5, -2.6, 1.69, 1.7, 1.98, 24, 1)
    LY.flat_poly(b1, [[(2.0, -2.0), (9.8, -2.0), (9.8, -7.4), (2.0, -7.4)]], 3.25, 2)
    # L2 부재: 말뚝 · 다짐 막대 · 통 테
    b2 = O.bm(2, 'Stakes', [m['wood_flat'], m['wood_dk']])
    for X in (0.4, 4.5, 8.5, 12.6):
        bx(b2, X - 0.22, 9.0, 0.0, X + 0.22, 9.42, 4.7, 0)
    bx(b2, -0.42, 0.4, 0.0, 0.0, 0.84, 4.7, 0)
    for (X, Y) in ((4.5, 3.6), (9.2, 5.8)):
        LY.rod(b2, (X + 0.8, -(Y + 0.8), 3.2 + 4.6), (X + 2.0, -(Y + 2.4), 3.25), 0.12, 0.12, 6, 1)
        LY.rod(b2, (X + 2.0, -(Y + 2.4), 3.25), (X + 2.0, -(Y + 2.4), 3.6), 0.4, 0.4, 8, 1)
    G.cyl(b2, 17.5, -2.6, 1.95, 0.5, 0.7, 14, 1); G.cyl(b2, 17.5, -2.6, 1.95, 1.5, 1.7, 14, 1)
    # L3 표면 무늬: 오른쪽 면의 다져 넣은 4켜(두 색 번갈아) · 수레바퀴 자국
    b3 = O.bm(3, 'Layers', [m['concrete'], m['concrete2'], m['layer_line']])
    for k in range(4):
        z0, z1 = 0.8 * k, 0.8 * k + 0.8
        bx(b3, 13.0, 0.6, z0 + 0.02, 13.05, 8.4, z1 - 0.02, k % 2)
        if k < 3:
            bx(b3, 13.0, 0.6, z1 - 0.05, 13.10, 8.4, z1 + 0.05, 2)                      # 켜 사이 짙은 선
    b3r = O.bm(3, 'Ruts', [m['soil']], closed=False)
    for (ax, ay, bx_, by_) in ((-8.6, 17.0, 1.2, 0.6), (-5.0, 19.4, 5.2, 0.6)):     # 광장 판석 경계 밖에서 시작(판석과 겹침 0)
        dx, dy = bx_ - ax, by_ - ay; L_ = math.hypot(dx, dy); nx, ny = -dy / L_ * 0.12, dx / L_ * 0.12
        LY.flat_poly(b3r, [[(ax - nx, ay - ny), (bx_ - nx, by_ - ny), (bx_ + nx, by_ + ny), (ax + nx, ay + ny)]], 0.15, 0)
    b3e = O.bm(3, 'EarthSpecks', [m['speck'], m['soil']], closed=False)             # 다진 흙 바닥 점무늬(빈 단색 면 0)
    for j in range(70):
        X = -0.6 + 24.2 * R.hash01(j, 131); Y = -0.6 + 14.2 * R.hash01(j, 132)
        if -0.2 < X < 13.6 and -0.2 < Y < 9.8:
            continue
        LY.flat_poly(b3e, [[(px, py) for px, py in LY.blob(X, -Y, 0.3 + 0.25 * R.hash01(j, 133), 0.18 + 0.12 * R.hash01(j, 134), 6, 6000 + j, 0.2, 50.0 * j)]], 0.15, j % 2)
    # L4 형태 디테일: 골재 덩이(응회암·벽돌 조각)와 흰 석회 알갱이(오른쪽 면) · 연장 · 널판 · 바구니
    b4 = O.bm(4, 'Aggregate', [m['tuffchunk'], m['ash'], m['aggr'], m['lime']])
    for k in range(4):
        for j in range(9):
            Y = 1.0 + 7.0 * R.hash01(k, j, 81); Zc = 0.8 * k + 0.2 + 0.4 * R.hash01(k, j, 82)
            w = 0.22 + 0.22 * R.hash01(k, j, 83)
            if R.hash01(k, j, 84) > 0.72:
                bx(b4, 13.10, Y - 0.09, Zc - 0.09, 13.16, Y + 0.09, Zc + 0.09, 3)       # 석회 알갱이
            else:
                bx(b4, 13.10, Y - w / 2, Zc - w * 0.35, 13.16, Y + w / 2, Zc + w * 0.35, j % 3)
    b4t = O.bm(4, 'Tools', [m['wood_flat'], m['mortar'], m['wood_lt']])
    for k in range(3):
        bx(b4t, 1.0, 10.4 + 0.5 * k, 0.1, 9.4, 10.8 + 0.5 * k, 0.3 + 0.2 * k, 2)
    for (X, Y, a) in ((15.6, 8.0, 30.0), (21.0, 2.0, -20.0)):
        LY.rod(b4t, (X, -Y, 0.6), (X + 1.6 * math.cos(math.radians(a)), -Y, 3.6), 0.09, 0.09, 6, 0)
        LY.obox(b4t, X, -Y, 0.3, 0.7, 0.12, 0.8, a, 1)
    G.cyl(b4t, 19.6, -10.6, 0.9, 0.1, 0.9, 10, 0, r_top=1.05, bottom=True)
    b4p = O.bm(4, 'PileLumps', [m['lime_lo'], m['ash_lo'], m['aggr_lo'], m['tuffchunk']])   # 재료 더미 덩이(같은 계열 짙은 색: 빈 단색 면 0)
    for k_, (X, Y, r, h) in enumerate(((16.0, 8.4, 2.8, 2.5), (20.6, 6.4, 2.6, 2.3), (21.6, 1.6, 2.2, 1.9))):
        for j in range(9):
            a = 2 * math.pi * R.hash01(k_, j, 141); q = 0.35 + 0.55 * R.hash01(k_, j, 142)
            zz = 0.1 + h * 0.55 * (1.0 - q) * 0.9
            LY.lump(b4p, X + r * q * math.cos(a), -Y + r * q * math.sin(a), zz + 0.15, 0.32, 0.28, 0.22, 700 + k_ * 20 + j,
                    k_ if R.hash01(k_, j, 143) > 0.25 else 3, 1)
    # L5 하이라이트: 널 윗선 · 통 테두리 · 콘크리트 오른쪽 위 모서리
    b5 = O.bm(5, 'Highlights', [m['wood_lt'], m['lime']])
    for (a, b_, d_, e) in ((0, 0, 13, 0.6), (0, 8.4, 13, 9.0), (0, 0.6, 0.6, 8.4)):
        bx(b5, a, b_, 4.0, d_, e, 4.05, 0)
    G.ring(b5, 17.5, -2.6, 1.68, 1.92, 2.1, 2.15, 24, 0)
    bx(b5, 12.75, 0.6, 3.2, 13.10, 8.4, 3.25, 1)
    # L6 얼룩·식생·생활: 석회 가루·화산재 자국 · 풀 포기 · 일꾼 3(다짐 2 + 반죽 1, 키 4.9)
    b6 = O.bm(6, 'Dust', [m['lime'], m['ash'], m['grass2']], closed=False)
    LY.flat_poly(b6, [LY.blob(15.0, -10.4, 2.4, 1.2, 10, 71.0, 0.3)], 0.20, 0)
    LY.flat_poly(b6, [LY.blob(23.0, -8.2, 1.6, 1.0, 10, 72.0, 0.3)], 0.20, 1)
    b6g = O.bm(6, 'Grass', [m['grass2'], m['grass1']])
    for j in range(12):
        X = -1.0 + 25.0 * R.hash01(j, 91); Y = (-1.2 if j % 2 else 14.2)
        LY.tuft(b6g, X, -Y, 0.1, 0.55, 900 + j, j % 2)
    for k, (X, Y, Z, rot) in enumerate(((4.5, 3.6, 3.2, 140.0), (9.2, 5.8, 3.2, 160.0), (15.4, 1.0, 0.1, 230.0))):
        person(O, 60 + k, X, -Y, Z, rot, 'Worker')
    O.done()
    return O.root


# ───────────────────────── 앵커(정보 층 지시선·라벨 끝) ─────────────────────────
def anchor(HC, name, world, parent=None):
    """숨긴 Empty ANCHOR_{대상}_{역할}. 부모 루트에 붙여 루트를 옮기면 함께 움직인다(월드 자리 = world)"""
    e = bpy.data.objects.new('ANCHOR_' + name, None)
    HC.objects.link(e)
    e.empty_display_type = 'SPHERE'; e.empty_display_size = 0.8; e.hide_render = True
    if parent is not None:
        e.parent = parent
        e.location = parent.matrix_world.inverted() @ world
    else:
        e.location = world
    return e


def stage_anchors(HC, top, m, head=None):
    bpy.context.view_layer.update()
    out = {}
    # HERO_label: (269.97, 244.0)에 가장 가까운 외벽 윗면(가운데 줄) 점
    base = top.matrix_world
    best = (1e9, None)
    for k in range(2400):
        s = C.E.L * k / 2400.0
        i = int(s / C.W) % C.NB
        x = s - (i + 0.5) * C.W
        h = C.wall_top(i, x)
        p = base @ LY.ell_pt(s, C.T1 * 0.5, h)
        sx, sy = R.scr(p)
        d = math.hypot(sx - HERO_LABEL_PT[0], sy - HERO_LABEL_PT[1])
        if d < best[0]:
            best = (d, p.copy())
    out['HERO_label'] = anchor(HC, 'HERO_label', best[1], colo_root(HC))
    # NERO_label: 거상 머리(보이는 면 위: 머리 가운데에서 카메라 쪽으로 반지름만큼)
    col = bpy.data.objects.get('HERO_NeroColossus_root')
    if col is not None:
        hb = K()['nero_base'][1]; s = (K()['nero_top'] - hb) / 15.0
        hc = col.matrix_world @ Vector((0.0, 0.0, 13.1 * s))
        out['NERO_label'] = anchor(HC, 'NERO_label', hc - R.FWD * 0.62, col)
    nb_ = bpy.data.objects.get('HERO_NeroBase_root')
    if col is None and nb_ is not None:              # 16:14 거상 없음: 받침 앞-왼쪽 면(−y) 코니스 바로 밑 가운데(보이는 면 위)
        sb_, hb_ = K()['nero_base']
        out['NERO_label'] = anchor(HC, 'NERO_label', nb_.matrix_world @ Vector((0.0, -(sb_ / 2.0 - 0.06) - 0.01, hb_ - 0.6)), nb_)
    ws = bpy.data.objects.get('HERO_Worksite_root')
    if ws is not None:
        mw = ws.matrix_world
        out['WS_s6'] = anchor(HC, 'WS_s6', mw @ Vector((6.5, -9.0, 2.0)), ws)          # 거푸집 앞-왼쪽 면 중심(⑥ 지시선 끝)
        out['WS_z1'] = anchor(HC, 'WS_z1', mw @ Vector((13.05, -4.5, 2.0)), ws)        # 오른쪽 면(다져 넣은 켜) = Z1 지시선 출발점
        out['WS_label'] = anchor(HC, 'WS_label', mw @ Vector((10.0, -9.0, 0.6)), ws)   # 공사장 태그 꼬리가 향하는 앞-왼쪽 널 아래
    return out


# ───────────────────────── 짓기 ─────────────────────────
NERO = False                         # 00:05 사용자 "네로거상 삭제해": 받침·거상·마당을 짓지 않는다(코드는 보관)
STAGES = (('colo_outer', 'colo_inner') + (('nero',) if NERO else ()) + ('anchors',)) if not DECOR else ('colo_outer', 'colo_inner', 'grounds', 'nero', 'worksite', 'anchors')
REMOVED = ('grounds', 'worksite')         # 16:14: 이 단계를 주면 지우기만 한다(광장·둘레 땅·길 연장·공사장)


def top_root(HC):
    t = bpy.data.objects.get('HERO_root')
    if t is None:
        t = bpy.data.objects.new('HERO_root', None); HC.objects.link(t)
        t.empty_display_size = 20
    HX, HY = K()['hero_plan']
    t.location = R.P(HX, HY, 0.0)            # 지도 땅 위에 바로(받침 없음)
    return t


def clear_tree(names_prefix):
    """루트 이름으로 시작하는 오브젝트 묶음만 지운다(단계별 다시 짓기)"""
    HC = bpy.data.collections.get(COLL)
    if HC is None:
        return
    for ob in list(HC.all_objects):
        if any(ob.name.startswith(p) for p in names_prefix):
            me = ob.data if ob.type == 'MESH' else None
            bpy.data.objects.remove(ob, do_unlink=True)
            if me is not None and me.users == 0:
                bpy.data.meshes.remove(me)


STAGE_PREFIX = {
    'colo_outer': ('HERO_Colosseum_', 'H_', 'X_CUT_HeroPit', 'ANCHOR_HERO'),
    'colo_inner': ('HERO_Colosseum_L0_CaveaVaults', 'HERO_Colosseum_L0_Seats', 'HERO_Colosseum_L0_RadialWalls', 'HERO_Colosseum_L0_InnerRings',
                   'HERO_Colosseum_L1_CaveaCavities', 'HERO_Colosseum_L5_Caps', 'HERO_Colosseum_L0_Arena', 'HERO_Colosseum_L0_PitFloor',
                   'HERO_Colosseum_L0_Hypogeum', 'HERO_Colosseum_L0_InnerFloor', 'HERO_Colosseum_L4_Rubble', 'HERO_Colosseum_L6_Moss',
                   'HERO_Colosseum_L6_Tufts', 'HERO_Colosseum_L6_Person', 'X_CUT_HeroPit', 'H_'),
    'grounds': ('HERO_Life_', 'HERO_Approach_', 'HERO_Plaza_'),
    'nero': ('HERO_NeroBase_', 'HERO_NeroColossus_', 'HERO_NeroYard_', 'ANCHOR_NERO'),
    'worksite': ('HERO_Worksite_', 'ANCHOR_WS'),
    'anchors': ('ANCHOR_',),
}


def build(stage=None):
    """stage=None: 내 컬렉션만 지우고 전부 다시 짓는다. stage='plaza' 등: 그 단계만 다시 짓는다(각 90초 안)"""
    global CFG
    CFG = None
    import time
    HC = R.coll(COLL, R.coll('ROMA_MAP'))
    if stage is None:
        R.clear_coll(COLL)
    m = mats()
    protos()
    ox, oy = K()['colo_off']
    C.CX, C.CY = ox, -oy                         # 타원 중심(Blender 지역 축) — 광장·앵커 단계도 같은 값을 쓴다
    top = top_root(HC)
    if stage == 'plaza':                         # 13:33 광장 제거: 옛 단계 이름은 'grounds'로 바꿔 짓는다
        stage = 'grounds'
    if stage is None and not DECOR:
        for st in REMOVED:
            clear_tree(STAGE_PREFIX[st])
    if stage in REMOVED and not DECOR:          # 16:14 core만: 지우기만 한다
        clear_tree(STAGE_PREFIX[stage])
        print('hero 단계 %s: 16:14 결정으로 지우기만 했다' % stage)
        return top
    todo = STAGES if stage is None else (stage,)
    FAILED.clear()
    head = None
    for st in todo:
        t0 = time.time()
        if stage is not None:
            clear_tree(STAGE_PREFIX[st])
            if st == 'colo_outer':
                clear_tree(STAGE_PREFIX['colo_inner'])
        if st == 'colo_outer':
            _guard('콜로세움 외벽', stage_colo_outer, HC, top, m)
        elif st == 'colo_inner':
            if colo_root(HC) is None:
                _guard('콜로세움 외벽', stage_colo_outer, HC, top, m)
            _guard('콜로세움 안(관람석·경기장·하이포게움)', stage_colo_inner, HC, top, m)
            apply_colo_scale()
        elif st == 'grounds':
            _guard('길 연장', stage_approach, HC, top, m)
            _guard('히어로 군 땅·생활', stage_grounds, HC, top, m)
        elif st == 'nero' and not NERO:                                   # 00:05 사용자: 네로 삭제
            clear_tree(STAGE_PREFIX['nero'])
        elif st == 'nero':
            _guard('네로 마당', stage_nero_yard, HC, top, m)
            _guard('네로 받침', stage_nero, HC, top, m)
            if DECOR or COLOSSUS:                # 16:29 사용자: 거상을 다시 세운다
                _guard('네로 거상', stage_colossus, HC, top, m)
            adopt(top, ('HERO_NeroYard_root', 'HERO_NeroBase_root', 'HERO_NeroColossus_root'))
        elif st == 'worksite':
            _guard('공사장', stage_worksite, HC, top, m)
            adopt(top, ('HERO_Worksite_root',))
        elif st == 'anchors':
            clear_tree(STAGE_PREFIX['anchors'])
            _guard('앵커', stage_anchors, HC, top, m)
        print('hero 단계 %s: %.1f초' % (st, time.time() - t0))
    print('hero 짓기 끝: 오브젝트 %d개, 실패 단계 %d개 %s' % (len(HC.all_objects), len(FAILED), FAILED))
    return top


FAILED = []


def _guard(label, fn, *a):
    """단계 하나가 실패해도 나머지는 짓는다(실패는 FAILED에 남기고 한국어로 알린다)"""
    import traceback
    try:
        return fn(*a)
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)[-1]
        FAILED.append('%s: %s (%s줄 %d)' % (label, e, tb.name, tb.lineno))
        print('hero 단계 실패 —', FAILED[-1])
        return None


# ───────────────────────── 검사·보고 ─────────────────────────
def screen_box(obs):
    xs, ys = [], []
    for ob in obs:
        if ob.type != 'MESH' or ob.hide_render:
            continue
        mw = ob.matrix_world
        n = len(ob.data.vertices)
        if n == 0:
            continue
        co = np.empty(n * 3, np.float32); ob.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        M = np.array(mw)
        w = co @ M[:3, :3].T + M[:3, 3]
        sx = R.K * (w @ np.array(R.RIGHT)); sy = -R.K * (w @ np.array(R.UP))
        xs += [float(sx.min()), float(sx.max())]; ys += [float(sy.min()), float(sy.max())]
    if not xs:
        return None
    return [round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2)]


def subtree(root, stop_roots=True):
    """루트 아래 메시(다른 _root 아래는 stop_roots면 뺀다)"""
    out = []
    def walk(o):
        for c in o.children:
            if stop_roots and c.name.endswith('_root'):
                continue
            out.append(c); walk(c)
    walk(root)
    return out


def layer_audit():
    """루트별 L0~L6 메시 수(빈 메시 0) · 조명 0 · Principled 0 · 받침/팔각/지층 0"""
    import re
    HC = bpy.data.collections.get(COLL)
    res = {}
    roots = [o for o in HC.all_objects if o.name.endswith('_root') and o.name != 'HERO_root']
    for rt in roots:
        cnt = {n: 0 for n in range(8)}
        empty = []
        for o in subtree(rt):
            mm = re.search(r'_L(\d)_', o.name)
            if not mm or o.type != 'MESH':
                continue
            if len(o.data.polygons) == 0:
                empty.append(o.name); continue
            cnt[int(mm.group(1))] += 1
        miss = [n for n in range(7) if cnt[n] == 0]
        res[rt.name] = {'L%d' % n: cnt[n] for n in range(7)} | {'missing': miss, 'empty': empty}
    lights = [o.name for o in bpy.data.objects if o.type == 'LIGHT']
    princ = []
    for ob in HC.all_objects:
        if ob.type != 'MESH':
            continue
        for ms in ob.material_slots:
            mt = ms.material
            if mt and mt.node_tree and any(n.type == 'BSDF_PRINCIPLED' for n in mt.node_tree.nodes):
                princ.append(mt.name)
    bad = [o.name for o in HC.all_objects if any(k in o.name.lower() for k in ('octa', 'strata', 'plinth', 'basering', 'cutaway', 'stratum'))]
    return {'roots': res, 'lights': lights, 'principled': sorted(set(princ)), 'base_like': bad}


def report():
    """실측 화면 상자·앵커·검사(JSON에 넣을 값)"""
    bpy.context.view_layer.update()
    HC = bpy.data.collections.get(COLL)
    g = bpy.data.objects.get
    out = {}
    colo = g('HERO_Colosseum_root'); lf = g('HERO_Life_root')
    out['colosseum_box'] = screen_box([o for o in subtree(colo, False)]) if colo else None
    out['life_box'] = screen_box([o for o in subtree(lf, False)]) if lf else None
    out['plaza_left'] = [o.name for o in bpy.data.objects if o.name.startswith('HERO_Plaza_')]     # 13:33 광장 제거: 0이어야 한다
    out['hero_group_box'] = screen_box([o for o in subtree(g('HERO_root'), False)]) if g('HERO_root') else None
    out['nero_base_box'] = screen_box(subtree(g('HERO_NeroBase_root'), False)) if g('HERO_NeroBase_root') else None
    out['nero_colossus_box'] = screen_box(subtree(g('HERO_NeroColossus_root'), False)) if g('HERO_NeroColossus_root') else None
    nb, nc = out['nero_base_box'], out['nero_colossus_box']
    if nb and nc:
        out['nero_box'] = [min(nb[0], nc[0]), min(nb[1], nc[1]), max(nb[2], nc[2]), max(nb[3], nc[3])]
    ws = g('HERO_Worksite_root')
    out['worksite_box'] = screen_box(subtree(ws, False)) if ws else None
    out['worksite_box_no_path'] = screen_box([o for o in subtree(ws, False) if not o.name.endswith('_L0_Pad')]) if ws else None
    out['anchors'] = {o.name[7:]: [round(v, 2) for v in R.scr(o.matrix_world.translation)] for o in HC.all_objects if o.name.startswith('ANCHOR_')}
    # 높이 검사: θ 구간별 외벽 최고 높이(칸 안 계단 포함)
    segs_max = {}
    table = [(100, 104, 41.0), (104, 108, 46.0), (108, 112, 50.0), (112, 205, 53.0), (205, 209, 44.0), (209, 322, 37.0), (322, 330, 31.0),
             (330, 338, 27.0), (338, 378, 24.5), (18, 72, 17.0), (72, 80, 30.0), (80, 100, 37.0)]
    for k in range(3600):
        s = C.E.L * k / 3600.0
        i = int(s / C.W) % C.NB; x = s - (i + 0.5) * C.W
        h = C.wall_top(i, x)
        th = C.E.az(s)
        for (a, b, ref) in table:
            t = th if not (b > 360 and th < 18) else th + 360
            if a <= t < b:
                key = '%d~%d' % (a, b % 360)
                segs_max[key] = max(segs_max.get(key, 0.0), h)
    out['wall_max_by_sector'] = segs_max
    out['h2_front_max'] = max(C.h2(C.E.az((i + 0.5) * C.W), i) for i in range(C.NB) if 10 <= C.E.az((i + 0.5) * C.W) % 360 < 80)
    # 나무 바닥 비율(경기장 u ≥ −2.0)
    a = C.A - CI.DP1; t = -CI.U_SPLIT / a
    out['wood_floor_frac'] = round(0.5 + (math.asin(t) + t * math.sqrt(1 - t * t)) / math.pi, 3)
    # 사람 키(화면 mm)
    hs = []
    for o in HC.all_objects:
        if o.type == 'MESH' and ('Person' in o.name or 'Worker' in o.name):
            hs.append(round(proto_h(o.data.name if o.data.name.startswith('P_') else 'person0') * o.scale.z, 2))
    out['person_h'] = [min(hs), max(hs), len(hs)] if hs else None
    out['audit'] = layer_audit()
    return out


# ───────────────────────── 보관: 12:49 철회로 짓지 않는 LocalBanana 조경 부품(build()에서 부르지 않는다) ─────────────────────────
# 사용자가 'LocalBanana와 같은 주변 조경'을 철회했다(설계 기준선 8.1). 앞선 워커가 쓴 코드를 버리지 않고(지침 6절) 여기에 둔다.
RETIRED_LAYOUT = {
    'col_ruins_L': (-67.1, 39.1), 'col_ruins_R': (42.3, -44.3), 'arch': (-15.0, 64.0), 'bricks_L': (-18.5, 78.5), 'bricks_F': (27.3, 60.8),
    'temple_small': (57.5, -47.5), 'temple6': (68.0, 8.0), 'gate_ruin': (40.0, -74.0),
}
LAYOUT = RETIRED_LAYOUT
def flutes(b3, x, y, r, z0, z1, angs=(-150, -120, -90, -60, -30, 0, 30), mi=0):
    """L3 기둥 홈(보이는 쪽 세로 줄)"""
    for a in angs:
        t = math.radians(a)
        LY.obox(b3, x + (r + 0.01) * math.cos(t), y + (r + 0.01) * math.sin(t), z0, 0.16, 0.07, z1 - z0, a + 90.0, mi)


def column_set(O, m, cols, seed):
    """cols: (x, y, r, z0, h, kind) kind: 'shaft' 부러진 몸통 · 'full' 주두까지 · 'stub' 밑동"""
    b2 = O.bm(2, 'Columns', [m['marble'], m['marble_lo']])
    b3 = O.bm(3, 'Flutes', [m['marble_lo']])
    b4 = O.bm(4, 'Broken', [m['marble'], m['marble_lo'], m['trav_blocks']])
    b5 = O.bm(5, 'Highlights', [m['hi']])
    for k, (x, y, r, z0, h, kind) in enumerate(cols):
        G.box(b2, x - r * 1.35, x + r * 1.35, y - r * 1.35, y + r * 1.35, z0, z0 + 0.3, 1)            # 주춧돌
        G.cyl(b2, x, y, r * 1.18, z0 + 0.3, z0 + 0.6, 14, 1, r_top=r * 1.05)                          # 토루스
        top = z0 + h
        if kind == 'full':
            G.cyl(b2, x, y, r, z0 + 0.6, top - 0.9, 14, 0, r_top=r * 0.9)
            G.cyl(b2, x, y, r * 0.95, top - 0.9, top - 0.45, 14, 1, r_top=r * 1.25)                   # 주두
            G.box(b2, x - r * 1.45, x + r * 1.45, y - r * 1.45, y + r * 1.45, top - 0.45, top, 1)      # 아바쿠스
            G.box(b5, x - r * 1.47, x + r * 1.47, y - r * 1.47, y + r * 1.47, top, top + 0.06, 0)
            flutes(b3, x, y, r * 0.95, z0 + 0.7, top - 1.0)
        else:
            G.cyl(b2, x, y, r, z0 + 0.6, top, 14, 0, r_top=r * 0.95)
            if kind == 'shaft':
                LY.obox(b4, x + 0.25 * r, y - 0.2 * r, top - 0.3, r * 1.2, r * 1.5, 0.55, 37.0 * k + seed, 0, (14.0, -9.0))   # 깨진 윗머리
            G.cyl(b5, x, y, r * 0.93, top, top + 0.05, 14, 0)
            if h > 2.0:
                flutes(b3, x, y, r * 0.97, z0 + 0.7, top - 0.15)


def build_col_ruins_L(HC, root, m):
    O = LY.Obj('HERO', 'ColumnRuinsL', HC, root, loc=pl(*LAYOUT['col_ruins_L']), rot=8.0)
    b0 = O.bm(0, 'Stylobate', [m['trav_blocks']])
    G.box(b0, -7.2, 7.2, -4.8, 4.8, 0.0, 0.8, 0)
    G.box(b0, -6.4, 3.8, -4.0, 4.0, 0.8, 1.4, 0)
    b1 = O.bm(1, 'Sockets', [m['deep'], m['soil_dk']], closed=False)
    LY.flat_poly(b1, [[(2.6 + 1.0 * math.cos(2 * math.pi * k / 12), 2.6 + 1.0 * math.sin(2 * math.pi * k / 12)) for k in range(12)]], 1.42, 0)   # 빠진 기둥 자리
    LY.flat_poly(b1, [[(-5.0, -4.75), (-4.6, -4.75), (-3.9, -4.1), (-4.3, -4.05)]], 0.82, 1)     # 갈라진 틈
    LY.flat_poly(b1, [[(4.6, -4.6), (5.2, -4.6), (6.6, 1.0), (6.2, 1.2)]], 0.82, 1)
    column_set(O, m, [(-4.4, 1.95, 1.3, 1.4, 15.0, 'shaft'), (-0.4, 2.0, 1.3, 1.4, 11.0, 'shaft'),
                      (-4.3, -1.95, 1.3, 1.4, 8.5, 'shaft'), (1.8, -1.7, 1.3, 1.4, 13.0, 'shaft')], 11.0)
    b4 = O.bm(4, 'Broken', [m['marble'], m['marble_lo'], m['trav_blocks']])
    LY.rod(b4, (8.8, -2.4, 1.3), (8.8, 1.3, 1.3), 1.3, 1.3, 14, 0)                              # 쓰러진 기둥 토막
    LY.rod(b4, (4.8, -6.6, 1.3), (8.0, -7.6, 1.3), 1.3, 1.3, 14, 0)
    LY.rod(b4, (-8.6, -6.2, 1.2), (-6.4, -7.0, 1.2), 1.2, 1.2, 14, 0)
    G.box(b4, -10.6, -8.4, 1.0, 3.2, 0.0, 0.9, 1)                                                # 쓰러진 주두
    G.cyl(b4, -9.5, 2.1, 1.25, 0.9, 1.5, 12, 1, r_top=0.9)
    for j in range(6):
        LY.obox(b4, -9.0 + 3.4 * j, 6.2 + 1.2 * R.hash01(j, 3), 0.0, 0.8 + 0.5 * R.hash01(j, 4), 0.6, 0.45, 50.0 * j, 2)
    b5 = O.bm(5, 'Highlights', [m['hi']])
    G.box(b5, -7.2, 7.2, -4.88, -4.76, 0.66, 0.84, 0); G.box(b5, 7.16, 7.28, -4.8, 4.8, 0.66, 0.84, 0)
    G.box(b5, -6.4, 3.8, -4.08, -3.96, 1.26, 1.44, 0); G.box(b5, 3.76, 3.88, -4.0, 4.0, 1.26, 1.44, 0)
    b6 = life_ring(O, m, 0.0, 0.0, 7.9, 5.4, 18, 3)
    LY.lump(b6, -5.4, -3.2, 0.85, 1.0, 0.6, 0.18, 5, 2); LY.lump(b6, 5.6, 3.0, 0.85, 0.9, 0.7, 0.16, 6, 2)
    LY.lump(b6, 1.0, -4.0, 1.42, 0.7, 0.4, 0.12, 7, 2)
    O.place('bush1', 9.6, 3.6, 0.0, 7.0, 30.0, 6, 'Bush')
    return O.done()


def build_col_ruins_R(HC, root, m):
    O = LY.Obj('HERO', 'ColumnRuinsR', HC, root, loc=pl(*LAYOUT['col_ruins_R']), rot=0.0)
    b0 = O.bm(0, 'Pedestal', [m['trav_blocks']])
    G.box(b0, -2.1, 2.1, -2.1, 2.1, 0.0, 2.6, 0)
    G.box(b0, -2.4, 2.4, -2.4, 2.4, 0.0, 0.45, 0)
    G.box(b0, -2.3, 2.3, -2.3, 2.3, 2.6, 2.9, 0)
    b1 = O.bm(1, 'Sockets', [m['deep']], closed=False)
    LY.flat_poly(b1, [[(4.6 + 1.0 * math.cos(2 * math.pi * k / 12), -0.6 + 1.0 * math.sin(2 * math.pi * k / 12)) for k in range(12)]], 0.03, 0)
    b1c = O.bm(1, 'Holes', [m['deep']])
    for (x, z) in ((-1.0, 1.4), (0.9, 0.9)):                                                     # 꺾쇠 구멍(앞면 −y)
        G.box(b1c, x - 0.2, x + 0.2, -2.14, -2.08, z - 0.2, z + 0.2, 0)
    column_set(O, m, [(0.0, 0.0, 1.35, 2.9, 15.5, 'full'), (5.2, 2.6, 1.25, 0.0, 2.2, 'stub'), (4.0, -3.8, 1.25, 0.0, 3.4, 'shaft')], 23.0)
    b4 = O.bm(4, 'Broken', [m['marble'], m['marble_lo'], m['trav_blocks']])
    LY.rod(b4, (-6.6, 1.6, 1.25), (-4.0, 4.0, 1.25), 1.25, 1.25, 14, 0)
    for j in range(4):
        LY.obox(b4, -4.0 + 2.6 * j, -5.4 - 0.8 * R.hash01(j, 5), 0.0, 0.7 + 0.4 * R.hash01(j, 6), 0.5, 0.4, 70.0 * j, 2)
    b5 = O.bm(5, 'Highlights', [m['hi']])
    G.box(b5, -2.3, 2.3, -2.38, -2.26, 2.75, 2.94, 0); G.box(b5, 2.26, 2.38, -2.3, 2.3, 2.75, 2.94, 0)
    life_ring(O, m, 1.0, 0.0, 6.2, 5.6, 16, 9)
    b6 = O.bm(6, 'Stains', [m['stain']])
    G.box(b6, -1.6, -1.25, -2.14, -2.1, 0.8, 2.5, 0); G.box(b6, 2.1, 2.14, 0.8, 1.1, 1.0, 2.5, 0)
    return O.done()


def arc_shell(bm, cx, zs, r_in, r_out, a0, a1, y0, y1, n, mi):
    """아치 안쪽 깊이색 판(호 a0→a1°, 반지름 r_in~r_out, 두께 방향 y0~y1) — 닫힌 입체"""
    def mk():
        for k in range(n):
            t0 = math.radians(a0 + (a1 - a0) * k / n); t1 = math.radians(a0 + (a1 - a0) * (k + 1) / n)
            pts = [(cx + r_in * math.cos(t0), zs + r_in * math.sin(t0)), (cx + r_out * math.cos(t0), zs + r_out * math.sin(t0)),
                   (cx + r_out * math.cos(t1), zs + r_out * math.sin(t1)), (cx + r_in * math.cos(t1), zs + r_in * math.sin(t1))]
            C.solid_from_2d(bm, pts, [], y0, y1)
    new_faces(bm, mk, mi)


def build_arch(HC, root, m):
    O = LY.Obj('HERO', 'Arch', HC, root, loc=pl(*LAYOUT['arch']), rot=0.0)
    b0 = O.bm(0, 'Mass', [m['trav_blocks']])
    G.wall_holes(b0, 'X', -6.0, 6.0, -2.2, 2.2, 0.0, 12.0, [('arch', -2.6, 2.6, 0.0, 6.4)], 0, n=14)
    G.box(b0, -6.3, 3.8, -2.4, 2.4, 12.0, 14.2, 0)                                               # 다락(오른쪽 끝 무너짐)
    G.box(b0, 3.8, 6.3, -2.4, 2.4, 12.0, 13.0, 0)
    b1 = O.bm(1, 'Depth', [m['trav_deep'], m['deep']])
    G.box(b1, -2.6, -2.55, -2.18, 2.18, 0.0, 6.4, 0)                                             # 왼쪽 문설주 안쪽(보이는 면)
    arc_shell(b1, 0.0, 6.4, 2.53, 2.58, 180.0, 112.0, -2.18, 2.18, 6, 0)                         # 홍예 안쪽 아랫부분
    for (x, z) in ((-4.6, 3.0), (-4.6, 7.6), (4.6, 2.4), (4.6, 8.8), (-6.0, 13.2)):
        y0_ = -2.46 if z > 12.0 else -2.25
        G.box(b1, x - 0.18, x + 0.18, y0_, y0_ + 0.08, z - 0.18, z + 0.18, 1)                      # 꺾쇠 구멍(중세에 쇠를 뽑아 간 자국)
    b2 = O.bm(2, 'Members', [m['trav'], m['marble']])
    for x in (-5.35, -3.45, 3.45, 5.35):
        G.box(b2, x - 0.65, x + 0.65, -2.85, -2.2, 0.0, 1.5, 0)                                   # 받침대
        G.cyl(b2, x, -2.3, 0.44, 1.5, 10.6, 12, 1, r_top=0.4)                                     # 붙은 기둥
        G.box(b2, x - 0.62, x + 0.62, -2.9, -2.2, 10.6, 11.0, 1)                                  # 주두
    G.box(b2, -6.2, 6.2, -2.7, -2.2, 11.0, 12.0, 0)                                              # 엔타블러처
    G.box(b2, 6.0, 6.3, -2.7, 2.4, 11.0, 12.0, 0)
    G.box(b2, -2.6, -2.3, -2.2, 2.2, 6.05, 6.45, 0); G.box(b2, 2.3, 2.6, -2.2, 2.2, 6.05, 6.45, 0)   # 홍예 받침 띠
    G.box(b2, -0.45, 0.45, -2.38, 2.38, 8.6, 9.8, 1)                                              # 쐐기돌
    G.box(b2, -6.45, 3.95, -2.62, 2.62, 13.9, 14.3, 0)                                            # 다락 코니스
    b3 = O.bm(3, 'Voussoirs', [m['marble_lo'], m['trav']])
    for k in range(9):
        t0 = math.pi - k * math.pi / 9 - 0.015; t1 = math.pi - (k + 1) * math.pi / 9 + 0.015
        if k == 4:
            continue
        pts = [(2.62 * math.cos(t0), 6.4 + 2.62 * math.sin(t0)), (3.55 * math.cos(t0), 6.4 + 3.55 * math.sin(t0)),
               (3.55 * math.cos(t1), 6.4 + 3.55 * math.sin(t1)), (2.62 * math.cos(t1), 6.4 + 2.62 * math.sin(t1))]
        new_faces(b3, lambda: C.solid_from_2d(b3, pts, [], -2.27, -2.19), k % 2)
    b4 = O.bm(4, 'Detail', [m['marble_lo'], m['marble'], m['trav_blocks']])
    G.box(b4, -5.5, -3.2, -2.5, -2.4, 12.35, 13.75, 0); G.box(b4, 1.2, 3.5, -2.5, -2.4, 12.35, 13.75, 0)   # 부조 판
    G.box(b4, -2.7, 0.9, -2.47, -2.4, 12.3, 13.8, 1)                                                    # 비문 판
    for (x, z) in ((-4.8, 12.7), (-4.0, 12.9), (2.0, 12.8), (2.8, 12.6)):
        LY.lump(b4, x, -2.52, z + 0.3, 0.28, 0.08, 0.45, x * 3 + z, 0)                                 # 부조 인물 자리
    LY.obox(b4, 4.9, 0.0, 12.9, 1.8, 4.2, 0.55, 0.0, 2, (0.0, 12.0))                                  # 다락 무너진 윗면 조각
    for j, (x, y, w, ang) in enumerate(((7.6, -3.2, 1.6, 20.0), (8.8, -1.0, 1.1, -15.0), (7.0, 3.0, 1.3, 40.0), (-7.6, -3.6, 1.0, 10.0))):
        LY.obox(b4, x, y, 0.0, w, w * 0.7, 0.75, ang, 2, (6.0 * (j % 2), 0.0))
    b5 = O.bm(5, 'Highlights', [m['hi']])
    G.box(b5, -6.2, 6.2, -2.78, -2.66, 11.7, 12.04, 0); G.box(b5, 6.26, 6.36, -2.7, 2.4, 11.7, 12.04, 0)
    G.box(b5, -6.45, 3.95, -2.7, -2.58, 13.96, 14.34, 0)
    G.box(b5, -0.45, 0.45, -2.42, 2.38, 9.8, 9.86, 0)
    for x in (-5.35, -3.45, 3.45, 5.35):
        G.box(b5, x - 0.65, x + 0.65, -2.93, -2.81, 1.3, 1.54, 0)
    b6 = life_ring(O, m, 0.0, 0.0, 6.6, 2.9, 16, 17)
    LY.lump(b6, -4.0, 0.0, 14.25, 1.2, 1.4, 0.3, 21, 2); LY.lump(b6, 1.8, 0.8, 14.25, 0.8, 1.0, 0.25, 22, 2)
    LY.lump(b6, 4.8, 0.6, 13.3, 0.8, 1.2, 0.3, 23, 0)
    b6s = O.bm(6, 'Stains', [m['stain']])
    for (x, z0, z1, w) in ((-4.05, 6.6, 10.9, 0.14), (4.05, 7.4, 10.9, 0.14), (5.88, 3.2, 10.9, 0.1)):
        G.box(b6s, x - w, x + w, -2.24, -2.19, z0, z1, 0)
    return O.done()


def brick_walls(HC, root, m, name, pX, pY, pieces, inner, rot=0.0, seed=0):
    """pieces: (x0, x1, y0, y1, h) 축 정렬 벽 토막. inner: 안뜰 사각형 (x0, x1, y0, y1) 또는 None"""
    O = LY.Obj('HERO', name, HC, root, loc=pl(pX, pY), rot=rot)
    b0 = O.bm(0, 'Walls', [m['brick']])
    b2 = O.bm(2, 'Coping', [m['trav'], m['trav_blocks']])
    b3 = O.bm(3, 'Courses', [m['trav']])
    b4 = O.bm(4, 'Broken', [m['brick'], m['core']])
    b5 = O.bm(5, 'Highlights', [m['hi']])
    for k, (x0, x1, y0, y1, h) in enumerate(pieces):
        G.box(b0, x0, x1, y0, y1, 0.0, h, 0)
        alx = (x1 - x0) >= (y1 - y0)
        L_ = (x1 - x0) if alx else (y1 - y0)
        if alx:                                                                                   # L2 트래버틴 밑돌 줄(보이는 면)
            G.box(b2, x0, x1, y0 - 0.06, y0 + 0.1, 0.0, 0.32, 1)
        else:
            G.box(b2, x1 - 0.1, x1 + 0.06, y0, y1, 0.0, 0.32, 1)
        if R.hash01(seed, k) > 0.45:                                                              # 트래버틴 갓돌
            G.box(b2, x0 - 0.06, x1 + 0.06, y0 - 0.06, y1 + 0.06, h, h + 0.2, 0)
        else:                                                                                     # 깨진 윗면(계단꼴 벽돌 + 속살)
            u0, u1 = 0.15 + 0.3 * R.hash01(seed, k, 1), 0.55 + 0.3 * R.hash01(seed, k, 2)
            if alx:
                G.box(b4, x0 + L_ * u0, x0 + L_ * u1, y0 + 0.05, y1 - 0.05, h, h + 0.45, 0)
                G.box(b4, x0 + L_ * (u0 + 0.1), x0 + L_ * (u1 - 0.12), y0 + 0.12, y1 - 0.12, h + 0.45, h + 0.62, 1)
            else:
                G.box(b4, x0 + 0.05, x1 - 0.05, y0 + L_ * u0, y0 + L_ * u1, h, h + 0.45, 0)
                G.box(b4, x0 + 0.12, x1 - 0.12, y0 + L_ * (u0 + 0.1), y0 + L_ * (u1 - 0.12), h + 0.45, h + 0.62, 1)
        for z in (0.95, 1.95, 2.95):                                                               # 보이는 두 면(−y·+x)의 띠 벽돌 줄
            if z + 0.3 > h:
                break
            if alx:
                G.box(b3, x0, x1, y0 - 0.03, y0 + 0.05, z, z + 0.14, 0)
            else:
                G.box(b3, x1 - 0.05, x1 + 0.03, y0, y1, z, z + 0.14, 0)
        if alx:
            G.box(b5, x0, x1, y0 - 0.05, y0 + 0.12, h - 0.02, h + 0.04, 0)
        else:
            G.box(b5, x1 - 0.12, x1 + 0.05, y0, y1, h - 0.02, h + 0.04, 0)
    for j in range(9):                                                                             # 무너진 벽돌 더미
        x = pieces[j % len(pieces)][1] + 0.6 * (R.hash01(seed, j, 3) - 0.3)
        y = pieces[j % len(pieces)][2] - 0.4 - 0.9 * R.hash01(seed, j, 4)
        LY.obox(b4, x, y, 0.0, 0.6, 0.32, 0.2 + 0.12 * (j % 2), 360.0 * R.hash01(seed, j, 5), 0)
    b1 = O.bm(1, 'Inner', [m['soil_dk'], m['soil']], closed=False)
    b6 = O.bm(6, 'Grass', [m['grass2'], m['grass1'], m['moss']])
    if inner:
        x0, x1, y0, y1 = inner
        LY.flat_poly(b1, [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]], 0.06, 0)
        b6g = O.bm(6, 'Lawn', [m['grass1']], closed=False)
        LY.flat_poly(b6g, [LY.blob(x0 * 0.3 + x1 * 0.7 - 1.0, (y0 + y1) / 2, (x1 - x0) * 0.32, (y1 - y0) * 0.38, 12, seed + 4.0, 0.25)], 0.09, 0)
        for j in range(10):
            LY.tuft(b6, x0 + (x1 - x0) * R.hash01(seed, j, 6), y0 + (y1 - y0) * R.hash01(seed, j, 7), 0.06, 0.6, seed * 50 + j, j % 2)
    else:
        xs = [p[0] for p in pieces] + [p[1] for p in pieces]; ys = [p[2] for p in pieces] + [p[3] for p in pieces]
        LY.flat_poly(b1, [[(min(xs) + 0.3, max(ys)), (max(xs) - 0.3, max(ys)), (max(xs) - 0.3, max(ys) + 2.6), (min(xs) + 0.3, max(ys) + 2.6)]], 0.06, 1)
    for k, (x0, x1, y0, y1, h) in enumerate(pieces):
        if R.hash01(seed, k, 8) > 0.5:
            LY.lump(b6, (x0 + x1) / 2, (y0 + y1) / 2, h + 0.1, 0.45, 0.45, 0.25, seed + k, 2)
        LY.tuft(b6, x1 + 0.4, y0 - 0.4, 0.0, 0.55, seed * 70 + k, k % 2)
    return O.done()


def build_temple_small(HC, root, m):
    O = LY.Obj('HERO', 'TempleSmall', HC, root, loc=pl(*LAYOUT['temple_small']), rot=0.0)
    # 앞면이 지역 −y(화면 왼-아래)를 본다. 기단 9 × 13, 신실 벽돌, 기둥 4(테트라스틸 프로스틸), 기와 박공지붕
    b0 = O.bm(0, 'Mass', [m['trav_blocks'], m['brick'], m['tile'], m['marble']])
    G.box(b0, -4.5, 4.5, -6.5, 6.5, 0.0, 2.2, 0)
    G.box(b0, -3.6, 3.6, -1.6, 6.0, 2.2, 9.0, 1)
    G.box(b0, -4.3, 4.3, -6.2, 6.3, 9.0, 10.1, 3)
    G.gable(b0, -4.3, 4.3, -5.95, 6.3, 10.1, 12.6, 'Y', 2, over=0.18)
    C.solid_from_2d(b0, [(-4.3, 10.1), (4.3, 10.1), (0.0, 12.55)], [], -6.22, -5.95)             # 박공 삼각면(대리석)
    for f in b0.faces:
        if f.material_index == 0 and f.calc_center_median().z > 10.05:
            f.material_index = 3
    b1 = O.bm(1, 'Depth', [m['trav_deep'], m['deep']])
    G.box(b1, -3.6, 3.6, -1.65, -1.58, 2.2, 9.0, 0)                                              # 현관 속(신실 앞벽)
    G.box(b1, -1.1, 1.1, -1.72, -1.6, 2.2, 6.6, 1)                                                # 문
    G.box(b1, -4.3, 4.3, -6.21, 6.3, 8.92, 9.0, 0)                                                # 현관 천장 밑(엔타블러처 밑면 띠)
    b2 = O.bm(2, 'Members', [m['marble'], m['marble_lo']])
    for x in (-3.45, -1.15, 1.15, 3.45):
        G.column(b2, x, -5.4, 0.5, 2.2, 9.0, 12, 0, 1)
    G.box(b2, -3.6, -2.9, -1.95, -1.5, 2.2, 9.0, 0); G.box(b2, 2.9, 3.6, -1.95, -1.5, 2.2, 9.0, 0)  # 안타 기둥
    G.box(b2, -4.45, 4.45, -6.36, 6.45, 9.85, 10.15, 1)                                           # 처마 코니스
    for sx in (-1, 1):
        pts = [(sx * 4.5, 10.0), (0.0, 12.62), (0.0, 12.92), (sx * 4.5, 10.3)]
        C.solid_from_2d(b2, pts if sx < 0 else pts[::-1], [], -6.36, -5.9)                       # 박공 사선 코니스
    b3 = O.bm(3, 'Pattern', [m['marble_lo'], m['tile']])
    for x in (-3.45, -1.15, 1.15, 3.45):
        flutes(b3, x, -5.4, 0.47, 2.9, 8.3, (-150, -120, -90, -60, -30, 0), 0)
    for j in range(14):
        y = -5.8 + 0.88 * j
        G.box(b3, -0.2, 0.2, y, y + 0.6, 12.55, 12.8, 1)                                          # 용마루 기와
    b4 = O.bm(4, 'Detail', [m['trav_blocks'], m['marble'], m['brick']])
    for k in range(5):
        G.box(b4, -3.0, 3.0, -6.5 - 0.44 * (5 - k), -6.5, 0.0, 0.44 * (k + 1), 0)                 # 앞 계단
    G.box(b4, -0.35, 0.35, -6.3, -5.9, 12.55, 13.3, 1)                                             # 아크로테리온
    G.box(b4, -4.5, -3.9, -6.3, -5.9, 10.1, 10.75, 1); G.box(b4, 3.9, 4.5, -6.3, -5.9, 10.1, 10.75, 1)
    G.box(b4, -1.35, -1.1, -1.76, -1.6, 2.2, 6.85, 1); G.box(b4, 1.1, 1.35, -1.76, -1.6, 2.2, 6.85, 1)
    G.box(b4, -1.35, 1.35, -1.76, -1.6, 6.6, 6.9, 1)                                               # 문틀
    LY.obox(b4, 5.7, 5.2, 0.0, 1.4, 1.0, 0.9, 25.0, 0); LY.obox(b4, 6.6, 3.4, 0.0, 0.9, 0.7, 0.6, -10.0, 0)
    b5 = O.bm(5, 'Highlights', [m['hi']])
    G.box(b5, -4.45, 4.45, -6.44, -6.32, 9.85, 10.18, 0); G.box(b5, 4.41, 4.51, -6.36, 6.45, 9.85, 10.18, 0)
    G.box(b5, -4.5, 4.5, -6.58, -6.46, 2.0, 2.24, 0); G.box(b5, 4.46, 4.58, -6.5, 6.5, 2.0, 2.24, 0)
    G.box(b5, -0.14, 0.14, -5.95, 6.3, 12.6, 12.86, 0)
    for k in range(5):
        y = -6.5 - 0.44 * (5 - k)
        G.box(b5, -3.0, 3.0, y - 0.06, y + 0.08, 0.44 * (k + 1) - 0.04, 0.44 * (k + 1) + 0.03, 0)
    b6 = life_ring(O, m, 0.0, 0.0, 5.2, 7.2, 20, 31)
    LY.lump(b6, 2.6, 2.4, 11.4, 1.0, 1.6, 0.22, 33, 2); LY.lump(b6, 1.4, -2.0, 12.0, 0.7, 1.0, 0.18, 34, 2)
    b6s = O.bm(6, 'Stains', [m['stain']])
    for x in (-2.2, 0.6, 3.1):
        G.box(b6s, x - 0.16, x + 0.16, -6.54, -6.49, 0.5, 1.9, 0)
    O.place('bush2', -5.6, 6.6, 0.0, 7.5, 10.0, 6, 'Bush')
    return O.done()


def build_temple6(HC, root, m):
    O = LY.Obj('HERO', 'Temple6', HC, root, loc=pl(*LAYOUT['temple6']), rot=0.0)
    # 기둥 줄이 지역 y를 따라가고 앞면이 +x(화면 오른-아래)를 본다
    b0 = O.bm(0, 'Podium', [m['trav_blocks']])
    G.box(b0, -3.8, 3.8, -11.4, 11.4, 0.0, 0.7, 0)
    G.box(b0, -3.2, 3.2, -10.8, 10.8, 0.7, 1.4, 0)
    G.box(b0, -2.6, 2.6, -10.2, 10.2, 1.4, 2.0, 0)
    ys = (-8.3, -5.0, -1.7, 1.7, 5.0, 8.3)
    cols = [(0.0, y, 0.72, 2.0, 12.0, 'full') for y in ys[:5]] + [(0.0, ys[5], 0.72, 2.0, 6.5, 'shaft')]
    column_set(O, m, cols, 41.0)
    b2 = O.bm(2, 'Entablature', [m['marble'], m['marble_lo']])
    G.box(b2, -1.05, 1.05, -9.3, 2.6, 14.0, 15.1, 0)                                              # 아키트레이브(기둥 1~4 위)
    G.box(b2, -1.25, 1.25, -9.5, -0.8, 15.1, 15.9, 1)                                             # 코니스 토막
    CI.prism_x(b2, [(-9.5, 15.9), (-4.0, 15.9), (-9.5, 18.3)], -1.1, 1.1)                         # 박공 모서리 조각
    b1 = O.bm(1, 'Depth', [m['deep'], m['trav_deep']])
    for y in (-5.05, 1.65):
        G.box(b1, 1.04, 1.09, y - 0.05, y + 0.05, 14.0, 15.1, 0)                                    # 아키트레이브 이음 틈
    for (y, z) in ((-7.2, 14.55), (-3.4, 14.5), (0.2, 14.6)):
        G.box(b1, 1.04, 1.1, y - 0.15, y + 0.15, z - 0.15, z + 0.15, 0)                             # 꺾쇠 구멍
    G.box(b1, 1.0, 1.08, 2.45, 2.6, 14.0, 15.1, 1)                                                  # 부러진 끝 단면(속)
    b3 = O.bm(3, 'Fasciae', [m['marble_lo']])
    G.box(b3, 1.05, 1.1, -9.3, 2.6, 14.32, 14.42, 0); G.box(b3, 1.05, 1.12, -9.3, 2.6, 14.68, 14.78, 0)
    b4 = O.bm(4, 'Broken', [m['marble'], m['marble_lo'], m['trav_blocks']])
    LY.rod(b4, (5.6, -6.8, 0.72), (5.6, -3.6, 0.72), 0.72, 0.72, 14, 0)
    LY.rod(b4, (4.8, 3.2, 0.7), (6.9, 5.2, 0.7), 0.7, 0.7, 14, 0)
    G.box(b4, 6.2, 7.8, 7.4, 9.0, 0.0, 0.6, 1); G.cyl(b4, 7.0, 8.2, 0.9, 0.6, 1.0, 12, 1, r_top=0.65)
    LY.obox(b4, 0.3, 3.6, 15.1, 1.8, 1.6, 0.5, 15.0, 1, (0.0, -14.0))
    for j in range(5):
        LY.obox(b4, 4.4 + 1.4 * R.hash01(j, 7), -10.0 + 4.6 * j, 0.0, 0.7 + 0.4 * R.hash01(j, 8), 0.55, 0.42, 60.0 * j, 2)
    b5 = O.bm(5, 'Highlights', [m['hi']])
    G.box(b5, 1.02, 1.15, -9.3, 2.6, 14.86, 15.14, 0); G.box(b5, 1.22, 1.35, -9.5, -0.8, 15.66, 15.94, 0)
    for (x, y, z) in ((3.8, 11.4, 0.7), (3.2, 10.8, 1.4), (2.6, 10.2, 2.0)):
        G.box(b5, x - 0.1, x + 0.06, -y, y, z - 0.1, z + 0.03, 0)
        G.box(b5, -x, x, -y - 0.06, -y + 0.1, z - 0.1, z + 0.03, 0)
    b6 = life_ring(O, m, 0.0, 0.0, 4.4, 12.0, 26, 43)
    LY.lump(b6, 2.8, -9.0, 0.72, 0.7, 1.4, 0.16, 44, 2); LY.lump(b6, -2.0, 6.0, 2.02, 0.6, 1.6, 0.14, 45, 2)
    LY.lump(b6, -0.4, -6.4, 15.92, 0.6, 1.2, 0.16, 46, 2)
    O.place('bush3', -5.2, -3.0, 0.0, 8.0, 50.0, 6, 'Bush'); O.place('bush0', -5.6, 7.4, 0.0, 7.0, 0.0, 6, 'Bush')
    return O.done()


def build_gate_ruin(HC, root, m):
    O = LY.Obj('HERO', 'GateRuin', HC, root, loc=pl(*LAYOUT['gate_ruin']), rot=0.0)
    b0 = O.bm(0, 'Wall', [m['brick']])
    G.box(b0, -6.0, -2.2, -0.8, 0.8, 0.0, 8.6, 0); G.box(b0, -6.0, -4.4, -0.8, 0.8, 8.6, 9.6, 0); G.box(b0, -4.4, -3.2, -0.8, 0.8, 8.6, 9.1, 0)
    G.box(b0, 2.2, 6.0, -0.8, 0.8, 0.0, 7.2, 0); G.box(b0, 3.6, 6.0, -0.8, 0.8, 7.2, 7.8, 0)
    G.box(b0, -2.2, 2.2, -0.8, 0.8, 6.8, 8.2, 0)
    b1 = O.bm(1, 'Depth', [m['deep'], m['trav_deep']])
    G.box(b1, -1.6, -1.55, -0.92, 0.92, 0.5, 6.0, 1)                                               # 문설주 안쪽(보이는 면)
    for (x, z) in ((-5.0, 3.0), (-3.4, 5.4), (4.2, 2.8), (3.0, 5.6), (-5.2, 7.4), (4.8, 6.4)):
        G.box(b1, x - 0.2, x + 0.2, -0.85, -0.78, z - 0.2, z + 0.2, 0)                             # 비계 구멍
    b2 = O.bm(2, 'Frame', [m['trav_blocks']])
    G.box(b2, -2.2, -1.6, -0.95, 0.95, 0.5, 6.0, 0); G.box(b2, 1.6, 2.2, -0.95, 0.95, 0.5, 6.0, 0)
    G.box(b2, -2.6, 2.6, -0.95, 0.95, 6.0, 6.8, 0); G.box(b2, -2.2, 2.2, -0.95, 0.95, 0.0, 0.5, 0)
    b3 = O.bm(3, 'Courses', [m['trav']])
    for (x0, x1, h) in ((-6.0, -2.2, 8.6), (2.2, 6.0, 7.2)):
        for z in (1.6, 3.4, 5.2, 7.0):
            if z + 0.4 < h:
                G.box(b3, x0, x1, -0.84, -0.78, z, z + 0.16, 0)
                if x1 > 0:
                    G.box(b3, x1 - 0.05, x1 + 0.03, -0.8, 0.8, z, z + 0.16, 0)                        # 오른쪽 끝면(+x)
    b4 = O.bm(4, 'Broken', [m['brick'], m['core']])
    for j in range(10):
        LY.obox(b4, 3.0 + 3.0 * R.hash01(j, 9), -1.6 - 1.4 * R.hash01(j, 10), 0.0, 0.6, 0.32, 0.22 + 0.1 * (j % 2), 360.0 * R.hash01(j, 11), 0)
    G.box(b4, -5.8, -4.6, -0.7, 0.7, 9.6, 9.85, 1); G.box(b4, 4.0, 5.6, -0.7, 0.7, 7.8, 8.0, 1)
    b5 = O.bm(5, 'Highlights', [m['hi']])
    G.box(b5, -2.6, 2.6, -1.02, -0.9, 6.62, 6.84, 0)
    for (x0, x1, h) in ((-6.0, -4.4, 9.6), (2.2, 3.6, 7.2), (3.6, 6.0, 7.8), (-2.2, 2.2, 8.2)):
        G.box(b5, x0, x1, -0.86, -0.72, h - 0.02, h + 0.04, 0)
    b6 = life_ring(O, m, 0.0, 0.0, 6.6, 1.6, 14, 51)
    LY.lump(b6, -5.2, 0.0, 9.65, 0.9, 0.8, 0.5, 52, 0); LY.lump(b6, 4.8, 0.0, 7.85, 0.8, 0.7, 0.45, 53, 1); LY.lump(b6, -0.4, 0.0, 8.25, 0.6, 0.6, 0.3, 54, 2)
    b6m = O.bm(6, 'Moss', [m['moss']])
    G.box(b6m, -5.6, -4.6, -0.84, -0.8, 0.2, 1.6, 0); G.box(b6m, 4.4, 5.6, -0.84, -0.8, 0.2, 1.1, 0)
    return O.done()

