# global 소품 원형 미리보기(공용 Blender가 응답하지 않을 때만 쓰는 임시 도구).
# 가짜 bpy/bmesh로 roma_props 원형 기하를 그대로 짓고, 등각 투영 + ISO_TONE 평면 톤(윗면 1.0 · 왼면 0.86 · 오른면 0.68)으로 z-버퍼 래스터화한다.
import sys, math, os
sys.path.insert(0, '/tmp/global_mock/mock')
sys.path.insert(1, '/Users/um-yunsang/roman-concrete-private-refs/.work/blender/lib')
import bpy, bmesh
import roma_kit as R, roma_flat as FL, roma_geo as G
import roma_props as RP
import numpy as np
from PIL import Image, ImageDraw

COL = {}
_flat = FL.flat
def _rec_flat(n, h):
    COL[n] = ('flat', h); return _flat(n, h)
FL.flat = _rec_flat
_var = RP.var_mat
def _rec_var(n, stops):
    COL[n] = ('var', stops); return _var(n, stops)
RP.var_mat = _rec_var
P = RP.build_protos()

def lin(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c]
def to_srgb(c):
    return [int(round(255 * (1.055 * max(0, x) ** (1 / 2.4) - 0.055 if x > 0.0031308 else 12.92 * x))) for x in c]
def ramp(stops, f):
    col = stops[0][1]
    for p, h in stops:
        if f >= p:
            col = h
    return col
TOC = R.Vector((1, -1, 1)).normalized()
def tone(n):
    if n.dot(TOC) < 0:
        n = -n
    ph = math.atan2(n.y, n.x)
    t = min(1, max(0, (ph - math.radians(-135)) / math.radians(180)))
    side = 0.95 + (0.59 - 0.95) * t
    return side + (1.0 - side) * max(0.0, n.z)

def stats():
    rows = []
    for k, ob in sorted(P.items()):
        me = ob.data
        used = sorted({mi for _, mi in me._faces})
        xs = [v.x for vs, _ in me._faces for v in vs]; ys = [v.y for vs, _ in me._faces for v in vs]; zs = [v.z for vs, _ in me._faces for v in vs]
        bad = 0
        for vs, _ in me._faces:
            n = R.Vector((0, 0, 0))
            for i in range(1, len(vs) - 1):
                n = n + (vs[i] - vs[0]).cross(vs[i + 1] - vs[0])
            if n.length < 1e-10:
                bad += 1
        unused = [i for i in range(len(me.materials)) if i not in used]
        rows.append('%-10s faces %5d  mats %2d unused %s  bbox x[%.3f,%.3f] y[%.3f,%.3f] z[%.3f,%.3f]  degenerate %d' % (
            k, me._nf, len(me.materials), unused, min(xs), max(xs), min(ys), max(ys), min(zs), max(zs), bad))
    return rows

def render(insts, box, ppm, out, bg='#E2D1B2', ss=3):
    W, H = int(round((box[2] - box[0]) * ppm)), int(round((box[3] - box[1]) * ppm))
    Ws, Hs = W * ss, H * ss
    col = np.zeros((Hs, Ws, 3), np.float32); col[:] = np.array(to_srgb(lin(bg)), np.float32)
    zb = np.full((Hs, Ws), -1e9, np.float32)
    def px(p):
        return ((p[0] - box[0]) * ppm * ss, (p[1] - box[1]) * ppm * ss)
    ntri = 0
    for (key, X, Y, Z, s, rot, rnd) in insts:
        ob = P[key]; me = ob.data
        c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        off = R.P(X, Y, Z)
        cache = {}
        for vs, mi in me._faces:
            w = [R.Vector((off.x + s * (v.x * c - v.y * sn), off.y + s * (v.x * sn + v.y * c), off.z + s * v.z)) for v in vs]
            n = R.Vector((0, 0, 0))
            for i in range(1, len(w) - 1):
                n = n + (w[i] - w[0]).cross(w[i + 1] - w[0])
            if n.length < 1e-12:
                continue
            n = n.normalized()
            m = me.materials[mi] if mi < len(me.materials) else me.materials[0]
            kind, val = COL.get(m.name, ('flat', '#FF00FF'))
            hx = val if kind == 'flat' else ramp(val, rnd)
            cc = np.array(to_srgb([x * tone(n) for x in lin(hx)]), np.float32)
            sp = [px(R.scr(v)) for v in w]; dp = [v.dot(TOC) for v in w]
            for k in range(1, len(w) - 1):
                p0, p1, p2 = sp[0], sp[k], sp[k + 1]
                xs = (p0[0], p1[0], p2[0]); ys = (p0[1], p1[1], p2[1])
                x0, x1 = max(0, int(math.floor(min(xs)))), min(Ws - 1, int(math.ceil(max(xs))))
                y0, y1 = max(0, int(math.floor(min(ys)))), min(Hs - 1, int(math.ceil(max(ys))))
                if x0 > x1 or y0 > y1:
                    continue
                den = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
                if abs(den) < 1e-12:
                    continue
                gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
                a = ((p1[1] - p2[1]) * (gx - p2[0]) + (p2[0] - p1[0]) * (gy - p2[1])) / den
                b = ((p2[1] - p0[1]) * (gx - p2[0]) + (p0[0] - p2[0]) * (gy - p2[1])) / den
                g = 1 - a - b
                msk = (a >= -1e-6) & (b >= -1e-6) & (g >= -1e-6)
                if not msk.any():
                    continue
                d = a * dp[0] + b * dp[k] + g * dp[k + 1]
                sub = zb[y0:y1 + 1, x0:x1 + 1]
                upd = msk & (d > sub)
                sub[upd] = d[upd]
                col[y0:y1 + 1, x0:x1 + 1][upd] = cc
                ntri += 1
    img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)
    img.save(out)
    return img, ntri

def at(sx, sy, Z=0.0):
    X, Y = R.to_plan(sx, sy)
    return X, Y, Z
