def draw_mausoleum():
    """L8 하드리아누스 영묘 + 폰스 아일리우스(22:10 재구성, 레퍼런스 user_hadrian_bridge.jpg):
    앞(+Y, 카메라 쪽)에서 영묘 앞 운하(canal_h6)를 건너는 아치 3개 다리(가운데 아치가 가장 큼) → 풀 덮인 둔덕(잔디 비탈) 위 축대 기단
    → 원형 기둥 회랑(작은 열주) + 얕은 돔. 모든 모양은 평면 X·Y축 정렬. 치수는 인쇄하지 않는다."""
    lm = LM.get("L8")
    if not lm:
        return
    g = {k: _lm_plan(lm, k, v) for k, v in D4_LANDMARKS[1]["plan"].items()}
    iso = _siso("L8")
    X0, Y0, X1, Y1 = [float(v) for v in g["base"]]                  # 둔덕 지면(풀 비탈 밑변)
    bh = float(g["base_h"])                                         # 축대 기단 윗면 z(5.0)
    dcx, dcy = [float(v) for v in g["drum_c"]]
    R = float(g["drum_r"])                                          # 회랑 바닥(스타일로베이트) 반지름
    z0d, z1d = [float(v) for v in g["drum_z"]]                      # 회랑 z: 기단 윗면 ~ 엔타블러처 윗면
    zt1 = float(g["top_z"][1])                                      # 돔 꼭대기 z
    bX0, bY0, bX1, bY1 = [float(v) for v in g["bridge"]]
    brh = float(g["bridge_h"])                                      # 다리 상판 z(3.0) = 둔덕 윗면 z
    nar = int(g["bridge_arches"])
    marble, trav = (246, 238, 220), (226, 212, 182)
    grass, grass_top = (122, 150, 84), (146, 172, 100)
    cxm, cym = (X0 + X1) / 2.0, (Y0 + Y1) / 2.0
    # 0 풀 둔덕: 사각 뿔대(비탈 잔디색), 밑변 = 기단 지면, 윗면(z = 상판 높이)은 안쪽으로 6 들어간다
    inset = 7.0
    hill_base = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]
    k_ = ((X1 - X0) - 2 * inset) / float(X1 - X0)
    hill = m_frustum(hill_base, 0.0, brh, k_, grass, top=grass_top)
    hill.draw(iso, lw=0.10)
    PX0, PY0, PX1, PY1 = X0 + inset, Y0 + inset, X1 - inset, Y1 - inset   # 둔덕 윗면(평평한 풀밭)
    for u in (0.3, 0.62):                                           # 비탈 풀결(수평 띠)
        zc = brh * u
        ii = inset * (1.0 - u)
        iso.line3([(X0 + ii, Y1 - ii + 0.01, zc), (X1 - ii, Y1 - ii + 0.01, zc)], (112, 138, 76), 0.1)
        iso.line3([(X1 - ii + 0.01, Y0 + ii, zc), (X1 - ii + 0.01, Y1 - ii, zc)], (108, 134, 72), 0.1)
    # 1 축대 기단(대리석 마감): 둔덕 윗면 위 사각 축대 z brh → bh
    WX0, WX1 = dcx - 15.5, dcx + 15.5
    WY0, WY1 = dcy - 14.0, dcy + 12.5
    wall = Mesh(None)
    wall.extend(m_box(WX0, WY0, brh, WX1, WY1, bh, marble, top=(232, 224, 206)))
    wall.draw(iso, lw=0.12)
    iso.line3([(WX0, WY1 + 0.01, brh + 1.0), (WX1, WY1 + 0.01, brh + 1.0)], (200, 190, 170), 0.15)
    iso.line3([(WX1 + 0.01, WY0, brh + 1.0), (WX1 + 0.01, WY1, brh + 1.0)], (194, 184, 164), 0.15)
    for xj in range(int(WX0) + 3, int(WX1), 4):                     # 축대 줄눈(앞면)
        iso.line3([(xj, WY1 + 0.01, brh), (xj, WY1 + 0.01, bh)], (214, 206, 188), 0.1)
    for yj in range(int(WY0) + 3, int(WY1), 4):
        iso.line3([(WX1 + 0.01, yj, brh), (WX1 + 0.01, yj, bh)], (208, 200, 182), 0.1)
    # 2 원형 기둥 회랑 + 얕은 돔(한 메시로 깊이순 정렬)
    col_r = R - 1.3                                                 # 기둥 고리 반지름
    ncol = 18
    zc0, zc1 = z0d + 0.7, z1d - 1.6                                 # 기둥 아래·위
    col = Mesh(None)
    col.extend(m_cyl(dcx, dcy, R, z0d, z0d + 0.7, marble, n=32, top=(236, 228, 210)))          # 스타일로베이트
    col.extend(m_cyl(dcx, dcy, col_r - 1.5, z0d + 0.7, zc1, (196, 184, 162), n=28, top=(214, 204, 184)))   # 안쪽 벽(그늘)
    for i in range(ncol):
        a = 2.0 * math.pi * i / ncol
        col.extend(m_cyl(dcx + col_r * math.cos(a), dcy + col_r * math.sin(a), 0.72, zc0, zc1, (250, 244, 228), n=8, top=(240, 232, 214)))
    col.extend(m_cyl(dcx, dcy, R - 0.2, zc1, z1d, marble, n=32, top=(238, 230, 212)))            # 엔타블러처
    ra, za = col_r - 2.4, z1d + 2.2
    col.extend(m_cyl(dcx, dcy, ra, z1d, za, (238, 230, 212), n=28, top=(226, 218, 200)))         # 낮은 아티카 원통
    dome_c = (150, 158, 160)
    prof = [(ra, za), (ra * 0.97, za + 0.6), (ra * 0.82, za + 1.5), (ra * 0.55, za + 2.2), (ra * 0.22, za + 2.6)]
    for (r_a, z_a), (r_b, z_b) in zip(prof[:-1], prof[1:]):
        col.extend(m_cyl(dcx, dcy, r_a, z_a, z_b, dome_c, n=28, k=r_b / r_a))
    col.extend(m_cyl(dcx, dcy, ra * 0.12, zt1 - 0.5, zt1, (214, 206, 188), n=8))
    col.draw(iso, lw=0.08)
    # 3 다리 앞 디딤 2단(상판 3.0 → 3.67 → 4.33 → 축대 윗면 5.0): 축대 앞(+Y) 변에서 상판 쪽으로
    st_x0, st_x1 = bX0, bX1
    rise = (bh - brh) / 3.0
    ys_n = WY1                                                      # 축대 앞 변 평면 Y
    stp = Mesh(None)
    steps_ = []
    for k in range(2):
        ya_, yb_ = ys_n + 2.0 * k, ys_n + 2.0 * (k + 1)             # k=0: 축대 쪽 높은 단(4.33), k=1: 바깥 단(3.67)
        zt_ = brh + rise * (2 - k)
        stp.extend(m_box(st_x0, ya_, brh - 0.01, st_x1, yb_, zt_, (232, 224, 206), top=(238, 230, 214)))
        steps_.append({"Y": [round(ya_, 2), round(yb_, 2)], "z_top": round(zt_, 2)})
    stp.draw(iso, lw=0.1)
    GEO["mausoleum_steps"] = {"X": [st_x0, st_x1], "steps": steps_, "riser": round(rise, 3), "ramp": None,
                              "rule": "22:10 재구성: 다리(앞쪽 +Y) 남쪽 둑 진입 경사 Z 3.0 → 0, 상판 3.0 → 축대 앞 디딤 2단(3.67·4.33) → 축대 윗면 5.0. 양 끝 보행면 높이 차 0"}
    # 4 다리: 상판·난간 + +X면 아치 3개(가운데 가장 큼), 영묘 앞 운하(수면이 땅보다 7 낮다) 위
    w_y0, w_y1 = [float(v) for v in _lm_plan(lm, "canal_Y", [bY0 + 12.0, bY0 + 24.0])]   # 영묘 앞 운하 Y 폭(물 구간)
    wz = -DIO_T                                                     # 수면 z
    lowp = Mesh(None)
    lowp.extend(m_box(bX0, w_y0, wz, bX1, w_y1, -0.3, trav, top=(236, 226, 202)))                 # 물 위 구간 교각 아랫부분(수면 ~ 땅)
    lowp.draw(iso, lw=0.1)
    br = Mesh(None)
    br.extend(m_box(bX0, bY0, -0.4, bX1, bY1, brh, trav, top=(236, 226, 202)))                    # 상판·받침·스팬드럴(한 덩이: 윗면 이음 없음)
    br.extend(m_box(bX0, bY0, brh, bX0 + 0.55, bY1, brh + 0.8, (230, 218, 192)))
    br.extend(m_box(bX1 - 0.55, bY0, brh, bX1, bY1, brh + 0.8, (230, 218, 192)))
    br.draw(iso, lw=0.1)
    # 아치: 물 구간 안에 3개. 가운데 = 큰 아치(반원), 좌우 = 작은 아치, 교각 0.9. 아치 아래는 수면까지 물이 보인다
    pier = 0.9
    wsm = (w_y1 - w_y0 - (nar - 1) * pier) / (nar - 1 + 2.0)        # 작은 아치 폭 (가운데 = 2배)
    wbig = wsm * 2.0
    widths = [wsm if k != nar // 2 else wbig for k in range(nar)]
    crown = [1.4 if k != nar // 2 else 2.2 for k in range(nar)]     # 아치 꼭대기 z(가운데가 높다)
    ya = w_y0
    arches_ = []
    for k in range(nar):
        aw, yc = widths[k], ya + widths[k] / 2.0
        rr_, zsp = aw / 2.0, crown[k] - aw / 2.0
        q = [(ya, wz), (ya + aw, wz), (ya + aw, zsp)] + [(yc + rr_ * math.cos(math.pi * i / 14.0), zsp + rr_ * math.sin(math.pi * i / 14.0)) for i in range(0, 15)] + [(ya, zsp)]
        P.poly([iso.p(bX1 + 0.02, u, z) for u, z in q], fill=(70, 116, 152), outline=(124, 108, 84), lw=0.12)
        qi = [(yc + rr_ * 0.84 * math.cos(math.pi * i / 14.0), zsp + rr_ * 0.84 * math.sin(math.pi * i / 14.0)) for i in range(0, 15)]
        P.line([iso.p(bX1 + 0.03, u, z) for u, z in qi], (50, 90, 124), 0.16)
        arches_.append([round(ya, 2), round(ya + aw, 2), crown[k]])
        ya += aw + pier
    iso.line3([(bX1 + 0.02, bY0, brh - 0.45), (bX1 + 0.02, bY1, brh - 0.45)], (196, 180, 150), 0.14)   # 아치 위 띠
    iso.line3([(bX1 + 0.02, bY0, brh), (bX1 + 0.02, bY1, brh)], (170, 154, 126), 0.16)
    for yj in [bY0 + 2.0 + 3.0 * i for i in range(int((bY1 - bY0) / 3.0))]:                              # 난간 기둥 마디
        iso.line3([(bX1 - 0.02, yj, brh), (bX1 - 0.02, yj, brh + 0.8)], (200, 186, 158), 0.1)
    # 5 남쪽 둑 진입 경사(다리 앞 끝 → 땅): Z 3.0 → 0, 평면 Y bY1 → bY1 + 10
    ra0, ra1 = bY1, bY1 + 10.0
    P.poly([iso.p(bX0, ra0, brh), iso.p(bX1, ra0, brh), iso.p(bX1, ra1, 0.0), iso.p(bX0, ra1, 0.0)], fill=(236, 226, 202))
    P.poly([iso.p(bX1, ra0, brh), iso.p(bX1, ra1, 0.0), iso.p(bX1, ra0, 0.0)], fill=ftone(trav, 0.7071, 0.7071))
    P.line([iso.p(bX1, ra0, brh), iso.p(bX1, ra1, 0.0)], (150, 134, 108), 0.2, joint=False)
    P.line([iso.p(bX0, ra0, brh), iso.p(bX0, ra1, 0.0)], (170, 154, 126), 0.15, joint=False)
    for k in range(1, 5):
        f_ = k / 5.0
        P.line([iso.p(bX0, ra0 + 10.0 * f_, brh * (1 - f_)), iso.p(bX1, ra0 + 10.0 * f_, brh * (1 - f_))], (206, 192, 164), 0.1, joint=False)
    # 6 기록
    hill_pts = [iso.p(x_, y_, z_) for x_ in (X0, X1) for y_ in (Y0, Y1) for z_ in (0.0,)] + [iso.p(x_, y_, brh) for x_ in (PX0, PX1) for y_ in (PY0, PY1)]
    wall_pts = [iso.p(x_, y_, z_) for x_ in (WX0, WX1) for y_ in (WY0, WY1) for z_ in (brh, bh)]
    col_pts = [iso.p(dcx + R * math.cos(math.radians(t)), dcy + R * math.sin(math.radians(t)), z) for t in range(0, 360, 10) for z in (z0d, z1d)]
    col_pts.append(iso.p(dcx, dcy, zt1))
    br_pts = ([iso.p(x_, y_, z_) for x_ in (bX0, bX1) for y_ in (bY0, bY1) for z_ in (-0.4, brh + 0.8)]
              + [iso.p(x_, y_, wz) for x_ in (bX0, bX1) for y_ in (w_y0, w_y1)])
    ramp_pts = [iso.p(x_, y_, z_) for x_ in (bX0, bX1) for y_, z_ in ((ra0, brh), (ra1, 0.0))]
    base_pts = hill_pts + wall_pts
    add_fp("영묘 기단", _hull(base_pts), "대상 면")
    add_fp("영묘 원통", _hull(col_pts), "대상 면")
    add_fp("폰스 아일리우스 다리", _hull(br_pts), "대상 면")
    strip_r = [iso.p(WX1 - 1.9, WY0 + 0.6, bh), iso.p(WX1 - 0.3, WY0 + 0.6, bh), iso.p(WX1 - 0.3, WY1 - 0.3, bh), iso.p(WX1 - 1.9, WY1 - 0.3, bh)]
    strip_f = [iso.p(WX0 + 0.6, WY1 - 1.5, bh), iso.p(WX1 - 0.3, WY1 - 1.5, bh), iso.p(WX1 - 0.3, WY1 - 0.3, bh), iso.p(WX0 + 0.6, WY1 - 0.3, bh)]
    GEO["fpset_영묘 기단 윗면"] = [strip_r, strip_f]
    add_fp("영묘 기단 윗면", strip_r, "대상 면")
    hull = _hull(base_pts + col_pts)
    GEO["parts_L8"] = [_hull(base_pts), _hull(col_pts), _hull(br_pts + ramp_pts)]
    for pg in GEO["parts_L8"]:
        ex_poly(pg, 2.0)
    GEO["sil_L8"] = hull
    GEO["sil_L8_bridge"] = _hull(br_pts + ramp_pts)
    bb = bbox_of(base_pts + col_pts + br_pts + ramp_pts)
    record("L8", lm["name"], "Core(표준 랜드마크)", lm["projected_box"], bb, "다리 포함 외곽")
    DRAWN["mausoleum_access"] = GEO.get("mausoleum_steps")
