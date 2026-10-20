# 목업에서 포스터를 잘라 내고, 상세 크롭 3장의 위치·배율을 템플릿 매칭으로 찾은 뒤
# (1) 포스터 크롭 (2) 고해상도 합성본 (3) 5% 격자 오버레이 (4) 커버리지 지도를 만든다.
import sys, json, cv2, numpy as np
src, out = sys.argv[1], sys.argv[2]
res = {}
for key in ["bj", "np"]:
    mock = cv2.imread(f"{src}/{key}_mock.jpg")
    bg = np.median(mock[5:40, 5:40].reshape(-1, 3), axis=0)
    diff = np.abs(mock.astype(int) - bg).sum(axis=2)
    hsv = cv2.cvtColor(mock, cv2.COLOR_BGR2HSV)
    mask = ((hsv[..., 1] > 35) | (diff > 80)).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    x, y, w, h = cv2.boundingRect(max(cnts, key=cv2.contourArea))
    poster = mock[y:y + h, x:x + w].copy()
    H, W = poster.shape[:2]
    cv2.imwrite(f"{out}/{key}_poster.png", poster)
    pg = cv2.cvtColor(poster, cv2.COLOR_BGR2GRAY)
    info = {"mock_bbox_xywh": [x, y, w, h], "poster_wh": [W, H], "aspect": round(H / W, 4), "crops": {}}
    scales = []
    for c in ["01", "04", "05"]:
        det = cv2.imread(f"{src}/{key}_{c}.jpg", cv2.IMREAD_GRAYSCALE)
        best = (-1, 0, (0, 0), (0, 0))
        for s in np.linspace(0.20, 0.32, 121):
            t = cv2.resize(det, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
            if t.shape[0] > pg.shape[0] or t.shape[1] > pg.shape[1]:
                continue
            r = cv2.matchTemplate(pg, t, cv2.TM_CCOEFF_NORMED)
            _, mv, _, ml = cv2.minMaxLoc(r)
            if mv > best[0]:
                best = (mv, s, ml, t.shape)
        mv, s, (mx, my), (th, tw) = best
        scales.append(s)
        info["crops"][c] = {"score": round(float(mv), 3), "scale": round(float(s), 4), "xy": [int(mx), int(my)],
                            "bbox_norm": [round(mx / W, 4), round(my / H, 4), round((mx + tw) / W, 4), round((my + th) / H, 4)]}
    k = 1 / float(np.median(scales))
    info["detail_px_per_poster_px"] = round(k, 3)
    # 고해상도 합성본: 포스터를 k배 확대하고 상세 크롭을 제자리에 붙인다
    comp = cv2.resize(poster, (int(round(W * k)), int(round(H * k))), interpolation=cv2.INTER_CUBIC)
    cov = np.zeros(comp.shape[:2], np.uint8)
    for c, d in info["crops"].items():
        det = cv2.imread(f"{src}/{key}_{c}.jpg")
        ox, oy = int(round(d["xy"][0] * k)), int(round(d["xy"][1] * k))
        hh, ww = min(det.shape[0], comp.shape[0] - oy), min(det.shape[1], comp.shape[1] - ox)
        comp[oy:oy + hh, ox:ox + ww] = det[:hh, :ww]
        cov[oy:oy + hh, ox:ox + ww] = 255
    cv2.imwrite(f"{out}/{key}_composite.png", comp)
    info["composite_wh"] = [comp.shape[1], comp.shape[0]]
    info["hires_coverage_pct"] = round(float((cov > 0).mean() * 100), 1)
    # 5% 격자 오버레이(합성본 기준, 확인용 축소본)
    g = comp.copy()
    Hc, Wc = g.shape[:2]
    for i in range(0, 21):
        xx = int(Wc * i / 20); yy = int(Hc * i / 20)
        th_ = 3 if i % 2 == 0 else 1
        cv2.line(g, (xx, 0), (xx, Hc), (255, 255, 255), th_)
        cv2.line(g, (0, yy), (Wc, yy), (255, 255, 255), th_)
        if i % 2 == 0:
            cv2.putText(g, str(i * 5), (xx + 4, 34), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 255), 3)
            cv2.putText(g, str(i * 5), (6, yy - 6 if yy > 40 else 40), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 255), 3)
    cv2.imwrite(f"{out}/{key}_grid.jpg", cv2.resize(g, (1100, int(1100 * Hc / Wc))), [cv2.IMWRITE_JPEG_QUALITY, 88])
    cm = cv2.cvtColor(cv2.resize(comp, (520, int(520 * Hc / Wc))), cv2.COLOR_BGR2GRAY)
    cvs = cv2.resize(cov, (520, int(520 * Hc / Wc)))
    vis = cv2.cvtColor(cm, cv2.COLOR_GRAY2BGR)
    vis[cvs > 0] = (0.5 * vis[cvs > 0] + 0.5 * np.array([0, 200, 0])).astype(np.uint8)
    cv2.imwrite(f"{out}/{key}_coverage.png", vis)
    res[key] = info
json.dump(res, open(f"{out}/register.json", "w"), ensure_ascii=False, indent=1)
for key, v in res.items():
    name = "베이징" if key == "bj" else "신문 제작 과정"
    print(f"[{name}] 포스터 {v['poster_wh'][0]}x{v['poster_wh'][1]}px(세로/가로 {v['aspect']}), 합성본 {v['composite_wh'][0]}x{v['composite_wh'][1]}px, 고해상도 커버리지 {v['hires_coverage_pct']}%")
    for c, d in v["crops"].items():
        b = d["bbox_norm"]
        print(f"   크롭 {c}: 일치도 {d['score']}, 위치 x {b[0]*100:.1f}~{b[2]*100:.1f}%, y {b[1]*100:.1f}~{b[3]*100:.1f}%")
