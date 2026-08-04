---
title: TASK-AR-653 Replacement Claim Preflight Administrative Supersession
date: 2026-07-30
created_at: 2026-07-30T23:17:52+09:00
task_id: TASK-AR-653
unit_id: UNIT-TASK-AR-653-001
claim_id: CLAIM-20260730-231354-task-ar-653-ar653002
status: supersede
signal: block
verdict: SUPERSEDE
priority: P1
finding_counts: {P0: 0, P1: 2, P2: 0}
reviewed_commit: cbc3eeffce5486c2b5bcd51971b81ae94815f3be
reviewed_tree: d0b13b99ca510589fe4b204e03f9c38e2cf0683c
verifier_agent_instance_id: qa-20260730-ar653-replacement-preflight-supersession
verified_by: qa-20260730-ar653-replacement-preflight-supersession
verifier_role: qa-reviewer
verifier_task: /root/task_ar_653_claim_supersession_audit
worker_identity: le-20260730-231354-kst-ar653002
independence_status: independent
implementation_reviewed: false
w4b_acceptance: false
administrative_release_evidence_only: true
claim_disposition: release_as_superseded_then_recreate_with_required_preflight
tags: [w4b, administrative-audit, preimplementation, claim-preflight, claim-supersession, independent-verification, block]
---

# TASK-AR-653 Replacement Claim Preflight Administrative Supersession

## Independent verdict

`SUPERSEDE — P0: 0, P1: 2, P2: 0`

Release setup claim
`CLAIM-20260730-231354-task-ar-653-ar653002` as superseded, then create a new
claim with explicit scope-transition approval and the canonical unit stop
condition. The claim has a corrected 16-file footprint, but its create
preflight accepted `scope_transition_approved=false` and an empty
`stop_condition`. It is consequently active while both taskset-boundary and
canonical state synchronization are blocking.

Verifier `qa-20260730-ar653-replacement-preflight-supersession`, role
`qa-reviewer`, is distinct from worker
`le-20260730-231354-kst-ar653002`.

> **NON-ACCEPTANCE BOUNDARY:** This report is administrative claim-release
> evidence only. It is not TASK-AR-653 implementation approval, is not W4b
> implementation acceptance, does not review Scribe code, and must never be
> cited as TASK-AR-653 final W4b.

No claim, pointer, task, unit, branch, or code file was modified or released
during this audit.

## Preimplementation state

The claim was created at `2026-07-30T23:13:54+09:00`, 28 seconds after main
commit `cbc3eeffce5486c2b5bcd51971b81ae94815f3be`. At audit time:

```text
status='claimed'
phase='unit-claimed'
progress_pct=0
scope_transition_approved=False
stop_condition=''
worktree_path='.worktrees/TASK-AR-653'
branch='codex/unit-task-ar-653-001-wave'
```

The path and branch are declarations only:

```text
$ git worktree list --porcelain
worktree /home/keti-itp-01/ycpiglet/.control-clones/agent-runtime-task-ar-648
HEAD cbc3eeffce5486c2b5bcd51971b81ae94815f3be
branch refs/heads/main

$ test -d .worktrees/TASK-AR-653
[false]

$ git show-ref --verify refs/heads/codex/unit-task-ar-653-001-wave
fatal: 'refs/heads/codex/unit-task-ar-653-001-wave' - not a valid ref
```

`git log --all --grep` found no claim/worker commit. Both the working-tree and
index diffs for all 16 target files were empty:

```text
worktree_diff_rc=0
index_diff_rc=0
```

There is therefore no worker worktree, branch, implementation commit, target
file modification, or code artifact to preserve. The generated claim,
handoff, log, instance metadata, pointer projection, pane events, and A2A
request are setup records, not implementation.

## Corrected footprint

The claim contains 16 unique target files, exactly matching the corrected unit
footprint:

1. `src/agent_runtime/state_projection.py`
2. `scripts/agent_runtime/state_projection.py`
3. `src/agent_runtime/templates/project/scripts/agent_runtime/state_projection.py`
4. `src/agent_runtime/doctor.py`
5. `scripts/scribe_due.py`
6. `src/agent_runtime/templates/project/scripts/scribe_due.py`
7. `scripts/closure_gate.py`
8. `src/agent_runtime/templates/project/scripts/closure_gate.py`
9. `scripts/session_start_hook.py`
10. `src/agent_runtime/templates/project/scripts/session_start_hook.py`
11. `src/agent_runtime/templates/project/agents/scribe/SKILL.md`
12. `tests/test_scribe_due.py`
13. `tests/test_closure_gate.py`
14. `tests/test_session_continuity_hooks.py`
15. `tests/test_doctor.py`
16. `tests/test_template_smoke.py`

This confirms only claim-scope completeness. It does not confirm that any file
was implemented correctly and is not implementation approval.

## Create-preflight gap

The dispatcher exposes `--scope-transition-approved` as an optional
`store_true` flag (`scripts/task_claim_dispatcher.py:2104-2111`) and
`--stop-condition` with the empty-string default
(`scripts/task_claim_dispatcher.py:2137-2139`). `_build_claim` records those
values verbatim (`scripts/task_claim_dispatcher.py:734`,
`scripts/task_claim_dispatcher.py:762`).

