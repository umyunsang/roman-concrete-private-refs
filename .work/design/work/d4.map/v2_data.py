# -*- coding: utf-8 -*-
"""설계안 기하 정의 모음(검사·조립·미리보기가 import v2_data as D 로 읽는다). 담당: global"""
from v2_base import *  # noqa: F401,F403
from v2_map import *  # noqa: F401,F403
from v2_panels import *  # noqa: F401,F403
from v2_base import to_screen, to_plan, plan_rect_screen_box, REMOVED_PANEL_IDS  # noqa: F401

# 인쇄 지면 패널(사용자 검토 2026-10-19 02:24: R·T를 뺀다). panels가 R·T를 지운 뒤에도 같은 결과다.
PANELS_PRINT = [p for p in PANELS if p["id"] not in REMOVED_PANEL_IDS]  # noqa: F405


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
