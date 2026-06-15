import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("work_efficiency", ROOT / "scripts" / "work_efficiency.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_item_metrics_variance_and_efficiency():
    mod = _load()
    m = mod.item_metrics({
        "id": "TASK-AR-901", "status": "completed",
        "est_tokens": 5000, "actual_tokens": 2000,
        "est_hours": 6, "actual_hours": 4, "team": "engineering",
    })
    assert m["token_variance"] == 3000          # est - actual (under budget)
    assert m["hour_variance"] == 2
    assert m["delivered"] is True
    assert m["efficiency"] == round(1000.0 / 2000, 4)   # delivered per 1k tokens
    # not delivered -> no efficiency
    nd = mod.item_metrics({"id": "X", "status": "planned", "actual_tokens": 100})
    assert nd["delivered"] is False and nd["efficiency"] is None


def test_rank_multi_factor_and_none_last():
    mod = _load()
    rows = [
        {"id": "A", "efficiency": 0.5, "actual_tokens": 2000},
        {"id": "B", "efficiency": 1.0, "actual_tokens": 1000},
        {"id": "C", "efficiency": None, "actual_tokens": None},
    ]
    by_eff = [r["id"] for r in mod.rank(rows, by="efficiency", desc=True)]
    assert by_eff[0] == "B" and by_eff[-1] == "C"        # higher efficiency first, None last
    by_tok = [r["id"] for r in mod.rank(rows, by="actual_tokens", desc=False)]
    assert by_tok[0] == "B"                               # fewest tokens first
    import pytest
    with pytest.raises(ValueError):
        mod.rank(rows, by="not_a_key")


def test_evaluate_reads_real_frontmatter(tmp_path):
    mod = _load()
    d = tmp_path
    (d / "TASK-AR-902.md").write_text(
        "---\nid: TASK-AR-902\nstatus: completed\ntask_set_id: TS\n"
        "est_tokens: 4000\nactual_tokens: 1000\n---\n", encoding="utf-8")
    rows = mod.evaluate(tasks_dir=d, taskset="TS")
    assert len(rows) == 1 and rows[0]["token_variance"] == 3000
