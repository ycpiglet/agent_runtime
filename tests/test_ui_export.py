"""Tests for the import/export engine (TASK-AR-333)."""

import io
import json
import zipfile
from pathlib import Path

from agent_runtime import ui_export
from agent_runtime import ui_state


NOW = "2026-06-12T09:00:00+09:00"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _task(
    root: Path,
    task_id: str,
    *,
    title: str = "Sample task",
    status: str = "planned",
    priority: str = "P1",
    owner: str = "lead-engineer",
    order: int = 10,
    task_set_id: str = "TASKSET-AR-DEMO",
    labels: list[str] | None = None,
) -> Path:
    lines = [
        "---",
        f"id: {task_id}",
        f"title: {title}",
        f"status: {status}",
        f"owner: {owner}",
        f"priority: {priority}",
        f"order: {order}",
        f"task_set_id: {task_set_id}",
    ]
    if labels:
        lines.append("labels:")
        for label in labels:
            lines.append(f"  - {label}")
    lines += ["---", "", "## Goal", "", f"{title} description.", ""]
    # Filenames must stay filesystem-safe even when the title carries CSV/MD
    # injection payloads; the title field inside the frontmatter is what the
    # export code reads, not the filename.
    safe = "".join(ch if ch.isalnum() else "-" for ch in title).strip("-").lower() or "task"
    path = root / "agents" / "lead_engineer" / "tasks" / f"{task_id}-{safe}.md"
    _write(path, "\n".join(lines))
    return path


def _build_state(root: Path):
    return ui_state.build_state(root, now=NOW)


# --------------------------------------------------------------------------- #
# CSV-injection hardening
# --------------------------------------------------------------------------- #
def test_sanitize_csv_cell_defangs_formula_triggers():
    assert ui_export.sanitize_csv_cell("=1+1") == "'=1+1"
    assert ui_export.sanitize_csv_cell("+SUM(A1)") == "'+SUM(A1)"
    assert ui_export.sanitize_csv_cell("-2") == "'-2"
    assert ui_export.sanitize_csv_cell("@cmd") == "'@cmd"
    # Leading whitespace that some parsers strip still exposes the trigger.
    assert ui_export.sanitize_csv_cell("\t=evil") == "'\t=evil"
    # Normal values are untouched.
    assert ui_export.sanitize_csv_cell("normal title") == "normal title"
    assert ui_export.sanitize_csv_cell("P1") == "P1"
    assert ui_export.sanitize_csv_cell(None) == ""


def test_csv_export_quotes_and_defangs_dangerous_cells(tmp_path):
    _task(tmp_path, "TASK-AR-900", title="=cmd|payload", labels=["alpha", "beta"])
    csv_text = ui_export.export_board_csv(_build_state(tmp_path))
    # Header present and first column.
    assert csv_text.splitlines()[0].startswith("id,display_id,title,")
    # The dangerous title is prefixed with a single quote so it cannot execute.
    assert "'=cmd" in csv_text
    # CSV quoting protects the comma in the list separator if needed; the row
    # parses cleanly back via the stdlib reader.
    rows = list(__import__("csv").DictReader(io.StringIO(csv_text)))
    assert rows[0]["title"] == "'=cmd|payload"


# --------------------------------------------------------------------------- #
# CSV round-trip (acceptance criterion)
# --------------------------------------------------------------------------- #
def test_csv_export_then_import_round_trips_without_loss(tmp_path):
    _task(tmp_path, "TASK-AR-901", title="First task", status="in_progress", priority="P0", order=1, labels=["x", "y"])
    _task(tmp_path, "TASK-AR-902", title="Second task", status="planned", priority="P2", order=2, owner="qa")
    state = _build_state(tmp_path)

    csv_text = ui_export.export_board_csv(state)
    candidates = ui_export.parse_csv_import(csv_text)

    assert len(candidates) == 2
    by_id = {c["id"]: c for c in candidates}

    original = {t["id"]: t for t in state["tasks"]}
    for tid, candidate in by_id.items():
        src = original[tid]
        assert candidate["title"] == src["title"]
        assert candidate["status"] == src["status"]
        assert candidate["priority"] == str(src["priority"])
        assert candidate["owner"] == str(src["owner_agent"])
        assert candidate["task_set_id"] == str(src["task_set_id"])
        assert candidate["order"] == str(src["order"])
        assert candidate["labels"] == [str(label) for label in src["labels"]]
    # No spurious extra/empty candidates.
    assert sorted(by_id) == ["TASK-AR-901", "TASK-AR-902"]


def test_csv_round_trip_preview_marks_all_as_duplicates(tmp_path):
    # Re-importing an exported board against the same state should detect every
    # row as an existing duplicate (no accidental re-creation).
    _task(tmp_path, "TASK-AR-903", title="Dup task")
    state = _build_state(tmp_path)
    csv_text = ui_export.export_board_csv(state)
    candidates = ui_export.parse_csv_import(csv_text)
    preview = ui_export.build_import_preview(candidates, state)
    assert preview["counts"]["total"] == 1
    assert preview["counts"]["duplicate"] == 1
    assert preview["counts"]["new"] == 0
    assert preview["items"][0]["duplicate"] is True


