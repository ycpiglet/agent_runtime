---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-636
display_id: TASK-AR-636
task_uid: b90037ce-451a-4971-bdeb-6a12f1ff01d9
work_id: TASK-AR-636
work_uid: b90037ce-451a-4971-bdeb-6a12f1ff01d9
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
registered_at: 2026-07-26T20:41:04+09:00
created_at: 2026-07-26T20:41:04+09:00
updated_at: 2026-07-26T20:41:04+09:00
title: Owner 승인 위험 티어링 (위임 확대)
status: planned
priority: P1
difficulty: M
est_hours: 7
est_tokens: 1000
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P1
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
reservation_id: RES-20260726-204104-63e72cf5-07
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-26-console-overhaul-owner-decisions.md
created_by: claude-session-overhaul-planner
summary: "\u001eagent-runtime-work-scalar-v1:[A3-7b] release-conductor\uc758 noncritical/critical \uc774\uc6d0\ud654\ub97c work close\u00b7green merge\ub85c \ud655\ub300, \uc704\uc784 \uc2b9\uc778\uc740 \uac01 \uac80\uc99d\uc790\uc758 \ub3c5\ub9bd \uadfc\uac70\ub97c reviews/COUNCIL-*.md\uc5d0 \uae30\ub85d. 1-6\uacfc \ub3d9\uc2dc \ubc30\ud3ec. (#9 \ud655\uc815: \uc800\uc704\ud5d8 council \uc704\uc784, \uace0\uc704\ud5d8 Owner \uc804\uacb0)"
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-636 - Owner 승인 위험 티어링 (위임 확대)

## Goal

- 저위험 승인을 council 위임으로 돌려 퀴즈/체크포인트로 늘어나는 Owner 접점을 상쇄한다.

## Scope

- 위험 티어링 정책 + council 근거 기록. orchestrator 권한 3분할 자체는 Phase 2(2-5).

## Acceptance Criteria

- work close(저위험)와 green 상태 merge process가 council 자율 처리 경로를 갖는다
- 위임 승인 시 각 검증자의 독립 근거가 reviews/COUNCIL-*.md에 표수가 아닌 근거로 기록된다
- critical 항목은 여전히 Owner 전결로 남는다

## Verification

- `python -m pytest tests/test_work_close.py -q`
- `python scripts/owner_governance_gate.py --allow-empty-owner-docs`
