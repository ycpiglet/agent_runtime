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


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _schema_path() -> Path:
    return REPO_ROOT / "agents" / "project" / "WORK-SCHEMA.yml"


def _minimal_task_frontmatter(*, extra: str = "", omit: str = "") -> str:
    rows = {
        "schema_version": "agent-runtime-work-item/v1",
        "work_id": "TASK-TEST-001",
        "work_uid": "11111111-1111-4111-8111-111111111111",
        "kind": "task",
        "parent_id": "TASKSET-TEST",
        "status": "planned",
        "owner": "lead_engineer",
        "created_at": "2026-06-12T00:00:00+09:00",
        "updated_at": "2026-06-12T00:00:00+09:00",
        "origin_type": "owner_request",
        "origin_ref": "reviews/TEST.md",
        "created_by": "codex",
    }
    rows.pop(omit, None)
    body = "\n".join(f"{key}: {value}" for key, value in rows.items())
    if extra:
        body = body + "\n" + extra.strip()
    return f"---\n{body}\n---\n\n# Test\n"


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


def test_gate_blocks_work_item_missing_required_field(tmp_path: Path) -> None:
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-TEST-001.md",
        _minimal_task_frontmatter(omit="origin_ref"),
    )

    result = _run("--root", str(tmp_path), "--path", str(_schema_path()), "--items", "--check")

    assert result.returncode == 1
    assert "work-item:missing-required:origin_ref" in result.stdout


def test_gate_blocks_work_item_stored_computed_field(tmp_path: Path) -> None:
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-TEST-001.md",
        _minimal_task_frontmatter(extra="progress_pct: 50"),
    )

    result = _run("--root", str(tmp_path), "--path", str(_schema_path()), "--items", "--check")

    assert result.returncode == 1
    assert "work-item:computed-field-stored:progress_pct" in result.stdout


def test_gate_reports_unknown_work_item_field_as_watch(tmp_path: Path) -> None:
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-TEST-001.md",
        _minimal_task_frontmatter(extra="unregistered_custom_field: keep-visible"),
    )

    result = _run("--root", str(tmp_path), "--path", str(_schema_path()), "--items", "--check")

    assert result.returncode == 0
    assert "work-schema-gate: watch" in result.stdout
    assert "warnings=1" in result.stdout
    assert "agents/lead_engineer/tasks/TASK-TEST-001.md: work-item:unknown-field:unregistered_custom_field" in result.stdout


def test_owner_governance_runs_work_schema_item_gate_in_root_and_template() -> None:
    root_gate = (REPO_ROOT / "scripts" / "owner_governance_gate.py").read_text(encoding="utf-8")
    template_gate = (
        REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "owner_governance_gate.py"
    ).read_text(encoding="utf-8")

    assert '"scripts/work_schema_gate.py", "--items", "--check"' in root_gate
    assert '"scripts/work_schema_gate.py", "--items", "--check"' in template_gate


def test_template_carries_work_schema_gate_and_catalog() -> None:
    assert (REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "work_schema_gate.py").exists()
    assert (
        REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "agents" / "project" / "WORK-SCHEMA.yml"
    ).exists()
