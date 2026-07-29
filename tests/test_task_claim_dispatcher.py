from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from agent_runtime import knowledge_records


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "task_claim_dispatcher.py"
GATE = REPO_ROOT / "scripts" / "parallel_worktree_gate.py"
CONCURRENCY_GATE = REPO_ROOT / "scripts" / "collaboration_concurrency_gate.py"
IDENTITY_GATE = REPO_ROOT / "scripts" / "agent_identity_gate.py"


def _routing_off_env() -> dict[str, str]:
    """Pin the dormant-role routing flags OFF so these baseline claim-lifecycle
    tests assert the unchanged behavior deterministically, regardless of an
    ambient flag in the developer's shell (the live review-routing seam is
    exercised in tests/test_role_routing_wiring.py)."""
    env = dict(os.environ)
    for flag in ("AR_ROLE_ROUTING", "AR_SCOUT_COUNCIL", "AR_BETA_ACTIVATION"):
        env.pop(flag, None)
    return env


def _run_dispatcher(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_routing_off_env(),
    )


def _run_gate(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GATE), "--root", str(root), "--check"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _run_concurrency_gate(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CONCURRENCY_GATE), "--root", str(root), "--check"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _run_identity_gate(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(IDENTITY_GATE), "--root", str(root), "--check"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _write_worktree(root: Path, task_id: str) -> None:
    worktree = root / ".worktrees" / task_id
    worktree.mkdir(parents=True, exist_ok=True)
    (worktree / ".git").write_text("gitdir: ../../.git/worktrees/test\n", encoding="utf-8")


def _write_routing_work(
    root: Path,
    task_id: str,
    *,
    worker_tier: str = "worker_low",
    triggers: list[str] | None = None,
) -> str:
    task_path = root / "agents" / "lead_engineer" / "tasks" / f"{task_id}.md"
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(
        "\n".join(
            [
                "---",
                f"work_id: {task_id}",
                f"worker_model_tier: {worker_tier}",
                "---",
                "",
            ]
        ),
        encoding="utf-8",
    )
    unit_id = f"UNIT-{task_id}-001"
    unit_rel = f"agents/lead_engineer/tasks/units/{task_id}/{unit_id}.md"
    unit_path = root / unit_rel
    unit_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        f"unit_id: {unit_id}",
        f"task_id: {task_id}",
        f"model_tier: {worker_tier}",
        "target_files:",
        "  - scripts/routing_target.py",
        "escalation_triggers:",
    ]
    lines.extend(f"  - {trigger}" for trigger in (triggers or []))
    lines.extend(["---", ""])
    unit_path.write_text("\n".join(lines), encoding="utf-8")
    return unit_rel


