from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from scripts import merge_queue as merge_queue_module


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "merge_queue.py"
TEMPLATE_SCRIPT = (
    REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "merge_queue.py"
)
QUEUE_REL = Path("agents/runtime/merge_queue/queue.json")

PASS_VERIFY = "python -c \"print('verify-ok')\""
FAIL_VERIFY = 'python -c "import sys; sys.exit(3)"'
# Appends one character per invocation so the tests can count batch regens.
REGEN_CMD = "python -c \"open('regen.log','a').write('x')\""


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return (result.stdout or "").strip()


def _mq_argv(root: Path, *args: str) -> list[str]:
    return [sys.executable, str(SCRIPT), *args, "--root", str(root)]


def _run_mq(root: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        _mq_argv(root, *args),
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env={**os.environ, **env} if env else None,
    )


def _start_lock_holder(
    root: Path, ready_path: Path, hold_seconds: float
) -> subprocess.Popen[str]:
    code = "\n".join(
        [
            "import sys, time",
            "from pathlib import Path",
            f"sys.path.insert(0, {str(REPO_ROOT)!r})",
            "from scripts.merge_queue import exclusive_queue_lock",
            (
                f"with exclusive_queue_lock(Path({str(root)!r}), "
                f"{'test-holder'!r}):"
            ),
            f"    Path({str(ready_path)!r}).write_text('ready', encoding='utf-8')",
            f"    time.sleep({hold_seconds!r})",
        ]
    )
    return subprocess.Popen(
        [sys.executable, "-c", code],
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _wait_for_path(path: Path, timeout: float = 3.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.01)
    raise AssertionError(f"timed out waiting for {path}")


def _make_repos(tmp_path: Path) -> Path:
    """Create a bare origin plus a clone with one pushed commit on main."""
    origin = tmp_path / "origin.git"
    origin.mkdir()
    _git(origin, "init", "--bare")
    _git(origin, "symbolic-ref", "HEAD", "refs/heads/main")
    work = tmp_path / "work"
    _git(tmp_path, "clone", str(origin), str(work))
    _git(work, "config", "user.email", "queue@test.local")
    _git(work, "config", "user.name", "Merge Queue Test")
    (work / "README.md").write_text("base\n", encoding="utf-8")
    _git(work, "add", "README.md")
    _git(work, "commit", "-m", "init")
    _git(work, "push", "-u", "origin", "main")
    return work


def _make_branch(work: Path, name: str, filename: str, content: str = "payload\n") -> None:
    _git(work, "checkout", "-b", name, "main")
    path = work / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    _git(work, "add", filename)
    _git(work, "commit", "-m", f"add {filename}")
    _git(work, "checkout", "main")


def _queue(work: Path) -> dict:
    return json.loads(
        merge_queue_module.queue_path(work).read_text(encoding="utf-8")
    )


def _write_policy(
    work: Path,
    gates: list[dict[str, object]],
    *,
    commit: bool = True,
    protected_paths: list[str] | None = None,
) -> Path:
    path = work / merge_queue_module.MERGE_GATES_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": merge_queue_module.MERGE_GATES_SCHEMA,
                "protected_paths": protected_paths
                or [merge_queue_module.MERGE_GATES_REL],
                "gates": gates,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if commit:
        _git(work, "add", merge_queue_module.MERGE_GATES_REL)
        _git(work, "commit", "-m", "configure required merge gates")
        _git(work, "push")
    return path


def test_three_disjoint_branches_merge_serially_with_one_board_regen(tmp_path: Path):
    work = _make_repos(tmp_path)
    for index in (1, 2, 3):
        _make_branch(work, f"feat/b{index}", f"file{index}.txt")
        result = _run_mq(
            work,
            "enqueue",
            "--branch",
            f"feat/b{index}",
            "--task-id",
            f"TASK-{index}",
            "--verify",
            PASS_VERIFY,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    result = _run_mq(work, "process", "--all", "--regen-cmd", REGEN_CMD)
    assert result.returncode == 0, result.stdout + result.stderr

    payload = _queue(work)
    assert payload["schema"] == "agent-runtime-merge-queue/v1"
    assert [entry["status"] for entry in payload["entries"]] == ["merged"] * 3
    assert all(entry["processed_at"] for entry in payload["entries"])

    assert _git(work, "rev-parse", "--abbrev-ref", "HEAD") == "main"
    for index in (1, 2, 3):
        assert (work / f"file{index}.txt").exists()
    assert _git(work, "rev-list", "--merges", "--count", "main") == "3"

    # Board regen runs exactly once per processed batch.
    assert (work / "regen.log").read_text(encoding="utf-8") == "x"
    assert "wave boundary" in result.stdout


def test_failing_verification_writes_feedback_and_keeps_main_clean(tmp_path: Path):
    work = _make_repos(tmp_path)
    _make_branch(work, "feat/bad", "bad.txt")
    _make_branch(work, "feat/good", "good.txt")
    _run_mq(work, "enqueue", "--branch", "feat/bad", "--task-id", "TASK-BAD", "--verify", FAIL_VERIFY)
    _run_mq(work, "enqueue", "--branch", "feat/good", "--task-id", "TASK-GOOD", "--verify", PASS_VERIFY)

    result = _run_mq(work, "process", "--all", "--regen-cmd", REGEN_CMD)
    assert result.returncode == 1, result.stdout + result.stderr

    entries = {entry["branch"]: entry for entry in _queue(work)["entries"]}
    assert entries["feat/bad"]["status"] == "failed"
    assert "exit 3" in entries["feat/bad"]["failure_reason"]
    assert entries["feat/good"]["status"] == "merged"

    feedback = work / "agents/runtime/merge_queue/feedback-feat-bad.md"
    assert feedback.exists()
    text = feedback.read_text(encoding="utf-8")
    assert "exit 3" in text
    assert "Next steps for the worker" in text

    # The failed branch never reaches main; the queue continued past it.
    assert _git(work, "rev-parse", "--abbrev-ref", "HEAD") == "main"
    assert not (work / "bad.txt").exists()
    assert (work / "good.txt").exists()
    assert _git(work, "rev-list", "--merges", "--count", "main") == "1"
    # Regen still runs exactly once for the partially merged batch.
    assert (work / "regen.log").read_text(encoding="utf-8") == "x"
    assert "wave boundary" not in result.stdout


def test_rebase_conflict_marks_failed_with_reason(tmp_path: Path):
    work = _make_repos(tmp_path)
    (work / "conflict.txt").write_text("base\n", encoding="utf-8")
    _git(work, "add", "conflict.txt")
    _git(work, "commit", "-m", "add conflict file")
    _git(work, "push")

    _make_branch(work, "feat/conflict", "conflict.txt", "branch change\n")
    (work / "conflict.txt").write_text("main change\n", encoding="utf-8")
    _git(work, "add", "conflict.txt")
    _git(work, "commit", "-m", "main change")
    _git(work, "push")
    main_before = _git(work, "rev-parse", "main")

    _run_mq(work, "enqueue", "--branch", "feat/conflict", "--task-id", "TASK-C", "--verify", PASS_VERIFY)
    result = _run_mq(work, "process", "--all", "--regen-cmd", REGEN_CMD)
    assert result.returncode == 1, result.stdout + result.stderr

    entry = _queue(work)["entries"][0]
    assert entry["status"] == "failed"
    assert entry["failure_reason"].startswith("rebase-conflict")
    assert (work / "agents/runtime/merge_queue/feedback-feat-conflict.md").exists()

    # The rebase was aborted and the work tree restored; main is untouched.
    assert _git(work, "status", "--porcelain", "--untracked-files=no") == ""
    assert _git(work, "rev-parse", "--abbrev-ref", "HEAD") == "main"
    assert _git(work, "rev-parse", "main") == main_before
    assert not (work / "regen.log").exists()


def test_dry_run_mutates_nothing(tmp_path: Path):
    work = _make_repos(tmp_path)
    _make_branch(work, "feat/one", "one.txt")
    _make_branch(work, "feat/two", "two.txt")
    for branch in ("feat/one", "feat/two"):
        _run_mq(work, "enqueue", "--branch", branch, "--task-id", "TASK-X", "--verify", PASS_VERIFY)
    queue_before = (work / QUEUE_REL).read_text(encoding="utf-8")
    main_before = _git(work, "rev-parse", "main")

    result = _run_mq(work, "process", "--all", "--dry-run", "--regen-cmd", REGEN_CMD)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "dry-run" in result.stdout
    assert "feat/one" in result.stdout and "feat/two" in result.stdout

    assert (work / QUEUE_REL).read_text(encoding="utf-8") == queue_before
    assert _git(work, "rev-parse", "main") == main_before
    assert [entry["status"] for entry in _queue(work)["entries"]] == ["pending", "pending"]
    assert not (work / "regen.log").exists()
    assert list((work / "agents/runtime/merge_queue").glob("feedback-*.md")) == []


def test_stale_local_branch_fast_forwards_to_pushed_fix(tmp_path: Path):
    work = _make_repos(tmp_path)
    _make_branch(work, "feat/fix", "fix.txt")
    _git(work, "push", "origin", "feat/fix")
    # Simulate a stale local copy (e.g. left behind by a previous failed run):
    # the worker's pushed fix is ahead of the local branch.
    _git(work, "branch", "-f", "feat/fix", "main")

    _run_mq(work, "enqueue", "--branch", "feat/fix", "--task-id", "TASK-F", "--verify", PASS_VERIFY)
    result = _run_mq(work, "process", "--all", "--regen-cmd", REGEN_CMD)
    assert result.returncode == 0, result.stdout + result.stderr

    # The merge picked up the pushed fix, not the stale local copy.
    assert _queue(work)["entries"][0]["status"] == "merged"
    assert (work / "fix.txt").exists()


def test_verification_timeout_fails_entry_with_timed_out_reason(tmp_path: Path):
    work = _make_repos(tmp_path)
    _make_branch(work, "feat/slow", "slow.txt")
    slow_verify = 'python -c "import time; time.sleep(30)"'
    _run_mq(work, "enqueue", "--branch", "feat/slow", "--task-id", "TASK-SLOW", "--verify", slow_verify)

    result = _run_mq(
        work,
        "process",
        "--all",
        "--regen-cmd",
        REGEN_CMD,
        env={"MERGE_QUEUE_TIMEOUT_SECONDS": "2"},
    )
    assert result.returncode == 1, result.stdout + result.stderr

    entry = _queue(work)["entries"][0]
    assert entry["status"] == "failed"
    assert entry["failure_reason"].startswith("timed-out")
    assert (work / "agents/runtime/merge_queue/feedback-feat-slow.md").exists()

    # The worktree was restored and main never received the branch.
    assert _git(work, "rev-parse", "--abbrev-ref", "HEAD") == "main"
    assert _git(work, "status", "--porcelain", "--untracked-files=no") == ""
    assert not (work / "slow.txt").exists()


def test_pr_mode_marks_entry_pr_handoff_and_blocks_reenqueue(tmp_path: Path):
    work = _make_repos(tmp_path)
    _make_branch(work, "feat/pr", "pr.txt")
    _run_mq(work, "enqueue", "--branch", "feat/pr", "--task-id", "TASK-PR", "--verify", PASS_VERIFY)

    result = _run_mq(work, "process", "--all", "--pr-mode", "--regen-cmd", REGEN_CMD)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "gh pr create" in result.stdout

    entry = _queue(work)["entries"][0]
    assert entry["status"] == "pr-handoff"  # terminal handoff, not "merging"
    assert entry["processed_at"]

    # No local merge happened; the gh commands were only printed.
    assert _git(work, "rev-list", "--merges", "--count", "main") == "0"

    # A pr-handoff entry still blocks re-enqueue until it is removed.
    duplicate = _run_mq(work, "enqueue", "--branch", "feat/pr", "--task-id", "TASK-PR")
    assert duplicate.returncode == 1
    assert "already queued" in duplicate.stdout

    removed = _run_mq(work, "remove", "--branch", "feat/pr")
    assert removed.returncode == 0
    assert _queue(work)["entries"] == []


def test_pr_mode_rejects_dependency_bearing_batch_before_mutation(tmp_path: Path):
    work = _make_repos(tmp_path)
    _make_branch(work, "feat/dependent", "dependent.txt")
    _make_branch(work, "feat/predecessor", "predecessor.txt")
    _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/dependent",
        "--task-id",
        "TASK-DEPENDENT",
        "--depends-on-task",
        "TASK-PREDECESSOR",
        "--verify",
        PASS_VERIFY,
    )
    _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/predecessor",
        "--task-id",
        "TASK-PREDECESSOR",
        "--verify",
        PASS_VERIFY,
    )
    queue_before = merge_queue_module.queue_path(work).read_bytes()
    main_before = _git(work, "rev-parse", "main")

    result = _run_mq(work, "process", "--all", "--pr-mode")

    assert result.returncode == 2
    assert "dependency-bearing entries cannot run in --pr-mode" in result.stdout
    assert merge_queue_module.queue_path(work).read_bytes() == queue_before
    assert _git(work, "rev-parse", "main") == main_before
    assert [entry["status"] for entry in _queue(work)["entries"]] == [
        "pending",
        "pending",
    ]


