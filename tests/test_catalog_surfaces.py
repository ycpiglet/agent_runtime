import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_runtime import ui_state  # noqa: E402


def test_catalog_entity_has_relations_and_backlinks() -> None:  # TASK-AR-541
    detail = ui_state.catalog_entity(ROOT, "TASK-AR-539")
    assert detail is not None
    assert detail["entity"]["id"] == "TASK-AR-539"
    # forward: the task is partOf its taskset
    assert any(rel["type"] == "partOf" for rel in detail["relations"])
    # backlinks: the W4B verification record references this task
    assert any(b["type"] == "references" for b in detail["backlinks"])


def test_catalog_entity_missing_returns_none() -> None:
    assert ui_state.catalog_entity(ROOT, "NOPE-DOES-NOT-EXIST") is None


def test_catalog_facets_counts_and_needs_attention() -> None:  # TASK-AR-543
    facets = ui_state.catalog_facets(ROOT)
    assert facets["by_kind"].get("task", 0) > 0
    assert facets["total"] > 0
    assert "triage_count" in facets["needs_attention"]


def test_catalog_docs_groups_doc_kinds() -> None:  # TASK-AR-545
    docs = ui_state.catalog_docs(ROOT)
    assert docs["counts"].get("verification", 0) > 0  # W4B records
    verifications = docs["kinds"]["verification"]
    assert verifications and all("id" in row for row in verifications)
    # doc kinds only -- no task/taskset leaked in
    assert "task" not in docs["counts"]


def test_entity_activity_unifies_records_and_commits() -> None:  # TASK-AR-542
    activity = ui_state.entity_activity(ROOT, "TASK-AR-539")
    assert activity["entity_id"] == "TASK-AR-539"
    assert activity["count"] >= 1
    types = {event["type"] for event in activity["events"]}
    assert "references" in types or "committed" in types
    dates = [event.get("date") or "" for event in activity["events"]]
    assert dates == sorted(dates, reverse=True)  # chronological desc


def test_scm_overview_has_branches_and_commits() -> None:  # TASK-AR-544
    scm = ui_state.scm_overview(ROOT)
    assert scm["current_branch"]
    assert scm["branch_count"] >= 1
    assert scm["recent_commits"] and "hash" in scm["recent_commits"][0]
