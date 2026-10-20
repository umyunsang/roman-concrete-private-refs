# -*- coding: utf-8 -*-
"""구획 실측 종합 + 확인용 구획 이미지(<ref>_zones.png).
- 상자 좌표는 아트 2000x2800 px. 정규 좌표 = x/2000, y/2800. mm = A2 환산(x 0.21, y 0.21214).
- 타이틀·패널·푸터: tightbox.py 실측값(잉크 외곽). 랜드마크·코어: objects.py 결과. 강·하늘·섬: classmap 성분 상자.
"""
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = "/Users/um-yunsang/roman-concrete-private-refs"
OUT = os.path.join(ROOT, ".work/out/refs-analysis")
W, H = 2000, 2800
MMX, MMY = 420 / 2000, 594 / 2800
POSTER_MM2 = 420 * 594
ROME_STAGE_MM2 = 420 * 413
FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"

ZONES = {
    "203x-tokyo": [
        ("타이틀(도리이 액자·후지산)", "title", (503, 37, 1497, 433), "잉크 외곽 실측. 폭 49.7%, 가운데 정렬(중심 x 210.0mm)"),
        ("CITY INFORMATION 도시 정보", "panel", (100, 97, 485, 320), "좌측 열 1"),
        ("FAMOUS CULTURE AREA 문화지역", "panel", (100, 365, 484, 685), "좌측 열 2, 점 격자 지도+핀"),
        ("CITY SYMBOL 도시 상징", "panel", (98, 731, 485, 1082), "좌측 열 3"),
        ("FAMOUS FOOD 유명한 음식", "panel", (96, 1124, 480, 1317), "좌측 열 4"),
        ("HISTORY 역사", "panel", (1511, 97, 1829, 342), "우상 1, 목록형 연표 5항"),
        ("BRIDGES OF SUMIDA RIVER 스미다강 다리", "panel", (100, 2345, 691, 2699), "좌하 1, 강 모양 꺾은선 위 다리 번호 25"),
        ("지도 무대", "map", (0, 433, 2000, 2682), "전폭 x 타이틀 아래~푸터 위. 세계는 푸터 뒤 아래 변까지 블리드(x 999~1446)"),
        ("스미다강(강 띠 전체)", "river", (934, 1553, 2000, 2800), "오른쪽 변 2곳 진입(y 1553~1651, 2250~2328), 아래 변 1곳 블리드(x 1275~1413)"),
        ("도로망(가장 큰 성분, +30° 주 대각로)", "road", (824, 1163, 1763, 1791), "띠에 수직인 폭 18.0mm(가운데 흰 줄 1.6mm). 판 사이를 잇는 ±30° 띠"),
        ("푸터", "footer", (101, 2682, 1904, 2739), "Street H 로고·크레딧·203X·QR"),
    ],
    "203x-newyork2-centralpark": [
        ("타이틀(브로드웨이 전광판형)", "title", (106, 121, 917, 380), "잉크 외곽 실측(전광 줄 포함). 글자·인용 상자만은 x 106~852"),
        ("하늘(남색 모서리, 타이틀 받침)", "other", (0, 0, 1432, 835), "하늘 클래스 성분 상자. 포스터의 7.5%"),
        ("위치 인셋(Harlem·Upper West·Upper East)", "panel", (1448, 1673, 1707, 1984), "우하 패널군 1(지도 범위 표시)"),
        ("CITY SYMBOL 도시 상징물", "panel", (1444, 1999, 1825, 2112), "우하 2"),
        ("CITY INFORMATION 도시 정보", "panel", (1439, 2147, 1833, 2639), "우하 3(지도+6칸 표+자치구 5)"),
        ("ART IN NEW YORK 뉴욕의 예술", "panel", (1014, 2245, 1404, 2661), "하단 가운데"),
        ("ART MUSEUM 미술관", "panel", (608, 2304, 968, 2659), "하단 왼쪽(강 건너 퀸즈 땅 위)"),
        ("지도 무대", "map", (0, 0, 2000, 2686), "푸터 위 전부. 땅은 네 변 모두 블리드"),
        ("이스트강", "river", (0, 971, 2000, 2800), "대각 강 띠(세로 두께 441~514px). 코어(좌상)와 패널 땅(우하)을 가른다"),
        ("할렘강(오른쪽 위)", "river", (1861, 97, 2000, 599), "오른쪽 변 블리드"),
        ("퀸즈 땅(강 건너, 패널 받침)", "other", (150, 1430, 2000, 2800), "이스트강 아래 +30° 해안선 아래쪽 땅. 패널 5개·인셋이 모두 이 땅 위에 얹힌다"),
        ("푸터", "footer", (100, 2686, 1914, 2739), ""),
    ],
    "203x-newyork": [
        ("타이틀(브로드웨이 전광판형)", "title", (98, 105, 1342, 390), "잉크 외곽 실측. 폭 62.2%, 왼쪽으로 치우침(중심 x 151mm)"),
        ("HISTORY 역사", "panel", (1505, 103, 1900, 387), "우상"),
        ("CITY INFORMATION 도시 정보", "panel", (100, 478, 502, 980), "좌측 열 1(지도+표+자치구 5)"),
        ("CITY SYMBOL 도시 상징", "panel", (98, 1009, 493, 1108), "좌측 열 2"),
        ("ART IN NEW YORK 뉴욕의 예술", "panel", (1505, 1823, 1902, 2285), "우측 열(강 위 빈 남색)"),
        ("ART MUSEUM 미술관", "panel", (1504, 2317, 1867, 2660), "우측 열"),
        ("NIGHT VIEW POINTS TOP 3 야경 명소", "panel", (585, 2416, 1465, 2662), "하단 가운데(스카이라인 실루엣 막대)"),
        ("지도 무대", "map", (0, 390, 2000, 2685), "전폭 x 타이틀 아래~푸터 위"),
        ("맨해튼 섬(지면 띠)", "other", (101, 462, 2000, 2275), "섬 지면 클래스 상자. 오른쪽 변으로 블리드, 왼쪽 아래 끝(배터리)은 액자 안"),
        ("허드슨강(남색 물 위 바닥 글)", "river", (1620, 490, 1830, 600), "강 띠 없음. 남색 바탕이 밤하늘·물을 겸하고, 섬 가장자리를 따라 +26° 바닥 글만 둔다"),
        ("이스트강(남색 물 위 바닥 글)", "river", (1650, 1690, 1900, 1810), "섬 아래 가장자리 +26° 바닥 글"),
        ("푸터", "footer", (100, 2685, 1895, 2732), ""),
    ],
}

