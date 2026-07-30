---
title: TASK-AR-653 Scribe Git Audit Anchor Repair Independent W4b
date: 2026-07-31
created_at: 2026-07-31T01:32:30+09:00
task_id: TASK-AR-653
unit_id: UNIT-TASK-AR-653-001
claim_id: CLAIM-20260730-234934-task-ar-653-ar653004
status: blocked
signal: block
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 4, P2: 0}
reviewed_base: ae998f7b3b96def7347be7317e3cadda6078150f
repair_parent: 1440ab4ec1370c3b4887efedcc4ac668c4cfeaa7
reviewed_commit: 74a82b2bf1bfa5a3476e059c34aaa1a02bd7164f
reviewed_tree: 9624446dc6f11c2373130abe51e375f4977768ab
w4a_evidence_head: aeb31e14ad45080e8842e2383b944d4dfbf26065
verifier_agent_instance_id: qa-20260731-ar653-git-audit-anchor-final-w4b
verified_by: qa-20260731-ar653-git-audit-anchor-final-w4b
verifier_role: qa-reviewer
verifier_task: /root/task_ar_653_git_audit_anchor_final_w4b
worker_identity: le-20260730-234934-kst-ar653004
prior_verifier_identity: qa-20260731-ar653-receipt-authority-repair-w4b
independence_status: independent
report_transcribed_by: le-20260730-234934-kst-ar653004
transcription_reason: verifier platform safety filter interrupted report serialization after findings were delivered to the orchestrator
w4b_acceptance: false
claim_disposition: remain_claimed_pending_repair_and_fresh_w4b
tags: [w4b, scribe, cleanup-receipt, git-audit-anchor, independent-verification, revise]
---

# TASK-AR-653 Scribe Git Audit Anchor Repair Independent W4b

## Independent Verdict

`REVISE — P0: 0, P1: 4, P2: 0.`

The repair closes the two previously reported trust-boundary failures and its
registered work-verification suite passes. A fresh independent verifier found
four stronger correctness failures, however. Each can still turn evidence
that violates the declared Scribe contract into a closure-ready outcome.

The verifier completed the analysis and delivered the verdict and findings to
the orchestrator, but the platform safety filter interrupted report
serialization three times. The worker transcribed this defensive summary
without changing the verdict, counts, reviewed hashes, or implementation.
This is a blocking `REVISE`, never an approval or release credential.

## Exact Reviewed State

| Identity | Exact value |
| --- | --- |
| Review base | `ae998f7b3b96def7347be7317e3cadda6078150f` |
| Repair parent | `1440ab4ec1370c3b4887efedcc4ac668c4cfeaa7` |
| Reviewed implementation | `74a82b2bf1bfa5a3476e059c34aaa1a02bd7164f` |
| Reviewed tree | `9624446dc6f11c2373130abe51e375f4977768ab` |
| W4a/evidence HEAD | `aeb31e14ad45080e8842e2383b944d4dfbf26065` |
| Independent verifier task | `/root/task_ar_653_git_audit_anchor_final_w4b` |
| Verifier identity | `qa-20260731-ar653-git-audit-anchor-final-w4b` |
| Worker identity | `le-20260730-234934-kst-ar653004` |

The worktree was clean when review began. The verifier did not edit
implementation, claim, unit, index, lifecycle, consumer repositories, or
existing evidence.

## P1-1 — Git Object View Is Not Canonicalized

Receipt verification asks local Git for commit and blob content, but it does
not disable or reject repository-local object-view substitution. The verifier
confirmed that the same stored commit identity can therefore be interpreted
through a different local object view and authorize a false reduction.

### Required repair

- Force all audit reads to ignore replacement objects.
- Reject repository graft or replacement state that can alter ancestry or
  object interpretation.
- Disable lazy object fetching so a read-only receipt check cannot cause
  network access.
- Add registered local-repository regressions for those conditions.

## P1-2 — Owner `no_touch` Does Not Require No Touch

An exact committed owner decision can currently unblock closure after the
source bytes have been replaced without reducing the hot count, or after the
hot count has increased. This conflicts with the declared `no_touch`
decision semantics.

### Required repair

- Require owner-decision outcomes to preserve the complete before-source
  binding set exactly, including content digest and hot count.
- Recheck that invariant during receipt replay.
- Keep valid byte-identical owner no-touch behavior covered.

## P1-3 — Approver Identity Grammar Remains Ambiguous

Several YAML implicit scalar forms and escaped quoted forms still pass as
approver identities even though they are not canonical stable identifiers.
The earlier null/boolean/object checks are therefore incomplete.

### Required repair

- Define one explicit, documented identifier-token grammar.
- Apply it equally to TASK/UNIT authorization and JSON owner identity.
- Reject implicit numeric, special-float, timestamp-like, control-escape, and
  other non-token forms regardless of quoting.
- Preserve registered positive identities used by canonical Runtime records.

## P1-4 — Reduction Is Not Restricted to the Authorized Plan

A reduction receipt verifies aggregate source and count changes but does not
prove that removed or replaced baseline rows were among the cleanup plan's
authorized candidates. The verifier confirmed that rows explicitly excluded
because they reference active or canonical records can be removed while the
receipt remains valid.

### Required repair

- Reconstruct the before/after source delta from the anchored baseline and
  current source bytes.
- Permit deletion or replacement only for source orders present in the bound
  cleanup plan.
- Preserve all plan-excluded baseline rows, including active and canonical
  references, and enforce the same rule during replay.
- Cover both Markdown and JSON state adapters and retain valid bounded
  reduction behavior.

## Verification Evidence

| Check | Result |
| --- | --- |
| Registered work-verification suite | `132 passed` in `40.48s` |
| Exact implementation/tree identity | matched |
| Prior two P1 regression families | closed |
| Stronger independent behavior families | 4 acceptance-impacting failures |
| Implementation edits by verifier | none |

The W4a full-suite evidence remains
`3020 passed, 3 skipped, 4 known UI warnings`. The independent verifier did
not substitute that worker evidence for the stronger behavior review.

## Boundary and Disposition

No consumer primary, credential, provider, live network, broker, order,
database migration, notification, version, tag, package publication, push,
deployment, or release action was performed.

This exact candidate must not release its claim, enter the merge queue, or
advance to W5. A repaired candidate needs new RED/GREEN evidence, a fresh W4a,
and another distinct independent W4b.
