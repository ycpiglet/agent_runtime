---
title: TASK-AR-642 UNIT-001 Independent W4b Approval
date: 2026-07-28
status: approved
signal: pass
score: 98
verdict: APPROVE
task_id: TASK-AR-642
unit_id: UNIT-TASK-AR-642-001
verified_head: c1b4a20ec5f37353464ac1cd800a8512f17ba83b
verified_by: /root/w4b_task_ar_640_001
verifier_role: independent-verifier
worker_instance: /root/w3_task_ar_640_001
tags: [w4b, independent-verification, sync, lock-v2, ownership]
---

# TASK-AR-642 UNIT-001 Independent W4b Approval

## Verdict

**APPROVE — 98/100.** Exact audited product HEAD:
`c1b4a20ec5f37353464ac1cd800a8512f17ba83b`.

The rework closes the prior P0 apply-time symlink escape and P1 lock-v2
metadata gap. No P0/P1 finding remains in this unit's bounded ownership,
reconcile, lock, or pinned-update surface.

## Independent commands

```text
python -m pytest tests/test_inventory_sync_sanitize.py tests/test_template_smoke.py -q
# 125 passed in 12.40s

python -m pytest tests/test_lock_merge_driver.py tests/test_regen_host_lock_if_needed.py -q
# 23 passed in 0.90s

python -m compileall -q src/agent_runtime
git diff --check
python scripts/owner_governance_gate.py
# passed (compound cadence advisory only)

python -m pytest -q
# 2328 passed, 3 skipped, 4 pre-existing UI escape warnings in 105.25s
```

## Contract evidence

- A precomputed safe plan was invalidated by replacing its `linked` ancestor
  with an external directory symlink. Both `apply_updates()` and
  `apply_safe_updates()` returned nonzero, printed `applied=0`, and wrote
  neither an earlier internal safe file nor `outside/file.py`.
- With two safe items and two pre-existing ordinary conflicts, legacy apply
  remained atomic (`applied=0`, no safe writes). Opt-in safe apply wrote exactly
  the create and lock-clean update, printed `applied=2` and
  `remaining_conflicts=2`, and preserved both conflicting host files.
- Explicit descendant `host_owned` and `generated` paths were excluded from
  all writes. Seed defaults remain one-time, and v1 unmanaged projection is
  consumed through the same descendant matcher. The Autofolio-shaped v1 seam
  fixture preserves all declared seams while applying its managed path.
- Reconcile text/JSON were byte-stable, action ordered, and record ownership,
  action, reason, safety, lock migration, configured upstream ref, actual
  template root, and canonical digest.
- v1 locks remain readable. Newly built v2 lock records are deterministic and
  include ordered top-level effective `profiles` and `capabilities`, ownership,
  managed digests, and truthful `seeded: []` for a not-yet-applied fixture.
  Lock writes refuse unresolved conflicts; the canonical fixture lock passes
  both regeneration check and write parity.
- Host update uses `git+https://github.com/example/agent_runtime.git@v0.1.0`
  in an isolated install dir, and reconcile execution routes through that
  installed CLI (`install-upstream`, `verify-templates`, `sync-reconcile`).
  No execution step uses ambient `package_version` to select the source.

## Scope audit

Implementation changes are confined to the registered sync/lock/CLI/host-update
surface and focused tests/fixture evidence. No profile manifest, dependency
closure, UI, lifecycle behavior, or consumer repository mutation was observed.

## Residual non-blocking watch

The implementation performs a fresh-plan and target/ancestor preflight before
application, closing the tested stale-plan escape. A future hardening pass can
use descriptor-based no-follow writes to narrow the remaining OS-level race
window between preflight and individual file writes; that is outside this
unit's explicit safe-only/revalidation contract.

No claim release, push, merge, or consumer-host mutation was performed by this
verifier.
