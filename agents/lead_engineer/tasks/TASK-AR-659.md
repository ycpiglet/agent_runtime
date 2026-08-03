---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-659
display_id: TASK-AR-659
task_uid: 019fc612-529b-7ee9-9234-9f60a41b5163
work_id: TASK-AR-659
work_uid: 019fc612-529b-7ee9-9234-9f60a41b5163
kind: task
parent_id: TASKSET-AR-V080-OPERABILITY-HARDENING
registered_at: 2026-08-03T14:21:57+09:00
created_at: 2026-08-03T14:21:57+09:00
updated_at: 2026-08-03T14:21:57+09:00
title: Give legacy and orchestrator claims a registered recovery path
status: in_progress
started_at: 2026-08-03T14:31:23+09:00
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260803-143123-task-ar-659-cfc8.json
priority: P1
difficulty: M
est_hours: 8
est_tokens: 16000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-659/UNIT-TASK-AR-659-001.md
reservation_id: RES-20260803-142150-4521fd55-01
origin_type: defect
origin_ref: reviews/RECOVERY-2026-08-03-task-ar-655-owner-claim-terminalize.md
created_by: owner-manual-recovery
summary: Let an owner-identified actor bootstrap, rotate, or terminalize a claim that no automated path can reach, so an expired claim can never deadlock its own task set again.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - allocator-created
  - legacy-claim
  - claim-authority
  - recovery
acceptance:
  - A claim missing mutation_revision or scope_binding can be adopted by a registered owner-bound command instead of becoming unrecoverable.
  - An expired claim can be terminalized by a registered command regardless of mode, without deleting, releasing, or completing it.
  - claim_reaper evaluates status and liveness for orchestrator-mode claims instead of short-circuiting on mode alone.
  - Every recovery command records owner identity, before/after digests, and a reason; an unidentified caller is refused.
  - No recovery command can terminalize a live claim, and none grants unit acceptance or release authority.
  - The recovery path is reachable from the runtime template mirror, not only from this repository.
verification:
  - PYTHONPATH=src python -m pytest tests/test_claim_reaper.py tests/test_claim_store.py tests/test_claim_lease.py tests/test_task_claim_dispatcher.py -q
  - python scripts/rbac_write_gate.py --check
  - python scripts/template_mirror_gate.py --check
---

# TASK-AR-659 - Give legacy and orchestrator claims a registered recovery path

## Goal

- Let an owner-identified actor bootstrap, rotate, or terminalize a claim that no automated path can reach, so an expired claim can never deadlock its own task set again.

## Context

On 2026-08-03 `CLAIM-20260803-002651-task-ar-655-5f27` expired and stayed
`status: claimed` with no registered command able to reach it. Four independent
paths were closed at once:

1. `claim_reaper.py:110` skips `mode == "orchestrator"` **before** testing
   status or liveness, so the claim was never a reap candidate.
2. `heartbeat` and `renew` both reject the claim because it predates the
   `mutation_revision` / `scope_binding` fields
   (`task_claim_dispatcher.py:2581`).
3. Creating a replacement claim is refused by task exclusivity
   (`:2075`, `:2144`) and task-set exclusivity (`:759`).
4. No `expire`, `terminalize`, or `bootstrap` subcommand exists in
   `claim_lease.py` or `task_claim_dispatcher.py`.

The result was a deadlock in which one stale claim blocked both resuming its
own task and claiming the recovery task needed to fix it. It was cleared only
by an Owner-authorized manual mutation, recorded in
`reviews/RECOVERY-2026-08-03-task-ar-655-owner-claim-terminalize.md`. That
manual step is the thing this task exists to make unnecessary.

This is the 4th recurrence in the claim-authority defect family; a Compound
record is required before closeout.

## Scope

- Owner-bound adoption (bootstrap) of pre-mutation-field claims.
- Owner-bound rotation and terminalization for claims no automated path reaches.
- Reaper classification that does not short-circuit on mode.
- Mirror the same surface into the runtime template.

## Out of Scope

- Any network or distributed lease dependency.
- Claim release, unit acceptance, or W4b approval semantics.
- Version, tag, push, publish, deploy, or external release actions.

## Acceptance Criteria

- A claim missing `mutation_revision` or `scope_binding` can be adopted by a registered owner-bound command instead of becoming unrecoverable.
- An expired claim can be terminalized by a registered command regardless of mode, without deleting, releasing, or completing it.
- `claim_reaper` evaluates status and liveness for orchestrator-mode claims instead of short-circuiting on mode alone.
- Every recovery command records owner identity, before/after digests, and a reason; an unidentified caller is refused.
- No recovery command can terminalize a live claim, and none grants unit acceptance or release authority.
- The recovery path is reachable from the runtime template mirror, not only from this repository.

## Verification

- `PYTHONPATH=src python -m pytest tests/test_claim_reaper.py tests/test_claim_store.py tests/test_claim_lease.py tests/test_task_claim_dispatcher.py -q`
- `python scripts/rbac_write_gate.py --check`
- `python scripts/template_mirror_gate.py --check`

`PYTHONPATH=src` is mandatory: the editable install resolves `agent_runtime`
to another worktree's source. `tests/test_claim_guard.py` is excluded — it is
a pre-existing 21 failed / 15 passed baseline on `main` that this task does
not own; see the unit spec.
