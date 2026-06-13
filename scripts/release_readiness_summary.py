"""Aggregate v0.1.8 release readiness evidence for agent_runtime.

This is a non-mutating summary gate. It verifies that technical readiness is
complete while release execution remains owner-pending.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_OUT = Path("reviews/RELEASE-READINESS-SUMMARY-2026-06-09-v0.1.8.json")

REQUIRED_REPORTS = {
    "migration_closure": Path("reviews/REVIEW-2026-06-09-agent-runtime-task-ar-220-migration-approval-closure.md"),
    "overlay_gate": Path("reviews/OVERLAY-SIMULATION-GATE-2026-06-09-task-ar-215.json"),
    "co_location_gate": Path("reviews/CO-LOCATION-GATE-2026-06-09-task-ar-204.json"),
    "autonomy_policy_gate": Path("reviews/AUTONOMY-POLICY-GATE-2026-06-09-v0.1.8.json"),
    "release_council_gate": Path("reviews/RELEASE-COUNCIL-GATE-2026-06-09-v0.1.8.json"),
    "release_execution_gate": Path("reviews/RELEASE-EXECUTION-GATE-2026-06-09-v0.1.8.json"),
    "owner_approval_gate": Path("reviews/OWNER-APPROVAL-GATE-2026-06-09-v0.1.8.json"),
    "pending_release_guard": Path("reviews/PENDING-RELEASE-GUARD-2026-06-09-v0.1.8.json"),
}


def _load_json(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"missing:{path.as_posix()}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"json-invalid:{path.as_posix()}:{exc.msg}"]
    if not isinstance(value, dict):
        return None, [f"json-not-object:{path.as_posix()}"]
    return value, []


def _check_report(name: str, path: Path) -> dict[str, Any]:
    if path.suffix.lower() != ".json":
        return {
            "name": name,
            "path": path.as_posix(),
            "status": "pass" if path.exists() else "block",
            "route": "evidence-record",
            "findings": [] if path.exists() else [f"missing:{path.as_posix()}"],
        }
    data, findings = _load_json(path)
    if data is None:
        return {"name": name, "path": path.as_posix(), "status": "block", "route": "", "findings": findings}
    status = str(data.get("status") or "")
    route = str(data.get("release_route") or data.get("decision_route") or data.get("guard_route") or "")
    if not route and name == "overlay_gate":
        case_routes = {
            str(case.get("expected_route") or "")
            for case in data.get("case_results", [])
            if isinstance(case, dict)
        }
        if "ready_for_overlay_use" in case_routes and "hold_for_overlay" in case_routes:
            route = "ready_for_overlay_use"
    report_findings = list(findings)
    if status != "pass":
        report_findings.append(f"status-not-pass:{status or '<missing>'}")
    if data.get("findings"):
        report_findings.append("report-findings-not-empty")
    return {
        "name": name,
        "path": path.as_posix(),
        "status": status,
        "route": route,
        "findings": report_findings,
    }


def evaluate() -> dict[str, Any]:
    results = [_check_report(name, path) for name, path in REQUIRED_REPORTS.items()]
    findings: list[str] = []
    for result in results:
        findings.extend(f"{result['name']}:{item}" for item in result["findings"])

    routes = {result["name"]: result["route"] for result in results}
    expected_routes = {
        "overlay_gate": "ready_for_overlay_use",
        "co_location_gate": "ready_for_release_redecision",
        "autonomy_policy_gate": "autonomy_policy_ready",
        "release_council_gate": "agent_council_approved_release_execution",
        "release_execution_gate": "release_evidence_ready",
        "owner_approval_gate": "agent_council_approved_release_execution",
        "pending_release_guard": "release_decision_recorded",
    }
    for name, expected in expected_routes.items():
        actual = routes.get(name, "")
        if actual != expected:
            findings.append(f"{name}:route-mismatch:{actual or '<missing>'}!={expected}")

    if not findings:
        release_route = "release_evidence_ready"
        status = "pass"
    else:
        release_route = "block"
        status = "block"

    return {
        "schema": "agent-runtime-release-readiness-summary/v1",
        "evaluation_mode": "v0.1.8_readiness_aggregation",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_tag": "v0.1.8",
        "status": status,
        "release_route": release_route,
        "owner_boundary": "explicit_owner_decision_required",
        "findings": findings,
        "reports": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--target-tag", default=None, help="release tag (default: derived from pyproject version)")
    args = parser.parse_args()
    report = evaluate()
    if args.target_tag:
        report["target_tag"] = args.target_tag
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"status={report['status']} route={report['release_route']} "
        f"target={report['target_tag']} findings={len(report['findings'])} out={args.out.as_posix()}"
    )
    return 1 if report["status"] == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
