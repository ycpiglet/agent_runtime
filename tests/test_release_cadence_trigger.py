from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "release_cadence_trigger.py"
TEMPLATE_SCRIPT = (
    REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "release_cadence_trigger.py"
)


def _run_trigger(root: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), "--check", *extra],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


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


def test_below_thresholds_is_silent_and_exits_zero(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "tag", "v0.1.0")
    _commit(repo, "chore: small change")
    _commit(repo, "fix: tiny fix")

    result = _run_trigger(repo)

    assert result.returncode == 0
    assert result.stdout.strip() == ""
    assert result.stderr.strip() == ""


def test_below_thresholds_verbose_prints_metrics(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "tag", "v0.1.0")
    _commit(repo, "chore: small change")

    result = _run_trigger(repo, "--verbose")

    assert result.returncode == 0
    assert "release-cadence: pass below-thresholds" in result.stdout
    assert "commits=1" in result.stdout


def test_commit_threshold_triggers_patch_proposal(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "tag", "v0.1.0")
    for index in range(40):
        _commit(repo, f"chore: tick {index}")

    result = _run_trigger(repo)

    assert result.returncode == 0
    assert "finding=release-cadence:proposal" in result.stdout
    assert "recommended_bump=patch" in result.stdout
    assert "recommended_version=0.1.1" in result.stdout
    assert "commits>=40 (actual 40)" in result.stdout
    assert "bump targets: pyproject.toml" in result.stdout


def test_feat_threshold_triggers_proposal(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "tag", "v0.1.0")
    for index in range(5):
        _commit(repo, f"feat(core): feature {index}")

    result = _run_trigger(repo)

    assert result.returncode == 0
    assert "finding=release-cadence:proposal" in result.stdout
    assert "feat>=5 (actual 5)" in result.stdout


def test_days_threshold_triggers_proposal(tmp_path: Path) -> None:
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
    _commit(repo, "chore: trailing work")

    result = _run_trigger(repo)

    assert result.returncode == 0
    assert "finding=release-cadence:proposal" in result.stdout
    assert "days>=14" in result.stdout


