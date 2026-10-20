"""압축 지리 측정: 랜드마크 바닥점(화면, 정규 단위) -> 지면 평면 역투영 -> 실제 위치(근사 위경도, km)와 닮음변환.
평면 단위 = 지면 축을 따라 잰 화면 길이(1단위 ≈ 0.42mm).
결과: work/geo.json
"""
import json, sys, math
import numpy as np
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from ra_common import *

# (이름, 화면 바닥점 x,y(정규 단위, ±15), 위도, 경도)  위경도는 공개 지도 기준 근사값
PTS = {
 "203x-seoul": {"theta": 26.0, "center": "N서울타워", "pts": [
   ("국회의사당", 150, 820, 37.5319, 126.9140), ("63빌딩", 285, 815, 37.5198, 126.9403),
   ("구 서울역", 150, 640, 37.5559, 126.9723), ("숭례문", 410, 640, 37.5600, 126.9752),
   ("서울시청", 560, 590, 37.5663, 126.9779), ("N서울타워", 650, 700, 37.5512, 126.9882),
   ("흥인지문", 725, 545, 37.5711, 127.0095), ("DDP", 900, 590, 37.5665, 127.0092),
   ("고속터미널", 410, 880, 37.5050, 127.0049), ("코엑스", 590, 930, 37.5116, 127.0595),
   ("롯데월드타워", 780, 990, 37.5126, 127.1025)]},
 "203x-london": {"theta": 26.0, "center": "빅벤", "pts": [
   ("웨스트민스터 사원", 160, 900, 51.4993, -0.1273), ("빅벤", 385, 1010, 51.5007, -0.1246),
   ("런던 아이", 490, 1070, 51.5033, -0.1196), ("30 St Mary Axe", 560, 590, 51.5145, -0.0803),
   ("타워브리지", 720, 680, 51.5055, -0.0754), ("더 샤드", 905, 815, 51.5045, -0.0865)]},
 "203x-berlin": {"theta": 30.0, "center": "TV탑", "pts": [
   ("국회의사당", 190, 630, 52.5186, 13.3762), ("브란덴부르크 문", 125, 985, 52.5163, 13.3777),
   ("홀로코스트 기념비", 250, 815, 52.5139, 13.3787), ("체크포인트 찰리", 395, 925, 52.5075, 13.3904),
   ("카이저 빌헬름 교회", 400, 530, 52.5048, 13.3350), ("베를린 돔", 565, 745, 52.5191, 13.4010),
   ("TV탑", 630, 1160, 52.5208, 13.4094), ("이스트 사이드 갤러리", 470, 1030, 52.5050, 13.4397),
   ("유대인 박물관", 790, 360, 52.5021, 13.3955), ("베를린 중앙역", 835, 540, 52.5251, 13.3694),
   ("전승기념탑", 840, 945, 52.5145, 13.3501), ("세계시계(알렉산더 광장)", 785, 1170, 52.5212, 13.4132)]},
}

def plan(x, y, th):
    t = math.radians(th)
    # 화면: x = (X - Y)cos t, y = (X + Y) sin t  (y 아래로 +).  X: 오른쪽 아래 축, Y: 왼쪽 아래 축
    X = (x / math.cos(t) + y / math.sin(t)) / 2
    Y = (y / math.sin(t) - x / math.cos(t)) / 2
    # 오른손 좌표계로: (X, -Y). 화면 위(뒤쪽) = -(X+Y) 이므로 (X,Y)는 왼손계다.
    return X, -Y

def umeyama(P, Q, allow_reflect=False):
    # Q ≈ s R P + t
    mp, mq = P.mean(0), Q.mean(0)
    A, B = P - mp, Q - mq
    U, S, Vt = np.linalg.svd(B.T @ A / len(P))
    D = np.eye(2)
    if np.linalg.det(U @ Vt) < 0 and not allow_reflect:
        D[1, 1] = -1
    R = U @ D @ Vt
    s = np.trace(np.diag(S) @ D) / (A ** 2).sum(1).mean()
    t = mq - s * R @ mp
    return s, R, t

