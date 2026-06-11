---
id: TASK-AR-330
display_id: TASK-AR-330
task_uid: 7bd76418-976d-4eac-827f-eac0390649f4
registered_at: 2026-06-11T18:56:35+09:00
created_at: 2026-06-11T18:56:35+09:00
updated_at: 2026-06-11T18:56:35+09:00
title: 서브태스크·의존성 모델 + 타임라인/의존 그래프
status: planned
priority: P1
difficulty: L
est_hours: 10
est_tokens: 8000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-PLATFORM-EXTENSIONS
tags:
  - ui-extensions
  - dependencies
  - gantt
---

# TASK-AR-330 - 서브태스크·의존성 모델 + 타임라인/의존 그래프

## Goal

- task 계층(서브태스크)과 의존성(blocks/blocked-by)을 데이터 모델로 정식화하고 타임라인(Gantt)·의존 그래프로 시각화한다.

## Scope

- task frontmatter에 `parent_id`, `blocks`, `blocked_by` 표준화 + 검증 게이트.
- 타임라인 뷰(Asana/ClickUp형): taskset·milestone 기준 가로 바, 의존 화살표.
- 의존 그래프(Live Map과 데이터 공유), 순환 의존 감지 경고.

## Acceptance Criteria

- 의존 관계가 보드/타임라인/그래프에서 일관 표시되고 순환 시 게이트가 경고한다.

## Evidence Targets

- `src/agent_runtime/ui_state.py`, 타임라인 뷰, 검증 테스트
