# -*- coding: utf-8 -*-
"""Codex 비평가 실행기(적대적 리뷰는 Codex, 수정은 Opus — 사용자 지시 2026-10-19 02:17).

흐름: 판정 지시문 작성 → codex-companion task(백그라운드, gpt-6.1-sol 또는 gpt-6-luna)
     → status --wait 반복 → result → 판정 JSON 추출·형식 검사·이미지 확인 검사 → 실패하면 sol로 1회 재시도.
사용:
  python3 -I codex_critic.py start --ver 2 --lens bench --mode full  [--model gpt-6.1-sol] [--effort high] [--prev <직전 판정 JSON>]
  python3 -I codex_critic.py wait  --ver 2 --lens bench               (최대 540초 기다린다. 끝나면 요약 JSON, 아니면 {"state": "running"})
출력은 항상 한 줄 JSON이다.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/um-yunsang/roman-concrete-private-refs"
DZ = ROOT + "/.work/design"
CX = DZ + "/codex"
RD = DZ + "/review/codex"
COMP = "/Users/um-yunsang/.claude/plugins/cache/openai-codex/codex/1.0.6/scripts/codex-companion.mjs"
SOL, LUNA = "gpt-6.1-sol", "gpt-6-luna"
PKGS = ("map", "panels", "render", "global")
GRADES = ("C", "B", "A", "AA", "AAA")
SEVS = ("blocker", "major", "moderate", "minor")

FULL = """
## 절차(전체 판정)
1) 기준선을 읽는다.
2) 다이어그램 전체를 view_image로 보고, 필요한 곳을 잘라 확대해 view_image로 본다.
3) 사양·검사 결과로 수치를 확인한다.
4) 근거 자료는 필요한 절만 읽는다.
5) 결함을 찾아 같은 원인끼리 묶고 등급을 매긴다.
목표 시간 20분.
"""
QUICK = """
## 절차(회귀 확인)
- 직전 판(d{NPREV})에서 당신은 AAA를 줬다.
- 이번 판(d{N})에서는 당신 렌즈의 회귀만 확인한다.
  - 이전 판과 이번 판의 다이어그램을 view_image로 보고 같은 자리를 비교한다.
  - 변경 기록(CHANGES.md)을 본다.
