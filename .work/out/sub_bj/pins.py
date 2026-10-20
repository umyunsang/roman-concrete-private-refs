# 점 지도에서 핀(점보다 큰 노랑 덩어리) 위치 검출
import sys, cv2, numpy as np
ART = "/Users/um-yunsang/roman-concrete-private-refs/.work/out/bj_art.png"
x, y, w, h = map(int, sys.argv[1:5]); amin = int(sys.argv[5]) if len(sys.argv) > 5 else 40
img = cv2.imread(ART); roi = img[y:y+h, x:x+w]
b, g, r = [roi[:, :, i].astype(int) for i in range(3)]
m = ((r > 230) & (g > 220) & (b < 80)).astype(np.uint8)
# 점 격자는 2px 크기라 3x3 열림으로 제거
m2 = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((4, 4), np.uint8))
n, lab, st, cen = cv2.connectedComponentsWithStats(m2, 8)
for i in range(1, n):
    sx, sy, sw, sh, a = st[i]
    if a >= amin:
        print(f"덩어리 x{sx+x}-{sx+x+sw-1} y{sy+y}-{sy+y+sh-1} (w{sw} h{sh}) 면적{a} 중심({cen[i][0]+x:.0f},{cen[i][1]+y:.0f})")
