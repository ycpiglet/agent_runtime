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


# --- WORK-SCHEMA-derived metrics (issue #128 deferred-metric wiring) ---------


def _ts(day: int, hour: int = 12) -> str:
    """ISO timestamp inside the June-2026 window used by the fixtures."""
    return f"2026-06-{day:02d}T{hour:02d}:00:00+09:00"


def _git_date(day: int, hour: int = 0) -> dict[str, str]:
    stamp = f"2026-06-{day:02d}T{hour:02d}:00:00 +0000"
    return {"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp}


def _write_task(
    repo: Path,
    task_id: str,
    *,
    completed_at: str | None,
    started_at: str | None = None,
    actual_hours: float | None = None,
    actual_tokens: int | None = None,
    reopened_count: int | None = None,
    status: str = "completed",
) -> None:
    lines = [
        "---",
        "schema_version: agent-runtime-work-item/v1",
        f"id: {task_id}",
        "kind: task",
        f"status: {status}",
    ]
    if started_at is not None:
        lines.append(f"started_at: {started_at}")
    if completed_at is not None:
        lines.append(f"completed_at: {completed_at}")
    if actual_hours is not None:
        lines.append(f"actual_hours: {actual_hours}")
    if actual_tokens is not None:
        lines.append(f"actual_tokens: {actual_tokens}")
    if reopened_count is not None:
        lines.append(f"reopened_count: {reopened_count}")
    lines += ["---", "", f"# {task_id}", ""]
    dest = repo / "agents" / "lead_engineer" / "tasks"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / f"{task_id}.md").write_text("\n".join(lines), encoding="utf-8")


def _write_verify(
    repo: Path,
    name: str,
    *,
    task_id: str,
    signal: str,
    verified_at: str,
    kind: str = "task",
) -> None:
    dest = repo / "reviews"
    dest.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "agent-runtime-work-verification/v1",
        "id": name,
        "work_id": task_id,
        "task_id": task_id,
        "kind": kind,
        "status": "failed" if signal == "fail" else "passed",
        "signal": signal,
        "verified_at": verified_at,
    }
    (dest / f"{name}.json").write_text(json.dumps(payload), encoding="utf-8")


