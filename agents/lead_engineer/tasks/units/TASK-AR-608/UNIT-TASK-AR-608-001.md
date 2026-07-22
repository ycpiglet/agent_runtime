---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-608-001
work_uid: be368852-62ad-4c8b-99bd-6a55469032a9
kind: unit
parent_id: TASK-AR-608
unit_id: UNIT-TASK-AR-608-001
task_id: TASK-AR-608
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
initiative_id: INIT-AR-JULY-RELEASE-IMPACT-REMEDIATION
project_id: PROJECT-AGENT-RUNTIME
status: in_progress
verification_status: pending
owner: lead-engineer
created_at: 2026-07-22T17:45:00+09:00
updated_at: 2026-07-23T06:31:27+09:00
started_at: 2026-07-23T06:31:27+09:00
origin_type: downstream_bug
origin_ref: reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
created_by: codex-root-planner
summary: Make frontmatter comment scanning quote-aware
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - data_integrity
  - security
context: GitHub #298 proves the hand-written parser truncates valid quoted YAML scalars at # before scalar parsing. The supported subset needs a small scanner that tracks single/double quote and escape state.
inputs:
  - reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
  - scripts/backlog_board.py
target_files:
  - scripts/backlog_board.py
  - src/agent_runtime/templates/project/scripts/backlog_board.py
  - tests/test_backlog_board_tasksets.py
  - tests/fixtures/host/agent_runtime.lock.json
scope: Replace only lexical comment stripping for the supported frontmatter subset and add adversarial parser tests. Do not introduce a new YAML dependency.
acceptance:
  - PR # markers inside quotes are preserved exactly.
  - Outside-quote comments are still removed.
  - Root/template parsers remain identical.
verification:
  - python -m pytest tests/test_backlog_board_tasksets.py -q
  - python scripts/regen_host_lock_if_needed.py --check
handoff: Report the supported scanner grammar, adversarial cases, parity, and issue #298 evidence.
stop_condition: Stop before expanding the parser into a general YAML implementation.
---

# UNIT-TASK-AR-608-001 - Make frontmatter comment scanning quote-aware

## Context

GitHub #298 proves the hand-written parser truncates valid quoted YAML scalars at # before scalar parsing. The supported subset needs a small scanner that tracks single/double quote and escape state.

## Inputs

- reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
- scripts/backlog_board.py

## Target Files

- scripts/backlog_board.py
- src/agent_runtime/templates/project/scripts/backlog_board.py
- tests/test_backlog_board_tasksets.py
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Replace only lexical comment stripping for the supported frontmatter subset and add adversarial parser tests. Do not introduce a new YAML dependency.

## Steps

1. Add failure-first quoted-hash, escape, list, and malformed-input cases.
2. Implement a quote-aware comment scanner in the root/template pair.
3. Run parity and lock verification.

## Acceptance Criteria

- PR # markers inside quotes are preserved exactly.
- Outside-quote comments are still removed.
- Root/template parsers remain identical.

## Verification

- `python -m pytest tests/test_backlog_board_tasksets.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`

## Handoff

Report the supported scanner grammar, adversarial cases, parity, and issue #298 evidence.

## Stop Boundary

Stop before expanding the parser into a general YAML implementation.
