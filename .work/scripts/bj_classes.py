# 베이징 지도 영역의 지배색을 k-평균으로 뽑아 색 분류 지도를 만든다(지면 요소 식별용).
import sys, cv2, numpy as np
out = sys.argv[1]
img = cv2.imread(f"{out}/bj_art.png")
small = cv2.resize(img, (500, 700), interpolation=cv2.INTER_AREA)
lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
K = 12
crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.5)
_, lbl, cen = cv2.kmeans(lab, K, None, crit, 4, cv2.KMEANS_PP_CENTERS)
lbl = lbl.reshape(700, 500)
cen_bgr = cv2.cvtColor(cen.reshape(1, K, 3).astype(np.uint8), cv2.COLOR_LAB2BGR).reshape(K, 3)
order = np.argsort(-np.bincount(lbl.ravel(), minlength=K))
for k in order:
    b, g, r = cen_bgr[k]; L, A, B = cen[k]
    print(f"  군집 {k:2d}: #{r:02x}{g:02x}{b:02x}  Lab({L*100/255:.0f},{A-128:.0f},{B-128:.0f})  비율 {np.mean(lbl==k)*100:5.1f}%")
# 군집별 마스크를 한 장에 모아 본다(4x3 격자)
tiles = []
for k in order:
    m = np.where(lbl[..., None] == k, small, (small * 0.15).astype(np.uint8))
    cv2.putText(m, str(k), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 255, 255), 3)
    tiles.append(cv2.resize(m, (250, 350)))
rows = [np.hstack(tiles[i:i + 4]) for i in range(0, 12, 4)]
cv2.imwrite(f"{out}/bj_clusters.jpg", np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
np.save(f"{out}/bj_kmeans_centers.npy", cen)
