"""전체 이미지 좌표로 영역을 잘라 확대하고 격자·좌표 숫자를 덧씌운다 (2026-10-18, refs-analysis 3묶음).

- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- 고해상 타일이 있으면 타일에서 잘라 쓴다(타일 좌표 = (전체 좌표 - 오프셋) x 2).
- 사용: uv run --no-project --with pillow python -I cpg_zoom.py <이미지> <x0> <y0> <x1> <y1> <출력> <격자간격> [<타일> <ox> <oy>]
  좌표·격자는 모두 전체 이미지 픽셀 단위다.
"""
import sys

from PIL import Image, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"


def main() -> None:
    src, x0, y0, x1, y1, out, step = sys.argv[1], *map(float, sys.argv[2:6]), sys.argv[6], float(sys.argv[7])
    if len(sys.argv) > 8:
        tile, ox, oy = sys.argv[8], float(sys.argv[9]), float(sys.argv[10])
        im = Image.open(tile).convert("RGB")
        k = 2.0
        box = (int((x0 - ox) * k), int((y0 - oy) * k), int((x1 - ox) * k), int((y1 - oy) * k))
    else:
        im = Image.open(src).convert("RGB")
        k = 1.0
        ox = oy = 0.0
        box = (int(x0), int(y0), int(x1), int(y1))
    crop = im.crop(box)
    target_w = 1400
    z = target_w / crop.width
    crop = crop.resize((int(crop.width * z), int(crop.height * z)), Image.LANCZOS)
    dr = ImageDraw.Draw(crop, "RGBA")
    font = ImageFont.truetype(FONT, 16)
    scale = z * k  # 전체 좌표 1px -> 출력 px

    def gx(x):
        return (x - x0) * scale

    def gy(y):
        return (y - y0) * scale

    import math
    xs = math.ceil(x0 / step) * step
    while xs <= x1:
        major = abs((xs / (step * 2)) - round(xs / (step * 2))) < 1e-6
        dr.line([(gx(xs), 0), (gx(xs), crop.height)], fill=(255, 0, 255, 140 if major else 70), width=2 if major else 1)
        dr.rectangle([gx(xs) + 2, 2, gx(xs) + 46, 20], fill=(255, 255, 255, 210))
        dr.text((gx(xs) + 3, 2), f"{xs:g}", fill=(190, 0, 190, 255), font=font)
        xs += step
    ys = math.ceil(y0 / step) * step
    while ys <= y1:
        major = abs((ys / (step * 2)) - round(ys / (step * 2))) < 1e-6
        dr.line([(0, gy(ys)), (crop.width, gy(ys))], fill=(0, 170, 255, 140 if major else 70), width=2 if major else 1)
        dr.rectangle([2, gy(ys) + 2, 50, gy(ys) + 20], fill=(255, 255, 255, 210))
        dr.text((3, gy(ys) + 2), f"{ys:g}", fill=(0, 110, 200, 255), font=font)
        ys += step
    crop.save(out, quality=90)
    print("ok", out, crop.size, "scale", round(scale, 3))


if __name__ == "__main__":
    main()
