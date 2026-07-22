---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-601
display_id: TASK-AR-601
task_uid: 8cc19b2e-59ac-4f1f-8743-07dd789328d0
work_id: TASK-AR-601
work_uid: 8cc19b2e-59ac-4f1f-8743-07dd789328d0
kind: task
parent_id: TASKSET-AR-ROLE-ROUTING-CLOSEOUT-RELIABILITY
registered_at: 2026-07-19T11:03:47+09:00
created_at: 2026-07-19T11:03:47+09:00
started_at: 2026-07-19T11:09:38+09:00
updated_at: 2026-07-19T11:43:51+09:00
title: Make routed review overlays cleanly releasable
status: completed
priority: P0
difficulty: S
est_hours: 2
est_tokens: 5000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-ROLE-ROUTING-CLOSEOUT-RELIABILITY
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-ROLE-ROUTING-CLOSEOUT-RELIABILITY
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-601/UNIT-TASK-AR-601-001.md
reservation_id: RES-20260719-110347-339abb00-01
origin_type: runtime_discovery
origin_ref: TASK-AR-594 closeout overlay release failure
created_by: codex-root-planner
summary: Add handoff/log artifacts at overlay creation and a recursion guard at release.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
verification:
  - python -m pytest tests/test_role_routing.py tests/test_role_routing_wiring.py tests/test_task_claim_dispatcher.py -q
  - python scripts/regen_host_lock_if_needed.py --check
verification_status: passed
verified_at: 2026-07-19T11:43:10+09:00
verified_by: codex-root-task-ar-601
evidence_refs:
  - reviews/VERIFY-2026-07-19-task-ar-601-20260719112303.json
  - reviews/VERIFY-2026-07-19-task-ar-601-20260719114310.json
  - reviews/W4B-2026-07-19-TASK-AR-601-HARDENING.md
  - reviews/ROLE-REVIEW-2026-07-19-TASK-AR-601-SKEPTIC-RECHECK.md
resolution: done
completed_at: 2026-07-19T11:43:51+09:00
closed_by: codex-root-task-ar-601
actual_hours: 1.5
actual_tokens: 16000
---

# TASK-AR-601 - Make routed review overlays cleanly releasable

## Goal

- Ensure role_routing overlay claims carry required lifecycle artifacts and releasing an overlay cannot recursively route another overlay.

## Scope

- Change the live-checkout role-routing claim creation/release seam and focused tests; preserve flag gating and additive review behavior. Host-template routing is out of scope because the generated host scaffold does not ship `role_routing.py` or enable this live-only seam.

## Acceptance Criteria

- Every generated overlay claim points to existing handoff and log records.
- Releasing an overlay with role routing enabled creates no nested REVIEW-REVIEW claim.
- Ordinary worker release still routes the configured additive reviews exactly once.

## Verification

- `python -m pytest tests/test_role_routing.py tests/test_role_routing_wiring.py tests/test_task_claim_dispatcher.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-19T11:43:51+09:00`
- Resolution: `done`
- Actual hours: `1.5`
- Actual tokens: `16000`
- Closed by: `codex-root-task-ar-601`
- Evidence:
  - `reviews/VERIFY-2026-07-19-task-ar-601-20260719112303.json`
  - `reviews/VERIFY-2026-07-19-task-ar-601-20260719114310.json`
<!-- work-close:end -->
