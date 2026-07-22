---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-605
display_id: TASK-AR-605
task_uid: fb47ad5e-3d39-4671-8959-e16fbd3d0762
work_id: TASK-AR-605
work_uid: fb47ad5e-3d39-4671-8959-e16fbd3d0762
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
registered_at: 2026-07-22T17:45:27+09:00
created_at: 2026-07-22T17:45:27+09:00
updated_at: 2026-07-22T17:45:27+09:00
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
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-605/UNIT-TASK-AR-605-001.md
reservation_id: RES-20260722-174527-39947af3-04
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: [A2-1·A2-2] registered<=started<=completed 단조성 게이트, 오염 레코드 격리 마커, claim wall-clock으로 actual_hours 자동, W4b 반려 시 rework 자동 +1, lead_time->cycle_time 정리.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-605 - 데이터 위생 — 타임스탬프 게이트 + actuals/rework 자동 파생

## Goal

- 흐름 지표의 원료를 신뢰 가능하게 만든다: 타임스탬프 모순 차단, 수동 기입 폐지.

## Scope

- 게이트 추가 + closeout/release 자동 파생 배선. WIP 시계열 소급 재구성은 후속 스텝, FLOW-DIGEST는 P0(전달 씨앗)/P1(1-8).

## Acceptance Criteria

- work_schema_gate가 registered_at<=started_at<=completed_at 단조성을 검사하고 위반을 findings로 낸다
- 기존 백필 모순 레코드에 timestamp_quality: backfilled 마커가 부여되어 지표 계산에서 제외된다
- closeout 시 claim wall-clock으로부터 actual_hours가 자동 기입된다
- W4b 반려 발생 시 task_claim_dispatcher가 rework_count를 자동 증가시킨다

## Verification

- `python -m pytest tests/test_work_efficiency.py tests/test_work_close.py -q`
- `python scripts/work_schema_gate.py --check`
