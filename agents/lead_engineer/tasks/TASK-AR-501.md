---
id: TASK-AR-501
display_id: TASK-AR-501
task_uid: cb503e0c-71fa-4aba-818b-5deec1412813
registered_at: 2026-06-12T18:35:45+09:00
created_at: 2026-06-12T18:35:45+09:00
updated_at: 2026-06-13T09:30:00+09:00
started_at: 2026-06-13T02:45:16+09:00
completed_at: 2026-06-13T09:30:00+09:00
title: Wave dispatcher — DAG/topological wave grouping + cascade/parallel mode
status: completed
priority: P1
difficulty: L
est_hours: 10
est_tokens: 8000
owner: lead_engineer
initiative_id: INIT-AR-PARALLEL-WAVE-EXECUTION
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-PARALLEL-WAVE-EXECUTION
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
escalation_triggers:
  - ambiguity
  - cross_cutting
tags:
  - parallel
  - dispatcher
  - scheduling
---

# TASK-AR-501 - Wave dispatcher with cascade/parallel modes

## Goal

- planner가 unit 의존성 DAG를 topological wave로 분해하고, 디스패처가
  같은 wave의 K개 unit에 대해 claim+worktree를 일괄 발급할 수 있게 한다.
  실행 모드는 Owner 옵션: cascade(기본, 현행 순차) / parallel(depth 또는
  max-panes 지정) — 필요할 때만 가속 비용을 지불한다.

## Context

- 현재 `scripts/taskset_dispatcher.py`는 "one task set" plan/start만 지원.
- 실측 증거: AR-310~316 순차 클레임, AR-372 4-워크트리 스택 체인 — 병렬
  프리미티브는 있으나 동시 발급 계층이 없어 cascade로만 동작.
- wave는 taskset과 직교하는 실행 묶음이며 기록 계층이 아니다(설계 기록
  Decision 참조). 한 wave에 여러 taskset의 unit이 실릴 수 있다.

## Preconditions

- 착수(claim) 전 `python scripts/plan_assumption_gate.py --check --taskset TASKSET-AR-PARALLEL-WAVE-EXECUTION` 실행 — drift 발견 시 replan 리뷰(차분 재계획 + anchor 갱신) 선행 필수. 근거: `reviews/MEETING-2026-06-12-plan-assumption-deferred-revalidation.md`.

## Scope

- unit frontmatter에 `depends_on`(unit/task id 목록) 선택 필드 추가 및
  readiness gate 검증 확장.
- `taskset_dispatcher.py`(또는 신규 `wave_dispatcher.py`)에:
  wave 계산(topological level + footprint 서로소 검증, TASK-AR-500 게이트
  재사용) / `--mode cascade|parallel --max-panes N` / wave 단위 claim+worktree
  일괄 발급 / wave 경계 동기화 포인트(전 unit 완료 시 풀 사이클 트리거 안내).
- pane당 발급 결과를 `pane_events`에 기록.
- 템플릿 미러 동기화.

## Out Of Scope

- 자동 페인 스폰(터미널 제어) — 발급까지만, 페인 기동은 Owner/codex 수동.
- 머지 직렬화(TASK-AR-502).

## Acceptance Criteria

- 의존성 있는 unit들이 같은 wave에 묶이지 않는다.
- `--mode parallel --max-panes 3`으로 서로소 unit 3개의 클레임이 한 번에
  발급되고, cascade 모드는 현행과 동일하게 동작한다.
- `pytest tests -q` 통과, 게이트 체인 exit 0.

## Evidence Targets

- 디스패처 변경분 + 테스트
- wave 발급 데모 클레임/이벤트 기록
- closeout review record

## Completion Evidence

- PR #64 (7302cec + a282185): scripts/wave_dispatcher.py topological wave planning (list scheduling) + cascade/parallel dispatch via claim dispatcher with per-unit footprints; depends_on validation + docs; 3 mirrors; 15 tests.

## Verification Results

- pytest tests/test_wave_dispatcher.py -q -> 15 passed
- pytest tests -q -> 590 passed (+1 pre-existing)
- real-repo --plan demo: units=9 waves=8 deferrals=28
- W4b inst-w4b-ar501-verifier -> Finding resolved (a282185), merged
