---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-361
work_uid: f078b413-65df-4ea1-9e90-200e67d8a07b
kind: task
parent_id: TASKSET-AR-UI-LIVING-CONSOLE
origin_type: planning_proposal
origin_ref: TASKSET-AR-UI-LIVING-CONSOLE
created_by: planner
id: TASK-AR-361
display_id: TASK-AR-361
task_uid: f078b413-65df-4ea1-9e90-200e67d8a07b
registered_at: 2026-06-11T19:48:00+09:00
created_at: 2026-06-11T19:48:00+09:00
updated_at: 2026-06-13T16:50:00+09:00
started_at: 2026-06-13T16:29:50+09:00
completed_at: 2026-06-13T16:50:00+09:00
resolution: done
verification_status: passed
title: Meeting Room — 에이전트 드래그 인 회의실
status: completed
priority: P1
difficulty: L
est_hours: 12
est_tokens: 9000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-LIVING-CONSOLE
tags:
  - meeting-room
  - drag-drop
  - interaction
---

# TASK-AR-361 - Meeting Room — 에이전트 드래그 인 회의실

## Goal

- 사이드탭의 회의실 공간에 에이전트를 마우스로 끌어다 넣고, 주제/태스크를 선택하면 참여 에이전트들이 의견을 주고받는 회의를 실행한다.

## Scope

- 드롭 존 패턴(Discord 음성채널 드래그 동형): 에이전트 카드 → 회의실 드롭, 참석자 슬롯 표시.
- 주제/task 선택 → 회의 유형(meeting/seminar/review) → 라운드 수/종결 조건 설정 → `meeting.start` 실행(TASK-AR-327 명령 기반).
- 진행 중: 발언이 실시간 스레드로 흐르고 Owner가 중간 개입(발언/안건 추가) 가능. 종료 시 결론 요약 + `reviews/MEETING-*.md` 자동 기록.
- 접근성: Discord 패턴의 키보드 등가(들기/이동/드롭/취소) 필수.

## Acceptance Criteria

- 드래그·키보드 양쪽으로 회의 소집이 가능하고 기록이 reviews/에 남는다.

## Evidence Targets

- `src/agent_runtime/ui_console.py`, `ui_commands.py`, MEETING 기록 샘플

## Verification Results

- scope delivered as structured shell (server-rendered); live multi-agent dialogue is a follow-up.
- `scripts/meeting_room.py plan`: proposal-only command; validates config and writes a `reviews/MEETING-<date>-<topic-slug>.md` skeleton (frontmatter `type: meeting` + participants + agenda rounds). Never mutates `reviews/` from the console directly.
- ui_state.py: `meeting_room` resource (available agents deduped by role, open-task topic options, config + constraints, proposal-only command descriptor).
- ui_console.py: Meeting Room tab/view with drag-drop drop-zone + keyboard equivalents (Enter/Space add, Delete remove), config form, `/api/meeting_room` (+ `/api/meeting-room`) route.
- pytest tests/test_meeting_room.py -q -> 13 passed
- pytest tests/test_ui_state.py tests/test_ui_console.py -q -> 45 passed
- pytest tests -q -> 742 passed
- `python scripts/owner_governance_gate.py` -> exit 0 (in worktree)
- real-repo demo: console on ephemeral port, GET /api/meeting_room -> HTTP 200, schema agent-runtime-meeting-room/v1
- meeting.plan demo (tmp dir): recorded MEETING-2026-06-13-meeting-room-demo-sync.md skeleton; failure path (1 participant) -> exit 1 with ASCII error.

## Completion Evidence

- PR #92: meeting_room resource + drag-drop panel (a11y) + proposal-only plan writer; 13+45 focused/742 full; W4b APPROVE.

## Verification Results

- W4b APPROVE; full suite green; see claim handoff closeout.
