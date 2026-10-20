"""구획 상자 확인용 이미지와 구획 JSON.

- 상자는 모두 앞선 실측 스크립트 결과(N 좌표 1000×1400)를 옮겨 적은 것이다.
  타이베이: r3_tightbox.py(패널·타이틀·푸터), r3_taipei_measure.py(지도·코어·랜드마크), r3_taipei_seg.py(강).
  제주: r3_tightbox.py, r3_jeju_measure.py.  자금성: r3_tightbox.py, r3_fc_measure.py, abc_inmap 크롭 판독.
- 출력: <ref>_zones.png(1.5배), r3_zones.json(0~1 정규 상자)
"""
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/refs")
from r3_common import OUT, load_norm  # noqa: E402

FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
COL = {"title": (255, 200, 0), "panel": (0, 200, 255), "map": (0, 200, 0), "core_group": (255, 0, 0), "hero": (255, 0, 160),
       "landmark": (255, 140, 0), "river": (0, 90, 255), "sea": (0, 60, 160), "road": (200, 160, 60), "legend": (120, 120, 120),
       "footer": (150, 150, 150), "other": (160, 0, 255)}

Z = {
    "203x-taipei": [
        ("타이틀(臺北 현판 액자)", "title", [293, 60, 710, 217], "건축 현판형 록업, 폭 41.7%, 175×67mm"),
        ("CITY INFORMATION 도시 정보", "panel", [55, 58, 245, 168], "좌측 열 1"),
        ("FAMOUS CULTURE AREA 문화지역", "panel", [55, 191, 244, 359], "좌측 열 2, 점 격자 위치도+핀 6"),
        ("CITY SYMBOL 도시 상징", "panel", [55, 387, 240, 485], "좌측 열 3, 아이콘 3"),
        ("NEARBY ATTRACTIONS 근교 볼거리", "panel", [55, 508, 228, 618], "좌측 열 4, 근교 3곳을 지도 밖 아이콘으로"),
        ("HISTORY 역사", "panel", [755, 58, 933, 192], "우상 1, 목록형 연표 7항목"),
        ("FAMOUS FOOD 유명한 음식", "panel", [55, 1203, 278, 1323], "좌하 1, 지도 위(밤 바탕)에 얹힘"),
        ("TRAFFIC LIGHT 신호등", "panel", [315, 1203, 431, 1325], "좌하 2"),
        ("지도 무대(전폭 띠)", "map", [0, 294, 1000, 1323], "세로 73.5%, 오른쪽 변만 블리드"),
        ("코어 군: 101 탑+판+몰+LOVE", "core_group", [176, 316, 525, 1140], "실면적 18,071mm² = 순 무대의 10.8%"),
        ("히어로: 타이베이 101", "hero", [266, 316, 399, 1038], "56×306mm, 포스터 높이 51.6%, x 33%"),
        ("고궁박물원", "landmark", [356, 295, 670, 524], "132×97mm"),
        ("디화제 기둥", "landmark", [696, 323, 728, 440], "13×50mm"),
        ("시립미술관", "landmark", [663, 420, 961, 641], "125×94mm"),
        ("스린 야시장(+101 라벨 판)", "landmark", [399, 549, 664, 817], "111×114mm"),
        ("그랜드 호텔", "landmark", [58, 657, 256, 888], "83×98mm"),
        ("타이베이 중앙역(+광장 판)", "landmark", [530, 720, 846, 961], "133×102mm"),
        ("공원 판(이름 없음)", "landmark", [770, 611, 1000, 801], "오른쪽 블리드"),
        ("용산사", "landmark", [21, 889, 202, 1086], "76×84mm"),
        ("라오허제 야시장", "landmark", [805, 795, 982, 1020], "74×96mm, 강 사이 반도"),
        ("시먼 홍러우", "landmark", [742, 1025, 960, 1228], "92×86mm"),
        ("닝샤 야시장", "landmark", [470, 1030, 646, 1256], "74×96mm(흩어진 소품)"),
        ("무지개 횡단보도", "landmark", [520, 1210, 706, 1323], "78×48mm, 바닥 그림"),
        ("택시", "other", [621, 470, 691, 522], "탈것 29×22mm, 깃대형 이름표"),
        ("시내버스", "other", [818, 565, 911, 641], "탈것 39×32mm, 깃대형 이름표"),
        ("고속철 THSR", "other", [496, 800, 613, 881], "탈것 49×34mm"),
        ("MRT", "other", [530, 904, 684, 1022], "탈것 65×50mm"),
        ("단수이강('<' 띠)", "river", [674, 779, 1000, 1156], "띠 폭(수직 단면×cos30°) 33~41N(14~17mm), 오른쪽 변 두 번 블리드"),
        ("길(도로망)", "road", [22, 294, 1000, 1318], "띠 폭 중앙값 35N(14.7mm; 수직 단면 40.5N×cos30°), ±30° 두 축"),
        ("푸터", "footer", [55, 1338, 945, 1362], "10mm"),
    ],
    "203x-jeju": [
        ("타이틀(FANTASTIC ISLAND / JEJU-DO)", "title", [240, 53, 759, 173], "글자 록업, 폭 51.9%, 218×51mm"),
        ("FORMATION 형성 과정", "panel", [49, 50, 211, 223], "좌상 1, 단면 도식 4단"),
        ("HISTORY 역사", "panel", [47, 255, 198, 409], "좌측 2, 목록형 연표 11항목"),
        ("PEOPLE 인물", "panel", [47, 433, 240, 569], "좌측 3, 초상 2"),
        ("SUMMARY 개요", "panel", [776, 50, 946, 207], "우상 1, 표+섬 크기 비교"),
        ("BUS 버스(노선 색 범례 겸용)", "legend", [765, 257, 953, 498], "우측 2, 버스 5종 색 = BUS ROUTE 노선 색"),
        ("ECOSYSTEM 제주의 식생(끌어낸 한라산 모형)", "panel", [269, 255, 724, 501], "중앙 상단, 191×104mm"),
        ("한라산 모형(히어로 역할)", "hero", [269, 290, 610, 497], "143×88mm, 지도 속 한라산의 약 2.9배"),
        ("BUS ROUTE 노선 지도(평면 정보 지도)", "map", [39, 505, 949, 920], "섬 실루엣 383×159mm, 같은 축척"),
        ("노선도 가운데 한라산", "landmark", [415, 650, 545, 745], "55×40mm"),
        ("PLACES TO GO 등각 지도", "map", [10, 880, 954, 1330], "섬 395×165mm, 오브젝트 약 60"),
        ("PLACES 섬 실루엣(지면, 코어 군 아님)", "map", [10, 924, 950, 1312], "포스터 15.3%, 섬 위 오브젝트 42.2%. 지역편이라 코어 군 없음"),
        ("한라산 국립공원(지도 중심)", "landmark", [418, 1036, 535, 1124], "49×37mm, 다른 명소와 같은 등급"),
        ("우도(작은 섬)", "landmark", [880, 900, 955, 962], "오른쪽 위 끝"),
        ("가파도·마라도(말풍선 인셋)", "landmark", [58, 1276, 170, 1327], "섬 밖 작은 섬은 인셋"),
        ("부속도서 위치도(짙은 파랑 실루엣)", "other", [605, 1250, 770, 1328], "ANNEXED ISLANDS 짝"),
        ("ANNEXED ISLANDS 부속도서", "panel", [725, 1218, 954, 1330], "우하, 지도 바다 위 글"),
        ("바다(바탕 전체)", "sea", [0, 0, 1000, 1400], "Lab(88,-11,-10) 단색+물결 무늬"),
        ("푸터", "footer", [49, 1340, 950, 1368], "12mm"),
    ],
    "203x-forbiddencity": [
        ("타이틀(지붕+붉은 판+紫禁城 편액)", "title", [240, 25, 765, 226], "건축 입면 록업, 폭 52.5%, 221×85mm"),
        ("전폭 처마 띠", "other", [0, 66, 1000, 110], "타이틀 지붕이 좌우 끝까지 이어짐"),
        ("SUMMARY 요약(왼쪽)", "panel", [39, 112, 268, 217], "위치도+수치 4"),
        ("SUMMARY 요약(오른쪽)", "panel", [728, 139, 970, 217], "건축가+수치 4"),
        ("HISTORY 역사(위 가로줄: 명·중화민국·중화인민공화국)", "panel", [35, 240, 494, 405], "가로 3단"),
        ("HISTORY 역사(왼쪽 세로 열: 청나라)", "panel", [35, 405, 180, 986], "황제 초상 연표, 세로 581N"),
        ("관모 도식(역사 부속)", "panel", [198, 428, 328, 497], "하조관·동조관"),
        ("ROOF BUILDING 지붕 9형식", "panel", [478, 240, 978, 492], "등각 지붕 9개, 궁역 오른쪽 위 하늘을 채움(지붕 유형 범례 역할)"),
        ("PLANE DRAWING 평면도", "panel", [38, 1008, 193, 1307], "좌하, 실제 평면"),
        ("지도 무대(궁역 세로 띠)", "map", [0, 416, 1000, 1316], "세로 64.3%"),
        ("코어 군: 궁역+끌어낸 모형 4", "core_group", [136, 416, 1000, 1316], "궁역 실면적 포스터 31.3% = 순 무대 58.9%(모형 포함 67.1%)"),
        ("끌어낸 모형 A 태화전", "hero", [192, 590, 392, 778], "건물 71×71mm = 지도 속의 2.0배"),
        ("끌어낸 모형 B 중화전", "hero", [340, 500, 488, 672], "건물 51×50mm = 2.1배"),
        ("끌어낸 모형 C 보화전", "hero", [458, 428, 640, 618], "건물 60×64mm = 1.9배"),
        ("천안문 모형(궁 남쪽 바깥, 제자리)", "hero", [238, 1078, 432, 1262], "71×64mm"),
        ("지도 속 A·B·C(갈색 외곽선 강조)", "landmark", [705, 748, 905, 935], "36×34 / 24×25 / 32×34mm"),
        ("오문(午門, 남문)", "landmark", [362, 1025, 548, 1178], "지도 속 남쪽 입구(ㄷ자 성문)"),
        ("해자(바깥 청록 띠)", "river", [136, 416, 1000, 1316], "띠 폭(수직 단면 15~16N×cos30°) 약 13.5N(5.7mm), 궁역 둘레"),
        ("푸터", "footer", [50, 1341, 951, 1369], "12mm"),
    ],
}

