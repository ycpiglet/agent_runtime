from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "rbac_write_gate.py"


def _run_gate(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), "--check"],
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


def _append_event(root: Path, payload: dict) -> None:
    path = root / "agents" / "runtime" / "pane_events" / "pane-events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _claim(
    *,
    claim_id: str,
    role: str,
    task_id: str,
    instance_id: str,
    display_name: str,
    callsite_id: str,
) -> dict:
    return {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": claim_id,
        "task_id": task_id,
        "task_set_id": "TASKSET-AR-VISION-GAP-CLOSURE",
        "agent_role": role,
        "team_id": "agent-runtime-core",
        "agent_instance_id": instance_id,
        "display_name": display_name,
        "callsite_id": callsite_id,
        "pane_id": callsite_id,
        "status": "claimed",
        "phase": "taskset-claimed",
        "progress_pct": 0,
        "status_text": f"{role} working {task_id}",
        "worktree_path": f".worktrees/{task_id}",
        "branch": f"codex/{task_id.lower()}",
        "claimed_at": "2026-06-12T00:10:00+09:00",
        "last_heartbeat": "2026-06-12T00:10:00+09:00",
        "handoff_path": f"agents/runtime/task_claims/{claim_id}.handoff.md",
        "log_path": f"agents/runtime/task_claims/{claim_id}.log.md",
    }


def _write_claim(root: Path, payload: dict) -> None:
    _write_json(root / "agents" / "runtime" / "task_claims" / f"{payload['claim_id']}.json", payload)


def _write_pointer(root: Path, claims: list[dict]) -> None:
    lines = [
        "schema: agent-runtime-next-session-pointer/v1",
        "active_work:",
        "  current_agents:",
    ]
    for claim in claims:
        lines.extend(
            [
                f"    - claim_id: {claim['claim_id']}",
                f"      agent_role: {claim['agent_role']}",
                f"      agent_instance_id: {claim['agent_instance_id']}",
                f"      display_name: {claim['display_name']}",
                f"      callsite_id: {claim['callsite_id']}",
            ]
        )
    _write(root / "agents" / "project" / "NEXT-SESSION-POINTER.yml", "\n".join(lines) + "\n")


def _write_empty_pointer(root: Path) -> None:
    _write(
        root / "agents" / "project" / "NEXT-SESSION-POINTER.yml",
        "\n".join(
            [
                "schema: agent-runtime-next-session-pointer/v1",
                "active_work:",
                "  current_agents: []",
            ]
        )
        + "\n",
    )


def _pane_started(root: Path, claim: dict, seq: int) -> None:
    _append_event(
        root,
        {
            "schema": "agent-runtime-pane-event/v1",
            "seq": seq,
            "ts": "2026-06-12T00:10:00+09:00",
            "event": "pane_started",
            "actor": claim["agent_role"],
            "task_id": claim["task_id"],
            "task_set_id": claim["task_set_id"],
            "claim_id": claim["claim_id"],
            "agent_instance_id": claim["agent_instance_id"],
            "callsite_id": claim["callsite_id"],
        },
    )


def _create_claim_with_dispatcher(root: Path, claim: dict) -> dict:
    worktree = root / str(claim["worktree_path"])
    worktree.mkdir(parents=True, exist_ok=True)
    (worktree / ".git").write_text("gitdir: ../../.git/worktrees/test\n", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_claim_dispatcher.py"),
            "--root",
            str(root),
            "create",
            "--task-id",
            str(claim["task_id"]),
            "--task-set-id",
            str(claim["task_set_id"]),
            "--agent-role",
            str(claim["agent_role"]),
            "--team-id",
            str(claim["team_id"]),
            "--mode",
            "vision-gap-closure",
            "--phase",
            "taskset-claimed",
            "--progress-pct",
            "0",
            "--step-index",
            "1",
            "--step-total",
            "10",
            "--status-text",
            str(claim["status_text"]),
            "--worktree-path",
            str(claim["worktree_path"]),
            "--branch",
            str(claim["branch"]),
            "--claim-id",
            str(claim["claim_id"]),
            "--agent-instance-id",
            str(claim["agent_instance_id"]),
            "--display-name",
            str(claim["display_name"]),
            "--callsite-id",
            str(claim["callsite_id"]),
            "--pane-id",
            str(claim["pane_id"]),
            "--now",
            "2026-06-12T00:10:00+09:00",
            "--allow-parallel-task-set",
            "--json",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    return payload["claim"]


def test_rbac_gate_accepts_three_distinct_active_instances(tmp_path: Path) -> None:
    claim_specs = [
        _claim(
            claim_id="CLAIM-lead",
            role="lead-engineer",
            task_id="TASK-AR-312",
            instance_id="lead-001",
            display_name="lead_engineer@vision-gap-01",
            callsite_id="terminal:lead",
        ),
        _claim(
            claim_id="CLAIM-qa",
            role="qa",
            task_id="TASK-AR-313",
            instance_id="qa-001",
            display_name="qa@vision-gap-01",
            callsite_id="terminal:qa",
        ),
        _claim(
            claim_id="CLAIM-doc",
            role="doc-steward",
            task_id="TASK-AR-314",
            instance_id="doc-001",
            display_name="doc_steward@vision-gap-01",
            callsite_id="terminal:doc",
        ),
    ]
    claims = [_create_claim_with_dispatcher(tmp_path, claim) for claim in claim_specs]
    _write_pointer(tmp_path, claims)

    result = _run_gate(tmp_path)

    assert result.returncode == 0
    assert "rbac-write-gate: pass" in result.stdout
    assert "findings=0" in result.stdout


def test_rbac_gate_blocks_qa_release_doc_write_attempt(tmp_path: Path) -> None:
    claim = _claim(
        claim_id="CLAIM-qa",
        role="qa",
        task_id="TASK-AR-312",
        instance_id="qa-001",
        display_name="qa@vision-gap-01",
        callsite_id="terminal:qa",
    )
    _write_claim(tmp_path, claim)
    _write_pointer(tmp_path, [claim])
    _pane_started(tmp_path, claim, 1)
    _append_event(
        tmp_path,
        {
            "schema": "agent-runtime-pane-event/v1",
            "seq": 2,
            "ts": "2026-06-12T00:11:00+09:00",
            "event": "role_write_attempted",
            "actor_role": "qa",
            "claim_id": "CLAIM-qa",
            "target_path": "agents/project/release/RELEASE-PUBLICATION-v0.1.8.md",
        },
    )

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "rbac-write:role-not-allowed:qa" in result.stdout
    assert "release-docs" in result.stdout


def test_rbac_gate_blocks_current_agents_missing_active_claim(tmp_path: Path) -> None:
    claim = _claim(
        claim_id="CLAIM-lead",
        role="lead-engineer",
        task_id="TASK-AR-312",
        instance_id="lead-001",
        display_name="lead_engineer@vision-gap-01",
        callsite_id="terminal:lead",
    )
    _write_claim(tmp_path, claim)
    _write_empty_pointer(tmp_path)
    _pane_started(tmp_path, claim, 1)

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "rbac-current-agents:missing-active-claim:CLAIM-lead" in result.stdout


def test_owner_governance_runs_rbac_write_gate() -> None:
    root_gate = (REPO_ROOT / "scripts" / "owner_governance_gate.py").read_text(encoding="utf-8")
    template_gate = (
        REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "owner_governance_gate.py"
    ).read_text(encoding="utf-8")

    assert "rbac_write_gate.py" in root_gate
    assert "rbac_write_gate.py" in template_gate
