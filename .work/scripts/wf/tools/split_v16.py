# -*- coding: utf-8 -*-
# 단일 파일 wireframe_v16.py → 담당 영역별 모듈(wf/v16/)로 분할. 그리는 코드는 한 줄도 바꾸지 않고 줄 범위만 옮긴다.
import os, sys
SRC = sys.argv[1]
DST = sys.argv[2]
L = open(SRC, encoding="utf-8").read().split("\n")


def rng(a, b):
    return "\n".join(L[a - 1:b])


USED = set()


def take(*ranges):
    out = []
    for a, b in ranges:
        for i in range(a, b + 1):
            if i in USED:
                raise SystemExit("중복 배정 줄 %d" % i)
            USED.add(i)
        out.append(rng(a, b))
    return "\n".join(out)


def head(desc, owner, extra=""):
    return ("# -*- coding: utf-8 -*-\n# 로마 콘크리트 A2 와이어프레임 — %s\n# 담당 패키지: %s · 이 파일은 담당 워커만 고친다(공용 도구는 common.py, 조립은 main.py).\n%s\n" % (desc, owner, extra))


STAR = "from common import *\nfrom common import _a\nimport common as C\n"

# ── common.py ──
common = head("공용 도구(글꼴·팔레트·레이어·등각 글자·라벨 규격·소품·받침)", "global",
              "# - 원본: wireframe_v16.py(v15 → v16 비평 반영본)를 모듈로 나눈 것. 최종 모델 수준은 LocalBanana 디오라마, 이 도면은 배치 도식이다.") + \
    take((8, 43), (44, 92), (93, 255), (256, 318), (319, 427), (428, 559), (563, 567), (576, 588), (841, 881), (883, 889),
         (1183, 1188), (1429, 1449), (1540, 1543), (1670, 1671), (2079, 2087)) + "\nVERSION = \"v16\"\n"

# ── m_core.py ──
core = head("Core: 로마 콘크리트 제작 과정(신문식 셀 체인)", "core") + STAR + "\n" + \
    take((800, 821), (1144, 1182), (1189, 1428)) + '''

# ───────────────────────── 배치 명세(main.py가 모아 z 순서로 그린다) ─────────────────────────
def objects():
    return [dict(z=60, name="Core 제작 과정", tier="Core", region=(8, 125, 170, 380), fn=draw_core, args=())]


def labels():
    return []


def extra_labels(LB):
    pass
'''

# ── m_arena.py ──
arena = head("아레나(콜로세움) — LocalBanana 참조 디오라마 형태", "arena") + STAR + "\n" + \
    take((826, 830), (882, 882), (890, 1143)) + '''

# ───────────────────────── 배치 명세 ─────────────────────────
def objects():
    return [dict(z=50, name="아레나", tier="아레나", region=(ARENA_XL - 8, 170, 448, 392), fn=draw_arena, args=(), bleed=True)]


def labels():
    return [dict(order=10, kind="label", name="아레나", T=(236.0, 306.0), M=M_WALL_DN, mode="above", side="R", col=C_ARENA_T,
                 en=["COLOSSEUM"], ko="콜로세움 아레나", sup=None,
                 body=["겉은 석회화, 속과 기초는", "콘크리트로 채움", "무너짐의 주원인:", "지반·석재 반출·관리 부재"], gap=2.4)]


def extra_labels(LB):
    pass
'''

