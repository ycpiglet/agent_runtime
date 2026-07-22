---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-602
display_id: TASK-AR-602
task_uid: afe4e45c-4752-4bd8-b06c-b9889b75aef5
work_id: TASK-AR-602
work_uid: afe4e45c-4752-4bd8-b06c-b9889b75aef5
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
registered_at: 2026-07-22T17:45:27+09:00
created_at: 2026-07-22T17:45:27+09:00
updated_at: 2026-07-22T17:45:27+09:00
title: 신뢰 복구 — 신선도 배지 + 캐시 사각지대 해소
status: planned
priority: P1
difficulty: M
est_hours: 4
est_tokens: 1000
owner: lead_engineer
team: ui-ux
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P0
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-602/UNIT-TASK-AR-602-001.md
reservation_id: RES-20260722-174527-39947af3-01
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: [A1-1] '빠르게 볼 수는 있으나 믿을 수 없다' 문제 해소. 모든 후속 화면 작업의 전제.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-602 - 신뢰 복구 — 신선도 배지 + 캐시 사각지대 해소

## Goal

- 콘솔·보드가 표시하는 데이터가 얼마나 오래되었는지 항상 보이게 하고, 감시 사각지대로 인한 최대 300초 stale을 없앤다.

## Scope

- ui_state의 상태 캐시 시그니처 확장과 홈 신선도 배지, 보드 generated_at 초 단위화까지. 홈 레이아웃 전면 재구성은 P1(1-2)로 이관.

## Acceptance Criteria

- _STATE_SIG_DIRS에 agents/messages, .ui_outbox, STATUS.md 변경이 반영되어 해당 소스 편집 시 상태 시그니처가 바뀐다
- 홈 헤더에 '데이터 기준: N초 전' 신선도 배지가 상시 표시되고 임계 초과 시 watch 색으로 바뀐다
- 콕핏 빈 상태 카피가 '처리할 것 없음 (기준 HH:MM:SS)' 형식으로 기준 시각을 포함한다
- BACKLOG-BOARD.md generated_at이 ISO 초 단위 타임스탬프다

## Verification

- `python -m pytest tests/test_ui_state.py tests/test_ui_console.py tests/test_backlog_board_tasksets.py -q`
- `python scripts/owner_governance_gate.py --allow-empty-owner-docs`
