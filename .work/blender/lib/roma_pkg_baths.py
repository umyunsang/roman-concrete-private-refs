# roma_pkg_baths — 카라칼라 욕장(절개, 뒤쪽)·수도교(아쿠아 안토니니아나: 2단 관통 아치·수로). 담당: baths
# 오브젝트마다 표현 레이어 L0~L6를 쌓는다. 이름: BATHS_{Obj}_L{n}_{part}, 루트 BATHS_{Obj}_root. 지침: .work/blender/지침-일러스트-모델.md
# 받침 없음(사용자 06:06 '8각형 받침대 제거'): 욕장은 지도 땅(Z=0) 위 0.3mm 포장 턱으로만 놓인다.
#   b5: 땅 속 기초(옛 Z −1.4~0)를 없앴다. 바닥판 밑면은 Z −0.05다. 그래서 다른 컬렉션을 숨긴 실루엣 렌더(export_sil)와
#   지도 렌더의 외곽·상자가 같다. 화면 상자는 보이는 모양으로 spec L3 [224, 94, 336, 190]에 맞는다.
# 좌표: 평면 지역 mm — X(화면 ↘)·Y(화면 ↙)·Z(위). Blender 지역 = (X, −Y, Z). 보이는 면: 윗면·+Y면(왼면)·+X면(오른면)
# 재질: roma_flat 평면색 × ISO_TONE만 쓴다(조명·AO·그림자·Principled·실사 텍스처 없음). L7 외곽선 없음(roma_flat.OUTLINE = False)
# b5(설계 d4 → d5) 바꾼 것: 대지 70.4×58.93(오른쪽 꼭짓점 = 수도교 기초선 시작 (336, 160)), 사람 키 2.4(D8), 물 PAL 'water'(D9),
#   냉탕실 교차 볼트(화면과 나란한 연직면으로 절개, 기점 = 열주 엔타블러처 윗면), 하이포코스트 기둥 열 L4, 수도교 d4 관통 아치
#   (아래 5.3·위 3.9, 아치 안쪽 면 1.5mm), 앵커 3개(ANCHOR_L3_label · ANCHOR_L4_label · ANCHOR_L4_m1)
import bpy, bmesh, math, json
from mathutils import Vector
import roma_kit as R, roma_flat as FL, roma_geo as G
try:
    import roma_props as RP
except Exception:
    RP = None
DECOR = False      # 16:14 사용자 결정(core 정보 오브젝트만): 욕장·수도교 둘레 사람·암포라·덤불·화분은 짓지 않는다(코드는 보관)
VAULT_TILT = False # 16:43 시험 결과: 기운 절개는 볼트 형태를 잃어 쓰지 않는다
BATHS = False      # 21:38 사용자: 카라칼라 욕장을 Core에서 지움 → 다음 빌드(b7)부터 욕장 건물·대지 0, 수도교만 짓는다(욕장·고도화 코드는 보관, True로 되살림)
GRAND = True       # 16:31 사용자 '레퍼런스 이미지랑 너무 달라': 욕장-참조.jpg의 장엄한 실내(기둥 숲·큰 청록 탕·코퍼 볼트·오큘러스 빛·목욕객)

COLL = 'LM_Baths'
SPEC = '/Users/um-yunsang/roman-concrete-private-refs/.work/design/current/out/spec.json'
PAGE_W = 420.0
P_H = 2.4                    # 사람 키(화면 mm, 발~머리): 표준 랜드마크 2.4(2.2~2.6) — 공통 결정 D8

# ── 욕장 대지 ─────────────────────────────────────────────────────────────────────────────
# 화면 상자 [224, 94, 336, 190]: 오른쪽 꼭짓점 (WX, 0, 0) = 수도교 기초선 시작 (336, 160)
#   c30·(WX + WY) = 112 → WX + WY = 129.33 · 아래 변 = 160 + WY/2 → WY 58.93(189.47) · 위 변 = 뒤 벽 바깥 꼭짓점 (2, 2, WH) → WH 32.8(94.0)
WX, WY, WH = 70.4, 58.93, 32.8
DX, DY = WX - 72.0, WY - 57.3    # 옛 대지(72 × 57.3) 좌표 중 오른쪽 변·앞 변에 붙은 것을 옮기는 양
FZ = 0.3                     # 바닥 포장 윗면(땅 위 턱 ≤ 0.3, 받침이 아니다)
FOUND = -0.05                # 바닥판 밑면(땅 윗면 바로 아래)
BATH_ORIGIN = (281.98, -33.98)   # 처음 놓는 자리(평면). build()가 fit_to_box 뒤 오른쪽 꼭짓점을 (336, 160)에 붙인다
SK = 0.45                    # 벽돌 겉켜 두께(겉은 벽돌, 속은 콘크리트)
BL_X = (2.0, 5.0)            # 뒤-왼쪽 벽(평면 X 두께). 안쪽 면 X=5가 보인다(오른면 톤)
BR_Y = (2.0, 5.0)            # 뒤-오른쪽 벽(평면 Y 두께). 안쪽 면 Y=5가 보인다(왼면 톤)
BL_END = WY - 6.8            # 뒤-왼쪽 벽 온전한 높이의 끝. 그 앞은 계단식 파손 → 앞 낮은 벽
BR_END = WX - 11.0           # 뒤-오른쪽 벽 끝(저수조에 닿는다)
FL_Y = (WY - 3.0, WY - 1.0)  # 앞-왼쪽 낮은 절개 벽
FR_X = (WX - 3.0, WX - 1.0)  # 앞-오른쪽 낮은 절개 벽
CIS = (WX - 11.0, WX, 0.0, 11.0)   # 저수조(대지 오른쪽 꼭짓점 = 수도교 시작점)
CIS_TOP = 26.0               # 저수조 윗면 = 수도교 높이
BAYS_BL = (11.8, 21.8, 31.8, 41.8)
PIL_BL = (6.8, 16.8, 26.8, 36.8, 46.8)
BAYS_BR1 = (10.3, 18.8, 27.3)
BAYS_BR2 = (10.3, 18.8, 27.3, 35.8, 44.3, 52.8)
PIL_BR = (6.05, 14.55, 23.05, 31.55, 40.05, 48.55, 57.05)
# ── 칼다리움(열탕실): 앞 반쪽을 절개. 절개면은 화면과 나란한 연직면 ──────────────────────────────
CXc, CYc = 46.0, 26.0
RI = 12.8                    # 안쪽 반지름(라벨: 돔 경간 약 36 m)
TW = 2.7                     # 드럼 벽 두께: 안 마감 0.45 + 콘크리트 1.8 + 겉 벽돌 0.45
DRUM_H = 19.0
FLOOR_C = 3.0                # 하이포코스트 위 바닥(수스펜수라) 윗면
SUS = 2.2                    # 수스펜수라 밑면 = 벽돌 기둥(필라이) 윗면
NF = 11                      # 남긴 반쪽의 다각 면 수(가운데 면이 뒤 정중앙)
A0, A1 = 45.0, 225.0         # 남긴 뒤쪽 반(Blender 방위, 도)
HO = 14.0                    # 돔 바깥 높이(안쪽은 반구)
R_OC = 1.6                   # 오큘러스 반지름(복원 추정: 형태만)
S2 = 1.0 / math.sqrt(2.0)
DV = (S2, -S2)               # 절개선 방향(평면): 화면 →
BV = (-S2, -S2)              # 절개면 뒤쪽(평면): 화면 ↑
# ── 냉탕실(프리기다리움) 교차 볼트: 정사각 칸 하나를 화면과 나란한 연직면(X + Y = VCUT)으로 절개 ───────────
#   실제는 세 칸 교차 볼트[S47]. 지도에는 열주 뒤 한 칸을 절개해 보인다. 기점 = 열주 엔타블러처 윗면(17.75)
VX0, VX1 = BL_X[1], BL_X[1] + 20.4     # 뒤-왼쪽 벽 안쪽 면 ~ 오른쪽 기둥(피어)
VY0, VY1 = 18.1, 38.5                  # 뒤 가장자리 ~ 열주 줄
VA = (VX1 - VX0) / 2.0                 # 10.2(반지름 = 반 경간)
VXC, VYC = VX0 + VA, VY0 + VA
VZS = 17.75                            # 기점
VT = 1.6                               # 껍질 두께(단면 띠가 화면 1.6mm로 읽힌다)
VFILL = 0.0                            # 귀퉁이 채움 없음: 얇은 껍질이라 바깥 면에 두 터널의 십자 등줄·대각 골이 보인다
VCUT = VXC + VYC + 1.2                 # 절개면: 대각 그로인(X + Y = 43.5)보다 1.2 앞
TH_R, TH_Z = 4.6, 21.8                 # 루넷의 반원 창(테르마이 창) 반지름·기점
# ── 수도교(spec aqueduct): 기초선 (336,160)→(424,210.8), 높이 26, 교각 간격 8 ────────────────────
AQ_PITCH, AQ_WLO, AQ_WHI, AQ_JAMB = 8.0, 5.3, 3.9, 1.5
AQ_LABEL_FREE = (53.0, 61.0)           # 수도교 라벨 블록 위(기초선 u 구간): 덤불·풀을 두지 않는다


# ═════════════════════════════════════ 재질 ═════════════════════════════════════
def _sock(coll, ident, name=None):
    for s in coll:
        if s.identifier == ident:
            return s
    return coll[name or ident]


def _voronoi(nt, vec_socket, scale):
    vo = nt.nodes.new('ShaderNodeTexVoronoi')
    try:
        vo.voronoi_dimensions = '3D'
    except Exception:
        pass
    try:
        vo.feature = 'F1'
    except Exception:
        pass
    nt.links.new(vec_socket, vo.inputs['Vector'])
    vo.inputs['Scale'].default_value = scale
    return vo


def _ramp2(nt, fac_socket, c1, c2):
    rp = nt.nodes.new('ShaderNodeValToRGB'); cr = rp.color_ramp; cr.interpolation = 'CONSTANT'
    cr.elements[0].position = 0.0; cr.elements[0].color = (*FL.srgb(c1), 1)
    e = cr.elements.new(0.5); e.color = (*FL.srgb(c2), 1)
    nt.links.new(fac_socket, rp.inputs['Fac'])
    return rp


def _mix(nt, fac, a, b):
    """RGBA 섞기: fac(소켓) · a·b는 소켓 또는 16진 색"""
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    nt.links.new(fac, _sock(mx.inputs, 'Factor_Float', 'Factor'))
    for key, v in (('A_Color', a), ('B_Color', b)):
        s = _sock(mx.inputs, key, key[0])
        if isinstance(v, str):
            s.default_value = (*FL.srgb(v), 1)
        else:
            nt.links.new(v, s)
    return _sock(mx.outputs, 'Result_Color', 'Result')


def spots(name, base, c1, c2, scale, thr):
    """콘크리트·경석 단면 무늬(L3): 또렷한 골재 점(Voronoi F1 거리 < thr, 셀마다 두 색) × ISO_TONE"""
    m, nt, tg = FL._base(name)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    vo = _voronoi(nt, tc.outputs['Object'], scale)
    lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'
    nt.links.new(_sock(vo.outputs, 'Distance'), lt.inputs[0]); lt.inputs[1].default_value = thr
    bw = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(_sock(vo.outputs, 'Color'), bw.inputs[0])
    rp = _ramp2(nt, bw.outputs[0], c1, c2)
    nt.links.new(_mix(nt, lt.outputs[0], base, rp.outputs['Color']), tg.inputs['Color'])
    m.diffuse_color = (*FL.srgb(base), 1)
    return m


def spots2(name, z_split, lo, hi, scale, thr):
    """두 켜 단면 무늬(L3): 지역 Z < z_split은 lo(바탕·점1·점2), 위는 hi — 볼트 아래 응회암 · 위 경석[S47]"""
    m, nt, tg = FL._base(name)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    vo = _voronoi(nt, tc.outputs['Object'], scale)
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sep.inputs[0])
    gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'
    nt.links.new(sep.outputs['Z'], gt.inputs[0]); gt.inputs[1].default_value = z_split
    lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'
    nt.links.new(_sock(vo.outputs, 'Distance'), lt.inputs[0]); lt.inputs[1].default_value = thr
    bw = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(_sock(vo.outputs, 'Color'), bw.inputs[0])
    r_lo = _ramp2(nt, bw.outputs[0], lo[1], lo[2]); r_hi = _ramp2(nt, bw.outputs[0], hi[1], hi[2])
    dots = _mix(nt, gt.outputs[0], r_lo.outputs['Color'], r_hi.outputs['Color'])
    base = _mix(nt, gt.outputs[0], lo[0], hi[0])
    nt.links.new(_mix(nt, lt.outputs[0], base, dots), tg.inputs['Color'])
    m.diffuse_color = (*FL.srgb(lo[0]), 1)
    return m


def mats():
    def fl(n, h):
        return FL.flat('F_baths_' + n, h)

    def bl(n, *a):
        return FL.blocks('F_baths_' + n, *a)
    W = FL.PAL.get('water', '#7FB3BD')        # 물은 PAL 'water' 한 값(hero·ground·coast와 같다, D9)
    M = {}
    # L0·L3 바탕(무늬가 든 평면색)
    M['brick'] = bl('brick', '#AE6142', '#C27753', '#B86A48', '#94563B', 0.9, 0.3, 0.06)
    M['brick_aq'] = bl('brick_aq', '#B5573A', '#CE6E48', '#C2603D', '#8F4429', 0.9, 0.3, 0.06)   # 지면보다 채도 2배 이상
    M['aq_stone'] = bl('aq_stone', '#CE9E6A', '#C3925F', '#D8AA76', '#A27A50', 2.0, 1.0, 0.05)   # 수도교 마름돌(d4 돌색)
    M['core'] = spots('F_baths_core', '#A39482', '#7E705F', '#C4B094', 1.4, 0.3)          # 콘크리트(무거운 골재)
    M['tuffcrete'] = spots('F_baths_tuffcrete', '#B9A587', '#97846C', '#CDBB9B', 1.6, 0.3)  # 응회암 골재 콘크리트
    M['pumice'] = spots('F_baths_pumice', '#D6CAAA', '#B8AA88', '#E8DFC8', 1.9, 0.32)     # 돔 위쪽 가벼운 경석
    M['vsec'] = spots2('F_baths_vsec', VZS + 0.45 * VA, ('#B9A587', '#97846C', '#CDBB9B'), ('#D6CAAA', '#A8957A', '#E8DFC8'), 1.7, 0.31)
    M['dado'] = bl('dado', '#E9E0CC', '#DCCBAE', '#F0E9DA', '#C2AD8B', 2.6, 1.3, 0.04)
    M['floor'] = (bl('floor', '#E9DCC0', '#CDB07A', '#E8D2C6', '#9C6B55', 2.0, 2.0, 0.07) if GRAND
                  else bl('floor', '#E6DAC2', '#D8C8AA', '#EDE4D2', '#C4AF8C', 2.4, 2.4, 0.035))
    M['frig'] = (bl('frig', '#D8B05A', '#E6D3C8', '#A9B994', '#8E3E35', 1.6, 1.6, 0.09) if GRAND        # 16:31 색 대리석 바닥(오푸스 섹틸레)
                 else bl('frig', '#EDE6D6', '#D9CCB2', '#F3EEE2', '#CDBD9F', 3.2, 1.6, 0.035))
    M['mosaic'] = bl('mosaic', '#E8DCC4', '#CDB892', '#F0E8D8', '#BFA780', 0.9, 0.9, 0.05)
    M['mosaic2'] = bl('mosaic2', '#F1EADB', '#4A3D33', '#E6DCC8', '#9C8B74', 1.1, 1.1, 0.06)
    M['tile'] = bl('tile', '#B8694A', '#C9805C', '#A85E40', '#8E4E35', 1.4, 0.25, 0.06)
    M['drum_in'] = bl('drum_in', '#E8DCC4', '#DDCDAF', '#EEE5D3', '#CDBA98', 1.8, 0.9, 0.035)
    M['vault_in'] = (bl('vault_in', '#B9A07A', '#B39A73', '#BFA781', '#F4ECDA', 1.5, 1.5, 0.24) if GRAND   # 16:31 코퍼(짙은 칸 + 밝은 살)
                     else bl('vault_in', '#E4D5B8', '#D9C8A8', '#EADFC8', '#C8B28E', 2.2, 1.1, 0.035))   # 볼트 안쪽 회반죽(줄눈)
    M['vroof'] = bl('vroof', '#D9C49E', '#CEB68E', '#E2CFAC', '#B79B73', 1.6, 0.8, 0.045)         # 볼트 바깥 회반죽 마감(돔 바깥과 같은 계열, 벽돌 벽과 구분)
    M['marble'] = fl('marble', '#EFE8DA')
    M['marble_lo'] = fl('marble_lo', '#DCCFB8')
    M['granite'] = fl('granite', '#BCA497')
    M['porphyry'] = fl('porphyry', '#8E3E35')
    M['giallo'] = fl('giallo', '#D8B05A')          # 색 대리석 판(L3): 지알로 안티코·베르데·파보나체토
    M['verde'] = fl('verde', '#7C9A6E')
    M['pavo'] = fl('pavo', '#E6D3C8')
    M['trav'] = fl('trav', '#D8B98E')
    M['aq_trav'] = fl('aq_trav', '#E0BC8A')          # 수도교 띠돌(돌색보다 밝게)
    M['coffer'] = fl('coffer', '#B6976C' if GRAND else '#D5C2A0')          # 16:43 코퍼 칸을 짙게(살과 대비)
    M['coffer_rib'] = fl('coffer_rib', '#F2E7D0' if GRAND else '#EADDC3')
    M['dome_out'] = fl('dome_out', '#CDB28D')
    # L1 깊이색
    M['deep'] = fl('deep', '#6B4635')
    M['deeper'] = fl('deeper', '#4E3124')
    M['jamb'] = fl('jamb', '#9A573C')                # 홍예 옆면(그늘진 벽돌색)
    M['aq_stone_lo'] = fl('aq_stone_lo', FL.shade('#CE9E6A', 0.76))   # 관통 아치 안쪽 면(돌 깊이색, d4 0.78)
    M['vault_lo'] = fl('vault_lo', '#C9B48F')        # 볼트 귀퉁이 안쪽 깊이색
    # L4 형태 디테일
    M['glass'] = fl('glass', '#FFF6E0')              # 큰 창으로 드는 빛(빛은 큰 창 중심)
    M['water'] = fl('water', W)
    M['signinum'] = fl('signinum', '#D99A84')        # 수로 안 방수 모르타르(분홍 회반죽)
    M['bronze'] = fl('bronze', '#9A7443')
    M['lead'] = fl('lead', '#A39E95')
    M['fire'] = fl('fire', '#FF9A3C')
    M['fire_hi'] = fl('fire_hi', '#FFE07A')
    M['wood'] = fl('wood', '#A97B4F')
    M['wood_dk'] = fl('wood_dk', '#7E5A39')
    M['statue'] = fl('statue', '#F4F0E8')
    M['tile_band'] = fl('tile_band', '#D88A63')
    M['aq_band'] = fl('aq_band', '#B9895A')          # 수도교 마름돌 줄눈 강조(L3)
    M['aq_blk2'] = fl('aq_blk2', '#C08C5A')          # 마름돌 색 변화(L3)
    M['aq_blk3'] = fl('aq_blk3', '#DCB07C')
    # L5 하이라이트(면색 명도 +10~15%)
    M['hl_brick'] = fl('hl_brick', '#E3A07E')
    M['hl_marble'] = fl('hl_marble', '#FFFDF6')
    M['hl_trav'] = fl('hl_trav', '#F6E6C8')
    M['hl_stone'] = fl('hl_stone', FL.shade('#CE9E6A', 1.15, '#FFF4DC'))
    M['hl_vault'] = fl('hl_vault', '#F4EAD6')
    M['water_hi'] = fl('water_hi', FL.shade(W, 1.45))
    M['hl_bronze'] = fl('hl_bronze', '#D2A866')
    # L6 얼룩·식생·생활
    M['moss'] = fl('moss', '#8E9A52')
    M['stain'] = fl('stain', '#965640')
    M['stain_st'] = fl('stain_st', '#A9845A')        # 돌면 빗물 자국
    M['soot'] = fl('soot', '#3E2A20')                # 하이포코스트 그을음
    M['calcite'] = fl('calcite', '#F1EDE2')
    M['steam'] = fl('steam', '#F4EEE2')            # 16:43 김: 크림색, 위로 갈수록 연하게
    M['steam2'] = fl('steam2', '#F8F4EC')
    M['steam3'] = fl('steam3', '#FCFAF5')
    M['revet'] = bl('revet', '#EFE5D0', '#E6D9BF', '#F4ECDC', '#CDBB98', 3.0, 1.5, 0.04)   # 16:31 안벽 대리석 판
    if GRAND:                                       # 코퍼·오푸스 섹틸레는 격자(벽돌 엇갈림 0)
        for k in ('vault_in', 'frig', 'floor'):
            for nd in M[k].node_tree.nodes:
                if nd.type == 'TEX_BRICK':
                    nd.offset = 0.0
    M['pool_tq'] = fl('pool_tq', '#62C2C0')          # 16:31 레퍼런스 청록 탕물
    M['pool_deep'] = fl('pool_deep', '#3F9DA3')      # L1 깊은 물
    M['pool_hi'] = fl('pool_hi', '#B4EAE3')          # L5 물빛
    M['light'] = fl('light', '#FFF6E2')              # L5 오큘러스 빛(방출 평면색, 조명 아님)
    M['light2'] = fl('light2', '#FBE5B4')
    M['light3'] = fl('light3', '#FFF9EA')            # 빛 한가운데·물 위 반사 원판
    M['towel'] = fl('towel', '#F3EEE2')
    M['terra'] = fl('terra', '#B4623E')
    M['terra_dk'] = fl('terra_dk', '#94502F')
    M['ivy'] = fl('ivy', '#4C6A34')
    M['ivy2'] = fl('ivy2', '#5F7F3E')
    M['ivy_hi'] = fl('ivy_hi', '#8FA85A')
    return M


