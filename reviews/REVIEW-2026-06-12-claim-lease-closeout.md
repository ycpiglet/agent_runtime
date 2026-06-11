---
type: brief
id: REVIEW-2026-06-12-claim-lease-closeout
audience: owner
signal: pass
score: 93
priority: High
tags: [claims, concurrency, lease, stale-recovery]
actions: [archive, continue-taskset]
evidence:
  - scripts/claim_lease.py
  - src/agent_runtime/templates/project/scripts/claim_lease.py
  - tests/test_claim_lease.py
  - agents/lead_engineer/tasks/TASK-AR-314.md
---

Bottom Line: TASK-AR-314는 pass다. message/resource claim을 append-only 추론이 아니라 atomic lease primitive로 분리했고, 동시 worker 경쟁과 stale-leader 복구 조건을 테스트로 고정했다.

## Signal

| Item | State | Evidence |
|------|-------|----------|
| Single winner under race | pass | `test_concurrent_claim_two_workers` |
| Active lease blocking | pass | second worker receives `lease-active` |
| Stale recovery guard | pass | recovery requires `--recover-stale` and expired lease |
| Source-presence guard | pass | missing source blocks stale recovery with `source-missing` |
| Host-project parity | pass | template script and fixture lock updated |

## Insight

1. Claim ownership should be a small file-system primitive before higher-level A2A routing consumes it.
2. Stale recovery needs two separate checks: the leader lease must be expired, and the original source must still exist.
3. Returning structured JSON for both acquired and blocked outcomes lets worker loops make deterministic routing decisions without parsing logs.

## Decision

1. Use `scripts/claim_lease.py acquire` as the local primitive for race-safe worker/message ownership.
2. Keep recovery opt-in through `--recover-stale`; normal workers should not silently take over expired work unless the dispatch policy explicitly chooses recovery.
3. Mirror this primitive into generated host projects so host repos inherit the same concurrency contract.

## Action Board

| Action | Owner | State |
|--------|-------|-------|
| Add atomic lease primitive | Lead Engineer | pass |
| Add concurrent two-worker test | QA | pass |
| Add stale recovery/source guard test | QA | pass |
| Update generated-project template parity | Lead Engineer | pass |

## Next

| Step | Owner | Trigger |
|------|-------|---------|
| Continue Vision Integrator taskset | dispatcher | next planned task |
| Integrate claim lease into higher-level runtime loops | future task | when worker/message dispatch starts consuming claims |

## Verification

- `python -m py_compile scripts/claim_lease.py src/agent_runtime/templates/project/scripts/claim_lease.py` -> pass.
- `pytest tests/test_claim_lease.py -q` -> 2 passed.
- `PYTHONPATH=src python -m agent_runtime.cli lock --root tests/fixtures/host --check` -> findings=0.
- `pytest tests/test_claim_lease.py tests/test_template_smoke.py::test_sync_and_smoke_runtime_scripts -q` -> 3 passed.
- `python scripts/owner_governance_gate.py` -> exit 0.
