---
id: TASK-AR-314
display_id: TASK-AR-314
task_uid: 616a4093-befe-4d53-bbdb-d0b49ad9cc9c
registered_at: 2026-06-11T17:58:45+09:00
created_at: 2026-06-11T17:58:45+09:00
updated_at: 2026-06-11T17:58:45+09:00
title: Race-safe message claiming 및 stale-leader 복구 (Phase 4)
status: planned
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
