---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-601
display_id: TASK-AR-601
task_uid: 2b3c140e-1213-4b2a-8663-7a7c817f3c8a
work_id: TASK-AR-601
work_uid: 2b3c140e-1213-4b2a-8663-7a7c817f3c8a
kind: task
parent_id: TASKSET-AR-UI-UX-DESIGN-DIRECTION-RFC
registered_at: 2026-06-19T08:18:00+09:00
created_at: 2026-06-19T08:18:00+09:00
updated_at: 2026-06-19T08:43:52+09:00
title: Publish UI design direction RFC
status: planned
started_at: 2026-06-19T08:36:00+09:00
verification_status: passed
verified_at: 2026-06-19T08:43:52+09:00
verified_by: codex-independent-verifier-ui-rfc-601
evidence_refs:
  - reviews/VERIFY-2026-06-19-task-ar-601-20260619084352.json
w4b_evidence: reviews/W4B-2026-06-19-TASK-AR-601.md
priority: P1
difficulty: M
est_hours: 3
est_tokens: 7000
owner: lead-designer
team: ui-ux
initiative_id: INIT-AR-UI-UX-DESIGN-DIRECTION-CYCLE
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-UI-UX-DESIGN-DIRECTION-RFC
reservation_id: RES-20260619-081800-ff02ebb7-02
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Create the RFC that promotes the seminar decision into an accepted design direction and names the exact token, component, pattern, and page-assembly deltas allowed for implementation.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-601 - Publish UI design direction RFC

## Goal

- Create the RFC that promotes the seminar decision into an accepted design direction and names the exact token, component, pattern, and page-assembly deltas allowed for implementation.

## Scope

- RFC and design-system documentation only. Do not mutate UI source files. Update DESIGN.md or DESIGN-SYSTEM.md only for accepted direction and governance deltas.

## Acceptance Criteria

- reviews/RFC-2026-06-19-ui-ux-design-direction.md states the selected visual direction, target workflow, references, rejected alternatives, risks, and promotion decision.
- The RFC lists minimum design-token, UI-component, pattern-component, and one-off boundaries before implementation.
- DESIGN.md and DESIGN-SYSTEM.md are updated only when the RFC promotes a reusable rule or asset contract.
- The RFC defines beta-tester and UX-evaluator evidence for the next implementation round.

## Verification

- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/evidence_index_generator.py --check`
- `python scripts/ui_ux_cycle.py --root . propose --dry-run --json`
