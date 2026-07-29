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
from datetime import datetime
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
POINTER_PATH = Path("agents/project/NEXT-SESSION-POINTER.yml")
POINTER_SCHEMA = "agent-runtime-next-session-pointer/v1"
POINTER_MAX_BYTES = 128 * 1024
POINTER_PLACEHOLDER_RE = re.compile(
    r"(?:YYYY-MM-DD|TASK-NNN|CLAIM-example|role-or-agent-id|"
    r"Replace this|replace this|<[^>\n]+>|\bTBD\b)"
)
POINTER_AGENT_FIELDS = (
    "claim_id",
    "agent_role",
    "team_id",
    "agent_instance_id",
    "display_name",
    "callsite_id",
    "pane_id",
    "task_id",
    "unit_id",
    "task_set_id",
    "status",
    "phase",
    "progress_pct",
    "step_index",
    "step_total",
    "status_text",
    "worktree_path",
    "branch",
    "claim_path",
    "handoff_path",
    "log_path",
    "last_heartbeat",
)
NULL_POINTER_SCALARS = {"", "null", "none", "~"}
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
CLAIM_COMMIT_TRANSACTION_SCHEMA = "agent-runtime-claim-commit-transaction/v2"
CLAIM_COMMIT_TRANSACTION_NONCE_RE = re.compile(r"^[0-9a-f]{32}$")
CLAIM_COMMIT_TRANSACTION_OID_RE = re.compile(r"^[0-9a-f]{40,64}$")


@dataclass(frozen=True)
class Finding:
    severity: str  # "block" | "watch"
    message: str


@dataclass(frozen=True)
class ContinuityReport:
    status: str
    mode: str
    pointer: str
    active_claims: int
    findings: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "mode": self.mode,
            "pointer": self.pointer,
            "active_claims": self.active_claims,
            "findings": list(self.findings),
        }


class _PointerMalformed(ValueError):
    pass


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


def _lexical_norm(path: Path) -> str:
    return os.path.normcase(os.path.abspath(os.fspath(path)))


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


def _pointer_scalar(raw: str) -> str:
    value = raw.strip()
    if not value:
        return ""
    if value.startswith('"'):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError as exc:
            raise _PointerMalformed("malformed quoted scalar") from exc
        if not isinstance(decoded, str):
            raise _PointerMalformed("pointer scalars must be strings")
        return decoded
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            raise _PointerMalformed("malformed quoted scalar")
        return value[1:-1].replace("''", "'")
    comment = re.search(r"\s+#", value)
    if comment:
        value = value[: comment.start()].rstrip()
    return value


def _pointer_mapping(
    lines: list[str],
    key: str,
    *,
    indent: int,
) -> tuple[int, str]:
    prefix = " " * indent + key + ":"
    matches: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        if not line.startswith(prefix):
            continue
        if line[:indent] != " " * indent:
            continue
        remainder = line[len(prefix) :]
        matches.append((index, remainder))
    if len(matches) != 1:
        raise _PointerMalformed(f"expected one {key} field")
    return matches[0]


def _pointer_block(
    lines: list[str],
    key: str,
    *,
    indent: int,
) -> list[str]:
    index, raw = _pointer_mapping(lines, key, indent=indent)
    if raw.strip():
        raise _PointerMalformed(f"{key} must be a mapping block")
    body: list[str] = []
    for line in lines[index + 1 :]:
        if line.strip():
            child_indent = len(line) - len(line.lstrip(" "))
            if child_indent <= indent:
                break
        body.append(line)
    return body


def _pointer_block_scalar(lines: list[str], key: str, *, indent: int) -> str:
    _, raw = _pointer_mapping(lines, key, indent=indent)
    if not raw.strip():
        raise _PointerMalformed(f"{key} must be a scalar")
    return _pointer_scalar(raw)


def _pointer_list(lines: list[str], key: str, *, indent: int) -> list[str]:
    index, raw = _pointer_mapping(lines, key, indent=indent)
    if raw.strip():
        if raw.strip() == "[]":
            return []
        raise _PointerMalformed(f"{key} must be a list")
    values: list[str] = []
    for line in lines[index + 1 :]:
        if not line.strip():
            continue
        child_indent = len(line) - len(line.lstrip(" "))
        if child_indent <= indent:
            break
        if child_indent != indent + 2 or not line[indent + 2 :].startswith("- "):
            raise _PointerMalformed(f"{key} has malformed list indentation")
        values.append(_pointer_scalar(line[indent + 4 :]))
    return values


