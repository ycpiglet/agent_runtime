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


def test_cumulative_totals_are_context_only_never_regressed() -> None:
    # Cumulative repo totals grow monotonically with work done; a bigger number
    # must be reported as context, not judged as a regression.
    base = {"version": "v1", "fixed": {"est_tokens_total": 800000, "est_hours_total": 1500.0}}
    cur = {"version": "v2", "fixed": {"est_tokens_total": 1100000, "est_hours_total": 1700.0}}
    lines = se.advisory_gate(cur, base)
    assert not any("REGRESSED" in line for line in lines)
    assert sum("context-only" in line for line in lines) == 2


def test_per_completed_task_estimates_are_judged_lower_is_better() -> None:
    base = {"version": "v1", "fixed": {"est_tokens_per_completed_task": 4200.0}}
    cur = {"version": "v2", "fixed": {"est_tokens_per_completed_task": 4400.0}}
    assert any("REGRESSED" in line for line in se.advisory_gate(cur, base))
    cur["fixed"]["est_tokens_per_completed_task"] = 4000.0
    assert any("improved" in line for line in se.advisory_gate(cur, base))


def test_snapshot_computes_per_task_estimates_and_owner_interventions() -> None:
    snap = se.compute_snapshot("test")
    fixed = snap["fixed"]
    assert fixed["est_tokens_per_completed_task"] == round(
        fixed["est_tokens_total"] / fixed["completed_tasks"], 1
    )
    # This repo has owner_request tasks and OWNER-APPROVAL records on disk.
    assert fixed["owner_intervention_count"] >= 1


def test_null_metrics_excluded_from_delta() -> None:
    # A fixed metric with no captured substrate (null) must not produce a delta line.
    base = {"version": "v1", "fixed": {"rework_count": None, "completed_tasks": 5}}
    cur = {"version": "v2", "fixed": {"rework_count": None, "completed_tasks": 6}}
    lines = se.advisory_gate(cur, base)
    assert not any("rework_count" in line for line in lines)
    assert any("completed_tasks" in line for line in lines)


def _host_root(tmp_path):
    # Minimal repo layout for compute_snapshot/load_host_snapshots against a tmp root.
    (tmp_path / "agents" / "lead_engineer" / "tasks").mkdir(parents=True)
    (tmp_path / "reviews").mkdir()
    return tmp_path


def test_host_eval_absence_is_not_an_error(tmp_path) -> None:
    root = _host_root(tmp_path)
    snap = se.compute_snapshot("test", root=root)
    assert snap["hosts"] == []
    assert "host_skipped" not in snap


def test_host_eval_snapshot_ingested_and_reported(tmp_path) -> None:
    root = _host_root(tmp_path)
    host_dir = root / "agents" / "host" / "eval"
    host_dir.mkdir(parents=True)
    payload = {
        "schema": se.HOST_SCHEMA,
        "host": "autofolio",
        "cycle": "2026-07-pilot-wave-1",
        "fixed": {"gate_failure_count": 2, "rework_count": 1},
        "variable": {"wave_concurrency": 3, "footprint_violations": 0},
    }
    (host_dir / "autofolio-2026-07.json").write_text(
        __import__("json").dumps(payload), encoding="utf-8"
    )
    snap = se.compute_snapshot("test", root=root)
    assert snap["hosts"] == [payload]
    lines = "\n".join(se.advisory_gate(snap, {"version": "v1", "fixed": {}}))
    assert "host[autofolio] cycle 2026-07-pilot-wave-1: 4 real-usage metrics supplied" in lines


def test_host_eval_foreign_or_incomplete_files_are_listed_not_dropped(tmp_path) -> None:
    root = _host_root(tmp_path)
    host_dir = root / "agents" / "host" / "eval"
    host_dir.mkdir(parents=True)
    (host_dir / "broken.json").write_text("{not json", encoding="utf-8")
    (host_dir / "foreign.json").write_text('{"schema": "other/v1"}', encoding="utf-8")
    (host_dir / "incomplete.json").write_text(
        '{"schema": "%s", "host": "autofolio"}' % se.HOST_SCHEMA, encoding="utf-8"
    )
    snap = se.compute_snapshot("test", root=root)
    assert snap["hosts"] == []
    skipped = "\n".join(snap["host_skipped"])
    assert "broken.json: unreadable" in skipped
    assert "foreign.json: schema is not" in skipped
    assert "incomplete.json: missing required host/cycle" in skipped
    # The advisory gate surfaces the skips loudly.
    lines = "\n".join(se.advisory_gate(snap, {"version": "v1", "fixed": {}}))
    assert "host-eval SKIPPED" in lines
