# -*- coding: utf-8 -*-
"""최종 배치 사양 미리보기 SVG(배치 골격 도면). 사용: python final_spec_svg.py <data_dir> <out.svg>"""
import json
import math
import sys

sys.path.insert(0, sys.argv[1])
import final_spec_data as D  # noqa: E402

chk = json.load(open(sys.argv[1] + "/final_spec_check.json"))
out = []
A = out.append
FONT = "Apple SD Gothic Neo, AppleSDGothicNeo, sans-serif"


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
    A(f'<text x="{x:.2f}" y="{y:.2f}" font-family="{FONT}" font-size="{size}" fill="{col}" text-anchor="{anchor}" font-weight="{weight}"{tr}>{s}</text>')


def line(p, col, sw=0.4, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    A(f'<polyline points="{pts(p)}" fill="none" stroke="{col}" stroke-width="{sw}"{d}/>')


def band(p, w):
    import final_spec_check  # noqa: F401  (지연 import 회피용 자리)


def band_poly(pp, w):
    left, right = [], []
    n = len(pp)
    dirs = []
    for i in range(n - 1):
        dx, dy = pp[i + 1][0] - pp[i][0], pp[i + 1][1] - pp[i][1]
        L = math.hypot(dx, dy)
        dirs.append((dx / L, dy / L))
    for i in range(n):
        d = dirs[0] if i == 0 else dirs[-1] if i == n - 1 else None
        if d:
            nn = (-d[1], d[0])
            left.append((pp[i][0] + nn[0] * w / 2, pp[i][1] + nn[1] * w / 2))
            right.append((pp[i][0] - nn[0] * w / 2, pp[i][1] - nn[1] * w / 2))
        else:
            a, b = dirs[i - 1], dirs[i]
            na, nb = (-a[1], a[0]), (-b[1], b[0])
            mx, my = na[0] + nb[0], na[1] + nb[1]
            ml = math.hypot(mx, my)
            mx, my = mx / ml, my / ml
            k = (w / 2) / (mx * na[0] + my * na[1])
            left.append((pp[i][0] + mx * k, pp[i][1] + my * k))
            right.append((pp[i][0] - mx * k, pp[i][1] - my * k))
    return left + right[::-1]


A('<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="594mm" viewBox="0 0 420 594">')
A('<defs><clipPath id="poster"><rect x="0" y="0" width="420" height="594"/></clipPath></defs>')
A('<g clip-path="url(#poster)">')
rect([0, 0, 420, 594], "#e7d0a0")
# 지도 무대 지면
rect(D.STAGE, "#e2c896")
# 바다(하단 띠 밑 연장 포함)
poly(D.SEA_UNDER_BAND, "#8caec8", op=0.35)
poly(D.SEA, "#8caec8")
line(D.COAST, "#5a7c98", 0.8)
# 녹지·밭 소품 면
for pr in D.MAP_PROPS:
    if pr["zone"] in ("왼쪽 가운데", "오른쪽 아래"):
        rect(pr["box"], "#a9b77a", op=0.55)
# 강
for s in D.RIVER:
    poly(band_poly(s["pts"], s["w"]), "#70aad2", "#42709c", 0.3)
# 길
for rd in D.ROADS:
    poly(band_poly(rd["pts"], rd["w"]), "#c8b088" if rd["w"] < 15 else "#b89c74", "#8a7050", 0.25)
# 코어 군 실루엣 외곽(점선)
# 셀
for k in range(1, 8):
    v = D.cell_verts(k)
    poly([v["T"], v["R"], v["B"], v["L"]], "#f6e6c8", "#c82236", 0.6)
    cx, cy = D.cell_center(k)
    st = D.CELL_STEP[k - 1]
    A(f'<circle cx="{cx - 30:.2f}" cy="{cy:.2f}" r="4.2" fill="#c82236"/>')
    text(cx - 30, cy + 1.6, str(st), 4.4, "#ffffff", "middle", "bold")
    text(cx - 23, cy + 1.4, D.STEP_NAME[st] + (" ②" if k == 5 else ""), 3.4, "#7a1424", "start", "bold")
    text(cx - 23, cy + 6.0, f"c{k} · 폭 {D.CELL_W:.0f}", 2.4, "#7a5a40")
for b in D.BOARDS:
    p = D.board_poly(b["cell"], b["edge"], b["h"], b.get("frac", (0.0, 1.0)))
    poly(p, "#f0dcb2" if b["h"] < 30 else "#e9c9a0", "#78463a", 0.35)
bp = D.board_poly(1, "UL", D.CORE_BOARD_H)
text((bp[0][0] + bp[1][0]) / 2 - 2, (bp[0][1] + bp[1][1]) / 2 - 18, "CORE", 7.0, "#a8182c", "middle", "bold", rot=-30)
# 아레나
o = D.arena_oct()
for k in (7, 0, 1):
    a, b = o[k], o[(k + 1) % 8]
    poly([a, b, (b[0], b[1] + D.ARENA_T), (a[0], a[1] + D.ARENA_T)], "#8a6a46", "#5a4028", 0.3)
poly(o, "#d4c0a0", "#5a4028", 0.6)
ax, ay = D.ARENA_C
r_ = D.ARENA_RING
A(f'<ellipse cx="{ax:.2f}" cy="{ay:.2f}" rx="{1.2247*r_:.2f}" ry="{0.7071*r_:.2f}" fill="#e8dcc0" stroke="#7a5a3a" stroke-width="0.5"/>')
A(f'<ellipse cx="{ax:.2f}" cy="{ay:.2f}" rx="{1.2247*0.42*D.ARENA_R:.2f}" ry="{0.7071*0.42*D.ARENA_R:.2f}" fill="#c49a68" stroke="#7a5a3a" stroke-width="0.4"/>')
frag = [D.arena_ring_pt(t, 0) for t in range(270, 361, 6)] + [D.arena_ring_pt(t, D.ARENA_FRAG_H) for t in range(360, 269, -6)]
poly(frag, "#d8c4a0", "#6a4a2a", 0.4, op=0.92)
back = [D.arena_ring_pt(t, 0) for t in range(225, 271, 5)] + [D.arena_ring_pt(t, D.ARENA_BACK_H) for t in range(270, 224, -5)]
poly(back, "#d0bc98", "#6a4a2a", 0.3, op=0.85)
text(ax, ay + 50, "콜로세움(완공) — 가장 큰 단일 오브젝트", 3.6, "#4a2c14", "middle", "bold")
# 코어 군 디테일
for d in D.CORE_DETAILS:
    rect(d["box"], "#efb07a", "#a0562a", 0.3, op=0.75)
    text((d["box"][0] + d["box"][2]) / 2, (d["box"][1] + d["box"][3]) / 2 + 1, d["name"].split("(")[0], 2.2, "#5a2a0a", "middle")
# Support
for s in D.SUPPORTS + D.SUPPORT2:
    col = "#2e933c" if s["tier"] == "Support" else "#6e8a80"
    rect(s["box"], "#d8ebc8" if s["tier"] == "Support" else "#d6dcd6", col, 0.6, op=0.85)
    b = s["box"]
    nm = s["name"].split("(")[0]
    text((b[0] + b[2]) / 2, (b[1] + b[3]) / 2 - 2, nm, 3.0, "#16642c", "middle", "bold")
    text((b[0] + b[2]) / 2, (b[1] + b[3]) / 2 + 3, f"{b[2]-b[0]:.0f}×{b[3]-b[1]:.0f}mm", 2.4, "#16642c", "middle")
# 포르투스 세부 앵커
A('<polygon points="' + pts([(54 + 14 * math.cos(math.radians(a)) * 1.0, 380 + 14 * math.sin(math.radians(a)) * 0.58) for a in range(0, 360, 60)]) + '" fill="#9cc4dc" stroke="#7a3a2a" stroke-width="0.5"/>')
A('<path d="M 10 418 A 22 13 0 1 1 48 404" fill="none" stroke="#7a5a3a" stroke-width="1.6"/>')
A('<rect x="12" y="414" width="4" height="12" fill="#e8dcc0" stroke="#5a4028" stroke-width="0.3"/>')
for pr in D.MAP_PROPS:
    if pr["zone"] in ("바다", "베수비오"):
        rect(pr["box"], "#d9c7a3", "#6a5030", 0.3, op=0.8)
        text((pr["box"][0] + pr["box"][2]) / 2, (pr["box"][1] + pr["box"][3]) / 2 + 1, pr["name"].split("(")[0], 2.2, "#3a2a1a", "middle")
# 확대 창과 지시선
mc, md = D.MAGNIFIER["c"], D.MAGNIFIER["d"]
A(f'<circle cx="{mc[0]}" cy="{mc[1]}" r="{md/2}" fill="#fbf1de" stroke="#de7010" stroke-width="1.2"/>')
for i, (dx, dy, rr) in enumerate([(-14, -8, 5), (10, -14, 4), (-4, 12, 6), (16, 8, 3.5), (-20, 14, 3)]):
    A(f'<circle cx="{mc[0]+dx}" cy="{mc[1]+dy}" r="{rr}" fill="#ffffff" stroke="#9a8a70" stroke-width="0.4"/>')
line([(mc[0] - 22, mc[1] - 30), (mc[0] - 2, mc[1] + 2), (mc[0] + 14, mc[1] + 30)], "#3a2a1a", 0.5)
text(mc[0], mc[1] + md / 2 - 6, "확대 창 Ø76", 2.8, "#963a00", "middle", "bold")
for ld in D.LEADERS:
    line(ld["pts"], "#de7010", 0.5)
    A(f'<circle cx="{ld["pts"][0][0]}" cy="{ld["pts"][0][1]}" r="0.9" fill="#de7010"/>')
# 라벨 자리
for lb in D.LABELS:
    rect(lb["box"], "#ffffff", "#5a4ab0", 0.35, op=0.35, dash="1.2,0.8")
    text(lb["box"][0] + 0.8, lb["box"][1] + 3.0, lb["name"].split("(")[0], 2.0, "#3a2a90")
for ft in D.FLOOR_TEXT:
    rot = -30 if ft["baseline"].startswith("↗") else 30
    text(ft["anchor"][0], ft["anchor"][1], ft["name"], 2.8, "#2a4a6a", "start", "bold", rot=rot)
# 틀: 타이틀·패널·푸터
t = D.TITLE["rect"]
poly([(t[0], t[3]), (t[0], t[1] + 30), ((t[0] + t[2]) / 2, t[1]), (t[2], t[1] + 30), (t[2], t[3])], "#fbf1de", "#c82236", 0.8)
text((t[0] + t[2]) / 2, 56, "ROMAN CONCRETE", 11, "#c82236", "middle", "bold")
text((t[0] + t[2]) / 2, 68, "타이틀: 신전 페디먼트 정면 입면 126.5~293.5 × 10~92", 3.0, "#7a1424", "middle")
for pn in D.PANELS:
    col = "#4636a0" if pn["tier"] == "Basic" else "#de7010"
    rect(pn["rect"], "#fbf4e6", col, 0.8, op=0.9)
    text(pn["rect"][0] + 3, pn["rect"][1] + 7, f'{pn["id"]} {pn["name"]}', 3.2, col, "start", "bold")
    b = pn["rect"]
    text(b[0] + 3, b[1] + 12.5, f'{pn["tier"]} · {b[2]-b[0]:.0f}×{b[3]-b[1]:.0f}mm', 2.6, col)
rect(D.FOOTER["rect"], "#efe2c6", "#8a7a60", 0.4, dash="2,1")
text(D.FOOTER["rect"][0] + 3, D.FOOTER["rect"][1] + 8, "푸터 18~402 × 568~581", 3.0, "#5a4a30")
# 코어 군 실루엣 외곽선(검사 결과의 상자)
cb = chk["core_group"]["bbox"]
rect(cb, "none", "#c82236", 0.5, dash="3,1.5")
cg = chk["core_group"]
text(cb[0] + 2, cb[3] - 2, f'코어 군 상자 {cg["bbox_wh"][0]:.0f}×{cg["bbox_wh"][1]:.0f} = 무대의 {cg["bbox_pct_stage"]}% · 껍질 {cg["hull_pct_stage"]}% · 실루엣 {cg["silhouette_pct_stage"]}%', 2.6, "#a8182c", "start", "bold")
A('</g></svg>')
open(sys.argv[2], "w").write("\n".join(out))
print("ok", sys.argv[2])
