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
                {"id": "TASKSET-A", "level": "taskset", "title": "Search Set"},
                {
                    "id": "TASK-AR-1",
                    "level": "task",
                    "title": "Searchable One",
                    "parent_id": "TASKSET-A",
                    "status": "planned",
                    "path": "agents/lead_engineer/tasks/TASK-AR-1.md",
                },
                {
                    "id": "TASK-AR-2",
                    "level": "task",
                    "title": "Other Task",
                    "parent_id": "TASKSET-A",
                    "status": "completed",
                    "path": "agents/lead_engineer/tasks/TASK-AR-2.md",
                },
            ]
        }),
        encoding="utf-8",
    )
    task_path = root / "agents" / "lead_engineer" / "tasks"
    task_path.mkdir(parents=True)
    (task_path / "TASK-AR-1.md").write_text("# TASK-AR-1\nSearchable One\n", encoding="utf-8")
    (task_path / "TASK-AR-2.md").write_text("# TASK-AR-2\nOther Task\n", encoding="utf-8")
    reviews = root / "reviews"
    reviews.mkdir()
    (reviews / "REVIEW-2026-06-18-search.md").write_text("Closed TASK-AR-1.\n", encoding="utf-8")


def test_ui_console_wiki_search_api_returns_ranked_results(tmp_path: Path) -> None:
    _write_wiki_fixture(tmp_path)

    response = ui_console.build_response("/api/wiki/search?q=TASK-AR-1", tmp_path)

    assert response.status == 200
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["resource"] == "wiki_search"
    assert payload["query"] == "TASK-AR-1"
    assert payload["results"][0]["id"] == "TASK-AR-1"
    assert payload["results"][0]["score"] == 3
    assert set(payload["results"][0]) == {"id", "kind", "title", "snippet", "score"}


def test_ui_console_wiki_ask_default_is_evidence_only(tmp_path: Path) -> None:
    _write_wiki_fixture(tmp_path)

    response = ui_console.build_response("/api/wiki/ask?q=Searchable", tmp_path)

    assert response.status == 200
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["resource"] == "wiki_ask"
    assert payload["query"] == "Searchable"
    assert payload["llm_used"] is False
    assert payload["cited"] == ["TASK-AR-1"]
    assert payload["evidence"][0]["id"] == "TASK-AR-1"
    assert "Evidence-only result" in payload["answer"]


def test_ui_console_wiki_ask_llm_opt_in_degrades_without_provider(tmp_path: Path, monkeypatch) -> None:
    _write_wiki_fixture(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    response = ui_console.build_response("/api/wiki/ask?q=Searchable&llm=1", tmp_path)

    payload = json.loads(response.body.decode("utf-8"))
    assert payload["llm_used"] is False
    assert payload["evidence"][0]["id"] == "TASK-AR-1"
    assert payload["note"] == "llm-requested-but-no-provider: returning deterministic evidence pack"


def test_build_wiki_ask_llm_opt_in_uses_mocked_synthesizer(tmp_path: Path) -> None:
    _write_wiki_fixture(tmp_path)

    payload = ui_state.build_wiki_ask(
        tmp_path,
        "Searchable",
        use_llm=True,
        synthesizer=lambda question, context: f"mock answer for {context[0]['root']['id']}",
    )

    assert payload["llm_used"] is True
    assert payload["answer"] == "mock answer for TASK-AR-1"
    assert payload["cited"] == ["TASK-AR-1"]
