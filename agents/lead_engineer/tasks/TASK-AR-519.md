---
id: TASK-AR-519
display_id: TASK-AR-519
task_uid: f9b99655-ff0b-4e94-a3c4-e060b1a04bdc
registered_at: 2026-06-12T23:35:00+09:00
created_at: 2026-06-12T23:35:00+09:00
updated_at: 2026-06-13T11:20:00+09:00
started_at: 2026-06-13T02:45:17+09:00
completed_at: 2026-06-13T11:20:00+09:00
title: Verification freshness and stale evidence gate
status: completed
priority: P1
difficulty: M
est_hours: 8
est_tokens: 6000
owner: lead_engineer
initiative_id: INIT-AR-WORK-METADATA-ANALYTICS
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-WORK-METADATA-ANALYTICS
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
escalation_triggers:
  - verification_gap
  - stale_evidence
tags:
  - verification
  - freshness
  - stale-evidence
  - gate
---

# Verification freshness and stale evidence gate

## Goal
- Mark verification evidence stale when source files, commits, claims, or task records move after verification, and block closeout when stale evidence is unresolved.

## Context

- Owner wants measurable verification before/after work, not success claims from
  stale or unrelated signals.
- Existing evidence registries store command evidence, but freshness against
  later file/commit/task movement is still incomplete.

## Scope

- Define freshness inputs: source file hashes or mtimes, commit refs,
  task/claim updated_at, verification command, verifier instance, and
  verified_at.
- Mark verification stale when relevant inputs change after verification.
- Block or watch closeout when a task relies on stale evidence.
- Feed stale status into Work Explorer and work stats.

## Out Of Scope

- Re-running every historical verification command.
- Provider-live evidence unless credentials are configured.

## Acceptance Criteria

- Fixture evidence becomes stale after changing a referenced source.
- Fresh evidence passes until a tracked input moves.
- Closeout gate reports stale evidence with task/evidence/source refs.

## Evidence Targets

- Freshness gate + tests.
- Evidence registry schema update.
- Closeout review with stale/fresh fixture proof.

## Completion Evidence

- PR #68 (b77edab): verification_freshness_gate.py with strong/advisory signal model, block only for strong+open; registry README freshness schema; chain wiring + mirror; 11 tests.

## Verification Results

- pytest tests/test_verification_freshness_gate.py -q -> 11 passed
- verification_freshness_gate --check (real repo) -> exit 0, records=12 legacy watch
- pytest tests -q -> 595 passed (+1 pre-existing)
- W4b inst-w4b-ar519-verifier -> APPROVE
