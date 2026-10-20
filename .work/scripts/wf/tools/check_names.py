# -*- coding: utf-8 -*-
# 별표 import를 명시 import로 펼친 임시 사본에 pyflakes를 돌려, 실행되지 않은 분기의 미정의 이름까지 찾는다.
# 사용: uv run --no-project --with pillow --with pyflakes python -I check_names.py <버전 폴더>
import os, sys, shutil, subprocess, tempfile, importlib
d = os.path.abspath(sys.argv[1])
sys.path.insert(0, d)
sys.dont_write_bytecode = True
common = importlib.import_module("common")
names = sorted(n for n in dir(common) if not n.startswith("__"))
tmp = tempfile.mkdtemp(prefix="chk_", dir=os.environ.get("TMPDIR"))
for fn in os.listdir(d):
    if not fn.endswith(".py"):
        continue
    src = open(os.path.join(d, fn), encoding="utf-8").read()
    src = src.replace("from common import *", "from common import " + ", ".join(names))
    open(os.path.join(tmp, fn), "w", encoding="utf-8").write(src)
r = subprocess.run([sys.executable, "-m", "pyflakes"] + sorted(os.path.join(tmp, f) for f in os.listdir(tmp)), capture_output=True, text=True)
bad = [ln.replace(tmp + "/", "") for ln in r.stdout.splitlines() if "undefined name" in ln]
print("\n".join(bad) if bad else "미정의 이름 없음")
shutil.rmtree(tmp)
sys.exit(1 if bad else 0)
