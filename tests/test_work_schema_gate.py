from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from scripts import work_schema_gate as schema_gate


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


def _template_schema_path() -> Path:
    return (
        REPO_ROOT
        / "src"
        / "agent_runtime"
        / "templates"
        / "project"
        / "agents"
        / "project"
        / "WORK-SCHEMA.yml"
    )


def _load_template_gate():
    path = (
        REPO_ROOT
        / "src"
        / "agent_runtime"
        / "templates"
        / "project"
        / "scripts"
        / "work_schema_gate.py"
    )
    spec = importlib.util.spec_from_file_location("template_work_schema_gate", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _catalog_field(path: Path, field: str) -> dict[str, str | list[str]]:
    text = path.read_text(encoding="utf-8")
    fields = schema_gate._named_blocks(schema_gate._mapping_block(text, "fields"))  # noqa: SLF001
    metadata: dict[str, str | list[str]] = {}
    for line in fields[field].splitlines():
        stripped = line.strip()
        if not stripped or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        metadata[key] = schema_gate._clean_scalar(value)  # noqa: SLF001
    return metadata


def _minimal_task_frontmatter(*, extra: str = "", omit: str = "", **overrides: str) -> str:
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
    rows.update(overrides)
    rows.pop(omit, None)
    body = "\n".join(f"{key}: {value}" for key, value in rows.items())
    if extra:
        body = body + "\n" + extra.strip()
    return f"---\n{body}\n---\n\n# Test\n"


def _closed_task_frontmatter(*, extra: str = "", **overrides: str) -> str:
    closed = {
        "status": "completed",
        "resolution": "done",
        "completed_at": "2026-06-13T00:00:00+09:00",
        "verification_status": "passed",
    }
    closed.update(overrides)
    return _minimal_task_frontmatter(extra=extra, **closed)


def test_repo_work_schema_passes_gate() -> None:
    result = _run("--check")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "work-schema-gate: pass" in result.stdout


def test_root_and_template_frontmatter_decode_work_emitter_marker():
    template_gate = _load_template_gate()

    def encoded(value: str) -> str:
        return json.dumps("\x1eagent-runtime-work-scalar-v1:" + value, ensure_ascii=True)

    summary = 'Schema #1 "quoted"'
    target = "src/#generated.py"
    text = (
        "---\n"
        f"summary: {encoded(summary)}\n"
        "target_files:\n"
        f"  - {encoded(target)}\n"
        "---\n"
    )

    for parser in (schema_gate._frontmatter, template_gate._frontmatter):  # noqa: SLF001
        meta = parser(text)
        assert meta["summary"] == summary
        assert meta["target_files"] == [target]


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


def test_repo_schema_catalogs_new_provenance_closure_and_governance_fields() -> None:
    text = _schema_path().read_text(encoding="utf-8")

    for field in (
        "merged_into",
        "superseded_by",
        "reopened_count",
        "split_from",
        "supersedes",
        "duplicate_of",
        "blocks",
        "blocked_by",
        "stakeholders",
        "watchers",
        "due_date",
        "blocked_since",
        "xp_value",
        "measurement_unavailable_reason",
        "recovered_without_claim",
        "recovery_reason",
        "recovered_at",
        "recovered_by",
        "recovery_independent_evidence_refs",
    ):
        assert f"\n  {field}:\n" in text, f"catalog missing field: {field}"
    assert "field_promotion_policy:" in text
    assert "default_entry: optional" in text
    assert "promote_to_required_when: consuming_tool_exists" in text


def test_gate_blocks_missing_new_catalog_field(tmp_path: Path) -> None:
    text = _schema_path().read_text(encoding="utf-8")
    broken = text.replace("  merged_into:\n", "  renamed_merged_into:\n", 1)
    path = tmp_path / "WORK-SCHEMA.yml"
    path.write_text(broken, encoding="utf-8")

    result = _run("--path", str(path), "--check")

    assert result.returncode == 1
    assert "work-schema:missing-field-catalog:merged_into" in result.stdout


def test_gate_blocks_missing_recovery_catalog_field(tmp_path: Path) -> None:
    text = _schema_path().read_text(encoding="utf-8")
    broken = text.replace("  recovery_reason:\n", "  renamed_recovery_reason:\n", 1)
    path = tmp_path / "WORK-SCHEMA.yml"
    path.write_text(broken, encoding="utf-8")

    result = _run("--path", str(path), "--check")

    assert result.returncode == 1
    assert "work-schema:missing-field-catalog:recovery_reason" in result.stdout


def test_gate_blocks_incomplete_recovered_without_claim_record(tmp_path: Path) -> None:
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-TEST-001.md",
        _minimal_task_frontmatter(extra="recovered_without_claim: true"),
    )

    result = _run("--root", str(tmp_path), "--path", str(_schema_path()), "--items", "--check")

    assert result.returncode == 1
    assert "work-item:recovery-missing-required:recovery_reason" in result.stdout


