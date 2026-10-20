# 아트 px 박스를 A2 mm로 환산 (x*0.21, y*0.2121)
import sys
boxes = [l.strip() for l in sys.stdin if l.strip()]
for b in boxes:
    name, rest = b.split("|")
    x0, y0, x1, y1 = map(float, rest.split(","))
    print("%-34s px (%4d,%4d)-(%4d,%4d)  mm (%5.1f,%5.1f)-(%5.1f,%5.1f)  %5.1f x %5.1f mm" % (
        name, x0, y0, x1, y1, x0 * .21, y0 * .2121, x1 * .21, y1 * .2121, (x1 - x0) * .21, (y1 - y0) * .2121))
