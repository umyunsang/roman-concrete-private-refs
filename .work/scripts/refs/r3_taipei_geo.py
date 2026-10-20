"""타이베이 지리 충실도: 랜드마크 바닥점(화면 N) → 등각 역투영 평면 → 실제 위경도(근사, ±200m)와 닮음변환 적합.

- 바닥점은 크롭 판독(받침 중심 또는 건물 밑동 중심, ±10N).
- 위경도는 일반 공개 좌표의 근사값(소수 넷째 자리). 실측이 아니라 참고값이다.
- 닮음변환: 회전·배율·이동(+반사 허용 여부 비교). 잔차는 평면 mm(A2 환산)로.
- 거리 압축: 평면 거리(101 기준) ≈ a·(실거리 km)^k 로그 회귀.
출력: taipei_geo.json
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/refs")
from r3_common import OUT  # noqa: E402

P = {  # 이름: (화면 x, y N), (위도, 경도)
    "고궁박물원": ((510, 440), (25.1024, 121.5485)),
    "디화제": ((712, 435), (25.0569, 121.5098)),
    "시립미술관": ((790, 570), (25.0724, 121.5246)),
    "스린 야시장": ((530, 700), (25.0880, 121.5241)),
    "그랜드 호텔": ((180, 850), (25.0793, 121.5262)),
    "타이베이 101": ((330, 1020), (25.0340, 121.5645)),
    "중앙역": ((690, 880), (25.0478, 121.5170)),
    "용산사": ((110, 1030), (25.0372, 121.4999)),
    "라오허제": ((895, 985), (25.0510, 121.5776)),
    "시먼 홍러우": ((850, 1180), (25.0421, 121.5066)),
    "닝샤 야시장": ((560, 1230), (25.0560, 121.5153)),
    "무지개 횡단보도": ((615, 1275), (25.0433, 121.5070)),
}
names = list(P)
scr = np.array([P[k][0] for k in names], float)
ll = np.array([P[k][1] for k in names], float)
c30, s30 = np.cos(np.radians(30)), np.sin(np.radians(30))
# 등각 역투영(지면): X=(x/c30 + y/s30)/2, Y=(y/s30 - x/c30)/2 (N 단위), mm 환산 0.42
X = (scr[:, 0] / c30 + scr[:, 1] / s30) / 2 * 0.42
Y = (scr[:, 1] / s30 - scr[:, 0] / c30) / 2 * 0.42
plan = np.stack([X, Y], 1)
lat0, lon0 = ll[:, 0].mean(), ll[:, 1].mean()
E = (ll[:, 1] - lon0) * np.cos(np.radians(lat0)) * 111320
N = (ll[:, 0] - lat0) * 110540
real = np.stack([E, N], 1)


def fit(src, dst, reflect):
    s = src.copy()
    if reflect:
        s[:, 1] *= -1
    ms, md = s.mean(0), dst.mean(0)
    a, b = s - ms, dst - md
    U, S, Vt = np.linalg.svd(a.T @ b)
    R = (U @ Vt).T
    if np.linalg.det(R) < 0:
        Vt[-1] *= -1
        R = (U @ Vt).T
    sc = S.sum() / (a ** 2).sum()
    pred = (sc * (R @ a.T)).T + md
    return R, sc, ms, md, pred


best = None
for refl in (False, True):
    # 실제 → 평면(mm)으로 맞춘다
    R, sc, ms, md, pred = fit(real, plan, refl)
    err = np.linalg.norm(pred - plan, axis=1)
    if best is None or err.mean() < best[0]:
        best = (err.mean(), refl, R, sc, ms, md, pred, err)
em, refl, R, sc, ms, md, pred, err = best
# 화면에서 실제 북쪽 방향: 실제 (0,1)m → 평면 → 화면
north_real = np.array([0.0, 1.0])
if refl:
    north_real = north_real * np.array([1, -1])
d_plan = R @ north_real
# 평면 → 화면: x = (X - Y)c30, y = (X + Y)s30 (y 아래)
dx = (d_plan[0] - d_plan[1]) * c30
dy = (d_plan[0] + d_plan[1]) * s30
north_screen_deg = float(np.degrees(np.arctan2(-dy, dx)))
# 거리 압축(101 기준)
i0 = names.index("타이베이 101")
dr = np.linalg.norm(real - real[i0], axis=1) / 1000
dp = np.linalg.norm(plan - plan[i0], axis=1)
m = dr > 0
k, loga = np.polyfit(np.log(dr[m]), np.log(dp[m]), 1)
res = {
    "n_points": len(names),
    "reflection_used": bool(refl),
    "scale_mm_per_km(평면)": round(float(sc) * 1000, 1),
    "mean_residual_mm": round(float(em), 1),
    "max_residual_mm": round(float(err.max()), 1),
    "plan_extent_mm(점들의 평면 범위)": [round(float(np.ptp(plan[:, 0])), 1), round(float(np.ptp(plan[:, 1])), 1)],
    "real_extent_km": [round(float(np.ptp(real[:, 0])) / 1000, 2), round(float(np.ptp(real[:, 1])) / 1000, 2)],
    "north_on_screen_deg(오른쪽0°·위+)": round(north_screen_deg, 1),
    "distance_law_from_101": {"plan_mm≈a·km^k": {"a": round(float(np.exp(loga)), 1), "k": round(float(k), 2)},
                              "real_km_range": [round(float(dr[m].min()), 2), round(float(dr[m].max()), 2)],
                              "plan_mm_range": [round(float(dp[m].min()), 1), round(float(dp[m].max()), 1)]},
    "residuals_mm": {n: round(float(e), 1) for n, e in zip(names, err)},
}
with open(os.path.join(OUT, "taipei_geo.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
