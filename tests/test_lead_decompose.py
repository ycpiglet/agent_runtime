import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# task_unit_readiness_gate imports sibling scripts by bare name (import backlog_board).
sys.path.insert(0, str(ROOT / "scripts"))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _brief(i):
    return {
        "title": f"Sample unit {i}",
        "context": f"context for unit {i}",
        "inputs": ["scripts/lead_decompose.py"],
        "target_files": ["scripts/lead_decompose.py"],
        "scope": f"scope for unit {i}",
        "steps": ["do a", "do b"],
        "acceptance": ["it works"],
        "verification": ["pytest -q"],
        "handoff": "report results",
        "stop_condition": "stop after the unit is verified",
    }


def test_decompose_creates_readiness_passing_units(tmp_path):
    ld = _load("lead_decompose")
    gate = _load("task_unit_readiness_gate")
    res = ld.decompose(
        task_id="TASK-AR-901",
        task_set_id="TASKSET-AR-AGENT-ORG-DELEGATION",
        briefs=[_brief(1), _brief(2)],
        units_root=tmp_path,
    )
    assert len(res["created"]) == 2
    pfm = _load("org_model_gate").parse_frontmatter   # stdlib frontmatter parser (no PyYAML)
    for p in res["created"]:
        path = Path(p)
        text = path.read_text(encoding="utf-8")
        meta = pfm(text)
        body = text.split("---", 2)[2]
        findings = gate.validate_unit(ROOT, path, meta, body, require_ready=True)
        assert findings == [], findings


def test_decompose_is_idempotent_and_records_provenance(tmp_path):
    ld = _load("lead_decompose")
    briefs = [_brief(1)]
    r1 = ld.decompose(task_id="TASK-AR-902", task_set_id="TS", briefs=briefs, units_root=tmp_path)
    r2 = ld.decompose(task_id="TASK-AR-902", task_set_id="TS", briefs=briefs, units_root=tmp_path)
    assert len(r1["created"]) == 1
    assert r2["created"] == [] and len(r2["existing"]) == 1
    prov = (tmp_path / "TASK-AR-902" / "DECOMPOSITION.json")
    assert prov.exists()
    assert "UNIT-TASK-AR-902-001" in prov.read_text(encoding="utf-8")


def test_render_unit_rejects_incomplete_brief():
    # W4b finding [Low]: incomplete brief should raise a clear error, not KeyError.
    import pytest
    ld = _load("lead_decompose")
    with pytest.raises(ValueError):
        ld.render_unit(task_id="TASK-AR-903", task_set_id="TS", n=1,
                       brief={"context": "", "scope": "s", "handoff": "h", "stop_condition": "x"})
