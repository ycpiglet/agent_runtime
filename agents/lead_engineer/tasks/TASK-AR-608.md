---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-608
display_id: TASK-AR-608
task_uid: 070b84b3-0578-4899-a232-75a1507b76a2
work_id: TASK-AR-608
work_uid: 070b84b3-0578-4899-a232-75a1507b76a2
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
registered_at: 2026-07-22T17:45:27+09:00
created_at: 2026-07-22T17:45:27+09:00
updated_at: 2026-07-22T17:45:27+09:00
title: 축3 씨앗 — requirements-lint + NEEDS CLARIFICATION 마커 + checkpoints 필드
status: planned
priority: P1
difficulty: M
est_hours: 6
est_tokens: 1000
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P0
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-608/UNIT-TASK-AR-608-001.md
reservation_id: RES-20260722-174527-39947af3-07
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: [A3-2·A3-4·A3-7a] requirements-lint 게이트, [NEEDS CLARIFICATION] 마커 잔존 시 claim 거부, unit 스키마 checkpoints 필드, closeout 재생성 단일 파이프라인. /quiz opt-in 스킬은 후속 태스크.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-608 - 축3 씨앗 — requirements-lint + NEEDS CLARIFICATION 마커 + checkpoints 필드

## Goal

- 요구 명확화·측정 검증 게이트의 기계적 토대를 심어 P1 승격 전 캘리브레이션 데이터를 모은다.

## Scope

- 게이트/스키마/파이프라인 씨앗까지. W4c 퀴즈 게이트 승격과 /clarify 인터뷰 스킬 본체는 P1(1-4,1-6).

## Acceptance Criteria

- requirements_lint_gate가 acceptance의 모호 어휘(빠르게/적절히/as needed)와 escape clause를 검사한다
- task_unit_readiness_gate가 [NEEDS CLARIFICATION] 마커 잔존 시 worker-ready를 거부한다
- unit 스키마에 checkpoints 필드가 추가되고 미해소 checkpoint의 release가 거부된다
- closeout 재생성 시퀀스(classifier->board->index->freshness)가 closeout_pipeline로 일괄 실행된다

## Verification

- `python -m pytest tests/test_work_item_classifier.py tests/test_taskset_work_gate.py -q`
- `python scripts/owner_governance_gate.py --allow-empty-owner-docs`
