---
id: TASK-AR-504
display_id: TASK-AR-504
task_uid: acd02367-581c-412f-97e3-dbee4b99fb5f
registered_at: 2026-06-12T18:51:54+09:00
created_at: 2026-06-12T18:51:54+09:00
started_at: 2026-06-12T18:51:54+09:00
updated_at: 2026-06-12T18:55:00+09:00
title: Plan assumption gate — deferred revalidation for parallel-session plans
status: completed
completed_at: 2026-06-12T18:55:00+09:00
priority: P1
difficulty: S
est_hours: 3
est_tokens: 3000
owner: lead_engineer
initiative_id: INIT-AR-PARALLEL-WAVE-EXECUTION
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-PARALLEL-WAVE-EXECUTION
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
escalation_triggers:
  - cross_cutting
tags:
  - parallel
  - plan-governance
  - lazy-evaluation
  - gate
---

# TASK-AR-504 - Plan assumption gate (deferred revalidation)

## Goal

- 병렬 세션(codex/claude)이 서로의 미머지 변경을 모른 채 세운 계획이
  merge 후 조용히 무효화되는 문제를 지연평가로 해결한다: 계획의 전제를
  등록 시점에 스냅샷하고, 평가는 착수(claim) 시점으로 미룬다. 전제가
  변했으면 착수를 차단하고 replan 리뷰를 요구한다.

## Context

- Owner 결정(2026-06-12): codex의 대대적 스키마 변경(WORK-SCHEMA.yml,
  TASKSET-DEFINITIONS.json 등)과 본 taskset 계획이 틀어질 수 있으므로,
  두 작업을 독립 진행한 뒤 나중에 재점검·검증하는 다단계 트리거를 설정.
  기록: `reviews/MEETING-2026-06-12-plan-assumption-deferred-revalidation.md`.
- 의도적으로 owner governance 커밋 체인에는 넣지 않는다 — merge 후
  드리프트는 "착수를 막아야 할 정상 상태"지 무관한 커밋을 막을 결함이
  아니다 (T2 dispatch-time 차단).

## Trigger Points

- T0 등록: `record`로 전제 스냅샷 기록 (본 세션에서 수행 완료).
- T1 관찰: merge 후 `--check` (비차단, 정보성).
- T2 착수: AR-500~503 claim 전 `--check --taskset ...` 필수 — drift 시
  replan 리뷰 선행.
- T3 재계획: replan 리뷰가 anchors를 `record`로 갱신한 뒤 착수.

## Scope (구현 완료)

- `scripts/plan_assumption_gate.py`: `record`(sha256/absent anchor 스냅샷),
  `--check [--taskset X]`(드리프트 보고, exit 1).
- `agents/project/work-items/PLAN-ASSUMPTIONS.json` 레지스트리
  (agent-runtime-plan-assumptions/v1).
- TASKSET-AR-PARALLEL-WAVE-EXECUTION 전제 8개 기록: 의존 파일 4개
  sha256(taskset_dispatcher, task_claim_dispatcher, parallel_worktree_gate,
  units/README), codex 신설 예정 파일 4개 absent(WORK-SCHEMA.yml,
  TASKSET-DEFINITIONS.json, TASK-ID-RESERVATIONS.json, work.py).
- AR-500~503 task 레코드에 Preconditions(T2 차단) 명시.
- `tests/test_plan_assumption_gate.py` 4건, 템플릿 미러 동기화.

## Out Of Scope

- owner governance 체인 편입 (codex가 owner_governance_gate.py 수정 중 —
  충돌 표면이며 의미상으로도 dispatch-time 게이트).
- 자동 replan 생성 (드리프트 보고까지만, 재계획은 planner 책임).

## Acceptance Criteria

- 전제 파일 수정 또는 absent 파일 등장 시 `--check`가 exit 1로 차단하고
  대상 anchor를 보고한다. (테스트로 검증)
- 현재 main 기준 `--check` exit 0. (수행 완료)
- `pytest tests/test_plan_assumption_gate.py -q` 통과. (4 passed)

## Evidence Targets

- `scripts/plan_assumption_gate.py`, `tests/test_plan_assumption_gate.py`
- `agents/project/work-items/PLAN-ASSUMPTIONS.json`
- `reviews/MEETING-2026-06-12-plan-assumption-deferred-revalidation.md`
