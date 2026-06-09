from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
SCRIPT_PATH = REPO_ROOT / "scripts" / "warning_summary_strict_ref_policy.py"


def _run(args: list[str], *, expect_zero: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [PYTHON, str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=dict(os.environ, PYTHONIOENCODING="utf-8"),
        cwd=str(REPO_ROOT),
        check=False,
    )
    if expect_zero and result.returncode != 0:
        detail = result.stdout.strip() or result.stderr.strip() or "<no output>"
        raise AssertionError(f"command failed ({args!r}) returncode={result.returncode}. output:\n{detail}")
    return result


def _normalize(value: str) -> str:
    return "\n".join(
        line.strip()
        for line in value.replace("\r", "").splitlines()
        if line.strip()
    )


def test_strict_ref_policy_script_roundtrip_with_normalized_lines(tmp_path: Path) -> None:
    artifact = tmp_path / "warning-summary-strict-ref-policy.json"

    write_result = _run(
        [
            "--mode",
            "write",
            "--artifact",
            str(artifact),
            "--github-event-name",
            "workflow_dispatch",
            "--github-ref",
            "refs/heads/main",
            "--run-id",
            "9999",
            "--job-attempt",
            "1",
            "--matrix-python-version",
            "3.11",
            "--strict-refs-source",
            "workflow_dispatch_input",
            "--strict-refs",
            "refs/heads/main\r\nrefs/heads/release/\n \nrefs/tags/\n",
            "--require-send-targets",
            "1",
        ]
    )
    assert write_result.returncode == 0

    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["github_event_name"] == "workflow_dispatch"
    assert payload["github_ref"] == "refs/heads/main"
    assert payload["run_id"] == "9999"
    assert payload["job_attempt"] == "1"
    assert payload["matrix_python_version"] == "3.11"
    assert payload["strict_refs_source"] == "workflow_dispatch_input"
    assert _normalize(payload["strict_refs"]) == _normalize("refs/heads/main\nrefs/heads/release/\nrefs/tags/")
    assert payload["require_send_targets"] == "1"

    validate_result = _run(
        [
            "--mode",
            "validate",
            "--artifact",
            str(artifact),
            "--github-event-name",
            "workflow_dispatch",
            "--github-ref",
            "refs/heads/main",
            "--run-id",
            "9999",
            "--job-attempt",
            "1",
            "--matrix-python-version",
            "3.11",
            "--strict-refs-source",
            "workflow_dispatch_input",
            "--strict-refs",
            "refs/heads/main\n  refs/heads/release/\nrefs/tags/",
            "--require-send-targets",
            "1",
        ]
    )
    assert validate_result.returncode == 0
    assert "policy artifact consistent" in validate_result.stdout


def test_strict_ref_policy_script_detects_mismatch(tmp_path: Path) -> None:
    artifact = tmp_path / "warning-summary-strict-ref-policy.json"
    _run(
        [
            "--mode",
            "write",
            "--artifact",
            str(artifact),
            "--github-event-name",
            "push",
            "--github-ref",
            "refs/heads/release",
            "--run-id",
            "100",
            "--job-attempt",
            "2",
            "--matrix-python-version",
            "3.11",
            "--strict-refs-source",
            "job_env_default",
            "--strict-refs",
            "refs/heads/main",
            "--require-send-targets",
            "0",
        ]
    )

    result = _run(
        [
            "--mode",
            "validate",
            "--artifact",
            str(artifact),
            "--github-event-name",
            "push",
            "--github-ref",
            "refs/heads/release",
            "--run-id",
            "100",
            "--job-attempt",
            "2",
            "--matrix-python-version",
            "3.11",
            "--strict-refs-source",
            "workflow_dispatch_input",
            "--strict-refs",
            "refs/heads/main",
            "--require-send-targets",
            "0",
        ],
        expect_zero=False,
    )
    assert result.returncode == 1
    assert "strict_refs_source mismatch" in result.stdout


def test_strict_ref_policy_script_fails_when_artifact_missing(tmp_path: Path) -> None:
    artifact = tmp_path / "missing.json"
    result = _run(
        [
            "--mode",
            "validate",
            "--artifact",
            str(artifact),
            "--github-event-name",
            "push",
            "--github-ref",
            "refs/heads/main",
            "--run-id",
            "1",
            "--job-attempt",
            "1",
            "--matrix-python-version",
            "3.11",
            "--strict-refs-source",
            "job_env_default",
            "--strict-refs",
            "refs/heads/main",
            "--require-send-targets",
            "0",
        ],
        expect_zero=False,
    )
    assert result.returncode == 1
    assert "policy artifact missing" in (result.stdout + result.stderr)


def test_strict_ref_policy_script_uses_environment_fallbacks(tmp_path: Path) -> None:
    artifact = tmp_path / "warning-summary-strict-ref-policy.json"
    env = dict(
        os.environ,
        GITHUB_EVENT_NAME="workflow_call",
        GITHUB_REF="refs/heads/main",
        GITHUB_RUN_ID="7777",
        GITHUB_RUN_ATTEMPT="3",
        MATRIX_PYTHON_VERSION="3.12",
        STRICT_REFS_SOURCE="fallback_job_env_default",
        STRICT_REFS="refs/heads/main\nrefs/heads/release/\n",
        REQUIRE_SEND_TARGETS="0",
    )

    write_result = subprocess.run(
        [
            PYTHON,
            str(SCRIPT_PATH),
            "--mode",
            "write",
            "--artifact",
            str(artifact),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        cwd=str(REPO_ROOT),
        check=False,
    )
    assert write_result.returncode == 0

    validate_result = subprocess.run(
        [
            PYTHON,
            str(SCRIPT_PATH),
            "--mode",
            "validate",
            "--artifact",
            str(artifact),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        cwd=str(REPO_ROOT),
        check=False,
    )
    assert validate_result.returncode == 0
    assert "policy artifact consistent" in validate_result.stdout
