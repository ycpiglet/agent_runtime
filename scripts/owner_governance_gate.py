"""Run Owner-facing governance gates used by hooks, CI, and release prep."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIVENESS_CHECKS = {
    "scripts/parallel_worktree_gate.py",
    "scripts/state_sync_gate.py",
}


def _parse_aware_datetime(value: str) -> str:
    raw = value.strip()
    normalized = raw[:-1] + "+00:00" if raw.endswith(("Z", "z")) else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "invalid --now: expected a timezone-aware ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise argparse.ArgumentTypeError(
            "invalid --now: expected a timezone-aware ISO-8601 timestamp"
        )
    return raw


def notify_governance_block(returncode: int) -> None:
    """Best-effort alert for a blocking owner gate; never changes the gate result."""
    try:
        source_root = str(ROOT / "src")
        if source_root not in sys.path:
            sys.path.insert(0, source_root)
        from agent_runtime.allimbot import emit_event

        emit_event(
            "attention.required",
            {
                "task_id": "owner-governance",
                "attention_kind": "governance-block",
                "owner_role": "owner",
                "state": "blocked",
            },
        )
    except Exception:
        pass


def run(args: list[str]) -> int:
    label = " ".join(args)
    print(f"owner-governance: start: {label}", flush=True)
    rc = subprocess.call([sys.executable, *args], cwd=ROOT)
    print(f"owner-governance: result: {label} -> {rc}", flush=True)
    return rc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Owner governance gate")
    parser.add_argument("--allow-empty-owner-docs", action="store_true")
    parser.add_argument(
        "--now",
        type=_parse_aware_datetime,
        help="Evaluate claim liveness at a timezone-aware ISO-8601 timestamp",
    )
    args = parser.parse_args(argv)

    owner_doc_args = ["scripts/owner_doc_format_gate.py", "--manifest", "owner-docs.yml"]
    if args.allow_empty_owner_docs:
        owner_doc_args.append("--allow-empty")
    checks = [
        owner_doc_args,
        [
            "scripts/state_machine_gate.py",
            "--path",
            "agents/project/STATE-MACHINES.yml",
            "--path",
            "schemas/state-machines.schema.json",
            "--optional-path",
            "src/agent_runtime/templates/project/agents/project/STATE-MACHINES.yml",
            "--optional-path",
            "src/agent_runtime/templates/project/schemas/state-machines.schema.json",
        ],
        ["scripts/response_contract_gate.py", "--check"],
        ["scripts/continuity_contract_gate.py", "--check"],
        ["scripts/task_identity.py", "check", "--check"],
        ["scripts/work_item_classifier.py", "--check"],
        ["scripts/org_model_gate.py", "--check"],
        ["scripts/design_system_gate.py", "--check"],
        ["scripts/work_schema_gate.py", "--items", "--check"],
        ["scripts/security_service_gate.py", "--check-active"],
        ["scripts/footprint_conflict_gate.py", "--check"],
        ["scripts/dependency_cycle_gate.py", "--check"],
        ["scripts/taskset_work_gate.py", "--check"],
        ["scripts/taskset_boundary_gate.py", "--check"],
        ["scripts/evidence_index_generator.py", "--check"],
        ["scripts/verification_freshness_gate.py", "--check"],
        ["scripts/context_knowledge_gate.py", "--check"],
        ["scripts/parallel_worktree_gate.py", "--check"],
        ["scripts/worktree_lifecycle_gate.py", "--check"],
        ["scripts/collaboration_concurrency_gate.py", "--check"],
        ["scripts/rbac_write_gate.py", "--check"],
        ["scripts/agent_identity_gate.py", "--check"],
        ["scripts/attribution_gate.py", "--check"],
        ["scripts/collaboration_governance_gate.py", "--check"],
        ["scripts/template_mirror_gate.py", "--check"],
        ["scripts/runtime_asset_usage.py", "--check"],
        ["scripts/state_sync_gate.py", "--check"],
        ["scripts/automation_rules_gate.py", "--check"],
        ["scripts/scheduled_dispatch_gate.py", "--check"],
        ["scripts/release_cadence_trigger.py", "--check"],
        ["scripts/conversation_work_audit.py", "--check"],
        ["scripts/knowledge_lint_gate.py", "--check"],
        ["scripts/planning_loop.py", "gate", "--trigger", "hook", "--action", "scan"],
    ]
    if args.now is not None:
        for check in checks:
            if check[0] in LIVENESS_CHECKS:
                check.extend(("--now", args.now))

    failed = 0
    for check in checks:
        rc = run(check)
        if rc:
            failed = rc
    if failed:
        notify_governance_block(failed)
    # Advisory (non-blocking): compound-cadence obligation. Source-repo only --
    # consumer projects lack this script, so guard on existence and skip silently
    # (never affects this gate's exit code).
    if (ROOT / "scripts" / "compound_cadence_gate.py").exists():
        if run(["scripts/compound_cadence_gate.py", "--obligation"]):
            print(
                "owner-governance: advisory: compound obligation due "
                "(review:compound ratio high) -- not blocking",
                flush=True,
            )
    return failed


if __name__ == "__main__":
    raise SystemExit(main())
