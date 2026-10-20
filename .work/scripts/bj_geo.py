# 베이징 포스터: 랜드마크 바닥점(화면 아트 px)을 등각 역투영해 평면 좌표로 바꾸고,
# 실제 위경도(근사)와 비교해 방위 회전·축척·거리 압축을 추정한다.
import numpy as np, json
S3 = np.sqrt(3)
# 이름: (화면 x, 화면 y, 위도, 경도)  — 화면 좌표는 아트 2000x2800 기준, 바닥 중심 추정(±20px)
L = {
 "자금성(태화전)": (1790, 1293, 39.9163, 116.3972),
 "천안문":       (1335, 1693, 39.9087, 116.3975),
 "천단(기년전)":  (936, 1980, 39.8822, 116.4066),
 "CCTV 본사":    (1760, 1920, 39.9150, 116.4635),
 "냐오차오":      (660, 960, 39.9929, 116.3965),
 "워터큐브":      (400, 1080, 39.9930, 116.3846),
 "이화원(불향각)": (900, 760, 39.9999, 116.2755),
 "만리장성(바다링)": (1300, 540, 40.3594, 116.0200),
 "CCTV 타워":    (270, 1900, 39.9187, 116.3014),
 "국가대극원":     (950, 1360, 39.9033, 116.3893),
 "왕푸징":        (540, 1800, 39.9149, 116.4108),
 "798 예술구":    (1360, 2200, 39.9842, 116.4955),
 "싼리툰 타이구리": (580, 2200, 39.9353, 116.4545),
}
names = list(L)
scr = np.array([[L[n][0], L[n][1]] for n in names], float)
X = scr[:, 0] / S3 + scr[:, 1]; Y = -scr[:, 0] / S3 + scr[:, 1]      # 등각 단위(px)
plan = np.stack([X, Y], 1) * 0.21                                       # mm 환산(등각 길이)
lat0, lon0 = L["자금성(태화전)"][2], L["자금성(태화전)"][3]
real = np.array([[(L[n][3] - lon0) * np.cos(np.radians(lat0)) * 111.32, (L[n][2] - lat0) * 110.57] for n in names])  # 동, 북 km
pc = plan - plan[0]
# 닮음변환(회전+균일 축척, 반사 허용 검사) 최소제곱: real -> plan
def fit(refl):
    R = real.copy()
    if refl: R[:, 0] = -R[:, 0]
    A = R - R.mean(0); B = pc - pc.mean(0)
    U, s, Vt = np.linalg.svd(A.T @ B); Rm = (U @ Vt)
    if np.linalg.det(Rm) < 0: return None
    sc = s.sum() / (A ** 2).sum(); pred = sc * A @ Rm + pc.mean(0)
    return sc, Rm, pred, np.sqrt(((pred - pc) ** 2).sum(1))
best = min([f for f in (fit(False), fit(True)) if f], key=lambda f: f[3].mean())
sc, Rm, pred, err = best
north = np.array([0, 1.0]) @ Rm                       # 실제 북쪽 단위벡터가 평면에서 가리키는 방향
ang_plan = np.degrees(np.arctan2(north[1], north[0]))
# 평면(월드 X,Y) 방향을 화면 방향으로: X축=화면 오른쪽 아래(-30°), Y축=화면 왼쪽 아래(-150°)
sx = (north[0] - north[1]) * np.cos(np.radians(30)); sy = (north[0] + north[1]) * 0.5
ang_screen = np.degrees(np.arctan2(-sy, sx))
print(f"닮음변환 적합: 축척 {sc:.2f} mm/km, 실제 북쪽 → 화면 방향 {ang_screen:+.0f}°(오른쪽=0°, 위=+90°), 평균 오차 {err.mean():.0f}mm")
print("랜드마크별: 실제 거리(km)·방위 | 포스터 평면 거리(mm) | 적합 오차(mm)")
for i, n in enumerate(names):
    d = np.hypot(*real[i]); brg = (np.degrees(np.arctan2(real[i][0], real[i][1])) + 360) % 360
    print(f"  {n:12s} 실제 {d:6.1f}km 방위 {brg:5.0f}° | 평면 {np.hypot(*pc[i]):5.0f}mm | 오차 {err[i]:5.0f}mm")
# 거리 압축: 평면 거리 vs 실제 거리(로그 적합, 자금성 제외)
d_real = np.hypot(real[1:, 0], real[1:, 1]); d_plan = np.hypot(pc[1:, 0], pc[1:, 1])
k, b = np.polyfit(np.log(d_real), np.log(d_plan), 1)
print(f"거리 압축 적합: 평면거리 ≈ {np.exp(b):.0f}mm × (실제 km)^{k:.2f}  (지수 1이면 축척 그대로, 0에 가까울수록 강한 압축)")
json.dump({"names": names, "plan_mm": pc.tolist(), "real_km": real.tolist(), "scale_mm_per_km": sc, "north_screen_deg": ang_screen, "compress_exp": k, "compress_coef_mm": float(np.exp(b))}, open("out/bj_geo.json", "w"), ensure_ascii=False, indent=1)
