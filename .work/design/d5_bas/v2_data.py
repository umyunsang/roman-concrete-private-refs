# -*- coding: utf-8 -*-
"""설계안 기하 정의 모음(검사·조립·미리보기가 import v2_data as D 로 읽는다). 담당: global
d4: 인쇄 패널 6개(L·P2·B·D·S·P5) 순서 고정, 랜드마크 다각형(poly_screen)·지면(ground_screen) 읽기,
필수 요소(네로 거상·R7·폰스 아일리우스 다리) 찾기, 짝 표지(PAIR_MARKS·mark·mark_pt) 모으기를 더했다(하위 호환)."""
import math
import re

from v2_base import *  # noqa: F401,F403
from v2_map import *  # noqa: F401,F403
from v2_panels import *  # noqa: F401,F403
from v2_base import to_screen, to_plan, plan_rect_screen_box, REMOVED_PANEL_IDS, PRINT_PANEL_IDS  # noqa: F401


def _order_panels(panels):
    """인쇄 패널: 뺀 패널(R·T)을 거르고 PRINT_PANEL_IDS 순서로 둔다. 순서 밖 id는 뒤에 붙여 검사가 잡게 한다"""
    keep = [p for p in panels if p.get("id") not in REMOVED_PANEL_IDS]
    rank = {pid: i for i, pid in enumerate(PRINT_PANEL_IDS)}
    return sorted(keep, key=lambda p: (rank.get(p.get("id"), len(rank)), keep.index(p)))


# 인쇄 지면 패널(사용자 검토 2026-10-19 02:24: R·T를 뺀다, 기준선 7절: P2·P5를 더한다)
PANELS_PRINT = _order_panels(PANELS)  # noqa: F405


def _union(a, b):
    return [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]


def detail_circle_box(d):
    c, dd = d["circle"]["c"], d["circle"]["d"]
    return [c[0] - dd / 2.0, c[1] - dd / 2.0, c[0] + dd / 2.0, c[1] + dd / 2.0]


def detail_box(d):
    """Detail 요소의 위계용 투영 상자. Z1은 원 + 글 칸 합성 상자(composite_box)를 쓴다.
    composite_box가 없으면 원 상자 ∪ text_box, 둘 다 없으면 원 상자(경고 대상)."""
    for k in ("composite_box", "composite"):
        if isinstance(d.get(k), (list, tuple)) and len(d[k]) == 4:
            return [float(v) for v in d[k]]
    if "circle" in d:
        b = detail_circle_box(d)
        tb = d.get("text_box")
        if isinstance(tb, (list, tuple)) and len(tb) == 4:
            b = _union(b, [float(v) for v in tb])
        return b
    return [float(v) for v in d["box"]]


def detail_box_source(d):
    if any(isinstance(d.get(k), (list, tuple)) for k in ("composite_box", "composite")):
        return "composite_box"
    if "circle" in d:
        return "circle+text_box" if isinstance(d.get("text_box"), (list, tuple)) else "circle_only"
    return "box"


def road_plan(r):
    """길의 평면 두 점(plan 또는 plan_pts)"""
    return r.get("plan") if r.get("plan") is not None else r.get("plan_pts")


def road_w(r):
    return r.get("w", r.get("w_screen_perp_mm"))


# ═════════════ d4 공용 읽기 함수(map·panels가 열쇠 이름을 조금 달리 써도 읽는다) ═════════════
def _isnum(a):
    return isinstance(a, (int, float)) and not isinstance(a, bool)


def _is_pt(p):
    return isinstance(p, (list, tuple)) and len(p) >= 2 and _isnum(p[0]) and _isnum(p[1])


def _is_box(v):
    return isinstance(v, (list, tuple)) and len(v) == 4 and all(_isnum(a) for a in v)


