# 등각 투영의 지면(Z=0)은 '평면도를 45° 돌린 뒤 세로로 1/√3 눌러 놓은 것'과 같다.
# 따라서 화면을 세로로 √3배 늘리면 지면이 실제 모양(45° 회전 평면도)으로 돌아온다.
# 이어서 -45° 회전하면 월드 X·Y축이 가로·세로에 맞는 평면도가 된다. 액자(포스터 테두리)는 마름모가 된다.
import sys, cv2, numpy as np
out = sys.argv[1]
s3 = np.sqrt(3)
for key in ["bj", "np"]:
    art = cv2.imread(f"{out}/{key}_art.png")
    H, W = art.shape[:2]
    st = cv2.resize(art, (W, int(round(H * s3))), interpolation=cv2.INTER_CUBIC)
    cv2.imwrite(f"{out}/{key}_plan45.jpg", cv2.resize(st, (700, int(700 * st.shape[0] / W))), [cv2.IMWRITE_JPEG_QUALITY, 88])
    # 월드축 평면도: 세로 √3 확대 후 -45° 회전(캔버스 확장)
    h2, w2 = st.shape[:2]
    c = (w2 / 2, h2 / 2)
    R = cv2.getRotationMatrix2D(c, -45, 1.0)
    cos, sin = abs(R[0, 0]), abs(R[0, 1])
    nw, nh = int(h2 * sin + w2 * cos), int(h2 * cos + w2 * sin)
    R[0, 2] += nw / 2 - c[0]; R[1, 2] += nh / 2 - c[1]
    pl = cv2.warpAffine(st, R, (nw, nh), flags=cv2.INTER_CUBIC, borderValue=(40, 40, 40))
    cv2.imwrite(f"{out}/{key}_planXY.jpg", cv2.resize(pl, (1100, int(1100 * nh / nw))), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(f"[{key}] 45° 평면도 {W}x{int(H*s3)}px, 월드축 평면도 {nw}x{nh}px 생성")
