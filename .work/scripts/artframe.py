# 원본 아트워크 좌표계(2000x2800, 타일 2x3)로 합성본을 다시 만들고 A2 mm 격자를 덧씌운다.
import sys, json, cv2, numpy as np
src, out = sys.argv[1], sys.argv[2]
reg = json.load(open(f"{out}/register.json"))
TW, TH = 1000, 2800 / 3
for key in ["bj", "np"]:
    r = reg[key]; W, H = r["poster_wh"]; k = r["detail_px_per_poster_px"]
    poster = cv2.imread(f"{out}/{key}_poster.png")
    x01, y01 = r["crops"]["01"]["xy"]               # 타일 01의 포스터상 좌상단 = 아트워크 원점
    ax0, ay0 = x01, y01
    aw, ah = 2000 / k, 2800 / k                      # 아트워크 크기(포스터 px)
    M = np.float32([[2000 / aw, 0, -ax0 * 2000 / aw], [0, 2800 / ah, -ay0 * 2800 / ah]])
    art = cv2.warpAffine(poster, M, (2000, 2800), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    for c, (tx, ty) in {"01": (0, 0), "04": (1000, 933), "05": (0, 1867)}.items():
        t = cv2.imread(f"{src}/{key}_{c}.jpg"); h, w = t.shape[:2]
        h = min(h, 2800 - ty); art[ty:ty + h, tx:tx + w] = t[:h, :w]
    cv2.imwrite(f"{out}/{key}_art.png", art)
    g = art.copy()
    for mm in range(0, 421, 10):                     # A2 420 x 594 mm, 10mm 격자, 50mm 굵게
        x = int(round(mm / 420 * 2000)); th = 3 if mm % 50 == 0 else 1
        cv2.line(g, (x, 0), (x, 2800), (255, 255, 255), th)
        if mm % 50 == 0: cv2.putText(g, str(mm), (x + 4, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)
    for mm in range(0, 595, 10):
        y = int(round(mm / 594 * 2800)); th = 3 if mm % 50 == 0 else 1
        cv2.line(g, (0, y), (2000, y), (255, 255, 255), th)
        if mm % 50 == 0: cv2.putText(g, str(mm), (6, max(40, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)
    cv2.imwrite(f"{out}/{key}_art_grid.jpg", cv2.resize(g, (1000, 1400)), [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(f"[{key}] 아트워크 좌표계 2000x2800 생성, 포스터상 원점({ax0},{ay0}) 크기({aw:.1f}x{ah:.1f})px")
