---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-603
display_id: TASK-AR-603
task_uid: ff9f0a9f-e5f2-4cf3-b6e8-8da4fa2830e9
work_id: TASK-AR-603
work_uid: ff9f0a9f-e5f2-4cf3-b6e8-8da4fa2830e9
kind: task
parent_id: TASKSET-AR-OPERATOR-ATTENTION-GRAPH
registered_at: 2026-06-19T09:08:00+09:00
created_at: 2026-06-19T09:08:00+09:00
updated_at: 2026-06-19T09:42:00+09:00
title: Implement operator attention graph relation assets
status: completed
started_at: 2026-06-19T09:15:00+09:00
verification_status: passed
verified_at: 2026-06-19T09:38:00+09:00
verified_by: codex-independent-w4b-verifier-2026-06-19
evidence_refs:
  - reviews/VERIFY-2026-06-19-operator-attention-graph-implementation.json
w4b_evidence: reviews/W4B-2026-06-19-TASK-AR-603.md
priority: P1
difficulty: M
est_hours: 5
est_tokens: 11000
owner: interface-designer
team: ui-ux
initiative_id: INIT-AR-OPERATOR-ATTENTION-GRAPH
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-OPERATOR-ATTENTION-GRAPH
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-603/UNIT-TASK-AR-603-001.md
reservation_id: RES-20260619-090800-36377773-01
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Add the first governed relation-aware UI assets and wire one taskset/claim/evidence/context/command-readiness workflow without bypassing the design-system contract.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
resolution: done
completed_at: 2026-06-19T09:42:00+09:00
closed_by: codex-interface-designer-oag-603
actual_hours: 1.7
actual_tokens: 11000
---

# TASK-AR-603 - Implement operator attention graph relation assets

## Goal

- Add the first governed relation-aware UI assets and wire one taskset/claim/evidence/context/command-readiness workflow without bypassing the design-system contract.

## Scope

- Source mutation is allowed only inside the declared UI asset and focused test files. Page assembly remains data wiring and composition; repeated relation chips, evidence previews, and relation panels must live in reusable asset helpers.

## Acceptance Criteria

- Touched UI is classified as design_token, ui_component, pattern_component, or one_off_for_now in closeout evidence.
- Existing tokens are reused first; any new relation token is added only in the token definition layer and labelled experimental.
- Reusable relation chip, evidence preview, attention relation panel, and graph context stack responsibilities are implemented or explicitly deferred with rationale.
- The first workflow connects a taskset or attention item to claim/evidence context and command readiness without hiding the active taskset.
- Page/server files remain focused on layout composition and data wiring; view-local duplicate relation markup is not added.

## Verification

- `python -m pytest tests/test_ui_design_assets.py tests/test_ui_console.py -q`
- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/ui_ux_cycle.py --root . assess --json`
- `python scripts/evidence_index_generator.py --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-19T09:42:00+09:00`
- Resolution: `done`
- Actual hours: `1.7`
- Actual tokens: `11000`
- Closed by: `codex-interface-designer-oag-603`
- Evidence:
  - `reviews/VERIFY-2026-06-19-operator-attention-graph-implementation.json`
<!-- work-close:end -->
