"""Bounded, non-blocking SessionStart continuity summary."""
from __future__ import annotations
import argparse,json,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
def run(root, script, *, root_arg=True):
 try:
  args=[sys.executable,str(root/"scripts"/script)]+(["--root",str(root)] if root_arg else [])
  result=subprocess.run(args,capture_output=True,text=True,timeout=8,cwd=root)
  text=(result.stdout or result.stderr).strip().replace("\n"," ")
  return text[:500] if result.returncode == 0 and text else "unavailable"
 except Exception: return "unavailable"
def checkpoint_summary(path, session_id):
 try:
  normalized=__import__("re").sub(r"[^A-Za-z0-9_-]","_",str(session_id))[:80]
  candidate=path.parent/(normalized+".json") if session_id else path
  data=json.loads((candidate if candidate.exists() else path).read_text(encoding="utf-8"))
  fields=("session_id","active_task","active_task_set","rebootstrap_required")
  active=", ".join(str(item.get("task_id") or item.get("task") or item.get("claim_id")) for item in data.get("active_claims",[])[:4] if isinstance(item,dict))
  return ("checkpoint: " + ", ".join(f"{k}={data[k]}" for k in fields if k in data) + (f", active_work={active}" if active else ""))[:800]
 except Exception: return "checkpoint: unavailable"
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,default=Path.cwd()); a=p.parse_args(argv); r=a.root
 try: event=json.load(sys.stdin)
 except Exception: event={}
 session_id=str(event.get("session_id") or "")[:80]; source=str(event.get("source") or event.get("trigger") or "unknown")[:80]
 checkpoint=r/"agents/runtime/session_checkpoints/latest.json"; lines=[f"agent-runtime host={r} source={source}",checkpoint_summary(checkpoint,session_id)]
 lines += [f"baseline: {run(r,'session_baseline.py')}",f"claim-reaper: {run(r,'claim_reaper_hook.py')}"]
 collectors=(("dashboard","session_dashboard.py"),("interrupted","interrupted_run_detector.py"),("resume","session_resume_check.py"))
 with ThreadPoolExecutor(max_workers=3) as pool:
  futures=[(label,pool.submit(run,r,script)) for label,script in collectors]
  lines += [f"{label}: {future.result()}" for label,future in futures]
 compound=r/"agents/lead_engineer/compound_log.md"
 try:
  headings=[line.strip()[3:] for line in compound.read_text(encoding="utf-8")[:12000].splitlines() if line.startswith("## COMPOUND-")]
  lines.append(f"compound: count={len(headings)}, latest={headings[-1][:240] if headings else 'none'}")
 except OSError: lines.append("compound: unavailable")
 context="\n".join(lines)[:6000]
 print(json.dumps({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":context}},ensure_ascii=False)); return 0
if __name__=="__main__": raise SystemExit(main())
