---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-604
display_id: TASK-AR-604
task_uid: ad899e53-4511-4f24-aebd-b24dcc469b5b
work_id: TASK-AR-604
work_uid: ad899e53-4511-4f24-aebd-b24dcc469b5b
kind: task
parent_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
registered_at: 2026-07-22T17:45:00+09:00
created_at: 2026-07-22T17:45:00+09:00
updated_at: 2026-07-22T21:24:21+09:00
title: Persist canonical task start status
status: planned
priority: P1
difficulty: M
est_hours: 2
est_tokens: 7000
owner: lead-engineer
initiative_id: INIT-AR-JULY-RELEASE-IMPACT-REMEDIATION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-604/UNIT-TASK-AR-604-001.md
reservation_id: RES-20260722-174500-dbaf8585-02
origin_type: downstream_bug
origin_ref: reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
created_by: codex-root-planner
summary: Close GitHub
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python -m pytest tests/test_taskset_dispatcher.py -q
  - python scripts/regen_host_lock_if_needed.py --check
tags:
  - github-293
  - taskset-dispatch
verification_status: passed
verified_at: 2026-07-22T21:24:21+09:00
verified_by: codex-root-task-ar-604
evidence_refs:
  - reviews/VERIFY-2026-07-22-task-ar-604-20260722212421.json
---

# TASK-AR-604 - Persist canonical task start status

## Goal

- Close GitHub #293 by separating normalized comparison aliases from the canonical status written to task frontmatter.

## Scope

- Close GitHub #293 by separating normalized comparison aliases from the canonical status written to task frontmatter.

## Acceptance Criteria

- Starting a localized task persists the canonical configured display status instead of the internal alias.
- Selection and readiness normalization remain unchanged.
- Root/template parity and host lock checks pass.

## Verification

- `python -m pytest tests/test_taskset_dispatcher.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`