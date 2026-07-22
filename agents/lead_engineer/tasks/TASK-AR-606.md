---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-606
display_id: TASK-AR-606
task_uid: b72d044c-8bf4-4fe6-a41f-5b45533f2a8f
work_id: TASK-AR-606
work_uid: b72d044c-8bf4-4fe6-a41f-5b45533f2a8f
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
registered_at: 2026-07-22T17:45:27+09:00
created_at: 2026-07-22T17:45:27+09:00
updated_at: 2026-07-22T17:45:27+09:00
title: 전달 씨앗 — 세션 delta + 보드 throughput
status: planned
priority: P2
difficulty: S
est_hours: 3
est_tokens: 1000
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P0
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-606/UNIT-TASK-AR-606-001.md
reservation_id: RES-20260722-174527-39947af3-05
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: [A2-3·A2-4 선행분] session_dashboard에 '지난 7일 flow delta' 1줄, 보드 Rollups에 throughput 숫자(velocity.weeks 재사용).
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-606 - 전달 씨앗 — 세션 delta + 보드 throughput

## Goal

- 이미 있는 데이터를 Owner에게 전달하는 최소 경로를 심는다.

## Scope

- 훅·계열 데이터 재사용 수준의 전달. 주간 FLOW-DIGEST 문서 자동 생성은 P1(1-8).

## Acceptance Criteria

- SessionStart의 session_dashboard 출력에 '지난 7일: 완료 N · median cycle X h · 반려 M' 1줄이 포함된다
- BACKLOG-BOARD.md Rollups에 주간 throughput 숫자가 표시된다(velocity 계열 재사용)

## Verification

- `python -m pytest tests/test_session_dashboard.py tests/test_backlog_board_tasksets.py -q`
- `python scripts/owner_governance_gate.py --allow-empty-owner-docs`
