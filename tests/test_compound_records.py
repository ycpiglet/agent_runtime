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