# ═════════════════════════════════════ 레이어 도구 ═════════════════════════════════════
def _close(bm, A, Bv, mi):
    """두 단면 꼭짓점 줄(A·B)로 닫힌 판"""
    fs = []
    for vs in (A, Bv[::-1]):
        try:
            fs.append(bm.faces.new(vs))
        except ValueError:
            pass
    n = len(A)
    for k in range(n):
        k2 = (k + 1) % n
        try:
            fs.append(bm.faces.new([A[k], A[k2], Bv[k2], Bv[k]]))
        except ValueError:
            pass
    for f in fs:
        f.material_index = mi
    G.uv_box(bm, fs)
    return fs


def dedup(pts, eps=1e-6):
    out = []
    for p in pts:
        if not out or abs(out[-1][0] - p[0]) > eps or abs(out[-1][1] - p[1]) > eps:
            out.append(p)
    if len(out) > 2 and abs(out[0][0] - out[-1][0]) <= eps and abs(out[0][1] - out[-1][1]) <= eps:
        out.pop()
    return out


def arch_outline(u0, u1, zb, zs, n=10):
    rr = (u1 - u0) / 2.0; cu = (u0 + u1) / 2.0
    return dedup([(u0, zb), (u1, zb)] + [(cu + rr * math.cos(math.pi * k / n), zs + rr * math.sin(math.pi * k / n)) for k in range(n + 1)])


def rect(u0, u1, z0, z1):
    return [(u0, z0), (u1, z0), (u1, z1), (u0, z1)]


class Lay:
    """표현 레이어 하나 = 메시 하나(재질 여러 개). 입력은 평면 지역 mm(X, Y, Z)"""
    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.mats, self.ix = [], {}

    def mi(self, m):
        if m.name not in self.ix:
            self.ix[m.name] = len(self.mats); self.mats.append(m)
        return self.ix[m.name]

    def box(self, m, X0, X1, Y0, Y1, Z0, Z1):
        if X1 - X0 < 1e-5 or Y1 - Y0 < 1e-5 or Z1 - Z0 < 1e-5:
            return []
        return G.box(self.bm, X0, X1, -Y1, -Y0, Z0, Z1, self.mi(m))

    def prism(self, m, pts, Z0, Z1):
        q = [(x, -y) for x, y in pts]
        a = sum(q[i][0] * q[(i + 1) % len(q)][1] - q[(i + 1) % len(q)][0] * q[i][1] for i in range(len(q)))
        if a < 0:
            q = q[::-1]
        return G.prism(self.bm, q, Z0, Z1, self.mi(m))

    def cyl(self, m, X, Y, r, Z0, Z1, n=12, r_top=None):
        return G.cyl(self.bm, X, -Y, r, Z0, Z1, n, self.mi(m), r_top=r_top, top=True, bottom=True)

    def obox(self, m, X, Y, ex, ey, u0, u1, v0, v1, Z0, Z1):
        """기운 상자: 평면 원점 (X, Y), 평면 단위 축 ex·ey"""
        pts = [(X + ex[0] * u + ey[0] * v, Y + ex[1] * u + ey[1] * v) for (u, v) in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]
        return self.prism(m, pts, Z0, Z1)

    def vplate(self, m, ox, oy, ex, ey, pts, t0, t1):
        """세운 판: (u, z) 볼록 다각형을 ey 방향 t0..t1로 민다. 평면 = (ox, oy) + ex·u + ey·t"""
        bm = self.bm

        def V(u, z, t):
            return bm.verts.new((ox + ex[0] * u + ey[0] * t, -(oy + ex[1] * u + ey[1] * t), z))
        pts = dedup(pts)
        A = [V(u, z, t0) for (u, z) in pts]
        Bv = [V(u, z, t1) for (u, z) in pts]
        return _close(bm, A, Bv, self.mi(m))

    def wall_x(self, m, X0, X1, Y0, Y1, Z0, Z1, holes=()):
        """평면 X 방향 벽(두께 Y0..Y1). holes: [('arch', X_u0, X_u1, z밑, z홍예)]"""
        return G.wall_holes(self.bm, 'X', X0, X1, -Y1, -Y0, Z0, Z1, list(holes), self.mi(m))

    def wall_y(self, m, X0, X1, Y0, Y1, Z0, Z1, holes=()):
        """평면 Y 방향 벽(두께 X0..X1). holes의 u는 평면 Y"""
        hh = [(k, -u1, -u0, zb, zs) for (k, u0, u1, zb, zs) in holes]
        return G.wall_holes(self.bm, 'Y', -Y1, -Y0, X0, X1, Z0, Z1, hh, self.mi(m))

    def obj(self, coll, parent):
        if not self.bm.faces:
            self.bm.free()
            return None
        return R.bm_to_obj(self.bm, self.name, self.mats, coll, parent, False, recalc=True)


LAYER_NAMES = ('L0_Mass', 'L1_Depth', 'L2_Members', 'L3_Pattern', 'L4_Detail', 'L5_Highlight', 'L6_Life')


def layers(obj):
    return {n[:2]: Lay('BATHS_%s_%s' % (obj, n)) for n in LAYER_NAMES}


class Facet:
    """드럼(원통 벽)의 평평한 한 면. 지역 (u 접선, t 바깥쪽, z) → Blender 지역. 옆면은 방사선에 맞춘다(마름질)"""
    def __init__(self, cx, cy, phi_c, dphi, ra):
        h = math.radians(dphi) / 2.0
        self.a = ra * math.cos(h); self.half = ra * math.sin(h)
        p = math.radians(phi_c)
        self.n = (math.cos(p), math.sin(p)); self.tg = (math.sin(p), -math.cos(p))
        self.c = (cx, cy)

    def P(self, u, t, z):
        k = (self.a + t) / self.a
        return Vector((self.c[0] + self.n[0] * (self.a + t) + self.tg[0] * u * k,
                       self.c[1] + self.n[1] * (self.a + t) + self.tg[1] * u * k, z))

    def plan(self, u, t):
        v = self.P(u, t, 0.0)
        return (v.x, -v.y)


def facet_wall(lay, m, F, t0, t1, z0, z1, holes=()):
    bm = lay.bm
    n0 = len(bm.verts)
    G.wall_holes(bm, 'X', -F.half, F.half, t0, t1, z0, z1, list(holes), lay.mi(m))
    bm.verts.ensure_lookup_table()
    for v in bm.verts[n0:]:
        v.co = F.P(v.co.x, v.co.y, v.co.z)


def facet_plate(lay, m, F, pts, t0, t1):
    bm = lay.bm
    pts = dedup(pts)
    A = [bm.verts.new(F.P(u, t0, z)) for (u, z) in pts]
    Bv = [bm.verts.new(F.P(u, t1, z)) for (u, z) in pts]
    return _close(bm, A, Bv, lay.mi(m))


def cf(u, v):
    """칼다리움 틀(u: 절개선 방향, v: 절개면 뒤쪽) → 평면 지역"""
    return (CXc + DV[0] * u + BV[0] * v, CYc + DV[1] * u + BV[1] * v)


def statue(lay, m, X, Y, Z, h, heroic=False):
    """대리석 조각상(L4): 옷자락·몸통·목·머리·한쪽 팔"""
    r0 = (0.42 if heroic else 0.3) * h / 4.4
    lay.cyl(m, X, Y, r0, Z, Z + 0.45 * h, 8, r_top=r0 * 0.85)
    lay.cyl(m, X, Y, r0 * 0.88, Z + 0.45 * h, Z + 0.78 * h, 8, r_top=r0 * 1.08)
    lay.cyl(m, X, Y, r0 * 0.42, Z + 0.78 * h, Z + 0.83 * h, 6)
    lay.cyl(m, X, Y, r0 * 0.62, Z + 0.83 * h, Z + h, 8, r_top=r0 * 0.5)
    lay.box(m, X + r0 * 0.85, X + r0 * 1.35, Y - 0.1 * h / 4.4, Y + 0.1 * h / 4.4, Z + 0.5 * h, Z + 0.76 * h)
    if heroic:      # 몽둥이(파르네세 헤라클레스)
        lay.box(m, X - r0 * 1.5, X - r0 * 1.05, Y - 0.12, Y + 0.12, Z, Z + 0.55 * h)


def place(GC, root, proto, X, Y, Z, s, rot, name):
    if not DECOR:            # 16:14 core만: 원형 소품(사람·암포라·덤불)은 짓지 않는다
        return None
    if RP is None or bpy.data.objects.get(proto) is None:
        return None
    return RP.place(proto, X, -Y, Z, s, rot, GC, name=name, parent=root, local=True)


def person(GC, root, i, X, Y, Z, name):
    """사람(L6): 원형 키 1.0 × P_H. 루트 축척은 build()가 맞춘 뒤 되돌려 곱한다(화면 키 = P_H)"""
    return place(GC, root, 'P_person%d' % (i % 3), X, Y, Z, P_H, 47.0 * i + 13.0, name)


# ═════════════════════════════════════ 욕장 ═════════════════════════════════════
FR_BL = (BL_X[1], 0.0, (0.0, 1.0), (1.0, 0.0))     # 뒤-왼쪽 벽 안쪽 면 틀: u = 평면 Y, t = 방 쪽(+X)
FR_BR = (0.0, BR_Y[1], (1.0, 0.0), (0.0, 1.0))     # 뒤-오른쪽 벽 안쪽 면 틀: u = 평면 X, t = 방 쪽(+Y)


def fbox(lay, m, fr, u0, u1, t0, t1, z0, z1):
    ox, oy, ex, ey = fr
    return lay.obox(m, ox, oy, ex, ey, u0, u1, t0, t1, z0, z1)


def fplate(lay, m, fr, pts, t0, t1):
    ox, oy, ex, ey = fr
    return lay.vplate(m, ox, oy, ex, ey, pts, t0, t1)


def fpt(fr, u, t):
    ox, oy, ex, ey = fr
    return (ox + ex[0] * u + ey[0] * t, oy + ex[1] * u + ey[1] * t)


def lunette_z(u):
    """뒤-왼쪽 벽(X = VX0) 위 볼트 루넷 곡선(안쪽 면 높이). 칸 Y 범위 밖이면 None"""
    d = u - VYC
    if abs(d) >= VA:
        return None
    return VZS + math.sqrt(VA * VA - d * d)


def zcap(fr, u0, u1):
    """벽면 부재가 볼트 안쪽 면과 겹치지 않는 최고 높이. 뒤-왼쪽 벽의 칸 범위 [VY0, VY1]에만 적용(그 밖은 제한 없음)"""
    if fr is not FR_BL or u1 <= VY0 or u0 >= VY1:
        return 1e9
    a, b = max(u0, VY0 + 1e-4), min(u1, VY1 - 1e-4)
    return min(lunette_z(a), lunette_z(b))      # 루넷 곡선은 위로 볼록 → 구간 끝에서 가장 낮다


def segs_minus(a, b, cuts):
    segs = [(a, b)]
    for c0, c1 in cuts:
        nxt = []
        for s0, s1 in segs:
            if c1 <= s0 or c0 >= s1:
                nxt.append((s0, s1)); continue
            if c0 > s0:
                nxt.append((s0, c0))
            if c1 < s1:
                nxt.append((c1, s1))
        segs = nxt
    return [(s0, s1) for (s0, s1) in segs if s1 - s0 > 0.05]


def vault_band_cuts(fr, ztop):
    """높이 ztop까지 오는 띠(코니스)가 볼트에 닿는 구간: 칸 끝 쪽 두 구간"""
    if fr is not FR_BL:
        return []
    h = ztop + 0.1 - VZS
    w = math.sqrt(max(0.0, VA * VA - h * h)) if h < VA else 0.0
    return [(VY0 - 0.02, VYC - w), (VYC + w, VY1 + 0.02)]


def niche(L, M, fr, uc, z0=FZ):
    """벽감 + 작은 기둥 두 개 + 박공 + 대리석 조각상(욕장 참조 이미지)"""
    fbox(L['L2'], M['marble_lo'], fr, uc - 1.9, uc + 1.9, 0.0, 0.9, z0, 0.9)                      # 받침단
    fplate(L['L1'], M['deep'], fr, arch_outline(uc - 1.3, uc + 1.3, 0.9, 5.4), 0.0, 0.2)        # 벽감 속(깊이색)
    for s in (-1, 1):
        X, Y = fpt(fr, uc + s * 1.55, 0.45)
        L['L2'].cyl(M['marble'], X, Y, 0.2, 0.9, 6.0, 8)
        fbox(L['L2'], M['marble'], fr, uc + s * 1.55 - 0.28, uc + s * 1.55 + 0.28, 0.17, 0.73, 6.0, 6.25)
    fbox(L['L2'], M['marble'], fr, uc - 1.95, uc + 1.95, 0.0, 0.8, 6.25, 6.75)                   # 엔타블러처
    fplate(L['L2'], M['marble_lo'], fr, [(uc - 1.95, 6.75), (uc + 1.95, 6.75), (uc, 7.6)], 0.0, 0.7)   # 박공
    fbox(L['L5'], M['hl_marble'], fr, uc - 1.95, uc + 1.95, 0.6, 0.8, 6.75, 6.8)
    X, Y = fpt(fr, uc, 0.55)
    statue(L['L4'], M['statue'], X, Y, 0.9, 4.3)


def window_set(L, M, fr, uc, w, zb, zs, mid, bars=True, sill=True, ring=True):
    """창(벽 구멍은 L0에서 뚫는다): 빛 판(벽 두께 가운데) · 창살 · 창턱 · 홍예 테"""
    fplate(L['L4'], M['glass'], fr, arch_outline(uc - w / 2, uc + w / 2, zb, zs), mid - 0.03, mid + 0.03)
    if bars:
        crown = zs + w / 2
        for s in (-1, 1):
            fplate(L['L4'], M['deep'], fr, rect(uc + s * w / 6 - 0.07, uc + s * w / 6 + 0.07, zb, crown - 0.25), mid + 0.03, mid + 0.1)
        fplate(L['L4'], M['deep'], fr, rect(uc - w / 2, uc + w / 2, zs - 0.07, zs + 0.07), mid + 0.03, mid + 0.1)
    if sill:
        fbox(L['L2'], M['marble'], fr, uc - w / 2 - 0.25, uc + w / 2 + 0.25, 0.0, 0.35, zb - 0.25, zb)
        fbox(L['L5'], M['hl_marble'], fr, uc - w / 2 - 0.25, uc + w / 2 + 0.25, 0.2, 0.35, zb, zb + 0.05)
    if ring:
        r1, r2 = w / 2 + 0.05, w / 2 + 0.45
        n = 7 if w < 6.0 else 11
        for k in range(n):
            a0, a1 = math.pi * k / n, math.pi * (k + 1) / n
            pts = [(uc + r1 * math.cos(a0), zs + r1 * math.sin(a0)), (uc + r2 * math.cos(a0), zs + r2 * math.sin(a0)),
                   (uc + r2 * math.cos(a1), zs + r2 * math.sin(a1)), (uc + r1 * math.cos(a1), zs + r1 * math.sin(a1))]
            fplate(L['L2'], M['marble_lo'] if k % 2 else M['marble'], fr, pts, 0.0, 0.12)


def thermal_window(L, M, fr, uc, r, zb, mid):
    """루넷의 반원 창(테르마이 창): 빛 판 + 세로 창살 2개(빛 세 칸) + 창턱 + 홍예 테"""
    window_set(L, M, fr, uc, 2 * r, zb, zb, mid, bars=False)
    for s in (-1, 1):
        u = uc + s * r / 3.0
        top = zb + math.sqrt(max(0.0, r * r - (r / 3.0) ** 2)) - 0.05
        fplate(L['L4'], M['deep'], fr, rect(u - 0.1, u + 0.1, zb, top), mid + 0.03, mid + 0.12)
    fplate(L['L4'], M['deep'], fr, rect(uc - r + 0.05, uc + r - 0.05, zb + 0.55 * r - 0.06, zb + 0.55 * r + 0.06), mid + 0.03, mid + 0.12)


def wall_decor(L, M, fr, u_from, u_to, bays_niche, pils, cut=()):
    """안쪽 면 부재: 대리석 징두리판(L3)·갓돌(L2)·벽기둥·코니스 2단(L2)·하이라이트(L5). 볼트(뒤-왼쪽 벽)와 겹치지 않게 자른다"""
    pan = (M['giallo'], M['verde'], M['pavo'], M['porphyry'])
    for a, b in segs_minus(u_from, u_to, cut):
        fbox(L['L3'], M['dado'], fr, a, b, 0.0, 0.12, FZ, 3.8)
        fbox(L['L2'], M['marble_lo'], fr, a, b, 0.0, 0.32, 3.8, 4.05)
        fbox(L['L5'], M['hl_marble'], fr, a, b, 0.12, 0.32, 4.05, 4.1)
        k = 0; u = a + 0.45
        while u + 1.5 <= b - 0.3:          # 징두리판 위 색 대리석 판(L3): 벽 아래쪽은 대리석[S47]
            fbox(L['L3'], pan[(k + int(a)) % 4], fr, u, u + 1.5, 0.12, 0.17, 1.0, 3.3)
            u += 2.3; k += 1
    lit = 1.0 if fr is FR_BL else -1.0          # 화면 왼쪽 모서리: 뒤-왼쪽 벽은 +Y, 뒤-오른쪽 벽은 −X
    for up in (() if GRAND else pils):
        zt = min(22.5, zcap(fr, up - 0.8, up + 0.8) - 0.1)      # 기둥머리 윗면(볼트 루넷 아래)
        fbox(L['L2'], M['marble_lo'], fr, up - 0.6, up + 0.6, 0.0, 0.4, 4.05, zt - 0.6)
        fbox(L['L2'], M['marble'], fr, up - 0.75, up + 0.75, 0.0, 0.55, 4.05, 4.45)
        fbox(L['L2'], M['marble'], fr, up - 0.8, up + 0.8, 0.0, 0.6, zt - 0.6, zt)
        e0, e1 = sorted((up + lit * 0.62, up + lit * 0.5))
        fbox(L['L5'], M['hl_marble'], fr, e0, e1, 0.3, 0.42, 4.6, zt - 0.9)      # 벽기둥 밝은 모서리 띠
        fbox(L['L5'], M['hl_marble'], fr, up - 0.8, up + 0.8, 0.4, 0.6, zt, zt + 0.05)
    for a, b in segs_minus(u_from, u_to, vault_band_cuts(fr, 23.3)):
        fbox(L['L2'], M['trav'], fr, a, b, 0.0, 0.55, 22.5, 23.3)
        fbox(L['L5'], M['hl_trav'], fr, a, b, 0.3, 0.55, 23.3, 23.35)
    fbox(L['L2'], M['trav'], fr, u_from, u_to, 0.0, 0.4, 30.9, 31.4)
    fbox(L['L5'], M['hl_trav'], fr, u_from, u_to, 0.2, 0.4, 31.4, 31.45)
    for uc in (() if GRAND else bays_niche):
        niche(L, M, fr, uc)


