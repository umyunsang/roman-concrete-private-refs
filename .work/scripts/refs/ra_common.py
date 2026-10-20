"""레퍼런스 정밀분석 공용 설정(서울·런던·베를린).
아트 좌표계: 원본 2000x2800 px(타일 2x3 분할 기준). 정규 좌표 = 아트 / (2000, 2800).
"""
from pathlib import Path

ROOT = Path("/Users/um-yunsang/roman-concrete-private-refs")
DL = ROOT / ".work/dl/refs-cities"
OUT = ROOT / ".work/out/refs-analysis"
WORK = OUT / "work"
ART_W, ART_H = 2000, 2800

REFS = {
    "203x-seoul": {
        "full": DL / "203x-seoul/seoul-4-1.jpg",
        "tiles": {1: DL / "203x-seoul/1000_41_seoul_1.jpg",
                  4: DL / "203x-seoul/1000_41_seoul_4.jpg",
                  5: DL / "203x-seoul/1000_41_seoul_5.jpg"},
    },
    "203x-london": {
        "full": DL / "203x-london/london1.jpg",
        "tiles": {1: DL / "203x-london/1000_32_london_1.jpg",
                  4: DL / "203x-london/1000_32_london_4.jpg",
                  5: DL / "203x-london/1000_32_london_5.jpg"},
    },
    "203x-berlin": {
        "full": DL / "203x-berlin/StH_202205_154_berlin_re.jpg",
        "tiles": {1: DL / "203x-berlin/1000_StH_202205_154_poster_re_01.jpg",
                  4: DL / "203x-berlin/1000_StH_202205_154_poster_re_04.jpg",
                  5: DL / "203x-berlin/1000_StH_202205_154_poster_re_05.jpg"},
    },
}

# 2x3 타일 번호 -> 기대 오프셋(아트 px). 높이 933+934+933 = 2800
TILE_EXPECT = {1: (0, 0), 2: (1000, 0), 3: (0, 933), 4: (1000, 933), 5: (0, 1867), 6: (1000, 1867)}

def composite_path(ref):
    return WORK / f"{ref}_art2000.png"

def mask_path(ref):
    return WORK / f"{ref}_hires_mask.png"
