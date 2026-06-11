---
id: TASK-AR-329
display_id: TASK-AR-329
task_uid: 7e0540ad-8cc8-4b9f-88e0-c089d6c7d6a4
registered_at: 2026-06-11T18:56:35+09:00
created_at: 2026-06-11T18:56:35+09:00
updated_at: 2026-06-11T18:56:35+09:00
title: Taskset 라이프사이클 UI — 생성/보관/이동/벌크/undo/템플릿
status: planned
priority: P1
difficulty: L
est_hours: 10
est_tokens: 8000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-PLATFORM-EXTENSIONS
tags:
  - ui-extensions
  - taskset-crud
  - bulk-edit
---

# TASK-AR-329 - Taskset 라이프사이클 UI — 생성/보관/이동/벌크/undo/템플릿

## Goal

- Owner가 UI에서 taskset을 직접 만들고, task를 넣고 빼고, 일괄 편집할 수 있게 한다 (Linear Projects / Notion DB 모델).

## Scope

- taskset 생성/이름변경/보관(아카이브) UI — `taskset.create` 등 명령 타입 추가, backlog_board 레지스트리(본체+템플릿) 동기 갱신 경로 포함.
- task의 taskset 간 이동(드래그 + 메뉴), 멀티선택 + 벌크 편집(상태/우선순위/담당), 실행 취소(undo) 토스트.
- task/taskset 템플릿: 반복 패턴(예: 분석 taskset 4종 구성)을 1클릭 생성.

## Acceptance Criteria

- UI에서 만든 taskset이 레지스트리·보드·게이트와 정합하고 레지스트리 잠금 테스트가 자동 갱신 경로를 가진다.

## Evidence Targets

- `src/agent_runtime/ui_commands.py`, `scripts/backlog_board.py`, UI 테스트