def test_failed_push_pr_handoff_does_not_satisfy_later_dependency(tmp_path: Path):
    work = _make_repos(tmp_path)
    _make_branch(work, "feat/predecessor", "predecessor.txt")
    _make_branch(work, "feat/dependent", "dependent.txt")
    missing_push_remote = tmp_path / "missing" / "origin.git"
    _git(work, "remote", "set-url", "--push", "origin", str(missing_push_remote))
    _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/predecessor",
        "--task-id",
        "TASK-PREDECESSOR",
        "--verify",
        PASS_VERIFY,
    )

    handoff = _run_mq(work, "process", "--once", "--pr-mode")

    assert handoff.returncode == 0, handoff.stdout + handoff.stderr
    assert "plain push was rejected or skipped" in handoff.stdout
    assert _queue(work)["entries"][0]["status"] == "pr-handoff"
    _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/dependent",
        "--task-id",
        "TASK-DEPENDENT",
        "--depends-on-task",
        "TASK-PREDECESSOR",
        "--verify",
        PASS_VERIFY,
    )
    main_before = _git(work, "rev-parse", "main")

    blocked = _run_mq(work, "process", "--all")

    assert blocked.returncode == 2
    assert "unmet dependency TASK-PREDECESSOR" in blocked.stdout
    assert "status=pr-handoff" in blocked.stdout
    assert _git(work, "rev-parse", "main") == main_before
    assert not (work / "dependent.txt").exists()


