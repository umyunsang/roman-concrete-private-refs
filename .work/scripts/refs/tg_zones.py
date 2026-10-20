"""Trabacchi 1960 지도·Gismondi 모형 사진의 실측 구획 상자를 그려 확인용 이미지를 만든다 (2026-10-18).

- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- 상자 좌표는 tg_* 실측 스크립트 결과와 확대 판독(tg_crop_grid.py)에서 옮겼다. 각 사진 폭·높이 기준 0~1 정규 좌표.
- 출력
  - <out>/trabacchi-rome-1960_zones.png
  - <out>/gismondi-plastico-rome_zones.png (사진 3장 D·R·E를 한 장에)
  - <out>/work_tg/zones_tg.json (같은 상자 목록)
- 사용: python -I tg_zones.py <refs-cities 폴더> <출력 폴더>
"""
import json
import sys

from PIL import Image, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
COL = {"title": (220, 20, 60), "panel": (0, 90, 255), "map": (40, 40, 40), "core_group": (255, 0, 0), "hero": (255, 140, 0),
       "landmark": (128, 0, 160), "river": (0, 150, 220), "sea": (0, 70, 160), "road": (150, 75, 0), "legend": (0, 140, 70),
       "footer": (90, 90, 90), "other": (60, 120, 60)}

TRABACCHI = [
    ("타이틀 PIANTA PANORAMICA DI ROMA", "title", [0.346, 0.034, 0.660, 0.051]),
    ("부제 CON CIRCA 500 MONUMENTI", "title", [0.738, 0.046, 0.969, 0.055]),
    ("다국어 안내문(뒷면 색인)", "legend", [0.030, 0.040, 0.310, 0.055]),
    ("지도 무대(안쪽 테두리)", "map", [0.036, 0.062, 0.964, 0.945]),
    ("바다 지평선 띠", "sea", [0.240, 0.064, 0.964, 0.082]),
    ("알바니 구릉(화산 지대)·호수·참피노", "landmark", [0.036, 0.062, 0.220, 0.155]),
    ("인셋: 리도 디 로마(오스티아)", "panel", [0.4247, 0.064, 0.570, 0.159]),
    ("인셋: E.U.R.", "panel", [0.036, 0.828, 0.168, 0.944]),
    ("테베레강 S자(주성분)", "river", [0.585, 0.091, 0.835, 0.921]),
    ("테베레 하구(바다와 만남)", "river", [0.800, 0.065, 0.840, 0.115]),
    ("포르투스 자리(트라야누스 호수)·피우미치노", "landmark", [0.845, 0.068, 0.880, 0.097]),
    ("테베레 북쪽 끝(밀비오 다리 쪽, 아래 변 블리드)", "river", [0.496, 0.913, 0.665, 0.943]),
    ("고대 도심 축(코어 군)", "core_group", [0.355, 0.245, 0.565, 0.400]),
    ("콜로세움", "hero", [0.365, 0.315, 0.405, 0.345]),
    ("대전차경기장", "landmark", [0.480, 0.262, 0.561, 0.310]),
    ("카라칼라 욕장(폐허)", "landmark", [0.400, 0.195, 0.480, 0.228]),
    ("아피아 가도·메텔라 무덤·산 세바스티아노", "landmark", [0.230, 0.080, 0.310, 0.110]),
    ("판테온", "landmark", [0.575, 0.445, 0.600, 0.495]),
    ("카스텔 산탄젤로", "landmark", [0.776, 0.472, 0.802, 0.510]),
    ("산 피에트로(바티칸)", "landmark", [0.860, 0.365, 0.950, 0.440]),
    ("테르미니역", "landmark", [0.130, 0.335, 0.245, 0.470]),
    ("포폴로 광장", "landmark", [0.565, 0.690, 0.620, 0.750]),
    ("펜 밀도 상위 10%(20~80분위 상자)", "other", [0.225, 0.326, 0.602, 0.529]),
]

