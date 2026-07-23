---
status: complete
origin_type: taskset_closeout
origin_ref: reviews/REVIEW-2026-07-23-taskset-ar-work-cli-integrity-registration.md
tags:
  - retrospective
  - work-cli
  - data-integrity
  - taskset-closeout
---

# TASKSET-AR-WORK-CLI-INTEGRITY Retrospective

## Outcome

`TASK-AR-617` and `TASK-AR-618` are complete. The first preserves quoted hash and type-like metadata across Work CLI rewrites; the second makes exact task and unit selectors deterministic. Both changes passed failure-first tests, independent W4b, pull-request CI, and post-merge Python 3.10/3.11/3.12 matrices.

## What Worked

- T2 plan-assumption checks stopped dispatch after intervening merges, and a bounded T3 review re-anchored only the affected selector work.
- Failure-first commits separated the reproduced defect from the implementation and made causal review straightforward.
- Shared-boundary fixes stayed small: TASK-AR-618 changed only candidate construction and the common ambiguity guard.
- Independent and skeptical reviews supplemented committed regressions with explicit relative/absolute path probes and mutation snapshots.
- Post-merge CI reran the complete repository matrix on the exact merge commit before taskset completion.

## Friction and Corrections

- TASK-AR-618 initially reached the canonical task correctly but could not self-verify because executable commands existed only in the body. Mirroring the already-declared commands into frontmatter enabled canonical task evidence without changing scope.
- Released claims used `phase: verified`, while the taskset completion gate requires the exact terminal phase `taskset-completed`. W6 normalized all claims in this taskset and retained `progress_pct: 100`.
- The implementation handoff contained one extra EOF blank line. It did not affect runtime or CI, but W6 removed it so closeout diff hygiene is clean.
- PR #340 was merged automatically after its required checks succeeded. Closeout therefore treated the immutable PR head and subsequent main run as separate evidence and did not claim manual merge control.

## Durable Rules

1. Exact task IDs select only canonical task records; descendant discovery belongs to explicit hierarchy operations, not generic item loading.
2. Exact unit IDs may search globally, but every multi-match result must fail closed with stable sorted paths.
3. Explicit existing paths remain privileged single-target selectors and require dedicated mutation-isolation probes.
4. A taskset is not complete until every released worker and review claim records `phase: taskset-completed` and `progress_pct: 100`.
5. Keep task-level executable verification metadata available when W4a and `work close` must operate on the canonical task record.

## Evidence

- `reviews/W4B-2026-07-23-TASK-AR-617-APPROVAL.md`
- `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-617-SKEPTIC-APPROVAL.md`
- `reviews/W4B-2026-07-23-TASK-AR-618-APPROVAL.md`
- `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-618-SKEPTIC-APPROVAL.md`
- PR #340 head `73e2f74b620a695d7bb0df343375e46325b7e726`, merge `d573b9512b3a43c54079ff8e138046a8628e4637`
- Pull-request run `29977028574`; post-merge main run `29977179983`