def test_gate_blocks_missing_promotion_policy(tmp_path: Path) -> None:
    text = _schema_path().read_text(encoding="utf-8")
    broken = text.replace("field_promotion_policy:\n", "renamed_promotion_policy:\n", 1)
    path = tmp_path / "WORK-SCHEMA.yml"
    path.write_text(broken, encoding="utf-8")

    result = _run("--path", str(path), "--check")

    assert result.returncode == 1
    assert "work-schema:missing-promotion-policy" in result.stdout


def test_gate_blocks_non_optional_promotion_default(tmp_path: Path) -> None:
    text = _schema_path().read_text(encoding="utf-8")
    broken = text.replace("  default_entry: optional\n", "  default_entry: required\n", 1)
    path = tmp_path / "WORK-SCHEMA.yml"
    path.write_text(broken, encoding="utf-8")

    result = _run("--path", str(path), "--check")

    assert result.returncode == 1
    assert "work-schema:promotion-policy-default-not-optional" in result.stdout


def test_gate_blocks_field_missing_source_metadata(tmp_path: Path) -> None:
    text = _schema_path().read_text(encoding="utf-8")
    broken = text.replace("    source: generator\n", "", 1)
    path = tmp_path / "WORK-SCHEMA.yml"
    path.write_text(broken, encoding="utf-8")

    result = _run("--path", str(path), "--check")

    assert result.returncode == 1
    assert "work-schema:field-missing-metadata:schema_version:source" in result.stdout


def test_gate_blocks_invalid_field_source_value(tmp_path: Path) -> None:
    text = _schema_path().read_text(encoding="utf-8")
    broken = text.replace("    source: generator\n", "    source: martian\n", 1)
    path = tmp_path / "WORK-SCHEMA.yml"
    path.write_text(broken, encoding="utf-8")

    result = _run("--path", str(path), "--check")

    assert result.returncode == 1
    assert "work-schema:field-invalid-source:schema_version:martian" in result.stdout


def test_gate_blocks_enum_without_allowed_values(tmp_path: Path) -> None:
    text = _schema_path().read_text(encoding="utf-8")
    broken = text.replace(
        "    allowed_values: [done, wontfix, duplicate, superseded, moved_to_vault]\n", "", 1
    )
    path = tmp_path / "WORK-SCHEMA.yml"
    path.write_text(broken, encoding="utf-8")

    result = _run("--path", str(path), "--check")

    assert result.returncode == 1
    assert "work-schema:enum-missing-allowed-values:resolution" in result.stdout


def test_gate_accepts_closed_item_with_optional_catalog_fields(tmp_path: Path) -> None:
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-TEST-001.md",
        _closed_task_frontmatter(
            extra=(
                "merged_into: TASK-TEST-002\n"
                "superseded_by: TASK-TEST-003\n"
                "reopened_count: 1\n"
                "risk_tier: low\n"
                "due_date: 2026-06-30"
            ),
        ),
    )

    result = _run("--root", str(tmp_path), "--path", str(_schema_path()), "--items", "--check")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "work-schema-gate: pass" in result.stdout


def test_gate_blocks_invalid_resolution_value(tmp_path: Path) -> None:
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-TEST-001.md",
        _closed_task_frontmatter(resolution="abandoned"),
    )

    result = _run("--root", str(tmp_path), "--path", str(_schema_path()), "--items", "--check")

    assert result.returncode == 1
    assert "work-item:invalid-resolution:abandoned" in result.stdout


