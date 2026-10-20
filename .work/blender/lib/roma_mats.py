
# roma_mats — 절차적 재질(LocalBanana 미니어처 디오라마 색감)
import bpy

def _inp(node, *names):
    for nm in names:
        for s in node.inputs:
            if s.identifier == nm or s.name == nm:
                return s
    raise KeyError((node.bl_idname, names))

def _out(node, *names):
    for nm in names:
        for s in node.outputs:
            if s.identifier == nm or s.name == nm:
                return s
    raise KeyError((node.bl_idname, names))

class NB:
    def __init__(self, name, reset=True):
        m = bpy.data.materials.get(name)
        if m is None:
            m = bpy.data.materials.new(name)
        try:
            m.use_nodes = True
        except Exception:
            pass
        self.m = m
        self.nt = m.node_tree
        if reset:
            for n in list(self.nt.nodes):
                self.nt.nodes.remove(n)
        self.out = self.n('ShaderNodeOutputMaterial', (600, 0))
        self.bsdf = self.n('ShaderNodeBsdfPrincipled', (300, 0))
        self.link(_out(self.bsdf, 'BSDF'), _inp(self.out, 'Surface'))
    def n(self, t, loc=(0, 0)):
        nd = self.nt.nodes.new(t)
        nd.location = loc
        return nd
    def link(self, a, b):
        self.nt.links.new(a, b)
    def coord(self, kind='Object'):
        tc = self.n('ShaderNodeTexCoord', (-1400, 0))
        return _out(tc, kind)
    def mix(self, fac, a, b, blend='MIX'):
        nd = self.n('ShaderNodeMix')
        nd.data_type = 'RGBA'
        nd.blend_type = blend
        if isinstance(fac, (int, float)):
            _inp(nd, 'Factor_Float').default_value = fac
        else:
            self.link(fac, _inp(nd, 'Factor_Float'))
        for sock, v in ((_inp(nd, 'A_Color'), a), (_inp(nd, 'B_Color'), b)):
            if isinstance(v, (tuple, list)):
                sock.default_value = (v[0], v[1], v[2], 1.0)
            else:
                self.link(v, sock)
        return _out(nd, 'Result_Color')
    def noise(self, vec, scale, detail=4.0, rough=0.55, dist=0.0):
        nd = self.n('ShaderNodeTexNoise')
        if vec is not None:
            self.link(vec, _inp(nd, 'Vector'))
        _inp(nd, 'Scale').default_value = scale
        _inp(nd, 'Detail').default_value = detail
        _inp(nd, 'Roughness').default_value = rough
        _inp(nd, 'Distortion').default_value = dist
        return nd
    def ramp(self, fac, stops, interp='LINEAR'):
        nd = self.n('ShaderNodeValToRGB')
        cr = nd.color_ramp
        cr.interpolation = interp
        while len(cr.elements) > 1:
            cr.elements.remove(cr.elements[-1])
        cr.elements[0].position = stops[0][0]
        cr.elements[0].color = (*stops[0][1], 1.0)
        for pos, col in stops[1:]:
            e = cr.elements.new(pos)
            e.color = (*col, 1.0)
        self.link(fac, _inp(nd, 'Fac'))
        return _out(nd, 'Color')
    def math(self, op, a, b=None, clamp=False):
        nd = self.n('ShaderNodeMath')
        nd.operation = op
        nd.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                nd.inputs[i].default_value = v
            else:
                self.link(v, nd.inputs[i])
        return nd.outputs[0]
    def ao_dark(self, col, dark, dist=1.5, amount=0.65):
        ao = self.n('ShaderNodeAmbientOcclusion')
        _inp(ao, 'Distance').default_value = dist
        f = self.math('MULTIPLY', self.math('SUBTRACT', 1.0, _out(ao, 'AO')), amount, clamp=True)
        return self.mix(f, col, dark)
    def bump(self, height, strength=0.3, distance=0.1, invert=False, bevel=0.0):
        bp = self.n('ShaderNodeBump')
        bp.invert = invert
        _inp(bp, 'Strength').default_value = strength
        _inp(bp, 'Distance').default_value = distance
        self.link(height, _inp(bp, 'Height'))
        if bevel > 0:
            bv = self.n('ShaderNodeBevel')
            bv.samples = 6
            _inp(bv, 'Radius').default_value = bevel
            self.link(_out(bv, 'Normal'), _inp(bp, 'Normal'))
        self.link(_out(bp, 'Normal'), _inp(self.bsdf, 'Normal'))
    def finish(self, col, rough=0.85, spec=0.25):
        if isinstance(col, (tuple, list)):
            _inp(self.bsdf, 'Base Color').default_value = (*col[:3], 1.0)
        else:
            self.link(col, _inp(self.bsdf, 'Base Color'))
        _inp(self.bsdf, 'Roughness').default_value = rough
        try:
            _inp(self.bsdf, 'Specular IOR Level').default_value = spec
        except KeyError:
            pass
        return self.m

