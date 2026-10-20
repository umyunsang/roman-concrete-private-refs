# -*- coding: utf-8 -*-
"""지도 화소를 클래스로 나눈다(바탕·길·물·글자 잉크·그 밖의 오브젝트).
도쿄: 바탕 = inkmask.py의 행별 세이가이하 모델, 길 = Lab(79.6,-3.1,14.0) ΔE<5, 물 = Lab(74.8,-7.9,-14.1) ΔE<6,
      글자 = 붉은 갈색 잉크(a>18, 35<L<75, b>5) 중 가는 획(두께 판정은 하지 않고 색만).
뉴욕2: 하늘 = 남색, 땅(길·블록) = 회베이지 군, 물 = 하늘색 군.
뉴욕1: 바탕 = 남색(밤·물), 섬 = 회청색 길.
출력: <ref>_class.png(팔레트 색), <ref>_class.npy(uint8 라벨)
"""
import os
import sys

import cv2
import numpy as np

ROOT = "/Users/um-yunsang/roman-concrete-private-refs"
OUT = os.path.join(ROOT, ".work/out/refs-analysis")
TMP = os.path.join(OUT, "tny_crops")

# 라벨 번호
BG, ROAD, WATER, TEXT, OBJ, GROUND, SKY = 0, 1, 2, 3, 4, 5, 6
PAL = {BG: (0, 0, 0), ROAD: (60, 160, 200), WATER: (220, 140, 40), TEXT: (40, 40, 230), OBJ: (235, 235, 235),
       GROUND: (90, 110, 110), SKY: (90, 40, 40)}


def to_lab(bgr):
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    lab[..., 0] *= 100 / 255.0
    lab[..., 1] -= 128
    lab[..., 2] -= 128
    return lab


def dE(lab, c):
    c = np.array(c, np.float32)
    return np.sqrt(((lab - c) ** 2).sum(-1))


def tokyo(lab):
    ink = cv2.imread(os.path.join(OUT, "203x-tokyo_ink.png"), 0) > 0
    cls = np.full(lab.shape[:2], OBJ, np.uint8)
    cls[~ink] = BG
    road = ink & (dE(lab, (79.6, -3.1, 14.0)) < 5.0)
    # 강물은 평평한 단색 #98bdd0. 모리 타워 창(#90b4c5, ΔE 3.3)과 가르려고 허용치를 2.6으로 좁힌다.
    water = ink & (dE(lab, (74.6, -7.9, -14.0)) < 2.6)
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    text = ink & (a > 18) & (L > 35) & (L < 78) & (b > 5)
    # 길·강은 '큰 연결 띠'만 인정한다(건물 창의 파란 줄무늬, 판 옆면의 베이지 조각은 오브젝트)
    road = keep_big(road, 2500, close_k=5)
    water = keep_big(water, 8000, close_k=9, return_closed=True) & ink
    cls[road] = ROAD
    cls[water] = WATER
    cls[text] = TEXT
    return cls


def keep_big(m, min_area, close_k=7, return_closed=False):
    """닫힘으로 잡티 틈을 메운 뒤 연결 성분 면적으로 큰 띠만 남긴다(기본: 원래 화소만 반환)."""
    mc = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((close_k, close_k), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(mc, 8)
    keep = np.zeros(n, bool)
    keep[1:] = st[1:, cv2.CC_STAT_AREA] >= min_area
    return keep[lab] if return_closed else (keep[lab] & m)


def ny2(lab):
    """뉴욕2: 하늘(남색) / 땅(블록 회베이지·대로 회색·퀸즈) / 물(이스트강 하늘색·하류 민트·오른쪽 강 파랑) / 그 밖 = 오브젝트."""
    cls = np.full(lab.shape[:2], OBJ, np.uint8)
    sky = dE(lab, (22.7, 6.0, -18.0)) < 8
    water = (dE(lab, (74.7, -6.0, -13.5)) < 6) | (dE(lab, (71.8, -4.7, -14.5)) < 5) | \
            (dE(lab, (81.7, -10.8, -1.0)) < 6) | (dE(lab, (84.1, -12.8, 1.8)) < 5) | \
            (dE(lab, (55.5, -0.3, -19.6)) < 6) | (dE(lab, (52.8, -2.2, -25.0)) < 6)
    ground = (dE(lab, (75.7, -3.0, 9.0)) < 5) | (dE(lab, (69.8, -2.4, 9.7)) < 5) | \
             (dE(lab, (64.8, -1.7, 6.1)) < 4.5) | (dE(lab, (57.6, 0.0, -2.0)) < 4.5) | (dE(lab, (80.0, -2.0, 4.0)) < 3.5)
    water = keep_big(water, 20000, close_k=9, return_closed=True) & (water | ~ground)
    ground = keep_big(ground, 20000, close_k=5)
    cls[ground] = GROUND
    cls[water & ~ground] = WATER
    cls[sky] = SKY
    return cls


def ny1(lab):
    cls = np.full(lab.shape[:2], OBJ, np.uint8)
    navy = (dE(lab, (23.1, 6.0, -19.0)) < 6) | (dE(lab, (25.6, 7.0, -20.5)) < 6)
    island = (dE(lab, (61.9, 0.2, -13.9)) < 6) | (dE(lab, (76.0, -0.6, -5.1)) < 5)
    cls[island] = GROUND
    cls[navy] = BG
    return cls


def main(ref):
    art = cv2.imread(os.path.join(OUT, f"{ref}_art.png"))
    lab = to_lab(art)
    cls = {"203x-tokyo": tokyo, "203x-newyork2-centralpark": ny2, "203x-newyork": ny1}[ref](lab)
    np.save(os.path.join(OUT, f"{ref}_class.npy"), cls)
    vis = np.zeros(art.shape, np.uint8)
    for k, c in PAL.items():
        vis[cls == k] = c
    cv2.imwrite(os.path.join(OUT, f"{ref}_class.png"), vis)
    cv2.imwrite(os.path.join(TMP, f"{ref}_class_small.png"), cv2.resize(vis, (700, 980), interpolation=cv2.INTER_AREA))
    tot = cls.size
    print(ref, {n: round(100 * (cls == k).sum() / tot, 1) for n, k in
                (("bg", BG), ("road", ROAD), ("water", WATER), ("text", TEXT), ("obj", OBJ), ("ground", GROUND), ("sky", SKY))})


if __name__ == "__main__":
    main(sys.argv[1])
