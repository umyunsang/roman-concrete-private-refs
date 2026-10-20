"""Trabacchi 지도 랜드마크 좌표 ↔ 실제 위경도 적합: 닮음·아핀·사영(호모그래피) 비교 (2026-10-18).

- 지도 좌표: 확대 판독·템플릿 정합으로 짚은 정규 좌표(trabacchi_2, 1500×1000). 판독 오차 약 ±0.005(±7px).
- 실제 좌표: 기억에 기반한 근사 위경도(±0.2km 안팎). 오차가 크므로 결과는 경향만 본다.
- 도심점(콜로세움 반경 약 6km)으로만 적합하고, 먼 점(15~30km)은 예측과 실제 그림 자리를 비교한다.
- 사용: python -I tg_tr_geo.py <출력 json>
"""
import json
import math
import sys

import numpy as np

W, H = 1500, 1000
LAT0, LON0 = 41.8902, 12.4922  # 콜로세움
KX = 111.32 * math.cos(math.radians(LAT0))  # km/° 경도
KY = 111.13  # km/° 위도

# (이름, 지도 정규 x, y, 위도, 경도, 신뢰도 1~3)
CITY = [
    ("콜로세움", 0.385, 0.330, 41.8902, 12.4922, 3),
    ("티베리나섬", 0.607, 0.333, 41.8906, 12.4775, 3),
    ("카스텔 산탄젤로", 0.789, 0.490, 41.9031, 12.4663, 3),
    ("트레비 분수(정합)", 0.483, 0.522, 41.9009, 12.4833, 3),
    ("판테온", 0.589, 0.478, 41.8986, 12.4769, 3),
    ("포폴로 광장 오벨리스크", 0.592, 0.728, 41.9107, 12.4764, 2),
    ("밀비오 다리", 0.671, 0.915, 41.9356, 12.4669, 2),
    ("산 파올로 대성당", 0.736, 0.124, 41.8587, 12.4768, 2),
    ("대전차경기장 중심", 0.521, 0.287, 41.8861, 12.4851, 2),
    ("아우구스투스 영묘", 0.5945, 0.630, 41.9060, 12.4763, 3),
    ("카라칼라 욕장(갈색 폐허 묶음)", 0.437, 0.212, 41.8790, 12.4925, 2),
    ("포를라니니 병원(정합)", 0.926, 0.136, 41.8722, 12.4553, 2),
    ("테르미니역 본관", 0.208, 0.448, 41.9010, 12.5005, 2),
    ("비토리아노", 0.470, 0.385, 41.8946, 12.4831, 1),
    ("산 피에트로 광장", 0.888, 0.420, 41.9022, 12.4576, 1),
    ("카이킬리아 메텔라 무덤(노랑 원통)", 0.261, 0.095, 41.8519, 12.5212, 2),
]
FAR = [
    ("치암피노 공항(글자)", 0.160, 0.113, 41.7994, 12.5949),
    ("프라스카티(글자)", 0.085, 0.112, 41.8086, 12.6803),
    ("알바노 호수", 0.1415, 0.0853, 41.7489, 12.6627),
    ("네미 호수", 0.1325, 0.0735, 41.7136, 12.7031),
    ("카스텔 간돌포(글자)", 0.161, 0.094, 41.7469, 12.6503),
    ("리도 디 로마(오스티아, 글자)", 0.773, 0.075, 41.7333, 12.2833),
    ("트라야누스 호수(포르투스 육각 내항 자리)", 0.860, 0.088, 41.7797, 12.2633),
    ("피우미치노(글자)", 0.863, 0.073, 41.7700, 12.2350),
]


def to_km(lat, lon):
    return (lon - LON0) * KX, (lat - LAT0) * KY  # 동(+), 북(+)


def fit_similarity(P, Q):
    # Q ≈ s R P + t  (복소수 최소제곱)
    p = P[:, 0] + 1j * P[:, 1]
    q = Q[:, 0] + 1j * Q[:, 1]
    A = np.c_[p, np.ones_like(p)]
    sol, *_ = np.linalg.lstsq(A, q, rcond=None)
    pred = A @ sol
    return np.c_[pred.real, pred.imag], sol


