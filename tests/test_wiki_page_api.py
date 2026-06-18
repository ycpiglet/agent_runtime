import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_runtime import ui_console, ui_state  # noqa: E402


def _write_wiki_fixture(root: Path) -> None:
    wi = root / "agents" / "project" / "work-items"
    wi.mkdir(parents=True)
    (wi / "WORK-ITEM-CLASSIFICATION.json").write_text(
        json.dumps({
            "records": [
                {"id": "TASKSET-A", "level": "taskset", "title": "Set A"},
                {
                    "id": "TASK-AR-1",
                    "level": "task",
                    "title": "One",
                    "parent_id": "TASKSET-A",
                    "status": "planned",
                    "path": "agents/lead_engineer/tasks/TASK-AR-1.md",
                },
            ]
        }),
        encoding="utf-8",
    )
    task_path = root / "agents" / "lead_engineer" / "tasks"
    task_path.mkdir(parents=True)
    (task_path / "TASK-AR-1.md").write_text("# TASK-AR-1\n", encoding="utf-8")
    reviews = root / "reviews"
    reviews.mkdir()
    (reviews / "REVIEW-2026-06-18-x.md").write_text("Closed TASK-AR-1.\n", encoding="utf-8")


def test_build_wiki_page_envelope_resolves_relations_backlinks_and_minigraph(tmp_path: Path) -> None:
    _write_wiki_fixture(tmp_path)

    page = ui_state.build_wiki_page(tmp_path, "TASK-AR-1", now="2026-06-18T00:00:00+00:00")

    assert page is not None
    assert page["schema"] == ui_state.WIKI_PAGE_SCHEMA
    assert page["id"] == "TASK-AR-1"
    assert page["kind"] == "task"
    assert "# TASK-AR-1" in page["summary"]
    assert page["metadata"]["status"] == "planned"
    assert page["metadata"]["source"] == "agents/lead_engineer/tasks/TASK-AR-1.md"
    assert any(rel["type"] == "partOf" and rel["target_id"] == "TASKSET-A" for rel in page["relations"])
    assert any(back["type"] == "references" and back["source_id"] == "REVIEW-2026-06-18-x" for back in page["backlinks"])
    minigraph_ids = {node["id"] for node in page["minigraph"]["nodes"]}
    assert "TASK-AR-1" in minigraph_ids and "TASKSET-A" in minigraph_ids
    assert all(edge["from"] in minigraph_ids and edge["to"] in minigraph_ids for edge in page["minigraph"]["edges"])


def test_build_wiki_page_missing_entity_returns_none(tmp_path: Path) -> None:
    _write_wiki_fixture(tmp_path)

    assert ui_state.build_wiki_page(tmp_path, "NOPE") is None


def test_ui_console_wiki_page_api_route(tmp_path: Path) -> None:
    _write_wiki_fixture(tmp_path)

    response = ui_console.build_response("/api/wiki/page?id=TASK-AR-1", tmp_path)

    assert response.status == 200
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["resource"] == "wiki_page"
    assert payload["id"] == "TASK-AR-1"
    assert payload["relations"]


def test_ui_console_wiki_page_api_missing_returns_404(tmp_path: Path) -> None:
    _write_wiki_fixture(tmp_path)

    response = ui_console.build_response("/api/wiki/page/NOPE", tmp_path)

    assert response.status == 404
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["resource"] == "wiki_page"
    assert payload["error"] == "not found"
