"""Validate task-claim isolation for parallel agent sessions.

The runtime protocol is intentionally simple:

- one active task may have only one active claim;
- one role may run in several terminals only when each call has a distinct
  agent_instance_id/callsite/worktree;
- worker claims must not point at the orchestrator checkout;
- active claims must leave handoff and log pointers so the next session can
  resume without reconstructing state from chat history;
- claim-first: every task worktree must be covered by an active claim
  (watch by default; block when claim-less work is already happening);
- claim files must be committed immediately -- untracked CLAIM-*.json files
  are erased by a concurrent session's reset+clean (2026-06-12 incident:
  CLAIM-...-task-ar-500-25db was lost and had to be recreated as -66ed).

The gate evaluates the repository it runs in (``--root``). When it runs from
a linked git worktree, the claim snapshot may predate claims committed on the
primary checkout afterwards, so claim-less worktree findings are capped at
watch severity there; the authoritative claim-first run is the one executed
from the primary checkout.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
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

TASK_WORKTREE_NAME_RE = re.compile(r"^TASK-", re.IGNORECASE)
WORKER_BRANCH_RE = re.compile(r"^(?:codex|claude)/", re.IGNORECASE)
TASK_ID_RE = re.compile(r"(TASK-[A-Z]+-\d+)", re.IGNORECASE)
SPIKE_MARKER_NAMES = ("SPIKE", "SPIKE.md")
AHEAD_BASE_REFS = ("origin/main", "origin/master", "main", "master")
CLAIM_LOSS_INCIDENT = (
    "untracked claims are erased by a concurrent session's reset+clean "
    "(2026-06-12 incident: CLAIM-...-task-ar-500-25db lost, recreated as -66ed)"
)


@dataclass(frozen=True)
class Finding:
    severity: str  # "block" | "watch"
    message: str


@dataclass(frozen=True)
class WorktreeInfo:
    path: Path
    branch: str


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

    @property
    def tags(self) -> set[str]:
        raw = self.payload.get("tags")
        if isinstance(raw, str):
            return {part.strip().lower() for part in re.split(r"[,\s]+", raw) if part.strip()}
        if isinstance(raw, (list, tuple)):
            return {str(item).strip().lower() for item in raw if str(item).strip()}
        return set()

    @property
    def spike(self) -> bool:
        return "spike" in self.tags or self.payload.get("spike") is True


def _rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _norm(path: Path) -> str:
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path.absolute()
    return os.path.normcase(str(resolved))


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


def _git(cwd: Path, *args: str) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(cwd), *args],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return 1, ""
    return proc.returncode, proc.stdout


def _git_toplevel(root: Path) -> Path | None:
    code, out = _git(root, "rev-parse", "--show-toplevel")
    if code != 0 or not out.strip():
        return None
    return Path(out.strip())


def _git_primary_root(root: Path) -> Path | None:
    """Primary checkout root of the repository containing root (if any)."""
    code, out = _git(root, "rev-parse", "--git-common-dir")
    if code != 0 or not out.strip():
        return None
    common = Path(out.strip())
    if not common.is_absolute():
        common = root / common
    try:
        return common.resolve().parent
    except OSError:
        return common.absolute().parent


def _resolved_worktree(root: Path, value: str, primary_root: Path | None = None) -> Path:
    """Resolve a claim worktree_path.

    Relative claim paths are recorded against the primary checkout root by
    protocol, so when the path does not exist under root (e.g. the gate runs
    inside a linked worktree) fall back to resolving against the primary root.
    """
    path = Path(value)
    candidates: list[Path] = []
    if path.is_absolute():
        candidates.append(path)
    else:
        candidates.append(root / path)
        if primary_root is not None and _norm(primary_root) != _norm(root):
            candidates.append(primary_root / path)
    resolved_candidates: list[Path] = []
    for candidate in candidates:
        try:
            resolved_candidates.append(candidate.resolve())
        except OSError:
            resolved_candidates.append(candidate.absolute())
    for resolved in resolved_candidates:
        if resolved.exists():
            return resolved
    return resolved_candidates[0]


def _has_git_worktree_marker(path: Path) -> bool:
    return path.is_dir() and (path / ".git").exists()


def _is_orchestrator_claim(record: ClaimRecord) -> bool:
    if record.agent_role in ORCHESTRATOR_ROLES:
        return True
    mode = str(record.payload.get("mode", "")).strip().lower()
    scope = str(record.payload.get("worker_scope", "")).strip().lower()
    return mode == "orchestrator" or scope == "orchestrator"


def _validate_claims(root: Path, records: Iterable[ClaimRecord], primary_root: Path | None) -> list[str]:
    findings: list[str] = []
    active: list[ClaimRecord] = []
    resolved_root = root.resolve()
    # Worker claims must not point at the orchestrator checkout. With git
    # context that is the primary worktree root; without it (plain host dirs)
    # the gate root itself plays that role.
    orchestrator_roots = {_norm(primary_root)} if primary_root is not None else {_norm(resolved_root)}

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
            worktree = _resolved_worktree(root, record.worktree_path, primary_root)
            if _norm(worktree) in orchestrator_roots and not _is_orchestrator_claim(record):
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
            key = _resolved_worktree(root, record.worktree_path, primary_root).as_posix().lower()
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


def _git_scans_enabled(root: Path) -> bool:
    """Git-backed scans only run when root is the toplevel of a git checkout.

    This keeps plain-directory fixtures (and roots nested inside unrelated
    repositories) on the legacy claim-only behaviour.
    """
    toplevel = _git_toplevel(root)
    return toplevel is not None and _norm(toplevel) == _norm(root)


def _list_worktrees(root: Path) -> list[WorktreeInfo]:
    code, out = _git(root, "worktree", "list", "--porcelain")
    if code != 0:
        return []
    worktrees: list[WorktreeInfo] = []
    path: Path | None = None
    branch = ""
    bare = False

    def _flush() -> None:
        nonlocal path, branch, bare
        if path is not None and not bare:
            worktrees.append(WorktreeInfo(path=path, branch=branch))
        path = None
        branch = ""
        bare = False

    for line in out.splitlines():
        line = line.rstrip()
        if not line:
            _flush()
            continue
        if line.startswith("worktree "):
            path = Path(line[len("worktree "):])
        elif line.startswith("branch "):
            branch = line[len("branch "):]
            if branch.startswith("refs/heads/"):
                branch = branch[len("refs/heads/"):]
        elif line == "bare":
            bare = True
    _flush()
    return worktrees


def _is_task_worktree(info: WorktreeInfo) -> bool:
    return bool(TASK_WORKTREE_NAME_RE.match(info.path.name) or WORKER_BRANCH_RE.match(info.branch))


def _worktree_task_ids(info: WorktreeInfo) -> set[str]:
    candidates: set[str] = set()
    for source in (info.path.name, info.branch):
        match = TASK_ID_RE.search(source)
        if match:
            candidates.add(match.group(1).upper())
    return candidates


def _worktree_dirty(path: Path) -> bool:
    code, out = _git(path, "status", "--porcelain")
    return code == 0 and any(line.strip() for line in out.splitlines())


def _worktree_ahead(path: Path) -> tuple[int, str]:
    for ref in AHEAD_BASE_REFS:
        code, _ = _git(path, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
        if code != 0:
            continue
        code, out = _git(path, "rev-list", "--count", f"{ref}..HEAD")
        if code != 0:
            continue
        try:
            return int(out.strip() or "0"), ref
        except ValueError:
            return 0, ref
    return 0, ""


def _spike_marker(path: Path) -> bool:
    return any((path / name).exists() for name in SPIKE_MARKER_NAMES)


def _claim_first_findings(root: Path, records: list[ClaimRecord], primary_root: Path | None) -> list[Finding]:
    if not _git_scans_enabled(root):
        return []
    findings: list[Finding] = []
    root_is_primary = primary_root is not None and _norm(primary_root) == _norm(root)

    active = [record for record in records if record.active]
    active_task_ids = {record.task_id.upper() for record in active if record.task_id}
    active_paths = {
        _norm(_resolved_worktree(root, record.worktree_path, primary_root))
        for record in active
        if record.worktree_path
    }
    spike_claims = [record for record in records if record.spike]
    spike_task_ids = {record.task_id.upper() for record in spike_claims if record.task_id}
    spike_paths = {
        _norm(_resolved_worktree(root, record.worktree_path, primary_root))
        for record in spike_claims
        if record.worktree_path
    }

    for info in _list_worktrees(root):
        if primary_root is not None and _norm(info.path) == _norm(primary_root):
            continue
        if not _is_task_worktree(info):
            continue
        task_ids = _worktree_task_ids(info)
        wt_key = _norm(info.path)
        if wt_key in active_paths or task_ids & active_task_ids:
            continue
        rel = _rel(root, info.path)
        if _spike_marker(info.path):
            findings.append(
                Finding("watch", f"{rel}: worktree:spike-exempt: claim-less task worktree exempted by SPIKE marker file")
            )
            continue
        if wt_key in spike_paths or task_ids & spike_task_ids:
            findings.append(
                Finding("watch", f"{rel}: worktree:spike-exempt: claim-less task worktree exempted by spike-tagged claim")
            )
            continue
        dirty = _worktree_dirty(info.path)
        ahead, base = _worktree_ahead(info.path)
        if dirty or ahead > 0:
            state_bits = []
            if dirty:
                state_bits.append("uncommitted changes")
            if ahead > 0:
                state_bits.append(f"ahead of {base or 'base'} by {ahead} commit(s)")
            state = " and ".join(state_bits)
            if root_is_primary:
                code = "worktree:missing-claim-dirty" if dirty else "worktree:missing-claim-ahead"
                findings.append(
                    Finding(
                        "block",
                        f"{rel}: {code}: claim-less task worktree has {state}; "
                        "commit an active claim on the primary checkout before working (claim-first protocol)",
                    )
                )
            else:
                findings.append(
                    Finding(
                        "watch",
                        f"{rel}: worktree:missing-claim: claim-less task worktree has {state}; "
                        "severity kept at watch because this snapshot may predate the claim commit "
                        "(run the gate from the primary checkout for the authoritative result)",
                    )
                )
            continue
        findings.append(
            Finding(
                "watch",
                f"{rel}: worktree:missing-claim: task worktree has no active claim in "
                "agents/runtime/task_claims (claim-first protocol)",
            )
        )
    return findings


def _untracked_claim_findings(root: Path, records: list[ClaimRecord]) -> list[Finding]:
    if not _git_scans_enabled(root):
        return []
    code, out = _git(root, "ls-files", "--others", "--exclude-standard", "--", "agents/runtime/task_claims")
    if code != 0:
        return []
    by_rel = {_rel(root, record.path).lower(): record for record in records}
    findings: list[Finding] = []
    for line in out.splitlines():
        rel_path = line.strip().strip('"')
        if not rel_path:
            continue
        name = PurePosixPath(rel_path).name
        if not (name.startswith("CLAIM-") and name.endswith(".json")):
            continue
        record = by_rel.get(rel_path.lower())
        if record is not None and record.spike:
            findings.append(
                Finding(
                    "watch",
                    f"{rel_path}: task-claim:claim-not-committed: spike-tagged claim file is not tracked by git; "
                    f"{CLAIM_LOSS_INCIDENT}",
                )
            )
            continue
        findings.append(
            Finding(
                "block",
                f"{rel_path}: task-claim:claim-not-committed: claim file is not tracked by git; "
                f"{CLAIM_LOSS_INCIDENT}; commit claim files immediately",
            )
        )
    return findings


def check_root(root: Path) -> list[Finding]:
    root = root.resolve()
    primary_root = _git_primary_root(root)
    records, parse_findings = _read_claims(root)
    findings = [Finding("block", message) for message in parse_findings]
    findings.extend(Finding("block", message) for message in _validate_claims(root, records, primary_root))
    active = [record for record in records if record.active]
    findings.extend(Finding("block", message) for message in _continuity_findings(root, active))
    findings.extend(_claim_first_findings(root, records, primary_root))
    findings.extend(_untracked_claim_findings(root, records))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Parallel worktree/task claim gate")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository or host root")
    parser.add_argument("--check", action="store_true", help="Return non-zero when block findings exist")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    findings = check_root(root)
    block = [finding for finding in findings if finding.severity == "block"]
    watch = [finding for finding in findings if finding.severity == "watch"]
    status = "fail" if block else "pass"
    print(f"parallel-worktree-gate: {status}")
    print(f"root={root}")
    print(f"claims={len(_claim_files(root))}")
    print(f"findings={len(findings)}")
    print(f"block={len(block)}")
    print(f"watch={len(watch)}")
    for finding in findings:
        print(f"- {finding.severity} {finding.message}")
    return 1 if args.check and block else 0


if __name__ == "__main__":
    raise SystemExit(main())
