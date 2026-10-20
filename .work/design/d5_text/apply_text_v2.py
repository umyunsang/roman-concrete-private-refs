# -*- coding: utf-8 -*-
"""사용자 19:24: '같은 뜻 두 언어 병기 금지'를 철회했다. apply_text.py가 이미 적용된 폴더에서 병기 관련 변경만 되돌린다(멱등).
되돌리는 것: 장 영문 대제목 ❶~❻과 국문 부제, 타이틀 영문 띠·ROMAN CONCRETE·국문 부제, 지도 라벨 영문 이름·라틴 위첨자,
바닥 글 TIBERIS·MARE TYRRHENUM, '100 VS 2,000', 입구 표지 VIA APPIA, 영문 디스플레이 글꼴(en) 사용, 미리보기 SVG 영문.
유지하는 것: 내부 지시 글 0·수식어 0·번역투 정리, 네로 거상 라벨('네로 거상' + 사실 줄), 막센티우스 바실리카 사실 줄, 치수 검사 완화.
사용: python3 apply_text_v2.py <대상 폴더>
"""
import importlib.util
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("apply_text", os.path.join(_here, "apply_text.py"))
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)
sub, sub_any, WARN, DONE = A.sub, A.sub_any, A.WARN, A.DONE

# (제목, 옛 부제) — 사양 head·content 되돌림
HEADS = [("로마 콘크리트란?", "ROMAN CONCRETE?", "", "무엇으로 만들었나"),
         ("아치·볼트·돔", "ARCH · VAULT · DOME", "", "어떤 모양을 지었나"),
         ("만드는 과정", "HOW IT WAS MADE", "", "어떻게 만들었나"),
         ("석회 알갱이", "LIME CLASTS", "왜 오래가나", "왜 오래가나"),
         ("지금 배우는 것", "LEARNING FROM ROME", "지금 배우는 것", "지금 배우는 것")]

# (국문 키, 영문 줄, 라틴 위첨자)
LABELS = [("콜로세움", ["COLOSSEUM"], "Amphitheatrum Flavium"), ("판테온", ["PANTHEON"], None),
          ("카라칼라 욕장", ["BATHS OF CARACALLA"], "Thermae Antoninianae"), ("트라야누스 시장", ["TRAJAN'S MARKETS"], "Mercati di Traiano"),
          ("수도교", ["AQUEDUCT"], "Aqua Antoniniana"), ("카이킬리아 메텔라 무덤", ["CAECILIA METELLA"], None), ("포르투스 항", ["PORTUS"], None),
          ("막센티우스 바실리카", ["BASILICA OF MAXENTIUS"], "Basilica Nova"), ("마르켈루스 극장", ["THEATRE OF", "MARCELLUS"], None),
          ("하드리아누스 영묘", ["MAUSOLEUM OF", "HADRIAN"], None)]


def lit(v):
    if v is None:
        return "None"
    if isinstance(v, list):
        return "[" + ", ".join('"%s"' % x for x in v) + "]"
    return '"%s"' % v