The create validator checks progress, step bounds, completion phase, and
non-empty status text only (`scripts/task_claim_dispatcher.py:794-807`). It
does not reject a required scope transition left false or a blank stop
condition. The existence of this active claim with those exact values confirms
that create preflight allowed both omissions.

## Direct gate evidence

### Taskset boundary — 18 blocking findings

```text
$ env PYTHONDONTWRITEBYTECODE=1 \
    python scripts/taskset_boundary_gate.py --check
taskset-boundary-gate: fail
findings=18
```

All 18 findings have the exact form:

```text
[block] agents/runtime/task_claims/CLAIM-20260730-231354-task-ar-653-ar653002.json:
taskset:boundary-violation:
completed-scope=<completed-taskset>:
new-out-of-scope-claim=CLAIM-20260730-231354-task-ar-653-ar653002:
task-set=TASKSET-AR-V080-OPERABILITY-HARDENING
```

They range from completed scope
`TASKSET-AR-BUSINESS-OPERATING-SYSTEM` through
`TASKSET-AR-WORK-VERIFY-WINDOWS-SHELL-INTEGRITY`. The gate action explicitly
requires owner scope-transition approval recorded on the new claim. This claim
has `scope_transition_approved=false`.

### State synchronization — 5 blocks and 1 watch

```text
$ env PYTHONDONTWRITEBYTECODE=1 python scripts/state_sync_gate.py --check
state-sync-gate: fail
findings=6
block=5
watch=1
```

Exact findings:

```text
watch surface:missing-active-task:STATUS.md
block claim:task-invalid-lifecycle:CLAIM-20260730-231354-task-ar-653-ar653002:planned
block claim:unit-invalid-lifecycle:CLAIM-20260730-231354-task-ar-653-ar653002:worker_ready
block claim:missing-task-ref:CLAIM-20260730-231354-task-ar-653-ar653002
block claim:missing-unit-ref:CLAIM-20260730-231354-task-ar-653-ar653002
block claim:invalid-worktree:CLAIM-20260730-231354-task-ar-653-ar653002
```

The absent worktree is expected only during a tightly bounded claim-first
setup interval. The other four blocks show that create did not atomically
project the canonical task from `planned`, the unit from `worker_ready`, or
the claim path into either `claim_refs`. The STATUS watch likewise shows the
claim was projected as active before all canonical surfaces agreed.

## Findings

### P1-1 — Required taskset transition was accepted as unapproved

The claim is active even though its explicit transition bit is false. It
causes 18 owner-boundary blocks and must not enter implementation.

### P1-2 — Create accepted an empty safety stop and incomplete canonical setup

The claim's stop condition is blank despite the unit carrying a concrete stop
boundary. No worktree exists, while task/unit lifecycle and claim refs remain
unprojected. Five state-sync blocks prove the setup is not dispatchable.

## Exact release recommendation

Release with the role-routing kill switch so releasing this non-overlay worker
claim cannot emit another synthetic closeout review:

```bash
env AR_ROLE_ROUTING=0 PYTHONDONTWRITEBYTECODE=1 \
  python scripts/task_claim_dispatcher.py release \
  --claim-id CLAIM-20260730-231354-task-ar-653-ar653002 \
  --verified-by qa-20260730-ar653-replacement-preflight-supersession \
  --verifier-role qa-reviewer \
  --verification-evidence reviews/W4B-2026-07-30-task-ar-653-replacement-claim-preflight-supersession.md
```

`AR_ROLE_ROUTING=0` is an explicit environment override of committed routing
configuration (`scripts/role_routing.py:116-122`). The release seam dispatches
an additive review only when routing is enabled
(`scripts/task_claim_dispatcher.py:2023-2053`).

Do not use `--allow-missing-evidence`.

## Recreation requirements

Create a fresh claim only after the release above. The create command must
include, at minimum:

```bash
python scripts/task_claim_dispatcher.py create \
  --task-id TASK-AR-653 \
  --task-set-id TASKSET-AR-V080-OPERABILITY-HARDENING \
  --active-scope TASKSET-AR-V080-OPERABILITY-HARDENING \
  --scope-transition-approved \
  --project-id PROJECT-AGENT-RUNTIME \
  --unit-id UNIT-TASK-AR-653-001 \
  --unit-spec agents/lead_engineer/tasks/units/TASK-AR-653/UNIT-TASK-AR-653-001.md \
  --agent-role lead-engineer \
  --team-id quality \
  --mode orchestrator \
  --phase unit-claimed \
  --stop-condition "Stop before automatically rewriting host-owned state, compressing active records, or making product/editorial decisions." \
  --status-text "TASK-AR-653 corrected-footprint implementation claim"
```

Derive the same 16-file footprint from the corrected unit spec. Then create
the fresh worktree/branch, project the claim into canonical task/unit
`claim_refs` and active lifecycle state, and rerun
`taskset_boundary_gate.py --check` plus `state_sync_gate.py --check` before
any implementation write.

A future worker W4a and a different implementation reviewer must still
produce TASK-AR-653 final W4b; this report cannot satisfy either gate.
