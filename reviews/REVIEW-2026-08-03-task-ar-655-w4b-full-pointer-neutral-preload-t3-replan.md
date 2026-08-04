---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-03-task-ar-655-w4b-full-pointer-neutral-preload-t3-replan
title: TASK-AR-655 W4b Full-Pointer and Neutral Pre-load T3 Amendment
date: 2026-08-03
created_at: 2026-08-03T06:30:10+09:00
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
verdict: ACCEPT_W4B_FULL_POINTER_AND_NEUTRAL_PRELOAD_REPAIR
priority: P1
finding_counts: {P0: 0, P1: 2, P2: 0}
candidate_commit: 5b6a5a9fddccd318fc6f8a813ddc1ab42f036ebb
candidate_tree: b956ec4edc5a705423704f49b191d9598b1112f5
projection_defect_signature: defect:claim-progress-accepts-non-matching-committed-pr:354921871935cffe
projection_recurrence_status: two_canonical_matches_found_pre_red
ui_defect_signature: defect:ui-console-pre-load-summary-fabricates-healthy-z:e18e21bcf63e1ade
ui_compound_lookup_status: clear_no_legacy
release_authorized: false
tags: [task-ar-655, t3-replan, w4b, recurrence, pointer-agent, ui, preload, truthfulness, fail-closed]
---

# TASK-AR-655 W4b full-pointer and neutral pre-load T3 amendment

## Decision

Accept both findings from the context-isolated post-repair W4b as
current-scope P1 defects. The candidate correctly repairs the named
current-agent path/status cases and the null dereference, but it does not yet
meet the already registered downstream contracts.

The first finding remains the same canonical projection-binding defect:
`defect:claim-progress-accepts-non-matching-committed-pr:354921871935cffe`.
Exact search with legacy fallback disabled returned two mitigated records at
recurrence counts 1 and 2. The validator binds seven identity fields plus
revision but accepts missing or conflicting values for the other sixteen
fields required by the canonical pointer consumer. After repair and fresh
Verify, add a third immutable record for this same signature with recurrence
count `3`; do not rewrite either predecessor.

The second finding has a different mechanism and observable failure from the
registered null-dereference signature. The page no longer throws, but a null
Runtime state is rendered as factual-looking healthy zeros. The deterministic
new signature
`defect:ui-console-pre-load-summary-fabricates-healthy-z:e18e21bcf63e1ade`
returned no canonical record with legacy fallback disabled. Register it
separately and append its first Compound record only after GREEN Verify.

## Failure-first order

1. Commit the W4b report, this accepted amendment, exact lookup results, new
   UI signature, expanded acceptance, and verification-failed lifecycle state.
2. Commit a test-only RED matrix built from the production dispatcher
   projection shape. Remove and conflict each complete canonical pointer-agent
   field individually and require exit `2`, indeterminate/unknown/non-retryable
   receipt semantics, and byte-identical claim and pointer sentinels.
3. Commit browser RED coverage for desktop and mobile with inbox rendering
   before a delayed `/api/state`, plus a failed-state response. Before state
   exists, assert no page error and no factual `pass`, `0`, `idle`, WIP, or flow
   values; after arrival, assert real state replaces the neutral presentation.
4. Put the canonical pointer-agent field tuple in the shared claim-store
   contract used by dispatcher, pointer gate, and orchestrator. Preserve the
   producer's supplementary routing metadata, but require every canonical
   field to be present and exactly equal to the committed claim or claim path.
5. Keep overlay receipts pointer-free and preserve every earlier bounded
   indeterminate, exact revision, active status, optional identity, no-mutation,
   and valid pass-through contract.
6. While `runtimeState` is null, clear or hide state-derived verdict, summary,
   and flow facts. Keep the freshness clock neutral and do not convert absent
   state into zeros or a healthy verdict. Once state arrives, render the same
   real metrics and timestamp precedence as before.
7. Refresh managed mirrors and the host lock, then run the exact REDs, complete
   orchestrator and UI suites, registered verification chain, and full suite.
8. Run fresh official Verify; append projection recurrence count `3` and the
   first UI truthfulness Compound; restore exact signature coverage; then
   produce replacement W4a and another context-isolated W4b. A skeptic is
   allowed only after that W4b passes.

## Acceptance contract

- A merge projection's sole `current_agents` record contains every field in
  the canonical shared pointer-agent tuple and every value equals the same
  committed claim, with `claim_path` equal to the canonical claim ref.
- The dispatcher producer, pointer consumer, and orchestrator validator use
  one shared field contract; a manually divergent third list is not accepted.
- Missing, empty, malformed, stale, or conflicting canonical fields yield exit
  `2`, `claim_progress_receipt_indeterminate`, `commit_state: unknown`, and
  `retry_safe: false`, without claim or pointer mutation.
- Valid full merge and pointer-free overlay receipts retain their existing
  success behavior, supplementary projection metadata, and exact revision.
- Before initial Runtime state is available, desktop and mobile show a neutral
  or explicit loading/unavailable summary with no factual healthy zero, pass,
  idle, WIP, throughput, or cycle claims and no browser exception.
- A failed state request leaves the neutral summary in place and exposes the
  existing error signal; a delayed successful request replaces it with the
  real blocked/active metrics.
- `built_at`, then `generated_at`, retains its precedence and stale-age
  semantics after state arrival.

## Preserved boundary

Unit verification returns to failed and the active claim remains held. Exact
Compound coverage will temporarily be 13 of 14 until the new UI truthfulness
record is appended; that does not waive the separate projection recurrence
record. The Scribe source-debt and active-coverage blocker remains unresolved
and unwaived. No skeptic, claim release, task close, merge, consumer pilot, CI
dispatch, push, tag, version, package, publication, deployment, or external
release action is authorized.
