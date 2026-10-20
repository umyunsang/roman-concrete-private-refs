# city 시험 렌더를 LocalBanana·203X 레퍼런스와 나란히 놓는 비교 그림(작업용)
import sys
from PIL import Image, ImageDraw

W = '/Users/um-yunsang/roman-concrete-private-refs/.work/blender/rounds/work/'
REF_LB = '/Users/um-yunsang/roman-concrete-private-refs/docs/references/assets/아레나-참조-localbanana.jpg'
REF_203X = '/Users/um-yunsang/roman-concrete-private-refs/.work/dl/refs-cities/203x-paris/StH_2021_04_Paris_04.jpg'
CROP = (0.0, 88.0, 240.0, 345.0)   # roma_render.CROPS['city']
PPM = 8.0
# 건물별 확대 상자(포스터 화면 mm)
ZOOM = {
    'pantheon': (14.0, 192.0, 118.0, 292.0),
    'market': (14.0, 94.0, 118.0, 186.0),
    'maxentius': (126.0, 142.0, 228.0, 232.0),
    'marcellus': (18.0, 284.0, 92.0, 334.0),
}


def main(src, tag, ppm=None):
    global PPM
    if ppm:
        PPM = float(ppm)
    im = Image.open(src).convert('RGB')
    paper = Image.new('RGB', im.size, (227, 207, 168))
    full = Image.open(src).convert('RGBA')
    paper.paste(full, (0, 0), full)
    im = paper
    for k, (x0, y0, x1, y1) in ZOOM.items():
        bx = (int((x0 - CROP[0]) * PPM), int((y0 - CROP[1]) * PPM), int((x1 - CROP[0]) * PPM), int((y1 - CROP[1]) * PPM))
        im.crop(bx).save(W + 'city_%s_%s.png' % (tag, k))
    H = 1100
    a = im.resize((int(im.width * H / im.height), H), Image.LANCZOS)
    lb = Image.open(REF_LB).convert('RGB'); lb = lb.resize((int(lb.width * (H // 2) / lb.height), H // 2), Image.LANCZOS)
    px = Image.open(REF_203X).convert('RGB'); px = px.resize((int(px.width * (H // 2) / px.height), H // 2), Image.LANCZOS)
    wr = max(lb.width, px.width)
    out = Image.new('RGB', (a.width + wr + 30, H + 40), (250, 247, 240))
    out.paste(a, (10, 30)); out.paste(lb, (a.width + 20, 30)); out.paste(px, (a.width + 20, 30 + H // 2))
    d = ImageDraw.Draw(out)
    d.text((12, 8), 'city (%s)' % tag, fill=(60, 40, 30))
    d.text((a.width + 22, 8), 'LocalBanana (detail level) / 203X Paris (vector style)', fill=(60, 40, 30))
    out.save(W + 'city_compare_%s.png' % tag)
    print(W + 'city_compare_%s.png' % tag)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'r1', sys.argv[3] if len(sys.argv) > 3 else None)
