# 22:33 포르투스 90° 회전 후 render.py 의 hexring · portus_params · draw_portus 전체(원본 d5 render.py 의 같은 세 함수를 통째로 교체)

def hexring(cx, cy, r, a0=30.0):
    return [(cx + r * math.cos(math.radians(a0 + 60 * k)), cy + r * math.sin(math.radians(a0 + 60 * k))) for k in range(6)]


def portus_params():
    """사양 core_map.portus_geometry의 방파제·운하·등대섬(없으면 결정 값)"""
    mol = sget(PG, "moles", "PORTUS_MOLES", default=None) or sget(CM, "portus_moles", default=None) or {}
    can = sget(PG, "canals", "PORTUS_CANALS", default=None) or sget(CM, "portus_canals", default=None) or []
    lh = sget(PG, "lighthouse", "PORTUS_LIGHTHOUSE", default=None) or sget(CM, "portus_lighthouse", default=None) or {}
    r_out = float(sget(mol, "r_out", "r_outer", default=21.0))
    r_in = float(sget(mol, "r_in", "r_inner", default=18.4))
    arm_a = [float(v) for v in sget(mol, "arm_a_deg", "arm_a", default=[173.0, 33.0])]
    arm_b = [float(v) for v in sget(mol, "arm_b_deg", "arm_b", default=[187.0, 327.0])]
    col = [float(v) for v in sget(mol, "colonnade_deg", "colonnade", default=[282.0, 324.0])]
    canals = []
    for c in (can or [{"name": "강 쪽 운하", "plan_x": [511.7, 531.4], "plan_y": [310.5, 313.5]},
                      {"name": "외항 쪽 운하", "plan_x": [554.8, 574.06], "plan_y": [310.5, 313.5]}]):
        canals.append({"name": c.get("name", "운하"), "x": [float(v) for v in c.get("plan_x")], "y": [float(v) for v in c.get("plan_y")]})
    ang = float(sget(lh, "plan_angle_deg", "angle_deg", "angle", default=348.0))
    lr = float(sget(lh, "plan_r", "r", default=24.0))
    isl = float(sget(lh, "island_r", default=3.4))
    tiers = sget(lh, "tiers", default=[[2.8, 1.0, 9.0], [2.25, 9.0, 15.4], [1.75, 15.4, 20.6]])
    lant = sget(lh, "lantern", default=[1.1, 20.6, 24.0])
    hwr = float(sget(PG, "hexagon_water_R", default=15.2) or 15.2)
    return dict(r_out=r_out, r_in=r_in, arm_a=arm_a, arm_b=arm_b, col=col, canals=canals, ang=ang, lr=lr, isl=isl, tiers=tiers, lant=lant, hwr=hwr)


