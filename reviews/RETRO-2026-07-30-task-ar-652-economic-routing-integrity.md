---
id: RETRO-2026-07-30-task-ar-652-economic-routing-integrity
title: TASK-AR-652 economic routing and receipt-integrity retrospective
kind: retrospective
status: completed
signal: pass-with-compound
date: 2026-07-30
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
---

# TASK-AR-652 Economic Routing and Receipt-Integrity Retrospective

## Outcome

TASK-AR-652 shipped explicit role-aware routing, persistent execution receipts
and budgets, observed model/reasoning and usage accounting, and fail-closed
economic eligibility. The final candidate passed independent W4b with zero
P0/P1/P2 findings, an additive independent-auditor closeout, and integration
verification on local `main`.

No production provider was called, no credential was read, and no realized
token or monetary saving was claimed. The positive economic examples remain
synthetic eligibility controls.

## What Worked

- Failure-first and independent review moved the design from request-time
  configuration claims to observed, durable, provenance-bound receipts.
- Root and packaged Runtime behavior stayed in parity throughout the repair
  sequence.
- Economic reporting now rejects copied, incomplete, substituted, mutated,
  duplicated, subclass-forged, and detached receipt collections.
- The release gate required a verifier distinct from the worker. Runtime's
  additive closeout routing then exercised the dormant independent-auditor
  role and was itself cross-verified before release.
- The merge queue reran governance plus the `108 + 421` routing suites and the
  SDK/taskset/lock suite before creating local merge commit `1a18a3a6`.

## Friction and Corrections

Three reusable failure families surfaced.

1. Several W4b rounds found adjacent forms of the same trust-boundary defect:
   provider identity, call provenance, receipt values, receipt membership, and
   container authority could still be inferred from or changed through
   caller-controlled state. The durable correction was to bind exact observed
   identity, immutable snapshots, canonical row digests, exact ordered object
   membership, and a sealed report-time authority boundary.
2. The documented lifecycle says merge-queue integration precedes worktree
   cleanup, but `merge_queue.py` checks out the worker branch in the integrator
   checkout. Git refuses that checkout while the same branch remains attached
   to its clean worker worktree. The first process attempt therefore failed
   before verification; removing only the completed worktree and re-enqueueing
   made the second attempt pass. The integrator needs a checked-out-worktree
   preflight or a worktree-aware integration strategy.
3. The two additive closeout reports used `parent_task_id` but not canonical
   `task_id`/`unit_id`. `work close` correctly rejected them as mismatched
   review evidence. The formal W4b remained consumable, and the additive
   reports stayed as indexed inputs. Review-producing skills must emit
   closeout-consumable identifiers by construction.

## Durable Rules

1. Economic evidence is a trust boundary: eligibility must depend on observed
   terminal receipts and sealed provenance, never request intent or mutable
   caller containers.
2. When independent review finds adjacent representations of one defect
   family, move authority to one canonical boundary instead of adding another
   example-specific check.
3. Merge tooling must either operate on the existing worker worktree or
   explicitly require and verify clean worktree detachment before checkout.
   Documentation and the executable preflight must describe the same order.
4. Every W4b/audit template intended for `work close` must carry canonical
   `task_id` and, for unit evidence, `unit_id`; aliases such as
   `parent_task_id` are not sufficient.
5. Unknown implementation hours or tokens remain unknown. They must not be
   coerced to zero merely to complete closeout.

## Failure-to-Regression Routes

- `economic-eligibility-caller-state-trust` is resolved by the packaged
  eval-harness receipt/container regression matrix.
- `merge-queue-checked-out-worktree-ordering` is routed to a TASK-AR-657 scope
  amendment covering merge-integrator preflight and procedure ordering.
- `closeout-review-canonical-linkage` recurred and is routed to TASK-AR-657's
  independent-verification/runtime-adoption skill templates plus closure
  contract tests.

## Evidence

- Final W4b:
  `reviews/W4B-2026-07-30-unit-task-ar-652-001-attested-container-sealing-approval.md`
- Additive audit:
  `reviews/INDEPENDENT-AUDIT-2026-07-30-task-ar-652-closeout.md`
- Audit cross-verification:
  `reviews/QA-REVIEW-2026-07-30-task-ar-652-additive-closeout.md`
- Merged-task verification:
  `reviews/VERIFY-2026-07-30-task-ar-652-20260730223016.json`

No push, PR, tag, version bump, package publication, deployment, or consumer
primary mutation occurred.
