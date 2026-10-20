# -*- coding: utf-8 -*-
# 설계안 한 판을 만든다: 사전 검사 → 사양 조립 → 내부 골격 SVG → 다이어그램 PNG(render, drawn.json 기록) → 사후 검사. 담당: global
# 사용: uv run --no-project --with pillow --with opencv-python-headless --with numpy python -I make.py [--no-render] [--info [--sil <sil.json>]] [--selftest]
# 사전 검사가 필수 요소 누락(패널 6·L1~L9·네로 거상·R7·폰스 아일리우스 다리)으로 실패하면 진단을 남기려고 끝까지 실행한 뒤 종료 코드 1로 끝낸다.
# 사전 기준선 8절 판정(baseline_8)은 기록하고 출력한다. 같은 내용을 사후 ⑱·⑲·⑳이 그린 결과로 판정한다.
# 사후 검사(v2_check.py --post)에서 실패가 1건이라도 있거나 drawn.json이 없으면 실패 항목을 출력하고 종료 코드 1로 끝낸다.
# d5 선택 항목:
#   --info      정보 층 두 번째 실행(render.py INFO_ONLY=1 → out/info/info_layer.png·info_check.json). b{N} sil.json(Blender 실루엣·앵커)이 생긴 뒤에 쓴다.
#               사후 ⑰(지시선 끝–앵커 ≤ 0.5mm, 라벨 블록–실루엣 겹침 0)이 판정한다. 기본 sil.json = .work/blender/rounds/b{N}/sil.json(N = 이 폴더의 d 번호)
#   --sil PATH  sil.json 경로를 바꾼다(render에 환경 변수 SIL_JSON으로 넘긴다)
#   --selftest  회귀 시험만 돌린다(v2_check.py --selftest: d4 사양 → 8.1·8.2 새 검사 실패, d5 사양 → 통과)
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
py = sys.executable
DRAWN = os.path.join(OUT, "drawn.json")
POST = os.path.join(OUT, "post_check.json")
PRE = os.path.join(HERE, "v2_check.json")
SPEC = os.path.join(OUT, "spec.json")
INFO_DIR = os.path.join(OUT, "info")
INFO_PNG = os.path.join(INFO_DIR, "info_layer.png")
INFO_CHECK = os.path.join(INFO_DIR, "info_check.json")
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))       # .work/design/<판>/ 또는 .work/design/work/<사본>/ → 저장소 뿌리를 아래에서 다시 찾는다


def _root():
    p = HERE
    for _ in range(6):
        if os.path.isdir(os.path.join(p, ".work")):
            return p
        p = os.path.dirname(p)
    return ROOT


def run(args, gate=True, env=None):
    t = time.time()
    r = subprocess.run([py, "-I"] + args, capture_output=True, text=True, env=(dict(os.environ, **env) if env else None))
    tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
    print("[%s] %.1fs %s" % (os.path.basename(args[0]), time.time() - t, " | ".join(tail)))
    if r.returncode != 0 and gate:
        print(r.stdout[-3000:], r.stderr[-3000:])
        sys.exit("실패: " + args[0])
    return r


