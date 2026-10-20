import time
src = open("scripts/wireframe_v16.py", encoding="utf-8").read()
exec(compile(src, "wireframe_v16.py", "exec"))
bgl = Layer(0, 0, 230, 90, "t", bg=BG + (255,))
specs = [("pantheon", draw_pantheon, 36, 40, 66), ("aqueduct", draw_aqueduct, 108, 40, 68), ("portus", draw_portus, 184, 40, 64)]
for name, fn, cx, cy, w in specs:
    l = Layer(cx - 45, cy - 40, cx + 45, cy + 40, name)
    fn(l, cx, cy, w)
    print(name, l.measure())
    bgl.paste(l)
out = bgl.img.resize((bgl.w // SS * 3, bgl.h // SS * 3), Image.LANCZOS).convert("RGB")
out.save("out/v16_work/test7.png"); print(out.size)