def as_polys(v):
    """다각형 하나([[x,y],…]) · 여러 다각형 · {poly/polys/pts…} · 상자 [x0,y0,x1,y1] → [[(x,y),…], …]"""
    if v is None:
        return []
    if isinstance(v, dict):
        for k in ("polys", "poly", "polygon", "pts", "points", "outline", "screen", "box", "rect"):
            if k in v and v[k] is not None:
                return as_polys(v[k])
        out = []                                  # {부분 이름: 다각형} 꼴이면 모두 모은다
        for vv in v.values():
            if isinstance(vv, (list, tuple, dict)):
                out += as_polys(vv)
        return out
    if _is_box(v):
        x0, y0, x1, y1 = [float(a) for a in v]
        return [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]
    if isinstance(v, (list, tuple)) and len(v) >= 3 and all(_is_pt(p) for p in v):
        return [[(float(p[0]), float(p[1])) for p in v]]
    out = []
    if isinstance(v, (list, tuple)):
        for e in v:
            out += as_polys(e)
    return out


def landmark_polys(x):
    """랜드마크 화면 다각형(겹침용). poly_screen이 있으면 그것, 없으면 None(검사가 상자로 대신하고 경고)"""
    for k in ("poly_screen", "polys_screen", "silhouette_screen"):
        if x.get(k) is not None:
            p = as_polys(x[k])
            if p:
                return p
    return None


def landmark_ground(x):
    """랜드마크 지면 다각형(땅·강·바다·접촉용). ground_screen이 있으면 그것, 없으면 None"""
    for k in ("ground_screen", "grounds_screen", "footprint_screen"):
        if x.get(k) is not None:
            p = as_polys(x[k])
            if p:
                return p
    return None


def landmark_by_id(lid):
    for x in LANDMARKS:  # noqa: F405
        if x.get("id") == lid:
            return x
    return None


def _txt(x):
    return " ".join(str(x.get(k, "")) for k in ("id", "name", "latin", "kind", "note"))


def find_prop(*keywords):
    """이름에 키워드가 든 소품(PROPS)"""
    for p in PROPS:  # noqa: F405
        nm = str(p.get("name", ""))
        if any(k in nm for k in keywords):
            return p
    return None


NERO_KEYS = ("네로 거상", "네로의 거상", "Colossus Neronis", "Colossus of Nero")
BRIDGE_KEYS = ("폰스 아일리우스", "Pons Aelius", "아일리우스 다리", "다리")


def find_nero():
    """네로 거상 받침 소품(기준선 7.3). PROPS 이름('네로'와 '거상'이 함께 든 이름, 또는 Colossus + Nero) 또는 모듈 상수 NERO·NERO_COLOSSUS"""
    p = find_prop(*NERO_KEYS)
    if p is None:
        for q in PROPS:  # noqa: F405
            nm = str(q.get("name", ""))
            if ("네로" in nm and "거상" in nm) or ("colossus" in nm.lower() and "nero" in nm.lower()):
                p = q
                break
    if p is not None:
        return {"source": "PROPS", "name": p.get("name"), "box": p.get("box"), "item": p}
    for k in ("NERO_COLOSSUS", "NERO", "COLOSSUS_NERO"):
        v = globals().get(k)
        if isinstance(v, dict):
            return {"source": k, "name": v.get("name", k), "box": v.get("box"), "item": v}
    return None


def _hull(pts):
    p = sorted(set((round(x, 4), round(y, 4)) for x, y in pts))
    if len(p) < 3:
        return p

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for q in p:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in reversed(p):
        while len(up) >= 2 and cross(up[-2], up[-1], q) <= 0:
            up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]


def plan_prism_poly(X0, X1, Y0, Y1, z0=0.0, z1=0.0):
    """평면 사각형(X0~X1 × Y0~Y1)을 z0~z1로 세운 각기둥의 화면 외곽(볼록 껍질)"""
    pts = [to_screen(X, Y, z) for X in (X0, X1) for Y in (Y0, Y1) for z in (z0, z1)]
    return _hull(pts)