- 새 결함이 없으면 AAA를 유지한다. 있으면 등급을 낮추고 적는다.
목표 시간 10분.
"""


def out(d):
    print(json.dumps(d, ensure_ascii=False))


def comp(args, timeout=None):
    r = subprocess.run(["node", COMP] + args, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def paths(ver, lens):
    base = "%s/d%s_%s" % (RD, ver, lens)
    return {"prompt": base + "_prompt.md", "state": base + ".state.json", "raw": base + "_raw.txt",
            "out": base + ".json", "crop": "%s/review/d%s_%s_codex" % (DZ, ver, lens)}


def build_prompt(ver, lens, mode, prev_file, note):
    L = json.load(open(CX + "/lenses.json", encoding="utf-8"))[lens]
    P = paths(ver, lens)
    s = open(CX + "/critic_common.md", encoding="utf-8").read()
    s += "\n## 당신의 판정 초점\n" + L["focus"] + "\n"
    s += QUICK if mode == "quick" else FULL
    if prev_file and os.path.exists(prev_file):
        try:
            pv = json.load(open(prev_file, encoding="utf-8"))
            s += "\n## 직전 판정(당신)\n- 등급 %s(%s). 그때 지적이 이번 판에서 고쳐졌는지 하나씩 확인한다.\n" % (pv.get("grade"), pv.get("score"))
            for i in pv.get("issues", [])[:30]:
                s += "  - %s: %s\n" % (i.get("target", ""), str(i.get("issue", ""))[:220])
        except Exception:
            pass
    if note:
        s += "\n## 다시 판정하는 이유\n" + note + "\n"
    rep = {"{N}": str(ver), "{NPREV}": str(int(ver) - 1), "{LENS_NAME}": L["name"], "{LENS_KEY}": lens,
           "{OUT_JSON}": P["out"], "{CROP_DIR}": P["crop"]}
    for k, v in rep.items():
        s = s.replace(k, v)
    return s


def start(ver, lens, mode, model, effort, prev_file, attempt=1, note=""):
    P = paths(ver, lens)
    os.makedirs(RD, exist_ok=True)
    os.makedirs(P["crop"], exist_ok=True)
    if os.path.exists(P["out"]):
        os.remove(P["out"])
    open(P["prompt"], "w", encoding="utf-8").write(build_prompt(ver, lens, mode, prev_file, note))
    args = ["task", "--background", "--write", "--model", model, "--prompt-file", P["prompt"], "--json", "--cwd", ROOT]
    if effort:
        args += ["--effort", effort]
    rc, so, se = comp(args, timeout=180)
    try:
        job = json.loads(so)["jobId"]
    except Exception:
        out({"state": "failed", "reason": "Codex 작업 시작 실패", "stderr": (se or so)[-400:]})
        return
    json.dump({"ver": ver, "lens": lens, "mode": mode, "model": model, "effort": effort, "job": job,
               "attempt": attempt, "started": time.time(), "prev": prev_file}, open(P["state"], "w"))
    out({"state": "running", "job": job, "model": model, "attempt": attempt})


def extract(raw):
    m = re.search(r"<<<VERDICT_JSON\s*(\{.*\})\s*VERDICT_JSON>>>", raw, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def normalize(v):
    if not isinstance(v, dict) or v.get("grade") not in GRADES:
        return None
    try:
        v["score"] = float(v.get("score"))
    except Exception:
        return None
    iss = v.get("issues")
    if not isinstance(iss, list):
        return None
    clean = []
    for i in iss:
        if not isinstance(i, dict):
            continue
        if not all(k in i for k in ("severity", "pkg", "target", "issue", "evidence", "fix")):
            continue
        if i["pkg"] not in PKGS:
            i["pkg"] = "global"
        if i["severity"] not in SEVS:
            i["severity"] = "moderate"
        clean.append(i)
    v["issues"] = clean
    v["summary"] = str(v.get("summary", ""))
    return v


def wait(ver, lens, budget=540):
    P = paths(ver, lens)
    if not os.path.exists(P["state"]):
        try:
            v = normalize(json.load(open(P["out"], encoding="utf-8")))
        except Exception:
            v = None
        if v is not None and v.get("image_checked") is True:
            out({"state": "done", "grade": v["grade"], "score": v["score"], "n": len(v["issues"]), "file": P["out"], "image_checked": True, "model": "reused", "attempt": 0})
            return
        out({"state": "failed", "reason": "시작 기록 없음(start 먼저)"})
        return
    st = json.load(open(P["state"]))
    t0 = time.time()
    status = None
    while time.time() - t0 < budget:
        left = max(5, int(budget - (time.time() - t0)))
        try:
            rc, so, se = comp(["status", st["job"], "--wait", "--timeout-ms", str(left * 1000), "--json"], timeout=left + 60)
            snap = json.loads(so)
            job = snap.get("job", snap)
            status = job.get("status")
        except Exception:
            status = None
            time.sleep(5)
        if status in ("completed", "failed", "cancelled", "error"):
            break
    if status not in ("completed", "failed", "cancelled", "error"):
        out({"state": "running", "job": st["job"], "elapsed_s": int(time.time() - st["started"])})
        return
    rc, raw, se = comp(["result", st["job"]], timeout=180)
    open(P["raw"], "w", encoding="utf-8").write(raw or se or "")
    v = None
    if os.path.exists(P["out"]):
        try:
            v = normalize(json.load(open(P["out"], encoding="utf-8")))
        except Exception:
            v = None
    if v is None:
        v = normalize(extract(raw or ""))
    if v is not None and v.get("image_checked") is True:
        json.dump(v, open(P["out"], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        out({"state": "done", "grade": v["grade"], "score": v["score"], "n": len(v["issues"]), "file": P["out"],
             "image_checked": True, "model": st["model"], "attempt": st["attempt"]})
        return
    if st["attempt"] < 2:
        why = "판정 JSON이 없거나 형식이 틀렸다" if v is None else "다이어그램을 view_image로 보지 않았다(image_checked가 true가 아님)"
        start(ver, lens, st["mode"], SOL, None, st.get("prev"), attempt=2,
              note="직전 시도에서 %s. 이번에는 반드시 view_image로 다이어그램을 열고, 출력 형식(파일 저장 + 표시 사이 JSON)을 지켜라." % why)
        return
    out({"state": "failed", "reason": "판정 JSON 없음 또는 이미지 미확인(2회)", "raw": P["raw"]})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["start", "wait"])
    ap.add_argument("--ver", required=True)
    ap.add_argument("--lens", required=True)
    ap.add_argument("--mode", default="full", choices=["full", "quick"])
    ap.add_argument("--model", default=None)
    ap.add_argument("--effort", default=None)
    ap.add_argument("--prev", default=None)
    ap.add_argument("--reuse", action="store_true", help="이미 유효한 판정(image_checked)이 있으면 다시 돌리지 않는다")
    a = ap.parse_args()
    if a.cmd == "start":
        if a.reuse:
            P = paths(a.ver, a.lens)
            try:
                v = normalize(json.load(open(P["out"], encoding="utf-8")))
            except Exception:
                v = None
            if v is not None and v.get("image_checked") is True:
                out({"state": "done", "grade": v["grade"], "score": v["score"], "n": len(v["issues"]), "file": P["out"],
                     "image_checked": True, "model": "reused", "attempt": 0})
                sys.exit(0)
            if os.path.exists(P["state"]):        # 이미 돌고 있는 작업이면 다시 시작하지 않고 기다리게 한다
                try:
                    st = json.load(open(P["state"]))
                    rc, so, se = comp(["status", st["job"], "--json"], timeout=120)
                    snap = json.loads(so); job = snap.get("job", snap)
                    if job.get("status") not in ("completed", "failed", "cancelled", "error"):
                        out({"state": "running", "job": st["job"], "model": st.get("model"), "attempt": st.get("attempt", 1), "reused": True})
                        sys.exit(0)
                except SystemExit:
                    raise
                except Exception:
                    pass
        model = a.model or (LUNA if a.mode == "quick" else SOL)
        start(a.ver, a.lens, a.mode, model, a.effort, a.prev)
    else:
        wait(a.ver, a.lens)