# ── m_support_bottom.py ──
sb = head("Support(아래 줄): 수도교·포르투스 항·카이킬리아 메텔라 무덤", "support_bottom") + STAR + "\n" + \
    take((1624, 1669), (1672, 1715), (1716, 1769)) + '''

# ───────────────────────── 배치 명세 ─────────────────────────
POS = {"aqueduct": (270, 425, 68), "metella": (388, 440, 64), "portus": (150, 455, 64)}


def objects():
    ax, ay, aw = POS["aqueduct"]
    mx, my, mw = POS["metella"]
    qx, qy, qw = POS["portus"]
    return [
        dict(z=80, name="수도교", tier="Support", region=(ax - 46, ay - 46, ax + 46, ay + 36), fn=draw_aqueduct, args=(ax, ay, aw)),
        dict(z=90, name="카이킬리아 메텔라 무덤", tier="Support", region=(mx - 46, my - 46, mx + 46, my + 36), fn=draw_metella, args=(mx, my, mw)),
        dict(z=100, name="포르투스 항", tier="Support", region=(qx - 42, qy - 40, qx + 62, qy + 36), fn=draw_portus, args=(qx, qy, qw)),
    ]


def labels():
    return [
        dict(order=40, kind="label", name="수도교", T=(270.0, 443.5), M=M_WALL_DN, mode="below", side="L", col=C_SUP_T,
             en=["AQUA CLAUDIA"], ko="아쿠아 클라우디아", sup=None, body=["석재 아치에 하드리아누스기", "벽돌면 콘크리트로 보수한", "구간(붉은 두 칸)"], gap=9.5),
        dict(order=50, kind="label", name="메텔라 무덤", T=(356.0, 440.0), M=M_WALL_DN, mode="above", side="R", col=C_SUP_T,
             en=["CAECILIA METELLA"], ko="카이킬리아 메텔라 무덤", sup=None,
             body=["지름 29m 콘크리트 드럼", "젖을 때마다 류사이트가", "녹아 접합부를 다시 짬", "※ 알갱이 치유와는 다름"], gap=2.4),
        dict(order=60, kind="label", name="포르투스 항", T=(150.0, 436.0), M=M_WALL_DN, mode="above", side="R", col=C_SUP_T,
             en=["PORTUS"], ko="포르투스 항", sup=None,
             body=["트라야누스 육각 내항", "(약 100~112년)", "방파제 모르타르: 로마", "근교+포추올리 화산재", "바닷물은 항구 구조물만"], gap=2.4, plate=True),
    ]


def extra_labels(LB):
    pass
'''

# ── m_map.py ──
setup_roads = take((2122, 2147)).replace('POS["aqueduct"]', 'SB.POS["aqueduct"]')
mp = head("지도 바탕(지면·테베레강·바다·길)과 풍경 소품(밭·수레·배·기중기·다리·바지선)", "map") + STAR + \
    "from m_core import NOTCH_X, NOTCH_Y, cell_verts, cell_center, CORE_X0, CORE_Y0, CORE_W, CORE_HW, CORE_HH, NCELL\n" + \
    "from m_arena import ARENA_R, ARENA_XL, ARENA_CY, ARENA_CX\nimport m_support_bottom as SB\n\n" + \
    take((822, 825), (831, 840), (1826, 1865), (1866, 1943), (1976, 2056)) + "\n" + setup_roads + '''

# ───────────────────────── 배치 명세 ─────────────────────────
POS = {"vineyard": (398, 486), "field1": (188, 228), "field2": (212, 407), "cart": (107, 355), "ship": (200, 478),
       "crane": (84, 479), "bridge": (133.5, 372.1), "barge": (342.0, 167.0)}


def objects():
    cx_, cy_ = POS["cart"]
    sx_, sy_ = POS["ship"]
    rx_, ry_ = POS["crane"]
    gx, gy = POS["bridge"]
    vx2, vy2 = POS["vineyard"]
    f1x, f1y = POS["field1"]
    f2x, f2y = POS["field2"]
    bgx, bgy = POS["barge"]
    return [
        dict(z=110, name="수레", tier="소품", region=(cx_ - 26, cy_ - 22, cx_ + 26, cy_ + 20), fn=draw_cart, args=(cx_, cy_)),
        dict(z=120, name="화산재 운반선", tier="소품", region=(sx_ - 28, sy_ - 24, sx_ + 28, sy_ + 20), fn=draw_ship, args=(sx_, sy_)),
        dict(z=130, name="답차 기중기", tier="소품", region=(rx_ - 28, ry_ - 28, rx_ + 28, ry_ + 20), fn=draw_crane, args=(rx_, ry_)),
        dict(z=140, name="돌 다리", tier="소품", region=(gx - 22, gy - 16, gx + 22, gy + 16), fn=draw_bridge, args=(gx, gy)),
        dict(z=150, name="포도밭 구획", tier="소품", region=(vx2 - 26, vy2 - 18, vx2 + 26, vy2 + 14), fn=draw_vineyard, args=(vx2, vy2)),
        dict(z=160, name="올리브 과수원", tier="소품", region=(f1x - 26, f1y - 20, f1x + 26, f1y + 18), fn=draw_field, args=(f1x, f1y, "olive")),
        dict(z=170, name="곡식밭", tier="소품", region=(f2x - 26, f2y - 18, f2x + 26, f2y + 16), fn=draw_field, args=(f2x, f2y, "grain")),
        dict(z=180, name="테베레 바지선", tier="소품", region=(bgx - 22, bgy - 22, bgx + 22, bgy + 20), fn=draw_barge, args=(bgx, bgy)),
    ]


def labels():
    return [
        dict(order=120, kind="flag", name="수레", T=(107.0, 353.0), M=M_WALL_DN, col=C_INK, en="CART", ko="수레", side="L", mode="above", pole=12.0),
        dict(order=130, kind="flag", name="화산재 운반선", T=(200.0, 468.0), M=M_WALL_DN, col=C_INK, en="ASH SHIP", ko="화산재 운반선", side="L", mode="above", pole=8.0),
        dict(order=140, kind="flag", name="답차 기중기", T=(84.0, 463.0), M=M_WALL_DN, col=C_INK, en="CRANE", ko="답차 기중기", side="L", mode="above", pole=6.0),
        dict(order=160, kind="flag", name="테베레 바지선", T=(343.0, 163.0), M=M_WALL_UP, col=C_INK, en="BARGE", ko="바지선", side="L", mode="below", pole=10.0),
    ]


def extra_labels(LB):
    """지형명: 바닥에 눕혀 지형색 톤온톤으로(강은 ↗ 기준선, 길·바다는 ↘ 기준선), 지시선 없음"""
    fe3, fk3 = fnt("en", 3.4 / 0.71), fnt("b", 3.2)
    cxr = 372.0
    cyr = RIVER_A[1] - T30 * (cxr - RIVER_A[0])
    floor_line(LB, cxr + 0.82, cyr + 1.43, [("TIBER", fe3, RIVER_T), ("테베레강", fk3, RIVER_T)], M_FLOOR_NE)
    F0 = (ARENA_CX - 12.0, ARENA_CY + 0.654 * ARENA_R)
    cxa = F0[0] + 30.0
    cya = F0[1] + T30 * 30.0
    floor_line(LB, cxa - 0.82, cya + 1.43, [("VIA APPIA", fe3, (126, 106, 76)), ("아피아 가도", fk3, (126, 106, 76))], M_FLOOR_SE)
    draw_floor_name(LB, 178.0, 431.0, "티레니아해", "TYRRHENIAN SEA", (60, 96, 132), kind="SE", em=3.4)
'''

