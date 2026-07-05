from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "open_state_sweep.py"


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _seed_repo(root: Path, messages: list[str]) -> None:
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "sweep-test@example.com")
    _git(root, "config", "user.name", "Sweep Test")
    for index, message in enumerate(messages):
        marker = root / f"file-{index}.txt"
        marker.write_text(f"change {index}\n", encoding="utf-8")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", message)


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), "--ref", "HEAD", *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _issues_file(root: Path, issues: list[dict[str, object]]) -> Path:
    path = root / "issues.json"
    path.write_text(json.dumps(issues), encoding="utf-8")
    return path


def test_reports_open_issue_already_closed_by_merged_history(tmp_path: Path) -> None:
    # COMPOUND-2026-07-04 stale-open-state-debt: closing keywords in merged
    # commits do not reliably auto-close issues (#211/#162), so the sweep
    # must surface still-open issues the history claims are done.
    _seed_repo(tmp_path, ["feat: base", "fix(templates): restore property\n\nFixes #211"])
    issues = _issues_file(tmp_path, [{"number": 211, "title": "template drift"}, {"number": 999, "title": "unrelated"}])

    result = _run(tmp_path, "--issues-file", str(issues), "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert [f["number"] for f in report["findings"]] == [211]
    assert report["findings"][0]["kind"] == "stale-open-issue"
    assert report["issues_source"] == "issues-file"


def test_closing_keyword_variants_are_detected(tmp_path: Path) -> None:
    _seed_repo(
        tmp_path,
        ["chore: base", "Closes #7", "resolve #8 in body\n\nlong text", "FIXED #9"],
    )
    issues = _issues_file(
        tmp_path,
        [{"number": 7, "title": "a"}, {"number": 8, "title": "b"}, {"number": 9, "title": "c"}],
    )

    result = _run(tmp_path, "--issues-file", str(issues), "--json")

    report = json.loads(result.stdout)
    assert [f["number"] for f in report["findings"]] == [7, 8, 9]


def test_no_findings_when_open_issues_are_untouched(tmp_path: Path) -> None:
    _seed_repo(tmp_path, ["feat: mentions issue #5 without closing keyword"])
    issues = _issues_file(tmp_path, [{"number": 5, "title": "still real"}])

    result = _run(tmp_path, "--issues-file", str(issues), "--json", "--check")

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["findings"] == []


def test_check_exits_nonzero_on_findings(tmp_path: Path) -> None:
    _seed_repo(tmp_path, ["fix: done\n\ncloses #3"])
    issues = _issues_file(tmp_path, [{"number": 3, "title": "done but open"}])

    result = _run(tmp_path, "--issues-file", str(issues), "--check")

    assert result.returncode == 1
    assert "stale-open-issue: #3" in result.stdout


def test_watch_only_default_exits_zero_even_with_findings(tmp_path: Path) -> None:
    _seed_repo(tmp_path, ["fix: done\n\ncloses #3"])
    issues = _issues_file(tmp_path, [{"number": 3, "title": "done but open"}])

    result = _run(tmp_path, "--issues-file", str(issues))

    assert result.returncode == 0, result.stdout + result.stderr


def _seed_dangling_stash(root: Path, lane_commits: int) -> None:
    # main line
    _seed_repo(root, ["feat: mainline base"])
    _git(root, "branch", "-M", "main")
    # divergent lane
    _git(root, "checkout", "-q", "-b", "lane")
    for index in range(lane_commits):
        marker = root / f"lane-{index}.txt"
        marker.write_text(f"lane {index}\n", encoding="utf-8")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", f"lane commit {index}")
    # stash-shaped merge commit whose first parent is the lane tip
    lane_tip = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True, encoding="utf-8",
    ).stdout.strip()
    (root / "wip.txt").write_text("wip\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "archive late dirty work")
    stash_commit = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True, encoding="utf-8",
    ).stdout.strip()
    _git(root, "update-ref", "refs/remotes/origin/archive/stashes/20260704/test-lane", stash_commit)
    _git(root, "checkout", "-q", "main")
    assert lane_tip  # first parent of the stash-shaped commit is the lane


def test_reports_dangling_lane_hanging_off_stash_parent(tmp_path: Path) -> None:
    # Issue #250: 160 unmerged commits were reachable only through one
    # stash ref's parent chain; the sweep must surface such lanes.
    _seed_dangling_stash(tmp_path, lane_commits=6)

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path), "--ref", "main",
         "--issues-file", str(_issues_file(tmp_path, [])), "--json"],
        check=False, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    lanes = [f for f in report["findings"] if f["kind"] == "dangling-lane"]
    assert len(lanes) == 1
    assert lanes[0]["unmerged_commit_count"] >= 6
    assert "archive/stashes/20260704/test-lane" in lanes[0]["stash"]


