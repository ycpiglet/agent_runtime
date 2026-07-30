---
title: TASK-AR-653 Invalid Runtime Config Fail-closed Repair W4a
date: 2026-07-31
created_at: 2026-07-31T03:36:35+09:00
task_id: TASK-AR-653
unit_id: UNIT-TASK-AR-653-001
claim_id: CLAIM-20260730-234934-task-ar-653-ar653004
status: passed
signal: pass
verdict: PASS_PENDING_FRESH_INDEPENDENT_W4B
priority: P1
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: ae998f7b3b96def7347be7317e3cadda6078150f
blocking_evidence_commit: a904ae8960420f125cb2c5bc8c46d12b717bbcd0
repair_parent: a904ae8960420f125cb2c5bc8c46d12b717bbcd0
reviewed_commit: ee7d0a8569f835b16b6ca8e1938db34f25628fa0
reviewed_tree: 408a3a18e3da964e671db6f7bf49fae904d53213
complete_review_range: ae998f7b3b96def7347be7317e3cadda6078150f..ee7d0a8569f835b16b6ca8e1938db34f25628fa0
repair_range: a904ae8960420f125cb2c5bc8c46d12b717bbcd0..ee7d0a8569f835b16b6ca8e1938db34f25628fa0
worker_identity: le-20260730-234934-kst-ar653004
revise_w4b: reviews/W4B-2026-07-31-unit-task-ar-653-001-configured-source-integrity-final.md
verification_evidence: reviews/VERIFY-2026-07-31-unit-task-ar-653-001-20260731033533.json
claim_disposition: remain_claimed_pending_fresh_independent_w4b
tags: [w4a, scribe, config-invalid, source-integrity, fail-closed, closure-gate, repair, regression]
---

# TASK-AR-653 Invalid Runtime Config Fail-closed Repair W4a

## Verdict

`PASS_PENDING_FRESH_INDEPENDENT_W4B — P0: 0, P1: 0, P2: 0.`

Implementation commit
`ee7d0a8569f835b16b6ca8e1938db34f25628fa0` closes the remaining
configuration-loader bypass. When a present `agent_runtime.yml` cannot be
loaded, its preserved `config-invalid` finding now also identifies
`agent_runtime.yml` as unavailable source-integrity debt. Readiness blocks and
the existing substantial Scribe closure obligation names the configuration
path and required repair.

This is worker self-review, not independent acceptance. Claim
`CLAIM-20260730-234934-task-ar-653-ar653004` remains claimed. Claim release,
merge-queue admission, W5, versioning, publication, deployment, and consumer
mutation remain prohibited until a fresh independent W4b approves this exact
commit and tree.

## Blocking Evidence Preserved

The immutable blocking report is:

`reviews/W4B-2026-07-31-unit-task-ar-653-001-configured-source-integrity-final.md`

Its SHA-256 is:

`59e7a0bc777701eb402a7799a9430887453c1daea36dc71a2a0021db5d487bc7`

The report and index were committed separately as
`a904ae8960420f125cb2c5bc8c46d12b717bbcd0` before implementation
changed. No prior W4b evidence was edited or replaced.

## RED Before Repair

The public configuration-to-closure matrix first failed as expected:

```text
8 failed, 153 deselected in 0.35s
```

Four invalid Runtime configurations were exercised through direct
`evaluate_state()` and normal `write_projection()`:

- unsafe `ownership.host_owned` path;
- unsafe `host.state_adapters` path;
- malformed indentation; and
- unsupported schema.

The same four cases were independently composed through
`closure_gate.assess()` with substantial work and an otherwise valid linked
review. All eight cases reproduced `unavailable/advisory`,
`closure_blocking=false`, or final `decision=approve`.

## Repair Invariants

`resolve_settings()` already preserved the exact load exception as a
`config-invalid` finding and marked the settings as configured. The repair
uses that existing signal without reparsing or weakening the configuration
validator.

- A top-level `config-invalid` adds `agent_runtime.yml` to the same
  deduplicated, sorted unavailable-source set used by per-source failures.
- `source_debt.unavailable_sources` exposes the bounded repair path.
- The original `config-invalid` detail remains in `findings`.
- The derived `configured-source-integrity` finding points to
  `agent_runtime.yml`.
- Closure reasons include `configured-source-integrity`, producing
  `readiness=blocked`.
- `write_projection()` continues refusing invalid configuration.
- Substantial closure uses the already verified
  `scribe-source-integrity`/`scribe_source_integrity` contract.
- A host with no Runtime config and no conventional source remains advisory
  and nonblocking.

## Verification

Focused invalid-config matrix after repair:

```text
8 passed, 153 deselected in 0.25s
```

Exact candidate Scribe and closure suites:

```text
161 passed in 11.32s
```

Final registered unit verification:

```text
214 passed in 48.34s
template-mirror: expected=84 common=84 identical=81 intentional=3 findings=0
```

Official evidence:

- path:
  `reviews/VERIFY-2026-07-31-unit-task-ar-653-001-20260731033533.json`
- SHA-256:
  `32bf9bd766f62269f367ae69cf0fc0467ee2966b299599f60b3acae58d3fa76b`

Exact implementation-candidate full suite:

```text
3102 passed, 3 skipped, 4 warnings in 172.41s
```

The four warnings are the existing UI-console invalid-escape
`DeprecationWarning` family and are unrelated.

| Check | Result |
| --- | --- |
| Three-way portable state module parity | byte-identical |
| `git diff --check` | pass |
| Template mirror gate | expected 84, common 84, identical 81, intentional 3, findings 0 |
| Host lock freshness | pass |
| Commit governance hooks | pass |

## Footprint and Boundary

Repair range
`a904ae8960420f125cb2c5bc8c46d12b717bbcd0..ee7d0a8569f835b16b6ca8e1938db34f25628fa0`
changes exactly six declared unit targets:

- `src/agent_runtime/state_projection.py`
- `scripts/agent_runtime/state_projection.py`
- `src/agent_runtime/templates/project/scripts/agent_runtime/state_projection.py`
- `tests/test_scribe_due.py`
- `tests/test_closure_gate.py`
- `tests/fixtures/host/agent_runtime.lock.json`

No credentials, provider calls, live network, broker/order action, database
migration, notification, consumer-repository write, version bump, tag, push,
package publication, deployment, release, merge, claim release, or W5 action
occurred.

## Fresh W4b Request

A distinct verifier must review:

- complete implementation range:
  `ae998f7b3b96def7347be7317e3cadda6078150f..ee7d0a8569f835b16b6ca8e1938db34f25628fa0`
- latest repair range:
  `a904ae8960420f125cb2c5bc8c46d12b717bbcd0..ee7d0a8569f835b16b6ca8e1938db34f25628fa0`

The verifier should independently probe:

1. unsafe ownership, adapter, projection, context, and overlay paths;
2. malformed, unsupported-schema, missing-field, unknown-key, and ownership
   conflict configurations;
3. evaluation, projection-write refusal, and substantial closure composition;
4. optional unconfigured, healthy, due, and overdue compatibility;
5. all prior Scribe cleanup/replay attack families, parity, host lock,
   package, and declared footprint.

Only a fresh `APPROVE` with P0=0 and P1=0 may permit claim release and W5.
