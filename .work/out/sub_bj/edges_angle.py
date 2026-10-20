# 영역 내 강한 경계선의 각도 분포(허프) — 투영 축 각도 실측용
import sys, math, cv2, numpy as np
ART = "/Users/um-yunsang/roman-concrete-private-refs/.work/out/bj_art.png"
x, y, w, h = map(int, sys.argv[1:5]); minlen = int(sys.argv[5]) if len(sys.argv) > 5 else 120
img = cv2.imread(ART); roi = img[y:y+h, x:x+w]
gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
e = cv2.Canny(gray, 40, 120)
ls = cv2.HoughLinesP(e, 1, np.pi/1440, threshold=int(minlen*0.7), minLineLength=minlen, maxLineGap=4)
res = []
if ls is not None:
    for l in ls.reshape(-1, 4):
        x1, y1, x2, y2 = map(int, l)
        ang = math.degrees(math.atan2(-(y2-y1), x2-x1))
        if ang <= -90: ang += 180
        if ang > 90: ang -= 180
        res.append((math.hypot(x2-x1, y2-y1), ang, x1+x, y1+y, x2+x, y2+y))
res.sort(reverse=True)
for r_ in res[:int(sys.argv[6]) if len(sys.argv) > 6 else 25]:
    print("len%6.1f ang%7.2f (%d,%d)-(%d,%d)" % r_)
# 각도 히스토그램(길이 가중)
hist = {}
for ln, a, *_ in res:
    k = round(a)
    hist[k] = hist.get(k, 0) + ln
print("각도(정수) 길이가중 상위:", sorted(hist.items(), key=lambda t: -t[1])[:8])
