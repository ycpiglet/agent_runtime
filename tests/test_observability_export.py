import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("observability_export", ROOT / "scripts" / "observability_export.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _fixture(tmp: Path):
    td = tmp / "agents" / "lead_engineer" / "tasks"
    td.mkdir(parents=True)
    (td / "TASK-AR-901.md").write_text("---\nid: TASK-AR-901\nstatus: completed\nest_tokens: 100\nactual_tokens: 80\n---\n", encoding="utf-8")
    (td / "TASK-AR-902.md").write_text("---\nid: TASK-AR-902\nstatus: in_progress\nest_tokens: 200\n---\n", encoding="utf-8")
    (td / "TASK-AR-903.md").write_text("---\nid: TASK-AR-903\nstatus: planned\n---\n", encoding="utf-8")


def test_collect_aggregates_metrics(tmp_path):
    mod = _load()
    _fixture(tmp_path)
    m = mod.collect(tmp_path)
    assert m["tasks_total"] == 3
    assert m["tasks_done"] == 1
    assert m["tasks_active"] == 1
    assert m["est_tokens_total"] == 300
    assert m["actual_tokens_total"] == 80
    assert m["completion_ratio"] == round(1 / 3, 4)


def test_prometheus_format(tmp_path):
    mod = _load()
    _fixture(tmp_path)
    text = mod.to_prometheus(mod.collect(tmp_path))
    assert "agent_runtime_tasks_total 3" in text
    assert "# TYPE agent_runtime_tasks_done gauge" in text
    assert 'agent_runtime_tasks_status{status="completed"} 1' in text


def test_collect_runs_on_real_repo():
    mod = _load()
    m = mod.collect()
    assert m["tasks_total"] > 0 and 0.0 <= m["completion_ratio"] <= 1.0
