---
status: candidate_ready
origin_type: release_gate
origin_ref: agents/lead_engineer/tasks/TASK-AR-602.md
signal: pass
score: 95
tags:
  - task-ar-602
  - v0.7.0
  - release-readiness
  - deployment
  - rollback
---

# v0.7.0 Candidate Release Readiness

## Gate

The candidate under review is commit `97271073a381286658e498f44b5795497e2ae8d4` on `codex/task-ar-602-v0-7-0-release`. It changes only the deterministic version cascade from `0.6.0` to `0.7.0` across 13 managed files, including the host fixture lock.

## Decision

**GO for independent candidate review and PR integration. HOLD for tag creation and public release.** The local candidate gates are green. Publication remains blocked until independent reviewers approve this exact candidate lineage, exact-head PR CI and post-merge main CI pass on Python 3.10/3.11/3.12, and the annotated tag target is proven equal to the verified merge commit.

## Passed Checks

| Check | Evidence | Result |
| --- | --- | --- |
| Version cascade | `python scripts/release_version_cascade.py --check --json` -> current `0.7.0`, mismatches `[]` | pass |
| Focused release tests | `tests/test_inventory_sync_sanitize.py tests/test_release_execution_gate.py` -> 108 passed | pass |
| Owner governance | `python scripts/owner_governance_gate.py` -> exit 0 | pass |
| Clean publish bundle | `publish-bundle` selected and wrote 704 files with 0 findings | pass |
| Release preflight | 13 checks; 0 findings, including local tag smoke plan, GitHub publish plan, host update/sync/lock | pass |
| Full test scope | 176 files, 2,204 collected; deterministic 8-batch execution -> 2,198 passed, 6 skipped, 0 failed | pass |
| Worktree isolation | dedicated claimed worktree and branch; root checkout contains only orchestrator state | pass |

The initial monolithic `python -m pytest -q` invocation hit the local 10-minute command limit without reporting a test failure. The same complete set was then sorted by filename and partitioned into eight disjoint 22-file batches. Batch totals were `192`, `169`, `273`, `162+2 skipped`, `213`, `254`, `710+4 skipped`, and `225`, which sum exactly to the 2,204 collected tests.

## Deployment Checklist

1. Obtain technical and skeptical independent approval against the committed candidate evidence.
2. Push `codex/task-ar-602-v0-7-0-release` and create a PR to `main`.
3. Require successful Python 3.10, 3.11, and 3.12 checks for the exact PR head.
4. Read back the merged commit and require the same three checks on exact merged `main`.
5. Confirm no local or remote `v0.7.0` exists, then create one annotated tag at the exact merge commit.
6. Verify `git cat-file -t v0.7.0` returns `tag` and the peeled target equals the merge commit; push only that tag.
7. Publish a non-draft, non-prerelease GitHub release, verify API readback, and close #280 only after visibility is proven.

## Rollback Checklist

- Before merge: close or abandon the PR; no public artifact changes.
- After merge but before tag: revert the version cascade through a new reviewed PR.
- After tag or release: never move or silently replace `v0.7.0`; add a release warning if needed, direct users to immutable `v0.6.0`, and forward-fix as `v0.7.1` through the same gates.
- No database, data, configuration, or secret migration is part of this release.
- Stop if any required check becomes red, the tag already exists unexpectedly, the tag target differs from the verified merge commit, or authentication boundaries are unclear.

## Residual Risks

- The release delta since `v0.6.0` is large; GitHub-generated notes must be reviewed after publication for accuracy and absence of sensitive content.
- Local full-suite duration exceeds the single-command 10-minute limit on this Windows host. Complete coverage is nevertheless proven by the disjoint batch sum and will be independently repeated by GitHub's three-version matrix.
- Public rollback is forward-fix based because the release tag is immutable operational history.

## Required Next Actions

Independent reviewers must inspect the exact candidate lineage and evidence. A favorable review authorizes PR integration only; tag and release publication stay on HOLD until merged-main CI and exact tag-target checks pass.
