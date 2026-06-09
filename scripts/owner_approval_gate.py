"""Owner approval gate for agent_runtime release execution.

Validates the owner decision handoff file for v0.1.8. A pending owner decision
is a valid governance state, but it must not be confused with release approval.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_APPROVAL = Path("agents/project/release/OWNER-APPROVAL-v0.1.8.yml")
DEFAULT_EXECUTION = Path("agents/project/release/RELEASE-EXECUTION-v0.1.8.yml")
DEFAULT_OUT = Path("reviews/OWNER-APPROVAL-GATE-2026-06-09-v0.1.8.json")

VALID_PENDING_STATUS = "pending_owner_approval"
VALID_DECISIONS = {"approve_release_execution", "hold_at_ready", "reject_release_execution"}
REQUIRED_APPROVAL_SCOPE = {
    "version bump from 0.1.6 to 0.1.8",
    "local release smoke",
    "external publish execution if remote is provided",
    "release_state transition from ready to release",
}


def _read(path: Path) -> tuple[str, list[str]]:
    if not path.exists():
        return "", [f"missing:{path.as_posix()}"]
    return path.read_text(encoding="utf-8"), []


def _field(text: str, key: str) -> str:
    pattern = re.compile(rf"^\s*{re.escape(key)}:\s*(.*?)\s*$", re.MULTILINE)
    match = pattern.search(text)
    return match.group(1).strip().strip('"').strip("'") if match else ""


def _list_after(text: str, key: str) -> list[str]:
    lines = text.splitlines()
    values: list[str] = []
    in_block = False
    base_indent = 0
    for raw in lines:
        stripped = raw.strip()
        indent = len(raw) - len(raw.lstrip())
        if stripped == f"{key}:":
            in_block = True
            base_indent = indent
            continue
        if not in_block:
            continue
        if stripped and indent <= base_indent and not stripped.startswith("-"):
            break
        if stripped.startswith("-"):
            values.append(stripped[1:].strip().strip('"').strip("'"))
    return values


def evaluate(approval_path: Path, execution_path: Path) -> dict[str, Any]:
    approval_text, approval_findings = _read(approval_path)
    execution_text, execution_findings = _read(execution_path)
    findings = [*approval_findings, *execution_findings]

    target_version = _field(approval_text, "target_version")
    target_tag = _field(approval_text, "target_tag")
    status = _field(approval_text, "status")
    owner = _field(approval_text, "owner")
    decision_date = _field(approval_text, "decision_date")
    approved_by = _field(approval_text, "approved_by")
    execution_approval_status = _field(execution_text, "owner_approval_status")
    execution_status = _field(execution_text, "execution_status")
    scope = set(_list_after(approval_text, "approval_scope"))
    required_decisions = set(_list_after(approval_text, "required_owner_decision"))

    if target_version != "0.1.8":
        findings.append(f"target_version:not-0.1.8:{target_version or '<missing>'}")
    if target_tag != "v0.1.8":
        findings.append(f"target_tag:not-v0.1.8:{target_tag or '<missing>'}")
    if not owner:
        findings.append("owner:missing")
    missing_scope = sorted(REQUIRED_APPROVAL_SCOPE - scope)
    findings.extend(f"approval_scope:missing:{item}" for item in missing_scope)
    missing_decisions = sorted(VALID_DECISIONS - required_decisions)
    findings.extend(f"required_owner_decision:missing:{item}" for item in missing_decisions)
    if execution_approval_status != status:
        findings.append(f"execution-plan-owner-status-mismatch:{execution_approval_status}!={status}")

    route = "owner_approval_pending"
    if status == VALID_PENDING_STATUS:
        if approved_by.upper() != "TBD":
            findings.append("pending-state:approved_by-must-remain-TBD")
        if decision_date.upper() != "TBD":
            findings.append("pending-state:decision_date-must-remain-TBD")
        if execution_status != "not_started":
            findings.append("pending-state:execution-status-not-started-required")
    elif status in {"approved", "agent_council_approved"}:
        route = "owner_approved_release_execution" if status == "approved" else "agent_council_approved_release_execution"
        if approved_by.upper() == "TBD" or not approved_by:
            findings.append("approved-state:approved_by-required")
        if decision_date.upper() == "TBD" or not decision_date:
            findings.append("approved-state:decision_date-required")
        if execution_status not in {"not_started", "executed"}:
            findings.append(f"approved-state:invalid-execution-status:{execution_status or '<missing>'}")
    elif status in {"hold_at_ready", "rejected"}:
        route = status
    else:
        findings.append(f"status:invalid:{status or '<missing>'}")

    return {
        "schema": "agent-runtime-owner-approval-gate/v1",
        "evaluation_mode": "owner_release_decision_boundary",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not findings else "block",
        "decision_route": route if not findings else "block",
        "target_version": target_version,
        "target_tag": target_tag,
        "owner_approval_status": status,
        "approved_by": approved_by,
        "decision_date": decision_date,
        "execution_status": execution_status,
        "findings": findings,
        "inputs": {
            "approval": approval_path.as_posix(),
            "execution": execution_path.as_posix(),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--approval", type=Path, default=DEFAULT_APPROVAL)
    parser.add_argument("--execution", type=Path, default=DEFAULT_EXECUTION)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    report = evaluate(args.approval, args.execution)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"status={report['status']} route={report['decision_route']} "
        f"target={report['target_tag']} approval={report['owner_approval_status']} "
        f"findings={len(report['findings'])} out={args.out.as_posix()}"
    )
    return 1 if report["status"] == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
