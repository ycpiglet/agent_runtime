---
schema_version: agent-runtime-review/v1
id: W4B-2026-08-09-unit-task-ar-660-001-authority-final-2
title: TASK-AR-660 Unit 001 Recovery Authority Final-2 Independent W4b
date: 2026-08-09
created_at: 2026-08-09T17:38:49+09:00
task_id: TASK-AR-660
unit_id: UNIT-TASK-AR-660-001
claim_id: CLAIM-20260809-125520-task-ar-660-491d
review_claim_id: CLAIM-REVIEW-TASK-AR-660-independent-auditor-w4b-authority-final-2
task_set_id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
review_kind: w4b
reviewer: independent-auditor-CLAIM-REVIEW-TASK-AR-660-independent-auditor-w4b-authority-final-2
reviewer_role: independent-auditor
verifier_instance_id: independent-auditor-CLAIM-REVIEW-TASK-AR-660-independent-auditor-w4b-authority-final-2
worker_instance_id: le-20260809-130000-kst-ar660001
status: blocked
signal: block
score: 60
summary: POSIX actor publication and canonical attribution repairs close their tested seams, but the supported non-POSIX receipt publisher still proves actor authority before sidecar preparation and destination publication.
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 1}
audited_commit: fd66ff1e995c35b2e6dbc8033210383d36924959
candidate_commit: fd66ff1e995c35b2e6dbc8033210383d36924959
candidate_tree: 8f9506f68484de23babf228d196865b0f25b85f4
accepted_baseline: 6c1f67f4c52c193e10236fc9ced1cc5eb53a4a59
implementation_range: 6c1f67f4c52c193e10236fc9ced1cc5eb53a4a59..fd66ff1e995c35b2e6dbc8033210383d36924959
independence_status: independent_context_isolated
implementation_reviewed: true
w4b_acceptance: false
release_authorized: false
claim_disposition: remain_claimed_pending_non_posix_authority_repair_fresh_w4a_and_fresh_independent_w4b
w4a_ref: reviews/VERIFY-2026-08-09-unit-task-ar-660-001-20260809171715.json
prior_w4b_ref: reviews/W4B-2026-08-09-unit-task-ar-660-001-actor-toctou-final.md
t3_ref: reviews/REVIEW-2026-08-09-task-ar-660-unit001-actor-toctou-t3-replan.md
tags: [w4b, task-ar-660, recovery-receipt, actor-registry, attribution, toctou, non-posix, revise]
---

# TASK-AR-660 Unit 001 recovery authority final-2 independent W4b

## Bottom line

`REVISE — P0: 0, P1: 1, P2: 1.`

The exact candidate
`fd66ff1e995c35b2e6dbc8033210383d36924959` (tree
`8f9506f68484de23babf228d196865b0f25b85f4`) closes the prior attribution
P1 and closes the prepared-receipt actor race on the POSIX path. It does not
close that authority boundary on the module's supported non-POSIX path:
`precommit()` still runs before `publish_json_atomic()` prepares and fsyncs its
sidecar and before the destination rename. An actor can therefore disappear,
be replaced, or drift after the last proof while the recovery still commits.

The rejected-proof POSIX path also leaves a newly created empty receipt-store
directory. No receipt authority survives, but that is a literal filesystem
mutation and the current regression snapshot treats a missing root and an
empty root as equivalent.

`w4b_acceptance: false`; `release_authorized: false`. The main claim must
remain claimed until this cross-platform publication seam is repaired and a
fresh worker W4a plus context-isolated W4b both pass.

## Signal

`BLOCK` — the supported non-POSIX path independently reproduces one P1
authority-boundary failure. Finding counts are `P0: 0, P1: 1, P2: 1`.

## Action

Move the external actor-authority callback into the atomic publisher on every
supported platform, after sidecar preparation and immediately before
destination publication. Add fallback-boundary non-mutation regressions for
all three recovery operations and all three actor damage shapes. Also decide
whether a rejected proof must remove a newly created empty receipt directory.

