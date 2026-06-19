---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-618
display_id: TASK-AR-618
task_uid: 92c20643-0ae0-4f66-89b7-613f33be71cf
work_id: TASK-AR-618
work_uid: 92c20643-0ae0-4f66-89b7-613f33be71cf
kind: task
parent_id: TASKSET-AR-TASKSET-BOARD-EVIDENCE-PERF-IA
registered_at: 2026-06-19T23:39:00+09:00
created_at: 2026-06-19T23:39:00+09:00
started_at: 2026-06-20T01:00:12+09:00
updated_at: 2026-06-20T01:14:17+09:00
verification_status: passed
verified_at: 2026-06-20T01:10:45+09:00
verified_by: independent-w4b-task-ar-618-20260620
evidence_refs:
  - reviews/VERIFY-2026-06-20-task-ar-618-implementation-beta-plan.json
w4b_evidence: reviews/W4B-2026-06-20-TASK-AR-618.md
title: Derive Taskset Board evidence and performance implementation units
status: completed
priority: P1
difficulty: M
est_hours: 3
est_tokens: 8000
owner: interface-designer
team: ui-ux
initiative_id: INIT-AR-TASKSET-BOARD-EVIDENCE-PERF-IA
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-TASKSET-BOARD-EVIDENCE-PERF-IA
reservation_id: RES-20260619-233900-c1780e1d-03
origin_type: beta_followup
origin_ref: reviews/UX-EVAL-2026-06-19-tsaw-claim-empty-refinement.md
created_by: codex-ux-evaluator-ar-615
summary: Turn the accepted evidence/performance IA RFC into a source-mutation implementation registration input and a paired beta/UX evaluation plan without bypassing W0-W6.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
resolution: done
completed_at: 2026-06-20T01:14:17+09:00
closed_by: codex-interface-designer-ar-618
actual_hours: 3
actual_tokens: 8000
---

# TASK-AR-618 - Derive Taskset Board evidence and performance implementation units

## Goal

- Turn the accepted evidence/performance IA RFC into a source-mutation implementation registration input and a paired beta/UX evaluation plan without bypassing W0-W6.

## Scope

- Planning and registration input only. Do not edit UI source files. The output must be specific enough for interface-designer and ux-evaluator claims.

## Acceptance Criteria

- A follow-up registration input names the next UI source mutation task, target files, target API/schema contracts, and token/component/pattern/one-off classification.
- A beta-tester artifact plan records clicked/typed flows, recovery attempts, viewport/data state, keyboard traversal, reduced-motion behavior, API latency observation, and BTC-style failure routing.
- The next implementation task keeps page files focused on layout and data wiring while repeated surface area is moved into pattern assets.
- The plan preserves design-system gate, focused UI tests, evidence index, and independent W4b verification commands.

## Verification

- `python scripts/ui_ux_cycle.py --root . propose --dry-run --json`
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-TASKSET-BOARD-EVIDENCE-PERF-IA --check`
- `python scripts/evidence_index_generator.py --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-20T01:14:17+09:00`
- Resolution: `done`
- Actual hours: `3`
- Actual tokens: `8000`
- Closed by: `codex-interface-designer-ar-618`
- Evidence:
  - `reviews/VERIFY-2026-06-20-task-ar-618-implementation-beta-plan.json`
<!-- work-close:end -->
