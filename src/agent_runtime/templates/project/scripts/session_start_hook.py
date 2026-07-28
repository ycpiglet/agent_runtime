"""Bounded, non-blocking SessionStart continuity summary."""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,default=Path.cwd()); a=p.parse_args(argv); r=a.root
 checkpoint=r/"agents/runtime/session_checkpoints/latest.json"; pointer=r/"agents/project/NEXT-SESSION-POINTER.yml"
 lines=[f"agent-runtime host={r}",f"pointer={'present' if pointer.exists() else 'absent'}",f"compact_checkpoint={'present' if checkpoint.exists() else 'absent'}"]
 for label, script in (("baseline","session_baseline.py"),("claims","claim_reaper_hook.py"),("dashboard","session_dashboard.py"),("interrupted","interrupted_run_detector.py"),("resume","session_resume_check.py"),("compound","kedb_search.py")):
  try:
   out=subprocess.run([sys.executable,str(r/"scripts"/script),"--root",str(r)],capture_output=True,text=True,timeout=8).stdout.strip().splitlines()
   lines.append(f"{label}: {(out[0] if out else 'no data')[:400]}")
  except Exception: lines.append(f"{label}: unavailable")
 print("\n".join(lines[:8])); return 0
if __name__=="__main__": raise SystemExit(main())
