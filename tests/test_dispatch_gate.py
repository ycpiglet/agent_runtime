import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def _load():
    spec = importlib.util.spec_from_file_location("dispatch_gate", ROOT / "scripts" / "dispatch_gate.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_orchestrator():
    spec = importlib.util.spec_from_file_location(
        "org_orchestrator_for_dispatch_test", ROOT / "scripts" / "org_orchestrator.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_risk_mode_auto_vs_owner_gate():
    mod = _load()
    assert mod.risk_mode({"risk_tier": "low"})[0] == "auto"
    assert mod.risk_mode({"risk_tier": "medium"})[0] == "auto"
    assert mod.risk_mode({"risk_tier": "high"})[0] == "owner-gate"
    assert mod.risk_mode({"risk_tier": "critical"})[0] == "owner-gate"
    assert mod.risk_mode({"risk_tier": "low", "security_sensitive": True})[0] == "owner-gate"
    assert mod.risk_mode({"risk_tier": "low", "approval_required": True})[0] == "owner-gate"
    assert mod.risk_mode({"risk_tier": "low", "budget_cap": 100, "est_tokens": 500})[0] == "owner-gate"
    assert mod.risk_mode({"risk_tier": "low", "escalation_triggers": ["security"]})[0] == "owner-gate"


def test_seam_parallel_only_when_disjoint():
    mod = _load()
    units = [
        ("U1", {"risk_tier": "low", "target_files": ["a.py"]}),
        ("U2", {"risk_tier": "low", "target_files": ["b.py"]}),      # disjoint -> parallel
        ("U3", {"risk_tier": "low", "target_files": ["a.py"]}),      # conflicts U1 -> serialize
        ("U4", {"risk_tier": "high", "target_files": ["c.py"]}),     # risky -> owner-gate
    ]
    plan = {e["unit_id"]: e for e in mod.plan_dispatch(units)}
    assert plan["U1"]["seam"] == "parallel"
    assert plan["U2"]["seam"] == "parallel"
    assert plan["U3"]["seam"] == "serialize"
    assert plan["U4"]["mode"] == "owner-gate"


def test_concurrency_cap_serializes_excess():
    mod = _load()
    units = [(f"U{i}", {"risk_tier": "low", "target_files": [f"f{i}.py"]}) for i in range(5)]
    plan = mod.plan_dispatch(units, max_parallel=2)
    seams = [e["seam"] for e in plan]
    assert seams.count("parallel") == 2
    assert seams.count("serialize") == 3


def test_unit_frontmatter_preserves_encoded_worker_order_fields(tmp_path):
    dispatch = _load()
    orchestrator = _load_orchestrator()
    import work

    context = "False"
    target = "007"
    acceptance = "-7"
    unit = tmp_path / "UNIT-TEST-001.md"
    unit.write_text(
        work._frontmatter(
            {
                "unit_id": "UNIT-TEST-001",
                "context": context,
                "target_files": [target],
                "acceptance": [acceptance],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    meta = dispatch._front_meta(unit)
    order = orchestrator.build_order("UNIT-TEST-001", meta, "worker")

    assert order["context"] == context
    assert order["target_files"] == [target]
    assert order["acceptance"] == [acceptance]
