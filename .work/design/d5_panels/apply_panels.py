# -*- coding: utf-8 -*-
"""위·아래 띠 Basic 패널 위계 재배치(사용자 2026-10-19 19:36~19:39)를 대상 폴더에 멱등 적용한다.
사용: python3 apply_panels.py <설계 폴더(d5 등)>
- 지도(중앙) 코드·LAYOUT_SHIFT·LABELS·강·건물 좌표는 건드리지 않는다. 패널 사양(v2_panels.py PANELS·DETAILS Z1)과
  render.py의 chapter_header·draw_panel_L·draw_panel_B·draw_panel_D·draw_panel_P5, v2_check.py 글자면 허용 범위, v2_text.py P8 설명만 바꾼다.
- 이미 적용된 곳은 '이미 적용'으로 세고 건너뛴다. 치환 대상이 없으면 '경고'로 세고 그 항목만 건너뛴다.
"""
import os
import re
import sys

MARK = "panels-v2"
APPLIED, WARNED, SKIPPED = [], [], []


def _read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def _write(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)


def sub_once(src, old, new, label, done_marker=None):
    """old 문자열 하나를 new로 바꾼다. new(또는 done_marker)가 이미 있으면 건너뛴다. old가 없으면 경고"""
    if (done_marker and done_marker in src) or (new in src and old not in src):
        SKIPPED.append(label)
        return src
    if old not in src:
        WARNED.append(label + " (치환 대상 문자열 없음)")
        return src
    APPLIED.append(label)
    return src.replace(old, new, 1)


def replace_func(src, name, new_code, label):
    """최상위 def name(...)부터 다음 최상위 문(빈 줄 둘 뒤 첫 글자)까지를 new_code로 바꾼다. 본문에 MARK가 있으면 이미 적용"""
    m = re.search(r"^def %s\(" % re.escape(name), src, re.M)
    if not m:
        WARNED.append(label + " (함수 %s 없음)" % name)
        return src
    nxt = re.search(r"\n\n\n(?=\S)", src[m.end():])
    end = m.end() + nxt.start() if nxt else len(src)
    old = src[m.start():end]
    if MARK in old:
        SKIPPED.append(label)
        return src
    APPLIED.append(label)
    return src[:m.start()] + new_code.strip("\n") + src[end:]


# ═════════════════════════════════ render.py 새 함수 ═════════════════════════════════
NEW_CHAPTER_HEADER = r'''def chapter_header(pid, n, en, ko, x0, x1, yb, en_x=None, ko_baseline=None, en_face=None, badge_d=None):
    # panels-v2: 장 머리글 + 제목 글자면(en_face)·배지 지름(badge_d)을 패널마다 다르게 줄 수 있다(Basic 위계: ❶ 8.4 > ❹ 7.6 > ❷ 7.0 > ❺ 6.6 > ❻ 6.2)
    """장 머리글: 배지(영문 제목 왼쪽, 제목 대문자 높이 가운데) + 영문 제목(기본 7.0) + 국문 장 질문 부제 2.8(영문 옆, 넘치면 아랫줄 왼쪽 맞춤)"""
    lay = "패널 " + pid
    ef = float(en_face) if en_face else CH_EN
    bd = float(badge_d) if badge_d else 10.0
    fe = fface("en", ef, en)[2]
    chapter_badge(n, x0 + bd / 2.0, yb - fe / 2.0, d=bd, layer=lay)
    ex = en_x if en_x is not None else x0 + bd / 2.0 + 7.5
    box, fa = ptext(ex, yb, en, "en", ef, ACCENT, "head_en", layer=lay, panel=pid)
    if not ko or ko == en:   # 사용자 17:28·17:29: 부제가 제목과 뜻이 겹치면 둘 중 하나만
        return yb, None
    kw = twf(ko, "b", CH_KO)
    if box[2] + 2.0 + kw <= x1 + 0.01 and ko_baseline is None:
        ptext(box[2] + 2.0, yb, ko, "b", CH_KO, ACCENT, "subtitle", layer=lay, panel=pid)
        return yb, None
    kb = ko_baseline if ko_baseline is not None else yb + 1.8 + fface("b", CH_KO, ko)[2]
    ptext(ex, kb, ko, "b", CH_KO, ACCENT, "subtitle", layer=lay, panel=pid)
    return yb, kb
'''

