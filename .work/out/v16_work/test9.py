src = open("scripts/wireframe_v16.py", encoding="utf-8").read()
exec(compile(src, "wireframe_v16.py", "exec"))
M = Layer(0, 0, PW, PH, "map", bg=BG + (255,))
for (x0, y0, x1, y1, c) in [(18,20,118,68,C_BASIC),(18,76,118,132,C_BASIC),(302,20,402,100,C_BASIC),(18,505,170,565,C_DETAIL),(178,505,294,565,C_BASIC),(302,505,402,565,C_BASIC),(126.5,10,293.5,90,C_CORE)]:
    M.dashed_rect(x0,y0,x1,y1,c,0.3)
for k in range(NCELL):
    v = cell_verts(k)
    M.poly([v["L"], v["T"], v["R"], v["B"]], fill=(250,238,210), outline=C_CORE, lw=0.4)
oct_pts = []
for kk in range(8):
    ang = math.radians(22.5 + 45*kk)
    X, Y = ARENA_R*math.cos(ang), ARENA_R*math.sin(ang)
    oct_pts.append((ARENA_CX + C30*(X-Y), ARENA_CY + 0.5*(X+Y)))
M.poly(oct_pts, fill=(214,204,182), outline=EDGE, lw=0.4)
# wall top approx
M.line([(ARENA_CX-70, ARENA_CY-85), (ARENA_CX-10, ARENA_CY-91)], (200,0,0), 0.5)
print("A", RIVER_A, "arena cx", ARENA_CX)
cl = river_centerline(L2=(215-RIVER_A[0])/C30, L3=130)
poly, l, r = band_poly(cl, RIVER_W)
M.poly(poly, fill=RIVER, outline=RIVER_T, lw=0.3)
print([(round(a,1), round(b,1)) for a,b in cl])
# 후보 개체 상자
def box(x0,y0,x1,y1,c,t):
    M.rect(x0,y0,x1,y1,outline=c,lw=0.5); M.text(x0+1,y0+4,t,fnt("s",3),c)
box(143,100,209,164,C_SUP,"욕장"); box(214,96,268,136,C_SUP2,"베수비오"); 
box(280,106,348,160,C_SUP,"판테온")
box(18,376,90,448,C_DETAIL,"확대창"); 
box(154,394,226,466,C_DETAIL,"확대창B")
box(240,380,308,436,C_SUP,"수도교"); box(345,380,409,436,C_SUP,"메텔라"); box(318,440,386,496,C_SUP,"시장")
box(30,432,94,478,C_SUP,"포르투스")
out = M.img.resize((840, 1188), Image.LANCZOS).convert("RGB")
out.save("out/v16_work/test9.png")
