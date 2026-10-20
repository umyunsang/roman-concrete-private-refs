"""구획 명세(JSON)를 읽어 정규 좌표·mm·면적 비율을 계산하고, 상자와 이름을 그려 넣은 확인용 이미지를 만든다 (2026-10-18).

- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- 사용: uv run --no-project --with pillow --with numpy --with opencv-python-headless python -I cpg_markup.py <명세.json> <출력.png> <결과.json>
- 명세 형식
  {"image": 경로, "W_mm": 420|null, "H_mm": 594|null, "scale": 1.6, "title": "...",
   "stage": [x0,y0,x1,y1],
   "zones": [{"name":..,"kind":..,"box":[x0,y0,x1,y1],"note":..,"poly":[[x,y],..](선택),"draw":true}],
   "groups": {"그룹명": {"members": [zone 이름..], "polys": [[[x,y],..],..](선택)}}}
- 좌표는 이미지 픽셀. 면적 비율은 stage(지도 무대) 상자 대비 %.
"""
import json
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
COL = {
    "title": (255, 200, 0), "panel": (0, 190, 255), "map": (0, 220, 0), "core_group": (255, 0, 60),
    "hero": (255, 60, 200), "landmark": (255, 140, 0), "river": (0, 90, 255), "sea": (0, 60, 200),
    "road": (150, 150, 150), "legend": (160, 80, 255), "footer": (120, 120, 120), "other": (0, 160, 140),
    "label": (90, 40, 0), "terrain": (40, 120, 40),
}


