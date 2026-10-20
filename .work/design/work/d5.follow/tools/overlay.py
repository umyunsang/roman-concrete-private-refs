# 진단 그림: 설계 다이어그램 위에 예약 타원·건물·랜드마크 상자·라벨·콜아웃·지시선을 겹친다
import json, sys, math
from PIL import Image, ImageDraw
d5 = sys.argv[1]; out = sys.argv[2]; crop = [float(v) for v in sys.argv[3].split(',')] if len(sys.argv) > 3 else [0, 88, 420, 510]
S = 3
im = Image.open(d5 + '/out/diagram.png').convert('RGB')
sc = im.size[0] / 420.0
im = im.resize((int(420 * S), int(594 * S)))
dr = ImageDraw.Draw(im, 'RGBA')
D = json.load(open(d5 + '/out/drawn.json'))
def P(p): return (p[0] * S, p[1] * S)
def box(b, c, w=2):
    dr.rectangle([b[0] * S, b[1] * S, b[2] * S, b[3] * S], outline=c, width=w)
# 예약 타원 R90
cx, cy = 250.0, 318.0
pts = [(cx + 110.23 * math.cos(t / 180 * math.pi), cy + 63.64 * math.sin(t / 180 * math.pi)) for t in range(0, 361, 3)]
dr.line([P(p) for p in pts], fill=(255, 0, 255, 255), width=3)
for o in D.get('objects', []):
    b = o.get('box')
    if not b: continue
    c = (255, 0, 0, 255) if str(o.get('id', '')).startswith('L') else (0, 0, 255, 255)
    box(b, c, 2)
    dr.text((b[0] * S + 3, b[1] * S + 3), str(o.get('id'))[:10], fill=c)
for l in D.get('labels', []):
    poly = l.get('poly') or l.get('block_poly')
    if poly:
        dr.polygon([P(p) for p in poly], outline=(0, 140, 0, 255))
for b in D.get('boxes', []):
    if b.get('box'): box(b['box'], (255, 140, 0, 255), 2)
for ld in D.get('leaders', []):
    pts = ld.get('pts') or ld.get('points')
    if pts and len(pts) > 1:
        dr.line([P(p) for p in pts], fill=(0, 0, 0, 255), width=2)
for x in range(0, 421, 10):
    dr.line([(x * S, 88 * S), (x * S, 92 * S)], fill=(0, 0, 0, 255))
    if x % 50 == 0: dr.text((x * S + 2, 92 * S), str(x), fill=(0, 0, 0, 255))
for y in range(90, 595, 10):
    dr.line([(0, y * S), (4 * S, y * S)], fill=(0, 0, 0, 255))
    if y % 50 == 0: dr.text((5 * S, y * S - 5), str(y), fill=(0, 0, 0, 255))
c = [int(v * S) for v in crop]
im.crop(c).save(out)
print('saved', out)
