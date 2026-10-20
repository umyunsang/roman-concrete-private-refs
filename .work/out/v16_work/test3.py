src = open("scripts/wireframe_v16.py", encoding="utf-8").read()
exec(compile(src, "wireframe_v16.py", "exec"))
M = Layer(0, 0, PW, PH, "map", bg=BG + (255,))
# 스케치: 패널 구획
for (x0, y0, x1, y1, c) in [(18,20,118,68,C_BASIC),(18,76,118,132,C_BASIC),(302,20,402,100,C_BASIC),(18,505,170,565,C_DETAIL),(178,505,294,565,C_BASIC),(302,505,402,565,C_BASIC),(134.5,10,285.5,90,C_CORE)]:
    M.dashed_rect(x0,y0,x1,y1,c,0.3)
# 코어 체인 윤곽
for k in range(NCELL):
    v = cell_verts(k)
    M.poly([v["L"], v["T"], v["R"], v["B"]], fill=(250,238,210), outline=C_CORE, lw=0.4)
    cx, cy = cell_center(k); M.text_c(cx, cy+1, str(k+1), fnt("b", 6), C_CORE)
# 아레나 받침 팔각
oct_pts = []
for kk in range(8):
    ang = math.radians(22.5 + 45*kk)
    X, Y = ARENA_R*math.cos(ang), ARENA_R*math.sin(ang)
    oct_pts.append((ARENA_CX + C30*(X-Y), ARENA_CY + 0.5*(X+Y)))
M.poly(oct_pts, fill=(214,204,182), outline=EDGE, lw=0.4)
print("octagon x range", min(p[0] for p in oct_pts), max(p[0] for p in oct_pts), "y", min(p[1] for p in oct_pts), max(p[1] for p in oct_pts))
# 강
cl = river_centerline()
poly, l, r = band_poly(cl, RIVER_W)
M.poly(poly, fill=RIVER, outline=RIVER_T, lw=0.3)
M.line(cl, (255,255,255,120), 0.3)
print("river", [(round(a,1), round(b,1)) for a, b in cl])
M.dot(*RIVER_A, 1.0, C_CORE)
out = M.img.resize((M.w//SS, M.h//SS), Image.LANCZOS).convert("RGB")
out.resize((840, 1188)).save("out/v16_work/test3.png")
