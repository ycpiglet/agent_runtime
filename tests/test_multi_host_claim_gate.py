import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("multi_host_claim_gate", ROOT / "scripts" / "multi_host_claim_gate.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_claim_host_resolution():
    mod = _load()
    assert mod.claim_host({"host": "alpha"}) == "alpha"
    assert mod.claim_host({"callsite_id": "beta:pane3"}) == "beta"
    assert mod.claim_host({"callsite_id": "gamma/term1"}) == "gamma"
    assert mod.claim_host({}) == "unknown"


def test_detect_cross_host_conflict():
    mod = _load()
    claims = [
        {"claim_id": "C1", "task_id": "TASK-AR-1", "status": "in_progress", "host": "alpha"},
        {"claim_id": "C2", "task_id": "TASK-AR-1", "status": "claimed", "host": "beta"},   # cross-host conflict
        {"claim_id": "C3", "task_id": "TASK-AR-2", "status": "in_progress", "host": "alpha"},
        {"claim_id": "C4", "task_id": "TASK-AR-2", "status": "released", "host": "beta"},   # not active -> no conflict
    ]
    conflicts = mod.detect_conflicts(claims)
    assert len(conflicts) == 1
    assert conflicts[0]["resource"] == "TASK-AR-1"
    assert conflicts[0]["hosts"] == ["alpha", "beta"]


def test_same_host_multiple_claims_is_not_a_conflict():
    mod = _load()
    claims = [
        {"claim_id": "C1", "task_id": "TASK-AR-1", "status": "in_progress", "host": "alpha"},
        {"claim_id": "C2", "task_id": "TASK-AR-1", "status": "claimed", "host": "alpha"},
    ]
    assert mod.detect_conflicts(claims) == []


def test_enforce_blocks_on_conflict(tmp_path):
    mod = _load()
    import json
    d = tmp_path
    (d / "CLAIM-a.json").write_text(json.dumps({"claim_id": "A", "task_id": "T", "status": "claimed", "host": "h1"}), encoding="utf-8")
    (d / "CLAIM-b.json").write_text(json.dumps({"claim_id": "B", "task_id": "T", "status": "claimed", "host": "h2"}), encoding="utf-8")
    claims = mod.load_claims(d)
    assert len(mod.detect_conflicts(claims)) == 1