# 표시할 랜드마크(이름 짧게)
SHORT = {
    "도쿄 도청": "도청", "가미나리몬(센소지)": "가미나리몬", "아사쿠사 등롱": "등롱", "도쿄 스카이트리": "스카이트리(히어로)",
    "황궁": "황궁", "메이지 신궁(도리이·숲 판)": "메이지 신궁", "도쿄 타워": "도쿄 타워", "롯폰기 힐스 모리 타워": "모리 타워",
    "하치코 동상": "하치코", "고토쿠지(마네키네코)": "고토쿠지", "도쿄역": "도쿄역", "신칸센": "신칸센", "시내버스": "버스",
    "JR 지상철": "JR", "도쿄 메트로": "메트로", "수상버스": "수상버스", "레인보우 브리지": "레인보우 브리지", "대관람차": "대관람차",
    "도쿄 빅사이트": "빅사이트", "택시": "택시",
}

COL = {"title": (230, 160, 0), "panel": (0, 170, 230), "map": (0, 170, 0), "core_group": (230, 0, 0), "hero": (200, 0, 200),
       "landmark": (255, 215, 0), "river": (0, 90, 255), "sea": (0, 60, 160), "road": (150, 110, 0), "footer": (120, 120, 120),
       "other": (0, 150, 150), "legend": (0, 0, 0)}


def norm(b):
    return [round(b[0] / W, 4), round(b[1] / H, 4), round(b[2] / W, 4), round(b[3] / H, 4)]


def mm(b):
    return [round(b[0] * MMX, 1), round(b[1] * MMY, 1), round(b[2] * MMX, 1), round(b[3] * MMY, 1)]


