import sys, io, contextlib
src = open("scripts/wireframe_v16.py", encoding="utf-8").read()
ns = {"__name__": "dbg"}
exec(compile(src, "wireframe_v16.py", "exec"), ns)
R = ns["build_map"]()
ns["build_labels"](R); ns["render_panels"](R)
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    lines = ns["analyze"](R)
from PIL import ImageChops, ImageFilter
for nm in ("아레나", "Core 제작 과정"):
    cur = R["m_river"]
    for step in range(1, 25):
        cur = cur.filter(ImageFilter.MaxFilter(3))
        inter = ImageChops.multiply(cur, R["masks"][nm])
        bb = inter.getbbox()
        if bb:
            print(nm, "step", step, "gap<=", step*0.5, "bbox mm", [v/2 for v in bb])
            break
inter = ImageChops.multiply(R["m_river"], R["masks"]["Core 제작 과정"]); print("core overlap bbox", [v/2 for v in inter.getbbox()] if inter.getbbox() else None)
