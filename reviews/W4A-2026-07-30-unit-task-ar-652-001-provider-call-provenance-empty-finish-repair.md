---
title: TASK-AR-652 UNIT-001 Provider-Call Provenance and Empty-Finish Repair W4a
date: 2026-07-30
created_at: 2026-07-30T20:04:56+09:00
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
claim_id: CLAIM-20260730-123600-task-ar-652-ar652001
reviewer: le-20260730-123600-kst-ar652001
status: passed
signal: pass
verdict: PASS_PENDING_INDEPENDENT_W4B
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: da4177f6211b2a1a049ba25b62332b113a54cf97
prior_candidate: 450d39eebaaeecf9b1ac99866ea08986fc91d7c4
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001-provenance-final.md
replan: reviews/REVIEW-2026-07-30-task-ar-652-w4b-provider-call-provenance-empty-finish-replan.md
replan_commit: 376cf7f1b8d4730c6849d598d20ddbd525940f78
implementation_commit: 873252354028adb175f1d175173425692fdbb080
implementation_tree: 8997c5b00214c0c27ce1fc4a24fb19ef87261244
verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730200353.json
tags: [w4a, provider-call-provenance, empty-finish, budget-integrity, restart]
---

# TASK-AR-652 UNIT-001 Provider-Call Provenance and Empty-Finish Repair W4a

## Verdict

`PASS_PENDING_INDEPENDENT_W4B — P0: 0, P1: 0, P2: 0.`

Implementation commit
`873252354028adb175f1d175173425692fdbb080`, tree
`8997c5b00214c0c27ce1fc4a24fb19ef87261244`, closes both P1 findings from
the latest independent review. This is worker/orchestrator self-review only.
The claim remains claimed until a fresh independent verifier approves the
exact clean final candidate.

The complete acceptance range is
`da4177f6211b2a1a049ba25b62332b113a54cf97..873252354028adb175f1d175173425692fdbb080`.
The focused repair range is
`376cf7f1b8d4730c6849d598d20ddbd525940f78..873252354028adb175f1d175173425692fdbb080`.

## P1 Closure

Completion provenance is preserved rather than reconstructed through
truthiness:

- `record_execution_receipt()` stores explicit empty finish as `""` and an
  omitted finish as null. Neither becomes a successful `stop`.
- Worker, auto-dispatch, native bridge, council, and SDK wrappers preserve an
  explicit empty result.
- Concrete Claude, Claude Agent, and Codex adapters distinguish an absent
  provider field from an explicitly empty field.
- Actual and baseline finalization therefore admit only the existing positive
  allowlist: `stop`, `completed`, `end_turn`, `stop_sequence`, and `success`.
- Explicit empty, omitted, whitespace, unknown, nonterminal, tool/action,
  truncation, error, cancellation, timeout, and skipped values remain
  economically ineligible.

Observed usage now requires durable call provenance:

- The append-only ledger has a new immutable
  `agent-runtime-provider-call-start/v1` record.
- Each marker binds dispatch, task, claim, reservation ID, complete
  reservation fingerprint, budget-authority fingerprint, provider, execution
  surface, and a narrow reservation-to-call transition.
- Only the shipped worker, auto-dispatch, SDK verification, native bridge, and
  council call transitions are accepted.
- In-process callers append the marker immediately before `provider.run`.
  Native bridge authorization revalidates and records an idempotent marker
  immediately before spawn; council authorization records one per authorized
  member and bulk authorization emits none when any member is denied.
- A marker-only crash remains a pending reservation. A marker and a
  no-provider settlement for the same dispatch are contradictory.
- `observed_usage` settlement requires a matching marker, authoritative token
  components, completed-or-error provider-result status, matching provider and
  execution surface, and the expected marker-to-result source transition.
- Generic skipped or synthetic `0 + 0` receipts without a call marker retain
  the conservative reservation ceiling after a fresh process restart.
- The dedicated no-provider settlement remains the only zero-commit release
  for a dispatch proven not to have started.
- Provider-call markers participate in integrity and cumulative accounting but
  are excluded from user-facing outcome rows.

## Failure-First and Adversarial Evidence

- Before implementation, the new focused matrix produced
  `15 failed, 185 passed`. Failures were confined to explicit-empty finish
  preservation and missing call-start provenance.
- After repair and the council bulk-authorization atomicity control, the
  focused eval/bridge/worker/auto/SDK matrix passes `223`.
- Fresh-process controls cover completed, provider-error, and skipped
  observed usage without a marker; all retain the full task and claim
  commitment.
- Positive controls prove matching completion and provider-error markers
  settle to authoritative observed usage.
- Marker-only restart, marker-plus-skipped, duplicate/idempotent replay,
  conflicting replay, orphan/missing reservation, marker/no-call conflict,
  provider/surface/source mismatch, and fourteen single-field tamper cases
  fail closed or remain conservative.
- Actual worker, auto-dispatch, SDK fixture, native bridge authorization, and
  council authorization paths emit the expected marker exactly once.
- Explicit-empty actual and baseline receipts remain ineligible in the
  finalizer and report, including concrete provider-adapter controls.

## Verification

- Canonical work evidence:
  `reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730200353.json`.
- Required root suite: `108 passed`.
- Required six-module consumer-template suite: `290 passed`.
- SDK fake-provider and adapter suite: `5 passed`.
- Focused repair suite: `223 passed`.
- Taskset governance suite: `12 passed`.
- Managed-host lock suite: `23 passed`; lock check is current.
- Full Runtime suite: `2982 passed, 3 skipped`; the four warnings are the
  pre-existing UI beta invalid-escape warnings.
- In-memory compilation of all eight changed production Python files passed.
- Template mirror remains `84 common / 81 identical / 3 intentional / 0
  findings`.
- Runtime asset usage remains `38 assets / 404 uses / 0 blocks / 0 watches`.
- Evidence index and taskset work gates report zero findings.
- `git diff --check` passed.
- Integrated Owner governance passed at the implementation commit.

All provider paths used fake, dummy, synthetic, or in-memory providers.
Credential variables were removed from verification commands. No credential
value was read and no live provider or network endpoint was called.

No token or monetary savings claim is made. The tests prove evidence
eligibility and conservative budget-accounting behavior only.

## Boundary

No consumer primary, credential, provider account, package, broker, order,
database migration, notification, deployment, remote branch, tag, version,
publication, or release state changed. Independent W4b must approve the exact
clean candidate before claim release or task advancement.
