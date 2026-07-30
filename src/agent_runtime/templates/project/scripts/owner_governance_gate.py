"""Run Owner-facing governance gates used by hooks, CI, and release prep."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Consumer-host guard (issue #273; host-proven in autofolio PR #148): a generated
# project ships this gate without the source repo's full surface, so checks whose
# substrate is absent in this checkout are skipped LOUDLY (never silently) and
# return 0. In the source repo every path below exists, so nothing is ever
# skipped there — source-repo behavior is unchanged by construction.
SOURCE_TEMPLATE_ROOT = ROOT / "src" / "agent_runtime" / "templates" / "project"
ROOT_STATE_SURFACES = ("BACKLOG-BOARD.md", "BACKLOG.md", "STATUS.md")
SOURCE_ONLY_CHECKS = {"scripts/collaboration_governance_gate.py", "scripts/runtime_asset_usage.py"}
LEGACY_ROOT_STATE_CHECKS = {"scripts/taskset_work_gate.py"}
PORTABLE_STATE_CHECKS = {"scripts/state_sync_gate.py"}
# Public compatibility projection used by existing host tests and extensions.
ROOT_STATE_CHECKS = LEGACY_ROOT_STATE_CHECKS | PORTABLE_STATE_CHECKS
PORTABLE_STATE_SURFACES = (
    "BACKLOG-BOARD.md",
    "agents/project/NEXT-SESSION-POINTER.yml",
)


class TrackedStateProbeError(RuntimeError):
    """Raised when canonical tracked-state inputs cannot be resolved safely."""


def _run_git_probe(
    root: Path,
    args: list[str],
    *,
    label: str,
    missing_rc: int | None = None,
) -> bytes | None:
    command = ["git", "-C", str(root), *args]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        raise TrackedStateProbeError(
            f"git {label} probe unavailable: {type(exc).__name__}"
        ) from exc
    if missing_rc is not None and result.returncode == missing_rc:
        return None
    if result.returncode != 0:
        raise TrackedStateProbeError(
            f"git {label} probe failed with code {result.returncode}"
        )
    return result.stdout


def _parse_exact_paths(
    output: bytes,
    paths: tuple[str, ...],
    *,
    label: str,
) -> set[str]:
    requested = {path.encode("utf-8") for path in paths}
    observed = {item for item in output.split(b"\0") if item}
    if observed - requested:
        raise TrackedStateProbeError(
            f"git {label} probe returned an unexpected path"
        )
    return {path for path in paths if path.encode("utf-8") in observed}


def _tracked_surface_state(
    root: Path,
    paths: tuple[str, ...],
) -> tuple[set[str], set[str]]:
    """Return exact HEAD and index path sets without opening worktree contents."""
    index_output = _run_git_probe(
        root,
        ["ls-files", "-z", "--cached", "--", *paths],
        label="index tracked-state",
    )
    if index_output is None:
        raise TrackedStateProbeError(
            "git index tracked-state probe returned no result"
        )
    index_paths = _parse_exact_paths(
        index_output,
        paths,
        label="index tracked-state",
    )

    head_oid = _run_git_probe(
        root,
        ["rev-parse", "--verify", "--quiet", "HEAD"],
        label="HEAD",
        missing_rc=1,
    )
    if head_oid is None:
        return set(), index_paths

    head_output = _run_git_probe(
        root,
        ["ls-tree", "-rz", "--name-only", "HEAD", "--", *paths],
        label="HEAD tracked-state",
    )
    if head_output is None:
        raise TrackedStateProbeError(
            "git HEAD tracked-state probe returned no result"
        )
    head_paths = _parse_exact_paths(
        head_output,
        paths,
        label="HEAD tracked-state",
    )
    return head_paths, index_paths


def _staged_deletion_error(
    head_paths: set[str],
    index_paths: set[str],
    ordered_paths: tuple[str, ...],
) -> None:
    staged_deleted = head_paths - index_paths
    if not staged_deleted:
        return
    ordered = [path for path in ordered_paths if path in staged_deleted]
    raise TrackedStateProbeError(
        "root state surface staged deletion "
        f"({', '.join(ordered)})"
    )


def _state_skip_reason(root: Path) -> str:
    """Accept one complete tracked state model and reject every partial one."""
    all_paths = tuple(dict.fromkeys(ROOT_STATE_SURFACES + PORTABLE_STATE_SURFACES))
    head_paths, index_paths = _tracked_surface_state(root, all_paths)
    _staged_deletion_error(head_paths, index_paths, all_paths)
    legacy_complete = set(ROOT_STATE_SURFACES).issubset(index_paths)
    portable_complete = set(PORTABLE_STATE_SURFACES).issubset(index_paths)
    if legacy_complete or portable_complete:
        return ""
    if not head_paths and not index_paths:
        return (
            "host checkout skip: root state surfaces absent from HEAD and "
            "index (portable and legacy)"
        )
    raise TrackedStateProbeError(
        "portable and legacy state surfaces partially tracked "
        f"(HEAD={len(head_paths)}, index={len(index_paths)}, "
        f"portable_required={len(PORTABLE_STATE_SURFACES)}, "
        f"legacy_required={len(ROOT_STATE_SURFACES)})"
    )


def _legacy_state_skip_reason(root: Path) -> str:
    """Run legacy checks only for a complete legacy tracked-state model."""
    all_paths = tuple(dict.fromkeys(ROOT_STATE_SURFACES + PORTABLE_STATE_SURFACES))
    head_paths, index_paths = _tracked_surface_state(root, all_paths)
    _staged_deletion_error(head_paths, index_paths, all_paths)
    if set(ROOT_STATE_SURFACES).issubset(index_paths):
        return ""
    if set(PORTABLE_STATE_SURFACES).issubset(index_paths):
        return (
            "host checkout skip: portable state model selected; "
            "legacy root state check is not applicable"
        )
    if not head_paths and not index_paths:
        return "host checkout skip: root state surfaces absent from HEAD and index"
    raise TrackedStateProbeError(
        "root state surfaces partially tracked "
        f"(HEAD={len(head_paths)}, index={len(index_paths)}, "
        f"required={len(ROOT_STATE_SURFACES)})"
    )


def _portable_state_skip_reason(root: Path) -> str:
    return _state_skip_reason(root)


def notify_governance_block(returncode: int) -> None:
    """Best-effort alert for a blocking owner gate; never changes the gate result."""
    if not (ROOT / "scripts" / "allimbot.py").is_file():
        return
    try:
        import allimbot

        allimbot.emit_event(
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


def skip_reason(args: list[str], *, root: Path | None = None) -> str:
    """Why this check cannot run in this checkout ('' when it can)."""
    root = root or ROOT
    script = args[0]
    if not (root / script).exists():
        return f"script missing: {script}"
    source_template_root = root / SOURCE_TEMPLATE_ROOT.relative_to(ROOT)
    if script in SOURCE_ONLY_CHECKS and not source_template_root.exists():
        return (
            "host checkout skip: "
            f"{source_template_root.relative_to(root).as_posix()} is absent"
        )
    if script in LEGACY_ROOT_STATE_CHECKS:
        return _legacy_state_skip_reason(root)
    if script in PORTABLE_STATE_CHECKS:
        return _portable_state_skip_reason(root)
    return ""


def run(args: list[str], *, root: Path | None = None) -> int:
    root = root or ROOT
    label = " ".join(args)
    try:
        reason = skip_reason(args, root=root)
    except TrackedStateProbeError as exc:
        print(
            f"owner-governance: block: {label} ({exc})",
            flush=True,
        )
        return 1
    if reason:
        print(f"owner-governance: skip: {label} ({reason})", flush=True)
        return 0
    print(f"owner-governance: start: {label}", flush=True)
    rc = subprocess.call([sys.executable, *args], cwd=root)
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
        ["scripts/security_service_gate.py", "--check-active"],
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
        # intentionally omitted: scripts/template_mirror_gate.py -- source-repo-specific
        # parity gate for scripts/** against src/agent_runtime/templates/project/scripts/**.
        # Generated projects contain only the consumer side of that comparison.
        # Mirrored in tests/test_owner_governance_chain_parity.py.
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
    if failed:
        notify_governance_block(failed)
    return failed


if __name__ == "__main__":
    raise SystemExit(main())
