---
title: W4b Receipt Attestation Approval Review - TASK-AR-652
date: 2026-07-30
created_at: 2026-07-30T21:28:05+09:00
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
claim_id: CLAIM-20260730-123600-task-ar-652-ar652001
status: blocked
signal: block
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 2, P2: 0}
reviewed_base: da4177f6211b2a1a049ba25b62332b113a54cf97
reviewed_base_tree: 00378c32c30050d266822180ccd99270f38a63a7
prior_rejected_candidate: bf15acb8a3af6a7ee9de1581855457a6abd0f96e
replan_commit: 749feec40dd33b3388a4736e63e089e429b46cb5
replan_tree: bbf2c5265885b1521c99b2dc9a32c303b2fc4d08
implementation_commit: 42ead90538b61b817fdbbccd992d896f35b26b1b
implementation_tree: 8f08cb6ee7768878ff87ed9f4786c4de07546efb
reviewed_commit: 68cef1ad497bfe132e25ceae0c99d4a78ef70c0b
reviewed_tree: e905e239ef0c8c980c2902fee9d1c6889bec7669
full_review_range: da4177f6211b2a1a049ba25b62332b113a54cf97..68cef1ad497bfe132e25ceae0c99d4a78ef70c0b
focused_implementation_range: 749feec40dd33b3388a4736e63e089e429b46cb5..42ead90538b61b817fdbbccd992d896f35b26b1b
implementation_to_candidate_range: 42ead90538b61b817fdbbccd992d896f35b26b1b..68cef1ad497bfe132e25ceae0c99d4a78ef70c0b
verifier_agent_instance_id: qa-20260730-w4b-ar652-receipt-attestation-approval
verified_by: qa-20260730-w4b-ar652-receipt-attestation-approval
verifier_role: qa-reviewer
verifier_task: /root/task_ar_652_w4b_receipt_attestation_approval
worker_identity: le-20260730-123600-kst-ar652001
independence_status: independent
pre_report_worktree_status: clean
post_report_worktree_status: report_only
claim_disposition: remain_claimed
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001-economic-provenance-approval.md
replan: reviews/REVIEW-2026-07-30-task-ar-652-w4b-receipt-row-attestation-replan.md
w4a_evidence: reviews/W4A-2026-07-30-unit-task-ar-652-001-receipt-row-attestation-repair.md
work_verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730211246.json
tags: [w4b, receipt-attestation, economic-evidence, immutable-ledger, independent-verification, revise]
---

# W4b Receipt Attestation Approval Review

## Independent verdict

`REVISE — P0: 0, P1: 2, P2: 0`

The exact clean candidate successfully closes the previously reported
same-object receipt mutation, plain-list, copy-and-strip, direct-constructor,
hidden-record mutation, and historical-unreserved compatibility cases when the
validated collection itself and its provenance attribute remain untouched.

It is nevertheless not ready for claim release. `ValidatedOutcomeRecords`
remains a mutable `list` after its one-time constructor check, while `report()`
trusts the collection's current membership without revalidation. Duplicating
the already-attested actual object therefore multiplies eligible comparisons,
token savings, and billed-cost savings. Separately, the supposedly read-only
provenance is stored in a writable slot. Replacing the slot with a new mapping
lets a caller re-attest a mutated receipt and restore manufactured savings.

Verifier `qa-20260730-w4b-ar652-receipt-attestation-approval`, role
`qa-reviewer`, is a fresh instance distinct from worker
`le-20260730-123600-kst-ar652001` and did not receive the worker conversation
context. Worker W4a and canonical VERIFY evidence were supporting inputs, not
independent approval.

At review start and immediately before this report, worktree and index were
clean. `HEAD` and tree exactly matched
`68cef1ad497bfe132e25ceae0c99d4a78ef70c0b` and
`e905e239ef0c8c980c2902fee9d1c6889bec7669`. The sole post-review repository
change is this uncommitted report.

## P1-1 — Post-construction list mutation can multiply economic evidence

`ValidatedOutcomeRecords` subclasses `list` at
`src/agent_runtime/templates/project/scripts/eval_harness.py:134`. Its exact
identity-preserving outcome-membership check occurs only in `__init__()` at
lines 148-174. The class does not override or deny `append`, `extend`,
`insert`, slice assignment, `__imul__`, deletion, reordering, or the other
structural list mutators, and it retains no immutable expected-membership
attestation for later comparison.

