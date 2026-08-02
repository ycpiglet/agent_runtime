---
schema_version: agent-runtime-review/v1
id: W4B-2026-08-03-unit-task-ar-655-001-lease-authority-final
title: TASK-AR-655 Lease Authority Final Independent W4b
date: 2026-08-03
created_at: 2026-08-03T04:31:18+09:00
task_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-001
claim_id: CLAIM-20260803-002651-task-ar-655-5f27
review_kind: w4b
reviewer: codex-independent-task-ar-655-lease-authority-final-w4b
reviewer_role: independent-auditor
status: blocked
signal: fail
verdict: REVISE
finding_counts: {P0: 0, P1: 1, P2: 0}
candidate_commit: 5c85d7fe5049b6205effafd940cab6df00c47fa4
candidate_tree: 84526eb1597688a22740390d6e11fab9ce790a2c
accepted_replan_commit: 531d4d75f4a2c428183dfd015882711332957852
accepted_replan_tree: 36e1dc9c9fe478282a90a457bd5aacbc2fd4453f
implementation_commit: 87df5980933c548e51d972ae3194d794e807d541
implementation_tree: 0010c036eecfd3916819a91a25b0ffbdf7e928bc
implementation_range: 531d4d75f4a2c428183dfd015882711332957852..87df5980933c548e51d972ae3194d794e807d541
evidence_commit: 49bc170b3a08f7689ed1febaa4de2e93de998414
evidence_tree: 53095fd70def441609760507787b16082da7f8cc
verification_evidence: reviews/VERIFY-2026-08-03-unit-task-ar-655-001-20260803040700.json
w4a_ref: reviews/W4A-2026-08-03-unit-task-ar-655-001-lease-authority-final.md
independence_status: independent
implementation_reviewed: true
w4b_acceptance: false
release_authorized: false
claim_disposition: remain_claimed
scribe_blocker: preserved_unresolved
external_release_blockers: preserved_not_run
tags: [w4b, lease, heartbeat, receipt, projection, data-integrity, revise]
---

# TASK-AR-655 Lease Authority Final Independent W4b

## Verdict

`REVISE — P0: 0, P1: 1, P2: 0.`

Independent reviewer
`codex-independent-task-ar-655-lease-authority-final-w4b` inspected exact
candidate `5c85d7fe5049b6205effafd940cab6df00c47fa4`, tree
`84526eb1597688a22740390d6e11fab9ce790a2c`, and the accepted implementation
range `531d4d75f4a2c428183dfd015882711332957852..87df5980933c548e51d972ae3194d794e807d541`.
The candidate acknowledges a claim-progress response whose projection selects
different task authority from the committed claim. It is not releasable.

The worktree was clean at review start and again immediately before this
report was added; `HEAD` and its tree remained the exact identities above.
All behavioral fixture state was created under a temporary directory. This
report is the reviewer's only repository write. No production, test,
lifecycle, index, claim, Compound, Git history, consumer, CI, network, release,
push, tag, or deployment state was changed.

## P1-1 — Claim-progress accepts a non-matching committed projection

`src/agent_runtime/templates/project/scripts/agent_orchestrator.py::_claim_progress_receipt_valid`
checks the requested claim ID and exact next revision in the claim, receipt,
and projection, plus an allowed projection operation. It does not bind the
projection's `task_id`, `unit_id`, `task_set_id`, `task_claim_ref`, or primary
pointer identities to the returned committed claim and canonical response
path.

An independent zero-exit dispatcher fixture returned claim
`CLAIM-AR655-W4B-RECEIPT` at revision 4 for `TASK-AR-655`, while its merge
projection selected `TASK-OTHER`, `UNIT-TASK-OTHER-001`, `TASKSET-OTHER`, and
`agents/runtime/task_claims/CLAIM-OTHER.json`; its pointer also named only the
other claim at revision 999. `cmd_claim_progress` nevertheless returned code
zero and summary `heartbeated`:

```text
{"accepted_projection_ref": "agents/runtime/task_claims/CLAIM-OTHER.json", "accepted_projection_task_id": "TASK-OTHER", "claim_task_id": "TASK-AR-655", "dispatcher_calls": 1, "expected_claim_ref": "agents/runtime/task_claims/CLAIM-AR655-W4B-RECEIPT.json", "outcome_code": 0, "outcome_summary": "heartbeated", "sentinels_unchanged": true}
```

