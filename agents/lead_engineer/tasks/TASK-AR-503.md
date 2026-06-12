---
id: TASK-AR-503
display_id: TASK-AR-503
task_uid: 4966fce3-64b3-4b7b-a484-e4e503a993e2
registered_at: 2026-06-12T18:35:45+09:00
created_at: 2026-06-12T18:35:45+09:00
updated_at: 2026-06-12T18:35:45+09:00
title: Claim-first enforcement — no worktree work without a main-side claim
status: planned
priority: P1
difficulty: S
est_hours: 4
est_tokens: 3000
owner: lead_engineer
initiative_id: INIT-AR-PARALLEL-WAVE-EXECUTION
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-PARALLEL-WAVE-EXECUTION
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
escalation_triggers:
  - repeated_failure
tags:
  - parallel
  - claim
  - gate
  - observability
---

# TASK-AR-503 - Claim-first enforcement

## Goal

- 워크트리 작업은 반드시 main 체크아웃에 활성 클레임을 먼저 남기고
  시작하도록 강제한다. 클레임 없는 워크트리 작업은 보드/ui-console 양쪽에서
  보이지 않는 관측 사각을 만든다.

## Context

- 실측 사례(2026-06-12): AR-372 작업이 워크트리 4개에서 진행되는 동안
  main에 클레임이 없어 Owner가 "백로그가 멈췄다"고 인지 — 관측 규약 위반.
  기록: `reviews/REVIEW-2026-06-12-agent-runtime-parallel-wave-scheduling-design.md`.
- `parallel_worktree_gate`는 클레임이 "있을 때"의 정합만 검사하고, 클레임
  없이 존재하는 작업 워크트리는 잡지 않는다.

## Preconditions

- 착수(claim) 전 `python scripts/plan_assumption_gate.py --check --taskset TASKSET-AR-PARALLEL-WAVE-EXECUTION` 실행 — drift 발견 시 replan 리뷰(차분 재계획 + anchor 갱신) 선행 필수. 근거: `reviews/MEETING-2026-06-12-plan-assumption-deferred-revalidation.md`.

## Scope

- `parallel_worktree_gate.py`(또는 신규 검사) 확장: `.worktrees/` 하위
  task 브랜치 워크트리 중 대응하는 main 클레임(활성 또는 released)이 없는
  경우 watch/block finding 생성.
- 예외 허용 목록(예: 실험용 spike 워크트리)을 명시적 태그로 정의.
- Stop hook / owner governance 체인에 포함 확인.
- 템플릿 미러 동기화.

## Out Of Scope

- 클레임 자동 생성(워커 프로토콜 준수가 원칙, 게이트는 감지만).
- 과거 사례 소급 처리.

## Acceptance Criteria

- 클레임 없는 task 워크트리가 존재하면 게이트가 finding을 보고한다.
- 클레임이 정상 존재하는 워크트리는 통과한다.
- `pytest tests -q` 통과, 게이트 체인 exit 0.

## Evidence Targets

- 게이트 변경분 + 테스트
- closeout review record
