"""Derived, bounded compact checkpoints; never stores conversation content."""
from __future__ import annotations
import argparse,json,os,tempfile,sys,subprocess,re
from datetime import datetime,timezone
from pathlib import Path
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,default=Path.cwd()); p.add_argument("--phase",choices=("pre-compact","post-compact"),required=True); a=p.parse_args(argv)
 try:event=json.load(sys.stdin)
 except Exception:event={}
 d=a.root/"agents/runtime/session_checkpoints"; d.mkdir(parents=True,exist_ok=True); out=d/"latest.json"; sid=re.sub(r"[^A-Za-z0-9_-]","_",str(event.get("session_id") or "default"))[:80]; per=d/f"{sid}.json"
 git=lambda *x: subprocess.run(["git","-C",str(a.root),*x],capture_output=True,text=True).stdout.strip()
 data={"schema":"agent-runtime-compact-checkpoint/v1","session_id":sid,"trigger":str(event.get("trigger") or "unknown")[:80],"phase":a.phase,"recorded_at":datetime.now(timezone.utc).isoformat(),"pointer_exists":(a.root/"agents/project/NEXT-SESSION-POINTER.yml").exists(),"git":{"branch":git("branch","--show-current"),"head":git("rev-parse","--short","HEAD"),"dirty_count":len(git("status","--porcelain").splitlines())},"rebootstrap_required":a.phase=="post-compact"}
 if a.phase=="post-compact" and out.exists():
  try:data.update(json.loads(out.read_text(encoding="utf-8")))
  except Exception:pass
  data.update({"phase":a.phase,"rebootstrap_required":True,"recorded_at":datetime.now(timezone.utc).isoformat()})
 for target in (per,out):
  fd,tmp=tempfile.mkstemp(dir=d,prefix=".checkpoint-"); os.write(fd,(json.dumps(data)+"\n").encode()); os.fsync(fd); os.close(fd); os.replace(tmp,target)
 print("{}"); return 0
if __name__=="__main__": raise SystemExit(main())
