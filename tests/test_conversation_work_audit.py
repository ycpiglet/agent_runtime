from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "conversation_work_audit.py"
SPEC = importlib.util.spec_from_file_location("conversation_work_audit", SCRIPT)
assert SPEC is not None
conversation_work_audit = importlib.util.module_from_spec(SPEC)
sys.modules["conversation_work_audit"] = conversation_work_audit
assert SPEC.loader is not None
SPEC.loader.exec_module(conversation_work_audit)


POINTER_TEMPLATE = """schema: agent-runtime-next-session-pointer/v1
updated_at: 2026-06-13T00:00:00+09:00
current_state:
  task_set_id: "{taskset_id}"
resume:
  active_task: {task_id}
  active_task_set: {taskset_id}
pointers:
  completed_tasks:
    - agents/lead_engineer/tasks/{task_id}.md
"""


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _record(body: str, *, tags: str = "[planning-record, backlog]") -> str:
    return (
        "---\n"
        "type: meeting\n"
        "id: MEETING-2026-06-13-fixture\n"
        "audience: owner\n"
        f"tags: {tags}\n"
        "---\n\n"
        "# Fixture Planning Meeting\n\n" + body
    )


def _fixture_repo(tmp_path: Path, record_body: str, *, with_task: bool = True) -> Path:
    root = tmp_path / "repo"
    _write(root / "reviews" / "MEETING-2026-06-13-fixture.md", _record(record_body))
    if with_task:
        _write(
            root / "agents" / "lead_engineer" / "tasks" / "TASK-AR-900.md",
            "---\nid: TASK-AR-900\nstatus: planned\n---\n\n# Fixture Task\n",
        )
    _write(
        root / "BACKLOG-BOARD.md",
        "# Backlog Decision Board\n\n### Fixture (`TASKSET-AR-FIXTURE`)\n\n| `TASK-AR-900` |\n",
    )
    _write(
        root / "agents" / "project" / "NEXT-SESSION-POINTER.yml",
        POINTER_TEMPLATE.format(task_id="TASK-AR-900", taskset_id="TASKSET-AR-FIXTURE"),
    )
    return root


def test_planning_record_with_action_items_but_no_work_links_is_watch(tmp_path: Path) -> None:
    body = (
        "## Action Board\n\n"
        "| Status | Action | Owner |\n"
        "| --- | --- | --- |\n"
        "| Next | Build the follow-up gate | lead-engineer |\n"
    )
    root = _fixture_repo(tmp_path, body)

    _, findings = conversation_work_audit.analyze(root)

    watch = [f for f in findings if f.kind == "unmapped-planning-record"]
    assert len(watch) == 1
    assert watch[0].severity == "watch"
    assert watch[0].path == "reviews/MEETING-2026-06-13-fixture.md"
    assert not any(f.severity == "block" for f in findings)
    # watch findings report but do not fail --check
    assert conversation_work_audit.main(["--root", str(root), "--check"]) == 0


def test_planning_record_with_review_task_board_and_pointer_links_passes(tmp_path: Path) -> None:
    body = (
        "## Action Board\n\n"
        "| Status | Action | Evidence |\n"
        "| --- | --- | --- |\n"
        "| Next | Implement the fixture follow-up | `TASK-AR-900` |\n\n"
        "## Proposed Follow-Up Registration\n\n"
        "| Proposed Task | Scope |\n"
        "| --- | --- |\n"
        "| `TASK-AR-900` | fixture scope under `TASKSET-AR-FIXTURE` |\n\n"
        "Review: reviews/MEETING-2026-06-13-fixture.md\n"
    )
    root = _fixture_repo(tmp_path, body)

    records, findings = conversation_work_audit.analyze(root)

    assert len(records) == 1
    assert findings == []
    assert conversation_work_audit.main(["--root", str(root), "--check"]) == 0


@pytest.mark.parametrize(
    "task_id",
    [
        "TASK-AR-20260721-221825-f53b6746",
        "TASK-AR-20260721-221825-F53B6746",
    ],
)
def test_planning_record_accepts_timestamp_task_id_suffix_case(
    tmp_path: Path, task_id: str
) -> None:
    body = (
        "## Proposed Follow-Up Registration\n\n"
        "| Proposed Task | Scope |\n"
        "| --- | --- |\n"
        f"| `{task_id}` | allocator-to-audit contract |\n"
    )
    root = _fixture_repo(tmp_path, body, with_task=False)
    _write(
        root / "agents" / "lead_engineer" / "tasks" / f"{task_id}.md",
        f"---\nid: {task_id}\nstatus: planned\n---\n\n# Timestamp task\n",
    )

    _, findings = conversation_work_audit.analyze(root)

    assert not any(
        finding.kind in {"unmapped-planning-record", "missing-task-file"}
        for finding in findings
    )


def test_task_id_extractor_does_not_match_inside_larger_tokens() -> None:
    text = "prefix_TASK-AR-901 suffixTASK-AR-902 TASK-AR-903_suffix"

    assert conversation_work_audit.TASK_ID_RE.findall(text) == []


def test_planning_record_referencing_missing_task_file_is_block(tmp_path: Path) -> None:
    body = (
        "## Proposed Follow-Up Registration\n\n"
        "| Proposed Task | Scope |\n"
        "| --- | --- |\n"
        "| `TASK-AR-901` | scope that was never registered |\n"
    )
    root = _fixture_repo(tmp_path, body)

    _, findings = conversation_work_audit.analyze(root)

    blocks = [f for f in findings if f.severity == "block"]
    assert len(blocks) == 1
    assert blocks[0].kind == "missing-task-file"
    assert "TASK-AR-901" in blocks[0].detail
    assert blocks[0].path == "reviews/MEETING-2026-06-13-fixture.md"
    assert conversation_work_audit.main(["--root", str(root), "--check"]) == 1