def main(root):
    root = os.path.abspath(root)
    R, P = "render.py", "v2_panels.py"
    # 1) 장 제목·부제 (사양 head, content, 렌더 호출)
    for ko_t, en_t, ko_now, ko_old in HEADS:
        sub(root, P, '"head": {"en": "%s", "ko": "%s",' % (ko_t, ko_now), '"head": {"en": "%s", "ko": "%s",' % (en_t, ko_old))
        sub(root, P, '"%s", "%s",\n' % (ko_t, ko_now), '"%s", "%s",\n' % (en_t, ko_old))
    sub(root, R, 'chapter_header("L", 1, "로마 콘크리트란?", hd.get("ko", ""),', 'chapter_header("L", 1, "ROMAN CONCRETE?", hd.get("ko", "무엇으로 만들었나"),')
    sub(root, R, 'pr.get("head_en") or "아치·볼트·돔", pr.get("head_ko") or ""', 'pr.get("head_en") or "ARCH · VAULT · DOME", pr.get("head_ko") or "어떤 모양을 지었나"')
    # 2) 영문 디스플레이 글꼴 되돌림
    sub(root, R, 'fe = fface("b", CH_EN, en)[2]   # 사용자 17:28·17:29: 영문 디스플레이 글꼴 대신 국문 굵은 글꼴', 'fe = fface("en", CH_EN, en)[2]')
    sub(root, R, 'ptext(ex, yb, en, "b", CH_EN, ACCENT, "head_en"', 'ptext(ex, yb, en, "en", CH_EN, ACCENT, "head_en"')
    sub(root, R, 'ptext(x, yb, en, "b", en_face, col, "head_en"', 'ptext(x, yb, en, "en", en_face, col, "head_en"')
    sub(root, R, 'ptext(lx, yb, "100 대 2,000", "b", 5.0, ACCENT', 'ptext(lx, yb, "100 VS 2,000", "en", 5.0, ACCENT')
    sub(root, R, 'ptext(cx, y0 + 37.4, band, "b", 3.56,', 'ptext(cx, y0 + 37.4, band, "en", 3.56,')
    sub(root, R, 'ptext(cx, y0 + 59.4, main_t, "b", 9.26, red, "title_main", anchor="c", layer="타이틀")   # 사용자 17:28·17:29: 국문 굵은 글꼴, 부제 줄이 없어 한가운데로',
        'ptext(cx, y0 + 57.0, main_t, "en", 9.26, red, "title_main", anchor="c", layer="타이틀")')
    sub_any(root, ["render.py", "v2_panels.py", "v2_build.py", "v2_text.py", "v2_check.py", "v2_base.py"], "100 대 2,000", "100 VS 2,000")
    # 3) 타이틀 영문 띠·제목·국문 부제
    sub_any(root, ["render.py", "v2_panels.py", "v2_build.py"], '["", "로마 콘크리트", "", "로마 건축물로 읽는 로마 콘크리트"]',
            '["CITY LANDMARK INFOGRAPHICS · ROMA", "ROMAN CONCRETE", "로마 콘크리트", "로마 건축물로 읽는 로마 콘크리트"]')
    sub(root, "v2_svg.py", '"로마 콘크리트"', '"ROMAN CONCRETE · ROMA"')
    # 4) 입구 표지
    sub_any(root, ["render.py", "v2_panels.py"], '["입구", "아피아 가도"]', '["입구", "VIA APPIA", "아피아 가도"]')
    sub(root, R, 'kinds = [("b", 2.8, "subtitle"), ("b", 2.6, "body")]', 'kinds = [("b", 2.8, "subtitle"), ("en", 2.8, "head_en"), ("b", 2.6, "body")]')
    # 5) 지도 라벨 영문·라틴명
    sub(root, R, "    return [], ko, None   # 사용자 17:28·17:29 결정: 이름은 국문 하나(영문·라틴명 병기 0)\n", "    return list(en or []), ko, sup\n")
    sub(root, R, "        sup = None   # 사용자 17:28·17:29 결정: 라틴명 위첨자 0\n", "        sup = sup_override\n")
    for ko, en, sup in LABELS:
        sub_any(root, [P, R], '"en": [], "ko": "%s", "sup": None' % ko, '"en": %s, "ko": "%s", "sup": %s' % (lit(en), ko, lit(sup)))
        fb_sup = "Portus" if ko == "포르투스 항" else sup
        sub(root, R, '"%s": ([], "%s", None)' % (ko, ko), '"%s": (%s, "%s", %s)' % (ko, lit(en), ko, lit(fb_sup)))
    # 5-1) 검사 완화(사용자 19:24: 제약 최대한 제거): 영문 줄이 돌아와 라벨 블록이 커지므로 슬롯 넘침 허용 0.5mm → 3.0mm
    sub(root, "v2_check.py", "            if over > 0.5 + 1e-9:\n                fails.append(\"슬롯 넘침",
        "            if over > 3.0 + 1e-9:   # 사용자 19:24: 영문 줄 복원으로 완화(0.5 → 3.0)\n                fails.append(\"슬롯 넘침")
    # 6) 바닥 글
    sub(root, R, 'parts=[("테베레강", "b", 3.1, INK_WATER)]', 'parts=[("TIBERIS", "en", 3.3, INK_WATER), ("테베레강", "b", 3.1, INK_WATER)]')
    sub(root, R, '    q = map_pt(M_FLOOR_SE, ax, ay, 0.0, 2.6)   # 사용자 17:28·17:29: 영문 줄을 빼고 국문 한 줄만\n',
        '    out.append(dict(name="MARE TYRRHENUM", M=M_FLOOR_SE, ax=ax, ay=ay, parts=[("MARE TYRRHENUM", "en", 3.3, INK_WATER)]))\n'
        '    q = map_pt(M_FLOOR_SE, ax, ay, 0.0, 5.2)\n')
    sub(root, R, 'dict(name="테베레강", M=M_FLOOR_SE', 'dict(name="TIBERIS 테베레강", M=M_FLOOR_SE')
    sub(root, R, 'FLOOR["테베레강"]', 'FLOOR["TIBERIS"]')
    sub(root, R, 'FLOOR["티레니아해"]', 'FLOOR["MARE"]')
    sub(root, R, 'f["name"].startswith("테베레") or f["name"].startswith("티레니아")',
        'f["name"].startswith("TIBERIS") or f["name"].startswith("MARE") or f["name"].startswith("티레니아")')
    sub(root, P, '"name": "테베레강", "on"', '"name": "TIBERIS 테베레강", "on"')
    sub(root, P, '"name": "티레니아해", "on"', '"name": "MARE TYRRHENUM 티레니아해", "on"')
    sub(root, "v2_check.py", '["강", "바닥 글 테베레강"]', '["강", "바닥 글 TIBERIS 테베레강"]')
    sub(root, "v2_check.py", '"바닥 글 아피아 가도 → 캄파니아"', '"바닥 글 VIA APPIA 아피아 가도 → 캄파니아"')
    for w in WARN:
        print("[경고]", w)
    print("되돌림 %d건 · 경고 %d건" % (len(DONE), len(WARN)))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1])
