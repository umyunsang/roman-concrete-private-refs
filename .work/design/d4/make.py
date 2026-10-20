# -*- coding: utf-8 -*-
# 설계안 한 판을 만든다: 사전 검사 → 사양 조립 → 내부 골격 SVG → 다이어그램 PNG(render, drawn.json 기록) → 사후 검사. 담당: global
# 사용: uv run --no-project --with pillow --with opencv-python-headless --with numpy python -I make.py [--no-render]
# 사전 검사가 필수 요소 누락(패널 6·L1~L9·네로 거상·R7·폰스 아일리우스 다리)으로 실패하면 진단을 남기려고 끝까지 실행한 뒤 종료 코드 1로 끝낸다.
# 사후 검사(v2_check.py --post)에서 실패가 1건이라도 있거나 drawn.json이 없으면 실패 항목을 출력하고 종료 코드 1로 끝낸다.
import os
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


def run(args, gate=True):
    t = time.time()
    r = subprocess.run([py, "-I"] + args, capture_output=True, text=True)
    tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
    print("[%s] %.1fs %s" % (os.path.basename(args[0]), time.time() - t, " | ".join(tail)))
    if r.returncode != 0 and gate:
        print(r.stdout[-3000:], r.stderr[-3000:])
        sys.exit("실패: " + args[0])
    return r


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
run([os.path.join(HERE, "v2_build.py"), HERE, os.path.join(OUT, "spec.json")])
run([os.path.join(HERE, "v2_svg.py"), HERE, os.path.join(OUT, "preview.svg")])
if "--no-render" in sys.argv:
    print("렌더·사후 검사 건너뜀(--no-render). 완료:", OUT)
    sys.exit(1 if pre_failed else 0)
for stale in (DRAWN, POST, os.path.join(OUT, "diagram.png")):          # 지난 판의 기록·그림으로 통과하거나 헷갈리지 않게 지운다
    if os.path.exists(stale):
        os.remove(stale)
run([os.path.join(HERE, "render.py"), os.path.join(OUT, "diagram.png"), os.path.join(OUT, "spec.json"), os.path.join(HERE, "v2_hero_cluster_sil.npy")])
if not os.path.exists(DRAWN):
    print("사후 검사 실패: render가 drawn.json을 쓰지 않았다 →", DRAWN)
    run([os.path.join(HERE, "v2_check.py"), "--post", DRAWN, POST, os.path.join(OUT, "spec.json")], gate=False)
    sys.exit(1)
r = run([os.path.join(HERE, "v2_check.py"), "--post", DRAWN, POST, os.path.join(OUT, "spec.json")], gate=False)
if r.returncode != 0:
    print("── 사후 검사 실패 항목 ──")
    print("\n".join(l for l in r.stdout.splitlines() if ("실패" in l or l.startswith("    "))))
    if r.stderr.strip():
        print(r.stderr[-2000:])
    print("결과:", POST)
    sys.exit(1)
if pre_failed:
    print("사전 검사 실패(필수 요소 누락) → 종료 코드 1. 결과:", PRE)
    sys.exit(1)
print("완료:", OUT, "· 사전 검사 통과:", PRE, "· 사후 검사 통과:", POST)
