---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-606
display_id: TASK-AR-606
task_uid: 5ef12a21-e069-4194-b418-2eb64abb7e34
work_id: TASK-AR-606
work_uid: 5ef12a21-e069-4194-b418-2eb64abb7e34
kind: task
parent_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
registered_at: 2026-07-22T17:45:00+09:00
created_at: 2026-07-22T17:45:00+09:00
updated_at: 2026-07-23T00:04:40+09:00
started_at: 2026-07-22T23:17:20+09:00
title: Activate configured pre-commit hooks on POSIX hosts
status: completed
priority: P1
difficulty: M
est_hours: 2
est_tokens: 8000
owner: lead-engineer
initiative_id: INIT-AR-JULY-RELEASE-IMPACT-REMEDIATION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-606/UNIT-TASK-AR-606-001.md
reservation_id: RES-20260722-174500-dbaf8585-04
origin_type: downstream_bug
origin_ref: reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
created_by: codex-root-planner
summary: Close GitHub issue 295 by preserving executable hook activation in source and repairing it during installation.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python -m pytest tests/test_lock_merge_driver.py tests/test_bootstrap_dev_env.py -q
  - python scripts/regen_host_lock_if_needed.py --check
  - git ls-files -s .githooks/pre-commit src/agent_runtime/templates/project/.githooks/pre-commit
tags:
  - github-295
  - git-hooks
  - governance
verification_status: passed
verified_at: 2026-07-22T23:49:57+09:00
verified_by: codex-root-task-ar-606
evidence_refs:
  - reviews/VERIFY-2026-07-22-task-ar-606-20260722232457.json
  - reviews/VERIFY-2026-07-22-task-ar-606-20260722233631.json
  - reviews/VERIFY-2026-07-22-task-ar-606-20260722234957.json
resolution: done
completed_at: 2026-07-23T00:04:40+09:00
closed_by: codex-root
actual_hours: 0.8
actual_tokens: 75000
---

# TASK-AR-606 - Activate configured pre-commit hooks on POSIX hosts

## Goal

- Close GitHub #295 by preserving executable hook activation in source and repairing it during installation.

## Scope

- Close GitHub #295 by preserving executable hook activation in source and repairing it during installation.

## Acceptance Criteria

- The root and template pre-commit hooks are executable in Git metadata.
- Install/bootstrap repairs missing POSIX executable permission idempotently.
- Windows remains supported and hook bodies are unchanged.

## Verification

- `python -m pytest tests/test_lock_merge_driver.py tests/test_bootstrap_dev_env.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`
- `git ls-files -s .githooks/pre-commit src/agent_runtime/templates/project/.githooks/pre-commit`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-23T00:04:40+09:00`
- Resolution: `done`
- Actual hours: `0.8`
- Actual tokens: `75000`
- Closed by: `codex-root`
- Evidence:
  - `reviews/VERIFY-2026-07-22-task-ar-606-20260722232457.json`
  - `reviews/VERIFY-2026-07-22-task-ar-606-20260722233631.json`
  - `reviews/VERIFY-2026-07-22-task-ar-606-20260722234957.json`
<!-- work-close:end -->