def test_taskset_missing_from_board_and_pointer_drift_are_watch(tmp_path: Path) -> None:
    body = (
        "## Action Board\n\n"
        "| Status | Action | Evidence |\n"
        "| --- | --- | --- |\n"
        "| Next | Start the unregistered set | `TASKSET-AR-UNREGISTERED` |\n"
    )
    root = _fixture_repo(tmp_path, body)
    _write(
        root / "agents" / "project" / "NEXT-SESSION-POINTER.yml",
        POINTER_TEMPLATE.format(task_id="TASK-AR-902", taskset_id="TASKSET-AR-NOT-ON-BOARD"),
    )

    _, findings = conversation_work_audit.analyze(root)

    kinds = {f.kind for f in findings}
    assert "board-taskset-missing" in kinds
    assert "pointer-task-missing" in kinds
    assert "pointer-board-mismatch" in kinds
    assert "pointer-task-file-missing" in kinds
    assert all(f.severity == "watch" for f in findings)
    assert conversation_work_audit.main(["--root", str(root), "--check"]) == 0


def _write_active_pointer(root: Path, task_id: str, task_file: str) -> None:
    _write(
        root / "agents" / "project" / "NEXT-SESSION-POINTER.yml",
        POINTER_TEMPLATE.format(task_id=task_id, taskset_id="TASKSET-AR-FIXTURE").replace(
            f"agents/lead_engineer/tasks/{task_id}.md", task_file
        ),
    )


def test_pointer_resolves_slugged_canonical_task_filename(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path, "## Notes\n\nNo follow-up.\n")
    slugged = "agents/lead_engineer/tasks/TASK-231-taskset-dispatcher-selection-order.md"
    _write(
        root / slugged,
        "---\nwork_id: TASK-231\nid: TASK-231\nkind: task\nstatus: planned\n---\n",
    )
    _write_active_pointer(root, "TASK-231", slugged)

    _, findings = conversation_work_audit.analyze(root)

    assert not any(f.kind in {"pointer-task-missing", "pointer-task-ambiguous"} for f in findings)


def test_pointer_resolves_task_by_frontmatter_id_without_filename_prefix(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path, "## Notes\n\nNo follow-up.\n")
    canonical = "agents/lead_engineer/tasks/descriptive-canonical-task.md"
    _write(root / canonical, "---\nwork_id: TASK-231\nkind: task\nstatus: planned\n---\n")
    _write_active_pointer(root, "TASK-231", canonical)

    _, findings = conversation_work_audit.analyze(root)

    assert not any(f.kind in {"pointer-task-missing", "pointer-task-ambiguous"} for f in findings)


def test_pointer_does_not_match_longer_task_id_prefix(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path, "## Notes\n\nNo follow-up.\n")
    longer = "agents/lead_engineer/tasks/TASK-2310.md"
    _write(root / longer, "---\nwork_id: TASK-2310\nkind: task\nstatus: planned\n---\n")
    _write_active_pointer(root, "TASK-231", longer)

    _, findings = conversation_work_audit.analyze(root)

    assert any(f.kind == "pointer-task-missing" for f in findings)


def test_pointer_reports_ambiguous_canonical_task_records(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path, "## Notes\n\nNo follow-up.\n")
    first = "agents/lead_engineer/tasks/TASK-231-first.md"
    second = "agents/lead_engineer/tasks/TASK-231-second.md"
    _write(root / first, "---\nwork_id: TASK-231\nkind: task\nstatus: planned\n---\n")
    _write(root / second, "---\nwork_id: TASK-231\nkind: task\nstatus: planned\n---\n")
    _write_active_pointer(root, "TASK-231", first)

    _, findings = conversation_work_audit.analyze(root)

    ambiguous = [f for f in findings if f.kind == "pointer-task-ambiguous"]
    assert len(ambiguous) == 1
    assert first in ambiguous[0].detail
    assert second in ambiguous[0].detail
    assert not any(f.kind == "pointer-task-missing" for f in findings)


def test_non_planning_reviews_are_ignored(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path, "## Notes\n\nNothing actionable.\n")
    _write(
        root / "reviews" / "REVIEW-2026-06-13-ordinary.md",
        "---\ntype: review\nid: REVIEW-2026-06-13-ordinary\n---\n\n"
        "## Proposed Follow-Up\n\n| Task | Scope |\n| --- | --- |\n| `TASK-AR-999` | not audited |\n",
    )

    records, findings = conversation_work_audit.analyze(root)

    assert [record.name for record in records] == ["MEETING-2026-06-13-fixture.md"]
    assert not any(f.severity == "block" for f in findings)


def test_owner_governance_runs_conversation_work_audit() -> None:
    root_gate = (REPO_ROOT / "scripts" / "owner_governance_gate.py").read_text(encoding="utf-8")
    template_gate = (
        REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "owner_governance_gate.py"
    ).read_text(encoding="utf-8")

    assert '"scripts/conversation_work_audit.py", "--check"' in root_gate
    assert '"scripts/conversation_work_audit.py", "--check"' in template_gate


def test_template_script_mirror_matches_root_script() -> None:
    root_script = SCRIPT.read_text(encoding="utf-8")
    template_script = (
        REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "conversation_work_audit.py"
    ).read_text(encoding="utf-8")

    assert root_script == template_script
