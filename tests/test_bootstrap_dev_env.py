import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "bootstrap_dev_env.py"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import bootstrap_dev_env as bootstrap  # noqa: E402


def _run(*extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *extra],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_check_is_watch_only_and_reports_every_item() -> None:
    result = _run("--check")
    assert result.returncode == 0, result.stderr
    for item in ("python:", "editable install:", "hooksPath:", "Codex hooks:", "push transport:", "gh:"):
        assert item in result.stdout, f"missing report line for {item}\n{result.stdout}"


def test_apply_never_blocks() -> None:
    # --apply may fix hooksPath but must still exit 0 regardless of state.
    result = _run("--apply")
    assert result.returncode == 0, result.stderr


def test_apply_repairs_non_executable_pre_commit(monkeypatch) -> None:
    state = {"executable": False}

    def fake_run(*args: str, timeout: int = 30) -> tuple[int, str]:
        if args == ("git", "config", "core.hooksPath"):
            return 0, ".githooks"
        raise AssertionError(args)

    def repair(_root: Path) -> bool:
        state["executable"] = True
        return True

    monkeypatch.setattr(bootstrap, "_run", fake_run)
    monkeypatch.setattr(
        bootstrap,
        "is_pre_commit_executable",
        lambda _root: state["executable"],
    )
    monkeypatch.setattr(bootstrap, "repair_pre_commit_executable", repair)

    result = bootstrap.check_hooks_path(apply=True)

    assert result.startswith("ok   hooksPath:")
    assert "pre-commit activation ready" in result


def test_check_reports_non_executable_pre_commit(monkeypatch) -> None:
    monkeypatch.setattr(
        bootstrap,
        "_run",
        lambda *args, **_kwargs: (0, ".githooks")
        if args == ("git", "config", "core.hooksPath")
        else (_ for _ in ()).throw(AssertionError(args)),
    )
    monkeypatch.setattr(bootstrap, "is_pre_commit_executable", lambda _root: False)

    result = bootstrap.check_hooks_path(apply=False)

    assert result.startswith("FIX  hooksPath:")
    assert "pre-commit is not executable" in result


def test_apply_reports_fix_when_chmod_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        bootstrap,
        "_run",
        lambda *args, **_kwargs: (0, ".githooks")
        if args == ("git", "config", "core.hooksPath")
        else (_ for _ in ()).throw(AssertionError(args)),
    )
    monkeypatch.setattr(bootstrap, "is_pre_commit_executable", lambda _root: False)
    monkeypatch.setattr(
        bootstrap,
        "repair_pre_commit_executable",
        lambda _root: (_ for _ in ()).throw(PermissionError("denied")),
    )

    result = bootstrap.check_hooks_path(apply=True)

    assert result.startswith("FIX  hooksPath:")
    assert "pre-commit is not executable" in result


def test_output_is_ascii_only() -> None:
    # Onboarding runs on fresh consoles (cp949 on Windows); keep output ASCII.
    result = _run("--check")
    result.stdout.encode("ascii")


def test_one_shot_wrappers_delegate_to_bootstrap() -> None:
    # setup.ps1 / setup.sh are the clone-and-run entry points; both must exist
    # and delegate to the bootstrap script with --apply.
    for name in ("setup.ps1", "setup.sh"):
        wrapper = (REPO_ROOT / name).read_text(encoding="utf-8")
        assert "scripts/bootstrap_dev_env.py" in wrapper, name
        assert "--apply" in wrapper, name