## Risks / Blockers

Until repaired, a non-POSIX recovery can durably mutate a claim or activation
marker and publish receipts/events after its registered actor disappeared or
changed. The positive Linux suites cannot discharge that cross-platform
authority risk. The empty directory is lower severity because it contains no
receipt authority, but it prevents a literal zero-mutation claim.

## Independence and exact-candidate isolation

The verifier instance
`independent-auditor-CLAIM-REVIEW-TASK-AR-660-independent-auditor-w4b-authority-final-2`
is different from worker `le-20260809-130000-kst-ar660001` and did not share
the worker conversation. The committed candidate was inspected with
`git show` and executed from a detached exact-commit clone and archive under
`/tmp`.

The live worktree's uncommitted reviewer claim, instance, pointer-event, and
pane-event bootstrap artifacts were never treated as candidate bytes. Their
governance effects are not findings. This evidence file is the verifier's only
repository write; no code, test, claim, task, unit, plan, index, host lock, or
historical artifact was edited, staged, committed, merged, released, pushed,
tagged, published, or deployed.

## P1 — Non-POSIX prepared-receipt publication still proves actor authority too early

The repaired POSIX path in `scripts/recovery_receipt.py` is correctly ordered:

1. Reserve, write, fsync, close, and re-stat the exclusive sidecar.
2. Invoke the dispatcher-supplied `precommit()` actor proof.
3. Immediately publish the immutable destination with `os.link()`.

The callback invokes `_revalidate_recovery_actor()`, whose equality includes
the canonical event fields, exact-byte SHA-256, device, and inode. Adopt and
terminalize pass it through `execute_recovery()`; activate-store passes it to
`prepare_recovery_receipt()`.

An independent POSIX probe injected actor damage only after observing the
prepared sidecar's file fsync. All nine operation/race combinations refused
with no subject, marker, receipt-entry, or pane-event mutation:

```text
adopt/disappearance: rc=1 sidecar=True injections=1 unchanged=True actor_error=True
adopt/replacement: rc=1 sidecar=True injections=1 unchanged=True actor_error=True
adopt/field-drift: rc=1 sidecar=True injections=1 unchanged=True actor_error=True
terminalize/disappearance: rc=1 sidecar=True injections=1 unchanged=True actor_error=True
terminalize/replacement: rc=1 sidecar=True injections=1 unchanged=True actor_error=True
terminalize/field-drift: rc=1 sidecar=True injections=1 unchanged=True actor_error=True
activate-store/disappearance: rc=1 sidecar=True injections=1 unchanged=True actor_error=True
activate-store/replacement: rc=1 sidecar=True injections=1 unchanged=True actor_error=True
activate-store/field-drift: rc=1 sidecar=True injections=1 unchanged=True actor_error=True
```

However, the non-POSIX branch at `scripts/recovery_receipt.py:918` remains:

```python
if precommit is not None:
    precommit()
publish_json_atomic(...)
```

`publish_json_atomic()` then performs parent validation/creation, sidecar
creation, writing, fsync, identity capture, and only afterward destination
publication. This recreates the prior post-proof window. Unit 001 is not
POSIX-only, and `atomic_io.py` explicitly implements non-POSIX/Windows parent,
rename, and retry behavior, so this is an in-scope authority defect rather
than an unsupported-platform observation.

A separate exact-tree control-flow probe forced this fallback while retaining
the real atomic sidecar publisher. It injected each damage at the publisher's
destination step, after sidecar preparation. The prepared receipt was still
published in every case:

```text
disappearance: order=['precommit', 'destination'] actor_present=False prepared_visible=True receipt_records=1
replacement: order=['precommit', 'destination'] actor_present=True prepared_visible=True receipt_records=1
field-drift: order=['precommit', 'destination'] actor_present=True prepared_visible=True receipt_records=1
```

An independent full-dispatcher fallback-order probe reproduced the durable
impact for every recovery command:

