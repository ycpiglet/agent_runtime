---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-364
work_uid: e7f72328-33c8-4fbd-b0d7-18cb600e46f9
kind: task
parent_id: TASKSET-AR-UI-LIVING-CONSOLE
origin_type: planning_proposal
origin_ref: TASKSET-AR-UI-LIVING-CONSOLE
created_by: planner
id: TASK-AR-364
display_id: TASK-AR-364
task_uid: e7f72328-33c8-4fbd-b0d7-18cb600e46f9
registered_at: 2026-06-11T19:48:00+09:00
created_at: 2026-06-11T19:48:00+09:00
updated_at: 2026-06-11T19:48:00+09:00
title: 2D 오피스 맵 — 회사 맵 + 에이전트 스프라이트 + 이모지 상태 글리프
status: completed
started_at: 2026-06-14T00:35:14+09:00
completed_at: 2026-06-14T01:05:00+09:00
resolution: done
verification_status: passed
priority: P3
difficulty: L
est_hours: 12
est_tokens: 9000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-LIVING-CONSOLE
tags:
  - office-map
  - 2d
  - avatar
  - spatial
---

# TASK-AR-364 - 2D 오피스 맵 — 회사 맵 + 에이전트 스프라이트 + 이모지 상태 글리프

## Goal

- 실제 회사 같은 2D 맵에 에이전트를 배치해 한눈에 조직 활동을 보여준다 (Smallville/Generative Agents 패턴 — arXiv 2304.03442).

## Scope

- 최소 실행 가능 패턴: 정적 회사 맵(팀별 방 — 기획실/개발실/QA실/회의실/릴리스룸) + 에이전트 스프라이트(귀여운 픽셀 아바타) + **아바타 위 이모지 글리프로 현재 행동 무문자 표시**(💻 작업, 📝 기록, 🔍 리뷰, 💤 유휴).
- 공간 데이터: world→areas 트리 + 에이전트별 위치/행동 JSON (`ui_state` 확장). 방 배치는 역할↔방 매핑.
- 회의실(TASK-AR-361)과 연동: 회의 중 에이전트는 맵상 회의실로 이동 표시.
- 경로탐색 애니메이션은 Idea Vault IV-008 — 본 태스크 범위 아님(즉시 순간이동 표시).

## Acceptance Criteria

- 활성 에이전트가 담당 방에 렌더되고 상태 변화가 글리프로 반영된다.

## Evidence Targets

- 맵 뷰 구현, 스프라이트 에셋, Playwright 스크린샷
