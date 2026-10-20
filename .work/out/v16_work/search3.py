import sys, io, contextlib, re
base = open("scripts/wireframe_v16.py", encoding="utf-8").read()

def patch(src, **kw):
    for k, v in kw.items():
        if k == "PEAK":
            src = src.replace("(152.1, 58), (205, 58), (232, 56)", "(152.1, %s), (205, %s), (232, %s)" % (v, v, v - 2))
        elif k == "T":
            src = src.replace("    T = 9.0\n    # ── 받침(흙 단면)", "    T = %s\n    # ── 받침(흙 단면)" % v)
        else:
            src = re.sub(r"^%s = [0-9.]+" % k, "%s = %s" % (k, v), src, count=1, flags=re.M)
    return src

def run(**kw):
    src = patch(base, **kw)
    ns = {"__name__": "dbg"}
    exec(compile(src, "w.py", "exec"), ns)
    R = ns["build_map"]()
    Image, ImageChops, ImageFilter = ns["Image"], ns["ImageChops"], ns["ImageFilter"]
    river = ns["poly_mask"](ns["band_poly"](R["river"], ns["RIVER_W"], bevel=True)[0])
    objs = {o["이름"]: o for o in R["objs"]}
    ar = ns["layer_mask"](objs["아레나"]["레이어"])
    co = ns["layer_mask"](objs["Core 제작 과정"]["레이어"])
    S2 = ns["S2"]
    def gap(m, region=None):
        if region:
            x0, y0, x1, y1 = [int(v * S2) for v in region]
            blank = Image.new("L", m.size, 0)
            blank.paste(m.crop((x0, y0, x1, y1)), (x0, y0))
            m = blank
        cur = river
        for step in range(0, 30):
            if step:
                cur = cur.filter(ImageFilter.MaxFilter(3))
            if ImageChops.multiply(cur, m).getbbox():
                return step * 0.5
        return 15
    gw = gap(ar, (240, 150, 420, 262)); gc = gap(ar, (200, 300, 360, 400)); gk = gap(co)
    ab = objs["아레나"]["측정"]["box"]; cb = objs["Core 제작 과정"]["측정"]["box"]
    aA = (ab[2]-ab[0])*(ab[3]-ab[1]); cA = (cb[2]-cb[0])*(cb[3]-cb[1])
    return dict(wall=gw, corner=gc, core=gk, arena=(round(ab[2]-ab[0]), round(ab[3]-ab[1]), round(aA)), corebox=(round(cb[2]-cb[0]), round(cb[3]-cb[1]), round(cA)), ratio=round(aA/cA, 3))

if __name__ == "__main__":
    tests = [dict(HUG=23, ARENA_XL=236, ARENA_CY=296.5, BOARD_H=15.0, ARENA_R=95.0, PEAK=54, T=7),
             dict(HUG=22, ARENA_XL=236, ARENA_CY=296.5, BOARD_H=15.0, ARENA_R=95.0, PEAK=54, T=7),
             dict(HUG=22, ARENA_XL=234, ARENA_CY=298.5, BOARD_H=15.0, ARENA_R=95.0, PEAK=54, T=7)]
    for kw in tests:
        print(kw, run(**kw))
