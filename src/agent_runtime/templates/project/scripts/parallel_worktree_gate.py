"""Validate task-claim isolation for parallel agent sessions.

The runtime protocol is intentionally simple:

- one active task may have only one active claim;
- one role may run in several terminals only when each call has a distinct
  agent_instance_id/callsite/worktree;
- worker claims must not point at the orchestrator checkout;
- active claims must leave handoff and log pointers so the next session can
  resume without reconstructing state from chat history.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ACTIVE_STATUSES = {
    "assigned",
    "claimed",
    "in_progress",
    "review",
    "waiting_review",
    "working",
}

REQUIRED_ACTIVE_FIELDS = (
    "schema",
    "claim_id",
    "task_id",
    "agent_role",
    "team_id",
    "agent_instance_id",
    "display_name",
    "callsite_id",
    "pane_id",
    "status",
    "phase",
    "progress_pct",
    "status_text",
    "worktree_path",
    "branch",
    "claimed_at",
    "last_heartbeat",
    "handoff_path",
    "log_path",
)

ORCHESTRATOR_ROLES = {"orchestrator", "release-orchestrator"}


@dataclass(frozen=True)
class ClaimRecord:
    path: Path
    payload: dict[str, object]

    @property
    def status(self) -> str:
        return str(self.payload.get("status", "")).strip().lower()

    @property
    def active(self) -> bool:
        return self.status in ACTIVE_STATUSES

    @property
    def task_id(self) -> str:
        return str(self.payload.get("task_id", "")).strip()

    @property
    def task_set_id(self) -> str:
        return str(self.payload.get("task_set_id", "")).strip()

    @property
    def agent_role(self) -> str:
        return str(self.payload.get("agent_role", "")).strip()

    @property
    def agent_instance_id(self) -> str:
        return str(self.payload.get("agent_instance_id", "")).strip()

    @property
    def callsite_id(self) -> str:
        return str(self.payload.get("callsite_id", "")).strip()

    @property
    def worktree_path(self) -> str:
        return str(self.payload.get("worktree_path", "")).strip()

    @property
    def branch(self) -> str:
        return str(self.payload.get("branch", "")).strip()


def _rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _claim_files(root: Path) -> list[Path]:
    claim_dir = root / "agents" / "runtime" / "task_claims"
    if not claim_dir.is_dir():
        return []
    return sorted(claim_dir.glob("*.json"), key=lambda path: path.name.lower())


def _read_claims(root: Path) -> tuple[list[ClaimRecord], list[str]]:
    records: list[ClaimRecord] = []
    findings: list[str] = []
    for path in _claim_files(root):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            findings.append(f"{_rel(root, path)}: task-claim:invalid-json: {exc}")
            continue
        if not isinstance(payload, dict):
            findings.append(f"{_rel(root, path)}: task-claim:invalid-payload: claim payload must be a JSON object")
            continue
        records.append(ClaimRecord(path=path, payload=payload))
    return records, findings


def _resolved_worktree(root: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    try:
        return path.resolve()
    except OSError:
        return path.absolute()


def _has_git_worktree_marker(path: Path) -> bool:
    return path.is_dir() and (path / ".git").exists()


def _is_orchestrator_claim(record: ClaimRecord) -> bool:
    if record.agent_role in ORCHESTRATOR_ROLES:
        return True
    mode = str(record.payload.get("mode", "")).strip().lower()
    scope = str(record.payload.get("worker_scope", "")).strip().lower()
    return mode == "orchestrator" or scope == "orchestrator"


def _validate_claims(root: Path, records: Iterable[ClaimRecord]) -> list[str]:
    findings: list[str] = []
    active: list[ClaimRecord] = []
    resolved_root = root.resolve()

    for record in records:
        rel = _rel(root, record.path)
        if not record.active:
            continue
        active.append(record)
        for field in REQUIRED_ACTIVE_FIELDS:
            value = record.payload.get(field)
            if value is None or str(value).strip() == "":
                finding_field = field.replace("_", "-")
                findings.append(f"{rel}: task-claim:missing-{finding_field}: active task claims must include {field}")

        schema = str(record.payload.get("schema", "")).strip()
        if schema != "agent-runtime-task-claim/v1":
            findings.append(f"{rel}: task-claim:invalid-schema: expected agent-runtime-task-claim/v1")

        if record.branch in {"main", "master"} and not _is_orchestrator_claim(record):
            findings.append(f"{rel}: task-claim:main-branch-worker: worker claims must use a task branch")

        if str(record.payload.get("phase", "")).strip() != "claim-created" and not record.task_set_id:
            findings.append(f"{rel}: task-claim:missing-task-set-id: active task-set work claims must include task_set_id")

        if record.worktree_path:
            worktree = _resolved_worktree(root, record.worktree_path)
            if worktree == resolved_root and not _is_orchestrator_claim(record):
                findings.append(
                    f"{rel}: task-claim:main-checkout-worker: worker claims must use a task-specific git worktree"
                )
            elif not _is_orchestrator_claim(record):
                if not worktree.exists():
                    findings.append(
                        f"{rel}: task-claim:worktree-path-missing: active worker claim points to a missing worktree"
                    )
                elif not _has_git_worktree_marker(worktree):
                    findings.append(
                        f"{rel}: task-claim:worktree-not-git-worktree: active worker claim must point to a git worktree"
                    )

    by_task: dict[str, list[ClaimRecord]] = {}
    by_task_set: dict[str, list[ClaimRecord]] = {}
    by_instance: dict[tuple[str, str], list[ClaimRecord]] = {}
    by_worktree: dict[str, list[ClaimRecord]] = {}
    for record in active:
        if record.task_id:
            by_task.setdefault(record.task_id, []).append(record)
        if record.task_set_id:
            by_task_set.setdefault(record.task_set_id, []).append(record)
        if record.agent_role and record.agent_instance_id:
            by_instance.setdefault((record.agent_role, record.agent_instance_id), []).append(record)
        if record.worktree_path:
            key = _resolved_worktree(root, record.worktree_path).as_posix().lower()
            by_worktree.setdefault(key, []).append(record)

    for task_id, task_records in sorted(by_task.items()):
        if len(task_records) <= 1:
            continue
        paths = ", ".join(_rel(root, record.path) for record in task_records)
        findings.append(f"{paths}: task-claim:duplicate-active-task:{task_id}: one task can have one active claim")

    for task_set_id, task_set_records in sorted(by_task_set.items()):
        if len(task_set_records) <= 1:
            continue
        allow_parallel = any(
            str(record.payload.get("allow_parallel_task_set", "")).strip().lower() == "true"
            for record in task_set_records
        )
        if allow_parallel:
            continue
        paths = ", ".join(_rel(root, record.path) for record in task_set_records)
        findings.append(
            f"{paths}: task-claim:duplicate-active-task-set:{task_set_id}: one task set can have one active claim"
        )

    for (role, instance_id), instance_records in sorted(by_instance.items()):
        task_ids = {record.task_id for record in instance_records if record.task_id}
        if len(task_ids) <= 1:
            continue
        paths = ", ".join(_rel(root, record.path) for record in instance_records)
        findings.append(
            f"{paths}: task-claim:duplicate-agent-instance:{role}:{instance_id}: one agent instance cannot own multiple active tasks"
        )

    for _, worktree_records in sorted(by_worktree.items()):
        task_ids = {record.task_id for record in worktree_records if record.task_id}
        if len(task_ids) <= 1:
            continue
        paths = ", ".join(_rel(root, record.path) for record in worktree_records)
        findings.append(f"{paths}: task-claim:duplicate-worktree: one worktree cannot host multiple active task claims")

    return findings


def _continuity_findings(root: Path, active_claims: Iterable[ClaimRecord]) -> list[str]:
    findings: list[str] = []
    active = list(active_claims)
    if not active and not (root / "STATUS.md").exists():
        return findings
    status = root / "STATUS.md"
    if not status.exists():
        findings.append("STATUS.md: continuity:status-missing: STATUS.md must exist for session resume")
    else:
        text = status.read_text(encoding="utf-8")
        if "Handoff Checklist" not in text and "Next Steps" not in text:
            findings.append(
                "STATUS.md: continuity:status-handoff-missing: STATUS.md must include Handoff Checklist or Next Steps"
            )

    for record in active:
        rel = _rel(root, record.path)
        handoff = str(record.payload.get("handoff_path", "")).strip()
        log_path = str(record.payload.get("log_path", "")).strip()
        if handoff and not (root / handoff).exists():
            findings.append(f"{rel}: task-claim:handoff-path-missing-file: {handoff}")
        if log_path and not (root / log_path).exists():
            findings.append(f"{rel}: task-claim:log-path-missing-file: {log_path}")
    return findings


def check_root(root: Path) -> list[str]:
    root = root.resolve()
    records, findings = _read_claims(root)
    findings.extend(_validate_claims(root, records))
    active = [record for record in records if record.active]
    findings.extend(_continuity_findings(root, active))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Parallel worktree/task claim gate")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository or host root")
    parser.add_argument("--check", action="store_true", help="Return non-zero when findings exist")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    findings = check_root(root)
    status = "fail" if findings else "pass"
    print(f"parallel-worktree-gate: {status}")
    print(f"root={root}")
    print(f"claims={len(_claim_files(root))}")
    print(f"findings={len(findings)}")
    for finding in findings:
        print(f"- {finding}")
    return 1 if args.check and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
