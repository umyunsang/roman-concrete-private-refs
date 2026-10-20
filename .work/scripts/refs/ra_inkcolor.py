"""글자 잉크 색: 작은 상자 안에서 바탕과 ΔE>30인 화소의 중앙값(hex)."""
import sys
import cv2, numpy as np
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from ra_common import *
Q = {
 "203x-seoul": [("패널 제목 SUMMARY", (50, 74, 120, 92)), ("라벨 영문명 Sungnyemun Gate", (432, 345, 492, 372)), ("라벨 본문(숭례문)", (440, 382, 495, 425)),
                ("메인 타이틀 SEOUL", (360, 100, 640, 210)), ("부제", (345, 228, 660, 250))],
 "203x-london": [("패널 제목 HISTORY", (50, 52, 96, 70)), ("라벨 영문명 Westminster Abbey", (50, 950, 120, 990)), ("라벨 본문(사원)", (50, 1000, 120, 1045)),
                 ("타이틀 배너", (330, 50, 940, 190))],
 "203x-berlin": [("패널 제목 CITY INFORMATION", (40, 42, 152, 63)), ("라벨 영문명 Berlin Hauptbahnhof", (732, 600, 812, 640)), ("라벨 본문(중앙역)", (735, 640, 815, 662)),
                 ("메인 타이틀 Berlin", (420, 125, 590, 188))],
}
for ref, items in Q.items():
    art = cv2.imread(str(composite_path(ref)))
    lab = cv2.cvtColor(art, cv2.COLOR_BGR2LAB).astype(np.float32)
    for name, (x0, y0, x1, y1) in items:
        sub = lab[y0 * 2:y1 * 2, x0 * 2:x1 * 2]; bgr = art[y0 * 2:y1 * 2, x0 * 2:x1 * 2]
        border = np.concatenate([sub[:2].reshape(-1, 3), sub[-2:].reshape(-1, 3), sub[:, :2].reshape(-1, 3), sub[:, -2:].reshape(-1, 3)])
        bg = np.median(border, 0)
        m = np.linalg.norm(sub - bg, axis=2) > 30
        if m.sum() < 10:
            print(ref, name, "잉크 없음"); continue
        c = np.median(bgr[m], 0).astype(int); b = np.median(art[y0*2:y1*2, x0*2:x1*2][~m], 0).astype(int)
        print(f"{ref} {name}: 잉크 #{c[2]:02x}{c[1]:02x}{c[0]:02x}  바탕 #{b[2]:02x}{b[1]:02x}{b[0]:02x}  잉크비 {m.mean()*100:.0f}%")
