---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-333
work_uid: 53e47fbc-3a57-4b6a-8b5e-e177c97abd57
kind: task
parent_id: TASKSET-AR-UI-PLATFORM-EXTENSIONS
origin_type: planning_proposal
origin_ref: TASKSET-AR-UI-PLATFORM-EXTENSIONS
created_by: planner
id: TASK-AR-333
display_id: TASK-AR-333
task_uid: 53e47fbc-3a57-4b6a-8b5e-e177c97abd57
registered_at: 2026-06-11T18:56:35+09:00
created_at: 2026-06-11T18:56:35+09:00
updated_at: 2026-06-11T18:56:35+09:00
title: 가져오기/내보내기 — Markdown/CSV/JSON + 백업 번들
status: planned
priority: P2
difficulty: M
est_hours: 6
est_tokens: 5000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-PLATFORM-EXTENSIONS
tags:
  - ui-extensions
  - import
  - export
---

# TASK-AR-333 - 가져오기/내보내기 — Markdown/CSV/JSON + 백업 번들

## Goal

- taskset/보드/이벤트를 표준 포맷으로 내보내고, 외부 목록을 task로 일괄 가져올 수 있게 한다 (Notion/Jira 모델).

## Scope

- 내보내기: taskset→md 패키지, 보드→CSV, 상태 스냅샷→JSON, 전체 백업 zip 번들.
- 가져오기: md 체크리스트/CSV → task 일괄 생성(미리보기·중복 감지 포함, `task.create` 명령 경유).

## Acceptance Criteria

- 내보낸 CSV를 다시 가져왔을 때 손실 없이 왕복(round-trip)된다.

## Evidence Targets

- export/import 스크립트, UI 메뉴, 왕복 테스트