NEW_BADGE = r'''def chapter_badge(n, cx, cy, d=10.0, layer="장 배지"):
    # panels-v2: 숫자 글자면을 배지 지름에 비례(Ø10 → 5.6)
    """장 배지: 원을 로마 콘크리트란? 제목색(ACCENT)으로 채우고 흰 숫자. 모든 장이 같은 모양"""
    r = d / 2.0
    P.ell(cx, cy, r, r, fill=ACCENT)
    f, em, fa = fface("b", 5.6 * d / 10.0, str(n))
    yb = cy + fa / 2.0
    P.text(cx, yb, str(n), f, (255, 255, 255), anchor="ms")
    bb = f.getbbox(str(n), anchor="ms")
    rec_text(str(n), "badge", "b", em, fa, box_poly((cx + bb[0] / KD, yb + bb[1] / KD, cx + bb[2] / KD, yb + bb[3] / KD)), layer)
    DRAWN["texts"][-1].update({"chapter_badge": int(n), "c": [round(cx, 2), round(cy, 2)], "d": d})
    DRAWN.setdefault("badges", []).append({"n": int(n), "c": [round(cx, 2), round(cy, 2)], "d": d, "ink": list(ACCENT), "layer": layer})
'''

NEW_L = r'''def draw_panel_L():
    # panels-v2: ❶ 로마 콘크리트란? = Basic 1순위(제목 8.4 · 정의 3.0 · 재료 그림 ×1.7 · 이름 3.2 · 설명 2.4). 칸·글 자리는 사양 rect·head에서 읽는다
    pn = PANEL["L"]
    x0, y0, x1, y1 = pn["rect"]
    lay = "패널 L"
    hd = pn.get("head") or {}
    bd = (hd.get("badge") or {}).get("d")
    yb, kb = chapter_header("L", 1, "ROMAN CONCRETE?", hd.get("ko", "무엇으로 만들었나"), x0, x1, float(hd.get("en_baseline_y", y0 + 12.5)), en_x=hd.get("en_x"),
                            en_face=hd.get("en_face"), badge_d=bd)
    ydef = (kb + 6.2) if kb else (yb + 9.0)
    defs = ["생석회와 화산재가 물과 반응해 굳는 반죽에", "돌·벽돌 조각(골재)을 다져 넣은 로마 건축 재료.", "돔·볼트·방파제에 쓰였고 철근은 쓰지 않았다."]
    draw_lines(x0 + 0.6, ydef, wrap_all(defs, "m", 3.0, x1 - x0 - 1.2), "m", 3.0, INK_L, "body", 3.9, lay)
    items = [("생석회", ["석회암을 구운 것"]), ("화산재", ["시내 = 알바노 구릉", "바다 = 포추올리"]),
             ("골재", ["응회암·벽돌·", "경석 조각"]), ("물", ["육상 = 민물", "바다 공사 = 바닷물"])]
    isc = float(hd.get("icon_scale", 1.5))
    for i, (name, sub) in enumerate(items):
        cx = x0 + 14.0 + i * float(hd.get("icon_pitch", 27.0))
        iso = ZIso(P, cx, y0 + float(hd.get("icon_oy", 54.5)), sc=isc)
        m = Mesh(None)
        if i == 0:
            m.extend(m_mound(0, 0, 0, 4.6, 4.2, LIME_W, key="L석회"))
            m.extend(m_box(3.2, 2.0, 0, 5.2, 4.0, 1.6, (240, 238, 228), top=(250, 250, 244)))
            m.extend(m_box(-4.6, 1.0, 0, -2.8, 2.8, 1.4, (240, 238, 228), top=(250, 250, 244)))
        elif i == 1:
            m.extend(m_mound(-2.4, 0.5, 0, 3.6, 3.4, ASH_R, key="L화산재1"))
            m.extend(m_mound(3.2, -0.5, 0, 3.4, 3.0, ASH_G, key="L화산재2"))
        elif i == 2:
            for k, (X, Y, c) in enumerate(((-3, 0, (168, 136, 104)), (0, 2.5, (186, 104, 78)), (2.6, -1.6, (150, 146, 138)), (-0.5, -3, (204, 196, 170)), (3.6, 2.4, (176, 140, 108)))):
                m.extend(m_blob(X, Y, 1.0, 1.7, c, n=6, key="L골재%d" % k, jit=0.25, squash=0.7))
        else:
            m.extend(m_cyl(0, 0, 3.0, 0, 4.6, (150, 108, 70), n=12, top=(110, 172, 214)))
        m.draw(iso, lw=0.10)
        ptext(cx, y0 + 69.5, name, "b", 3.2, INK_L, "subtitle", anchor="c", layer=lay)
        draw_lines(cx, y0 + 73.1, sub, "m", 2.4, INK_L, "iconcaption", 3.0, lay, anchor="c")
    P.line([(x0 + 0.6, y0 + 79.4), (x1 - 2.2, y0 + 79.4)], (176, 156, 120), 0.25, joint=False)
    ptext(x0 + 0.6, y0 + 83.6, "섞는 순서가 열쇠 → ❹", "b", 2.8, INK_L, "body", layer=lay)
'''

