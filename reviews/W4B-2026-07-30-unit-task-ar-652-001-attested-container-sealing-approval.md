---
title: W4b Attested-Container Sealing Approval - TASK-AR-652
date: 2026-07-30
created_at: 2026-07-30T22:02:21+09:00
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
claim_id: CLAIM-20260730-123600-task-ar-652-ar652001
status: approved
signal: pass
verdict: APPROVE
priority: P1
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: da4177f6211b2a1a049ba25b62332b113a54cf97
reviewed_base_tree: 00378c32c30050d266822180ccd99270f38a63a7
replan_commit: 3eeca1ac88bb963c9ef70d8f1f0846c9138d6a02
replan_tree: cb63cdfd5ad9865332bb295a0b66fb3e19dc496e
implementation_commit: c3f14800f886923836f4b4682d742e55667dd73a
implementation_tree: f392e2613f398a81751ceb15d85008f94fd1aec4
reviewed_commit: 5f8a06ab7fb1cbdef021aa7838330ab5ef6c4739
reviewed_tree: b6e669a561be5fafe68214b484b5292f26925465
full_review_range: da4177f6211b2a1a049ba25b62332b113a54cf97..5f8a06ab7fb1cbdef021aa7838330ab5ef6c4739
focused_implementation_range: 3eeca1ac88bb963c9ef70d8f1f0846c9138d6a02..c3f14800f886923836f4b4682d742e55667dd73a
implementation_to_candidate_range: c3f14800f886923836f4b4682d742e55667dd73a..5f8a06ab7fb1cbdef021aa7838330ab5ef6c4739
verifier_agent_instance_id: qa-20260730-w4b-ar652-container-integrity-final
verified_by: qa-20260730-w4b-ar652-container-integrity-final
verifier_role: qa-reviewer
verifier_task: /root/task_ar_652_w4b_container_integrity_final
worker_identity: le-20260730-123600-kst-ar652001
independence_status: independent
pre_report_worktree_status: clean
post_report_worktree_status: report_only
claim_disposition: remain_claimed_pending_orchestrator_release
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001-receipt-attestation-approval.md
replan: reviews/REVIEW-2026-07-30-task-ar-652-w4b-attested-container-sealing-replan.md
w4a_evidence: reviews/W4A-2026-07-30-unit-task-ar-652-001-attested-container-sealing-repair.md
work_verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730214428.json
tags: [w4b, attested-container, economic-evidence, immutable-ledger, independent-verification, approve]
---

# W4b Attested-Container Sealing Approval

## Independent verdict

`APPROVE — P0: 0, P1: 0, P2: 0`

The exact clean candidate closes both container-boundary P1 findings from the
prior W4b. An unchanged validated baseline/actual pair remains economically
eligible, while normal structural mutations are rejected and direct mutable
`list` base-method bypasses fail closed before any changed view can contribute
economic evidence. Provenance authority is no longer stored in a replaceable
instance attribute, reinitialization is rejected, subclass overrides are not
trusted, and one attested receipt cannot be counted twice.

Verifier `qa-20260730-w4b-ar652-container-integrity-final`, role
`qa-reviewer`, is distinct from worker
`le-20260730-123600-kst-ar652001`. The independent-verification skill was
applied: worker W4a and canonical VERIFY evidence were reviewed as supporting
inputs, not used as a substitute for fresh W4b inspection and execution.

At review start and immediately before this report, the worktree and index
were clean. `HEAD`, tree, and merge base exactly matched:

- candidate commit:
  `5f8a06ab7fb1cbdef021aa7838330ab5ef6c4739`;
- candidate tree:
  `b6e669a561be5fafe68214b484b5292f26925465`;
- reviewed base:
  `da4177f6211b2a1a049ba25b62332b113a54cf97`;
- reviewed base tree:
  `00378c32c30050d266822180ccd99270f38a63a7`.

The sole post-review repository change is this uncommitted report.

## Container-integrity results

Fresh local checks used synthetic, temporary, or in-memory ledgers only.

### Positive control and duplicate exclusion

A complete reserved baseline/actual ledger with provider-call-start evidence
reported exactly:

- one token-eligible comparison;
- 100 baseline tokens, 15 actual tokens, and 85 saved tokens;
- one monetary-eligible comparison; and
- USD 0.10 baseline billed cost, USD 0.02 actual billed cost, and USD 0.08
  saved billed cost.

Appending the already-attested actual receipt with `list.append()` changed the
view's membership. The next report returned zero token eligibility, zero saved
tokens, zero monetary eligibility, and no saved billed cost. The focused
direct-base-method matrix also covered `list.__init__`, `append`, `extend`,
`insert`, `__iadd__`, `__imul__`, item and slice replacement, item and slice
deletion, `pop`, `remove`, `clear`, `reverse`, and `sort`. Every changed view
was ineligible. A validated receipt therefore contributes at most once.

