import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("unit_readiness_report", ROOT / "scripts" / "unit_readiness_report.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _task(d: Path, tid: str, status: str):
    (d / f"{tid}.md").write_text(f"---\nid: {tid}\nstatus: {status}\n---\n", encoding="utf-8")


def _unit(units_root: Path, tid: str, uid: str, status: str):
    ud = units_root / tid
    ud.mkdir(parents=True, exist_ok=True)
    (ud / f"{uid}.md").write_text(f"---\nunit_id: {uid}\nstatus: {status}\n---\n", encoding="utf-8")


def test_report_splits_ready_vs_needs_refinement(tmp_path):
    mod = _load()
    tasks = tmp_path / "tasks"
    units = tasks / "units"
    tasks.mkdir(parents=True)
    _task(tasks, "TASK-AR-901", "planned")          # no units -> needs refinement
    _task(tasks, "TASK-AR-902", "planned")          # has worker-ready unit
    _unit(units, "TASK-AR-902", "UNIT-TASK-AR-902-001", "worker_ready")
    _task(tasks, "TASK-AR-903", "completed")        # not pending -> ignored

    r = mod.report(tasks_dir=tasks, units_root=units)
    assert r["summary"]["ready_to_dispatch"] == 1
    assert r["summary"]["needs_planner_refinement"] == 1
    assert "TASK-AR-901" in r["needs_refinement"]
    assert r["with_worker_ready_units"][0]["task"] == "TASK-AR-902"
    assert r["with_worker_ready_units"][0]["worker_ready"] == 1
    # completed task is excluded from the pending migration report
    assert r["pending_total"] == 2
