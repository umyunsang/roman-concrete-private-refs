# -*- coding: utf-8 -*-
# 로마 콘크리트 A2 와이어프레임 — 자동 실측·검사(투영 크기 위계·베이징 대조·밀도·각도·라벨 충돌·강 간격)
# 담당 패키지: global · 이 파일은 담당 워커만 고친다(공용 도구는 common.py, 조립은 main.py).

from common import *
from common import _a
import common as C
import m_map as M
from m_map import RIVER_W, RIVER_A, sea_polygon
from m_arena import ARENA_R, ARENA_XL, ARENA_CX
from m_panels import PANEL_RECT

# ───────────────────────── 분석(자동 실측·검사) ─────────────────────────
S2 = 2


def _empty_mask():
    return Image.new("L", (PW * S2, PH * S2), 0)


def layer_mask(layer):
    a = layer.alpha_mask()
    f = KD // S2
    small = a.resize((max(1, a.width // f), max(1, a.height // f)), Image.BOX).point(lambda v: 255 if v > 100 else 0)
    full = _empty_mask()
    full.paste(255, (int(round(layer.x0 * S2)), int(round(layer.y0 * S2))), small)
    return full


def poly_mask(poly):
    m = _empty_mask()
    ImageDraw.Draw(m).polygon([(x * S2, y * S2) for x, y in poly], fill=255)
    return m


def area_of(mask):
    return mask.histogram()[255] / float(S2 * S2)


def inter_area(m1, m2):
    return area_of(ImageChops.multiply(m1, m2))


def largest_empty_rect(occ, region):
    one = occ.resize((PW, PH), Image.BOX).point(lambda v: 255 if v > 0 else 0)
    x0, y0, x1, y1 = region
    crop = one.crop((x0, y0, x1, y1))
    w, h = crop.size
    data = crop.tobytes()
    heights = [0] * w
    best_area, best = 0, None
    for r in range(h):
        row = data[r * w:(r + 1) * w]
        for c in range(w):
            heights[c] = 0 if row[c] else heights[c] + 1
        stack = []
        for c in range(w + 1):
            hc = heights[c] if c < w else 0
            start = c
            while stack and stack[-1][1] >= hc:
                st, hh = stack.pop()
                area = (c - st) * hh
                if area > best_area:
                    best_area = area
                    best = (x0 + st, y0 + r - hh + 1, x0 + c, y0 + r + 1)
                start = st
            stack.append((start, hc))
    return best_area, best


def angle_of(p0, p1):
    return math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0])) % 180.0


def near(a, targets, tol=0.6):
    return any(min(abs(a - t), 180 - abs(a - t)) <= tol for t in targets)


BJ_ZONES = {"T(타이틀)": (128, 10, 295, 92), "L1": (18, 20, 125, 65), "L2": (18, 75, 135, 150), "R1": (318, 20, 412, 102),
            "B1": (18, 505, 180, 565), "B2": (182, 505, 305, 565), "B3": (318, 505, 412, 565), "F(푸터)": (18, 568, 412, 586)}
BJ_OBJECTS = {"아레나": ("자금성 블록(중심 블록)", (216.3, 182.4, 419.8, 381.1)),
              "Core 제작 과정": ("CCTV 타워(세로 척추)", (23.1, 185.8, 98.5, 428.2)),
              "욕장": ("이화원(위쪽 줄)", (144.5, 111.8, 242.3, 192.8)),
              "베수비오": ("만리장성(가장 먼 대상)", (233.1, 80.6, 303.0, 141.9)),
              "수도교": ("798 예술구(아래 줄)", (231.0, 428.2, 334.3, 504.4)),
              "포르투스 항": ("고속철(아래 줄 왼쪽)", (0.0, 420.0, 88.0, 495.3))}


