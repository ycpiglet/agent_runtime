---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-605
display_id: TASK-AR-605
task_uid: 010bff90-0ade-47e2-8434-244ec1de9482
work_id: TASK-AR-605
work_uid: 010bff90-0ade-47e2-8434-244ec1de9482
kind: task
parent_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
registered_at: 2026-07-22T17:45:00+09:00
created_at: 2026-07-22T17:45:00+09:00
updated_at: 2026-07-22T23:02:22+09:00
started_at: 2026-07-22T22:17:46+09:00
title: Make the generated session dashboard self-contained
status: completed
priority: P1
difficulty: M
est_hours: 3
est_tokens: 10000
owner: lead-engineer
initiative_id: INIT-AR-JULY-RELEASE-IMPACT-REMEDIATION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-605/UNIT-TASK-AR-605-001.md
reservation_id: RES-20260722-174500-dbaf8585-03
origin_type: downstream_bug
origin_ref: reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
created_by: codex-root-planner
summary: Close GitHub issue 294 by making the template W0 dashboard work when repository-only scripts/work.py is absent.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python -m pytest tests/test_session_dashboard.py -q
  - python scripts/regen_host_lock_if_needed.py --check
tags:
  - github-294
  - generated-host
  - session-dashboard
verification_status: passed
verified_at: 2026-07-22T22:42:20+09:00
verified_by: codex-root-task-ar-605
evidence_refs:
  - reviews/VERIFY-2026-07-22-task-ar-605-20260722224220.json
resolution: done
completed_at: 2026-07-22T23:02:22+09:00
closed_by: codex-root
actual_hours: 0.8
actual_tokens: 60000
---

# TASK-AR-605 - Make the generated session dashboard self-contained

## Goal

- Close GitHub #294 by making the template W0 dashboard work when repository-only scripts/work.py is absent.

## Scope

- Close GitHub #294 by making the template W0 dashboard work when repository-only scripts/work.py is absent.

## Acceptance Criteria

- A clean generated template runs session_dashboard.py without ModuleNotFoundError.
- The dashboard provides a useful read-only W0 fallback without mutating host state.
- Repository-root behavior remains unchanged when work.py is available.

## Verification

- `python -m pytest tests/test_session_dashboard.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-22T23:02:22+09:00`
- Resolution: `done`
- Actual hours: `0.8`
- Actual tokens: `60000`
- Closed by: `codex-root`
- Evidence:
  - `reviews/VERIFY-2026-07-22-task-ar-605-20260722224220.json`
<!-- work-close:end -->
