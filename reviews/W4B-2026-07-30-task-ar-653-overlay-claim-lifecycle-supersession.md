---
title: TASK-AR-653 Overlay Claim Lifecycle Administrative Supersession
date: 2026-07-30
created_at: 2026-07-30T23:07:44+09:00
task_id: TASK-AR-653
unit_id: UNIT-TASK-AR-653-001
claim_ids:
  - CLAIM-SCOUT-TASKSET-AR-V080-OPERABILITY-HARDENING-W1
  - CLAIM-REVIEW-TASK-AR-653-independent-auditor-closeout
status: supersede
signal: block
verdict: SUPERSEDE
priority: P1
finding_counts: {P0: 0, P1: 2, P2: 0}
reviewed_commit: 4fd24097dcce0fbeb79471ccfdc192c70d46ac80
verifier_agent_instance_id: qa-20260730-ar653-overlay-lifecycle-supersession
verified_by: qa-20260730-ar653-overlay-lifecycle-supersession
verifier_role: qa-reviewer
verifier_task: /root/task_ar_653_claim_supersession_audit
worker_identity: le-20260730-225027-kst-ar653001
overlay_identities:
  - progress-scout-CLAIM-SCOUT-TASKSET-AR-V080-OPERABILITY-HARDENING-W1
  - independent-auditor-CLAIM-REVIEW-TASK-AR-653-independent-auditor-closeout
independence_status: independent
implementation_reviewed: false
w4b_acceptance: false
administrative_release_evidence_only: true
claim_disposition: release_both_as_superseded_pending_orchestrator
tags: [w4b, administrative-audit, overlay, lifecycle, claim-supersession, independent-verification, block]
---

# TASK-AR-653 Overlay Claim Lifecycle Administrative Supersession

## Independent verdict

`SUPERSEDE — P0: 0, P1: 2, P2: 0`

Release both synthetic overlay claims as superseded:

1. `CLAIM-SCOUT-TASKSET-AR-V080-OPERABILITY-HARDENING-W1`
2. `CLAIM-REVIEW-TASK-AR-653-independent-auditor-closeout`

They were directly materialized by `scripts/role_routing.py`; no separately
running agent, worker checkout, implementation branch, or implementation
commit exists for either identity. Their minimal overlay records are accepted
by the overlay-aware worktree/state gates but not by the owner chain's identity,
RBAC/current-agents, and taskset-boundary gates. Leaving them active therefore
blocks pre-commit governance without preserving executable work.

Verifier `qa-20260730-ar653-overlay-lifecycle-supersession`, role
`qa-reviewer`, is distinct from the TASK-AR-653 worker and both synthetic
overlay identities.

> **NON-ACCEPTANCE BOUNDARY:** This is administrative release evidence only.
> It is not TASK-AR-653 implementation approval, is not final W4b, does not
> review any Scribe implementation, and must never be cited as implementation
> or final-W4b acceptance.

No claim was modified or released during this audit.

## Overlay provenance and execution evidence

### Direct generation by `role_routing.py`

The module contract says additive claims are written directly rather than
through `task_claim_dispatcher` because they are orchestration overlays with no
worktree (`scripts/role_routing.py:25-29`). `_write_overlay_claim`:

- creates an in-memory `overlay: true` claim with synthetic identity
  (`scripts/role_routing.py:180-214`);
- writes only handoff, log, and claim JSON
  (`scripts/role_routing.py:218-242`); and
- appends one routing event (`scripts/role_routing.py:250-267`).

It does not spawn a process, register an agent instance, create a worktree, or
create a branch. The two call sites match the records exactly:

- `dispatch_wave_hooks` constructs
  `CLAIM-SCOUT-<taskset>-W<wave>` and emits `progress_scout_sweep`
  (`scripts/role_routing.py:369-405`);
- `route_review_pass` constructs
  `CLAIM-REVIEW-<task>-<role>-<event>` and emits
  `review_pass_dispatched` (`scripts/role_routing.py:314-331`).

The claim `callsite_id`, `pane_id`, generated identity, mode, task ID, and event
names match those constructors.

### No separate execution or implementation

The exact runtime summary was:

```text
CLAIM-SCOUT-TASKSET-AR-V080-OPERABILITY-HARDENING-W1
  overlay=True
  status='claimed'
  phase='claim-created'
  progress_pct=0
  worktree_path=None
  branch=None
  target_files=None
  scope_transition_approved=None

CLAIM-REVIEW-TASK-AR-653-independent-auditor-closeout
  overlay=True
  status='claimed'
  phase='claim-created'
  progress_pct=0
  worktree_path=None
  branch=None
  target_files=None
  scope_transition_approved=None
```

