"""패널 제목(영문 압축 대문자)·국문 부제의 글자 높이를 고해상도 타일 합성본에서 잰다. 입력은 읽기만 한다. (2026-10-18)
y 1px(2배 합성본) = 0.212143mm.
"""
import cv2
import numpy as np
from pshk_common import composite2x
S = [  # ref, 이름, 상자(포스터 좌표)
    ("203x-paris", "CITY INFORMATION(영문)", (50, 50, 172, 74)), ("203x-paris", "도시정보(국문)", (174, 50, 215, 66)),
    ("203x-paris", "HISTORY(영문)", (756, 52, 812, 76)), ("203x-paris", "BRIDGES OF SEINE RIVER(영문)", (50, 1166, 207, 1192)),
    ("203x-shanghai", "CITY INFORMATION(영문)", (50, 70, 165, 96)), ("203x-shanghai", "도시정보(국문)", (165, 72, 205, 88)),
    ("203x-shanghai", "HISTORY(영문)", (768, 70, 815, 96)),
    ("203x-hongkong", "CITY INFORMATION(영문)", (50, 50, 175, 75)), ("203x-hongkong", "도시정보(국문)", (175, 50, 215, 66)),
    ("203x-hongkong", "HISTORY(영문)", (756, 50, 812, 76)),
]
cache = {}
for rid, name, (x0, y0, x1, y1) in S:
    if rid not in cache:
        cache[rid] = composite2x(rid)
    big, cov = cache[rid]
    c = big[2 * y0:2 * y1, 2 * x0:2 * x1]
    bg = np.median(np.concatenate([c[0], c[-1]]), axis=0)
    d = np.sqrt(((c.astype(np.float32) - bg) ** 2).sum(-1))
    m = d > 60
    rows = np.where(m.mean(1) > 0.02)[0]
    cols = np.where(m.mean(0) > 0.02)[0]
    hires = cov[2 * y0:2 * y1, 2 * x0:2 * x1].mean() > 0.9
    if len(rows):
        h = (rows.max() - rows.min() + 1) * 0.212143
        w = (cols.max() - cols.min() + 1) * 0.21
        print(f"{rid:14s} {name:28s} 글자 높이 {h:4.1f}mm  폭 {w:5.1f}mm  {'타일' if hires else '확대'}")
