# -*- coding: utf-8 -*-
"""압축 지리 실측(베이징 3.4절과 같은 방법).
1) 랜드마크 바닥점: 분할 마스크의 아래 25% 행 화소의 x 평균, y = 상자 높이 87.5% 지점 [추정, ±20~40px]
2) 등각 역투영: 화면 (sx, sy)[mm] → 평면 (u, v)[mm]. 지면 축 각 θ(도쿄·뉴욕2 30°, 뉴욕1 26°)
   u = sx/(2cosθ) - sy/(2sinθ),  v = sx/(2cosθ) + sy/(2sinθ)
3) 실제 위경도(근사, ±200m) → 동·북 km. 닮음변환(회전·배율·이동, 반사 허용 여부 둘 다) 최소제곱 적합
4) 거리 압축: 중심 랜드마크에서의 평면 거리 d_p = a · d_r^k (로그 회귀)
"""
import json
import os
import sys

import numpy as np

OUT = "/Users/um-yunsang/roman-concrete-private-refs/.work/out/refs-analysis"
MMX, MMY = 0.21, 594 / 2800

GEO = {
    "203x-tokyo": {
        "theta": 30.0, "center": "도쿄역",
        "pts": {
            "도쿄역": (35.6812, 139.7671), "도쿄 도청": (35.6896, 139.6917), "황궁": (35.6852, 139.7528),
            "가미나리몬(센소지)": (35.7111, 139.7964), "도쿄 스카이트리": (35.7101, 139.8107), "메이지 신궁(도리이·숲 판)": (35.6764, 139.6993),
            "도쿄 타워": (35.6586, 139.7454), "롯폰기 힐스 모리 타워": (35.6604, 139.7292), "하치코 동상": (35.6590, 139.7006),
            "고토쿠지(마네키네코)": (35.6486, 139.6475), "레인보우 브리지": (35.6365, 139.7631), "대관람차": (35.6262, 139.7810),
            "도쿄 빅사이트": (35.6298, 139.7942),
        },
    },
    "203x-newyork2-centralpark": {
        "theta": 30.0, "center": "메트로폴리탄 미술관",
        "pts": {
            "메트로폴리탄 미술관": (40.7794, -73.9632), "구겐하임 미술관": (40.7830, -73.9590), "노이에 갤러리": (40.7813, -73.9602),
            "쿠퍼 휴잇 디자인 박물관": (40.7843, -73.9578), "뉴욕시 박물관": (40.7925, -73.9519), "미국 자연사 박물관": (40.7813, -73.9740),
            "다코타": (40.7764, -73.9762), "군인·선원 기념비": (40.7932, -73.9801), "세인트 존 더 디바인 대성당": (40.8038, -73.9619),
            "컬럼비아 대학교": (40.8075, -73.9626), "아폴로 극장": (40.8100, -73.9500), "애플 5번가": (40.7637, -73.9727),
            "퀸즈버러교": (40.7570, -73.9544), "윌리엄스버그교": (40.7134, -73.9724),
        },
    },
    "203x-newyork": {
        "theta": 26.0, "center": "엠파이어 스테이트 빌딩",
        "pts": {
            "엠파이어 스테이트 빌딩": (40.7484, -73.9857), "크라이슬러 빌딩": (40.7516, -73.9755), "타임스스퀘어(전광판 탑)": (40.7580, -73.9855),
            "플랫아이언 빌딩": (40.7411, -73.9897), "뉴욕 증권거래소": (40.7069, -74.0113), "원 월드 트레이드 센터": (40.7127, -74.0134),
            "자유의 여신상(리버티섬 받침)": (40.6892, -74.0445), "브루클린 다리": (40.7061, -73.9969), "맨해튼 다리": (40.7075, -73.9908),
            "GE 빌딩": (40.7587, -73.9787), "링컨 센터": (40.7725, -73.9835), "센트럴파크": (40.7829, -73.9654),
        },
    },
}


def base_point(mask):
    ys, xs = np.nonzero(mask)
    y0, y1 = ys.min(), ys.max()
    sel = ys >= y0 + 0.75 * (y1 - y0)
    return float(xs[sel].mean()), float(y0 + 0.875 * (y1 - y0))


def iso_inv(sx, sy, th):
    t = np.radians(th)
    return sx / (2 * np.cos(t)) - sy / (2 * np.sin(t)), sx / (2 * np.cos(t)) + sy / (2 * np.sin(t))