def test_small_stash_delta_is_not_a_dangling_lane(tmp_path: Path) -> None:
    _seed_dangling_stash(tmp_path, lane_commits=2)

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path), "--ref", "main",
         "--issues-file", str(_issues_file(tmp_path, [])), "--json"],
        check=False, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )

    report = json.loads(result.stdout)
    assert [f for f in report["findings"] if f["kind"] == "dangling-lane"] == []


def test_lane_pinned_under_archive_branches_is_not_dangling(tmp_path: Path) -> None:
    # A lane already preserved by an archive/branches/* ref is tethered; the
    # stash is no longer its only anchor, so it must not be reported.
    _seed_dangling_stash(tmp_path, lane_commits=6)
    stash_parent = subprocess.run(
        ["git", "-C", str(tmp_path), "rev-parse", "refs/remotes/origin/archive/stashes/20260704/test-lane^1"],
        check=True, capture_output=True, text=True, encoding="utf-8",
    ).stdout.strip()
    _git(tmp_path, "update-ref", "refs/remotes/origin/archive/branches/20260704/pinned-lane", stash_parent)

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path), "--ref", "main",
         "--issues-file", str(_issues_file(tmp_path, [])), "--json"],
        check=False, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )

    report = json.loads(result.stdout)
    assert [f for f in report["findings"] if f["kind"] == "dangling-lane"] == []


# --------------------------------------------------------------------------- #
# merged-remote-branch: fully-merged (ahead=0) non-archive branches are debris.
# --------------------------------------------------------------------------- #
def test_reports_merged_remote_branch_past_age_floor(tmp_path: Path) -> None:
    _seed_repo(tmp_path, ["feat: base", "chore: tip"])
    _git(tmp_path, "update-ref", "refs/remotes/origin/old-lane", "HEAD~1")

    result = _run(tmp_path, "--merged-branch-age-days", "0", "--json")

    assert result.returncode == 0
    report = json.loads(result.stdout)
    kinds = [(f["kind"], f.get("branch")) for f in report["findings"]]
    assert ("merged-remote-branch", "origin/old-lane") in kinds


def test_fresh_zero_ahead_branch_is_below_age_floor(tmp_path: Path) -> None:
    # A branch just cut from the tip (work not started) must not be flagged
    # under the default 7-day age floor: its committerdate is "now".
    _seed_repo(tmp_path, ["feat: base"])
    _git(tmp_path, "update-ref", "refs/remotes/origin/just-cut", "HEAD")

    result = _run(tmp_path, "--json")

    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert all(f["kind"] != "merged-remote-branch" for f in report["findings"])


def test_unmerged_branch_is_not_reported(tmp_path: Path) -> None:
    _seed_repo(tmp_path, ["feat: base"])
    _git(tmp_path, "branch", "-M", "main")
    _git(tmp_path, "checkout", "-q", "-b", "lane")
    (tmp_path / "lane.txt").write_text("lane\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "feat: lane work")
    _git(tmp_path, "update-ref", "refs/remotes/origin/live-lane", "HEAD")
    _git(tmp_path, "checkout", "-q", "main")

    result = _run(tmp_path, "--merged-branch-age-days", "0", "--json")

    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert all(f["kind"] != "merged-remote-branch" for f in report["findings"])


def test_archive_branches_are_excluded_from_merged_branch_findings(tmp_path: Path) -> None:
    _seed_repo(tmp_path, ["feat: base"])
    _git(tmp_path, "update-ref", "refs/remotes/origin/archive/branches/20260704/pinned", "HEAD")

    result = _run(tmp_path, "--merged-branch-age-days", "0", "--json")

    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert all(f["kind"] != "merged-remote-branch" for f in report["findings"])


# --------------------------------------------------------------------------- #
# Scheduled workflow wiring: weekly sweep surfaces findings as a dedup'd issue.
# --------------------------------------------------------------------------- #
def test_sweep_workflow_wiring() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "open-state-sweep.yml").read_text(encoding="utf-8")
    # Periodic + manual trigger; may open/close the findings issue.
    assert "schedule:" in workflow
    assert "workflow_dispatch:" in workflow
    assert "issues: write" in workflow
    # Findings reach the Owner proactively via a single dedup'd issue that
    # auto-closes when a sweep is clean (release-auto notification pattern).
    assert "gh issue create" in workflow
    assert "gh issue close" in workflow
    assert "[open-state-sweep] Open state drifted from merged reality" in workflow
    # Cross-step file contract pinned (casebook: silent-cross-step-wiring):
    # .tmp exists before tee, and a missing result file fails loudly.
    mkdir_pos = workflow.find("mkdir -p .tmp")
    tee_pos = workflow.find("tee .tmp/open-state-sweep.json")
    assert mkdir_pos != -1 and tee_pos != -1 and mkdir_pos < tee_pos
    assert "result file was not written" in workflow
    # Archive stash/branch refs live under refs/heads on origin; the sweep needs
    # the full remote refspec, not just the checked-out ref.
    assert "+refs/heads/*:refs/remotes/origin/*" in workflow
