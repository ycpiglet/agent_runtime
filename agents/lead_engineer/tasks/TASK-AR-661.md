---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-661
display_id: TASK-AR-661
task_uid: 08ba3ad1-ab16-4172-9f98-2f5917fe917b
work_id: TASK-AR-661
work_uid: 08ba3ad1-ab16-4172-9f98-2f5917fe917b
kind: task
parent_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
registered_at: 2026-07-30T11:25:17+09:00
created_at: 2026-07-30T11:25:17+09:00
updated_at: 2026-07-30T11:25:17+09:00
title: Seal integration with SHA-bound remote attestation
status: planned
priority: P1
difficulty: XL
est_hours: 22
est_tokens: 47000
owner: lead-engineer
team: release-integrity
initiative_id: INIT-AR-AUTONOMOUS-EXECUTION-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-661/UNIT-TASK-AR-661-001.md
reservation_id: RES-20260730-112517-91ed5cf4-07
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md
created_by: codex-root-session-isolation-planner
summary: Make the serialized integration authority the only path that can absorb worker commits into the protected branch.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
tags:
  - work-cli-created
acceptance:
  - Only the integration role may merge, rebase, cherry-pick, or advance the protected branch.
  - Every candidate commit belongs to one released session/claim and valid scope revision.
  - Gate evidence is bound to repository, base SHA, candidate SHA, task, run, and gate bundle.
  - Remote required checks cannot be satisfied by evidence for a different SHA.
  - Candidate changes to gate policy are evaluated under protected-base policy and elevated review.
verification:
  - python -m pytest -q tests/test_merge_queue.py tests/test_merge_queue_policy.py tests/test_session_scm_guard.py tests/test_remote_gate_attestation.py tests/test_gate_governance.py
  - python scripts/merge_queue_policy.py --check
---

# TASK-AR-661 - Seal integration with SHA-bound remote attestation

## Goal

- Make the serialized integration authority the only path that can absorb worker commits into the protected branch.

## Scope

- Verify commit provenance, revalidate against the current base, bind gate results to exact SHAs and gate versions, and enforce required remote checks and protected gate policy.

## Acceptance Criteria

- Only the integration role may merge, rebase, cherry-pick, or advance the protected branch.
- Every candidate commit belongs to one released session/claim and valid scope revision.
- Gate evidence is bound to repository, base SHA, candidate SHA, task, run, and gate bundle.
- Remote required checks cannot be satisfied by evidence for a different SHA.
- Candidate changes to gate policy are evaluated under protected-base policy and elevated review.

## Verification

- `python -m pytest -q tests/test_merge_queue.py tests/test_merge_queue_policy.py tests/test_session_scm_guard.py tests/test_remote_gate_attestation.py tests/test_gate_governance.py`
- `python scripts/merge_queue_policy.py --check`
