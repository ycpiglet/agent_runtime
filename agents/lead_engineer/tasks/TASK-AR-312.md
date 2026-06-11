---
id: TASK-AR-312
display_id: TASK-AR-312
task_uid: 13d31d8a-bac0-4a5f-aae5-38c50cf30918
registered_at: 2026-06-11T17:58:45+09:00
created_at: 2026-06-11T17:58:45+09:00
started_at: 2026-06-12T00:08:33+09:00
updated_at: 2026-06-12T00:08:33+09:00
title: 멀티에이전트 동시 실행 검증 및 RBAC 역할 강제
status: in_progress
priority: P1
difficulty: L
est_hours: 8
est_tokens: 6000
owner: lead_engineer
task_set_id: TASKSET-AR-VISION-GAP-CLOSURE
tags:
  - multi-agent
  - rbac
  - concurrency
  - verification
---

# TASK-AR-312 - 멀티에이전트 동시 실행 검증 및 RBAC 역할 강제

## Goal

- 문서로만 정의된 역할 체계(TEAMS/ORG/diversity council)를 실제 2~3개 동시 에이전트 인스턴스 실행으로 증명하고, 역할별 쓰기 권한을 게이트로 강제한다.

## Scope

- 2~3개 인스턴스(`agent_instance_id`/`display_name`/`callsite_id` 구분)가 태스크 클레임 충돌 없이 동시 작업하는 시나리오 구성 및 증거 기록.
- 역할 기반 쓰기 경계(예: qa 역할의 release 문서 변경 차단)를 검사하는 RBAC 게이트 추가.
- `NEXT-SESSION-POINTER.yml`의 `current_agents`가 실 인스턴스를 반영하는지 검증.

## Acceptance Criteria

- 동시 실행 시나리오의 pane event/claim 증거가 기록되고 충돌 0건이다.
- 비인가 역할의 보호 문서 변경이 게이트에서 차단되는 테스트가 존재한다.

## Evidence Targets

- `agents/runtime/task_claims/`, `agents/runtime/pane_events/`
- 신규 RBAC 게이트 스크립트 및 테스트