GISMONDI = {
    "D": ("Vue_maquette_de_Gismondi_JP_Dalbera.jpg", "D: Dalbera 2011, 남쪽에서 북쪽", [
        ("모형 면(보이는 범위)", "map", [0.0, 0.015, 1.0, 1.0]),
        ("전시실(모형 밖)", "other", [0.0, 0.0, 1.0, 0.10]),
        ("테베레 먼 굽이", "river", [0.0, 0.090, 0.190, 0.150]),
        ("테베레 앞 굽이·티베리나섬", "river", [0.0, 0.405, 0.135, 0.720]),
        ("코어 군(콜로세움 골짜기)", "core_group", [0.450, 0.390, 0.673, 0.660]),
        ("콜로세움", "hero", [0.534, 0.4005, 0.611, 0.500]),
        ("클라우디우스 신전 경내", "landmark", [0.555, 0.505, 0.673, 0.631]),
        ("팔라티노 궁전군", "landmark", [0.280, 0.470, 0.470, 0.730]),
        ("대전차경기장", "landmark", [0.165, 0.595, 0.425, 0.870]),
        ("네로 수도교(벽돌색 선)", "road", [0.426, 0.526, 1.0, 0.756]),
        ("나무 숲 덩어리", "other", [0.580, 0.760, 0.800, 0.970]),
    ]),
    "R": ("Model_of_imperial_Rome_Velian_Colosseum_Raddato.jpg", "R: Raddato 2014, 동남동에서 서북서", [
        ("테베레·티베리나섬", "river", [0.400, 0.0, 0.980, 0.130]),
        ("대전차경기장", "landmark", [0.050, 0.190, 0.470, 0.400]),
        ("코어 군(콜로세움 골짜기)", "core_group", [0.0, 0.400, 0.740, 0.930]),
        ("네로 수도교(벽돌색 선)", "road", [0.0, 0.405, 0.436, 0.722]),
        ("클라우디우스 신전 경내", "landmark", [0.125, 0.600, 0.360, 0.800]),
        ("콜로세움", "hero", [0.4574, 0.6011, 0.6374, 0.8186]),
        ("루두스 마그누스(검투사 훈련장)", "landmark", [0.420, 0.840, 0.520, 0.915]),
        ("거상(콜로수스) 받침", "other", [0.655, 0.600, 0.680, 0.660]),
    ]),
    "E": ("RomemodelEUR3.jpg", "E: Notafly 2008, 남쪽에서 북쪽", [
        ("테베레·티베리나섬", "river", [0.0, 0.170, 0.270, 0.550]),
        ("코어 군(콜로세움 골짜기)", "core_group", [0.600, 0.170, 0.820, 0.400]),
        ("콜로세움", "hero", [0.6506, 0.2094, 0.7297, 0.2804]),
        ("팔라티노 궁전군", "landmark", [0.430, 0.240, 0.580, 0.400]),
        ("대전차경기장", "landmark", [0.320, 0.340, 0.580, 0.520]),
        ("네로 수도교(벽돌색 선)", "road", [0.559, 0.299, 0.995, 0.463]),
        ("카라칼라 욕장", "landmark", [0.730, 0.600, 1.0, 1.0]),
    ]),
}


