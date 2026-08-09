---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-662
display_id: TASK-AR-662
task_uid: 4cf21015-3b16-43cd-b439-2c0dd8b1e8ba
work_id: TASK-AR-662
work_uid: 4cf21015-3b16-43cd-b439-2c0dd8b1e8ba
kind: task
parent_id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
registered_at: 2026-08-09T12:00:00+09:00
created_at: 2026-08-09T12:00:00+09:00
updated_at: 2026-08-09T12:00:00+09:00
title: Re-key and re-attest the lost V080 Scribe work
status: planned
priority: P1
difficulty: M
est_hours: 8
est_tokens: 16000
owner: lead-engineer
team: quality
initiative_id: INIT-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-662/UNIT-TASK-AR-662-001.md
reservation_id: RES-20260809-120000-5c48af85-03
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-08-09-claim-recovery-work-identity-correction-plan.md
created_by: codex-root-owner-approved-correction
summary: Restore canonical task/unit authority for the already integrated Scribe source-debt implementation under a new collision-free identity.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - scribe
  - identity-recovery
  - re-attestation
acceptance:
  - The new task is linked to lost task_uid d7d6d63a-5059-4a2f-8399-d7ca683ba6ef and all four historical worker claims by immutable digest.
  - Current Scribe debt, active coverage, cleanup receipt, no-touch, configuration, Git-view, and template behavior pass the complete registered suite.
  - No historical task, unit, claim, review, receipt, or Compound record is rewritten.
  - Fresh evidence and independent W4b cite the new task/unit identity and distinguish historical evidence from current approval.
verification:
  - PYTHONPATH=src python -m pytest tests/test_scribe_due.py tests/test_closure_gate.py tests/test_session_continuity_hooks.py tests/test_doctor.py tests/test_template_smoke.py -q
  - PYTHONPATH=src python scripts/scribe_due.py --root . --json
  - PYTHONPATH=src python scripts/template_mirror_gate.py --check
depends_on:
  - TASK-AR-661
---

# TASK-AR-662 - Re-key and re-attest the lost V080 Scribe work

## Goal

- Restore canonical task/unit authority for the already integrated Scribe source-debt implementation under a new collision-free identity.

## Scope

- Claim normally, verify the inherited implementation and historical approval against current main, record exact old-to-new evidence mapping, and close only with fresh W4a/W4b under the new identity.

## Acceptance Criteria

- The new task is linked to lost task_uid d7d6d63a-5059-4a2f-8399-d7ca683ba6ef and all four historical worker claims by immutable digest.
- Current Scribe debt, active coverage, cleanup receipt, no-touch, configuration, Git-view, and template behavior pass the complete registered suite.
- No historical task, unit, claim, review, receipt, or Compound record is rewritten.
- Fresh evidence and independent W4b cite the new task/unit identity and distinguish historical evidence from current approval.

## Verification

- `PYTHONPATH=src python -m pytest tests/test_scribe_due.py tests/test_closure_gate.py tests/test_session_continuity_hooks.py tests/test_doctor.py tests/test_template_smoke.py -q`
- `PYTHONPATH=src python scripts/scribe_due.py --root . --json`
- `PYTHONPATH=src python scripts/template_mirror_gate.py --check`
