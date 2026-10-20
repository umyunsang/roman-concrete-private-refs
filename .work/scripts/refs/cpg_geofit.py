"""등각 지도 위 랜드마크 위치를 지면 평면으로 되돌린 뒤, 실제 평면도 위치와 닮음변환으로 맞춰 지리 충실도를 잰다 (2026-10-18).

- 기존 베이징 분석(bj_geo.py)과 같은 생각: 지도 화면 좌표 → 등각 역투영(평면 좌표) → 실제 위치와 닮음변환(회전·배율·이동, 반사 허용 여부 둘 다) 적합.
- 등각 역투영: 화면 (x, y)[mm, y 아래 +] → X = (x/cos30 + y/sin30)/2, Y = (y/sin30 - x/cos30)/2
- 입력 JSON: {"map_pts": {이름: [x_mm, y_mm]}, "real_pts": {이름: [u, v]}}  (real 은 평면도 좌표, v 아래 +)
- 출력: 반사 없음/있음 각각 RMS 잔차(지도 평면 mm), 랜드마크별 잔차, 회전각, 배율
- 사용: uv run --no-project --with numpy python -I cpg_geofit.py <입력.json>
"""
import json
import math
import sys

import numpy as np


def umeyama(src, dst, allow_reflection):
    """dst ≈ s R src + t"""
    mu_s, mu_d = src.mean(0), dst.mean(0)
    xs, xd = src - mu_s, dst - mu_d
    cov = xd.T @ xs / len(src)
    U, S, Vt = np.linalg.svd(cov)
    D = np.eye(2)
    if not allow_reflection and np.linalg.det(U @ Vt) < 0:
        D[1, 1] = -1
    if allow_reflection:
        D = np.eye(2)
    R = U @ D @ Vt
    var_s = (xs ** 2).sum() / len(src)
    s = np.trace(np.diag(S) @ D) / var_s
    t = mu_d - s * R @ mu_s
    return s, R, t


def main() -> None:
    d = json.load(open(sys.argv[1]))
    names = [n for n in d["map_pts"] if n in d["real_pts"]]
    c30, s30 = math.cos(math.radians(30)), math.sin(math.radians(30))
    plan = []
    for n in names:
        x, y = d["map_pts"][n]
        plan.append(((x / c30 + y / s30) / 2, (y / s30 - x / c30) / 2))
    P = np.array(plan)
    Q = np.array([d["real_pts"][n] for n in names], float)
    for refl in (False, True):
        # 실제 → 지도 평면으로 맞춘다(잔차를 지도 평면 mm로 읽기 위해)
        s, R, t = umeyama(Q, P, refl)
        pred = (s * (R @ Q.T)).T + t
        res = np.linalg.norm(pred - P, axis=1)
        ang = math.degrees(math.atan2(R[1, 0], R[0, 0]))
        det = np.linalg.det(R)
        spread = np.sqrt(((P - P.mean(0)) ** 2).sum(1).mean())
        print(f"[{'반사 허용' if refl else '반사 없음'}] det={det:+.0f} 회전 {ang:+.1f}° 배율 {s:.3f} "
              f"RMS 잔차 {np.sqrt((res ** 2).mean()):.1f}mm 평균 {res.mean():.1f}mm 최대 {res.max():.1f}mm "
              f"(랜드마크 분산 반경 {spread:.1f}mm, 잔차/반경 {np.sqrt((res ** 2).mean()) / spread:.2f})")
        for n, r in sorted(zip(names, res), key=lambda z: -z[1]):
            print(f"    {n}: {r:.1f}mm")


if __name__ == "__main__":
    main()