def up_window_ok(fr, uc):
    return zcap(fr, uc - 1.95, uc + 1.95) >= 28.5 + 0.6


def build_back_walls(L, M):
    """뒤 두 벽: 겉 벽돌 | 콘크리트 속 | 안 벽돌 세 켜. 큰 창 2단(빛은 큰 창 중심). 뒤-왼쪽 벽 앞 끝은 계단식 파손.
    냉탕실 볼트 루넷 안의 위층 창 2개는 반원 창(테르마이 창) 하나로 바꾼다(볼트가 창을 덮지 않게)"""
    holes_bl = []
    for yc in BAYS_BL:
        if not GRAND:
            holes_bl.append(('arch', yc - 2.3, yc + 2.3, 12.0, 18.7))
        if up_window_ok(FR_BL, yc):
            holes_bl.append(('arch', yc - 1.5, yc + 1.5, 24.6, 27.0))
    holes_bl.append(('arch', VYC - TH_R, VYC + TH_R, TH_Z, TH_Z))
    kinds = (M['brick'], M['core'], M['brick'])
    xs = (BL_X[0], BL_X[0] + SK, BL_X[1] - SK, BL_X[1])
    steps = ((BL_END, BL_END + 1.5, 24.0), (BL_END + 1.5, BL_END + 3.0, 15.5), (BL_END + 3.0, FL_Y[0], 8.0))
    for i in range(3):
        L['L0'].wall_y(kinds[i], xs[i], xs[i + 1], BR_Y[0], BL_END, FZ, WH, holes_bl)
        for (y0, y1, zt) in steps:
            L['L0'].box(kinds[i], xs[i], xs[i + 1], y0, y1, FZ, zt)
    holes_br = ([] if GRAND else [('arch', xc - 2.3, xc + 2.3, 12.0, 18.7) for xc in BAYS_BR1]) + [('arch', xc - 1.5, xc + 1.5, 24.6, 27.0) for xc in BAYS_BR2]
    ys = (BR_Y[0], BR_Y[0] + SK, BR_Y[1] - SK, BR_Y[1])
    for i in range(3):
        L['L0'].wall_x(kinds[i], BL_X[1], BR_END, ys[i], ys[i + 1], FZ, WH, holes_br)
    if GRAND:                                          # 16:31 레퍼런스: 안쪽 면은 대리석 판 마감(창 구멍 그대로, 잘린 윗면 세 켜는 그대로 보인다)
        L['L3'].wall_y(M['revet'], BL_X[1], BL_X[1] + 0.06, BR_Y[1], BL_END, 4.1, 30.9, holes_bl)
        L['L3'].wall_x(M['revet'], BL_X[1], BR_END, BR_Y[1], BR_Y[1] + 0.06, 4.1, 30.9, holes_br)
    mid = (BL_X[0] + BL_X[1]) / 2.0 - BL_X[1]          # 벽 두께 가운데(안쪽 면 기준 t)
    for yc in BAYS_BL:
        if not GRAND:
            window_set(L, M, FR_BL, yc, 4.6, 12.0, 18.7, mid)
        if up_window_ok(FR_BL, yc):
            window_set(L, M, FR_BL, yc, 3.0, 24.6, 27.0, mid, bars=False, ring=False)
    thermal_window(L, M, FR_BL, VYC, TH_R, TH_Z, mid)
    for xc in (() if GRAND else BAYS_BR1):
        window_set(L, M, FR_BR, xc, 4.6, 12.0, 18.7, mid)
    for xc in BAYS_BR2:
        window_set(L, M, FR_BR, xc, 3.0, 24.6, 27.0, mid, bars=False, ring=False)
    wall_decor(L, M, FR_BL, BR_Y[1], BL_END, BAYS_BL, PIL_BL, cut=[(yc - 1.95, yc + 1.95) for yc in BAYS_BL])
    wall_decor(L, M, FR_BR, BL_X[1], BR_END, BAYS_BR1, PIL_BR, cut=[(xc - 1.95, xc + 1.95) for xc in BAYS_BR1])
    # L5 윗면 안쪽 모서리 밝은 띠(잘린 윗면은 세 켜가 보인다: 라벨 대상 '욕장 왼쪽 벽 윗면')
    L['L5'].box(M['hl_brick'], BL_X[1] - 0.22, BL_X[1], BR_Y[0] + 0.3, BL_END, WH, WH + 0.05)
    L['L5'].box(M['hl_brick'], BL_X[1], BR_END, BR_Y[1] - 0.22, BR_Y[1], WH, WH + 0.05)
    for (y0, y1, zt) in steps:
        L['L5'].box(M['hl_brick'], BL_X[1] - 0.22, BL_X[1], y0, y1, zt, zt + 0.05)
        L['L5'].box(M['hl_brick'], BL_X[0], BL_X[1], y1 - 0.2, y1, zt, zt + 0.05)
    # L4 파손: 계단 위 깨진 벽돌 토막
    for i, (y, zt) in enumerate(((BL_END + 0.4, 24.0), (BL_END + 1.1, 24.0), (BL_END + 2.0, 15.5), (BL_END + 2.6, 15.5), (BL_END + 3.4, 8.0))):
        L['L4'].obox(M['brick'] if i % 2 else M['core'], 2.4 + 0.5 * R.hash01(i, 3), y, (math.cos(0.4 * i), math.sin(0.4 * i)),
                     (-math.sin(0.4 * i), math.cos(0.4 * i)), -0.35, 0.35, -0.25, 0.25, zt, zt + 0.3 + 0.2 * R.hash01(i, 5))
    # L6 얼룩: 아래층 창턱 밑 물때 줄(창 옆으로 비껴 흐른다) · 잘린 윗선에서 내려온 빗물 자국
    for fr, bays in ((FR_BL, BAYS_BL), (FR_BR, BAYS_BR1)):
        for i, uc in enumerate(bays):
            du = (0.7 if i % 2 else -0.8) + 0.3 * R.hash01(i, 41)
            fbox(L['L6'], M['stain'], fr, uc + du - 0.11, uc + du + 0.11, 0.0, 0.06, max(7.9, 12.0 - 3.6 - 1.2 * R.hash01(i, 43)), 11.7)
    for fr, us in ((FR_BL, (9.0, 44.0, 49.2)), (FR_BR, (12.5, 33.0, 50.3, 56.0))):       # 벽기둥·창·볼트·코니스를 피한 자리
        for i, u in enumerate(us):
            fbox(L['L6'], M['stain'], fr, u - 0.1, u + 0.12, 0.0, 0.06, WH - 4.0 - 2.5 * R.hash01(i, 47), 30.85)
    # L6 이끼: 무너진 계단 윗면(깨끗한 절개 윗면에는 두지 않는다) + 벽 밑동 물때
    for (y0, y1, zt) in steps[:2]:
        L['L6'].box(M['moss'], BL_X[0] + 0.15, BL_X[1] - 0.6, y0 + 0.2, y1 - 0.4, zt, zt + 0.06)


def build_floor(L, M):
    fs = L['L0'].box(M['trav'], 0.0, WX, 0.0, WY, FOUND, FZ)
    fs[1].material_index = L['L0'].mi(M['floor'])
    # L3 냉탕실 대리석 바닥판(볼트 칸·열주·수영장까지) + 수영장 둘레 반암(포르피리) 띠
    L['L3'].box(M['frig'], 5.4, 30.0, VY0 + 0.3, FL_Y[0] - 0.1, FZ, FZ + 0.05)
    py0, py1 = 41.5 + DY, 52.5 + DY            # 수영장(build_frigidarium)과 같은 값
    for (x0, x1, a, b) in () if GRAND else ((7.3, 30.7, py0 - 0.7, py0 - 0.3), (7.3, 30.7, py1 + 0.3, py1 + 0.7), (7.3, 7.7, py0 - 0.3, py1 + 0.3), (30.3, 30.7, py0 - 0.3, py1 + 0.3)):
        L['L3'].box(M['porphyry'], x0, x1, a, b, FZ + 0.05, FZ + 0.1)
    # L3 앞-오른쪽 모자이크 바닥판(반암 테 + 흑백 칸 + 가운데 원판)
    if GRAND:                                  # 16:31: 앞 바닥은 큰 탕이 덮는다
        return
    mx0, mx1, my0, my1 = 46.0, 66.0 + DX, 45.0 + DY, 53.4 + DY
    L['L3'].box(M['porphyry'], mx0, mx1, my0, my1, FZ, FZ + 0.05)
    L['L3'].box(M['mosaic2'], mx0 + 0.5, mx1 - 0.5, my0 + 0.5, my1 - 0.5, FZ, FZ + 0.1)
    cx, cy = (mx0 + mx1) / 2.0, (my0 + my1) / 2.0
    L['L3'].cyl(M['porphyry'], cx, cy, 2.2, FZ, FZ + 0.15, 24)
    L['L3'].cyl(M['marble'], cx, cy, 1.6, FZ, FZ + 0.2, 24)


def build_caldarium(L, M, GC, root):
    """열탕실: 반쪽 드럼(세 켜 단면) + 반쪽 돔(아래 콘크리트·가운데 응회암·위 경석 단면, 코퍼·오큘러스는 복원 추정: 형태만)
    + 하이포코스트(벽돌 기둥 필라이 위 수스펜수라, 기둥 열 L4) + 뜨거운 욕조·물동이(라브룸)·증기"""
    cx, cy = CXc, -CYc
    dphi = (A1 - A0) / NF
    for k in range(NF):
        F = Facet(cx, cy, A0 + dphi * (k + 0.5), dphi, RI)
        win = (k % 2 == 1)
        holes = [('arch', -1.1, 1.1, 11.2, 15.2)] if win else []
        facet_wall(L['L0'], M['drum_in'], F, 0.0, SK, FZ, DRUM_H, holes)
        facet_wall(L['L0'], M['core'], F, SK, TW - SK, FZ, DRUM_H, holes)
        facet_wall(L['L0'], M['brick'], F, TW - SK, TW, FZ, DRUM_H, holes)
        # L2 띠: 바닥 몰딩·가운데 코니스·돔 받침 코니스(안쪽으로 내민다)
        facet_plate(L['L2'], M['marble_lo'], F, rect(-F.half, F.half, FLOOR_C, FLOOR_C + 0.35), -0.2, 0.0)
        facet_plate(L['L2'], M['marble'], F, rect(-F.half, F.half, 10.4, 10.9), -0.35, 0.0)
        facet_plate(L['L2'], M['trav'], F, rect(-F.half, F.half, 18.4, 19.0), -0.45, 0.0)
        facet_plate(L['L5'], M['hl_marble'], F, rect(-F.half, F.half, 10.9, 10.95), -0.35, -0.15)
        facet_plate(L['L5'], M['hl_trav'], F, rect(-F.half, F.half, 19.0, 19.05), -0.45, -0.25)
        if win:     # 빛 판(드럼 콘크리트 한가운데) + 창살 + 창턱
            facet_plate(L['L4'], M['glass'], F, arch_outline(-1.1, 1.1, 11.2, 15.2), 1.32, 1.38)
            for s in (-1, 1):
                facet_plate(L['L4'], M['deep'], F, rect(s * 0.37 - 0.06, s * 0.37 + 0.06, 11.2, 16.0), 1.25, 1.32)
            facet_plate(L['L4'], M['deep'], F, rect(-1.1, 1.1, 13.25, 13.37), 1.25, 1.32)
            facet_plate(L['L2'], M['marble'], F, rect(-1.35, 1.35, 10.95, 11.2), -0.3, 0.0)
        elif k in (2, 4, 6, 8):     # 벽감 + 조각상
            facet_plate(L['L1'], M['deep'], F, arch_outline(-1.0, 1.0, FLOOR_C + 0.6, 7.4), -0.12, 0.0)
            facet_plate(L['L2'], M['marble_lo'], F, rect(-0.7, 0.7, FLOOR_C, FLOOR_C + 0.6), -1.0, 0.0)
            X, Y = F.plan(0.0, -0.6)
            statue(L['L4'], M['statue'], X, Y, FLOOR_C + 0.6, 4.0)
    # 면 이음매마다 붙은 화강암 기둥 + 대리석 주두(욕장 참조 이미지의 열주)
    for j in range(1, NF):
        a = math.radians(A0 + dphi * j)
        X, Y = cx + (RI - 0.32) * math.cos(a), -(cy + (RI - 0.32) * math.sin(a))
        L['L2'].cyl(M['granite'], X, Y, 0.36, FLOOR_C + 0.35, 10.0, 10, r_top=0.32)
        L['L2'].cyl(M['marble'], X, Y, 0.34, 10.0, 10.4, 10, r_top=0.5)
        L['L2'].cyl(M['marble'], X, Y, 0.48, FLOOR_C + 0.35, FLOOR_C + 0.6, 10)
        L['L5'].cyl(M['hl_marble'], X, Y, 0.5, 10.4, 10.42, 10)
    build_dome(GC, root, M)
    # 하이포코스트(뒤 반쪽): 그을린 바닥(L1) · 벽돌 기둥(필라이, L4) · 세 켜 수스펜수라(기와·콘크리트·모자이크)
    arc = []
    for k in range(NF + 1):
        a = math.radians(A0 + dphi * k)
        arc.append((cx + RI * math.cos(a), -(cy + RI * math.sin(a))))
    L['L1'].prism(M['deeper'], arc, FZ, FZ + 0.06)

    def pila(u, v):
        X, Y = cf(u, v)
        L['L4'].obox(M['tile'], X, Y, DV, BV, -0.38, 0.38, -0.38, 0.38, FZ + 0.06, FZ + 0.18)      # 밑 기와(1.5피트)
        L['L4'].obox(M['tile'], X, Y, DV, BV, -0.27, 0.27, -0.27, 0.27, FZ + 0.18, SUS - 0.18)     # 8인치 벽돌 기둥
        L['L4'].obox(M['tile'], X, Y, DV, BV, -0.42, 0.42, -0.42, 0.42, SUS - 0.18, SUS)          # 위 기와(2피트)
    PS = 1.75
    for i in range(-7, 8):
        for v in (0.55, 2.3):
            u = PS * i
            if math.hypot(u, v) <= RI - 0.7:
                pila(u, v)
    L['L0'].prism(M['tile'], arc, SUS, SUS + 0.25)
    L['L0'].prism(M['core'], arc, SUS + 0.25, FLOOR_C - 0.15)
    fs = L['L0'].prism(M['marble'], arc, FLOOR_C - 0.15, FLOOR_C)
    fs[len(arc)].material_index = L['L0'].mi(M['mosaic'])     # 윗면 = 모자이크
    # 앞 반쪽(절개로 걷어낸 쪽): 낮게 남은 드럼 밑동(세 켜 단면) + 바닥판을 걷어 드러난 필라이 열 + 남은 바닥판 한 조각
    arc_f = []
    for k in range(NF + 1):
        a = math.radians(A1 + dphi * k)
        arc_f.append((cx + RI * math.cos(a), -(cy + RI * math.sin(a))))
    L['L1'].prism(M['deeper'], arc_f, FZ, FZ + 0.06)
    for k in range(NF):
        F = Facet(cx, cy, A1 + dphi * (k + 0.5), dphi, RI)
        hk = FZ + 0.8 + 0.9 * R.hash01(k, 21)
        facet_wall(L['L0'], M['drum_in'], F, 0.0, SK, FZ, hk)
        facet_wall(L['L0'], M['core'], F, SK, TW - SK, FZ, hk)
        facet_wall(L['L0'], M['brick'], F, TW - SK, TW, FZ, hk)
        facet_plate(L['L5'], M['hl_brick'], F, rect(-F.half, F.half, hk, hk + 0.05), TW - 0.2, TW)
    for i in range(-7, 8):
        for j in range(1, 8):
            u, v = PS * i, 0.45 - PS * j
            if math.hypot(u, v) > RI - 0.65 or R.hash01(i, j, 31) < 0.07:      # 몇 개는 빠졌다(발굴 흔적)
                continue
            pila(u, v)
    # L6 그을음: 화로 쪽(뒤-오른쪽) 바닥이 더 검다
    for (u, v, r) in ((6.5, -2.4, 1.6), (3.0, -6.2, 1.2), (-4.0, -4.5, 1.0)):
        X, Y = cf(u, v)
        L['L6'].cyl(M['soot'], X, Y, r, FZ + 0.06, FZ + 0.12, 12)
    for (a, b, c, d) in ((-7.3, -3.8, -3.6, -0.15),):
        L['L4'].obox(M['tile'], CXc, CYc, DV, BV, a, b, c, d, SUS, SUS + 0.25)
        L['L4'].obox(M['core'], CXc, CYc, DV, BV, a + 0.1, b - 0.15, c + 0.1, d, SUS + 0.25, FLOOR_C - 0.15)
        L['L4'].obox(M['mosaic'], CXc, CYc, DV, BV, a + 0.2, b - 0.3, c + 0.2, d, FLOOR_C - 0.15, FLOOR_C)
    # 뜨거운 욕조(알베우스): 절개선과 나란한 대리석 테(1.2) + 물(깊이 1.05 → 목욕객이 허리까지 잠긴다)
    u0, u1, v0, v1, t = -5.5, 5.5, 3.4, 7.6, 0.45
    for (a, b, c, d) in () if GRAND else ((u0, u1, v0, v0 + t), (u0, u1, v1 - t, v1), (u0, u0 + t, v0 + t, v1 - t), (u1 - t, u1, v0 + t, v1 - t)):
        L['L0'].obox(M['marble'], CXc, CYc, DV, BV, a, b, c, d, FLOOR_C, FLOOR_C + 1.2)
    if not GRAND:                    # 16:31: 작은 뜨거운 욕조·라브룸 대신 반원 큰 탕(build_grand)
        L['L0'].obox(M['water'], CXc, CYc, DV, BV, u0 + t, u1 - t, v0 + t, v1 - t, FLOOR_C, FLOOR_C + 1.05)
        L['L2'].obox(M['marble_lo'], CXc, CYc, DV, BV, -1.0, 1.0, 2.5, v0, FLOOR_C, FLOOR_C + 0.6)          # 계단
        L['L2'].obox(M['marble_lo'], CXc, CYc, DV, BV, -1.0, 1.0, 1.9, 2.5, FLOOR_C, FLOOR_C + 0.3)
        L['L5'].obox(M['hl_marble'], CXc, CYc, DV, BV, u0, u1, v0, v0 + 0.12, FLOOR_C + 1.2, FLOOR_C + 1.225)
        for (a, b, c) in ((-3.8, -1.6, 4.4), (0.4, 2.8, 6.4), (2.2, 4.2, 4.9), (-4.6, -3.2, 6.6), (3.4, 4.6, 6.9)):
            L['L5'].obox(M['water_hi'], CXc, CYc, DV, BV, a, b, c, c + 0.12, FLOOR_C + 1.05, FLOOR_C + 1.1)
        # 라브룸(대리석 물동이) + 의자 + 수건
        X, Y = cf(-8.6, 2.6)
        L['L4'].cyl(M['marble_lo'], X, Y, 0.45, FLOOR_C, FLOOR_C + 1.6, 10)
        L['L4'].cyl(M['marble'], X, Y, 1.5, FLOOR_C + 1.6, FLOOR_C + 2.15, 16, r_top=1.7)
        L['L4'].cyl(M['water'], X, Y, 1.35, FLOOR_C + 1.9, FLOOR_C + 2.1, 16)
        L['L5'].cyl(M['water_hi'], X - 0.3, Y - 0.3, 0.45, FLOOR_C + 2.1, FLOOR_C + 2.15, 10)
    for k in (3, 7):
        F = Facet(cx, cy, A0 + dphi * (k + 0.5), dphi, RI)
        facet_plate(L['L4'], M['marble'], F, rect(-1.4, 1.4, FLOOR_C, FLOOR_C + 0.55), -0.9, -0.15)
        facet_plate(L['L6'], M['towel'], F, rect(-0.9, 0.1, FLOOR_C + 0.55, FLOOR_C + 0.7), -0.8, -0.35)
    # 증기(L6, 열탕실에만): 화면과 나란한 S자 김 세 가닥
    for (bu, bv, ph) in (() if GRAND else ((-2.4, 5.6, 0.0), (1.2, 6.3, 1.7), (3.8, 5.0, 3.1))):     # 16:43: 김은 cloud()가 맡는다
        ox, oy = cf(bu, bv)
        n = 8
        for i in range(n):
            s0, s1 = i / n, (i + 1) / n

            def cu(s):
                return 0.38 * math.sin(2 * math.pi * 1.1 * s + ph)
            w0, w1 = 0.3 * (1 - 0.65 * s0), 0.3 * (1 - 0.65 * s1)
            z0, z1 = FLOOR_C + 1.3 + 3.4 * s0, FLOOR_C + 1.3 + 3.4 * s1
            pts = [(cu(s0) - w0 / 2, z0), (cu(s0) + w0 / 2, z0), (cu(s1) + w1 / 2, z1), (cu(s1) - w1 / 2, z1)]
            L['L6'].vplate(M['steam'], ox, oy, DV, BV, pts, -0.03, 0.03)


