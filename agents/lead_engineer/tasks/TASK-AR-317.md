---
id: TASK-AR-317
display_id: TASK-AR-317
task_uid: 4ffc5085-45ba-4e42-8d7c-ca06f4fd3fdc
registered_at: 2026-06-11T17:58:45+09:00
created_at: 2026-06-11T17:58:45+09:00
updated_at: 2026-06-11T17:58:45+09:00
title: UI 실시간화(SSE) 및 Planner 승인/거절 워크플로
status: planned
priority: P2
difficulty: L
est_hours: 10
est_tokens: 8000
owner: lead_engineer
task_set_id: TASKSET-AR-VISION-GAP-CLOSURE
tags:
  - ui-console
  - sse
  - planner
  - workflow
---

# TASK-AR-317 - UI 실시간화(SSE) 및 Planner 승인/거절 워크플로

## Goal

- UI 콘솔을 읽기 전용 스냅샷 대시보드에서 운영 제어 표면으로 승격한다: 에이전트 루프 진행이 실시간 반영되고, 제안 승인/거절이 UI에서 가능해야 한다.

## Scope

- Server-Sent Events(또는 WebSocket) 레이어 추가로 페이지 새로고침 없는 상태 갱신.
- Planner 패널에 제안 diff 표시 + 승인/거절 액션(서명된 감사 추적 포함, Owner 게이트 유지).
- 빌드/커밋 식별자 노출(TASK-AR-309 가드 계획과 연계).

## Acceptance Criteria

- 에이전트 이벤트 발생 시 UI가 자동 갱신되는 시나리오 테스트 통과.
- 제안 승인/거절이 기존 planning gate 체계를 우회하지 않음이 검증된다.

## Evidence Targets

- `src/agent_runtime/ui_console.py`, `ui_state.py`, `ui_commands.py`
- Playwright 검증 기록
