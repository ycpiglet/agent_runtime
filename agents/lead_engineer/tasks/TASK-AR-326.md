---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-326
work_uid: b7f20335-3e03-4ae1-b7c4-ce57b56d340c
kind: task
parent_id: TASKSET-AR-UI-UX-V2
origin_type: planning_proposal
origin_ref: TASKSET-AR-UI-UX-V2
created_by: planner
id: TASK-AR-326
display_id: TASK-AR-326
task_uid: b7f20335-3e03-4ae1-b7c4-ce57b56d340c
registered_at: 2026-06-11T18:39:01+09:00
created_at: 2026-06-11T18:39:01+09:00
updated_at: 2026-06-11T18:39:01+09:00
title: 실시간 프레즌스 + rqt형 라이브 그래프
status: planned
priority: P2
difficulty: L
est_hours: 12
est_tokens: 9000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-UX-V2
tags:
  - ui-ux-v2
  - realtime
  - sse
  - graph
---

# TASK-AR-326 - 실시간 프레즌스 + rqt형 라이브 그래프

## Goal

- 에이전트/업무/메시지가 온라인 RPG처럼 실시간으로 살아 움직이는 감각을 SSE 이벤트 스트림과 라이브 그래프로 구현한다.

## Scope

- TASK-AR-317의 SSE 기반 위에 구축(의존): 프레즌스 상태 전이, 활동 피드 토스트, 진행률 실시간 갱신.
- Live Map: 노드(Owner/에이전트/taskset/게이트)·엣지(메시지/할당/리뷰/차단) 그래프. 이벤트 수신 시 엣지 펄스 하이라이트.
- 1단계 정적 그래프+주기 갱신 → 2단계 SSE 라이브.

## Acceptance Criteria

- 에이전트 상태 변화가 새로고침 없이 카드·그래프에 반영되고 메시지 흐름이 엣지로 시각화된다.

## Evidence Targets

- `src/agent_runtime/ui_console.py`, SSE 엔드포인트, Playwright 검증