def build_dome(GC, root, M):
    """반쪽 돔 껍질(닫힌 입체): 안쪽 = 반구(코퍼 패임), 바깥 = 낮은 타원. 절개 단면 = 아래 콘크리트·가운데 응회암·위 경석"""
    bm = bmesh.new()
    cx, cy = CXc, -CYc
    h = math.radians((A1 - A0) / NF) / 2.0
    ro = (RI * math.cos(h) + TW) / math.cos(h)
    nr = 8
    phi_max = math.acos(R_OC / RI); psi_max = math.acos(R_OC / ro)
    ang = [math.radians(A0 + (A1 - A0) * k / NF) for k in range(NF + 1)]
    VI, VO = [], []
    for k in range(NF + 1):
        ca, sa = math.cos(ang[k]), math.sin(ang[k])
        ri_row, ro_row = [], []
        for j in range(nr + 1):
            s = j / nr
            ph = s * phi_max; rh = RI * math.cos(ph)
            ri_row.append(bm.verts.new((cx + rh * ca, cy + rh * sa, DRUM_H + RI * math.sin(ph))))
            ps = s * psi_max; rh2 = ro * math.cos(ps)
            ro_row.append(bm.verts.new((cx + rh2 * ca, cy + rh2 * sa, DRUM_H + HO * math.sin(ps))))
        VI.append(ri_row); VO.append(ro_row)
    inner = []
    for k in range(NF):
        for j in range(nr):
            f = bm.faces.new([VI[k][j], VI[k][j + 1], VI[k + 1][j + 1], VI[k + 1][j]]); f.material_index = 1
            if j < nr - 2:
                inner.append(f)
            f = bm.faces.new([VO[k][j], VO[k + 1][j], VO[k + 1][j + 1], VO[k][j + 1]]); f.material_index = 0
        f = bm.faces.new([VI[k][0], VI[k + 1][0], VO[k + 1][0], VO[k][0]]); f.material_index = 0
        f = bm.faces.new([VI[k][nr], VO[k][nr], VO[k + 1][nr], VI[k + 1][nr]]); f.material_index = 6
    for k in (0, NF):
        for j in range(nr):
            s = (j + 0.5) / nr
            mi = 3 if s < 0.34 else (4 if s < 0.67 else 5)
            f = bm.faces.new([VI[k][j], VO[k][j], VO[k][j + 1], VI[k][j + 1]]); f.material_index = mi
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    res = bmesh.ops.inset_individual(bm, faces=inner, thickness=0.3, depth=-0.18, use_even_offset=True)
    for f in res.get('faces', []):
        f.material_index = 2
    G.uv_box(bm, bm.faces[:])
    mats_ = [M['dome_out'], M['coffer'], M['coffer_rib'], M['core'], M['tuffcrete'], M['pumice'], M['trav']]
    return R.bm_to_obj(bm, 'BATHS_Caracalla_L0_Dome', mats_, GC, root, False, recalc=False)


# ── 냉탕실 교차 볼트 ────────────────────────────────────────────────────────────────────────
def vz_in(X, Y):
    """교차 볼트 안쪽 면 높이: 두 터널(X·Y 방향 반원)의 합집합 천장 = 높은 쪽(그로인은 대각선)"""
    dx, dy = X - VXC, Y - VYC
    return VZS + max(math.sqrt(max(0.0, VA * VA - dy * dy)), math.sqrt(max(0.0, VA * VA - dx * dx)))


def vz_out(X, Y):
    return max(vz_in(X, Y) + VT, VZS + VFILL * VA)


def build_frig_vault(GC, root, M, L):
    """냉탕실 교차 볼트 한 칸(닫힌 입체): 안쪽 면(회반죽 줄눈, 그로인 주름은 면 톤 차이로 보인다) · 바깥 면(경석 콘크리트) ·
    가장자리 아치 면(벽돌) · 절개 단면(아래 응회암 · 위 경석 골재, 안쪽 가장자리에 거푸집 경계 정사각 벽돌 줄[S47]).
    뒤-왼쪽 벽 쪽 한 줄은 벽 속으로 0.05 묻는다(벽 안쪽 면과 같은 평면 금지). 그다음 X + Y = VCUT 앞쪽을 잘라 낸다"""
    bm = bmesh.new()
    N = 28
    VI = [[None] * (N + 1) for _ in range(N + 1)]
    VO = [[None] * (N + 1) for _ in range(N + 1)]
    for i in range(N + 1):
        for j in range(N + 1):
            X = VX0 + 2.0 * VA * i / N; Y = VY0 + 2.0 * VA * j / N
            Xb = X - 0.05 if i == 0 else X
            VI[i][j] = bm.verts.new((Xb, -Y, vz_in(X, Y)))
            VO[i][j] = bm.verts.new((Xb, -Y, vz_out(X, Y)))
    h = N // 2

    def tris(i, j):
        if ((i + 0.5 - h) * (j + 0.5 - h)) > 0:      # 그로인 dx = dy
            return ((i, j), (i + 1, j), (i + 1, j + 1)), ((i, j), (i + 1, j + 1), (i, j + 1))
        return ((i, j), (i + 1, j), (i, j + 1)), ((i + 1, j), (i + 1, j + 1), (i, j + 1))
    for i in range(N):
        for j in range(N):
            for tr in tris(i, j):
                f = bm.faces.new([VI[a][b] for (a, b) in tr]); f.material_index = 0          # 안쪽(아래를 본다)
                f = bm.faces.new([VO[a][b] for (a, b) in tr[::-1]]); f.material_index = 1    # 바깥(위를 본다)
    for i in range(N):
        f = bm.faces.new([VO[i][0], VO[i + 1][0], VI[i + 1][0], VI[i][0]]); f.material_index = 2      # 뒤 가장자리
        f = bm.faces.new([VI[i][N], VI[i + 1][N], VO[i + 1][N], VO[i][N]]); f.material_index = 2      # 앞 가장자리
    for j in range(N):
        f = bm.faces.new([VI[0][j], VI[0][j + 1], VO[0][j + 1], VO[0][j]]); f.material_index = 2      # 벽 쪽
        f = bm.faces.new([VO[N][j], VO[N][j + 1], VI[N][j + 1], VI[N][j]]); f.material_index = 2      # 오른쪽 가장자리
    # 절개: 평면 X + Y = VCUT의 앞쪽(+X+Y) 제거 → 단면을 채운다
    pco = Vector((VCUT / 2.0, -VCUT / 2.0, 0.0)); pno = Vector((S2, -S2, 0.0))
    if GRAND and VAULT_TILT:         # 16:43 시험: 카메라 쪽으로 40° 기운 절개면 — 껍질이 거의 다 걷혀 아치 띠만 남아 끈다(VAULT_TILT = False)
        ch, cv = math.cos(math.radians(40.0)), math.sin(math.radians(40.0))
        pco = Vector((VCUT / 2.0, -VCUT / 2.0, VZS + 0.55 * VA)); pno = Vector((S2 * ch, -S2 * ch, cv))
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=pco, plane_no=pno, clear_outer=True)
    cut_e = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge) and e.is_boundary]
    fill = bmesh.ops.holes_fill(bm, edges=cut_e, sides=0)
    for f in fill.get('faces', []):
        f.material_index = 3
        f.normal_update()
        if f.normal.dot(pno) < 0:
            f.normal_flip()
    for f in bm.faces:              # 기점 가까운 안쪽 면 = 깊이색(빛 계산이 아니라 색 지정, L1 원칙)
        if f.material_index == 0 and f.calc_center_median().z < VZS + 0.32 * VA:
            f.material_index = 4
    G.uv_box(bm, bm.faces[:])
    ob = R.bm_to_obj(bm, 'BATHS_Caracalla_L0_Vault', [M['vault_in'], M['vroof'], M['brick'], M['vsec'], M['vault_lo']], GC, root, False, recalc=False)
    # 단면 앞(0.05)의 띠: 안쪽 가장자리 정사각 벽돌 줄(L2) · 윗선 하이라이트(L5)
    pa = (VCUT - VY1 + 1e-3, VY1 - 1e-3)               # 앞 가장자리와 만나는 점
    pb = (VX1 - 1e-3, VCUT - VX1 + 1e-3)               # 오른쪽 가장자리와 만나는 점
    M_ = 40
    off = 0.05 * S2
    for k in range(0 if (GRAND and VAULT_TILT) else M_):     # 수직 절개선용 단면 띠(기운 절개에는 맞지 않는다)
        s0, s1 = k / M_, (k + 1) / M_
        A = (pa[0] + (pb[0] - pa[0]) * s0, pa[1] + (pb[1] - pa[1]) * s0)
        B = (pa[0] + (pb[0] - pa[0]) * s1, pa[1] + (pb[1] - pa[1]) * s1)
        za0, zb0 = vz_in(*A), vz_in(*B)
        zo0, zo1 = vz_out(*A), vz_out(*B)
        for (lay, m, z_lo0, z_lo1, z_hi0, z_hi1) in ((L['L2'], M['tile'], za0, zb0, za0 + 0.22, zb0 + 0.22),
                                                    (L['L5'], M['hl_vault'], zo0 - 0.14, zo1 - 0.14, zo0, zo1)):
            bmv = lay.bm
            q = [bmv.verts.new((A[0] + off, -(A[1] + off), z_lo0)), bmv.verts.new((B[0] + off, -(B[1] + off), z_lo1)),
                 bmv.verts.new((B[0] + off, -(B[1] + off), z_hi1)), bmv.verts.new((A[0] + off, -(A[1] + off), z_hi0))]
            f = bmv.faces.new(q); f.material_index = lay.mi(m)
    # 오른쪽 꼭짓점 피어(벽돌면 콘크리트) + 대리석 머리돌 + 앞에 붙은 화강암 기둥(냉탕실 화강암 기둥 8개[S80] 중 하나)
    L['L0'].box(M['brick'], VX1 - 1.1, VX1 + 1.1, VY0 - 1.1, VY0 + 1.1, FZ, VZS - 0.45)
    L['L3'].box(M['dado'], VX1 - 1.15, VX1 + 1.15, VY0 - 1.15, VY0 + 1.15, FZ, 12.5)      # 피어 대리석 겉판(아래쪽)
    L['L2'].box(M['marble'], VX1 - 1.3, VX1 + 1.3, VY0 - 1.3, VY0 + 1.3, VZS - 0.45, VZS)
    L['L5'].box(M['hl_marble'], VX1 - 1.3, VX1 + 1.3, VY0 + 1.1, VY0 + 1.3, VZS, VZS + 0.05)
    gx, gy = VX1 + 0.1, VY0 + 1.15 + 0.97                 # 피어 겉판 앞에 붙는다(기둥 받침과 겹치지 않는다)
    L['L2'].box(M['marble'], gx - 0.95, gx + 0.95, gy - 0.95, gy + 0.95, FZ, FZ + 0.5)
    L['L2'].cyl(M['granite'], gx, gy, 0.7, FZ + 0.5, VZS - 1.05, 14, r_top=0.62)
    L['L2'].cyl(M['marble'], gx, gy, 0.62, VZS - 1.05, VZS - 0.45, 14, r_top=0.95)
    for (z0, z1) in ((FZ + 0.8, 6.5), (6.5, 12.0), (12.0, VZS - 1.3)):
        L['L5'].box(M['hl_marble'], gx - 0.06, gx + 0.06, gy + 0.62, gy + 0.72, z0, z1)
    return ob


def build_service(L, M):
    """화로(프라이푸르니움) + 청동 보일러 + 납 관 + 장작 + 저수조(수도교가 닿는 자리)"""
    # 화로: 몸체 + 아치 아궁이(오른면) + 아궁이 속 깊이색 + 불꽃
    L['L0'].box(M['brick'], 52.5, 55.6, 6.4, 10.0, FZ, 4.8)
    L['L1'].box(M['deeper'], 55.6, 56.2, 7.0, 9.4, FZ, 2.6)
    L['L0'].box(M['brick'], 55.6, 56.2, 6.4, 7.0, FZ, 4.8)
    L['L0'].box(M['brick'], 55.6, 56.2, 9.4, 10.0, FZ, 4.8)
    L['L0'].box(M['brick'], 55.6, 56.2, 7.0, 9.4, 2.6, 4.8)
    L['L0'].wall_y(M['brick'], 56.2, 56.5, 6.4, 10.0, FZ, 4.8, [('arch', 7.35, 9.05, FZ, 1.55)])
    L['L2'].box(M['trav'], 52.3, 56.7, 6.2, 10.2, 4.8, 5.1)
    L['L5'].box(M['hl_trav'], 56.5, 56.7, 6.2, 10.2, 5.1, 5.125)
    flame = [(7.6, FZ), (8.8, FZ), (8.75, 0.9), (8.5, 1.5), (8.2, 2.05), (7.95, 1.5), (7.65, 0.9)]
    core = [(7.9, FZ), (8.5, FZ), (8.45, 0.8), (8.2, 1.35), (7.95, 0.8)]
    L['L4'].vplate(M['fire'], 0.0, 0.0, (0.0, 1.0), (1.0, 0.0), flame, 56.22, 56.26)
    L['L4'].vplate(M['fire_hi'], 0.0, 0.0, (0.0, 1.0), (1.0, 0.0), core, 56.27, 56.3)
    # 보일러(청동) + 뚜껑 + 밝은 세로 띠(L5) + 납 관(칼다리움으로)
    L['L4'].cyl(M['bronze'], 54.0, 8.2, 1.25, 5.1, 7.4, 16)
    L['L4'].cyl(M['bronze'], 54.0, 8.2, 1.3, 7.4, 7.9, 16, r_top=0.45)
    L['L5'].obox(M['hl_bronze'], 54.0, 8.2, (S2, -S2), (S2, S2), -0.12, 0.12, 1.2, 1.29, 5.3, 7.3)
    d = (52.36 - 53.49, 11.85 - 9.34); ln = math.hypot(*d); ex = (d[0] / ln, d[1] / ln); ey = (-ex[1], ex[0])
    L['L4'].obox(M['lead'], 53.49, 9.34, ex, ey, 0.0, ln, -0.18, 0.18, 5.8, 6.16)
    # 장작 더미(아궁이 앞-왼쪽)
    for i in range(3):
        L['L4'].box(M['wood'], 56.9, 58.9, 10.7 + 0.55 * i, 11.15 + 0.55 * i, FZ, FZ + 0.45)
    for i in range(2):
        L['L4'].box(M['wood_dk'], 57.0, 59.0, 10.95 + 0.55 * i, 11.4 + 0.55 * i, FZ + 0.45, FZ + 0.9)
    # 저수조(벽돌 상자, 위는 칸막이 칸마다 물): 보이는 두 면에 2층 아치 개구부(속은 깊이색)
    x0, x1, y0, y1 = CIS
    zt = CIS_TOP - 1.4
    L['L1'].box(M['deeper'], x0 + 0.4, x1 - 0.4, y0 + 0.4, y1 - 0.4, FZ, zt - 0.6)
    holes_f = []
    for xc in (x0 + 2.4, x0 + 5.5, x0 + 8.6):
        holes_f += [('arch', xc - 0.8, xc + 0.8, 1.6, 4.4), ('arch', xc - 0.65, xc + 0.65, 14.6, 17.6)]
    L['L0'].wall_x(M['brick'], x0, x1, y1 - 0.4, y1, FZ, zt, holes_f)
    holes_r = []
    for yc in (4.6, 7.8):
        holes_r += [('arch', yc - 0.8, yc + 0.8, 1.6, 4.4), ('arch', yc - 0.65, yc + 0.65, 14.6, 17.6)]
    L['L0'].wall_y(M['brick'], x1 - 0.4, x1, y0 + 0.4, y1 - 0.4, FZ, zt, holes_r)
    L['L0'].box(M['brick'], x0, x1, y0, y0 + 0.4, FZ, zt)
    L['L0'].box(M['brick'], x0, x0 + 0.4, y0 + 0.4, y1 - 0.4, FZ, zt)
    L['L0'].box(M['core'], x0 + 0.4, x1 - 0.4, y0 + 0.4, y1 - 0.4, zt - 0.6, zt)          # 칸 바닥(콘크리트)
    # 윗 테(난간) + 칸막이 4×4 + 물
    L['L0'].box(M['brick'], x0, x1, y1 - 0.6, y1, zt, CIS_TOP)
    L['L0'].box(M['brick'], x0, x1 - 1.4, y0, y0 + 0.6, zt, CIS_TOP)
    L['L0'].box(M['brick'], x0, x0 + 0.6, y0 + 0.6, y1 - 0.6, zt, CIS_TOP)
    L['L0'].box(M['brick'], x1 - 0.6, x1, y0 + 1.8, y1 - 0.6, zt, CIS_TOP)
    L['L4'].box(M['water'], x0 + 0.6, x1 - 0.6, y0 + 0.6, y1 - 0.6, zt, zt + 0.6)
    L['L4'].box(M['water'], x1 - 1.4, x1, y0, y0 + 1.8, zt, zt + 0.6)          # 수로 물이 드는 들목
    for xp in (x0 + 3.05, x0 + 5.5, x0 + 7.95):
        L['L2'].box(M['brick'], xp - 0.15, xp + 0.15, y0 + 0.6, y1 - 0.6, zt, zt + 1.0)
    for yp in (3.05, 5.5, 7.95):
        L['L2'].box(M['brick'], x0 + 0.6, x1 - 0.6, yp - 0.15, yp + 0.15, zt, zt + 1.0)
    for (a, b, c) in ((x0 + 1.0, x0 + 2.6, 9.0), (x0 + 4.0, x0 + 6.2, 4.2), (x0 + 8.2, x0 + 9.6, 6.6)):
        L['L5'].box(M['water_hi'], a, b, c, c + 0.12, zt + 0.6, zt + 0.65)
    # 띠(L2): 층 띠·코니스(대지 오른쪽 꼭짓점 밖으로 내밀지 않는다)
    L['L2'].box(M['trav'], x0 - 0.2, x1, y1, y1 + 0.2, 12.8, 13.2)
    L['L2'].box(M['trav'], x1, x1 + 0.2, y0 + 1.8, y1 + 0.2, 12.8, 13.2)
    L['L2'].box(M['trav'], x0 - 0.2, x1, y1, y1 + 0.2, CIS_TOP - 0.5, CIS_TOP)
    L['L2'].box(M['trav'], x1, x1 + 0.2, y0 + 1.8, y1 + 0.2, CIS_TOP - 0.5, CIS_TOP)
    L['L2'].box(M['trav'], x0 - 0.2, x0, BR_Y[1], y1 + 0.2, CIS_TOP - 0.5, CIS_TOP)
    L['L5'].box(M['hl_trav'], x0 - 0.2, x1, y1, y1 + 0.2, 13.2, 13.225)
    L['L5'].box(M['hl_brick'], x0, x1, y1 - 0.2, y1, CIS_TOP, CIS_TOP + 0.05)
    L['L5'].box(M['hl_brick'], x1 - 0.2, x1, y0 + 1.8, y1, CIS_TOP, CIS_TOP + 0.05)
    # L3 벽돌 사이 기와 띠(이음 켜)
    for z in (6.0, 9.8, 20.4, 22.6):
        L['L3'].box(M['tile_band'], x0, x1, y1, y1 + 0.05, z, z + 0.2)
        L['L3'].box(M['tile_band'], x1, x1 + 0.05, y0 + 1.8, y1, z, z + 0.2)
    # L6 빗물 얼룩·석회 자국·이끼
    for i, xs in enumerate((x0 + 1.2, x0 + 4.1, x0 + 7.3)):
        L['L6'].box(M['stain'], xs, xs + 0.25 + 0.1 * (i % 2), y1, y1 + 0.1, 19.5 - 2.0 * (i % 2), CIS_TOP - 0.5)
    L['L6'].box(M['calcite'], x1 - 1.6, x1 - 1.38, y1, y1 + 0.1, 18.2, CIS_TOP - 0.5)
    L['L6'].box(M['calcite'], x1, x1 + 0.1, 2.4, 2.62, 16.8, CIS_TOP - 0.5)
    L['L6'].box(M['moss'], x0, x0 + 3.4, y1, y1 + 0.1, FZ, FZ + 0.9)
    L['L6'].box(M['moss'], x1, x1 + 0.1, 8.2, 10.6, FZ, FZ + 1.1)


