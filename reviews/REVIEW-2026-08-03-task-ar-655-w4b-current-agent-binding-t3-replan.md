---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-03-task-ar-655-w4b-current-agent-binding-t3-replan
title: TASK-AR-655 W4b Current-Agent Binding T3 Recurrence Amendment
date: 2026-08-03
created_at: 2026-08-03T05:16:54+09:00
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
verdict: ACCEPT_W4B_CURRENT_AGENT_BINDING_REPAIR
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 0}
candidate_commit: b78f484d6e599d3ef1e376d1d6fe3b945f98906e
candidate_tree: d13684d7f47d92f8f95b704a2b0a6f58c4ccbd22
defect_signature: defect:claim-progress-accepts-non-matching-committed-pr:354921871935cffe
recurrence_status: canonical_match_found_pre_red
matched_compound: agents/project/knowledge/compounds/records/COMPOUND-20260803-050159-bind-claim-progress-projection-to-committed-clai-2398011ac247.json
release_authorized: false
tags: [task-ar-655, t3-replan, w4b, recurrence, current-agent, claim-path, status, identity, fail-closed]
---

# TASK-AR-655 W4b current-agent binding T3 recurrence amendment

## Decision

Accept the new context-isolated W4b `REVISE` finding as a current-scope P1.
The exact canonical search for
`defect:claim-progress-accepts-non-matching-committed-pr:354921871935cffe`
returned one existing mitigated record with legacy fallback disabled. This is
a recurrence of the same matching-projection defect, not a new unrelated
signature: the prior prevention bound the outer projection tuple but did not
bind all primary-pointer current-agent authority required by registered
consumers.

The existing Compound record remains immutable. After a fresh GREEN Verify,
create a new append-only record for the same signature with recurrence count
`2`, cite both W4b findings, and record the strengthened prevention. Do not
rewrite or supersede the prior record in place.

## Failure-first order

1. Commit the new W4b, this accepted amendment, the canonical-match result,
   and verification-failed lifecycle state.
2. Commit a separate test-only RED matrix in
   `tests/test_orchestrator_atomic_writes.py` for zero-exit merge responses
   with missing/conflicting current-agent `claim_path`, missing/conflicting
   current-agent `status`, and present empty optional unit/task-set identity.
3. Tighten only the registered orchestrator validator so a merge current-agent
   is the complete authority tuple required by the primary-pointer consumer:
   canonical claim path, active status equal to the committed claim, non-empty
   present identities, same claim/task/unit/taskset, and exact revision.
4. Import or reuse the canonical active claim-status set rather than creating
   a divergent lifecycle vocabulary. Preserve intentional `null` optional
   unit/task-set semantics and pointer-free overlay behavior.
5. Preserve the bounded indeterminate result for every unverifiable zero-exit,
   exact pass-through for valid normal and committed-with-warning responses,
   and no orchestrator-side mutation or retry.
6. Refresh the managed host lock and rerun the RED, full orchestrator file,
   registered suites, mirror/lock checks, and complete repository suite.
7. Append the recurrence Compound, then produce a replacement W4a, a new
   context-isolated W4b, and only after its pass a different skeptic review.

## Acceptance contract

- A present optional `unit_id` or `task_set_id` is a non-empty, exact-trimmed,
  bounded string; intentional absence remains `null`.
- The committed claim status is a canonical active claim status.
- A merge `current_agents` list still contains exactly one mapping, and that
  mapping's `claim_path` equals the same canonical claim ref required from the
  response, projection, and pointer active-claim list.
- The merge current-agent `status` is present, canonical, active, and exactly
  equals the committed claim status.
- Claim ID, task/unit/taskset, and exact committed revision remain bound as in
  the first repair. All prior gross mismatch and overlay regressions stay
  green.
- Missing, malformed, empty, duplicated, stale, or conflicting current-agent
  authority yields exit `2`, `claim_progress_receipt_indeterminate`,
  `commit_state: unknown`, and `retry_safe: false` without mutation.

## Preserved boundary

The active claim remains held and unit verification returns to failed pending
the recurrence repair. The Scribe source-debt and active-coverage blocker
remains unresolved and unwaived. No skeptic, claim release, task close, merge,
consumer pilot, CI dispatch, push, tag, version, package, publication,
deployment, or external release action is authorized.
