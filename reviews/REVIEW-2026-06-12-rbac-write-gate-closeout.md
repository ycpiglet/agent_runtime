# REVIEW: TASK-AR-312 RBAC Write Gate Closeout

## Scope

- Task: `TASK-AR-312`
- Task set: `TASKSET-AR-VISION-GAP-CLOSURE`
- Goal: prove real multi-agent identity records and enforce role-based write boundaries.

## Changes

- Added `scripts/rbac_write_gate.py`.
  - Reads active task claims from `agents/runtime/task_claims/`.
  - Reads pane lifecycle/write events from `agents/runtime/pane_events/pane-events.jsonl`.
  - Reads `active_work.current_agents` from `agents/project/NEXT-SESSION-POINTER.yml`.
  - Blocks protected release/owner-doc writes by unauthorized roles.
  - Blocks active claims missing from `current_agents`, stale pointer claims, missing pane lifecycle events, and duplicate instance identity fields.
- Added `src/agent_runtime/templates/project/scripts/rbac_write_gate.py`.
  - Keeps generated host projects under the same protocol.
- Updated root and template `scripts/owner_governance_gate.py`.
  - Runs `scripts/rbac_write_gate.py --check` before collaboration governance.
- Added `tests/test_rbac_write_gate.py`.
  - Uses `task_claim_dispatcher.py` subprocess calls to create three distinct active instances with claim/handoff/log/pane event evidence.
  - Verifies `lead-engineer`, `qa`, and `doc-steward` identities are distinct and reflected in `current_agents`.
  - Verifies qa release-document write attempts are blocked.
  - Verifies active claims missing from `current_agents` are blocked.

## Verification

- `python -m py_compile scripts/rbac_write_gate.py src/agent_runtime/templates/project/scripts/rbac_write_gate.py scripts/owner_governance_gate.py src/agent_runtime/templates/project/scripts/owner_governance_gate.py` -> pass.
- `pytest tests/test_rbac_write_gate.py -q` -> 4 passed.
- `pytest tests/test_rbac_write_gate.py tests/test_parallel_worktree_gate.py tests/test_collaboration_concurrency_gate.py tests/test_collaboration_governance_gate.py -q` -> 24 passed.
- `pytest tests/test_template_smoke.py::test_sync_and_smoke_runtime_scripts -q` -> 1 passed.
- `PYTHONPATH=src python -m agent_runtime.cli lock --root tests/fixtures/host --check` -> findings=0.
- `python scripts/owner_governance_gate.py` -> exit 0.

## Boundary

This proves local identity, claim, pane-event, pointer, and write-boundary
enforcement. It does not claim live remote agent execution or external release
authorization; protected release writes remain Owner/release-steward scoped.