def build_frigidarium(L, M):
    """냉탕실 열주(화강암 기둥 5개·엔타블러처 = 볼트 기점) + 수영장(나타티오, 지붕 없음·증기 없음) + 파르네세 헤라클레스상"""
    x0, x1, t = 8.0, 30.0, 0.55
    y0, y1 = 41.5 + DY, 52.5 + DY
    zb = FZ + 0.05
    for (a, b, c, d) in () if GRAND else ((x0, x1, y0, y0 + t), (x0, x1, y1 - t, y1), (x0, x0 + t, y0 + t, y1 - t), (x1 - t, x1, y0 + t, y1 - t)):
        L['L0'].box(M['marble'], a, b, c, d, zb, zb + 1.4)
    if not GRAND:
        L['L0'].box(M['water'], x0 + t, x1 - t, y0 + t, y1 - t, zb, zb + 1.2)       # 깊이 1.2 → 헤엄치는 사람이 가슴까지 잠긴다
        L['L2'].box(M['marble_lo'], 18.0, 20.5, y1, y1 + 0.9, zb, zb + 0.7)
        L['L2'].box(M['marble_lo'], 18.0, 20.5, y1, y1 + 0.45, zb + 0.7, zb + 1.1)
        L['L5'].box(M['hl_marble'], x0, x1, y1 - 0.15, y1, zb + 1.4, zb + 1.45)
        L['L5'].box(M['hl_marble'], x1 - 0.15, x1, y0, y1, zb + 1.4, zb + 1.45)
    # L5 물빛 선: 3mm 이하 간격 격자(6×6mm 빈 단색 면 0)
    for r_, yy in enumerate(() if GRAND else (y0 + 1.3, y0 + 3.3, y0 + 5.3, y0 + 7.3, y0 + 9.3)):
        for k in range(5):
            a = x0 + 1.3 + 4.3 * k + (1.6 if r_ % 2 else 0.0)
            b = min(x1 - 0.8, a + 1.5 + 0.8 * R.hash01(k, r_))
            if b - a > 0.4 and yy < y1 - 0.8:
                L['L5'].box(M['water_hi'], a, b, yy, yy + 0.13, zb + 1.2, zb + 1.25)
    cols = FRIG_COLS if GRAND else (8.5, 13.4, 18.3, 23.2, 28.1)
    yc = 38.5
    cs = 1.5 if GRAND else 1.0                                                  # 16:43 기둥 지름 약 2배(간격 = 지름 1.5~2배)
    for i_, X in enumerate(cols):
        L['L2'].box(M['marble'], X - 1.15 * cs, X + 1.15 * cs, yc - 1.15 * cs, yc + 1.15 * cs, zb, 0.6 + (1.4 if GRAND else 0.0))
        L['L2'].cyl(M['marble'], X, yc, 1.05 * cs, 0.6 + (1.4 if GRAND else 0.0), 0.95 + (1.4 if GRAND else 0.0), 14)
        L['L2'].cyl(M[SHAFTS[i_ % len(SHAFTS)]] if GRAND else M['granite'], X, yc, 0.85 * cs, 0.95 + (1.4 if GRAND else 0.0), 14.5, 14, r_top=0.75 * cs)
        L['L2'].cyl(M['marble'], X, yc, 0.8 * cs, 14.5, 15.2, 14, r_top=1.15 * cs)
        L['L2'].box(M['marble'], X - 1.3 * cs, X + 1.3 * cs, yc - 1.3 * cs, yc + 1.3 * cs, 15.2, 15.6)
        for (z0, z1, rr) in ((2.6, 5.6, 0.83), (5.6, 10.0, 0.8), (10.0, 14.2, 0.77)):     # 기둥 밝은 쪽(왼쪽 앞) 세로 띠
            L['L5'].box(M['hl_marble'], X - 0.07, X + 0.07, yc + rr * cs - 0.04, yc + rr * cs + 0.06, z0, z1)
        L['L5'].box(M['hl_marble'], X - 1.3 * cs, X + 1.3 * cs, yc + 1.3 * cs - 0.2, yc + 1.3 * cs, 15.6, 15.625)
    L['L2'].box(M['marble'], 5.4, 30.0, 37.5, 39.5, 15.6, 16.5)
    L['L2'].box(M['marble_lo'], 5.4, 30.0, 37.65, 39.35, 16.5, 17.2)
    L['L2'].box(M['marble'], 5.4, 30.4, 37.2, 39.8, 17.2, VZS)
    L['L5'].box(M['hl_marble'], 5.4, 30.4, 39.55, 39.8, VZS, VZS + 0.05)
    L['L5'].box(M['hl_marble'], 5.4, 30.0, 39.45, 39.5, 15.75, 16.4)
    # 냉탕실 분수 물동이(라브룸): 볼트 칸 가운데(장축 시선 끝의 분수[S47])
    fx, fy = VXC + 0.6, VYC - 0.4
    if GRAND:                                   # 16:43: 볼트 밑은 큰 탕(라브룸 0)
        fx = None
    for _ in (() if fx is None else (0,)):
        L['L4'].cyl(M['marble_lo'], fx, fy, 0.5, zb, zb + 1.5, 12)
        L['L4'].cyl(M['marble'], fx, fy, 1.7, zb + 1.5, zb + 2.05, 20, r_top=1.9)
        L['L4'].cyl(M['water'], fx, fy, 1.55, zb + 1.8, zb + 2.0, 20)
        L['L5'].cyl(M['hl_marble'], fx, fy, 1.92, zb + 2.05, zb + 2.1, 20)
        L['L5'].cyl(M['water_hi'], fx - 0.4, fy - 0.3, 0.5, zb + 2.0, zb + 2.05, 10)
    # 파르네세 헤라클레스(카라칼라 욕장에서 나온 상)
    L['L2'].box(M['marble_lo'], 31.6, 33.4, 37.6, 39.4, zb, 1.9)
    L['L2'].box(M['marble'], 31.45, 33.55, 37.45, 39.55, 1.9, 2.15)
    L['L5'].box(M['hl_marble'], 31.45, 33.55, 39.35, 39.55, 2.15, 2.175)
    statue(L['L4'], M['statue'], 32.5, 38.5, 2.15, 6.0, heroic=True)
    # 앞-오른쪽: 받침 위 청동상
    bx = 63.1 + DX
    L['L2'].box(M['marble_lo'], bx - 0.8, bx + 0.8, 39.2, 40.8, FZ, 1.7)
    L['L2'].box(M['marble'], bx - 0.95, bx + 0.95, 39.05, 40.95, 1.7, 1.95)
    L['L5'].box(M['hl_marble'], bx - 0.95, bx + 0.95, 40.75, 40.95, 1.95, 1.975)
    statue(L['L4'], M['bronze'], bx, 40.0, 1.95, 4.8)
    L['L5'].box(M['hl_bronze'], bx - 0.05, bx + 0.07, 40.2, 40.32, 2.2, 4.0)


# ═════════════ 16:31 장엄한 실내(욕장-참조.jpg): 기둥 숲 · 큰 청록 탕 · 오큘러스 빛살 · 김 ═════════════
#   사람 0(사용자 16:35 '맵에 사람 오브젝트는 있으면 안 돼'): 생활감은 김 줄기·물결·젖은 대리석 반사띠(L5·L6)로만 낸다
SHAFTS = ('granite', 'giallo', 'pavo', 'porphyry', 'verde')      # 기둥 몸 색 대리석(번갈아)
POOL = (6.4, 64.2, 42.3, 55.6)                                    # 큰 탕(나타티오) 평면 상자: 앞 바닥 대부분
POOL_ZR, POOL_ZW = FZ + 0.05 + 1.9, FZ + 0.05 + 1.45              # 테 윗면 · 물 윗면
CAL_PR, CAL_PV = 10.6, 0.6                                        # 칼다리움 반원 탕 반지름 · 앞 변(v)


def capital(L, M, X, Y, z0, r, h=0.7, ab=None):
    """코린트 주두(L2 종 + 대판, L4 잎 8장, L5 대판 앞 모서리)"""
    ab = ab or r * 1.7
    L['L2'].cyl(M['marble'], X, Y, r * 0.95, z0, z0 + h, 10, r_top=r * 1.45)
    L['L2'].box(M['marble'], X - ab, X + ab, Y - ab, Y + ab, z0 + h, z0 + h + 0.25)
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        L['L4'].cyl(M['marble_lo'], X + r * 1.05 * math.cos(a), Y + r * 1.05 * math.sin(a), r * 0.24, z0, z0 + h * 0.62, 5, r_top=r * 0.04)
    L['L5'].box(M['hl_marble'], X - ab, X + ab, Y + ab - 0.16, Y + ab, z0 + h + 0.25, z0 + h + 0.27)


def column(L, M, X, Y, zb, zt, r, k, ped=False):
    """기둥 하나(대좌·밑동·색 대리석 몸·코린트 주두). zt = 대판 윗면"""
    z = zb
    if ped:
        L['L2'].box(M['marble_lo'], X - r * 1.5, X + r * 1.5, Y - r * 1.5, Y + r * 1.5, z, z + 0.7)
        L['L5'].box(M['hl_marble'], X - r * 1.5, X + r * 1.5, Y + r * 1.5 - 0.15, Y + r * 1.5, z + 0.7, z + 0.72)
        z += 0.7
    L['L2'].cyl(M['marble'], X, Y, r * 1.3, z, z + 0.3, 12, r_top=r * 1.05)
    zc = zt - 0.25 - 0.7
    L['L2'].cyl(M[SHAFTS[k % len(SHAFTS)]], X, Y, r, z + 0.3, zc, 12, r_top=r * 0.88)
    L['L5'].box(M['hl_marble'], X - 0.06, X + 0.06, Y + r * 0.9 - 0.04, Y + r * 0.9 + 0.05, z + 0.6, zc - 0.3)      # 몸 밝은 쪽 세로 띠
    capital(L, M, X, Y, zc, r * 0.9)


FRIG_COLS = (7.6, 12.0, 16.4, 20.8, 25.2, 29.6)                 # 16:43 냉탕실 열주(지름 2.6, 간격 4.4)
WC_R, WC_R2, WC_P = 1.2, 0.85, 5.0                               # 벽 앞 기둥 반지름(아래·위) · 간격(지름의 약 2배)


def niche2(L, M, fr, uc, z0, z1, w, sh):
    """아치 벽감(L1 속) + 대리석 테(L2) + 흰 조각상(L4, 조형물) + 받침"""
    fplate(L['L1'], M['deep'], fr, arch_outline(uc - w / 2, uc + w / 2, z0, z1 - w / 2), 0.0, 0.2)
    r1, r2 = w / 2 + 0.03, w / 2 + 0.3
    for k in range(7):
        a0, a1 = math.pi * k / 7, math.pi * (k + 1) / 7
        zs = z1 - w / 2
        pts = [(uc + r1 * math.cos(a0), zs + r1 * math.sin(a0)), (uc + r2 * math.cos(a0), zs + r2 * math.sin(a0)),
               (uc + r2 * math.cos(a1), zs + r2 * math.sin(a1)), (uc + r1 * math.cos(a1), zs + r1 * math.sin(a1))]
        fplate(L['L2'], M['marble'], fr, pts, 0.0, 0.18)
    fbox(L['L2'], M['marble_lo'], fr, uc - w / 2 - 0.2, uc + w / 2 + 0.2, 0.0, 0.7, z0 - 0.35, z0)
    fbox(L['L5'], M['hl_marble'], fr, uc - w / 2 - 0.2, uc + w / 2 + 0.2, 0.5, 0.7, z0, z0 + 0.03)
    X, Y = fpt(fr, uc, 0.5)
    statue(L['L4'], M['statue'], X, Y, z0, sh)


def wall_colonnade(L, M, fr, u_from, u_to, skip=()):
    """벽 앞 2단 기둥 숲: 아래 큰 기둥(대좌) + 엔타블러처 + 난간 회랑 + 위 기둥 + 위 엔타블러처.
    기둥 사이마다 2단 아치 벽감 + 흰 조각상 · 벽감 사이 코니스 띠(볼트와 겹치는 구간은 아래 단만)"""
    cuts = vault_band_cuts(fr, 23.3)
    us = []
    u = u_from + 2.2
    while u < u_to - 1.6:
        us.append(u); u += WC_P
    for k, u in enumerate(us):
        if any(a <= u <= b for (a, b) in skip):
            continue
        X, Y = fpt(fr, u, 2.0)
        column(L, M, X, Y, FZ, 11.3, WC_R, k + (0 if fr is FR_BL else 2), ped=True)
        if not any(a - 1.5 < u < b + 1.5 for (a, b) in cuts):
            X2, Y2 = fpt(fr, u, 1.6)
            column(L, M, X2, Y2, 12.0, 21.25, WC_R2, k + 1)
    for k, (ua, ub) in enumerate(zip(us[:-1], us[1:])):
        uc = (ua + ub) / 2.0
        if any(a <= uc <= b for (a, b) in skip):
            continue
        niche2(L, M, fr, uc, 4.4, 9.6, 2.0, 4.0)                                  # 아래 벽감
        if not any(a - 1.0 < uc < b + 1.0 for (a, b) in cuts):
            niche2(L, M, fr, uc, 13.6, 18.6, 1.8, 3.6)                            # 위 벽감
    fbox(L['L2'], M['marble_lo'], fr, u_from, u_to, 0.0, 0.35, 10.15, 10.45)     # 벽감 위 코니스 띠
    fbox(L['L5'], M['hl_marble'], fr, u_from, u_to, 0.15, 0.35, 10.45, 10.48)
    for a, b in ((u_from, u_to),):
        fbox(L['L2'], M['marble'], fr, a, b, 0.0, 3.4, 11.3, 11.75)              # 아키트레이브
        fbox(L['L3'], M['porphyry'], fr, a, b, 3.4, 3.44, 11.42, 11.62)          # 프리즈 색 띠
        fbox(L['L2'], M['marble'], fr, a, b, 0.0, 3.6, 11.75, 12.0)              # 코니스 = 회랑 바닥
        fbox(L['L5'], M['hl_marble'], fr, a, b, 3.4, 3.6, 12.0, 12.03)
        fbox(L['L2'], M['marble_lo'], fr, a, b, 3.2, 3.5, 12.0, 12.2)            # 난간 밑단
        u = a + 0.3
        while u < b - 0.2:                                                        # 난간 동자(L4)
            X, Y = fpt(fr, u, 3.35)
            L['L4'].cyl(M['marble'], X, Y, 0.11, 12.2, 12.8, 6, r_top=0.08)
            u += 0.5
        fbox(L['L2'], M['marble'], fr, a, b, 3.15, 3.55, 12.8, 12.98)            # 난간 손잡이
        fbox(L['L5'], M['hl_marble'], fr, a, b, 3.4, 3.55, 12.98, 13.01)
    for a, b in segs_minus(u_from, u_to, cuts):
        fbox(L['L2'], M['marble'], fr, a, b, 0.0, 2.6, 21.25, 21.75)             # 위 엔타블러처(기존 코니스 22.5 밑)
        fbox(L['L3'], M['giallo'], fr, a, b, 2.6, 2.64, 21.82, 22.08)
        fbox(L['L2'], M['marble'], fr, a, b, 0.0, 2.8, 22.15, 22.5)
        fbox(L['L5'], M['hl_marble'], fr, a, b, 2.6, 2.8, 22.5, 22.53)


def free_row(L, M, pts, zt, r, k0=0, ent=True, ped=True):
    """실내 기둥 열(탕 둘레·탕 속): 기둥 + 이어진 엔타블러처(열 방향이 평면 X나 Y와 나란할 때)"""
    for k, (X, Y, zb) in enumerate(pts):
        column(L, M, X, Y, zb, zt, r, k0 + k, ped=ped)
    if ent and len(pts) > 1:
        (xa, ya, _), (xb, yb, _) = pts[0], pts[-1]
        e = r * 1.7
        L['L2'].box(M['marble'], min(xa, xb) - e, max(xa, xb) + e, min(ya, yb) - e * 0.6, max(ya, yb) + e * 0.6, zt, zt + 0.45)
        L['L3'].box(M['porphyry'], min(xa, xb) - e, max(xa, xb) + e, max(ya, yb) + e * 0.6, max(ya, yb) + e * 0.6 + 0.04, zt + 0.12, zt + 0.32)
        L['L2'].box(M['marble'], min(xa, xb) - e - 0.15, max(xa, xb) + e + 0.15, min(ya, yb) - e * 0.6 - 0.15, max(ya, yb) + e * 0.6 + 0.15, zt + 0.45, zt + 0.7)
        L['L5'].box(M['hl_marble'], min(xa, xb) - e - 0.15, max(xa, xb) + e + 0.15, max(ya, yb) + e * 0.6, max(ya, yb) + e * 0.6 + 0.15, zt + 0.7, zt + 0.73)


def cloud(L, M, X, Y, z0, size, ph):
    """김 덩어리(L6): 크기가 다른 둥근 타원 4장을 겹친 평면(화면과 나란함). 아래 #F4EEE2 → 위로 갈수록 연하다"""
    spec = ((0.0, 0.0, 1.0, 'steam'), (-0.75, 0.55, 0.8, 'steam'), (0.8, 0.75, 0.72, 'steam2'), (0.1, 1.45, 0.6, 'steam3'))
    for i, (du, dz, sc, mk) in enumerate(spec):
        rx = size * sc * (0.9 + 0.2 * R.hash01(i, ph, 5)); rz = rx * 0.72
        cu = du * size + 0.3 * math.sin(ph + i)
        zc = z0 + rz + dz * size
        pts = [(cu + rx * math.cos(2 * math.pi * k / 18), zc + rz * math.sin(2 * math.pi * k / 18)) for k in range(18)]
        L['L6'].vplate(M[mk], X, Y, DV, BV, pts, -0.03 + 0.05 * i, 0.03 + 0.05 * i)


