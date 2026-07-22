---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-600-001
work_uid: dd1b1933-4a89-4bad-ac82-8a9e0dc94ce1
kind: unit
parent_id: TASK-AR-600
unit_id: UNIT-TASK-AR-600-001
task_id: TASK-AR-600
task_set_id: TASKSET-AR-AUTO-MERGE-INTEGRITY
initiative_id: INIT-AR-AUTO-MERGE-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead_engineer
created_at: 2026-07-19T10:34:25+09:00
updated_at: 2026-07-19T10:34:25+09:00
origin_type: downstream_bug
origin_ref: reviews/REVIEW-2026-07-19-auto-merge-execution-readback.md
created_by: codex-root
summary: Patch auto-merge execution read-back
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: Autofolio BUG-014 reproduced a Draft merge false-success in the managed template helper.
inputs:
  - reviews/REVIEW-2026-07-19-auto-merge-execution-readback.md
  - https://github.com/ycpiglet/agent_runtime/issues/291
target_files:
  - src/agent_runtime/templates/project/scripts/auto_merge.py
  - new:tests/test_auto_merge_execution.py
  - tests/fixtures/host/agent_runtime.lock.json
scope: Template helper and deterministic package regression only.
acceptance:
  - False success is impossible when the remote PR remains OPEN.
  - Remote MERGED read-back is authoritative.
verification:
  - python -m pytest tests/test_auto_merge_execution.py src/agent_runtime/templates/project/scripts/test_auto_merge.py -q
  - python scripts/regen_host_lock_if_needed.py --check
handoff: Report exact head, tests, issue/PR links, rollback, and residual risks.
stop_condition: Stop on workflow, secret, force-push, branch-protection, or unrelated merge-policy changes.
---

# UNIT-TASK-AR-600-001 - Patch auto-merge execution read-back

## Context

Autofolio BUG-014 reproduced a Draft merge false-success in the managed template helper.

## Inputs

- reviews/REVIEW-2026-07-19-auto-merge-execution-readback.md
- https://github.com/ycpiglet/agent_runtime/issues/291

## Target Files

- src/agent_runtime/templates/project/scripts/auto_merge.py
- new:tests/test_auto_merge_execution.py
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Template helper and deterministic package regression only.

## Steps

1. Add failure-first Draft rejection coverage.
2. Implement remote state read-back.
3. Run focused and parity/governance gates.

## Acceptance Criteria

- False success is impossible when the remote PR remains OPEN.
- Remote MERGED read-back is authoritative.

## Verification

- `python -m pytest tests/test_auto_merge_execution.py src/agent_runtime/templates/project/scripts/test_auto_merge.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`

## Handoff

Report exact head, tests, issue/PR links, rollback, and residual risks.

## Stop Boundary

Stop on workflow, secret, force-push, branch-protection, or unrelated merge-policy changes.