NEW_B = r'''def draw_panel_B():
    # panels-v2: ❹ 만드는 과정 = Basic 2순위. 칸 폭 60·그림 ×1.0(❺·❻보다 한 단계 큼), 단계명 3.4·설명 2.8, 4단계 '뜨거운 혼합' 강조(그림 ×1.08 + 장 색 테 + 장 색 단계명)
    """❹ 만드는 과정: 6단계 등각 장면(3열 2행), 단계마다 이름 + 1줄(근거 수준 표기 1곳만 2줄), Ø4 테두리 단계 번호"""
    pn = PANEL["B"]
    x0, y0, x1, y1 = pn["rect"]
    lay = "패널 B"
    hd = pn["head"]
    chapter_header("B", 4, hd["en"], hd["ko"], x0, x1, float(hd["en_baseline_y"]), en_x=hd.get("en_x"), en_face=hd.get("en_face"), badge_d=(hd.get("badge") or {}).get("d"))
    g = pn["grid"]
    tile_sc = float(g.get("tile_scale", 1.0))
    emph_sc = float(g.get("emph_scale", 1.08))
    emph_n = int(g.get("emph_step", 4))
    nface, dface = float(g.get("name_face", 3.4)), float(g.get("desc_face", 2.8))
    cwid = float(g["cell_w"])
    for i, st in enumerate(pn["steps"][:6]):
        col, row = i % int(g["cols"]), i // int(g["cols"])
        cl = float(g["col_x0"]) + col * cwid
        cxm = cl + cwid / 2.0
        ry = float(g["row_y0"][row])
        emph = int(st["n"]) == emph_n
        if emph:                                                   # 4단계 강조: 장 색 테(0.5mm) + 옅은 바탕
            rrect(P, cl + 1.5, ry + 1.0, cl + cwid - 3.0, ry + 47.6, 1.8, fill=(252, 236, 228, 120), outline=ACCENT, lw=0.5)
        iso = ZIso(P, cxm, ry + 18.6, sc=emph_sc if emph else tile_sc)
        scene_tile(iso)
        draw_scene(i + 1, iso)
        nx_, ny_ = cxm - 12.5, ry + 14.6                           # 단계 번호: Ø4 테두리 원(장 배지보다 확실히 작다)
        P.ell(nx_, ny_, 2.0, 2.0, fill=(255, 255, 255), outline=ACCENT, lw=0.3)
        fn_, emn, fan = fface("b", 2.2, str(st["n"]))
        P.text(nx_, ny_ + fan / 2.0, str(st["n"]), fn_, ACCENT, anchor="ms")
        bbn = fn_.getbbox(str(st["n"]), anchor="ms")
        rec_text(str(st["n"]), "number", "b", emn, fan, box_poly((nx_ + bbn[0] / KD, ny_ + fan / 2.0 + bbn[1] / KD, nx_ + bbn[2] / KD, ny_ + fan / 2.0 + bbn[3] / KD)), lay)
        DRAWN["texts"][-1].update({"step_number": int(st["n"]), "c": [round(nx_, 2), round(ny_, 2)], "d": 4.0})
        ptext(cxm, ry + 41.0, st["name"], "b", nface, ACCENT if emph else INK_L, "step", anchor="c", layer=lay)
        lines = wrap_all(st["lines"], "m", dface, cwid - 4.0)
        draw_lines(cxm, ry + 45.2, lines, "m", dface, INK_L, "body", 3.9, lay, anchor="c")
        if col < int(g["cols"]) - 1:
            ax_ = cl + cwid + 0.6
            ay_ = ry + 25.4
            P.poly([(ax_ - 1.6, ay_ - 0.8), (ax_ + 0.2, ay_ - 0.8), (ax_ + 0.2, ay_ - 1.7), (ax_ + 1.9, ay_), (ax_ + 0.2, ay_ + 1.7), (ax_ + 0.2, ay_ + 0.8), (ax_ - 1.6, ay_ + 0.8)],
                   fill=BROWN_A)
    DRAWN["panel_B"] = {"cols": int(g["cols"]), "rows": int(g["rows"]), "steps": len(pn["steps"]), "number_circle_d": 4.0}
'''

