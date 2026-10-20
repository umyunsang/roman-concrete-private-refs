# 막센티우스 바실리카 도면 판(plate) 새·바뀐 함수 전체 본문. 원본 d5 로 가져갈 때 같은 이름 함수를 통째로 교체(없으면 추가).

# ===== zoom_figs_B.py : 파일 끝에 추가(상수 PAPER·INKD·INKL·PLATE_SUB, _hatch, fig_basilica_plate) =====
# ──────────────────────────────────────────────────────────────
# 2b) 막센티우스 바실리카 — 도면 판(복원 평면 + 축척 막대·방위표 + 바깥 입면). 교과서 Fig.113 의 도면 형식.
#     d=40 정사각 자리 가운데에 34×40 mm 판. sub(0~62)의 단위 1 = 0.688 mm. 판 = sub 의 PLATE_SUB 사각형.
#     구조는 지도의 Core 바실리카(render.py draw_basilica)와 같다: 앞(+Y, 평면 아래쪽) 큰 아치 열(교각 3·반원 아치 2) + 안뜰을 두른 아케이드 벽.
#     평면 비율 100×65 m(Basic-대체 조사 L437). 글자는 축척 숫자 0·25·50 과 N 뿐.
# ──────────────────────────────────────────────────────────────
PAPER = (250, 244, 232)
INKD = (58, 42, 28)
INKL = (150, 130, 106)
PLATE_SUB = (6.3, 1.9, 55.7, 60.1)


def _hatch(L, x0, y0, x1, y1, sp, col, lw):
    """사각형 안 45° 빗금(오른쪽 위로 올라가는 선), 간격 sp"""
    h = y1 - y0
    k = x0 - h
    while k < x1:
        xa, ya = k, y1
        xb, yb = k + h, y0
        if xa < x0:
            ya -= (x0 - xa)
            xa = x0
        if xb > x1:
            yb += (xb - x1)
            xb = x1
        if ya > yb + 1e-6 and xb > xa:
            L.line([(xa, ya), (xb, yb)], col, lw, joint=False)
        k += sp
    return


