---
type: planning
title: TASK-AR-648 Claim Tree TOCTOU P0 Replan
date: 2026-07-29
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-005
signal: pass
score: 98
priority: P0
tags: [planning-record, task-ar-648, t3-replan, claim-transaction, git-tree, toctou]
---

# TASK-AR-648 Claim Tree TOCTOU P0 Replan

## Bottom Line

Independent W4b rejected UNIT-004 at product SHA
`76212dc0c1898c35542cf2838039b5ee88af360f`. A real pre-commit gate approved
the original indexed claim, a later hook command changed and re-staged the
same JSON, and Git committed the unverified replacement. The final gate then
reported `block=0`.

This is a release-blocking final-content integrity defect. Bean Wiki attempt 2
and Allimbot remain stopped.

## Pinned Evidence

| Item | Value |
| --- | --- |
| W4b verdict | `REQUEST_CHANGES`, 42/100 |
| W4b report | `reviews/W4B-2026-07-29-unit-task-ar-648-004.md` |
| Product SHA | `76212dc0c1898c35542cf2838039b5ee88af360f` |
| Lifecycle SHA | `704aece5dcb0ed8ed475b6532427cffb2820a976` |
| Reproducer commit | `ee631907d17aeeadc8ac0ff90e04ca30e0b8c46c` in a disposable fixture |
| Reproducer result | changed `status_text` entered HEAD; post-commit gate `block=0` |
| Full regression | `2611 passed, 3 skipped`; missing the post-gate sequence |
| Defect signature | `defect:claim-commit-final-tree-toctou:f39b32eb331a6963` |

## Options Considered

| Option | Decision | Reason |
| --- | --- | --- |
| Add blob OIDs to the existing marker | necessary but insufficient | Detects mutation before the gate, not an index writer after it. |
| Move the gate to the final hook line | defense in depth only | Reduces official hook ordering risk but cannot close the post-hook index race. |
| Validate normal commit and roll back with CAS | rejected | The invalid commit is already visible, and exact real-index restoration is unsafe. |
| Private index plus immutable tree and CAS ref update | selected | Hooks cannot alter the sealed tree used by `commit-tree`; the real index and unrelated user staging remain isolated. |
| Disable explicit SCM claim persistence | fallback only | Safe but removes an explicitly requested crash-safety capability from trusted control repositories. |

## Repair Boundary

`UNIT-TASK-AR-648-005` owns only the explicit claim commit transaction:

1. Bind exact artifact blob IDs, private index, starting HEAD, and sealed tree
   to a private-record-backed child marker.
2. Run commit checks against the private index.
3. Revalidate the complete private tree and working blobs after hook return.
4. Commit the immutable tree and update the symbolic branch only by
   compare-and-swap.
5. Preserve every unrelated real-index and working-tree byte on success and
   failure.
6. Keep failed artifacts staged and canonically blocked.

The Bean green replay becomes a separate subsequent unit after independent
approval. This prevents another consumer attempt from being coupled to an
unapproved Git transaction implementation.

## Required Red Evidence

- The W4b hook sequence must fail before `HEAD` advances.
- JSON, handoff, and log post-gate substitutions must each fail.
- Unrelated staged, partially staged, unstaged, and untracked changes must be
  byte-for-byte stable.
- Concurrent ref movement, detached HEAD, hook failure, and every marker
  identity/OID mismatch must fail closed.

## Lifecycle

- UNIT-004 and its claim are blocked, not released.
- Record a fresh T0 snapshot for UNIT-005, then create a distinct claim.
- Write the deterministic failing hook tests before product changes.
- Require W4a and a fresh independent W4b at one exact product SHA.
- Do not register or create a consumer pilot worktree before W4b approval.

## Stop Boundary

Stop on path-only authorization, a normal-commit rollback design, user-index
mutation, hook bypass, non-CAS ref update, private transaction leakage, weakened
ordinary claim persistence, evidence rewrite, consumer mutation, or any new P0.
