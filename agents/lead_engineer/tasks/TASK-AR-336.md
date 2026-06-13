---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-336
work_uid: 8176e789-20ee-4a7e-92c0-b9f68515fb81
kind: task
parent_id: TASKSET-AR-UI-PLATFORM-EXTENSIONS
origin_type: planning_proposal
origin_ref: TASKSET-AR-UI-PLATFORM-EXTENSIONS
created_by: planner
id: TASK-AR-336
display_id: TASK-AR-336
task_uid: 8176e789-20ee-4a7e-92c0-b9f68515fb81
registered_at: 2026-06-11T18:56:35+09:00
created_at: 2026-06-11T18:56:35+09:00
updated_at: 2026-06-11T18:56:35+09:00
title: 상태머신 인터랙티브 뷰어
status: planned
priority: P2
difficulty: M
est_hours: 6
est_tokens: 5000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-PLATFORM-EXTENSIONS
tags:
  - ui-extensions
  - state-machine
  - visualization
---

# TASK-AR-336 - 상태머신 인터랙티브 뷰어

## Goal

- `agents/project/STATE-MACHINES.yml`의 라이프사이클(task/claim/role)을 인터랙티브 그래프로 보여주고, 선택한 task의 현재 상태와 전이 이력을 하이라이트한다 (Jira workflow viewer / XState viz 모델).

## Scope

- 상태 노드·전이 엣지 그래프 렌더(편집 불가 — YAML이 SSoT).
- task 상세에서 "상태머신에서 보기" → 현재 상태 강조 + 지나온 전이 경로 표시(이벤트 로그 기반).

## Acceptance Criteria

- 모든 정의된 머신이 렌더되고 임의 task의 현재 상태가 그래프에서 식별된다.

## Evidence Targets

- 상태머신 뷰, `ui_state.py` 어댑터
