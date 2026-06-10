# Multi-Pane Runtime Assurance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a measurable assurance layer that can prove whether live multi-pane collaboration followed the required runtime process.

**Architecture:** Keep task claims, pane events, task files, and worktrees as separate evidence sources. Add read-only census and audit commands first, then gates, then UI state, then Owner closeout. Root remains the orchestrator and shared SSoT writer.

**Tech Stack:** Python stdlib, pytest, JSON/JSONL, Markdown frontmatter, existing task claim files, `pane_event_log.py`, `collaboration_governance_gate.py`, `ui_state.py`, and `ui_console.py`.

---

## File Structure

- Create `scripts/multipane_census.py`: reads claims, pane events, worktree references, task files, and handoff paths; emits JSON plus text summary.
- Create `scripts/multipane_process_audit.py`: verifies plan/review/compound/retro/meeting/seminar/Ralph/scribe/doc-steward coverage by policy.
- Create `agents/project/MULTIPANE-PROCESS-POLICY.yml`: defines required, optional, monitored, and waived process evidence.
- Create `scripts/multipane_drift_gate.py`: flags future heartbeat, released-claim phase/progress drift, missing active worktrees, and stale worktree candidates.
- Modify `scripts/collaboration_governance_gate.py`: include role coverage and waiver lifecycle findings from the multi-pane policy.
- Modify `scripts/collaboration_concurrency_gate.py`: require pane lifecycle event coverage for active worker claims.
- Modify `src/agent_runtime/ui_state.py`: expose `multipane_assurance` data from census, process audit, role coverage, drift, and event replay.
- Modify `src/agent_runtime/ui_console.py`: render multi-pane assurance state without adding write paths.
- Create tests: `tests/test_multipane_census.py`, `tests/test_multipane_process_audit.py`, `tests/test_multipane_drift_gate.py`.
- Modify existing tests: `tests/test_collaboration_governance_gate.py`, `tests/test_collaboration_concurrency_gate.py`, `tests/test_ui_state.py`, `tests/test_ui_console.py`.
- Create closeout report: `reviews/REVIEW-2026-06-11-multipane-runtime-assurance-closeout.md`.

## Task 1: `TASK-AR-285` Live Multi-Pane Census

**Files:**
- Create: `scripts/multipane_census.py`
- Create: `tests/test_multipane_census.py`

- [ ] **Step 1: Write the failing census test**

```python
from pathlib import Path

from scripts import multipane_census


def test_census_classifies_active_and_historical_claims(tmp_path: Path):
    root = tmp_path
    claims = root / "agents" / "runtime" / "task_claims"
    claims.mkdir(parents=True)
    (claims / "active.json").write_text(
        '{"claim_id":"active","task_id":"TASK-1","task_set_id":"SET","agent_role":"lead-engineer","status":"in_progress","phase":"implement","progress_pct":50,"worktree_path":".worktrees/TASK-1","branch":"task/TASK-1","handoff_path":"handoff.md","log_path":"log.md","last_heartbeat":"2026-06-11T01:00:00+09:00"}',
        encoding="utf-8",
    )
    (claims / "released.json").write_text(
        '{"claim_id":"released","task_id":"TASK-2","task_set_id":"SET","agent_role":"qa","status":"released","phase":"claim-released","progress_pct":100,"worktree_path":".worktrees/TASK-2","branch":"task/TASK-2","handoff_path":"handoff.md","log_path":"log.md"}',
        encoding="utf-8",
    )

    report = multipane_census.build_report(root)

    assert report["claims_total"] == 2
    assert report["active_claims"] == 1
    assert report["historical_claims"] == 1
    assert report["active_panes_threshold_met"] is False
```

- [ ] **Step 2: Run the failing test**

Run: `PYTHONPATH=src pytest tests/test_multipane_census.py::test_census_classifies_active_and_historical_claims -q`

Expected: FAIL because `scripts.multipane_census` does not exist.

