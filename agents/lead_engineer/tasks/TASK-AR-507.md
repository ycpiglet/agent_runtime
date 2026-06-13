---
id: TASK-AR-507
display_id: TASK-AR-507
task_uid: 2df22d07-ceab-4402-99d2-b455dbdc8c53
registered_at: 2026-06-12T21:24:50+09:00
created_at: 2026-06-12T21:24:50+09:00
updated_at: 2026-06-13T10:30:00+09:00
started_at: 2026-06-13T08:37:43+09:00
completed_at: 2026-06-13T10:30:00+09:00
title: Cross-verification gate — verifier must differ from worker
status: completed
priority: P1
difficulty: M
est_hours: 6
est_tokens: 5000
owner: lead_engineer
initiative_id: INIT-AR-PARALLEL-WAVE-EXECUTION
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-PARALLEL-WAVE-EXECUTION
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
escalation_triggers:
  - cross_cutting
tags:
  - verification
  - independence
  - gate
---

# TASK-AR-507 - Cross-verification gate

## Goal

- Owner 규칙 "작업자가 스스로 검증 금지, 항상 다른 에이전트가 검증"을
  실행 가능하게 강제한다: claim release/closeout 시 verifier 식별자가
  worker 식별자와 다름을 게이트가 검사한다.

## Context

- 결정 기록: `reviews/MEETING-2026-06-12-independent-verification-rule.md`
  (W4a 작업자 verification 실행 / W4b 독립 검증 승인 분리).
- 인스턴스 귀속(agent_instance_id 스폰 기록, attribution gate)은 codex
  AR-375가 구축 중 — 본 게이트의 식별 기반이므로 merge 후 착수한다.

## Preconditions

- codex agent-identity 브랜치 merge 완료 (인스턴스 귀속 스키마 확정).
- 착수(claim) 전 `python scripts/plan_assumption_gate.py --check --taskset TASKSET-AR-PARALLEL-WAVE-EXECUTION` 실행 — drift 발견 시 replan 리뷰 선행 필수.

## Scope

- claim/closeout 스키마에 `verified_by`(instance id + role) 필드 추가.
- release/closeout 경로에서 `verified_by` 부재 또는 worker와 동일 시 차단.
- 검증 증거 경로(리뷰 기록/검증 로그) 첨부 요건.
- 과도기 수동 기록과의 호환(기존 closeout 소급 면제).
- 템플릿 미러 동기화.

## Out Of Scope

- 검증의 품질 평가(독립성 식별만 강제).
- 사람 Owner 승인 플로우 변경.

## Acceptance Criteria

- worker == verifier 또는 verifier 부재 시 release가 차단된다.
- 서로 다른 인스턴스/역할 검증 기록이 있으면 통과한다.
- `pytest tests -q` 통과, 게이트 체인 exit 0.

## Evidence Targets

- 게이트 변경분 + 테스트
- closeout review record

## Completion Evidence

- PR #66 (9a91fdf): release path enforces verifier != worker with evidence requirement; claim JSON + pane event carry W4b actor; mirrors; 8 new tests.

## Verification Results

- pytest tests/test_task_claim_dispatcher.py -q -> 21 passed
- pytest tests -q -> 627 passed (+1 environment, patch-roundtrip proven at base)
- tmp-repo demo: self-release refused / distinct verifier passes
- W4b inst-w4b-ar507-verifier2 -> APPROVE
