---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-628
display_id: TASK-AR-628
task_uid: 0d114f5b-42ba-490e-8eba-5277ab7be58b
work_id: TASK-AR-628
work_uid: 0d114f5b-42ba-490e-8eba-5277ab7be58b
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
registered_at: 2026-07-26T13:16:03+09:00
created_at: 2026-07-26T13:16:03+09:00
updated_at: 2026-07-26T13:16:03+09:00
title: Owner-facing 계약 봉합 — REPORTING-FORMAT + 참조 드리프트
status: planned
priority: P2
difficulty: S
est_hours: 3
est_tokens: 1000
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P0
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-628/UNIT-TASK-AR-628-001.md
reservation_id: RES-20260726-131603-af796687-06
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: [A3-8] REPORTING-FORMAT 정본 복원 + response_contract_gate 강화, OPS 참조 스킬 6종 추가, 예시 powershell->bash 정정.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-628 - Owner-facing 계약 봉합 — REPORTING-FORMAT + 참조 드리프트

## Goal

- 신설 스킬(/clarify·/quiz)이 등재될 canonical surface를 먼저 정상화한다.

## Scope

- 문서 정본 복원 + 게이트 강화 + 참조 드리프트 수정. 신규 스킬 자체는 P0(축3 씨앗)/P1.

## Acceptance Criteria

- agents/lead_engineer/REPORTING-FORMAT.md 정본이 복원되고 Bottom Line->Signal->Insight->Decision 포맷을 담는다
- response_contract_gate가 등재 경로 부재 시 fail한다(현재 조용히 통과)
- OPS-COMMAND-REFERENCE.md 스킬 표에 grill/enable/scaffold/rsi-planning-loop/failure-to-regression/session-closeout이 추가되고 예시가 bash로 정정된다

## Verification

- `python -m pytest tests/test_session_dashboard.py -q`
- `python scripts/response_contract_gate.py`
- `python scripts/owner_governance_gate.py --allow-empty-owner-docs`