def test_gate_blocks_non_integer_reopened_count(tmp_path: Path) -> None:
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-TEST-001.md",
        _minimal_task_frontmatter(extra="reopened_count: many"),
    )

    result = _run("--root", str(tmp_path), "--path", str(_schema_path()), "--items", "--check")

    assert result.returncode == 1
    assert "work-item:invalid-counter:reopened_count:many" in result.stdout


def test_gate_blocks_stored_variance_derived_field(tmp_path: Path) -> None:
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-TEST-001.md",
        _minimal_task_frontmatter(extra="variance: 0.5"),
    )

    result = _run("--root", str(tmp_path), "--path", str(_schema_path()), "--items", "--check")

    assert result.returncode == 1
    assert "work-item:computed-field-stored:variance" in result.stdout


def test_verification_status_enum_includes_generator_default_pending() -> None:
    # scripts/work.py _render_unit seeds new units with
    # `verification_status: pending`; the catalog must allow that initial
    # state in both schema copies (W4b AR-515 finding, TASK-AR-522).
    expected = "allowed_values: [pending, passed, failed, blocked, stale]"
    template_schema = (
        REPO_ROOT
        / "src"
        / "agent_runtime"
        / "templates"
        / "project"
        / "agents"
        / "project"
        / "WORK-SCHEMA.yml"
    )

    assert expected in _schema_path().read_text(encoding="utf-8")
    assert expected in template_schema.read_text(encoding="utf-8")


def test_template_schema_mirror_passes_gate() -> None:
    template_schema = (
        REPO_ROOT
        / "src"
        / "agent_runtime"
        / "templates"
        / "project"
        / "agents"
        / "project"
        / "WORK-SCHEMA.yml"
    )

    result = _run("--path", str(template_schema), "--check")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "work-schema-gate: pass" in result.stdout


def test_taskset_tasks_catalog_semantics_match_root_and_template() -> None:
    expected = {
        "type": "list",
        "required_for": [],
        "populated_by": "planner",
        "source": "human",
        "consumed_by": ["dispatcher", "taskset_work_gate"],
        "query_use": "Preserve the approved taskset membership and execution order.",
    }
    root = _catalog_field(_schema_path(), "tasks")
    template = _catalog_field(_template_schema_path(), "tasks")

    assert {key: root[key] for key in expected} == expected
    assert {key: template[key] for key in expected} == expected
    assert root["mutable"] == "planner_only"
    assert "mutable" not in template


def test_template_gate_mirror_matches_root_gate() -> None:
    root_gate = (REPO_ROOT / "scripts" / "work_schema_gate.py").read_text(encoding="utf-8")
    template_gate = (
        REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "work_schema_gate.py"
    ).read_text(encoding="utf-8")

    assert root_gate == template_gate


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


def test_ar626_gate_flags_nonmonotonic_timestamps(tmp_path: Path) -> None:
    # TASK-AR-626: started_at after completed_at is a contradiction the gate flags.
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-TEST-001.md",
        _minimal_task_frontmatter(
            extra="started_at: 2026-06-12T12:00:00+09:00\ncompleted_at: 2026-06-12T09:00:00+09:00"
        ),
    )
    result = _run("--root", str(tmp_path), "--path", str(_schema_path()), "--items", "--check")
    assert result.returncode == 1
    assert "work-item:timestamp-not-monotonic:started_at>completed_at" in result.stdout


def test_ar626_backfilled_marker_exempts_nonmonotonic(tmp_path: Path) -> None:
    # A record explicitly marked backfilled is isolated, not flagged.
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-TEST-001.md",
        _minimal_task_frontmatter(
            extra="started_at: 2026-06-12T12:00:00+09:00\n"
            "completed_at: 2026-06-12T09:00:00+09:00\n"
            "timestamp_quality: backfilled"
        ),
    )
    result = _run("--root", str(tmp_path), "--path", str(_schema_path()), "--items", "--check")
    assert "timestamp-not-monotonic" not in result.stdout
