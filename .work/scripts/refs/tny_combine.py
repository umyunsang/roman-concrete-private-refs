# -*- coding: utf-8 -*-
"""세 레퍼런스의 핵심 수치와 1차 실측 정정 내역을 한 파일로 모은다(데이터 파일)."""
import json, os
OUT = "/Users/um-yunsang/roman-concrete-private-refs/.work/out/refs-analysis"
refs = ["203x-tokyo", "203x-newyork2-centralpark", "203x-newyork"]
res = {"좌표계": "아트 2000x2800px(원본 타일 정합), 정규 좌표 = x/2000, y/2800, A2 mm = x*0.21, y*0.21214",
       "파일": {}, "핵심": {}}
for r in refs:
    a = json.load(open(os.path.join(OUT, f"{r}_analysis.json"), encoding="utf-8"))
    g = json.load(open(os.path.join(OUT, f"{r}_geo_fit.json"), encoding="utf-8"))
    gp = json.load(open(os.path.join(OUT, f"{r}_gaps.json"), encoding="utf-8"))
    la = json.load(open(os.path.join(OUT, f"{r}_label_angles.json"), encoding="utf-8"))
    res["파일"][r] = {k: os.path.join(OUT, f"{r}_{k}") for k in ("zones.png", "analysis.json", "objects.json", "network.json", "geo_fit.json", "gaps.json", "label_angles.json", "objects_vis.png")}
    res["핵심"][r] = {
        "지도무대_포스터대비%": a["map_stage_pct_of_poster"], "패널수": sum(1 for z in a["zones"] if z["kind"] == "panel"),
        "패널면적_포스터대비%": a["panels_pct_of_poster"], "밀도": a["density"],
        "코어군": {k: {"덩어리%": c["mass_pct_of_map_stage"], "볼록껍질%": c["hull_pct_of_map_stage"], "외곽상자%": c["bbox_pct_of_map_stage"],
                     "구성원상자합%": c["member_box_union_pct"], "로마무대환산_덩어리%": c["mass_pct_of_map_stage_as_rome_stage_pct"],
                     "로마무대환산_껍질%": c["hull_pct_of_map_stage_as_rome_stage_pct"], "무게중심_norm": c["centroid_norm"],
                     "외곽상자_mm": c["bbox_mm"], "모양": c["shape"]} for k, c in a["core_groups"].items()},
        "투영_지도창": a["angles"]["map_windows_hi"],
        "압축지리": {"평균오차mm": g["fit"]["mean_mm"], "RMSmm": g["fit"]["rms_mm"], "mm_per_km": g["fit"]["scale_mm_per_km"],
                  "북쪽_화면각": g["north_on_screen_deg(오른쪽=0, 위=+90)"], "거리법칙": g["distance_law"], "점수": g["n"]},
        "이웃간격": {"화소_중앙값mm": gp["median_pixel_gap_mm"], "상자_중앙값mm": gp["median_box_gap_mm"]},
        "라벨기울기": {k: v["baseline_deg"] for k, v in la.items()},
    }
res["1차실측_정정"] = {
    "203x-tokyo": [
        "코어 bbox 33.3%(포스터) → 37.9%(포스터)=지도 무대의 47.2%. 도쿄역 오른쪽 끝(x 863/1000)과 도쿄 타워 받침 아래(y 1084/1400)가 1차 상자 밖이었다.",
        "스미다강 '폭 약 70(포스터 폭 7%)'은 30° 띠를 가로로 자른 폭이다. 띠에 수직인 폭은 14.2~17.5mm(3.4~4.2%), 주 대각로 18.0mm와 같다.",
        "HISTORY 오른쪽 끝 960 → 914.5(글 블록 오른쪽 끝, 1000 기준).",
        "스카이트리 높이 59.3% → 탑 59.5%(받침 판 포함 61.1%). 꼭대기 y 75.5mm, HISTORY 패널 아래 3mm.",
    ],
    "203x-newyork2-centralpark": [
        "코어 bbox 41.5%(포스터, x0~830·y0~700)는 타이틀·하늘 모서리와 할렘까지 넣은 상자다. 센트럴파크+뮤지엄 마일만 재면 외곽 상자 28.3%(포스터)=지도의 29.5%, 실점유 덩어리 16.0%다. 북부 띠 전체도 덩어리 19.7%.",
        "이스트강 '폭 약 250'은 세로 두께(420~514px=210~257/1000)다. 띠에 수직인 폭은 76~94mm(포스터 폭 18~22%).",
        "CITY SYMBOL·CITY INFORMATION 오른쪽 끝 960 → 912~917(1000 기준).",
    ],
    "203x-newyork": [
        "히어로 엠파이어 높이 46.1% → 47.3%(안테나 끝 y 78.9mm~바닥 360.0mm). '타이틀 침범 아님' → 안테나 끝이 타이틀 아래 막대에 닿는다(겹침 0~4mm).",
        "코어 bbox 22.0%(포스터) → 26.2%(포스터)=지도의 31.9%(타임스스퀘어 라벨·플랫아이언 포함). 실점유 덩어리 19.7%.",
        "라벨 18개 → 약 21개 + 강 바닥 글 2(저해상 구역이 있어 ±2).",
        "투영 26.0°는 정확한 2:1(26.57°)보다 0.5° 낮다. 방위 45° 직교 투영이면 카메라 고도 약 29.2°.",
    ],
}
p = os.path.join(OUT, "tny_refs_analysis_tokyo_ny.json")
json.dump(res, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(p)
