---
schema_version: agent-runtime-review/v1
id: AUDIT-2026-08-03-task-ar-655-heartbeat-expiry-consumers
title: TASK-AR-655 heartbeat, renewal, and expiry-consumer audit
date: 2026-08-03
created_at: 2026-08-03T01:22:02+09:00
task_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
review_kind: audit
reviewer: codex-ar655-heartbeat-expiry-audit-council-20260803
reviewer_role: independent-auditor
status: completed
signal: fail
verdict: REVISE_SCOPE_BEFORE_HEARTBEAT_RED
priority: P1
finding_counts: {P0: 0, P1: 7, P2: 4}
candidate_commit: 0c3048ae5acd877ca8f6cc949ae66b69decb9cd7
candidate_tree: 018a483df964bd2b6e8582f890f2a9eb02803647
release_authorized: false
tags: [task-ar-655, heartbeat, renewal, expiry, pointer, ui, doctor, failure-to-regression]
---

# TASK-AR-655 heartbeat, renewal, and expiry-consumer audit

## Outcome

The bounded lease/grace repair is verified and compounded, but the original
AR-655 heartbeat/renewal acceptance still has no implementation. Two
independent read-only audits found no destructive P0 path and found seven P1
contract gaps. The unit footprint must be amended before the next RED commit.

Exact canonical Compound lookup, with legacy lookup disabled, returned `[]`
for all four newly registered defect signatures before any new RED test was
written:

- `defect:task-claim-progress-outlives-unrenewed-lease:9dae21269ca06d88`
- `defect:expired-task-claim-appears-live-across-runtime-c:39f0d2087c60993c`
- `defect:concurrent-task-claim-renewal-overwrites-newer-o:c22a19adb1ea01e9`
- `defect:task-claim-renewal-silently-broadens-scope-witho:972c3033ed564ed9`

## P1 findings

### No task-claim heartbeat or renewal authority exists

`task_claim_dispatcher.py` exposes only `create`, `projection`, and `release`.
The claim repeats authoritative lifecycle values across top-level
`last_heartbeat`, `updated_at`, `expires_at` and nested
`lease.heartbeat_at`, `lease.expires_at`, but there is no owner-checked path
that updates them together. Long-running progress therefore outlives the
recorded lease.

### Concurrent progress has no compare-and-swap token

The claim has no mutation revision. A store lock serializes file writes, but
without a caller-supplied expected revision a delayed writer can still acquire
the lock later and overwrite newer progress. The new path needs an integer
revision CAS in addition to exact claim, instance, and callsite ownership.

### Renewal scope is not bound to a replan

The current task, unit identity/spec, target-file footprint, and stop boundary
are plain fields with no canonical digest. A future renewal could extend or
broaden authority without proving what changed. Create needs a baseline scope
binding; renewal needs old/new component digests and a direct accepted replan
reference whenever any bound component changes.

### Claim, pointer, instance, and event timestamps cannot be reconciled

`projection` emits status-active claims even after raw expiry. A claim-only
progress write would make `NEXT-SESSION-POINTER.yml` stale because the parallel
continuity gate compares its `current_agents` projection with claim progress
and heartbeat fields. `agent_instance_registry.build_instance_record()` also
derives `updated_at` from `claimed_at`, so re-recording an existing instance
does not advance it. A mutation response needs one structured receipt
containing the committed claim revision, fresh serial-owner projection,
instance result, pane heartbeat event, and post-commit warnings.

### Expiry interpretations disagree across read surfaces

At one fixed `now` and 600-second grace, the reaper uses the latest valid
top/nested deadline, state sync and parallel gates use status only, UI presents
status-active claims online, and worktree lifecycle uses the first parseable
deadline with no grace. This produces all of the following contradictions:

- a grace-exceeded claim is dead to the reaper but active/online elsewhere;
- a claim inside grace is live to the reaper but stale to lifecycle cleanup;
- stale top-level plus future nested expiry is live to the reaper but stale to
  lifecycle cleanup; and
- malformed or missing expiry is skipped by the reaper but silently active on
  other surfaces.

### Doctor can report an expired task claim as healthy

Doctor checks claim-store markers and imports parallel continuity output, but
does not classify task-claim expiry or validate every canonical claim payload.
A valid marker pair with a malformed non-witness claim can therefore pass the
marker inspection, and an expired status-active claim can inherit a healthy
continuity result.

### The console recomputes WIP from raw status

The server UI state can be corrected while the browser home summary still
counts raw status-active `task_claims`. The browser must consume the
server-derived liveness/authority flag rather than maintain another status
vocabulary.

## P2 findings

- The unit registers template `agent_orchestrator.py` but omits its test. The
  template has no claim-progress command and its legacy `TASK_RE` vocabulary
  is unrelated to canonical `TASK-AR-*` identity.
- The instance registry source/template pair and identity test are absent from
  the footprint even though the acceptance requires a reconciled instance
  timestamp.
- Doctor source/tests and UI console source/tests are absent despite explicit
  task acceptance.
- Many lifecycle-neutral transport, dispatch, conflict, and Scribe consumers
  intentionally retain status authority until the reaper performs a terminal
  transition. They must not be changed to auto-discard an expired claim in this
  unit; expiry presentation and blocking belong to the registered surfaces.

## Required shared liveness contract

Add a pure classifier to all three byte-identical `agent_runtime.claim_store`
copies. It must return `inactive`, `live`, `expired`, or `indeterminate` with a
reason, effective deadline, source list, and bounded findings.

- Only canonical active/inactive status vocabularies are authoritative.
- Parse only timezone-aware ISO-8601 timestamps; never guess a timezone.
- Use the later valid value of top-level and nested expiry, and expose a
  mismatch finding.
- Missing, partial, malformed, or naive active deadlines are indeterminate:
  retain authority conservatively and expose degraded/blocking evidence.
- Equality, including positive-grace equality, is live.
- Preserve the existing environment rule: absent/malformed grace is 600;
  negative environment grace normalizes to zero.
- Keep orchestrator and overlay policy outside the pure classifier.

## Required mutation contract

- `heartbeat` requires exact claim id, agent instance id, callsite id, expected
  revision, and a strictly increasing aware timestamp.
- It rejects inactive, overlay, expired, mismatched, malformed, or stale-CAS
  authority without mutation. Equality with expiry remains live.
- It extends the existing positive lease duration and atomically updates both
  heartbeat/expiry copies, `updated_at`, progress fields, and revision in one
  JSON replacement.
- `renew` additionally requires a positive lease duration and expected scope
  digest. It writes old/new scope bindings and refuses any scope change without
  a direct accepted T2/T3 replan tied to the same task/unit.
- Claim authority commits once. Instance and pane-event work occurs after the
  store lock and is reported as success or bounded warning; callers must not
  blindly retry a committed mutation.
- Neither command writes the pointer or Git state. It returns a fresh
  projection for the serial projection owner.

## RED matrix

The next test-only commit must cover owner/callsite mismatch, inactive and
expired claims, timestamp regression, equal/concurrent revisions, atomic write
failure, top/nested mismatch, progress coherence, unchanged-scope renewal,
replan-bound scope change, silent broadening refusal, instance/event partial
failure receipts, and a cross-surface expiry matrix spanning reaper, state
sync, parallel continuity, lifecycle, UI, console-derived WIP, and Doctor.

No claim release, CI dispatch, versioning, tag, push, publish, deployment, or
external release action is authorized.
