---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-632
display_id: TASK-AR-632
task_uid: f5a68bf6-f67a-4378-a7b3-7a8ab0dbba32
work_id: TASK-AR-632
work_uid: f5a68bf6-f67a-4378-a7b3-7a8ab0dbba32
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
registered_at: 2026-07-26T20:41:04+09:00
created_at: 2026-07-26T20:41:04+09:00
updated_at: 2026-07-26T20:41:04+09:00
title: renderAll() 해체 — 선택 렌더 + 갱신 경로 단일화
status: planned
priority: P2
difficulty: L
est_hours: 10
est_tokens: 1000
owner: lead_engineer
team: ui-ux
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P1
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
reservation_id: RES-20260726-204104-63e72cf5-03
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-26-console-overhaul-owner-decisions.md
created_by: claude-session-overhaul-planner
summary: [A1-4] 성능이자 인터랙션 품질(포커스/스크롤 보존)이자 calm technology 문제. 1-2와 병행 가능(모놀리스 위에서도 가능).
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-632 - renderAll() 해체 — 선택 렌더 + 갱신 경로 단일화

## Goal

- 매 4초 37개 렌더 함수 전량 재실행을 활성 뷰+콕핏 선택 렌더로 바꾸고 4s/8s/15s+SSE 4중 경로를 단일 디스패처로 통합한다.

## Scope

- route->renderer 매핑 + dirty-flag 렌더 + state epoch 단일 디스패처. 파일 물리 분리는 Phase 2(2-0).

## Acceptance Criteria

- 폴링 시 활성 뷰와 홈 콕핏만 재렌더되고 비활성 뷰는 진입 시 dirty-flag 렌더된다
- 4s/8s/15s setInterval + SSE 경로가 단일 state epoch 디스패처로 통합된다
- 갱신 중 활성 뷰의 포커스/스크롤 위치가 보존된다

## Verification

- `python -m pytest tests/test_ui_console.py tests/test_ui_console_microinteractions.py -q`