def _install_real_security_gate(root: Path) -> None:
    policy = root / "agents" / "project" / "SECURITY-SERVICE-POLICY.json"
    policy.parent.mkdir(parents=True, exist_ok=True)
    policy.write_text(
        (
            REPO_ROOT
            / "agents"
            / "project"
            / "SECURITY-SERVICE-POLICY.json"
        ).read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    gate = root / "scripts" / "security_service_gate.py"
    gate.parent.mkdir(parents=True, exist_ok=True)
    gate.write_bytes(
        (REPO_ROOT / "scripts" / "security_service_gate.py").read_bytes()
    )


def _write_runtime_config(root: Path, *profiles: str) -> None:
    lines = [
        "schema: agent-runtime-config/v2",
        "project: dispatcher-test",
        "profiles:",
    ]
    lines.extend(f"  - {profile}" for profile in profiles)
    lines.extend(
        [
            "sync:",
            "  mode: check-diff-apply",
            "  allow_silent_overwrite: false",
            "",
        ]
    )
    (root / "agent_runtime.yml").write_text("\n".join(lines), encoding="utf-8")


def test_create_claim_separates_system_identity_from_readable_display_name(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-246")

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-246",
        "--agent-role",
        "lead-engineer",
        "--mode",
        "design",
        "--tag",
        "planning",
        "--tag",
        "no-ssot-write",
        "--now",
        "2026-06-10T14:30:12+09:00",
        "--suffix",
        "a7f3",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    claim = payload["claim"]
    assert claim["agent_role"] == "lead-engineer"
    assert claim["team_id"] == "agent-runtime-core"
    assert claim["agent_instance_id"] == "le-20260610-143012-kst-a7f3"
    assert claim["display_name"] == "lead_engineer@design-01"
    assert claim["callsite_id"] == "terminal:wt-task-ar-246:tab-01"
    assert claim["pane_id"] == "terminal:wt-task-ar-246:tab-01"
    assert claim["mode"] == "design"
    assert claim["phase"] == "claim-created"
    assert claim["progress_pct"] == 0
    assert claim["task_set_id"] == ""
    assert claim["step_index"] == 1
    assert claim["step_total"] == 6
    assert claim["status_text"] == "Claim created"
    assert claim["updated_at"] == "2026-06-10T14:30:12+09:00"
    assert claim["tags"] == ["planning", "no-ssot-write"]
    assert claim["worktree_path"] == ".worktrees/TASK-AR-246"
    assert claim["branch"] == "codex/task-ar-246-design-01"

    claim_path = tmp_path / payload["path"]
    assert claim_path.exists()
    instance_path = tmp_path / "agents" / "runtime" / "instances" / "le-20260610-143012-kst-a7f3.json"
    assert instance_path.exists()
    instance = json.loads(instance_path.read_text(encoding="utf-8"))
    assert instance["schema"] == "agent-runtime-agent-instance/v1"
    assert instance["role"] == "lead-engineer"
    assert instance["team_id"] == "agent-runtime-core"
    assert instance["agent_instance_id"] == "le-20260610-143012-kst-a7f3"
    assert instance["display_name"] == "lead_engineer@design-01"
    assert instance["callsign"] == "lead_engineer@design-01"
    assert instance["callsite_id"] == "terminal:wt-task-ar-246:tab-01"
    assert instance["pane_id"] == "terminal:wt-task-ar-246:tab-01"
    assert instance["spawned_at"] == "2026-06-10T14:30:12+09:00"
    assert instance["spawned_by"] == "task_claim_dispatcher"
    assert instance["task_id"] == "TASK-AR-246"
    assert instance["worktree_path"] == ".worktrees/TASK-AR-246"
    assert instance["claim_refs"] == [payload["path"]]
    assert (tmp_path / claim["handoff_path"]).exists()
    assert (tmp_path / claim["log_path"]).exists()
    event_log = tmp_path / "agents" / "runtime" / "pane_events" / "pane-events.jsonl"
    events = [json.loads(line) for line in event_log.read_text(encoding="utf-8").splitlines()]
    assert events[-1]["event"] == "claim_created"
    assert events[-1]["actor"] == "le-20260610-143012-kst-a7f3"
    assert events[-1]["actor_role"] == "lead-engineer"
    assert events[-1]["agent_instance_id"] == "le-20260610-143012-kst-a7f3"
    assert events[-1]["display_name"] == "lead_engineer@design-01"
    assert events[-1]["callsite_id"] == "terminal:wt-task-ar-246:tab-01"
    assert events[-1]["claim_id"] == claim["claim_id"]
    assert events[-1]["task_id"] == "TASK-AR-246"

    gate = _run_gate(tmp_path)
    assert gate.returncode == 0, gate.stdout
    concurrency_gate = _run_concurrency_gate(tmp_path)
    assert concurrency_gate.returncode == 0, concurrency_gate.stdout
    identity_gate = _run_identity_gate(tmp_path)
    assert identity_gate.returncode == 0, identity_gate.stdout


def test_create_claim_refuses_task_that_is_already_active(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-246")
    first = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-246",
        "--agent-role",
        "lead-engineer",
        "--mode",
        "design",
        "--now",
        "2026-06-10T14:30:12+09:00",
        "--suffix",
        "a7f3",
        "--json",
    )
    assert first.returncode == 0, first.stderr or first.stdout

    second = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-246",
        "--agent-role",
        "qa-reviewer",
        "--mode",
        "review",
        "--now",
        "2026-06-10T14:35:12+09:00",
        "--suffix",
        "b8c4",
        "--json",
    )

    assert second.returncode == 1
    assert "task already has an active claim" in (second.stderr or second.stdout)
    claim_files = list((tmp_path / "agents" / "runtime" / "task_claims").glob("*.json"))
    assert len(claim_files) == 1


def test_projection_emits_full_pointer_agent_record_not_scalar_claim_id(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-246")
    created = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-246",
        "--task-set-id",
        "TASKSET-AR-PROJECTION",
        "--unit-id",
        "UNIT-TASK-AR-246-001",
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-06-10T14:30:12+09:00",
        "--suffix",
        "projection",
        "--json",
    )
    assert created.returncode == 0, created.stderr or created.stdout
    claim = json.loads(created.stdout)["claim"]

    result = _run_dispatcher(tmp_path, "projection", "--claim-id", claim["claim_id"], "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    projection = json.loads(result.stdout)
    assert projection["operation"] == "merge"
    assert projection["task_claim_ref"].endswith(f"{claim['claim_id']}.json")
    assert projection["pointer"]["active_task"] == "TASK-AR-246"
    assert projection["pointer"]["current_agents"] == [{
        "claim_id": claim["claim_id"],
        "agent_role": "lead-engineer",
        "agent_instance_id": claim["agent_instance_id"],
        "display_name": claim["display_name"],
        "callsite_id": claim["callsite_id"],
        "pane_id": claim["pane_id"],
    }]


def test_projection_rejects_released_or_overlay_claims(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-246")
    created = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id", "TASK-AR-246",
        "--agent-role", "lead-engineer",
        "--now", "2026-06-10T14:30:12+09:00",
        "--suffix", "reject-projection",
        "--json",
    )
    assert created.returncode == 0, created.stderr or created.stdout
    claim = json.loads(created.stdout)["claim"]
    path = tmp_path / "agents/runtime/task_claims" / f"{claim['claim_id']}.json"

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["status"] = "released"
    path.write_text(json.dumps(payload), encoding="utf-8")
    inactive = _run_dispatcher(tmp_path, "projection", "--claim-id", claim["claim_id"], "--json")
    assert inactive.returncode == 1
    assert "requires an active worker claim" in inactive.stderr

    payload["status"] = "claimed"
    payload["overlay"] = True
    path.write_text(json.dumps(payload), encoding="utf-8")
    overlay = _run_dispatcher(tmp_path, "projection", "--claim-id", claim["claim_id"], "--json")
    assert overlay.returncode == 1
    assert "does not apply to overlay claim" in overlay.stderr


def test_release_claim_requires_existing_handoff_and_log_files(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-246")
    created = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-246",
        "--agent-role",
        "lead-engineer",
        "--mode",
        "design",
        "--now",
        "2026-06-10T14:30:12+09:00",
        "--suffix",
        "a7f3",
        "--json",
    )
    assert created.returncode == 0, created.stderr or created.stdout
    payload = json.loads(created.stdout)
    claim = payload["claim"]
    (tmp_path / claim["handoff_path"]).unlink()

    failed = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--now",
        "2026-06-10T14:45:12+09:00",
        "--json",
    )

    assert failed.returncode == 1
    assert "handoff/log pointer is missing" in (failed.stderr or failed.stdout)
    saved = json.loads((tmp_path / payload["path"]).read_text(encoding="utf-8"))
    assert saved["status"] == "claimed"


def test_create_claim_accepts_taskset_progress_fields(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-248")

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-248",
        "--task-set-id",
        "TASKSET-AR-PANE-PROGRESS",
        "--agent-role",
        "lead-engineer",
        "--team-id",
        "agent-runtime-core",
        "--mode",
        "implement",
        "--phase",
        "implement",
        "--progress-pct",
        "48",
        "--step-index",
        "3",
        "--step-total",
        "6",
        "--status-text",
        "Rendering task-set progress in UI state",
        "--now",
        "2026-06-10T19:45:00+09:00",
        "--suffix",
        "p2",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]
    assert claim["task_set_id"] == "TASKSET-AR-PANE-PROGRESS"
    assert claim["step_index"] == 3
    assert claim["step_total"] == 6
    assert claim["status_text"] == "Rendering task-set progress in UI state"
    assert claim["updated_at"] == "2026-06-10T19:45:00+09:00"


def test_create_claim_accepts_pm_unit_scope_fields(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-344")

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-344",
        "--task-set-id",
        "TASKSET-AR-PM-OPERATING-SYSTEM",
        "--project-id",
        "PROJECT-AGENT-RUNTIME-PM-OS",
        "--unit-id",
        "UNIT-TASK-AR-344-001",
        "--unit-spec",
        "agents/lead_engineer/tasks/units/TASK-AR-344/UNIT-TASK-AR-344-001.md",
        "--model-tier",
        "worker_standard",
        "--wip-slot",
        "2",
        "--stop-condition",
        "stop_after:UNIT-TASK-AR-344-001:no_adjacent_taskset",
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-06-10T19:45:00+09:00",
        "--suffix",
        "pm1",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]
    assert claim["project_id"] == "PROJECT-AGENT-RUNTIME-PM-OS"
    assert claim["unit_id"] == "UNIT-TASK-AR-344-001"
    assert claim["unit_spec"].endswith("UNIT-TASK-AR-344-001.md")
    assert claim["model_tier"] == "worker_standard"
    assert claim["wip_slot"] == 2
    assert claim["stop_condition"] == "stop_after:UNIT-TASK-AR-344-001:no_adjacent_taskset"


def test_create_claim_derives_low_requested_and_selected_tier_from_unit(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-646"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(tmp_path, task_id)

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:00:00+09:00",
        "--suffix",
        "route-low",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]
    assert claim["requested_model_tier"] == "worker_low"
    assert claim["selected_model_tier"] == "worker_low"
    assert claim["model_tier"] == "worker_low"
    assert claim["provider_tier"] == "haiku"
    assert claim["routing_status"] == "selected"
    assert claim["routing_signals"] == []
    assert claim["actual_model"] is None
    assert claim["actual_model_status"] == "unverified"


def test_create_claim_visibly_escalates_data_integrity_signal(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-647"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(
        tmp_path, task_id, triggers=["data_integrity"]
    )

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:01:00+09:00",
        "--suffix",
        "route-risk",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]
    assert claim["requested_model_tier"] == "worker_low"
    assert claim["selected_model_tier"] == "planner_high"
    assert claim["model_tier"] == "planner_high"
    assert claim["provider_tier"] == "opus"
    assert claim["routing_status"] == "escalated"
    assert claim["routing_signals"] == ["data_integrity"]
    assert claim["routing_unknown_triggers"] == []


