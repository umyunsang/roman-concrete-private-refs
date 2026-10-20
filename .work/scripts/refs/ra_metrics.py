"""측정값 묶음(데이터 파일): stats·geo·angles·textsize·titlesize·sizes·plate·register -> 203x-seoul-london-berlin_metrics.json"""
import json
from pathlib import Path
OUT = Path("/Users/um-yunsang/roman-concrete-private-refs/.work/out/refs-analysis"); W = OUT / "work"
L = lambda n: json.load(open(W / n))
st, geo, ang, ts, tt, sz, pl, rg = L("stats.json"), L("geo.json"), L("angles.json"), L("textsize.json"), L("titlesize.json"), L("sizes.json"), L("plate.json"), L("register.json")
m = {}
for ref in st:
    s = dict(st[ref]); s["core"] = {k: v for k, v in s["core"].items() if k != "polygon_u"}
    m[ref] = {"register": rg[ref], "stats": s, "geo": {k: v for k, v in geo[ref].items() if k not in ("fit",)} | {"fit": {k: v for k, v in geo[ref]["fit"].items() if k in ("reflect", "rms_mm", "mean_err_mm", "per_point_err_mm")}},
              "angles": ang[ref], "label_text_mm": ts[ref], "title_text_mm": tt[ref],
              "sizes": {k: v for k, v in sz[ref].items() if k != "rows"} | {"objects_mm": sz[ref]["rows"]},
              "plate": pl.get(ref), "units": "정규 1000x1400 단위 / A2 mm 환산(가로 0.42, 세로 0.4243 mm/단위)"}
json.dump(m, open(OUT / "203x-seoul-london-berlin_metrics.json", "w"), ensure_ascii=False, indent=1)
print(OUT / "203x-seoul-london-berlin_metrics.json")
