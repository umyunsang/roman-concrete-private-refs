# -*- coding: utf-8 -*-
"""인쇄 글 정리(사용자 17:28·17:29) 멱등 적용 스크립트.

사용: python3 apply_text.py <대상 폴더>   (예: .work/design/d5)
- 글 문자열·폰트 선택·제목 렌더 함수 부분만 문자열 치환한다. 지도 배치(v2_map.py, LAYOUT_SHIFT, 길·강·건물 좌표)와
  라벨 배치 로직(plan_label·LEAD_RULE)은 건드리지 않는다.
- 이미 적용된 대상은 조용히 건너뛰고(멱등), 치환 대상도 없고 적용 흔적도 없으면 경고를 출력한다.
- 규칙(사용자 17:28·17:29): 1) 내부 지시 글 0  2) 수식어 0  3) 같은 뜻 두 언어 병기 0  4) 번역투 0  5) 영문 큰 제목은 국문 굵은 글꼴.
"""
import os
import re
import sys

WARN = []
DONE = []


def sub(root, fname, old, new, count=None, note=""):
    """파일 안 old → new 전부 치환. old가 없고 new가 있으면 이미 적용된 것으로 본다. count가 있으면 old 개수를 확인한다."""
    path = os.path.join(root, fname)
    if not os.path.exists(path):
        WARN.append("파일 없음: %s" % fname)
        return
    s = open(path, encoding="utf-8").read()
    n = s.count(old)
    if n == 0:
        if new and new in s:
            return
        if not new:
            return
        WARN.append("치환 대상 없음: %s | %r%s" % (fname, old[:60], (" [" + note + "]") if note else ""))
        return
    if count is not None and n != count:
        WARN.append("개수 불일치(기대 %d, 실제 %d): %s | %r" % (count, n, fname, old[:60]))
    s = s.replace(old, new)
    open(path, "w", encoding="utf-8").write(s)
    DONE.append((fname, old, new, n))


def sub_any(root, files, old, new):
    """같은 글이 여러 파일에 나올 때: 한 곳도 못 찾고 적용 흔적도 없을 때만 경고"""
    hit = False
    for f in files:
        p = os.path.join(root, f)
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8").read()
        if old in s:
            open(p, "w", encoding="utf-8").write(s.replace(old, new))
            DONE.append((f, old, new, s.count(old)))
            hit = True
        elif new and new in s:
            hit = True
    if not hit and old != new and new:
        WARN.append("치환 대상 없음(전 파일): %r" % old[:60])


# 인쇄 글이 들어 있는 파일(사양 원본 v2_panels.py·렌더 기본값 render.py·사양/보고 복제본 v2_build.py·v2_text.py)
PRINT_FILES = ["render.py", "v2_panels.py", "v2_build.py", "v2_text.py"]