def draw_boxes(im, zones, scale_font=1.0, lw=3):
    d = ImageDraw.Draw(im, "RGBA")
    W, H = im.size
    fs = max(14, int(W / 70 * scale_font))
    font = ImageFont.truetype(FONT, fs)
    placed = []
    for name, kind, b in zones:
        c = COL[kind]
        x0, y0, x1, y1 = b[0] * W, b[1] * H, b[2] * W, b[3] * H
        if kind == "core_group":
            d.rectangle([x0, y0, x1, y1], fill=c + (40,))
        d.rectangle([x0, y0, x1, y1], outline=c + (255,), width=lw + (2 if kind in ("core_group", "map") else 0))
        tw = d.textlength(name, font=font)
        tx, ty = x0 + 3, y0 + 2
        if kind == "map":
            tx, ty = x1 - tw - 6, y1 - fs - 8
        if ty + fs > H:
            ty = y0 - fs - 4
        if tx + tw > W:
            tx = W - tw - 4
        # 겹침 회피: 이미 놓인 글 상자와 겹치면 아래로 내린다
        for _ in range(8):
            if any(not (tx + tw < a or tx > c2 or ty + fs < bb or ty > dd) for a, bb, c2, dd in placed):
                ty += fs + 4
            else:
                break
        d.rectangle([tx - 2, ty - 1, tx + tw + 2, ty + fs + 3], fill=(255, 255, 255, 215))
        d.text((tx, ty), name, fill=c + (255,), font=font)
        placed.append((tx - 2, ty - 1, tx + tw + 2, ty + fs + 3))
    return im


def main():
    src, out = sys.argv[1], sys.argv[2]
    # Trabacchi
    im = Image.open(f"{src}/trabacchi-rome-1960/trabacchi_2.jpg").convert("RGB").resize((3000, 2000), Image.LANCZOS)
    draw_boxes(im, TRABACCHI, 0.75, 3)
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype(FONT, 30)
    d.rectangle([0, 1915, 3000, 2000], fill=(255, 255, 255))
    d.text((20, 1925), "Trabacchi 1960 「Pianta Panoramica di Roma」 실측 구획 (trabacchi_2.jpg 1500×1000 기준 정규 좌표, 2배 확대 표시)",
           fill=(0, 0, 0), font=font)
    d.text((20, 1962), "빨강 채움 = 코어 군, 주황 = 히어로, 보라 = 랜드마크, 파랑 = 강·바다, 청색 = 인셋 패널, 회색 = 펜 밀도 상위 구역",
           fill=(60, 60, 60), font=font)
    im.save(f"{out}/trabacchi-rome-1960_zones.png")
    # Gismondi: 3장을 세로로 쌓는다(폭 2000)
    tiles = []
    for key, (fn, cap, zones) in GISMONDI.items():
        p = Image.open(f"{src}/gismondi-plastico-rome/{fn}").convert("RGB")
        w = 2000
        p = p.resize((w, int(p.size[1] * w / p.size[0])), Image.LANCZOS)
        draw_boxes(p, zones, 1.0, 4)
        cap_h = 56
        t = Image.new("RGB", (w, p.size[1] + cap_h), (255, 255, 255))
        t.paste(p, (0, cap_h))
        ImageDraw.Draw(t).text((16, 10), cap + f"  ({fn})", fill=(0, 0, 0), font=ImageFont.truetype(FONT, 34))
        tiles.append(t)
    Ht = sum(t.size[1] for t in tiles) + 20 * (len(tiles) - 1) + 70
    comp = Image.new("RGB", (2000, Ht), (245, 245, 245))
    y = 0
    for t in tiles:
        comp.paste(t, (0, y))
        y += t.size[1] + 20
    ImageDraw.Draw(comp).text((16, Ht - 56), "Gismondi 1:250 로마 모형 사진 3장 실측 구획 (상자는 각 사진 폭·높이 기준 정규 좌표). 빨강 채움 = 코어 군(콜로세움 골짜기)",
                              fill=(0, 0, 0), font=ImageFont.truetype(FONT, 30))
    comp.save(f"{out}/gismondi-plastico-rome_zones.png")
    with open(f"{out}/work_tg/zones_tg.json", "w") as f:
        json.dump({"trabacchi-rome-1960": TRABACCHI, "gismondi-plastico-rome": {k: v[2] for k, v in GISMONDI.items()}}, f,
                  ensure_ascii=False, indent=1)
    print("ok")


if __name__ == "__main__":
    main()
