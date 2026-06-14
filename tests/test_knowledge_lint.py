"""Tests for knowledge_lint — integrity + freshness gate over the graph (sub-project #3).

Builds on knowledge_graph (#1) and knowledge_digest (#2): lint surfaces stale/orphan
memory pages, duplicate ids, dangling edges (structural=block vs informational=watch),
and orphan entities as severity-classified, CI-wireable findings. Deterministic.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import knowledge_graph as kg  # noqa: E402
import knowledge_digest as kd  # noqa: E402
import knowledge_lint as kl  # noqa: E402


def _graph(extra=None):
    nodes = [
        {"kind": "task", "id": "TASK-AR-1", "title": "T1", "metadata": {"status": "planned"},
         "relations": [{"type": "partOf", "target": "TASKSET-A"}]},
        {"kind": "taskset", "id": "TASKSET-A", "title": "Set A", "metadata": {},
         "relations": []},
        {"kind": "review", "id": "REVIEW-x", "title": "rx", "metadata": {},
         "relations": [{"type": "references", "target": "TASK-AR-1"}]},
    ]
    if extra:
        nodes += extra
    return {"schema": kg.SCHEMA, "nodes": nodes}


def _codes(findings):
    return {f["code"] for f in findings}


def _by_code(findings, code):
    return [f for f in findings if f["code"] == code]


# --- structural ---

def test_clean_graph_has_no_block_findings():
    findings = kl.lint_structural(_graph(), kg.build_index(_graph()))
    assert all(f["severity"] != "block" for f in findings)


def test_duplicate_id_is_block():
    dup = {"kind": "task", "id": "TASK-AR-1", "title": "dup", "metadata": {}, "relations": []}
    g = _graph(extra=[dup])
    findings = kl.lint_structural(g, kg.build_index(g))
    dups = _by_code(findings, "duplicate-id")
    assert dups and dups[0]["severity"] == "block"
    assert dups[0]["id"] == "TASK-AR-1"


def test_dangling_structural_edge_is_block():
    g = _graph(extra=[{"kind": "task", "id": "TASK-AR-9", "title": "T9", "metadata": {},
                       "relations": [{"type": "dependsOn", "target": "TASK-AR-MISSING"}]}])
    findings = kl.lint_structural(g, kg.build_index(g))
    dangling = _by_code(findings, "dangling-edge")
    structural = [f for f in dangling if "TASK-AR-MISSING" in f["detail"]]
    assert structural and structural[0]["severity"] == "block"


def test_dangling_informational_edge_is_watch():
    g = _graph(extra=[{"kind": "commit", "id": "abc123", "title": "c", "metadata": {},
                       "relations": [{"type": "mentions", "target": "TASK-AR-GONE"}]}])
    findings = kl.lint_structural(g, kg.build_index(g))
    dangling = [f for f in _by_code(findings, "dangling-edge") if "TASK-AR-GONE" in f["detail"]]
    assert dangling and dangling[0]["severity"] == "watch"


def test_orphan_entity_is_watch():
    # an isolated work-item kind (taskset nobody links to) is a planning defect
    g = _graph(extra=[{"kind": "taskset", "id": "TASKSET-LONELY", "title": "lonely", "metadata": {},
                       "relations": []}])
    findings = kl.lint_structural(g, kg.build_index(g))
    orphans = _by_code(findings, "orphan-entity")
    assert any(f["id"] == "TASKSET-LONELY" and f["severity"] == "watch" for f in orphans)
    # connected nodes are not orphans
    assert all(f["id"] != "TASK-AR-1" for f in orphans)


def test_orphan_entity_ignores_observational_kinds():
    # commits/reviews are leaves by nature; isolation must not be flagged
    g = _graph(extra=[{"kind": "commit", "id": "deadbeef", "title": "c", "metadata": {},
                       "relations": []}])
    findings = kl.lint_structural(g, kg.build_index(g))
    assert all(f["id"] != "deadbeef" for f in _by_code(findings, "orphan-entity"))


# --- memory freshness ---

def test_stale_memory_is_block(tmp_path):
    idx = kg.build_index(_graph())
    kd.remember(tmp_path, idx, "TASK-AR-1")
    # mutate the graph so the remembered page drifts
    g2 = _graph()
    g2["nodes"][0]["metadata"]["status"] = "completed"
    findings = kl.lint_memory(tmp_path, kg.build_index(g2))
    stale = _by_code(findings, "stale-memory")
    assert stale and stale[0]["severity"] == "block" and stale[0]["id"] == "TASK-AR-1"


def test_orphan_memory_is_block(tmp_path):
    idx = kg.build_index(_graph())
    kd.remember(tmp_path, idx, "TASK-AR-1")
    # graph no longer contains TASK-AR-1
    g2 = {"schema": kg.SCHEMA, "nodes": [
        {"kind": "taskset", "id": "TASKSET-A", "title": "A", "metadata": {}, "relations": []}]}
    findings = kl.lint_memory(tmp_path, kg.build_index(g2))
    orphan = _by_code(findings, "orphan-memory")
    assert orphan and orphan[0]["severity"] == "block" and orphan[0]["id"] == "TASK-AR-1"


def test_fresh_memory_has_no_findings(tmp_path):
    idx = kg.build_index(_graph())
    kd.remember(tmp_path, idx, "TASK-AR-1")
    assert kl.lint_memory(tmp_path, idx) == []


# --- combine + summarize ---

def test_lint_combines_and_sorts(tmp_path):
    dup = {"kind": "task", "id": "TASK-AR-1", "title": "dup", "metadata": {}, "relations": []}
    g = _graph(extra=[dup])
    findings = kl.lint(tmp_path, g)
    assert "duplicate-id" in _codes(findings)
    severities = [f["severity"] for f in findings]
    # blocks sort before watches
    assert severities == sorted(severities, key=lambda s: 0 if s == "block" else 1)


def test_summarize_counts():
    findings = [
        {"code": "duplicate-id", "severity": "block", "id": "x", "detail": ""},
        {"code": "orphan-entity", "severity": "watch", "id": "y", "detail": ""},
    ]
    s = kl.summarize(findings)
    assert s == {"block": 1, "watch": 1, "total": 2}


# --- CLI ---

def _write_classification(tmp_path):
    wi = tmp_path / "agents" / "project" / "work-items"
    wi.mkdir(parents=True, exist_ok=True)
    (wi / "WORK-ITEM-CLASSIFICATION.json").write_text(json.dumps({"records": [
        {"id": "TASKSET-A", "level": "taskset", "title": "A"},
        {"id": "TASK-AR-1", "level": "task", "title": "T1", "parent_id": "TASKSET-A"}]}), encoding="utf-8")


def test_cli_clean_exit_zero(tmp_path, capsys):
    _write_classification(tmp_path)
    rc = kl.main(["--root", str(tmp_path), "check", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert out["summary"]["block"] == 0
    assert rc == 0


def test_cli_block_exit_one(tmp_path, capsys):
    _write_classification(tmp_path)
    # remember TASK-AR-1, then make it stale by re-tagging status in classification
    kg_graph = kg.build_graph(tmp_path)
    kd.remember(tmp_path, kg.build_index(kg_graph), "TASK-AR-1")
    cls = tmp_path / "agents" / "project" / "work-items" / "WORK-ITEM-CLASSIFICATION.json"
    cls.write_text(json.dumps({"records": [
        {"id": "TASKSET-A", "level": "taskset", "title": "A"},
        {"id": "TASK-AR-1", "level": "task", "title": "T1 RENAMED", "parent_id": "TASKSET-A"}]}), encoding="utf-8")
    rc = kl.main(["--root", str(tmp_path), "check", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert "stale-memory" in {f["code"] for f in out["findings"]}
    assert rc == 1


def test_cli_strict_fails_on_watch(tmp_path, capsys):
    _write_classification(tmp_path)
    # add an orphan work-item entity directly via a prebuilt graph file
    graph_path = tmp_path / kg.GRAPH_REL
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_text(json.dumps(_graph(extra=[
        {"kind": "taskset", "id": "TASKSET-LONELY", "title": "lonely", "metadata": {}, "relations": []}])), encoding="utf-8")
    rc_default = kl.main(["--root", str(tmp_path), "check", "--graph", str(graph_path), "--json"])
    capsys.readouterr()
    assert rc_default == 0  # orphan is watch-only
    rc_strict = kl.main(["--root", str(tmp_path), "check", "--graph", str(graph_path), "--strict", "--json"])
    capsys.readouterr()
    assert rc_strict == 1
