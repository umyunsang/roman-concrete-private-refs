def _bas_arch(uc, zs, r, a0=0.0, a1=180.0, n=14):
    """반원 호 점(u, z) 목록: 각 a0 → a1"""
    return [(uc + r * math.cos(math.radians(a0 + (a1 - a0) * i / float(n))), zs + r * math.sin(math.radians(a0 + (a1 - a0) * i / float(n)))) for i in range(n + 1)]


def _bas_runs(u0, u1, step, ok):
    """u0~u1을 step 간격으로 훑어 ok(u)가 참인 연속 구간 목록"""
    out, cur, u = [], None, u0
    while u <= u1 + 1e-9:
        if ok(u):
            cur = [u, u] if cur is None else [cur[0], u]
        elif cur is not None:
            out.append(tuple(cur))
            cur = None
        u += step
    if cur is not None:
        out.append(tuple(cur))
    return out


def draw_basilica():
    """L7 막센티우스 바실리카(d5_bas 새 그림, 사용자 21:57): 레퍼런스(키 큰 붉은 벽돌 교각 + 거대한 반원 아치 열 + 너머 2~3단 아케이드 벽이 둘러싼 안뜰).
    모든 모양은 평면 X·Y축에 맞춘다. 큰 아치 열 = 화면에 보이는 +Y 면(앞), 뒤 -Y·-X 벽 안쪽 면 2~3단 아케이드, +X 바깥 면 낮은 2단 아케이드,
    윗변은 폐허처럼 들쭉날쭉. 지면 포장은 기존 L자 기단. 높이 수치는 인쇄하지 않는다."""
    lm = LM.get("L7")
    if not lm:
        return
    g = {k: _lm_plan(lm, k, v) for k, v in D4_LANDMARKS[0]["plan"].items()}
    iso = _siso("L7")
    rects = [[float(v) for v in r] for r in g["base_rects"]]
    bh = float(g["base_h"])
    mx0, my0, mx1, my1 = rects[1]                      # 본체 직사각형(안뜰 + 큰 아치 열)
    brick, cream = (186, 118, 88), (232, 222, 196)
    cream_top, wall_top = (222, 208, 180), (206, 190, 160)
    dark, glow = (96, 70, 58), (236, 190, 138)
    fcol = lit(brick, (0.0, 1.0, 0.0))                 # +Y 면 벽돌색
    xcol = lit(brick, (1.0, 0.0, 0.0))                 # +X 면 벽돌색
    ccolY, ccolX = lit(cream, (0.0, 1.0, 0.0)), lit(cream, (1.0, 0.0, 0.0))
    lineY, lineX = shade(fcol, 0.84), shade(xcol, 0.84)

    def Q(face, f, u, z):
        return (u, f, bh + z) if face == "Y" else (f, u, bh + z)

    def face_poly(face, f, pts_uz, fill, ol=None, lw=0.1):
        iso.poly3([Q(face, f, u, z) for u, z in pts_uz], fill=fill, ol=ol, lw=lw)

    def face_line(face, f, pts_uz, col, lw=0.1):
        iso.line3([Q(face, f, u, z) for u, z in pts_uz], col, lw)

    # 1 기단 포장(L자) + 줄눈
    pave = Mesh(None)
    for r in rects:
        pave.extend(m_box(r[0], r[1], 0, r[2], r[3], bh, (202, 188, 158), top=(226, 214, 190)))
    pave.draw(iso, lw=0.12)

    def y_range(X):
        ys_ = [(r[1], r[3]) for r in rects if r[0] <= X <= r[2]]
        return (min(a for a, b in ys_), max(b for a, b in ys_)) if ys_ else None

    def x_range(Y):
        xs_ = [(r[0], r[2]) for r in rects if r[1] <= Y <= r[3]]
        return (min(a for a, b in xs_), max(b for a, b in xs_)) if xs_ else None
    jc = (212, 198, 170)
    X = min(r[0] for r in rects) + 4.0
    while X < max(r[2] for r in rects) - 1.0:
        yr = y_range(X)
        if yr:
            iso.line3([(X, yr[0] + 0.4, bh + 0.02), (X, yr[1] - 0.4, bh + 0.02)], jc, 0.1)
        X += 4.0
    Y = min(r[1] for r in rects) + 4.0
    while Y < max(r[3] for r in rects) - 1.0:
        xr_ = x_range(Y)
        if xr_:
            iso.line3([(xr_[0] + 0.4, Y, bh + 0.02), (xr_[1] - 0.4, Y, bh + 0.02)], jc, 0.1)
        Y += 4.0

    # 2 아케이드 벽(뒤 -Y 벽·-X 벽 안쪽 면, +X 바깥 면): 칸마다 벽돌 상자(윗변 들쭉날쭉) + 단마다 반원 개구부 + 크림 띠
    def arcade(face, f, u0, u1, depth, heights, tiers, ow, ring=0.6):
        """face 'Y': 벽 +Y 면이 Y=f에 있고 두께가 -Y로 depth. face 'X': +X 면이 X=f, 두께 -X로 depth. u = 면을 따라 가는 좌표.
        tiers = [(바닥 z, 스프링 z, 반지름, 빛(참이면 밝은 개구부))...]"""
        n = len(heights)
        pitch = (u1 - u0) / float(n)
        wall = Mesh(None)
        for k in range(n):
            ua, ub = u0 + pitch * k, u0 + pitch * (k + 1)
            if face == "Y":
                wall.extend(m_box(ua, f - depth, bh, ub, f, bh + heights[k], brick, top=wall_top))
            else:
                wall.extend(m_box(f - depth, ua, bh, f, ub, bh + heights[k], brick, top=wall_top))
        wall.draw(iso, lw=0.1)
        base_f = fcol if face == "Y" else xcol
        cr = ccolY if face == "Y" else ccolX
        ln_c = lineY if face == "Y" else lineX
        # 벽돌 줄눈
        zt_max = max(heights)
        z_ = 1.6
        while z_ < zt_max:
            def ok(u, z_=z_):
                k = min(n - 1, int((u - u0) / pitch))
                if z_ > heights[k] - 0.3:
                    return False
                uc = u0 + pitch * (k + 0.5)
                for (zb, zs_, rr, lt) in tiers:
                    if zs_ + rr + 0.4 < heights[k] + 0.5 and abs(u - uc) < rr + ring + 0.2 and zb - 0.1 <= z_ <= zs_ + rr + ring + 0.1:
                        return False
                return True
            for (a, b) in _bas_runs(u0 + 0.2, u1 - 0.2, 0.4, ok):
                if b - a > 0.5:
                    face_line(face, f + 0.01, [(a, z_), (b, z_)], ln_c, 0.1)
            z_ += 1.8
        # 단 사이 크림 띠(벽 높이를 넘지 않는 만큼)
        for t in range(len(tiers) - 1):
            zb = tiers[t][1] + tiers[t][2] + ring + 0.15
            zc = zb + 0.6
            for (a, b) in _bas_runs(u0, u1, 0.5, lambda u, zc=zc: heights[min(n - 1, int((u - u0) / pitch))] > zc + 0.3):
                face_poly(face, f + 0.01, [(a, zb), (b + 0.5 * 0, zb), (b, zc), (a, zc)], cr, ol=None)
        # 개구부(반원 아치) + 크림 아치 띠
        for k in range(n):
            uc = u0 + pitch * (k + 0.5)
            for (zb, zs_, rr, lt) in tiers:
                if heights[k] < zs_ + rr + ring + 1.0:
                    continue
                arc_in = _bas_arch(uc, zs_, rr)
                op = [(uc - rr, zb), (uc + rr, zb)] + arc_in[:]
                face_poly(face, f + 0.012, op, glow if lt else dark, ol=None)
                outer = _bas_arch(uc, zs_, rr + ring)
                rg = outer + arc_in[::-1]
                face_poly(face, f + 0.02, rg, cr, ol=None)
                for a_ in range(15, 180, 30):
                    ca, sa = math.cos(math.radians(a_)), math.sin(math.radians(a_))
                    face_line(face, f + 0.03, [(uc + rr * ca, zs_ + rr * sa), (uc + (rr + ring) * ca, zs_ + (rr + ring) * sa)], shade(cr, 0.8), 0.1)
                # 아래 벽돌 지지 교각 기둥머리 자리: 뒤 단 개구부 아래 크림 문턱
                face_poly(face, f + 0.02, [(uc - rr - 0.3, zb), (uc + rr + 0.3, zb), (uc + rr + 0.3, zb + 0.35), (uc - rr - 0.3, zb + 0.35)], cr, ol=None)

    # 뒤쪽 낮은 유적 연장(왼쪽 로브 쪽 -Y 벽 토막, 안쪽 면 없음)
    ruin = Mesh(None)
    lx0 = rects[0][0]
    for k_, (a_, b_, h_) in enumerate(((lx0 + 0.4, lx0 + 5.6, 6.0), (lx0 + 5.6, lx0 + 10.4, 10.2), (lx0 + 10.4, lx0 + 13.8, 4.8), (lx0 + 13.8, mx0, 8.6))):
        ruin.extend(m_box(a_, my0, bh, b_, my0 + 3.4, bh + h_, brick, top=wall_top))
    for (cx_, cy_, hh_) in ((lx0 + 6.0, my0 + 9.0, 2.6), (lx0 + 12.0, my0 + 14.0, 1.8), (lx0 + 4.0, my0 + 15.0, 1.2)):
        ruin.extend(m_cyl(cx_, cy_, 1.3, bh, bh + hh_, cream, n=8))
    ruin.draw(iso, lw=0.1)

    # 2a 뒤 -Y 벽(안쪽 +Y 면): 6칸, 3단(맨 위는 일부만)
    t_back = [(0.0, 6.2, 2.2, False), (10.0, 13.6, 2.0, True), (17.4, 20.2, 1.8, True)]
    h_back = [24.6, 21.0, 18.8, 23.8, 16.8, 22.4]
    arcade("Y", my0 + 4.6, mx0, mx1, 4.6, h_back, t_back, 2.2)
    # 2b -X 벽(안쪽 +X 면): 뒤 벽 안쪽 모서리부터 앞 아치 열 뒤까지 5칸
    t_side = [(0.0, 6.2, 2.1, False), (10.0, 13.6, 1.9, True)]
    h_wx = [20.0, 23.6, 15.6, 21.6, 14.4]
    arcade("X", mx0 + 3.2, my0 + 4.6, my1 - 6.0, 3.2, h_wx, t_side, 2.1)
    # 2c +X 바깥 면 낮은 2단 아케이드(여러 칸이 무너져 낮다)
    t_east = [(0.0, 4.6, 1.7, False), (8.0, 9.8, 1.7, True)]
    h_east = [12.8, 9.0, 6.8, 13.0, 7.4, 11.2]
    arcade("X", mx1, my0 + 4.6, my1 - 6.0, 3.0, h_east, t_east, 1.7)

    # 안뜰 바닥 잔해(무너져 내린 크림 돌덩이와 기둥 도막)
    deb = Mesh(None)
    for (px_, py_, sx_, sy_, hz_) in ((mx0 + 14.0, my0 + 14.0, 3.0, 2.2, 1.4), (mx0 + 20.0, my0 + 22.0, 2.2, 3.0, 0.9), (mx0 + 28.0, my0 + 12.0, 2.6, 2.0, 1.1), (mx0 + 12.0, my0 + 26.0, 2.0, 2.4, 0.8)):
        deb.extend(m_box(px_, py_, bh, px_ + sx_, py_ + sy_, bh + hz_, cream, top=cream_top))
    for (px_, py_, hz_) in ((mx0 + 22.0, my0 + 10.0, 2.2), (mx0 + 31.0, my0 + 20.0, 1.4)):
        deb.extend(m_cyl(px_, py_, 1.3, bh, bh + hz_, cream, n=8))
    deb.draw(iso, lw=0.1)

    # 3 큰 아치 열(앞 +Y 면): 키 큰 붉은 벽돌 교각 4개 + 크림 돌 기둥머리·받침·아치 띠 + 3칸 반원 아치, 윗변 폐허
    yF, dp = my1, 6.0
    npier, pw = 3, 5.2
    nb_ = npier - 1
    ow = (mx1 - mx0 - npier * pw) / float(nb_)                 # 아치 열린 폭
    r_a = ow / 2.0
    z_s = 14.6
    pier_h = [27.4, 29.0, 25.8]
    px0 = [mx0 + k * (pw + ow) for k in range(npier)]
    row = Mesh(None)
    for k in range(npier):
        a, b = px0[k], px0[k] + pw
        row.extend(m_box(a, yF - dp, bh, b, yF, bh + pier_h[k], brick, top=wall_top))
        row.extend(m_box(a - 0.45, yF - dp - 0.45, bh, b + 0.45, yF + 0.45, bh + 1.6, cream, top=cream_top))              # 받침
        row.extend(m_box(a - 0.55, yF - dp - 0.55, bh + z_s - 1.7, b + 0.55, yF + 0.55, bh + z_s, cream, top=cream_top))   # 기둥머리
        row.extend(m_box(a - 0.8, yF - dp - 0.8, bh + z_s - 0.45, b + 0.8, yF + 0.8, bh + z_s + 0.2, cream, top=cream_top))  # 주판
    row.draw(iso, lw=0.1)
    # 벽돌 줄눈(교각 앞면)
    z_ = 3.0
    while z_ < max(pier_h) - 0.5:
        for k in range(npier):
            if z_ < pier_h[k] - 0.4 and not (z_s - 1.9 < z_ < z_s + 0.5):
                face_line("Y", yF + 0.01, [(px0[k] + 0.2, z_), (px0[k] + pw - 0.2, z_)], lineY, 0.1)
        z_ += 1.8
    tops = [[(0.0, 26.4), (0.55, 26.4), (0.55, 25.6), (1.0, 25.6)],
            [(0.0, 26.0), (0.22, 26.0), (0.22, 24.9), (0.62, 24.9), (0.62, 24.0), (0.8, 24.0), (0.8, 25.2), (1.0, 25.2)]]

    def top_at(k, ua, ub, u):
        t = (u - ua) / (ub - ua)
        zz = tops[k][0][1]
        for (tt, zv) in tops[k]:
            if t >= tt - 1e-9:
                zz = zv
        return zz
    for k in range(nb_):
        ua, ub = px0[k] + pw, px0[k + 1]
        uc = (ua + ub) / 2.0
        # 아치 안쪽 면(왼쪽 반 = +X를 향해 보임)
        Fo, Bo = [], []
        for (u, z) in _bas_arch(uc, z_s, r_a, 90.0, 180.0, 10):
            Fo.append((u, yF, bh + z))
            Bo.append((u, yF - dp, bh + z))
        for i in range(len(Fo) - 1):
            iso.poly3([Fo[i], Fo[i + 1], Bo[i + 1], Bo[i]], fill=shade(xcol, 0.78), ol=None, lw=0.1)
        # 앞면 스팬드럴(아치 위 벽돌 면)
        topline = []
        nt = len(tops[k])
        for i, (tt, zv) in enumerate(tops[k]):
            topline.append((ua + (ub - ua) * tt, zv))
            nxt = tops[k][i + 1][0] if i + 1 < nt else 1.0
            topline.append((ua + (ub - ua) * nxt, zv))
        arc = _bas_arch(uc, z_s, r_a, 0.0, 180.0, 24)
        # 반시계: (ua,z_s) → 아치 호(왼쪽 → 위 → 오른쪽) → (ub,z_s) → 윗변 오른쪽에서 왼쪽
        sp = [(ua, z_s)] + [(u, z) for (u, z) in arc[::-1]] + [(ub, z_s)] + topline[::-1]
        face_poly("Y", yF + 0.005, sp, fcol, ol=None)
        # 벽돌 줄눈(스팬드럴)
        z_ = z_s + 0.9
        while z_ < 26.0:
            def okk(u, z_=z_, k=k, ua=ua, ub=ub, uc=uc):
                if z_ > top_at(k, ua, ub, u) - 1.4:
                    return False
                d = z_ - z_s
                return abs(u - uc) > math.sqrt(max(0.0, (r_a + 1.4) ** 2 - d * d)) if abs(d) < r_a + 1.4 else True
            for (a, b) in _bas_runs(ua + 0.1, ub - 0.1, 0.3, okk):
                if b - a > 0.4:
                    face_line("Y", yF + 0.01, [(a, z_), (b, z_)], lineY, 0.1)
            z_ += 1.8
        # 크림 돌 아치 띠 + 쐐기돌 줄
        outer = _bas_arch(uc, z_s, r_a + 1.4, 0.0, 180.0, 24)
        face_poly("Y", yF + 0.02, outer + arc[::-1], ccolY, ol=None)
        for a_ in range(8, 180, 10):
            ca, sa = math.cos(math.radians(a_)), math.sin(math.radians(a_))
            face_line("Y", yF + 0.03, [(uc + r_a * ca, z_s + r_a * sa), (uc + (r_a + 1.4) * ca, z_s + (r_a + 1.4) * sa)], shade(ccolY, 0.78), 0.1)
        # 윗변 크림 코니스 띠 + 마른 윗면
        for i, (tt, zv) in enumerate(tops[k]):
            nxt = tops[k][i + 1][0] if i + 1 < nt else 1.0
            a, b = ua + (ub - ua) * tt, ua + (ub - ua) * nxt
            face_poly("Y", yF + 0.02, [(a, zv - 1.0), (b, zv - 1.0), (b, zv), (a, zv)], ccolY, ol=None)
            iso.poly3([(a, yF - dp, bh + zv), (b, yF - dp, bh + zv), (b, yF, bh + zv), (a, yF, bh + zv)], fill=wall_top, ol=shade(wall_top, 0.8), lw=0.1)
    # 앞 가장자리 교각 윗면 균열 표시(폐허 느낌): 가장 낮은 교각 위 돌 두 덩이
    brk = Mesh(None)
    k_lo = pier_h.index(min(pier_h))
    brk.extend(m_box(px0[k_lo] + 0.5, yF - dp + 0.5, bh + pier_h[k_lo], px0[k_lo] + 2.4, yF - 1.4, bh + pier_h[k_lo] + 1.5, brick, top=wall_top))
    brk.draw(iso, lw=0.1)

    # 기록
    base_pts = [iso.p(r[i], r[j], z) for r in rects for i in (0, 2) for j in (1, 3) for z in (0.0, bh)]
    row_pts = [iso.p(x_, y_, bh + z_) for x_ in (mx0, mx1) for y_ in (yF - dp, yF) for z_ in (0.0, max(pier_h))]
    back_pts = [iso.p(x_, y_, bh + z_) for x_, y_, z_ in ((mx0, my0, 0.0), (mx1, my0, 0.0), (mx1, my0 + 4.6, 0.0), (mx0, my0, max(h_back)), (mx1, my0, max(h_back)),
                                                      (mx0, my1 - 6.0, 0.0), (mx0 + 3.2, my1 - 6.0, max(h_wx)))]
    add_fp("바실리카 지면", _hull(base_pts), "지면")
    add_fp("바실리카 측랑 볼트", _hull(row_pts), "대상 면")
    add_fp("바실리카 신랑 유적", _hull(back_pts), "대상 면")
    uc0 = (px0[0] + pw + px0[1]) / 2.0
    uc1 = (px0[1] + pw + px0[2]) / 2.0
    tgt = iso.p(mx1, yF - dp * 0.5, bh + pier_h[-1] - 3.6)         # 큰 아치 열 오른쪽 끝 교각 윗부분(+X 면)
    GEO["lead_tgt_막센티우스 바실리카"] = tgt
    if "막센티우스 바실리카" in SLOT:
        SLOT["막센티우스 바실리카"]["target_pt"] = [round(tgt[0], 2), round(tgt[1], 2)]
    GEO["basilica_mid_bay"] = iso.p(uc1, yF, bh + z_s + r_a + 2.2)
    all_pts = base_pts + row_pts + back_pts
    GEO["parts_L7"] = [_hull([iso.p(r[i], r[j], z) for i in (0, 2) for j in (1, 3) for z in (0.0, bh)]) for r in rects] + [_hull(row_pts), _hull(back_pts)]
    for pg in GEO["parts_L7"]:
        ex_poly(pg, 2.0)
    GEO["sil_L7"] = _hull(all_pts)
    bb = bbox_of(all_pts)
    GEO["basilica_form"] = {"bays": [{"bay": k + 1, "u": [round(px0[k] + pw, 2), round(px0[k + 1], 2)],
                                      "open_face_center": [round(v, 2) for v in iso.p((px0[k] + pw + px0[k + 1]) / 2.0, yF, bh + z_s * 0.55)]} for k in range(nb_)],
                            "arch_r_plan": round(r_a, 2), "spring_z": round(z_s, 2), "aisle_h": max(pier_h), "vault_ghost_h_max": 0.0,
                            "ghost_rule": "점선 복원 없음(d5_bas: 큰 아치 열 + 안뜰 아케이드 벽)"}
    record("L7", lm["name"], "Core(표준 랜드마크)", lm["projected_box"], bb, "큰 반원 아치 열(벽돌 교각 4·아치 3) + 안뜰을 두른 2~3단 아케이드 벽(폐허 윗변)")