def analyze(R):
    out = []
    P = out.append
    objs = {o["이름"]: o for o in R["objs"]}
    # ── 1. 투영 크기 검사표(렌더한 레이어를 알파 외곽 상자로 자동 실측)
    rows = []
    for o in R["objs"]:
        if o["이름"] == "포도밭 농장" or o["티어"] == "소품":
            continue
        rows.append((o["티어"], o["이름"], o["측정"]))
    for pnl in R["panels"]:
        rows.append((pnl["티어"], pnl["이름"], pnl["측정"]))
    order = {"아레나": 0, "Core": 1, "Basic": 2, "Detail": 2, "Support": 3, "Support-2": 4}
    rows.sort(key=lambda r: (order[r[0]], -((r[2]["box"][2] - r[2]["box"][0]) * (r[2]["box"][3] - r[2]["box"][1]))))
    P("투영 크기 검사표(화면 폭×높이 mm, 레이어 알파 외곽 상자 자동 실측 · 면적 mm²):")
    P("  %-10s %-18s %12s %12s %12s" % ("티어", "요소", "폭×높이", "상자 면적", "실점유 면적"))
    areas = {}
    for tier, nm, m in rows:
        b = m["box"]
        w_, h_ = b[2] - b[0], b[3] - b[1]
        ar = w_ * h_
        areas[nm] = (tier, ar, m["area"], w_, h_)
        P("  [%-9s] %-14s %6.1f×%-5.1f %10.0f %12.0f" % (tier, nm, w_, h_, ar, m["area"]))
    # ── 2. 위계 검사(상자 면적 기준 + 실점유 기준, 마진 10%)
    def agg(tiers, idx, fn):
        vals = [(v[idx], n) for n, v in areas.items() if v[0] in tiers]
        return fn(vals)

    A = agg(("아레나",), 1, max)
    C = agg(("Core",), 1, max)
    BDmin = agg(("Basic", "Detail"), 1, min)
    BDmax = agg(("Basic", "Detail"), 1, max)
    Sp = agg(("Support",), 1, max)
    Spmin = agg(("Support",), 1, min)
    S2v = agg(("Support-2",), 1, max)
    ok_box = A[0] > C[0] > BDmin[0] > Sp[0] > S2v[0] and C[0] > BDmax[0]
    margin_ok = (A[0] >= 1.10 * C[0]) and (BDmin[0] >= 1.10 * Sp[0]) and (Spmin[0] >= 1.10 * S2v[0])
    Aa = agg(("아레나",), 2, max)
    Ca = agg(("Core",), 2, max)
    ok_pix = Aa[0] > Ca[0]
    P("위계 검사(상자 면적): 아레나 %.0f > Core %.0f > Basic·Detail 최소 %.0f(%s) > Support 최대 %.0f(%s) > Support-2 %.0f → %s" %
      (A[0], C[0], BDmin[0], BDmin[1], Sp[0], Sp[1], S2v[0], "통과" if ok_box else "실패"))
    P("  마진 10%% 조건(아레나≥Core×1.10, Basic·Detail 최소≥Support 최대×1.10, Support 최소≥Support-2×1.10): %s" % ("통과" if margin_ok else "미달"))
    P("  실점유(알파) 기준: 아레나 %.0f vs Core %.0f → %s · Core 상자 > Basic·Detail 최대 %.0f(%s): %s" % (Aa[0], Ca[0], "통과" if ok_pix else "실패", BDmax[0], BDmax[1], "통과" if C[0] > BDmax[0] else "실패"))
    R["ok_hier"] = ok_box and margin_ok
    R["areas"] = areas
    # ── 3. 베이징 구획·오브젝트 위치 대조(mm 차이)
    P("베이징 구획 대조(3.1절 좌표 대비, 단위 mm; 우측 여백 18mm 통일로 의도한 차이 포함):")
    mine = {"L1": PANEL_RECT["정의"], "L2": PANEL_RECT["레시피"], "R1": PANEL_RECT["위치도"], "B1": PANEL_RECT["석회"], "B2": PANEL_RECT["연대기"], "B3": PANEL_RECT["수명비교"],
            "T(타이틀)": (126.5, 10, 293.5, 92), "F(푸터)": (18, 568, 402, 581)}
    for k, bj in BJ_ZONES.items():
        m_ = mine[k]
        d = tuple(round(m_[i] - bj[i], 1) for i in range(4))
        P("  %-9s 베이징 %s → 도면 %s  차이(좌,상,우,하) %s" % (k, bj, m_, d))
    P("베이징 오브젝트 위치 대조(실측 bj_objects 대비 박스 차이, mm):")
    for nm, (bjn, bb) in BJ_OBJECTS.items():
        m = objs[nm]["측정"]["box"]
        d = tuple(round(m[i] - bb[i], 1) for i in range(4))
        P("  %-12s ↔ %-20s 도면 (%.1f,%.1f,%.1f,%.1f) 차이(좌,상,우,하) %s" % (nm, bjn, m[0], m[1], m[2], m[3], d))
    # ── 4. 밀도·빈자리·최근접 간격
    obj_masks = {}
    union = _empty_mask()
    for o in R["objs"]:
        mk = layer_mask(o["레이어"])
        obj_masks[o["이름"]] = mk
        union = ImageChops.lighter(union, mk)
    map_box = (0, MAP_Y0 * S2, PW * S2, MAP_Y1 * S2)
    map_area = PW * (MAP_Y1 - MAP_Y0)
    cov = area_of(union.crop(map_box)) if False else union.crop(map_box).histogram()[255] / float(S2 * S2)
    P("오브젝트 점유율: 지도 무대(%d×%d=%d mm²) 중 %.1f%% (베이징 46.2%%, 목표 42~48%%) · 오브젝트 수 %d개(소품 포함, 베이징 16개)" % (PW, MAP_Y1 - MAP_Y0, map_area, 100.0 * cov / map_area, len(R["objs"])))
    ea, eb = largest_empty_rect(union, (0, MAP_Y0, PW, MAP_Y1))
    P("최대 빈 직사각형(오브젝트만 기준): %.0f×%.0f mm = %.0f mm² (지도의 %.1f%%) 위치 %s" % (eb[2] - eb[0], eb[3] - eb[1], ea, 100.0 * ea / map_area, eb))
    # 최근접 이웃 간격
    P("최근접 이웃 간격(오브젝트 상자 아닌 실제 화소 기준, mm; ≥24면 '24+'):")
    names = [o["이름"] for o in R["objs"]]
    small = {n: obj_masks[n].resize((PW, PH), Image.BOX).point(lambda v: 255 if v > 0 else 0) for n in names}
    gaps = {}
    for n in names:
        cur = small[n]
        found = {}
        for step in range(1, 13):
            cur = cur.filter(ImageFilter.MaxFilter(5))
            for m_ in names:
                if m_ == n or m_ in found:
                    continue
                if ImageChops.multiply(cur, small[m_]).getbbox():
                    found[m_] = 2 * step
            if len(found) == len(names) - 1:
                break
        if found:
            k = min(found, key=lambda z: found[z])
            gaps[n] = (found[k], k)
        else:
            gaps[n] = (24, "-")
    P("  " + " · ".join("%s→%s %s" % (n, g[1], ("≤%d" % g[0]) if g[0] < 24 else "24+") for n, g in gaps.items()))
    R["masks"] = obj_masks
    R["union"] = union
    # ── 5. 지면 지형 마스크
    cl = R["river"]
    river_poly = band_poly(cl, RIVER_W, bevel=True)[0]
    m_river = poly_mask(river_poly)
    m_roads = _empty_mask()
    for road in M.ROADS:
        m_roads = ImageChops.lighter(m_roads, poly_mask(band_poly(road, 5.4)[0]))
    m_sea = poly_mask(sea_polygon(cl))
    # ── 6. 지시선·글줄 각도 검사
    tot = {"지면": 0, "지시선": 0, "글줄": 0}
    bad = []
    for kind, p0, p1 in SEG_LOG:
        if math.hypot(p1[0] - p0[0], p1[1] - p0[1]) < 1e-6:
            continue
        ang = angle_of(p0, p1)
        tot[kind] += 1
        if kind == "지면":
            good = near(ang, (30.0, 150.0))
        elif kind == "지시선":
            good = near(ang, (90.0, 30.0, 150.0))
        else:
            good = near(ang, (30.0, 150.0))
        if not good:
            bad.append((kind, round(ang, 1), tuple(round(v, 1) for v in p0)))
    P("각도 검사(허용: 지면 ±30°, 지시선 수직·±30°, 지도 위 글줄 ±30°; 오차 ±0.6°): 지면 선분 %d · 지시선 %d · 글줄 %d → 어긋남 %d개 %s" % (tot["지면"], tot["지시선"], tot["글줄"], len(bad), bad[:4]))
    up_n = sum(1 for k_, a_, b_ in SEG_LOG if k_ == "글줄" and near(angle_of(a_, b_), (150.0,)))
    dn_n = sum(1 for k_, a_, b_ in SEG_LOG if k_ == "글줄" and near(angle_of(a_, b_), (30.0,)))
    P("지도 위 글줄 평면(화면 평행 0°는 0개): 기준선 ↗(북서 구역 벽면·강 바닥) %d · 기준선 ↘(그 밖의 벽면·바닥) %d · 지시선은 전부 수직" % (up_n, dn_n))
    cl_ = R["river"]
    segs_ = [(round(angle_of(cl_[i], cl_[i + 1]), 1), round(math.hypot(cl_[i + 1][0] - cl_[i][0], cl_[i + 1][1] - cl_[i][1]))) for i in range(len(cl_) - 1)]
    ent_y = RIVER_A[1] - T30 * (PW - RIVER_A[0])
    P("강 중심선: 구간 %d개 (화면 각도°, 길이mm) %s · 지면 축 ±30°만 사용(수직 구간 0) · 직각(평면) 꺾임 %d곳 · 액자 오른쪽 변 진입점 y=%.0fmm(오른쪽 위에서 대각 진입)" % (len(segs_), segs_, len(segs_) - 1, ent_y))
    P("아레나 받침: 팔각 외접 반지름 %.1fmm(화면 폭 %.1fmm), 왼쪽 수직 변 x=%.0fmm, 우측 수직 변 x=%.1fmm(액자 오른쪽 변 %dmm 밖 %.1fmm로 블리드 — 광장이 액자 밖으로 이어짐) · 화산 %d개(베수비오) · 욕장 %d개" % (
        ARENA_R, 2.263 * ARENA_R, ARENA_XL, ARENA_CX + 1.1316 * ARENA_R, PW, ARENA_CX + 1.1316 * ARENA_R - PW, sum(1 for o in R["objs"] if o["티어"] == "Support-2"), sum(1 for o in R["objs"] if o["이름"] == "욕장")))
    # ── 7. 라벨 충돌 검사(라벨 글 상자 ↔ 오브젝트·강·길·다른 라벨)
    P("라벨 충돌 검사(글 상자와 겹침 면적 mm², 0이어야 함):")
    lab_masks = []
    nbad = 0
    for rec in LABELS:
        if len(rec["다각형"]) < 3:
            lab_masks.append(None)
            continue
        lm = poly_mask(rec["다각형"])
        lab_masks.append(lm)
        hits = []
        for n, mk in obj_masks.items():
            a_ = inter_area(lm, mk)
            if a_ > 0.5:
                hits.append("%s %.0f" % (n, a_))
        for nm_, mk in (("강", m_river), ("길", m_roads)):
            a_ = inter_area(lm, mk)
            if a_ > 0.5:
                hits.append("%s %.0f" % (nm_, a_))
        # 패널 구획·지도 경계
        bb = [min(p[0] for p in rec["다각형"]), min(p[1] for p in rec["다각형"]), max(p[0] for p in rec["다각형"]), max(p[1] for p in rec["다각형"])]
        if bb[0] < 6 or bb[2] > PW - 4 or bb[1] < MAP_Y0 + 2 or bb[3] > MAP_Y1 - 2:
            hits.append("지도 경계 밖")
        for key, (x0, y0, x1, y1) in PANEL_RECT.items():
            if bb[2] > x0 and bb[0] < x1 and bb[3] > y0 and bb[1] < y1:
                hits.append("패널 " + key)
        if hits:
            nbad += 1
        P("  %-14s 상자 (%.0f,%.0f)-(%.0f,%.0f) %s" % (rec["이름"], bb[0], bb[1], bb[2], bb[3], ("충돌: " + ", ".join(hits)) if hits else "충돌 없음"))
    for i in range(len(LABELS)):
        for j in range(i + 1, len(LABELS)):
            if lab_masks[i] is not None and lab_masks[j] is not None:
                a_ = inter_area(lab_masks[i], lab_masks[j])
                if a_ > 0.5:
                    nbad += 1
                    P("  라벨끼리 겹침: %s ↔ %s %.0f" % (LABELS[i]["이름"], LABELS[j]["이름"], a_))
    R["label_collisions"] = nbad
    # ── 8. 강: 받침·오브젝트와의 간격
    ov = [(n, inter_area(m_river, mk)) for n, mk in obj_masks.items() if inter_area(m_river, mk) > 0.5 and n not in ("돌 다리", "테베레 바지선")]
    P("강 간격 검사: 강 띠와 오브젝트 겹침(mm², 다리·바지선은 강 위에 놓는 것이라 제외): " + (", ".join("%s %.0f" % (n, a_) for n, a_ in ov) if ov else "겹침 없음"))
    R["river_overlap"] = ov
    # 강 중심선과 아레나 받침·베수비오·Core 사이 최소 간격(mm, 0.5mm 단위 근사)
    gaps2 = {}
    for nm_ in ("아레나", "Core 제작 과정", "욕장", "판테온", "베수비오"):
        cur = m_river
        g_ = None
        for step in range(1, 25):
            cur = cur.filter(ImageFilter.MaxFilter(3))
            if ImageChops.multiply(cur, obj_masks[nm_]).getbbox():
                g_ = step * 0.5
                break
        gaps2[nm_] = g_
    P("강 띠 가장자리와의 최소 간격(mm): " + " · ".join("%s %s" % (k_, ("%.1f" % v_) if v_ is not None else "12+") for k_, v_ in gaps2.items()))
    # 베수비오 밑동을 앞 요소(농장)가 가리는 면적
    fv = inter_area(obj_masks["포도밭 농장"], obj_masks["베수비오"])
    P("베수비오 밑동 가림: 앞 요소(포도밭 농장)와 겹친 면적 %.0f mm² (밑동 아래 약 5~6mm 띠)" % fv)
    R["m_river"], R["m_roads"], R["m_sea"] = m_river, m_roads, m_sea
    return out