```text
operation=adopt rc=0 actor_present=False receipt_count=2 events_changed=True claims_changed=True
operation=terminalize rc=0 actor_present=False receipt_count=2 events_changed=True claims_changed=True
operation=activate-store rc=0 actor_present=False receipt_count=2 events_changed=True marker_before=False marker_after=True
```

These fallback probes emulate the statically selected non-POSIX ordering on
the available POSIX host; they are not represented as native-Windows runs.
The ordering defect itself is platform-branch source code and is definitive.

Required repair: put the external-authority callback inside the exclusive
atomic publisher on every supported platform, after sidecar preparation and
immediately before its destination link/rename. Pin disappearance,
identical-byte inode replacement, and field drift for all three operations on
that fallback boundary, with exact non-mutation assertions.

## P2 — A rejected proof leaves an empty receipt-store directory

When the receipt directory does not yet exist, `_atomic_direct_parent()`
creates it before the POSIX publisher invokes `precommit()`. Callback failure
cleans the owned sidecar but not the newly created directory:

```text
before_exists=False after_exists=True entries=[] error=stale actor
```

No prepared, terminal, or sidecar record survives, so this does not create
receipt authority and is not another P1. It does violate the requested literal
zero receipt-store mutation. The regression helper
`_tree_entry_snapshot(receipt_dir)` returns `{}` for both a missing root and an
empty root, masking the difference. Repair or explicitly adjudicate this
surface, and make the test compare root existence as well as entries.

## Prior P1-2 — Canonical attribution repair is closed

The attribution gate now uses a bounded strict reader for receipt-era recovery
events: duplicate-member JSON is rejected, every registry ancestor is checked
for symlink/reparse aliasing, identity text is capped at 160 characters, the
filename and payload instance IDs must match, and canonical role/display/
callsite values must match the event. Dispatcher and attribution limits and
path rules agree.

Independent black-box fixtures produced:

```text
valid-control: rc=0 block=0 watch=0
duplicate-member: rc=1 block=1 watch=0 ...recovery-instance-unregistered...
symlinked-registry-ancestor: rc=1 block=1 watch=0 ...recovery-instance-unregistered...
role-161: rc=1 block=1 watch=0 ...recovery-instance-role-invalid...
pre-cutoff-duplicate-watch: rc=0 block=0 watch=1
nonrecovery-selection-control: rc=0 block=0 watch=0
```

The same malformed registry records were independently sent to the dispatcher
resolver: the valid control was accepted, while duplicate `role`, symlinked
registry ancestor, and 161-character role were all rejected. The pre-cutoff
watch and non-recovery control show that cutoff and legacy selection semantics
remain intact. Root and template attribution scripts are byte-identical.

## Full-range and invariant review

The accepted-baseline range
`6c1f67f4c52c193e10236fc9ced1cc5eb53a4a59..fd66ff1e995c35b2e6dbc8033210383d36924959`
contains 60 changed paths, 16,233 insertions, and 1,492 deletions. The complete
diff, Unit, T3 replan, rejected W4b, and fresh W4a were reviewed; `git diff
--check` passed. No additional P0/P1/P2 finding was identified beyond the two
findings above.

The following invariants remain intact:

- Root/template parity passes with 87 common paths, 84 identical, three
  intentional differences, and zero findings. Dispatcher, attribution, and
  recovery-receipt source/template pairs are directly byte-identical.
- The managed host lock is up to date.
- `recovery_receipt.py --check` passes. The four existing receipt files are
  byte-unchanged since commit `7b98b69f`; their SHA-256 values remain
  `550edb5b...`, `edace69d...`, `5a1b79d4...`, and `f13a1409...`.
- Both receipt pairs, pane events 668/669, and the adopted claim preserve Owner
  provenance exactly as
  `ycpiglet <68498184+ycpiglet@users.noreply.github.com>`. The events' actor,
  role, display name, and callsite equal the direct worker instance record.
