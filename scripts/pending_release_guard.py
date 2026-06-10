"""Pending release guard for agent_runtime.

Blocks accidental release execution while owner approval is still pending.
This is intentionally narrower than the full release execution gate: it only
guards the no-mutation boundary for version, release state, and execution state.
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
DEFAULT_TEMPLATE = Path("agents/project/RELEASE-GATE-TEMPLATE.yml")
DEFAULT_PYPROJECT = Path("pyproject.toml")
DEFAULT_INIT = Path("src/agent_runtime/__init__.py")
DEFAULT_OUT = Path("reviews/PENDING-RELEASE-GUARD-2026-06-09-v0.1.8.json")


def _read(path: Path) -> tuple[str, list[str]]:
    if not path.exists():
        return "", [f"missing:{path.as_posix()}"]
    return path.read_text(encoding="utf-8"), []


def _yaml_field(text: str, key: str) -> str:
    match = re.search(rf"^\s*{re.escape(key)}:\s*(.*?)\s*$", text, re.MULTILINE)
    return match.group(1).strip().strip('"').strip("'") if match else ""


def _toml_field(text: str, key: str) -> str:
    match = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.*?)\s*$", text, re.MULTILINE)
    return match.group(1).strip().strip('"').strip("'") if match else ""


def _init_version(text: str) -> str:
    match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", text)
    return match.group(1) if match else ""


def evaluate(
    approval_path: Path,
    execution_path: Path,
    template_path: Path,
    pyproject_path: Path,
    init_path: Path,
) -> dict[str, Any]:
    approval_text, approval_findings = _read(approval_path)
    execution_text, execution_findings = _read(execution_path)
    template_text, template_findings = _read(template_path)
    pyproject_text, pyproject_findings = _read(pyproject_path)
    init_text, init_findings = _read(init_path)
    findings = [
        *approval_findings,
        *execution_findings,
        *template_findings,
        *pyproject_findings,
        *init_findings,
    ]

    owner_status = _yaml_field(approval_text, "status")
    execution_owner_status = _yaml_field(execution_text, "owner_approval_status")
    execution_status = _yaml_field(execution_text, "execution_status")
    release_state = _yaml_field(template_text, "release_state")
    target_version = _yaml_field(execution_text, "target_version")
    target_tag = _yaml_field(execution_text, "target_tag")
    pyproject_version = _toml_field(pyproject_text, "version")
    init_version = _init_version(init_text)

    if owner_status in {"approved", "agent_council_approved"}:
        return {
            "schema": "agent-runtime-pending-release-guard/v1",
            "evaluation_mode": "owner_pending_no_mutation_guard",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "pass" if not findings else "block",
            "guard_route": "release_decision_recorded" if not findings else "block",
            "owner_status": owner_status,
            "execution_status": execution_status,
            "release_state": release_state,
            "target_version": target_version,
            "target_tag": target_tag,
            "pyproject_version": pyproject_version,
            "init_version": init_version,
            "findings": findings,
            "inputs": {
                "approval": approval_path.as_posix(),
                "execution": execution_path.as_posix(),
                "template": template_path.as_posix(),
                "pyproject": pyproject_path.as_posix(),
                "init": init_path.as_posix(),
            },
        }
    if owner_status != "pending_owner_approval":
        findings.append(f"owner-status-not-pending:{owner_status or '<missing>'}")
    if execution_owner_status != owner_status:
        findings.append(f"execution-owner-status-mismatch:{execution_owner_status}!={owner_status}")
    if execution_status != "not_started":
        findings.append(f"execution-status-not-started-required:{execution_status or '<missing>'}")
    if release_state == "release":
        findings.append("release-state-is-release-while-owner-pending")
    if release_state != "ready":
        findings.append(f"release-state-not-ready:{release_state or '<missing>'}")
    if target_version != "0.1.8":
        findings.append(f"target-version-not-0.1.8:{target_version or '<missing>'}")
    if target_tag != "v0.1.8":
        findings.append(f"target-tag-not-v0.1.8:{target_tag or '<missing>'}")
    if pyproject_version == target_version:
        findings.append("pyproject-version-bumped-before-owner-approval")
    if init_version == target_version:
        findings.append("init-version-bumped-before-owner-approval")
    if pyproject_version != init_version:
        findings.append(f"current-package-version-mismatch:{pyproject_version}!={init_version}")

    return {
        "schema": "agent-runtime-pending-release-guard/v1",
        "evaluation_mode": "owner_pending_no_mutation_guard",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not findings else "block",
        "guard_route": "hold_at_ready_pending_owner" if not findings else "block",
        "owner_status": owner_status,
        "execution_status": execution_status,
        "release_state": release_state,
        "target_version": target_version,
        "target_tag": target_tag,
        "pyproject_version": pyproject_version,
        "init_version": init_version,
        "findings": findings,
        "inputs": {
            "approval": approval_path.as_posix(),
            "execution": execution_path.as_posix(),
            "template": template_path.as_posix(),
            "pyproject": pyproject_path.as_posix(),
            "init": init_path.as_posix(),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--approval", type=Path, default=DEFAULT_APPROVAL)
    parser.add_argument("--execution", type=Path, default=DEFAULT_EXECUTION)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--pyproject", type=Path, default=DEFAULT_PYPROJECT)
    parser.add_argument("--init", type=Path, default=DEFAULT_INIT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    report = evaluate(args.approval, args.execution, args.template, args.pyproject, args.init)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"status={report['status']} route={report['guard_route']} "
        f"owner={report['owner_status']} release_state={report['release_state']} "
        f"package={report['pyproject_version']} findings={len(report['findings'])} out={args.out.as_posix()}"
    )
    return 1 if report["status"] == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
