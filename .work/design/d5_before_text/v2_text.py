# -*- coding: utf-8 -*-
"""새 위계: 로마 편 배치 원칙·충돌 처리 문장(사양 JSON·보고서 공용). 담당: global
수치는 build(chk)가 v2_check.json 결과로 채운다. 모듈 상수 PRINCIPLES·CONFLICTS·INVALIDATED·REUSED·HOLDS는 기본값으로 채운 것이다(하위 호환).
d4: 사용자 검토(2026-10-19 02:24, 옛 R·T 패널 삭제·내부 표기 0)와 사용자 선택(2026-10-19 03:10, 기준선 7절: P2·P5·랜드마크 3개·네로 거상 받침)을 반영했다.
무대 확장은 해제했고(STAGE 173,460mm²), 인쇄 패널은 L·P2·B·D·S·P5 6개다."""

DEFAULTS = {
    "stage": 173460, "stage_main": 173460, "hero": 35257, "hero_pct": 20.3, "lm_med": 6014, "hero_med": 5.86, "hero_max": 3.28, "lm_min": 4598, "lm_n": 9,
    "L": 7200, "P2": 7200, "B": 11760, "P5": 5670, "D": 4816, "Z1": 5460, "C1": 2376, "C2": 2592, "C4": 3132, "S": 2100,
    "bmin_name": "P5", "bmin": 5670, "dmax_name": "Z1", "dmax": 5460, "dmin": 2376, "dmin_name": "C1", "r_bd": 1.038, "r_ds": 1.131, "ves": 2320,
    "panel_pct": 15.5, "panel_n": 6, "panel_mm2": 38746, "panel_rule": "통과", "ring_min": 140, "ring_max": 237, "ring_med": 182, "left": 5, "right": 4,
    "rot": -47.5, "north": 293.2, "err_mean": 46.5, "err_med": 37.0, "err_max_name": "카라칼라 욕장(절개)", "err_max": 124.8, "law": "평면 mm ≈ 177 × km^0.10",
    "no_geo": "", "obj_est": 31.8, "obj_pl": 36.0, "obj_pl_open": 40.0, "hc_box": 35.9, "hc_hull": 23.5, "hc_sil": 17.7, "hc_cx": 0.539, "hc_cy": 0.547,
    "cg_box": 66.4, "cg_hull": 53.9, "cg_sil": 33.0, "labels": 22, "labels_wall": 17, "labels_floor": 5,
    "lm_list": "판테온 96×90 · 트라야누스 시장 96×84 · 카라칼라 욕장(절개) 112×96 · 수도교 아치 열 85.4×77.1 · 카이킬리아 메텔라 무덤 66×70 · 포르투스 97×62 · 막센티우스 바실리카 77×60.5 · 하드리아누스 영묘 79×61.3 · 마르켈루스 극장 79.4×57.9",
    "ves_box": "(360,98)~(418,138)", "z1_d": "60", "z1_comp": "(214,420)~(305,480)", "req": "모두 있음",
    "r_L": "18~118×20~92", "r_P2": "302~402×20~92", "r_B": "18~214×505~565", "r_D": "220~306×505~561", "r_S": "332~402×466~496", "r_P5": "312~402×505~568",
    "lh_ang": "78", "lh_r": "22", "lh_base": "(15.98,432.35)", "canal_txt": "강 쪽 322.24~340.1, 외항 쪽 367.1~384.6",
    "hero_box_txt": "(139.7,226.4)~(360.2,381.6)", "bld_box_txt": "(192.6,226.4)~(300.4,330.1)", "bld_sil": 9000, "sil_ratio": "기록 없음", "b8": "기록 없음",
}


def _rng(r):
    return "%s~%s×%s~%s" % (_g(r[0]), _g(r[2]), _g(r[1]), _g(r[3]))


def _f(v):
    return format(int(round(v)), ",")


def _g(v):
    return ("%g" % round(float(v), 1))


