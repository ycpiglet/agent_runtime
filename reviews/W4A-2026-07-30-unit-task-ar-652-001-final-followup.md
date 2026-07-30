---
title: TASK-AR-652 UNIT-001 Final Recheck Repair W4a
date: 2026-07-30
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
claim_id: CLAIM-20260730-123600-task-ar-652-ar652001
reviewer: le-20260730-123600-kst-ar652001
status: passed
signal: pass
verdict: PASS_PENDING_INDEPENDENT_W4B_FINAL_APPROVAL
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: da4177f6211b2a1a049ba25b62332b113a54cf97
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001-final-recheck.md
scope_amendment: reviews/REVIEW-2026-07-30-task-ar-652-w4b-final-scope-amendment.md
repair_base: dc48733bffeaccc98ce0eeb771dc7635f0843f36
implementation_commit: 94ac7332f48e20e5098044fa5801152bb836bb28
implementation_tree: cbc76a9dff7424ab981d38f7c992de5a52214958
verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730155247.json
tags: [w4a, final-followup, route-authority, baseline-integrity, deterministic-governance]
---

# TASK-AR-652 UNIT-001 Final Recheck Repair W4a

## Verdict

`PASS_PENDING_INDEPENDENT_W4B_FINAL_APPROVAL — P0: 0, P1: 0, P2: 0.`

Implementation commit
`94ac7332f48e20e5098044fa5801152bb836bb28`, tree
`cbc76a9dff7424ab981d38f7c992de5a52214958`, closes the three P1 findings
from the final independent recheck. This is worker/orchestrator self-review
only. The claim remains claimed until a fresh independent verifier approves
this exact candidate.

The complete acceptance range is
`da4177f6211b2a1a049ba25b62332b113a54cf97..94ac7332f48e20e5098044fa5801152bb836bb28`.
The focused final-repair range is
`dc48733bffeaccc98ce0eeb771dc7635f0843f36..94ac7332f48e20e5098044fa5801152bb836bb28`.

## P1 closure map

| W4b finding | Repair and negative proof |
| --- | --- |
| P1-1 pre-resolved dictionaries bypass Scribe policy | `render_prompt()` and `emit_call_message()` now independently resolve the final tier/provider authority from role, requested tier, explicit escalation triggers, and provider. Supplied dictionaries are assertions only; any authoritative-field mismatch raises before prompt or message emission. Direct Scribe forged-high and forged-raw negatives cover both final boundaries. CLI and Codex single/council callers pass the explicit authority inputs. |
| P1-2 missing baseline reasoning creates false savings | A receipt route is comparable only when the model and every supported identity dimension are observed. Missing reasoning is allowed only when `resolved_reasoning_source` explicitly says `unsupported`. An incomplete native baseline becomes `invalid` with `baseline_route_observation_incomplete`; the reporting gate independently excludes forged `verified` data as `baseline_reasoning_observation_unavailable`. Token and monetary eligibility both remain zero. |
| P1-3 exact candidate governance fails on rolling throughput | The root and packaged taskset gate now mask the seven-day throughput line alongside the existing time-derived generated-at, WIP-age, and attention projections. Task rows, status changes, active-claim changes, and record-derived counts remain unmasked. The new root/package regression failed before the repair and passes afterward. The orchestrator regenerated `BACKLOG-BOARD.md`; exact-candidate owner governance now exits 0. |

## Failure-first evidence

- Four direct forged route-dictionary negatives and two incomplete-baseline
  negatives first produced `6 failed`; the same selection now passes `6`.
- The rolling-throughput drift regression first failed with
  `BACKLOG-BOARD.md: stale:content-mismatch`; after the root/package mirror
  repair it passes, and the real taskset gate reports zero findings.
- The full six-module template suite increased from `160` to `166` passing
  tests. Existing provider fixtures that intentionally omit reasoning now
  explicitly record the authoritative `unsupported` schema state.
- All provider paths used fake, dummy, or in-memory providers. Credential
  variables were removed from verification commands; no live provider ran.

## Verification

- Canonical work evidence:
  `reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730155247.json`.
- Required root suite: `106 passed`.
- Required consumer-template suite: `166 passed`.
- SDK bypass suite: `2 passed`.
- Taskset governance suite: `12 passed`.
- Full Runtime suite: `2980 passed, 3 skipped`; the four warnings are the
  pre-existing UI beta invalid-escape warnings.
- `runtime_asset_usage.py --check`: 38 assets, 404 uses, 0 blocks, 0 watches.
- `template_mirror_gate.py --check`: 84 expected/common, 81 identical,
  3 intentional, 0 findings.
- Host lock, evidence index, taskset gate, T3 assumption gate,
  `git diff --check`, direct CLI controls, and integrated Owner governance:
  pass.

No token or monetary savings claim is made. The tests prove evidence
eligibility and fail-closed behavior, not live economic performance.

## Boundary

No consumer primary, credential, provider account, package, broker, order,
database migration, notification, deployment, remote branch, tag, version,
publication, or product release was changed. Independent W4b must review this
exact candidate before the claim may be released or TASK-AR-652 may advance.
