from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "taskset_boundary_gate.py"


def _run(root: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), "--check", *extra],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _write_claim(root: Path, claim_id: str, payload: dict) -> None:
    claims_dir = root / "agents" / "runtime" / "task_claims"
    claims_dir.mkdir(parents=True, exist_ok=True)
    payload = {"claim_id": claim_id, **payload}
    (claims_dir / f"{claim_id}.json").write_text(json.dumps(payload), encoding="utf-8")


def _completed_claim(root: Path, scope: str, *, released_at: str = "2026-06-12T10:00:00+09:00") -> None:
    _write_claim(
        root,
        "CLAIM-DONE",
        {
            "task_id": "TASK-AR-901",
            "task_set_id": scope,
            "active_scope": scope,
            "status": "released",
            "phase": "taskset-completed",
            "progress_pct": 100,
            "claimed_at": "2026-06-12T09:00:00+09:00",
            "released_at": released_at,
        },
    )


def test_gate_is_noop_with_no_active_scope_claims(tmp_path: Path) -> None:
    # No completed-scope claim => guard is OFF => pass. This is the clean-repo
    # / no-regression case that the stop-hook approve path depends on.
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout
    assert "findings=0" in result.stdout


def test_gate_is_noop_when_scope_active_but_not_completed(tmp_path: Path) -> None:
    _write_claim(
        tmp_path,
        "CLAIM-ACTIVE",
        {
            "task_id": "TASK-AR-901",
            "task_set_id": "TASKSET-AR-QUALITY-LOOP",
            "active_scope": "TASKSET-AR-QUALITY-LOOP",
            "status": "in_progress",
            "phase": "implement",
            "claimed_at": "2026-06-12T09:00:00+09:00",
        },
    )
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout
    assert "findings=0" in result.stdout


def test_gate_blocks_out_of_scope_work_after_completion(tmp_path: Path) -> None:
    _completed_claim(tmp_path, "TASKSET-AR-QUALITY-LOOP")
    # New active claim in a DIFFERENT taskset opened AFTER completion = drift.
    _write_claim(
        tmp_path,
        "CLAIM-DRIFT",
        {
            "task_id": "TASK-AR-999",
            "task_set_id": "TASKSET-AR-SOMETHING-ELSE",
            "active_scope": "TASKSET-AR-SOMETHING-ELSE",
            "status": "in_progress",
            "phase": "implement",
            "claimed_at": "2026-06-12T11:00:00+09:00",
        },
    )
    result = _run(tmp_path)
    assert result.returncode == 1, result.stdout
    assert "taskset:boundary-violation" in result.stdout
    assert "completed-scope=TASKSET-AR-QUALITY-LOOP" in result.stdout
    assert "CLAIM-DRIFT" in result.stdout


def test_gate_does_not_block_in_scope_followon(tmp_path: Path) -> None:
    _completed_claim(tmp_path, "TASKSET-AR-QUALITY-LOOP")
    # A remaining task in the SAME taskset is in-scope and must not block.
    _write_claim(
        tmp_path,
        "CLAIM-INSCOPE",
        {
            "task_id": "TASK-AR-902",
            "task_set_id": "TASKSET-AR-QUALITY-LOOP",
            "active_scope": "TASKSET-AR-QUALITY-LOOP",
            "status": "in_progress",
            "phase": "implement",
            "claimed_at": "2026-06-12T11:00:00+09:00",
        },
    )
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout
    assert "findings=0" in result.stdout


def test_gate_does_not_block_preexisting_parallel_claim(tmp_path: Path) -> None:
    _completed_claim(tmp_path, "TASKSET-AR-QUALITY-LOOP")
    # An out-of-scope claim that was created BEFORE the completion is pre-existing
    # parallel work, not post-completion drift.
    _write_claim(
        tmp_path,
        "CLAIM-PARALLEL",
        {
            "task_id": "TASK-AR-800",
            "task_set_id": "TASKSET-AR-SOMETHING-ELSE",
            "active_scope": "TASKSET-AR-SOMETHING-ELSE",
            "status": "in_progress",
            "phase": "implement",
            "claimed_at": "2026-06-12T08:00:00+09:00",
        },
    )
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout
    assert "findings=0" in result.stdout


def test_gate_respects_approved_scope_transition(tmp_path: Path) -> None:
    _completed_claim(tmp_path, "TASKSET-AR-QUALITY-LOOP")
    _write_claim(
        tmp_path,
        "CLAIM-APPROVED",
        {
            "task_id": "TASK-AR-999",
            "task_set_id": "TASKSET-AR-SOMETHING-ELSE",
            "active_scope": "TASKSET-AR-SOMETHING-ELSE",
            "status": "in_progress",
            "phase": "implement",
            "claimed_at": "2026-06-12T11:00:00+09:00",
            "scope_transition_approved": True,
        },
    )
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout
    assert "findings=0" in result.stdout


def test_allow_scope_transition_escape_downgrades_to_watch(tmp_path: Path) -> None:
    _completed_claim(tmp_path, "TASKSET-AR-QUALITY-LOOP")
    _write_claim(
        tmp_path,
        "CLAIM-DRIFT",
        {
            "task_id": "TASK-AR-999",
            "task_set_id": "TASKSET-AR-SOMETHING-ELSE",
            "active_scope": "TASKSET-AR-SOMETHING-ELSE",
            "status": "in_progress",
            "phase": "implement",
            "claimed_at": "2026-06-12T11:00:00+09:00",
        },
    )
    result = _run(tmp_path, "--allow-scope-transition")
    assert result.returncode == 0, result.stdout
    assert "[watch]" in result.stdout
    assert "taskset:boundary-violation" in result.stdout


def test_gate_is_chained_in_owner_governance() -> None:
    text = (REPO_ROOT / "scripts" / "owner_governance_gate.py").read_text(encoding="utf-8")
    assert "scripts/taskset_boundary_gate.py" in text