### Ordinary mutations and sealed instance boundary

The ordinary mutation matrix covered append, extend, insert, `+=`, `*=`, item
and slice assignment, item and slice deletion, pop, remove, clear, reverse,
and sort. All raised `ReceiptIntegrityError` with the immutable-collection
signal.

All assign/delete combinations were independently exercised for the former
authority names:

- `_economic_provenance`;
- `_ValidatedOutcomeRecords__attestation`; and
- `_ValidatedOutcomeRecords__sealed`.

Ordinary `setattr`/`delattr` and direct `object.__setattr__`/
`object.__delattr__` could not create, replace, or delete those attributes.
The exact class has no instance `__dict__` and no authority-bearing slot.
Reinvoking the validated class `__init__` on an attested instance raised
`ReceiptIntegrityError`.

A subclass that overrode `_validated_report_inputs()` with a forged mapping
remained ineligible. `report()` accepts authority only when
`type(records) is ValidatedOutcomeRecords` and invokes the exact Runtime class
implementation rather than virtual-dispatching through the subclass.

### Receipt, copy, constructor, and historical controls

The following controls passed:

- complete post-read receipt-field mutation cases for baseline and actual rows
  yielded zero token and monetary eligibility;
- a fresh nested mutation inside the actual receipt's `budget_preflight`
  mapping yielded zero token and monetary eligibility;
- copying validated rows into a plain list yielded zero eligibility;
- copying reserved rows and removing all five derived budget fields yielded
  zero eligibility;
- exact direct construction with the complete, identity-preserving valid
  ledger retained the positive result;
- incomplete outcome membership, identity-substituted row copies, and a
  duplicate/corrupt complete ledger were rejected by direct construction;
- caller-held reservation, no-provider-settlement, and provider-call-start
  dictionaries could be changed after construction without changing the
  sealed snapshots or the positive result; and
- a genuine historical unreserved baseline/actual pair, read from a strict
  JSONL ledger and containing no derived reservation fields, retained one
  token-eligible and one monetary-eligible comparison.

These checks confirm both fail-closed exclusion and the documented
strict-ledger compatibility path.

## Validation-authority design and Python boundary

The focused implementation creates `ValidatedOutcomeRecords` inside a factory
closure. Its validation authority is a closure-held registry keyed by view
identity. Each registry entry contains:

- a weak reference to the exact view;
- an immutable ordered tuple of the exact accepted outcome objects; and
- a `MappingProxyType` over canonical receipt digests plus immutable
  reservation, settlement, and call-start JSON snapshots.

The instance itself has only the `__weakref__` slot. Report-time validation
requires the same live object, exact member count, exact order, and exact
member identity before returning the sealed mapping. The existing canonical
receipt digest then rejects value or nested-value mutation. Weakref cleanup
checks the same reference before deleting a registry entry, avoiding stale
identity cleanup.

Within the supported caller boundary—`read_outcomes()`, `report()`, normal
list operations, direct base-list mutation attempts, attribute operations,
reinitialization, copying, and subclassing—no ordinary use can replace the
validation authority or manufacture eligibility.

This is an in-process Python integrity boundary, not a hostile-code sandbox.
Python code that deliberately mutates private implementation objects can
monkeypatch the exact class/module methods, and deep interpreter introspection
can walk function `__closure__` cells (or use debugger/`ctypes` techniques).
Those operations can rewrite any pure-Python implementation and are outside
the supported caller API. The closure cells were observed without mutation so
that this limitation is explicit; no such unsupported introspection is needed
or available through normal reporting use.

## Exact range inspection

All three required ranges passed `git diff --check`:

- `da4177f6211b2a1a049ba25b62332b113a54cf97..5f8a06ab7fb1cbdef021aa7838330ab5ef6c4739`;
- `3eeca1ac88bb963c9ef70d8f1f0846c9138d6a02..c3f14800f886923836f4b4682d742e55667dd73a`;
- `c3f14800f886923836f4b4682d742e55667dd73a..5f8a06ab7fb1cbdef021aa7838330ab5ef6c4739`.

The complete acceptance range contains 80 changed paths and the full
registered routing/accounting implementation and evidence history. The
focused repair contains four changed paths: the packaged eval harness, its
tests, the T3 plan-assumption snapshot, and the managed-host lock. The
implementation adds closure-private authority, immutable mutator overrides,
exact membership validation, subclass exclusion, and 38 focused regression
cases. The implementation-to-candidate range contains only unit/evidence/
index/plan metadata and no later implementation or test change.

