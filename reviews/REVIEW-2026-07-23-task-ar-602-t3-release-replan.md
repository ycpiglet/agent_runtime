---
status: approved
origin_type: deferred_revalidation
origin_ref: agents/lead_engineer/tasks/TASK-AR-602.md
signal: watch
score: 90
tags:
  - task-ar-602
  - t3-replan
  - release-readiness
  - rollback
---

# TASK-AR-602 T3 Release Replan

## Gate

Product release `v0.7.0` from the current verified `main` branch. The release artifact is an annotated Git tag plus a non-draft, non-prerelease GitHub release for `ycpiglet/agent_runtime`. The audience is repository users and downstream installations; the operator is the Owner-authorized lead-engineer claim.

## Readiness Decision

**HOLD pending candidate construction and verification.** Dispatch may resume after this T3 record is anchored, but tagging and publication remain blocked until the version cascade, full tests, governance, release preflight, exact-head PR CI, independent candidate review, merged-main CI, and tag target equality all pass.

## Passed Checks

| Check | Evidence | Result |
| --- | --- | --- |
| W0 isolation | `work.py status`: active claims 0, root worktree only, inflight 0 | pass |
| Predecessors | TASK-AR-594 through TASK-AR-599 are completed with passed verification | pass |
| Current main | `3c27bf8fa353fb46e5d5d2b6db49c3678e16b9fb`; run `29977819328` passed Python 3.10/3.11/3.12 | pass |
| Intake state | #274, #279, #285, #287, #289, #290 closed; only release approval #280 remains open | pass |
| Baseline cascade | `release_version_cascade.py --check` reports current `0.6.0`, no mismatches | pass |
| Tag namespace | no local or remote `v0.7.0`; latest release is `v0.6.0` | pass |

## T2 Drift Adjudication

The recorded plan correctly refused dispatch after four anchor hashes changed. All changes are now intentional, merged prerequisites rather than unreviewed drift.

| Anchor | Current source | Release impact |
| --- | --- | --- |
| `scripts/conversation_work_audit.py` | `839f0490` canonical task-ID producer/consumer alignment | consumes canonical task records consistently |
| `scripts/owner_governance_gate.py` | `3162f20f` never-blocking allimbot governance wiring | full release gate includes the current notification contract |
| `scripts/taskset_dispatcher.py` | `3c1df97a` terminal taskset preservation | completed predecessors cannot be restarted during release dispatch |
| `scripts/work.py` | `99dfaaa3`..`1ee8a666`, `c4b384ff` metadata and selector integrity | lifecycle evidence and exact task selection are safe on current main |

T3 re-anchors these files together with the release cascade, release preflight/publish modules, release gate template, and TASK-AR-602 task/unit records.

## Verification Correction

The registered unit used `git tag -v v0.7.0`, which verifies a cryptographic signature and fails for the repository's established unsigned annotated tags, including `v0.6.0`. TASK-AR-602 requires an annotated tag, not a signed tag. Verification is corrected to:

- `git cat-file -t v0.7.0` -> exact output `tag`
- `git rev-parse 'v0.7.0^{}'` -> exact verified release commit

This keeps the annotated-object and target-commit guarantees without inventing a signing requirement.

## Deployment Checklist

1. Claim TASK-AR-602 after T2 passes and create the dedicated release worktree.
2. Reconcile state and write version `0.7.0` through `release_version_cascade.py --write` only.
3. Run cascade, governance, full pytest, publish plan, release preflight, and clean-state checks.
4. Obtain independent candidate go/no-go against the exact feature head.
5. Merge only through green PR CI; require post-merge main CI at the exact merge commit.
6. Create the annotated `v0.7.0` tag at that merge commit, push the tag, publish GitHub release notes, and verify remote/API readback.
7. Close #280 only after release visibility and exact tag target are proven; then run task/unit W4a, final W4b, W5, and W6.

## Rollback Checklist

- Pre-merge: abandon the candidate branch; `main` and public artifacts remain unchanged.
- Post-merge but pre-tag: revert the version-cascade commit through a new PR if release checks regress.
- Post-tag/publication: never move or silently replace `v0.7.0`. Mark the release with a warning if needed, direct users to the immutable `v0.6.0` artifact, and publish a forward-fix `v0.7.1` after the same gates.
- Data migrations: none. Config or secret migrations: none. Credentials are used only by existing Git/GitHub authentication and must never appear in logs or release notes.
- Recovery validation: exact tag target, GitHub release API readback, install/smoke plan, owner governance, full tests, and W0 status.
- Stop and escalate if the tag target differs from the verified merge commit, any required check is red, the remote tag already exists unexpectedly, or credential boundaries are unclear.

## Blockers

- The `0.7.0` cascade and release notes do not yet exist.
- Full local candidate validation, exact-head PR CI, independent candidate approval, and merged-main CI are still pending.
- External tag and GitHub release do not yet exist, as expected before go/no-go.

## Warnings or Residual Risks

- A public tag is immutable operational history; rollback is forward-fix based after publication.
- GitHub auto-merge may merge immediately after checks. The exact merged SHA must be read back before tagging.
- The release contains a large accumulated delta since `v0.6.0`; release notes must summarize user-visible changes without exposing internal secrets or transient evidence paths.

## Required Next Actions

Record the current anchors, pass T2 claim creation, build and verify the candidate, obtain an independent go/no-go, then publish only from the exact green merged commit.
