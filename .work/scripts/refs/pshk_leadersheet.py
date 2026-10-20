"""라벨 둘레를 넓게(위 40·옆 70·아래 150px) 잘라 상자를 표시한 판독 모음. 지시선 형식 판독용. 입력은 읽기만 한다. (2026-10-18)"""
import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pshk_common import FONT, WORK, poster
from pshk_labels import LABELS
rid = sys.argv[1]
img = poster(rid)
big = cv2.resize(img, (2000, 2800), interpolation=cv2.INTER_CUBIC)
f = ImageFont.truetype(FONT, 22)
tiles = []
for i, (name, (x0, y0, x1, y1)) in enumerate(LABELS[rid]):
    X0, Y0, X1, Y1 = max(0, x0 - 70), max(0, y0 - 40), min(1000, x1 + 70), min(1400, y1 + 150)
    c = big[2 * Y0:2 * Y1, 2 * X0:2 * X1].copy()
    cv2.rectangle(c, (2 * (x0 - X0), 2 * (y0 - Y0)), (2 * (x1 - X0), 2 * (y1 - Y0)), (0, 255, 255), 2)
    pil = Image.fromarray(cv2.cvtColor(c, cv2.COLOR_BGR2RGB))
    ImageDraw.Draw(pil).text((4, 2), f"{i + 1}", font=f, fill=(255, 255, 0), stroke_width=3, stroke_fill=(0, 0, 0))
    tiles.append(pil)
cw, ch, cols = 420, 470, 4
sheet = Image.new("RGB", (cols * cw, ((len(tiles) + cols - 1) // cols) * ch), (40, 40, 40))
for i, t in enumerate(tiles):
    t.thumbnail((cw - 6, ch - 6))
    sheet.paste(t, ((i % cols) * cw + 3, (i // cols) * ch + 3))
sheet.save(f"{WORK}/{rid}_leaders_sheet.png")
print(sheet.size)
