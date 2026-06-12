from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "merge_queue.py"
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


def _run_mq(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args, "--root", str(root)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


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
