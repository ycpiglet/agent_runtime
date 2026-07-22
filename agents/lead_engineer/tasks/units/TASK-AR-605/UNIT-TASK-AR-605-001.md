---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-605-001
work_uid: 867c3c4e-b1ba-4508-b604-2360a98d4cd7
kind: unit
parent_id: TASK-AR-605
unit_id: UNIT-TASK-AR-605-001
task_id: TASK-AR-605
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
initiative_id: INIT-AR-JULY-RELEASE-IMPACT-REMEDIATION
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead-engineer
created_at: 2026-07-22T17:45:00+09:00
updated_at: 2026-07-22T23:02:21+09:00
started_at: 2026-07-22T22:17:46+09:00
origin_type: downstream_bug
origin_ref: reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
created_by: codex-root-planner
summary: Add a clean-template W0 fallback
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - cross_cutting
  - data_integrity
context: GitHub issue 294 demonstrates that the generated session_dashboard imports repository-only work.py, which the template and host lock do not ship. The fallback must remain read-only and tolerate partial Git/runtime state.
inputs:
  - reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
  - scripts/session_dashboard.py
  - src/agent_runtime/templates/project/scripts/session_dashboard.py
target_files:
  - scripts/session_dashboard.py
  - src/agent_runtime/templates/project/scripts/session_dashboard.py
  - tests/test_session_dashboard.py
  - tests/fixtures/host/agent_runtime.lock.json
scope: Implement a self-contained read-only fallback in the dashboard pair and a clean-template execution test. Do not copy the full repository work CLI into generated hosts.
acceptance:
  - Clean template execution returns structured W0 data without import failure.
  - Fallback failures degrade to explicit read-only notes and exit successfully.
verification:
  - python -m pytest tests/test_session_dashboard.py -q
  - python scripts/regen_host_lock_if_needed.py --check
handoff: Report clean-template output, fallback boundaries, root behavior, and GitHub issue 294 evidence.
stop_condition: Stop before adding repository-only work.py or its transitive dependency graph to the template.
verified_at: 2026-07-22T22:42:06+09:00
verified_by: codex-root-task-ar-605
evidence_refs:
  - reviews/VERIFY-2026-07-22-unit-task-ar-605-001-20260722222914.json
  - reviews/VERIFY-2026-07-22-unit-task-ar-605-001-20260722224206.json
resolution: done
completed_at: 2026-07-22T23:02:21+09:00
closed_by: codex-root
actual_hours: 0.8
actual_tokens: 60000
---

# UNIT-TASK-AR-605-001 - Add a clean-template W0 fallback

## Context

GitHub #294 demonstrates that the generated session_dashboard imports repository-only work.py, which the template and host lock do not ship. The fallback must remain read-only and tolerate partial Git/runtime state.

## Inputs

- reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
- scripts/session_dashboard.py
- src/agent_runtime/templates/project/scripts/session_dashboard.py

## Target Files

- scripts/session_dashboard.py
- src/agent_runtime/templates/project/scripts/session_dashboard.py
- tests/test_session_dashboard.py
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Implement a self-contained read-only fallback in the dashboard pair and a clean-template execution test. Do not copy the full repository work CLI into generated hosts.

## Steps

1. Add a clean-template failure-first test.
2. Implement the bounded fallback while retaining the richer root path.
3. Regenerate the lock and verify parity.

## Acceptance Criteria

- Clean template execution returns structured W0 data without import failure.
- Fallback failures degrade to explicit read-only notes and exit successfully.

## Verification

- `python -m pytest tests/test_session_dashboard.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`

## Handoff

Report clean-template output, fallback boundaries, root behavior, and issue #294 evidence.

## Stop Boundary

Stop before adding repository-only work.py or its transitive dependency graph to the template.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-22T23:02:21+09:00`
- Resolution: `done`
- Actual hours: `0.8`
- Actual tokens: `60000`
- Closed by: `codex-root`
- Evidence:
  - `reviews/VERIFY-2026-07-22-unit-task-ar-605-001-20260722222914.json`
  - `reviews/VERIFY-2026-07-22-unit-task-ar-605-001-20260722224206.json`
<!-- work-close:end -->
