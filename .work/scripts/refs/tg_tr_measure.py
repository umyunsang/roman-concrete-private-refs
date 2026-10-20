"""Trabacchi 1960「Pianta Panoramica di Roma」 정량 실측 (2026-10-18).

- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- 측정
  1) 지도 무대(안쪽 테두리) 안의 색 분류 점유율(주황 블록·녹지·물·노랑·흰 길·잉크·빨강 번호)
  2) 바다(지평선 띠)와 테베레 마스크: 상자, 면적, 중심선 길이, 평균 폭, 액자 출입점
  3) 빨간 번호(뒷면 목록 색인) 개수와 격자 칸별 분포
  4) 펜 그림 밀도(에지 밀도) 지도: 상위 구역의 상자·무게중심
  5) LSD 선분 방향 히스토그램(전체 지도, 고해상 상세 trabacchi_4)
- 사용: python -I tg_tr_measure.py <trabacchi_2.jpg> <trabacchi_4.jpg> <출력 폴더>
"""
import json
import sys

import cv2
import numpy as np

W_EXP, H_EXP = 1500, 1000
# 실측 테두리(tg_tr_frame.py 결과와 확대 판독): 바깥 검은 선과 안쪽 지도 가장자리, 정규 좌표
OUTER = (0.0300, 0.0560, 0.9687, 0.9520)
INNER = (0.0360, 0.0620, 0.9640, 0.9450)
INSETS = {"리도 디 로마(오스티아) 인셋": (0.4247, 0.0655, 0.5703, 0.1590),
          "E.U.R. 인셋": (0.0360, 0.8290, 0.1685, 0.9450)}
SEA_Y_MAX = 0.0845  # 지평선 바다 띠의 아래 끝(확대 판독)


def px_box(b, W, H):
    return int(round(b[0] * W)), int(round(b[1] * H)), int(round(b[2] * W)), int(round(b[3] * H))


# tg_kmeans.py(무대, k=12, 표본 20만, 씨앗 0) 군집 중심 RGB → 의미 분류. 가장 가까운 Lab 중심으로 화소를 나눈다.
CENTERS = [((241, 237, 218), 0), ((218, 206, 181), 0),
           ((244, 166, 105), 1), ((220, 176, 137), 1), ((201, 143, 101), 1),
           ((239, 231, 168), 2),
           ((174, 215, 169), 3), ((169, 188, 154), 3), ((155, 165, 139), 3),
           ((105, 192, 207), 4),
           ((131, 136, 114), 6), ((103, 102, 83), 6)]
NAMES = ["크림(길·광장·여백·기념물 바탕)", "주황(일반 시가 블록 지붕)", "노랑(경기장·특수 부지)", "녹지(공원·구릉·교외)",
         "물(테베레·바다)", "빨강(번호·격자)", "짙은 색(나무 그늘·해칭·펜 선)"]


