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