def test_create_claim_runs_installed_security_service_gate_before_persistence(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-647"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(tmp_path, task_id)
    unit = tmp_path / unit_rel
    unit.write_text(
        unit.read_text(encoding="utf-8").replace(
            "  - scripts/routing_target.py",
            "  - .env.production",
        ),
        encoding="utf-8",
    )
    _install_real_security_gate(tmp_path)

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:03:00+09:00",
        "--suffix",
        "security-block",
        "--json",
    )

    assert result.returncode == 1
    assert "security-service claim gate refused claim creation" in result.stderr
    assert ".env.production" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_installed_security_profile_refuses_claim_without_unit_spec(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-648"
    _write_worktree(tmp_path, task_id)
    _install_real_security_gate(tmp_path)

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--agent-role",
        "lead-engineer",
        "--target-file",
        ".env.production",
        "--now",
        "2026-07-29T07:04:00+09:00",
        "--suffix",
        "security-no-unit",
        "--json",
    )

    assert result.returncode == 1
    assert "requires registered task and unit identities" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_non_regular_installed_security_gate_refuses_claim(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-648"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(tmp_path, task_id)
    gate = tmp_path / "scripts" / "security_service_gate.py"
    gate.mkdir(parents=True)

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:04:30+09:00",
        "--suffix",
        "security-gate-dir",
        "--json",
    )

    assert result.returncode == 1
    assert "not a regular managed file" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_symlinked_security_gate_parent_refuses_claim(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-648"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(tmp_path, task_id)
    external_scripts = tmp_path / "external-scripts"
    external_scripts.mkdir()
    (external_scripts / "security_service_gate.py").write_text(
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )
    (tmp_path / "scripts").symlink_to(external_scripts, target_is_directory=True)

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:04:40+09:00",
        "--suffix",
        "security-gate-parent-link",
        "--json",
    )

    assert result.returncode == 1
    assert "not a regular managed file" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_drifted_regular_security_gate_refuses_claim(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-648"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(tmp_path, task_id)
    gate = tmp_path / "scripts" / "security_service_gate.py"
    gate.parent.mkdir(parents=True)
    gate.write_text("raise SystemExit(0)\n", encoding="utf-8")

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:04:50+09:00",
        "--suffix",
        "security-gate-drift",
        "--json",
    )

    assert result.returncode == 1
    assert "drifted" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


