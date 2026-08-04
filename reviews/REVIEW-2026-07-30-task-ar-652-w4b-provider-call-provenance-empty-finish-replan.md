---
schema_version: agent-runtime-review/v1
work_id: TASK-AR-652
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: replan
status: accepted
created_at: 2026-07-30T19:33:00+09:00
reviewer: codex-root-task-ar-652-orchestrator
trigger_ref: reviews/W4B-2026-07-30-unit-task-ar-652-001-provenance-final.md
tags: [task-ar-652, w4b, replan, provider-call-provenance, terminal-success]
---

# TASK-AR-652 provider-call provenance and empty-finish replan

## Bottom Line

The fresh independent W4b verified that the positive success allowlist and
reservation-bound no-provider settlement work for their intended cases, then
reproduced two remaining fail-open boundaries. First, public and adapter
recording paths convert an explicitly empty finish value to `stop`, so the
success predicate never sees the invalid value. Second, a generic skipped
receipt with caller-supplied observed `0 + 0` tokens settles a reservation as
ordinary observed usage without proving that a provider call started. This
replan keeps the current unit, offline boundary, worktree, and active claim,
and makes both success and usage settlement depend on preserved, structured
provenance.

## Reproduced Findings

### Explicit empty finish is promoted to success

`record_execution_receipt`, the native Codex bridge, the worker, auto
dispatch, and the SDK verification adapter use truthiness fallbacks such as
`finish_reason or "stop"`. A completed, error-free receipt supplied with
`finish_reason=""` is therefore stored as `stop` and becomes eligible
economic evidence. The same conversion verifies an otherwise matching
baseline. Whitespace and other nonempty invalid values already fail closed.

### Generic observed zero bypasses no-call provenance

The bridge reserved the complete task and claim ceiling, then wrote a generic
`native_codex_reply` receipt with skipped status and observed zero input and
output tokens. Because observed components are checked before the dedicated
no-provider settlement, cumulative accounting released the reservation. A
fresh Python process then reserved the complete ceiling again. The unavailable
usage control retained the ceiling, and no provider was called in either
fixture.

## Decision

- Preserve finish values exactly at recording boundaries. Omission may remain
  null or unavailable, while an explicitly supplied empty string remains
  empty. Generic constructors and wrappers must not promote either value to a
  successful finish.
- Normalize only inside the positive success predicate and continue admitting
  exactly `stop`, `completed`, `end_turn`, `stop_sequence`, and `success`.
  Empty, missing, whitespace, unknown, nonterminal, tool/action, truncation,
  failure, cancellation, timeout, and skipped values remain non-success.
- Provider adapters may emit a canonical finish only where their concrete
  provider-return contract supplies it. Worker, auto-dispatch, SDK, and bridge
  wrappers must preserve an explicit empty value returned or supplied at
  their boundary.
- Add an immutable `agent-runtime-provider-call-start/v1` ledger record and a
  dedicated recording operation. It must copy one pending reservation's
  dispatch, task, claim, reservation identifier, reservation fingerprint, and
  budget-authority fingerprint, then bind the configured provider, execution
  surface, and a narrow call-source transition.
- Permit only shipped billable-call transitions:
  `auto_dispatch -> auto_dispatch_provider_run`,
  `agent_worker -> agent_worker_provider_run`,
  `verify_sdk_backend -> verify_sdk_provider_run`,
  `codex_subagent_bridge -> native_codex_authorize`, and
  `codex_subagent_council -> native_codex_authorize`.
- Write the marker immediately before each in-process `provider.run`. For the
  native Codex bridge, make the existing mandatory pre-spawn `authorize`
  operation atomically revalidate the reservation and record or return the
  matching idempotent marker immediately before the parent spawn. Apply the
  same rule per council member.
- A marker without a receipt represents a crash or uncertain dispatch and
  leaves the reservation pending. A marker and a no-provider settlement for
  the same dispatch are contradictory and fail ledger validation.
- Classify a reserved receipt as `observed_usage` only when authoritative token
  components, a valid matching call-start marker, a provider-result-compatible
  status, and the expected marker-to-receipt source transition all agree.
  Completed and provider-error paths may retain truly observed usage; skipped
  or other no-call receipts never settle through generic observed usage.
- Bind the marker to receipt provider and execution-surface identity. Missing,
  orphaned, duplicate, replayed, mismatched, malformed, or tampered markers
  fail closed. Caller-supplied stored settlement-basis fields remain
  non-authoritative.
- Keep the dedicated no-provider settlement as the only zero-commit release
  for a call that did not start. Its two legitimate auto-dispatch transitions
  remain unchanged.
- Exclude provider-call markers from user-facing outcome rows while including
  them in ledger integrity and cumulative accounting.
- Regenerate the managed-host lock after packaged Runtime assets change.

## Failure-First Matrix

- Public execution-receipt and native-bridge actual/baseline matrices for
  omitted, explicit empty, whitespace, every unsupported finish class, and all
  five supported success spellings.
- Worker, auto-dispatch, and SDK provider-result controls with explicit empty
  finish, canonical success, provider error, and partial or unavailable usage.
- Direct-ledger and public-bridge skipped `0 + 0` cases without a marker; each
  must retain task and claim ceilings after a true fresh-process read.
- Generic completed or error observed usage without a marker, with a forged
  marker source, or with provider/execution-surface mismatch; each remains
  conservative or raises an integrity error.
- Valid in-process provider completion and observed provider-error controls
  with a matching marker; authoritative usage settles to the observed amount.
- Marker-only crash/restart, marker plus skipped receipt, duplicate marker,
  orphan marker, marker replay, marker/no-provider contradiction, and
  single-field tamper matrices.
- Actual auto-dispatch session-budget and claim-lost no-call branches remain
  zero-call releases through the dedicated settlement. Actual auto-dispatch,
  worker, SDK fixture, bridge authorize, and council authorize call paths emit
  the expected marker exactly once.

## Invariants

- A truthiness fallback can never manufacture terminal success.
- Caller-supplied token components alone do not prove that a provider call
  occurred.
- Missing or contradictory call provenance retains the conservative ceiling;
  it never becomes claimed actual usage.
- A pre-call crash may over-reserve but cannot under-account. A valid observed
  result releases only the unused portion of its matching reservation.
- A valid no-call settlement and a provider-call marker are mutually
  exclusive for one dispatch.
- No live provider, credential, account, dependency, consumer primary,
  database, broker, notification, deploy, push, tag, version, publication, or
  release action is authorized.
- No token or monetary savings claim is made.
- The task claim remains `claimed` until a repaired clean candidate receives a
  new independent W4b approval.

## Verification Plan

1. Record this replan and the blocking W4b in the unit, evidence index, and T3
   assumption snapshot while keeping the claim active.
2. Add the full failure-first finish and provider-call-provenance matrices and
   capture their expected failures before implementation.
3. Implement exact finish preservation, the immutable call-start schema,
   ledger validation, cumulative-accounting binding, in-process call-site
   markers, and native bridge authorize integration.
4. Rerun every prior provider identity, SDK telemetry, terminal-success,
   no-provider settlement, economic assertion, budget/restart, replay,
   role-tier, and equivalence control.
5. Run the required root, template, SDK, taskset, lock, and full Runtime suites
   with credential variables removed.
6. Check Runtime assets, template mirror, host lock, evidence index, taskset
   state, T3 assumptions, root/template parity, compilation, diff, and Owner
   governance.
7. Record a new canonical VERIFY and W4a against exact commits, then submit a
   clean candidate to a fresh independent W4b. Release the claim only after an
   `APPROVE` verdict with no task-scope P0/P1.
