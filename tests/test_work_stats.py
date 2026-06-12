from __future__ import annotations

import csv
import io
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "work.py"


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), "stats", *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


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