def fig_basilica_plate(sub, vc, vr, rng):
    L = sub
    px0, py0, px1, py1 = PLATE_SUB
    L.rect(px0, py0, px1, py1, fill=PAPER)
    W, W2, W3 = 0.52, 0.40, 0.34                  # 주선 / 보조선 / 빗금·점선 (최종 약 0.36 / 0.28 / 0.23 mm)

    def ln(pts, lw=W, col=INKD):
        L.line(pts, col, lw, joint=True)

    def box(x0, y0, x1, y1, lw=W, fill=None):
        if fill:
            L.rect(x0, y0, x1, y1, fill=fill)
        ln([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], lw)

    # ── (a) 복원 평면도 ─────────────────────────────
    X0, X1, Y0, Y1 = 11.0, 51.0, 4.5, 30.5         # 100×65 m 를 0.4 단위/m 로
    TW = 1.8                                       # 벽 두께
    PW_, OW = 5.0, 12.5                            # 앞 교각 폭 · 아치 열린 폭 (입면과 같은 칸)
    DY = 3.4                                       # 앞 교각 깊이
    yf0 = Y1 - DY
    # 뒤·좌·우 벽(빗금 단면)
    for (a, b, c, d) in ((X0, Y0, X1, Y0 + TW), (X0, Y0 + TW, X0 + TW, yf0), (X1 - TW, Y0 + TW, X1, yf0)):
        L.rect(a, b, c, d, fill=(244, 236, 220))
        _hatch(L, a, b, c, d, 1.15, INKD, W3)
        box(a, b, c, d, W2)
    # 아케이드 교각(안쪽으로 튀어나온 부벽): 뒤 벽 7개, 좌우 벽 6개
    for i in range(7):
        x = X0 + i * (X1 - X0 - 1.8) / 6.0
        box(x, Y0 + TW, x + 1.8, Y0 + TW + 1.1, W2, fill=(240, 230, 212))
    for i in range(6):
        y = Y0 + TW + 1.1 + i * (yf0 - Y0 - TW - 1.1 - 1.8) / 5.0
        box(X0 + TW, y, X0 + TW + 1.1, y + 1.8, W2, fill=(240, 230, 212))
        box(X1 - TW - 1.1, y, X1 - TW, y + 1.8, W2, fill=(240, 230, 212))
    # 앞 큰 아치 열: 교각 3 (빗금 단면) + 아치 문턱선(점선)
    for k in range(3):
        a = X0 + k * (PW_ + OW)
        box(a, yf0, a + PW_, Y1, W, fill=(244, 236, 220))
        _hatch(L, a, yf0, a + PW_, Y1, 1.15, INKD, W3)
        box(a, yf0, a + PW_, Y1, W)
    for k in range(2):
        a = X0 + PW_ + k * (PW_ + OW)
        L.dashed((a, yf0 + DY / 2), (a + OW, yf0 + DY / 2), INKD, W3, dash=1.0, gap=0.8)
    # 층 표시: 위 층이 물러선 선(점선 2겹)
    for off in (3.1, 4.1):
        x0_, x1_, y0_, y1_ = X0 + off, X1 - off, Y0 + TW + off - 0.4, yf0 - 0.5
        L.dashed_rect(x0_, y0_, x1_, y1_, INKL, W3, dash=1.0, gap=0.9)
    # 안뜰 바닥: 포장 십자 표시와 무너진 돌덩이·기둥 도막
    for gx in range(0, 7):
        for gy in range(0, 4):
            x, y = X0 + 7.5 + gx * 4.2, Y0 + 8.4 + gy * 3.8
            L.line([(x - 0.35, y), (x + 0.35, y)], INKL, 0.22, joint=False)
            L.line([(x, y - 0.35), (x, y + 0.35)], INKL, 0.22, joint=False)
    for (cx_, cy_) in ((22.0, 15.0), (31.0, 19.5), (40.0, 14.0)):
        L.ell(cx_, cy_, 0.95, 0.95, fill=PAPER, outline=INKD, lw=W2)
        L.ell(cx_, cy_, 0.35, 0.35, outline=INKD, lw=0.3)
    for (a, b, c, d) in ((26.5, 22.0, 28.6, 23.4), (35.5, 11.8, 37.2, 13.0)):
        box(a, b, c, d, W2, fill=PAPER)
    # 바깥 외곽 한 번 더
    ln([(X0, Y0), (X1, Y0), (X1, yf0), (X1, Y1), (X0, Y1), (X0, Y0)], W)

    # ── 축척 막대 0–25–50 m 와 방위표 N ───────────────
    sx, sy = X0, 35.4
    bl = 20.0                                       # 50 m = 20 단위
    L.rect(sx, sy, sx + bl / 2, sy + 1.1, fill=INKD)
    box(sx + bl / 2, sy, sx + bl, sy + 1.1, W2, fill=PAPER)
    box(sx, sy, sx + bl / 2, sy + 1.1, W2)
    for xx in (0.0, bl / 2, bl):
        ln([(sx + xx, sy - 0.8), (sx + xx, sy + 1.1)], W2)
    fs = fnt("m", 2.9)
    for xx, s_ in ((0.0, "0"), (bl / 2, "25"), (bl, "50")):
        L.text(sx + xx, sy - 1.3, s_, fs, INKD, anchor="ms")
    nx, ny = 48.0, 36.6                             # 방위표: 화살표(왼쪽 반 칠함) + N
    ln([(nx, ny), (nx, ny - 4.6)], W2)
    L.poly([(nx, ny - 5.2), (nx - 1.1, ny - 2.8), (nx, ny - 3.4)], fill=INKD)
    L.poly([(nx, ny - 5.2), (nx + 1.1, ny - 2.8), (nx, ny - 3.4)], fill=PAPER, outline=INKD, lw=0.3)
    L.text(nx + 2.8, ny - 2.4, "N", fnt("b", 3.0), INKD, anchor="ms")

    # ── (b) 바깥 입면도: 큰 아치 열 정면 2칸 ───────────
    G = 57.8                                        # 땅선
    zs = G - 9.0                                    # 아치 스프링 높이
    ra = OW / 2.0
    rv = 1.0                                        # 홍예 쐐기 띠 폭
    ctop = 41.0                                     # 처마 띠 아래
    ln([(X0 - 1.5, G), (X1 + 1.5, G)], 0.7)
    # 교각
    for k in range(3):
        a = X0 + k * (PW_ + OW)
        b = a + PW_
        L.rect(a, ctop, b, G, fill=PAPER)
        ln([(a, G), (a, ctop)], W)
        ln([(b, G), (b, ctop)], W)
        # 받침(두 단) · 기둥머리(주두) 두 단
        box(a - 0.45, G - 1.2, b + 0.45, G, W2)
        box(a - 0.6, zs - 1.7, b + 0.6, zs - 0.8, W2)
        box(a - 0.9, zs - 0.8, b + 0.9, zs + 0.15, W2)
        # 그늘 빗금(오른쪽 1.4)과 벽돌 줄 일부
        _hatch(L, b - 1.5, ctop + 0.2, b - 0.05, zs - 1.8, 0.8, INKD, W3)
        _hatch(L, b - 1.5, zs + 0.3, b - 0.05, G - 1.3, 0.8, INKD, W3)
        yy = ctop + 1.6
        while yy < G - 1.5:
            if not (zs - 1.9 < yy < zs + 0.3):
                ln([(a + 0.3, yy), (a + 2.6, yy)], 0.22, INKL)
            yy += 1.7
    # 아치 2칸: 안쪽 선 · 홍예 쐐기 · 안쪽 그늘(왼쪽 반)
    for k in range(2):
        ua = X0 + PW_ + k * (PW_ + OW)
        uc = ua + ra
        n = 40
        inner = [(uc - ra * math.cos(math.pi * i / n), zs - ra * math.sin(math.pi * i / n)) for i in range(n + 1)]
        outer = [(uc - (ra + rv) * math.cos(math.pi * i / n), zs - (ra + rv) * math.sin(math.pi * i / n)) for i in range(n + 1)]
        ln([(ua, zs)] + inner[1:-1] + [(ua + OW, zs)], W)
        ln(outer, W2)
        for a_ in range(12, 180, 12):
            ca, sa = math.cos(math.radians(a_)), math.sin(math.radians(a_))
            ln([(uc + ra * ca, zs - ra * sa), (uc + (ra + rv) * ca, zs - (ra + rv) * sa)], 0.3)
        for a_ in range(95, 180, 7):                # 안쪽 면(깊이) 그늘 방사 빗금
            ca, sa = math.cos(math.radians(a_)), math.sin(math.radians(a_))
            ln([(uc + ra * ca, zs - ra * sa), (uc + (ra - 0.9) * ca, zs - (ra - 0.9) * sa)], 0.22)
        # 스팬드럴(아치 위) 벽돌 줄
        yy = ctop + 1.5
        while yy < zs - 1.0:
            xs_ = [x for x in (ua + 0.3 + j * 0.2 for j in range(int(OW / 0.2))) if (x - uc) ** 2 + (yy - zs) ** 2 > (ra + rv + 0.5) ** 2 and (yy < zs - ra - rv - 0.5 or abs(x - uc) > ra + rv + 0.5)]
            if xs_:
                ln([(min(xs_), yy), (min(xs_) + 1.4, yy)], 0.22, INKL)
                ln([(max(xs_) - 1.4, yy), (max(xs_), yy)], 0.22, INKL)
            yy += 1.7
    # 처마 띠(코니스): 두 줄 + 이빨 장식(덴틸) + 위로 들쭉날쭉한 폐허 윗변
    xa, xb = X0 - 0.6, X1 + 0.6
    L.rect(xa, ctop - 1.1, xb, ctop, fill=PAPER)
    ln([(xa, ctop), (xb, ctop)], W)
    ln([(xa, ctop - 1.1), (xb, ctop - 1.1)], W)
    ln([(xa, ctop - 0.45), (xb, ctop - 0.45)], 0.22)
    x = xa + 0.4
    while x < xb - 0.2:
        ln([(x, ctop - 0.45), (x, ctop)], 0.22)
        x += 0.8
    tops_ = {0: (1.5, 0.6, 1.2), 1: (0.9, 1.6, 0.5), 2: (1.3, 0.7, 1.6)}
    for k in range(3):
        a = X0 + k * (PW_ + OW)
        h1, h2, h3 = tops_[k]
        ln([(a, ctop - 1.1), (a, ctop - 1.1 - h1), (a + PW_ * 0.35, ctop - 1.1 - h1), (a + PW_ * 0.35, ctop - 1.1 - h2),
            (a + PW_ * 0.7, ctop - 1.1 - h2), (a + PW_ * 0.7, ctop - 1.1 - h3), (a + PW_, ctop - 1.1 - h3), (a + PW_, ctop - 1.1)], W2)