out = {}
for ref, cfg in PTS.items():
    th = cfg["theta"]
    names = [p[0] for p in cfg["pts"]]
    P = np.array([plan(p[1], p[2], th) for p in cfg["pts"]])       # 평면(포스터 단위)
    lat0 = np.mean([p[3] for p in cfg["pts"]]); lon0 = np.mean([p[4] for p in cfg["pts"]])
    Q = np.array([((p[4] - lon0) * 111.32 * math.cos(math.radians(lat0)), (p[3] - lat0) * 110.57) for p in cfg["pts"]])  # km (동, 북)
    best = None
    for refl in (False, True):
        # 실제(km) -> 평면(단위) 방향으로 맞춘다: P ≈ s R Q + t
        s, R, t = umeyama(Q, P, allow_reflect=refl)
        pred = (s * (R @ Q.T)).T + t
        err = np.linalg.norm(pred - P, axis=1)
        rms = float(np.sqrt((err ** 2).mean()))
        det = np.linalg.det(R)
        cand = {"reflect": bool(det < 0), "scale_units_per_km": round(float(s), 2), "rms_units": round(rms, 1),
                "rms_mm": round(rms * 0.42, 1), "mean_err_mm": round(float(err.mean()) * 0.42, 1),
                "per_point_err_mm": {n: round(float(e) * 0.42, 1) for n, e in zip(names, err)}, "R": R.tolist(), "t": t.tolist()}
        if best is None or rms < best["rms_units"] - 1e-6:
            best = cand
    # 실제 북쪽(0,1 km)이 화면에서 가리키는 방향
    R = np.array(best["R"]); s = best["scale_units_per_km"]
    north_plan = R @ np.array([0, 1.0])
    t_ = math.radians(th)
    # 평면 벡터 -> 화면 벡터
    def to_screen(v):
        X, Y = v[0], -v[1]
        return np.array([(X - Y) * math.cos(t_), (X + Y) * math.sin(t_)])
    ns = to_screen(north_plan); ns = ns / np.linalg.norm(ns)
    north_screen_deg = math.degrees(math.atan2(-ns[1], ns[0]))   # 화면 각(수평 0, 위 +90)
    # 거리 압축: 중심 랜드마크로부터 평면 거리 vs 실제 거리 (log-log 기울기)
    ci = names.index(cfg["center"])
    dP = np.linalg.norm(P - P[ci], axis=1) * 0.42     # mm
    dQ = np.linalg.norm(Q - Q[ci], axis=1)            # km
    msk = np.arange(len(names)) != ci
    b, a = np.polyfit(np.log(dQ[msk]), np.log(dP[msk]), 1)
    # 쌍별 거리 비 분포(평면 mm / 실제 km)
    ratios = (dP[msk] / dQ[msk])
    # 적합도와 방위 오차(중심 기준, 맞춤 회전 적용 후)
    r2 = float(np.corrcoef(np.log(dQ[msk]), np.log(dP[msk]))[0, 1] ** 2)
    Rm = np.array(best["R"])
    bear_err = {}
    for i, n in enumerate(names):
        if i == ci:
            continue
        vq = Rm @ (Q[i] - Q[ci]); vp = P[i] - P[ci]
        d = math.degrees(math.atan2(vp[1], vp[0]) - math.atan2(vq[1], vq[0]))
        d = (d + 180) % 360 - 180
        bear_err[n] = round(d, 0)
    out_extra = {"loglog_r2": round(r2, 2), "bearing_err_deg_after_fit": bear_err,
                 "bearing_abs_err_median": round(float(np.median(np.abs(list(bear_err.values())))), 0)}
    out[ref] = {**out_extra, "theta": th, "n": len(names), "fit": best, "north_on_screen_deg": round(north_screen_deg, 1),
                "dist_exponent_b": round(float(b), 2), "dist_coef_mm": round(float(math.exp(a)), 1),
                "real_km_range_from_center": [round(float(dQ[msk].min()), 2), round(float(dQ[msk].max()), 2)],
                "poster_mm_range_from_center": [round(float(dP[msk].min()), 1), round(float(dP[msk].max()), 1)],
                "mm_per_km_range": [round(float(ratios.min()), 1), round(float(ratios.max()), 1)],
                "per_point": {n: {"real_km": round(float(dq), 2), "poster_mm": round(float(dp), 1)} for n, dq, dp in zip(names, dQ, dP)}}
    print(ref, json.dumps({k: v for k, v in out[ref].items() if k not in ("per_point",)}, ensure_ascii=False))
    print("   per_point", json.dumps(out[ref]["per_point"], ensure_ascii=False))
json.dump(out, open(WORK / "geo.json", "w"), ensure_ascii=False, indent=1)
