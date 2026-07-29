---
title: TASK-AR-648 Portable Continuity P0 Replan
date: 2026-07-29
status: active
signal: stop
score: 0
priority: P0
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-006
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
tags: [replan, portable-continuity, bean-wiki, adoption, release-blocker]
---

# TASK-AR-648 Portable Continuity P0 Replan

## Bottom Line

Stop Bean Wiki attempt 2, keep Allimbot and release work closed, and preserve
the attempt as immutable failure evidence. A fresh `core+web-content`
installation can create a valid default working-tree claim, but that claim
immediately makes the installed `parallel_worktree_gate.py` require
`STATUS.md` or `agents/lead_engineer/STATUS.md`. Neither selected template
projection, adoption plan, lock, nor doctor installs or diagnoses either
candidate.

Do not add an ad hoc Bean status file. Repair the cross-layer Runtime contract
under a new unit, prove it RED-first, obtain fresh independent W4b approval,
and then replay Bean from a third worktree at the original baseline.

## Frozen Observation

| Boundary | Observed value |
| --- | --- |
| Runtime product | `6ccfd9192185a87fa4ef0d4bd654fdba4dd84e39` |
| Runtime template tree | `2ca1fe7da2ab1de3706ba16802678c13ada68e8c` |
| Bean attempt-2 baseline and final `HEAD` | `357eee4fd8c29c33a949adbe3a0ffa80c874bf42` |
| Bean attempt-2 path | `.pilot-worktrees/bean-wiki-task-ar-648-green-2` |
| Bean branch | `codex/task-ar-648-agent-runtime-green-pilot-2` |
| Profiles | `core+web-content` |
| Selected files | `246` |
| Ownership | `239 managed`, `5 seed_once`, `2 host_owned` |
| Initial reconcile | `244 safe`, `0 preserved`, `2 excluded`, `0 conflicts` |
| Immediate and post-registration reconcile | `0 safe`, `244 preserved`, `2 excluded`, `0 conflicts` |
| Default claim | `working_tree`, `scm_commit_authorized=false` |
| Claim `HEAD` movement | none |
| First active-claim gate | exit `1`, block `1` |
| Terminal frozen gate after recording block | exit `0`, block `0`, watch `7` |

The first gate failure was:

```text
STATUS.md, agents/lead_engineer/STATUS.md:
continuity:status-missing: one status candidate must exist for session resume
```

The terminal pass is not a product pass. It only proves that the frozen host is
internally consistent after the task and claim were marked blocked and removed
from the active set.

## Preservation And Stop Proof

- All 16 declared Bean host assets still match the original red baseline.
- `BACKLOG.md` remains
  `c8c323352fcaf1b477094afb86f789728b2f85cc7f23429a9462af1c1dfad591`.
- All 125 `src/content/**` files remain
  `2d45cb99dbcd1e3fe86ad0ebf9d31646580a0720d3496c27c952e829e2ba07cb`
  under the original byte-manifest algorithm.
- The semantic content manifest remains
  `e57721821c3397630b1fa7ebaa5e29520a905b709146b60bdde43a675939f6d7`.
- Host commits, pushes, publishes, deploys, credential reads, network
  deliveries, and content mutations are all integer zero.
- The editorial specialist, restart/Scribe task, Allimbot pilot, and release
  work were not started.
- The dirty Bean primary remains at
  `808309a7b41b80b901e79a1fa6ad546871187ab9`; frozen attempt 1 remains at
  `c93d12baa0020c30e71b50211ecd0c760a65e5e2`.

Canonical frozen evidence is
`agents/host/pilot/evidence/adoption-verification-green-2.json` inside the
attempt-2 worktree. The full preflight and host baseline captures remain
outside the disposable worktree at `/tmp/task-ar-648-bean-preflight.json` and
`/tmp/task-ar-648-bean-host-baseline.json`.

## Cross-Layer Contract Defect

1. `scripts/parallel_worktree_gate.py` treats either `STATUS.md` or
   `agents/lead_engineer/STATUS.md` as mandatory whenever an active claim
   exists.
2. The `core` template includes
   `agents/project/NEXT-SESSION-POINTER.yml` and claim handoff/log machinery,
   but it includes neither status candidate.
3. Configuration classifies both status candidates as `host_owned`; missing
   host-owned paths are therefore not supplied by reconcile.
4. `doctor` requires the pointer and installed gate, but it does not diagnose
   the missing continuity path before the first claim.
5. Existing gate tests encode the isolated rule “active claim without STATUS
   blocks” but do not exercise the supported adoption-to-first-claim journey.

This is a release-blocking portable bootstrap failure, not a Bean policy or
configuration error.

## Remediation Decision To Verify Independently

Prefer one canonical live continuity contract over seeding another monolithic
status ledger:

- A present status candidate keeps its existing handoff-marker validation.
- When neither status candidate exists, a live
  `agents/project/NEXT-SESSION-POINTER.yml` may satisfy continuity only when it
  is no longer the untouched template placeholder and identifies every active
  claim with matching task, claim path or claim id, worktree, branch, phase,
  progress, status text, handoff path, and heartbeat.
- Every active claim must still point to existing handoff and log files.
- A stale, placeholder, malformed, ambiguous, or mismatching pointer must
  block; the fallback must not be fail-open.
- Adoption/doctor must diagnose before first work when neither a valid status
  path nor a viable pointer-based path exists.
- Add an end-to-end regression for fresh `core` adoption, default claim
  creation, and the installed gate.

The independent reviewer must compare this with adding a generic
`agents/lead_engineer/STATUS.md` seed. A seed is acceptable only if the reviewer
shows that it does not create an immediately stale second source of truth or
reintroduce unbounded manual Scribe accumulation.

## Next Unit

After independent confirmation:

1. Mark `UNIT-TASK-AR-648-006` blocked and release its Runtime claim with the
   frozen evidence and independent report.
2. Register a new Runtime-only remediation unit.
3. Add RED tests for the complete adoption-to-first-claim journey and for
   malformed, placeholder, stale, and mismatching pointer cases.
4. Implement the smallest portable contract across source and mirrored
   template surfaces.
5. Run focused verification, routing gates, template parity, sanitizer,
   governance, and the full suite.
6. Obtain a fresh independent W4b on the exact product SHA.
7. Create Bean attempt 3 from
   `357eee4fd8c29c33a949adbe3a0ffa80c874bf42`; never reuse or repair attempt 2.

## Stop Boundary

Any P0/P1, mutation of Bean primary or either frozen attempt, consumer commit,
host/content overwrite, unverified continuity fallback, missing RED proof,
external effect, Allimbot action, version bump, tag, package, push, publish,
deploy, credential access, or release action keeps this task stopped.