For both records, the declared handoff and log exist, but the declared instance
record does not:

```text
CLAIM-SCOUT-TASKSET-AR-V080-OPERABILITY-HARDENING-W1
  handoff_exists=True
  log_exists=True
  instance_exists=False
  pane_events=['progress_scout_sweep']
  accepted_lifecycle_events=[]

CLAIM-REVIEW-TASK-AR-653-independent-auditor-closeout
  handoff_exists=True
  log_exists=True
  instance_exists=False
  pane_events=['review_pass_dispatched']
  accepted_lifecycle_events=[]
```

The handoffs and logs contain only creation metadata. `git worktree list
--porcelain` showed only the control clone on main; no overlay-named local
branch exists; and `git log --all --grep` returned no commit for either claim
ID. On the authoritative repository/runtime surfaces, there is therefore no
evidence of a separate agent executing or producing implementation.

## Direct owner-chain gate results

The affected check-mode members of `scripts/owner_governance_gate.py` were
executed directly with bytecode writes disabled.

### Agent identity — blocking

```text
$ env PYTHONDONTWRITEBYTECODE=1 python scripts/agent_identity_gate.py --check
agent-identity-gate: fail
findings=2
- agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-653-independent-auditor-closeout.json: agent-identity:instance-missing:CLAIM-REVIEW-TASK-AR-653-independent-auditor-closeout:independent-auditor-CLAIM-REVIEW-TASK-AR-653-independent-auditor-closeout
- agents/runtime/task_claims/CLAIM-SCOUT-TASKSET-AR-V080-OPERABILITY-HARDENING-W1.json: agent-identity:instance-missing:CLAIM-SCOUT-TASKSET-AR-V080-OPERABILITY-HARDENING-W1:progress-scout-CLAIM-SCOUT-TASKSET-AR-V080-OPERABILITY-HARDENING-W1
```

### RBAC/current-agents — blocking

`agents/project/NEXT-SESSION-POINTER.yml` currently has
`current_agents: []` and `active_claims: []`.

```text
$ env PYTHONDONTWRITEBYTECODE=1 python scripts/rbac_write_gate.py --check
rbac-write-gate: fail
findings=2
- rbac-current-agents:missing-active-claim:CLAIM-REVIEW-TASK-AR-653-independent-auditor-closeout
- rbac-current-agents:missing-active-claim:CLAIM-SCOUT-TASKSET-AR-V080-OPERABILITY-HARDENING-W1
```

The RBAC gate's accepted pane lifecycle set is:

```text
claim_created, claim_heartbeat, claimed, heartbeat,
pane_heartbeat, pane_started, started
```

The scout has only `progress_scout_sweep`; the review overlay has only
`review_pass_dispatched`. Neither is an accepted lifecycle event. The live gate
reports the missing `current_agents` entries first and skips subsequent
per-claim checks, but a direct comparison against
`rbac_write_gate.PANE_LIFECYCLE_EVENTS` returned
`accepted_lifecycle_events=[]` for both. Merely projecting the two records into
`current_agents` would therefore expose the next
`rbac-current-agents:missing-pane-event` inconsistency.

### Taskset boundary approval — blocking

```text
$ env PYTHONDONTWRITEBYTECODE=1 python scripts/taskset_boundary_gate.py --check
taskset-boundary-gate: fail
findings=36
```

Both claims omit `scope_transition_approved`. The gate emits the same exact
`taskset:boundary-violation` shape for each claim against 18 completed scopes:

```text
taskset:boundary-violation:
completed-scope=<scope>:
new-out-of-scope-claim=<claim-id>:
task-set=TASKSET-AR-V080-OPERABILITY-HARDENING
```

The 18 scopes are:

```text
TASKSET-AR-BUSINESS-OPERATING-SYSTEM
TASKSET-AR-BUSINESS-OPERATIONS-TEAMS
TASKSET-AR-DESIGN-SYSTEM-ASSETIZATION
TASKSET-AR-DESIGN-SYSTEM-COMPONENT-PATTERNS
TASKSET-AR-DESIGN-SYSTEM-DEBT-CONSOLIDATION
TASKSET-AR-DESIGN-SYSTEM-GOVERNANCE
TASKSET-AR-DESIGN-SYSTEM-SERVED-ASSET-SPLIT
TASKSET-AR-DESIGN-SYSTEM-TOKEN-DEBT
TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
TASKSET-AR-RELEASE-AUTO-FIXTURE-HEAD-RECOVERY
TASKSET-AR-RELEASE-AUTO-FIXTURE-RECOVERY-WINDOW
TASKSET-AR-RELEASE-CADENCE-QUERY-RECOVERY
TASKSET-AR-SELF-EVAL-QUERY-INTEGRITY
TASKSET-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE
TASKSET-AR-VISUAL-ASSET-ADOPTION
TASKSET-AR-VISUAL-SYSTEM-INTEGRATION
TASKSET-AR-WORK-CLI-INTEGRITY
TASKSET-AR-WORK-VERIFY-WINDOWS-SHELL-INTEGRITY
```