def test_module_enforces_cross_process_boundary_and_template_mirror():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "Not concurrent-safe" not in text
    assert "exclusive_queue_lock" in text
    assert "os.replace" in text
    assert text == TEMPLATE_SCRIPT.read_text(encoding="utf-8")


def test_enqueue_rejects_duplicate_active_branch_and_remove_clears_it(tmp_path: Path):
    work = _make_repos(tmp_path)
    first = _run_mq(work, "enqueue", "--branch", "feat/x", "--task-id", "T1")
    assert first.returncode == 0, first.stdout + first.stderr
    duplicate = _run_mq(work, "enqueue", "--branch", "feat/x", "--task-id", "T1")
    assert duplicate.returncode == 1
    assert "already queued" in duplicate.stdout

    listing = _run_mq(work, "list")
    assert listing.returncode == 0
    assert "feat/x" in listing.stdout
    assert "pending" in listing.stdout

    removed = _run_mq(work, "remove", "--branch", "feat/x")
    assert removed.returncode == 0
    assert _queue(work)["entries"] == []
    missing = _run_mq(work, "remove", "--branch", "feat/x")
    assert missing.returncode == 1


def test_lock_queue_and_feedback_paths_are_shared_by_linked_worktrees(tmp_path: Path):
    work = _make_repos(tmp_path)
    linked = tmp_path / "linked"
    _git(work, "worktree", "add", "-b", "feat/linked", str(linked), "main")

    assert merge_queue_module.queue_lock_path(work) == merge_queue_module.queue_lock_path(
        linked
    )
    assert merge_queue_module.queue_path(work) == merge_queue_module.queue_path(linked)
    assert merge_queue_module.queue_path(work) == work.resolve() / QUEUE_REL
    assert merge_queue_module.feedback_path(
        work, "feat/example"
    ) == merge_queue_module.feedback_path(linked, "feat/example")


