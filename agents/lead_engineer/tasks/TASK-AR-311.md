---
id: TASK-AR-311
display_id: TASK-AR-311
task_uid: 6a155432-3a24-4ada-9f5a-cd15526a66d4
registered_at: 2026-06-11T17:58:45+09:00
created_at: 2026-06-11T17:58:45+09:00
updated_at: 2026-06-11T17:58:45+09:00
title: A2A 전용 메시지 라우팅 레이어 도입
status: planned
priority: P1
difficulty: L
est_hours: 8
est_tokens: 6000
owner: lead_engineer
task_set_id: TASKSET-AR-VISION-GAP-CLOSURE
tags:
  - a2a
  - multi-agent
  - messaging
---

# TASK-AR-311 - A2A 전용 메시지 라우팅 레이어 도입

## Goal

- 에이전트 간 통신을 태스크 상태/로그 추론 방식에서 명시적 메시지 패싱 API로 전환해 A2A 체인을 구조적으로 보장한다.

## Scope

- `agents/runtime/` 하위에 로컬 메시지 큐/라우팅 모듈 설계 (taskId + contextId 연속성, A2A 3.3/3.4 정렬).
- request → review → decision → correction 이벤트 체인을 메시지 단위로 기록.
- 기존 `scripts/a2a_trace_gate.py`가 신규 메시지 로그를 검증하도록 확장.

## Acceptance Criteria

- 두 에이전트 인스턴스가 메시지 API로 핸드오프하는 로컬 시나리오가 테스트로 증명된다.
- a2a_trace_gate가 메시지 기반 체인을 pass로 판정한다.

## Evidence Targets

- `agents/runtime/` 메시지 모듈 및 테스트
- `scripts/a2a_trace_gate.py`