That is 18 findings per claim, 36 total.

### Overlay-aware comparison gates

The following direct checks passed:

```text
$ env PYTHONDONTWRITEBYTECODE=1 python scripts/parallel_worktree_gate.py --check
parallel-worktree-gate: pass
block=0

$ env PYTHONDONTWRITEBYTECODE=1 python scripts/state_sync_gate.py --check
state-sync-gate: pass
findings=0
block=0
watch=0
```

`parallel_worktree_gate` emitted persistence watches but no block. These passes
do not neutralize the three blocking owner-chain members above; instead, they
demonstrate the lifecycle contract split: some gates explicitly exempt
overlays while identity, RBAC, and taskset-boundary gates still treat them as
fully active agent claims.

## Release recursion and loss-safety

### Nested review guard

`task_claim_dispatcher.cmd_release` normalizes the claim's `overlay` marker and
calls `role_routing.route_review_pass` only when `not is_overlay`
(`scripts/task_claim_dispatcher.py:2036-2053`). Both target records use the
canonical boolean `true`, so standard release cannot create a nested
`REVIEW-REVIEW` claim.

Focused regression evidence:

```text
$ env -u OPENAI_API_KEY PYTHONDONTWRITEBYTECODE=1 \
    PYTEST_ADDOPTS='-p no:cacheprovider' \
    python -m pytest \
    'tests/test_role_routing_wiring.py::test_releasing_overlay_does_not_route_nested_review_claim' \
    -q
....                                                                     [100%]
4 passed in 0.96s
```

The four cases exercise `overlay` values `True`, `"true"`, `1`, and `"1"` and
assert that release leaves exactly the primary plus its one overlay, with no
`REVIEW-REVIEW` claim (`tests/test_role_routing_wiring.py:271-292`).

### No worker or implementation loss

Neither overlay owns a worktree, branch, target footprint, implementation
commit, or SCM-write authority. Both use synthetic task IDs distinct from
`TASK-AR-653` and have remained at zero progress.

Standard dispatcher release updates the selected claim JSON with released
status and verifier evidence, then appends lifecycle/A2A evidence
(`scripts/task_claim_dispatcher.py:1979-2022`). It contains no branch,
worktree, or implementation-file deletion. Releasing these two overlays
therefore cannot discard TASK-AR-653 worker code, commits, or worktree
artifacts; none are attached to these records.

## Findings

### P1-1 — Scout overlay is an active synthetic claim outside the full lifecycle contract

The scout is a direct routing artifact with handoff/log only. It has no
instance, accepted pane lifecycle, current-agents projection, scope-transition
approval, or executable work. It blocks the owner identity, RBAC, and taskset
boundary checks. Supersede and release it.

### P1-2 — Review overlay is an active synthetic claim outside the full lifecycle contract

The independent-auditor overlay has the same lifecycle defects and was not an
actual independent TASK-AR-653 review. Its role-like name must not be mistaken
for a running verifier or final W4b. Supersede and release it.

## Exact release recommendation

After this report exists at its committed/staged repository-relative path, the
orchestrator should run:

```bash
python scripts/task_claim_dispatcher.py release \
  --claim-id CLAIM-REVIEW-TASK-AR-653-independent-auditor-closeout \
  --verified-by qa-20260730-ar653-overlay-lifecycle-supersession \
  --verifier-role qa-reviewer \
  --verification-evidence reviews/W4B-2026-07-30-task-ar-653-overlay-claim-lifecycle-supersession.md

python scripts/task_claim_dispatcher.py release \
  --claim-id CLAIM-SCOUT-TASKSET-AR-V080-OPERABILITY-HARDENING-W1 \
  --verified-by qa-20260730-ar653-overlay-lifecycle-supersession \
  --verifier-role qa-reviewer \
  --verification-evidence reviews/W4B-2026-07-30-task-ar-653-overlay-claim-lifecycle-supersession.md
```

Do not use `--allow-missing-evidence`. Release both before judging owner-gate
recovery, then rerun at minimum:

```bash
python scripts/agent_identity_gate.py --check
python scripts/rbac_write_gate.py --check
python scripts/taskset_boundary_gate.py --check
```

This recommendation closes only the two administrative overlay lifecycles. A
fresh worker W4a and a distinct implementation reviewer must still produce the
real TASK-AR-653 final W4b.