@pytest.mark.parametrize(
    "profile_evidence",
    ["config-only", "full-runtime", "partial-assets", "lock-only"],
)
def test_selected_security_profile_with_missing_gate_refuses_claim(
    tmp_path: Path,
    profile_evidence: str,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-648"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(tmp_path, task_id)
    unit = tmp_path / unit_rel
    unit.write_text(
        unit.read_text(encoding="utf-8").replace(
            "  - scripts/routing_target.py",
            "  - .env.production",
        ),
        encoding="utf-8",
    )
    if profile_evidence == "config-only":
        _write_runtime_config(tmp_path, "core", "security-service")
    if profile_evidence == "full-runtime":
        _write_runtime_config(tmp_path, "full-runtime")
    if profile_evidence == "partial-assets":
        _install_real_security_gate(tmp_path)
        (tmp_path / ".allimbot.json").write_bytes(
            (
                REPO_ROOT
                / "src"
                / "agent_runtime"
                / "templates"
                / "project"
                / ".allimbot.json"
            ).read_bytes()
        )
        (tmp_path / "scripts" / "security_service_gate.py").unlink()
    if profile_evidence == "lock-only":
        (tmp_path / "agent_runtime.lock.json").write_text(
            json.dumps(
                {
                    "schema": "agent-runtime-lock/v2",
                    "profiles": ["core", "security-service"],
                }
            ),
            encoding="utf-8",
        )

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:04:55+09:00",
        "--suffix",
        f"security-gate-missing-{profile_evidence}",
        "--json",
    )

    assert result.returncode == 1
    assert "selected or partially installed profile" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_malformed_host_config_blocks_at_claim_dispatch_seam(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-649"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(tmp_path, task_id)
    _install_real_security_gate(tmp_path)
    (tmp_path / "agent_runtime.yml").write_text(
        "schema: agent-runtime-config/v2\n"
        "project: broken\n"
        "host:\n"
        "  risk_paths: nope\n",
        encoding="utf-8",
    )

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:05:00+09:00",
        "--suffix",
        "security-bad-config",
        "--json",
    )

    assert result.returncode == 1
    assert "security-service claim gate refused claim creation" in result.stderr
    assert "policy_error" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_unterminated_required_security_metadata_refuses_claim(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-649"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(
        tmp_path,
        task_id,
        triggers=["security"],
    )
    unit = tmp_path / unit_rel
    unit_text = unit.read_text(encoding="utf-8")
    unit_text = unit_text.replace(
        "  - scripts/routing_target.py",
        "  - .env.production",
    ).replace(
        "target_files:",
        'risk_tier: "high\n'
        'security_sensitive: "true\n'
        'approval_required: "true\n'
        "target_files:",
    )
    unit.write_text(
        unit_text + "\n## Security Controls\n\nSynthetic test boundary.\n",
        encoding="utf-8",
    )
    _write_runtime_config(tmp_path, "core", "security-service")
    _install_real_security_gate(tmp_path)

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:05:30+09:00",
        "--suffix",
        "unterminated-security-metadata",
        "--json",
    )

    assert result.returncode == 1
    assert "security-service claim gate refused claim creation" in result.stderr
    assert "policy_error" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_safe_review_document_cannot_substitute_for_requested_unit(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-650"
    _write_worktree(tmp_path, task_id)
    canonical_unit = _write_routing_work(tmp_path, task_id)
    canonical_path = tmp_path / canonical_unit
    canonical_path.write_text(
        canonical_path.read_text(encoding="utf-8").replace(
            "  - scripts/routing_target.py",
            "  - .env.production",
        ),
        encoding="utf-8",
    )
    review = tmp_path / "reviews" / "safe-unit.md"
    review.parent.mkdir(parents=True)
    review.write_text(
        "---\n"
        f"unit_id: UNIT-{task_id}-001\n"
        f"task_id: {task_id}\n"
        "target_files:\n"
        "  - README.md\n"
        "---\n",
        encoding="utf-8",
    )
    _install_real_security_gate(tmp_path)

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        "reviews/safe-unit.md",
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:06:00+09:00",
        "--suffix",
        "security-substitute",
        "--json",
    )

    assert result.returncode == 1
    assert "security-service claim gate refused claim creation" in result.stderr
    assert "policy_error" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_non_regular_host_config_blocks_at_claim_dispatch_seam(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-651"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(tmp_path, task_id)
    _install_real_security_gate(tmp_path)
    (tmp_path / "agent_runtime.yml").mkdir()

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:07:00+09:00",
        "--suffix",
        "security-config-dir",
        "--json",
    )

    assert result.returncode == 1
    assert "security-service claim gate refused claim creation" in result.stderr
    assert "policy_error" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_create_claim_has_zero_security_profile_burden_when_gate_absent(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-648"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(tmp_path, task_id)
    _write_runtime_config(tmp_path, "core # core-only host")

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:04:00+09:00",
        "--suffix",
        "core-no-gate",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_create_claim_keeps_unknown_routing_signal_visible(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-648"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(
        tmp_path, task_id, triggers=["future_unregistered_risk"]
    )

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T07:02:00+09:00",
        "--suffix",
        "route-unknown",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]
    assert claim["routing_status"] == "unverified"
    assert claim["routing_unknown_triggers"] == ["future_unregistered_risk"]
    assert claim["actual_model"] is None


