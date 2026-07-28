"""Derived, bounded compact checkpoints; never stores conversation content."""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,default=Path.cwd()); p.add_argument("--phase",choices=("pre-compact","post-compact"),required=True); a=p.parse_args(argv)
 d=a.root/"agents/runtime/session_checkpoints"; d.mkdir(parents=True,exist_ok=True); out=d/"latest.json"; out.write_text(json.dumps({"schema":"agent-runtime-compact-checkpoint/v1","phase":a.phase,"recorded_at":datetime.now(timezone.utc).isoformat(),"pointer_exists":(a.root/"agents/project/NEXT-SESSION-POINTER.yml").exists()})+"\n"); print(out); return 0
if __name__=="__main__": raise SystemExit(main())
