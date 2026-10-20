"""도시 인포그래픽 후보 포스터에 측정용 격자를 덧씌운다 (2026-10-18).

- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 하고, 결과는 별도 폴더에 쓴다.
- 모든 포스터를 1000x1400 정규 좌표로 맞춘 뒤 50 단위 가는 선, 100 단위 굵은 선과 좌표 숫자를 그린다.
- 사용: uv run --no-project --with pillow python -I refs_cities_grid.py <출력폴더> <slug>=<이미지경로> ...
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1000, 1400
FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"


def overlay(src: Path, dst: Path) -> None:
    im = Image.open(src).convert("RGB").resize((W, H), Image.LANCZOS)
    dr = ImageDraw.Draw(im, "RGBA")
    font = ImageFont.truetype(FONT, 18)
    for x in range(0, W + 1, 50):
        major = x % 100 == 0
        dr.line([(x, 0), (x, H)], fill=(255, 0, 255, 150 if major else 70), width=2 if major else 1)
    for y in range(0, H + 1, 50):
        major = y % 100 == 0
        dr.line([(0, y), (W, y)], fill=(0, 200, 255, 150 if major else 70), width=2 if major else 1)
    for x in range(100, W, 100):
        for y in (4, H // 2, H - 24):
            dr.rectangle([x + 2, y, x + 44, y + 20], fill=(255, 255, 255, 200))
            dr.text((x + 4, y), str(x), fill=(200, 0, 200, 255), font=font)
    for y in range(100, H, 100):
        for x in (2, W // 2 + 2, W - 50):
            dr.rectangle([x, y + 2, x + 46, y + 22], fill=(255, 255, 255, 200))
            dr.text((x + 2, y + 2), str(y), fill=(0, 120, 200, 255), font=font)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, quality=85)


def main() -> None:
    out = Path(sys.argv[1])
    for arg in sys.argv[2:]:
        slug, path = arg.split("=", 1)
        overlay(Path(path), out / f"{slug}.jpg")
        print("ok", slug)


if __name__ == "__main__":
    main()
