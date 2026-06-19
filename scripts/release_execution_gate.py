"""Release execution gate for agent_runtime.

This validates the boundary between `ready` and `release`. It allows a ready
governance package to pass while owner approval is pending, but blocks any
attempt to treat that state as a published release without explicit approval
and execution evidence.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_PLAN = Path("agents/project/release/RELEASE-EXECUTION.yml")
DEFAULT_TEMPLATE = Path("agents/project/RELEASE-GATE-TEMPLATE.yml")
DEFAULT_PYPROJECT = Path("pyproject.toml")
DEFAULT_INIT = Path("src/agent_runtime/__init__.py")
DEFAULT_OUT = Path("reviews/RELEASE-EXECUTION-GATE.json")

REQUIRED_READY_EVIDENCE = [
    "reviews/REVIEW-2026-06-09-agent-runtime-task-ar-220-migration-approval-closure.md",
    "reviews/REVIEW-2026-06-09-agent-runtime-task-ar-215-overlay-simulation-closure.md",
    "reviews/REVIEW-2026-06-09-agent-runtime-task-ar-204-co-location-gate-closure.md",
    "reviews/REVIEW-2026-06-09-agent-runtime-task-ar-210-ready-redecision.md",
]


def _read(path: Path) -> tuple[str, list[str]]:
    if not path.exists():
        return "", [f"missing:{path.as_posix()}"]
    return path.read_text(encoding="utf-8"), []


def _field(text: str, key: str) -> str:
    pattern = re.compile(rf"^\s*{re.escape(key)}:\s*(.*?)\s*$", re.MULTILINE)
    match = pattern.search(text)
    return match.group(1).strip().strip('"').strip("'") if match else ""


def _toml_field(text: str, key: str) -> str:
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=\s*(.*?)\s*$", re.MULTILINE)
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


def _pyproject_version(pyproject: Path) -> str:
    if not pyproject.exists():
        return ""
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', pyproject.read_text(encoding="utf-8"))
    return match.group(1) if match else ""


def _package_versions(pyproject: Path, init: Path) -> tuple[str, str, list[str]]:
    py_text, py_findings = _read(pyproject)
    init_text, init_findings = _read(init)
    findings = [*py_findings, *init_findings]
    py_version = _toml_field(py_text, "version")
    init_match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", init_text)
    init_version = init_match.group(1) if init_match else ""
    if not py_version:
        findings.append("pyproject:missing-version")
    if not init_version:
        findings.append("__init__:missing-__version__")
    if py_version and init_version and py_version != init_version:
        findings.append(f"package-version-mismatch:{py_version}!={init_version}")
    return py_version, init_version, findings


def evaluate(plan_path: Path, template_path: Path, pyproject: Path, init: Path) -> dict[str, Any]:
    plan_text, plan_findings = _read(plan_path)
    template_text, template_findings = _read(template_path)
    findings = [*plan_findings, *template_findings]

    target_version = _field(plan_text, "target_version")
    target_tag = _field(plan_text, "target_tag")
    release_state = _field(template_text, "release_state")
    release_cause = _field(template_text, "release_cause")
    owner_approval_status = _field(plan_text, "owner_approval_status")
    execution_status = _field(plan_text, "execution_status")
    package_version, init_version, version_findings = _package_versions(pyproject, init)
    findings.extend(version_findings)

    # Resolve expected version parametrically from pyproject.toml (mirrors release_council_gate)
    resolved_expected = _pyproject_version(pyproject)

    if execution_status == "executed":
        if release_state not in {"ready", "release"}:
            findings.append(f"release-template:not-ready-or-release:{release_state or '<missing>'}")
    elif release_state != "ready":
        findings.append(f"release-template:not-ready:{release_state or '<missing>'}")
    if release_cause != "all_hold_routes_closed_with_evidence":
        findings.append(f"release-cause:unexpected:{release_cause or '<missing>'}")
    if not target_version:
        findings.append("target_version:missing")
    elif resolved_expected and target_version != resolved_expected:
        findings.append(f"target_version:mismatch-pyproject:{target_version}!={resolved_expected}")
    if target_tag != f"v{target_version}":
        findings.append(f"target_tag:not-v-target-version:{target_tag or '<missing>'}!=v{target_version}")
    if package_version != init_version:
        findings.append("package-version:not-in-sync")
    if package_version and target_version and package_version == target_version and execution_status != "executed":
        findings.append("package-version-already-target-without-release-execution")

    evidence = _list_after(plan_text, "ready_evidence")
    for required in REQUIRED_READY_EVIDENCE:
        if required not in evidence:
            findings.append(f"ready_evidence:missing:{required}")
        elif not Path(required).exists():
            findings.append(f"ready_evidence:file-not-found:{required}")

    if owner_approval_status not in {"pending_owner_approval", "approved", "agent_council_approved"}:
        findings.append(f"owner_approval_status:invalid:{owner_approval_status or '<missing>'}")
    if execution_status not in {"not_started", "executed"}:
        findings.append(f"execution_status:invalid:{execution_status or '<missing>'}")
    if execution_status == "executed" and owner_approval_status not in {"approved", "agent_council_approved"}:
        findings.append("release-executed-without-release-approval")

    release_route = "ready_pending_owner_approval"
    if owner_approval_status == "approved" and execution_status == "not_started" and not findings:
        release_route = "approved_pending_release_execution"
    if owner_approval_status == "approved" and execution_status == "executed" and not findings:
        release_route = "release_evidence_ready"
    if owner_approval_status == "agent_council_approved" and execution_status == "not_started" and not findings:
        release_route = "agent_council_approved_pending_release_execution"
    if owner_approval_status == "agent_council_approved" and execution_status == "executed" and not findings:
        release_route = "release_evidence_ready"

    return {
        "schema": "agent-runtime-release-execution-gate/v1",
        "evaluation_mode": "ready_to_release_boundary",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not findings else "block",
        "release_route": release_route if not findings else "block",
        "target_version": target_version,
        "target_tag": target_tag,
        "package_version": package_version,
        "init_version": init_version,
        "release_state": release_state,
        "owner_approval_status": owner_approval_status,
        "execution_status": execution_status,
        "findings": findings,
        "inputs": {
            "plan": plan_path.as_posix(),
            "template": template_path.as_posix(),
            "pyproject": pyproject.as_posix(),
            "init": init.as_posix(),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--pyproject", type=Path, default=DEFAULT_PYPROJECT)
    parser.add_argument("--init", type=Path, default=DEFAULT_INIT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    report = evaluate(args.plan, args.template, args.pyproject, args.init)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"status={report['status']} route={report['release_route']} "
        f"target={report['target_tag']} package={report['package_version']} findings={len(report['findings'])} "
        f"out={args.out.as_posix()}"
    )
    return 1 if report["status"] == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
