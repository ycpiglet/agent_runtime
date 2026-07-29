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
    (work / filename).write_text(content, encoding="utf-8")
    _git(work, "add", filename)
    _git(work, "commit", "-m", f"add {filename}")
    _git(work, "checkout", "main")


def _queue(work: Path) -> dict:
    return json.loads((work / QUEUE_REL).read_text(encoding="utf-8"))


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


def test_git_common_lock_path_is_shared_by_linked_worktrees(tmp_path: Path):
    work = _make_repos(tmp_path)
    linked = tmp_path / "linked"
    _git(work, "worktree", "add", "-b", "feat/linked", str(linked), "main")

    assert merge_queue_module.queue_lock_path(work) == merge_queue_module.queue_lock_path(
        linked
    )


def test_concurrent_enqueues_are_serialized_without_lost_updates(tmp_path: Path):
    work = _make_repos(tmp_path)
    ready = tmp_path / "lock-ready"
    holder = _start_lock_holder(work, ready, 0.35)
    _wait_for_path(ready)
    env = {**os.environ, "MERGE_QUEUE_LOCK_TIMEOUT_SECONDS": "2"}

    processes = [
        subprocess.Popen(
            _mq_argv(
                work,
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
        for index in (1, 2)
    ]
    results = [process.communicate(timeout=5) for process in processes]
    holder_output = holder.communicate(timeout=5)

    assert holder.returncode == 0, "".join(holder_output)
    for process, output in zip(processes, results, strict=True):
        assert process.returncode == 0, "".join(output)
    assert {
        entry["branch"] for entry in _queue(work)["entries"]
    } == {"feat/concurrent-1", "feat/concurrent-2"}


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


def test_failed_predecessor_stops_dependent_and_leaves_it_pending(tmp_path: Path):
    work = _make_repos(tmp_path)
    _make_branch(work, "feat/dependent", "dependent.txt")
    _make_branch(work, "feat/bad", "bad.txt")
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

    result = _run_mq(work, "process", "--all", "--regen-cmd", REGEN_CMD)

    assert result.returncode == 1
    assert "dependency changed before merge" in result.stdout
    by_task = {entry["task_id"]: entry for entry in _queue(work)["entries"]}
    assert by_task["TASK-BAD"]["status"] == "failed"
    assert by_task["TASK-DEPENDENT"]["status"] == "pending"
    assert not (work / "bad.txt").exists()
    assert not (work / "dependent.txt").exists()
