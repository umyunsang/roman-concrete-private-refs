# -*- coding: utf-8 -*-
"""인쇄 글 위반 검사(사용자 17:28·17:29): drawn.json의 texts 전체와 spec.json의 인쇄 글 필드에서
내부 지시 글·수식어·같은 뜻 두 언어 병기·번역투 위반을 센다. 전부 0이어야 통과(종료 코드 0).

사용: python3 check_text.py [폴더(기본: 이 파일 위치)]   → 폴더/out/text-list.json 에 인쇄 글 목록도 쓴다.
"""
import json
import os
import re
import sys

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
ROOT = os.path.abspath(ARGS[0]) if ARGS else os.path.dirname(os.path.abspath(__file__))
# 사용자 19:24: 병기 금지 철회 → apply_text_v2.py 적용 뒤에는 --병기허용 로 실행(병기 검사를 건너뛴다)
ALLOW_BI = "--병기허용" in sys.argv

# 1) 내부 지시 글: 그림을 어떻게 그렸는지·사양·제작 메모·설계자 관점
INTERNAL = [r"모식", r"자리만", r"확대", r"예약", r"그림은", r"[를을] 나타낸다", r"나타낸다", r"지시선", r"[A-D] ?표지", r"실선", r"점선", r"비교 기준",
            r"\(복원 ?추정\)", r"\(추정\)", r"거상\(추정\)", r"받침 위의", r"작업", r"사양", r"검사", r"[0-9]\s?mm", r"티어", r"위치도", r"연대기", r"선택 대기",
            r"막대 길이 ?=", r"스팬 비교"]
# 2) 수식어: 사실을 꾸미는 형용사·부사·관용구(재료·기술 용어 '가벼운 골재'·'판상 결정'은 용어라 허용)
MODIFIER = [r"거대한", r"[0-9,]+년째", r"오히려", r"스스로", r"철근 없는", r"매우", r"아주", r"엄청", r"놀라운", r"훌륭", r"정교한", r"웅장", r"뛰어난",
            r"그야말로", r"무려", r"단연", r"열쇠", r"실마리", r"이득", r"더욱", r"훨씬", r"굉장"]
# 3) 번역투(국문)
TRANSLATIONESE = [r"에 의해", r"에 의하여", r"로부터", r"[를을] 가진", r"[를을] 가지고", r"하는 것이다", r"것이다", r"에 있어서", r"[를을] 통하여", r"되어진", r"로 인해",
                  r"의 경우"]
# 4) 병기: 영문 낱말(3자 이상, 허용 약어 제외)·영문 디스플레이 글꼴
LATIN = re.compile(r"[A-Za-z]{3,}")
LATIN_OK = {"MIT"}


def load(rel):
    return json.load(open(os.path.join(ROOT, rel), encoding="utf-8"))


def scan(strings, where):
    """(위치, 글) 목록 → 위반 목록"""
    bad = []
    for loc, s in strings:
        if not isinstance(s, str) or not s.strip():
            continue
        for pat in INTERNAL:
            if re.search(pat, s):
                bad.append(("내부 지시", where, loc, s, pat))
        for pat in MODIFIER:
            if re.search(pat, s):
                bad.append(("수식어", where, loc, s, pat))
        for pat in TRANSLATIONESE:
            if re.search(pat, s):
                bad.append(("번역투", where, loc, s, pat))
        for m in LATIN.findall(s):
            if m not in LATIN_OK:
                bad.append(("병기", where, loc, s, "영문 낱말 %s" % m))
    return bad


def spec_print_strings(spec):
    """spec.json에서 인쇄되는 글 필드만 모은다(키 이름 기준). 설계 주석(note 등)은 제외"""
    keys = {"en", "ko", "sup", "body", "print", "print_texts", "content", "tag_text", "lines", "caption", "footnote", "carbon", "text", "title", "step", "steps"}
    out = []

    skip = ("/meta", "/note", "figure_spec", "/owner", "anchor", "/figure", "_rule", "/rule")

    def walk(o, path, in_print):
        if any(sg in path for sg in skip):
            return
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, path + "/" + k, in_print or k in keys)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, path + "[%d]" % i, in_print)
        elif isinstance(o, str) and in_print:
            out.append((path, o))
    walk(spec, "", False)
    # 사양 라벨·바닥 글 이름(인쇄되는 이름)
    for fl in ((spec.get("core_map") or {}).get("labels") or {}).get("floor_text", []):
        out.append(("core_map/labels/floor_text/name", fl.get("name", "")))
    return out


def main():
    drawn = load("out/drawn.json")
    texts = [t for t in drawn["texts"] if t.get("text") and t.get("role") != "mark"]
    items = [("%s/%s" % (t.get("layer", ""), t.get("role", "")), t["text"]) for t in texts]
    bad = scan(items, "drawn.json texts")
    # 영문 디스플레이 글꼴(en) 사용 0
    for t in texts:
        if t.get("font") == "en":
            bad.append(("병기", "drawn.json texts", t.get("layer", ""), t["text"], "영문 디스플레이 글꼴(en) 사용"))
    # 같은 장의 제목과 부제가 같은 글이거나 포함 관계면 중복
    by_layer = {}
    for t in texts:
        by_layer.setdefault(t.get("layer", ""), []).append(t)
    for lay, ts in by_layer.items():
        heads = [t["text"] for t in ts if t["role"] in ("head_en", "title_main")]
        subs = [t["text"] for t in ts if t["role"] in ("subtitle", "title_sub", "head_ko") and t["text"] not in ()]
        for h in heads:
            for sb in subs:
                if sb == h or (len(sb) > 3 and sb in h) or (len(h) > 3 and h in sb):
                    bad.append(("병기", "drawn.json texts", lay, "%s / %s" % (h, sb), "제목과 부제가 같은 뜻 중복"))
    # 지도 라벨: 이름 1줄(label_ko) + 영문(label_en)·라틴명(label_sup) 0
    for t in texts:
        if t["role"] in ("label_en", "label_sup", "floor_en", "head_en_latin"):
            bad.append(("병기", "drawn.json texts", t["layer"], t["text"], "라벨·바닥 글에 영문/라틴 줄(%s)" % t["role"]))
    # 사양
    sp_items = spec_print_strings(load("out/spec.json"))
    bad += scan(sp_items, "spec.json")
    json.dump([{"layer": t.get("layer", ""), "role": t.get("role", ""), "font": t.get("font", ""), "text": t["text"]} for t in texts],
              open(os.path.join(ROOT, "out", "text-list.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if ALLOW_BI:
        bad = [b for b in bad if b[0] != "병기"]
    cnt = {k: sum(1 for b in bad if b[0] == k) for k in ("내부 지시", "수식어", "병기", "번역투")}
    print("검사한 글: drawn.json texts %d줄 · spec.json 인쇄 필드 %d개" % (len(texts), len(sp_items)))
    for b in bad:
        print("  위반 [%s] %s | %s | %r | %s" % b)
    print("위반 수  내부 지시 %d · 수식어 %d · 병기 %d · 번역투 %d" % (cnt["내부 지시"], cnt["수식어"], cnt["병기"], cnt["번역투"]))
    sys.exit(0 if not bad else 1)


if __name__ == "__main__":
    main()
