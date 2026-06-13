---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-335
work_uid: 3908d50e-cd42-4efe-a3a1-1323258b97ee
kind: task
parent_id: TASKSET-AR-UI-PLATFORM-EXTENSIONS
origin_type: planning_proposal
origin_ref: TASKSET-AR-UI-PLATFORM-EXTENSIONS
created_by: planner
id: TASK-AR-335
display_id: TASK-AR-335
task_uid: 3908d50e-cd42-4efe-a3a1-1323258b97ee
registered_at: 2026-06-11T18:56:35+09:00
created_at: 2026-06-11T18:56:35+09:00
updated_at: 2026-06-11T18:56:35+09:00
title: 캘린더/스케줄링 — 예약 디스패치·반복·리마인더
status: planned
priority: P2
difficulty: L
est_hours: 10
est_tokens: 8000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-PLATFORM-EXTENSIONS
tags:
  - ui-extensions
  - calendar
  - scheduling
---

# TASK-AR-335 - 캘린더/스케줄링 — 예약 디스패치·반복·리마인더

## Goal

- 마일스톤/회의/완료 이력/예약 실행을 캘린더 뷰로 통합하고, taskset 디스패치를 예약·반복 실행할 수 있게 한다 (Notion Calendar/Motion 모델).

## Scope

- 월/주 캘린더 뷰: milestone 기한, meeting/seminar 기록, task 완료 이력, 예약 실행 표시.
- 예약 디스패치: 지정 시각/반복(cron형)에 `taskset_dispatcher` 실행 등록 — 로컬 스케줄러, 외부 서비스 없음.
- 마감 임박/지연 리마인더를 알림 센터(TASK-AR-338)로 발행.

## Acceptance Criteria

- 예약한 디스패치가 기록·실행되고 캘린더와 알림에서 추적된다.

## Evidence Targets

- 스케줄러 스크립트, 캘린더 뷰, 테스트
