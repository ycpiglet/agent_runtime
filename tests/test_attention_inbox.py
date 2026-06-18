import datetime as dt
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))  # org_model_gate / multi_host_claim_gate sibling imports


def _load():
    spec = importlib.util.spec_from_file_location("attention_inbox", ROOT / "scripts" / "attention_inbox.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _task(d: Path, tid: str, **fm):
    lines = "\n".join(f"{k}: {v}" for k, v in fm.items())
    (d / f"{tid}.md").write_text(f"---\nid: {tid}\n{lines}\n---\n", encoding="utf-8")


def test_blocked_adapter(tmp_path):
    mod = _load()
    _task(tmp_path, "TASK-AR-901", status="blocked")
    _task(tmp_path, "TASK-AR-902", status="in_progress")
    items = mod.blocked(mod._load_tasks(tmp_path))
    assert [i["id"] for i in items] == ["TASK-AR-901"]
    assert items[0]["group"] == "blocked" and items[0]["action"]


def test_approval_adapter(tmp_path):
    mod = _load()
    _task(tmp_path, "TASK-AR-903", status="planned", approval_required="true")
    _task(tmp_path, "TASK-AR-904", status="completed", approval_required="true")  # done -> excluded
    items = mod.approval_pending(mod._load_tasks(tmp_path))
    assert [i["id"] for i in items] == ["TASK-AR-903"]
    assert items[0]["group"] == "approval_pending"


def test_stale_adapter(tmp_path):
    mod = _load()
    now = dt.datetime(2026, 6, 15, tzinfo=dt.timezone.utc)
    _task(tmp_path, "TASK-AR-905", status="in_progress", updated_at="2026-06-01T00:00:00+00:00")  # 14d
    _task(tmp_path, "TASK-AR-906", status="in_progress", updated_at="2026-06-14T00:00:00+00:00")  # 1d
    items = mod.stale(mod._load_tasks(tmp_path), now=now, stale_days=7)
    assert [i["id"] for i in items] == ["TASK-AR-905"]
    assert items[0]["age_days"] >= 7


def test_cost_and_gate_adapters(tmp_path):
    mod = _load()
    _task(tmp_path, "TASK-AR-907", status="in_progress", est_tokens="100", actual_tokens="500")
    _task(tmp_path, "TASK-AR-908", status="in_progress", gate_failure_count="2")
    cost = mod.cost_anomalies(mod._load_tasks(tmp_path))
    gates = mod.gate_failures(mod._load_tasks(tmp_path))
    assert [i["id"] for i in cost] == ["TASK-AR-907"]
    assert [i["id"] for i in gates] == ["TASK-AR-908"]


def test_inbox_aggregates_and_empty_state(tmp_path):
    mod = _load()
    now = dt.datetime(2026, 6, 15, tzinfo=dt.timezone.utc)
    td = tmp_path / "agents" / "lead_engineer" / "tasks"
    td.mkdir(parents=True)
    empty = mod.inbox(tmp_path, now=now)
    assert empty["total"] == 0
    assert set(empty["groups"]) == {"approval_pending", "blocked", "stale",
                                    "gate_failures", "cost_anomalies", "runtime_anomalies"}
    assert empty["counts"]["blocked"] == 0
    _task(td, "TASK-AR-909", status="blocked")
    one = mod.inbox(tmp_path, now=now)
    assert one["total"] == 1 and one["counts"]["blocked"] == 1


def test_runtime_anomaly_adapter_uses_claim_conflicts(tmp_path, monkeypatch):
    mod = _load()
    monkeypatch.setattr(mod, "_claim_conflicts", lambda root: [{"resource": "TASK-AR-1", "hosts": ["a", "b"]}])
    items = mod.runtime_anomalies(tmp_path)
    assert items and items[0]["group"] == "runtime_anomalies"
    assert "a" in items[0]["why"] and "b" in items[0]["why"]
