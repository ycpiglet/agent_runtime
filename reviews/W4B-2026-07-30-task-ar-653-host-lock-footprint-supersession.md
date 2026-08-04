---
title: TASK-AR-653 Host-Lock Footprint Administrative Supersession
date: 2026-07-30
created_at: 2026-07-30T23:43:03+09:00
task_id: TASK-AR-653
unit_id: UNIT-TASK-AR-653-001
claim_id: CLAIM-20260730-232037-task-ar-653-ar653003
status: supersede
signal: block
verdict: SUPERSEDE
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 0}
reviewed_base: c9b9f8cf2daf10fa31efb0a4e48637f13c40e0fb
reviewed_base_tree: af29875ed128fb58a4b61a1d0ae8489c03c4987f
reviewed_branch: codex/task-ar-653-v080-operability-hardening
verifier_agent_instance_id: qa-20260730-ar653-host-lock-footprint-supersession
verified_by: qa-20260730-ar653-host-lock-footprint-supersession
verifier_role: qa-reviewer
verifier_task: /root/task_ar_653_claim_supersession_audit
worker_identity: le-20260730-232037-kst-ar653003
independence_status: independent
implementation_reviewed: false
w4b_acceptance: false
administrative_scope_audit_only: true
preserve_worktree: .worktrees/TASK-AR-653
preserve_diff_sha256: 9a6c1febce99988681298469292a5f905520c844c3aea375e211488946b8d0b8
claim_disposition: release_as_superseded_then_replace_with_17_file_scope
tags: [w4b, administrative-audit, footprint, host-lock, claim-supersession, independent-verification, block]
---

# TASK-AR-653 Host-Lock Footprint Administrative Supersession

## Independent verdict

`SUPERSEDE — P0: 0, P1: 1, P2: 0`

Claim `CLAIM-20260730-232037-task-ar-653-ar653003` has an incomplete
implementation footprint. The worker's Scribe/template changes make the
committed host lock stale, but the required generated file
`tests/fixtures/host/agent_runtime.lock.json` is not one of the claim's 16
target files. Continuing would require either an out-of-claim write or a
knowingly stale derived artifact.

Release this claim as administratively superseded, preserve the existing
worker worktree and all uncommitted implementation exactly, and replace the
claim with the same 16 paths plus the host lock: 17 target files total.

Verifier `qa-20260730-ar653-host-lock-footprint-supersession`, role
`qa-reviewer`, is distinct from worker
`le-20260730-232037-kst-ar653003`.

> **NON-ACCEPTANCE BOUNDARY:** This is an administrative scope audit only. It
> does not approve, reject, or modify the Scribe implementation; it is not
> TASK-AR-653 implementation W4b and must never be used as final W4b
> acceptance.

No claim, pointer, task, unit, worktree, branch, implementation file, or lock
file was modified or released during this audit.

## Read-only stale-lock evidence

Executed in the worker worktree:

```text
$ env PYTHONDONTWRITEBYTECODE=1 \
    python scripts/regen_host_lock_if_needed.py --check
STALE: template_digest mismatch in .../.worktrees/TASK-AR-653/tests/fixtures/host/agent_runtime.lock.json
STALE: .../.worktrees/TASK-AR-653/tests/fixtures/host/agent_runtime.lock.json is out of date with the current template tree.
Run: python scripts/regen_host_lock_if_needed.py --write
[exit 1]
```

The same command at clean main passed:

```text
OK: .../agent-runtime-task-ar-648/tests/fixtures/host/agent_runtime.lock.json is up to date.
[exit 0]
```

This isolates the drift to the worker's template-tree changes rather than the
reviewed base. The modified paths include the Scribe skill and the portable
template copies of `state_projection.py`, `closure_gate.py`, and
`scribe_due.py`.

The check is non-mutating by construction: it copies the host fixture to a
temporary directory and regenerates only the copy
(`scripts/regen_host_lock_if_needed.py:44-52`). After the check, the real lock
remained clean in both index and worktree:

```text
sha256=887555f64d6e65ceb4606fbc3d2509760fb9b360dc19362b043bdbf3187a124e
fixture_worktree_diff_rc=0
fixture_index_diff_rc=0
```

