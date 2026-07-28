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
  candidate=path.parent/(str(session_id).replace("/","_")+".json") if session_id else path
  data=json.loads((candidate if candidate.exists() else path).read_text(encoding="utf-8"))
  return "checkpoint: " + ", ".join(f"{k}={data[k]}" for k in ("session_id","active_task","active_task_set","rebootstrap_required") if k in data)[:800]
 except Exception: return "checkpoint: unavailable"
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,default=Path.cwd()); a=p.parse_args(argv); r=a.root
 try: event=json.load(sys.stdin)
 except Exception: event={}
 session_id=str(event.get("session_id") or "")[:80]; source=str(event.get("source") or event.get("trigger") or "unknown")[:80]
 checkpoint=r/"agents/runtime/session_checkpoints/latest.json"; lines=[f"agent-runtime source={source}",checkpoint_summary(checkpoint,session_id)]
 # These mutations must stay ordered; all remaining collectors are read-only.
 lines += [f"baseline: {run(r,'session_baseline.py')}",f"claim-reaper: {run(r,'claim_reaper_hook.py')}"]
 collectors=(("dashboard","session_dashboard.py"),("interrupted","interrupted_run_detector.py"),("resume","session_resume_check.py"))
 with ThreadPoolExecutor(max_workers=3) as pool:
  futures=[(label,pool.submit(run,r,script)) for label,script in collectors]
  lines += [f"{label}: {future.result()}" for label,future in futures]
 compound=next(iter(sorted((r/"agents/project").glob("*compound*"))),None)
 lines.append("compound: " + (compound.name if compound else "unavailable"))
 context="\n".join(lines)[:6000]
 print(json.dumps({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":context}},ensure_ascii=False)); return 0
if __name__=="__main__": raise SystemExit(main())
