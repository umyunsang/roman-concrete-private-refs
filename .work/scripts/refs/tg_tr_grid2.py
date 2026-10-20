"""Trabacchi 좌표 격자선 탐지 2: 열·행별 '붉은 기' 평균의 국소 최대(주변 15px 대비 돌출)를 찾는다 (2026-10-18).
입력 이미지는 읽기만 한다. 사용: python -I tg_tr_grid2.py <trabacchi_2.jpg> <trabacchi_4.jpg>
"""
import sys
import cv2
import numpy as np
det = cv2.imread(sys.argv[2]).astype(int)
# 상세 사진의 빨간 격자선 색(열 x≈0.53, y 0.55~0.70)
col = det[550:700, 520:540].reshape(-1, 3)
red_like = col[(col[:, 2] - col[:, 1] > 60)]
print("상세 격자선 색 BGR 중앙값:", np.median(red_like, 0).astype(int).tolist(), "표본", len(red_like))
img = cv2.imread(sys.argv[1]).astype(int); H, W = img.shape[:2]
x0, y0, x1, y1 = int(0.036*W), int(0.062*H), int(0.964*W), int(0.945*H)
redness = img[..., 2] - (img[..., 1] + img[..., 0]) / 2
# 주황 블록(빨강 우세 넓은 면)의 영향을 줄이려고 가로·세로 1px 선만 돌출되는 성분을 쓴다
def prof(axis):
    sub = redness[y0:y1, x0:x1]
    p = sub.mean(axis=axis)
    sm = np.convolve(p, np.ones(31) / 31, mode="same")
    return p - sm
for nm, axis, off, scale in [("수직선 x", 0, x0, W), ("수평선 y", 1, y0, H)]:
    d = prof(axis)
    thr = d.mean() + 3.0 * d.std()
    idx = np.nonzero(d > thr)[0]
    out = []
    for i in idx:
        if out and i - out[-1][-1] <= 4: out[-1].append(i)
        else: out.append([i])
    vals = [round((np.mean(o) + off) / scale, 4) for o in out]
    gaps = np.diff(vals) if len(vals) > 1 else []
    print(nm, "후보:", vals)
    print("   간격:", [round(float(g), 4) for g in gaps])
# 예측 위치 확인: 수평선 간격 0.098 가정 시 각 예측 y 주변 ±6px 안 최대 돌출값(표준편차 단위)
d = prof(1); sd = d.std()
for yv in np.arange(0.1625, 0.945, 0.0977):
    i = int(yv * H) - y0
    seg = d[max(0, i - 6): i + 7]
    j = int(np.argmax(seg)) + max(0, i - 6)
    print(f"  예측 y {yv:.4f} → 최대 돌출 {seg.max() / sd:.1f}σ at y {(j + y0) / H:.4f}")
