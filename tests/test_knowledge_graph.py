"""Tests for knowledge_graph — agent-first knowledge graph substrate + ingest + query.

Sub-project #1 (design 2026-06-14): a self-contained typed entity graph
(`{kind,id,title,metadata,relations}`, compatible with entity_catalog) ingesting
work-items / reviews / git / claims, with an in-memory index and agent query API
(get / search / neighbors / backlinks / path / context-pack). Deterministic, no LLM.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import knowledge_graph as kg  # noqa: E402


def _graph(*entities) -> dict:
    return {"schema": kg.SCHEMA, "nodes": list(entities)}


def _node(kind, eid, title="", rels=None):
    return {"kind": kind, "id": eid, "title": title or eid, "metadata": {}, "relations": rels or []}


def _rel(t, target):
    return {"type": t, "target": target}


# --- index + traversal ---

def test_build_index_forward_and_backward():
    g = _graph(
        _node("task", "TASK-AR-1", rels=[_rel("partOf", "TASKSET-A")]),
        _node("task", "TASK-AR-2", rels=[_rel("partOf", "TASKSET-A"), _rel("blocks", "TASK-AR-1")]),
        _node("taskset", "TASKSET-A"),
    )
    idx = kg.build_index(g)
    assert idx.by_id["TASK-AR-1"]["kind"] == "task"
    assert ("partOf", "TASKSET-A") in idx.forward["TASK-AR-1"]
    # backward: who points at TASKSET-A / TASK-AR-1
    assert ("partOf", "TASK-AR-1") in idx.backward["TASKSET-A"]
    assert ("blocks", "TASK-AR-2") in idx.backward["TASK-AR-1"]


def test_neighbors_and_backlinks():
    g = _graph(
        _node("task", "T1", rels=[_rel("partOf", "S1"), _rel("references", "R1")]),
        _node("taskset", "S1"),
        _node("review", "R1"),
        _node("commit", "abc", rels=[_rel("mentions", "T1")]),
    )
    idx = kg.build_index(g)
    nb = {(r, t) for r, t in kg.neighbors(idx, "T1")}
    assert nb == {("partOf", "S1"), ("references", "R1")}
    assert kg.neighbors(idx, "T1", rel="partOf") == [("partOf", "S1")]
    # backlinks: the commit mentions T1
    assert ("mentions", "abc") in kg.backlinks(idx, "T1")


def test_path_between():
    g = _graph(
        _node("commit", "c1", rels=[_rel("mentions", "T1")]),
        _node("task", "T1", rels=[_rel("partOf", "S1")]),
        _node("taskset", "S1"),
    )
    idx = kg.build_index(g)
    p = kg.path(idx, "c1", "S1")
    assert p == ["c1", "T1", "S1"]
    assert kg.path(idx, "S1", "nonexistent") == []


def test_context_pack_assembles_subgraph():
    g = _graph(
        _node("task", "T1", "Do thing", rels=[_rel("partOf", "S1")]),
        _node("taskset", "S1"),
        _node("review", "R1", rels=[_rel("references", "T1")]),
    )
    idx = kg.build_index(g)
    pack = kg.context_pack(idx, "T1")
    assert pack["root"]["id"] == "T1"
    out_ids = {n["id"] for n in pack["neighbors"]}
    in_ids = {n["id"] for n in pack["backlinks"]}
    assert "S1" in out_ids        # T1 -> partOf -> S1
    assert "R1" in in_ids         # R1 -> references -> T1


def test_search_scoped_and_ranked():
    g = _graph(
        _node("task", "TASK-AR-9", "alpha widget"),
        _node("review", "REVIEW-x", "alpha review"),
    )
    res = kg.search(g, "kind:task alpha")
    assert [n["id"] for n in res] == ["TASK-AR-9"]


def test_check_graph_flags_dangling():
    g = _graph(_node("task", "T1", rels=[_rel("partOf", "MISSING")]))
    findings = kg.check_graph(g)
    assert any("MISSING" in f for f in findings)


# --- ingest from sources ---

def test_ingest_work_items(tmp_path):
    wi = tmp_path / "agents" / "project" / "work-items"
    wi.mkdir(parents=True)
    (wi / "WORK-ITEM-CLASSIFICATION.json").write_text(json.dumps({"records": [
        {"id": "TASKSET-A", "level": "taskset", "title": "Set A", "number": "1", "status": "active", "path": "x"},
        {"id": "TASK-AR-1", "level": "task", "title": "Task 1", "parent_id": "TASKSET-A", "status": "planned"},
    ]}), encoding="utf-8")
    nodes = kg.ingest_work_items(tmp_path)
    by_id = {n["id"]: n for n in nodes}
    assert by_id["TASK-AR-1"]["kind"] == "task"
    assert {"type": "partOf", "target": "TASKSET-A"} in by_id["TASK-AR-1"]["relations"]


def test_ingest_reviews(tmp_path):
    reviews = tmp_path / "reviews"
    reviews.mkdir()
    (reviews / "RETRO-2026-06-14-x-TASK-AR-1.md").write_text("retro body", encoding="utf-8")
    (reviews / "INDEX.md").write_text("index", encoding="utf-8")
    nodes = kg.ingest_reviews(tmp_path)
    by_id = {n["id"]: n for n in nodes}
    assert "INDEX" not in by_id
    rev = next(n for n in nodes if n["kind"] == "retro")
    assert {"type": "references", "target": "TASK-AR-1"} in rev["relations"]


def test_ingest_reviews_scans_body_for_references(tmp_path):
    reviews = tmp_path / "reviews"
    reviews.mkdir()
    # filename has no entity id; the body cites a task, taskset, and initiative
    (reviews / "REVIEW-2026-06-14-process-closeout.md").write_text(
        "## Bottom Line\nClosed TASK-AR-552 under TASKSET-AR-COLLAB-CONCURRENCY for INIT-AR-HOST-FEEDBACK-INTAKE.\n",
        encoding="utf-8",
    )
    nodes = kg.ingest_reviews(tmp_path)
    rev = next(n for n in nodes if n["id"] == "REVIEW-2026-06-14-process-closeout")
    targets = {r["target"] for r in rev["relations"] if r["type"] == "references"}
    assert {"TASK-AR-552", "TASKSET-AR-COLLAB-CONCURRENCY", "INIT-AR-HOST-FEEDBACK-INTAKE"} <= targets


def test_ingest_docs_adds_doc_nodes_and_work_item_edges(tmp_path):
    wi = tmp_path / "agents" / "project" / "work-items"
    wi.mkdir(parents=True)
    (wi / "WORK-ITEM-CLASSIFICATION.json").write_text(
        json.dumps({"records": [{"id": "TASK-AR-1", "level": "task", "title": "One"}]}),
        encoding="utf-8",
    )
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text("# Guide\nDocuments TASK-AR-1 and links [[Ops]].\n", encoding="utf-8")
    (tmp_path / "OPS-TEST.md").write_text("# Ops\n", encoding="utf-8")

    graph = kg.build_graph(tmp_path, git_limit=0)
    by_id = {n["id"]: n for n in graph["nodes"]}
    guide = by_id["doc:docs/guide.md"]

    assert guide["kind"] == "doc"
    assert guide["title"] == "Guide"
    assert {"type": "references", "target": "TASK-AR-1"} in guide["relations"]
    assert {"type": "documents", "target": "TASK-AR-1"} in guide["relations"]
    assert {"type": "references", "target": "doc:OPS-TEST.md"} in guide["relations"]


def test_ingest_code_modules_adds_import_file_and_test_edges(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "a.py").write_text("import b\n", encoding="utf-8")
    (scripts / "b.py").write_text("VALUE = 1\n", encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_a.py").write_text("import a\n", encoding="utf-8")

    graph = kg.build_graph(tmp_path, git_limit=0)
    by_id = {n["id"]: n for n in graph["nodes"]}
    module_a = by_id["module:scripts.a"]
    test_a = by_id["module:tests.test_a"]

    assert by_id["file:scripts/a.py"]["kind"] == "file"
    assert {"type": "defined_in", "target": "file:scripts/a.py"} in module_a["relations"]
    assert {"type": "imports", "target": "module:scripts.b"} in module_a["relations"]
    assert {"type": "tests", "target": "module:scripts.a"} in test_a["relations"]
    assert {"type": "tested_by", "target": "module:tests.test_a"} in module_a["relations"]


def test_ingest_configs_and_schemas_adds_validation_edges(tmp_path):
    wi = tmp_path / "agents" / "project" / "work-items"
    wi.mkdir(parents=True)
    (wi / "WORK-ITEM-CLASSIFICATION.json").write_text(
        json.dumps({"records": [{"id": "TASK-AR-1", "level": "task", "title": "One"}]}),
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text("# configures TASK-AR-1\n", encoding="utf-8")
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    (schemas / "task.schema.json").write_text('{"description":"validates TASK-AR-1"}', encoding="utf-8")

    graph = kg.build_graph(tmp_path, git_limit=0)
    by_id = {n["id"]: n for n in graph["nodes"]}

    assert by_id["config:pyproject.toml"]["kind"] == "config"
    assert {"type": "configures", "target": "TASK-AR-1"} in by_id["config:pyproject.toml"]["relations"]
    assert by_id["schema:schemas/task.schema.json"]["kind"] == "schema"
    assert {"type": "validates", "target": "TASK-AR-1"} in by_id["schema:schemas/task.schema.json"]["relations"]


def test_ingest_assets_links_registry_to_files_and_evidence(tmp_path):
    registry_dir = tmp_path / "agents" / "project"
    registry_dir.mkdir(parents=True)
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "example_gate.py").write_text("print('example_gate')\n", encoding="utf-8")
    reviews = tmp_path / "reviews"
    reviews.mkdir()
    (reviews / "REVIEW-2026-06-18-example.md").write_text("example_gate evidence\n", encoding="utf-8")
    (registry_dir / "RUNTIME-ASSET-REGISTRY.json").write_text(
        json.dumps({
            "schema": "agent-runtime-asset-registry/v1",
            "assets": [{
                "id": "gate.example",
                "kind": "gate",
                "status": "active",
                "lifecycle": "keep",
                "paths": ["scripts/example_gate.py"],
                "evidence_paths": ["reviews/REVIEW-2026-06-18-example.md"],
                "tokens": ["example_gate"],
            }],
        }),
        encoding="utf-8",
    )

    graph = kg.build_graph(tmp_path, git_limit=0)
    by_id = {n["id"]: n for n in graph["nodes"]}
    asset = by_id["asset:gate/example"]

    assert asset["kind"] == "asset"
    assert asset["metadata"]["asset_id"] == "gate.example"
    assert {"type": "defined_in", "target": "file:scripts/example_gate.py"} in asset["relations"]
    assert {"type": "used_by", "target": "REVIEW-2026-06-18-example"} in asset["relations"]


def test_build_graph_wires_capability_domains(tmp_path):
    wi = tmp_path / "agents" / "project" / "work-items"
    wi.mkdir(parents=True)
    (wi / "WORK-ITEM-CLASSIFICATION.json").write_text(json.dumps({"records": [
        {"id": "INIT-AR-X", "level": "initiative", "title": "Init X"},
        {"id": "TASKSET-AR-X", "level": "taskset", "title": "Set X"}]}), encoding="utf-8")
    (wi / "DOMAINS.json").write_text(json.dumps({
        "schema": "agent-runtime-domains/v1",
        "domains": [{"id": "DOMAIN-X", "title": "Domain X", "summary": "s", "members": ["INIT-AR-X"]}],
        "initiative_tasksets": {"INIT-AR-X": ["TASKSET-AR-X"], "INIT-AR-MISSING": ["TASKSET-AR-X"]},
    }), encoding="utf-8")
    graph = kg.build_graph(tmp_path, git_limit=0)
    by_id = {n["id"]: n for n in graph["nodes"]}
    assert by_id["DOMAIN-X"]["kind"] == "domain"
    # initiative -> domain and taskset -> initiative partOf edges exist
    assert {"type": "partOf", "target": "DOMAIN-X"} in by_id["INIT-AR-X"]["relations"]
    assert {"type": "partOf", "target": "INIT-AR-X"} in by_id["TASKSET-AR-X"]["relations"]
    # an edge to a non-existent parent (INIT-AR-MISSING) is skipped, not dangling
    assert all(r["target"] != "INIT-AR-MISSING" for r in by_id["TASKSET-AR-X"]["relations"])


def test_ingest_domains_missing_file_is_empty(tmp_path):
    assert kg.ingest_domains(tmp_path) == []


def test_build_graph_prunes_dangling_reference_edges(tmp_path):
    # a review body references a real task plus bogus id-shaped tokens (filename / date)
    reviews = tmp_path / "reviews"
    reviews.mkdir()
    (reviews / "REVIEW-2026-06-14-x.md").write_text(
        "Closed TASK-AR-1; see TASKSET-DEFINITIONS and TASK-AR-20260611.\n", encoding="utf-8")
    wi = tmp_path / "agents" / "project" / "work-items"
    wi.mkdir(parents=True)
    (wi / "WORK-ITEM-CLASSIFICATION.json").write_text(
        json.dumps({"records": [{"id": "TASK-AR-1", "level": "task", "title": "One"}]}), encoding="utf-8")
    graph = kg.build_graph(tmp_path, git_limit=0)
    review = next(n for n in graph["nodes"] if n["id"] == "REVIEW-2026-06-14-x")
    targets = {r["target"] for r in review["relations"] if r["type"] == "references"}
    assert "TASK-AR-1" in targets  # real node kept
    assert "TASKSET-DEFINITIONS" not in targets  # dangling reference pruned
    assert "TASK-AR-20260611" not in targets


def test_build_graph_keeps_dangling_structural_edges(tmp_path):
    # a task whose partOf taskset is missing must STAY dangling (lint flags it block)
    wi = tmp_path / "agents" / "project" / "work-items"
    wi.mkdir(parents=True)
    (wi / "WORK-ITEM-CLASSIFICATION.json").write_text(
        json.dumps({"records": [
            {"id": "TASK-AR-9", "level": "task", "title": "Nine", "parent_id": "TASKSET-GONE"}]}),
        encoding="utf-8")
    graph = kg.build_graph(tmp_path, git_limit=0)
    task = next(n for n in graph["nodes"] if n["id"] == "TASK-AR-9")
    assert {"type": "partOf", "target": "TASKSET-GONE"} in task["relations"]


def test_build_graph_prunes_inactive_claim_executes_missing_task(tmp_path):
    cl = tmp_path / "agents" / "runtime" / "task_claims"
    cl.mkdir(parents=True)
    (cl / "CLAIM-x.json").write_text(json.dumps({
        "claim_id": "CLAIM-x",
        "task_id": "TASK-AR-590",
        "status": "expired",
    }), encoding="utf-8")

    graph = kg.build_graph(tmp_path, git_limit=0)
    claim = next(n for n in graph["nodes"] if n["id"] == "CLAIM-x")

    assert {"type": "executes", "target": "TASK-AR-590"} not in claim["relations"]
    assert kg.check_graph(graph) == []


def test_build_graph_keeps_active_claim_executes_missing_task(tmp_path):
    cl = tmp_path / "agents" / "runtime" / "task_claims"
    cl.mkdir(parents=True)
    (cl / "CLAIM-x.json").write_text(json.dumps({
        "claim_id": "CLAIM-x",
        "task_id": "TASK-AR-590",
        "status": "assigned",
    }), encoding="utf-8")

    graph = kg.build_graph(tmp_path, git_limit=0)
    claim = next(n for n in graph["nodes"] if n["id"] == "CLAIM-x")

    assert {"type": "executes", "target": "TASK-AR-590"} in claim["relations"]
    assert any("TASK-AR-590" in finding for finding in kg.check_graph(graph))


def test_reference_targets_dedupes_caps_and_excludes_self():
    body = " ".join(f"TASK-AR-{i}" for i in range(60)) + " REVIEW-SELF"
    refs = kg._reference_targets("REVIEW-SELF", body, self_id="REVIEW-SELF")
    assert "REVIEW-SELF" not in refs
    assert len(refs) <= kg.MAX_BODY_REFS
    assert refs == sorted(refs)


def test_ingest_claims(tmp_path):
    cl = tmp_path / "agents" / "runtime" / "task_claims"
    cl.mkdir(parents=True)
    (cl / "CLAIM-x.json").write_text(json.dumps({
        "claim_id": "CLAIM-x", "task_id": "TASK-AR-1", "status": "released"}), encoding="utf-8")
    nodes = kg.ingest_claims(tmp_path)
    assert nodes[0]["kind"] == "claim"
    assert {"type": "executes", "target": "TASK-AR-1"} in nodes[0]["relations"]


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_ingest_git(tmp_path):
    def g(*a):
        return subprocess.run(["git", "-C", str(tmp_path), *a], capture_output=True, text=True)
    g("init"); g("config", "user.email", "t@e"); g("config", "user.name", "t")
    (tmp_path / "f.txt").write_text("x", encoding="utf-8")
    g("add", "-A"); g("commit", "-m", "feat: do TASK-AR-1 (#42)")
    nodes = kg.ingest_git(tmp_path, limit=5)
    commit = next(n for n in nodes if n["kind"] == "commit")
    targets = {(r["type"], r["target"]) for r in commit["relations"]}
    assert ("mentions", "TASK-AR-1") in targets
    assert ("partOf", "PR-42") in targets


# --- end to end build + CLI ---

def test_build_graph_combines_sources(tmp_path):
    wi = tmp_path / "agents" / "project" / "work-items"
    wi.mkdir(parents=True)
    (wi / "WORK-ITEM-CLASSIFICATION.json").write_text(json.dumps({"records": [
        {"id": "TASK-AR-1", "level": "task", "title": "Task 1", "status": "planned"}]}), encoding="utf-8")
    (tmp_path / "reviews").mkdir()
    (tmp_path / "reviews" / "REVIEW-2026-06-14-x-TASK-AR-1.md").write_text("r", encoding="utf-8")
    graph = kg.build_graph(tmp_path, git_limit=0)
    assert graph["schema"] == kg.SCHEMA
    ids = {n["id"] for n in graph["nodes"]}
    assert "TASK-AR-1" in ids
    assert any(n["kind"] == "review" for n in graph["nodes"])


def test_cli_build_and_query(tmp_path, capsys):
    wi = tmp_path / "agents" / "project" / "work-items"
    wi.mkdir(parents=True)
    (wi / "WORK-ITEM-CLASSIFICATION.json").write_text(json.dumps({"records": [
        {"id": "TASKSET-A", "level": "taskset", "title": "A"},
        {"id": "TASK-AR-1", "level": "task", "title": "T1", "parent_id": "TASKSET-A"}]}), encoding="utf-8")
    assert kg.main(["--root", str(tmp_path), "build", "--write"]) == 0
    assert (wi / "KNOWLEDGE-GRAPH.json").exists()
    capsys.readouterr()
    assert kg.main(["--root", str(tmp_path), "neighbors", "TASK-AR-1", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert any(t == "TASKSET-A" for _, t in out["neighbors"]) or \
        any(n.get("target") == "TASKSET-A" for n in out["neighbors"])


def test_enable_utf8_stdout_is_safe_on_unreconfigurable_stream(monkeypatch):
    import io
    # a plain StringIO has no reconfigure(); the helper must not raise
    monkeypatch.setattr("knowledge_graph.sys.stdout", io.StringIO())
    monkeypatch.setattr("knowledge_graph.sys.stderr", io.StringIO())
    kg.enable_utf8_stdout()  # no exception = pass