def fit_similarity(P, Q, allow_reflect):
    """P(평면 mm) ≈ s R Q(실제 km) + t. 반환: s, 각, 반사 여부, 잔차."""
    best = None
    for refl in ([False, True] if allow_reflect else [False]):
        Qr = Q.copy()
        if refl:
            Qr[:, 0] = -Qr[:, 0]
        mp, mq = P.mean(0), Qr.mean(0)
        A, B = P - mp, Qr - mq
        U, S, Vt = np.linalg.svd(B.T @ A)
        R = (U @ Vt).T
        if np.linalg.det(R) < 0:
            Vt[-1] *= -1
            R = (U @ Vt).T
        s = S.sum() / (B ** 2).sum()
        pred = (s * (R @ B.T)).T + mp
        res = np.sqrt(((pred - P) ** 2).sum(1))
        ang = float(np.degrees(np.arctan2(R[1, 0], R[0, 0])))
        cand = {"scale_mm_per_km": float(s), "rot_deg": ang, "reflect": refl, "rms_mm": float(np.sqrt((res ** 2).mean())),
                "mean_mm": float(res.mean()), "res_mm": res.tolist(), "R": R, "mp": mp, "mq": mq}
        if best is None or cand["rms_mm"] < best["rms_mm"]:
            best = cand
    return best


def main(ref):
    G = GEO[ref]
    M = np.load(os.path.join(OUT, f"{ref}_lm_masks.npz"))
    names = list(G["pts"].keys())
    lat0 = np.mean([v[0] for v in G["pts"].values()])
    lon0 = np.mean([v[1] for v in G["pts"].values()])
    P, Q, scr = [], [], {}
    for n in names:
        sx, sy = base_point(M[n.replace("/", "_")])
        scr[n] = (round(sx), round(sy))
        u, v = iso_inv(sx * MMX, sy * MMY, G["theta"])
        # 오른손 평면 좌표: p1 = v축(화면 오른쪽 아래 -θ), p2 = u축(화면 오른쪽 위 +θ). (u, v) 순서는 왼손이라 반사가 끼어든다.
        P.append((v, u))
        la, lo = G["pts"][n]
        Q.append(((lo - lon0) * 111.32 * np.cos(np.radians(lat0)), (la - lat0) * 110.57))
    P, Q = np.array(P), np.array(Q)
    f = fit_similarity(P, Q, allow_reflect=False)
    fr = fit_similarity(P, Q, allow_reflect=True)
    # 북쪽 방향이 화면에서 어디로 가나: 실제 북(0,1)을 평면으로 → 화면으로
    t = np.radians(G["theta"])
    nvec = f["R"] @ np.array([0.0, 1.0])  # 평면 (v, u) 방향
    vv, uu = nvec[0], nvec[1]
    sxv = (uu + vv) * np.cos(t)
    syv = (vv - uu) * np.sin(t)
    north_screen = float(np.degrees(np.arctan2(-syv, sxv)))
    # 거리 압축
    ci = names.index(G["center"])
    dp = np.sqrt(((P - P[ci]) ** 2).sum(1))
    dr = np.sqrt(((Q - Q[ci]) ** 2).sum(1))
    m = np.arange(len(names)) != ci
    k, loga = np.polyfit(np.log(dr[m]), np.log(dp[m]), 1)
    res = {"ref": ref, "theta": G["theta"], "n": len(names), "base_points_art": scr,
           "fit": {k2: (round(v, 2) if isinstance(v, float) else v) for k2, v in f.items() if k2 in ("scale_mm_per_km", "rot_deg", "reflect", "rms_mm", "mean_mm")},
           "fit_with_reflection": {k2: (round(v, 2) if isinstance(v, float) else v) for k2, v in fr.items() if k2 in ("scale_mm_per_km", "rot_deg", "reflect", "rms_mm", "mean_mm")},
           "north_on_screen_deg(오른쪽=0, 위=+90)": round(north_screen, 1),
           "per_landmark": {n: {"real_km_from_center": round(float(dr[i]), 2), "plan_mm_from_center": round(float(dp[i]), 1),
                                "fit_residual_mm": round(f["res_mm"][i], 1)} for i, n in enumerate(names)},
           "distance_law": {"plan_mm = a * real_km^k": {"a": round(float(np.exp(loga)), 1), "k": round(float(k), 3)}},
           "real_extent_km": [round(float(Q[:, 0].max() - Q[:, 0].min()), 1), round(float(Q[:, 1].max() - Q[:, 1].min()), 1)],
           "plan_extent_mm": [round(float(P[:, 0].max() - P[:, 0].min()), 1), round(float(P[:, 1].max() - P[:, 1].min()), 1)]}
    with open(os.path.join(OUT, f"{ref}_geo_fit.json"), "w", encoding="utf-8") as fo:
        json.dump(res, fo, ensure_ascii=False, indent=1)
    print(json.dumps({k2: v for k2, v in res.items() if k2 not in ("per_landmark", "base_points_art")}, ensure_ascii=False))
    for n, v in res["per_landmark"].items():
        print("  ", n, v)


if __name__ == "__main__":
    main(sys.argv[1])
