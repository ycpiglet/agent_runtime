---
type: w4b-independent-verification
title: TASK-AR-601 W4b Independent Verification Recheck
date: 2026-07-19
task_id: TASK-AR-601
unit_id: UNIT-TASK-AR-601-001
task_set_id: TASKSET-AR-ROLE-ROUTING-CLOSEOUT-RELIABILITY
claim_id: CLAIM-20260719-110938-task-ar-601-overlay-closeout
status: approved
signal: pass
worker_agent_id: codex-root-task-ar-601
verifier_agent_id: codex-independent-verifier-task-ar-601-recheck-20260719
verifier_role: independent-w4b
branch: codex/task-ar-601-overlay-closeout
design_replan_commit: 758659d
implementation_commit: 43a6b9f
w4a_revalidation_commit: 9d0bfae
verified_at: 2026-07-19T11:20:11+09:00
supersedes_blocker_in: reviews/W4B-2026-07-19-TASK-AR-601.md
findings: []
---

# TASK-AR-601 W4b Independent Verification Recheck

## Verdict

APPROVE.

T3 replan commit `758659d` preserves the first W4b failure as historical
evidence and corrects the registered scope to the live-checkout role-routing
seam where the TASK-AR-594 incident occurred. The generated host scaffold does
not ship `role_routing.py` or the activation configuration, so host routing is
now explicitly a separate product-surface decision and out of this repair.

Against that re-anchored contract, implementation commit `43a6b9f` and W4a
revalidation commit `9d0bfae` pass every acceptance criterion. No blocking
findings remain.

## T3 Scope Review

- `TASK-AR-601.md`, its unit spec, the work-registration JSON, the registration
  review, and the plan-assumption anchors consistently describe the live seam.
- The unit target list no longer claims to modify the host-template dispatcher.
- The registration review records why host routing is not silently omitted:
  enabling it in generated hosts requires shipping a new module, activation
  config, dependencies, and product behavior beyond the observed closeout bug.
- `tests/fixtures/host/agent_runtime.lock.json` remains a non-drift check and is
  unchanged from replan commit `758659d` through W4a commit `9d0bfae`.

The scope correction is therefore an explicit T3 product-boundary decision,
not an attempt to redefine completed implementation after the fact.

## Requirement Decisions

| Metric | Threshold | Measured value | Source | Status |
| --- | --- | --- | --- | --- |
| Overlay lifecycle pointers | Every generated overlay JSON points to existing handoff/log files | Both paths resolve to files and contain the claim ID | role-routing unit/E2E tests | PASS |
| Artifact-before-JSON ordering | Handoff and log writes occur before claim JSON exposure, with both pointers already in the claim | Static offsets: handoff `1860`, log `2237`, JSON `2546`; both pointer entries precede JSON | `_write_overlay_claim` source-order assertion | PASS |
| Ordinary routing ON | Non-high-risk worker release creates exactly one additive auditor overlay | Primary remains released lead claim; overlay role set is exactly `independent-auditor` | focused E2E tests | PASS |
| Overlay release with routing ON | Overlay release succeeds and creates no nested review claim | Claim count remains two, overlay is released, no `REVIEW-REVIEW` ID | `test_releasing_overlay_does_not_route_nested_review_claim` | PASS |
| Flag OFF inertness | Release behavior is unchanged with zero overlays/events | Exactly one released primary claim | `test_release_with_role_routing_off_creates_no_overlay_claim` | PASS |
| Routing fault tolerance | Overlay write failure cannot fail the primary release | Collision-induced routing fault still returns exit 0 and primary is released | `test_release_routing_failure_never_breaks_release` | PASS |
| Focused suite | 67/67 tests pass on required runtime | Python 3.10.11, `67 passed in 23.42s` | pytest | PASS |
| Core acceptance subset | Six named live-contract tests pass independently | `6 passed in 4.13s` | verbose pytest run | PASS |
| Taskset gate | Zero findings | `taskset-work-gate: pass`, `findings=0` | taskset gate | PASS |
| Host lock | Current and unchanged across implementation/W4a | Regeneration check passes; `git diff 758659d 9d0bfae -- lock` is empty | lock check and git | PASS |
| Branch diff quality | No whitespace errors | `git diff --check 758659d..9d0bfae` exits zero | git | PASS |

## Verification Commands

```powershell
$env:PATH='C:\Users\ycpig\AppData\Local\Programs\Python\Python310;' + $env:PATH
$env:PYTHONDONTWRITEBYTECODE='1'

python -m pytest `
  tests/test_role_routing.py `
  tests/test_role_routing_wiring.py `
  tests/test_task_claim_dispatcher.py -q -p no:cacheprovider
# 67 passed in 23.42s

python -m pytest `
  tests/test_role_routing.py::test_review_routing_on_creates_additive_claim_without_touching_lead `
  tests/test_role_routing_wiring.py::test_release_with_role_routing_off_creates_no_overlay_claim `
  tests/test_role_routing_wiring.py::test_release_with_role_routing_on_creates_additive_review_overlay `
  tests/test_role_routing_wiring.py::test_releasing_overlay_does_not_route_nested_review_claim `
  tests/test_role_routing_wiring.py::test_release_routing_failure_never_breaks_release `
  tests/test_role_routing_wiring.py::test_non_high_risk_release_is_auditor_only `
  -vv -p no:cacheprovider
# 6 passed in 4.13s

python scripts/taskset_work_gate.py `
  --task-set-id TASKSET-AR-ROLE-ROUTING-CLOSEOUT-RELIABILITY --check
# taskset-work-gate: pass
# findings=0

py -3.10 scripts/regen_host_lock_if_needed.py --check
# OK: tests/fixtures/host/agent_runtime.lock.json is up to date.

git diff --exit-code 758659d 9d0bfae -- `
  tests/fixtures/host/agent_runtime.lock.json
# exit 0, no output

git diff --check 758659d..9d0bfae
# exit 0, no output
```

The artifact ordering check imported the current live `role_routing` module,
inspected `_write_overlay_claim`, and asserted:

```json
{
  "order": "handoff < log < json",
  "artifact_before_json": true,
  "pointers_before_json": true
}
```

## Code Review

- Overlay artifact names are deterministic derivatives of the overlay claim ID.
- The handoff and log records are atomically written before the claim JSON, so
  a visible overlay claim never advertises missing lifecycle pointers.
- Release routing is skipped only when `claim.overlay is True`; ordinary claims
  continue through the existing flag-gated additive review path.
- Routing remains best effort inside the existing broad exception boundary, so
  an overlay artifact or routing fault cannot roll back a completed release.
- Flag OFF remains the default and creates no overlay artifacts or routing
  events.

## Residual Risk and Scope

- A failure after the first artifact write but before claim JSON may leave an
  orphan artifact. It does not expose a broken claim, satisfies the lifecycle
  safety requirement, and can be handled by routine stale-artifact cleanup.
- Generated-host role routing remains intentionally unavailable until a
  separate product decision specifies its modules, activation config,
  dependencies, tests, and migration behavior.
- The original FAIL report remains valid evidence of the pre-T3 specification
  mismatch; this recheck supersedes its blocker only under the recorded T3
  scope.
- The verifier did not modify code, claims, release state, or shared indexes.
