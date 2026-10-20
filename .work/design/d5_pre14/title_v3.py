"""타이틀부 v3: 베를린식 신전 정면 틀 + 로마 비문 계열 세리프 대형 제목 + 파리식 부제(양옆 가는 줄) + 박공 안 시리즈 줄 + SPQR 명판.
render.py 의 draw_title() 이 draw(globals()) 로 부른다. 지면에는 띠 y 3~91, x 126.5~293.5 만 쓴다."""
from PIL import ImageFont

SERIF = "/System/Library/Fonts/Palatino.ttc"      # 로마 비문 대문자 계열(르네상스 로마 대문자 기원). 굵은체 = index 2
SERIF_IDX = 2
_RATIO = {}


def _f(px):
    return ImageFont.truetype(SERIF, px, index=SERIF_IDX)


def _ratio():
    if "H" not in _RATIO:
        f = _f(1000)
        b = f.getbbox("H", anchor="ls")
        _RATIO["H"] = (b[3] - b[1]) / 1000.0
    return _RATIO["H"]


def draw(G):
    P, KD, ACC = G["P"], G["KD"], G["ACCENT"]
    rec_text, box_poly = G["rec_text"], G["box_poly"]
    ptext = G["ptext"]
    pr = G["FR"]["title"].get("print") or ["CITY LANDMARK INFOGRAPHICS · ROMA", "ROMAN CONCRETE", "로마 콘크리트", "로마 건축물로 읽는 로마 콘크리트"]
    _band, main_t, sub_t, line_t = (pr + [""] * 4)[:4]
    X0, X1 = 126.5, 293.5
    Y0, Y1 = 3.0, 91.0
    cx = (X0 + X1) / 2.0
    red = ACC
    STONE = (250, 240, 222)       # 트라버틴(바탕 위 신전 돌색)
    STONE_D = (238, 222, 194)
    TYMP = (240, 218, 190)        # 박공 안
    SHADE = (222, 196, 160)

    def tracked(x, y, s, px_em, track, col, anchor="c", role="", shadow=None, rec=True, layer="타이틀"):
        """글자 사이 track(mm)을 더한 대문자 조판. (x 는 anchor 기준) 외곽 상자를 돌려준다."""
        f = _f(max(6, int(round(px_em * KD))))
        em = f.size / KD
        adv = [f.getlength(c) / KD for c in s]
        w = sum(adv) + track * (len(s) - 1)
        xs = x - w / 2.0 if anchor == "c" else x
        if shadow:
            xx = xs
            for c, a in zip(s, adv):
                P.text(xx + shadow[0], y + shadow[1], c, f, shadow[2], anchor="ls")
                xx += a + track
        xx = xs
        for c, a in zip(s, adv):
            P.text(xx, y, c, f, col, anchor="ls")
            xx += a + track
        fa = em * _ratio()
        box = (xs, y - fa, xs + w, y + 0.12 * em * 0.0)
        if rec:
            rec_text(s, role, "en", em, fa, box_poly(box), layer)
        return box, fa

    def em_for_cap(cap):
        return cap / _ratio()

    # ── 계단(기단) ──
    for i, (inset, top) in enumerate(((0.0, Y1 - 8.0), (2.2, Y1 - 5.4), (4.4, Y1 - 2.7))):
        P.rect(X0 + inset, top, X1 - inset, top + (2.7 if i < 2 else 2.7), fill=(STONE if i != 1 else STONE_D), outline=red, lw=0.4)
    # ── 기둥(좌우 두 쌍) ──
    by0, by1 = Y0 + 30.0, Y1 - 8.0
    cols = [X0 + 5.5, X0 + 14.5, X1 - 14.5, X1 - 5.5]
    for x in cols:
        P.rect(x - 3.3, by1 - 2.2, x + 3.3, by1, fill=STONE_D, outline=red, lw=0.3)          # 주초
        P.rect(x - 2.4, by0 + 2.4, x + 2.4, by1 - 2.2, fill=STONE, outline=red, lw=0.35)       # 기둥 몸
        for dx in (-1.0, 0.0, 1.0):
            P.line([(x + dx, by0 + 3.4), (x + dx, by1 - 3.2)], (226, 176, 170), 0.16, joint=False)   # 플루팅
        P.rect(x - 3.6, by0 + 0.8, x + 3.6, by0 + 2.4, fill=STONE_D, outline=red, lw=0.3)     # 주두 하단
        P.rect(x - 4.2, by0, x + 4.2, by0 + 0.8, fill=STONE, outline=red, lw=0.3)             # 주두 상단
    # ── 엔타블러처(처마 띠) ──
    P.rect(X0 + 1.0, Y0 + 24.0, X1 - 1.0, Y0 + 30.0, fill=STONE_D, outline=red, lw=0.5)
    P.rect(X0 + 1.0, Y0 + 24.0, X1 - 1.0, Y0 + 25.5, fill=STONE, outline=red, lw=0.3)
    n_t = 33
    for i in range(n_t):
        x = X0 + 4.0 + i * (X1 - X0 - 8.0) / (n_t - 1)
        P.line([(x, Y0 + 26.6), (x, Y0 + 29.0)], (206, 120, 120), 0.25, joint=False)           # 프리즈 홈줄
    # ── 박공 ──
    P.poly([(X0 + 1.0, Y0 + 24.0), (cx, Y0 + 0.6), (X1 - 1.0, Y0 + 24.0)], fill=STONE, outline=red, lw=0.6)
    P.poly([(X0 + 8.0, Y0 + 22.4), (cx, Y0 + 5.0), (X1 - 8.0, Y0 + 22.4)], fill=TYMP, outline=(226, 150, 150), lw=0.3)
    # SPQR 명판(꼭대기에 붙은 작은 붉은 판 — 바탕 위에 직접 얹은 색 판)
    P.rect(cx - 9.5, Y0 + 7.6, cx + 9.5, Y0 + 14.4, fill=red)
    tracked(cx, Y0 + 12.6, "SPQR", em_for_cap(3.6), 0.9, (252, 240, 224), role="title_plaque")
    # 시리즈 줄(박공 안)
    tracked(cx, Y0 + 20.6, "CITY LANDMARK INFOGRAPHICS", em_for_cap(2.7), 0.62, red, role="title_series")
    # ── 큰 제목 ──
    title = "ROMA"
    cap = 24.0
    track = 0.8
    em = em_for_cap(cap)
    _, _ = None, None
    box, fa = tracked(cx, Y0 + 58.5, title, em, track, red, role="title_main", shadow=(0.7, 0.7, SHADE))
    # ── 부제(파리식: 굵은 대문자 + 양옆 가는 줄) ──
    if main_t:
        sbox, sfa = tracked(cx, Y0 + 67.4, main_t, em_for_cap(4.4), 1.4, red, role="title_sub")
        ym = Y0 + 67.4 - sfa / 2.0
        P.line([(sbox[0] - 14.0, ym), (sbox[0] - 3.0, ym)], red, 0.4, joint=False)
        P.line([(sbox[2] + 3.0, ym), (sbox[2] + 14.0, ym)], red, 0.4, joint=False)
    ko = (sub_t + " · " + line_t) if (sub_t and line_t) else (sub_t or line_t)
    if ko:
        ptext(cx, Y0 + 74.6, ko, "b", 2.9, red, "title_line", anchor="c", layer="타이틀")
    return {"title_w": round(box[2] - box[0], 1), "title_cap": round(fa, 2)}