def _pointer_agents(lines: list[str]) -> list[dict[str, str]]:
    index, raw = _pointer_mapping(lines, "current_agents", indent=2)
    if raw.strip():
        if raw.strip() == "[]":
            return []
        raise _PointerMalformed("current_agents must be a record list")
    agents: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in lines[index + 1 :]:
        if not line.strip():
            continue
        child_indent = len(line) - len(line.lstrip(" "))
        if child_indent <= 2:
            break
        if child_indent == 4 and line[4:].startswith("- "):
            if current is not None:
                agents.append(current)
            current = {}
            entry = line[6:]
        elif child_indent == 6 and current is not None:
            entry = line[6:]
        else:
            raise _PointerMalformed("current_agents has malformed record indentation")
        key, separator, raw_value = entry.partition(":")
        key = key.strip()
        if not separator or not key or key in current:
            raise _PointerMalformed("current_agents has a malformed or duplicate field")
        current[key] = _pointer_scalar(raw_value)
    if current is not None:
        agents.append(current)
    return agents


def _parse_pointer(text: str) -> dict[str, object]:
    if "\x00" in text or "\t" in text:
        raise _PointerMalformed("pointer contains an unsupported control character")
    lines = text.splitlines()
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indentation = len(line) - len(line.lstrip(" "))
        if indentation % 2:
            raise _PointerMalformed("pointer indentation must use two-space levels")
    schema = _pointer_block_scalar(lines, "schema", indent=0)
    updated_at = _pointer_block_scalar(lines, "updated_at", indent=0)
    _pointer_block(lines, "active_work", indent=0)
    resume = _pointer_block(lines, "resume", indent=0)
    pointers = _pointer_block(lines, "pointers", indent=0)
    return {
        "schema": schema,
        "updated_at": updated_at,
        "current_agents": _pointer_agents(lines),
        "active_task": _pointer_block_scalar(resume, "active_task", indent=2),
        "active_task_set": _pointer_block_scalar(
            resume, "active_task_set", indent=2
        ),
        "next_actions": _pointer_list(resume, "next_actions", indent=2),
        "active_claims": _pointer_list(pointers, "active_claims", indent=2),
    }


def _normalized_pointer_value(value: object) -> str:
    normalized = "" if value is None else str(value).strip()
    return "" if normalized.lower() in NULL_POINTER_SCALARS else normalized


def _pointer_timestamp(value: object) -> datetime | None:
    raw = _normalized_pointer_value(value)
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def _pointer_finding(code: str, detail: str) -> str:
    return f"{POINTER_PATH.as_posix()}: continuity:{code}: {detail}"