POOL_A = (6.6, 31.0, 18.6, 55.6)      # 냉탕실 볼트 밑 ~ 앞(평면 X0, X1, Y0, Y1)
POOL_B = (31.0, 64.2, 41.6, 55.6)     # 앞 띠(칼다리움 앞)


def big_pool(L, M):
    """ㄱ자 큰 청록 탕(나타티오, 바닥의 약 60%): 테 + 둘레를 도는 안쪽 계단 2단 + 물 + 깊은 물 띠 + 물빛 + 젖은 테 반사띠"""
    zb, ZR, ZW, t = FZ + 0.05, POOL_ZR, POOL_ZW, 0.7
    ax0, ax1, ay0, ay1 = POOL_A; bx0, bx1, by0, by1 = POOL_B
    poly = [(ax0, ay0), (ax1, ay0), (ax1, by0), (bx1, by0), (bx1, by1), (ax0, ay1)]
    n = len(poly)
    def inset(d):
        """다각형을 안쪽으로 d만큼(축 정렬 ㄱ자라 변마다 법선 이동 + 꼭짓점은 두 변의 교점)"""
        lines = []
        for i in range(n):
            (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
            dx, dy = x1 - x0, y1 - y0; Lh = math.hypot(dx, dy)
            nx, ny = -dy / Lh, dx / Lh                      # 왼쪽 법선(시계 반대 다각형이면 안쪽)
            lines.append(((x0 + nx * d, y0 + ny * d), (dx, dy)))
        out = []
        for i in range(n):
            (p1, d1), (p2, d2) = lines[i - 1], lines[i]
            den = d1[0] * d2[1] - d1[1] * d2[0]
            tt = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
            out.append((p1[0] + d1[0] * tt, p1[1] + d1[1] * tt))
        return out
    sgn = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    if sgn < 0:
        poly = poly[::-1]
    def band(d0, d1, z0, z1, m, lay='L0'):
        A, B_ = inset(d0), inset(d1)
        for i in range(n):
            L[lay].prism(M[m], [A[i], A[(i + 1) % n], B_[(i + 1) % n], B_[i]], z0, z1)
    band(0.0, t, zb, ZR, 'marble')                                                # 테
    band(t, t + 0.55, zb, ZR - 0.22, 'marble_lo', 'L2')                           # 둘레를 도는 계단 2단
    band(t + 0.55, t + 1.1, zb, ZW + 0.08, 'marble_lo', 'L2')
    L['L0'].prism(M['pool_tq'], inset(t + 1.1), zb, ZW)                           # 물
    L['L0'].prism(M['marble_lo'], inset(t + 1.1), zb - 0.01, zb)                  # (물 밑판)
    A5 = inset(t + 0.55)
    for i in range(n):                                                            # 계단 앞 모서리 밝은 띠
        L['L5'].prism(M['hl_marble'], [A5[i], A5[(i + 1) % n], inset(t + 0.4)[(i + 1) % n], inset(t + 0.4)[i]], ZR - 0.22, ZR - 0.2)
    band(0.2, 0.46, ZR, ZR + 0.03, 'porphyry', 'L3')                              # 테 윗면 반암 줄(띠)
    L['L1'].box(M['pool_deep'], ax0 + 3.0, ax1 - 3.0, ay0 + 3.0, ay0 + 4.0, ZW, ZW + 0.02)
    L['L1'].box(M['pool_deep'], bx0 + 3.0, bx1 - 3.0, by0 + 2.4, by0 + 3.2, ZW, ZW + 0.02)
    for (x0, x1, y0, y1) in ((ax0 + 2.6, ax1 - 1.6, ay0 + 5.0, ay1 - 2.0), (bx0 + 1.0, bx1 - 2.2, by0 + 4.0, by1 - 2.0)):   # 물빛 선
        r_ = 0
        yy = y0
        while yy < y1:
            k = 0; xx = x0 + (1.8 if r_ % 2 else 0.0)
            while xx < x1 - 0.6:
                b_ = min(x1, xx + 1.4 + 0.9 * R.hash01(k, r_, 3))
                L['L5'].box(M['pool_hi'], xx, b_, yy, yy + 0.12, ZW, ZW + 0.04)
                xx += 4.1; k += 1
            yy += 1.8; r_ += 1
    for k in range(10):                                                           # 젖은 테 반사띠(L6)
        a = ax0 + 1.5 + 5.6 * k
        if a < ax1 - 1.0:
            L['L6'].box(M['pool_hi'], a, a + 1.6, ay1 - 0.2, ay1 - 0.08, ZR + 0.03, ZR + 0.05)
        b2 = bx0 + 1.5 + 5.6 * k
        if b2 < bx1 - 1.5:
            L['L6'].box(M['pool_hi'], b2, b2 + 1.6, by1 - 0.2, by1 - 0.08, ZR + 0.03, ZR + 0.05)


def cal_pool(L, M):
    """칼다리움 반원 탕(남긴 뒤 반쪽 바닥을 채운다): 대리석 테 + 안쪽 계단 + 물 + 물빛 + 김"""
    n = 24
    Rp, v0, t = CAL_PR, CAL_PV, 0.5
    def arcpts(r, vv=v0):
        return [cf(r * math.cos(math.pi * i / n), vv + r * math.sin(math.pi * i / n)) for i in range(n + 1)]
    out, inn = arcpts(Rp + t), arcpts(Rp)
    for i in range(n):
        L['L0'].prism(M['marble'], [out[i], out[i + 1], inn[i + 1], inn[i]], FLOOR_C, FLOOR_C + 1.25)
    L['L0'].obox(M['marble'], CXc, CYc, DV, BV, -Rp - t, Rp + t, v0 - t, v0, FLOOR_C, FLOOR_C + 1.25)
    L['L0'].prism(M['pool_tq'], inn, FLOOR_C, FLOOR_C + 1.0)
    st = arcpts(Rp - 0.55)
    for i in range(n):
        L['L2'].prism(M['marble_lo'], [inn[i], inn[i + 1], st[i + 1], st[i]], FLOOR_C, FLOOR_C + 1.08)
    L['L5'].obox(M['hl_marble'], CXc, CYc, DV, BV, -Rp - t, Rp + t, v0 - 0.15, v0, FLOOR_C + 1.25, FLOOR_C + 1.27)
    L['L1'].prism(M['pool_deep'], arcpts(3.2, v0 + 0.6), FLOOR_C + 1.0, FLOOR_C + 1.02)
    for (a, b, c) in ((-7.0, -4.6, 2.2), (-2.0, 0.6, 4.6), (2.6, 5.0, 2.8), (-5.2, -3.0, 7.0), (3.4, 5.6, 6.8), (-0.6, 1.8, 8.6)):
        L['L5'].obox(M['pool_hi'], CXc, CYc, DV, BV, a, b, c, c + 0.12, FLOOR_C + 1.0, FLOOR_C + 1.04)


def oculus_light(L, M):
    """오큘러스 빛(16:43): 돔 아래 한 줄기 넓은 크림색 빛기둥(방출 평면, 조명 아님) + 물 위 밝은 반사 원판"""
    ztop = DRUM_H + RI * math.sin(math.acos(R_OC / RI)) - 0.3
    zbot = FLOOR_C + 1.05
    ox, oy = cf(0.0, 2.0)
    L['L5'].vplate(M['light'], ox, oy, DV, BV, [(-4.2, zbot), (4.2, zbot), (R_OC, ztop), (-R_OC, ztop)], -0.02, 0.02)      # 아래로 퍼지는 빛
    L['L5'].vplate(M['light3'], ox, oy, DV, BV, [(-2.0, zbot), (2.0, zbot), (0.7, ztop), (-0.7, ztop)], 0.03, 0.05)
    X, Y = cf(0.0, 2.0)
    L['L5'].cyl(M['light3'], X, Y, 3.0, FLOOR_C + 1.0, FLOOR_C + 1.06, 24)


def cal_upper_columns(L, M):
    """칼다리움 위층 기둥(가운데 코니스 10.9 위 → 돔 받침 코니스 18.4): 아래층과 함께 2단 기둥 열"""
    dphi = (A1 - A0) / NF
    for j in range(1, NF):
        a = math.radians(A0 + dphi * j)
        X, Y = CXc + (RI - 0.32) * math.cos(a), -(-CYc + (RI - 0.32) * math.sin(a))
        L['L2'].cyl(M['marble'], X, Y, 0.4, 10.9, 11.15, 10)
        L['L2'].cyl(M[SHAFTS[j % len(SHAFTS)]], X, Y, 0.42, 11.15, 17.7, 10, r_top=0.38)
        L['L2'].cyl(M['marble'], X, Y, 0.28, 17.7, 18.4, 10, r_top=0.45)
        for k in range(6):
            b = 2 * math.pi * k / 6
            L['L4'].cyl(M['marble_lo'], X + 0.3 * math.cos(b), Y + 0.3 * math.sin(b), 0.08, 17.7, 18.1, 5, r_top=0.02)
        L['L5'].cyl(M['hl_marble'], X, Y, 0.46, 18.4, 18.42, 10)


def build_grand(L, M, GC, root):
    wall_colonnade(L, M, FR_BL, BR_Y[1] + 0.3, BL_END - 0.3)
    wall_colonnade(L, M, FR_BR, BL_X[1] + 0.3, BR_END - 0.3, skip=((50.5, 58.5),))      # 화로·보일러 자리는 비운다
    cal_upper_columns(L, M)
    big_pool(L, M)
    cal_pool(L, M)
    oculus_light(L, M)
    zw0 = FZ + 0.05
    # 실내 가운데 기둥 2열: ① 탕 B 뒤 변(칼다리움 앞, 낮은 한 단) ② 탕 A·B 이음(X 31) 탕 속 2단
    free_row(L, M, [(X, POOL_B[2] - 0.2, zw0) for X in (35.0, 39.8, 44.6, 49.4, 54.2, 59.0)], 9.8, 1.0, 3)
    for k, Y in enumerate((44.6, 49.6, 54.0)):
        column(L, M, POOL_A[1], Y, zw0, 11.3, 1.1, 7 + k, ped=True)
        column(L, M, POOL_A[1], Y, 12.0, 20.0, 0.8, 8 + k)
    L['L2'].box(M['marble'], POOL_A[1] - 1.9, POOL_A[1] + 1.9, 42.6, 55.4, 11.3, 12.0)
    L['L5'].box(M['hl_marble'], POOL_A[1] + 1.7, POOL_A[1] + 1.9, 42.6, 55.4, 12.0, 12.03)
    L['L2'].box(M['marble'], POOL_A[1] - 1.5, POOL_A[1] + 1.5, 43.0, 55.0, 20.0, 20.7)
    for X in FRIG_COLS:                                                           # 냉탕실 열주에도 코린트 잎
        for k in range(8):
            a = 2 * math.pi * (k + 0.5) / 8
            L['L4'].cyl(M['marble_lo'], X + 1.3 * math.cos(a), 38.5 + 1.3 * math.sin(a), 0.28, 14.5, 15.0, 5, r_top=0.04)
    # 김 덩어리: 탕 위에서 피어올라 기둥 아랫부분을 살짝 덮는다
    ZW = POOL_ZW
    for k, (X, Y, sz) in enumerate(((9.5, 41.5, 1.6), (15.5, 46.0, 1.9), (22.0, 41.0, 1.7), (27.5, 49.5, 1.8), (12.0, 52.0, 1.5),
                                     (20.0, 30.5, 1.5), (11.0, 24.0, 1.4), (26.5, 26.0, 1.4),
                                     (36.5, 45.0, 1.7), (44.0, 49.0, 1.9), (51.5, 45.5, 1.7), (58.0, 50.0, 1.8), (62.0, 45.0, 1.4))):
        cloud(L, M, X, Y, ZW + 0.1, sz, 1.7 * k)
    for k, (u, v, sz) in enumerate(((-6.0, 3.2, 1.3), (5.8, 2.8, 1.3), (-2.8, 7.2, 1.1), (6.0, 7.0, 1.1))):
        X, Y = cf(u, v)
        cloud(L, M, X, Y, FLOOR_C + 1.1, sz, 2.3 * k)


def build_front_walls(L, M):
    """앞 낮은 절개 벽(세 켜 단면이 보인다) + 문턱 + 잔해. 들쭉날쭉한 윗선 = 절개·파손"""
    def segs(a, b, gap, step=2.8):
        out, x = [], a
        while x < b - 1e-6:
            x2 = min(b, x + step)
            if not (x2 <= gap[0] or x >= gap[1]):
                if x < gap[0]:
                    out.append((x, gap[0]))
                x = gap[1]
                continue
            out.append((x, x2)); x = x2
        return out

    def hgt(i, seed):
        return max(1.6, min(3.6, 2.6 + 0.8 * math.sin(0.9 * i + seed) + 0.6 * (R.hash01(i, seed) - 0.5)))
    kinds = (M['brick'], M['core'], M['brick'])
    ys = (FL_Y[0], FL_Y[0] + SK, FL_Y[1] - SK, FL_Y[1])
    for i, (a, b) in enumerate(segs(BL_X[0], FR_X[0], (37.5, 41.0))):
        h = FZ + hgt(i, 1.3)
        for k in range(3):
            L['L0'].box(kinds[k], a, b, ys[k], ys[k + 1], FZ, h)
        L['L5'].box(M['hl_brick'], a, b, ys[3] - 0.2, ys[3], h, h + 0.05)        # 보이는 바깥 면 쪽 윗선
        if i % 3 == 1:          # L6 빗물 자국(잘린 윗선에서 아래로)
            L['L6'].box(M['stain'], a + 0.6, a + 0.85, ys[3], ys[3] + 0.06, FZ + 0.4, h - 0.2)
    xs = (FR_X[0], FR_X[0] + SK, FR_X[1] - SK, FR_X[1])
    for i, (a, b) in enumerate(segs(CIS[3], FL_Y[1], (27.0, 30.5))):
        h = FZ + hgt(i, 4.1)
        for k in range(3):
            L['L0'].box(kinds[k], xs[k], xs[k + 1], a, b, FZ, h)
        L['L5'].box(M['hl_brick'], xs[3] - 0.2, xs[3], a, b, h, h + 0.05)
        if i % 3 == 2:
            L['L6'].box(M['stain'], xs[3], xs[3] + 0.06, a + 0.7, a + 0.95, FZ + 0.4, h - 0.2)
    L['L2'].box(M['marble'], 37.5, 41.0, FL_Y[0], FL_Y[1], FZ, FZ + 0.12)
    L['L2'].box(M['marble'], FR_X[0], FR_X[1], 27.0, 30.5, FZ, FZ + 0.12)
    for i, (X, Y) in enumerate(((12.0, 53.6 + DY), (26.5, 53.4 + DY), (45.0, 53.7 + DY), (60.2 + DX, 53.5 + DY),
                                (68.2 + DX, 20.0), (68.4 + DX, 44.0), (66.9 + DX, 52.6 + DY))):
        a = 0.7 * i
        L['L4'].obox(M['brick'] if i % 2 else M['core'], X, Y, (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a)),
                     -0.4, 0.4, -0.25, 0.25, FZ, FZ + 0.3 + 0.25 * R.hash01(i, 9))


def build_caracalla(GC, CM, M):
    root = G.new_root('BATHS_Caracalla_root', GC, BATH_ORIGIN[0], BATH_ORIGIN[1], 0.0)
    L = layers('Caracalla')
    build_floor(L, M)
    build_back_walls(L, M)
    build_caldarium(L, M, GC, root)
    build_frig_vault(GC, root, M, L)
    build_service(L, M)
    build_frigidarium(L, M)
    build_front_walls(L, M)
    if GRAND:
        build_grand(L, M, GC, root)
    obs = [L[k].obj(GC, root) for k in sorted(L)]
    # L6 사람(목욕객·시중꾼·화부, 키 2.4) · 풀 · 암포라 · 화분
    ppl = []
    for (u, v) in ((-3.0, 5.6), (0.6, 5.2), (3.4, 6.0)):                    # 뜨거운 욕조 속(욕조 바닥 = FLOOR_C, 허리까지 잠김)
        X, Y = cf(u, v); ppl.append((X, Y, FLOOR_C))
    for (u, v) in ((-6.8, 5.6), (7.6, 3.0), (-1.2, 1.4)):
        X, Y = cf(u, v); ppl.append((X, Y, FLOOR_C))
    for (X, Y) in ((12.5, 46.5 + DY), (17.8, 49.2 + DY), (22.6, 45.2 + DY), (26.9, 48.6 + DY)):  # 수영장 속(바닥 = FZ + 0.05)
        ppl.append((X, Y, FZ + 0.05))
    for (X, Y) in ((10.8, 34.6), (15.9, 36.0), (20.6, 34.8), (25.8, 35.6), (31.0, 44.0 + DY), (34.5, 49.0 + DY), (39.2, 52.0 + DY),
                   (66.8 + DX, 28.8), (58.4, 47.4 + DY), (52.6, 50.8 + DY), (65.6 + DX, 43.6 + DY), (9.6, 24.5), (14.2, 21.4),
                   (21.0, 27.5), (29.0, 14.6), (36.2, 9.0)):
        on_frig = (5.4 <= X <= 30.0 and VY0 + 0.3 <= Y <= FL_Y[0] - 0.1)
        ppl.append((X, Y, FZ + (0.05 if on_frig else 0.0)))
    ppl.append((57.6, 8.4, FZ))                                               # 화부(불 때는 일꾼)
    ppl.append((58.2, 13.2, FZ))                                              # 장작 나르는 일꾼
    for i, (X, Y, Z) in enumerate(ppl):
        person(GC, root, i, X, Y, Z, 'BATHS_Caracalla_L6_Person%02d' % i)
    tuft = [(3.4, BL_END + 0.8, 24.0, 1.2), (3.6, BL_END + 2.3, 15.5, 1.0), (3.3, BL_END + 3.4, 8.0, 1.1),
            (14.0, WY - 0.5, FZ, 1.4), (30.0, WY - 0.45, FZ, 1.2), (52.0, WY - 0.5, FZ, 1.5), (63.0 + DX, WY - 0.45, FZ, 1.1),
            (WX - 0.5, 22.0, FZ, 1.3), (WX - 0.4, 40.0, FZ, 1.4), (WX - 0.5, 50.5 + DY, FZ, 1.2), (6.0, WY - 0.5, FZ, 1.0)]
    for i, (X, Y, Z, s) in enumerate(tuft):
        place(GC, root, 'P_bush%d' % (i % 4), X, Y, Z, s, 37.0 * i, 'BATHS_Caracalla_L6_Tuft%02d' % i)
    for i, (X, Y) in enumerate(((57.4, 12.7), (57.95, 13.25), (57.2, 13.45), (35.6, 52.6 + DY), (36.3, 53.1 + DY))):
        place(GC, root, 'P_amphora', X, Y, FZ, 0.45 * P_H / 0.75, 20.0 * i, 'BATHS_Caracalla_L6_Amphora%02d' % i)
    # 화분 나무(테라코타 화분 + 덤불): 열주 끝·모자이크판 둘레·드럼 앞
    pots = Lay('BATHS_Caracalla_L6_Pots')
    if not DECOR:                                                             # 16:14: 화분 나무 0
        return root, [o for o in obs if o]
    for i, (X, Y) in enumerate(((6.9, 33.2), (31.6, 34.6), (45.2, 45.8), (67.0 + DX, 45.8 + DY), (66.6 + DX, 53.0 + DY), (44.4, 53.2 + DY))):
        pots.cyl(M['terra'], X, Y, 0.55, FZ, FZ + 0.75, 10, r_top=0.7)
        pots.cyl(M['terra_dk'], X, Y, 0.62, FZ + 0.75, FZ + 0.85, 10)
        place(GC, root, 'P_bush%d' % (i % 4), X, Y, FZ + 0.6, 2.4, 53.0 * i, 'BATHS_Caracalla_L6_Shrub%02d' % i)
    pots.obj(GC, root)
    return root, [o for o in obs if o]