def _plan_rect_of(item):
    """사양 항목의 평면 사각형(plan_x·plan_y 또는 plan [X0,X1,Y0,Y1])과 높이"""
    if not isinstance(item, dict):
        return None
    px, py = item.get("plan_x"), item.get("plan_y")
    h = item.get("deck_h", item.get("h", item.get("height", 0.0)))
    h = float(h) if _isnum(h) else 0.0
    if isinstance(px, (list, tuple)) and isinstance(py, (list, tuple)) and len(px) == 2 and len(py) == 2:
        return (float(px[0]), float(px[1]), float(py[0]), float(py[1]), h)
    pl = item.get("plan") or item.get("plan_rect")
    if isinstance(pl, (list, tuple)) and len(pl) == 4 and all(_isnum(v) for v in pl):
        return (float(pl[0]), float(pl[1]), float(pl[2]), float(pl[3]), h)
    return None


def find_bridge():
    """폰스 아일리우스 다리(L8과 함께, 기준선 7.2). 모듈 상수 → L8 열쇠 → PROPS → ROADS 순서로 찾는다.
    화면 다각형이 없고 평면 사각형(plan_x·plan_y)만 있으면 상판 각기둥으로 투영한다"""
    r = _find_bridge_raw()
    if r is not None and not r.get("polys"):
        pr = _plan_rect_of(r.get("item"))
        if pr:
            r["polys"] = [plan_prism_poly(pr[0], pr[1], pr[2], pr[3], 0.0, pr[4])]
            r["polys_from"] = "plan_x·plan_y 투영"
    return r


def _find_bridge_raw():
    for k in ("PONS_AELIUS", "BRIDGE", "BRIDGES"):
        v = globals().get(k)
        if isinstance(v, dict):
            return {"source": k, "name": v.get("name", k), "item": v, "polys": as_polys(v.get("screen") or v.get("poly_screen") or v.get("box"))}
        if isinstance(v, list) and v:
            return {"source": k, "name": str(v[0].get("name", k)) if isinstance(v[0], dict) else k, "item": v, "polys": as_polys(v)}
    l8 = landmark_by_id("L8")
    if l8 is not None:
        bs = l8.get("bridge_screen")
        if bs is not None and as_polys(bs):
            return {"source": "L8.bridge_screen", "name": "폰스 아일리우스 다리", "item": l8.get("bridge") if isinstance(l8.get("bridge"), dict) else None, "polys": as_polys(bs)}
        ps = l8.get("parts_screen")
        if isinstance(ps, dict):
            for k, v in ps.items():
                if any(b in str(k) for b in BRIDGE_KEYS) and as_polys(v):
                    return {"source": "L8.parts_screen", "name": str(k), "item": None, "polys": as_polys(v)}
        for k in ("bridge", "pons", "다리", "bridge_plan"):
            v = l8.get(k)
            if v is not None and not isinstance(v, bool):
                item = v if isinstance(v, dict) else {"geom": v}
                g = item.get("screen") or item.get("poly_screen") or item.get("box") or item.get("geom")
                return {"source": "L8." + k, "name": item.get("name", "폰스 아일리우스 다리"), "item": item, "polys": as_polys(g) if g is not None else []}
        for k, v in l8.items():                    # L8 안의 부분 목록(parts 등)에 이름이 다리인 항목
            for e in (v if isinstance(v, list) else [v] if isinstance(v, dict) else []):
                if isinstance(e, dict) and any(b in str(e.get("name", "")) for b in BRIDGE_KEYS):
                    g = e.get("screen") or e.get("poly_screen") or e.get("box")
                    return {"source": "L8.%s" % k, "name": e.get("name"), "item": e, "polys": as_polys(g) if g is not None else []}
        if l8.get("bridge") is True or (any(b in _txt(l8) for b in BRIDGE_KEYS[:3]) and any(b in str(l8.get("form", "")) for b in ("다리", "Pons", "bridge"))):
            return {"source": "L8.form", "name": "폰스 아일리우스 다리", "item": None, "polys": []}
    p = find_prop(*BRIDGE_KEYS[:3])
    if p is not None:
        return {"source": "PROPS", "name": p.get("name"), "item": p, "polys": as_polys(p.get("poly_screen") or p.get("box"))}
    for r in ROADS:  # noqa: F405
        if any(b in str(r.get("name", "")) for b in BRIDGE_KEYS[:3]) or "bridge" in str(r.get("kind", "")):
            return {"source": "ROADS." + str(r.get("id")), "name": r.get("name"), "item": r, "polys": []}
    return None


