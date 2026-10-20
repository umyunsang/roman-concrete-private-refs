"""사각형(또는 다각형) 초기값으로 GrabCut 분할을 해서 오브젝트 윤곽·상자·면적을 잰다 (2026-10-18).

- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- 사용: uv run --no-project --with opencv-python-headless --with numpy --with pillow python -I cpg_grabcut.py <이미지> <명세.json> <출력접두사>
- 명세 JSON: {"W_mm":420, "H_mm":594, "stage":[x0,y0,x1,y1],
              "objects":[{"name":..,"kind":..,"rect":[x0,y0,x1,y1]} | {"name":..,"kind":..,"poly":[[x,y],..]}]}
  rect 는 GrabCut 초기 사각형, poly 는 분할 없이 다각형 그대로(지면 판·평면 판처럼 경계가 분명한 것).
  "keep": 남길 연결 성분 수(기본 3), "iters": 반복(기본 6)
- 출력: <접두사>_objects.json, <접두사>_overlay.jpg, <접두사>_masks.npz
"""
import json
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
PAL = [(255, 230, 0), (0, 255, 255), (255, 0, 255), (0, 255, 0), (255, 128, 0), (128, 0, 255), (0, 128, 255),
       (255, 0, 128), (128, 255, 0), (255, 255, 255), (0, 200, 120), (200, 120, 0)]


