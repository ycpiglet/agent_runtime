---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-620-001
work_uid: 8db302f1-96c1-4a6b-9fa6-b129b69f0149
kind: unit
parent_id: TASK-AR-620
unit_id: UNIT-TASK-AR-620-001
task_id: TASK-AR-620
task_set_id: TASKSET-AR-TASKSET-BOARD-EVIDENCE-REVIEW-QUEUE
initiative_id: INIT-AR-TASKSET-BOARD-EVIDENCE-REVIEW-QUEUE
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: ux-evaluator
created_at: 2026-06-20T01:08:00+09:00
updated_at: 2026-06-20T01:08:00+09:00
origin_type: ui_ux_rfc
origin_ref: reviews/RFC-2026-06-19-taskset-board-evidence-performance-ia.md
created_by: codex-interface-designer-ar-618
summary: Record evidence review queue beta and UX evidence
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: This unit runs after the source-mutating implementation lands and checks that the accepted evidence/performance IA works as a user-like operator workflow.
inputs:
  - reviews/BETA-PLAN-2026-06-20-taskset-board-evidence-review-queue.md
  - reviews/RFC-2026-06-19-taskset-board-evidence-performance-ia.md
  - src/agent_runtime/ui_state.py
  - src/agent_runtime/ui_design_assets.py
  - src/agent_runtime/ui_console_assets.py
target_files:
  - reviews/BETA-TEST-2026-06-20-taskset-board-evidence-review-queue.md
  - reviews/UX-EVAL-2026-06-20-taskset-board-evidence-review-queue.md
  - reviews/VERIFY-2026-06-20-taskset-board-evidence-review-queue-beta.json
  - reviews/INDEX.md
scope: Record exploratory evidence only. Do not patch UI source files in this unit.
acceptance:
  - Evidence lists exact actions, viewport, data state, expected result, observed result, pass/fail, and follow-up owner.
  - Accessibility review covers keyboard order, focus visibility, labels, count announcements, reduced motion, and non-color-only state.
  - Responsiveness review distinguishes active Taskset Board viewport fit from inactive DOM scan noise.
  - The handoff recommends closure, another implementation refinement, or a new lead-designer seminar.
verification:
  - python scripts/design_system_gate.py --check --all-ui
  - python scripts/evidence_index_generator.py --check
  - python scripts/ui_ux_cycle.py --root . assess --json
handoff: Report beta paths, UX findings, BTC defects, closed risks, residual risks, and the next UI/UX cycle decision.
stop_condition: Stop after beta/UX evidence is complete and ready for independent W4b verification.
---

# UNIT-TASK-AR-620-001 - Record evidence review queue beta and UX evidence

## Context

This unit runs after the source-mutating implementation lands and checks that the accepted evidence/performance IA works as a user-like operator workflow.

## Inputs

- reviews/BETA-PLAN-2026-06-20-taskset-board-evidence-review-queue.md
- reviews/RFC-2026-06-19-taskset-board-evidence-performance-ia.md
- src/agent_runtime/ui_state.py
- src/agent_runtime/ui_design_assets.py
- src/agent_runtime/ui_console_assets.py

## Target Files

- reviews/BETA-TEST-2026-06-20-taskset-board-evidence-review-queue.md
- reviews/UX-EVAL-2026-06-20-taskset-board-evidence-review-queue.md
- reviews/VERIFY-2026-06-20-taskset-board-evidence-review-queue-beta.json
- reviews/INDEX.md

## Scope

Record exploratory evidence only. Do not patch UI source files in this unit.

## Steps

1. Launch or inspect the local UI surface after implementation.
2. Run unknown evidence triage from Taskset Board first viewport to selected queue detail.
3. Run known-target retrieval by taskset id/title and confirm queue/detail state remains coherent.
4. Open a capped group and record visible count, hidden count, ordering reason, and selected item state.
5. Exercise slow detail, stale summary, retryable, defer, empty group, blocked command, interrupted claim, expired claim, and no active claim paths where data exists; otherwise document the fixture/simulation gap.
6. Repeat primary flows at desktop and 390x844, then record keyboard and reduced-motion notes.
7. Route failures with BTC-TSERQ IDs and assetization class.

## Acceptance Criteria

- Evidence lists exact actions, viewport, data state, expected result, observed result, pass/fail, and follow-up owner.
- Accessibility review covers keyboard order, focus visibility, labels, count announcements, reduced motion, and non-color-only state.
- Responsiveness review distinguishes active Taskset Board viewport fit from inactive DOM scan noise.
- The handoff recommends closure, another implementation refinement, or a new lead-designer seminar.

## Verification

- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/evidence_index_generator.py --check`
- `python scripts/ui_ux_cycle.py --root . assess --json`

## Handoff

Report beta paths, UX findings, BTC defects, closed risks, residual risks, and the next UI/UX cycle decision.

## Stop Boundary

Stop after beta/UX evidence is complete and ready for independent W4b verification.
