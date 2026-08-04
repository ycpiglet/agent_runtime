---
title: TASK-AR-652 UNIT-001 Final Approval Repair W4a
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
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001-final-approval.md
replan: reviews/REVIEW-2026-07-30-task-ar-652-w4b-final-approval-replan.md
repair_base: fd06f7be04a678a5c306a1582a8086b5b9666bbd
implementation_commit: 4f721559d45a02f20e9035d7443cbfeceb9c48b0
implementation_tree: 3d4bde7200c2855af0b11fa9d36320fe68ca7cfe
verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730163357.json
tags: [w4a, final-approval-repair, route-authority, provider-capability, savings-integrity]
---

# TASK-AR-652 UNIT-001 Final Approval Repair W4a

## Verdict

`PASS_PENDING_INDEPENDENT_W4B_FINAL_APPROVAL — P0: 0, P1: 0, P2: 0.`

Implementation commit
`4f721559d45a02f20e9035d7443cbfeceb9c48b0`, tree
`3d4bde7200c2855af0b11fa9d36320fe68ca7cfe`, closes the two P1 findings
from the independent final-approval review. This is worker/orchestrator
self-review only. The claim remains claimed until a fresh independent verifier
approves the exact final candidate.

The complete acceptance range is
`da4177f6211b2a1a049ba25b62332b113a54cf97..4f721559d45a02f20e9035d7443cbfeceb9c48b0`.
The focused repair range is
`fd06f7be04a678a5c306a1582a8086b5b9666bbd..4f721559d45a02f20e9035d7443cbfeceb9c48b0`.

## P1 Closure Map

| W4b finding | Repair and negative proof |
| --- | --- |
| Partial route assertions become executable authority | `_resolve_role_bound_routes()` no longer reads `requested_tier` or `provider` from supplied route dictionaries. Tier comes only from the separate request or role default; provider comes only from the separate provider input or native default. Partial tier, registered alternate-provider, and mixed dictionaries are rejected at both `render_prompt()` and `emit_call_message()`. |
| Native receipt forges reasoning as unsupported | `provider_reasoning_capability()` derives `required`, `unsupported`, or `unknown` from the canonical provider map. Any non-null resolved reasoning requires an observation. Native configured or observed providers require reasoning, while missing reasoning is allowed only when both the canonical configured provider and the receipt source say `unsupported`. Forged native baseline and actual rows yield zero token and monetary eligibility; a real `codex-agent` route remains comparable. |

## Failure-First Evidence

- Partial assertion selection first produced `4 failed, 2 passed`; the two
  already-passing cases were blocked by the message boundary's explicit
  `auto` request. The repaired six-case selection passes `6`.
- Native unsupported-source tests first produced `3 failed`. The new canonical
  capability contract was absent in both routing suites. The repaired
  selections pass `3`, `1`, and `1`.
- The required root suite increased from `106` to `107`; the six-module
  template suite increased from `166` to `176`.
- The first full run had only the four expected stale-lock failures after the
  packaged template changed. Canonical lock regeneration made the dedicated
  23-test lock suite and the second full run pass.

## Verification

- Canonical work evidence:
  `reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730163357.json`.
- Required root suite: `107 passed`.
- Required six-module consumer-template suite: `176 passed`.
- SDK fake-provider suite: `2 passed`.
- Taskset governance suite: `12 passed`.
- Full Runtime suite: `2981 passed, 3 skipped`; the four warnings are the
  pre-existing UI beta invalid-escape warnings.
- Managed-host lock regression suite: `23 passed`; lock check is current.
- Runtime asset usage: 38 assets, 404 uses, 0 blocks, 0 watches.
- Template mirror: 84 expected/common, 81 identical, 3 intentional,
  0 findings.
- Evidence index, taskset gate, T3 plan-assumption gate, root/template routing
  parity, compilation, `git diff --check`, and integrated Owner governance:
  pass.

All provider paths used fake, dummy, or in-memory providers. Credential
variables were removed from verification commands; no credential value was
read and no live provider or network endpoint was called.

No token or monetary savings claim is made. The tests prove fail-closed
evidence eligibility and preserve the registered provider-worker exception;
they do not claim live economic performance.

## Boundary

No consumer primary, credential, provider account, package, broker, order,
database migration, notification, deployment, remote branch, tag, version,
publication, or release state changed. Independent W4b must review the exact
clean final candidate before the claim may be released or TASK-AR-652 may
advance.