def test_create_claim_rejects_missing_worktree(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-246",
        "--agent-role",
        "lead-engineer",
    )

    assert result.returncode == 1
    assert "task worktree is not ready" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_create_claim_refuses_duplicate_active_taskset(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-248")
    _write_worktree(tmp_path, "TASK-AR-249")
    first = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-248",
        "--task-set-id",
        "TASKSET-AR-PANE-PROGRESS",
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-06-10T19:45:00+09:00",
        "--suffix",
        "p2",
        "--json",
    )
    assert first.returncode == 0, first.stderr or first.stdout

    second = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-249",
        "--task-set-id",
        "TASKSET-AR-PANE-PROGRESS",
        "--agent-role",
        "qa-reviewer",
        "--now",
        "2026-06-10T19:46:00+09:00",
        "--suffix",
        "p3",
        "--json",
    )

    assert second.returncode == 1
    assert "task set already has an active claim" in second.stderr


def test_create_claim_rejects_intersecting_footprint_listing_conflicting_claim(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-501")
    _write_worktree(tmp_path, "TASK-AR-502")
    first = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-501",
        "--agent-role",
        "lead-engineer",
        "--target-file",
        "scripts/shared.py",
        "--target-file",
        "docs/notes.md",
        "--now",
        "2026-06-13T10:00:00+09:00",
        "--suffix",
        "fp1",
        "--json",
    )
    assert first.returncode == 0, first.stderr or first.stdout
    first_claim = json.loads(first.stdout)["claim"]
    assert first_claim["target_files"] == ["scripts/shared.py", "docs/notes.md"]

    second = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-502",
        "--agent-role",
        "qa-reviewer",
        "--target-file",
        "scripts/shared.py",
        "--now",
        "2026-06-13T10:05:00+09:00",
        "--suffix",
        "fp2",
        "--json",
    )

    assert second.returncode == 1
    assert "footprint conflict with active claims" in second.stderr
    assert first_claim["claim_id"] in second.stderr
    claim_files = list((tmp_path / "agents" / "runtime" / "task_claims").glob("*.json"))
    assert len(claim_files) == 1


def test_create_claims_with_disjoint_footprints_coexist(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    footprints = {
        "TASK-AR-501": "scripts/alpha.py",
        "TASK-AR-502": "scripts/beta.py",
        "TASK-AR-503": "docs/gamma.md",
    }
    for index, (task_id, target) in enumerate(sorted(footprints.items()), start=1):
        _write_worktree(tmp_path, task_id)
        result = _run_dispatcher(
            tmp_path,
            "create",
            "--task-id",
            task_id,
            "--agent-role",
            "lead-engineer",
            "--target-file",
            target,
            "--now",
            f"2026-06-13T10:0{index}:00+09:00",
            "--suffix",
            f"dj{index}",
            "--json",
        )
        assert result.returncode == 0, result.stderr or result.stdout
    claim_files = list((tmp_path / "agents" / "runtime" / "task_claims").glob("*.json"))
    assert len(claim_files) == len(footprints)


def test_create_claim_rejects_glob_prefix_footprint_overlap(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-501")
    _write_worktree(tmp_path, "TASK-AR-502")
    first = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-501",
        "--agent-role",
        "lead-engineer",
        "--target-file",
        "scripts/**",
        "--now",
        "2026-06-13T11:00:00+09:00",
        "--suffix",
        "gl1",
        "--json",
    )
    assert first.returncode == 0, first.stderr or first.stdout
    first_claim = json.loads(first.stdout)["claim"]

    second = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-502",
        "--agent-role",
        "qa-reviewer",
        "--target-file",
        "scripts/sub/module.py",
        "--now",
        "2026-06-13T11:05:00+09:00",
        "--suffix",
        "gl2",
        "--json",
    )

    assert second.returncode == 1
    assert "footprint conflict with active claims" in second.stderr
    assert first_claim["claim_id"] in second.stderr


def test_create_claim_footprint_less_legacy_claim_does_not_block(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-501")
    _write_worktree(tmp_path, "TASK-AR-502")
    legacy = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-501",
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-06-13T12:00:00+09:00",
        "--suffix",
        "lg1",
        "--json",
    )
    assert legacy.returncode == 0, legacy.stderr or legacy.stdout
    assert "footprint-less" in legacy.stderr
    legacy_claim = json.loads(legacy.stdout)["claim"]
    assert legacy_claim["target_files"] == []

    second = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-502",
        "--agent-role",
        "qa-reviewer",
        "--target-file",
        "scripts/shared.py",
        "--now",
        "2026-06-13T12:05:00+09:00",
        "--suffix",
        "lg2",
        "--json",
    )

    assert second.returncode == 0, second.stderr or second.stdout
    assert "footprint-less" in second.stderr
    assert legacy_claim["claim_id"] in second.stderr
    claim_files = list((tmp_path / "agents" / "runtime" / "task_claims").glob("*.json"))
    assert len(claim_files) == 2


