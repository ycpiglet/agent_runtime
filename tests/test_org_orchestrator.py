import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("org_orchestrator", ROOT / "scripts" / "org_orchestrator.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _units():
    return [
        ("U1", {"risk_tier": "low", "target_files": ["a.py"], "est_tokens": 100}),
        ("U2", {"risk_tier": "low", "target_files": ["b.py"], "est_tokens": 100}),
        ("U3", {"risk_tier": "high", "target_files": ["c.py"], "est_tokens": 100}),  # owner-gate
    ]


def test_orchestrator_spawns_workers_and_reviewers_holds_risky():
    mod = _load()
    backend = mod.RecordingBackend()
    rep = mod.Orchestrator(backend).run(_units())
    worker_ids = [w["unit_id"] for w in rep["workers"]]
    assert worker_ids == ["U1", "U2"]                       # U3 held
    assert [h["unit_id"] for h in rep["held_for_owner"]] == ["U3"]
    # every released worker gets an independent reviewer (reviewer != worker order)
    assert [r["unit_id"] for r in rep["reviewers"]] == ["U1", "U2"]
    roles = {o["role"] for o in backend.spawned}
    assert roles == {"worker", "reviewer"}


def test_orchestrator_idempotent_skip():
    mod = _load()
    rep = mod.Orchestrator(mod.RecordingBackend()).run(_units(), done_unit_ids={"U1"})
    assert "U1" in rep["skipped_idempotent"]
    assert "U1" not in [w["unit_id"] for w in rep["workers"]]


def test_orchestrator_token_budget_stops_dispatch():
    mod = _load()
    rep = mod.Orchestrator(mod.RecordingBackend(), budget_total=150).run(_units())
    # U1 (100) fits; U2 (would be 200) stops; U3 is owner-gated regardless
    assert [w["unit_id"] for w in rep["workers"]] == ["U1"]
    assert "U2" in rep["stopped_over_budget"]
    assert rep["tokens_spent"] == 100


def test_budget_is_stop_the_line_not_skip_over():
    # W4b finding [Med]: spec F2 = once budget is consumed, remaining units WAIT.
    mod = _load()
    units = [
        ("U1", {"risk_tier": "low", "target_files": ["a.py"], "est_tokens": 100}),
        ("U2", {"risk_tier": "low", "target_files": ["b.py"], "est_tokens": 100}),  # over budget
        ("U3", {"risk_tier": "low", "target_files": ["c.py"], "est_tokens": 10}),   # cheap, but line stopped
    ]
    rep = mod.Orchestrator(mod.RecordingBackend(), budget_total=150).run(units)
    assert [w["unit_id"] for w in rep["workers"]] == ["U1"]
    assert rep["stopped_over_budget"] == ["U2", "U3"]   # U3 not dispatched despite being cheap


def test_backend_is_swappable_interface():
    mod = _load()
    # the orchestrator only depends on the WorkerBackend ABC, never on a concrete backend
    assert issubclass(mod.RecordingBackend, mod.WorkerBackend)
    for method in ("spawn", "poll", "terminate"):
        assert hasattr(mod.WorkerBackend, method)
