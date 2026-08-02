from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import inflight_overlay

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "inflight_overlay.py"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _task_text(task_id: str, status: str) -> str:
    return "\n".join(
        [
            "---",
            f"id: {task_id}",
            f"status: {status}",
            "priority: P1",
            "owner: lead_engineer",
            "---",
            "",
            "## Goal",
            "",
            f"Goal text for {task_id}.",
            "",
        ]
    )


def _claim_text(task_id: str, status: str) -> str:
    return json.dumps(
        {
            "schema": "agent-runtime-task-claim/v1",
            "claim_id": f"CLAIM-TEST-{task_id}",
            "task_id": task_id,
            "status": status,
        }
    )


# Module-scoped: every test treats the fixture repo as read-only.
@pytest.fixture(scope="module")
def overlay_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    repo = tmp_path_factory.mktemp("inflight-overlay") / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Overlay Test")
    _git(repo, "config", "commit.gpgsign", "false")

    tasks = repo / "agents" / "lead_engineer" / "tasks"
    _write(tasks / "TASK-AR-900.md", _task_text("TASK-AR-900", "planned"))
    _write(tasks / "TASK-AR-901.md", _task_text("TASK-AR-901", "planned"))
    _write(repo / "agents" / "runtime" / "task_claims" / "CLAIM-TEST-TASK-AR-901.json", _claim_text("TASK-AR-901", "claimed"))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "seed main")

    # Claim-less divergence: status flips to completed, branch is 2 ahead.
    _git(repo, "checkout", "-b", "codex/task-ar-900")
    _write(tasks / "TASK-AR-900.md", _task_text("TASK-AR-900", "completed"))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "complete TASK-AR-900 on branch")
    _write(repo / "notes.md", "extra branch commit\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "extra branch work")

    # Claimed divergence: planned -> in_progress.
    _git(repo, "checkout", "main")
    _git(repo, "checkout", "-b", "claude/task-ar-901")
    _write(tasks / "TASK-AR-901.md", _task_text("TASK-AR-901", "in_progress"))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "start TASK-AR-901 on branch")

    # Agent branch without task changes: must not produce records.
    _git(repo, "checkout", "main")
    _git(repo, "checkout", "-b", "claude/no-task-change")
    _write(repo / "docs" / "scratch.md", "no task change\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "non-task change")

    # Non-agent branch with a task status change: must be excluded by pattern.
    _git(repo, "checkout", "main")
    _git(repo, "checkout", "-b", "feature/ignored")
    _write(tasks / "TASK-AR-900.md", _task_text("TASK-AR-900", "blocked"))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "task change on non-agent branch")

    _git(repo, "checkout", "main")
    return repo


def test_overlay_detects_status_divergence_and_claim_join(overlay_repo: Path) -> None:
    overlay = inflight_overlay.build_overlay(overlay_repo)

    assert overlay["schema"] == "agent-runtime-inflight-overlay/v1"
    assert overlay["base"] == "main"
    assert overlay["branches_scanned"] == 3  # codex/task-ar-900, claude/task-ar-901, claude/no-task-change

    by_task = {record["task_id"]: record for record in overlay["records"]}
    assert set(by_task) == {"TASK-AR-900", "TASK-AR-901"}

    ar900 = by_task["TASK-AR-900"]
    assert ar900["main_status"] == "planned"
    assert ar900["branch_status"] == "completed"
    assert ar900["branch"] == "codex/task-ar-900"
    assert ar900["ahead"] == 2
    assert ar900["divergence_flag"] is True
    assert ar900["claim_status"] == "none"
    assert ar900["claimless_flag"] is True
    assert ar900["last_commit"]["subject"] == "extra branch work"
    assert ar900["last_commit"]["hash"]
    assert ar900["last_commit"]["date"]

    ar901 = by_task["TASK-AR-901"]
    assert ar901["main_status"] == "planned"
    assert ar901["branch_status"] == "in_progress"
    assert ar901["branch"] == "claude/task-ar-901"
    assert ar901["ahead"] == 1
    assert ar901["claim_status"] == "active"
    assert ar901["claim_id"] == "CLAIM-TEST-TASK-AR-901"
    assert ar901["claimless_flag"] is False

    assert overlay["summary"] == {
        "divergent_tasks": 2,
        "divergent_records": 2,
        "branches_with_divergence": 2,
        "claimless": 1,
    }


def test_overlay_uses_supplied_canonical_claim_snapshot_without_disk_reload(
    overlay_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    supplied = [
        {
            "schema": "agent-runtime-task-claim/v1",
            "claim_id": "CLAIM-SNAPSHOT-TASK-AR-900",
            "task_id": "TASK-AR-900",
            "status": "claimed",
        }
    ]

    def forbidden_reload(_root: Path) -> dict[str, dict[str, object]]:
        raise AssertionError("supplied canonical snapshot was reloaded from disk")

    monkeypatch.setattr(inflight_overlay, "load_claim_index", forbidden_reload)

    overlay = inflight_overlay.build_overlay(
        overlay_repo,
        claim_snapshot=supplied,
    )
    by_task = {record["task_id"]: record for record in overlay["records"]}

    assert by_task["TASK-AR-900"]["claim_status"] == "active"
    assert by_task["TASK-AR-900"]["claim_id"] == "CLAIM-SNAPSHOT-TASK-AR-900"
    assert by_task["TASK-AR-900"]["claimless_flag"] is False
    assert by_task["TASK-AR-901"]["claim_status"] == "none"
    assert by_task["TASK-AR-901"]["claimless_flag"] is True


def test_overlay_summary_line_formats(overlay_repo: Path) -> None:
    overlay = inflight_overlay.build_overlay(overlay_repo)
    line = inflight_overlay.summary_line(overlay)
    assert line.startswith("inflight: 2 tasks diverge across 2 branches")
    assert "1 claimless" in line
    line.encode("ascii")


def test_overlay_empty_when_no_agent_branch_diverges(tmp_path: Path) -> None:
    repo = tmp_path / "clean"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Overlay Test")
    _git(repo, "config", "commit.gpgsign", "false")
    _write(repo / "agents" / "lead_engineer" / "tasks" / "TASK-AR-910.md", _task_text("TASK-AR-910", "planned"))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "seed")

    overlay = inflight_overlay.build_overlay(repo)

    assert overlay["records"] == []
    assert overlay["summary"]["divergent_tasks"] == 0
    assert inflight_overlay.summary_line(overlay) == "inflight: 0 tasks diverge across 0 branches"