def road_by_id(rid):
    for r in ROADS:  # noqa: F405
        if r.get("id") == rid:
            return r
    return None


# ── 짝 표지(A~D: 지도 ↔ Detail, 1~4: P2 칸 ↔ 지도). 사양 mark·mark_pt 값만 모은다(이름 추론 금지) ──
_GLYPH_KEYS = ("mark", "glyph", "letter", "print", "n", "no", "num", "label", "text", "id")
_PT_KEYS = ("mark_pt", "pt", "c", "center", "중심", "xy")
_SRC_KEYS = ("source", "src", "출처", "where", "side")
_SIDE_KEYS = {"map": "map", "지도": "map", "map_pt": "map", "panel": "panel", "패널": "panel", "panel_pt": "panel", "p2": "panel",
              "detail": "detail", "detail_pt": "detail", "z1": "detail", "callout": "detail"}


def _glyph(e):
    """표지 글자: 한 글자(A~Z·0~9)만 받는다(패널 id 'P2' 같은 값을 글자로 읽지 않게)"""
    for k in _GLYPH_KEYS:
        v = e.get(k)
        if isinstance(v, (str, int)) and not isinstance(v, bool):
            s_ = str(v).strip().upper()
            if re.fullmatch(r"[A-Z0-9]", s_):
                return s_
    return None


def _norm_src(s):
    s = str(s or "").lower()
    if any(k in s for k in ("map", "지도")):
        return "map"
    if any(k in s for k in ("detail", "z1", "확대", "콜아웃", "callout")):
        return "detail"
    if any(k in s for k in ("panel", "패널", "p2", "칸", "cell")):
        return "panel"
    return s or None


def pair_marks():
    """사양에 적힌 짝 표지 점 목록: [{glyph, pt, source, from}]. PAIR_MARKS(panels) + LEADERS·DETAILS·PANELS의 mark·mark_pt.
    형식을 몰라도 읽도록 너그럽게 훑는다(검사 판정은 사후 검사 ⑬이 drawn.json으로 한다)"""
    out = []

    def add(glyph, pt, src, frm):
        if glyph and _is_pt(pt):
            out.append({"glyph": glyph, "pt": [round(float(pt[0]), 2), round(float(pt[1]), 2)], "source": _norm_src(src), "from": frm})

    def walk(e, frm, glyph=None, src=None, depth=0):
        if depth > 6:
            return
        if isinstance(e, list):
            if e and all(_is_pt(p) for p in e) and glyph:
                for p in e:
                    add(glyph, p, src, frm)
                return
            for v in e:
                walk(v, frm, glyph, src, depth + 1)
            return
        if not isinstance(e, dict):
            return
        g = _glyph(e) or glyph
        s_ = next((e[k] for k in _SRC_KEYS if e.get(k)), src)
        for k in _PT_KEYS:
            v = e.get(k)
            if _is_pt(v):
                add(g, v, s_, frm)
                break
            if k == "mark_pt" and isinstance(v, (list, tuple)) and v and all(_is_pt(p) for p in v):
                for p in v:
                    add(g, p, s_, frm)
                break
        for k, v in e.items():
            side = _SIDE_KEYS.get(str(k).lower())
            if side and _is_pt(v):
                add(g, v, side, frm)
            elif isinstance(v, (dict, list)) and k not in _PT_KEYS:
                walk(v, frm, g, side or s_, depth + 1)

    pmk = globals().get("PRINT_MARKS")               # panels가 만든 전체 표지 목록(mark·src·pt)이 있으면 그것이 원본이다
    if isinstance(pmk, list) and pmk:
        for e in pmk:
            if isinstance(e, dict):
                add(_glyph(e), e.get("pt") or e.get("mark_pt") or e.get("c"), e.get("src") or e.get("source"), "PRINT_MARKS")
        seen, uniq = set(), []
        for m in out:
            k = (m["glyph"], m["pt"][0], m["pt"][1])
            if k not in seen:
                seen.add(k)
                uniq.append(m)
        return uniq
    pm = globals().get("PAIR_MARKS")
    if isinstance(pm, dict):
        for k, v in pm.items():
            gk = str(k).strip().upper() if re.fullmatch(r"[A-Za-z0-9]", str(k).strip()) else None
            walk(v, "PAIR_MARKS", gk)
    elif pm is not None:
        walk(pm, "PAIR_MARKS")
    for src_list, frm, dflt in ((LEADERS, "LEADERS", "map"), (DETAILS, "DETAILS", "detail"), (PANELS, "PANELS", "panel")):  # noqa: F405
        for e in src_list:
            g = _glyph({"mark": e.get("mark")})
            mp = e.get("mark_pt")
            if g and _is_pt(mp):
                add(g, mp, e.get("mark_source") or dflt, frm)
            elif g and isinstance(mp, (list, tuple)):
                for p in mp:
                    if _is_pt(p):
                        add(g, p, e.get("mark_source") or dflt, frm)
                    elif isinstance(p, dict):
                        walk(p, frm, g, e.get("mark_source") or dflt)
            elif g and isinstance(mp, dict):
                walk(mp, frm, g, e.get("mark_source") or dflt)
    # 같은 글자·같은 점은 한 번만
    seen, uniq = set(), []
    for m in out:
        k = (m["glyph"], m["pt"][0], m["pt"][1])
        if k not in seen:
            seen.add(k)
            uniq.append(m)
    return uniq


