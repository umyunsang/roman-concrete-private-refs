# -*- coding: utf-8 -*-
"""설계안 공용 기초(상수·좌표 변환). 담당: global"""
import math

C30 = math.cos(math.radians(30))
T30 = math.tan(math.radians(30))
SQ3 = math.sqrt(3)

POSTER = (420.0, 594.0)
STAGE = (0.0, 92.0, 420.0, 505.0)          # 지도 무대 x0, y0, x1, y1 (베이징 실측 틀)
STAGE_AREA = (STAGE[2] - STAGE[0]) * (STAGE[3] - STAGE[1])
POSTER_AREA = POSTER[0] * POSTER[1]


def to_screen(X, Y, Z=0.0):
    return (C30 * (X - Y), 0.5 * (X + Y) - Z)


def to_plan(x, y):
    a = x / C30
    return ((a + 2 * y) / 2.0, (2 * y - a) / 2.0)


def plan_rect_screen_box(X0, X1, Y0, Y1, h=0.0):
    pts = [to_screen(X, Y) for X in (X0, X1) for Y in (Y0, Y1)]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return [round(min(xs), 1), round(min(ys) - h, 1), round(max(xs), 1), round(max(ys), 1)]

