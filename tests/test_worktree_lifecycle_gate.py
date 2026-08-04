"""Tests for lifecycle stage W5 zombie worktree detection/cleanup (TASK-AR-505)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import worktree_lifecycle_gate


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


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "symbolic-ref", "HEAD", "refs/heads/main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    (repo / ".gitignore").write_text(".worktrees/\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "init")
    # Simulate the integration base the gate compares against.
    _git(repo, "update-ref", "refs/remotes/origin/main", "main")
    return repo


def _add_worktree(repo: Path, task_id: str, branch: str) -> Path:
    worktree = repo / ".worktrees" / task_id
    _git(repo, "worktree", "add", "-b", branch, str(worktree))
    return worktree


def _write_claim(
    repo: Path,
    claim_id: str,
    task_id: str,
    *,
    status: str = "released",
    worktree_path: str | None = None,
    released_at: str | None = None,
    expires_at: str | None = None,
    nested_expires_at: str | None = None,
    tags: list[str] | None = None,
) -> None:
    claims = repo / "agents" / "runtime" / "task_claims"
    claims.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": claim_id,
        "task_id": task_id,
        "status": status,
        "worktree_path": worktree_path if worktree_path is not None else f".worktrees/{task_id}",
        "tags": tags or [],
    }
    if released_at is not None:
        payload["released_at"] = released_at
    if expires_at is not None:
        payload["expires_at"] = expires_at
        payload["lease"] = {
            "expires_at": nested_expires_at or expires_at,
        }
    (claims / f"{claim_id}.json").write_text(json.dumps(payload), encoding="utf-8")


OLD = _iso(datetime.now(timezone.utc) - timedelta(days=30))
RECENT = _iso(datetime.now(timezone.utc) - timedelta(days=1))


def _run_check(repo: Path, *extra: str, capsys) -> tuple[int, str]:
    rc = worktree_lifecycle_gate.main(["--root", str(repo), *extra])
    return rc, capsys.readouterr().out


def test_zombie_detected_as_watch(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _add_worktree(repo, "TASK-AR-901", "task-ar-901-branch")
    _write_claim(repo, "CLAIM-901", "TASK-AR-901", released_at=OLD)

    rc, out = _run_check(repo, "--check", capsys=capsys)
    assert rc == 0
    assert "worktree-lifecycle-gate: pass" in out
    assert "zombies=1" in out
    assert "zombies_cleanable=1" in out
    assert "- watch zombie:.worktrees/TASK-AR-901" in out
    assert "claim=CLAIM-901" in out


def test_check_exits_zero_even_with_findings(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _add_worktree(repo, "TASK-AR-901", "task-ar-901-branch")
    _write_claim(repo, "CLAIM-901", "TASK-AR-901", released_at=OLD)
    _write_claim(
        repo, "CLAIM-902", "TASK-AR-902", status="working", expires_at=OLD
    )

    rc, out = _run_check(repo, "--check", capsys=capsys)
    assert rc == 0
    assert "watch" in out


def test_ahead_branch_never_flagged(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    worktree = _add_worktree(repo, "TASK-AR-902", "task-ar-902-branch")
    (worktree / "new.txt").write_text("work\n", encoding="utf-8")
    _git(worktree, "add", ".")
    _git(worktree, "commit", "-m", "unmerged work")
    _write_claim(repo, "CLAIM-902", "TASK-AR-902", released_at=OLD)

    rc, out = _run_check(repo, "--check", capsys=capsys)
    assert rc == 0
    assert "zombies=0" in out
    assert "zombie:.worktrees/TASK-AR-902" not in out


def test_dirty_worktree_never_flagged(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    worktree = _add_worktree(repo, "TASK-AR-903", "task-ar-903-branch")
    (worktree / "scratch.txt").write_text("uncommitted\n", encoding="utf-8")
    _write_claim(repo, "CLAIM-903", "TASK-AR-903", released_at=OLD)

    rc, out = _run_check(repo, "--check", capsys=capsys)
    assert rc == 0
    assert "zombies=0" in out


def test_active_claim_never_flagged(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _add_worktree(repo, "TASK-AR-904", "task-ar-904-branch")
    _write_claim(repo, "CLAIM-904", "TASK-AR-904", status="in_progress")

    rc, out = _run_check(repo, "--check", capsys=capsys)
    assert rc == 0
    assert "zombies=0" in out


def test_preserve_marker_exempt(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    worktree = _add_worktree(repo, "TASK-AR-905", "task-ar-905-branch")
    (worktree / "PRESERVE").write_text("keep me\n", encoding="utf-8")
    _write_claim(repo, "CLAIM-905", "TASK-AR-905", released_at=OLD)

    rc, out = _run_check(repo, "--check", capsys=capsys)
    assert rc == 0
    assert "zombies=1" in out
    assert "zombies_cleanable=0" in out
    assert "exempt=preserve-marker" in out


def test_preserve_tag_exempt(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _add_worktree(repo, "TASK-AR-906", "task-ar-906-branch")
    _write_claim(
        repo, "CLAIM-906", "TASK-AR-906", released_at=OLD, tags=["preserve"]
    )

    rc, out = _run_check(repo, "--check", capsys=capsys)
    assert rc == 0
    assert "zombies=1" in out
    assert "zombies_cleanable=0" in out
    assert "exempt=preserve-tag" in out


def test_retention_window_exempt(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _add_worktree(repo, "TASK-AR-907", "task-ar-907-branch")
    _write_claim(repo, "CLAIM-907", "TASK-AR-907", released_at=RECENT)

    rc, out = _run_check(repo, "--check", capsys=capsys)
    assert rc == 0
    assert "zombies=1" in out
    assert "zombies_cleanable=0" in out
    assert "exempt=retention-window" in out


def test_retention_days_zero_makes_recent_zombie_cleanable(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _add_worktree(repo, "TASK-AR-907", "task-ar-907-branch")
    _write_claim(repo, "CLAIM-907", "TASK-AR-907", released_at=RECENT)

    rc, out = _run_check(repo, "--check", "--retention-days", "0", capsys=capsys)
    assert rc == 0
    assert "zombies_cleanable=1" in out


def test_missing_release_timestamp_is_retention_exempt(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _add_worktree(repo, "TASK-AR-908", "task-ar-908-branch")
    _write_claim(repo, "CLAIM-908", "TASK-AR-908")  # no released_at

    rc, out = _run_check(repo, "--check", capsys=capsys)
    assert rc == 0
    assert "zombies=1" in out
    assert "zombies_cleanable=0" in out
    assert "exempt=retention-window" in out


def test_no_claim_never_flagged(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _add_worktree(repo, "TASK-AR-909", "task-ar-909-branch")

    rc, out = _run_check(repo, "--check", capsys=capsys)
    assert rc == 0
    assert "zombies=0" in out


def test_stale_claim_watch(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _write_claim(
        repo,
        "CLAIM-910",
        "TASK-AR-910",
        status="working",
        expires_at=OLD,
    )

    rc, out = _run_check(repo, "--check", capsys=capsys)
    assert rc == 0
    assert "stale_claims=1" in out
    assert "- watch stale-claim:CLAIM-910 task=TASK-AR-910" in out


def test_ar655_lifecycle_stale_detection_uses_shared_grace_boundary() -> None:
    now = datetime(2026, 8, 3, 0, 0, tzinfo=timezone.utc)
    equality = (now - timedelta(seconds=600)).isoformat()
    one_microsecond_old = (
        now - timedelta(seconds=600, microseconds=1)
    ).isoformat()

    equal_claim = {
        "claim_id": "CLAIM-AR655-GRACE-EQUALITY",
        "task_id": "TASK-AR-655",
        "status": "working",
        "expires_at": equality,
        "lease": {"expires_at": equality},
    }
    expired_claim = {
        "claim_id": "CLAIM-AR655-GRACE-AFTER",
        "task_id": "TASK-AR-655",
        "status": "working",
        "expires_at": one_microsecond_old,
        "lease": {"expires_at": one_microsecond_old},
    }

    assert worktree_lifecycle_gate.find_stale_claims(
        [equal_claim],
        now,
        grace_seconds=600,
    ) == []
    stale = worktree_lifecycle_gate.find_stale_claims(
        [expired_claim],
        now,
        grace_seconds=600,
    )
    assert len(stale) == 1
    assert "stale-claim:CLAIM-AR655-GRACE-AFTER" in stale[0]


def test_ar655_lifecycle_stale_detection_uses_latest_deadline_copy() -> None:
    now = datetime(2026, 8, 3, 0, 0, tzinfo=timezone.utc)
    claim = {
        "claim_id": "CLAIM-AR655-LATEST-DEADLINE",
        "task_id": "TASK-AR-655",
        "status": "working",
        "expires_at": (now - timedelta(seconds=601)).isoformat(),
        "lease": {"expires_at": (now + timedelta(seconds=1)).isoformat()},
    }

    assert worktree_lifecycle_gate.find_stale_claims(
        [claim],
        now,
        grace_seconds=600,
    ) == []


def test_ar655_clean_never_removes_status_active_expired_worktree(
    tmp_path: Path,
    capsys,
) -> None:
    repo = _make_repo(tmp_path)
    worktree = _add_worktree(
        repo,
        "TASK-AR-930",
        "task-ar-930-branch",
    )
    _write_claim(
        repo,
        "CLAIM-930",
        "TASK-AR-930",
        status="working",
        expires_at=OLD,
    )

    rc, out = _run_check(
        repo,
        "--clean",
        "--retention-days",
        "0",
        capsys=capsys,
    )

    assert rc == 0
    assert "stale-claim:CLAIM-930" in out
    assert "zombies=0" in out
    assert "removed-worktree .worktrees/TASK-AR-930" not in out
    assert worktree.exists()


def test_released_claim_with_past_expiry_not_stale(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _write_claim(
        repo,
        "CLAIM-911",
        "TASK-AR-911",
        status="released",
        released_at=OLD,
        expires_at=OLD,
    )

    rc, out = _run_check(repo, "--check", capsys=capsys)
    assert rc == 0
    assert "stale_claims=0" in out


def test_clean_removes_only_eligible(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)

    # Eligible zombie: merged, released long ago, clean.
    zombie = _add_worktree(repo, "TASK-AR-920", "task-ar-920-branch")
    _write_claim(repo, "CLAIM-920", "TASK-AR-920", released_at=OLD)

    # Ahead of base: must survive.
    ahead = _add_worktree(repo, "TASK-AR-921", "task-ar-921-branch")
    (ahead / "new.txt").write_text("work\n", encoding="utf-8")
    _git(ahead, "add", ".")
    _git(ahead, "commit", "-m", "unmerged")
    _write_claim(repo, "CLAIM-921", "TASK-AR-921", released_at=OLD)

    # Dirty: must survive.
    dirty = _add_worktree(repo, "TASK-AR-922", "task-ar-922-branch")
    (dirty / "scratch.txt").write_text("dirty\n", encoding="utf-8")
    _write_claim(repo, "CLAIM-922", "TASK-AR-922", released_at=OLD)

    # Preserved: must survive.
    preserved = _add_worktree(repo, "TASK-AR-923", "task-ar-923-branch")
    (preserved / "PRESERVE").write_text("keep\n", encoding="utf-8")
    _write_claim(repo, "CLAIM-923", "TASK-AR-923", released_at=OLD)

    # Inside retention window: must survive.
    recent = _add_worktree(repo, "TASK-AR-924", "task-ar-924-branch")
    _write_claim(repo, "CLAIM-924", "TASK-AR-924", released_at=RECENT)

    rc, out = _run_check(repo, "--clean", capsys=capsys)
    assert rc == 0
    assert "- clean removed-worktree .worktrees/TASK-AR-920" in out
    assert "- clean deleted-branch task-ar-920-branch" in out

    assert not zombie.exists()
    assert ahead.exists()
    assert dirty.exists()
    assert preserved.exists()
    assert recent.exists()

    branches = _git(repo, "branch", "--format=%(refname:short)")
    assert "task-ar-920-branch" not in branches.split()
    for survivor in (
        "task-ar-921-branch",
        "task-ar-922-branch",
        "task-ar-923-branch",
        "task-ar-924-branch",
    ):
        assert survivor in branches.split()


def test_clean_skip_lines_reported(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _add_worktree(repo, "TASK-AR-925", "task-ar-925-branch")
    _write_claim(repo, "CLAIM-925", "TASK-AR-925", released_at=RECENT)

    rc, out = _run_check(repo, "--clean", capsys=capsys)
    assert rc == 0
    assert "- clean skip .worktrees/TASK-AR-925 reason=retention-window" in out
    assert (repo / ".worktrees" / "TASK-AR-925").exists()


def test_clean_skips_when_dirty_recheck_is_unknown(tmp_path: Path, monkeypatch) -> None:
    """An unknown dirty state at clean time must skip, not count as clean."""
    repo = _make_repo(tmp_path)
    worktree = _add_worktree(repo, "TASK-AR-929", "task-ar-929-branch")
    _write_claim(repo, "CLAIM-929", "TASK-AR-929", released_at=OLD)

    info = worktree_lifecycle_gate.WorktreeInfo(
        path=worktree, branch="task-ar-929-branch", rel=".worktrees/TASK-AR-929"
    )
    verdict = worktree_lifecycle_gate.ZombieVerdict(worktree=info, zombie=True)
    monkeypatch.setattr(worktree_lifecycle_gate, "_is_dirty", lambda path: None)

    actions, failures = worktree_lifecycle_gate.clean_zombies(repo, [verdict])

    assert actions == ["skip .worktrees/TASK-AR-929 reason=dirty-recheck-unknown"]
    assert failures == 0
    assert worktree.exists()


def test_no_mode_prints_help(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    rc = worktree_lifecycle_gate.main(["--root", str(repo)])
    assert rc == 2


def test_output_is_ascii_only(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _add_worktree(repo, "TASK-AR-926", "task-ar-926-branch")
    _write_claim(repo, "CLAIM-926", "TASK-AR-926", released_at=OLD)
    _write_claim(repo, "CLAIM-927", "TASK-AR-927", status="working", expires_at=OLD)

    rc, out = _run_check(repo, "--check", capsys=capsys)
    assert rc == 0
    out.encode("ascii")  # raises if any non-ASCII output sneaks in


def test_subprocess_check_runs_cleanly(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    _add_worktree(repo, "TASK-AR-928", "task-ar-928-branch")
    _write_claim(repo, "CLAIM-928", "TASK-AR-928", released_at=OLD)
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "worktree_lifecycle_gate.py"),
            "--root",
            str(repo),
            "--check",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "- watch zombie:.worktrees/TASK-AR-928" in result.stdout


def test_owner_governance_chain_includes_gate() -> None:
    root_gate = (REPO_ROOT / "scripts" / "owner_governance_gate.py").read_text(encoding="utf-8")
    template_gate = (
        REPO_ROOT
        / "src"
        / "agent_runtime"
        / "templates"
        / "project"
        / "scripts"
        / "owner_governance_gate.py"
    ).read_text(encoding="utf-8")
    expected = '["scripts/worktree_lifecycle_gate.py", "--check"]'
    assert expected in root_gate
    assert expected in template_gate


def test_template_mirror_is_identical() -> None:
    root_script = (REPO_ROOT / "scripts" / "worktree_lifecycle_gate.py").read_text(encoding="utf-8")
    template_script = (
        REPO_ROOT
        / "src"
        / "agent_runtime"
        / "templates"
        / "project"
        / "scripts"
        / "worktree_lifecycle_gate.py"
    ).read_text(encoding="utf-8")
    assert root_script == template_script
