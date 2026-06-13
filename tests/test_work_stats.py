from __future__ import annotations

import csv
import io
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "work.py"


def _run_cli(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return _run_cli(root, "stats", *args)


def _json_payload(stdout: str) -> dict:
    return json.loads(stdout[stdout.index("{") :])


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _work_item(
    *,
    work_id: str,
    kind: str = "task",
    status: str = "completed",
    team: str = "agent-runtime-core",
    owner: str = "lead_engineer",
    origin_type: str = "owner_request",
    worker_model_tier: str = "worker_standard",
    actual_tokens: int | None = None,
    actual_hours: str | None = None,
    rework_count: int | None = None,
    gate_failure_count: int | None = None,
    created_at: str = "2026-06-12T09:00:00+09:00",
    started_at: str | None = "2026-06-12T10:00:00+09:00",
    completed_at: str | None = "2026-06-12T12:30:00+09:00",
    tags: list[str] | None = None,
    extra_lines: list[str] | None = None,
) -> str:
    parent_id = "TASKSET-TEST" if kind == "task" else "TASK-TEST"
    lines = [
        "---",
        "schema_version: agent-runtime-work-item/v1",
        f"work_id: {work_id}",
        "work_uid: 11111111-1111-4111-8111-111111111111",
        f"kind: {kind}",
        f"parent_id: {parent_id}",
        f"status: {status}",
        f"owner: {owner}",
        f"team: {team}",
        f"created_at: {created_at}",
        "updated_at: 2026-06-12T13:00:00+09:00",
        f"origin_type: {origin_type}",
        "origin_ref: reviews/TEST.md",
        "created_by: stats-test",
        f"worker_model_tier: {worker_model_tier}",
        "verification_status: passed",
    ]
    if started_at:
        lines.append(f"started_at: {started_at}")
    if completed_at:
        lines.append(f"completed_at: {completed_at}")
    if actual_tokens is not None:
        lines.append(f"actual_tokens: {actual_tokens}")
    if actual_hours is not None:
        lines.append(f"actual_hours: {actual_hours}")
    if rework_count is not None:
        lines.append(f"rework_count: {rework_count}")
    if gate_failure_count is not None:
        lines.append(f"gate_failure_count: {gate_failure_count}")
    if tags:
        lines.append("tags:")
        lines.extend(f"  - {tag}" for tag in tags)
    if extra_lines:
        lines.extend(extra_lines)
    lines.extend(["---", "", f"# {work_id}", ""])
    return "\n".join(lines)


def test_work_stats_groups_metric_by_dimension_as_json(tmp_path: Path) -> None:
    _write(tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-A.md", _work_item(work_id="TASK-A", actual_tokens=100))
    _write(tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-B.md", _work_item(work_id="TASK-B", actual_tokens=50))
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-C.md",
        _work_item(work_id="TASK-C", team="evaluation-office", origin_type="planning_proposal", actual_tokens=25),
    )

    result = _run(tmp_path, "--by", "team", "--metric", "actual_tokens", "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    assert "work-stats: pass" in result.stdout
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    rows = {row["group"]["team"]: row for row in payload["rows"]}
    assert payload["metric"] == "actual_tokens"
    assert payload["total_items"] == 3
    assert rows["agent-runtime-core"]["count"] == 2
    assert rows["agent-runtime-core"]["value_count"] == 2
    assert rows["agent-runtime-core"]["sum"] == 150
    assert rows["agent-runtime-core"]["avg"] == 75
    assert rows["evaluation-office"]["sum"] == 25


def test_work_stats_computes_lead_time_without_stored_field(tmp_path: Path) -> None:
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-A.md",
        _work_item(
            work_id="TASK-A",
            created_at="2026-06-12T08:00:00+09:00",
            started_at="2026-06-12T10:00:00+09:00",
            completed_at="2026-06-12T13:30:00+09:00",
        ),
    )
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-B.md",
        _work_item(
            work_id="TASK-B",
            created_at="2026-06-12T09:00:00+09:00",
            started_at="",
            completed_at="2026-06-12T10:30:00+09:00",
        ),
    )

    result = _run(tmp_path, "--by", "origin_type", "--metric", "lead_time", "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    row = payload["rows"][0]
    assert row["group"] == {"origin_type": "owner_request"}
    assert row["count"] == 2
    assert row["value_count"] == 2
    assert row["sum"] == 5.0
    assert row["avg"] == 2.5


def test_work_stats_csv_filters_kind_and_status_and_skips_legacy(tmp_path: Path) -> None:
    _write(tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-A.md", _work_item(work_id="TASK-A", actual_hours="1.5"))
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-B.md",
        _work_item(work_id="TASK-B", status="planned", actual_hours="9"),
    )
    _write(tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-LEGACY.md", "---\nid: TASK-LEGACY\n---\n")

    result = _run(tmp_path, "--kind", "task", "--status", "completed", "--by", "status", "--metric", "actual_hours", "--csv")

    assert result.returncode == 0, result.stderr or result.stdout
    assert "TASK-LEGACY" not in result.stdout
    reader = csv.DictReader(io.StringIO(result.stdout))
    rows = list(reader)
    assert rows == [
        {
            "status": "completed",
            "count": "1",
            "value_count": "1",
            "sum": "1.5",
            "avg": "1.5",
            "min": "1.5",
            "max": "1.5",
        }
    ]


def test_work_stats_blocks_unknown_metric_without_writes(tmp_path: Path) -> None:
    _write(tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-A.md", _work_item(work_id="TASK-A"))

    result = _run(tmp_path, "--metric", "progress_pct", "--json")

    assert result.returncode == 1
    assert "work-stats:invalid-metric:progress_pct" in result.stderr
    assert [path.name for path in tmp_path.rglob("*")] == ["agents", "lead_engineer", "tasks", "TASK-A.md"]


def test_work_stats_aggregates_multiple_metrics_per_group(tmp_path: Path) -> None:
    tasks = tmp_path / "agents" / "lead_engineer" / "tasks"
    _write(tasks / "TASK-A.md", _work_item(work_id="TASK-A", actual_tokens=100, rework_count=1))
    _write(tasks / "TASK-B.md", _work_item(work_id="TASK-B", actual_tokens=50))
    _write(tasks / "TASK-C.md", _work_item(work_id="TASK-C", team="evaluation-office", actual_tokens=25, rework_count=2))

    result = _run(tmp_path, "--by", "team", "--metric", "count,actual_tokens,rework_count", "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = _json_payload(result.stdout)
    assert payload["metric"] == "count,actual_tokens,rework_count"
    assert payload["metrics"] == ["count", "actual_tokens", "rework_count"]
    rows = {row["group"]["team"]: row for row in payload["rows"]}
    core = rows["agent-runtime-core"]
    assert core["count"] == 2
    assert "sum" not in core  # legacy flat keys only mirror single-metric queries
    assert core["metrics"]["actual_tokens"] == {"value_count": 2, "sum": 150, "avg": 75, "min": 50, "max": 100}
    assert core["metrics"]["rework_count"] == {"value_count": 1, "sum": 1, "avg": 1, "min": 1, "max": 1}
    assert rows["evaluation-office"]["metrics"]["rework_count"]["sum"] == 2


def test_work_stats_filter_flag_is_repeatable_and_anded(tmp_path: Path) -> None:
    tasks = tmp_path / "agents" / "lead_engineer" / "tasks"
    _write(tasks / "TASK-A.md", _work_item(work_id="TASK-A"))
    _write(tasks / "TASK-B.md", _work_item(work_id="TASK-B", owner="qa"))
    _write(tasks / "TASK-C.md", _work_item(work_id="TASK-C", team="evaluation-office"))

    result = _run(
        tmp_path,
        "--filter",
        "team=agent-runtime-core",
        "--filter",
        "owner=lead_engineer",
        "--by",
        "owner",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = _json_payload(result.stdout)
    assert payload["total_items"] == 1
    assert payload["filters"]["where"] == ["team=agent-runtime-core", "owner=lead_engineer"]
    assert payload["rows"] == [
        {
            "group": {"owner": "lead_engineer"},
            "count": 1,
            "metrics": {"count": {"value_count": 1, "sum": 1, "avg": 1, "min": 1, "max": 1}},
            "value_count": 1,
            "sum": 1,
            "avg": 1,
            "min": 1,
            "max": 1,
        }
    ]


def test_work_stats_age_metric_is_computed_from_now(tmp_path: Path) -> None:
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-A.md",
        _work_item(work_id="TASK-A", created_at="2026-06-12T00:00:00+09:00"),
    )

    result = _run(tmp_path, "--metric", "age", "--now", "2026-06-12T12:00:00+09:00", "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = _json_payload(result.stdout)
    assert payload["rows"][0]["sum"] == 12.0


def test_work_stats_rejects_computed_only_dimensions_and_filters(tmp_path: Path) -> None:
    _write(tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-A.md", _work_item(work_id="TASK-A"))

    by_computed = _run(tmp_path, "--by", "progress_pct", "--json")
    assert by_computed.returncode == 1
    assert "work-stats:computed-only-dimension:progress_pct" in by_computed.stderr

    filter_computed = _run(tmp_path, "--filter", "variance=1", "--json")
    assert filter_computed.returncode == 1
    assert "work-stats:computed-only-filter:variance" in filter_computed.stderr

    by_unknown = _run(tmp_path, "--by", "summary", "--json")
    assert by_unknown.returncode == 1
    assert "work-stats:invalid-dimension:summary" in by_unknown.stderr


def test_work_stats_reports_stored_computed_fields_as_schema_violations(tmp_path: Path) -> None:
    tasks = tmp_path / "agents" / "lead_engineer" / "tasks"
    _write(tasks / "TASK-A.md", _work_item(work_id="TASK-A"))
    _write(tasks / "TASK-B.md", _work_item(work_id="TASK-B", extra_lines=["progress_pct: 80"]))

    result = _run(tmp_path, "--by", "status", "--json")

    assert result.returncode == 1
    assert "TASK-B.md: work-stats:computed-field-stored:progress_pct" in result.stderr


def test_work_stats_exports_item_rows_as_csv(tmp_path: Path) -> None:
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-A.md",
        _work_item(work_id="TASK-A", actual_tokens=100, tags=["alpha", "beta"]),
    )

    result = _run(tmp_path, "--by", "status", "--format", "csv", "--out", "reviews/work-stats-export.csv", "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = _json_payload(result.stdout)
    assert payload["export"] == "reviews/work-stats-export.csv"
    assert payload["export_format"] == "csv"
    assert payload["export_items"] == 1
    export_path = tmp_path / "reviews" / "work-stats-export.csv"
    reader = csv.DictReader(io.StringIO(export_path.read_text(encoding="utf-8")))
    rows = list(reader)
    assert len(rows) == 1
    row = rows[0]
    assert row["work_id"] == "TASK-A"
    assert row["kind"] == "task"
    assert row["status"] == "completed"
    assert row["owner"] == "lead_engineer"
    assert row["team"] == "agent-runtime-core"
    assert row["created_at"] == "2026-06-12T09:00:00+09:00"
    assert row["completed_at"] == "2026-06-12T12:30:00+09:00"
    assert row["tags"] == "alpha|beta"
    assert row["actual_tokens"] == "100"
    assert row["lead_time_hours"] == "2.5"
    assert row["path"] == "agents/lead_engineer/tasks/TASK-A.md"


def test_work_stats_exports_json_with_query_summary_and_items(tmp_path: Path) -> None:
    tasks = tmp_path / "agents" / "lead_engineer" / "tasks"
    _write(tasks / "TASK-A.md", _work_item(work_id="TASK-A", actual_tokens=100, tags=["alpha"]))
    _write(tasks / "TASK-B.md", _work_item(work_id="TASK-B", team="evaluation-office", actual_tokens=25))
    out_path = tmp_path / ".tmp" / "work-stats-export.json"

    result = _run(tmp_path, "--by", "team", "--metric", "actual_tokens", "--out", str(out_path), "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "agent-runtime-work-stats-export/v1"
    assert payload["query"] == {
        "by": ["team"],
        "metrics": ["actual_tokens"],
        "kind": [],
        "status": [],
        "where": [],
    }
    assert payload["summary"]["total_items"] == 2
    assert payload["item_count"] == 2
    items = {item["work_id"]: item for item in payload["items"]}
    assert items["TASK-A"]["tags"] == ["alpha"]
    assert items["TASK-A"]["actual_tokens"] == 100
    assert items["TASK-B"]["team"] == "evaluation-office"
    assert items["TASK-B"]["lead_time_hours"] == 2.5


def test_work_view_save_list_run_roundtrip_reproduces_query(tmp_path: Path) -> None:
    tasks = tmp_path / "agents" / "lead_engineer" / "tasks"
    _write(tasks / "TASK-A.md", _work_item(work_id="TASK-A", actual_tokens=100))
    _write(tasks / "TASK-B.md", _work_item(work_id="TASK-B", status="planned", actual_tokens=10))
    _write(tasks / "TASK-C.md", _work_item(work_id="TASK-C", team="evaluation-office", actual_tokens=25))

    saved = _run_cli(
        tmp_path,
        "view",
        "save",
        "team-tokens",
        "--by",
        "team",
        "--metric",
        "actual_tokens",
        "--filter",
        "status=completed",
        "--now",
        "2026-06-13T10:00:00+09:00",
        "--json",
    )
    assert saved.returncode == 0, saved.stderr or saved.stdout
    assert "work-view-save: saved" in saved.stdout
    views_path = tmp_path / "agents" / "project" / "work-items" / "WORK-VIEWS.json"
    views_payload = json.loads(views_path.read_text(encoding="utf-8"))
    assert views_payload["schema"] == "agent-runtime-work-views/v1"
    assert views_payload["views"][0]["name"] == "team-tokens"
    assert views_payload["views"][0]["query"] == {
        "by": ["team"],
        "metrics": ["actual_tokens"],
        "kind": [],
        "status": [],
        "where": ["status=completed"],
    }

    listed = _run_cli(tmp_path, "view", "list", "--json")
    assert listed.returncode == 0, listed.stderr or listed.stdout
    listed_payload = _json_payload(listed.stdout)
    assert listed_payload["view_count"] == 1
    assert listed_payload["views"][0]["name"] == "team-tokens"

    run = _run_cli(tmp_path, "view", "run", "team-tokens", "--json")
    assert run.returncode == 0, run.stderr or run.stdout
    run_payload = _json_payload(run.stdout)
    assert run_payload.pop("view") == "team-tokens"
    direct = _run(tmp_path, "--by", "team", "--metric", "actual_tokens", "--filter", "status=completed", "--json")
    assert direct.returncode == 0, direct.stderr or direct.stdout
    assert run_payload == _json_payload(direct.stdout)


def test_work_view_run_uses_saved_export_settings(tmp_path: Path) -> None:
    _write(tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-A.md", _work_item(work_id="TASK-A", actual_tokens=100))

    saved = _run_cli(
        tmp_path,
        "view",
        "save",
        "export-view",
        "--by",
        "status",
        "--format",
        "csv",
        "--out",
        ".tmp/view-export.csv",
        "--json",
    )
    assert saved.returncode == 0, saved.stderr or saved.stdout

    run = _run_cli(tmp_path, "view", "run", "export-view", "--json")
    assert run.returncode == 0, run.stderr or run.stdout
    run_payload = _json_payload(run.stdout)
    assert run_payload["export"] == ".tmp/view-export.csv"
    assert run_payload["export_format"] == "csv"
    export_path = tmp_path / ".tmp" / "view-export.csv"
    rows = list(csv.DictReader(io.StringIO(export_path.read_text(encoding="utf-8"))))
    assert [row["work_id"] for row in rows] == ["TASK-A"]


def test_work_view_save_rejects_duplicates_and_invalid_queries(tmp_path: Path) -> None:
    _write(tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-A.md", _work_item(work_id="TASK-A"))

    first = _run_cli(tmp_path, "view", "save", "by-status", "--by", "status", "--json")
    assert first.returncode == 0, first.stderr or first.stdout

    duplicate = _run_cli(tmp_path, "view", "save", "by-status", "--by", "team", "--json")
    assert duplicate.returncode == 1
    assert "work-view:exists:by-status" in duplicate.stderr

    forced = _run_cli(tmp_path, "view", "save", "by-status", "--by", "team", "--force", "--json")
    assert forced.returncode == 0, forced.stderr or forced.stdout
    assert "work-view-save: updated" in forced.stdout

    invalid_metric = _run_cli(tmp_path, "view", "save", "bad-metric", "--metric", "progress_pct", "--json")
    assert invalid_metric.returncode == 1
    assert "work-stats:invalid-metric:progress_pct" in invalid_metric.stderr

    invalid_name = _run_cli(tmp_path, "view", "save", "bad name", "--by", "status", "--json")
    assert invalid_name.returncode == 1
    assert "work-view:invalid-name:bad name" in invalid_name.stderr

    views_payload = json.loads(
        (tmp_path / "agents" / "project" / "work-items" / "WORK-VIEWS.json").read_text(encoding="utf-8")
    )
    assert [view["name"] for view in views_payload["views"]] == ["by-status"]
    assert views_payload["views"][0]["query"]["by"] == ["team"]

    missing = _run_cli(tmp_path, "view", "run", "missing-view", "--json")
    assert missing.returncode == 1
    assert "work-view:not-found:missing-view" in missing.stderr
