---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-606-001
work_uid: 2bcc6338-7b39-4f33-a83f-f41345939aca
kind: unit
parent_id: TASK-AR-606
unit_id: UNIT-TASK-AR-606-001
task_id: TASK-AR-606
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P0
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: passed
owner: lead_engineer
created_at: 2026-07-22T17:45:27+09:00
updated_at: 2026-07-22T23:01:17+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: session_dashboard flow delta 1줄 + 보드 throughput 숫자
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: 인사이트가 Owner에게 도달하는 push 경로가 없다(work.py stats는 pull 전용). session_dashboard(scripts/session_dashboard.py)는 SessionStart 훅으로 이미 실행되고, 주간 velocity 실계열이 ui_state.py:7888-7897에 계산돼 있다.
inputs:
  - scripts/session_dashboard.py
  - scripts/backlog_board.py (Rollups 렌더)
  - scripts/work.py (stats/velocity 계산)
target_files:
  - scripts/session_dashboard.py
  - scripts/backlog_board.py
scope: 세션 시작 1줄 + 보드 Rollups throughput 숫자. 신규 문서 산출물 없음.
acceptance:
  - session_dashboard 출력에 flow delta 1줄이 있다
  - 보드 Rollups에 throughput 숫자가 있다
verification:
  - python -m pytest tests/test_session_dashboard.py tests/test_backlog_board_tasksets.py -q
handoff: session_dashboard 출력 예시와 보드 diff를 evidence로 남긴다.
stop_condition: 주간 FLOW-DIGEST 문서 파이프라인 구축으로 넓히지 말 것 — P1(1-8).
verified_at: 2026-07-22T23:01:17+09:00
verified_by: work.py verify
evidence_refs:
  - reviews/VERIFY-2026-07-22-unit-task-ar-606-001-20260722230117.json
---

# UNIT-TASK-AR-606-001 - session_dashboard flow delta 1줄 + 보드 throughput 숫자

## Context

인사이트가 Owner에게 도달하는 push 경로가 없다(work.py stats는 pull 전용). session_dashboard(scripts/session_dashboard.py)는 SessionStart 훅으로 이미 실행되고, 주간 velocity 실계열이 ui_state.py:7888-7897에 계산돼 있다.

## Inputs

- scripts/session_dashboard.py
- scripts/backlog_board.py (Rollups 렌더)
- scripts/work.py (stats/velocity 계산)

## Target Files

- scripts/session_dashboard.py
- scripts/backlog_board.py

## Scope

세션 시작 1줄 + 보드 Rollups throughput 숫자. 신규 문서 산출물 없음.

## Steps

1. session_dashboard에 지난 7일 완료수·median cycle·반려수를 계산해 1줄로 출력하는 블록을 추가한다
2. backlog_board Rollups 렌더에 주간 throughput 숫자를 추가한다(velocity 계열 재사용)
3. tests/test_session_dashboard.py, tests/test_backlog_board_tasksets.py에 케이스를 추가한다

## Acceptance Criteria

- session_dashboard 출력에 flow delta 1줄이 있다
- 보드 Rollups에 throughput 숫자가 있다

## Verification

- `python -m pytest tests/test_session_dashboard.py tests/test_backlog_board_tasksets.py -q`

## Handoff

session_dashboard 출력 예시와 보드 diff를 evidence로 남긴다.

## Stop Boundary

주간 FLOW-DIGEST 문서 파이프라인 구축으로 넓히지 말 것 — P1(1-8).