# --------------------------------------------------------------------------- #
# Markdown package export
# --------------------------------------------------------------------------- #
def test_taskset_markdown_export_renders_checklist(tmp_path):
    _task(tmp_path, "TASK-AR-904", title="Open item", status="planned")
    _task(tmp_path, "TASK-AR-905", title="Done item", status="completed")
    md = ui_export.export_taskset_markdown(_build_state(tmp_path))
    assert md.startswith("# Taskset Export Package")
    assert "## " in md
    assert "- [ ] **TASK-AR-904** Open item" in md
    assert "- [x] **TASK-AR-905** Done item" in md


def test_markdown_export_escapes_pipe(tmp_path):
    _task(tmp_path, "TASK-AR-906", title="pipe | break")
    md = ui_export.export_taskset_markdown(_build_state(tmp_path))
    # The pipe is escaped so a field can't break a Markdown table or inject markup.
    assert "pipe \\| break" in md


def test_md_escape_collapses_newlines_and_escapes_pipe():
    # Unit-level coverage for the escaper (filenames can't hold newlines, but the
    # escaper must still neutralize them if a field ever carries one).
    assert ui_export._md_escape("a | b") == "a \\| b"
    assert ui_export._md_escape("line1\nline2") == "line1 line2"
    assert ui_export._md_escape("back\\slash") == "back\\\\slash"


# --------------------------------------------------------------------------- #
# JSON status snapshot export
# --------------------------------------------------------------------------- #
def test_status_snapshot_json_export(tmp_path):
    _task(tmp_path, "TASK-AR-907", status="in_progress")
    _task(tmp_path, "TASK-AR-908", status="completed")
    snapshot = json.loads(ui_export.export_status_snapshot(_build_state(tmp_path)))
    assert snapshot["resource"] == "status_snapshot"
    assert snapshot["totals"]["tasks"] == 2
    assert snapshot["status_counts"]["in_progress"] == 1
    assert snapshot["status_counts"]["completed"] == 1
    ids = {t["id"] for t in snapshot["tasks"]}
    assert ids == {"TASK-AR-907", "TASK-AR-908"}


# --------------------------------------------------------------------------- #
# Backup zip bundle structure
# --------------------------------------------------------------------------- #
def test_backup_zip_bundle_structure(tmp_path):
    _task(tmp_path, "TASK-AR-909", title="Backup me")
    blob = ui_export.export_backup_zip(_build_state(tmp_path))
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        names = archive.namelist()
        assert names == list(ui_export.BACKUP_MEMBERS)
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["kind"] == "agent-runtime-backup"
        assert manifest["members"] == list(ui_export.BACKUP_MEMBERS)
        # Bundled board.csv is the same lossless artifact as the standalone export.
        board = archive.read("board.csv").decode("utf-8")
        assert "TASK-AR-909" in board
        assert "Backup me" in board
        status = json.loads(archive.read("status.json"))
        assert status["totals"]["tasks"] == 1


def test_backup_zip_is_deterministic(tmp_path):
    _task(tmp_path, "TASK-AR-910")
    state = _build_state(tmp_path)
    first = ui_export.export_backup_zip(state)
    second = ui_export.export_backup_zip(state)
    assert first == second


# --------------------------------------------------------------------------- #
# Import preview + duplicate detection
# --------------------------------------------------------------------------- #
def test_import_preview_detects_existing_and_intra_upload_duplicates(tmp_path):
    _task(tmp_path, "TASK-AR-911", title="Existing")
    state = _build_state(tmp_path)
    csv_text = "\r\n".join(
        [
            "id,title,status,priority",
            "TASK-AR-911,Existing,planned,P1",  # existing id -> duplicate
            "TASK-AR-912,Brand new,planned,P1",  # genuinely new
            "TASK-AR-912,Repeat id,planned,P1",  # intra-upload dup id
            ",Existing,planned,P1",              # title collides with existing
            ",,planned,P1",                       # invalid (no title)
        ]
    )
    candidates = ui_export.parse_csv_import(csv_text)
    preview = ui_export.build_import_preview(candidates, state)
    counts = preview["counts"]
    assert counts["total"] == 5
    assert counts["new"] == 1
    assert counts["invalid"] == 1
    assert counts["duplicate"] == 3
    actions = [item["action"] for item in preview["items"]]
    assert actions.count("create") == 1


def test_markdown_checklist_import_parses_candidates(tmp_path):
    state = _build_state(tmp_path)
    md = "\n".join(
        [
            "# Some list",
            "- [ ] **TASK-AR-913** Build the thing (status=planned, priority=P0)",
            "- [x] Plain finished item",
            "- not a checklist line",
        ]
    )
    candidates = ui_export.parse_markdown_import(md)
    assert len(candidates) == 2
    first = candidates[0]
    assert first["id"] == "TASK-AR-913"
    assert first["title"] == "Build the thing"
    assert first["priority"] == "P0"
    second = candidates[1]
    assert second["title"] == "Plain finished item"
    assert second["status"] == "completed"


def test_candidate_to_task_create_payload_filters_safe_fields():
    candidate = {
        "id": "TASK-AR-914",
        "title": "New task",
        "status": "planned",
        "priority": "P1",
        "owner": "qa",
        "order": "5",
        "labels": ["alpha"],
        "task_set_id": "TASKSET-AR-DEMO",
        "errors": [],
    }
    payload = ui_export.candidate_to_task_create_payload(candidate)
    assert payload["id"] == "TASK-AR-914"
    assert payload["title"] == "New task"
    assert payload["order"] == 5
    assert payload["tags"] == ["alpha"]
    # No filesystem path keys leak into the payload (proposal-only contract).
    assert "path" not in payload
    assert "source_path" not in payload
