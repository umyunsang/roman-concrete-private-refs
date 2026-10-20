# -*- coding: utf-8 -*-
"""Codex 비평가 여러 명을 한 번에 돌린다(동시 par명). 중계 에이전트 하나가 이 명령을 반복 실행하면 된다.
사용: python3 -I codex_batch.py run --ver N --lenses bench,style,... [--quick hero,city] [--prev-ver M] [--par 7] [--budget 510]
- 처음 실행: 시작 안 된 렌즈를 par명까지 시작한다.
- 다시 실행: 끝난 작업을 거두고(검사·재시도 포함) 빈자리에 다음 렌즈를 시작한다. budget초 동안 반복한다.
- 출력은 한 줄 JSON: {"state": "done"|"running", "results": {렌즈: {...}}, "pending": [...]}
"""
import argparse
import json
import os
import subprocess
import sys
import time

ROOT = "/Users/um-yunsang/roman-concrete-private-refs"
BZ = ROOT + "/.work/blender"
RD = BZ + "/review/codex"
CRIT = BZ + "/tools/codex_critic.py"
COMP = "/Users/um-yunsang/.claude/plugins/cache/openai-codex/codex/1.0.6/scripts/codex-companion.mjs"


def sh(args, timeout=600):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout, cwd=ROOT)
    return r.stdout.strip()


def last_json(txt):
    for line in reversed(txt.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except Exception:
                pass
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run"])
    ap.add_argument("--ver", required=True)
    ap.add_argument("--lenses", required=True)
    ap.add_argument("--quick", default="")
    ap.add_argument("--prev-ver", default=None)
    ap.add_argument("--par", type=int, default=7)
    ap.add_argument("--budget", type=int, default=510)
    a = ap.parse_args()
    lenses = [x for x in a.lenses.split(",") if x]
    quick = set(x for x in a.quick.split(",") if x)
    os.makedirs(RD, exist_ok=True)
    stp = "%s/b%s_batch.json" % (RD, a.ver)
    st = json.load(open(stp)) if os.path.exists(stp) else {}
    t0 = time.time()
    while True:
        running = [k for k in lenses if st.get(k, {}).get("state") == "running"]
        # 끝난 작업 거두기
        for k in running:
            sp = "%s/b%s_%s.state.json" % (RD, a.ver, k)
            try:
                sj = json.load(open(sp))
                job = sj["job"]
                # 판정 JSON이 이번 시작 뒤에 저장됐으면 끝난 것으로 본다(status 출력 형식에 기대지 않음)
                outp = "%s/b%s_%s.json" % (RD, a.ver, k)
                if os.path.exists(outp) and os.path.getmtime(outp) > float(sj.get("started", 0)):
                    status = "completed"
                else:
                    snap = last_json(sh(["node", COMP, "status", job, "--json"], 120))
                    status = (snap.get("job") or snap).get("status")
            except Exception:
                status = None
            if status in ("completed", "failed", "cancelled", "error"):
                res = last_json(sh([sys.executable, "-I", CRIT, "wait", "--ver", str(a.ver), "--lens", k], 900))
                if res.get("state") == "done":
                    st[k] = {"state": "done", "grade": res.get("grade"), "score": res.get("score"), "n": res.get("n"), "file": res.get("file"), "model": res.get("model")}
                elif res.get("state") == "failed":
                    st[k] = {"state": "failed", "reason": res.get("reason")}
                else:
                    st[k] = {"state": "running"}       # 재시도로 다시 시작됨
        # 빈자리에 시작
        running = [k for k in lenses if st.get(k, {}).get("state") == "running"]
        todo = [k for k in lenses if k not in st]
        while todo and len(running) < a.par:
            k = todo.pop(0)
            mode = "quick" if k in quick else "full"
            args = [sys.executable, "-I", CRIT, "start", "--ver", str(a.ver), "--lens", k, "--mode", mode]
            if a.prev_ver:
                prev = "%s/b%s_%s.json" % (RD, a.prev_ver, k)
                if os.path.exists(prev):
                    args += ["--prev", prev]
            res = last_json(sh(args, 300))
            st[k] = {"state": "running"} if res.get("state") == "running" else {"state": "failed", "reason": res.get("reason", "시작 실패")}
            running.append(k)
        json.dump(st, open(stp, "w"), ensure_ascii=False, indent=1)
        pending = [k for k in lenses if st.get(k, {}).get("state") not in ("done", "failed")]
        if not pending or time.time() - t0 > a.budget:
            break
        time.sleep(30)
    pending = [k for k in lenses if st.get(k, {}).get("state") not in ("done", "failed")]
    print(json.dumps({"state": "done" if not pending else "running", "results": {k: st.get(k) for k in lenses}, "pending": pending}, ensure_ascii=False))


if __name__ == "__main__":
    main()
