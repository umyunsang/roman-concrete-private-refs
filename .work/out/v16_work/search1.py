import sys, io, contextlib, itertools, re
base = open("scripts/wireframe_v16.py", encoding="utf-8").read()

def run(HUG, XL, CY, PEAK, T):
    src = base
    src = re.sub(r"HUG = [0-9.]+ ", "HUG = %s " % HUG, src, count=1)
    src = re.sub(r"ARENA_XL = [0-9.]+ ", "ARENA_XL = %s " % XL, src, count=1)
    src = re.sub(r"ARENA_CY = [0-9.]+", "ARENA_CY = %s" % CY, src, count=1)
    # 벽 최고 높이
    src = src.replace("(152.1, 58), (205, 58), (232, 56)", "(152.1, %s), (205, %s), (232, %s)" % (PEAK, PEAK, PEAK - 2))
    src = src.replace("    T = 9.0\n    # ── 받침(흙 단면)", "    T = %s\n    # ── 받침(흙 단면)" % T)
    ns = {"__name__": "dbg"}
    exec(compile(src, "w.py", "exec"), ns)
    R = ns["build_map"]()
    Image, ImageChops, ImageFilter = ns["Image"], ns["ImageChops"], ns["ImageFilter"]
    cl = R["river"]
    river = ns["poly_mask"](ns["band_poly"](cl, ns["RIVER_W"], bevel=True)[0])
    ar = ns["layer_mask"]([o for o in R["objs"] if o["이름"] == "아레나"][0]["레이어"])
    co = ns["layer_mask"]([o for o in R["objs"] if o["이름"] == "Core 제작 과정"][0]["레이어"])
    S2 = ns["S2"]
    W, H = ar.size
    # 영역 분리: 벽(상단 y<262), 모서리(y>300)
    def gap(mask_obj, region=None):
        m = mask_obj
        if region:
            x0, y0, x1, y1 = [int(v * S2) for v in region]
            blank = Image.new("L", m.size, 0)
            blank.paste(m.crop((x0, y0, x1, y1)), (x0, y0))
            m = blank
        if not m.getbbox():
            return None
        cur = river
        for step in range(0, 30):
            if step:
                cur = cur.filter(ImageFilter.MaxFilter(3))
            if ImageChops.multiply(cur, m).getbbox():
                return step * 0.5
        return 15
    g_wall = gap(ar, (240, 150, 420, 262))
    g_corner = gap(ar, (200, 300, 360, 400))
    g_core = gap(co)
    top = [o for o in R["objs"] if o["이름"] == "아레나"][0]["측정"]["box"]
    return g_wall, g_corner, g_core, top

if __name__ == "__main__":
    for HUG, XL, CY, PEAK, T in [(22, 236, 292.5, 54, 7), (22, 236, 290.5, 54, 7), (22, 236, 294.5, 54, 7), (23, 238, 292.5, 54, 7)]:
        print(HUG, XL, CY, PEAK, T, run(HUG, XL, CY, PEAK, T))
