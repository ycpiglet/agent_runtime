"""Derived, bounded compact checkpoints; never stores conversation content."""
from __future__ import annotations
import argparse,json,os,tempfile,sys,subprocess,re
from datetime import datetime,timezone
from pathlib import Path
ACTIVE={"assigned","claimed","in_progress","review","waiting_review","working"}
def pointer_state(path: Path) -> dict:
 data={"pointer_exists":path.exists()}
 if not path.exists(): return data
 try: text=path.read_text(encoding="utf-8")[:8000]
 except OSError: return data
 for field in ("active_task","active_task_set"):
  match=re.search(rf"^\s*{field}\s*:\s*['\"]?([^\n'\"]+)", text, re.M)
  if match: data[field]=match.group(1).strip()[:240]
 return data
def active_claims(root: Path) -> list[dict]:
 found=[]
 for path in sorted((root/"agents/runtime/task_claims").glob("*.json"))[:100]:
  try: claim=json.loads(path.read_text(encoding="utf-8"))
  except Exception: continue
  if isinstance(claim,dict) and str(claim.get("status","")).lower() in ACTIVE:
   found.append({key:str(claim.get(key, ""))[:240] for key in ("claim_id","task","branch") if claim.get(key)})
  if len(found)>=12: break
 return found
def atomic_json(path: Path, data: dict) -> None:
 fd,tmp=tempfile.mkstemp(dir=path.parent,prefix=".checkpoint-")
 try:
  with os.fdopen(fd,"w",encoding="utf-8") as handle:
   json.dump(data,handle,ensure_ascii=False); handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp): os.unlink(tmp)
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,default=Path.cwd()); p.add_argument("--phase",choices=("pre-compact","post-compact"),required=True); a=p.parse_args(argv)
 try:event=json.load(sys.stdin)
 except Exception:event={}
 d=a.root/"agents/runtime/session_checkpoints"; d.mkdir(parents=True,exist_ok=True); out=d/"latest.json"; sid=re.sub(r"[^A-Za-z0-9_-]","_",str(event.get("session_id") or "default"))[:80]; per=d/f"{sid}.json"
 git=lambda *x: subprocess.run(["git","-C",str(a.root),*x],capture_output=True,text=True).stdout.strip()
 data={"schema":"agent-runtime-compact-checkpoint/v1","session_id":sid,"trigger":str(event.get("trigger") or "unknown")[:80],"phase":a.phase,"recorded_at":datetime.now(timezone.utc).isoformat(),**pointer_state(a.root/"agents/project/NEXT-SESSION-POINTER.yml"),"active_claims":active_claims(a.root),"git":{"branch":git("branch","--show-current"),"head":git("rev-parse","--short","HEAD"),"dirty_count":len(git("status","--porcelain").splitlines())},"rebootstrap_required":a.phase=="post-compact"}
 if a.phase=="post-compact" and per.exists():
  try:data.update(json.loads(per.read_text(encoding="utf-8")))
  except Exception:pass
  data.update({"session_id":sid,"phase":a.phase,"rebootstrap_required":True,"recorded_at":datetime.now(timezone.utc).isoformat()})
 for target in (per,out):
  atomic_json(target,data)
 print("{}"); return 0
if __name__=="__main__": raise SystemExit(main())
