"""오브젝트 크기 등급(상자 mm, A2 환산) + 패널·타이틀 요약."""
import json, statistics as stt
from pathlib import Path
OUT = Path("/Users/um-yunsang/roman-concrete-private-refs/.work/out/refs-analysis")
Z = json.load(open(OUT / "203x-seoul-london-berlin_zones.json"))
MMX, MMY = 420, 594
PROPS = ("버스", "택시", "지하철", "전화박스", "신사", "블랙캡", "언더그라운드", "근위병", "S반", "U반")
res = {}
for ref, zones in Z.items():
    rows = []
    for z in zones:
        if z["kind"] in ("hero", "landmark"):
            x0, y0, x1, y1 = z["bbox_norm"]
            w, h = (x1 - x0) * MMX, (y1 - y0) * MMY
            rows.append((z["name"], z["kind"], round(w, 1), round(h, 1), round(w * h)))
    std = [r for r in rows if r[1] == "landmark" and not any(p in r[0] for p in PROPS) and "받침 판" not in r[0]]
    props = [r for r in rows if any(p in r[0] for p in PROPS)]
    hero = [r for r in rows if r[1] == "hero"][0]
    big = max(rows, key=lambda r: r[4])
    panels = [z for z in zones if z["kind"] == "panel"]
    parea = sum((z["bbox_norm"][2] - z["bbox_norm"][0]) * (z["bbox_norm"][3] - z["bbox_norm"][1]) for z in panels) * 100
    t = [z for z in zones if z["kind"] == "title"][0]["bbox_norm"]
    res[ref] = {"hero": hero, "largest_box": big,
                "std_n": len(std), "std_w_median": round(stt.median(r[2] for r in std), 1), "std_h_median": round(stt.median(r[3] for r in std), 1),
                "std_area_median": round(stt.median(r[4] for r in std)), "std_w_range": [min(r[2] for r in std), max(r[2] for r in std)],
                "std_h_range": [min(r[3] for r in std), max(r[3] for r in std)],
                "hero_over_std_area": round(hero[4] / stt.median(r[4] for r in std), 2),
                "props": [(r[0], r[2], r[3]) for r in props],
                "panel_count": len(panels), "panel_area_pct": round(parea, 1),
                "title_w_pct": round((t[2] - t[0]) * 100, 1), "title_mm": [round((t[2] - t[0]) * MMX), round((t[3] - t[1]) * MMY)],
                "rows": rows}
    print(ref, json.dumps({k: v for k, v in res[ref].items() if k != "rows"}, ensure_ascii=False))
json.dump(res, open(OUT / "work/sizes.json", "w"), ensure_ascii=False, indent=1)