# ===== render.py : _win_half(신규) + _window_box(교체) =====
def _win_half(w):
    """창 반폭·반높이(mm): 원 = d/2 두 개, 판(plate) = plate_wh/2"""
    if w.get("shape") == "plate":
        return w["plate_wh"][0] / 2.0, w["plate_wh"][1] / 2.0
    return w["d"] / 2.0, w["d"] / 2.0

def _window_box(w):
    cx, cy = w["c"]
    hw, hh = _win_half(w)
    tf = _win_tf(w)
    tw, th = 38.0 * tf, 18.5 * tf
    side = w.get("side", "below")
    if side == "right":
        return [cx - hw - 1.0, cy - hh - 1.0, cx + hw + 3.0 + tw, cy + hh + 1.0]
    if side == "left":
        return [cx - hw - 3.0 - tw, cy - hh - 1.0, cx + hw + 1.0, cy + hh + 1.0]
    if side == "above":
        return [cx - max(hw + 1.0, tw / 2.0), cy - hh - th, cx + max(hw + 1.0, tw / 2.0), cy + hh + 1.0]
    return [cx - max(hw + 1.0, tw / 2.0), cy - hh - 1.0, cx + max(hw + 1.0, tw / 2.0), cy + hh + th]

# ===== render.py : auto_place_all 은 길어서 바뀐 3줄만 =====
# render.py:4837
# bx = _window_box({"c": (0.0, 0.0), "d": w["d"], "side": side, "shape": w.get("shape"), "plate_wh": w.get("plate_wh")})   # 중심 (0,0) 기준 상자
# render.py:4841
# f_ring, rwp, rhp = free_map(st_r, *((w["plate_wh"][0], w["plate_wh"][1]) if w.get("shape") == "plate" else (2 * r, 2 * r)), 0, 0)
# render.py:4900
# bx = _window_box({"c": (0.0, 0.0), "d": w["d"], "side": side, "shape": w.get("shape"), "plate_wh": w.get("plate_wh")})

