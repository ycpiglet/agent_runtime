"""Agent release council decision gate for agent_runtime."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DECISION = Path("agents/project/release/RELEASE-DECISION-v0.1.8.yml")
DEFAULT_OUT = Path("reviews/RELEASE-COUNCIL-GATE-2026-06-09-v0.1.8.json")

REQUIRED_ROLES = {"lead-engineer", "qa", "independent-auditor", "doc-steward"}
CRITICAL_FLAGS = {
    "major_or_breaking_release",
    "secret_or_credential_change",
    "production_data_write",
    "billing_or_legal_impact",
    "failed_or_missing_critical_gate",
    "destructive_or_irreversible_operation",
    "untrusted_external_publication_target",
}


def _read(path: Path) -> tuple[str, list[str]]:
    if not path.exists():
        return "", [f"missing:{path.as_posix()}"]
    return path.read_text(encoding="utf-8").strip(), []


def _field(text: str, key: str) -> str:
    match = re.search(rf"^\s*{re.escape(key)}:\s*(.*?)\s*$", text, re.MULTILINE)
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


def _vote_roles(text: str) -> set[str]:
    return set(re.findall(r"^\s*-?\s*role:\s*([A-Za-z0-9_-]+)\s*$", text, flags=re.MULTILINE))


def evaluate(decision_path: Path) -> dict[str, Any]:
    text, findings = _read(decision_path)
    status = _field(text, "status")
    target_version = _field(text, "target_version")
    target_tag = _field(text, "target_tag")
    criticality = _field(text, "criticality")
    owner_required = _field(text, "owner_required")
    approved_by = _field(text, "approved_by")
    decision_date = _field(text, "decision_date")
    roles = _vote_roles(text)
    critical_flags = set(_list_after(text, "critical_flags"))
    evidence = _list_after(text, "evidence")

    if status != "agent_council_approved":
        findings.append(f"status:not-agent-council-approved:{status or '<missing>'}")
    if target_version != "0.1.8":
        findings.append(f"target_version:not-0.1.8:{target_version or '<missing>'}")
    if target_tag != "v0.1.8":
        findings.append(f"target_tag:not-v0.1.8:{target_tag or '<missing>'}")
    if criticality != "noncritical":
        findings.append(f"criticality:not-noncritical:{criticality or '<missing>'}")
    if owner_required != "false":
        findings.append(f"owner_required:not-false:{owner_required or '<missing>'}")
    if approved_by != "agent-release-council":
        findings.append(f"approved_by:not-agent-release-council:{approved_by or '<missing>'}")
    if not decision_date:
        findings.append("decision_date:missing")
    findings.extend(f"votes:missing-role:{role}" for role in sorted(REQUIRED_ROLES - roles))
    findings.extend(f"critical_flags:must-be-empty:{flag}" for flag in sorted(CRITICAL_FLAGS & critical_flags))
    if not evidence:
        findings.append("evidence:missing")
    else:
        for item in evidence:
            if not Path(item).exists():
                findings.append(f"evidence:not-found:{item}")

    return {
        "schema": "agent-runtime-release-council-gate/v1",
        "evaluation_mode": "agent_council_release_decision",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not findings else "block",
        "decision_route": "agent_council_approved_release_execution" if not findings else "block",
        "target_version": target_version,
        "target_tag": target_tag,
        "criticality": criticality,
        "owner_required": owner_required,
        "approved_by": approved_by,
        "decision_date": decision_date,
        "roles": sorted(roles),
        "findings": findings,
        "inputs": {"decision": decision_path.as_posix()},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", type=Path, default=DEFAULT_DECISION)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    report = evaluate(args.decision)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"status={report['status']} route={report['decision_route']} "
        f"target={report['target_tag']} findings={len(report['findings'])} out={args.out.as_posix()}"
    )
    return 1 if report["status"] == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
