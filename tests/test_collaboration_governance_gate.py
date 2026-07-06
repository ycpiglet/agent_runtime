from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "collaboration_governance_gate.py"


def _run_gate(root: Path, *, now: str = "2026-06-10T22:30:00+09:00") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), "--now", now, "--check"],
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


def _write_json(path: Path, payload: dict) -> None:
    _write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _policy(
    *,
    minimum_roles: dict[str, int] | None = None,
    monitored_roles: list[str] | None = None,
    monitored_role_evidence: dict | None = None,
    artifacts: list[str] | None = None,
    capabilities: dict[str, list[str]] | None = None,
) -> dict:
    return {
        "schema": "agent-runtime-collaboration-governance/v1",
        "version": 1,
        "min_claims_for_role_coverage": 1,
        "minimum_claim_roles": minimum_roles if minimum_roles is not None else {},
        "monitored_roles": monitored_roles if monitored_roles is not None else [],
        "monitored_role_evidence": monitored_role_evidence if monitored_role_evidence is not None else {},
        "required_review_artifacts": artifacts if artifacts is not None else [],
        "required_root_capabilities": capabilities if capabilities is not None else {},
        "lifecycle_thresholds": {
            "future_heartbeat_watch_minutes": 5,
            "released_claim_expected_phase": "taskset-completed",
            "released_claim_expected_progress_pct": 100,
        },
        "waiver_contract": {
            "directory": "agents/project/waivers",
            "schema": "agent-runtime-collaboration-waiver/v1",
            "required_fields": [
                "schema",
                "id",
                "subjects",
                "reason",
                "approved_by",
                "created_at",
                "expires_at",
                "mitigation",
            ],
        },
    }


def _claim(role: str = "qa", *, status: str = "claimed", claim_id: str = "CLAIM-1") -> dict:
    return {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": claim_id,
        "task_id": "TASK-1",
        "agent_role": role,
        "team_id": "agent-runtime-core",
        "agent_instance_id": f"{role}-1",
        "display_name": f"{role}@test-01",
        "callsite_id": f"terminal:{role}",
        "pane_id": f"terminal:{role}",
        "status": status,
        "phase": "claim-created",
        "progress_pct": 0,
        "status_text": "test claim",
        "worktree_path": ".worktrees/TASK-1",
        "branch": "codex/task-1",
        "claimed_at": "2026-06-10T22:00:00+09:00",
        "last_heartbeat": "2026-06-10T22:00:00+09:00",
        "handoff_path": "agents/runtime/task_claims/CLAIM-1.handoff.md",
        "log_path": "agents/runtime/task_claims/CLAIM-1.log.md",
    }


def test_collaboration_governance_gate_blocks_missing_policy(tmp_path: Path) -> None:
    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "policy:missing-or-invalid" in result.stdout


def test_collaboration_governance_gate_blocks_unwaived_missing_role_artifact_and_capability(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "agents" / "project" / "COLLABORATION-GOVERNANCE.json",
        _policy(
            minimum_roles={"scribe": 1},
            artifacts=["RETRO"],
            capabilities={"scribe": ["scripts/scribe_due.py"]},
        ),
    )
    _write_json(tmp_path / "agents" / "runtime" / "task_claims" / "CLAIM-1.json", _claim("qa"))

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "role-usage:scribe" in result.stdout
    assert "artifact:RETRO" in result.stdout
    assert "root-capability:scribe" in result.stdout


def test_collaboration_governance_gate_accepts_explicit_unexpired_waivers(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "agents" / "project" / "COLLABORATION-GOVERNANCE.json",
        _policy(
            minimum_roles={"scribe": 1},
            artifacts=["RETRO"],
            capabilities={"scribe": ["scripts/scribe_due.py"]},
        ),
    )
    _write_json(tmp_path / "agents" / "runtime" / "task_claims" / "CLAIM-1.json", _claim("qa"))
    _write_json(
        tmp_path / "agents" / "project" / "waivers" / "WAIVER-test.json",
        {
            "schema": "agent-runtime-collaboration-waiver/v1",
            "id": "WAIVER-test",
            "subjects": ["role-usage:scribe", "artifact:RETRO", "root-capability:scribe"],
            "reason": "test waiver",
            "approved_by": "owner",
            "created_at": "2026-06-10T22:00:00+09:00",
            "expires_at": "2026-06-11T22:00:00+09:00",
            "mitigation": "promote root runtime script",
        },
    )

    result = _run_gate(tmp_path)

    assert result.returncode == 0
    assert "collaboration-governance-gate: pass" in result.stdout
    assert "waived=3" in result.stdout
    assert "waiver=WAIVER-test" in result.stdout