# ═════════════════════════════════════ 수도교 ═════════════════════════════════════
def lining(lay, m, u0, u1, zb, zs, t0, t1, inset=0.05, n=12):
    """L1 깊이색: 관통 아치 개구부 안쪽 면(문설주·홍예 안쪽)을 개구부 쪽으로 inset 들인 띠 면. 법선은 개구부 가운데를 본다"""
    bm = lay.bm
    rr = (u1 - u0) / 2.0 - inset; cu = (u0 + u1) / 2.0
    prof = [(u0 + inset, zb)] + [(cu - rr * math.cos(math.pi * k / n), zs + rr * math.sin(math.pi * k / n)) for k in range(n + 1)] + [(u1 - inset, zb)]
    prof = dedup(prof)
    mi = lay.mi(m)
    for k in range(len(prof) - 1):
        (ua, za), (ub, zb_) = prof[k], prof[k + 1]
        q = [bm.verts.new((ua, -t0, za)), bm.verts.new((ub, -t0, zb_)), bm.verts.new((ub, -t1, zb_)), bm.verts.new((ua, -t1, za))]
        f = bm.faces.new(q); f.material_index = mi


def ivy(lay, M, u_c, t, h, w, seed):
    """L6 담쟁이: 교각 앞면(+Y)에 붙은 잎 무리(짙은·가운데·밝은 잎 세 색, 아래가 넓다)"""
    rng = 0
    for k in range(int(26 + 10 * w)):
        rng += 1
        s = R.hash01(seed, k, 1)
        z = h * (s ** 0.8)
        half = w * (1.0 - 0.55 * (z / h)) / 2.0
        u = u_c + (R.hash01(seed, k, 2) * 2.0 - 1.0) * half
        r = 0.32 + 0.22 * R.hash01(seed, k, 3)
        c = R.hash01(seed, k, 4)
        m = M['ivy'] if c < 0.42 else (M['ivy2'] if c < 0.85 else M['ivy_hi'])
        dt = 0.18 + 0.04 * (k % 3)
        pts = [(u + r * math.cos(a), max(0.0, z) + r * 0.85 * math.sin(a)) for a in (0.3, 1.5, 2.6, 3.7, 4.9)]
        lay.vplate(m, 0.0, 0.0, (1.0, 0.0), (0.0, 1.0), pts, t + dt, t + dt + 0.03)


AQ_PDG = dict(pitch=18.0, w_lo=13.6, w_hi=12.8, n_small=5, w_small=2.2, center_X=395.0, k_w=2.5)   # 23:29: 퐁 뒤 가르 비율(None = 옛 좁은 아치) · 00:16 사용자: 폭(축에 수직 두께) 2.5배


