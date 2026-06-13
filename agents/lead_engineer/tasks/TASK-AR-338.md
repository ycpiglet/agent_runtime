---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-338
work_uid: d15c8e5a-6ef3-401b-992f-af333b342015
kind: task
parent_id: TASKSET-AR-UI-PLATFORM-EXTENSIONS
origin_type: planning_proposal
origin_ref: TASKSET-AR-UI-PLATFORM-EXTENSIONS
created_by: planner
id: TASK-AR-338
display_id: TASK-AR-338
task_uid: d15c8e5a-6ef3-401b-992f-af333b342015
registered_at: 2026-06-11T18:56:35+09:00
created_at: 2026-06-11T18:56:35+09:00
updated_at: 2026-06-11T18:56:35+09:00
title: 알림 센터 + 멘션/핀/리액션 + 데일리 브리프
status: planned
priority: P2
difficulty: M
est_hours: 8
est_tokens: 6000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-PLATFORM-EXTENSIONS
tags:
  - ui-extensions
  - notifications
  - mentions
---

# TASK-AR-338 - 알림 센터 + 멘션/핀/리액션 + 데일리 브리프

## Goal

- 중요한 변화(blocked, 승인 대기, 마감 임박, 멘션)를 인앱 알림 인박스로 모으고, 채널에 멘션·핀·리액션을 더한다 (Slack + Linear Inbox 모델).

## Scope

- 알림 센터: 이벤트 구독 규칙(타입/심각도/taskset), mute·키워드 규칙, 읽음 처리.
- @멘션(에이전트/역할/Owner) — 멘션 시 해당 대상 알림 + 에이전트 런타임 메시지 발행. 메시지 핀/리액션.
- 데일리 브리프: 오늘 완료/차단/결정/다음 권장 작업 자동 요약 카드 (brief §13.2).

## Acceptance Criteria

- blocked 발생→알림 수신→해당 task 딥링크 흐름이 동작하고 mute 규칙이 적용된다.

## Evidence Targets

- 알림 모듈, Channels 뷰 확장, 테스트
