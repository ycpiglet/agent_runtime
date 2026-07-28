from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


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
