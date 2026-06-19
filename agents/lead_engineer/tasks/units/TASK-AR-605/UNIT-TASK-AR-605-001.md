---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-605-001
work_uid: e0612cb3-cc15-41de-b005-0c48a7cb96c8
kind: unit
parent_id: TASK-AR-605
unit_id: UNIT-TASK-AR-605-001
task_id: TASK-AR-605
task_set_id: TASKSET-AR-OAG-CLAIM-AWARE-RELATION-ADAPTER
initiative_id: INIT-AR-OAG-CLAIM-AWARE-RELATION-ADAPTER
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: interface-designer
created_at: 2026-06-19T12:26:00+09:00
updated_at: 2026-06-19T12:26:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Add claim-aware relation state mapping
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: TASK-AR-604 beta/UX evidence accepted the visual direction but found that `/api/state` includes resumed and expired claim records while the relation panel still reports ready-to-claim and task.create-ready. The next implementation must make the relation adapter consume that state.
inputs:
  - reviews/BETA-TEST-2026-06-19-operator-attention-graph.md
  - reviews/UX-EVAL-2026-06-19-operator-attention-graph.md
  - reviews/W4B-2026-06-19-TASK-AR-604.md
  - src/agent_runtime/ui_console_assets.py
  - src/agent_runtime/ui_design_assets.py
  - tests/test_ui_console.py
  - tests/test_ui_design_assets.py
target_files:
  - src/agent_runtime/ui_console_assets.py
  - src/agent_runtime/ui_design_assets.py
  - tests/test_ui_console.py
  - tests/test_ui_design_assets.py
  - reviews/VERIFY-2026-06-19-oag-claim-aware-relation-adapter.json
  - reviews/INDEX.md
scope: Implement claim-aware relation state mapping and focused tests only. Do not add a new visual theme, new navigation model, or broad page refactor.
acceptance:
  - Tests prove active claim state changes relation chip and command readiness wording.
  - Tests prove interrupted phase no longer maps to plain stale.
  - Existing empty/stale/missing graph context fallbacks still pass.
  - No raw color, spacing, radius, shadow, or type literal is introduced outside token definitions.
  - The implementation keeps page code focused on data wiring and delegates repeated UI to helpers or pattern assets.
verification:
  - python -m pytest tests/test_ui_design_assets.py tests/test_ui_console.py -q
  - python scripts/design_system_gate.py --check --all-ui
  - python scripts/ui_ux_cycle.py --root . assess --json
  - python scripts/evidence_index_generator.py --check
handoff: Report adapter ownership, state mapping table, tests added, assetization classification, and remaining UX/beta risks.
stop_condition: Stop after the claim-aware relation adapter passes focused tests and W4a evidence is ready for independent verification.
---

# UNIT-TASK-AR-605-001 - Add claim-aware relation state mapping

## Context

TASK-AR-604 beta/UX evidence accepted the visual direction but found that `/api/state` includes resumed and expired claim records while the relation panel still reports ready-to-claim and task.create-ready. The next implementation must make the relation adapter consume that state.

## Inputs

- reviews/BETA-TEST-2026-06-19-operator-attention-graph.md
- reviews/UX-EVAL-2026-06-19-operator-attention-graph.md
- reviews/W4B-2026-06-19-TASK-AR-604.md
- src/agent_runtime/ui_console_assets.py
- src/agent_runtime/ui_design_assets.py
- tests/test_ui_console.py
- tests/test_ui_design_assets.py

## Target Files

- src/agent_runtime/ui_console_assets.py
- src/agent_runtime/ui_design_assets.py
- tests/test_ui_console.py
- tests/test_ui_design_assets.py
- reviews/VERIFY-2026-06-19-oag-claim-aware-relation-adapter.json
- reviews/INDEX.md

## Scope

Implement claim-aware relation state mapping and focused tests only. Do not add a new visual theme, new navigation model, or broad page refactor.

## Steps

1. Read TASK-AR-604 beta, UX, and W4b findings.
2. Trace how `task_claims` reach the Taskset Board state and how `tasksetRelationSummary` currently derives claim path and command readiness.
3. Promote or replace the adapter so claim readiness can distinguish unclaimed, claimed, expired/reaped, guarded, interrupted, and completed states.
4. Keep relation state labels text-visible and tokenized through existing component/pattern helpers.
5. Add focused tests for active claim, expired predecessor, interrupted phase, blocked/guarded command, stale evidence, and no-claim fallback.
6. Run W4a verification commands and record evidence.

## Acceptance Criteria

- Tests prove active claim state changes relation chip and command readiness wording.
- Tests prove interrupted phase no longer maps to plain stale.
- Existing empty/stale/missing graph context fallbacks still pass.
- No raw color, spacing, radius, shadow, or type literal is introduced outside token definitions.
- The implementation keeps page code focused on data wiring and delegates repeated UI to helpers or pattern assets.

## Verification

- `python -m pytest tests/test_ui_design_assets.py tests/test_ui_console.py -q`
- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/ui_ux_cycle.py --root . assess --json`
- `python scripts/evidence_index_generator.py --check`

## Handoff

Report adapter ownership, state mapping table, tests added, assetization classification, and remaining UX/beta risks.

## Stop Boundary

Stop after the claim-aware relation adapter passes focused tests and W4a evidence is ready for independent verification.
