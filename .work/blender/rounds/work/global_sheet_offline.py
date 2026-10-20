# global 원형 시험 그림: A 확대(원형별 색 변주) · B 히어로 광장 축척(LocalBanana와 나란히) · C 포스터 축척(3 px/mm)
import sys, time
sys.path.insert(0, '/tmp/global_mock')
import preview as PV
from PIL import Image, ImageDraw
OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/global_mock/out'
tag = sys.argv[2] if len(sys.argv) > 2 else 'r1'
t0 = time.time()
for r in PV.stats():
    print(r)
I = []
at = PV.at
# A: 확대 시트(화면 mm). 줄마다 원형, 칸마다 다른 Random 값
rnds = [0.08, 0.27, 0.42, 0.56, 0.68, 0.81, 0.93]
y = 16.0
for k in range(3):
    for j, rv in enumerate(rnds[:6]):
        X, Y, Z = at(8.0 + 10.0 * j + 60.0 * 0 + k * 0.0, y + 9.0 * k)
        I.append(('person%d' % k, X, Y, Z, 6.0, 25.0 + 47.0 * j, rv))
for j in range(4):
    X, Y, Z = at(72.0 + 12.0 * j, 26.0); I.append(('cypress%d' % j, X, Y, Z, 19.0, 30.0 * j, rnds[j * 2]))
for j in range(4):
    X, Y, Z = at(10.0 + 24.0 * j, 64.0); I.append(('olive%d' % j, X, Y, Z, 26.0, 40.0 * j, rnds[j + 1]))
for j in range(4):
    X, Y, Z = at(10.0 + 24.0 * j, 92.0); I.append(('pine%d' % j, X, Y, Z, 24.0, 50.0 * j, rnds[j + 2]))
for j in range(4):
    X, Y, Z = at(112.0 + 12.0 * j, 52.0); I.append(('bush%d' % j, X, Y, Z, 9.0, 33.0 * j, rnds[j]))
X, Y, Z = at(118.0, 74.0); I.append(('stall', X, Y, Z, 11.0, 0.0, 0.1))
X, Y, Z = at(140.0, 74.0); I.append(('stall', X, Y, Z, 11.0, 90.0, 0.55))
for j in range(4):
    X, Y, Z = at(106.0 + 5.0 * j, 90.0); I.append(('amphora', X, Y, Z, 4.0, 40.0 * j, rnds[j * 2]))
X, Y, Z = at(136.0, 94.0); I.append(('cart', X, Y, Z, 11.0, 20.0, 0.3))
for j in range(4):
    X, Y, Z = at(16.0 + 22.0 * j, 122.0); I.append(('house%d' % j, X, Y, Z, 14.0, 0.0 if j % 2 == 0 else 90.0, rnds[j + 2]))
X, Y, Z = at(108.0, 124.0); I.append(('barge', X, Y, Z, 12.0, 15.0, 0.5))
X, Y, Z = at(138.0, 120.0); I.append(('ship', X, Y, Z, 13.0, -20.0, 0.2))
img, nt = PV.render(I, (0.0, 0.0, 160.0, 134.0), 10.0, OUT + '/global_%s_A.png' % tag)
print('A tris', nt, '%.1fs' % (time.time() - t0))

# B: 히어로 광장 축척(사람 5.2 · 노점 8 · 암포라 3 · 사이프러스 16~19 · 올리브 26 · 덤불 7) — 8 px/mm, LocalBanana와 나란히
J = []
def add(key, sx, sy, s, rot, rv):
    X, Y, Z = at(sx, sy); J.append((key, X, Y, Z, s, rot, rv))
for k, (hx, hy) in enumerate(((14, 18), (34, 12), (54, 8))):
    add('house%d' % k, hx, hy, 11.0, 90.0 * (k % 2), 0.2 + 0.25 * k)
add('cypress0', 8, 44, 19.0, 0, 0.1); add('cypress1', 15, 47, 16.0, 40, 0.6)
add('olive1', 92, 30, 26.0, 20, 0.4); add('olive2', 100, 52, 25.0, 70, 0.75)
add('pine2', 78, 14, 22.0, 10, 0.3)
for k, (bx, by) in enumerate(((24, 54), (70, 58), (84, 44), (4, 60))):
    add('bush%d' % k, bx, by, 7.0, 30 * k, 0.15 + 0.2 * k)
add('stall', 40, 40, 8.0, 0.0, 0.1); add('stall', 58, 36, 8.0, 0.0, 0.62)
for k, (ax, ay) in enumerate(((47, 44), (48.5, 45.2), (46, 45.5), (66, 41), (67.4, 42.3))):
    add('amphora', ax, ay, 3.0, 40 * k, 0.1 + 0.18 * k)
ppl = [(30, 50), (33, 52), (35.5, 50.5), (52, 52), (54.5, 54), (57, 51.5), (61, 55), (44, 56), (47, 58.5), (73, 48), (26, 40), (28.5, 42)]
for k, (px_, py_) in enumerate(ppl):
    add('person%d' % (k % 3), px_, py_, 5.2, 37.0 * k, (k * 0.137 + 0.05) % 1.0)
add('cart', 84, 64, 9.0, 200, 0.4)
imgB, nt = PV.render(J, (0.0, 0.0, 110.0, 72.0), 8.0, OUT + '/global_%s_B.png' % tag)
print('B tris', nt)
imgC, nt = PV.render(J, (0.0, 0.0, 110.0, 72.0), 3.0, OUT + '/global_%s_C.png' % tag)
# 비교 그림: B · LocalBanana 앞 광장 · 203X(파리) · 포스터 축척 C(3배 확대)
LB = '/Users/um-yunsang/roman-concrete-private-refs/.work/blender/ref/lb_front.png'
PX = '/Users/um-yunsang/roman-concrete-private-refs/.work/dl/refs-cities/203x-seoul/1000_41_seoul_4.jpg'
H = imgB.height
lb = Image.open(LB).convert('RGB'); lb = lb.crop((0, 0, lb.width, lb.height)); lb = lb.resize((int(lb.width * (H // 2) / lb.height), H // 2), Image.LANCZOS)
px = Image.open(PX).convert('RGB').crop((150, 280, 700, 700)); px = px.resize((int(px.width * (H // 2) / px.height), H // 2), Image.LANCZOS)
c3 = imgC.resize((imgC.width * 3, imgC.height * 3), Image.NEAREST)
wr = max(lb.width, px.width)
out = Image.new('RGB', (imgB.width + wr + 30, H + c3.height + 70), (250, 247, 240))
out.paste(imgB, (10, 30)); out.paste(lb, (imgB.width + 20, 30)); out.paste(px, (imgB.width + 20, 30 + H // 2))
out.paste(c3, (10, H + 60))
d = ImageDraw.Draw(out)
d.text((12, 8), 'global props %s - hero plaza scale 8 px/mm' % tag, fill=(60, 40, 30))
d.text((imgB.width + 22, 8), 'LocalBanana (detail) / 203X Seoul (vector style)', fill=(60, 40, 30))
d.text((12, H + 40), 'poster scale 3 px/mm (shown x3 nearest)', fill=(60, 40, 30))
out.save(OUT + '/global_compare_%s.png' % tag)
print(OUT + '/global_compare_%s.png' % tag, '%.1fs' % (time.time() - t0))