def test_create_claim_derives_target_files_from_unit_spec(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-503")
    unit_rel = "agents/lead_engineer/tasks/units/TASK-AR-503/UNIT-TASK-AR-503-001.md"
    unit_path = tmp_path / unit_rel
    unit_path.parent.mkdir(parents=True, exist_ok=True)
    unit_path.write_text(
        "\n".join(
            [
                "---",
                "unit_id: UNIT-TASK-AR-503-001",
                "task_id: TASK-AR-503",
                "status: worker_ready",
                "target_files:",
                "  - scripts/unit_target.py",
                "  - docs/unit_target.md",
                "---",
                "",
                "## Context",
                "",
                "Unit spec for footprint derivation.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-503",
        "--agent-role",
        "lead-engineer",
        "--unit-spec",
        unit_rel,
        "--now",
        "2026-06-13T13:00:00+09:00",
        "--suffix",
        "us1",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]
    assert claim["target_files"] == ["scripts/unit_target.py", "docs/unit_target.md"]


def test_explicit_target_files_are_unioned_with_registered_unit_footprint(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    task_id = "TASK-AR-504"
    _write_worktree(tmp_path, task_id)
    unit_rel = _write_routing_work(tmp_path, task_id)

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--unit-id",
        f"UNIT-{task_id}-001",
        "--unit-spec",
        unit_rel,
        "--agent-role",
        "lead-engineer",
        "--target-file",
        "README.md",
        "--now",
        "2026-07-29T07:06:00+09:00",
        "--suffix",
        "union-footprint",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]
    assert claim["target_files"] == ["README.md", "scripts/routing_target.py"]


def test_create_claim_normalizes_new_targets_and_surfaces_matching_compound(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    _write_worktree(tmp_path, "TASK-AR-645")
    task_path = tmp_path / "agents/lead_engineer/tasks/TASK-AR-645.md"
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(
        "---\nwork_id: TASK-AR-645\ndefect_signatures:\n"
        "  - claim lookup omitted\n---\n",
        encoding="utf-8",
    )
    unit_rel = (
        "agents/lead_engineer/tasks/units/TASK-AR-645/"
        "UNIT-TASK-AR-645-001.md"
    )
    unit_path = tmp_path / unit_rel
    unit_path.parent.mkdir(parents=True, exist_ok=True)
    unit_path.write_text(
        "---\nunit_id: UNIT-TASK-AR-645-001\ntask_id: TASK-AR-645\n"
        "status: worker_ready\ntarget_files:\n"
        "  - new:src/agent_runtime/knowledge_records.py\n"
        "  - scripts/task_claim_dispatcher.py\n"
        "defect_signatures:\n"
        "  - claim lookup omitted\n---\n",
        encoding="utf-8",
    )
    _path, prior = knowledge_records.create_record(
        tmp_path,
        work_ids=["TASK-AR-500"],
        defect_signatures=["claim lookup omitted"],
        title="Search before claim",
        summary="A worker repeated a known error.",
        cause="The dispatcher did not search.",
        prevention="Search before persistence.",
        source_refs=["reviews/source.md"],
        prevention_refs=["scripts/task_claim_dispatcher.py"],
        verification_refs=["reviews/verify.json"],
        created_at="2026-07-28T12:00:00+09:00",
    )

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-645",
        "--agent-role",
        "lead-engineer",
        "--unit-id",
        "UNIT-TASK-AR-645-001",
        "--unit-spec",
        unit_rel,
        "--now",
        "2026-07-29T04:20:00+09:00",
        "--suffix",
        "lookup",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]
    assert claim["target_files"] == [
        "src/agent_runtime/knowledge_records.py",
        "scripts/task_claim_dispatcher.py",
    ]
    assert claim["defect_signatures"] == [
        knowledge_records.normalize_signature("claim lookup omitted")
    ]
    assert claim["knowledge_lookup"] == {"status": "matched", "match_count": 1}
    assert claim["knowledge_matches"][0]["id"] == prior["id"]
    assert "before claim persistence" in result.stderr


def test_create_claim_refuses_malformed_canonical_compound_before_persistence(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n", encoding="utf-8"
    )
    _write_worktree(tmp_path, "TASK-AR-646")
    record_dir = knowledge_records.records_dir(tmp_path)
    record_dir.mkdir(parents=True)
    (record_dir / "COMPOUND-20260729-000000-bad-000000000000.json").write_text(
        '{"schema":"wrong"}\n', encoding="utf-8"
    )

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-646",
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-07-29T04:21:00+09:00",
        "--suffix",
        "bad-record",
        "--json",
    )

    assert result.returncode == 1
    assert "compound knowledge lookup failed before claim persistence" in result.stderr
    claims = tmp_path / "agents/runtime/task_claims"
    assert not claims.exists() or not list(claims.glob("*.json"))


def _create_release_candidate(tmp_path: Path, *, task_id: str = "TASK-AR-507", suffix: str = "cv1") -> dict:
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, task_id)
    created = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        task_id,
        "--agent-role",
        "lead-engineer",
        "--mode",
        "implement",
        "--now",
        "2026-06-13T09:00:00+09:00",
        "--suffix",
        suffix,
        "--json",
    )
    assert created.returncode == 0, created.stderr or created.stdout
    return json.loads(created.stdout)


def _write_evidence(tmp_path: Path, rel: str = "agents/runtime/task_claims/evidence/W4B-VERIFICATION.md") -> str:
    evidence = tmp_path / rel
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text("# W4b verification\n\n- result: pass\n", encoding="utf-8")
    return rel