# ─────────── 글 문자열 치환 (옛 글 → 새 글) ───────────
TEXT = [
    # 장 제목: 영문 병기 없이 국문 하나 (4)
    ("ROMAN CONCRETE?", "로마 콘크리트란?"),
    ("ARCH · VAULT · DOME", "아치·볼트·돔"),
    ("HOW IT WAS MADE", "만드는 과정"),
    ("LIME CLASTS", "석회 알갱이"),
    ("LEARNING FROM ROME", "지금 배우는 것"),
    # 장 부제가 제목과 뜻이 겹치면 지운다 (4)
    ("무엇으로 만들었나", ""),
    ("어떤 모양을 지었나", ""),
    ("어떻게 만들었나", ""),
    # 타이틀: 영문 시리즈 띠·영문 큰 제목·중복 국문 부제 제거, '로마 콘크리트' 하나만 (4)
    ('["CITY LANDMARK INFOGRAPHICS · ROMA", "ROMAN CONCRETE", "로마 콘크리트", "로마 건축물로 읽는 로마 콘크리트"]',
     '["", "로마 콘크리트", "", "로마 건축물로 읽는 로마 콘크리트"]'),
    # 입구 표지 (4)
    ('["입구", "VIA APPIA", "아피아 가도"]', '["입구", "아피아 가도"]'),
    # 100 VS 2,000 → 국문 (4)
    ("100 VS 2,000", "100 대 2,000"),
    # 설계자 관점·내부 지시·그림 설명 (1)
    ("로마 콘크리트 단면(모식)", "로마 콘크리트 단면"),
    ("아치(비교 기준)", "아치"),
    ("(바실리카 측랑, 실선)", "바실리카 측랑"),
    ("점선: 바실리카 신랑", "바실리카 신랑"),
    ("막대 길이 = 기둥 없이 덮은 폭 · 반죽을 나무 거푸집에 다져 넣어 곡면 지붕을 만들었다",
     "기둥 없이 덮은 폭(경간) · 반죽을 나무 거푸집에 다져 넣어 곡면 지붕을 만들었다"),
    ("(2025 폼페이: 미리 섞은 더미)", "폼페이 현장의 미리 섞은 더미(2025)"),
    ("(압축 강도는 현대 콘크리트가 높다)", "압축 강도는 현대 콘크리트가 높다"),
    ("(큰 골재, 철근 없음) · 3D 프린팅 내구성", "큰 골재·철근 없음 · 3D 프린팅 내구성"),
    # 수식어·관용구 (3)
    ("철근 없는 돔 · 지름 43.3 m", "돔 지름 43.3 m"),
    ("철근 없이 돔·볼트·방파제를 지었다.", "돔·볼트·방파제에 쓰였고 철근은 쓰지 않았다."),
    ("섞는 순서가 열쇠 → ❹", "섞는 순서는 ❹"),
    ("2023 MIT: 뜨거운 혼합·석회 알갱이의 실마리", "2023 MIT: 뜨거운 혼합·석회 알갱이 제시"),
    ("2023 MIT 연구(프리베르노 시료)가 실마리를 찾고, 2025 폼페이 공사 현장 연구가 확인했다",
     "2023 MIT 연구(프리베르노 시료)가 뜨거운 혼합을 제시하고, 2025 폼페이 공사 현장 연구가 확인했다"),
    ("탄소: 만들 때 배출은 현대 콘크리트와 비슷하거나 더 크고, 오래 쓸수록 이득이다",
     "탄소: 만들 때 배출은 현대 콘크리트와 같거나 더 크고, 수명이 길어 연간 배출은 적다"),
    # 근거 수준은 괄호 메모 대신 사실 문장으로 (1)
    ("열탕실 돔 경간 약 36 m(복원 추정)", "열탕실 돔 경간 약 36 m, 복원안 기준"),
    ("BCE 30–10년 · 드럼 지름 29 m", "기원전 30~10년 · 드럼 지름 29 m"),
    # 네로 거상 라벨: 이름 + 사실 1줄 (2). 근거: docs/research/Basic-대체-정보-추가-건축물-조사-2026-10-19.md 567·572행(플리니우스 약 30.3 m, 콘크리트 받침)
    ('["콘크리트(벽돌 마감) 받침 위의", "네로의 청동 거상(추정)"]', '["네로 거상", "높이 약 30 m 청동상,", "콘크리트 받침"]'),
]

# 막센티우스 바실리카: 이름만 있던 라벨에 사실 1줄을 붙인다. 근거: 같은 조사 보고서 55행(신랑은 교차 볼트 3칸)
BASILICA = [
    ('"en": ["BASILICA OF MAXENTIUS"], "ko": "막센티우스 바실리카", "sup": "Basilica Nova", "body": [],',
     '"en": [], "ko": "막센티우스 바실리카", "sup": None, "body": ["신랑은 교차 볼트 3칸"],'),
]


def resub(root, fname, pattern, repl):
    """정규식 치환(이미 적용돼 바뀔 것이 없으면 조용히 건너뜀)"""
    path = os.path.join(root, fname)
    if not os.path.exists(path):
        WARN.append("파일 없음: %s" % fname)
        return
    s = open(path, encoding="utf-8").read()
    t, n = re.subn(pattern, repl, s)
    if t != s:
        open(path, "w", encoding="utf-8").write(t)
        DONE.append((fname, pattern, repl, n))


