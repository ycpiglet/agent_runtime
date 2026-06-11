---
id: TASK-AR-314
display_id: TASK-AR-314
task_uid: 616a4093-befe-4d53-bbdb-d0b49ad9cc9c
registered_at: 2026-06-11T17:58:45+09:00
created_at: 2026-06-11T17:58:45+09:00
started_at: 2026-06-12T00:37:16+09:00
updated_at: 2026-06-12T00:44:07+09:00
title: Race-safe message claiming 및 stale-leader 복구 (Phase 4)
status: completed
completed_at: 2026-06-12T00:44:07+09:00
priority: P1
difficulty: L
est_hours: 8
est_tokens: 6000
owner: lead_engineer
task_set_id: TASKSET-AR-VISION-GAP-CLOSURE
tags:
  - concurrency
  - claims
  - loop-engineering
---

# TASK-AR-314 - Race-safe message claiming 및 stale-leader 복구 (Phase 4)

## Goal

- 리스 기반 클레임 원시 연산으로 다중 프로세스 환경의 중복 응답/소유권 경합을 구조적으로 차단한다.

## Scope

- IMPLEMENTATION_PLAN.md Phase 4: `agents/runtime/claims/` 리스 기반 클레임 구현.
- 동시 클레임 테스트(`test_concurrent_claim_two_workers`)로 단일 승자 보장 증명.
- stale-leader 복구 정책(무응답 + 만료 리스 + 소스 유지 시에만 재클레임) 다중 프로세스 증거 확보.

## Acceptance Criteria

- 동시 클레임 테스트 통과, 중복 응답 0건 증거 기록.
- stale 클레임 복구 시나리오가 결정적으로 재현/통과한다.

## Evidence Targets

- `agents/runtime/claims/` 및 동시성 테스트
- `IMPLEMENTATION_PLAN.md` Phase 4 섹션

## Completion - 2026-06-12

- Result: `scripts/claim_lease.py`를 추가해 `agents/runtime/claims/*.lease.json` 기반 atomic lease primitive를 만들었다.
- Race safety: lease별 `.lock` 파일을 `O_CREAT | O_EXCL`로 잡고 atomic replace로 lease를 쓰기 때문에 두 worker가 같은 message/resource를 동시에 claim해도 단일 승자만 남는다.
- Stale recovery: active lease는 차단하고, 만료된 lease는 `--recover-stale`이 명시되어 있으며 원본 source file이 남아 있을 때만 새 owner가 인계한다.
- Template parity: 같은 스크립트를 `src/agent_runtime/templates/project/scripts/claim_lease.py`에 반영하고 fixture lock을 갱신했다.
- Closeout review: `reviews/REVIEW-2026-06-12-claim-lease-closeout.md`.
- Verification:
  - `python -m py_compile scripts/claim_lease.py src/agent_runtime/templates/project/scripts/claim_lease.py` -> pass.
  - `pytest tests/test_claim_lease.py -q` -> 2 passed.
  - `PYTHONPATH=src python -m agent_runtime.cli lock --root tests/fixtures/host --check` -> findings=0.
  - `pytest tests/test_claim_lease.py tests/test_template_smoke.py::test_sync_and_smoke_runtime_scripts -q` -> 3 passed.
  - `python scripts/owner_governance_gate.py` -> exit 0.
