# 도식 전수 목록의 바운딩 박스를 축소 포스터 위에 번호와 함께 표시
import cv2

ART = "/Users/um-yunsang/roman-concrete-private-refs/.work/out/bj_art.png"
OUT = "/Users/um-yunsang/roman-concrete-private-refs/.work/out/sub_bj/overlay_diagrams.png"

# (번호, x0, y0, x1, y1, 종류) — 아트 px
BOXES = [
    ("D01", 610, 73, 1395, 423, "panel"),
    ("D02", 103, 107, 485, 326, "panel"),
    ("D03", 100, 359, 534, 679, "panel"),
    ("D04", 1500, 105, 1872, 476, "panel"),
    ("D05", 100, 2383, 767, 2632, "panel"),
    ("D06", 866, 2384, 1436, 2668, "panel"),
    ("D07", 1521, 2385, 1872, 2644, "panel"),
    ("D08", 98, 2677, 1902, 2731, "panel"),
    ("L01", 644, 471, 829, 658, "label"),
    ("L02", 1026, 432, 1131, 619, "label"),
    ("L03", 405, 635, 613, 960, "label"),
    ("L04", 101, 748, 245, 1002, "label"),
    ("L05", 98, 1269, 262, 1409, "label"),
    ("L06", 495, 1265, 690, 1452, "label"),
    ("L07", 683, 1144, 756, 1234, "label"),
    ("L08", 728, 1385, 888, 1589, "label"),
    ("L09", 930, 1566, 1083, 1719, "label"),
    ("L10", 1243, 1184, 1441, 1446, "bubble"),
    ("L11", 1692, 966, 1899, 1218, "bubble"),
    ("L12", 1257, 1760, 1351, 1856, "label"),
    ("L13", 1444, 1872, 1508, 2010, "label"),
    ("L14", 1656, 1996, 1891, 2171, "label"),
    ("L15", 738, 2120, 952, 2340, "label"),
    ("L16", 1100, 2178, 1249, 2332, "label"),
    ("L17", 96, 2158, 192, 2328, "label"),
    ("G01", 1654, 550, 1727, 593, "geo"),
    ("G02", 1360, 707, 1437, 763, "geo"),
    ("G03", 1074, 886, 1146, 932, "geo"),
    ("G04", 1043, 1204, 1162, 1261, "geo"),
    ("G05", 1575, 2135, 1765, 2250, "geo"),
]
COL = {"panel": (255, 255, 255), "label": (255, 255, 0), "bubble": (0, 255, 0), "geo": (255, 160, 0)}

img = cv2.imread(ART)
s = 0.5
small = cv2.resize(img, (int(img.shape[1] * s), int(img.shape[0] * s)), interpolation=cv2.INTER_AREA)
for name, x0, y0, x1, y1, kind in BOXES:
    c = COL[kind]
    p0 = (int(x0 * s), int(y0 * s))
    p1 = (int(x1 * s), int(y1 * s))
    cv2.rectangle(small, p0, p1, (0, 0, 0), 3)
    cv2.rectangle(small, p0, p1, c, 1)
    (tw, th), _ = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
    cv2.rectangle(small, (p0[0], p0[1] - th - 4), (p0[0] + tw + 4, p0[1]), (0, 0, 0), -1)
    cv2.putText(small, name, (p0[0] + 2, p0[1] - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.45, c, 1, cv2.LINE_AA)
cv2.imwrite(OUT, small)
print("저장", OUT, small.shape)