def test_release_without_verifier_is_refused(tmp_path: Path):
    payload = _create_release_candidate(tmp_path)
    claim = payload["claim"]
    evidence_rel = _write_evidence(tmp_path)

    refused = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verification-evidence",
        evidence_rel,
        "--now",
        "2026-06-13T10:00:00+09:00",
        "--json",
    )

    assert refused.returncode == 1
    assert "cross-verification required" in refused.stderr
    assert "--verified-by" in refused.stderr
    saved = json.loads((tmp_path / payload["path"]).read_text(encoding="utf-8"))
    assert saved["status"] == "claimed"
    assert "verified_by" not in saved


def test_release_refuses_worker_self_verification_listing_both_ids(tmp_path: Path):
    payload = _create_release_candidate(tmp_path)
    claim = payload["claim"]
    worker_id = claim["agent_instance_id"]
    evidence_rel = _write_evidence(tmp_path)

    refused = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verified-by",
        worker_id,
        "--verifier-role",
        "lead-engineer",
        "--verification-evidence",
        evidence_rel,
        "--now",
        "2026-06-13T10:00:00+09:00",
        "--json",
    )

    assert refused.returncode == 1
    assert "cross-verification violation" in refused.stderr
    assert f"verified_by={worker_id}" in refused.stderr
    assert f"worker agent_instance_id={worker_id}" in refused.stderr
    saved = json.loads((tmp_path / payload["path"]).read_text(encoding="utf-8"))
    assert saved["status"] == "claimed"


def test_release_with_distinct_verifier_records_fields_and_pane_event(tmp_path: Path):
    payload = _create_release_candidate(tmp_path)
    claim = payload["claim"]
    evidence_rel = _write_evidence(tmp_path)

    released = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verified-by",
        "qa-20260613-101500-kst-w4b1",
        "--verifier-role",
        "qa-reviewer",
        "--verification-evidence",
        evidence_rel,
        "--now",
        "2026-06-13T10:15:00+09:00",
        "--json",
    )

    assert released.returncode == 0, released.stderr or released.stdout
    saved = json.loads((tmp_path / payload["path"]).read_text(encoding="utf-8"))
    assert saved["status"] == "released"
    assert saved["released_at"] == "2026-06-13T10:15:00+09:00"
    assert saved["verified_by"] == "qa-20260613-101500-kst-w4b1"
    assert saved["verifier_role"] == "qa-reviewer"
    assert saved["verification_evidence"] == evidence_rel
    event_log = tmp_path / "agents" / "runtime" / "pane_events" / "pane-events.jsonl"
    events = [json.loads(line) for line in event_log.read_text(encoding="utf-8").splitlines()]
    release_event = events[-1]
    assert release_event["event"] == "claim_released"
    assert release_event["claim_id"] == claim["claim_id"]
    assert release_event["actor"] == claim["agent_instance_id"]
    assert release_event["verified_by"] == "qa-20260613-101500-kst-w4b1"
    assert release_event["verifier_role"] == "qa-reviewer"


def test_release_requires_evidence_ref_by_default(tmp_path: Path):
    payload = _create_release_candidate(tmp_path)
    claim = payload["claim"]

    refused = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verified-by",
        "qa-20260613-101500-kst-w4b1",
        "--verifier-role",
        "qa-reviewer",
        "--now",
        "2026-06-13T10:15:00+09:00",
        "--json",
    )

    assert refused.returncode == 1
    assert "verification evidence required" in refused.stderr
    saved = json.loads((tmp_path / payload["path"]).read_text(encoding="utf-8"))
    assert saved["status"] == "claimed"


def test_release_refuses_nonexistent_evidence_ref(tmp_path: Path):
    payload = _create_release_candidate(tmp_path)
    claim = payload["claim"]

    refused = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verified-by",
        "qa-20260613-101500-kst-w4b1",
        "--verifier-role",
        "qa-reviewer",
        "--verification-evidence",
        "agents/runtime/task_claims/evidence/does-not-exist.md",
        "--now",
        "2026-06-13T10:15:00+09:00",
        "--json",
    )

    assert refused.returncode == 1
    assert "verification evidence not found" in refused.stderr


def test_release_allow_missing_evidence_escape_prints_loud_warning(tmp_path: Path):
    payload = _create_release_candidate(tmp_path)
    claim = payload["claim"]

    released = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verified-by",
        "qa-20260613-101500-kst-w4b1",
        "--verifier-role",
        "qa-reviewer",
        "--allow-missing-evidence",
        "--now",
        "2026-06-13T10:15:00+09:00",
        "--json",
    )

    assert released.returncode == 0, released.stderr or released.stdout
    assert "WARNING" in released.stderr
    assert "--allow-missing-evidence" in released.stderr
    saved = json.loads((tmp_path / payload["path"]).read_text(encoding="utf-8"))
    assert saved["status"] == "released"
    assert saved["verified_by"] == "qa-20260613-101500-kst-w4b1"
    assert saved["verification_evidence"] == ""


def test_release_still_refuses_self_verification_with_missing_evidence_escape(tmp_path: Path):
    payload = _create_release_candidate(tmp_path)
    claim = payload["claim"]
    worker_id = claim["agent_instance_id"]

    refused = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verified-by",
        worker_id,
        "--verifier-role",
        "lead-engineer",
        "--allow-missing-evidence",
        "--now",
        "2026-06-13T10:15:00+09:00",
        "--json",
    )

    assert refused.returncode == 1
    assert "cross-verification violation" in refused.stderr


