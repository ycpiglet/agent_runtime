---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-621
display_id: TASK-AR-621
task_uid: fda7eb07-f96d-4713-9ce3-24bc24c7fd1c
work_id: TASK-AR-621
work_uid: fda7eb07-f96d-4713-9ce3-24bc24c7fd1c
kind: task
parent_id: TASKSET-AR-WORK-VERIFY-WINDOWS-SHELL-INTEGRITY
registered_at: 2026-07-23T14:08:00+09:00
created_at: 2026-07-23T14:08:00+09:00
updated_at: 2026-07-23T16:14:17+09:00
started_at: 2026-07-23T15:39:58+09:00
title: Preserve work-verify command arguments on Windows
status: completed
priority: P1
difficulty: M
est_hours: 2
est_tokens: 6000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-WORK-VERIFY-WINDOWS-SHELL-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-WORK-VERIFY-WINDOWS-SHELL-INTEGRITY
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-621/UNIT-TASK-AR-621-001.md
reservation_id: RES-20260723-140800-58712166-01
origin_type: runtime_bug
origin_ref: reviews/REVIEW-2026-07-23-work-verify-windows-shell-registration.md
created_by: codex-root-planner
summary: Specify and implement a cross-platform work.py verify execution contract with regression coverage for caret-bearing Git revisions.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python -m pytest tests/test_work_verify.py -q
  - python scripts/owner_governance_gate.py
tags:
  - work-cli
  - windows
  - verification-integrity
verification_status: passed
verified_at: 2026-07-23T16:12:45+09:00
verified_by: /root/task-ar-621
evidence_refs:
  - reviews/VERIFY-2026-07-23-task-ar-621-20260723161245.json
resolution: done
completed_at: 2026-07-23T16:14:17+09:00
closed_by: /root/task-ar-621
actual_hours: 0.8
actual_tokens: 12000
---

# TASK-AR-621 - Preserve work-verify command arguments on Windows

## Goal

- Prevent shell metacharacters in registered verification commands from being silently changed by the Windows command shell.

## Scope

- Prevent shell metacharacters in registered verification commands from being silently changed by the Windows command shell.

## Acceptance Criteria

- A registered command containing a caret-bearing Git revision reaches the child process without silent argument mutation.
- Existing verification success, failure, timeout, stdout, and stderr evidence behavior remains compatible.
- Focused work-verify tests and Owner governance pass.

## Verification

- `python -m pytest tests/test_work_verify.py -q`
- `python scripts/owner_governance_gate.py`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-23T16:14:17+09:00`
- Resolution: `done`
- Actual hours: `0.8`
- Actual tokens: `12000`
- Closed by: `/root/task-ar-621`
- Evidence:
  - `reviews/VERIFY-2026-07-23-task-ar-621-20260723161245.json`
<!-- work-close:end -->
