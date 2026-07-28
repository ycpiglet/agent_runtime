"""Create an indexed, schema-complete BRIEF or PLAN report for any host."""
from __future__ import annotations
import argparse, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

def _next(reports: Path, prefix: str, day: str) -> int:
    return 1 + max([int(m.group(1)) for p in reports.glob(f"{prefix}-{day}-*.md") if (m := re.search(r"-(\d{3})\.md$", p.name))] or [0])

def main(argv=None) -> int:
    p=argparse.ArgumentParser(description="Save an indexed generic report")
    p.add_argument("kind", choices=("brief","plan")); p.add_argument("--title",required=True); p.add_argument("--audience",required=True); p.add_argument("--scale",required=True); p.add_argument("--body-file",type=Path,required=True); p.add_argument("--author",default="agent-runtime"); p.add_argument("--root",type=Path,default=Path.cwd()); p.add_argument("--related-task",action="append",default=[])
    a=p.parse_args(argv); now=datetime.now(timezone.utc); day=now.date().isoformat(); reports=a.root/"agents/lead_engineer/reports"; reports.mkdir(parents=True,exist_ok=True)
    prefix=a.kind.upper(); rid=f"{prefix}-{day}-{_next(reports,prefix,day):03d}"; body=a.body_file.read_text(encoding="utf-8").strip()
    if a.audience.lower() in {"owner","ceo","mixed"} and not body.startswith("Bottom Line:"): body="Bottom Line: " + body
    front=["---",f"type: {prefix}",f"id: {rid}",f"kind: {a.kind}",f"date: {day}",f"recorded_at: {now.isoformat()}",f"audience: {a.audience}",f"scale: {a.scale}",f"title: {a.title}",f"author: {a.author}","insights_count: 0","decisions_count: 0","---",""]
    target=reports/f"{rid}.md"; target.write_text("\n".join(front)+body+"\n",encoding="utf-8")
    index=reports/"INDEX.md"; existing=index.read_text(encoding="utf-8") if index.exists() else "# Reports\n\n| ID | Kind | Title |\n|---|---|---|\n"; index.write_text(existing+f"| {rid} | {a.kind} | {a.title} |\n",encoding="utf-8")
    generator=a.root/"scripts/generate_report_views.py"
    if generator.exists(): subprocess.run([sys.executable,str(generator),"--root",str(a.root)],check=False)
    print(target.relative_to(a.root)); return 0
if __name__ == "__main__": raise SystemExit(main())
