---
schema_version: agent-runtime-review/v1
work_id: TASK-AR-652
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: replan
status: accepted
created_at: 2026-07-30T17:03:00+09:00
reviewer: codex-root-task-ar-652-orchestrator
trigger_ref: reviews/W4B-2026-07-30-unit-task-ar-652-001-final-candidate.md
tags: [task-ar-652, w4b, replan, provider-identity, savings-integrity]
---

# TASK-AR-652 final-candidate provider-identity replan

## Bottom Line

The fresh independent W4b confirmed that partial route assertions and native
reasoning-source forgery are closed, then found one adjacent P1: the
unsupported-reasoning exception checked provider capability but not provider
identity. This replan keeps the existing unit, footprint, consumer boundary,
and release boundary. It adds no production subsystem.

## Reproduced Finding

For a configured `codex-agent` route with reasoning unsupported, missing,
unknown, or `claude-agent` observed-provider values were accepted for either
the baseline or actual receipt. Each offline pair reported 85 saved tokens and
USD 0.08 saved billed cost. Provider capability equality therefore stood in
for proof that the same provider had been observed.

The same structural defect also existed before the early return for an
observed reasoning effort: missing, unknown, or mismatched provider identity
could be accepted even when reasoning telemetry was populated.

## Decision

- Add a canonical provider identity registry for the supported names.
- Normalize `native-codex`, `codex-session`, and `codex-native` to one native
  identity; normalize `codex` and `codex-agent` to one provider-worker
  identity; retain `claude-agent` as a distinct identity.
- Return no identity for blank or unregistered provider names.
- Validate configured and observed provider identities before every successful
  route-observation result, including the observed-reasoning path.
- Reject missing, unknown, or cross-provider identity.
- Allow absent reasoning only when the matching canonical provider is
  reasoning-unsupported, resolved reasoning is null, and the receipt source
  also says `unsupported`.
- Add baseline and actual negatives for missing, unknown, cross-unsupported,
  and all native aliases, plus reasoning-present negatives and the registered
  `codex`/`codex-agent` alias positive.
- Correct old positive fixtures that used bare `claude`, generic `provider`,
  or omitted provider completion telemetry; no production telemetry is
  inferred from configuration.
- Regenerate the managed fixture host lock for changed packaged scripts.

## Failure-First Evidence

- The new provider-identity matrix first produced `9 failed, 7 passed`.
  Missing, unknown, and cross-unsupported baseline/actual cases plus all three
  reasoning-present cases failed as expected; the existing native-alias
  negatives and canonical alias positive already passed.
- The canonical identity API was absent in both the root and template routing
  suites.
- After repair, the provider matrix passes `16`, and both canonical identity
  selections pass `2`.
- The required template suite exposed nine stale positive fixtures. After
  those fixtures supplied registered configured/observed provider identity,
  the suite passes `193`.

## Invariants

- Completion provider telemetry is never inferred from request configuration.
  Missing telemetry makes economic evidence ineligible.
- Aliases compare equal only when the registry explicitly maps them to the
  same canonical identity.
- No live provider, credential, account, dependency, consumer primary,
  database, broker, notification, deploy, push, tag, version, publication, or
  release is authorized.
- No token or monetary savings claim is made.
- The claim remains `claimed` until a new exact candidate receives independent
  W4b approval.

## Verification Plan

1. Rerun the focused provider-identity and prior P1 controls.
2. Run the required root, six-module template, SDK, taskset, and lock suites.
3. Run the full Runtime suite with credential variables removed.
4. Check runtime assets, mirrors, host lock, evidence index, taskset state,
   T3 assumptions, static parity, and integrated Owner governance.
5. Record W4a against the implementation commit and submit a clean exact
   candidate to a fresh independent W4b.