NEW_D = r'''def draw_panel_D():
    # panels-v2: ❺ 석회 알갱이 = 건물을 넘는 공통 원리만(자가치유 4단계 + 단면 원). 건물별 근거 카드(포르투스·메텔라)는 지도 Detail 창이 맡는다
    """❺ 석회 알갱이 왜 오래가나: [석회 알갱이 자가치유 4단계 + 화살표] [확대 원(단면)] + 출처 1줄"""
    pn = PANEL["D"]
    x0, y0, x1, y1 = pn["rect"]
    lay = "패널 D"
    hd = pn["head"]
    chapter_header("D", 5, hd["en"], hd["ko"], x0, x1, float(hd["en_baseline_y"]), en_x=hd.get("en_x"), en_face=hd.get("en_face"), badge_d=(hd.get("badge") or {}).get("d"))
    sl = pn["stage_layout"]
    s_ = float(sl["tile_s"])
    for i, st in enumerate(pn["stages"][:4]):
        ty = float(sl["y0"]) + i * float(sl["pitch"])
        lime_sq(float(sl["x"]), ty, s_, i + 1)
        ptext(float(sl["text_x"]), ty + float(sl["name_dy"]), st["name"], "b", 3.0, INK_L, "subtitle", layer=lay)
        ptext(float(sl["text_x"]), ty + float(sl["line_dy"]), st["line"], "m", 2.6, INK_L, "body", layer=lay)
        if i < 3:                                                    # 단계 사이 아래 화살표
            ax_ = float(sl["arrow_x"])
            P.line([(ax_, ty + s_ + 0.6), (ax_, ty + s_ + 3.4)], BROWN_A, 0.35, joint=False)
            P.poly([(ax_ - 0.9, ty + s_ + 2.8), (ax_ + 0.9, ty + s_ + 2.8), (ax_, ty + s_ + 4.4)], fill=BROWN_A)
    draw_zoom()
    src = pn["source"]
    ptext(float(src["x"]), float(src["baseline_y"]), src["print"], "m", 2.6, INK_L, "body", layer=lay)
    DRAWN["panel_D"] = {"stages": len(pn["stages"]), "cards": [], "zoom_d": float(DMAP["Z1"]["circle"]["d"])}
'''

