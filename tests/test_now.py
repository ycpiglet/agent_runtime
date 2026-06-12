from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
NOW = REPO_ROOT / "scripts" / "now.py"
WORK = REPO_ROOT / "scripts" / "work.py"

LOCAL_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EPOCH_RE = re.compile(r"^\d{10,}$")


def _run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_now_script_outputs_canonical_timestamp_formats() -> None:
    cases = [
        ((), LOCAL_RE),
        (("--utc",), UTC_RE),
        (("--date",), DATE_RE),
        (("--epoch",), EPOCH_RE),
    ]
    for args, pattern in cases:
        result = _run(NOW, *args)
        assert result.returncode == 0, result.stderr or result.stdout
        assert pattern.match(result.stdout.strip())


def test_work_now_uses_canonical_timestamp_formats() -> None:
    cases = [
        (("now",), LOCAL_RE),
        (("now", "--utc"), UTC_RE),
        (("now", "--date"), DATE_RE),
        (("now", "--epoch"), EPOCH_RE),
    ]
    for args, pattern in cases:
        result = _run(WORK, *args)
        assert result.returncode == 0, result.stderr or result.stdout
        assert pattern.match(result.stdout.strip())


def test_work_help_lists_now_command() -> None:
    result = _run(WORK, "--help")

    assert result.returncode == 0, result.stderr or result.stdout
    assert "now" in result.stdout
