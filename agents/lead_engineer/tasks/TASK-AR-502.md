---
id: TASK-AR-502
display_id: TASK-AR-502
task_uid: 59fda519-2e92-43bb-b20a-5233183b9d25
registered_at: 2026-06-12T18:35:45+09:00
created_at: 2026-06-12T18:35:45+09:00
updated_at: 2026-06-12T18:35:45+09:00
title: Integrator merge queue — serial rebase-test-merge for worker branches
status: planned
priority: P2
difficulty: M
est_hours: 8
est_tokens: 6000
owner: lead_engineer
initiative_id: INIT-AR-PARALLEL-WAVE-EXECUTION
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-PARALLEL-WAVE-EXECUTION
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
escalation_triggers:
  - cross_cutting
  - repeated_failure
tags:
  - parallel
  - merge-queue
  - integration
---

# TASK-AR-502 - Integrator merge queue

## Goal

- 워커 브랜치의 main 합류를 단일 통합자(orchestrator)가 직렬
  rebase-test-merge 큐로 처리해, 병렬 구현 기간에도 merge 충돌과 공유
  SSoT 경합이 발생하지 않게 한다.

## Context

- 기존 Decision(PARALLEL_SESSION_PROTOCOL): main checkout = orchestrator
  전용 + 공유 SSoT 유일 작성자. 이 task는 그 결정의 머지 절차 구현이다.
- 병렬 wave 완료 시 N개 브랜치가 동시에 합류 대기 — 순서 없는 머지는
  보드/INDEX/BACKLOG 재생성 경합을 만든다.

## Preconditions

- 착수(claim) 전 `python scripts/plan_assumption_gate.py --check --taskset TASKSET-AR-PARALLEL-WAVE-EXECUTION` 실행 — drift 발견 시 replan 리뷰(차분 재계획 + anchor 갱신) 선행 필수. 근거: `reviews/MEETING-2026-06-12-plan-assumption-deferred-revalidation.md`.

## Scope

- `scripts/merge_queue.py`: 합류 대기 브랜치 등록 → 순차 rebase → 좁은
  검증(해당 unit verification + 게이트 체인) → merge → 보드/INDEX 재생성
  → 다음 항목. 실패 항목은 큐에서 제외하고 워커에 피드백 기록.
- 큐 상태를 `agents/runtime/`에 JSON으로 기록해 ui-console에서 관측 가능하게.
- wave 경계 풀 사이클(보드 재생성·retro 트리거)과의 연결 지점 정의.
- 템플릿 미러 동기화.

## Out Of Scope

- GitHub PR API 자동화(로컬 브랜치 큐가 우선).
- 충돌 자동 해소(충돌 시 워커/Owner 에스컬레이션).

## Acceptance Criteria

- 서로소 footprint 브랜치 3개가 큐를 통해 순차 합류하고 보드가 1회만
  재생성된다.
- 검증 실패 브랜치는 main을 오염시키지 않고 피드백 기록을 남긴다.
- `pytest tests -q` 통과, 게이트 체인 exit 0.

## Evidence Targets

- `scripts/merge_queue.py` + 테스트
- 큐 상태 JSON 스키마
- closeout review record
