# -*- coding: utf-8 -*-
# 로마 콘크리트 A2 와이어프레임 — 조립(main)
# 담당 패키지: global · 각 모듈의 objects()/labels()/extra_labels()를 모아 z·order 순서로 그리고, 자동 실측·검사 후 저장한다.
# 실행: uv run --no-project --with pillow python -I main.py --ver v17 --out /절대경로/wireframe_v17.png [--hi] [--fast]
#   --hi   : 내부 해상도(1mm=8px) 원본도 <out>_hi.png로 저장(비평가 crop용)
#   --fast : 자동 검사(analysis)를 건너뛴다(워커의 빠른 확인용, 최종 렌더에는 쓰지 않는다)
import os, sys, json, argparse, traceback
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True

import common as C
from common import *
import m_core, m_arena, m_support_bottom, m_map, m_support_top, m_panels
import analysis

# (패키지 이름, 모듈) — 패키지 이름은 OWNERS.json의 키와 같다
MODULES = [("core", m_core), ("arena", m_arena), ("support_top", m_support_top), ("support_bottom", m_support_bottom),
           ("map", m_map), ("panels", m_panels)]
EXTRA_ORDER = [m_map, m_panels, m_core, m_arena, m_support_top, m_support_bottom]


def build_map():
    page = Layer(0, 0, PW, PH, "page", bg=BG + (255,))
    cl_params = m_map.river_params()
    cl = m_map.river_centerline(*cl_params)
    m_map.setup_roads()
    ground = Layer(0, MAP_Y0, PW, MAP_Y1, "지면")
    m_map.draw_ground(ground, cl)
    page.paste(ground)
    specs = []
    for pkg, mod in MODULES:
        for s in mod.objects():
            s = dict(s)
            s["담당"] = pkg
            specs.append(s)
    specs.sort(key=lambda s: s["z"])
    objs = []
    for s in specs:
        # 선택: 그림자 함수(s["shadow"])는 별도 레이어에 먼저 깔고, 크기 자동 실측에서 뺀다
        if s.get("shadow"):
            sl = Layer(*s["region"], s["name"] + "/그림자")
            try:
                s["shadow"](sl, *s.get("args", ()))
            except Exception:
                traceback.print_exc()
                print("※ 그림자 실패: %s (담당 %s)" % (s["name"], s["담당"]))
            page.paste(sl)
        l = Layer(*s["region"], s["name"])
        try:
            s["fn"](l, *s.get("args", ()))
        except Exception:
            traceback.print_exc()
            print("※ 그리기 실패: %s (담당 %s)" % (s["name"], s["담당"]))
            x0, y0, x1, y1 = s["region"]
            l.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, outline=(220, 0, 0), lw=1.0)
        m = l.measure()
        objs.append({"이름": s["name"], "티어": s["tier"], "레이어": l, "측정": m,
                     "경계접촉": clip_edge_touch(l) and not s.get("bleed", False), "담당": s["담당"], "z": s["z"]})
        page.paste(l)
    return {"page": page, "objs": objs, "river": cl, "ground": ground}


def build_labels(R):
    LABELS.clear()
    LB = Layer(0, MAP_Y0 - 10, PW, MAP_Y1 + 10, "라벨")
    specs = []
    for pkg, mod in MODULES:
        for s in mod.labels():
            s = dict(s)
            s["담당"] = pkg
            specs.append(s)
    specs.sort(key=lambda s: s["order"])
    for s in specs:
        try:
            if s["kind"] == "label":
                draw_label(LB, s["T"], s["en"], s["ko"], s["body"], s["col"], s["M"], mode=s["mode"], side=s["side"], sup=s.get("sup"),
                           name=s["name"], gap=s.get("gap", 2.4), plate=s.get("plate", False), **s.get("kw", {}))
            else:
                draw_flag(LB, s["T"], s["en"], s["ko"], s["col"], s["M"], side=s["side"], name=s["name"], mode=s["mode"],
                          pole=s.get("pole", 8.0), **s.get("kw", {}))
        except Exception:
            traceback.print_exc()
            print("※ 라벨 실패: %s (담당 %s)" % (s["name"], s["담당"]))
    for mod in EXTRA_ORDER:
        fn = getattr(mod, "extra_labels", None)
        if fn is None:
            continue
        try:
            fn(LB)
        except Exception:
            traceback.print_exc()
            print("※ 추가 라벨 실패: %s" % mod.__name__)
    R["page"].paste(LB)
    R["labels"] = LB


def render_panels(R):
    page = R["page"]
    rows = []
    for key, tier, nm, fn in m_panels.PANELS:
        x0, y0, x1, y1 = m_panels.PANEL_RECT[key]
        l = Layer(x0 - 3, y0 - 3, x1 + 3, y1 + 3, nm)
        try:
            fn(l)
        except Exception:
            traceback.print_exc()
            print("※ 패널 실패: %s" % nm)
        m = l.measure()
        rows.append({"이름": nm, "티어": tier, "측정": m, "레이어": l, "구획": (x0, y0, x1, y1)})
        page.paste(l)
    R["panels"] = rows
    try:
        m_panels.draw_title(page)
    except Exception:
        traceback.print_exc()
        print("※ 타이틀 실패")


def finish(page, path):
    out = page.img.resize((PW * K, PH * K), Image.LANCZOS).convert("RGB")
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    out.save(path)
    return out


def _bbox(poly):
    if not poly:
        return None
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return [round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2)]


def _m(m):
    if m is None:
        return {"box": None, "area": 0}
    return {"box": [round(v, 2) for v in m["box"]], "area": round(m["area"], 1)}


def write_measure(R, lines, path, ver, png):
    data = {
        "version": ver,
        "png": png,
        "mm_to_px_final": K,
        "objects": [dict(name=o["이름"], tier=o["티어"], owner=o["담당"], z=o["z"], edge_touch=o["경계접촉"], **_m(o["측정"])) for o in R["objs"]],
        "panels": [dict(name=p["이름"], tier=p["티어"], rect=list(p["구획"]), **_m(p["측정"])) for p in R.get("panels", [])],
        "labels": [dict(name=r.get("이름"), kind=r.get("종류"), bbox=_bbox(r.get("다각형"))) for r in LABELS],
        "ok_hier": R.get("ok_hier"),
        "label_collisions": R.get("label_collisions"),
        "river_overlap": [[n, round(a_, 1)] for n, a_ in R.get("river_overlap", [])],
        "analysis": lines,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ver", default="v16")
    ap.add_argument("--out", required=True)
    ap.add_argument("--hi", action="store_true")
    ap.add_argument("--fast", action="store_true")
    a = ap.parse_args()
    C.VERSION = a.ver
    R = build_map()
    build_labels(R)
    render_panels(R)
    lines = []
    if not a.fast:
        try:
            lines = analysis.analyze(R)
        except Exception:
            lines = ["※ 자동 검사 실패(통합 담당이 고칠 것):"] + traceback.format_exc().split("\n")
    try:
        m_panels.draw_footer(R["page"], R)
    except Exception:
        traceback.print_exc()
        print("※ 푸터 실패")
    out = finish(R["page"], a.out)
    base = os.path.splitext(a.out)[0]
    out.resize((840, 1188), Image.LANCZOS).save(base + "_small.png")
    if a.hi:
        R["page"].img.convert("RGB").save(base + "_hi.png")
    write_measure(R, lines, base + "_measure.json", a.ver, a.out)
    for ln in lines:
        print(ln)
    print("와이어프레임 %s 생성: %s" % (a.ver, a.out))
    return R


if __name__ == "__main__":
    main()
