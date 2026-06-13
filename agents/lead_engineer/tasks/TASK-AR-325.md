---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-325
work_uid: 49b8b641-aaae-4fe6-978d-254920b8e089
kind: task
parent_id: TASKSET-AR-UI-UX-V2
origin_type: planning_proposal
origin_ref: TASKSET-AR-UI-UX-V2
created_by: planner
id: TASK-AR-325
display_id: TASK-AR-325
task_uid: 49b8b641-aaae-4fe6-978d-254920b8e089
registered_at: 2026-06-11T18:39:01+09:00
created_at: 2026-06-11T18:39:01+09:00
updated_at: 2026-06-11T18:39:01+09:00
title: Roadmap 뷰 — Vision/Milestone/Release 타임라인
status: planned
priority: P2
difficulty: M
est_hours: 6
est_tokens: 5000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-UX-V2
tags:
  - ui-ux-v2
  - roadmap
  - vision
  - milestone
---

# TASK-AR-325 - Roadmap 뷰 — Vision/Milestone/Release 타임라인

## Goal

- Vision → Milestone/Release → Taskset 3계층을 한 뷰에서 보여줘 고수준 방향과 실제 진행률을 연결한다.

## Scope

- 데이터: `agents/project/VISION.md`, `ROADMAP.md`, BACKLOG.md 릴리스 계획, taskset 진행률.
- Milestone 타임라인(가로 바, 날짜, done 여부) + milestone-taskset 연결 및 합산 진행률 (Linear Projects/Milestones 모델 차용).

## Acceptance Criteria

- 각 milestone에서 연결된 taskset과 진행률이 표시되고 출처 파일이 링크된다.

## Evidence Targets

- `src/agent_runtime/ui_console.py`, `ui_state.py` roadmap 어댑터