def poly_area(p):
    p = np.asarray(p, float)
    x, y = p[:, 0], p[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def main() -> None:
    spec = json.load(open(sys.argv[1]))
    out_png, out_json = sys.argv[2], sys.argv[3]
    im = Image.open(spec["image"]).convert("RGB")
    W, H = im.size
    wmm, hmm = spec.get("W_mm"), spec.get("H_mm")
    sx0, sy0, sx1, sy1 = spec["stage"]
    sA = (sx1 - sx0) * (sy1 - sy0)
    zres = []
    zmap = {}
    for i, z in enumerate(spec["zones"]):
        x0, y0, x1, y1 = z["box"]
        r = {"idx": i + 1, "name": z["name"], "kind": z["kind"], "note": z.get("note", ""),
             "box_px": [x0, y0, x1, y1],
             "bbox_norm": [round(x0 / W, 4), round(y0 / H, 4), round(x1 / W, 4), round(y1 / H, 4)],
             "bbox_pct_stage": round((x1 - x0) * (y1 - y0) / sA * 100, 2),
             "bbox_pct_image": round((x1 - x0) * (y1 - y0) / (W * H) * 100, 2)}
        if wmm:
            r["w_mm"] = round((x1 - x0) * wmm / W, 1)
            r["h_mm"] = round((y1 - y0) * hmm / H, 1)
        if "poly" in z:
            a = poly_area(z["poly"])
            r["poly_pct_stage"] = round(a / sA * 100, 2)
            r["poly_pct_image"] = round(a / (W * H) * 100, 2)
            if wmm:
                r["poly_mm2"] = round(a * wmm / W * hmm / H)
        zres.append(r)
        zmap[z["name"]] = z
    gres = {}
    for g, gd in spec.get("groups", {}).items():
        mask = np.zeros((H, W), np.uint8)
        xs0, ys0, xs1, ys1 = [], [], [], []
        for nm in gd["members"]:
            z = zmap[nm]
            if "poly" in z:
                cv2.fillPoly(mask, [np.array(z["poly"], np.int32)], 1)
            else:
                a0, b0, a1, b1 = z["box"]
                mask[b0:b1, a0:a1] = 1
            a0, b0, a1, b1 = z["box"]
            xs0.append(a0); ys0.append(b0); xs1.append(a1); ys1.append(b1)
        for p in gd.get("polys", []):
            cv2.fillPoly(mask, [np.array(p, np.int32)], 1)
            p = np.array(p)
            xs0.append(p[:, 0].min()); ys0.append(p[:, 1].min()); xs1.append(p[:, 0].max()); ys1.append(p[:, 1].max())
        bx = [int(min(xs0)), int(min(ys0)), int(max(xs1)), int(max(ys1))]
        ys, xs = np.where(mask > 0)
        hull = cv2.convexHull(np.stack([xs, ys], 1).astype(np.int32))
        st = mask[sy0:sy1, sx0:sx1].sum()
        rr = {"members": gd["members"], "box_px": bx,
              "bbox_norm": [round(bx[0] / W, 4), round(bx[1] / H, 4), round(bx[2] / W, 4), round(bx[3] / H, 4)],
              "bbox_pct_stage": round((bx[2] - bx[0]) * (bx[3] - bx[1]) / sA * 100, 2),
              "union_pct_stage": round(st / sA * 100, 2),
              "hull_pct_stage": round(cv2.contourArea(hull) / sA * 100, 2),
              "centroid_norm": [round(xs.mean() / W, 4), round(ys.mean() / H, 4)]}
        if wmm:
            rr["w_mm"] = round((bx[2] - bx[0]) * wmm / W, 1)
            rr["h_mm"] = round((bx[3] - bx[1]) * hmm / H, 1)
        gres[g] = rr
    res = {"image": spec["image"], "size_px": [W, H], "stage_px": spec["stage"],
           "stage_norm": [round(sx0 / W, 4), round(sy0 / H, 4), round(sx1 / W, 4), round(sy1 / H, 4)],
           "stage_pct_image": round(sA / (W * H) * 100, 2), "zones": zres, "groups": gres}
    if wmm:
        res["stage_mm"] = [round((sx1 - sx0) * wmm / W, 1), round((sy1 - sy0) * hmm / H, 1)]
    json.dump(res, open(out_json, "w"), ensure_ascii=False, indent=1)

    # ---- 그림 ----
    sc = spec.get("scale", 1.6)
    big = im.resize((int(W * sc), int(H * sc)), Image.LANCZOS)
    ov = Image.new("RGBA", big.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    fs = max(15, int(min(W, H) * sc / 75))
    f = ImageFont.truetype(FONT, fs)
    fb = ImageFont.truetype(FONT, int(fs * 1.25))
    # 무대
    d.rectangle([sx0 * sc, sy0 * sc, sx1 * sc - 1, sy1 * sc - 1], outline=(0, 220, 0, 255), width=5)
    for g, rr in gres.items():
        b = rr["box_px"]
        d.rectangle([b[0] * sc, b[1] * sc, b[2] * sc, b[3] * sc], outline=(255, 0, 60, 255), width=7)
    for z, r in zip(spec["zones"], zres):
        if not z.get("draw", True):
            continue
        c = COL.get(z["kind"], (255, 255, 255))
        x0, y0, x1, y1 = [v * sc for v in z["box"]]
        if "poly" in z:
            d.polygon([(px * sc, py * sc) for px, py in z["poly"]], fill=c + (60,), outline=c + (255,))
        d.rectangle([x0, y0, x1, y1], outline=c + (255,), width=spec.get("lw", 3), fill=c + (18,))
        tag = f"{r['idx']}"
        if spec.get("draw_names", True):
            nm = z.get("short", z["name"])
            tag = f"{r['idx']} {nm}"
        tw = d.textlength(tag, font=fb)
        d.rectangle([x0 + 2, y0 + 2, x0 + tw + 10, y0 + fs * 1.5], fill=(0, 0, 0, 170))
        d.text((x0 + 6, y0 + 2), tag, font=fb, fill=c + (255,))
    big = Image.alpha_composite(big.convert("RGBA"), ov).convert("RGB")
    # 범례 패널
    lines = [spec.get("title", ""), f"초록 굵은 테두리 = 지도 무대 {res['stage_norm']}  ·  빨강 굵은 테두리 = 코어 군 상자", ""]
    for r in zres:
        sz = f"{r['w_mm']}×{r['h_mm']}mm" if "w_mm" in r else f"{r['box_px'][2]-r['box_px'][0]}×{r['box_px'][3]-r['box_px'][1]}px"
        extra = f", 실루엣 {r['poly_pct_stage']}%" if "poly_pct_stage" in r else ""
        lines.append(f"{r['idx']:>2}. [{r['kind']}] {r['name']}  {r['bbox_norm']}  {sz}  상자/무대 {r['bbox_pct_stage']}%{extra}")
    for g, rr in gres.items():
        sz = f"{rr['w_mm']}×{rr['h_mm']}mm" if "w_mm" in rr else ""
        lines.append(f"[군] {g}: {rr['bbox_norm']} {sz} 상자/무대 {rr['bbox_pct_stage']}% · 합집합 {rr['union_pct_stage']}% · 볼록껍질 {rr['hull_pct_stage']}%")
    lf = ImageFont.truetype(FONT, max(16, fs))
    lh = int(max(16, fs) * 1.45)
    panel_w = 1750
    panel_h = max(big.height, lh * (len(lines) + 2))
    canvas = Image.new("RGB", (big.width + panel_w, panel_h), (250, 250, 248))
    canvas.paste(big, (0, 0))
    dd = ImageDraw.Draw(canvas)
    y = 16
    for i, t in enumerate(lines):
        dd.text((big.width + 20, y), t, font=lf if i else ImageFont.truetype(FONT, int(fs * 1.3)), fill=(20, 20, 20))
        y += lh
    canvas.save(out_png)
    print("saved", out_png, canvas.size, "/", out_json)
    for r in zres:
        print(r["idx"], r["kind"], r["name"], r["bbox_norm"], r.get("w_mm"), r.get("h_mm"), r["bbox_pct_stage"], r.get("poly_pct_stage"))
    for g, rr in gres.items():
        print("[군]", g, rr)


if __name__ == "__main__":
    main()
