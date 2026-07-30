---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-653
display_id: TASK-AR-653
task_uid: d7d6d63a-5059-4a2f-8399-d7ca683ba6ef
work_id: TASK-AR-653
work_uid: d7d6d63a-5059-4a2f-8399-d7ca683ba6ef
kind: task
parent_id: TASKSET-AR-V080-OPERABILITY-HARDENING
registered_at: 2026-07-30T11:25:00+09:00
created_at: 2026-07-30T11:25:00+09:00
updated_at: 2026-07-30T22:45:39+09:00
title: Close the Scribe source-debt and active-work loop
status: planned
priority: P1
difficulty: L
est_hours: 12
est_tokens: 24000
owner: lead-engineer
team: quality
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-653/UNIT-TASK-AR-653-001.md
reservation_id: RES-20260730-112500-842c7890-02
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
created_by: codex-root-task-ar-650-planner
summary: Ensure Scribe freshness means current work is covered and overdue state was actually handled, not merely projected.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
acceptance:
  - A fresh projection over an overdue source no longer reports debt clearance.
  - Active task and claim identities are represented or the Scribe result is not ready.
  - Cleanup candidates exclude active and no-touch records and select only cold history.
  - A cleanup receipt binds source before/after digests and the resulting hot count.
  - Scribe can be selectively routed through the low-cost role policy without gaining canonical decision authority.
verification:
  - python -m pytest tests/test_scribe_due.py tests/test_closure_gate.py tests/test_session_start_hook.py tests/test_doctor.py tests/test_template_smoke.py -q
  - python scripts/scribe_due.py --root . --json
  - python scripts/template_mirror_gate.py --check
---

# TASK-AR-653 - Close the Scribe source-debt and active-work loop

## Goal

- Ensure Scribe freshness means current work is covered and overdue state was actually handled, not merely projected.

## Scope

- Separate projection freshness from source debt, require active task coverage, generate bounded cleanup plans and receipts, and keep overdue closure blocked until a valid outcome exists.

## Acceptance Criteria

- A fresh projection over an overdue source no longer reports debt clearance.
- Active task and claim identities are represented or the Scribe result is not ready.
- Cleanup candidates exclude active and no-touch records and select only cold history.
- A cleanup receipt binds source before/after digests and the resulting hot count.
- Scribe can be selectively routed through the low-cost role policy without gaining canonical decision authority.

## Verification

- `python -m pytest tests/test_scribe_due.py tests/test_closure_gate.py tests/test_session_start_hook.py tests/test_doctor.py tests/test_template_smoke.py -q`
- `python scripts/scribe_due.py --root . --json`
- `python scripts/template_mirror_gate.py --check`
