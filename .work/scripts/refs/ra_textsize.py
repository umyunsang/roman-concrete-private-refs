"""지도 라벨 글자 높이: 라벨 영역을 기준선 각도로 전단 해제(세로획은 수직 유지) -> 글자 화소(오츠) -> 행 투영 -> 글줄 띠.
고해상 타일 안 라벨만. 단위: 아트 px -> mm(세로 0.2121mm/px).
출력: work/textsize.json, work/ts_<ref>_<k>.png(전단 해제본)
"""
import json, sys, math
import cv2, numpy as np
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from ra_common import *

L = {
 "203x-seoul": (26.0, [("Sungnyemun Gate", (430, 336, 496, 430), +1), ("63 Building", (300, 376, 354, 482), +1),
                       ("Lotte World Tower", (830, 732, 896, 802), +1), ("Cheonggye Creek", (900, 698, 962, 792), +1),
                       ("Taxi", (900, 792, 962, 848), +1), ("Seoul Express Bus Terminal", (400, 944, 478, 1058), +1),
                       ("City Bus", (48, 928, 102, 992), +1), ("Subway", (50, 998, 98, 1058), +1)]),
 "203x-london": (26.0, [("Big Ben", (134, 386, 228, 512), +1), ("Westminster Abbey", (46, 942, 128, 1048), +1),
                        ("The Underground", (94, 1092, 172, 1202), +1), ("London Bus", (328, 1072, 392, 1125), +1),
                        ("Black Cab", (740, 832, 802, 898), +1)]),
 "203x-berlin": (30.0, [("Reichstagsgebaeude", (140, 404, 268, 482), +1), ("Kaiser-Wilhelm-Gedaechtniskirche", (298, 342, 438, 422), +1),
                        ("Berlin Hauptbahnhof", (730, 586, 818, 662), +1), ("Berliner Siegessaeule", (888, 762, 978, 852), -1),
                        ("Brandenburger Tor", (150, 1078, 282, 1182), +1), ("East Side Gallery", (390, 1072, 472, 1162), +1)]),
}
MMV = 0.2121
out = {}
for ref, (th, items) in L.items():
    art = cv2.imread(str(composite_path(ref)))
    lab = cv2.cvtColor(art, cv2.COLOR_BGR2LAB)[:, :, 0]
    res = []
    for k, (name, (x0, y0, x1, y1), sgn) in enumerate(items):
        X0, Y0, X1, Y1 = x0 * 2, y0 * 2, x1 * 2, y1 * 2
        sub = lab[Y0:Y1, X0:X1]
        h, w = sub.shape
        t = math.tan(math.radians(th))
        # 오름 기준선(+): 오른쪽으로 갈수록 위 -> y' = y + sgn*x*t 로 펴기
        extra = int(w * t) + 2
        M = np.float32([[1, 0, 0], [sgn * t, 1, extra if sgn < 0 else 0]])
        if sgn > 0:
            M = np.float32([[1, 0, 0], [t, 1, 0]])
        flat = cv2.warpAffine(sub, M, (w, h + extra), flags=cv2.INTER_LINEAR, borderValue=255)
        valid = cv2.warpAffine(np.full_like(sub, 255), M, (w, h + extra), flags=cv2.INTER_NEAREST, borderValue=0) > 0
        thr, _ = cv2.threshold(flat[valid].reshape(-1, 1), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        ink = (flat < thr - 8) & valid
        # 세로 지시선(긴 세로 획) 제거: 열마다 연속 길이가 영역 높이의 40% 넘으면 그 열 제외
        colsum = ink.sum(0)
        ink[:, colsum > 0.4 * ink.shape[0]] = False
        prof = ink.sum(1).astype(float)
        prof = np.convolve(prof, np.ones(3) / 3, mode="same")
        on = prof > max(2, 0.08 * prof.max())
        bands = []
        i = 0
        while i < len(on):
            if on[i]:
                j = i
                while j < len(on) and on[j]:
                    j += 1
                if j - i >= 6:
                    bands.append((i, j))
                i = j
            else:
                i += 1
        bh = [round((b - a) * MMV, 2) for a, b in bands]
        pitch = [round((bands[i + 1][0] - bands[i][0]) * MMV, 2) for i in range(len(bands) - 1)]
        res.append({"label": name, "bands_mm": bh, "pitch_mm": pitch})
        vis = cv2.cvtColor(flat, cv2.COLOR_GRAY2BGR)
        for a, b in bands:
            cv2.line(vis, (0, a), (vis.shape[1] - 1, a), (0, 0, 255), 1); cv2.line(vis, (0, b), (vis.shape[1] - 1, b), (255, 0, 0), 1)
        cv2.imwrite(str(WORK / f"ts_{ref}_{k}.png"), vis)
        print(ref, name, "bands(mm):", bh, "pitch:", pitch)
    out[ref] = res
json.dump(out, open(WORK / "textsize.json", "w"), ensure_ascii=False, indent=1)
