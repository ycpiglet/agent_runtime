"""Cross-project overlay simulation gate for agent_runtime.

Validates that a project can swap only overlay/context files while keeping the
shared runtime core unchanged, and that missing overlay dimensions route to
hold_for_overlay through TASK-AR-204/TASK-AR-216.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("agents/project/overlays/simulations/mvp-client-2026-06-09/context-packet-simulation.json")
DEFAULT_OUT = Path("reviews/OVERLAY-SIMULATION-GATE-2026-06-09-task-ar-215.json")

REQUIRED_DIMENSIONS = ["vision", "roadmap", "organization", "team", "links", "communication"]
REQUIRED_APPROVAL_FIELDS = ["approved_by", "decision_date", "expiry", "justification"]


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


def _check_file(path_value: Any, prefix: str) -> list[str]:
    if not path_value:
        return [f"{prefix}:missing-path"]
    path = Path(str(path_value))
    if not path.exists():
        return [f"{prefix}:file-not-found:{path.as_posix()}"]
    return []


def _check_approvals(case: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    changes = case.get("overlay_changes")
    if not isinstance(changes, list) or not changes:
        return ["overlay_changes:missing"]
    for idx, change in enumerate(changes, start=1):
        if not isinstance(change, dict):
            findings.append(f"overlay_changes:{idx}:not-object")
            continue
        for field in REQUIRED_APPROVAL_FIELDS:
            if not change.get(field):
                findings.append(f"overlay_changes:{idx}:missing-{field}")
    return findings


def _check_routing_output(case: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    output = case.get("query_routing_output")
    if not isinstance(output, dict):
        return ["query_routing_output:missing"]
    for dimension in REQUIRED_DIMENSIONS:
        if dimension not in output or not output.get(dimension):
            findings.append(f"query_routing_output:missing-{dimension}")
    required_route = case.get("expected_route")
    if required_route and output.get("release_route") != required_route:
        findings.append(f"query_routing_output:release-route-mismatch:{output.get('release_route')}!={required_route}")
    return findings


def _check_case(case: dict[str, Any], root: Path) -> dict[str, Any]:
    name = str(case.get("name") or "unknown")
    findings: list[str] = []
    if case.get("runtime_core_modified") is not False:
        findings.append("runtime_core_modified:not-false")

    overlay_refs = case.get("overlay_refs")
    if not isinstance(overlay_refs, dict):
        findings.append("overlay_refs:missing")
    else:
        for dimension in REQUIRED_DIMENSIONS:
            path_value = overlay_refs.get(dimension)
            if path_value:
                findings.extend(_check_file(root / str(path_value), f"overlay_refs:{dimension}"))
            elif case.get("expected_route") != "hold_for_overlay":
                findings.append(f"overlay_refs:missing-{dimension}")

    findings.extend(_check_approvals(case))
    findings.extend(_check_routing_output(case))

    missing = case.get("expected_missing_dimensions") or []
    if missing:
        if case.get("expected_route") != "hold_for_overlay":
            findings.append("missing-case:route-not-hold_for_overlay")
        if case.get("escalation_task") != "TASK-AR-204":
            findings.append("missing-case:escalation-not-task-ar-204")
        if case.get("handoff_task") != "TASK-AR-216":
            findings.append("missing-case:handoff-not-task-ar-216")

    return {
        "name": name,
        "status": "pass" if not findings else "block",
        "expected_route": case.get("expected_route"),
        "findings": findings,
    }


def evaluate(input_path: Path) -> dict[str, Any]:
    data, load_findings = _load_json(input_path)
    findings = list(load_findings)
    case_results: list[dict[str, Any]] = []
    root = input_path.parent

    if data:
        if data.get("task_id") != "TASK-AR-215":
            findings.append("task_id:not-task-ar-215")
        if data.get("runtime_core_policy") != "overlay-only":
            findings.append("runtime_core_policy:not-overlay-only")
        cases = data.get("cases")
        if not isinstance(cases, list) or not cases:
            findings.append("cases:missing")
        else:
            has_pass_case = False
            has_hold_case = False
            for case in cases:
                if not isinstance(case, dict):
                    findings.append("case:not-object")
                    continue
                result = _check_case(case, root)
                case_results.append(result)
                findings.extend(f"{result['name']}:{item}" for item in result["findings"])
                has_pass_case = has_pass_case or result["expected_route"] == "ready_for_overlay_use"
                has_hold_case = has_hold_case or result["expected_route"] == "hold_for_overlay"
            if not has_pass_case:
                findings.append("cases:missing-ready-overlay-use-case")
            if not has_hold_case:
                findings.append("cases:missing-hold-for-overlay-case")

    status = "pass" if data and not findings else "block"
    return {
        "schema": "agent-runtime-overlay-simulation-gate/v1",
        "evaluation_mode": "cross_project_overlay_simulation",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": input_path.as_posix(),
        "status": status,
        "required_dimensions": REQUIRED_DIMENSIONS,
        "cases": len(case_results),
        "findings": findings,
        "case_results": case_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    report = evaluate(args.input)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"status={report['status']} cases={report['cases']} findings={len(report['findings'])} out={args.out.as_posix()}")
    for case in report["case_results"]:
        print(f"{case['name']} route={case['expected_route']} findings={len(case['findings'])}")
    return 1 if report["status"] == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