# ═════════════════════════════════ v2_panels.py 사양 덧씌우기 ═════════════════════════════════
SPEC_BLOCK = r'''

# ═════════════ panels-v2 (사용자 2026-10-19 19:36~19:39): 위·아래 띠 Basic 위계 재배치 ═════════════
# Basic 순위: ❶ 정의·재료(제목 8.4) > ❹ 만드는 과정(7.6) > ❷ 아치·볼트·돔(7.0) > ❺ 석회 알갱이(6.6) > ❻ 지금 배우는 것(6.2). 지도 안 Basic 없음.
# 위 띠(y 0~92): ❶ x 14~122 y 8~92(타이틀 x 126.5 앞 4.5mm), ❷ 그대로. 하단 띠(y 478~594): ❹ 14~196 · ❺ 202~322 · ❻ 328~406(칸 사이 6).
def _panels_v2():
    P_ = {p["id"]: p for p in PANELS}
    L_, B_, D_, P5_, S_ = P_["L"], P_["B"], P_["D"], P_["P5"], P_["S"]
    L_["rect"] = [14.0, 8.0, 122.0, 92.0]
    L_["head"].update({"en_face": 8.4, "badge": {"n": 1, "c": [19.75, 16.9], "d": 11.5}, "en_x": 27.5, "en_baseline_y": 20.5, "icon_scale": 1.7, "icon_pitch": 27.0, "icon_oy": 55.0})
    L_["type_mm"] = {"머리글 영문": 8.4, "머리글 국문": 2.8, "정의 본문": 3.0, "본문 피치": 3.9, "아이콘 이름": 3.2, "아이콘 설명": 2.4, "주석 피치": 3.0}
    L_["content"] = [c if c != "섞는 순서는 ❹" else "섞는 순서가 열쇠 → ❹" for c in L_["content"]]
    L_["rank"] = 1
    B_["rect"] = [14.0, 482.0, 196.0, 588.0]
    B_["head"].update({"en_face": 7.6, "badge": {"n": 4, "c": [19.25, 488.4], "d": 10.5}, "en_x": 26.3, "en_baseline_y": 491.5})
    B_["grid"] = {"cols": 3, "rows": 2, "cell_w": 60.0, "col_x0": 14.0, "row_y0": [494.0, 540.0], "tile_scale": 1.0, "emph_scale": 1.08, "emph_step": 4,
                  "name_face": 3.4, "desc_face": 2.8, "number_circle_d": 4.0}
    B_["type_mm"] = {"머리글 영문": 7.6, "머리글 국문 부제": 2.8, "단계명": 3.4, "단계 설명": 2.8, "설명 피치": 3.9, "단계 번호 원": 4.0}
    B_["rank"] = 2
    D_["rect"] = [202.0, 482.0, 322.0, 588.0]
    D_["name"] = "왜 오래가나(석회 알갱이 자가치유 4단계 + 단면 원)"
    D_["head"].update({"en_face": 6.6, "badge": {"n": 5, "c": [206.6, 487.6], "d": 9.2}, "en_x": 213.4, "en_baseline_y": 490.0})
    D_["stage_layout"] = {"tile_s": 16.0, "x": 203.0, "y0": 499.0, "pitch": 20.8, "text_x": 221.6, "name_dy": 6.2, "line_dy": 11.0, "arrow_x": 211.0}
    D_["zoom"] = {"c": [290.0, 535.0], "d": 46.0, "caption": "로마 콘크리트 단면", "caption_baseline_y": 563.6}
    D_["cards"] = []
    D_["source"] = {"print": "뜨거운 혼합: 2023 MIT 연구 제시(프리베르노 시료), 2025 폼페이 현장 연구 확인", "x": 204.0, "baseline_y": 584.6}
    D_["type_mm"] = {"머리글 영문": 6.6, "머리글 국문 부제": 2.8, "소제목": 3.0, "설명": 2.6, "설명 피치": 3.9, "출처": 2.6}
    D_["content"] = ["LIME CLASTS", "왜 오래가나",
                     "뜨거운 혼합", "생석회+물 → 흰 석회 알갱이", "균열", "금이 알갱이를 지난다", "빗물", "빗물이 칼슘을 녹인다", "결정 봉합", "탄산칼슘이 틈을 메운다",
                     "로마 콘크리트 단면", D_["source"]["print"]]
    D_["rank"] = 5
    P5_["rect"] = [328.0, 482.0, 406.0, 588.0]
    P5_["head"].update({"en_face": 6.2, "badge": {"n": 6, "c": [332.4, 487.6], "d": 8.8}, "en_x": 338.4, "ko_x": 338.4, "en_baseline_y": 490.0, "ko_baseline_y": 495.5})
    P5_["stair_text"].update({"text_x": 332.5, "max_w": 72.5, "line_x": 329.6})
    P5_["cells"][0]["box"] = [328.0, 539.5, 366.0, 552.0]
    P5_["cells"][1]["box"] = [368.0, 539.5, 406.0, 552.0]
    P5_["cells"][0]["body"] = ["반응하는 화산재·석회", "뜨거운 혼합·석회 알갱이"]
    P5_["cells"][1]["body"] = ["강도가 느리게 붙는다", "철근 못 지킴(알칼리 낮음)"]
    P5_["cell_text"]["max_w"] = 36.0
    P5_["carbon"].update({"print": "탄소: 만들 때 배출은 같거나 더 크고, 수명이 길어 연간 배출은 적다", "x": 328.0})
    P5_["content"] = [c.replace("철근을 못 지킨다(알칼리성 낮음)", "철근 못 지킴(알칼리 낮음)").replace("반응하는 화산재와 석회의 결합", "반응하는 화산재·석회").replace(
        "탄소: 만들 때 배출은 현대 콘크리트와 같거나 더 크고, 수명이 길어 연간 배출은 적다", "탄소: 만들 때 배출은 같거나 더 크고, 수명이 길어 연간 배출은 적다") for c in P5_["content"]]
    P5_["type_mm"].update({"머리글 영문": 6.2})
    P5_["rank"] = 6
    S_["rect"] = [328.0, 553.0, 406.0, 580.0]
    S_["bars"].update({"left_x": 330.0})
    S_["bars"]["items"][0]["outer_x"] = 333.0
    S_["bars"]["items"][1]["outer_x"] = 390.0
    P_["P2"]["rank"] = 3
    for d_ in DETAILS:
        if d_.get("id") == "Z1":
            d_["circle"] = {"c": [290.0, 535.0], "d": 46.0}
            d_["composite_box"] = [267.0, 512.0, 313.0, 558.0]
            d_["note"] = "panels-v2: 확대 원 Ø46(중심 (290,535))을 ❺ 오른쪽에 둔다. 건물별 근거 카드는 없앴고 지도 Detail 창이 맡는다."


_panels_v2()
'''


