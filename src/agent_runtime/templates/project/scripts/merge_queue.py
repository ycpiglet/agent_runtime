"""Integrator merge queue: serial rebase-test-merge for worker branches.

Parallel waves end with N worker branches waiting to join main. Unordered
joins create rebase races and shared-SSoT regeneration contention
(board/INDEX/BACKLOG). This script encodes the orchestrator's manually proven
flow (PRs #45-#53) as a single-integrator serial queue:

  enqueue -> [per entry] fetch -> rebase onto the integration base -> narrow
  verification -> base-owned required gates -> merge (local mode) or print PR
  commands (--pr-mode) -> next entry -> regenerate the board once per
  processed batch.

Queue state lives in the primary checkout at
``agents/runtime/merge_queue/queue.json`` (schema
``agent-runtime-merge-queue/v1``) so ui-console and every linked worktree
observe one state file. A failing entry is marked ``failed`` with a reason
plus a worker feedback file beside the shared queue
(``agents/runtime/merge_queue/feedback-<branch>.md``); the queue continues
with the next eligible entry and never poisons the integration branch.

Safety invariants:
  - every mutating command holds one cross-process lock in the Git common
    directory, so linked worktrees cannot race queue or integration state;
  - queue JSON is flushed and atomically replaced while that lock is held;
  - declared task dependencies are validated and topologically ordered before
    any branch is rebased or merged;
  - optional ``agents/host/MERGE-GATES.json`` policy is bound at enqueue,
    revalidated from the integration base, and cannot be weakened by a worker
    branch or an enqueue-time ``--verify`` override;
  - never force-pushes; never deletes branches;
  - failed rebases/merges are aborted and the work tree is restored;
  - ``--pr-mode`` performs no remote merge: it pushes the rebased branch only
    when the push is a plain fast-forward/new ref and PRINTS the ``gh``
    commands for the orchestrator instead of executing them;
  - ``--dry-run`` mutates nothing (read-only git inspection and no queue
    writes).

Usage:
  python scripts/merge_queue.py enqueue --branch B --task-id T
      [--claim-id C] [--depends-on-task T]... [--verify CMD]...
  python scripts/merge_queue.py list
  python scripts/merge_queue.py process [--once|--all] [--dry-run]
      [--base origin/main] [--integration-branch NAME] [--pr-mode]
      [--regen-cmd CMD]
  python scripts/merge_queue.py remove --branch B

All subcommands accept ``--root PATH`` (defaults to this repository).
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import heapq
import json
import math
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, BinaryIO, Iterator

ROOT = Path(__file__).resolve().parent.parent
QUEUE_REL = "agents/runtime/merge_queue/queue.json"
FEEDBACK_DIR_REL = "agents/runtime/merge_queue"
MERGE_GATES_REL = "agents/host/MERGE-GATES.json"
SCHEMA = "agent-runtime-merge-queue/v1"
MERGE_GATES_SCHEMA = "agent-runtime-merge-gates/v1"
DEFAULT_BASE = "origin/main"
DEFAULT_VERIFY_CMD = "python scripts/owner_governance_gate.py"
DEFAULT_REGEN_CMD = "python scripts/backlog_board.py --write"
ACTIVE_STATUSES = {"pending", "rebasing", "testing", "merging"}
# pr-handoff is terminal for this queue (the merge happens remotely via the
# printed gh commands) but still blocks re-enqueue until the orchestrator
# runs `remove` after the PR merges.
ENQUEUE_BLOCKING_STATUSES = ACTIVE_STATUSES | {"pr-handoff"}
ALL_STATUSES = {"pending", "rebasing", "testing", "merging", "pr-handoff", "merged", "failed"}
OUTPUT_TAIL_LINES = 60
PREFIX = "[merge-queue]"
# Every git/verify/regen subprocess is bounded so one hung command cannot
# wedge the queue. Override via the MERGE_QUEUE_TIMEOUT_SECONDS env var.
DEFAULT_COMMAND_TIMEOUT_SECONDS = 600.0
DEFAULT_LOCK_TIMEOUT_SECONDS = 10.0
LOCK_POLL_SECONDS = 0.05
LOCK_FILENAME = "agent-runtime-merge-queue.lock"
DEPENDENCY_SUCCESS_STATUSES = {"merged"}
GATE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
GATE_PLACEHOLDER_RE = re.compile(r"\{([^{}]+)\}")
ALLOWED_GATE_PLACEHOLDERS = {"task_id", "branch", "base"}


class MergeQueueError(Exception):
    """Environmental or preflight error that aborts the current command."""


class CommandTimedOut(MergeQueueError):
    """A bounded subprocess exceeded the configured timeout."""


class CommandLaunchFailed(MergeQueueError):
    """A configured subprocess could not be started."""


def _command_timeout_seconds() -> float:
    raw = os.environ.get("MERGE_QUEUE_TIMEOUT_SECONDS", "").strip()
    if raw:
        try:
            value = float(raw)
        except ValueError:
            value = 0.0
        if value > 0:
            return value
    return DEFAULT_COMMAND_TIMEOUT_SECONDS


def _now_iso() -> str:
    text = dt.datetime.now(dt.timezone.utc).astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
    if len(text) >= 5 and text[-5] in "+-":
        text = text[:-2] + ":" + text[-2:]
    return text


def _say(message: str) -> None:
    print(f"{PREFIX} {message}")


def queue_path(root: Path) -> Path:
    return shared_state_root(root) / QUEUE_REL


def _empty_queue() -> dict[str, Any]:
    return {"schema": SCHEMA, "updated_at": "", "entries": []}


def load_queue(root: Path) -> dict[str, Any]:
    path = queue_path(root)
    if not path.exists():
        return _empty_queue()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MergeQueueError(f"queue file unreadable: {path} ({exc})") from exc
    if not isinstance(payload, dict) or str(payload.get("schema") or "") != SCHEMA:
        raise MergeQueueError(
            f"queue file has unexpected schema (want {SCHEMA}): {path}"
        )
    if not isinstance(payload.get("entries"), list):
        raise MergeQueueError(f"queue file entries must be a list: {path}")
    return payload


def save_queue(root: Path, payload: dict[str, Any]) -> None:
    path = queue_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload["schema"] = SCHEMA
    payload["updated_at"] = _now_iso()
    encoded = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode(
        "utf-8"
    )
    descriptor = -1
    temporary_path: Path | None = None
    try:
        descriptor, raw_path = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=str(path.parent),
        )
        temporary_path = Path(raw_path)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
        try:
            directory_fd = os.open(path.parent, os.O_RDONLY)
        except OSError:
            directory_fd = -1
        if directory_fd >= 0:
            try:
                try:
                    os.fsync(directory_fd)
                except OSError:
                    # Some platforms do not support fsync on a directory.
                    pass
            finally:
                os.close(directory_fd)
    except OSError as exc:
        raise MergeQueueError(f"queue file atomic write failed: {path} ({exc})") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def new_entry(
    branch: str,
    task_id: str,
    claim_id: str = "",
    verify_cmds: list[str] | None = None,
    depends_on_task_ids: list[str] | None = None,
    required_gate_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry = {
        "branch": branch,
        "task_id": task_id,
        "claim_id": claim_id,
        "depends_on_task_ids": list(depends_on_task_ids or []),
        "narrow_verification_cmds": list(verify_cmds or []),
        "enqueued_at": _now_iso(),
        "status": "pending",
        "failure_reason": "",
        "processed_at": "",
    }
    policy = required_gate_policy or _empty_merge_gate_policy()
    if policy["gates"]:
        entry["required_gate_policy_digest"] = merge_gate_policy_digest(policy)
        entry["required_gate_ids"] = [gate["id"] for gate in policy["gates"]]
    return entry


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    timeout = _command_timeout_seconds()
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise CommandTimedOut(f"git {' '.join(args)} exceeded {timeout}s") from exc
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise MergeQueueError(f"git {' '.join(args)} failed: {detail}")
    return result


def _lock_timeout_seconds() -> float:
    raw = os.environ.get("MERGE_QUEUE_LOCK_TIMEOUT_SECONDS", "").strip()
    if raw:
        try:
            value = float(raw)
        except ValueError:
            value = 0.0
        if value > 0 and math.isfinite(value):
            return value
    return DEFAULT_LOCK_TIMEOUT_SECONDS


def git_common_dir(root: Path) -> Path:
    result = _git(root, "rev-parse", "--git-common-dir")
    value = (result.stdout or "").strip()
    if not value:
        raise MergeQueueError(f"git common directory is unavailable: {root}")
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    try:
        return path.resolve(strict=True)
    except OSError as exc:
        raise MergeQueueError(
            f"git common directory is unavailable: {path} ({exc})"
        ) from exc


def queue_lock_path(root: Path) -> Path:
    return git_common_dir(root) / LOCK_FILENAME


def shared_state_root(root: Path) -> Path:
    """Resolve the primary checkout shared by every linked worktree."""

    common_dir = git_common_dir(root)
    result = _git(root, "worktree", "list", "--porcelain")
    for line in (result.stdout or "").splitlines():
        if not line.startswith("worktree "):
            continue
        candidate_text = line.removeprefix("worktree ").strip()
        if not candidate_text:
            continue
        try:
            candidate = Path(candidate_text).resolve(strict=True)
        except OSError:
            continue
        if git_common_dir(candidate) == common_dir:
            return candidate
        break
    raise MergeQueueError(
        f"primary worktree is unavailable for shared merge queue state: {root}"
    )


def _empty_merge_gate_policy() -> dict[str, Any]:
    return {
        "schema": MERGE_GATES_SCHEMA,
        "protected_paths": [],
        "gates": [],
    }


def _validate_gate_patterns(gate_id: str, field: str, raw: Any) -> list[str]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise MergeQueueError(
            f"{MERGE_GATES_REL}: gate {gate_id!r} {field} must be a list"
        )
    patterns: list[str] = []
    for value in raw:
        if not isinstance(value, str) or not value.strip():
            raise MergeQueueError(
                f"{MERGE_GATES_REL}: gate {gate_id!r} {field} entries "
                "must be non-empty strings"
            )
        pattern = value.strip()
        path = Path(pattern)
        if path.is_absolute() or ".." in path.parts or "\\" in pattern:
            raise MergeQueueError(
                f"{MERGE_GATES_REL}: gate {gate_id!r} has unsafe {field} "
                f"pattern {pattern!r}"
            )
        if pattern not in patterns:
            patterns.append(pattern)
    return patterns


def normalize_merge_gate_policy(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise MergeQueueError(f"{MERGE_GATES_REL}: policy must be a JSON object")
    if str(payload.get("schema") or "") != MERGE_GATES_SCHEMA:
        raise MergeQueueError(
            f"{MERGE_GATES_REL}: unexpected schema "
            f"(want {MERGE_GATES_SCHEMA})"
        )
    raw_gates = payload.get("gates")
    if not isinstance(raw_gates, list):
        raise MergeQueueError(f"{MERGE_GATES_REL}: gates must be a list")
    protected_paths = _validate_gate_patterns(
        "policy", "protected_paths", payload.get("protected_paths")
    )
    if raw_gates and not protected_paths:
        raise MergeQueueError(
            f"{MERGE_GATES_REL}: protected_paths must be a non-empty list "
            "when gates are configured"
        )
    if raw_gates and MERGE_GATES_REL not in protected_paths:
        raise MergeQueueError(
            f"{MERGE_GATES_REL}: protected_paths must include "
            f"{MERGE_GATES_REL!r}"
        )

    gates: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw_gate in enumerate(raw_gates, start=1):
        if not isinstance(raw_gate, dict):
            raise MergeQueueError(
                f"{MERGE_GATES_REL}: gate #{index} must be a JSON object"
            )
        gate_id = str(raw_gate.get("id") or "").strip()
        if not GATE_ID_RE.fullmatch(gate_id):
            raise MergeQueueError(
                f"{MERGE_GATES_REL}: gate #{index} has invalid id {gate_id!r}"
            )
        if gate_id in seen_ids:
            raise MergeQueueError(
                f"{MERGE_GATES_REL}: duplicate gate id {gate_id!r}"
            )
        seen_ids.add(gate_id)

        command = raw_gate.get("command")
        if not isinstance(command, str) or not command.strip():
            raise MergeQueueError(
                f"{MERGE_GATES_REL}: gate {gate_id!r} command must be "
                "a non-empty string"
            )
        command = command.strip()
        try:
            argv = _split_command(command)
        except ValueError as exc:
            raise MergeQueueError(
                f"{MERGE_GATES_REL}: gate {gate_id!r} command cannot be "
                f"parsed: {exc}"
            ) from exc
        if not argv:
            raise MergeQueueError(
                f"{MERGE_GATES_REL}: gate {gate_id!r} command is empty"
            )
        placeholders = set(GATE_PLACEHOLDER_RE.findall(command))
        unknown = sorted(placeholders - ALLOWED_GATE_PLACEHOLDERS)
        if unknown:
            raise MergeQueueError(
                f"{MERGE_GATES_REL}: gate {gate_id!r} uses unknown "
                f"placeholder(s): {', '.join(unknown)}"
            )

        gates.append(
            {
                "id": gate_id,
                "command": command,
                "include_paths": _validate_gate_patterns(
                    gate_id, "include_paths", raw_gate.get("include_paths")
                ),
                "exclude_paths": _validate_gate_patterns(
                    gate_id, "exclude_paths", raw_gate.get("exclude_paths")
                ),
            }
        )
    return {
        "schema": MERGE_GATES_SCHEMA,
        "protected_paths": protected_paths,
        "gates": gates,
    }


def _parse_merge_gate_policy(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MergeQueueError(
            f"{MERGE_GATES_REL}: invalid JSON ({exc})"
        ) from exc
    return normalize_merge_gate_policy(payload)


def load_merge_gate_policy(root: Path) -> dict[str, Any]:
    path = shared_state_root(root) / MERGE_GATES_REL
    if not path.exists():
        return _empty_merge_gate_policy()
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise MergeQueueError(f"{MERGE_GATES_REL}: unreadable ({exc})") from exc
    return _parse_merge_gate_policy(text)


def load_merge_gate_policy_from_ref(root: Path, ref: str) -> dict[str, Any]:
    if not _git_ok(root, "rev-parse", "--verify", "--quiet", ref):
        raise MergeQueueError(
            f"required-gate policy base ref does not resolve: {ref}"
        )
    object_ref = f"{ref}:{MERGE_GATES_REL}"
    if not _git_ok(root, "cat-file", "-e", object_ref):
        return _empty_merge_gate_policy()
    result = _git(root, "show", object_ref, check=False)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise MergeQueueError(
            f"required-gate policy cannot be read from {ref}: {detail}"
        )
    return _parse_merge_gate_policy(result.stdout or "")


def merge_gate_policy_digest(policy: dict[str, Any]) -> str:
    normalized = normalize_merge_gate_policy(policy)
    encoded = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_entry_gate_policy(
    entry: dict[str, Any], policy: dict[str, Any]
) -> None:
    gates = policy["gates"]
    expected_digest = merge_gate_policy_digest(policy) if gates else ""
    expected_ids = [gate["id"] for gate in gates]
    bound_digest = str(entry.get("required_gate_policy_digest") or "")
    bound_ids = entry.get("required_gate_ids")

    if not gates and not bound_digest and bound_ids in (None, []):
        return
    task_id = str(entry.get("task_id") or "?")
    if gates and (not bound_digest or not isinstance(bound_ids, list)):
        raise MergeQueueError(
            f"required-gate policy is not bound to {task_id}; remove and "
            "re-enqueue the branch"
        )
    if bound_digest != expected_digest or bound_ids != expected_ids:
        raise MergeQueueError(
            f"required-gate policy drift for {task_id}; remove and re-enqueue "
            "the branch against the current integration policy"
        )


def _path_matches(path: str, pattern: str) -> bool:
    return fnmatch.fnmatchcase(path, pattern)


def gate_applies(gate: dict[str, Any], changed_paths: list[str]) -> bool:
    remaining = [
        path
        for path in changed_paths
        if not any(
            _path_matches(path, pattern)
            for pattern in gate.get("exclude_paths", [])
        )
    ]
    if not remaining:
        return False
    includes = gate.get("include_paths", [])
    if not includes:
        return True
    return any(
        _path_matches(path, pattern)
        for path in remaining
        for pattern in includes
    )


def protected_path_changes(
    policy: dict[str, Any], changed_paths: list[str]
) -> list[str]:
    patterns = policy.get("protected_paths", [])
    return sorted(
        path
        for path in changed_paths
        if any(_path_matches(path, pattern) for pattern in patterns)
    )


def _prepare_lock_handle(path: Path) -> BinaryIO:
    try:
        handle = path.open("a+b")
        if os.name == "nt":
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\n")
                handle.flush()
        return handle
    except OSError as exc:
        raise MergeQueueError(f"merge queue lock is unavailable: {path} ({exc})") from exc


def _try_acquire_file_lock(handle: BinaryIO) -> bool:
    if os.name == "nt":
        import msvcrt

        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            return False
        return True

    import fcntl

    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _release_file_lock(handle: BinaryIO) -> None:
    if os.name == "nt":
        import msvcrt

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        return

    import fcntl

    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _lock_holder_text(handle: BinaryIO) -> str:
    try:
        handle.seek(0)
        return handle.read(2048).decode("utf-8", errors="replace").strip()
    except OSError:
        return ""


@contextmanager
def exclusive_queue_lock(root: Path, command: str) -> Iterator[Path]:
    path = queue_lock_path(root)
    handle = _prepare_lock_handle(path)
    timeout = _lock_timeout_seconds()
    deadline = time.monotonic() + timeout
    acquired = False
    try:
        while not acquired:
            acquired = _try_acquire_file_lock(handle)
            if acquired:
                break
            if time.monotonic() >= deadline:
                holder = _lock_holder_text(handle)
                detail = f"; last holder={holder}" if holder else ""
                raise MergeQueueError(
                    f"merge queue lock busy after {timeout:g}s: {path}{detail}; "
                    "wait for the active enqueue/remove/process command to finish"
                )
            time.sleep(LOCK_POLL_SECONDS)

        owner = json.dumps(
            {
                "pid": os.getpid(),
                "command": command,
                "acquired_at": _now_iso(),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        handle.seek(0)
        handle.truncate()
        handle.write(owner)
        handle.flush()
        os.fsync(handle.fileno())
        yield path
    finally:
        if acquired:
            try:
                _release_file_lock(handle)
            except OSError:
                pass
        handle.close()


def _git_ok(root: Path, *args: str) -> bool:
    return _git(root, *args, check=False).returncode == 0


def _split_command(command: str) -> list[str]:
    argv = shlex.split(command, posix=True)
    if argv and argv[0] in {"python", "python3"}:
        argv[0] = sys.executable
    return argv


def _run_argv(
    root: Path, argv: list[str], display_command: str
) -> subprocess.CompletedProcess[str]:
    if not argv:
        raise MergeQueueError(f"empty command: {display_command!r}")
    timeout = _command_timeout_seconds()
    try:
        return subprocess.run(
            argv,
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise CommandTimedOut(f"{display_command} exceeded {timeout}s") from exc
    except OSError as exc:
        raise CommandLaunchFailed(
            f"{display_command} could not start: {exc}"
        ) from exc


def _run_command(root: Path, command: str) -> subprocess.CompletedProcess[str]:
    return _run_argv(root, _split_command(command), command)


def _required_gate_argv(
    gate: dict[str, Any],
    *,
    task_id: str,
    branch: str,
    base: str,
) -> list[str]:
    values = {
        "task_id": task_id,
        "branch": branch,
        "base": base,
    }
    rendered: list[str] = []
    for argument in _split_command(str(gate["command"])):
        for placeholder, value in values.items():
            argument = argument.replace(f"{{{placeholder}}}", value)
        rendered.append(argument)
    return rendered


def changed_paths(root: Path, base: str, head: str = "HEAD") -> list[str]:
    result = _git(
        root,
        "diff",
        "--name-only",
        "--diff-filter=ACDMRTUXB",
        f"{base}...{head}",
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise MergeQueueError(
            f"required-gate diff cannot be computed for {base}...{head}: {detail}"
        )
    return sorted(
        {
            line.strip().replace("\\", "/")
            for line in (result.stdout or "").splitlines()
            if line.strip()
        }
    )


def _output_tail(result: subprocess.CompletedProcess[str]) -> str:
    combined = "\n".join(
        part.strip("\n") for part in (result.stdout or "", result.stderr or "") if part.strip()
    )
    lines = combined.splitlines()
    return "\n".join(lines[-OUTPUT_TAIL_LINES:])


def _safe_branch_name(branch: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", branch).strip("-") or "branch"


def feedback_path(root: Path, branch: str) -> Path:
    return (
        shared_state_root(root)
        / FEEDBACK_DIR_REL
        / f"feedback-{_safe_branch_name(branch)}.md"
    )


def write_feedback(
    root: Path,
    entry: dict[str, Any],
    stage: str,
    reason: str,
    output_tail: str,
    base_ref: str,
    required_gates: list[dict[str, Any]] | None = None,
) -> Path:
    path = feedback_path(root, str(entry["branch"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    verify_cmds = entry.get("narrow_verification_cmds") or [DEFAULT_VERIFY_CMD]
    lines = [
        f"# Merge queue feedback - {entry['branch']}",
        "",
        f"- branch: {entry['branch']}",
        f"- task_id: {entry.get('task_id', '')}",
        f"- claim_id: {entry.get('claim_id', '')}",
        f"- stage: {stage}",
        f"- failed_at: {_now_iso()}",
        f"- reason: {reason}",
        "",
        "## Output (tail)",
        "",
        "```",
        output_tail or "(no output captured)",
        "```",
        "",
        "## Next steps for the worker",
        "",
        f"1. Update your branch onto the integration base ({base_ref}) and",
        "   resolve any conflicts locally:",
        f"   git fetch && git rebase {base_ref} {entry['branch']}",
        "2. Re-run the narrow verification until it passes:",
    ]
    lines.extend(f"   {cmd}" for cmd in verify_cmds)
    if required_gates:
        lines.append("   Required host gates (cannot be overridden at enqueue):")
        lines.extend(
            f"   [{gate['id']}] {gate['command']}" for gate in required_gates
        )
    lines.extend(
        [
            "3. Re-enqueue the fixed branch:",
            f"   python scripts/merge_queue.py enqueue --branch {entry['branch']} "
            f"--task-id {entry.get('task_id', '')}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _split_base(root: Path, base: str) -> tuple[str | None, str]:
    """Return (remote, branch_part) for the integration base ref."""
    if "/" in base:
        candidate_remote, _, rest = base.partition("/")
        remotes = (_git(root, "remote", check=False).stdout or "").split()
        if candidate_remote in remotes and rest:
            return candidate_remote, rest
    return None, base


def _branch_exists(root: Path, branch: str) -> bool:
    return _git_ok(root, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}")


def _remote_branch_exists(root: Path, remote: str, branch: str) -> bool:
    return _git_ok(root, "rev-parse", "--verify", "--quiet", f"refs/remotes/{remote}/{branch}")


def _current_branch(root: Path) -> str:
    return (_git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout or "").strip()


def _checkout(root: Path, ref: str) -> None:
    _git(root, "checkout", ref)


def _restore_worktree(root: Path, ref: str) -> None:
    """Best-effort: abort in-progress rebase/merge and return to ``ref``."""
    git_dir = Path((_git(root, "rev-parse", "--git-dir").stdout or "").strip())
    if not git_dir.is_absolute():
        git_dir = root / git_dir
    if (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists():
        _git(root, "rebase", "--abort", check=False)
    if (git_dir / "MERGE_HEAD").exists():
        _git(root, "merge", "--abort", check=False)
    _git(root, "checkout", ref, check=False)


class ProcessContext:
    def __init__(
        self,
        root: Path,
        base: str,
        integration_branch: str | None,
        pr_mode: bool,
        regen_cmd: str,
    ) -> None:
        self.root = root
        self.base = base
        self.pr_mode = pr_mode
        self.regen_cmd = regen_cmd
        self.remote, base_branch = _split_base(root, base)
        self.integration_branch = integration_branch or base_branch
        # Rebase target: in local mode the integration branch accumulates the
        # batch's merges, so later entries stack on earlier ones; in PR mode
        # merges happen remotely, so the remote base ref is the target.
        self.rebase_target = base if pr_mode else self.integration_branch
        self.start_branch = ""
        self.required_gate_policy = _empty_merge_gate_policy()

    def preflight(self) -> None:
        if not _git_ok(self.root, "rev-parse", "--is-inside-work-tree"):
            raise MergeQueueError(f"not a git work tree: {self.root}")
        dirty = (
            _git(self.root, "status", "--porcelain", "--untracked-files=no").stdout or ""
        ).strip()
        if dirty:
            raise MergeQueueError(
                "tracked files are modified in the integrator checkout; "
                "commit or stash before processing the merge queue"
            )
        self.start_branch = _current_branch(self.root)
        if self.start_branch == "HEAD":
            raise MergeQueueError("integrator checkout is on a detached HEAD")
        state_root = shared_state_root(self.root)
        tracked = _git(
            state_root, "ls-files", "--error-unmatch", QUEUE_REL, check=False
        )
        if tracked.returncode == 0:
            _say(
                f"WARN {QUEUE_REL} is tracked by git; keep the merge_queue "
                "directory untracked so branch switches cannot conflict with "
                "live queue state"
            )
        if self.remote:
            self.fetch()
        if not self.pr_mode:
            self._sync_integration_branch()

    def fetch(self) -> None:
        if self.remote:
            _git(self.root, "fetch", self.remote)

    def _sync_integration_branch(self) -> None:
        branch = self.integration_branch
        if not _branch_exists(self.root, branch):
            if not _git_ok(self.root, "rev-parse", "--verify", "--quiet", self.base):
                raise MergeQueueError(
                    f"integration base {self.base!r} does not resolve; cannot "
                    f"create local integration branch {branch!r}"
                )
            _git(self.root, "branch", branch, self.base)
        _checkout(self.root, branch)
        if self.remote:
            # Fast-forward only: never rewrite the integration branch. If the
            # local branch is ahead (unpushed queue merges) this is a no-op;
            # if it diverged, stop and let the orchestrator resolve it.
            result = _git(self.root, "merge", "--ff-only", self.base, check=False)
            if result.returncode != 0:
                raise MergeQueueError(
                    f"integration branch {branch!r} diverged from {self.base!r}; "
                    "resolve manually before processing the queue"
                )


def _fail_entry(
    ctx: ProcessContext,
    root: Path,
    queue: dict[str, Any],
    entry: dict[str, Any],
    stage: str,
    reason: str,
    output_tail: str = "",
) -> None:
    entry["status"] = "failed"
    entry["failure_reason"] = reason
    entry["processed_at"] = _now_iso()
    save_queue(root, queue)
    path = write_feedback(
        root,
        entry,
        stage,
        reason,
        output_tail,
        ctx.rebase_target,
        ctx.required_gate_policy["gates"],
    )
    _say(f"FAILED {entry['branch']} at {stage}: {reason}")
    _say(f"feedback written: {path}")


def _print_pr_handoff(ctx: ProcessContext, entry: dict[str, Any], pushed: bool) -> None:
    branch = entry["branch"]
    task_id = entry.get("task_id", "")
    _say(f"PR handoff for {branch} (orchestrator runs these; not executed here):")
    if not pushed:
        _say(f"  git push {ctx.remote or 'origin'} {branch}")
        _say("  (plain push was rejected or skipped; the orchestrator decides "
             "how to publish the rebased branch -- this queue never force-pushes)")
    _say(
        f"  gh pr create --head {branch} --base {ctx.integration_branch} "
        f'--title "{task_id}: merge-queue join" --fill'
    )
    _say(f"  gh pr merge {branch} --merge")
    _say(f"  python scripts/merge_queue.py remove --branch {branch}  (after the PR merges)")


def process_entry(
    ctx: ProcessContext, queue: dict[str, Any], entry: dict[str, Any]
) -> bool:
    """Process one entry. Returns True when merged (or handed off in PR mode)."""
    try:
        return _process_entry(ctx, queue, entry)
    except CommandTimedOut as exc:
        try:
            _restore_worktree(ctx.root, ctx.start_branch)
        except CommandTimedOut:
            _say(f"WARN worktree restore also timed out for {entry['branch']}")
        _fail_entry(ctx, ctx.root, queue, entry, "timeout", f"timed-out: {exc}")
        return False


def _process_entry(
    ctx: ProcessContext, queue: dict[str, Any], entry: dict[str, Any]
) -> bool:
    root = ctx.root
    branch = str(entry["branch"])
    _say(f"processing {branch} ({entry.get('task_id', '')})")

    entry["status"] = "rebasing"
    entry["failure_reason"] = ""
    save_queue(root, queue)
    ctx.fetch()

    if not _branch_exists(root, branch):
        if ctx.remote and _remote_branch_exists(root, ctx.remote, branch):
            _git(root, "branch", branch, f"{ctx.remote}/{branch}")
        else:
            _fail_entry(ctx, root, queue, entry, "rebase", "branch-not-found")
            return False
    elif ctx.remote and _remote_branch_exists(root, ctx.remote, branch):
        # A worker may have pushed a fix since the local copy was created
        # (e.g. re-enqueue after a failed verification). Fast-forward only:
        # never rewrite local-ahead work, and git itself refuses to move a
        # branch that is checked out in another worktree.
        remote_ref = f"{ctx.remote}/{branch}"
        local_sha = (_git(root, "rev-parse", branch).stdout or "").strip()
        remote_sha = (_git(root, "rev-parse", remote_ref).stdout or "").strip()
        if local_sha != remote_sha and _git_ok(
            root, "merge-base", "--is-ancestor", branch, remote_ref
        ):
            _git(root, "branch", "-f", branch, remote_ref, check=False)

    try:
        _checkout(root, branch)
    except MergeQueueError as exc:
        _restore_worktree(root, ctx.start_branch)
        _fail_entry(ctx, root, queue, entry, "rebase", f"checkout-failed: {exc}")
        return False

    rebase = _git(root, "rebase", ctx.rebase_target, check=False)
    if rebase.returncode != 0:
        _restore_worktree(root, ctx.start_branch)
        detail = (rebase.stderr or rebase.stdout or "").strip().splitlines()
        reason = f"rebase-conflict onto {ctx.rebase_target}: " + (
            detail[-1] if detail else "unknown"
        )
        _fail_entry(ctx, root, queue, entry, "rebase", reason, _output_tail(rebase))
        return False

    diff_paths = changed_paths(root, ctx.rebase_target)
    protected_changes = protected_path_changes(
        ctx.required_gate_policy, diff_paths
    )
    if protected_changes:
        _restore_worktree(root, ctx.start_branch)
        reason = (
            "required-gate-protected-path-modified: gate control files are "
            "owned by the integration base; update them through an "
            "owner-controlled policy change, then re-enqueue: "
            + ", ".join(protected_changes)
        )
        _fail_entry(ctx, root, queue, entry, "required-gate-integrity", reason)
        return False

    entry["status"] = "testing"
    save_queue(root, queue)
    verify_cmds = entry.get("narrow_verification_cmds") or [DEFAULT_VERIFY_CMD]
    for command in verify_cmds:
        _say(f"  verify: {command}")
        result = _run_command(root, command)
        if result.returncode != 0:
            _restore_worktree(root, ctx.start_branch)
            reason = f"verification-failed: {command} (exit {result.returncode})"
            _fail_entry(ctx, root, queue, entry, "verify", reason, _output_tail(result))
            return False

    for gate in ctx.required_gate_policy["gates"]:
        gate_id = str(gate["id"])
        if not gate_applies(gate, diff_paths):
            _say(f"  required gate: {gate_id} (skipped: path filters)")
            continue
        command = str(gate["command"])
        argv = _required_gate_argv(
            gate,
            task_id=str(entry.get("task_id") or ""),
            branch=branch,
            base=ctx.rebase_target,
        )
        _say(f"  required gate: {gate_id}: {command}")
        try:
            result = _run_argv(root, argv, command)
        except CommandTimedOut as exc:
            _restore_worktree(root, ctx.start_branch)
            reason = f"required-gate-timed-out:{gate_id}: {exc}"
            _fail_entry(ctx, root, queue, entry, "required-gate", reason)
            return False
        except CommandLaunchFailed as exc:
            _restore_worktree(root, ctx.start_branch)
            reason = f"required-gate-launch-failed:{gate_id}: {exc}"
            _fail_entry(ctx, root, queue, entry, "required-gate", reason)
            return False
        if result.returncode != 0:
            _restore_worktree(root, ctx.start_branch)
            reason = (
                f"required-gate-failed:{gate_id}: {command} "
                f"(exit {result.returncode})"
            )
            _fail_entry(
                ctx,
                root,
                queue,
                entry,
                "required-gate",
                reason,
                _output_tail(result),
            )
            return False

    entry["status"] = "merging"
    save_queue(root, queue)

    if ctx.pr_mode:
        pushed = False
        if ctx.remote:
            push = _git(root, "push", ctx.remote, branch, check=False)
            pushed = push.returncode == 0
            if pushed:
                _say(f"  pushed {branch} to {ctx.remote}")
        _checkout(root, ctx.start_branch)
        # Terminal handoff status: distinct from "merging" so observers can
        # tell a completed PR handoff from a merge stuck mid-flight.
        entry["status"] = "pr-handoff"
        entry["processed_at"] = _now_iso()
        save_queue(root, queue)
        _print_pr_handoff(ctx, entry, pushed)
        return True

    _checkout(root, ctx.integration_branch)
    message = f"merge: {entry.get('task_id', '')} via merge-queue ({branch})"
    merge = _git(root, "merge", "--no-ff", "-m", message, branch, check=False)
    if merge.returncode != 0:
        _restore_worktree(root, ctx.integration_branch)
        detail = (merge.stderr or merge.stdout or "").strip().splitlines()
        reason = "merge-failed: " + (detail[-1] if detail else "unknown")
        _fail_entry(ctx, root, queue, entry, "merge", reason, _output_tail(merge))
        return False

    entry["status"] = "merged"
    entry["processed_at"] = _now_iso()
    save_queue(root, queue)
    _say(f"merged {branch} into {ctx.integration_branch}")
    return True


def _print_wave_hint(ctx: ProcessContext, merged_count: int) -> None:
    _say(f"wave boundary: batch fully merged ({merged_count} branch(es)).")
    _say("full-cycle follow-ups for the integrator:")
    _say(f"  {DEFAULT_REGEN_CMD}")
    _say("  python scripts/evidence_index_generator.py --write")
    _say("  (run the wave retro per AGENT_RUNTIME_PARALLEL_SESSION_PROTOCOL.md)")
    _say(
        f"  git push {ctx.remote or 'origin'} {ctx.integration_branch}  "
        "(orchestrator-only remote mutation)"
    )


def _depends_on_task_ids(entry: dict[str, Any]) -> list[str]:
    raw = entry.get("depends_on_task_ids", [])
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise MergeQueueError(
            f"dependency list must be an array for branch {entry.get('branch', '?')}"
        )
    result: list[str] = []
    for item in raw:
        value = str(item or "").strip()
        if not value:
            raise MergeQueueError(
                f"dependency task id must not be empty for branch "
                f"{entry.get('branch', '?')}"
            )
        if value not in result:
            result.append(value)
    return result


def _dependency_matches(
    queue: dict[str, Any], task_id: str
) -> list[dict[str, Any]]:
    return [
        entry
        for entry in queue["entries"]
        if str(entry.get("task_id") or "").strip() == task_id
    ]


def dependency_order(queue: dict[str, Any]) -> list[dict[str, Any]]:
    pending_rows = [
        (index, entry)
        for index, entry in enumerate(queue["entries"])
        if entry.get("status") == "pending"
    ]
    if not pending_rows:
        return []

    pending_by_task: dict[str, list[int]] = {}
    entries_by_index = {index: entry for index, entry in pending_rows}
    for index, entry in pending_rows:
        task_id = str(entry.get("task_id") or "").strip()
        if not task_id:
            raise MergeQueueError(
                f"dependency preflight failed: branch "
                f"{entry.get('branch', '?')} has no task id"
            )
        pending_by_task.setdefault(task_id, []).append(index)

    incoming: dict[int, set[int]] = {index: set() for index, _ in pending_rows}
    followers: dict[int, set[int]] = {index: set() for index, _ in pending_rows}
    problems: list[str] = []

    for index, entry in pending_rows:
        current_task = str(entry.get("task_id") or "").strip()
        for dependency in _depends_on_task_ids(entry):
            matches = _dependency_matches(queue, dependency)
            if not matches:
                problems.append(
                    f"unknown dependency {dependency} for {current_task}"
                )
                continue
            if any(
                str(match.get("status") or "") in DEPENDENCY_SUCCESS_STATUSES
                for match in matches
            ):
                continue
            predecessors = pending_by_task.get(dependency, [])
            if not predecessors:
                statuses = sorted(
                    {str(match.get("status") or "?") for match in matches}
                )
                problems.append(
                    f"unmet dependency {dependency} for {current_task} "
                    f"(status={','.join(statuses)})"
                )
                continue
            for predecessor in predecessors:
                incoming[index].add(predecessor)
                followers[predecessor].add(index)

    if problems:
        raise MergeQueueError(
            "dependency preflight failed: " + "; ".join(sorted(set(problems)))
        )

    ready = [index for index, edges in incoming.items() if not edges]
    heapq.heapify(ready)
    ordered_indices: list[int] = []
    while ready:
        index = heapq.heappop(ready)
        ordered_indices.append(index)
        for follower in sorted(followers[index]):
            incoming[follower].discard(index)
            if not incoming[follower]:
                heapq.heappush(ready, follower)

    if len(ordered_indices) != len(pending_rows):
        cycle_indices = sorted(set(incoming) - set(ordered_indices))
        cycle = ", ".join(
            f"{entries_by_index[index].get('task_id', '?')}"
            f"[{entries_by_index[index].get('branch', '?')}]"
            for index in cycle_indices
        )
        raise MergeQueueError(f"dependency preflight failed: cycle detected: {cycle}")

    return [entries_by_index[index] for index in ordered_indices]


def dependency_block_reason(
    queue: dict[str, Any], entry: dict[str, Any]
) -> str | None:
    current_task = str(entry.get("task_id") or "").strip() or "?"
    for dependency in _depends_on_task_ids(entry):
        matches = _dependency_matches(queue, dependency)
        if not matches:
            return f"unknown dependency {dependency} for {current_task}"
        if any(
            str(match.get("status") or "") in DEPENDENCY_SUCCESS_STATUSES
            for match in matches
        ):
            continue
        statuses = sorted({str(match.get("status") or "?") for match in matches})
        return (
            f"unmet dependency {dependency} for {current_task} "
            f"(status={','.join(statuses)})"
        )
    return None


def cmd_enqueue(args: argparse.Namespace) -> int:
    root = args.root
    queue = load_queue(root)
    required_policy = load_merge_gate_policy(root)
    branch = args.branch.strip()
    if not branch:
        _say("ERROR --branch must not be empty")
        return 1
    task_id = args.task_id.strip()
    if not task_id:
        _say("ERROR --task-id must not be empty")
        return 1
    dependencies: list[str] = []
    for raw in args.depends_on_task:
        dependency = raw.strip()
        if not dependency:
            _say("ERROR --depends-on-task must not be empty")
            return 1
        if dependency == task_id:
            _say(f"ERROR task {task_id} cannot depend on itself")
            return 1
        if dependency not in dependencies:
            dependencies.append(dependency)
    for entry in queue["entries"]:
        if entry.get("branch") == branch and entry.get("status") in ENQUEUE_BLOCKING_STATUSES:
            _say(
                f"ERROR branch {branch} already queued with status "
                f"{entry.get('status')}; remove it first to re-enqueue"
            )
            return 1
    entry = new_entry(
        branch,
        task_id,
        args.claim_id.strip(),
        args.verify,
        dependencies,
        required_policy,
    )
    queue["entries"].append(entry)
    save_queue(root, queue)
    verify_note = ", ".join(entry["narrow_verification_cmds"]) or f"default: {DEFAULT_VERIFY_CMD}"
    dependency_note = ", ".join(dependencies) or "none"
    required_note = ", ".join(entry.get("required_gate_ids", [])) or "none"
    _say(
        f"enqueued {branch} ({entry['task_id']}) "
        f"depends_on=[{dependency_note}] verify=[{verify_note}] "
        f"required_gates=[{required_note}]"
    )
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    root = args.root
    queue = load_queue(root)
    entries = queue["entries"]
    rel = queue_path(root)
    try:
        rel_text = rel.relative_to(root).as_posix()
    except ValueError:
        rel_text = str(rel)
    _say(f"queue: {rel_text} ({len(entries)} entries)")
    for index, entry in enumerate(entries, start=1):
        status = str(entry.get("status", "?"))
        extra = ""
        if status == "failed" and entry.get("failure_reason"):
            extra = f" reason={entry['failure_reason']}"
        elif entry.get("processed_at"):
            extra = f" processed={entry['processed_at']}"
        dependencies = ",".join(_depends_on_task_ids(entry)) or "-"
        required_gates = ",".join(entry.get("required_gate_ids", [])) or "-"
        print(
            f"  {index}. [{status:<8}] branch={entry.get('branch', '?')} "
            f"task={entry.get('task_id', '?')} enqueued={entry.get('enqueued_at', '?')}"
            f" depends_on={dependencies} required_gates={required_gates}{extra}"
        )
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    root = args.root
    queue = load_queue(root)
    branch = args.branch.strip()
    kept = [entry for entry in queue["entries"] if entry.get("branch") != branch]
    removed = len(queue["entries"]) - len(kept)
    if removed == 0:
        _say(f"ERROR branch {branch} not found in queue")
        return 1
    queue["entries"] = kept
    save_queue(root, queue)
    _say(f"removed {removed} entr{'y' if removed == 1 else 'ies'} for {branch}")
    return 0


def cmd_process(args: argparse.Namespace) -> int:
    root = args.root
    queue = load_queue(root)
    pending = dependency_order(queue)
    if not pending:
        _say("no pending entries")
        return 0
    if args.once:
        pending = pending[:1]

    if args.pr_mode:
        dependency_entries = [
            entry for entry in pending if _depends_on_task_ids(entry)
        ]
        if dependency_entries:
            tasks = ", ".join(
                str(entry.get("task_id") or "?") for entry in dependency_entries
            )
            raise MergeQueueError(
                "dependency-bearing entries cannot run in --pr-mode because "
                "a PR handoff does not prove the predecessor reached the remote "
                f"base (blocked tasks: {tasks}); merge predecessors first or "
                "use local serial mode"
            )

    if args.dry_run:
        dry_ctx = ProcessContext(
            root,
            args.base,
            args.integration_branch,
            args.pr_mode,
            args.regen_cmd,
        )
        policy_ref = dry_ctx.rebase_target
        if (
            not dry_ctx.pr_mode
            and not _branch_exists(root, dry_ctx.integration_branch)
        ):
            policy_ref = args.base
        required_policy = load_merge_gate_policy_from_ref(root, policy_ref)
        for entry in pending:
            validate_entry_gate_policy(entry, required_policy)
        mode = "pr" if args.pr_mode else "local"
        _say(
            f"dry-run: would process {len(pending)} entr"
            f"{'y' if len(pending) == 1 else 'ies'} "
            f"(base={args.base}, mode={mode}); nothing was mutated"
        )
        for index, entry in enumerate(pending, start=1):
            cmds = entry.get("narrow_verification_cmds") or [DEFAULT_VERIFY_CMD]
            diff_paths = (
                changed_paths(root, policy_ref, str(entry.get("branch") or ""))
                if required_policy["gates"]
                else []
            )
            applied = [
                gate["id"]
                for gate in required_policy["gates"]
                if gate_applies(gate, diff_paths)
            ]
            skipped = [
                gate["id"]
                for gate in required_policy["gates"]
                if gate["id"] not in applied
            ]
            _say(
                f"  {index}. {entry.get('branch')} ({entry.get('task_id')}) "
                f"verify=[{', '.join(cmds)}] "
                f"required=[{', '.join(applied) or '-'}] "
                f"skipped=[{', '.join(skipped) or '-'}]"
            )
        _say(f"  then board regen once: {args.regen_cmd}")
        return 0

    ctx = ProcessContext(root, args.base, args.integration_branch, args.pr_mode, args.regen_cmd)
    ctx.preflight()

    merged = 0
    failed = 0
    try:
        ctx.required_gate_policy = load_merge_gate_policy_from_ref(
            root, ctx.rebase_target
        )
        for entry in pending:
            validate_entry_gate_policy(entry, ctx.required_gate_policy)
        for entry in pending:
            blocked = dependency_block_reason(queue, entry)
            if blocked:
                _say(f"ERROR dependency changed before merge: {blocked}")
                failed += 1
                continue
            if process_entry(ctx, queue, entry):
                merged += 1
            else:
                failed += 1
    finally:
        _restore_worktree(root, ctx.start_branch)

    regen_failed = False
    if merged > 0:
        if ctx.pr_mode:
            _say(f"after the PRs merge, regenerate the board once: {ctx.regen_cmd}")
        else:
            _say(f"board regen (once per batch): {ctx.regen_cmd}")
            result = _run_command(root, ctx.regen_cmd)
            if result.returncode != 0:
                regen_failed = True
                _say(f"WARN board regen failed (exit {result.returncode})")

    remaining = [entry for entry in queue["entries"] if entry.get("status") == "pending"]
    _say(f"batch done: merged={merged} failed={failed} pending={len(remaining)}")
    if not ctx.pr_mode and merged > 0 and failed == 0 and not remaining:
        _print_wave_hint(ctx, merged)
    return 1 if failed or regen_failed else 0


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", type=Path, default=ROOT, help="repository root")

    parser = argparse.ArgumentParser(
        description="Integrator merge queue: serial rebase-test-merge for worker branches"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    enqueue = sub.add_parser("enqueue", parents=[common], help="add a branch to the queue")
    enqueue.add_argument("--branch", required=True)
    enqueue.add_argument("--task-id", required=True)
    enqueue.add_argument("--claim-id", default="")
    enqueue.add_argument(
        "--depends-on-task",
        action="append",
        default=[],
        help=(
            "queue-local predecessor task id (repeatable); predecessor entries "
            "must remain in queue history until this entry is processed"
        ),
    )
    enqueue.add_argument(
        "--verify",
        action="append",
        default=[],
        help=f"narrow verification command (repeatable; default: {DEFAULT_VERIFY_CMD})",
    )
    enqueue.set_defaults(func=cmd_enqueue)

    listing = sub.add_parser("list", parents=[common], help="show queue entries")
    listing.set_defaults(func=cmd_list)

    process = sub.add_parser("process", parents=[common], help="process pending entries")
    group = process.add_mutually_exclusive_group()
    group.add_argument("--once", action="store_true", help="process only the first pending entry")
    group.add_argument("--all", action="store_true", help="process every pending entry (default)")
    process.add_argument("--dry-run", action="store_true", help="print the plan; mutate nothing")
    process.add_argument("--base", default=DEFAULT_BASE, help="integration base ref")
    process.add_argument(
        "--integration-branch",
        default=None,
        help="local integration branch (default: base without its remote prefix)",
    )
    process.add_argument(
        "--pr-mode",
        action="store_true",
        help="push rebased branches and print gh pr commands instead of merging locally",
    )
    process.add_argument(
        "--regen-cmd",
        default=DEFAULT_REGEN_CMD,
        help="board regeneration command, run once per processed batch",
    )
    process.set_defaults(func=cmd_process)

    remove = sub.add_parser("remove", parents=[common], help="remove a branch from the queue")
    remove.add_argument("--branch", required=True)
    remove.set_defaults(func=cmd_remove)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.root = Path(args.root).resolve()
    try:
        mutates = args.command in {"enqueue", "remove"} or (
            args.command == "process" and not args.dry_run
        )
        if not mutates:
            return int(args.func(args))
        with exclusive_queue_lock(args.root, args.command):
            return int(args.func(args))
    except MergeQueueError as exc:
        _say(f"ERROR {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
