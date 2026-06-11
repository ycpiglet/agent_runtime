---
id: TASK-AR-337
display_id: TASK-AR-337
task_uid: fa90ed9a-ed2b-46c1-9fc3-19893bfaa29c
registered_at: 2026-06-11T18:56:35+09:00
created_at: 2026-06-11T18:56:35+09:00
updated_at: 2026-06-11T18:56:35+09:00
title: 팀/역할 배정 모델 + 워크로드 히트맵
status: planned
priority: P1
difficulty: M
est_hours: 8
est_tokens: 6000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-PLATFORM-EXTENSIONS
tags:
  - ui-extensions
  - team-assignment
  - workload
---

# TASK-AR-337 - 팀/역할 배정 모델 + 워크로드 히트맵

## Goal

- task/taskset을 개인 에이전트가 아닌 팀/역할 단위로 배정하고, 에이전트·팀별 부하를 히트맵으로 보여준다 (Jira 컴포넌트 + Asana Workload 모델).

## Scope

- `assignee` 외에 `team`/`role` 배정 필드 표준화 (TEAMS.md 역할과 연동), taskset→팀 기본 배정.
- 워크로드 히트맵: 에이전트/팀 × 기간, 과부하·유휴 시각화. 배정 변경은 명령 경유.
- Team 뷰(TASK-AR-324 조직도)와 연동 — 역할 노드에서 담당 task 드릴다운.

## Acceptance Criteria

- 팀 배정이 task 메타데이터로 저장되고 히트맵·조직도·필터에서 일관 표시된다.

## Evidence Targets

- task frontmatter 스키마 확장, 히트맵 뷰, 테스트
