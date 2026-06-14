"""Tests for knowledge_digest — agent-consumable wiki pages + memory (sub-project #2).

Builds on knowledge_graph (#1): digest condenses an entity + its graph context into
an agent-readable page; memory persists pages so an agent can recall them and check
freshness before execution. Deterministic (LLM prose is a later opt-in).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import knowledge_graph as kg  # noqa: E402
import knowledge_digest as kd  # noqa: E402


def _graph():
    return {"schema": kg.SCHEMA, "nodes": [
        {"kind": "task", "id": "TASK-AR-1", "title": "Do the thing",
         "metadata": {"status": "planned"}, "relations": [{"type": "partOf", "target": "TASKSET-A"}]},
        {"kind": "taskset", "id": "TASKSET-A", "title": "Set A", "metadata": {}, "relations": []},
        {"kind": "review", "id": "REVIEW-x", "title": "review x", "metadata": {},
         "relations": [{"type": "references", "target": "TASK-AR-1"}]},
        {"kind": "commit", "id": "abc123", "title": "feat", "metadata": {},
         "relations": [{"type": "mentions", "target": "TASK-AR-1"}]},
    ]}


def _idx():
    return kg.build_index(_graph())


# --- digest page ---

def test_build_page_groups_related_and_backlinks():
    page = kd.build_page(_idx(), "TASK-AR-1")
    assert page["id"] == "TASK-AR-1"
    assert page["kind"] == "task"
    assert page["metadata"]["status"] == "planned"
    fwd = {g["relation"]: [e["id"] for e in g["entities"]] for g in page["related"]}
    assert fwd["partOf"] == ["TASKSET-A"]
    back = {g["relation"]: [e["id"] for e in g["entities"]] for g in page["backlinks"]}
    assert set(back["references"]) == {"REVIEW-x"}
    assert set(back["mentions"]) == {"abc123"}


def test_build_page_unknown_entity_returns_none():
    assert kd.build_page(_idx(), "NOPE") is None


def test_render_markdown_has_sections():
    page = kd.build_page(_idx(), "TASK-AR-1")
    md = kd.render_markdown(page)
    assert "# TASK-AR-1" in md
    assert "Do the thing" in md
    assert "partOf" in md and "TASKSET-A" in md
    assert "Backlinks" in md and "REVIEW-x" in md


# --- fingerprint / freshness ---

def test_fingerprint_stable_and_sensitive():
    idx = _idx()
    fp1 = kd.fingerprint(idx, "TASK-AR-1")
    assert fp1 == kd.fingerprint(_idx(), "TASK-AR-1")  # deterministic
    # change a backlink edge -> fingerprint changes
    g2 = _graph()
    g2["nodes"].append({"kind": "commit", "id": "def456", "title": "x", "metadata": {},
                        "relations": [{"type": "mentions", "target": "TASK-AR-1"}]})
    fp2 = kd.fingerprint(kg.build_index(g2), "TASK-AR-1")
    assert fp1 != fp2


# --- memory ---

def test_remember_recall_list(tmp_path):
    idx = _idx()
    path = kd.remember(tmp_path, idx, "TASK-AR-1")
    assert path.exists()
    recalled = kd.recall(tmp_path, "TASK-AR-1")
    assert recalled["id"] == "TASK-AR-1"
    assert "fingerprint" in recalled
    assert kd.recall(tmp_path, "NOPE") is None
    assert "TASK-AR-1" in kd.list_memory(tmp_path)


def test_is_stale_detects_graph_change(tmp_path):
    kd.remember(tmp_path, _idx(), "TASK-AR-1")
    assert kd.is_stale(tmp_path, _idx(), "TASK-AR-1") is False
    # graph changed -> stored page is stale
    g2 = _graph()
    g2["nodes"][0]["metadata"]["status"] = "completed"
    assert kd.is_stale(tmp_path, kg.build_index(g2), "TASK-AR-1") is True
    # never-remembered entity is "stale" (missing)
    assert kd.is_stale(tmp_path, _idx(), "TASKSET-A") is True


# --- CLI ---

def test_cli_digest_and_memory(tmp_path, capsys, monkeypatch):
    wi = tmp_path / "agents" / "project" / "work-items"
    wi.mkdir(parents=True)
    (wi / "WORK-ITEM-CLASSIFICATION.json").write_text(json.dumps({"records": [
        {"id": "TASKSET-A", "level": "taskset", "title": "A"},
        {"id": "TASK-AR-1", "level": "task", "title": "T1", "parent_id": "TASKSET-A"}]}), encoding="utf-8")
    rc = kd.main(["--root", str(tmp_path), "digest", "TASK-AR-1", "--json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["id"] == "TASK-AR-1"
    assert kd.main(["--root", str(tmp_path), "remember", "TASK-AR-1"]) == 0
    capsys.readouterr()
    assert kd.main(["--root", str(tmp_path), "recall", "TASK-AR-1", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["id"] == "TASK-AR-1"