def masonry(name, c1, c2, mortar, bw, rh, msize=0.035, var=0.12, dark=None, uv=True, bevel=0.06, bump=0.35):
    """UV(mm) 위 돌 블록 쌓기. 블록마다 색, 큰 얼룩, 아래쪽 풍화, 오목한 곳 어둡게"""
    b = NB(name)
    vec = b.coord('UV' if uv else 'Object')
    obj = b.coord('Object')
    br = b.n('ShaderNodeTexBrick')
    b.link(vec, _inp(br, 'Vector'))
    for k, v in (('Color1', c1), ('Color2', c2), ('Mortar', mortar)):
        _inp(br, k).default_value = (*v, 1.0)
    _inp(br, 'Scale').default_value = 1.0
    _inp(br, 'Mortar Size').default_value = msize
    _inp(br, 'Mortar Smooth').default_value = 0.35
    _inp(br, 'Bias').default_value = 0.0
    _inp(br, 'Brick Width').default_value = bw
    _inp(br, 'Row Height').default_value = rh
    br.offset = 0.5
    col = _out(br, 'Color')
    big = b.noise(obj, 0.035, 3.0, 0.5)
    col = b.mix(b.math('MULTIPLY', _out(big, 'Fac'), var * 2.2, clamp=True), col,
                tuple(min(1.0, c * 1.08 + 0.02) for c in c1), 'OVERLAY')
    stain = b.noise(obj, 0.12, 6.0, 0.62)
    col = b.mix(b.math('MULTIPLY', b.math('SUBTRACT', _out(stain, 'Fac'), 0.42, clamp=True), 1.2, clamp=True), col,
                tuple(c * 0.78 for c in c2), 'MIX')
    dk = dark or tuple(c * 0.55 for c in c2)
    col = b.ao_dark(col, dk, 1.2, 0.7)
    pores = b.noise(obj, 6.0, 5.0, 0.6)
    h = b.math('ADD', b.math('MULTIPLY', _out(br, 'Fac'), -1.0), b.math('MULTIPLY', _out(pores, 'Fac'), 0.18))
    b.bump(h, bump, 0.12, False, bevel)
    return b.finish(col, 0.88, 0.2)

