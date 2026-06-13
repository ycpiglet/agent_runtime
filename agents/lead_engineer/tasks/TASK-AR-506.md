---
id: TASK-AR-506
display_id: TASK-AR-506
task_uid: 25e129f5-2ad1-4b21-af3f-3c5655d358be
registered_at: 2026-06-12T21:15:09+09:00
created_at: 2026-06-12T21:15:09+09:00
updated_at: 2026-06-13T12:40:00+09:00
started_at: 2026-06-13T09:53:21+09:00
completed_at: 2026-06-13T12:40:00+09:00
title: Lifecycle discipline by default — W0~W6 contract + auto T0/T2 wiring
status: completed
priority: P1
difficulty: M
est_hours: 7
est_tokens: 6000
owner: lead_engineer
initiative_id: INIT-AR-PARALLEL-WAVE-EXECUTION
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-PARALLEL-WAVE-EXECUTION
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
escalation_triggers:
  - ambiguity
  - cross_cutting
tags:
  - parallel
  - plan-governance
  - contract
  - lifecycle
---

# TASK-AR-506 - Lifecycle discipline by default

## Goal

- 이번 taskset에만 수동 적용된 지연평가 규율(T0 스냅샷/T2 착수 체크)과
  W0~W6 수명주기를 **모든 작업의 기본값**으로 만든다 — Owner 요구:
  "이번 건만이 아니라 앞으로 모든 작업들이 그렇게 되길 원한다."

## Context

- 현재 `plan_assumption_gate`는 opt-in이다: 등록자가 record를 잊으면
  보호가 없다. 규율은 플로우에 내장될 때만 기본값이 된다.
- W0~W6 규칙은 회의 기록에만 존재한다
  (`reviews/MEETING-2026-06-12-parallel-work-lifecycle-rules.md`).
  계약 문서 명문화는 codex가 AGENTS.md와
  PROJECT-MANAGEMENT-CONTRACT.md를 미머지 브랜치에서 수정 중이라 merge
  후로 지연했다.
- codex의 AR-372 등록 CLI(`work.py` 계열)가 merge되면 등록/디스패치
  진입점이 바뀐다 — 본 task는 그 새 진입점에 T0/T2를 편입한다.

## Preconditions

- codex `TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE` + agent-identity
  브랜치 merge 완료 후에만 착수 (이 task의 대상 파일이 merge로 확정됨).
- 착수(claim) 전 `python scripts/plan_assumption_gate.py --check --taskset TASKSET-AR-PARALLEL-WAVE-EXECUTION` 실행 — drift 발견 시 replan 리뷰 선행 필수.

## Scope

- 등록 플로우(post-merge 기준 work.py 또는 현행 수동 절차)에 T0
  `plan_assumption_gate record` 자동 편입 — taskset 등록 시 전제 스냅샷이
  기본 생성되도록.
- 디스패치 플로우(`taskset_dispatcher start` / `task_claim_dispatcher
  create`)에 T2 `--check` 자동 편입 — drift 시 claim 발급 거부.
- W0 가시성: 세션 시작 시 활성 클레임/워크트리 요약을 출력하는 진입점
  (기존 NEXT-SESSION-POINTER 절차에 명령어로 연결).
- W0~W6 수명주기를 AGENTS.md(또는 PROJECT-MANAGEMENT-CONTRACT.md)에
  명문화 + 템플릿 전파.
- 템플릿 미러 동기화.

## Out Of Scope

- footprint 게이트(AR-500), wave 디스패처(AR-501), 머지 큐(AR-502),
  claim-first 게이트(AR-503), 워크트리 정리(AR-505) 자체의 구현.
- codex 신규 스키마의 재설계 — 편입만 한다.

## Acceptance Criteria

- 신규 taskset 등록 시 전제 스냅샷이 자동 기록된다.
- drift 상태에서 claim 발급이 거부되고 replan 안내가 출력된다.
- W0~W6이 계약 문서에 존재하고 템플릿에 전파된다.
- `pytest tests -q` 통과, 게이트 체인 exit 0.

## Evidence Targets

- 등록/디스패치 플로우 변경분 + 테스트
- 계약 문서 변경분
- closeout review record

## Completion Evidence

- PR #72 (9d41e03): auto T0 snapshot in work.py registration, inline T2 drift refusal in claim creation, work.py status W0 entrypoint, W0-W6 contract in AGENTS.md + template; 11 tests.

## Verification Results

- pytest tests/test_lifecycle_defaults.py -q -> 11 passed
- pytest tests -q -> 696 passed
- owner governance chain -> pass (no bypass)
- W4b inst-w4b-ar506-verifier -> APPROVE