def test_schema_change_recommends_minor(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "tag", "v0.1.0")
    schema = repo / "schemas" / "demo.schema.json"
    schema.parent.mkdir(parents=True, exist_ok=True)
    schema.write_text("{}\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _commit(repo, "feat: add schema")

    result = _run_trigger(repo, "--commits-threshold", "1")

    assert result.returncode == 0
    assert "recommended_bump=minor" in result.stdout
    assert "recommended_version=0.2.0" in result.stdout
    assert "schema-changed:schemas/demo.schema.json" in result.stdout


def test_template_deletion_recommends_minor(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    template = repo / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "old_tool.py"
    template.parent.mkdir(parents=True, exist_ok=True)
    template.write_text("print('old')\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _commit(repo, "chore: add template tool")
    _git(repo, "tag", "v0.1.0")
    _git(repo, "rm", "-q", template.relative_to(repo).as_posix())
    _commit(repo, "refactor: drop template tool")

    result = _run_trigger(repo, "--commits-threshold", "1")

    assert result.returncode == 0
    assert "recommended_bump=minor" in result.stdout
    assert "template-deleted-or-renamed:" in result.stdout


def test_feat_commits_recommend_minor(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "tag", "v0.1.0")
    for index in range(5):
        _commit(repo, f"feat(core): feature {index}")

    result = _run_trigger(repo)

    assert result.returncode == 0
    assert "recommended_bump=minor" in result.stdout
    assert "recommended_version=0.2.0" in result.stdout


def test_breaking_change_bang_recommends_major(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "tag", "v0.1.0")
    _commit(repo, "feat(core)!: drop legacy api")

    result = _run_trigger(repo, "--commits-threshold", "1")

    assert result.returncode == 0
    assert "recommended_bump=major" in result.stdout
    assert "recommended_version=1.0.0" in result.stdout


def test_breaking_change_footer_recommends_major(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "tag", "v0.1.0")
    _git(
        repo,
        "commit",
        "--allow-empty",
        "-q",
        "-m",
        "feat(core): rework pipeline",
        "-m",
        "BREAKING CHANGE: removes the old trigger contract",
    )

    result = _run_trigger(repo, "--commits-threshold", "1")

    assert result.returncode == 0
    assert "recommended_bump=major" in result.stdout
    assert "recommended_version=1.0.0" in result.stdout


def test_fix_only_stays_patch(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "tag", "v0.1.0")
    for index in range(3):
        _commit(repo, f"fix: bug {index}")

    result = _run_trigger(repo, "--commits-threshold", "1")

    assert result.returncode == 0
    assert "recommended_bump=patch" in result.stdout
    assert "recommended_version=0.1.1" in result.stdout


def test_no_tags_is_graceful_and_silent(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _commit(repo, "feat: work without any tag")

    result = _run_trigger(repo)
    assert result.returncode == 0
    assert result.stdout.strip() == ""

    verbose = _run_trigger(repo, "--verbose")
    assert verbose.returncode == 0
    assert "no-baseline-tag" in verbose.stdout


def test_bump_targets_reuse_release_steward_file_list(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    release = repo / "agents" / "project" / "release" / "RELEASE.yml"
    release.parent.mkdir(parents=True, exist_ok=True)
    release.write_text("version: 0.1.0\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _commit(repo, "chore: record release state")
    _git(repo, "tag", "v0.1.0")
    _commit(repo, "feat: more work")

    result = _run_trigger(repo, "--commits-threshold", "1")

    assert result.returncode == 0
    assert "bump targets: pyproject.toml, agents/project/release/RELEASE.yml" in result.stdout


def test_check_output_is_ascii_only(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "tag", "v0.1.0")
    for index in range(3):
        _commit(repo, f"feat: feature {index}")

    result = _run_trigger(repo, "--feat-threshold", "1")

    assert result.returncode == 0
    result.stdout.encode("ascii")


def test_owner_governance_chain_wires_release_cadence_trigger() -> None:
    root_gate = (REPO_ROOT / "scripts" / "owner_governance_gate.py").read_text(encoding="utf-8")
    template_gate = (
        REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "owner_governance_gate.py"
    ).read_text(encoding="utf-8")

    for gate in (root_gate, template_gate):
        assert '"scripts/release_cadence_trigger.py", "--check"' in gate


def test_template_script_copy_matches_root_script() -> None:
    assert TEMPLATE_SCRIPT.read_text(encoding="utf-8") == SCRIPT.read_text(encoding="utf-8")


def test_swallowed_error_is_visible_on_stdout(tmp_path: Path, monkeypatch) -> None:
    # The watch-only blanket handler converts any build_report exception into
    # exit 0 under --check. That used to leave stdout completely EMPTY, which
    # read as a silent skip and made CI flakes undiagnosable (2026-07-03 CI:
    # 'finding=... in ""'). The error must be mirrored to stdout.
    import importlib.util

    spec = importlib.util.spec_from_file_location("release_cadence_trigger_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def _boom(*args, **kwargs):
        raise RuntimeError("transient runner failure")

    monkeypatch.setattr(module, "build_report", _boom)
    import io
    from contextlib import redirect_stdout

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        rc = module.main(["--root", str(tmp_path), "--check"])

    assert rc == 0
    assert "release-cadence: error RuntimeError" in buffer.getvalue()


# --------------------------------------------------------------------------- #
# Git query failures must be an ERROR, never a quiet "not-triggered" pass.
# (2026-07-03 main CI flake: a transient git spawn failure inside the trigger
# collapsed commits to 0, release-auto reported 'not-triggered' with exit 0,
# and a whole release cycle would have been silently skipped in production.)
# --------------------------------------------------------------------------- #
def _load_module():
    import importlib.util
    import types

    spec = importlib.util.spec_from_file_location("release_cadence_trigger_query_errors", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # The imported module initially holds process-global mutable modules. Give
    # query-error tests private facades so monkeypatching retry seams cannot
    # leak into unrelated tests or background activity in collection order.
    module.subprocess = types.SimpleNamespace(run=subprocess.run)
    module.time = types.SimpleNamespace(sleep=time.sleep, time=time.time)
    return module


def _successful_cadence_query(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    """Return a complete, deterministic tagged-repository query surface.

    Query-failure tests must fail only the query selected by the scenario. A
    fallback to real Git lets an unrelated runner transient stop build_report()
    before the selected query is reached and turns the retry-count assertion
    into a false failure.
    """
    args = list(cmd[1:])
    if args == ["describe", "--tags", "--abbrev=0"]:
        stdout = "v0.1.0\n"
    elif args == ["log", "--format=%s", "v0.1.0..HEAD"]:
        stdout = "".join(
            f"{'feat' if index < 5 else 'chore'}: tick {index}\n"
            for index in range(40)
        )
    elif args == ["rev-list", "--count", "v0.1.0..HEAD"]:
        stdout = "40\n"
    elif args == ["log", "-1", "--format=%ct", "v0.1.0"]:
        stdout = "1767225600\n"
    elif args == ["log", "--format=%s%n%b%x00", "v0.1.0..HEAD"]:
        stdout = "".join(f"chore: tick {index}\x00" for index in range(40))
    elif args == [
        "diff",
        "--name-status",
        "v0.1.0..HEAD",
        "--",
        "src/agent_runtime/templates/",
    ] or args == ["diff", "--name-only", "v0.1.0..HEAD", "--", "schemas/"]:
        stdout = ""
    else:
        raise AssertionError(f"unexpected cadence query: {args!r}")
    return subprocess.CompletedProcess(cmd, returncode=0, stdout=stdout, stderr="")


def test_successful_cadence_query_rejects_wrong_range() -> None:
    with pytest.raises(AssertionError, match="unexpected cadence query"):
        _successful_cadence_query(["git", "log", "--format=%s", "WRONG..HEAD"])


def test_loaded_module_subprocess_patch_is_process_local(monkeypatch) -> None:
    module = _load_module()
    parent_run = subprocess.run
    parent_sleep = time.sleep

    def _sentinel(*args, **kwargs):
        raise AssertionError("test-only subprocess sentinel")

    monkeypatch.setattr(module.subprocess, "run", _sentinel)
    monkeypatch.setattr(module.time, "sleep", _sentinel)

    assert subprocess.run is parent_run
    assert time.sleep is parent_sleep


def test_spawn_failure_reports_git_query_error(tmp_path: Path, monkeypatch) -> None:
    module = _load_module()
    monkeypatch.setattr(module.time, "sleep", lambda _s: None)

    def _boom(*args, **kwargs):
        raise OSError("spawn failed")

    monkeypatch.setattr(module.subprocess, "run", _boom)
    report = module.build_report(tmp_path)

    assert report["status"] == "error"
    assert report["triggered"] is False
    assert report["reason"] == "git-query-error"
    assert report["git_query_errors"]
    assert "describe" in report["git_query_errors"][0]["command"]
    assert "OSError" in report["git_query_errors"][0]["error"]


def test_signal_killed_git_is_retried_then_recorded(tmp_path: Path, monkeypatch) -> None:
    module = _load_module()
    monkeypatch.setattr(module.time, "sleep", lambda _s: None)
    calls: list[list[str]] = []

    def _killed(cmd, **kwargs):
        calls.append(list(cmd))
        return subprocess.CompletedProcess(cmd, returncode=-9, stdout="", stderr="")

    monkeypatch.setattr(module.subprocess, "run", _killed)
    module._QUERY_ERRORS.clear()
    out = module._git(tmp_path, "describe", "--tags")

    assert out is None
    # A signal death is transient, not a deterministic git answer: retried.
    assert len(calls) == 3
    assert module._QUERY_ERRORS
    assert "signal 9" in module._QUERY_ERRORS[0]["error"]


def test_transient_spawn_failure_recovers_without_error(tmp_path: Path, monkeypatch) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "tag", "v0.1.0")
    for index in range(41):
        _commit(repo, f"chore: tick {index}")

    module = _load_module()
    monkeypatch.setattr(module.time, "sleep", lambda _s: None)
    real_run = subprocess.run
    state = {"raised": False}

    def _flaky_once(cmd, **kwargs):
        if not state["raised"]:
            state["raised"] = True
            raise OSError("transient spawn failure")
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(module.subprocess, "run", _flaky_once)
    report = module.build_report(repo)

    assert report["triggered"] is True
    assert report["status"] == "watch"
    assert "git_query_errors" not in report


def test_transient_nonzero_git_failure_recovers_without_error(tmp_path: Path, monkeypatch) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "tag", "v0.1.0")
    for index in range(41):
        _commit(repo, f"chore: tick {index}")

    module = _load_module()
    monkeypatch.setattr(module.time, "sleep", lambda _s: None)
    real_run = subprocess.run
    state = {"failed": False}

    def _nonzero_once(cmd, **kwargs):
        if not state["failed"]:
            state["failed"] = True
            return subprocess.CompletedProcess(
                cmd,
                returncode=128,
                stdout="",
                stderr="fatal: transient runner resource failure",
            )
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(module.subprocess, "run", _nonzero_once)
    report = module.build_report(repo)

    assert report["triggered"] is True
    assert report["status"] == "watch"
    assert "git_query_errors" not in report


def test_exhausted_unexpected_nonzero_git_failure_is_error(tmp_path: Path, monkeypatch) -> None:
    module = _load_module()
    monkeypatch.setattr(module.time, "sleep", lambda _s: None)
    calls: list[list[str]] = []

    def _nonzero(cmd, **kwargs):
        calls.append(list(cmd))
        return subprocess.CompletedProcess(
            cmd,
            returncode=128,
            stdout="",
            stderr=(
                "fatal: transient runner resource failure "
                "token=top-secret https://runner:password@example.invalid/repo.git"
            ),
        )

    monkeypatch.setattr(module.subprocess, "run", _nonzero)
    report = module.build_report(tmp_path)

    assert len(calls) == 3
    assert report["status"] == "error"
    assert report["triggered"] is False
    assert report["reason"] == "git-query-error"
    assert report["git_query_errors"]
    error = report["git_query_errors"][0]
    assert error["returncode"] == 128
    assert "transient runner resource failure" in error["error"]
    assert "top-secret" not in error["error"]
    assert "password" not in error["error"]
    assert "[REDACTED]" in error["error"]


def test_partial_query_error_overrides_other_trigger_metrics(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path

    module = _load_module()
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
    report = module.build_report(repo)

    assert failed_diff_calls == 6
    assert report["metrics"]["commits"] == 40
    assert report["status"] == "error"
    assert report["triggered"] is False
    assert report["finding"] is None
    assert report["reason"] == "git-query-error"
    assert len(report["git_query_errors"]) == 2
    assert report["recommended_bump"] is None
    assert report["recommended_version"] is None


@pytest.mark.parametrize(
    "query_kind",
    [
        "subjects",
        "commit-count",
        "tag-time",
        "breaking",
        "template-diff",
        "schema-diff",
    ],
)
def test_each_partial_query_failure_invalidates_triggered_report(
    tmp_path: Path, monkeypatch, query_kind: str
) -> None:
    repo = tmp_path

    module = _load_module()
    monkeypatch.setattr(module.time, "sleep", lambda _s: None)
    failed_calls = 0

    def _matches(args: list[str]) -> bool:
        if query_kind == "subjects":
            return args[:2] == ["log", "--format=%s"]
        if query_kind == "commit-count":
            return args[:2] == ["rev-list", "--count"]
        if query_kind == "tag-time":
            return args[:3] == ["log", "-1", "--format=%ct"]
        if query_kind == "breaking":
            return args[:2] == ["log", "--format=%s%n%b%x00"]
        if query_kind == "template-diff":
            return args[:2] == ["diff", "--name-status"]
        return args[:2] == ["diff", "--name-only"]

    def _fail_selected(cmd, **kwargs):
        nonlocal failed_calls
        if _matches(list(cmd[1:])):
            failed_calls += 1
            return subprocess.CompletedProcess(
                cmd,
                returncode=128,
                stdout="",
                stderr=f"fatal: {query_kind} query unavailable",
            )
        return _successful_cadence_query(cmd)

    monkeypatch.setattr(module.subprocess, "run", _fail_selected)
    report = module.build_report(repo)

    assert failed_calls == 3
    assert report["status"] == "error"
    assert report["triggered"] is False
    assert report["finding"] is None
    assert report["reason"] == "git-query-error"
    assert len(report["git_query_errors"]) == 1
    assert report["recommended_bump"] is None
    assert report["recommended_version"] is None


def test_no_baseline_tag_is_still_a_quiet_pass(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)  # commits but no tag: deterministic non-zero from describe
    module = _load_module()
    report = module.build_report(repo)

    assert report["status"] == "pass"
    assert report["reason"] == "no-baseline-tag"
    assert "git_query_errors" not in report


def test_expected_no_tag_result_is_not_retried(tmp_path: Path, monkeypatch) -> None:
    module = _load_module()
    calls: list[list[str]] = []

    def _no_tags(cmd, **kwargs):
        calls.append(list(cmd))
        return subprocess.CompletedProcess(
            cmd,
            returncode=128,
            stdout="",
            stderr="fatal: No names found, cannot describe anything.",
        )

    monkeypatch.setattr(module.subprocess, "run", _no_tags)
    report = module.build_report(tmp_path)

    assert len(calls) == 1
    assert report["status"] == "pass"
    assert report["reason"] == "no-baseline-tag"
    assert "git_query_errors" not in report


@pytest.mark.parametrize(
    ("stderr",),
    [
        ("fatal: No names found, cannot describe anything.",),
        (
            "fatal: No tags can describe 'abc123'.\n"
            "Try --always, or create some tags.",
        ),
        (
            "fatal: No annotated tags can describe 'abc123'.\n"
            "However, there were unannotated tags: try --tags.",
        ),
    ],
)
def test_known_no_tag_signatures_are_quiet(
    tmp_path: Path, monkeypatch, stderr: str
) -> None:
    module = _load_module()
    calls = 0

    def _no_tags(cmd, **kwargs):
        nonlocal calls
        calls += 1
        return subprocess.CompletedProcess(cmd, returncode=128, stdout="", stderr=stderr)

    monkeypatch.setattr(module.subprocess, "run", _no_tags)
    report = module.build_report(tmp_path)

    assert calls == 1
    assert report["status"] == "pass"
    assert report["reason"] == "no-baseline-tag"
    assert "git_query_errors" not in report


@pytest.mark.parametrize(
    ("returncode", "stdout", "stderr"),
    [
        (1, "", "fatal: No names found, cannot describe anything."),
        (128, "No tags can describe placeholder", "fatal: detected dubious ownership"),
        (128, "", "fatal: No names found; permission denied"),
        (
            128,
            "",
            "fatal: No names found, cannot describe anything.\n"
            "fatal: detected dubious ownership",
        ),
    ],
)
def test_conflicting_no_tag_diagnostics_retry_and_fail_loud(
    tmp_path: Path,
    monkeypatch,
    returncode: int,
    stdout: str,
    stderr: str,
) -> None:
    module = _load_module()
    monkeypatch.setattr(module.time, "sleep", lambda _s: None)
    calls = 0

    def _unexpected(cmd, **kwargs):
        nonlocal calls
        calls += 1
        return subprocess.CompletedProcess(
            cmd, returncode=returncode, stdout=stdout, stderr=stderr
        )

    monkeypatch.setattr(module.subprocess, "run", _unexpected)
    report = module.build_report(tmp_path)

    assert calls == 3
    assert report["status"] == "error"
    assert report["triggered"] is False
    assert report["reason"] == "git-query-error"
    assert report["git_query_errors"][0]["returncode"] == returncode


def test_sensitive_diagnostics_redact_complete_values_and_bound_length() -> None:
    module = _load_module()
    diagnostic = (
        "Authorization: Bearer auth-secret\n"
        'token="two word-secret"\n'
        "password=first-secret secret=second-secret\n"
        "PASSWD: Basic passwd-secret\n"
        "access-token=access token-secret\n"
        'access_token="underscore underscore-secret"\n'
        "fetch https://user-one:pass-one@example.invalid/a "
        "and https://user-two:pass-two@example.invalid/b\n"
        + ("x" * 800)
    )

    sanitized = module._sanitize_git_diagnostic(diagnostic)

    for secret in (
        "auth-secret",
        "word-secret",
        "first-secret",
        "second-secret",
        "passwd-secret",
        "token-secret",
        "underscore-secret",
        "user-one",
        "pass-one",
        "user-two",
        "pass-two",
    ):
        assert secret not in sanitized
    assert sanitized.count("[REDACTED]") >= 8
    assert len(sanitized) <= 500


def test_mixed_retry_oserror_resets_returncode_and_sanitizes_evidence(
    tmp_path: Path, monkeypatch
) -> None:
    module = _load_module()
    monkeypatch.setattr(module.time, "sleep", lambda _s: None)
    attempts = 0

    def _mixed(cmd, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return subprocess.CompletedProcess(
                cmd, returncode=7, stdout="", stderr="temporary failure"
            )
        raise OSError(
            "authorization: Bearer os-secret "
            "https://os-user:os-password@example.invalid/repo"
        )

    monkeypatch.setattr(module.subprocess, "run", _mixed)
    module._QUERY_ERRORS.clear()
    assert (
        module._git(
            tmp_path,
            "rev-list",
            "https://command-user:command-pass@example.invalid/repo",
            "token=command-secret",
        )
        is None
    )

    assert attempts == 3
    error = module._QUERY_ERRORS[0]
    assert error["returncode"] is None
    assert "os-secret" not in error["error"]
    assert "os-user" not in error["error"]
    assert "os-password" not in error["error"]
    assert "[REDACTED]" in error["error"]
    assert len(error["error"]) <= 500
    assert "command-user" not in error["command"]
    assert "command-pass" not in error["command"]
    assert "command-secret" not in error["command"]
    assert "[REDACTED]" in error["command"]


def test_git_query_error_prints_loud_without_verbose(capsys) -> None:
    module = _load_module()
    report = {
        "thresholds": {"commits": 40, "feat": 5, "days": 14},
        "triggered": False,
        "status": "error",
        "reason": "git-query-error",
        "git_query_errors": [
            {"command": "git rev-list --count v0.1.0..HEAD", "error": "OSError: spawn failed"}
        ],
    }
    module._print_report(report, verbose=False)
    out = capsys.readouterr().out

    assert "release-cadence: ERROR git-query-error" in out
    assert "git rev-list" in out
