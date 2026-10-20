# 포스터 전체의 지배색 10개(k-평균, Lab) — 문서용 팔레트 표
import sys, cv2, numpy as np
for key, name in [("np", "신문 제작 과정"), ("bj", "베이징")]:
    img = cv2.imread(f"out/{key}_art.png"); small = cv2.resize(img, (400, 560), interpolation=cv2.INTER_AREA)
    lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
    _, lbl, cen = cv2.kmeans(lab, 10, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.5), 4, cv2.KMEANS_PP_CENTERS)
    bgr = cv2.cvtColor(cen.reshape(1, 10, 3).astype(np.uint8), cv2.COLOR_LAB2BGR).reshape(10, 3)
    cnt = np.bincount(lbl.ravel(), minlength=10) / lbl.size * 100
    print(f"[{name}] 지배색(비율순):")
    for k in np.argsort(-cnt):
        b, g, r = bgr[k]; L, A, B = cen[k]
        print(f"   #{r:02x}{g:02x}{b:02x}  {cnt[k]:4.1f}%  Lab({L*100/255:.0f},{A-128:.0f},{B-128:.0f})")
