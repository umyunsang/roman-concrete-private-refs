# -*- coding: utf-8 -*-
import os, sys, random, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..", "lib")))
import map_fx as F
from prim import *

W, H = 420, 200
P = Layer(0, 0, W, H, "test", bg=F.GROUND_C + (255,))
rng = random.Random(7)

# 강 중심선(±30° 꺾임) + 가장자리 오프셋
cl = [(-5, 52), (95, 109.7), (150, 78), (235, 127), (300, 127 - 0), (330, 144), (425, 144 + 30)]
cl = [(-5, 52), (95, 109.7), (150, 78), (225, 121.3), (260, 101), (330, 141.4), (425, 196)]
w = 18.0
def offs(pts, d):
    nr = F._vnormals(pts)
    return [(p[0] + n[0] * d, p[1] + n[1] * d) for p, n in zip(pts, nr)]
A = offs(cl, -w / 2); B = offs(cl, w / 2)
poly = A + B[::-1]
P_masks = [poly]

# 건물 대지(마름모 외곽 + 팔각) 두 곳
def rh(cx, cy, w_, h_):
    return [(cx, cy - h_ / 2), (cx + w_ / 2, cy), (cx, cy + h_ / 2), (cx - w_ / 2, cy)]
site1 = rh(300, 50, 70, 40.4)
site2 = [(60, 150), (80, 140), (112, 140), (132, 150), (112, 160), (80, 160)]
site2 = rh(70, 35, 60, 34.6)
hill_a_anchor = (170, 30)
hill_v_anchor = (388, 122)
for s in (site1, site2):
    P_masks.append(s)
P_masks.append([(140, 0), (215, 0), (215, 40), (140, 40)])
P_masks.append([(360, 90), (420, 90), (420, 140), (360, 140)])

# 1) 땅 무늬
n = F.draw_ground_texture(P, (0, 0, W, H), rng, mask_polys=P_masks)

# 2) 강 면 + 옆면(render.draw_river 와 같은 방식) + facet
P.poly(poly, fill=RIV_C if 'RIV_C' in globals() else (122, 180, 216))
facet_fill(P, poly, (122, 180, 216), cell=6.0, amp=0.05, key="강", jit=0.12)
for side in (A, B):
    for i in range(len(side) - 1):
        p0, p1 = side[i], side[i + 1]
        if abs(p1[0] - p0[0]) < 0.05: continue
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        if in_poly((mx, my + 0.8), poly):
            P.poly([p0, p1, (p1[0], p1[1] + 2.2), (p0[0], p0[1] + 2.2)], fill=(150, 124, 88))
for e in (A, B):
    P.line(e, (214, 200, 170), 0.45)

# 3) 강 디테일 + 나루 + 부두
nl = F.draw_river_detail(P, A, B, cl, w, rng)
def at(edge, t):
    # edge 위에서 호 길이 비율 t 의 점과 접선
    L = [0.0]
    for i in range(len(edge) - 1):
        L.append(L[-1] + math.hypot(edge[i+1][0]-edge[i][0], edge[i+1][1]-edge[i][1]))
    s_ = L[-1] * t
    for i in range(len(edge) - 1):
        if L[i] <= s_ <= L[i+1]:
            u = (s_ - L[i]) / (L[i+1] - L[i])
            return F._lerp(edge[i], edge[i+1], u), edge[i], edge[i+1]
pt, e0, e1 = at(A, 0.22)
F.draw_steps(P, (pt[0], pt[1] + 0.2), (0.0, 1.0))
pt2, f0, f1 = at(B, 0.80)
F.draw_steps(P, (pt2[0], pt2[1] - 0.2), (0.0, -1.0), width=5.5)
q0, g0, g1 = at(A, 0.52)
q1 = F._lerp(q0, g1, 0.0)
F.draw_quay(P, q0, (q0[0] + (g1[0]-g0[0]) / math.hypot(g1[0]-g0[0], g1[1]-g0[1]) * 18, q0[1] + (g1[1]-g0[1]) / math.hypot(g1[0]-g0[0], g1[1]-g0[1]) * 18), 6.0)

# 4) 대지 판석 + 구릉
F.draw_site_plate(P, site1, 1.2)
F.draw_site_plate(P, site2, 1.2)
box_a = F.draw_hills(P, "albano", hill_a_anchor, rng)
box_v = F.draw_hills(P, "vesuvio", hill_v_anchor, rng)
print("ground marks", n, "ripples", nl)
print(box_a["screen_box"], box_v["screen_box"])
print(box_a["plan"])

out = os.path.join(HERE, "out", "map_fx_test.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
im = P.img.convert("RGB")
im.resize((W * 4, H * 4), Image.LANCZOS).save(out)
im.crop((int(100*KD), int(60*KD), int(260*KD), int(150*KD))).resize((1280, 720), Image.LANCZOS).save(os.path.join(HERE, "out", "map_fx_test_zoom_river.png"))
im.crop((int(130*KD), 0, int(220*KD), int(50*KD))).resize((1260, 700), Image.LANCZOS).save(os.path.join(HERE, "out", "map_fx_test_zoom_hill.png"))
im.crop((int(340*KD), int(85*KD), int(420*KD), int(145*KD))).resize((1200, 900), Image.LANCZOS).save(os.path.join(HERE, "out", "map_fx_test_zoom_vesuvio.png"))
