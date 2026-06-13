---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-327
work_uid: 32d13202-2b7c-4633-95b4-f709871abb22
kind: task
parent_id: TASKSET-AR-UI-UX-V2
origin_type: planning_proposal
origin_ref: TASKSET-AR-UI-UX-V2
created_by: planner
id: TASK-AR-327
display_id: TASK-AR-327
task_uid: 32d13202-2b7c-4633-95b4-f709871abb22
registered_at: 2026-06-11T18:39:01+09:00
created_at: 2026-06-11T18:39:01+09:00
updated_at: 2026-06-11T18:39:01+09:00
title: Channels 뷰 — 에이전트 대화 + meeting/seminar 소집
status: completed
started_at: 2026-06-13T19:12:22+09:00
completed_at: 2026-06-13T19:35:00+09:00
resolution: done
verification_status: passed
priority: P2
difficulty: L
est_hours: 10
est_tokens: 8000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-UX-V2
tags:
  - ui-ux-v2
  - comms
  - meeting
  - seminar
---

# TASK-AR-327 - Channels 뷰 — 에이전트 대화 + meeting/seminar 소집

## Goal

- 에이전트 간 대화를 Slack/Discord처럼 채널/스레드로 관전하고, Owner가 UI에서 meeting/seminar를 소집할 수 있게 한다.

## Scope

- 채널 = taskset 자동 채널 + #general + #governance, 스레드 = task 단위. 발신자 아바타·역할색.
- Owner 입력창: 에이전트/채널 지시 전송(`runtime.message`), `/meeting <주제> @역할`, `/seminar <주제>` 슬래시 명령.
- `meeting.start`/`seminar.start` 런타임 명령 타입 추가 → 합의 라운드 실행, reviews/MEETING-·SEMINAR- 기록과 Meetings 뷰 연동.

## Acceptance Criteria

- UI에서 소집한 meeting이 런타임 이벤트와 reviews/ 기록으로 남고 채널에서 대화가 추적된다.

## Evidence Targets

- `src/agent_runtime/ui_commands.py`, `ui_console.py`, reviews/ 기록 샘플