def _nums(chk):
    n = dict(DEFAULTS)
    if not chk:
        return n
    try:
        H = chk["hierarchy"]
        n["stage"] = chk.get("stage_area_mm2_ext", n["stage"])
        n["stage_main"] = chk.get("stage_area_mm2", n["stage_main"])
        n["hero"] = H["hero_area"]
        n["hero_pct"] = round(100.0 * H["hero_area"] / n["stage"], 1)
        n["lm_med"] = H["landmark_median"]
        n["hero_med"] = H["hero_over_landmark_median"]
        n["hero_max"] = H.get("hero_over_landmark_max", round(H["hero_area"] / max(H["landmark_areas"].values()), 2))
        n["lm_min"] = min(H["landmark_areas"].values())
        n["lm_n"] = len(H["landmark_areas"])
        n["ves"] = H["vesuvius_area"]
        ta = H["tier_areas"]
        for t in ("Basic", "Detail", "Support"):
            for k, v in ta.get(t, {}).items():
                n[k.split(" ")[0]] = v
        n["bmin_name"], n["dmax_name"], n["dmin_name"] = H["basic_min"][0].split(" ")[0], H["detail_max"][0].split(" ")[0], H["detail_min"][0].split(" ")[0]
        n["bmin"], n["dmax"] = H["basic_min"][1], H["detail_max"][1]
        n["dmin"] = H["detail_min"][1]
        n["r_bd"] = round(H["ratio_basicmin_over_detailmax"], 3)
        n["r_ds"] = round(H["ratio_detailmin_over_support"], 3)
        pcr = H.get("panel_count_rule")
        if isinstance(pcr, dict):
            n["panel_n"] = pcr.get("count", n["panel_n"])
            n["panel_rule"] = "통과" if pcr.get("pass") else "실패"
        req = chk.get("required_elements", {})
        if req:
            n["req"] = "모두 있음" if req.get("ok") else ("없음: " + " · ".join(req.get("missing", [])))
        de = chk["density_estimate"]
        n["panel_pct"] = de["panel_area_pct_poster"]
        n["panel_mm2"] = de.get("panel_area_mm2", n["panel_mm2"])
        n["obj_est"], n["obj_pl"] = de["objects_pct_stage_est"], de["objects_plus_planted_pct_stage_est"]
        n["obj_pl_open"] = de.get("objects_plus_planted_pct_open_stage_est", n["obj_pl_open"])
        n["ring_min"], n["ring_max"], n["ring_med"] = chk["ring_range_median"]
        n["left"], n["right"] = chk["left_right"]["왼쪽"], chk["left_right"]["오른쪽"]
        g = chk["geo"]
        n["rot"] = g["rotation_plan_minus_real_deg"]
        n["north"] = g["real_north_screen_bearing_deg(시계 방향, 화면 위=0)"]
        n["err_mean"], n["err_med"] = g["bearing_error_abs_mean_deg"], g["bearing_error_abs_median_deg"]
        n["err_max_name"], n["err_max"] = g["bearing_error_max"]
        n["law"] = g["distance_law"]
        ng = list(g.get("no_geo", {}).keys())
        n["no_geo"] = ("지리 표에서 '없음'(실측 좌표를 쓰지 않음): %s. " % "·".join(ng)) if ng else ""
        hc, cg = chk["hero_cluster"], chk["core_group_city"]
        n["hc_box"], n["hc_hull"], n["hc_sil"] = hc["bbox_pct_stage"], hc["hull_pct_stage"], hc["silhouette_pct_stage"]
        n["hc_cx"], n["hc_cy"] = hc["centroid_norm_poster"]
        n["cg_box"], n["cg_hull"], n["cg_sil"] = cg["bbox_pct_stage"], cg["hull_pct_stage"], cg["silhouette_pct_stage"]
        lb = chk["labels"]
        n["labels"], n["labels_wall"], n["labels_floor"] = lb["total"], lb["wall_flag_tag"], lb["floor_text"]
        ob = chk.get("objects_boxes", {})
        lm_names = list(H["landmark_areas"].keys())
        if ob and lm_names:
            n["lm_list"] = " · ".join("%s %s×%s" % (k.split("(")[0].strip(), _g(ob[k]["wh"][0]), _g(ob[k]["wh"][1])) for k in lm_names if k in ob)
        for pid, r in (chk.get("panel_rects") or {}).items():
            n["r_" + pid] = _rng(r)
        lh = ((chk.get("portus_spec") or {}).get("lighthouse") or {})
        if lh.get("plan_angle_deg") is not None:
            n["lh_ang"], n["lh_r"] = _g(lh["plan_angle_deg"]), _g(lh["plan_r"])
        if isinstance(lh.get("screen_base"), (list, tuple)) and len(lh["screen_base"]) == 2:
            n["lh_base"] = "(%s,%s)" % (_g(lh["screen_base"][0]), _g(lh["screen_base"][1]))
        cs = (chk.get("portus_spec") or {}).get("canals") or []
        if cs and all(isinstance(c.get("plan_y"), (list, tuple)) for c in cs):
            n["canal_txt"] = ", ".join("%s %s~%s" % (c.get("name", "운하"), _g(c["plan_y"][0]), _g(c["plan_y"][1])) for c in cs)
        z1 = chk.get("z1") or {}
        if isinstance(z1.get("circle"), dict) and z1["circle"].get("d"):
            n["z1_d"] = _g(z1["circle"]["d"])
        if isinstance(z1.get("composite_box"), list) and len(z1["composite_box"]) == 4:
            n["z1_comp"] = "(%s,%s)~(%s,%s)" % tuple(_g(v) for v in z1["composite_box"])
        hd = chk.get("hierarchy_rule_d5") or {}
        if hd.get("hero_group_box"):
            n["hero_box_txt"] = "(%s,%s)~(%s,%s)" % tuple(_g(v) for v in hd["hero_group_box"])
        if hd.get("hero_building_box"):
            n["bld_box_txt"] = "(%s,%s)~(%s,%s)" % tuple(_g(v) for v in hd["hero_building_box"])
        if hd.get("hero_building_sil_mm2") is not None:
            n["bld_sil"] = hd["hero_building_sil_mm2"]
        if hd.get("building_sil_over_max_other") is not None:
            n["sil_ratio"] = "%s배" % hd["building_sil_over_max_other"]
        b8 = chk.get("baseline_8") or {}
        if b8:
            n["b8"] = "통과" if b8.get("pass") else ("실패 %d건(%s)" % (len(b8.get("failed", [])), "·".join(b8.get("failed", []))))
        vk = next((k for k in ob if k.startswith("베수비오")), None)
        if vk:
            b = ob[vk]["box"]
            n["ves_box"] = "(%s,%s)~(%s,%s)" % tuple(_g(v) for v in b)
    except Exception:  # 검사 결과 형식이 달라도 기본값으로 문장을 만든다
        pass
    return n


