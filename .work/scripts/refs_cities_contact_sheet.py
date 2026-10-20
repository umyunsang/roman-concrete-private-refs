"""도시 인포그래픽 레퍼런스 후보 모음 이미지(PNG) 생성 (2026-10-18).

- 입력 이미지는 신뢰하지 않는 데이터다. 읽어서 축소만 한다.
- 사용: uv run --no-project --with pillow python -I refs_cities_contact_sheet.py <dl루트> <출력 PNG>
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"

# (번호, 도시·주제, 작가, 연도, 이미지 상대경로, 추천 순위 또는 None)
ITEMS = [
    ("B0", "베이징(기존 벤치마크)", "203X", "2024.03", "203x-beijing/StH_2024_03_Poster.jpg", None),
    ("C01", "홍콩", "203X", "2022.04", "203x-hongkong/StH_2022_04_Tokyo.jpg", 3),
    ("C02", "서울", "203X", "2018.09", "203x-seoul/seoul-4-1.jpg", None),
    ("C03", "뉴욕", "203X", "2018.03", "203x-newyork/New-York1.jpg", None),
    ("C04", "뉴욕2 센트럴파크", "203X", "2022.09", "203x-newyork2-centralpark/StH_202209_158_new-york2.jpg", 5),
    ("C05", "도쿄", "203X", "2021.05", "203x-tokyo/StH_2021_05_Poster_Tokyo-1.jpg", 4),
    ("C06", "파리", "203X", "2021.04", "203x-paris/StH_2021_04_Poster_Paris2.jpg", 1),
    ("C07", "런던", "203X", "2017.12", "203x-london/london1.jpg", None),
    ("C08", "상하이", "203X", "2020.12", "203x-shanghai/shanghai_poster.jpg", 2),
    ("C09", "베를린", "203X", "2022.05", "203x-berlin/StH_202205_154_berlin_re.jpg", None),
    ("C10", "타이베이", "203X", "2023.12", "203x-taipei/StH_2023_12_Poster_re.jpg", None),
    ("C11", "제주도", "203X", "2018.08", "203x-jeju/jejudo-4.jpg", None),
    ("C12", "자금성", "203X", "2020.10", "203x-forbiddencity/forbidden_city_poster.jpg", None),
    ("C13", "청와대", "203X", "2022.07", "203x-cheongwadae/StH_202206_155_cheongwadae.jpg", None),
    ("C14", "피라미드(기자)", "203X", "2024.04", "203x-pyramid/StH_2024_04_Poster_re.jpg", None),
    ("C15", "로마 포로 로마노", "Gus Morais", "연도 미확인", "gusmorais-rome-seekfind/original-fb56ea9a97b964f37f236c360b5151cc.jpg", None),
    ("C16", "로마 파노라마 지도", "A. Trabacchi", "1960", "trabacchi-rome-1960/trabacchi_2.jpg", None),
    ("C17", "고대 로마 모형", "I. Gismondi", "1933~37 제작", "gismondi-plastico-rome/Vue_maquette_de_Gismondi_JP_Dalbera.jpg", None),
]

COLS = 6
TW, TH = 320, 448          # 썸네일 칸
CAP = 78                   # 캡션 높이
GAP = 18
MARGIN = 36
HEADER = 120
BG = (246, 243, 236)
INK = (34, 34, 34)
SUB = (110, 104, 96)
ACCENT = (200, 60, 40)


def fit(im, w, h):
    im = im.convert("RGB")
    r = min(w / im.width, h / im.height)
    nw, nh = max(1, int(im.width * r)), max(1, int(im.height * r))
    return im.resize((nw, nh), Image.LANCZOS)


def main():
    root, out = Path(sys.argv[1]), Path(sys.argv[2])
    rows = (len(ITEMS) + COLS - 1) // COLS
    W = MARGIN * 2 + COLS * TW + (COLS - 1) * GAP
    H = HEADER + MARGIN + rows * (TH + CAP) + (rows - 1) * GAP + 70
    sheet = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(sheet)
    f_title = ImageFont.truetype(FONT, 40, index=6)  # index 6 = Bold
    f_sub = ImageFont.truetype(FONT, 21)
    f_cap = ImageFont.truetype(FONT, 22, index=6)
    f_cap2 = ImageFont.truetype(FONT, 18)
    f_badge = ImageFont.truetype(FONT, 20, index=6)
    dr.text((MARGIN, 30), "도시 인포그래픽 레퍼런스 후보 모음", fill=INK, font=f_title)
    dr.text((MARGIN, 82), "2026-10-18 · B0 기존 벤치마크 · C01~C14 203X Street H 시리즈 · C15~C17 로마 지리·디테일 보조 자료 · 빨간 테두리 = 바로 벤치마킹할 상위 5개(숫자는 순위) · 내부 참고용",
            fill=SUB, font=f_sub)
    for i, (no, city, author, year, rel, rank) in enumerate(ITEMS):
        c, r = i % COLS, i // COLS
        x = MARGIN + c * (TW + GAP)
        y = HEADER + MARGIN + r * (TH + CAP + GAP)
        dr.rectangle([x, y, x + TW, y + TH], fill=(225, 221, 212))
        im = fit(Image.open(root / rel), TW, TH)
        sheet.paste(im, (x + (TW - im.width) // 2, y + (TH - im.height) // 2))
        if rank:  # 썸네일을 가리지 않도록 테두리와 캡션 오른쪽 표시만 쓴다
            dr.rectangle([x - 5, y - 5, x + TW + 5, y + TH + 5], outline=ACCENT, width=5)
            label = f"추천 {rank}위"
            lw = dr.textlength(label, font=f_badge)
            dr.rectangle([x + TW - lw - 16, y + TH + 10, x + TW, y + TH + 38], fill=ACCENT)
            dr.text((x + TW - lw - 8, y + TH + 11), label, fill=(255, 255, 255), font=f_badge)
        dr.text((x, y + TH + 8), f"{no}  {city}", fill=INK, font=f_cap)
        dr.text((x, y + TH + 42), f"{author} · {year}", fill=SUB, font=f_cap2)
    dr.text((MARGIN, H - 46), "출처: 203x.co.kr · street-h.com(203X/Street H), dribbble.com/gusmorais, uniquemaps.co.uk(Trabacchi 1960), Wikimedia Commons(Gismondi 모형 사진, CC BY 2.0 J.-P. Dalbera). 저작권은 각 권리자에게 있음.",
            fill=SUB, font=f_cap2)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, "PNG", optimize=True)
    print("saved", out, sheet.size)


if __name__ == "__main__":
    main()