def _post_summary():
    """사후 검사 결과(⑪ 위계·⑱~⑳ 8절)를 spec.json에 적는다: 예정 상자가 아니라 그린 외곽 상자 기준의 최종 판정"""
    try:
        post = json.load(open(POST, encoding="utf-8"))
        spec = json.load(open(SPEC, encoding="utf-8"))
    except Exception as e:  # 기록용이라 실패해도 실행을 막지 않는다
        print("사후 요약 기록 건너뜀:", e)
        return
    rr = {r_["no"]: r_ for r_ in post.get("rules", [])}
    h = rr.get("⑪", {})
    spec.setdefault("hierarchy", {})["post_summary"] = {
        "source": POST, "pass": h.get("pass"), "fails": h.get("fails", [])[:12],
        **{k: (h.get("info") or {}).get(k) for k in ("hero_group_box", "hero_group_area", "hero_building_box", "hero_plaza_box", "landmark_median_drawn",
                                                       "hero_over_median", "hero_over_landmark_max", "L5_drawn_area", "building_sil_mm2", "building_sil_over_max_other",
                                                       "landmark_areas_drawn", "basis")}}
    spec.setdefault("meta", {}).setdefault("baseline_8", {})["post_result"] = {
        no: {"pass": rr.get(no, {}).get("pass"), "fails": rr.get(no, {}).get("fails", [])[:8]} for no in ("⑱", "⑲", "⑳")}
    spec["meta"]["baseline_8"]["post_result"]["⑰ 정보 층"] = {"pass": rr.get("⑰", {}).get("pass"), "info": rr.get("⑰", {}).get("info")}
    json.dump(spec, open(SPEC, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


argv = sys.argv[1:]
if "--selftest" in argv:
    r = run([os.path.join(HERE, "v2_check.py"), "--selftest"], gate=False)
    print(r.stdout[-2500:])
    sys.exit(r.returncode)
INFO = "--info" in argv
SIL = None
if "--sil" in argv and argv.index("--sil") + 1 < len(argv):
    SIL = os.path.abspath(argv[argv.index("--sil") + 1])
elif INFO:
    m = re.search(r"d(\d+)", os.path.basename(HERE))
    if m:
        SIL = os.path.join(_root(), ".work", "blender", "rounds", "b%s" % m.group(1), "sil.json")

if os.path.exists(PRE):                      # 지난 판의 사전 검사 결과로 조립하지 않게 지운다
    os.remove(PRE)
r_pre = run([os.path.join(HERE, "v2_check.py"), HERE, HERE], gate=False)
if not os.path.exists(PRE):                  # 검사 자체가 깨졌다(결과 없음) → 바로 멈춘다
    print(r_pre.stdout[-3000:], r_pre.stderr[-3000:])
    sys.exit("실패: v2_check.py(사전 검사 결과 없음)")
pre_failed = r_pre.returncode != 0
if pre_failed:
    print("── 사전 검사 실패(필수 요소 누락) — 진단을 남기려고 계속 실행한다 ──")
    print("\n".join(l for l in r_pre.stdout.splitlines() if "사전 검사 실패" in l))
print("\n".join(l for l in r_pre.stdout.splitlines() if ("8절" in l or "사전 위계" in l)))
run([os.path.join(HERE, "v2_build.py"), HERE, SPEC])
run([os.path.join(HERE, "v2_svg.py"), HERE, os.path.join(OUT, "preview.svg")])
if "--no-render" in argv:
    print("렌더·사후 검사 건너뜀(--no-render). 완료:", OUT)
    sys.exit(1 if pre_failed else 0)
for stale in (DRAWN, POST, os.path.join(OUT, "diagram.png")) + ((INFO_PNG, INFO_CHECK, os.path.join(INFO_DIR, "drawn.json")) if INFO else ()):
    if os.path.exists(stale):                # 지난 판의 기록·그림으로 통과하거나 헷갈리지 않게 지운다
        os.remove(stale)
run([os.path.join(HERE, "render.py"), os.path.join(OUT, "diagram.png"), SPEC, os.path.join(HERE, "v2_hero_cluster_sil.npy")])
info_failed = False
if INFO:                                     # 정보 층만(지도 그림은 Blender): out/info/에 쓴다(본판 drawn.json은 건드리지 않는다)
    os.makedirs(INFO_DIR, exist_ok=True)
    env = {"INFO_ONLY": "1", "INFO_CHECK": INFO_CHECK}
    if SIL and os.path.exists(SIL):
        env["SIL_JSON"] = SIL
    else:
        print("정보 층: sil.json 없음(%s) — 앵커 맞춤 없이 정보 층만 그린다" % SIL)
    run([os.path.join(HERE, "render.py"), INFO_PNG, SPEC, os.path.join(HERE, "v2_hero_cluster_sil.npy")], env=env)
    if not os.path.exists(INFO_CHECK):
        info_failed = True
        print("정보 층 실패: render INFO_ONLY가 info_check.json을 쓰지 않았다 →", INFO_CHECK)
post_args = [os.path.join(HERE, "v2_check.py"), "--post", DRAWN, POST, SPEC] + (["--info", INFO_CHECK] if INFO and os.path.exists(INFO_CHECK) else [])
if not os.path.exists(DRAWN):
    print("사후 검사 실패: render가 drawn.json을 쓰지 않았다 →", DRAWN)
    run(post_args, gate=False)
    sys.exit(1)
r = run(post_args, gate=False)
_post_summary()
if r.returncode != 0:
    print("── 사후 검사 실패 항목 ──")
    print("\n".join(l for l in r.stdout.splitlines() if ("실패" in l or l.startswith("    "))))
    if r.stderr.strip():
        print(r.stderr[-2000:])
    print("결과:", POST)
    sys.exit(1)
if pre_failed or info_failed:
    print("사전 검사 실패(필수 요소 누락) 또는 정보 층 기록 없음 → 종료 코드 1. 결과:", PRE)
    sys.exit(1)
print("완료:", OUT, "· 사전 검사 통과:", PRE, "· 사후 검사 통과:", POST, ("· 정보 층: " + INFO_PNG) if INFO else "")
