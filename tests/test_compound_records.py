from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from agent_runtime import knowledge_records as records


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "compound_record.py"
TEMPLATE_SCRIPT = (
    REPO_ROOT
    / "src"
    / "agent_runtime"
    / "templates"
    / "project"
    / "scripts"
    / "compound_record.py"
)
WORK_SCRIPT = REPO_ROOT / "scripts" / "work.py"


def _create(
    root: Path,
    *,
    work_id: str = "UNIT-TASK-AR-645-001",
    signature: str = "same-day closeout accepted unrelated review",
    title: str = "Link closure evidence",
    created_at: str = "2026-07-29T04:00:00+09:00",
    prevention_refs: list[str] | None = None,
    update_index: bool = True,
) -> tuple[Path, dict]:
    return records.create_record(
        root,
        work_ids=[work_id],
        defect_signatures=[signature],
        title=title,
        summary="An unrelated same-day record approved the current closeout.",
        cause="The gate searched by date instead of work identity.",
        prevention="Validate explicit review and compound references against work IDs.",
        source_refs=["reviews/REVIEW-2026-07-29-source.md"],
        prevention_refs=prevention_refs or ["scripts/closure_gate.py"],
        verification_refs=["reviews/VERIFY-2026-07-29-unit.json"],
        recurrence_count=2,
        status="mitigated",
        created_by="test-suite",
        created_at=created_at,
        update_index=update_index,
    )