def test_linked_worktree_enqueues_are_serialized_without_lost_updates(tmp_path: Path):
    work = _make_repos(tmp_path)
    linked = tmp_path / "linked"
    _git(work, "worktree", "add", "-b", "feat/linked", str(linked), "main")
    ready = tmp_path / "lock-ready"
    holder = _start_lock_holder(work, ready, 0.35)
    _wait_for_path(ready)
    env = {**os.environ, "MERGE_QUEUE_LOCK_TIMEOUT_SECONDS": "2"}

    processes = [
        subprocess.Popen(
            _mq_argv(
                invocation_root,
                "enqueue",
                "--branch",
                f"feat/concurrent-{index}",
                "--task-id",
                f"TASK-CONCURRENT-{index}",
            ),
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        for index, invocation_root in ((1, work), (2, linked))
    ]
    results = [process.communicate(timeout=5) for process in processes]
    holder_output = holder.communicate(timeout=5)

    assert holder.returncode == 0, "".join(holder_output)
    for process, output in zip(processes, results, strict=True):
        assert process.returncode == 0, "".join(output)
    assert {
        entry["branch"] for entry in _queue(work)["entries"]
    } == {"feat/concurrent-1", "feat/concurrent-2"}
    listing = _run_mq(linked, "list")
    assert listing.returncode == 0, listing.stdout + listing.stderr
    assert "feat/concurrent-1" in listing.stdout
    assert "feat/concurrent-2" in listing.stdout
    assert not (linked / QUEUE_REL).exists()


def test_non_finite_lock_timeout_falls_back_to_bounded_default(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("MERGE_QUEUE_LOCK_TIMEOUT_SECONDS", "inf")
    assert (
        merge_queue_module._lock_timeout_seconds()
        == merge_queue_module.DEFAULT_LOCK_TIMEOUT_SECONDS
    )


def test_competing_mutator_times_out_with_actionable_lock_error(tmp_path: Path):
    work = _make_repos(tmp_path)
    ready = tmp_path / "lock-ready"
    holder = _start_lock_holder(work, ready, 0.6)
    _wait_for_path(ready)

    result = _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/blocked",
        "--task-id",
        "TASK-BLOCKED",
        env={"MERGE_QUEUE_LOCK_TIMEOUT_SECONDS": "0.1"},
    )
    holder_output = holder.communicate(timeout=5)

    assert holder.returncode == 0, "".join(holder_output)
    assert result.returncode == 2
    assert "lock busy" in result.stdout
    assert merge_queue_module.LOCK_FILENAME in result.stdout
    assert "wait for the active" in result.stdout
    assert not (work / QUEUE_REL).exists()


def test_atomic_save_failure_preserves_last_valid_queue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    work = _make_repos(tmp_path)
    result = _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/existing",
        "--task-id",
        "TASK-EXISTING",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    path = work / QUEUE_REL
    before = path.read_bytes()
    payload = _queue(work)
    payload["entries"].append(
        merge_queue_module.new_entry("feat/new", "TASK-NEW")
    )

    def fail_replace(_source: object, _destination: object) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr(merge_queue_module.os, "replace", fail_replace)
    with pytest.raises(merge_queue_module.MergeQueueError, match="atomic write failed"):
        merge_queue_module.save_queue(work, payload)

    assert path.read_bytes() == before
    assert json.loads(path.read_text(encoding="utf-8"))["entries"][0][
        "branch"
    ] == "feat/existing"
    assert list(path.parent.glob(f".{path.name}.*.tmp")) == []


def test_dry_run_creates_no_lock_and_mutates_no_queue_state(tmp_path: Path):
    work = _make_repos(tmp_path)
    path = work / QUEUE_REL
    path.parent.mkdir(parents=True)
    payload = merge_queue_module._empty_queue()
    payload["entries"].append(
        merge_queue_module.new_entry("feat/dry", "TASK-DRY")
    )
    merge_queue_module.save_queue(work, payload)
    before = path.read_bytes()
    lock_path = merge_queue_module.queue_lock_path(work)
    assert not lock_path.exists()

    result = _run_mq(work, "process", "--all", "--dry-run")

    assert result.returncode == 0, result.stdout + result.stderr
    assert path.read_bytes() == before
    assert not lock_path.exists()


def test_dependencies_override_fifo_with_stable_topological_order(tmp_path: Path):
    work = _make_repos(tmp_path)
    _make_branch(work, "feat/dependent", "dependent.txt")
    _make_branch(work, "feat/predecessor", "predecessor.txt")
    dependent = _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/dependent",
        "--task-id",
        "TASK-DEPENDENT",
        "--depends-on-task",
        "TASK-PREDECESSOR",
        "--verify",
        PASS_VERIFY,
    )
    predecessor = _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/predecessor",
        "--task-id",
        "TASK-PREDECESSOR",
        "--verify",
        PASS_VERIFY,
    )
    assert dependent.returncode == predecessor.returncode == 0

    result = _run_mq(work, "process", "--all", "--regen-cmd", REGEN_CMD)

    assert result.returncode == 0, result.stdout + result.stderr
    merge_subjects = _git(work, "log", "--merges", "-2", "--format=%s").splitlines()
    assert "TASK-DEPENDENT" in merge_subjects[0]
    assert "TASK-PREDECESSOR" in merge_subjects[1]
    assert (work / "predecessor.txt").exists()
    assert (work / "dependent.txt").exists()


def test_unknown_dependency_blocks_before_git_or_queue_mutation(tmp_path: Path):
    work = _make_repos(tmp_path)
    _make_branch(work, "feat/dependent", "dependent.txt")
    enqueued = _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/dependent",
        "--task-id",
        "TASK-DEPENDENT",
        "--depends-on-task",
        "TASK-MISSING",
        "--verify",
        PASS_VERIFY,
    )
    assert enqueued.returncode == 0
    queue_before = (work / QUEUE_REL).read_bytes()
    main_before = _git(work, "rev-parse", "main")

    result = _run_mq(work, "process", "--all", "--regen-cmd", REGEN_CMD)

    assert result.returncode == 2
    assert "unknown dependency TASK-MISSING" in result.stdout
    assert (work / QUEUE_REL).read_bytes() == queue_before
    assert _git(work, "rev-parse", "main") == main_before
    assert _git(work, "rev-parse", "--abbrev-ref", "HEAD") == "main"
    assert not (work / "dependent.txt").exists()


