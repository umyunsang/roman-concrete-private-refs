"""[재구성본] 레퍼런스 3점(타이베이·제주·자금성) 타일 선분 각도 측정 (2026-10-18).

알림
- 이 이름의 원본 스크립트는 2026-10-18 20:25쯤, 같은 폴더에서 일하던 다른 분석 워커
  (청와대·피라미드·Gus Morais 담당, 파일 접두사 cpg_)가 같은 파일 이름으로 실수로 덮어써 지워졌다.
- 이 파일은 그 워커가 원본의 출력(.work/out/refs-analysis/r3_angles.json) 형식에 맞춰 다시 만든 재구성본이다.
  최소 선분 길이, 타일 제외 기준 같은 세부는 원본과 다를 수 있다.
- 기존 r3_angles.json 의 값은 원본 스크립트가 낸 것이다. 이 재구성본은 기본으로 r3_angles_reconstructed.json 에 쓰고,
  --overwrite 를 줄 때만 r3_angles.json 을 덮어쓴다.

방법
- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다(r3_common.imread).
- 타일(01·04·05)마다 OpenCV LSD 선분 → 길이 가중 방향 히스토그램 → +30° 근처·-30° 근처 지배 각과 길이 비율.
- 'all'은 세 타일 선분을 합친 값이다. peak_* = [가중 평균 각, 가중 표준편차], share_pct = 길이 비율(%).
- 사용: r3_run.sh r3_angles.py [--overwrite]
"""
import sys

import cv2
import numpy as np

from r3_common import OUT, REFS, imread, save_json

MINLEN = 20.0


def segs(gray):
    lines = cv2.createLineSegmentDetector().detect(gray)[0]
    if lines is None:
        return np.zeros(0), np.zeros(0)
    s = lines.reshape(-1, 4)
    dx, dy = s[:, 2] - s[:, 0], s[:, 3] - s[:, 1]
    L = np.hypot(dx, dy)
    a = np.degrees(np.arctan2(-dy, dx))  # 화면 위쪽이 +, -180~180
    a = (a + 90) % 180 - 90               # -90~90 으로 접는다
    k = L >= MINLEN
    return a[k], L[k]


def pk(a, L, lo, hi):
    m = (a >= lo) & (a <= hi)
    if L[m].sum() == 0:
        return None, 0.0
    h, e = np.histogram(a[m], bins=np.arange(lo, hi + 0.25, 0.25), weights=L[m])
    i = int(np.argmax(h))
    c = (e[i] + e[i + 1]) / 2
    near = m & (np.abs(a - c) <= 1.5)
    mu = float(np.average(a[near], weights=L[near]))
    sd = float(np.sqrt(np.average((a[near] - mu) ** 2, weights=L[near])))
    return (round(mu, 2), round(sd, 2)), float(L[near].sum())


def share(a, L, c, tol=1.5):
    tot = L.sum() if L.sum() > 0 else 1.0
    if c == 90:
        m = np.abs(np.abs(a) - 90) <= tol
    else:
        m = np.abs(a - c) <= tol
    return round(float(L[m].sum() / tot * 100), 1)


def main() -> None:
    res = {}
    for ref, info in REFS.items():
        out, A, LL = {}, [], []
        for t, rel in info["tiles"].items():
            try:
                g = cv2.cvtColor(imread(rel), cv2.COLOR_BGR2GRAY)
            except FileNotFoundError:
                continue
            a, L = segs(g)
            A.append(a)
            LL.append(L)
            p, _ = pk(a, L, 15, 45)
            n, _ = pk(a, L, -45, -15)
            out[t] = {"n": int(a.size),
                      "peak_pos(deg,share%)": [p[0] if p else None, share(a, L, p[0]) if p else 0.0],
                      "peak_neg(deg,share%)": [n[0] if n else None, share(a, L, n[0]) if n else 0.0],
                      "share0": share(a, L, 0), "share90": share(a, L, 90)}
        if A:
            a, L = np.concatenate(A), np.concatenate(LL)
            p, _ = pk(a, L, 15, 45)
            n, _ = pk(a, L, -45, -15)
            out["all"] = {"n_segments": int(a.size), "peak_pos": list(p) if p else None, "peak_neg": list(n) if n else None,
                          "share_pct": {"0°": share(a, L, 0), "90°": share(a, L, 90), "+30°": share(a, L, 30),
                                        "-30°": share(a, L, -30), "+26.6°": share(a, L, 26.57, 1.0),
                                        "-26.6°": share(a, L, -26.57, 1.0)}}
        res[ref] = out
    name = "r3_angles.json" if "--overwrite" in sys.argv else "r3_angles_reconstructed.json"
    print("saved", save_json(name, res), "(OUT =", OUT, ")")


if __name__ == "__main__":
    main()
