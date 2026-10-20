# -*- coding: utf-8 -*-
"""최종본 합성: 종이색 + Blender 지도 렌더(투명 바탕, 설계 다이어그램과 같은 가장자리 그라데이션) + 정보 층 → poster.png
사용: python3 -I compose.py <회차 폴더(rounds/bN)> [정보 층 PNG] [spec.json]
- 정보 층 기본 경로(b5, bglobal): .work/design/current/out/info/info_layer.png (current 설계판 render.py를 INFO_ONLY=1로 돌린 결과)
- 크기 검사: 지도(map.png)와 정보 층은 포스터 1 mm = 3 px, 1260×1782여야 한다. 다르면 멈춘다(exit 2).
  꼭 늘려 맞춰야 하면 환경 변수 COMPOSE_ALLOW_RESIZE=1을 준다(경고를 찍고 LANCZOS로 맞춘다).
- 겹치는 순서: 종이 PAPER (231, 208, 160) = 설계 BG → 지도 → 정보 층
가장자리 처리는 승인 설계 다이어그램(d4·v2)을 실측해 맞춘다(사용자 13:40).
- 위쪽(무대 윗선 y0): y0−4 ~ y0 mm에서 부드럽게 나타난다. 땅색이 종이색과 비슷해 경계가 거의 보이지 않는다.
- 무대 안: 그대로.
- 아래쪽(무대 아랫선 y1): 아래 띠 밑으로 바다만 이어지고(땅·집·밭은 y1에서 멈춘다. ground 패키지 몫),
  y1 ~ y1+62 mm 동안 (1−t)^1.2 곡선으로 종이색에 녹아든다(d4 실측: y1+15 ≈ 0.5, y1+45 ≈ 0.2, y1+60 ≈ 0).
- 좌우는 블리드.
spec을 주지 않으면 .work/design/current/out/spec.json의 frame.stage.rect를 쓴다."""
import json
Image_MAX = None
import os
import sys

try:
    from PIL import Image, ImageChops
    Image.MAX_IMAGE_PIXELS = None
except ModuleNotFoundError:          # python3 -I(격리)에서는 사용자 site-packages가 빠진다 → 그 경로만 명시해 더한다
    import site
    sys.path.append(site.getusersitepackages())
    from PIL import Image, ImageChops

ROOT = "/Users/um-yunsang/roman-concrete-private-refs"
PAPER = (231, 208, 160)          # .work/lib/common.py BG(인쇄 바탕) = 설계 BG
PAGE_MM = (420.0, 594.0)
PX_PER_MM = 16
EXPECT = (int(PAGE_MM[0] * PX_PER_MM), int(PAGE_MM[1] * PX_PER_MM))     # (1260, 1782)
TOP_FADE_MM = 4.0
BOTTOM_FADE_MM = 62.0
BOTTOM_GAMMA = 1.2
INFO_DEFAULT = ROOT + "/.work/design/current/out/info/info_layer.png"
SPEC_DEFAULT = ROOT + "/.work/design/current/out/spec.json"
ALLOW_RESIZE = os.environ.get("COMPOSE_ALLOW_RESIZE", "") == "1"


def fail(msg):
    print("합성 중단:", msg)
    sys.exit(2)


def check_size(img, name):
    if img.size == EXPECT:
        return img
    if not ALLOW_RESIZE:
        fail("%s 크기 %s ≠ %s(1 mm = %d px). 렌더 해상도를 맞추거나 COMPOSE_ALLOW_RESIZE=1로 다시 실행한다" % (name, img.size, EXPECT, PX_PER_MM))
    print("경고: %s 크기 %s → %s로 늘려 맞춘다(COMPOSE_ALLOW_RESIZE=1)" % (name, img.size, EXPECT))
    return img.resize(EXPECT, Image.LANCZOS)


if len(sys.argv) < 2:
    fail("회차 폴더를 준다: python3 -I compose.py <rounds/bN> [정보 층 PNG] [spec.json]")
d = sys.argv[1]
info = sys.argv[2] if len(sys.argv) > 2 else INFO_DEFAULT
spec_path = sys.argv[3] if len(sys.argv) > 3 else SPEC_DEFAULT
map_path = os.path.join(d, "hires", "map_16.png")
if not os.path.exists(map_path):
    fail("지도 렌더가 없다: " + map_path)
if not os.path.exists(info):
    fail("정보 층이 없다: " + info + " (current 설계판 render.py를 INFO_ONLY=1로 먼저 돌린다)")
m = check_size(Image.open(map_path).convert("RGBA"), "지도 map.png")
W, H = m.size
ky = H / PAGE_MM[1]
y0, y1 = 92.0, 505.0
try:
    r = json.load(open(spec_path, encoding="utf-8"))["frame"]["stage"]["rect"]
    y0, y1 = float(r[1]), float(r[3])
except Exception as e:
    print("spec 무대 읽기 실패, 기본 무대 사용:", e)


def row_alpha(ymm):
    if ymm < y0 - TOP_FADE_MM:
        return 0.0
    if ymm < y0:
        t = (ymm - (y0 - TOP_FADE_MM)) / TOP_FADE_MM
        return t * t * (3 - 2 * t)
    if ymm <= y1:
        return 1.0
    t = (ymm - y1) / BOTTOM_FADE_MM
    return max(0.0, 1.0 - t) ** BOTTOM_GAMMA if t < 1 else 0.0


col = Image.new("L", (1, H))
col.putdata([int(round(255 * row_alpha((py + 0.5) / ky))) for py in range(H)])
fade = col.resize((W, H))
m.putalpha(ImageChops.multiply(m.getchannel("A"), fade))
inf = check_size(Image.open(info).convert("RGBA"), "정보 층 " + os.path.basename(info))
out = Image.new("RGBA", m.size, PAPER + (255,))
out.alpha_composite(m)
out.alpha_composite(inf)
out.convert("RGB").save(os.path.join(d, "hires", "poster_16pxmm.png"), optimize=True, dpi=(406.4, 406.4))
print(os.path.join(d, "hires", "poster_16pxmm.png"), out.size, "정보 층", info, "· 무대 y", y0, "~", y1, "· 위", TOP_FADE_MM, "mm · 아래", BOTTOM_FADE_MM, "mm 그라데이션")
