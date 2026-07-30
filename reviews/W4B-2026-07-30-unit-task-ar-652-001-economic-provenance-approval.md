---
title: W4b Economic Provenance Approval Review - TASK-AR-652
date: 2026-07-30
created_at: 2026-07-30T20:54:02+09:00
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
claim_id: CLAIM-20260730-123600-task-ar-652-ar652001
status: blocked
signal: block
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 0}
reviewed_base: da4177f6211b2a1a049ba25b62332b113a54cf97
reviewed_base_tree: 00378c32c30050d266822180ccd99270f38a63a7
replan_commit: 4ef0f96a92e3a364b794c987cbcc59ddb675b222
replan_tree: 42f640d63e1a92ddc287d2abd5f6ed748a8f5f98
implementation_commit: edfe564b76415f3324654d9d223671a58ccdb276
implementation_tree: 80c340ab02213f781e1899598e7a4015ec205855
reviewed_commit: bf15acb8a3af6a7ee9de1581855457a6abd0f96e
reviewed_tree: 452400992e19872716ffb4797af8652988a84fdc
full_review_range: da4177f6211b2a1a049ba25b62332b113a54cf97..bf15acb8a3af6a7ee9de1581855457a6abd0f96e
focused_implementation_range: 4ef0f96a92e3a364b794c987cbcc59ddb675b222..edfe564b76415f3324654d9d223671a58ccdb276
implementation_to_candidate_range: edfe564b76415f3324654d9d223671a58ccdb276..bf15acb8a3af6a7ee9de1581855457a6abd0f96e
verifier_agent_instance_id: qa-20260730-w4b-ar652-economic-provenance-approval
verified_by: qa-20260730-w4b-ar652-economic-provenance-approval
verifier_role: qa-reviewer
verifier_task: /root/task_ar_652_w4b_economic_provenance_approval
worker_identity: le-20260730-123600-kst-ar652001
independence_status: independent
pre_report_worktree_status: clean
post_report_worktree_status: report_only
claim_disposition: remain_claimed
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001-call-provenance-final.md
replan: reviews/REVIEW-2026-07-30-task-ar-652-w4b-economic-call-provenance-replan.md
w4a_evidence: reviews/W4A-2026-07-30-unit-task-ar-652-001-economic-call-provenance-repair.md
work_verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730204330.json
tags: [w4b, economic-evidence, call-provenance, in-memory-attestation, independent-verification, revise]
---

# W4b Economic Provenance Approval Review

## Independent verdict

`REVISE — P0: 0, P1: 1, P2: 0`

The exact clean candidate closes the prior missing-call-marker finding for an
untouched strict-ledger read. Missing baseline or actual markers are excluded,
matching markers remain eligible after restart, invalid markers fail strict
reading, and persisted derived budget fields are recomputed.

The candidate is nevertheless not ready for claim release. The new
`ValidatedOutcomeRecords` context attests the reservation, settlement, and
call-start records by Python object identity, but it does not attest the
execution receipt row itself. A caller can therefore mutate a receipt after
`read_outcomes()` and retain the same provenance entry, or copy a reserved row,
remove its five derived budget fields, and enter the unreserved compatibility
branch. Both paths independently reproduced eligible token and monetary
savings from data no longer equal to the strict ledger.

Verifier `qa-20260730-w4b-ar652-economic-provenance-approval`, role
`qa-reviewer`, is a fresh agent instance distinct from worker
`le-20260730-123600-kst-ar652001`. The worker W4a and canonical VERIFY record
were read as supporting evidence, not treated as independent approval.

Immediately before this report was written, both worktree and index were
clean. `HEAD` and its tree exactly matched
`bf15acb8a3af6a7ee9de1581855457a6abd0f96e` and
`452400992e19872716ffb4797af8652988a84fdc`. The sole post-review repository
change is this report.

## P1 - The provenance context is not bound to the immutable receipt row

`ValidatedOutcomeRecords` builds `_economic_provenance` at
`src/agent_runtime/templates/project/scripts/eval_harness.py:111-154`. Each
entry is keyed by `id(receipt)` and contains only the matching reservation,
no-provider settlement, and call-start objects. It does not retain a canonical
receipt digest, immutable snapshot, or other equality proof for the receipt
that passed `_strict_records()`.

`_economic_provider_call_provenance_verified()` at lines 869-944 retrieves the
entry using the current object's identity and recomputes its checks from the
current mutable dictionary. Changing token components, billed cost, currency,
observed route fields, workload, or baseline reference does not invalidate the
entry merely because those values differ from the strict-ledger row.
`report()` at lines 2800-2803 consumes this object-identity index without
revalidating the receipt against the ledger.

The fallback at lines 879-906 creates a second bypass. When no provenance entry
exists, an execution receipt is accepted as compatible legacy evidence whenever
it does not currently contain a value that claims reserved state. Copying a
new-runtime reserved row and removing these five fields is sufficient:

- `budget_reservation_id`;
- `budget_no_provider_settlement_id`;
- `budget_provider_call_start_id`;
- `budget_reservation_status`; and
- `budget_settlement_basis`.

The copied row is then indistinguishable from a manually supplied unreserved
row and is accepted, even though it came from a reserved dispatch. This
contradicts the replan invariant that historical unreserved compatibility
cannot be used by new reserved execution surfaces as an escape hatch.

### Independent reproduction

An offline synthetic strict ledger contained two valid reserved,
provider-call-marked receipts for one workload:

| Receipt | Tokens | Billed cost | Route |
| --- | ---: | ---: | --- |
| baseline | 100 | USD 0.10 | `gpt-5.6-sol` / `high` |
| actual | 15 | USD 0.02 | `gpt-5.6-terra` / `low` |

