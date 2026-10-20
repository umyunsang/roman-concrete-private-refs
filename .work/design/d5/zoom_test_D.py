import sys, random
sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/lib")
sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/design/d5")
from common import *
from PIL import Image, ImageDraw, ImageChops
import zoom_figs_D as Z

def make(fn, seed):
    sub = Layer(0, 0, 62, 62)
    fn(sub, 31.0, 30.0, random.Random(seed))
    mask = Image.new("L", (sub.w, sub.h), 0)
    ImageDraw.Draw(mask).ellipse([sub.X(1), sub.Y(1), sub.X(61), sub.Y(61)], fill=255)
    big = Image.new("RGBA", (sub.w, sub.h), (231, 208, 160, 255))
    img = sub.img.copy(); img.putalpha(ImageChops.multiply(img.getchannel("A"), mask))
    big.alpha_composite(img)
    small = img.resize((sub.w // 2, sub.h // 2), Image.LANCZOS)
    sm = Image.new("RGBA", small.size, (231, 208, 160, 255)); sm.alpha_composite(small)
    return big.convert("RGB"), sm.convert("RGB")

fns = [Z.fig_aqueduct, Z.fig_nero, Z.fig_concrete_master]
ims = [make(f, i + 1) for i, f in enumerate(fns)]
W = ims[0][0].width
sheet = Image.new("RGB", (W * 3 + 40, W + W // 2 + 30), (255, 255, 255))
for i, (b, s) in enumerate(ims):
    sheet.paste(b, (10 + i * (W + 10), 10))
    sheet.paste(s, (10 + i * (W + 10), W + 20))
sheet.save("out/zoom_test/D_시트.png")
print(sheet.size)