def test_overlay_reports_error_outside_git_repo(tmp_path: Path) -> None:
    overlay = inflight_overlay.build_overlay(tmp_path)

    assert overlay["records"] == []
    assert "error" in overlay
    assert inflight_overlay.summary_line(overlay).startswith("inflight: unavailable")


def test_overlay_scans_remote_tracking_branches(overlay_repo: Path, tmp_path: Path) -> None:
    clone = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", "--quiet", str(overlay_repo), str(clone)],
        check=True,
        capture_output=True,
        text=True,
    )

    overlay = inflight_overlay.build_overlay(clone)

    assert overlay["base"] == "origin/main"
    by_task = {record["task_id"]: record for record in overlay["records"]}
    assert set(by_task) == {"TASK-AR-900", "TASK-AR-901"}
    # Remote prefix is stripped from the reported branch name.
    assert by_task["TASK-AR-900"]["branch"] == "codex/task-ar-900"
    assert by_task["TASK-AR-900"]["branch_ref"] == "origin/codex/task-ar-900"


def test_overlay_cli_json_summary_and_table(overlay_repo: Path) -> None:
    json_run = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(overlay_repo), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(json_run.stdout)
    assert payload["schema"] == "agent-runtime-inflight-overlay/v1"
    assert {record["task_id"] for record in payload["records"]} == {"TASK-AR-900", "TASK-AR-901"}
    record = payload["records"][0]
    for key in (
        "task_id",
        "main_status",
        "branch_status",
        "branch",
        "ahead",
        "last_commit",
        "claim_status",
        "divergence_flag",
        "claimless_flag",
    ):
        assert key in record
    json_run.stdout.encode("ascii")

    summary_run = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(overlay_repo), "--summary"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert summary_run.stdout.strip().startswith("inflight: 2 tasks diverge across 2 branches")

    table_run = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(overlay_repo)],
        check=True,
        capture_output=True,
        text=True,
    )
    table_run.stdout.encode("ascii")
    assert "TASK-AR-900" in table_run.stdout
    assert "claimless" in table_run.stdout
    assert table_run.stdout.strip().splitlines()[-1].startswith("inflight: 2 tasks diverge")


def test_frontmatter_status_parses_only_leading_block() -> None:
    assert inflight_overlay.frontmatter_status("---\nstatus: planned\n---\nbody") == "planned"
    assert inflight_overlay.frontmatter_status("---\nid: X\n---\nstatus: stray") is None
    assert inflight_overlay.frontmatter_status("no frontmatter") is None
    assert inflight_overlay.frontmatter_status(None) is None


def test_agent_branch_pattern_excludes_archive_and_other_prefixes() -> None:
    assert inflight_overlay.is_agent_branch("codex/task-ar-370")
    assert inflight_overlay.is_agent_branch("claude/task-ar-513-inflight-overlay")
    assert not inflight_overlay.is_agent_branch("archive/codex/task-ar-370")
    assert not inflight_overlay.is_agent_branch("feature/anything")
    assert not inflight_overlay.is_agent_branch("main")


def test_ui_state_exposes_inflight_resource(overlay_repo: Path) -> None:
    from agent_runtime import ui_state

    assert "inflight" in ui_state.RESOURCE_NAMES
    resource = ui_state.build_resource(overlay_repo, "inflight")
    overlay = resource["items"]
    assert overlay["schema"] == "agent-runtime-inflight-overlay/v1"
    assert {record["task_id"] for record in overlay["records"]} == {"TASK-AR-900", "TASK-AR-901"}
    assert overlay["summary"]["claimless"] == 1


def test_ui_console_serves_inflight_route_and_board_annotation_hooks(overlay_repo: Path) -> None:
    from agent_runtime import ui_console

    response = ui_console.build_response("/api/inflight", overlay_repo)
    payload = json.loads(response.body.decode("utf-8"))
    assert response.status == 200
    assert payload["resource"] == "inflight"
    assert {record["task_id"] for record in payload["items"]["records"]} == {"TASK-AR-900", "TASK-AR-901"}

    js = ui_console.build_response("/app.js", overlay_repo).body.decode("utf-8")
    assert "inflightAnnotation" in js
    assert "task-card-inflight" in js
    css = ui_console.build_response("/app.css", overlay_repo).body.decode("utf-8")
    assert ".task-card .task-card-inflight" in css


def test_ui_state_inflight_warns_but_stays_empty_outside_git(tmp_path: Path) -> None:
    from agent_runtime import ui_state

    state = ui_state.build_state(tmp_path, now="2026-06-13T00:00:00+09:00")
    assert state["inflight"]["records"] == []
    warning_kinds = {warning["kind"] for warning in state["warnings"]}
    assert "inflight-overlay-unavailable" in warning_kinds
