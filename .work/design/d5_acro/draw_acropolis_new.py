# 아크로폴리스 파르테논 폐허 (draw_pantheon 대체). render.py 의 'def draw_pantheon():' ~ 'def draw_metella():' 직전까지를 이 파일 내용으로 교체.
# 모든 좌표는 평면(plan) X·Y: 정면(기둥 8개 짧은 변)은 +X, 긴 변(17개)은 ±Y. 회전 없음.
def _acr_rnd(i, j=0):
    v = math.sin(i * 127.1 + j * 311.7 + 17.3) * 43758.5453
    return v - math.floor(v)


def draw_pantheon():
    L1 = LM["L1"]
    box = L1["projected_box"]
    X0, Y0 = 34.75, 15.45                 # 열주 중심 사각 (기둥 중심선: 가로 69.5 m × 세로 30.9 m)
    NX, NY = 17, 8                        # 긴 변 17, 짧은 변 8 (모서리 공유)
    ZB = 1.7                              # 스타일로베이트 윗면
    CH, EH = 10.4, 3.3                    # 기둥 높이, 엔타블러처 높이
    MAR = (226, 212, 182)                 # 대리석 베이지
    MAR_L = (240, 230, 206)
    ARCH = (214, 198, 166)
    FRIEZE = (234, 222, 194)
    ROCK = [(196, 164, 112), (214, 184, 132), (186, 154, 104), (206, 174, 122), (192, 160, 108), (220, 190, 140), (200, 168, 116)]
    # ── 바위 언덕: 위로 갈수록 조금씩 안쪽으로 들어간 직사각 슬랩을 쌓는다(층 줄무늬 + 들쭉날쭉한 절벽). 윗면은 평평한 대지.
    rock = Mesh(None)
    PX0, PX1, PY0, PY1 = -42.5, 44.0, -22.5, 23.5
    nsl = 7
    sh = 19.0 / nsl
    for k in range(nsl):
        zb = -19.0 + k * sh
        ins = 2.6 * (k) / nsl
        jx = [(_acr_rnd(k, a) - 0.5) * 4.6 for a in range(4)]
        rock.extend(m_box(PX0 + ins + jx[0], PY0 + ins + jx[1], zb, PX1 - ins + jx[2] * 1.5, PY1 - ins + jx[3] * 1.5, zb + sh + 0.02, ROCK[k % len(ROCK)], top=(206, 178, 128)))
    rock.extend(m_box(PX0, PY0, -0.9, PX1, PY1, 0.0, (214, 196, 152), top=(222, 208, 172)))
    # 앞 가장자리 바위 덩이(축 정렬 작은 직사각 기둥)
    for i, (bx, by, w, d, h) in enumerate(((38.0, 17.0, 6.0, 5.0, 2.0), (28.0, 20.5, 7.0, 3.5, 1.4), (-30.0, 20.0, 8.0, 3.5, 1.6), (40.5, -6.0, 3.5, 7.0, 1.6), (-40.0, 8.0, 3.5, 7.0, 1.3))):
        rock.extend(m_box(bx - w / 2, by - d / 2, 0, bx + w / 2, by + d / 2, h, (190, 158, 110), top=(210, 186, 140)))
    # ── 스타일로베이트 3단
    st = Mesh(None)
    for k, (m_, z0_, z1_) in enumerate(((2.8, 0.0, 0.6), (1.9, 0.6, 1.15), (1.0, 1.15, ZB))):
        st.extend(m_box(-X0 - m_, -Y0 - m_, z0_, X0 + m_, Y0 + m_, z1_, (228, 216, 188) if k != 1 else (222, 208, 178), top=(236, 226, 200)))
    # ── 기둥·엔타블러처·셀라 벽
    rn = Mesh(None)
    cols = []
    for i in range(NX):
        for (y, side) in ((-Y0, "S"), (Y0, "N")):
            cols.append((-X0 + i * 2 * X0 / (NX - 1), y, ("L", i)))
    for j in range(1, NY - 1):
        for (x, side) in ((-X0, "W"), (X0, "E")):
            cols.append((x, -Y0 + j * 2 * Y0 / (NY - 1), ("E" if x > 0 else "W", j)))
    broken = {("L", 7, +1): 5.2, ("L", 8, +1): 3.4, ("L", 9, +1): 6.5, ("L", 6, +1): 8.0, ("L", 10, +1): 4.4,
              ("L", 3, -1): 7.2, ("L", 12, -1): 6.0, ("L", 13, -1): 8.4, ("L", 1, +1): 9.0, ("L", 0, -1): 9.6,
              ("W", 2, 0): 6.4, ("W", 4, 0): 4.6, ("W", 5, 0): 8.2, ("E", 3, 0): 9.4}
    for (x, y, kk) in cols:
        sgn = 0 if kk[0] in ("E", "W") else (1 if y > 0 else -1)
        h = broken.get((kk[0], kk[1], sgn), CH)
        if kk[0] == "L" and kk[1] in (6, 7, 8, 9, 10) and y > 0 and h == CH:
            h = 6.0
        r = 0.95
        rn.extend(m_cyl(x, y, r, ZB, ZB + h, MAR, n=8, top=(214, 200, 170) if h < CH else MAR_L))
        if h >= CH:
            rn.extend(m_cyl(x, y, r, ZB + h, ZB + h + 0.55, MAR_L, n=8, k=1.22))
            rn.extend(m_box(x - 1.3, y - 1.3, ZB + h + 0.55, x + 1.3, y + 1.3, ZB + h + 1.0, MAR_L))
    zt = ZB + CH + 1.0
    # 엔타블러처: 기둥 사이 칸마다 한 덩이. 윗변이 들쭉날쭉(높이 다름), 일부 칸은 없다.
    def bay(xa, ya, xb, yb, key, along):
        r_ = _acr_rnd(*key)
        if along == "N" and 6 <= key[0] <= 9:
            return                                                   # 폭발로 날아간 가운데 칸(앞 긴 변)
        if along == "S" and 5 <= key[0] <= 11:
            return
        if along == "W" and key[0] in (2, 3, 4, 5):
            return
        eh = EH * (0.55 + 0.45 * r_) if r_ < 0.55 else EH
        w = 1.15
        if along in ("N", "S"):
            b1 = m_box(xa, ya - w, zt, xb, ya + w, zt + 1.5, ARCH)
            rn.extend(b1)
            if eh > 1.7:
                rn.extend(m_box(xa, ya - w + 0.1, zt + 1.5, xb, ya + w - 0.1, zt + eh, FRIEZE, top=MAR_L))
        else:
            b1 = m_box(xa - w, ya, zt, xa + w, yb, zt + 1.5, ARCH)
            rn.extend(b1)
            if eh > 1.7:
                rn.extend(m_box(xa - w + 0.1, ya, zt + 1.5, xa + w - 0.1, yb, zt + eh, FRIEZE, top=MAR_L))
    xs = [-X0 + i * 2 * X0 / (NX - 1) for i in range(NX)]
    ys = [-Y0 + j * 2 * Y0 / (NY - 1) for j in range(NY)]
    for i in range(NX - 1):
        bay(xs[i], Y0, xs[i + 1], Y0, (i, 1), "N")
        bay(xs[i], -Y0, xs[i + 1], -Y0, (i, 2), "S")
    for j in range(NY - 1):
        bay(X0, ys[j], X0, ys[j + 1], (j, 3), "E") if j != 99 else None
        bay(-X0, ys[j], -X0, ys[j + 1], (j, 4), "W")
    # 셀라(안쪽 신전 벽): 구간마다 높이가 다른 낮은 벽 토막
    cx0, cx1, cy0, cy1, th = -22.0, 22.0, -9.4, 9.4, 1.25
    seg = 6
    for s in range(seg):
        xa = cx0 + (cx1 - cx0) * s / seg
        xb = cx0 + (cx1 - cx0) * (s + 1) / seg
        hN = 3.0 + 7.0 * _acr_rnd(s, 9)
        hS = 4.0 + 6.0 * _acr_rnd(s, 5)
        if 2 <= s <= 3:
            hN = 1.4 + _acr_rnd(s, 2) * 1.4
        rn.extend(m_box(xa, cy1 - th, ZB, xb, cy1, ZB + hN, MAR, top=MAR_L))
        rn.extend(m_box(xa, cy0, ZB, xb, cy0 + th, ZB + hS, MAR, top=MAR_L))
    for t_ in range(4):
        ya = cy0 + (cy1 - cy0) * t_ / 4
        yb = cy0 + (cy1 - cy0) * (t_ + 1) / 4
        rn.extend(m_box(cx1 - th, ya, ZB, cx1, yb, ZB + 2.0 + 6.5 * _acr_rnd(t_, 3), MAR, top=MAR_L))
        rn.extend(m_box(cx0, ya, ZB, cx0 + th, yb, ZB + 3.0 + 7.0 * _acr_rnd(t_, 8), MAR, top=MAR_L))
    rn.extend(m_box(cx0 + 12, cy0 + 1.25, ZB, cx0 + 14, cy0 + 3.0, ZB + 2.2, MAR_L))
    # 정면 앞 흩어진 돌 조각
    rub = Mesh(None)
    for i, (bx, by, w, d, h) in enumerate(((40.0, -9.0, 2.6, 1.8, 1.0), (41.5, 4.0, 2.2, 2.6, 0.9), (38.8, 11.0, 2.8, 1.6, 0.7), (36.0, -13.5, 1.8, 1.8, 0.8), (-39.5, -3.0, 2.4, 2.0, 0.8), (-37.0, 12.0, 2.0, 2.6, 0.7))):
        rub.extend(m_box(bx - w / 2, by - d / 2, 0, bx + w / 2, by + d / 2, h, (226, 212, 184), top=(240, 230, 206)))
    for (x, y) in ((24.0, 19.5), (2.0, 19.8)):
        rub.extend(m_cyl(x, y, 1.0, 0, 2.0, MAR, n=8, top=MAR_L))
    pts = mesh_pts(rock, st, rn, rub)
    ox, oy, sc, zs, bb = fit_frame(pts, box, zs_max=1.22)
    iso = ZIso(P, ox, oy, sc, zs)
    ip = iso.p
    rock.draw(iso, lw=0.12)
    st.draw(iso, lw=0.10)
    rn.draw(iso, lw=0.10)
    rub.draw(iso, lw=0.10)
    # 엔타블러처 정면(+X) 면: 지시선 대상
    ent = [ip(X0, -Y0, zt), ip(X0, Y0, zt), ip(X0, Y0, zt + EH), ip(X0, -Y0, zt + EH)]
    ent_pts = [ip(X0 + 0.0, y_, z_) for y_ in (-Y0 * 0.9, Y0 * 0.9) for z_ in (zt + 0.3, zt + EH * 0.6)]
    GEO["pantheon_iso"] = iso
    GEO["lead_tgt_파르테논 엔타블러처"] = ip(X0, 0.0, zt + 1.7)
    GEO["pantheon_dome_ul"] = [ip(X0, y_, zt + z_) for y_ in (-10.0, -5.0, 0.0, 5.0, 10.0) for z_ in (0.6, 1.2, 1.8)]
    GEO["snap_pantheon_dome"] = list(GEO["pantheon_dome_ul"])
    add_fp("아크로폴리스 지면", _hull([ip(X, Y, Z) for X in (PX0, PX1) for Y in (PY0, PY1) for Z in (-0.9, 0)]), "지면")
    add_fp("파르테논 엔타블러처", _hull(ent_pts + ent), "대상 면")
    add_fp("아크로폴리스 암반", _hull([ip(X, Y, Z) for X in (PX0, PX1) for Y in (PY0, PY1) for Z in (-19.0, -0.9)]), "대상 면")
    hullp = _hull([ip(*q) for q in pts])
    GEO["sil_L1"] = hullp
    GEO["parts_L1"] = [hullp]
    record("L1", L1["name"], "Core(표준 랜드마크)", box, bb, "높이 과장 %.2f배" % zs)


