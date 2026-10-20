"""정규 좌표(0~1) 격자를 얹어 이미지 일부를 확대 저장한다 (2026-10-18, Trabacchi·Gismondi 실측용).

- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- 사용: python -I tg_crop_grid.py <이미지> <출력.png> <x0> <y0> <x1> <y1> [긴 변 px=1400] [격자 간격=0.01]
  x0~y1은 원본 폭·높이 기준 0~1 정규 좌표다. 굵은 선(자홍)은 격자 간격 5칸마다 그리고 값을 적는다.
"""
import sys

from PIL import Image, ImageDraw, ImageFont


def main():
    src, out = sys.argv[1], sys.argv[2]
    x0, y0, x1, y1 = (float(v) for v in sys.argv[3:7])
    long_side = int(sys.argv[7]) if len(sys.argv) > 7 else 1400
    step = float(sys.argv[8]) if len(sys.argv) > 8 else 0.01
    im = Image.open(src).convert("RGB")
    W, H = im.size
    box = (int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H))
    crop = im.crop(box)
    cw, ch = crop.size
    s = long_side / max(cw, ch)
    crop = crop.resize((max(1, int(cw * s)), max(1, int(ch * s))), Image.LANCZOS)
    d = ImageDraw.Draw(crop)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
    n = round(1 / step)
    for k in range(n + 1):
        v = k * step
        major = k % 5 == 0
        col = (255, 0, 255) if major else (0, 190, 255)
        if x0 - 1e-9 <= v <= x1 + 1e-9:
            px = (v * W - box[0]) * s
            d.line([(px, 0), (px, crop.size[1])], fill=col, width=1)
            if major:
                d.text((px + 2, 2), f"{v:.3f}".rstrip("0").rstrip("."), fill=col, font=font)
        if y0 - 1e-9 <= v <= y1 + 1e-9:
            py = (v * H - box[1]) * s
            d.line([(0, py), (crop.size[0], py)], fill=col, width=1)
            if major:
                d.text((2, py + 2), f"{v:.3f}".rstrip("0").rstrip("."), fill=col, font=font)
    crop.save(out)
    print(out, crop.size, "원본 px 상자", box)


if __name__ == "__main__":
    main()
