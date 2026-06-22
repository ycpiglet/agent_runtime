from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "self_eval_metrics.py"


def _run(root: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *extra],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _run_json(root: Path, *extra: str) -> dict:
    result = _run(root, "--json", *extra)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _git(repo: Path, *args: str, env: dict[str, str] | None = None) -> None:
    merged = dict(os.environ)
    if env:
        merged.update(env)
    subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=merged,
    )


def _commit(repo: Path, subject: str, *, env: dict[str, str] | None = None) -> None:
    _git(repo, "commit", "--allow-empty", "-q", "-m", subject, env=env)


def _init_repo(tmp_path: Path, *, version: str = "0.1.0") -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "commit.gpgsign", "false")
    (repo / "pyproject.toml").write_text(
        f'[project]\nname = "demo"\nversion = "{version}"\n', encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _commit(repo, "chore: init")
    return repo


def _build_two_tag_repo(tmp_path: Path) -> Path:
    """Repo with v0.1.0 .. v0.2.0 spanning a known set of commits."""
    repo = _init_repo(tmp_path)
    _git(repo, "tag", "v0.1.0")
    # Window under measurement: between v0.1.0 (exclusive) and v0.2.0 (inclusive).
    _commit(repo, "feat(core): add widget")
    _commit(repo, "feat(core): add gadget")
    _commit(repo, "fix(core): correct widget edge case")
    _commit(repo, "chore: housekeeping")
    _git(repo, "tag", "v0.2.0")
    return repo


def test_emits_json_with_schema_and_window(tmp_path: Path) -> None:
    repo = _build_two_tag_repo(tmp_path)

    report = _run_json(repo, "--from", "v0.1.0", "--to", "v0.2.0")

    assert report["schema"].startswith("agent-runtime-self-eval/")
    assert report["from_ref"] == "v0.1.0"
    assert report["to_ref"] == "v0.2.0"


def test_counts_feat_and_fix_in_window(tmp_path: Path) -> None:
    repo = _build_two_tag_repo(tmp_path)

    report = _run_json(repo, "--from", "v0.1.0", "--to", "v0.2.0")
    metrics = report["fixed_metrics"]

    assert metrics["feat_count"]["value"] == 2
    assert metrics["fix_count"]["value"] == 1
    assert metrics["commit_count"]["value"] == 4


def test_merge_commit_count(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "tag", "v0.1.0")
    # Create a side branch and merge it (forces a real merge commit).
    _commit(repo, "feat: mainline work")
    _git(repo, "checkout", "-q", "-b", "side")
    _commit(repo, "feat: side work")
    _git(repo, "checkout", "-q", "main")
    _git(repo, "merge", "-q", "--no-ff", "-m", "Merge pull request #1 from side", "side")
    _git(repo, "tag", "v0.2.0")

    report = _run_json(repo, "--from", "v0.1.0", "--to", "v0.2.0")
    metrics = report["fixed_metrics"]

    assert metrics["merge_commit_count"]["value"] == 1


def test_rework_ratio_and_first_pass_proxy(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "tag", "v0.1.0")
    _commit(repo, "feat: add a")
    _commit(repo, "feat: add b")
    _commit(repo, "fix: rework add a")  # rework signal
    _commit(repo, "revert: bad change")  # rework signal
    _git(repo, "tag", "v0.2.0")

    report = _run_json(repo, "--from", "v0.1.0", "--to", "v0.2.0")
    metrics = report["fixed_metrics"]

    # 2 rework commits (fix + revert) out of 4 commits => 0.5 rework ratio.
    assert metrics["rework_count"]["value"] == 2
    assert abs(metrics["rework_ratio"]["value"] - 0.5) < 1e-9
    # first_pass proxy = 1 - rework_ratio.
    assert abs(metrics["first_pass_rate_proxy"]["value"] - 0.5) < 1e-9


def test_days_since_from_tag(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "commit.gpgsign", "false")
    (repo / "pyproject.toml").write_text('[project]\nname = "demo"\nversion = "0.1.0"\n', encoding="utf-8")
    _git(repo, "add", "-A")
    old = {
        "GIT_AUTHOR_DATE": "2026-01-01T00:00:00 +0000",
        "GIT_COMMITTER_DATE": "2026-01-01T00:00:00 +0000",
    }
    _commit(repo, "chore: init", env=old)
    _git(repo, "tag", "v0.1.0")
    _commit(repo, "feat: later work")
    _git(repo, "tag", "v0.2.0")

    report = _run_json(repo, "--from", "v0.1.0", "--to", "v0.2.0")
    metrics = report["fixed_metrics"]

    # Tag v0.1.0 is far in the past; days_since_from_tag should be large/positive.
    assert metrics["days_since_from_tag"]["value"] >= 100


def test_tokens_per_task_is_not_collected(tmp_path: Path) -> None:
    repo = _build_two_tag_repo(tmp_path)

    report = _run_json(repo, "--from", "v0.1.0", "--to", "v0.2.0")
    metrics = report["fixed_metrics"]

    assert metrics["tokens_per_task"]["status"] == "not_collected"
    assert metrics["tokens_per_task"]["value"] is None


def test_defaults_to_latest_tag_and_head(tmp_path: Path) -> None:
    repo = _build_two_tag_repo(tmp_path)
    _commit(repo, "feat: post-release work")

    # No --from/--to: should use latest tag (v0.2.0) .. HEAD.
    report = _run_json(repo)

    assert report["from_ref"] == "v0.2.0"
    assert report["to_ref"] == "HEAD"
    assert report["fixed_metrics"]["feat_count"]["value"] == 1


def test_check_exits_zero_watch_only(tmp_path: Path) -> None:
    repo = _build_two_tag_repo(tmp_path)

    result = _run(repo, "--check")

    assert result.returncode == 0


def test_check_exits_zero_even_with_no_tags(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)  # no tags at all

    result = _run(repo, "--check")

    assert result.returncode == 0


def test_output_is_ascii_only(tmp_path: Path) -> None:
    repo = _build_two_tag_repo(tmp_path)

    result = _run(repo, "--from", "v0.1.0", "--to", "v0.2.0")
    assert result.returncode == 0
    result.stdout.encode("ascii")

    json_result = _run(repo, "--json", "--from", "v0.1.0", "--to", "v0.2.0")
    json_result.stdout.encode("ascii")


def test_reuses_release_cadence_helpers() -> None:
    """The tool must reuse helpers from release_cadence_trigger, not fork them."""
    source = SCRIPT.read_text(encoding="utf-8")
    assert "release_cadence_trigger" in source


def test_not_wired_into_owner_governance_gate() -> None:
    """Source-repo-only tool: must NOT be added to the governance chain."""
    gate = (REPO_ROOT / "scripts" / "owner_governance_gate.py").read_text(encoding="utf-8")
    assert "self_eval_metrics" not in gate
