---
id: TASK-AR-318
display_id: TASK-AR-318
task_uid: 367a501a-c74b-4762-b9f5-b0c0ce0d2b03
registered_at: 2026-06-11T17:58:45+09:00
created_at: 2026-06-11T17:58:45+09:00
updated_at: 2026-06-11T17:58:45+09:00
title: 증거 타임 스크러버/리플레이 뷰
status: planned
priority: P3
difficulty: M
est_hours: 6
est_tokens: 5000
owner: lead_engineer
task_set_id: TASKSET-AR-VISION-GAP-CLOSURE
tags:
  - ui-console
  - evidence
  - replay
---

# TASK-AR-318 - 증거 타임 스크러버/리플레이 뷰

## Goal

- 이벤트/수정 기록을 나열에서 인과 체인 재생으로 승격해, 상태 변화를 프레임 단위로 거슬러 볼 수 있게 한다.

## Scope

- Evidence 패널에 타임 스크러버 추가: pane event/correction/A2A 추적의 시점별 상태 재구성.
- 기존 append-only 이벤트 로그(`agents/runtime/pane_events/` 등)를 재생 소스로 사용.

## Acceptance Criteria

- 특정 시점 선택 시 해당 시점의 상태 스냅샷이 재구성되어 표시된다.

## Evidence Targets

- `src/agent_runtime/ui_console.py` Evidence 패널