out = {}
for ref, zones in Z.items():
    im, _ = load_norm(ref)
    S = 1.5
    big = cv2.resize(im, (int(1000 * S), int(1400 * S)), interpolation=cv2.INTER_CUBIC)
    big = (big * 0.55 + 100).astype(np.uint8)
    pil = Image.fromarray(cv2.cvtColor(big, cv2.COLOR_BGR2RGB))
    dr = ImageDraw.Draw(pil, "RGBA")
    fnt = ImageFont.truetype(FONT, 17, index=0)
    fsm = ImageFont.truetype(FONT, 13, index=0)
    lst = []
    CONT = {"203x-taipei": [("taipei_core_mask.npy", (255, 0, 0))],
            "203x-forbiddencity": [("fc_palace_mask.npy", (255, 0, 0))],
            "203x-jeju": [("jeju_island_places.npy", (255, 0, 0)), ("jeju_island_bus.npy", (0, 160, 0))]}
    for fn, c in CONT.get(ref, []):
        mk = np.load(os.path.join(OUT, fn)).astype(np.uint8)
        mk = cv2.resize(mk, (int(1000 * S), int(1400 * S)), interpolation=cv2.INTER_NEAREST)
        cs, _ = cv2.findContours(mk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cc in cs:
            if cv2.contourArea(cc) < 500:
                continue
            pts = [tuple(int(v) for v in pt[0]) for pt in cc]
            dr.line(pts + [pts[0]], fill=c + (255,), width=3)
    for i, (name, kind, b, note) in enumerate(zones):
        x0, y0, x1, y1 = [v * S for v in b]
        c = COL[kind]
        if kind in ("sea",):
            dr.rectangle([x0 + 3, y0 + 3, x1 - 3, y1 - 3], outline=c + (255,), width=2)
        else:
            w = 4 if kind in ("core_group", "map") else 2
            dr.rectangle([x0, y0, x1, y1], outline=c + (255,), width=w)
        tag = f"{i + 1}. {name}"
        ty = y0 + 2 if kind not in ("map", "sea") else y1 - 22
        if kind == "core_group":
            ty = y0 + 22
        tw = dr.textlength(tag, font=fnt)
        dr.rectangle([x0 + 2, ty, x0 + 6 + tw, ty + 20], fill=(255, 255, 255, 215))
        dr.text((x0 + 4, ty), tag, font=fnt, fill=c[::-1][::-1] + (255,) if False else (0, 0, 0, 255))
        dr.rectangle([x0 + 2, ty + 1, x0 + 6, ty + 19], fill=c + (255,))
        lst.append({"name": name, "kind": kind, "bbox_norm": [round(b[0] / 1000, 4), round(b[1] / 1400, 4), round(b[2] / 1000, 4), round(b[3] / 1400, 4)], "note": note})
    # 범례
    lx, ly = 10, int(1400 * S) - 30
    for k, c in COL.items():
        dr.rectangle([lx, ly, lx + 14, ly + 14], fill=c + (255,))
        dr.text((lx + 18, ly - 1), k, font=fsm, fill=(0, 0, 0, 255))
        lx += 26 + int(dr.textlength(k, font=fsm))
    p = os.path.join(OUT, f"{ref}_zones.png")
    pil.save(p)
    out[ref] = {"markup_png": p, "zones": lst}
    print(p, len(lst))
with open(os.path.join(OUT, "r3_zones.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
