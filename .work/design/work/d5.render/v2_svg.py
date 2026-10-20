# -*- coding: utf-8 -*-
"""배치 사양 내부 골격 미리보기(인쇄 지면이 아님: 상자·치수·티어 색은 이 내부 도면에만). 담당: global
d4: 사용자 검토(02:24)·사용자 선택(03:10) 반영 — 옛 R·T 패널 없음, 무대 = STAGE 하나(확장 0), 패널 L·P2·B·D·S·P5,
랜드마크 L1~L9(poly_screen 외곽), 길 R7, 네로 거상 받침, 짝 표지(A~D·1~4) 점. 사용: python -I v2_svg.py <data_dir> <out.svg>"""
import json
import math
import sys

sys.path.insert(0, sys.argv[1])
import v2_data as D  # noqa: E402

chk = json.load(open(sys.argv[1] + "/v2_check.json"))
out = []
A = out.append
FONT = "Apple SD Gothic Neo, AppleSDGothicNeo, Noto Sans CJK KR, sans-serif"
COL = {"Core": "#2f6b3a", "Basic": "#3f3aa0", "Detail": "#d0650e", "Support": "#2f7f86", "accent": "#c82236"}


def pts(p):
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in p)


def poly(p, fill, stroke="none", sw=0.3, op=1.0, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    A(f'<polygon points="{pts(p)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" fill-opacity="{op}"{d}/>')


def rect(b, fill, stroke="none", sw=0.3, op=1.0, dash=None, rx=0):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    A(f'<rect x="{b[0]:.2f}" y="{b[1]:.2f}" width="{b[2]-b[0]:.2f}" height="{b[3]-b[1]:.2f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" fill-opacity="{op}"{d}/>')


def text(x, y, s, size=3.0, col="#2a2018", anchor="start", weight="normal", rot=0):
    tr = f' transform="rotate({rot} {x:.2f} {y:.2f})"' if rot else ""
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    A(f'<text x="{x:.2f}" y="{y:.2f}" font-family="{FONT}" font-size="{size}" fill="{col}" text-anchor="{anchor}" font-weight="{weight}"{tr}>{s}</text>')


def line(p, col, sw=0.4, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    A(f'<polyline points="{pts(p)}" fill="none" stroke="{col}" stroke-width="{sw}"{d}/>')


def plan_band(p0, p1, w):
    hw = w / (2 * D.C30)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    nx, ny = -dy / L * hw, dx / L * hw
    return [D.to_screen(p0[0] + nx, p0[1] + ny), D.to_screen(p1[0] + nx, p1[1] + ny), D.to_screen(p1[0] - nx, p1[1] - ny), D.to_screen(p0[0] - nx, p0[1] - ny)]


A('<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="594mm" viewBox="0 0 420 594">')
A('<defs><clipPath id="poster"><rect x="0" y="0" width="420" height="594"/></clipPath>'
  '<pattern id="vine" width="4" height="2.3" patternUnits="userSpaceOnUse" patternTransform="rotate(-30)"><line x1="0" y1="1" x2="4" y2="1" stroke="#7d9a52" stroke-width="0.5"/></pattern>'
  '<linearGradient id="seafade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8fb3cc" stop-opacity="0.55"/><stop offset="1" stop-color="#8fb3cc" stop-opacity="0.08"/></linearGradient></defs>')
A('<g clip-path="url(#poster)">')
rect([0, 0, 420, 594], "#ead6a8")
rect(D.STAGE, "#e3c995")
for _er in getattr(D, "STAGE_EXT", []):
    rect(_er, "#e3c995")          # R·T 자리를 돌려준 무대 확장
# 심은 지면(밭·포도밭·숲)
for pl in D.PLANTED:
    rect(pl["box"], "#b9c58a", op=0.55)
    rect(pl["box"], "url(#vine)", op=0.6)
for tr in D.TERRAIN:
    if tr["name"].startswith("알바노"):
        rect(tr["box"], "#b3b48c", op=0.55)
# 바다
poly(D.SEA_UNDER_BAND, "url(#seafade)")
poly(D.SEA, "#8fb3cc")
line(D.COAST, "#4f7593", 0.9)
text(D.COAST[0][0] + 2, D.COAST[0][1] - 1.5, "해안선 y = tan30·x + 380 (지층 단면 10mm)", 2.2, "#2c4d66", "start", "normal", rot=30)
# 강
poly(D.river_polygon(), "#6fa8d0", "#3d6f98", 0.3)
# 길
for r in D.ROADS:
    _pl, _w = D.road_plan(r), D.road_w(r)
    for _p0, _p1 in zip(_pl[:-1], _pl[1:]):
        if math.hypot(_p1[0] - _p0[0], _p1[1] - _p0[1]) > 1e-6:
            poly(plan_band(_p0, _p1, _w), "#cdb38a" if _w < 15 else "#b89a70", "#86683f", 0.25)
    if r.get("center_line"):
        line([D.to_screen(*_pl[0]), D.to_screen(*_pl[-1])], "#fbf4e2", 0.6, dash="2,1.5")
# 수도교 아치 열
a0 = D.to_screen(*D.AQUEDUCT_PLAN[0])
a1 = D.to_screen(*D.AQUEDUCT_PLAN[1])
poly([a0, a1, (a1[0], a1[1] - D.AQUEDUCT_H), (a0[0], a0[1] - D.AQUEDUCT_H)], "#c99a6e", "#7a5232", 0.4, op=0.8)
n = 11
for i in range(n + 1):
    t = i / n
    x = a0[0] + (a1[0] - a0[0]) * t
    y = a0[1] + (a1[1] - a0[1]) * t
    line([(x, y), (x, y - D.AQUEDUCT_H)], "#7a5232", 0.35)
# 소품
for pr in D.PROPS:
    b = D.prop_box(pr) if hasattr(D, "prop_box") else pr.get("box")
    if not b:
        continue
    rect(b, "#efc793" if pr.get("on") != "물" else "#d9e4ea", "#9a6a3a", 0.3, op=0.85)
    text((b[0] + b[2]) / 2, (b[1] + b[3]) / 2 + 0.8, pr["name"].split("(")[0], 1.9, "#5a3410", "middle")
# 배경: 베수비오(가장 먼 곳)
for bgx in D.BACKGROUND:
    b = bgx["box"]
    poly([(b[0], b[3]), ((b[0] + b[2]) / 2 - 6, b[1] + 3), ((b[0] + b[2]) / 2 + 6, b[1] + 3), (b[2], b[3])], "#a7aea4", "#6f7b72", 0.4, op=0.7)
    rect(b, "none", COL["Core"], 0.4, dash="1.2,0.8")
    text((b[0] + b[2]) / 2, b[3] - 3, "베수비오(배경) %g×%g" % (b[2] - b[0], b[3] - b[1]), 2.3, "#33463a", "middle", "bold")
# Core 랜드마크
for x in D.LANDMARKS:
    b = chk["objects_boxes"][x["name"]]["box"]
    if x["id"] != "L4":
        rect(b, "#d6e8c4", COL["Core"], 0.7, op=0.82)
    else:
        rect(b, "none", COL["Core"], 0.7, dash="2,1")
    _pl = D.landmark_polys(x) if hasattr(D, "landmark_polys") else None
    for _pg in (_pl or []):
        poly(_pg, "#c3dcae", COL["Core"], 0.35, op=0.7)          # 랜드마크 다각형(poly_screen)
    _gr = D.landmark_ground(x) if hasattr(D, "landmark_ground") else None
    for _pg in (_gr or []):
        poly(_pg, "none", "#1d4a26", 0.3, dash="0.8,0.6")       # 지면(ground_screen)
    nm = x["id"] + " " + x["name"]
    text((b[0] + b[2]) / 2, (b[1] + b[3]) / 2 - 1.5, nm, 3.0, "#1d4a26", "middle", "bold")
    text((b[0] + b[2]) / 2, (b[1] + b[3]) / 2 + 3.2, f'{b[2]-b[0]:.0f}×{b[3]-b[1]:.0f}mm', 2.3, "#1d4a26", "middle")
# 포르투스 외형
for part, polys in D.portus_polys().items():
    for pg in polys:
        poly(pg, "#a9cde2" if "외항" in part else ("#e9c3a3" if "육각" in part else "#f4ead8"), "#7a3a2a", 0.4, op=0.9)
# 히어로(콜로세움)
o = D.hero_oct()
for k in (7, 0, 1):
    a, b = o[k], o[(k + 1) % 8]
    poly([a, b, (b[0], b[1] + D.HERO_SIDE), (a[0], a[1] + D.HERO_SIDE)], "#8c6a45", "#5a4028", 0.3)
poly(o, "#d6c19f", "#5a4028", 0.6)
cx, cy = D.HERO_C
rr = D.HERO_RING * D.HERO_R
A(f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{1.2247*rr:.2f}" ry="{0.7071*rr:.2f}" fill="#e8dcc0" stroke="#7a5a3a" stroke-width="0.5"/>')
A(f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{1.2247*0.42*D.HERO_R:.2f}" ry="{0.7071*0.42*D.HERO_R:.2f}" fill="#c49a68" stroke="#7a5a3a" stroke-width="0.4"/>')
for w in D.HERO_WALLS:
    seg = [D.hero_ring_pt(t, 0) for t in range(w["t0"], w["t1"] + 1, 5)] + [D.hero_ring_pt(t, w["h"]) for t in range(w["t1"], w["t0"] - 1, -5)]
    poly(seg, "#dcc8a4", "#6a4a2a", 0.4, op=0.88 if w["h"] > 20 else 0.6)
cut = D.HERO_CUTAWAY["x"]
poly([(cut[0], o[1][1]), (cut[1], o[0][1]), (cut[1], o[0][1] + D.HERO_SIDE), (cut[0], o[1][1] + D.HERO_SIDE)], "#b8b0a2", "#3a3a3a", 0.5)
text((cut[0] + cut[1]) / 2, o[0][1] + D.HERO_SIDE - 1.6, "기초 절개(콘크리트 고리 단면)", 2.0, "#ffffff", "middle", "bold")
text(cx, cy + 4, "콜로세움 — Core 히어로·최대 단일 오브젝트", 3.6, "#3a2410", "middle", "bold")
hb = chk["hierarchy"]["hero_box"]
text(cx, cy + 9, f'투영 상자 {hb[2]-hb[0]:.0f}×{hb[3]-hb[1]:.0f}mm = {chk["hierarchy"]["hero_area"]:,}mm²', 2.6, "#3a2410", "middle")
rect(hb, "none", COL["Core"], 0.5, dash="2.5,1.2")
ws = D.WORKSITE["box"]
rect(ws, "#f2b77a", "#a0562a", 0.4, op=0.9)
text((ws[0] + ws[2]) / 2, (ws[1] + ws[3]) / 2 + 0.8, "공사장(다져 넣기)", 2.1, "#5a2a0a", "middle", "bold")
# Detail: 확대 창·콜아웃
for d in D.DETAILS:
    if "circle" in d:
        c, dd = d["circle"]["c"], d["circle"]["d"]
        A(f'<circle cx="{c[0]}" cy="{c[1]}" r="{dd/2}" fill="#fbf1de" stroke="{COL["Detail"]}" stroke-width="1.2"/>')
        for dx, dy, r_ in [(-12, -8, 4.5), (9, -13, 3.5), (-4, 11, 5.5), (14, 7, 3), (-19, 12, 2.6)]:
            A(f'<circle cx="{c[0]+dx}" cy="{c[1]+dy}" r="{r_}" fill="#ffffff" stroke="#9a8a70" stroke-width="0.4"/>')
        line([(c[0] - 20, c[1] - 26), (c[0] - 1, c[1] + 1), (c[0] + 12, c[1] + 26)], "#3a2a1a", 0.5)
        text(c[0], c[1] + dd / 2 - 5, f'{d["id"]} 확대 창 Ø{dd:.0f} · {d.get("mark", "")}', 2.4, "#8a3a00", "middle", "bold")
        if d.get("text_box"):
            rect(d["text_box"], "#fdf3e2", COL["Detail"], 0.4, op=0.9)
        rect(D.detail_box(d), "none", COL["Detail"], 0.35, dash="1.5,1")
    else:
        b = d["box"]
        rect(b, "#fde9cf", COL["Detail"], 0.7, op=0.95)
        text(b[0] + 1.5, b[1] + 4, f'{d["id"]} {d["name"].replace("콜아웃: ", "")}', 2.2, "#8a3a00", "start", "bold")
        text(b[0] + 1.5, b[1] + 8, f'Detail {b[2]-b[0]:.0f}×{b[3]-b[1]:.0f} · 표지 {d.get("mark", "")}', 2.0, "#8a3a00")
# 지시선
for ld in D.LEADERS:
    line(ld["pts"], COL["Detail"] if "제작 과정" not in ld["name"] else COL["Basic"], 0.55)
    A(f'<circle cx="{ld["pts"][0][0]}" cy="{ld["pts"][0][1]}" r="0.9" fill="#444"/>')
# 라벨 자리
for lb in D.LABELS:
    _lb = lb.get("box") or lb.get("slot")
    if not _lb:
        continue
    rect(_lb, "#ffffff", "#5a4ab0", 0.35, op=0.45, dash="1.2,0.8")
    text(_lb[0] + 0.8, _lb[1] + 2.8, lb["name"].split("(")[0], 1.9, "#3a2a90")
for ft in D.FLOOR_TEXT:
    rot = 30 if ft["baseline"].startswith("↘") else -30
    text(ft["anchor"][0], ft["anchor"][1], ft["name"], 2.4, "#24465f", "start", "bold", rot=rot)
# 코어 군 외곽(측정 상자)
hc = chk["hero_cluster"]
rect(hc["bbox"], "none", COL["accent"], 0.45, dash="3,1.5")
text(hc["bbox"][0] + 1, hc["bbox"][3] - 1.5, f'히어로 군 상자 {hc["bbox_pct_stage"]}% · 껍질 {hc["hull_pct_stage"]}% · 실루엣 {hc["silhouette_pct_stage"]}%', 2.3, COL["accent"], "start", "bold")
cg = chk["core_group_city"]
rect(cg["bbox"], "none", "#7a1424", 0.4, dash="1,1.2")
text(cg["bbox"][0] + 1, cg["bbox"][1] + 3.2, f'도심·시내 코어 군 상자 {cg["bbox_pct_stage"]}% · 껍질 {cg["hull_pct_stage"]}% · 실루엣 {cg["silhouette_pct_stage"]}%', 2.2, "#7a1424", "start", "bold")
# 틀: 타이틀·패널·푸터
t = D.TITLE["rect"]
poly([(t[0], t[3]), (t[0], t[1] + 30), ((t[0] + t[2]) / 2, t[1]), (t[2], t[1] + 30), (t[2], t[3])], "#fbf1de", COL["accent"], 0.8)
text((t[0] + t[2]) / 2, 56, "ROMAN CONCRETE · ROMA", 9.5, COL["accent"], "middle", "bold")
text((t[0] + t[2]) / 2, 67, "도시 인포그래픽 '로마 편' — 신전 페디먼트 정면 입면", 3.0, "#7a1424", "middle")
text((t[0] + t[2]) / 2, 74, "126.5~293.5 × 10~92 (폭 39.8%)", 2.6, "#7a1424", "middle")
for pn in D.PANELS_PRINT:
    col = COL.get(pn["tier"], "#555555")
    b = pn["rect"]
    rect(b, "#fbf4e6", col, 0.8, op=0.93)
    text(b[0] + 2, b[1] + 6, f'{pn["id"]} {pn["name"]}', 3.0 if pn["id"] != "S" else 2.5, col, "start", "bold")
    text(b[0] + 2, b[1] + 11, f'{pn["tier"]} · {b[2]-b[0]:.0f}×{b[3]-b[1]:.0f}mm = {(b[2]-b[0])*(b[3]-b[1]):,.0f}mm²', 2.3 if pn["id"] != "S" else 2.0, col)
    if pn["id"] == "P2":                                          # 등각 소형 단면 4칸 + 스팬 막대 3줄(기준선 7.1)
        for i, (x0, nm_) in enumerate(zip((302.0, 327.67, 353.33, 379.0), ("아치(비교)", "배럴 볼트", "교차 볼트", "돔"))):
            rect([x0, 32.0, x0 + 23.0, 62.0], "#f6e6c8", col, 0.35)
            A(f'<circle cx="{x0 + 2.5:.2f}" cy="33.5" r="2.0" fill="#3a2a1c"/>')
            text(x0 + 2.5, 34.3, str(i + 1), 2.2, "#ffffff", "middle", "bold")
            text(x0 + 11.5, 58.5, nm_, 2.1, "#2a2060", "middle")
        for i, (L_, nm_) in enumerate(((11.9, "대회랑 8.6 m"), (49.9, "열탕실 약 36 m"), (60.0, "판테온 43.3 m"))):
            y0 = 66.0 + 6.5 * i
            rect([302.0, y0, 302.0 + L_, y0 + 2.5], "#c9b28a")
            text(302.0 + L_ + 2.0, y0 + 2.3, nm_, 2.1, "#2a2060")
    if pn["id"] == "P5":                                          # 3단 계단 + 두 칸(기준선 7.1)
        for i, nm_ in enumerate(("연구", "현장", "적용")):
            x0 = b[0] + i * 30.0
            rect([x0, 520.0 + (2 - i) * 3, x0 + 28.7, 541.0], "#efe0f0", col, 0.35)
            text(x0 + 2, 526.0 + (2 - i) * 3, nm_, 2.4, "#2a2060", "start", "bold")
        rect([b[0], 543.0, b[0] + 44.0, 562.0], "#e8f0e0", col, 0.3)
        rect([b[0] + 46.0, 543.0, b[0] + 90.0, 562.0], "#f4e4e0", col, 0.3)
        text(b[0] + 2, 547.0, "가져올 것", 2.2, "#2a2060", "start", "bold")
        text(b[0] + 48, 547.0, "못 가져올 것", 2.2, "#2a2060", "start", "bold")
    if pn["id"] == "B":
        cw = (b[2] - b[0] - 8) / 6
        for i, nm in enumerate(["재료 준비", "마른 혼합", "물 붓기", "뜨거운 혼합", "다져 넣기", "굳기·석회 알갱이"]):
            x0 = b[0] + 2 + i * (cw + 0.8)
            poly([(x0 + cw / 2, b[1] + 15), (x0 + cw, b[1] + 15 + cw * 0.29), (x0 + cw / 2, b[1] + 15 + cw * 0.58), (x0, b[1] + 15 + cw * 0.29)], "#f6e6c8", COL["accent"], 0.4)
            A(f'<circle cx="{x0 + 4:.2f}" cy="{b[1] + 38:.2f}" r="3" fill="{COL["accent"]}"/>')
            text(x0 + 4, b[1] + 39.1, str(i + 1), 3.0, "#ffffff", "middle", "bold")
            text(x0 + 8.5, b[1] + 39.0, nm, 2.3, "#5a1420", "start", "bold")
        line([(b[0] + 4, b[1] + 50), (b[2] - 6, b[1] + 50)], "#7a5a40", 0.4, dash="1.5,1")
        text(b[0] + 4, b[1] + 55, "등각 소형 장면 6칸 + 바닥 화살표 + 시간 화살표(피라미드 CHANGE OF THE FORM 문법)", 2.1, "#7a5a40")
    if pn["id"] == "S":
        rect([b[0] + 3, b[1] + 15, b[0] + 6, b[1] + 19], "#9aa6ad")
        text(b[0] + 7, b[1] + 18.5, "현대 약 100년", 2.0, "#2a4a50")
        rect([b[0] + 3, b[1] + 22, b[0] + 63, b[1] + 26], "#c9b28a")
        text(b[0] + 4, b[1] + 25.3, "로마 2,000년+", 2.0, "#4a3410", "start", "bold")
# 짝 표지(사양 mark·mark_pt·PAIR_MARKS 점): A~D·1~4
try:
    _pm = D.pair_marks() if hasattr(D, "pair_marks") else []
except Exception:
    _pm = []
for _m in _pm:
    _c = _m["pt"]
    A(f'<circle cx="{_c[0]:.2f}" cy="{_c[1]:.2f}" r="2.0" fill="#3a2a1c" stroke="#ffffff" stroke-width="0.3"/>')
    text(_c[0], _c[1] + 0.8, _m["glyph"], 2.2, "#ffffff", "middle", "bold")
rect(D.FOOTER["rect"], "#efe2c6", "#8a7a60", 0.4, dash="2,1")
text(D.FOOTER["rect"][0] + 3, D.FOOTER["rect"][1] + 8, "내부 골격 미리보기(인쇄 지면 아님) · 무대 = STAGE 하나(확장 0) · 패널 %s · 랜드마크 %d · 티어 색은 이 내부 도면에만" % ("·".join(p["id"] for p in D.PANELS_PRINT), len(D.LANDMARKS)), 2.6, "#5a4a30")
A('</g></svg>')
open(sys.argv[2], "w", encoding="utf-8").write("\n".join(out))
print("미리보기 SVG 저장:", sys.argv[2])