def build_aqueduct(GC, CM, M):
    """아쿠아 안토니니아나(아쿠아 마르키아 지선) 급수 관계 모식(d4 관통 아치): 마름돌 2단 관통 아치(아래 개구 5.3 · 위 3.9,
    교각 간격 8, 아치 안쪽 면 화면 1.5mm) + 벽돌 수로 단(안은 분홍 방수 모르타르·물빛 선, 덮개돌은 두 칸마다)"""
    AQ = CM['aqueduct']
    (x0s, y0s), (x1s, y1s) = AQ['ground_line_screen']
    H = float(AQ['arch_height_mm'])
    pitch = float(AQ.get('pier_pitch_mm', AQ_PITCH))
    w_lo = float(AQ.get('opening_lower_mm', AQ_WLO)); w_hi = float(AQ.get('opening_upper_mm', AQ_WHI))
    if AQ_PDG:                                            # 23:29 사용자: 레퍼런스(퐁 뒤 가르) 비율 — 넓은 아치 3단(아래·가운데 같은 칸, 맨 위 한 칸에 5개)
        pitch, w_lo, w_hi = AQ_PDG['pitch'], AQ_PDG['w_lo'], AQ_PDG['w_hi']
    jamb = float(AQ.get('inner_face_mm', AQ_JAMB))
    KW = AQ_PDG.get('k_w', 1.0) if AQ_PDG else 1.0         # 00:16 사용자 '폭을 늘리라고': 단면 치수(교각·볼트 깊이·단 상판·수로 폭)만 KW배, 길이·아치 수·단 높이는 그대로
    TT = jamb / R.C30 * KW; T = TT / 2.0                  # 벽 두께(평면) 1.732 × KW: 화면 안쪽 면 폭 = c30 × TT
    CW = 0.55 * KW                                        # 수로 물 폭 반(방수 모르타르 0.1 바깥이 수로 벽)
    X0, Y0 = R.to_plan(x0s, y0s); X1, _ = R.to_plan(x1s, y1s)
    LA = (X1 - X0) + 4.0                                  # 오른쪽 변 밖으로 블리드
    root = G.new_root('BATHS_Aqueduct_root', GC, X0, Y0, 0.0)
    L = layers('Aqueduct')
    U0, Z0 = -0.05, -0.05                                 # 왼쪽 끝은 저수조 속으로 0.05 묻는다 · 밑면은 땅 바로 아래
    UA = 0.35                                             # 내민 부재(띠돌·코니스·수로 단)는 맞댐 덩어리 다음부터: 화면 왼쪽 끝 ≥ 335.2
    # 18:40 메인·레퍼런스(user_aqueduct 퐁 뒤 가르) 3단: 아래 큰 아치(벽이 더 두껍다) · 가운데 큰 아치(조금 낮게) · 맨 위 작은 아치(큰 칸 하나에 3개) · 돌 수로
    #   높이 26(spec) 안에 단 높이를 나눈다: 아래 0~10.6 · 띠돌 10.6~11.0 · 가운데 11.0~19.8 · 코니스 19.8~20.2 · 맨 위 20.2~23.9 · 띠돌 23.9~24.2 · 수로 24.2~26
    kH = H / 26.0                                         # 20:01 d5 높이 24 등: 단 높이를 비례로(메인 18:40 '상자 높이가 모자라면 비례대로')
    ZSC0, ZSC1, ZC0, ZC1 = 10.6 * kH, 11.0 * kH, 19.8 * kH, 20.2 * kH
    ZT1, ZT2 = H - 2.1 * kH, H - 1.8 * kH                 # 맨 위 단 윗 띠돌
    ZCH0, ZWT = ZT2, H - 0.4 * kH                         # 수로 바닥 · 물 윗면
    if not AQ_PDG:
        w_lo = max(w_lo, 5.6); w_hi = min(w_lo - 0.4, pitch - 2.8)   # 가운데 단도 큰 아치(spec 위층 3.9 → 5.2, 퐁 뒤 가르)
    S1, S2_ = ZSC0 - 0.6 * kH - w_lo / 2.0, ZC0 - 0.6 * kH - w_hi / 2.0   # 홍예 기점
    TL = T + 0.3 * KW                                     # 아래 단 벽 두께 반(가운데 단보다 0.3 × KW 두껍다 → 단마다 턱)
    nb = int(LA // pitch) + 1
    c0 = (AQ_PDG['center_X'] - X0) % pitch if AQ_PDG else 4.0          # PDG: 강 가운데(평면 X)에 아치 하나가 오게
    cen = [pitch * k + c0 for k in range(nb + 1)]
    lo = [(c - w_lo / 2.0, c + w_lo / 2.0) for c in cen if c + w_lo / 2.0 < LA - 0.6]
    hi = [(c - w_hi / 2.0, c + w_hi / 2.0) for c in cen if c + w_hi / 2.0 < LA - 0.6]
    st, br = M['aq_stone'], M['aq_stone']              # 16:25 레퍼런스(퐁 뒤 가르): 수로 단도 돌(붉은 벽돌 0)
    # 16:25 레퍼런스: 맨 위 작은 아치 줄(큰 아치 1칸에 3개)이 수로 바닥 단(ZC1~ZCH0)을 받친다
    NSM = AQ_PDG['n_small'] if AQ_PDG else 3
    WSM = AQ_PDG['w_small'] if AQ_PDG else 1.8
    sm = [(pitch * k + pitch * (j + 0.5) / NSM - WSM / 2, pitch * k + pitch * (j + 0.5) / NSM + WSM / 2)
          for k in range(nb) for j in range(NSM) if pitch * k + pitch * (j + 0.5) / NSM + WSM / 2 < LA - 0.4 and pitch * k + pitch * (j + 0.5) / NSM - WSM / 2 > UA + 0.3]
    ZSM = ZC1 + 1.55 * kH                                 # 작은 아치 홍예 기점(꼭대기 ZSM + 0.9 < ZT1)
    # L0 덩어리: 아래 단(관통 아치) · 띠돌 · 위 단 · 코니스 · 수로 단(벽돌)
    L['L0'].wall_x(st, U0, LA, -TL, TL, Z0, ZSC0, [('arch', a, b, Z0, S1) for (a, b) in lo])
    L['L0'].wall_x(st, U0, LA, -T, T, ZSC1, ZC0, [('arch', a, b, ZSC1, S2_) for (a, b) in hi])
    L['L0'].box(st, U0, UA, -T, T, ZC0, ZCH0)                                   # 맞댐 덩어리(저수조 오른쪽 면에 붙는다)
    L['L0'].box(st, U0, UA, -TL, TL, Z0, ZSC0)
    L['L0'].box(st, U0, UA, -T, -CW, ZCH0, H)                                   # 수로가 지나는 홈(물이 저수조로 든다)
    L['L0'].box(st, U0, UA, CW, T, ZCH0, H)
    L['L0'].wall_x(br, UA, LA, -T, T, ZC1, ZT1, [('arch', a, b, ZC1, ZSM) for (a, b) in sm])   # 맨 위 단(작은 관통 아치 줄)
    L['L0'].box(br, UA, LA, -T, -CW - 0.1, ZCH0, H)                             # 수로 뒤 벽(높이 26 = spec)
    L['L0'].box(br, UA, LA, CW + 0.1, T, ZCH0, H)                                   # 수로 앞 벽
    # L1 깊이색: 관통 아치 안쪽 면(문설주·홍예 안쪽, d4 0.78) — 개구부 뒤로 땅이 보인다
    for (a, b) in lo:
        lining(L['L1'], M['aq_stone_lo'], a, b, Z0, S1, -TL, TL)
    for (a, b) in hi:
        lining(L['L1'], M['aq_stone_lo'], a, b, ZSC1, S2_, -T, T)
    L['L1'].box(M['deeper'], UA, LA, -CW, CW, ZCH0 + 0.1, ZCH0 + 0.16)          # 수로 바닥 그늘(물 밑)
    for (a, b) in sm:
        lining(L['L1'], M['aq_stone_lo'], a, b, ZC1, ZSM, -T, T, n=8)
    # L2 부재: 띠돌·코니스·홍예석(두 색 번갈아)·덮개돌(두 칸마다)
    L['L2'].box(M['aq_trav'], UA, LA, -TL - 0.25, TL + 0.25, ZSC0, ZSC1)
    L['L2'].box(M['aq_trav'], UA, LA, -T - 0.32, T + 0.32, ZC0, ZC1)
    L['L2'].box(M['aq_trav'], UA, LA, -T - 0.2, T + 0.2, ZT1, ZT2)                # 맨 위 단 띠돌(수로 받침)
    for (lst, zs, nv, tv) in ((lo, S1, 9, TL), (hi, S2_, 9, T)):
        for (a, b) in lst:
            cu, rr = (a + b) / 2.0, (b - a) / 2.0
            r1, r2 = rr + 0.02, rr + 0.55
            for i in range(nv):
                a0, a1 = math.pi * i / nv, math.pi * (i + 1) / nv
                pts = [(cu + r1 * math.cos(a0), zs + r1 * math.sin(a0)), (cu + r2 * math.cos(a0), zs + r2 * math.sin(a0)),
                       (cu + r2 * math.cos(a1), zs + r2 * math.sin(a1)), (cu + r1 * math.cos(a1), zs + r1 * math.sin(a1))]
                L['L2'].vplate(M['aq_trav'] if i % 2 else M['aq_blk3'], 0.0, 0.0, (1.0, 0.0), (0.0, 1.0), pts, tv, tv + 0.08)
    covers = []
    u = 2.0 * pitch + 0.6
    while u + 2.4 < LA:
        covers.append((u, u + 2.4)); u += 2.0 * pitch
    for (a, b) in covers:
        L['L2'].box(M['aq_trav'], a, b, -T - 0.2, T + 0.2, H, H + 0.3)
    # L3 표면 무늬: 마름돌 색 변화(앞면 블록 몇 개) · 수로 단 기와 이음 켜 · 띠돌 아래 줄눈 강조
    for k in range(int(LA // 2.0)):
        for row in range(12):
            z0 = row * 1.0
            uu = 2.0 * k + (1.0 if row % 2 else 0.0)
            hsh = R.hash01(k, row, 7)
            if hsh > 0.2 or uu + 1.9 > LA:
                continue
            ok = True
            for (a, b) in lo:
                if uu + 1.9 > a - 0.6 and uu < b + 0.6 and z0 < S1 + (b - a) / 2.0 + 0.7:
                    ok = False
            if ok and z0 + 0.9 < ZSC0:
                L['L3'].box(M['aq_blk2'] if hsh < 0.1 else M['aq_blk3'], uu + 0.05, uu + 1.95, TL, TL + 0.04, z0 + 0.05, z0 + 0.95)
        for row in range(9):
            z0 = ZSC1 + row * 1.0
            uu = 2.0 * k + (1.0 if row % 2 else 0.0)
            hsh = R.hash01(k, row, 11)
            if hsh > 0.2 or uu + 1.9 > LA or z0 + 0.9 > ZC0:
                continue
            if any(uu + 1.9 > a - 0.6 and uu < b + 0.6 and z0 < S2_ + (b - a) / 2.0 + 0.7 for (a, b) in hi):
                continue
            L['L3'].box(M['aq_blk2'] if hsh < 0.1 else M['aq_blk3'], uu + 0.05, uu + 1.95, T, T + 0.04, z0 + 0.05, z0 + 0.95)
    for (lst, z0p, z1p, tv) in ((lo, 0.4, ZSC0 - 0.2, TL), (hi, ZSC1 + 0.3, ZC0 - 0.2, T)):   # 18:40 3단: 교각 마름돌 켜 선(L3)
        prs = [(UA if k == 0 else lst[k - 1][1], lst[k][0]) for k in range(len(lst))]
        for (a, b) in prs:
            if b - a < 0.8:
                continue
            zz = z0p + 0.4
            while zz < z1p:
                L['L3'].box(M['aq_band'], a + 0.12, b - 0.12, tv, tv + 0.03, zz, zz + 0.05)
                zz += 0.75
    for (lst, zb, zs, tv) in ((lo, Z0, S1, TL), (hi, ZSC1, S2_, T)):            # 00:16 넓어진 볼트: 홍예 링 이음(폭 1.15마다) · 문설주 켜 선(0.75마다)
        nr = max(1, int(round(2.0 * tv / 1.15)))
        for (a, b) in lst:
            cu, rr = (a + b) / 2.0, (b - a) / 2.0 - 0.08
            arc = [(cu - rr * math.cos(math.pi * k / 16), zs + rr * math.sin(math.pi * k / 16)) for k in range(17)]
            for j in range(1, nr):
                t0_ = -tv + 2.0 * tv * j / nr - 0.025
                for k in range(16):
                    (ua, za), (ub, zb_) = arc[k], arc[k + 1]
                    q = [L['L3'].bm.verts.new((ua, -t0_, za)), L['L3'].bm.verts.new((ub, -t0_, zb_)), L['L3'].bm.verts.new((ub, -t0_ - 0.05, zb_)), L['L3'].bm.verts.new((ua, -t0_ - 0.05, za))]
                    L['L3'].bm.faces.new(q).material_index = L['L3'].mi(M['aq_band'])
            zz = zb + 0.75
            while zz < zs - 0.1:
                q = [L['L3'].bm.verts.new((a + 0.08, tv, zz)), L['L3'].bm.verts.new((a + 0.08, -tv, zz)), L['L3'].bm.verts.new((a + 0.08, -tv, zz + 0.05)), L['L3'].bm.verts.new((a + 0.08, tv, zz + 0.05))]
                L['L3'].bm.faces.new(q).material_index = L['L3'].mi(M['aq_band'])
                zz += 0.75
    for (a, b) in [(UA if k == 0 else sm[k - 1][1], sm[k][0]) for k in range(len(sm))]:
        if b - a > 0.3:
            for zz in (ZC1 + 0.6, ZC1 + 1.2):
                L['L3'].box(M['aq_band'], a + 0.06, b - 0.06, T, T + 0.03, zz, zz + 0.04)
    for z in (ZCH0 + 0.4, H - 0.6):
        L['L3'].box(M['aq_band'], UA, LA, T, T + 0.05, z, z + 0.16)             # 수로 벽 돌 줄눈 띠
    L['L3'].box(M['aq_band'], U0, LA, TL, TL + 0.04, ZSC0 - 0.12, ZSC0)
    # L4 형태 디테일: 수로 안 분홍 방수 모르타르(오푸스 시그니눔) + 물 · 비계 구멍 · 홍예 머릿돌 · 경계석(키푸스)
    L['L4'].box(M['signinum'], UA, LA, -CW - 0.1, -CW, ZCH0, H)
    L['L4'].box(M['signinum'], UA, LA, -CW, CW + 0.1, ZCH0, ZCH0 + 0.1)
    L['L4'].box(M['signinum'], UA, LA, CW, CW + 0.1, ZCH0, H)
    L['L4'].box(M['water'], U0, LA, -CW, CW, ZCH0 + 0.16, ZWT)
    for k in range(nb + 1):
        for z in (3.6, 6.4):
            if pitch * k + 0.9 > U0 and pitch * k + 0.9 < LA - 0.5:
                L['L4'].box(M['deeper'], pitch * k + 0.2, pitch * k + 0.6, TL, TL + 0.07, z, z + 0.4)
        if pitch * k + 3.2 < LA - 0.5:
            L['L4'].box(M['deeper'], pitch * k + 0.0, pitch * k + 0.4, T, T + 0.07, 17.8, 18.2)
    for (lst, zs, tv) in ((lo, S1, TL), (hi, S2_, T)):
        for (a, b) in lst:
            cu, rr = (a + b) / 2.0, (b - a) / 2.0
            L['L4'].vplate(M['aq_trav'], 0.0, 0.0, (1.0, 0.0), (0.0, 1.0),
                           [(cu - 0.32, zs + rr - 0.05), (cu + 0.32, zs + rr - 0.05), (cu + 0.42, zs + rr + 0.65), (cu - 0.42, zs + rr + 0.65)], tv, tv + 0.14)
    for k in range(nb + 1):     # 16:25 레퍼런스: 교각 앞 돌출 돌(코벨, 비계 받침) — 띠돌 밑·코니스 밑
        uc = pitch * k + 0.7
        if UA + 0.3 < uc < LA - 0.8:
            for zz, tv in ((ZSC0 - 1.6, TL), (ZC0 - 1.4, T)):
                L['L4'].box(M['aq_trav'], uc - 0.3, uc + 0.3, tv, tv + 0.4, zz, zz + 0.4)
                L['L5'].box(M['hl_trav'], uc - 0.3, uc + 0.3, tv + 0.05, tv + 0.4, zz + 0.4, zz + 0.44)
    for k in (2, 9, 11):        # 라벨 칸(기초선 u 53~61) 위·오른쪽 끝(상자 아래 변)은 비운다
        if pitch * k + 1.8 < LA:
            L['L4'].box(M['aq_trav'], pitch * k + 0.6, pitch * k + 1.8, TL + 0.6, TL + 1.2, 0.0, 1.0)
            L['L5'].box(M['hl_trav'], pitch * k + 0.6, pitch * k + 1.8, TL + 1.0, TL + 1.2, 1.0, 1.05)
    # 18:58 레퍼런스(퐁 뒤 가르) 잣대: 교각 비계 돌 줄 더하기(L4) · 맨 위 작은 아치 홍예석(L2) · 2단 얼룩 조각(L6)
    for k in range(nb + 1):
        uc = pitch * k - 0.6
        if UA + 0.3 < uc < LA - 0.8:
            for zz in (2.2, 5.6, ZSC1 + 1.6, ZSC1 + 4.6):
                tv = TL if zz < ZSC0 else T
                L['L4'].box(M['aq_trav'], uc - 0.22, uc + 0.22, tv, tv + 0.3, zz, zz + 0.32)
                L['L5'].box(M['hl_trav'], uc - 0.22, uc + 0.22, tv + 0.04, tv + 0.3, zz + 0.32, zz + 0.35)
    for (a, b) in sm:
        cu, rr = (a + b) / 2.0, (b - a) / 2.0
        for i in range(5):
            a0, a1 = math.pi * i / 5 + 0.04, math.pi * (i + 1) / 5 - 0.04
            pts = [(cu + (rr + 0.02) * math.cos(a0), ZSM + (rr + 0.02) * math.sin(a0)), (cu + (rr + 0.3) * math.cos(a0), ZSM + (rr + 0.3) * math.sin(a0)),
                   (cu + (rr + 0.3) * math.cos(a1), ZSM + (rr + 0.3) * math.sin(a1)), (cu + (rr + 0.02) * math.cos(a1), ZSM + (rr + 0.02) * math.sin(a1))]
            L['L2'].vplate(M['aq_trav'] if i % 2 else M['aq_blk3'], 0.0, 0.0, (1.0, 0.0), (0.0, 1.0), pts, T, T + 0.06)
    def in_open(u, z):
        for (lst, zb, zs) in ((lo, Z0, S1), (hi, ZSC1, S2_)):
            for (a, b) in lst:
                cu, rr = (a + b) / 2.0, (b - a) / 2.0
                if a - 0.15 < u < b + 0.15 and zb - 0.1 < z < zs + math.sqrt(max(0.0, (rr + 0.65) ** 2 - (u - cu) ** 2)):
                    return True
        return False
    n_ok = j = 0
    while n_ok < 130 and j < 3000:
        u = UA + 0.4 + (LA - UA - 1.2) * R.hash01(j, 81); z = 0.4 + (ZC0 - 0.8) * R.hash01(j, 82); j += 1
        w = 0.35 + 0.8 * R.hash01(j, 83); h = 0.3 + 0.7 * R.hash01(j, 84)
        if ZSC0 - 0.3 < z + h / 2 and z - h / 2 < ZSC1 + 0.3:
            continue
        if any(in_open(u + du, z + dz) for du in (-w / 2, w / 2) for dz in (-h / 2, h / 2)):
            continue
        pts = [(u - w / 2, z - h / 2), (u + w * 0.3, z - h / 2 - 0.05), (u + w / 2, z), (u + w * 0.2, z + h / 2), (u - w * 0.35, z + h / 2 + 0.04), (u - w / 2 - 0.04, z + 0.05)]
        tv = TL if z < ZSC0 else T
        L['L6'].vplate((M['aq_blk2'], M['stain_st'], M['aq_blk3'])[n_ok % 3], 0.0, 0.0, (1.0, 0.0), (0.0, 1.0), pts, tv, tv + 0.05)
        n_ok += 1
    # L5 하이라이트: 띠돌·코니스·앞 난간·덮개돌 윗선, 교각 왼쪽 모서리 세로 띠, 물빛 선(흐름)
    L['L5'].box(M['hl_trav'], UA, LA, TL + 0.07, TL + 0.25, ZSC1, ZSC1 + 0.05)
    L['L5'].box(M['hl_trav'], UA, LA, T + 0.12, T + 0.32, ZC1, ZC1 + 0.05)
    L['L5'].box(M['hl_trav'], UA, LA, T + 0.05, T + 0.2, ZT2, ZT2 + 0.05)
    L['L5'].box(M['hl_trav'], UA, LA, T - 0.15, T, H, H + 0.05)
    L['L5'].box(M['hl_stone'], U0, UA, T - 0.2, T, H, H + 0.05)
    for (a, b) in covers:
        L['L5'].box(M['hl_trav'], a, b, T + 0.05, T + 0.2, H + 0.3, H + 0.35)
        L['L5'].box(M['hl_trav'], b - 0.18, b, -T - 0.2, T + 0.2, H + 0.3, H + 0.35)
    piers_lo = [(U0 if k == 0 else lo[k - 1][1], lo[k][0]) for k in range(len(lo))]
    for (a, b) in piers_lo:
        if b - a > 0.6:
            L['L5'].box(M['hl_stone'], a + 0.02, a + 0.3, TL, TL + 0.1, 0.4, S1 - 0.2)
    piers_hi = [(U0 if k == 0 else hi[k - 1][1], hi[k][0]) for k in range(len(hi))]
    for (a, b) in piers_hi:
        if b - a > 0.6:
            L['L5'].box(M['hl_stone'], a + 0.02, a + 0.3, T, T + 0.1, ZSC1 + 0.3, S2_ - 0.2)
    for j in range(max(1, int(2.0 * CW / 1.1))):                               # 물빛 선: 수로 폭 1.1마다 한 줄(엇갈려)
        yy = -CW + 0.25 + j * 1.1
        u = 1.0 + 2.4 * (j % 2)
        while u < LA - 2.0:
            L['L5'].box(M['water_hi'], u, u + 2.6, yy, yy + 0.15, ZWT, ZWT + 0.05)
            u += 5.3
    # L6 석회 자국(코니스·띠돌 아래 흰 줄) · 빗물 자국 · 이끼 · 담쟁이 · 풀 · 길손
    for k in (1, 4, 6, 9, 11):
        a = pitch * k + 0.4 + 1.2 * R.hash01(k, 2)
        L['L6'].box(M['calcite'], a, a + 0.22, T, T + 0.12, ZC0 - 2.8 - 1.5 * R.hash01(k, 3), ZC0 - 0.05)
    for k in (2, 5, 8, 10):
        a = pitch * k + 0.2 + 1.0 * R.hash01(k, 5)
        L['L6'].box(M['stain_st'], a, a + 0.3, TL, TL + 0.12, ZSC0 - 3.6, ZSC0 - 0.15)
    for (a, b) in piers_lo:
        L['L6'].box(M['moss'], a, b, TL, TL + 0.13, 0.0, 0.5 + 0.7 * R.hash01(int(a * 10), 4))
    for (k, hgt_, w) in ((3, 6.5, 2.4), (6, 8.8, 2.6), (10, 5.6, 2.2), (12, 7.4, 2.5)):
        uc = pitch * k + 0.05
        if uc < LA - 1.5 and not (AQ_LABEL_FREE[0] - 2 <= uc <= AQ_LABEL_FREE[1] + 2):
            ivy(L['L6'], M, uc, TL, min(hgt_, ZSC0 - 0.4), w, k)
    obs = [L[k].obj(GC, root) for k in sorted(L)]

    def free(u):
        return not (AQ_LABEL_FREE[0] <= u <= AQ_LABEL_FREE[1]) and 1.5 <= u <= 86.0
    for k in range(nb + 1):
        for j, du in enumerate((-0.6, 3.0)):
            u = pitch * k + 1.2 + du
            if u < 0.4 or u > LA - 1.0 or not free(u):
                continue
            place(GC, root, 'P_bush%d' % ((k + j) % 4), u, TL + 0.7 + 0.3 * j, 0.0, 1.1 + 0.4 * R.hash01(k, j), 31.0 * k,
                  'BATHS_Aqueduct_L6_Tuft%02d' % (2 * k + j))
    for i, k in enumerate((1, 3, 5, 8, 10, 12)):          # 교각 밑 덤불(LocalBanana 식생 밀도)
        u = pitch * k + 0.4 + 1.6 * R.hash01(k, 7)
        if free(u) and u < LA - 1.0:
            place(GC, root, 'P_bush%d' % (i % 4), u, TL + 1.1, 0.0, 2.0 + 0.8 * R.hash01(k, 8), 67.0 * i,
                  'BATHS_Aqueduct_L6_Bush%02d' % i)
    place(GC, root, 'P_person1', 37.0, T + 2.2, 0.0, P_H, 120.0, 'BATHS_Aqueduct_L6_Person00')
    place(GC, root, 'P_person2', 38.6, T + 2.6, 0.0, P_H, 140.0, 'BATHS_Aqueduct_L6_Person01')
    return root, [o for o in obs if o], dict(T=T, T_lo=TL, lo=lo, hi=hi, S1=S1, S2=S2_, ZSC1=ZSC1, LA=LA, H=H,
                                             ZSC0=ZSC0, ZC0=ZC0, ZC1=ZC1, ZT1=ZT1, sm=sm, ZSM=ZSM, U0=U0, X0=X0, Y0=Y0)   # 21:55: 수면 반영용 단 높이


# ═════════════════════════════════════ 측정·앵커 ═════════════════════════════════════
def _kids(root):
    return [o for o in root.children_recursive if o.type == 'MESH' and not o.hide_render]


def screen_tris(obs):
    """메시들의 삼각형 화면 좌표(mm) 목록: [(x0,y0,x1,y1,x2,y2), ...]"""
    out = []
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in obs:
        me = ob.evaluated_get(dg).data
        me.calc_loop_triangles()
        mw = ob.matrix_world
        sc = [R.scr(mw @ v.co) for v in me.vertices]
        for t in me.loop_triangles:
            a, b, c = t.vertices
            out.append((*sc[a], *sc[b], *sc[c]))
    return out


def clip_bbox(tris, xmax=PAGE_W):
    """삼각형들을 x ≤ xmax로 자른 화면 외곽 상자"""
    x0 = y0 = 1e9; x1 = y1 = -1e9
    for t in tris:
        pts = [(t[0], t[1]), (t[2], t[3]), (t[4], t[5])]
        poly = []
        for i in range(3):
            p, q = pts[i], pts[(i + 1) % 3]
            pin, qin = p[0] <= xmax, q[0] <= xmax
            if pin:
                poly.append(p)
            if pin != qin:
                s = (xmax - p[0]) / (q[0] - p[0])
                poly.append((xmax, p[1] + s * (q[1] - p[1])))
        for (x, y) in poly:
            x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x), max(y1, y)
    return [round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)]


def anchor(GC, root, name, world_co):
    e = bpy.data.objects.new(name, None)
    GC.objects.link(e)
    e.empty_display_type = 'PLAIN_AXES'; e.empty_display_size = 1.0
    e.parent = root
    e.location = root.matrix_world.inverted() @ world_co
    e.hide_render = True
    return e


def _solve_lin(f, t0, t1, target):
    """f(t)가 t에 대해 1차일 때 f(t) = target인 t"""
    a, b = f(t0), f(t1)
    return t0 + (target - a) * (t1 - t0) / (b - a)


ANCHOR_PT = {'L3_label': (234.86, 117.89), 'L4_label': (384.15, 187.97), 'L4_m1': (372.0, 163.0)}   # d4 지시선 끝·짝 표지(잠정, D11)


def spec_anchor_pts(S):
    """d5 spec에 blender_anchor 열쇠가 있으면 그 점(target_pt·map_pt·pt·pts 끝)을 쓴다. 없으면 ANCHOR_PT(D1)"""
    out = dict(ANCHOR_PT)

    def walk(o):
        if isinstance(o, dict):
            ba = o.get('blender_anchor')
            if isinstance(ba, str):
                key = ba[len('ANCHOR_'):] if ba.startswith('ANCHOR_') else ba
                pt = o.get('target_pt') or o.get('map_pt') or o.get('pt') or (o.get('pts') or [None])[-1]
                if key in out and isinstance(pt, (list, tuple)) and len(pt) == 2:
                    out[key] = (float(pt[0]), float(pt[1]))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(S)
    return out


LAST_AQI = None


def make_anchors(GC, broot, aroot, AQI, PT=ANCHOR_PT):
    """앵커(D11): 정보 층 지시선·짝 표지가 가리키는 보이는 면 위 3D 점"""
    out = {}
    if broot is None:                                                   # 21:38: 욕장 0 → L3_label 앵커 0(수도교 앵커만)
        old = bpy.data.objects.get('ANCHOR_L3_label')
        if old is not None:
            bpy.data.objects.remove(old, do_unlink=True)
        return _aq_anchors(GC, aroot, AQI, PT, out)
    mwb = broot.matrix_world
    # ① L3_label: 뒤-왼쪽 벽 윗면(세 켜 단면 가운데 콘크리트 위) — d4 지시선 끝 (234.86, 117.89)에 가장 가까운 점
    Xw = (BL_X[0] + BL_X[1]) / 2.0

    def sx(Y):
        return R.scr(mwb @ Vector((Xw, -Y, WH)))[0]
    Y = _solve_lin(sx, 10.0, 40.0, PT['L3_label'][0])
    Y = min(max(Y, BR_Y[1] + 0.5), BL_END - 0.4)
    out['ANCHOR_L3_label'] = anchor(GC, broot, 'ANCHOR_L3_label', mwb @ Vector((Xw, -Y, WH)))
    return _aq_anchors(GC, aroot, AQI, PT, out)


def _aq_anchors(GC, aroot, AQI, PT, out):
    """수도교 앵커(L4_label · L4_m1). 욕장이 없어도 짓는다"""
    # ② L4_label: 수도교 아치 열 기초선(앞면 아래, 교각 위) — d4 지시선 끝 (384.15, 187.97)
    mwa = aroot.matrix_world
    T = AQI['T']

    TLo = AQI.get('T_lo', T)                       # 18:40 3단: 아래 단 앞면은 가운데 단보다 0.3 앞

    def ax(u, z=0.35, tv=None):
        return R.scr(mwa @ Vector((u, -(T if tv is None else tv), z)))
    u = _solve_lin(lambda t: ax(t, 0.35, TLo)[0], 40.0, 70.0, PT['L4_label'][0])
    piers = [(-0.05 if k == 0 else AQI['lo'][k - 1][1], AQI['lo'][k][0]) for k in range(len(AQI['lo']))]
    best = min(piers, key=lambda p: 0.0 if p[0] + 0.3 <= u <= p[1] - 0.3 else min(abs(u - p[0] - 0.3), abs(u - p[1] + 0.3)))
    u = min(max(u, best[0] + 0.3), best[1] - 0.3)
    out['ANCHOR_L4_label'] = anchor(GC, aroot, 'ANCHOR_L4_label', mwa @ Vector((u, -TLo, 0.35)))
    # ③ L4_m1: 짝 표지 1 (372.0, 163.0) — 아치 면(앞면). 개구부·홍예석 띠 안이면 위로 올려 단단한 벽면에 둔다
    u1 = _solve_lin(lambda t: ax(t, 18.0)[0], 30.0, 50.0, PT['L4_m1'][0])
    z1 = _solve_lin(lambda z: ax(u1, z)[1], 10.0, 20.0, PT['L4_m1'][1])

    def solid(uu, zz):
        for (a, b) in AQI['hi']:
            cu, rr = (a + b) / 2.0, (b - a) / 2.0
            if a - 0.6 <= uu <= b + 0.6 and AQI['ZSC1'] <= zz <= AQI['S2'] + math.sqrt(max(0.0, (rr + 0.6) ** 2 - (uu - cu) ** 2)):
                return False
        return True
    zz = z1
    while not solid(u1, zz) and zz < AQI['H'] - 3.8:
        zz += 0.1
    out['ANCHOR_L4_m1'] = anchor(GC, aroot, 'ANCHOR_L4_m1', mwa @ Vector((u1, -T, zz)))
    bpy.context.view_layer.update()
    return {k: [round(v, 2) for v in R.scr(o.matrix_world.translation)] for k, o in out.items()}


def layer_audit(roots):
    """오브젝트마다 L0~L6 메시 수(빈 메시 0). bglobal roma_kit.layer_audit가 있으면 그것을 쓴다"""
    res = {}
    for r in roots:
        obj = r.name[len('BATHS_'):-len('_root')]
        cnt = {('L%d' % n): 0 for n in range(7)}
        empty = []
        for o in r.children_recursive:
            if o.type != 'MESH':
                continue
            for n in range(7):
                if ('_L%d_' % n) in o.name:
                    if len(o.data.polygons) == 0:
                        empty.append(o.name)
                    else:
                        cnt['L%d' % n] += 1
        res[obj] = {'layers': cnt, 'missing': [k for k, v in cnt.items() if v == 0], 'empty_meshes': empty}
    return res


def dump_tris(path, roots):
    """실루엣 측정용(오프라인 래스터): 루트별 화면 삼각형을 JSON으로"""
    data = {r.name: screen_tris(_kids(r)) for r in roots}
    with open(path, 'w') as f:
        json.dump(data, f)
    return {k: len(v) for k, v in data.items()}


# ═════════════════════════════════════ 짓기 ═════════════════════════════════════
def build():
    S = json.load(open(SPEC, encoding='utf-8'))
    CM = S['core_map']
    LM = {l['id']: l for l in CM['landmarks']}
    GC = R.coll(COLL, R.coll('ROMA_MAP'))
    R.clear_coll(COLL)
    M = mats()
    broot, s_b = None, None
    if BATHS:
        # 카라칼라 욕장: 지역 좌표로 지은 뒤 spec 투영 상자에 맞춘다(균일 축척 + 평면 이동, 지면 Z 유지)
        broot, bobs = build_caracalla(GC, CM, M)
        s_b, bb_fit = G.fit_to_box(broot, LM['L3']['projected_box'])
        # 대지 오른쪽 꼭짓점을 수도교 지면선 시작점에 정확히 맞춘다(평행 이동만, 축척은 fit 값 유지)
        bpy.context.view_layer.update()
        tx, ty = CM['aqueduct']['ground_line_screen'][0]
        sx, sy = R.scr(broot.matrix_world @ Vector((WX, 0.0, 0.0)))
        dX, dY = R.to_plan(tx - sx, ty - sy)
        broot.location = broot.location + Vector((dX, -dY, 0.0))
        bpy.context.view_layer.update()
        # 사람 키를 화면 P_H로(루트 축척을 되돌려 곱한다)
        sw = broot.matrix_world.to_scale()[0]
        for o in broot.children:
            if '_Person' in o.name:
                o.scale = (P_H / sw,) * 3
        bpy.context.view_layer.update()
    # 수도교: spec 지면선·높이로 바로 놓는다(오른쪽 변 밖으로 블리드)
    aroot, aobs, AQI = build_aqueduct(GC, CM, M)
    global LAST_AQI
    LAST_AQI = AQI                                                     # b7: 물 위 교각 연장·수면 반영(roma_aq_valley)이 쓴다
    bpy.context.view_layer.update()
    anc = make_anchors(GC, broot, aroot, AQI, spec_anchor_pts(S))
    bpy.context.view_layer.update()
    tb, ta = (screen_tris(_kids(broot)) if broot else []), screen_tris(_kids(aroot))
    ph = []
    for o in (list(broot.children_recursive) if broot else []) + list(aroot.children_recursive):
        if '_Person' in o.name and o.type == 'MESH':
            zs = [(o.matrix_world @ v.co).z for v in o.data.vertices]
            hh = (max(zs) - min(zs)) * (1.0 / 1.115 if o.data.name.startswith('P_person1') else 1.0)   # 머리 위 바구니는 뺀다
            ph.append(round(hh, 2))
    info = {
        'baths_scale': round(s_b, 5) if broot else None, 'baths_bbox': clip_bbox(tb) if broot else None, 'baths_box': LM['L3']['projected_box'] if broot else None,
        'aq_bbox_clip420': clip_bbox(ta), 'aq_box': LM['L4']['projected_box'],
        'right_corner': [round(v, 2) for v in R.scr(broot.matrix_world @ Vector((WX, 0.0, 0.0)))] if broot else None,
        'anchors': anc, 'person_screen_h': [min(ph), max(ph)] if ph else None,
        'audit': layer_audit([r_ for r_ in (broot, aroot) if r_]), 'objects': len(GC.all_objects),
    }
    print('BATHS build', json.dumps(info, ensure_ascii=False))
    return GC
