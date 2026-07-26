---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-626
display_id: TASK-AR-626
task_uid: 48696c56-44a6-4f8e-a67f-2af2c300c39c
work_id: TASK-AR-626
work_uid: 48696c56-44a6-4f8e-a67f-2af2c300c39c
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
registered_at: 2026-07-26T13:16:03+09:00
created_at: 2026-07-26T13:16:03+09:00
updated_at: 2026-07-26T13:16:03+09:00
title: 데이터 위생 — 타임스탬프 게이트 + actuals/rework 자동 파생
status: planned
priority: P1
difficulty: M
est_hours: 5
est_tokens: 1000
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P0
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-626/UNIT-TASK-AR-626-001.md
reservation_id: RES-20260726-131603-af796687-04
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: [A2-1 core] registered<=started<=completed 단조성 게이트 + 모순 레코드 backfilled 격리 + timestamp_quality 스키마 등록. actuals/rework 자동 파생은 main-evolved 코어(cmd_close/dispatcher) 위험으로 closeout-automation 후속 태스크로 이관.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-626 - 데이터 위생 — 타임스탬프 게이트 + actuals/rework 자동 파생

## Goal

- 흐름 지표의 원료를 신뢰 가능하게 만든다: 타임스탬프 모순 차단, 수동 기입 폐지.

## Scope

- 단조성 게이트 + backfilled 격리 마커 + 스키마 카탈로그 등록(자가완결 core). closeout/release 자동 파생은 후속 태스크로 이관. WIP 소급 재구성·FLOW-DIGEST는 P1.

## Acceptance Criteria

- work_schema_gate가 registered_at<=started_at<=completed_at 단조성을 검사하고 위반을 findings로 낸다
- 기존 백필 모순 레코드에 timestamp_quality: backfilled 마커가 부여되어 지표 계산에서 제외되고, timestamp_quality가 WORK-SCHEMA 카탈로그(root+template 변이 스타일)에 등록된다
- deferred(closeout-automation 후속): closeout 시 actual_hours 자동 기입 / W4b 반려 시 rework_count 자동 증가

## Verification

- `python -m pytest tests/test_work_schema_gate.py -q`
- `python scripts/work_schema_gate.py --items --check`
