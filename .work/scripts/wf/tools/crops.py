# -*- coding: utf-8 -*-
# 비평가용 확대 crop: 자동 실측(measure.json)의 오브젝트·패널 상자 ±4mm를 내부 해상도(1mm=8px) 원본에서 잘라 낸다.
# 사용: python crops.py --measure out/wireframe_v17_measure.json --hi out/wireframe_v17_hi.png --out out/review/v17
import os, json, argparse
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("--measure", required=True)
ap.add_argument("--hi", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--pad", type=float, default=4.0)
a = ap.parse_args()
M = json.load(open(a.measure, encoding="utf-8"))
im = Image.open(a.hi)
PXMM = im.width / 420.0
os.makedirs(a.out, exist_ok=True)
idx = []


def cut(tag, name, box):
    x0, y0, x1, y1 = box
    p = a.pad
    bx = (max(0, int((x0 - p) * PXMM)), max(0, int((y0 - p) * PXMM)), min(im.width, int((x1 + p) * PXMM)), min(im.height, int((y1 + p) * PXMM)))
    if bx[2] <= bx[0] or bx[3] <= bx[1]:
        return
    safe = name.replace(" ", "_").replace("/", "_").replace("·", "_")
    fn = "%02d_%s_%s.png" % (len(idx) + 1, tag, safe)
    im.crop(bx).save(os.path.join(a.out, fn))
    idx.append("%s\t%s\t%s\t%.1f,%.1f,%.1f,%.1f" % (fn, tag, name, x0, y0, x1, y1))


for o in M["objects"]:
    if o.get("box"):
        cut(o["tier"], o["name"], o["box"])
for pnl in M["panels"]:
    cut(pnl["tier"], pnl["name"], pnl["rect"])
cut("타이틀", "타이틀", (126.5, 10, 293.5, 92))
cut("푸터", "푸터", (18, 566, 402, 583))
# 3행×2열 구역(겹침 10mm) — 이웃 경계·라벨 충돌 확인용
for r in range(3):
    for c in range(2):
        x0, y0 = c * 205.0, r * 192.0
        cut("구역", "구역_%d%d" % (r + 1, c + 1), (x0, y0, min(420, x0 + 215.0), min(594, y0 + 210.0)))
with open(os.path.join(a.out, "index.txt"), "w", encoding="utf-8") as f:
    f.write("파일\t티어\t이름\t상자(mm: x0,y0,x1,y1)\n" + "\n".join(idx) + "\n")
print("crop %d개: %s" % (len(idx), a.out))