def test_legacy_released_claims_without_verifier_fields_pass_check_gates(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    claim_dir.mkdir(parents=True, exist_ok=True)
    legacy = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": "CLAIM-20260601-090000-task-ar-400-old1",
        "task_id": "TASK-AR-400",
        "agent_role": "lead-engineer",
        "team_id": "agent-runtime-core",
        "agent_instance_id": "le-20260601-090000-kst-old1",
        "display_name": "lead_engineer@implement-01",
        "callsite_id": "terminal:wt-task-ar-400:tab-01",
        "pane_id": "terminal:wt-task-ar-400:tab-01",
        "mode": "implement",
        "status": "released",
        "task_set_id": "",
        "worktree_path": ".worktrees/TASK-AR-400",
        "branch": "codex/task-ar-400-implement-01",
        "claimed_at": "2026-06-01T09:00:00+09:00",
        "released_at": "2026-06-01T12:00:00+09:00",
        "last_heartbeat": "2026-06-01T12:00:00+09:00",
        "updated_at": "2026-06-01T12:00:00+09:00",
        "expires_at": "2026-06-01T09:30:00+09:00",
        "handoff_path": "agents/runtime/task_claims/CLAIM-20260601-090000-task-ar-400-old1.handoff.md",
        "log_path": "agents/runtime/task_claims/CLAIM-20260601-090000-task-ar-400-old1.log.md",
        "tags": [],
        "target_files": [],
    }
    (claim_dir / f"{legacy['claim_id']}.json").write_text(
        json.dumps(legacy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    gate = _run_gate(tmp_path)
    assert gate.returncode == 0, gate.stdout
    concurrency_gate = _run_concurrency_gate(tmp_path)
    assert concurrency_gate.returncode == 0, concurrency_gate.stdout
    identity_gate = _run_identity_gate(tmp_path)
    assert identity_gate.returncode == 0, identity_gate.stdout


def test_create_claim_rejects_invalid_progress_and_step_state(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")

    bad_progress = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-249",
        "--agent-role",
        "lead-engineer",
        "--progress-pct",
        "104",
    )
    bad_step = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-249",
        "--agent-role",
        "lead-engineer",
        "--step-index",
        "7",
        "--step-total",
        "6",
    )
    bad_done = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-249",
        "--agent-role",
        "lead-engineer",
        "--phase",
        "completed",
        "--step-index",
        "2",
        "--step-total",
        "6",
    )

    assert bad_progress.returncode == 1
    assert "progress_pct must be between 0 and 100" in bad_progress.stderr
    assert bad_step.returncode == 1
    assert "step_index must be between 1 and step_total" in bad_step.stderr
    assert bad_done.returncode == 1
    assert "completion phase requires step_index to equal step_total" in bad_done.stderr


def test_create_claim_records_active_scope_boundary(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-328")

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-328",
        "--task-set-id",
        "TASKSET-AR-UI-UX-V2",
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-06-13T09:00:00+09:00",
        "--suffix",
        "sc1",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]
    # Active scope defaults to the task_set_id so the boundary guard has a
    # recorded scope to enforce against.
    assert claim["active_scope"] == "TASKSET-AR-UI-UX-V2"
    assert claim["scope_transition_approved"] is False


def test_release_with_taskset_completed_phase_emits_completion_event(tmp_path: Path):
    payload = _create_release_candidate(tmp_path, task_id="TASK-AR-329", suffix="tc1")
    claim = payload["claim"]
    evidence_rel = _write_evidence(tmp_path)

    # Mark the claim's scope + completion phase before release so the dispatcher
    # emits the taskset.completed boundary signal.
    claim_path = tmp_path / payload["path"]
    saved = json.loads(claim_path.read_text(encoding="utf-8"))
    saved["active_scope"] = "TASKSET-AR-UI-UX-V2"
    saved["phase"] = "taskset-completed"
    saved["progress_pct"] = 100
    claim_path.write_text(json.dumps(saved), encoding="utf-8")

    released = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verified-by",
        "qa-20260613-101500-kst-w4b1",
        "--verifier-role",
        "qa-reviewer",
        "--verification-evidence",
        evidence_rel,
        "--now",
        "2026-06-13T10:15:00+09:00",
        "--json",
    )

    assert released.returncode == 0, released.stderr or released.stdout
    event_log = tmp_path / "agents" / "runtime" / "pane_events" / "pane-events.jsonl"
    events = [json.loads(line) for line in event_log.read_text(encoding="utf-8").splitlines()]
    completed = [event for event in events if event["event"] == "taskset.completed"]
    assert completed, "expected a taskset.completed event to be emitted"
    event = completed[-1]
    assert event["task_set_id"] == "TASKSET-AR-UI-UX-V2"
    assert event["claim_id"] == claim["claim_id"]
    assert "stop and report" in event["message"]


def test_release_without_completion_phase_emits_no_completion_event(tmp_path: Path):
    payload = _create_release_candidate(tmp_path, task_id="TASK-AR-330", suffix="nc1")
    claim = payload["claim"]
    evidence_rel = _write_evidence(tmp_path)

    released = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verified-by",
        "qa-20260613-101500-kst-w4b1",
        "--verifier-role",
        "qa-reviewer",
        "--verification-evidence",
        evidence_rel,
        "--now",
        "2026-06-13T10:15:00+09:00",
        "--json",
    )

    assert released.returncode == 0, released.stderr or released.stdout
    event_log = tmp_path / "agents" / "runtime" / "pane_events" / "pane-events.jsonl"
    events = [json.loads(line) for line in event_log.read_text(encoding="utf-8").splitlines()]
    assert not [event for event in events if event["event"] == "taskset.completed"]