def test_collaboration_governance_gate_blocks_waiver_missing_lifecycle_metadata(tmp_path: Path) -> None:
    _write_json(tmp_path / "agents" / "project" / "COLLABORATION-GOVERNANCE.json", _policy())
    _write_json(
        tmp_path / "agents" / "project" / "waivers" / "WAIVER-bad.json",
        {
            "schema": "agent-runtime-collaboration-waiver/v1",
            "id": "WAIVER-bad",
            "subjects": ["role-usage:scribe"],
            "reason": "missing metadata",
            "created_at": "2026-06-10T22:00:00+09:00",
        },
    )

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "waiver:invalid" in result.stdout
    assert "approved_by" in result.stdout
    assert "expires_at" in result.stdout
    assert "mitigation" in result.stdout


def test_collaboration_governance_gate_reports_lifecycle_watch_without_blocking(tmp_path: Path) -> None:
    _write_json(tmp_path / "agents" / "project" / "COLLABORATION-GOVERNANCE.json", _policy())
    active = _claim("lead-engineer", claim_id="CLAIM-active")
    active["last_heartbeat"] = "2026-06-10T23:00:00+09:00"
    active["worktree_path"] = ".worktrees/MISSING"
    released = _claim("qa", status="released", claim_id="CLAIM-released")
    released["phase"] = "claim-released"
    released["progress_pct"] = 80
    _write_json(tmp_path / "agents" / "runtime" / "task_claims" / "CLAIM-active.json", active)
    _write_json(tmp_path / "agents" / "runtime" / "task_claims" / "CLAIM-released.json", released)

    result = _run_gate(tmp_path)

    assert result.returncode == 0
    assert "lifecycle:future-heartbeat:CLAIM-active" in result.stdout
    assert "lifecycle:active-worktree-missing:CLAIM-active" in result.stdout
    assert "lifecycle:released-claim-incomplete:CLAIM-released" in result.stdout
    assert "watch=3" in result.stdout


def test_monitored_role_accepts_configured_artifact_evidence(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "agents" / "project" / "COLLABORATION-GOVERNANCE.json",
        _policy(
            monitored_roles=["council", "skeptic", "progress-scout"],
            monitored_role_evidence={
                "council": [{"path_glob": "reviews/COUNCIL-*.md", "contains": ["type: council", "council"]}],
                "skeptic": [{"path_glob": "reviews/COUNCIL-*.md", "contains": ["skeptic"]}],
            },
        ),
    )
    _write_json(tmp_path / "agents" / "runtime" / "task_claims" / "CLAIM-1.json", _claim("qa"))
    (tmp_path / ".worktrees" / "TASK-1").mkdir(parents=True)
    _write(
        tmp_path / "reviews" / "COUNCIL-2026-06-18-example.md",
        "---\ntype: council\n---\n# Council\n\n| role | verdict |\n| --- | --- |\n| skeptic | hold |\n",
    )

    result = _run_gate(tmp_path)

    assert result.returncode == 0
    assert "role-monitor:council" not in result.stdout
    assert "role-monitor:skeptic" not in result.stdout
    assert "role-monitor:progress-scout" in result.stdout
    assert "watch=1" in result.stdout


def test_monitored_role_artifact_must_match_required_tokens(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "agents" / "project" / "COLLABORATION-GOVERNANCE.json",
        _policy(
            monitored_roles=["skeptic"],
            monitored_role_evidence={
                "skeptic": [{"path_glob": "reviews/COUNCIL-*.md", "contains": ["skeptic"]}],
            },
        ),
    )
    _write_json(tmp_path / "agents" / "runtime" / "task_claims" / "CLAIM-1.json", _claim("qa"))
    _write(tmp_path / "reviews" / "COUNCIL-2026-06-18-example.md", "---\ntype: council\n---\n# Council\n")

    result = _run_gate(tmp_path)

    assert result.returncode == 0
    assert "role-monitor:skeptic" in result.stdout
    assert "no claim or configured artifact evidence" in result.stdout


def test_owner_governance_runs_collaboration_governance_gate() -> None:
    root_gate = (REPO_ROOT / "scripts" / "owner_governance_gate.py").read_text(encoding="utf-8")
    template_gate = (
        REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "owner_governance_gate.py"
    ).read_text(encoding="utf-8")

    assert "collaboration_governance_gate.py" in root_gate
    assert "collaboration_governance_gate.py" in template_gate