def test_dependency_cycle_blocks_without_mutating_main(tmp_path: Path):
    work = _make_repos(tmp_path)
    _make_branch(work, "feat/a", "a.txt")
    _make_branch(work, "feat/b", "b.txt")
    _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/a",
        "--task-id",
        "TASK-A",
        "--depends-on-task",
        "TASK-B",
    )
    _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/b",
        "--task-id",
        "TASK-B",
        "--depends-on-task",
        "TASK-A",
    )
    queue_before = (work / QUEUE_REL).read_bytes()
    main_before = _git(work, "rev-parse", "main")

    result = _run_mq(work, "process", "--all")

    assert result.returncode == 2
    assert "cycle detected" in result.stdout
    assert (work / QUEUE_REL).read_bytes() == queue_before
    assert _git(work, "rev-parse", "main") == main_before
    assert not (work / "a.txt").exists()
    assert not (work / "b.txt").exists()


def test_previously_failed_dependency_is_unmet_before_preflight(tmp_path: Path):
    work = _make_repos(tmp_path)
    _make_branch(work, "feat/bad", "bad.txt")
    _make_branch(work, "feat/dependent", "dependent.txt")
    _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/bad",
        "--task-id",
        "TASK-BAD",
        "--verify",
        FAIL_VERIFY,
    )
    failed = _run_mq(work, "process", "--once", "--regen-cmd", REGEN_CMD)
    assert failed.returncode == 1
    _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/dependent",
        "--task-id",
        "TASK-DEPENDENT",
        "--depends-on-task",
        "TASK-BAD",
        "--verify",
        PASS_VERIFY,
    )
    queue_before = (work / QUEUE_REL).read_bytes()
    main_before = _git(work, "rev-parse", "main")

    result = _run_mq(work, "process", "--all", "--regen-cmd", REGEN_CMD)

    assert result.returncode == 2
    assert "unmet dependency TASK-BAD" in result.stdout
    assert "status=failed" in result.stdout
    assert (work / QUEUE_REL).read_bytes() == queue_before
    assert _git(work, "rev-parse", "main") == main_before
    assert not (work / "dependent.txt").exists()


def test_failed_predecessor_leaves_dependent_pending_but_merges_independent(
    tmp_path: Path,
):
    work = _make_repos(tmp_path)
    _make_branch(work, "feat/dependent", "dependent.txt")
    _make_branch(work, "feat/bad", "bad.txt")
    _make_branch(work, "feat/independent", "independent.txt")
    _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/dependent",
        "--task-id",
        "TASK-DEPENDENT",
        "--depends-on-task",
        "TASK-BAD",
        "--verify",
        PASS_VERIFY,
    )
    _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/bad",
        "--task-id",
        "TASK-BAD",
        "--verify",
        FAIL_VERIFY,
    )
    _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/independent",
        "--task-id",
        "TASK-INDEPENDENT",
        "--verify",
        PASS_VERIFY,
    )

    result = _run_mq(work, "process", "--all", "--regen-cmd", REGEN_CMD)

    assert result.returncode == 1
    assert "dependency changed before merge" in result.stdout
    by_task = {entry["task_id"]: entry for entry in _queue(work)["entries"]}
    assert by_task["TASK-BAD"]["status"] == "failed"
    assert by_task["TASK-DEPENDENT"]["status"] == "pending"
    assert by_task["TASK-INDEPENDENT"]["status"] == "merged"
    assert not (work / "bad.txt").exists()
    assert not (work / "dependent.txt").exists()
    assert (work / "independent.txt").exists()


def test_absent_required_gate_policy_preserves_legacy_entry_shape(tmp_path: Path):
    work = _make_repos(tmp_path)
    _make_branch(work, "feat/legacy", "legacy.txt")

    enqueued = _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/legacy",
        "--task-id",
        "TASK-LEGACY",
        "--verify",
        PASS_VERIFY,
    )

    assert enqueued.returncode == 0, enqueued.stdout + enqueued.stderr
    entry = _queue(work)["entries"][0]
    assert "required_gate_policy_digest" not in entry
    assert "required_gate_ids" not in entry
    processed = _run_mq(
        work, "process", "--all", "--regen-cmd", REGEN_CMD
    )
    assert processed.returncode == 0, processed.stdout + processed.stderr
    assert (work / "legacy.txt").exists()


def test_empty_required_gate_policy_ignores_protected_paths_for_legacy_behavior(
    tmp_path: Path,
):
    work = _make_repos(tmp_path)
    _write_policy(
        work,
        [],
        protected_paths=[
            merge_queue_module.MERGE_GATES_REL,
            "legacy-protected.txt",
        ],
    )
    _make_branch(
        work,
        "feat/empty-policy",
        "legacy-protected.txt",
    )

    enqueued = _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/empty-policy",
        "--task-id",
        "TASK-EMPTY-POLICY",
        "--verify",
        PASS_VERIFY,
    )

    assert enqueued.returncode == 0, enqueued.stdout + enqueued.stderr
    entry = _queue(work)["entries"][0]
    assert "required_gate_policy_digest" not in entry
    assert "required_gate_ids" not in entry
    processed = _run_mq(
        work, "process", "--all", "--regen-cmd", REGEN_CMD
    )
    assert processed.returncode == 0, processed.stdout + processed.stderr
    assert (work / "legacy-protected.txt").exists()