def classify(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
    cen = np.array([cv2.cvtColor(np.uint8([[c[::-1]]]), cv2.COLOR_BGR2LAB)[0, 0] for c, _ in CENTERS], np.float32)
    d = ((lab[:, None, :] - cen[None, :, :]) ** 2).sum(-1)
    k = np.argmin(d, 1)
    cls = np.array([c for _, c in CENTERS], np.uint8)[k].reshape(img.shape[:2])
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    red = ((h <= 8) | (h >= 175)) & (s >= 110) & (v >= 140)
    cls[red] = 5
    return cls


def skeleton(mask):
    sk = np.zeros_like(mask)
    el = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    m = mask.copy()
    while True:
        er = cv2.erode(m, el)
        op = cv2.dilate(er, el)
        sk |= (m & ~op)
        m = er
        if not m.any():
            break
    return sk


def lsd_peaks(gray, minlen):
    lsd = cv2.createLineSegmentDetector()
    segs = lsd.detect(gray)[0]
    if segs is None:
        return [], 0
    segs = segs.reshape(-1, 4)
    dx, dy = segs[:, 2] - segs[:, 0], segs[:, 3] - segs[:, 1]
    L = np.hypot(dx, dy)
    keep = L >= minlen
    a = (np.degrees(np.arctan2(-dy[keep], dx[keep])) + 90) % 180 - 90  # 화면 위쪽 +, [-90, 90)
    w = L[keep]
    bins = np.arange(-90, 90.5, 1.0)
    hist, _ = np.histogram(a, bins=bins, weights=w)
    tot = w.sum()
    out = []
    order = np.argsort(hist)[::-1]
    for i in order:
        c = (bins[i] + bins[i + 1]) / 2
        if all(abs(((c - o[0]) + 90) % 180 - 90) > 6 for o in out):
            win = np.abs(((a - c) + 90) % 180 - 90) <= 3
            m = float(np.degrees(np.arctan2(np.sum(w[win] * np.sin(np.radians(2 * a[win]))),
                                            np.sum(w[win] * np.cos(np.radians(2 * a[win]))))) / 2)
            out.append((round(m, 1), round(float(w[win].sum() / tot * 100), 1)))
        if len(out) >= 6:
            break
    # 15~45°, 135~165° 대역(지면 축 후보)의 집중도: ±1.5° 안 길이 비
    band = {}
    for nm, lo, hi in [("우상향 15~45°", 15, 45), ("좌상향 -45~-15°", -45, -15)]:
        m = (a >= lo) & (a <= hi)
        if m.sum() == 0:
            band[nm] = None
            continue
        hb, eb = np.histogram(a[m], bins=np.arange(lo, hi + 0.5, 0.5), weights=w[m])
        k = int(np.argmax(hb))
        pk = (eb[k] + eb[k + 1]) / 2
        near = m & (np.abs(a - pk) <= 1.5)
        band[nm] = {"봉우리°": round(float(pk), 2), "봉우리±1.5° 길이비%": round(float(w[near].sum() / tot * 100), 2),
                    "대역 전체 길이비%": round(float(w[m].sum() / tot * 100), 1)}
    vert = float(w[np.abs(np.abs(a) - 90) <= 2].sum() / tot * 100) if tot else 0
    hor = float(w[np.abs(a) <= 2].sum() / tot * 100) if tot else 0
    return {"봉우리(각°, 길이비%)": out, "지면 축 대역": band, "수직±2° 길이비%": round(vert, 1),
            "수평±2° 길이비%": round(hor, 1), "선분 수": int(keep.sum())}, tot


def main():
    src, det_path, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    img = cv2.imread(src)
    H, W = img.shape[:2]
    assert (W, H) == (W_EXP, H_EXP), (W, H)
    x0, y0, x1, y1 = px_box(INNER, W, H)
    stage = np.zeros((H, W), bool)
    stage[y0:y1, x0:x1] = True
    for b in INSETS.values():
        a0, b0, a1, b1 = px_box(b, W, H)
        stage[b0:b1, a0:a1] = False
    res = {"이미지": src, "크기": [W, H], "바깥 테두리": OUTER, "지도 무대(안쪽)": INNER, "인셋": INSETS}
    stage_area = int(stage.sum())
    full_inner = (x1 - x0) * (y1 - y0)
    res["무대 면적 px"] = {"안쪽 테두리 전체": full_inner, "인셋 제외": stage_area,
                       "인셋 합 비율%(안쪽 대비)": round((full_inner - stage_area) / full_inner * 100, 2)}
    res["영역 비율%(이미지 전체 대비)"] = {
        "바깥 테두리 안": round((OUTER[2] - OUTER[0]) * (OUTER[3] - OUTER[1]) * 100, 1),
        "지도 무대(안쪽)": round((INNER[2] - INNER[0]) * (INNER[3] - INNER[1]) * 100, 1),
        **{k: round((b[2] - b[0]) * (b[3] - b[1]) * 100, 2) for k, b in INSETS.items()},
    }
    cls = classify(img)
    frac = {}
    for k, nm in enumerate(NAMES):
        frac[nm] = round(float(((cls == k) & stage).sum() / stage_area * 100), 1)
    res["색 분류 점유율%(인셋 제외 무대)"] = frac
    # 색 분류 확인 이미지
    pal = np.array([[235, 240, 245], [80, 140, 245], [60, 220, 240], [90, 200, 90], [230, 160, 40], [40, 40, 230],
                    [40, 60, 40]], np.uint8)
    vis = pal[cls]
    vis[~stage] = (vis[~stage] * 0.35).astype(np.uint8)
    cv2.imwrite(f"{outdir}/tr_classes.png", vis)

    # 2) 물: 바다 띠와 테베레
    blue = (cls == 4) & stage
    sea = blue.copy()
    sea[int(SEA_Y_MAX * H):, :] = False
    tib = blue.copy()
    tib[:int(SEA_Y_MAX * H), :] = False
    m8 = tib.astype(np.uint8) * 255
    m8 = cv2.morphologyEx(m8, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))  # 잔 점 제거
    m8 = cv2.morphologyEx(m8, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))  # 다리·글자 끊김 메움
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m8, 8)
    order = np.argsort(stats[1:, cv2.CC_STAT_AREA])[::-1] + 1
    comps = []
    for i in order[:6]:
        x, y, w, h, a = stats[i]
        comps.append({"상자 정규": [round(x / W, 4), round(y / H, 4), round((x + w) / W, 4), round((y + h) / H, 4)],
                      "면적 px": int(a), "무대 대비%": round(a / stage_area * 100, 2)})
    main_id = order[0]
    tmask_closed = (lab == main_id)
    tmask = tmask_closed & tib  # 메움 전 실제 물 화소
    sk = skeleton(tmask_closed.astype(np.uint8))
    sk_len = int(sk.sum())
    dist = cv2.distanceTransform(tmask_closed.astype(np.uint8), cv2.DIST_L2, 5)
    widths = 2 * dist[sk > 0]
    ys = np.nonzero(sk)[0]
    wb = {}
    for nm, lo, hi in [("위(먼 쪽) y<0.30", 0, 0.30), ("가운데 0.30~0.60", 0.30, 0.60), ("아래(가까운 쪽) y>0.60", 0.60, 1.0)]:
        sel = (ys >= lo * H) & (ys < hi * H)
        wb[nm] = round(float(np.median(widths[sel])), 1) if sel.any() else None
    # 액자 출입점: 테베레 주성분이 안쪽 테두리 가장자리(±4px)·바다 띠 경계에 닿는 지점
    edge_pts = []
    ys_t, xs_t = np.nonzero(tmask)
    for nm, sel in [("아래 변", ys_t >= y1 - 5), ("오른쪽 변", xs_t >= x1 - 5), ("왼쪽 변", xs_t <= x0 + 5),
                    ("바다 띠 경계(지평선)", ys_t <= int(SEA_Y_MAX * H) + 6)]:
        if sel.any():
            edge_pts.append({"변": nm, "x 범위 정규": [round(xs_t[sel].min() / W, 4), round(xs_t[sel].max() / W, 4)],
                             "y 범위 정규": [round(ys_t[sel].min() / H, 4), round(ys_t[sel].max() / H, 4)]})
    res["물"] = {
        "바다 띠": {"면적 무대 대비%": round(sea.sum() / stage_area * 100, 2),
                  "x 범위 정규": [round(np.nonzero(sea)[1].min() / W, 4), round(np.nonzero(sea)[1].max() / W, 4)] if sea.any() else None,
                  "y 범위 정규": [round(np.nonzero(sea)[0].min() / H, 4), round(np.nonzero(sea)[0].max() / H, 4)] if sea.any() else None},
        "테베레 성분(큰 순)": comps,
        "테베레 주성분": {"중심선 길이 px": sk_len, "중심선 길이/무대 폭": round(sk_len / (x1 - x0), 2),
                     "평균 폭 px(면적/길이)": round(float(tmask.sum() / max(sk_len, 1)), 1),
                     "중심선 폭 중앙값 px(구간별)": wb, "폭/이미지 폭%(가운데 구간)": round((wb["가운데 0.30~0.60"] or 0) / W * 100, 2),
                     "액자·지평선 접점": edge_pts},
    }
    tv = np.zeros((H, W, 3), np.uint8)
    tv[tmask] = (230, 160, 40)
    tv[sea] = (200, 120, 20)
    tv[sk > 0] = (0, 0, 255)
    cv2.imwrite(f"{outdir}/tr_water.png", cv2.addWeighted(img, 0.45, tv, 0.9, 0))

    # 3) 빨간 번호
    red = ((cls == 5) & stage).astype(np.uint8) * 255
    lines_h = cv2.morphologyEx(red, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1)))
    lines_v = cv2.morphologyEx(red, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25)))
    digits = cv2.subtract(red, cv2.dilate(cv2.bitwise_or(lines_h, lines_v), np.ones((3, 3), np.uint8)))
    digits = cv2.morphologyEx(digits, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    merged = cv2.dilate(digits, cv2.getStructuringElement(cv2.MORPH_RECT, (7, 3)))
    n2, lab2, st2, cen2 = cv2.connectedComponentsWithStats(merged, 8)
    keep = []
    for i in range(1, n2):
        x, y, w, h, a = st2[i]
        if 6 <= w <= 40 and 5 <= h <= 18 and a >= 25:
            keep.append((cen2[i][0] / W, cen2[i][1] / H, w, h))
    # 격자 칸(A~N 14열 × 9행 추정 대신 무대 4×4 등분) 분포
    grid = np.zeros((4, 4), int)
    for cx, cy, _, _ in keep:
        gx = min(3, int((cx - INNER[0]) / (INNER[2] - INNER[0]) * 4))
        gy = min(3, int((cy - INNER[1]) / (INNER[3] - INNER[1]) * 4))
        if 0 <= gx < 4 and 0 <= gy < 4:
            grid[gy, gx] += 1
    res["빨간 번호"] = {"검출 수": len(keep), "글자 높이 px 중앙값": float(np.median([k[3] for k in keep])) if keep else None,
                     "무대 4×4 등분 분포(위→아래 행)": grid.tolist(),
                     "주의": "번호 글자 묶음을 연결 성분으로 센 근사값. 노랑·흰 원판 속 번호, 겹친 번호는 하나로 셀 수 있다."}
    nv = img.copy()
    for cx, cy, w, h in keep:
        cv2.rectangle(nv, (int(cx * W - w / 2), int(cy * H - h / 2)), (int(cx * W + w / 2), int(cy * H + h / 2)), (255, 0, 255), 1)
    cv2.imwrite(f"{outdir}/tr_numbers.png", nv)

    # 4) 펜 그림 밀도(에지 밀도): 주황·녹지·물 평면 바깥의 에지만 센다
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    e = cv2.Canny(g, 60, 140) > 0
    flat = np.isin(cls, [1, 3, 4])
    ed = (e & ~flat & stage).astype(np.float32)
    k = 61
    dens = cv2.boxFilter(ed, -1, (k, k), normalize=True)
    dens[~stage] = 0
    thr = np.percentile(dens[stage], 90)
    top = (dens >= thr) & stage
    ys2, xs2 = np.nonzero(top)
    wts = dens[top]
    cx, cy = float(np.average(xs2, weights=wts) / W), float(np.average(ys2, weights=wts) / H)
    # 상위 10% 구역의 30%~70% 분위 상자(핵심 덩어리)
    qx = np.percentile(xs2, [20, 80]) / W
    qy = np.percentile(ys2, [20, 80]) / H
    # 무대를 8×8 칸으로 나눈 밀도
    cells = np.zeros((8, 8))
    for r in range(8):
        for c in range(8):
            a0 = int(x0 + (x1 - x0) * c / 8)
            a1 = int(x0 + (x1 - x0) * (c + 1) / 8)
            b0 = int(y0 + (y1 - y0) * r / 8)
            b1 = int(y0 + (y1 - y0) * (r + 1) / 8)
            cells[r, c] = ed[b0:b1, a0:a1].mean()
    cells = cells / cells.max()
    res["펜 그림 밀도"] = {"상위 10% 무게중심 정규": [round(cx, 3), round(cy, 3)],
                       "상위 10% 20~80분위 상자 정규": [round(qx[0], 3), round(qy[0], 3), round(qx[1], 3), round(qy[1], 3)],
                       "8×8 칸 상대 밀도(최대=1, 위→아래 행)": np.round(cells, 2).tolist()}
    hm = cv2.applyColorMap((dens / dens.max() * 255).astype(np.uint8), cv2.COLORMAP_JET)
    cv2.imwrite(f"{outdir}/tr_density.png", cv2.addWeighted(img, 0.5, hm, 0.5, 0))

    # 5) LSD
    gstage = g[y0:y1, x0:x1]
    p_full, _ = lsd_peaks(gstage, 20)
    det = cv2.imread(det_path, cv2.IMREAD_GRAYSCALE)
    p_det, _ = lsd_peaks(det, 40)
    res["선분 방향(LSD, 길이 가중)"] = {"전체 지도 무대(선분≥20px)": p_full, "고해상 상세 trabacchi_4(선분≥40px)": p_det}
    with open(f"{outdir}/tr_measure.json", "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=float)
    print(json.dumps(res, ensure_ascii=False, indent=1, default=float))


if __name__ == "__main__":
    main()
