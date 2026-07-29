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
- every claim declares `working_tree` or `scm_commit` persistence; intentional
  working-tree persistence is visible as a reset/clean risk, while ambiguous
  legacy claims and failed explicitly authorized commits remain blocking
  (2026-06-12 incident: CLAIM-...-task-ar-500-25db was lost and recreated).

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

OVERLAY_OPTIONAL_ACTIVE_FIELDS = {"worktree_path", "branch"}
ORCHESTRATOR_ROLES = {"orchestrator", "release-orchestrator"}

TASK_WORKTREE_NAME_RE = re.compile(r"^TASK-", re.IGNORECASE)
WORKER_BRANCH_RE = re.compile(r"^(?:codex|claude)/", re.IGNORECASE)
TASK_ID_RE = re.compile(r"(TASK-[A-Z]+-\d+)", re.IGNORECASE)
SPIKE_MARKER_NAMES = ("SPIKE", "SPIKE.md")
AHEAD_BASE_REFS = ("origin/main", "origin/master", "main", "master")
STATUS_CANDIDATES = (
    Path("STATUS.md"),
    Path("agents/lead_engineer/STATUS.md"),
)
HANDOFF_MARKERS = (
    "Handoff Checklist",
    "Next Steps",
    "다음 세션",
    "다음 단계",
    "인수인계",
)
CLAIM_LOSS_INCIDENT = (
    "claims absent from HEAD are erased by a concurrent session's reset+clean "
    "(2026-06-12 incident: CLAIM-...-task-ar-500-25db lost, recreated as -66ed)"
)
CLAIM_COMMIT_TRANSACTION_ENV = "AGENT_RUNTIME_CLAIM_COMMIT_TRANSACTION"
CLAIM_COMMIT_TRANSACTION_SCHEMA = "agent-runtime-claim-commit-transaction/v1"
CLAIM_COMMIT_TRANSACTION_NONCE_RE = re.compile(r"^[0-9a-f]{32}$")


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

    @property
    def overlay(self) -> bool:
        return self.payload.get("overlay") is True


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
            if record.overlay and field in OVERLAY_OPTIONAL_ACTIVE_FIELDS:
                continue
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

        if record.overlay:
            persistence = record.payload.get("persistence")
            if persistence != {
                "mode": "working_tree",
                "scm_commit_authorized": False,
            }:
                findings.append(
                    f"{rel}: task-claim:overlay-persistence-invalid: orchestration overlays "
                    "must declare working_tree persistence without SCM authorization"
                )
            if record.payload.get("allow_parallel_task_set") is not True:
                findings.append(
                    f"{rel}: task-claim:overlay-parallel-declaration-missing: orchestration "
                    "overlays must explicitly allow parallel task-set participation"
                )
        elif record.worktree_path:
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
    status = next(
        (root / relative for relative in STATUS_CANDIDATES if (root / relative).is_file()),
        None,
    )
    if not active and status is None:
        return findings
    if status is None:
        candidates = ", ".join(path.as_posix() for path in STATUS_CANDIDATES)
        findings.append(
            f"{candidates}: continuity:status-missing: one status candidate must exist for session resume"
        )
    else:
        text = status.read_text(encoding="utf-8")
        if not any(marker in text for marker in HANDOFF_MARKERS):
            relative = _rel(root, status)
            markers = ", ".join(HANDOFF_MARKERS)
            findings.append(
                f"{relative}: continuity:status-handoff-missing: "
                f"status must include one resume marker: {markers}"
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


def _claim_matches_head(root: Path, rel_path: str) -> bool:
    """Return whether the current claim JSON is persisted exactly in HEAD.

    Merely being present in the index is insufficient: an explicitly
    authorized claim commit can fail after ``git add`` (for example in a
    pre-commit hook), leaving a staged file that is still vulnerable to
    reset+clean. Comparing the worktree path with HEAD covers both that case
    and later staged or unstaged edits to an otherwise tracked claim.
    """

    code, _ = _git(root, "cat-file", "-e", f"HEAD:{rel_path}")
    if code != 0:
        return False
    code, _ = _git(root, "diff", "--quiet", "HEAD", "--", rel_path)
    return code == 0


def _process_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _transaction_record_path(root: Path, nonce: str) -> Path | None:
    code, out = _git(
        root,
        "rev-parse",
        "--git-path",
        f"agent-runtime/claim-commit/{nonce}.json",
    )
    if code != 0 or not out.strip():
        return None
    path = Path(out.strip())
    if not path.is_absolute():
        path = root / path
    return path


def _load_claim_commit_transaction(root: Path) -> dict[str, object] | None:
    raw = os.environ.get(CLAIM_COMMIT_TRANSACTION_ENV, "")
    if not raw or len(raw) > 16_384:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    required = {
        "schema",
        "root",
        "claim_paths",
        "nonce",
        "owner_pid",
        "head",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        return None
    if payload.get("schema") != CLAIM_COMMIT_TRANSACTION_SCHEMA:
        return None
    try:
        marker_root = Path(str(payload.get("root") or "")).resolve()
    except OSError:
        return None
    if _norm(marker_root) != _norm(root):
        return None
    nonce = str(payload.get("nonce") or "")
    if CLAIM_COMMIT_TRANSACTION_NONCE_RE.fullmatch(nonce) is None:
        return None
    owner_pid = payload.get("owner_pid")
    if not isinstance(owner_pid, int) or isinstance(owner_pid, bool):
        return None
    if not _process_is_alive(owner_pid):
        return None
    claim_paths = payload.get("claim_paths")
    if (
        not isinstance(claim_paths, list)
        or not claim_paths
        or len(claim_paths) > 16
        or len(set(claim_paths)) != len(claim_paths)
    ):
        return None
    for value in claim_paths:
        if not isinstance(value, str):
            return None
        path = Path(value)
        if (
            path.is_absolute()
            or ".." in path.parts
            or len(path.parts) != 4
            or path.parts[:3] != ("agents", "runtime", "task_claims")
            or path.suffix != ".json"
        ):
            return None
    code, head = _git(root, "rev-parse", "HEAD")
    if code != 0 or head.strip() != str(payload.get("head") or ""):
        return None
    record_path = _transaction_record_path(root, nonce)
    if record_path is None or not record_path.is_file() or record_path.is_symlink():
        return None
    try:
        persisted = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if persisted != payload:
        return None
    return payload


def _claim_matches_index(root: Path, rel_path: str) -> bool:
    code, indexed = _git(root, "rev-parse", f":{rel_path}")
    if code != 0 or not indexed.strip():
        return False
    code, working = _git(root, "hash-object", f"--path={rel_path}", rel_path)
    if code != 0 or not working.strip():
        return False
    return indexed.strip() == working.strip()


def _transaction_authorizes_claim(
    root: Path,
    rel_path: str,
    record: ClaimRecord | None,
    transaction: dict[str, object] | None,
) -> bool:
    if record is None or transaction is None:
        return False
    persistence = record.payload.get("persistence")
    if persistence != {
        "mode": "scm_commit",
        "scm_commit_authorized": True,
    }:
        return False
    claim_paths = transaction.get("claim_paths")
    if not isinstance(claim_paths, list) or rel_path not in claim_paths:
        return False
    return _claim_matches_index(root, rel_path)


def _non_head_claim_findings(root: Path, records: list[ClaimRecord]) -> list[Finding]:
    if not _git_scans_enabled(root):
        return []
    by_rel = {_rel(root, record.path).lower(): record for record in records}
    transaction = _load_claim_commit_transaction(root)
    findings: list[Finding] = []
    for path in _claim_files(root):
        rel_path = _rel(root, path)
        if _claim_matches_head(root, rel_path):
            continue
        record = by_rel.get(rel_path.lower())
        persistence = record.payload.get("persistence") if record is not None else None
        mode = str(persistence.get("mode") or "").strip().lower() if isinstance(persistence, dict) else ""
        authorized = persistence.get("scm_commit_authorized") if isinstance(persistence, dict) else None
        if mode == "working_tree" and authorized is False:
            findings.append(
                Finding(
                    "watch",
                    f"{rel_path}: task-claim:working-tree-persistence: claim intentionally "
                    f"persists outside Git and leaves HEAD unchanged; {CLAIM_LOSS_INCIDENT}; "
                    "preserve the worktree or use an explicit authorized claim commit",
                )
            )
            continue
        if mode == "scm_commit" and authorized is True:
            if _transaction_authorizes_claim(root, rel_path, record, transaction):
                findings.append(
                    Finding(
                        "watch",
                        f"{rel_path}: task-claim:authorized-commit-transaction: exact "
                        "staged claim is being persisted by the active claim-only Git "
                        "transaction; ordinary post-commit HEAD validation still applies",
                    )
                )
                continue
            findings.append(
                Finding(
                    "block",
                    f"{rel_path}: task-claim:authorized-commit-not-persisted: claim explicitly "
                    f"authorized SCM persistence but is absent from or differs from HEAD; "
                    f"{CLAIM_LOSS_INCIDENT}",
                )
            )
            continue
        if record is not None and record.spike:
            findings.append(
                Finding(
                    "watch",
                    f"{rel_path}: task-claim:claim-not-committed: spike-tagged claim file "
                    f"is absent from or differs from HEAD; "
                    f"{CLAIM_LOSS_INCIDENT}",
                )
            )
            continue
        findings.append(
            Finding(
                "block",
                f"{rel_path}: task-claim:claim-not-committed: claim file is absent from or "
                f"differs from HEAD; "
                f"{CLAIM_LOSS_INCIDENT}; persistence mode is missing, ambiguous, or inconsistent",
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
    findings.extend(_non_head_claim_findings(root, records))
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
