---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-322
work_uid: 144350a0-85cd-4510-8758-24d0b4dc4701
kind: task
parent_id: TASKSET-AR-UI-UX-V2
origin_type: planning_proposal
origin_ref: TASKSET-AR-UI-UX-V2
created_by: planner
id: TASK-AR-322
display_id: TASK-AR-322
task_uid: 144350a0-85cd-4510-8758-24d0b4dc4701
registered_at: 2026-06-11T18:39:01+09:00
created_at: 2026-06-11T18:39:01+09:00
updated_at: 2026-06-11T18:39:01+09:00
title: 공통 리스트 패턴 — 정렬/필터/그룹/검색 + 밀도 토글
status: planned
priority: P1
difficulty: L
est_hours: 10
est_tokens: 8000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-UX-V2
tags:
  - ui-ux-v2
  - filter
  - sort
  - density
---

# TASK-AR-322 - 공통 리스트 패턴 — 정렬/필터/그룹/검색 + 밀도 토글

## Goal

- 모든 리스트 뷰(task/agent/event/message/evidence)에 Notion/Linear형 정렬·필터·그룹·검색 바와 간략히/자세히 밀도 토글을 공통 컴포넌트로 제공한다.

## Scope

- 필터: 상태/우선순위/담당/taskset/태그/날짜. 그룹: taskset(기본)·상태·담당. 정렬: 우선순위·갱신시각·진행률.
- 밀도 `compact / cozy / detail` 3단, 저장된 뷰(명명된 필터 조합), 조건의 URL+localStorage 영속화.
- 커맨드 팔레트(Ctrl+K)와 키보드 내비게이션(j/k/Enter) 기반 마련.

## Acceptance Criteria

- 동일 컴포넌트가 최소 3개 뷰에서 재사용되고 새로고침 후 조건이 유지된다.

## Evidence Targets

- `src/agent_runtime/ui_console.py`, UI 테스트
