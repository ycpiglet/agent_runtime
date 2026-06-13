"""Integrator merge queue: serial rebase-test-merge for worker branches.

Not concurrent-safe: run at most one process invocation at a time.

Parallel waves end with N worker branches waiting to join main. Unordered
joins create rebase races and shared-SSoT regeneration contention
(board/INDEX/BACKLOG). This script encodes the orchestrator's manually proven
flow (PRs #45-#53) as a single-integrator serial queue:

  enqueue -> [per entry] fetch -> rebase onto the integration base -> narrow
  verification -> merge (local mode) or print PR commands (--pr-mode) -> next
  entry -> regenerate the board once per processed batch.

Queue state lives at ``agents/runtime/merge_queue/queue.json`` (schema
``agent-runtime-merge-queue/v1``) so ui-console can observe progress. A
failing entry is marked ``failed`` with a reason plus a worker feedback file
(``agents/runtime/merge_queue/feedback-<branch>.md``); the queue continues
with the next entry and never poisons the integration branch.

Safety invariants:
  - never force-pushes; never deletes branches;
  - failed rebases/merges are aborted and the work tree is restored;
  - ``--pr-mode`` performs no remote merge: it pushes the rebased branch only
    when the push is a plain fast-forward/new ref and PRINTS the ``gh``
    commands for the orchestrator instead of executing them;
  - ``--dry-run`` mutates nothing (no git commands, no queue writes).

Usage:
  python scripts/merge_queue.py enqueue --branch B --task-id T
      [--claim-id C] [--verify CMD]...
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
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
QUEUE_REL = "agents/runtime/merge_queue/queue.json"
FEEDBACK_DIR_REL = "agents/runtime/merge_queue"
SCHEMA = "agent-runtime-merge-queue/v1"
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


class MergeQueueError(Exception):
    """Environmental or preflight error that aborts the current command."""


class CommandTimedOut(MergeQueueError):
    """A bounded subprocess exceeded the configured timeout."""


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
    return root / QUEUE_REL


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
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def new_entry(
    branch: str,
    task_id: str,
    claim_id: str = "",
    verify_cmds: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "branch": branch,
        "task_id": task_id,
        "claim_id": claim_id,
        "narrow_verification_cmds": list(verify_cmds or []),
        "enqueued_at": _now_iso(),
        "status": "pending",
        "failure_reason": "",
        "processed_at": "",
    }


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


def _git_ok(root: Path, *args: str) -> bool:
    return _git(root, *args, check=False).returncode == 0


def _split_command(command: str) -> list[str]:
    argv = shlex.split(command, posix=True)
    if argv and argv[0] in {"python", "python3"}:
        argv[0] = sys.executable
    return argv


def _run_command(root: Path, command: str) -> subprocess.CompletedProcess[str]:
    argv = _split_command(command)
    if not argv:
        raise MergeQueueError(f"empty command: {command!r}")
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
        raise CommandTimedOut(f"{command} exceeded {timeout}s") from exc


def _output_tail(result: subprocess.CompletedProcess[str]) -> str:
    combined = "\n".join(
        part.strip("\n") for part in (result.stdout or "", result.stderr or "") if part.strip()
    )
    lines = combined.splitlines()
    return "\n".join(lines[-OUTPUT_TAIL_LINES:])


def _safe_branch_name(branch: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", branch).strip("-") or "branch"


def feedback_path(root: Path, branch: str) -> Path:
    return root / FEEDBACK_DIR_REL / f"feedback-{_safe_branch_name(branch)}.md"


def write_feedback(
    root: Path,
    entry: dict[str, Any],
    stage: str,
    reason: str,
    output_tail: str,
    base_ref: str,
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
        tracked = _git(
            self.root, "ls-files", "--error-unmatch", QUEUE_REL, check=False
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
    path = write_feedback(root, entry, stage, reason, output_tail, ctx.rebase_target)
    _say(f"FAILED {entry['branch']} at {stage}: {reason}")
    _say(f"feedback written: {path.relative_to(root).as_posix()}")


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


def cmd_enqueue(args: argparse.Namespace) -> int:
    root = args.root
    queue = load_queue(root)
    branch = args.branch.strip()
    if not branch:
        _say("ERROR --branch must not be empty")
        return 1
    for entry in queue["entries"]:
        if entry.get("branch") == branch and entry.get("status") in ENQUEUE_BLOCKING_STATUSES:
            _say(
                f"ERROR branch {branch} already queued with status "
                f"{entry.get('status')}; remove it first to re-enqueue"
            )
            return 1
    entry = new_entry(branch, args.task_id.strip(), args.claim_id.strip(), args.verify)
    queue["entries"].append(entry)
    save_queue(root, queue)
    verify_note = ", ".join(entry["narrow_verification_cmds"]) or f"default: {DEFAULT_VERIFY_CMD}"
    _say(f"enqueued {branch} ({entry['task_id']}) verify=[{verify_note}]")
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
        print(
            f"  {index}. [{status:<8}] branch={entry.get('branch', '?')} "
            f"task={entry.get('task_id', '?')} enqueued={entry.get('enqueued_at', '?')}"
            f"{extra}"
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
    pending = [entry for entry in queue["entries"] if entry.get("status") == "pending"]
    if not pending:
        _say("no pending entries")
        return 0
    if args.once:
        pending = pending[:1]

    if args.dry_run:
        mode = "pr" if args.pr_mode else "local"
        _say(
            f"dry-run: would process {len(pending)} entr"
            f"{'y' if len(pending) == 1 else 'ies'} "
            f"(base={args.base}, mode={mode}); nothing was mutated"
        )
        for index, entry in enumerate(pending, start=1):
            cmds = entry.get("narrow_verification_cmds") or [DEFAULT_VERIFY_CMD]
            _say(
                f"  {index}. {entry.get('branch')} ({entry.get('task_id')}) "
                f"verify=[{', '.join(cmds)}]"
            )
        _say(f"  then board regen once: {args.regen_cmd}")
        return 0

    ctx = ProcessContext(root, args.base, args.integration_branch, args.pr_mode, args.regen_cmd)
    ctx.preflight()

    merged = 0
    failed = 0
    try:
        for entry in pending:
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
        return int(args.func(args))
    except MergeQueueError as exc:
        _say(f"ERROR {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
