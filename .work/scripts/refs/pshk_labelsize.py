"""고해상도 타일 위 대표 라벨을 '전단 풀기'로 눕혀 글줄 높이·줄 간격을 잰다 (2026-10-18).

- 등각 벽면 라벨은 글줄이 ±30°로 기울고 세로획은 수직이다(전단). y = y' + x·tan(θ)로 되돌리면 글줄이 수평이 된다.
  전단은 세로 길이를 보존하므로, 펴진 글줄의 띠 높이가 곧 화면 세로 글자 높이다.
- 2배 합성본(타일 해상도) 기준: x 1px = 0.21mm, y 1px = 0.212143mm.
- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- 사용: uv run --no-project --with opencv-python-headless --with numpy --with pillow python -I pshk_labelsize.py
"""
import json

import cv2
import numpy as np

from pshk_common import WORK, composite2x

SAMPLES = [  # ref, 이름, 포스터 좌표 상자, 글줄 기울기(+ 오른쪽 위로 오름)
    ("203x-paris", "Musée d'Orsay", (606, 776, 694, 874), 30),
    ("203x-paris", "Arc de Triomphe", (161, 1036, 239, 1139), 30),
    ("203x-paris", "Musée Rodin", (858, 783, 972, 887), 30),
    ("203x-shanghai", "Shanghai Tower", (621, 731, 699, 864), 30),
    ("203x-shanghai", "Yu Garden", (46, 1091, 134, 1199), -30),
    ("203x-shanghai", "China Art Palace", (906, 746, 984, 854), 30),
    ("203x-hongkong", "Observation Wheel", (618, 571, 704, 654), -30),
    ("203x-hongkong", "Tsim Sha Tsui", (246, 1056, 334, 1144), 30),
    ("203x-hongkong", "Maritime Museum", (761, 721, 844, 794), 30),
]
PXX, PXY = 0.21, 0.212143


def unshear(img, deg):
    h, w = img.shape[:2]
    t = np.tan(np.radians(deg))
    # 화면 y'(아래로 +)에서 글줄은 y' = y0 - x·t (오른쪽 위로 오르면 t>0). 펴려면 y = y' + x·t.
    pad = int(abs(t) * w) + 4
    M = np.float32([[1, 0, 0], [t, 1, pad if t < 0 else 0]])
    if t > 0:
        M = np.float32([[1, 0, 0], [t, 1, 0]])
    out_h = h + pad
    return cv2.warpAffine(img, M, (w, out_h), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))


def bands(prof, thr):
    on = prof > thr
    res, s = [], None
    for i, v in enumerate(on):
        if v and s is None:
            s = i
        if not v and s is not None:
            res.append((s, i))
            s = None
    if s is not None:
        res.append((s, len(on)))
    return [b for b in res if b[1] - b[0] >= 3]


def main():
    out = []
    cache = {}
    for rid, name, (x0, y0, x1, y1), deg in SAMPLES:
        if rid not in cache:
            cache[rid] = composite2x(rid)[0]
        big = cache[rid]
        crop = big[2 * y0:2 * y1, 2 * x0:2 * x1].copy()
        bg = cv2.medianBlur(crop, 31)
        d = np.sqrt(((cv2.cvtColor(crop, cv2.COLOR_BGR2LAB).astype(np.float32) - cv2.cvtColor(bg, cv2.COLOR_BGR2LAB).astype(np.float32)) ** 2).sum(-1))
        m = (d > 24).astype(np.uint8) * 255
        um = unshear(m, deg)
        ui = unshear(crop, deg)
        prof = (um > 0).sum(1).astype(float)
        bs = bands(prof, max(3.0, 0.06 * prof.max()))
        rows = [{"y0": b[0], "y1": b[1], "h_px2x": b[1] - b[0], "h_mm": round((b[1] - b[0]) * PXY, 2)} for b in bs]
        gaps = [round((bs[i + 1][0] - bs[i][0]) * PXY, 2) for i in range(len(bs) - 1)]
        cv2.imwrite(f"{WORK}/crops/labelsize_{rid}_{name.replace(' ', '_').replace(chr(39), '')}.png", ui)
        out.append({"ref": rid, "name": name, "deg": deg, "bands": rows, "pitch_mm": gaps})
        print(f"[{rid}] {name}: 띠 {len(rows)}개 높이(mm) {[r['h_mm'] for r in rows]} 피치(mm) {gaps}")
    json.dump(out, open(f"{WORK}/labelsize.json", "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
