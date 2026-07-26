---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-624
display_id: TASK-AR-624
task_uid: da880246-e32a-4201-9857-8933bcd7c5b8
work_id: TASK-AR-624
work_uid: da880246-e32a-4201-9857-8933bcd7c5b8
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
registered_at: 2026-07-26T13:16:03+09:00
created_at: 2026-07-26T13:16:03+09:00
updated_at: 2026-07-26T13:16:03+09:00
title: 홈 위계 1차 — 요약 소음 제거
status: planned
priority: P1
difficulty: S
est_hours: 3
est_tokens: 1000
owner: lead_engineer
team: ui-ux
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P0
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-624/UNIT-TASK-AR-624-001.md
reservation_id: RES-20260726-131603-af796687-02
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: [A1-2 선행분] 전역 폼을 홈/Work 한정, 히어로·타일 접이식 강등, 0건 그룹 렌더 생략.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-624 - 홈 위계 1차 — 요약 소음 제거

## Goal

- 홈 최상단의 시각적 소음과 위계 붕괴를 마크업/CSS 이동 수준에서 즉시 완화한다.

## Scope

- 기존 마크업/CSS 재배치와 0건 그룹 조건부 렌더까지. verdict 배지·흐름 타일 신설은 P1(1-2).

## Acceptance Criteria

- 태스크 생성/런타임 커맨드 폼이 홈·Work 뷰에만 노출되고 Labels·Knowledge Graph 등 무관한 뷰에서는 사라진다
- 콕핏에서 개체 0건인 어텐션 그룹 카드는 렌더되지 않는다
- Work state 히어로와 위젯이 접이식/2차 강등되어 콕핏이 첫 화면 상단을 차지한다

## Verification

- `python -m pytest tests/test_ui_console.py tests/test_ui_console_microinteractions.py -q`
- `python scripts/nav_budget_gate.py --check`
