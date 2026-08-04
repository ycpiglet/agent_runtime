---
title: TASK-AR-652 UNIT-001 Provider Identity Repair W4a
date: 2026-07-30
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
claim_id: CLAIM-20260730-123600-task-ar-652-ar652001
reviewer: le-20260730-123600-kst-ar652001
status: passed
signal: pass
verdict: PASS_PENDING_INDEPENDENT_W4B
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: da4177f6211b2a1a049ba25b62332b113a54cf97
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001-final-candidate.md
replan: reviews/REVIEW-2026-07-30-task-ar-652-w4b-final-candidate-replan.md
repair_base: c7ca39afc53c9c0a63be93a545dab48742f22c8f
implementation_commit: f48ff8a9514a5e1e49e784088ba19ad283328289
implementation_tree: 8d7442f26247df91d9bf2d6dc2b0e764c039862c
verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730170435.json
tags: [w4a, provider-identity, route-observation, savings-integrity]
---

# TASK-AR-652 UNIT-001 Provider Identity Repair W4a

## Verdict

`PASS_PENDING_INDEPENDENT_W4B — P0: 0, P1: 0, P2: 0.`

Implementation commit
`f48ff8a9514a5e1e49e784088ba19ad283328289`, tree
`8d7442f26247df91d9bf2d6dc2b0e764c039862c`, closes the provider-identity
P1 from the independent final-candidate review. This is worker/orchestrator
self-review only. The claim remains claimed until a fresh independent verifier
approves the exact final candidate.

The complete acceptance range is
`da4177f6211b2a1a049ba25b62332b113a54cf97..f48ff8a9514a5e1e49e784088ba19ad283328289`.
The focused provider-identity repair is
`c7ca39afc53c9c0a63be93a545dab48742f22c8f..f48ff8a9514a5e1e49e784088ba19ad283328289`.

## P1 Closure

`canonical_provider_identity()` now returns a stable identity only for
registered providers:

- `native-codex`, `codex-session`, and `codex-native` normalize to
  `native-codex`;
- `codex` and `codex-agent` normalize to `codex-agent`;
- `claude-agent` remains distinct;
- blank and unregistered names return no identity.

`_route_observation_complete()` validates both configured and observed
provider identity before any success return. Missing, unknown, or mismatched
identity therefore fails even when reasoning telemetry is populated.
Reasoning may be absent only for a matching canonically unsupported provider
with null resolved reasoning and an `unsupported` route source.

The finalizer and report now exclude missing, unknown, cross-unsupported, and
native-alias provider observations for both baseline and actual receipts.
Token and monetary eligible counts remain zero. Registered
`codex`/`codex-agent` aliases remain comparable and eligible.

## Failure-First Evidence

- The new provider matrix first produced `9 failed, 7 passed`. Missing,
  unknown, and cross-unsupported baseline/actual cases plus three
  reasoning-present identity gaps failed.
- The canonical provider identity API was absent in both root and template
  routing suites.
- After repair, the complete matrix passes `16`; the root and template
  identity/capability selections each pass `2`.
- Nine old positive fixtures then failed because they used bare `claude`,
  generic `provider`, or omitted provider completion telemetry. They were
  corrected to supply registered observed identity; no production code infers
  provider telemetry from configuration.

## Verification

- Canonical work evidence:
  `reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730170435.json`.
- Required root suite: `108 passed`.
- Required six-module consumer-template suite: `193 passed`.
- SDK fake-provider suite: `2 passed`.
- Taskset governance suite: `12 passed`.
- Managed-host lock suite: `23 passed`; lock check is current.
- Full Runtime suite: `2982 passed, 3 skipped`; the four warnings are the
  pre-existing UI beta invalid-escape warnings.
- Runtime asset usage: 38 assets, 404 uses, 0 blocks, 0 watches.
- Template mirror: 84 expected/common, 81 identical, 3 intentional,
  0 findings.
- Evidence index, taskset gate, T3 assumptions, root/template routing parity,
  compilation, `git diff --check`, and integrated Owner governance: pass.

All provider paths used fake, dummy, or in-memory providers. Credential
variables were removed from verification commands. No credential value was
read and no live provider or network endpoint was called.

No token or monetary savings claim is made. The tests prove evidence
eligibility behavior only.

## Boundary

No consumer primary, credential, provider account, package, broker, order,
database migration, notification, deployment, remote branch, tag, version,
publication, or release state changed. Independent W4b must approve the exact
clean candidate before claim release or task advancement.