def main():
    if len(sys.argv) < 2:
        print("사용: python3 apply_panels.py <설계 폴더>")
        sys.exit(2)
    root = os.path.abspath(sys.argv[1])
    if not os.path.isdir(root):
        print("폴더 없음:", root)
        sys.exit(2)

    # ── render.py ──
    p = os.path.join(root, "render.py")
    if os.path.exists(p):
        s = _read(p)
        s = replace_func(s, "chapter_badge", NEW_BADGE, "render.py chapter_badge(배지 숫자 비례)")
        s = replace_func(s, "chapter_header", NEW_CHAPTER_HEADER, "render.py chapter_header(제목·배지 크기 인자)")
        s = replace_func(s, "draw_panel_L", NEW_L, "render.py draw_panel_L(❶ 1순위)")
        s = replace_func(s, "draw_panel_B", NEW_B, "render.py draw_panel_B(❹ 2순위·4단계 강조)")
        s = replace_func(s, "draw_panel_D", NEW_D, "render.py draw_panel_D(❺ 카드 삭제)")
        old = 'chapter_header("P5", 6, hd["en"], hd["ko"], x0, x1, float(hd["en_baseline_y"]), en_x=hd.get("en_x"), ko_baseline=hd.get("ko_baseline_y"))'
        new = ('chapter_header("P5", 6, hd["en"], hd["ko"], x0, x1, float(hd["en_baseline_y"]), en_x=hd.get("en_x"), ko_baseline=hd.get("ko_baseline_y"),\n'
               '                   en_face=hd.get("en_face"), badge_d=(hd.get("badge") or {}).get("d"))')
        s = sub_once(s, old, new, "render.py draw_panel_P5 머리글 인자", done_marker='badge_d=(hd.get("badge") or {}).get("d"))\n    stx')
        _write(p, s)
    else:
        WARNED.append("render.py 없음")

    # ── v2_panels.py ──
    p = os.path.join(root, "v2_panels.py")
    if os.path.exists(p):
        s = _read(p)
        if "_panels_v2()" in s:
            SKIPPED.append("v2_panels.py 패널 사양(_panels_v2)")
        elif "PANELS = [" not in s or "DETAILS = [" not in s:
            WARNED.append("v2_panels.py PANELS/DETAILS 없음")
        else:
            s = s.rstrip("\n") + "\n" + SPEC_BLOCK
            APPLIED.append("v2_panels.py 패널 사양(_panels_v2: L·B·D·P5·S rect·글 자리·Z1 원)")
        _write(p, s)
    else:
        WARNED.append("v2_panels.py 없음")

    # ── v2_check.py: 글자면 허용 범위(위계로 크기가 갈라졌다) ──
    p = os.path.join(root, "v2_check.py")
    if os.path.exists(p):
        s = _read(p)
        s = sub_once(s, '("panel_head_en", ["headen", "머리글영문", "headeren"], 7.0),', '("panel_head_en", ["headen", "머리글영문", "headeren"], (6.0, 8.6)),   # panels-v2: Basic 순위별 6.2~8.4',
                     "v2_check.py 장 영문 제목 글자면 6.0~8.6", done_marker="panels-v2: Basic 순위별")
        s = sub_once(s, '("step", ["step", "단계명"], 3.0),', '("step", ["step", "단계명"], (3.0, 3.4)),   # panels-v2: ❹ 3.4', "v2_check.py 단계명 3.0~3.4", done_marker="panels-v2: ❹ 3.4")
        s = sub_once(s, '"footnote", "아이콘설명", "iconcaption"], 2.1),', '"footnote", "아이콘설명", "iconcaption"], (2.1, 2.4)),   # panels-v2: ❶ 아이콘 설명 2.4',
                     "v2_check.py 주석 2.1~2.4", done_marker="panels-v2: ❶ 아이콘 설명")
        s = sub_once(s, '"title2"], 2.8),', '"title2"], (2.8, 3.2)),   # panels-v2: ❶ 아이콘 이름 3.2·❺ 소제목 3.0', "v2_check.py 소제목 2.8~3.2", done_marker="panels-v2: ❶ 아이콘 이름")
        s = sub_once(s, '("body", ["body", "본문"], 2.6),', '("body", ["body", "본문"], (2.6, 3.0)),   # panels-v2: ❶ 정의 3.0', "v2_check.py 본문 2.6~3.0", done_marker="panels-v2: ❶ 정의")
        _write(p, s)
    else:
        WARNED.append("v2_check.py 없음")

    # ── v2_text.py: P8 설명(내부 문서) ──
    p = os.path.join(root, "v2_text.py")
    if os.path.exists(p):
        s = _read(p)
        for old, new, lb in (("❹ 만드는 과정(B, x 14~158)", "❹ 만드는 과정(B, x 14~196, 하단 띠에서 가장 넓다. 4단계 뜨거운 혼합은 장 색 테로 강조)", "v2_text.py ❹ 폭"),
                             ("❺ 석회 알갱이(D, x 164~318)", "❺ 석회 알갱이(D, x 202~322)", "v2_text.py ❺ 폭"),
                             ("확대 원 Ø30 '로마 콘크리트 단면', 근거 카드 2장(바닷물 · 포르투스 2017·코사 항 시료, 빗물 · 메텔라 무덤 2021 연구), 출처 1줄(2023 MIT 연구가 실마리를 찾고 2025 폼페이 공사 현장 연구가 확인했다)",
                              "확대 원 Ø46 '로마 콘크리트 단면', 출처 1줄(뜨거운 혼합: 2023 MIT 연구 제시, 2025 폼페이 현장 연구 확인). 건물별 근거 카드는 지도 Detail 창이 맡는다", "v2_text.py ❺ 내용"),
                             ("❻ 지금 배우는 것(P5, x 324~406)", "❻ 지금 배우는 것(P5, x 328~406)", "v2_text.py ❻ 폭")):
            s = sub_once(s, old, new, lb)
        _write(p, s)
    else:
        WARNED.append("v2_text.py 없음")

    print("적용 %d · 이미 적용 %d · 경고 %d" % (len(APPLIED), len(SKIPPED), len(WARNED)))
    for a in APPLIED:
        print("  적용:", a)
    for a in SKIPPED:
        print("  이미 적용:", a)
    for a in WARNED:
        print("  경고:", a)


if __name__ == "__main__":
    main()
