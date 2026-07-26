---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-629-001
work_uid: eba43350-2c4b-45aa-b0a0-261e44e11d92
kind: unit
parent_id: TASK-AR-629
unit_id: UNIT-TASK-AR-629-001
task_id: TASK-AR-629
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P0
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: passed
owner: lead_engineer
created_at: 2026-07-26T13:16:03+09:00
updated_at: 2026-07-26T13:19:26+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: requirements-lint 게이트 + NEEDS CLARIFICATION 마커 거부
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: 수용 기준은 필드 존재만 검사되고 '빠르게 동작'도 통과한다(task_unit_readiness_gate). 요구 명확화 인터뷰 산출물이 미확정 항목을 표시할 [NEEDS CLARIFICATION] 마커 규약이 없다. 측정 가능한 검증의 전제는 기준 문법이 측정 가능한 것이다.
inputs:
  - scripts/task_unit_readiness_gate.py:17-42
  - scripts/owner_governance_gate.py (게이트 체인 등록)
  - reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md (§Owner Decisions 5,8)
target_files:
  - new:scripts/requirements_lint_gate.py
  - scripts/task_unit_readiness_gate.py
  - scripts/owner_governance_gate.py
scope: 모호 어휘 린트 게이트 신설 + readiness 게이트의 NEEDS CLARIFICATION 거부. EARS 템플릿 전면 강제와 /clarify 스킬 본체는 P1.
acceptance:
  - 모호 어휘가 포함된 acceptance가 requirements_lint_gate에서 findings로 잡힌다
  - [NEEDS CLARIFICATION] 마커가 있는 unit이 readiness에서 거부된다
verification:
  - python -m pytest tests/test_work_item_classifier.py -q
  - python scripts/owner_governance_gate.py --allow-empty-owner-docs
handoff: 게이트 findings 샘플과 체인 등록 diff를 evidence로 남긴다. checkpoints 필드·closeout_pipeline은 후속 스텝으로 명시한다.
stop_condition: W4c 퀴즈 게이트나 /clarify 인터뷰 스킬 본체 구현으로 넓히지 말 것 — P1(1-4,1-6).
verified_at: 2026-07-26T13:19:26+09:00
verified_by: work.py verify
evidence_refs:
  - reviews/VERIFY-2026-07-26-unit-task-ar-629-001-20260726131926.json
---

# UNIT-TASK-AR-629-001 - requirements-lint 게이트 + NEEDS CLARIFICATION 마커 거부

## Context

수용 기준은 필드 존재만 검사되고 '빠르게 동작'도 통과한다(task_unit_readiness_gate). 요구 명확화 인터뷰 산출물이 미확정 항목을 표시할 [NEEDS CLARIFICATION] 마커 규약이 없다. 측정 가능한 검증의 전제는 기준 문법이 측정 가능한 것이다.

## Inputs

- scripts/task_unit_readiness_gate.py:17-42
- scripts/owner_governance_gate.py (게이트 체인 등록)
- reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md (§Owner Decisions 5,8)

## Target Files

- new:scripts/requirements_lint_gate.py
- scripts/task_unit_readiness_gate.py
- scripts/owner_governance_gate.py

## Scope

모호 어휘 린트 게이트 신설 + readiness 게이트의 NEEDS CLARIFICATION 거부. EARS 템플릿 전면 강제와 /clarify 스킬 본체는 P1.

## Steps

1. requirements_lint_gate.py를 신설해 acceptance/criteria의 한/영 모호 어휘와 escape clause를 findings로 낸다
2. task_unit_readiness_gate에 [NEEDS CLARIFICATION] 마커 잔존 시 worker-ready 거부 로직을 추가한다
3. owner_governance_gate 체인에 requirements_lint_gate를 등록한다
4. 테스트를 추가한다

## Acceptance Criteria

- 모호 어휘가 포함된 acceptance가 requirements_lint_gate에서 findings로 잡힌다
- [NEEDS CLARIFICATION] 마커가 있는 unit이 readiness에서 거부된다

## Verification

- `python -m pytest tests/test_work_item_classifier.py -q`
- `python scripts/owner_governance_gate.py --allow-empty-owner-docs`

## Handoff

게이트 findings 샘플과 체인 등록 diff를 evidence로 남긴다. checkpoints 필드·closeout_pipeline은 후속 스텝으로 명시한다.

## Stop Boundary

W4c 퀴즈 게이트나 /clarify 인터뷰 스킬 본체 구현으로 넓히지 말 것 — P1(1-4,1-6).