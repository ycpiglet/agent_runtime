---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-648-001
work_uid: 6e563637-ea70-43fe-946e-b1d9aa18bb79
kind: unit
parent_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-001
task_id: TASK-AR-648
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T16:36:01+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Adopt and exercise core plus web-content in Bean Wiki
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: Bean Wiki has strong host-owned editorial agents and publishing gates but no common task/claim/compound/scribe/model-cost harness.
inputs:
  - ../bean-wiki/AGENTS.md
  - ../bean-wiki/docs/AGENT-EDITORIAL-OPS.md
  - ../allimbot/integrations/projects/bean-wiki.json
target_files:
  - tests/fixtures/pilots/bean-wiki
  - reviews/PILOT-BEAN-WIKI-v080.md
  - scripts/pilot_acceptance.py
  - tests/test_pilot_acceptance.py
scope: Run adoption plan/apply in a clean host worktree, preserve editorial assets, execute three safe tasks, and collect evidence. No push, deploy, or live publish.
acceptance:
  - Unexpected host overwrite count is zero.
  - Doctor blockers and dangling dependencies are zero.
  - Task trace is complete for all pilot diffs.
  - All publish commands remain dry-run or uncalled.
verification:
  - python scripts/pilot_acceptance.py --host bean-wiki --check
  - python -m pytest tests/test_pilot_acceptance.py -q
handoff: Attach before/after inventory, adoption duration, seams, task trace, model routing, and Bean verification output.
stop_condition: Stop before live publish, origin push, or modification of unrelated dirty host work.
---

# UNIT-TASK-AR-648-001 - Adopt and exercise core plus web-content in Bean Wiki

## Context

Bean Wiki has strong host-owned editorial agents and publishing gates but no common task/claim/compound/scribe/model-cost harness.

## Inputs

- ../bean-wiki/AGENTS.md
- ../bean-wiki/docs/AGENT-EDITORIAL-OPS.md
- ../allimbot/integrations/projects/bean-wiki.json

## Target Files

- tests/fixtures/pilots/bean-wiki
- reviews/PILOT-BEAN-WIKI-v080.md
- scripts/pilot_acceptance.py
- tests/test_pilot_acceptance.py

## Scope

Run adoption plan/apply in a clean host worktree, preserve editorial assets, execute three safe tasks, and collect evidence. No push, deploy, or live publish.

## Steps

1. Capture pre-adoption state and ownership plan.
2. Apply core plus web-content profile.
3. Run mini-task, specialist review, and restart scenarios.
4. Run Bean content/editorial gates and record metrics.

## Acceptance Criteria

- Unexpected host overwrite count is zero.
- Doctor blockers and dangling dependencies are zero.
- Task trace is complete for all pilot diffs.
- All publish commands remain dry-run or uncalled.

## Verification

- `python scripts/pilot_acceptance.py --host bean-wiki --check`
- `python -m pytest tests/test_pilot_acceptance.py -q`

## Handoff

Attach before/after inventory, adoption duration, seams, task trace, model routing, and Bean verification output.

## Stop Boundary

Stop before live publish, origin push, or modification of unrelated dirty host work.
