"""Autonomy policy gate for agent_runtime templates."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_POLICY = Path("src/agent_runtime/templates/project/agents/project/AUTONOMY-POLICY.example.yml")
DEFAULT_AGENTS = Path("src/agent_runtime/templates/project/AGENTS.md")
DEFAULT_REPORTING = Path("src/agent_runtime/templates/project/agents/lead_engineer/REPORTING-FORMAT.md")
DEFAULT_OUT = Path("reviews/AUTONOMY-POLICY-GATE-2026-06-09-v0.1.8.json")

REQUIRED_POLICY_TERMS = [
    "branch_commit_pr_merge:",
    "allowed_without_owner_approval: true",
    "release_council:",
    "owner_required_when:",
    "executive_brief:",
    "required_frontmatter:",
]

REQUIRED_AGENTS_TERMS = [
    "Autonomous Delivery Lane",
    "Agent may create a scoped task branch",
    "Agent may commit scoped changes",
    "Agent may open/update PR",
    "Agent may merge when configured gates pass",
    "Release Council",
    "Owner approval is required only for critical releases",
]

REQUIRED_REPORTING_TERMS = [
    "Executive BRIEF v2",
    "type: brief|plan|review|release|handoff",
    "Bottom Line -> Signal -> Action -> Insight -> Decision -> Footer",
    "frontmatter/tag/evidence/action",
]


def _read(path: Path) -> tuple[str, list[str]]:
    if not path.exists():
        return "", [f"missing:{path.as_posix()}"]
    return path.read_text(encoding="utf-8"), []


def _check_terms(label: str, text: str, terms: list[str]) -> list[str]:
    return [f"{label}:missing-term:{term}" for term in terms if term not in text]


def evaluate(policy: Path, agents: Path, reporting: Path) -> dict[str, Any]:
    policy_text, policy_findings = _read(policy)
    agents_text, agents_findings = _read(agents)
    reporting_text, reporting_findings = _read(reporting)
    findings = [
        *policy_findings,
        *agents_findings,
        *reporting_findings,
        *_check_terms("policy", policy_text, REQUIRED_POLICY_TERMS),
        *_check_terms("agents", agents_text, REQUIRED_AGENTS_TERMS),
        *_check_terms("reporting", reporting_text, REQUIRED_REPORTING_TERMS),
    ]
    return {
        "schema": "agent-runtime-autonomy-policy-gate/v1",
        "evaluation_mode": "autonomous_delivery_and_executive_brief_policy",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not findings else "block",
        "release_route": "autonomy_policy_ready" if not findings else "block",
        "findings": findings,
        "inputs": {
            "policy": policy.as_posix(),
            "agents": agents.as_posix(),
            "reporting": reporting.as_posix(),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--agents", type=Path, default=DEFAULT_AGENTS)
    parser.add_argument("--reporting", type=Path, default=DEFAULT_REPORTING)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    report = evaluate(args.policy, args.agents, args.reporting)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"status={report['status']} route={report['release_route']} findings={len(report['findings'])} out={args.out.as_posix()}")
    return 1 if report["status"] == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