## Commands and results

All Python commands removed the common OpenAI, Anthropic, Google/Gemini, Azure
OpenAI, and AWS credential variables. Bytecode and pytest cache writes were
disabled. No credential value, network endpoint, provider, or external system
was accessed.

- `git status --porcelain=v2`; `git rev-parse HEAD`; `git rev-parse
  'HEAD^{tree}'`; `git merge-base <base> HEAD`:
  clean, exact candidate/tree/base.
- `git log`, `git diff --name-status`, and `git diff --stat` for all three
  exact ranges: inspected; focused and final ranges matched the intended
  implementation/evidence split.
- `git diff --check` for all three exact ranges: pass, no output.
- Focused six-node pytest selection for ordinary/direct mutation,
  reinitialization, former-slot, and subclass cases: `38 passed in 0.16s`.
- Targeted receipt/constructor/copy/compatibility selection:
  `76 passed in 4.32s`.
- Independent bounded synthetic container program: pass; positive
  `1/85/1/USD0.08`, duplicate `0`, nested mutation `0`, hidden snapshots
  stable, copies `0`, invalid constructors rejected, historical pair positive.
- `python -m pytest tests/test_model_routing.py
  tests/test_task_claim_dispatcher.py tests/test_doctor.py -q`:
  `108 passed in 26.70s`.
- `python -m pytest
  src/agent_runtime/templates/project/scripts/test_model_routing.py
  src/agent_runtime/templates/project/scripts/test_subagent_dispatch.py
  src/agent_runtime/templates/project/scripts/test_codex_subagent_bridge.py
  src/agent_runtime/templates/project/scripts/test_agent_worker_routing.py
  src/agent_runtime/templates/project/scripts/test_auto_dispatch.py
  src/agent_runtime/templates/project/scripts/test_eval_harness.py -q`:
  `421 passed in 11.07s`.
- `python -m pytest
  src/agent_runtime/templates/project/scripts/test_verify_sdk_backend.py -q`:
  `5 passed in 0.25s`.
- `python -m pytest
  src/agent_runtime/templates/project/scripts/test_eval_harness.py -q`:
  `261 passed in 8.42s`.
- `python -m pytest tests/test_taskset_work_gate.py -q`:
  `12 passed in 0.46s`.
- `python -m pytest tests/test_lock_merge_driver.py
  tests/test_regen_host_lock_if_needed.py -q`:
  `23 passed in 1.32s`.
- `python scripts/runtime_asset_usage.py --check`: pass; 38 assets, 404 uses,
  0 blocks, 0 watches.
- `python scripts/template_mirror_gate.py --check`: 84 common, 81 identical,
  3 intentional, 0 findings.
- `python scripts/regen_host_lock_if_needed.py --check`: current.
- `python scripts/evidence_index_generator.py --check`: pass, 0 findings
  before adding this report.
- Root and packaged `taskset_work_gate.py --check`: pass, 0 findings.
- `python scripts/plan_assumption_gate.py --check --taskset
  TASKSET-AR-V080-OPERABILITY-HARDENING`: pass, 0 findings.
- `python scripts/owner_governance_gate.py`: exit 0. Its repository-wide
  lifecycle/release observations remained non-blocking watches and it
  performed no mutation or release action.
- `python scripts/work.py status`: one active TASK-AR-652 claim, status
  `claimed`; this candidate worktree is the claim's branch.

The canonical worker VERIFY record was also checked: its three recorded
commands passed `108`, `421`, and `5` tests at the pinned candidate. The
broader W4a report was reviewed but was not treated as independent evidence.

## Claim and boundary confirmation

The claim file SHA-256 is:

`997dbf33dbb7cc8e660614dcb037476106ecf473ee6a568bbcd69ff7a0aa37ce`

It remains:

- status: `claimed`;
- phase: `wave-claimed`;
- worker: `le-20260730-123600-kst-ar652001`; and
- `verified_by`, `verifier_role`, and `verification_evidence`: unset.

No release transition was performed. This report is approval evidence for the
orchestrator's later release gate; it does not itself release, merge, close,
push, tag, publish, deploy, or begin TASK-AR-653.

No implementation, test, task/unit, claim, plan, board, index, managed-host
lock, credential, dependency, consumer primary, provider account, database,
broker, order, notification, deployment, remote branch, tag, version,
publication, or release state was changed. All adversarial fixtures were
synthetic, in-memory, temporary, or automatically cleaned.

## Final verdict

`APPROVE — P0: 0, P1: 0, P2: 0`