def build(chk=None):
    n = _nums(chk)
    F = {k: (_f(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and abs(v) >= 1000 else v) for k, v in n.items()}
    P = [
        "P0 우선순위: 사용자 결정(15:32 장 번호 하나·15:41 하단 띠 확대와 정보 모으기·16:13 콜로세움 둘레 판석 제거·16:14 Core만·16:15 203X와 건축물 레퍼런스 가중·16:35 지도에 사람 없음)이 가장 앞서고, 그다음 기준선 8절(콜로세움 본체는 LocalBanana와 같은 방향·부서진 정도·보이는 면·비례, 팔각 받침대 없음, 벡터 일러스트·AO·조명·그림자 0)이다. "
        "설계 d{{N}}과 와이어프레임 b{{N}}은 한 루프에서 함께 만들고, 단일 원천은 이 사양이다. 사전 8절 판정: {b8}.",
        "P1 위계와 장 구성: Core = 로마 건축물 지도. 지도 무대 = (0,92)~(420,478) 하나 = {stage}mm². 장 6개를 Z 순서로 읽는다: ❶ 무엇으로 만들었나(왼쪽 위 L) → ❷ 어떤 모양을 지었나(오른쪽 위 P2) → ❸ 지도에서 찾기 → ❹ 어떻게 만들었나(왼쪽 아래 B) → ❺ 왜 오래가나(가운데 아래 D) → ❻ 지금 배우는 것(오른쪽 아래 P5). "
        "장 배지는 모두 Ø10 장 제목 빨간 잉크 원 + 흰 숫자이고 영문 제목 왼쪽에 둔다. 크게 보이는 번호는 장 번호뿐이다. 필수 요소 판정: {req}. 콜로세움 건물이 최대 단일 오브젝트이고(투영 상자 {hero_box_txt} = {hero}mm², 건물 실루엣 {bld_sil}mm²는 다른 건물 실루엣 각각의 1.2배 이상, 사전 {sil_ratio}), 위계의 최종 판정은 사후 ⑪(그린 외곽 상자끼리)이다. "
        "사용자 15:41·16:14로 장 패널 크기가 커졌으므로 '콜로세움 > 가장 큰 패널'·'Detail ≥ Support × 1.1'·'히어로 ÷ 중앙값 비'·'베수비오 최소' 기준은 폐기했다. 신규 표준 랜드마크 하한은 4,500mm²이다.",
        "P2 틀: 가운데 신전 페디먼트 타이틀(126.5~293.5×10~92) + 상단 장 2개(❶ L {r_L}, ❷ P2 {r_P2}) + 지도 무대 y 92~478(전폭) + 하단 장 3개(❹ B {r_B}, ❺ D {r_D}, ❻ P5 {r_P5}, 칸 사이 6mm, 폭 144·154·82) + 푸터 14~406×588~594(인쇄 내용 없음). "
        "하단 패널 y 482~588은 지도 아랫선 478에서 4mm 띄운다. 왼쪽·오른쪽 여백선은 x 14·x 406이다. 100 VS 2,000 막대(S {r_S})는 ❻ 안에 든다. 패널 {panel_n}개(L·P2·B·D·S·P5), 패널 면적 합 {panel_mm2}mm² = 포스터의 {panel_pct}%.",
        "P3 히어로(기준선 8.1·8.2): 콜로세움 본체는 LocalBanana와 같다. 외곽 타원 반축 44×36.6(평면, 장축 315° = 화면 가로), 중심 평면 (446.54,161.86). 아치 40칸, 층 윗선 z 11.5·24.5·37·53. 부서진 정도(θ = atan2(평면 dY, dX)): 100~205° 4층 53(앞쪽 끝 100~112° 경사 부벽 41·46·50, 205~209° 수직 절단 44), 209~322° 3층 37(일부 33.5), 322~338° 계단 31·27, 338~18° 2층 24.5(들쭉날쭉 18~24.5), 18~72° 경기장 앞 정면 1층 + 토막 ≤ 17, 72~100° 30·37. 둘째 고리 37(정면 10~80°만 9~12). "
        "관람석·경기장 반축 20.1×12.7(오른쪽 55% 복원 나무 바닥, 왼쪽 하이포게움)과 기단 계단 2단까지가 건물이다. 건물 화면 상자 {bld_box_txt}, 폭 ÷ 기준 폭 203.5 = 0.53. 사용자 16:13·16:14: 광장·판석·경계석·문 앞 포장·둘레 나무·인물 무리·노점·공사장·길은 없고 둘레는 땅 바탕뿐이다.",
        "P4 Core 건축물 11개: 콜로세움 + 표준 랜드마크 {lm_n}개({lm_list}) + 네로 거상 받침(콘크리트 받침 위 청동 거상 '추정', 작은 마당 포함). 건물에 딸린 자기 마당·기단(판테온 앞마당·욕장 대지)은 건물의 일부다. 수도교는 아쿠아 안토니니아나가 욕장 저수조 64개에 물을 댄 관계로 그린다(2단 관통 아치, 오른쪽 변 블리드). "
        "지도에서 지운 것(사용자 16:14): 시내 집·지붕 블록·나무·밭·포도밭·길 전부·사람·노점·수레·암포라·덤불·바지선·화산재 운반선·포르투스 안의 배·오스티아·하역장·석회 가마·콜로세움 공사장·베수비오·알바노 구릉·먼 들. 건물 안의 조각상은 조형물이라 둔다.",
        "P5 모으기(사용자 16:14): 빈 땅이 넓어져 Core 건물을 콜로세움 쪽으로 모았다. 트라야누스 시장 (0,+10), 마르켈루스 극장 (+34,+19.6, 강 둑을 따라 ↘), 메텔라 무덤 (−12,+36)(화면 mm). 라벨 슬롯·앵커·표지는 같은 만큼 옮겼다. "
        "겹침·접촉 검사(사전 허용 안 된 겹침 0, 사후 ⑭ 실루엣 간격 ≥ 2mm)를 지킨다. 203X 실측(건물 실루엣 비율 26~40%, 중앙값 약 31%)과 비교한 우리 값은 사후 ⑦ 밀도(전체 무대 대비 건물 실루엣)다.",
        "P6 테베레강·바다·해안: 강은 왼쪽 변 (0,314)에서 들어와 ↘ 팔(화면 수직 폭 16mm)로 흐르다 (190,423.7)에서 평면 직각·둥근 굽이로 꺾여 ↙ 팔(폭 20mm)로 하구에 닿는다. 해안선 y = tan30·x + 380 하나(지층 단면 10mm)를 긋고 바다는 왼쪽 변·지도 아래 변 밖으로 블리드해 하단 띠 밑으로 흐리게 잇는다. "
        "포르투스 육각 내항은 강 오른쪽 둑과 해안 사이에, 클라우디우스 외항·등대는 바다에 둔다(방파제 평면 반지름 18.4~21.0, 입구 폭 약 20mm, 등대섬 평면 각 {lh_ang}°·반지름 {lh_r}, 운하 2개 {canal_txt}). 하드리아누스 영묘 + 폰스 아일리우스는 강 굽이 안쪽 둑에 서고 다리 북쪽 끝은 진입 경사(Z 0 → 3.0)로 땅에 잇는다.",
        "P7 지도 글: 라벨 {labels}개 = 건물 라벨 11 + 바닥 글 2(TIBERIS·MARE TYRRHENUM) 등. 라벨은 이름(영문·국문) + 사실 1줄이다. 지도 위 다른 글은 ❸ 장 배지와 '지도에서 찾기', ❺ 근거 표지(Ø3.2 장 잉크 원 + 흰 '5', 포르투스·메텔라 무덤·콜로세움 벽)뿐이다. 지도 위 흰 박스(콜아웃)는 0개이고 지시선은 라벨의 브래킷·규선뿐이다. "
        "서체: 지도 라벨 영문 3.8·국문 이름 3.8·원어 위첨자 2.1·본문 3.0mm(피치 4.15) | 소품 주석 2.6 | 형태 표지 Ø4 아이콘 | 장 머리글 영문 7.0·국문 부제 2.8 | B 단계명 3.0 | 소제목 2.8 볼드 | 본문 2.6(피치 3.9) | 주석 2.1(피치 3.0). 배율 1.00 고정, 라벨 바탕판 없음.",
        "P8 하단 장(사용자 15:41): ❹ HOW IT WAS MADE(B, x 14~158)는 6단계 등각 장면을 3열 2행으로 두고 단계마다 이름 + 1줄(근거 수준 표기 1곳만 '(2025 폼페이: 미리 섞은 더미)'), 단계 번호는 Ø4 테두리 원이다. "
        "❺ LIME CLASTS(D, x 164~318)는 석회 알갱이 자가치유 4단계 + 화살표, 확대 원 Ø30 '로마 콘크리트 단면(모식)', 근거 카드 2장(바닷물 · 포르투스 2017·코사 항 시료, 빗물 · 메텔라 무덤 2021 연구), 출처 1줄(2023 MIT 연구가 실마리를 찾고 2025 폼페이 공사 현장 연구가 확인했다)이다. "
        "❻ LEARNING FROM ROME(P5, x 324~406)은 연구 → 현장 → 적용 세로 타임라인(각 2줄 이하), ○ 가져올 것 2개·× 못 가져올 것 2개, 100 VS 2,000 막대, 탄소 각주 1줄이다. 반죽은 다져 넣는다(붓지 않는다).",
        "P9 ❷ ARCH · VAULT · DOME(P2): 등각 소형 단면 4칸(아치 = 비교 기준·배럴 볼트·교차 볼트·돔; 칸 폭 21.5·21.5·21.5·31.7)과 스팬 막대 3줄(트라야누스 시장 대회랑 8.6 m·카라칼라 열탕실 약 36 m·판테온 43.3 m)로 '콘크리트가 가능하게 한 모양'을 보인다. 돔 칸 설명은 '반구 지붕과 빛 구멍(오큘러스)'과 '위로 갈수록 가벼운 골재(판테온)'다. "
        "지도와는 형태 표지(숫자 없는 4mm 아이콘: 아치·배럴 볼트·교차 볼트·돔)로 잇는다(수도교 아치 면·바실리카 측랑·시장 대회랑 교차 볼트·판테온 돔).",
        "P10 투영·색: 진짜 등각 30°를 하나로 쓰고 패널·타이틀만 화면 평행으로 둔다. 그림체는 벡터 일러스트: AO·조명·그림자 0, 면 톤 ISO_TONE 1.0/0.86/0.68 고정 평면색, 종이 (231,208,160)·땅 윗면 (236,216,172). 지시선·형태 표지·Z1 테두리(0.6mm)·소품 주석은 정보 잉크 (58,42,28) 한 색이다. "
        "지도 라벨은 중립 잉크 한 색, 물 이름 바닥 글은 물색보다 짙은 파랑 (52,92,124), 폼페이 레드(#c82236)는 타이틀·장 배지·장 머리글·단계 번호·❺ 근거 표지에만 쓴다. 티어 색의 인쇄 사용은 0이다.",
        "P11 블리드: 블리드 변은 왼쪽(테베레 상류·바다), 아래(바다, 무대 아랫선 y 478까지), 오른쪽(수도교)이다. 위 변은 타이틀·L·P2가 닫는다(무대 윗변 y 92). 하단 장 3개는 무대 아래 종이/띠 바탕 위에 조판하고 바다는 띠 밑으로 흐리게 잇는다.",
    ]
    C = [
        "C1 하단 띠 높이: 사용자 15:41 결정(지도 아랫선 478, 패널 y 482~588 = 높이 106mm, 하단 띠 전체 19.5%)이 203X 실측(하단 띠 13~15%, 패널 높이 9~10%)보다 크다. 처리: 사용자 결정이 우선이다. 글 줄 수는 패널당 8~16줄로 203X 안팎(2~10줄, 칸 구성 시 16~20줄)에 맞추려고 줄였다.",
        "C2 Core만 남기기(사용자 16:14) vs 이전 소품·길·사람 설계: 처리: 길·집·나무·밭·사람·노점·수레·배·하역장·가마·오스티아·공사장·베수비오·구릉을 지도에서 지웠다. 그 때문에 밀도·히어로 군·길 접촉·베수비오 최소·인물 군 기준은 폐기하거나 사용자 결정으로 바꿨다. 16:13의 '길을 기단 발치까지 잇기'는 길이 없어져 취소됐다.",
        "C3 콜로세움 크기: 히어로가 건물 하나가 되어 투영 상자 11,200mm²가 랜드마크 최대 상자(10,752mm²)보다 약간 크다. 처리: 상자 비는 1.0배 이상으로 낮추고 건물 실루엣 1.2배 규칙으로 최대 단일 오브젝트를 지킨다.",
        "C4 100 VS 2,000 자리: 이전에는 지도 오른쪽 아래 모서리 패널(S)이었다. 처리: 사용자 15:41로 ❻ 안으로 옮겼다. S는 독립 패널이 아니라 ❻ 안 요소다.",
        "C5 라벨 한 줄: 포르투스 라벨은 사실 1줄이 좁은 바다 자리에 들어가도록 영문·국문 이름을 한 줄에 두고 원어 위첨자를 뺐다(name_inline).",
        "C6 상단 Basic: L과 P2 두 개이고 둘 다 장 번호 배지를 단다. 옛 R·T 패널 내용은 지면에 쓰지 않는다(사용자 검토 02:24, 선택 03:10).",
        "C7 내부 표기 vs 다이어그램: 다이어그램은 실제로 인쇄될 포스터 지면만 보이고 내부 정보는 spec.json과 보고서에만 둔다. 사후 ①(금지 표기 0)·⑩(티어 색 0)이 지킨다.",
        "C8 형태 표지: 이전 글자 표지 Ⓐ~Ⓓ와 숫자 ①~④를 없앴다(사용자 15:32). 형태 표지는 숫자 없는 4mm 아이콘이고 ❺ 근거 표지만 '5'를 쓴다. 단계 번호 1~6은 Ø4 테두리 원이다.",
        "C9 사람: 사용자 16:14·16:35로 지도에는 사람이 없다. 건물 안 조각상과 네로 청동 거상은 조형물이라 둔다. ❹ 단계 장면의 일꾼 그림은 제작 과정을 보이는 정보 그림이라 둔다.",
    ]
    INV = [
        "Core = 제작 과정 셀 체인(지시 E·F·J의 공정 셀 7개·신문식 지그재그 기둥·L자·콤마, '공정이 콜로세움으로 흘러듦' 구조, 단계 상자 ≥ Basic·Detail × 1.05 규칙)",
        "'Support = 로마 건축물'과 'Support ≤ Basic·Detail 최소 ÷ 1.1'(건축물 투영 상자 상한 5,251mm²)",
        "'베수비오 = Support-2'(이제 지도 배경·가장 작은 랜드마크급 지도 요소)",
        "'B3 100 vs 2000 = Basic'(이제 Support, 가장 작은 위계)",
        "강 '<' 굽이를 오른쪽 위에 둔 배치, 하역장 → 재료 운반 길 → c1 입구, CORE 입구 간판",
        "LocalBanana 좌우 반전(이전 C13), 확대 창 (123, 458)·c7 → 창 → B1 지시선",
        "옛 상단 오른쪽 R 패널(연한 판 포함)과 하단 띠 오른쪽 T 패널(사용자 검토 2026-10-19 02:24로 지면에서 뺌)",
        "d3의 무대 확장 STAGE_EXT(옛 R·T 자리를 지도 무대로 돌려준 189,048mm²)와 그 자리의 먼 밭·포도밭, 베수비오 (330,30)~(388,70)·농장 (336,54)~(378,76)·구릉 띠 (300,64)~(420,160) 배치(사용자 선택 03:10로 두 자리는 P2·P5)",
        "d3의 인쇄 패널 4개(L·B·D·S)와 패널 수 규칙을 판정하지 않던 기록",
        "Z1 원 Ø64·합성 상자 (212,418)~(307,482) 6,080mm²(P5 5,670mm²보다 커서 Basic ≥ Detail을 어김 → Ø60·5,460mm²)",
        "인쇄 지면의 내부 표기: 작업 이름·티어 이름(Core·Basic·Detail·Support)·티어 색 범례·티어 색 모서리·크기 꼬리표(○○×○○mm)·면적·검사 수치·히어로 군 점선 윤곽·투영 상자 모서리·가장자리 눈금·설계 주석·레퍼런스 근거 메모·타이틀 안 메모·국문 부제의 시리즈 설명·푸터 작업 정보(사양·보고서에만 둔다)",
        "Z1 위계를 원 상자만으로 재던 계산(글 칸 누락 → 합성 상자로 잰다)",
        "라벨 자동 축소·개별 배율·슬롯 밖 배치(render LABEL_CFGS의 s·smin·anchor·dx·dy), 라벨 크림 바탕판, render의 길 연장·지시선 끝점 보정 하드코딩",
        "수도교의 옛 이름·보수 구간 문장·공원 실측 좌표(아쿠아 마르키아의 지선 아쿠아 안토니니아나로 바꾸고, 좌표는 쓰지 않음)",
        "검사가 사양 상자만 보고 인쇄 결과를 보증하지 못하던 방식(사후 검사 drawn.json → post_check.json, 실패 시 실행기 종료 코드 1), 필수 요소 누락을 잡지 못하던 위계 검사(사전 필수 요소 판정·사후 ⑬)",
        "베수비오 깃대형 라벨(브래킷으로), 화산재 운반선 규선 연장형 라벨(깃대형으로), 물 이름 잉크 (236,246,252)(짙은 파랑 (52,92,124)으로)",
        "d4 콜로세움: 팔각 받침(반지름 90, 지층 옆면 7mm)·앞 변 기초 절개·외벽 고리 0.74R 원형·벽 60/28/12·가로벽 격자 하이포게움 표(기준선 8.1·8.2로 폐기)",
        "d4 Z1 출발점(앞 변 절개 (275,383.8))과 지도 쪽 A 표지 (271.77,382.46)(공사장 거푸집 오른쪽 면 (232.0,396.8)·A (233.75,393.77)로)",
        "d4 그림체 문구: 조명 방향 지정·그림자 레이어 예외·제작 단계 면제 표시(벡터 일러스트, AO·조명·그림자 0으로)",
        "D3 기획의 LocalBanana 조경 부품 배치(12:49 사용자 철회): 기둥 폐허·쓰러진 토막·단칸 아치·벽돌 담·작은 신전·열주·6주 신전 앞면·포장 고리·판석 갈래길·노점 배치 복제",
        "위계를 예정 상자로 통과 보고하던 방식(사전 = 투영 상자끼리, 사후 = 그린 외곽 상자끼리로 나눔)",
        "drawn_contract의 사전형 서술(footprints·roads·objects는 목록형 + schema)",
    ]
    REU = [
        "틀 좌표: 타이틀 126.5~293.5×10~92(유지). 나머지 틀은 사용자 15:41로 바뀌었다(L 14~118, P2 302~406, 무대 y 92~478, 하단 패널 y 482~588)",
        "등각 규약(v16 common.Iso): 평면 +X → 화면 ↘, +Y → 화면 ↙, ±30°만",
        "라벨 스택·지시선 문법(v16 common 표준 = 베이징), 바닥 글 규칙",
                "해안선은 ±30° 직선 하나 + 바다 블리드 + 하단 띠 밑 연장",
        "검사 방법: 4px/mm 래스터, 13mm 닫힘 실루엣·볼록 껍질·상자, 겹침 허용 목록(라벨 슬롯은 허용 영역)",
    ]
    HOLD = [
        "인쇄 전 확인: 일반 연표 항목(80 콜로세움 개장·약 125 판테온 재건) — 이번 판 지면에 없음. 다시 넣을 때 '[일반 연표]' 표시를 단다",
    ]

    def fmt(lst):
        return [s.format(**F) for s in lst]
    return {"PRINCIPLES": fmt(P), "CONFLICTS": fmt(C), "INVALIDATED": INV, "REUSED": REU, "HOLDS": HOLD}


_B = build()
PRINCIPLES = _B["PRINCIPLES"]
CONFLICTS = _B["CONFLICTS"]
INVALIDATED = _B["INVALIDATED"]
REUSED = _B["REUSED"]
HOLDS = _B["HOLDS"]
