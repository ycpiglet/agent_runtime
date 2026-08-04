---
title: TASK-AR-652 UNIT-001 Attested-Container Sealing Repair W4a
date: 2026-07-30
created_at: 2026-07-30T21:45:37+09:00
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
claim_id: CLAIM-20260730-123600-task-ar-652-ar652001
reviewer: le-20260730-123600-kst-ar652001
status: passed
signal: pass
verdict: PASS_PENDING_INDEPENDENT_W4B
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: da4177f6211b2a1a049ba25b62332b113a54cf97
prior_candidate: 68cef1ad497bfe132e25ceae0c99d4a78ef70c0b
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001-receipt-attestation-approval.md
replan: reviews/REVIEW-2026-07-30-task-ar-652-w4b-attested-container-sealing-replan.md
replan_commit: 3eeca1ac88bb963c9ef70d8f1f0846c9138d6a02
replan_tree: cb63cdfd5ad9865332bb295a0b66fb3e19dc496e
implementation_commit: c3f14800f886923836f4b4682d742e55667dd73a
implementation_tree: f392e2613f398a81751ceb15d85008f94fd1aec4
verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730214428.json
tags: [w4a, economic-evidence, immutable-container, sealed-provenance, fail-closed]
---

# TASK-AR-652 UNIT-001 Attested-Container Sealing Repair W4a

## Verdict

`PASS_PENDING_INDEPENDENT_W4B — P0: 0, P1: 0, P2: 0.`

Implementation commit
`c3f14800f886923836f4b4682d742e55667dd73a`, tree
`f392e2613f398a81751ceb15d85008f94fd1aec4`, closes both container-boundary
P1s reported against the prior candidate. This is worker self-review only.
The claim remains claimed until a fresh independent agent approves the exact
clean final candidate.

The exact implementation ranges checked are:

- complete acceptance:
  `da4177f6211b2a1a049ba25b62332b113a54cf97..c3f14800f886923836f4b4682d742e55667dd73a`;
- focused container sealing:
  `3eeca1ac88bb963c9ef70d8f1f0846c9138d6a02..c3f14800f886923836f4b4682d742e55667dd73a`;
- prior rejected candidate through repair:
  `68cef1ad497bfe132e25ceae0c99d4a78ef70c0b..c3f14800f886923836f4b4682d742e55667dd73a`.

`git diff --check` passed for all three ranges.

## P1 Closure

The validated view now seals membership and provenance as one authority:

- Every ordinary structural list mutator raises
  `ReceiptIntegrityError`: append, extend, insert, item and slice assignment,
  item and slice deletion, pop, remove, clear, reverse, sort, `+=`, and `*=`.
- Constructor-accepted outcome objects are retained as an immutable ordered
  membership snapshot.
- `report()` calls the exact Runtime class implementation, checks current
  length, order, and object identity before consuming any row, and replaces a
  structurally detached view with an empty reporting view.
- Direct base-list calls such as `list.append`, `list.__setitem__`,
  `list.__delitem__`, `list.__imul__`, and `list.__init__` can corrupt only
  the caller's view; the next report yields zero economic eligibility.
- A receipt object can therefore contribute at most once to one report.
- Provenance and membership authority no longer live in any instance slot.
  They are held in a closure-private registry whose entries contain only a
  weak reference to the view, the immutable membership tuple, and a read-only
  provenance mapping.
- The weak-reference callback removes registry state when the view is
  collected and verifies the same reference before removal, preventing stale
  identity cleanup from affecting a newer object.
- Attribute assignment and deletion always fail. Direct
  `object.__setattr__` cannot recreate the former provenance, attestation, or
  seal slots because those slots do not exist.
- Reinvoking `__init__` on an already attested instance fails closed.
- Subclasses are not accepted as provenance authority, so overriding the
  internal reporting method cannot inject a forged mapping.
- The existing complete receipt digest still detects value and nested-value
  mutation on an otherwise exact member.
- Existing immutable reservation, settlement, and provider-call-start
  snapshots remain unchanged.

Historical unreserved execution receipts remain compatible only through an
exact, fully validated strict-ledger view. Plain lists, copies, structurally
changed views, and reserved rows with stripped fields remain ineligible.

## Failure-First and Adversarial Evidence

- Before implementation, the new 32-case container matrix produced
  `26 failed, 6 passed`.
- The first structural and public-slot repair passed those `32` cases.
- A deeper direct-slot matrix then produced `2 failed, 1 passed`, proving that
  name-mangled instance slots were still replaceable through
  `object.__setattr__`.
- Moving authority out of instance state and adding reinitialization and
  subclass negatives produced `38 passed`.
- The final full eval-harness suite passed `261`.
- Direct base-list tests cover initialization, append, extend, insert, `+=`,
  `*=`, item/slice replacement, item/slice deletion, pop, remove, clear,
  reverse, and sort.
- The prior 112-field baseline/actual mutation matrix, plain-list,
  copy-and-strip, direct-constructor, hidden-provenance, provider-call,
  terminal-success, reservation/settlement, restart-budget, and historical
  unreserved controls remain green.

## Verification

- Canonical work evidence:
  `reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730214428.json`.
- Required root routing/claim/Doctor suite: `108 passed`.
- Required six-module consumer-template suite: `421 passed`.
- SDK fake-provider and adapter suite: `5 passed`.
- Eval-harness suite: `261 passed`.
- Taskset and managed-host lock suites: `35 passed` (`12 + 23`); the lock
  check is current.
- Full Runtime suite: `2982 passed, 3 skipped, 4 warnings`; the warnings are
  the pre-existing UI beta invalid-escape warnings.
- Compilation of both changed Python files passed.
- Template mirror remains `84 common / 81 identical / 3 intentional / 0
  findings`.
- Runtime asset usage remains `38 assets / 404 uses / 0 blocks / 0 watches`.
- Evidence index, plan-assumption, taskset-work, and Owner-governance gates
  pass after metadata refresh.

Every provider-sensitive verification command removed the common OpenAI,
Anthropic, Google/Gemini, Azure OpenAI, and AWS credential variables. Tests
used fake, dummy, synthetic, temporary, or in-memory data. No credential value
was read and no live provider or network endpoint was called.

No token or monetary savings claim is made. The tests establish evidence
eligibility and fail-closed exclusion behavior only.

## Boundary

The claim file retained SHA-256
`997dbf33dbb7cc8e660614dcb037476106ecf473ee6a568bbcd69ff7a0aa37ce`
and remains `claimed`, phase `wave-claimed`, under worker
`le-20260730-123600-kst-ar652001`.

No consumer primary, credential, provider account, package, broker, order,
database migration, notification, deployment, remote branch, tag, version,
publication, or release state changed. Independent W4b must approve the exact
clean candidate before claim release, W5 integration, W6 closeout, or
TASK-AR-653 dispatch.