def _pointer_findings(
    root: Path,
    active_claims: list[ClaimRecord],
    *,
    require_standby_pointer: bool,
) -> list[str]:
    pointer_path = root / POINTER_PATH
    if not pointer_path.is_file():
        return [
            _pointer_finding(
                "pointer-missing",
                "canonical pointer is required when STATUS is absent",
            )
        ]
    try:
        if pointer_path.stat().st_size > POINTER_MAX_BYTES:
            return [
                _pointer_finding(
                    "pointer-too-large",
                    f"pointer exceeds {POINTER_MAX_BYTES} bytes",
                )
            ]
        text = pointer_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [_pointer_finding("pointer-unreadable", str(exc))]
    if POINTER_PLACEHOLDER_RE.search(text):
        return [
            _pointer_finding(
                "pointer-placeholder",
                "operational continuity cannot use template placeholder values",
            )
        ]
    try:
        pointer = _parse_pointer(text)
    except _PointerMalformed as exc:
        return [_pointer_finding("pointer-malformed", str(exc))]

    findings: list[str] = []
    if pointer["schema"] != POINTER_SCHEMA:
        findings.append(
            _pointer_finding(
                "pointer-schema-invalid",
                f"expected {POINTER_SCHEMA}",
            )
        )
    pointer_time = _pointer_timestamp(pointer["updated_at"])
    if pointer_time is None:
        findings.append(
            _pointer_finding(
                "pointer-updated-at-invalid",
                "updated_at must be an ISO-8601 timestamp with a timezone",
            )
        )

    pointer_refs = [str(value).strip() for value in pointer["active_claims"]]
    if len(pointer_refs) != len(set(pointer_refs)):
        findings.append(
            _pointer_finding(
                "pointer-duplicate-active-claim",
                "pointers.active_claims contains a duplicate claim path",
            )
        )
    agents = pointer["current_agents"]
    assert isinstance(agents, list)
    agent_ids = [
        _normalized_pointer_value(agent.get("claim_id"))
        for agent in agents
        if isinstance(agent, dict)
    ]
    if len(agent_ids) != len(set(agent_ids)):
        findings.append(
            _pointer_finding(
                "pointer-duplicate-current-agent",
                "active_work.current_agents contains a duplicate claim_id",
            )
        )
    next_actions = [
        _normalized_pointer_value(value) for value in pointer["next_actions"]
    ]
    if not next_actions or not all(next_actions):
        findings.append(
            _pointer_finding(
                "pointer-next-actions-missing",
                "resume.next_actions must contain at least one concrete action",
            )
        )

    expected_refs = [_rel(root, record.path) for record in active_claims]
    expected_ids = [
        _normalized_pointer_value(record.payload.get("claim_id"))
        for record in active_claims
    ]
    if not active_claims:
        if pointer_refs:
            findings.append(
                _pointer_finding(
                    "pointer-active-claims-mismatch",
                    "standby pointer must not retain active claim paths",
                )
            )
        if agents:
            findings.append(
                _pointer_finding(
                    "pointer-current-agents-mismatch",
                    "standby pointer must not retain current agent records",
                )
            )
        if any(
            _normalized_pointer_value(pointer[field])
            for field in ("active_task", "active_task_set")
        ):
            findings.append(
                _pointer_finding(
                    "pointer-resume-mismatch",
                    "standby pointer must use null active task and task-set values",
                )
            )
        return findings

    if set(pointer_refs) != set(expected_refs) or len(pointer_refs) != len(
        expected_refs
    ):
        findings.append(
            _pointer_finding(
                "pointer-active-claims-mismatch",
                "pointers.active_claims must exactly match active non-overlay claims",
            )
        )
    if set(agent_ids) != set(expected_ids) or len(agent_ids) != len(expected_ids):
        findings.append(
            _pointer_finding(
                "pointer-current-agents-mismatch",
                "current_agents claim ids must exactly match active non-overlay claims",
            )
        )

    agents_by_id = {
        _normalized_pointer_value(agent.get("claim_id")): agent
        for agent in agents
        if isinstance(agent, dict)
        and _normalized_pointer_value(agent.get("claim_id"))
    }
    heartbeat_times: list[datetime] = []
    for record in active_claims:
        claim_id = _normalized_pointer_value(record.payload.get("claim_id"))
        heartbeat = _pointer_timestamp(record.payload.get("last_heartbeat"))
        if heartbeat is None:
            findings.append(
                _pointer_finding(
                    "pointer-claim-heartbeat-invalid",
                    f"{claim_id} last_heartbeat is not a timezone-aware ISO-8601 timestamp",
                )
            )
        else:
            heartbeat_times.append(heartbeat)
        agent = agents_by_id.get(claim_id)
        if agent is None:
            continue
        for field in POINTER_AGENT_FIELDS:
            if field not in agent:
                findings.append(
                    _pointer_finding(
                        "pointer-agent-field-missing",
                        f"{claim_id} is missing {field}",
                    )
                )
                continue
            expected = (
                _rel(root, record.path)
                if field == "claim_path"
                else record.payload.get(field)
            )
            if _normalized_pointer_value(agent[field]) != _normalized_pointer_value(
                expected
            ):
                findings.append(
                    _pointer_finding(
                        "pointer-agent-field-mismatch",
                        f"{claim_id} field {field} differs from its claim",
                    )
                )
    if pointer_time is not None and heartbeat_times and pointer_time < max(
        heartbeat_times
    ):
        findings.append(
            _pointer_finding(
                "pointer-stale",
                "pointer updated_at predates an active claim heartbeat",
            )
        )

    resume_pair = (
        _normalized_pointer_value(pointer["active_task"]),
        _normalized_pointer_value(pointer["active_task_set"]),
    )
    claim_pairs = {
        (
            _normalized_pointer_value(record.payload.get("task_id")),
            _normalized_pointer_value(record.payload.get("task_set_id")),
        )
        for record in active_claims
    }
    if resume_pair not in claim_pairs:
        findings.append(
            _pointer_finding(
                "pointer-resume-mismatch",
                "resume active task and task-set must select an active claim",
            )
        )
    return findings


