"""203X 도시 인포그래픽 후보의 지면 구성 실측값 정리 (2026-10-18).

- 좌표: 포스터 전체를 1000x1400 정규 좌표로 맞춘 격자 위에서 눈으로 짚은 값(±15 단위).
  격자 이미지는 refs_cities_grid.py가 만든 .work/out/refs-cities-grid/*.jpg.
- 박스 형식: (x0, y0, x1, y1). 'core'는 중심 군의 바깥 상자(bbox)라 실제 면적보다 크게 나온다.
- 출력: JSON(다음 단계 워크플로용), 마크다운 표, 박스를 그린 검증용 이미지와 모음.
- 사용: uv run --no-project --with pillow python -I refs_cities_measure.py <dl루트> <출력폴더>
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1000, 1400
FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"

# slug: 이미지 상대경로, 타이틀, 패널(이름, 자리, 박스), 지도 세로 범위, 히어로, 코어, 물, 라벨 수
DATA = {
    "203x-beijing": dict(
        img="203x-beijing/StH_2024_03_Poster.jpg", issue="2024-03",
        title=(320, 45, 680, 215),
        panels=[("CITY INFORMATION", "TL", (50, 50, 250, 160)), ("FAMOUS CULTURE AREA", "TL", (50, 175, 300, 345)),
                ("HISTORY", "TR", (750, 50, 950, 245)), ("REPRESENTATIVE ARCHITECTURE", "B", (50, 1185, 420, 1320)),
                ("FAMOUS FOOD", "B", (430, 1185, 720, 1340)), ("OLYMPICS", "B", (755, 1185, 950, 1320))],
        map_y=(190, 1190), hero=("CCTV Tower", (40, 300, 230, 1010)), core=("자금성 블록+해자+천안문", (500, 300, 1000, 900)),
        water="대각 강 띠(폭 약 60)+자금성 해자", labels=17),
    "203x-hongkong": dict(
        img="203x-hongkong/StH_2022_04_Tokyo.jpg", issue="2022-04",
        title=(275, 20, 725, 215),
        panels=[("CITY INFORMATION", "TL", (50, 50, 245, 160)), ("FAMOUS CULTURE AREA", "TL", (50, 185, 250, 320)),
                ("HISTORY", "TR", (755, 50, 955, 245)), ("TOP 5 SKYSCRAPERS", "B", (50, 1200, 300, 1330)),
                ("FAMOUS FOOD", "B", (390, 1205, 620, 1335)), ("HONG KONG TAXI", "B", (655, 1205, 955, 1320))],
        map_y=(195, 1200), hero=("ICC(좌측 기둥)", (45, 495, 200, 1200)), core=("센트럴 마천루 군+관람차", (230, 195, 840, 960)),
        water="빅토리아 항을 폭 약 90의 수로로 압축", labels=16),
    "203x-seoul": dict(
        img="203x-seoul/seoul-4-1.jpg", issue="2018-09",
        title=(340, 65, 660, 250),
        panels=[("SUMMARY", "TL", (50, 70, 250, 190)), ("SYMBOL", "TL", (50, 200, 250, 390)),
                ("HISTORY", "TR", (750, 70, 960, 215)), ("PERSON IN SEOUL", "B", (50, 1175, 240, 1330)),
                ("HANGANG RIVER BRIDGES", "B", (260, 1175, 720, 1330)), ("FAMOUS CULTURE AREA", "B", (750, 1175, 960, 1330))],
        map_y=(260, 1110), hero=("롯데월드타워", (700, 510, 860, 1025)), core=("숭례문+남산타워+롯데타워", (490, 260, 870, 1030)),
        water="청계천 수로(폭 약 30)+판 아래 한강 띠", labels=16),
    "203x-newyork": dict(
        img="203x-newyork/New-York1.jpg", issue="2018-03",
        title=(50, 45, 670, 195),
        panels=[("CITY INFORMATION", "L", (50, 235, 250, 495)), ("CITY SYMBOL", "L", (50, 500, 250, 555)),
                ("HISTORY", "TR", (750, 50, 960, 200)), ("ART IN NEW YORK", "R", (750, 905, 960, 1150)),
                ("ART MUSEUM", "R", (750, 1155, 960, 1320)), ("NIGHT VIEW POINTS TOP 3", "B", (300, 1215, 730, 1330))],
        map_y=(195, 1290), hero=("엠파이어 스테이트 빌딩", (555, 195, 680, 840)), core=("미드타운 군", (330, 195, 800, 850)),
        water="허드슨·이스트강 대각 띠 2개", labels=18),
    "203x-newyork2-centralpark": dict(
        img="203x-newyork2-centralpark/StH_202209_158_new-york2.jpg", issue="2022-09",
        title=(50, 55, 430, 195),
        panels=[("위치 인셋", "BR", (725, 840, 850, 990)), ("CITY SYMBOL", "BR", (720, 995, 960, 1060)),
                ("CITY INFORMATION", "BR", (720, 1070, 960, 1320)), ("ART IN NEW YORK", "B", (505, 1120, 700, 1330)),
                ("ART MUSEUM", "B", (300, 1150, 500, 1320))],
        map_y=(0, 1330), hero=("센트럴파크(가로 지면)", (330, 250, 700, 520)), core=("공원+뮤지엄 마일", (0, 0, 830, 700)),
        water="이스트강 폭 약 250 대각 띠(패널 받침)", labels=20),
    "203x-tokyo": dict(
        img="203x-tokyo/StH_2021_05_Poster_Tokyo-1.jpg", issue="2021-05",
        title=(250, 20, 750, 215),
        panels=[("CITY INFORMATION", "L", (50, 45, 245, 165)), ("FAMOUS CULTURE AREA", "L", (50, 180, 245, 340)),
                ("CITY SYMBOL", "L", (50, 365, 245, 540)), ("FAMOUS FOOD", "L", (50, 560, 245, 655)),
                ("HISTORY", "TR", (755, 45, 960, 175)), ("BRIDGES OF SUMIDA RIVER", "BL", (50, 1170, 350, 1335))],
        map_y=(180, 1345), hero=("도쿄 스카이트리", (835, 180, 970, 1010)), core=("황궁·도쿄타워·도청 군", (255, 230, 830, 1040)),
        water="스미다강 폭 약 70 길", labels=21),
    "203x-paris": dict(
        img="203x-paris/StH_2021_04_Poster_Paris2.jpg", issue="2021-04",
        title=(270, 35, 730, 260),
        panels=[("CITY INFORMATION", "L", (50, 50, 245, 165)), ("CITY SYMBOL", "L", (50, 185, 245, 305)),
                ("ARTIST IN PARIS", "L", (50, 330, 245, 445)), ("HISTORY", "TR", (755, 50, 960, 170)),
                ("FAMOUS BREAD", "TR", (755, 185, 960, 360)), ("BRIDGES OF SEINE RIVER", "BL", (50, 1170, 355, 1335))],
        map_y=(265, 1290), hero=("에펠탑", (320, 232, 760, 1150)), core=("에펠탑+받침 판", (290, 232, 835, 1240)),
        water="센강 폭 약 60(세로·가로 구간)", labels=15),
    "203x-london": dict(
        img="203x-london/london1.jpg", issue="2017-12",
        title=(315, 40, 950, 195),
        panels=[("HISTORY", "TL", (50, 50, 250, 240)), ("WILLIAM MORRIS", "TL", (50, 245, 250, 335)),
                ("CITY INFORMATION", "TR", (750, 210, 950, 380)), ("FAMOUS FESTIVALS", "R", (750, 920, 960, 1200)),
                ("STREET PERFORMANCE", "R", (750, 1210, 960, 1330)), ("HARRY BECK", "B", (50, 1210, 250, 1330)),
                ("BUS LINE 9", "B", (330, 1210, 690, 1330))],
        map_y=(45, 1180), hero=("빅벤", (270, 45, 500, 1065)), core=("랜드마크 한 덩어리 전체", (40, 45, 960, 1180)),
        water="템스강 가는 띠(최소)", labels=11),
    "203x-shanghai": dict(
        img="203x-shanghai/shanghai_poster.jpg", issue="2020-12",
        title=(265, 20, 745, 240),
        panels=[("CITY INFORMATION", "L", (50, 70, 245, 190)), ("FAMOUS CULTURE AREA", "L", (50, 205, 245, 385)),
                ("CITY SYMBOLS", "L", (50, 400, 245, 470)), ("HISTORY", "TR", (765, 70, 960, 260)),
                ("TOP 4 SKYSCRAPERS", "B", (50, 1200, 295, 1335)), ("FAMOUS FOOD", "B", (315, 1210, 520, 1335)),
                ("BRIDGES OF HUANGPU RIVER", "B", (545, 1210, 960, 1335))],
        map_y=(215, 1195), hero=("동방명주", (510, 215, 600, 740)), core=("푸둥 마천루 군", (430, 215, 1000, 800)),
        water="황푸강 S자(폭 약 70)가 지도 척추", labels=21),
    "203x-berlin": dict(
        img="203x-berlin/StH_202205_154_berlin_re.jpg", issue="2022-05",
        title=(285, 30, 720, 215),
        panels=[("CITY INFORMATION", "TL", (40, 40, 245, 150)), ("FAMOUS CULTURE AREA", "TL", (40, 180, 255, 345)),
                ("HISTORY", "TR", (745, 40, 960, 180)), ("FAMOUS FOOD", "BL", (40, 1215, 250, 1335)),
                ("AMPELMANN", "BL", (280, 1215, 440, 1325))],
        map_y=(115, 1345), hero=("베를린 TV탑", (570, 115, 690, 1170)), core=("TV탑+받침 판+베를린 돔", (345, 115, 895, 1345)),
        water="슈프레강 폭 약 50 굽은 띠", labels=15),
    "203x-taipei": dict(
        img="203x-taipei/StH_2023_12_Poster_re.jpg", issue="2023-12",
        title=(295, 55, 710, 215),
        panels=[("CITY INFORMATION", "L", (50, 55, 245, 165)), ("FAMOUS CULTURE AREA", "L", (50, 190, 245, 355)),
                ("CITY SYMBOL", "L", (50, 385, 245, 485)), ("NEARBY ATTRACTIONS", "L", (50, 505, 245, 605)),
                ("HISTORY", "TR", (750, 55, 960, 195)), ("FAMOUS FOOD", "BL", (50, 1200, 250, 1330)),
                ("TRAFFIC LIGHT", "BL", (310, 1200, 440, 1330))],
        map_y=(285, 1310), hero=("타이베이 101", (265, 310, 390, 1040)), core=("101+받침 판+LOVE", (180, 310, 500, 1110)),
        water="단수이강 오른쪽 아래 가장자리 띠(폭 약 120)", labels=18),
    "203x-jeju": dict(
        img="203x-jeju/jejudo-4.jpg", issue="2018-08",
        title=(240, 45, 760, 175),
        panels=[("FORMATION", "L", (50, 45, 210, 220)), ("HISTORY", "L", (50, 255, 245, 415)),
                ("PEOPLE", "L", (50, 435, 245, 570)), ("SUMMARY", "R", (775, 45, 960, 210)),
                ("BUS", "R", (775, 255, 960, 495)), ("ECOSYSTEM(한라산 단면)", "C", (270, 255, 720, 500)),
                ("BUS ROUTE(평면 지도)", "M", (40, 510, 950, 910)), ("ANNEXED ISLANDS", "BR", (720, 1225, 960, 1330))],
        map_y=(905, 1335), hero=("없음(한라산이 중심)", (420, 1000, 560, 1110)), core=("섬 전체(PLACES TO GO)", (0, 905, 1000, 1335)),
        water="바다가 바탕(섬 실루엣)", labels=40),
    "203x-forbiddencity": dict(
        img="203x-forbiddencity/forbidden_city_poster.jpg", issue="2020-10",
        title=(270, 30, 730, 215),
        panels=[("SUMMARY(타이틀 좌)", "T", (40, 115, 270, 210)), ("SUMMARY(타이틀 우)", "T", (735, 140, 960, 210)),
                ("HISTORY", "L", (40, 240, 500, 990)), ("ROOF BUILDING", "TR", (480, 240, 970, 480)),
                ("PLANE DRAWING", "BL", (40, 1010, 195, 1305))],
        map_y=(410, 1310), hero=("태화전 등 끌어낸 확대 모형", (195, 420, 640, 770)), core=("궁역 평행사변형(오른쪽 블리드)", (170, 410, 1000, 1310)),
        water="해자(외곽 하늘색 띠)", labels=40),
    "203x-cheongwadae": dict(
        img="203x-cheongwadae/StH_202206_155_cheongwadae.jpg", issue="2022-07",
        title=(230, 30, 780, 200),
        panels=[("DEFINITION", "TL", (40, 45, 245, 135)), ("SPACE LAYOUT", "TL", (40, 150, 230, 305)),
                ("LOGO HISTORY", "T", (250, 200, 720, 295)), ("MAIN REMAINS", "TR", (805, 45, 960, 320)),
                ("PRESIDENTS", "B", (40, 1195, 960, 1335))],
        map_y=(230, 1200), hero=("본관", (290, 400, 770, 730)), core=("본관+관저 축", (290, 400, 960, 800)),
        water="없음(북악산 능선이 배경 띠 y230~470)", labels=12),
    "203x-pyramid": dict(
        img="203x-pyramid/StH_2024_04_Poster_re.jpg", issue="2024-04",
        title=(205, 50, 780, 200),
        panels=[("WHAT IS PYRAMID", "TL", (50, 55, 245, 190)), ("PYRAMID DISTRIBUTION", "TR", (785, 55, 960, 190)),
                ("HISTORY", "T", (50, 200, 945, 305)), ("CHANGE OF THE FORM", "L", (50, 330, 520, 455)),
                ("GOLDEN AGE", "C", (555, 330, 730, 500)), ("GREAT PYRAMID OF GIZA", "R", (745, 330, 960, 470)),
                ("INTERIOR AND MATERIALS", "L", (50, 475, 330, 640)), ("NECROPOLIS", "R", (745, 480, 960, 700)),
                ("PAPYRUS JARF", "L", (50, 660, 250, 745)), ("CONSTRUCTION TOOLS", "L", (50, 975, 300, 1095)),
                ("COMPARE HEIGHTS", "B", (50, 1120, 345, 1310)), ("GIZA PYRAMID COMPLEX", "B", (385, 1120, 730, 1310)),
                ("GREAT SPHINX", "B", (755, 1120, 960, 1330))],
        map_y=(495, 1100), hero=("쿠푸왕 대피라미드(절개)", (90, 495, 950, 1100)), core=("피라미드+스핑크스", (90, 495, 950, 1100)),
        water="없음(지평선 y≈780)", labels=10),
}


def area(b):
    return max(0, b[2] - b[0]) * max(0, b[3] - b[1])


def metrics(d):
    t = d["title"]
    hx0, hy0, hx1, hy1 = d["hero"][1]
    return {
        "title_w_pct": round((t[2] - t[0]) / W * 100, 1),
        "title_h_pct": round((t[3] - t[1]) / H * 100, 1),
        "panel_count": len(d["panels"]),
        "panel_area_pct": round(sum(area(p[2]) for p in d["panels"]) / (W * H) * 100, 1),
        "panel_slots": {s: sum(1 for p in d["panels"] if p[1] == s) for s in sorted({p[1] for p in d["panels"]})},
        "map_y_pct": round((d["map_y"][1] - d["map_y"][0]) / H * 100, 1),
        "hero_h_pct": round((hy1 - hy0) / H * 100, 1),
        "hero_cx_pct": round((hx0 + hx1) / 2 / W * 100, 1),
        "hero_top_in_title": hy0 < t[3],
        "core_bbox_pct": round(area(d["core"][1]) / (W * H) * 100, 1),
    }


def draw(src, dst, d):
    im = Image.open(src).convert("RGB").resize((W, H), Image.LANCZOS)
    dr = ImageDraw.Draw(im, "RGBA")
    f = ImageFont.truetype(FONT, 22)
    y0, y1 = d["map_y"]
    dr.rectangle([0, y0, W - 1, y1], outline=(0, 255, 0, 255), width=3)
    dr.rectangle(d["title"], outline=(255, 220, 0, 255), width=5)
    for name, slot, b in d["panels"]:
        dr.rectangle(b, outline=(0, 230, 255, 255), width=4, fill=(0, 230, 255, 40))
    dr.rectangle(d["core"][1], outline=(255, 140, 0, 255), width=5)
    dr.rectangle(d["hero"][1], outline=(255, 0, 60, 255), width=6)
    im.save(dst, quality=85)


def contact(paths, dst, cols=5):
    tw, th = 300, 420
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (th + 30)), (30, 30, 30))
    f = ImageFont.truetype(FONT, 20)
    dr = ImageDraw.Draw(sheet)
    for i, (slug, p) in enumerate(paths):
        im = Image.open(p).resize((tw, th), Image.LANCZOS)
        x, y = (i % cols) * tw, (i // cols) * (th + 30)
        sheet.paste(im, (x, y))
        dr.text((x + 6, y + th + 4), slug, fill=(255, 255, 255), font=f)
    sheet.save(dst, quality=85)


def main():
    root, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    result, made = {}, []
    for slug, d in DATA.items():
        m = metrics(d)
        result[slug] = {**{k: v for k, v in d.items()}, "metrics": m}
        dst = out / f"{slug}_measure.jpg"
        draw(root / d["img"], dst, d)
        made.append((slug, dst))
    (out / "refs_cities_measure.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    contact(made, out / "measure_contact.jpg")
    print("| ref | 호 | 타이틀 폭% | 패널 수 | 패널 자리 | 패널 면적% | 지도 세로% | 히어로 | 히어로 높이% | 히어로 중심 x% | 타이틀 침범 | 코어 bbox% |")
    for slug, r in result.items():
        m = r["metrics"]
        slots = " ".join(f"{k}{v}" for k, v in m["panel_slots"].items())
        print(f"| {slug} | {r['issue']} | {m['title_w_pct']} | {m['panel_count']} | {slots} | {m['panel_area_pct']} | {m['map_y_pct']} | {r['hero'][0]} | {m['hero_h_pct']} | {m['hero_cx_pct']} | {'예' if m['hero_top_in_title'] else '아니오'} | {m['core_bbox_pct']} |")


if __name__ == "__main__":
    main()
