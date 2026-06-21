"""Tests for scripts/release_auto_noncritical.py (TASK-AR-586).

These prove the orchestrator's decision boundaries WITHOUT ever creating a real
git tag or pushing: every test runs in the default dry-run mode against a
throwaway temp git repo, so the host repository is never touched.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import release_auto_noncritical as orch
from scripts import release_execution_gate as execution_gate

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "release_auto_noncritical.py"


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


def _make_repo(tmp_path: Path, *, version: str = "0.2.0", triggered: bool = True) -> Path:
    """A temp repo with a baseline tag and enough commits to fire the cadence trigger."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "commit.gpgsign", "false")
    (repo / "pyproject.toml").write_text(
        f'[project]\nname = "agent_runtime"\nversion = "{version}"\n', encoding="utf-8"
    )
    init = repo / "src" / "agent_runtime" / "__init__.py"
    init.parent.mkdir(parents=True, exist_ok=True)
    init.write_text(f'__version__ = "{version}"\n', encoding="utf-8")
    # A ready RELEASE-GATE-TEMPLATE so the execution gate sees release_state: ready.
    template = repo / "agents" / "project" / "RELEASE-GATE-TEMPLATE.yml"
    template.parent.mkdir(parents=True, exist_ok=True)
    template.write_text(
        "release_state: ready\nrelease_cause: all_hold_routes_closed_with_evidence\n",
        encoding="utf-8",
    )
    # Materialize the REQUIRED_READY_EVIDENCE files so the execution gate's
    # ready_evidence check passes against the temp repo.
    for ev in execution_gate.REQUIRED_READY_EVIDENCE:
        path = repo / ev
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("evidence\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _commit(repo, "chore: init")
    _git(repo, "tag", "v0.2.0")
    if triggered:
        for index in range(40):
            _commit(repo, f"chore: tick {index}")
    return repo


def _run(repo: Path, **kwargs):
    # Let ready_evidence default to release_execution_gate.REQUIRED_READY_EVIDENCE
    # (relative paths). The gate resolves Path(required).exists() against the test
    # process cwd (the host repo root), where those evidence files genuinely exist,
    # so the noncritical path can reach its release decision in tests.
    return orch.orchestrate(
        repo,
        out_dir=repo / ".tmp" / "release-auto",
        **kwargs,
    )


# --------------------------------------------------------------------------- #
# Noncritical happy path: dry-run reaches "executed" without a real tag/push.
# --------------------------------------------------------------------------- #
def test_noncritical_path_reaches_release_in_dry_run(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    result = _run(repo, ci_status="green", criticality="noncritical")

    assert result["result"] == orch.RESULT_EXECUTED
    assert result["dry_run"] is True
    assert result["mutated"] is False  # dry-run mutates nothing
    assert result["target_tag"] == "v0.2.1"
    assert result["council_gate"]["status"] == "pass"
    assert result["execution_gate"]["status"] == "pass"
    # Owner notification record was written.
    assert result["owner_notification"]["record"]["tag_pushed"] is False
    assert Path(result["owner_notification"]["out"]).exists()


def test_dry_run_creates_no_git_tag(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    _run(repo, ci_status="green", criticality="noncritical")

    tags = subprocess.run(
        ["git", "tag", "--list"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.split()
    # Only the baseline tag exists; the orchestrator's dry-run created no new tag.
    assert tags == ["v0.2.0"]
    assert "v0.2.1" not in tags


def test_dry_run_does_not_bump_pyproject(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    _run(repo, ci_status="green", criticality="noncritical")
    assert 'version = "0.2.0"' in (repo / "pyproject.toml").read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Critical / major / flagged paths: halt with owner-approval-required, no mutation.
# --------------------------------------------------------------------------- #
def test_critical_criticality_halts_for_owner(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    result = _run(repo, ci_status="green", criticality="critical")

    assert result["result"] == orch.RESULT_OWNER_REQUIRED
    assert result["owner_action_required"] is True
    assert result["mutated"] is False
    assert any("criticality:critical" in f for f in result["blocking_flags"])


@pytest.mark.parametrize("flag", sorted(orch.CRITICAL_FLAGS))
def test_each_critical_flag_halts_for_owner(tmp_path: Path, flag: str) -> None:
    repo = _make_repo(tmp_path)
    result = _run(repo, ci_status="green", criticality="noncritical", critical_flags=[flag])

    assert result["result"] == orch.RESULT_OWNER_REQUIRED
    assert flag in result["blocking_flags"]
    assert result["mutated"] is False
    # No release decision/notification is produced on the Owner-required path.
    assert "owner_notification" not in result


def test_major_or_breaking_flag_halts(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    result = _run(
        repo,
        ci_status="green",
        criticality="noncritical",
        critical_flags=["major_or_breaking_release"],
    )
    assert result["result"] == orch.RESULT_OWNER_REQUIRED
    assert "major_or_breaking_release" in result["blocking_flags"]


# --------------------------------------------------------------------------- #
# CI / SHA safety gate.
# --------------------------------------------------------------------------- #
def test_non_green_ci_blocks_release(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    result = _run(repo, ci_status="failed", criticality="noncritical")
    assert result["result"] == orch.RESULT_NOT_GREEN
    assert result["mutated"] is False


def test_sha_mismatch_blocks_release(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    result = _run(
        repo,
        ci_status="green",
        criticality="noncritical",
        validated_sha="0000000000000000000000000000000000000000",
    )
    assert result["result"] == orch.RESULT_NOT_GREEN
    assert result["sha_match"] is False
    assert result["mutated"] is False


def test_matching_validated_sha_allows_release(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()
    result = _run(repo, ci_status="green", criticality="noncritical", validated_sha=head)
    assert result["result"] == orch.RESULT_EXECUTED


# --------------------------------------------------------------------------- #
# Cadence gate.
# --------------------------------------------------------------------------- #
def test_not_triggered_does_nothing(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, triggered=False)
    result = _run(repo, ci_status="green", criticality="noncritical")
    assert result["result"] == orch.RESULT_NOT_TRIGGERED
    assert result["mutated"] is False


# --------------------------------------------------------------------------- #
# Decision artifact correctness.
# --------------------------------------------------------------------------- #
def test_decision_record_is_agent_council_noncritical(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    result = _run(repo, ci_status="green", criticality="noncritical")
    decision_text = Path(result["decision_path"]).read_text(encoding="utf-8")
    assert "status: agent_council_approved" in decision_text
    assert "approved_by: agent-release-council" in decision_text
    assert "criticality: noncritical" in decision_text
    assert "owner_required: false" in decision_text
    assert "critical_flags: []" in decision_text
    # W4b independent role votes for all four required roles.
    for role in orch.REQUIRED_ROLES:
        assert f"role: {role}" in decision_text
    assert "w4b_independent" in decision_text


# --------------------------------------------------------------------------- #
# CLI exit-code contract.
# --------------------------------------------------------------------------- #
def _run_cli(repo: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(repo), *extra],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_cli_owner_required_exits_nonzero(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    result = _run_cli(repo, "--criticality", "critical")
    assert result.returncode == orch._EXIT_CODES[orch.RESULT_OWNER_REQUIRED]
    assert "OWNER APPROVAL REQUIRED" in result.stdout


def test_cli_defaults_to_dry_run_no_tag(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    result = _run_cli(repo)  # no --execute -> dry-run
    assert result.returncode == 0
    tags = subprocess.run(
        ["git", "tag", "--list"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.split()
    assert tags == ["v0.2.0"]  # never created v0.2.1


def test_cli_dry_run_flag_overrides_execute(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    # Even with --execute, --dry-run must win and create no tag.
    result = _run_cli(repo, "--execute", "--dry-run")
    assert result.returncode == 0
    tags = subprocess.run(
        ["git", "tag", "--list"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.split()
    assert "v0.2.1" not in tags


def test_cli_output_is_ascii(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    result = _run_cli(repo)
    result.stdout.encode("ascii")


# --------------------------------------------------------------------------- #
# Source-level safety guard: no unguarded tag/push at import/decision level.
# --------------------------------------------------------------------------- #
def test_orchestrator_default_is_dry_run() -> None:
    """orchestrate() must default to NOT executing (dry-run) so it cannot mutate."""
    import inspect

    sig = inspect.signature(orch.orchestrate)
    assert sig.parameters["execute"].default is False


def test_release_auto_workflow_fires_on_test_completion_and_releases_validated_sha() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "release-auto.yml").read_text(encoding="utf-8")
    # Metric-bound: fires right after a `test` run completes (not weekly-cron-only).
    assert "workflow_run:" in workflow
    assert 'workflows: ["test"]' in workflow
    # Releases the CI-validated green SHA by checking it out, instead of requiring
    # it to still equal a fast-moving main HEAD (the old perpetual-skip cause).
    assert "github.event.workflow_run.head_sha" in workflow
    assert "ref: ${{ steps.validated.outputs.validated_sha }}" in workflow
    assert "moved past the CI-validated" not in workflow