def pair_mark_counts():
    c = {}
    for m in pair_marks():
        c[m["glyph"]] = c.get(m["glyph"], 0) + 1
    return c


def dist_pt(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def prop_box(p):
    """소품 투영 상자: box가 있으면 그것, 없으면 poly_screen·parts_screen 외곽 상자, 둘 다 없으면 None"""
    b = p.get("box")
    if _is_box(b):
        return [float(v) for v in b]
    pl = as_polys(p.get("poly_screen")) or as_polys(p.get("parts_screen"))
    if pl:
        xs = [q[0] for pg in pl for q in pg]
        ys = [q[1] for pg in pl for q in pg]
        return [min(xs), min(ys), max(xs), max(ys)]
    return None


def label_block(lb):
    """라벨 글 블록 다각형(block_poly가 있으면 그것). 없으면 None(슬롯 상자로 대신한다)"""
    for k in ("block_poly", "poly_screen", "block"):
        v = lb.get(k)
        if v is not None:
            pl = as_polys(v)
            if pl:
                return pl
    return None


# ═════════════ d5 공용 읽기: 콜로세움 본체(8.1)·히어로 둘레(8.2, 12:49)·앵커(D11) ═════════════
# map이 새 dict를 어떤 이름으로 두어도 읽는다(없으면 d4 옛 상수 HERO_RING·HERO_WALLS·HERO_SIDE를 '옛 형식'으로 읽는다).
_COLO_KEYS = ("HERO_COLOSSEUM", "COLOSSEUM", "HERO_COLO", "HERO_BODY", "HERO_BUILDING", "COLOSSEUM_BODY", "HERO_MODEL", "COLO_D5")
_LAND_KEYS = ("HERO_LANDSCAPE", "LANDSCAPE", "HERO_PLAZA", "HERO_SURROUND", "HERO_GROUNDS", "HERO_GROUP", "PLAZA")
_CROWD_KEYS = ("HERO_CROWDS", "CROWDS", "HERO_PEOPLE")


def _first(d, *keys):
    if not isinstance(d, dict):
        return None
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def _pair(v):
    if isinstance(v, (list, tuple)) and len(v) >= 2 and _isnum(v[0]) and _isnum(v[1]):
        return (float(v[0]), float(v[1]))
    if isinstance(v, dict):
        a, b = _first(v, "a", "rx", "major", "semi_major", "X", "x"), _first(v, "b", "ry", "minor", "semi_minor", "Y", "y")
        if _isnum(a) and _isnum(b):
            return (float(a), float(b))
    return None


import v2_base as _VB  # noqa: E402  (순수 기하 도우미: 사전·사후 검사와 같은 구현을 쓴다)
plan_az = _VB.plan_az
az_in = _VB.az_in
_profile = _VB.parse_profile
wall_h = _VB.wall_h
_ellipse_r = _VB.ellipse_r


def hero_model():
    """콜로세움 본체 정규형(검사·조립 공용). source = 'map:<이름>'(d5 새 dict) 또는 'map:d4 옛 상수'(HERO_RING·HERO_WALLS·HERO_SIDE).
    필드: center_plan, semi_axes, major_az, profile[(t0,t1,lo,hi,메모)], second_ring{h, front_az, front_h_max}, arena_semi_axes, wood_frac,
    building_box(사양 값, 없으면 None), base_side, octagon, front_cut, arches, tier_lines_z, raw(원본)"""
    g = globals()
    raw, src = None, None
    for k in _COLO_KEYS:
        if isinstance(g.get(k), dict):
            raw, src = g[k], "map:" + k
            break
    if raw is not None:
        c = _pair(_first(raw, "center_plan", "outer_center_plan", "ellipse_center_plan", "c_plan", "plan_center"))
        if c is None and _pair(_first(raw, "center_screen", "c_screen")):
            c = to_plan(*_pair(_first(raw, "center_screen", "c_screen")))
        if c is None and _pair(raw.get("center")):
            c = _pair(raw.get("center"))
        ax = _pair(_first(raw, "semi_axes_plan", "semi_axes", "outer_semi_axes", "axes_plan", "axes", "ab", "outer_semi"))
        if ax is None and _isnum(raw.get("a")) and _isnum(raw.get("b")):
            ax = (float(raw["a"]), float(raw["b"]))
        if ax is None and isinstance(raw.get("outer"), dict):
            ax = _pair(_first(raw["outer"], "semi_axes_plan", "semi_axes", "axes"))
        maz = _first(raw, "major_az_deg", "major_axis_az_deg", "major_az", "long_axis_az_deg", "axis_az_deg", "az_major_deg")
        prof = _profile(_first(raw, "wall_profile", "outer_wall_profile", "wall_heights", "outer_walls", "walls", "segments", "heights"))
        r2 = _first(raw, "second_ring", "ring2", "inner_ring", "inner_arcade", "ring_2")
        ring2 = None
        if isinstance(r2, dict):
            fh = _first(r2, "front_h_max", "front_max")
            fr = r2.get("front_h")
            if fh is None and isinstance(fr, (list, tuple)) and fr:
                fh = max(fr)
            elif fh is None and _isnum(fr):
                fh = fr
            ring2 = {"h": _first(r2, "h", "height"), "front_az": _first(r2, "front_az", "front", "front_deg"), "front_h_max": fh,
                     "profile": _profile(_first(r2, "profile", "wall_profile", "segments"))}
        ar = _pair(_first(raw, "arena_semi_axes_plan", "arena_semi_axes", "arena_axes"))
        if ar is None and isinstance(raw.get("arena"), dict):
            ar = _pair(_first(raw["arena"], "semi_axes_plan", "semi_axes", "axes"))
        elif ar is None:
            ar = _pair(raw.get("arena"))
        fl = _first(raw, "floor", "wood_floor", "arena_floor") or {}
        wf = _first(fl, "wood_frac", "wood_fraction", "frac") if isinstance(fl, dict) else None
        if wf is None:
            wf = raw.get("wood_frac")
        us = _first(fl, "u_split", "u0", "split_u") if isinstance(fl, dict) else None
        if wf is None and _isnum(us) and ar:
            t = max(-1.0, min(1.0, -float(us) / ar[0]))
            wf = 0.5 + (math.asin(t) + t * math.sqrt(1 - t * t)) / math.pi
        bs = _first(raw, "base_side_mm", "base_side", "plinth_side_mm", "side_mm")
        return {"source": src, "legacy": False, "center_plan": c, "semi_axes": ax, "major_az": float(maz) if _isnum(maz) else None,
                "profile": prof, "second_ring": ring2, "arena_semi_axes": ar, "wood_frac": float(wf) if _isnum(wf) else None, "u_split": us,
                "building_box": _first(raw, "building_screen_box", "screen_box", "building_box", "projected_box", "box"),
                "base_side": float(bs) if _isnum(bs) else float(g.get("HERO_SIDE", 0.0) or 0.0) if "HERO_SIDE" in g else 0.0,
                "octagon": bool(raw.get("octagon", False)), "front_cut": bool(raw.get("front_cut", False)),
                "arches": _first(raw, "arches", "arch_count", "n_arches"), "tier_lines_z": _first(raw, "tier_lines_z", "tiers_z", "floor_lines_z"),
                "raw": raw}
    # d4 옛 상수(팔각 받침 + 원형 고리 + 벽 60/28/12)
    R = float(g.get("HERO_R", 90.0) or 90.0)
    ring = float(g.get("HERO_RING", 0.0) or 0.0)
    walls = g.get("HERO_WALLS") or []
    prof = [(float(w["t0"]), float(w["t1"]), float(w["h"]), float(w["h"]), str(w.get("part", ""))) for w in walls if all(k in w for k in ("t0", "t1", "h"))]
    hi = g.get("HERO_INTERIOR") or {}
    exposed = str(((hi.get("hypogeum") or {}).get("exposed")) or "")
    cut = g.get("HERO_CUTAWAY")
    return {"source": "map:d4 옛 상수(HERO_RING·HERO_WALLS·HERO_SIDE)", "legacy": True,
            "center_plan": tuple(g["HERO_C_PLAN"]) if g.get("HERO_C_PLAN") else None,
            "semi_axes": (ring * R, ring * R) if ring > 0 else None, "major_az": 315.0 if ring > 0 else None,
            "profile": prof, "second_ring": None, "arena_semi_axes": None,
            "wood_frac": 0.5 if "반쪽" in exposed else None, "u_split": 0.0 if "반쪽" in exposed else None,
            "building_box": None, "base_side": float(g.get("HERO_SIDE", 0.0) or 0.0),
            "octagon": callable(g.get("hero_oct")), "front_cut": isinstance(cut, dict) and bool(cut.get("x")),
            "arches": None, "tier_lines_z": None, "raw": {"HERO_R": R, "HERO_RING": ring, "HERO_WALLS": walls, "HERO_SIDE": g.get("HERO_SIDE")}}


def hero_building_polys(m, step=2.0):
    """본체 화면 실루엣 다각형들: 바닥 타원 + θ마다 외벽 사각(바닥 → 윗선 hi). 모델 자료가 모자라면 []"""
    if not m or not m.get("center_plan") or not m.get("semi_axes"):
        return []
    return _VB.colo_building_polys(m["center_plan"], m["semi_axes"], m.get("major_az"), m.get("profile") or [], step)


def hero_landscape():
    """히어로 둘레 정규형(사용자 16:14: 땅 바탕뿐). source = 'map:<이름>' 또는 'map:d4 옛 팔각 받침'.
    필드: center_plan, reserve_R, rep_R, boundary_screen(다각형 또는 None), base_side, octagon, front_cut, parts[이름], crowds, raw"""
    g = globals()
    raw, src = None, None
    for k in _LAND_KEYS:
        if isinstance(g.get(k), dict):
            raw, src = g[k], "map:" + k
            break
    if raw is None:
        for k in _COLO_KEYS:                                 # 본체 dict 안의 둘레 묶음
            v = g.get(k)
            if isinstance(v, dict) and isinstance(_first(v, "landscape", "surround"), dict):
                raw, src = _first(v, "landscape", "surround"), "map:%s.landscape" % k
                break
    crowds = None
    for k in _CROWD_KEYS:
        if isinstance(g.get(k), list):
            crowds = g[k]
            break
    if raw is not None:
        c = _pair(_first(raw, "center_plan", "c_plan", "plan_center")) or (to_plan(*_pair(raw["center_screen"])) if _pair(raw.get("center_screen")) else None)
        bnd = None
        for k in ("boundary_screen", "poly_screen", "outline_screen", "slab_screen"):
            pl = as_polys(raw.get(k))
            if pl:
                bnd = pl
                break
        if bnd is None:
            for k in ("boundary_plan", "plan_poly", "outline_plan", "slab_plan"):
                v = raw.get(k)
                if isinstance(v, (list, tuple)) and len(v) >= 3 and all(_is_pt(p) for p in v):
                    bnd = [[to_screen(float(p[0]), float(p[1])) for p in v]]
                    break
        parts = []
        for k in ("parts", "props", "items", "elements", "layout", "pieces"):
            v = raw.get(k)
            if isinstance(v, list):
                parts += [str(_first(e, "name", "kind", "type", "id") or "") if isinstance(e, dict) else str(e) for e in v]
            elif isinstance(v, dict):
                parts += [str(kk) for kk in v.keys()]
        if crowds is None and isinstance(_first(raw, "crowds", "people_groups", "groups"), list):
            crowds = _first(raw, "crowds", "people_groups", "groups")
        bs = _first(raw, "base_side_mm", "base_side", "side_mm")
        return {"source": src, "legacy": False, "center_plan": c,
                "reserve_R": _first(raw, "reserve_R_plan", "reserve_R", "R_reserve", "R"),
                "rep_R": _first(raw, "rep_R_plan", "rep_R", "R_rep", "rb_mean"),
                "boundary_screen": bnd, "base_side": float(bs) if _isnum(bs) else 0.0,
                "octagon": bool(raw.get("octagon", False)), "front_cut": bool(raw.get("front_cut", False)),
                "parts": parts, "crowds": crowds, "raw": raw}
    oct_ = hero_oct() if callable(g.get("hero_oct")) else None
    return {"source": "map:d4 옛 팔각 받침(hero_oct·HERO_SIDE)", "legacy": True, "center_plan": tuple(g["HERO_C_PLAN"]) if g.get("HERO_C_PLAN") else None,
            "reserve_R": g.get("HERO_R"), "rep_R": None, "boundary_screen": [oct_] if oct_ else None,
            "base_side": float(g.get("HERO_SIDE", 0.0) or 0.0), "octagon": bool(oct_),
            "front_cut": isinstance(g.get("HERO_CUTAWAY"), dict) and bool(g["HERO_CUTAWAY"].get("x")),
            "parts": [], "crowds": crowds, "raw": None}


def landscape_width(ls):
    """비례 기준 화면 폭: 경계 다각형 외곽 폭 → 없으면 대표 반지름(2·R·1.2247). 둘 다 없으면 None"""
    if ls.get("boundary_screen"):
        xs = [p[0] for pg in ls["boundary_screen"] for p in pg]
        return max(xs) - min(xs)
    if _isnum(ls.get("rep_R")):
        return 2.0 * float(ls["rep_R"]) * math.sqrt(1.5)
    return None


def hero_part_names():
    """히어로 둘레 구성 부품 이름(조경 dict parts + PROPS + TERRAIN·PLANTED + 공사장 + 네로 + 길 문)"""
    ls = hero_landscape()
    names = list(ls.get("parts") or [])
    names += [str(p.get("name", "")) for p in PROPS]  # noqa: F405
    names += [str(t.get("name", "")) for t in (globals().get("TERRAIN") or [])]
    names += [str(t.get("name", "")) for t in (globals().get("PLANTED") or [])]
    ws = globals().get("WORKSITE")
    if isinstance(ws, dict):
        names.append(str(ws.get("name", "공사장")))
    return names


def blender_anchor_items():
    """labels·leaders·marks의 blender_anchor 값(panels가 더한 열쇠) 모음: [{from, name, anchor}]"""
    out = []
    for src, lst in (("LABELS", globals().get("LABELS") or []), ("LEADERS", globals().get("LEADERS") or []),
                     ("PRINT_MARKS", globals().get("PRINT_MARKS") or []), ("PAIR_MARKS", globals().get("PAIR_MARKS") or [])):
        if not isinstance(lst, list):
            continue
        for e in lst:
            if isinstance(e, dict) and e.get("blender_anchor") is not None:
                out.append({"from": src, "name": e.get("name") or e.get("mark") or e.get("glyph"), "anchor": e.get("blender_anchor")})
    return out