`report()` at lines 2879-2963 reads the cached provenance mapping and then
iterates the collection's current contents. Each repeated reference to the
same attested actual dictionary passes the same receipt digest and provenance
checks. The repeated references are independently accumulated into eligible
record counts, actual and baseline token sums, and monetary buckets.

### Independent reproduction

An offline temporary strict ledger held:

- one reserved, call-start-marked baseline: 100 tokens, USD 0.10;
- one reserved, call-start-marked actual: 15 tokens, USD 0.02; and
- one separately reserved and durably settled pre-provider skip, used to cover
  hidden settlement provenance.

The untouched validated view produced one eligible comparison, 85 saved
tokens, and USD 0.08 saved billed cost. Structural mutations using only the
already-attested actual identity produced:

| Operation after `read_outcomes()` | Eligible | Saved tokens | Saved USD |
| --- | ---: | ---: | ---: |
| untouched control | 1 | 85 | 0.08 |
| `append(actual)` | 2 | 170 | 0.16 |
| `extend([actual, actual])` | 3 | 255 | 0.24 |
| `insert(0, actual)` | 2 | 170 | 0.16 |
| slice assignment with duplicate actual | 2 | 170 | 0.16 |
| `records *= 2` | 2 | 170 | 0.16 |

Removing the baseline failed closed at zero, but removing the unrelated skip
or reversing the rows retained the original eligible aggregate. This confirms
that `report()` does not enforce the constructor's exact-ledger membership or
order invariant. Repeating `extend()` can inflate the aggregate without a
bound.

### Required repair

- Make the validated outcome view structurally immutable, or override every
  mutation path and fail closed.
- Retain an immutable ordered identity/membership attestation and revalidate
  it before `report()` consumes any row.
- Independently enforce unique attested receipt/dispatch membership during
  reporting so repeated object references cannot contribute twice.
- Add regression tests for `append`, `extend`, `insert`, `+=`, `*=`, item and
  slice assignment, removal, deletion, clear, reverse, sort, and direct
  `list` base-method calls. Every structural deviation should reject or yield
  zero economic eligibility.

## P1-2 — The provenance slot is replaceable, allowing caller re-attestation

The candidate stores provenance in a `MappingProxyType` at
`eval_harness.py:207`, but `__slots__ = ("_economic_provenance",)` at line 146
does not make the slot itself read-only. Ordinary assignment can replace the
entire mapping. `report()` at lines 2881-2884 accepts whatever object is
currently stored in that slot; it does not validate the mapping's type,
constructor origin, collection binding, or an independent ledger-level
attestation.

The mapping proxy prevents item assignment only. Its tuple values, including
the hidden canonical reservation, settlement, and call-start JSON, remain
readable. The receipt digest is an unkeyed SHA-256 over documented canonical
JSON. A caller therefore needs no secret or provider access to calculate a new
digest and replace the slot.

### Independent reproduction

Using a freshly read copy of the same synthetic strict ledger:

1. untouched rows reported one comparison, 85 saved tokens, USD 0.08;
2. mutating the actual receipt to one token and USD 0.00 correctly caused zero
   token and monetary eligibility;
3. using only Python standard-library `json` and `hashlib`, the reviewer
   calculated the mutated row's canonical digest, copied the original hidden
   snapshot tuple, and assigned a replacement mapping to
   `records._economic_provenance`;
4. the same report then restored one eligible comparison and claimed 99 saved
   tokens and USD 0.10.

This bypass does not corrupt the ledger and does not require access to a
credential, provider, network, or the module's digest helper.

### Required repair

- Do not treat a caller-replaceable attribute as validation authority.
- Seal provenance and collection membership together in an immutable
  constructor-created representation, and make `report()` validate that
  representation rather than trust a current attribute.
- At minimum, prevent post-initialization attribute replacement and verify an
  internal ledger/collection binding before use; rejecting a plain replacement
  mapping is necessary but not sufficient without the membership repair above.
- Add an adversarial test proving slot reassignment cannot restore eligibility
  after a receipt digest mismatch.

## Verified closure controls

The following requested controls behaved conservatively in fresh synthetic or
temporary data:

- 112 distinct post-read field mutations across both baseline and actual
  receipts covered schema/immutability, receipt/dispatch/task/claim/workload
  identity, requested and selected tiers, resolved and observed
  provider/model/reasoning and their sources/statuses, execution surface,
  source, terminal status/error/finish/outcome, complete token telemetry,
  billed cost/status/currency, baseline identity and observation fields,
  routing flags/status, all five derived budget fields, and nested routing/
  budget payloads. After correcting one initially no-op field assignment, all
  produced zero token and monetary eligibility.
- Untouched execution receipts copied into a plain list produced zero
  eligibility.
- Reserved rows copied and stripped of all five derived budget fields produced
  zero eligibility.
- Direct `ValidatedOutcomeRecords` construction rejected incomplete
  membership, identity-substituted copies, and a corrupt full ledger with a
  duplicate receipt. An exact valid full ledger was accepted and produced the
  positive one-comparison control.
- Caller-held hidden provenance objects were mutated after construction:
  three reservations, one no-provider settlement, and two provider-call-start
  records. The immutable snapshots preserved the original one-comparison,
  85-token, USD 0.08 result.
- A genuine historical unreserved execution-receipt pair with no derived
  budget fields, read through a strict JSONL ledger, retained one eligible
  comparison.
- The full eval-harness suite exercised provider-call markers, positive and
  invalid terminal success, reservation and settlement derivation,
  provider/no-provider mutual exclusion, restart-persistent budgets,
  conservative unobserved commitments, and false-savings negatives.

These passing controls do not mitigate either P1 because both findings mutate
the validated container or its authority after the one-time validation.

## Exact ranges and verification results

All requested exact ranges passed `git diff --check`:

- `da4177f6211b2a1a049ba25b62332b113a54cf97..68cef1ad497bfe132e25ceae0c99d4a78ef70c0b`;
- `749feec40dd33b3388a4736e63e089e429b46cb5..42ead90538b61b817fdbbccd992d896f35b26b1b`;
- `42ead90538b61b817fdbbccd992d896f35b26b1b..68cef1ad497bfe132e25ceae0c99d4a78ef70c0b`.

Substantive range inspection confirmed that the focused implementation changes
are the receipt digest, constructor, immutable hidden-snapshot, and test
changes in the packaged eval harness plus managed-host lock refresh. The final
range contains unit/evidence/index/plan metadata only and no additional
implementation change.

Every Python command removed the common OpenAI, Anthropic, Google/Gemini,
Azure OpenAI, and AWS credential variables; bytecode and pytest cache writes
were disabled. No credential value was read and no provider or network was
called.

Independent tests:

- full eval-harness suite: `223 passed in 8.79s`;
- required root routing/claim/Doctor suite: `108 passed in 27.33s`;
- required six-module template suite: `383 passed in 10.87s`;
- SDK fake-provider/adapter suite: `5 passed in 0.26s`;
- taskset work-gate tests: `12 passed in 0.48s`;
- managed-host lock tests: `23 passed in 1.35s`.

Read-only repository gates:

- evidence index: pass, 0 findings;
- T3 plan assumptions for `TASKSET-AR-V080-OPERABILITY-HARDENING`: pass,
  0 findings;
- root and packaged taskset work gates: pass, 0 findings;
- template mirror: 84 common, 81 identical, 3 intentional, 0 findings;
- Runtime assets: 38 assets, 404 uses, 0 blocks, 0 watches;
- managed-host lock: current.

The canonical worker evidence records its broader self-check. It was not used
as a substitute for the independent mutations above.

## Claim, hash, and boundary confirmation

Before this report, the claim file SHA-256 was
`997dbf33dbb7cc8e660614dcb037476106ecf473ee6a568bbcd69ff7a0aa37ce`.
It remained `claimed`, phase `wave-claimed`, under worker
`le-20260730-123600-kst-ar652001`, with `verified_by`, `verifier_role`, and
`verification_evidence` unset. No release transition was performed.

No implementation, test, task/unit, claim, plan, board, index, managed-host
lock, credential, dependency, consumer primary, provider account, database,
broker, order, notification, deployment, remote branch, tag, version,
publication, or release state was changed. All adversarial ledgers were
temporary, synthetic, in-memory, or automatically cleaned.

Because two task-scope P1 findings remain, the claim must stay claimed and
unreleased. W5 integration, W6 closeout, and TASK-AR-653 must not begin.

## Final verdict

`REVISE — P0: 0, P1: 2, P2: 0`
