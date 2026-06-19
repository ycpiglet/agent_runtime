---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-619-001
work_uid: 88a0ecb2-c945-44e5-957f-36764a421c43
kind: unit
parent_id: TASK-AR-619
unit_id: UNIT-TASK-AR-619-001
task_id: TASK-AR-619
task_set_id: TASKSET-AR-TASKSET-BOARD-EVIDENCE-REVIEW-QUEUE
initiative_id: INIT-AR-TASKSET-BOARD-EVIDENCE-REVIEW-QUEUE
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: interface-designer
created_at: 2026-06-20T01:08:00+09:00
updated_at: 2026-06-20T01:08:00+09:00
origin_type: ui_ux_rfc
origin_ref: reviews/RFC-2026-06-19-taskset-board-evidence-performance-ia.md
created_by: codex-interface-designer-ar-618
summary: Derive evidence review queue schema from Taskset Board state
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: TASK-AR-617 accepted the evidence review queue direction because evidence_gaps=49 made the stale/missing lane too flat and API latency made detail loading ambiguous. The first implementation must add a read-only summary/detail schema before rendering new UI.
inputs:
  - reviews/RFC-2026-06-19-taskset-board-evidence-performance-ia.md
  - src/agent_runtime/ui_state.py
  - tests/test_ui_state.py
target_files:
  - src/agent_runtime/ui_state.py
  - tests/test_ui_state.py
  - reviews/VERIFY-2026-06-20-taskset-board-evidence-review-queue-implementation.json
  - reviews/INDEX.md
scope: Add only read-only derived fields under the existing Taskset Board payload. Do not write tasks, claims, boards, indexes, or registries from the UI state path.
acceptance:
  - A focused state test proves at least two evidence groups can be generated from fixture tasksets.
  - A focused state test proves a group with more than the visible cap reports hidden_count and keeps the highest-severity items visible.
  - A focused state test proves summary/detail loading labels are present and textual.
  - No source path outside `ui_state.py` and focused tests changes in this unit.
verification:
  - python -m pytest tests/test_ui_state.py -q
  - python scripts/evidence_index_generator.py --check
  - git diff --check
handoff: Report schema fields, grouping rules, cap value, derived freshness/severity rules, and any unresolved true-async split risk.
stop_condition: Stop after the read-only schema is implemented, tested, and ready for UI asset rendering.
---

# UNIT-TASK-AR-619-001 - Derive evidence review queue schema from Taskset Board state

## Context

TASK-AR-617 accepted the evidence review queue direction because evidence_gaps=49 made the stale/missing lane too flat and API latency made detail loading ambiguous. The first implementation must add a read-only summary/detail schema before rendering new UI.

## Inputs

- reviews/RFC-2026-06-19-taskset-board-evidence-performance-ia.md
- src/agent_runtime/ui_state.py
- tests/test_ui_state.py

## Target Files

- src/agent_runtime/ui_state.py
- tests/test_ui_state.py
- reviews/VERIFY-2026-06-20-taskset-board-evidence-review-queue-implementation.json
- reviews/INDEX.md

## Scope

Add only read-only derived fields under the existing Taskset Board payload. Do not write tasks, claims, boards, indexes, or registries from the UI state path.

## Steps

1. Read the current `TASKSET_ATTENTION_LANES`, `_taskset_attention_workspace`, and `build_tasksets_board` implementation.
2. Derive freshness and severity from current card fields: recent activity, child phases, progress, claim summary, command readiness, status bucket, and staleness note.
3. Create capped groups with visible count, hidden count, ordering reason, and selected defaults.
4. Expose summary/detail loading labels as data even before a true async API split exists.
5. Add focused tests for stale/missing grouping, hidden count, ordering reason, claim/command fields, and safe empty states.

## Acceptance Criteria

- A focused state test proves at least two evidence groups can be generated from fixture tasksets.
- A focused state test proves a group with more than the visible cap reports hidden_count and keeps the highest-severity items visible.
- A focused state test proves summary/detail loading labels are present and textual.
- No source path outside `ui_state.py` and focused tests changes in this unit.

## Verification

- `python -m pytest tests/test_ui_state.py -q`
- `python scripts/evidence_index_generator.py --check`
- `git diff --check`

## Handoff

Report schema fields, grouping rules, cap value, derived freshness/severity rules, and any unresolved true-async split risk.

## Stop Boundary

Stop after the read-only schema is implemented, tested, and ready for UI asset rendering.