The probe ran as an inline Python command in
`TemporaryDirectory(prefix="task-ar-655-w4b-receipt-")`. It loaded the exact
candidate orchestrator, replaced only its subprocess seam with the conflicting
zero-exit JSON above, called `cmd_claim_progress` with expected revision 3, and
asserted that the temporary claim and pointer sentinels remained unchanged.
That last result confirms the orchestrator did not directly mutate the
projection surfaces, but it does not make the acknowledged projection safe for
the serial projection owner.

This violates the registered contract that success requires a matching claim
projection. A downstream serial owner can receive a successful receipt for one
claim while being told to project another task and claim. The safe result for
this response is the existing bounded indeterminate outcome: non-zero,
`commit_state=unknown`, and `retry_safe=false`.

Required repair is to bind the response path and projection task-claim
reference to the committed claim, compare task/unit/taskset identities between
the claim and projection, and validate operation-specific pointer structure.
For `merge`, the primary pointer and current-agent entry must identify the same
claim and revision; for an explicit overlay, only
`overlay-no-primary-pointer` without an invented pointer may pass. Add a
zero-exit non-mutation regression for the conflicting identity tuple above.

## Independent command evidence completed before the P1

| Command/check | Result |
| --- | --- |
| `git status --short`; exact commit/tree resolution | clean; candidate `5c85d7fe5049b6205effafd940cab6df00c47fa4`, tree `84526eb1597688a22740390d6e11fab9ce790a2c` |
| Accepted replan and implementation resolution | replan tree `36e1dc9c9fe478282a90a457bd5aacbc2fd4453f`; implementation tree `0010c036eecfd3916819a91a25b0ffbdf7e928bc` |
| `git diff --check 531d4d75f4a2c428183dfd015882711332957852..5c85d7fe5049b6205effafd940cab6df00c47fa4` | pass |
| Registered lease/liveness/dispatcher/consumer suite | `786 passed, 2 skipped in 111.66s` |
| Registered mirror/host suite | `68 passed in 20.80s` |
| `python scripts/template_mirror_gate.py --check` | `expected=86 common=86 identical=83 intentional=3 findings=0` |
| `python scripts/regen_host_lock_if_needed.py --check` | pass; installed host lock current |
| `python scripts/compound_record.py --root . check` | `compound-record: pass` |
| `python scripts/evidence_index_generator.py --check` | pass, findings 0 |
| `python scripts/work_schema_gate.py --items --check` | findings 0; 19 unrelated legacy warnings |
| Fresh Verify identity/content | actor equals active worker `le-20260803-001200-kst-ar655lease001`; status/signal pass; exactly 5 commands, all return code 0; SHA-256 `8d0228b8fb6cb53ee302711b374be7af9b5f388cf9c3d7c462cb1e878396267e` |
| Compound coverage | linked records cover distinct ordered sets of 2 and 9 signatures; their union equals the TASK, UNIT, and active-claim set exactly, 11/11 with no uncovered signature |
| Compound record hashes | earlier `382334aacedd2e671cabdf09c618964412ccff3c5ef5ba6a142dd44e7ac6538e`; new `b4002b45440f8b045e0c7c7a96c2835e0c5aa44519897af57b2cdb4a680e0d99` |
| Temporary conflicting-projection adverse probe | reproduced code-zero `heartbeated` acknowledgment with mismatched task/unit/taskset/ref/pointer identities |

The positive test and parity results cover strict duration/grace admission,
owner/callsite/CAS mutation, scope-drift renewal, shared liveness consumers,
registry serialization, omitted-clock projection, role-overlay lease behavior,
source/template parity, and host-lock consistency. They do not neutralize the
current-scope receipt/projection counterexample. Per the stop-on-P1 rule, no
further adversarial combinations or complete repository suite were run after
the reproduction.

## Preserved blockers and release decision

The active claim must remain `claimed`. Do not release, merge, close, version,
tag, push, publish, deploy, dispatch CI, mutate a consumer, or assert external
release on this candidate. A repaired exact candidate requires fresh Verify,
W4a, independent W4b, and skeptic review.

The separately owned Scribe blocker remains unresolved and is not waived by
this review. Native Windows CI and consumer pilots remain external release
gates and were not run. No credential, network, live provider, package,
database, notification, or external system was touched.