- [ ] **Step 3: Implement the minimal census reader**

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ACTIVE_STATUSES = {"active", "in_progress", "claimed", "running"}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report(root: Path) -> dict[str, Any]:
    claim_dir = root / "agents" / "runtime" / "task_claims"
    claims = [_read_json(path) for path in sorted(claim_dir.glob("*.json"))] if claim_dir.exists() else []
    active = [claim for claim in claims if str(claim.get("status", "")).lower() in ACTIVE_STATUSES]
    historical = [claim for claim in claims if claim not in active]
    return {
        "claims_total": len(claims),
        "active_claims": len(active),
        "historical_claims": len(historical),
        "active_panes_threshold": 5,
        "active_panes_threshold_met": len(active) >= 5,
        "active": active,
        "historical": historical,
    }
```

- [ ] **Step 4: Run the census test**

Run: `PYTHONPATH=src pytest tests/test_multipane_census.py -q`

Expected: PASS.

## Task 2: `TASK-AR-286` Process Compliance Audit

**Files:**
- Create: `agents/project/MULTIPANE-PROCESS-POLICY.yml`
- Create: `scripts/multipane_process_audit.py`
- Create: `tests/test_multipane_process_audit.py`

- [ ] **Step 1: Write policy and failing audit test**

```python
from pathlib import Path

from scripts import multipane_process_audit


def test_process_audit_reports_missing_scribe_and_retro(tmp_path: Path):
    root = tmp_path
    reviews = root / "reviews"
    reviews.mkdir()
    (reviews / "REVIEW-1.md").write_text("# Review", encoding="utf-8")
    policy = root / "agents" / "project" / "MULTIPANE-PROCESS-POLICY.yml"
    policy.parent.mkdir(parents=True)
    policy.write_text("required_artifacts:\\n  - REVIEW\\n  - RETRO\\nrequired_roles:\\n  - scribe\\n", encoding="utf-8")

    report = multipane_process_audit.audit(root)

    assert "artifact:RETRO" in report["missing"]
    assert "role:scribe" in report["missing"]
    assert report["status"] == "watch"
