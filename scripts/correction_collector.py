"""Collect correction proposals from eval/reviewer reports.

The collector reads JSON reports, extracts `correction_proposals`, and writes
owner-routed Markdown proposals. It does not apply corrections; proposals
require accountable owner approval.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any


DEFAULT_OUT_DIR = Path("agents/project/corrections")


def _slug(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "correction"


def _load_report(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - report collector should preserve failures as data.
        return None, str(exc)
    if not isinstance(value, dict):
        return None, "json-root-not-object"
    return value, None


def _proposal_markdown(report_path: Path, report: dict[str, Any], proposal: dict[str, Any], index: int) -> str:
    today = date.today().isoformat()
    due = (date.today() + timedelta(days=7)).isoformat()
    owner = str(proposal.get("owner") or "lead_engineer")
    route = str(proposal.get("route") or "TASK-AR-207")
    ptype = str(proposal.get("type") or "correction")
    severity = str(proposal.get("severity") or ("high" if report.get("status") == "block" else "medium"))
    next_action = str(proposal.get("next_action") or "review and approve correction before applying")
    report_status = str(report.get("status") or "unknown")
    report_schema = str(report.get("schema") or "unknown")
    return f"""# Correction Proposal: {ptype}

## Metadata

- created_at: {today}
- due_date: {due}
- severity: {severity}
- owner: {owner}
- approval_required: true
- approval_status: pending
- route: {route}
- source_report: {report_path.as_posix()}
- source_report_schema: {report_schema}
- source_report_status: {report_status}
- proposal_index: {index}

## Proposed Correction

{next_action}

## Guardrail

This proposal must not be applied automatically. Final definitions require owner/accountable human sign-off.
"""


def collect(report_paths: list[Path], out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []
    for report_path in report_paths:
        report, error = _load_report(report_path)
        if error:
            errors.append(f"{report_path.as_posix()}:{error}")
            continue
        assert report is not None
        proposals = report.get("correction_proposals") or []
        if not isinstance(proposals, list) or not proposals:
            skipped.append(f"{report_path.as_posix()}:no-correction-proposals")
            continue
        for idx, proposal in enumerate(proposals, start=1):
            if not isinstance(proposal, dict):
                errors.append(f"{report_path.as_posix()}:proposal-{idx}-not-object")
                continue
            ptype = str(proposal.get("type") or "correction")
            filename = f"{date.today().isoformat()}-{_slug(report_path.stem)}-{idx}-{_slug(ptype)}.md"
            target = out_dir / filename
            target.write_text(_proposal_markdown(report_path, report, proposal, idx), encoding="utf-8")
            written.append(target.as_posix())
    return {
        "schema": "agent-runtime-correction-collector-report/v1",
        "status": "pass" if written and not errors else "block",
        "reports_scanned": len(report_paths),
        "written": written,
        "skipped": skipped,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="append", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    result = collect(args.report, args.out_dir)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"status={result['status']} written={len(result['written'])} summary={args.summary.as_posix()}")
    for path in result["written"]:
        print(path)
    return 1 if result["status"] == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