The untouched `ValidatedOutcomeRecords` produced one eligible comparison,
85 saved tokens, and USD 0.08 saved billed cost. The reviewer then modified
the same actual receipt dictionary in memory to one token and USD 0.00 without
changing the ledger or its provenance objects. The report still emitted one
eligible comparison, now claiming 99 saved tokens and USD 0.10 saved cost:

```json
{
  "before": {
    "eligible": 1,
    "saved_cost": 0.08,
    "saved_tokens": 85
  },
  "mutated_same_objects": {
    "eligible": 1,
    "saved_cost": 0.1,
    "saved_tokens": 99
  }
}
```

A separate control copied the untouched validated rows into ordinary
dictionaries, removed only the five derived budget fields listed above, and
called `report()`:

```json
{
  "eligible": 1,
  "money": 1,
  "saved_cost": 0.08,
  "saved_tokens": 85
}
```

By contrast, copying the same rows without removing those fields is correctly
denied by the worker's new test. The bypass therefore sits precisely at the
new-runtime versus legacy classification boundary.

No provider was called. All provider names, models, observations, token
components, billed costs, and ledgers were synthetic and temporary.

### Required repair

- Bind each provenance entry to the exact immutable execution receipt accepted
  by `_strict_records()`, for example with a canonical full-record digest or an
  immutable snapshot, and compare that binding before any economic field is
  used.
- Treat a missing provenance entry as ineligible for
  `agent-runtime-execution-receipt/v1`. Historical unreserved compatibility
  should be allowed only when a strict-ledger read explicitly supplies an
  entry proving that the receipt has no reservation, rather than inferring
  legacy status from absent caller-controlled fields.
- Prevent direct construction of an apparently validated outcome collection
  from bypassing strict validation, or make the constructor/factory validate
  and bind the complete ledger before exposing provenance.
- Add adversarial tests that mutate every economic and identity-bearing receipt
  field after `read_outcomes()`, including token components, billed cost,
  currency, provider/model/reasoning observations, status/finish, workload,
  baseline receipt ID, and route fields.
- Add a copy-and-strip regression that removes all reservation-derived fields
  and proves zero token and monetary eligibility.
- Preserve legacy compatibility with a historical unreserved receipt actually
  read from a strict ledger, rather than with an unattested plain list.

## Verified closure controls

The previous P1's direct missing-marker cases now behave conservatively in a
fresh Python process:

| Baseline marker | Actual marker | Token eligible | Money eligible | Result |
| --- | --- | ---: | ---: | --- |
| missing | missing | 0 | 0 | `baseline_provider_call_provenance_unverified` |
| missing | present | 0 | 0 | `baseline_provider_call_provenance_unverified` |
| present | missing | 0 | 0 | `actual_provider_call_provenance_unverified` |
| present | present | 1 | 1 | positive control |

An independently corrupted actual marker with the wrong provider failed fresh
reading with `ReceiptIntegrityError`. The selected worker tests also confirmed:

- missing/forged/mismatched reservation and call-start derivations fail;
- wrong reservation, authority, provider, execution surface, and transition
  markers fail;
- a marked skipped actual remains economically ineligible;
- copied rows retaining reserved state fail closed;
- native bridge baseline-only and actual-only authorization are denied, while
  both-authorized evidence remains eligible; and
- the intended unreserved direct-list compatibility test still passes, which
  is the compatibility branch exploited by the P1.

## Exact range and verification evidence

All three requested ranges passed `git diff --check`:

- full candidate:
  `da4177f6211b2a1a049ba25b62332b113a54cf97..bf15acb8a3af6a7ee9de1581855457a6abd0f96e`;
- focused implementation:
  `4ef0f96a92e3a364b794c987cbcc59ddb675b222..edfe564b76415f3324654d9d223671a58ccdb276`;
- implementation-to-candidate metadata:
  `edfe564b76415f3324654d9d223671a58ccdb276..bf15acb8a3af6a7ee9de1581855457a6abd0f96e`.

Fresh independent test results, with credential variables removed, bytecode
writes disabled, and pytest cache disabled:

- economic provenance / native bridge selected matrix:
  `20 passed, 166 deselected`;
- required root routing, claim, and doctor suite: `108 passed`;
- required six-module consumer-template suite: `310 passed`;
- SDK fake-provider and adapter suite: `5 passed`.

Repository checks:

- evidence index: pass, 0 findings;
- T3 plan assumptions: pass, 0 findings;
- taskset work gate: pass, 0 findings;
- managed-host lock: current;
- Runtime assets: 38 assets, 404 uses, 0 blocks, 0 watches;
- template mirror within Owner governance: 84 common, 81 identical,
  3 intentional, 0 findings;
- integrated Owner governance: exit 0 with nonblocking repository-wide watches.

The canonical worker evidence additionally records the broader full Runtime
suite. This verifier did not substitute that self-check for the independent
adversarial reproduction above.

## Boundary and claim disposition

The claim file's pre-report SHA-256 was
`997dbf33dbb7cc8e660614dcb037476106ecf473ee6a568bbcd69ff7a0aa37ce`.
It remained `claimed`, phase `wave-claimed`, under worker
`le-20260730-123600-kst-ar652001`, with no verifier or release transition.

No implementation, task/unit metadata, evidence index, plan assumption,
managed-host lock, consumer primary, credential, environment setting,
dependency, provider account, database, broker, order, notification,
deployment, remote branch, tag, version, publication, or release state was
changed by this review.

Because one task-scope P1 remains, the claim must remain claimed and
unreleased. W5 integration and W6 closeout must not begin.

## Final verdict

`REVISE — P0: 0, P1: 1, P2: 0`
