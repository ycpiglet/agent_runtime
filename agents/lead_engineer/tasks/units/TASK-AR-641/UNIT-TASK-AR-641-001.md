---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-641-001
work_uid: fbff3d52-fbaa-4ecf-8efd-78dd695aeea6
kind: unit
parent_id: TASK-AR-641
unit_id: UNIT-TASK-AR-641-001
task_id: TASK-AR-641
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: in_progress
verification_status: pending
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T20:54:00+09:00
started_at: 2026-07-28T20:54:00+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Implement read-only brownfield adoption planner
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: Current main has config v2 diagnostics but no adoption module or CLI. At W0, Bean Wiki inventory included 11,136 files and Allimbot 2,926, while normal doctor reported installation absence as nineteen blockers for each. Both pilot worktrees are dirty and must remain read-only.
inputs:
  - src/agent_runtime/inventory.py
  - src/agent_runtime/doctor.py
  - src/agent_runtime/cli.py
  - src/agent_runtime/config.py
  - reviews/REVIEW-2026-07-28-task-ar-641-w0-t3-replan.md
  - Bean Wiki and Allimbot preflight counts
target_files:
  - src/agent_runtime/adoption.py
  - src/agent_runtime/inventory.py
  - src/agent_runtime/doctor.py
  - src/agent_runtime/cli.py
  - tests/test_adoption.py
  - tests/test_inventory_sync_sanitize.py
  - tests/test_doctor.py
scope: Produce a deterministic, read-only adoption plan; use Git-native ignore evaluation with a conservative no-Git fallback; filter generated trees; detect host assets; and add a separate pre-adoption doctor mode. Do not apply changes, repair a host, or modify Bean Wiki or Allimbot.
acceptance:
  - Plan output is stable across repeated runs.
  - Generated dependency/build trees do not appear as host conflicts.
  - No file is written during adopt --plan.
  - Every proposed mutation names ownership and reason.
  - Missing Agent Runtime files are not broken-installation blockers in doctor --pre-adoption, while normal doctor remains strict.
  - Bean Wiki and Allimbot path-shape fixtures preserve source-visible instructions, agents, skills, and product documents.
verification:
  - python -m pytest tests/test_adoption.py tests/test_inventory_sync_sanitize.py tests/test_doctor.py -q
handoff: Attach Bean Wiki and Allimbot before/after inventory counts, sample ownership plans, repeated-run stability, and file-list/content/mtime immutability evidence.
stop_condition: Stop before adopt --apply, profile manifests, ownership-aware sync, seed/generated transitions, adapter execution, or any host file modification.
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260728-205400-task-ar-641-641001.json
---

# UNIT-TASK-AR-641-001 - Implement read-only brownfield adoption planner

## Context

Current inventory produced thousands of review entries for Bean Wiki and Allimbot because generated trees were treated as source, while doctor reported installation absence as nineteen blockers instead of an adoption plan.

## Inputs

- src/agent_runtime/inventory.py
- src/agent_runtime/doctor.py
- src/agent_runtime/cli.py
- src/agent_runtime/config.py
- reviews/REVIEW-2026-07-28-task-ar-641-w0-t3-replan.md
- Bean Wiki and Allimbot preflight counts

## Target Files

- src/agent_runtime/adoption.py
- src/agent_runtime/inventory.py
- src/agent_runtime/doctor.py
- src/agent_runtime/cli.py
- tests/test_adoption.py
- tests/test_inventory_sync_sanitize.py
- tests/test_doctor.py

## Scope

Produce a deterministic, read-only adoption plan. Use Git-native ignore
evaluation with a conservative no-Git fallback, filter generated trees,
detect host assets, and add a separate pre-adoption doctor path. Do not apply
changes, repair a host, or modify Bean Wiki or Allimbot.

## Steps

1. Add generated and VCS-ignore aware inventory filtering.
2. Classify existing host harness assets.
3. Compute effective profile file set and ownership actions.
4. Expose text and JSON adopt plans plus pre-adoption doctor mode.

## Acceptance Criteria

- Plan output is stable across repeated runs.
- Generated dependency/build trees do not appear as host conflicts.
- No file is written during adopt --plan.
- Every proposed mutation names ownership and reason.
- Missing runtime files are not broken-installation blockers in
  `doctor --pre-adoption`, while normal doctor remains strict.
- Bean Wiki and Allimbot path-shape fixtures preserve source-visible
  instructions, agents, skills, and product documents.

## Verification

- `python -m pytest tests/test_adoption.py tests/test_inventory_sync_sanitize.py tests/test_doctor.py -q`

## Handoff

Attach Bean Wiki and Allimbot before/after inventory counts, sample ownership
plans, repeated-run stability, and file-list/content/mtime immutability
evidence.

## Stop Boundary

Stop before `adopt --apply`, profile manifests, ownership-aware sync,
seed/generated transitions, adapter execution, or any host file modification.