def test_invalid_or_duplicate_required_gate_policy_blocks_enqueue_without_queue_write(
    tmp_path: Path,
):
    work = _make_repos(tmp_path)
    _write_policy(
        work,
        [
            {"id": "design", "command": PASS_VERIFY},
            {"id": "design", "command": PASS_VERIFY},
        ],
        commit=False,
    )

    result = _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/blocked",
        "--task-id",
        "TASK-BLOCKED",
    )

    assert result.returncode == 2
    assert "duplicate gate id" in result.stdout
    assert not (work / QUEUE_REL).exists()


def test_nonempty_required_gate_policy_requires_protected_paths(
    tmp_path: Path,
):
    work = _make_repos(tmp_path)
    path = work / merge_queue_module.MERGE_GATES_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": merge_queue_module.MERGE_GATES_SCHEMA,
                "gates": [{"id": "design", "command": PASS_VERIFY}],
            }
        ),
        encoding="utf-8",
    )

    result = _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/unprotected-gate",
        "--task-id",
        "TASK-UNPROTECTED-GATE",
    )

    assert result.returncode == 2
    assert "protected_paths must be a non-empty list" in result.stdout
    assert not (work / QUEUE_REL).exists()


def test_required_gates_append_after_narrow_verify_and_apply_path_filters(
    tmp_path: Path,
):
    work = _make_repos(tmp_path)
    required = (
        'python -c "open(\'gate-order.log\',\'a\').write(\'required|\')"'
    )
    skipped = (
        'python -c "open(\'gate-order.log\',\'a\').write(\'docs|\')"'
    )
    narrow = 'python -c "open(\'gate-order.log\',\'a\').write(\'narrow|\')"'
    _write_policy(
        work,
        [
            {
                "id": "design",
                "command": required,
                "include_paths": ["src/**"],
            },
            {
                "id": "docs",
                "command": skipped,
                "include_paths": ["docs/**"],
            },
        ],
    )
    _make_branch(work, "feat/ui", "src/ui.txt")

    enqueued = _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/ui",
        "--task-id",
        "TASK-UI",
        "--verify",
        narrow,
    )
    entry = _queue(work)["entries"][0]
    assert enqueued.returncode == 0, enqueued.stdout + enqueued.stderr
    assert entry["required_gate_ids"] == ["design", "docs"]
    assert len(entry["required_gate_policy_digest"]) == 64

    result = _run_mq(
        work, "process", "--all", "--regen-cmd", REGEN_CMD
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (work / "gate-order.log").read_text(encoding="utf-8") == (
        "narrow|required|"
    )
    assert "required gate: docs (skipped: path filters)" in result.stdout


def test_required_gate_failure_keeps_integration_branch_clean(tmp_path: Path):
    work = _make_repos(tmp_path)
    _write_policy(
        work,
        [
            {
                "id": "design-visual",
                "command": FAIL_VERIFY,
                "include_paths": ["src/**"],
            }
        ],
    )
    _make_branch(work, "feat/visual-regression", "src/bad.txt")
    main_before = _git(work, "rev-parse", "main")
    _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/visual-regression",
        "--task-id",
        "TASK-VISUAL",
        "--verify",
        PASS_VERIFY,
    )

    result = _run_mq(
        work, "process", "--all", "--regen-cmd", REGEN_CMD
    )

    assert result.returncode == 1
    entry = _queue(work)["entries"][0]
    assert entry["status"] == "failed"
    assert entry["failure_reason"].startswith(
        "required-gate-failed:design-visual"
    )
    assert _git(work, "rev-parse", "main") == main_before
    assert not (work / "src" / "bad.txt").exists()
    feedback = (
        work
        / "agents/runtime/merge_queue/"
        "feedback-feat-visual-regression.md"
    ).read_text(encoding="utf-8")
    assert "Required host gates" in feedback
    assert "[design-visual]" in feedback


def test_required_gate_policy_drift_blocks_before_queue_or_branch_mutation(
    tmp_path: Path,
):
    work = _make_repos(tmp_path)
    _write_policy(
        work,
        [{"id": "design", "command": PASS_VERIFY}],
    )
    _make_branch(work, "feat/drifted", "drifted.txt")
    _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/drifted",
        "--task-id",
        "TASK-DRIFT",
    )
    _write_policy(
        work,
        [
            {"id": "design", "command": PASS_VERIFY},
            {"id": "ownership", "command": PASS_VERIFY},
        ],
    )
    queue_before = (work / QUEUE_REL).read_bytes()
    main_before = _git(work, "rev-parse", "main")

    result = _run_mq(work, "process", "--all")

    assert result.returncode == 2
    assert "required-gate policy drift" in result.stdout
    assert "re-enqueue" in result.stdout
    assert (work / QUEUE_REL).read_bytes() == queue_before
    assert _git(work, "rev-parse", "main") == main_before
    assert not (work / "drifted.txt").exists()


def test_nonempty_policy_rejects_legacy_unbound_queue_entry(tmp_path: Path):
    work = _make_repos(tmp_path)
    _write_policy(
        work,
        [{"id": "ownership", "command": PASS_VERIFY}],
    )
    _make_branch(work, "feat/unbound", "unbound.txt")
    payload = merge_queue_module._empty_queue()
    payload["entries"].append(
        merge_queue_module.new_entry("feat/unbound", "TASK-UNBOUND")
    )
    merge_queue_module.save_queue(work, payload)
    before = (work / QUEUE_REL).read_bytes()

    result = _run_mq(work, "process", "--all")

    assert result.returncode == 2
    assert "policy is not bound" in result.stdout
    assert "re-enqueue" in result.stdout
    assert (work / QUEUE_REL).read_bytes() == before
    assert not (work / "unbound.txt").exists()


