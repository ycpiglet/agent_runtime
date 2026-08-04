---
schema_version: agent-runtime-review/v1
work_id: TASK-AR-652
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: replan
status: accepted
created_at: 2026-07-30T17:25:00+09:00
reviewer: codex-root-task-ar-652-orchestrator
trigger_ref: reviews/W4B-2026-07-30-unit-task-ar-652-001-provider-identity.md
tags: [task-ar-652, w4b, replan, sdk-verifier, telemetry-integrity]
---

# TASK-AR-652 SDK completion-telemetry replan

## Bottom Line

The fresh independent W4b approved the provider-identity matrix and every
earlier economic-routing repair, then found one adjacent P1 in the complete
acceptance range. The live SDK verifier substitutes its selected backend name
when the completion carries no provider telemetry. This replan keeps the
existing unit, target-file footprint, offline boundary, and claim. It adds no
provider integration or production subsystem.

## Reproduced Finding

`verify_sdk_backend._record()` currently evaluates:

```python
str(getattr(result, "provider", "") or "claude")
```

The declared `ProviderResult` and the shipped SDK test completion have no
provider field, so a successful completion is recorded with
`observed_provider="claude"`. The value came from backend selection, not the
completion. The economic gate currently rejects bare `claude`, but the
immutable receipt still mislabels inferred configuration as observation and
violates the unit invariant that actual usage cannot be inferred from request
configuration.

## Decision

- Preserve completion provider telemetry exactly: absent stays null, an
  explicit value remains explicit.
- Record the configured routing provider from `route["provider"]`; never copy
  it into `observed_provider`.
- Do not extend `ProviderResult` or invent provider telemetry in this repair.
  A future adapter may supply a registered identity explicitly, but missing
  and unknown values remain ineligible.
- Add a failure-first SDK receipt test whose successful completion has no
  provider field. It must assert configured provider `claude-agent`, null
  observed provider, and zero token and monetary eligibility.
- Add an explicit matching-provider control and keep it separate from any
  economic-savings claim.
- Rerun the provider-identity matrix and all earlier W4b regression controls
  so a local helper cannot bypass the central receipt gate.

## Invariants

- `provider` means configured route identity; `observed_provider` means
  completion telemetry only.
- Backend selection, provider factory name, route configuration, assertions,
  and request metadata never become observed telemetry.
- Missing or unregistered completion identity cannot support token or
  monetary eligibility.
- No live provider, credential, account, dependency, consumer primary,
  database, broker, notification, deploy, push, tag, version, publication, or
  release is authorized.
- No token or monetary savings claim is made.
- The task claim remains `claimed` until a repaired clean candidate receives
  a new independent W4b approval.

## Verification Plan

1. Run the new SDK telemetry test first and capture the expected failure.
2. Apply the minimal receipt-boundary repair and rerun the focused SDK and
   provider-identity controls.
3. Run the required root, template, SDK, taskset, lock, and full Runtime suites
   with credential variables removed.
4. Check runtime assets, template mirror, managed-host lock, evidence index,
   taskset state, T3 assumptions, parity, compilation, diff, and Owner
   governance.
5. Record a new W4a against the exact implementation commit, then submit a
   clean final candidate to a fresh independent W4b.