def main(root):
    root = os.path.abspath(root)
    for old, new in TEXT:
        sub_any(root, PRINT_FILES, old, new)
    for old, new in BASILICA:
        sub(root, "render.py", old, new)
        sub(root, "v2_panels.py", old, new)

    R = "render.py"
    # 1) 라벨: 영문 줄·라틴명(위첨자)을 조판에서 뺀다. 국문 이름 1줄 + 사실 줄. 배치 로직(plan_label)은 그대로.
    sub(root, R, "    return list(en or []), ko, sup\n",
        "    return [], ko, None   # 사용자 17:28·17:29 결정: 이름은 국문 하나(영문·라틴명 병기 0)\n")
    sub(root, R, "    if sup_override is not None:\n        sup = sup_override\n",
        "    if sup_override is not None:\n        sup = None   # 사용자 17:28·17:29 결정: 라틴명 위첨자 0\n")
    # 소품 주석(네로 거상): 첫 줄 = 이름(굵게, 라벨 이름 크기), 나머지 = 사실(본문 크기). 다른 건물 라벨과 같은 형식
    sub(root, R,
        "    for i, t_ in enumerate(lines_):\n        lines.append((t_, fk_, LF_PROP, 0.0, v + i * LF_PROP_PITCH, \"prop_label\"))\n"
        "    W = max(twf(t_, fk_, LF_PROP) for t_ in lines_) if lines_ else 1.0\n"
        "    H = v + LF_PROP_PITCH * (len(lines_) - 1) + 0.7\n",
        "    # 사용자 17:28·17:29 결정: 이름(굵게) + 사실 줄(본문 크기)\n"
        "    v = 0.3 + 3.0\n"
        "    for i, t_ in enumerate(lines_):\n"
        "        if i == 0:\n"
        "            lines.append((t_, \"b\", 3.0, 0.0, v, \"prop_label\"))\n"
        "        else:\n"
        "            lines.append((t_, \"m\", LF_PROP, 0.0, v + 0.6 + LF_PROP_PITCH * i, \"prop_label\"))\n"
        "    W = max(twf(l_[0], l_[1], l_[2]) for l_ in lines) if lines else 1.0\n"
        "    H = v + 0.6 + LF_PROP_PITCH * (len(lines_) - 1) + 0.7\n")

    # 2) 바닥 글: 병기 없이 국문 하나
    sub(root, R, 'parts=[("TIBERIS", "en", 3.3, INK_WATER), ("테베레강", "b", 3.1, INK_WATER)]', 'parts=[("테베레강", "b", 3.1, INK_WATER)]')
    sub(root, R, '    out.append(dict(name="MARE TYRRHENUM", M=M_FLOOR_SE, ax=ax, ay=ay, parts=[("MARE TYRRHENUM", "en", 3.3, INK_WATER)]))\n'
                 '    q = map_pt(M_FLOOR_SE, ax, ay, 0.0, 5.2)\n',
        '    q = map_pt(M_FLOOR_SE, ax, ay, 0.0, 2.6)   # 사용자 17:28·17:29: 영문 줄을 빼고 국문 한 줄만\n')
    # 3) 입구 표지 2줄: 입구(굵게) + 아피아 가도
    sub(root, R, 'kinds = [("b", 2.8, "subtitle"), ("en", 2.8, "head_en"), ("b", 2.6, "body")]', 'kinds = [("b", 2.8, "subtitle"), ("b", 2.6, "body")]')
    sub(root, R, 'ent.get("lines") or ["입구", "VIA APPIA", "아피아 가도"]', 'ent.get("lines") or ["입구", "아피아 가도"]')
    # 4) 타이틀: 영문 큰 글꼴 → 국문 굵은 글꼴, 빈 줄은 건너뜀
    sub(root, R, 'ptext(cx, y0 + 57.0, main_t, "en", 9.26, red, "title_main", anchor="c", layer="타이틀")',
        'ptext(cx, y0 + 59.4, main_t, "b", 9.26, red, "title_main", anchor="c", layer="타이틀")   # 사용자 17:28·17:29: 국문 굵은 글꼴, 부제 줄이 없어 한가운데로')
    sub(root, R, 'ptext(cx, y0 + 37.4, band, "en", 3.56, red, "title_band", anchor="c", layer="타이틀")',
        'ptext(cx, y0 + 37.4, band, "b", 3.56, red, "title_band", anchor="c", layer="타이틀")')
    # 5) 장 머리글: 국문 굵은 글꼴, 부제가 없거나 제목과 같으면 그리지 않는다
    sub(root, R, '    fe = fface("en", CH_EN, en)[2]\n', '    fe = fface("b", CH_EN, en)[2]   # 사용자 17:28·17:29: 영문 디스플레이 글꼴 대신 국문 굵은 글꼴\n')
    sub(root, R, '    box, fa = ptext(ex, yb, en, "en", CH_EN, ACCENT, "head_en", layer=lay, panel=pid)\n    kw = twf(ko, "b", CH_KO)\n',
        '    box, fa = ptext(ex, yb, en, "b", CH_EN, ACCENT, "head_en", layer=lay, panel=pid)\n'
        '    if not ko or ko == en:   # 사용자 17:28·17:29: 부제가 제목과 뜻이 겹치면 둘 중 하나만\n        return yb, None\n'
        '    kw = twf(ko, "b", CH_KO)\n')
    # 6) 100 대 2,000 머리: 국문 굵은 글꼴
    sub(root, R, 'ptext(lx, yb, "100 대 2,000", "en", 5.0, ACCENT, "head_en", layer=lay, panel="S")',
        'ptext(lx, yb, "100 대 2,000", "b", 5.0, ACCENT, "head_en", layer=lay, panel="S")')
    sub(root, R, 'ptext(x, yb, en, "en", en_face, col, "head_en", layer="패널 " + panel, panel=panel)',
        'ptext(x, yb, en, "b", en_face, col, "head_en", layer="패널 " + panel, panel=panel)')

    # 6-1) 사양 원본의 영문·라틴명도 비운다(사양 slot en/sup, 렌더 기본값·대체 문안)
    for f in ("v2_panels.py", "render.py"):
        resub(root, f, r'"en": \[[^\]]*\]', '"en": []')
        resub(root, f, r'"sup": "[^"]+"', '"sup": None')
    resub(root, "render.py", r'\(\[[^\]]*\], ("[^"]+"), ("[^"]+"|None)\)(?=[,\n}])', r'([], \1, None)')
    sub(root, "render.py", '"body_alt_sup": "Pons Aelius", ', '')
    sub(root, "v2_panels.py", '"body_alt_sup": "Pons Aelius", ', '')
    # 6-2) 바닥 글 사양 이름과 렌더 열쇠도 국문 하나로
    sub(root, "v2_panels.py", '"name": "TIBERIS 테베레강"', '"name": "테베레강"')
    sub(root, "v2_panels.py", '"name": "MARE TYRRHENUM 티레니아해"', '"name": "티레니아해"')
    sub(root, R, 'FLOOR["TIBERIS"]', 'FLOOR["테베레강"]')
    sub(root, R, 'FLOOR["MARE"]', 'FLOOR["티레니아해"]')
    sub(root, R, 'dict(name="TIBERIS 테베레강", M=M_FLOOR_SE', 'dict(name="테베레강", M=M_FLOOR_SE')
    sub(root, R, 'f["name"].startswith("TIBERIS") or f["name"].startswith("MARE") or f["name"].startswith("티레니아")',
        'f["name"].startswith("테베레") or f["name"].startswith("티레니아")')
    sub(root, "v2_check.py", '["강", "바닥 글 TIBERIS 테베레강"]', '["강", "바닥 글 테베레강"]')
    sub(root, "v2_check.py", '"바닥 글 VIA APPIA 아피아 가도 → 캄파니아"', '"바닥 글 아피아 가도 → 캄파니아"')

    # 6-3) 사양 설명문(인쇄 안 됨)도 새 타이틀 글에 맞춘다
    sub(root, "v2_panels.py", "국문 부제 = 로마 콘크리트(작업 이름 문구 없음). 영문 띠·ROMAN CONCRETE·로마 건축물로 읽는 로마 콘크리트는 유지. ",
        "사용자 17:28·17:29: 영문 띠·영문 제목·중복 국문 부제를 지우고 '로마 콘크리트'와 '로마 건축물로 읽는 로마 콘크리트'만 둔다. ")
    sub(root, "v2_build.py", "인쇄 글은 영문 시리즈 띠 'CITY LANDMARK INFOGRAPHICS · ROMA', 'ROMAN CONCRETE', 국문 부제 '로마 콘크리트', '로마 건축물로 읽는 로마 콘크리트'뿐이다",
        "인쇄 글은 국문 제목 '로마 콘크리트'와 '로마 건축물로 읽는 로마 콘크리트'뿐이다")

    # 7) 검사 규칙: 네로 거상 라벨의 높이 수치 허용(사용자 17:28·17:29 결정 — 근거 있는 수치 '약 30 m'). 바실리카·영묘·극장 치수 금지는 그대로
    sub(root, "v2_base.py",
        '"극장", "theatre", "marcellus", "네로", "거상", "colossus")',
        '"극장", "theatre", "marcellus")   # 사용자 17:28·17:29 결정: 네로 거상은 근거 있는 높이(약 30 m) 허용')

    # 8) 미리보기 SVG의 영문 표기도 국문으로
    sub(root, "v2_svg.py", '"ROMAN CONCRETE · ROMA"', '"로마 콘크리트"')

    for w in WARN:
        print("[경고]", w)
    print("적용 %d건 · 경고 %d건" % (len(DONE), len(WARN)))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1])