def _build_work_schema_repo(tmp_path: Path) -> Path:
    """Two-tag repo whose window (v0.1.0..v0.2.0) brackets WORK-SCHEMA records."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "commit.gpgsign", "false")
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _commit(repo, "chore: init", env=_git_date(1))
    _git(repo, "tag", "v0.1.0")  # window opens day 1

    # Records that fall INSIDE the window (days 5-20).
    _write_task(
        repo, "TASK-AR-IN1",
        started_at=_ts(5, 9), completed_at=_ts(5, 12),
        actual_hours=2.0, actual_tokens=4000, reopened_count=1,
    )
    _write_task(
        repo, "TASK-AR-IN2",
        started_at=_ts(10, 8), completed_at=_ts(10, 12),
        actual_hours=4.0, actual_tokens=6000,
    )
    # VERIFY: two PASS rounds for IN1 (1 re-verification), one FAIL for IN2.
    _write_verify(repo, "VERIFY-in1-a", task_id="TASK-AR-IN1", signal="pass", verified_at=_ts(5, 10))
    _write_verify(repo, "VERIFY-in1-b", task_id="TASK-AR-IN1", signal="pass", verified_at=_ts(5, 11))
    _write_verify(repo, "VERIFY-in2-a", task_id="TASK-AR-IN2", signal="fail", verified_at=_ts(10, 9))

    # A record OUTSIDE the window (after v0.2.0): must be excluded.
    _write_task(
        repo, "TASK-AR-OUT",
        started_at=_ts(28, 8), completed_at=_ts(28, 12),
        actual_hours=99.0, actual_tokens=99000,
    )
    _write_verify(repo, "VERIFY-out", task_id="TASK-AR-OUT", signal="fail", verified_at=_ts(28, 9))

    _git(repo, "add", "-A")
    _commit(repo, "feat: in-window work", env=_git_date(20))
    _git(repo, "tag", "v0.2.0")  # window closes day 20 (excludes day-28 records)
    return repo


def test_gate_failure_count_from_verify_records(tmp_path: Path) -> None:
    repo = _build_work_schema_repo(tmp_path)

    report = _run_json(repo, "--from", "v0.1.0", "--to", "v0.2.0")
    metric = report["fixed_metrics"]["gate_failure_count"]

    assert metric["status"] == "collected"
    # Only the in-window FAIL VERIFY counts; the day-28 one is excluded.
    assert metric["value"] == 1


def test_reverification_count_from_verify_records(tmp_path: Path) -> None:
    repo = _build_work_schema_repo(tmp_path)

    report = _run_json(repo, "--from", "v0.1.0", "--to", "v0.2.0")
    metric = report["fixed_metrics"]["reverification_count"]

    assert metric["status"] == "collected"
    # IN1 verified twice => 1 re-verification round; IN2 once => 0.
    assert metric["value"] == 1


def test_reopened_count_from_task_frontmatter(tmp_path: Path) -> None:
    repo = _build_work_schema_repo(tmp_path)

    report = _run_json(repo, "--from", "v0.1.0", "--to", "v0.2.0")
    metric = report["fixed_metrics"]["reopened_count"]

    assert metric["status"] == "collected"
    # IN1 has reopened_count: 1; IN2 has none; OUT excluded.
    assert metric["value"] == 1


def test_actual_tokens_and_hours_from_frontmatter(tmp_path: Path) -> None:
    repo = _build_work_schema_repo(tmp_path)

    report = _run_json(repo, "--from", "v0.1.0", "--to", "v0.2.0")
    metrics = report["fixed_metrics"]

    # In-window totals: tokens 4000+6000=10000; hours 2.0+4.0=6.0; 2 tasks.
    assert metrics["actual_tokens_total"]["status"] == "collected"
    assert metrics["actual_tokens_total"]["value"] == 10000
    assert metrics["actual_hours_total"]["value"] == 6.0
    assert metrics["measured_task_count"]["value"] == 2
    # Per-task means.
    assert abs(metrics["tokens_per_task"]["value"] - 5000.0) < 1e-9
    assert metrics["tokens_per_task"]["status"] == "collected"


def test_wall_clock_per_task_from_timestamps(tmp_path: Path) -> None:
    repo = _build_work_schema_repo(tmp_path)

    report = _run_json(repo, "--from", "v0.1.0", "--to", "v0.2.0")
    metrics = report["fixed_metrics"]

    # IN1: 9->12 = 3h; IN2: 8->12 = 4h; mean 3.5h over 2 tasks.
    assert metrics["wall_clock_hours_total"]["status"] == "collected"
    assert abs(metrics["wall_clock_hours_total"]["value"] - 7.0) < 1e-9
    assert abs(metrics["wall_clock_per_task"]["value"] - 3.5) < 1e-9


def test_since_until_aliases_for_from_to(tmp_path: Path) -> None:
    repo = _build_two_tag_repo(tmp_path)

    report = _run_json(repo, "--since", "v0.1.0", "--until", "v0.2.0")

    assert report["from_ref"] == "v0.1.0"
    assert report["to_ref"] == "v0.2.0"
    assert report["fixed_metrics"]["feat_count"]["value"] == 2


def test_owner_interventions_stays_not_collected(tmp_path: Path) -> None:
    repo = _build_work_schema_repo(tmp_path)

    report = _run_json(repo, "--from", "v0.1.0", "--to", "v0.2.0")
    metric = report["fixed_metrics"]["owner_interventions"]

    assert metric["status"] == "not_collected"
    assert metric["value"] is None


def test_work_schema_metrics_absent_when_no_records(tmp_path: Path) -> None:
    """A plain git repo (no WORK-SCHEMA records) still works and reports zero/empty."""
    repo = _build_two_tag_repo(tmp_path)

    report = _run_json(repo, "--from", "v0.1.0", "--to", "v0.2.0")
    metrics = report["fixed_metrics"]

    # No task/VERIFY records => collected with zero counts (honest empty window),
    # not a crash and not a fabricated value.
    assert metrics["gate_failure_count"]["value"] == 0
    assert metrics["measured_task_count"]["value"] == 0
    assert metrics["tokens_per_task"]["value"] is None


def test_reuses_release_cadence_helpers() -> None:
    """The tool must reuse helpers from release_cadence_trigger, not fork them."""
    source = SCRIPT.read_text(encoding="utf-8")
    assert "release_cadence_trigger" in source


def test_not_wired_into_owner_governance_gate() -> None:
    """Source-repo-only tool: must NOT be added to the governance chain."""
    gate = (REPO_ROOT / "scripts" / "owner_governance_gate.py").read_text(encoding="utf-8")
    assert "self_eval_metrics" not in gate
