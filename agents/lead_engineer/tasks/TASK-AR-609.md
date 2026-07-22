---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-609
display_id: TASK-AR-609
task_uid: 70f28077-3a99-45f6-8381-21cc797a1889
work_id: TASK-AR-609
work_uid: 70f28077-3a99-45f6-8381-21cc797a1889
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
registered_at: 2026-07-22T17:45:34+09:00
created_at: 2026-07-22T17:45:34+09:00
updated_at: 2026-07-22T17:45:34+09:00
title: attention 신호 단일 정본화 (보드=콕핏 로직 공유)
status: planned
priority: P1
difficulty: M
est_hours: 6
est_tokens: 1000
owner: lead_engineer
team: ui-ux
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P1
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
reservation_id: RES-20260722-174534-8e86c307-01
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: [A1-3] 웹 콘솔=1차 표면 / 보드=파생물 역할 분리의 논리 기반. 1-2가 이 로직을 소비하므로 선행. (§Decision 1 관련)
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-609 - attention 신호 단일 정본화 (보드=콕핏 로직 공유)

## Goal

- 보드 Rollups 휴리스틱과 콘솔 attention_inbox를 하나의 모듈로 통합해 두 표면이 다른 현황을 말하는 구조를 원천 차단하고, watch 단계를 콕핏에 승격한다.

## Scope

- attention 계산 단일 모듈화 + 양쪽 import 소비 + watch 티어 카드 승격. 홈 레이아웃 재구성 자체는 1-2.

## Acceptance Criteria

- backlog_board Rollups/lane_for와 콘솔 attention_inbox가 단일 모듈을 공유 import한다
- 콕핏 gate 그룹에 block뿐 아니라 watch 단계(예: compound_cadence_gate watch)가 저강조 카드로 표시된다
- 동일 상태에서 보드와 콘솔의 attention 집계가 일치한다(회귀 테스트)

## Verification

- `python -m pytest tests/test_ui_state.py tests/test_backlog_board_tasksets.py -q`
- `python scripts/taskset_work_gate.py --check`