def test_linked_enqueue_binds_primary_checkout_policy(tmp_path: Path):
    work = _make_repos(tmp_path)
    _write_policy(
        work,
        [{"id": "design-check", "command": PASS_VERIFY}],
    )
    linked = tmp_path / "linked-policy"
    _git(work, "worktree", "add", "-b", "feat/linked-policy", str(linked), "main")

    result = _run_mq(
        linked,
        "enqueue",
        "--branch",
        "feat/linked-policy",
        "--task-id",
        "TASK-LINKED",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    entry = _queue(work)["entries"][0]
    assert entry["required_gate_ids"] == ["design-check"]
    assert not (linked / QUEUE_REL).exists()


def test_worker_branch_cannot_delete_base_owned_required_gate_policy(
    tmp_path: Path,
):
    work = _make_repos(tmp_path)
    _write_policy(
        work,
        [{"id": "design-check", "command": PASS_VERIFY}],
    )
    _git(work, "checkout", "-b", "feat/delete-policy", "main")
    _git(work, "rm", merge_queue_module.MERGE_GATES_REL)
    (work / "attempt.txt").write_text("attempt\n", encoding="utf-8")
    _git(work, "add", "attempt.txt")
    _git(work, "commit", "-m", "attempt policy deletion")
    _git(work, "checkout", "main")
    main_before = _git(work, "rev-parse", "main")
    _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/delete-policy",
        "--task-id",
        "TASK-DELETE",
    )

    result = _run_mq(
        work, "process", "--all", "--regen-cmd", REGEN_CMD
    )

    assert result.returncode == 1
    entry = _queue(work)["entries"][0]
    assert entry["failure_reason"].startswith(
        "required-gate-protected-path-modified"
    )
    assert _git(work, "rev-parse", "main") == main_before
    assert (work / merge_queue_module.MERGE_GATES_REL).exists()
    assert not (work / "attempt.txt").exists()


def test_required_gate_placeholders_are_substituted_as_argv(tmp_path: Path):
    work = _make_repos(tmp_path)
    command = (
        "python -c \"import sys; "
        "open('placeholder.log','w').write('|'.join(sys.argv[1:]))\" "
        "{task_id} {branch} {base}"
    )
    _write_policy(
        work,
        [{"id": "ownership", "command": command}],
    )
    _make_branch(work, "feat/placeholders", "placeholder.txt")
    _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/placeholders",
        "--task-id",
        "TASK-PLACEHOLDER",
        "--verify",
        PASS_VERIFY,
    )

    result = _run_mq(
        work, "process", "--all", "--regen-cmd", REGEN_CMD
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (work / "placeholder.log").read_text(encoding="utf-8") == (
        "TASK-PLACEHOLDER|feat/placeholders|main"
    )


def test_worker_cannot_weaken_a_base_owned_gate_implementation(
    tmp_path: Path,
):
    work = _make_repos(tmp_path)
    gate_path = work / "gate.py"
    gate_path.write_text("raise SystemExit(3)\n", encoding="utf-8")
    _git(work, "add", "gate.py")
    _git(work, "commit", "-m", "add failing owner gate")
    _git(work, "push")
    _write_policy(
        work,
        [{"id": "owner-gate", "command": "python gate.py"}],
        protected_paths=[merge_queue_module.MERGE_GATES_REL, "gate.py"],
    )
    _git(work, "checkout", "-b", "feat/weaken-gate", "main")
    gate_path.write_text("raise SystemExit(0)\n", encoding="utf-8")
    (work / "product.txt").write_text("rollback\n", encoding="utf-8")
    _git(work, "add", "gate.py", "product.txt")
    _git(work, "commit", "-m", "weaken gate with product rollback")
    _git(work, "checkout", "main")
    main_before = _git(work, "rev-parse", "main")
    _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/weaken-gate",
        "--task-id",
        "TASK-WEAKEN",
        "--verify",
        PASS_VERIFY,
    )

    result = _run_mq(
        work, "process", "--all", "--regen-cmd", REGEN_CMD
    )

    assert result.returncode == 1
    entry = _queue(work)["entries"][0]
    assert entry["status"] == "failed"
    assert entry["failure_reason"].startswith(
        "required-gate-protected-path-modified"
    )
    assert "gate.py" in entry["failure_reason"]
    assert _git(work, "rev-parse", "main") == main_before
    assert gate_path.read_text(encoding="utf-8") == "raise SystemExit(3)\n"
    assert not (work / "product.txt").exists()


def test_worker_cannot_rename_a_protected_gate_implementation(
    tmp_path: Path,
):
    work = _make_repos(tmp_path)
    gate_path = work / "gate.py"
    gate_path.write_text("raise SystemExit(0)\n", encoding="utf-8")
    _git(work, "add", "gate.py")
    _git(work, "commit", "-m", "add owner gate")
    _git(work, "push")
    _write_policy(
        work,
        [{"id": "owner-gate", "command": "python gate.py"}],
        protected_paths=[merge_queue_module.MERGE_GATES_REL, "gate.py"],
    )
    _git(work, "checkout", "-b", "feat/rename-gate", "main")
    _git(work, "mv", "gate.py", "renamed-gate.py")
    (work / "product.txt").write_text("rollback\n", encoding="utf-8")
    _git(work, "add", "product.txt")
    _git(work, "commit", "-m", "rename gate with product rollback")
    _git(work, "checkout", "main")
    _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/rename-gate",
        "--task-id",
        "TASK-RENAME-GATE",
        "--verify",
        PASS_VERIFY,
    )

    result = _run_mq(
        work, "process", "--all", "--regen-cmd", REGEN_CMD
    )

    assert result.returncode == 1
    entry = _queue(work)["entries"][0]
    assert entry["failure_reason"].startswith(
        "required-gate-protected-path-modified"
    )
    assert "gate.py" in entry["failure_reason"]
    assert gate_path.exists()
    assert not (work / "renamed-gate.py").exists()
    assert not (work / "product.txt").exists()


