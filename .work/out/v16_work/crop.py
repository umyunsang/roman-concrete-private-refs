import sys
from PIL import Image
# usage: crop.py name x0 y0 x1 y1 [scale]   (mm)
name = sys.argv[1]
x0, y0, x1, y1 = [float(v) for v in sys.argv[2:6]]
scale = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0
im = Image.open("out/wireframe_v16.png")
box = (int(x0 * 4), int(y0 * 4), int(x1 * 4), int(y1 * 4))
c = im.crop(box)
if scale != 1.0:
    c = c.resize((int(c.width * scale), int(c.height * scale)), Image.LANCZOS)
c.save("out/v16_work/crop_%s.png" % name)
print(c.size)
