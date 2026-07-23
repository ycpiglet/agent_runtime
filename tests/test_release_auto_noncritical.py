"""Tests for scripts/release_auto_noncritical.py (TASK-AR-586).

These prove the orchestrator's decision boundaries WITHOUT ever creating a real
git tag or pushing: every test runs in the default dry-run mode against a
throwaway temp git repo, so the host repository is never touched.
"""

from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
import time
import types
from pathlib import Path

import pytest

from scripts import release_auto_noncritical as orch
from scripts import release_execution_gate as execution_gate

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "release_auto_noncritical.py"
CADENCE_SCRIPT = REPO_ROOT / "scripts" / "release_cadence_trigger.py"

_URL_USERINFO_RE = re.compile(r"(?i)([a-z][a-z0-9+.-]*://)[^/@\s]+@")
_SENSITIVE_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(password|passwd|token|access[_-]?token|secret|authorization)"
    r"\s*[:=]\s*[^\r\n]*"
)
_FIXTURE_GIT_RETRY_DELAYS = (0.1, 0.2, 0.4, 0.8, 1.0)
_FIXTURE_GIT_MAX_ATTEMPTS = len(_FIXTURE_GIT_RETRY_DELAYS) + 1


def _sanitize_git_diagnostic(value: str) -> str:
    value = _URL_USERINFO_RE.sub(r"\1[REDACTED]@", value)
    return _SENSITIVE_ASSIGNMENT_RE.sub(r"\1=[REDACTED]", value)


def _is_retryable_fixture_commit_failure(
    command: list[str], result: subprocess.CompletedProcess[str]
) -> bool:
    """Recognize only the observed pre-commit HEAD parse transient.

    Git mutations are not generally idempotent, so ambiguous failures must not
    be replayed. This exact result occurs before `git commit` advances HEAD and
    is therefore the sole bounded-retry exception for this test fixture.
    """
    return (
        command[1:2] == ["commit"]
        and result.returncode == 128
        and not (result.stdout or "").strip()
        and (result.stderr or "").strip() == "fatal: could not parse HEAD"
    )


def _git(repo: Path, *args: str, env: dict[str, str] | None = None) -> None:
    merged = dict(os.environ)
    if env:
        merged.update(env)
    command = ["git", *args]
    attempts = 0
    while True:
        attempts += 1
        result = subprocess.run(
            command,
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=merged,
        )
        if result.returncode == 0:
            return
        if (
            attempts >= _FIXTURE_GIT_MAX_ATTEMPTS
            or not _is_retryable_fixture_commit_failure(command, result)
        ):
            break
        time.sleep(_FIXTURE_GIT_RETRY_DELAYS[attempts - 1])

    if result.returncode != 0:
        rendered_command = subprocess.list2cmdline(
            [_sanitize_git_diagnostic(part) for part in command]
        )
        stdout = _sanitize_git_diagnostic(result.stdout or "<empty>")
        stderr = _sanitize_git_diagnostic(result.stderr or "<empty>")
        raise AssertionError(
            "git helper failed\n"
            f"command: {rendered_command}\n"
            f"return code: {result.returncode}\n"
            f"attempts: {attempts}\n"
            f"stdout:\n{stdout}\n"
            f"stderr:\n{stderr}"
        )


def test_git_failure_reports_sanitized_command_and_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    command_url = "https://user:top-secret@example.invalid/repo.git"
    failure = subprocess.CompletedProcess(
        args=["git", "fetch", command_url],
        returncode=128,
        stdout="fetch started\n",
        stderr=(
            f"fatal: unable to access '{command_url}'\n"
            "debug: authorization: Bearer secondary-secret\n"
        ),
    )
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: failure)

    with pytest.raises(AssertionError) as caught:
        _git(tmp_path, "fetch", command_url)

    message = str(caught.value)
    expected_command = "command: git fetch https://[REDACTED]@example.invalid/repo.git"
    assert expected_command in message
    assert "return code: 128" in message
    assert "stdout:\nfetch started" in message
    assert "stderr:\nfatal: unable to access" in message
    assert "top-secret" not in message
    assert "secondary-secret" not in message
    assert "authorization=[REDACTED]" in message


