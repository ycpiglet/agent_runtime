---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-03-task-ar-655-w4b-projection-binding-t3-replan
title: TASK-AR-655 W4b projection binding T3 amendment
date: 2026-08-03
created_at: 2026-08-03T04:35:00+09:00
task_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
review_kind: t3-replan
reviewer: codex-root-task-ar-655-orchestrator
reviewer_role: orchestrator
status: accepted
signal: pass
verdict: ACCEPT_W4B_PROJECTION_BINDING_REPAIR
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 0}
candidate_commit: 5c85d7fe5049b6205effafd940cab6df00c47fa4
candidate_tree: 84526eb1597688a22740390d6e11fab9ce790a2c
release_authorized: false
tags: [task-ar-655, t3-replan, w4b, receipt, projection, pointer, fail-closed]
---

# TASK-AR-655 W4b projection binding T3 amendment

## Decision

Accept the independent W4b `REVISE` finding as a current-scope P1. Exact
canonical Compound lookup for
`defect:claim-progress-accepts-non-matching-committed-pr:354921871935cffe`
returned no record with legacy fallback disabled.

The implementation footprint remains bounded to the already registered
orchestrator template and its atomic-write regression file. This amendment
adds only the W4b report, this decision record, lifecycle metadata, and later
append-only verification/Compound/review evidence. It does not authorize a
new subsystem, consumer mutation, or release action.

## Failure-first order

1. Commit the W4b report, this accepted amendment, exact lookup evidence, the
   new defect signature, and verification-failed lifecycle state.
2. Commit a separate test-only RED in
   `tests/test_orchestrator_atomic_writes.py` for a zero-exit response whose
   claim ID/revision are correct but whose path, task/unit/taskset, claim ref,
   current agent, and primary pointer select different authority.
3. Tighten only
   `src/agent_runtime/templates/project/scripts/agent_orchestrator.py` so the
   committed claim, response path, projection, and operation-specific pointer
   form one identity-bound tuple.
4. Preserve exact pass-through of valid committed-with-warning responses and
   the existing bounded indeterminate result for every unverifiable zero-exit.
5. Refresh the installed host lock, rerun the exact RED, full orchestrator
   file, registered suites, mirror/lock checks, and full repository suite.
6. Create one append-only Compound record for the new signature, then produce
   a fresh W4a, a new context-isolated W4b, and a different skeptic review.

## Acceptance contract

- Response `path` and projection `task_claim_ref` equal the canonical claim
  reference `agents/runtime/task_claims/<claim_id>.json`.
- Projection `task_id`, `unit_id`, and `task_set_id` equal the committed claim's
  corresponding values; present values must not be accepted by stringifying a
  conflicting shape.
- A `merge` projection contains one primary pointer for the same task/taskset,
  exactly the same active claim ref, and exactly one current-agent record for
  the same claim, task/unit/taskset, and mutation revision.
- An `overlay-no-primary-pointer` projection has the same claim identity and
  revision but contains no `pointer` key at all.
- Any malformed, missing, duplicated, or conflicting identity makes the
  zero-exit response `claim_progress_receipt_indeterminate`, with non-zero
  outcome, `commit_state=unknown`, and `retry_safe=false`.
- The repair remains read-only at the orchestrator seam; it never synthesizes
  a receipt, retries the mutation, or writes claim/pointer state.

## Preserved boundary

The task and claim remain active, and unit verification returns to failed
pending repair. The Scribe blocker remains unresolved. No merge, claim release,
consumer pilot, CI dispatch, push, tag, version, package, publish, deploy, or
external release is authorized.
