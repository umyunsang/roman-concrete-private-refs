# -*- coding: utf-8 -*-
# 워커 사본들에서 담당 파일만 모아 새 버전 폴더를 만든다(결정적 병합, 담당 밖 변경은 버리고 알린다).
# 사용: python merge.py --base wf/v16 --out wf/v17 --owners wf/OWNERS.json --work core=wf/work/v17.core arena=wf/work/v17.arena ...
import os, sys, json, shutil, filecmp, fnmatch, argparse

ap = argparse.ArgumentParser()
ap.add_argument("--base", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--owners", required=True)
ap.add_argument("--work", nargs="*", default=[])
ap.add_argument("--force", action="store_true", help="이미 있는 출력 폴더의 파일을 덮어쓴다")
a = ap.parse_args()
owners = json.load(open(a.owners, encoding="utf-8"))
if os.path.exists(a.out) and not a.force:
    sys.exit("출력 폴더가 이미 있습니다(덮어쓰려면 --force): " + a.out)
ign = shutil.ignore_patterns("__pycache__", "*.pyc", "*.png", "*.json.tmp")
shutil.copytree(a.base, a.out, ignore=ign, dirs_exist_ok=True)


def owned(pkg, fn):
    return any(fnmatch.fnmatch(fn, pat) for pat in owners[pkg]["files"])


report = []
for item in a.work:
    pkg, wdir = item.split("=", 1)
    if pkg not in owners:
        report.append("[%s] 알 수 없는 패키지 — 건너뜀" % pkg)
        continue
    if not os.path.isdir(wdir):
        report.append("[%s] 사본 폴더 없음 — 건너뜀: %s" % (pkg, wdir))
        continue
    taken, ignored = [], []
    for fn in sorted(os.listdir(wdir)):
        if not fn.endswith(".py"):
            continue
        src = os.path.join(wdir, fn)
        basef = os.path.join(a.base, fn)
        changed = (not os.path.exists(basef)) or (not filecmp.cmp(src, basef, shallow=False))
        if not changed:
            continue
        if owned(pkg, fn):
            shutil.copy2(src, os.path.join(a.out, fn))
            taken.append(fn + ("(새 파일)" if not os.path.exists(basef) else ""))
        else:
            ignored.append(fn)
    report.append("[%s] 반영: %s%s" % (pkg, ", ".join(taken) if taken else "없음",
                                     (" · 담당 밖이라 버린 변경: " + ", ".join(ignored)) if ignored else ""))
print("\n".join(report))
print("병합 완료:", a.out)
