---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-323
work_uid: e6d32d94-52e2-4872-a176-d3742e821dc2
kind: task
parent_id: TASKSET-AR-UI-UX-V2
origin_type: planning_proposal
origin_ref: TASKSET-AR-UI-UX-V2
created_by: planner
id: TASK-AR-323
display_id: TASK-AR-323
task_uid: e6d32d94-52e2-4872-a176-d3742e821dc2
registered_at: 2026-06-11T18:39:01+09:00
created_at: 2026-06-11T18:39:01+09:00
updated_at: 2026-06-13T16:50:00+09:00
started_at: 2026-06-13T16:29:49+09:00
completed_at: 2026-06-13T16:50:00+09:00
resolution: done
verification_status: passed
title: Tasksets 중심 작업 뷰 + Owner task 주입
status: completed
priority: P1
difficulty: L
est_hours: 10
est_tokens: 8000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-UX-V2
tags:
  - ui-ux-v2
  - taskset
  - task-management
---

# TASK-AR-323 - Tasksets 중심 작업 뷰 + Owner task 주입

## Goal

- task 평면 나열 대신 taskset 단위로 묶인 직관적 작업 뷰를 기본 진입점으로 만들고, Owner가 진행 중 흐름에 task를 안전하게 삽입할 수 있게 한다.

## Scope

- taskset 카드: 진행률 bar(done/total), 상태 분포, 담당 에이전트 아바타 스택, 최근 활동. 확장 시 소속 task 리스트(상태칩 plan/work/review 라벨, 담당, 진행률%, 우선순위).
- "+ Add task": `task.create` 명령 경유 + 큐 위치 지정(맨 앞/특정 task 다음). 직접 파일 변경 금지 원칙 유지.
- Board 칸반에 taskset 스윔레인 토글.

## Acceptance Criteria

- 진행중 task의 상태·담당·%가 taskset 맥락에서 5초 내 파악된다. 주입된 task가 런타임 큐에 반영된다.

## Evidence Targets

- `src/agent_runtime/ui_console.py`, `src/agent_runtime/ui_commands.py`, UI 테스트

## Completion Evidence

- PR #93: tasksets_board resource + Taskset Board panel + task.create insertion; 51 focused/735 full; W4b APPROVE.

## Verification Results

- W4b APPROVE; full suite green; see claim handoff closeout.
