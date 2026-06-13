---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-324
work_uid: cf51aa7e-b10c-492d-91db-a52ca37a8f2f
kind: task
parent_id: TASKSET-AR-UI-UX-V2
origin_type: planning_proposal
origin_ref: TASKSET-AR-UI-UX-V2
created_by: planner
id: TASK-AR-324
display_id: TASK-AR-324
task_uid: cf51aa7e-b10c-492d-91db-a52ca37a8f2f
registered_at: 2026-06-11T18:39:01+09:00
created_at: 2026-06-11T18:39:01+09:00
updated_at: 2026-06-11T18:39:01+09:00
title: Team 뷰 — Agent 조직도 + RPG 프레즌스 카드
status: completed
started_at: 2026-06-13T17:19:47+09:00
completed_at: 2026-06-13T18:10:00+09:00
resolution: done
verification_status: passed
priority: P1
difficulty: M
est_hours: 8
est_tokens: 6000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-UX-V2
tags:
  - ui-ux-v2
  - org-chart
  - presence
---

# TASK-AR-324 - Team 뷰 — Agent 조직도 + RPG 프레즌스 카드

## Goal

- TEAMS/ORG/roles 데이터로 조직도 트리를 렌더링하고, 에이전트 카드를 온라인 RPG 길드 멤버처럼 상태가 살아있는 프레즌스로 보여준다.

## Scope

- 조직도 트리(Owner → 역할 계층), 역할 노드에 활성 인스턴스 수 뱃지 (`agents/project/TEAMS.md`, `ORG.md`, `agents/roles.yml`, task_claims 기반).
- 에이전트 카드: 역할 아이콘 아바타, online/idle/working/reviewing/in_meeting/offline 상태 링 + 펄스 애니메이션, 현재 task, 진행률, 마지막 발언.
- Agent Focus 패널(최근 메시지/이벤트/상태 전이 이력).

## Acceptance Criteria

- 조직도와 실제 활성 인스턴스가 일치하고 상태 전이가 시각적으로 구분된다.

## Evidence Targets

- `src/agent_runtime/ui_console.py`, `ui_state.py`
