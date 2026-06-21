"""Run Owner-facing governance gates used by hooks, CI, and release prep."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(args: list[str]) -> int:
    label = " ".join(args)
    print(f"owner-governance: start: {label}", flush=True)
    rc = subprocess.call([sys.executable, *args], cwd=ROOT)
    print(f"owner-governance: result: {label} -> {rc}", flush=True)
    return rc


def main() -> int:
    parser = argparse.ArgumentParser(description="Owner governance gate")
    parser.add_argument("--allow-empty-owner-docs", action="store_true")
    args = parser.parse_args()

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
        ["scripts/work_schema_gate.py", "--items", "--check"],
        ["scripts/footprint_conflict_gate.py", "--check"],
        ["scripts/dependency_cycle_gate.py", "--check"],
        ["scripts/taskset_work_gate.py", "--check"],
        ["scripts/taskset_boundary_gate.py", "--check"],
        ["scripts/evidence_index_generator.py", "--check"],
        ["scripts/verification_freshness_gate.py", "--check"],
        # intentionally omitted: scripts/context_knowledge_gate.py -- root-repo-specific
        # (validates TASKSET-AR-CONTEXT-KNOWLEDGE contracts against src/agent_runtime/templates/**,
        # agents/project/overlays/**, and agents/project/evals/* evidence that generated projects
        # do not ship). Mirrored in tests/test_owner_governance_chain_parity.py exceptions.
        # intentionally omitted: scripts/org_model_gate.py -- root-repo-specific (org-delegation
        # Unit 1): resolves work-item owner/team against the live checkout's
        # agents/project/ORG-MODEL.yml. Generated projects may seed their own
        # ORG-MODEL overlay, but this root watch-level gate remains root-only.
        # Mirrored in tests/test_owner_governance_chain_parity.py.
        # intentionally omitted: scripts/design_system_gate.py -- root-repo-specific
        # design-system maturity gate for the Agent Runtime monolith. Generated
        # projects may adopt their own design-system gate after choosing a UI stack.
        # Mirrored in tests/test_owner_governance_chain_parity.py.
        ["scripts/parallel_worktree_gate.py", "--check"],
        ["scripts/worktree_lifecycle_gate.py", "--check"],
        ["scripts/collaboration_concurrency_gate.py", "--check"],
        ["scripts/rbac_write_gate.py", "--check"],
        ["scripts/agent_identity_gate.py", "--check"],
        ["scripts/attribution_gate.py", "--check"],
        ["scripts/collaboration_governance_gate.py", "--check"],
        ["scripts/runtime_asset_usage.py", "--check"],
        ["scripts/state_sync_gate.py", "--check"],
        ["scripts/automation_rules_gate.py", "--check"],
        ["scripts/scheduled_dispatch_gate.py", "--check"],
        ["scripts/release_cadence_trigger.py", "--check"],
        ["scripts/conversation_work_audit.py", "--check"],
        ["scripts/knowledge_lint_gate.py", "--check"],
        ["scripts/planning_loop.py", "gate", "--trigger", "hook", "--action", "scan"],
    ]

    failed = 0
    for check in checks:
        rc = run(check)
        if rc:
            failed = rc
    return failed


if __name__ == "__main__":
    raise SystemExit(main())
