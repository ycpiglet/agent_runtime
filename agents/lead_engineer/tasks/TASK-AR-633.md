---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-633
display_id: TASK-AR-633
task_uid: 650be20d-9d63-466a-ae19-291553f46e36
work_id: TASK-AR-633
work_uid: 650be20d-9d63-466a-ae19-291553f46e36
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
registered_at: 2026-07-26T20:41:04+09:00
created_at: 2026-07-26T20:41:04+09:00
updated_at: 2026-07-26T20:41:04+09:00
title: /clarify 엔지니어링 인터뷰 게이트 (W1.5) + EARS 수용 기준
status: planned
priority: P1
difficulty: L
est_hours: 12
est_tokens: 1000
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P1
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
reservation_id: RES-20260726-204104-63e72cf5-04
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-26-console-overhaul-owner-decisions.md
created_by: claude-session-overhaul-planner
summary: "\u001eagent-runtime-work-scalar-v1:[A3-1\u00b7A3-2] grill \uc124\uacc4\ub97c \uc5d4\uc9c0\ub2c8\uc5b4\ub9c1 \ub808\uc778\uc73c\ub85c \uc774\uc2dd(\ubcc4\ub3c4 \uc2a4\ud0ac). \ubcf5\uc218 \ud574\uc11d \uc0d8\ud50c\ub9c1->\uac1d\uad00\uc2dd \uc778\ud130\ubdf0->reviews/INTERVIEW-*.md, \ub9c8\ucee4 0\uac1c+owner_approved_at\uc744 claim \uc804\uc81c\ub85c. Phase0(requirements-lint\u00b7\ub9c8\ucee4) \uc774\ud6c4. (#8 \ud655\uc815: grill\uacfc \ubcc4\ub3c4 \uc2a4\ud0ac\ub85c \ubcd1\ud589 \uacf5\uc874. #5 \ud655\uc815: \ubc1c\ub3d9 \uc784\uacc4 diff 100\uc904+\ud575\uc2ec \uacbd\ub85c \ubb34\uc870\uac74+est_hours)"
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-633 - /clarify 엔지니어링 인터뷰 게이트 (W1.5) + EARS 수용 기준

## Goal

- 엔지니어링 요구에 대해 모호성을 탐지하고 불일치 지점만 인터뷰해 합의된 EARS 수용 기준을 강제한다.

## Scope

- 인터뷰 스킬 + readiness 게이트 확장(마커+승인 전제) + EARS 템플릿/린트 전면화. W4c 퀴즈는 1-6.

## Acceptance Criteria

- /clarify 스킬이 위험 분류(ambiguous/high-risk/cross-cutting)로 임계 차등 발동하고 불일치 지점만 객관식으로 질문한다
- 인터뷰 결과가 reviews/INTERVIEW-*.md로 물화되고 미확정은 [NEEDS CLARIFICATION] 마커로 남는다
- task_unit_readiness_gate가 마커 0개 + owner_approved_at 존재를 claim 생성(W2) 전제로 강제한다
- acceptance가 EARS 6패턴 템플릿을 따르고 requirements-lint를 통과한다

## Verification

- `python -m pytest tests/test_work_item_classifier.py tests/test_work_criteria.py -q`
- `python scripts/owner_governance_gate.py --allow-empty-owner-docs`
