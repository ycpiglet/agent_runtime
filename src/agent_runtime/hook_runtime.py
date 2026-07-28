"""Allowlisted portable dispatcher; blocking hook streams are transparent."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
SCRIPTS={"session-start":"scripts/session_start_hook.py","pre-compact":"scripts/session_compact_hook.py","post-compact":"scripts/session_compact_hook.py","prompt-submit":"scripts/taskset_prompt_hook.py","stop-owner":"scripts/stop_hook_owner_governance.py","stop-closure":"scripts/stop_hook_closure_gate.py","stop-dirty":"scripts/stop_hook_dirty_intake.py","posttool-owner-doc":"scripts/owner_doc_format_gate.py"}
ADVISORY={"session-start","pre-compact","post-compact"}
def root_for(cwd:str)->Path:
 p=Path(cwd or ".").resolve()
 try:return Path(subprocess.run(["git","-C",str(p),"rev-parse","--show-toplevel"],capture_output=True,text=True,check=True).stdout.strip())
 except Exception:return p
def main(argv=None):
 mode=(argv or sys.argv[1:])[0] if (argv or sys.argv[1:]) else ""
 if mode not in SCRIPTS:return 2
 raw=sys.stdin.read();
 try:event=json.loads(raw or "{}")
 except Exception:event={}
 root=root_for(str(event.get("cwd") or "")); args=[sys.executable,str(root/SCRIPTS[mode])]
 if mode=="session-start":args += ["--root",str(root)]
 if mode in {"pre-compact","post-compact"}:args += ["--root",str(root),"--phase",mode]
 if mode=="posttool-owner-doc":args += ["--manifest","owner-docs.yml"]
 try:r=subprocess.run(args,input=raw,text=True,capture_output=True,cwd=root)
 except Exception:
  if mode in ADVISORY: print("{}"); return 0
  return 1
 if mode in ADVISORY:
  print(r.stdout if r.returncode==0 and r.stdout.strip() else "{}")
  return 0
 sys.stdout.write(r.stdout); sys.stderr.write(r.stderr); return r.returncode
if __name__=="__main__":raise SystemExit(main())