def continuity_report(
    root: Path,
    active_claims: Iterable[ClaimRecord] | None = None,
    *,
    require_standby_pointer: bool = False,
) -> ContinuityReport:
    root = root.resolve()
    parse_findings: list[str] = []
    if active_claims is None:
        records, parse_findings = _read_claims(root)
        active = [record for record in records if record.active]
    else:
        active = list(active_claims)
    active_workers = [record for record in active if not record.overlay]
    findings = list(parse_findings)
    status = next(
        (root / relative for relative in STATUS_CANDIDATES if (root / relative).is_file()),
        None,
    )
    mode = "idle"
    if status is not None:
        mode = "status+sidecars"
        try:
            text = status.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            findings.append(
                f"{_rel(root, status)}: continuity:status-unreadable: {exc}"
            )
        else:
            if not any(marker in text for marker in HANDOFF_MARKERS):
                relative = _rel(root, status)
                markers = ", ".join(HANDOFF_MARKERS)
                findings.append(
                    f"{relative}: continuity:status-handoff-missing: "
                    f"status must include one resume marker: {markers}"
                )
    elif active_workers or require_standby_pointer:
        mode = "pointer+sidecars"
        findings.extend(
            _pointer_findings(
                root,
                active_workers,
                require_standby_pointer=require_standby_pointer,
            )
        )

    for record in active:
        rel = _rel(root, record.path)
        handoff = str(record.payload.get("handoff_path", "")).strip()
        log_path = str(record.payload.get("log_path", "")).strip()
        if handoff and not (root / handoff).exists():
            findings.append(f"{rel}: task-claim:handoff-path-missing-file: {handoff}")
        if log_path and not (root / log_path).exists():
            findings.append(f"{rel}: task-claim:log-path-missing-file: {log_path}")
    return ContinuityReport(
        status="fail" if findings else "pass",
        mode=mode,
        pointer=POINTER_PATH.as_posix(),
        active_claims=len(active_workers),
        findings=tuple(findings),
    )


def _continuity_findings(root: Path, active_claims: Iterable[ClaimRecord]) -> list[str]:
    return list(continuity_report(root, active_claims).findings)


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
    return Path(os.path.abspath(os.fspath(path)))


def _transaction_private_dir(root: Path) -> Path | None:
    code, out = _git(
        root,
        "rev-parse",
        "--git-path",
        "agent-runtime/claim-commit",
    )
    if code != 0 or not out.strip():
        return None
    path = Path(out.strip())
    if not path.is_absolute():
        path = root / path
    try:
        return path.resolve()
    except OSError:
        return None


def _valid_transaction_artifact_path(value: object) -> bool:
    if not isinstance(value, str) or len(value) > 300:
        return False
    path = Path(value)
    if (
        path.is_absolute()
        or ".." in path.parts
        or len(path.parts) != 4
        or path.parts[:3] != ("agents", "runtime", "task_claims")
    ):
        return False
    name = path.name
    if not name or not all(character.isalnum() or character in "._-" for character in name):
        return False
    return (
        path.suffix == ".json"
        or name.endswith(".handoff.md")
        or name.endswith(".log.md")
    )


def _private_index_entry(root: Path, rel_path: str) -> tuple[str, str] | None:
    code, staged = _git(root, "ls-files", "--stage", "--", rel_path)
    lines = [line for line in staged.splitlines() if line.strip()]
    if code != 0 or len(lines) != 1:
        return None
    fields = lines[0].split(None, 3)
    if len(fields) != 4 or fields[2] != "0" or fields[3] != rel_path:
        return None
    return fields[0], fields[1]


