# 랜드마크별 최대 확대 배율(상자 수준, 보수적): 기준점(모서리·변 중점) 9개 × 배율 1.00~1.60
import json, sys, math
d5 = sys.argv[1]
D = json.load(open(d5 + '/out/drawn.json')); S = json.load(open(d5 + '/out/spec.json'))
cm = S['core_map']
def bb(poly):
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]; return [min(xs), min(ys), max(xs), max(ys)]
def inter(a, b, m=0.0):
    return not (a[2] + m <= b[0] or b[2] + m <= a[0] or a[3] + m <= b[1] or b[3] + m <= a[1])
obs = []   # (name, box)
for o in D['objects']:
    obs.append(('obj:' + str(o['id']), o['box']))
lab = {}
for l in D.get('labels', []):
    p = l.get('poly') or l.get('block_poly')
    if p:
        obs.append(('label:' + str(l.get('key') or l.get('name'))[:14], bb(p)))
for b in D.get('boxes', []):
    if b.get('box') and b.get('kind') != '패널':
        obs.append(('box:' + str(b['id']), b['box']))
    elif b.get('kind') == '패널':
        obs.append(('panel:' + str(b['id']), b['box']))
for r in D.get('roads', []):
    for p in r.get('polys', []):
        obs.append(('road:' + str(r['id']), bb(p)))
for c in D.get('crowds', []):
    xs = [f[0] for f in c['feet']]; ys = [f[1] for f in c['feet']]
    obs.append(('crowd:' + c['name'][:4], [min(xs) - 1.5, min(ys) - 5.5, max(xs) + 1.5, max(ys) + 0.5]))
for t in D.get('texts', []):
    if t.get('role') in ('floor', 'floortext', '바닥 글') or 'floor' in str(t.get('role', '')):
        if t.get('bbox'): obs.append(('floor:' + str(t.get('text', ''))[:8], t['bbox']))
LM = {o['id']: o['box'] for o in D['objects'] if str(o['id']).startswith('L')}
names = {o['id']: o['name'] for o in D['objects']}
stage = [0, 92, 420, 505]
res = {}
for lid, box in sorted(LM.items()):
    w, h = box[2] - box[0], box[3] - box[1]
    anchors = {'TL': (box[0], box[1]), 'TR': (box[2], box[1]), 'BL': (box[0], box[3]), 'BR': (box[2], box[3]),
               'T': ((box[0] + box[2]) / 2, box[1]), 'B': ((box[0] + box[2]) / 2, box[3]), 'L': (box[0], (box[1] + box[3]) / 2),
               'R': (box[2], (box[1] + box[3]) / 2), 'C': ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)}
    best = {}
    for an, (ax, ay) in anchors.items():
        smax = 1.0; hit = None
        s = 1.0
        while s <= 1.601:
            nb = [ax + (box[0] - ax) * s, ay + (box[1] - ay) * s, ax + (box[2] - ax) * s, ay + (box[3] - ay) * s]
            clip = [max(nb[0], -50), max(nb[1], 92.5), min(nb[2], 470), nb[3]]
            bad = None
            for nm, ob in obs:
                if nm == 'obj:' + lid: continue
                # 자기 라벨은 같이 옮긴다고 보고 뺀다
                if nm.startswith('label:') and (names[lid][:3] in nm or nm[6:9] in names[lid]): continue
                if nm.startswith('road:'): continue   # 길은 따로 다룬다(접속 길)
                if inter(clip, ob, 2.0): bad = nm; break
            if clip[1] < 93 and lid not in ('L3', 'L4'): bad = bad or 'stage_top'
            if bad: hit = bad; break
            smax = s; s += 0.01
        best[an] = (round(smax, 2), hit)
    top = sorted(best.items(), key=lambda kv: -kv[1][0])[:3]
    res[lid] = {'name': names[lid], 'box': box, 'area': round(w * h), 'best': top}
    print(lid, names[lid][:10], [round(v, 1) for v in box], round(w * h), top)
