# -*- coding: utf-8 -*-
# 설계안 한 판을 만든다: 검사 → 사양 조립 → 미리보기 SVG → 다이어그램 PNG. 담당: global
# 사용: uv run --no-project --with pillow --with opencv-python-headless --with numpy python -I make.py [--no-render]
import os, sys, subprocess, time
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
py = sys.executable


def run(args):
    t = time.time()
    r = subprocess.run([py, "-I"] + args, capture_output=True, text=True)
    tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
    print("[%s] %.1fs %s" % (os.path.basename(args[0]), time.time() - t, " | ".join(tail)))
    if r.returncode != 0:
        print(r.stdout[-3000:], r.stderr[-3000:])
        sys.exit("실패: " + args[0])


run([os.path.join(HERE, "v2_check.py"), HERE, HERE])
run([os.path.join(HERE, "v2_build.py"), HERE, os.path.join(OUT, "spec.json")])
run([os.path.join(HERE, "v2_svg.py"), HERE, os.path.join(OUT, "preview.svg")])
if "--no-render" not in sys.argv:
    run([os.path.join(HERE, "render.py"), os.path.join(OUT, "diagram.png"), os.path.join(OUT, "spec.json"), os.path.join(HERE, "v2_hero_cluster_sil.npy")])
print("완료:", OUT)
