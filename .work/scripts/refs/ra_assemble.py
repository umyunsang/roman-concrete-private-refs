"""측정값 조립 -> 구획 목록(0~1 정규) + 확인용 이미지(<ref>_zones.png) + refs_analysis.json"""
import json, sys
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from ra_common import *
from ra_labels_def import LABELS, ORIENT

FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
INK = json.load(open(WORK / "ink.json")); ST = json.load(open(WORK / "stats.json"))
GEO = json.load(open(WORK / "geo.json")); ANG = json.load(open(WORK / "angles.json"))
MMX, MMY = 420 / 1000, 594 / 1400

# 최종 오브젝트 상자(정규 단위): 격자 판독 + GrabCut 외곽 대조로 고른 값
FINAL = {
 "203x-seoul": [
  ("롯데월드타워(히어로, 잠실)", "hero", (698, 503, 868, 1036)),
  ("흥인지문(동대문)+성곽", "landmark", (582, 258, 866, 596)),
  ("N서울타워+남산 블록", "landmark", (588, 318, 764, 832)),
  ("코엑스·무역센터", "landmark", (487, 650, 704, 994)),
  ("서울시청", "landmark", (492, 416, 646, 632)),
  ("DDP(동대문디자인플라자)", "landmark", (796, 504, 1000, 662)),
  ("숭례문", "landmark", (304, 437, 528, 686)),
  ("구 서울역", "landmark", (45, 425, 252, 692)),
  ("63빌딩", "landmark", (226, 506, 316, 838)),
  ("국회의사당", "landmark", (45, 684, 270, 880)),
  ("고속터미널", "landmark", (300, 742, 506, 932)),
  ("시내버스", "landmark", (182, 880, 324, 994)),
  ("지하철(+선로·터널 입구)", "landmark", (40, 1008, 248, 1142)),
  ("택시", "landmark", (832, 852, 948, 923)),
 ],
 "203x-london": [
  ("빅벤(히어로, 엘리자베스 타워)", "hero", (272, 42, 504, 1070)),
  ("웨스트민스터 사원", "landmark", (48, 540, 282, 962)),
  ("30 St Mary Axe(거킨)", "landmark", (505, 302, 615, 605)),
  ("빨간 전화박스", "landmark", (543, 543, 590, 662)),
  ("타워브리지", "landmark", (574, 425, 872, 768)),
  ("더 샤드", "landmark", (860, 425, 962, 852)),
  ("런던 아이", "landmark", (390, 687, 690, 1100)),
  ("신사(볼러 모자·우산)", "landmark", (700, 644, 762, 830)),
  ("블랙캡", "landmark", (748, 788, 876, 876)),
  ("런던 버스(9번)", "landmark", (200, 1004, 350, 1128)),
  ("언더그라운드+원형 표지", "landmark", (50, 944, 242, 1127)),
  ("근위병 2명", "landmark", (524, 899, 650, 1187)),
 ],
 "203x-berlin": [
  ("베를린 TV탑(히어로)", "hero", (566, 114, 694, 1172)),
  ("TV탑 받침 판(이스트사이드·세계시계·정자·숲)", "landmark", (343, 978, 897, 1347)),
  ("베를린 돔", "landmark", (431, 462, 705, 810)),
  ("이스트 사이드 갤러리", "landmark", (382, 917, 567, 1097)),
  ("세계시계(Urania-Weltzeituhr)", "landmark", (750, 1045, 835, 1182)),
  ("카이저 빌헬름 기념 교회", "landmark", (300, 373, 492, 580)),
  ("국회의사당(+판)", "landmark", (14, 482, 367, 737)),
  ("홀로코스트 기념비(+판)", "landmark", (110, 714, 394, 897)),
  ("브란덴부르크 문(+원판, 왼쪽 블리드)", "landmark", (0, 860, 258, 1080)),
  ("체크포인트 찰리", "landmark", (333, 760, 495, 967)),
  ("유대인 박물관(+숲)", "landmark", (688, 230, 907, 442)),
  ("베를린 중앙역(+침하 분지)", "landmark", (700, 418, 1000, 625)),
  ("전승기념탑(+원판)", "landmark", (730, 595, 950, 1032)),
  ("S반", "landmark", (690, 800, 845, 915)),
  ("U반(터널 출구)", "landmark", (825, 1190, 915, 1287)),
  ("노란 버스", "landmark", (234, 881, 296, 933)),
  ("택시", "landmark", (908, 568, 985, 612)),
 ],
}
EXTRA = {  # 강·바다·길·지면 판(정규 단위, note)
 "203x-seoul": [
  ("한강(판 아래 물 바닥, 하단 패널 받침)", "sea", None, "물 마스크 실측. 판 앞 변 아래 전폭, 하단 패널 3개가 이 물 위에 놓인다"),
  ("서울 지면 판(민트, 좌우 블리드)", "other", (0, 395, 1000, 1143), "판 색 마스크 실측: 왼쪽 변 y 578~985, 오른쪽 변 y 591~1038에서 액자 밖으로 이어짐. 뒤 변 계단 윤곽 y≈395~560(눈 판독), 앞 변 옆면 바닥 y≈1143"),
  ("큰길 구간(DDP 앞, 흰 점선 중앙선)", "road", (780, 570, 1000, 725), "수직 두께 약 48단위 -> 축 직각 약 43단위(약 18mm, 폭의 4.3%) 실측"),
 ],
 "203x-london": [
  ("런던 지면 판(회녹색, 계단형 윤곽)", "other", (0, 470, 1000, 1204), "판 색 마스크 실측: 왼쪽 변 y 681~938, 오른쪽 변 y 667~897 블리드, 앞 변 바닥 y≈1204. 뒤 변 y≈470~600(눈 판독). 도로 없음"),
 ],
 "203x-berlin": [
  ("주축 길 구간(흰 중앙선)", "road", (820, 290, 1000, 405), "왼쪽 변 y≈860에서 오른쪽 위 변 y≈300까지 +30° 대각 관통. 폭 약 40단위(17mm 안팎)"),
  ("보조 길 구간(카이저 빌헬름 교회 앞)", "road", (300, 555, 500, 680), "수직 두께 약 20단위 -> 축 직각 약 18단위(7~8mm)"),
 ],
}
RIVER_NAME = {"203x-seoul": "청계천(판 전체를 좌->우로 가로지르는 개천)", "203x-london": "템스강(보이는 물 면 조각)", "203x-berlin": "슈프레강(둑 벽이 보이는 수로)"}
RIVER_NOTE = {
 "203x-seoul": "왼쪽 변 y≈740 진입 -> 63빌딩·고속터미널 사이 -> 남산 블록을 ㅁ자로 감쌈 -> 롯데 오른쪽 -> 오른쪽 변 y≈860~920. 축 직각 폭 약 7~13mm(폭의 2~3%), 녹색 다리 3~4개",
 "203x-london": "타워브리지 아래(607~705, 718~779) -> 런던아이 받침 오른쪽(616~733, 849~971) -> 아이 아래 왼쪽(403~461, 1037~1098)에서 판 앞 변으로 끝남. 보이는 폭 약 15~18mm, 보이는 물 면은 지도 무대의 0.8%",
 "203x-berlin": "오른쪽 변(y≈460, 중앙역 분지) -> 돔 오른쪽 -> 돔과 TV탑 판 사이를 −30°로 내려와 (250,1045)에서 화면 수직(평면 대각)으로 꺾여 아래로 흐려지며 빠짐(y≈1250~1300). 둑 벽 포함 폭 약 13~20mm",
}