def test_git_recovers_one_transient_fixture_commit_head_parse_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    attempts = 0
    sleeps: list[float] = []

    def _run(command, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return subprocess.CompletedProcess(
                command,
                returncode=128,
                stdout="",
                stderr="fatal: could not parse HEAD\n",
            )
        return subprocess.CompletedProcess(command, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", _run)
    monkeypatch.setattr(time, "sleep", sleeps.append)

    _git(tmp_path, "commit", "--allow-empty", "-q", "-m", "chore: tick 36")

    assert attempts == 2
    assert sleeps == [0.1]


def test_git_recovers_after_three_transient_fixture_commit_head_parse_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    attempts = 0
    sleeps: list[float] = []

    def _run(command, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts <= 3:
            return subprocess.CompletedProcess(
                command,
                returncode=128,
                stdout="",
                stderr="fatal: could not parse HEAD\n",
            )
        return subprocess.CompletedProcess(command, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", _run)
    monkeypatch.setattr(time, "sleep", sleeps.append)

    _git(tmp_path, "commit", "--allow-empty", "-q", "-m", "chore: tick 36")

    assert attempts == 4
    assert sleeps == [0.1, 0.2, 0.4]


def test_git_exhausts_recognized_fixture_commit_head_parse_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    attempts = 0
    sleeps: list[float] = []

    def _run(command, **kwargs):
        nonlocal attempts
        attempts += 1
        return subprocess.CompletedProcess(
            command,
            returncode=128,
            stdout="",
            stderr="fatal: could not parse HEAD\n",
        )

    monkeypatch.setattr(subprocess, "run", _run)
    monkeypatch.setattr(time, "sleep", sleeps.append)

    with pytest.raises(AssertionError) as caught:
        _git(tmp_path, "commit", "--allow-empty", "-q", "-m", "chore: tick 36")

    assert attempts == 6
    assert sleeps == [0.1, 0.2, 0.4, 0.8, 1.0]
    assert sum(sleeps) == 2.5
    assert "attempts: 6" in str(caught.value)
    assert "fatal: could not parse HEAD" in str(caught.value)


@pytest.mark.parametrize(
    ("args", "returncode", "stdout", "stderr"),
    [
        (("commit", "--allow-empty", "-m", "x"), 1, "", "fatal: could not parse HEAD"),
        (("commit", "--allow-empty", "-m", "x"), 128, "created", "fatal: could not parse HEAD"),
        (
            ("commit", "--allow-empty", "-m", "x"),
            128,
            "",
            "fatal: could not parse HEAD\nfatal: detected dubious ownership",
        ),
        (("rev-parse", "HEAD"), 128, "", "fatal: could not parse HEAD"),
    ],
)
def test_git_does_not_retry_ambiguous_or_unrelated_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    args: tuple[str, ...],
    returncode: int,
    stdout: str,
    stderr: str,
) -> None:
    attempts = 0

    def _run(command, **kwargs):
        nonlocal attempts
        attempts += 1
        return subprocess.CompletedProcess(
            command,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )

    monkeypatch.setattr(subprocess, "run", _run)

    with pytest.raises(AssertionError) as caught:
        _git(tmp_path, *args)

    assert attempts == 1
    assert "attempts: 1" in str(caught.value)


def test_git_stops_when_retryable_failure_is_followed_by_ambiguous_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    responses = [
        subprocess.CompletedProcess(
            ["git", "commit"],
            returncode=128,
            stdout="",
            stderr="fatal: could not parse HEAD",
        ),
        subprocess.CompletedProcess(
            ["git", "commit"],
            returncode=128,
            stdout="",
            stderr="fatal: detected dubious ownership",
        ),
    ]
    sleeps: list[float] = []

    def _run(command, **kwargs):
        return responses.pop(0)

    monkeypatch.setattr(subprocess, "run", _run)
    monkeypatch.setattr(time, "sleep", sleeps.append)

    with pytest.raises(AssertionError) as caught:
        _git(tmp_path, "commit", "--allow-empty", "-m", "x")

    assert responses == []
    assert sleeps == [0.1]
    assert "attempts: 2" in str(caught.value)
    assert "fatal: detected dubious ownership" in str(caught.value)


def _commit(repo: Path, subject: str, *, env: dict[str, str] | None = None) -> None:
    _git(repo, "commit", "--allow-empty", "-q", "-m", subject, env=env)


def test_git_real_fixture_commit_after_three_transients_advances_head_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "commit.gpgsign", "false")
    _commit(repo, "chore: init")

    actual_run = subprocess.run
    transient_failures = 3
    commit_attempts = 0
    sleeps: list[float] = []

    def _run(command, **kwargs):
        nonlocal transient_failures, commit_attempts
        if command[1:2] == ["commit"]:
            commit_attempts += 1
            if transient_failures:
                transient_failures -= 1
                return subprocess.CompletedProcess(
                    command,
                    returncode=128,
                    stdout="",
                    stderr="fatal: could not parse HEAD\n",
                )
        return actual_run(command, **kwargs)

    before = int(
        actual_run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    monkeypatch.setattr(subprocess, "run", _run)
    monkeypatch.setattr(time, "sleep", sleeps.append)

    _commit(repo, "chore: tick 36")

    after = int(
        actual_run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    subjects = actual_run(
        ["git", "log", "--format=%s"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    assert commit_attempts == 4
    assert transient_failures == 0
    assert sleeps == [0.1, 0.2, 0.4]
    assert after - before == 1
    assert subjects.count("chore: tick 36") == 1


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


def _successful_cadence_query(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    """Return deterministic cadence answers for release-auto injection tests."""
    args = list(cmd[1:])
    if args == ["describe", "--tags", "--abbrev=0"]:
        stdout = "v0.2.0\n"
    elif args[:2] == ["log", "--format=%s"]:
        stdout = "".join(f"chore: tick {index}\n" for index in range(40))
    elif args[:2] == ["rev-list", "--count"]:
        stdout = "40\n"
    elif args[:3] == ["log", "-1", "--format=%ct"]:
        stdout = "1767225600\n"
    elif args[:2] == ["log", "--format=%s%n%b%x00"]:
        stdout = "".join(f"chore: tick {index}\x00" for index in range(40))
    elif args[:2] in (["diff", "--name-status"], ["diff", "--name-only"]):
        stdout = ""
    else:
        raise AssertionError(f"unexpected cadence query: {args!r}")
    return subprocess.CompletedProcess(cmd, returncode=0, stdout=stdout, stderr="")


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


def test_release_auto_surfaces_owner_approval_via_github_issue() -> None:
    # A non-patch (minor/major) release halts for Owner approval (NONCRITICAL_BUMPS =
    # {"patch"}). That halt must reach the Owner PROACTIVELY -- a GitHub issue -- not
    # just sit in the Actions run summary nobody watches. Regression guard for the
    # silent-owner-notification gap.
    workflow = (REPO_ROOT / ".github" / "workflows" / "release-auto.yml").read_text(encoding="utf-8")
    assert "issues: write" in workflow  # GITHUB_TOKEN may open/close issues
    assert "owner-approval-required" in workflow
    assert "gh issue create" in workflow  # open when approval is needed
    assert "gh issue close" in workflow  # close once a release executes
    assert "[release-auto] Release pending Owner approval" in workflow  # single dedup'd issue


def test_release_auto_workflow_persists_the_orchestrator_result_file() -> None:
    # The notify + Owner-approval-issue steps read .tmp/release-auto-result.json. But
    # .tmp/ is gitignored and absent in a fresh CI checkout, so `tee` used to fail to
    # create the file while PIPESTATUS[0] masked the failure — every notification step
    # then skipped with "no orchestrator result file" and the Owner was never told a
    # release was pending (v0.6.0 sat unnoticed from 2026-06-29, run 28353042537).
    workflow = (REPO_ROOT / ".github" / "workflows" / "release-auto.yml").read_text(encoding="utf-8")
    mkdir_pos = workflow.find("mkdir -p .tmp")
    tee_pos = workflow.find("tee .tmp/release-auto-result.json")
    assert mkdir_pos != -1, "workflow must create .tmp before tee-ing the result file"
    assert tee_pos != -1
    assert mkdir_pos < tee_pos
    # And a missing result file must fail loudly instead of silently skipping notify.
    assert "result file was not written" in workflow


def test_auto_merge_dispatches_main_ci_after_merging() -> None:
    # Pushes made with GITHUB_TOKEN do not trigger `on: push` workflows
    # (recursion prevention), so auto-merged commits never ran test.yml on
    # main: post-merge integration CI was weekly-cron only and the
    # metric-bound release-auto trigger (PR #183) silently degenerated back
    # to weekly. auto-merge must chain main CI via workflow_dispatch — the
    # documented exception to that prevention.
    workflow = (REPO_ROOT / ".github" / "workflows" / "auto-merge.yml").read_text(encoding="utf-8")
    merge_pos = workflow.find("gh pr merge")
    dispatch_pos = workflow.find("gh workflow run test.yml")
    assert dispatch_pos != -1, "auto-merge must dispatch main CI after merging"
    assert merge_pos != -1 and merge_pos < dispatch_pos
    assert "--ref main" in workflow


def test_auto_merge_has_actions_write_for_main_ci_dispatch() -> None:
    # gh workflow run needs `actions: write`; without it the dispatch fails
    # 403 behind the non-fatal guard and main silently stays unvalidated
    # (observed on the first post-merge dispatch attempt, 2026-07-03).
    workflow = (REPO_ROOT / ".github" / "workflows" / "auto-merge.yml").read_text(encoding="utf-8")
    assert "actions: write" in workflow


# --------------------------------------------------------------------------- #
# Trigger evaluation failure: loud, never a quiet "not-triggered" exit 0.
# --------------------------------------------------------------------------- #
def test_trigger_git_query_error_halts_loud(tmp_path: Path, monkeypatch) -> None:
    repo = _make_repo(tmp_path)

    def _error_report(root, now_ts=None):
        return {
            "triggered": False,
            "status": "error",
            "reason": "git-query-error",
            "git_query_errors": [
                {"command": "git describe --tags --abbrev=0", "error": "OSError: spawn failed"}
            ],
        }

    monkeypatch.setattr(orch.cadence, "build_report", _error_report)
    result = _run(repo, ci_status="green", criticality="noncritical")

    assert result["result"] == orch.RESULT_TRIGGER_ERROR
    assert result["mutated"] is False
    assert result["git_query_errors"]
    # Exit-code contract: an unevaluated trigger is NOT "nothing to do".
    assert orch._EXIT_CODES[orch.RESULT_TRIGGER_ERROR] != 0


def test_unexpected_nonzero_cadence_query_halts_release_auto_loud(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _make_repo(tmp_path)
    spec = importlib.util.spec_from_file_location(
        "release_cadence_trigger_release_auto_nonzero", CADENCE_SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.subprocess = types.SimpleNamespace(run=subprocess.run)
    module.time = types.SimpleNamespace(sleep=time.sleep, time=time.time)
    monkeypatch.setattr(module.time, "sleep", lambda _s: None)

    def _nonzero(cmd, **kwargs):
        return subprocess.CompletedProcess(
            cmd,
            returncode=128,
            stdout="",
            stderr="fatal: transient runner resource failure",
        )

    monkeypatch.setattr(module.subprocess, "run", _nonzero)
    monkeypatch.setattr(orch, "cadence", module)
    result = _run(repo, ci_status="green", criticality="noncritical")

    assert result["result"] == orch.RESULT_TRIGGER_ERROR
    assert result["mutated"] is False
    assert result["git_query_errors"]


def test_partial_cadence_query_error_halts_even_when_commit_threshold_fires(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _make_repo(tmp_path)
    spec = importlib.util.spec_from_file_location(
        "release_cadence_trigger_release_auto_partial_query", CADENCE_SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.subprocess = types.SimpleNamespace(run=_successful_cadence_query)
    module.time = types.SimpleNamespace(sleep=time.sleep, time=time.time)
    monkeypatch.setattr(module.time, "sleep", lambda _s: None)
    failed_diff_calls = 0

    def _fail_diff_queries(cmd, **kwargs):
        nonlocal failed_diff_calls
        if len(cmd) > 1 and cmd[1] == "diff":
            failed_diff_calls += 1
            return subprocess.CompletedProcess(
                cmd,
                returncode=128,
                stdout="",
                stderr="fatal: transient runner resource failure",
            )
        return _successful_cadence_query(cmd)

    monkeypatch.setattr(module.subprocess, "run", _fail_diff_queries)
    monkeypatch.setattr(orch, "cadence", module)
    result = _run(repo, ci_status="green", criticality="noncritical")

    assert failed_diff_calls == 6
    assert result["cadence"]["triggered"] is False
    assert result["result"] == orch.RESULT_TRIGGER_ERROR
    assert result["mutated"] is False
    assert len(result["git_query_errors"]) == 2


def test_genuinely_quiet_repo_is_still_not_triggered(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, triggered=False)
    result = _run(repo, ci_status="green", criticality="noncritical")

    assert result["result"] == orch.RESULT_NOT_TRIGGERED
    assert "git_query_errors" not in result
    assert orch._EXIT_CODES[orch.RESULT_NOT_TRIGGERED] == 0


def test_release_auto_workflow_fails_red_on_trigger_error() -> None:
    # Exit 5 (trigger-error) means the cadence trigger never got answers out of
    # git: the cycle was NOT assessed. The workflow must fail the step (red run)
    # instead of folding it into the "clean stop" non-zero family, or a git
    # spawn failure silently skips a release cycle with a green run.
    workflow = (REPO_ROOT / ".github" / "workflows" / "release-auto.yml").read_text(encoding="utf-8")
    assert '"$rc" = "5"' in workflow
    assert "release cycle was not assessed" in workflow