# ── m_support_top.py ──
st = head("Support(위 줄·뒤쪽): 카라칼라 욕장(절개)·판테온, Support-2 베수비오와 밑동을 가리는 포도밭 농장", "support_top") + STAR + "\n" + \
    take((1450, 1538), (1539, 1539), (1544, 1623), (1770, 1825)) + '''

# ───────────────────────── 배치 명세 ─────────────────────────
POS = {"bath": (176, 138, 64), "pantheon": (245, 138, 66), "vesuvius": (326, 126, 52), "farm": (332, 127)}


def objects():
    bx, by, bw = POS["bath"]
    vx, vy, vw = POS["vesuvius"]
    fx, fy = POS["farm"]
    px, py, pw = POS["pantheon"]
    return [
        dict(z=10, name="베수비오", tier="Support-2", region=(vx - 40, vy - 40, vx + 40, vy + 28), fn=draw_vesuvius, args=(vx, vy, vw)),
        dict(z=20, name="포도밭 농장", tier="소품", region=(fx - 24, fy - 20, fx + 24, fy + 18), fn=draw_farm, args=(fx, fy)),
        dict(z=30, name="욕장", tier="Support", region=(bx - 46, by - 46, bx + 46, by + 36), fn=draw_bath, args=(bx, by, bw)),
        dict(z=40, name="판테온", tier="Support", region=(px - 46, py - 46, px + 46, py + 36), fn=draw_pantheon, args=(px, py, pw)),
    ]


def labels():
    return [
        dict(order=20, kind="label", name="욕장", T=(176.0, 156.5), M=M_WALL_UP, mode="below", side="L", col=C_SUP_T,
             en=["CARACALLA BATHS"], ko="카라칼라 욕장", sup=None,
             body=["열탕실 복원 상상도", "오큘러스·코퍼는 복원 추정", "냉탕실 열주를 합친 복합도", "겉은 벽돌, 속은 콘크리트"], gap=9.5),
        dict(order=30, kind="label", name="판테온", T=(245.0, 156.5), M=M_WALL_UP, mode="below", side="L", col=C_SUP_T,
             en=["PANTHEON"], ko="판테온", sup=None, body=["철근 없는 콘크리트 돔", "지름 43.3m", "위로 갈수록 가벼운 골재"], gap=9.5),
        dict(order=110, kind="flag", name="베수비오", T=(341.3, 114.0), M=M_WALL_UP, col=C_SUP_T, en="VESUVIUS", ko="베수비오", side="L", mode="above", pole=9.0),
    ]


def extra_labels(LB):
    pass
'''