def test_missing_required_gate_executable_fails_entry_with_feedback(
    tmp_path: Path,
):
    work = _make_repos(tmp_path)
    _write_policy(
        work,
        [{"id": "missing", "command": "definitely-not-a-real-executable"}],
    )
    _make_branch(work, "feat/missing-gate", "missing-gate.txt")
    main_before = _git(work, "rev-parse", "main")
    _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/missing-gate",
        "--task-id",
        "TASK-MISSING-GATE",
        "--verify",
        PASS_VERIFY,
    )

    result = _run_mq(
        work, "process", "--all", "--regen-cmd", REGEN_CMD
    )

    assert result.returncode == 1
    assert "Traceback" not in result.stdout + result.stderr
    entry = _queue(work)["entries"][0]
    assert entry["status"] == "failed"
    assert entry["failure_reason"].startswith(
        "required-gate-launch-failed:missing"
    )
    assert _git(work, "rev-parse", "main") == main_before
    assert not (work / "missing-gate.txt").exists()
    feedback = (
        work
        / "agents/runtime/merge_queue/feedback-feat-missing-gate.md"
    ).read_text(encoding="utf-8")
    assert "required-gate-launch-failed:missing" in feedback


def test_invalid_utf8_required_gate_policy_fails_without_queue_write(
    tmp_path: Path,
):
    work = _make_repos(tmp_path)
    path = work / merge_queue_module.MERGE_GATES_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xff\xfe\x00")

    result = _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/invalid-policy",
        "--task-id",
        "TASK-INVALID-POLICY",
    )

    assert result.returncode == 2
    assert "unreadable" in result.stdout
    assert "Traceback" not in result.stdout + result.stderr
    assert not (work / QUEUE_REL).exists()


def test_dry_run_uses_custom_integration_branch_policy(
    tmp_path: Path,
):
    work = _make_repos(tmp_path)
    _write_policy(
        work,
        [{"id": "main-gate", "command": PASS_VERIFY}],
    )
    _git(work, "checkout", "-b", "staging", "main")
    _write_policy(
        work,
        [
            {"id": "main-gate", "command": PASS_VERIFY},
            {"id": "staging-gate", "command": PASS_VERIFY},
        ],
        commit=False,
    )
    _git(work, "add", merge_queue_module.MERGE_GATES_REL)
    _git(work, "commit", "-m", "configure staging gates")
    _git(work, "push", "-u", "origin", "staging")
    _git(work, "checkout", "main")
    _make_branch(work, "feat/staging-drift", "staging-drift.txt")
    _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/staging-drift",
        "--task-id",
        "TASK-STAGING-DRIFT",
    )
    before = (work / QUEUE_REL).read_bytes()

    result = _run_mq(
        work,
        "process",
        "--all",
        "--dry-run",
        "--integration-branch",
        "staging",
    )

    assert result.returncode == 2
    assert "required-gate policy drift" in result.stdout
    assert (work / QUEUE_REL).read_bytes() == before


def test_dry_run_uses_remote_base_policy_when_local_main_would_fast_forward(
    tmp_path: Path,
):
    work = _make_repos(tmp_path)
    _write_policy(
        work,
        [{"id": "base-gate", "command": PASS_VERIFY}],
    )
    _make_branch(work, "feat/stale-main", "stale-main.txt")
    _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/stale-main",
        "--task-id",
        "TASK-STALE-MAIN",
    )
    before = (work / QUEUE_REL).read_bytes()

    updater = tmp_path / "updater"
    _git(tmp_path, "clone", str(tmp_path / "origin.git"), str(updater))
    _git(updater, "config", "user.email", "updater@test.local")
    _git(updater, "config", "user.name", "Policy Updater")
    _write_policy(
        updater,
        [
            {"id": "base-gate", "command": PASS_VERIFY},
            {"id": "updated-gate", "command": PASS_VERIFY},
        ],
        commit=False,
    )
    _git(updater, "add", merge_queue_module.MERGE_GATES_REL)
    _git(updater, "commit", "-m", "update remote main policy")
    _git(updater, "push", "origin", "main")
    _git(work, "fetch", "origin")

    result = _run_mq(work, "process", "--all", "--dry-run")

    assert result.returncode == 2
    assert "required-gate policy drift" in result.stdout
    assert (work / QUEUE_REL).read_bytes() == before
    assert _git(work, "rev-parse", "main") != _git(
        work, "rev-parse", "origin/main"
    )


def test_dry_run_lists_applied_and_skipped_required_gates_without_mutation(
    tmp_path: Path,
):
    work = _make_repos(tmp_path)
    _write_policy(
        work,
        [
            {
                "id": "design",
                "command": PASS_VERIFY,
                "include_paths": ["src/**"],
            },
            {
                "id": "docs",
                "command": PASS_VERIFY,
                "include_paths": ["docs/**"],
            },
        ],
    )
    _make_branch(work, "feat/dry-policy", "src/dry.txt")
    _run_mq(
        work,
        "enqueue",
        "--branch",
        "feat/dry-policy",
        "--task-id",
        "TASK-DRY-POLICY",
    )
    before = (work / QUEUE_REL).read_bytes()
    main_before = _git(work, "rev-parse", "main")

    result = _run_mq(work, "process", "--all", "--dry-run")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "required=[design]" in result.stdout
    assert "skipped=[docs]" in result.stdout
    assert (work / QUEUE_REL).read_bytes() == before
    assert _git(work, "rev-parse", "main") == main_before
