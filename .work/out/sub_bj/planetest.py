# 라벨이 어떤 평면 변환인지 판별: (a) 단순 회전, (b) 세로 전단(벽면), (c) 등각 윗면(바닥) 역변환
import sys, math, cv2, numpy as np
ART = "/Users/um-yunsang/roman-concrete-private-refs/.work/out/bj_art.png"
x, y, w, h = map(int, sys.argv[1:5]); ang = float(sys.argv[5]); s = int(sys.argv[6]); out = sys.argv[7]
img = cv2.imread(ART)[y:y+h, x:x+w]
big = cv2.copyMakeBorder(img, h, h, w, w, cv2.BORDER_REPLICATE)
H, W = big.shape[:2]; c = (W/2, H/2)
a = math.radians(ang)
# (a) 회전: 기준선을 수평으로
Ra = cv2.getRotationMatrix2D(c, -ang, 1.0)
A = cv2.warpAffine(big, Ra, (W, H), flags=cv2.INTER_LANCZOS4)
# (b) 세로 전단: y' = y + tan(ang)*(x-cx)
t = math.tan(a)
Sb = np.float32([[1, 0, 0], [t, 1, -t*c[0]]])
B = cv2.warpAffine(big, Sb, (W, H), flags=cv2.INTER_LANCZOS4)
# (c) 바닥면: 텍스트 x축 = 기준선 방향 u=(cos a, -sin a), 텍스트 위쪽 = 다른 등각축 v
#   ang=-30 이면 u=(cos30, +sin30)(오른쪽 아래), 위쪽 v=(cos30, -sin30)(오른쪽 위)
#   ang=+30 이면 u=(cos30, -sin30), 위쪽 v=(-cos30, -sin30)(왼쪽 위)
u = np.array([math.cos(a), -math.sin(a)])
v = np.array([math.cos(a), math.sin(a)]) if ang < 0 else np.array([-math.cos(a), -math.sin(a)])
# 화면 = M_img * 텍스트좌표 (텍스트 y는 아래로 +이므로 위쪽 = -v)
Mimg = np.array([[u[0], -v[0]], [u[1], -v[1]]])
Minv = np.linalg.inv(Mimg)
off = np.array(c) - Minv @ np.array(c)
Cc = np.hstack([Minv, off[:, None]]).astype(np.float32)
C = cv2.warpAffine(big, Cc, (W, H), flags=cv2.INTER_LANCZOS4)
def crop(im): return im[int(H*0.25):int(H*0.75), int(W*0.25):int(W*0.75)]
row = np.hstack([crop(A), crop(B), crop(C)])
row = cv2.resize(row, None, fx=s, fy=s, interpolation=cv2.INTER_LANCZOS4)
cv2.imwrite(out, row)
print("저장: 좌=회전, 중=세로전단(벽), 우=바닥면 역변환")
