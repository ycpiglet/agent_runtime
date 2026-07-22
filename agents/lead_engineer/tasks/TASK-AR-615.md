---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-615
display_id: TASK-AR-615
task_uid: 6bd359ac-3a79-4540-8be5-6a2c7a2e6ba5
work_id: TASK-AR-615
work_uid: 6bd359ac-3a79-4540-8be5-6a2c7a2e6ba5
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
registered_at: 2026-07-22T17:45:34+09:00
created_at: 2026-07-22T17:45:34+09:00
updated_at: 2026-07-22T17:45:34+09:00
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
reservation_id: RES-20260722-174534-8e86c307-07
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: [A3-7b] release-conductor의 noncritical/critical 이원화를 work close·green merge로 확대, 위임 승인은 각 검증자의 독립 근거를 reviews/COUNCIL-*.md에 기록. 1-6과 동시 배포. (§Decision 9 종속)
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-615 - Owner 승인 위험 티어링 (위임 확대)

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