def fit_affine(P, Q):
    A = np.c_[P, np.ones(len(P))]
    M, *_ = np.linalg.lstsq(A, Q, rcond=None)
    return A @ M, M


def fit_homography(P, Q):
    rows = []
    for (x, y), (u, v) in zip(P, Q):
        rows.append([-x, -y, -1, 0, 0, 0, u * x, u * y, u])
        rows.append([0, 0, 0, -x, -y, -1, v * x, v * y, v])
    _, _, Vt = np.linalg.svd(np.array(rows))
    Hm = Vt[-1].reshape(3, 3)
    Hm /= Hm[2, 2]
    return Hm


def apply_h(Hm, P):
    X = np.c_[P, np.ones(len(P))] @ Hm.T
    return X[:, :2] / X[:, 2:3]


def jac(Hm, e, n, d=0.05):
    p0 = apply_h(Hm, np.array([[e, n]]))[0]
    pe = apply_h(Hm, np.array([[e + d, n]]))[0]
    pn = apply_h(Hm, np.array([[e, n + d]]))[0]
    return np.c_[(pe - p0) / d, (pn - p0) / d]  # px/km, 열 = 동, 북


def main():
    out = {}
    P = np.array([to_km(r[3], r[4]) for r in CITY])
    Q = np.array([[r[1] * W, r[2] * H] for r in CITY])
    names = [r[0] for r in CITY]
    res = {}
    Pm = P.copy()
    Pm[:, 1] *= -1  # 화면 y는 아래로 커지므로 (동, -북)을 회전·확대해야 거울상이 아니다
    ps, sol = fit_similarity(Pm, Q)
    pa, M = fit_affine(P, Q)
    Hm = fit_homography(P, Q)
    ph = apply_h(Hm, P)
    stage_w = (0.964 - 0.036) * W
    for nm, pred in [("닮음(4, 회전·확대·이동)", ps), ("아핀(6)", pa), ("사영(8)", ph)]:
        err = np.hypot(*(pred - Q).T)
        res[nm] = {"평균 오차 px": round(float(err.mean()), 1), "평균 오차/무대 폭%": round(float(err.mean() / stage_w * 100), 1),
                   "RMS px": round(float(np.sqrt((err ** 2).mean())), 1),
                   "최대 px": round(float(err.max()), 1), "최대 점": names[int(err.argmax())]}
    out[f"적합 비교(도심 {len(CITY)}점)"] = res
    rot = math.degrees(math.atan2(sol[0].imag, sol[0].real))
    out["닮음 변환"] = {"축척 px/km": round(abs(sol[0]), 1), "회전°": round(rot, 1),
                    "해석": "회전 약 180°: 화면 위쪽이 실제 남쪽, 왼쪽이 동쪽(북쪽에서 남쪽을 내려다본 시점)"}
    # 아핀 특이값: 두 방향 축척 비 = 기울기(고도) 추정
    A2 = M[:2, :].T  # 2×2: 열 = 동, 북 → 화면 (x, y)
    U, S, Vt = np.linalg.svd(A2)
    out["아핀 분해"] = {"큰 축척 px/km": round(float(S[0]), 1), "작은 축척 px/km": round(float(S[1]), 1),
                    "비(작은/큰)": round(float(S[1] / S[0]), 3),
                    "평행 투영이라면 시선 고도°(asin 비)": round(math.degrees(math.asin(min(1, S[1] / S[0]))), 1),
                    "동쪽 → 화면 벡터(px/km)": np.round(A2[:, 0], 1).tolist(), "북쪽 → 화면 벡터(px/km)": np.round(A2[:, 1], 1).tolist(),
                    "행렬식 부호(+ 거울 아님)": float(np.sign(np.linalg.det(A2)))}
    # 사영: 지도 위·가운데·아래의 국소 축척과 지평선
    loc = {}
    for nm, (e, n) in [("산 파올로(위·먼 쪽)", to_km(41.8587, 12.4768)), ("콜로세움(위 1/3)", (0.0, 0.0)),
                       ("트레비(가운데)", to_km(41.9009, 12.4833)), ("포폴로(아래 1/4)", to_km(41.9107, 12.4764)),
                       ("밀비오 다리(아래·가까운 쪽)", to_km(41.9356, 12.4669))]:
        J = jac(Hm, e, n)
        sv = np.linalg.svd(J, compute_uv=False)
        loc[nm] = {"동쪽 px/km": round(float(np.hypot(*J[:, 0])), 1), "북쪽 px/km": round(float(np.hypot(*J[:, 1])), 1),
                   "특이값 비": round(float(sv[1] / sv[0]), 3)}
    out["사영 국소 축척"] = loc
    # 소실선(지평선): Hm[2,0]*e + Hm[2,1]*n + 1 = 0 인 땅 직선의 화면 상
    h31, h32 = Hm[2, 0], Hm[2, 1]
    # 화면 y = (h21 e + h22 n + h23)/(h31 e + h32 n + 1) 의 극한: 방향 (−h32, h31)으로 멀리 갈 때의 화면점 두 개로 선을 정한다
    def far_pt(direction, k=1e5):
        dvec = np.array(direction, float)
        dvec /= np.linalg.norm(dvec)
        g = np.array([h31, h32])
        g_unit = g / np.linalg.norm(g)
        base = -g_unit * 1e4  # 분모가 0으로 가는 쪽으로 멀리
        return apply_h(Hm, np.array([base + dvec * k * 0.0]))[0]
    g = np.array([h31, h32])
    # 분모 0 직선: g·p = -1. 그 근처(분모 = 0.02, 0.01) 점들의 화면 y로 지평선 높이를 근사
    hz = []
    perp = np.array([-g[1], g[0]]) / np.linalg.norm(g)
    for t in [-30, 0, 30]:
        for eps in [0.02]:
            p = -g / (g @ g) * (1 - eps) + perp * t
            hz.append(apply_h(Hm, np.array([p]))[0].tolist())
    out["사영 지평선(분모→0 근처, 화면 px)"] = {"점": np.round(hz, 1).tolist(),
                                       "지평선 y 정규 근사": round(float(np.mean([p[1] for p in hz]) / H), 3),
                                       "분모 0 땅 직선까지 콜로세움에서 거리 km": round(float(1 / np.linalg.norm(g)), 1)}
    # 먼 점: 사영 예측 vs 실제 그림 자리
    farr = []
    Pf = np.array([to_km(r[3], r[4]) for r in FAR])
    pred_h = apply_h(Hm, Pf)
    pred_a = np.c_[Pf, np.ones(len(Pf))] @ M
    for r, pe, ph_, pa_ in zip(FAR, Pf, pred_h, pred_a):
        d = math.hypot(*pe)
        farr.append({"이름": r[0], "콜로세움에서 km": round(d, 1), "그림 자리 정규": [r[1], r[2]],
                     "사영 예측 정규": [round(ph_[0] / W, 3), round(ph_[1] / H, 3)],
                     "아핀 예측 정규": [round(pa_[0] / W, 3), round(pa_[1] / H, 3)]})
    # 방위 오차: 화면 방향(콜로세움→그림 자리)을 아핀 선형부 역으로 땅 방향으로 되돌려 실제 방위와 비교
    Ainv = np.linalg.inv(M[:2, :].T)
    c0 = np.array([0.385 * W, 0.330 * H])
    for item, r, pe in zip(farr, FAR, Pf):
        vec = Ainv @ (np.array([r[1] * W, r[2] * H]) - c0)
        b_map = (math.degrees(math.atan2(vec[0], vec[1])) + 360) % 360
        b_real = (math.degrees(math.atan2(pe[0], pe[1])) + 360) % 360
        item["실제 방위°"] = round(b_real, 0)
        item["그림 자리 방위°(아핀 역변환)"] = round(b_map, 0)
        item["방위 오차°"] = round(((b_map - b_real) + 180) % 360 - 180, 0)
        item["그림 자리까지 화면 거리 px"] = round(float(np.hypot(*(np.array([r[1] * W, r[2] * H]) - c0))), 0)
    out["먼 점(13~26km) 예측 대비"] = farr
    # 기념물 크기 과장: 그림 화면 폭 px ÷ (실제 동서 폭 × 사영 국소 동쪽 축척)
    MON = [("콜로세움", 0.385, 0.330, 41.8902, 12.4922, 55.7, 184, "타원 188×156m, 장축 동서±25° 가정"),
           ("대전차경기장", 0.521, 0.287, 41.8861, 12.4851, 122.0, 562, "길이 621m·폭 118m, 축 방위 약 128° 가정"),
           ("판테온 원당(돔)", 0.589, 0.470, 41.8986, 12.4769, 37.0, 56, "원당 바깥 지름 약 56m"),
           ("판테온 현관", 0.591, 0.487, 41.8986, 12.4769, 28.0, 34, "현관 폭 약 34m"),
           ("카스텔 산탄젤로 원통", 0.789, 0.490, 41.9031, 12.4663, 33.5, 64, "원통 지름 약 64m"),
           ("아우구스투스 영묘", 0.5945, 0.630, 41.9060, 12.4763, 34.5, 87, "지름 약 87m")]
    mon = []
    for nm, x, y, la, lo, dpx, real_m, note in MON:
        e, n = to_km(la, lo)
        J = jac(Hm, e, n)
        ex = float(abs(J[0, 0]))  # 동쪽 1km당 화면 x 변화(px)
        exp_px = real_m / 1000 * ex
        mon.append({"이름": nm, "그림 폭 px": dpx, "실제 동서 폭 m": real_m, "국소 동서 축척 px/km": round(ex, 1),
                    "실제 축척이면 px": round(exp_px, 1), "과장 배율": round(dpx / exp_px, 2), "가정": note})
    out["기념물 크기 과장(사영 국소 축척 기준)"] = mon
    xs = np.log([m["실제 동서 폭 m"] for m in mon if m["이름"] != "판테온 현관"])
    ys = np.log([m["그림 폭 px"] / m["국소 동서 축척 px/km"] * 1000 for m in mon if m["이름"] != "판테온 현관"])
    out["크기 지수(그림 등가 크기 ∝ 실제 크기^b, 현관 제외 5점)"] = round(float(np.polyfit(xs, ys, 1)[0]), 2)
    # 도심점 잔차 표(사영)
    out["도심점 잔차(사영, px)"] = [{"이름": nm, "실제 동·북 km": [round(p[0], 2), round(p[1], 2)],
                                "잔차 px": round(float(math.hypot(*(a - b))), 1)} for nm, p, a, b in zip(names, P, ph, Q)]
    # 거리 압축: 콜로세움 기준 화면 거리 vs 실제 거리(전 점)
    allp = [(r[0], r[1], r[2], r[3], r[4]) for r in CITY[1:]] + [(r[0], r[1], r[2], r[3], r[4]) for r in FAR]
    dk, dp = [], []
    for nm, x, y, la, lo in allp:
        e, n = to_km(la, lo)
        dk.append(math.hypot(e, n))
        dp.append(math.hypot((x - 0.385) * W, (y - 0.330) * H))
    dk, dp = np.array(dk), np.array(dp)
    b, a = np.polyfit(np.log(dk), np.log(dp), 1)
    out[f"거리 압축(콜로세움 기준, 전 {len(allp)}점)"] = {"화면 거리 px ≈ A × 실제 km^b": {"A": round(float(math.exp(a)), 1), "b": round(float(b), 3)},
                                       "도심(≤6km) 지수": round(float(np.polyfit(np.log(dk[:len(CITY) - 1]), np.log(dp[:len(CITY) - 1]), 1)[0]), 3),
                                       "먼 점(≥13km) 화면 거리 px 범위": [round(float(dp[len(CITY) - 1:].min()), 0), round(float(dp[len(CITY) - 1:].max()), 0)],
                                       "먼 점 실제 km 범위": [round(float(dk[len(CITY) - 1:].min()), 1), round(float(dk[len(CITY) - 1:].max()), 1)]}
    with open(sys.argv[1], "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