```

- [ ] **Step 2: Run the failing test**

Run: `PYTHONPATH=src pytest tests/test_multipane_process_audit.py::test_process_audit_reports_missing_scribe_and_retro -q`

Expected: FAIL because `scripts.multipane_process_audit` does not exist.

- [ ] **Step 3: Implement deterministic artifact and role counting**

Implement `audit(root: Path) -> dict[str, object]` that counts review filename prefixes and claim `agent_role` values, then returns `missing`, `observed`, and `status`.

- [ ] **Step 4: Run process audit tests**

Run: `PYTHONPATH=src pytest tests/test_multipane_process_audit.py -q`

Expected: PASS.

## Task 3: `TASK-AR-287` Pane Lifecycle Event Enforcement

**Files:**
- Modify: `scripts/collaboration_concurrency_gate.py`
- Modify: `tests/test_collaboration_concurrency_gate.py`

- [ ] **Step 1: Add a failing test for active claim without pane events**

Add a test that creates one active claim and no matching pane lifecycle event, then asserts a `pane-event:missing-lifecycle` finding.

- [ ] **Step 2: Run the failing test**

Run: `PYTHONPATH=src pytest tests/test_collaboration_concurrency_gate.py -q`

Expected: FAIL with the new expected finding missing.

- [ ] **Step 3: Add claim-to-event coverage logic**

Map active claims by `claim_id` and require matching `started`, `claimed`, `heartbeat`, and `handoff` or `released` event types depending on claim status.

- [ ] **Step 4: Run concurrency gate tests**

Run: `PYTHONPATH=src pytest tests/test_collaboration_concurrency_gate.py -q`

Expected: PASS.

## Task 4: `TASK-AR-288` Role Coverage and Waiver Lifecycle

**Files:**
- Modify: `scripts/collaboration_governance_gate.py`
- Modify: `tests/test_collaboration_governance_gate.py`

- [ ] **Step 1: Add a failing waiver metadata test**

Add a test that creates a waiver missing `approved_by`, `expires_at`, or `mitigation`, then asserts the gate reports `waiver:invalid`.

- [ ] **Step 2: Run the failing test**

Run: `PYTHONPATH=src pytest tests/test_collaboration_governance_gate.py -q`

Expected: FAIL with missing waiver lifecycle validation.

- [ ] **Step 3: Implement waiver lifecycle validation**

Require every waiver to include `subjects`, `reason`, `approved_by`, `created_at`, `expires_at`, and `mitigation`.

- [ ] **Step 4: Run collaboration governance tests**

Run: `PYTHONPATH=src pytest tests/test_collaboration_governance_gate.py -q`

Expected: PASS.

## Task 5: `TASK-AR-289` Timeline Claim and Worktree Drift Gate

**Files:**
- Create: `scripts/multipane_drift_gate.py`
- Create: `tests/test_multipane_drift_gate.py`

- [ ] **Step 1: Add failing drift tests**

Write tests for future heartbeat, released claim with `progress_pct < 100`, and active claim with missing worktree path.

- [ ] **Step 2: Run the failing drift tests**

Run: `PYTHONPATH=src pytest tests/test_multipane_drift_gate.py -q`

Expected: FAIL because `scripts.multipane_drift_gate` does not exist.

- [ ] **Step 3: Implement drift classification**

Implement a gate that returns `block`, `watch`, and `findings` lists without deleting or modifying worktrees.

- [ ] **Step 4: Run drift gate tests**

Run: `PYTHONPATH=src pytest tests/test_multipane_drift_gate.py -q`

Expected: PASS.

## Task 6: `TASK-AR-290` UI Multi-Pane Assurance Surface

**Files:**
- Modify: `src/agent_runtime/ui_state.py`
- Modify: `src/agent_runtime/ui_console.py`
- Modify: `tests/test_ui_state.py`
- Modify: `tests/test_ui_console.py`

- [ ] **Step 1: Add failing UI state test**

Assert that `build_state()` exposes `multipane_assurance` with census, process, role, drift, and event summary keys.

- [ ] **Step 2: Run the failing UI state test**

Run: `PYTHONPATH=src pytest tests/test_ui_state.py -q`

Expected: FAIL because `multipane_assurance` is absent.

- [ ] **Step 3: Add read-only UI state resource**

Load reports from the new scripts and include source paths and freshness timestamps.

- [ ] **Step 4: Add console rendering test and implementation**

Assert that the console HTML includes "Multi-pane assurance", "active panes", "role coverage", and "drift" labels.

- [ ] **Step 5: Run focused UI tests**

Run: `PYTHONPATH=src pytest tests/test_ui_state.py tests/test_ui_console.py -q`

Expected: PASS.

## Task 7: `TASK-AR-291` Closeout Report and Gates

**Files:**
- Create: `reviews/REVIEW-2026-06-11-multipane-runtime-assurance-closeout.md`
- Modify: `BACKLOG.md`
- Modify: `STATUS.md`
- Modify: `BACKLOG-BOARD.md`

- [ ] **Step 1: Run focused assurance commands**

Run: `python scripts/multipane_census.py --check`, `python scripts/multipane_process_audit.py --check`, and `python scripts/multipane_drift_gate.py --check`.

Expected: each command reports pass or watch with explicit findings.

- [ ] **Step 2: Run generated board refresh**

Run: `python scripts/backlog_board.py --write`

Expected: board includes `TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE`.

- [ ] **Step 3: Run task-set and owner gates**

Run: `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE --check` and `python scripts/owner_governance_gate.py`.

Expected: both commands exit 0 before any completion claim.

- [ ] **Step 4: Publish closeout review**

Create the closeout review with exact sections: `Bottom Line`, `Signal`, `Insight`, `Decision`, `Action Board`, `Risks / Blockers`, and `Next Steps`.

## Self-Review

- Spec coverage: covers live pane census, process compliance, pane event enforcement, role coverage, lifecycle drift, UI visibility, and Owner closeout.
- Placeholder scan: no `TBD`, `TODO`, or "implement later" placeholders are used.
- Type consistency: reports use `status`, `findings`, `block`, `watch`, and count fields consistently across gates and UI state.

