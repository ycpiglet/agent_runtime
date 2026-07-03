from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


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