def main() -> None:
    img = cv2.imread(sys.argv[1])
    spec = json.load(open(sys.argv[2]))
    pre = sys.argv[3]
    H, W = img.shape[:2]
    mmx, mmy = spec.get("W_mm", 420) / W, spec.get("H_mm", 594) / H
    sx0, sy0, sx1, sy1 = spec["stage"]
    stage_area = (sx1 - sx0) * (sy1 - sy0)
    res, masks = [], {}
    for o in spec["objects"]:
        if "poly" in o:
            fg = np.zeros((H, W), np.uint8)
            cv2.fillPoly(fg, [np.array(o["poly"], np.int32)], 1)
        else:
            x0, y0, x1, y1 = o["rect"]
            m = np.zeros((H, W), np.uint8)
            bgd = np.zeros((1, 65), np.float64)
            fgd = np.zeros((1, 65), np.float64)
            if o.get("bg_colors") or o.get("bg_green") or o.get("bg_rects"):
                # 색 씨앗: 사각형 안은 '아마 전경', 지정 색·초록 우세 화소·지정 사각형은 '확실한 배경'
                m[:] = cv2.GC_BGD
                m[y0:y1, x0:x1] = cv2.GC_PR_FGD
                rgb = img[:, :, ::-1].astype(int)
                sel = np.zeros((H, W), bool)
                for (r_, g_, b_, tol) in o.get("bg_colors", []):
                    sel |= np.sqrt(((rgb - np.array([r_, g_, b_])) ** 2).sum(-1)) < tol
                if o.get("bg_green"):
                    gm = o.get("bg_green_margin", 12)
                    sel |= (rgb[:, :, 1] > rgb[:, :, 0] + gm) & (rgb[:, :, 1] >= rgb[:, :, 2] + 4)
                for (a0, b0, a1, b1) in o.get("bg_rects", []):
                    sel[b0:b1, a0:a1] = True
                inside = np.zeros((H, W), bool)
                inside[y0:y1, x0:x1] = True
                m[sel & inside] = cv2.GC_BGD
                cv2.grabCut(img, m, None, bgd, fgd, o.get("iters", 6), cv2.GC_INIT_WITH_MASK)
            else:
                cv2.grabCut(img, m, (x0, y0, x1 - x0, y1 - y0), bgd, fgd, o.get("iters", 6), cv2.GC_INIT_WITH_RECT)
            fg = ((m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD)).astype(np.uint8)
            fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
            n, lb, st, _ = cv2.connectedComponentsWithStats(fg)
            if n > 1:
                kk = o.get("keep", 3)
                keep = 1 + np.argsort(-st[1:, 4])[:kk]
                keep = [q for q in keep if st[q, 4] > 0.05 * st[keep[0], 4]]
                fg = np.isin(lb, keep).astype(np.uint8)
            fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((o.get("close", 5), o.get("close", 5)), np.uint8))
            if o.get("fill", True):
                cnts, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                fg = np.zeros_like(fg)
                cv2.drawContours(fg, cnts, -1, 1, thickness=-1)
        ys, xs = np.where(fg > 0)
        bx0, bx1, by0, by1 = int(xs.min()), int(xs.max()) + 1, int(ys.min()), int(ys.max()) + 1
        area = int(fg.sum())
        res.append({
            "name": o["name"], "kind": o.get("kind", ""),
            "bbox_px": [bx0, by0, bx1, by1],
            "bbox_norm": [round(bx0 / W, 4), round(by0 / H, 4), round(bx1 / W, 4), round(by1 / H, 4)],
            "w_mm": round((bx1 - bx0) * mmx, 1), "h_mm": round((by1 - by0) * mmy, 1),
            "bbox_mm2": round((bx1 - bx0) * (by1 - by0) * mmx * mmy),
            "mask_mm2": round(area * mmx * mmy),
            "mask_pct_stage": round(area / stage_area * 100, 2),
            "bbox_pct_stage": round((bx1 - bx0) * (by1 - by0) / stage_area * 100, 2),
            "centroid_norm": [round(xs.mean() / W, 4), round(ys.mean() / H, 4)],
        })
        masks[o["name"]] = fg.astype(bool)
    groups = spec.get("groups", {})
    gres = {}
    for g, names in groups.items():
        u = np.zeros((H, W), bool)
        for nme in names:
            u |= masks[nme]
        ys, xs = np.where(u)
        bx0, bx1, by0, by1 = int(xs.min()), int(xs.max()) + 1, int(ys.min()), int(ys.max()) + 1
        hull = cv2.convexHull(np.stack([xs, ys], 1).astype(np.int32))
        hull_area = cv2.contourArea(hull)
        gres[g] = {
            "members": names,
            "bbox_px": [bx0, by0, bx1, by1],
            "bbox_norm": [round(bx0 / W, 4), round(by0 / H, 4), round(bx1 / W, 4), round(by1 / H, 4)],
            "w_mm": round((bx1 - bx0) * mmx, 1), "h_mm": round((by1 - by0) * mmy, 1),
            "union_mask_pct_stage": round(u.sum() / stage_area * 100, 2),
            "bbox_pct_stage": round((bx1 - bx0) * (by1 - by0) / stage_area * 100, 2),
            "hull_pct_stage": round(hull_area / stage_area * 100, 2),
            "union_mask_mm2": round(u.sum() * mmx * mmy),
        }
    allu = np.zeros((H, W), bool)
    for v in masks.values():
        allu |= v
    allu_stage = allu[sy0:sy1, sx0:sx1].sum()
    out = {"image": sys.argv[1], "size": [W, H], "stage_px": spec["stage"],
           "stage_norm": [round(sx0 / W, 4), round(sy0 / H, 4), round(sx1 / W, 4), round(sy1 / H, 4)],
           "stage_mm": [round((sx1 - sx0) * mmx, 1), round((sy1 - sy0) * mmy, 1)],
           "objects": res, "groups": gres,
           "union_all_pct_stage": round(allu_stage / stage_area * 100, 2)}
    json.dump(out, open(pre + "_objects.json", "w"), ensure_ascii=False, indent=1)
    np.savez_compressed(pre + "_masks.npz", **{f"m{i}": masks[o["name"]] for i, o in enumerate(spec["objects"])})
    vis = img.copy()
    for i, o in enumerate(spec["objects"]):
        fg = masks[o["name"]]
        c = np.array(PAL[i % len(PAL)][::-1])
        vis[fg] = (0.5 * vis[fg] + 0.5 * c).astype(np.uint8)
        cnts, _ = cv2.findContours(fg.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(vis, cnts, -1, (0, 0, 0), 2)
    pil = Image.fromarray(cv2.cvtColor(vis, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(pil)
    f = ImageFont.truetype(FONT, max(14, W // 60))
    for i, r in enumerate(res):
        x, y = r["centroid_norm"][0] * W, r["centroid_norm"][1] * H
        d.text((x - 10, y - 10), f"{i + 1}", font=f, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
    pil.save(pre + "_overlay.jpg", quality=88)
    print(f"{'#':>2} {'이름':16s} {'폭x높이mm':>12s} {'상자mm2':>8s} {'윤곽mm2':>8s} {'윤곽/무대%':>9s} bbox_norm")
    for i, r in enumerate(res):
        print(f"{i + 1:2d} {r['name']:16s} {r['w_mm']:5.1f}x{r['h_mm']:5.1f} {r['bbox_mm2']:8d} {r['mask_mm2']:8d} "
              f"{r['mask_pct_stage']:8.2f} {r['bbox_norm']}")
    for g, v in gres.items():
        print(f"[군] {g}: {v['w_mm']}x{v['h_mm']}mm 합집합 {v['union_mask_pct_stage']}% 상자 {v['bbox_pct_stage']}% "
              f"볼록껍질 {v['hull_pct_stage']}% bbox_norm {v['bbox_norm']}")
    print("전체 합집합/무대 %:", out["union_all_pct_stage"], "무대 mm:", out["stage_mm"])


if __name__ == "__main__":
    main()
