---
type: w4b-independent-verification
title: TASK-AR-601 Hardening W4b Independent Verification
date: 2026-07-19
task_id: TASK-AR-601
unit_id: UNIT-TASK-AR-601-001
task_set_id: TASKSET-AR-ROLE-ROUTING-CLOSEOUT-RELIABILITY
claim_id: CLAIM-20260719-110938-task-ar-601-overlay-closeout
status: approved
signal: pass
worker_agent_id: codex-root-task-ar-601
verifier_agent_id: codex-independent-verifier-task-ar-601-hardening-20260719
verifier_role: independent-w4b
branch: codex/task-ar-601-overlay-closeout
baseline_commit: 652f46f
hardening_commit: aa3d9a5
verified_at: 2026-07-19T11:36:45+09:00
resolves_findings:
  - SKEPTIC-601-001
  - SKEPTIC-601-002
  - SKEPTIC-601-003
preserves_evidence:
  - reviews/W4B-2026-07-19-TASK-AR-601.md
  - reviews/W4B-2026-07-19-TASK-AR-601-RECHECK.md
findings: []
---

# TASK-AR-601 Hardening W4b Independent Verification

## Verdict

APPROVE.

Hardening commit `aa3d9a5` closes all three findings from the TASK-AR-601
skeptic review. The release boundary now conservatively recognizes truthy
non-boolean overlay markers, partial overlay publication rolls back sidecar
artifacts when claim JSON publication fails, a real artifact-path fault remains
isolated from the completed primary release, and an explicit environment value
overrides committed role-routing configuration in both directions.

The focused suite passes 73/73 tests on Python 3.10.11. The taskset gate, host
lock check, compilation check, lock non-drift check, and branch diff check also
pass. No blocking finding remains.

## Skeptic Finding Decisions

| Finding | Required threshold | Measured result | Status |
| --- | --- | --- | --- |
| `SKEPTIC-601-001` | Releasing overlays marked `true`, `"true"`, `1`, or `"1"` creates zero nested review claims | All four releases exit 0; final claim count remains two; no claim ID contains `REVIEW-REVIEW` | PASS |
| `SKEPTIC-601-002` / JSON rollback | Injected claim JSON publication failure leaves no claim, handoff, or log artifact | `write_json_atomic` raises the injected `OSError`; the deterministic `CLAIM-REVIEW-TASK-AR-900-*` artifact set is empty afterward | PASS |
| `SKEPTIC-601-002` / real release fault | An actual artifact publication failure cannot fail or roll back primary release | A directory at the deterministic handoff path makes artifact publication fail after the claim-JSON existence check; release exits 0, primary status is `released`, and no overlay JSON/log appears | PASS |
| `SKEPTIC-601-003` / kill switch | Committed config `role_routing: true` plus `AR_ROLE_ROUTING=0` is disabled | Result is disabled and creates zero overlays | PASS |
| `SKEPTIC-601-003` / override | Config `role_routing: false` plus `AR_ROLE_ROUTING=1` is enabled | Result is enabled and creates one overlay | PASS |

## Implementation Review

- `task_claim_dispatcher.cmd_release` derives one conservative `is_overlay`
  predicate. Boolean/numeric values use their truth value, known false strings
  remain false, and all other non-null objects are treated as overlays. This
  prevents malformed or legacy truthy markers from entering review routing.
- `_write_overlay_claim` tracks handoff and log artifacts only after successful
  publication. If a later publication step raises, it removes the published
  sidecars in reverse order and re-raises the original failure.
- Release routing remains inside the existing best-effort exception boundary,
  after the primary release state has been persisted. The actual handoff-path
  collision therefore exercises a real write fault without changing release
  success.
- `_feature_enabled` checks a non-empty explicit environment value before the
  committed configuration. This makes `0` an effective kill switch and `1` an
  effective emergency override. With no explicit environment value, committed
  configuration continues to control activation.
- The committed root configuration currently has `role_routing: true`, so the
  config-true/environment-zero regression covers the production-relevant
  precedence case identified by the skeptic.

## Verification Commands

```powershell
$env:PATH='C:\Users\ycpig\AppData\Local\Programs\Python\Python310;' + $env:PATH
$env:PYTHONDONTWRITEBYTECODE='1'

python -m pytest `
  tests/test_role_routing.py `
  tests/test_role_routing_wiring.py `
  tests/test_task_claim_dispatcher.py -q -p no:cacheprovider
# 73 passed in 27.89s

python -m pytest `
  tests/test_role_routing.py::test_explicit_environment_value_overrides_committed_config `
  tests/test_role_routing.py::test_json_publish_failure_rolls_back_overlay_artifacts `
  tests/test_role_routing_wiring.py::test_releasing_overlay_does_not_route_nested_review_claim `
  tests/test_role_routing_wiring.py::test_release_routing_failure_never_breaks_release `
  -vv -p no:cacheprovider
# 8 passed in 4.85s

python scripts/taskset_work_gate.py `
  --task-set-id TASKSET-AR-ROLE-ROUTING-CLOSEOUT-RELIABILITY --check
# taskset-work-gate: pass
# findings=0

py -3.10 scripts/regen_host_lock_if_needed.py --check
# OK: tests/fixtures/host/agent_runtime.lock.json is up to date.

git diff --exit-code 652f46f..aa3d9a5 -- `
  tests/fixtures/host/agent_runtime.lock.json
# exit 0, no output

py -3.10 -m py_compile `
  scripts/role_routing.py `
  scripts/task_claim_dispatcher.py
# exit 0, no output

git diff --check 652f46f..aa3d9a5
# exit 0, no output
```

## Residual Risk and Scope

- Rollback cleanup is deliberately best effort. If the filesystem refuses the
  cleanup `unlink`, an orphan sidecar may remain, but no overlay claim JSON is
  published and the primary release remains valid.
- An empty environment value is treated as unset and therefore falls back to
  committed configuration. The verified operator controls are explicit `0`
  and `1` values.
- Generated-host routing remains outside the recorded T3 live-checkout scope,
  as documented by the prior W4b recheck.
- The original FAIL and RECHECK reports remain unchanged as historical
  evidence. This verifier changed no code, claim, release state, or shared
  index.
