from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "taskset_dispatcher.py"


def _write_task(root: Path, task_id: str, task_set_id: str, *, status: str = "planned", priority: str = "P0") -> None:
    tasks_dir = root / "agents" / "lead_engineer" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    (tasks_dir / f"{task_id}.md").write_text(
        f"""---
id: {task_id}
status: {status}
priority: {priority}
difficulty: M
est_hours: 2
est_tokens: 200
task_set_id: {task_set_id}
tags:
  - test
---

## Goal
- Test task for {task_set_id}.
""",
        encoding="utf-8",
    )


def _run(root: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


def test_plan_accepts_human_friendly_taskset_alias_and_emits_next_commands(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-901", "TASKSET-AR-QUALITY-LOOP", status="planned")
    _write_task(tmp_path, "TASK-AR-902", "TASKSET-AR-QUALITY-LOOP", status="planned", priority="P1")

    result = _run(tmp_path, "plan", "quality-loop", "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["task_set_id"] == "TASKSET-AR-QUALITY-LOOP"
    assert payload["display_name"] == "Quality Sentinel"
    assert payload["next_task_id"] == "TASK-AR-901"
    assert payload["claim_command"][0].endswith("python.exe") or payload["claim_command"][0].endswith("python")
    assert "--task-set-id" in payload["claim_command"]
    assert "TASKSET-AR-QUALITY-LOOP" in payload["claim_command"]
    assert payload["worktree_path"] == ".worktrees/TASK-AR-901"
    assert payload["branch"].startswith("codex/task-ar-901-quality-loop")


def test_plan_skips_completed_tasks(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-901", "TASKSET-AR-RELEASE-STEWARD", status="completed")
    _write_task(tmp_path, "TASK-AR-902", "TASKSET-AR-RELEASE-STEWARD", status="planned")

    result = _run(tmp_path, "plan", "release-steward", "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["next_task_id"] == "TASK-AR-902"
    assert payload["next_task_status"] == "planned"


def test_plan_fails_when_taskset_has_no_open_tasks(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-901", "TASKSET-AR-RELEASE-STEWARD", status="completed")

    result = _run(tmp_path, "plan", "release-steward", "--json")

    assert result.returncode == 1
    assert "task set has no open tasks" in (result.stderr or result.stdout)


def test_start_creates_claim_with_taskset_progress_metadata(tmp_path: Path) -> None:
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_task(tmp_path, "TASK-AR-901", "TASKSET-AR-PANE-PROGRESS", status="planned")
    worktree = tmp_path / ".worktrees" / "TASK-AR-901"
    worktree.mkdir(parents=True, exist_ok=True)
    (worktree / ".git").write_text("gitdir: ../../.git/worktrees/test\n", encoding="utf-8")

    result = _run(
        tmp_path,
        "start",
        "progress-scout",
        "--agent-role",
        "lead-engineer",
        "--team-id",
        "agent-runtime-core",
        "--mode",
        "implement",
        "--now",
        "2026-06-10T19:40:00+09:00",
        "--suffix",
        "p1",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    claim = payload["claim"]["claim"]
    assert payload["next_task_id"] == "TASK-AR-901"
    assert claim["task_set_id"] == "TASKSET-AR-PANE-PROGRESS"
    assert claim["step_index"] == 1
    assert claim["step_total"] == 1
    assert claim["status_text"] == "Starting Progress Scout: TASK-AR-901"
    assert claim["phase"] == "taskset-claimed"
    assert claim["progress_pct"] == 0


def test_start_creates_missing_worktree_before_claiming_taskset(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_task(tmp_path, "TASK-AR-901", "TASKSET-AR-PANE-PROGRESS", status="planned")
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_git = fake_bin / "git.cmd"
    fake_git.write_text(
        "\n".join(
            [
                "@echo off",
                "echo %*>>\"%GIT_FAKE_LOG%\"",
                "mkdir \"%CD%\\.worktrees\\TASK-AR-901\" 2>nul",
                "echo gitdir: fake>\"%CD%\\.worktrees\\TASK-AR-901\\.git\"",
                "exit /b 0",
            ]
        ),
        encoding="utf-8",
    )
    fake_log = tmp_path / "fake-git.log"
    env = dict(**__import__("os").environ)
    path_key = "Path" if "Path" in env else "PATH"
    env[path_key] = f"{fake_bin};{env.get(path_key, '')}"
    env["GIT_FAKE_LOG"] = str(fake_log)
    env["AGENT_RUNTIME_GIT"] = str(fake_git)

    result = _run(tmp_path, "start", "progress-scout", "--json", env=env)

    assert result.returncode == 0, result.stderr or result.stdout
    assert "worktree add -b codex/task-ar-901-pane-progress .worktrees/TASK-AR-901" in fake_log.read_text(
        encoding="utf-8"
    )
    assert (tmp_path / ".worktrees" / "TASK-AR-901" / ".git").exists()
    assert list((tmp_path / "agents" / "runtime" / "task_claims").glob("*.json"))


def test_start_blocks_when_taskset_already_has_active_claim(tmp_path: Path) -> None:
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_task(tmp_path, "TASK-AR-901", "TASKSET-AR-QUALITY-LOOP", status="planned")
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    claim_dir.mkdir(parents=True, exist_ok=True)
    (claim_dir / "CLAIM-active.json").write_text(
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": "CLAIM-active",
                "task_id": "TASK-AR-900",
                "task_set_id": "TASKSET-AR-QUALITY-LOOP",
                "agent_role": "qa",
                "agent_instance_id": "qa-1",
                "display_name": "qa@eval-01",
                "callsite_id": "terminal-1",
                "pane_id": "terminal-1",
                "team_id": "validation-team",
                "status": "working",
                "phase": "implement",
                "progress_pct": 20,
                "status_text": "Already working",
                "worktree_path": ".worktrees/TASK-AR-900",
                "branch": "codex/task-ar-900-quality-loop",
                "claimed_at": "2026-06-10T19:30:00+09:00",
                "last_heartbeat": "2026-06-10T19:35:00+09:00",
                "handoff_path": "STATUS.md",
                "log_path": "STATUS.md",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run(tmp_path, "start", "TASKSET-AR-QUALITY-LOOP", "--json")

    assert result.returncode == 1
    assert "task set already has an active claim" in (result.stderr or result.stdout)