# ── m_panels.py ──
footer = take((2248, 2279)).replace('"※ 와이어프레임 v16: ', '"※ 와이어프레임 " + C.VERSION + ": ')
pn = head("화면 평행 정보 패널(타이틀·Basic L1/L2/R1·하단 B1/B2/B3·푸터)과 Detail 확대 창", "panels") + STAR + \
    "from m_core import cell_verts, NCELL\n\n" + \
    take((561, 562), (568, 575), (589, 607), (608, 799), (1944, 1975)) + "\n" + footer + '''

# ───────────────────────── 배치 명세 ─────────────────────────
POS = {"zoom": (58, 415, 66)}
PANELS = [("정의", "Basic", "로마 콘크리트란?", panel_definition), ("레시피", "Basic", "레시피·순서", panel_recipe),
          ("위치도", "Basic", "위치도", panel_where), ("석회", "Detail", "석회 알갱이 패널", panel_lime),
          ("연대기", "Basic", "연대기·근거", panel_history), ("수명비교", "Basic", "100 vs 2000", panel_100v2000)]


def objects():
    zx, zy, zd = POS["zoom"]
    return [dict(z=70, name="확대 창", tier="Detail", region=(zx - zd / 2 - 2, zy - zd / 2 - 2, zx + zd / 2 + 2, zy + zd / 2 + 2), fn=draw_zoom, args=(zx, zy, zd))]


def labels():
    return [dict(order=150, kind="flag", name="확대 창", T=(36.8, 389.7), M=M_WALL_DN, col=C_DETAIL_T, en="DETAIL", ko="확대 창", side="R", mode="above", pole=8.0)]


def extra_labels(LB):
    """6단계 → 확대 창: 셀 앞 꼭짓점의 굳은 단면에서 수직 지시선, 확대 창 → 하단 Detail 패널 윗변"""
    zx, zy, zd = POS["zoom"]
    bx_, by_ = cell_verts(NCELL - 1)["B"][0], cell_verts(NCELL - 1)["B"][1] - 12.4
    LB.line([(bx_, by_), (bx_, zy - zd / 2.0)], C_DETAIL_T, LEAD_LW, joint=False, kind="지시선")
    LB.dot(bx_, by_, DOT_R, C_DETAIL_T)
    LABELS.append({"이름": "확대 창 지시선", "종류": "지시선", "다각형": [], "대상": (bx_, by_), "열": ""})
    bx2 = bx_
    LB.line([(bx2, zy + zd / 2.0), (bx2, PANEL_RECT["석회"][1])], C_DETAIL_T, LEAD_LW, joint=False, kind="지시선")
    LB.dot(bx2, PANEL_RECT["석회"][1], DOT_R, C_DETAIL_T)
'''

# ── analysis.py ──
an = head("자동 실측·검사(투영 크기 위계·베이징 대조·밀도·각도·라벨 충돌·강 간격)", "global") + STAR + \
    "import m_map as M\nfrom m_map import RIVER_W, RIVER_A, sea_polygon\nfrom m_arena import ARENA_R, ARENA_XL, ARENA_CX\nfrom m_panels import PANEL_RECT\n\n" + \
    take((2280, 2546)).replace("for road in ROADS:", "for road in M.ROADS:")

# 조립 부분(원본 2057~2078 POS, 2088~2121 라벨 명세, 2148~2247 조립, 2547~2570 main)은 main.py와 각 모듈 명세로 다시 썼다.
for a, b in ((1, 7), (2057, 2078), (2088, 2121), (2148, 2247), (2547, 2570)):
    for i in range(a, b + 1):
        USED.add(i)
missing = [i for i in range(1, len(L) + 1) if i not in USED and L[i - 1].strip()]
if missing:
    print("배정되지 않은 줄:", missing[:60])
    for i in missing[:60]:
        print(i, L[i - 1][:90])
    raise SystemExit(1)

os.makedirs(DST, exist_ok=True)
for name, txt in (("common.py", common), ("m_core.py", core), ("m_arena.py", arena), ("m_support_bottom.py", sb), ("m_map.py", mp),
                  ("m_support_top.py", st), ("m_panels.py", pn), ("analysis.py", an)):
    with open(os.path.join(DST, name), "w", encoding="utf-8") as f:
        f.write(txt.rstrip("\n") + "\n")
    print("작성:", name, len(txt.split("\n")), "줄")
