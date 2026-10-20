import time
src = open("scripts/wireframe_v16.py", encoding="utf-8").read()
exec(compile(src, "wireframe_v16.py", "exec"))
bgl = Layer(0, 0, 300, 160, "t", bg=BG + (255,))
specs = [("metella", lambda l: draw_metella(l, 40, 60, 64), (0,10,85,110)), ("market", lambda l: draw_market(l, 128, 60, 66), (85,10,170,110)),
         ("vesuvius", lambda l: draw_vesuvius(l, 210, 60, 52), (170,10,250,110)), ("farm", lambda l: draw_farm(l, 215, 70), (170, 10, 250, 110))]
for name, fn, reg in specs:
    l = Layer(reg[0], reg[1], reg[2], reg[3], name)
    fn(l)
    print(name, l.measure())
    bgl.paste(l)
for name, fn, cx, cy in [("cart", draw_cart, 30, 140), ("ship", draw_ship, 90, 140), ("crane", draw_crane, 150, 140)]:
    l = Layer(cx - 30, cy - 25, cx + 30, cy + 20, name)
    fn(l, cx, cy)
    print(name, l.measure())
    bgl.paste(l)
l = Layer(200, 90, 300, 160, "zoom"); 
l2 = Layer(190, 88, 262, 160, "zoom"); draw_zoom(l2, 226, 124, 70); print("zoom", l2.measure()); bgl.paste(l2)
out = bgl.img.resize((bgl.w // SS * 3, bgl.h // SS * 3), Image.LANCZOS).convert("RGB")
out.save("out/v16_work/test8.png"); print(out.size)