def _load_claim_commit_transaction(root: Path) -> dict[str, object] | None:
    raw = os.environ.get(CLAIM_COMMIT_TRANSACTION_ENV, "")
    if not raw or len(raw) > 65_536:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    required = {
        "schema",
        "root",
        "claim_paths",
        "artifacts",
        "nonce",
        "owner_pid",
        "head",
        "ref",
        "index",
        "tree",
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
    head_oid = payload.get("head")
    tree_oid = payload.get("tree")
    ref_name = payload.get("ref")
    if (
        not isinstance(head_oid, str)
        or CLAIM_COMMIT_TRANSACTION_OID_RE.fullmatch(head_oid) is None
        or not isinstance(tree_oid, str)
        or CLAIM_COMMIT_TRANSACTION_OID_RE.fullmatch(tree_oid) is None
        or not isinstance(ref_name, str)
        or not ref_name.startswith("refs/heads/")
    ):
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
        if not _valid_transaction_artifact_path(value) or Path(value).suffix != ".json":
            return None

    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts or len(artifacts) > 48:
        return None
    artifact_map: dict[str, tuple[str, str]] = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict) or set(artifact) != {"path", "mode", "oid"}:
            return None
        artifact_path = artifact.get("path")
        mode = artifact.get("mode")
        oid = artifact.get("oid")
        if (
            not _valid_transaction_artifact_path(artifact_path)
            or not isinstance(mode, str)
            or mode != "100644"
            or not isinstance(oid, str)
            or CLAIM_COMMIT_TRANSACTION_OID_RE.fullmatch(oid) is None
            or artifact_path in artifact_map
        ):
            return None
        artifact_map[artifact_path] = (mode, oid)
    artifact_claim_paths = sorted(
        path for path in artifact_map if Path(path).suffix == ".json"
    )
    if sorted(claim_paths) != artifact_claim_paths:
        return None

    code, head = _git(root, "rev-parse", "HEAD")
    if code != 0 or head.strip() != head_oid:
        return None
    code, current_ref = _git(root, "symbolic-ref", "-q", "HEAD")
    if code != 0 or current_ref.strip() != ref_name:
        return None

    private_dir = _transaction_private_dir(root)
    raw_index = payload.get("index")
    env_index = os.environ.get("GIT_INDEX_FILE", "")
    if private_dir is None or not isinstance(raw_index, str) or not raw_index or not env_index:
        return None
    marker_index = Path(raw_index)
    inherited_index = Path(env_index)
    expected_index = private_dir / f"{nonce}.index"
    if (
        not marker_index.is_absolute()
        or not inherited_index.is_absolute()
        or _lexical_norm(marker_index) != _lexical_norm(expected_index)
        or _lexical_norm(inherited_index) != _lexical_norm(expected_index)
        or not marker_index.is_file()
        or marker_index.is_symlink()
    ):
        return None
    if os.name != "nt":
        try:
            if marker_index.stat().st_mode & 0o077:
                return None
        except OSError:
            return None

    code, current_tree = _git(root, "write-tree")
    if code != 0 or current_tree.strip() != tree_oid:
        return None
    for artifact_path, expected_entry in artifact_map.items():
        if _private_index_entry(root, artifact_path) != expected_entry:
            return None

    code, changed = _git(
        root,
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "--no-renames",
        "-r",
        head_oid,
        tree_oid,
        "--",
    )
    changed_paths = {line for line in changed.splitlines() if line}
    if code != 0 or not changed_paths or not changed_paths.issubset(artifact_map):
        return None

    record_path = _transaction_record_path(root, nonce)
    expected_record = private_dir / f"{nonce}.json"
    if (
        record_path is None
        or _lexical_norm(record_path) != _lexical_norm(expected_record)
        or not record_path.is_file()
        or record_path.is_symlink()
    ):
        return None
    if os.name != "nt":
        try:
            if record_path.stat().st_mode & 0o077:
                return None
        except OSError:
            return None
    try:
        persisted = record_path.read_text(encoding="utf-8")
    except OSError:
        return None
    if persisted != raw + "\n":
        return None
    return payload


def _claim_matches_index(root: Path, rel_path: str, expected_oid: str) -> bool:
    entry = _private_index_entry(root, rel_path)
    if entry != ("100644", expected_oid):
        return False
    code, working = _git(root, "hash-object", f"--path={rel_path}", rel_path)
    if code != 0 or not working.strip():
        return False
    return working.strip() == expected_oid


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
    artifacts = transaction.get("artifacts")
    if not isinstance(artifacts, list):
        return False
    expected_oid = ""
    for artifact in artifacts:
        if isinstance(artifact, dict) and artifact.get("path") == rel_path:
            expected_oid = str(artifact.get("oid") or "")
            break
    if CLAIM_COMMIT_TRANSACTION_OID_RE.fullmatch(expected_oid) is None:
        return False
    return _claim_matches_index(root, rel_path, expected_oid)


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
    parser.add_argument(
        "--continuity-only",
        action="store_true",
        help="Evaluate only the effective STATUS or pointer-plus-sidecars path",
    )
    parser.add_argument(
        "--require-standby-pointer",
        action="store_true",
        help="Require a structurally usable pointer even when no claim is active",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    if args.continuity_only:
        report = continuity_report(
            root,
            require_standby_pointer=args.require_standby_pointer,
        )
        if args.json:
            print(json.dumps(report.as_dict(), ensure_ascii=False, sort_keys=True))
        else:
            print(f"continuity: {report.status}")
            print(f"mode={report.mode}")
            print(f"pointer={report.pointer}")
            print(f"active_claims={report.active_claims}")
            print(f"findings={len(report.findings)}")
            for finding in report.findings:
                print(f"- {finding}")
        return 1 if report.findings else 0
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
