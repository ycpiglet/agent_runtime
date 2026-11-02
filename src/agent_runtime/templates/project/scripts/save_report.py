"""Save a schema-valid, indexed BRIEF or PLAN report for a host."""
from __future__ import annotations
import argparse, json, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
from owner_doc_format_gate import (
    FRONTMATTER_PATTERN, LAYOUT_PATTERN, PROFILE_KEY_PATTERN, check_compact,
)

def quote(value: str) -> str: return json.dumps(value, ensure_ascii=False)
def next_number(reports: Path, kind: str, date: str) -> int:
    values=[int(m.group(1)) for p in reports.glob(f"{kind}-{date}-*.md") if (m:=re.search(r"-(\d{3})\.md$",p.name))]
    return max(values, default=0)+1


def prepare_body(text: str) -> tuple[str, list[str]]:
    """Transfer the generator's compact metadata once; never nest frontmatter."""
    text = text.strip()
    frontmatter = FRONTMATTER_PATTERN.match(text)
    if not frontmatter:
        if PROFILE_KEY_PATTERN.search(text):
            raise ValueError("report_layout: malformed compact frontmatter")
        return text, []
    header = frontmatter.group(0)
    if not PROFILE_KEY_PATTERN.search(header):
        return text, []  # Preserve historical unprofiled body behavior.
    if LAYOUT_PATTERN.findall(header) != ["compact-v1"]:
        raise ValueError("report_layout: unknown-or-invalid")
    body = text[frontmatter.end():].strip()
    findings = check_compact(header, body)
    if findings:
        raise ValueError("compact report: " + ", ".join(findings))
    allowed = {"report_layout", "signal", "score", "score_source"}
    lines = header.splitlines()[1:-1]
    seen = set()
    for line in lines:
        key, separator, _ = line.partition(":")
        if not separator or key not in allowed or key in seen:
            raise ValueError("compact source frontmatter: unsupported or duplicate field")
        seen.add(key)
    return body, lines


def main(argv=None) -> int:
 p=argparse.ArgumentParser(); p.add_argument("kind",choices=("brief","plan")); p.add_argument("--title",required=True); p.add_argument("--audience",choices=("Owner","CEO","agent","mixed"),required=True); p.add_argument("--scale",choices=("mini","standard","full"),required=True); p.add_argument("--body-file",type=Path,required=True); p.add_argument("--author",default="agent-runtime"); p.add_argument("--related-task",action="append",default=[]); p.add_argument("--insights-count",type=int,default=0); p.add_argument("--decisions-count",type=int,default=0); p.add_argument("--now"); p.add_argument("--root",type=Path,default=Path.cwd()); a=p.parse_args(argv)
 try:
  body, compact_fields = prepare_body(a.body_file.read_text(encoding="utf-8"))
 except (ValueError, OSError) as exc:
  print(f"save-report: {exc}", file=sys.stderr); return 2
 now=datetime.fromisoformat(a.now.replace("Z","+00:00")) if a.now else datetime.now(timezone.utc); date=now.date().isoformat(); kind=a.kind.upper(); reports=a.root/"agents/lead_engineer/reports"; reports.mkdir(parents=True,exist_ok=True); rid=f"{kind}-{date}-{next_number(reports,kind,date):03d}"
 if not compact_fields and a.audience in {"Owner","CEO","mixed"} and not body.startswith("Bottom Line:"): body="Bottom Line: "+body
 fields={"type":"report","id":rid,"kind":kind,"date":date,"recorded_at":now.isoformat(),"audience":a.audience,"scale":a.scale,"title":a.title,"author":a.author,"related_task":a.related_task,"insights_count":a.insights_count,"decisions_count":a.decisions_count}
 target=reports/f"{rid}.md"; target.write_text("---\n"+"\n".join([*(f"{k}: {quote(v) if isinstance(v,str) else v}" for k,v in fields.items()), *compact_fields])+"\n---\n\n"+body+"\n",encoding="utf-8")
 index=reports/"INDEX.md"; header="# Reports\n\n| ID | Kind | Date | Audience | Title |\n|---|---|---|---|---|\n"; old=index.read_text(encoding="utf-8") if index.exists() else header; marker="|---|---|---|---|---|\n";
 if marker not in old: raise RuntimeError("reports/INDEX.md missing canonical five-column marker")
 safe_title=a.title.replace("|", "\\|"); row=f"| [{rid}]({rid}.md) | {kind} | {date} | {a.audience} | {safe_title} |\n"; index.write_text(old.replace(marker,marker+row,1),encoding="utf-8")
 subprocess.run([sys.executable,"scripts/generate_report_views.py"],cwd=a.root,check=True); print(target.relative_to(a.root)); return 0
if __name__=="__main__": raise SystemExit(main())