# ===== render.py : draw_detail_windows (전체 교체) =====
def draw_detail_windows():
    """Core 건물 곁 Detail: 원 안 확대 단면(zoom_figs_*.py) + 주황 테 + 지시선 + 제목 1줄·본문 2줄 + 수치 칩(Support)."""
    import importlib
    import random as _rnd
    try:
        import v2_windows as _W
    except Exception as e_:                                          # noqa: BLE001
        REPORT["notes"].append("확대 창 자료 없음: %s" % e_)
        return
    mods = []
    for t_ in "ABCD":
        try:
            mods.append(importlib.import_module("zoom_figs_" + t_))
        except Exception as e_:                                      # noqa: BLE001
            REPORT["notes"].append("확대 창 그림 모듈 %s 못 읽음: %s" % (t_, e_))
    DRAWN["detail_windows"] = []
    for w in _W.DETAIL_WINDOWS:
        if w.get("reserved"):
            DRAWN["detail_windows"].append({"key": w["key"], "rank": w["rank"], "c": list(w["c"]), "d": w["d"], "reserved": True})
            continue
        fn = next((getattr(m, "fig_" + w["fig"]) for m in mods if hasattr(m, "fig_" + w["fig"])), None)
        (cx, cy), d = w["c"], w["d"]
        r = d / 2.0
        if fn is None:
            REPORT["notes"].append("확대 창 그림 함수 없음: fig_%s" % w["fig"])
            continue
        vc, vr = 31.0, 30.0
        sub = Layer(0, 0, 62, 62)
        fn(sub, vc, vr, _rnd.Random(w["key"]))
        plate = w.get("shape") == "plate"
        hw, hh = _win_half(w)
        if not plate:
            mask = Image.new("L", (sub.w, sub.h), 0)
            ImageDraw.Draw(mask).ellipse([sub.X(vc - vr), sub.Y(vc - vr), sub.X(vc + vr), sub.Y(vc + vr)], fill=255)
            sub.img.putalpha(ImageChops.multiply(sub.img.getchannel("A"), mask))
        k = d / 60.0
        tgt = Layer(cx - r - k, cy - r - k, cx + r + k, cy + r + k)
        tgt.img = sub.img.resize((tgt.w, tgt.h), Image.LANCZOS)
        tgt.d = ImageDraw.Draw(tgt.img)
        P.paste(tgt)
        if plate:                                                    # 도면 판: 직사각형 주황 테(다른 확대 창과 같은 색·두께)
            P.rect(cx - hw, cy - hh, cx + hw, cy + hh, outline=_W.ORANGE, lw=0.9)
        else:
            P.ell(cx, cy, r, r, outline=_W.ORANGE, lw=0.9)
        tx, ty = w["t"]
        dist = math.hypot(tx - cx, ty - cy)
        pth = w.get("path")
        if pth and len(pth) >= 2 and dist > r + 1.5:
            # 꺾은선이 원(판이면 직사각형) 가장자리를 벗어나는 첫 점에서 시작한다(안쪽은 자른다)
            def _ins(p_):
                return (abs(p_[0] - cx) <= hw and abs(p_[1] - cy) <= hh) if plate else math.hypot(p_[0] - cx, p_[1] - cy) <= r
            pl = None
            for q0, q1 in zip(pth[:-1], pth[1:]):
                if _ins(q1):
                    continue
                if not _ins(q0):
                    ex = tuple(q0)
                else:
                    lo, hi = 0.0, 1.0
                    for _ in range(30):
                        mm = (lo + hi) / 2.0
                        pm = (q0[0] + (q1[0] - q0[0]) * mm, q0[1] + (q1[1] - q0[1]) * mm)
                        if _ins(pm):
                            lo = mm
                        else:
                            hi = mm
                    ex = (q0[0] + (q1[0] - q0[0]) * hi, q0[1] + (q1[1] - q0[1]) * hi)
                rest = [tuple(q) for q in pth[pth.index(q1):]] if q1 in pth else [tuple(q1)]
                pl = [ex] + rest
                break
            if pl is None:
                pl = [(cx, cy), (tx, ty)]
            P.line(pl, _W.ORANGE, 0.35, joint=False)
            P.dot(tx, ty, 0.5, _W.ORANGE)
            w["leader_pts"] = [[round(q[0], 2), round(q[1], 2)] for q in pl]
        side = w.get("side", "below")
        chip = w.get("chip")
        tf = _win_tf(w)
        st_ = 3.9 * tf
        if side == "below":
            tx0, anc, y0 = cx, "c", cy + hh + 4.2 * tf
        elif side == "right":
            tx0, anc, y0 = cx + hw + 3.0, "l", cy - 5.5 * tf
        elif side == "above":
            tx0, anc, y0 = cx, "c", cy - hh - 14.8 * tf
        else:
            tx0, anc, y0 = cx - hw - 3.0, "r", cy - 5.5 * tf
        ptext(tx0, y0, w["title"], "b", 3.0 * tf, INK_L, "caption", anchor=anc, layer="확대 창 " + w["key"], panel="MAP")
        for i_, ln in enumerate(w["lines"][:2]):
            ptext(tx0, y0 + st_ * (i_ + 1), ln, "m", 2.5 * tf, INK_L, "caption", anchor=anc, layer="확대 창 " + w["key"], panel="MAP")
        if chip:
            yc = y0 + st_ * 3 + 1.0
            wch = max(14.0, 2.35 * tf * len(chip) * 0.62 + 4.0)
            xa = tx0 - wch / 2.0 if anc == "c" else (tx0 if anc == "l" else tx0 - wch)
            P.rect(xa, yc - 3.2 * tf, xa + wch, yc + 1.0, fill=(250, 238, 214), outline=_W.ORANGE, lw=0.25)
            ptext(xa + wch / 2.0, yc, chip, "m", 2.3 * tf, INK_L, "caption", anchor="c", layer="확대 창 " + w["key"], panel="MAP")
        DRAWN["detail_windows"].append({"key": w["key"], "rank": w["rank"], "c": [cx, cy], "d": d, "target": [tx, ty],
                                        "leader_mm": round(max(0.0, dist - r), 1), "leader_pts": w.get("leader_pts"), "title": w["title"], "lines": w["lines"][:2], "chip": chip})
