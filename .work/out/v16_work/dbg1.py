import runpy, sys
sys.argv = ["x"]
src = open("scripts/wireframe_v16.py", encoding="utf-8").read()
ns = {"__name__": "dbg"}
exec(compile(src, "wireframe_v16.py", "exec"), ns)
R = ns["build_map"]()
ns["build_labels"](R); ns["render_panels"](R)
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    lines = ns["analyze"](R)
from PIL import ImageChops
inter = ImageChops.multiply(R["m_river"], R["masks"]["아레나"])
bb = inter.getbbox()
print("river∩arena bbox (px@2/mm):", bb, "→ mm", [v/2 for v in bb] if bb else None)
