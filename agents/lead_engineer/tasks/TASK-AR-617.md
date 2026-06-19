---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-617
display_id: TASK-AR-617
task_uid: c356e6f9-6b84-4bf7-90af-f6c096d540b0
work_id: TASK-AR-617
work_uid: c356e6f9-6b84-4bf7-90af-f6c096d540b0
kind: task
parent_id: TASKSET-AR-TASKSET-BOARD-EVIDENCE-PERF-IA
registered_at: 2026-06-19T23:39:00+09:00
created_at: 2026-06-19T23:39:00+09:00
started_at: 2026-06-20T00:34:24+09:00
updated_at: 2026-06-20T00:49:37+09:00
verification_status: passed
verified_at: 2026-06-20T00:44:00+09:00
verified_by: independent-w4b-task-ar-617-20260620
evidence_refs:
  - reviews/VERIFY-2026-06-20-task-ar-617-rfc.json
w4b_evidence: reviews/W4B-2026-06-20-TASK-AR-617.md
title: Publish Taskset Board evidence and performance IA RFC
status: completed
priority: P1
difficulty: M
est_hours: 3
est_tokens: 8000
owner: lead-designer
team: ui-ux
initiative_id: INIT-AR-TASKSET-BOARD-EVIDENCE-PERF-IA
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-TASKSET-BOARD-EVIDENCE-PERF-IA
reservation_id: RES-20260619-233900-c1780e1d-02
origin_type: beta_followup
origin_ref: reviews/UX-EVAL-2026-06-19-tsaw-claim-empty-refinement.md
created_by: codex-ux-evaluator-ar-615
summary: Promote the seminar decision into an accepted design-direction RFC that names the exact IA, visual, token, component, pattern, schema, loading-budget, and beta-evidence boundaries allowed for the next implementation round.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
resolution: done
completed_at: 2026-06-20T00:49:37+09:00
closed_by: codex-lead-designer-ar-617
actual_hours: 3
actual_tokens: 8000
---

# TASK-AR-617 - Publish Taskset Board evidence and performance IA RFC

## Goal

- Promote the seminar decision into an accepted design-direction RFC that names the exact IA, visual, token, component, pattern, schema, loading-budget, and beta-evidence boundaries allowed for the next implementation round.

## Scope

- RFC and accepted design-system documentation only. Do not edit UI source files. Update DESIGN.md or DESIGN-SYSTEM.md only for promoted reusable rules or asset contracts.

## Acceptance Criteria

- reviews/RFC-2026-06-19-taskset-board-evidence-performance-ia.md states the selected IA/visual direction, target workflow, references, rejected alternatives, risks, and promotion decision.
- The RFC defines typography, density, color/non-color state, motion, effects/focus, schema, assets, accessibility, responsiveness, interaction, and latency requirements for the next implementation.
- The RFC lists minimum design-token, UI-component, pattern-component, and one-off boundaries before implementation.
- DESIGN.md and DESIGN-SYSTEM.md are updated only when the RFC promotes a reusable rule or asset contract.
- The RFC defines beta-tester and UX-evaluator evidence for the next implementation round.

## Verification

- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/evidence_index_generator.py --check`
- `python scripts/ui_ux_cycle.py --root . propose --dry-run --json`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-20T00:49:37+09:00`
- Resolution: `done`
- Actual hours: `3`
- Actual tokens: `8000`
- Closed by: `codex-lead-designer-ar-617`
- Evidence:
  - `reviews/VERIFY-2026-06-20-task-ar-617-rfc.json`
<!-- work-close:end -->
