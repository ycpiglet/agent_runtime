"""Bounded, non-blocking SessionStart continuity summary."""
from __future__ import annotations
import argparse,json
from pathlib import Path
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,default=Path.cwd()); a=p.parse_args(argv); r=a.root
 checkpoint=r/"agents/runtime/session_checkpoints/latest.json"; pointer=r/"agents/project/NEXT-SESSION-POINTER.yml"
 lines=[f"agent-runtime host={r}",f"pointer={'present' if pointer.exists() else 'absent'}",f"compact_checkpoint={'present' if checkpoint.exists() else 'absent'}", "resume: run python scripts/session_resume_check.py --root ."]
 print("\n".join(lines[:8])); return 0
if __name__=="__main__": raise SystemExit(main())