def build_all():
    M = {}
    M['TRAV'] = masonry('M_Travertine', (0.80, 0.68, 0.52), (0.72, 0.60, 0.45), (0.58, 0.50, 0.40), 1.7, 0.85)
    M['TRAV_IN'] = masonry('M_TravertineShade', (0.74, 0.61, 0.46), (0.66, 0.53, 0.40), (0.52, 0.44, 0.35), 1.7, 0.85)
    M['BRICK'] = masonry('M_Brick', (0.64, 0.38, 0.25), (0.55, 0.32, 0.21), (0.72, 0.64, 0.53), 0.75, 0.24, 0.045, 0.1, None, True, 0.04, 0.25)
    M['TUFF'] = masonry('M_Tuff', (0.63, 0.57, 0.47), (0.55, 0.49, 0.40), (0.48, 0.43, 0.36), 1.3, 0.65)
    # 콘크리트 단면(오푸스 카이멘티키움): 회색 바탕 + 응회암·용암·벽돌 골재 덩어리
    b = NB('M_ConcreteSection'); obj = b.coord('Object')
    vo = b.n('ShaderNodeTexVoronoi'); b.link(obj, _inp(vo, 'Vector')); _inp(vo, 'Scale').default_value = 1.6
    _inp(vo, 'Randomness').default_value = 1.0
    agg = b.ramp(_out(vo, 'Color'), [(0.0, (0.55, 0.30, 0.20)), (0.3, (0.34, 0.32, 0.30)), (0.55, (0.70, 0.62, 0.48)), (0.8, (0.45, 0.40, 0.36))], 'CONSTANT')
    vo2 = b.n('ShaderNodeTexVoronoi'); vo2.feature = 'DISTANCE_TO_EDGE'; b.link(obj, _inp(vo2, 'Vector')); _inp(vo2, 'Scale').default_value = 1.6
    mask = b.math('GREATER_THAN', _out(vo2, 'Distance'), 0.12)
    col = b.mix(mask, (0.66, 0.64, 0.60), agg)
    gr = b.noise(obj, 9.0, 4.0, 0.7)
    col = b.mix(b.math('MULTIPLY', _out(gr, 'Fac'), 0.35), col, (0.50, 0.49, 0.46))
    b.bump(b.math('ADD', mask, b.math('MULTIPLY', _out(gr, 'Fac'), 0.3)), 0.4, 0.08)
    M['CONC'] = b.finish(col, 0.92, 0.15)
    # 광장 포석: 보로노이 돌 + 줄눈 + 줄눈 풀
    b = NB('M_Cobble'); obj = b.coord('Object')
    vo = b.n('ShaderNodeTexVoronoi'); b.link(obj, _inp(vo, 'Vector')); _inp(vo, 'Scale').default_value = 0.62
    stone = b.ramp(_out(vo, 'Color'), [(0.0, (0.66, 0.63, 0.58)), (0.35, (0.58, 0.55, 0.51)), (0.6, (0.72, 0.68, 0.61)), (0.85, (0.52, 0.50, 0.47))], 'LINEAR')
    ed = b.n('ShaderNodeTexVoronoi'); ed.feature = 'DISTANCE_TO_EDGE'; b.link(obj, _inp(ed, 'Vector')); _inp(ed, 'Scale').default_value = 0.62
    joint = b.math('LESS_THAN', _out(ed, 'Distance'), 0.06)
    gn = b.noise(obj, 0.25, 3.0, 0.5)
    grass_j = b.math('MULTIPLY', joint, b.math('GREATER_THAN', _out(gn, 'Fac'), 0.52))
    col = b.mix(joint, stone, (0.40, 0.37, 0.33))
    col = b.mix(grass_j, col, (0.36, 0.40, 0.20))
    col = b.ao_dark(col, (0.30, 0.28, 0.25), 1.0, 0.5)
    rnd = b.noise(obj, 4.0, 3.0, 0.6)
    b.bump(b.math('ADD', b.math('MULTIPLY', _out(ed, 'Distance'), 3.0), b.math('MULTIPLY', _out(rnd, 'Fac'), 0.15)), 0.45, 0.1)
    M['COBBLE'] = b.finish(col, 0.9, 0.2)
    # 풀밭
    b = NB('M_Grass'); obj = b.coord('Object')
    g1 = b.noise(obj, 0.18, 4.0, 0.6); g2 = b.noise(obj, 3.5, 4.0, 0.7)
    col = b.ramp(_out(g1, 'Fac'), [(0.3, (0.27, 0.34, 0.13)), (0.5, (0.38, 0.44, 0.20)), (0.7, (0.47, 0.48, 0.26))])
    col = b.mix(b.math('MULTIPLY', _out(g2, 'Fac'), 0.5), col, (0.22, 0.28, 0.10))
    b.bump(_out(g2, 'Fac'), 0.5, 0.15)
    M['GRASS'] = b.finish(col, 0.95, 0.1)
    # 지층(받침 옆면): 물체 Z로 층
    b = NB('M_Strata'); obj = b.coord('Object')
    sep = b.n('ShaderNodeSeparateXYZ'); b.link(obj, _inp(sep, 'Vector'))
    wob = b.noise(obj, 0.25, 3.0, 0.5)
    z = b.math('ADD', _out(sep, 'Z'), b.math('MULTIPLY', b.math('SUBTRACT', _out(wob, 'Fac'), 0.5), 0.9))
    zf = b.math('DIVIDE', b.math('ADD', z, 7.5), 7.5, clamp=True)
    col = b.ramp(zf, [(0.0, (0.47, 0.40, 0.32)), (0.27, (0.66, 0.55, 0.38)), (0.56, (0.56, 0.33, 0.22)), (0.84, (0.36, 0.25, 0.16))], 'CONSTANT')
    st = b.n('ShaderNodeTexVoronoi'); b.link(obj, _inp(st, 'Vector')); _inp(st, 'Scale').default_value = 2.2
    pebble = b.math('LESS_THAN', _out(st, 'Distance'), 0.16)
    col = b.mix(b.math('MULTIPLY', pebble, 0.35), col, (0.80, 0.74, 0.62))
    gr = b.noise(obj, 7.0, 4.0, 0.7)
    col = b.mix(b.math('MULTIPLY', _out(gr, 'Fac'), 0.3), col, (0.25, 0.18, 0.12))
    b.bump(b.math('ADD', _out(gr, 'Fac'), b.math('MULTIPLY', pebble, 0.6)), 0.5, 0.1)
    M['STRATA'] = b.finish(col, 0.95, 0.1)
    # 나무 판재 바닥
    b = NB('M_WoodDeck'); vec = b.coord('Object')
    br = b.n('ShaderNodeTexBrick'); b.link(vec, _inp(br, 'Vector'))
    for k, v in (('Color1', (0.58, 0.40, 0.23)), ('Color2', (0.48, 0.32, 0.18)), ('Mortar', (0.22, 0.14, 0.08))):
        _inp(br, k).default_value = (*v, 1.0)
    _inp(br, 'Scale').default_value = 1.0; _inp(br, 'Brick Width').default_value = 4.0; _inp(br, 'Row Height').default_value = 0.42
    _inp(br, 'Mortar Size').default_value = 0.025; br.offset = 0.37
    grain = b.noise(vec, 3.0, 6.0, 0.6, 2.0)
    col = b.mix(b.math('MULTIPLY', _out(grain, 'Fac'), 0.35), _out(br, 'Color'), (0.36, 0.24, 0.13))
    col = b.ao_dark(col, (0.25, 0.16, 0.09), 1.0, 0.5)
    b.bump(b.math('MULTIPLY', _out(br, 'Fac'), -1.0), 0.3, 0.06)
    M['WOOD'] = b.finish(col, 0.75, 0.3)
    # 단색 계열
    def flat(key, name, col, rough=0.8, metal=0.0, nscale=2.0, nvar=0.12):
        b = NB(name); obj = b.coord('Object')
        nz = b.noise(obj, nscale, 4.0, 0.6)
        c = b.mix(b.math('MULTIPLY', _out(nz, 'Fac'), nvar * 2), col, tuple(x * 0.7 for x in col))
        if metal:
            _inp(b.bsdf, 'Metallic').default_value = metal
        b.bump(_out(nz, 'Fac'), 0.15, 0.05)
        M[key] = b.finish(c, rough, 0.3)
    flat('CYPRESS', 'M_Cypress', (0.15, 0.24, 0.10), 0.9, 0, 3.0, 0.2)
    flat('OLIVE', 'M_OliveLeaf', (0.38, 0.43, 0.27), 0.9, 0, 3.0, 0.2)
    flat('SHRUB', 'M_Shrub', (0.27, 0.36, 0.15), 0.9, 0, 3.0, 0.2)
    flat('BARK', 'M_Bark', (0.30, 0.23, 0.16), 0.95, 0, 6.0, 0.25)
    flat('TERRA', 'M_Terracotta', (0.66, 0.36, 0.22), 0.7, 0, 3.0, 0.12)
    flat('C_RED', 'M_ClothRed', (0.68, 0.17, 0.12), 0.85)
    flat('C_WHITE', 'M_ClothWhite', (0.88, 0.85, 0.78), 0.85)
    flat('C_BLUE', 'M_ClothBlue', (0.20, 0.32, 0.55), 0.85)
    flat('C_OCHRE', 'M_ClothOchre', (0.76, 0.56, 0.22), 0.85)
    flat('C_GREEN', 'M_ClothGreen', (0.30, 0.42, 0.25), 0.85)
    flat('SKIN', 'M_Skin', (0.74, 0.52, 0.38), 0.6, 0, 2.0, 0.05)
    flat('HAIR', 'M_Hair', (0.14, 0.10, 0.07), 0.7)
    flat('BRONZE', 'M_Bronze', (0.42, 0.30, 0.16), 0.38, 0.9, 1.5, 0.25)
    flat('LIME', 'M_Lime', (0.93, 0.92, 0.88), 0.95, 0, 4.0, 0.06)
    flat('POZZ', 'M_Pozzolana', (0.56, 0.30, 0.20), 0.95, 0, 5.0, 0.18)
    flat('AGGR', 'M_Aggregate', (0.50, 0.49, 0.46), 0.95, 0, 6.0, 0.3)
    flat('TIMBER', 'M_Timber', (0.52, 0.36, 0.21), 0.8, 0, 3.0, 0.2)
    flat('GROUND', 'M_Ground', (0.72, 0.62, 0.45), 0.95, 0, 0.3, 0.15)
    flat('DARK', 'M_Shadow', (0.18, 0.14, 0.11), 0.95)
    return M
