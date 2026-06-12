from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "work_schema_gate.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_repo_work_schema_passes_gate() -> None:
    result = _run("--check")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "work-schema-gate: pass" in result.stdout


def test_gate_blocks_missing_required_catalog_field(tmp_path: Path) -> None:
    source = REPO_ROOT / "agents" / "project" / "WORK-SCHEMA.yml"
    text = source.read_text(encoding="utf-8")
    broken = text.replace("  work_uid:\n", "  removed_work_uid:\n", 1)
    path = tmp_path / "WORK-SCHEMA.yml"
    path.write_text(broken, encoding="utf-8")

    result = _run("--path", str(path), "--check")

    assert result.returncode == 1
    assert "work-schema:missing-field-catalog:work_uid" in result.stdout


def test_gate_blocks_stored_derived_fields(tmp_path: Path) -> None:
    source = REPO_ROOT / "agents" / "project" / "WORK-SCHEMA.yml"
    text = source.read_text(encoding="utf-8")
    broken = text.replace("storage_policy: computed_only", "storage_policy: stored", 1)
    path = tmp_path / "WORK-SCHEMA.yml"
    path.write_text(broken, encoding="utf-8")

    result = _run("--path", str(path), "--check")

    assert result.returncode == 1
    assert "work-schema:computed-field-stored:progress_pct" in result.stdout
