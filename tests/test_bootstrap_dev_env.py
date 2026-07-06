import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "bootstrap_dev_env.py"


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
    for item in ("python:", "editable install:", "hooksPath:", "push transport:", "gh:"):
        assert item in result.stdout, f"missing report line for {item}\n{result.stdout}"


def test_apply_never_blocks() -> None:
    # --apply may fix hooksPath but must still exit 0 regardless of state.
    result = _run("--apply")
    assert result.returncode == 0, result.stderr


def test_output_is_ascii_only() -> None:
    # Onboarding runs on fresh consoles (cp949 on Windows); keep output ASCII.
    result = _run("--check")
    result.stdout.encode("ascii")
