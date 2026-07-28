"""Portable allowlisted dispatcher for tracked Codex hooks."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ALLOWED = {
 "session-start": "scripts/session_start_hook.py", "pre-compact": "scripts/session_compact_hook.py",
 "post-compact": "scripts/session_compact_hook.py", "prompt-submit": "scripts/taskset_prompt_hook.py",
 "stop-owner": "scripts/stop_hook_owner_governance.py", "stop-closure": "scripts/stop_hook_closure_gate.py",
 "stop-dirty": "scripts/stop_hook_dirty_intake.py", "posttool-owner-doc": "scripts/owner_doc_format_gate.py",
}
def main(argv=None):
 mode=(argv or sys.argv[1:])[0] if (argv or sys.argv[1:]) else ""
 if mode not in ALLOWED: return 2
 try: event=json.load(sys.stdin)
 except Exception: event={}
 root=Path(event.get("cwd") or ".").resolve(); script=root/ALLOWED[mode]
 if not script.exists():
  if mode in {"session-start","pre-compact","post-compact"}: print(json.dumps({"hookSpecificOutput":{"additionalContext":"agent-runtime continuity hook unavailable"}})); return 0
  return 0
 args=[sys.executable,str(script),"--root",str(root)]
 if mode in {"pre-compact","post-compact"}: args += ["--phase",mode]
 result=subprocess.run(args,input=json.dumps(event),text=True,capture_output=True,check=False)
 if mode=="session-start":
  context=(result.stdout or "")[-6000:]
  print(json.dumps({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":context}}))
 return 0 if mode in {"session-start","pre-compact","post-compact"} else result.returncode
if __name__=="__main__": raise SystemExit(main())