## Why the host lock is required

The repository contract states that after editing any file under
`src/agent_runtime/templates/`, the developer must regenerate
`tests/fixtures/host/agent_runtime.lock.json`; otherwise
`test_regenerate_noop_when_current` fails
(`scripts/regen_host_lock_if_needed.py:1-17`).

The regression test independently says the fixture lock is a digest over every
template file and requires the committed lock content to equal the lock plan
for the current template tree (`tests/test_lock_merge_driver.py:1-5`,
`tests/test_lock_merge_driver.py:33-48`).

The stale result therefore identifies a mandatory derived output, not an
optional cleanup.

## Claim-footprint evidence

The live claim has 16 unique `target_files` and reports:

```text
target_file_count=16
target_file_unique_count=16
host_lock_in_target_files=False
```

The canonical unit spec likewise has 16 targets and omits the host lock:

```text
unit_target_count=16
host_lock_in_unit_targets=False
```

The corrected footprint is the current 16-file list plus exactly:

```text
tests/fixtures/host/agent_runtime.lock.json
```

This footprint conclusion is not an assessment of implementation quality.

## Implementation-preservation evidence

The worker worktree and branch are live and based on the same current main
commit:

```text
worktree=.worktrees/TASK-AR-653
branch=codex/task-ar-653-v080-operability-hardening
HEAD=c9b9f8cf2daf10fa31efb0a4e48637f13c40e0fb
main=c9b9f8cf2daf10fa31efb0a4e48637f13c40e0fb
unique_commits_over_main=0
```

The implementation is currently uncommitted:

```text
13 files changed, 3285 insertions(+), 185 deletions(-)
binary_diff_sha256=9a6c1febce99988681298469292a5f905520c844c3aea375e211488946b8d0b8
```

That diff is valuable worker output and is vulnerable to worktree removal,
reset, or clean. Supersession is safe only if the orchestrator keeps the exact
worktree and branch in place. Do not remove the worktree, delete the branch,
reset, clean, or regenerate the lock until the corrected replacement claim is
active.

## Finding

### P1 — Mandatory generated host lock is outside registered write authority

Template changes deterministically require a new host lock, while both claim
and unit authorize only 16 files and omit that output. The claim cannot reach
a gate-clean implementation state without exceeding its footprint. It must be
superseded before any further implementation write.

## Exact supersession and replacement recommendation

First stop worker writes. Release only the claim lifecycle, with role routing
disabled to avoid issuing a premature synthetic closeout review:

```bash
env AR_ROLE_ROUTING=0 PYTHONDONTWRITEBYTECODE=1 \
  python scripts/task_claim_dispatcher.py release \
  --claim-id CLAIM-20260730-232037-task-ar-653-ar653003 \
  --verified-by qa-20260730-ar653-host-lock-footprint-supersession \
  --verifier-role qa-reviewer \
  --verification-evidence reviews/W4B-2026-07-30-task-ar-653-host-lock-footprint-supersession.md
```

Do not use `--allow-missing-evidence`, and do not run any worktree cleanup
after release.

Then:

1. Amend the canonical unit footprint to include
   `tests/fixtures/host/agent_runtime.lock.json`.
2. Create a replacement claim with all 17 target files, the same stop
   condition and scope-transition approval, and these exact existing checkout
   coordinates:

   ```text
   worktree_path=.worktrees/TASK-AR-653
   branch=codex/task-ar-653-v080-operability-hardening
   ```

3. Before resuming, verify that the worktree still has base
   `c9b9f8cf2daf10fa31efb0a4e48637f13c40e0fb` and binary diff SHA-256
   `9a6c1febce99988681298469292a5f905520c844c3aea375e211488946b8d0b8`.
4. Only under the corrected claim, run
   `python scripts/regen_host_lock_if_needed.py --write`, then rerun
   `--check` and the relevant lock regression.
5. Require fresh worker W4a and a distinct implementation W4b over the
   completed 17-file candidate.

This report supplies administrative supersession evidence only; it cannot
satisfy step 5.
