"""Tests for knowledge_ask — RAG Q&A grounded in the graph, LLM opt-in (sub-project #4).

Retrieval + context assembly are deterministic and always run; LLM synthesis is an
opt-in that degrades to the deterministic evidence pack with no provider. No network
calls here — the LLM path is exercised via an injected synthesizer.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import knowledge_graph as kg  # noqa: E402
import knowledge_ask as ka  # noqa: E402


def _graph():
    return {"schema": kg.SCHEMA, "nodes": [
        {"kind": "task", "id": "TASK-AR-552", "title": "claim reaper concurrency stress tests",
         "metadata": {"status": "planned"},
         "relations": [{"type": "partOf", "target": "TASKSET-REL"}]},
        {"kind": "taskset", "id": "TASKSET-REL", "title": "reliability", "metadata": {}, "relations": []},
        {"kind": "task", "id": "TASK-AR-341", "title": "workspace switcher and widgets ui",
         "metadata": {}, "relations": []},
        {"kind": "review", "id": "REVIEW-reap", "title": "concurrency reaping review", "metadata": {},
         "relations": [{"type": "references", "target": "TASK-AR-552"}]},
    ]}


def _idx():
    return kg.build_index(_graph())


# --- term extraction ---

def test_terms_drops_stopwords_and_short():
    terms = ka._terms("How is the claim reaper concurrency-safe?")
    assert "claim" in terms and "reaper" in terms
    assert "is" not in terms and "the" not in terms
    assert all(len(t) >= 3 for t in terms)


# --- retrieval ---

def test_retrieve_ranks_on_topic_first():
    seeds = ka.retrieve(_graph(), _idx(), "claim reaper concurrency", k=5)
    ids = [s["id"] for s in seeds]
    assert ids[0] == "TASK-AR-552"
    assert "TASK-AR-341" not in ids[:1]


def test_retrieve_respects_k():
    seeds = ka.retrieve(_graph(), _idx(), "reaper reliability concurrency review", k=2)
    assert len(seeds) <= 2


# --- answer: deterministic default ---

def test_answer_deterministic_shape():
    res = ka.answer(Path("."), _graph(), "claim reaper concurrency", k=3)
    assert res["mode"] == "deterministic"
    assert res["answer"] is None
    assert "TASK-AR-552" in res["citations"]
    assert res["context"] and res["context"][0]["root"]["id"] in res["citations"]


# --- answer: LLM opt-in via injected synthesizer ---

def test_answer_llm_uses_injected_synthesizer():
    seen = {}

    def fake(question, context):
        seen["q"] = question
        seen["n"] = len(context)
        return "Reaping is once-only via per-claim lock [TASK-AR-552]."

    res = ka.answer(Path("."), _graph(), "claim reaper concurrency", use_llm=True, synthesizer=fake)
    assert res["mode"] == "llm"
    assert "TASK-AR-552" in res["answer"]
    assert seen["q"] == "claim reaper concurrency"
    assert seen["n"] == len(res["context"])


def test_answer_llm_without_provider_degrades(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    res = ka.answer(Path("."), _graph(), "claim reaper concurrency", use_llm=True)
    assert res["mode"] == "deterministic"
    assert res["answer"] is None
    assert res["note"] and "provider" in res["note"]


# --- prompt assembly ---

def test_build_prompt_grounds_and_cites():
    idx = _idx()
    context = [kg.context_pack(idx, "TASK-AR-552")]
    prompt = ka._build_prompt("how is reaping safe?", context)
    assert "how is reaping safe?" in prompt
    assert "TASK-AR-552" in prompt
    assert "only" in prompt.lower()  # grounding instruction


# --- CLI ---

def test_cli_deterministic_json(tmp_path, capsys):
    graph_path = tmp_path / kg.GRAPH_REL
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_text(json.dumps(_graph()), encoding="utf-8")
    rc = ka.main(["--root", str(tmp_path), "ask", "claim reaper concurrency",
                  "--graph", str(graph_path), "--json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["mode"] == "deterministic"
    assert "TASK-AR-552" in out["citations"]
