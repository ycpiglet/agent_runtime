---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-620
display_id: TASK-AR-620
task_uid: 2c901d8f-2678-4b43-b5a6-db80b732f759
work_id: TASK-AR-620
work_uid: 2c901d8f-2678-4b43-b5a6-db80b732f759
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P2
registered_at: 2026-07-22T17:45:34+09:00
created_at: 2026-07-22T17:45:34+09:00
updated_at: 2026-07-22T17:45:34+09:00
title: 실패 패턴 압축 파이프라인
status: planned
priority: P3
difficulty: M
est_hours: 7
est_tokens: 1000
owner: lead_engineer
team: evaluation-office
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P2
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P2
reservation_id: RES-20260722-174534-069bcc6e-04
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: [A2-7] failure-to-regression 스킬의 'fixture/게이트/태스크 전환' 규칙에 공급. 동일 근본원인 캐스케이드는 1건으로 그룹화. 2-2 이벤트 데이터로 정밀도 상승. REVIEW 303 vs COMPOUND/RETRO 8(watch) 압축 부채 해소.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-620 - 실패 패턴 압축 파이프라인

## Goal

- 게이트 실패·W4b 반려·VERIFY 실패를 원인/파일 기준 클러스터링해 top recurring failure를 뽑아 regression으로 전환한다.

## Scope

- 실패 클러스터링 + top 후보 생성 + regression 전환 연동. 실시간 알림은 범위 밖.

## Acceptance Criteria

- 게이트 실패/W4b 반려/VERIFY 실패가 원인·대상 파일 기준으로 클러스터링된다
- top recurring failure 후보가 생성되어 failure-to-regression 경로에 공급된다
- 동일 근본 원인의 캐스케이드가 1건으로 그룹화된다

## Verification

- `python -m pytest tests/test_work_efficiency.py -q`