def draw_portus():
    L6 = LM["L6"]
    hx, hy = PG["hexagon_plan_center"]
    HR = PG["hexagon_plan_R"]
    bx, by = PG["claudian_basin_plan_center"]
    pp = portus_params()
    r_in, r_out, HWR = pp["r_in"], pp["r_out"], pp["hwr"]
    iso = _siso("L6")
    # 1 육각 내항(육지): 포장 둘레·성벽·창고 고리(붉은 기와)·부두·물
    pave = hexring(hx, hy, HR)
    iso.poly3([(x, y, 0) for x, y in pave], fill=(216, 202, 170), ol=(150, 130, 98), lw=0.25)
    wall = Mesh(None)
    # 22:33: 운하는 +X(변 5)·−X(변 2) 쪽 변 가운데로 지난다 → 그 두 변은 가운데(0.44~0.56, 변 24mm 중 약 2.9mm 위로 개구 3mm 이상)를 비운다
    trims = {2: [(0.0, 0.42), (0.58, 1.0)], 5: [(0.0, 0.42), (0.58, 1.0)]}
    for k in range(6):
        a0p, b0p = pave[k], pave[(k + 1) % 6]
        for (f0, f1) in trims.get(k, [(0.0, 1.0)]):
            a, b = lerp(a0p, b0p, f0), lerp(a0p, b0p, f1)
            wall.extend(m_prism([a, b, lerp(b, (hx, hy), 0.04), lerp(a, (hx, hy), 0.04)], 0, 1.4, (198, 176, 140), top=(214, 196, 162)))
    iso.poly3([(x, y, 0.3) for x, y in hexring(hx, hy, HWR + 1.4)], fill=(206, 194, 168), ol=(150, 132, 104), lw=0.18)
    water = [(x, y, 0.32) for x, y in hexring(hx, hy, HWR)]
    wp = [iso.p(*p) for p in water]
    P.poly(wp, fill=HARBOR_C, outline=(96, 136, 166), lw=0.2)
    facet_fill(P, wp, HARBOR_C, cell=3.2, amp=0.05, key="육각물", jit=0.12)
    wh = Mesh(None)
    for k in range(6):
        a0_, a1_ = math.radians(30 + 60 * k), math.radians(30 + 60 * (k + 1))
        pieces = [(0.06, 0.46), (0.54, 0.94)]
        if k in (2, 5):          # 운하가 지나는 변: 가운데 폭 약 3.5mm 이상 비운다
            pieces = [(0.06, 0.40), (0.60, 0.94)]
        for (f0, f1) in pieces:
            q = []
            for (r, f) in ((17.2, f0), (17.2, f1), (22.0, f1), (22.0, f0)):
                pa = (hx + r * math.cos(a0_), hy + r * math.sin(a0_))
                pb = (hx + r * math.cos(a1_), hy + r * math.sin(a1_))
                q.append((pa[0] + (pb[0] - pa[0]) * f, pa[1] + (pb[1] - pa[1]) * f))
            wh.extend(m_prism(q, 0.3, 4.2, WALL_W))
            wh.extend(m_frustum(q, 4.2, 6.0, 0.5, ROOF))
    # 2 클라우디우스 외항 수면(바다 위): 방파제 안쪽
    cx_, cy_ = iso.p(bx, by, 0)
    P.ell(cx_, cy_, 1.2247 * (r_in + 0.6), 0.7071 * (r_in + 0.6), fill=HARBOR_C)
    # 3 운하 2개(사양 plan_x·plan_y): 강·외항 수면에서 육각 내항 수면 안쪽까지, 포장·안벽 위에 그려 폭 3mm 개구부를 낸다
    canal_info = []
    for c in pp["canals"]:
        (x0, x1), (y0, y1) = c["x"], c["y"]
        xa, xb = min(x0, x1), max(x0, x1)
        ya, yb_ = min(y0, y1), max(y0, y1)
        # 22:33 회전: 운하는 X축 방향(긴 쪽 x, 폭 y). 사양 plan_x 그대로 그린다(추가 연장 0)
        q = [iso.p(xa, ya, 0.33), iso.p(xb, ya, 0.33), iso.p(xb, yb_, 0.33), iso.p(xa, yb_, 0.33)]
        P.poly(q, fill=HARBOR_C)
        P.line([iso.p(xa, ya, 0.33), iso.p(xb, ya, 0.33)], (96, 136, 166), 0.15, joint=False)
        P.line([iso.p(xa, yb_, 0.33), iso.p(xb, yb_, 0.33)], (96, 136, 166), 0.15, joint=False)
        hexw = hexring(hx, hy, HWR)
        if xa > hx:          # 외항 쪽(+X): 육각 수면(안쪽 끝 xa) ↔ 외항 수면(바깥 끝 xb)
            e_hex, e_out = xa, xb
            ok_hex = all(in_poly((e_hex, y), hexw) for y in (y0, y1))
            ok_out = all(math.hypot(e_out - bx, y - by) < r_in for y in (y0, y1))
        else:                # 강 쪽(−X): 강(바깥 끝 xa) ↔ 육각 수면(안쪽 끝 xb)
            e_hex, e_out = xb, xa
            ok_hex = all(in_poly((e_hex, y), hexw) for y in (y0, y1))
            ok_out = e_out <= hx - 31.0          # 지도의 강은 원본 d5에서 −X 쪽으로 옮긴다(복사본 지도에는 아직 없음)
        canal_info.append({"name": c["name"], "continuous": bool(ok_hex and ok_out), "opening_w": round(y1 - y0, 2),
                           "screen_w": round((y1 - y0) * C30, 2), "plan_y": [round(ya, 2), round(yb_, 2)], "plan_x": [round(xa, 2), round(xb, 2)],
                           "plan_y_drawn": [round(ya, 2), round(yb_, 2)], "plan_y_spec": [round(ya, 2), round(yb_, 2)],
                           "end_dev_mm": 0.0, "render_extension_mm": 0.0})
    wall.draw(iso, lw=0.10)
    wh.draw(iso, lw=0.10)
    # 4 방파제 두 팔(마지막 조각을 끝각에서 정확히 자른다) + 창고·열주
    moles = Mesh(None)
    tip_polys = {}

    def mole_arc(t0, t1, key):
        n = max(1, int(math.ceil(abs(t1 - t0) / 6.15)))
        for i in range(n):
            ta = math.radians(t0 + (t1 - t0) * i / n)
            tb = math.radians(t0 + (t1 - t0) * (i + 1) / n)
            q = [(bx + r_in * math.cos(ta), by + r_in * math.sin(ta)), (bx + r_out * math.cos(ta), by + r_out * math.sin(ta)),
                 (bx + r_out * math.cos(tb), by + r_out * math.sin(tb)), (bx + r_in * math.cos(tb), by + r_in * math.sin(tb))]
            moles.extend(m_prism(q, -9.7, 0.0, (206, 196, 174)))          # d5: 바다 수면 −9.7부터(Blender coast·D12와 같은 바깥 면 9.7mm)
            if i == n - 1:
                tip_polys[key] = _hull([iso.p(x, y, -9.7) for x, y in q])          # 수면(−9.7) 높이 팔 끝 외곽
    mole_arc(pp["arm_a"][0], pp["arm_a"][1], "arm_a")
    mole_arc(pp["arm_b"][0], pp["arm_b"][1], "arm_b")
    rm = (r_in + r_out) / 2.0
    for th in (60.0, 75.0, 90.0, 105.0, 120.0):                     # 바다 쪽 방파제(팔 A) 위 창고(옛 150~210°에서 −90°)
        t = math.radians(th)
        Xc, Yc = bx + rm * math.cos(t), by + rm * math.sin(t)
        moles.extend(m_box(Xc - 1.2, Yc - 1.2, 0.0, Xc + 1.2, Yc + 1.2, 1.9, (230, 210, 180)))
        moles.extend(m_frustum([(Xc - 1.3, Yc - 1.3), (Xc + 1.3, Yc - 1.3), (Xc + 1.3, Yc + 1.3), (Xc - 1.3, Yc + 1.3)], 1.9, 3.1, 0.4, ROOF))
    c0, c1 = pp["col"]
    th = c0
    while th <= c1 + 1e-6:                                          # 열주: 팔 B의 12~54°에만
        t = math.radians(th)
        moles.extend(m_cyl(bx + rm * math.cos(t), by + rm * math.sin(t), 0.35, 0.0, 2.6, (240, 232, 214), n=6))
        th += 7.0
    # 5 등대섬(사양 평면 각·반지름): 섬 + 층을 쌓은 탑 + 등롱
    LX, LY = bx + pp["lr"] * math.cos(math.radians(pp["ang"])), by + pp["lr"] * math.sin(math.radians(pp["ang"]))
    tower = Mesh(None)
    tower.extend(m_cyl(LX, LY, pp["isl"], -9.7, -0.4, (150, 140, 124), n=16))                # d5: 섬 옆면을 바다 수면 −9.7까지(Blender coast와 같은 깊이)
    tower.extend(m_mound(LX, LY, -0.4, pp["isl"], 1.4, (150, 140, 124), key="등대섬"))
    for (r, z0, z1) in pp["tiers"]:
        tower.extend(m_cyl(LX, LY, r * 0.82, z0, z1, (236, 226, 204), n=8, top=(246, 238, 220)))
    r_l, z0_l, z1_l = pp["lant"]
    tower.extend(m_cyl(LX, LY, r_l * 0.9, z0_l, z1_l, (236, 226, 204), n=8))
    tower.extend(m_cone(LX, LY, r_l * 1.05, z1_l, 1.4, (196, 92, 64), n=8))
    moles.draw(iso, lw=0.10)
    tower.draw(iso, lw=0.10)
    for k_, (r, z0, z1) in enumerate(pp["tiers"]):
        zc = (z0 + z1) / 2.0
        cx2, cy2 = iso.p(LX + r * 0.82 * 0.7071, LY + r * 0.82 * 0.7071, zc)
        P.rect(cx2 - 0.4, cy2 - 0.8, cx2 + 0.4, cy2 + 0.8, fill=(110, 90, 70))
    lx, ly = iso.p(LX, LY, (z0_l + z1_l) / 2.0)
    soft_ell(P, lx, ly, 2.0, 1.6, (255, 214, 110), alpha=120, blur=0.5)
    P.dot(lx, ly, 0.55, (250, 196, 70))
    # 사용자 16:14: 포르투스 안의 배(돛배 4)는 지도에서 지웠다
    # 6 기록: 외곽·입구 폭·섬 양옆 물길·운하
    fps = []
    for key, (t0, t1) in (("팔 A", pp["arm_a"]), ("팔 B", pp["arm_b"])):
        n = max(8, int(abs(t1 - t0) / 3))
        ts = [t0 + (t1 - t0) * i / n for i in range(n + 1)]
        top = [iso.p(*_polar2(bx, by, r_out, t), 1.0) for t in ts] + [iso.p(*_polar2(bx, by, r_in, t), 1.0) for t in reversed(ts)]
        face = [iso.p(*_polar2(bx, by, r_out, t), 1.0) for t in ts] + [iso.p(*_polar2(bx, by, r_out, t), -0.4) for t in reversed(ts)]
        fps += [top, face]
        add_fp("포르투스 외항 방파제 %s 윗면" % key, top, "대상 면")
        add_fp("포르투스 외항 방파제 %s 바깥 면" % key, face, "대상 면")
    GEO["fpset_포르투스 외항 방파제"] = fps
    isl_fp = [iso.p(LX + pp["isl"] * math.cos(math.radians(t)), LY + pp["isl"] * math.sin(math.radians(t)), -9.7) for t in range(0, 360, 10)]
    add_fp("포르투스 등대섬", isl_fp, "섬")
    add_fp("포르투스 육각 내항", [iso.p(x, y, 0) for x, y in pave], "지면")
    ea, eb = tip_polys.get("arm_a"), tip_polys.get("arm_b")

    def face_seg(e_deg):
        return (iso.p(*_polar2(bx, by, r_in, e_deg), 0.0), iso.p(*_polar2(bx, by, r_out, e_deg), 0.0))
    sa, sb = face_seg(pp["arm_a"][1]), face_seg(pp["arm_b"][1])
    ent = min(math.hypot(p[0] - q[0], p[1] - q[1]) for p in sa for q in sb)
    ent_x = abs(sb[1][0] - sa[1][0])
    gw = [round(_poly_dist(isl_fp, ea), 2) if ea else None, round(_poly_dist(isl_fp, eb), 2) if eb else None]
    tower_fp = _hull([iso.p(LX + r * 0.82 * math.cos(math.radians(t)), LY + r * 0.82 * math.sin(math.radians(t)), z)
                      for (r, z0, z1) in pp["tiers"] for z in (z0, z1) for t in range(0, 360, 45)])
    gw_tower = [round(_poly_dist(tower_fp, ea), 2) if ea else None, round(_poly_dist(tower_fp, eb), 2) if eb else None]
    DRAWN["portus"] = {"entrance_w": round(ent, 2), "entrance_screen_x_w": round(ent_x, 2), "island_water": gw,
                       "island_water_rule": "바다 수면 높이(z −9.7, D12)에서 등대섬 외곽 ↔ 두 팔 끝 조각 외곽의 화면 거리(팔 A, 팔 B)",
                       "tower_to_arm_tips": gw_tower, "canals": canal_info,
                       "arm_end_deg": [pp["arm_a"][1] % 360, pp["arm_b"][1] % 360], "colonnade_deg": [c0, c1],
                       "lighthouse_plan": [round(LX, 2), round(LY, 2)], "lighthouse_screen_base": [round(v, 2) for v in iso.p(LX, LY, 0)]}
    pts = [iso.p(x, y, 6.0) for x, y in pave] + [iso.p(x, y, 0) for x, y in pave] + [iso.p(LX, LY, z1_l + 1.4)]
    for t in range(0, 360, 10):
        pts.append(iso.p(bx + r_out * math.cos(math.radians(t)), by + r_out * math.sin(math.radians(t)), 0))
    pts += isl_fp
    bb = bbox_of(pts)
    GEO["portus_basin_c"] = (cx_, cy_)
    GEO["portus_light"] = iso.p(LX, LY, 0)
    record("L6", L6["name"], "Core(표준 랜드마크)", L6["projected_box"], bb)


