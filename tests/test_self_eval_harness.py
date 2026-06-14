import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import self_eval_harness as se  # noqa: E402


def test_snapshot_has_full_fixed_schema_and_variable() -> None:
    snap = se.compute_snapshot("test")
    assert snap["schema"] == se.SCHEMA
    # The held-out fixed schema is the stable spine -- every metric key present.
    assert set(snap["fixed"].keys()) == set(se.FIXED_METRICS)
    assert snap["fixed"]["completed_tasks"] >= 1
    assert 0 <= snap["fixed"]["verification_coverage_pct"] <= 100
    assert "council_deliberations" in snap["variable"]


def test_advisory_gate_reports_improvement() -> None:
    base = {"version": "v1", "fixed": {"completed_tasks": 10, "verification_coverage_pct": 50.0, "open_tasks": 5}}
    cur = {"version": "v2", "fixed": {"completed_tasks": 15, "verification_coverage_pct": 70.0, "open_tasks": 3}}
    text = "\n".join(se.advisory_gate(cur, base))
    assert "improved" in text  # more done, higher coverage, fewer open
    assert "REGRESSED" not in text


def test_advisory_gate_flags_regression_by_direction() -> None:
    # coverage is higher-is-better; a drop must read as a regression.
    base = {"version": "v1", "fixed": {"verification_coverage_pct": 80.0}}
    cur = {"version": "v2", "fixed": {"verification_coverage_pct": 60.0}}
    assert any("REGRESSED" in line for line in se.advisory_gate(cur, base))


def test_null_metrics_excluded_from_delta() -> None:
    # A fixed metric with no captured substrate (null) must not produce a delta line.
    base = {"version": "v1", "fixed": {"rework_count": None, "completed_tasks": 5}}
    cur = {"version": "v2", "fixed": {"rework_count": None, "completed_tasks": 6}}
    lines = se.advisory_gate(cur, base)
    assert not any("rework_count" in line for line in lines)
    assert any("completed_tasks" in line for line in lines)