def main(ref):
    obj = json.load(open(os.path.join(OUT, f"{ref}_objects.json"), encoding="utf-8"))
    net = json.load(open(os.path.join(OUT, f"{ref}_network.json"), encoding="utf-8"))
    ang = json.load(open(os.path.join(OUT, "tny_angles.json"), encoding="utf-8"))[ref]
    masks = np.load(os.path.join(OUT, f"{ref}_lm_masks.npz"))
    zones = []
    for name, kind, b, note in ZONES[ref]:
        zones.append({"name": name, "kind": kind, "bbox_art": list(b), "bbox_norm": norm(b), "bbox_mm": mm(b),
                      "wh_mm": [round((b[2] - b[0]) * MMX, 1), round((b[3] - b[1]) * MMY, 1)], "note": note})
    stage = obj["map_stage_art"]
    stage_mm2 = (stage[2] - stage[0]) * MMX * (stage[3] - stage[1]) * MMY
    cores = {}
    for cname, c in obj["core_groups"].items():
        cc = dict(c)
        for k in ("bbox_pct_of_map_stage", "hull_pct_of_map_stage", "mass_pct_of_map_stage", "object_px_pct_of_map_stage", "member_box_union_pct"):
            a = c[k] / 100 * stage_mm2
            cc[k.replace("_pct", "_mm2").replace("_of_map_stage", "")] = round(a)
            cc[k + "_as_rome_stage_pct"] = round(100 * a / ROME_STAGE_MM2, 1)
            cc[k + "_as_poster_pct"] = round(100 * a / POSTER_MM2, 1)
        cores[cname] = cc
        zones.append({"name": f"코어 군: {cname}", "kind": "core_group", "bbox_art": c["bbox_art"], "bbox_norm": c["bbox_norm"],
                      "bbox_mm": c["bbox_mm"], "wh_mm": [round((c['bbox_art'][2] - c['bbox_art'][0]) * MMX, 1),
                                                         round((c['bbox_art'][3] - c['bbox_art'][1]) * MMY, 1)],
                      "note": f"덩어리 {c['mass_pct_of_map_stage']}% · 볼록 껍질 {c['hull_pct_of_map_stage']}% · 외곽 상자 {c['bbox_pct_of_map_stage']}% (지도 무대 대비)"})
    for nm, info in obj["landmarks"].items():
        if not info["bbox_art"] or info.get("label") is False:
            continue
        kind = "hero" if "히어로" in info["tier"] else "landmark"
        zones.append({"name": nm, "kind": kind, "bbox_art": info["bbox_art"], "bbox_norm": info["bbox_norm"],
                      "bbox_mm": mm(info["bbox_art"]), "wh_mm": info["wh_mm"],
                      "note": f"{info['tier']} · 실면적 {info['area_mm2']:.0f}mm² ({info['pct_of_map_stage']}%)"})
    res = {"ref": ref, "map_stage_art": stage, "map_stage_mm2": round(stage_mm2), "map_stage_pct_of_poster": round(100 * stage_mm2 / POSTER_MM2, 1),
           "zones": zones, "core_groups": cores,
           "density": {"objects_union_pct": obj["objects_union_pct_of_map_stage"], "landmarks_union_pct": obj["landmarks_union_pct_of_map_stage"],
                       "road_pct": obj["road_pct_of_map_stage"], "water_pct": obj["water_pct_of_map_stage"], "ground_pct": obj["ground_pct_of_map_stage"]},
           "network": net, "angles": {"map_windows_hi": ang["map_windows_hi"],
                                      "tiles": {k: {"pos": v["pos"], "neg": v["neg"], "vert": v["vert"], "share_pct": v["share_pct"]} for k, v in ang["tiles"].items()}},
           "landmarks": obj["landmarks"]}
    # 패널 합계
    pz = [z for z in zones if z["kind"] == "panel"]
    res["panels_total_mm2"] = round(sum(z["wh_mm"][0] * z["wh_mm"][1] for z in pz))
    res["panels_pct_of_poster"] = round(100 * res["panels_total_mm2"] / POSTER_MM2, 1)
    with open(os.path.join(OUT, f"{ref}_analysis.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)

    # ---- 확인용 구획 이미지(1000x1400) ----
    art = Image.open(os.path.join(OUT, f"{ref}_art.png")).convert("RGB")
    S = 0.5
    img = art.resize((int(W * S), int(H * S)), Image.LANCZOS)
    base = img.copy()
    # 코어 덩어리 반투명 채움
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for i, cname in enumerate(obj["core_groups"]):
        key = "__core__" + cname
        if key not in masks.files:
            continue
        m = masks[key].astype(np.uint8)
        m = cv2.resize(m, img.size, interpolation=cv2.INTER_NEAREST)
        cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        col = (255, 0, 0) if i == 0 else (255, 0, 200)
        for cnt in cs:
            pts = [tuple(p[0]) for p in cnt]
            if len(pts) > 2:
                if i == 0:
                    od.polygon(pts, fill=col + (55,))
                od.line(pts + [pts[0]], fill=col + (255,), width=4 if i == 0 else 2)
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(img)
    f_big = ImageFont.truetype(FONT, 17)
    f_sm = ImageFont.truetype(FONT, 12)

    def box(b, col, wdt, label, font, inside=True, dash=False):
        x0, y0, x1, y1 = [int(v * S) for v in b]
        if dash:
            for x in range(x0, x1, 12):
                d.line([(x, y0), (min(x + 6, x1), y0)], fill=col, width=wdt)
                d.line([(x, y1), (min(x + 6, x1), y1)], fill=col, width=wdt)
            for y in range(y0, y1, 12):
                d.line([(x0, y), (x0, min(y + 6, y1))], fill=col, width=wdt)
                d.line([(x1, y), (x1, min(y + 6, y1))], fill=col, width=wdt)
        else:
            d.rectangle([x0, y0, x1, y1], outline=col, width=wdt)
        if label:
            tw = d.textlength(label, font=font)
            th = font.size + 4
            ty = y0 + 2 if inside else max(0, y0 - th)
            tx = min(max(0, x0 + 2), img.size[0] - tw - 4)
            d.rectangle([tx, ty, tx + tw + 4, ty + th], fill=(255, 255, 255))
            d.text((tx + 2, ty + 1), label, fill=col, font=font)

    order = {"map": 0, "sea": 1, "other": 2, "river": 3, "road": 4, "landmark": 5, "hero": 6, "core_group": 7, "panel": 8, "title": 9, "footer": 10}
    for z in sorted(zones, key=lambda z: order.get(z["kind"], 5)):
        k = z["kind"]
        col = COL.get(k, (0, 0, 0))
        if k == "landmark":
            box(z["bbox_art"], col, 1, SHORT.get(z["name"], z["name"]), f_sm)
        elif k == "hero":
            box(z["bbox_art"], col, 3, SHORT.get(z["name"], z["name"]), f_big)
        elif k == "core_group":
            first = z["name"].endswith(list(obj["core_groups"].keys())[0])
            box(z["bbox_art"], (230, 0, 0) if first else (230, 0, 180), 2, z["name"] + " 외곽 상자", f_sm, inside=False, dash=True)
        elif k == "map":
            box(z["bbox_art"], col, 4, "지도 무대", f_big)
        elif k in ("river", "sea", "road", "other"):
            box(z["bbox_art"], col, 2, z["name"], f_sm, dash=True)
        else:
            box(z["bbox_art"], col, 3, z["name"], f_big if k == "title" else f_sm)
    # 범례·요약: 오른쪽 띠(그림을 가리지 않게)
    strip = 300
    canvas = Image.new("RGB", (img.size[0] + strip, img.size[1]), (255, 255, 255))
    canvas.paste(img, (0, 0))
    d = ImageDraw.Draw(canvas)
    lx, ly = img.size[0] + 14, 16
    d.text((lx, ly), ref, fill=(0, 0, 0), font=f_big)
    ly += 30
    lg = [("타이틀", COL["title"]), ("패널", COL["panel"]), ("지도 무대", COL["map"]), ("코어 군 덩어리(빨강 채움)", (230, 0, 0)),
          ("확장 코어(분홍 윤곽)", (230, 0, 180)), ("히어로", COL["hero"]), ("랜드마크", COL["landmark"]), ("강·물(점선)", COL["river"]),
          ("길(점선)", COL["road"]), ("그 밖 지면(점선)", COL["other"]), ("푸터", COL["footer"])]
    for i, (t, c) in enumerate(lg):
        d.rectangle([lx, ly + i * 20, lx + 14, ly + i * 20 + 12], outline=c, width=3)
        d.text((lx + 22, ly + i * 20 - 2), t, fill=(20, 20, 20), font=f_sm)
    ly += 20 * len(lg) + 16
    lines = [f"지도 무대: 포스터의 {res['map_stage_pct_of_poster']}%", f"패널 {len(pz)}개, 포스터의 {res['panels_pct_of_poster']}%",
             f"오브젝트 합집합: 지도의 {res['density']['objects_union_pct']}%"]
    for cname, c in obj["core_groups"].items():
        lines += [f"[{cname}]", f"  덩어리 {c['mass_pct_of_map_stage']}% / 껍질 {c['hull_pct_of_map_stage']}%",
                  f"  외곽 상자 {c['bbox_pct_of_map_stage']}% (지도 대비)"]
    for t in lines:
        d.text((lx, ly), t, fill=(20, 20, 20), font=f_sm)
        ly += 17
    img = canvas
    p = os.path.join(OUT, f"{ref}_zones.png")
    img.save(p, optimize=True)
    print(p, img.size, "panels", len(pz), res["panels_total_mm2"], res["panels_pct_of_poster"], "stage%", res["map_stage_pct_of_poster"])
    for cname, c in cores.items():
        print(" ", cname, {k: v for k, v in c.items() if k.endswith("_as_rome_stage_pct") or k.endswith("_as_poster_pct")})


if __name__ == "__main__":
    main(sys.argv[1])