- Historical `CLAIM-20260803-002651-task-ar-655-5f27` JSON, handoff, and log
  are unchanged from the accepted baseline. Their SHA-256 values remain
  `42e536db...`, `72c02cf...`, and `21281f4b...` respectively.
- The candidate-isolated RBAC, taskset-work, taskset-boundary, identity,
  state-sync, and Owner governance checks pass.

## W4a freshness

The fresh W4a record is committed in the exact candidate and reports the two
declared Unit suites as `753 passed, 6 skipped` and `36 passed`. Commit
`fd66ff1e` changes only Unit/plan/index/W4a evidence relative to repair commit
`94b40cee`; `scripts`, `src`, `schemas`, and `tests` have no post-W4a diff.
The verifier independently repeated both suites with matching counts. W4a is
therefore fresh for the audited implementation, although its positive suites
do not cover the residual non-POSIX timing seam.

## Commands and results

| Command/check | Result |
| --- | --- |
| `git rev-parse HEAD` / `git rev-parse HEAD^{tree}` | exact commit `fd66ff1e995c35b2e6dbc8033210383d36924959`; tree `8f9506f68484de23babf228d196865b0f25b85f4` |
| `git diff --check 6c1f67f4..fd66ff1e` | pass |
| Declared seven-file Unit suite | `753 passed, 6 skipped in 153.41s` |
| Declared template/lock/smoke Unit suite | `36 passed in 20.09s` |
| Independent POSIX post-sidecar actor matrix | nine of nine refused; subject/marker/receipt entries/events unchanged |
| Independent non-POSIX fallback-order probes | prior authority window reproduced; three operations commit after actor disappearance |
| Independent attribution malformed/control matrix | three malformed post-cutoff cases block; valid, legacy-watch, and non-recovery controls correct |
| `python scripts/recovery_receipt.py --check` | pass |
| `python scripts/template_mirror_gate.py --check` | pass; expected/common 87, identical 84, intentional 3, findings 0 |
| `python scripts/regen_host_lock_if_needed.py --check` | pass; host lock up to date |
| `python scripts/attribution_gate.py --check` | pass; block 0, 910 legacy watch findings |
| `parallel_worktree_gate`, `agent_identity_gate`, `task_identity`, scoped `plan_assumption_gate` | pass; findings 0 |
| `rbac_write_gate`, scoped `taskset_work_gate`, `taskset_boundary_gate` | exact-candidate pass; findings 0 |
| `python scripts/owner_governance_gate.py` | exact-candidate pass after reproducing the claim's linked-worktree topology in `/tmp` |
| `git diff --exit-code 7b98b69f..fd66ff1e -- agents/runtime/recovery_receipts` | pass; historical receipt bytes unchanged |
| Historical AR-655 claim/handoff/log baseline diff | pass; unchanged |
| Direct dispatcher/attribution/recovery root-template `cmp` | all byte-identical |

The first standalone detached clone made `state_sync_gate` report the main
claim's relative `.worktrees/TASK-AR-660` as absent. Recreating an exact linked
worker worktree in the temporary clone made state-sync and the full Owner gate
pass. This was an audit-topology artifact, not a candidate or overlay finding.

## Next Steps

Repair the non-POSIX prepared-publication callback boundary, add the missing
cross-platform regressions, adjudicate the empty-directory cleanup, and rerun
the exact Unit suites and gates. Record a fresh worker W4a on the repaired
tree, then assign a different context-isolated verifier for a fresh W4b.

## Decision and claim disposition

Do not accept, close, merge, or release Unit 001 or its main claim. Keep
`CLAIM-20260809-125520-task-ar-660-491d` claimed, repair the non-POSIX
publication callback boundary, adjudicate the empty-directory P2, then record
a fresh W4a and obtain a fresh context-isolated W4b. This evidence grants no
release, commit, merge, push, tag, publish, deploy, external-CI, rotation, or
consumer-mutation authority.
