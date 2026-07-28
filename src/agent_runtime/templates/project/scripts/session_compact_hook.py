"""Derived, bounded compact checkpoints; never stores conversation content."""
from __future__ import annotations
import argparse,json,os,tempfile
from datetime import datetime,timezone
from pathlib import Path
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,default=Path.cwd()); p.add_argument("--phase",choices=("pre-compact","post-compact"),required=True); a=p.parse_args(argv)
 d=a.root/"agents/runtime/session_checkpoints"; d.mkdir(parents=True,exist_ok=True); out=d/"latest.json"; data={"schema":"agent-runtime-compact-checkpoint/v1","phase":a.phase,"recorded_at":datetime.now(timezone.utc).isoformat(),"pointer_exists":(a.root/"agents/project/NEXT-SESSION-POINTER.yml").exists(),"rebootstrap_required":a.phase=="post-compact"}
 fd,tmp=tempfile.mkstemp(dir=d,prefix=".checkpoint-"); os.write(fd,(json.dumps(data)+"\n").encode()); os.close(fd); os.replace(tmp,out); print(out); return 0
if __name__=="__main__": raise SystemExit(main())
