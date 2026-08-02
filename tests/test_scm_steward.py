"""Tests for the SCM steward hygiene loop (TASK-AR-512)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import scm_steward


def _git(cwd: Path, *args: str, env: dict[str, str] | None = None) -> str:
    merged_env = dict(os.environ)
    if env:
        merged_env.update(env)
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=merged_env,
        check=True,
    )
    return (result.stdout or "").strip()


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


OLD = _iso(datetime.now(timezone.utc) - timedelta(days=30))
RECENT = _iso(datetime.now(timezone.utc) - timedelta(days=1))


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
    released_at: str | None = None,
    expires_at: str | None = None,
    branch: str = "",
    handoff_path: str = "",
) -> None:
    claims = repo / "agents" / "runtime" / "task_claims"
    claims.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": claim_id,
        "task_id": task_id,
        "status": status,
        "worktree_path": f".worktrees/{task_id}",
        "tags": [],
    }
    if released_at is not None:
        payload["released_at"] = released_at
    if expires_at is not None:
        payload["expires_at"] = expires_at
        payload["lease"] = {"expires_at": expires_at}
    if branch:
        payload["branch"] = branch
    if handoff_path:
        payload["handoff_path"] = handoff_path
    (claims / f"{claim_id}.json").write_text(json.dumps(payload), encoding="utf-8")


def _write_task(repo: Path, task_id: str, status: str) -> None:
    tasks = repo / "agents" / "lead_engineer" / "tasks"
    tasks.mkdir(parents=True, exist_ok=True)
    (tasks / f"{task_id}.md").write_text(
        f"---\nid: {task_id}\nstatus: {status}\n---\n\n# {task_id}\n", encoding="utf-8"
    )


def _add_archive_stash(repo: Path, name: str, when_iso: str, *, remote: bool = False) -> str:
    env = {"GIT_COMMITTER_DATE": when_iso, "GIT_AUTHOR_DATE": when_iso}
    tree = _git(repo, "rev-parse", "HEAD^{tree}")
    sha = _git(repo, "commit-tree", tree, "-p", "HEAD", "-m", "stash snapshot", env=env)
    prefix = "refs/remotes/origin" if remote else "refs/heads"
    _git(repo, "update-ref", f"{prefix}/archive/stashes/{name}", sha)
    return sha


def _stub_runner(gh_responses: dict[tuple[str, ...], tuple[int, str, str]] | None = None):
    """Runner stub: gh calls answered from fixtures, everything else succeeds."""
    gh_responses = gh_responses or {}
    calls: list[list[str]] = []

    def runner(args: list[str], cwd: Path) -> tuple[int, str, str]:
        calls.append(list(args))
        if args and args[0] == "gh":
            for prefix, result in gh_responses.items():
                if tuple(args[: len(prefix)]) == prefix:
                    return result
            return (0, "[]", "")
        return (0, "", "")

    runner.calls = calls  # type: ignore[attr-defined]
    return runner


PR_FIXTURE = json.dumps(
    [
        {
            "number": 7,
            "title": "TASK-AR-900 work",
            "isDraft": True,
            "createdAt": OLD,
            "headRefName": "claude/task-ar-900",
        },
        {
            "number": 8,
            "title": "fresh PR",
            "isDraft": False,
            "createdAt": RECENT,
            "headRefName": "claude/task-ar-901",
        },
    ]
)

ISSUE_FIXTURE = json.dumps(
    [
        {"number": 19, "title": "BUG-001 crash on start", "body": "details", "createdAt": OLD},
        {"number": 22, "title": "tracked work", "body": "see TASK-AR-900", "createdAt": OLD},
        {"number": 23, "title": "done work", "body": "see TASK-AR-901", "createdAt": OLD},
        {"number": 24, "title": "free-form note", "body": "", "createdAt": OLD},
    ]
)


def _gh_fixture_runner():
    return _stub_runner(
        {
            ("gh", "pr", "list"): (0, PR_FIXTURE, ""),
            ("gh", "issue", "list"): (0, ISSUE_FIXTURE, ""),
        }
    )


def _run(argv: list[str], runner=None, capsys=None) -> tuple[int, str]:
    rc = scm_steward.main(argv, runner=runner)
    out = capsys.readouterr().out if capsys else ""
    return rc, out


# ---------------------------------------------------------------------------
# report: sections a (zombies) and b (stale claims)
# ---------------------------------------------------------------------------


def test_report_zombie_worktree_detected(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _add_worktree(repo, "TASK-AR-901", "task-ar-901-branch")
    _write_claim(repo, "CLAIM-901", "TASK-AR-901", released_at=OLD)

    rc, out = _run(
        ["report", "--root", str(repo), "--skip-gh"], runner=_stub_runner(), capsys=capsys
    )
    assert rc == 0
    assert "[worktrees] status=attention worktrees=1 zombies=1 cleanable=1" in out
    assert "- watch zombie-worktree:.worktrees/TASK-AR-901" in out
    assert "claim=CLAIM-901" in out


def test_report_stale_claim_detected(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _write_claim(repo, "CLAIM-910", "TASK-AR-910", status="working", expires_at=OLD)

    rc, out = _run(
        ["report", "--root", str(repo), "--skip-gh"], runner=_stub_runner(), capsys=capsys
    )
    assert rc == 0
    assert "stale=1" in out
    assert "- watch stale-claim:CLAIM-910 task=TASK-AR-910" in out


# ---------------------------------------------------------------------------
# report: section c (archive stashes)
# ---------------------------------------------------------------------------


def test_report_old_archive_stash_flagged_with_recovery_guidance(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    sha = _add_archive_stash(repo, "20260501/lost-work", OLD)

    rc, out = _run(
        ["report", "--root", str(repo), "--skip-gh"], runner=_stub_runner(), capsys=capsys
    )
    assert rc == 0
    assert "refs=1 flagged=1" in out
    assert "- watch stash-unreclaimed:archive/stashes/20260501/lost-work" in out
    assert f"recover=git stash apply {sha[:7]}" in out


def test_report_recent_archive_stash_not_flagged(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _add_archive_stash(repo, "20260612/fresh", RECENT)

    rc, out = _run(
        ["report", "--root", str(repo), "--skip-gh"], runner=_stub_runner(), capsys=capsys
    )
    assert rc == 0
    assert "refs=1 flagged=0" in out
    assert "- info stash-archive:archive/stashes/20260612/fresh" in out


def test_report_archive_stash_local_and_origin_deduped(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _add_archive_stash(repo, "20260501/both", OLD)
    _add_archive_stash(repo, "20260501/both", OLD, remote=True)

    rc, out = _run(
        ["report", "--root", str(repo), "--skip-gh"], runner=_stub_runner(), capsys=capsys
    )
    assert rc == 0
    assert "refs=1 flagged=1" in out
    assert "locations=local+origin" in out


# ---------------------------------------------------------------------------
# report: section d (gh PRs/issues via injected runner; no network)
# ---------------------------------------------------------------------------


def test_report_gh_pr_aging_and_drafts(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    rc, out = _run(["report", "--root", str(repo)], runner=_gh_fixture_runner(), capsys=capsys)
    assert rc == 0
    assert "open_prs=2 drafts=1 aged_prs=1" in out
    assert "- watch pr:#7 flags=draft,aged" in out
    assert "pr:#8" not in out  # fresh non-draft PR is counted but not flagged


def test_report_gh_issue_cross_check(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _write_task(repo, "TASK-AR-900", "in_progress")
    _write_task(repo, "TASK-AR-901", "completed")
    (repo / "BACKLOG.md").write_text("- TASK-AR-900 ongoing\n- TASK-AR-901 done\n", encoding="utf-8")

    rc, out = _run(["report", "--root", str(repo)], runner=_gh_fixture_runner(), capsys=capsys)
    assert rc == 0
    # BUG-001 is not registered anywhere -> unregistered.
    assert "- watch issue-unregistered:#19" in out
    assert "refs=BUG-001" in out
    # TASK-AR-900 registered and in progress -> not flagged.
    assert "#22" not in out
    # TASK-AR-901 registered and completed -> close candidate.
    assert "- watch issue-completed-refs:#23" in out
    # No reference at all.
    assert "- watch issue-no-reference:#24" in out
    assert "no_reference=1 unregistered=1 completed_refs=1" in out


def test_report_gh_unavailable_is_nonblocking(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    runner = _stub_runner({("gh",): (1, "", "gh: not logged in")})

    rc, out = _run(["report", "--root", str(repo)], runner=runner, capsys=capsys)
    assert rc == 0
    assert "[github] status=unavailable" in out
    assert "reason=gh: not logged in" in out


# ---------------------------------------------------------------------------
# report: section e (generated-view drift via --check probes)
# ---------------------------------------------------------------------------


def test_report_view_drift_detected(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    scripts = repo / "scripts"
    scripts.mkdir()
    (scripts / "backlog_board.py").write_text(
        "import sys\nprint('board stale')\nsys.exit(1)\n", encoding="utf-8"
    )
    (scripts / "work_item_classifier.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
    (scripts / "evidence_index_generator.py").write_text(
        "import sys\nsys.exit(2)\n", encoding="utf-8"
    )

    rc, out = _run(["report", "--root", str(repo), "--skip-gh"], capsys=capsys)
    assert rc == 0
    assert "drift=1 clean=1 unavailable=1" in out
    assert "- watch view-drift:backlog-board" in out
    assert "regenerate: python scripts/backlog_board.py --write" in out
    assert "- info view-check-unsupported:evidence-index" in out


def test_report_views_missing_scripts_are_info_only(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    rc, out = _run(
        ["report", "--root", str(repo), "--skip-gh"], runner=_stub_runner(), capsys=capsys
    )
    assert rc == 0
    assert "[views] status=ok" in out
    assert "- info view-missing:backlog-board" in out


# ---------------------------------------------------------------------------
# report: invariants
# ---------------------------------------------------------------------------


def test_report_exit_zero_even_outside_git_repo(tmp_path: Path, capsys) -> None:
    plain = tmp_path / "not-a-repo"
    plain.mkdir()
    rc, out = _run(
        ["report", "--root", str(plain), "--skip-gh"], runner=_stub_runner(), capsys=capsys
    )
    assert rc == 0
    assert "scm-steward: report" in out


def test_report_json_output(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _write_claim(repo, "CLAIM-910", "TASK-AR-910", status="working", expires_at=OLD)
    rc, out = _run(
        ["report", "--root", str(repo), "--skip-gh", "--json"],
        runner=_stub_runner(),
        capsys=capsys,
    )
    assert rc == 0
    payload = json.loads(out)
    assert payload["schema"] == "agent-runtime-scm-steward/v1"
    assert set(payload["sections"]) == {"worktrees", "claims", "stashes", "github", "views"}
    assert payload["sections"]["claims"]["counts"]["stale"] == 1
    assert payload["summary"]["watch"] >= 1


def test_report_output_is_ascii_only(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _add_worktree(repo, "TASK-AR-901", "task-ar-901-branch")
    _write_claim(repo, "CLAIM-901", "TASK-AR-901", released_at=OLD)
    _add_archive_stash(repo, "20260501/old", OLD)
    rc, out = _run(["report", "--root", str(repo)], runner=_gh_fixture_runner(), capsys=capsys)
    assert rc == 0
    out.encode("ascii")  # raises if any non-ASCII output sneaks in


def test_report_subprocess_runs_cleanly(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    _add_worktree(repo, "TASK-AR-901", "task-ar-901-branch")
    _write_claim(repo, "CLAIM-901", "TASK-AR-901", released_at=OLD)
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "scm_steward.py"),
            "report",
            "--root",
            str(repo),
            "--skip-gh",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "- watch zombie-worktree:.worktrees/TASK-AR-901" in result.stdout


# ---------------------------------------------------------------------------
# clean: report -> approve -> execute discipline
# ---------------------------------------------------------------------------


def test_clean_without_approve_does_nothing(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    worktree = _add_worktree(repo, "TASK-AR-920", "task-ar-920-branch")
    _write_claim(repo, "CLAIM-920", "TASK-AR-920", released_at=OLD)

    rc, out = _run(
        ["clean", "--root", str(repo), "--skip-gh"], runner=_stub_runner(), capsys=capsys
    )
    assert rc == 0
    assert "no --approve given; nothing changed" in out
    assert worktree.exists()


def test_clean_approve_worktrees_delegates_to_lifecycle_gate(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    worktree = _add_worktree(repo, "TASK-AR-920", "task-ar-920-branch")
    _write_claim(repo, "CLAIM-920", "TASK-AR-920", released_at=OLD)

    rc, out = _run(
        ["clean", "--root", str(repo), "--skip-gh", "--approve", "worktrees"],
        runner=_stub_runner(),
        capsys=capsys,
    )
    assert rc == 0
    assert "clean[worktrees]: delegated to worktree_lifecycle_gate" in out
    assert "- clean removed-worktree .worktrees/TASK-AR-920" in out
    assert not worktree.exists()
    branches = _git(repo, "branch", "--format=%(refname:short)")
    assert "task-ar-920-branch" not in branches.split()


def test_clean_approve_github_prints_but_does_not_execute(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _write_task(repo, "TASK-AR-901", "completed")
    runner = _gh_fixture_runner()

    rc, out = _run(
        ["clean", "--root", str(repo), "--approve", "github"], runner=runner, capsys=capsys
    )
    assert rc == 0
    assert "- would-run: gh pr close 7" in out
    assert "- would-run: gh issue close 23" in out
    assert "- manual: issue #19 needs work-item registration" in out
    mutations = [
        call
        for call in runner.calls
        if call[:3] in (["gh", "pr", "close"], ["gh", "issue", "close"])
    ]
    assert mutations == []


def test_clean_approve_github_executes_with_owner_gate(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _write_task(repo, "TASK-AR-901", "completed")
    runner = _gh_fixture_runner()

    rc, out = _run(
        ["clean", "--root", str(repo), "--approve", "github", "--execute-gh"],
        runner=runner,
        capsys=capsys,
    )
    assert rc == 0
    assert "- run: gh pr close 7" in out
    executed = [call[:3] for call in runner.calls]
    assert ["gh", "pr", "close"] in executed
    assert ["gh", "issue", "close"] in executed


def test_clean_approve_stashes_prints_commands_only(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _add_archive_stash(repo, "20260501/old", OLD)
    _add_archive_stash(repo, "20260501/old", OLD, remote=True)

    rc, out = _run(
        ["clean", "--root", str(repo), "--skip-gh", "--approve", "stashes"],
        runner=_stub_runner(),
        capsys=capsys,
    )
    assert rc == 0
    assert "- would-run: git branch -D archive/stashes/20260501/old" in out
    assert "- would-run: git push origin --delete archive/stashes/20260501/old" in out
    # The ref must still exist: stash cleanup is print-only.
    assert _git(repo, "rev-parse", "--verify", "refs/heads/archive/stashes/20260501/old")


# ---------------------------------------------------------------------------
# gh helpers: pr-open / pr-close / issue-sync
# ---------------------------------------------------------------------------


def test_pr_open_dry_run_prints_push_and_draft_pr(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _write_claim(
        repo,
        "CLAIM-940",
        "TASK-AR-940",
        status="working",
        branch="claude/task-ar-940-feature",
        handoff_path="agents/runtime/task_claims/CLAIM-940.handoff.md",
    )
    runner = _stub_runner()

    rc, out = _run(
        ["pr-open", "--root", str(repo), "--task", "TASK-AR-940"], runner=runner, capsys=capsys
    )
    assert rc == 0
    assert "- would-run: git push -u origin claude/task-ar-940-feature" in out
    assert "gh pr create --draft --title TASK-AR-940" in out
    assert "agents/runtime/task_claims/CLAIM-940.handoff.md" in out
    assert runner.calls == []  # dry-run never touches the runner


def test_pr_open_execute_gh_runs_commands(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _write_claim(repo, "CLAIM-940", "TASK-AR-940", status="working", branch="claude/task-ar-940")
    runner = _stub_runner()

    rc, out = _run(
        ["pr-open", "--root", str(repo), "--task", "TASK-AR-940", "--execute-gh"],
        runner=runner,
        capsys=capsys,
    )
    assert rc == 0
    assert ["git", "push", "-u", "origin", "claude/task-ar-940"] in runner.calls
    assert any(call[:4] == ["gh", "pr", "create", "--draft"] for call in runner.calls)


def test_pr_close_dry_run(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    runner = _stub_runner()
    rc, out = _run(
        ["pr-close", "--root", str(repo), "--pr", "12", "--task", "TASK-AR-940"],
        runner=runner,
        capsys=capsys,
    )
    assert rc == 0
    assert "- would-run: gh pr comment 12 --body" in out
    assert "- would-run: gh pr close 12" in out
    assert runner.calls == []


def test_issue_sync_dry_run_intake_and_close_direction(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    _write_task(repo, "TASK-AR-901", "completed")
    runner = _gh_fixture_runner()

    rc, out = _run(
        [
            "issue-sync",
            "--root",
            str(repo),
            "--intake-title",
            "stash event lost on closeout",
            "--intake-ref",
            "BUG-005",
        ],
        runner=runner,
        capsys=capsys,
    )
    assert rc == 0
    assert '- would-run: gh issue create --title "[BUG-005] stash event lost on closeout"' in out
    assert "- would-run: gh issue close 23" in out
    assert "- manual: BUG-005 is not registered yet" in out
    mutations = [call for call in runner.calls if call[:3] == ["gh", "issue", "close"]]
    assert mutations == []


# ---------------------------------------------------------------------------
# packaging invariants
# ---------------------------------------------------------------------------


def test_no_subcommand_prints_help() -> None:
    assert scm_steward.main([]) == 2


def test_template_mirror_is_identical() -> None:
    template_root = REPO_ROOT / "src" / "agent_runtime" / "templates" / "project"
    root_script = (REPO_ROOT / "scripts" / "scm_steward.py").read_text(encoding="utf-8")
    template_script = (template_root / "scripts" / "scm_steward.py").read_text(encoding="utf-8")
    assert root_script == template_script

    root_skill = (REPO_ROOT / "skills" / "scm-steward" / "SKILL.md").read_text(encoding="utf-8")
    template_skill = (template_root / "skills" / "scm-steward" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert root_skill == template_skill