def norm(b):
    x0, y0, x1, y1 = b
    return [round(x0 / 1000, 4), round(y0 / 1400, 4), round(x1 / 1000, 4), round(y1 / 1400, 4)]

def mm(b):
    x0, y0, x1, y1 = b
    return f"{(x1-x0)*MMX:.0f}×{(y1-y0)*MMY:.0f}mm"

out = {}
for ref in FINAL:
    z = INK[ref]; st = ST[ref]
    zones = []
    zones.append({"name": "타이틀", "kind": "title", "bbox_norm": norm(z["title"]["bbox"]), "note": f"{z['title']['name']} · {mm(z['title']['bbox'])}"})
    for i, p in enumerate(z["panels"]):
        zones.append({"name": f"P{i+1} {p['name']}", "kind": "panel", "bbox_norm": norm(p["bbox"]), "note": f"자리 {p['slot']} · {mm(p['bbox'])} · 포스터 면적 {((p['bbox'][2]-p['bbox'][0])*(p['bbox'][3]-p['bbox'][1]))/1.4e6*100:.1f}%"})
    M = st["map_stage_u"]
    zones.append({"name": "M 지도 무대", "kind": "map", "bbox_norm": norm(M), "note": f"전폭 × 타이틀 아래 변~하단 띠 위 변 · 420×{(M[3]-M[1])*MMY:.0f}mm · 포스터의 {st['map_stage_pct_of_poster_area']}% · 지도 요소 세로 범위 y {st['fg_elements_y_extent_u'][0]}~{st['fg_elements_y_extent_u'][1]}"})
    c = st["core"]
    zones.append({"name": "코어 군(덩어리)", "kind": "core_group", "bbox_norm": norm(c["obj_box_union_u"]),
                  "note": f"구성: {', '.join(c['members'])} + 강 구간 · 상자 {mm(c['obj_box_union_u'])} = 지도 무대의 {c['obj_box_pct_of_M']}% · 덩어리 실면적 {c['mass_area_pct_of_M']}% · 실루엣 {c['silhouette_pct_of_M']}%"})
    for name, kind, b in FINAL[ref]:
        zones.append({"name": name, "kind": kind, "bbox_norm": norm(b), "note": mm(b)})
    river = np.load(WORK / f"river_{ref}.npy")
    ys, xs = np.nonzero(river)
    rb = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    if ref == "203x-berlin":
        rb[3] = 1300  # 아래로 흐려지는 수직 구간(마스크 밖, 확대 판독)
    zones.append({"name": RIVER_NAME[ref], "kind": "river", "bbox_norm": norm(rb), "note": RIVER_NOTE[ref]})
    for name, kind, b, note in EXTRA[ref]:
        if b is None and kind == "sea":
            b = st["sea"]["bbox_u"]
        zones.append({"name": name, "kind": kind, "bbox_norm": norm(b), "note": note})
    zones.append({"name": "푸터", "kind": "footer", "bbox_norm": norm(z["footer"]["bbox"]), "note": mm(z["footer"]["bbox"])})
    for (nm, b), ori in zip(LABELS[ref], ORIENT[ref]):
        zones.append({"name": f"라벨: {nm}", "kind": "other", "bbox_norm": norm(b), "note": f"지도 위 라벨 블록(이름+규선+본문), 기준선 {ori}, 상자 눈 판독 ±5"})
    out[ref] = zones

    # ---------- 그리기 ----------
    art = cv2.imread(str(composite_path(ref)))
    S = 1.4
    base = cv2.resize(art, (int(1000 * S), int(1400 * S)), interpolation=cv2.INTER_AREA)
    base = cv2.addWeighted(base, 0.72, np.full_like(base, 255), 0.28, 0)
    im = Image.fromarray(cv2.cvtColor(base, cv2.COLOR_BGR2RGB)).convert("RGBA")
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f14 = ImageFont.truetype(FONT, 15); f18 = ImageFont.truetype(FONT, 19); f24 = ImageFont.truetype(FONT, 26)
    def R(b): return [b[0] * S, b[1] * S, b[2] * S, b[3] * S]
    def tag(x, y, text, col, font=f14):
        tw = d.textlength(text, font=font)
        d.rectangle([x, y, x + tw + 8, y + font.size + 6], fill=col + (235,))
        d.text((x + 4, y + 2), text, font=font, fill=(255, 255, 255, 255) if sum(col) < 500 else (0, 0, 0, 255))
    def dashed(b, col, w, dash=14):
        x0, y0, x1, y1 = R(b)
        for (ax, ay, bx, by) in [(x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)]:
            L = max(abs(bx - ax), abs(by - ay)); n = int(L // dash)
            for k in range(0, n, 2):
                t0, t1 = k / max(n, 1), min((k + 1) / max(n, 1), 1)
                d.line([ax + (bx - ax) * t0, ay + (by - ay) * t0, ax + (bx - ax) * t1, ay + (by - ay) * t1], fill=col + (255,), width=w)
    # 강 마스크
    def tint(img, mask, rgb, a):
        arr = np.zeros((img.size[1], img.size[0], 4), np.uint8)
        arr[..., 0], arr[..., 1], arr[..., 2] = rgb
        arr[..., 3] = (mask > 0).astype(np.uint8) * a
        return Image.alpha_composite(img, Image.fromarray(arr, "RGBA"))
    rm = cv2.resize(river.astype(np.uint8) * 255, im.size, interpolation=cv2.INTER_NEAREST)
    im = tint(im, rm, (0, 90, 255), 150)
    if "sea" in st:
        lb = np.load(WORK / f"water_{ref}_hangang_labels.npy"); sea = (lb == 50).astype(np.uint8) * 255
        sm = cv2.resize(sea, im.size, interpolation=cv2.INTER_NEAREST)
        im = tint(im, sm, (20, 30, 140), 60)
    # 코어 덩어리
    cm = cv2.imread(str(WORK / f"coremass_{ref}.png"), 0)
    cmr = cv2.resize(cm, im.size, interpolation=cv2.INTER_NEAREST)
    im = tint(im, cmr, (255, 110, 0), 70)
    cnts, _ = cv2.findContours(cmr, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cn in cnts:
        pts = [tuple(p[0]) for p in cn]
        if len(pts) > 2: d.line(pts + [pts[0]], fill=(255, 110, 0, 255), width=4)
    COL = {"title": (255, 212, 0), "panel": (0, 170, 255), "map": (0, 200, 83), "core_group": (255, 110, 0), "hero": (229, 57, 53),
           "landmark": (255, 255, 255), "river": (0, 90, 255), "sea": (26, 35, 126), "road": (141, 110, 99), "footer": (120, 120, 120), "other": (213, 0, 249)}
    legend = []
    li = 0
    for zz in zones:
        b = [zz["bbox_norm"][0] * 1000, zz["bbox_norm"][1] * 1400, zz["bbox_norm"][2] * 1000, zz["bbox_norm"][3] * 1400]
        k = zz["kind"]; col = COL[k]
        if k == "other" and zz["name"].startswith("라벨"):
            d.rectangle(R(b), outline=col + (200,), width=1); continue
        if k == "map":
            dashed(b, col, 4); tag(R(b)[0] + 6, R(b)[1] + 6, "M 지도 무대", col, f18); legend.append(("M", zz)); continue
        if k == "core_group":
            dashed(b, col, 4, 20); tag(R(b)[0] + 4, R(b)[3] - 30, "코어 군", col, f18); legend.append(("C", zz)); continue
        if k == "landmark":
            li += 1
            d.rectangle(R(b), outline=(0, 0, 0, 255), width=4); d.rectangle(R(b), outline=col + (255,), width=2)
            tag(R(b)[0] + 3, R(b)[1] + 3, f"L{li}", (40, 40, 40)); legend.append((f"L{li}", zz)); continue
        if k == "hero":
            d.rectangle(R(b), outline=col + (255,), width=5); tag(R(b)[2] - 70, R(b)[1] + 3, "히어로", col, f18); legend.append(("H", zz)); continue
        if k == "panel":
            d.rectangle(R(b), outline=col + (255,), width=4); tag(R(b)[0] + 3, R(b)[1] + 3, zz["name"].split(" ")[0], col, f18); legend.append((zz["name"].split(" ")[0], zz)); continue
        if k == "title":
            d.rectangle(R(b), outline=col + (255,), width=5); tag(R(b)[0] + 3, R(b)[3] + 3, "T 타이틀", col, f18); legend.append(("T", zz)); continue
        if k in ("river", "sea"):
            d.rectangle(R(b), outline=col + (255,), width=3); tag(R(b)[0] + 3, R(b)[1] + 3, "강" if k == "river" else "바다·큰물", col, f18); legend.append(("R" if k == "river" else "S", zz)); continue
        if k == "road":
            dashed(b, col, 3, 10); tag(R(b)[0] + 3, R(b)[1] + 3, "길", col); legend.append(("길", zz)); continue
        if k == "footer":
            d.rectangle(R(b), outline=col + (255,), width=3); legend.append(("F", zz)); continue
        if k == "other":
            dashed(b, (90, 160, 90), 2, 8); legend.append(("G", zz)); continue
    im = Image.alpha_composite(im, lay)
    # 오른쪽 범례
    LW = 640
    canvas = Image.new("RGBA", (im.size[0] + LW, im.size[1]), (255, 255, 255, 255))
    canvas.paste(im, (0, 0))
    dl = ImageDraw.Draw(canvas)
    y = 18
    dl.text((im.size[0] + 18, y), f"{ref} 구획 실측(정규 1000×1400 단위 상자)", font=f24, fill=(0, 0, 0)); y += 40
    lines = [f"지도 무대 M {st['map_stage_pct_of_poster_area']}% · 오브젝트 밀도 {st['object_density_pct_of_M']}%(M 대비)",
             f"코어 군 상자 {st['core']['obj_box_pct_of_M']}% · 덩어리 {st['core']['mass_area_pct_of_M']}% · 실루엣 {st['core']['silhouette_pct_of_M']}%(M 대비)",
             f"투영(LSD, 지도 영역): {ANG[ref]['window_pct']}",
             f"압축 지리: RMS {GEO[ref]['fit']['rms_mm']}mm · 거리 지수 {GEO[ref]['dist_exponent_b']} · 실제 북쪽 화면 {GEO[ref]['north_on_screen_deg']}°",
             "주황 칠 = 코어 군 덩어리(닫힘 21단위) · 파랑 칠 = 강 물 면 마스크 · 남색 칠 = 큰물",
             "보라 가는 상자 = 지도 위 라벨 블록 · 초록 점선 = 지면 판 · 갈색 점선 = 길"]
    for t in lines:
        dl.text((im.size[0] + 18, y), t, font=f14, fill=(30, 30, 30)); y += 22
    y += 8
    for code, zz in legend:
        b = zz["bbox_norm"]
        col = COL[zz["kind"]] if zz["kind"] != "landmark" else (60, 60, 60)
        dl.rectangle([im.size[0] + 18, y + 3, im.size[0] + 32, y + 17], fill=col + (255,))
        txt = f"{code}  {zz['name']}"
        dl.text((im.size[0] + 40, y), txt[:46], font=f14, fill=(0, 0, 0)); y += 19
        dl.text((im.size[0] + 60, y), f"[{b[0]:.3f}, {b[1]:.3f}, {b[2]:.3f}, {b[3]:.3f}]  {zz['note'][:34]}", font=ImageFont.truetype(FONT, 12), fill=(90, 90, 90)); y += 18
        if y > im.size[1] - 40: break
    p = OUT / f"{ref}_zones.png"
    canvas.convert("RGB").save(p, optimize=True)
    print(p, canvas.size, "zones", len(zones))
json.dump(out, open(OUT / "203x-seoul-london-berlin_zones.json", "w"), ensure_ascii=False, indent=1)