def _write_closeable_unit(root: Path) -> tuple[str, str]:
    task_id = "TASK-AR-645"
    unit_id = "UNIT-TASK-AR-645-001"
    task = root / "agents" / "lead_engineer" / "tasks" / f"{task_id}.md"
    task.parent.mkdir(parents=True, exist_ok=True)
    task.write_text(
        "---\n"
        "schema_version: agent-runtime-work-item/v1\n"
        f"id: {task_id}\n"
        f"display_id: {task_id}\n"
        f"work_id: {task_id}\n"
        "kind: task\n"
        "status: in_progress\n"
        "title: Compound closeout fixture\n"
        "priority: P1\n"
        "difficulty: M\n"
        "owner: lead_engineer\n"
        "---\n\n# Compound closeout fixture\n",
        encoding="utf-8",
    )
    evidence_ref = "reviews/VERIFY-2026-07-29-unit-task-ar-645-001.json"
    unit = (
        root
        / "agents"
        / "lead_engineer"
        / "tasks"
        / "units"
        / task_id
        / f"{unit_id}.md"
    )
    unit.parent.mkdir(parents=True, exist_ok=True)
    unit.write_text(
        "---\n"
        "schema_version: agent-runtime-work-item/v1\n"
        f"work_id: {unit_id}\n"
        "kind: unit\n"
        f"parent_id: {task_id}\n"
        f"unit_id: {unit_id}\n"
        f"task_id: {task_id}\n"
        "status: worker_ready\n"
        "verification_status: passed\n"
        "owner: lead_engineer\n"
        "evidence_refs:\n"
        f"  - {evidence_ref}\n"
        "---\n\n# Compound closeout fixture\n",
        encoding="utf-8",
    )
    evidence = root / evidence_ref
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(
        json.dumps(
            {
                "schema": "agent-runtime-work-verification/v1",
                "work_id": unit_id,
                "task_id": task_id,
                "unit_id": unit_id,
                "status": "passed",
                "signal": "pass",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return unit_id, evidence_ref


def _run_work(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(WORK_SCRIPT), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


_DUPLICATE_WATCH_FIELDS = (
    "decision",
    "status",
    "reviewed_by",
    "work_id",
)

_DUPLICATE_WATCH_CASES = [
    pytest.param(
        watch_format,
        field,
        order,
        id=f"{watch_format}-{field}-{order}",
    )
    for watch_format in ("markdown", "json")
    for field in _DUPLICATE_WATCH_FIELDS
    for order in ("invalid-then-valid", "valid-then-invalid")
]


def _duplicate_accepted_watch_document(
    *,
    watch_format: str,
    field: str,
    order: str,
    current_work_id: str,
) -> str:
    valid = {
        "status": "accepted",
        "decision": "accepted_watch",
        "reviewed_by": "qa-independent",
        "work_id": current_work_id,
    }
    invalid: dict[str, object] = {
        "status": "rejected",
        "decision": "rejected",
        "reviewed_by": None,
        "work_id": "UNIT-TASK-AR-999-001",
    }
    duplicate_values = (
        (invalid[field], valid[field])
        if order == "invalid-then-valid"
        else (valid[field], invalid[field])
    )
    pairs: list[tuple[str, object]] = []
    for key in ("status", "decision", "reviewed_by", "work_id"):
        if key == field:
            pairs.extend((key, value) for value in duplicate_values)
        else:
            pairs.append((key, valid[key]))

    if watch_format == "json":
        rows = [
            f"  {json.dumps(key)}: {json.dumps(value)}"
            for key, value in pairs
        ]
        return "{\n" + ",\n".join(rows) + "\n}\n"

    def frontmatter_scalar(value: object) -> str:
        return "null" if value is None else str(value)

    rows = [
        f"{key}: {frontmatter_scalar(value)}\n"
        for key, value in pairs
    ]
    return "---\n" + "".join(rows) + "---\n\n# Duplicate watch authority\n"


_SEMANTIC_WATCH_REVIEWER_FIELDS = (
    "reviewed_by",
    "reviewer",
    "approved_by",
    "accepted_by",
    "verified_by",
)
_SEMANTIC_WATCH_WORK_FIELDS = (
    "work_id",
    "task_id",
    "unit_id",
    "work_ids",
)
_SEMANTIC_WATCH_FIELDS = (
    "decision",
    "status",
    *_SEMANTIC_WATCH_REVIEWER_FIELDS,
    *_SEMANTIC_WATCH_WORK_FIELDS,
)
_SEMANTIC_WATCH_QUOTE_STYLES = (
    "single",
    "double",
    "escaped-double",
)
_SEMANTIC_DUPLICATE_WATCH_CASES = [
    pytest.param(
        field,
        quote_style,
        order,
        value_mode,
        id=f"{field}-{quote_style}-{order}-{value_mode}",
    )
    for field in _SEMANTIC_WATCH_FIELDS
    for quote_style in _SEMANTIC_WATCH_QUOTE_STYLES
    for order in ("quoted-then-plain", "plain-then-quoted")
    for value_mode in ("quoted-invalid", "plain-invalid")
] + [
    pytest.param(
        field,
        quote_style,
        "quoted-then-plain",
        "equal",
        id=f"{field}-{quote_style}-equal",
    )
    for field in _SEMANTIC_WATCH_FIELDS
    for quote_style in _SEMANTIC_WATCH_QUOTE_STYLES
]


def _quoted_watch_key(field: str, quote_style: str) -> str:
    if quote_style == "single":
        return f"'{field}'"
    if quote_style == "double":
        return json.dumps(field)
    return f'"\\u{ord(field[0]):04x}{field[1:]}"'


def _semantic_watch_value(
    field: str,
    *,
    current_work_id: str,
    valid: bool,
) -> object:
    if field == "decision":
        return "accepted_watch" if valid else "rejected"
    if field == "status":
        return "accepted" if valid else "rejected"
    if field in _SEMANTIC_WATCH_REVIEWER_FIELDS:
        return "qa-independent" if valid else None
    linked_id = (
        "TASK-AR-645"
        if field == "task_id"
        else current_work_id
    )
    if not valid:
        linked_id = (
            "TASK-AR-999"
            if field == "task_id"
            else "UNIT-TASK-AR-999-001"
        )
    return [linked_id] if field == "work_ids" else linked_id


def _render_watch_frontmatter(entries: list[tuple[str, object]]) -> str:
    rows: list[str] = []
    for key, value in entries:
        if isinstance(value, list):
            rows.append(f"{key}:\n")
            rows.extend(f"  - {item}\n" for item in value)
        else:
            scalar = "null" if value is None else str(value)
            rows.append(f"{key}: {scalar}\n")
    return "---\n" + "".join(rows) + "---\n\n# Semantic watch authority\n"


def _semantic_duplicate_accepted_watch_document(
    *,
    field: str,
    quote_style: str,
    order: str,
    value_mode: str,
    current_work_id: str,
) -> str:
    reviewer_field = (
        field
        if field in _SEMANTIC_WATCH_REVIEWER_FIELDS
        else "reviewed_by"
    )
    work_field = (
        field if field in _SEMANTIC_WATCH_WORK_FIELDS else "work_id"
    )
    base_fields = ("status", "decision", reviewer_field, work_field)
    if value_mode == "quoted-invalid":
        quoted_valid, plain_valid = False, True
    elif value_mode == "plain-invalid":
        quoted_valid, plain_valid = True, False
    else:
        quoted_valid = plain_valid = True
    semantic_pair = [
        (
            _quoted_watch_key(field, quote_style),
            _semantic_watch_value(
                field,
                current_work_id=current_work_id,
                valid=quoted_valid,
            ),
        ),
        (
            field,
            _semantic_watch_value(
                field,
                current_work_id=current_work_id,
                valid=plain_valid,
            ),
        ),
    ]
    if order == "plain-then-quoted":
        semantic_pair.reverse()

    entries: list[tuple[str, object]] = []
    for key in base_fields:
        if key == field:
            entries.extend(semantic_pair)
        else:
            entries.append(
                (
                    key,
                    _semantic_watch_value(
                        key,
                        current_work_id=current_work_id,
                        valid=True,
                    ),
                )
            )
    return _render_watch_frontmatter(entries)


def _quoted_accepted_watch_document(
    *,
    quote_style: str,
    current_work_id: str,
) -> str:
    return _render_watch_frontmatter(
        [
            (
                _quoted_watch_key(field, quote_style),
                _semantic_watch_value(
                    field,
                    current_work_id=current_work_id,
                    valid=True,
                ),
            )
            for field in ("status", "decision", "reviewed_by", "work_id")
        ]
    )


_SEMANTIC_SCALAR_INVALID_STYLES = (
    "nested-single-inside-double",
    "nested-double-inside-single",
    "mixed-single-double",
    "mixed-double-single",
)
_SEMANTIC_SCALAR_VALID_STYLES = (
    "single",
    "double",
    "escaped-double",
)
_INDENTED_WATCH_FRAGMENTS = (
    pytest.param(
        "  decision: rejected\n",
        id="space-indented-authority",
    ),
    pytest.param(
        "\tdecision: rejected\n",
        id="tab-indented-authority",
    ),
    pytest.param(
        "summary: accepted\n  rejected\n",
        id="malformed-continuation",
    ),
    pytest.param(
        "  - rejected\n",
        id="orphan-list-item",
    ),
)


def _valid_watch_scalar(field: str, *, current_work_id: str) -> str:
    value = _semantic_watch_value(
        field,
        current_work_id=current_work_id,
        valid=True,
    )
    if isinstance(value, list):
        return str(value[0])
    return str(value)


def _styled_watch_scalar(value: str, style: str) -> str:
    if style == "single":
        return f"'{value}'"
    if style == "double":
        return json.dumps(value)
    if style == "escaped-double":
        return f'"\\u{ord(value[0]):04x}{value[1:]}"'
    if style == "nested-single-inside-double":
        return json.dumps(f"'{value}'")
    if style == "nested-double-inside-single":
        return f"'\"{value}\"'"
    if style == "mixed-single-double":
        return f"'{value}\""
    return f"\"{value}'"


def _semantic_scalar_accepted_watch_document(
    *,
    field: str,
    style: str,
    current_work_id: str,
) -> str:
    reviewer_field = (
        field
        if field in _SEMANTIC_WATCH_REVIEWER_FIELDS
        else "reviewed_by"
    )
    work_field = (
        field if field in _SEMANTIC_WATCH_WORK_FIELDS else "work_id"
    )
    rows: list[str] = []
    for key in ("status", "decision", reviewer_field, work_field):
        if key == field:
            scalar = _styled_watch_scalar(
                _valid_watch_scalar(
                    field,
                    current_work_id=current_work_id,
                ),
                style,
            )
            if key == "work_ids":
                rows.extend((f"{key}:\n", f"  - {scalar}\n"))
            else:
                rows.append(f"{key}: {scalar}\n")
            continue
        value = _semantic_watch_value(
            key,
            current_work_id=current_work_id,
            valid=True,
        )
        if isinstance(value, list):
            rows.append(f"{key}:\n")
            rows.extend(f"  - {item}\n" for item in value)
        else:
            rows.append(f"{key}: {value}\n")
    return "---\n" + "".join(rows) + "---\n\n# Semantic scalar authority\n"


def _indented_accepted_watch_document(
    *,
    fragment: str,
    current_work_id: str,
) -> str:
    return (
        "---\n"
        f"{fragment}"
        "status: accepted\n"
        "decision: accepted_watch\n"
        "reviewed_by: qa-independent\n"
        f"work_id: {current_work_id}\n"
        "---\n\n# Indented watch authority\n"
    )


def test_signature_is_deterministic_bounded_and_rejects_unsafe_input() -> None:
    first = records.normalize_signature(" Closure   same-day evidence ")
    second = records.normalize_signature("closure same-day evidence")

    assert first == second
    assert first.startswith("defect:closure-same-day-evidence:")
    assert records.normalize_signature(first) == first

    for unsafe in ("", "/tmp/private.log", "password=hunter2"):
        with pytest.raises(records.CompoundRecordError):
            records.normalize_signature(unsafe)
    with pytest.raises(records.CompoundRecordError, match="oversized"):
        records.normalize_signature("x" * 241)


def test_create_search_and_deterministic_index_are_task_linked(tmp_path: Path) -> None:
    path, record = _create(tmp_path)
    ref = records.record_ref(tmp_path, path)

    assert ref.startswith("agents/project/knowledge/compounds/records/COMPOUND-")
    assert path.read_text(encoding="utf-8").endswith("\n")
    assert records.check_store(tmp_path) == []

    by_work = records.search_records(
        tmp_path, work_ids=["UNIT-TASK-AR-645-001"]
    )
    by_signature = records.search_records(
        tmp_path, defect_signatures=["same-day closeout accepted unrelated review"]
    )
    unrelated = records.search_records(
        tmp_path, work_ids=["UNIT-TASK-AR-999-001"]
    )
    assert [row["id"] for row in by_work] == [record["id"]]
    assert [row["id"] for row in by_signature] == [record["id"]]
    assert unrelated == []

    before = records.index_path(tmp_path).read_bytes()
    records.write_index(tmp_path)
    assert records.index_path(tmp_path).read_bytes() == before


def test_record_content_is_immutable_and_malformed_store_fails_closed(
    tmp_path: Path,
) -> None:
    path, _record = _create(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["prevention"] = "silently weaken the guard"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(records.CompoundRecordError, match="digest-mismatch"):
        records.load_records(tmp_path)
    assert records.check_store(tmp_path)[0].startswith(
        "compound:id-content-digest-mismatch:"
    )


def test_concurrent_records_use_separate_files_and_rebuild_one_complete_index(
    tmp_path: Path,
) -> None:
    def create(index: int) -> str:
        path, _ = _create(
            tmp_path,
            work_id=f"UNIT-TASK-AR-645-{index:03d}",
            signature=f"parallel defect {index}",
            title=f"Parallel lesson {index}",
            update_index=False,
        )
        return path.name

    with ThreadPoolExecutor(max_workers=8) as pool:
        names = list(pool.map(create, range(1, 17)))

    assert len(names) == len(set(names)) == 16
    assert len(list(records.records_dir(tmp_path).glob("*.json"))) == 16
    records.write_index(tmp_path)
    payload = json.loads(records.index_path(tmp_path).read_text(encoding="utf-8"))
    assert payload["record_count"] == 16
    assert len(payload["records"]) == 16
    assert records.check_store(tmp_path) == []


def test_legacy_search_is_read_only_fallback(tmp_path: Path) -> None:
    legacy = tmp_path / records.LEGACY_REL
    legacy.parent.mkdir(parents=True)
    legacy.write_text(
        "# Compound Log\n\n## COMPOUND-2026-07-28-001: Same-day closure bug\n"
        "\n### Prevention\nValidate the current task id.\n",
        encoding="utf-8",
    )
    before = legacy.read_bytes()

    matches = records.search_knowledge(
        tmp_path, keywords=["same-day closure"], include_legacy=True
    )

    assert matches and matches[0]["legacy"] is True
    assert matches[0]["path"] == records.LEGACY_REL.as_posix()
    assert legacy.read_bytes() == before
    assert not records.records_dir(tmp_path).exists()


def test_work_close_keeps_verification_review_and_compound_refs_separate(
    tmp_path: Path,
) -> None:
    unit_id, evidence_ref = _write_closeable_unit(tmp_path)
    prevention = tmp_path / "scripts" / "closure_gate.py"
    prevention.parent.mkdir(parents=True)
    prevention.write_text("raise SystemExit(0)\n", encoding="utf-8")
    review_ref = "reviews/REVIEW-2026-07-29-task-ar-645-closeout.md"
    review = tmp_path / review_ref
    review.write_text(
        "---\n"
        f"work_id: {unit_id}\n"
        "task_id: TASK-AR-645\n"
        "---\n\n# Linked review\n",
        encoding="utf-8",
    )
    record_path, _record = _create(
        tmp_path,
        work_id=unit_id,
        signature="same-day closeout accepted unrelated review",
    )
    compound_ref = records.record_ref(tmp_path, record_path)

    result = _run_work(
        tmp_path,
        "close",
        unit_id,
        "--actual-hours",
        "1",
        "--actual-tokens",
        "10",
        "--review-ref",
        review_ref,
        "--compound-ref",
        compound_ref,
        "--defect-signature",
        "same-day closeout accepted unrelated review",
        "--json",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    assert payload["evidence_refs"] == [evidence_ref]
    assert payload["review_refs"] == [review_ref]
    assert payload["compound_refs"] == [compound_ref]
    text = (
        tmp_path
        / "agents"
        / "lead_engineer"
        / "tasks"
        / "units"
        / "TASK-AR-645"
        / f"{unit_id}.md"
    ).read_text(encoding="utf-8")
    assert "- Verification evidence:" in text
    assert "- Reviews:" in text
    assert "- Compounds:" in text


def test_work_close_rejects_unrelated_review_and_compound_refs(
    tmp_path: Path,
) -> None:
    unit_id, _evidence_ref = _write_closeable_unit(tmp_path)
    review_ref = "reviews/REVIEW-2026-07-29-unrelated.md"
    review = tmp_path / review_ref
    review.write_text(
        "---\nwork_id: UNIT-TASK-AR-999-001\n---\n\n# Unrelated\n",
        encoding="utf-8",
    )
    record_path, _record = _create(
        tmp_path,
        work_id="UNIT-TASK-AR-999-001",
        signature="different unrelated defect",
    )

    result = _run_work(
        tmp_path,
        "close",
        unit_id,
        "--actual-hours",
        "1",
        "--actual-tokens",
        "10",
        "--review-ref",
        review_ref,
        "--compound-ref",
        records.record_ref(tmp_path, record_path),
        "--json",
    )

    assert result.returncode == 1
    assert "closeout:review-work-mismatch" in result.stderr
    assert "closeout:compound-work-mismatch" in result.stderr


def test_declared_defect_requires_a_current_work_compound_without_prior_match(
    tmp_path: Path,
) -> None:
    unit_id, _evidence_ref = _write_closeable_unit(tmp_path)

    result = _run_work(
        tmp_path,
        "close",
        unit_id,
        "--actual-hours",
        "1",
        "--actual-tokens",
        "10",
        "--defect-signature",
        "same recurring defect",
        "--json",
    )

    assert result.returncode == 1
    assert "closeout:repeat-defect-current-compound-required" in result.stderr


def test_parent_repeated_failure_trigger_requires_compound_for_unit(
    tmp_path: Path,
) -> None:
    unit_id, _evidence_ref = _write_closeable_unit(tmp_path)
    task = (
        tmp_path
        / "agents"
        / "lead_engineer"
        / "tasks"
        / "TASK-AR-645.md"
    )
    task.write_text(
        "---\n"
        "schema_version: agent-runtime-work-item/v1\n"
        "id: TASK-AR-645\n"
        "display_id: TASK-AR-645\n"
        "work_id: TASK-AR-645\n"
        "kind: task\n"
        "status: in_progress\n"
        "title: Compound closeout fixture\n"
        "priority: P1\n"
        "difficulty: M\n"
        "owner: lead_engineer\n"
        "escalation_triggers:\n"
        "  - repeated_failure\n"
        "---\n\n# Compound closeout fixture\n",
        encoding="utf-8",
    )

    result = _run_work(
        tmp_path,
        "close",
        unit_id,
        "--actual-hours",
        "1",
        "--actual-tokens",
        "10",
        "--json",
    )

    assert result.returncode == 1
    assert "closeout:repeat-defect-current-compound-required" in result.stderr


def test_parent_compound_ref_with_supported_prevention_satisfies_unit(
    tmp_path: Path,
) -> None:
    unit_id, _evidence_ref = _write_closeable_unit(tmp_path)
    prevention = tmp_path / "scripts" / "repeat_gate.py"
    prevention.parent.mkdir(parents=True)
    prevention.write_text("raise SystemExit(0)\n", encoding="utf-8")
    record_path, _record = _create(
        tmp_path,
        work_id="TASK-AR-645",
        signature="parent repeated failure",
        prevention_refs=["scripts/repeat_gate.py"],
    )
    compound_ref = records.record_ref(tmp_path, record_path)
    task = (
        tmp_path
        / "agents"
        / "lead_engineer"
        / "tasks"
        / "TASK-AR-645.md"
    )
    task.write_text(
        "---\n"
        "schema_version: agent-runtime-work-item/v1\n"
        "id: TASK-AR-645\n"
        "display_id: TASK-AR-645\n"
        "work_id: TASK-AR-645\n"
        "kind: task\n"
        "status: in_progress\n"
        "title: Compound closeout fixture\n"
        "priority: P1\n"
        "difficulty: M\n"
        "owner: lead_engineer\n"
        "escalation_triggers:\n"
        "  - repeated_failure\n"
        "compound_refs:\n"
        f"  - {compound_ref}\n"
        "---\n\n# Compound closeout fixture\n",
        encoding="utf-8",
    )

    result = _run_work(
        tmp_path,
        "close",
        unit_id,
        "--actual-hours",
        "1",
        "--actual-tokens",
        "10",
        "--json",
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_current_compound_with_missing_prevention_destination_is_rejected(
    tmp_path: Path,
) -> None:
    unit_id, _evidence_ref = _write_closeable_unit(tmp_path)
    record_path, _record = _create(
        tmp_path,
        work_id=unit_id,
        signature="missing prevention destination",
        prevention_refs=["tests/regressions/test_missing.py"],
    )

    result = _run_work(
        tmp_path,
        "close",
        unit_id,
        "--actual-hours",
        "1",
        "--actual-tokens",
        "10",
        "--compound-ref",
        records.record_ref(tmp_path, record_path),
        "--defect-signature",
        "missing prevention destination",
        "--json",
    )

    assert result.returncode == 1
    assert "closeout:compound:prevention-ref-missing" in result.stderr
    assert "closeout:repeat-defect-current-compound-required" in result.stderr


def test_ordinary_closeout_remains_compatible_with_linked_review_only(
    tmp_path: Path,
) -> None:
    unit_id, _evidence_ref = _write_closeable_unit(tmp_path)
    review_ref = "reviews/REVIEW-2026-07-29-ordinary-closeout.md"
    review = tmp_path / review_ref
    review.write_text(
        "---\n"
        f"work_id: {unit_id}\n"
        "task_id: TASK-AR-645\n"
        "---\n\n# Ordinary closeout review\n",
        encoding="utf-8",
    )

    result = _run_work(
        tmp_path,
        "close",
        unit_id,
        "--actual-hours",
        "1",
        "--actual-tokens",
        "10",
        "--review-ref",
        review_ref,
        "--json",
    )

    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("prevention_ref", "contents"),
    [
        ("tests/regressions/test_repeat.py", "def test_repeat():\n    assert True\n"),
        ("scripts/repeat_gate.py", "raise SystemExit(0)\n"),
        (
            "agents/lead_engineer/tasks/TASK-PREVENT-1.md",
            "---\nwork_id: TASK-PREVENT-1\n---\n\n# Prevention task\n",
        ),
        (
            "reviews/REVIEW-2026-07-29-accepted-watch.md",
            "---\n"
            "status: accepted\n"
            "decision: accepted_watch\n"
            "reviewed_by: qa-independent\n"
            "work_id: UNIT-TASK-AR-645-001\n"
            "---\n\n# Accepted watch\n",
        ),
    ],
    ids=["regression", "gate", "task-proposal", "accepted-watch"],
)
def test_prevention_destinations_accept_supported_repo_paths(
    tmp_path: Path,
    prevention_ref: str,
    contents: str,
) -> None:
    destination = tmp_path / prevention_ref
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(contents, encoding="utf-8")
    _path, record = _create(tmp_path, prevention_refs=[prevention_ref])

    assert (
        records.validate_prevention_destinations(
            tmp_path,
            record,
            current_work_ids=["UNIT-TASK-AR-645-001", "TASK-AR-645"],
        )
        == []
    )


def test_prevention_destinations_reject_missing_unsupported_and_symlink_escape(
    tmp_path: Path,
) -> None:
    _path, missing = _create(
        tmp_path,
        title="Missing prevention",
        prevention_refs=["tests/regressions/test_missing.py"],
        update_index=False,
    )
    missing_findings = records.validate_prevention_destinations(
        tmp_path,
        missing,
        current_work_ids=["UNIT-TASK-AR-645-001"],
    )
    assert any("prevention-ref-missing" in finding for finding in missing_findings)

    unsupported_ref = "docs/repeated-failure-note.md"
    unsupported_path = tmp_path / unsupported_ref
    unsupported_path.parent.mkdir(parents=True)
    unsupported_path.write_text("# Note\n", encoding="utf-8")
    _path, unsupported = _create(
        tmp_path,
        title="Unsupported prevention",
        prevention_refs=[unsupported_ref],
        update_index=False,
    )
    unsupported_findings = records.validate_prevention_destinations(
        tmp_path,
        unsupported,
        current_work_ids=["UNIT-TASK-AR-645-001"],
    )
    assert "compound:prevention-destination-unsupported" in unsupported_findings

    outside = tmp_path.parent / f"{tmp_path.name}-outside-gate.py"
    outside.write_text("raise SystemExit(0)\n", encoding="utf-8")
    link_ref = "scripts/escaped_gate.py"
    link = tmp_path / link_ref
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        link.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")
    _path, escaped = _create(
        tmp_path,
        title="Escaped prevention",
        prevention_refs=[link_ref],
        update_index=False,
    )
    escaped_findings = records.validate_prevention_destinations(
        tmp_path,
        escaped,
        current_work_ids=["UNIT-TASK-AR-645-001"],
    )
    assert any("prevention-ref-outside-root" in finding for finding in escaped_findings)


def test_accepted_watch_requires_reviewer_and_current_work_link(
    tmp_path: Path,
) -> None:
    watch_ref = "reviews/REVIEW-2026-07-29-invalid-watch.md"
    watch = tmp_path / watch_ref
    watch.parent.mkdir(parents=True)
    watch.write_text(
        "---\n"
        "status: accepted\n"
        "decision: accepted_watch\n"
        "work_id: UNIT-TASK-AR-999-001\n"
        "---\n\n# Invalid watch\n",
        encoding="utf-8",
    )
    _path, record = _create(
        tmp_path,
        title="Invalid accepted watch",
        prevention_refs=[watch_ref],
        update_index=False,
    )

    findings = records.validate_prevention_destinations(
        tmp_path,
        record,
        current_work_ids=["UNIT-TASK-AR-645-001"],
    )

    assert any("prevention-watch-reviewer-missing" in item for item in findings)
    assert any("prevention-watch-work-mismatch" in item for item in findings)
    assert "compound:prevention-destination-unsupported" in findings


@pytest.mark.parametrize(
    ("watch_metadata", "expected_finding"),
    [
        (
            "decision: accepted_watch\nreviewed_by: []\n",
            "closeout:compound:prevention-watch-reviewer-missing",
        ),
        (
            "decision: accepted_watch\nreviewed_by: null\n",
            "closeout:compound:prevention-watch-reviewer-missing",
        ),
        (
            "decision: accepted_watch\nreviewed_by: false\n",
            "closeout:compound:prevention-watch-reviewer-missing",
        ),
        (
            "decision: accepted_watch\nreviewed_by: TBD\n",
            "closeout:compound:prevention-watch-reviewer-missing",
        ),
        (
            "disposition: accepted_watch\nreviewed_by: qa-independent\n",
            "closeout:compound:prevention-destination-unsupported",
        ),
        (
            "prevention_status: accepted_watch\nreviewed_by: qa-independent\n",
            "closeout:compound:prevention-destination-unsupported",
        ),
        (
            "? decision\n"
            ": rejected\n"
            "decision: accepted_watch\n"
            "reviewed_by: qa-independent\n",
            "closeout:compound:prevention-watch-invalid",
        ),
        (
            "!!str decision: rejected\n"
            "decision: accepted_watch\n"
            "reviewed_by: qa-independent\n",
            "closeout:compound:prevention-watch-invalid",
        ),
        (
            "<<: *authority\n"
            "decision: accepted_watch\n"
            "reviewed_by: qa-independent\n",
            "closeout:compound:prevention-watch-invalid",
        ),
        (
            "\"\\x64ecision\": rejected\n"
            "decision: accepted_watch\n"
            "reviewed_by: qa-independent\n",
            "closeout:compound:prevention-watch-invalid",
        ),
        (
            "\"decision: rejected\n"
            "decision: accepted_watch\n"
            "reviewed_by: qa-independent\n",
            "closeout:compound:prevention-watch-invalid",
        ),
    ],
    ids=[
        "empty-list-reviewer",
        "null-reviewer",
        "boolean-reviewer",
        "placeholder-reviewer",
        "disposition-alias",
        "prevention-status-alias",
        "explicit-key-syntax",
        "tagged-key-syntax",
        "merge-key-syntax",
        "unsupported-key-escape",
        "unclosed-quoted-key",
    ],
)
def test_work_close_rejects_invalid_accepted_watch_metadata(
    tmp_path: Path,
    watch_metadata: str,
    expected_finding: str,
) -> None:
    unit_id, _evidence_ref = _write_closeable_unit(tmp_path)
    signature = "invalid accepted watch authority"
    watch_ref = "reviews/REVIEW-2026-07-29-invalid-watch-authority.md"
    (tmp_path / watch_ref).write_text(
        "---\n"
        "status: accepted\n"
        f"{watch_metadata}"
        f"work_id: {unit_id}\n"
        "---\n\n# Invalid accepted watch authority\n",
        encoding="utf-8",
    )
    record_path, _record = _create(
        tmp_path,
        work_id=unit_id,
        signature=signature,
        title="Reject invalid accepted watch authority",
        prevention_refs=[watch_ref],
    )

    result = _run_work(
        tmp_path,
        "close",
        unit_id,
        "--actual-hours",
        "1",
        "--actual-tokens",
        "10",
        "--compound-ref",
        records.record_ref(tmp_path, record_path),
        "--defect-signature",
        signature,
        "--json",
    )

    assert result.returncode == 1
    assert expected_finding in result.stderr
    assert "closeout:repeat-defect-current-compound-required" in result.stderr


@pytest.mark.parametrize(
    ("watch_format", "field", "order"),
    _DUPLICATE_WATCH_CASES,
)
def test_work_close_rejects_duplicate_accepted_watch_authority(
    tmp_path: Path,
    watch_format: str,
    field: str,
    order: str,
) -> None:
    unit_id, _evidence_ref = _write_closeable_unit(tmp_path)
    signature = "duplicate accepted watch authority"
    suffix = "json" if watch_format == "json" else "md"
    watch_ref = f"reviews/REVIEW-2026-07-29-duplicate-watch.{suffix}"
    watch = tmp_path / watch_ref
    watch.parent.mkdir(parents=True, exist_ok=True)
    watch.write_text(
        _duplicate_accepted_watch_document(
            watch_format=watch_format,
            field=field,
            order=order,
            current_work_id=unit_id,
        ),
        encoding="utf-8",
    )
    record_path, _record = _create(
        tmp_path,
        work_id=unit_id,
        signature=signature,
        title="Reject duplicate accepted watch authority",
        prevention_refs=[watch_ref],
    )

    result = _run_work(
        tmp_path,
        "close",
        unit_id,
        "--actual-hours",
        "1",
        "--actual-tokens",
        "10",
        "--compound-ref",
        records.record_ref(tmp_path, record_path),
        "--defect-signature",
        signature,
        "--json",
    )

    assert result.returncode == 1
    assert (
        f"closeout:compound:prevention-watch-invalid:{watch_ref}"
        in result.stderr
    )
    assert "closeout:repeat-defect-current-compound-required" in result.stderr


@pytest.mark.parametrize(
    ("field", "quote_style", "order", "value_mode"),
    _SEMANTIC_DUPLICATE_WATCH_CASES,
)
def test_work_close_rejects_semantic_duplicate_watch_authority(
    tmp_path: Path,
    field: str,
    quote_style: str,
    order: str,
    value_mode: str,
) -> None:
    unit_id, _evidence_ref = _write_closeable_unit(tmp_path)
    signature = "semantic duplicate accepted watch authority"
    watch_ref = "reviews/REVIEW-2026-07-29-semantic-duplicate-watch.md"
    watch = tmp_path / watch_ref
    watch.parent.mkdir(parents=True, exist_ok=True)
    watch.write_text(
        _semantic_duplicate_accepted_watch_document(
            field=field,
            quote_style=quote_style,
            order=order,
            value_mode=value_mode,
            current_work_id=unit_id,
        ),
        encoding="utf-8",
    )
    record_path, _record = _create(
        tmp_path,
        work_id=unit_id,
        signature=signature,
        title="Reject semantic duplicate accepted watch authority",
        prevention_refs=[watch_ref],
    )

    result = _run_work(
        tmp_path,
        "close",
        unit_id,
        "--actual-hours",
        "1",
        "--actual-tokens",
        "10",
        "--compound-ref",
        records.record_ref(tmp_path, record_path),
        "--defect-signature",
        signature,
        "--json",
    )

    assert result.returncode == 1
    assert (
        f"closeout:compound:prevention-watch-invalid:{watch_ref}"
        in result.stderr
    )
    assert "closeout:repeat-defect-current-compound-required" in result.stderr


@pytest.mark.parametrize(
    "quote_style",
    _SEMANTIC_WATCH_QUOTE_STYLES,
)
def test_work_close_accepts_single_semantic_quoted_watch_keys(
    tmp_path: Path,
    quote_style: str,
) -> None:
    unit_id, _evidence_ref = _write_closeable_unit(tmp_path)
    signature = "valid quoted accepted watch authority"
    watch_ref = "reviews/REVIEW-2026-07-29-valid-quoted-watch.md"
    watch = tmp_path / watch_ref
    watch.parent.mkdir(parents=True, exist_ok=True)
    watch.write_text(
        _quoted_accepted_watch_document(
            quote_style=quote_style,
            current_work_id=unit_id,
        ),
        encoding="utf-8",
    )
    record_path, _record = _create(
        tmp_path,
        work_id=unit_id,
        signature=signature,
        title="Accept valid quoted watch authority",
        prevention_refs=[watch_ref],
    )

    result = _run_work(
        tmp_path,
        "close",
        unit_id,
        "--actual-hours",
        "1",
        "--actual-tokens",
        "10",
        "--compound-ref",
        records.record_ref(tmp_path, record_path),
        "--defect-signature",
        signature,
        "--json",
    )

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("field", _SEMANTIC_WATCH_FIELDS)
@pytest.mark.parametrize("style", _SEMANTIC_SCALAR_INVALID_STYLES)
def test_work_close_rejects_invalid_semantic_watch_scalars(
    tmp_path: Path,
    field: str,
    style: str,
) -> None:
    unit_id, _evidence_ref = _write_closeable_unit(tmp_path)
    signature = "invalid semantic accepted watch scalar"
    watch_ref = "reviews/REVIEW-2026-07-29-invalid-semantic-scalar.md"
    watch = tmp_path / watch_ref
    watch.parent.mkdir(parents=True, exist_ok=True)
    watch.write_text(
        _semantic_scalar_accepted_watch_document(
            field=field,
            style=style,
            current_work_id=unit_id,
        ),
        encoding="utf-8",
    )
    record_path, _record = _create(
        tmp_path,
        work_id=unit_id,
        signature=signature,
        title="Reject invalid semantic watch scalar",
        prevention_refs=[watch_ref],
    )

    result = _run_work(
        tmp_path,
        "close",
        unit_id,
        "--actual-hours",
        "1",
        "--actual-tokens",
        "10",
        "--compound-ref",
        records.record_ref(tmp_path, record_path),
        "--defect-signature",
        signature,
        "--json",
    )

    assert result.returncode == 1
    if style.startswith("mixed-"):
        assert (
            f"closeout:compound:prevention-watch-invalid:{watch_ref}"
            in result.stderr
        )
    assert "closeout:repeat-defect-current-compound-required" in result.stderr


@pytest.mark.parametrize("field", _SEMANTIC_WATCH_FIELDS)
@pytest.mark.parametrize("style", _SEMANTIC_SCALAR_VALID_STYLES)
def test_work_close_accepts_valid_semantic_watch_scalars(
    tmp_path: Path,
    field: str,
    style: str,
) -> None:
    unit_id, _evidence_ref = _write_closeable_unit(tmp_path)
    signature = "valid semantic accepted watch scalar"
    watch_ref = "reviews/REVIEW-2026-07-29-valid-semantic-scalar.md"
    watch = tmp_path / watch_ref
    watch.parent.mkdir(parents=True, exist_ok=True)
    watch.write_text(
        _semantic_scalar_accepted_watch_document(
            field=field,
            style=style,
            current_work_id=unit_id,
        ),
        encoding="utf-8",
    )
    record_path, _record = _create(
        tmp_path,
        work_id=unit_id,
        signature=signature,
        title="Accept valid semantic watch scalar",
        prevention_refs=[watch_ref],
    )

    result = _run_work(
        tmp_path,
        "close",
        unit_id,
        "--actual-hours",
        "1",
        "--actual-tokens",
        "10",
        "--compound-ref",
        records.record_ref(tmp_path, record_path),
        "--defect-signature",
        signature,
        "--json",
    )

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("fragment", _INDENTED_WATCH_FRAGMENTS)
def test_work_close_rejects_unexpected_watch_indentation(
    tmp_path: Path,
    fragment: str,
) -> None:
    unit_id, _evidence_ref = _write_closeable_unit(tmp_path)
    signature = "unexpected accepted watch indentation"
    watch_ref = "reviews/REVIEW-2026-07-29-unexpected-indentation.md"
    watch = tmp_path / watch_ref
    watch.parent.mkdir(parents=True, exist_ok=True)
    watch.write_text(
        _indented_accepted_watch_document(
            fragment=fragment,
            current_work_id=unit_id,
        ),
        encoding="utf-8",
    )
    record_path, _record = _create(
        tmp_path,
        work_id=unit_id,
        signature=signature,
        title="Reject unexpected watch indentation",
        prevention_refs=[watch_ref],
    )

    result = _run_work(
        tmp_path,
        "close",
        unit_id,
        "--actual-hours",
        "1",
        "--actual-tokens",
        "10",
        "--compound-ref",
        records.record_ref(tmp_path, record_path),
        "--defect-signature",
        signature,
        "--json",
    )

    assert result.returncode == 1
    assert (
        f"closeout:compound:prevention-watch-invalid:{watch_ref}"
        in result.stderr
    )
    assert "closeout:repeat-defect-current-compound-required" in result.stderr


@pytest.mark.parametrize("script", [SCRIPT, TEMPLATE_SCRIPT])
def test_root_and_template_cli_create_check_search(script: Path, tmp_path: Path) -> None:
    command = [
        sys.executable,
        str(script),
        "--root",
        str(tmp_path),
        "create",
        "--work-id",
        "TASK-AR-645",
        "--signature",
        "claim lookup omitted",
        "--title",
        "Surface prior errors",
        "--summary",
        "A claim began without querying prior failures.",
        "--cause",
        "The dispatcher had no compound lookup.",
        "--prevention",
        "Search canonical records before claim persistence.",
        "--source-ref",
        "reviews/source.md",
        "--prevention-ref",
        "scripts/task_claim_dispatcher.py",
        "--verification-ref",
        "reviews/verify.json",
        "--created-at",
        "2026-07-29T04:10:00+09:00",
    ]
    created = subprocess.run(command, check=False, capture_output=True, text=True)
    assert created.returncode == 0, created.stdout + created.stderr

    checked = subprocess.run(
        [sys.executable, str(script), "--root", str(tmp_path), "check"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr
    searched = subprocess.run(
        [
            sys.executable,
            str(script),
            "--root",
            str(tmp_path),
            "search",
            "--signature",
            "claim lookup omitted",
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert searched.returncode == 0, searched.stdout + searched.stderr
    assert json.loads(searched.stdout)[0]["work_ids"] == ["TASK-AR-645"]
